from langchain_core.chat_history import InMemoryChatMessageHistory

try:
    from langchain_classic.memory import ConversationTokenBufferMemory
except ImportError:
    ConversationTokenBufferMemory = None


class SessionMemory:
    """Memória por sessão com histórico e limite aproximado de tokens."""

    def __init__(self, max_tokens: int = 2000, llm=None):
        self.max_tokens = max_tokens
        self.history = InMemoryChatMessageHistory()
        self.buffer_memory = None
        if ConversationTokenBufferMemory is not None and llm is not None:
            try:
                self.buffer_memory = ConversationTokenBufferMemory(
                    llm=llm, memory_key="history", return_messages=True, max_token_limit=max_tokens
                )
            except Exception:
                self.buffer_memory = None

    def get_history(self):
        return self.history

    def clear(self):
        self.history.clear()
        if self.buffer_memory is not None:
            self.buffer_memory.clear()

    def token_count(self, counter):
        text = "\n".join(message.content for message in self.history.messages)
        return counter(text)

    def trim_with_counter(self, counter):
        while self.history.messages and self.token_count(counter) > self.max_tokens:
            self.history.messages.pop(0)


_sessions: dict[str, SessionMemory] = {}


def get_session_memory(session_id: str, max_tokens: int = 2000, llm=None) -> SessionMemory:
    if session_id not in _sessions:
        _sessions[session_id] = SessionMemory(max_tokens=max_tokens, llm=llm)
    return _sessions[session_id]


def clear_session(session_id: str):
    memory = _sessions.get(session_id)
    if memory:
        memory.clear()
