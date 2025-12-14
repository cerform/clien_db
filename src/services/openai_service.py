"""
OpenAI service wrapper - централизует работу с OpenAI/Groq клиентом

Этот модуль создаёт и инкапсулирует OpenAI/Groq клиент, предоставляя
удобный API для чат-комплитшнов и других операций, используемых движком AI.
"""
import logging
from typing import Any, Dict, List, Optional
import os

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
        function_call: Optional[str] = None,
        assistant_id: Optional[str] = None,
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
        import time
        logger.debug(f"Calling OpenAI model: {model_to_use} (messages: {len(messages)})")
        last_exc = None
        max_attempts = 3
        backoff = 0.5
        for attempt in range(1, max_attempts + 1):
            start = time.time()
            try:
                # If an Assistant ID is provided (via param or env), use the Responses/Assistants API
                # This maps the assistant response into a compatible structure expected by callers.
                assistant = assistant_id or os.getenv("OPENAI_ASSISTANT_ID")
                if assistant:
                    # Convert messages into a single input text (simple concatenation)
                    input_text = "\n".join([f"{m.get('role','user')}: {m.get('content','')}" for m in messages])
                    # Use Responses API when assistant is specified
                    try:
                        resp = self.client.responses.create(
                            assistant=assistant,
                            input=input_text,
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        )
                        # Try to extract text content in a few common locations
                        text = None
                        try:
                            # New responses structure: resp.output[0].content[0].text
                            text = resp.output[0].content[0].text
                        except Exception:
                            try:
                                # Fallback: resp.output_text
                                text = getattr(resp, 'output_text', None)
                            except Exception:
                                text = None

                        # Build a compatibility object with .choices[0].message.content
                        class Choice:
                            def __init__(self, txt):
                                self.message = type('M', (), {'content': txt})

                        class RespObj:
                            def __init__(self, c):
                                self.choices = [Choice(c)]

                        return RespObj(text)
                    except Exception as e:
                        logger.warning(f"Assistant response call failed: {e}")
                        # Fall through to chat completions

                # Build parameters dynamically to avoid sending `function_call`
                # when `functions` are not provided (OpenAI rejects that).
                params = {
                    "model": model_to_use,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if functions:
                    params["functions"] = functions
                    # If functions are provided but caller didn't request a specific
                    # function_call behavior, default to 'auto'
                    params["function_call"] = function_call if function_call is not None else "auto"

                resp = self.client.chat.completions.create(**params)
                elapsed = time.time() - start
                logger.info(f"OpenAI call success: model={model_to_use} attempt={attempt} time={elapsed:.3f}s")
                try:
                    from src.services.telemetry import incr
                    incr("llm_client_success", 1)
                    incr("llm_client_latency_ms", int(elapsed * 1000))
                except Exception:
                    pass
                return resp
            except Exception as e:
                elapsed = time.time() - start
                logger.warning(f"OpenAI call failed (attempt {attempt}/{max_attempts}) after {elapsed:.3f}s: {e}")
                last_exc = e
                try:
                    from src.services.telemetry import incr
                    incr("llm_client_errors", 1)
                except Exception:
                    pass
                # Exponential backoff with jitter
                import random, time as _tt
                _tt.sleep(backoff * (2 ** (attempt - 1)) * (0.8 + 0.4 * random.random()))
                continue

        # If we get here, all attempts failed
        logger.error(f"OpenAI call failed after {max_attempts} attempts: {last_exc}")
        try:
            from src.services.telemetry import incr
            incr("llm_client_failed_after_retries", 1)
        except Exception:
            pass
        raise last_exc

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

