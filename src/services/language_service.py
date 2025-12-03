"""User language management service"""

from typing import Optional
from src.config.env_loader import load_env
from src.config.config import Config
from src.db.sheets_client import SheetsClient
import logging

logger = logging.getLogger(__name__)


class UserLanguageService:
    """Service for managing user language preferences"""

    def __init__(self, sheets_client: SheetsClient, spreadsheet_id: str):
        self.sheets = sheets_client
        self.spreadsheet_id = spreadsheet_id

    def set_user_language(self, user_id: int, language: str) -> bool:
        """Set user language preference"""
        try:
            # Check if user exists in clients table
            clients = self.sheets.read_sheet(self.spreadsheet_id, "clients")
            user_exists = False
            user_row = None

            for i, client in enumerate(clients):
                if len(client) > 1 and str(client[1]) == str(user_id):
                    user_exists = True
                    user_row = i + 2  # +2 because of header and 1-based indexing
                    break

            if user_exists and user_row:
                # Update language in clients table (add language column if needed)
                # For now, store in a separate language mapping
                try:
                    languages = self.sheets.read_sheet(self.spreadsheet_id, "user_languages")
                except:
                    # Create table if doesn't exist
                    self.sheets.append_row(
                        self.spreadsheet_id,
                        "user_languages!A:B",
                        ["user_id", "language"]
                    )
                    languages = []

                # Check if user already has language set
                for lang_row in languages[1:]:  # Skip header
                    if len(lang_row) > 0 and str(lang_row[0]) == str(user_id):
                        # Update existing
                        self.sheets.update_row(
                            self.spreadsheet_id,
                            "user_languages",
                            languages.index(lang_row) + 1,
                            [user_id, language]
                        )
                        return True

                # Add new
                self.sheets.append_row(
                    self.spreadsheet_id,
                    "user_languages!A:B",
                    [user_id, language]
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to set user language: {e}")
            return False

    def get_user_language(self, user_id: int) -> str:
        """Get user language preference (default: Russian)"""
        try:
            languages = self.sheets.read_sheet(self.spreadsheet_id, "user_languages")

            for lang_row in languages[1:]:  # Skip header
                if len(lang_row) > 0 and str(lang_row[0]) == str(user_id):
                    return lang_row[1] if len(lang_row) > 1 else "ru"

            return "ru"  # Default to Russian

        except Exception as e:
            logger.error(f"Failed to get user language: {e}")
            return "ru"  # Default to Russian


# Global instance
def get_language_service() -> UserLanguageService:
    """Get or create language service"""
    load_env()
    cfg = Config.from_env()
    sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
    return UserLanguageService(sc, cfg.SPREADSHEET_ID)
