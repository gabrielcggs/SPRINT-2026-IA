import os
from pathlib import Path

import tiktoken
from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_core.runnables.history import RunnableWithMessageHistory
from schemas.consulta_recarga import ConsultaRecarga
from chain.memoria import get_session_memory

load_dotenv(override=True)

ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = ROOT / "prompts" / "system_prompt_v3.md"

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")

TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
TOP_P = float(os.getenv("TOP_P", "0.9"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "512"))
MAX_HISTORY_TOKENS = int(os.getenv("MAX_HISTORY_TOKENS", "2000"))


def load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def token_counter(text: str) -> int:
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        return len(text.split())


def build_llm(model: str | None = None):
    return ChatOllama(
        model=model or OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=TEMPERATURE,
        top_p=TOP_P,
        num_predict=MAX_TOKENS,
        reasoning=False,
        client_kwargs={
            "headers": {
                "Authorization": f"Bearer {OLLAMA_API_KEY}"
            }
        },
    )


def build_chain(model: str | None = None):
    llm = build_llm(model)

    parser = PydanticOutputParser(
        pydantic_object=ConsultaRecarga
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            load_system_prompt()
            + "\n\nRetorne obrigatoriamente um JSON válido conforme estas instruções:\n"
            + "{format_instructions}"
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]).partial(
        format_instructions=parser.get_format_instructions()
    )

    return prompt | llm | parser, llm


def build_conversational_chain(model: str | None = None):
    llm = build_llm(model)
    parser = PydanticOutputParser(pydantic_object=ConsultaRecarga)

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            load_system_prompt()
            + "\n\nRetorne obrigatoriamente um JSON válido conforme estas instruções:\n{format_instructions}"
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]).partial(
        format_instructions=parser.get_format_instructions()
    )

    chat_chain = prompt | llm

    def get_history(session_id: str):
        return get_session_memory(
            session_id,
            max_tokens=MAX_HISTORY_TOKENS,
            llm=llm
        ).get_history()

    wrapped = RunnableWithMessageHistory(
        chat_chain,
        get_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    return wrapped | parser, llm
