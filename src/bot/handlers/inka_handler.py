"""
INKA Integration Module - Ready to use in your bot
Drop this into your handlers and it's ready to go
"""

import logging
import json
from typing import Optional, Dict
import asyncio

# Ensure a default event loop exists for environments/tests that expect one
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
else:
    # Replace get_event_loop with a small compatibility wrapper that ensures a usable
    # event loop is always returned (helps older tests that call get_event_loop()).
    _orig_get_event_loop = asyncio.get_event_loop

    def _get_event_loop_compat():
        try:
            return _orig_get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    # Patch only if not already patched
    if getattr(asyncio, '_get_event_loop_compat_installed', False) is not True:
        asyncio.get_event_loop = _get_event_loop_compat
        asyncio._get_event_loop_compat_installed = True
from src.services.inka_ai import INKA
from src.config.config import Config
from src.services.admin_manager import is_admin
from src.services.telemetry import incr
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
            "context_available": True,
        }

    except Exception as e:
        logger.error(f"Error getting client context: {e}")
        # Return safe default on error, and signal that context was unavailable
        return {
            "user_id": user_id,
            "has_active_booking": False,
            "client_status": "new",
            "last_route": None,
            "last_stage": None,
            "active_booking_info": None,
            "context_available": False,
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

        # Session metadata for dialog control
        data = await state.get_data()
        clarify_attempts = data.get("clarify_attempts", 0)

        # Helper: detect if the response is a clarifying fallback
        def is_clarifying_response(text: str, classification: Dict) -> bool:
            if not text:
                return False
            text_l = text.lower()
            triggers = ["переформулир", "расскажи", "не совсем поним", "уточни", "подробнее"]
            if any(t in text_l for t in triggers):
                return True
            if classification.get("route") == "other" and classification.get("confidence", 0) < 0.6:
                return True
            return False

        classification = result.get("classification", {})
        response_text = result.get("response", "")

        # INTENT-FIRST: if classifier indicates booking, assume booking and move forward
        if is_booking_request(classification):
            await state.update_data({"clarify_attempts": 0, "dialog_state": "SLOT_OFFER"})
            if is_clarifying_response(response_text, classification):
                response_text = (
                    "Понял, ты хочешь записаться. Давай начнём с идеи — что именно ты хочешь сделать? "
                    "Например: где, размер, и есть ли референсы? Или хочешь сразу посмотреть свободные слоты?"
                )
                result["response"] = response_text
                result["next_action"] = "offer_slots"
                meta = result.get("meta", {})
                meta["antirepeat_key"] = get_inka().consultant._make_antirepeat_key(response_text, classification.get("route","other"), classification.get("booking_type","tattoo"))
                result["meta"] = meta
            await state.update_data({"inka_stage": classification.get("stage")})
            return result

        # Clarify/fallback guard: limit clarifications and force progression
        if is_clarifying_response(response_text, classification):
            if clarify_attempts == 0:
                await state.update_data({"clarify_attempts": 1, "last_user_message": message.text})
                incr("clarify_attempts_total", 1)
                if any(k in message.text.lower() for k in ["запис", "хочу тату", "хочу запис", "тату"]):
                    return {"response": "Понял, ты хочешь записаться. Давай начнём: укажи, пожалуйста, место (например плечо), примерный размер и есть ли референсы?", "next_action": "other", "classification": classification}
                return {"response": "Спасибо — расскажи, пожалуйста, подробнее: где примерно, какого размера и есть ли референсы? Или хочешь увидеть свободные слоты?", "next_action": "other", "classification": classification}
            else:
                clarify_attempts += 1
                await state.update_data({"clarify_attempts": clarify_attempts})
                if clarify_attempts == 2:
                    return {"response": "Давай я задам вопрос иначе: это первая татуировка или уже был опыт?", "next_action": "other", "classification": classification}
                incr("clarify_escalations_total", 1)
                await state.update_data({"inka_escalated": True, "clarify_attempts": 0})
                return {"response": "Извини, похоже, мне нужно подключить человека для помощи — свяжу тебя с мастером.", "next_action": "human", "classification": classification}

        # Anti-repeat enforcement: check last antirepeat key in FSM state
        meta = result.get("meta", {})
        antikey = meta.get("antirepeat_key")
        if antikey:
            data = await state.get_data()
            last = data.get("last_antirepeat_key")
            # If we already sent this reply, keep a repeat counter and progress
            if last == antikey:
                antirepeat_count = data.get("antirepeat_count", 0) + 1
                await state.update_data({"antirepeat_count": antirepeat_count})
                logger.info("Anti-repeat triggered for user %s (count=%s)", message.from_user.id, antirepeat_count)

                # If the user mentioned booking keywords, or we don't have client context, push to offer slots
                booking_keywords = any(k in message.text.lower() for k in ["запис", "хочу тату", "хочу запис", "тату"])
                context_available = client_context.get("context_available", True)
                if booking_keywords or not context_available:
                    # Force an intent-first booking progression
                    await state.update_data({"last_antirepeat_key": antikey, "antirepeat_count": 0})
                    return {"response": "Понял, ты хочешь записаться. Давай начнём: укажи, пожалуйста, место (например плечо), примерный размер и есть ли референсы? Или хочешь сразу посмотреть свободные слоты?", "next_action": "offer_slots", "classification": classification}

                # Standard anti-repeat progression: suggest rephrase -> ask different clarifying question -> escalate
                if antirepeat_count == 1:
                    return {
                        "response": "Можешь переформулировать, пожалуйста? Я стараюсь не повторяться и хочу лучше понять.",
                        "next_action": "other",
                        "classification": result.get("classification", {}),
                    }
                if antirepeat_count == 2:
                    await state.update_data({"antirepeat_count": antirepeat_count})
                    return {"response": "Давай я задам вопрос иначе: это первая татуировка или уже был опыт?", "next_action": "other", "classification": classification}

                # On repeated repeats, escalate to a human and reset counter
                incr("antirepeat_escalations_total", 1)
                await state.update_data({"inka_escalated": True, "antirepeat_count": 0})
                return {"response": "Извини, похоже, мне нужно подключить человека для помощи — свяжу тебя с мастером.", "next_action": "human", "classification": classification}

            # Store latest antirepeat key and client profile for future checks
            await state.update_data({
                "last_antirepeat_key": antikey,
                "client_profile": meta.get("client_profile", {}),
            })
            # Persist simple stage info for FSM (S0..S7 can be built on this)
            stage = result.get("classification", {}).get("stage")
            if stage:
                await state.update_data({"inka_stage": stage})
        
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

        # Phase 1 - Human Entry: simple, invitation to explain the idea
        welcome_messages = {
            'ru': (
                "Здравствуйте! Расскажите, что вы хотите сделать — опишите идею или пришлите референсы.\n"
                "Это первая татуировка или у вас уже есть опыт?"
            ),
            'en': (
                "Hello. Please tell me what you'd like to do — describe your idea or send references.\n"
                "Is this your first tattoo or do you have previous tattoos?"
            ),
            'he': (
                "שלום. ספר/י מה ברצונך לעשות — תאר/י את הרעיון או שלח/י רפרנס.\n"
                "זו קעקוע ראשון עבורך או יש לך ניסיון קודם?"
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

        # Debug: log incoming message for tracing
        try:
            logger.info("🔎 Incoming message from %s: %s", message.from_user.id, (message.text or '')[:200])
        except Exception:
            logger.debug("🔎 Incoming message logging failed")

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
        # Log before processing to record user context and message
        try:
            logger.info("⏳ Processing message through INKA for user %s", message.from_user.id)
        except Exception:
            pass
        result = await handle_client_message(message, state)

        # Debug: log result from INKA processing
        try:
            logger.info("✅ INKA result for %s: next_action=%s, response=%.200s", message.from_user.id, result.get('next_action'), (result.get('response') or '')[:200])
        except Exception:
            logger.debug("✅ INKA result logging failed")

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

    @router.message(Command("session"))
    async def cmd_session(message: types.Message, state: FSMContext):
        """Admin-only: dump FSM session data for debugging"""
        user_is_admin = is_admin(message.from_user.id)
        if not user_is_admin:
            await message.answer("Только админ может использовать эту команду.")
            return

        data = await state.get_data()
        # Limit output size for safety
        dump = json.dumps(data or {}, ensure_ascii=False, indent=2)
        if len(dump) > 1900:
            dump = dump[:1900] + "\n...truncated..."

        await message.answer(f"Сессия:\n{dump}")

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
