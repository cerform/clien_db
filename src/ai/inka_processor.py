"""
INKA Processor

Provides staged processing similar to the `fix-e2e-test` branch: a strict
JSON classifier (stage 1) and a booking-engine helper (stage 2). The goal is
to provide deterministic, machine-readable signals (S1) that downstream
logic or the main AI engine can use to reliably decide on actions.

This is intentionally lightweight and integrates with our existing
`OpenAIService` and `INKALearningSystem` components.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from src.services.openai_service import OpenAIService
from src.ai.inka_learning import get_inka_learning

logger = logging.getLogger(__name__)


class INKAProcessor:
    def __init__(self, openai_service: Optional[OpenAIService] = None, services: Optional[dict] = None):
        self.openai = openai_service
        # services may include booking_service, calendar_service, etc.
        self.services = services or {}
        self.inka_learning = get_inka_learning()

    def _build_stage1_prompt(self, user_message: str, user_info: Optional[Dict] = None) -> str:
        user_info = user_info or {}
        base = (
            "You are a classifier that must OUTPUT ONLY valid JSON following the schema described.\n"
            "Do not add any explanatory text.\n"
            "Schema: {\n"
            "  \"intent\": \"string\", // e.g. \"create_booking\", \"ask_price\", \"greeting\"\n"
            "  \"booking_needed\": \"boolean\",\n"
            "  \"booking_details\": {\n"
            "    \"date\": \"YYYY-MM-DD\",\n"
            "    \"time\": \"HH:MM\",\n"
            "    \"service\": \"string\",\n"
            "    \"master_id\": \"string\"\n"
            "  },\n"
            "  \"language\": \"string\",\n"
            "  \"confidence\": \"float(0..1)\"\n"
            "}\n"
        )

        try:
            learning_ctx = self.inka_learning.build_prompt_context()
            base += "\n" + learning_ctx
        except Exception:
            pass

        base += f"\nUser message: {user_message}\n"
        base += f"\nContext user: {json.dumps(user_info, ensure_ascii=False)}\n"
        base += "\nRespond with strict JSON only."
        return base

    def stage_1_classify(self, user_message: str, user_info: Optional[Dict] = None) -> Dict[str, Any]:
        """Run stage 1 classifier and return parsed JSON structure.

        If OpenAI API is not available, a small heuristic fallback is used.
        """
        prompt = self._build_stage1_prompt(user_message, user_info)

        if not self.openai or not getattr(self.openai, 'api_enabled', False):
            logger.debug("INKAProcessor: OpenAI unavailable, using heuristic stage1")
            # Heuristic: if typical booking words present - mark booking
            text = user_message.lower()
            booking_keywords = ['запись', 'записаться', 'записать', 'booking', 'appointment', 'запис', 'хочу']
            is_booking = any(k in text for k in booking_keywords)
            intent = 'create_booking' if is_booking else ('greeting' if 'прив' in text or 'hi' in text else 'chat')
            return {
                'intent': intent,
                'booking_needed': is_booking,
                'booking_details': {},
                'language': 'ru' if any('\u0400' <= c <= '\u04FF' for c in user_message) else ('he' if any('\u0590' <= c <= '\u05FF' for c in user_message) else 'en'),
                'confidence': 0.6
            }

        try:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message}
            ]
            resp = self.openai.chat_completion(messages=messages, temperature=0.0, max_tokens=200)
            content = resp.choices[0].message.content
            # Try parse as JSON
            try:
                parsed = json.loads(content)
                return parsed
            except Exception:
                # Some models might return JSON wrapped in backticks or with trailing text
                txt = content.strip().strip('`')
                try:
                    parsed = json.loads(txt)
                    return parsed
                except Exception as e:
                    logger.warning(f"INKAProcessor: failed to parse S1 JSON: {e} - raw: {content}")
                    return {
                        'intent': 'chat',
                        'booking_needed': False,
                        'booking_details': {},
                        'language': 'ru',
                        'confidence': 0.0,
                        'raw': content
                    }
        except Exception as e:
            logger.exception(f"INKAProcessor.stage_1_classify error: {e}")
            return {'intent': 'chat', 'booking_needed': False, 'booking_details': {}, 'language': 'ru', 'confidence': 0.0}

    def stage_2_booking_engine(self, classification: Dict[str, Any], user_message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Produce booking suggestions / slot proposals based on S1 classification.

        Returns structured JSON with the following schema:

        {
          "suggested_slots": [
            {
              "slot_id": "string",
              "date": "YYYY-MM-DD",
              "time": "HH:MM",
              "end_time": "HH:MM",
              "master_id": "string",
              "service": "string",
              "available": true|false,
              "source": "calendar|heuristic|llm",
              "confidence": 0.0-1.0
            }
          ],
          "reason": "string",
          "confidence": 0.0-1.0
        }

        The LLM must return strict JSON only. If the OpenAI API is not
        available we return a deterministic fallback.
        """
        if not classification.get('booking_needed'):
            return {'suggested_slots': [], 'reason': 'no_booking_needed'}

        prompt_lines = [
            "You are a booking assistant. Produce ONLY valid JSON following the schema described below.",
            "Schema: {\n  \"suggested_slots\": [ {\n    \"slot_id\": \"string\",\n    \"date\": \"YYYY-MM-DD\",\n    \"time\": \"HH:MM\",\n    \"end_time\": \"HH:MM\",\n    \"master_id\": \"string\",\n    \"service\": \"string\",\n    \"available\": true|false,\n    \"source\": \"calendar|heuristic|llm\",\n    \"confidence\": 0.0\n  } ],\n  \"reason\": \"string\",\n  \"confidence\": 0.0\n}\n",
            "Return an array of up to 5 suggested_slots ordered by best match. Do not include explanatory text."
        ]

        try:
            if self.openai and getattr(self.openai, 'api_enabled', False):
                messages = [
                    {"role": "system", "content": "\n".join(prompt_lines)},
                    {"role": "user", "content": f"User message: {user_message}\nClassification: {json.dumps(classification, ensure_ascii=False)}\nContext: {json.dumps(context or {}, ensure_ascii=False)}"}
                ]
                resp = self.openai.chat_completion(messages=messages, temperature=0.0, max_tokens=400)
                content = resp.choices[0].message.content
                try:
                    parsed = json.loads(content)
                    # If we can, validate availability using booking/slot engine
                    try:
                        return self._validate_suggested_slots(parsed, classification)
                    except Exception:
                        return parsed
                except Exception:
                    txt = content.strip().strip('`')
                    try:
                        parsed = json.loads(txt)
                        return parsed
                    except Exception:
                        logger.warning(f"INKAProcessor: failed to parse S2 JSON - raw: {content}")
                        return {'suggested_slots': [], 'raw': content}
            else:
                # Heuristic fallback: suggest 'tomorrow 12:00' as a dummy slot
                import datetime
                tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
                slots = [{
                    'slot_id': 'heur-1',
                    'date': tomorrow,
                    'time': '12:00',
                    'end_time': '13:00',
                    'master_id': '1',
                    'service': classification.get('booking_details', {}).get('service', 'tattoo'),
                    'available': True,
                    'source': 'heuristic',
                    'confidence': 0.5
                }]
                try:
                    return self._validate_suggested_slots({'suggested_slots': slots, 'reason': 'heuristic_fallback', 'confidence': 0.5}, classification)
                except Exception:
                    return {'suggested_slots': slots, 'reason': 'heuristic_fallback', 'confidence': 0.5}
        except Exception as e:
            logger.exception(f"INKAProcessor.stage_2_booking_engine error: {e}")
            return {'suggested_slots': []}

    def _validate_suggested_slots(self, parsed: Dict[str, Any], classification: Dict[str, Any]) -> Dict[str, Any]:
        """Check suggested_slots against booking_service availability when available.

        This will set `available` True/False and `source` to 'calendar' if confirmed via slot engine,
        otherwise keep existing `source` and set `available` accordingly.
        """
        slots = parsed.get('suggested_slots', []) if isinstance(parsed, dict) else []
        if not slots:
            return parsed

        duration = classification.get('booking_details', {}).get('duration', 60)
        bs = self.services.get('booking_service') if self.services else None
        validated = []
        from datetime import datetime, timedelta
        for s in slots:
            try:
                s_copy = dict(s)
                date = s_copy.get('date')
                time = s_copy.get('time')
                master_id = s_copy.get('master_id')
                # compute end_time if missing
                if not s_copy.get('end_time') and time and duration:
                    hh, mm = map(int, (time.split(':') if isinstance(time, str) else ['12','0']))
                    start_dt = datetime.fromisoformat(f"{date}T{time}")
                    end_dt = (start_dt + timedelta(minutes=int(duration))).time().strftime("%H:%M") if duration else None
                    s_copy['end_time'] = end_dt

                available = None
                if bs and date and master_id:
                    try:
                        avail = bs.list_available_slots(date, master_id)
                        # normalize times
                        found = any((a.get('start').strftime('%H:%M') if hasattr(a.get('start'), 'strftime') else a.get('time') == s_copy.get('time')) or (a.get('time') == s_copy.get('time')) for a in avail)
                        available = bool(found)
                        if available:
                            s_copy['source'] = 'calendar'
                        else:
                            s_copy['source'] = s_copy.get('source', 'llm')
                    except Exception:
                        available = s_copy.get('available', False)
                else:
                    available = s_copy.get('available', False)

                s_copy['available'] = bool(available)
                # ensure confidence present
                s_copy['confidence'] = float(s_copy.get('confidence', 0.5))
                validated.append(s_copy)
            except Exception:
                validated.append(s)

        parsed['suggested_slots'] = validated
        return parsed

    def stage_3_reserve_slot(self, slot: Dict[str, Any], user_id: int, client_name: str = '', client_phone: str = '', notes: str = '') -> Dict[str, Any]:
        """Attempt to reserve a suggested slot.

        This will try to create a pending booking via BookingService (which uses
        Postgres slot_engine if configured) and return a structured result.

        Returns:
          { success: bool, booking_id: str|None, event_id: str|None, message: str, requires_confirmation: bool }
        """
        bs = self.services.get('booking_service') if self.services else None
        if not bs:
            return {'success': False, 'booking_id': None, 'event_id': None, 'message': 'Booking service not available', 'requires_confirmation': False}

        try:
            # slot expected: {date, time, end_time, master_id, service}
            date = slot.get('date')
            time = slot.get('time')
            end_time = slot.get('end_time') or slot.get('time')
            master_id = slot.get('master_id')
            service_name = slot.get('service') or slot.get('service_id')

            res = bs.create_booking(client_telegram_id=user_id, client_name=client_name or f'user_{user_id}', client_phone=client_phone or '', date=date, master_id=master_id, slot_start=time, slot_end=end_time, notes=notes)
            booking_id = res.get('booking_id') if isinstance(res, dict) else None
            event_id = res.get('event_id') if isinstance(res, dict) else None

            success = bool(booking_id)
            message = 'Pending booking created' if booking_id else 'Failed to create pending booking'
            # We treat booking_id presence as requiring confirmation (pending) in most deployments
            requires_confirmation = True if booking_id else False
            return {'success': success, 'booking_id': booking_id, 'event_id': event_id, 'message': message, 'requires_confirmation': requires_confirmation}
        except Exception as e:
            logger.exception(f"stage_3_reserve_slot error: {e}")
            return {'success': False, 'booking_id': None, 'event_id': None, 'message': str(e), 'requires_confirmation': False}


__all__ = ["INKAProcessor"]
