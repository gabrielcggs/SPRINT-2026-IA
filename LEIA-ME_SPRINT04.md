# Entrega Sprint 04 — como aplicar no seu projeto

Extraia o zip **na raiz do projeto** (a pasta que tem `src/`, `docs/`, `evals/`). Ele mantém a estrutura de pastas.

## Arquivos que já existem e serão SUBSTITUÍDOS (confira o diff antes de commitar)

| Arquivo | O que mudou |
|---|---|
| `requirements.txt` | + chromadb, langchain-chroma, langchain-community, text-splitters, pymupdf, reportlab, streamlit, ragas |
| `.env.example` | + variáveis `RAG_*` (modelo, k, limiar, chunking) |
| `.gitignore` | + `data/chroma_db/` |
| `README.md` | reescrito para a Sprint 04 (integrantes mantidos) |
| `src/schemas/consulta_recarga.py` | aceita qualquer `CG-NN` (antes só CG-01..04) e ganhou o campo `fontes` |
| `docs/relatorio_modelos.md` | agora é o da Sprint 04 (o da Sprint 03 fica no histórico do Git) |
| `prompts/version_history.md` | + tabela das versões do prompt RAG (sem números inventados) |

## Arquivos NOVOS

- `src/rag/`: `config.py`, `ingest.py`, `llm.py`, `prompt_rag.py`, `pipeline.py` (+ `loader`, `chunking`, `embeddings`, `vector_store`, `retriever`, `security`, `__init__` já incluídos)
- `src/main_rag.py` (chat no terminal)
- `app/streamlit_app.py`, `app/README.md`
- `scripts/gerar_base_conhecimento.py`, `scripts/ingest.py`, `scripts/calibrar_limiar.py`
- `data/knowledge_base/*.pdf` (5 PDFs simulados)
- `evals/rag_eval_set.json`, `evals/run_rag_eval.py`, `evals/gerar_tabelas.py`
- `tests/test_rag_offline.py`
- `docs/relatorio_rag.md`, `docs/relatorio_evolucao_sprint04.md`

Não foi alterado: `src/chain/`, `src/chatbot.py`, `src/main.py`, `src/guardrails/`, `prompts/system_prompt_v*.md` (Sprint 03 segue funcionando).

## Ordem para rodar

```bash
pip install -r requirements.txt
cp .env.example .env            # coloque OLLAMA_API_KEY
pytest -q                       # 27 testes, sem rede
python scripts/ingest.py        # precisa da chave (embeddings na Ollama Cloud)
python scripts/calibrar_limiar.py   # ajuste RAG_MIN_SCORE no .env
streamlit run app/streamlit_app.py
python evals/run_rag_eval.py --nome it1_prompt_v1 --prompt v1
python evals/run_rag_eval.py --nome it2_prompt_v2 --prompt v2
python evals/run_rag_eval.py --nome it3_prompt_v3 --prompt v3
python evals/gerar_tabelas.py
```

Depois cole as tabelas nos `docs/*.md`, gere o PDF (até 5 páginas) como
`docs/relatorio_evolucao_sprint04.pdf` e commite `evals/results/`.

## O que eu NÃO consegui testar (sem a chave da Ollama Cloud)

- Qualidade real do `nomic-embed-text` e o valor certo de `RAG_MIN_SCORE` (o 0.45 é um palpite: calibre).
- Chamadas reais ao `gpt-oss`, e o fallback `--metrica ragas` (escrito para ragas>=0.2, não executado).
- Os provedores `openai`, `gemini` e `anthropic` (código escrito, não executado).
Testado: PDF -> chunks -> ChromaDB em disco, retriever, citação, recusa, anti-injection, prompts, modo multi-provider,
runner de avaliação, geração de tabelas e a interface Streamlit, tudo com embedding lexical e LLM falso.

Apague este arquivo antes de commitar.
