<#
.SYNOPSIS
    Start i20 AI Garage application

.DESCRIPTION
    Activates the Python virtual environment and launches the Streamlit application.

.NOTES
    Author: i20 AI Garage Team
    Project: i20 AI Garage v1.0
#>

param(
    [switch]$NoBrowser = $false,
    [string]$Port = "8501",
    [string]$Address = "localhost"
)

# Set error handling
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    i20 AI Garage - Starting Up" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectDir = $ScriptDir

Write-Host "Project directory: $ProjectDir" -ForegroundColor Gray

# Check for virtual environment
$VenvPath = Join-Path $ProjectDir ".venv"
$VenvPython = Join-Path $VenvPath "Scripts" "python.exe"
$VenvActivate = Join-Path $VenvPath "Scripts" "Activate.ps1"

if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found at: $VenvPath"
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Gray
    Write-Host "  .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Gray
    exit 1
}

Write-Host "Virtual environment: $VenvPath" -ForegroundColor Green

# Check for LM Studio
Write-Host ""
Write-Host "Checking LM Studio connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:1234/v1/models" -Method Get -TimeoutSec 5 -ErrorAction Stop
    $model = $response.data | Where-Object { $_.id -eq "qwen2.5-3b-instruct" }
    if ($model) {
        Write-Host "✓ LM Studio is running with qwen2.5-3b-instruct" -ForegroundColor Green
    } else {
        Write-Host "⚠ LM Studio is running but qwen2.5-3b-instruct model not found" -ForegroundColor Yellow
        Write-Host "  Available models: $($response.data.id -join ', ')" -ForegroundColor Gray
    }
} catch {
    Write-Warning "LM Studio not accessible at http://localhost:1234/v1"
    Write-Host "  Please ensure LM Studio is running and the local server is started (Developer → Start Server)" -ForegroundColor Yellow
}

# Check for app.py
$AppPath = Join-Path $ProjectDir "app.py"
if (-not (Test-Path $AppPath)) {
    Write-Error "app.py not found at: $AppPath"
    exit 1
}

Write-Host ""
Write-Host "Starting Streamlit application..." -ForegroundColor Cyan
Write-Host "URL: http://$Address:$Port" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Build Streamlit command
$StreamlitArgs = @("run", $AppPath, "--server.port=$Port", "--server.address=$Address")
if ($NoBrowser) {
    $StreamlitArgs += "--server.headless=true"
}

# Run Streamlit with virtual environment's Python
& $VenvPython -m streamlit @StreamlitArgs

Write-Host ""
Write-Host "i20 AI Garage stopped." -ForegroundColor Cyan