"""
Is anyone watching the live log?

The verbose logging in this project -- every WebSocket frame, every API request
body -- exists for the live log page. Producing it when nobody has that page
open costs CPU on the hot path and fills the disk for no reader, so it is gated
on viewer presence.

The signal is the mtime of a marker file, touched on every poll of
api/app-logs/. A file is used rather than the cache framework because no shared
cache is configured (LocMemCache is per-process) and the HTTP worker and the
WebSocket consumer are not guaranteed to be the same process. A stat() is about
a microsecond and the result is memoised for a second, so the per-frame cost is
effectively nil.
"""

import os
import time

from django.conf import settings

# How long after the last poll a viewer is still considered present. The page
# polls every 2 s, so this tolerates a couple of missed ticks without flapping.
WATCH_WINDOW_S = 10

# Re-stat at most this often; between checks the previous answer stands.
_CHECK_INTERVAL_S = 1.0

_cache = {"checked_at": 0.0, "watched": False}


def _marker_path():
    directory = getattr(settings, "APP_LOG_DIR", None)
    if directory is None:
        return None
    return os.path.join(str(directory), ".viewer-heartbeat")


def touch():
    """Record that a viewer just asked for log output."""
    path = _marker_path()
    if not path:
        return
    try:
        with open(path, "a"):
            os.utime(path, None)
    except OSError:
        return
    # Make the new state visible immediately rather than up to a second later,
    # so the first frame after opening the page is already captured.
    _cache["checked_at"] = time.monotonic()
    _cache["watched"] = True


def is_watched():
    """True when the log page was polled within WATCH_WINDOW_S."""
    if not getattr(settings, "LOG_ONLY_WHEN_WATCHED", True):
        return True

    now = time.monotonic()
    if now - _cache["checked_at"] < _CHECK_INTERVAL_S:
        return _cache["watched"]

    path = _marker_path()
    watched = False
    if path:
        try:
            watched = (time.time() - os.path.getmtime(path)) <= WATCH_WINDOW_S
        except OSError:
            watched = False

    _cache["checked_at"] = now
    _cache["watched"] = watched
    return watched
