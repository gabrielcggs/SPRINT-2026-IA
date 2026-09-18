import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chatbot import create_chatbot


def main():
    chatbot = create_chatbot()
    
    print("=" * 50)
    print("  ChargeGrid Intelligence — GoodWe EV Challenge 2026")
    print("=" * 50)
    print("Digite sua pergunta (ou 'sair' para encerrar, 'limpar' para novo diálogo)\n")
    
    while True:
        pergunta = input("Você: ").strip()
        
        if pergunta.lower() == "sair":
            print("\nEncerrando ChargeGrid Intelligence. Até logo!")
            break
        
        if pergunta.lower() == "limpar":
            chatbot.reset()
            print("\n[Histórico limpo — nova conversa iniciada]\n")
            continue
        
        resultado = chatbot.chat(pergunta)
        print(f"\nChargeGrid: {resultado['resposta']}\n")


if __name__ == "__main__":
    main()
