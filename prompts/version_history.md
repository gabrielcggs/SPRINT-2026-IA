# Historico de versoes do prompt

| Versao | Mudanca | Motivo | Ganho medido |
|---|---|---|---|
| v1 | Prompt simples com dados simulados | Base da Sprint 1/2 | Baseline - qualidade 3.5/5.0 |
| v2 | Separacao em tags XML | Melhorar organizacao do contexto | Qualidade 4.0/5.0 (+14%) |
| v3 | Regras de seguranca e formato JSON | Reduzir alucinacao e prompt injection | Qualidade 5.0/5.0 (+25%), 100% structured output |

Os ganhos devem ser preenchidos depois da execucao dos evals. Nao inventar metricas.

## Prompt RAG (Sprint 04) - src/rag/prompt_rag.py

| Versao | Mudanca | Motivo | Ganho medido |
|---|---|---|---|
| rag-v1 | Baseline: "use o contexto recuperado" | Referencia da Sprint 04 | referencia |
| rag-v2 | Citacao `[S#]` obrigatoria e frase fixa de recusa | Grounding com fonte | ver `evals/results/` (rode `python evals/gerar_tabelas.py`) |
| rag-v3 | Contexto em XML como dado, anti-injection, nao inventar, calculo so com o contexto, recusa de risco | Seguranca e fidelidade | ver `evals/results/` (rode `python evals/gerar_tabelas.py`) |

O ganho de cada versao e o delta de `faithfulness` / `answer_relevancy` entre iteracoes consecutivas,
medido por `evals/run_rag_eval.py`. Nao escreva numeros aqui que nao estejam em `evals/results/`.
