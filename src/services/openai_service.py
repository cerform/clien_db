"""
OpenAI service wrapper - централизует работу с OpenAI/Groq клиентом

Этот модуль создаёт и инкапсулирует OpenAI/Groq клиент, предоставляя
удобный API для чат-комплитшнов и других операций, используемых движком AI.
"""
import logging
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

import httpx

logger = logging.getLogger(__name__)


class OpenAIService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 30.0):
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"
        self.client = None
        self.api_enabled = False

        if api_key and OpenAI:
            try:
                http_client = httpx.Client(verify=True, timeout=timeout)
                client_kwargs = {
                    "api_key": api_key,
                    "http_client": http_client,
                    "timeout": timeout,
                    "max_retries": 2
                }
                if api_key.startswith("gsk_"):
                    client_kwargs["base_url"] = "https://api.groq.com/openai/v1"
                self.client = OpenAI(**client_kwargs)
                self.api_enabled = True
                logger.info("✅ OpenAIService initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize OpenAI client: {e}")
                self.client = None
                self.api_enabled = False
        else:
            logger.info("ℹ️ OpenAI API is not available (running fallback)")

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict]] = None,
        function_call: Optional[str] = "auto",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        model: Optional[str] = None
    ) -> Any:
        """Call the chat completion endpoint with the established client.

        Returns API response object. Raises exception on failure.
        """
        if not self.api_enabled or not self.client:
            raise RuntimeError("OpenAI API not enabled or client missing")

        model_to_use = model or self.model
        logger.debug(f"Calling OpenAI model: {model_to_use} (messages: {len(messages)})")
        return self.client.chat.completions.create(
            model=model_to_use,
            messages=messages,
            functions=functions,
            function_call=function_call,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def simple_summary(self, messages: List[Dict], max_tokens: int = 200) -> Optional[str]:
        if not self.api_enabled:
            return None
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to create summary: {e}")
            return None


__all__ = ["OpenAIService"]

