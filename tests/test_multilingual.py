#!/usr/bin/env python3
"""
Скрипт для быстрого тестирования многоязычной локализации ИНКА

Тестирует:
1. Определение языка
2. Перевод текста
3. Локализацию БД полей
4. Обработку сообщений middleware
5. Интеграцию с INKA
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from src.services.localization_service import LocalizationService, Language
from src.ai.inka_localization import create_inka_localization_middleware

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultilingualTester:
    """Тестер многоязычной функциональности ИНКА"""
    
    def __init__(self, openai_api_key: str = None):
        """Инициализировать тестер"""
        self.openai_key = openai_api_key
        if openai_api_key:
            self.localization = LocalizationService(openai_api_key)
            self.middleware = create_inka_localization_middleware(openai_api_key)
        else:
            logger.warning("No OpenAI API key provided - translation tests will be skipped")
            self.localization = None
            self.middleware = None
    
    def test_language_detection(self):
        """Тест 1: Определение языка"""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: Language Detection 🌍")
        logger.info("="*70)
        
        test_cases = [
            ("Привет! Хочу тату", Language.RUSSIAN),
            ("Hello, I want a tattoo", Language.ENGLISH),
            ("שלום! אני רוצה קעקוע", Language.HEBREW),
            ("Привет", Language.RUSSIAN),
            ("Hi there", Language.ENGLISH),
            ("שלום", Language.HEBREW),
        ]
        
        for text, expected_lang in test_cases:
            detected = self.localization.detect_language(text)
            status = "✅" if detected == expected_lang else "❌"
            logger.info(f"{status} '{text}' → {detected.value} (expected {expected_lang.value})")
    
    def test_glossary_translation(self):
        """Тест 2: Перевод из глоссария"""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: Glossary Translation 📚")
        logger.info("="*70)
        
        test_terms = [
            ("master", Language.RUSSIAN),
            ("master", Language.HEBREW),
            ("service", Language.RUSSIAN),
            ("piercing", Language.HEBREW),
            ("available", Language.RUSSIAN),
            ("monday", Language.HEBREW),
        ]
        
        for term, lang in test_terms:
            translation = self.localization.glossary.get(term, {}).get(lang.value)
            logger.info(f"  '{term}' → {lang.value}: {translation}")
    
    def test_response_templates(self):
        """Тест 3: Предварительно переведенные ответы"""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: Response Templates 💬")
        logger.info("="*70)
        
        response_keys = ["greeting", "confirm_booking", "no_slots", "too_busy"]
        
        for key in response_keys:
            for lang in [Language.RUSSIAN, Language.ENGLISH, Language.HEBREW]:
                response = self.localization.get_response(key, lang)
                logger.info(f"  {key} ({lang.value}): {response[:60]}...")
    
    def test_middleware_user_language(self):
        """Тест 4: Сохранение языка пользователя"""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: User Language Persistence 👤")
        logger.info("="*70)
        
        # Тест 1: Первое сообщение на русском
        lang1 = self.middleware.get_user_language("user1", "Привет! Как дела?")
        logger.info(f"User1 first message (Russian): {lang1.value}")
        
        # Тест 2: Второе сообщение - должен вспомнить язык
        lang1_again = self.middleware.get_user_language("user1", "")
        logger.info(f"User1 second message (no text): {lang1_again.value} (remembered: {lang1_again == lang1})")
        
        # Тест 3: Другой пользователь на английском
        lang2 = self.middleware.get_user_language("user2", "Hello there!")
        logger.info(f"User2 message (English): {lang2.value}")
        
        # Тест 4: Третий пользователь на иврите
        lang3 = self.middleware.get_user_language("user3", "שלום לך!")
        logger.info(f"User3 message (Hebrew): {lang3.value}")
    
    def test_incoming_message_processing(self):
        """Тест 5: Обработка входящих сообщений"""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: Incoming Message Processing 📨")
        logger.info("="*70)
        
        test_messages = [
            ("user_ru", "Привет! Хочу маленькую тату с надписью"),
            ("user_en", "Hi, I want a small tattoo with text"),
            ("user_he", "שלום! אני רוצה קעקוע קטן עם טקסט"),
        ]
        
        for user_id, message in test_messages:
            result = self.middleware.process_incoming_message(user_id, message)
            logger.info(f"\n  User: {user_id}")
            logger.info(f"  Original: {result['original_message']}")
            logger.info(f"  Language: {result['detected_language'].value}")
    
    def test_database_localization(self):
        """Тест 6: Локализация БД полей"""
        logger.info("\n" + "="*70)
        logger.info("TEST 6: Database Field Localization 🗄️")
        logger.info("="*70)
        
        # Симуляция БД ответа (как если бы пришло из Google Sheets)
        master_data = {
            "id": "master-123",
            "name": "Anna Levi",  # English base
            "name_ru": "Анна Леви",
            "name_en": "Anna Levi",
            "name_he": "אנה לוי",
            "specialization": "Realistic Tattoos",
            "specialization_ru": "Реалистичные татуировки",
            "specialization_en": "Realistic Tattoos",
            "specialization_he": "קעקועים אמיתיים",
            "bio": "Expert in portrait and nature tattoos",
            "bio_ru": "Специалист по портретам и природе",
            "bio_en": "Expert in portrait and nature tattoos",
            "bio_he": "מומחה בדיוקנאות וטבע"
        }
        
        for lang in [Language.RUSSIAN, Language.ENGLISH, Language.HEBREW]:
            localized = self.middleware.localize_database_response(
                master_data,
                lang,
                data_type="master"
            )
            logger.info(f"\n  {lang.value.upper()}:")
            logger.info(f"    name: {localized.get('name')}")
            logger.info(f"    specialization: {localized.get('specialization')}")
            logger.info(f"    bio: {localized.get('bio', '')[:50]}...")
    
    def test_booking_intent_extraction(self):
        """Тест 7: Извлечение намерения бронирования"""
        logger.info("\n" + "="*70)
        logger.info("TEST 7: Booking Intent Extraction 🎯")
        logger.info("="*70)
        
        test_intents = [
            ("Хочу записаться на татуировку", Language.RUSSIAN),
            ("I want to book a piercing", Language.ENGLISH),
            ("אני רוצה הזמנה ליום שני", Language.HEBREW),
            ("Консультация по тату", Language.RUSSIAN),
            ("Free consultation available?", Language.ENGLISH),
        ]
        
        for message, lang in test_intents:
            intent = self.middleware.extract_booking_intent(message, lang)
            logger.info(f"\n  Message ({lang.value}): {message}")
            logger.info(f"    Booking intent: {intent.get('has_booking_intent')}")
            logger.info(f"    Service type: {intent.get('service_type')}")
    
    def test_full_workflow(self):
        """Тест 8: Полный workflow обработки сообщения"""
        logger.info("\n" + "="*70)
        logger.info("TEST 8: Full Message Processing Workflow 🔄")
        logger.info("="*70)
        
        # Симуляция полного workflow
        user_id = "test_user_123"
        user_message = "Привет! Мне нужна консультация по татуировке"
        
        logger.info(f"\n📥 User input: {user_message}")
        
        # Шаг 1: Обработать сообщение
        msg_info = self.middleware.process_incoming_message(user_id, user_message)
        logger.info(f"✓ Language detected: {msg_info['detected_language'].value}")
        logger.info(f"✓ Processed message: {msg_info['processed_message']}")
        
        # Шаг 2: Извлечь намерение
        intent = self.middleware.extract_booking_intent(
            user_message,
            msg_info['detected_language']
        )
        logger.info(f"✓ Booking intent: {intent['has_booking_intent']}")
        logger.info(f"✓ Service type: {intent['service_type']}")
        
        # Шаг 3: Получить локализованный системный промпт
        system_prompt = self.middleware.create_system_prompt_with_localization(
            msg_info['detected_language']
        )
        logger.info(f"✓ System prompt created for {msg_info['detected_language'].value}")
        logger.info(f"  First 100 chars: {system_prompt[:100]}...")
        
        logger.info("\n✅ Full workflow completed successfully!")
    
    def run_all_tests(self):
        """Запустить все тесты"""
        logger.info("\n" + "🎬 STARTING MULTILINGUAL INKA TESTS 🎬".center(70))
        logger.info("=" * 70)
        
        if not self.localization:
            logger.error("❌ Cannot run tests without OpenAI API key")
            logger.info("Set OPENAI_API_KEY environment variable and try again")
            return False
        
        try:
            self.test_language_detection()
            self.test_glossary_translation()
            self.test_response_templates()
            self.test_middleware_user_language()
            self.test_incoming_message_processing()
            self.test_database_localization()
            self.test_booking_intent_extraction()
            self.test_full_workflow()
            
            logger.info("\n" + "=" * 70)
            logger.info("🎉 ALL TESTS COMPLETED SUCCESSFULLY! 🎉".center(70))
            logger.info("=" * 70)
            return True
        
        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)
            return False

def main():
    """Главная функция"""
    import os
    
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        logger.error("❌ OPENAI_API_KEY not set")
        logger.info("Run: export OPENAI_API_KEY=sk-...")
        return 1
    
    tester = MultilingualTester(openai_key)
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
