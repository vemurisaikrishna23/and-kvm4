"""
Camera worker: keeps MediaMTX in sync with camera sessions and captures
snapshots during fuel requests. Run exactly ONE instance:

    python manage.py camera_worker

Every tick (2 s):
  - collects finished snapshot JPEGs → MEDIA_ROOT/camera_snapshots/YYYY/MM/DD/<txn>/<uuid>.jpg
    and saves a RequestCameraSnapshot row + request.latest_snapshot_path/snapshot_count
Every CAMERA_RECONCILE_INTERVAL_S (15 s):
  - reconcile_all(): expire sessions, add/remove MediaMTX paths
  - log camera_live / camera_offline / unknown_publisher events
  - start/stop one FFmpeg per active fuel-request session whose camera is live
  - one extra "stage" snapshot whenever the request status changes
Once a day (only if CAMERA_SNAPSHOT_RETENTION_DAYS > 0): delete old snapshots.

Design: ATD_Server/CAMERA_MANAGEMENT_DESIGN.md (sections 5 and 6.4a)
"""
import fcntl
import os
import shutil
import signal
import struct
import subprocess
import time
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.models import F
from django.utils import timezone

from IoT_Panel import camera_service, mediamtx
from IoT_Panel.mediamtx import MediaMTXError
from IoT_Panel.models import (
    Camera,
    CameraStreamSession,
    OrderFuelDispensingDetails,
    RequestCameraSnapshot,
    RequestFuelDispensingDetails,
)

TICK_S = 2
UNKNOWN_PUBLISHER_LOG_EVERY_S = 3600
FFMPEG_RESTART_BACKOFF_S = 5


def jpeg_size(path):
    """(width, height) from a JPEG's SOF marker, without Pillow."""
    try:
        with open(path, "rb") as f:
            if f.read(2) != b"\xff\xd8":
                return None, None
            while True:
                b = f.read(1)
                while b and b != b"\xff":
                    b = f.read(1)
                while b == b"\xff":
                    b = f.read(1)
                if not b:
                    return None, None
                marker = b[0]
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    continue
                seg_len = struct.unpack(">H", f.read(2))[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    f.read(1)
                    h, w = struct.unpack(">HH", f.read(4))
                    return w, h
                f.seek(seg_len - 2, os.SEEK_CUR)
    except (OSError, struct.error):
        return None, None


class Capture:
    """One FFmpeg process writing a frame every N seconds for one session."""

    def __init__(self, session_id, input_url, tmp_dir):
        self.session_id = session_id
        self.input_url = input_url
        self.tmp_dir = tmp_dir
        self.proc = None
        self.next_start_at = 0

    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self):
        os.makedirs(self.tmp_dir, exist_ok=True)
        interval = max(1, settings.CAMERA_SNAPSHOT_INTERVAL_S)
        cmd = [
            settings.FFMPEG_BIN, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-rtsp_transport", "tcp",
            "-skip_frame", "nokey",              # decoder option (before -i): keyframes only → low CPU
            "-i", self.input_url,
            "-vf", f"fps=1/{interval},scale={settings.CAMERA_SNAPSHOT_WIDTH}:-2",
            "-q:v", "5", "-f", "image2",
            os.path.join(self.tmp_dir, f"p_{int(time.time())}_%06d.jpg"),
        ]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop(self):
        if self.running():
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None


