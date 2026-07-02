"""
Logging de cada lead procesado a una Google Sheet.
Columnas: fecha | datos_recibidos | decision | motivo | chat_id | confianza
"""
import logging
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_SERVICE_ACCOUNT_FILE, GOOGLE_SHEET_ID, GOOGLE_SHEET_NAME

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

HEADER = ["fecha", "datos_recibidos", "decision", "motivo", "confianza", "chat_id"]

_worksheet = None  # cache simple para no reconectar en cada mensaje


def _get_worksheet():
    global _worksheet
    if _worksheet is not None:
        return _worksheet

    creds = Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID)

    try:
        worksheet = sheet.worksheet(GOOGLE_SHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=GOOGLE_SHEET_NAME, rows=1000, cols=len(HEADER))
        worksheet.append_row(HEADER)

    # Si la hoja está vacía, aseguramos el encabezado
    if worksheet.row_count == 0 or not worksheet.get_all_values():
        worksheet.append_row(HEADER)

    _worksheet = worksheet
    return _worksheet


def log_lead(raw_text: str, decision: dict, chat_id: int) -> bool:
    """
    Registra el lead en la Google Sheet. Devuelve True/False según éxito.
    Un fallo aquí NUNCA debe tumbar el bot: se loguea el error y se sigue.
    """
    try:
        worksheet = _get_worksheet()
        row = [
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            raw_text.strip()[:1000],
            "CUALIFICADO" if decision["qualified"] else "NO CUALIFICADO",
            decision["reasoning"],
            decision.get("confidence", ""),
            str(chat_id),
        ]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("Error al loguear en Google Sheets: %s", e)
        return False
