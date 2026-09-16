# Relatório de Evolução — Sprint 03

## 1. Resumo da evolução

Nas Sprints 1 e 2, o ChargeGrid Intelligence utilizava uma implementação manual em Python, com gerenciamento próprio de histórico e integração direta com provedores de IA. Na Sprint 03, o núcleo conversacional foi refatorado para LangChain LCEL, com memória por sessão, structured output Pydantic v2, context engineering e guardrails.

## 2. Refatoração

A principal decisão foi separar o fluxo em componentes: prompt, modelo, parser, memória e validações. O trade-off foi aumentar a quantidade de arquivos e dependências para obter uma arquitetura mais organizada e mensurável.

## 3. Comparativo antes/depois

A Sprint 03 também passou a permitir a comparação entre os modelos locais `qwen3:8b` e `llama3.2:3b`, mantendo a mesma cadeia LCEL, prompt e parâmetros documentados em `docs/relatorio_modelos.md`.

| Métrica | Sprints 1/2 — versão manual | Sprint 03 — LCEL |
|---|---:|---:|
| Qualidade das respostas | Preencher com eval anterior | Preencher com eval Sprint 3 |
| Tokens por turno | Não medido na Sprint 2 | Preencher |
| Latência média | Não medida na Sprint 2 | Preencher |
| Acurácia do structured output | Não aplicável | Preencher |

> Não preencher números sem execução dos testes.

## 4. Problemas encontrados e soluções

### Problema 1 — histórico sem limite de tokens
Solução: memória por sessão com política de limite de tokens e contagem com `tiktoken`.

### Problema 2 — respostas sem formato estruturado
Solução: Pydantic v2 com `PydanticOutputParser` e `field_validator`.

### Problema 3 — tentativas de prompt injection
Solução: validação prévia de segurança e regras explícitas no prompt versionado.

## 5. Equipe

| Integrante | RM | Tarefa principal |
|---|---:|---|
| Gabriel Camarosani | 569189 | Refatoração LCEL e integração |
| Gustavo Lima | 571709 | Memória e testes |
| Lucas Hummel | 569673 | Pydantic e structured output |
| Pedro Castro | 569311 | Guardrails e avaliação |
| Bruno Kanashiro | 571776 | Prompt engineering e documentação |
