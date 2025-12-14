# INKA updates

- Added structured LLM responses via `INKAConsultant.respond_structured` which asks the model to return a JSON contract:
  - text: human-readable reply (1-3 short sentences)
  - next_action: `continue_consultation|offer_slots|other`
  - meta: contains `antirepeat_key` and `client_profile`

- Anti-repeat enforcement:
  - A short key (`antirepeat_key`) is generated and stored in FSM state (`last_antirepeat_key`). If a new message would produce the same key, the bot asks the user to rephrase instead of repeating the same reply.

- FSM session persistence improvements:
  - `client_profile` and `inka_stage` are persisted in FSMContext for later S2 booking flows (S0..S7 can be implemented on top of these values).

- Admin debug command added: `/session` (admin-only) — dumps the current FSM session data for debugging.

- Fixed persona naming: replaced references to 'Anna'/'Аня' with the correct bot name **INKA**, and allowed INKA to identify herself briefly when asked.

Notes:
- This change prepares the codebase for a full S0..S7 state machine and structured booking integration with the S2 booking engine.
- Tests added: `tests/test_inka_structured.py`, `tests/test_inka_process.py` (unit tests validate stable antirepeat key generation and structured fallback responses).
