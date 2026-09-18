import logging
import os
import time
import warnings

from dotenv import load_dotenv

from chain.builder import build_conversational_chain, token_counter
from chain.memoria import clear_session, get_session_memory
from guardrails.moderation import moderation_message
from guardrails.scope_validator import validate_scope

load_dotenv(override=True)

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="langchain")
warnings.filterwarnings("ignore", message=".*deprecated.*")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("chargegrid")


class ChargeGridChatbot:
    def __init__(self, model=None):
        self.chain, self.llm = build_conversational_chain(model)
        self.model = model or os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")

    def chat(self, user_message: str, session_id: str = "default") -> dict:
        user_message = user_message.strip()

        if not user_message:
            return self._simple_response("Digite uma pergunta sobre recarga de veiculos eletricos.")

        moderation = moderation_message(user_message)
        if moderation:
            return self._simple_response(moderation, escopo="seguranca", user_text=user_message)

        memory = get_session_memory(session_id, llm=self.llm)
        in_scope, message = validate_scope(user_message, memory.get_history())
        if not in_scope:
            return self._simple_response(message, escopo="fora_escopo", user_text=user_message)

        start = time.perf_counter()

        try:
            result = self.chain.invoke(
                {"input": user_message},
                config={"configurable": {"session_id": session_id}},
            )

            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            memory.trim_with_counter(token_counter)

            logger.debug(
                "modelo=%s latencia_ms=%s tokens_historico=%s",
                self.model,
                latency_ms,
                memory.token_count(token_counter),
            )

            data = result.model_dump()
            data["latency_ms"] = latency_ms
            data["tokens_input"] = token_counter(user_message)
            data["structured_valid"] = True
            data["model_called"] = True
            return data

        except Exception as exc:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error("Erro ao executar o chatbot: %s", exc, exc_info=True)

            return {
                "resposta": (
                    "Nao consegui validar a resposta do modelo. "
                    "Tente perguntar de forma mais direta sobre um carregador ou recarga."
                ),
                "escopo": "goodwe_ev",
                "latency_ms": latency_ms,
                "tokens_input": token_counter(user_message),
                "structured_valid": False,
                "error": str(exc),
                "model_called": True,
            }

    def reset(self, session_id: str = "default"):
        clear_session(session_id)

    @staticmethod
    def _simple_response(text, escopo="goodwe_ev", structured_valid=True, user_text=""):
        return {
            "resposta": text,
            "escopo": escopo,
            "latency_ms": 0,
            "tokens_input": token_counter(user_text or text),
            "structured_valid": structured_valid,
            "model_called": False,
        }


def create_chatbot(model=None):
    return ChargeGridChatbot(model=model)


class ConversationManager:
    """Versao simples mantida como comparativo das Sprints 1/2."""

    def __init__(self, max_turns=3):
        self.max_turns = max_turns
        self.messages = []

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant_message(self, content):
        self.messages.append({"role": "assistant", "content": content})
        self._trim()

    def get_messages(self):
        return self.messages

    def _trim(self):
        self.messages = self.messages[-self.max_turns * 2:]


def resposta_local(pergunta: str) -> str:
    """Resposta manual antiga usada nos testes de baseline."""
    pergunta = pergunta.lower()

    if "gastei" in pergunta or "consumo" in pergunta:
        return "Em junho/2026 foram 847 kWh, com custo estimado de R$ 753,83."

    if "sobrecarga" in pergunta:
        return "Nao existe sobrecarga: a demanda atual e 38 kW de 50 kW contratados."

    if "disponivel" in pergunta or "livre" in pergunta:
        return "CG-01 e CG-04 estao disponiveis."

    return "Tenho dados apenas sobre os carregadores CG-01 a CG-04 do projeto."
