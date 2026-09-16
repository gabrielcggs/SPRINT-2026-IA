# ChargeGrid Intelligence — Sprint 03

Projeto do EV Challenge 2026 da FIAP × GoodWe Brasil. Esta versão evolui o chatbot das Sprints 1 e 2 para uma arquitetura com **LangChain LCEL**, memória por sessão, **Pydantic v2**, context engineering e guardrails.

## Integrantes

| Nome | RM |
|---|---:|
| Gabriel Camarosani Gouvea Goncalves da Silva | 569189 |
| Gustavo Lima Andrade Santos | 571709 |
| Lucas Seiji Hummel | 569673 |
| Pedro Souza Castro | 569311 |
| Bruno Yudi Moritaka Kanashiro | 571776 |
| Lucas Barreto Santana | 573149 |

## Estrutura

- `prompts/`: prompts versionados.
- `src/chain/`: LCEL e memória.
- `src/schemas/`: schema Pydantic.
- `src/guardrails/`: segurança e escopo.
- `evals/`: conjunto de avaliação e comparação dos modelos.
- `docs/`: relatórios.

## Modelos locais

O projeto foi configurado para comparar dois modelos locais no Ollama:

- **qwen3:8b** — modelo principal para desenvolvimento e execução local.
- **llama3.2:3b** — segundo modelo para comparação.

A escolha prioriza a execução em computadores com recursos mais limitados, mantendo dois modelos de tamanhos diferentes para avaliar o trade-off entre qualidade e custo computacional.

## Requisitos

- Python 3.10+
- Ollama instalado e em execução.
- `qwen3:8b`
- `llama3.2:3b`

Instale as dependências:

```bash
pip install -r requirements.txt
```

Baixe os modelos no Ollama:

```bash
ollama pull qwen3:8b
ollama pull llama3.2:3b
```

## Configuração

Copie `.env.example` para `.env` e ajuste os parâmetros se necessário. Nunca publique o `.env`.

Configuração padrão:

```text
OLLAMA_MODEL=qwen3:8b
OLLAMA_MODEL_2=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434
TEMPERATURE=0.1
TOP_P=0.9
MAX_TOKENS=512
MAX_HISTORY_TOKENS=2000
```

## Execução

Na raiz:

```bash
python src/main.py
```

Para testar o segundo modelo, altere temporariamente `OLLAMA_MODEL` no `.env` para:

```text
OLLAMA_MODEL=llama3.2:3b
```

## Testes

```bash
pytest -q
```

## Avaliação

```bash
python evals/run_evals.py
```

O arquivo `evals/sprint3_results.json` será gerado com resposta, latência, tokens e validade do structured output. A revisão qualitativa deve ser feita pelo grupo antes do relatório final.

Para comparar os dois modelos com o mesmo conjunto de avaliação:

```bash
python evals/compare_models.py
```

O script executa o eval set separadamente para `qwen3:8b` e `llama3.2:3b` e salva os resultados em `evals/model_comparison.json`.

## Requisitos atendidos

- Chain LCEL `prompt | llm | parser`.
- `RunnableWithMessageHistory`.
- Memória com limite de tokens e uso de `ConversationTokenBufferMemory` quando disponível.
- Pydantic v2 + `field_validator`.
- Prompt XML versionado.
- Medição de tokens com `tiktoken`.
- Guardrails para escopo, jailbreak, prompt injection e segurança.
- Eval set com happy path, edge cases, jailbreak e out-of-scope.
- Comparação de `qwen3:8b` e `llama3.2:3b`.
- Parâmetros documentados: `temperature`, `top_p` e `max_tokens`.

## Relatórios

- `docs/relatorio_modelos.md`
- `docs/relatorio_evolucao.md`
- `docs/relatorio_evolucao.pdf`

Os números de qualidade, latência e structured output devem ser preenchidos somente após a execução dos testes.

