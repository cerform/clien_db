"""
INKA - Персональный AI-ассистент тату-мастера Ани
Архитектура S1 → S2 → S3
"""

import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class INKAProcessor:
    """INKA - AI-ассистент с трёхуровневой архитектурой"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Инициализация INKA"""
        self.api_key = api_key
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
        
        self.system_prompt = """Ты — ИНКА, персональный AI-ассистент тату-мастера Ани.
Ты встроена в Python-бот системы бронирования.
Ты работаешь строго по архитектуре S1 → S2 → S3.

Ты не выполняешь API-запросы.
Ты не взаимодействуешь с базой данных.
Ты генерируешь ТОЛЬКО ответ для клиента в нужном формате.

ПРАВИЛА:
• Никогда не придумывай данные
• Не генерируй JSON, если явно не указано
• Соблюдай формат выхода строго
• Коротко, живо, тепло, уважительно
• Без давления, без продажного тона"""
    
    def stage_1_classify(self, user_message: str, context: Dict = None) -> Dict:
        """
        S1 - КЛАССИФИКАТОР (возвращает ТОЛЬКО JSON)
        
        Args:
            user_message: Текст от пользователя
            context: Контекст (client_status, has_active_booking и т.д.)
        
        Returns:
            JSON с route, stage, booking_type, intent_summary
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return self._default_classification()
        
        context = context or {}
        
        s1_prompt = f"""Ты S1 классификатор. Твоя ЕДИНСТВЕННАЯ задача — вернуть JSON.

Сообщение пользователя:
"{user_message}"

Контекст:
- client_status: {context.get('client_status', 'unknown')}
- has_active_booking: {context.get('has_active_booking', False)}
- Есть callback_slot_id: {context.get('callback_slot_id', None) is not None}

ПРАВИЛА КЛАССИФИКАЦИИ:
1. Клиент хочет записаться → route="booking", stage="offer_slots"
2. Клиент выбирает слот (callback_slot_id есть) → route="booking_confirm", stage="confirming_choice"
3. Есть активная бронь и запрос на изменение → route="booking_reschedule"
4. Вопросы о цене, уходе, боли → route="info"
5. Обсуждение идеи татуировки → route="consultation"
6. Остальное → route="other"

Допустимые значения:
- route: [booking, booking_confirm, booking_reschedule, consultation, info, other]
- stage: [offer_slots, waiting_client_choice, confirming_choice, completed, error, none]
- booking_type: [tattoo, consultation, walk-in, none]

Верни СТРОГО этот JSON, без текста:
{{
  "route": "...",
  "stage": "...",
  "booking_type": "...",
  "intent_summary": "..."
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": s1_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Извлекаем JSON из ответа
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse S1 response: {response_text}")
                return self._default_classification()
        
        except Exception as e:
            logger.error(f"S1 classification error: {e}")
            return self._default_classification()
    
    def stage_2_booking_engine(self, 
                               stage: str, 
                               available_slots: List[Dict] = None,
                               slot_taken: bool = False,
                               booking_info: Dict = None) -> str:
        """
        S2 - BOOKING ENGINE (возвращает ТОЛЬКО ТЕКСТ)
        
        Args:
            stage: offer_slots или confirming_choice
            available_slots: Список доступных слотов
            slot_taken: Занят ли выбранный слот
            booking_info: Информация о бронировании
        
        Returns:
            Текстовый ответ для клиента
        """
        if stage == "offer_slots":
            return self._offer_slots_text(available_slots or [])
        
        elif stage == "confirming_choice":
            return self._confirming_choice_text(slot_taken, booking_info or {})
        
        else:
            return "Что-то пошло не так. Давай попробуем заново."
    
    def stage_3_post_booking(self, action: str, booking_data: Dict = None) -> str:
        """
        S3 - ПОСЛЕ БРОНИ (возвращает ТОЛЬКО ТЕКСТ)
        
        Args:
            action: Тип действия (confirm, reschedule, cancel и т.д.)
            booking_data: Данные о бронировании
        
        Returns:
            Текстовый ответ
        """
        booking_data = booking_data or {}
        
        if action == "confirm":
            date = booking_data.get("date", "")
            time = booking_data.get("time", "")
            return f"""Отлично! Закрепила за тобой {date} в {time}.
Скоро пришлю детали подготовки."""
        
        elif action == "reschedule":
            return "Хорошо, давай выберем новое время для твоей записи."
        
        elif action == "cancel":
            return "Запись отменена. Будешь скучать 😔"
        
        else:
            return "Что дальше?"
    
    # ==================== ПРИВАТНЫЕ МЕТОДЫ ====================
    
    def _default_classification(self) -> Dict:
        """Классификация по умолчанию"""
        return {
            "route": "other",
            "stage": "none",
            "booking_type": "none",
            "intent_summary": "Не удалось определить намерение"
        }
    
    def _offer_slots_text(self, available_slots: List[Dict]) -> str:
        """S2: Предложение доступных слотов"""
        if not available_slots:
            return """Сейчас свободных окон для этого типа записи нет.
Могу написать, как только появится подходящее время."""
        
        slots_text = "\n".join([
            f"• {self._format_slot(slot)}"
            for slot in available_slots
        ])
        
        return f"""Вот свободные окна:

{slots_text}

Нажми на удобный вариант, и я закреплю время."""
    
    def _confirming_choice_text(self, slot_taken: bool, booking_info: Dict) -> str:
        """S2: Подтверждение выбора слота"""
        if slot_taken:
            return """Этот слот только что заняли.
Могу показать другие свободные варианты."""
        
        date = booking_info.get("date", "")
        time = booking_info.get("time", "")
        
        return f"""Отлично, закрепила за тобой {date} в {time}.
Скоро пришлю детали подготовки."""
    
    def _format_slot(self, slot: Dict) -> str:
        """Форматирование слота в читаемый вид"""
        date_str = slot.get("date", "")
        time_str = slot.get("start_time", "")
        
        if date_str and time_str:
            # Преобразование YYYY-MM-DD в DD.MM
            try:
                parts = date_str.split("-")
                if len(parts) == 3:
                    day, month = parts[2], parts[1]
                    return f"{day}.{month} в {time_str}"
            except:
                pass
        
        return f"{date_str} в {time_str}"


def get_inka_processor(api_key: Optional[str] = None) -> INKAProcessor:
    """Фабрика для создания INKA процессора"""
    return INKAProcessor(api_key)
