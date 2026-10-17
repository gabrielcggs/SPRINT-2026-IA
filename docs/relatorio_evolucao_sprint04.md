# Relatório de Evolução do Projeto — Sprint 04

**ChargeGrid Intelligence · FIAP × GoodWe Brasil · Prompt and Artificial Intelligence · 2026.2**

> RASCUNHO para virar o PDF de até 5 páginas (`docs/relatorio_evolucao_sprint04.pdf`).
> Preencha os trechos marcados com os números de `python evals/gerar_tabelas.py`.
> Não use o nome `relatorio_evolucao.pdf`: ele está no `.gitignore` e não iria para o repositório.

## 1. Resumo da evolução

- **Sprints 1 e 2:** respostas manuais em Python (`resposta_local`) e histórico simples; os dados dos carregadores ficavam escritos no código.
- **Sprint 03:** refatoração para LangChain LCEL com prompt versionado, memória por sessão, saída estruturada (Pydantic v2) e guardrails; os dados ainda ficavam fixos dentro do prompt.
- **Sprint 04:** RAG **medido e com interface**. A base passou a ser de PDFs (5 documentos), indexados em ChromaDB persistente com `nomic-embed-text`; as respostas usam só o contexto recuperado, citam documento, página e seção, e foram avaliadas em <!-- N --> iterações. Interface web em Streamlit com as fontes visíveis.

## 2. Pipeline RAG

- **Fluxo:** PyMuPDFLoader → RecursiveCharacterTextSplitter → nomic-embed-text → ChromaDB (cosseno, persistente) → retriever top-k → sanitização → prompt RAG versionado → LLM → resposta com `[S#]`.
- **Chunking:** `chunk_size=700`, `chunk_overlap=100`, por seção, com cabeçalho `[documento | seção]`. Por quê: manter cada regra inteira dentro de um chunk e permitir citar a seção exata. Trade-off: chunks menores citam melhor mas perdem contexto. <!-- cite a comparação medida entre configurações, se o grupo rodou -->
- **Base de conhecimento:** manual ChargeGrid, manual EV ChargeOps, regimento condominial, FAQ e tabela tarifária (simulados, identificados como tal).
- **Segurança:** bloqueio de entrada maliciosa, corte por relevância, sanitização de instruções dentro de documentos, prompt v3 (contexto como dado) e citação validada.

## 3. Comparativo antes/depois (obrigatório)

<!-- COLE AQUI a tabela "Antes/depois" de python evals/gerar_tabelas.py e,
     abaixo dela, a "Evolução por iteração" (mínimo 2 iterações com ganho). -->

Fonte dos números: `evals/results/*.json`. Métrica: <!-- RAGAS (versão X) ou rubrica manual 0–1, justificada em docs/relatorio_rag.md §6 -->.

## 4. Problemas encontrados e soluções

1. **Listas numeradas viravam "seções".** O detector de títulos tratava "1. Abra o app" como seção e quebrava a citação. Decisão: listas com "Passo 1 –" e títulos numerados só em linha própria.
2. **Filtro anti-injection x texto legítimo.** Frases como "não ignore as regras" casariam com o padrão de ataque. Decisão: redigir a base sem elas e testar automaticamente que nenhum PDF da base aciona o filtro.
3. **Validador de escopo da Sprint 03 não filtrava.** ~1000 termos genéricos aprovavam quase tudo. Decisão: recusa por limiar de relevância + prompt; mantidos só os termos de segurança.
4. **JSON truncado com `max_tokens=512`.** Decisão: 1024 no RAG.
<!-- Acrescente os problemas reais das iterações do grupo. -->

## 5. Equipe e divisão de trabalho

| Nome | RM | Tarefa principal |
|---|---:|---|
| Gabriel Camarosani Gouvea Goncalves da Silva | 569189 | <!-- preencher --> |
| Gustavo Lima Andrade Santos | 571709 | <!-- preencher --> |
| Lucas Seiji Hummel | 569673 | <!-- preencher --> |
| Pedro Souza Castro | 569311 | <!-- preencher --> |
| Bruno Yudi Moritaka Kanashiro | 571776 | <!-- preencher --> |
| Lucas Barreto Santana | 573149 | <!-- preencher --> |

Sugestão de divisão (ajuste ao que cada um fez de verdade; o professor confere os commits): base de conhecimento · chunking/ingestão · retriever e prompt · segurança e guardrails · avaliação e relatórios · interface.
