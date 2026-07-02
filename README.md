# Lead Qualification Agent 🤖

Microservicio que califica leads recibidos por Telegram contra un ICP (Ideal
Customer Profile) usando Gemini, con salida estructurada, logging a Google
Sheets, y observabilidad básica (health checks + métricas). Diseñado para
correr en Cloud Run, sin credenciales en disco.

## Arquitectura

```
                    Telegram
                        │
                        ▼
                HTTPS Webhook  (POST /webhook)
                        │
                        ▼
               Google Cloud Run  (Flask + Gunicorn)
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
  Gemini 2.5 Flash              Google Sheets
  (google-genai SDK,            (Application Default
   response_schema)              Credentials — sin JSON)
```

**Flujo de un mensaje:**

1. Telegram hace `POST /webhook` con el update en JSON.
2. `app.py` valida el `secret_token` y delega a `bot.process_update`.
3. `bot.py` (puente sync/async) entrega el update al `Application` de
   `python-telegram-bot`, que dispara `handlers.lead_message_handler`.
4. `llm_classifier.py` llama a Gemini con `response_schema=LeadDecision`
   (Pydantic) — la respuesta ya llega validada, sin parseo manual de JSON.
5. Se responde al usuario en Telegram y se registra el resultado en
   `sheets_logger.py` (Google Sheets vía ADC).
6. `metrics.py` acumula contadores en memoria, expuestos en `/metrics`.

## Estructura del proyecto

```
lead-qualification-agent/
│
├── app.py                  # Entrada Flask: webhook, health check, métricas
├── bot.py                  # Application de Telegram + puente sync/async
├── handlers.py              # Lógica de /start y mensajes de leads
├── llm_classifier.py        # Clasificación con Gemini (google-genai, response_schema)
├── sheets_logger.py         # Logging a Google Sheets vía ADC
├── metrics.py                # Contadores en memoria
├── config.py                 # Variables de entorno centralizadas
│
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .env.example
├── .gitignore
├── README.md
│
└── scripts/
    └── set_webhook.py       # Registra el webhook ante Telegram tras el deploy
```

## Tecnologías

- Python 3.12
- Flask 3.1 + Gunicorn
- python-telegram-bot 21.3
- google-genai 2.3 (SDK unificado, `response_schema`)
- Google Sheets API (gspread + Application Default Credentials)
- Docker (`python:3.12-slim`) + Cloud Run

## Setup local

### 1. Bot de Telegram

