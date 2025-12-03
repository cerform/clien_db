"""
Admin Chat Service - AI-powered chat for studio administration
Supports multilingual conversations and automatic message categorization

Integrated with INKA AI for intelligent client interaction classification
"""

from openai import OpenAI
from datetime import datetime
from typing import Optional, Dict
from src.services.inka_ai import INKA, INKAClassifier


class AdminChatService:
    """Chat service for admin communication with AI that acts as studio admin"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
        # Store conversation history per admin user
        self.conversations = {}
        # Initialize INKA for client message classification
        self.inka = INKA(api_key=api_key)

    def _get_system_prompt(self) -> str:
        """Create system prompt for admin persona"""
        return """You are a professional tattoo studio administrator. Your role is to help manage the studio operations.

You should:
1. Communicate naturally in any language the user uses (Russian, English, Hebrew, etc.)
2. Be helpful, professional, and friendly
3. Ask clarifying questions when needed
4. Extract key information from conversations
5. Summarize information clearly

When the user provides information, acknowledge it and ask if you need clarification.
Always be concise but thorough.

Categories you help manage:
- Client Information (names, contacts, preferences)
- Master Information (availability, specialties, notes)
- Appointment Details (dates, times, designs, prices)
- Studio Operations (hours, policies, equipment)
- Financial Information (prices, payments, costs)
- Marketing & Feedback (promotions, reviews, inquiries)
- Technical Issues & Other Notes

Respond in a natural, conversational way without being too formal."""

    def process_message(
        self, user_id: int, message: str, admin_user_id: int = None
    ) -> dict:
        """
        Process admin message with AI and extract categories

        Args:
            user_id: Telegram user ID (admin)
            message: Message text
            admin_user_id: Optional admin ID for tracking

        Returns:
            dict with ai_response, categories, extracted_data
        """
        # Initialize conversation if needed
        if user_id not in self.conversations:
            self.conversations[user_id] = []

        # Add user message to history
        self.conversations[user_id].append({"role": "user", "content": message})

        # Get AI response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                *self.conversations[user_id],
            ],
            temperature=0.7,
            max_tokens=500,
        )

        ai_response = response.choices[0].message.content

        # Add AI response to history
        self.conversations[user_id].append({"role": "assistant", "content": ai_response})

        # Keep only last 10 messages to avoid token limits
        if len(self.conversations[user_id]) > 20:
            self.conversations[user_id] = self.conversations[user_id][-20:]

        # Extract categories and data
        categories = self._extract_categories(message, ai_response)
        extracted_data = self._extract_data(message, categories)

        return {
            "ai_response": ai_response,
            "categories": categories,
            "extracted_data": extracted_data,
            "timestamp": datetime.now().isoformat(),
            "admin_user_id": admin_user_id,
        }

    def _extract_categories(self, message: str, ai_response: str) -> list:
        """Detect message categories based on content"""
        lower_msg = message.lower()
        categories = []

        # Category keywords mapping
        category_keywords = {
            "Client Information": [
                "клиент",
                "client",
                "customer",
                "контакт",
                "phone",
                "email",
                "телефон",
            ],
            "Master Information": [
                "мастер",
                "master",
                "artist",
                "tattoo artist",
                "специалист",
                "availability",
                "доступность",
            ],
            "Appointment Details": [
                "appointment",
                "запись",
                "booking",
                "date",
                "time",
                "время",
                "дата",
                "slot",
            ],
            "Financial Information": [
                "price",
                "цена",
                "payment",
                "платеж",
                "cost",
                "стоимость",
                "invoice",
                "счет",
            ],
            "Studio Operations": [
                "studio",
                "студия",
                "hours",
                "часы",
                "policy",
                "политика",
                "операции",
                "operations",
            ],
            "Marketing & Feedback": [
                "promotion",
                "промо",
                "review",
                "отзыв",
                "feedback",
                "marketing",
                "маркетинг",
            ],
            "Technical Issues": [
                "error",
                "ошибка",
                "bug",
                "issue",
                "problem",
                "проблема",
                "technical",
                "техническая",
            ],
        }

        for category, keywords in category_keywords.items():
            if any(kw in lower_msg for kw in keywords):
                categories.append(category)

        # If no categories detected, mark as "Other Notes"
        if not categories:
            categories.append("Other Notes")

        return list(set(categories))  # Remove duplicates

    def _extract_data(self, message: str, categories: list) -> dict:
        """Extract structured data from message"""
        extracted = {
            "categories": categories,
            "raw_message": message,
            "has_contact_info": any(
                x in message for x in ["@", "+", "tel:", "phone", "телефон"]
            ),
            "has_date": any(
                x in message.lower()
                for x in [
                    "2024",
                    "2025",
                    "january",
                    "february",
                    "january",
                    "январь",
                    "февраль",
                ]
            ),
            "has_price": any(
                x in message for x in ["$", "₪", "€", "₽", "грн", "рубль"]
            ),
        }
        return extracted

    def clear_history(self, user_id: int):
        """Clear conversation history for user"""
        if user_id in self.conversations:
            del self.conversations[user_id]

    def get_conversation_summary(self, user_id: int) -> str:
        """Get summary of conversation so far"""
        if user_id not in self.conversations or not self.conversations[user_id]:
            return "No conversation history"

        # Create brief summary using AI
        history_text = "\n".join(
            [
                f"{msg['role']}: {msg['content'][:100]}..."
                for msg in self.conversations[user_id][-6:]
            ]
        )

        return f"Recent conversation:\n{history_text}"

    # =========================================================================
    # INKA CLIENT INTERACTION CLASSIFICATION
    # =========================================================================

    def classify_client_message(
        self, client_message: str, client_context: Optional[Dict] = None
    ) -> Dict:
        """
        Classify client message to determine intent and route
        
        Uses INKA classifier to determine:
        - route: booking, consultation, info, etc.
        - booking_type: tattoo, walk-in, consultation
        - confidence: how sure we are about classification
        
        Args:
            client_message: Message from client
            client_context: Optional context (has_active_booking, etc.)
            
        Returns:
            Classification result dict
        """
        client_context = client_context or {}
        return self.inka.process(client_message, client_context)

    def get_client_response(
        self, client_message: str, client_context: Optional[Dict] = None
    ) -> Dict:
        """
        Get AI response to client message (for consultation/info routes)
        
        Args:
            client_message: Message from client
            client_context: Optional context
            
        Returns:
            {
                "response": "AI consultant response",
                "classification": {...},
                "next_action": "offer_slots|continue_consultation|other"
            }
        """
        return self.inka.process(client_message, client_context)

    def should_route_to_booking(self, classification: Dict) -> bool:
        """Check if classification indicates ready to book"""
        return classification["classification"]["route"] in [
            "booking",
            "booking_confirm",
            "booking_reschedule",
        ]

    def get_inka_system_prompts(self) -> Dict[str, str]:
        """Get all INKA system prompts for Make.com integration"""
        return self.inka.get_system_prompts()

