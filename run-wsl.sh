#!/usr/bin/env bash
# Run the ATD backend on WSL, listening on all interfaces.
# Port-forward from Windows is handled by expose-wsl.ps1 (run from PowerShell as Admin).

#
#   ./run-wsl.sh              # port 8000, reloads on file changes
#   ./run-wsl.sh 8080         # or pick a port
#   ./run-wsl.sh --no-reload  # run bare daphne, exactly as production does

set -e

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

cd "$(dirname "$0")/backend/atd"

# Activate venv
source ../../env/bin/activate

# Show the WSL IP so you can confirm port forwarding
WSL_IP=$(hostname -I | awk '{print $1}')
echo "================================================"
echo "  WSL IP:        $WSL_IP"
echo "  Listening on:  0.0.0.0:$PORT"
echo "  HTTP:          http://192.168.1.16:$PORT/"
echo "  Swagger:       http://192.168.1.16:$PORT/api/docs/"
echo "  WebSocket:     ws://192.168.1.16:$PORT/ws/dispenser-control/"
echo "================================================"
echo ""
echo "If you can't reach the Windows IP, run from elevated PowerShell:"
echo "  .\\expose-wsl.ps1 -Port $PORT"
echo ""

if [ "$RELOAD" -eq 1 ]; then
    # `daphne` is first in INSTALLED_APPS, so it replaces Django's runserver with
    # its own ASGI one: same WebSocket support as bare daphne, plus autoreload.
    echo "Auto-reload is ON. Use --no-reload for bare daphne."
    echo ""
    exec python manage.py runserver "0.0.0.0:$PORT"
fi

# Daphne is required for ASGI + WebSocket support
echo "Auto-reload is OFF: restart manually after every .py change."
echo ""
exec daphne -b 0.0.0.0 -p "$PORT" atd.asgi:application
