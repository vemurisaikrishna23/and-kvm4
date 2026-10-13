"""
Tail the backend's own log file for the live log viewer.

Modelled on mediamtx_logs: the caller gets the last N lines on the first call and
then passes the returned cursor back every couple of seconds to receive only
what is new. The cursor carries the file's inode so log rotation is detected and
reported instead of silently replaying an old file.

Why a file and not Django's logging alone: most of this codebase's diagnostics
are `print()` calls in consumers.py (`[GPS REJECT]`, `[FUEL REJECT]`,
`[CONNECT]`, ...), which go to the process's stdout and never reach a logging
handler. run.sh therefore tees stdout/stderr into settings.APP_LOG_FILE, and the
LOGGING config in settings points Django's own loggers at the same file, so one
file holds everything an operator would otherwise read in the terminal.
"""

import os
import re

from django.conf import settings

# Secrets must not travel to a browser just because they were printed on a
# server console. Applied to every line before it leaves this module.
# Order matters: the key/value rule runs first so a value it has already
# replaced is not re-matched by the JWT rule, which produced "<redacted> redacted>".
_REDACTIONS = [
    # key=value and "key": "value" forms for anything sensitive-sounding
    (
        re.compile(
            r"(?i)\b(password|passwd|secret|token|access|refresh|authorization|api[_-]?key)"
            r"(\"?\s*[:=]\s*\"?)([^\s\",}&]+)"
        ),
        r"\1\2<redacted>",
    ),
    # Bearer headers and bare JWTs appearing without a key name
    (re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._\-]{20,}"), r"\1<redacted>"),
    (re.compile(r"\beyJ[A-Za-z0-9._\-]{20,}"), "<jwt redacted>"),
]

