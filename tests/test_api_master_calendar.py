#!/usr/bin/env python3
"""
Tests for Admin Master Calendar endpoint to ensure `calendar_events` is normalized as array
"""

import pytest
from fastapi.testclient import TestClient

import src.web.app as webapp
from src.web.app import create_app
from src.calendars.google_calendar_sync import GoogleCalendarSync


class FakeDBManager:
    def get_all_masters(self):
        return [{"id": "master-1", "name": "Test Master", "calendar_id": "abc"}]

    def get_schedule(self, master_id):
        return {"schedule": []}

    def get_all_bookings(self):
        return []


def test_master_calendar_returns_array_for_calendar_events(monkeypatch):
    # Replace the app db_manager with fake one
    # Create app then assign the fake db manager so create_app's initialization
    # doesn't overwrite our fake implementation.
    app = create_app()
    webapp.db_manager = FakeDBManager()

    # Patch GoogleCalendarSync.get_events to return a non-array value (e.g. 0)
    monkeypatch.setattr(GoogleCalendarSync, "get_events", lambda self, a, b: 0)

    client = TestClient(app)

    res = client.get("/api/calendar/master/master-1?start_date=2025-12-01&end_date=2025-12-07")
    assert res.status_code == 200
    data = res.json()
    assert data.get("success") is True
    # calendar_events should always be a list
    assert isinstance(data.get("calendar_events"), list)
