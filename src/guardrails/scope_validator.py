import re


# ============================================================
# TERMOS PRINCIPAIS DO PROJETO
# ============================================================

GOODWE_TERMS = [
    "goodwe",
    "good we",
    "sems",
    "sems+",
    "chargegrid",
    "charge grid",
]

EV_TERMS = [
    "veículo elétrico",
    "veiculo eletrico",
    "veículos elétricos",
    "veiculos eletricos",
    "ve",
    "carro elétrico",
    "carro eletrico",
    "carros elétricos",
    "carros eletricos",
    "automóvel elétrico",
    "automovel eletrico",
    "mobilidade elétrica",
    "mobilidade eletrica",
    "eletromobilidade",
    "ev",
    "electric vehicle",
    "carro",
    "carregar meu carro",
    "carregar o carro",
    "carrego meu carro",
    "meu carro",
    "meu veículo",
    "meu veiculo",
]

CHARGING_TERMS = [
    "recarga",
    "recarregar",
    "recarrega",
    "carregamento",
    "carregar",
    "carregando",
    "carga",
    "carregador",
    "carregadores",
    "estação de recarga",
    "estacao de recarga",
    "estação de carregamento",
    "estacao de carregamento",
    "ponto de recarga",
    "ponto de carregamento",
    "wallbox",
    "plugue",
    "plug",
    "conector",
    "conectado",
    "conectar",
    "carrego",
    "carregar",
    "carregando",
    "carreguei",
    "carrega meu carro",
    "carregar meu veículo",
    "carregar meu veiculo",
]

ENERGY_TERMS = [
    "energia",
    "energia elétrica",
    "energia eletrica",
    "elétrica",
    "eletrica",
    "kwh",
    "kw",
    "quilowatt",
    "quilowatts",
    "quilowatt-hora",
    "quilowatt hora",
    "potência",
    "potencia",
    "demanda",
    "consumo",
    "consumida",
    "consumido",
    "geração",
    "geracao",
    "gerada",
    "solar",
    "energia solar",
    "painel solar",
    "painéis solares",
    "paineis solares",
    "fotovoltaica",
    "fotovoltaico",
]

COST_TERMS = [
    "custo",
    "custos",
    "preço",
    "preco",
    "valor",
    "valores",
    "tarifa",
    "tarifas",
    "r$",
    "reais",
    "dinheiro",
    "gasto",
    "gastos",
    "gastar",
    "economizar",
    "economia",
    "econômico",
    "economico",
    "horário econômico",
    "horario economico",
    "cobrança",
    "cobranca",
    "cobrar",
    "cobrado",
    "pagamento",
    "pagar",
    "fatura",
    "conta",
    "financeiro",
]

SYSTEM_TERMS = [
    "sistema",
    "monitoramento",
    "monitorar",
    "monitor",
    "dashboard",
    "painel",
    "plataforma",
    "gestão",
    "gestao",
    "gerenciamento",
    "controle",
    "automação",
    "automacao",
    "inteligente",
    "inteligência",
    "inteligencia",
    "ia",
    "inteligência artificial",
    "inteligencia artificial",
    "algoritmo",
    "dados",
    "informação",
    "informacoes",
    "informação",
    "informações",
]

STATUS_TERMS = [
    "status",
    "estado",
    "situação",
    "situacao",
    "disponível",
    "disponivel",
    "indisponível",
    "indisponivel",
    "em uso",
    "ocupado",
    "livre",
    "manutenção",
    "manutencao",
    "funcionando",
    "funciona",
    "funcionamento",
    "problema",
    "problemas",
    "erro",
    "falha",
    "falhando",
    "defeito",
    "quebrado",
]

TIME_TERMS = [
    "horário",
    "horario",
    "hora",
    "horas",
    "minuto",
    "minutos",
    "tempo",
    "quando",
    "manhã",
    "manha",
    "tarde",
    "noite",
    "madrugada",
    "hoje",
    "amanhã",
    "amanha",
    "agora",
    "dia",
    "dias",
    "período",
    "periodo",
    "22:00",
    "06:00",
]

CHARGER_IDS = [
    "cg-01",
    "cg-02",
    "cg-03",
    "cg-04",
    "cg01",
    "cg02",
    "cg03",
    "cg04",
]

LOCATION_TERMS = [
    "garagem",
    "bloco a",
    "bloco b",
    "estacionamento",
    "vip",
    "visitantes",
    "área visitantes",
    "area visitantes",
]

