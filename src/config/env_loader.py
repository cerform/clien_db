import os
from pathlib import Path
from dotenv import load_dotenv

def load_env(path: str = ".env"):
    """
    Load environment variables from .env file
    Searches in current dir, script dir, and parent dirs
    """
    # Try current directory first
    if os.path.exists(path):
        load_dotenv(path)
        return
    
    # Try script directory (tattoo_appointment_bot/)
    script_dir = Path(__file__).parent.parent.parent  # Go up to project root
    env_path = script_dir / path
    if env_path.exists():
        load_dotenv(env_path)
        return
    
    # Try .env.example as fallback
    example_path = script_dir / ".env.example"
    if example_path.exists():
        load_dotenv(example_path)
        return
    
    # Try current dir .env.example
    if os.path.exists(".env.example"):
        load_dotenv(".env.example")
