#!/usr/bin/env bash
# Run the ATD backend on macOS, listening on all interfaces.
#
#   ./run.sh              # port 8000, reloads on file changes
#   ./run.sh 8080         # or pick a port
#   ./run.sh --no-reload  # run bare daphne, exactly as production does
#
# Sets up the venv and installs requirements on first run, then starts the
# server. Use run-wsl.sh instead when working under WSL.

set -euo pipefail

PORT=8000
RELOAD=1

for arg in "$@"; do
    case "$arg" in
        --no-reload) RELOAD=0 ;;
        --reload)    RELOAD=1 ;;
        ''|*[!0-9]*) echo "Unknown argument: $arg" >&2; exit 1 ;;
        *)           PORT="$arg" ;;
    esac
done

ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/env"
APP="$ROOT/backend/atd"

# mysqlclient builds against Homebrew's keg-only MySQL libs, which are not on
# the default pkg-config search path.
if [ -d /opt/homebrew/opt/mysql-client/lib/pkgconfig ]; then
    export PKG_CONFIG_PATH="/opt/homebrew/opt/mysql-client/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
    export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"
fi

# First run: build the venv.
if [ ! -x "$VENV/bin/python" ]; then
    echo "==> Creating virtualenv at env/"
    python3 -m venv "$VENV"
fi

# Install requirements whenever daphne is missing (fresh or half-built venv).
if [ ! -x "$VENV/bin/daphne" ]; then
    echo "==> Installing dependencies (first run, takes a few minutes)"
    "$VENV/bin/pip" install --upgrade pip
    "$VENV/bin/pip" install -r "$APP/requirements.txt"
fi

cd "$APP"

# Fail fast on a bad settings/urls/models change instead of half-starting.
echo "==> Checking project"
"$VENV/bin/python" manage.py check

# A stale server on the port makes daphne die with a confusing bind error.
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo ""
    echo "ERROR: port $PORT is already in use. Free it with:"
    echo "  lsof -nP -iTCP:$PORT -sTCP:LISTEN"
    echo "  kill <PID>"
    echo "...or start on another port:  ./run.sh 8080"
    exit 1
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo 127.0.0.1)"

echo "================================================"
echo "  Listening on:  0.0.0.0:$PORT"
echo "  HTTP:          http://localhost:$PORT/"
echo "  Swagger:       http://localhost:$PORT/api/docs/"
echo "  Admin:         http://localhost:$PORT/admin/"
echo "  WebSocket:     ws://localhost:$PORT/ws/dispenser-control/"
echo "  On the LAN:    http://$LAN_IP:$PORT/"
echo "================================================"
echo ""
if [ "$RELOAD" -eq 1 ]; then
    echo "Auto-reload is ON: edits to .py files restart the server automatically."
    echo "Use --no-reload to run bare daphne, the way production does."
else
    echo "Auto-reload is OFF: restart manually after every .py change."
fi
echo "Ctrl+C to stop. Add new hosts to CORS_ALLOWED_ORIGINS in atd/settings.py."
echo ""

if [ "$RELOAD" -eq 1 ]; then
    # `daphne` is first in INSTALLED_APPS, so it replaces Django's runserver with
    # its own ASGI one: WebSockets are served exactly as under bare daphne, and
    # the autoreloader comes along for free. It is a development server -- the
    # Dockerfile still launches daphne directly.
    exec "$VENV/bin/python" manage.py runserver "0.0.0.0:$PORT"
fi

# Daphne, not Django's WSGI runserver: this app serves WebSockets and needs ASGI.
exec "$VENV/bin/daphne" -b 0.0.0.0 -p "$PORT" atd.asgi:application
