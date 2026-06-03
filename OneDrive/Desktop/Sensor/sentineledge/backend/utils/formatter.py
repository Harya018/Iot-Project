"""
utils/formatter.py — Single source of truth for ALL alert message formatting.

Temperature monitoring only. Every module that needs a human-readable
alert string imports from here. No formatting logic lives anywhere else.
"""


# ── Internal helper ───────────────────────────────────────────────────────────

def _breach_phrase(
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
    unit: str,
) -> str:
    """
    Build the core breach description.

    Example: "Temperature is 42.0°C — exceeds high threshold of 40.0°C"
    """
    param_name = parameter.capitalize()
    if direction == "high":
        relation = "exceeds high threshold"
    else:
        relation = "below low threshold"
    return (
        f"{param_name} is {value}{unit} — "
        f"{relation} of {threshold}{unit}"
    )


# ── Public formatters ─────────────────────────────────────────────────────────

def format_alert_message(
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
    severity: str,
    unit: str,
) -> str:
    """
    Return a single-line alert message for email body and in-app display.

    Example:
        "[WARNING] Temperature is 42.0°C — exceeds high threshold of 40.0°C"
    """
    phrase = _breach_phrase(parameter, value, threshold, direction, unit)
    return f"[{severity}] {phrase}"


def format_escalation_message(
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
    severity: str,
    unit: str,
    level: int,
    prev_name: str = None,
    timeout: int = 60,
) -> str:
    """
    Return an escalation message appropriate for the given level.

    Level 1: same as format_alert_message.
    Level 2: adds "has not responded in Ns. Immediate action required."
    Level 3: adds "Unacknowledged for Ns. All personnel alerted."
    """
    base = format_alert_message(parameter, value, threshold, direction, severity, unit)
    if level == 1:
        return base
    elif level == 2:
        prev = prev_name or "The primary contact"
        return (
            f"ESCALATION (Level 2): {base}. "
            f"{prev} has not responded in {timeout}s. "
            f"Immediate action required."
        )
    else:
        return (
            f"CRITICAL (Level 3 \u2014 Final): {base}. "
            f"Unacknowledged for {timeout * 2}s. "
            f"All personnel alerted."
        )


def format_email_subject(
    parameter: str,
    direction: str,
    severity: str,
    level: int,
) -> str:
    """
    Return a short, descriptive email subject line.

    Example:
        "[CRITICAL] SentinelEdge Alert \u2014 Temperature HIGH \u2014 Escalation Level 2"
    """
    param_name = parameter.capitalize()
    dir_label = direction.upper()
    if level == 1:
        return f"[{severity}] SentinelEdge Alert \u2014 {param_name} {dir_label}"
    return (
        f"[{severity}] SentinelEdge Alert \u2014 "
        f"{param_name} {dir_label} \u2014 Escalation Level {level}"
    )


def format_sms_message(
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
    severity: str,
    unit: str,
    level: int,
    server_url: str = "http://localhost:5000",
) -> str:
    """
    Return a compact SMS message (target: \u2264160 chars).

    Example:
        "SENTINEL [CRITICAL] Temp 42.0\u00b0C > 40.0\u00b0C threshold. Level 2.
         Acknowledge: http://192.168.1.x:5000"
    """
    op = ">" if direction == "high" else "<"
    msg = (
        f"SENTINEL [{severity}] Temp {value}{unit} {op} "
        f"{threshold}{unit} threshold. Level {level}. "
        f"Acknowledge: {server_url}"
    )
    # Truncate to 160 chars as a safeguard
    return msg[:160]


def format_daily_report(stats: dict) -> str:
    """
    Return a plain-text email body for the daily summary report.

    Expected keys in stats:
        date, total_readings, valid_readings, invalid_readings,
        total_alerts, alerts_by_parameter,
        avg_temperature,
        peak_temperature, peak_temperature_time,
        escalations_count,
        email_sent, email_failed, sms_sent, sms_failed
    """
    lines = [
        "SentinelEdge \u2014 Daily Summary Report",
        f"Date: {stats.get('date', 'N/A')}",
        f"Generated at: {stats.get('generated_at', 'N/A')}",
        "",
        "=== SENSOR READINGS ===",
        f"Total readings    : {stats.get('total_readings', 0)}",
        f"Valid readings    : {stats.get('valid_readings', 0)}",
        f"Invalid readings  : {stats.get('invalid_readings', 0)}",
        f"Avg temperature   : {stats.get('avg_temperature', 0.0)} \u00b0C",
    ]

    if stats.get("peak_temperature") is not None:
        lines.append(
            f"Peak temperature  : {stats['peak_temperature']} \u00b0C"
            f"  at {stats.get('peak_temperature_time', '')}"
        )

    lines += [
        "",
        "=== ALERTS ===",
        f"Total alerts      : {stats.get('total_alerts', 0)}",
        f"Total escalations : {stats.get('escalations_count', 0)}",
    ]

    by_param = stats.get("alerts_by_parameter", {})
    for key, count in by_param.items():
        lines.append(f"  {key}: {count}")

    lines += [
        "",
        "=== DELIVERY ===",
        f"Email sent        : {stats.get('email_sent', 0)}",
        f"Email failed      : {stats.get('email_failed', 0)}",
        f"SMS sent          : {stats.get('sms_sent', 0)}",
        f"SMS failed        : {stats.get('sms_failed', 0)}",
        "",
        "-- SentinelEdge automated report",
    ]

    return "\n".join(lines)
