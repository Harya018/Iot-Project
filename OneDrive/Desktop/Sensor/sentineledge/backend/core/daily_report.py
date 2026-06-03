"""
core/daily_report.py — Daily summary report generator and scheduler (Addition 8).

generate_daily_report() — collects today's stats from the database
send_daily_report()     — emails the report to all active subscribers
schedule_daily_report() — asyncio task that fires once at midnight UTC each day
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import database
from modules.email.smtp import send_email_async
from modules.email.templates import format_alert_message

logger = logging.getLogger("sentineledge.daily_report")


# ─── Data collection ──────────────────────────────────────────────────────────

async def generate_daily_report() -> dict:
    """
    Collect today's sensor and alert statistics from the database.

    Returns a dict with:
      total_readings, total_alerts, alerts_by_type,
      avg_temperature, avg_humidity,
      peak_temperature, peak_temperature_time,
      peak_humidity, peak_humidity_time,
      total_escalations, delivery_stats
    """
    from database.connection import get_connection
    conn = get_connection()
    today = datetime.now(timezone.utc).date().isoformat()

    try:
        # ── Readings stats ────────────────────────────────────────────────────
        readings = conn.execute(
            "SELECT * FROM readings WHERE timestamp >= ? AND is_valid = 1",
            (today,),
        ).fetchall()

        total_readings = len(readings)
        avg_temp = round(
            sum(r["temperature"] for r in readings) / total_readings, 2
        ) if readings else 0.0
        avg_hum = round(
            sum(r["humidity"] for r in readings) / total_readings, 2
        ) if readings else 0.0

        peak_temp_row = max(readings, key=lambda r: r["temperature"]) if readings else None
        peak_hum_row = max(readings, key=lambda r: r["humidity"]) if readings else None

        # ── Alert stats ───────────────────────────────────────────────────────
        alerts = conn.execute(
            "SELECT * FROM alerts WHERE timestamp >= ?",
            (today,),
        ).fetchall()
        total_alerts = len(alerts)

        alerts_by_type: dict = {}
        for alert in alerts:
            key = f"{alert['parameter']}_{alert['direction']}"
            alerts_by_type[key] = alerts_by_type.get(key, 0) + 1

        # ── Escalation stats ──────────────────────────────────────────────────
        esc_rows = conn.execute(
            "SELECT COUNT(*) as cnt FROM escalation_log WHERE sent_at >= ?",
            (today,),
        ).fetchone()
        total_escalations = esc_rows["cnt"] if esc_rows else 0

    except Exception as exc:
        logger.exception("generate_daily_report DB error: %s", exc)
        total_readings = total_alerts = total_escalations = 0
        avg_temp = avg_hum = 0.0
        peak_temp_row = peak_hum_row = None
        alerts_by_type = {}
    finally:
        conn.close()

    # ── Delivery stats (from receipts table) ──────────────────────────────────
    delivery_stats = database.get_delivery_stats_today()

    report = {
        "date": today,
        "total_readings": total_readings,
        "total_alerts": total_alerts,
        "alerts_by_type": alerts_by_type,
        "avg_temperature": avg_temp,
        "avg_humidity": avg_hum,
        "peak_temperature": peak_temp_row["temperature"] if peak_temp_row else None,
        "peak_temperature_time": peak_temp_row["timestamp"] if peak_temp_row else None,
        "peak_humidity": peak_hum_row["humidity"] if peak_hum_row else None,
        "peak_humidity_time": peak_hum_row["timestamp"] if peak_hum_row else None,
        "total_escalations": total_escalations,
        "delivery_stats": delivery_stats,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return report


def _format_daily_report(report: dict) -> str:
    """Format the daily report dict into a plain-text email body."""
    lines = [
        f"SentinelEdge — Daily Summary Report",
        f"Date: {report['date']}",
        f"Generated at: {report['generated_at']}",
        "",
        "=== SENSOR READINGS ===",
        f"Total valid readings : {report['total_readings']}",
        f"Average temperature  : {report['avg_temperature']} C",
        f"Average humidity     : {report['avg_humidity']} %",
    ]
    if report["peak_temperature"] is not None:
        lines.append(
            f"Peak temperature     : {report['peak_temperature']} C"
            f"  at {report['peak_temperature_time']}"
        )
    if report["peak_humidity"] is not None:
        lines.append(
            f"Peak humidity        : {report['peak_humidity']} %"
            f"  at {report['peak_humidity_time']}"
        )
    lines += [
        "",
        "=== ALERTS ===",
        f"Total alerts today   : {report['total_alerts']}",
    ]
    for key, count in report.get("alerts_by_type", {}).items():
        lines.append(f"  {key}: {count}")
    lines += [
        f"Total escalations    : {report['total_escalations']}",
        "",
        "=== DELIVERY STATS ===",
    ]
    for channel, stats in report.get("delivery_stats", {}).items():
        lines.append(
            f"  {channel:12s}: sent={stats.get('sent', 0)}, failed={stats.get('failed', 0)}"
        )
    lines += ["", "-- SentinelEdge automated report"]
    return "\n".join(lines)


# ─── Send ─────────────────────────────────────────────────────────────────────

async def send_daily_report() -> None:
    """Generate and email the daily report to all active subscribers."""
    try:
        report = await generate_daily_report()
        body = _format_daily_report(report)
        subject = f"SentinelEdge Daily Report — {report['date']}"
        subscribers = database.get_subscribers_ordered()
        if not subscribers:
            logger.info("Daily report: no subscribers to send to.")
            return
        for sub in subscribers:
            ok = await send_email_async(sub["email"], subject, body)
            if ok:
                logger.info("Daily report sent to %s", sub["email"])
            else:
                logger.warning("Daily report failed to send to %s", sub["email"])
    except Exception as exc:
        logger.exception("send_daily_report failed: %s", exc)


# ─── Scheduler ────────────────────────────────────────────────────────────────

async def schedule_daily_report() -> None:
    """
    Asyncio background task — fires send_daily_report() once at midnight UTC,
    then waits 24 h, forever.
    """
    logger.info("Daily report scheduler started.")
    while True:
        now = datetime.now(timezone.utc)
        # Next midnight UTC
        tomorrow = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        wait_seconds = (tomorrow - now).total_seconds()
        logger.info(
            "Daily report scheduled in %.0f seconds (at %s UTC).",
            wait_seconds,
            tomorrow.isoformat(),
        )
        await asyncio.sleep(wait_seconds)
        await send_daily_report()
