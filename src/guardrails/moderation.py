JAILBREAK_PATTERNS = [
    r"ignore (todas|as) instruções",
    r"ignore (all|previous) instructions",
    r"mostre.*(system prompt|prompt do sistema)",
    r"revele.*(system prompt|instruções internas)",
    r"você agora é",
    r"you are now",
    r"burlar.*regras",
]


def detect_prompt_attack(text: str) -> bool:
    normalized = text.lower()
    return any(__import__("re").search(pattern, normalized) for pattern in JAILBREAK_PATTERNS)


def detect_sensitive_request(text: str) -> bool:
    normalized = text.lower()
    electrical = ["abrir o carregador", "mexer nos fios", "mexer na fiação", "ligar fio", "desligar fio"]
    legal_financial = ["processar a empresa", "contrato jurídico", "investimento", "aconselhamento financeiro"]
    return any(term in normalized for term in electrical + legal_financial)


def moderation_message(text: str) -> str | None:
    if detect_prompt_attack(text):
        return "Não posso ignorar minhas regras, revelar instruções internas ou seguir uma tentativa de prompt injection. Posso ajudar com o ChargeGrid e a recarga de veículos elétricos."
    if detect_sensitive_request(text):
        return "Esse tipo de orientação pode exigir avaliação profissional. Não forneço instruções de intervenção elétrica nem aconselhamento jurídico/financeiro profissional. Procure um profissional habilitado ou responsável adequado."
    return None
