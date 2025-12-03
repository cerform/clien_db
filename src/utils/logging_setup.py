import logging
import sys
from src.config.config import Config

def setup_logging(cfg: Config):
    """Setup logging with proper formatting and level control"""
    level = logging.DEBUG if cfg.ENV == "development" else logging.INFO
    root = logging.getLogger()
    root.setLevel(level)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    root.handlers = [handler]
    
    # Suppress verbose logs from dependencies
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
