"""Stap 1 van RAG: documenten ophalen, tekst eruit halen, opknippen en doorzoekbaar maken.

Gebruik:  python -m app.ingest
Draai dit opnieuw zodra er documenten bijkomen of veranderen (bijv. elke week).
"""
import hashlib
import io
import json
import re

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app import config, llm, store


def download(url: str) -> bytes:
    """Download een bestand, met een lokale kopie zodat je niet steeds opnieuw downloadt."""
    config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = config.CACHE_DIR / hashlib.sha1(url.encode()).hexdigest()
    if cache_file.exists():
        return cache_file.read_bytes()
    resp = requests.get(url, timeout=60, headers={"User-Agent": "brakken-assistent (studentproject)"})
    resp.raise_for_status()
    cache_file.write_bytes(resp.content)
    return resp.content


def pdf_pages(content: bytes) -> list[tuple[int, str]]:
    """Geeft (paginanummer, tekst) per pagina terug."""
    reader = PdfReader(io.BytesIO(content))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((i, text))
    return pages


def html_text(content: bytes) -> str:
    """Haalt de leesbare tekst uit een webpagina, zonder menu, footer en scripts."""
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "form", "svg"]):
        tag.decompose()
    # Elementor (WordPress) zet menu en footer soms in gewone div's
    for tag in soup.select(".elementor-location-header, .elementor-location-footer"):
        tag.decompose()
    main = soup.find("main") or soup.body or soup
    return main.get_text(separator="\n")


def clean(text: str) -> str:
    text = text.replace("­", "")              # zachte afbreekstreepjes uit pdf's
    text = re.sub(r"-\n(\w)", r"\1", text)          # woorden die over een regel zijn afgebroken
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def chunk(text: str, size: int = config.CHUNK_SIZE, overlap: int = config.CHUNK_OVERLAP) -> list[str]:
    """Knipt tekst in stukken van ongeveer `size` tekens, bij voorkeur op alinea-grenzen.

    De overlap zorgt dat een antwoord dat precies op een grens valt niet verloren gaat.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) + 1 <= size:
            current = f"{current}\n{p}" if current else p
            continue
        if current:
            chunks.append(current)
            current = current[-overlap:] + "\n" + p if overlap else p
        else:
            current = p
        # een heel lange alinea hard opknippen
        while len(current) > size:
            chunks.append(current[:size])
            current = current[size - overlap :]
    if current.strip():
        chunks.append(current)
    return chunks


def build_chunks(source: dict) -> list[dict]:
    content = download(source["url"])
    if source["type"] == "pdf":
        parts = pdf_pages(content)
    else:
        parts = [(None, html_text(content))]

    out = []
    for page, text in parts:
        for piece in chunk(clean(text)):
            out.append({
                "title": source["title"],
                "url": source["url"],
                "page": page,
                "text": piece,
            })
    return out


def main() -> None:
    sources = json.loads(config.SOURCES_FILE.read_text(encoding="utf-8"))
    all_chunks: list[dict] = []
    for source in sources:
        try:
            chunks = build_chunks(source)
        except Exception as exc:  # één kapot document mag de rest niet tegenhouden
            print(f"  ! Overgeslagen: {source['title']} ({exc})")
            continue
        print(f"  {source['title']}: {len(chunks)} stukken")
        all_chunks.extend(chunks)

    if not all_chunks:
        raise SystemExit("Geen tekst gevonden. Controleer sources.json en je internetverbinding.")

    # De titel meesturen helpt het zoeken: "Jaarkalender: 23 december vrij" vindt je makkelijker terug.
    texts = [f"{c['title']}\n{c['text']}" for c in all_chunks]
    print(f"Embeddings maken voor {len(texts)} stukken...")
    vectors = llm.embed(texts)
    store.save(all_chunks, vectors)
    print(f"Klaar. Index opgeslagen in {config.INDEX_DIR}")


if __name__ == "__main__":
    main()
