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


def _completar_hit_trecho(r: dict) -> dict:
    """Resultados antigos nao tem hit_trecho: calcula a partir dos contextos enviados ao modelo
    (aproximacao: so os trechos aceitos pelo corte de relevancia)."""
    resumo = r["resumo"]
    if resumo.get("hit_trecho") is not None:
        return r
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from rag.lexical import normalizar

    casos = {c["id"]: c for c in json.loads((ROOT / "evals" / "rag_eval_set.json").read_text(encoding="utf-8"))}
    vals = []
    for l in r["casos"]:
        caso = casos.get(l["id"])
        if not caso or l.get("deve_recusar") or not caso["palavras_chave"]:
            continue
        chaves = [normalizar(p) for p in caso["palavras_chave"]]
        vals.append(1.0 if any(all(c in normalizar(t) for c in chaves) for t in l.get("contextos", [])) else 0.0)
    resumo["hit_trecho"] = round(sum(vals) / len(vals), 4) if vals else None
    return r


def carregar() -> list[dict]:
    arquivos = sorted(RESULTADOS.glob("*.json"), key=lambda p: p.stat().st_mtime)
    return [_completar_hit_trecho(json.loads(p.read_text(encoding="utf-8"))) for p in arquivos]


def tabela_iteracoes(res: list[dict]) -> str:
    linhas = [
        "| Iteração | Prompt | Chunking | Faithfulness | Answer relevancy | Contém esperado | Hit da fonte | Hit do trecho | Citação | Recusa correta | Recusa indevida | Descrição |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in res:
        c, s = r["config"], r["resumo"]
        ch = c["chunking"]
        linhas.append(
            f"| {r['iteracao']} | {c['prompt']} | {ch['chunk_size']}/{ch['chunk_overlap']} {ch['modo']} | "
            f"{_f(s['faithfulness'])} | {_f(s['answer_relevancy'])} | {_f(s['contem_esperado'])} | "
            f"{_f(s['hit_fonte'], True)} | {_f(s.get('hit_trecho'), True)} | {_f(s['citacao'], True)} | {_f(s['recusa_correta'], True)} | "
            f"{_f(s['recusa_indevida'], True)} | {r.get('descricao', '')}{f' (ATENÇÃO: {_erros(r)} casos com erro de chamada)' if _erros(r) else ''} |"
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


def _erros(r: dict) -> int:
    return sum(1 for l in r.get("casos", []) if l.get("motivo") == "erro")


def tabela_antes_depois(res: list[dict], primeira_nome: str | None = None, ultima_nome: str | None = None) -> str:
    if not res:
        return "(sem resultados)"
    por_nome = {r["iteracao"]: r for r in res}
    primeira = por_nome[primeira_nome] if primeira_nome else res[0]
    ultima = por_nome[ultima_nome] if ultima_nome else res[-1]
    a, d = primeira["resumo"], ultima["resumo"]
    linhas = [
        f"| Métrica | Sprints 1/2 (versão original) | Sprint 04 — {primeira['iteracao']} (1ª iteração) | Sprint 04 — {ultima['iteracao']} (última) |",
        "|---|---|---:|---:|",
        f"| Faithfulness ({primeira['metrica']}) | não medida | {_f(a['faithfulness'])} | {_f(d['faithfulness'])} |",
        f"| Answer relevancy | não medida | {_f(a['answer_relevancy'])} | {_f(d['answer_relevancy'])} |",
        f"| Qualidade do contexto recuperado (hit da fonte esperada) | sem recuperação (dados fixos no prompt) | {_f(a['hit_fonte'], True)} | {_f(d['hit_fonte'], True)} |",
        f"| Trecho com a resposta entre os recuperados (hit do trecho) | sem recuperação | {_f(a.get('hit_trecho'), True)} | {_f(d.get('hit_trecho'), True)} |",
        f"| Recusa indevida (pergunta respondível recusada) | não medida | {_f(a['recusa_indevida'], True)} | {_f(d['recusa_indevida'], True)} |",
        f"| Respostas com citação de fonte | 0% (não citava) | {_f(a['citacao'], True)} | {_f(d['citacao'], True)} |",
        f"| Recusa correta fora do contexto | não medida | {_f(a['recusa_correta'], True)} | {_f(d['recusa_correta'], True)} |",
    ]
    return "\n".join(linhas)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--saida", type=Path)
    ap.add_argument("--primeira", help="iteracao usada como 'antes' (padrao: a mais antiga)")
    ap.add_argument("--ultima", help="iteracao usada como 'depois' (padrao: a mais recente)")
    args = ap.parse_args()

    res = carregar()
    if not res:
        raise SystemExit("Nenhum resultado em evals/results/. Rode evals/run_rag_eval.py primeiro.")

    texto = (
        "## Evolução por iteração\n\n" + tabela_iteracoes(res)
        + "\n\n## Modelos e parâmetros\n\n" + tabela_modelos(res)
        + "\n\n## Antes/depois\n\n" + tabela_antes_depois(res, args.primeira, args.ultima) + "\n"
    )
    if args.saida:
        args.saida.write_text(texto, encoding="utf-8")
        print(f"salvo em {args.saida}")
    else:
        print(texto)


if __name__ == "__main__":
    main()
