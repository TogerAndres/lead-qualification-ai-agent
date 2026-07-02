"""
app.py

Punto de entrada de la aplicación para Google Cloud Run.

Responsabilidades:
- Exponer endpoints de salud.
- Recibir Webhooks de Telegram.
- Procesar actualizaciones.
- Configurar automáticamente el webhook.
"""

import logging

from flask import Flask, jsonify, request
from telegram import Update

from bot import application
from config import (
    PORT,
    TELEGRAM_BOT_TOKEN,
    WEBHOOK_URL,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

_initialized = False


async def initialize_bot():
    """
    Inicializa python-telegram-bot una única vez.
    """

    global _initialized

    if not _initialized:
        await application.initialize()
        await application.start()
        _initialized = True
        logger.info("Telegram Application inicializada.")


@app.before_request
async def before_request():
    await initialize_bot()


# ==========================================================
# Health Checks
# ==========================================================

@app.get("/")
def index():
    return "Lead Qualification AI Agent running.", 200


@app.get("/health")
def health():
    return (
        jsonify(
            {
                "status": "ok",
                "service": "Lead Qualification AI Agent",
            }
        ),
        200,
    )


# ==========================================================
# Telegram Webhook
# ==========================================================

@app.post("/webhook")
async def webhook():

    try:

        secret = request.headers.get(
            "X-Telegram-Bot-Api-Secret-Token"
        )

        if secret != TELEGRAM_BOT_TOKEN[:20]:
            return (
                jsonify(
                    {
                        "error": "Unauthorized",
                    }
                ),
                401,
            )

        update = Update.de_json(
            request.get_json(force=True),
            application.bot,
        )

        await application.process_update(update)

        return "OK", 200

    except Exception:

        logger.exception("Error procesando webhook")

        return (
            jsonify(
                {
                    "status": "error",
                }
            ),
            500,
        )


# ==========================================================
# Configurar Webhook
# ==========================================================

@app.get("/set-webhook")
async def set_webhook():

    if not WEBHOOK_URL:

        return (
            jsonify(
                {
                    "error": "WEBHOOK_URL no configurada.",
                }
            ),
            500,
        )

    await initialize_bot()

    success = await application.bot.set_webhook(
        url=f"{WEBHOOK_URL}/webhook",
        secret_token=TELEGRAM_BOT_TOKEN[:20],
        drop_pending_updates=True,
    )

    return jsonify(
        {
            "success": success,
            "webhook": f"{WEBHOOK_URL}/webhook",
        }
    )


@app.get("/delete-webhook")
async def delete_webhook():

    await initialize_bot()

    success = await application.bot.delete_webhook()

    return jsonify(
        {
            "success": success,
        }
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT,
    )