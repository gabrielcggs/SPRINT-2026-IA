## Evolução por iteração

| Iteração | Prompt | Chunking | Faithfulness | Answer relevancy | Contém esperado | Hit da fonte | Hit do trecho | Citação | Recusa correta | Recusa indevida | Descrição |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| it1_prompt_v1 | v1 | 700/100 secao | 1.00 | 0.69 | 0.83 | 83% | 78% | 100% | 100% | 17% | Baseline: prompt simples, sem citação |
| it2_prompt_v2 | v2 | 700/100 secao | 1.00 | 0.69 | 0.96 | 83% | 78% | 100% | 100% | 28% | Citação [S#] obrigatória e frase fixa de recusa |
| it3_prompt_v3 | v3 | 700/100 secao | 1.00 | 0.69 | 0.96 | 83% | 78% | 100% | 100% | 28% | Contexto em XML como dado, anti-injection, cálculo só do contexto |
| it4_v3_chunk400 | v3 | 400/60 secao | 1.00 | 0.69 | 0.96 | 83% | 78% | 100% | 100% | 28% | Chunks menores (400/60) |
| v3_gptoss20b | v3 | 700/100 secao | 1.00 | 0.72 | 0.89 | 83% | 78% | 100% | 100% | 22% | Modelo menor |
| v3_temp07 | v3 | 700/100 secao | 1.00 | 0.71 | 0.96 | 83% | 78% | 100% | 100% | 28% | temperature 0.7 |
| v3_k2 | v3 | 700/100 secao | 0.92 | 0.71 | 0.96 | 83% | 67% | 100% | 100% | 28% | k=2 |
| v3_k6 | v3 | 700/100 secao | 1.00 | 0.71 | 0.89 | 89% | 83% | 100% | 100% | 22% | k=6 |
| v3_gemini | v3 | 700/100 secao | 0.93 | 0.62 | 0.86 | 83% | 78% | 93% | 100% | 22% | Provedor Gemini |
| it5_v3_hibrido | v3 | 700/100 secao | 1.00 | 0.75 | 0.90 | 94% | 89% | 100% | 100% | 17% | Busca híbrida (densa + BM25 por RRF) |
| it6_v3_hibrido_k6 | v3 | 700/100 secao | 1.00 | 0.83 | 0.91 | 100% | 100% | 100% | 100% | 6% | Híbrida com k=6 |
| final_gptoss120b | v3 | 700/100 secao | 1.00 | 0.83 | 0.91 | 100% | 100% | 100% | 100% | 6% | Final: gpt-oss 120b |
| final_gptoss20b | v3 | 700/100 secao | 1.00 | 0.85 | 0.85 | 100% | 100% | 100% | 100% | 6% | Final: gpt-oss 20b |
| final_gemini | v3 | 700/100 secao | 0.06 | 0.11 | 0.12 | 100% | 100% | 12% | 29% | 6% | Final: Gemini 2.5 Flash |
| final_temp07 | v3 | 700/100 secao | 1.00 | 0.85 | 0.91 | 100% | 100% | 100% | 100% | 6% | Final: temperature 0.7 |

## Modelos e parâmetros

| Execução | Provedor:modelo | Prompt | temperature | top_p | k | max_tokens | Faithfulness | Answer relevancy | Contém esperado | Latência média (ms) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| it1_prompt_v1 | ollama:gpt-oss:120b-cloud | v1 | 0.0 | 0.9 | 4 | 1024 | 1.00 | 0.69 | 0.83 | 832.88 |
| it2_prompt_v2 | ollama:gpt-oss:120b-cloud | v2 | 0.0 | 0.9 | 4 | 1024 | 1.00 | 0.69 | 0.96 | 892.868 |
| it3_prompt_v3 | ollama:gpt-oss:120b-cloud | v3 | 0.0 | 0.9 | 4 | 1024 | 1.00 | 0.69 | 0.96 | 872.436 |
| it4_v3_chunk400 | ollama:gpt-oss:120b-cloud | v3 | 0.0 | 0.9 | 4 | 1024 | 1.00 | 0.69 | 0.96 | 1763.656 |
| v3_gptoss20b | ollama:gpt-oss:20b-cloud | v3 | 0.0 | 0.9 | 4 | 1024 | 1.00 | 0.72 | 0.89 | 1741.088 |
| v3_temp07 | ollama:gpt-oss:120b-cloud | v3 | 0.7 | 0.9 | 4 | 1024 | 1.00 | 0.71 | 0.96 | 1039.812 |
| v3_k2 | ollama:gpt-oss:120b-cloud | v3 | 0.0 | 0.9 | 2 | 1024 | 0.92 | 0.71 | 0.96 | 864.62 |
| v3_k6 | ollama:gpt-oss:120b-cloud | v3 | 0.0 | 0.9 | 6 | 1024 | 1.00 | 0.71 | 0.89 | 929.612 |
| v3_gemini | gemini:gemini-2.5-flash | v3 | 0.0 | 0.9 | 4 | 1024 | 0.93 | 0.62 | 0.86 | 5645.344 |
| it5_v3_hibrido | ollama:gpt-oss:120b-cloud | v3 | 0.0 | 0.9 | 4 | 1024 | 1.00 | 0.75 | 0.90 | 811.392 |
| it6_v3_hibrido_k6 | ollama:gpt-oss:120b-cloud | v3 | 0.0 | 0.9 | 6 | 1024 | 1.00 | 0.83 | 0.91 | 973.04 |
| final_gptoss120b | ollama:gpt-oss:120b-cloud | v3 | 0.0 | 0.9 | 6 | 1024 | 1.00 | 0.83 | 0.91 | 905.004 |
| final_gptoss20b | ollama:gpt-oss:20b-cloud | v3 | 0.0 | 0.9 | 6 | 1024 | 1.00 | 0.85 | 0.85 | 1690.372 |
| final_gemini | gemini:gemini-2.5-flash | v3 | 0.0 | 0.9 | 6 | 1024 | 0.06 | 0.11 | 0.12 | 31428.608 |
| final_temp07 | ollama:gpt-oss:120b-cloud | v3 | 0.7 | 0.9 | 6 | 1024 | 1.00 | 0.85 | 0.91 | 943.984 |

## Antes/depois

| Métrica | Sprints 1/2 (versão original) | Sprint 04 — it1_prompt_v1 (1ª iteração) | Sprint 04 — final_temp07 (última) |
|---|---|---:|---:|
| Faithfulness (manual) | não medida | 1.00 | 1.00 |
| Answer relevancy | não medida | 0.69 | 0.85 |
| Qualidade do contexto recuperado (hit da fonte esperada) | sem recuperação (dados fixos no prompt) | 83% | 100% |
| Trecho com a resposta entre os recuperados (hit do trecho) | sem recuperação | 78% | 100% |
| Recusa indevida (pergunta respondível recusada) | não medida | 17% | 6% |
| Respostas com citação de fonte | 0% (não citava) | 100% | 100% |
| Recusa correta fora do contexto | não medida | 100% | 100% |
