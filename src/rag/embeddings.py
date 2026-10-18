"""Embeddings (Aula 05).

Padrao do projeto: ``nomic-embed-text`` servido pela Ollama Cloud.
O provedor ``hash`` existe apenas para testes automatizados e demos offline
(nao deve ser usado nas avaliacoes que vao para o relatorio).
"""
from __future__ import annotations

import hashlib
import math
import os
import re
import unicodedata

from langchain_core.embeddings import Embeddings

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "e", "ou", "que", "qual", "quais", "como", "para", "por", "com", "se",
    "ao", "aos", "eu", "meu", "minha", "ser", "ter", "ha", "sao", "foi", "esta", "estao",
    "tem", "pode", "posso", "quando", "onde", "quanto", "quanta", "mais", "mas", "ja",
}


def _sem_acentos(texto: str) -> str:
    norm = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in norm if not unicodedata.combining(c))


class HashingEmbeddings(Embeddings):
    """Embedding lexical deterministico (bag-of-words com hashing). So para testes."""

    def __init__(self, dim: int = 1024):
        self.dim = dim

    def _tokens(self, texto: str) -> list[str]:
        tokens = re.findall(r"[a-z0-9]+", _sem_acentos(texto.lower()))
        return [t for t in tokens if t not in STOPWORDS]

    def _embed(self, texto: str) -> list[float]:
        vetor = [0.0] * self.dim
        tokens = self._tokens(texto)
        for termo in tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]:
            h = int.from_bytes(hashlib.blake2b(termo.encode(), digest_size=8).digest(), "big")
            vetor[h % self.dim] += 1.0 if (h >> 63) & 1 else -1.0
        norma = math.sqrt(sum(v * v for v in vetor)) or 1.0
        return [v / norma for v in vetor]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class PrefixedEmbeddings(Embeddings):
    """Aplica os prefixos recomendados pelo nomic-embed-text.

    O modelo foi treinado com "search_document: " para os textos indexados e
    "search_query: " para as perguntas; usar os prefixos melhora a busca.
    """

    def __init__(self, base: Embeddings, query_prefix: str, doc_prefix: str):
        self.base = base
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.base.embed_documents([self.doc_prefix + t for t in texts])

    def embed_query(self, text: str) -> list[float]:
        return self.base.embed_query(self.query_prefix + text)


def build_embeddings(provider: str | None = None, model: str | None = None) -> Embeddings:
    provider = (provider or os.getenv("RAG_EMBEDDING_PROVIDER", "ollama")).lower()
    model = model or os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text")

    if provider == "hash":
        return HashingEmbeddings()

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        # RAG_EMBEDDING_BASE_URL permite embeddings num Ollama LOCAL
        # (http://localhost:11434, apos `ollama pull nomic-embed-text`) enquanto a
        # geracao continua na Ollama Cloud. Em servidor local nao precisa de chave.
        base_url = os.getenv("RAG_EMBEDDING_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
        local = any(h in base_url for h in ("localhost", "127.0.0.1", "0.0.0.0"))
        api_key = os.getenv("OLLAMA_API_KEY", "")
        if not api_key and not local:
            raise RuntimeError(
                "OLLAMA_API_KEY nao definida. Copie .env.example para .env e preencha a chave."
            )
        client_kwargs = {"headers": {"Authorization": f"Bearer {api_key}"}} if (api_key and not local) else {}
        base = OllamaEmbeddings(model=model, base_url=base_url, client_kwargs=client_kwargs)
        if model.startswith("nomic"):
            return PrefixedEmbeddings(base, "search_query: ", "search_document: ")
        return base

    raise ValueError(f"Provedor de embeddings desconhecido: {provider!r}")
