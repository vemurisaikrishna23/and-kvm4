"""
Camera on-demand logic: sessions, desired state, MediaMTX sync, events and
fuel-request hooks. Design: ATD_Server/CAMERA_MANAGEMENT_DESIGN.md

Rule:
    camera ENABLED  <=>  is_active
                         AND stream_mode != Disabled
                         AND (stream_mode == Always On OR it has an active session)

Active session: ended_at IS NULL AND expires_at > now().
"""
import logging
import re
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from . import mediamtx
from .mediamtx import MediaMTXError
from .models import (
    Camera,
    CameraEvent,
    CameraStreamSession,
    DispenserUnits,
    OrderFuelDispensingDetails,
    RequestFuelDispensingDetails,
)

log = logging.getLogger(__name__)

RTMP_PATH_RE = re.compile(r"^[A-Za-z0-9_-]+(/[A-Za-z0-9_-]+)*$")

STREAM_MODE_ON_DEMAND = 0
STREAM_MODE_ALWAYS_ON = 1
STREAM_MODE_DISABLED = 2

# RequestFuelDispensingDetails.request_status
STATUS_HARDWARE_RECEIVED = 1
STATUS_DISPENSING = 2
FINAL_STATUS_END_REASON = {
    3: "request_completed",
    4: "request_interrupted",
    5: "request_failed",
}


# --- helpers ---------------------------------------------------------------

def rtmp_publish_url(camera):
    return f"{settings.CAMERA_PUBLIC_RTMP_BASE.rstrip('/')}/{camera.rtmp_path}"


def default_webrtc_url(rtmp_path):
    return f"{settings.CAMERA_PUBLIC_WEBRTC_BASE.rstrip('/')}/{rtmp_path}/"


def log_event(camera, event, details=None, user_id=None):
    try:
        CameraEvent.objects.create(
            camera=camera,
            event=event,
            details=details or {},
            user_id=user_id,
            created_at=timezone.now(),
        )
    except Exception:  # logging must never break the caller
        log.exception("camera event log failed: %s", event)


def active_sessions(camera=None):
    qs = CameraStreamSession.objects.filter(ended_at__isnull=True, expires_at__gt=timezone.now())
    if camera is not None:
        qs = qs.filter(camera=camera)
    return qs


def is_desired_enabled(camera):
    if not camera.is_active or camera.stream_mode == STREAM_MODE_DISABLED:
        return False
    if camera.stream_mode == STREAM_MODE_ALWAYS_ON:
        return True
    return active_sessions(camera).exists()


# --- worker heartbeat ---------------------------------------------------------
# The worker touches a file in the shared media folder every cycle; the API
# container reads its mtime. No DB table or cache needed.

WORKER_STALE_AFTER_S = 60


def _heartbeat_file():
    import os
    return os.path.join(settings.MEDIA_ROOT, settings.CAMERA_SNAPSHOT_DIR, ".camera_worker.heartbeat")


def touch_worker_heartbeat():
    import os
    path = _heartbeat_file()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(timezone.now().isoformat())


def worker_status():
    import os
    try:
        mtime = os.path.getmtime(_heartbeat_file())
    except OSError:
        return {"worker_alive": False, "worker_last_seen": None}
    from datetime import datetime, timezone as dt_timezone
    last = datetime.fromtimestamp(mtime, tz=dt_timezone.utc)
    age = (timezone.now() - last).total_seconds()
    return {"worker_alive": age <= WORKER_STALE_AFTER_S, "worker_last_seen": last.isoformat(), "worker_age_s": int(age)}


# --- MediaMTX sync -----------------------------------------------------------

def apply_path_state(camera, enabled, rtmp_path=None):
    """Make MediaMTX match `enabled` for one camera. Returns True on success."""
    path = rtmp_path or camera.rtmp_path
    try:
        if enabled:
            if mediamtx.add_path(path):
                log_event(camera, "path_enabled", {"path": path})
        else:
            if mediamtx.delete_path(path):
                log_event(camera, "path_disabled", {"path": path})
        return True
    except MediaMTXError as e:
        log_event(camera, "mediamtx_error", {"path": path, "action": "enable" if enabled else "disable", "error": str(e)})
        return False


def reconcile_camera(camera):
    """Immediate sync for one camera (called right after a change)."""
    return apply_path_state(camera, is_desired_enabled(camera))


