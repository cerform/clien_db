"""
Advanced INKA - Продвинутый AI-ассистент с доступом к реальным данным
- Работа с Google Sheets в реальном времени
- Интеграция с Google Calendar
- Unified Data Sync Service для синхронизации всех данных
- Поиск в интернете
- Максимально человечное общение
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from openai import OpenAI

logger = logging.getLogger(__name__)


class AdvancedINKA:
    """Продвинутая версия INKA с доступом к реальным данным"""
    
    def __init__(self, api_key: str, assistant_id: str, sheets_client=None, calendar_service=None, data_sync=None, admin_ids: List[int] = None):
        """
        Args:
            api_key: OpenAI API ключ
            assistant_id: ID OpenAI Assistant
            sheets_client: Клиент для работы с Google Sheets
            calendar_service: Сервис для работы с Google Calendar
            data_sync: DataSyncService для синхронизации всех данных
            admin_ids: Список ID администраторов для доступа к админ-функциям
        """
        logger.info(f"🔴 AdvancedINKA.__init__ START")
        try:
            logger.info(f"🟡 Creating OpenAI client...")
            self.client = OpenAI(api_key=api_key)
            logger.info(f"🟡 Setting assistant_id...")
            self.assistant_id = assistant_id
            self.sheets_client = sheets_client
            self.calendar_service = calendar_service
            self.admin_ids = admin_ids if admin_ids else []
            logger.info(f"🟡 Admin IDs configured: {self.admin_ids}")
            
            logger.info(f"🟡 Initializing caches...")
            # Unified data sync service (lazy initialization)
            self._data_sync = data_sync
            self._data_sync_initialized = data_sync is not None
            
            # Кэши для ускорения
            self._schedule_cache = None
            self._schedule_cache_time = 0
            self._masters_cache = None
            self._masters_cache_time = 0
            self._services_cache = None
            self._services_cache_time = 0
            
            # Текущий user_id для проверки прав в функциях
            self._current_user_id = None
            
            # Системный промпт для профессионального администратора
            self.system_prompt = """Ты — ИНКА, профессиональный администратор тату-салона Ани.
Ты ЖИВОЙ ЧЕЛОВЕК за стойкой, который общается через мессенджер.

═══════════════════════════════════════════════════
🎯 ТВОЯ ГЛАВНАЯ ЗАДАЧА
═══════════════════════════════════════════════════
Вести клиента по воронке продаж от первого сообщения до записи.
Ты работаешь с ХОЛОДНЫМ трафиком из рекламы - люди пришли по кнопке "Хочу тату".

═══════════════════════════════════════════════════
👥 ТИПЫ КЛИЕНТОВ (определяй автоматически)
═══════════════════════════════════════════════════

🔥 ГОРЯЧИЙ (готов записаться прямо сейчас):
   Признаки: "хочу записаться", "когда можно", "сколько стоит [конкретика]"
   Действия: Быстро уточни детали → Предложи 2-3 слота → Запиши
   
🌡️ ТЁПЛЫЙ (интересуется, но сомневается):
   Признаки: "а как это", "больно ли", "сколько заживает", "покажите работы"
   Действия: Ответь кратко → Развей сомнения → Мягко предложи консультацию
   
❄️ ХОЛОДНЫЙ (просто смотрит):
   Признаки: "привет", "что у вас есть", "сколько вообще стоит"
   Действия: Общайся легко → Заинтересовывай → НЕ дави на запись

═══════════════════════════════════════════════════
🎨 ТИПЫ РАБОТ И МАРШРУТИЗАЦИЯ
═══════════════════════════════════════════════════

✅ СРАЗУ НА ЗАПИСЬ (простые случаи):
• Надпись/текст до 10 слов
• Маленькая тату до 5см (символ, иконка, минималистика)
• Точное повторение готового эскиза
→ Действие: Уточни размер → Предложи слоты → Запиши

🤝 НА КОНСУЛЬТАЦИЮ (сложные случаи):
• Большая работа (от 10см)
• Нужен индивидуальный эскиз
• Сложная идея, много деталей
• Клиент не определился с дизайном
• Кавер (перекрытие старой тату)
→ Действие: Объясни зачем нужна конса → Предложи бесплатную встречу

🔧 ПИРСИНГ:
• Любая зона: нос, ухо, пупок и т.д.
→ Действие: Уточни зону → Расскажи про уход → Запиши на слот 30 мин

═══════════════════════════════════════════════════
👥 НАША КОМАНДА (РЕАЛЬНЫЕ МАСТЕРА)
═══════════════════════════════════════════════════

🎨 АННА ЛЕВИ (@m_anna_levi) - Татуировка
   ⭐ Рейтинг: 4.8/5
   🎯 Специализация: РЕАЛИСТИЧНЫЕ ТАТУИРОВКИ
   📞 Опыт: 8 лет, сертифицирована
   💰 Цена: от ₪250 (с премиумом за реалистику)
   ⏰ График: Пн-Пт 10:00-19:00, Сб 12:00-17:00
   💡 Лучше всего: Портреты, животные, детальные рисунки

🎨 ПЛАТОН СОСНИЦКИЙ (@m_platon_sosnitsky) - Татуировка
   ⭐ Рейтинг: 4.9/5
   🎯 Специализация: МИНИМАЛИЗМ И АВТОРСКИЕ ДИЗАЙНЫ
   📞 Опыт: 12 лет, творческий подход
   💰 Цена: от ₪250 (премиум за сложные дизайны)
   ⏰ График: Пн-Пт 10:00-19:00
   💡 Лучше всего: Линии, геометрия, оригинальные идеи

🔧 МОЙШЕ (@m_sarah_moshe) - Пирсинг
   ⭐ Рейтинг: 4.7/5
   🎯 Специализация: ПИРСИНГ (сертифицирована APP)
   📞 Опыт: сертифицированный мастер
   💰 Цена: ухо ₪90-150, нос ₪120-180, тело ₪150-250
   ⏰ График: Пн-Пт 10:00-18:00, Сб 10:00-14:00
   💡 Лучше всего: Микропирсинг, хрящ, сложные зоны

═══════════════════════════════════════════════════
🔍 КАК НАЙТИ НУЖНОГО МАСТЕРА
═══════════════════════════════════════════════════

Клиент спрашивает про СТИЛЬ ТАТУИРОВКИ (реализм, минимализм, etc):
→ Ищи по ключевому слову в описании мастера:
   • "реализм" / "реалистичные" → АННА ЛЕВИ
   • "минимализм" / "линии" / "геометрия" → ПЛАТОН СОСНИЦКИЙ
   • "пирсинг" → МОЙШЕ

Вызывай: get_database_info(table='masters', filter_field='specialization', filter_value='реализм')
Система автоматически поищет это ключевое слово в поле bio каждого мастера!

═══════════════════════════════════════════════════

═══════════════════════════════════════════════════
💰 ПРАЙС-ЛИСТ 2025 (Израиль)
═══════════════════════════════════════════════════

🎨 ТАТУИРОВКИ:
   📌 Маленькая (до 5см): ₪250-500
      Пример: надпись, символ, простой дизайн
   
   📌 Средняя (5-15см): ₪600-1500
      Пример: животное, портрет, цветная работа
   
   📌 Большая (15+ см): ₪1800-5000
      Пример: рукав, спина, сложный сюжет
   
   📌 Надпись (до 10 слов): ₪250-400
      Любой шрифт и размер

