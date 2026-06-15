# Instrukcja API — System STT

Dokumentacja endpointów dostępnych dla zewnętrznych serwisów i automatyzacji.

---

## Autoryzacja

API obsługuje dwie metody autoryzacji. Endpointy API są zwolnione z wymogu tokenu CSRF — do wyboru klucz API lub sesja.

---

### Metoda 1 — Klucz API (zalecana dla zewnętrznych serwisów)

Klucze generujesz w **Ustawienia → Klucze API**. Klucz jest widoczny tylko raz po wygenerowaniu — zapisz go bezpiecznie.

Dołącz klucz do każdego żądania jako nagłówek HTTP:

```
Authorization: Bearer stt_TWÓJ_KLUCZ
```

lub alternatywnie:

```
X-API-Key: stt_TWÓJ_KLUCZ
```

**Przykład (curl):**
```bash
curl -X GET http://localhost:8000/get-history \
  -H "Authorization: Bearer stt_TWÓJ_KLUCZ"
```

**Ograniczenie do domeny (opcjonalne):**

Klucz można powiązać z konkretną domeną. Jeśli `allowed_origin` jest ustawiony, serwer weryfikuje nagłówek `Origin` lub `Referer` każdego żądania. Brak pasującego nagłówka skutkuje odpowiedzią `401`.

- Podaj pełne origin ze schematem: `https://example.com`
- Requestom server-to-server (skrypty, n8n), które nie wysyłają `Origin`/`Referer`, nie należy ustawiać tej opcji
- Puste `allowed_origin` = brak ograniczenia

**Zarządzanie kluczami:**

| Endpoint | Opis |
|---|---|
| `GET /api/keys` | Lista kluczy (bez wartości — klucz widoczny tylko przy tworzeniu) |
| `POST /api/keys` | Wygeneruj nowy klucz; JSON: `{"name": "...", "allowed_origin": "https://example.com"}` — `allowed_origin` opcjonalne |
| `DELETE /api/keys/<id>` | Usuń klucz |

**Przykładowa odpowiedź `POST /api/keys`:**
```json
{
  "id": 3,
  "name": "n8n produkcja",
  "allowed_origin": "https://n8n.example.com",
  "key": "stt_TWÓJ_KLUCZ_WIDOCZNY_TYLKO_RAZ"
}
```

---

### Metoda 2 — Sesja (dla aplikacji przeglądarkowych)

Sesja ustawiana jest przez cookie po zalogowaniu.

```
POST /
Content-Type: application/x-www-form-urlencoded
```

| Pole | Opis |
|---|---|
| `email` | Adres e-mail użytkownika |
| `password` | Hasło |
| `csrf_token` | Token CSRF z meta tagu `<meta name="csrf-token">` |

Sesja cookie (`session`) musi być wysyłana z każdym kolejnym żądaniem.  
Token CSRF jest wymagany tylko dla metody sesji (formularze HTML).

---

---

## Limity żądań

| Endpoint | Limit |
|---|---|
| `POST /transcribe` | 30/godz., 5/min |
| `POST /api/youtube/transcribe` | 10/godz., 2/min |
| `POST /api/webpage/read` | brak limitu |
| `POST /ask-question` | 60/godz., 10/min |
| `POST /new-chat` | 30/godz. |
| `POST /` (login) | 20/min, 5/s |

Przekroczenie limitu zwraca `429 Too Many Requests`.

---

## Endpointy

---

### GET /api/models

Zwraca listę dostępnych modeli AI. Nie wymaga autoryzacji.

**Parametry query:**

| Parametr | Wartości | Opis |
|---|---|---|
| `type` | `transcription`, `notes`, `chat` | Filtruj po typie modelu |
| `include_disabled` | `true` / `false` | Uwzględnij wyłączone modele (domyślnie `false`) |

**Przykład żądania:**
```
GET /api/models?type=transcription
```

**Przykład odpowiedzi:**
```json
{
  "local": [
    {
      "id": "local:base",
      "label": "Whisper Base (lokalny)",
      "provider": "local",
      "model_type": "transcription",
      "request_settings": { "processing_mode": "offline", "model_name": "base" }
    }
  ],
  "cloud": [
    {
      "id": 3,
      "label": "Whisper Large v3 (Groq)",
      "provider": "groq",
      "model_type": "transcription",
      "is_default": true,
      "request_settings": { "processing_mode": "online", "cloud_model_id": "3" }
    }
  ],
  "models": [...],
  "counts": { "local": 3, "cloud": 5, "total": 8 },
  "filters": { "type": "transcription", "include_disabled": false }
}
```

