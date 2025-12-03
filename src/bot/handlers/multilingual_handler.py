"""
Multilingual Natural Language Handler
Uses INKA AI to understand any text message in Russian, English, or Hebrew
Automatically detects language and routes accordingly
"""

import logging
from typing import Optional, Dict
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter

from src.services.inka_ai import INKA
from src.utils.i18n import i18n, LANG_RU, LANG_EN, LANG_HE
from src.bot.keyboards.common_kb import main_menu, language_selection_kb
from src.services.language_service import get_language_service
from src.config.config import Config
from src.config.env_loader import load_env

logger = logging.getLogger(__name__)

# Global INKA instance
_inka_instance: Optional[INKA] = None


def get_inka() -> INKA:
    """Get or initialize INKA instance"""
    global _inka_instance
    if _inka_instance is None:
        try:
            load_env()
            cfg = Config.from_env()
            _inka_instance = INKA(api_key=cfg.OPENAI_API_KEY)
            logger.info("✅ INKA AI initialized for multilingual mode")
        except Exception as e:
            logger.error(f"Failed to initialize INKA: {e}")
            _inka_instance = INKA(api_key=None)
    return _inka_instance


class MultilingualStates(StatesGroup):
    """States for multilingual conversation flow"""
    waiting_for_language = State()
    in_conversation = State()


async def get_user_language(user_id: int) -> str:
    """Get user language or default"""
    try:
        lang_service = get_language_service()
        language = lang_service.get_user_language(user_id)
        return language if language in [LANG_RU, LANG_EN, LANG_HE] else LANG_RU
    except Exception as e:
        logger.debug(f"Could not get language from DB: {e}")
        return i18n.get_user_language(user_id)


async def set_user_language(user_id: int, language: str) -> bool:
    """Set user language in both i18n and database"""
    i18n.set_user_language(user_id, language)
    try:
        lang_service = get_language_service()
        return lang_service.set_user_language(user_id, language)
    except Exception as e:
        logger.warning(f"Could not save language to DB: {e}")
        return True  # Still successful in-memory


