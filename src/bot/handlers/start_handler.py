from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging

from src.ai.advanced_inka import get_advanced_inka
from src.config import get_config
from src.db.sheets_client import GoogleSheetsClient

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command - просто передай в INKA"""
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "друг"
    
    config = get_config()
    sheets = GoogleSheetsClient(config.google_credentials_json, config.google_spreadsheet_id)
    
    inka = get_advanced_inka(
        api_key=config.openai_api_key,
        assistant_id=config.openai_assistant_id,
        sheets_client=sheets,
        calendar_service=None
    )
    
    # Инициализируем историю
    await state.update_data(conversation_history=[])
    
    # INKA сама приветствует
    greeting_text = f"привет я {user_name}, я только что пришел из рекламы"
    response = await inka.chat(greeting_text, str(user_id), [])
    
    await message.answer(response)
