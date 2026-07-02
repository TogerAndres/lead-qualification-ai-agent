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


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 Lead Qualification AI\n\n"
        "Tu asistente inteligente para evaluar prospectos mediante IA.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📌 ¿Qué puedo hacer?\n\n"
        "• Analizar un lead.\n"
        "• Evaluar si encaja con el ICP.\n"
        "• Explicar la decisión.\n"
        "• Registrar el resultado automáticamente en Google Sheets.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✍️ Solo envíame una descripción del prospecto.\n\n"
        "Ejemplo:\n\n"
        "Empresa de software con 18 empleados en Colombia interesada en automatizar su atención al cliente mediante IA.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚡ Responderé en pocos segundos.",
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

    # Enviar mensaje de análisis en progreso
    msg = await message.reply_text(
        "🤖 Analizando el lead...\n\n⏳ Esto tardará unos segundos."
    )

    start_time = time.monotonic()
    try:
        decision = classify_lead(raw_text)
        errored = decision.reasoning.startswith("No fue posible analizar")
    except Exception as e:  # noqa: BLE001 — red de seguridad final
        logger.exception("Error inesperado clasificando el lead: %s", e)
        elapsed = time.monotonic() - start_time
        metrics.record_lead(qualified=False, elapsed_seconds=elapsed, errored=True)
        await msg.delete()
        await message.reply_text(
            "⚠️ Tuve un problema analizando este lead. El error quedó registrado. "
            "Inténtalo de nuevo en unos minutos."
        )
        return

    elapsed = time.monotonic() - start_time
    metrics.record_lead(qualified=decision.qualified, elapsed_seconds=elapsed, errored=errored)

    # Construcción del mensaje de respuesta con nuevo formato
    if decision.qualified:
        result_icon = "🟢"
        result_label = "✅ Lead Cualificado"
    else:
        result_icon = "🔴"
        result_label = "❌ Lead No Cualificado"

    reply = (
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 Lead Qualification AI\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{result_icon} RESULTADO\n\n"
        f"{result_label}\n\n"
        "📈 Confianza\n\n"
        f"{decision.confidence.capitalize()}\n\n"
        "🧠 Análisis\n\n"
        f"{decision.reasoning}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📄 Lead registrado correctamente."
    )
    await msg.delete()
    await message.reply_text(reply)

    logged_ok = log_lead(raw_text, decision, chat_id)
    if not logged_ok:
        logger.warning(
            "El lead se clasificó pero NO se pudo loguear en Google Sheets (chat_id=%s)", chat_id
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler global de errores no capturados por python-telegram-bot."""
    logger.error("Excepción no capturada: %s", context.error, exc_info=context.error)