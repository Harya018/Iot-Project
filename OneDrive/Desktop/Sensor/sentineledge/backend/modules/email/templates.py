"""
modules/email/templates.py — Human-readable alert message formatter.

Extracted from the original notifier.py (format_alert_message).
No external dependencies.
"""


def format_alert_message(
    parameter: str,
    value: float,
    threshold: float,
    direction: str,
) -> str:
    """
    Build a human-readable alert message for any of the four breach types.

    Examples
    --------
    "ALERT: Temperature is 39.2°C — exceeds high threshold of 38.0°C"
    "ALERT: Humidity is 30.5% — below low threshold of 35.0%"
    """
    if parameter == "temperature":
        label = "Temperature"
        unit = "°C"
    else:
        label = "Humidity"
        unit = "%"

    if direction == "high":
        return (
            f"ALERT: {label} is {value}{unit} — exceeds high threshold of {threshold}{unit}"
        )
    else:
        return (
            f"ALERT: {label} is {value}{unit} — below low threshold of {threshold}{unit}"
        )
