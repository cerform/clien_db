# Testing & Monitoring

This file explains how to run tests, pre-deployment checks, and use the built-in monitoring features integrated into the admin UI.

## Run all unit tests

Use a Python virtual environment, install dependencies and run pytest:

```bash
source venv/bin/activate
pip install -r requirements.txt
pytest
```

Some tests rely on FastAPI; if dependencies are not present, tests that require it will be skipped.

## Pre-deployment checks

We provide a `pre_deploy_check.py` script to validate the project before deploying:

```bash
python3 pre_deploy_check.py
```

Checks being performed include:
- Python syntax checks
- Dockerfile & requirements checks
- Environment variables check and `.env` parsing
- Google Sheets credentials
- OpenAI connectivity (attempts to query assistant)
- API endpoints (internal checks run via `TestClient`) — skipped if FastAPI not present
- Unit test run via `pytest`
- Pylint code quality check

If everything is OK, the script prints `ALL CHECKS PASSED` and exit code 0.

## Local smoke testing

You can run the application locally and manually check endpoints:

```bash
python -m uvicorn src.web.app:create_app --reload --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/api/stats
```

## Monitoring in Admin Panel

A monitoring endpoint is available at `GET /api/monitoring/checks` which runs internal health checks on key endpoints and returns a JSON report.

The Admin Panel dashboard and Web Console include a dedicated monitoring card and a "Run Monitoring" button which triggers checks and displays results in the logs.

- Web Console: `GET /console` – real-time logs and the endpoint tests widget
- Dashboard: `GET /` – monitoring card that polls the monitoring endpoint every minute

## CI Integration

- Add the `pre_deploy_check.py` as part of CI pipeline to stop faulty builds before publishing to Cloud Run.
- Add `pytest` to CI and ensure test coverage meets project metrics.

## Notes

- Some checks (OpenAI, Google Sheets) require credentials set as environment variables or configured in `.env` — for CI use secret manager to store them.
- Memory usage on Cloud Run may fail if container memory is insufficient; pre-deploy script does not emulate Cloud Run memory limits and checks logs in deployed environment for exceeding memory.

**If you need support adding these checks to CI/CD or adding more monitoring toggles/alerts, I can help integrate them with your monitoring stack (e.g., Cloud Monitoring, Sentry, or custom webhook alerts).**
