import os
from pathlib import Path
from dotenv import load_dotenv

def setup_environment():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        return True
    return False