OPERATION_TERMS = [
    "como funciona",
    "como funciona o sistema",
    "como funciona a recarga",
    "como funciona o carregador",
    "como usar",
    "como utilizar",
    "como iniciar",
    "como parar",
    "iniciar recarga",
    "parar recarga",
    "começar",
    "comecar",
    "iniciar",
    "finalizar",
    "encerrar",
    "conectar",
    "desconectar",
]

COMPARISON_TERMS = [
    "comparar",
    "compare",
    "comparação",
    "comparacao",
    "diferença",
    "diferenca",
    "diferenças",
    "diferencas",
    "melhor",
    "pior",
    "mais barato",
    "mais caro",
    "mais rápido",
    "mais rapido",
    "mais lento",
    "maior",
    "menor",
    "qual deles",
    "qual é melhor",
    "qual e melhor",
]

OPTIMIZATION_TERMS = [
    "otimizar",
    "otimização",
    "otimizacao",
    "eficiência",
    "eficiencia",
    "eficiente",
    "economizar",
    "reduzir consumo",
    "reduzir custo",
    "diminuir custo",
    "diminuir consumo",
    "economia de energia",
    "gestão de energia",
    "gestao de energia",
    "distribuição de energia",
    "distribuicao de energia",
    "pico",
    "horário de pico",
    "horario de pico",
    "sobrecarga",
    "sobrecarga de energia",
]

SECURITY_TERMS = [
    "jailbreak",
    "prompt injection",
    "prompt injection",
    "ignore as instruções",
    "ignore as instrucoes",
    "ignore todas as instruções",
    "ignore todas as instrucoes",
    "ignore o prompt",
    "ignore as regras",
    "revele o prompt",
    "revela o prompt",
    "mostre o prompt",
    "mostrar o prompt",
    "system prompt",
    "prompt do sistema",
    "instruções do sistema",
    "instrucoes do sistema",
    "burlar as regras",
    "burlar o sistema",
    "finja que",
    "troque de persona",
]


# ============================================================
# TERMOS DE CONTINUIDADE
# ============================================================

CONTINUATION_TERMS = [
    "isso",
    "isto",
    "aquilo",
    "esse",
    "essa",
    "esse carregador",
    "essa recarga",
    "esse valor",
    "essa tarifa",
    "esse custo",
    "esse horário",
    "esse horario",
    "nesse",
    "nessa",
    "nele",
    "nela",
    "dele",
    "dela",
    "eles",
    "elas",
    "qual deles",
    "qual deles seria",
    "e quanto",
    "e qual",
    "e como",
    "e quando",
    "e onde",
    "e esse",
    "e essa",
    "e se",
    "também",
    "tambem",
    "então",
    "entao",
    "nesse caso",
    "nesse cenário",
    "nesse cenario",
    "anterior",
    "anteriormente",
    "como você falou",
    "como voce falou",
    "como mencionado",
    "daquele",
    "daquela",
]


# ============================================================
# TERMOS QUE INDICAM ASSUNTOS FORA DO ESCOPO
# ============================================================

