# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
python app.py                  # loads Whisper models (tiny/base/small) at startup — slow
python app.py --no-local-models  # skip Whisper loading, cloud-only mode — fast startup
```

Defaults to port 8000; auto-increments if busy. Override with `PORT=` in `.env` or environment.

## Environment

The app has its own `.env` loader (not python-dotenv). Create `.env` in the project root:

```
GROQ_API_KEY=...
OPENAI_API_KEY=...
FLASK_SECRET_KEY=...
OPENAI_MODEL=gpt-4o-mini
OPENAI_WEB_SEARCH_MODEL=gpt-4o-mini
OPENAI_TRANSCRIBE_MODEL=gpt-4o-mini-transcribe
PORT=8000

# Optional
OLLAMA_IP_URL=http://192.168.1.248:11434   # network Ollama instance (provider: ollama_ip)
NO_LOCAL_MODELS=1                           # alternative to --no-local-models flag
MAX_UPLOAD_MB=200                           # default 200
FLASK_ENV=production                        # enables HTTPS, HSTS, secure cookies
FLASK_DEBUG=1                               # enables Flask debug mode

# Password reset emails
SMTP_SERVER=...
SMTP_PORT=465
SMTP_USER=...
SMTP_PASSWORD=...
SENDER_EMAIL=...
```

Keys already set in the OS environment are NOT overridden by `.env`.

## Architecture

The entire application is one file: `app.py` (~4200 lines). There is no test suite and no build step.

**Database** — SQLite `users.db`, initialised on every startup via `init_db()`:
- `users` — email (PK), first_name, last_name, password_hash, role (`user`/`admin`)
- `projects` — groups of history items per user
- `history` — transcription results (raw_text, ai_notes, notes_model_used, notes_mode, openai_usage_history, project_id, image_path)
- `chat_history` — per-history-item Q&A (linked to `history.id`)
- `project_chat_history` — multi-source chat at the project level
- `ai_models` — cloud model registry (provider, model_type, model_id, enabled, is_default)
- `api_keys` — hashed bearer tokens for programmatic API access
- `compare_results` — log of compare-notes runs
- `app_logs` — server-side error/event log
- `password_reset_tokens` — short-lived email reset codes

**DB migration script** — `python db_migrate.py [--check]` applies schema changes without restarting Flask. Use on production when you want to migrate without a restart. `--check` is a dry run.

**Two processing modes** controlled by `processing_mode` field in every request:
- `offline` — local Whisper (`tiny`/`base`/`small`) for STT, Ollama `llama3` for notes/chat
- `online` — Groq or OpenAI for STT; OpenAI Responses API (with `web_search` tool) for chat; standard chat completions for notes

**Three model types**: `transcription`, `notes`, `chat`

**Three cloud providers**: `groq`, `openai`, `ollama_ip` (network Ollama via `OLLAMA_IP_URL`)

**Model selection flow**:
1. `MODEL_CATALOG` (in-code) defines what can be added to the DB
2. `DEFAULT_AI_MODELS` seeds `ai_models` on first run
3. At runtime, routes call `get_default_ai_model()` / `get_ai_model_by_id()` to pick from DB
4. Local models are never stored in DB — they are built on the fly by `build_local_model_list()`

**OpenAI-specific**: Notes always go through `chat_with_openai_responses()` (Responses API). Chat always uses `analyze_with_web_search()` (Responses API + `web_search` tool). Raw transcriptions use the `/v1/audio/transcriptions` REST endpoint directly. All OpenAI calls log usage to `openai_usage_history.jsonl` and attach per-request records to Flask `g`.

**Notes modes** — `notes_mode` field passed to `build_audio_notes_prompt()`:
- `full` — default; structured notes with tasks, summary, authenticity score
- `summary` — short 5-sentence summary
- `overview` — 2-4 paragraph overview
- `bullets` — 5-10 key bullet points
- `prompt` — generates an AI prompt from the text
- `reel-prepare` — generates a JSON payload for video reel generation
- `custom` — uses `custom_prompt_text` field (supports `{{tekst}}` placeholder)

**Projects** — every history item belongs to a project (auto-created if not provided). Routes under `/api/projects` manage project CRUD. `project_chat_history` stores multi-source chat at the project level.

**Authentication**:
- Session cookie (browser login at `/`)
- API key via `Authorization: Bearer <key>` or `X-API-Key` header — managed at `/api/keys`

**Roles**: `user` (default) and `admin`. Admin email is hardcoded as `ADMIN_EMAIL` in `app.py:47`. Admin routes are protected by `@require_role('admin')`.

**YouTube support**: `yt_dlp` downloads best-quality audio to `temp_uploads/`, transcribes, then deletes the file. Optional Deno runtime path configurable via `YT_DLP_DENO_PATH`.

## Key routes

| Route | Auth | Notes |
|---|---|---|
| `GET /api/models` | None | Returns local + cloud models with `request_settings` ready for use |
| `POST /transcribe` | Session | Multipart form; handles file upload, mic recording, YouTube URL, or webpage URL |
| `POST /api/youtube/transcribe` | Session/API key | JSON body; `save_to_history` defaults to false |
| `POST /api/webpage/read` | Session | Fetch and transcribe a webpage URL |
| `POST /transcribe-image` | Session | Upload an image for vision/OCR transcription |
| `POST /ask-question` | Session | JSON; Q&A against a stored transcription (6-message chat context) |
| `POST /new-chat` | Session | Reset chat history for a history item |
| `GET /get-history` | Session | Paginated list (50/page) of transcription history |
| `DELETE /delete-history/<id>` | Session | Delete a single history item |
| `POST /delete-history/bulk` | Session | Bulk delete history items |
| `PATCH /history/<id>/rename` | Session | Rename a history item |
| `POST /export/docx` | Session | Export notes as Word document |
| `POST /export/pdf` | Session | Export notes as PDF |
| `GET /settings` | Session | UI for managing `ai_models` table |
| `POST /settings/models` | Session | Add a model |
| `POST /settings/models/<id>` | Session | Update; set `display_name` to `"usun model"` to delete |
| `POST /settings/ollama-ip-url` | Session | Update `OLLAMA_IP_URL` in .env |
| `POST /settings/update-pricing` | Admin | Update model pricing overrides in `pricing_data.json` |
| `GET /usage-history` | Session | Per-request OpenAI usage and cost breakdown |
| `GET /api/keys` | Session | List API keys |
| `POST /api/keys` | Session | Create API key |
| `DELETE /api/keys/<id>` | Session | Delete API key |
| `POST /api/compare-notes` | Session | Compare notes across multiple sources with multiple models |
| `GET /api/compare-reports` | Session | Retrieve past compare-notes results |
| `GET /api/projects` | Session | List projects |
| `POST /api/projects` | Session | Create project |
| `PATCH /api/projects/<id>` | Session | Rename project |
| `DELETE /api/projects/<id>` | Session | Delete project |
| `GET /api/notes-prompt/<mode>` | Session | Retrieve system prompt for a given notes mode |
| `GET /api/ollama-ip/status` | Session | Check network Ollama connectivity |
| `GET /admin/users` | Admin | List all users |
| `POST /admin/users/<email>/role` | Admin | Change user role |
| `DELETE /admin/users/<email>` | Admin | Delete user |
| `POST /admin/restart` | Admin | Restart the Flask process |
| `GET /logs` | Admin | Application error/event log |
| `GET /reset-password` | None | Password reset request (requires SMTP config) |

## Model configuration

Model data and provider helpers live in `models_config.py`, imported into `app.py` after `load_env_file()` (so env vars are resolved at import time). Edit `models_config.py` to add providers, change catalog entries, or update `DEFAULT_AI_MODELS` / `LOCAL_MODEL_REQUIREMENTS`. DB-dependent model functions (`list_ai_models`, `get_default_ai_model`, etc.) remain in `app.py`.

Pricing lives in `MODEL_PRICING` / `AUDIO_PRICING` in `models_config.py` and can be overridden at runtime via `pricing_data.json` (written by `/settings/update-pricing`).

## Templates

Six Jinja2 templates in `templates/`: `login-page.html` (login), `rejestracja.html` (register), `index.html` (desktop transcription UI), `mobile-page.html` (mobile SPA), `settings.html` (model management), `zmiana-hasla.html` (change password).

**UI changes go to `mobile-page.html` only — `index.html` is frozen.**

### Shared functionality: `/test-page` and `/mobile`

Both pages implement the same feature set against identical Flask endpoints. When changing behaviour in one, apply the same change to the other:

| Feature | index.html | mobile-page.html |
|---|---|---|
| Transcription (file/mic/YT/URL) | `sendAudio()` → `POST /transcribe` | `submitFormData()` → `POST /transcribe` |
| AI chat Q&A | `sendQuestion()` → `POST /ask-question` | `sendChat()` → `POST /ask-question` |
| History load | `loadHistoryFromServer()` → `GET /get-history` | `loadHistory()` → `GET /get-history` |
| History item select | `displayHistoryItem(index)` | `loadHistItem(item)` |
| Authenticity prompt | `populateChatInputFromAuthenticityPrompt()` reads `currentNotes` | same function, same logic |
| History item rendering | event listeners on `.history-item-info` / `.delete-item-btn` | event listeners on `.hist-info` / `.hist-del` |

**Rule**: never use `JSON.stringify` or raw object data inside inline `onclick="..."` attributes — always attach event listeners in JS so arbitrary text in history titles cannot break parsing.

## External API integration notes

- **Groq**: uses the `groq` SDK (`client.audio.transcriptions.create`, `client.chat.completions.create`)
- **OpenAI transcription**: raw `requests.post` to `https://api.openai.com/v1/audio/transcriptions`
- **OpenAI chat/notes**: `create_openai_responses()` posts to `https://api.openai.com/v1/responses`
- **Ollama (local)**: `ollama.chat(model='llama3', ...)` — requires Ollama running locally with `llama3` pulled
- **Ollama (network)**: HTTP calls to `OLLAMA_IP_URL` — provider key is `ollama_ip`

## Adding a new cloud provider

1. Add entry to `PROVIDERS` dict in `models_config.py`
2. Add model definitions to `MODEL_CATALOG`
3. Add seed entries to `DEFAULT_AI_MODELS`
4. Add provider branch in `transcribe_with_cloud()` and/or `chat_with_cloud()` in `app.py`