Pole `request_settings` z każdego modelu możesz przekazać bezpośrednio do `/transcribe` lub `/api/youtube/transcribe`.

---

### POST /transcribe

Transkrybuje plik audio, link YouTube, adres strony WWW lub wklejony tekst.  
Generuje notatki AI i opcjonalnie zapisuje wynik do historii.

**Content-Type:** `multipart/form-data`

**Pola formularza:**

| Pole | Wymagane | Opis |
|---|---|---|
| `file` | \* | Plik audio (aac, flac, m4a, mp3, mp4, ogg, opus, wav, webm) — jeśli nie podano `youtube_url`, `webpage_url` ani `direct_text` |
| `youtube_url` | \* | URL YouTube (zamiast pliku) |
| `webpage_url` | \* | URL strony WWW (zamiast pliku) |
| `direct_text` | \* | Tekst wklejony bezpośrednio (zamiast pliku) |
| `processing_mode` | nie | `online` (domyślny) lub `offline` (lokalne modele Whisper/Ollama) |
| `cloud_model_id` | nie | ID modelu transkrypcji z `/api/models` (tryb online) |
| `model_name` | nie | Nazwa lokalnego modelu Whisper: `tiny`, `base`, `small` (tryb offline) |
| `language` | nie | Kod języka (`pl`, `en`, `de`, …) lub `auto` (domyślny) |
| `task` | nie | `transcribe` (domyślny) lub `translate` (tłumaczenie na angielski) |
| `notes_mode` | nie | Tryb notatek AI (patrz tabela poniżej) |
| `custom_name` | nie | Własna nazwa rekordu w historii |

**Tryby notatek (`notes_mode`):**

| Wartość | Opis |
|---|---|
| `full` | Pełne notatki strukturalne (domyślny) |
| `summary` | Zwięzłe podsumowanie |
| `overview` | Ogólny przegląd tematyczny |
| `bullets` | Lista punktów kluczowych |
| `prompt` | Niestandardowy prompt |
| `reel-prepare` | Format do przygotowania materiału wideo |

**Przykład żądania (curl):**
```bash
curl -X POST http://localhost:8000/transcribe \
  -H "X-CSRFToken: TOKEN" \
  -b "session=COOKIE" \
  -F "file=@nagranie.mp3" \
  -F "processing_mode=online" \
  -F "notes_mode=summary" \
  -F "language=pl"
```

**Przykład odpowiedzi:**
```json
{
  "text": "Pełny tekst transkrypcji...",
  "notes": "Podsumowanie AI...",
  "summary": "Podsumowanie AI...",
  "language": "pl",
  "model_used": "Groq / whisper-large-v3",
  "notes_model_used": "gpt-4o-mini",
  "task": "transcribe",
  "saved": true,
  "saved_name": "nagranie.mp3",
  "record_id": 42,
  "authenticity_score": 0.78,
  "openai_usage_history": [...]
}
```

---

### POST /api/youtube/transcribe

Transkrybuje film YouTube na podstawie URL. Próbuje najpierw pobrać napisy (szybko), w razie ich braku pobiera audio i wykonuje STT.

**Content-Type:** `application/json`

**Ciało żądania:**
```json
{
  "yt_url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
  "settings": {
    "processing_mode": "online",
    "cloud_model_id": "3",
    "language": "auto",
    "task": "transcribe",
    "custom_name": "Moja nazwa",
    "save_to_history": false
  }
}
```

| Pole | Wymagane | Opis |
|---|---|---|
| `yt_url` | **tak** | URL YouTube (akceptuje też `youtube_url`) |
| `settings.processing_mode` | nie | `online` / `offline` |
| `settings.cloud_model_id` | nie | ID modelu z `/api/models` |
| `settings.language` | nie | Kod języka lub `auto` |
| `settings.task` | nie | `transcribe` lub `translate` |
| `settings.custom_name` | nie | Własna nazwa rekordu |
| `settings.save_to_history` | nie | `true` / `false` (domyślnie `false`) |

Pola z `settings` można podać też na poziomie głównym (`yt_url`, `processing_mode`, …).

**Przykład odpowiedzi:**
```json
{
  "text": "Treść transkrypcji...",
  "notes": "Notatki AI...",
  "summary": "Notatki AI...",
  "language": "pl",
  "model_used": "Groq / whisper-large-v3",
  "notes_model_used": "gpt-4o-mini",
  "task": "transcribe",
  "saved": false,
  "saved_name": "Tytuł filmu YT",
  "record_id": null,
  "authenticity_score": 0.91,
  "youtube": {
    "id": "XXXXXXXXXXX",
    "title": "Tytuł filmu",
    "duration": 342,
    "url": "https://www.youtube.com/watch?v=XXXXXXXXXXX"
  },
  "openai_usage_history": [...]
}
```

