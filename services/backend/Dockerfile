FROM python:3.12-slim
WORKDIR /app
# install build deps
RUN apt-get update && apt-get install -y gcc wget && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PYTHONUNBUFFERED=1
ENV CLOUD_RUN_ENV=false
EXPOSE 8080
CMD ["python", "src/web/app.py"]
