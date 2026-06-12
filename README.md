# **Projekt STT (Speech-to-Text) z Notatkami AI** 🚀

Aplikacja webowa typu **SaaS** zbudowana we **Flasku**, która pozwala na **rejestrację użytkowników**, **nagrywanie lub przesyłanie plików audio**, a następnie **automatyczne generowanie transkrypcji** oraz **inteligentnych notatek i list zadań**.

---

## **🛠️ Główne Funkcje (Tech Stack)**

* **Logowanie i Baza Danych:** System **rejestracji, autoryzacji oraz zmiany hasła** użytkowników oparty na **Flask** oraz bazie **SQLite**. Wszystkie hasła są bezpiecznie i nieodwracalnie **haszowane jednokierunkowo z** algorytmem `pbkdf2:sha256` przy użyciu biblioteki *Werkzeug*.
* **Panel Historii Nagrań:** Integracja bazy danych z bocznym panelem (Sidebar), który pozwala przeglądać listę zapisanych nagrań pod własnymi nazwami, wczytywać archiwalne transkrypcje oraz trwale je usuwać.
* **Hybrydowa Transkrypcja (STT):** Zamiana **mowy na tekst** w dwóch trybach do wyboru:
  * **Lokalnie:** Przy użyciu modeli **OpenAI Whisper** (*Tiny*, *Base*, *Small*).
  * **W chmurze:** Przetwarzanie sieciowe przez modele skonfigurowane w ustawieniach, m.in. **Groq** oraz **OpenAI**.
* **Inteligentny Timer i Odliczanie:** Interfejs automatycznie kalkuluje czas oczekiwania. Dla modeli chmurowych uruchamia stoper zliczający sekundy w górę, a dla modeli lokalnych (w tym zoptymalizowanego modelu `base`) precyzyjnie wylicza czas na podstawie długości pliku audio za pomocą zaawansowanych mnożników.
* **Obsługa Różnych Źródeł Danych:** Możliwość nagrywania z mikrofonu (z funkcją pauzy i wznawiania), przesyłania gotowych plików audio/tekstowych z dysku oraz **automatycznego pobierania i przetwarzania filmów z serwisu YouTube (URL)**.
* **Wizualizator Audio Live:** Dynamiczny wykres falowy wbudowany w interfejs, reagujący w czasie rzeczywistym na głos z mikrofonu podczas nagrywania.
* **Analiza AI (LLM):** Automatyczne **strukturyzowanie tekstu**, wyciąganie **wniosków** i zadań (**To-Do**) przy użyciu modelu **Llama 3** (uruchamianego lokalnie przez **Ollama**).
* **Interaktywny Czat Kontekstowy:** Dedykowane okno konwersacyjne z Llama 3 pod wynikami, pozwalające zadawać pytania bezpośrednio do treści przetworzonego tekstu lub nagrania z zachowaniem pamięci kontekstu.
* **Wielofunkcyjny Eksport:** Możliwość niezależnego pobierania surowego tekstu transkrypcji oraz ustrukturyzowanej notatki AI do plików w formatach **TXT, Word (DOCX) oraz PDF**.
* **Dwu-kolumnowy Interfejs:** Czytelny, nowoczesny frontend w ciemnym stylu (**HTML/CSS/JS**) prezentujący **surowy tekst** po prawej stronie oraz **gotową notatkę AI** po lewej.

---

## **📦 Wymagania i Instalacja**

### **1. Klonowanie repozytorium i środowisko**
Klonujemy projekt, tworzymy wirtualne środowisko Pythona (**`venv`**) i je aktywujemy:

```bash
git clone [https://github.com/29Geishaa/projektSTT.git](https://github.com/29Geishaa/projektSTT.git)
cd projektSTT
python3 -m venv venv
source venv/bin/activate
```
**1.2 Na system Windows (Command Prompt / PowerShell):**
```
git clone [https://github.com/29Geishaa/projektSTT.git](https://github.com/29Geishaa/projektSTT.git)
cd projektSTT
python -m venv venv
```

**Jeśli używasz klasycznego CMD (Wiersz polecenia):**
```
venv\Scripts\activate
```
**Jeśli używasz PowerShell (może wymagać uruchomienia jako Administrator):**
```
.\venv\Scripts\Activate.ps1
```

**2. Instalacja zależności**
<br>Instalujemy wszystkie wymagane biblioteki Pythona zapisane w pliku konfiguracyjnym:

```Bash
pip install -r requirements.txt
```
**Ważna uwaga dla Windowsa: Aby lokalny model Whisper działał prawidłowo na procesorze (CPU) bez błędów kompilacji, na systemie Windows zaleca się najpierw zainstalować wersję procesorową PyTorcha bezpośrednio z oficjalnego repozytorium twórców, a dopiero potem resztę pakietów:**
```
Krok 1 (Tylko Windows - instalacja stabilnego Torch CPU):
pip install torch --index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)
```
```
Krok 2 (Wszystkie systemy - instalacja pozostałych bibliotek):
pip install -r requirements.txt
```
**2.1 Konfiguracja kluczy API w pliku `.env`**
<br>Tryb chmurowy korzysta z kluczy zapisanych w lokalnym pliku `.env`:

