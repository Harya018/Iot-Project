@echo off
REM SentinelEdge stop script for Windows
echo Stopping SentinelEdge...
taskkill /F /IM uvicorn.exe /T 2>nul && echo SentinelEdge stopped. || echo SentinelEdge was not running.
