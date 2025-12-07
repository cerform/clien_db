"""
Admin Panel - Text Commands Only
Админ-панель только с текстовыми командами, без кнопок меню
"""

import logging
from typing import Optional, Dict, Any
from aiogram import Router, types, F
from aiogram.filters import Command
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
    master_name = State()
    master_phone = State()
    master_specialization = State()
    adding_training = State()
    training_category = State()
    training_input = State()
    training_response = State()


router = Router()


class AdminMenuHandler:
    """Обработчик админ-меню (только текстовые команды)"""
    
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
        
        help_text = (
            "🔐 *АДМИН-ПАНЕЛЬ* (только текстовые команды)\n\n"
            "📊 /stats - Статистика БД\n"
            "👥 /masters - Управление мастерами\n"
            "💼 /services - Управление услугами\n"
            "👤 /clients - Управление клиентами\n"
            "📅 /schedule - Управление расписанием\n"
            "🧠 /train - Обучение ИНКИ\n"
            "📈 /train_stats - Статистика обучения\n"
            "❌ /cancel - Отмена текущей операции"
        )
        
        await message.reply_text(help_text, parse_mode="Markdown")
    
    # ============ СТАТИСТИКА ============
    
    async def show_stats(self, message: types.Message, state: FSMContext):
        """Показать статистику"""
        await state.clear()
        
        stats = self.db.get_stats()
        
        if "error" in stats:
            await message.reply_text(f"❌ Ошибка: {stats['error']}")
            return
        
        text = (
            "📊 *Статистика БД*\n\n"
            f"👥 Мастеров: {stats.get('total_masters', 0)}\n"
            f"💼 Услуг: {stats.get('total_services', 0)}\n"
            f"👤 Клиентов: {stats.get('total_clients', 0)}\n"
            f"📝 Записей: {stats.get('total_bookings', 0)}\n"
            f"\n🕐 Обновлено: {stats.get('timestamp', 'N/A')[:10]}"
        )
        
        await message.reply_text(text, parse_mode="Markdown")
    
    # ============ МАСТЕРА ============
    
    async def manage_masters(self, message: types.Message, state: FSMContext):
        """Управление мастерами"""
        await state.clear()
        
        masters_list = self.db.get_masters_list()
        
        if "error" in masters_list:
            await message.reply_text(f"❌ Ошибка: {masters_list['error']}")
            return
        
        text = "👥 *Мастера*\n\n"
        for master in masters_list.get('masters', []):
            text += (
                f"*{master.get('name', 'N/A')}*\n"
                f"  Специальность: {master.get('specialization', 'N/A')}\n"
                f"  Рейтинг: {master.get('rating', 'N/A')}\n"
                f"  Статус: {master.get('status', 'N/A')}\n\n"
            )
        
        text += (
            "\n*Команды:*\n"
            "/add_master - добавить мастера\n"
            "/admin - главное меню"
        )
        
        await message.reply_text(text or "Мастеров не найдено", parse_mode="Markdown")
    
    async def add_master_start(self, message: types.Message, state: FSMContext):
        """Начать процесс добавления мастера"""
        await state.set_state(AdminStates.master_name)
        await message.reply_text("✏️ Добавление нового мастера\n\nВведи имя мастера:")
    
    async def handle_master_name(self, message: types.Message, state: FSMContext):
        """Обработать имя мастера"""
        await state.update_data(master_name=message.text)
        await state.set_state(AdminStates.master_phone)
        await message.reply_text("Введи телефон (начиная с +):")
    
    async def handle_master_phone(self, message: types.Message, state: FSMContext):
        """Обработать телефон мастера"""
        if not message.text.startswith('+'):
            await message.reply_text("❌ Телефон должен начинаться с +\nПопробуй еще раз:")
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
    
    async def manage_services(self, message: types.Message, state: FSMContext):
        """Управление услугами"""
        await state.clear()
        
        services_list = self.db.get_services_list()
        
        if "error" in services_list:
            await message.reply_text(f"❌ Ошибка: {services_list['error']}")
            return
        
        text = "💼 *Услуги*\n\n"
        for service in services_list.get('services', []):
            text += (
                f"*{service.get('name', 'N/A')}*\n"
                f"  Длительность: {service.get('duration', 'N/A')} мин\n"
                f"  Цена: {service.get('price', 'N/A')} руб\n"
                f"  Статус: {service.get('status', 'N/A')}\n\n"
            )
        
        text += "\n*Команды:*\n/add_service - добавить услугу\n/admin - главное меню"
        
        await message.reply_text(text or "Услуг не найдено", parse_mode="Markdown")
    
    # ============ КЛИЕНТЫ ============
    
    async def manage_clients(self, message: types.Message, state: FSMContext):
        """Управление клиентами"""
        await state.clear()
        
        clients_list = self.db.get_clients_list()
        
        if "error" in clients_list:
            await message.reply_text(f"❌ Ошибка: {clients_list['error']}")
            return
        
        text = f"👤 *Клиенты* ({clients_list.get('total', 0)} всего)\n\n"
        for client in clients_list.get('clients', [])[:10]:
            text += (
                f"*{client.get('name', 'N/A')}*\n"
                f"  Телефон: {client.get('phone', 'N/A')}\n"
                f"  С: {str(client.get('created_at', 'N/A'))[:10]}\n\n"
            )
        
        text += "\n*Команды:*\n/add_client - добавить клиента\n/admin - главное меню"
        
        await message.reply_text(text or "Клиентов не найдено", parse_mode="Markdown")
    
    # ============ РАСПИСАНИЕ ============
    
    async def manage_schedule(self, message: types.Message, state: FSMContext):
        """Управление расписанием"""
        await state.clear()
        
        schedule = self.db.get_schedule()
        
        if "error" in schedule:
            await message.reply_text(f"❌ Ошибка: {schedule['error']}")
            return
        
        text = "📅 *Расписание*\n\n"
        days_data = {}
        for entry in schedule.get('schedule', []):
            day = entry.get('day_of_week', 'N/A')
            if day not in days_data:
                days_data[day] = []
            days_data[day].append(entry)
        
        for day, entries in sorted(days_data.items())[:7]:
            text += f"*{day}*: {len(entries)} записей\n"
        
        text += "\n*Команды:*\n/add_schedule - добавить запись\n/admin - главное меню"
        
        await message.reply_text(text, parse_mode="Markdown")
    
    # ============ ОБУЧЕНИЕ ИНКИ ============
    
    async def train_inka_menu(self, message: types.Message, state: FSMContext):
        """Меню обучения ИНКИ"""
        await state.clear()
        
        text = (
            "🧠 *Обучение ИНКИ*\n\n"
            "Ты можешь обучать ИНКУ через чат, добавляя примеры разговоров.\n\n"
            "*Команды:*\n"
            "/add_example - добавить пример обучения\n"
            "/view_examples - просмотреть примеры\n"
            "/improvements - предложения улучшений\n"
            "/admin - главное меню"
        )
        
        await message.reply_text(text, parse_mode="Markdown")
    
    async def add_training_example(self, message: types.Message, state: FSMContext):
        """Начать добавление примера обучения"""
        categories = (
            "🧠 *Выбери категорию:*\n\n"
            "greeting - приветствие\n"
            "booking - запись на услугу\n"
            "question - ответ на вопрос\n"
            "help - техническая помощь\n\n"
            "Введи категорию:"
        )
        
        await state.set_state(AdminStates.training_category)
        await message.reply_text(categories, parse_mode="Markdown")
    
    async def handle_training_category(self, message: types.Message, state: FSMContext):
        """Обработать категорию"""
        category = message.text.lower().strip()
        
        if category not in ['greeting', 'booking', 'question', 'help']:
            await message.reply_text("❌ Неизвестная категория. Введи одну из: greeting, booking, question, help")
            return
        
        await state.update_data(training_category=category)
        await state.set_state(AdminStates.training_input)
        await message.reply_text("Что написал клиент?")
    
    async def handle_training_input(self, message: types.Message, state: FSMContext):
        """Обработать ввод клиента"""
        await state.update_data(training_input=message.text)
        await state.set_state(AdminStates.training_response)
        await message.reply_text("Как должна ответить ИНКА?")
    
    async def handle_training_response(self, message: types.Message, state: FSMContext):
        """Завершить добавление примера"""
        data = await state.get_data()
        
        success, msg = self.learning.add_training_example(
            category=data.get('training_category'),
            user_input=data.get('training_input'),
            inka_response=message.text,
            tags=''
        )
        
        await message.reply_text(msg)
        await state.clear()
    
    async def view_training_examples(self, message: types.Message, state: FSMContext):
        """Показать примеры обучения"""
        await state.clear()
        
        examples = self.learning.get_training_examples()
        
        if "error" in examples:
            await message.reply_text(f"❌ Ошибка: {examples['error']}")
            return
        
        text = f"📚 *Примеры обучения* ({examples.get('total', 0)} всего)\n\n"
        for example in examples.get('examples', [])[:10]:
            text += (
                f"*{example.get('category', 'N/A')}*\n"
                f"  Ввод: {example.get('user_input', 'N/A')[:50]}...\n"
                f"  Теги: {example.get('tags', 'N/A')}\n\n"
            )
        
        text += "\n*Команды:*\n/train - меню обучения\n/admin - главное меню"
        
        await message.reply_text(text or "Примеров не найдено", parse_mode="Markdown")
    
    async def view_improvements(self, message: types.Message, state: FSMContext):
        """Показать предложения улучшений"""
        await state.clear()
        
        improvements = self.learning.get_improvement_suggestions()
        
        text = "💡 *Предложения улучшений ИНКИ*\n\n"
        if not improvements:
            text += "Улучшений не найдено ✨"
        else:
            for imp in improvements[:5]:
                text += (
                    f"❌ *{imp.get('category', 'N/A')}*\n"
                    f"  Было: {imp.get('wrong_response', 'N/A')[:50]}...\n"
                    f"  ✅ Должно быть: {imp.get('correct_response', 'N/A')[:50]}...\n\n"
                )
        
        text += "\n*Команды:*\n/train - меню обучения\n/admin - главное меню"
        
        await message.reply_text(text, parse_mode="Markdown")
    
    async def view_training_stats(self, message: types.Message, state: FSMContext):
        """Показать статистику обучения"""
        await state.clear()
        
        stats = self.learning.get_training_stats()
        
        if "error" in stats:
            await message.reply_text(f"❌ Ошибка: {stats['error']}")
            return
        
        text = (
            "📈 *Статистика обучения ИНКИ*\n\n"
            f"📚 Всего примеров: {stats.get('total_examples', 0)}\n"
            f"✅ Улучшений: {stats.get('total_improvements', 0)}\n"
            f"📊 % улучшений: {stats.get('improvement_rate', 0)}\n\n"
            f"*По категориям:*\n"
        )
        
        for category, count in stats.get('categories', {}).items():
            text += f"  • {category}: {count}\n"
        
        text += "\n*Команды:*\n/train - меню обучения\n/admin - главное меню"
        
        await message.reply_text(text, parse_mode="Markdown")
    
    async def handle_cancel(self, message: types.Message, state: FSMContext):
        """Отмена текущей операции"""
        await state.clear()
        await message.reply_text("❌ Операция отменена\n\n/admin - главное меню")


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


