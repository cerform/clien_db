FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc wget && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PYTHONUNBUFFERED=1
ENV CLOUD_RUN_ENV=false
CMD ["python", "examples_s2_booking_engine.py"]
