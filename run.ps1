# ThreatLens AI Professional Dev Runner
# This script manages the FastAPI backend and Vite frontend processes together.

Clear-Host

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[*] ThreatLens AI - Enterprise SIEM & SOC Dashboard Runner" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python and Virtual Environment
Write-Host "[*] Checking Backend Environment..." -ForegroundColor Yellow
$BackendDir = Join-Path $PSScriptRoot "backend"
$VenvDir = Join-Path $BackendDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$UvicornExe = Join-Path $VenvDir "Scripts\uvicorn.exe"

if (!(Test-Path $PythonExe)) {
    Write-Error "Backend Python Virtual Environment (.venv) not found at $VenvDir"
    Write-Host "Please create it and install requirements first." -ForegroundColor Red
    Exit 1
}
Write-Host "[+] Virtual Environment found." -ForegroundColor Green

# 2. Check Node and NPM
Write-Host "[*] Checking Frontend Environment..." -ForegroundColor Yellow
$FrontendDir = Join-Path $PSScriptRoot "frontend"
if (!(Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "node_modules not found. Installing frontend dependencies..." -ForegroundColor Yellow
    Start-Process -NoNewWindow -Wait -FilePath "npm" -ArgumentList "install" -WorkingDirectory $FrontendDir
}
Write-Host "[+] Frontend environment validated." -ForegroundColor Green
Write-Host ""

# 3. Start Backend
Write-Host "[*] Starting FastAPI Backend on http://localhost:8000 ..." -ForegroundColor Cyan
$BackendJob = Start-Job -Name "ThreatLens-Backend" -ScriptBlock {
    param($cwd, $uvicorn)
    Set-Location $cwd
    & $uvicorn app.main:app --port 8000
} -ArgumentList $BackendDir, $UvicornExe

Start-Sleep -Seconds 2

# Check if job is still running
$BackendStatus = Get-Job -Name "ThreatLens-Backend"
if ($BackendStatus.State -ne "Running") {
    Write-Error "Backend failed to start. Logs:"
    Receive-Job -Name "ThreatLens-Backend"
    Exit 1
}
Write-Host "[+] Backend service started successfully." -ForegroundColor Green

# 4. Start Frontend
Write-Host "[*] Starting React Frontend on http://localhost:5173 ..." -ForegroundColor Cyan
$FrontendJob = Start-Job -Name "ThreatLens-Frontend" -ScriptBlock {
    param($cwd)
    Set-Location $cwd
    npm run dev
} -ArgumentList $FrontendDir

Start-Sleep -Seconds 2

# Check if job is still running
$FrontendStatus = Get-Job -Name "ThreatLens-Frontend"
if ($FrontendStatus.State -ne "Running") {
    Write-Error "Frontend failed to start. Cleaning up backend..." -ForegroundColor Red
    Stop-Job -Name "ThreatLens-Backend"
    Remove-Job -Name "ThreatLens-Backend"
    Exit 1
}
Write-Host "[+] Frontend service started successfully." -ForegroundColor Green
Write-Host ""

# 5. Beautiful Banner & Information
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "[+] THREATLENS AI IS NOW RUNNING SUCCESSFULLY!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "[*] SOC Dashboard URL:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "[*] API Documentation:  http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "[*] DEMO CREDENTIALS" -ForegroundColor Yellow
Write-Host "   * Admin Role:      admin@threatlens.ai   /  Admin@1234" -ForegroundColor White
Write-Host "   * Analyst Role:    analyst@threatlens.ai /  Analyst@1234" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to gracefully shut down both services..." -ForegroundColor DarkYellow

try {
    [void][System.Console]::ReadKey($true)
} catch {
    Write-Host "[*] Non-interactive console detected. Running services in background..." -ForegroundColor Cyan
    Write-Host "[*] To stop the services, please terminate this process (Ctrl+C or cancel task)." -ForegroundColor Cyan
    while ($true) {
        Start-Sleep -Seconds 1
    }
}

Write-Host ""
Write-Host "[*] Shutting down services..." -ForegroundColor Yellow

# Clean up
Stop-Job -Name "ThreatLens-Backend"
Stop-Job -Name "ThreatLens-Frontend"
Remove-Job -Name "ThreatLens-Backend"
Remove-Job -Name "ThreatLens-Frontend"

Write-Host "[+] Services stopped cleanly. Goodbye!" -ForegroundColor Green
