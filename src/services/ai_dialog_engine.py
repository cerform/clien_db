"""
AI Dialog Engine - Полноценный диалоговый движок на базе GPT
Обрабатывает ВСЕ сообщения через AI, поддерживает любой язык,
выполняет административные функции через natural language
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """Роли пользователей"""
    CLIENT = "client"
    ADMIN = "admin"
    MASTER = "master"


class ActionType(Enum):
    """Типы действий, которые может выполнять AI"""
    # Клиентские действия
    SHOW_AVAILABLE_SLOTS = "show_available_slots"
    CREATE_BOOKING = "create_booking"
    CANCEL_BOOKING = "cancel_booking"
    RESCHEDULE_BOOKING = "reschedule_booking"
    SHOW_MY_BOOKINGS = "show_my_bookings"
    
    # Административные действия
    VIEW_ALL_BOOKINGS = "view_all_bookings"
    VIEW_SCHEDULE = "view_schedule"
    ADD_AVAILABLE_SLOT = "add_available_slot"
    REMOVE_SLOT = "remove_slot"
    VIEW_STATISTICS = "view_statistics"
    SEND_MESSAGE_TO_CLIENT = "send_message_to_client"
    
    # Информационные
    CONSULTATION = "consultation"
    INFO = "info"
    CHAT = "chat"


class AIDialogEngine:
    """
    Центральный AI-движок для обработки всех сообщений
    Полностью заменяет клавиатуры и команды естественным языком
    """
    
    def __init__(self, api_key: str = None, default_language: str = "ru"):
        """
        Инициализация AI движка
        
        Args:
            api_key: OpenAI API ключ (опционально, работает и без него)
            default_language: Язык по умолчанию (ru, en, he)
        """
        self.api_enabled = False
        self.client = None
        
        # Определяем провайдера по ключу
        is_groq = api_key and api_key.startswith("gsk_")
        self.provider = "Groq" if is_groq else "OpenAI"
        
        # Пробуем инициализировать AI клиент (OpenAI или Groq)
        if api_key and api_key != "YOUR_OPENAI_API_KEY" and OpenAI:
            try:
                import httpx
                import ssl
                
                # Create custom HTTP client with SSL disabled
                http_client = httpx.Client(
                    verify=False,  # Disable SSL verification
                    timeout=30.0
                )
                
                client_kwargs = {
                    "api_key": api_key,
                    "http_client": http_client,
                    "timeout": 30.0,
                    "max_retries": 2
                }
                
                # Groq использует OpenAI-совместимый API
                if is_groq:
                    client_kwargs["base_url"] = "https://api.groq.com/openai/v1"
                    self.model = "llama-3.3-70b-versatile"  # Быстрая модель Groq
                else:
                    self.model = "gpt-4o-mini"  # Быстрая и экономичная модель OpenAI
                
                self.client = OpenAI(**client_kwargs)
                self.api_enabled = True
                logger.info(f"✅ {self.provider} API enabled (model: {self.model})")
            except Exception as e:
                logger.warning(f"⚠️ {self.provider} API disabled: {e}")
                self.client = None
                self.api_enabled = False
                self.model = "gpt-4o-mini"
        else:
            logger.info("ℹ️ Running in fallback mode (no AI API)")
            self.model = "gpt-4o-mini"
        self.default_language = default_language
        
        # История диалогов (user_id -> messages)
        self.conversation_history: Dict[int, List[Dict]] = {}
        
        # Максимальная длина истории
        self.max_history_length = 20
        
    def _get_system_prompt(self, user_role: UserRole, user_info: Dict) -> str:
        """
        Генерирует system prompt в зависимости от роли пользователя
        
        Args:
            user_role: Роль пользователя
            user_info: Информация о пользователе (имя, язык, и т.д.)
            
        Returns:
            System prompt для AI
        """
        base_personality = """Ты - интеллектуальный ассистент тату-студии. 
        
Твои ключевые качества:
- Дружелюбный и профессиональный
- Понимаешь и отвечаешь на русском, английском и иврите
- Автоматически определяешь язык клиента и общаешься на нём
- Помогаешь с записями, консультациями и информацией
- Можешь выполнять административные функции"""

        if user_role == UserRole.CLIENT:
            return f"""{base_personality}

КАК КЛИЕНТСКИЙ АССИСТЕНТ ты можешь:

1. **Консультировать** по татуировкам:
   - Стили, размеры, расположение
   - Время заживления и уход
   - Ориентировочные цены и длительность

