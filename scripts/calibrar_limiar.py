"""Calibra RAG_MIN_SCORE (limiar de relevancia) com o eval set.

Mede o score do melhor trecho (top-1) para as perguntas que DEVEM ser respondidas e
para as que DEVEM ser recusadas, e sugere um limiar entre os dois grupos.

    python scripts/calibrar_limiar.py

Se os grupos se sobrepoem (acontece: "preco de compra do CG-01" fala de carregador),
o limiar sozinho nao separa tudo. Nesse caso a recusa fica por conta do prompt (v2/v3),
e isso e um bom "problema encontrado e solucao" para o relatorio.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag import config  # noqa: E402
from rag.embeddings import build_embeddings  # noqa: E402
from rag.retriever import Retriever  # noqa: E402
from rag.security import verificar_entrada  # noqa: E402
from rag.vector_store import get_vector_store, total_chunks  # noqa: E402


def main() -> None:
    cfg = config.chunking_padrao()
    emb = build_embeddings(config.embedding_provider(), config.embedding_model())
    store = get_vector_store(emb, config.persist_dir(), config.nome_colecao(cfg))
    if total_chunks(store) == 0:
        raise SystemExit("Colecao vazia. Rode scripts/ingest.py primeiro.")
    retriever = Retriever(store, k=config.top_k(), min_score=0.0)

    casos = json.loads((ROOT / "evals" / "rag_eval_set.json").read_text(encoding="utf-8"))
    dentro, fora = [], []
    for c in casos:
        if verificar_entrada(c["pergunta"]):
            continue  # ja barrada antes da busca
        busca = retriever.buscar(c["pergunta"] if not c.get("turnos_previos")
                                 else f"{c['turnos_previos'][-1]} {c['pergunta']}")
        (fora if c["deve_recusar"] else dentro).append((busca.top1_score or 0.0, c["id"], c["pergunta"]))

    for titulo, grupo in (("DEVEM responder", dentro), ("DEVEM recusar", fora)):
        print(f"\n{titulo}:")
        for score, cid, perg in sorted(grupo):
            print(f"  {score:.3f}  {cid}  {perg}")

    menor_dentro = min(s for s, *_ in dentro)
    maior_fora = max(s for s, *_ in fora) if fora else 0.0
    print(f"\nmenor score que deve passar: {menor_dentro:.3f} | maior score que deve ser barrado: {maior_fora:.3f}")
    if menor_dentro > maior_fora:
        print(f"sugestao: RAG_MIN_SCORE={(menor_dentro + maior_fora) / 2:.2f}  (separa os dois grupos)")
    else:
        print(f"os grupos se sobrepoem; use um limiar conservador (<= {menor_dentro - 0.02:.2f}) e deixe o prompt recusar o resto.")


if __name__ == "__main__":
    main()
