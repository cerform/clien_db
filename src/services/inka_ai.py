"""
INKA AI System - Three-in-one AI Assistant for Tattoo Studio
Roles: Classifier (S1) → Consultant-Seller → Booking Assistant (S2)

Architecture:
- Level S1: Intent Classification + Consultation + Booking Assistant Communication
- Level S2: Actual Booking Engine (Slot Management)
- Level S3: Confirmation & Payment

New Architecture with S2 Booking Engine:
- S1: Classification & Consultation (this module)
- S2: Booking Engine with real slots (inka_booking_engine.py)
- S3: Confirmation & Payment (Make.com)
"""

import logging
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

from src.services.openai_service import OpenAIService
from src.services.inka_schema import validate_contract, ContractValidationError, load_contract_from_text
from src.services.telemetry import incr

from src.services.inka_booking_engine import INKABookingEngine, BookingEngineStage
import hashlib

logger = logging.getLogger(__name__)


class BookingType(Enum):
    """Supported booking types"""
    TATTOO = "tattoo"
    WALK_IN = "walk-in"
    CONSULTATION = "consultation"
    NONE = "none"


class Route(Enum):
    """Allowed routes for classification"""
    BOOKING = "booking"
    BOOKING_CONFIRM = "booking_confirm"
    BOOKING_RESCHEDULE = "booking_reschedule"
    CONSULTATION = "consultation"
    INFO = "info"
    OTHER = "other"


class Stage(Enum):
    """Allowed stages in booking flow"""
    OFFER_SLOTS = "offer_slots"
    WAITING_CLIENT_CHOICE = "waiting_client_choice"
    CONFIRMING_CHOICE = "confirming_choice"
    COMPLETED = "completed"
    ERROR = "error"
    NONE = "none"