---

### POST /api/webpage/read

Pobiera i przetwarza treść strony WWW. Generuje notatki AI.

**Content-Type:** `application/json`

**Ciało żądania:**
```json
{
  "url": "https://example.com/artykul",
  "settings": {
    "processing_mode": "online",
    "cloud_model_id": "3",
    "custom_name": "Artykuł o X",
    "save_to_history": true
  }
}
```

| Pole | Wymagane | Opis |
|---|---|---|
| `url` | **tak** | Adres URL strony (akceptuje też `webpage_url`) |
| `settings.processing_mode` | nie | `online` / `offline` |
| `settings.cloud_model_id` | nie | ID modelu z `/api/models` |
| `settings.custom_name` | nie | Własna nazwa rekordu |
| `settings.save_to_history` | nie | `true` / `false` (domyślnie `false`) |

**Przykład odpowiedzi:**
```json
{
  "text": "Pełna treść strony...",
  "notes": "Notatki AI...",
  "summary": "Notatki AI...",
  "notes_model_used": "gpt-4o-mini",
  "model_used": "Strona internetowa + notatki: gpt-4o-mini",
  "saved": true,
  "saved_name": "Artykuł o X",
  "record_id": 17,
  "authenticity_score": 0.83,
  "webpage": {
    "url": "https://example.com/artykul",
    "title": "Tytuł strony"
  },
  "openai_usage_history": [...]
}
```

---

### POST /ask-question

Wysyła pytanie do AI w kontekście wybranego rekordu transkrypcji. AI ma dostęp do treści transkrypcji oraz ostatnich 6 wiadomości z historii czatu.  
OpenAI używa Responses API z narzędziem `web_search`.

**Content-Type:** `application/json`

**Ciało żądania:**
```json
{
  "id": 42,
  "question": "Jakie są główne wnioski z tego nagrania?",
  "processing_mode": "online",
  "chat_model_id": "5"
}
```

| Pole | Wymagane | Opis |
|---|---|---|
| `id` | **tak** | ID rekordu z historii (`record_id` z `/transcribe` lub `/get-history`) |
| `question` | **tak** | Treść pytania |
| `processing_mode` | nie | `online` / `offline` |
| `chat_model_id` | nie | ID modelu czatu z `/api/models?type=chat` |

**Przykład odpowiedzi:**
```json
{
  "answer": "Odpowiedź AI na pytanie...",
  "engine": "gpt-4o-mini",
  "chat_model_used": "gpt-4o-mini",
  "sources": [
    { "url": "https://...", "title": "Źródło" }
  ],
  "authenticity_score": null,
  "openai_usage_history": [...]
}
```

---

### GET /get-history

Pobiera historię transkrypcji zalogowanego użytkownika. Zwraca 50 rekordów na stronę.

**Parametry query:**

| Parametr | Opis |
|---|---|
| `offset` | Przesunięcie (domyślnie `0`) |

**Przykład żądania:**
```
GET /get-history?offset=50
```

**Przykład odpowiedzi:**
```json
{
  "items": [
    {
      "id": 42,
      "filename": "Moja transkrypcja",
      "raw_text": "Treść transkrypcji...",
      "ai_notes": "Notatki AI...",
      "notes_model_used": "gpt-4o-mini",
      "created_at": "2026-06-15 10:30:00",
      "chat_count": 3,
      "authenticity_score": 0.78,
      "token_summary": { "input": 1200, "output": 450, "cost": 0.0003 },
      "chat_messages": [
        {
          "role": "user",
          "content": "Pytanie...",
          "created_at": "2026-06-15 10:31:00",
          "engine": "gpt-4o-mini"
        }
      ],
      "openai_usage_history": [...]
    }
  ],
  "total": 127,
  "offset": 50,
  "limit": 50
}
```

---

### POST /new-chat

Tworzy nowy pusty rekord w historii (bez transkrypcji). Przydatne do inicjowania sesji czatu bez pliku audio.

**Content-Type:** `application/json` lub `application/x-www-form-urlencoded` (brak ciała)

**Odpowiedź:**
```json
{ "record_id": 43 }
```

---

### DELETE /delete-history/\<id\>

Usuwa pojedynczy rekord z historii.

```
DELETE /delete-history/42
X-CSRFToken: TOKEN
```

**Odpowiedź:** `200 OK` lub `404` jeśli rekord nie istnieje lub nie należy do użytkownika.

---

### POST /delete-history/bulk

Usuwa wiele rekordów historii jednocześnie.

**Content-Type:** `application/json`

