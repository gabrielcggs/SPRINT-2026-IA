"""Indexa a base de conhecimento no ChromaDB persistente.

Exemplos:
    python scripts/ingest.py                         # configuracao do .env
    python scripts/ingest.py --reset                 # apaga a colecao e reindexa
    python scripts/ingest.py --chunk-size 400 --overlap 60 --modo pagina   # iteracao de teste
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag import config  # noqa: E402
from rag.embeddings import build_embeddings  # noqa: E402
from rag.ingest import ingerir  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kb", type=Path, default=config.kb_dir())
    ap.add_argument("--persist", type=Path, default=config.persist_dir())
    ap.add_argument("--chunk-size", type=int)
    ap.add_argument("--overlap", type=int)
    ap.add_argument("--modo", choices=["secao", "pagina"])
    ap.add_argument("--sem-cabecalho", action="store_true")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--embedding-provider", help="ollama (padrao) ou hash (so testes)")
    args = ap.parse_args()

    cfg = config.chunking_padrao()
    if args.chunk_size:
        cfg = replace(cfg, chunk_size=args.chunk_size)
    if args.overlap is not None:
        cfg = replace(cfg, chunk_overlap=args.overlap)
    if args.modo:
        cfg = replace(cfg, modo=args.modo)
    if args.sem_cabecalho:
        cfg = replace(cfg, cabecalho=False)

    provider = args.embedding_provider or config.embedding_provider()
    emb = build_embeddings(provider, config.embedding_model())
    colecao = config.nome_colecao(cfg, provider=provider)
    ingerir(args.kb, args.persist, colecao, cfg, emb, reset=args.reset)


if __name__ == "__main__":
    main()
