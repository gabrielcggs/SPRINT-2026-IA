"""Mostra, para os casos do eval set, ONDE esta o trecho que contem a resposta no ranking da busca.

    python scripts/diagnostico_recuperacao.py                 # casos R02 R03 R04 R16 R24
    python scripts/diagnostico_recuperacao.py R05 R10         # outros casos

Para cada caso imprime o top-6 (documento, secao, score) e a posicao do primeiro trecho que
contem as palavras-chave esperadas. Se essa posicao for > k, o problema e a BUSCA (nao o prompt).
"""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag import config  # noqa: E402
from rag.embeddings import build_embeddings  # noqa: E402
from rag.pipeline import RagPipeline  # noqa: E402
from rag.retriever import Retriever  # noqa: E402
from rag.vector_store import get_vector_store, total_chunks  # noqa: E402


def _norm(t: str) -> str:
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()


def main() -> None:
    ids = set(sys.argv[1:]) or {"R02", "R03", "R04", "R16", "R24"}
    cfg = config.chunking_padrao()
    store = get_vector_store(build_embeddings(config.embedding_provider(), config.embedding_model()),
                             config.persist_dir(), config.nome_colecao(cfg))
    n = total_chunks(store)
    if n == 0:
        raise SystemExit("Colecao vazia. Rode scripts/ingest.py primeiro.")
    retriever = Retriever(store, k=n, min_score=0.0, hibrido=config.busca_hibrida())
    print(f"modo de busca: {'hibrido (densa + BM25)' if config.busca_hibrida() else 'densa'}")

    casos = {c["id"]: c for c in json.loads((ROOT / "evals" / "rag_eval_set.json").read_text(encoding="utf-8"))}
    for cid in sorted(ids):
        c = casos[cid]
        hist = [{"pergunta": c["turnos_previos"][-1], "resposta": ""}] if c.get("turnos_previos") else None
        consulta = RagPipeline._consulta_busca(c["pergunta"], hist)
        busca = retriever.buscar(consulta)
        print(f"\n[{cid}] {c['pergunta']}")
        print(f"  consulta enviada a busca: {consulta!r}")
        chaves = [_norm(p) for p in c.get("palavras_chave", [])]
        achou = None
        for pos, r in enumerate(busca.todos, start=1):
            tem = bool(chaves) and all(k in _norm(r.texto) for k in chaves)
            if tem and achou is None:
                achou = pos
            if pos <= 6 or tem:
                print(f"  #{pos:<2} {r.score:.3f}  {r.documento} | {r.secao}{'   <-- contem a resposta' if tem else ''}")
        print(f"  trecho com a resposta aparece na posicao: {achou if achou else 'nenhuma'} (k atual = {config.top_k()})")


if __name__ == "__main__":
    main()
