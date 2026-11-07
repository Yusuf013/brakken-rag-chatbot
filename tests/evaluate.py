"""Test de assistent met een vaste set vragen en meet kwaliteit en snelheid.

Gebruik:  python -m tests.evaluate
Draai dit na elke wijziging (andere prompt, ander model, nieuwe documenten) en vergelijk.

Dit is een simpele, automatische eerste check op trefwoorden. Lees de antwoorden ook zelf na:
in je verslag telt jouw beoordeling ("goed / deels / fout") het zwaarst.
"""
import json
import time
from pathlib import Path

from app import config, rag

REFUSAL_HINTS = ["niet vinden", "weet ik niet", "contact op", "kan ik niet", "niet in de informatie",
                 config.SCHOOL_CONTACT]


def check(item: dict, answer: str) -> str:
    """OK = een verwacht trefwoord staat erin én geen enkel verboden trefwoord."""
    text = answer.lower()
    if any(w.lower() in text for w in item.get("niet_verwacht", [])):
        return "FOUT"
    if item["soort"] == "weigeren":
        return "OK" if any(h.lower() in text for h in REFUSAL_HINTS) else "FOUT"
    if not item["verwacht"]:
        return "HANDMATIG"
    return "OK" if any(v.lower() in text for v in item["verwacht"]) else "FOUT"


def main() -> None:
    items = json.loads((Path(__file__).parent / "vragen.json").read_text(encoding="utf-8"))
    results, durations = [], []
    print(f"Model: {config.CHAT_MODEL}  |  embeddings: {config.EMBED_MODEL}\n")

    for n, item in enumerate(items):
        if n and config.EVAL_DELAY:
            time.sleep(config.EVAL_DELAY)   # tussen vragen, telt niet mee in de antwoordtijd
        start = time.perf_counter()
        try:
            out = rag.answer(item["vraag"])
            answer, nsrc = out["answer"], len(out["sources"])
            score = out["top_score"] if out["top_score"] is not None else -1.0  # -1 = harde regel
        except Exception as exc:
            answer, nsrc, score = f"[fout: {exc}]", 0, 0.0
        seconds = time.perf_counter() - start
        durations.append(seconds)
        verdict = check(item, answer)
        results.append({**item, "antwoord": answer, "oordeel": verdict, "bronnen": nsrc,
                        "score": round(score, 3), "seconden": round(seconds, 2)})
        label = "regel" if score < 0 else f"{score:.2f}"
        print(f"[{verdict:9}] {seconds:4.1f}s  score {label:5}  {item['vraag']}")
        print(f"            -> {answer[:160]}\n")

    ok = sum(r["oordeel"] == "OK" for r in results)
    auto = sum(r["oordeel"] in ("OK", "FOUT") for r in results)
    print(f"Automatisch goed: {ok}/{auto}  |  handmatig te beoordelen: {len(results) - auto}")
    print(f"Gemiddelde antwoordtijd: {sum(durations) / len(durations):.1f}s")

    safe_name = config.CHAT_MODEL.replace("/", "-").replace(":", "-")
    out_file = Path(__file__).parent / f"resultaten-{safe_name}.json"
    out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Alle antwoorden opgeslagen in {out_file.name}")


if __name__ == "__main__":
    main()
