@echo off
REM ========================================
REM i20 AI Garage - Startup Script (Windows Batch)
REM ========================================

setlocal enabledelayedexpansion

echo ========================================
echo    i20 AI Garage - Starting Up
echo ========================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"

echo Project directory: %PROJECT_DIR%

REM Check for virtual environment
set "VENV_PATH=%PROJECT_DIR%.venv"
set "VENV_PYTHON=%VENV_PATH%\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo ERROR: Virtual environment not found at: %VENV_PATH%
    echo.
    echo Please create a virtual environment first:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Virtual environment: %VENV_PATH%

REM Check for LM Studio
echo.
echo Checking LM Studio connection...
curl -s -m 5 "http://localhost:1234/v1/models" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] LM Studio is running
    REM Check for specific model (requires jq or python)
    %VENV_PYTHON% -c "
import requests, sys
try:
    r = requests.get('http://localhost:1234/v1/models', timeout=5)
    models = [m['id'] for m in r.json().get('data', [])]
    if 'qwen2.5-3b-instruct' in models:
        print('[OK] qwen2.5-3b-instruct model found')
    else:
        print('[WARN] qwen2.5-3b-instruct not found. Available:', ', '.join(models))
except Exception as e:
    print('[WARN] Could not check models:', e)
"
) else (
    echo [WARN] LM Studio not accessible at http://localhost:1234/v1
    echo        Please ensure LM Studio is running and the local server is started
    echo        (Developer -> Start Server)
)

REM Check for app.py
set "APP_PATH=%PROJECT_DIR%app.py"
if not exist "%APP_PATH%" (
    echo ERROR: app.py not found at: %APP_PATH%
    pause
    exit /b 1
)

echo.
echo Starting Streamlit application...
echo URL: http://localhost:8501
echo Press Ctrl+C to stop
echo.

REM Run Streamlit with virtual environment's Python
"%VENV_PYTHON%" -m streamlit run "%APP_PATH%" --server.port=8501 --server.address=localhost

echo.
echo i20 AI Garage stopped.
pause