@router.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    """Команда /cancel"""
    if _admin_handler:
        await _admin_handler.handle_cancel(message, state)


@router.message(Command("stats"))
async def stats_command(message: types.Message, state: FSMContext):
    """Команда /stats"""
    if _admin_handler:
        await _admin_handler.show_stats(message, state)


@router.message(Command("masters"))
async def masters_command(message: types.Message, state: FSMContext):
    """Команда /masters"""
    if _admin_handler:
        await _admin_handler.manage_masters(message, state)


@router.message(Command("add_master"))
async def add_master_command(message: types.Message, state: FSMContext):
    """Команда /add_master"""
    if _admin_handler:
        await _admin_handler.add_master_start(message, state)


@router.message(AdminStates.master_name)
async def handle_master_name(message: types.Message, state: FSMContext):
    """Обработать имя мастера"""
    if _admin_handler:
        await _admin_handler.handle_master_name(message, state)


@router.message(AdminStates.master_phone)
async def handle_master_phone(message: types.Message, state: FSMContext):
    """Обработать телефон мастера"""
    if _admin_handler:
        await _admin_handler.handle_master_phone(message, state)


@router.message(AdminStates.master_specialization)
async def handle_master_specialization(message: types.Message, state: FSMContext):
    """Обработать специальность мастера"""
    if _admin_handler:
        await _admin_handler.handle_master_specialization(message, state)


