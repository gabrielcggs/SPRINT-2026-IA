"""Retriever (Aula 06): busca semantica top-k com corte por relevancia minima."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Recuperado:
    """Um trecho recuperado da base, pronto para ser citado."""

    id: str          # "S1", "S2"... usado no prompt e na citacao
    texto: str
    documento: str
    pagina: int
    secao: str
    score: float     # relevancia = 1 - distancia cosseno (maior = mais parecido)

    def citacao(self) -> str:
        return f"{self.documento}, p. {self.pagina}, seção {self.secao}"


@dataclass
class Busca:
    todos: list[Recuperado] = field(default_factory=list)    # top-k bruto
    aceitos: list[Recuperado] = field(default_factory=list)  # acima do corte

    @property
    def top1_score(self) -> float | None:
        return self.todos[0].score if self.todos else None


class Retriever:
    def __init__(self, store, k: int = 4, min_score: float = 0.0):
        self.store = store
        self.k = k
        self.min_score = min_score

    def buscar(self, consulta: str, k: int | None = None, min_score: float | None = None) -> Busca:
        k = k or self.k
        corte = self.min_score if min_score is None else min_score

        resultados = self.store.similarity_search_with_score(consulta, k=k)

        todos: list[Recuperado] = []
        for pos, (doc, distancia) in enumerate(resultados, start=1):
            meta = doc.metadata
            todos.append(
                Recuperado(
                    id=f"S{pos}",
                    texto=doc.page_content,
                    documento=meta.get("source", "desconhecido"),
                    pagina=int(meta.get("page", 0)),
                    secao=meta.get("section", ""),
                    score=round(1.0 - float(distancia), 4),
                )
            )
        aceitos = [r for r in todos if r.score >= corte]
        return Busca(todos=todos, aceitos=aceitos)