```env
GROQ_API_KEY=twoj_klucz_groq
OPENAI_API_KEY=twoj_klucz_openai
OPENAI_MODEL=gpt-5
# opcjonalnie osobny model dla formularza "Zapytaj AI" z web_search
OPENAI_WEB_SEARCH_MODEL=gpt-5
```

**3. Konfiguracja modeli AI (Ollama)
Upewnij się, że masz zainstalowaną aplikację Ollama oraz pobrany odpowiedni model językowy:
```Bash
ollama run llama3
```
 Uruchomienie Projektu
Odpal serwer deweloperski Flaska:

```Bash
python app.py
```
Aplikacja domyślnie zacznie działać lokalnie na porcie 8000 (http://127.0.0.1:8000). Jeśli port 8000 jest zajęty, serwer automatycznie wybierze kolejny wolny port.

Jeśli chcesz uruchomić aplikację bez ładowania lokalnych modeli Whisper, użyj:

```bash
python app.py --no-local-models
```

W tym trybie aplikacja działa w trybie chmurowym, a lokalne modele `tiny`, `base` i `small` nie są ładowane przy starcie.

### **Endpoint API dla YouTube**

Endpoint wymaga aktywnej sesji zalogowanego użytkownika i przyjmuje JSON:

```bash
curl -X POST http://127.0.0.1:8000/api/youtube/transcribe \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "yt_url": "https://www.youtube.com/watch?v=...",
    "settings": {
      "processing_mode": "offline",
      "model_name": "base",
      "language": "auto",
      "task": "transcribe",
      "save_to_history": false
    }
  }'
```

Odpowiedź zawiera m.in. pola `text`, `summary`, `language`, `model_used` oraz metadane filmu w polu `youtube`.

Lista modeli dostępnych w aplikacji:

```bash
curl http://127.0.0.1:8000/api/models
```

Endpoint zwraca osobno tablice `local` i `cloud` oraz wspólną tablicę `models`. Obsługuje filtry `?type=transcription`, `?type=chat` oraz `?include_disabled=true`.

 Przykładowy Scenariusz Testowy
Aby przetestować pełne możliwości systemu, zaloguj się, kliknij przycisk nagrywania i przeczytaj na głos poniższy tekst:

"Dobra, słuchajcie, musimy szybko ogarnąć plan na ten tydzień, bo gonią nas terminy. Przede wszystkim, Kasia musi do czwartku skończyć ten raport finansowy dla zarządu, bo bez tego nie ruszymy z budżetem. Janek, Ty miałeś pogadać z klientem i ustalić, czy odpowiada im ten nowy projekt graficzny – daj mi znać, jak tylko dostaniesz maila, najlepiej do jutra do piętnastej. No i ja zajmę się rezerwacją sali na piątkowe spotkanie podsumowujące. Ogólnie najważniejsze jest to, żebyśmy do końca miesiąca zamknęli ten etap projektu, bo inaczej naliczą nam kary. Czy ktoś ma jeszcze jakieś pytania? Jak nie, to bierzemy się do roboty."

Efekt: System Whisper przepisze słowo w słowo Twoją mowę, a Llama 3 automatycznie stworzy z tego czystą agendę z podziałem na zadania dla Kasi, Janka oraz Ciebie wraz z terminami.

### 💡 O czym jeszcze warto pamiętać przy wsparciu dla Windowsa?

1. **Wtyczka do obsługi audio (FFmpeg):** Lokalny model Whisper (z biblioteki `openai-whisper`) potrzebuje do działania programu `ffmpeg` do dekodowania plików audio. Na Linuxie instaluje się go jedną komendą, ale na Windowsie użytkownik musi pobrać pliki binarne FFmpeg, wrzucić je np. na dysk `C:\` i dodać ścieżkę do zmiennych środowiskowych systemowych (tzw. `PATH`). **Warto o tym wspomnieć użytkownikom**, jeśli zgłoszą, że lokalna transkrypcja rzuca błędem `FileNotFoundError: [WinError 2]`. (Dla trybu w chmurze Groq to nie jest wymagane!).
2. **Uprawnienia PowerShell:** Na Windowsie domyślnie zablokowane jest uruchamianie skryptów w PowerShellu (w tym aktywacja `venv`). Jeśli ktoś dostanie błąd `Script Execution Restriced`, musi jednorazowo wbić do PowerShella jako Administrator i wpisać: `Set-ExecutionPolicy RemoteSigned`.

Dzięki dodaniu tych ścieżek i instrukcji w pliku README Twój projekt stanie się w pełni **multiplatformowy** (Cross-platform) i każdy programista korzystający z Windowsa bez problemu go uruchomi! Zaktualizuj plik, zrób `git commit` i zsynchronizuj zmiany.

### **Miłego użytkowania :D**
