"""
Вспомогательные функции для работы с базой данных
Используются ИНКОЙ и Админ-панелью для парсинга и обработки данных
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


def parse_master_id(text: str, masters: List[Dict]) -> Optional[str]:
    """
    Находит ID мастера по имени в тексте
    
    Args:
        text: Текст содержащий имя мастера
        masters: Список всех мастеров
    
    Returns:
        ID мастера или None
    
    Example:
        >>> masters = [{'id': 'm_123', 'name': 'Анна Федорова'}]
        >>> parse_master_id('Запись к Анне', masters)
        'm_123'
    """
    if not text or not masters:
        return None
    
    text_lower = text.lower()
    
    # Сначала ищем точное совпадение
    for master in masters:
        name = master.get('name', '').lower()
        if name and name == text_lower:
            return master.get('id')
    
    # Затем ищем частичное совпадение
    for master in masters:
        name = master.get('name', '').lower()
        if name and name in text_lower:
            return master.get('id')
    
    # Ищем по частям имени (первое слово)
    for master in masters:
        name = master.get('name', '').lower()
        if name:
            first_name = name.split()[0] if name.split() else name
            if first_name and first_name in text_lower:
                return master.get('id')
    
    return None


def parse_client_id(identifier: str, clients: List[Dict]) -> Optional[str]:
    """
    Находит ID клиента по имени, телефону или telegram_id
    
    Args:
        identifier: Имя, телефон или telegram_id клиента
        clients: Список всех клиентов
    
    Returns:
        ID клиента или None
    """
    if not identifier or not clients:
        return None
    
    identifier_lower = str(identifier).lower()
    
    for client in clients:
        # Проверяем по имени
        name = client.get('name', '').lower()
        if name and identifier_lower in name:
            return client.get('id')
        
        # Проверяем по телефону
        phone = client.get('phone', '')
        if phone and identifier_lower in phone.lower():
            return client.get('id')
        
        # Проверяем по telegram_id
        telegram_id = str(client.get('telegram_id', ''))
        if telegram_id and telegram_id == identifier_lower:
            return client.get('id')
    
    return None


def format_master_info(master: Dict[str, Any], language: str = 'ru') -> str:
    """
    Форматирует информацию о мастере для отображения
    
    Args:
        master: Словарь с данными мастера
        language: Язык вывода
    
    Returns:
        Форматированная строка с информацией о мастере
    """
    if not master:
        return "Мастер не найден"
    
    name = master.get('name', 'Unknown')
    specialization = master.get('specialization', 'Не указано')
    rating = master.get('rating', '0')
    experience = master.get('experience', '0')
    bio = master.get('bio', '')
    
    if language == 'ru':
        info = f"👨‍🎨 {name}\n"
        info += f"🎨 Специализация: {specialization}\n"
        info += f"⭐ Рейтинг: {rating}\n"
        info += f"📅 Опыт: {experience} лет\n"
        if bio:
            info += f"ℹ️ {bio}"
    else:
        info = f"👨‍🎨 {name}\n"
        info += f"🎨 Specialization: {specialization}\n"
        info += f"⭐ Rating: {rating}\n"
        info += f"📅 Experience: {experience} years"
    
    return info


def format_service_info(service: Dict[str, Any], language: str = 'ru') -> str:
    """
    Форматирует информацию об услуге для отображения
    
    Args:
        service: Словарь с данными услуги
        language: Язык вывода
    
    Returns:
        Форматированная строка с информацией об услуге
    """
    if not service:
        return "Услуга не найдена"
    
    name = service.get('name', 'Unknown')
    duration = service.get('duration_min', '0')
    price_from = service.get('price_from', '0')
    price_to = service.get('price_to', price_from)
    description = service.get('description', '')
    
    if language == 'ru':
        info = f"💼 {name}\n"
        info += f"⏱️ Длительность: {duration} мин\n"
        if price_from == price_to:
            info += f"💰 Цена: ₪{price_from}\n"
        else:
            info += f"💰 Цена: ₪{price_from}-{price_to}\n"
        if description:
            info += f"📝 {description}"
    else:
        info = f"💼 {name}\n"
        info += f"⏱️ Duration: {duration} min\n"
        if price_from == price_to:
            info += f"💰 Price: ₪{price_from}"
        else:
            info += f"💰 Price: ₪{price_from}-{price_to}"
    
    return info


def format_booking_info(booking: Dict[str, Any], 
                       master_name: str = None,
                       client_name: str = None,
                       language: str = 'ru') -> str:
    """
    Форматирует информацию о записи для отображения
    
    Args:
        booking: Словарь с данными записи
        master_name: Имя мастера
        client_name: Имя клиента
        language: Язык вывода
    
    Returns:
        Форматированная строка с информацией о записи
    """
    if not booking:
        return "Запись не найдена"
    
    date = booking.get('date', '')
    time = booking.get('time', '')
    status = booking.get('status', 'pending')
    service = booking.get('service_id', 'Не указано')
    
    status_emoji = {
        'pending': '⏳',
        'confirmed': '✅',
        'completed': '🎉',
        'cancelled': '❌'
    }
    
    if language == 'ru':
        info = f"{status_emoji.get(status, '📝')} Запись\n"
        info += f"📅 Дата: {date}\n"
        info += f"🕐 Время: {time}\n"
        if master_name:
            info += f"👨‍🎨 Мастер: {master_name}\n"
        if client_name:
            info += f"👤 Клиент: {client_name}\n"
        info += f"💼 Услуга: {service}\n"
        info += f"📊 Статус: {status}"
    else:
        info = f"{status_emoji.get(status, '📝')} Booking\n"
        info += f"📅 Date: {date}\n"
        info += f"🕐 Time: {time}\n"
        if master_name:
            info += f"👨‍🎨 Master: {master_name}\n"
        if client_name:
            info += f"👤 Client: {client_name}\n"
        info += f"📊 Status: {status}"
    
    return info


def get_available_time_slots(schedule: List[Dict], 
                             bookings: List[Dict],
                             date: str,
                             duration_min: int = 60) -> List[str]:
    """
    Вычисляет доступные временные слоты для записи
    
    Args:
        schedule: Расписание мастера
        bookings: Существующие записи
        date: Дата в формате YYYY-MM-DD
        duration_min: Требуемая длительность в минутах
    
    Returns:
        Список доступных временных слотов в формате HH:MM
    """
    available_slots = []
    
    # Определяем день недели
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    day_of_week = date_obj.strftime('%A').lower()  # monday, tuesday, etc.
    
    # Находим расписание на этот день
    day_schedule = [s for s in schedule if s.get('day_of_week') == day_of_week]
    
    if not day_schedule:
        return []
    
    for slot in day_schedule:
        if slot.get('is_working', 'false').lower() != 'true':
            continue
        
        start_time = slot.get('start_time', '09:00')
        end_time = slot.get('end_time', '18:00')
        
        # Генерируем слоты с шагом в duration_min
        current = datetime.strptime(start_time, '%H:%M')
        end = datetime.strptime(end_time, '%H:%M')
        
        while current < end:
            time_str = current.strftime('%H:%M')
            
            # Проверяем, не занят ли этот слот
            is_busy = False
            for booking in bookings:
                if booking.get('date') == date and booking.get('time') == time_str:
                    if booking.get('status') not in ['cancelled']:
                        is_busy = True
                        break
            
            if not is_busy:
                available_slots.append(time_str)
            
            current += timedelta(minutes=duration_min)
    
    return available_slots


def validate_date(date_str: str) -> bool:
    """
    Проверяет корректность формата даты
    
    Args:
        date_str: Дата в формате YYYY-MM-DD
    
    Returns:
        True если формат корректный
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_time(time_str: str) -> bool:
    """
    Проверяет корректность формата времени
    
    Args:
        time_str: Время в формате HH:MM
    
    Returns:
        True если формат корректный
    """
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False


