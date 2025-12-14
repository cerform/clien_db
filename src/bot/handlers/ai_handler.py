"""
AI Handler - Главный обработчик всех сообщений через AI
Полностью заменяет клавиатуры и команды естественным диалогом
"""

import logging
from typing import Optional
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from src.services.ai_dialog_engine import AIDialogEngine, UserRole
from src.services.ai_orchestrator import AIOrchestrator
from src.config.config import Config
from src.services.admin_manager import is_admin, get_admin_ids as get_runtime_admin_ids
from src.config.env_loader import load_env

logger = logging.getLogger(__name__)

# Глобальные экземпляры
_ai_engine: Optional[AIDialogEngine] = None
_ai_orchestrator: Optional[AIOrchestrator] = None


def get_ai_engine() -> AIDialogEngine:
    """Получить или инициализировать AI engine"""
    global _ai_engine
    if _ai_engine is None:
        try:
            load_env()
            cfg = Config.from_env()
            
            # Check if API key is valid and has quota
            api_key = cfg.OPENAI_API_KEY
            if not api_key or api_key == "YOUR_OPENAI_API_KEY":
                logger.warning("⚠️ No valid OpenAI API key - using fallback mode")
                api_key = None
            
            _ai_engine = AIDialogEngine(
                api_key=api_key,
                default_language="ru"
            )
            logger.info("✅ AI Dialog Engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AI Engine: {e}")
            raise
    return _ai_engine


def get_ai_orchestrator() -> AIOrchestrator:
    """Получить или инициализировать AI orchestrator"""
    global _ai_orchestrator
    if _ai_orchestrator is None:
        engine = get_ai_engine()
        _ai_orchestrator = AIOrchestrator(engine)
        logger.info("✅ AI Orchestrator initialized")
    return _ai_orchestrator


def determine_user_role(user_id: int, admin_ids: list) -> UserRole:
    """
    Определить роль пользователя
    
    Args:
        user_id: Telegram user ID
        admin_ids: Список ID администраторов
        
    Returns:
        UserRole
    """
    # Use admin manager for checks if provided
    try:
        if is_admin(user_id):
            return UserRole.ADMIN
    except Exception:
        # fallback to provided admin_ids list
        pass
    if user_id in admin_ids:
        return UserRole.ADMIN
    # Можно добавить логику для определения мастеров
    return UserRole.CLIENT


