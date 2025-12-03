"""
INKA S2 - Booking Engine Module

This module handles Level S2 (Booking Engine) operations:
- Formatting available slots for client presentation
- Generating human-friendly slot offer messages
- Handling slot selection confirmation
- Managing slot availability validation

Architecture:
- S1 (Classification) → S2 (Booking Engine) → S3 (Confirmation)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class BookingEngineStage(Enum):
    """Stages in S2 Booking Engine"""
    OFFER_SLOTS = "offer_slots"
    WAITING_CLIENT_CHOICE = "waiting_client_choice"
    CONFIRMING_CHOICE = "confirming_choice"


class INKABookingEngine:
    """
    INKA S2: Booking Engine
    
    Responsibilities:
    1. Format available slots for presentation
    2. Generate human-friendly messages (offer_slots mode)
    3. Generate confirmation messages (confirming_choice mode)
    4. Validate slot availability
    
    Does NOT:
    - Create or modify slots
    - Invent dates or times
    - Make booking decisions
    - Directly interact with database
    """

    def __init__(self):
        """Initialize Booking Engine"""
        self.stage = None

    def format_slots_for_display(self, slots: List[Dict]) -> List[Dict]:
        """
        Format raw slot data for client display
        
        Args:
            slots: List of slot dicts with keys:
                - slot_id: str
                - date: str (YYYY-MM-DD)
                - start_time: str (HH:MM)
                - end_time: str (HH:MM)
                - available: bool
        
        Returns:
            Formatted slots with human-readable date/time
        """
        formatted = []
        for slot in slots:
            if not slot.get("available", True):
                continue
                
            try:
                # Parse date
                date_obj = datetime.strptime(slot["date"], "%Y-%m-%d")
                date_formatted = date_obj.strftime("%d.%m")  # 12.12
                
                formatted.append({
                    "slot_id": slot["slot_id"],
                    "date": slot["date"],
                    "date_formatted": date_formatted,
                    "start_time": slot["start_time"],
                    "end_time": slot["end_time"],
                    "display_text": f"{date_formatted} в {slot['start_time']}"
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Error formatting slot {slot.get('slot_id')}: {e}")
                continue
        
        return formatted

    def generate_slot_offer_message(
        self, 
        available_slots: List[Dict],
        booking_type: str = "tattoo"
    ) -> Dict:
        """
        Generate human-friendly message for offering slots (stage: offer_slots)
        
        Args:
            available_slots: List of formatted slot dicts
            booking_type: Type of booking (tattoo, walk-in, consultation)
        
        Returns:
            {
                "message": str,  # Human-readable message
                "has_slots": bool,
                "slot_count": int,
                "formatted_slots": List[Dict]
            }
        """
        if not available_slots:
            return {
                "message": (
                    "Сейчас свободных окон для этого типа записи нет.\n"
                    "Могу написать тебе, как только появится подходящее время."
                ),
                "has_slots": False,
                "slot_count": 0,
                "formatted_slots": []
            }
        
        formatted_slots = self.format_slots_for_display(available_slots)
        
        # Build message
        message_lines = ["Вот ближайшие свободные окна:\n"]
        
        for slot in formatted_slots[:10]:  # Limit to first 10 slots
            message_lines.append(f"— {slot['display_text']}")
        
        message_lines.append("\nНажми на удобный вариант, и я закреплю время.")
        
        return {
            "message": "\n".join(message_lines),
            "has_slots": True,
            "slot_count": len(formatted_slots),
            "formatted_slots": formatted_slots
        }

    def generate_confirmation_message(
        self,
        selected_slot: Dict,
        slot_taken: bool = False
    ) -> Dict:
        """
        Generate confirmation message (stage: confirming_choice)
        
        Args:
            selected_slot: Dict with slot_id, date, start_time, end_time
            slot_taken: Whether slot is no longer available
        
        Returns:
            {
                "message": str,
                "success": bool,
                "slot_id": str
            }
        """
        if slot_taken:
            return {
                "message": (
                    "Этот слот только что заняли.\n"
                    "Хочешь посмотреть другие свободные варианты?"
                ),
                "success": False,
                "slot_id": selected_slot.get("slot_id")
            }
        
        # Parse date for formatting
        try:
            date_obj = datetime.strptime(selected_slot["date"], "%Y-%m-%d")
            date_formatted = date_obj.strftime("%d.%m")  # 12.12
        except (ValueError, KeyError):
            date_formatted = selected_slot.get("date", "")
        
        start_time = selected_slot.get("start_time", "")
        
        return {
            "message": (
                f"Отлично, записала тебя на {date_formatted} в {start_time}.\n"
                f"Скоро пришлю детали и подготовку к сеансу."
            ),
            "success": True,
            "slot_id": selected_slot.get("slot_id"),
            "date": selected_slot.get("date"),
            "time": start_time
        }

    def build_slot_keyboard_data(self, formatted_slots: List[Dict]) -> List[Dict]:
        """
        Build inline keyboard data for Telegram
        
        Args:
            formatted_slots: List of formatted slot dicts
        
        Returns:
            List of button data for inline keyboard
        """
        buttons = []
        for slot in formatted_slots[:10]:  # Max 10 buttons
            buttons.append({
                "text": slot["display_text"],
                "callback_data": f"slot_{slot['slot_id']}"
            })
        return buttons

    def validate_slot_selection(
        self,
        slot_id: str,
        available_slots: List[Dict]
    ) -> Dict:
        """
        Validate that selected slot is still available
        
        Args:
            slot_id: Selected slot ID
            available_slots: Current list of available slots
        
        Returns:
            {
                "valid": bool,
                "slot": Dict or None,
                "reason": str
            }
        """
        for slot in available_slots:
            if slot.get("slot_id") == slot_id:
                if slot.get("available", True):
                    return {
                        "valid": True,
                        "slot": slot,
                        "reason": "Slot is available"
                    }
                else:
                    return {
                        "valid": False,
                        "slot": None,
                        "reason": "Slot is no longer available"
                    }
        
        return {
            "valid": False,
            "slot": None,
            "reason": "Slot not found"
        }

    def get_system_prompt_for_stage(self, stage: str) -> str:
        """
        Get system prompt for OpenAI based on current stage
        
        Args:
            stage: "offer_slots" or "confirming_choice"
        
        Returns:
            System prompt string
        """
        base_prompt = """Ты — ИНКА, ассистент тату-мастера Ани.
