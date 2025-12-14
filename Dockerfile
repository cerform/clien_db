# Use official Python runtime as base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for Cloud SQL socket
RUN mkdir -p /cloudsql

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CLOUD_RUN_ENV=true

# Expose port for webhook (if needed)
EXPOSE 8080

# Run the bot
CMD ["python", "run_production.py"]
