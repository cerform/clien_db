import os
from typing import Optional
from src.core.config_manager import get_secret

class LLMClient:
    """Light-weight LLM adapter — supports OpenAI and Claude through a simple provider switching.

    Usage:
        client = LLMClient(provider='openai')
        reply = client.generate_admin_reply(...)
    """
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        self.provider = provider.lower() if provider else "openai"
        self.api_key = api_key or get_secret("LLM_API_KEY")
        # Lazy imports
        self._client = None

    def _ensure_openai(self):
        try:
            import openai
            self._client = openai
            self._client.api_key = self.api_key
        except Exception as ex:
            raise RuntimeError("OpenAI library not installed or failed to import: %s" % ex)

    def _ensure_anthropic(self):
        try:
            import anthropic
            self._client = anthropic
        except Exception as ex:
            raise RuntimeError("Anthropic library not installed or failed to import: %s" % ex)

    def generate_admin_reply(self, context: str, user_message: str, state: dict | None = None) -> str:
        """Generates an admin-oriented reply from the configured LLM provider."""
        if self.provider == "openai":
            if not self._client:
                self._ensure_openai()
            # Build a standard Chat Completion
            messages = [{"role": "system", "content": context}, {"role": "user", "content": user_message}]
            resp = self._client.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
            return resp["choices"][0]["message"]["content"]
        elif self.provider == "anthropic" or self.provider == "claude":
            if not self._client:
                self._ensure_anthropic()
            # Simple Anthropic text generation (pseudo code)
            client = self._client.Client(api_key=self.api_key)
            prompt = f"Assistant: {context}\nUser: {user_message}"
            resp = client.completions.create(model="claude-2.1", prompt=prompt)
            return resp.completion
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def classify_client_tone(self, message: str) -> str:
        """Light classification wrapper that uses LLM to classify tone into categories."""
        prompt = f"Classify the sentiment of the message into: aggressive, persistent, calm. Message: {message}\nReturn single-word label."
        result = self.generate_admin_reply("Tone classifier", prompt)
        return result.strip().lower()

    def summarize_client_history(self, client_data: list) -> str:
        prompt = "Summarize client's history: " + (str(client_data)[:5000])
        return self.generate_admin_reply("Summary", prompt)
