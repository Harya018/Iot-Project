"""
watchdog_config.py — SentinelEdge Watchdog Configuration
Edit these values before deploying to client.
"""

# ── Server location ───────────────────────────────────────────────────────────
SERVER_HOST = "localhost"
SERVER_PORT = 5000

# NOTE: SentinelEdge runs HTTPS (self-signed cert). The watchdog uses
# verify=False so it can reach the health endpoint without CA validation.
HEALTH_ENDPOINT = f"https://{SERVER_HOST}:{SERVER_PORT}/api/health"

# ── Timing ───────────────────────────────────────────────────────────────────
CHECK_INTERVAL_SECONDS         = 30   # ping server every 30 s
FAILURE_RETRY_SECONDS          = 10   # wait before confirming down
CONSECUTIVE_FAILURES_TO_RESTART = 2   # 2 consecutive failures → restart

# ── Server start command (matches start_server.bat exactly) ──────────────────
SERVER_COMMAND = [
    "uvicorn", "main:app",
    "--host",          "0.0.0.0",
    "--port",          "5000",
    "--app-dir",       "backend",
    "--ssl-keyfile",   "ssl/key.pem",
    "--ssl-certfile",  "ssl/cert.pem",
]
SERVER_WORKING_DIR     = r"C:\Users\harya\OneDrive\Desktop\Sensor\sentineledge"
SERVER_ENV_PYTHONPATH  = r"C:\Users\harya\OneDrive\Desktop\Sensor\sentineledge\backend"

# ── Developer alert settings ──────────────────────────────────────────────────
ALERT_EMAIL = True           # send email when server restarts
# These are loaded from .env.development at runtime; set fallbacks here.
DEVELOPER_EMAIL = "crharya@gmail.com"
DEVELOPER_PHONE = "6385936224"

# ── Watchdog log file ─────────────────────────────────────────────────────────
LOG_FILE = r"C:\Users\harya\OneDrive\Desktop\Sensor\sentineledge\logs\watchdog.log"

# ── Restart limits ────────────────────────────────────────────────────────────
MAX_RESTART_ATTEMPTS      = 5    # give up after 5 consecutive restart failures
RESTART_COOLDOWN_SECONDS  = 60   # wait 60 s between restart attempts
