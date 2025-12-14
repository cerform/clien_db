"""
INKA Integration Module - Ready to use in your bot
Drop this into your handlers and it's ready to go
"""

import logging
from typing import Optional, Dict
from src.services.inka_ai import INKA
from src.config.config import Config
from src.services.admin_manager import is_admin
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

# Global INKA instance
_inka_instance: Optional[INKA] = None


def get_inka() -> INKA:
    """Get or initialize INKA instance"""
    global _inka_instance
    if _inka_instance is None:
        try:
            cfg = Config.from_env()
            _inka_instance = INKA(api_key=cfg.OPENAI_API_KEY)
            logger.info("✅ INKA AI initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize INKA: {e}")
            # Will still work with fallback rule-based responses
            _inka_instance = INKA(api_key=None)
    return _inka_instance


async def get_client_context(user_id: int, db=None) -> Dict:
    """
    Get client context from database - PRODUCTION READY
    Fetches real client data from Google Sheets
    """
    try:
        from src.config.env_loader import load_env
        from src.db.sheets_client import SheetsClient
        from src.db.repositories.clients_repo import ClientsRepo
        from src.db.repositories.bookings_repo import BookingsRepo

        load_env()
        cfg = Config.from_env()

        if not cfg.SPREADSHEET_ID:
            logger.warning("No SPREADSHEET_ID - returning default context")
            return {
                "user_id": user_id,
                "has_active_booking": False,
                "client_status": "new",
                "last_route": None,
                "last_stage": None,
                "active_booking_info": None,
            }

        # Initialize repositories
        sc = SheetsClient()
        clients_repo = ClientsRepo(sc, cfg.SPREADSHEET_ID)
        bookings_repo = BookingsRepo(sc, cfg.SPREADSHEET_ID)

        # Get client info
        clients = clients_repo.list_clients()
        client = None
        for c in clients:
            if str(c.get('telegram_id')) == str(user_id):
                client = c
                break

        # Get active bookings
        bookings = bookings_repo.list_bookings()
        active_booking = None
        has_active_booking = False

        for b in bookings:
            if str(b.get('client_telegram_id')) == str(user_id):
                status = b.get('status', '').lower()
                if status in ['pending', 'confirmed', 'active']:
                    has_active_booking = True
                    active_booking = {
                        "id": b.get('id'),
                        "date": b.get('date'),
                        "time": b.get('slot_start'),
                        "master_id": b.get('master_id'),
                        "status": status
                    }
                    break

        return {
            "user_id": user_id,
            "has_active_booking": has_active_booking,
            "client_status": "returning" if client else "new",
            "last_route": None,
            "last_stage": None,
            "active_booking_info": active_booking,
            "client_name": client.get('name') if client else None,
            "client_phone": client.get('phone') if client else None,
        }

    except Exception as e:
        logger.error(f"Error getting client context: {e}")
        # Return safe default on error
        return {
            "user_id": user_id,
            "has_active_booking": False,
            "client_status": "new",
            "last_route": None,
            "last_stage": None,
            "active_booking_info": None,
        }


async def handle_client_message(
    message: types.Message,
    state: FSMContext,
    db=None
) -> Dict:
    """
    Main handler: Process any client message through INKA
    
    Returns:
        {
            "response": text to send,
            "next_action": "offer_slots|continue_consultation|other",
            "classification": {...}
        }
    """
    inka = get_inka()
    
    try:
        # Get client context
        client_context = await get_client_context(message.from_user.id, db)
        
        # Process through INKA
        result = inka.process(message.text, client_context)
        
        # Log classification
        logger.debug(
            f"[{message.from_user.id}] Route: {result['classification']['route']}, "
            f"Type: {result['classification']['booking_type']}, "
            f"Confidence: {result['classification']['confidence']:.2f}"
        )
        
        return result
        
    except Exception as e:
        logger.exception(f"INKA processing error: {e}")
        return {
            "response": "Извините, давайте попробуем еще раз.",
            "next_action": "error",
            "classification": {"route": "error", "stage": "error"}
        }


