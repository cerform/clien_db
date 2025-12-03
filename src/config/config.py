import os
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
ENV_FILE = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ENV_FILE)

@dataclass
class Config:
    """Application configuration"""
    
    # Telegram
    telegram_bot_token: str
    
    # Google API
    google_spreadsheet_id: str
    google_credentials_json: str
    
    # OpenAI API
    openai_api_key: Optional[str] = None
    
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
            raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")
        
        spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SPREADSHEET_ID not set in .env")
        
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON", "credentials.json")
        if not Path(creds_json).exists():
            raise FileNotFoundError(f"Google credentials file not found: {creds_json}")
        
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
        
        openai_key = os.getenv("OPENAI_API_KEY")
        
        return cls(
            telegram_bot_token=token,
            google_spreadsheet_id=spreadsheet_id,
            google_credentials_json=creds_json,
            openai_api_key=openai_key,
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
