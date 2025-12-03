"""AI-powered tattoo consultation service"""
import logging
import json
from typing import Dict, List
import openai

logger = logging.getLogger(__name__)

class AIConsultant:
    """AI consultant for tattoo consultation and booking details"""
    
    def __init__(self, api_key: str):
        """Initialize with OpenAI API key"""
        openai.api_key = api_key
        self.model = "gpt-3.5-turbo"
        self.consultation_history = {}
    
    def get_tattoo_consultation(self, user_id: int, user_message: str, consultation_context: Dict = None) -> Dict:
        """
        Get AI consultation about tattoo design, size, placement, duration
        
        Args:
            user_id: Telegram user ID
            user_message: User's message/question
            consultation_context: Previous conversation context
            
        Returns:
            {
                "response": "AI response message",
                "estimated_duration": 120,  # minutes
                "type": "consultation|design|placement|size",
                "details": {...}
            }
        """
        try:
            # Initialize user history if needed
            if user_id not in self.consultation_history:
                self.consultation_history[user_id] = []
            
            # Build system prompt
            system_prompt = self._build_system_prompt()
            
            # Add user message to history
            self.consultation_history[user_id].append({
                "role": "user",
                "content": user_message
            })
            
            # Keep only last 10 messages for context
            messages = self.consultation_history[user_id][-10:]
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                temperature=0.7,
                max_tokens=500
            )
            
            assistant_message = response.choices[0].message.content
            
            # Add response to history
            self.consultation_history[user_id].append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Extract structured info from response
            structured_info = self._parse_consultation_response(assistant_message)
            
            return {
                "response": assistant_message,
                "estimated_duration": structured_info.get("duration", 120),
                "tattoo_type": structured_info.get("type", "custom"),
                "placement": structured_info.get("placement", ""),
                "size": structured_info.get("size", "medium"),
                "requires_consultation": structured_info.get("requires_consultation", False)
            }
            
        except Exception as e:
            logger.exception(f"AI consultation error: {e}")
            return {
                "response": "Извините, я не смогу обработать ваш запрос. Пожалуйста, попробуйте позже.",
                "estimated_duration": 120,
                "tattoo_type": "custom",
                "error": str(e)
            }
    
    def estimate_booking_duration(self, tattoo_description: str) -> Dict:
        """
        Estimate how long the tattoo appointment should be
        
        Args:
            tattoo_description: Description of desired tattoo
            
        Returns:
            {
                "min_duration": 60,
                "recommended_duration": 120,
                "max_duration": 240,
                "reason": "explanation"
            }
        """
        try:
            prompt = f"""Based on this tattoo description, estimate the appointment duration in minutes:
            
"{tattoo_description}"

Provide a JSON response with:
- min_duration: minimum minutes needed
- recommended_duration: ideal duration
- max_duration: maximum if very detailed
- reason: brief explanation

Consider factors like complexity, size, number of colors, detail level."""
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content
            
            # Try to parse JSON from response
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
            except:
                pass
            
            # Fallback if JSON parsing fails
            return {
                "min_duration": 60,
                "recommended_duration": 120,
                "max_duration": 240,
                "reason": "Standard tattoo appointment"
            }
            
        except Exception as e:
            logger.exception(f"Duration estimation error: {e}")
            return {
                "min_duration": 60,
                "recommended_duration": 120,
                "max_duration": 240,
                "reason": "Standard appointment"
            }
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for tattoo consultation"""
        return """You are a professional tattoo consultant chatbot. Your role is to:

1. Ask about the client's tattoo ideas and preferences
2. Discuss placement, size, and style
3. Explain time requirements based on complexity
4. Help determine if they need a consultation with the master
5. Suggest tattoo types: small/medium/large, color/black&white, minimalist/detailed
6. Always be friendly and professional

When discussing tattoos, consider:
- Simple small tattoos (30-90 min): names, symbols, small designs
- Medium tattoos (90-180 min): moderate designs with detail
- Large/complex tattoos (180+ min): full pieces, sleeves, detailed work
- Cover-ups: usually 180-300 min
- Consultations: 30 min discussions

Ask clarifying questions about:
- Design ideas or references
- Preferred placement (arm, chest, leg, etc.)
- Size preference (small/medium/large)
- Color vs black & white
- Whether it's their first tattoo

Respond in the user's language. Be encouraging but realistic about time/complexity."""
    
    def _parse_consultation_response(self, response: str) -> Dict:
        """Parse AI response to extract structured information"""
        result = {
            "duration": 120,
            "type": "custom",
            "placement": "",
            "size": "medium",
            "requires_consultation": False
        }
        
        # Check for duration hints
        response_lower = response.lower()
        if "30 min" in response_lower or "полчас" in response_lower:
            result["duration"] = 30
        elif "60 min" in response_lower or "час" in response_lower:
            result["duration"] = 60
        elif "90 min" in response_lower:
            result["duration"] = 90
        elif "180 min" in response_lower or "3 часа" in response_lower:
            result["duration"] = 180
        elif "240 min" in response_lower or "4 часа" in response_lower:
            result["duration"] = 240
        
        # Check for size
        if "маленькая" in response_lower or "small" in response_lower or "tiny" in response_lower:
            result["size"] = "small"
        elif "большая" in response_lower or "large" in response_lower or "huge" in response_lower:
            result["size"] = "large"
        
        # Check if consultation needed
        if "консультация" in response_lower or "consultation" in response_lower or "мастер" in response_lower:
            result["requires_consultation"] = True
        
        return result
    
    def clear_history(self, user_id: int):
        """Clear consultation history for user"""
        if user_id in self.consultation_history:
            del self.consultation_history[user_id]
