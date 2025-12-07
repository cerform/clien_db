"""
INKA Localization Middleware
Интегрирует многоязычную поддержку в INKA
"""

import logging
from typing import Dict, Optional, Any, List
from enum import Enum
from src.services.localization_service import LocalizationService, Language

logger = logging.getLogger(__name__)


class InkaLocalizationMiddleware:
    """
    Middleware для интеграции локализации в INKA
    - Автоматическое определение языка пользователя
    - Перевод входящих сообщений
    - Локализация БД запросов
    - Мультиязычные ответы
    """
    
    def __init__(self, localization_service: LocalizationService):
        """
        Args:
            localization_service: Сервис локализации
        """
        self.localization = localization_service
        self.user_languages: Dict[str, Language] = {}  # telegram_user_id -> Language
    
    def set_user_language(self, user_id: str, language: Language):
        """Установить язык пользователя"""
        self.user_languages[user_id] = language
        logger.info(f"User {user_id} language set to {language.value}")
    
    def get_user_language(self, user_id: str, message_text: str = "") -> Language:
        """
        Получить язык пользователя
        Сначала проверяем сохраненное предпочтение,
        потом определяем по текущему сообщению
        
        Args:
            user_id: Telegram ID пользователя
            message_text: Текст сообщения для определения
        
        Returns:
            Language enum
        """
        # Если язык уже сохранен, возвращаем его
        if user_id in self.user_languages:
            return self.user_languages[user_id]
        
        # Определяем по текущему сообщению
        if message_text:
            detected = self.localization.detect_language(message_text)
            if detected != Language.AUTO:
                self.set_user_language(user_id, detected)
                return detected
        
        # По умолчанию русский
        default_lang = Language.RUSSIAN
        self.set_user_language(user_id, default_lang)
        return default_lang
    
    def process_incoming_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Обработать входящее сообщение
        - Определить язык
        - Перевести на нужный язык (для обработки INKA на английском)
        - Сохранить информацию о языке
        
        Args:
            user_id: Telegram ID пользователя
            message: Исходное сообщение
        
        Returns:
            Dict с processed_message и detected_language
        """
        # Определить язык
        user_lang = self.get_user_language(user_id, message)
        
        # Если сообщение на русском/иврите, переводим на английский для INKA
        # (INKA работает на английском, но может понимать многоязычные ввода)
        processed_message = message
        if user_lang == Language.RUSSIAN:
            processed_message = self.localization.translate_text(message, Language.ENGLISH)
        elif user_lang == Language.HEBREW:
            processed_message = self.localization.translate_text(message, Language.ENGLISH)
        
        logger.info(f"User {user_id} language: {user_lang.value}")
        logger.info(f"Original: {message}")
        logger.info(f"Processed: {processed_message}")
        
        return {
            "original_message": message,
            "processed_message": processed_message,
            "detected_language": user_lang,
            "user_id": user_id
        }
    
    def localize_database_response(self, data: Dict[str, Any], user_lang: Language, 
                                   data_type: str = "service") -> Dict[str, Any]:
        """
        Локализовать ответ из базы данных
        
        Args:
            data: Данные из БД (с полями _ru, _en, _he)
            user_lang: Язык пользователя
            data_type: Тип данных (service, master, booking и т.д.)
        
        Returns:
            Локализованные данные
        """
        localized = data.copy()
        lang_code = user_lang.value
        
        # Определяем какие поля можно локализовать
        localizable_fields = {
            "service": ["name", "description"],
            "master": ["name", "specialization", "bio"],
            "booking": ["service_name", "master_name"],
            "review": ["text"]
        }
        
        fields_to_process = localizable_fields.get(data_type, [])
        
        for field in fields_to_process:
            # Ищем локализованное поле (name_ru, name_en, name_he)
            localized_field = f"{field}_{lang_code}"
            
            if localized_field in data:
                localized[field] = data[localized_field]
            elif f"{field}_ru" in data:
                # Fallback на русский если нет нужного языка
                localized[field] = data[f"{field}_ru"]
        
        return localized
    
    def format_outgoing_message(self, response: str, user_lang: Language) -> str:
        """
        Форматировать исходящее сообщение пользователю
        Убедиться что язык правильный
        
        Args:
            response: Сообщение от INKA
            user_lang: Язык пользователя
        
        Returns:
            Отформатированное сообщение
        """
        # Если ответ на английском, а пользователь говорит по-русски,
        # переводим ответ
        if user_lang == Language.RUSSIAN:
            return self.localization.translate_text(response, Language.RUSSIAN)
        elif user_lang == Language.HEBREW:
            return self.localization.translate_text(response, Language.HEBREW)
        
        return response
    
    def get_schedule_display(self, slots: List[Dict], user_lang: Language) -> str:
        """
        Получить расписание в формате для пользователя на его языке
        
        Args:
            slots: Список доступных слотов
            user_lang: Язык пользователя
        
        Returns:
            Отформатированное расписание
        """
        return self.localization.format_schedule_for_user(slots, user_lang)
    
    def get_localized_response(self, key: str, user_lang: Language, **kwargs) -> str:
        """
        Получить предварительно переведенный ответ системы
        
        Args:
            key: Ключ ответа (greeting, confirm_booking и т.д.)
            user_lang: Язык пользователя
            **kwargs: Переменные для подстановки
        
        Returns:
            Ответ на языке пользователя
        """
        return self.localization.get_response(key, user_lang, **kwargs)
    
    def create_system_prompt_with_localization(self, user_lang: Language) -> str:
        """
        Создать системный промпт для INKA с учетом языка пользователя
        
        Args:
            user_lang: Язык пользователя
        
        Returns:
            Системный промпт на нужном языке
        """
        base_prompt = """You are INKA, a professional receptionist for Ani's tattoo salon.