🔧 ПИРСИНГ:
   📌 Пирсинг уха: ₪90-150 (30 мин)
   📌 Пирсинг носа: ₪120-180 (30 мин)
   📌 Пирсинг тела: ₪150-250 (30 мин)
   ⚕️ Консультация: БЕСПЛАТНО

✨ ПРИМЕРЫ ЦЕН:
   • "Хочу надпись "Семья" на иврите" → ₪250-350
   • "Роза на плече" → ₪400-700
   • "Портрет любимого человека" → ₪1500-2500
   • "Пирсинг уха" → ₪120 (Сара)

═══════════════════════════════════════════════════
💬 СТИЛЬ ОБЩЕНИЯ (КРИТИЧНО!)
═══════════════════════════════════════════════════

ТЫ НЕ РОБОТ! Пиши как живой человек:
• Короткие предложения (5-10 слов)
• Живой разговорный язык
• Эмодзи там где естественно (не перебарщивай)
• Задавай уточняющие вопросы
• Реагируй на эмоции клиента

ПРИМЕРЫ ПРАВИЛЬНОГО ОБЩЕНИЯ:

Клиент: "Привет"
❌ Плохо: "Здравствуйте! Я AI-ассистент салона. Чем могу помочь?"
✅ ХОРОШО: "Привет! 😊 Думаешь над татуировкой?"

Клиент: "Хочу надпись на руке"
❌ Плохо: "Вам необходимо определиться с текстом и шрифтом"
✅ ХОРОШО: "О, надписи люблю! Уже знаешь что за текст будет?"

Клиент: "Больно?"
❌ Плохо: "Уровень болевых ощущений зависит от зоны"
✅ ХОРОШО: "Терпимо 😊 Как пощипывание. Где думаешь делать?"

Клиент: "Сколько стоит?"
❌ Плохо: "Цена зависит от размера и сложности работы"
✅ ХОРОШО: "Что именно хочешь? Расскажи про идею"

═══════════════════════════════════════════════════
🎯 ВОРОНКА ПРОДАЖ (веди по этапам)
═══════════════════════════════════════════════════

ЭТАП 1: КОНТАКТ
• Клиент написал первое сообщение
• Задача: Поздороваться живо, создать комфорт
• "Привет! 😊" / "О, классно что написал!"

ЭТАП 2: ВЫЯВЛЕНИЕ ПОТРЕБНОСТИ
• Узнай ЧТО хочет клиент
• Задавай простые вопросы:
  - "Что планируешь сделать?"
  - "Уже есть идея или эскиз?"
  - "Какой размер примерно?"

ЭТАП 3: КВАЛИФИКАЦИЯ (определи тип)
• Простая работа → на запись
• Сложная работа → на консу
• Не определился → помоги с выбором

ЭТАП 4: РАБОТА С ВОЗРАЖЕНИЯМИ
• "Дорого" → "Да, качество стоит. Зато на всю жизнь 😊"
• "Больно" → "Терпимо, все справляются. Можем на менее болючем месте"
• "Думаю" → "Окей! Напиши когда решишь. Эскизы могу показать"

ЭТАП 5: ЗАКРЫТИЕ (запись или конса)
• Предложи конкретные даты (2-3 варианта)
• "Когда тебе удобнее - завтра в 14:00 или в пятницу в 11:00?"
• Подтверди и сохрани

═══════════════════════════════════════════════════
⚡ СКОРОСТЬ РАБОТЫ
═══════════════════════════════════════════════════

ОТВЕЧАЙ БЫСТРО:
• НЕ лезь в БД пока не нужно
• Сначала поговори, потом ищи информацию
• Typing indicator показывается автоматически

КОГДА ИСПОЛЬЗОВАТЬ ФУНКЦИИ:
1. get_database_info - вызывай ТОЛЬКО ЕСЛИ клиент явно спросил про:
   • Конкретного мастера ПО ИМЕНИ (даже если имя на другом языке)
   • Цены на услуги
   • Информацию о мастерах
   ❌ НЕ вызывай просто для общей информации или при приветствии
   
2. get_calendar_slots - вызывай ТОЛЬКО когда:
   • Клиент сказал "запиши", "когда можно", "какие времена", "есть ли свободные дни"
   • Явно просит выбрать дату/время
   • После обсуждения дня/времени
   ⚠️ ЕСЛИ В БД НЕТ РАСПИСАНИЯ - просто скажи что нужно согласовать время лично
   ❌ НЕ вызывай при простом общении, приветствии или обсуждении услуги
   
3. create_booking - используй КРИТИЧЕСКИ ВАЖНО когда:
   • Клиент подтвердил дату, время и согласился на запись
   • Все детали уточнены (мастер, услуга, время)
   • Клиент дал явное "да", "записывай", "подтверждаю"
   ❌ НЕ вызывай без явного подтверждения!
   
4. create_client - автоматически создаётся в create_booking

═══════════════════════════════════════════════════
🚫 ЧТО ЗАПРЕЩЕНО (КРИТИЧНО!)
═══════════════════════════════════════════════════

• Писать "Я AI/бот/ассистент" - ты ЖИВОЙ администратор
• Использовать шаблонные фразы
• Отвечать формально и сухо
• Давить на клиента
• Проверять БД при каждом сообщении
• Долго молчать (если думаешь - пиши "секунду...")
• **НИКОГДА не использовать кнопки, [кнопки], /кнопки или типа того**
• **НИКОГДА не использовать markdown кнопки или ссылки формата [text](url)**
• **Писать ТОЛЬКО чистый текст без форматирования кнопок**
• Использовать числовые меню (1) 2) 3)) - только естественный текст
• Не использовать команды типа /start /help /booking - пиши текстом
• Если нужно предложить выбор - пиши: "Могу предложить: вариант А, вариант Б, вариант В. Какой подходит?"

═══════════════════════════════════════════════════
📝 ФОРМАТ ОТВЕТОВ
═══════════════════════════════════════════════════

✅ ПРАВИЛЬНО (только текст):
"У нас есть слоты на завтра в 14:00 и в пятницу в 11:00. Какой время подходит?"

❌ НЕПРАВИЛЬНО (с кнопками/форматированием):
"Выберите время:
[14:00 завтра]
[11:00 пятницу]"

или

"Время:
1) 14:00 завтра
2) 11:00 пятницу"

ВСЕГДА ТОЛЬКО ЖИВОЙ ТЕКСТ БЕЗ ФОРМАТИРОВАНИЯ!

═══════════════════════════════════════════════════
✨ ТВОЙ ХАРАКТЕР
═══════════════════════════════════════════════════

• Дружелюбная и открытая
• Слегка ироничная (уместно)
• Позитивная, но не навязчивая
• Профессионал который любит свою работу
• Помнишь всё что обсуждали
• Умеешь шутить и поддержать беседу
• Искренне помогаешь, а не впариваешь