class INKAClassifier:
    """
    Level S1: Intent Classification Engine
    
    Determines:
    - route (booking, consultation, info, etc.)
    - stage (where in the flow)
    - booking_type (tattoo, walk-in, consultation)
    - intent_summary (what client wants)
    """

    def __init__(self):
        """Initialize classifier with rule-based and keyword patterns"""
        self.booking_keywords = [
            "когда есть время",
            "хочу записаться",
            "когда можно",
            "запишите",
            "book appointment",
            "когда",
            "записать",
            "can i book",
            "want to book",
            "хочу тату",
            "могу записаться",
            "есть свободно",
            "цена",
            "стоимость",
        ]

        self.consultation_keywords = [
            "идея",
            "концепция",
            "рефер",
            "картинка",
            "эскиз",
            "дизайн",
            "обсудить",
            "посоветовать",
            "какую",
            "где сделать",
            "idea",
            "concept",
            "design",
            "what tattoo",
            "suggest",
            "обсуждение",
            "консультация",
            "consultation",
        ]

        self.walkin_keywords = [
            "маленькая",
            "быстро",
            "small",
            "quick",
            "на сегодня",
            "сейчас",
            "now",
            "today",
            "quick session",
            "tiny",
            "простая",
            "легко",
        ]

        self.info_keywords = [
            "боль",
            "больно",
            "уход",
            "уходит",
            "痛",
            "болит",
            "зуд",
            "восстановление",
            "pain",
            "care",
            "healing",
            "aftercare",
            "cost",
            "price",
            "how long",
            "как долго",
            "сколько стоит",
            "область",
            "место",
            "где",
            "зона",
        ]

        self.reschedule_keywords = [
            "перенести",
            "другое время",
            "не могу",
            "отменить",
            "change",
            "reschedule",
            "cancel",
            "another time",
            "переносить",
            "перенесите",
        ]

    def classify(
        self,
        message: str,
        client_status: Optional[str] = None,
        has_active_booking: bool = False,
        active_booking_info: Optional[Dict] = None,
        last_route: Optional[str] = None,
        last_stage: Optional[str] = None,
        callback_slot_id: Optional[str] = None,
    ) -> Dict:
        """
        Classify client intent based on message and context

        Args:
            message: User's message text
            client_status: Previous client status
            has_active_booking: Whether client has an active booking
            active_booking_info: Details of active booking
            last_route: Previous route
            last_stage: Previous stage
            callback_slot_id: Callback slot ID if selecting from offered slots

        Returns:
            {
                "route": "booking|consultation|info|booking_confirm|booking_reschedule|other",
                "stage": "offer_slots|waiting_client_choice|confirming_choice|completed|error|none",
                "booking_type": "tattoo|walk-in|consultation|none",
                "intent_summary": "description of what client wants",
                "confidence": 0.0-1.0,
                "requires_human_review": bool
            }
        """
        msg_lower = message.lower()
        result = {
            "route": Route.OTHER.value,
            "stage": Stage.NONE.value,
            "booking_type": BookingType.NONE.value,
            "intent_summary": "",
            "confidence": 0.5,
            "requires_human_review": False,
        }

        # 1. Check for callback slot selection (highest priority)
        if callback_slot_id:
            result["route"] = Route.BOOKING_CONFIRM.value
            result["stage"] = Stage.CONFIRMING_CHOICE.value
            result["intent_summary"] = "Client selecting offered time slot"
            result["confidence"] = 0.95
            return result

        # 2. Check for reschedule intent (if client has active booking)
        if has_active_booking and self._has_keywords(msg_lower, self.reschedule_keywords):
            result["route"] = Route.BOOKING_RESCHEDULE.value
            result["stage"] = Stage.OFFER_SLOTS.value
            result["booking_type"] = (
                active_booking_info.get("booking_type", BookingType.TATTOO.value)
                if active_booking_info
                else BookingType.TATTOO.value
            )
            result["intent_summary"] = "Client wants to reschedule existing booking"
            result["confidence"] = 0.90
            return result

        # 3. Check for booking intent
        if self._has_keywords(msg_lower, self.booking_keywords):
            result["route"] = Route.BOOKING.value
            result["stage"] = Stage.OFFER_SLOTS.value
            result["booking_type"] = self._classify_booking_type(
                message, self.walkin_keywords, self.consultation_keywords
            )
            result["intent_summary"] = f"Client wants to book {result['booking_type']} appointment"
            result["confidence"] = 0.85
            return result

        # 4. Check for consultation intent
        if self._has_keywords(msg_lower, self.consultation_keywords):
            result["route"] = Route.CONSULTATION.value
            result["stage"] = Stage.NONE.value
            result["intent_summary"] = "Client wants to discuss tattoo idea/design"
            result["confidence"] = 0.80
            return result

        # 5. Check for info intent
        if self._has_keywords(msg_lower, self.info_keywords):
            result["route"] = Route.INFO.value
            result["stage"] = Stage.NONE.value
            result["intent_summary"] = "Client asking for information (pain, care, price, etc.)"
            result["confidence"] = 0.75
            return result

        # 6. Check for slot confirmation by time/date mention
        if self._looks_like_time_selection(msg_lower):
            result["route"] = Route.BOOKING_CONFIRM.value
            result["stage"] = Stage.CONFIRMING_CHOICE.value
            result["intent_summary"] = "Client selecting time/date for appointment"
            result["confidence"] = 0.80
            return result

        # 7. Default: other/unclear
        result["route"] = Route.OTHER.value
        result["stage"] = Stage.NONE.value
        result["intent_summary"] = "Unclear intent - requires clarification"
        result["confidence"] = 0.4
        result["requires_human_review"] = True

        return result

    def _has_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords"""
        return any(kw in text for kw in keywords)

    def _classify_booking_type(
        self, message: str, walkin_keywords: List[str], consultation_keywords: List[str]
    ) -> str:
        """Determine booking type from message"""
        msg_lower = message.lower()

        # Check for walk-in indicators
        if self._has_keywords(msg_lower, walkin_keywords):
            return BookingType.WALK_IN.value

        # Check for consultation indicators
        if self._has_keywords(msg_lower, consultation_keywords):
            return BookingType.CONSULTATION.value

        # Default to tattoo
        return BookingType.TATTOO.value

    def _looks_like_time_selection(self, text: str) -> bool:
        """Check if message looks like selecting a specific time/date"""
        time_patterns = [
            r"\d{1,2}[-/:.]\d{1,2}",  # HH:MM or DD/MM
            r"(понедельник|вторник|среду|четверг|пятницу|субботу|воскресенье|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"(9|10|11|12|13|14|15|16|17|18|19|20|21|22)[:.]?(\d{2})?",  # Hour (9, 14:30, etc.)
            r"завтра|tomorrow|сегодня|today|утром|вечером|morning|evening",
            r"(янв|фев|март|апр|май|июн|июл|авг|сен|окт|ноя|дек|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
        ]
        for pattern in time_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


class INKAConsultant:
    """
    Level S1-S2: Consultant-Seller
    
    When route = consultation/info/other:
    - Responds warmly and professionally
    - Asks clarifying questions (1-2)
    - Explains studio capabilities
    - Guides to booking when ready
    """

    def __init__(self, api_key: Optional[str] = None, openai_service: Optional[OpenAIService] = None):
        """Initialize consultant with optional OpenAI integration"""
        self.api_key = api_key
        self.openai_service = openai_service
        # If no service provided and key is present, create it
        if not self.openai_service and api_key:
            try:
                self.openai_service = OpenAIService(api_key=api_key)
            except Exception:
                self.openai_service = None
        # Default model
        self.model = "gpt-3.5-turbo"

        # Enforce LLM usage by default. If configuration explicitly disables it,
        # honor that, otherwise require the LLM path and escalate when unavailable.
        self.enable_llm = True
        try:
            from src.config.config import Config
            cfg = Config.from_env()
            # If an operator explicitly set ENABLE_LLM to false, respect it
            if hasattr(cfg, 'ENABLE_LLM') and not bool(cfg.ENABLE_LLM):
                self.enable_llm = False
        except Exception:
            # keep default True if config cannot be read
            pass

        # Note: We do not override `enable_llm` if OpenAI service is absent.
        # When `ENABLE_LLM` is explicitly set to true in the environment but
        # there is no valid OpenAI service, `respond_structured` will escalate
        # to a human handler (model_unavailable) as intended by policy.

    def get_system_prompt(self) -> str:
        """
        Core INKA Consultant System Prompt
        For Make.com integration (Russian version)
        """
        return """Ты — INKA, персональный ассистент тату-студии.