# ============================================================================
# EXAMPLE ROUTER - Ready to use
# ============================================================================

def create_inka_router() -> Router:
    """Create router with INKA message handling - CLEAN CHAT INTERFACE"""
    router = Router()

    @router.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        """
        /start command - Clean welcome message without any keyboards
        Pure AI receptionist experience
        """
        # Clear any previous state
        await state.clear()

        # Welcome message in user's language (detect from Telegram settings)
        lang_code = message.from_user.language_code or 'ru'

        welcome_messages = {
            'ru': (
                "👋 Здравствуйте! Я AI-ассистент тату студии.\n\n"
                "Я помогу вам записаться на сеанс.\n"
                "Просто напишите мне, что хотите сделать:\n\n"
                "• Записаться на тату\n"
                "• Узнать цены\n"
                "• Задать вопрос\n"
                "• Перенести запись\n\n"
                "Пишите свободно, я вас понимаю! 😊"
            ),
            'en': (
                "👋 Hello! I'm the AI assistant of the tattoo studio.\n\n"
                "I'll help you book a session.\n"
                "Just tell me what you want to do:\n\n"
                "• Book a tattoo\n"
                "• Check prices\n"
                "• Ask a question\n"
                "• Reschedule appointment\n\n"
                "Write freely, I understand you! 😊"
            ),
            'he': (
                "👋 שלום! אני העוזר הדיגיטלי של סטודיו הקעקועים.\n\n"
                "אעזור לך להזמין תור.\n"
                "פשוט כתוב לי מה אתה רוצה לעשות:\n\n"
                "• להזמין קעקוע\n"
                "• לבדוק מחירים\n"
                "• לשאול שאלה\n"
                "• לשנות תור\n\n"
                "כתוב בחופשיות, אני מבין אותך! 😊"
            )
        }

        # Get appropriate message
        welcome = welcome_messages.get(lang_code, welcome_messages['ru'])

        # Send WITHOUT keyboard - clean chat interface
        await message.answer(
            welcome,
            reply_markup=types.ReplyKeyboardRemove()
        )

    @router.message(F.text)
    async def handle_text_message(message: types.Message, state: FSMContext):
        """Handle any text message with INKA - Pure AI Receptionist"""

        # Check if user is admin trying to access admin panel
        from src.config.config import Config
        from src.config.env_loader import load_env
        load_env()
        cfg = Config.from_env()
        user_is_admin = is_admin(message.from_user.id)

        # Admin commands should be handled by admin handlers, not INKA
        admin_triggers = ["👨‍💼 Админ", "👨‍💼 Admin", "👨‍💼 מנהל", "/admin"]
        if user_is_admin and message.text in admin_triggers:
            # Skip INKA processing for admin commands
            return

        # Process through INKA
        result = await handle_client_message(message, state)

        # Send response WITHOUT any keyboard (clean chat interface)
        # This removes all buttons and creates a pure conversational experience
        await message.answer(
            result["response"],
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Handle based on next_action
        if result["next_action"] == "offer_slots":
            # TODO: Trigger your S2 booking flow
            logger.debug(f"Ready to offer slots: {result['booking_context']}")
            # Example:
            # await offer_booking_slots(message, result["booking_context"])

        elif result["next_action"] == "error":
            logger.error(f"Error in processing: {result}")

        # else: continue_consultation - just wait for next message

    return router


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_inka_system_prompt() -> str:
    """Get the main INKA system prompt for Make.com"""
    inka = get_inka()
    return inka.consultant.get_system_prompt()


def classify_message(message: str, client_context: Optional[Dict] = None) -> Dict:
    """
    Quick classification without full processing
    
    Use this if you only need to classify, not get response
    """
    inka = get_inka()
    classifier = inka.classifier
    
    return classifier.classify(
        message=message,
        client_status=client_context.get("client_status") if client_context else None,
        has_active_booking=client_context.get("has_active_booking", False) if client_context else False,
        active_booking_info=client_context.get("active_booking_info") if client_context else None,
    )


def is_booking_request(classification: Dict) -> bool:
    """Check if classification indicates booking request"""
    return classification["route"] in [
        "booking",
        "booking_confirm", 
        "booking_reschedule"
    ]


def get_booking_type(classification: Dict) -> str:
    """Extract booking type from classification"""
    return classification.get("booking_type", "tattoo")


# ============================================================================
# DATABASE OPERATIONS - PRODUCTION READY
# ============================================================================

async def create_or_update_client(user_id: int, name: str, phone: str = "", email: str = "") -> Dict:
    """
    Create new client or update existing client in Google Sheets
    Returns client data
    """
    try:
        from src.config.env_loader import load_env
        from src.db.sheets_client import SheetsClient
        from src.db.repositories.clients_repo import ClientsRepo

        load_env()
        cfg = Config.from_env()

        if not cfg.SPREADSHEET_ID:
            logger.error("Cannot create client: No SPREADSHEET_ID")
            return None

        sc = SheetsClient()
        clients_repo = ClientsRepo(sc, cfg.SPREADSHEET_ID)

        # Check if client exists
        clients = clients_repo.list_clients()
        existing_client = None
        for c in clients:
            if str(c.get('telegram_id')) == str(user_id):
                existing_client = c
                break

        if existing_client:
            # Update existing client
            update_data = {
                'name': name or existing_client.get('name'),
                'phone': phone or existing_client.get('phone'),
                'email': email or existing_client.get('email'),
            }
            success = clients_repo.update_client(existing_client['id'], update_data)
            if success:
                logger.info(f"✅ Updated client {user_id}: {name}")
                return {**existing_client, **update_data}
        else:
            # Create new client
            new_client = clients_repo.create_client(
                telegram_id=user_id,
                name=name,
                phone=phone,
                email=email
            )
            logger.info(f"✅ Created new client {user_id}: {name}")
            return new_client

    except Exception as e:
        logger.error(f"Error creating/updating client: {e}")
        return None


async def create_booking(
    user_id: int,
    client_name: str,
    date: str,
    slot_start: str,
    slot_end: str = None,
    master_id: str = None,
    phone: str = "",
    notes: str = ""
) -> Dict:
    """
    Create a new booking in Google Sheets
    Returns booking data or None on error
    """
    try:
        from src.config.env_loader import load_env
        from src.db.sheets_client import SheetsClient
        from src.db.repositories.bookings_repo import BookingsRepo
        from src.db.repositories.masters_repo import MastersRepo

        load_env()
        cfg = Config.from_env()

        if not cfg.SPREADSHEET_ID:
            logger.error("Cannot create booking: No SPREADSHEET_ID")
            return None

        sc = SheetsClient()
        bookings_repo = BookingsRepo(sc, cfg.SPREADSHEET_ID)

        # Get default master if not specified
        if not master_id:
            masters_repo = MastersRepo(sc, cfg.SPREADSHEET_ID)
            masters = masters_repo.list_masters()
            for m in masters:
                if m.get('active') in ['yes', 'Yes', 'true', 'True', True]:
                    master_id = m.get('id')
                    break
            if not master_id and masters:
                master_id = masters[0].get('id')

        # Create booking
        new_booking = bookings_repo.create_booking(
            client_telegram_id=user_id,
            client_name=client_name,
            client_phone=phone,
            date=date,
            master_id=master_id or "default_master",
            slot_start=slot_start,
            slot_end=slot_end or slot_start,
            notes=notes
        )

        logger.info(f"✅ Created booking for user {user_id} on {date} at {slot_start}")
        return new_booking

    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        return None


async def get_available_slots(date: str = None) -> list:
    """
    Get available time slots from calendar
    Returns list of available slots
    """
    try:
        from src.config.env_loader import load_env
        from src.db.sheets_client import SheetsClient
        from src.db.repositories.calendar_repo import CalendarRepo

        load_env()
        cfg = Config.from_env()

        if not cfg.SPREADSHEET_ID:
            logger.error("Cannot get slots: No SPREADSHEET_ID")
            return []

        sc = SheetsClient()
        calendar_repo = CalendarRepo(sc, cfg.SPREADSHEET_ID)

        if date:
            # Get slots for specific date
            slots = calendar_repo.get_slots_by_date(date)
        else:
            # Get all available slots
            all_slots = calendar_repo.list_calendar()
            slots = [s for s in all_slots if s.get('available') in ['yes', 'Yes', 'true', 'True', True]]

        logger.info(f"Found {len(slots)} available slots" + (f" for {date}" if date else ""))
        return slots

    except Exception as e:
        logger.error(f"Error getting available slots: {e}")
        return []


# ============================================================================
# LOGGING UTILITIES
# ============================================================================

def log_classification(user_id: int, message: str, classification: Dict):
    """Log classification for monitoring"""
    logger.info(
        f"[User {user_id}] Message: '{message[:50]}...' | "
        f"Route: {classification['route']} | "
        f"Type: {classification['booking_type']} | "
        f"Confidence: {classification['confidence']:.2%}"
    )


def log_response(user_id: int, response: str, next_action: str):
    """Log AI response for monitoring"""
    logger.debug(
        f"[User {user_id}] Response: '{response[:100]}...' | "
        f"Next: {next_action}"
    )


# ============================================================================
# TESTING HELPERS
# ============================================================================

def test_inka_classifier():
    """Test INKA classifier with sample inputs"""
    test_cases = [
        ("хочу записаться на тату", "booking"),
        ("маленькая тату на сегодня", "booking"),
        ("идея: сова и луна", "consultation"),
        ("больно ли делать?", "info"),
        ("сколько стоит?", "info"),
        ("перенесите запись", "booking_reschedule"),
        ("привет, как дела?", "other"),
    ]
    
    inka = get_inka()
    passed = 0
    failed = 0
    
    print("\n" + "="*60)
    print("🧪 INKA CLASSIFIER TEST")
    print("="*60)
    
    for message, expected_route in test_cases:
        result = inka.classifier.classify(message)
        route = result["route"]
        confidence = result["confidence"]
        
        status = "✅" if route == expected_route else "❌"
        passed += 1 if route == expected_route else 0
        failed += 0 if route == expected_route else 1
        
        print(f"\n{status} Message: '{message}'")
        print(f"   Expected: {expected_route}")
        print(f"   Got: {route}")
        print(f"   Confidence: {confidence:.1%}")
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


def test_inka_consultant():
    """Test INKA consultant with sample inputs"""
    test_cases = [
        ("Больно ли делать тату?", "Should mention individual sensitivity"),
        ("Как ухаживать после?", "Should mention care instructions"),
        ("Сколько стоит?", "Should mention it depends on size"),
    ]
    
    inka = get_inka()
    
    print("\n" + "="*60)
    print("🧪 INKA CONSULTANT TEST (Rule-based fallback)")
    print("="*60)
    
    for message, expectation in test_cases:
        response = inka.consultant._rule_based_response(message)
        
        print(f"\n❓ Message: '{message}'")
        print(f"   Expectation: {expectation}")
        print(f"📱 Response: {response}")
    
    print("\n" + "="*60 + "\n")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'get_inka',
    'create_inka_router',
    'get_client_context',
    'handle_client_message',
    'create_or_update_client',
    'create_booking',
    'get_available_slots',
    'classify_message',
    'is_booking_request',
    'get_booking_type',
]


# ============================================================================
# COMMAND: Run tests
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    if "test" in sys.argv:
        print("\n🚀 Running INKA tests...\n")
        test_inka_classifier()
        test_inka_consultant()
        print("✅ All tests completed!")