2. **Управлять записями**:
   - Показывать свободное время
   - Создавать бронирования
   - Переносить и отменять записи
   - Показывать текущие записи клиента

3. **Общаться естественно**:
   - Отвечать на любые вопросы
   - Поддерживать контекст разговора
   - Быть эмпатичным и полезным

ВАЖНО:
- Всегда отвечай на ЯЗЫКЕ КЛИЕНТА
- Если нужно выполнить действие (запись, отмена), верни JSON с action
- Никогда не придумывай даты и время - только из реальной БД
- Если что-то непонятно - уточни у клиента

Текущий клиент: {user_info.get('name', 'Гость')}
Предпочитаемый язык: {user_info.get('language', 'ru')}"""

        elif user_role == UserRole.ADMIN:
            return f"""{base_personality}

КАК АДМИНИСТРАТИВНЫЙ АССИСТЕНТ ты можешь:

1. **Управлять расписанием**:
   - Просматривать все записи
   - Добавлять/удалять слоты времени
   - Видеть статистику бронирований

2. **Работать с клиентами**:
   - Просматривать информацию о клиентах
   - Отправлять сообщения клиентам
   - Управлять записями любого клиента

3. **Аналитика**:
   - Статистика по записям
   - Загруженность мастера
   - Популярные услуги

ВАЖНО:
- У тебя есть полный административный доступ
- Отвечай на языке администратора
- Для действий возвращай JSON с action и parameters

Администратор: {user_info.get('name', 'Admin')}"""

        elif user_role == UserRole.MASTER:
            return f"""{base_personality}

КАК АССИСТЕНТ МАСТЕРА ты можешь:

1. **Управлять своим расписанием**:
   - Просматривать сегодняшние/будущие записи
   - Блокировать/открывать время
   - Отмечать выполненные сеансы

2. **Общаться с клиентами**:
   - Подтверждать записи
   - Отправлять напоминания
   - Отменять при необходимости

3. **Видеть статистику**:
   - Количество клиентов
   - Выручка
   - Загруженность

