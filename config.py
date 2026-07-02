"""
Configuración centralizada del servicio.

Todo se lee de variables de entorno. En Cloud Run, las credenciales de Google
(Sheets) NO se leen de un archivo: se usa la Service Account adjunta a la propia
revisión de Cloud Run vía Application Default Credentials (ADC). Ver sheets_logger.py.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# --- Telegram ---
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET: str | None = os.getenv("TELEGRAM_WEBHOOK_SECRET")

# --- Gemini ---
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_TIMEOUT_SECONDS: float = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "20"))
GEMINI_MAX_RETRIES: int = int(os.getenv("GEMINI_MAX_RETRIES", "2"))

# --- Google Sheets ---
GOOGLE_SHEET_ID: str | None = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_SHEET_NAME: str = os.getenv("GOOGLE_SHEET_NAME", "Leads")

# --- Servicio ---
PORT: int = int(os.getenv("PORT", "8080"))
MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "4000"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

REQUIRED_VARS = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "GOOGLE_SHEET_ID": GOOGLE_SHEET_ID,
}


def validate_config() -> None:
    """Falla rápido y con mensaje claro si falta alguna variable crítica."""
    missing = [name for name, value in REQUIRED_VARS.items() if not value]
    if missing:
        raise EnvironmentError(
            f"Faltan variables de entorno requeridas: {', '.join(missing)}. "
            f"Revisa tu .env (local) o la configuración de variables/secretos en "
            f"Cloud Run (producción)."
        )
