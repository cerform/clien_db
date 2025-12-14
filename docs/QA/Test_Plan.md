# Test Plan — INKA

## Objectives
Проверить стабильность и корректность работы INKA в продакшен-условиях и обеспечить 100% покрытие бизнес требований.

## Schedule
- Week 1 — Architecture review, create tests skeletons, unit test coverage
- Week 2 — Integration tests and E2E tests creation
- Week 3 — Load testing and security tests
- Week 4 — Regression testing and final release

## Roles
- QA Lead: oversees QA
- QA Engineers: design and implement tests
- DevOps: pipeline and infra
- Developers: fix defects and implement changes

## Communication
Use GitHub for issues, Slack for real-time alerts, and email for TRR/QCR.

## Entry criteria
- Requirements agreed and up to date
- Dev branch ready with setup and basic features
- CI pipeline available

## Exit criteria
- All critical defects closed
- E2E and integration success in CI for 3 consecutive builds
- Performance metrics within expected KPIs

## Tools
- pytest, playwright, locust/k6, Jenkins, flake8, bandit

## Risks and dependencies
- External API availability
- Access credentials

