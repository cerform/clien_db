# Tattoo Studio Bot — Human-like Dialog Design

Summary
-------
This document describes the design and implementation changes made to transform the Telegram receptionist into a human-like LLM-powered administrator.

Core principles
---------------
- Sound like a live administrator (calm, confident, professional).
- Ask one contextual question at a time; never send checklist-style questionnaires.
- Do not ask for dates/times until the client shows readiness.
- Automatically detect and reply only in the user's language (ru/en/he).
- Classify client psychotype silently and adjust pace (Aggressive/Hesitant/VIP/Neutral).
- Never claim to be a bot/AI or refer to system internals; never invent dates/prices/availability.

Key code changes
----------------
- `src/services/ai_dialog_engine.py`: client-facing system prompt tightened to enforce one-question-at-a-time, phase flow, psychotype classification, and anti-prompt rules.
- `src/services/ai_consultant.py`: consultation prompt updated with behavioral constraints (avoid asking date/time early, ask one question at a time).
- `src/bot/handlers/inka_handler.py`: `/start` welcome message changed to Phase 1 style — short invitation to describe the idea and a single question about experience.
- `tests/test_dialog_constraints.py`: new tests validating presence of rules in prompts and absence of emojis / bullet lists in start messages.

Developer notes
---------------
- The system prompt is intentionally prescriptive. If you need to tune tone or behavior, change the strings in:
  - `AIDialogEngine._get_system_prompt` (client section)
  - `AIConsultant._build_system_prompt`

- When modifying prompts, keep the same constraints: one question at a time, no form-like messages, no promises, and never reveal internal system facts.

Testing
-------
- New unit tests were added to assert presence of key constraints. Run full tests locally:

```bash
pytest -q
```

If integration tests fail due to environment (database or webhook initialization), ensure local env vars and test DB are configured per developer README.

Examples of client messages (Phase 1)
-----------------------------------
- ru: "Здравствуйте! Расскажите, что вы хотите сделать — опишите идею или пришлите референсы. Это первая татуировка или у вас уже есть опыт?"
- en: "Hello. Please tell me what you'd like to do — describe your idea or send references. Is this your first tattoo or do you have previous tattoos?"

Behavior reminders for designers
--------------------------------
- Avoid leading the client by asking multiple things at once.
- Delay offering slots until the client's readiness is clear.
- If the LLM is uncertain, ask exactly one clarifying question.

License
-------
This project follows the repository's existing license.
