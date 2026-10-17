"""Chat RAG no terminal (alternativa a interface web).

    python src/main_rag.py
    python src/main_rag.py --prompt v2 --k 6
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag.pipeline import abrir_pipeline  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default=None, help="v1 | v2 | v3")
    ap.add_argument("--k", type=int, default=None)
    ap.add_argument("--min-score", type=float, default=None)
    args = ap.parse_args()

    pipeline = abrir_pipeline(k=args.k, min_score=args.min_score, prompt_version=args.prompt)
    historico: list[dict] = []

    print("=" * 56)
    print("  ChargeGrid Intelligence (RAG) — GoodWe EV Challenge 2026")
    print("=" * 56)
    print("Digite sua pergunta ('sair' encerra, 'limpar' zera a conversa)\n")

    while True:
        pergunta = input("Você: ").strip()
        if pergunta.lower() == "sair":
            break
        if pergunta.lower() == "limpar":
            historico.clear()
            print("[conversa limpa]\n")
            continue

        r = pipeline.responder(pergunta, historico)
        print(f"\nChargeGrid: {r.resposta}")
        for f in r.fontes:
            print(f"  [{f['id']}] {f['citacao']} (relevância {f['score']:.2f})")
        print(f"  ({r.provider}:{r.model} · prompt {r.prompt_version} · {r.latency_ms:.0f} ms)\n")
        historico.append({"pergunta": pergunta, "resposta": r.resposta})


if __name__ == "__main__":
    main()
