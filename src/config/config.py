import os
from dataclasses import dataclass
from typing import List

@dataclass
class Config:
    BOT_TOKEN: str
    USE_WEBHOOK: bool
    WEBHOOK_URL: str
    PORT: int
    GOOGLE_CREDENTIALS_PATH: str
    GOOGLE_TOKEN_PATH: str
    SPREADSHEET_ID: str
    MASTER_CALENDAR_ID: str
    DEFAULT_TIMEZONE: str
    ADMIN_USER_IDS: List[int]
    ENV: str
    OPENAI_API_KEY: str
    DEFAULT_SLOT_DURATION: int

    @staticmethod
    def from_env():
        # Get project root directory (where .env file is)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Helper to convert relative paths to absolute
        def to_absolute_path(path: str) -> str:
            if not path or os.path.isabs(path):
                return path
            return os.path.join(project_root, path)
        
        return Config(
            BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
            USE_WEBHOOK=os.getenv("USE_WEBHOOK", "false").lower() in ("1","true","yes"),
            WEBHOOK_URL=os.getenv("WEBHOOK_URL", ""),
            PORT=int(os.getenv("PORT", "8080")),
            GOOGLE_CREDENTIALS_PATH=to_absolute_path(os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")),
            GOOGLE_TOKEN_PATH=to_absolute_path(os.getenv("GOOGLE_TOKEN_PATH", "token.json")),
            SPREADSHEET_ID=os.getenv("SPREADSHEET_ID", ""),
            MASTER_CALENDAR_ID=os.getenv("MASTER_CALENDAR_ID", ""),
            DEFAULT_TIMEZONE=os.getenv("DEFAULT_TIMEZONE", "Asia/Jerusalem"),
            ADMIN_USER_IDS=[int(x.strip()) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()],
            ENV=os.getenv("ENV", "development"),
            OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
            DEFAULT_SLOT_DURATION=int(os.getenv("DEFAULT_SLOT_DURATION", "120")),
        )
