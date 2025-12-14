# QA Strategy — INKA (clien_db)

## Overview
Полная QA-стратегия для проекта INKA — Telegram бот и админ-панель с Google Sheets/Calendar интеграцией и LLM.

### Modules
- Bot (aiogram)
- Web Admin (FastAPI)
- Google Sheets (main DB)
- Google Calendar
- LLM Adapter (OpenAI/Anthropic)
- Setup/Installer (CLI + web setup)
- CI/CD (Cloud Run deploy)

## Scope
Полный охват: функциональное, интеграционное, E2E, нагрузочное, безопасность, тестирование установщика, webhook и CI.

## Levels of Testing
- Unit: All core functions, adapters, validators, error handlers
- Integration: Sheets/Calendar adapter interactions, Bot→LLM→Sheets flows (mocked where appropriate)
- System/E2E: End-to-end scenarios via Playwright + API calls + Webhook simulation
- Performance: Locust / K6 for webhook flood and user concurrency
- Security: Secret leaks, IAM, token validation

## Automation Strategy
- Unit and integration: pytest
- E2E: Playwright
- Load: Locust or K6 scripts in /tests/performance
- CI: Jenkinsfile (stages for Lint, Unit, Integration, E2E, Performance, and Security scans)

## Data Strategy
- Use test spreadsheets and Calendar test resources
- Setup fixtures to create/delete test spreadsheets
- Mock LLM and Telegram in unit/integration tests
- Use ephemeral Google test accounts for CI

## Environments
- Local dev: .eco virtualenv, OAuth to local credentials.json
- CI: ephemeral service account with minimal roles, token injection
- Prod: Cloud Run, secret manager

## Risks
- Flaky external APIs (Google, Telegram, LLM) — mitigate by mocking in unit/integration tests and limited integration tests against dev environments
- Rate limits / quota issues in API calls
- Secrets leakage
- Sheet schema drift

## KPIs
- Unit coverage >= 80%
- E2E success rate 100% per suite run
- No critical and high severity bugs before release
- Performance: < 200ms median for typical bot handling; capable of processing 50 messages/s under simulated load

