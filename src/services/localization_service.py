"""
Multilingual Localization Service
Поддерживает автоматический перевод и распознание языков
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from openai import OpenAI

logger = logging.getLogger(__name__)

class Language(Enum):
    """Поддерживаемые языки"""
    RUSSIAN = "ru"
    ENGLISH = "en"
    HEBREW = "he"
    AUTO = "auto"

class LocalizationService:
    """
    Сервис локализации для ИНКА
    - Автоматическое определение языка клиента
    - Перевод информации из БД на нужный язык
    - Мультиязычное взаимодействие
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Инициализация сервиса локализации
        
        Args:
            openai_api_key: OpenAI API ключ для перевода
        """
        self.openai_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        
        # Прямые переводы словаря (часто используемые термины)
        self.glossary = {
            # Общие термины
            "master": {"ru": "мастер", "he": "מהיר", "en": "master"},
            "client": {"ru": "клиент", "he": "לקוח", "en": "client"},
            "service": {"ru": "услуга", "he": "שירות", "en": "service"},
            "booking": {"ru": "запись", "he": "הזמנה", "en": "booking"},
            "schedule": {"ru": "расписание", "he": "לוח זמנים", "en": "schedule"},
            "available": {"ru": "доступно", "he": "זמין", "en": "available"},
            "free": {"ru": "свободно", "he": "פנוי", "en": "free"},
            "busy": {"ru": "занято", "he": "עסוק", "en": "busy"},
            
            # Дни недели
            "monday": {"ru": "понедельник", "he": "יום ב'", "en": "monday"},
            "tuesday": {"ru": "вторник", "he": "יום ג'", "en": "tuesday"},
            "wednesday": {"ru": "среда", "he": "יום ד'", "en": "wednesday"},
            "thursday": {"ru": "четверг", "he": "יום ה'", "en": "thursday"},
            "friday": {"ru": "пятница", "he": "יום ו'", "en": "friday"},
            "saturday": {"ru": "суббота", "he": "יום ש'", "en": "saturday"},
            "sunday": {"ru": "воскресенье", "he": "יום א'", "en": "sunday"},
            
            # Услуги
            "tattoo": {"ru": "татуировка", "he": "קעקוע", "en": "tattoo"},
            "piercing": {"ru": "пирсинг", "he": "פירסינג", "en": "piercing"},
            "consultation": {"ru": "консультация", "he": "ייעוץ", "en": "consultation"},
            "realistic": {"ru": "реалистичные", "he": "אמיתי", "en": "realistic"},
            "minimalism": {"ru": "минимализм", "he": "מינימליזם", "en": "minimalism"},
        }
        
        # Стандартные отклики на разных языках
        self.responses = {
            "greeting": {
                "ru": "Привет! 😊 Хочешь сделать тату или пирсинг?",
                "en": "Hi there! 😊 Interested in a tattoo or piercing?",
                "he": "שלום! 😊 מעוניין בקעקוע או פירסינג?"
            },
            "confirm_booking": {
                "ru": "Отлично! Я записал тебя на {date} в {time} к мастеру {master}.",
                "en": "Great! I've booked you on {date} at {time} with {master}.",
                "he": "מעולה! הזמנתי אותך ב-{date} בשעה {time} עם {master}."
            },
            "no_slots": {
                "ru": "К сожалению, нет свободных слотов на {date}. Попробуй другую дату?",
                "en": "Unfortunately, no available slots on {date}. Try another date?",
                "he": "למצערתי, אין זמנים פנויים ב-{date}. תנסה תאריך אחר?"
            },
            "too_busy": {
                "ru": "Сейчас много клиентов 😅 Может быть, запишешься на потом?",
                "en": "Quite busy right now 😅 How about booking for later?",
                "he": "די עסוק עכשיו 😅 איך לגבי הזמנה מאוחר יותר?"
            }
        }
    
    def detect_language(self, text: str) -> Language:
        """
        Определить язык текста
        
        Args:
            text: Текст для определения
        
        Returns:
            Language enum
        """
        if not text or len(text) < 3:
            return Language.AUTO
        
        # Простое определение по символам
        ru_count = sum(1 for c in text if ord(c) in range(0x0400, 0x04FF))
        he_count = sum(1 for c in text if ord(c) in range(0x0590, 0x05FF))
        en_count = sum(1 for c in text if c.isascii() and c.isalpha())
        
        total = ru_count + he_count + en_count
        if total == 0:
            return Language.AUTO
        
        if ru_count > total * 0.5:
            return Language.RUSSIAN
        elif he_count > total * 0.5:
            return Language.HEBREW
        elif en_count > total * 0.5:
            return Language.ENGLISH
        
        return Language.AUTO
    
    def translate_text(self, text: str, target_language: Language) -> str:
        """
        Перевести текст используя GPT
        
        Args:
            text: Текст для перевода
            target_language: Целевой язык
        
        Returns:
            Переведенный текст
        """
        if target_language == Language.AUTO:
            return text
        
        if not self.client:
            logger.warning("OpenAI client not initialized, returning original text")
            return text
        
        try:
            # Проверяем глоссарий сначала
            text_lower = text.lower()
            if text_lower in self.glossary:
                translation = self.glossary[text_lower].get(target_language.value)
                if translation:
                    return translation
            
            # Используем GPT для перевода
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate the following text to {target_language.name}. Return ONLY the translation, nothing else."
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
    
    def translate_database_row(self, row_dict: Dict, target_language: Language, 
                              fields_to_translate: List[str]) -> Dict:
        """
        Перевести поля БД на нужный язык
        
        Args:
            row_dict: Строка из БД (словарь)
            target_language: Целевой язык
            fields_to_translate: Какие поля переводить
        
        Returns:
            Словарь с переведенными полями
        """
        if target_language == Language.AUTO or target_language == Language.ENGLISH:
            return row_dict
        
        result = row_dict.copy()
        
        for field in fields_to_translate:
            if field in result and result[field]:
                result[f"{field}_translated"] = self.translate_text(str(result[field]), target_language)
        
        return result
    
    def translate_service_info(self, service: Dict, target_language: Language) -> Dict:
        """Перевести информацию о услуге"""
        return self.translate_database_row(
            service, 
            target_language, 
            ["name", "description"]
        )
    
    def translate_master_info(self, master: Dict, target_language: Language) -> Dict:
        """Перевести информацию о мастере"""
        return self.translate_database_row(
            master,
            target_language,
            ["name", "specialization", "bio"]
        )
    
    def format_schedule_for_user(self, slots: List[Dict], target_language: Language) -> str:
        """
        Форматировать расписание для пользователя на нужном языке
        
        Args:
            slots: Список доступных слотов
            target_language: Язык пользователя
        
        Returns:
            Отформатированное расписание
        """
        if not slots:
            return self.responses["no_slots"].get(target_language.value, self.responses["no_slots"]["en"])
        
        lines = []
        lang = target_language.value
        
        for slot in slots[:5]:  # Показываем первые 5 слотов
            date = slot.get("date", "")
            time = slot.get("time", "")
            lines.append(f"  • {date} в {time}")
        
        header_text = {
            "ru": "📅 Доступные слоты:",
            "en": "📅 Available slots:",
            "he": "📅 משבצות זמינות:"
        }.get(lang, "📅 Available slots:")
        
        return header_text + "\n" + "\n".join(lines)
    
    def get_response(self, key: str, target_language: Language, **kwargs) -> str:
        """
        Получить предварительно переведенный ответ
        
        Args:
            key: Ключ ответа (greeting, confirm_booking и т.д.)
            target_language: Язык пользователя
            **kwargs: Переменные для подстановки
        
        Returns:
            Ответ на нужном языке
        """
        lang = target_language.value
        
        if key not in self.responses:
            return ""
        
        response = self.responses[key].get(lang, self.responses[key].get("en", ""))
        
        try:
            return response.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable in response template: {e}")
            return response
    
    @staticmethod
    def get_language_name(language: Language) -> str:
        """Получить название языка"""
        names = {
            Language.RUSSIAN: "Russian",
            Language.ENGLISH: "English",
            Language.HEBREW: "Hebrew",
            Language.AUTO: "Auto-detect"
        }
        return names.get(language, "Unknown")


def get_localization_service(openai_api_key: Optional[str] = None) -> LocalizationService:
    """Фабрика для создания сервиса локализации"""
    return LocalizationService(openai_api_key)
