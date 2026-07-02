<div align="center">

<img src="capturas/LogoChatBot.png" alt="Lead Qualification Agent Logo" width="160">

# 🤖 Lead Qualification Agent

### A Telegram bot that qualifies leads for you, in seconds and without human judgment in the loop.

A microservice that receives lead messages via Telegram, evaluates them against an
**ICP (Ideal Customer Profile)** using Gemini with structured output, logs every result to
Google Sheets, and exposes basic metrics — built to run on Cloud Run with zero credentials
on disk.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Telegram Bot](https://img.shields.io/badge/python--telegram--bot-21.3-26A5E4?logo=telegram&logoColor=white)](https://python-telegram-bot.org/)
[![Gemini](https://img.shields.io/badge/Gemini%202.5%20Flash-LLM-4285F4?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#-license)

</div>

<br>

<p align="center">
  <img src="capturas/Lead-Cualificado.png" alt="Example of a qualified lead" width="420">
</p>

---

## 🔗 Live project

| | |
|---|---|
| 🤖 **Telegram bot** | [@LeadQualificationAIBot](https://t.me/LeadQualificationAIBot) |
| 💻 **GitHub repository** | [github.com/TogerAndres/lead-qualification-ai-agent](https://github.com/TogerAndres/lead-qualification-ai-agent) |
| 📊 **Google Sheet** (automatic lead log) | [View sheet](https://docs.google.com/spreadsheets/d/1auEmjbskYBtZuHBX5WgFH1iLnWnCwTCRm36VXo75tV8/edit?usp=sharing) |

The project was built in Python and deployed on Google Cloud Run. It uses Gemini for lead
classification, Telegram as the user interface, and Google Sheets for automatically logging
every evaluation. Message the bot on Telegram to see it qualify a lead in real time, and
check the sheet to see the row it just wrote.

## 📌 What problem does it solve?

When leads come in through chat (web, campaigns, forms connected to Telegram), someone on
the team has to read them one by one and decide whether they're worth pursuing before
handing them to sales. That doesn't scale, it's slow, and it depends on whoever happens to
be on shift that day.

**Lead Qualification Agent** automates that first filter: it receives the lead's message,
evaluates it against an ideal customer profile using an LLM with **real structured output
(not free text)**, replies instantly with a score and an analysis, and logs everything to a
Google Sheet ready for sales to review.

## ✨ Features

- 🤖 **Production-ready Telegram bot**, with `/start`, `/help`, and `/about` commands
  auto-registered via the Bot API on startup (nothing to configure by hand in BotFather).
- 🧠 **Real structured output classification**: Gemini responds with a Pydantic schema
  (`response_schema`) instead of hand-parsed JSON — eliminating an entire class of parsing
  errors.
- 🛡️ **Prompt-injection resistant**: the lead's text is always delimited
  (`<lead_data>...</lead_data>`) and the model can only fill in the schema fields, never
  "respond freely."
- 🧯 **Fail-safe, not fail-open**: if anything fails (network, quota, parsing), the lead is
  marked as NOT qualified with low confidence — never the other way around.
- 📊 **Automatic logging to Google Sheets** via Application Default Credentials, with no
  credentials JSON in the repo or the container.
- 📈 **In-memory metrics** exposed at `/metrics`: leads processed, qualified, rejected,
  average score, and response time.
- ☁️ **Cloud Run first**: health checks, fast startup, no state on disk, and a Service
  Account with minimal permissions (Editor access to the Sheet only).

## ⚙️ How it works

```
Telegram
   │  User sends a message describing their company / need
   ▼
HTTPS Webhook  (POST /webhook)
   │  app.py validates the secret_token and delegates to bot.process_update
   ▼
python-telegram-bot (bot.py)
   │  Sync/async bridge: delivers the update to the Application,
   │  triggers handlers.lead_message_handler
   ▼
llm_classifier.py
   │  Calls Gemini 2.5 Flash with response_schema=LeadDecision (Pydantic)
   │  The lead's text is delimited as data, never as an instruction
   ▼
Gemini 2.5 Flash
   │  Returns an already validated, typed LeadDecision (score, ICP criteria,
   │  decision, confidence, analysis) — no manual JSON parsing
   ▼
Telegram + Google Sheets
   Replies to the user with the result and logs the row
   (date, company, employees, location, interest, score, decision...)
   via sheets_logger.py (Google Sheets API + ADC, no credentials on disk)
```

## 🖼️ Screenshots

<table>
<tr>
<td width="50%">

**Qualified lead**

The bot replies in Telegram with the score against the ICP, a per-criterion
breakdown, and a natural-language analysis generated by the model.

<img src="capturas/Lead-Cualificado.png" alt="Lead qualified by the bot">

</td>
<td width="50%">

**Prompt injection resistance**

An attempt to manipulate the model through the lead's text is ignored: the
`system_instruction` and `response_schema` force the model to only fill in
the schema, never to follow instructions injected into the message.

<img src="capturas/Prompt-Injection-Malo.png" alt="Example of a blocked prompt injection attempt">

</td>
</tr>
</table>

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3.1 + Gunicorn |
| Bot | python-telegram-bot 21.3 |
| LLM | Gemini 2.5 Flash (`google-genai`, `response_schema`) |
| Validation | Pydantic |
| Data logging | Google Sheets API (gspread + Application Default Credentials) |
| Infrastructure | Docker (`python:3.12-slim`) + Google Cloud Run |

## 📁 Project structure

```
lead-qualification-agent/
│
├── app.py                  # Flask entry point: webhook, health check, metrics
├── bot.py                  # Telegram Application + sync/async bridge
├── handlers.py             # /start logic and lead message handling
├── llm_classifier.py       # Classification with Gemini (google-genai, response_schema)
├── sheets_logger.py        # Logging to Google Sheets via ADC
├── metrics.py               # In-memory counters
├── config.py                # Centralized environment variables
│
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .env.example
├── .gitignore
│
├── capturas/                # Screenshots used in this README
│
└── scripts/
    └── set_webhook.py       # Registers the webhook with Telegram after deploy
```

## 🚀 Local setup

### 1. Telegram bot

Talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token.

### 2. Gemini API key

Create one at [Google AI Studio](https://aistudio.google.com/apikey).

### 3. Google Sheets

For local development, the simplest approach is to authenticate with your own account:

```bash
gcloud auth application-default login
```

Create the Sheet, copy its ID from the URL, and share it with Editor access to the account
you're using. No credentials JSON is needed in the repo.

### 4. Run it

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in the variables
python app.py
```

> Telegram can't reach your `localhost` via webhook. For a full end-to-end local flow you'd
> need a tunnel (ngrok, Cloudflare Tunnel); the recommended approach is to test the
> endpoints (`/`, `/health`, `/metrics`) locally and the full flow once deployed.

## 🔐 Environment variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Yes | Bot token, obtained from BotFather |
| `TELEGRAM_WEBHOOK_SECRET` | No | Secret validated on every request to the webhook (strongly recommended in production) |
| `GEMINI_API_KEY` | Yes | Gemini key, from [aistudio.google.com](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | No | Model to use (default `gemini-2.5-flash`) |
| `GOOGLE_SHEET_ID` | Yes | ID of the Sheet where leads are logged |
| `GOOGLE_SHEET_NAME` | No | Sheet tab name (default `Leads`) |
| `PORT` | No | Service port (default `8080`) |

## ☁️ Deploying to Cloud Run

```bash
# 1. Build and push the image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/lead-qualification-agent

# 2. Deploy — no service_account.json: the Service Account with Editor
#    permissions on the Sheet is attached directly to the service
gcloud run deploy lead-qualification-agent \
  --image gcr.io/YOUR_PROJECT/lead-qualification-agent \
  --service-account YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com \
  --set-env-vars TELEGRAM_BOT_TOKEN=...,GEMINI_API_KEY=...,GOOGLE_SHEET_ID=...,TELEGRAM_WEBHOOK_SECRET=... \
  --allow-unauthenticated \
  --region us-central1

# 3. Register the webhook with Telegram (one time only)
python scripts/set_webhook.py https://your-service-xxxxx.run.app
```

The Cloud Run Service Account only needs **Editor** permissions on the Google Sheet (shared
with its `...@YOUR_PROJECT.iam.gserviceaccount.com` email) — no additional project-level IAM
roles are required.

## 🔌 Endpoints

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Root health check (Cloud Run) → `OK` |
| GET | `/health` | Explicit health check → `{"status": "ok"}` |
| GET | `/version` | Service version and stack |
| GET | `/metrics` | Leads processed / qualified / rejected, average score and response time |
| POST | `/webhook` | Receives Telegram updates |

## 💬 Telegram commands

| Command | What it does |
|---|---|
| `/start` | Welcome message and usage example |
| `/help` | List of available commands |
| `/about` | Technical info about the project (version, model, stack) |

These commands are automatically registered via the Bot API (`set_my_commands`,
`set_my_description`) when the service starts — nothing to set up manually in BotFather,
except the bot's profile picture (`/setuserpic`), which the Bot API doesn't allow managing
programmatically.

## 📝 Usage example

**The user sends via Telegram:**
> Consulting company, 15 employees, Madrid, looking to automate their sales process.

**The bot replies with the score against the ICP and an analysis explaining why** (see
screenshot above), and the Google Sheet gets a new row with date, company, employees,
location, interest, score, decision, confidence, reasoning, the lead's original text, and
`chat_id`. The first time the Sheet is used, the service automatically creates a formatted
header row.

**Example `/metrics` response:**

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

## 🧠 Relevant design decisions

- **Real structured output**: `response_schema=LeadDecision` (Pydantic) instead of
  `json.loads` on free text — the SDK validates client-side and exposes a fully typed
  `response.parsed`.
- **Prompt injection**: the lead's text is always delimited, and the `system_instruction`
  makes it explicit that everything inside it is data, never an instruction — combined with
  the schema, the model has no way to "respond freely."
- **Fail-safe, not fail-open**: any failure causes the lead to be marked as NOT qualified
  with low confidence, never the other way around.
- **No credentials on disk**: Google Sheets uses Application Default Credentials — on Cloud
  Run it resolves automatically against the service's attached Service Account; locally,
  against `gcloud auth application-default login`.
- **Documented sync/async bridge**: Flask/Gunicorn are synchronous and python-telegram-bot
  is async-first; a single persistent event loop runs on a background thread, and coroutines
  are scheduled from the sync handler with `asyncio.run_coroutine_threadsafe`.
- **A Sheets failure never takes down the bot**: the user still gets their reply even if
  logging fails; the error is logged for later review.
- **In-memory metrics with a known limitation**: since they live in the process, if Cloud
  Run scales to more than one instance, each one keeps its own counters — documented
  explicitly, not presented as more than it is.

## 🔭 What I'd change for real production

1. **Real secrets and queues**: move `TELEGRAM_BOT_TOKEN` and `GEMINI_API_KEY` to Secret
   Manager, and add a queue (Cloud Tasks/Pub-Sub) between the webhook and processing so no
   updates are lost if Gemini is slow or the service restarts mid-process.
2. **Rate limiting and cost control**: limit messages per user/minute and set a daily cap on
   Gemini calls with budget alerts.
3. **Reinforced prompt-injection auditing**: add a prior moderation step that detects
   explicit manipulation attempts before the main classifier, logging them separately for
   team review.

## 💼 How to pitch it on a resume

> Built a microservice that qualifies leads received via Telegram against an ICP using
> Gemini with structured output (Pydantic), with automatic logging to Google Sheets and
> basic observability, deployed on Cloud Run with no credentials on disk and explicit
> mitigations against prompt injection.

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026 Lead Qualification Agent

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.
```

Free to use, modify, and distribute.

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
