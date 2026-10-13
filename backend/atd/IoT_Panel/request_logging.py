"""
Log every HTTP request through Python's logging, so the live log viewer shows the
same traffic the terminal does without depending on the server's stdout being
captured.

Daphne/runserver already print an access line per request, but that goes to
stdout only. This middleware emits an equivalent line through the `IoT_Panel.http`
logger, which the file handler in settings.LOGGING picks up, so the log is
complete however the process was started.

Request and response bodies are included for the API paths only, truncated, and
are passed through app_logs.redact before being written -- so a token in a login
body never reaches the file in the first place.
"""

import json
import time
import logging

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from . import app_logs, log_presence

log = logging.getLogger("IoT_Panel.http")

# Health checks and static assets would drown out everything else. The log
# endpoint itself is skipped too: the viewer polls every couple of seconds, and
# logging those calls would fill the log with the act of reading the log.
_SKIP_PREFIXES = ("/static/", "/media/", "/favicon.ico", "/api/app-logs")


def _should_log_body(path):
    # Reading and redacting a body is the costly part; the record would be
    # filtered out anyway when nobody has the log page open.
    return (
        path.startswith("/api/")
        and getattr(settings, "LOG_HTTP_BODIES", True)
        and log_presence.is_watched()
    )


def _is_json(content_type):
    return "application/json" in (content_type or "").lower()


def _loggable_request_body(request):
    """
    Only JSON request bodies are logged.

    multipart/form-data is deliberately excluded: it carries file uploads, and a
    credential in it appears as `name="password"` followed by a blank line and
    the value, which redact() cannot match -- a login POST would have written the
    password to the log in clear. Form-urlencoded is excluded for the same
    reason. If it cannot be redacted reliably, it is not logged.
    """
    if not _is_json(request.META.get("CONTENT_TYPE")):
        return ""
    return _body_text(getattr(request, "body", b""))


def _trim(text, limit=None):
    limit = limit or getattr(settings, "LOG_BODY_MAX_CHARS", 2000)
    if text is None:
        return ""
    text = str(text)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}… (+{len(text) - limit} chars)"


def _body_text(raw):
    if not raw:
        return ""
    try:
        decoded = raw.decode("utf-8", errors="replace")
    except Exception:  # pragma: no cover - defensive
        return "<unreadable body>"
    # Collapse pretty-printed JSON onto one line so a request is one log line.
    try:
        return json.dumps(json.loads(decoded), separators=(",", ":"))
    except (ValueError, TypeError):
        return decoded.replace("\n", " ")


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._atd_started = time.monotonic()
        path = request.path
        if path.startswith(_SKIP_PREFIXES):
            return None
        if _should_log_body(path) and request.method in ("POST", "PUT", "PATCH"):
            # request.body is safe to touch here: DRF re-reads from the cached
            # copy Django keeps once it has been accessed.
            body = _loggable_request_body(request)
            if body:
                log.info(
                    "HTTP %-6s   ·   %s   body %s",
                    request.method,
                    path,
                    app_logs.redact(_trim(body)),
                )
        return None

    def process_response(self, request, response):
        path = request.path
        if path.startswith(_SKIP_PREFIXES):
            return response

        started = getattr(request, "_atd_started", None)
        took_ms = f"{(time.monotonic() - started) * 1000:.0f}ms" if started else "?"
        user_id = getattr(getattr(request, "user", None), "id", None)
        query = request.META.get("QUERY_STRING") or ""
        target = f"{path}?{query}" if query else path

        # Fixed-width method and a right-aligned duration so a column of these
        # lines up in the terminal and in the viewer:
        #   HTTP GET     200   12ms  /api/vin-vehicle/get/4/   user 6789
        line = "HTTP %-6s %s %6s  %s   %s"
        args = (
            request.method,
            response.status_code,
            took_ms,
            app_logs.redact(target),
            f"user {user_id}" if user_id else "anon",
        )

        # A failing response is the thing an operator is looking for, so give it
        # a level that survives the viewer's "errors only" filter.
        if response.status_code >= 500:
            log.error(line, *args)
        elif response.status_code >= 400:
            log.warning(line, *args)
        else:
            log.info(line, *args)

        # Only API error payloads, never Django's HTML debug/404 pages -- those
        # are hundreds of characters of markup that say nothing useful.
        if (
            _should_log_body(path)
            and response.status_code >= 400
            and _is_json(response.get("Content-Type"))
        ):
            content = getattr(response, "content", b"")
            body = _body_text(content)
            if body:
                log.warning(
                    "HTTP %-6s   ·   %s   replied %s",
                    request.method,
                    path,
                    app_logs.redact(_trim(body)),
                )

        return response

    def process_exception(self, request, exception):
        log.exception(
            "HTTP %-6s   ·   %s   raised %s",
            request.method,
            request.path,
            type(exception).__name__,
        )
        return None
