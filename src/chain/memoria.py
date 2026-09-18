from langchain_classic.memory import ConversationTokenBufferMemory


class SessionMemory:
    def __init__(self, llm, max_tokens=2000):
        self.max_tokens = max_tokens

        self.memory = ConversationTokenBufferMemory(
            llm=llm,
            memory_key="history",
            return_messages=True,
            max_token_limit=max_tokens,
        )

    def get_history(self):
        return self.memory.chat_memory

    def clear(self):
        self.memory.clear()

    def token_count(self, counter):
        text = "\n".join(
            message.content
            for message in self.memory.chat_memory.messages
        )
        return counter(text)

    def trim_with_counter(self, counter):
        while (
            self.memory.chat_memory.messages
            and self.token_count(counter) > self.max_tokens
        ):
            self.memory.chat_memory.messages.pop(0)


_sessions = {}


def get_session_memory(session_id, llm, max_tokens=2000):
    if session_id not in _sessions:
        _sessions[session_id] = SessionMemory(
            llm=llm,
            max_tokens=max_tokens,
        )

    return _sessions[session_id]


def clear_session(session_id):
    if session_id in _sessions:
        _sessions[session_id].clear()
