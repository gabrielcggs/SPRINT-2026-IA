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
    """Busca por similaridade (densa) ou hibrida (densa + BM25 fundidas por RRF).

    No modo hibrido, ``Recuperado.score`` continua sendo a similaridade cosseno do trecho
    (o que o medidor da interface e o ``min_score`` usam); o BM25 so muda a ORDEM e quais
    trechos entram no top-k.
    """

    RRF_K = 60

    def __init__(self, store, k: int = 4, min_score: float = 0.0, hibrido: bool = False):
        self.store = store
        self.k = k
        self.min_score = min_score
        self.hibrido = hibrido
        self._bm25 = None
        self._corpus: list[tuple[str, dict]] = []

    def _indice_lexical(self):
        if self._bm25 is None:
            from rag.lexical import BM25

            dados = self.store.get(include=["documents", "metadatas"])
            self._corpus = list(zip(dados["documents"], dados["metadatas"]))
            self._bm25 = BM25([t for t, _ in self._corpus])
        return self._bm25

    def _buscar_hibrido(self, consulta: str, k: int) -> list[tuple[str, dict, float]]:
        bm25 = self._indice_lexical()
        n = len(self._corpus)
        pool = min(n, max(50, k * 10))
        densos = self.store.similarity_search_with_score(consulta, k=pool)
        dens = {d.page_content: (d.metadata, 1.0 - float(dist)) for d, dist in densos}
        ordem_densa = [d.page_content for d, _ in densos]

        notas = bm25.pontuar(consulta)
        ordem_lex = [self._corpus[i][0] for i in sorted(range(n), key=lambda i: -notas[i]) if notas[i] > 0]

        fusao: dict[str, float] = {}
        for lista in (ordem_densa, ordem_lex):
            for rank, texto in enumerate(lista, start=1):
                fusao[texto] = fusao.get(texto, 0.0) + 1.0 / (self.RRF_K + rank)

        piso = min((s for _, s in dens.values()), default=0.0)
        meta_por_texto = {t: m for t, m in self._corpus}
        saida = []
        for texto in sorted(fusao, key=lambda t: -fusao[t])[:k]:
            meta, score = dens.get(texto, (meta_por_texto[texto], piso))
            saida.append((texto, meta, score))
        return saida

    def buscar(self, consulta: str, k: int | None = None, min_score: float | None = None) -> Busca:
        k = k or self.k
        corte = self.min_score if min_score is None else min_score

        if self.hibrido:
            triplas = self._buscar_hibrido(consulta, k)
        else:
            triplas = [(d.page_content, d.metadata, 1.0 - float(dist))
                       for d, dist in self.store.similarity_search_with_score(consulta, k=k)]

        todos: list[Recuperado] = []
        for pos, (texto, meta, score) in enumerate(triplas, start=1):
            todos.append(
                Recuperado(
                    id=f"S{pos}",
                    texto=texto,
                    documento=meta.get("source", "desconhecido"),
                    pagina=int(meta.get("page", 0)),
                    secao=meta.get("section", ""),
                    score=round(score, 4),
                )
            )
        aceitos = [r for r in todos if r.score >= corte]
        return Busca(todos=todos, aceitos=aceitos)
