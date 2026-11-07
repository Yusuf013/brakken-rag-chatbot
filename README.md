# Brakken-assistent (prototype)

Een AI-assistent die praktische vragen van ouders beantwoordt op basis van de **openbare**
documenten op brakken.nl, met bronvermelding. Studentproject HBO-ICT.

## Hoe het werkt (RAG)

```
sources.json ──► ingest ──► stukken tekst + embeddings ──► data/index/
                                                              │
vraag van ouder ──► embedding ──► zoek 5 beste stukken ◄──────┘
                                        │
                     taalmodel (Mistral) + regels ──► kort antwoord + bronnen
```

| Bestand | Wat het doet |
|---|---|
| `sources.json` | Welke documenten de bot mag gebruiken |
| `app/ingest.py` | Downloadt, haalt tekst eruit, knipt op, maakt embeddings |
| `app/store.py` | Zoekt de stukken die het best bij de vraag passen |
| `app/rag.py` | Systeemprompt + antwoord met bronnen; "weet ik niet" bij lage score |
| `app/llm.py` | Praat met het taalmodel (wisselbaar via `.env`) |
| `app/main.py` | API (`POST /ask`) en demo-pagina |
| `tests/evaluate.py` | Draait de testvragen en meet kwaliteit en snelheid |

## Installeren

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # en zet je Mistral-sleutel in .env
```

## Gebruiken

```bash
python -m app.ingest               # documenten inladen (opnieuw draaien bij nieuwe documenten)
uvicorn app.main:app --reload      # start de server, open http://localhost:8000
python -m tests.evaluate           # testset draaien
```

## Van model wisselen

Pas in `.env` aan, bijvoorbeeld voor OpenAI:

```
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
CHAT_MODEL=gpt-4o-mini
EMBED_MODEL=text-embedding-3-small
```

Na het wisselen van **embedmodel** altijd opnieuw `python -m app.ingest` draaien.
Draai daarna `python -m tests.evaluate`; de resultaten worden per model opgeslagen,
zodat je modellen kunt vergelijken.

## Privacy-uitgangspunten

- Alleen openbare documenten van de website; geen leerling- of oudergegevens.
- Vragen van ouders worden niet opgeslagen of gelogd.
- De bot meldt dat hij AI is en toont altijd de bron.
- Gratis Mistral-plan alleen voor ontwikkelen met testvragen; voor echte gebruikers
  overstappen op betaald (betalen per gebruik), zodat data niet voor training wordt gebruikt.

## MIN_SCORE afstellen

`MIN_SCORE` in `.env` bepaalt wanneer de bot zegt "dat weet ik niet" zonder het model te vragen.
Kijk na een testrun naar de `score` per vraag: zet de grens net onder de scores van vragen
die wél beantwoord moeten worden en boven die van onzinvragen.
