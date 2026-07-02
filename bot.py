"""
Bot de Telegram para calificación de leads.

Flujo:
1. Usuario envía texto libre con datos de un lead.
2. Se clasifica contra el ICP usando Gemini (llm_classifier.py).
3. Se responde en el mismo chat con la decisión y el razonamiento.
4. Se loguea el resultado en Google Sheets (sheets_logger.py).

Manejo de errores: cualquier fallo en clasificación o logging se captura,
se informa al usuario de forma clara, y queda registrado en logs — el bot
nunca se cae por un error de una sola solicitud.
"""
import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

from config import TELEGRAM_BOT_TOKEN, validate_config
from llm_classifier import classify_lead
from sheets_logger import log_lead

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000  # límite defensivo para evitar abuso / costes de API descontrolados


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola, soy el bot de calificación de leads.\n\n"
        "Envíame los datos de un lead en texto libre, por ejemplo:\n"
        '"Empresa de consultoría, 15 empleados, Madrid, quieren automatizar '
        'su proceso de ventas."\n\n'
        "Te diré si el lead está cualificado según nuestro ICP y por qué."
    )


async def handle_lead_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    raw_text = message.text.strip()
    chat_id = message.chat_id

    # Validación defensiva de entrada — evita gastar tokens en mensajes vacíos/absurdos
    if len(raw_text) < 5:
        await message.reply_text(
            "Necesito un poco más de contexto sobre el lead (empresa, tamaño, "
            "ubicación, interés) para poder evaluarlo."
        )
        return

    if len(raw_text) > MAX_MESSAGE_LENGTH:
        await message.reply_text(
            f"El mensaje es demasiado largo ({len(raw_text)} caracteres). "
            f"Por favor resume los datos del lead en menos de {MAX_MESSAGE_LENGTH} caracteres."
        )
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        decision = classify_lead(raw_text)
    except Exception as e:  # noqa: BLE001 — red de seguridad final, classify_lead ya maneja sus propios errores
        logger.exception("Error inesperado clasificando el lead: %s", e)
        await message.reply_text(
            "⚠️ Tuve un problema analizando este lead. Ya quedó registrado el error "
            "y no se pudo completar la evaluación automática. Inténtalo de nuevo en unos minutos."
        )
        return

    icon = "✅" if decision["qualified"] else "❌"
    label = "CUALIFICADO" if decision["qualified"] else "NO CUALIFICADO"
    reply = (
        f"{icon} *{label}* (confianza: {decision['confidence']})\n\n"
        f"{decision['reasoning']}"
    )
    await message.reply_text(reply, parse_mode="Markdown")

    logged_ok = log_lead(raw_text, decision, chat_id)
    if not logged_ok:
        logger.warning("El lead se clasificó pero NO se pudo loguear en Google Sheets (chat_id=%s)", chat_id)
        # No se lo mostramos al usuario final: es un problema interno, no suyo.
        # Pero queda en logs para que el equipo lo detecte.


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Excepción no capturada: %s", context.error, exc_info=context.error)


def main():
    validate_config()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_lead_message))
    app.add_error_handler(error_handler)

    logger.info("Bot iniciado. Escuchando mensajes...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
