"""
Handlers de Telegram. Separados de bot.py para mantener la inicialización del
Application aislada de la lógica de negocio (más testeable).
"""
from __future__ import annotations

import logging
import time

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

import metrics
from config import MAX_MESSAGE_LENGTH
from llm_classifier import classify_lead
from sheets_logger import log_lead

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde al comando /start con instrucciones de uso."""
    await update.message.reply_text(
        "👋 Hola, soy el agente de calificación de leads.\n\n"
        "Envíame los datos de un lead en texto libre, por ejemplo:\n"
        '"Empresa de consultoría, 15 empleados, Madrid, quieren automatizar '
        'su proceso de ventas."\n\n'
        "Te diré si el lead está cualificado según nuestro ICP y por qué."
    )


async def lead_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Recibe texto libre con datos de un lead, lo clasifica y responde."""
    message = update.message
    if not message or not message.text:
        return

    raw_text = message.text.strip()
    chat_id = message.chat_id

    if len(raw_text) < 5:
        await message.reply_text(
            "Necesito un poco más de contexto sobre el lead (empresa, tamaño, "
            "ubicación, interés) para poder evaluarlo."
        )
        return

    if len(raw_text) > MAX_MESSAGE_LENGTH:
        await message.reply_text(
            f"El mensaje es demasiado largo ({len(raw_text)} caracteres). "
            f"Resume los datos del lead en menos de {MAX_MESSAGE_LENGTH} caracteres."
        )
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    start_time = time.monotonic()
    try:
        decision = classify_lead(raw_text)
        errored = decision.reasoning.startswith("No se pudo completar el análisis")
    except Exception as e:  # noqa: BLE001 — red de seguridad final
        logger.exception("Error inesperado clasificando el lead: %s", e)
        elapsed = time.monotonic() - start_time
        metrics.record_lead(qualified=False, elapsed_seconds=elapsed, errored=True)
        await message.reply_text(
            "⚠️ Tuve un problema analizando este lead. El error quedó registrado. "
            "Inténtalo de nuevo en unos minutos."
        )
        return

    elapsed = time.monotonic() - start_time
    metrics.record_lead(qualified=decision.qualified, elapsed_seconds=elapsed, errored=errored)

    icon = "✅" if decision.qualified else "❌"
    label = "CUALIFICADO" if decision.qualified else "NO CUALIFICADO"
    reply = f"{icon} *{label}* (confianza: {decision.confidence})\n\n{decision.reasoning}"
    await message.reply_text(reply, parse_mode="Markdown")

    logged_ok = log_lead(raw_text, decision, chat_id)
    if not logged_ok:
        logger.warning(
            "El lead se clasificó pero NO se pudo loguear en Google Sheets (chat_id=%s)", chat_id
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler global de errores no capturados por python-telegram-bot."""
    logger.error("Excepción no capturada: %s", context.error, exc_info=context.error)
