
"""De API en de demo-pagina.

Starten: uvicorn app.main:app --reload
Open dan http://localhost:8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import config, rag
from app.llm import LLMError


app = FastAPI(
    title="Brakken-assistent",
    version="0.1"
)

# CORS: sta verzoeken toe vanaf de lokale WordPress-website
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8881",
        "http://127.0.0.1:8881",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.mount(
    "/static",
    StaticFiles(directory=config.ROOT / "static"),
    name="static"
)


class Question(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    language: str = "auto"


@app.get("/")
def index():
    return FileResponse(
        config.ROOT / "static" / "index.html"
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": config.CHAT_MODEL
    }


@app.post("/ask")
def ask(q: Question):
    # Geen logging van vragen vanwege privacy.
    try:
        return rag.answer(q.question, q.language)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc)
        )

    except LLMError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        )
