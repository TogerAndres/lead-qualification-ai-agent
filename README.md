<div align="center">

<img src="capturas/LogoChatBot.png" alt="Lead Qualification Agent Logo" width="160">

# 🤖 Lead Qualification Agent

### Un bot de Telegram que califica leads por ti, en segundos y sin criterio humano de por medio.

Microservicio que recibe mensajes de leads por Telegram, los evalúa contra un **ICP (Ideal
Customer Profile)** usando Gemini con salida estructurada, registra cada resultado en
Google Sheets y expone métricas básicas — todo pensado para correr en Cloud Run sin
credenciales en disco.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Telegram Bot](https://img.shields.io/badge/python--telegram--bot-21.3-26A5E4?logo=telegram&logoColor=white)](https://python-telegram-bot.org/)
[![Gemini](https://img.shields.io/badge/Gemini%202.5%20Flash-LLM-4285F4?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#-licencia)

</div>

<br>

<p align="center">
  <img src="capturas/Lead-Cualificado.png" alt="Ejemplo de lead calificado por el bot" width="420">
</p>

---

## 📌 ¿Qué problema resuelve?

Cuando entran leads por chat (web, campañas, formularios conectados a Telegram), alguien del
equipo tiene que leerlos uno por uno y decidir si valen la pena antes de pasarlos a ventas.
Eso no escala, es lento y depende del criterio de quien esté de turno ese día.

**Lead Qualification Agent** automatiza ese primer filtro: recibe el mensaje del lead,
lo evalúa contra un perfil de cliente ideal usando un LLM con **salida estructurada
(no texto libre)**, responde al instante con un score y un análisis, y deja todo
registrado en una Google Sheet lista para que ventas la revise.

## ✨ Features

- 🤖 **Bot de Telegram listo para producción**, con comandos `/start`, `/help` y `/about`
  autoregistrados vía Bot API al arrancar (nada que configurar a mano en BotFather).
- 🧠 **Clasificación con salida estructurada real**: Gemini responde con un schema de
  Pydantic (`response_schema`), no con JSON parseado a mano — se elimina toda una clase
  de errores de parseo.
- 🛡️ **Resistente a prompt injection**: el texto del lead siempre viaja delimitado
  (`<lead_data>...</lead_data>`) y el modelo solo puede rellenar los campos del schema,
  nunca "responder libremente".
- 🧯 **Fail-safe, no fail-open**: si algo falla (red, cuota, parseo), el lead se marca
  como NO calificado con confianza baja — nunca al revés.
- 📊 **Logging automático a Google Sheets** vía Application Default Credentials, sin
  ningún JSON de credenciales en el repo ni en el contenedor.
- 📈 **Métricas en memoria** expuestas en `/metrics`: leads procesados, calificados,
  rechazados, score promedio y tiempo de respuesta.
- ☁️ **Cloud Run first**: health checks, arranque rápido, sin estado en disco y Service
  Account con permisos mínimos (solo Editor sobre la Sheet).

## ⚙️ Cómo funciona

```
Telegram
   │  Usuario envía un mensaje describiendo su empresa / necesidad
   ▼
HTTPS Webhook  (POST /webhook)
   │  app.py valida el secret_token y delega a bot.process_update
   ▼
python-telegram-bot (bot.py)
   │  Puente sync/async: entrega el update al Application,
   │  dispara handlers.lead_message_handler
   ▼
llm_classifier.py
   │  Llama a Gemini 2.5 Flash con response_schema=LeadDecision (Pydantic)
   │  El texto del lead va delimitado como dato, nunca como instrucción
   ▼
Gemini 2.5 Flash
   │  Devuelve un LeadDecision ya validado y tipado (score, criterios ICP,
   │  decisión, confianza, análisis) — sin parseo manual de JSON
   ▼
Telegram + Google Sheets
   Responde al usuario con el resultado y registra la fila
   (fecha, empresa, empleados, ubicación, interés, score, decisión...)
   vía sheets_logger.py (Google Sheets API + ADC, sin credenciales en disco)
```

## 🖼️ Capturas

<table>
<tr>
<td width="50%">

**Lead calificado**

El bot responde en Telegram con el score contra el ICP, el desglose por criterio
y un análisis en lenguaje natural generado por el modelo.

<img src="capturas/Lead-Cualificado.png" alt="Lead calificado por el bot">

</td>
<td width="50%">

**Resistencia a prompt injection**

Un intento de manipular al modelo a través del texto del lead es ignorado: el
`system_instruction` y el `response_schema` fuerzan al modelo a solo rellenar
el schema, nunca a seguir instrucciones inyectadas en el mensaje.

<img src="capturas/Prompt-Injection-Malo.png" alt="Ejemplo de intento de prompt injection bloqueado">

</td>
</tr>
</table>

## 🧰 Tech stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, Flask 3.1 + Gunicorn |
| Bot | python-telegram-bot 21.3 |
| LLM | Gemini 2.5 Flash (`google-genai`, `response_schema`) |
| Validación | Pydantic |
| Logging de datos | Google Sheets API (gspread + Application Default Credentials) |
| Infraestructura | Docker (`python:3.12-slim`) + Google Cloud Run |

## 📁 Estructura del proyecto

```
lead-qualification-agent/
│
├── app.py                  # Entrada Flask: webhook, health check, métricas
├── bot.py                  # Application de Telegram + puente sync/async
├── handlers.py             # Lógica de /start y mensajes de leads
├── llm_classifier.py       # Clasificación con Gemini (google-genai, response_schema)
├── sheets_logger.py        # Logging a Google Sheets vía ADC
├── metrics.py               # Contadores en memoria
├── config.py                # Variables de entorno centralizadas
│
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .env.example
├── .gitignore
│
├── capturas/                # Capturas usadas en este README
│
└── scripts/
    └── set_webhook.py       # Registra el webhook ante Telegram tras el deploy
```

## 🚀 Setup local

### 1. Bot de Telegram

Habla con [@BotFather](https://t.me/BotFather) → `/newbot` → copia el token.

### 2. API key de Gemini

Créala en [Google AI Studio](https://aistudio.google.com/apikey).

### 3. Google Sheets

Para desarrollo local, la forma más simple es autenticarte con tu propia cuenta:

```bash
gcloud auth application-default login
```

Crea la Sheet, copia su ID de la URL y compártela con Editor a la cuenta que uses.
No se necesita ningún JSON de credenciales en el repo.

### 4. Ejecutar

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # rellena las variables
python app.py
```

> Telegram no puede alcanzar tu `localhost` por webhook. Para un flujo end-to-end en local
> necesitarías un túnel (ngrok, Cloudflare Tunnel); el enfoque recomendado es probar los
> endpoints (`/`, `/health`, `/metrics`) en local y el flujo completo ya desplegado.

## 🔐 Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Sí | Token del bot, obtenido en BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | No | Secreto validado en cada request al webhook (muy recomendado en producción) |
| `GEMINI_API_KEY` | Sí | Key de Gemini, desde [aistudio.google.com](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | No | Modelo a usar (default `gemini-2.5-flash`) |
| `GOOGLE_SHEET_ID` | Sí | ID de la Sheet donde se registran los leads |
| `GOOGLE_SHEET_NAME` | No | Nombre de la hoja (default `Leads`) |
| `PORT` | No | Puerto del servicio (default `8080`) |

## ☁️ Despliegue en Cloud Run

```bash
# 1. Build y push de la imagen
gcloud builds submit --tag gcr.io/TU_PROYECTO/lead-qualification-agent

# 2. Deploy — sin service_account.json: la Service Account con permisos
#    de Editor sobre la Sheet se asigna directamente al servicio
gcloud run deploy lead-qualification-agent \
  --image gcr.io/TU_PROYECTO/lead-qualification-agent \
  --service-account TU_SERVICE_ACCOUNT@TU_PROYECTO.iam.gserviceaccount.com \
  --set-env-vars TELEGRAM_BOT_TOKEN=...,GEMINI_API_KEY=...,GOOGLE_SHEET_ID=...,TELEGRAM_WEBHOOK_SECRET=... \
  --allow-unauthenticated \
  --region us-central1

# 3. Registrar el webhook ante Telegram (una sola vez)
python scripts/set_webhook.py https://tu-servicio-xxxxx.run.app
```

La Service Account de Cloud Run solo necesita permisos de **Editor** sobre la Google Sheet
(compartida con su email `...@TU_PROYECTO.iam.gserviceaccount.com`) — no requiere roles de
IAM adicionales a nivel de proyecto.

## 🔌 Endpoints

| Método | Ruta | Propósito |
|---|---|---|
| GET | `/` | Health check raíz (Cloud Run) → `OK` |
| GET | `/health` | Health check explícito → `{"status": "ok"}` |
| GET | `/version` | Versión y stack del servicio |
| GET | `/metrics` | Leads procesados / calificados / rechazados, score y tiempo promedio |
| POST | `/webhook` | Recibe updates de Telegram |

## 💬 Comandos de Telegram

| Comando | Qué hace |
|---|---|
| `/start` | Bienvenida y ejemplo de uso |
| `/help` | Lista de comandos disponibles |
| `/about` | Info técnica del proyecto (versión, modelo, stack) |

Estos comandos se registran automáticamente vía Bot API (`set_my_commands`,
`set_my_description`) al arrancar el servicio — no hace falta tocar BotFather, salvo para
la foto de perfil del bot (`/setuserpic`, algo que la Bot API no permite gestionar por código).

## 📝 Ejemplo de uso

**El usuario envía por Telegram:**
> Empresa de consultoría, 15 empleados, Madrid, quieren automatizar su proceso de ventas.

**El bot responde con el score contra el ICP y un análisis explicando el porqué** (ver
captura arriba), y en la Google Sheet queda registrada una fila con fecha, empresa,
empleados, ubicación, interés, score, decisión, confianza, motivo, texto original del lead
y `chat_id`. La primera vez que se usa la Sheet, el servicio crea automáticamente el
encabezado con formato.

**Ejemplo de `/metrics`:**

```json
{
  "leads_procesados": 12,
  "leads_calificados": 7,
  "leads_rechazados": 5,
  "errores_clasificacion": 0,
  "leads_hoy": 4,
  "score_promedio": 61.3,
  "tiempo_promedio_respuesta_segundos": 1.842,
  "uptime_segundos": 3421.6
}
```

## 🧠 Decisiones de diseño relevantes

- **Salida estructurada real**: `response_schema=LeadDecision` (Pydantic) en vez de
  `json.loads` sobre texto libre — el SDK valida del lado del cliente y expone
  `response.parsed` ya tipado.
- **Prompt injection**: el texto del lead siempre va delimitado y el `system_instruction`
  aclara que todo lo que hay ahí dentro es dato, nunca instrucción — combinado con el
  schema, el modelo no tiene forma de "responder libremente".
- **Fail-safe, no fail-open**: cualquier fallo hace que el lead se marque como NO
  calificado con confianza baja, nunca al revés.
- **Sin credenciales en disco**: Google Sheets usa Application Default Credentials —
  en Cloud Run resuelve contra la Service Account del servicio; en local, contra
  `gcloud auth application-default login`.
- **Puente sync/async documentado**: Flask/Gunicorn son síncronos y python-telegram-bot es
  async-first; se corre un event loop persistente en un hilo de fondo y se programan
  corrutinas con `asyncio.run_coroutine_threadsafe`.
- **Un fallo en Sheets nunca tumba el bot**: el usuario recibe su respuesta igual aunque
  el logging falle; el error queda en logs para revisión.
- **Métricas en memoria con limitación conocida**: si Cloud Run escala a más de una
  instancia, cada una lleva su propio contador — documentado, no se presenta como más de
  lo que es.

## 🔭 Qué cambiaría para producción real

1. **Secretos y colas reales**: mover `TELEGRAM_BOT_TOKEN` y `GEMINI_API_KEY` a Secret
   Manager, y añadir una cola (Cloud Tasks/Pub-Sub) entre el webhook y el procesamiento
   para no perder updates si Gemini tarda o el servicio se reinicia a mitad de proceso.
2. **Rate limiting y control de costes**: limitar mensajes por usuario/minuto y poner un
   tope diario de llamadas a Gemini con alertas de presupuesto.
3. **Prompt injection y auditoría reforzada**: añadir un paso de moderación previo que
   detecte intentos de manipulación explícitos antes del clasificador principal,
   registrándolos por separado para revisión del equipo.

## 💼 Cómo pitchearlo en un CV

> Construí un microservicio que califica leads recibidos por Telegram contra un ICP usando
> Gemini con salida estructurada (Pydantic), con logging automático a Google Sheets y
> observabilidad básica, desplegado en Cloud Run sin credenciales en disco y con
> mitigaciones explícitas contra prompt injection.


## 👤 Author

**Roger Andrés Álvarez Díaz**
Computer Science and Systems Engineering

<p>
  <a href="https://github.com/TogerAndres">
    <img src="https://img.shields.io/badge/GitHub-TogerAndres-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  </a>
  <a href="https://www.linkedin.com/in/roger-andrés-alvarez-diaz-52b395333/">
    <img src="https://img.shields.io/badge/LinkedIn-Roger%20Andrés%20Álvarez%20Díaz-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
  </a>
</p>

- 💻 GitHub: [github.com/TogerAndres](https://github.com/TogerAndres)
- 💼 LinkedIn: [roger-andrés-alvarez-diaz](https://www.linkedin.com/in/roger-andrés-alvarez-diaz-52b395333/)