Мастер: {user_info.get('name', 'Master')}"""

        return base_personality

    def _build_function_definitions(self, user_role: UserRole) -> List[Dict]:
        """
        Определяет доступные функции для AI в зависимости от роли
        
        Args:
            user_role: Роль пользователя
            
        Returns:
            Список определений функций для OpenAI Function Calling
        """
        functions = []
        
        # Функции для всех
        functions.extend([
            {
                "name": "show_available_slots",
                "description": "Показать доступные слоты для записи на указанную дату или диапазон дат",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Начальная дата в формате YYYY-MM-DD"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "Конечная дата в формате YYYY-MM-DD (опционально)"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Требуемая длительность сеанса в минутах (60, 120, 180, 240)"
                        }
                    },
                    "required": ["start_date"]
                }
            },
            {
                "name": "create_booking",
                "description": "Создать новую запись на татуировку",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "slot_id": {
                            "type": "string",
                            "description": "ID выбранного слота времени"
                        },
                        "date": {
                            "type": "string",
                            "description": "Дата записи в формате YYYY-MM-DD"
                        },
                        "time": {
                            "type": "string",
                            "description": "Время записи в формате HH:MM"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Длительность сеанса в минутах"
                        },
                        "description": {
                            "type": "string",
                            "description": "Описание татуировки"
                        }
                    },
                    "required": ["date", "time", "duration_minutes"]
                }
            },
            {
                "name": "show_my_bookings",
                "description": "Показать все записи пользователя (прошлые и будущие)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["all", "upcoming", "past", "pending"],
                            "description": "Фильтр по статусу записей"
                        }
                    }
                }
            },
            {
                "name": "cancel_booking",
                "description": "Отменить существующую запись",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "ID записи для отмены"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Причина отмены (опционально)"
                        }
                    },
                    "required": ["booking_id"]
                }
            },
            {
                "name": "reschedule_booking",
                "description": "Перенести существующую запись на другое время",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "ID записи для переноса"
                        },
                        "new_date": {
                            "type": "string",
                            "description": "Новая дата в формате YYYY-MM-DD"
                        },
                        "new_time": {
                            "type": "string",
                            "description": "Новое время в формате HH:MM"
                        }
                    },
                    "required": ["booking_id"]
                }
            }
        ])
        
        # Административные функции
        if user_role in [UserRole.ADMIN, UserRole.MASTER]:
            functions.extend([
                {
                    "name": "view_all_bookings",
                    "description": "Просмотреть все записи в системе с фильтрацией",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Фильтр по дате YYYY-MM-DD"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["all", "pending", "confirmed", "completed", "cancelled"],
                                "description": "Фильтр по статусу"
                            },
                            "client_name": {
                                "type": "string",
                                "description": "Фильтр по имени клиента"
                            }
                        }
                    }
                },
                {
                    "name": "view_schedule",
                    "description": "Просмотреть расписание мастера на дату/период",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Начальная дата YYYY-MM-DD"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "Конечная дата YYYY-MM-DD"
                            }
                        },
                        "required": ["start_date"]
                    }
                },
                {
                    "name": "add_available_slot",
                    "description": "Добавить новый доступный слот в расписание",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Дата YYYY-MM-DD"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "Время начала HH:MM"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "Время окончания HH:MM"
                            }
                        },
                        "required": ["date", "start_time", "end_time"]
                    }
                },
                {
                    "name": "remove_slot",
                    "description": "Удалить или заблокировать слот в расписании",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "slot_id": {
                                "type": "string",
                                "description": "ID слота для удаления"
                            },
                            "date": {
                                "type": "string",
                                "description": "Дата слота YYYY-MM-DD"
                            },
                            "time": {
                                "type": "string",
                                "description": "Время слота HH:MM"
                            }
                        }
                    }
                },
                {
                    "name": "view_statistics",
                    "description": "Получить статистику по записям и клиентам",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "period": {
                                "type": "string",
                                "enum": ["today", "week", "month", "all"],
                                "description": "Период для статистики"
                            }
                        }
                    }
                },
                {
                    "name": "send_message_to_client",
                    "description": "Отправить сообщение клиенту",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "client_id": {
                                "type": "string",
                                "description": "ID клиента"
                            },
                            "message": {
                                "type": "string",
                                "description": "Текст сообщения"
                            }
                        },
                        "required": ["client_id", "message"]
                    }
                }
            ])
        
        return functions

    async def process_message(
        self,
        user_id: int,
        message: str,
        user_role: UserRole = UserRole.CLIENT,
        user_info: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Обработка входящего сообщения через AI
        
        Args:
            user_id: ID пользователя
            message: Текст сообщения
            user_role: Роль пользователя
            user_info: Дополнительная информация о пользователе
            context: Контекст (доступные слоты, текущие записи и т.д.)
            
        Returns:
            {
                "response": "Текст ответа",
                "action": "action_type" | None,
                "action_params": {...} | None,
                "language": "detected_language",
                "requires_confirmation": bool
            }
        """
        try:
            user_info = user_info or {}
            context = context or {}
            
            # Инициализация истории для нового пользователя
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # Добавляем сообщение пользователя в историю
            self.conversation_history[user_id].append({
                "role": "user",
                "content": message
            })
            
            # Ограничиваем историю
            if len(self.conversation_history[user_id]) > self.max_history_length:
                # Оставляем первое сообщение (контекст) и последние N
                self.conversation_history[user_id] = (
                    [self.conversation_history[user_id][0]] + 
                    self.conversation_history[user_id][-(self.max_history_length-1):]
                )
            
            # Формируем system prompt
            system_prompt = self._get_system_prompt(user_role, user_info)
            
            # Добавляем контекст если есть
            if context:
                context_str = f"\n\nТЕКУЩИЙ КОНТЕКСТ:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
                system_prompt += context_str
            
            # Получаем определения функций
            functions = self._build_function_definitions(user_role)
            
            # Определяем язык ДО всех вызовов
            detected_language = self._detect_language(message)
            logger.info(f"🌐 Detected language: {detected_language}")
            
            # Проверяем, доступен ли AI API
            if not self.api_enabled or not self.client:
                logger.warning("⚠️ AI API not enabled, using fallback")
                # Fallback: используем rule-based ответы
                return self._fallback_response(message, user_role, detected_language)
            
            # Вызов AI API с Function Calling
            messages = [
                {"role": "system", "content": system_prompt}
            ] + self.conversation_history[user_id]
            
            logger.info(f"🔄 Calling {self.provider} API...")
            logger.info(f"   Model: {self.model}")
            logger.info(f"   Messages count: {len(messages)}")
            logger.info(f"   Functions count: {len(functions)}")
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=functions,
                    function_call="auto",
                    temperature=0.7,
                    max_tokens=1000
                )
                logger.info(f"✅ {self.provider} API responded successfully")
            except Exception as api_error:
                # Если ошибка API (quota, rate limit и т.д.) - используем fallback
                logger.error(f"❌ {self.provider} API error: {api_error}")
                logger.info("🔄 Switching to fallback mode...")
                return self._fallback_response(message, user_role, detected_language)
            
            assistant_message = response.choices[0].message
            
            # Проверяем, вызвана ли функция
            if assistant_message.function_call:
                function_name = assistant_message.function_call.name
                # Groq возвращает arguments как строку JSON
                function_args_raw = assistant_message.function_call.arguments
                function_args = json.loads(function_args_raw) if isinstance(function_args_raw, str) else function_args_raw
                
                # Сохраняем в историю (для Groq arguments должен быть строкой)
                self.conversation_history[user_id].append({
                    "role": "assistant",
                    "content": assistant_message.content or f"Выполняю действие: {function_name}",
                    "function_call": {
                        "name": function_name,
                        "arguments": json.dumps(function_args) if isinstance(function_args, dict) else function_args
                    }
                })
                
                return {
                    "response": assistant_message.content or self._get_action_confirmation_message(function_name, detected_language),
                    "action": function_name,
                    "action_params": function_args,
                    "language": detected_language,
                    "requires_confirmation": self._requires_confirmation(function_name),
                    "timestamp": datetime.now().isoformat()
                }
            
            else:
                # Обычный ответ без действия
                response_text = assistant_message.content
                
                # Сохраняем в историю
                self.conversation_history[user_id].append({
                    "role": "assistant",
                    "content": response_text
                })
                
                detected_language = self._detect_language(message)
                
                return {
                    "response": response_text,
                    "action": None,
                    "action_params": None,
                    "language": detected_language,
                    "requires_confirmation": False,
                    "timestamp": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.exception(f"AI Dialog Engine error: {e}")
            return {
                "response": "Извините, произошла ошибка. Пожалуйста, попробуйте еще раз.",
                "action": None,
                "action_params": None,
                "language": self.default_language,
                "requires_confirmation": False,
                "error": str(e)
            }
    
    def _detect_language(self, text: str) -> str:
        """
        Простое определение языка по тексту
        
        Args:
            text: Текст для анализа
            
        Returns:
            Код языка: 'ru', 'en', 'he'
        """
        # Проверка на кириллицу
        if any('\u0400' <= char <= '\u04FF' for char in text):
            return 'ru'
        
        # Проверка на иврит
        if any('\u0590' <= char <= '\u05FF' for char in text):
            return 'he'
        
        # По умолчанию английский
        return 'en'
    
    def _fallback_response(self, message: str, user_role: str, language: str) -> Dict:
        """
        Fallback режим без OpenAI API - используем простые правила
        
        Args:
            message: Сообщение пользователя
            user_role: Роль пользователя
            language: Язык
            
        Returns:
            Ответ в формате AI engine
        """
        message_lower = message.lower()
        
        # Приветствия
        greetings = {
            'ru': ['привет', 'здравствуй', 'добрый', 'hi', 'hello'],
            'en': ['hi', 'hello', 'hey', 'good morning', 'good day'],
            'he': ['שלום', 'היי', 'בוקר טוב']
        }
        
        # Запись/тату
        booking_keywords = {
            'ru': ['запись', 'записаться', 'тату', 'tattoo', 'хочу', 'сделать', 'маленьк'],
            'en': ['appointment', 'booking', 'tattoo', 'want', 'book', 'make', 'small'],
            'he': ['תור', 'קעקוע', 'רוצה', 'לעשות']
        }
        
        # Вопросы о ценах
        price_keywords = {
            'ru': ['цена', 'стоимость', 'сколько', 'стоит', 'прайс', 'цены'],
            'en': ['price', 'cost', 'how much', 'pricing'],
            'he': ['מחיר', 'כמה', 'עלות']
        }
        
        # Вопросы о портфолио/работах
        portfolio_keywords = {
            'ru': ['работы', 'портфолио', 'примеры', 'фото', 'галерея'],
            'en': ['portfolio', 'works', 'examples', 'photos', 'gallery'],
            'he': ['עבודות', 'תיק', 'דוגמאות']
        }
        
        # Вопросы об уходе
        care_keywords = {
            'ru': ['уход', 'заживление', 'после', 'как ухаживать'],
            'en': ['care', 'healing', 'aftercare', 'after'],
            'he': ['טיפול', 'אחרי', 'ריפוי']
        }
        
        responses = {
            'ru': {
                'greeting': 'Здравствуйте! 👋\n\nЯ помогу вам записаться на сеанс татуировки.\n\nРасскажите:\n• Какую татуировку хотите сделать?\n• Желаемое место на теле\n• Примерный размер\n\nПосле этого предложу доступное время! 📅',
                'booking': 'Отлично! 🎨\n\nДля записи мне нужно:\n1️⃣ Описание татуировки\n2️⃣ Место на теле\n3️⃣ Размер (см)\n4️⃣ Желаемая дата\n\nНапишите эту информацию, и я покажу свободные слоты!',
                'price': '💰 **Цены на татуировки:**\n\n• Маленькая (до 5см) - от $50\n• Средняя (5-10см) - от $100\n• Большая (10-20см) - от $200\n• Рукав/спина - от $500\n\nТочная цена зависит от сложности!\n\nХотите записаться? Опишите что хотите сделать 🎨',
                'portfolio': '🎨 **Посмотреть работы:**\n\n📸 Instagram: [ваш_аккаунт]\n🌐 Сайт: [ваш_сайт]\n\nТам вы найдёте примеры работ в разных стилях!\n\nЕсли понравилось - пишите, запишу на сеанс! ✨',
                'care': '💡 **Уход за татуировкой:**\n\n1. Первые 2-3 часа - не снимать плёнку\n2. Промывать тёплой водой с мылом 2-3 раза в день\n3. Наносить заживляющую мазь (Bepanthen/Panthenol)\n4. Не чесать, не сдирать корочки!\n5. Избегать солнца 2-3 недели\n\nПодробные инструкции дам после сеанса! 📋',
                'default': 'Спасибо за сообщение!\n\nЧтобы записаться на сеанс татуировки, расскажите:\n• Что хотите сделать\n• Где (место на теле)\n• Размер\n• Когда хотите прийти\n\nОтвечу в ближайшее время! ⏰'
            },
            'en': {
                'greeting': 'Hello! 👋\n\nI will help you book a tattoo session.\n\nPlease tell me:\n• What tattoo do you want?\n• Desired body placement\n• Approximate size\n\nThen I\'ll suggest available times! 📅',
                'booking': 'Great! 🎨\n\nFor booking I need:\n1️⃣ Tattoo description\n2️⃣ Body placement\n3️⃣ Size (cm)\n4️⃣ Preferred date\n\nWrite this info and I\'ll show available slots!',
                'price': '💰 **Tattoo Pricing:**\n\n• Small (up to 5cm) - from $50\n• Medium (5-10cm) - from $100\n• Large (10-20cm) - from $200\n• Sleeve/back - from $500\n\nFinal price depends on complexity!\n\nWant to book? Describe what you want 🎨',
                'portfolio': '🎨 **View our works:**\n\n📸 Instagram: [your_account]\n🌐 Website: [your_site]\n\nCheck out examples in different styles!\n\nLike what you see? Message me to book! ✨',
                'care': '💡 **Tattoo Aftercare:**\n\n1. First 2-3 hours - keep the film on\n2. Wash with warm water & soap 2-3 times daily\n3. Apply healing ointment (Bepanthen/Panthenol)\n4. Don\'t scratch or pick scabs!\n5. Avoid sun for 2-3 weeks\n\nDetailed instructions after session! 📋',
                'default': 'Thanks for your message!\n\nTo book a tattoo session, tell me:\n• What you want\n• Where (body placement)\n• Size\n• When you want to come\n\nI\'ll reply soon! ⏰'
            },
            'he': {
                'greeting': 'שלום! 👋\n\nאני אעזור לך לקבוע תור לקעקוע.\n\nספר לי:\n• איזה קעקוע את/ה רוצה?\n• מיקום על הגוף\n• גודל משוער\n\nאחר כך אציע זמנים פנויים! 📅',
                'booking': 'מעולה! 🎨\n\nלקביעת תור אני צריך:\n1️⃣ תיאור הקעקוע\n2️⃣ מיקום על הגוף\n3️⃣ גודל (ס"מ)\n4️⃣ תאריך מועדף\n\nכתוב את המידע ואראה זמנים פנויים!',
                'default': 'תודה על ההודעה!\n\nכדי לקבוע תור לקעקוע, ספר לי:\n• מה את/ה רוצה\n• איפה (מיקום על הגוף)\n• גודל\n• מתי את/ה רוצה לבוא\n\nאחזור אליך בקרוב! ⏰'
            }
        }
        
        # Выбираем ответ
        lang_responses = responses.get(language, responses['en'])
        
        # Проверяем тип сообщения
        is_greeting = any(word in message_lower for word in greetings.get(language, []))
        is_booking = any(word in message_lower for word in booking_keywords.get(language, []))
        is_price = any(word in message_lower for word in price_keywords.get(language, []))
        is_portfolio = any(word in message_lower for word in portfolio_keywords.get(language, []))
        is_care = any(word in message_lower for word in care_keywords.get(language, []))
        
        if is_greeting:
            response_text = lang_responses['greeting']
        elif is_price:
            response_text = lang_responses.get('price', lang_responses['default'])
        elif is_portfolio:
            response_text = lang_responses.get('portfolio', lang_responses['default'])
        elif is_care:
            response_text = lang_responses.get('care', lang_responses['default'])
        elif is_booking:
            response_text = lang_responses['booking']
        else:
            response_text = lang_responses['default']
        
        return {
            "response": response_text,
            "action": None,
            "action_params": {},
            "language": language,
            "requires_confirmation": False,
            "timestamp": datetime.now().isoformat()
        }
    
    def _requires_confirmation(self, function_name: str) -> bool:
        """
        Определяет, требуется ли подтверждение для действия
        
        Args:
            function_name: Название функции
            
        Returns:
            True если требуется подтверждение
        """
        confirmation_required = [
            "create_booking",
            "cancel_booking",
            "reschedule_booking",
            "remove_slot",
            "send_message_to_client"
        ]
        return function_name in confirmation_required
    
    def _get_action_confirmation_message(self, function_name: str, language: str) -> str:
        """
        Возвращает сообщение подтверждения действия на нужном языке
        
        Args:
            function_name: Название функции
            language: Язык
            
        Returns:
            Текст подтверждения
        """
        messages = {
            "ru": {
                "create_booking": "Создаю запись...",
                "cancel_booking": "Отменяю запись...",
                "reschedule_booking": "Переношу запись...",
                "show_available_slots": "Проверяю свободное время...",
                "show_my_bookings": "Загружаю ваши записи...",
                "view_all_bookings": "Загружаю все записи...",
                "add_available_slot": "Добавляю слот в расписание...",
                "remove_slot": "Удаляю слот...",
                "view_statistics": "Собираю статистику...",
            },
            "en": {
                "create_booking": "Creating booking...",
                "cancel_booking": "Cancelling booking...",
                "reschedule_booking": "Rescheduling booking...",
                "show_available_slots": "Checking available time...",
                "show_my_bookings": "Loading your bookings...",
                "view_all_bookings": "Loading all bookings...",
                "add_available_slot": "Adding slot to schedule...",
                "remove_slot": "Removing slot...",
                "view_statistics": "Collecting statistics...",
            },
            "he": {
                "create_booking": "יוצר הזמנה...",
                "cancel_booking": "מבטל הזמנה...",
                "reschedule_booking": "משנה הזמנה...",
                "show_available_slots": "בודק זמנים פנויים...",
                "show_my_bookings": "טוען את ההזמנות שלך...",
                "view_all_bookings": "טוען את כל ההזמנות...",
                "add_available_slot": "מוסיף משבצת ללוח זמנים...",
                "remove_slot": "מוחק משבצת...",
                "view_statistics": "אוסף סטטיסטיקות...",
            }
        }
        
        return messages.get(language, messages["en"]).get(function_name, "Processing...")
    
    def clear_history(self, user_id: int):
        """Очистить историю диалога пользователя"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            logger.info(f"Cleared conversation history for user {user_id}")
    
    def get_conversation_summary(self, user_id: int) -> Optional[str]:
        """
        Получить краткое резюме диалога
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Краткое резюме или None
        """
        if user_id not in self.conversation_history or not self.conversation_history[user_id]:
            return None
        
        try:
            messages = self.conversation_history[user_id]
            
            summary_prompt = """Создай краткое резюме этого диалога (2-3 предложения):
- Что хочет клиент
- Какие действия были выполнены
- Что нужно сделать дальше"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages + [{"role": "user", "content": summary_prompt}],
                temperature=0.5,
                max_tokens=200
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Failed to create summary: {e}")
            return None


# Export
__all__ = ["AIDialogEngine", "UserRole", "ActionType"]
