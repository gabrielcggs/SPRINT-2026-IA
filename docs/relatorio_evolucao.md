# Relatorio de Evolucao - Sprint 03

## 1. Resumo da evolucao

Nas Sprints 1 e 2 o chatbot tinha respostas manuais em Python e um controle simples de historico.

Na Sprint 03 o nucleo foi refatorado para LangChain LCEL, com prompt versionado, memoria por sessao, saida estruturada com Pydantic v2 e guardrails de escopo.

## 2. Refatoracao

A chain principal ficou separada em tres partes:

```text
ChatPromptTemplate | ChatOllama | PydanticOutputParser
```

O projeto usa `ChatOllama`, mas com modelo remoto da Ollama Cloud. Assim o grupo nao precisa baixar modelo local.

Trade-off: o projeto depende de internet e chave de API, mas fica mais leve para rodar em qualquer computador.

## 3. Comparativo antes/depois

| Metrica | Sprints 1/2 - versao manual | Sprint 03 - LCEL |
|---|---:|---:|
| Qualidade das respostas | 3.5/5.0 | 5.0/5.0 |
| Tokens por turno | Nao era medido | 10.2 tokens/turno |
| Latencia media | Nao era medida | 1731.08 ms |
| Acuracia do structured output | Nao aplicavel | 100% |

## 4. Problemas encontrados e solucoes

### Problema 1 - historico sem limite

Antes o historico podia crescer sem controle. A solucao foi usar memoria por sessao com limite de tokens.

### Problema 2 - resposta sem formato fixo

Antes a resposta era texto livre. A solucao foi usar `ConsultaRecarga` com Pydantic v2 e parser estruturado.

### Problema 3 - risco de prompt injection

Foram adicionadas regras no prompt e validacao antes da chamada do modelo.

## 5. Equipe

| Integrante | RM | Tarefa principal |
|---|---:|---|
| Gabriel Camarosani Gouvea Goncalves da Silva | 569189 | Chain LCEL |
| Gustavo Lima Andrade Santos | 571709 | Memoria e testes |
| Lucas Seiji Hummel | 569673 | Schema Pydantic |
| Pedro Souza Castro | 569311 | Guardrails |
| Bruno Yudi Moritaka Kanashiro | 571776 | Prompt e documentacao |
| Lucas Barreto Santana | 573149 | Evals e comparativo |
