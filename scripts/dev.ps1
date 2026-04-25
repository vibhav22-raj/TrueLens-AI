param(
    [ValidateSet("next", "streamlit")]
    [string]$Stack = "next"
)

$ErrorActionPreference = "Stop"

function Start-BackendApi {
    $backendPath = Join-Path $PSScriptRoot "..\backend-api"
    Write-Host "Starting backend (FastAPI)..." -ForegroundColor Cyan
    Start-Process -WorkingDirectory $backendPath -FilePath "powershell" -ArgumentList @(
        "-NoExit",
        "-Command",
        "uvicorn app.main:app --reload"
    )
}

function Start-FrontendNext {
    $frontendPath = Join-Path $PSScriptRoot "..\frontend-next"
    Write-Host "Starting frontend (Next.js)..." -ForegroundColor Cyan
    Start-Process -WorkingDirectory $frontendPath -FilePath "powershell" -ArgumentList @(
        "-NoExit",
        "-Command",
        "npm run dev"
    )
}

function Start-BackendLegacy {
    $backendPath = Join-Path $PSScriptRoot "..\backend"
    Write-Host "Starting backend (FastAPI legacy)..." -ForegroundColor Cyan
    Start-Process -WorkingDirectory $backendPath -FilePath "powershell" -ArgumentList @(
        "-NoExit",
        "-Command",
        "uvicorn backend.main:app --reload"
    )
}

function Start-FrontendStreamlit {
    $frontendPath = Join-Path $PSScriptRoot "..\frontend"
    Write-Host "Starting frontend (Streamlit)..." -ForegroundColor Cyan
    Start-Process -WorkingDirectory $frontendPath -FilePath "powershell" -ArgumentList @(
        "-NoExit",
        "-Command",
        "streamlit run streamlit_app.py"
    )
}

if ($Stack -eq "next") {
    Start-BackendApi
    Start-FrontendNext
    Write-Host "Done. Backend: http://localhost:8000 | Frontend: http://localhost:3000" -ForegroundColor Green
}
else {
    Start-BackendLegacy
    Start-FrontendStreamlit
    Write-Host "Done. Backend: http://localhost:8000 | Frontend: http://localhost:8501" -ForegroundColor Green
}
