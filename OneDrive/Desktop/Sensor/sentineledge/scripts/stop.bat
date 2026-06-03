@echo off
echo Stopping SentinelEdge...
taskkill /f /im uvicorn.exe
echo Stopped.
pause
