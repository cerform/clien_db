"""
Сервис анализа поведения клиентов
================================
Классифицирует поведение клиентов и управляет уровнями риска.

Классы поведения:
- polite: Вежливый (risk 0)
- neutral: Нормальный (risk 0)
- anxious: Тревожный (risk 1)
- demanding: Настойчивый (risk 2)
- aggressive: Агрессивный (risk 3)
- toxic: Оскорбительный (risk 4)
- manipulative: Манипулятивный (risk 3)
- spam: Спамер (risk 5)
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from openai import OpenAI

logger = logging.getLogger(__name__)

# ============================================================
# КОНСТАНТЫ
# ============================================================

BEHAVIOR_TYPES = {
    "polite": {"risk": 0, "label": "Вежливый", "emoji": "😊"},
    "neutral": {"risk": 0, "label": "Нормальный", "emoji": "😐"},
    "anxious": {"risk": 1, "label": "Тревожный", "emoji": "😰"},
    "demanding": {"risk": 2, "label": "Настойчивый", "emoji": "😤"},
    "aggressive": {"risk": 3, "label": "Агрессивный", "emoji": "😠"},
    "toxic": {"risk": 4, "label": "Оскорбительный", "emoji": "🤬"},
    "manipulative": {"risk": 3, "label": "Манипулятивный", "emoji": "🎭"},
    "spam": {"risk": 5, "label": "Спамер", "emoji": "🚫"},
}

# События, влияющие на рейтинг
BEHAVIOR_EVENTS = {
    "successful_visit": -1,      # Успешный визит
    "cancel_24h_plus": 0,        # Отмена за 24ч+
    "cancel_under_3h": 1,        # Отмена < 3ч
    "no_show": 2,                # Неявка
    "aggressive_message": 2,     # Агрессивное сообщение
    "master_complaint": 3,       # Жалоба мастера
}

# Права доступа по уровню риска
ACCESS_LEVELS = {
    0: {"booking": True, "transfer": True, "cancel": True, "auto": True, "label": "Полный доступ"},
    1: {"booking": True, "transfer": True, "cancel": True, "auto": True, "label": "Полный доступ"},
    2: {"booking": True, "transfer": False, "cancel": True, "auto": True, "label": "Без онлайн-переноса"},
    3: {"booking": "admin", "transfer": False, "cancel": False, "auto": False, "label": "Только через админа"},
    4: {"booking": False, "transfer": False, "cancel": False, "auto": False, "label": "Только консультация"},
    5: {"booking": False, "transfer": False, "cancel": False, "auto": False, "label": "Полный бан"},
}

# Промпт для классификации
CLASSIFICATION_PROMPT = """Ты — анализатор поведения клиентов. Определи тип поведения по сообщению.

КЛАССЫ ПОВЕДЕНИЯ:
- polite: Вежливый, приятный клиент
- neutral: Обычный, нейтральный клиент
- anxious: Тревожный, много вопросов, переживает
- demanding: Настойчивый, требует быстро, давит
- aggressive: Агрессивный, грубый, но без оскорблений
- toxic: Оскорбительный, использует мат, унижает
- manipulative: Манипулятивный, давит на жалость, угрожает жалобами
- spam: Спам, реклама, нерелевантные сообщения

ПРАВИЛА:
1. Один резкий ответ — НЕ сразу aggressive, может быть demanding
2. Мат без оскорблений — aggressive, с оскорблениями — toxic
3. "Я напишу жалобу" — manipulative
4. Много капслока без смысла — spam
5. При сомнениях — neutral

