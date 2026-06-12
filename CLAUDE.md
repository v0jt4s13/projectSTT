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
```

Keys already set in the OS environment are NOT overridden by `.env`.

## Architecture

The entire application is one file: `app.py` (~2200 lines). There is no test suite and no build step.

**Database** — SQLite `users.db`, initialised on every startup via `init_db()`:
- `users` — email (PK), first_name, last_name, password_hash
- `history` — transcription results per user (raw_text, ai_notes, notes_model_used, openai_usage_history)
- `chat_history` — per-transcription Q&A conversation (linked to `history.id`)
- `ai_models` — cloud model registry (provider, model_type, model_id, enabled, is_default)

**Two processing modes** controlled by `processing_mode` field in every request:
- `offline` — local Whisper (`tiny`/`base`/`small`) for STT, Ollama `llama3` for notes/chat
- `online` — Groq or OpenAI for STT; OpenAI Responses API (with `web_search` tool) for chat; standard chat completions for notes

**Three model types**: `transcription`, `notes`, `chat`

**Two cloud providers**: `groq`, `openai`

**Model selection flow**:
1. `MODEL_CATALOG` (in-code) defines what can be added to the DB
2. `DEFAULT_AI_MODELS` seeds `ai_models` on first run
3. At runtime, routes call `get_default_ai_model()` / `get_ai_model_by_id()` to pick from DB
4. Local models are never stored in DB — they are built on the fly by `build_local_model_list()`

**OpenAI-specific**: Notes always go through `chat_with_openai_responses()` (Responses API). Chat always uses `analyze_with_web_search()` (Responses API + `web_search` tool). Raw transcriptions use the `/v1/audio/transcriptions` REST endpoint directly. All OpenAI calls log usage to `openai_usage_history.jsonl` and attach per-request records to Flask `g`.

**YouTube support**: `yt_dlp` downloads best-quality audio to `temp_uploads/`, transcribes, then deletes the file. Optional Deno runtime path configurable via `YT_DLP_DENO_PATH`.

## Key routes

| Route | Auth | Notes |
|---|---|---|
| `GET /api/models` | None | Returns local + cloud models with `request_settings` ready for use |
| `POST /api/youtube/transcribe` | Session | JSON body; `save_to_history` defaults to false |
| `POST /transcribe` | Session | Multipart form; handles file upload or YouTube URL |
| `POST /ask-question` | Session | JSON; Q&A against a stored transcription with 6-message chat context |
| `GET /settings` | Session | UI for managing `ai_models` table |
| `POST /settings/models/<id>` | Session | Set `display_name` to `"usun model"` to delete |

## Model configuration

Model data and provider helpers live in `models_config.py`, imported into `app.py` after `load_env_file()` (so env vars are resolved at import time). Edit `models_config.py` to add providers, change catalog entries, or update `DEFAULT_AI_MODELS` / `LOCAL_MODEL_REQUIREMENTS`. DB-dependent model functions (`list_ai_models`, `get_default_ai_model`, etc.) remain in `app.py`.

## Templates

Six Jinja2 templates in `templates/`: `login-page.html` (login), `rejestracja.html` (register), `index.html` (desktop transcription UI), `mobile-page.html` (mobile SPA), `settings.html` (model management), `zmiana-hasla.html` (change password).

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
- **Ollama**: `ollama.chat(model='llama3', ...)` — requires Ollama running locally with `llama3` pulled

## Adding a new cloud provider

1. Add entry to `PROVIDERS` dict
2. Add model definitions to `MODEL_CATALOG`
3. Add seed entries to `DEFAULT_AI_MODELS`
4. Add provider branch in `transcribe_with_cloud()` and/or `chat_with_cloud()`
