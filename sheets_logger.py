"""
Logging de cada lead a Google Sheets.

En producción (Cloud Run), las credenciales NO vienen de un archivo JSON: se
resuelven automáticamente vía Application Default Credentials (ADC) a partir de
la Service Account adjunta a la revisión de Cloud Run (google.auth.default()).

En desarrollo local, ADC se puede resolver de dos formas sin subir ningún
secreto al repo:
  1. `gcloud auth application-default login` (recomendado), o
  2. Variable de entorno GOOGLE_APPLICATION_CREDENTIALS apuntando a un JSON
     local que tú mismo generes y que está en .gitignore.

En ambos casos el código es exactamente el mismo — es la gracia de ADC.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

import google.auth
import gspread

from config import GOOGLE_SHEET_ID, GOOGLE_SHEET_NAME
from llm_classifier import LeadDecision

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADER = ["fecha", "datos_recibidos", "decision", "motivo", "confianza", "chat_id"]

_worksheet = None
_lock = threading.Lock()


def _get_worksheet():
    """Conecta (una sola vez, cacheado) con la worksheet destino usando ADC."""
    global _worksheet
    if _worksheet is not None:
        return _worksheet

    with _lock:
        if _worksheet is not None:  # doble check tras adquirir el lock
            return _worksheet

        credentials, _project = google.auth.default(scopes=SCOPES)
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(GOOGLE_SHEET_ID)

        try:
            worksheet = sheet.worksheet(GOOGLE_SHEET_NAME)
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=GOOGLE_SHEET_NAME, rows=1000, cols=len(HEADER))
            worksheet.append_row(HEADER)

        if not worksheet.get_all_values():
            worksheet.append_row(HEADER)

        _worksheet = worksheet
        return _worksheet


def log_lead(raw_text: str, decision: LeadDecision, chat_id: int) -> bool:
    """
    Registra el lead en la Google Sheet. Devuelve True/False según éxito.
    Un fallo aquí nunca debe tumbar el flujo principal: se loguea y se sigue.
    """
    try:
        worksheet = _get_worksheet()
        row = [
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            raw_text.strip()[:1000],
            "CUALIFICADO" if decision.qualified else "NO CUALIFICADO",
            decision.reasoning,
            decision.confidence,
            str(chat_id),
        ]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("Error al loguear en Google Sheets: %s", e)
        return False
