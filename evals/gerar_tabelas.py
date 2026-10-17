"""Gera as tabelas dos relatorios a partir de evals/results/*.json (numeros REAIS, nada digitado).

    python evals/gerar_tabelas.py                      # imprime no terminal
    python evals/gerar_tabelas.py --saida docs/tabelas_sprint04.md

Produz: (1) evolucao por iteracao / versoes do prompt, (2) comparativo de modelos
e parametros, (3) tabela antes/depois para o relatorio de evolucao.
Cole essas tabelas em docs/relatorio_rag.md, docs/relatorio_modelos.md e no PDF.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTADOS = ROOT / "evals" / "results"


def _f(v, pct=False):
    if v is None:
        return "n/d"
    return f"{v * 100:.0f}%" if pct else f"{v:.2f}"


def carregar() -> list[dict]:
    arquivos = sorted(RESULTADOS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    return [json.loads(p.read_text(encoding="utf-8")) for p in arquivos]


def tabela_iteracoes(res: list[dict]) -> str:
    linhas = [
        "| Iteração | Prompt | Chunking | Faithfulness | Answer relevancy | Contém esperado | Hit da fonte | Citação | Recusa correta | Descrição |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in res:
        c, s = r["config"], r["resumo"]
        ch = c["chunking"]
        linhas.append(
            f"| {r['iteracao']} | {c['prompt']} | {ch['chunk_size']}/{ch['chunk_overlap']} {ch['modo']} | "
            f"{_f(s['faithfulness'])} | {_f(s['answer_relevancy'])} | {_f(s['contem_esperado'])} | "
            f"{_f(s['hit_fonte'], True)} | {_f(s['citacao'], True)} | {_f(s['recusa_correta'], True)} | {r.get('descricao', '')} |"
        )
    return "\n".join(linhas)


def tabela_modelos(res: list[dict]) -> str:
    linhas = [
        "| Execução | Provedor:modelo | Prompt | temperature | top_p | k | max_tokens | Faithfulness | Answer relevancy | Contém esperado | Latência média (ms) |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in res:
        c, s = r["config"], r["resumo"]
        linhas.append(
            f"| {r['iteracao']} | {c['provider']}:{c['model']} | {c['prompt']} | {c['temperature']} | {c['top_p']} | "
            f"{c['k']} | {c['max_tokens']} | {_f(s['faithfulness'])} | {_f(s['answer_relevancy'])} | "
            f"{_f(s['contem_esperado'])} | {s['latencia_ms_media']} |"
        )
    return "\n".join(linhas)


def tabela_antes_depois(res: list[dict]) -> str:
    if not res:
        return "(sem resultados)"
    primeira, ultima = res[0], res[-1]
    a, d = primeira["resumo"], ultima["resumo"]
    linhas = [
        f"| Métrica | Sprints 1/2 (versão original) | Sprint 04 — {primeira['iteracao']} (1ª iteração) | Sprint 04 — {ultima['iteracao']} (última) |",
        "|---|---|---:|---:|",
        f"| Faithfulness ({primeira['metrica']}) | não medida | {_f(a['faithfulness'])} | {_f(d['faithfulness'])} |",
        f"| Answer relevancy | não medida | {_f(a['answer_relevancy'])} | {_f(d['answer_relevancy'])} |",
        f"| Qualidade do contexto recuperado (hit da fonte esperada) | sem recuperação (dados fixos no prompt) | {_f(a['hit_fonte'], True)} | {_f(d['hit_fonte'], True)} |",
        f"| Respostas com citação de fonte | 0% (não citava) | {_f(a['citacao'], True)} | {_f(d['citacao'], True)} |",
        f"| Recusa correta fora do contexto | não medida | {_f(a['recusa_correta'], True)} | {_f(d['recusa_correta'], True)} |",
    ]
    return "\n".join(linhas)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--saida", type=Path)
    args = ap.parse_args()

    res = carregar()
    if not res:
        raise SystemExit("Nenhum resultado em evals/results/. Rode evals/run_rag_eval.py primeiro.")

    texto = (
        "## Evolução por iteração\n\n" + tabela_iteracoes(res)
        + "\n\n## Modelos e parâmetros\n\n" + tabela_modelos(res)
        + "\n\n## Antes/depois\n\n" + tabela_antes_depois(res) + "\n"
    )
    if args.saida:
        args.saida.write_text(texto, encoding="utf-8")
        print(f"salvo em {args.saida}")
    else:
        print(texto)


if __name__ == "__main__":
    main()
