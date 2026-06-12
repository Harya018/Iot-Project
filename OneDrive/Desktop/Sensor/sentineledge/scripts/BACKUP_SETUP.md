# SentinelEdge Backup Setup Guide

## Why rclone?
rclone is a free command-line tool that syncs files to Google Drive.
It handles authentication properly without needing OAuth keys in code.
Configure it once on the client machine — backups run forever after that.

## Step 1 — Install rclone
Download from: https://rclone.org/downloads/
Choose: Windows 64-bit
Extract rclone.exe to: C:\Program Files\rclone\rclone.exe
Add to PATH or use full path in backup.py

## Step 2 — Configure Google Drive remote
Open PowerShell and run:
  rclone config

Follow the prompts:
  n  → New remote
  Name: gdrive
  Storage: Google Drive (pick the number)
  client_id: (leave blank)
  client_secret: (leave blank)
  scope: 1 (full access)
  root_folder_id: (leave blank)
  service_account_file: (leave blank)
  Auto config: Yes
  → Browser opens → log in with client's Google account → Allow
  Team drive: No
  Done

## Step 3 — Create backup folder in Google Drive
1. Open drive.google.com
2. Create a folder named: SentinelEdge_Backups
3. Open the folder
4. Copy the folder ID from the URL:
   drive.google.com/drive/folders/COPY_THIS_PART
5. Paste it into scripts/backup.py → GDRIVE_FOLDER_ID

## Step 4 — Update backup.py credentials
Open: scripts/backup.py
Fill in:
  PG_PASSWORD    = "your postgres password"
  GDRIVE_FOLDER_ID = "folder id from step 3"
  DEVELOPER_EMAIL  = "your email for error alerts"

## Step 5 — Test manually
  python scripts/backup.py
  → Should show: Backup completed successfully.
  → Check Google Drive folder for the .sql file

## Step 6 — Run setup_autostart.bat as Administrator
This registers the nightly 2 AM backup task in Windows Task Scheduler.
