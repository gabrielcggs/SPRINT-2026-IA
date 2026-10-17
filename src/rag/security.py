"""Guardrails do RAG (Aula 07).

Duas barreiras independentes:

1. ``verificar_entrada``: bloqueia a pergunta do usuario antes de qualquer busca
   ou chamada de modelo (jailbreak, prompt injection, intervencao eletrica,
   aconselhamento juridico/financeiro).
2. ``sanitizar_recuperados``: remove, dos trechos recuperados, frases que
   tentam dar ordens ao modelo (prompt injection indireta via documentos).
   O texto dos documentos e tratado como DADO, nunca como instrucao.

O prompt v3 reforca as duas barreiras do lado do modelo.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import replace

from rag.retriever import Recuperado

MARCADOR_REMOVIDO = "[trecho removido: possível injeção de prompt]"

MENSAGEM_ENTRADA_BLOQUEADA = (
    "Não posso ignorar regras, revelar instruções internas ou seguir instruções "
    "embutidas na pergunta. Posso ajudar com ChargeGrid, GoodWe e recarga de "
    "veículos elétricos."
)


def _norm(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).lower()


# Aplicados sobre texto sem acentos e em minusculas.
PADROES_INJECAO = [
    r"ignor\w*\s+(?:\w+\s+){0,3}(?:instruc|regra|orientac|comando|prompt)",
    r"desconsider\w*\s+(?:\w+\s+){0,3}(?:instruc|regra|orientac)",
    r"esqueca\s+(?:\w+\s+){0,3}(?:instruc|regra|orientac)",
    r"nao\s+(?:siga|obedeca|respeite)\s+(?:\w+\s+){0,2}(?:instruc|regra)",
    r"ignore\s+(?:all|any|the|previous|prior|above)",
    r"disregard\s+(?:all|any|the|previous|prior|above)",
    r"system\s*prompt|prompt\s+d[eo]\s+sistema|prompt\s+interno",
    r"(?:revele|revelar|mostre|exiba|imprima|vaze)\s+(?:\w+\s+){0,3}(?:prompt|instruc)",
    r"(?:reveal|show|print|leak)\s+(?:\w+\s+){0,3}(?:prompt|instructions)",
    r"voce\s+agora\s+e\b|you\s+are\s+now\b|a\s+partir\s+de\s+agora\s+voce",
    r"\b(?:finja|aja\s+como|atue\s+como)\b.{0,40}\b(?:assistente|sem\s+restric)",
    r"jailbreak|modo\s+dan\b|developer\s+mode|modo\s+desenvolvedor",
    r"</?\s*(?:system|assistant|user|instruc\w*|contexto|trecho|pergunta|historico)\b[^>]*>",
    r"\[\s*/?\s*(?:inst|system)\s*\]",
    r"responda\s+(?:ao\s+usuario\s+)?que\s+(?:todos|todas|o\s+usuario)",
    r"informe\s+ao\s+usuario\s+que",
]
_REGEX_INJECAO = [re.compile(p) for p in PADROES_INJECAO]


def contem_injecao(texto: str) -> bool:
    alvo = _norm(texto)
    return any(rx.search(alvo) for rx in _REGEX_INJECAO)


def verificar_entrada(pergunta: str) -> str | None:
    """Retorna a mensagem de recusa se a pergunta deve ser bloqueada, senao None."""
    try:
        from guardrails.moderation import moderation_message

        mensagem = moderation_message(pergunta)
        if mensagem:
            return mensagem
    except ImportError:  # pasta guardrails/ da Sprint 03 ausente
        pass

    if contem_injecao(pergunta):
        return MENSAGEM_ENTRADA_BLOQUEADA
    return None


_SENTENCAS = re.compile(r"(?<=[.!?])\s+")


def sanitizar_texto(texto: str) -> tuple[str, int]:
    """Substitui frases suspeitas por um marcador. Retorna (texto_limpo, n_frases_removidas)."""
    removidas = 0
    linhas_limpas: list[str] = []
    for linha in texto.split("\n"):
        frases = _SENTENCAS.split(linha)
        limpas = []
        for frase in frases:
            if frase.strip() and contem_injecao(frase):
                limpas.append(MARCADOR_REMOVIDO)
                removidas += 1
            else:
                limpas.append(frase)
        linhas_limpas.append(" ".join(limpas))
    return "\n".join(linhas_limpas), removidas


def sanitizar_recuperados(recuperados: list[Recuperado]) -> tuple[list[Recuperado], int]:
    """Limpa todos os trechos. Retorna (trechos_limpos, total_de_frases_removidas)."""
    limpos: list[Recuperado] = []
    total = 0
    for r in recuperados:
        texto, n = sanitizar_texto(r.texto)
        total += n
        limpos.append(replace(r, texto=texto) if n else r)
    return limpos, total