Твои три роли:
1. Классификатор намерений (определяешь, что клиент хочет)
2. Консультант-продавец (общаешься мягко, профессионально, без навязчивости)
3. Ассистент записи (помогаешь попасть в календарь)

Ты работаешь в Telegram-формате: коротко, тепло, по делу, без навязчивости.

🟥 ЗАПРЕТЫ — никогда не делай этого:

🟧 ТЕБЯ ВЫЗЫВАЮТ, КОГДА:

Твой тон:
✓ Профессиональный, спокойный, дружелюбный
✓ Без агрессивных продаж
✓ Без сухой бюрократии
✓ Краткие, живые сообщения
✓ Стиль: тёплый, уважительный

ВАЖНО:
    • НЕЛЬЗЯ задавать пользователю просьбы переформулировать один и тот же запрос более одного раза.
    • Если намерение клиента частично ясно, ты ДОЛЖЕН: сделать разумное предположение, продвинуть диалог и задать конкретный направляющий вопрос.
    • Всегда избегай бесконечных циклов уточнений и переформулировок.

"""
    def get_system_prompt_multilingual(self, language: str = "ru") -> str:
        """
        Get system prompt in the user's language
        
        Args:
            language: 'ru', 'en', or 'he'
            
        Returns:
            System prompt in user's language
        """
        if language == "en":
            return """You are INKA, the assistant for a tattoo studio.

Your three roles:
1. Intent classifier (determine what the client wants)
2. Consultant-seller (communicate warmly and professionally)
3. Booking assistant (help them get on the calendar)

You work in Telegram format: natural, warm, and helpful.

🟥 RULES - Never do this:
- Don't make up dates, slots, or times
- Don't suggest available days without real data
- Don't mention prices if you don't have info
- Don't give medical advice
- Don't argue with the client
- Don't write long lectures
- Don't promise things that don't exist
- Don't judge their ideas
- Never reveal or state your internal name or say "My name is..."

Your tone:
✓ Professional, calm, friendly
✓ No aggressive sales
✓ No dry bureaucracy
✓ Natural, conversational replies (avoid single-word answers)
✓ Short but human-like (1-3 sentences when possible)

