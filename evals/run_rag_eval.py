"""Avaliacao do RAG por iteracao (Aula 07): RAGAS ou fallback manual documentado.

Cada execucao e UMA iteracao e grava ``evals/results/<nome>.json`` com as respostas,
os contextos e os scores por caso. Compare iteracoes com ``evals/gerar_tabelas.py``.

Exemplos:
    python evals/run_rag_eval.py --nome it1_prompt_v1 --prompt v1
    python evals/run_rag_eval.py --nome it2_prompt_v2 --prompt v2
    python evals/run_rag_eval.py --nome it3_prompt_v3 --prompt v3
    python evals/run_rag_eval.py --nome it4_v3_chunk400 --prompt v3 --chunk-size 400 --overlap 60   # reindexe antes
    python evals/run_rag_eval.py --nome it5_v3_hibrido --prompt v3 --hibrido --min-score 0.55
    python evals/run_rag_eval.py --nome v3_gemini --prompt v3 --provider gemini --model <modelo>

Metricas
--------
* faithfulness        (0-1) respostas dadas: as afirmacoes estao apoiadas no contexto?
* answer_relevancy    (0-1) a resposta atende a pergunta? Recusa indevida conta 0.
* contem_esperado     (0-1) fracao das palavras-chave do gabarito presentes na resposta (deterministico).
* hit_fonte                 o documento esperado esta entre os recuperados? (qualidade do contexto)
* citacao                   a resposta citou um trecho [S#] valido?
* recusa_correta            perguntas fora do contexto foram recusadas?

Fallback manual (equivalente ao RAGAS, rubrica 0-1): o juiz e o proprio LLM com a
rubrica escrita abaixo, aplicada ao MESMO eval set em todas as iteracoes. Os criterios
ficam em RUBRICAS e sao gravados no JSON de resultado (campo ``rubricas``).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import replace
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag import config  # noqa: E402
from rag.pipeline import RagPipeline, abrir_pipeline  # noqa: E402

EVAL_SET = ROOT / "evals" / "rag_eval_set.json"
RESULTADOS = ROOT / "evals" / "results"

RUBRICAS = {
    "faithfulness": (
        "Divida a RESPOSTA em afirmacoes factuais. Score = fracao das afirmacoes que estao "
        "explicitamente apoiadas no CONTEXTO. Valores permitidos: 0, 0.25, 0.5, 0.75, 1. "
        "Afirmacao inventada ou contraria ao contexto = nao apoiada."
    ),
    "answer_relevancy": (
        "1 = responde diretamente e por completo a PERGUNTA; 0.75 = responde com pequena "
        "omissao ou excesso; 0.5 = responde parcialmente; 0.25 = tangencial; 0 = nao responde "
        "ou recusa uma pergunta que o contexto permitia responder."
    ),
}


def _norm(txt: str) -> str:
    d = unicodedata.normalize("NFKD", txt.lower())
    return "".join(c for c in d if not unicodedata.combining(c))


def _num(txt: str) -> str:
    """Normaliza 'R$ 753,83' / '753.83' para comparar numeros."""
    return _norm(txt).replace(".", ",")


def contem_esperado(resposta: str, palavras: list[str]) -> float | None:
    if not palavras:
        return None
    alvo = _num(resposta)
    return round(sum(1 for p in palavras if _num(p) in alvo) / len(palavras), 4)


# ---------------- juiz manual ----------------
def _juiz(llm, criterio: str, entrada: str) -> float:
    from langchain_core.messages import HumanMessage, SystemMessage

    sistema = (
        "Voce e um avaliador rigoroso de sistemas RAG. Aplique a rubrica e responda SOMENTE "
        'com JSON: {"score": <numero entre 0 e 1>, "motivo": "<uma frase>"}.\n\nRubrica: ' + criterio
    )
    saida = llm.invoke([SystemMessage(content=sistema), HumanMessage(content=entrada)])
    texto = getattr(saida, "content", str(saida))
    m = re.search(r"\{.*\}", str(texto), re.DOTALL)
    try:
        return max(0.0, min(1.0, float(json.loads(m.group(0))["score"])))
    except Exception:  # noqa: BLE001
        return float("nan")


def avaliar_manual(llm_juiz, caso: dict, r: dict) -> dict:
    contexto = "\n---\n".join(r["contextos"]) or "(sem contexto)"
    out: dict = {}
    if not r["recusado"]:
        out["faithfulness"] = _juiz(
            llm_juiz, RUBRICAS["faithfulness"], f"CONTEXTO:\n{contexto}\n\nRESPOSTA:\n{r['resposta']}"
        )
    out["answer_relevancy"] = _juiz(
        llm_juiz, RUBRICAS["answer_relevancy"],
        f"PERGUNTA:\n{caso['pergunta']}\n\nGABARITO:\n{caso['ground_truth']}\n\nRESPOSTA:\n{r['resposta']}",
    )
    return out


def avaliar_ragas(casos_resultados: list[tuple[dict, dict]], llm, embeddings) -> list[dict]:
    """Tenta RAGAS (faithfulness + answer_relevancy). Escrito para ragas>=0.2; levanta se indisponivel."""
    from ragas import EvaluationDataset, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import Faithfulness, ResponseRelevancy

    amostras, indices = [], []
    for i, (caso, r) in enumerate(casos_resultados):
        if r["recusado"] and caso["deve_recusar"]:
            continue  # recusa correta nao tem o que medir
        amostras.append({
            "user_input": caso["pergunta"],
            "response": r["resposta"],
            "retrieved_contexts": r["contextos"] or ["(sem contexto)"],
            "reference": caso["ground_truth"],
        })
        indices.append(i)
    ds = EvaluationDataset.from_list(amostras)
    res = evaluate(
        ds,
        metrics=[Faithfulness(), ResponseRelevancy()],
        llm=LangchainLLMWrapper(llm),
        embeddings=LangchainEmbeddingsWrapper(embeddings),
    )
    df = res.to_pandas()
    saida: list[dict] = [{} for _ in casos_resultados]
    for linha, i in enumerate(indices):
        row = df.iloc[linha]
        saida[i] = {
            "faithfulness": float(row["faithfulness"]),
            "answer_relevancy": float(row["answer_relevancy"]),
        }
    return saida


# ---------------- execucao ----------------
def executar_caso(pipe: RagPipeline, caso: dict, **kw) -> dict:
    historico: list[dict] = []
    for previa in caso.get("turnos_previos", []):
        rp = pipe.responder(previa, historico, **kw)
        historico.append({"pergunta": previa, "resposta": rp.resposta})
    return pipe.responder(caso["pergunta"], historico, **kw).to_dict()


def _hit_trecho(recuperados: list[dict], palavras: list[str]) -> float:
    """1 se algum trecho enviado ao modelo contem TODAS as palavras-chave do gabarito (qualidade da busca)."""
    from rag.lexical import normalizar

    chaves = [normalizar(p) for p in palavras]
    return 1.0 if any(all(c in normalizar(x["trecho"]) for c in chaves) for x in recuperados) else 0.0


def _media(vals):
    vals = [v for v in vals if v is not None and v == v]
    return round(mean(vals), 4) if vals else None


def resumir(linhas: list[dict]) -> dict:
    responder = [l for l in linhas if not l["deve_recusar"]]
    recusar = [l for l in linhas if l["deve_recusar"]]
    dadas = [l for l in responder if not l["recusado"]]
    return {
        "casos": len(linhas),
        "faithfulness": _media([l["scores"].get("faithfulness") for l in dadas]),
        "answer_relevancy": _media(
            [0.0 if l["recusado"] else l["scores"].get("answer_relevancy") for l in responder]
        ),
        "contem_esperado": _media([l["scores"].get("contem_esperado") for l in responder]),
        "hit_fonte": _media([l["scores"].get("hit_fonte") for l in responder if l["scores"].get("hit_fonte") is not None]),
        "hit_trecho": _media([l["scores"].get("hit_trecho") for l in responder if l["scores"].get("hit_trecho") is not None]),
        "citacao": _media([1.0 if l["citou"] else 0.0 for l in dadas]),
        "recusa_correta": _media([1.0 if l["recusado"] else 0.0 for l in recusar]),
        "recusa_indevida": _media([1.0 if l["recusado"] else 0.0 for l in responder]),
        "latencia_ms_media": _media([l["latency_ms"] for l in linhas]),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nome", required=True, help="nome da iteracao (vira evals/results/<nome>.json)")
    ap.add_argument("--prompt", default=config.prompt_version(), help="v1 | v2 | v3")
    ap.add_argument("--provider", default=config.llm_provider())
    ap.add_argument("--model", default=config.llm_model())
    ap.add_argument("--k", type=int, default=config.top_k())
    ap.add_argument("--min-score", type=float, default=config.min_score())
    ap.add_argument("--temperature", type=float, default=config.llm_temperature())
    ap.add_argument("--top-p", type=float, default=config.llm_top_p())
    ap.add_argument("--max-tokens", type=int, default=config.llm_max_tokens())
    ap.add_argument("--hibrido", action="store_true", help="busca hibrida: densa + BM25 (RRF)")
    ap.add_argument("--densa", action="store_true", help="busca so por embeddings (como nas iteracoes 1 a 4)")
    ap.add_argument("--chunk-size", type=int)
    ap.add_argument("--overlap", type=int)
    ap.add_argument("--modo", choices=["secao", "pagina"])
    ap.add_argument("--sem-cabecalho", action="store_true")
    ap.add_argument("--metrica", choices=["manual", "ragas"], default="manual")
    ap.add_argument("--juiz-provider", help="padrao: o mesmo provedor da geracao")
    ap.add_argument("--juiz-model", help="padrao: o mesmo modelo da geracao")
    ap.add_argument("--descricao", default="", help="o que mudou nesta iteracao")
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

    pipe = abrir_pipeline(
        k=args.k, min_score=args.min_score, prompt_version=args.prompt,
        provider=args.provider, model=args.model, chunking=cfg,
        hibrido=True if args.hibrido else (False if args.densa else None),
    )
    pipe.temperature, pipe.top_p, pipe.max_tokens = args.temperature, args.top_p, args.max_tokens

    casos = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    pares: list[tuple[dict, dict]] = []
    for caso in casos:
        print(f"[{caso['id']}] {caso['pergunta']}")
        pares.append((caso, executar_caso(pipe, caso)))

    # metricas deterministicas
    linhas: list[dict] = []
    for caso, r in pares:
        esperadas = caso["fontes_esperadas"]
        recuperados = {x["documento"] for x in r["recuperados"]}
        scores = {
            "contem_esperado": None if r["recusado"] else contem_esperado(r["resposta"], caso["palavras_chave"]),
            "hit_fonte": (1.0 if recuperados & set(esperadas) else 0.0) if esperadas else None,
            "hit_trecho": _hit_trecho(r["recuperados"], caso["palavras_chave"]) if caso["palavras_chave"] else None,
        }
        linhas.append({
            "id": caso["id"], "categoria": caso["categoria"], "pergunta": caso["pergunta"],
            "ground_truth": caso["ground_truth"], "deve_recusar": caso["deve_recusar"],
            "resposta": r["resposta"], "recusado": r["recusado"], "motivo": r["motivo"],
            "citou": r["citou"], "fontes": [f["citacao"] for f in r["fontes"]],
            "top1_score": r["top1_score"], "latency_ms": r["latency_ms"],
            "contextos": r["contextos"], "scores": scores,
        })

    # metricas por LLM (RAGAS ou rubrica manual)
    metrica_usada = args.metrica
    juiz_provider = args.juiz_provider or args.provider
    juiz_model = args.juiz_model or args.model
    from rag.llm import build_llm
    juiz = build_llm(juiz_provider, juiz_model, temperature=0.0, max_tokens=512)

    avaliados: list[dict] | None = None
    if args.metrica == "ragas":
        try:
            from rag.embeddings import build_embeddings
            avaliados = avaliar_ragas(pares, juiz,
                                      build_embeddings(config.embedding_provider(), config.embedding_model()))
        except Exception as exc:  # noqa: BLE001
            print(f"RAGAS indisponivel ({type(exc).__name__}: {exc}). Usando fallback manual.")
            metrica_usada = "manual (fallback: ragas falhou)"
    if avaliados is None:
        avaliados = [avaliar_manual(juiz, caso, r) for caso, r in pares]
    for linha, av in zip(linhas, avaliados):
        linha["scores"].update(av)

    resumo = resumir(linhas)
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    saida = RESULTADOS / f"{args.nome}.json"
    saida.write_text(json.dumps({
        "iteracao": args.nome,
        "descricao": args.descricao,
        "metrica": metrica_usada,
        "juiz": f"{juiz_provider}:{juiz_model}",
        "rubricas": RUBRICAS,
        "config": {
            "prompt": args.prompt, "provider": args.provider, "model": args.model,
            "k": args.k, "min_score": args.min_score, "temperature": args.temperature,
            "top_p": args.top_p, "max_tokens": args.max_tokens,
            "chunking": {"chunk_size": cfg.chunk_size, "chunk_overlap": cfg.chunk_overlap,
                         "modo": cfg.modo, "cabecalho": cfg.cabecalho},
            "embedding": f"{config.embedding_provider()}:{config.embedding_model()}",
        },
        "resumo": resumo,
        "casos": linhas,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nResumo ({metrica_usada}):")
    for k, v in resumo.items():
        print(f"  {k}: {v}")
    print(f"\nSalvo em {saida}")


if __name__ == "__main__":
    main()