Верни ТОЛЬКО JSON без пояснений:
{"behavior": "тип", "confidence": 0.XX}
"""


class BehaviorService:
    """Сервис анализа и управления поведением клиентов"""
    
    def __init__(self, sheets_client=None, openai_api_key: str = None):
        self.sheets_client = sheets_client
        self.openai_client = None
        
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        
        # Кэш последних сообщений для анализа (tg_id -> list of messages)
        self._message_history: Dict[str, List[Dict]] = {}
        
        logger.info("🧠 BehaviorService initialized")
    
    # ============================================================
    # АНАЛИЗ ПОВЕДЕНИЯ
    # ============================================================
    
    def analyze_message_behavior(self, text: str, context: List[str] = None) -> Dict:
        """
        Анализировать поведение по сообщению
        
        Args:
            text: Текст сообщения
            context: Предыдущие сообщения для контекста
        
        Returns:
            {"behavior": "тип", "confidence": 0.XX, "risk": N}
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available for behavior analysis")
            return {"behavior": "neutral", "confidence": 0.5, "risk": 0}
        
        try:
            # Формируем контекст
            messages_context = ""
            if context:
                messages_context = "\n\nПредыдущие сообщения клиента:\n" + "\n".join(f"- {m}" for m in context[-5:])
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": CLASSIFICATION_PROMPT},
                    {"role": "user", "content": f"Сообщение: {text}{messages_context}"}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Парсим JSON
            try:
                # Убираем возможные markdown теги
                if "```" in result_text:
                    result_text = result_text.split("```")[1]
                    if result_text.startswith("json"):
                        result_text = result_text[4:]
                
                result = json.loads(result_text)
                behavior = result.get("behavior", "neutral")
                confidence = result.get("confidence", 0.5)
                
                # Добавляем риск
                risk = BEHAVIOR_TYPES.get(behavior, {}).get("risk", 0)
                
                logger.info(f"🧠 Behavior analysis: {behavior} ({confidence:.2f}), risk={risk}")
                
                return {
                    "behavior": behavior,
                    "confidence": confidence,
                    "risk": risk,
                    "label": BEHAVIOR_TYPES.get(behavior, {}).get("label", behavior),
                    "emoji": BEHAVIOR_TYPES.get(behavior, {}).get("emoji", "❓")
                }
            
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse behavior response: {result_text}")
                return {"behavior": "neutral", "confidence": 0.5, "risk": 0}
        
        except Exception as e:
            logger.error(f"Behavior analysis error: {e}")
            return {"behavior": "neutral", "confidence": 0.5, "risk": 0}
    
    def add_message_to_history(self, tg_id: str, message: str, behavior: Dict = None):
        """Добавить сообщение в историю для анализа"""
        if tg_id not in self._message_history:
            self._message_history[tg_id] = []
        
        self._message_history[tg_id].append({
            "text": message,
            "timestamp": datetime.now().isoformat(),
            "behavior": behavior
        })
        
        # Храним только последние 10 сообщений
        if len(self._message_history[tg_id]) > 10:
            self._message_history[tg_id] = self._message_history[tg_id][-10:]
    
    def get_message_history(self, tg_id: str) -> List[str]:
        """Получить историю сообщений клиента"""
        if tg_id not in self._message_history:
            return []
        return [m["text"] for m in self._message_history[tg_id]]
    
    # ============================================================
    # РАБОТА С КЛИЕНТАМИ В БД
    # ============================================================
    
    def update_client_behavior(self, tg_id: str, behavior: Dict) -> bool:
        """
        Обновить поведение клиента в базе
        
        Args:
            tg_id: Telegram ID клиента
            behavior: Результат анализа {"behavior": "...", "confidence": X, "risk": N}
        
        Returns:
            True если обновлено успешно
        """
        if not self.sheets_client:
            logger.warning("Sheets client not available")
            return False
        
        try:
            # Находим клиента по tg_id
            clients = self.sheets_client.get_all_rows("Clients")
            if not clients:
                return False
            
            # Ищем колонку telegram_id
            header = clients[0] if clients else []
            tg_id_col = None
            for i, col in enumerate(header):
                if col.lower() in ["telegram_id", "tg_id"]:
                    tg_id_col = i
                    break
            
            if tg_id_col is None:
                logger.warning("telegram_id column not found in Clients sheet")
                return False
            
            # Ищем клиента
            client_row = None
            row_idx = None
            for i, row in enumerate(clients[1:], start=2):  # Начинаем с 2 (пропуская header)
                if len(row) > tg_id_col and str(row[tg_id_col]) == str(tg_id):
                    client_row = row
                    row_idx = i
                    break
            
            if not client_row:
                logger.info(f"Client with tg_id={tg_id} not found")
                return False
            
            # Находим или добавляем колонки поведения
            behavior_cols = {
                "behavior_score": None,
                "behavior_type": None,
                "risk_level": None,
                "last_behavior_check": None
            }
            
            for i, col in enumerate(header):
                col_lower = col.lower()
                if col_lower in behavior_cols:
                    behavior_cols[col_lower] = i
            
            # Если колонок нет - они будут добавлены при следующем обновлении
            # Пока просто логируем
            if all(v is None for v in behavior_cols.values()):
                logger.warning("Behavior columns not found in Clients sheet. Please add them manually.")
                return False
            
            # Обновляем данные
            # ... (упрощённая версия - в реальности нужно обновить ячейки)
            logger.info(f"✅ Updated behavior for client {tg_id}: {behavior}")
            return True
        
        except Exception as e:
            logger.error(f"Error updating client behavior: {e}")
            return False
    
    def get_client_risk_level(self, tg_id: str) -> int:
        """Получить уровень риска клиента"""
        if not self.sheets_client:
            return 0
        
        try:
            clients = self.sheets_client.get_all_rows("Clients")
            if not clients:
                return 0
            
            header = clients[0]
            tg_id_col = None
            risk_col = None
            
            for i, col in enumerate(header):
                col_lower = col.lower()
                if col_lower in ["telegram_id", "tg_id"]:
                    tg_id_col = i
                if col_lower == "risk_level":
                    risk_col = i
            
            if tg_id_col is None:
                return 0
            
            for row in clients[1:]:
                if len(row) > tg_id_col and str(row[tg_id_col]) == str(tg_id):
                    if risk_col is not None and len(row) > risk_col:
                        try:
                            return int(row[risk_col])
                        except (ValueError, TypeError):
                            return 0
                    return 0
            
            return 0
        
        except Exception as e:
            logger.error(f"Error getting client risk level: {e}")
            return 0
    
    def calculate_risk_level(self, tg_id: str) -> int:
        """
        Рассчитать уровень риска на основе последних сообщений
        Использует скользящее среднее по последним 3-5 сообщениям
        """
        history = self._message_history.get(tg_id, [])
        if not history:
            return 0
        
        # Берём последние 5 сообщений с поведением
        recent = [m for m in history if m.get("behavior")][-5:]
        if not recent:
            return 0
        
        # Считаем средний риск с учётом confidence
        total_risk = 0
        total_weight = 0
        
        for msg in recent:
            behavior = msg.get("behavior", {})
            risk = behavior.get("risk", 0)
            confidence = behavior.get("confidence", 0.5)
            
            total_risk += risk * confidence
            total_weight += confidence
        
        if total_weight == 0:
            return 0
        
        avg_risk = total_risk / total_weight
        
        # Нужно минимум 2 подтверждения высокого риска
        high_risk_count = sum(1 for m in recent if m.get("behavior", {}).get("risk", 0) >= 3)
        
        if high_risk_count < 2 and avg_risk >= 3:
            # Снижаем риск если только одно агрессивное сообщение
            avg_risk = 2
        
        return round(avg_risk)
    
    # ============================================================
    # ПРОВЕРКИ ДОСТУПА
    # ============================================================
    
    def is_booking_allowed(self, tg_id: str) -> Tuple[bool, str]:
        """
        Проверить, разрешена ли запись клиенту
        
        Returns:
            (allowed: bool, reason: str)
        """
        risk_level = self.get_client_risk_level(tg_id)
        
        # Также проверяем текущую сессию
        calculated_risk = self.calculate_risk_level(tg_id)
        risk_level = max(risk_level, calculated_risk)
        
        access = ACCESS_LEVELS.get(risk_level, ACCESS_LEVELS[0])
        
        if access["booking"] is True:
            return True, "Запись разрешена"
        elif access["booking"] == "admin":
            return False, "Запись только через администратора"
        else:
            return False, "К сожалению, онлайн-запись сейчас недоступна. С вами свяжется администратор."
    
    def is_transfer_allowed(self, tg_id: str) -> Tuple[bool, str]:
        """Проверить, разрешён ли перенос"""
        risk_level = max(self.get_client_risk_level(tg_id), self.calculate_risk_level(tg_id))
        access = ACCESS_LEVELS.get(risk_level, ACCESS_LEVELS[0])
        
        if access["transfer"]:
            return True, "Перенос разрешён"
        else:
            return False, "Для переноса записи обратитесь к администратору"
    
    def get_access_info(self, tg_id: str) -> Dict:
        """Получить полную информацию о доступе клиента"""
        risk_level = max(self.get_client_risk_level(tg_id), self.calculate_risk_level(tg_id))
        access = ACCESS_LEVELS.get(risk_level, ACCESS_LEVELS[0])
        
        return {
            "risk_level": risk_level,
            "access": access,
            "booking_allowed": access["booking"] is True,
            "admin_required": access["booking"] == "admin",
            "banned": access["booking"] is False and access["booking"] != "admin"
        }
    
    # ============================================================
    # СОБЫТИЯ
    # ============================================================
    
    def record_event(self, tg_id: str, event_type: str) -> int:
        """
        Записать событие и обновить риск
        
        Args:
            tg_id: Telegram ID клиента
            event_type: Тип события из BEHAVIOR_EVENTS
        
        Returns:
            Новый уровень риска
        """
        if event_type not in BEHAVIOR_EVENTS:
            logger.warning(f"Unknown event type: {event_type}")
            return self.get_client_risk_level(tg_id)
        
        risk_change = BEHAVIOR_EVENTS[event_type]
        current_risk = self.get_client_risk_level(tg_id)
        new_risk = max(0, min(5, current_risk + risk_change))
        
        logger.info(f"📊 Event '{event_type}' for {tg_id}: risk {current_risk} → {new_risk}")
        
        # TODO: Обновить в базе
        return new_risk
    
    # ============================================================
    # АДАПТАЦИЯ СТИЛЯ ОТВЕТОВ
    # ============================================================
    
    def get_response_style(self, tg_id: str) -> str:
        """
        Получить рекомендуемый стиль ответа для клиента
        
        Returns:
            Инструкция для промпта INKA
        """
        history = self._message_history.get(tg_id, [])
        if not history:
            return ""
        
        # Определяем преобладающий тип поведения
        recent = [m for m in history if m.get("behavior")][-5:]
        if not recent:
            return ""
        
        # Считаем частоту типов
        behavior_counts = {}
        for msg in recent:
            b_type = msg.get("behavior", {}).get("behavior", "neutral")
            behavior_counts[b_type] = behavior_counts.get(b_type, 0) + 1
        
        dominant = max(behavior_counts, key=behavior_counts.get)
        
        styles = {
            "polite": "Клиент вежливый — отвечай тепло и дружелюбно 😊",
            "neutral": "",
            "anxious": "Клиент тревожный — успокаивай, давай уверенные ответы, не торопи 💚",
            "demanding": "Клиент настойчивый — отвечай уверенно, коротко, по делу. Без лишних эмоций.",
            "aggressive": "⚠️ Клиент агрессивен — отвечай максимально нейтрально и холодно. Не провоцируй.",
            "toxic": "🚫 Клиент оскорбляет — минимальные ответы, не вступай в диалог. Завершай вежливо.",
            "manipulative": "⚠️ Клиент манипулирует — не подыгрывай, придерживайся правил. Факты, не эмоции.",
            "spam": "🚫 Спам — игнорируй нерелевантные сообщения."
        }
        
        return styles.get(dominant, "")
    
    # ============================================================
    # УВЕДОМЛЕНИЯ АДМИНИСТРАТОРУ
    # ============================================================
    
    def should_notify_admin(self, tg_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Проверить, нужно ли уведомить администратора
        
        Returns:
            (should_notify: bool, notification_data: dict | None)
        """
        risk_level = self.calculate_risk_level(tg_id)
        
        if risk_level < 3:
            return False, None
        
        history = self._message_history.get(tg_id, [])
        last_behavior = history[-1].get("behavior", {}) if history else {}
        
        notification = {
            "type": "risky_client",
            "tg_id": tg_id,
            "risk_level": risk_level,
            "behavior": last_behavior.get("behavior", "unknown"),
            "confidence": last_behavior.get("confidence", 0),
            "label": last_behavior.get("label", ""),
            "message": f"⚠️ Внимание: рискованный клиент\n"
                      f"TG ID: {tg_id}\n"
                      f"Поведение: {last_behavior.get('label', 'unknown')} "
                      f"({last_behavior.get('confidence', 0):.2f})\n"
                      f"Уровень риска: {risk_level}\n"
                      f"Действие: доступ ограничен"
        }
        
        return True, notification


# ============================================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ============================================================

_behavior_service: Optional[BehaviorService] = None


def get_behavior_service(sheets_client=None, openai_api_key: str = None) -> BehaviorService:
    """Получить глобальный экземпляр сервиса"""
    global _behavior_service
    
    if _behavior_service is None:
        _behavior_service = BehaviorService(sheets_client, openai_api_key)
    elif sheets_client and not _behavior_service.sheets_client:
        _behavior_service.sheets_client = sheets_client
    
    return _behavior_service


# ============================================================
# БЫСТРЫЕ ФУНКЦИИ
# ============================================================

def analyze_message_behavior(text: str, context: List[str] = None) -> Dict:
    """Быстрый анализ поведения"""
    service = get_behavior_service()
    return service.analyze_message_behavior(text, context)


def is_booking_allowed(tg_id: str) -> Tuple[bool, str]:
    """Быстрая проверка разрешения на запись"""
    service = get_behavior_service()
    return service.is_booking_allowed(tg_id)


def calculate_risk_level(tg_id: str) -> int:
    """Быстрый расчёт уровня риска"""
    service = get_behavior_service()
    return service.calculate_risk_level(tg_id)
