"""Admin handlers"""
from aiogram import types, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.config.env_loader import load_env
from src.config.config import Config
from src.services.admin_manager import get_admin_ids, is_admin, grant_admin, revoke_admin
from src.db.sheets_client import SheetsClient
from src.services.admin_service import AdminService
from src.services.master_service import MasterService
from src.services.sync_service import SyncService
from src.services.admin_chat_service import AdminChatService
from src.bot.keyboards.common_kb import admin_menu, main_menu, cancel_kb
from src.utils.i18n import i18n
import logging

logger = logging.getLogger(__name__)

def get_user_lang(user_id: int) -> str:
    """Helper to get user language with fallback to Russian"""
    return i18n.get_user_language(user_id) or "ru"

class AddMasterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_calendar_id = State()
    waiting_for_specialties = State()

class AddSlotStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_master_id = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()

class AdminChatStates(StatesGroup):
    in_chat = State()

def setup(dp: Dispatcher):
    dp.message.register(cmd_admin, Command(commands=["admin"]))
    # Admin menu buttons - all languages
    dp.message.register(show_admin_menu, F.text.in_(["📊 Dashboard", "📊 Панель", "📊 לוח בקרה"]))
    dp.message.register(cmd_add_master, F.text.in_(["👨‍🎨 Add Master", "👨‍🎨 Добавить", "👨‍🎨 הוסף אמן"]))
    dp.message.register(cmd_add_slot, F.text.in_(["⏰ Add Slot", "⏰ Слот", "⏰ הוסף חריץ"]))
    dp.message.register(cmd_sync, F.text.in_(["📅 Sync Calendar", "📅 Синхро", "📅 סנכרן לוח שנה"]))
    dp.message.register(cmd_view_clients, F.text.in_(["👥 View Clients", "👥 Клиенты", "👥 צפה בלקוחות"]))
    dp.message.register(cmd_view_bookings, F.text.in_(["📋 View Bookings", "📋 Бронирования", "📋 צפה בהזמנות"]))
    dp.message.register(cmd_admin_chat, F.text.in_(["💬 Admin Chat", "💬 Чат", "💬 צ'אט מנהל"]))
    dp.message.register(cmd_chat_stats, F.text.in_(["📊 Chat Stats", "📊 Статистика", "📊 סטטיסטיקת צ'אט"]))
    dp.message.register(cmd_back_menu, F.text.in_(["🏠 Main Menu", "🏠 Главное меню", "🏠 תפריט ראשי"]))
    dp.message.register(process_admin_message, AdminChatStates.in_chat)
    dp.message.register(process_master_name, AddMasterStates.waiting_for_name)
    dp.message.register(process_calendar_id, AddMasterStates.waiting_for_calendar_id)
    dp.message.register(process_specialties, AddMasterStates.waiting_for_specialties)
    dp.message.register(process_slot_date, AddSlotStates.waiting_for_date)
    dp.message.register(process_slot_master, AddSlotStates.waiting_for_master_id)
    dp.message.register(process_slot_start, AddSlotStates.waiting_for_start_time)
    dp.message.register(process_slot_end, AddSlotStates.waiting_for_end_time)
    # Admin control commands
    dp.message.register(cmd_grant_admin, Command(commands=["grant_admin"]))
    dp.message.register(cmd_revoke_admin, Command(commands=["revoke_admin"]))

async def cmd_admin(message: types.Message):
    """Admin dashboard"""
    from src.utils.i18n import i18n
    user_lang = i18n.get_user_language(message.from_user.id) or "ru"
    
    load_env()
    cfg = Config.from_env()
    if not is_admin(message.from_user.id):
        await message.answer("❌ Not admin")
        return
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        admin = AdminService(sc, cfg.SPREADSHEET_ID)
        clients = admin.list_clients()
        masters = admin.list_masters()
        bookings = admin.list_bookings()
        msg = f"""📊 Admin Dashboard

👥 Clients: {len(clients)}
👨‍🎨 Masters: {len(masters)}
📅 Bookings: {len(bookings)}"""
    msg += "\n\n*Admin controls:*\n`/grant_admin <telegram_id>` - add admin\n`/revoke_admin <telegram_id>` - remove admin"
        await message.answer(msg, reply_markup=admin_menu(user_lang))
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:100]}")
        logger.exception("Admin error")


