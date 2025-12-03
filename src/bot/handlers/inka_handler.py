"""
INKA Integration Module - Ready to use in your bot
Drop this into your handlers and it's ready to go
"""

import logging
from typing import Optional, Dict
from src.services.inka_ai import INKA
from src.config.config import Config
from aiogram import types, Router, F
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
    Get client context from database
    
    This is a template - implement based on your database structure
    """
    # TODO: Implement your database query
    # For now, return basic structure
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
    """Create router with INKA message handling"""
    router = Router()
    
    @router.message(F.text)
    async def handle_text_message(message: types.Message, state: FSMContext):
        """Handle any text message with INKA"""
        
        # Process through INKA
        result = await handle_client_message(message, state)
        
        # Send response
        await message.answer(result["response"])
        
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
