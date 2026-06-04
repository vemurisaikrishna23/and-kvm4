#!/usr/bin/env bash
# Run the ATD backend on WSL, listening on all interfaces.
# Port-forward from Windows is handled by expose-wsl.ps1 (run from PowerShell as Admin).

set -e

PORT="${1:-8000}"

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

# Daphne is required for ASGI + WebSocket support
exec daphne -b 0.0.0.0 -p "$PORT" atd.asgi:application
