# ChargeGrid Intelligence - Sprint 04

Projeto FIAP x GoodWe Brasil para um chatbot de recarga de veiculos eletricos.

A Sprint 04 evolui o projeto para um **RAG medido, confiavel e utilizavel**: base de PDFs em
ChromaDB persistente (`nomic-embed-text`), respostas apenas com o contexto recuperado e
**citacao de fonte**, avaliacao por iteracao (RAGAS ou rubrica manual) e **interface web**
(Streamlit). O chatbot LCEL da Sprint 03 continua em `src/chain/` e `src/chatbot.py`.

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

O projeto nao usa modelo local e nao precisa baixar nada pelo Ollama. A geracao e os embeddings
usam a **Ollama Cloud** (`OLLAMA_API_KEY` em variavel de ambiente):

- geracao: `gpt-oss:120b-cloud` (comparacao: `gpt-oss:20b-cloud`)
- embeddings: `nomic-embed-text`
- opcional (bonus multi-provider): `openai`, `gemini` ou `anthropic`, veja `src/rag/llm.py`

## Instalar

```bash
pip install -r requirements.txt
cp .env.example .env     # preencha OLLAMA_API_KEY (o .env esta no .gitignore)
```

## Rodar o RAG (Sprint 04)

```bash
python scripts/gerar_base_conhecimento.py   # PDFs simulados em data/knowledge_base/
python scripts/ingest.py                    # indexa no ChromaDB (data/chroma_db/)
python scripts/calibrar_limiar.py           # sugere RAG_MIN_SCORE para o .env
streamlit run app/streamlit_app.py          # interface web (http://localhost:8501)
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
- `app/`: interface Streamlit + README de execucao.
- `evals/`: `rag_eval_set.json`, `run_rag_eval.py`, `gerar_tabelas.py` e `results/` por iteracao. (`run_evals.py` e `compare_models.py` sao da Sprint 03.)
- `scripts/`: geracao da base, ingestao e calibracao do limiar.
- `docs/`: `relatorio_rag.md`, `relatorio_modelos.md`, `relatorio_evolucao_sprint04.md` (+ PDF da entrega).
- `prompts/`, `src/chain/`, `src/guardrails/`, `src/schemas/`: Sprints 02 e 03.

## Guardrails do RAG

Entrada maliciosa bloqueada antes da busca; sem trecho relevante o sistema recusa sem chamar o
modelo; frases de comando dentro dos PDFs sao removidas; o prompt v3 trata o contexto como dado,
proibe inventar especificacoes e exige citacao `[S#]` validada contra os trechos enviados.