PREFER: concise, helpful, human-sounding responses. If asked about your name, reply briefly: "I am INKA." 

You are NOT allowed to ask the user to rephrase the same request more than once. If user intent is partially clear, make a reasonable assumption, move the conversation forward, and ask a specific guiding question."""

        elif language == "he":
            return """אתה INKA, העוזר האישי של הסטודיו.

שלוש תפקידים שלך:
1. מסווג כוונות (קבע מה הלקוח רוצה)
2. יועץ-מוכר (התקשר בחום ובמקצועיות)
3. עוזר הזמנה (עזור להם להזמין)

אתה עובד בפורמט טלגרם: קצר, חם, ישיר, ללא לחץ.

🟥 כללים - לעולם אל תעשה:
- אל תימצא תאריכים, משבצות או זמנים
- אל תציע ימים פנויים ללא נתונים אמיתיים
- אל תציין מחירים אם אין לך מידע
- אל תן עצות רפואיות
- אל תתווכח עם הלקוח
- אל תכתוב הרצאות ארוכות
- אל תתן הבטחות לדברים שלא קיימים
- אל תשפוט את הרעיונות שלהם

הטון שלך:
✓ מקצועי, רגוע, ידידותי
✓ אין מכירות תוקפניות
✓ אין ביורוקרטיה יבשה
✓ הודעות קצרות וחיות
✓ סגנון INKA: חם, מקצועי, בלי תכתיבים

שמור תשובות קצרות וברורות!"""

        else:  # default to Russian
            return self.get_system_prompt()

    def _get_user_prompt(self, message: str, booking_type: str, language: str = "ru") -> str:
        """Get user prompt in appropriate language"""
        if language == "en":
            return f"""Client message:
"{message}"

Booking type: {booking_type}

Respond as INKA. Remember:
- Keep it short (1-2 sentences)
- Warm, professional tone
- No sales pressure
- If needed, one clarifying question"""

        elif language == "he":
            return f"""הודעת הלקוח:
"{message}"

סוג הזמנה: {booking_type}

הגב כ-INKA. זכור:
- שמור על קוצר (1-2 משפטים)
- טון חם ומקצועי
- אין לחץ מכירה
- אם צריך, שאלה הבהרה אחת"""

        else:  # Russian
            return """Клиент написал:
"{message}"

Booking type: {booking_type}

