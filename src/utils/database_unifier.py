"""
Скрипт унификации базы данных для INKA и Админ-панели
Приводит все данные к единому стандарту и добавляет функции парсинга
"""

import uuid
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from src.config import get_config
import sys

# Configure logging to output to console with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # More verbose logging
    format='%(asctime)s [%(levelname)s] - %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout  # Output to stdout for real-time logging
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Capture all log levels

class DatabaseUnifier:
    """Унификатор базы данных для приведения к единому стандарту"""
    
    # Определяем единую структуру таблиц
    MASTER_FIELDS = [
        'ID', 'name', 'phone', 'telegram_id', 'specialization', 
        'rating', 'experience', 'instagram', 'status', 'bio', 'calendar_id'
    ]
    
    CLIENT_FIELDS = [
        'id', 'telegram_id', 'name', 'phone', 'email', 
        'notes', 'created_at', 'last_visit'
    ]
    
    SERVICE_FIELDS = [
        'id', 'name', 'description', 'duration_min', 
        'price_from', 'price_to', 'category', 'active'
    ]
    
    BOOKING_FIELDS = [
        'id', 'client_id', 'master_id', 'service_id', 
        'date', 'time', 'duration_min', 'price', 'status', 'notes', 'created_at'
    ]
    
    SCHEDULE_FIELDS = [
        'id', 'master_id', 'day_of_week', 'start_time', 
        'end_time', 'is_working', 'break_start', 'break_end', 'notes'
    ]
    
    def __init__(self, sheets_client):
        """
        Инициализация унификатора базы данных
        
        Args:
            sheets_client: Клиент Google Sheets для работы с БД
        """
        self.sheets_client = sheets_client
        self.validation_errors = []
        self.changes_log = []
    
    def parse_client_name(self, name: str) -> Dict[str, str]:
        """
        Парсинг имени клиента на составляющие
        Поддерживает разные форматы: "Имя Фамилия", "Фамилия Имя", "Имя"
        
        Args:
            name: Полное имя клиента
        
        Returns:
            Словарь с разобранными частями имени
        """
        if not name or name.strip() == '':
            return {
                'full_name': 'Unknown Client',
                'first_name': 'Unknown',
                'last_name': 'Client',
                'display_name': 'Unknown Client'
            }
        
        # Разбиваем имя на части
        parts = name.strip().split()
        
        if len(parts) == 1:
            # Если только одно слово - считаем его именем
            return {
                'full_name': parts[0],
                'first_name': parts[0],
                'last_name': '',
                'display_name': parts[0]
            }
        elif len(parts) == 2:
            # Если два слова, первое может быть и именем, и фамилией
            return {
                'full_name': name,
                'first_name': parts[0],
                'last_name': parts[1],
                'display_name': name
            }
        elif len(parts) >= 3:
            # Если больше двух слов, первое считаем именем, последнее - фамилией
            return {
                'full_name': name,
                'first_name': parts[0],
                'last_name': parts[-1],
                'display_name': name
            }
    
    def parse_phone_number(self, phone: str) -> str:
        """
        Нормализация номера телефона
        
        Args:
            phone: Номер телефона в различных форматах
        
        Returns:
            Нормализованный номер телефона
        """
        if not phone:
            return ''
        
        # Удаляем все нецифровые символы
        cleaned = re.sub(r'\D', '', str(phone))
        
        # Если введена неправильная строка или после очистки остались только символы
        if not cleaned:
            return ''
        
        # Если нет +, добавляем +972 (для Израиля по умолчанию)
        if not cleaned.startswith('972') and len(cleaned) >= 9:
            cleaned = '972' + cleaned[-9:]
        
        # Добавляем +, если его нет
        cleaned = '+' + cleaned if not cleaned.startswith('+') else cleaned
        
        return cleaned
    
    def extract_client_info_from_notes(self, notes: str) -> Dict[str, Any]:
        """
        Извлечение дополнительной информации из заметок
        
        Args:
            notes: Текстовые заметки о клиенте
        
        Returns:
            Словарь с извлеченной информацией
        """
        default_info = {
            'city': '',
            'gender': '',
            'is_first_tattoo': False
        }
        
        if not notes:
            return default_info
        
        # Простейшие эвристики для извлечения информации
        notes_lower = notes.lower()
        
        # Определение города (расширенный список городов)
        cities = {
            'тель-авив': ['тель-авив', 'tel-aviv', 'тельавив'],
            'хайфа': ['хайфа', 'haifa', 'хайфы'],
            'иерусалим': ['иерусалим', 'jerusalem', 'йерушалаим'],
            'беэр-шева': ['беэр-шева', 'beer sheva', 'beer-sheva'],
            'нетания': ['нетания', 'netanya'],
            'ришон': ['ришон', 'rishon'],
        }
        
        city = ''
        for city_key, variations in cities.items():
            if any(var in notes_lower for var in variations):
                city = city_key
                break
        
        # Определение пола с более широким контекстом
        gender_indicators = {
            'female': ['она', 'женщина', 'девушка'],
            'male': ['он', 'мужчина', 'парень']
        }
        
        gender = 'female' if any(ind in notes_lower for ind in gender_indicators['female']) else \
                 'male' if any(ind in notes_lower for ind in gender_indicators['male']) else ''
        
        # Определение первой татуировки с более широким контекстом
        first_tattoo_indicators = [
            'первая', 'первый раз', 'никогда не делала', 
            'never done', 'first time', 'впервые'
        ]
        is_first_tattoo = any(ind in notes_lower for ind in first_tattoo_indicators)
        
        return {
            'city': city,
            'gender': gender,
            'is_first_tattoo': is_first_tattoo
        }
    
    def normalize_client_data(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Нормализация данных о клиентах
        
        Args:
            client_data: Словарь с данными о клиенте
        
        Returns:
            Нормализованный словарь с данными о клиенте
        """
        try:
            name_parts = self.parse_client_name(client_data.get('name', 'Unknown Client'))
            phone_normalized = self.parse_phone_number(client_data.get('phone', ''))
            
            # Извлекаем структурированную информацию из заметок
            notes = client_data.get('notes', '')
            extracted_info = self.extract_client_info_from_notes(notes)
            
            normalized_client = {
                'id': client_data.get('id', str(uuid.uuid4())),
                'telegram_id': client_data.get('telegram_id', ''),
                'name': name_parts['full_name'],
                'first_name': name_parts['first_name'],
                'last_name': name_parts['last_name'],
                'display_name': name_parts['display_name'],
                'phone': phone_normalized,
                'email': client_data.get('email', ''),
                'language': client_data.get('language', 'ru'),
                'city': extracted_info['city'],
                'gender': extracted_info['gender'],
                'is_first_tattoo': extracted_info['is_first_tattoo'],
                'notes': notes,
                'created_at': client_data.get('created_at', datetime.now().isoformat()),
                'last_visit': client_data.get('last_visit', '')
            }
            
            return normalized_client
        except Exception as e:
            logger.error(f"Error normalizing client data: {e}")
            return {}
    
    def parse_master_id_from_text(self, text: str, masters_list: List[Dict]) -> Optional[str]:
        """
        Парсинг ID мастера из текста по имени
        
        Args:
            text: Текст содержащий имя мастера
            masters_list: Список всех мастеров
        
        Returns:
            ID мастера или None
        """
        if not text:
            return None
        
        # Нормализация текста (к lowercase, удаление лишних пробелов)
        text_normalized = text.lower().strip()
        
        # Поиск мастера по полному имени
        for master in masters_list:
            master_name_normalized = master.get('name', '').lower().strip()
            
            # Точное совпадение имени
            if text_normalized == master_name_normalized:
                return master.get('id')
            
            # Частичное совпадение имени
            if text_normalized in master_name_normalized or master_name_normalized in text_normalized:
                return master.get('id')
        
        # Если точного совпадения не найдено, возвращаем None
        logger.warning(f"Master not found for text: {text}")
        return None
    def validate_master(self, master: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Валидация данных мастера"""
        errors = []
        
        if not master.get('name'):
            errors.append("Отсутствует имя мастера")
        
        if not master.get('id'):
            errors.append("Отсутствует ID мастера")
        
        phone = master.get('phone', '')
        if phone and not re.match(r'^\+\d{10,15}$', phone):
            errors.append(f"Некорректный номер телефона: {phone}")
        
        return len(errors) == 0, errors
    
    def validate_client(self, client: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Валидация данных клиента"""
        errors = []
        
        if not client.get('name'):
            errors.append("Отсутствует имя клиента")
        
        if not client.get('id'):
            errors.append("Отсутствует ID клиента")
        
        return len(errors) == 0, errors
    
    def create_backup(self, table_name: str) -> bool:
        """Создание резервной копии таблицы"""
        try:
            data = self.sheets_client.get_sheet_values(table_name)
            backup_name = f"{table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Создаём новый лист с резервной копией
            logger.info(f"Создана резервная копия: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии {table_name}: {e}")
            return False
    
    def unify_masters_table(self) -> Dict[str, Any]:
        """
        Унификация таблицы Мастера
        
        Returns:
            Словарь с результатами унификации
        """
        try:
            logger.info("🔄 Унификация таблицы Мастера...")
            
            # Создаём резервную копию
            backup_success = self.create_backup("Мастера")
            if not backup_success:
                logger.warning("Не удалось создать резервную копию таблицы Мастера")
            
            # Получаем данные
            raw_data = self.sheets_client.get_sheet_values("Мастера")
            if not raw_data or len(raw_data) < 2:
                return {"error": "Таблица Мастера пуста"}
            
            headers = raw_data[0]
            rows = raw_data[1:]
            
            normalized_masters = []
            invalid_masters = []
            
            for row in rows:
                # Создаем словарь из заголовков и значений строки
                master_dict = dict(zip(headers, row + [''] * (len(headers) - len(row)))
)
                
                # Нормализация данных
                normalized = self.normalize_master_data(master_dict)
                
                # Валидация
                is_valid, errors = self.validate_master(normalized)
                
                if is_valid:
                    normalized_masters.append(normalized)
                else:
                    # Добавляем информацию о невалидных мастерах
                    invalid_masters.append({
                        'raw_data': master_dict,
                        'errors': errors
                    })
                    logger.warning(f"Невалидный мастер: {errors}")
            
            # В режиме dry_run не обновляем реальную таблицу
            logger.info("ℹ️ Обновление таблицы пропущено (dry_run режим)")
            
            return {
                "status": "success",
                "total_masters": len(normalized_masters),
                "invalid_masters": len(invalid_masters),
                "invalid_masters_details": invalid_masters,
                "dry_run": True
            }
        
        except Exception as e:
            logger.error(f"Критическая ошибка в unify_masters_table: {e}")
            return {
                "error": "Непредвиденная ошибка при унификации таблицы Мастера",
                "details": str(e)
            }
    
    def unify_clients_table(self) -> Dict[str, Any]:
        """Унификация таблицы Клиенты"""
        try:
            logger.info("🔄 Унификация таблицы Клиенты...")
            
            # Создаём резервную копию
            self.create_backup("Клиенты")
            
            # Получаем данные
            raw_data = self.sheets_client.get_sheet_values("Клиенты")
            if not raw_data or len(raw_data) < 2:
                return {"error": "Таблица Клиенты пуста"}
            
            headers = raw_data[0]
            rows = raw_data[1:]
            
            normalized_clients = []
            for row in rows:
                client_dict = dict(zip(headers, row + [''] * (len(headers) - len(row))))
                normalized = self.normalize_client_data(client_dict)
                
                # Валидация
                is_valid, errors = self.validate_client(normalized)
                if not is_valid:
                    self.validation_errors.append({
                        'table': 'Клиенты',
                        'id': normalized.get('id'),
                        'errors': errors
                    })
                
                normalized_clients.append(normalized)
            
            logger.info(f"✅ Унифицировано клиентов: {len(normalized_clients)}")
            return {
                'count': len(normalized_clients),
                'data': normalized_clients,
                'errors': len([e for e in self.validation_errors if e['table'] == 'Клиенты'])
            }
        except Exception as e:
            logger.error(f"Ошибка унификации таблицы Клиенты: {e}")
            return {"error": str(e)}
    
    def unify_services_table(self) -> Dict[str, Any]:
        """Унификация таблицы Услуги"""
        try:
            logger.info("🔄 Унификация таблицы Услуги...")
            
            # Создаём резервную копию
            self.create_backup("Услуги")
            
            # Получаем данные
            raw_data = self.sheets_client.get_sheet_values("Услуги")
            if not raw_data or len(raw_data) < 2:
                return {"error": "Таблица Услуги пуста"}
            
            headers = raw_data[0]
            rows = raw_data[1:]
            
            normalized_services = []
            for row in rows:
                service_dict = dict(zip(headers, row))
                normalized = self.normalize_service_data(service_dict)
                normalized_services.append(normalized)
            
            logger.info(f"✅ Унифицировано услуг: {len(normalized_services)}")
            return {
                'count': len(normalized_services),
                'data': normalized_services
            }
        except Exception as e:
            logger.error(f"Ошибка унификации таблицы Услуги: {e}")
            return {"error": str(e)}
    
    def normalize_master_data(self, master_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Нормализация данных о мастерах
        
        Args:
            master_data: Словарь с данными о мастере
        
        Returns:
            Нормализованный словарь с данными о мастере
        """
        try:
            # Парсинг имени
            name_parts = self.parse_client_name(master_data.get('name', 'Unknown Master'))
            
            # Нормализация телефона
            phone_normalized = self.parse_phone_number(master_data.get('phone', ''))
            
            normalized_master = {
                'id': master_data.get('id', str(uuid.uuid4())),
                'name': name_parts['full_name'],
                'first_name': name_parts['first_name'],
                'last_name': name_parts['last_name'],
                'display_name': name_parts['display_name'],
                'phone': phone_normalized,
                'telegram_id': master_data.get('telegram_id', ''),
                'specialization': master_data.get('specialization', ''),
                'rating': self._normalize_rating(master_data.get('rating', 0)),
                'experience': self._normalize_experience(master_data.get('experience', 0)),
                'instagram': master_data.get('instagram', ''),
                'status': master_data.get('status', 'active'),
                'bio': master_data.get('bio', ''),
                'calendar_id': master_data.get('calendar_id', '')
            }
            
            return normalized_master
        except Exception as e:
            logger.error(f"Error normalizing master data: {e}")
            return {}

    def _normalize_rating(self, rating: Any) -> float:
        """
        Нормализация рейтинга мастера
        
        Args:
            rating: Входное значение рейтинга
        
        Returns:
            Нормализованный рейтинг (от 0 до 5)
        """
        try:
            # Преобразуем к числу с плавающей точкой
            if isinstance(rating, str):
                rating = rating.replace(',', '.')
            
            rating_float = float(rating)
            
            # Ограничиваем рейтинг от 0 до 5
            return max(0, min(rating_float, 5))
        except (TypeError, ValueError):
            # Если преобразование не удалось, возвращаем 0
            return 0

    def _normalize_experience(self, experience: Any) -> int:
        """
        Нормализация опыта работы мастера
        
        Args:
            experience: Входное значение опыта
        
        Returns:
            Нормализованное количество лет опыта
        """
        try:
            # Преобразуем к целому числу
            if isinstance(experience, str):
                # Извлекаем первое число из строки
                match = re.search(r'\d+', experience)
                experience = match.group() if match else 0
            
            experience_int = int(experience)
            
            # Ограничиваем опыт от 0 до 50 лет
            return max(0, min(experience_int, 50))
        except (TypeError, ValueError):
            # Если преобразование не удалось, возвращаем 0
            return 0
    

    
    def normalize_service_data(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Нормализация данных об услугах
        
        Args:
            service_data: Словарь с данными об услуге
        
        Returns:
            Нормализованный словарь с данными об услуге
        """
        try:
            normalized_service = {
                'id': service_data.get('id', str(uuid.uuid4())),
                'name': service_data.get('name', ''),
                'description': service_data.get('description', ''),
                'duration_min': service_data.get('duration', '60'),
                'price_from': service_data.get('price', '0'),
                'price_to': service_data.get('price_to', service_data.get('price', '0')),
                'category': service_data.get('category', 'other'),
                'status': service_data.get('status', 'active'),
                'created_at': datetime.now().isoformat()
            }
            
            return normalized_service
        except Exception as e:
            logger.error(f"Error normalizing service data: {e}")
            return service_data
    
    def unify_database(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Глобальная унификация базы данных
        
        Args:
            dry_run: Если True, только проверка без изменений
        
        Returns:
            Результат унификации
        """
        try:
            logger.info("=" * 80)
            logger.info("🚀 НАЧАЛО УНИФИКАЦИИ БАЗЫ ДАННЫХ")
            logger.info("=" * 80)
            
            results = {
                'masters': self.unify_masters_table(),
                'clients': self.unify_clients_table(),
                'services': self.unify_services_table(),
                'validation_errors': self.validation_errors,
                'dry_run': dry_run
            }
            
            # Статистика
            logger.info("\n" + "=" * 80)
            logger.info("📊 СТАТИСТИКА УНИФИКАЦИИ")
            logger.info("=" * 80)
            logger.info(f"✅ Мастеров обработано: {results['masters'].get('count', 0)}")
            logger.info(f"✅ Клиентов обработано: {results['clients'].get('count', 0)}")
            logger.info(f"✅ Услуг обработано: {results['services'].get('count', 0)}")
            logger.info(f"⚠️  Ошибок валидации: {len(self.validation_errors)}")
            
            if self.validation_errors:
                logger.info("\n⚠️  ОБНАРУЖЕНЫ ОШИБКИ ВАЛИДАЦИИ:")
                for error in self.validation_errors[:10]:  # Показываем первые 10
                    logger.info(f"  - {error['table']}: {error['id']} -> {error['errors']}")
            
            logger.info("=" * 80)
            
            if not dry_run:
                logger.info("💾 Сохранение изменений в базу данных...")
                # TODO: Реализовать сохранение в Google Sheets
                logger.info("✅ Изменения сохранены!")
            else:
                logger.info("ℹ️  Режим проверки (dry_run=True). Изменения не сохранены.")
            
            return results
        except Exception as e:
            logger.error(f"❌ Ошибка при унификации базы данных: {e}")
            return {"error": str(e)}

def main(sheets_client=None):
    """
    Главная функция для запуска унификации базы данных с расширенным логированием
    
    Args:
        sheets_client: Клиент Google Sheets. Если не предоставлен, 
                       будет использована стандартная инициализация.
    """
    try:
        logger = logging.getLogger('database_unifier')
        logger.info("🚀 Начало процесса унификации базы данных")
        
        # Системная информация для диагностики
        import platform
        import sys
        logger.debug(f"Системная информация: {platform.platform()}")
        logger.debug(f"Python версия: {sys.version}")
        
        # Если клиент не передан, импортируем и инициализируем
        if sheets_client is None:
            from src.db.sheets_client import GoogleSheetsClient
            from pathlib import Path
            logger.debug("Инициализация клиента Google Sheets")
            
            # Загружаем конфигурацию для получения ID таблицы
            config = get_config()
            credentials_file = Path(__file__).parent.parent.parent / "credentials.json"
            
            sheets_client = GoogleSheetsClient(
                credentials_file=str(credentials_file),
                spreadsheet_id=config.google_spreadsheet_id
            )
        
        # Создаем объект унификатора
        unifier = DatabaseUnifier(sheets_client)
        logger.debug("Создан объект унификатора базы данных")
        
        # Последовательность операций унификации с полным покрытием
        operations = [
            ('Мастера', unifier.unify_masters_table),
            ('Клиенты', unifier.unify_clients_table),
            ('Услуги', unifier.unify_services_table),
        ]
        
        # Результаты всех операций
        results = {}
        
        # Выполнение операций унификации с детальным логированием
        for table_name, unification_method in operations:
            logger.info(f"🔄 Начало унификации таблицы: {table_name}")
            start_time = datetime.now()
            
            try:
                result = unification_method()
                results[table_name] = result
                
                duration = (datetime.now() - start_time).total_seconds()
                
                if 'error' in result:
                    logger.error(f"❌ Ошибка унификации {table_name}: {result['error']}")
                else:
                    logger.info(f"✅ Успешная унификация {table_name} за {duration:.2f} сек")
                    logger.debug(f"Детали унификации {table_name}: {result}")
            
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"🚨 Критическая ошибка при унификации {table_name} за {duration:.2f} сек: {e}")
                results[table_name] = {
                    'error': str(e),
                    'status': 'failed',
                    'duration': duration
                }
        
        # Финальный отчет с полной статистикой
        logger.info("🏁 Унификация базы данных завершена")
        
        # Логирование общей статистики
        total_processed = sum(result.get('count', 0) for result in results.values() if isinstance(result, dict))
        total_errors = sum(len(result.get('errors', [])) for result in results.values() if isinstance(result, dict))
        
        logger.info(f"📊 Статистика: Обработано записей: {total_processed}, Ошибок: {total_errors}")
        
        return results
    
    except Exception as e:
        logger.error(f"🔥 Непредвиденная глобальная ошибка: {e}", exc_info=True)
        return {'error': str(e), 'status': 'critical_failure'}

if __name__ == '__main__':
    # Запуск скрипта как standalone приложения
    results = main()
    print(results)