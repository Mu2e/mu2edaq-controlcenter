<#
.SYNOPSIS
    Standardized Mu2e control-room start script (PowerShell port of
    start-mu2edaq-controlcenter.sh) for the Control Center.

.DESCRIPTION
    Honors CRS_PORT_CMD as the status-server port (default 9876). Probes for a
    working GPU/OpenGL context (QWebEngineView needs one) and falls back to
    software rendering if absent, launches the app in the background with a pid
    file, waits for the status server, and pings the status indicators.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$Venv    = Join-Path $ScriptDir 'venv'
$VenvPy  = Join-Path $Venv 'Scripts\python.exe'
$Send    = Join-Path $ScriptDir 'src\controlcenter_send.py'
$Config  = Join-Path $ScriptDir 'config\controlcenter.yaml'
$PidFile = Join-Path $ScriptDir 'controlcenter.pid'
if (-not $env:CRS_PORT_CMD) { $env:CRS_PORT_CMD = '9876' }

if (-not (Test-Path $VenvPy)) {
    Write-Error 'virtual environment not found. Run .\bootstrap.ps1 first.'
    exit 1
}

function Test-ProcessAlive([int]$ProcId) {
    return [bool](Get-Process -Id $ProcId -ErrorAction SilentlyContinue)
}

# 2. Detect GPU/OpenGL support (QWebEngineView / Chromium needs one). Probe with
#    a fast isolated Qt OpenGL context creation before launching the full app.
$probe = @'
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QOpenGLContext, QOffscreenSurface
app = QApplication(sys.argv)
surface = QOffscreenSurface(); surface.create()
ctx = QOpenGLContext()
ok = ctx.create() and ctx.makeCurrent(surface)
sys.exit(0 if ok else 1)
'@
Write-Host 'Checking for GPU/OpenGL support...'
& $VenvPy -c $probe 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host '  GPU/OpenGL context OK; using hardware-accelerated rendering.'
} else {
    Write-Host '  No usable GPU/OpenGL context detected; forcing software rendering.'
    $env:QT_QUICK_BACKEND = 'software'
    $env:QTWEBENGINE_CHROMIUM_FLAGS = '--disable-gpu --enable-unsafe-swiftshader'
}

# 3. Launch the application in the background.
Write-Host 'Starting Control Center...'
$proc = Start-Process -FilePath $VenvPy `
    -ArgumentList @((Join-Path $ScriptDir 'src\controlcenter.py'), '--config', $Config) `
    -WorkingDirectory $ScriptDir -WindowStyle Hidden -PassThru
Set-Content -Path $PidFile -Value $proc.Id -Encoding ascii
Write-Host "  PID: $($proc.Id)"

# 4. Wait for the status server to accept connections.
$connectProbe = @"
import socket, sys
try:
    s = socket.create_connection(('127.0.0.1', $($env:CRS_PORT_CMD)), timeout=1); s.close(); sys.exit(0)
except OSError:
    sys.exit(1)
"@
$maxWait = 15; $waited = 0
Write-Host "Waiting for status server on 127.0.0.1:$($env:CRS_PORT_CMD)..."
while ($true) {
    & $VenvPy -c $connectProbe 2>$null
    if ($LASTEXITCODE -eq 0) { break }
    if (-not (Test-ProcessAlive $proc.Id)) { Write-Error 'process died while waiting for status server'; exit 1 }
    if ($waited -ge $maxWait) {
        Write-Error "status server did not start within ${maxWait}s"
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        exit 1
    }
    Start-Sleep -Seconds 1; $waited++
}
Write-Host "  Server ready (${waited}s)."

# 5. Ping each status indicator.
Write-Host 'Pinging status indicators...'
foreach ($indicator in @('DAQ', 'Trigger', 'Misc', 'Storage')) {
    Write-Host -NoNewline "  ${indicator}: "
    if ((Test-ProcessAlive $proc.Id)) {
        & $VenvPy $Send ping | Out-Null
        if ($LASTEXITCODE -eq 0) { Write-Host 'ok' } else { Write-Host 'FAILED' }
    } else { Write-Host 'FAILED' }
}

if (-not (Test-ProcessAlive $proc.Id)) { Write-Error 'process died during startup'; exit 1 }
Write-Host "Control Center is running (PID $($proc.Id))."
