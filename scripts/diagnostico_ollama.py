"""Diagnostico da conexao com a Ollama (chave, chat e embeddings, separados).

    python scripts/diagnostico_ollama.py

Mostra DE ONDE a chave vem (shell x .env), sem imprimir a chave inteira, e testa:
  1) chat   com o modelo de geracao
  2) embeds com o nomic-embed-text
O par de resultados indica a causa:
  chat OK  + embeds 401      -> a nuvem nao libera embeddings para a conta: use Ollama local nos embeddings
  chat 401 + embeds 401      -> chave invalida, revogada ou com espaco/aspas no .env
  embeds 404 / "not found"   -> o modelo de embeddings nao existe nesse servidor
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import dotenv_values  # noqa: E402


def mascara(chave: str | None) -> str:
    if not chave:
        return "(vazia)"
    return f"{chave[:2]}…{chave[-4:]} ({len(chave)} caracteres)"


def main() -> None:
    env_path = ROOT / ".env"
    print(f"Projeto: {ROOT}")
    print(f".env existe: {env_path.exists()}")

    do_shell = os.environ.get("OLLAMA_API_KEY")
    do_arquivo = dotenv_values(env_path).get("OLLAMA_API_KEY") if env_path.exists() else None
    print(f"\nOLLAMA_API_KEY no SHELL : {mascara(do_shell)}")
    print(f"OLLAMA_API_KEY no .env  : {mascara(do_arquivo)}")
    if do_shell and do_arquivo and do_shell != do_arquivo:
        print("  ⚠ As duas sao DIFERENTES. O projeto agora usa a do .env (override=True), "
              "mas outros scripts antigos podem usar a do shell. Remova a antiga do ~/.zshrc / ~/.zprofile.")
    if do_arquivo and (do_arquivo != do_arquivo.strip() or any(c in do_arquivo for c in "\"' ")):
        print("  ⚠ A chave no .env tem espaco ou aspas. Deixe assim: OLLAMA_API_KEY=abc123 (sem aspas, sem espaco).")
    if do_arquivo and do_arquivo.upper().startswith("SUA_CHAVE"):
        print("  ⚠ A chave no .env ainda e o placeholder.")

    from rag import config  # carrega o .env com override=True

    chave = os.environ.get("OLLAMA_API_KEY", "")
    base_url = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
    emb_url = os.getenv("RAG_EMBEDDING_BASE_URL") or base_url
    print(f"\nChave EM USO pelo projeto: {mascara(chave)}")
    print(f"Servidor de geracao : {base_url}")
    print(f"Servidor de embeds  : {emb_url}")
    print(f"Modelo de geracao   : {config.llm_model()}")
    print(f"Modelo de embeddings: {config.embedding_model()}")

    from ollama import Client, ResponseError

    def cliente(url: str) -> Client:
        local = any(h in url for h in ("localhost", "127.0.0.1"))
        headers = {} if local or not chave else {"Authorization": f"Bearer {chave}"}
        return Client(host=url, headers=headers)

    resultados = {}

    print("\n[1/2] Chat...")
    try:
        r = cliente(base_url).chat(model=config.llm_model(), messages=[{"role": "user", "content": "Diga apenas: ok"}],
                                   options={"num_predict": 8})
        resultados["chat"] = "OK"
        print("  OK")
    except ResponseError as e:
        resultados["chat"] = f"erro {e.status_code}: {e.error}"
        print(f"  FALHOU -> {resultados['chat']}")
    except Exception as e:  # noqa: BLE001
        resultados["chat"] = f"{type(e).__name__}: {e}"
        print(f"  FALHOU -> {resultados['chat']}")

    print("[2/2] Embeddings...")
    try:
        r = cliente(emb_url).embed(model=config.embedding_model(), input=["teste"])
        resultados["embed"] = f"OK ({len(r['embeddings'][0])} dimensoes)"
        print(f"  {resultados['embed']}")
    except ResponseError as e:
        resultados["embed"] = f"erro {e.status_code}: {e.error}"
        print(f"  FALHOU -> {resultados['embed']}")
    except Exception as e:  # noqa: BLE001
        resultados["embed"] = f"{type(e).__name__}: {e}"
        print(f"  FALHOU -> {resultados['embed']}")

    print("\n=== Leitura ===")
    chat_ok = resultados["chat"] == "OK"
    embed_ok = resultados["embed"].startswith("OK")
    if chat_ok and embed_ok:
        print("Tudo certo. Rode: python scripts/ingest.py --reset")
    elif chat_ok and "401" in resultados["embed"]:
        print("A chave funciona no chat mas a nuvem recusa embeddings.\n"
              "Solucao: instale o Ollama no Mac (https://ollama.com/download), rode `ollama pull nomic-embed-text`\n"
              "e coloque no .env:  RAG_EMBEDDING_BASE_URL=http://localhost:11434   (a geracao continua na nuvem).")
    elif chat_ok and ("404" in resultados["embed"] or "not found" in resultados["embed"].lower()):
        print("O modelo de embeddings nao existe na nuvem. Use Ollama local (veja acima) com `ollama pull nomic-embed-text`.")
    elif not chat_ok and "401" in resultados["chat"]:
        print("A chave foi recusada ate no chat: confira se foi copiada inteira, se nao foi revogada\n"
              "e se nao tem espaco/aspas no .env. Gere outra chave no site da Ollama se precisar.")
    else:
        print("Resultado inesperado; mande esta saida (a chave aparece mascarada) para analise.")


if __name__ == "__main__":
    main()
