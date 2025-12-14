# Test Cases — INKA (clien_db)

This file lists the test cases for the project grouped by domain. Each test case line includes ID, Title, Preconditions, Steps, Expected Result, Priority, Type, Auto/Manual.

## A. Functional Tests (UI/Backend) — 120+

- TC-FUNC-001 | Create client from admin UI | Preconditions: Admin user logged in | Steps: Admin -> Clients -> Create Client -> Fill fields -> Save | Expected: New client appears in sheet and in UI | Priority: High | Type: Functional | Auto/Manual: Manual/Auto
- TC-FUNC-002 | Edit client | Preconditions: Client exists | Steps: Edit fields and save | Expected: Fields updated | Priority: High | Type: Functional | Auto/Manual: Auto
- TC-FUNC-003 | Delete client | Preconditions: Client exists | Steps: Delete client | Expected: Client removed from sheet + UI | Priority: High | Type: Functional | Auto/Manual: Auto
- TC-FUNC-004..TC-FUNC-120 (omitted for brevity) — include master CRUD, service CRUD, booking create/update/delete, business rules (slot validation), booking capactity constraints, schedule validation, reminders sending.

## B. API Tests (FastAPI) — 40+
- TC-API-001 | GET /health | Preconditions: Service running | Steps: Call endpoint | Expected: 200 OK, JSON {status: 'OK'} | Priority: Critical | Type: API | Auto: Yes
- TC-API-002 | POST /setup invalid token | Preconditions: None | Steps: Post with missing fields | Expected: 400 error and error message | Priority: High | Type: API | Auto: Yes
- TC-API-003..TC-API-040: All CRUD endpoints, error cases, unauthorized calls.

## C. Telegram bot (webhook) — 40
- TC-BOT-001 | Bot registration getMe | Preconditions: Bot token present | Steps: call getMe via API or library | Expected: Bot details | Priority: Critical | Type: Integration | Auto: Yes
- TC-BOT-002 | New booking via bot flow | Preconditions: Bot running, user prev created | Steps: User initiates booking flow | Expected: Booking created in sheets + confirmation to user | Priority: High | Type: E2E | Auto: Yes
- TC-BOT-003..TC-BOT-040 (cover admin flows, reminder notifications, canceled flows, aggresive user char classification)

## D. Google Sheets — 40
- TC-SHEETS-001 | Create default spreadsheet | Preconditions: Valid OAuth | Steps: Run create_google_sheets_structure.py | Expected: Template created + headers | Priority: High | Type: Integration | Auto: Yes
- TC-SHEETS-002 | Update sheet row | Preconditions: Sheet exists | Steps: Append row | Expected: Row added | Priority: Medium | Type: Integration | Auto: Yes
- TC-SHEETS-003..TC-SHEETS-040: Tests for migration, schema change, race conditions, row level update collisions, permission errors, quota handling.

## E. Google Calendar — 20
- TC-CAL-001 | Create calendar event via API | Steps: create event | Expected: Event created | Priority: High | Type: Integration | Auto: Yes
- TC-CAL-002..TC-CAL-020: Calendar permission tests, event update/delete, sync issues.

## F. Setup Wizard — 20
- TC-SETUP-001 | Load setup page | Preconditions: Service unconfigured | Steps: Open /setup | Expected: Setup HTML | Priority: High | Type: UI | Auto: Yes
- TC-SETUP-002 | Submit valid setup | Preconditions: Valid tokens & IDs | Steps: Fill out form and submit | Expected: Redirect to admin and configuration saved in Secret Manager | Priority: Critical | Type: E2E | Auto: Yes
- TC-SETUP-003..TC-SETUP-020: Edge cases: invalid tokens, missing tokens, partial configuration, network error handling.

## G. CLI Installer — 20
- TC-CLI-001 | Pre-check missing gcloud | Preconditions: gcloud not installed | Steps: Run script | Expected: Script fails gracefully with helpful message | Priority: High | Type: CLI | Auto: Yes
- TC-CLI-002 | Full deploy flow (dry-run) | Preconditions: gcloud authenticated | Steps: Run script with flags | Expected: image built & pushed, service deployed | Priority: Critical | Type: CLI | Auto: Yes
- TC-CLI-003..TC-CLI-020: Edge cases including SA creation, role assignment, API enabling errors.

## H. LLM Integration — 20
- TC-LLM-001 | Generate admin reply via OpenAI | Preconditions: OpenAI API key | Steps: Provide context and message | Expected: Non-empty response, valid string | Priority: High | Type: Functional | Auto: Yes
- TC-LLM-002 | Provider fallback (switch to Anthropic) | Preconditions: Anthropic key | Steps: Switch provider | Expected: Response from Anthropic | Priority: Medium | Type: Functional | Auto: Yes
- TC-LLM-003..TC-LLM-020: Test classification, summarization, handling of long text inputs, rate limit errors.

## I. Negative & Edge Cases — 40
- TC-NEG-001 | Invalid I/O data | Preconditions: None | Steps: Call endpoint with malformed JSON | Expected: 400 | Priority: High | Type: API | Auto: Yes
- TC-NEG-002..TC-NEG-040: Network timeouts, invalid tokens, 403 errors, race conditions, concurrency errors.

## J. Security Tests — 20
- TC-SEC-001 | Secrets not exposed in logs | Preconditions: Logs exist | Steps: Hit endpoints that would fail | Expected: logs contain no tokens | Priority: Critical | Type: Security | Auto: Yes
- TC-SEC-002..TC-SEC-020: IAM role checks, secret manager access controls, CSRF/XSS tests, input validation.

## K. Performance/Load — 20
- TC-PERF-001 | Webhook flood — 1000 msgs/sec | Preconditions: Local load generator | Steps: Run locust/k6 script | Expected: App remains responsive; errors < 5% | Priority: Critical | Type: Load | Auto: Yes
- TC-PERF-002..TC-PERF-020: Spike, stress, soak, concurrency, resource usage and TTFB latency.

## Notes
- Detailed test steps for each TC are provided in the QA system or linked spreadsheets.
- Many tests are designed to be automated. For 3rd-party API tests, use mocks where possible to avoid rate limits or cost.

*** End of Test Cases ***