def create_ai_router() -> Router:
    """Создать router с AI обработкой"""
    router = Router()
    
    # Загружаем конфиг для получения admin_ids
    try:
        # Prefer runtime admin list (env + sheet) to keep web and bot permissions in sync
        admin_ids = get_runtime_admin_ids()
        if not admin_ids:
            load_env()
            cfg = Config.from_env()
            admin_ids = cfg.ADMIN_USER_IDS or []
    except Exception as e:
        logger.warning(f"Failed to load admin IDs: {e}")
        admin_ids = []
    
    @router.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        """
        Команда /start - приветствие на языке пользователя
        """
        try:
            orchestrator = get_ai_orchestrator()
            user_role = determine_user_role(message.from_user.id, admin_ids)
            
            # Обрабатываем как обычное сообщение через AI
            welcome_message = "Hello! I want to learn about tattoos and book an appointment."
            
            result = await orchestrator.process_user_message(
                user_id=message.from_user.id,
                message=welcome_message,
                user_role=user_role,
                telegram_user=message.from_user
            )
            
            # Отправляем ответ
            await message.answer(result["text_response"])
            
        except Exception as e:
            logger.exception(f"Error in /start: {e}")
            await message.answer(
                "🎨 Добро пожаловать в тату-студию!\n\n"
                "Пишите мне на любом языке (русский, English, עברית), "
                "я вас пойму и помогу с записью или консультацией! 😊"
            )
    
    @router.message(Command("reset"))
    async def cmd_reset(message: types.Message):
        """Сбросить историю диалога"""
        try:
            engine = get_ai_engine()
            engine.clear_history(message.from_user.id)
            
            reset_messages = {
                "ru": "🔄 История диалога очищена. Начнём сначала!",
                "en": "🔄 Conversation history cleared. Let's start fresh!",
                "he": "🔄 היסטוריית השיחה נוקתה. בוא נתחיל מחדש!"
            }
            
            # Определяем язык пользователя (простая эвристика)
            lang_code = message.from_user.language_code or "en"
            if lang_code.startswith("ru"):
                msg = reset_messages["ru"]
            elif lang_code.startswith("he"):
                msg = reset_messages["he"]
            else:
                msg = reset_messages["en"]
            
            await message.answer(msg)
            
        except Exception as e:
            logger.exception(f"Error in /reset: {e}")
            await message.answer("✅ Reset complete")
    
    @router.message(Command("help"))
    async def cmd_help(message: types.Message):
        """Помощь - что умеет AI бот"""
        user_role = determine_user_role(message.from_user.id, admin_ids)
        
        if user_role == UserRole.ADMIN:
            help_text = """🤖 **AI Администратор тату-студии**

Я понимаю естественный язык и могу:

**📋 Управление записями:**
• Просмотреть все записи
• Показать расписание на дату
• Добавить/удалить слоты
• Управлять записями клиентов

**📊 Аналитика:**
• Статистика по периодам
• Загруженность мастера
• Популярные услуги

**💬 Общение:**
• Отправить сообщение клиенту
• Ответить на вопросы

Просто пишите мне на русском, английском или иврите, как обычно общаетесь!

Примеры:
- "Покажи все записи на завтра"
- "Добавь свободное время 15 декабря с 14:00 до 18:00"
- "Какая статистика за неделю?"
"""
        else:
            help_text = """🤖 **AI Ассистент тату-студии**

Я понимаю естественный язык на русском, английском и иврите!

Что я могу:

**🎨 Консультации:**
• Помочь с выбором дизайна
• Посоветовать размер и расположение
• Ответить на вопросы об уходе
• Рассказать о стилях

**📅 Записи:**
• Показать свободное время
• Записать на сеанс
• Перенести или отменить запись
• Показать ваши записи

**💬 Диалог:**
• Ответить на любые вопросы
• Помочь с идеей татуировки
• Обсудить детали

Примеры сообщений:
- "Хочу маленькую татуировку на запястье"
- "Когда есть свободное время на следующей неделе?"
- "Покажи мои записи"
- "Можно перенести запись на другой день?"

Просто пишите естественно, как обычно общаетесь! 😊
"""
        
        await message.answer(help_text, parse_mode="Markdown")
    
    @router.message(Command("admin"))
    async def cmd_admin(message: types.Message):
        """Административная панель"""
        user_role = determine_user_role(message.from_user.id, admin_ids)
        
        if user_role != UserRole.ADMIN:
            await message.answer("⛔️ У вас нет доступа к административным функциям")
            return
        
        admin_text = """👑 **Административная панель**

Вы можете управлять студией через естественный язык:

📋 **Записи:**
- "Покажи все записи на сегодня"
- "Кто записан на завтра?"
- "Отмени запись клиента Иван"

📅 **Расписание:**
- "Покажи расписание на неделю"
- "Добавь слот 20 декабря 15:00-19:00"
- "Заблокируй 25 декабря"

📊 **Статистика:**
- "Статистика за месяц"
- "Сколько записей за неделю?"
- "Покажи доход"

💬 **Клиенты:**
- "Отправь сообщение клиенту 123"
- "Список всех клиентов"

Примеры команд для управления админ-правами:
- `/grant_admin <telegram_id>` — добавить нового администратора
- `/revoke_admin <telegram_id>` — лишить администратора прав

Просто пишите команды естественным языком!
"""
        await message.answer(admin_text, parse_mode="Markdown")
    
    @router.message(F.text)
    async def handle_text_message(message: types.Message, state: FSMContext):
        """
        Главный обработчик всех текстовых сообщений через AI
        """
        user_id = message.from_user.id
        user_name = message.from_user.full_name
        message_text = message.text
        
        try:
            logger.info("="*80)
            logger.info(f"📨 INCOMING MESSAGE")
            logger.info(f"   User: {user_name} (ID: {user_id})")
            logger.info(f"   Text: {message_text}")
            logger.info("="*80)
            
            # Показываем что бот печатает
            await message.bot.send_chat_action(
                chat_id=message.chat.id,
                action="typing"
            )
            
            user_role = determine_user_role(message.from_user.id, admin_ids)
            logger.info(f"👤 User role: {user_role}")
            
            orchestrator = get_ai_orchestrator()
            
            # Обрабатываем сообщение через AI
            logger.info("🤖 Sending to AI orchestrator...")
            result = await orchestrator.process_user_message(
                user_id=message.from_user.id,
                message=message.text,
                user_role=user_role,
                telegram_user=message.from_user
            )
            
            logger.info("="*80)
            logger.info(f"🤖 AI RESPONSE")
            logger.info(f"   Response: {result.get('text_response', 'N/A')[:200]}")
            logger.info(f"   Action: {result.get('action_executed', 'None')}")
            logger.info(f"   Language: {result.get('language', 'N/A')}")
            logger.info(f"   Confirmation: {result.get('requires_confirmation', False)}")
            logger.info("="*80)
            
            # Отправляем ответ
            response_text = result["text_response"]
            await message.answer(
                response_text,
                parse_mode=None  # Отключаем парсинг, чтобы AI мог использовать любые символы
            )
            
            logger.info(f"✅ Response sent to user {user_id}")
            
            # Если требуется подтверждение - добавляем кнопки
            if result.get("requires_confirmation"):
                # Можно добавить inline кнопки "Подтвердить" / "Отменить"
                pass
            
        except Exception as e:
            logger.error("="*80)
            logger.error(f"❌ ERROR processing message")
            logger.error(f"   User: {user_id}")
            logger.error(f"   Message: {message_text}")
            logger.error(f"   Error: {str(e)}")
            logger.exception("Full traceback:")
            logger.error("="*80)
            
            # Последняя попытка - прямой fallback ответ
            try:
                logger.info("🔄 Trying fallback response...")
                engine = get_ai_engine()
                result = engine._fallback_response(message.text, user_role, "ru")
                fallback_text = result.get("response", "Извините, произошла ошибка.")
                
                logger.info(f"💬 Fallback response: {fallback_text[:100]}")
                await message.answer(fallback_text, parse_mode=None)
                logger.info("✅ Fallback response sent")
                return
            except Exception as fallback_error:
                logger.error(f"❌ Even fallback failed: {fallback_error}")
            
            error_messages = {
                "ru": "Извините, произошла ошибка. Попробуйте переформулировать запрос или напишите /help",
                "en": "Sorry, an error occurred. Try rephrasing or type /help",
                "he": "סליחה, אירעה שגיאה. נסה לנסח מחדש או כתוב /help"
            }
            
            lang_code = message.from_user.language_code or "en"
            if lang_code.startswith("ru"):
                error_msg = error_messages["ru"]
            elif lang_code.startswith("he"):
                error_msg = error_messages["he"]
            else:
                error_msg = error_messages["en"]
            
            await message.answer(error_msg)
    
    @router.message(F.photo | F.document)
    async def handle_media(message: types.Message):
        """Обработка фото и документов (референсы татуировок)"""
        try:
            orchestrator = get_ai_orchestrator()
            user_role = determine_user_role(message.from_user.id, admin_ids)
            
            # Создаём текстовое сообщение для AI
            media_message = "Пользователь отправил изображение (возможно референс татуировки)"
            if message.caption:
                media_message += f": {message.caption}"
            
            result = await orchestrator.process_user_message(
                user_id=message.from_user.id,
                message=media_message,
                user_role=user_role,
                telegram_user=message.from_user
            )
            
            # Отправляем ответ
            reference_response = {
                "ru": "Отличный референс! 📸 Сохранил. Давайте обсудим детали: размер, расположение, когда хотите сделать?",
                "en": "Great reference! 📸 Saved. Let's discuss the details: size, placement, when would you like to do it?",
                "he": "התמונה שמורה! 📸 בואו נדבר על הפרטים: גודל, מיקום, מתי תרצה לעשות?"
            }
            
            lang = result.get("language", "ru")
            response_text = reference_response.get(lang, reference_response["en"])
            
            await message.answer(response_text + "\n\n" + result["text_response"])
            
        except Exception as e:
            logger.exception(f"Error handling media: {e}")
            await message.answer("✅ Изображение получено! Расскажите подробнее что хотите.")
    
    return router


def setup(dp):
    """Регистрация AI router"""
    router = create_ai_router()
    dp.include_router(router)
    logger.info("✅ AI Handler registered")


# Export
__all__ = ["create_ai_router", "setup"]