async def cmd_grant_admin(message: types.Message):
    """Grant admin access to another Telegram user by ID or username"""
    load_env()
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ You are not an admin")
        return

    args = message.get_args()
    if not args:
        await message.answer("Usage: /grant_admin <telegram_id>")
        return

    try:
        new_id = int(args.strip())
    except Exception:
        await message.answer("Please provide a valid Telegram numeric ID.")
        return

    success = grant_admin(new_id)
    if success:
        await message.answer(f"✅ Granted admin rights to {new_id}")
    else:
        await message.answer(f"❌ Failed to grant admin rights to {new_id}")


async def cmd_revoke_admin(message: types.Message):
    """Revoke admin access from a user"""
    load_env()
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ You are not an admin")
        return

    args = message.get_args()
    if not args:
        await message.answer("Usage: /revoke_admin <telegram_id>")
        return

    try:
        revoke_id = int(args.strip())
    except Exception:
        await message.answer("Please provide a valid Telegram numeric ID.")
        return

    success = revoke_admin(revoke_id)
    if success:
        await message.answer(f"✅ Revoked admin rights from {revoke_id}")
    else:
        await message.answer(f"❌ Failed to revoke admin rights from {revoke_id}")

async def show_admin_menu(message: types.Message):
    """Show admin menu"""
    from src.utils.i18n import i18n
    user_lang = i18n.get_user_language(message.from_user.id) or "ru"
    
    load_env()
    if message.from_user.id not in get_admin_ids():
        await message.answer("❌ Not admin")
        return
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        admin = AdminService(sc, cfg.SPREADSHEET_ID)
        clients = admin.list_clients()
        masters = admin.list_masters()
        bookings = admin.list_bookings()
        msg = f"""📊 Admin Dashboard

👥 Clients: {len(clients)}
👨‍🎨 Masters: {len(masters)}
📅 Bookings: {len(bookings)}"""
        await message.answer(msg, reply_markup=admin_menu(user_lang))
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:100]}")
        logger.exception("Admin error")

async def cmd_back_menu(message: types.Message):
    """Go back to main menu"""
    from src.utils.i18n import i18n
    user_lang = i18n.get_user_language(message.from_user.id) or "ru"
    # Admin always sees admin button
    await message.answer("🏠 Main Menu", reply_markup=main_menu(user_lang, is_admin=True))

async def cmd_view_clients(message: types.Message):
    """View all clients"""
    load_env()
    if message.from_user.id not in get_admin_ids():
        await message.answer("❌ Not admin")
        return
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        admin = AdminService(sc, cfg.SPREADSHEET_ID)
        clients = admin.list_clients()
        
        if not clients:
            await message.answer("👥 No clients yet", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
            return
        
        msg = "👥 Clients:\n\n"
        for c in clients[:20]:  # Show first 20
            msg += f"• {c.get('name')} - {c.get('phone', 'N/A')}\n"
        
        await message.answer(msg, reply_markup=admin_menu(get_user_lang(message.from_user.id)))
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))

async def cmd_view_bookings(message: types.Message):
    """View all bookings"""
    load_env()
    if message.from_user.id not in get_admin_ids():
        await message.answer("❌ Not admin")
        return
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        admin = AdminService(sc, cfg.SPREADSHEET_ID)
        bookings = admin.list_bookings()
        
        if not bookings:
            await message.answer("📋 No bookings yet", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
            return
        
        msg = "📋 Recent Bookings:\n\n"
        for b in bookings[-10:]:  # Show last 10
            status = "✅" if b.get("status") == "confirmed" else "⏳"
            msg += f"{status} {b.get('date')} {b.get('slot_start')}\n"
        
        await message.answer(msg, reply_markup=admin_menu(get_user_lang(message.from_user.id)))
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))

async def cmd_add_master(message: types.Message, state: FSMContext):
    """Start adding new master"""
    load_env()
    if not is_admin(message.from_user.id):
        await message.answer("❌ Not admin")
        return
    
    await state.set_state(AddMasterStates.waiting_for_name)
    await message.answer("👨‍🎨 Enter master name:", reply_markup=cancel_kb())

