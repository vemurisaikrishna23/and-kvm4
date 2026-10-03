"""
Thin client for the MediaMTX HTTP API (v3).

Only the calls the camera feature needs. Every call has a short timeout and
raises MediaMTXError on any failure, so callers handle a single exception type.
Uses urllib (stdlib) so no extra dependency is needed.
"""
import base64
import json
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings


class MediaMTXError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def _url(path):
    return settings.MEDIAMTX_API_URL.rstrip("/") + path


def _quote_path(name):
    # Path names may contain "/" (e.g. rtmp_push/D001); keep it, escape the rest.
    return urllib.parse.quote(name, safe="/")


def _request(method, path, body=None, ok=(200,)):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(_url(path), data=data, method=method)
    token = base64.b64encode(
        f"{settings.MEDIAMTX_API_USER}:{settings.MEDIAMTX_API_PASS}".encode()
    ).decode()
    req.add_header("Authorization", f"Basic {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=settings.MEDIAMTX_API_TIMEOUT_S) as resp:
            raw = resp.read()
            if resp.status not in ok:
                raise MediaMTXError(f"{method} {path} → HTTP {resp.status}", resp.status)
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode()[:300]
        except Exception:
            pass
        raise MediaMTXError(f"{method} {path} → HTTP {e.code} {detail}".strip(), e.code)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise MediaMTXError(f"{method} {path} → {e}")


def _list(path):
    items, page = [], 0
    while True:
        sep = "&" if "?" in path else "?"
        res = _request("GET", f"{path}{sep}itemsPerPage=500&page={page}") or {}
        items.extend(res.get("items", []))
        page += 1
        if page >= int(res.get("pageCount", 1) or 1):
            return items


# --- config (paths enabled/disabled) -------------------------------------

def list_config_paths():
    """Names of all paths currently configured in MediaMTX (file + API-added)."""
    return [p["name"] for p in _list("/v3/config/paths/list")]


def add_path(name):
    """Enable a camera: add a publisher path. Already existing is not an error."""
    try:
        _request("POST", f"/v3/config/paths/add/{_quote_path(name)}", {"source": "publisher"})
        return True
    except MediaMTXError as e:
        # MediaMTX answers 400 when the path exists; confirm rather than trust the message text.
        if e.status_code == 400 and name in list_config_paths():
            return False
        raise


def delete_path(name):
    """Disable a camera: remove the path (MediaMTX also closes the publisher)."""
    try:
        _request("DELETE", f"/v3/config/paths/delete/{_quote_path(name)}")
        return True
    except MediaMTXError as e:
        if e.status_code == 404:
            return False
        raise


# --- live state ------------------------------------------------------------

def get_path(name):
    """Live state of a path, or None if it has no active stream/config."""
    try:
        return _request("GET", f"/v3/paths/get/{_quote_path(name)}")
    except MediaMTXError as e:
        if e.status_code == 404:
            return None
        raise


def list_paths():
    return _list("/v3/paths/list")


def list_rtmp_conns():
    return _list("/v3/rtmpconns/list")


def kick_rtmp_conn(conn_id):
    _request("POST", f"/v3/rtmpconns/kick/{conn_id}")


def health():
    """Cheap reachability check; returns MediaMTX global config subset."""
    g = _request("GET", "/v3/config/global/get") or {}
    return {
        "reachable": True,
        "rtmp": g.get("rtmp"),
        "rtmpAddress": g.get("rtmpAddress"),
        "webrtc": g.get("webrtc"),
        "authMethod": g.get("authMethod"),
    }