Ответь как INKA. Помни:
- Если спросят, представься коротко как INKA
- Отвечай естественно, как живой человек (избегай односложных ответов)
- Кратко и информативно (1-3 предложения)
- Тёплый, профессиональный тон
- Если нужно, задай один уточняющий вопрос"""

    def respond_to_consultation(
        self, message: str, context: Optional[Dict] = None, language: str = "ru"
    ) -> str:
        """
        Generate consultant response for consultation/info route

        Args:
            message: Client message
            context: Additional context (booking_type, client_history, etc.)
            language: User's language (ru, en, he)

        Returns:
            Text response from consultant in user's language
        """
        # If LLM is enforced but the OpenAI service is unavailable, escalate
        if getattr(self, "enable_llm", False) and (not self.openai_service or not self.openai_service.api_enabled):
            incr("llm_enforced_unavailable", 1)
            logger.warning("LLM enforced but unavailable for user=%s; escalating to human", context.get('user_id') if context else None)
            return "Извините, временные трудности с системой — сейчас свяжу с человеком."

        try:
            # Debug: record that we are about to consult the LLM (if enabled)
            try:
                uid = context.get('user_id') if context else None
            except Exception:
                uid = None
            logger.info("🔎 respond_to_consultation: user=%s booking_type=%s llm_enabled=%s", uid, booking_type, self.enable_llm)
            system_prompt = self.get_system_prompt_multilingual(language)
            booking_type = context.get("booking_type", "tattoo") if context else "tattoo"

            user_prompt = self._get_user_prompt(message, booking_type, language)

            # Telemetry: llm call
            incr("llm_calls_total", 1)
            logger.info("💬 Calling LLM (respond_to_consultation) for user=%s...", uid)
            response = self.openai_service.chat_completion(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.7,
                max_tokens=300,
                model=self.model
            )

            return response.choices[0].message.content
        except Exception as e:
            incr("llm_errors_total", 1)
            logger.exception(f"AI consultation error: {e}")
            return self._rule_based_response(message, context, language)

    def _make_antirepeat_key(self, text: str, route: str, booking_type: str) -> str:
        """Create a short anti-repeat key based on content and classification"""
        data = f"{text}|{route}|{booking_type}".encode("utf-8")
        return hashlib.sha256(data).hexdigest()[:12]

    def respond_structured(
        self, message: str, context: Optional[Dict] = None, language: str = "ru"
    ) -> Dict:
        """
        Ask the LLM to produce a strict JSON contract response.

        Returns dict with keys:
            - text: human-readable reply
            - next_action: one of continue_consultation|offer_slots|other
            - meta: { antirepeat_key: str, client_profile: dict }
        Falls back to deterministic contract when LLM is not available or parsing fails.
        """
        context = context or {}
        booking_type = context.get("booking_type", "tattoo")

        # If LLM is required (enabled) but service unavailable, escalate
        if getattr(self, "enable_llm", False) and (not self.openai_service or not self.openai_service.api_enabled):
            incr("llm_enforced_unavailable", 1)
            # Escalate to human if LLM required but not available
            return {"text": "Извините, временные трудности с системой — сейчас свяжу с человеком.", "next_action": "human", "meta": {"stage": "s1", "antirepeat_key": self._make_antirepeat_key(message, context.get("route", "other"), booking_type), "client_profile": {"booking_type": booking_type}, "model_unavailable": True}}

        # Try LLM first
        if self.openai_service and self.openai_service.api_enabled and self.enable_llm:
            try:
                uid = context.get('user_id') if context else None
                logger.info("🔎 respond_structured: user=%s booking_type=%s calling LLM", uid, booking_type)
                system = self.get_system_prompt_multilingual(language)
                instruction = (
                    "You MUST output ONLY a JSON object with the following keys:\n"
                    "{\"text\": string, \"next_action\": string, \"meta\": {\"antirepeat_key\": string, \"client_profile\": object}}\n"
                    "next_action must be one of: continue_consultation, offer_slots, other.\n"
                    "IMPORTANT: You are NOT allowed to ask the user to rephrase the same request more than once.\n"
                    "client_profile should be a short object with any extracted facts (style, size, preferred days, constraints).\n"
                    "Do NOT include any extra commentary outside the JSON. Keep text 1-3 short sentences.\n"
                )

                user_prompt = f"Client message: {message}\nBooking type: {booking_type}\n{instruction}"

                # Telemetry: llm call
                incr("llm_calls_total", 1)
                logger.info("💬 Calling LLM (respond_structured) for user=%s...", uid)
                response = self.openai_service.chat_completion(
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user_prompt}],
                    temperature=0.25,
                    max_tokens=400,
                    model=self.model
                )

                raw = response.choices[0].message.content.strip()

                # The model should return pure JSON; attempt to extract the first JSON object
                try:
                    payload = load_contract_from_text(raw)
                    # Validate completed by load_contract_from_text
                    text = payload.get("text", "Извини, не поняла — уточни, пожалуйста.")
                    next_action = payload.get("next_action", "other")
                    meta = payload.get("meta", {})
                    # Safety: avoid simple echo loops where model repeats client's message
                    try:
                        norm_text = " ".join(text.lower().split())
                        norm_msg = " ".join(message.lower().split())
                        if norm_text == norm_msg or norm_msg in norm_text:
                            # Replace with a clarifying prompt instead of echoing
                            text = "Извини, не совсем понимаю — уточни, пожалуйста: где именно (место), какого размера примерно и есть ли референсы?"
                            next_action = "other"
                            meta["antirepeat_key"] = self._make_antirepeat_key(text, context.get("route", "other"), booking_type)
                    except Exception:
                        # If normalization check fails, ignore and proceed
                        pass
                    # Ensure antirepeat & client_profile exist
                    if "antirepeat_key" not in meta or not meta.get("antirepeat_key"):
                        meta["antirepeat_key"] = self._make_antirepeat_key(text, context.get("route", "other"), booking_type)
                    if "client_profile" not in meta:
                        meta["client_profile"] = {"booking_type": booking_type}

                    # Final validation: ensure stage matches next_action if present
                    if meta.get("stage") and meta.get("stage").lower() != next_action:
                        # keep them in sync by setting stage to next_action
                        meta["stage"] = next_action

                    return {"text": text, "next_action": next_action, "meta": meta}
                except ContractValidationError as e:
                    incr("llm_parse_failures", 1)
                    logger.warning(f"Model returned invalid contract: {e}; escalating to human because LLM is enforced")
                    # When LLM is enforced, invalid contract means we cannot safely continue.
                    return {"text": "Извините, временные трудности с системой — свяжу с человеком.", "next_action": "human", "meta": {"stage": "s1", "antirepeat_key": self._make_antirepeat_key(message, context.get("route", "other"), booking_type), "client_profile": {"booking_type": booking_type}, "model_unavailable": True}}

            except Exception as e:
                logger.exception(f"Structured LLM response failed: {e}")
                # If LLM is enforced, escalate instead of falling back to deterministic contract
                if getattr(self, "enable_llm", False):
                    incr("llm_errors_total", 1)
                    return {"text": "Извините, временные трудности с системой — свяжу с человеком.", "next_action": "human", "meta": {"stage": "s1", "antirepeat_key": self._make_antirepeat_key(message, context.get("route", "other"), booking_type), "client_profile": {"booking_type": booking_type}, "model_unavailable": True}}

        # Fallback deterministic contract
        text = self._rule_based_response(message, context, language)
        next_action = "continue_consultation"
        if context.get("route") in ["booking", "booking_confirm", "booking_reschedule"]:
            next_action = "offer_slots"

        meta = {
            "antirepeat_key": self._make_antirepeat_key(text, context.get("route", "other"), booking_type),
            "client_profile": {"booking_type": booking_type},
        }

        return {"text": text, "next_action": next_action, "meta": meta}

    def _rule_based_response(self, message: str, context: Optional[Dict] = None, language: str = "ru") -> str:
        """Fallback rule-based response for consultation in user's language"""
        msg_lower = message.lower()

        # Pain-related questions
        if any(
            kw in msg_lower
            for kw in ["боль", "больно", "pain", "hurt", "ache", "болит", "כאב"]
        ):
            responses = {
                "ru": "Ощущения индивидуальны и зависят от области и объёма работы. Я помогу подобрать место и расскажу, как подготовиться. Где ты планируешь тату?",
                "en": "Pain varies depending on placement, design size, and your pain threshold. I can help you pick the best location and prepare. Where are you thinking?",
                "he": "הכאב משתנה בהתאם למיקום וגודל. אני יכולה לעזור לבחור את המקום ולהסביר איך להתכונן. איפה אתה חושב?"
            }
            return responses.get(language, responses["ru"])

        # Care/aftercare questions
        if any(
            kw in msg_lower
            for kw in ["уход", "восстановление", "care", "aftercare", "healing", "уходит", "טיפול"]
        ):
            responses = {
                "ru": "После тату важен правильный уход — могу дать пошаговые инструкции и ответы на вопросы. Что именно тебя интересует?",
                "en": "Proper aftercare is important after a tattoo — I can provide step-by-step care instructions and answer your questions. What would you like to know?",
                "he": "טיפול נכון חשוב לאחר קעקוע — אני יכולה לספק הוראות שלב אחר שלב ולענות על שאלות. מה מעניין אותך?"
            }
            return responses.get(language, responses["ru"])

        # Price/cost questions
        if any(
            kw in msg_lower
            for kw in ["цена", "стоимость", "price", "cost", "сколько стоит", "מחיר"]
        ):
            responses = {
                "ru": "Стоимость зависит от размера, сложности и времени работы — если расскажешь идею, я постараюсь сориентировать по цене или предложить варианты.",
                "en": "Price depends on size, complexity, and time required — tell me your idea and I can give an estimate or suggest options.",
                "he": "המחיר תלוי בגודל ובמורכבות — ספר את הרעיון ואני אתן הערכה או אפשרויות."
            }
            return responses.get(language, responses["ru"])

        # Design/idea discussion
        if any(
            kw in msg_lower
            for kw in ["идея", "дизайн", "концепция", "design", "idea", "картинка", "рефер", "עיצוב", "רעיון"]
        ):
            responses = {
                "ru": "Отлично! Расскажи подробнее о своей идее. Это большая работа или компактная? Есть ли у тебя рефы для вдохновения?",
                "en": "Excellent! Tell me more about your idea. Is it a large piece or something small? Do you have any references for inspiration?",
                "he": "מעולה! ספר לי עוד על הרעיון שלך. האם זה יצירה גדולה או משהו קטן? יש לך הפניות להשראה?"
            }
            return responses.get(language, responses["ru"])

        # Default warm response
        responses = {
            "ru": "Спасибо за вопрос — расскажи, пожалуйста, подробнее, что именно тебя интересует, и я помогу.",
            "en": "Thanks for the question — tell me more about what you're interested in and I will help.",
            "he": "תודה על השאלה — ספר יותר על מה מעניין אותך ואני אעזור."
        }
        return responses.get(language, responses["ru"])

    def suggest_booking(self, language: str = "ru") -> str:
        """Suggest moving to booking when client is ready"""
        suggestions = {
            "ru": "Хорошо, могу показать свободные варианты. Хочешь посмотреть время?",
            "en": "Great, I can show you available options. Want to see the times?",
            "he": "מעולה, אני יכול להראות לך אפשרויות זמינות. רוצה לראות את הזמנים?"
        }
        return suggestions.get(language, suggestions["ru"])