async def process_master_name(message: types.Message, state: FSMContext):
    """Process master name input"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    await state.update_data(name=message.text)
    await state.set_state(AddMasterStates.waiting_for_calendar_id)
    await message.answer("📅 Enter Google Calendar ID:", reply_markup=cancel_kb())

async def process_calendar_id(message: types.Message, state: FSMContext):
    """Process calendar ID input"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    await state.update_data(calendar_id=message.text)
    await state.set_state(AddMasterStates.waiting_for_specialties)
    await message.answer("🎨 Enter specialties (comma-separated):", reply_markup=cancel_kb())

async def process_specialties(message: types.Message, state: FSMContext):
    """Process specialties and create master"""
    load_env()
    cfg = Config.from_env()
    
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ Not admin")
        await state.clear()
        return
    
    try:
        await state.update_data(specialties=message.text)
        data = await state.get_data()
        
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        master_service = MasterService(sc, cfg.SPREADSHEET_ID)
        
        result = master_service.add_master(
            name=data.get("name"),
            calendar_id=data.get("calendar_id"),
            specialties=data.get("specialties", "")
        )
        
        await message.answer(f"✅ Master added: {result.get('name')}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        logger.exception("Add master error")
        await state.clear()

async def cmd_add_slot(message: types.Message, state: FSMContext):
    """Start adding new time slot"""
    load_env()
    cfg = Config.from_env()
    if not is_admin(message.from_user.id):
        await message.answer("❌ Not admin")
        return
    
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        admin = AdminService(sc, cfg.SPREADSHEET_ID)
        masters = admin.list_masters()
        
        if not masters:
            await message.answer("❌ No masters found. Add masters first!", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
            return
        
        # Show available masters
        master_list = "Available masters:\n" + "\n".join([f"{m.get('id')} - {m.get('name')}" for m in masters])
        await state.set_state(AddSlotStates.waiting_for_date)
        await message.answer(f"{master_list}\n\n📅 Enter date (YYYY-MM-DD):", reply_markup=cancel_kb())
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        logger.exception("Add slot error")

async def process_slot_date(message: types.Message, state: FSMContext):
    """Process slot date"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    await state.update_data(date=message.text)
    await state.set_state(AddSlotStates.waiting_for_master_id)
    await message.answer("👨‍🎨 Enter master ID:", reply_markup=cancel_kb())

async def process_slot_master(message: types.Message, state: FSMContext):
    """Process master ID"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    await state.update_data(master_id=message.text)
    await state.set_state(AddSlotStates.waiting_for_start_time)
    await message.answer("🕐 Enter start time (HH:MM):", reply_markup=cancel_kb())

async def process_slot_start(message: types.Message, state: FSMContext):
    """Process start time"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    await state.update_data(start_time=message.text)
    await state.set_state(AddSlotStates.waiting_for_end_time)
    await message.answer("🕑 Enter end time (HH:MM):", reply_markup=cancel_kb())

async def process_slot_end(message: types.Message, state: FSMContext):
    """Process end time and create slot"""
    load_env()
    cfg = Config.from_env()
    
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ Not admin")
        await state.clear()
        return
    
    try:
        await state.update_data(end_time=message.text)
        data = await state.get_data()
        
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        from src.db.repositories.calendar_repo import CalendarRepo
        calendar_repo = CalendarRepo(sc, cfg.SPREADSHEET_ID)
        
        calendar_repo.add_slot(
            date=data.get("date"),
            master_id=data.get("master_id"),
            slot_start=data.get("start_time"),
            slot_end=data.get("end_time"),
            available="yes"
        )
        
        await message.answer(f"✅ Slot added!\n📅 {data.get('date')}\n⏰ {data.get('start_time')}-{data.get('end_time')}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        logger.exception("Add slot error")
        await state.clear()

async def cmd_sync(message: types.Message):
    """Sync calendar slots from Google Calendar"""
    load_env()
    cfg = Config.from_env()
    if not is_admin(message.from_user.id):
        await message.answer("❌ Not admin")
        return
    
    try:
        await message.answer("⏳ Syncing calendar slots...")
        
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        sync_service = SyncService(sc, cfg.SPREADSHEET_ID)
        admin_service = AdminService(sc, cfg.SPREADSHEET_ID)
        
        # Get all masters with calendar IDs
        masters = admin_service.list_masters()
        synced_count = 0
        failed_count = 0
        
        for master in masters:
            if not master.get("calendar_id"):
                logger.info(f"⏭️ Master {master.get('name')} has no calendar_id, skipping")
                continue
            
            result = sync_service.sync_calendar_slots(
                master_id=master.get("id"),
                calendar_id=master.get("calendar_id"),
                days_ahead=30
            )
            
            if result.get("status") == "success":
                synced_count += 1
                logger.info(f"✅ Synced {master.get('name')}")
            else:
                failed_count += 1
                logger.error(f"❌ Failed to sync {master.get('name')}: {result.get('message')}")
        
        msg = f"""✅ Calendar Sync Complete

📅 Synced: {synced_count} master(s)
❌ Failed: {failed_count}

Slots generated for next 30 days (9 AM - 6 PM)"""
        
        await message.answer(msg, reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        logger.exception("Sync error")

# Admin Chat Handlers

async def cmd_admin_chat(message: types.Message, state: FSMContext):
    """Start admin chat"""
    load_env()
    cfg = Config.from_env()
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ Only admins can use this")
        return

    try:
        # Check if OpenAI API key is configured
        if not cfg.OPENAI_API_KEY or cfg.OPENAI_API_KEY == "sk-svcacct-":
            await message.answer(
                "⚠️ OpenAI API key not configured!\n\n"
                "Add OPENAI_API_KEY to .env file:\n"
                "OPENAI_API_KEY=sk-your-key-here"
            )
            return
        
        await state.set_state(AdminChatStates.in_chat)
        await message.answer(
            "👋 Welcome to Admin Chat!\n\n"
            "You can chat naturally about:\n"
            "• 👥 Client information\n"
            "• 👨‍🎨 Master details\n"
            "• 📅 Appointments\n"
            "• 💰 Prices and payments\n"
            "• 📋 Studio operations\n"
            "• 📊 Any other info\n\n"
            "I'll automatically categorize and save everything.\n\n"
            "Type /exit or ❌ Cancel to leave.",
            reply_markup=cancel_kb(),
        )
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)[:100]}")
        logger.exception("Admin chat init error")

async def process_admin_message(message: types.Message, state: FSMContext):
    """Process admin message with AI and save to sheets"""
    load_env()
    cfg = Config.from_env()
    
    # Handle exit commands
    if message.text in ["/exit", "❌ Cancel"]:
        await state.clear()
        await message.answer("👋 Chat ended. Saving all information.", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    try:
        # Safety: ensure only admins in this chat can send admin-learning commands.
        if not is_admin(message.from_user.id):
            await message.answer("⛔️ You are not an admin")
            return
        # Admin learning commands (/rule, /answer, /style, /forbid, /teach)
        if message.text and message.text.strip().startswith("/"):
            cmd, *rest = message.text.strip().split(" ", 1)
            body = rest[0] if rest else ""
            # Single-line commands support key|value with pipe separator
            if cmd.lower() in ("/rule", "/teach"):
                # parse key|value
                parts = [p.strip() for p in body.split("|", 1)]
                if len(parts) < 2:
                    await message.answer("Usage: /rule <key>|<description>")
                    return
                key, desc = parts
                from src.ai.inka_learning import get_inka_learning
                get_inka_learning().teach_rule(key, desc)
                # Audit record
                from src.ai.inka_learning import log_admin_event
                log_admin_event(message.from_user.username or str(message.from_user.id), f"teach rule {key}")
                await message.answer(f"✅ Rule added: {key}")
                return
            if cmd.lower() == "/answer":
                parts = [p.strip() for p in body.split("|", 1)]
                if len(parts) < 2:
                    await message.answer("Usage: /answer <question>|<answer>")
                    return
                q, a = parts
                from src.ai.inka_learning import get_inka_learning
                get_inka_learning().teach_faq(q, a)
                from src.ai.inka_learning import log_admin_event
                log_admin_event(message.from_user.username or str(message.from_user.id), f"teach faq {q}")
                await message.answer(f"✅ FAQ added for: {q}")
                return
            if cmd.lower() == "/style":
                parts = [p.strip() for p in body.split("|", 1)]
                if len(parts) < 2:
                    await message.answer("Usage: /style <key>|<value>")
                    return
                k, v = parts
                from src.ai.inka_learning import get_inka_learning
                get_inka_learning().teach_style(k, v)
                from src.ai.inka_learning import log_admin_event
                log_admin_event(message.from_user.username or str(message.from_user.id), f"teach style {k}")
                await message.answer(f"✅ Style setting saved: {k}")
                return
            if cmd.lower() in ("/forbid", "/forbidden"):
                parts = [p.strip() for p in body.split("|", 1)]
                if len(parts) < 2:
                    await message.answer("Usage: /forbid <key>|<description>")
                    return
                k, desc = parts
                from src.ai.inka_learning import get_inka_learning
                get_inka_learning().forbid_behavior(k, desc)
                from src.ai.inka_learning import log_admin_event
                log_admin_event(message.from_user.username or str(message.from_user.id), f"forbid {k}")
                await message.answer(f"✅ Forbidden behavior recorded: {k}")
                return
            if cmd.lower() == "/show_learning":
                from src.ai.inka_learning import get_inka_learning
                dom = get_inka_learning()
                rules = dom.list("rules")
                faq = dom.list("faq")
                style = dom.list("style")
                forbidden = dom.list("forbidden")
                resp = f"Rules: {len(rules)}, FAQ: {len(faq)}, Style: {len(style)}, Forbidden: {len(forbidden)}"
                await message.answer(resp)
                return

        # Otherwise, proceed with admin chat processing below
        # Show thinking indicator
        thinking_msg = await message.answer("🤔 Processing your message...")

        # Initialize services with Cloud SQL repo
        from src.bot.entrypoint import get_admin_messages_repo
        repo = get_admin_messages_repo()
        admin_chat_service = AdminChatService(cfg.OPENAI_API_KEY, repo=repo)

        # Process message with AI
        result = admin_chat_service.process_message(
            message.from_user.id, message.text, message.from_user.id
        )

        # Save message to database
        if result and repo:
            username = message.from_user.username or message.from_user.full_name
            category = result["categories"][0] if result["categories"] else "Other"
            admin_chat_service.save_message(
                user_id=message.from_user.id,
                username=username,
                message=message.text,
                category=category,
                data=result.get("extracted_data", {}),
                inka_category=""
            )

        # Build response message with categorization
        categories_emoji = {
            "Client Information": "👥",
            "Master Information": "👨‍🎨",
            "Appointment Details": "📅",
            "Financial Information": "💰",
            "Studio Operations": "📋",
            "Marketing & Feedback": "📊",
            "Technical Issues": "⚠️",
            "Other Notes": "📝",
        }

        categories_text = " ".join(
            [
                f"{categories_emoji.get(cat, '•')} {cat}"
                for cat in result["categories"]
            ]
        )

        # Send AI response with categorization
        response_text = (
            f"✅ *Saved*\n\n"
            f"📂 Categories:\n{categories_text}\n\n"
            f"💬 Response:\n{result['ai_response']}\n\n"
            f"💾 Saved"
        )

        await thinking_msg.delete()
        await message.answer(response_text, parse_mode="Markdown", reply_markup=cancel_kb())

    except Exception as e:
        await message.answer(
            f"❌ Error: {str(e)[:150]}\n\n"
            "Make sure OPENAI_API_KEY is set in .env and valid."
        )
        logger.exception("Admin message processing error")

async def cmd_chat_stats(message: types.Message):
    """Show admin chat statistics"""
    load_env()
    cfg = Config.from_env()
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ Only admins can use this")
        return

    try:
        # Simple stats message
        stats_text = (
            f"📊 *Admin Chat Statistics*\n\n"
            f"✅ Chat system is active\n"
            f"📝 Messages are processed by ChatGPT\n"
            f"💾 All data is saved for admin\n\n"
            f"Use Admin Chat to manage:\n"
            f"• Client information\n"
            f"• Master details\n"
            f"• Pricing\n"
            f"• Schedule"
        )

        await message.answer(stats_text, parse_mode="Markdown", reply_markup=admin_menu(get_user_lang(message.from_user.id)))

    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        logger.exception("Chat stats error")