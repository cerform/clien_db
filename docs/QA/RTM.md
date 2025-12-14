# Requirements Traceability Matrix (RTM)

| Req ID | Requirement description | Test Cases (IDs) | Auto/Manual | Status |
|--------|-------------------------|------------------|-------------|--------|
| R-001  | Bot accepts bookings via Telegram | TC-BOT-001, TC-BOT-002, TC-E2E-BOOKING-001 | Auto/E2E | Covered |
| R-002  | Admin panel supports CRUD for masters | TC-UI-MASTERS-001..005 | Auto/UI | Covered |
| R-003  | Google Sheets schema matches LLM requirements | TC-SHEETS-001..020 | Auto/Manual | Covered |
| R-004  | Webhook securely handles Telegram updates | TC-BOT-WEBHOOK-001..010 | Auto | Covered |
| R-005  | LLM classification of tone works | TC-LLM-CLS-001..010 | Auto | Covered |
| R-006  | Setup wizard saves configs securely | TC-SETUP-001..020 | Auto/UI | Covered |

(Full RTM in CSV: docs/QA/rtm_full.csv)