[@BotFather](https://t.me/BotFather) → `/newbot` → copia el token.

### 2. API key de Gemini

[Google AI Studio](https://aistudio.google.com/apikey) → crea una key.

### 3. Google Sheets (desarrollo local)

Para desarrollo local sin credenciales de Cloud Run, la forma más simple es:

```bash
gcloud auth application-default login
```

Esto resuelve `google.auth.default()` automáticamente con tu propia cuenta de
Google (debes tener acceso de Editor a la Sheet). Alternativa: generar un JSON
de cuenta de servicio y apuntar `GOOGLE_APPLICATION_CREDENTIALS` a él (nunca
se sube al repo — está en `.gitignore`).

Crea la Sheet, copia su ID de la URL, y compártela con Editor a la cuenta que
uses (tu propia cuenta o el email de la service account).

### 4. Ejecutar

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # rellena las variables
python app.py
```

En local, Telegram no puede alcanzar tu `localhost` por webhook — para probar
de extremo a extremo local necesitarías un túnel (ngrok, Cloudflare Tunnel).
El flujo pensado es probar los endpoints (`/`, `/health`, `/metrics`) en local
y el flujo completo ya desplegado en Cloud Run.

## Despliegue en Cloud Run

```bash
# 1. Build y push de la imagen
gcloud builds submit --tag gcr.io/TU_PROYECTO/lead-qualification-agent

# 2. Deploy — nota: SIN service_account.json, se asigna una Service Account
#    con permisos de Editor sobre la Sheet directamente al servicio
gcloud run deploy lead-qualification-agent \
  --image gcr.io/TU_PROYECTO/lead-qualification-agent \
  --service-account TU_SERVICE_ACCOUNT@TU_PROYECTO.iam.gserviceaccount.com \
  --set-env-vars TELEGRAM_BOT_TOKEN=...,GEMINI_API_KEY=...,GOOGLE_SHEET_ID=...,TELEGRAM_WEBHOOK_SECRET=... \
  --allow-unauthenticated \
  --region us-central1

# 3. Registrar el webhook ante Telegram (una sola vez, con la URL que te dio Cloud Run)
python scripts/set_webhook.py https://tu-servicio-xxxxx.run.app
```

Para variables sensibles (`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`), en
producción real se recomienda usar **Secret Manager** en vez de
`--set-env-vars` en texto plano — ver "Qué cambiaría para producción real"
más abajo.

La Service Account de Cloud Run necesita permisos de **Editor** sobre la
Google Sheet (compártela con su email `...@TU_PROYECTO.iam.gserviceaccount.com`).
No necesita ningún rol de IAM adicional a nivel de proyecto para Sheets —
el acceso se controla compartiendo el documento, como con cualquier cuenta.

## Endpoints

| Método | Ruta        | Propósito                                          |
|--------|-------------|-----------------------------------------------------|
| GET    | `/`         | Health check raíz (Cloud Run) → `OK`                |
| GET    | `/health`   | Health check explícito → `{"status": "ok"}`         |
| GET    | `/version`  | Versión y stack del servicio (texto plano)          |
| GET    | `/metrics`  | Leads procesados/cualificados/rechazados, score promedio, tiempo promedio |
| POST   | `/webhook`  | Recibe updates de Telegram                          |

## Comandos de Telegram

| Comando   | Qué hace                                             |
|-----------|-------------------------------------------------------|
| `/start`  | Bienvenida y ejemplo de uso                            |
| `/help`   | Lista de comandos disponibles                          |
| `/about`  | Info técnica del proyecto (versión, modelo, stack)      |

Estos tres comandos, además de la descripción del bot, se registran
**automáticamente vía Bot API** (`set_my_commands`, `set_my_description`,
`set_my_short_description`) al arrancar el servicio — no hace falta
configurarlos a mano en BotFather. Lo único que la Bot API no permite
gestionar por código es la **foto de perfil del bot**: para eso sí necesitas
hablar con [@BotFather](https://t.me/BotFather) → `/setuserpic`.

## Ejemplo de uso

**Usuario envía a través de Telegram:**
> Empresa de consultoría, 15 empleados, Madrid, quieren automatizar su proceso de ventas.

**Bot responde (edita el mensaje "Analizando..." con el resultado final):**
```
━━━━━━━━━━━━━━━━━━━━━━
🤖 Lead Qualification AI
━━━━━━━━━━━━━━━━━━━━━━

🟢 LEAD CALIFICADO

📈 Score: 96/100
🟩🟩🟩🟩🟩  (confianza: alta)

🏢 Empresa: Consultoría
👥 Empleados: 15
📍 Ubicación: Madrid
💡 Interés: Automatización de ventas

📋 Criterios ICP
🏢 Empresa       ✅
👥 Empleados     ✅
📍 Ubicación     ✅
💡 Interés       ✅

🧠 Análisis
Es una empresa de consultoría (encaja con el tipo de negocio), tiene 15
empleados (supera el mínimo de 5), está en Madrid, España (región válida), y
busca automatización de ventas (interés alineado con el ICP).

━━━━━━━━━━━━━━━━━━━━━━
⚡ Gemini 2.5 Flash
```

Y en la Google Sheet queda registrada una fila con: fecha, empresa, empleados,
ubicación, interés, score, decisión, confianza, motivo, texto original del
lead y `chat_id`. La primera vez que se usa la Sheet, el servicio crea
automáticamente el encabezado con fondo verde, fila congelada y filtro básico.

**Ejemplo de `/metrics`:**
```json
{
  "leads_procesados": 12,
  "leads_cualificados": 7,
  "leads_rechazados": 5,
  "errores_clasificacion": 0,
  "leads_hoy": 4,
  "score_promedio": 61.3,
  "tiempo_promedio_respuesta_segundos": 1.842,
  "uptime_segundos": 3421.6
}
```

## Decisiones de diseño relevantes

- **Salida estructurada real** (`response_schema=LeadDecision` con Pydantic,
  no `json.loads` sobre texto libre): el SDK valida el schema del lado del
  cliente y expone `response.parsed` ya tipado, eliminando una clase entera de
  errores de parseo.
- **Prompt injection**: el texto del lead siempre va delimitado
  (`<lead_data>...</lead_data>`) y el `system_instruction` indica
  explícitamente que todo lo que esté ahí dentro es dato, nunca instrucción.
  Combinado con `response_schema`, el modelo no tiene forma de "responder
  libremente": solo puede rellenar los campos del schema.
- **Fail-safe, no fail-open**: cualquier fallo (red, cuota, parseo) hace que el
  lead se marque como NO cualificado con confianza baja, nunca al revés.
- **Sin credenciales en disco**: Google Sheets usa Application Default
  Credentials — en Cloud Run resuelve automáticamente contra la Service
  Account adjunta al servicio; en local, contra `gcloud auth application-default
  login` o una variable de entorno que apunta a un archivo fuera del repo.
- **Puente sync/async documentado**: Flask/Gunicorn son síncronos y
  python-telegram-bot es async-first. En vez de reescribir todo el servicio en
  asyncio, se corre un único event loop persistente en un hilo de fondo, y se
  programan corrutinas desde el handler síncrono con
  `asyncio.run_coroutine_threadsafe`.
- **Un fallo en Sheets nunca tumba el bot**: el usuario recibe su respuesta
  aunque el logging falle; el error queda en logs para revisión.
- **Métricas en memoria con limitación conocida**: al vivir en el proceso, si
  Cloud Run escala a más de una instancia cada una lleva su propio contador.
  Documentado explícitamente — no se presenta como más de lo que es.

## Qué cambiaría para producción real

1. **Secretos y colas reales**: movería `TELEGRAM_BOT_TOKEN` y `GEMINI_API_KEY`
   a Secret Manager (no como env vars en texto plano), y añadiría una cola
   (Cloud Tasks/Pub-Sub) entre el webhook y el procesamiento para no perder
   updates si Gemini tarda o el servicio se reinicia a mitad de proceso.
2. **Rate limiting y control de costes**: limitaría mensajes por
   usuario/minuto y pondría un tope diario de llamadas a Gemini con alertas de
   presupuesto (Cloud Monitoring), para que nadie pueda saturar el bot con
   mensajes repetidos y disparar la factura.
3. **Prompt injection y auditoría reforzada**: además del delimitado actual,
   añadiría un paso de moderación previo (o un modelo más barato) que detecte
   intentos de manipulación explícitos antes de pasar el texto al clasificador
   principal, registrando esos intentos por separado para revisión del equipo.