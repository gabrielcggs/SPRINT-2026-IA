JAILBREAK_TERMS = [
    "ignore as instru",
    "ignore todas",
    "system prompt",
    "prompt do sistema",
    "revele",
    "mostre o prompt",
    "voce agora e",
    "você agora é",
]

RISK_TERMS = [
    "abrir o carregador",
    "mexer nos fios",
    "mexer na fiacao",
    "mexer na fiação",
    "ligar fio",
    "desligar fio",
    "processar a empresa",
    "contrato juridico",
    "contrato jurídico",
    "aconselhamento financeiro",
    "investimento",
]


def moderation_message(text: str) -> str | None:
    text = text.lower()

    if any(term in text for term in JAILBREAK_TERMS):
        return (
            "Nao posso ignorar regras, revelar instrucoes internas ou seguir "
            "prompt injection. Posso ajudar com ChargeGrid, GoodWe e recarga."
        )

    if any(term in text for term in RISK_TERMS):
        return (
            "Nao posso orientar intervencao eletrica nem dar aconselhamento "
            "juridico ou financeiro profissional. Procure um profissional habilitado."
        )

    return None
