"""
routers/reports.py — Daily summary reports.

Endpoints:
    GET /api/reports/daily?days=30
"""



from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone, timedelta

from middleware.auth import require_admin
from database.connection import execute_read
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/daily", dependencies=[Depends(require_admin)])
async def daily_reports(days: int = Query(30, ge=1, le=90)):
    """
    Return one summary object per calendar day for the last N days.
    Each day: date, total_readings, total_alerts, avg_temp, peak_temp,
    peak_temp_time, min_temp, email_sent, email_failed, sms_sent, sms_failed.
    """
    results = []
    today = datetime.now(timezone.utc).date()

    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.isoformat()
        start = f"{date_str}T00:00:00"
        end   = f"{date_str}T23:59:59"

        try:
            readings = execute_read(
                "SELECT temperature, timestamp FROM readings "
                "WHERE timestamp >= %s AND timestamp <= %s",
                (start, end),
            )
            alerts = execute_read(
                "SELECT id FROM alerts WHERE timestamp >= %s AND timestamp <= %s",
                (start, end),
            )
            receipts = execute_read(
                "SELECT channel, success, COUNT(*) as cnt FROM delivery_receipts "
                "WHERE sent_at >= %s AND sent_at <= %s GROUP BY channel, success",
                (start, end),
            )

            temps = [r["temperature"] for r in readings if r.get("temperature") is not None]
            peak_row = max(readings, key=lambda r: r["temperature"], default=None) if readings else None
            min_row  = min(readings, key=lambda r: r["temperature"], default=None) if readings else None

            delivery = {"email_sent": 0, "email_failed": 0, "sms_sent": 0, "sms_failed": 0}
            for r in receipts:
                ch = r["channel"]
                key = f"{ch}_{'sent' if r['success'] else 'failed'}"
                if key in delivery:
                    delivery[key] += r["cnt"]

            results.append({
                "date":            date_str,
                "total_readings":  len(readings),
                "total_alerts":    len(alerts),
                "avg_temp":        round(sum(temps) / len(temps), 2) if temps else None,
                "peak_temp":       peak_row["temperature"] if peak_row else None,
                "peak_temp_time":  peak_row.get("timestamp") if peak_row else None,
                "min_temp":        min_row["temperature"] if min_row else None,
                **delivery,
            })
        except Exception as exc:
            logger.error("daily_reports failed for %s: %s", date_str, exc)
            results.append({"date": date_str, "error": str(exc)})

    return results
