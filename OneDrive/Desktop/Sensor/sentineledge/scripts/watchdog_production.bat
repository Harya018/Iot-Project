@echo off
:loop
echo ================================================
echo  SentinelEdge Watchdog (Production)
echo  Server will auto-restart if it crashes.
echo  Press Ctrl+C twice to stop completely.
echo ================================================
cd /d "%~dp0\.."
set APP_ENV=production
set PYTHONPATH=%CD%;%CD%\backend
call venv\Scripts\activate
uvicorn backend.main:app --host 0.0.0.0 --port 5000 --workers 1
echo.
echo Server stopped. Restarting in 5 seconds...
echo (Press Ctrl+C now to cancel restart)
timeout /t 5
goto loop
