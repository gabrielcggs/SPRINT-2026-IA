"""Configuracao central do RAG (caminhos, chunking, parametros de busca).

Tudo pode ser sobrescrito por variavel de ambiente (.env), o que permite rodar
iteracoes diferentes de avaliacao sem mexer no codigo.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv

from rag.chunking import ChunkingConfig

ROOT = Path(__file__).resolve().parents[2]
# override=True: o .env do projeto vence qualquer OLLAMA_API_KEY antiga exportada no
# shell (~/.zshrc, conda...). Mesmo comportamento do chatbot da Sprint 03.
load_dotenv(ROOT / ".env", override=True)


def _bool(valor: str | None, padrao: bool) -> bool:
    if valor is None:
        return padrao
    return valor.strip().lower() in {"1", "true", "sim", "yes", "on"}


def kb_dir() -> Path:
    return Path(os.getenv("RAG_KB_DIR", ROOT / "data" / "knowledge_base"))


def persist_dir() -> Path:
    return Path(os.getenv("RAG_PERSIST_DIR", ROOT / "data" / "chroma_db"))


def chunking_padrao() -> ChunkingConfig:
    return ChunkingConfig(
        chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "700")),
        chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "100")),
        modo=os.getenv("RAG_CHUNK_MODO", "secao"),
        cabecalho=_bool(os.getenv("RAG_CHUNK_CABECALHO"), True),
    )


def embedding_provider() -> str:
    return os.getenv("RAG_EMBEDDING_PROVIDER", "ollama").lower()


def embedding_model() -> str:
    return os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text")


def nome_colecao(cfg: ChunkingConfig, provider: str | None = None, modelo: str | None = None) -> str:
    """Uma colecao por (chunking, embedding): trocar o chunking nao suja o indice anterior."""
    provider = provider or embedding_provider()
    modelo = modelo or embedding_model()
    tag = "hash" if provider == "hash" else re.sub(r"[^a-zA-Z0-9._-]", "-", modelo)
    nome = f"chargegrid_{cfg.assinatura()}_{tag}"
    return nome[:63].strip("-_.")


# Busca
def top_k() -> int:
    return int(os.getenv("RAG_K", "6"))


def busca_hibrida() -> bool:
    """RAG_HIBRIDO=1 liga a busca hibrida (densa + BM25 por RRF)."""
    return _bool(os.getenv("RAG_HIBRIDO"), True)


def min_score() -> float:
    # Limiar de relevancia (1 - distancia cosseno). CALIBRAR com scripts/calibrar_limiar.py.
    return float(os.getenv("RAG_MIN_SCORE", "0.55"))


# Geracao
def llm_provider() -> str:
    return os.getenv("RAG_LLM_PROVIDER", "ollama").lower()


def llm_model() -> str:
    return os.getenv("RAG_LLM_MODEL", os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud"))


def llm_temperature() -> float:
    return float(os.getenv("RAG_TEMPERATURE", "0"))


def llm_top_p() -> float:
    return float(os.getenv("RAG_TOP_P", "0.9"))


def llm_max_tokens() -> int:
    return int(os.getenv("RAG_MAX_TOKENS", "1024"))


def prompt_version() -> str:
    return os.getenv("RAG_PROMPT_VERSION", "v3")
