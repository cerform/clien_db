"""
INKA - Персональный AI-ассистент тату-мастера Ани
Архитектура S1 → S2 → S3 с улучшенным диалогом
"""

import json
import logging
import time
from typing import Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class INKAProcessor:
    """INKA - AI-ассистент с трёхуровневой архитектурой и человечным общением"""
    
    def __init__(self, api_key: Optional[str] = None, assistant_id: str = "asst_LBGeLxauJ3nYbauR3pilbifN"):
        """Инициализация INKA"""
        self.api_key = api_key
        self.assistant_id = assistant_id
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
        
        # Основной системный промпт для классификации
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
        
        # Промпт для человечного общения
        self.conversational_prompt = """Ты — ИНКА, дружелюбный и понимающий AI-ассистент тату-мастера Ани.

ТВОЯ ЛИЧНОСТЬ:
• Теплая, искренняя, понимающая
• Говоришь естественно, как живой человек
• Используешь эмодзи умеренно и уместно
• Проявляешь эмпатию и заботу о клиенте
• Умеешь поддержать беседу на разные темы

СТИЛЬ ОБЩЕНИЯ:
• Пиши коротко, живо, без канцелярщины
• Задавай уточняющие вопросы, если что-то непонятно
• Запоминай контекст разговора
• Отвечай на вопросы клиента, даже если они не связаны с записью
• Если не знаешь ответа — честно признайся, предложи связаться с мастером

ЗАПРЕЩЕНО:
• Придумывать информацию о ценах, услугах, мастере
• Давить на клиента или настаивать на записи
• Игнорировать вопросы клиента
• Отвечать шаблонно или формально

Твоя главная цель — создать комфортную атмосферу общения и помочь клиенту."""
    
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
4. Вопросы о цене, уходе, боли, процедуре → route="info"
5. Обсуждение идеи татуировки, консультация → route="consultation"
6. Общие вопросы, приветствия, благодарности → route="conversation"
7. Остальное → route="other"

Допустимые значения:
- route: [booking, booking_confirm, booking_reschedule, consultation, info, conversation, other]
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
                model="gpt-4o-mini",  # Улучшенная модель
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": s1_prompt}
                ],
                temperature=0.3,
                max_tokens=200,
                timeout=10.0
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Извлекаем JSON из ответа
            try:
                result = json.loads(response_text)
                logger.info(f"S1 Classification: route={result.get('route')}, summary={result.get('intent_summary')}")
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
    
    def conversational_response(self, user_message: str, conversation_history: List[Dict] = None, 
                                context: Dict = None) -> str:
        """
        Человечный диалоговый ответ с использованием Assistant API
        
        Args:
            user_message: Сообщение пользователя
            conversation_history: История диалога [{"role": "user", "content": "..."}, ...]
            context: Дополнительный контекст (имя клиента, статус и т.д.)
        
        Returns:
            Естественный человечный ответ
        """
        if not self.client:
            logger.error("OpenAI client not initialized")
            return "Извини, у меня временные технические проблемы. Попробуй чуть позже? 🙏"
        
        context = context or {}
        conversation_history = conversation_history or []
        
        try:
            # Используем Assistant API для более глубокого понимания контекста
            if self.assistant_id:
                return self._use_assistant_api(user_message, conversation_history, context)
            else:
                return self._use_chat_completion(user_message, conversation_history, context)
        
        except Exception as e:
            logger.error(f"Conversational response error: {e}")
            return "Прости, что-то пошло не так. Можешь повторить? 🙏"
    
    def _use_assistant_api(self, user_message: str, conversation_history: List[Dict], 
                           context: Dict) -> str:
        """Использование Assistant API для диалога"""
        try:
            # Создаем thread для разговора
            thread = self.client.beta.threads.create()
            
            # Добавляем историю разговора
            for msg in conversation_history[-5:]:  # Последние 5 сообщений
                self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role=msg.get("role", "user"),
                    content=msg.get("content", "")
                )
            
            # Добавляем контекст
            context_info = ""
            if context.get("client_name"):
                context_info += f"\nИмя клиента: {context['client_name']}"
            if context.get("has_active_booking"):
                context_info += f"\nУ клиента есть активная запись"
            
            # Добавляем текущее сообщение
            message_content = user_message
            if context_info:
                message_content = f"{user_message}{context_info}"
            
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message_content
            )
            
            # Запускаем Assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Ждем завершения (с таймаутом)
            timeout = 30  # 30 секунд
            start_time = time.time()
            while run.status in ["queued", "in_progress"]:
                if time.time() - start_time > timeout:
                    logger.error("Assistant API timeout")
                    return self._use_chat_completion(user_message, conversation_history, context)
                
                time.sleep(0.5)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Получаем ответ
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                response = messages.data[0].content[0].text.value
                return response
            else:
                logger.warning(f"Assistant run failed with status: {run.status}")
                return self._use_chat_completion(user_message, conversation_history, context)
        
        except Exception as e:
            logger.error(f"Assistant API error: {e}")
            return self._use_chat_completion(user_message, conversation_history, context)
    
    def _use_chat_completion(self, user_message: str, conversation_history: List[Dict], 
                             context: Dict) -> str:
        """Fallback: использование Chat Completion API"""
        # Формируем сообщения
        messages = [{"role": "system", "content": self.conversational_prompt}]
        
        # Добавляем историю
        messages.extend(conversation_history[-5:])
        
        # Добавляем контекст
        context_info = []
        if context.get("client_name"):
            context_info.append(f"Имя клиента: {context['client_name']}")
        if context.get("has_active_booking"):
            context_info.append("У клиента есть активная запись")
        
        if context_info:
            context_text = "\n".join(context_info)
            user_message = f"{user_message}\n\n[Контекст: {context_text}]"
        
        messages.append({"role": "user", "content": user_message})
        
        # Запрос к API
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,  # Больше креативности
            max_tokens=500,
            timeout=15.0
        )
        
        return response.choices[0].message.content.strip()
    
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


def get_inka_processor(api_key: Optional[str] = None, assistant_id: Optional[str] = None) -> INKAProcessor:
    """Фабрика для создания INKA процессора"""
    return INKAProcessor(api_key, assistant_id or "asst_LBGeLxauJ3nYbauR3pilbifN")
