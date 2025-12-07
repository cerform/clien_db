"""
Enhanced Calendar Slots Finder for INKA
Получение доступных слотов прямо из Google Calendar
"""

import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta, timezone
import pytz

logger = logging.getLogger(__name__)


class EnhancedSlotsFinder:
    """
    Получение доступных слотов из Google Calendar
    """
    
    WORK_HOURS_START = 10  # 10:00
    WORK_HOURS_END = 22    # 22:00
    SLOT_DURATION = 60     # minutes
    
    def __init__(self, calendar_service):
        """
        Инициализация с сервисом Google Calendar
        
        Args:
            calendar_service: Google Calendar API service
        """
        self.calendar_service = calendar_service
        self.tz = pytz.timezone('Europe/Moscow')
    
    def get_busy_slots_from_calendar(self, calendar_id: str, date: str) -> List[Tuple[str, str]]:
        """
        Получить занятые слоты из Google Calendar
        
        Args:
            calendar_id: ID календаря (из Google Sheets)
            date: Дата в формате "YYYY-MM-DD"
            
        Returns:
            Список кортежей (start_time, end_time) "HH:MM"
        """
        try:
            # Преобразуем дату
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            
            # Устанавливаем временной диапазон на весь день
            day_start = datetime(
                date_obj.year, date_obj.month, date_obj.day,
                0, 0, 0, tzinfo=self.tz
            )
            day_end = datetime(
                date_obj.year, date_obj.month, date_obj.day,
                23, 59, 59, tzinfo=self.tz
            )
            
            # Получаем события из календаря
            events_result = self.calendar_service.events().list(
                calendarId=calendar_id,
                timeMin=day_start.isoformat(),
                timeMax=day_end.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            busy_slots = []
            
            for event in events:
                start = event['start'].get('dateTime')
                end = event['end'].get('dateTime')
                
                if start and end:
                    # Парсим время
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00')).astimezone(self.tz)
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00')).astimezone(self.tz)
                    
                    start_time = start_dt.strftime("%H:%M")
                    end_time = end_dt.strftime("%H:%M")
                    
                    busy_slots.append((start_time, end_time))
                    logger.info(f"📅 Занятый слот: {start_time}-{end_time} ({event.get('summary', 'No title')})")
            
            return busy_slots
        
        except Exception as e:
            logger.error(f"❌ Ошибка получения занятых слотов: {e}")
            return []
    
    def get_available_slots(self, busy_slots: List[Tuple[str, str]]) -> List[str]:
        """
        Получить доступные слоты на основе занятых
        
        Args:
            busy_slots: Список кортежей (start, end) занятых слотов
            
        Returns:
            Список доступных слотов "HH:MM"
        """
        available = []
        
        # Генерируем все возможные слоты
        for hour in range(self.WORK_HOURS_START, self.WORK_HOURS_END):
            for minute in [0, 30]:
                slot_str = f"{hour:02d}:{minute:02d}"
                slot_time = datetime.strptime(slot_str, "%H:%M").time()
                
                # Проверяем, не пересекается ли слот с занятыми
                is_occupied = False
                for busy_start, busy_end in busy_slots:
                    busy_start_time = datetime.strptime(busy_start, "%H:%M").time()
                    busy_end_time = datetime.strptime(busy_end, "%H:%M").time()
                    
                    # Проверяем пересечение
                    slot_end_time = (datetime.combine(datetime.today(), slot_time) + 
                                     timedelta(minutes=self.SLOT_DURATION)).time()
                    
                    if not (slot_end_time <= busy_start_time or slot_time >= busy_end_time):
                        is_occupied = True
                        break
                
                if not is_occupied:
                    available.append(slot_str)
        
        logger.info(f"✅ Доступных слотов: {len(available)}")
        return available
    
    def create_event_in_calendar(self, calendar_id: str, event_data: Dict) -> Optional[str]:
        """
        Создать событие (бронирование) в Google Calendar
        
        Args:
            calendar_id: ID календаря
            event_data: Данные события
                {
                    'title': 'Бронирование для Ивана',
                    'date': '2025-12-10',
                    'start_time': '15:00',
                    'end_time': '16:00',
                    'client_name': 'Иван',
                    'client_phone': '+79991234567',
                    'service': 'Татуировка',
                    'price': '5000'
                }
            
        Returns:
            Event ID если успешно, None если ошибка
        """
        try:
            date_str = event_data['date']
            start_time_str = event_data['start_time']
            end_time_str = event_data['end_time']
            
            # Создаем datetime объекты
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
            
            start_dt = self.tz.localize(datetime.combine(date_obj.date(), start_time))
            end_dt = self.tz.localize(datetime.combine(date_obj.date(), end_time))
            
            # Подготавливаем данные события
            event = {
                'summary': f"Запись: {event_data.get('client_name', 'Клиент')}",
                'description': f"""
Услуга: {event_data.get('service', 'Не указана')}
Цена: {event_data.get('price', 'Не указана')} руб
Телефон: {event_data.get('client_phone', 'Не указан')}
                """.strip(),
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'Europe/Moscow'
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'Europe/Moscow'
                },
                'attendees': [
                    {
                        'email': calendar_id,
                        'displayName': 'Мастер'
                    }
                ] if '@' in calendar_id else []
            }
            
            # Создаем событие
            created_event = self.calendar_service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            event_id = created_event['id']
            logger.info(f"✅ Событие создано: {event_id}")
            return event_id
        
        except Exception as e:
            logger.error(f"❌ Ошибка создания события: {e}")
            return None
    
    def update_event_in_calendar(self, calendar_id: str, event_id: str, 
                                start_time: str, end_time: str, date: str) -> bool:
        """
        Обновить событие (изменить время бронирования)
        
        Args:
            calendar_id: ID календаря
            event_id: ID события
            start_time: Новое время начала "HH:MM"
            end_time: Новое время окончания "HH:MM"
            date: Дата "YYYY-MM-DD"
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            # Получаем существующее событие
            event = self.calendar_service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Создаем новые datetime
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            start_time_dt = datetime.strptime(start_time, "%H:%M").time()
            end_time_dt = datetime.strptime(end_time, "%H:%M").time()
            
            start_dt = self.tz.localize(datetime.combine(date_obj.date(), start_time_dt))
            end_dt = self.tz.localize(datetime.combine(date_obj.date(), end_time_dt))
            
            # Обновляем время
            event['start'] = {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Europe/Moscow'
            }
            event['end'] = {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Europe/Moscow'
            }
            
            # Сохраняем изменения
            self.calendar_service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"✅ Событие обновлено: {event_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Ошибка обновления события: {e}")
            return False
    
    def delete_event_from_calendar(self, calendar_id: str, event_id: str) -> bool:
        """
        Удалить событие (отмена бронирования)
        
        Args:
            calendar_id: ID календаря
            event_id: ID события
            
        Returns:
            True если успешно, False если ошибка
        """
        try:
            self.calendar_service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"✅ Событие удалено: {event_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Ошибка удаления события: {e}")
            return False
    
    @staticmethod
    def get_next_available_days(n: int = 7) -> List[str]:
        """
        Получить следующие N доступных дней (без выходных)
        
        Args:
            n: Количество дней
            
        Returns:
            Список дат в формате "YYYY-MM-DD"
        """
        days = []
        current_day = datetime.now().date() + timedelta(days=1)
        
        while len(days) < n:
            # Пропускаем выходные (5=Saturday, 6=Sunday)
            if current_day.weekday() not in [5, 6]:
                days.append(current_day.strftime("%Y-%m-%d"))
            current_day += timedelta(days=1)
        
        return days
    
    @staticmethod
    def format_time_range(start_time: str, end_time: str) -> str:
        """Форматировать диапазон времени для отображения"""
        return f"{start_time} - {end_time}"
    
    @staticmethod
    def is_slot_available(slot_time: str, busy_slots: List[Tuple[str, str]]) -> bool:
        """Проверить, доступен ли конкретный слот"""
        slot_time_dt = datetime.strptime(slot_time, "%H:%M").time()
        slot_end_dt = (datetime.combine(datetime.today(), slot_time_dt) + 
                       timedelta(minutes=60)).time()
        
        for busy_start, busy_end in busy_slots:
            busy_start_dt = datetime.strptime(busy_start, "%H:%M").time()
            busy_end_dt = datetime.strptime(busy_end, "%H:%M").time()
            
            # Проверяем пересечение
            if not (slot_end_dt <= busy_start_dt or slot_time_dt >= busy_end_dt):
                return False
        
        return True
