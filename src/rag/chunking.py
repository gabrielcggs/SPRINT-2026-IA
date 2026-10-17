"""Estrategia de chunking (Aula 07).

Dois modos, para poder comparar nas iteracoes de avaliacao:

* ``pagina``: divide o texto de cada pagina com RecursiveCharacterTextSplitter,
  sem respeitar secoes (baseline). A secao do chunk e a ultima secao iniciada
  antes dele.
* ``secao``: primeiro separa o texto nos titulos numerados ("2. Carregadores"),
  depois divide cada secao com o splitter. Nenhum chunk cruza duas secoes.

Opcionalmente cada chunk recebe um cabecalho "[documento | secao]" (contextual
chunk header), que ajuda a busca semantica a saber de onde o trecho veio.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Titulo numerado em linha propria: "1. Visao geral", "2.1 Estados do carregador".
HEADING_RE = re.compile(
    r"^(\d+(?:\.\d+)*)\.?\s+([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^\n]{2,90})$",
    re.MULTILINE,
)

MIN_CHUNK_CHARS = 30


@dataclass(frozen=True)
class ChunkingConfig:
    chunk_size: int = 700
    chunk_overlap: int = 100
    modo: str = "secao"  # "secao" | "pagina"
    cabecalho: bool = True

    def assinatura(self) -> str:
        return (
            f"cs{self.chunk_size}_ov{self.chunk_overlap}_{self.modo}_"
            f"{'cab' if self.cabecalho else 'semcab'}"
        )


def _titulo_documento(source: str) -> str:
    return Path(source).stem.replace("_", " ")


def _chunk_id(source: str, page: int, secao: str, idx: int, texto: str) -> str:
    base = f"{source}|{page}|{secao}|{idx}|{texto}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:20]


def _blocos_por_secao(texto: str, titulos: list[tuple[int, str]], secao_inicial: str):
    """Quebra o texto da pagina nos titulos. Retorna [(secao, texto_do_bloco)]."""
    blocos: list[tuple[str, str]] = []
    if not titulos:
        return [(secao_inicial, texto)]

    primeiro = titulos[0][0]
    if texto[:primeiro].strip():
        blocos.append((secao_inicial, texto[:primeiro]))

    for i, (pos, nome) in enumerate(titulos):
        fim = titulos[i + 1][0] if i + 1 < len(titulos) else len(texto)
        blocos.append((nome, texto[pos:fim]))
    return blocos


def dividir_documentos(docs: list[Document], cfg: ChunkingConfig) -> list[Document]:
    """Recebe paginas (uma Document por pagina) e devolve os chunks com metadados."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )

    por_fonte: dict[str, list[Document]] = {}
    for doc in docs:
        por_fonte.setdefault(doc.metadata["source"], []).append(doc)

    chunks: list[Document] = []
    for source, paginas in por_fonte.items():
        titulo = _titulo_documento(source)
        secao_atual = "Introdução"
        idx = 0

        for pagina in sorted(paginas, key=lambda d: d.metadata.get("page", 0)):
            texto = pagina.page_content
            titulos = [
                (m.start(), f"{m.group(1)} {m.group(2).strip()}")
                for m in HEADING_RE.finditer(texto)
            ]
            page = int(pagina.metadata.get("page", 1))
            meta_base = {"source": source, "page": page}

            partes: list[tuple[str, Document]] = []
            if cfg.modo == "secao":
                for secao, bloco in _blocos_por_secao(texto, titulos, secao_atual):
                    for parte in splitter.create_documents([bloco], [meta_base]):
                        partes.append((secao, parte))
            else:
                for parte in splitter.create_documents([texto], [meta_base]):
                    inicio = parte.metadata.get("start_index", 0)
                    secao = secao_atual
                    for pos, nome in titulos:
                        if pos <= inicio:
                            secao = nome
                    partes.append((secao, parte))

            for secao, parte in partes:
                corpo = parte.page_content.strip()
                if len(corpo) < MIN_CHUNK_CHARS:
                    continue
                conteudo = f"[{titulo} | {secao}]\n{corpo}" if cfg.cabecalho else corpo
                chunks.append(
                    Document(
                        page_content=conteudo,
                        metadata={
                            "source": source,
                            "page": page,
                            "section": secao,
                            "chunk_index": idx,
                            "titulo": titulo,
                            "chunk_id": _chunk_id(source, page, secao, idx, corpo),
                        },
                    )
                )
                idx += 1

            if titulos:
                secao_atual = titulos[-1][1]

    return chunks
