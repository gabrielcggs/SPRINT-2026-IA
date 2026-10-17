# Interface web — ChargeGrid Intelligence (Streamlit)

Interface do RAG com **citação visível**: cada resposta mostra, em "Fontes citadas", o
documento, a página, a seção, a relevância e o trecho recuperado.

## Executar

Na raiz do projeto:

```bash
pip install -r requirements.txt
cp .env.example .env                    # preencha OLLAMA_API_KEY
python scripts/gerar_base_conhecimento.py   # cria os PDFs simulados (ou copie seus PDFs para data/knowledge_base/)
python scripts/ingest.py                    # indexa no ChromaDB persistente (data/chroma_db/)
streamlit run app/streamlit_app.py
```

Abre em http://localhost:8501.

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
