# Changelog

## 2026-06-15 — Statystyki użycia, cennik modeli, refaktor CSS, nawigacja sidebar

### models_config.py (nowe funkcje)

- Dodano `MODEL_PRICING` — słownik cen tokenów (USD/1M) dla wszystkich modeli OpenAI i Groq, w tym `gpt-4o-transcribe` i `gpt-4o-mini-transcribe`
- Dodano `AUDIO_PRICING` — słownik cen modeli audio (USD/minutę): `whisper-1`, `whisper-large-v3`, `distil-whisper-large-v3-en`, `whisper-large-v3-turbo`
- `resolve_pricing_key(model_name)` — dopasowanie prefiksowe nazwy modelu do klucza cennika (obsługa wersjonowanych nazw jak `gpt-4o-mini-2024-07-18`)
- `get_audio_duration_seconds(file_path)` — czas trwania audio przez `ffprobe`
- `get_audio_cost(model_name, seconds)` — koszt USD na podstawie czasu i cennika
- `PRICING_DATA_FILE`, `load_pricing_data()`, `save_pricing_data()` — zapis/odczyt nadpisań cennika do pliku `pricing_data.json` z timestampem ostatniej aktualizacji
- `get_effective_model_pricing()` — scala `MODEL_PRICING` z nadpisaniami z pliku; używane w runtime bez restartu

### app.py

**Śledzenie kosztów modeli audio**
- `extract_openai_usage()` obsługuje teraz pole `duration` (sekundy) z odpowiedzi `verbose_json` (`whisper-1`)
- `transcribe_with_cloud()` — Groq: po transkrypcji mierzy czas pliku przez `ffprobe` i zapisuje rekord użycia z polem `seconds`; OpenAI `whisper-1`: wymuszony format `verbose_json` dla uchwycenia czasu trwania
- `compute_token_summary()` i `_aggregate()` w `usage_history`: gdy rekord ma `seconds` zamiast tokenów — koszt obliczany przez `get_audio_cost()`

**Nowe trasy**
- `GET /usage-history` — widok historii zużycia tokenów i kosztów; admin może przeglądać dowolnego użytkownika (`?view=email`) lub wszystkich (`?view=__all__`)
- `POST /settings/update-pricing` — pobiera aktualny cennik z LiteLLM (`model_prices_and_context_window.json`), zapisuje zmiany do `pricing_data.json`, zwraca liczbę zaktualizowanych modeli
- `POST /admin/restart` — restart procesu serwera (tylko admin)
- `POST /new-chat` — zeruje historię czatu dla danego rekordu
- `POST /delete-history/bulk` — masowe usuwanie elementów historii
- `PATCH /history/<id>/rename` — zmiana tytułu rekordu historii

**Trasa `/settings`**
- Przekazuje do szablonu: `model_pricing`, `audio_pricing`, `pricing_last_updated`, `user` (dane zalogowanego użytkownika)

**Trasa `/usage-history`**
- Przekazuje do szablonu: `user`, `model_pricing`, dane agregatów (tokeny, koszty, wykresy dzienne, zestawienie per model/operacja)
- Admin: `user_leaderboard` — ranking użytkowników według kosztu

### templates/usage-history-page.html (nowy plik)

- Karty podsumowania (tokeny wejściowe/wyjściowe, koszt całkowity, koszt ostatnich 30 dni)
- Wykres słupkowy aktywności dziennej (ostatnie 30 dni)
- Tabela kosztów per model i per operacja
- Admin: przełącznik widoku użytkowników (pill-linki), tabela rankingowa
- Nawigacja: sidebar overlay (przycisk ☰ + panel z prawej) identyczny jak w `mobile-page.html`

### templates/settings.html

- Sekcja cennika tokenów (tabela `MODEL_PRICING` per model)
- Sekcja cennika audio (tabela `AUDIO_PRICING` per model)
- Przycisk „Aktualizuj cenniki" (tylko admin) + etykieta „zaktualizowano N dni temu"
- Nawigacja: zastąpiono stary dropdown hamburger sidebar overlay (przycisk ☰ + panel z prawej)
- Szablon otrzymuje zmienną `user` (dane zalogowanego użytkownika do wyświetlenia w profilu sidebara)

### Refaktor CSS — ekstrakcja styli inline do plików zewnętrznych

Wszystkie bloki `<style>` usunięte z szablonów HTML i zastąpione linkami do plików CSS:

| Szablon | Pliki CSS |
|---|---|
| `index.html` | `style.css` |
| `mobile-page.html` | `style.css` + `style-mobile.css` |
| `settings.html` | `style.css` + `style-settings.css` |
| `login-page.html` | `style.css` + `style-login.css` |
| `rejestracja.html` | `style.css` + `style-rejestracja.css` |
| `zmiana-hasla.html` | `style.css` + `style-zmiana-hasla.css` |
| `usage-history-page.html` | `style.css` + `style-usage-history.css` |

**Nowe pliki CSS (`static/`)**
- `style-mobile.css` — kompletny design system mobile (tokeny, ekrany, karty, overlaye, bottom sheets, czat, historia, toast)
- `style-settings.css` — nadpisania specyficzne dla strony ustawień (body, label, input, .btn)
- `style-usage-history.css` — nadpisania body + pełny CSS sidebar overlay dla tej strony
- `style-login.css` — jasny motyw dla strony logowania (Bootstrap override)
- `style-rejestracja.css` — jasny motyw dla strony rejestracji
- `style-zmiana-hasla.css` — ciemny glassmorphism override dla strony zmiany hasła

**`style.css` — rozszerzenia**
- Nowe tokeny CSS w `:root`: `--bg-panel`, `--bg-control`, `--purple`, `--blue`, `--green`, `--amber`, `--red`, `--border`, `--gradient`, `--r-card`, `--r-panel`, `--touch`
- Nowe klasy wspólne: `.page`, `.topbar`, `.section`, `.section-header`, `.nav-link`, `.view-label`, `.user-switcher`, `.user-pill`, karty statystyk, wykresy słupkowe, tabele
- Sidebar overlay: `.overlay`, `.overlay--right`, `.backdrop`, `.sidebar`, `.sidebar-profile`, `.sidebar-avatar`, `.sidebar-nav`, `.nav-item`, `.nav-icon`, `.sidebar-footer`, `.logout-btn`, `.icon-btn`

### pricing_data.json (nowy plik)

Plik nadpisań cennika — tworzony automatycznie przy pierwszej aktualizacji przez `/settings/update-pricing`. Zawiera ceny per model i timestamp ostatniej aktualizacji.

---

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
