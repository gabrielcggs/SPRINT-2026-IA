# ChargeGrid Intelligence - Sprint 04

Projeto FIAP x GoodWe Brasil para um chatbot de recarga de veiculos eletricos.

A Sprint 04 evolui o projeto para um **RAG medido, confiavel e utilizavel**: base de PDFs em
ChromaDB persistente (`nomic-embed-text`), respostas apenas com o contexto recuperado e
**citacao de fonte**, busca hibrida (embeddings + BM25), avaliacao por iteracao (rubrica manual
documentada) e **interface web** (HTML/CSS/JS sobre FastAPI; Streamlit como alternativa). O chatbot LCEL da Sprint 03 continua em `src/chain/` e `src/chatbot.py`.

## Integrantes

| Nome | RM |
|---|---:|
| Gabriel Camarosani Gouvea Goncalves da Silva | 569189 |
| Gustavo Lima Andrade Santos | 571709 |
| Lucas Seiji Hummel | 569673 |
| Pedro Souza Castro | 569311 |
| Bruno Yudi Moritaka Kanashiro | 571776 |
| Lucas Barreto Santana | 573149 |

## Como o modelo funciona

- **Geracao:** Ollama Cloud (`OLLAMA_API_KEY` no `.env`): `gpt-oss:120b-cloud` (comparacao: `gpt-oss:20b-cloud`).
- **Embeddings:** `nomic-embed-text` rodando no **Ollama local** (`ollama pull nomic-embed-text`, sem chave).
  Em algumas contas a Ollama Cloud recusa `/api/embed` com 401 mesmo com a chave valida para chat; por isso o
  `.env.example` aponta os embeddings para `http://localhost:11434`.
- **Opcional (bonus multi-provider):** `openai`, `gemini` ou `anthropic`, veja `src/rag/llm.py`.

## Instalar

```bash
pip install -r requirements.txt
cp .env.example .env     # preencha OLLAMA_API_KEY (o .env esta no .gitignore)
ollama pull nomic-embed-text   # embeddings locais (Ollama instalado e aberto)
```

## Rodar o RAG (Sprint 04)

```bash
python scripts/gerar_base_conhecimento.py   # PDFs simulados em data/knowledge_base/
python scripts/ingest.py                    # indexa no ChromaDB (data/chroma_db/)
python scripts/calibrar_limiar.py           # mostra os scores por pergunta (dentro/fora do contexto)
RAG_HIBRIDO=1 python scripts/diagnostico_recuperacao.py   # posicao do trecho que responde, por caso
python app/web_server.py                     # interface HTML/CSS/JS (http://127.0.0.1:8000)
streamlit run app/streamlit_app.py          # alternativa em Streamlit (http://localhost:8501)
python src/main_rag.py                      # ou chat no terminal
```

## Avaliar (uma execucao = uma iteracao)

```bash
python evals/run_rag_eval.py --nome it1_prompt_v1 --prompt v1 --descricao "baseline"
python evals/run_rag_eval.py --nome it2_prompt_v2 --prompt v2 --descricao "citacao + recusa"
python evals/run_rag_eval.py --nome it3_prompt_v3 --prompt v3 --descricao "XML + anti-injection"
python evals/gerar_tabelas.py --saida docs/tabelas_sprint04.md
```

Os resultados ficam em `evals/results/` (versione no Git: sao a evidencia das iteracoes).
Use `--metrica ragas` para tentar RAGAS; sem ele, vale a rubrica manual documentada.

## Testes

```bash
pytest -q          # tests/test_rag_offline.py roda sem rede e sem chave
```

## Estrutura

- `data/knowledge_base/`: PDFs da base de conhecimento (simulados).
- `src/rag/`: `loader`, `chunking`, `embeddings`, `vector_store`, `retriever`, `prompt_rag` (versionado), `security`, `pipeline`, `llm`, `ingest`, `config`.
- `app/`: interface web (`web_server.py` + `web/` em HTML/CSS/JS puro), alternativa Streamlit e README de execucao.
- `evals/`: `rag_eval_set.json`, `run_rag_eval.py`, `gerar_tabelas.py` e `results/` por iteracao. (`run_evals.py` e `compare_models.py` sao da Sprint 03.)
- `scripts/`: geracao da base, ingestao e calibracao do limiar.
- `docs/`: `relatorio_rag.md`, `relatorio_modelos.md`, `relatorio_evolucao_sprint04.md` (+ PDF da entrega).
- `prompts/`, `src/chain/`, `src/guardrails/`, `src/schemas/`: Sprints 02 e 03.

## Guardrails do RAG

Entrada maliciosa bloqueada antes da busca; sem trecho relevante o sistema recusa sem chamar o
modelo; frases de comando dentro dos PDFs sao removidas; o prompt v3 trata o contexto como dado,
proibe inventar especificacoes e exige citacao `[S#]` validada contra os trechos enviados.

## Configuracao final medida (iteracao 6)

```bash
RAG_EMBEDDING_BASE_URL=http://localhost:11434
RAG_HIBRIDO=1          # embeddings + BM25 (RRF)
RAG_K=6
RAG_MIN_SCORE=0.55
```

Relatorios: `docs/relatorio_rag.md`, `docs/relatorio_modelos.md` e `docs/relatorio_evolucao_sprint04.pdf`.
