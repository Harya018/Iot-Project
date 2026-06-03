@echo off
echo Starting SentinelEdge (Development)...
cd /d "%~dp0\.."
set APP_ENV=development
set PYTHONPATH=%CD%;%CD%\backend
call venv\Scripts\activate
uvicorn backend.main:app --host 0.0.0.0 --port 5000 --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem
pause