OUT_OF_SCOPE_TERMS = [
    "futebol",
    "futebol brasileiro",
    "basquete",
    "nba",
    "filme",
    "filmes",
    "série",
    "serie",
    "séries",
    "series",
    "música",
    "musica",
    "cantor",
    "cantora",
    "jogo",
    "games",
    "videogame",
    "receita",
    "bolo",
    "comida",
    "política",
    "politica",
    "presidente",
    "eleição",
    "eleicao",
    "celebridade",
    "novela",
    "piada",
    "poema",
    "programação em python",
    "código em python",
    "codigo em python",
    "javascript",
    "java",
    "c++",
]


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalize_text(text: str) -> str:
    """Normaliza o texto para facilitar a comparação."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def contains_any(text: str, terms: list[str]) -> bool:
    """Verifica se o texto contém pelo menos um dos termos."""
    return any(term in text for term in terms)


def get_history_text(history) -> str:
    """
    Converte o histórico da conversa em texto.

    Aceita:
    - lista de mensagens
    - InMemoryChatMessageHistory
    - objetos que possuam .messages
    """
    if history is None:
        return ""

    if hasattr(history, "messages"):
        history = history.messages

    if not history:
        return ""

    parts = []

    for message in history:
        if hasattr(message, "content"):
            content = message.content
        else:
            content = str(message)

        if content:
            parts.append(str(content))

    return normalize_text(" ".join(parts))


def is_security_request(text: str) -> bool:
    """Detecta tentativas explícitas de jailbreak ou prompt injection."""
    normalized = normalize_text(text)
    return contains_any(normalized, SECURITY_TERMS)


def is_directly_in_scope(text: str) -> bool:
    """
    Verifica se a própria pergunta possui contexto suficiente
    para ser considerada relacionada ao projeto.
    """
    normalized = normalize_text(text)

    domain_groups = [
        GOODWE_TERMS,
        EV_TERMS,
        CHARGING_TERMS,
        ENERGY_TERMS,
        COST_TERMS,
        SYSTEM_TERMS,
        STATUS_TERMS,
        LOCATION_TERMS,
        CHARGER_IDS,
    ]

    for group in domain_groups:
        if contains_any(normalized, group):
            return True

    return False


def is_out_of_scope(text: str) -> bool:
    """Detecta assuntos explicitamente fora do projeto."""
    normalized = normalize_text(text)

    return contains_any(normalized, OUT_OF_SCOPE_TERMS)


def is_continuation_question(text: str) -> bool:
    """
    Identifica perguntas que normalmente dependem do contexto anterior.
    """
    normalized = normalize_text(text)

    if contains_any(normalized, CONTINUATION_TERMS):
        return True

    # Perguntas curtas normalmente dependem do contexto anterior.
    words = normalized.split()

    if len(words) <= 8:
        continuation_patterns = [
            r"^e ",
            r"^mas ",
            r"^então ",
            r"^entao ",
            r"^quanto ",
            r"^qual ",
            r"^como ",
            r"^quando ",
            r"^onde ",
            r"^por que ",
            r"^porque ",
            r"^isso ",
            r"^esse ",
            r"^essa ",
        ]

        return any(
            re.search(pattern, normalized)
            for pattern in continuation_patterns
        )

    return False


def history_has_domain_context(history) -> bool:
    """
    Verifica se a conversa anterior já possui contexto relacionado
    ao ChargeGrid/GoodWe/EV.
    """
    history_text = get_history_text(history)

    if not history_text:
        return False

    return is_directly_in_scope(history_text)


# ============================================================
# VALIDADOR PRINCIPAL
# ============================================================

def validate_scope(
    text: str,
    history=None,
) -> tuple[bool, str]:
    """
    Valida se uma pergunta pertence ao escopo do ChargeGrid/GoodWe.

    Regras:

    1. Mensagem vazia é recusada.
    2. Tentativas de jailbreak/prompt injection são recusadas.
    3. Perguntas diretamente relacionadas ao domínio são aceitas.
    4. Perguntas de continuidade são aceitas quando existe contexto
       válido na memória.
    5. Assuntos claramente externos ao projeto são recusados.
    6. Perguntas ambíguas sem contexto são recusadas.
    """

    normalized = normalize_text(text)

    # --------------------------------------------------------
    # 1. Mensagem vazia
    # --------------------------------------------------------

    if not normalized:
        return (
            False,
            "Digite uma pergunta sobre mobilidade elétrica e recarga.",
        )

    # --------------------------------------------------------
    # 2. Segurança
    # --------------------------------------------------------

    if is_security_request(normalized):
        return (
            False,
            "Não posso ignorar as regras de segurança, revelar instruções internas ou alterar as regras do sistema.",
        )

    # --------------------------------------------------------
    # 3. Pergunta diretamente relacionada ao projeto
    # --------------------------------------------------------

    if is_directly_in_scope(normalized):
        return True, ""

    # --------------------------------------------------------
    # 4. Pergunta explicitamente fora do domínio
    # --------------------------------------------------------

    if is_out_of_scope(normalized):
        return (
            False,
            "Posso ajudar apenas com o projeto ChargeGrid/GoodWe e temas relacionados à recarga de veículos elétricos.",
        )

    # --------------------------------------------------------
    # 5. Pergunta de continuidade
    # --------------------------------------------------------

    if is_continuation_question(normalized):

        if history_has_domain_context(history):
            return True, ""

    # --------------------------------------------------------
    # 6. Caso ambíguo
    # --------------------------------------------------------

    return (
        False,
        "Posso ajudar apenas com o projeto ChargeGrid/GoodWe e temas relacionados à recarga de veículos elétricos.",
    )