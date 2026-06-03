"""
backend/database — SQLite persistence layer.
Re-exports every public function so callers can do:
    from database import insert_reading, get_alert, insert_receipt, ...
"""

from database.connection import get_connection, init_db
from database.queries.readings import insert_reading, get_recent_readings
from database.queries.alerts import (
    insert_alert,
    get_alert,
    get_unacknowledged_alerts,
    acknowledge_alert,
    update_escalation_level,
    set_max_escalated,
    get_recent_alerts,
    get_alerts_today_count,
)
from database.queries.subscribers import (
    get_subscribers_ordered,
    get_subscriber_by_order,
    add_subscriber,
    update_push_subscription,
    delete_subscriber,
)
from database.queries.escalation_log import log_escalation
from database.queries.receipts import (
    insert_receipt,
    get_receipts_for_alert,
    get_delivery_stats_today,
)
from database.queries.config_log import log_config_change, get_recent_config_changes

__all__ = [
    # connection
    "get_connection", "init_db",
    # readings
    "insert_reading", "get_recent_readings",
    # alerts
    "insert_alert", "get_alert", "get_unacknowledged_alerts",
    "acknowledge_alert", "update_escalation_level",
    "set_max_escalated", "get_recent_alerts", "get_alerts_today_count",
    # subscribers
    "get_subscribers_ordered", "get_subscriber_by_order",
    "add_subscriber", "update_push_subscription", "delete_subscriber",
    # escalation log
    "log_escalation",
    # delivery receipts
    "insert_receipt", "get_receipts_for_alert", "get_delivery_stats_today",
    # config audit
    "log_config_change", "get_recent_config_changes",
]

# Initialise the database when this package is first imported.
init_db()
