@echo off
echo ============================================
echo  SentinelEdge — One-Time Machine Setup
echo ============================================
echo.

echo [1/4] Setting PostgreSQL service to auto-start on boot...
sc config postgresql-x64-16 start= auto
if %errorlevel%==0 (
    echo       OK — PostgreSQL will start automatically on every boot.
) else (
    echo       WARNING — Could not configure PostgreSQL service.
    echo       Run this script as Administrator.
)

echo [2/4] Starting PostgreSQL now (if not already running)...
net start postgresql-x64-16 2>nul
if %errorlevel%==0 (
    echo       OK — PostgreSQL started.
) else (
    echo       OK — PostgreSQL was already running.
)

echo [3/4] Configuring Windows power settings...
echo       Disabling sleep on AC power...
powercfg /change standby-timeout-ac 0
echo       Disabling hibernate on AC power...
powercfg /change hibernate-timeout-ac 0
echo       Disabling monitor timeout on AC power...
powercfg /change monitor-timeout-ac 0
echo       OK — Machine will never sleep while plugged in.

echo [4/4] Registering SentinelEdge watchdog as Windows startup task...
schtasks /delete /tn "SentinelEdge" /f 2>nul
schtasks /create /tn "SentinelEdge" ^
  /tr "C:\Users\harya\OneDrive\Desktop\Sensor\sentineledge\start_with_watchdog.bat" ^
  /sc onstart ^
  /delay 0000:30 ^
  /ru SYSTEM ^
  /rl HIGHEST ^
  /f
if %errorlevel%==0 (
    echo       OK — SentinelEdge will start automatically 30 seconds after every boot.
) else (
    echo       WARNING — Could not register startup task.
    echo       Run this script as Administrator.
)

echo.
echo ============================================
echo  Setup complete.
echo  Next step: configure BIOS to auto-restart
echo  after power failure (see instructions below)
echo ============================================
echo.
echo  BIOS INSTRUCTION (do this once manually):
echo  1. Restart the PC and press DEL or F2 to enter BIOS
echo  2. Find setting named one of:
echo       "Restore on AC Power Loss"
echo       "After Power Loss"
echo       "AC Power Recovery"
echo  3. Set it to: Power On (or Always On)
echo  4. Save and exit BIOS
echo.
pause
