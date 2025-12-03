"""
Example usage of INKA S2 Booking Engine

This file demonstrates how to use the new S2 Booking Engine module
in different scenarios.
"""

from src.services.inka_ai import INKA
from src.services.inka_booking_engine import INKABookingEngine, BookingEngineStage


def example_1_offer_slots():
    """Example 1: Offering available slots to client"""
    
    # Initialize INKA
    inka = INKA()
    
    # Simulate available slots from database
    available_slots = [
        {
            "slot_id": "S-1",
            "date": "2025-12-12",
            "start_time": "14:00",
            "end_time": "18:00",
            "available": True
        },
        {
            "slot_id": "S-2",
            "date": "2025-12-14",
            "start_time": "15:00",
            "end_time": "19:00",
            "available": True
        },
        {
            "slot_id": "S-3",
            "date": "2025-12-15",
            "start_time": "12:00",
            "end_time": "16:00",
            "available": True
        }
    ]
    
    # Process S2 booking stage: offer_slots
    result = inka.process_s2_booking(
        available_slots=available_slots,
        stage="offer_slots"
    )
    
    print("=" * 60)
    print("EXAMPLE 1: Offering Slots")
    print("=" * 60)
    print(f"Message to client:\n{result['message']}\n")
    print(f"Has slots: {result['has_slots']}")
    print(f"Slot count: {result['slot_count']}")
    print(f"Formatted slots: {result['formatted_slots']}")
    print(f"Keyboard data: {result['keyboard_data']}")
    print("=" * 60)


def example_2_no_slots():
    """Example 2: No available slots"""
    
    inka = INKA()
    
    # Empty slots
    available_slots = []
    
    result = inka.process_s2_booking(
        available_slots=available_slots,
        stage="offer_slots"
    )
    
    print("\n" + "=" * 60)
    print("EXAMPLE 2: No Available Slots")
    print("=" * 60)
    print(f"Message to client:\n{result['message']}\n")
    print(f"Has slots: {result['has_slots']}")
    print("=" * 60)


def example_3_confirm_selection():
    """Example 3: Confirming client's slot selection"""
    
    inka = INKA()
    
    # Client selected this slot
    selected_slot = {
        "slot_id": "S-1",
        "date": "2025-12-12",
        "start_time": "14:00",
        "end_time": "18:00"
    }
    
    result = inka.process_s2_booking(
        available_slots=[],  # Not needed for confirmation
        stage="confirming_choice",
        selected_slot=selected_slot,
        slot_taken=False
    )
    
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Confirming Slot Selection")
    print("=" * 60)
    print(f"Message to client:\n{result['message']}\n")
    print(f"Success: {result['success']}")
    print(f"Selected slot: {result['selected_slot']}")
    print("=" * 60)


def example_4_slot_taken():
    """Example 4: Selected slot is no longer available"""
    
    inka = INKA()
    
    selected_slot = {
        "slot_id": "S-1",
        "date": "2025-12-12",
        "start_time": "14:00",
        "end_time": "18:00"
    }
    
    result = inka.process_s2_booking(
        available_slots=[],
        stage="confirming_choice",
        selected_slot=selected_slot,
        slot_taken=True  # Slot was taken by someone else
    )
    
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Slot Already Taken")
    print("=" * 60)
    print(f"Message to client:\n{result['message']}\n")
    print(f"Success: {result['success']}")
    print("=" * 60)


def example_5_full_flow():
    """Example 5: Full S1 → S2 flow"""
    
    inka = INKA()
    
    # Step 1: S1 Classification
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Full S1 → S2 Flow")
    print("=" * 60)
    
    client_message = "Хочу записаться на маленькую тату"
    
    s1_result = inka.process(
        message=client_message,
        client_context={"client_status": "new"}
    )
    
    print(f"\nClient message: {client_message}")
    print(f"\nS1 Classification:")
    print(f"  Route: {s1_result['classification']['route']}")
    print(f"  Stage: {s1_result['classification']['stage']}")
    print(f"  Booking type: {s1_result['classification']['booking_type']}")
    print(f"  Next action: {s1_result['next_action']}")
    print(f"\nS1 Response:\n{s1_result['response']}")
    
    # Step 2: If next_action is "offer_slots", proceed to S2
    if s1_result['next_action'] == "offer_slots":
        available_slots = [
            {
                "slot_id": "S-1",
                "date": "2025-12-10",
                "start_time": "14:00",
                "end_time": "16:00",
                "available": True
            },
            {
                "slot_id": "S-2",
                "date": "2025-12-12",
                "start_time": "16:00",
                "end_time": "18:00",
                "available": True
            }
        ]
        
        s2_result = inka.process_s2_booking(
            available_slots=available_slots,
            stage="offer_slots"
        )
        
        print(f"\nS2 Response (Offering Slots):\n{s2_result['message']}")
        print(f"\nSlots offered: {s2_result['slot_count']}")
    
    print("=" * 60)


def example_6_get_system_prompts():
    """Example 6: Get system prompts for Make.com"""
    
    inka = INKA()
    prompts = inka.get_system_prompts()
    
    print("\n" + "=" * 60)
    print("EXAMPLE 6: System Prompts for Make.com")
    print("=" * 60)
    
    for key, prompt in prompts.items():
        print(f"\n{key.upper()}:")
        print("-" * 60)
        print(prompt[:200] + "..." if len(prompt) > 200 else prompt)
    
    print("=" * 60)


def example_7_validate_slot():
    """Example 7: Validate slot selection"""
    
    booking_engine = INKABookingEngine()
    
    available_slots = [
        {
            "slot_id": "S-1",
            "date": "2025-12-12",
            "start_time": "14:00",
            "end_time": "18:00",
            "available": True
        },
        {
            "slot_id": "S-2",
            "date": "2025-12-14",
            "start_time": "15:00",
            "end_time": "19:00",
            "available": False  # Not available
        }
    ]
    
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Slot Validation")
    print("=" * 60)
    
    # Valid slot
    result1 = booking_engine.validate_slot_selection("S-1", available_slots)
    print(f"\nValidating S-1: {result1['valid']} - {result1['reason']}")
    
    # Unavailable slot
    result2 = booking_engine.validate_slot_selection("S-2", available_slots)
    print(f"Validating S-2: {result2['valid']} - {result2['reason']}")
    
    # Non-existent slot
    result3 = booking_engine.validate_slot_selection("S-999", available_slots)
    print(f"Validating S-999: {result3['valid']} - {result3['reason']}")
    
    print("=" * 60)


if __name__ == "__main__":
    """Run all examples"""
    
    print("\n" + "🚀 " * 30)
    print("INKA S2 BOOKING ENGINE - USAGE EXAMPLES")
    print("🚀 " * 30)
    
    example_1_offer_slots()
    example_2_no_slots()
    example_3_confirm_selection()
    example_4_slot_taken()
    example_5_full_flow()
    example_6_get_system_prompts()
    example_7_validate_slot()
    
    print("\n" + "✅ " * 30)
    print("ALL EXAMPLES COMPLETED")
    print("✅ " * 30 + "\n")
