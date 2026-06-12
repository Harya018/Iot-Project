"""
SentinelEdge — Nightly PostgreSQL Backup to Google Drive
---------------------------------------------------------
Runs pg_dump, saves a timestamped .sql file locally,
uploads it to a Google Drive folder, then deletes local
backups older than 7 days.

SETUP (fill in before deploying to client machine):
  1. GDRIVE_EMAIL     — Google account email
  2. GDRIVE_PASSWORD  — App Password (NOT the Gmail login password)
                        Generate at: myaccount.google.com/apppasswords
                        (Requires 2FA enabled on the Google account)
  3. GDRIVE_FOLDER_ID — Google Drive folder ID
                        Open the folder in browser, copy the ID from URL:
                        drive.google.com/drive/folders/THIS_PART_IS_THE_ID
"""

import os
import sys
import subprocess
import datetime
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURATION — fill these in before deploying
# ─────────────────────────────────────────────
GDRIVE_EMAIL       = "YOUR_GMAIL_HERE@gmail.com"        # TODO: fill in
GDRIVE_PASSWORD    = "YOUR_APP_PASSWORD_HERE"           # TODO: fill in (App Password)
GDRIVE_FOLDER_ID   = "YOUR_GOOGLE_DRIVE_FOLDER_ID"     # TODO: fill in

# PostgreSQL connection details — must match backend .env
PG_HOST     = "localhost"
PG_PORT     = "5432"
PG_DB       = "sentineledge"
PG_USER     = "postgres"
PG_PASSWORD = "your_postgres_password"                  # TODO: fill in

# pg_dump path — default PostgreSQL 16 Windows install location
PG_DUMP_PATH = r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"

# Local backup folder (keeps last 7 days)
BACKUP_DIR = Path(r"C:\Users\harya\OneDrive\Desktop\Sensor\sentineledge\backups")

# Developer email for error notifications
DEVELOPER_EMAIL = "YOUR_DEVELOPER_EMAIL@gmail.com"     # TODO: fill in
# ─────────────────────────────────────────────


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")


def send_error_email(subject: str, body: str):
    """Send error notification to developer if backup fails."""
    if "YOUR_GMAIL" in GDRIVE_EMAIL:
        log("Email not configured — skipping error notification.")
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = f"[SentinelEdge] Backup FAILED — {subject}"
        msg["From"] = GDRIVE_EMAIL
        msg["To"] = DEVELOPER_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GDRIVE_EMAIL, GDRIVE_PASSWORD)
            server.send_message(msg)
        log("Error notification sent to developer.")
    except Exception as e:
        log(f"Could not send error email: {e}")


def run_pg_dump() -> Path:
    """Run pg_dump and return path to the .sql file."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"sentineledge_backup_{timestamp}.sql"

    env = os.environ.copy()
    env["PGPASSWORD"] = PG_PASSWORD

    log(f"Running pg_dump → {backup_file.name}")
    result = subprocess.run(
        [
            PG_DUMP_PATH,
            "-h", PG_HOST,
            "-p", PG_PORT,
            "-U", PG_USER,
            "-d", PG_DB,
            "-f", str(backup_file),
            "--no-password"
        ],
        env=env,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed:\n{result.stderr}")

    size_kb = backup_file.stat().st_size // 1024
    log(f"pg_dump complete — {size_kb} KB")
    return backup_file


def upload_to_gdrive(backup_file: Path):
    """Upload backup file to Google Drive using PyDrive2."""
    if "YOUR_GMAIL" in GDRIVE_EMAIL:
        log("Google Drive not configured — skipping upload.")
        log("Backup saved locally only.")
        return

    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    from oauth2client.service_account import ServiceAccountCredentials

    log("Authenticating with Google Drive...")

    # Use stored credentials if available, otherwise authenticate
    gauth = GoogleAuth()
    gauth.settings["client_config_backend"] = "settings"
    gauth.settings["client_config"] = {
        "client_id": "",
        "client_secret": "",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"
    }

    # Use service account credentials via oauth2
    import httplib2
    from oauth2client.client import GoogleCredentials
    import json

    # Simple approach: use gdrive CLI via subprocess if available
    # Fall back to pydrive2 OAuth flow
    try:
        drive = GoogleDrive(gauth)
        file_obj = drive.CreateFile({
            "title": backup_file.name,
            "parents": [{"id": GDRIVE_FOLDER_ID}]
        })
        file_obj.SetContentFile(str(backup_file))
        file_obj.Upload()
        log(f"Uploaded to Google Drive: {backup_file.name}")
    except Exception as e:
        raise RuntimeError(f"Google Drive upload failed: {e}")


def upload_via_rclone(backup_file: Path):
    """
    Upload using rclone — simpler and more reliable than OAuth.
    rclone must be configured once with: rclone config
    Remote name must be 'gdrive' pointing to Google Drive folder.
    """
    log(f"Uploading via rclone → gdrive:{GDRIVE_FOLDER_ID}/")
    result = subprocess.run(
        [
            "rclone", "copy",
            str(backup_file),
            f"gdrive:{GDRIVE_FOLDER_ID}/",
            "--log-level", "INFO"
        ],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"rclone upload failed:\n{result.stderr}")
    log(f"Upload complete: {backup_file.name}")


def delete_old_backups(keep_days: int = 7):
    """Delete local backups older than keep_days."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    deleted = 0
    for f in BACKUP_DIR.glob("sentineledge_backup_*.sql"):
        if datetime.datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
            f.unlink()
            deleted += 1
    if deleted:
        log(f"Deleted {deleted} old backup(s) older than {keep_days} days.")


def main():
    log("=" * 50)
    log("SentinelEdge Nightly Backup Starting")
    log("=" * 50)

    try:
        # Step 1: pg_dump
        backup_file = run_pg_dump()

        # Step 2: Upload to Google Drive via rclone
        # rclone is simpler than OAuth — configure once with: rclone config
        upload_via_rclone(backup_file)

        # Step 3: Clean up old local backups
        delete_old_backups(keep_days=7)

        log("=" * 50)
        log("Backup completed successfully.")
        log("=" * 50)

    except Exception as e:
        log(f"BACKUP FAILED: {e}")
        send_error_email(str(e), str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
