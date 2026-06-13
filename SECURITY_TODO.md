# Security TODO

Zmiany już wdrożone przez Claude (pkt 1-3):
- ✅ FLASK_SECRET_KEY wymagany — aplikacja nie startuje bez niego (app.py:83)
- ✅ debug=False domyślnie — sterowany przez FLASK_DEBUG=1 w .env (app.py:2239)
- ✅ SESSION_COOKIE_HTTPONLY, SESSION_COOKIE_SAMESITE='Lax' (app.py:91-93)
- ✅ SESSION_COOKIE_SECURE=True gdy FLASK_ENV=production (app.py:93)
- ✅ Rate limiting (flask-limiter) na: /, /register, /transcribe, /api/youtube/transcribe, /ask-question

---

## Do zrobienia przez Ciebie

### Wymagające decyzji / pracy manualnej

**[WYSOKI] SSRF — walidacja URL przed pobraniem**
- `app.py:853` — `fetch_webpage_content(url)` pobiera dowolny URL bez sprawdzania zakresu IP
- `app.py:1572` — `download_youtube_audio(youtube_url)` bez weryfikacji, że to faktycznie YouTube
- Naprawić: odrzucać URL z prywatnymi zakresami IP (127.x, 10.x, 192.168.x, 172.16-31.x) i wymuszać https://

**[WYSOKI] XSS — innerHTML z treścią AI**
- `templates/index.html` — `chatResponse.innerHTML = chatHistoryHtml` wstawia AI-generowany markdown do DOM
- `templates/mobile-page.html` — analogiczne miejsca
- Naprawić: dodać [DOMPurify](https://github.com/cure53/DOMPurify) przed każdym `innerHTML =` z zewnętrzną treścią

**[WYSOKI] Brak CSRF**
- Żaden endpoint POST nie sprawdza tokenu CSRF
- Opcja A (prosta): dodać nagłówek `X-CSRF-Token` generowany przy logowaniu, sprawdzać w każdym POST
- Opcja B: zainstalować Flask-WTF i użyć `CSRFProtect(app)`
- Dotyczy: /transcribe, /ask-question, /delete-history, /change-password, /settings/models, /export/*

**[ŚREDNI] Nagłówki bezpieczeństwa HTTP**
- Brak: X-Frame-Options, X-Content-Type-Options, Content-Security-Policy, HSTS
- Naprawić: `pip install flask-talisman` + `Talisman(app, ...)` po inicjalizacji app

**[ŚREDNI] Brak paginacji historii**
- `app.py` — `GET /get-history` pobiera WSZYSTKIE rekordy użytkownika bez LIMIT
- Dodać `LIMIT 50 OFFSET ?` i obsługę stronicowania w JS

**[ŚREDNI] Walidacja siły hasła przy zmianie**
- `app.py:2206+` — `/change-password` nie sprawdza wymagań (8 znaków, wielka litera, cyfra, znak specjalny)
- Przenieść funkcję walidacji z `/register` i użyć jej też tutaj

### Konfiguracja serwera produkcyjnego

**[KRYTYCZNY] Nie używać `python app.py` na produkcji**
- Użyć gunicorn/uwsgi: `gunicorn -w 4 app:app`
- Ustawić `FLASK_ENV=production` w zmiennych środowiskowych serwera

**[WYSOKI] Zabezpieczyć plik users.db**
- Plik bazy danych jest w katalogu aplikacji
- Upewnić się, że serwer WWW (nginx/apache) nie serwuje plików `.db` bezpośrednio
- Rozważyć przeniesienie poza katalog webroot

**[WYSOKI] Zabezpieczyć openai_usage_history.jsonl**
- Plik zawiera dane użycia API i może zawierać fragmenty zapytań
- Upewnić się, że nie jest dostępny publicznie (jak wyżej)

**[NISKI] Rate limiting — rozważyć Redis w produkcji**
- Obecna konfiguracja używa `memory://` (reset przy restarcie aplikacji)
- Na produkcji: `storage_uri="redis://localhost:6379"` w inicjalizacji Limitera (app.py:~100)

### Monitoring

**[NISKI] Dodać logowanie zdarzeń bezpieczeństwa**
- Nieudane próby logowania
- Zmiany hasła
- Usunięcia rekordów historii
- Można użyć istniejącego `app.logger`
