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

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from src.services.inka_booking_engine import INKABookingEngine, BookingEngineStage

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

    def __init__(self, api_key: Optional[str] = None):
        """Initialize consultant with optional OpenAI integration"""
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key) if api_key and OpenAI else None
        self.model = "gpt-3.5-turbo"

    def get_system_prompt(self) -> str:
        """
        Core INKA Consultant System Prompt
        For Make.com integration (Russian version)
        """
        return """Ты — ИНКА, персональный ассистент тату-мастера Ани.

Твои три роли:
1. Классификатор намерений (определяешь, что клиент хочет)
2. Консультант-продавец (общаешься мягко, профессионально, без навязчивости)
3. Ассистент записи (помогаешь попасть в календарь)

Ты работаешь в Telegram-формате: коротко, тепло, по делу, без навязчивости.

🟥 ЗАПРЕТЫ — никогда не делай этого:
- Не придумывай даты, слоты, время
- Не предлагай свободные дни без реальных данных
- Не называй стоимость, если нет информации
- Не давай медицинские советы
- Не спорь с клиентом
- Не пиши длинные лекции
- Не обещай то, чего нет
- Не осуждай идеи клиента

🟧 ТЕБЯ ВЫЗЫВАЮТ, КОГДА:
- route = consultation (клиент обсуждает идею)
- route = info (клиент спрашивает про боль, уход, цены, место)
- route = other (неясное намерение)

Твой тон:
✓ Профессиональный, спокойный, дружелюбный
✓ Без агрессивных продаж
✓ Без сухой бюрократии
✓ Краткие, живые сообщения
✓ Стиль Ани: тёплый, уважительный, без сюсюкалки

ОТВЕТЫ КОРОТКО И ЧЕТКО!"""

    def get_system_prompt_multilingual(self, language: str = "ru") -> str:
        """
        Get system prompt in the user's language
        
        Args:
            language: 'ru', 'en', or 'he'
            
        Returns:
            System prompt in user's language
        """
        if language == "en":
            return """You are INKA, the personal assistant for tattoo artist Anna.

Your three roles:
1. Intent classifier (determine what the client wants)
2. Consultant-seller (communicate warmly and professionally)
3. Booking assistant (help them get on the calendar)

You work in Telegram format: short, warm, to the point, no pressure.

🟥 RULES - Never do this:
- Don't make up dates, slots, or times
- Don't suggest available days without real data
- Don't mention prices if you don't have info
- Don't give medical advice
- Don't argue with the client
- Don't write long lectures
- Don't promise things that don't exist
- Don't judge their ideas

Your tone:
✓ Professional, calm, friendly
✓ No aggressive sales
✓ No dry bureaucracy
✓ Brief, vivid messages
✓ Anna's style: warm, respectful, no baby talk

KEEP ANSWERS SHORT AND CLEAR!"""

        elif language == "he":
            return """אתה INKA, העוזר האישי של האמן טטו אנה.

שלוש תפקידים שלך:
1. מסווג כוונות (קבע מה הלקוח רוצה)
2. יועץ-מוכר (התקשר בחום ובמקצועיות)
3. עוזר הזמנה (עזור להם להזמין)

אתה עובד בפורמט טלגרם: קצר, חם, ישיר, ללא לחץ.

🟥 כללים - לעולם אל תעשה:
- אל תימציא תאריכים, משבצות או זמנים
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
✓ סגנון אנה: חם, כבודי, ללא תינוק

שמור תשובות קצרות וברורות!"""

        else:  # default to Russian
            return self.get_system_prompt()

    def _get_user_prompt(self, message: str, booking_type: str, language: str = "ru") -> str:
        """Get user prompt in appropriate language"""
        if language == "en":
            return f"""Client message:
"{message}"

Booking type: {booking_type}

Respond as Anna (INKA). Remember:
- Keep it short (1-2 sentences)
- Warm, professional tone
- No sales pressure
- If needed, one clarifying question"""

        elif language == "he":
            return f"""הודעת הלקוח:
"{message}"

סוג הזמנה: {booking_type}

הגב כאנה (INKA). זכור:
- שמור על קוצר (1-2 משפטים)
- טון חם ומקצועי
- אין לחץ מכירה
- אם צריך, שאלה הבהרה אחת"""

        else:  # Russian
            return f"""Клиент написал:
"{message}"

Booking type: {booking_type}

Ответь как Аня (ИНКА). Помни:
- Коротко (1-2 предложения)
- Теплый, профессиональный тон
- Без продажного давления
- Если нужно, один уточняющий вопрос"""

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
        if not self.client:
            # Fallback: rule-based response
            return self._rule_based_response(message, context, language)

        try:
            system_prompt = self.get_system_prompt_multilingual(language)
            booking_type = context.get("booking_type", "tattoo") if context else "tattoo"

            user_prompt = self._get_user_prompt(message, booking_type, language)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=300,
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.exception(f"AI consultation error: {e}")
            return self._rule_based_response(message, context, language)

    def _rule_based_response(self, message: str, context: Optional[Dict] = None, language: str = "ru") -> str:
        """Fallback rule-based response for consultation in user's language"""
        msg_lower = message.lower()

        # Pain-related questions
        if any(
            kw in msg_lower
            for kw in ["боль", "больно", "pain", "hurt", "ache", "болит", "כאב"]
        ):
            responses = {
                "ru": "Ощущения индивидуальны и зависят от места, размера работы и твоего болевого порога. Аня подберёт место и подготовит тебя. Где ты планируешь тату?",
                "en": "Pain varies depending on placement, design size, and your pain threshold. Anna will help you choose the best location and prepare. Where are you thinking?",
                "he": "הכאב משתנה בהתאם למיקום, גודל העיצוב וסף הכאב שלך. אנה תעזור לך לבחור את המיקום הטוב ביותר. איפה אתה חושב?"
            }
            return responses.get(language, responses["ru"])

        # Care/aftercare questions
        if any(
            kw in msg_lower
            for kw in ["уход", "восстановление", "care", "aftercare", "healing", "уходит", "טיפול"]
        ):
            responses = {
                "ru": "После тату важно правильно ухаживать. Аня даст подробные инструкции по уходу и ответит на все вопросы. Что тебя интересует?",
                "en": "Proper aftercare is important after a tattoo. Anna will give detailed instructions and answer all your questions. What would you like to know?",
                "he": "טיפול נכון חשוב לאחר קעקוע. אנה תתן הוראות מפורטות ותענה על כל שאלותיך. מה אתה רוצה לדעת?"
            }
            return responses.get(language, responses["ru"])

        # Price/cost questions
        if any(
            kw in msg_lower
            for kw in ["цена", "стоимость", "price", "cost", "сколько стоит", "מחיר"]
        ):
            responses = {
                "ru": "Стоимость зависит от размера, сложности и времени работы. Аня обсудит все детали и подберёт вариант. Какая у тебя идея?",
                "en": "Price depends on size, complexity, and time required. Anna will discuss all details and find the best option. What's your idea?",
                "he": "המחיר תלוי בגודל, במורכבות ובזמן הנדרש. אנה תדון בפרטים וההיצע הטוב ביותר. מה הרעיון שלך?"
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
            "ru": "Спасибо за вопрос! Аня ответит на всё. Расскажи подробнее, что тебе интересно?",
            "en": "Thanks for the question! Anna will answer everything. Tell me more about what you're interested in?",
            "he": "תודה על השאלה! אנה תענה על הכל. ספר לי עוד על מה אתה מעוניין?"
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

        # Step 2: RESPOND based on route
        if classification["route"] in [
            Route.CONSULTATION.value,
            Route.INFO.value,
            Route.OTHER.value,
        ]:
            # Consultant responds
            response = self.consultant.respond_to_consultation(
                message,
                context={
                    "booking_type": classification["booking_type"],
                    "route": classification["route"],
                },
            )
            next_action = "continue_consultation"
        elif classification["route"] in [
            Route.BOOKING.value,
            Route.BOOKING_CONFIRM.value,
            Route.BOOKING_RESCHEDULE.value,
        ]:
            # Transition to booking
            response = self.consultant.suggest_booking()
            next_action = "offer_slots"
        else:
            response = self.consultant._rule_based_response(message)
            next_action = "other"

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
- Не пиши длинные речи
- Будь как Аня: теплая, опытная, без давления""",
            "s2_offer_slots_prompt": self.booking_engine.get_system_prompt_for_stage(
                BookingEngineStage.OFFER_SLOTS.value
            ),
            "s2_confirming_choice_prompt": self.booking_engine.get_system_prompt_for_stage(
                BookingEngineStage.CONFIRMING_CHOICE.value
            ),
        }


# Export for easy imports
__all__ = [
    "INKA",
    "INKAClassifier",
    "INKAConsultant",
    "INKABookingAssistant",
    "INKABookingEngine",
    "BookingType",
    "Route",
    "Stage",
    "BookingEngineStage",
]