def normalize_phone(phone: str) -> str:
    """
    Нормализует номер телефона к единому формату
    
    Args:
        phone: Номер телефона в любом формате
    
    Returns:
        Нормализованный номер телефона
    """
    if not phone:
        return ''
    
    # Убираем все нецифровые символы кроме +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Если начинается с 8, заменяем на +7
    if cleaned.startswith('8') and len(cleaned) == 11:
        cleaned = '+7' + cleaned[1:]
    
    # Если нет +, добавляем +972 (Израиль)
    if not cleaned.startswith('+'):
        cleaned = '+972' + cleaned
    
    return cleaned


def extract_keywords_from_text(text: str) -> List[str]:
    """
    Извлекает ключевые слова из текста для поиска
    
    Args:
        text: Исходный текст
    
    Returns:
        Список ключевых слов
    """
    if not text:
        return []
    
    # Убираем знаки препинания и приводим к нижнему регистру
    cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Разбиваем на слова и фильтруем короткие
    words = [w for w in cleaned.split() if len(w) > 2]
    
    return list(set(words))  # Убираем дубликаты


def calculate_booking_stats(bookings: List[Dict]) -> Dict[str, Any]:
    """
    Вычисляет статистику по записям
    
    Args:
        bookings: Список записей
    
    Returns:
        Словарь со статистикой
    """
    if not bookings:
        return {
            'total': 0,
            'confirmed': 0,
            'pending': 0,
            'completed': 0,
            'cancelled': 0
        }
    
    stats = {
        'total': len(bookings),
        'confirmed': len([b for b in bookings if b.get('status') == 'confirmed']),
        'pending': len([b for b in bookings if b.get('status') == 'pending']),
        'completed': len([b for b in bookings if b.get('status') == 'completed']),
        'cancelled': len([b for b in bookings if b.get('status') == 'cancelled'])
    }
    
    return stats


def group_bookings_by_date(bookings: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Группирует записи по датам
    
    Args:
        bookings: Список записей
    
    Returns:
        Словарь {дата: [список записей]}
    """
    grouped = {}
    
    for booking in bookings:
        date = booking.get('date', 'Unknown')
        if date not in grouped:
            grouped[date] = []
        grouped[date].append(booking)
    
    return grouped