class Command(BaseCommand):
    help = "Camera worker: MediaMTX sync + fuel-request snapshots (run exactly one instance)."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Run one reconcile + snapshot cycle and exit (for testing).")

    def handle(self, *args, **opts):
        self.snap_root = os.path.join(settings.MEDIA_ROOT, settings.CAMERA_SNAPSHOT_DIR)
        self.tmp_root = os.path.join(self.snap_root, ".tmp")
        os.makedirs(self.tmp_root, exist_ok=True)

        lock = open(os.path.join(self.snap_root, ".camera_worker.lock"), "w")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.stderr.write("Another camera_worker is already running. Exiting.")
            return

        self.captures = {}            # session_id -> Capture
        self.stage_procs = []         # (Popen, session_id, out_path, started_at)
        self.last_status = {}         # session_id -> request_status seen
        self.live_prev = {}           # camera_id -> bool
        self.unknown_logged = {}      # path -> last log time
        self.last_cleanup = 0
        self.stop_flag = False

        signal.signal(signal.SIGTERM, self._on_signal)
        signal.signal(signal.SIGINT, self._on_signal)

        self.stdout.write(
            f"camera_worker started: reconcile every {settings.CAMERA_RECONCILE_INTERVAL_S}s, "
            f"snapshot every {settings.CAMERA_SNAPSHOT_INTERVAL_S}s, media={self.snap_root}"
        )
        next_reconcile = 0
        try:
            while not self.stop_flag:
                close_old_connections()
                self._safe(camera_service.touch_worker_heartbeat)
                now = time.time()
                if now >= next_reconcile:
                    self._safe(self.reconcile_cycle)
                    next_reconcile = now + settings.CAMERA_RECONCILE_INTERVAL_S
                self._safe(self.collect_snapshots)
                self._safe(self.maybe_cleanup)
                if opts.get("once"):
                    time.sleep(TICK_S)
                    self._safe(self.collect_snapshots)
                    break
                time.sleep(TICK_S)
        finally:
            for c in self.captures.values():
                c.stop()
            self._safe(self.collect_snapshots)
            self.stdout.write("camera_worker stopped")

    def _on_signal(self, *_):
        self.stop_flag = True

    def _safe(self, fn):
        try:
            fn()
        except Exception as e:  # keep the loop alive no matter what
            self.stderr.write(f"[camera_worker] {fn.__name__} error: {e}")

    # --- reconcile + live tracking + capture management ----------------------------

    def reconcile_cycle(self):
        camera_service.reconcile_all()

        cameras = list(Camera.objects.all())
        live = camera_service.live_status_map(cameras)
        unreachable = any(v["live_status"] == "mediamtx_unreachable" for v in live.values())
        if not unreachable:
            for cam in cameras:
                is_live = live[cam.id]["live_status"] == "live"
                was = self.live_prev.get(cam.id)
                if was is not None and was != is_live:
                    details = {"path": cam.rtmp_path}
                    if is_live and live[cam.id]["live"]:
                        details["tracks"] = live[cam.id]["live"].get("tracks")
                    camera_service.log_event(cam, "camera_live" if is_live else "camera_offline", details)
                self.live_prev[cam.id] = is_live
            self.log_unknown_publishers({c.rtmp_path for c in cameras})

        # Captures: one per active fuel-request session whose camera is live
        sessions = list(
            camera_service.active_sessions()
            .filter(reason="fuel_request")
            .select_related("camera", "request", "order_request")
        )
        wanted = set()
        for s in sessions:
            cam_live = live.get(s.camera_id, {}).get("live_status") == "live"
            if not cam_live:
                continue
            wanted.add(s.id)
            cap = self.captures.get(s.id)
            if cap is None:
                cap = Capture(
                    s.id,
                    f"{settings.MEDIAMTX_RTSP_BASE.rstrip('/')}/{s.camera.rtmp_path}",
                    os.path.join(self.tmp_root, str(s.id)),
                )
                self.captures[s.id] = cap
            if not cap.running() and time.time() >= cap.next_start_at:
                cap.start()
                cap.next_start_at = time.time() + FFMPEG_RESTART_BACKOFF_S

            # Stage snapshot on request-status change (first sighting counts as a stage too)
            req = s.request or s.order_request
            status_now = getattr(req, "request_status", None)
            if status_now is not None and self.last_status.get(s.id) != status_now:
                self.last_status[s.id] = status_now
                self.start_stage_capture(s, cap.input_url, status_now)

        for sid in list(self.captures):
            if sid not in wanted:
                self.captures[sid].stop()
                del self.captures[sid]
                self.last_status.pop(sid, None)

    def start_stage_capture(self, session, input_url, request_status):
        d = os.path.join(self.tmp_root, str(session.id))
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, f"s_{int(time.time())}_{request_status}.jpg")
        cmd = [
            settings.FFMPEG_BIN, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-rtsp_transport", "tcp", "-skip_frame", "nokey", "-i", input_url,
            "-frames:v", "1", "-vf", f"scale={settings.CAMERA_SNAPSHOT_WIDTH}:-2", "-q:v", "4", "-y", out,
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.stage_procs.append((proc, session.id, out, time.time()))

    def log_unknown_publishers(self, known_paths):
        try:
            conns = mediamtx.list_rtmp_conns()
        except MediaMTXError:
            return
        now = time.time()
        for c in conns:
            path = c.get("path")
            if not path or path in known_paths:
                continue
            if now - self.unknown_logged.get(path, 0) >= UNKNOWN_PUBLISHER_LOG_EVERY_S:
                camera_service.log_event(None, "unknown_publisher", {"path": path, "remote_addr": c.get("remoteAddr"), "state": c.get("state")})
                self.unknown_logged[path] = now

    # --- snapshot collection --------------------------------------------------------

    def collect_snapshots(self):
        # finished one-shot stage captures
        still = []
        for proc, sid, out, started in self.stage_procs:
            if proc.poll() is None:
                if time.time() - started > 30:
                    proc.kill()  # stuck (camera dropped)
                    proc.wait()
                else:
                    still.append((proc, sid, out, started))
                    continue
            if os.path.exists(out) and os.path.getsize(out) > 0:
                self.save_snapshot(sid, out, "stage")
            elif os.path.exists(out):
                os.remove(out)
        self.stage_procs = still

        # periodic frames: a file is complete once a newer one exists, or the capture stopped
        if not os.path.isdir(self.tmp_root):
            return
        for sid_name in os.listdir(self.tmp_root):
            d = os.path.join(self.tmp_root, sid_name)
            if not os.path.isdir(d) or not sid_name.isdigit():
                continue
            sid = int(sid_name)
            frames = sorted(f for f in os.listdir(d) if f.startswith("p_") and f.endswith(".jpg"))
            cap = self.captures.get(sid)
            done = frames if (cap is None or not cap.running()) else frames[:-1]
            for f in done:
                path = os.path.join(d, f)
                if os.path.getsize(path) > 0:
                    self.save_snapshot(sid, path, "periodic")
                else:
                    os.remove(path)
            if cap is None and not os.listdir(d) and not any(p[1] == sid for p in self.stage_procs):
                shutil.rmtree(d, ignore_errors=True)

    def save_snapshot(self, session_id, tmp_path, kind):
        s = CameraStreamSession.objects.select_related("camera", "request", "order_request").filter(id=session_id).first()
        if s is None or not s.transaction_id:
            os.remove(tmp_path)
            return
        captured_at = timezone.localtime(datetime.fromtimestamp(os.path.getmtime(tmp_path), tz=dt_timezone.utc))
        rel_dir = os.path.join(settings.CAMERA_SNAPSHOT_DIR, captured_at.strftime("%Y/%m/%d"), s.transaction_id)
        abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        name = f"{uuid.uuid4().hex}.jpg"
        abs_path = os.path.join(abs_dir, name)
        shutil.move(tmp_path, abs_path)
        width, height = jpeg_size(abs_path)
        media_path = "/" + os.path.join(settings.MEDIA_URL.strip("/"), rel_dir, name).replace(os.sep, "/")

        req = s.request
        order = s.order_request
        src = req or order
        gps = None
        if src is not None:
            gps = getattr(src, "gps_coordinates_ending", None) or getattr(src, "gps_coordinates_starting", None)
        RequestCameraSnapshot.objects.create(
            request=req,
            order_request=order,
            transaction_id=s.transaction_id,
            dispenser_unit_id=s.dispenser_unit_id or s.camera.dispenser_unit_id,
            camera=s.camera,
            session=s,
            dispenser_serialnumber=getattr(src, "dispenser_serialnumber", None),
            dispenser_imeinumber=getattr(src, "dispenser_imeinumber", None),
            dispenser_gun_mapping_id=getattr(src, "dispenser_gun_mapping_id", None),
            request_status=getattr(src, "request_status", None),
            dispense_status_code=getattr(src, "dispense_status_code", None),
            dispensed_volume=getattr(src, "dispenser_received_volume", None),
            dispensed_amount=getattr(src, "dispenser_received_price", None),
            gps_coordinates=gps,
            kind=kind,
            image_path=media_path,
            width=width,
            height=height,
            size_bytes=os.path.getsize(abs_path),
            captured_at=captured_at,
            created_at=timezone.now(),
        )
        if req is not None:
            RequestFuelDispensingDetails.objects.filter(id=req.id).update(
                latest_snapshot_path=media_path, snapshot_count=F("snapshot_count") + 1
            )

    # --- retention (off by default: keep everything) ---------------------------------

    def maybe_cleanup(self):
        days = settings.CAMERA_SNAPSHOT_RETENTION_DAYS
        if days <= 0 or time.time() - self.last_cleanup < 24 * 3600:
            return
        self.last_cleanup = time.time()
        cutoff = timezone.now() - timedelta(days=days)
        old = RequestCameraSnapshot.objects.filter(captured_at__lt=cutoff)
        removed = 0
        for snap in old.iterator():
            rel = snap.image_path.lstrip("/")
            media_prefix = settings.MEDIA_URL.strip("/") + "/"
            if rel.startswith(media_prefix):
                rel = rel[len(media_prefix):]
            try:
                os.remove(os.path.join(settings.MEDIA_ROOT, rel))
            except FileNotFoundError:
                pass
            removed += 1
        old.delete()
        if removed:
            self.stdout.write(f"retention: removed {removed} snapshots older than {days} days")
