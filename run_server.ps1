#!/usr/bin/env pwsh
# Smart server launcher - Automatically kills existing process on port 8000

param(
    [int]$Port = 8000,
    [switch]$NoReload
)

function Get-ProcessOnPort {
    param([int]$Port)
    try {
        $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                     Select-Object -ExpandProperty OwningProcess -Unique
        return $processes
    }
    catch {
        return $null
    }
}

function Kill-ProcessOnPort {
    param([int]$Port)
    $pids = Get-ProcessOnPort -Port $Port
    
    if ($pids) {
        foreach ($p in $pids) {
            try {
                Write-Host "Killing process $p on port $Port..."
                Stop-Process -Id $p -Force -ErrorAction Stop
                Start-Sleep -Milliseconds 500
                Write-Host "Process killed, port $Port released"
                return $true
            }
            catch {
                Write-Host "Failed to kill process $p"
            }
        }
    }
    return $false
}

# Main
Write-Host "=========================================="
Write-Host "SMART SERVER LAUNCHER"
Write-Host "=========================================="

# Check port
$pids = Get-ProcessOnPort -Port $Port
if ($pids) {
    Write-Host "Port $Port is in use, killing..."
    Kill-ProcessOnPort -Port $Port
    Start-Sleep -Seconds 1
}

Write-Host "Port $Port is free"
Write-Host "Starting server..."
Write-Host ""

# Build args
$uvicornArgs = @(
    "app:app",
    "--host", "0.0.0.0",
    "--port", $Port.ToString()
)

if (-not $NoReload) {
    $uvicornArgs += "--reload"
}

Write-Host "=========================================="
Write-Host "Server: http://localhost:$Port"
Write-Host "Press CTRL+C to stop"
Write-Host "=========================================="
Write-Host ""

# Start
& python -m uvicorn @uvicornArgs

