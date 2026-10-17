"""Fabrica de LLMs com varios provedores (bonus multi-provider).

Provedores: ``ollama`` (padrao, Ollama Cloud), ``openai``, ``gemini``, ``anthropic``.
Os pacotes dos provedores extras sao importados so quando usados:

    pip install langchain-openai          # provider=openai
    pip install langchain-google-genai    # provider=gemini   (GOOGLE_API_KEY)
    pip install langchain-anthropic       # provider=anthropic (ANTHROPIC_API_KEY)
"""
from __future__ import annotations

import os

PROVEDORES = ("ollama", "openai", "gemini", "anthropic")


def build_llm(
    provider: str = "ollama",
    model: str | None = None,
    temperature: float = 0.0,
    top_p: float = 0.9,
    max_tokens: int = 1024,
):
    provider = (provider or "ollama").lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        api_key = os.getenv("OLLAMA_API_KEY", "")
        if not api_key:
            raise RuntimeError("OLLAMA_API_KEY nao definida (.env).")
        return ChatOllama(
            model=model or os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud"),
            base_url=os.getenv("OLLAMA_BASE_URL", "https://ollama.com"),
            temperature=temperature,
            top_p=top_p,
            num_predict=max_tokens,
            reasoning=False,
            client_kwargs={"headers": {"Authorization": f"Bearer {api_key}"}},
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        if not model:
            raise ValueError("Informe o modelo OpenAI (ex.: RAG_LLM_MODEL).")
        return ChatOpenAI(model=model, temperature=temperature, top_p=top_p, max_tokens=max_tokens)

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not model:
            raise ValueError("Informe o modelo Gemini (ex.: RAG_LLM_MODEL).")
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_tokens,
            google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if not model:
            raise ValueError("Informe o modelo Anthropic (ex.: RAG_LLM_MODEL).")
        # Modelos recentes da Anthropic nao aceitam temperature e top_p juntos: so temperature.
        return ChatAnthropic(model=model, temperature=temperature, max_tokens=max_tokens)

    raise ValueError(f"Provedor desconhecido: {provider!r}. Opcoes: {', '.join(PROVEDORES)}")
