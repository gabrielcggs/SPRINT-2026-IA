"""Ingestao: PDFs -> chunks -> embeddings -> ChromaDB persistente."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from langchain_core.embeddings import Embeddings

from rag.chunking import ChunkingConfig, dividir_documentos
from rag.loader import carregar_pdfs
from rag.vector_store import (
    escrever_manifesto,
    get_vector_store,
    indexar_chunks,
    total_chunks,
)


def ingerir(
    kb_dir: str | Path,
    persist_dir: str | Path,
    colecao: str,
    cfg: ChunkingConfig,
    embeddings: Embeddings,
    reset: bool = False,
    log: Callable[[str], None] = print,
) -> dict:
    paginas = carregar_pdfs(kb_dir)
    chunks = dividir_documentos(paginas, cfg)
    log(f"{len(paginas)} paginas -> {len(chunks)} chunks ({cfg.assinatura()})")

    store = get_vector_store(embeddings, persist_dir, colecao, reset=reset)
    novos = indexar_chunks(store, chunks)
    total = total_chunks(store)
    log(f"{novos} chunks novos indexados; colecao '{colecao}' tem {total} chunks")

    documentos = sorted({p.metadata["source"] for p in paginas})
    info = {
        "colecao": colecao,
        "chunking": {
            "chunk_size": cfg.chunk_size,
            "chunk_overlap": cfg.chunk_overlap,
            "modo": cfg.modo,
            "cabecalho": cfg.cabecalho,
        },
        "documentos": documentos,
        "paginas": len(paginas),
        "chunks_gerados": len(chunks),
        "chunks_na_colecao": total,
    }
    escrever_manifesto(persist_dir, colecao, info)
    return info