You help clients book tattoos, piercings, and consultations.

KEY RESPONSIBILITIES:
1. Understand client needs
2. Recommend appropriate masters based on their request
3. Check availability using the calendar
4. Guide them through the booking process
5. Be friendly, professional, and multilingual

IMPORTANT: Always respond in the user's language (Russian, English, or Hebrew).
"""
        
        lang_instructions = {
            Language.RUSSIAN: "Всегда отвечай на РУССКОМ языке. Будь дружелюбна и профессиональна.",
            Language.ENGLISH: "Always respond in ENGLISH. Be friendly and professional.",
            Language.HEBREW: "Always respond in HEBREW (עברית). Be friendly and professional."
        }
        
        lang_note = lang_instructions.get(user_lang, lang_instructions[Language.ENGLISH])
        
        return base_prompt + "\n\n" + lang_note
    
    def extract_booking_intent(self, message: str, user_lang: Language) -> Dict[str, Any]:
        """
        Извлечь намерение бронирования из сообщения
        
        Args:
            message: Сообщение пользователя
            user_lang: Язык пользователя
        
        Returns:
            Dict с найденными параметрами бронирования
        """
        intent = {
            "has_booking_intent": False,
            "service_type": None,  # tattoo, piercing, consultation
            "size": None,           # small, medium, large
            "area": None,           # body area
            "design_type": None,    # style or specific idea
            "preferred_master": None,
            "preferred_date": None,
            "preferred_time": None
        }
        
        # Простые правила для определения интента (можно расширить с ML)
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["запись", "записать", "хочу", "когда", "book", "appointment", "הזמנה"]):
            intent["has_booking_intent"] = True
        
        if any(word in message_lower for word in ["татуировк", "тату", "tattoo", "קעקוע"]):
            intent["service_type"] = "tattoo"
        
        if any(word in message_lower for word in ["пирсинг", "пробить", "piercing", "פירסינג"]):
            intent["service_type"] = "piercing"
        
        if any(word in message_lower for word in ["консультаци", "консул", "consultation", "ייעוץ"]):
            intent["service_type"] = "consultation"
        
        return intent


def create_inka_localization_middleware(openai_api_key: str) -> InkaLocalizationMiddleware:
    """Фабрика для создания middleware локализации"""
    loc_service = LocalizationService(openai_api_key)
    return InkaLocalizationMiddleware(loc_service)