# Daphne colourises its access lines, so the file contains escape sequences that
# would render as stray characters in the browser.
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\[m")

MAX_LINES = 2000
DEFAULT_LINES = 300
# Never read more than this much tail in one go, so a huge file cannot be pulled
# into memory by a single request.
_MAX_TAIL_BYTES = 2 * 1024 * 1024


class LogsUnavailable(Exception):
    """The log file is not configured, missing, or not readable."""


def log_path():
    path = getattr(settings, "APP_LOG_FILE", None)
    if not path:
        raise LogsUnavailable("APP_LOG_FILE is not configured.")
    return str(path)


# Running three regexes over every telemetry frame costs more than the rest of
# the log call. Almost no line contains anything sensitive, so a substring scan
# decides whether the regexes are worth running at all.
# Compared against a lowercased line, so every hint must be lowercase -- "eyJ"
# here would never match and a bare JWT would slip through unredacted.
_SENSITIVE_HINTS = (
    "password", "passwd", "secret", "token", "access", "refresh",
    "authorization", "bearer", "api_key", "api-key", "apikey", "eyj",
)


def redact(line):
    if "\x1b" in line or "[m" in line:
        line = _ANSI.sub("", line)
    lowered = line.lower()
    if not any(hint in lowered for hint in _SENSITIVE_HINTS):
        return line
    for pattern, repl in _REDACTIONS:
        line = pattern.sub(repl, line)
    return line


def _inode(path):
    try:
        return os.stat(path).st_ino
    except OSError:
        return None


def _tail(path, lines):
    """Last `lines` lines plus the offset we read up to."""
    size = os.path.getsize(path)
    start = max(0, size - _MAX_TAIL_BYTES)
    with open(path, "rb") as fh:
        fh.seek(start)
        data = fh.read()
    text = data.decode("utf-8", errors="replace")
    if start:
        # The first line is probably cut in half; drop it.
        text = text.split("\n", 1)[-1]
    out = text.splitlines()
    return out[-lines:], size


def _read_from(path, offset):
    size = os.path.getsize(path)
    if offset > size:
        # Truncated in place (e.g. `> atd.log`): start over from the top.
        offset = 0
    with open(path, "rb") as fh:
        fh.seek(offset)
        data = fh.read()
    return data.decode("utf-8", errors="replace").splitlines(), size


def read(cursor=None, initial_lines=DEFAULT_LINES):
    """
    Returns (lines, cursor, rotated).

    `cursor` is "<inode>:<offset>". A changed inode means the file rotated, in
    which case the caller is handed the new file's tail and rotated=True.
    """
    path = log_path()
    if not os.path.exists(path):
        raise LogsUnavailable(
            f"No log file at {path}. Start the server through run.sh so its output is captured."
        )

    inode = _inode(path)
    initial_lines = max(10, min(int(initial_lines), MAX_LINES))

    if not cursor:
        lines, end = _tail(path, initial_lines)
        return [redact(l) for l in lines], f"{inode}:{end}", False

    try:
        prev_inode, prev_offset = cursor.split(":")
        prev_offset = int(prev_offset)
    except (ValueError, AttributeError):
        lines, end = _tail(path, initial_lines)
        return [redact(l) for l in lines], f"{inode}:{end}", False

    if str(inode) != str(prev_inode):
        lines, end = _tail(path, initial_lines)
        return [redact(l) for l in lines], f"{inode}:{end}", True

    lines, end = _read_from(path, prev_offset)
    return [redact(l) for l in lines], f"{inode}:{end}", False


# --- line parsing -------------------------------------------------------------
# Two shapes reach the file: Django's logging format (configured in settings as
# "LEVEL <time> logger: message") and bare print() output, which has no prefix.
# Anything unrecognised is returned as a plain message so nothing is dropped.

_DJANGO_LINE = re.compile(
    r"^(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+"
    r"(?P<time>[\d\-: ,\.]+)\s+(?P<logger>[\w\.\-]+):\s*(?P<message>.*)$"
)
# print() diagnostics in this codebase are tagged like "[GPS REJECT] ..."
_TAGGED = re.compile(r"^\[(?P<tag>[A-Z0-9 _\-/]+)\]\s*(?P<message>.*)$")

_TAG_LEVEL = {
    "ERROR": "ERROR",
    "CRITICAL": "ERROR",
    "FUEL REJECT": "WARNING",
    "GPS REJECT": "WARNING",
    "OMNICOMM SKIP": "WARNING",
    "SKIP PRICE UPDATE": "WARNING",
    "GUN STATUS": "INFO",
}


def parse_line(raw):
    line = (raw or "").rstrip()
    if not line:
        return None

    m = _DJANGO_LINE.match(line)
    if m:
        return {
            "level": m.group("level"),
            "time": m.group("time").strip(),
            "source": m.group("logger"),
            "message": m.group("message"),
            "raw": line,
        }

    m = _TAGGED.match(line)
    if m:
        tag = m.group("tag").strip()
        level = _TAG_LEVEL.get(tag)
        if level is None:
            level = "ERROR" if "ERROR" in tag or "CRITICAL" in tag else "INFO"
        return {
            "level": level,
            "time": None,
            "source": tag,
            "message": m.group("message"),
            "raw": line,
        }

    # Tracebacks and anything else: keep the text, guess the level from content.
    lowered = line.lower()
    if "traceback" in lowered or "error" in lowered or "exception" in lowered:
        level = "ERROR"
    elif "warn" in lowered:
        level = "WARNING"
    else:
        level = "INFO"
    return {"level": level, "time": None, "source": None, "message": line, "raw": line}


def truncate():
    """
    Empty the log file in place.

    Opened in "w" mode rather than deleted: the running server (and `tee`) hold
    open descriptors on this inode, so unlinking it would leave them writing to
    a file nobody can read. Truncating keeps those writers pointed at the same
    inode and they continue at the new end of file.

    Returns the new cursor so a caller can carry on tailing without replaying.
    """
    path = log_path()
    with open(path, "w", encoding="utf-8"):
        pass
    return f"{_inode(path)}:0"
