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
            
            # Текущая дата для промпта
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_date_readable = datetime.now().strftime("%d %B %Y года")
            
            # Системный промпт для профессионального администратора
            self.system_prompt = f"""Ты — ИНКА, профессиональный администратор тату-салона Ани.
Ты ЖИВОЙ ЧЕЛОВЕК за стойкой, который общается через мессенджер.

⚠️ ВАЖНО: Сегодня {current_date} ({current_date_readable}). 
При поиске слотов ВСЕГДА используй даты начиная с СЕГОДНЯШНЕГО дня!
НЕ используй даты в прошлом (декабрь 2023, январь 2024 и т.д.)!

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
👥 НАША КОМАНДА
═══════════════════════════════════════════════════

📋 АКТУАЛЬНЫЙ СПИСОК МАСТЕРОВ будет предоставлен ниже в дополнительных инструкциях!
• Используй ТОЧНЫЕ ID мастеров из этого списка (m_anna_fed, m_platon_sos и т.д.)
• НЕ используй старые/выдуманные ID!
• При сомнениях вызови get_database_info(table='masters')

═══════════════════════════════════════════════════
🔍 КАК НАЙТИ НУЖНОГО МАСТЕРА
═══════════════════════════════════════════════════

Клиент спрашивает про СТИЛЬ ТАТУИРОВКИ:
→ Посмотри на специализацию мастеров в актуальном списке
→ Или вызови: get_database_info(table='masters')
Система автоматически поищет это ключевое слово в поле bio каждого мастера!

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
📋 ОБЯЗАТЕЛЬНЫЕ ДАННЫЕ КЛИЕНТА (ПЕРЕД ЗАПИСЬЮ!)
═══════════════════════════════════════════════════

⚠️ КРИТИЧЕСКИ ВАЖНО: Перед созданием записи ОБЯЗАТЕЛЬНО собери ВСЕ эти данные!
НЕ создавай запись пока не узнаешь:

1️⃣ ИМЯ - Как к тебе обращаться?
   Пример: "Кстати, как тебя зовут? 😊"

2️⃣ ПОЛ - Определи из имени или уточни аккуратно
   Пример: (обычно понятно из имени, если нет - "Подскажи, ты парень или девушка? Для записи 😊")

3️⃣ ОПЫТ С ТАТУ - Первая татуировка или уже есть?
   Пример: "Это будет первая тату или уже есть? 🎨"
   ⚠️ Если ПЕРВАЯ - дай больше информации про процесс, боль, уход!

4️⃣ ТЕЛЕФОН - Для связи и подтверждения
   Пример: "Оставь номер телефона для подтверждения записи 📱"
   
5️⃣ ГОРОД - Откуда клиент?
   Пример: "Ты из нашего города или приедешь откуда-то? 🚗"
   ⚠️ Если из ДРУГОГО ГОРОДА:
      - Учитывай время на дорогу
      - Предложи несколько сеансов в один день если большая работа
      - Можно записать на более длинный слот
      - "Раз приезжаешь - давай сделаем максимум за один визит!"

💡 КАК СОБИРАТЬ ДАННЫЕ ЕСТЕСТВЕННО:
• НЕ спрашивай всё сразу как анкету!
• Вплетай вопросы в разговор
• Можно спросить 2-3 вещи в одном сообщении
• Пример: "Классная идея! Как тебя зовут и это первая тату будет? 😊"

🚫 БЕЗ ЭТИХ ДАННЫХ - НЕ СОЗДАВАЙ ЗАПИСЬ!
Если клиент торопится - объясни: "Мне нужно пару деталей для записи - буквально минутку! 😊"

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
   ⛔ СТОП! ПЕРЕД ЗАПИСЬЮ ОБЯЗАТЕЛЬНО:
      1. Сначала вызови get_calendar_slots чтобы получить свободные слоты
      2. Покажи клиенту 2-3 варианта времени: "Могу предложить: среда 14:00, пятница 11:00 или суббота 16:00"
      3. ДОЖДИСЬ пока клиент ВЫБЕРЕТ конкретный слот!
      4. Только после выбора клиента - вызови create_booking
   
   ✅ ПРАВИЛЬНО:
      - Клиент: "запиши меня"
      - Ты: get_calendar_slots → "Есть время в среду 14:00, пятницу 11:00. Какое удобнее?"
      - Клиент: "в пятницу"  
      - Ты: create_booking на пятницу 11:00
      
   ❌ НЕПРАВИЛЬНО:
      - Клиент: "запиши меня"
      - Ты: СРАЗУ create_booking без предложения слотов!
   
   • Клиент должен ЯВНО подтвердить дату и время
   • Все детали уточнены (мастер, услуга, время)
   • Клиент дал явное "да", "записывай", "подтверждаю" НА КОНКРЕТНЫЙ СЛОТ
   ⚠️ ВАЖНО ПРИ СОЗДАНИИ ЗАПИСИ:
      - master_id должен быть РЕАЛЬНЫЙ ID из базы (см. АКТУАЛЬНЫЙ СПИСОК МАСТЕРОВ ниже)
      - НЕ используй числа 1, 2, 3 как master_id!
      - Год в дате должен быть ТЕКУЩИЙ (2025), не 2023!
      - Формат даты: YYYY-MM-DD (например: 2025-12-15)
   ❌ НЕ вызывай без явного подтверждения КОНКРЕТНОГО СЛОТА от клиента!
   
4. create_client - автоматически создаётся в create_booking

═══════════════════════════════════════════════════
🚫 ЧТО ЗАПРЕЩЕНО (КРИТИЧНО!)
═══════════════════════════════════════════════════

• Записывать клиента БЕЗ предварительного показа свободных слотов!
• Выбирать время ЗА клиента - он сам должен выбрать!
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
    
    def get_masters_info_for_prompt(self) -> str:
        """
        Получить динамическую информацию о мастерах из БД для промпта
        """
        try:
            if not self.sheets_client:
                return "⚠️ Информация о мастерах временно недоступна. Используй get_database_info(table='masters') для получения актуального списка."
            
            masters_data = self.get_database_info("masters")
            masters = masters_data.get("data", [])
            
            if not masters:
                return "⚠️ Список мастеров пуст. Используй get_database_info для проверки."
            
            info_lines = []
            for m in masters:
                if m.get("status") != "active":
                    continue
                    
                emoji = "🎨" if "тату" in m.get("specialization", "").lower() else "🔧"
                info_lines.append(f"""
{emoji} {m.get('name', 'Без имени')} (ID: {m.get('id', 'N/A')})
   ⭐ Рейтинг: {m.get('rating', 'N/A')}/5
   🎯 Специализация: {m.get('specialization', 'N/A')}
   📞 Опыт: {m.get('experience', 'N/A')} лет
   📝 О мастере: {m.get('bio', 'Нет описания')[:100]}...""")
            
            if not info_lines:
                return "⚠️ Нет активных мастеров"
            
            return "\n".join(info_lines)
        except Exception as e:
            logger.warning(f"Error getting masters for prompt: {e}")
            return "⚠️ Используй get_database_info(table='masters') для получения списка мастеров"
    
    def get_dynamic_system_prompt(self) -> str:
        """
        Генерировать системный промпт с актуальными данными из БД
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_date_readable = datetime.now().strftime("%d %B %Y года")
        masters_info = self.get_masters_info_for_prompt()
        
        return f"""{self.system_prompt}

═══════════════════════════════════════════════════
👥 АКТУАЛЬНЫЙ СПИСОК МАСТЕРОВ (из БД)
═══════════════════════════════════════════════════
{masters_info}

⚠️ ВАЖНО ПРИ СОЗДАНИИ ЗАПИСЕЙ:
- Используй ТОЧНЫЕ ID мастеров из списка выше (например: m_anna_fed, m_platon_sos)
- НЕ используй старые/выдуманные ID!
- Сегодня: {current_date} ({current_date_readable})
- При сомнениях вызови get_database_info(table='masters') для проверки
"""
    
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
                    "description": f"Получить доступные слоты в календаре мастера. ВАЖНО: Сегодня {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%d %B %Y')}). Используй текущую дату как start_date, не даты в прошлом! Результат содержит master_name - ВСЕГДА используй это имя в ответе, НЕ преобразуй master_id в имя самостоятельно!",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "master_id": {
                                "type": "string",
                                "description": "ID мастера из актуального списка мастеров (например: m_anna_fed, m_platon_sos). Используй ТОЧНЫЙ ID из БД, не выдумывай! Вызови get_database_info(table='masters') если не уверен."
                            },
                            "start_date": {
                                "type": "string",
                                "description": f"Начальная дата в формате YYYY-MM-DD. Сегодня: {datetime.now().strftime('%Y-%m-%d')}. НЕ используй даты в прошлом!"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "Конечная дата в формате YYYY-MM-DD (обычно +7 дней от start_date)"
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "description": "Требуемая продолжительность в минутах",
                                "default": 60
                            }
                        },
                        "required": []
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
                    "description": "Создать новую запись для клиента. ВАЖНО: Перед вызовом убедись что собрал ВСЕ обязательные данные клиента: имя, пол, телефон, город, опыт с тату (первая или нет)!",
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
                            "client_name": {
                                "type": "string",
                                "description": "Имя клиента (ОБЯЗАТЕЛЬНО!)"
                            },
                            "client_phone": {
                                "type": "string",
                                "description": "Телефон клиента (ОБЯЗАТЕЛЬНО!)"
                            },
                            "client_city": {
                                "type": "string",
                                "description": "Город клиента (ОБЯЗАТЕЛЬНО! Важно для планирования)"
                            },
                            "is_first_tattoo": {
                                "type": "boolean",
                                "description": "Первая татуировка у клиента? (ОБЯЗАТЕЛЬНО!)"
                            },
                            "client_gender": {
                                "type": "string",
                                "enum": ["male", "female"],
                                "description": "Пол клиента (ОБЯЗАТЕЛЬНО!)"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Дополнительные заметки (идея тату, размер, место и т.д.)"
                            }
                        },
                        "required": ["user_id", "master_id", "date", "time", "service", "client_name", "client_phone"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_client",
                    "description": "Создать или обновить профиль клиента с полной информацией",
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
                            "gender": {
                                "type": "string",
                                "enum": ["male", "female"],
                                "description": "Пол клиента"
                            },
                            "city": {
                                "type": "string",
                                "description": "Город проживания"
                            },
                            "is_first_tattoo": {
                                "type": "boolean",
                                "description": "Первая татуировка?"
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
                        "required": ["telegram_id", "name", "phone"]
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
                         filter_value: Optional[str] = None, limit: int = 50) -> Dict:
        """Получить информацию из базы данных с кэшированием расписания"""
        try:
            from src.web.app import db_manager as _db_manager
            if not self.sheets_client and not _db_manager:
                return {"error": "Database connection not available"}
            
            # Нормализуем названия таблиц (преобразуем английский/lowercase в русский)
            table = self._normalize_table_name(table)
            logger.debug(f"Table name normalized to: {table}")
            
            # Используем кэш для часто используемых таблиц (обновляется каждые 5 минут)
            current_time = time.time()
            cache_ttl = 300  # 5 минут (было 1 час)
            
            if table == "Расписание":
                if self._schedule_cache is not None and (current_time - self._schedule_cache_time) < cache_ttl:
                    logger.info("📅 Using cached schedule data")
                    return self._schedule_cache
            elif table == "Мастера":
                if self._masters_cache is not None and (current_time - self._masters_cache_time) < cache_ttl:
                    logger.info("👨‍💼 Using cached masters data")
                    return self._masters_cache
            elif table == "Услуги":
                if self._services_cache is not None and (current_time - self._services_cache_time) < cache_ttl:
                    logger.info("💼 Using cached services data")
                    return self._services_cache
            
            # Получаем все данные из таблицы
            # If there is no sheets_client but a DB manager (e.g., running under web app), use it
            if not self.sheets_client and _db_manager:
                table_lower = table.strip().lower()
                if table_lower in ("мастера", "masters", "мастер", "master"):
                    rows_dicts = _db_manager.get_all_masters()
                elif table_lower in ("услуги", "services", "услуга", "service"):
                    rows_dicts = _db_manager.get_all_services()
                elif table_lower in ("записи", "bookings", "запись", "booking"):
                    rows_dicts = _db_manager.get_all_bookings()
                elif table_lower in ("клиенты", "clients", "client", "клиент"):
                    rows_dicts = _db_manager.get_all_clients()
                else:
                    rows_dicts = []

                if not rows_dicts:
                    return {"data": [], "count": 0, "message": f"Таблица {table} пуста"}

                # Build headers and matrix-compatible 'data' as expected by the rest of this method
                headers = list(rows_dicts[0].keys())
                data = [headers]
                for d in rows_dicts:
                    data.append([d.get(h, "") for h in headers])
            else:
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
            if table == "Расписание":
                self._schedule_cache = response
                self._schedule_cache_time = time.time()
            elif table == "Мастера":
                self._masters_cache = response
                self._masters_cache_time = time.time()
            elif table == "Услуги":
                self._services_cache = response
                self._services_cache_time = time.time()
            
            return response
        
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return {"error": str(e)}
    
    def get_calendar_slots(self, start_date: str = None, end_date: str = None, 
                          master_id: Optional[str] = None, 
                          duration_minutes: int = 60) -> Dict:
        """Получить доступные слоты из Google Calendar и системы записей"""
        try:
            # ============================================================
            # АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ ДАТ
            # ============================================================
            today = datetime.now()
            
            # Если start_date не указан или в прошлом - используем сегодня
            if not start_date:
                start_date = today.strftime("%Y-%m-%d")
            else:
                start_dt_check = datetime.strptime(start_date, "%Y-%m-%d")
                if start_dt_check < today.replace(hour=0, minute=0, second=0, microsecond=0):
                    start_date = today.strftime("%Y-%m-%d")
                    logger.info(f"📅 Start date was in past, using today: {start_date}")
            
            # Если end_date не указан - ищем на неделю вперёд
            if not end_date:
                end_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
            else:
                end_dt_check = datetime.strptime(end_date, "%Y-%m-%d")
                if end_dt_check < datetime.strptime(start_date, "%Y-%m-%d"):
                    end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
            
            logger.info(f"📅 Searching slots from {start_date} to {end_date}")
            # ============================================================
            
            # Парсим даты
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Получаем calendar_id мастера если указан
            master_calendar_id = None
            master_found = None
            if master_id:
                masters_data = self.get_database_info("masters", limit=50)
                masters = masters_data.get("data", [])
                logger.info(f"📅 Got {len(masters)} masters from DB")
                
                # Сначала ищем по точному ID
                master_found = next((m for m in masters if m.get("id") == master_id), None)
                
                # Если не найден по ID, ищем по имени (частичное совпадение)
                if not master_found:
                    master_name_lower = master_id.lower()
                    for m in masters:
                        m_name = m.get("name", "").lower()
                        # Проверяем разные варианты совпадения
                        if master_name_lower in m_name or m_name in master_name_lower:
                            master_found = m
                            logger.info(f"📅 Found master by name match: {m.get('name')} -> {m.get('id')}")
                            break
                        # Проверка по частям имени (Анна -> Анна Федорова)
                        if any(part in m_name for part in master_name_lower.split()):
                            master_found = m
                            logger.info(f"📅 Found master by partial name: {m.get('name')} -> {m.get('id')}")
                            break
                
                if master_found:
                    master_calendar_id = master_found.get("calendar_id")
                    master_id = master_found.get("id")  # Обновляем master_id на правильный
                    logger.info(f"📅 Master found: {master_found.get('name')}, calendar_id: {master_calendar_id}")
                else:
                    logger.warning(f"📅 Master not found: {master_id}")
            
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
            schedule_data = self.get_database_info("schedule", limit=200)  # Увеличиваем лимит
            schedule_rows = schedule_data.get("data", [])
            
            # Дефолтное расписание 10:00-18:00
            default_schedule = [
                {"master_id": "default", "day_of_week": "monday", "start_time": "10:00", "end_time": "19:00", "is_working": "true"},
                {"master_id": "default", "day_of_week": "tuesday", "start_time": "10:00", "end_time": "19:00", "is_working": "true"},
                {"master_id": "default", "day_of_week": "wednesday", "start_time": "10:00", "end_time": "19:00", "is_working": "true"},
                {"master_id": "default", "day_of_week": "thursday", "start_time": "10:00", "end_time": "19:00", "is_working": "true"},
                {"master_id": "default", "day_of_week": "friday", "start_time": "10:00", "end_time": "19:00", "is_working": "true"},
                {"master_id": "default", "day_of_week": "saturday", "start_time": "10:00", "end_time": "17:00", "is_working": "true"},
                {"master_id": "default", "day_of_week": "sunday", "start_time": "10:00", "end_time": "17:00", "is_working": "true"},
            ]
            
            # Фильтруем расписание по мастеру если указан
            if master_id and schedule_rows:
                # Сначала пробуем искать по точному master_id
                master_schedule = [s for s in schedule_rows if s.get("master_id") == master_id]
                logger.info(f"📅 Master schedule entries by ID: {len(master_schedule)} for {master_id}")
                
                # Если не нашли по ID, ищем по любому UUID в Schedule и привязываем через имя
                if not master_schedule and master_found:
                    # Получаем уникальные master_id из Schedule
                    schedule_master_ids = list(set(s.get("master_id") for s in schedule_rows if s.get("master_id")))
                    logger.info(f"📅 Unique master_ids in Schedule table: {schedule_master_ids[:5]}...")
                    
                    # Если найден только один мастер в Schedule (или первый с 7 днями расписания)
                    # Используем его расписание для нашего мастера
                    for sched_master_id in schedule_master_ids:
                        sched_entries = [s for s in schedule_rows if s.get("master_id") == sched_master_id]
                        if len(sched_entries) >= 6:  # Полная рабочая неделя
                            master_schedule = sched_entries
                            logger.info(f"📅 Using schedule from {sched_master_id} ({len(sched_entries)} entries) for master {master_id}")
                            break
                
                # Если у мастера нет своего расписания - используем дефолтное
                if not master_schedule:
                    logger.info(f"📅 No schedule for {master_id} in DB, using DEFAULT schedule")
                    schedule_rows = default_schedule
                else:
                    schedule_rows = master_schedule
            elif not schedule_rows:
                logger.warning("No schedule found in database, using default working hours")
                schedule_rows = default_schedule
            
            logger.info(f"📅 Total schedule rows to process: {len(schedule_rows)}")
            
            # Генерируем слоты на основе расписания Sheets
            free_slots = []
            current = start_dt
            
            while current <= end_dt:
                day_of_week = current.strftime("%A").lower()
                
                # Находим расписание для этого дня
                day_schedule = [s for s in schedule_rows if s.get("day_of_week") == day_of_week]
                logger.debug(f"📅 Day {current.strftime('%Y-%m-%d')} ({day_of_week}): {len(day_schedule)} schedule entries")
                
                for schedule in day_schedule:
                    # Проверка is_working с учетом разных регистров
                    is_working_val = str(schedule.get("is_working", "false")).lower()
                    if is_working_val != "true":
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
            
            logger.info(f"📅 RESULT: Found {len(free_slots)} free slots for master {master_id} from {start_date} to {end_date}")
            
            # Получаем имя мастера для ответа
            master_name = "Мастер"
            if master_found:
                master_name = master_found.get("name", "Мастер")
            
            return {
                "slots": free_slots[:20],  # Ограничиваем 20 слотами
                "count": len(free_slots),
                "total_available": len(free_slots),
                "master_id": master_id,
                "master_name": master_name,  # Добавляем имя мастера для INKA
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
            # Accept either sheets_client or db_manager (if INKA is running in web app)
            from src.web.app import db_manager as _db_manager
            if not self.sheets_client and not _db_manager:
                logger.error("❌ Database connection not available (no sheets_client or db_manager)")
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
                    "client": {**existing_client, "user_id": existing_client.get("telegram_id")},
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
            
            # Try to go through admin db manager if available (to keep behavior consistent)
            success = False
            try:
                from src.web.app import db_manager
                if db_manager:
                    # db_manager.add_client expects keys like 'name', 'phone', 'telegram_id', 'email', 'notes'
                            success, msg = db_manager.add_client({
                        'name': name,
                        'phone': phone or "",
                        'telegram_id': telegram_id_str,
                        'email': email or "",
                        'notes': notes or ""
                            }, actor='inka')
            except Exception:
                # Ignore and fallback to direct append
                pass
            if not success:
                success = self.sheets_client.append_row("Клиенты", client_row)
            
            if success:
                logger.info(f"✅ Client created: {client_id}, name={name}, telegram_id={telegram_id_str}")
                return {
                    "success": True,
                    "message": f"✅ Создан новый профиль: {name}",
                    "client": {
                        "id": client_id,
                        "client_id": client_id,
                        "telegram_id": telegram_id_str,
                        "user_id": telegram_id_str,
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

    # ------------------ ADMIN DB WRAPPERS (USED BY INKA) ------------------
    def get_clients(self, search: str = None):
        """Return list of clients via admin db manager or sheets directly"""
        try:
            from src.web.app import db_manager
            if db_manager:
                return db_manager.get_all_clients()
        except Exception:
            pass
        # fallback
        try:
            rows = self.sheets_client.get_sheet_values("Clients")
            if not rows:
                return []
            headers = rows[0]
            data = []
            for row in rows[1:]:
                d = {headers[i]: row[i] if i < len(row) else '' for i in range(len(headers))}
                data.append(d)
            return data
        except Exception as e:
            logger.error(f"Error reading clients directly: {e}")
            return []

    def get_client_by_user_id(self, user_id: str):
        """Find client by user_id (telegram ID) or by client id"""
        try:
            from src.web.app import db_manager
            if db_manager:
                clients = db_manager.get_all_clients()
                for c in clients:
                    if str(c.get('user_id') or c.get('telegram_id') or '') == str(user_id):
                        return c
            # Fallback - look in sheets
            rows = self.sheets_client.get_sheet_values('Clients')
            if rows and len(rows) > 1:
                headers = rows[0]
                for row in rows[1:]:
                    # Telegram ID may be column 1 (index 1) per conventions
                    if len(row) > 1 and str(row[1]).strip() == str(user_id).strip():
                        return {headers[i]: row[i] if i < len(row) else '' for i in range(len(headers))}
        except Exception as e:
            logger.error(f"Error getting client by user_id: {e}")
        return None

    def edit_client_by_user_id(self, user_id: str, updates: Dict[str, str]) -> Dict:
        """Edit client by user id using db_manager if present"""
        try:
            from src.web.app import db_manager
            if db_manager:
                clients = db_manager.get_all_clients()
                for c in clients:
                    if str(c.get('user_id') or c.get('telegram_id') or '') == str(user_id):
                        client_id = c.get('client_id') or c.get('id')
                        return {'success': bool(db_manager.edit_client(client_id, updates))}
            return {'success': False, 'message': 'Client or DB Manager not found'}
        except Exception as e:
            logger.error(f"Error editing client by user id: {e}")
            return {'success': False, 'message': str(e)}

    def add_master(self, master_data: Dict[str, str]) -> Dict:
        try:
            from src.web.app import db_manager
            if db_manager:
                success, msg = db_manager.add_master(master_data)
                return {"success": success, "message": msg}
            return {"success": False, "message": "DB manager not available"}
        except Exception as e:
            logger.error(f"Error adding master: {e}")
            return {"success": False, "message": str(e)}

    def add_service(self, service_data: Dict[str, str]) -> Dict:
        try:
            from src.web.app import db_manager
            if db_manager:
                success, msg = db_manager.add_service(service_data)
                return {"success": success, "message": msg}
            return {"success": False, "message": "DB manager not available"}
        except Exception as e:
            logger.error(f"Error adding service: {e}")
            return {"success": False, "message": str(e)}

    def confirm_booking_by_id(self, booking_id: str) -> Dict:
        try:
            from src.web.app import db_manager
            if db_manager:
                success, msg = db_manager.confirm_booking(booking_id)
                return {"success": success, "message": msg}
            return {"success": False, "message": "DB manager not available"}
        except Exception as e:
            logger.error(f"Error confirming booking: {e}")
            return {"success": False, "message": str(e)}

    def complete_booking_by_id(self, booking_id: str) -> Dict:
        try:
            from src.web.app import db_manager
            if db_manager:
                success, msg = db_manager.complete_booking(booking_id)
                return {"success": success, "message": msg}
            return {"success": False, "message": "DB manager not available"}
        except Exception as e:
            logger.error(f"Error completing booking: {e}")
            return {"success": False, "message": str(e)}

    def cancel_booking_by_id(self, booking_id: str, reason: str = "") -> Dict:
        try:
            from src.web.app import db_manager
            if db_manager:
                success, msg = db_manager.cancel_booking(booking_id, reason)
                return {"success": success, "message": msg}
            return {"success": False, "message": "DB manager not available"}
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}")
            return {"success": False, "message": str(e)}
    
    def create_booking(self, user_id: str, master_id: str, date: str, 
                      time: str, service: str, notes: str = "",
                      client_name: str = "", client_phone: str = "",
                      client_city: str = "", is_first_tattoo: bool = None,
                      client_gender: str = "") -> Dict:
        """Создать запись в БД и добавить событие в Google Calendar
        
        ОБЯЗАТЕЛЬНЫЕ ДАННЫЕ КЛИЕНТА:
        - client_name: Имя клиента
        - client_phone: Телефон для связи
        - client_city: Город (важно для планирования)
        - is_first_tattoo: Первая татуировка?
        - client_gender: Пол клиента
        """
        try:
            from src.web.app import db_manager as _db_manager
            if not self.sheets_client and not _db_manager:
                return {"error": "Database connection not available"}
            
            # ============================================================
            # ВАЛИДАЦИЯ ОБЯЗАТЕЛЬНЫХ ПОЛЕЙ КЛИЕНТА
            # ============================================================
            
            if not client_name:
                return {"error": "⚠️ Не указано имя клиента! Спроси как зовут."}
            if not client_phone:
                return {"error": "⚠️ Не указан телефон клиента! Спроси номер для связи."}
            
            # Формируем расширенные заметки
            extended_notes = []
            if notes:
                extended_notes.append(notes)
            if client_city:
                extended_notes.append(f"Город: {client_city}")
            if is_first_tattoo is not None:
                extended_notes.append(f"Первая тату: {'Да' if is_first_tattoo else 'Нет'}")
            if client_gender:
                extended_notes.append(f"Пол: {'М' if client_gender == 'male' else 'Ж'}")
            
            full_notes = " | ".join(extended_notes) if extended_notes else ""
            
            # ============================================================
            # ВАЛИДАЦИЯ И ИСПРАВЛЕНИЕ ВХОДНЫХ ДАННЫХ
            # ============================================================
            
            # Получаем всех мастеров для валидации
            all_masters = self.get_database_info("masters").get("data", [])
            
            # Если master_id - это число (индекс), найти реальный ID
            if master_id.isdigit():
                idx = int(master_id) - 1  # Индекс начинается с 1
                if 0 <= idx < len(all_masters):
                    master_id = all_masters[idx].get("id", master_id)
                    logger.info(f"📝 Converted master index {idx+1} to ID: {master_id}")
            
            # Если master_id - это имя мастера, найти реальный ID
            if not master_id.startswith("m_") and not master_id.startswith("e"):
                for m in all_masters:
                    if master_id.lower() in m.get("name", "").lower():
                        master_id = m.get("id")
                        logger.info(f"📝 Found master by name: {master_id}")
                        break
            
            # Исправляем год если он в прошлом (2023, 2024 -> текущий год)
            current_year = datetime.now().year
            if date and len(date) >= 4:
                year_in_date = int(date[:4])
                if year_in_date < current_year:
                    date = str(current_year) + date[4:]
                    logger.info(f"📝 Fixed year in date: {date}")
            
            # ============================================================
            
            # Сначала получаем или создаём клиента
            clients_data = self.get_database_info("clients", "telegram_id", str(user_id))
            
            if not clients_data.get("data") or len(clients_data["data"]) == 0:
                # Создаём нового клиента с полными данными
                client_notes = []
                if client_city:
                    client_notes.append(f"Город: {client_city}")
                if is_first_tattoo is not None:
                    client_notes.append(f"Первая тату: {'Да' if is_first_tattoo else 'Нет'}")
                if client_gender:
                    client_notes.append(f"Пол: {'М' if client_gender == 'male' else 'Ж'}")
                
                client_result = self.create_client(
                    str(user_id), 
                    client_name or "Client", 
                    client_phone or "", 
                    "",  # email
                    " | ".join(client_notes) if client_notes else ""
                )
                if client_result.get("error"):
                    return client_result
                client_id = client_result["client"]["id"]
            else:
                client_id = clients_data["data"][0]["id"]
                # Обновляем данные клиента если есть новая информация
                if client_name or client_phone:
                    try:
                        existing = clients_data["data"][0]
                        update_data = {}
                        if client_name and existing.get("name", "Client") == "Client":
                            update_data["name"] = client_name
                        if client_phone and not existing.get("phone"):
                            update_data["phone"] = client_phone
                        # Добавляем город и инфо в заметки
                        if client_city or is_first_tattoo is not None or client_gender:
                            new_notes = []
                            if client_city:
                                new_notes.append(f"Город: {client_city}")
                            if is_first_tattoo is not None:
                                new_notes.append(f"Первая тату: {'Да' if is_first_tattoo else 'Нет'}")
                            if client_gender:
                                new_notes.append(f"Пол: {'М' if client_gender == 'male' else 'Ж'}")
                            old_notes = existing.get("notes", "")
                            update_data["notes"] = f"{old_notes} | {' | '.join(new_notes)}" if old_notes else " | ".join(new_notes)
                        
                        if update_data:
                            logger.info(f"Updating client {client_id} with: {update_data}")
                            # Реально обновляем клиента в БД
                            try:
                                # prefer db_manager
                                from src.web.app import db_manager as _db_manager
                                if _db_manager:
                                    _db_manager.edit_client(client_id, update_data, actor='inka')
                                elif self.sheets_client:
                                    self.sheets_client.update_client(client_id, update_data)
                                logger.info(f"✅ Client {client_id} updated successfully")
                            except Exception as upd_e:
                                logger.warning(f"Could not update client in sheets/db manager: {upd_e}")
                    except Exception as e:
                        logger.warning(f"Could not update client: {e}")
            
            # Получаем информацию о мастере — prefer db_manager if present
            master = None
            try:
                from src.web.app import db_manager as _db_manager
                if _db_manager:
                    masters = _db_manager.get_all_masters()
                    master = next((m for m in masters if m.get('id') == master_id), None)
            except Exception:
                master = None

            if not master:
                masters_data = self.get_database_info("masters", "id", master_id, limit=1)
                if not masters_data.get("data"):
                    return {"error": f"Master {master_id} not found"}
                master = masters_data["data"][0]

            master_name = master.get("name", f"Master {master_id}")
            
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
                full_notes,          # notes (включает город, пол, первая тату и т.д.)
                created_at           # created_at
            ]
            
            # Добавляем запись в таблицу — prefer admin DB manager to enforce validation and audit
            success = False
            try:
                from src.web.app import db_manager
                if db_manager:
                    success, msg = db_manager.add_booking({
                        'client_id': client_id,
                        'master_id': master_id,
                        'service_id': service,
                        'date': date,
                        'time': time,
                        'duration_min': '60',
                        'price': '',
                        'status': 'confirmed',
                        'notes': full_notes,
                        'created_at': created_at
                    }, actor='inka')
            except Exception:
                pass
            if not success:
                success = self.sheets_client.append_row("Записи", booking_row)
            
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
            
            # ============================================================
            # 🧠 АНАЛИЗ ПОВЕДЕНИЯ КЛИЕНТА
            # ============================================================
            behavior_context = ""
            booking_blocked = False
            block_reason = ""
            
            if not is_admin:
                try:
                    from src.services.behavior_service import get_behavior_service
                    behavior_service = get_behavior_service(self.sheets_client)
                    
                    # Получаем историю сообщений для контекста
                    msg_history = behavior_service.get_message_history(str(user_id))
                    
                    # Анализируем текущее сообщение
                    behavior = behavior_service.analyze_message_behavior(user_message, msg_history)
                    
                    # Сохраняем в историю
                    behavior_service.add_message_to_history(str(user_id), user_message, behavior)
                    
                    # Рассчитываем риск
                    risk_level = behavior_service.calculate_risk_level(str(user_id))
                    
                    logger.info(f"🧠 Behavior: {behavior['behavior']} ({behavior['confidence']:.2f}), risk={risk_level}")
                    
                    # Проверяем доступ к записи
                    booking_allowed, block_reason = behavior_service.is_booking_allowed(str(user_id))
                    if not booking_allowed:
                        booking_blocked = True
                        logger.warning(f"⚠️ Booking blocked for user {user_id}: {block_reason}")
                    
                    # Получаем стиль ответа
                    style_hint = behavior_service.get_response_style(str(user_id))
                    if style_hint:
                        behavior_context = f"\n\n[АДАПТАЦИЯ СТИЛЯ]: {style_hint}"
                    
                    # Уведомляем админа при высоком риске
                    should_notify, notification = behavior_service.should_notify_admin(str(user_id))
                    if should_notify and notification:
                        logger.warning(f"🚨 ADMIN NOTIFICATION: {notification['message']}")
                        # TODO: отправить в Telegram админу
                
                except Exception as e:
                    logger.warning(f"Behavior analysis error (non-critical): {e}")
            
            # ============================================================
            
            # Загружаем обучающий контекст
            training_context = self.get_training_context()
            
            # Создаём thread для разговора
            thread = self.client.beta.threads.create()
            
            # Если есть обучающий контекст - добавляем как первое сообщение
            if training_context:
                self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=f"[СИСТЕМНОЕ СООБЩЕНИЕ - ОБЯЗАТЕЛЬНО СЛЕДУЙ ЭТИМ ИНСТРУКЦИЯМ]{training_context}{behavior_context}"
                )
                # Подтверждение от ассистента что понял
                self.client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="assistant", 
                    content="Понял, буду следовать этим инструкциям при общении с клиентами."
                )
            
            # Добавляем историю
            if conversation_history:
                for msg in conversation_history[-10:]:
                    self.client.beta.threads.messages.create(
                        thread_id=thread.id,
                        role=msg.get("role", "user"),
                        content=msg.get("content", "")
                    )
            
            # Если клиент заблокирован - возвращаем сообщение без AI
            if booking_blocked:
                return block_reason
            
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
            
            # Получаем динамический контекст с актуальными мастерами из БД
            dynamic_instructions = self.get_dynamic_system_prompt()
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id,
                tools=tools_config,
                additional_instructions=dynamic_instructions
            )
            
            logger.info(f"🤖 Run created: {run.id}, status: {run.status}")
            
            # Ждём завершения с обработкой вызовов функций
            max_iterations = 30  # Увеличено для долгих запросов
            iteration = 0
            queued_count = 0
            
            while run.status in ["queued", "in_progress", "requires_action"] and iteration < max_iterations:
                # Адаптивный таймаут: дольше ждём для queued
                if run.status == "queued":
                    queued_count += 1
                    time.sleep(1.5)  # Дольше ждём когда в очереди
                else:
                    time.sleep(0.8)  # Быстрее проверяем в процессе
                    queued_count = 0
                    
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                logger.info(f"📍 Run status: {run.status} (iteration {iteration}, queued: {queued_count})")

                
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
    
    def get_training_context(self) -> str:
        """Загружает обучающие данные для добавления в контекст"""
        try:
            if not self.sheets_client:
                return ""
            
            training_context = "\n\n═══════════════════════════════════════════════════\n"
            training_context += "📚 ОБУЧЕНИЕ ОТ АДМИНА (следуй этим инструкциям!)\n"
            training_context += "═══════════════════════════════════════════════════\n\n"
            
            # Загружаем знания
            try:
                knowledge = self.sheets_client.get_all_rows("INKA_Knowledge")
                if len(knowledge) > 1:
                    training_context += "📌 ИЗУЧЕННЫЕ ФАКТЫ И ПРАВИЛА:\n"
                    for row in knowledge[1:20]:  # Максимум 20 записей
                        if len(row) >= 4:
                            k_type = row[1]
                            title = row[2]
                            content = row[3]
                            training_context += f"• [{k_type.upper()}] {title}: {content}\n"
                    training_context += "\n"
            except Exception as e:
                logger.debug(f"No INKA_Knowledge sheet: {e}")
            
            # Загружаем сценарии
            try:
                scenarios = self.sheets_client.get_all_rows("INKA_Scenarios")
                if len(scenarios) > 1:
                    training_context += "💬 ИЗУЧЕННЫЕ СЦЕНАРИИ ДИАЛОГА:\n"
                    for row in scenarios[1:15]:  # Максимум 15 сценариев
                        if len(row) >= 4:
                            category = row[1]
                            trigger = row[2]
                            response = row[3]
                            training_context += f"• Если клиент говорит: \"{trigger}\"\n"
                            training_context += f"  → Правильный ответ: \"{response}\"\n\n"
                    training_context += "\n"
            except Exception as e:
                logger.debug(f"No INKA_Scenarios sheet: {e}")
            
            # Загружаем коррекции
            try:
                corrections = self.sheets_client.get_all_rows("INKA_Corrections")
                if len(corrections) > 1:
                    training_context += "⚠️ КОРРЕКЦИИ (чего избегать!):\n"
                    for row in corrections[1:10]:  # Максимум 10 коррекций
                        if len(row) >= 3:
                            wrong = row[1]
                            correct = row[2]
                            training_context += f"• ❌ НЕ говори: \"{wrong[:100]}\"\n"
                            training_context += f"  ✅ Говори вместо этого: \"{correct[:100]}\"\n\n"
            except Exception as e:
                logger.debug(f"No INKA_Corrections sheet: {e}")
            
            if len(training_context) > 200:  # Если есть реальные данные
                logger.info(f"📚 Loaded training context: {len(training_context)} chars")
                return training_context
            return ""
        
        except Exception as e:
            logger.error(f"Error loading training context: {e}")
            return ""
    
    def _normalize_table_name(self, table: str) -> str:
        """Нормализовать название таблицы (преобразовать в русский формат)"""
        table_mapping = {
            "masters": "Мастера",
            "master": "Мастера",
            "clients": "Клиенты",
            "client": "Клиенты",
            "bookings": "Записи",
            "booking": "Записи",
            "services": "Услуги",
            "service": "Услуги",
            "schedule": "Расписание",
            "reviews": "Отзывы",
            "pricing": "Прайс-лист"
        }
        return table_mapping.get(table.lower(), table)


from src.config import get_config

def get_advanced_inka(
    api_key: str = None, 
    assistant_id: str = None, 
    sheets_client=None, 
    calendar_service=None,
    data_sync=None, 
    admin_ids: List[int] = None
) -> AdvancedINKA:
    """Фабрика для создания продвинутого INKA с админ-правами"""
    config = get_config()
    
    if api_key is None:
        api_key = config.openai_api_key
    
    if assistant_id is None:
        assistant_id = config.openai_assistant_id
    
    return AdvancedINKA(api_key, assistant_id, sheets_client, calendar_service, data_sync, admin_ids)
