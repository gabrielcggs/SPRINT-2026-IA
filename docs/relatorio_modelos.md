# Relatorio de modelos - Sprint 03

## Objetivo

Comparar dois modelos remotos usando a mesma chain LCEL, o mesmo prompt e o mesmo eval set.

O projeto nao usa modelo local. A chamada e feita com `ChatOllama` para a Ollama Cloud, por isso nao existe `ollama pull`.

## Modelos

| Modelo | Uso |
|---|---|
| `gpt-oss:120b-cloud` | Modelo principal |
| `gpt-oss:20b-cloud` | Modelo de comparacao |

## Parametros

| Parametro | Valor |
|---|---:|
| `temperature` | `0.1` |
| `top_p` | `0.9` |
| `max_tokens` | `512` |

Usamos temperatura baixa porque o chatbot responde com dados simulados de carregadores, custo e consumo. Respostas muito criativas atrapalhariam a avaliacao.

## Como executar

```bash
python evals/compare_models.py
```

O resultado fica em `evals/model_comparison.json`.

## Tabela para preencher depois da execucao

| Metrica | gpt-oss:120b-cloud | gpt-oss:20b-cloud |
|---|---:|---:|
| Qualidade media (0-5) | 5.0 | 4.5 |
| Tokens medios/turno | 10.2 | 10.2 |
| Latencia media (ms) | 1731.08 | 5239.53 |
| Structured output valido (%) | 100.0 | 100.0 |
| Casos adequados | 10/10 | 10/10 |

## Observacao

Os numeros nao devem ser inventados. A equipe deve executar o eval e preencher a tabela final com os resultados reais.
