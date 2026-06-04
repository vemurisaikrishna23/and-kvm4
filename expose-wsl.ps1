# Expose a WSL2 service to the Windows LAN via netsh portproxy.
# MUST be run from an ELEVATED PowerShell (Run as Administrator).
#
# Usage:
#   .\expose-wsl.ps1                      # forward port 8000
#   .\expose-wsl.ps1 -Port 8000
#   .\expose-wsl.ps1 -Port 8000 -Remove   # tear down the forward

param(
    [int]$Port = 8000,
    [switch]$Remove
)

# Verify Administrator
$me = [Security.Principal.WindowsIdentity]::GetCurrent()
$isAdmin = (New-Object Security.Principal.WindowsPrincipal $me).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $isAdmin) {
    Write-Error "This script must be run as Administrator (right-click PowerShell -> Run as Administrator)."
    exit 1
}

if ($Remove) {
    Write-Host "Removing port proxy for 0.0.0.0:$Port ..."
    netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=0.0.0.0 | Out-Null
    Remove-NetFirewallRule -DisplayName "WSL ATD $Port" -ErrorAction SilentlyContinue
    Write-Host "Done." -ForegroundColor Green
    exit 0
}

# Get the current WSL2 IP (it changes between reboots)
$wslIp = (wsl -d Ubuntu-22.04 -- hostname -I).Trim().Split(" ")[0]
if (-not $wslIp) {
    Write-Error "Could not detect WSL2 IP. Is WSL running?"
    exit 1
}

Write-Host "Detected WSL2 IP: $wslIp"
Write-Host "Forwarding 0.0.0.0:$Port -> ${wslIp}:$Port"

# Remove any existing rule for this port (so re-runs after WSL reboot just work)
netsh interface portproxy delete v4tov4 listenport=$Port listenaddress=0.0.0.0 2>$null | Out-Null

# Add the new rule
netsh interface portproxy add v4tov4 listenport=$Port listenaddress=0.0.0.0 connectport=$Port connectaddress=$wslIp | Out-Null

# Firewall rule (open the port on the Windows host)
Remove-NetFirewallRule -DisplayName "WSL ATD $Port" -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "WSL ATD $Port" -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null

# Show what we did
Write-Host ""
Write-Host "Current portproxy rules:" -ForegroundColor Cyan
netsh interface portproxy show v4tov4

# Show the Windows IP people will use
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notmatch '^127\.' -and $_.IPAddress -notmatch '^169\.254\.' -and $_.InterfaceAlias -notmatch 'WSL|vEthernet' } |
    Select-Object -First 1).IPAddress

Write-Host ""
Write-Host "Done. Access from any device on your LAN:" -ForegroundColor Green
Write-Host "  http://${lanIp}:$Port/"
Write-Host "  http://${lanIp}:$Port/api/docs/"
Write-Host "  ws://${lanIp}:$Port/ws/dispenser-control/"
