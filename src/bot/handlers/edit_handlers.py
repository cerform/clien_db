"""
Edit handlers for clients, masters, and services
Provides CRUD operations via Telegram bot interface
"""
from aiogram import types, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.config.env_loader import load_env
from src.config.config import Config
from src.db.sheets_client import SheetsClient
from src.db.repositories.clients_repo import ClientsRepo
from src.db.repositories.masters_repo import MastersRepo
from src.db.repositories.services_repo import ServicesRepo
from src.bot.keyboards.common_kb import admin_menu, cancel_kb
from src.utils.i18n import i18n
import logging

logger = logging.getLogger(__name__)

def get_user_lang(user_id: int) -> str:
    """Helper to get user language"""
    return i18n.get_user_language(user_id) or "ru"

# ==================== FSM STATES ====================

class EditClientStates(StatesGroup):
    selecting_client = State()
    editing_field = State()
    entering_value = State()

class EditMasterStates(StatesGroup):
    selecting_master = State()
    editing_field = State()
    entering_value = State()

class EditServiceStates(StatesGroup):
    selecting_service = State()
    editing_field = State()
    entering_value = State()

# ==================== CLIENT EDITING ====================

async def cmd_edit_clients(message: types.Message, state: FSMContext):
    """Start editing clients"""
    load_env()
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ Admin only")
        return
    
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        repo = ClientsRepo(sc, cfg.SPREADSHEET_ID)
        clients = repo.list_clients()
        
        if not clients:
            await message.answer("❌ No clients found", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
            return
        
        # Show clients list with numbers
        msg = "📝 Select client to edit:\n\n"
        for idx, client in enumerate(clients[:20], 1):  # Show first 20
            name = client.get('name', 'Unknown')
            phone = client.get('phone', 'N/A')
            msg += f"{idx}. {name} - {phone}\n"
        
        msg += "\n💡 Send client number (1-{}) or /cancel".format(min(len(clients), 20))
        
        await state.set_state(EditClientStates.selecting_client)
        await state.update_data(clients=clients[:20])
        await message.answer(msg, reply_markup=cancel_kb())
        
    except Exception as e:
        logger.exception("Edit clients error")
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))

async def process_client_selection(message: types.Message, state: FSMContext):
    """Process client selection"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    try:
        client_num = int(message.text)
        data = await state.get_data()
        clients = data.get('clients', [])
        
        if client_num < 1 or client_num > len(clients):
            await message.answer(f"❌ Invalid number. Send 1-{len(clients)}")
            return
        
        selected_client = clients[client_num - 1]
        
        # Show editable fields
        msg = f"✏️ Editing: {selected_client.get('name')}\n\n"
        msg += "Select field to edit:\n"
        msg += "1. Name\n"
        msg += "2. Phone\n"
        msg += "3. Email\n"
        msg += "4. Notes\n"
        msg += "\n💡 Send field number or /cancel"
        
        await state.set_state(EditClientStates.editing_field)
        await state.update_data(selected_client=selected_client)
        await message.answer(msg, reply_markup=cancel_kb())
        
    except ValueError:
        await message.answer("❌ Send a number")

async def process_client_field(message: types.Message, state: FSMContext):
    """Process field selection"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    field_map = {
        "1": ("name", "Name"),
        "2": ("phone", "Phone"),
        "3": ("email", "Email"),
        "4": ("notes", "Notes")
    }
    
    field_info = field_map.get(message.text)
    if not field_info:
        await message.answer("❌ Invalid field. Send 1-4")
        return
    
    field_key, field_name = field_info
    await state.update_data(field_key=field_key, field_name=field_name)
    await state.set_state(EditClientStates.entering_value)
    await message.answer(f"📝 Enter new {field_name}:", reply_markup=cancel_kb())

