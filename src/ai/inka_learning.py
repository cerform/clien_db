"""
INKA Learning System
Provides a safe, admin-controlled "learning" store where admins can add
approved rules, FAQs, style guidelines and forbidden behaviors. It does NOT
fine-tune models — instead, it builds a prompt context that is injected into
the LLM system prompt.

Files are stored under the `learning/` directory in JSON files and audit.log.
"""
from __future__ import annotations

import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import logging

logger = logging.getLogger(__name__)


class INKALearningSystem:
    """
    Controlled learning system for INKA.
    Stores admin-approved knowledge and injects it into prompts.
    """

    BASE_DIR = Path("learning")

    FILES = {
        "rules": "rules.json",
        "faq": "faq.json",
        "style": "style.json",
        "forbidden": "forbidden.json",
    }

    def __init__(self):
        # Ensure base directory
        self.BASE_DIR.mkdir(exist_ok=True)
        # Create empty files if missing
        for file in self.FILES.values():
            path = self.BASE_DIR / file
            if not path.exists():
                path.write_text("{}", encoding="utf-8")

        # Lock for thread-safe file writes
        self._lock = threading.Lock()

    # ---------- PUBLIC API ----------

    def teach_rule(self, key: str, description: str) -> None:
        self._save("rules", key, description)

    def teach_faq(self, question: str, answer: str) -> None:
        # Use question as key for simplicity (strip whitespace)
        q = question.strip()
        self._save("faq", q, answer)

    def teach_style(self, key: str, value: str) -> None:
        self._save("style", key, value)

    def forbid_behavior(self, key: str, description: str) -> None:
        self._save("forbidden", key, description)

    def get(self, category: str, key: str) -> Optional[Any]:
        data = self._load(category)
        return data.get(key)

    def list(self, category: str) -> Dict[str, Any]:
        return self._load(category)

    def build_prompt_context(self) -> str:
        """
        Builds a SYSTEM PROMPT injection from learned data
        """
        rules = self._load("rules")
        faq = self._load("faq")
        style = self._load("style")
        forbidden = self._load("forbidden")

        prompt_lines = [
            "You are INKA — professional tattoo studio assistant.",
            "The following admin-approved rules, style guides and FAQs are authoritative for this session.",
            "",
            "=== BEHAVIOR RULES ===",
        ]

        for r in rules.values():
            prompt_lines.append(f"- {r}")

        prompt_lines.append("")
        prompt_lines.append("=== FORBIDDEN ACTIONS ===")
        for f in forbidden.values():
            prompt_lines.append(f"- {f}")

        prompt_lines.append("")
        prompt_lines.append("=== STYLE GUIDE ===")
        for k, v in style.items():
            prompt_lines.append(f"{k}: {v}")

        prompt_lines.append("")
        prompt_lines.append("=== FAQ KNOWLEDGE ===")
        for q, a in faq.items():
            prompt_lines.append(f"Q: {q}\nA: {a}")

        prompt = "\n".join(prompt_lines)
        return prompt

    # ---------- INTERNAL ----------

    def _save(self, category: str, key: str, value: str) -> None:
        with self._lock:
            data = self._load(category)
            data[key] = value
            self._write(category, data)
            self._audit(f"LEARN[{category}]: {key}")

    def _load(self, category: str) -> Dict[str, Any]:
        path = self.BASE_DIR / self.FILES[category]
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return {}
        if not content.strip():
            return {}
        try:
            return json.loads(content)
        except Exception as e:
            logger.exception(f"Failed to load {category}: {e}")
            return {}

    def _write(self, category: str, data: Dict[str, Any]) -> None:
        path = self.BASE_DIR / self.FILES[category]
        ps = json.dumps(data, ensure_ascii=False, indent=2)
        path.write_text(ps, encoding="utf-8")

    def _audit(self, event: str) -> None:
        try:
            with open(self.BASE_DIR / "audit.log", "a", encoding="utf-8") as f:
                f.write(f"{datetime.datetime.now(datetime.timezone.utc).isoformat()} | {event}\n")
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")


# Module-level singleton
_INKA_LEARNING: Optional[INKALearningSystem] = None


def get_inka_learning() -> INKALearningSystem:
    global _INKA_LEARNING
    if _INKA_LEARNING is None:
        _INKA_LEARNING = INKALearningSystem()
    return _INKA_LEARNING


    # Public helper for logging admin event with actor
def log_admin_event(actor: str, event: str) -> None:
    try:
        il = get_inka_learning()
        il._audit(f"{actor}: {event}")
    except Exception:
        logger.warning("Failed to log admin event")


__all__ = ["INKALearningSystem", "get_inka_learning"]
# End of file
