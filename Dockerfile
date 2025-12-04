# Multi-stage build для оптимизации размера образа
FROM python:3.10-slim as builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.10-slim

# Создание пользователя для безопасности
RUN useradd -m -u 1000 botuser && \
    mkdir -p /app && \
    chown -R botuser:botuser /app

WORKDIR /app

# Копирование установленных пакетов из builder
COPY --from=builder --chown=botuser:botuser /root/.local /home/botuser/.local

# Копирование кода приложения
COPY --chown=botuser:botuser . .

# Обновление PATH
ENV PATH=/home/botuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Переключение на непривилегированного пользователя
USER botuser

# Healthcheck для Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Порт для Cloud Run
EXPOSE 8080

# Запуск production бота с полной интеграцией
CMD ["python", "-u", "run_production.py"]
