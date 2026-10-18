# Relatório de Evolução do Projeto — Sprint 04

**ChargeGrid Intelligence · FIAP × GoodWe Brasil · Prompt and Artificial Intelligence · 2026.2**

## 1. Resumo da evolução

- **Sprints 1 e 2:** respostas manuais em Python e histórico simples; os dados dos carregadores ficavam escritos no código.
- **Sprint 03:** refatoração para LangChain LCEL com prompt versionado, memória por sessão, saída estruturada (Pydantic v2) e guardrails; os dados ainda ficavam fixos no prompt.
- **Sprint 04:** RAG **medido e com interface**. Base de 5 PDFs indexados em ChromaDB persistente com `nomic-embed-text`; busca híbrida (embeddings + BM25); respostas só com o contexto recuperado, com citação de documento, página e seção; avaliação em 25 casos ao longo de 6 iterações; interface web em HTML, CSS e JavaScript; comparação de 2 modelos e 2 provedores.

## 2. Pipeline RAG

PyMuPDFLoader → RecursiveCharacterTextSplitter (700/100, por seção, com cabeçalho `[documento | seção]`) → `nomic-embed-text` → ChromaDB (cosseno, persistente) → busca híbrida (embeddings + BM25, fusão RRF, k=6) → corte de relevância (0,55) → sanitização → prompt RAG v3 → LLM → resposta com `[S#]` validado.

**Segurança:** bloqueio de entrada maliciosa antes da busca; sanitização de instruções escondidas nos documentos; contexto tratado como dado (prompt v3); citação validada contra os trechos enviados; recusa de risco elétrico, jurídico e financeiro.

**Interface:** FastAPI + HTML/CSS/JS puros. A resposta traz chips `[S1]` clicáveis que abrem o trecho da base, com documento, página, seção e relevância; mostra também o que foi recuperado quando o assistente recusa.

## 3. Comparativo antes/depois

| Métrica | Sprints 1/2 (original) | Sprint 04, 1ª iteração (baseline v1) | Sprint 04, final (iteração 6) |
|---|---|---:|---:|
| Faithfulness (fidelidade ao contexto, 0–1) | não medida | 1.00 | 1.00 |
| Answer relevancy (0–1) | não medida | 0.69 | 0.83 |
| Trecho com a resposta entre os recuperados | sem recuperação (dados fixos no prompt) | 78% | 100% |
| Documento esperado entre os recuperados | sem recuperação | 83% | 100% |
| Perguntas respondíveis recusadas por engano | não medida | 17% | 6% |
| Respostas com citação de fonte | 0% (não citava) | 100% | 100% |
| Recusa correta fora do contexto | não medida | 100% | 100% |

Evolução por iteração (mesmo eval set de 25 casos, mesma rubrica):

| Iter. | Configuração | Faithfulness | Answer relevancy | Contém esperado | Hit fonte | Hit trecho | Recusa correta | Recusa indevida |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | v1 · densa, k=4, chunks 700/100 | 1.00 | 0.69 | 0.83 | 83% | 78% | 100% | 17% |
| 2 | v2 (citação + recusa fixa) | 1.00 | 0.69 | 0.96 | 83% | 78% | 100% | 28% |
| 3 | v3 (XML, anti-injection) | 1.00 | 0.69 | 0.96 | 83% | 78% | 100% | 28% |
| 4 | v3 + chunks 400/60 | 1.00 | 0.69 | 0.96 | 83% | 78% | 100% | 28% |
| 5 | v3 + busca híbrida, k=4 | 1.00 | 0.75 | 0.90 | 94% | 89% | 100% | 17% |
| 6 | v3 + busca híbrida, k=6 | 1.00 | 0.83 | 0.91 | 100% | 100% | 100% | 6% |

- **Iteração 2 (prompt v2):** a citação obrigatória elevou `contém esperado` de 0,83 para 0,96, mas as recusas indevidas subiram de 17% para 28%.
- **Iterações 3 e 4 (prompt v3, chunks de 400):** sem mudança nas métricas. A v3 vale pela segurança; os chunks menores só dobraram a latência.
- **Iterações 5 e 6 (busca híbrida):** o ganho principal. `answer_relevancy` 0,69 → 0,83, trecho certo recuperado em 100% dos casos e recusa indevida 28% → 6%.

Métrica: rubrica manual de 0 a 1 aplicada por LLM juiz (equivalente às definições de faithfulness e answer relevancy do RAGAS), documentada em `docs/relatorio_rag.md`. Números de `evals/results/*.json`.

**Modelos e provedores** (detalhes em `docs/relatorio_modelos.md`): na busca final, `gpt-oss:120b` e `gpt-oss:20b` empataram em recusa indevida (6%) e fidelidade (1,00); o 120b deu respostas mais completas (`contém esperado` 0,91 contra 0,85). Com busca só por embeddings, o Gemini 2.5 Flash ficou abaixo do gpt-oss:120b em fidelidade (0,93 contra 1,00) e foi cerca de 6 vezes mais lento.

**Limitações:** eval set pequeno (18 casos respondíveis; um caso vale 5,6 pontos percentuais); a configuração final foi escolhida olhando as falhas do mesmo eval set (números otimistas); o juiz é o próprio modelo avaliado.

## 4. Problemas encontrados e soluções

1. **Trecho com a resposta fora do top-k.** Com `nomic-embed-text` todos os scores ficavam entre 0,58 e 0,76 e a resposta aparecia nas posições 8 a 18. *Solução:* busca híbrida (BM25 + embeddings) e k=6; recusa indevida de 28% para 6%.
2. **Pergunta curta contaminada pela anterior.** "Quanto custa uma hora de recarga no CG-02?" era tratada como continuação e recebia contexto errado. *Solução:* detectar continuações só por marcadores ("e…", "ele", "isso") ou até 3 palavras; casos de regressão no eval set.
3. **Limiar de relevância não separa dentro/fora do contexto.** Perguntas do mesmo assunto sem resposta na base (preço, garantia) pontuam mais que uma pergunta de futebol. *Solução:* corte conservador (0,55) e recusa pelo prompt v3. As 7 perguntas que deviam ser recusadas foram todas recusadas (entre bloqueio de entrada e prompt).
4. **Embeddings na Ollama Cloud retornaram 401** (o chat funcionava). *Solução:* embeddings no Ollama local e geração na nuvem.
5. **Chave antiga do terminal sobrepunha o `.env`.** *Solução:* `override=True` e script de diagnóstico com chave mascarada.
6. **`hit da fonte` escondia a falha de busca.** *Solução:* nova métrica `hit do trecho`.
7. **Filtro anti-injection e listas numeradas.** Texto legítimo acionava o filtro ou virava "seção"; resolvido ao redigir a base de forma controlada e testar isso automaticamente.

## 5. Grupo

| Nome | RM |
|---|---:|
| Gabriel Camarosani Gouvea Goncalves da Silva | 569189 |
| Gustavo Lima Andrade Santos | 571709 |
| Lucas Seiji Hummel | 569673 |
| Pedro Souza Castro | 569311 |
| Bruno Yudi Moritaka Kanashiro | 571776 |
| Lucas Barreto Santana | 573149 |

Repositório: https://github.com/gabrielcggs/SPRINT-2026-IA