Ты работаешь в сценарии S2 (Booking Engine).

Ты не придумываешь данные. Ты не генерируешь JSON.
Ты выводишь только готовый, человеческий текст-сообщение.

Все слоты, доступные тебе, приходят в переменной available_slots.

Тебе запрещено:
 • добавлять новые даты,
 • придумывать время,
 • сокращать или менять массив,
 • выдавать выдуманные окна,
 • делать выводы о загрузке мастера.

Тон общения:
 • коротко, по делу, живо;
 • никакой офисной, шаблонной речи;
 • стиль Ани — тёплый, аккуратный, уважительный;
 • без нажима;
 • без агрессивных продаж.
"""

        if stage == BookingEngineStage.OFFER_SLOTS.value:
            return base_prompt + """
Твоя задача: Мягко и коротко предложить клиенту доступные варианты.

Если массив пустой:
«Сейчас свободных окон для этого типа записи нет.
Могу написать тебе, как только появится подходящее время.»

Если слоты есть:
Перечисли все и дай ясную инструкцию:
«Нажми на удобный вариант, и я закреплю время.»
"""

        elif stage == BookingEngineStage.CONFIRMING_CHOICE.value:
            return base_prompt + """
Твоя задача: Подтвердить, что время принято.

Тон — спокойный, уверенный.

Шаблон ответа:
«Отлично, записала тебя на [дата] в [время].
Скоро пришлю детали и подготовку к сеансу.»

Если slot_taken = true:
«Этот слот только что заняли.
Хочешь посмотреть другие свободные варианты?»
"""

        return base_prompt

    def prepare_s2_context(
        self,
        available_slots: List[Dict],
        stage: str,
        selected_slot: Optional[Dict] = None,
        slot_taken: bool = False
    ) -> Dict:
        """
        Prepare complete context for S2 processing
        
        Args:
            available_slots: List of available slot dicts
            stage: Current stage (offer_slots, confirming_choice)
            selected_slot: Selected slot (for confirming_choice stage)
            slot_taken: Whether selected slot is taken
        
        Returns:
            Complete S2 context dict
        """
        context = {
            "stage": stage,
            "available_slots": available_slots,
            "timestamp": datetime.now().isoformat()
        }
        
        if stage == BookingEngineStage.OFFER_SLOTS.value:
            offer = self.generate_slot_offer_message(available_slots)
            context.update({
                "message": offer["message"],
                "has_slots": offer["has_slots"],
                "slot_count": offer["slot_count"],
                "formatted_slots": offer["formatted_slots"],
                "keyboard_data": self.build_slot_keyboard_data(
                    offer["formatted_slots"]
                ) if offer["has_slots"] else []
            })
        
        elif stage == BookingEngineStage.CONFIRMING_CHOICE.value:
            if selected_slot:
                confirmation = self.generate_confirmation_message(
                    selected_slot, slot_taken
                )
                context.update({
                    "message": confirmation["message"],
                    "success": confirmation["success"],
                    "selected_slot": selected_slot
                })
        
        return context


# Export
__all__ = [
    "INKABookingEngine",
    "BookingEngineStage"
]
