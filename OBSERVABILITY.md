# Observability setup (Sentry & Cloud Logging)

This file documents how to configure Sentry and Google Cloud Logging (Stackdriver) for the application.

Sentry
- Install: Sentry SDK is already included in `requirements.txt` (sentry-sdk).
- Configure DSN: Set `SENTRY_DSN` environment variable in the deployment environment.
- The application initializes Sentry if `SENTRY_DSN` is set in `src/web/app.py`.
- Use the `sentry_sdk` API to report messages or exceptions as needed from code.

Google Cloud Logging
- Install: `google-cloud-logging` package (already included).
- Enable Cloud Logging: set `ENABLE_CLOUD_LOGGING=true` and ensure the service account used has `roles/logging.logWriter` role.
- The app will call `client.setup_logging()` to forward logs to Cloud Logging.

Best practices
- Keep DSNs and secrets in the environment or secret manager; do not commit values into repo.
- Configure log levels and sample rates carefully; Sentry sampling (`traces_sample_rate`) should be tuned for production.
- Use structured logs (JSON) for better querying in Cloud Logging.
