import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chatbot import create_chatbot
from chain.builder import token_counter


MODELS = [
    os.getenv("OLLAMA_MODEL", "qwen3:8b"),
    os.getenv("OLLAMA_MODEL_2", "llama3.2:3b"),
]


def run_model(model, cases):
    chatbot = create_chatbot(model=model)
    results = []

    for case in cases:
        session_id = f"{model}-{case['id']}"
        start = time.perf_counter()
        result = chatbot.chat(case["pergunta"], session_id)
        elapsed = round((time.perf_counter() - start) * 1000, 2)

        results.append({
            "id": case["id"],
            "modelo": model,
            "categoria": case["categoria"],
            "pergunta": case["pergunta"],
            "resposta": result.get("resposta", ""),
            "latency_ms": result.get("latency_ms", elapsed),
            "tokens_input": result.get(
                "tokens_input", token_counter(case["pergunta"])
            ),
            "structured_valid": result.get("structured_valid", False),
            "avaliacao": "preencher",
            "justificativa": "Preencher após revisão qualitativa.",
        })

    return results


def main():
    cases = json.loads(
        (ROOT / "evals" / "eval_set.json").read_text(encoding="utf-8")
    )

    all_results = []
    for model in MODELS:
        print(f"Executando avaliação com {model}...")
        all_results.extend(run_model(model, cases))

    output = ROOT / "evals" / "model_comparison.json"
    output.write_text(
        json.dumps(all_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Resultados salvos em {output}")


if __name__ == "__main__":
    main()
