"""
Event publishing module - Separation of concerns for event handling

This module handles all event publishing logic, keeping it separate from
the main API endpoints.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import json
from collections import defaultdict


class EventPublisher:
    """
    Simple event publisher that can be easily extended or mocked for testing.

    In production, this would publish to Kafka, SNS, SQS, etc.
    For this assessment, it's an in-memory implementation.
    """

    def __init__(self):
        self.events: list[Dict[str, Any]] = []
        self.enabled = True

    def publish(self, event_type: str, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Publish an event. Returns True if successful, False otherwise.

        Args:
            event_type: Type of event (e.g., "user.created")
            user_id: ID of the user
            data: Event payload data

        Returns:
            bool: True if published successfully
        """
        if not self.enabled:
            return False

        event = {
            "event_type": event_type,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        try:
            self.events.append(event)
            return True
        except Exception:
            # In production, log this error
            return False

    def get_events(self) -> list[Dict[str, Any]]:
        """Get all published events (for testing/debugging)"""
        return self.events.copy()

    def clear(self):
        """Clear all events (for testing)"""
        self.events.clear()

    def disable(self):
        """Disable event publishing (simulates outage)"""
        self.enabled = False

    def enable(self):
        """Enable event publishing"""
        self.enabled = True


class MetricsCollector:
    """
    Metrics collection - Separation of concerns for observability.

    Tracks application metrics independently of business logic.
    """

    def __init__(self):
        self.counters = defaultdict(int)
        self.start_time = datetime.utcnow()

    def increment(self, metric_name: str, amount: int = 1):
        """Increment a counter metric"""
        self.counters[metric_name] += amount

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as a dictionary"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            "counters": dict(self.counters),
            "uptime_seconds": int(uptime)
        }

    def reset(self):
        """Reset all metrics (for testing)"""
        self.counters.clear()
        self.start_time = datetime.utcnow()


# Global instances (in production, these would be dependency-injected)
event_publisher = EventPublisher()
metrics_collector = MetricsCollector()