@router.message(Command("services"))
async def services_command(message: types.Message, state: FSMContext):
    """Команда /services"""
    if _admin_handler:
        await _admin_handler.manage_services(message, state)


@router.message(Command("clients"))
async def clients_command(message: types.Message, state: FSMContext):
    """Команда /clients"""
    if _admin_handler:
        await _admin_handler.manage_clients(message, state)


@router.message(Command("schedule"))
async def schedule_command(message: types.Message, state: FSMContext):
    """Команда /schedule"""
    if _admin_handler:
        await _admin_handler.manage_schedule(message, state)


@router.message(Command("train"))
async def train_command(message: types.Message, state: FSMContext):
    """Команда /train"""
    if _admin_handler:
        await _admin_handler.train_inka_menu(message, state)


@router.message(Command("add_example"))
async def add_example_command(message: types.Message, state: FSMContext):
    """Команда /add_example"""
    if _admin_handler:
        await _admin_handler.add_training_example(message, state)


@router.message(AdminStates.training_category)
async def handle_training_category(message: types.Message, state: FSMContext):
    """Обработать категорию обучения"""
    if _admin_handler:
        await _admin_handler.handle_training_category(message, state)


@router.message(AdminStates.training_input)
async def handle_training_input(message: types.Message, state: FSMContext):
    """Обработать ввод клиента"""
    if _admin_handler:
        await _admin_handler.handle_training_input(message, state)


@router.message(AdminStates.training_response)
async def handle_training_response(message: types.Message, state: FSMContext):
    """Обработать ответ ИНКИ"""
    if _admin_handler:
        await _admin_handler.handle_training_response(message, state)


@router.message(Command("view_examples"))
async def view_examples_command(message: types.Message, state: FSMContext):
    """Команда /view_examples"""
    if _admin_handler:
        await _admin_handler.view_training_examples(message, state)


@router.message(Command("improvements"))
async def improvements_command(message: types.Message, state: FSMContext):
    """Команда /improvements"""
    if _admin_handler:
        await _admin_handler.view_improvements(message, state)


@router.message(Command("train_stats"))
async def train_stats_command(message: types.Message, state: FSMContext):
    """Команда /train_stats"""
    if _admin_handler:
        await _admin_handler.view_training_stats(message, state)
