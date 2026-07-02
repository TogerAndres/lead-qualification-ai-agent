"""
Configuración centralizada del proyecto.

Todas las credenciales se leen desde variables de entorno (.env).
Nunca deben almacenarse credenciales directamente en el código.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ==========================================================
# Telegram
# ==========================================================

TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

# URL pública de Cloud Run
# Ejemplo:
# https://lead-agent-xxxxx-uc.a.run.app
WEBHOOK_URL: str | None = os.getenv("WEBHOOK_URL")


# ==========================================================
# Gemini
# ==========================================================

GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL: str = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


# ==========================================================
# Google Sheets
# ==========================================================

GOOGLE_SERVICE_ACCOUNT_FILE: str = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    "service_account.json",
)

GOOGLE_SHEET_ID: str | None = os.getenv("GOOGLE_SHEET_ID")

GOOGLE_SHEET_NAME: str = os.getenv(
    "GOOGLE_SHEET_NAME",
    "Leads",
)


# ==========================================================
# Flask / Cloud Run
# ==========================================================

PORT: int = int(os.getenv("PORT", "8080"))

DEBUG: bool = os.getenv(
    "DEBUG",
    "False",
).lower() == "true"


# ==========================================================
# Validaciones
# ==========================================================

REQUIRED_VARS = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "GOOGLE_SHEET_ID": GOOGLE_SHEET_ID,
}


def validate_config() -> None:
    """
    Verifica que existan todas las variables críticas antes
    de iniciar la aplicación.
    """

    missing = [
        key
        for key, value in REQUIRED_VARS.items()
        if not value
    ]

    if missing:
        raise EnvironmentError(
            "Faltan las siguientes variables de entorno:\n\n"
            + "\n".join(f"- {item}" for item in missing)
            + "\n\nRevisa tu archivo .env."
        )