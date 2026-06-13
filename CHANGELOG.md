# Changelog

## 2026-06-13 — Hardening bezpieczeństwa

### app.py

**Konfiguracja aplikacji**
- `FLASK_SECRET_KEY` jest teraz wymagany — aplikacja rzuca `RuntimeError` przy starcie jeśli zmienna nie jest ustawiona
- `debug=True` zastąpiony przez `FLASK_DEBUG=1` (env var); domyślnie `False`
- Dodano `SESSION_COOKIE_HTTPONLY = True` — JavaScript nie może odczytać ciasteczka sesji
- Dodano `SESSION_COOKIE_SAMESITE = 'Lax'` — blokuje wysyłanie ciasteczka w cross-site requestach
- Dodano `SESSION_COOKIE_SECURE = True` gdy `FLASK_ENV=production`
- Dodano `MAX_CONTENT_LENGTH` (domyślnie 200 MB, konfigurowalne przez `MAX_UPLOAD_MB` w `.env`)
- Dodano `ALLOWED_AUDIO_EXTENSIONS` — whitelist rozszerzeń plików akceptowanych przy uploadzie

**Rate limiting (flask-limiter)**
- `POST /` (login): 20/min, 5/s
- `POST /register`: 10/h, 3/min
- `POST /transcribe`: 30/h, 5/min
- `POST /api/youtube/transcribe`: 10/h, 2/min
- `POST /ask-question`: 60/h, 10/min

**CSRF (flask-wtf)**
- `CSRFProtect(app)` aktywne globalnie dla wszystkich POST/DELETE
- Handler `CSRFError` zwraca JSON `400` z komunikatem po polsku zamiast domyślnej strony HTML

**Nagłówki HTTP (flask-talisman)**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Content-Security-Policy`: `default-src 'self'`; skrypty/style z `'unsafe-inline'` i `cdn.jsdelivr.net`; `frame-ancestors 'none'`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy`: mikrofon tylko `'self'`, kamera/geolokalizacja zablokowane
- HSTS i `force_https` aktywne tylko gdy `FLASK_ENV=production`

**SSRF — ochrona przed wewnętrznymi requestami**
- Nowa funkcja `_assert_safe_url(url)` — odrzuca protokoły inne niż http/https oraz URL wskazujące na prywatne zakresy IP (127.x, 10.x, 172.16-31.x, 192.168.x, link-local, IPv6 private)
- Nowa funkcja `_assert_youtube_url(url)` — waliduje regex youtube.com/youtu.be po stronie serwera
- Obie funkcje wywołane wewnątrz `fetch_webpage_content()` i `download_youtube_audio()` — chronią wszystkich wywołujących

**Upload plików**
- Walidacja rozszerzenia przed zapisem pliku (whitelist: aac, flac, m4a, mp3, mp4, mpeg, mpga, ogg, opus, txt, wav, webm)
- Handler błędu `413` zwraca JSON z czytelnym komunikatem o limicie

**Paginacja historii**
- `GET /get-history?offset=N` — zwraca `{"items": [...], "total": N, "offset": N, "limit": 50}` zamiast całej listy
- Zapytanie chat_history ograniczone do rekordów z bieżącej strony (`WHERE record_id IN (...)`)
- Stała `HISTORY_PAGE_SIZE = 50`

**Walidacja hasła**
- Nowa funkcja `validate_password_strength(password)` — zwraca komunikat błędu lub `None`
- Używana zarówno przy rejestracji (`/register`) jak i zmianie hasła (`/change-password`)
- Wymagania: min. 8 znaków, wielka litera, cyfra, znak specjalny

### .env

- Dodano `FLASK_SECRET_KEY` (losowy 32-bajtowy hex)
- Dodano `FLASK_DEBUG=0`

### requirements.txt

- Dodano `flask-limiter==4.1.1`
- Dodano `flask-wtf==1.3.0`
- Dodano `flask-talisman==1.1.0`

### templates/index.html i mobile-page.html

- Dodano `<meta name="csrf-token" content="{{ csrf_token() }}">` w `<head>`
- Dodano `getCsrfToken()` — helper JS odczytujący token z meta tagu
- Nagłówek `X-CSRFToken` dodany do wszystkich fetch POST/DELETE: `/transcribe`, `/ask-question`, `/delete-history`
- Paginacja historii: `loadHistoryFromServer(append)` / `loadHistory(append)` z przyciskiem "Pokaż więcej"
- Dodano `DOMPurify 3.2.6` (jsdelivr CDN)
- Sanitizacja treści AI przed wstawieniem do DOM: `DOMPurify.sanitize(chatHistoryHtml)` i `DOMPurify.sanitize(formatAiText(text))`

### templates/login-page.html, rejestracja.html, zmiana-hasla.html, settings.html

- Dodano `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` w każdym formularzu POST

### SECURITY_TODO.md (nowy plik)

Zawiera listę zadań wymagających ręcznej konfiguracji serwera produkcyjnego (gunicorn, nginx, Redis dla rate limitera, logowanie zdarzeń bezpieczeństwa).