def create_multilingual_router() -> Router:
    """Create router with multilingual message handling"""
    router = Router()

    @router.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        """Start - ask for language if not set"""
        user_id = message.from_user.id
        user_language = await get_user_language(user_id)

        # If language not set, ask to select
        if user_language == LANG_RU and user_id not in i18n.user_languages:
            await message.answer(
                "🌐 Select your language / Выберите язык / בחר שפה",
                reply_markup=language_selection_kb()
            )
            await state.set_state(MultilingualStates.waiting_for_language)
            return

        # Show welcome in user's language
        welcome_msgs = {
            LANG_RU: "🎨 Добро пожаловать в студию тату!\n\nПиши на русском языке - я тебя пойму 😊",
            LANG_EN: "🎨 Welcome to our Tattoo Studio!\n\nWrite in English - I'll understand you 😊",
            LANG_HE: "🎨 ברוכים הבאים לסטודיו הטטו שלנו!\n\nכתוב בעברית - אני אבין אותך 😊"
        }
        welcome = welcome_msgs.get(user_language, welcome_msgs[LANG_RU])
        await message.answer(welcome, reply_markup=main_menu(user_language))
        await state.set_state(MultilingualStates.in_conversation)

    @router.message(MultilingualStates.waiting_for_language)
    async def process_language_selection(message: types.Message, state: FSMContext):
        """Process language selection"""
        text = message.text
        lang_map = {
            "🇷🇺 Русский": LANG_RU,
            "🇬🇧 English": LANG_EN,
            "🇮🇱 עברית": LANG_HE,
        }

        if text not in lang_map:
            await message.answer(
                "❌ Пожалуйста, выберите из кнопок / Please select from buttons / בחר מהכפתורים"
            )
            return

        language = lang_map[text]
        await set_user_language(message.from_user.id, language)

        confirmations = {
            LANG_RU: "✅ Язык установлен на Русский",
            LANG_EN: "✅ Language set to English",
            LANG_HE: "✅ השפה הוגדרה לעברית",
        }

        await message.answer(
            confirmations[language],
            reply_markup=main_menu(language)
        )
        await state.set_state(MultilingualStates.in_conversation)

    @router.message(Command("language"))
    async def cmd_change_language(message: types.Message, state: FSMContext):
        """Change language"""
        await message.answer(
            "🌐 Select your language / Выберите язык / בחר שפה",
            reply_markup=language_selection_kb()
        )
        await state.set_state(MultilingualStates.waiting_for_language)

    @router.message(
        MultilingualStates.in_conversation,
        F.text.in_(["❌ Отмена", "❌ Cancel", "❌ ביטול"])
    )
    async def handle_cancel(message: types.Message, state: FSMContext):
        """Handle cancel in any language"""
        user_language = await get_user_language(message.from_user.id)
        cancel_msgs = {
            LANG_RU: "❌ Отменено",
            LANG_EN: "❌ Cancelled",
            LANG_HE: "❌ בוטל",
        }
        await message.answer(cancel_msgs[user_language], reply_markup=main_menu(user_language))

    @router.message(
        MultilingualStates.in_conversation,
        F.text.in_(["🌐 Язык", "🌐 Language", "🌐 שפה"])
    )
    async def handle_language_button(message: types.Message, state: FSMContext):
        """Handle language button"""
        await message.answer(
            "🌐 Select your language / Выберите язык / בחר שפה",
            reply_markup=language_selection_kb()
        )
        await state.set_state(MultilingualStates.waiting_for_language)

    @router.message(StateFilter(None))
    @router.message(MultilingualStates.in_conversation)
    async def handle_natural_text(message: types.Message, state: FSMContext):
        """
        Handle any natural text message
        Uses INKA to understand intent and respond appropriately
        """
        user_id = message.from_user.id
        user_language = await get_user_language(user_id)
        text = message.text

        # Skip system messages and buttons
        if not text or text.startswith("/"):
            return

        try:
            # Show "typing" indicator
            await message.chat.action("typing")

            # Get INKA processing
            inka = get_inka()
            result = inka.process(
                message=text,
                client_context={
                    "user_id": user_id,
                    "has_active_booking": False,
                    "client_status": "active"
                }
            )

            # Log classification
            classification = result["classification"]
            logger.info(
                f"[{user_id}] Message: '{text[:50]}...' | "
                f"Route: {classification['route']} | "
                f"Type: {classification['booking_type']} | "
                f"Confidence: {classification['confidence']:.1%}"
            )

            # Get response
            response = result["response"]

            # Determine keyboard based on next action
            next_action = result["next_action"]

            keyboard = None
            if next_action == "offer_slots":
                keyboard = main_menu(user_language)
            elif next_action in ["continue_consultation", "other"]:
                keyboard = main_menu(user_language)
            else:
                keyboard = main_menu(user_language)

            # Send response with appropriate keyboard
            await message.answer(response, reply_markup=keyboard)

            # Set state to in_conversation to continue
            await state.set_state(MultilingualStates.in_conversation)

        except Exception as e:
            logger.exception(f"Error processing message from {user_id}: {e}")

            error_msgs = {
                LANG_RU: "❌ Ошибка обработки сообщения. Пожалуйста, попробуйте еще раз.",
                LANG_EN: "❌ Error processing message. Please try again.",
                LANG_HE: "❌ שגיאה בעיבוד ההודעה. אנא נסה שוב.",
            }

            await message.answer(
                error_msgs.get(user_language, error_msgs[LANG_RU]),
                reply_markup=main_menu(user_language)
            )

    return router


def setup(dp):
    """Register multilingual router"""
    router = create_multilingual_router()
    dp.include_router(router)


__all__ = ["setup", "create_multilingual_router", "get_inka"]
