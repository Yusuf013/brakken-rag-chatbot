"""Instellingen uit .env, op één plek, zodat je van model of aanbieder wisselt zonder code te veranderen."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.mistral.ai/v1").rstrip("/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "mistral-small-latest")
EMBED_MODEL = os.getenv("EMBED_MODEL", "mistral-embed")

# Het zoekmodel (embeddings) mag bij een andere aanbieder draaien dan het taalmodel,
# bijv. Gemini voor antwoorden en bge-m3 lokaal via Ollama voor zoeken.
# Niet ingevuld = dezelfde aanbieder als het taalmodel.
EMBED_BASE_URL = os.getenv("EMBED_BASE_URL", LLM_BASE_URL).rstrip("/")
EMBED_API_KEY = os.getenv("EMBED_API_KEY", LLM_API_KEY)

# Optioneel: hoeveel het model "nadenkt" (none, low, medium, high). Leeg = standaard van het model.
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "").strip()

# Pauze in seconden tussen testvragen, voor gratis plannen met een limiet per minuut
EVAL_DELAY = float(os.getenv("EVAL_DELAY", "0"))

TOP_K = int(os.getenv("TOP_K", "5"))
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.45"))
SCHOOL_CONTACT = os.getenv("SCHOOL_CONTACT", "info@brakken.nl")

SOURCES_FILE = ROOT / "sources.json"
CACHE_DIR = ROOT / "data" / "cache"   # gedownloade documenten
INDEX_DIR = ROOT / "data" / "index"   # stukken tekst + embeddings

# Opknippen: lengte van een stuk tekst en overlap tussen stukken (in tekens)
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
