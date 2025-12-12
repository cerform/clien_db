Microservices scaffolding for local development

This folder contains simple service wrappers and Dockerfiles to run the project as microservices:
- backend: FastAPI API / web app
- bot: Telegram webhook service (uses aiogram)
- ai: LLM/worker service (orchestrator)
- frontend: a simple static admin UI (optional - placeholder)

Use the docker-compose.yml in the project root to run them together locally.