async def process_client_value(message: types.Message, state: FSMContext):
    """Process new value and save"""
    load_env()
    cfg = Config.from_env()
    
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    try:
        data = await state.get_data()
        client = data.get('selected_client')
        field_key = data.get('field_key')
        field_name = data.get('field_name')
        new_value = message.text
        
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        repo = ClientsRepo(sc, cfg.SPREADSHEET_ID)
        
        # Update the field
        update_data = {field_key: new_value}
        success = repo.update_client(client.get('id'), update_data)
        
        if success:
            await message.answer(
                f"✅ Updated!\n{field_name}: {new_value}",
                reply_markup=admin_menu(get_user_lang(message.from_user.id))
            )
        else:
            await message.answer("❌ Update failed", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        
        await state.clear()
        
    except Exception as e:
        logger.exception("Update client error")
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        await state.clear()

# ==================== MASTER EDITING ====================

async def cmd_edit_masters(message: types.Message, state: FSMContext):
    """Start editing masters"""
    load_env()
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ Admin only")
        return
    
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        repo = MastersRepo(sc, cfg.SPREADSHEET_ID)
        masters = repo.list_masters()
        
        if not masters:
            await message.answer("❌ No masters found", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
            return
        
        msg = "📝 Select master to edit:\n\n"
        for idx, master in enumerate(masters, 1):
            name = master.get('name', 'Unknown')
            spec = master.get('specialization', 'N/A')
            msg += f"{idx}. {name} - {spec}\n"
        
        msg += f"\n💡 Send master number (1-{len(masters)}) or /cancel"
        
        await state.set_state(EditMasterStates.selecting_master)
        await state.update_data(masters=masters)
        await message.answer(msg, reply_markup=cancel_kb())
        
    except Exception as e:
        logger.exception("Edit masters error")
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))

async def process_master_selection(message: types.Message, state: FSMContext):
    """Process master selection"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    try:
        master_num = int(message.text)
        data = await state.get_data()
        masters = data.get('masters', [])
        
        if master_num < 1 or master_num > len(masters):
            await message.answer(f"❌ Invalid number. Send 1-{len(masters)}")
            return
        
        selected_master = masters[master_num - 1]
        
        msg = f"✏️ Editing: {selected_master.get('name')}\n\n"
        msg += "Select field to edit:\n"
        msg += "1. Name\n"
        msg += "2. Specialization\n"
        msg += "3. Calendar ID\n"
        msg += "4. Notes\n"
        msg += "\n💡 Send field number or /cancel"
        
        await state.set_state(EditMasterStates.editing_field)
        await state.update_data(selected_master=selected_master)
        await message.answer(msg, reply_markup=cancel_kb())
        
    except ValueError:
        await message.answer("❌ Send a number")

async def process_master_field(message: types.Message, state: FSMContext):
    """Process master field selection"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    field_map = {
        "1": ("name", "Name"),
        "2": ("specialization", "Specialization"),
        "3": ("calendar_id", "Calendar ID"),
        "4": ("notes", "Notes")
    }
    
    field_info = field_map.get(message.text)
    if not field_info:
        await message.answer("❌ Invalid field. Send 1-4")
        return
    
    field_key, field_name = field_info
    await state.update_data(field_key=field_key, field_name=field_name)
    await state.set_state(EditMasterStates.entering_value)
    await message.answer(f"📝 Enter new {field_name}:", reply_markup=cancel_kb())

async def process_master_value(message: types.Message, state: FSMContext):
    """Process master new value and save"""
    load_env()
    cfg = Config.from_env()
    
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    try:
        data = await state.get_data()
        master = data.get('selected_master')
        field_key = data.get('field_key')
        field_name = data.get('field_name')
        new_value = message.text
        
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        repo = MastersRepo(sc, cfg.SPREADSHEET_ID)
        
        update_data = {field_key: new_value}
        success = repo.update_master(master.get('id'), update_data)
        
        if success:
            await message.answer(
                f"✅ Updated!\n{field_name}: {new_value}",
                reply_markup=admin_menu(get_user_lang(message.from_user.id))
            )
        else:
            await message.answer("❌ Update failed", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        
        await state.clear()
        
    except Exception as e:
        logger.exception("Update master error")
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        await state.clear()

# ==================== SERVICE EDITING ====================

async def cmd_edit_services(message: types.Message, state: FSMContext):
    """Start editing services"""
    load_env()
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ Admin only")
        return
    
    try:
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        repo = ServicesRepo(sc, cfg.SPREADSHEET_ID)
        services = repo.list_services()
        
        if not services:
            await message.answer("❌ No services found", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
            return
        
        msg = "📝 Select service to edit:\n\n"
        for idx, service in enumerate(services, 1):
            name = service.get('name', 'Unknown')
            price_from = service.get('price_from', '0')
            price_to = service.get('price_to', '0')
            msg += f"{idx}. {name} - {price_from}-{price_to}₽\n"
        
        msg += f"\n💡 Send service number (1-{len(services)}) or /cancel"
        
        await state.set_state(EditServiceStates.selecting_service)
        await state.update_data(services=services)
        await message.answer(msg, reply_markup=cancel_kb())
        
    except Exception as e:
        logger.exception("Edit services error")
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))

