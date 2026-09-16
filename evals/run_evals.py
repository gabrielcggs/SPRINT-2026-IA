import json
import sys
import time
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chatbot import create_chatbot
from chain.builder import token_counter


def main():
    cases = json.loads((ROOT / "evals" / "eval_set.json").read_text(encoding="utf-8"))
    chatbot = create_chatbot(model=os.getenv("OLLAMA_MODEL", "qwen3:8b"))
    results = []
    for case in cases:
        session_id = f"eval-{case['id']}"
        if case["categoria"] == "memory":
            chatbot.chat("Qual carregador está disponível agora?", session_id)
            chatbot.chat("Qual deles é mais potente?", session_id)
        start = time.perf_counter()
        result = chatbot.chat(case["pergunta"], session_id)
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        answer = result["resposta"]
        results.append({
            **case,
            "resposta": answer,
            "latency_ms": result.get("latency_ms", elapsed),
            "tokens_input": result.get("tokens_input", token_counter(case["pergunta"])),
            "structured_valid": result.get("structured_valid", False),
            "avaliacao": "preencher",
            "justificativa": "Preencher após revisar a resposta."
        })

    output = ROOT / "evals" / "sprint3_results.json"
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resultados salvos em {output}")


if __name__ == "__main__":
    main()
