# Interface web — ChargeGrid Intelligence

Interface do RAG com **citação visível**: cada resposta mostra, em "Fontes citadas", o
documento, a página, a seção, a relevância e o trecho recuperado.

## Executar

Na raiz do projeto:

```bash
pip install -r requirements.txt
cp .env.example .env                    # preencha OLLAMA_API_KEY
ollama pull nomic-embed-text            # embeddings locais
python scripts/ingest.py                # indexa a base (data/knowledge_base/) no ChromaDB (data/chroma_db/)
python app/web_server.py                # interface HTML/CSS/JS em http://127.0.0.1:8000
```

Alternativa em Streamlit: `streamlit run app/streamlit_app.py` (http://localhost:8501).

Arquivos da interface principal: `web_server.py` (FastAPI: `/api/config`, `/api/chat`) e `web/` (`index.html`, `style.css`, `app.js`).
Cada resposta traz chips `[S1]` clicaveis que abrem, no painel "Evidencia", o documento, a pagina, a secao, a
relevancia e o trecho; a aba "Recuperadas" mostra tudo o que a busca trouxe, inclusive quando o assistente recusa.

## O que a interface faz

- Chat com memória curta (as 3 últimas trocas) para perguntas de seguimento.
- Barra lateral: provedor, modelo, versão do prompt (v1/v2/v3), `k`, relevância mínima,
  `temperature`, `top_p` e `max_tokens`.
- **Comparar (multi-provider)**: duas variantes (modelo + prompt) respondem sobre a
  mesma recuperação, lado a lado. É o item bônus da Sprint 04.
- Perguntas fora da base, jailbreak e intervenção elétrica são recusadas (aviso amarelo).
- "Reindexar base" refaz o índice depois de você trocar os PDFs.

## Problemas comuns

| Sintoma | Causa | Solução |
|---|---|---|
| "A coleção ... está vazia" | Não rodou a ingestão | `python scripts/ingest.py` |
| "OLLAMA_API_KEY nao definida" | `.env` ausente | Copie `.env.example` e preencha |
| Tudo é recusado | `RAG_MIN_SCORE` alto demais | `python scripts/calibrar_limiar.py` |

## Interface HTML/CSS/JS (principal)

```bash
python app/web_server.py     # http://127.0.0.1:8000  (WEB_HOST / WEB_PORT mudam o endereco)
```

Backend FastAPI (`web_server.py`) + frontend sem build em `web/` (`index.html`, `style.css`, `app.js`).
Mostra a resposta com chips `[S1]` clicaveis, o painel de evidencia (trechos citados e recuperados, com
medidor de relevancia), ajustes (modelo, prompt, k, relevancia minima, temperature, top_p, max_tokens) e
modo comparar duas variantes. Se o indice nao existir, a tela explica como cria-lo.

A versao em Streamlit (`streamlit run app/streamlit_app.py`) continua disponivel.
