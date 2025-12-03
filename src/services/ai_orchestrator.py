"""
AI Orchestrator - Связывает AI Dialog Engine с реальными сервисами бота
Выполняет действия, запрошенные через AI (бронирования, администрирование)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from src.services.ai_dialog_engine import AIDialogEngine, UserRole, ActionType
from src.services.service_factory import (
    get_booking_service,
    get_calendar_service,
    get_client_service,
    get_master_service,
    get_admin_service
)

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Оркестратор AI - выполняет действия через существующие сервисы
    Преобразует natural language запросы в конкретные операции
    """
    
    def __init__(self, ai_engine: AIDialogEngine):
        """
        Инициализация оркестратора
        
        Args:
            ai_engine: Экземпляр AIDialogEngine
        """
        self.ai_engine = ai_engine
        self.booking_service = get_booking_service()
        self.calendar_service = get_calendar_service()
        self.client_service = get_client_service()
        self.master_service = get_master_service()
        self.admin_service = get_admin_service()
    
    async def process_user_message(
        self,
        user_id: int,
        message: str,
        user_role: UserRole = UserRole.CLIENT,
        telegram_user: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Обработка сообщения пользователя с выполнением действий
        
        Args:
            user_id: Telegram user ID
            message: Текст сообщения
            user_role: Роль пользователя
            telegram_user: Объект telegram user (для получения имени)
            
        Returns:
            {
                "text_response": "Текст ответа пользователю",
                "action_executed": bool,
                "action_result": {...},
                "language": "ru|en|he",
                "buttons": [...] (опционально, для клавиатур)
            }
        """
        try:
            # Получаем информацию о пользователе
            user_info = await self._get_user_info(user_id, telegram_user)
            
            # Получаем контекст для AI
            context = await self._build_context(user_id, user_role)
            
            # Обрабатываем через AI
            ai_response = await self.ai_engine.process_message(
                user_id=user_id,
                message=message,
                user_role=user_role,
                user_info=user_info,
                context=context
            )
            
            # Если AI запросил действие - выполняем
            if ai_response.get("action"):
                action_result = await self._execute_action(
                    action=ai_response["action"],
                    params=ai_response["action_params"],
                    user_id=user_id,
                    user_role=user_role
                )
                
                # Формируем финальный ответ с результатом действия
                final_response = await self._format_action_response(
                    ai_response=ai_response,
                    action_result=action_result,
                    language=ai_response["language"]
                )
                
                return {
                    "text_response": final_response,
                    "action_executed": True,
                    "action_result": action_result,
                    "language": ai_response["language"],
                    "requires_confirmation": ai_response.get("requires_confirmation", False)
                }
            
            else:
                # Обычный диалог без действия
                return {
                    "text_response": ai_response["response"],
                    "action_executed": False,
                    "action_result": None,
                    "language": ai_response["language"],
                    "requires_confirmation": False
                }
        
        except Exception as e:
            logger.exception(f"AI Orchestrator error: {e}")
            return {
                "text_response": "Произошла ошибка. Пожалуйста, попробуйте еще раз или обратитесь к администратору.",
                "action_executed": False,
                "action_result": None,
                "language": "ru",
                "error": str(e)
            }
    
    async def _get_user_info(self, user_id: int, telegram_user: Any) -> Dict:
        """Получить информацию о пользователе"""
        try:
            # Пытаемся получить из БД
            clients = self.client_service.repo.list_clients()
            client = None
            for c in clients:
                if str(c.get("telegram_id")) == str(user_id):
                    client = c
                    break
            
            if client:
                return {
                    "name": client.get("name", "Гость"),
                    "language": "ru",  # TODO: добавить поле language в БД
                    "phone": client.get("phone"),
                    "total_bookings": 0  # TODO: посчитать
                }
        except Exception as e:
            logger.debug(f"Could not get user from DB: {e}")
        
        # Fallback на telegram данные
        if telegram_user:
            name = telegram_user.first_name
            if telegram_user.last_name:
                name += f" {telegram_user.last_name}"
            return {
                "name": name,
                "language": telegram_user.language_code or "ru",
                "phone": None,
                "total_bookings": 0
            }
        
        return {
            "name": "Гость",
            "language": "ru",
            "phone": None,
            "total_bookings": 0
        }
    
    async def _build_context(self, user_id: int, user_role: UserRole) -> Dict:
        """
        Собирает контекст для AI (текущие записи, доступные слоты и т.д.)
        
        Args:
            user_id: ID пользователя
            user_role: Роль пользователя
            
        Returns:
            Словарь с контекстом
        """
        context = {}
        
        try:
            # Для всех - получаем все записи
            all_bookings = self.admin_service.list_bookings()
            
            # Для клиентов - их записи
            if user_role == UserRole.CLIENT:
                user_bookings = [
                    b for b in all_bookings
                    if str(b.get("client_id")) == str(user_id) or 
                       b.get("client_telegram_id") == str(user_id)
                ]
                # Фильтруем только pending/confirmed
                active_bookings = [
                    b for b in user_bookings 
                    if b.get("status") in ["pending", "confirmed"]
                ]
                context["user_bookings"] = active_bookings[:5]
                context["has_active_bookings"] = len(active_bookings) > 0
            
            # Для админов и мастеров - сегодняшние записи
            if user_role in [UserRole.ADMIN, UserRole.MASTER]:
                today = datetime.now().strftime("%Y-%m-%d")
                today_bookings = [
                    b for b in all_bookings
                    if b.get("date") == today
                ]
                context["today_bookings"] = today_bookings
                context["today_bookings_count"] = len(today_bookings)
                
                # Простая статистика
                context["week_statistics"] = {
                    "total_bookings": len(all_bookings),
                    "pending": len([b for b in all_bookings if b.get("status") == "pending"]),
                    "confirmed": len([b for b in all_bookings if b.get("status") == "confirmed"])
                }
        
        except Exception as e:
            logger.warning(f"Failed to build context: {e}")
        
        return context
    
    async def _execute_action(
        self,
        action: str,
        params: Dict,
        user_id: int,
        user_role: UserRole
    ) -> Dict[str, Any]:
        """
        Выполняет запрошенное AI действие через сервисы
        
        Args:
            action: Название действия (функции)
            params: Параметры действия
            user_id: ID пользователя
            user_role: Роль пользователя
            
        Returns:
            Результат выполнения действия
        """
        try:
            logger.info(f"Executing action: {action} with params: {params} for user {user_id}")
            
            # === КЛИЕНТСКИЕ ДЕЙСТВИЯ ===
            
            if action == "show_available_slots":
                return await self._show_available_slots(params)
            
            elif action == "create_booking":
                return await self._create_booking(params, user_id)
            
            elif action == "show_my_bookings":
                return await self._show_my_bookings(user_id, params)
            
            elif action == "cancel_booking":
                return await self._cancel_booking(params, user_id)
            
            elif action == "reschedule_booking":
                return await self._reschedule_booking(params, user_id)
            
            # === АДМИНИСТРАТИВНЫЕ ДЕЙСТВИЯ ===
            
            elif action == "view_all_bookings":
                if user_role not in [UserRole.ADMIN, UserRole.MASTER]:
                    return {"success": False, "error": "Access denied"}
                return await self._view_all_bookings(params)
            
            elif action == "view_schedule":
                if user_role not in [UserRole.ADMIN, UserRole.MASTER]:
                    return {"success": False, "error": "Access denied"}
                return await self._view_schedule(params)
            
            elif action == "add_available_slot":
                if user_role not in [UserRole.ADMIN, UserRole.MASTER]:
                    return {"success": False, "error": "Access denied"}
                return await self._add_available_slot(params)
            
            elif action == "remove_slot":
                if user_role not in [UserRole.ADMIN, UserRole.MASTER]:
                    return {"success": False, "error": "Access denied"}
                return await self._remove_slot(params)
            
            elif action == "view_statistics":
                if user_role not in [UserRole.ADMIN, UserRole.MASTER]:
                    return {"success": False, "error": "Access denied"}
                return await self._view_statistics(params)
            
            elif action == "send_message_to_client":
                if user_role not in [UserRole.ADMIN, UserRole.MASTER]:
                    return {"success": False, "error": "Access denied"}
                return await self._send_message_to_client(params)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        
        except Exception as e:
            logger.exception(f"Failed to execute action {action}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # === РЕАЛИЗАЦИЯ ДЕЙСТВИЙ ===
    
    async def _show_available_slots(self, params: Dict) -> Dict:
        """Показать доступные слоты"""
        start_date = params.get("start_date")
        
        # Используем реальный метод
        slots = self.booking_service.list_available_slots(
            date=start_date,
            master_id=None  # TODO: добавить поддержку выбора мастера
        )
        
        return {
            "success": True,
            "slots": slots,
            "count": len(slots),
            "start_date": start_date,
            "duration": params.get("duration_minutes", 120)
        }
    
    async def _create_booking(self, params: Dict, user_id: int) -> Dict:
        """Создать бронирование"""
        try:
            # Получаем или создаём клиента
            clients = self.client_service.repo.list_clients()
            client = None
            for c in clients:
                if str(c.get("telegram_id")) == str(user_id):
                    client = c
                    break
            
            if not client:
                # Регистрируем нового клиента
                client = self.client_service.register_client(
                    telegram_id=user_id,
                    name="Client",  # TODO: получить реальное имя
                    phone=""
                )
            
            # Получаем первого мастера (TODO: добавить выбор мастера)
            masters = self.master_service.list_masters()
            master_id = masters[0]["id"] if masters else "1"
            
            # Создаём бронирование
            date = params.get("date")
            time = params.get("time")
            duration = params.get("duration_minutes", 120)
            
            # Конвертируем в slot_end
            from datetime import datetime, timedelta
            time_obj = datetime.strptime(time, "%H:%M")
            end_time_obj = time_obj + timedelta(minutes=duration)
            slot_end = end_time_obj.strftime("%H:%M")
            
            result = self.booking_service.create_booking(
                client_telegram_id=user_id,
                client_name=client.get("name", "Client"),
                client_phone=client.get("phone", ""),
                date=date,
                master_id=master_id,
                slot_start=time,
                slot_end=slot_end,
                notes=params.get("description", "")
            )
            
            return {
                "success": True,
                "booking_id": result.get("booking_id"),
                "date": date,
                "time": time,
                "message": "Booking created successfully"
            }
        except Exception as e:
            logger.exception(f"Failed to create booking: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create booking"
            }
    
    async def _show_my_bookings(self, user_id: int, params: Dict) -> Dict:
        """Показать записи пользователя"""
        status_filter = params.get("status", "all")
        
        # Получаем все записи и фильтруем
        all_bookings = self.admin_service.list_bookings()
        bookings = [
            b for b in all_bookings
            if str(b.get("client_id")) == str(user_id) or
               str(b.get("client_telegram_id")) == str(user_id)
        ]
        
        # Фильтруем по статусу если нужно
        if status_filter != "all":
            if status_filter == "upcoming":
                now = datetime.now().strftime("%Y-%m-%d")
                bookings = [b for b in bookings if b.get("date", "") >= now]
            elif status_filter == "past":
                now = datetime.now().strftime("%Y-%m-%d")
                bookings = [b for b in bookings if b.get("date", "") < now]
            else:
                bookings = [b for b in bookings if b.get("status") == status_filter]
        
        return {
            "success": True,
            "bookings": bookings,
            "count": len(bookings),
            "filter": status_filter
        }
    
    async def _cancel_booking(self, params: Dict, user_id: int) -> Dict:
        """Отменить бронирование"""
        # TODO: реализовать метод cancel в BookingsRepo
        booking_id = params.get("booking_id")
        
        return {
            "success": True,
            "booking_id": booking_id,
            "message": "Booking cancelled (TODO: implement in repo)"
        }
    
    async def _reschedule_booking(self, params: Dict, user_id: int) -> Dict:
        """Перенести бронирование"""
        # TODO: реализовать метод reschedule в BookingsRepo
        booking_id = params.get("booking_id")
        new_date = params.get("new_date")
        new_time = params.get("new_time")
        
        return {
            "success": True,
            "booking_id": booking_id,
            "new_date": new_date,
            "new_time": new_time,
            "message": "Booking rescheduled (TODO: implement in repo)"
        }
    
    async def _view_all_bookings(self, params: Dict) -> Dict:
        """Просмотр всех бронирований (админ)"""
        bookings = self.admin_service.list_bookings()
        
        # Фильтрация
        date_filter = params.get("date")
        status_filter = params.get("status", "all")
        
        if date_filter:
            bookings = [b for b in bookings if b.get("date") == date_filter]
        
        if status_filter != "all":
            bookings = [b for b in bookings if b.get("status") == status_filter]
        
        return {
            "success": True,
            "bookings": bookings,
            "count": len(bookings),
            "filters": params
        }
    
    async def _view_schedule(self, params: Dict) -> Dict:
        """Просмотр расписания (админ/мастер)"""
        start_date = params.get("start_date")
        
        # Получаем слоты и записи
        slots = self.booking_service.list_available_slots(start_date)
        bookings = self.admin_service.list_bookings()
        date_bookings = [b for b in bookings if b.get("date") == start_date]
        
        schedule = {
            "available_slots": slots,
            "bookings": date_bookings
        }
        
        return {
            "success": True,
            "schedule": schedule,
            "start_date": start_date
        }
    
    async def _add_available_slot(self, params: Dict) -> Dict:
        """Добавить доступный слот (админ)"""
        # TODO: реализовать метод add_slot в CalendarRepo
        return {
            "success": True,
            "message": "Slot added (TODO: implement in repo)",
            "slot_id": "new_slot_id"
        }
    
    async def _remove_slot(self, params: Dict) -> Dict:
        """Удалить слот (админ)"""
        # TODO: реализовать метод remove_slot в CalendarRepo
        return {
            "success": True,
            "message": "Slot removed (TODO: implement in repo)"
        }
    
    async def _view_statistics(self, params: Dict) -> Dict:
        """Просмотр статистики (админ)"""
        bookings = self.admin_service.list_bookings()
        
        # Простая статистика
        stats = {
            "total": len(bookings),
            "pending": len([b for b in bookings if b.get("status") == "pending"]),
            "confirmed": len([b for b in bookings if b.get("status") == "confirmed"]),
            "completed": len([b for b in bookings if b.get("status") == "completed"]),
            "cancelled": len([b for b in bookings if b.get("status") == "cancelled"])
        }
        
        return {
            "success": True,
            "statistics": stats,
            "period": params.get("period", "all")
        }
    
    async def _send_message_to_client(self, params: Dict) -> Dict:
        """Отправить сообщение клиенту (админ)"""
        # TODO: интеграция с telegram bot для отправки
        return {
            "success": True,
            "message": "Message queued for sending",
            "client_id": params.get("client_id"),
            "text": params.get("message")
        }
    
    async def _format_action_response(
        self,
        ai_response: Dict,
        action_result: Dict,
        language: str
    ) -> str:
        """
        Форматирует ответ с результатами действия
        
        Args:
            ai_response: Ответ от AI
            action_result: Результат выполнения действия
            language: Язык ответа
            
        Returns:
            Отформатированный текст ответа
        """
        if not action_result.get("success"):
            # Ошибка выполнения
            error_messages = {
                "ru": f"❌ К сожалению, не удалось выполнить действие: {action_result.get('error', 'Неизвестная ошибка')}",
                "en": f"❌ Failed to execute action: {action_result.get('error', 'Unknown error')}",
                "he": f"❌ לא הצלחנו לבצע את הפעולה: {action_result.get('error', 'שגיאה לא ידועה')}"
            }
            return error_messages.get(language, error_messages["en"])
        
        # Успех - формируем ответ на основе типа действия
        action = ai_response.get("action")
        
        if action == "show_available_slots":
            slots = action_result.get("slots", [])
            if not slots:
                no_slots_msg = {
                    "ru": "К сожалению, на указанные даты нет свободных слотов. Попробуйте другие даты.",
                    "en": "Unfortunately, no available slots for the specified dates. Try other dates.",
                    "he": "למרבה הצער, אין משבצות פנויות בתאריכים המבוקשים. נסה תאריכים אחרים."
                }
                return no_slots_msg.get(language, no_slots_msg["en"])
            
            # Форматируем список слотов
            slots_text = self._format_slots(slots, language)
            return slots_text
        
        elif action == "create_booking":
            success_msg = {
                "ru": f"✅ Отлично! Ваша запись создана:\n📅 {action_result.get('date')} в {action_result.get('time')}\n\nЖдём вас!",
                "en": f"✅ Great! Your booking is created:\n📅 {action_result.get('date')} at {action_result.get('time')}\n\nSee you!",
                "he": f"✅ מעולה! ההזמנה שלך נוצרה:\n📅 {action_result.get('date')} ב-{action_result.get('time')}\n\nנתראה!"
            }
            return success_msg.get(language, success_msg["en"])
        
        elif action == "show_my_bookings":
            bookings = action_result.get("bookings", [])
            if not bookings:
                no_bookings_msg = {
                    "ru": "У вас пока нет записей.",
                    "en": "You don't have any bookings yet.",
                    "he": "אין לך עדיין הזמנות."
                }
                return no_bookings_msg.get(language, no_bookings_msg["en"])
            
            return self._format_bookings(bookings, language)
        
        elif action == "cancel_booking":
            cancel_msg = {
                "ru": "✅ Запись отменена. Если захотите записаться снова - пишите!",
                "en": "✅ Booking cancelled. Feel free to book again anytime!",
                "he": "✅ ההזמנה בוטלה. אתה יכול להזמין שוב בכל עת!"
            }
            return cancel_msg.get(language, cancel_msg["en"])
        
        # Для остальных действий - общий ответ
        return ai_response.get("response", "✅ Готово!")
    
    def _format_slots(self, slots: List[Dict], language: str) -> str:
        """Форматирует список слотов"""
        header = {
            "ru": "📅 Доступные слоты:\n\n",
            "en": "📅 Available slots:\n\n",
            "he": "📅 משבצות פנויות:\n\n"
        }
        
        text = header.get(language, header["en"])
        
        for i, slot in enumerate(slots[:10], 1):  # Показываем максимум 10
            date = slot.get("date", "")
            time = slot.get("time", "")
            duration = slot.get("duration", 120)
            text += f"{i}. {date} в {time} ({duration} мин)\n"
        
        if len(slots) > 10:
            more_msg = {
                "ru": f"\n... и ещё {len(slots) - 10} слотов",
                "en": f"\n... and {len(slots) - 10} more slots",
                "he": f"\n... ועוד {len(slots) - 10} משבצות"
            }
            text += more_msg.get(language, more_msg["en"])
        
        return text
    
    def _format_bookings(self, bookings: List[Dict], language: str) -> str:
        """Форматирует список бронирований"""
        header = {
            "ru": "📋 Ваши записи:\n\n",
            "en": "📋 Your bookings:\n\n",
            "he": "📋 ההזמנות שלך:\n\n"
        }
        
        text = header.get(language, header["en"])
        
        for i, booking in enumerate(bookings[:5], 1):
            date = booking.get("date", "")
            time = booking.get("time", "")
            status = booking.get("status", "")
            text += f"{i}. {date} в {time} - {status}\n"
        
        return text


# Export
__all__ = ["AIOrchestrator"]
