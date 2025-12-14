"""Minimal in-repo Database manager utilities.

This module previously contained stubs which caused runtime errors when
callers attempted to pass dependencies (e.g. a SheetsClient) to
DatabaseManager(). Provide a small, well-documented constructor so runtime
initialization in `src.web.app` succeeds and tests can instantiate the
module without requiring a full database backend.
"""

from typing import Optional


class DatabaseManager:
    """Lightweight DatabaseManager used by the web app in tests and
    lightweight deployments.

    Args:
        sheets_client: Optional client used to access Google Sheets. The
            implementation stores this value for downstream services and
            does not enforce a strict interface — this keeps tests simple.
    """

    def __init__(self, sheets_client: Optional[object] = None):
        self.sheets_client = sheets_client

    def __repr__(self) -> str:  # helpful for debugging/logging
        return f"<DatabaseManager sheets_client={'set' if self.sheets_client is not None else 'none'}>"


class InkaLearningSystem:
    """Compatibility stub for typing / imports. The real INKA learning
    facility is implemented in `src.ai.inka_learning` and referenced where
    needed. Keeping this class prevents import errors in some test paths.
    """

    def __init__(self):
        pass
