"""ChromaDB persistente (Aula 05).

* Os vetores ficam em disco (``persist_directory``) e sobrevivem entre execucoes.
* A colecao usa distancia cosseno, entao ``relevancia = 1 - distancia``.
* Cada chunk tem um id deterministico: reindexar a mesma base nao duplica
  nada e nao gasta chamadas de embedding com chunks que ja existem.
"""
from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langchain_chroma import Chroma


def get_vector_store(
    embeddings: Embeddings,
    persist_dir: str | Path,
    collection: str,
    reset: bool = False,
) -> Chroma:
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    def _abrir() -> Chroma:
        return Chroma(
            collection_name=collection,
            embedding_function=embeddings,
            persist_directory=str(persist_dir),
            collection_metadata={"hnsw:space": "cosine"},
        )

    store = _abrir()
    if reset:
        store.delete_collection()
        store = _abrir()
    return store


def total_chunks(store: Chroma) -> int:
    return store._collection.count()


def indexar_chunks(store: Chroma, chunks: list[Document], lote: int = 64) -> int:
    """Indexa so os chunks novos. Retorna quantos foram efetivamente adicionados."""
    novos = 0
    for i in range(0, len(chunks), lote):
        grupo = chunks[i : i + lote]
        ids = [c.metadata["chunk_id"] for c in grupo]
        existentes = set(store.get(ids=ids).get("ids", []))
        pendentes = [(c, cid) for c, cid in zip(grupo, ids) if cid not in existentes]
        if not pendentes:
            continue
        store.add_documents(
            [c for c, _ in pendentes],
            ids=[cid for _, cid in pendentes],
        )
        novos += len(pendentes)
    return novos


def _caminho_manifesto(persist_dir: str | Path, collection: str) -> Path:
    return Path(persist_dir) / f"manifesto_{collection}.json"


def escrever_manifesto(persist_dir: str | Path, collection: str, info: dict) -> Path:
    caminho = _caminho_manifesto(persist_dir, collection)
    info = {**info, "atualizado_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    caminho.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def ler_manifesto(persist_dir: str | Path, collection: str) -> dict | None:
    caminho = _caminho_manifesto(persist_dir, collection)
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))
