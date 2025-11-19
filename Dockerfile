# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY alembic.ini .
COPY migrations ./migrations

WORKDIR /app
ENV PYTHONPATH=/app

# Faster installs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY .env ./.env

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

