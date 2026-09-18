import logging
import os
import time

from dotenv import load_dotenv

from chain.builder import build_conversational_chain, token_counter
from chain.memoria import clear_session, get_session_memory
from guardrails.moderation import moderation_message
from guardrails.scope_validator import validate_scope

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("chargegrid")


class ChargeGridChatbot:

    def __init__(self, model=None):
        self.chain, self.llm = build_conversational_chain(model)
        self.model = model or os.getenv(
            "OLLAMA_MODEL",
            "gpt-oss:20b-cloud"
        )

    def chat(self, user_message: str, session_id: str = "default") -> dict:

        user_message = user_message.strip()

        if not user_message:
            return {
                "resposta": "Digite uma pergunta sobre recarga de veículos elétricos.",
                "latency_ms": 0,
                "tokens_input": 0,
                "structured_valid": True,
                "model_called": False
            }

        moderation = moderation_message(user_message)

        if moderation:
            return {
                "resposta": moderation,
                "escopo": "seguranca",
                "latency_ms": 0,
                "tokens_input": token_counter(user_message),
                "structured_valid": True,
                "model_called": False
            }

        memory = get_session_memory(
            session_id,
            llm=self.llm
        )

        in_scope, message = validate_scope(
            user_message,
            memory.get_history()
        )

        if not in_scope:
            return {
                "resposta": message,
                "escopo": "fora_escopo",
                "latency_ms": 0,
                "tokens_input": token_counter(user_message),
                "structured_valid": True,
                "model_called": False
            }

        start = time.perf_counter()

        try:
            result = self.chain.invoke(
                {"input": user_message},
                config={
                    "configurable": {
                        "session_id": session_id
                    }
                },
            )

            latency_ms = round(
                (time.perf_counter() - start) * 1000,
                2
            )

            memory.trim_with_counter(token_counter)

            logger.info(
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

            latency_ms = round(
                (time.perf_counter() - start) * 1000,
                2
            )

            logger.exception("Erro ao executar o chatbot")

            return {
                "resposta": (
                    "Não foi possível acessar o modelo da Ollama Cloud. "
                    "Verifique sua API Key e sua conexão com a internet."
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


def create_chatbot(model=None):
    return ChargeGridChatbot(model=model)