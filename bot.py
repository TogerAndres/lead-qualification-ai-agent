"""
Inicializa el Application de python-telegram-bot (v21, async) y expone un
puente síncrono para que app.py (Flask, síncrono) pueda alimentarle updates
recibidos por webhook.

python-telegram-bot es async-first; Flask + gunicorn son síncronos. La forma
limpia de conectarlos sin reescribir todo en asyncio es: correr un único event
loop persistente en un hilo de fondo, y usar
`asyncio.run_coroutine_threadsafe` para programar corrutinas desde el handler
síncrono de Flask, esperando el resultado con `.result(timeout=...)`.
"""
from __future__ import annotations

import asyncio
import logging
import threading

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN
from handlers import error_handler, lead_message_handler, start_handler

logger = logging.getLogger(__name__)

application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lead_message_handler))
application.add_error_handler(error_handler)

_loop = asyncio.new_event_loop()
_loop_thread = threading.Thread(target=_loop.run_forever, daemon=True, name="ptb-event-loop")
_loop_thread.start()

_initialized = False
_init_lock = threading.Lock()


def _ensure_initialized() -> None:
    """Inicializa el Application (una sola vez) en el event loop de fondo."""
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        future = asyncio.run_coroutine_threadsafe(application.initialize(), _loop)
        future.result(timeout=30)
        _initialized = True
        logger.info("Telegram Application inicializado correctamente.")


def process_update(update_data: dict, timeout: float = 25.0) -> None:
    """
    Punto de entrada síncrono llamado desde el endpoint /webhook de Flask.
    Convierte el JSON crudo de Telegram en un Update y lo procesa.
    """
    _ensure_initialized()
    update = Update.de_json(update_data, application.bot)
    future = asyncio.run_coroutine_threadsafe(application.process_update(update), _loop)
    future.result(timeout=timeout)


def set_webhook_sync(webhook_url: str, secret_token: str | None = None, timeout: float = 30.0) -> None:
    """Registra la URL de webhook ante Telegram. Pensado para usarse una vez tras el deploy."""
    _ensure_initialized()

    async def _set():
        await application.bot.set_webhook(url=webhook_url, secret_token=secret_token)

    future = asyncio.run_coroutine_threadsafe(_set(), _loop)
    future.result(timeout=timeout)
