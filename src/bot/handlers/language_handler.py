"""Language selection handler"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from src.utils.i18n import i18n, LANG_RU, LANG_EN, LANG_HE
from src.services.language_service import get_language_service
from src.bot.keyboards.common_kb import main_menu

import logging

logger = logging.getLogger(__name__)


class LanguageStates(StatesGroup):
    """FSM states for language selection"""
    selecting_language = State()


def setup(dp):
    """Register language handlers"""
    router = Router()
    
    @router.message(Command("language"))
    @router.message(F.text.in_(["🌐 Language", "🌐 Язык", "🌐 שפה"]))
    async def cmd_select_language(message: Message, state: FSMContext):
        """Start language selection"""
        await state.set_state(LanguageStates.selecting_language)
        
        # Create language buttons
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🇷🇺 Русский")],
                [KeyboardButton(text="🇬🇧 English")],
                [KeyboardButton(text="🇮🇱 עברית")],
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            "🌐 Select your language / Выберите язык / בחר שפה",
            reply_markup=kb
        )

    @router.message(LanguageStates.selecting_language)
    async def process_language_selection(message: Message, state: FSMContext):
        """Process language selection"""
        text = message.text
        
        # Map button text to language code
        lang_map = {
            "🇷🇺 Русский": LANG_RU,
            "🇬🇧 English": LANG_EN,
            "🇮🇱 עברית": LANG_HE,
        }
        
        if text not in lang_map:
            await message.answer("❌ Invalid language. Please select from buttons.")
            return
        
        language = lang_map[text]
        
        # Set language for user
        i18n.set_user_language(message.from_user.id, language)
        
        # Try to save in database
        try:
            language_service = get_language_service()
            language_service.set_user_language(message.from_user.id, language)
        except Exception as e:
            logger.warning(f"Could not save language preference: {e}")
        
        # Confirmation message in selected language
        confirmations = {
            LANG_RU: "✅ Язык установлен на Русский",
            LANG_EN: "✅ Language set to English",
            LANG_HE: "✅ השפה הוגדרה לעברית",
        }
        
        await state.clear()
        await message.answer(
            confirmations.get(language, "✅ Language selected"),
            reply_markup=main_menu(language)
        )

    dp.include_router(router)


__all__ = ["setup", "LanguageStates"]
