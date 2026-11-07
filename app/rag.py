"""Stap 3 van RAG: de gevonden stukken + de vraag naar het taalmodel, antwoord met bronnen terug."""
import re

from app import config, guardrails, i18n, llm, store

SYSTEM_PROMPT = """Je bent de digitale assistent van basisschool De Brakken. Je helpt ouders \
snel praktische informatie te vinden.

Regels:
- Beantwoord de vraag ALLEEN met informatie die letterlijk in de bronnen staat. Verzin niets en \
voeg geen eigen advies, redenen of voorbeelden toe.
- Staat het antwoord niet in de bronnen? Zeg dat eerlijk en verwijs naar de school: {contact}.
- Antwoord kort (maximaal 3 zinnen), vriendelijk en in eenvoudige taal.
- Zet na elke bewering het nummer van de bron, bijvoorbeeld [1] of [2].
- Is de vraag een ja/nee-vraag? Begin met "Ja" of "Nee" en zorg dat de rest van je antwoord daarmee klopt.
- Gelden regels alleen voor bepaalde groepen (bijvoorbeeld groep 1-4)? Noem dat erbij.
- Gebruik niets uit de bronnen over kinderopvang, BSO of peuterspeelgroep.
- Noem nooit namen, telefoonnummers of e-mailadressen van personen, tenzij de vraag precies naar \
die functie vraagt (bijvoorbeeld "wie is de schoolmaatschappelijk werker?").
- Iets aanvragen of doorgeven (verlof, ziekmelding, absentie, oudergesprek) doen ouders via \
Social Schools. Verwijs daarnaar.
- Antwoord in de taal die aan het eind van het bericht wordt gevraagd. Veel ouders spreken weinig \
Nederlands: gebruik korte zinnen en eenvoudige woorden."""

# Kleine modellen volgen regels aan het eind van het bericht beter dan regels bovenaan.
REMINDER = ("Onthoud: alleen informatie uit de bronnen, maximaal 3 zinnen, bronnummers erbij. "
            "{language}")

TRANSLATE_PROMPT = ("Translate this question from a parent into Dutch. "
                    "Reply with only the translation, nothing else.\n\n{question}")


def _search_query(question: str, lang: str) -> str:
    """De documenten zijn Nederlands. Een vraag in een andere taal vertalen we eerst,
    zodat het zoeken net zo goed werkt als bij een Nederlandse vraag."""
    if lang == "nl":
        return question
    try:
        return llm.chat([{"role": "user", "content": TRANSLATE_PROMPT.format(question=question)}], temperature=0)
    except llm.LLMError:
        return question  # dan zoeken we gewoon met de originele vraag


def _format_context(hits: list[dict]) -> str:
    blocks = []
    for n, hit in enumerate(hits, start=1):
        where = f"{hit['title']}" + (f", pagina {hit['page']}" if hit.get("page") else "")
        blocks.append(f"[{n}] ({where})\n{hit['text']}")
    return "\n\n".join(blocks)


def _cited_sources(answer: str, hits: list[dict]) -> list[dict]:
    """Geeft alleen de bronnen terug die het model echt noemt, zonder dubbele."""
    seen, sources = set(), []
    for num in re.findall(r"\[(\d+)\]", answer):
        i = int(num) - 1
        if not 0 <= i < len(hits):
            continue
        hit = hits[i]
        key = (hit["url"], hit.get("page"))
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "nr": i + 1,
            "title": hit["title"],
            "url": hit["url"] + (f"#page={hit['page']}" if hit.get("page") else ""),
            "page": hit.get("page"),
        })
    return sources


def answer(question: str, language: str | None = None) -> dict:
    question = question.strip()
    lang = i18n.resolve(question, language)

    fixed = guardrails.check(question, lang)
    if fixed:
        return {"answer": fixed, "sources": [], "top_score": None, "guardrail": True, "language": lang}

    query = _search_query(question, lang)
    query_vector = llm.embed([query])[0]
    hits = store.search(query_vector, k=config.TOP_K)

    top_score = hits[0]["score"] if hits else 0.0
    if top_score < config.MIN_SCORE:
        # Niets relevants gevonden: niet het model laten gokken.
        return {"answer": i18n.text("fallback", lang, contact=config.SCHOOL_CONTACT),
                "sources": [], "top_score": top_score, "language": lang}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(contact=config.SCHOOL_CONTACT)},
        {"role": "user", "content": (
            f"Bronnen:\n\n{_format_context(hits)}\n\n"
            f"Vraag van een ouder: {question}\n\n"
            + REMINDER.format(language=i18n.instruction(lang))
        )},
    ]
    text = llm.chat(messages)
    return {"answer": text, "sources": _cited_sources(text, hits), "top_score": top_score, "language": lang}
