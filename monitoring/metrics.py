"""
Monitoring and metrics collection for the Telegram bot.

This module provides utilities for collecting and exporting metrics about:
- Message processing (count, latency, errors)
- User interactions (new users, active users)
- Booking operations (created, confirmed, cancelled)
- AI responses (INKA requests, processing time)
- Google Sheets sync (sync count, success rate)
- Google Calendar sync (event count, sync time)
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Single metric data point."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "unit": self.unit,
        }


class MetricsCollector:
    """Collects and manages metrics for the bot."""

    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: List[Metric] = []
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.start_time = datetime.utcnow()

    def increment_counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        key = f"{name}_{self._tag_key(tags)}"
        self.counters[key] += value
        self._record_metric(name, value, tags, "count")

    def set_gauge(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        key = f"{name}_{self._tag_key(tags)}"
        self.gauges[key] = value
        self._record_metric(name, value, tags, "gauge")

    def record_timer(
        self, name: str, duration: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timer metric."""
        key = f"{name}_{self._tag_key(tags)}"
        self.timers[key].append(duration)
        self._record_metric(name, duration, tags, "ms")

    def _record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        unit: str = "",
    ) -> None:
        """Record a metric."""
        metric = Metric(name=name, value=value, tags=tags or {}, unit=unit)
        self.metrics.append(metric)

    def _tag_key(self, tags: Optional[Dict[str, str]] = None) -> str:
        """Create tag key from tags dict."""
        if not tags:
            return "default"
        return "_".join(f"{k}_{v}" for k, v in sorted(tags.items()))

    def get_counter(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> int:
        """Get counter value."""
        key = f"{name}_{self._tag_key(tags)}"
        return self.counters[key]

    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value."""
        key = f"{name}_{self._tag_key(tags)}"
        return self.gauges[key]

    def get_timer_stats(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Get timer statistics."""
        key = f"{name}_{self._tag_key(tags)}"
        times = self.timers[key]

        if not times:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}

        return {
            "min": min(times),
            "max": max(times),
            "avg": sum(times) / len(times),
            "count": len(times),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        uptime = datetime.utcnow() - self.start_time
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timers": {
                name: self.get_timer_stats(name.split("_")[0])
                for name in self.timers.keys()
            },
            "total_metrics_recorded": len(self.metrics),
        }

    def get_metrics_json(self) -> List[Dict[str, Any]]:
        """Export all metrics as JSON."""
        return [metric.to_dict() for metric in self.metrics]

    def clear(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.timers.clear()


class BotMetrics:
    """Bot-specific metrics."""

    def __init__(self):
        """Initialize bot metrics."""
        self.collector = MetricsCollector()

    # Message metrics
    def record_message_received(self, chat_id: int, user_id: int) -> None:
        """Record incoming message."""
        self.collector.increment_counter(
            "message_received", tags={"chat_type": "private"}
        )

    def record_message_processed(
        self, chat_id: int, processing_time: float, success: bool = True
    ) -> None:
        """Record processed message."""
        status = "success" if success else "error"
        self.collector.increment_counter("message_processed", tags={"status": status})
        self.collector.record_timer(
            "message_processing_time", processing_time, tags={"status": status}
        )

    def record_command(self, command: str) -> None:
        """Record command execution."""
        self.collector.increment_counter("command_executed", tags={"command": command})

    # User metrics
    def record_new_user(self, user_id: int) -> None:
        """Record new user."""
        self.collector.increment_counter("new_user")

    def record_active_user(self, user_id: int) -> None:
        """Record active user."""
        # Use gauge to track unique active users
        pass

    # Booking metrics
    def record_booking_created(self, service: str, master: str) -> None:
        """Record booking creation."""
        self.collector.increment_counter(
            "booking_created", tags={"service": service, "master": master}
        )

    def record_booking_confirmed(self, booking_id: str) -> None:
        """Record booking confirmation."""
        self.collector.increment_counter("booking_confirmed")

    def record_booking_cancelled(self, booking_id: str) -> None:
        """Record booking cancellation."""
        self.collector.increment_counter("booking_cancelled")

    def record_booking_error(self, error_type: str) -> None:
        """Record booking error."""
        self.collector.increment_counter("booking_error", tags={"error_type": error_type})

    # AI metrics
    def record_inka_request(self, prompt_length: int) -> None:
        """Record INKA request."""
        self.collector.increment_counter("inka_request")
        self.collector.set_gauge("inka_last_prompt_length", prompt_length)

    def record_inka_response(self, response_time: float, success: bool = True) -> None:
        """Record INKA response."""
        status = "success" if success else "error"
        self.collector.record_timer("inka_response_time", response_time, tags={"status": status})

    def record_inka_error(self, error_type: str) -> None:
        """Record INKA error."""
        self.collector.increment_counter("inka_error", tags={"error_type": error_type})

    # Google Sheets sync metrics
    def record_sheets_sync(self, sync_time: float, success: bool = True, rows: int = 0) -> None:
        """Record Google Sheets sync."""
        status = "success" if success else "error"
        self.collector.record_timer("sheets_sync_time", sync_time, tags={"status": status})
        self.collector.increment_counter("sheets_sync", tags={"status": status})
        if success:
            self.collector.set_gauge("sheets_last_sync_rows", rows)

    def record_sheets_error(self, error_type: str) -> None:
        """Record Google Sheets error."""
        self.collector.increment_counter("sheets_error", tags={"error_type": error_type})

    # Google Calendar sync metrics
    def record_calendar_sync(
        self, sync_time: float, success: bool = True, events: int = 0
    ) -> None:
        """Record Google Calendar sync."""
        status = "success" if success else "error"
        self.collector.record_timer(
            "calendar_sync_time", sync_time, tags={"status": status}
        )
        self.collector.increment_counter("calendar_sync", tags={"status": status})
        if success:
            self.collector.set_gauge("calendar_last_sync_events", events)

    def record_calendar_error(self, error_type: str) -> None:
        """Record Google Calendar error."""
        self.collector.increment_counter(
            "calendar_error", tags={"error_type": error_type}
        )

    # Health metrics
    def record_health_check(self, endpoint: str, status_code: int, response_time: float) -> None:
        """Record health check."""
        status = "ok" if status_code == 200 else "error"
        self.collector.record_timer(
            "health_check_time", response_time, tags={"endpoint": endpoint, "status": status}
        )

    def record_database_status(self, status: str, latency: float = 0) -> None:
        """Record database status."""
        self.collector.set_gauge(
            "database_latency", latency, tags={"status": status}
        )

    # Export metrics
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return self.collector.get_summary()

    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        # Counters
        for name, value in self.collector.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        # Gauges
        for name, value in self.collector.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        # Timers (as histograms)
        for name, times in self.collector.timers.items():
            if times:
                stats = self.collector.get_timer_stats(name.split("_")[0])
                lines.append(f"# TYPE {name}_seconds histogram")
                lines.append(f"{name}_seconds_sum {sum(times)}")
                lines.append(f"{name}_seconds_count {len(times)}")

        return "\n".join(lines)

    def export_json(self) -> str:
        """Export metrics as JSON string."""
        import json
        return json.dumps(self.get_summary(), indent=2, default=str)


# Global metrics instance
_metrics_instance: Optional[BotMetrics] = None


def get_metrics() -> BotMetrics:
    """Get or create global metrics instance."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = BotMetrics()
    return _metrics_instance


def reset_metrics() -> None:
    """Reset global metrics instance (for testing)."""
    global _metrics_instance
    _metrics_instance = None


if __name__ == "__main__":
    # Example usage
    metrics = get_metrics()

    # Simulate some activity
    metrics.record_message_received(chat_id=123, user_id=456)
    metrics.record_message_processed(chat_id=123, processing_time=0.15, success=True)
    metrics.record_command(command="/start")

    metrics.record_new_user(user_id=789)

    metrics.record_booking_created(service="tattoo", master="Anna")
    metrics.record_booking_confirmed(booking_id="booking_1")

    metrics.record_inka_request(prompt_length=250)
    metrics.record_inka_response(response_time=1.23, success=True)

    metrics.record_sheets_sync(sync_time=0.5, success=True, rows=50)
    metrics.record_calendar_sync(sync_time=0.3, success=True, events=10)

    # Print summary
    print("=== Metrics Summary ===")
    print(metrics.export_json())

    print("\n=== Prometheus Format ===")
    print(metrics.get_prometheus_format())
