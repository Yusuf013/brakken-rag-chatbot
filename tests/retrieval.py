"""Meet alleen het ZOEKEN (de R van RAG), los van het taalmodel.

Gebruik:  python -m tests.retrieval            (overzicht)
          python -m tests.retrieval --toon     (ook de gevonden stukken per vraag)

Per testvraag kijkt dit script welke stukken tekst het zoekmodel vindt en meet het:
- Gevonden:   staat het verwachte antwoord (een trefwoord uit vragen.json) in de gevonden stukken?
              Zo niet, dan kan zelfs het beste taalmodel het niet goed beantwoorden.
- Vervuiling: komen er bij een schoolvraag stukken over de opvang mee?
- Score:      hoe goed het beste stuk bij de vraag past (0-1).

Draai dit vóór en na een verbetering, en vergelijk.
"""
import json
import re
import sys
import time
from pathlib import Path

from app import config, i18n, llm, rag, store

OPVANG_WORDS = re.compile(
    r"\b(bso|kdv|psg|kinderopvang|kinderdagverblijf|peuterspeelgroep|buitenschoolse|"
    r"naschoolse opvang|voorschoolse opvang|harlekijn|18[.:]30|07[.:]30)\b",
    re.I,
)
SKIP = {"grens", "weigeren", "tegenstrijdig"}


def looks_like_opvang(chunk: dict) -> bool:
    if chunk.get("domain"):
        return chunk["domain"] == "opvang"
    return len(OPVANG_WORDS.findall(chunk["text"])) >= 2


def search(question: str) -> tuple[str, list[dict]]:
    lang = i18n.resolve(question, None)
    query = rag._search_query(question, lang)
    vector = llm.embed([query])[0]
    route = getattr(rag, "route", None)          # bestaat pas na stap 2 (labels)
    if route:
        domains = route(question)
        return ",".join(sorted(domains)), store.search(vector, k=config.TOP_K, domains=domains)
    return "-", store.search(vector, k=config.TOP_K)


def main() -> None:
    show = "--toon" in sys.argv
    items = json.loads((Path(__file__).parent / "vragen.json").read_text(encoding="utf-8"))
    rows = []
    print(f"Zoekmodel: {config.EMBED_MODEL}  |  TOP_K: {config.TOP_K}\n")

    for item in items:
        if item["soort"] in SKIP or item["soort"] == "opvang":
            continue
        start = time.perf_counter()
        domains, hits = search(item["vraag"])
        seconds = time.perf_counter() - start

        context = " ".join(h["text"] for h in hits).lower()
        if item["verwacht"]:
            found = any(v.lower() in context for v in item["verwacht"])
            label = "JA " if found else "NEE"
        else:
            found, label = None, " ? "
        opvang = sum(looks_like_opvang(h) for h in hits)
        top = hits[0]["score"] if hits else 0.0

        rows.append({"vraag": item["vraag"], "gevonden": found, "opvang_stukken": opvang,
                     "top_score": round(top, 3), "domein": domains,
                     "stukken": [{"titel": h["title"], "pagina": h.get("page"),
                                  "score": round(h["score"], 3), "opvang": looks_like_opvang(h)}
                                 for h in hits]})
        warn = f"  ! {opvang} opvang" if opvang else ""
        print(f"[{label}] score {top:.2f}  {seconds:4.1f}s  {item['vraag']}{warn}")
        if show:
            for h in hits:
                tag = "OPVANG" if looks_like_opvang(h) else "school"
                page = f" p.{h['page']}" if h.get("page") else ""
                snippet = " ".join(h["text"].split())[:110]
                print(f"        {h['score']:.2f} [{tag}] {h['title']}{page}: {snippet}")
            print()

    scored = [r for r in rows if r["gevonden"] is not None]
    hit = sum(r["gevonden"] for r in scored)
    polluted = sum(r["opvang_stukken"] > 0 for r in rows)
    print(f"\nAntwoord in gevonden stukken: {hit}/{len(scored)}")
    print(f"Vragen met opvangstukken erbij: {polluted}/{len(rows)}")
    print(f"Gemiddelde beste score: {sum(r['top_score'] for r in rows) / len(rows):.2f}")

    out = Path(__file__).parent / f"retrieval-{time.strftime('%Y%m%d-%H%M')}.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Details opgeslagen in {out.name}")


if __name__ == "__main__":
    main()
