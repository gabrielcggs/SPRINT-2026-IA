# Relatório de uso de modelos e parâmetros — Sprint 03

## 1. Objetivo

No Sprint 3, o ChargeGrid Intelligence passou a utilizar `ChatOllama` dentro de uma cadeia LangChain LCEL. Para avaliar a influência do modelo no comportamento do chatbot, foram selecionados dois modelos locais:

- **qwen3:8b** — modelo principal para desenvolvimento e execução local.
- **llama3.2:3b** — segundo modelo utilizado para comparação.

A comparação utiliza a mesma arquitetura, o mesmo prompt versionado e os mesmos parâmetros de geração sempre que possível.

## 2. Modelos comparados

| Modelo | Função no projeto | Porte relativo | Uso |
|---|---|---|---|
| `qwen3:8b` | Principal | Maior | Execução principal e avaliação |
| `llama3.2:3b` | Comparação | Menor | Comparação e avaliação |

A escolha de dois modelos locais permite avaliar o trade-off entre capacidade do modelo e recursos computacionais. O `qwen3:8b` foi escolhido como principal por oferecer uma opção ainda viável para execução local, enquanto o `llama3.2:3b` representa uma alternativa mais leve.

## 3. Parâmetros de geração

| Parâmetro | Valor |
|---|---:|
| `temperature` | `0.1` |
| `top_p` | `0.9` |
| `max_tokens` | `512` |

### Temperature

Foi utilizado `temperature=0.1` para reduzir variações desnecessárias nas respostas. O chatbot trabalha com informações de carregadores, consumo, tarifas e gestão de energia, portanto respostas consistentes são desejáveis.

### Top P

Foi utilizado `top_p=0.9` para manter alguma diversidade na geração sem aumentar excessivamente a aleatoriedade.

### Max Tokens

Foi utilizado `max_tokens=512` para limitar o tamanho das respostas e evitar gerações excessivamente longas.

No `ChatOllama`, o limite é enviado ao Ollama por meio do parâmetro `num_predict`, correspondente ao limite de tokens de saída configurado pelo projeto.

## 4. Configuração

A configuração é feita por variáveis de ambiente:

```text
OLLAMA_MODEL=qwen3:8b
OLLAMA_MODEL_2=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434

TEMPERATURE=0.1
TOP_P=0.9
MAX_TOKENS=512
```

Dessa forma, o modelo pode ser alterado sem modificar a lógica principal da aplicação.

## 5. Estratégia de avaliação

Os dois modelos devem receber o mesmo conjunto de casos localizado em `evals/eval_set.json`.

São observadas as seguintes métricas:

- qualidade da resposta;
- aderência ao escopo GoodWe/ChargeGrid;
- respeito aos guardrails;
- validade do structured output;
- tokens de entrada por turno;
- latência da resposta.

A qualidade pode ser avaliada em uma escala de 0 a 5:

| Nota | Critério |
|---:|---|
| 5 | Correta, objetiva, dentro do escopo e adequada ao formato |
| 4 | Correta, com pequena limitação |
| 3 | Parcialmente adequada |
| 2 | Possui erro relevante |
| 1 | Pouco adequada |
| 0 | Incorreta, insegura ou inadequada |

## 6. Resultados

Os valores abaixo **não devem ser inventados**. Após executar `python evals/compare_models.py`, preencher a tabela com os resultados obtidos.

| Métrica | qwen3:8b | llama3.2:3b |
|---|---:|---:|
| Qualidade média (0–5) | A preencher | A preencher |
| Tokens médios/turno | A preencher | A preencher |
| Latência média (ms) | A preencher | A preencher |
| Structured output válido (%) | A preencher | A preencher |
| Casos adequados | A preencher | A preencher |

## 7. Análise

Após a execução, a equipe deve registrar qual modelo apresentou o melhor equilíbrio entre qualidade e desempenho.

A análise deve considerar que um modelo menor pode apresentar menor latência e exigir menos recursos, enquanto um modelo maior pode apresentar respostas mais completas em determinadas tarefas. A conclusão deve ser baseada nos resultados reais do conjunto de avaliação, e não apenas no tamanho dos modelos.

## 8. Conclusão

A arquitetura do projeto permite trocar o modelo local sem alterar a estrutura da cadeia LCEL. Isso facilita a comparação entre `qwen3:8b` e `llama3.2:3b`.

A escolha final do modelo deve considerar conjuntamente qualidade, latência, validade do structured output e disponibilidade de recursos computacionais.
