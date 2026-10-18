"""Servidor web do ChargeGrid Intelligence: API (FastAPI) + frontend HTML/CSS/JS puro.

    python app/web_server.py          # abre em http://127.0.0.1:8000

O frontend fica em app/web/ (index.html, style.css, app.js) e fala com a API:

    GET  /api/config   configuracao, versoes de prompt e estado da base
    POST /api/chat     pergunta -> resposta(s) com fontes e trechos recuperados
    GET  /api/health   200 quando o indice esta pronto

Variaveis opcionais: WEB_HOST (padrao 127.0.0.1), WEB_PORT (padrao 8000).
O servidor e sem estado: o navegador envia o historico curto a cada pergunta.
"""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from rag import config, prompt_rag  # noqa: E402
from rag.llm import PROVEDORES  # noqa: E402
from rag.pipeline import RagPipeline, abrir_pipeline  # noqa: E402
from rag.vector_store import ler_manifesto  # noqa: E402

WEB_DIR = Path(__file__).resolve().parent / "web"

app = FastAPI(title="ChargeGrid Intelligence", docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json")

_lock = threading.Lock()
_estado: dict = {"pipeline": None, "erro": None}


def obter_pipeline() -> RagPipeline:
    """Abre o pipeline na primeira chamada e tenta de novo se o indice ainda nao existia
    (assim o usuario roda `scripts/ingest.py` sem precisar reiniciar o servidor)."""
    with _lock:
        if _estado["pipeline"] is None:
            try:
                _estado["pipeline"] = abrir_pipeline()
                _estado["erro"] = None
            except Exception as exc:  # noqa: BLE001
                _estado["erro"] = f"{type(exc).__name__}: {exc}"
    if _estado["pipeline"] is None:
        raise HTTPException(status_code=503, detail=_estado["erro"] or "Pipeline indisponivel.")
    return _estado["pipeline"]


class Turno(BaseModel):
    pergunta: str = Field(max_length=1000)
    resposta: str = Field(max_length=4000)


class Variante(BaseModel):
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None


class ChatIn(BaseModel):
    pergunta: str = Field(min_length=1, max_length=1000)
    historico: list[Turno] = Field(default_factory=list, max_length=6)
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    k: int | None = Field(default=None, ge=1, le=10)
    min_score: float | None = Field(default=None, ge=0, le=1)
    temperature: float | None = Field(default=None, ge=0, le=1)
    top_p: float | None = Field(default=None, gt=0, le=1)
    max_tokens: int | None = Field(default=None, ge=64, le=4096)
    variantes: list[Variante] | None = Field(default=None, max_length=3)


def _validar(provider: str | None, versao: str | None) -> None:
    if provider is not None and provider not in PROVEDORES:
        raise HTTPException(400, f"Provedor invalido: {provider!r}. Opcoes: {', '.join(PROVEDORES)}")
    if versao is not None and versao not in prompt_rag.PROMPTS:
        raise HTTPException(400, f"Versao de prompt invalida: {versao!r}. Opcoes: {prompt_rag.versoes()}")


@app.get("/api/health")
def health():
    obter_pipeline()
    return {"status": "ok"}


@app.get("/api/config")
def configuracao():
    pronto = _estado["pipeline"] is not None
    erro = _estado["erro"]
    if not pronto:
        try:
            obter_pipeline()
            pronto, erro = True, None
        except HTTPException as exc:
            erro = str(exc.detail)

    cfg = config.chunking_padrao()
    manifesto = ler_manifesto(config.persist_dir(), config.nome_colecao(cfg))
    return {
        "pronto": pronto,
        "erro": erro,
        "providers": list(PROVEDORES),
        "prompts": [{"id": v, "descricao": prompt_rag.PROMPTS[v]["descricao"]} for v in prompt_rag.versoes()],
        "padroes": {
            "provider": config.llm_provider(),
            "model": config.llm_model(),
            "model_b": os.getenv("OLLAMA_MODEL_2", "gpt-oss:20b-cloud"),
            "prompt_version": config.prompt_version(),
            "k": config.top_k(),
            "min_score": config.min_score(),
            "temperature": config.llm_temperature(),
            "top_p": config.llm_top_p(),
            "max_tokens": config.llm_max_tokens(),
        },
        "base": None if not manifesto else {
            "documentos": manifesto["documentos"],
            "chunks": manifesto["chunks_na_colecao"],
            "chunking": manifesto["chunking"],
        },
    }


@app.post("/api/chat")
def chat(corpo: ChatIn):
    _validar(corpo.provider, corpo.prompt_version)
    pipeline = obter_pipeline()
    historico = [t.model_dump() for t in corpo.historico]
    k = corpo.k or pipeline.retriever.k
    min_score = pipeline.retriever.min_score if corpo.min_score is None else corpo.min_score

    if corpo.variantes:
        for v in corpo.variantes:
            _validar(v.provider, v.prompt_version)
        base = {
            "temperature": corpo.temperature if corpo.temperature is not None else pipeline.temperature,
            "top_p": corpo.top_p if corpo.top_p is not None else pipeline.top_p,
            "max_tokens": corpo.max_tokens or pipeline.max_tokens,
        }
        variantes = [{**{k_: v_ for k_, v_ in v.model_dump().items() if v_ is not None}, **base}
                     for v in corpo.variantes]
        respostas = pipeline.responder_multi(corpo.pergunta, variantes, historico, k=k, min_score=min_score)
    else:
        respostas = [pipeline.responder(
            corpo.pergunta, historico, provider=corpo.provider, model=corpo.model,
            prompt_version=corpo.prompt_version, k=k, min_score=min_score,
            temperature=corpo.temperature, top_p=corpo.top_p, max_tokens=corpo.max_tokens,
        )]

    saida = []
    for r in respostas:
        d = r.to_dict()
        d.pop("contextos", None)  # textos completos ja vao em `recuperados`
        d["k_usado"], d["min_score_usado"] = k, min_score
        saida.append(d)
    return {"respostas": saida}


@app.exception_handler(HTTPException)
async def erro_http(_, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.detail})


@app.get("/")
def raiz():
    return FileResponse(WEB_DIR / "index.html")


app.mount("/", StaticFiles(directory=WEB_DIR), name="web")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("WEB_HOST", "127.0.0.1")
    port = int(os.getenv("WEB_PORT", "8000"))
    print(f"ChargeGrid Intelligence em http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")
