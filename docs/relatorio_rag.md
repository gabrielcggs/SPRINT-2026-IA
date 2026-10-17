# Relatório do RAG — Sprint 04

> Os números deste relatório vêm de `evals/results/*.json`. Gere as tabelas com
> `python evals/gerar_tabelas.py` e cole nos pontos marcados. Não digite métricas à mão.

## 1. Pipeline

```text
PDFs (data/knowledge_base/)
  -> PyMuPDFLoader                       src/rag/loader.py
  -> RecursiveCharacterTextSplitter      src/rag/chunking.py
  -> nomic-embed-text (Ollama Cloud)     src/rag/embeddings.py
  -> ChromaDB persistente (cosseno)      src/rag/vector_store.py
  -> retriever top-k + corte de score    src/rag/retriever.py
  -> sanitização anti-injection          src/rag/security.py
  -> prompt RAG versionado               src/rag/prompt_rag.py
  -> LLM (Ollama Cloud / outro)          src/rag/llm.py
  -> resposta JSON + citação [S#]        src/rag/pipeline.py
```

## 2. Base de conhecimento

Cinco PDFs em `data/knowledge_base/`, todos **simulados** (gerados por
`scripts/gerar_base_conhecimento.py`) e identificados como tal no próprio documento:

| Documento | Conteúdo |
|---|---|
| `manual_chargegrid_goodwe.pdf` | carregadores CG-01 a CG-04, estado operacional, consumo e demanda |
| `manual_ev_chargeops.pdf` | monitoramento, alertas de sobrecarga, reservas, relatórios, perfis |
| `regimento_condominial_recarga.pdf` | quem usa, tempo de uso, ociosidade, segurança, rateio, penalidades |
| `faq_recarga.pdf` | disponibilidade, custos, problemas e segurança |
| `tabela_tarifaria.pdf` | tarifa padrão, janela econômica, taxa de ociosidade, exemplos de cálculo |

> Se o grupo usar manuais reais da GoodWe, troque/adicione os PDFs e rode `python scripts/ingest.py --reset`.

## 3. Estratégia de chunking

Configuração padrão: `chunk_size=700`, `chunk_overlap=100`, modo `secao`, com cabeçalho `[documento | seção]`.

- **Por seção:** o texto é separado nos títulos numerados ("2. Carregadores…") antes de dividir. Nenhum chunk mistura duas seções, então a citação "documento, página, seção" é exata.
- **Cabeçalho contextual:** cada chunk começa com `[documento | seção]`, o que ajuda a busca semântica a distinguir, por exemplo, a "tarifa" do regimento da "tarifa" da tabela.
- **Overlap de 100:** evita cortar uma regra ao meio quando uma seção passa de 700 caracteres.
- **IDs determinísticos:** reindexar a mesma base não duplica chunks nem gasta embeddings.

Trade-offs: chunks menores aumentam a precisão do trecho citado, mas perdem contexto; chunks maiores trazem mais contexto, mas diluem o vetor. A comparação medida entre configurações fica na tabela abaixo.

<!-- COLE AQUI a tabela "Evolução por iteração" de python evals/gerar_tabelas.py -->

## 4. Versões do prompt RAG

| Versão | O que mudou | Ganho medido |
|---|---|---|
| v1 | Baseline: "use o contexto". | referência |
| v2 | Citação obrigatória `[S#]` e frase fixa de recusa. | <!-- preencher com a linha da iteração v2 vs v1 --> |
| v3 | Contexto em XML tratado como dado, regras anti-injection e anti-invenção, cálculo só com o contexto, recusa de risco elétrico/jurídico/financeiro. | <!-- preencher com a linha da iteração v3 vs v2 --> |

## 5. Grounding, segurança e guardrails

Camadas independentes (a falha de uma não derruba as outras):

1. **Entrada** (`security.verificar_entrada`): jailbreak, prompt injection, intervenção elétrica, aconselhamento jurídico/financeiro. Bloqueia **antes** de buscar ou chamar o modelo.
2. **Relevância** (`Retriever.min_score`): sem trecho acima do limiar, o sistema recusa **sem chamar o modelo**. Limiar calibrado com `scripts/calibrar_limiar.py`.
3. **Documentos** (`security.sanitizar_recuperados`): frases de comando dentro dos PDFs ("ignore as instruções…", "revele o prompt…") são removidas dos trechos e as tags do contexto são escapadas. Teste: `tests/test_rag_offline.py::test_injecao_dentro_do_documento_e_removida_do_prompt`. Demonstração: `python scripts/gerar_base_conhecimento.py --com-injecao` cria um PDF malicioso para ingerir.
4. **Prompt v3**: o conteúdo de `<contexto>` é dado, nunca instrução; não inventar produtos nem especificações; citar `[S#]` em toda informação.
5. **Citação validada**: só contam ids `[S#]` que existem entre os trechos realmente enviados ao modelo. Uma citação inventada (`[S9]`) é descartada e a resposta fica marcada como "não citou".

## 6. Avaliação

Eval set: `evals/rag_eval_set.json` (23 casos: factual, cálculo, regimento, procedimento, memória, produto inexistente, dado ausente, fora de contexto, jailbreak e risco).

Métricas por iteração: `faithfulness` e `answer_relevancy` (RAGAS ou rubrica manual de 0 a 1 — critérios em `evals/run_rag_eval.py::RUBRICAS` e gravados no JSON), mais `contem_esperado`, `hit_fonte`, `citacao` e `recusa_correta`, todas determinísticas.

**Equivalência da rubrica manual:** a rubrica reproduz as definições do RAGAS — `faithfulness` é a fração de afirmações da resposta apoiadas no contexto; `answer_relevancy` mede se a resposta atende à pergunta (recusa indevida vale 0) — aplicadas ao mesmo eval set em todas as iterações. <!-- Se rodar com --metrica ragas, troque este parágrafo pelo resultado e cite a versão do ragas. -->

**Limitação a declarar:** o juiz é um LLM (por padrão o mesmo modelo que gera). Para reduzir viés, use `--juiz-model` com outro modelo.

## 7. Problemas encontrados e soluções

1. **Listas numeradas viravam "seções".** O detector de títulos (`1. Texto`) tratava "1. Abra o app" como seção e quebrava a citação. *Decisão:* escrever listas com "Passo 1 –" nos documentos; títulos só em linha própria, numerados.
2. **Filtro anti-injection removendo texto legítimo.** Uma regra como "não ignore as regras do condomínio" casaria com o padrão de ataque. *Decisão:* redigir a base sem esse tipo de frase e cobrir isso com `test_base_de_conhecimento_simulada_nao_dispara_o_filtro`, que falha se algum PDF da base acionar o filtro.
3. **`scope_validator` da Sprint 03 não filtrava nada.** A lista de ~1000 termos genéricos ("tempo", "valor", "sistema") aprovava quase qualquer pergunta. *Decisão:* a recusa passou a vir da recuperação (limiar de relevância) e do prompt; só os termos de segurança foram mantidos.
4. **JSON truncado com `max_tokens=512`.** Respostas com citações não cabiam. *Decisão:* subir para 1024 no RAG (`RAG_MAX_TOKENS`).

<!-- Acrescente aqui os problemas que o grupo viveu nas iterações de avaliação (ex.: limiar de relevância sobrepondo perguntas dentro/fora do contexto). -->
