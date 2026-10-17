# Relatório de modelos e parâmetros — Sprint 04

> Substitui o relatório da Sprint 03 (o comparativo antigo continua no histórico do Git).
> Todos os números vêm de `evals/results/*.json`; gere a tabela com `python evals/gerar_tabelas.py`.

## 1. Modelos comparados

| Papel | Provedor : modelo | Observação |
|---|---|---|
| Principal | `ollama:gpt-oss:120b-cloud` | modelo da Sprint 03, via Ollama Cloud |
| Comparação | `ollama:gpt-oss:20b-cloud` | mesmo provedor, modelo menor |
| Multi-provider (bônus) | <!-- ex.: gemini:<modelo> ou openai:<modelo> ou anthropic:<modelo> --> | outro provedor, mesmo prompt e mesmo eval set |
| Embeddings | `nomic-embed-text` (Ollama Cloud) | com prefixos `search_query:` / `search_document:` |

Como rodar cada execução (mesmo eval set, mesmo índice):

```bash
python evals/run_rag_eval.py --nome m1_120b --prompt v3 --model gpt-oss:120b-cloud
python evals/run_rag_eval.py --nome m2_20b  --prompt v3 --model gpt-oss:20b-cloud
python evals/run_rag_eval.py --nome m3_outro --prompt v3 --provider gemini --model <modelo>
```

## 2. Parâmetros e justificativa

| Parâmetro | Valor | Por quê |
|---|---:|---|
| `temperature` | 0 | respostas factuais e reproduzíveis; criatividade piora a fidelidade ao contexto |
| `top_p` | 0.9 | com temperature 0 tem efeito mínimo; mantido para comparar com a Sprint 03 |
| `k` (top-k) | 4 | cobre respostas que cruzam documentos (ex.: tarifa + potência) sem inflar o prompt |
| `max_tokens` | 1024 | o JSON com citações truncava em 512 |
| `min_score` | <!-- valor calibrado --> | limiar de relevância (1 − distância cosseno), calibrado com `scripts/calibrar_limiar.py` |

Se o grupo testar outros valores de `k`, `temperature` ou `top_p`, rode com `--k`, `--temperature`, `--top-p` e registre cada execução (o nome fica na tabela).

## 3. Resultados

<!-- COLE AQUI a tabela "Modelos e parâmetros" de python evals/gerar_tabelas.py -->

## 4. Análise

<!-- Escreva a leitura dos números: qual modelo ganhou em faithfulness, em answer_relevancy e em latência; se o modelo maior compensa o custo/latência; se o outro provedor mudou a taxa de citação ou de recusa. Só afirme o que a tabela mostra. -->
