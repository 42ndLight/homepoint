# Django Backend Dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

# 1. Create user AND directories BEFORE switching user (still root here)
RUN groupadd -g 1001 appuser && \
    useradd -m -u 1001 -g appuser appuser && \
    mkdir -p /app/staticfiles_collected && \
    chown -R appuser:appuser /app

# 2. NOW switch to appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=5)" || exit 1

CMD ["sh", "-c", "python manage.py wait_for_db && python manage.py collectstatic --noinput && python manage.py migrate && gunicorn homepointBackend.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120"]