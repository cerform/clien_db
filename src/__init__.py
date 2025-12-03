# Telegram Bot Package
__version__ = "1.0.0"
__author__ = "Your Name"

try:
    from src.config import get_config, Config
    __all__ = ['get_config', 'Config']
except ImportError:
    # Если config недоступен, продолжаем без него
    __all__ = []
