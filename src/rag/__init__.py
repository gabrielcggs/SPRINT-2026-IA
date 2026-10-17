"""Pipeline RAG do ChargeGrid Intelligence (Sprint 04).

Fluxo: PDFs -> loader -> chunking -> embeddings -> ChromaDB persistente
       -> retriever -> sanitizacao -> prompt RAG versionado -> LLM -> resposta com fontes.
"""
