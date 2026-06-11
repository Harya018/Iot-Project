@echo off
title SentinelEdge Watchdog
color 0A

echo.
echo ==========================================
echo   SentinelEdge -- Starting with Watchdog
echo ==========================================
echo.
echo The watchdog will:
echo   - Start the SentinelEdge server automatically
echo   - Monitor it every 30 seconds (HTTPS health check)
echo   - Restart it automatically if it crashes
echo   - Email you if something goes wrong
echo   - Stop after 5 consecutive failed restarts
echo.
echo Log file: logs\watchdog.log
echo.
echo Press Ctrl+C to stop the watchdog.
echo The watchdog will ask if you also want to stop the server.
echo.

cd /d C:\Users\harya\OneDrive\Desktop\Sensor\sentineledge

:: Check Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    echo         Make sure your virtual environment is activated.
    pause
    exit /b 1
)

:: Kill anything already on 5000 so the watchdog gets a clean slate
echo [*] Checking port 5000...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    echo [*] Freeing port 5000 (PID %%a)...
    taskkill /PID %%a /F >nul 2>&1
)

echo [*] Starting watchdog...
echo.

set PYTHONPATH=C:\Users\harya\OneDrive\Desktop\Sensor\sentineledge\backend
python watchdog.py

echo.
echo [Watchdog] Exited.
pause
