# ChargeGrid Intelligence - Sprint 03

Projeto FIAP x GoodWe Brasil para um chatbot de recarga de veiculos eletricos.

Esta versao usa LangChain LCEL, memoria por sessao, Pydantic v2, prompt com XML tagging, guardrails e evals.

## Integrantes

| Nome | RM |
|---|---:|
| Gabriel Camarosani Gouvea Goncalves da Silva | 569189 |
| Gustavo Lima Andrade Santos | 571709 |
| Lucas Seiji Hummel | 569673 |
| Pedro Souza Castro | 569311 |
| Bruno Yudi Moritaka Kanashiro | 571776 |
| Lucas Barreto Santana | 573149 |

## Como o modelo funciona

O projeto nao usa modelo local e nao precisa baixar nada pelo Ollama.

Foi mantido `ChatOllama` porque ele aparece na rubrica da Sprint 03, mas apontando para a Ollama Cloud:

- modelo principal: `gpt-oss:120b-cloud`
- modelo de comparacao: `gpt-oss:20b-cloud`
- chave em variavel de ambiente: `OLLAMA_API_KEY`

## Instalar

```bash
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preencha a chave:

```text
OLLAMA_API_KEY=SUA_CHAVE_AQUI
```

O arquivo `.env` esta no `.gitignore`.

## Rodar

```bash
python src/main.py
```

## Testes

```bash
pytest -q
```

## Evals

```bash
python evals/run_evals.py
python evals/compare_models.py
```

Os resultados gerados ficam em:

- `evals/sprint3_results.json`
- `evals/model_comparison.json`

## Estrutura

- `prompts/`: prompts versionados e historico.
- `src/chain/`: builder LCEL e memoria.
- `src/schemas/`: schema Pydantic v2.
- `src/guardrails/`: validacao de seguranca e escopo.
- `evals/`: testes de avaliacao.
- `docs/`: relatorios da entrega.

## Itens da Sprint 03

- LCEL: `ChatPromptTemplate | ChatOllama | PydanticOutputParser`.
- Memoria: `RunnableWithMessageHistory` por `session_id`.
- Structured output: schema `ConsultaRecarga` com `field_validator`.
- Context engineering: prompt XML versionado e contagem com `tiktoken`.
- Guardrails: jailbreak, prompt injection, escopo GoodWe e riscos eletricos/juridicos/financeiros.
- Relatorios: `docs/relatorio_modelos.md` e `docs/relatorio_evolucao.md`.
