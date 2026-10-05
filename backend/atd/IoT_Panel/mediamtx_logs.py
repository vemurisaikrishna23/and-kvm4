"""
Read MediaMTX's own log lines (the same lines as `docker logs mediamtx-server`)
for the live log page.

MediaMTX logs to stdout; Docker writes them as JSON lines to
/var/lib/docker/containers/<id>/<id>-json.log and rotates them (10 MB × 3 on
this host: <id>-json.log → .1 → .2 …). That directory is mounted read-only into
the backend container at MEDIAMTX_LOG_DIR (/mediamtx-logs). No MediaMTX change.

Paging uses a cursor "<inode>:<offset>". After a rotation the old file keeps
its inode under a new name (.1), so we finish it before continuing with the
new file, and no lines are lost.
"""
import glob
import json
import os
import re

from django.conf import settings

LINE_RE = re.compile(r"^(\d{4}/\d\d/\d\d \d\d:\d\d:\d\d) (\w{3}) (.*)$")
TAG_RE = re.compile(r"^\[([^\]]+)\]\s*")
PATH_IN_TEXT_RE = re.compile(r"path '([^']+)'")
INITIAL_BYTES_PER_LINE = 400
MAX_READ_BYTES = 2 * 1024 * 1024


class LogsUnavailable(Exception):
    pass


def _log_dir():
    return getattr(settings, "MEDIAMTX_LOG_DIR", "/mediamtx-logs")


def current_log_file():
    files = [f for f in glob.glob(os.path.join(_log_dir(), "*-json.log")) if os.path.isfile(f)]
    if not files:
        raise LogsUnavailable(
            f"No MediaMTX log file in {_log_dir()}. Mount the mediamtx-server Docker log folder read-only "
            "into atd-backend (see DEPLOY_GUIDE.md)."
        )
    return max(files, key=os.path.getmtime)


def _file_with_inode(inode):
    for f in glob.glob(os.path.join(_log_dir(), "*-json.log*")):
        if f.endswith(".gz"):
            continue
        try:
            if os.stat(f).st_ino == inode:
                return f
        except OSError:
            pass
    return None


def parse_line(raw):
    """Docker JSON line → structured MediaMTX log entry (or None)."""
    try:
        obj = json.loads(raw)
    except ValueError:
        return None
    text = (obj.get("log") or "").rstrip("\n")
    if not text:
        return None
    entry = {"time": obj.get("time"), "text": text, "level": None, "tags": [], "component": None,
             "conn": None, "ip": None, "session": None, "path": None, "message": text}
    m = LINE_RE.match(text)
    if not m:
        return entry
    _, level, rest = m.groups()
    entry["level"] = level
    tags = []
    while True:
        t = TAG_RE.match(rest)
        if not t:
            break
        tags.append(t.group(1))
        rest = rest[t.end():]
    entry["tags"] = tags
    entry["message"] = rest
    for tag in tags:
        if tag.startswith("conn "):
            entry["conn"] = tag[5:]
            entry["ip"] = entry["conn"].rsplit(":", 1)[0]
        elif tag.startswith("session "):
            entry["session"] = tag[8:]
        elif tag.startswith("path ") or tag.startswith("muxer "):
            entry["path"] = tag.split(" ", 1)[1]
        elif entry["component"] is None and " " not in tag:
            entry["component"] = tag  # RTMP, WebRTC, HLS, RTSP, API …
    if entry["component"] is None and tags:
        entry["component"] = tags[-1]  # e.g. "RTSP source" after [path x]
    if entry["path"] is None:
        p = PATH_IN_TEXT_RE.search(rest)
        if p:
            entry["path"] = p.group(1)
    return entry


def _read_from(path, offset):
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        if offset > size:
            offset = 0  # truncated
        f.seek(offset)
        data = f.read(MAX_READ_BYTES)
        end = offset + len(data)
    # only complete lines; the rest is read next time
    cut = data.rfind(b"\n")
    if cut < 0:
        return [], offset
    complete = data[: cut + 1]
    return complete.decode("utf-8", errors="replace").splitlines(), offset + len(complete)


def _tail(path, lines):
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        start = max(0, size - lines * INITIAL_BYTES_PER_LINE)
        f.seek(start)
        data = f.read()
    text = data.decode("utf-8", errors="replace").splitlines()
    if start > 0 and text:
        text = text[1:]  # first line is probably partial
    return text[-lines:], size


def read(cursor=None, initial_lines=300):
    """Returns (raw_lines, new_cursor, rotated)."""
    path = current_log_file()
    st = os.stat(path)
    if not cursor:
        raw, end = _tail(path, initial_lines)
        return raw, f"{st.st_ino}:{end}", False
    try:
        inode_s, offset_s = cursor.split(":", 1)
        inode, offset = int(inode_s), int(offset_s)
    except ValueError:
        raw, end = _tail(path, initial_lines)
        return raw, f"{st.st_ino}:{end}", False
    if inode == st.st_ino:
        raw, end = _read_from(path, offset)
        return raw, f"{inode}:{end}", False
    # rotated: finish the old file (now .1), then start the new one from 0
    raw = []
    old = _file_with_inode(inode)
    if old:
        raw, _ = _read_from(old, offset)
    new_raw, end = _read_from(path, 0)
    return raw + new_raw, f"{st.st_ino}:{end}", True


def decode_rtmp_path(path, cameras_by_path=None):
    """Camera identity for a path: exact from a registered camera, otherwise decoded
    from the auto-path format rtmp_push/<MODEL>_<SERIAL> (best effort)."""
    if not path:
        return None
    cam = (cameras_by_path or {}).get(path)
    if cam is not None:
        return {
            "source": "registered",
            "camera_id": cam.id,
            "model_number": cam.model_number,
            "serial_number": cam.serial_number,
            "dispenser_serial_number": getattr(cam.dispenser_unit, "serial_number", None),
        }
    prefix = "rtmp_push/"
    if path.startswith(prefix) and "_" in path[len(prefix):]:
        model, serial = path[len(prefix):].split("_", 1)
        if model and serial:
            return {"source": "decoded", "camera_id": None, "model_number": model, "serial_number": serial,
                    "dispenser_serial_number": None}
    return None
