param (
    [int]$bport = 8000,
    [int]$fport = 5173
)

Write-Host "Starting Backend (FastAPI) on port $bport..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit -Command `"& .\.venv\Scripts\Activate.ps1; uvicorn backend.main:app --reload --host 0.0.0.0 --port $bport`""

Write-Host "Starting Frontend (Svelte) on port $fport..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit -Command `"cd frontend; `$env:VITE_API_BASE='http://127.0.0.1:$bport/api'; npm run dev -- --port $fport`""

Write-Host "Servers started in two new windows!" -ForegroundColor Cyan
