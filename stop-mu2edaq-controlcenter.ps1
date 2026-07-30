<#
.SYNOPSIS
    Shut down a running Control Center instance cleanly on Windows (PowerShell
    port of stop-mu2edaq-controlcenter.sh): read the pid file (or find the
    process by command line), close it, then force a kill after a timeout.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $ScriptDir 'controlcenter.pid'

function Test-ProcessAlive([int]$ProcId) {
    return [bool](Get-Process -Id $ProcId -ErrorAction SilentlyContinue)
}

# 1. Resolve the PID (pid file, else search by command line via CIM = pgrep -f).
$ProcId = 0
if (Test-Path $PidFile) {
    $raw = (Get-Content $PidFile -Raw).Trim()
    if ($raw -match '^\d+$') { $ProcId = [int]$raw }
} else {
    $match = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'controlcenter\.py' } | Select-Object -First 1
    if ($match) { $ProcId = [int]$match.ProcessId }
}

if ($ProcId -eq 0) {
    Write-Host 'Control Center does not appear to be running.'
    exit 0
}
if (-not (Test-ProcessAlive $ProcId)) {
    Write-Host "No process found with PID $ProcId -- already stopped."
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    exit 0
}

# 2. Close, then force a kill after the timeout.
Write-Host "Stopping Control Center (PID $ProcId)..."
$proc = Get-Process -Id $ProcId -ErrorAction SilentlyContinue
if ($proc) { $proc.CloseMainWindow() | Out-Null }
$maxWait = 10; $waited = 0
while (Test-ProcessAlive $ProcId) {
    if ($waited -ge $maxWait) {
        Write-Host "Process did not exit after ${maxWait}s -- forcing..."
        Stop-Process -Id $ProcId -Force -ErrorAction SilentlyContinue
        break
    }
    Start-Sleep -Seconds 1; $waited++
}

Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
Write-Host 'Control Center stopped.'
