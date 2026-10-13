"""
Logging filters.

The live log viewer polls api/app-logs/ every couple of seconds. The middleware
already skips those requests, but the ASGI server writes its own access line per
request (django.channels.server under `manage.py runserver`, daphne.access under
bare daphne), which would scroll the terminal -- and the log file -- with the act
of reading the log. This drops those access lines only.
"""

# Matched against the formatted message, which looks like
#   HTTP GET /api/app-logs/?cursor=... 200 [0.01, 127.0.0.1:52001]
_NOISY_PATHS = ("/api/app-logs",)


class SkipLogViewerAccess:
    """Reject access-log records for the log viewer's own polling endpoint."""

    def filter(self, record):
        try:
            message = record.getMessage()
        except Exception:  # pragma: no cover - never break logging
            return True
        return not any(path in message for path in _NOISY_PATHS)


class OnlyWhenWatched:
    """
    Drop high-volume traffic records while nobody has the live log page open.

    WARNING and above always pass: a failure that happened when no one was
    looking is exactly the thing worth having a record of, and those are rare
    enough to cost nothing. Only the per-request / per-frame INFO chatter is
    gated.
    """

    VERBOSE_LOGGERS = (
        "IoT_Panel.ws",
        "IoT_Panel.http",
        "django.channels.server",
        "daphne",
    )

    def filter(self, record):
        import logging

        from . import log_presence

        if record.levelno >= logging.WARNING:
            return True
        if not record.name.startswith(self.VERBOSE_LOGGERS):
            return True
        return log_presence.is_watched()
