"""
Executa os 5 casos obrigatórios do modelo de teste e gera relatório Markdown.

Uso (na raiz do projeto):
    python src/run_tests.py
"""

import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chatbot import create_chatbot

TEST_CASES = [
    {
        "id": 1,
        "categoria": "Factual",
        "pergunta": "Quanto gastei este mês em recarga?",
        "esperado": "Consumo ~847 kWh e custo ~R$ 753,83 (junho/2026)",
    },
    {
        "id": 2,
        "categoria": "Factual",
        "pergunta": "Qual carregador está disponível agora?",
        "esperado": "CG-01 e CG-04 disponíveis; CG-02 em uso; CG-03 em manutenção",
    },
    {
        "id": 3,
        "categoria": "Instrução",
        "pergunta": "Quanto custa carregar meu veículo no CG-02?",
        "esperado": "Tarifa R$ 0,89/kWh e estimativa de custo",
    },
    {
        "id": 4,
        "categoria": "Factual",
        "pergunta": "Meu carregamento no CG-02 terminou?",
        "esperado": "CG-02 em uso (~68%), carregamento não concluído",
    },
    {
        "id": 5,
        "categoria": "Factual",
        "pergunta": "Existe sobrecarga energética agora no condomínio?",
        "esperado": "38/50 kW, sem sobrecarga",
    },
]

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "docs" / "testes" / "resultados_testes_sprint02.md"


def avaliar_qualitativa(resposta, case_id):
    texto = resposta.lower()
    if texto.startswith("erro da api"):
        return "Inadequada"

    checks = {
        1: ["847", "753"],
        2: ["cg-01", "cg-04", "dispon"],
        3: ["0,89", "0.89", "19,58", "22 kW", "kWh"],
        4: ["68", "uso", "andamento", "carreg"],
        5: ["38", "50", "sobrecarga", "sem"],
    }
    if case_id in checks:
        hits = sum(1 for kw in checks[case_id] if kw in texto)
        if hits >= 2:
            return "Adequada"
        if hits == 1:
            return "Parcialmente adequada"
    return "Parcialmente adequada" if len(resposta) > 40 else "Inadequada"


def main():
    chatbot = create_chatbot()
    linhas = [
        "# Resultados dos Testes — Sprint 2",
        "",
        f"Data da execução: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        "| # | Categoria | Pergunta | Resposta Obtida | Avaliação |",
        "|---|-----------|----------|-----------------|-----------|",
    ]
    
    encontrou_erro_api = False

    for index, caso in enumerate(TEST_CASES):
        chatbot.reset()
        resultado = chatbot.chat(caso["pergunta"])
        resposta = resultado["resposta"].replace("\n", " ").replace("|", "/")
        if resposta.startswith("Erro da API"):
            encontrou_erro_api = True
        avaliacao = avaliar_qualitativa(resposta, caso["id"])
        linhas.append(
            f"| {caso['id']} | {caso['categoria']} | {caso['pergunta']} | {resposta} | {avaliacao} |"
        )
        print(f"[{caso['id']}] {avaliacao}: {caso['pergunta']}")
        if index < len(TEST_CASES) - 1:
            time.sleep(12)
    
    linhas.extend(
        [
            "",
            "## Observações",
            "- Avaliação automática é indicativa; revise manualmente antes da entrega.",
            "- Ajuste o SYSTEM_PROMPT em `src/chatbot.py` se algum caso ficar inadequado.",
        ]
    )
    
    if encontrou_erro_api and OUTPUT_PATH.exists():
        print("\nA API retornou erro em pelo menos um caso.")
        print("O relatorio anterior foi mantido para nao substituir resultados validos por erro de cota.")
        print(f"Relatorio mantido em: {OUTPUT_PATH}")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(linhas), encoding="utf-8")
    print(f"\nRelatório salvo em: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
