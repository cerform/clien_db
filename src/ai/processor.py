"""
Модуль для обработки текста пользователя через LLM
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIProcessor:
    """Обработчик текста через OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация AI процессора
        
        Args:
            api_key: API ключ для OpenAI. Если не указан, берёт из переменной окружения
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. AI features will be limited.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
        
        # Инструкции для LLM на русском
        self.system_prompt = """Ты ассистент для тату-салона. 
        
Твоя задача:
1. Распознавать намерения пользователя из его текста
2. Извлекать релевантную информацию (дату, время, имя мастера и т.д.)
3. Возвращать структурированный ответ в JSON

Возможные типы действий:
- "booking" - запись на процедуру (параметры: date, time, master, procedure)
- "profile_view" - просмотр профиля (параметры: master_name)
- "masters_list" - список мастеров
- "cancel_booking" - отмена записи (параметры: booking_id)
- "my_bookings" - мои записи
- "general_question" - общий вопрос (параметры: question)

Ответ должен быть JSON с полями:
{
    "action": "action_type",
    "confidence": 0-100,
    "parameters": {...},
    "response": "Ответ пользователю на русском"
}

Если уверенность < 50%, установи action="general_question"."""
    
    async def process_message(self, user_message: str, user_id: int) -> Dict:
        """
        Обработать сообщение пользователя через LLM
        
        Args:
            user_message: Текст сообщения от пользователя
            user_id: ID пользователя в Telegram
            
        Returns:
            Словарь с результатом обработки
        """
        if not self.client:
            logger.warning("AI client not initialized")
            return {
                "action": "general_question",
                "confidence": 0,
                "parameters": {"question": user_message},
                "response": f"Вы написали: {user_message}\n\nПолная функциональность требует настройки OpenAI API"
            }
        
        try:
            # Запрос к OpenAI
            response = await self._call_openai(user_message)
            
            # Парсим ответ
            result = self._parse_response(response)
            logger.info(f"User {user_id}: action={result['action']}, confidence={result['confidence']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "action": "error",
                "confidence": 0,
                "parameters": {},
                "response": f"Ошибка обработки: {str(e)}"
            }
    
    async def _call_openai(self, message: str) -> str:
        """Вызов OpenAI API"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content
    
    def _parse_response(self, response_text: str) -> Dict:
        """Парсим JSON ответ от LLM"""
        try:
            # Пытаемся найти JSON в ответе
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                
                # Убедимся, что есть все нужные поля
                return {
                    "action": data.get("action", "general_question"),
                    "confidence": data.get("confidence", 0),
                    "parameters": data.get("parameters", {}),
                    "response": data.get("response", response_text)
                }
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response from LLM")
        
        # Если не получилось распарсить, возвращаем как общий вопрос
        return {
            "action": "general_question",
            "confidence": 0,
            "parameters": {"question": response_text},
            "response": response_text
        }
    
    def get_action_response(self, action_result: Dict) -> str:
        """
        Получить ответ для пользователя на основе результата обработки
        
        Args:
            action_result: Результат обработки от process_message
            
        Returns:
            Строка с ответом для пользователя
        """
        action = action_result.get("action", "general_question")
        response = action_result.get("response", "")
        confidence = action_result.get("confidence", 0)
        
        # Добавляем уверенность если она низкая
        if confidence < 50:
            response += f"\n\n⚠️ Я не совсем понял ваш запрос (уверенность: {confidence}%). Пожалуйста, уточните."
        
        return response


# Глобальный экземпляр AI процессора
_ai_processor: Optional[AIProcessor] = None

def get_ai_processor() -> AIProcessor:
    """Получить или создать экземпляр AI процессора"""
    global _ai_processor
    if _ai_processor is None:
        _ai_processor = AIProcessor()
    return _ai_processor