class INKABookingAssistant:
    """
    Level S2: Booking Assistant
    
    Prepares transition to booking engine
    - Does NOT create slots
    - Does NOT assign times
    - Prepares context for S2 booking system
    """

    @staticmethod
    def prepare_for_booking(
        route: str, booking_type: str, message: str
    ) -> Dict:
        """
        Prepare booking context for S2

        Args:
            route: Classification route
            booking_type: Type of booking (tattoo, walk-in, consultation)
            message: Original client message

        Returns:
            Context dict for booking engine
        """
        return {
            "route": route,
            "booking_type": booking_type,
            "client_message": message,
            "ready_for_slots": route in [
                Route.BOOKING.value,
                Route.BOOKING_CONFIRM.value,
                Route.BOOKING_RESCHEDULE.value,
            ],
            "transition_message": "Хорошо, могу показать свободные варианты. Хочешь посмотреть время?",
        }

    @staticmethod
    def validate_booking_ready(classification: Dict) -> bool:
        """Check if ready to move to booking slots"""
        return classification.get("route") in [
            Route.BOOKING.value,
            Route.BOOKING_CONFIRM.value,
            Route.BOOKING_RESCHEDULE.value,
        ]


class INKA:
    """
    Main INKA orchestrator
    Coordinates all three roles (Classifier → Consultant → Booking Assistant)
    
    Now includes S2 Booking Engine integration
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize INKA with all components including S2 Booking Engine"""
        self.classifier = INKAClassifier()
        # If an API key is provided, prefer the new LLM-only consultant (INKAConsultantV2)
        if api_key:
            try:
                from src.services.inka_consultant_v2 import INKAConsultantV2

                self.consultant = INKAConsultantV2(api_key=api_key)
            except Exception:
                # Fall back to legacy consultant if anything goes wrong during import/initialization
                logger = logging.getLogger(__name__)
                logger.exception("Failed to initialize INKAConsultantV2, falling back to legacy INKAConsultant")
                self.consultant = INKAConsultant(api_key)
        else:
            self.consultant = INKAConsultant(api_key)
        self.booking_assistant = INKABookingAssistant()
        self.booking_engine = INKABookingEngine()  # New S2 Booking Engine

    def process(
        self,
        message: str,
        client_context: Optional[Dict] = None,
        callback_slot_id: Optional[str] = None,
    ) -> Dict:
        """
        Main processing pipeline: Classify → Respond → Prepare Booking

        Args:
            message: Client message
            client_context: Dict with client_status, has_active_booking, etc.
            callback_slot_id: If client is selecting from offered slots

        Returns:
            {
                "classification": {...},
                "response": "text response",
                "booking_context": {...},
                "next_action": "continue_consultation|offer_slots|other"
            }
        """
        client_context = client_context or {}

        # Step 1: CLASSIFY
        classification = self.classifier.classify(
            message=message,
            client_status=client_context.get("client_status"),
            has_active_booking=client_context.get("has_active_booking", False),
            active_booking_info=client_context.get("active_booking_info"),
            last_route=client_context.get("last_route"),
            last_stage=client_context.get("last_stage"),
            callback_slot_id=callback_slot_id,
        )

        # Use structured responses for all routes (contains text + meta)
        resp_context = {
            "booking_type": classification["booking_type"],
            "route": classification["route"],
        }

        structured = self.consultant.respond_structured(message, context=resp_context)
        # structured: {text, next_action, meta}
        response = structured.get("text")
        next_action = structured.get("next_action", "other")
        meta = structured.get("meta", {})

        # Step 3: PREPARE BOOKING CONTEXT
        booking_context = (
            self.booking_assistant.prepare_for_booking(
                classification["route"], classification["booking_type"], message
            )
            if self.booking_assistant.validate_booking_ready(classification)
            else {}
        )

        return {
            "classification": classification,
            "response": response,
            "meta": meta if 'meta' in locals() else {},
            "booking_context": booking_context,
            "next_action": next_action,
            "timestamp": datetime.now().isoformat(),
        }

    def process_s2_booking(
        self,
        available_slots: List[Dict],
        stage: str = "offer_slots",
        selected_slot: Optional[Dict] = None,
        slot_taken: bool = False
    ) -> Dict:
        """
        Process S2 Booking Engine stage
        
        Args:
            available_slots: List of available slot dicts from database
            stage: "offer_slots" or "confirming_choice"
            selected_slot: Selected slot (for confirming_choice)
            slot_taken: Whether slot is no longer available
        
        Returns:
            Complete S2 response with message and data
        """
        return self.booking_engine.prepare_s2_context(
            available_slots=available_slots,
            stage=stage,
            selected_slot=selected_slot,
            slot_taken=slot_taken
        )

    def get_system_prompts(self) -> Dict[str, str]:
        """
        Get all system prompts for Make.com integration

        Returns dict with prompts for different branches
        """
        return {
            "s1_consultation_prompt": self.consultant.get_system_prompt(),
            "s1_info_prompt": self.consultant.get_system_prompt(),
            "s1_communication_prompt": self.consultant.get_system_prompt(),
            "s1_general_prompt": f"""Ты — INKA, персональный ассистент тату-мастера Ани.

Твоя задача:
1. Понять, что хочет клиент (классификация)
2. Ответить профессионально и теплу (консультация)
3. Мягко перевести в бронирование, если он готов

Помни правила:
- Не придумывай даты и слоты
- Не давай точные цены
-- Не пиши длинные речи
-- Будь как INKA: тёплая, опытная, без давления""",
            "s2_offer_slots_prompt": self.booking_engine.get_system_prompt_for_stage(
                BookingEngineStage.OFFER_SLOTS.value
            ),
            "s2_confirming_choice_prompt": self.booking_engine.get_system_prompt_for_stage(
                BookingEngineStage.CONFIRMING_CHOICE.value
            ),
            # Extended stages S8..S12
            "s8_reschedule_prompt": "You are INKA. Help the client reschedule: offer alternative slots and confirm. Keep it warm and one question at a time.",
            "s9_cancel_prompt": "You are INKA. Confirm cancellation, show refund/cancellation policy briefly, and offer to rebook. Keep it short.",
            "s10_payment_prompt": "You are INKA. Explain payment options briefly and provide a secure payment link if required. Do not ask for payment details in chat.",
            "s11_reminder_prompt": "You are INKA. Provide concise reminders and pre-visit instructions and ask if they need to add the event to calendar.",
            "s12_smalltalk_prompt": "You are INKA. Handle short friendly chit-chat gracefully but always offer to help with booking or questions. Keep answers short and warm.",
        }


# Export for easy imports
__all__ = [
    "INKA",
    "INKAClassifier",
    "INKAConsultant",
    "INKAConsultantV2",
    "INKABookingAssistant",
    "INKABookingEngine",
    "BookingType",
    "Route",
    "Stage",
    "BookingEngineStage",
]