def expire_sessions():
    """End sessions past expires_at. Fuel-request sessions whose request reached a
    final status get the matching end reason instead of 'timeout'."""
    now = timezone.now()
    ended = []
    for s in CameraStreamSession.objects.filter(ended_at__isnull=True, expires_at__lte=now).select_related("request", "order_request"):
        reason = "timeout"
        if s.reason == "fuel_request":
            req = s.request or s.order_request
            if req is not None and req.request_status in FINAL_STATUS_END_REASON:
                reason = FINAL_STATUS_END_REASON[req.request_status]
        s.ended_at = now
        s.end_reason = reason
        s.save(update_fields=["ended_at", "end_reason"])
        log_event(s.camera, "session_ended", {"session_id": s.id, "reason": s.reason, "end_reason": reason, "transaction_id": s.transaction_id})
        ended.append(s)
    return ended


def reconcile_all():
    """Full sync, run by the worker every CAMERA_RECONCILE_INTERVAL_S.
    Only paths of registered cameras are touched."""
    expire_sessions()
    try:
        configured = set(mediamtx.list_config_paths())
    except MediaMTXError as e:
        log.warning("reconcile: MediaMTX unreachable: %s", e)
        return {"ok": False, "error": str(e)}

    changed = 0
    for camera in Camera.objects.all():
        want = is_desired_enabled(camera)
        have = camera.rtmp_path in configured
        if want != have:
            if apply_path_state(camera, want):
                changed += 1
    return {"ok": True, "changed": changed}


# --- live status -------------------------------------------------------------

def _live_from_path(p):
    if not p or not p.get("ready"):
        return None
    source = p.get("source") or {}
    return {
        "ready_time": p.get("readyTime"),
        "tracks": p.get("tracks"),
        "bytes_received": p.get("bytesReceived", 0),
        "readers": len(p.get("readers", [])),
        "source_type": source.get("type"),
    }


def live_status_map(cameras):
    """{camera_id: {"live_status": ..., "live": {...}|None}} with 2 MediaMTX calls total."""
    result = {}
    try:
        configured = set(mediamtx.list_config_paths())
        live_paths = {p["name"]: p for p in mediamtx.list_paths()}
    except MediaMTXError:
        return {c.id: {"live_status": "mediamtx_unreachable", "live": None} for c in cameras}
    for c in cameras:
        live = _live_from_path(live_paths.get(c.rtmp_path))
        if live:
            status_ = "live"
        elif c.rtmp_path in configured:
            status_ = "waiting"
        else:
            status_ = "disabled"
        result[c.id] = {"live_status": status_, "live": live}
    return result


def camera_status(camera):
    st = live_status_map([camera])[camera.id]
    if st["live"]:
        try:
            conns = [c for c in mediamtx.list_rtmp_conns() if c.get("path") == camera.rtmp_path]
            if conns:
                st["live"]["remote_addr"] = conns[0].get("remoteAddr")
        except MediaMTXError:
            pass
    st["desired_enabled"] = is_desired_enabled(camera)
    st["active_sessions"] = [
        {
            "id": s.id,
            "reason": s.reason,
            "user_id": s.user_id,
            "transaction_id": s.transaction_id,
            "started_at": s.started_at,
            "expires_at": s.expires_at,
        }
        for s in active_sessions(camera).order_by("started_at")
    ]
    return st


# --- sessions ----------------------------------------------------------------

def start_session(camera, reason, ttl_s, user_id=None, request=None, order_request=None, transaction_id=None, reconcile=True):
    now = timezone.now()
    s = CameraStreamSession.objects.create(
        camera=camera,
        reason=reason,
        user_id=user_id,
        request=request,
        order_request=order_request,
        dispenser_unit_id=camera.dispenser_unit_id,
        transaction_id=transaction_id,
        started_at=now,
        expires_at=now + timedelta(seconds=ttl_s),
        last_heartbeat_at=now if reason == "live_view" else None,
    )
    log_event(camera, "session_started", {"session_id": s.id, "reason": reason, "transaction_id": transaction_id}, user_id)
    if reconcile:
        reconcile_camera(camera)
    return s


def heartbeat(session, ttl_s):
    now = timezone.now()
    session.expires_at = now + timedelta(seconds=ttl_s)
    session.last_heartbeat_at = now
    session.save(update_fields=["expires_at", "last_heartbeat_at"])
    return session


def end_session(session, end_reason, user_id=None, reconcile=True):
    if session.ended_at is not None:
        return session
    session.ended_at = timezone.now()
    session.end_reason = end_reason
    session.save(update_fields=["ended_at", "end_reason"])
    log_event(session.camera, "session_ended", {"session_id": session.id, "reason": session.reason, "end_reason": end_reason, "transaction_id": session.transaction_id}, user_id)
    if reconcile:
        reconcile_camera(session.camera)
    return session


