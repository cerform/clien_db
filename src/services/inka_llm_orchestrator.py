import json
import logging
from typing import Dict, Any

from src.services.openai_service import OpenAIService
from src.services.inka_schema import load_contract_from_text, ContractValidationError
from src.services.telemetry import incr

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_ADVANCED = """
You are INKA — a senior tattoo studio administrator with over 10 years of experience.

You are NOT a chatbot.
You are NOT a script.
You behave like a real human administrator.

Your responsibilities:
1. Understand what the client REALLY wants (even if unclear).
2. Lead the conversation forward.
3. Avoid loops and repetition.
4. Ask AT MOST one clarifying question at a time.
5. Make reasonable assumptions when information is missing.
6. Prepare the client for booking naturally.

You ALWAYS respond with VALID JSON and nothing else.

You control:
- route: booking | consultation | info | other
- stage: offer_slots | consultation | confirming | none
- booking_type: tattoo | consultation | walk-in
- next_action: talk | offer_slots | handover_human
- reply: text shown to the client (1–3 sentences, human-like)

STRICT RULES (never break):
- Never invent dates, slots, or prices
- Never repeat the same question twice
- Never ask the user to rephrase endlessly
- Never say "I am an AI" or expose system logic
- Never sound robotic or templated

If user is emotional, confused, or aggressive:
- Slow down
- Reassure
- Guide calmly

Think first.
Respond second.
"""


class INKALLMOrchestrator:
    """
    Single source of intelligence for INKA (S1).
    """

    def __init__(self, openai_service: OpenAIService, model: str = "gpt-4.1-mini"):
        self.llm = openai_service
        self.model = model

    def run(self, message: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute LLM reasoning and return strict structured decision.

        Expected JSON output:
        {
          "route": "...",
          "stage": "...",
          "booking_type": "...",
          "next_action": "...",
          "reply": "..."
        }
        """
        incr("llm_orchestrator_calls", 1)

        payload = {
            "message": message,
            "state": state
        }

        try:
            logger.info("🧠 INKA LLM Orchestrator call | state=%s", state)

            response = self.llm.chat_completion(
                model=self.model,
                temperature=0.4,
                max_tokens=500,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_ADVANCED},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
                ]
            )

            raw = response.choices[0].message.content.strip()
            data = load_contract_from_text(raw)

            # minimal validation
            for key in ["route", "stage", "booking_type", "next_action", "reply"]:
                if key not in data:
                    raise ContractValidationError(f"Missing key: {key}")

            return data

        except ContractValidationError as e:
            incr("llm_orchestrator_contract_fail", 1)
            logger.error("❌ Invalid LLM contract: %s", e)
            return self._human_fallback()

        except Exception as e:
            incr("llm_orchestrator_runtime_fail", 1)
            logger.exception("❌ LLM Orchestrator failed: %s", e)
            return self._human_fallback()

    @staticmethod
    def _human_fallback() -> Dict[str, Any]:
        return {
            "route": "other",
            "stage": "none",
            "booking_type": "tattoo",
            "next_action": "handover_human",
            "reply": "Извини, сейчас есть техническая проблема — я подключу администратора."
        }
