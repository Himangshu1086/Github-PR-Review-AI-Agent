# Use an official Python base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Set environment for production (optional)
ENV ENV=production

# Start FastAPI and Celery worker using a shell script
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & celery -A app.worker.celery_app worker --loglevel=info"]