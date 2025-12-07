"""
AI обработка текста для бота
"""

from .processor import AIProcessor, get_ai_processor
from .inka_localization import InkaLocalizationMiddleware, create_inka_localization_middleware

__all__ = [
    'AIProcessor',
    'get_ai_processor',
    'InkaLocalizationMiddleware',
    'create_inka_localization_middleware'
]
