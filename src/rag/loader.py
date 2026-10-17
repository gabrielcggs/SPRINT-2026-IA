"""Carregamento dos PDFs da base de conhecimento com PyMuPDFLoader (Aula 06)."""
from __future__ import annotations

import warnings
from pathlib import Path

from langchain_core.documents import Document

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from langchain_community.document_loaders import PyMuPDFLoader


def carregar_pdfs(diretorio: str | Path) -> list[Document]:
    """Le todos os PDFs de uma pasta. Uma Document por pagina.

    Metadados padronizados: ``source`` (nome do arquivo) e ``page`` (1-based).
    """
    pasta = Path(diretorio)
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta da base de conhecimento nao encontrada: {pasta}")

    pdfs = sorted(pasta.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(
            f"Nenhum PDF em {pasta}. Rode: python scripts/gerar_base_conhecimento.py"
        )

    paginas: list[Document] = []
    for pdf in pdfs:
        for doc in PyMuPDFLoader(str(pdf)).load():
            texto = doc.page_content.strip()
            if not texto:
                continue
            doc.page_content = texto
            doc.metadata = {
                "source": pdf.name,
                "page": int(doc.metadata.get("page", 0)) + 1,
                "total_pages": doc.metadata.get("total_pages"),
            }
            paginas.append(doc)
    return paginas
