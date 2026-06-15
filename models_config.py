import json
import os
import time

# ── Providers ─────────────────────────────────────────────────────────────────

PROVIDERS = {
    "groq": {
        "label": "Groq",
        "env_key": "GROQ_API_KEY"
    },
    "openai": {
        "label": "OpenAI",
        "env_key": "OPENAI_API_KEY"
    }
}

# ── Model types ───────────────────────────────────────────────────────────────

MODEL_TYPES = {
    "transcription": "Transkrypcja",
    "notes": "Notatki AI",
    "chat": "Czat z AI"
}

# ── Cloud model catalog ───────────────────────────────────────────────────────
# Env vars are resolved at import time; load_env_file() must be called first.

def _build_model_catalog():
    openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini').strip() or 'gpt-4o-mini'
    openai_web_search_model = os.getenv('OPENAI_WEB_SEARCH_MODEL', openai_model).strip() or openai_model
    return {
        "groq": {
            "transcription": [
                {"id": "whisper-large-v3", "label": "Whisper Large V3"},
                {"id": "whisper-large-v3-turbo", "label": "Whisper Large V3 Turbo"}
            ],
            "chat": [
                {"id": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B Versatile"},
                {"id": "llama-3.1-8b-instant", "label": "Llama 3.1 8B Instant"},
                {"id": "openai/gpt-oss-120b", "label": "GPT OSS 120B"},
                {"id": "openai/gpt-oss-20b", "label": "GPT OSS 20B"},
                {"id": "qwen/qwen3-32b", "label": "Qwen3 32B"},
                {"id": "meta-llama/llama-4-scout-17b-16e-instruct", "label": "Llama 4 Scout 17B 16E"}
            ]
        },
        "openai": {
            "transcription": [
                {"id": "whisper-1", "label": "STT Whisper 1"},
                {"id": "gpt-4o-mini-transcribe", "label": "GPT-4o mini transcribe"},
                {"id": "gpt-4o-transcribe", "label": "GPT-4o transcribe"},
                {"id": "gpt-4o-transcribe-diarize", "label": "GPT-4o transcribe diarize"}
            ],
            "chat": [
                {"id": openai_web_search_model, "label": f"{openai_web_search_model} (z .env)"},
                {"id": "gpt-5.5", "label": "GPT-5.5 - drogi model"},
            ],
            "notes": [
                {"id": openai_model, "label": f"{openai_model} (z .env)"},
                {"id": "gpt-4o-mini", "label": "GPT-4o mini"},
                {"id": "gpt-4o", "label": "GPT-4o"},
                {"id": "gpt-4.1-mini", "label": "GPT-4.1 mini"},
                {"id": "gpt-4.1", "label": "GPT-4.1"}
            ]
        }
    }

MODEL_CATALOG = _build_model_catalog()

# ── Default DB seed models ────────────────────────────────────────────────────

DEFAULT_AI_MODELS = [
    {
        "provider": "groq",
        "model_type": "transcription",
        "display_name": "Whisper Large V3",
        "model_id": "whisper-large-v3",
        "is_default": 1
    },
    {
        "provider": "groq",
        "model_type": "chat",
        "display_name": "Llama 3.3 70B Versatile",
        "model_id": "llama-3.3-70b-versatile",
        "is_default": 1
    },
    {
        "provider": "openai",
        "model_type": "transcription",
        "display_name": "Whisper-1 API - STT",
        "model_id": "whisper-1",
        "is_default": 1
    },
    {
        "provider": "openai",
        "model_type": "transcription",
        "display_name": "Whisper GPT-4o-mini-transcribe",
        "model_id": "gpt-4o-mini-transcribe",
        "is_default": 1
    },
    {
        "provider": "openai",
        "model_type": "notes",
        "display_name": "GPT-4o mini",
        "model_id": "gpt-4o-mini",
        "is_default": 1
    },
    {
        "provider": "openai",
        "model_type": "chat",
        "display_name": "GPT-5.4",
        "model_id": "gpt-5.4",
        "is_default": 1
    }
]

# ── Local model requirements ──────────────────────────────────────────────────

LOCAL_MODEL_REQUIREMENTS = [
    {
        "id": "whisper-tiny",
        "name": "Whisper Tiny",
        "category": "Transkrypcja lokalna",
        "engine": "openai-whisper",
        "summary": "Najszybszy lokalny model STT. Dobry do krótkich nagrań i słabszego sprzętu.",
        "resource_usage": {
            "uses_local_hardware": True,
            "summary": "Informacja pokazuje, jakie zasoby model potrafi wykorzystać w tej aplikacji. Nie jest to bieżący pomiar użycia.",
            "capabilities": [
                {"name": "CPU", "status": "Tak", "state": "yes", "detail": "Może wykonywać transkrypcję na procesorze."},
                {"name": "RAM", "status": "Tak", "state": "yes", "detail": "Wymagana do załadowania modelu i przetwarzania audio."},
                {"name": "Dysk", "status": "Tak", "state": "yes", "detail": "Używany na pliki modelu oraz pliki tymczasowe audio."},
                {"name": "GPU NVIDIA / CUDA", "status": "Może", "state": "optional", "detail": "Użyje GPU, jeśli PyTorch widzi CUDA i model zostanie załadowany na CUDA."},
                {"name": "Apple Metal / MPS", "status": "Nie w tej konfiguracji", "state": "no", "detail": "Ten kod nie wybiera urządzenia MPS dla Whisper."}
            ]
        },
        "libraries": ["openai-whisper", "torch", "numpy", "ffmpeg"],
        "drivers": [
            "CPU: brak dodatkowych sterowników poza FFmpeg.",
            "GPU NVIDIA: opcjonalnie sterownik NVIDIA oraz CUDA zgodne z używaną wersją PyTorch."
        ],
        "hardware": {
            "RAM": "ok. 1 GB wolnej pamięci",
            "VRAM": "opcjonalnie ok. 1 GB",
            "Dysk": "ok. 75 MB na model",
            "CPU": "dowolny nowoczesny CPU; działa wolniej bez GPU"
        },
        "notes": ["Najmniejsze zużycie zasobów.", "Niższa dokładność niż Base i Small."]
    },
    {
        "id": "whisper-base",
        "name": "Whisper Base",
        "category": "Transkrypcja lokalna",
        "engine": "openai-whisper",
        "summary": "Domyślny kompromis między szybkością i jakością lokalnej transkrypcji.",
        "resource_usage": {
            "uses_local_hardware": True,
            "summary": "Informacja pokazuje, jakie zasoby model potrafi wykorzystać w tej aplikacji. Nie jest to bieżący pomiar użycia.",
            "capabilities": [
                {"name": "CPU", "status": "Tak", "state": "yes", "detail": "Może wykonywać transkrypcję na procesorze."},
                {"name": "RAM", "status": "Tak", "state": "yes", "detail": "Wymagana do załadowania modelu i przetwarzania audio."},
                {"name": "Dysk", "status": "Tak", "state": "yes", "detail": "Używany na pliki modelu oraz pliki tymczasowe audio."},
                {"name": "GPU NVIDIA / CUDA", "status": "Może", "state": "optional", "detail": "Użyje GPU, jeśli PyTorch widzi CUDA i model zostanie załadowany na CUDA."},
                {"name": "Apple Metal / MPS", "status": "Nie w tej konfiguracji", "state": "no", "detail": "Ten kod nie wybiera urządzenia MPS dla Whisper."}
            ]
        },
        "libraries": ["openai-whisper", "torch", "numpy", "ffmpeg"],
        "drivers": [
            "CPU: brak dodatkowych sterowników poza FFmpeg.",
            "GPU NVIDIA: opcjonalnie sterownik NVIDIA oraz CUDA zgodne z używaną wersją PyTorch."
        ],
        "hardware": {
            "RAM": "ok. 1-2 GB wolnej pamięci",
            "VRAM": "opcjonalnie ok. 1 GB",
            "Dysk": "ok. 150 MB na model",
            "CPU": "zalecany wielordzeniowy CPU"
        },
        "notes": ["Najbezpieczniejszy wybór dla większości nagrań.", "W aplikacji jest ustawiony jako model zrównoważony."]
    },
    {
        "id": "whisper-small",
        "name": "Whisper Small",
        "category": "Transkrypcja lokalna",
        "engine": "openai-whisper",
        "summary": "Dokładniejszy lokalny model STT, ale wolniejszy i bardziej wymagający.",
        "resource_usage": {
            "uses_local_hardware": True,
            "summary": "Informacja pokazuje, jakie zasoby model potrafi wykorzystać w tej aplikacji. Nie jest to bieżący pomiar użycia.",
            "capabilities": [
                {"name": "CPU", "status": "Tak", "state": "yes", "detail": "Może wykonywać transkrypcję na procesorze."},
                {"name": "RAM", "status": "Tak", "state": "yes", "detail": "Wymagana do załadowania modelu i przetwarzania audio."},
                {"name": "Dysk", "status": "Tak", "state": "yes", "detail": "Używany na pliki modelu oraz pliki tymczasowe audio."},
                {"name": "GPU NVIDIA / CUDA", "status": "Może", "state": "optional", "detail": "Użyje GPU, jeśli PyTorch widzi CUDA i model zostanie załadowany na CUDA."},
                {"name": "Apple Metal / MPS", "status": "Nie w tej konfiguracji", "state": "no", "detail": "Ten kod nie wybiera urządzenia MPS dla Whisper."}
            ]
        },
        "libraries": ["openai-whisper", "torch", "numpy", "ffmpeg"],
        "drivers": [
            "CPU: brak dodatkowych sterowników poza FFmpeg.",
            "GPU NVIDIA: opcjonalnie sterownik NVIDIA oraz CUDA zgodne z używaną wersją PyTorch."
        ],
        "hardware": {
            "RAM": "ok. 2-4 GB wolnej pamięci",
            "VRAM": "opcjonalnie ok. 2 GB",
            "Dysk": "ok. 500 MB na model",
            "CPU": "zalecany szybszy wielordzeniowy CPU"
        },
        "notes": ["Lepsza jakość dla trudniejszego audio.", "Na CPU może działać zauważalnie wolniej."]
    },
    {
        "id": "ollama-llama3",
        "name": "Llama 3 przez Ollama",
        "category": "Lokalne notatki i czat AI",
        "engine": "ollama",
        "summary": "Lokalny model językowy używany do generowania notatek i odpowiedzi w czacie.",
        "resource_usage": {
            "uses_local_hardware": True,
            "summary": "Informacja pokazuje, jakie zasoby Ollama potrafi wykorzystać. Nie jest to bieżący pomiar użycia.",
            "capabilities": [
                {"name": "CPU", "status": "Tak", "state": "yes", "detail": "Może generować odpowiedzi na procesorze."},
                {"name": "RAM", "status": "Tak", "state": "yes", "detail": "Wymagana do utrzymania modelu w pamięci."},
                {"name": "Dysk", "status": "Tak", "state": "yes", "detail": "Używany na pobrany model Ollama."},
                {"name": "GPU NVIDIA / CUDA", "status": "Może", "state": "optional", "detail": "Może użyć, jeśli Ollama i sterownik NVIDIA wspierają akcelerację."},
                {"name": "Apple Metal", "status": "Może", "state": "optional", "detail": "Może użyć na wspieranym macOS i sprzęcie Apple."},
                {"name": "AMD / ROCm", "status": "Może", "state": "optional", "detail": "Zależy od systemu, sterownika i wariantu Ollama."}
            ]
        },
        "libraries": ["ollama", "model llama3 pobrany przez `ollama run llama3`"],
        "drivers": [
            "CPU: działa bez dodatkowych sterowników GPU.",
            "GPU NVIDIA: opcjonalnie aktualny sterownik NVIDIA obsługiwany przez Ollama.",
            "macOS: Ollama może korzystać z Metal na wspieranym sprzęcie Apple."
        ],
        "hardware": {
            "RAM": "minimum ok. 8 GB, zalecane 16 GB",
            "VRAM": "opcjonalnie 4-8 GB zależnie od wariantu modelu",
            "Dysk": "kilka GB na pobrany model",
            "CPU": "zalecany wielordzeniowy CPU"
        },
        "notes": ["Wymaga uruchomionej usługi Ollama.", "Jeśli Ollama nie działa, aplikacja zwróci komunikat o braku lokalnych notatek AI."]
    }
]

# ── Model pricing (USD per 1 million tokens) ─────────────────────────────────
# input / output prices; audio-only models (whisper-*) billed per minute – omitted here.

MODEL_PRICING = {
    # OpenAI text models
    "gpt-4o-mini":            {"input": 0.15,  "output": 0.60},
    "gpt-4o":                 {"input": 2.50,  "output": 10.00},
    "gpt-4o-search-preview":  {"input": 2.50,  "output": 10.00},
    "gpt-4.1":                {"input": 2.00,  "output": 8.00},
    "gpt-4.1-mini":           {"input": 0.40,  "output": 1.60},
    "gpt-4.1-nano":           {"input": 0.10,  "output": 0.40},
    "gpt-5":                  {"input": 3.00,  "output": 15.00},
    "gpt-5.4":                {"input": 3.00,  "output": 15.00},
    "gpt-5.5":                {"input": 5.00,  "output": 25.00},
    # OpenAI transcription models (token-based billing)
    "gpt-4o-transcribe":      {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini-transcribe": {"input": 0.15,  "output": 0.60},
    # Groq text models
    "llama-3.3-70b-versatile":                    {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant":                       {"input": 0.05, "output": 0.08},
    "openai/gpt-oss-120b":                        {"input": 0.90, "output": 0.90},
    "openai/gpt-oss-20b":                         {"input": 0.60, "output": 0.60},
    "qwen/qwen3-32b":                             {"input": 0.29, "output": 0.59},
    "meta-llama/llama-4-scout-17b-16e-instruct":  {"input": 0.11, "output": 0.34},
}

# Audio transcription pricing (USD per minute) — for models billed by duration, not tokens.
AUDIO_PRICING = {
    # OpenAI
    "whisper-1":                       0.006,
    # Groq (converted from per-hour rates)
    "whisper-large-v3":                0.111 / 60,
    "distil-whisper-large-v3-en":      0.020 / 60,
    "whisper-large-v3-turbo":          0.04  / 60,
}

def resolve_pricing_key(model_name):
    """Return the MODEL_PRICING key matching model_name (exact, then longest prefix)."""
    if not model_name:
        return None
    if model_name in MODEL_PRICING:
        return model_name
    best = None
    for key in MODEL_PRICING:
        if model_name.startswith(key) and (best is None or len(key) > len(best)):
            best = key
    return best


def get_audio_duration_seconds(file_path):
    """Return audio duration in seconds via ffprobe, or None on failure."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return None

def get_audio_cost(model_name, seconds):
    """Return USD cost for duration-billed audio transcription."""
    if not model_name or not seconds:
        return 0.0
    if model_name in AUDIO_PRICING:
        return seconds / 60.0 * AUDIO_PRICING[model_name]
    for key in AUDIO_PRICING:
        if model_name.startswith(key):
            return seconds / 60.0 * AUDIO_PRICING[key]
    return 0.0


# ── Pricing overrides (pricing_data.json) ────────────────────────────────────

PRICING_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pricing_data.json')

def load_pricing_data():
    """Return (prices_dict, last_updated_timestamp) from pricing_data.json."""
    if not os.path.exists(PRICING_DATA_FILE):
        return {}, None
    try:
        with open(PRICING_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('prices', {}), data.get('last_updated')
    except Exception:
        return {}, None

def save_pricing_data(prices, timestamp=None):
    """Write pricing overrides + timestamp to pricing_data.json."""
    if timestamp is None:
        timestamp = time.time()
    with open(PRICING_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({'last_updated': timestamp, 'prices': prices}, f, indent=2)

def get_effective_model_pricing():
    """Return MODEL_PRICING merged with any stored overrides from pricing_data.json."""
    overrides, _ = load_pricing_data()
    if not overrides:
        return MODEL_PRICING
    result = dict(MODEL_PRICING)
    result.update(overrides)
    return result


# ── Provider helpers ──────────────────────────────────────────────────────────

def get_provider_label(provider):
    return PROVIDERS.get(provider, {}).get("label", provider)

def get_provider_api_key(provider):
    env_key = PROVIDERS.get(provider, {}).get("env_key")
    if not env_key:
        return ""
    return os.getenv(env_key, "").strip()

def get_provider_env_key(provider):
    return PROVIDERS.get(provider, {}).get("env_key", "API_KEY")

def require_provider_api_key(provider):
    api_key = get_provider_api_key(provider)
    if not api_key:
        env_key = get_provider_env_key(provider)
        raise RuntimeError(f"Brak klucza {env_key} w pliku .env")
    return api_key

def raise_invalid_api_key_error(provider):
    env_key = get_provider_env_key(provider)
    provider_label = get_provider_label(provider)
    raise RuntimeError(f"Nieprawidłowy klucz {env_key} dla {provider_label}. Sprawdź wartość w pliku .env.")

def raise_provider_api_error(provider, error):
    message = str(error)
    normalized = message.lower()
    if "invalid_api_key" in normalized or "invalid api key" in normalized or "401" in normalized:
        raise_invalid_api_key_error(provider)
    raise RuntimeError(f"Błąd API {get_provider_label(provider)}: {message}")

# ── Model description helpers ─────────────────────────────────────────────────

def describe_cloud_model(model_config):
    if not model_config:
        return "Brak modelu"
    return f"{model_config['provider_label']} ({model_config['display_name']})"

def describe_local_notes_model():
    return "Ollama (Llama 3)"

def describe_notes_model(model_config=None, processing_mode=None):
    if model_config:
        return describe_cloud_model(model_config)
    if processing_mode == "online":
        return "Brak modelu notatek"
    return describe_local_notes_model()

def describe_chat_answer_model(model_config):
    label = describe_cloud_model(model_config)
    if model_config and model_config.get("provider") == "openai":
        return f"{label} + web_search"
    return label
