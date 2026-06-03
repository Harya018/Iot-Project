"""
utils/formatter.py — Number and unit formatting helpers.
"""


def format_metric(value: float, parameter: str) -> str:
    """
    Return a human-readable metric string.

    Examples
    --------
    format_metric(38.5, "temperature")  → "38.5°C"
    format_metric(75.0, "humidity")     → "75.0%"
    """
    unit = "°C" if parameter == "temperature" else "%"
    return f"{value}{unit}"


def format_duration(seconds: int) -> str:
    """
    Return a human-readable duration string.

    Examples
    --------
    format_duration(90)   → "1m 30s"
    format_duration(3665) → "1h 1m 5s"
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)
