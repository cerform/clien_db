import os
import json
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env only if running locally (not in Cloud Run)
# Cloud Run uses environment variables from service configuration
if os.getenv("K_SERVICE") is None:  # K_SERVICE is set by Cloud Run
    ENV_FILE = Path(__file__).parent.parent.parent / ".env"
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)

@dataclass
class Config:
    """Application configuration"""
    
    # Telegram
    telegram_bot_token: str
    
    # Google API
    google_spreadsheet_id: str
    google_calendar_id: Optional[str] = None  # Google Calendar ID for scheduling
    
    # OpenAI API
    openai_api_key: Optional[str] = None
    openai_assistant_id: Optional[str] = None
    
    # Application
    timezone: str = "Europe/Moscow"
    log_level: str = "INFO"
    
    # Admin settings
    admin_ids: List[int] = None
    
    def __post_init__(self):
        if self.admin_ids is None:
            self.admin_ids = []
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID not set")
        
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
        
        openai_key = os.getenv("OPENAI_API_KEY")
        openai_assistant = os.getenv("OPENAI_ASSISTANT_ID", "asst_NPqHLNqQeTi7rgyaZR0iL5kE")
        
        google_calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
        
        return cls(
            telegram_bot_token=token,
            google_spreadsheet_id=spreadsheet_id,
            google_calendar_id=google_calendar_id,
            openai_api_key=openai_key,
            openai_assistant_id=openai_assistant,
            timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            admin_ids=admin_ids
        )

_config: Optional[Config] = None

def get_config() -> Config:
    """Get application configuration (singleton)"""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config

def set_config(config: Config) -> None:
    """Set configuration (for testing)"""
    global _config
    _config = config
