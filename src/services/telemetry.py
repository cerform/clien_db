"""Simple telemetry counters for LLM and INKA events.

This is intentionally lightweight: counters are process-local and intended for
basic testing and logs. For production, wire these to Cloud Monitoring.
"""
from typing import Dict
import threading

_lock = threading.Lock()
_counters: Dict[str, int] = {}


def incr(name: str, amount: int = 1) -> None:
    with _lock:
        _counters[name] = _counters.get(name, 0) + amount


def get(name: str) -> int:
    with _lock:
        return _counters.get(name, 0)


def reset() -> None:
    with _lock:
        _counters.clear()


def snapshot() -> Dict[str, int]:
    with _lock:
        return dict(_counters)