```json
{ "ids": [42, 43, 44] }
```

**Odpowiedź:** `200 OK` z liczbą usuniętych rekordów.

---

### PATCH /history/\<id\>/rename

Zmienia tytuł (nazwę) rekordu w historii.

**Content-Type:** `application/json`

```json
{ "title": "Nowa nazwa rekordu" }
```

**Odpowiedź:**
```json
{ "id": 42, "title": "Nowa nazwa rekordu" }
```

---

### POST /export/docx

Generuje i pobiera plik `.docx` z podaną treścią.

**Content-Type:** `application/x-www-form-urlencoded`

| Pole | Opis |
|---|---|
| `content` | Treść dokumentu (tekst, nowe linie jako `\n`) |
| `title` | Tytuł dokumentu (domyślnie `Dokument`) |

**Odpowiedź:** plik `.docx` (`Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`)

---

### POST /export/pdf

Generuje i pobiera plik `.pdf` z podaną treścią.

**Content-Type:** `application/x-www-form-urlencoded`

| Pole | Opis |
|---|---|
| `content` | Treść dokumentu |
| `title` | Tytuł dokumentu (domyślnie `Dokument`) |

**Odpowiedź:** plik `.pdf` (`Content-Type: application/pdf`)

---

## Kody błędów

| Kod | Znaczenie |
|---|---|
| `400` | Nieprawidłowe żądanie (brakujące pola, zły format, zły typ pliku) |
| `401` | Brak autoryzacji (brak sesji lub wygasłe cookie) |
| `403` | Błąd CSRF (brakujący lub nieprawidłowy token) |
| `404` | Rekord nie istnieje lub nie należy do użytkownika |
| `413` | Plik za duży (domyślny limit: 200 MB) |
| `429` | Przekroczono limit żądań |
| `500` | Błąd serwera (błąd modelu AI, błąd sieci, itd.) |

Wszystkie błędy zwracają JSON:
```json
{ "error": "Opis błędu po polsku" }
```

---

## Przykład kompletnego przepływu (Python)

```python
import requests

BASE = "http://localhost:8000"
s = requests.Session()

# 1. Pobierz stronę logowania (CSRF token)
login_page = s.get(f"{BASE}/")
csrf = login_page.text.split('name="csrf-token" content="')[1].split('"')[0]

# 2. Zaloguj się
s.post(f"{BASE}/", data={
    "email": "user@example.com",
    "password": "haslo123",
    "csrf_token": csrf
})

# 3. Pobierz listę modeli
models = s.get(f"{BASE}/api/models?type=transcription").json()
cloud_model_id = next(
    m["id"] for m in models["cloud"] if m.get("is_default")
)

# 4. Transkrybuj plik
with open("nagranie.mp3", "rb") as f:
    result = s.post(f"{BASE}/transcribe", 
        headers={"X-CSRFToken": csrf},
        data={
            "processing_mode": "online",
            "cloud_model_id": cloud_model_id,
            "notes_mode": "summary",
            "language": "pl"
        },
        files={"file": f}
    ).json()

record_id = result["record_id"]
print("Transkrypcja:", result["text"][:200])
print("Notatki:", result["notes"][:200])

# 5. Zadaj pytanie do AI
answer = s.post(f"{BASE}/ask-question",
    headers={"X-CSRFToken": csrf, "Content-Type": "application/json"},
    json={"id": record_id, "question": "Jakie są kluczowe wnioski?"}
).json()

print("Odpowiedź AI:", answer["answer"])
```

---

## Przykład przepływu (n8n / Make)

### Krok 1 — Logowanie (HTTP Request)
- Method: `POST`
- URL: `http://localhost:8000/`
- Body: `form-urlencoded` → `email`, `password`, `csrf_token`
- Zapisz cookie sesji i CSRF token do zmiennych przepływu

### Krok 2 — Transkrypcja YouTube (HTTP Request)
- Method: `POST`
- URL: `http://localhost:8000/api/youtube/transcribe`
- Headers: `X-CSRFToken: {{csrf_token}}`, `Content-Type: application/json`
- Cookie: `session={{session_cookie}}`
- Body (JSON):
```json
{
  "yt_url": "{{youtube_url}}",
  "settings": {
    "processing_mode": "online",
    "save_to_history": true
  }
}
```

### Krok 3 — Pytanie do AI (HTTP Request)
- Method: `POST`  
- URL: `http://localhost:8000/ask-question`
- Headers: `X-CSRFToken: {{csrf_token}}`, `Content-Type: application/json`
- Body (JSON):
```json
{
  "id": "{{record_id}}",
  "question": "Streść materiał w 3 zdaniach."
}
```
