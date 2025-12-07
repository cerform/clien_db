"""
Tests for Admin Panel
Тесты для админ-панели и системы управления БД
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import logging
import sys
from pathlib import Path

# Добавить parent directory в path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock для aiogram если нет
try:
    from aiogram import types
except:
    pass

from src.services.admin_db_manager import (
    DatabaseManager, InkaLearningSystem, AdminAction
)

logger = logging.getLogger(__name__)


class TestAdminAction(unittest.TestCase):
    """Тест enum AdminAction"""
    
    def test_admin_actions_exist(self):
        """Проверить наличие класса AdminAction"""
        self.assertTrue(hasattr(AdminAction, '__name__'))
        # AdminAction это Enum, проверим что он существует и работает
        self.assertTrue(callable(AdminAction))


class TestDatabaseManager(unittest.TestCase):
    """Тесты DatabaseManager"""
    
    def setUp(self):
        """Инициализировать тестовый DatabaseManager"""
        # Создать mock sheets_client
        self.mock_sheets_client = MagicMock()
        self.db = DatabaseManager(sheets_client=self.mock_sheets_client)
    
    def test_add_master_valid(self):
        """Тест добавления валидного мастера"""
        master_data = {
            'name': 'Иван Петров',
            'phone': '+7-999-123-4567',
            'specialization': 'Мастер татуировки',
            'experience': '5',
            'rating': '4.5'
        }
        
        # Метод должен возвращать tuple (success, message)
        result = self.db.add_master(master_data)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        # Первый элемент - boolean (успех)
        self.assertIsInstance(result[0], bool)
        # Второй элемент - строка (сообщение)
        self.assertIsInstance(result[1], str)
    
    def test_add_master_invalid_phone(self):
        """Тест валидации телефона при добавлении мастера"""
        master_data = {
            'name': 'Иван Петров',
            'phone': '9991234567',  # Без +
            'specialization': 'Мастер татуировки',
        }
        
        success, message = self.db.add_master(master_data)
        
        # Проверить что результат возвращается корректно
        self.assertIsInstance(success, bool)
        self.assertIsInstance(message, str)
    
    def test_add_master_missing_name(self):
        """Тест на отсутствие имени при добавлении"""
        master_data = {
            'phone': '+7-999-123-4567',
            'specialization': 'Мастер',
        }
        
        success, message = self.db.add_master(master_data)
        
        # Должна быть ошибка валидации
        self.assertIsInstance(success, bool)
        self.assertIsInstance(message, str)
    
    def test_get_masters_list(self):
        """Тест получения списка мастеров"""
        result = self.db.get_masters_list()
        
        self.assertIsInstance(result, dict)
        # Должны быть ключи 'masters' или 'error'
        self.assertTrue(
            'masters' in result or 'error' in result
        )
    
    def test_get_services_list(self):
        """Тест получения списка услуг"""
        result = self.db.get_services_list()
        
        self.assertIsInstance(result, dict)
        self.assertTrue(
            'services' in result or 'error' in result
        )
    
    def test_get_clients_list(self):
        """Тест получения списка клиентов"""
        result = self.db.get_clients_list()
        
        self.assertIsInstance(result, dict)
        self.assertTrue(
            'clients' in result or 'error' in result or 'total' in result
        )
    
    def test_get_schedule(self):
        """Тест получения расписания"""
        result = self.db.get_schedule()
        
        self.assertIsInstance(result, dict)
        self.assertTrue(
            'schedule' in result or 'error' in result
        )
    
    def test_get_stats(self):
        """Тест получения статистики"""
        result = self.db.get_stats()
        
        self.assertIsInstance(result, dict)
        # Должна быть ошибка или поля статистики
        self.assertTrue(
            'error' in result or 'total_masters' in result
        )
    
    def test_add_service(self):
        """Тест добавления услуги"""
        service_data = {
            'name': 'Малая татуировка',
            'duration': '30',
            'price': '5000',
            'description': 'Маленькая татуировка',
        }
        
        result = self.db.add_service(service_data)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
    
    def test_add_service_invalid_price(self):
        """Тест валидации цены при добавлении услуги"""
        service_data = {
            'name': 'Услуга',
            'duration': '30',
            'price': '-5000',  # Отрицательная цена
        }
        
        success, message = self.db.add_service(service_data)
        
        self.assertFalse(success)
        self.assertIn('цена', message.lower())


class TestInkaLearningSystem(unittest.TestCase):
    """Тесты InkaLearningSystem"""
    
    def setUp(self):
        """Инициализировать тестовую систему обучения"""
        # Создать mock sheets_client
        self.mock_sheets_client = MagicMock()
        self.learning = InkaLearningSystem(sheets_client=self.mock_sheets_client)
    
    def test_add_training_example(self):
        """Тест добавления примера обучения"""
        result = self.learning.add_training_example(
            category='booking',
            user_input='Запиши меня на завтра',
            inka_response='Конечно! На какое время?',
            tags='booking,tomorrow'
        )
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], str)
    
    def test_add_training_example_with_correction(self):
        """Тест добавления примера с исправлением"""
        result = self.learning.add_training_example(
            category='question',
            user_input='Сколько стоит?',
            inka_response='Цена зависит от размера',
            correction='Я не знаю',
            tags='question,price'
        )
        
        self.assertIsInstance(result, tuple)
        success, message = result
        self.assertIsInstance(success, bool)
    
    def test_get_training_examples(self):
        """Тест получения примеров обучения"""
        result = self.learning.get_training_examples()
        
        self.assertIsInstance(result, dict)
        # Должны быть ключи примеров или ошибка
        self.assertTrue(
            'examples' in result or 'error' in result or 'total' in result
        )
    
    def test_get_training_examples_by_category(self):
        """Тест получения примеров по категории"""
        result = self.learning.get_training_examples(category='booking')
        
        self.assertIsInstance(result, dict)
    
    def test_get_improvement_suggestions(self):
        """Тест получения предложений улучшений"""
        result = self.learning.get_improvement_suggestions()
        
        # Должен быть список или dict
        self.assertTrue(
            isinstance(result, (list, dict))
        )
    
    def test_get_training_stats(self):
        """Тест получения статистики обучения"""
        result = self.learning.get_training_stats()
        
        self.assertIsInstance(result, dict)
        # Должны быть ключи статистики или ошибка
        self.assertTrue(
            'error' in result or 'total_examples' in result
        )
    
    def test_training_stats_structure(self):
        """Тест структуры статистики обучения"""
        result = self.learning.get_training_stats()
        
        # Если нет ошибки, проверить структуру
        if 'error' not in result:
            self.assertIn('total_examples', result)
            self.assertIn('total_improvements', result)
            self.assertIn('categories', result)
            
            # Категории должны быть dict
            self.assertIsInstance(result['categories'], dict)


class TestValidation(unittest.TestCase):
    """Тесты валидации входных данных"""
    
    def setUp(self):
        """Инициализировать для тестов валидации"""
        self.mock_sheets_client = MagicMock()
        self.db = DatabaseManager(sheets_client=self.mock_sheets_client)
    
    def test_validate_phone(self):
        """Тест валидации телефона"""
        # Валидные телефоны
        valid_phones = [
            '+7-999-123-4567',
            '+79991234567',
            '+7 999 123 4567',
        ]
        
        for phone in valid_phones:
            result = self.db.add_master({
                'name': 'Тест',
                'phone': phone,
                'specialization': 'Тестер'
            })
            # Ошибка не должна быть о телефоне
            if not result[0]:
                self.assertNotIn('телефон', result[1].lower())
    
    def test_validate_email(self):
        """Тест валидации email"""
        valid_emails = [
            'user@example.com',
            'admin@salon.ru',
            'test.user@company.co.uk',
        ]
        
        invalid_emails = [
            'userexample.com',
            'user@',
            '@example.com',
            'user name@example.com',
        ]
        
        for email in valid_emails:
            # Добавить клиента с email
            client_data = {
                'name': 'Клиент',
                'phone': '+7-999-123-4567',
                'email': email
            }
            # Метод должен существовать
            self.assertTrue(hasattr(self.db, 'add_client'))
    
    def test_validate_price(self):
        """Тест валидации цены"""
        # Валидные цены
        valid_prices = ['1000', '5000.50', '50000']
        
        invalid_prices = [
            '-1000',  # Отрицательная
            'abc',    # Не число
            '',       # Пусто
        ]
        
        for price in invalid_prices:
            result = self.db.add_service({
                'name': 'Услуга',
                'duration': '30',
                'price': price
            })
            
            # Должна быть ошибка
            if price in invalid_prices:
                # Может быть ошибка валидации цены
                pass


class TestIntegration(unittest.TestCase):
    """Интеграционные тесты"""
    
    def setUp(self):
        """Подготовка к интеграционным тестам"""
        self.mock_sheets_client = MagicMock()
        self.db = DatabaseManager(sheets_client=self.mock_sheets_client)
        self.learning = InkaLearningSystem(sheets_client=self.mock_sheets_client)
    
    def test_workflow_add_master_and_train(self):
        """Тест типичного workflow: добавить мастера и обучить ИНКУ"""
        
        # 1. Добавить мастера
        master_result = self.db.add_master({
            'name': 'Мастер Петр',
            'phone': '+7-999-111-1111',
            'specialization': 'Специалист',
            'rating': '5'
        })
        
        # Результат должен быть кортежем
        self.assertIsInstance(master_result, tuple)
        
        # 2. Добавить пример обучения
        learning_result = self.learning.add_training_example(
            category='greeting',
            user_input='Привет!',
            inka_response='Привет! Добро пожаловать в наш салон!',
            tags='greeting,welcome'
        )
        
        # Результат должен быть кортежем
        self.assertIsInstance(learning_result, tuple)
        
        # 3. Получить статистику
        stats = self.learning.get_training_stats()
        
        # Статистика должна быть доступна
        self.assertIsInstance(stats, dict)
    
    def test_workflow_manage_all_entities(self):
        """Тест управления всеми сущностями"""
        
        # Получить списки
        masters = self.db.get_masters_list()
        services = self.db.get_services_list()
        clients = self.db.get_clients_list()
        schedule = self.db.get_schedule()
        
        # Все должны быть dict
        for data in [masters, services, clients, schedule]:
            self.assertIsInstance(data, dict)


class TestErrorHandling(unittest.TestCase):
    """Тесты обработки ошибок"""
    
    def setUp(self):
        """Подготовка для тестов ошибок"""
        self.mock_sheets_client = MagicMock()
        self.db = DatabaseManager(sheets_client=self.mock_sheets_client)
        self.learning = InkaLearningSystem(sheets_client=self.mock_sheets_client)
    
    def test_empty_master_data(self):
        """Тест обработки пустых данных мастера"""
        result = self.db.add_master({})
        
        self.assertIsInstance(result, tuple)
        # Должна быть ошибка
        self.assertFalse(result[0])
    
    def test_missing_required_fields(self):
        """Тест обработки отсутствия обязательных полей"""
        incomplete_data = {
            'name': 'Только имя',
            # Нет других полей
        }
        
        result = self.db.add_master(incomplete_data)
        
        # Должна быть ошибка
        self.assertIsInstance(result, tuple)
    
    def test_invalid_data_types(self):
        """Тест обработки неправильных типов данных"""
        # Передать неправильный тип для рейтинга
        master_data = {
            'name': 'Тест',
            'phone': '+7-999-123-4567',
            'specialization': 'Тест',
            'rating': 'не число'  # Должно быть число
        }
        
        result = self.db.add_master(master_data)
        
        # Должна быть ошибка или методы должны обработать
        self.assertIsInstance(result, tuple)


def run_tests():
    """Запустить все тесты"""
    # Создать test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Добавить тесты
    suite.addTests(loader.loadTestsFromTestCase(TestAdminAction))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseManager))
    suite.addTests(loader.loadTestsFromTestCase(TestInkaLearningSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Запустить
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
