"""
Script de un solo uso: registra la URL de webhook ante Telegram después de
desplegar el servicio (por ejemplo, tras el primer deploy a Cloud Run, cuando
ya conoces la URL pública asignada).

Uso:
    python scripts/set_webhook.py https://tu-servicio-xxxxx.run.app

Requiere las mismas variables de entorno que el servicio (TELEGRAM_BOT_TOKEN,
y opcionalmente TELEGRAM_WEBHOOK_SECRET si quieres validar el header secreto).
"""
from __future__ import annotations

import sys

sys.path.insert(0, ".")  # permite ejecutar el script desde la raíz del repo

from bot import set_webhook_sync  # noqa: E402
from config import TELEGRAM_WEBHOOK_SECRET  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python scripts/set_webhook.py <URL_PUBLICA_DEL_SERVICIO>")
        sys.exit(1)

    base_url = sys.argv[1].rstrip("/")
    webhook_url = f"{base_url}/webhook"

    set_webhook_sync(webhook_url, secret_token=TELEGRAM_WEBHOOK_SECRET)
    print(f"✅ Webhook registrado correctamente: {webhook_url}")
    if TELEGRAM_WEBHOOK_SECRET:
        print("   (con validación de secret_token habilitada)")
    else:
        print("   ⚠️ TELEGRAM_WEBHOOK_SECRET no está configurado — se recomienda definirlo.")


if __name__ == "__main__":
    main()