def end_all_sessions(camera, end_reason, user_id=None):
    for s in active_sessions(camera):
        end_session(s, end_reason, user_id=user_id, reconcile=False)


# --- fuel-request hooks (called from the websocket consumer) -----------------
# These run off the websocket's critical path (fired as background tasks) and
# swallow every error: a camera problem must never affect dispensing.

def _find_request(transaction_id):
    req = RequestFuelDispensingDetails.objects.filter(transaction_id=transaction_id).first()
    if req is not None:
        return req, None
    return None, OrderFuelDispensingDetails.objects.filter(transaction_id=transaction_id).first()


def on_fuel_request_started(imei, transaction_id):
    """type 1 start command (web, or sent internally for type 71 tag scans)."""
    try:
        if not transaction_id:
            return
        req, order = _find_request(str(transaction_id))
        if not imei:  # fall back to the request row's IMEI
            imei = getattr(req or order, "dispenser_imeinumber", None)
        if not imei:
            return
        dispenser = DispenserUnits.objects.filter(imei_number=str(imei)).first()
        if dispenser is None:
            return
        cameras = Camera.objects.filter(dispenser_unit=dispenser, is_active=True).exclude(stream_mode=STREAM_MODE_DISABLED)
        if not cameras:
            return
        for camera in cameras:
            existing = active_sessions(camera).filter(reason="fuel_request", transaction_id=str(transaction_id)).first()
            if existing:
                heartbeat(existing, settings.CAMERA_FUEL_REQUEST_START_TTL_S)
                continue
            start_session(
                camera,
                "fuel_request",
                settings.CAMERA_FUEL_REQUEST_START_TTL_S,
                request=req,
                order_request=order,
                transaction_id=str(transaction_id),
            )
    except Exception:
        log.exception("camera hook on_fuel_request_started failed (txn=%s)", transaction_id)


def on_fuel_request_status(transaction_id, request_status):
    """Status change from type 11 / type 41 (update_request_status_from_status_code)."""
    try:
        if not transaction_id:
            return
        sessions = list(active_sessions().filter(reason="fuel_request", transaction_id=str(transaction_id)))
        if not sessions:
            return
        now = timezone.now()
        if request_status in (STATUS_HARDWARE_RECEIVED, STATUS_DISPENSING):
            for s in sessions:
                heartbeat(s, settings.CAMERA_FUEL_REQUEST_TTL_S)
        elif request_status in FINAL_STATUS_END_REASON:
            # Keep the camera a few seconds so the worker captures the final
            # stage snapshot; expire_sessions() then ends it with the right reason.
            grace_until = now + timedelta(seconds=settings.CAMERA_FINAL_GRACE_S)
            for s in sessions:
                if s.expires_at > grace_until:
                    s.expires_at = grace_until
                    s.save(update_fields=["expires_at"])
    except Exception:
        log.exception("camera hook on_fuel_request_status failed (txn=%s)", transaction_id)


# --- camera lifecycle ----------------------------------------------------------

def validate_rtmp_path(path):
    path = (path or "").strip()
    if not RTMP_PATH_RE.match(path):
        return None
    return path


RTMP_PATH_PREFIX = "rtmp_push"


def _path_part(value):
    """Make a value safe for a MediaMTX path segment (upper-cased, like serial/model numbers):
    anything outside A-Z 0-9 _ - becomes '-'."""
    return re.sub(r"[^A-Z0-9_-]+", "-", (value or "").strip().upper()).strip("-")


def generate_rtmp_path(model_number, serial_number):
    """rtmp_push/<model>_<serial>, e.g. rtmp_push/DS-2CD1023_K12345678.
    Keep in sync with generateRtmpPath() in the frontend (camera-assign-fields.tsx)."""
    model, serial = _path_part(model_number), _path_part(serial_number)
    name = "_".join(p for p in (model, serial) if p)
    if not name:
        return None
    return f"{RTMP_PATH_PREFIX}/{name}"[:150]


def on_camera_saved(camera, old_rtmp_path=None, user_id=None):
    """After create/update: move the path if it changed, then sync."""
    if old_rtmp_path and old_rtmp_path != camera.rtmp_path:
        apply_path_state(camera, False, rtmp_path=old_rtmp_path)
    reconcile_camera(camera)


def on_camera_deleting(camera, user_id=None):
    """Before delete: end sessions and remove the path."""
    with transaction.atomic():
        end_all_sessions(camera, "camera_deleted", user_id=user_id)
    apply_path_state(camera, False)
