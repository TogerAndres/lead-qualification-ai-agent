FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Dependencias del sistema mínimas (certificados TLS para llamadas HTTPS salientes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

# workers=1 es intencional: mantiene un único proceso para que el event loop
# de python-telegram-bot y las métricas en memoria vivan en un solo lugar.
# La concurrencia se maneja con threads (Cloud Run además puede escalar
# horizontalmente añadiendo más instancias/contenedores si hace falta).
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "60", "app:app"]
