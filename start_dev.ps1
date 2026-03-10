param (
    [int]$bport = 8000,
    [int]$fport = 3000
)

function Get-FreePort {
    param([int]$StartingPort)
    $port = $StartingPort
    while ($true) {
        Write-Host "Checking port $port... " -NoNewline
        try {
            # Try to bind to IPv6Any on the port (covers IPv4 and IPv6)
            $tcpListener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::IPv6Any, $port)
            $tcpListener.Start()
            $tcpListener.Stop()
            
            # Double check with Get-NetTCPConnection for OS-level confirmation
            $occupied = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
            if (-not $occupied) {
                Write-Host "Available!" -ForegroundColor Green
                return $port
            }
            Write-Host "Occupied (OS reports active connection)." -ForegroundColor Yellow
        }
        catch {
            Write-Host "Occupied (Failed to bind)." -ForegroundColor Yellow
        }
        $port++
    }
}

Write-Host "Finding available ports..." -ForegroundColor Cyan

$actualBport = Get-FreePort -StartingPort $bport
$actualFport = Get-FreePort -StartingPort $fport

$backendUrl = "http://localhost:$actualBport"
$frontendUrl = "http://localhost:$actualFport"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Backend (FastAPI) will be available at: " -NoNewline; Write-Host $backendUrl -ForegroundColor Green
Write-Host "Frontend (Svelte) will be available at: " -NoNewline; Write-Host $frontendUrl -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting servers in THIS terminal. Press CTRL+C to stop both." -ForegroundColor Yellow

# Start Backend in the background without a new window
# Limit reload to the backend directory so it doesn't choke on the .venv junction
$backendProcess = Start-Process powershell -WorkingDirectory $PSScriptRoot -ArgumentList "-NoProfile -Command `"& .\.venv\Scripts\Activate.ps1; python -m uvicorn backend.main:app --reload --reload-dir backend --host 0.0.0.0 --port $actualBport`"" -NoNewWindow -PassThru

# Ensure the backend process is killed when the script stops or is interrupted
try {
    # Start Frontend in the foreground
    Push-Location frontend
    if (-not (Test-Path "node_modules")) {
        Write-Host "First time in this worktree? Installing frontend dependencies..." -ForegroundColor Yellow
        npm install
    }
    $env:VITE_API_BASE = "$backendUrl/api"
    npm run dev -- --port $actualFport
}
finally {
    Write-Host "`nStopping servers..." -ForegroundColor Yellow
    if ($backendProcess -and !$backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force
    }
    Pop-Location
}
