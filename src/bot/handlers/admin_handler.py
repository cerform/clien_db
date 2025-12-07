"""
Telegram Admin Handlers
Обработчики команд админ-меню для управления БД и обучения ИНКИ
"""

import logging
from typing import Optional
from telegram import types, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from src.services.admin_db_manager import DatabaseManager, InkaLearningSystem

logger = logging.getLogger(__name__)

ADMIN_IDS = [123456789]  # Будет загружаться из config


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
        self.user_state = {}  # Отслеживание состояния пользователя
    
    # ============ ГЛАВНОЕ МЕНЮ ============
    
    async def show_admin_menu(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать главное админ-меню"""
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ У тебя нет прав администратора")
            return
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton("👥 Мастера", callback_data="admin_masters")
            ],
            [
                InlineKeyboardButton("💼 Услуги", callback_data="admin_services"),
                InlineKeyboardButton("👤 Клиенты", callback_data="admin_clients")
            ],
            [
                InlineKeyboardButton("📅 Расписание", callback_data="admin_schedule"),
                InlineKeyboardButton("🧠 Обучить ИНКУ", callback_data="admin_train_inka")
            ],
            [
                InlineKeyboardButton("📈 Статистика обучения", callback_data="admin_train_stats"),
                InlineKeyboardButton("💾 Экспорт данных", callback_data="admin_export")
            ]
        ])
        
        await update.message.reply_text(
            "🔐 *Админ-Панель*\n\n"
            "Выбери что хочешь сделать:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    # ============ СТАТИСТИКА ============
    
    async def show_stats(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику"""
        query = update.callback_query
        await query.answer()
        
        stats = self.db.get_stats()
        
        if "error" in stats:
            await query.edit_message_text(f"❌ Ошибка: {stats['error']}")
            return
        
        message = (
            "📊 *Статистика БД*\n\n"
            f"👥 Мастеров: {stats['total_masters']}\n"
            f"💼 Услуг: {stats['total_services']}\n"
            f"👤 Клиентов: {stats['total_clients']}\n"
            f"📝 Записей: {stats['total_bookings']}\n"
            f"\n🕐 Обновлено: {stats['timestamp'][:10]}"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.edit_message_text(message, reply_markup=keyboard, parse_mode="Markdown")
    
    # ============ МАСТЕРА ============
    
    async def manage_masters(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Управление мастерами"""
        query = update.callback_query
        await query.answer()
        
        masters_list = self.db.get_masters_list()
        
        if "error" in masters_list:
            await query.edit_message_text(f"❌ Ошибка: {masters_list['error']}")
            return
        
        message = "👥 *Мастера*\n\n"
        for master in masters_list['masters']:
            message += (
                f"*{master['name']}*\n"
                f"  Специальность: {master['specialization']}\n"
                f"  Рейтинг: {master['rating']}\n"
                f"  Статус: {master['status']}\n\n"
            )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить мастера", callback_data="admin_add_master")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.edit_message_text(
            message or "Мастеров не найдено",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        self.user_state[update.effective_user.id] = "viewing_masters"
    
    async def add_master_flow(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать процесс добавления мастера"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        self.user_state[user_id] = "adding_master"
        context.user_data["master_data"] = {}
        
        await query.edit_message_text(
            "✏️ *Добавление нового мастера*\n\n"
            "Введи имя мастера:"
        )
    
    async def handle_master_input(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать ввод данных для нового мастера"""
        user_id = update.effective_user.id
        
        if self.user_state.get(user_id) != "adding_master":
            return
        
        step = context.user_data.get("master_step", 0)
        master_data = context.user_data.get("master_data", {})
        
        steps = [
            ("name", "Введи имя мастера:"),
            ("specialization", "Введи специальность:"),
            ("phone", "Введи телефон (начиная с +):"),
            ("experience", "Опыт работы (лет):"),
            ("rating", "Начальный рейтинг (0-5):"),
        ]
        
        if step < len(steps):
            field, _ = steps[step]
            master_data[field] = update.message.text
            context.user_data["master_data"] = master_data
            context.user_data["master_step"] = step + 1
            
            if step + 1 < len(steps):
                next_field, next_prompt = steps[step + 1]
                await update.message.reply_text(f"✓ Записано\n\n{next_prompt}")
            else:
                # Завершить добавление
                success, msg = self.db.add_master(master_data)
                await update.message.reply_text(msg)
                
                self.user_state[user_id] = None
                context.user_data["master_data"] = {}
                context.user_data["master_step"] = 0
    
    # ============ УСЛУГИ ============
    
    async def manage_services(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Управление услугами"""
        query = update.callback_query
        await query.answer()
        
        services_list = self.db.get_services_list()
        
        if "error" in services_list:
            await query.edit_message_text(f"❌ Ошибка: {services_list['error']}")
            return
        
        message = "💼 *Услуги*\n\n"
        for service in services_list['services']:
            message += (
                f"*{service['name']}*\n"
                f"  Длительность: {service['duration']} мин\n"
                f"  Цена: {service['price']} руб\n"
                f"  Статус: {service['status']}\n\n"
            )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить услугу", callback_data="admin_add_service")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.edit_message_text(
            message or "Услуг не найдено",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    # ============ КЛИЕНТЫ ============
    
    async def manage_clients(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Управление клиентами"""
        query = update.callback_query
        await query.answer()
        
        clients_list = self.db.get_clients_list()
        
        if "error" in clients_list:
            await query.edit_message_text(f"❌ Ошибка: {clients_list['error']}")
            return
        
        message = f"👤 *Клиенты* ({clients_list['total']} всего)\n\n"
        for client in clients_list['clients'][:5]:
            message += (
                f"*{client['name']}*\n"
                f"  Телефон: {client['phone']}\n"
                f"  С: {client['created_at'][:10]}\n\n"
            )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить клиента", callback_data="admin_add_client")],
            [InlineKeyboardButton("🔍 Поиск", callback_data="admin_search_client")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.edit_message_text(
            message or "Клиентов не найдено",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    # ============ РАСПИСАНИЕ ============
    
    async def manage_schedule(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Управление расписанием"""
        query = update.callback_query
        await query.answer()
        
        schedule = self.db.get_schedule()
        
        if "error" in schedule:
            await query.edit_message_text(f"❌ Ошибка: {schedule['error']}")
            return
        
        message = "📅 *Расписание*\n\n"
        days_data = {}
        for entry in schedule['schedule']:
            day = entry['day_of_week']
            if day not in days_data:
                days_data[day] = []
            days_data[day].append(entry)
        
        for day, entries in sorted(days_data.items())[:7]:
            message += f"*{day}*: {len(entries)} записей\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить запись", callback_data="admin_add_schedule")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    # ============ ОБУЧЕНИЕ ИНКИ ============
    
    async def train_inka_menu(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Меню обучения ИНКИ"""
        query = update.callback_query
        await query.answer()
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить пример", callback_data="admin_add_example")],
            [InlineKeyboardButton("📚 Мои примеры", callback_data="admin_view_examples")],
            [InlineKeyboardButton("💡 Предложения улучшений", callback_data="admin_improvements")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.edit_message_text(
            "🧠 *Обучение ИНКИ*\n\n"
            "Ты можешь обучать ИНКУ через чат, добавляя примеры разговоров.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def add_training_example(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Начать добавление примера обучения"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        self.user_state[user_id] = "adding_training"
        context.user_data["training_data"] = {}
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Приветствие", callback_data="train_greeting"),
                InlineKeyboardButton("Запись", callback_data="train_booking")
            ],
            [
                InlineKeyboardButton("Вопрос", callback_data="train_question"),
                InlineKeyboardButton("Техническая помощь", callback_data="train_help")
            ],
            [InlineKeyboardButton("Отмена", callback_data="admin_menu")]
        ])
        
        await query.edit_message_text(
            "📝 *Добавление примера обучения*\n\n"
            "Выбери категорию:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def view_training_examples(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать примеры обучения"""
        query = update.callback_query
        await query.answer()
        
        examples = self.learning.get_training_examples()
        
        if "error" in examples:
            await query.edit_message_text(f"❌ Ошибка: {examples['error']}")
            return
        
        message = f"📚 *Примеры обучения* ({examples['total']} всего)\n\n"
        for example in examples['examples'][:5]:
            message += (
                f"*{example['category']}*\n"
                f"  Ввод: {example['user_input'][:50]}...\n"
                f"  Теги: {example['tags']}\n\n"
            )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_train_inka")]
        ])
        
        await query.edit_message_text(
            message or "Примеров не найдено",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def view_improvements(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать предложения улучшений"""
        query = update.callback_query
        await query.answer()
        
        improvements = self.learning.get_improvement_suggestions()
        
        message = "💡 *Предложения улучшений ИНКИ*\n\n"
        if not improvements:
            message += "Улучшений не найдено ✨"
        else:
            for imp in improvements[:5]:
                message += (
                    f"❌ *{imp['category']}*\n"
                    f"  Было: {imp['wrong_response'][:50]}...\n"
                    f"  ✅ Должно быть: {imp['correct_response'][:50]}...\n\n"
                )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_train_inka")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    async def view_training_stats(self, update: types.Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику обучения"""
        query = update.callback_query
        await query.answer()
        
        stats = self.learning.get_training_stats()
        
        if "error" in stats:
            await query.edit_message_text(f"❌ Ошибка: {stats['error']}")
            return
        
        message = (
            "📈 *Статистика обучения ИНКИ*\n\n"
            f"📚 Всего примеров: {stats['total_examples']}\n"
            f"✅ Улучшений: {stats['total_improvements']}\n"
            f"📊 % улучшений: {stats['improvement_rate']}\n\n"
            f"*По категориям:*\n"
        )
        
        for category, count in stats.get('categories', {}).items():
            message += f"  • {category}: {count}\n"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Назад", callback_data="admin_menu")]
        ])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


def register_admin_handlers(dp, db_manager: DatabaseManager, learning_system: InkaLearningSystem):
    """Регистрировать все админ-обработчики"""
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
    
    handler = AdminMenuHandler(db_manager, learning_system)
    
    # Команда /admin
    dp.add_handler(CommandHandler("admin", handler.show_admin_menu))
    
    # Callback handlers
    dp.add_handler(CallbackQueryHandler(handler.show_stats, pattern="^admin_stats$"))
    dp.add_handler(CallbackQueryHandler(handler.manage_masters, pattern="^admin_masters$"))
    dp.add_handler(CallbackQueryHandler(handler.add_master_flow, pattern="^admin_add_master$"))
    dp.add_handler(CallbackQueryHandler(handler.manage_services, pattern="^admin_services$"))
    dp.add_handler(CallbackQueryHandler(handler.manage_clients, pattern="^admin_clients$"))
    dp.add_handler(CallbackQueryHandler(handler.manage_schedule, pattern="^admin_schedule$"))
    dp.add_handler(CallbackQueryHandler(handler.train_inka_menu, pattern="^admin_train_inka$"))
    dp.add_handler(CallbackQueryHandler(handler.add_training_example, pattern="^admin_add_example$"))
    dp.add_handler(CallbackQueryHandler(handler.view_training_examples, pattern="^admin_view_examples$"))
    dp.add_handler(CallbackQueryHandler(handler.view_improvements, pattern="^admin_improvements$"))
    dp.add_handler(CallbackQueryHandler(handler.view_training_stats, pattern="^admin_train_stats$"))
    
    # Обработчик текстовых сообщений для форм ввода
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_master_input))
