"""Busca lexical (BM25) sem dependencias externas, para a busca hibrida.

Por que existe: com embeddings densos numa base pequena e homogenea, os scores ficam todos
na mesma faixa (ex.: 0,58 a 0,76) e o trecho que responde pode cair na posicao 8, 14 ou 18.
Palavras raras da pergunta ("sobrecarga", "CG-02", "hora") identificam o trecho certo; o BM25
captura isso. A fusao com a busca densa e feita por Reciprocal Rank Fusion (retriever.py).
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_STOP = frozenset("""
a o as os um uma uns umas de do da dos das em no na nos nas por para com sem sobre e ou mas que se
qual quais quanto quantos quanta quantas como quando onde quem eu voce ele ela eles elas meu minha
ao aos ha ja foi sao ser esta estao estou tem tenho pode posso preciso agora hoje isso esse essa
""".split())
_PREFIXO = 6

# Expansao de consulta (so no lado da pergunta): sinonimos do dominio de recarga.
# Chaves e valores sao radicais de 6 letras, como sai de tokenizar().
SINONIMOS: dict[str, tuple[str, ...]] = {
    "termin": ("conclu", "andame"),
    "acabou": ("conclu",),
    "finali": ("conclu",),
    "custa": ("custo", "tarifa"),
    "preco": ("tarifa", "custo"),
    "valor": ("tarifa", "custo"),
    "gasto": ("consum", "custo"),
}


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def tokenizar(texto: str) -> list[str]:
    """Minusculas, sem acento, sem stopwords; radical = primeiros 6 caracteres (disponivel ~ disponiveis).
    Codigos como 'cg-02' ficam inteiros."""
    saida = []
    for tok in _TOKEN.findall(normalizar(texto)):
        if tok in _STOP:
            continue
        if any(c.isdigit() for c in tok):
            saida.append(tok)
        else:
            saida.append(tok[:_PREFIXO])
    return saida


class BM25:
    def __init__(self, textos: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenizar(t)) for t in textos]
        self.tam = [sum(d.values()) for d in self.docs]
        self.media = (sum(self.tam) / len(self.tam)) if self.tam else 0.0
        n = len(self.docs)
        df: Counter = Counter()
        for d in self.docs:
            df.update(d.keys())
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def pontuar(self, consulta: str) -> list[float]:
        termos = set(tokenizar(consulta))
        for t in list(termos):
            termos.update(SINONIMOS.get(t, ()))
        notas = []
        for doc, tam in zip(self.docs, self.tam):
            s = 0.0
            for t in termos:
                f = doc.get(t, 0)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * tam / (self.media or 1)))
            notas.append(s)
        return notas