ПОМНИ: Ты настоящий человек за стойкой тату-салона! 🎨
"""
        except Exception as e:
            logger.error(f"❌ AdvancedINKA.__init__ ERROR: {e}", exc_info=True)
            raise
    
    def create_tools_config(self, is_admin: bool = False) -> List[Dict]:
        """Создаёт конфигурацию инструментов (функций) для Assistant
        
        Args:
            is_admin: True если текущий пользователь - администратор
        """
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_database_info",
                    "description": "Получить информацию из базы данных (клиенты, записи, мастера, услуги)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {
                                "type": "string",
                                "enum": ["clients", "masters", "bookings", "services", "price_list", "reviews", "schedule"],
                                "description": "Table name to query"
                            },
                            "filter_field": {
                                "type": "string",
                                "description": "Поле для фильтрации (например, 'user_id', 'name', 'phone')"
                            },
                            "filter_value": {
                                "type": "string",
                                "description": "Значение для фильтрации"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Максимальное количество записей (по умолчанию 10)",
                                "default": 10
                            }
                        },
                        "required": ["table"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_calendar_slots",
                    "description": "Получить доступные слоты в календаре мастера",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "master_id": {
                                "type": "string",
                                "description": "ID мастера (опционально, если не указан - все мастера)"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Начальная дата в формате YYYY-MM-DD"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "Конечная дата в формате YYYY-MM-DD"
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "description": "Требуемая продолжительность в минутах",
                                "default": 60
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Искать актуальную информацию в интернете (цены, советы по уходу, тренды и т.д.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Поисковый запрос"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Максимальное количество результатов",
                                "default": 3
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_booking",
                    "description": "Создать новую запись для клиента",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Telegram ID пользователя"
                            },
                            "master_id": {
                                "type": "string",
                                "description": "ID мастера"
                            },
                            "date": {
                                "type": "string",
                                "description": "Дата в формате YYYY-MM-DD"
                            },
                            "time": {
                                "type": "string",
                                "description": "Время в формате HH:MM"
                            },
                            "service": {
                                "type": "string",
                                "description": "Название услуги"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Дополнительные заметки"
                            }
                        },
                        "required": ["user_id", "master_id", "date", "time", "service"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_client",
                    "description": "Создать или обновить профиль клиента",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "telegram_id": {
                                "type": "string",
                                "description": "Telegram ID пользователя"
                            },
                            "name": {
                                "type": "string",
                                "description": "Имя клиента"
                            },
                            "phone": {
                                "type": "string",
                                "description": "Номер телефона"
                            },
                            "email": {
                                "type": "string",
                                "description": "Email (опционально)"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Заметки о клиенте"
                            }
                        },
                        "required": ["telegram_id", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "format_table",
                    "description": "Форматировать данные в красивую таблицу с нужными колонками в нужном порядке",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "array",
                                "description": "Массив объектов (строк таблицы)",
                                "items": {"type": "object"}
                            },
                            "columns": {
                                "type": "array",
                                "description": "Список колонок для отображения в нужном порядке",
                                "items": {"type": "string"}
                            },
                            "column_titles": {
                                "type": "object",
                                "description": "Красивые названия для колонок (ключ -> название)",
                                "additionalProperties": {"type": "string"}
                            },
                            "max_width": {
                                "type": "integer",
                                "description": "Максимальная ширина каждой колонки (по умолчанию 20)",
                                "default": 20
                            }
                        },
                        "required": ["data", "columns"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_formatted_response",
                    "description": "Создать красиво отформатированный ответ с таблицей, описанием и рекомендациями",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Заголовок ответа"
                            },
                            "description": {
                                "type": "string",
                                "description": "Описание перед таблицей"
                            },
                            "table_data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "description": "Строка данных таблицы"
                                },
                                "description": "Данные для таблицы"
                            },
                            "columns": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "description": "Название колонки"
                                },
                                "description": "Колонки для отображения"
                            },
                            "footer": {
                                "type": "string",
                                "description": "Текст после таблицы (рекомендации, следующие шаги)"
                            }
                        },
                        "required": ["title"]
                    }
                }
            }
        ]
        
        # ============================================================
        # 👑 АДМИН-ФУНКЦИИ (ТОЛЬКО ДЛЯ АДМИНИСТРАТОРОВ)
        # ============================================================
        if is_admin:
            admin_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "edit_master",
                        "description": "👑 [АДМИН] Редактировать информацию о мастере (имя, специализация, цены)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "master_id": {
                                    "type": "string",
                                    "description": "ID мастера"
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Новое имя мастера"
                                },
                                "phone": {
                                    "type": "string",
                                    "description": "Телефон мастера"
                                },
                                "specialty": {
                                    "type": "string",
                                    "description": "Специализация (например: 'Реалистичные портреты', 'Минимализм')"
                                },
                                "rate_per_hour": {
                                    "type": "number",
                                    "description": "Ставка в час (в рублях)"
                                }
                            },
                            "required": ["master_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "edit_service",
                        "description": "👑 [АДМИН] Редактировать услугу (название, описание, цена, время)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "service_id": {
                                    "type": "string",
                                    "description": "ID услуги"
                                },
                                "name": {
                                    "type": "string",
                                    "description": "Название услуги"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Описание услуги"
                                },
                                "price": {
                                    "type": "number",
                                    "description": "Цена услуги (в рублях)"
                                },
                                "duration_minutes": {
                                    "type": "integer",
                                    "description": "Продолжительность услуги в минутах"
                                }
                            },
                            "required": ["service_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "add_schedule_slot",
                        "description": "👑 [АДМИН] Добавить временной слот в расписание мастера",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "master_id": {
                                    "type": "string",
                                    "description": "ID мастера"
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Дата в формате YYYY-MM-DD"
                                },
                                "start_time": {
                                    "type": "string",
                                    "description": "Время начала в формате HH:MM"
                                },
                                "end_time": {
                                    "type": "string",
                                    "description": "Время окончания в формате HH:MM"
                                },
                                "notes": {
                                    "type": "string",
                                    "description": "Примечания (например: выходной, отпуск, техническое обслуживание)"
                                }
                            },
                            "required": ["master_id", "date", "start_time", "end_time"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "cancel_booking",
                        "description": "👑 [АДМИН] Отменить запись клиента",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "booking_id": {
                                    "type": "string",
                                    "description": "ID записи"
                                },
                                "reason": {
                                    "type": "string",
                                    "description": "Причина отмены"
                                },
                                "notify_client": {
                                    "type": "boolean",
                                    "description": "Отправить ли уведомление клиенту",
                                    "default": True
                                }
                            },
                            "required": ["booking_id"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "export_statistics",
                        "description": "👑 [АДМИН] Экспортировать статистику (доход, загруженность, популярные услуги)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "date_from": {
                                    "type": "string",
                                    "description": "Дата начала в формате YYYY-MM-DD"
                                },
                                "date_to": {
                                    "type": "string",
                                    "description": "Дата конца в формате YYYY-MM-DD"
                                },
                                "stat_type": {
                                    "type": "string",
                                    "enum": ["revenue", "bookings", "masters", "services", "clients"],
                                    "description": "Тип статистики"
                                }
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "send_broadcast_message",
                        "description": "👑 [АДМИН] Отправить рассылку всем клиентам (только админы!)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "message": {
                                    "type": "string",
                                    "description": "Текст сообщения для рассылки"
                                },
                                "target_group": {
                                    "type": "string",
                                    "enum": ["all_clients", "recent_clients", "vip_clients"],
                                    "description": "Группа для рассылки"
                                }
                            },
                            "required": ["message"]
                        }
                    }
                }
            ]
            tools.extend(admin_tools)
            logger.info(f"✅ Added {len(admin_tools)} admin tools for administrator")
        
        return tools
    
    def get_database_info(self, table: str, filter_field: Optional[str] = None, 
                         filter_value: Optional[str] = None, limit: int = 10) -> Dict:
        """Получить информацию из базы данных с кэшированием расписания"""
        try:
            if not self.sheets_client:
                return {"error": "Database connection not available"}
            
            # Используем кэш для часто используемых таблиц (обновляется каждый час)
            current_time = time.time()
            cache_ttl = 3600  # 1 час
            
            if table == "schedule":
                if self._schedule_cache is not None and (current_time - self._schedule_cache_time) < cache_ttl:
                    logger.info("📅 Using cached schedule data")
                    return self._schedule_cache
            elif table == "masters":
                if self._masters_cache is not None and (current_time - self._masters_cache_time) < cache_ttl:
                    logger.info("👨‍💼 Using cached masters data")
                    return self._masters_cache
            elif table == "services":
                if self._services_cache is not None and (current_time - self._services_cache_time) < cache_ttl:
                    logger.info("💼 Using cached services data")
                    return self._services_cache
            
            # Получаем все данные из таблицы
            data = self.sheets_client.get_all_rows(table)
            
            if not data or len(data) < 2:
                return {"data": [], "count": 0, "message": f"Таблица {table} пуста"}
            
            headers = data[0]
            rows = data[1:]
            
            # Фильтрация если указана
            if filter_field and filter_value:
                try:
                    field_index = headers.index(filter_field)
                    filter_value_lower = str(filter_value).strip().lower()
                    
                    filtered_rows = []
                    for row in rows:
                        if len(row) > field_index:
                            row_value = str(row[field_index]).strip().lower()
                            # Точное совпадение
                            if row_value == filter_value_lower:
                                filtered_rows.append(row)
                            # Или поиск по ключевому слову (для мастеров ищем в bio)
                            elif table == "masters" and field_index == headers.index("specialization"):
                                # Поиск ключевого слова в поле bio (стиль татуировки)
                                bio_index = headers.index("bio") if "bio" in headers else -1
                                if bio_index >= 0 and len(row) > bio_index:
                                    bio_text = str(row[bio_index]).lower()
                                    if filter_value_lower in bio_text:
                                        filtered_rows.append(row)
                    
                    rows = filtered_rows
                except ValueError:
                    return {"error": f"Field {filter_field} not found in table {table}"}
            
            # Ограничение количества
            rows = rows[:limit]
            
            # Преобразуем в словари
            result = []
            for row in rows:
                row_dict = {}
                for i, header in enumerate(headers):
                    row_dict[header] = row[i] if i < len(row) else ""
                result.append(row_dict)
            
            response = {
                "data": result,
                "count": len(result),
                "table": table,
                "headers": headers
            }
            
            # Кэшируем часто используемые таблицы (1 час TTL)
            if table == "schedule":
                self._schedule_cache = response
                self._schedule_cache_time = time.time()
            elif table == "masters":
                self._masters_cache = response
                self._masters_cache_time = time.time()
            elif table == "services":
                self._services_cache = response
                self._services_cache_time = time.time()
            
            return response
        
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return {"error": str(e)}
    
    def get_calendar_slots(self, start_date: str, end_date: str, 
                          master_id: Optional[str] = None, 
                          duration_minutes: int = 60) -> Dict:
        """Получить доступные слоты из Google Calendar и системы записей"""
        try:
            # Парсим даты
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Получаем calendar_id мастера если указан
            master_calendar_id = None
            if master_id:
                masters_data = self.get_database_info("masters")
                masters = masters_data.get("data", [])
                master = next((m for m in masters if m.get("id") == master_id), None)
                if master:
                    master_calendar_id = master.get("calendar_id")
                    logger.info(f"📅 Using master calendar: {master_calendar_id}")
            
            # Получаем события из Google Calendar мастера
            calendar_events = []
            if self.calendar_service and master_calendar_id:
                try:
                    events_result = self.calendar_service.events().list(
                        calendarId=master_calendar_id,  # Используем календарь мастера
                        timeMin=f"{start_date}T00:00:00Z",
                        timeMax=f"{end_date}T23:59:59Z",
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    calendar_events = events_result.get('items', [])
                    logger.info(f"📅 Retrieved {len(calendar_events)} events from master's Google Calendar")
                except Exception as e:
                    logger.warning(f"Failed to fetch master calendar events: {e}")
                    calendar_events = []
            
            # Получаем записи из таблицы Bookings
            bookings_data = self.get_database_info("bookings")
            bookings = bookings_data.get("data", [])
            # Фильтруем записи по мастеру и датам
            master_bookings = []
            for b in bookings:
                if b.get("status") in ["cancelled"]:
                    continue
                if master_id and b.get("master_id") != master_id:
                    continue
                booking_date = b.get("date", "")
                if booking_date >= start_date and booking_date <= end_date:
                    master_bookings.append(b)
            logger.info(f"📅 Found {len(master_bookings)} bookings for master in date range")
            
            # Получаем расписание мастера из Sheets (для определения рабочих часов)
            schedule_data = self.get_database_info("schedule")
            schedule_rows = schedule_data.get("data", [])
            
            # Если нет расписания - генерируем стандартное расписание (10:00-18:00)
            if not schedule_rows:
                logger.warning("No schedule found in database, using default working hours")
                schedule_rows = [
                    {"master_id": "default", "day_of_week": "monday", "start_time": "10:00", "end_time": "18:00", "is_working": "true"},
                    {"master_id": "default", "day_of_week": "tuesday", "start_time": "10:00", "end_time": "18:00", "is_working": "true"},
                    {"master_id": "default", "day_of_week": "wednesday", "start_time": "10:00", "end_time": "18:00", "is_working": "true"},
                    {"master_id": "default", "day_of_week": "thursday", "start_time": "10:00", "end_time": "18:00", "is_working": "true"},
                    {"master_id": "default", "day_of_week": "friday", "start_time": "10:00", "end_time": "18:00", "is_working": "true"},
                    {"master_id": "default", "day_of_week": "saturday", "start_time": "10:00", "end_time": "16:00", "is_working": "true"},
                ]
            
            # Фильтруем расписание по мастеру если указан
            if master_id:
                schedule_rows = [s for s in schedule_rows if s.get("master_id") == master_id]
            
            # Генерируем слоты на основе расписания Sheets
            free_slots = []
            current = start_dt
            
            while current <= end_dt:
                day_of_week = current.strftime("%A").lower()
                
                # Находим расписание для этого дня
                day_schedule = [s for s in schedule_rows if s.get("day_of_week") == day_of_week]
                
                for schedule in day_schedule:
                    if schedule.get("is_working") != "true":
                        continue
                    
                    start_time = schedule.get("start_time", "10:00")
                    end_time = schedule.get("end_time", "18:00")
                    
                    # Генерируем слоты по указанной длительности
                    slot_start_h, slot_start_m = map(int, start_time.split(":"))
                    end_h, end_m = map(int, end_time.split(":"))
                    
                    current_slot = current.replace(hour=slot_start_h, minute=slot_start_m)
                    end_slot_time = current.replace(hour=end_h, minute=end_m)
                    
                    while current_slot + timedelta(minutes=duration_minutes) <= end_slot_time:
                        slot_end = current_slot + timedelta(minutes=duration_minutes)
                        
                        # Проверяем пересечение с событиями в Google Calendar
                        is_booked = False
                        for event in calendar_events:
                            try:
                                event_start = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
                                event_end = event.get('end', {}).get('dateTime') or event.get('end', {}).get('date')
                                
                                if not event_start or not event_end:
                                    continue
                                
                                # Парсим времена событий
                                if 'T' in str(event_start):
                                    event_start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                                else:
                                    event_start_dt = datetime.strptime(event_start, "%Y-%m-%d")
                                
                                if 'T' in str(event_end):
                                    event_end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00'))
                                else:
                                    event_end_dt = datetime.strptime(event_end, "%Y-%m-%d")
                                
                                # Проверяем пересечение времени
                                if (current_slot < event_end_dt and slot_end > event_start_dt):
                                    is_booked = True
                                    logger.debug(f"Slot {current_slot.strftime('%H:%M')} occupied by event: {event.get('summary')}")
                                    break
                            except Exception as e:
                                logger.warning(f"Error parsing calendar event: {e}")
                                continue
                        
                        # Проверяем пересечение с записями из Bookings
                        if not is_booked:
                            slot_date_str = current.strftime("%Y-%m-%d")
                            slot_time_str = current_slot.strftime("%H:%M")
                            for booking in master_bookings:
                                if booking.get("date") == slot_date_str:
                                    booking_time = booking.get("time", "")[:5]  # Берем HH:MM
                                    if booking_time == slot_time_str:
                                        is_booked = True
                                        logger.debug(f"Slot {slot_time_str} on {slot_date_str} occupied by booking")
                                        break
                        
                        if not is_booked:
                            free_slots.append({
                                "date": current.strftime("%Y-%m-%d"),
                                "time": current_slot.strftime("%H:%M"),
                                "end_time": slot_end.strftime("%H:%M"),
                                "master_id": schedule.get("master_id") or master_id,
                                "duration_minutes": duration_minutes
                            })
                        
                        current_slot += timedelta(minutes=60)
                
                current += timedelta(days=1)
            
            return {
                "slots": free_slots[:20],  # Ограничиваем 20 слотами
                "count": len(free_slots),
                "total_available": len(free_slots),
                "master_id": master_id,
                "duration_minutes": duration_minutes,
                "source": "Google Calendar + Bookings + Schedule"
            }
        
        except Exception as e:
            logger.error(f"Calendar query error: {e}", exc_info=True)
            return {"error": str(e)}
    
    def search_web(self, query: str, max_results: int = 3) -> Dict:
        """Поиск информации в интернете"""
        try:
            # Используем GPT для генерации ответа на основе общих знаний
            # В продакшене можно интегрировать реальный поиск (Google Custom Search API, Bing API и т.д.)
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты эксперт по татуировкам. Предоставь краткую, актуальную информацию."},
                    {"role": "user", "content": f"Вопрос: {query}\n\nДай краткий, информативный ответ (2-3 предложения)."}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            answer = response.choices[0].message.content
            
            return {
                "query": query,
                "answer": answer,
                "source": "AI Knowledge Base",
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {"error": str(e)}
    
    def create_client(self, telegram_id: str, name: str = None, phone: str = "", 
                     email: str = "", notes: str = "") -> Dict:
        """Создать или обновить клиента в БД. Автоматически создаёт если не существует."""
        try:
            if not self.sheets_client:
                logger.error("❌ Database connection not available")
                return {"error": "Database connection not available"}
            
            # Нормализуем telegram_id
            telegram_id_str = str(telegram_id).strip()
            if not telegram_id_str or telegram_id_str == "None":
                logger.error("❌ telegram_id не может быть пустым")
                return {"error": "telegram_id не может быть пустым"}
            
            # Если имя не указано, используем telegram_id как имя
            if not name:
                name = f"User_{telegram_id_str[-6:]}"
            
            logger.info(f"🔍 Checking for existing client: telegram_id={telegram_id_str}")
            
            # Получаем существующих клиентов
            clients_data = self.get_database_info("clients", "telegram_id", telegram_id_str)
            
            # Если клиент уже существует, возвращаем его
            if clients_data.get("data") and len(clients_data["data"]) > 0:
                existing_client = clients_data["data"][0]
                logger.info(f"✅ Client already exists: {existing_client.get('name')}")
                return {
                    "success": True,
                    "message": f"✅ Профиль найден: {existing_client.get('name')}",
                    "client": existing_client,
                    "is_new": False
                }
            
            # Создаём нового клиента
            import uuid
            client_id = str(uuid.uuid4())
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Подготавливаем строку для добавления
            # Колонки: id, telegram_id, name, phone, email, notes, created_at, last_visit
            client_row = [
                client_id,           # id
                telegram_id_str,     # telegram_id
                name,                # name
                phone or "",         # phone
                email or "",         # email
                notes or "",         # notes
                created_at,          # created_at
                ""                   # last_visit
            ]
            
            logger.info(f"📝 Creating new client with row: {client_row}")
            
            # Добавляем в таблицу
            success = self.sheets_client.append_row("clients", client_row)
            
            if success:
                logger.info(f"✅ Client created: {client_id}, name={name}, telegram_id={telegram_id_str}")
                return {
                    "success": True,
                    "message": f"✅ Создан новый профиль: {name}",
                    "client": {
                        "id": client_id,
                        "telegram_id": telegram_id_str,
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "notes": notes
                    },
                    "is_new": True
                }
            else:
                logger.error(f"❌ Failed to create client in database")
                return {"error": "Failed to create client in database"}
        
        except Exception as e:
            logger.error(f"Client creation error: {e}", exc_info=True)
            return {"error": str(e)}
    
    def create_booking(self, user_id: str, master_id: str, date: str, 
                      time: str, service: str, notes: str = "") -> Dict:
        """Создать запись в БД и добавить событие в Google Calendar"""
        try:
            if not self.sheets_client:
                return {"error": "Database connection not available"}
            
            # Сначала получаем или создаём клиента
            clients_data = self.get_database_info("clients", "telegram_id", str(user_id))
            
            if not clients_data.get("data") or len(clients_data["data"]) == 0:
                # Создаём нового клиента с базовой инфой
                client_result = self.create_client(str(user_id), "Client", "", "", notes)
                if client_result.get("error"):
                    return client_result
                client_id = client_result["client"]["id"]
            else:
                client_id = clients_data["data"][0]["id"]
            
            # Получаем информацию о мастере
            masters_data = self.get_database_info("masters", "id", master_id, limit=1)
            if not masters_data.get("data"):
                return {"error": f"Master {master_id} not found"}
            
            master_name = masters_data["data"][0].get("name", f"Master {master_id}")
            
            # Создаём бронирование
            import uuid
            booking_id = str(uuid.uuid4())
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Подготавливаем строку для добавления
            # Колонки: id, client_id, master_id, service_id, date, time, duration_min, price, status, notes, created_at
            booking_row = [
                booking_id,          # id
                client_id,           # client_id
                master_id,           # master_id
                service,             # service_id
                date,                # date
                time,                # time
                "60",                # duration_min
                "",                  # price (оставляем пусто)
                "confirmed",         # status
                notes,               # notes
                created_at           # created_at
            ]
            
            # Добавляем запись в таблицу
            success = self.sheets_client.append_row("bookings", booking_row)
            
            if success:
                logger.info(f"Booking created: {booking_id}, client={client_id}, master={master_id}, date={date}, time={time}")
                
                # Создаём событие в Google Calendar
                calendar_event_created = False
                if self.calendar_service:
                    try:
                        # Парсим дату и время
                        start_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
                        end_dt = start_dt + timedelta(minutes=60)  # 60 минут по умолчанию
                        
                        event = {
                            'summary': f"{service} - {master_name}",
                            'description': f"Booking ID: {booking_id}\nClient: {client_id}\nNotes: {notes}",
                            'start': {
                                'dateTime': start_dt.isoformat(),
                                'timeZone': 'UTC'
                            },
                            'end': {
                                'dateTime': end_dt.isoformat(),
                                'timeZone': 'UTC'
                            }
                        }
                        
                        result = self.calendar_service.events().insert(
                            calendarId='primary',
                            body=event
                        ).execute()
                        
                        logger.info(f"✅ Calendar event created: {result.get('id')}")
                        calendar_event_created = True
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to create calendar event: {e}")
                
                return {
                    "success": True,
                    "message": f"✅ Запись создана!\n📅 {date}\n🕐 {time}\n🎨 {master_name}",
                    "booking_id": booking_id,
                    "calendar_event_created": calendar_event_created,
                    "booking": {
                        "id": booking_id,
                        "client_id": client_id,
                        "master_id": master_id,
                        "date": date,
                        "time": time,
                        "service": service,
                        "status": "confirmed"
                    }
                }
            else:
                return {"error": "Failed to create booking in database"}
        
        except Exception as e:
            logger.error(f"Booking creation error: {e}", exc_info=True)
            return {"error": str(e)}

    def handle_function_call(self, function_name: str, arguments: Dict) -> str:
        """Обработка вызова функции с проверкой прав"""
        logger.info(f"🔴 handle_function_call START: {function_name}, user_id: {self._current_user_id}")
        try:
            # ============================================================
            # 👑 ПРОВЕРКА ПРАВ ДЛЯ АДМИН-ФУНКЦИЙ
            # ============================================================
            admin_functions = [
                "edit_master", "edit_service", "add_schedule_slot", 
                "cancel_booking", "export_statistics", "send_broadcast_message"
            ]
            
            if function_name in admin_functions:
                # Проверяем права администратора
                current_user = int(self._current_user_id) if self._current_user_id else None
                if current_user not in self.admin_ids:
                    error_msg = f"❌ ДОСТУП ЗАПРЕЩЁН! Функция '{function_name}' доступна ТОЛЬКО администраторам. Ваш ID: {current_user}, Админы: {self.admin_ids}"
                    logger.warning(error_msg)
                    return json.dumps({"error": error_msg, "access_denied": True}, ensure_ascii=False)
                logger.info(f"✅ Admin {current_user} has access to {function_name}")
            
            # ============================================================
            # ОБРАБОТКА ФУНКЦИЙ
            # ============================================================
            if function_name in ["save_client", "create_client"]:
                logger.info(f"🟡 Calling create_client with args: {arguments}")
                result = self.create_client(**arguments)
                logger.info(f"🟢 create_client returned: {result}")
            elif function_name == "get_database_info":
                result = self.get_database_info(**arguments)
            elif function_name == "get_calendar_slots":
                result = self.get_calendar_slots(**arguments)
            elif function_name == "search_web":
                result = self.search_web(**arguments)
            elif function_name == "create_booking":
                result = self.create_booking(**arguments)
            elif function_name == "format_table":
                result = self.format_table(**arguments)
            elif function_name == "create_formatted_response":
                result = self.create_formatted_response(**arguments)
            
            # ============================================================
            # 👑 АДМИН-ФУНКЦИИ
            # ============================================================
            elif function_name == "edit_master":
                result = self._edit_master(**arguments)
            elif function_name == "edit_service":
                result = self._edit_service(**arguments)
            elif function_name == "add_schedule_slot":
                result = self._add_schedule_slot(**arguments)
            elif function_name == "cancel_booking":
                result = self._cancel_booking(**arguments)
            elif function_name == "export_statistics":
                result = self._export_statistics(**arguments)
            elif function_name == "send_broadcast_message":
                result = self._send_broadcast_message(**arguments)
            
            else:
                result = {"error": f"Unknown function: {function_name}"}
            
            logger.info(f"✅ Function {function_name} result: {json.dumps(result, ensure_ascii=False)[:200]}")
            return json.dumps(result, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Function call error: {e}", exc_info=True)
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    async def chat(self, user_message: str, user_id: str, conversation_history: List[Dict] = None) -> str:
        """
        Главный метод для общения с пользователем
        
        Args:
            user_message: Сообщение пользователя
            user_id: ID пользователя
            conversation_history: История разговора
        
        Returns:
            Ответ ассистента
        """
        try:
            # Сохраняем текущего пользователя для проверки прав в handle_function_call
            self._current_user_id = user_id
            
            # Определяем, является ли пользователь администратором
            is_admin = int(user_id) in self.admin_ids if user_id else False
            logger.info(f"👤 User {user_id} - Admin: {is_admin}")
            
            # Создаём thread для разговора
            thread = self.client.beta.threads.create()
            
            # Добавляем историю
            if conversation_history:
                for msg in conversation_history[-10:]:
                    self.client.beta.threads.messages.create(
                        thread_id=thread.id,
                        role=msg.get("role", "user"),
                        content=msg.get("content", "")
                    )
            
            # Добавляем текущее сообщение
            # Не запрашиваем БД при каждом сообщении - Assistant сам вызовет функцию когда нужно
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"[User ID: {user_id}]\n{user_message}"
            )
            
            # Запускаем Assistant с инструментами
            # Передаём tools в run для использования функций
            tools_config = self.create_tools_config(is_admin=is_admin)
            logger.info(f"📋 Tools configured: {len(tools_config)} tools available (admin={is_admin})")
            for tool in tools_config:
                logger.info(f"   - {tool['function']['name']}")
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id,
                tools=tools_config
            )
            
            logger.info(f"🤖 Run created: {run.id}, status: {run.status}")
            
            # Ждём завершения с обработкой вызовов функций
            max_iterations = 10
            iteration = 0
            
            while run.status in ["queued", "in_progress", "requires_action"] and iteration < max_iterations:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                logger.info(f"📍 Run status: {run.status} (iteration {iteration})")

                
                # Обработка вызовов функций
                if run.status == "requires_action":
                    tool_outputs = []
                    
                    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        logger.info(f"Function call: {function_name} with args: {function_args}")
                        
                        # Выполняем функцию
                        output = self.handle_function_call(function_name, function_args)
                        
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": output
                        })
                    
                    # Отправляем результаты функций
                    run = self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                
                iteration += 1
            
            if run.status == "completed":
                # Получаем ответ
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                response = messages.data[0].content[0].text.value
                return response
            else:
                logger.error(f"Run failed with status: {run.status}")
                return "Извини, у меня возникли технические трудности. Попробуй чуть позже? 🙏"
        
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return "Ой, что-то пошло не так! Давай попробуем снова? 😊"
    
    # ============================================================================
    # Методы работы с единой синхронизированной системой данных
    # ============================================================================
    
    @property
    def data_sync(self):
        """Lazy initialization of data sync service"""
        if not self._data_sync_initialized:
            try:
                from src.services.data_sync import get_data_sync_service
                self._data_sync = get_data_sync_service(self.sheets_client, self.calendar_service)
                self._data_sync_initialized = True
                logger.info("✅ Data sync service initialized")
            except Exception as e:
                logger.warning(f"⚠️ Data sync service unavailable: {e}")
                self._data_sync = None
                self._data_sync_initialized = True
        return self._data_sync
    
    def get_masters_unified(self) -> List[Dict[str, Any]]:
        """Получить мастеров из единой системы синхронизации"""
        if self.data_sync:
            return self.data_sync.get_masters()
        elif self.sheets_client:
            return self.get_database_info("masters").get("data", [])
        return []
    
    def get_services_unified(self) -> List[Dict[str, Any]]:
        """Получить услуги из единой системы синхронизации"""
        if self.data_sync:
            return self.data_sync.get_services()
        elif self.sheets_client:
            return self.get_database_info("services").get("data", [])
        return []
    
    def search_masters_unified(self, keyword: str) -> List[Dict[str, Any]]:
        """Поиск мастеров по ключевому слову (реализм, минимализм и т.д.)"""
        if self.data_sync:
            return self.data_sync.search_masters(keyword)
        else:
            return self.get_database_info("masters", "specialization", keyword).get("data", [])
    
    def get_available_slots_unified(self, master_id: str, 
                                   date: str, 
                                   duration_minutes: int = 60) -> List[Dict]:
        """
        Получить доступные слоты через единую систему
        Комбинирует Sheets + Calendar данные
        """
        if self.data_sync:
            return self.data_sync.get_available_slots(
                master_id, date, duration_minutes
            )
        else:
            return self.get_calendar_slots(date, date, master_id, duration_minutes).get("slots", [])
    
    def sync_all_data(self) -> Dict:
        """Выполнить полную синхронизацию всех данных"""
        if not self.data_sync:
            logger.warning("⚠️ Data sync service not available")
            return {"error": "Sync service unavailable"}
        
        logger.info("🔄 Syncing all data...")
        stats = self.data_sync.sync_all()
        
        return {
            "status": "success" if not stats.errors else "partial",
            "tables_synced": stats.tables_synced,
            "masters": stats.masters_cached,
            "services": stats.services_cached,
            "events": stats.events_synced,
            "errors": stats.errors
        }

    def format_table(self, data: List[Dict], columns: List[str], 
                    column_titles: Optional[Dict] = None, max_width: int = 20) -> Dict:
        """Форматировать данные в красивую таблицу"""
        try:
            if not data:
                return {"error": "Нет данных для таблицы", "formatted": ""}
            
            if not columns:
                columns = list(data[0].keys())
            
            if column_titles is None:
                column_titles = {col: col.replace('_', ' ').title() for col in columns}
            
            # Создаём заголовки
            headers = [column_titles.get(col, col) for col in columns]
            
            # Определяем ширину колонок
            col_widths = {}
            for col in columns:
                col_width = max(
                    len(column_titles.get(col, col)),
                    max((len(str(row.get(col, ''))) for row in data), default=0)
                )
                col_widths[col] = min(col_width, max_width)
            
            # Строим таблицу
            lines = []
            
            # Линия сверху
            top_line = "┌" + "┬".join("─" * (col_widths[col] + 2) for col in columns) + "┐"
            lines.append(top_line)
            
            # Заголовки
            header_line = "│" + "│".join(
                f" {headers[i]:<{col_widths[columns[i]]}} "
                for i in range(len(columns))
            ) + "│"
            lines.append(header_line)
            
            # Линия под заголовками
            separator_line = "├" + "┼".join("─" * (col_widths[col] + 2) for col in columns) + "┤"
            lines.append(separator_line)
            
            # Строки данных
            for row in data:
                row_line = "│" + "│".join(
                    f" {str(row.get(col, '')):<{col_widths[col]}} "
                    for col in columns
                ) + "│"
                lines.append(row_line)
            
            # Линия снизу
            bottom_line = "└" + "┴".join("─" * (col_widths[col] + 2) for col in columns) + "┘"
            lines.append(bottom_line)
            
            formatted_table = "\n".join(lines)
            
            return {
                "success": True,
                "formatted": formatted_table,
                "rows_count": len(data),
                "columns_count": len(columns)
            }
        
        except Exception as e:
            logger.error(f"Table formatting error: {e}")
            return {"error": str(e)}

    def create_formatted_response(self, title: str, description: str = "", 
                                 table_data: List[Dict] = None, columns: List[str] = None,
                                 footer: str = "") -> Dict:
        """Создать красиво отформатированный ответ с таблицей"""
        try:
            response_parts = [f"{'='*50}\n{title}\n{'='*50}"]
            
            if description:
                response_parts.append(f"\n{description}")
            
            if table_data and columns:
                table_result = self.format_table(table_data, columns)
                if table_result.get("formatted"):
                    response_parts.append(f"\n{table_result['formatted']}")
            
            if footer:
                response_parts.append(f"\n{footer}")
            
            formatted_response = "\n".join(response_parts)
            
            return {
                "success": True,
                "formatted": formatted_response,
                "title": title
            }
        
        except Exception as e:
            logger.error(f"Response formatting error: {e}")
            return {"error": str(e)}

    # ============================================================================
    # 👑 АДМИН-ФУНКЦИИ (ТОЛЬКО ДЛЯ АДМИНИСТРАТОРОВ)
    # ============================================================================
    
    def _edit_master(self, master_id: str, **kwargs) -> Dict:
        """👑 Редактировать информацию о мастере"""
        try:
            logger.info(f"👑 Admin editing master {master_id}: {kwargs}")
            
            if not self.sheets_client:
                return {"error": "Database not available"}
            
            # Получаем текущие данные мастера
            current_data = self.sheets_client.get_data("Masters")
            master = next((m for m in current_data if m.get("ID") == master_id), None)
            
            if not master:
                return {"error": f"Master {master_id} not found"}
            
            # Обновляем поля
            update_data = {}
            if "name" in kwargs:
                master["Имя"] = kwargs["name"]
                update_data["Имя"] = kwargs["name"]
            if "phone" in kwargs:
                master["Телефон"] = kwargs["phone"]
                update_data["Телефон"] = kwargs["phone"]
            if "specialty" in kwargs:
                master["Специализация"] = kwargs["specialty"]
                update_data["Специализация"] = kwargs["specialty"]
            if "rate_per_hour" in kwargs:
                master["Ставка в час"] = kwargs["rate_per_hour"]
                update_data["Ставка в час"] = kwargs["rate_per_hour"]
            
            # Сохраняем изменения
            self.sheets_client.update_data("Masters", master_id, master)
            
            logger.info(f"✅ Master {master_id} updated: {update_data}")
            return {
                "success": True,
                "message": f"Мастер {master.get('Имя', master_id)} успешно обновлен",
                "updated_fields": update_data
            }
        
        except Exception as e:
            logger.error(f"Error editing master: {e}")
            return {"error": str(e)}
    
    def _edit_service(self, service_id: str, **kwargs) -> Dict:
        """👑 Редактировать услугу"""
        try:
            logger.info(f"👑 Admin editing service {service_id}: {kwargs}")
            
            if not self.sheets_client:
                return {"error": "Database not available"}
            
            # Получаем текущие данные услуги
            current_data = self.sheets_client.get_data("Services")
            service = next((s for s in current_data if s.get("ID") == service_id), None)
            
            if not service:
                return {"error": f"Service {service_id} not found"}
            
            # Обновляем поля
            update_data = {}
            if "name" in kwargs:
                service["Название"] = kwargs["name"]
                update_data["Название"] = kwargs["name"]
            if "description" in kwargs:
                service["Описание"] = kwargs["description"]
                update_data["Описание"] = kwargs["description"]
            if "price" in kwargs:
                service["Цена"] = kwargs["price"]
                update_data["Цена"] = kwargs["price"]
            if "duration_minutes" in kwargs:
                service["Длительность (мин)"] = kwargs["duration_minutes"]
                update_data["Длительность (мин)"] = kwargs["duration_minutes"]
            
            # Сохраняем изменения
            self.sheets_client.update_data("Services", service_id, service)
            
            logger.info(f"✅ Service {service_id} updated: {update_data}")
            return {
                "success": True,
                "message": f"Услуга {service.get('Название', service_id)} успешно обновлена",
                "updated_fields": update_data
            }
        
        except Exception as e:
            logger.error(f"Error editing service: {e}")
            return {"error": str(e)}
    
    def _add_schedule_slot(self, master_id: str, date: str, start_time: str, end_time: str, notes: str = "") -> Dict:
        """👑 Добавить временной слот в расписание мастера"""
        try:
            logger.info(f"👑 Admin adding schedule slot for master {master_id} on {date} {start_time}-{end_time}")
            
            if not self.sheets_client:
                return {"error": "Database not available"}
            
            # Добавляем в Schedule лист
            slot_data = {
                "Мастер ID": master_id,
                "Дата": date,
                "Время начала": start_time,
                "Время окончания": end_time,
                "Примечание": notes,
                "Статус": "Доступно"
            }
            
            self.sheets_client.add_data("Schedule", slot_data)
            
            logger.info(f"✅ Schedule slot added for master {master_id}")
            return {
                "success": True,
                "message": f"Слот добавлен: {date} {start_time}-{end_time}",
                "slot": slot_data
            }
        
        except Exception as e:
            logger.error(f"Error adding schedule slot: {e}")
            return {"error": str(e)}
    
    def _cancel_booking(self, booking_id: str, reason: str = "", notify_client: bool = True) -> Dict:
        """👑 Отменить запись клиента"""
        try:
            logger.info(f"👑 Admin cancelling booking {booking_id}, reason: {reason}")
            
            if not self.sheets_client:
                return {"error": "Database not available"}
            
            # Получаем данные бронирования
            current_data = self.sheets_client.get_data("Bookings")
            booking = next((b for b in current_data if b.get("ID") == booking_id), None)
            
            if not booking:
                return {"error": f"Booking {booking_id} not found"}
            
            # Обновляем статус
            booking["Статус"] = "Отменено"
            booking["Причина отмены"] = reason
            self.sheets_client.update_data("Bookings", booking_id, booking)
            
            # Если нужно отправить уведомление клиенту (в реальном коде здесь была бы отправка в Telegram)
            if notify_client:
                client_id = booking.get("ID Клиента")
                logger.info(f"📧 Would notify client {client_id} about cancelled booking")
            
            logger.info(f"✅ Booking {booking_id} cancelled")
            return {
                "success": True,
                "message": f"Запись {booking_id} отменена",
                "reason": reason,
                "client_notified": notify_client
            }
        
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}")
            return {"error": str(e)}
    
    def _export_statistics(self, date_from: str = None, date_to: str = None, stat_type: str = "revenue") -> Dict:
        """👑 Экспортировать статистику"""
        try:
            logger.info(f"👑 Admin exporting statistics: {stat_type} ({date_from} to {date_to})")
            
            if not self.sheets_client:
                return {"error": "Database not available"}
            
            # Получаем данные бронирований
            bookings = self.sheets_client.get_data("Bookings")
            
            # Фильтруем по датам если указаны
            if date_from and date_to:
                bookings = [b for b in bookings if date_from <= b.get("Дата", "") <= date_to]
            
            stats = {}
            
            if stat_type == "revenue":
                # Считаем общий доход
                total_revenue = sum(float(b.get("Цена", 0)) for b in bookings if b.get("Статус") == "Завершено")
                stats = {
                    "total_revenue": total_revenue,
                    "bookings_count": len([b for b in bookings if b.get("Статус") == "Завершено"]),
                    "period": f"{date_from or 'all'} to {date_to or 'all'}"
                }
            
            elif stat_type == "bookings":
                stats = {
                    "total_bookings": len(bookings),
                    "completed": len([b for b in bookings if b.get("Статус") == "Завершено"]),
                    "cancelled": len([b for b in bookings if b.get("Статус") == "Отменено"]),
                    "scheduled": len([b for b in bookings if b.get("Статус") == "Запланировано"])
                }
            
            elif stat_type == "masters":
                masters = self.sheets_client.get_data("Masters")
                stats = {
                    "total_masters": len(masters),
                    "masters": [{"name": m.get("Имя"), "bookings": len([b for b in bookings if b.get("Мастер ID") == m.get("ID")])} 
                               for m in masters]
                }
            
            elif stat_type == "services":
                services = self.sheets_client.get_data("Services")
                service_stats = {}
                for service in services:
                    service_name = service.get("Название")
                    service_stats[service_name] = len([b for b in bookings if service_name in b.get("Услуга", "")])
                stats = {"services": service_stats}
            
            logger.info(f"✅ Statistics exported: {stat_type}")
            return {
                "success": True,
                "stat_type": stat_type,
                "data": stats
            }
        
        except Exception as e:
            logger.error(f"Error exporting statistics: {e}")
            return {"error": str(e)}
    
    def _send_broadcast_message(self, message: str, target_group: str = "all_clients") -> Dict:
        """👑 Отправить рассылку всем клиентам (только админы!)"""
        try:
            logger.info(f"👑 Admin sending broadcast message to {target_group}")
            
            if not self.sheets_client:
                return {"error": "Database not available"}
            
            # Получаем клиентов
            clients = self.sheets_client.get_data("Clients")
            
            # Фильтруем по группе
            if target_group == "recent_clients":
                # Последние 10 клиентов (по ID)
                clients = sorted(clients, key=lambda x: x.get("ID", ""), reverse=True)[:10]
            elif target_group == "vip_clients":
                # VIP клиенты (у которых 5+ бронирований)
                bookings = self.sheets_client.get_data("Bookings")
                vip_ids = set()
                for booking in bookings:
                    client_id = booking.get("ID Клиента")
                    vip_ids.add(client_id)
                clients = [c for c in clients if c.get("ID") in vip_ids]
            
            # В реальном коде здесь была бы отправка в Telegram
            recipient_count = len(clients)
            logger.info(f"📧 Broadcast would be sent to {recipient_count} clients: {target_group}")
            
            return {
                "success": True,
                "message": f"Рассылка подготовлена для {recipient_count} клиентов",
                "target_group": target_group,
                "recipients_count": recipient_count
            }
        
        except Exception as e:
            logger.error(f"Error sending broadcast: {e}")
            return {"error": str(e)}


def get_advanced_inka(api_key: str, assistant_id: str, 
                     sheets_client=None, calendar_service=None,
                     data_sync=None, admin_ids: List[int] = None) -> AdvancedINKA:
    """Фабрика для создания продвинутого INKA с админ-правами"""
    return AdvancedINKA(api_key, assistant_id, sheets_client, calendar_service, data_sync, admin_ids)
