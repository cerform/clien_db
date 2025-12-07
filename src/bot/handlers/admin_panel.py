"""
Admin Handlers for Aiogram
Обработчики админ-команд для управления БД и обучения ИНКИ
"""

import logging
from typing import Optional, Dict, Any
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.services.admin_db_manager import DatabaseManager, InkaLearningSystem
from src.config import get_config

logger = logging.getLogger(__name__)

# Получить admin IDs из конфига
try:
    config = get_config()
    ADMIN_IDS = [int(id_) for id_ in config.admin_ids.split(',') if id_.strip()]
except:
    ADMIN_IDS = []


class AdminStates(StatesGroup):
    """FSM states для админ-процессов"""
    adding_master = State()
    adding_service = State()
    adding_client = State()
    adding_schedule = State()
    adding_training = State()
    master_name = State()
    master_phone = State()
    master_specialization = State()
    training_category = State()
    training_input = State()
    training_response = State()


router = Router()


class AdminMenuHandler:
    """Обработчик админ-меню"""
    
    def __init__(self, db_manager: DatabaseManager, learning_system: InkaLearningSystem):
        """
        Args:
            db_manager: DatabaseManager
            learning_system: InkaLearningSystem
        """
        self.db = db_manager
        self.learning = learning_system
    
    def is_admin(self, user_id: int) -> bool:
        """Проверить является ли пользователь админом"""
        return user_id in ADMIN_IDS
    
    # ============ ГЛАВНОЕ МЕНЮ ============
    
    async def show_admin_menu(self, message: types.Message, state: FSMContext):
        """Показать главное админ-меню"""
        if not self.is_admin(message.from_user.id):
            await message.reply_text("❌ У тебя нет прав администратора")
            return
        
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton(text="👥 Мастера", callback_data="admin_masters")
            ],
            [
                InlineKeyboardButton(text="💼 Услуги", callback_data="admin_services"),
                InlineKeyboardButton(text="👤 Клиенты", callback_data="admin_clients")
            ],
            [
                InlineKeyboardButton(text="📅 Расписание", callback_data="admin_schedule"),
                InlineKeyboardButton(text="🧠 Обучить ИНКУ", callback_data="admin_train_inka")
            ],
            [
                InlineKeyboardButton(text="📈 Статистика обучения", callback_data="admin_train_stats"),
            ]
        ])
        
        await message.reply_text(
            "🔐 *Админ-Панель*\n\n"
            "Выбери что хочешь сделать:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    # ============ СТАТИСТИКА ============
    
    async def show_stats(self, query: types.CallbackQuery, state: FSMContext):
        """Показать статистику"""
        await query.answer()
        
        stats = self.db.get_stats()
        
        if "error" in stats:
            await query.message.edit_text(f"❌ Ошибка: {stats['error']}")
            return
        
        message = (
            "📊 *Статистика БД*\n\n"
            f"👥 Мастеров: {stats.get('total_masters', 0)}\n"
            f"💼 Услуг: {stats.get('total_services', 0)}\n"
            f"👤 Клиентов: {stats.get('total_clients', 0)}\n"
            f"📝 Записей: {stats.get('total_bookings', 0)}\n"
            f"\n🕐 Обновлено: {stats.get('timestamp', 'N/A')[:10]}"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.message.edit_text(message, reply_markup=keyboard, parse_mode="Markdown")
    
    # ============ МАСТЕРА ============
    
    async def manage_masters(self, query: types.CallbackQuery, state: FSMContext):
        """Управление мастерами"""
        await query.answer()
        
        masters_list = self.db.get_masters_list()
        
        if "error" in masters_list:
            await query.message.edit_text(f"❌ Ошибка: {masters_list['error']}")
            return
        
        message = "👥 *Мастера*\n\n"
        for master in masters_list.get('masters', []):
            message += (
                f"*{master.get('name', 'N/A')}*\n"
                f"  Специальность: {master.get('specialization', 'N/A')}\n"
                f"  Рейтинг: {master.get('rating', 'N/A')}\n"
                f"  Статус: {master.get('status', 'N/A')}\n\n"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить мастера", callback_data="admin_add_master")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.message.edit_text(
            message or "Мастеров не найдено",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def add_master_start(self, query: types.CallbackQuery, state: FSMContext):
        """Начать процесс добавления мастера"""
        await query.answer()
        await state.set_state(AdminStates.master_name)
        
        await query.message.edit_text(
            "✏️ *Добавление нового мастера*\n\n"
            "Введи имя мастера:"
        )
    
    async def handle_master_name(self, message: types.Message, state: FSMContext):
        """Обработать имя мастера"""
        await state.update_data(master_name=message.text)
        await state.set_state(AdminStates.master_phone)
        
        await message.reply_text("Введи телефон (начиная с +):")
    
    async def handle_master_phone(self, message: types.Message, state: FSMContext):
        """Обработать телефон мастера"""
        if not message.text.startswith('+'):
            await message.reply_text("❌ Телефон должен начинаться с +")
            return
        
        await state.update_data(master_phone=message.text)
        await state.set_state(AdminStates.master_specialization)
        
        await message.reply_text("Введи специальность:")
    
    async def handle_master_specialization(self, message: types.Message, state: FSMContext):
        """Завершить добавление мастера"""
        data = await state.get_data()
        master_data = {
            'name': data.get('master_name'),
            'phone': data.get('master_phone'),
            'specialization': message.text,
            'rating': '5',
            'experience': '0',
        }
        
        success, msg = self.db.add_master(master_data)
        await message.reply_text(msg)
        
        await state.clear()
    
    # ============ УСЛУГИ ============
    
    async def manage_services(self, query: types.CallbackQuery, state: FSMContext):
        """Управление услугами"""
        await query.answer()
        
        services_list = self.db.get_services_list()
        
        if "error" in services_list:
            await query.message.edit_text(f"❌ Ошибка: {services_list['error']}")
            return
        
        message = "💼 *Услуги*\n\n"
        for service in services_list.get('services', []):
            message += (
                f"*{service.get('name', 'N/A')}*\n"
                f"  Длительность: {service.get('duration', 'N/A')} мин\n"
                f"  Цена: {service.get('price', 'N/A')} руб\n"
                f"  Статус: {service.get('status', 'N/A')}\n\n"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить услугу", callback_data="admin_add_service")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.message.edit_text(
            message or "Услуг не найдено",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    # ============ КЛИЕНТЫ ============
    
    async def manage_clients(self, query: types.CallbackQuery, state: FSMContext):
        """Управление клиентами"""
        await query.answer()
        
        clients_list = self.db.get_clients_list()
        
        if "error" in clients_list:
            await query.message.edit_text(f"❌ Ошибка: {clients_list['error']}")
            return
        
        message = f"👤 *Клиенты* ({clients_list.get('total', 0)} всего)\n\n"
        for client in clients_list.get('clients', [])[:5]:
            message += (
                f"*{client.get('name', 'N/A')}*\n"
                f"  Телефон: {client.get('phone', 'N/A')}\n"
                f"  С: {str(client.get('created_at', 'N/A'))[:10]}\n\n"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить клиента", callback_data="admin_add_client")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.message.edit_text(
            message or "Клиентов не найдено",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    # ============ РАСПИСАНИЕ ============
    
    async def manage_schedule(self, query: types.CallbackQuery, state: FSMContext):
        """Управление расписанием"""
        await query.answer()
        
        schedule = self.db.get_schedule()
        
        if "error" in schedule:
            await query.message.edit_text(f"❌ Ошибка: {schedule['error']}")
            return
        
        message = "📅 *Расписание*\n\n"
        days_data = {}
        for entry in schedule.get('schedule', []):
            day = entry.get('day_of_week', 'N/A')
            if day not in days_data:
                days_data[day] = []
            days_data[day].append(entry)
        
        for day, entries in sorted(days_data.items())[:7]:
            message += f"*{day}*: {len(entries)} записей\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить запись", callback_data="admin_add_schedule")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.message.edit_text(
            message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    # ============ ОБУЧЕНИЕ ИНКИ ============
    
    async def train_inka_menu(self, query: types.CallbackQuery, state: FSMContext):
        """Меню обучения ИНКИ"""
        await query.answer()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить пример", callback_data="admin_add_example")],
            [InlineKeyboardButton(text="📚 Мои примеры", callback_data="admin_view_examples")],
            [InlineKeyboardButton(text="💡 Предложения улучшений", callback_data="admin_improvements")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.message.edit_text(
            "🧠 *Обучение ИНКИ*\n\n"
            "Ты можешь обучать ИНКУ через чат, добавляя примеры разговоров.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def add_training_example(self, query: types.CallbackQuery, state: FSMContext):
        """Начать добавление примера обучения"""
        await query.answer()
        await state.set_state(AdminStates.training_category)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Приветствие", callback_data="train_greeting"),
                InlineKeyboardButton(text="Запись", callback_data="train_booking")
            ],
            [
                InlineKeyboardButton(text="Вопрос", callback_data="train_question"),
                InlineKeyboardButton(text="Помощь", callback_data="train_help")
            ],
            [InlineKeyboardButton(text="Отмена", callback_data="admin_menu")]
        ])
        
        await query.message.edit_text(
            "📝 *Добавление примера обучения*\n\n"
            "Выбери категорию:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def view_training_examples(self, query: types.CallbackQuery, state: FSMContext):
        """Показать примеры обучения"""
        await query.answer()
        
        examples = self.learning.get_training_examples()
        
        if "error" in examples:
            await query.message.edit_text(f"❌ Ошибка: {examples['error']}")
            return
        
        message = f"📚 *Примеры обучения* ({examples.get('total', 0)} всего)\n\n"
        for example in examples.get('examples', [])[:5]:
            message += (
                f"*{example.get('category', 'N/A')}*\n"
                f"  Ввод: {example.get('user_input', 'N/A')[:50]}...\n"
                f"  Теги: {example.get('tags', 'N/A')}\n\n"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_train_inka")]
        ])
        
        await query.message.edit_text(
            message or "Примеров не найдено",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def view_improvements(self, query: types.CallbackQuery, state: FSMContext):
        """Показать предложения улучшений"""
        await query.answer()
        
        improvements = self.learning.get_improvement_suggestions()
        
        message = "💡 *Предложения улучшений ИНКИ*\n\n"
        if not improvements:
            message += "Улучшений не найдено ✨"
        else:
            for imp in improvements[:5]:
                message += (
                    f"❌ *{imp.get('category', 'N/A')}*\n"
                    f"  Было: {imp.get('wrong_response', 'N/A')[:50]}...\n"
                    f"  ✅ Должно быть: {imp.get('correct_response', 'N/A')[:50]}...\n\n"
                )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_train_inka")]
        ])
        
        await query.message.edit_text(
            message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def view_training_stats(self, query: types.CallbackQuery, state: FSMContext):
        """Показать статистику обучения"""
        await query.answer()
        
        stats = self.learning.get_training_stats()
        
        if "error" in stats:
            await query.message.edit_text(f"❌ Ошибка: {stats['error']}")
            return
        
        message = (
            "📈 *Статистика обучения ИНКИ*\n\n"
            f"📚 Всего примеров: {stats.get('total_examples', 0)}\n"
            f"✅ Улучшений: {stats.get('total_improvements', 0)}\n"
            f"📊 % улучшений: {stats.get('improvement_rate', 0)}\n\n"
            f"*По категориям:*\n"
        )
        
        for category, count in stats.get('categories', {}).items():
            message += f"  • {category}: {count}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.message.edit_text(
            message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def handle_back_to_menu(self, query: types.CallbackQuery, state: FSMContext):
        """Вернуться в главное меню"""
        await query.answer()
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton(text="👥 Мастера", callback_data="admin_masters")
            ],
            [
                InlineKeyboardButton(text="💼 Услуги", callback_data="admin_services"),
                InlineKeyboardButton(text="👤 Клиенты", callback_data="admin_clients")
            ],
            [
                InlineKeyboardButton(text="📅 Расписание", callback_data="admin_schedule"),
                InlineKeyboardButton(text="🧠 Обучить ИНКУ", callback_data="admin_train_inka")
            ],
            [
                InlineKeyboardButton(text="📈 Статистика обучения", callback_data="admin_train_stats"),
            ]
        ])
        
        await query.message.edit_text(
            "🔐 *Админ-Панель*\n\n"
            "Выбери что хочешь сделать:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


# Создать экземпляр обработчика (будет инициализирован в main.py)
_admin_handler: Optional[AdminMenuHandler] = None


def init_admin_handler(db_manager: DatabaseManager, learning_system: InkaLearningSystem):
    """Инициализировать админ-обработчик"""
    global _admin_handler
    _admin_handler = AdminMenuHandler(db_manager, learning_system)


# ============ РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ============

@router.message(Command("admin"))
async def admin_command(message: types.Message, state: FSMContext):
    """Команда /admin"""
    if _admin_handler:
        await _admin_handler.show_admin_menu(message, state)


@router.callback_query(F.data == "admin_menu")
async def admin_back_to_menu(query: types.CallbackQuery, state: FSMContext):
    """Вернуться в админ-меню"""
    if _admin_handler:
        await _admin_handler.handle_back_to_menu(query, state)


@router.callback_query(F.data == "admin_stats")
async def admin_stats(query: types.CallbackQuery, state: FSMContext):
    """Показать статистику"""
    if _admin_handler:
        await _admin_handler.show_stats(query, state)


@router.callback_query(F.data == "admin_masters")
async def admin_masters(query: types.CallbackQuery, state: FSMContext):
    """Управление мастерами"""
    if _admin_handler:
        await _admin_handler.manage_masters(query, state)


@router.callback_query(F.data == "admin_add_master")
async def admin_add_master(query: types.CallbackQuery, state: FSMContext):
    """Добавить мастера"""
    if _admin_handler:
        await _admin_handler.add_master_start(query, state)


@router.message(AdminStates.master_name)
async def admin_handle_master_name(message: types.Message, state: FSMContext):
    """Обработать имя мастера"""
    if _admin_handler:
        await _admin_handler.handle_master_name(message, state)


@router.message(AdminStates.master_phone)
async def admin_handle_master_phone(message: types.Message, state: FSMContext):
    """Обработать телефон мастера"""
    if _admin_handler:
        await _admin_handler.handle_master_phone(message, state)


@router.message(AdminStates.master_specialization)
async def admin_handle_master_specialization(message: types.Message, state: FSMContext):
    """Обработать специальность мастера"""
    if _admin_handler:
        await _admin_handler.handle_master_specialization(message, state)


@router.callback_query(F.data == "admin_services")
async def admin_services(query: types.CallbackQuery, state: FSMContext):
    """Управление услугами"""
    if _admin_handler:
        await _admin_handler.manage_services(query, state)


@router.callback_query(F.data == "admin_clients")
async def admin_clients(query: types.CallbackQuery, state: FSMContext):
    """Управление клиентами"""
    if _admin_handler:
        await _admin_handler.manage_clients(query, state)


@router.callback_query(F.data == "admin_schedule")
async def admin_schedule(query: types.CallbackQuery, state: FSMContext):
    """Управление расписанием"""
    if _admin_handler:
        await _admin_handler.manage_schedule(query, state)


@router.callback_query(F.data == "admin_train_inka")
async def admin_train_inka(query: types.CallbackQuery, state: FSMContext):
    """Меню обучения ИНКИ"""
    if _admin_handler:
        await _admin_handler.train_inka_menu(query, state)


@router.callback_query(F.data == "admin_add_example")
async def admin_add_example(query: types.CallbackQuery, state: FSMContext):
    """Добавить пример обучения"""
    if _admin_handler:
        await _admin_handler.add_training_example(query, state)


@router.callback_query(F.data == "admin_view_examples")
async def admin_view_examples(query: types.CallbackQuery, state: FSMContext):
    """Показать примеры обучения"""
    if _admin_handler:
        await _admin_handler.view_training_examples(query, state)


@router.callback_query(F.data == "admin_improvements")
async def admin_improvements(query: types.CallbackQuery, state: FSMContext):
    """Показать предложения улучшений"""
    if _admin_handler:
        await _admin_handler.view_improvements(query, state)


@router.callback_query(F.data == "admin_train_stats")
async def admin_train_stats(query: types.CallbackQuery, state: FSMContext):
    """Показать статистику обучения"""
    if _admin_handler:
        await _admin_handler.view_training_stats(query, state)


# ================== INKA AI КОМАНДЫ ==================

class InkaAdminStates(StatesGroup):
    """Состояния для общения с ИНКОЙ"""
    waiting_command = State()


_inka_processor = None


def get_inka_processor():
    """Получить или создать INKA процессор"""
    global _inka_processor
    if _inka_processor is None:
        try:
            from src.ai.inka import get_inka_processor
            from src.config import get_config
            config = get_config()
            _inka_processor = get_inka_processor(
                api_key=config.openai_api_key,
                assistant_id=config.openai_assistant_id
            )
        except Exception as e:
            logger.error(f"Failed to init INKA: {e}")
    return _inka_processor


@router.message(Command("inka"))
async def inka_command(message: types.Message, state: FSMContext):
    """Команда /inka - общение с ИНКОЙ для администрирования"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.reply("❌ Эта команда доступна только администраторам")
        return
    
    # Проверяем есть ли текст после команды
    command_text = message.text.replace("/inka", "").strip()
    
    if command_text:
        # Если есть текст - сразу выполняем команду
        await process_inka_command(message, command_text)
    else:
        # Если нет - показываем меню
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="inka_stats"),
                InlineKeyboardButton(text="📅 Расписание", callback_data="inka_schedule")
            ],
            [
                InlineKeyboardButton(text="💬 Свободный запрос", callback_data="inka_free")
            ]
        ])
        
        await message.reply(
            "🧠 *ИНКА - Административный ассистент*\n\n"
            "Я могу помочь с управлением салоном!\n\n"
            "Примеры команд:\n"
            "• `/inka покажи всех мастеров`\n"
            "• `/inka добавь клиента Иван +79991234567`\n"
            "• `/inka создай запись на завтра 14:00`\n"
            "• `/inka отмени запись #123`\n"
            "• `/inka какая выручка за неделю?`\n"
            "• `/inka свободные слоты у Ани на понедельник`\n\n"
            "Или выбери быстрое действие:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


async def process_inka_command(message: types.Message, command_text: str):
    """Обработать команду для ИНКИ"""
    inka = get_inka_processor()
    
    if not inka:
        await message.reply("❌ ИНКА временно недоступна")
        return
    
    # Показываем что думаем
    thinking_msg = await message.reply("🤔 Думаю...")
    
    try:
        # Выполняем админ-команду
        response = inka.admin_command(command_text, message.from_user.id)
        
        # Удаляем сообщение о процессе
        await thinking_msg.delete()
        
        # Отправляем ответ
        await message.reply(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"INKA command error: {e}")
        await thinking_msg.edit_text(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data == "inka_stats")
async def inka_quick_stats(query: types.CallbackQuery):
    """Быстрая статистика через ИНКУ"""
    await query.answer()
    
    inka = get_inka_processor()
    if not inka:
        await query.message.edit_text("❌ ИНКА недоступна")
        return
    
    stats = inka.get_quick_stats()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="inka_stats")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="inka_back")]
    ])
    
    await query.message.edit_text(stats, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data == "inka_schedule")
async def inka_today_schedule(query: types.CallbackQuery):
    """Расписание на сегодня через ИНКУ"""
    await query.answer()
    
    inka = get_inka_processor()
    if not inka:
        await query.message.edit_text("❌ ИНКА недоступна")
        return
    
    schedule = inka.get_today_schedule()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="inka_schedule")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="inka_back")]
    ])
    
    await query.message.edit_text(schedule, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data == "inka_free")
async def inka_free_command(query: types.CallbackQuery, state: FSMContext):
    """Режим свободного запроса к ИНКЕ"""
    await query.answer()
    await state.set_state(InkaAdminStates.waiting_command)
    
    await query.message.edit_text(
        "💬 *Свободный режим*\n\n"
        "Напиши любую команду на русском языке.\n"
        "Например:\n"
        "• Добавь мастера Анна, специализация тату\n"
        "• Покажи записи на завтра\n"
        "• Какой доход за последнюю неделю?\n"
        "• Отмени запись клиента Иван на 15:00\n\n"
        "Напиши /cancel для выхода",
        parse_mode="Markdown"
    )


@router.message(InkaAdminStates.waiting_command)
async def inka_handle_free_command(message: types.Message, state: FSMContext):
    """Обработать свободную команду для ИНКИ"""
    if message.text == "/cancel":
        await state.clear()
        await message.reply("Выход из режима ИНКИ")
        return
    
    await process_inka_command(message, message.text)


@router.callback_query(F.data == "inka_back")
async def inka_back(query: types.CallbackQuery, state: FSMContext):
    """Вернуться в меню ИНКИ"""
    await query.answer()
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="inka_stats"),
            InlineKeyboardButton(text="📅 Расписание", callback_data="inka_schedule")
        ],
        [
            InlineKeyboardButton(text="💬 Свободный запрос", callback_data="inka_free")
        ]
    ])
    
    await query.message.edit_text(
        "🧠 *ИНКА - Административный ассистент*\n\n"
        "Выбери действие или напиши `/inka <команда>`",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
