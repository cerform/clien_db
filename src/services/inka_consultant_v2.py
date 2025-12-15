import logging
from typing import Dict, Optional

from src.services.openai_service import OpenAIService
from src.services.inka_llm_orchestrator import INKALLMOrchestrator
from src.services.telemetry import incr

logger = logging.getLogger(__name__)


class INKAConsultantV2:
    """
    Advanced LLM-driven consultant (S1).
    """

    def __init__(self, api_key: str):
        self.llm_service = OpenAIService(api_key=api_key)
        self.orchestrator = INKALLMOrchestrator(
            openai_service=self.llm_service,
            model="gpt-4.1-mini"
        )

    def respond(
        self,
        message: str,
        client_state: Optional[Dict] = None
    ) -> Dict:
        """
        Main S1 entrypoint.

        Returns:
        {
          response: text,
          route,
          stage,
          booking_type,
          next_action
        }
        """
        incr("s1_consultant_calls", 1)

        client_state = client_state or {}

        try:
            decision = self.orchestrator.run(
                message=message,
                state=client_state
            )

            logger.info(
                "INKA decision | route=%s stage=%s next=%s",
                decision["route"],
                decision["stage"],
                decision["next_action"]
            )

            return {
                "response": decision["reply"],
                "route": decision["route"],
                "stage": decision["stage"],
                "booking_type": decision["booking_type"],
                "next_action": decision["next_action"],
            }

        except Exception as e:
            incr("s1_consultant_fail", 1)
            logger.exception("❌ INKAConsultantV2 failed: %s", e)

            return {
                "response": "Извини, сейчас я передам тебя администратору.",
                "route": "other",
                "stage": "none",
                "booking_type": "tattoo",
                "next_action": "handover_human",
            }
