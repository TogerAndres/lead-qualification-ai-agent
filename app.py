"""
Entrada Flask del microservicio. Expone:

  GET  /            -> health check simple para Cloud Run ("OK")
  GET  /health       -> health check explícito (JSON)
  GET  /version      -> versión y stack del servicio (texto plano)
  GET  /metrics      -> métricas en memoria del servicio
  POST /webhook      -> recibe updates de Telegram

El webhook valida el header `X-Telegram-Bot-Api-Secret-Token` (si se configuró
TELEGRAM_WEBHOOK_SECRET) para asegurarse de que la petición viene realmente de
Telegram y no de un tercero que adivinó la URL.
"""
from __future__ import annotations

import logging

from flask import Flask, jsonify, request

import metrics
from bot import process_update
from config import LOG_LEVEL, TELEGRAM_WEBHOOK_SECRET, validate_config

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger(__name__)

validate_config()

app = Flask(__name__)


@app.get("/")
def index():
    """Health check raíz — Cloud Run lo usa para saber que el contenedor arrancó."""
    return "OK", 200


@app.get("/health")
def health():
    """Health check explícito en JSON, útil para monitoreo externo."""
    return jsonify({"status": "ok"}), 200


@app.get("/version")
def version():
    """Info de versión y stack — útil para verificar qué revisión está corriendo en Cloud Run."""
    return (
        "Lead Qualification AI\n"
        "Version 1.0.0\n"
        "Gemini 2.5 Flash\n"
        "Cloud Run\n"
        "Google Sheets\n"
        "Telegram Bot\n"
    ), 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/metrics")
def get_metrics():
    """Métricas en memoria: leads procesados, cualificados, rechazados, tiempo promedio."""
    return jsonify(metrics.snapshot()), 200


@app.post("/webhook")
def webhook():
    """Recibe un update de Telegram y lo procesa de forma síncrona (vía bot.process_update)."""
    if TELEGRAM_WEBHOOK_SECRET:
        received_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if received_secret != TELEGRAM_WEBHOOK_SECRET:
            logger.warning("Webhook rechazado: secret_token inválido o ausente.")
            return jsonify({"error": "unauthorized"}), 401

    update_data = request.get_json(silent=True)
    if update_data is None:
        logger.warning("Webhook recibió un body que no es JSON válido.")
        return jsonify({"error": "invalid payload"}), 400

    try:
        process_update(update_data)
    except Exception as e:  # noqa: BLE001 — nunca dejar caer el proceso por un update
        logger.exception("Error procesando update de Telegram: %s", e)
        # Igual respondemos 200: Telegram reintentará si devolvemos error, y no
        # queremos reintentos infinitos de un update que ya falló de forma no transitoria.
        return jsonify({"status": "error logged"}), 200

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Solo para desarrollo local (python app.py). En producción corre gunicorn (ver Dockerfile).
    from config import PORT

    app.run(host="0.0.0.0", port=PORT, debug=False)