from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "relatorio_evolucao.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleCenter", parent=styles["Title"], alignment=TA_CENTER))

doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
story = []
story.append(Paragraph("ChargeGrid Intelligence — Relatório de Evolução Sprint 03", styles["TitleCenter"]))
story.append(Spacer(1, 12))
story.append(Paragraph("1. Resumo da evolução", styles["Heading2"]))
story.append(Paragraph("As Sprints 1 e 2 utilizavam uma implementação manual. Na Sprint 03, o núcleo foi refatorado para LangChain LCEL, memória por sessão, Pydantic v2, context engineering e guardrails.", styles["BodyText"]))
story.append(Spacer(1, 8))
story.append(Paragraph("2. Refatoração", styles["Heading2"]))
story.append(Paragraph("A arquitetura foi separada em prompt, modelo, parser, memória e guardrails. O trade-off é uma estrutura maior, porém com responsabilidades mais claras e métricas de avaliação. A Sprint 03 também permite comparar os modelos locais qwen3:8b e llama3.2:3b com a mesma cadeia e os mesmos parâmetros.", styles["BodyText"]))
story.append(Spacer(1, 8))
story.append(Paragraph("Parâmetros de geração", styles["Heading2"]))
story.append(Paragraph("qwen3:8b e llama3.2:3b: temperature=0.1, top_p=0.9 e max_tokens=512 (enviado ao Ollama como num_predict). Os resultados devem ser preenchidos somente após execução.", styles["BodyText"]))
story.append(Spacer(1, 8))
story.append(Paragraph("3. Comparativo antes/depois", styles["Heading2"]))
data=[["Métrica","Sprints 1/2","Sprint 03"],["Qualidade","Preencher","Preencher"],["Tokens/turno","Não medido","Preencher"],["Latência média","Não medida","Preencher"],["Structured output","N/A","Preencher"]]
t=Table(data,colWidths=[150,150,150]); t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t)
story.append(Spacer(1, 8))
story.append(Paragraph("4. Problemas e soluções", styles["Heading2"]))
story.append(Paragraph("Problema 1: histórico sem limite. Solução: memória por sessão e limite de tokens. Problema 2: saída não estruturada. Solução: Pydantic v2 e parser. Problema 3: prompt injection. Solução: guardrails e regras de segurança.", styles["BodyText"]))
story.append(Spacer(1, 8))
story.append(Paragraph("5. Equipe", styles["Heading2"]))
team=[["Integrante","RM","Tarefa"],["Gabriel Camarosani","569189","LCEL e integração"],["Gustavo Lima","571709","Memória e testes"],["Lucas Hummel","569673","Pydantic"],["Pedro Castro","569311","Guardrails e eval"],["Bruno Kanashiro","571776","Prompts e documentação"]]
t2=Table(team,colWidths=[150,70,230]); t2.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('VALIGN',(0,0),(-1,-1),'TOP')]))
story.append(t2)
doc.build(story)
print(f"PDF gerado em: {OUT}")