async def process_service_selection(message: types.Message, state: FSMContext):
    """Process service selection"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    try:
        service_num = int(message.text)
        data = await state.get_data()
        services = data.get('services', [])
        
        if service_num < 1 or service_num > len(services):
            await message.answer(f"❌ Invalid number. Send 1-{len(services)}")
            return
        
        selected_service = services[service_num - 1]
        
        msg = f"✏️ Editing: {selected_service.get('name')}\n\n"
        msg += "Select field to edit:\n"
        msg += "1. Name\n"
        msg += "2. Description\n"
        msg += "3. Price From\n"
        msg += "4. Price To\n"
        msg += "5. Duration (minutes)\n"
        msg += "\n💡 Send field number or /cancel"
        
        await state.set_state(EditServiceStates.editing_field)
        await state.update_data(selected_service=selected_service)
        await message.answer(msg, reply_markup=cancel_kb())
        
    except ValueError:
        await message.answer("❌ Send a number")

async def process_service_field(message: types.Message, state: FSMContext):
    """Process service field selection"""
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    field_map = {
        "1": ("name", "Name"),
        "2": ("description", "Description"),
        "3": ("price_from", "Price From"),
        "4": ("price_to", "Price To"),
        "5": ("duration_min", "Duration (minutes)")
    }
    
    field_info = field_map.get(message.text)
    if not field_info:
        await message.answer("❌ Invalid field. Send 1-5")
        return
    
    field_key, field_name = field_info
    await state.update_data(field_key=field_key, field_name=field_name)
    await state.set_state(EditServiceStates.entering_value)
    await message.answer(f"📝 Enter new {field_name}:", reply_markup=cancel_kb())

async def process_service_value(message: types.Message, state: FSMContext):
    """Process service new value and save"""
    load_env()
    cfg = Config.from_env()
    
    if message.text == "❌ Cancel":
        await state.clear()
        await message.answer("❌ Cancelled", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        return
    
    try:
        data = await state.get_data()
        service = data.get('selected_service')
        field_key = data.get('field_key')
        field_name = data.get('field_name')
        new_value = message.text
        
        sc = SheetsClient(cfg.GOOGLE_CREDENTIALS_PATH, cfg.GOOGLE_TOKEN_PATH)
        repo = ServicesRepo(sc, cfg.SPREADSHEET_ID)
        
        update_data = {field_key: new_value}
        success = repo.update_service(service.get('id'), update_data)
        
        if success:
            await message.answer(
                f"✅ Updated!\n{field_name}: {new_value}",
                reply_markup=admin_menu(get_user_lang(message.from_user.id))
            )
        else:
            await message.answer("❌ Update failed", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        
        await state.clear()
        
    except Exception as e:
        logger.exception("Update service error")
        await message.answer(f"❌ Error: {str(e)[:100]}", reply_markup=admin_menu(get_user_lang(message.from_user.id)))
        await state.clear()

# ==================== SETUP ====================

def setup(dp: Dispatcher):
    """Register all edit handlers"""
    # Commands
    dp.message.register(cmd_edit_clients, F.text.in_(["✏️ Edit Clients", "✏️ Редактировать клиентов"]))
    dp.message.register(cmd_edit_masters, F.text.in_(["✏️ Edit Masters", "✏️ Редактировать мастеров"]))
    dp.message.register(cmd_edit_services, F.text.in_(["✏️ Edit Services", "✏️ Редактировать услуги"]))
    
    # Client editing FSM
    dp.message.register(process_client_selection, EditClientStates.selecting_client)
    dp.message.register(process_client_field, EditClientStates.editing_field)
    dp.message.register(process_client_value, EditClientStates.entering_value)
    
    # Master editing FSM
    dp.message.register(process_master_selection, EditMasterStates.selecting_master)
    dp.message.register(process_master_field, EditMasterStates.editing_field)
    dp.message.register(process_master_value, EditMasterStates.entering_value)
    
    # Service editing FSM
    dp.message.register(process_service_selection, EditServiceStates.selecting_service)
    dp.message.register(process_service_field, EditServiceStates.editing_field)
    dp.message.register(process_service_value, EditServiceStates.entering_value)
