# Relatório de modelos e parâmetros — Sprint 04

> Substitui o relatório da Sprint 03 (o comparativo antigo continua no histórico do Git).
> Todos os números vêm de `evals/results/*.json` (`python evals/gerar_tabelas.py`). Eval set: 25 casos
> (18 que devem ser respondidos e 7 que devem ser recusados). Com 18 casos, **um caso vale 5,6 pontos percentuais**:
> diferenças pequenas não são conclusivas.

## 1. Modelos comparados

| Papel | Provedor : modelo | Observação |
|---|---|---|
| Principal | `ollama:gpt-oss:120b-cloud` | modelo da Sprint 03, via Ollama Cloud |
| Comparação | `ollama:gpt-oss:20b-cloud` | mesmo provedor, modelo menor |
| Multi-provider (bônus) | `gemini:gemini-2.5-flash` | outro provedor, mesmo prompt v3 e mesmo eval set |
| Embeddings | `nomic-embed-text` (Ollama local) | com prefixos `search_query:` / `search_document:`; a Ollama Cloud recusou `/api/embed` (401) |

O provedor é escolhido por configuração (`RAG_LLM_PROVIDER`, `--provider`): a mesma função `build_llm` atende
`ollama`, `openai`, `gemini` e `anthropic`, sem mudar o restante do pipeline.

## 2. Parâmetros e justificativa

| Parâmetro | Valor final | Por quê |
|---|---:|---|
| `temperature` | 0 | respostas factuais e reproduzíveis; testado 0,7 (seção 3.3) sem ganho |
| `top_p` | 0,9 | não foi variado: com `temperature` 0 tem efeito mínimo; mantido para comparar com a Sprint 03 |
| `k` (top-k) | 6 | a resposta costuma estar na 5ª ou 6ª posição do ranking (seção 3.2) |
| `max_tokens` | 1024 | não foi variado nas rodadas; com 512 o JSON com citações truncava em testes manuais |
| `min_score` | 0,55 | com `nomic-embed-text` os scores ficam entre ~0,58 e 0,76; o corte só barra trechos muito distantes. Quem recusa o que está fora do assunto é o prompt v3 |
| Busca | híbrida | embeddings + BM25 fundidos por RRF (ver `docs/relatorio_rag.md`) |

## 3. Resultados

### 3.1 Modelos, com a configuração final de busca (híbrida, k=6)

| Modelo | temperature | Faithfulness | Answer relevancy | Contém esperado | Recusa indevida | Latência (ms) |
|---|---:|---:|---:|---:|---:|---:|
| gpt-oss:120b (Ollama Cloud) | 0.0 | 1.00 | 0.83 | 0.91 | 6% | 905 |
| gpt-oss:20b (Ollama Cloud) | 0.0 | 1.00 | 0.85 | 0.85 | 6% | 1690 |
| gpt-oss:120b, temperature 0.7 | 0.7 | 1.00 | 0.85 | 0.91 | 6% | 944 |

### 3.2 Valor de k (busca só por embeddings, prompt v3, gpt-oss:120b)

| k | Faithfulness | Answer relevancy | Hit do trecho | Recusa indevida |
|---|---:|---:|---:|---:|
| 2 | 0.92 | 0.71 | 67% | 28% |
| 4 | 1.00 | 0.69 | 78% | 28% |
| 6 | 1.00 | 0.71 | 83% | 22% |

### 3.3 Temperatura (configuração final)

| temperature | Faithfulness | Answer relevancy | Contém esperado | Latência (ms) |
|---|---:|---:|---:|---:|
| 0.0 | 1.00 | 0.83 | 0.91 | 905 |
| 0.7 | 1.00 | 0.85 | 0.91 | 944 |

### 3.4 Outro provedor (mesma configuração: busca por embeddings, k=4, prompt v3)

| Provedor : modelo | Faithfulness | Answer relevancy | Contém esperado | Citação | Recusa indevida | Latência (ms) |
|---|---:|---:|---:|---:|---:|---:|
| ollama: gpt-oss:120b-cloud | 1.00 | 0.69 | 0.96 | 100% | 28% | 872 |
| gemini: gemini-2.5-flash | 0.93 | 0.62 | 0.86 | 93% | 22% | 5645 |

O juiz de `answer_relevancy` e `faithfulness` foi o `gpt-oss:120b-cloud` nas duas linhas.

## 4. Análise

- **120b x 20b.** Com a mesma busca, os dois recusam por engano o mesmo número de casos (6%) e mantêm `faithfulness` 1,00.
  O 20b teve `answer_relevancy` 0,02 maior, diferença menor que um caso e dentro do ruído do juiz. O 120b teve `contém esperado`
  0,06 maior (0,91 contra 0,85): o 20b omitiu mais dados do gabarito. Nas nossas rodadas o 20b também foi mais lento
  (1690 ms contra 905 ms), o que pode refletir a fila da nuvem e não só o tamanho do modelo. Escolhemos o 120b: respostas mais completas e mais rápidas aqui.
- **k.** Subir `k` melhora a recuperação: o trecho com a resposta entra em 67% dos casos com k=2, 78% com k=4 e 83% com k=6 (busca só por embeddings).
  Com k=2 a `faithfulness` cai para 0,92. A busca híbrida com k=6 chega a 100% (relatório do RAG, seção 6).
- **Temperatura.** 0,7 não mudou `faithfulness` nem `contém esperado` e deu +0,02 de `answer_relevancy` (dentro do ruído).
  Mantivemos 0 pela reprodutibilidade, já que o ganho não é mensurável com 18 casos.
- **Outro provedor.** Nas mesmas condições, o Gemini 2.5 Flash ficou abaixo do gpt-oss:120b em `faithfulness` (0,93 contra 1,00),
  `answer_relevancy` (0,62 contra 0,69), `contém esperado` (0,86 contra 0,96) e citação (93% contra 100%), e foi cerca de 6 vezes
  mais lento (5645 ms contra 872 ms). Recusou por engano menos casos (22% contra 28%). **Ressalva:** o juiz foi o gpt-oss:120b, que também
  era o modelo avaliado na outra linha; esse viés pode favorecê-lo. O ideal seria um juiz de um terceiro provedor.
- **Rodada descartada.** Uma execução do Gemini com a busca final (`final_gemini`) retornou métricas incompatíveis com a anterior
  (`faithfulness` 0,06 e latência de 31 s), o que indica falha nas chamadas à API. Ela não foi usada nas conclusões e deve ser refeita antes de ser citada.
