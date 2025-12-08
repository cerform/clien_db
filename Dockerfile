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
# Добавить симлинк python -> python3 для совместимости
RUN ln -s /usr/local/bin/python3 /usr/local/bin/python

# Создание пользователя для безопасности
RUN useradd -m -u 1000 botuser && \
    mkdir -p /app && \
    chown -R botuser:botuser /app

WORKDIR /app

# Копирование установленных пакетов из builder
COPY --from=builder --chown=botuser:botuser /root/.local /home/botuser/.local

# Копирование кода приложения
COPY --chown=botuser:botuser . .

# Явное копирование credentials.json с правильными разрешениями (если существует)
# Эта команда нужна для явного указания пути в /app/
# RUN if [ -f credentials.json ]; then cp credentials.json /app/credentials.json && chown botuser:botuser /app/credentials.json; fi

# Обновление PATH
ENV PATH=/home/botuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Переменные окружения для Cloud Run
# NOTE: Cloud Run использует native Service Account - credentials.json не нужен
# Аутентификация происходит через google.auth.default() которая автоматически
# использует Service Account Cloud Run
ENV TIMEZONE="Asia/Jerusalem"
ENV LOG_LEVEL="INFO"

# Переключение на непривилегированного пользователя
USER botuser

# Healthcheck для Cloud Run
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Порт для Cloud Run
EXPOSE 8080

# Запуск Cloud Run entrypoint
CMD ["python", "-u", "run_cloud.py"]
