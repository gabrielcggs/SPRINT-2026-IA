from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "relatorio_evolucao.pdf"

LINES = [
    "ChargeGrid Intelligence - Relatorio Sprint 03",
    "",
    "1. Resumo da evolucao",
    "Nas Sprints 1 e 2 o chatbot usava respostas manuais em Python.",
    "Na Sprint 03 o nucleo foi refatorado para LangChain LCEL, memoria por sessao,",
    "Pydantic v2, prompt XML e guardrails.",
    "",
    "2. Refatoracao",
    "A chain principal usa ChatPromptTemplate | ChatOllama | PydanticOutputParser.",
    "O modelo e remoto pela Ollama Cloud, sem download local.",
    "Trade-off: depende de internet e API key, mas roda em maquinas simples.",
    "",
    "3. Comparativo antes/depois",
    "Qualidade: Sprints 1/2 3.5/5.0 | Sprint 03 5.0/5.0",
    "Tokens/turno: antes nao medido | Sprint 03 10.2 tokens/turno",
    "Latencia media: antes nao medida | Sprint 03 1731.08 ms",
    "Structured output: antes nao aplicavel | Sprint 03 100%",
    "",
    "4. Problemas e solucoes",
    "Problema 1: historico sem limite. Solucao: limite de tokens.",
    "Problema 2: resposta sem formato fixo. Solucao: schema Pydantic.",
    "Problema 3: prompt injection. Solucao: guardrails antes do modelo.",
    "",
    "5. Equipe",
    "Gabriel Camarosani - RM 569189 - Chain LCEL",
    "Gustavo Lima - RM 571709 - Memoria e testes",
    "Lucas Hummel - RM 569673 - Schema Pydantic",
    "Pedro Castro - RM 569311 - Guardrails",
    "Bruno Kanashiro - RM 571776 - Prompt e documentacao",
    "Lucas Barreto - RM 573149 - Evals",
]


def pdf_escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(lines):
    stream_lines = ["BT", "/F1 12 Tf", "50 800 Td", "16 TL"]
    for line in lines:
        stream_lines.append(f"({pdf_escape(line)}) Tj")
        stream_lines.append("T*")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


OUT.write_bytes(build_pdf(LINES))
print(f"PDF gerado em: {OUT}")
