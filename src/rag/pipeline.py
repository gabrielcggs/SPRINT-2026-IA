"""Pipeline RAG end-to-end com grounding, citacao e recusa (Aulas 06 e 07).

Fluxo de ``RagPipeline.responder``:

1. ``verificar_entrada``: bloqueia jailbreak/injection/risco antes de tudo.
2. Retriever top-k no ChromaDB; trechos abaixo de ``min_score`` sao descartados.
3. Sem nenhum trecho relevante -> recusa SEM chamar o modelo (grounding por construcao).
4. ``sanitizar_recuperados``: remove frases de comando vindas dos documentos.
5. Prompt RAG versionado + LLM -> JSON {resposta, fontes, sem_contexto}.
6. Citacoes: ids [S#] validados contra os trechos realmente enviados ao modelo.
"""
from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass, field
from typing import Callable

from rag import prompt_rag
from rag.retriever import Busca, Recuperado, Retriever
from rag.security import sanitizar_recuperados, verificar_entrada

RECUSA_SEM_CONTEXTO = (
    f"{prompt_rag.FRASE_RECUSA} Posso ajudar com carregadores, tarifas, regras de "
    "recarga e uso do EV ChargeOps."
)

_PRONOMES = re.compile(
    r"\b(ele|ela|eles|elas|dele|dela|deles|delas|isso|esse|essa|esses|essas|desse|dessa|"
    r"nele|nela|qual deles|e qual|e quanto|e o|e a)\b",
    re.IGNORECASE,
)


@dataclass
class RagResposta:
    pergunta: str
    resposta: str
    recusado: bool = False
    motivo: str = "respondido"  # respondido | entrada_bloqueada | sem_contexto | modelo_sem_contexto | erro
    fontes: list[dict] = field(default_factory=list)       # trechos citados (ou consultados)
    citou: bool = False                                    # o modelo citou [S#] valido?
    recuperados: list[dict] = field(default_factory=list)  # top-k bruto, com score
    contextos: list[str] = field(default_factory=list)     # textos enviados ao modelo (para avaliacao)
    top1_score: float | None = None
    trechos_removidos: int = 0
    latency_ms: float = 0.0
    model: str = ""
    provider: str = ""
    prompt_version: str = ""
    erro: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _fonte_dict(r: Recuperado) -> dict:
    return {
        "id": r.id,
        "documento": r.documento,
        "pagina": r.pagina,
        "secao": r.secao,
        "score": r.score,
        "trecho": r.texto,
        "citacao": r.citacao(),
    }


class RagPipeline:
    def __init__(
        self,
        retriever: Retriever,
        provider: str = "ollama",
        model: str | None = None,
        prompt_version: str = prompt_rag.VERSAO_PADRAO,
        temperature: float = 0.0,
        top_p: float = 0.9,
        max_tokens: int = 1024,
        llm_factory: Callable[..., object] | None = None,
    ):
        self.retriever = retriever
        self.provider = provider
        self.model = model
        self.prompt_version = prompt_version
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        if llm_factory is None:
            from rag.llm import build_llm as llm_factory  # noqa: N813
        self._llm_factory = llm_factory
        self._llms: dict[tuple, object] = {}

    # ---------- LLM ----------
    def _llm(self, provider: str, model: str | None, temperature: float, top_p: float, max_tokens: int):
        chave = (provider, model, temperature, top_p, max_tokens)
        if chave not in self._llms:
            self._llms[chave] = self._llm_factory(
                provider=provider, model=model, temperature=temperature, top_p=top_p, max_tokens=max_tokens
            )
        return self._llms[chave]

    # ---------- recuperacao ----------
    @staticmethod
    def _consulta_busca(pergunta: str, historico: list[dict] | None) -> str:
        """Pergunta de seguimento ("e qual deles e mais potente?") herda o tema do turno anterior."""
        if historico and (len(pergunta.split()) <= 8 or _PRONOMES.search(pergunta)):
            return f"{historico[-1]['pergunta']} {pergunta}"
        return pergunta

    def _recuperar(self, pergunta, historico, k, min_score) -> tuple[Busca, list[Recuperado], int]:
        busca = self.retriever.buscar(self._consulta_busca(pergunta, historico), k=k, min_score=min_score)
        limpos, removidos = sanitizar_recuperados(busca.aceitos)
        return busca, limpos, removidos

    # ---------- geracao ----------
    def _gerar(self, base: RagResposta, pergunta, limpos, historico, provider, model, prompt_version,
               temperature, top_p, max_tokens) -> RagResposta:
        resp = RagResposta(**{**base.to_dict(), "model": model or "", "provider": provider,
                              "prompt_version": prompt_version})
        inicio = time.perf_counter()
        try:
            llm = self._llm(provider, model, temperature, top_p, max_tokens)
            mensagens = prompt_rag.montar_mensagens(prompt_version, pergunta, limpos, historico)
            saida = llm.invoke(mensagens)
            texto = getattr(saida, "content", saida)
            if isinstance(texto, list):  # alguns provedores devolvem blocos
                texto = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in texto)
        except Exception as exc:  # noqa: BLE001
            resp.resposta = "Não consegui gerar a resposta agora. Tente novamente em instantes."
            resp.motivo = "erro"
            resp.erro = f"{type(exc).__name__}: {exc}"
            resp.latency_ms = round((time.perf_counter() - inicio) * 1000, 1)
            return resp

        resp.latency_ms = round((time.perf_counter() - inicio) * 1000, 1)
        dado = prompt_rag.extrair_json(str(texto))
        if dado is None:
            resposta, sem_contexto, ids_json = str(texto).strip(), False, []
        else:
            resposta = str(dado.get("resposta", "")).strip() or str(texto).strip()
            sem_contexto = bool(dado.get("sem_contexto", False))
            ids_json = [str(x) for x in (dado.get("fontes") or [])]

        validos = {r.id for r in limpos}
        citados = prompt_rag.ids_citados(resposta, validos)
        for sid in ids_json:
            sid = sid.strip("[] ")
            if sid in validos and sid not in citados:
                citados.append(sid)

        recusou = sem_contexto or resposta.startswith(prompt_rag.FRASE_RECUSA)
        resp.resposta = resposta
        if recusou:
            resp.recusado, resp.motivo, resp.fontes, resp.citou = True, "modelo_sem_contexto", [], False
            return resp

        por_id = {r.id: r for r in limpos}
        if citados:
            resp.fontes = [_fonte_dict(por_id[i]) for i in citados]
            resp.citou = True
        else:  # respondeu sem citar: mostra o que foi consultado, mas marca citou=False
            resp.fontes = [_fonte_dict(r) for r in limpos]
            resp.citou = False
        return resp

    # ---------- API publica ----------
    def _preparar(self, pergunta, historico, k, min_score):
        pergunta = (pergunta or "").strip()
        base = RagResposta(pergunta=pergunta, resposta="")
        if not pergunta:
            base.resposta, base.recusado, base.motivo = "Digite uma pergunta sobre recarga de veículos elétricos.", True, "entrada_bloqueada"
            return base, None, None

        bloqueio = verificar_entrada(pergunta)
        if bloqueio:
            base.resposta, base.recusado, base.motivo = bloqueio, True, "entrada_bloqueada"
            return base, None, None

        busca, limpos, removidos = self._recuperar(pergunta, historico, k, min_score)
        base.recuperados = [_fonte_dict(r) for r in busca.todos]
        base.top1_score = busca.top1_score
        base.trechos_removidos = removidos
        if not limpos:
            base.resposta, base.recusado, base.motivo = RECUSA_SEM_CONTEXTO, True, "sem_contexto"
            return base, None, None
        base.contextos = [r.texto for r in limpos]
        return base, limpos, pergunta

    def responder(
        self,
        pergunta: str,
        historico: list[dict] | None = None,
        *,
        provider: str | None = None,
        model: str | None = None,
        prompt_version: str | None = None,
        k: int | None = None,
        min_score: float | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
    ) -> RagResposta:
        inicio = time.perf_counter()
        base, limpos, pergunta_ok = self._preparar(pergunta, historico, k, min_score)
        provider = provider or self.provider
        model = model if model is not None else self.model
        versao = prompt_version or self.prompt_version
        if limpos is None:
            base.provider, base.model, base.prompt_version = provider, model or "", versao
            base.latency_ms = round((time.perf_counter() - inicio) * 1000, 1)
            return base
        resp = self._gerar(
            base, pergunta_ok, limpos, historico, provider, model, versao,
            self.temperature if temperature is None else temperature,
            self.top_p if top_p is None else top_p,
            max_tokens or self.max_tokens,
        )
        resp.latency_ms = round((time.perf_counter() - inicio) * 1000, 1)
        return resp

    def responder_multi(
        self,
        pergunta: str,
        variantes: list[dict],
        historico: list[dict] | None = None,
        k: int | None = None,
        min_score: float | None = None,
    ) -> list[RagResposta]:
        """Bonus multi-provider: a MESMA recuperacao alimenta varias variantes.

        Cada variante e um dict com ``provider``, ``model`` e ``prompt_version``
        (opcionalmente ``temperature``, ``top_p``, ``max_tokens``).
        """
        base, limpos, pergunta_ok = self._preparar(pergunta, historico, k, min_score)
        resultados: list[RagResposta] = []
        for v in variantes:
            provider = v.get("provider", self.provider)
            model = v.get("model", self.model)
            versao = v.get("prompt_version", self.prompt_version)
            if limpos is None:
                r = RagResposta(**base.to_dict())
                r.provider, r.model, r.prompt_version = provider, model or "", versao
                resultados.append(r)
                continue
            resultados.append(self._gerar(
                base, pergunta_ok, limpos, historico, provider, model, versao,
                v.get("temperature", self.temperature), v.get("top_p", self.top_p),
                v.get("max_tokens", self.max_tokens),
            ))
        return resultados


def abrir_pipeline(
    *,
    embeddings=None,
    k: int | None = None,
    min_score: float | None = None,
    prompt_version: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    chunking=None,
    llm_factory=None,
) -> RagPipeline:
    """Monta o pipeline sobre o indice ChromaDB ja persistido (rode scripts/ingest.py antes)."""
    from rag import config
    from rag.embeddings import build_embeddings
    from rag.vector_store import get_vector_store, total_chunks

    cfg = chunking or config.chunking_padrao()
    emb = embeddings or build_embeddings(config.embedding_provider(), config.embedding_model())
    colecao = config.nome_colecao(cfg)
    store = get_vector_store(emb, config.persist_dir(), colecao)
    if total_chunks(store) == 0:
        raise RuntimeError(
            f"A colecao '{colecao}' esta vazia. Rode: python scripts/gerar_base_conhecimento.py "
            "e depois python scripts/ingest.py"
        )
    retriever = Retriever(store, k=k or config.top_k(),
                          min_score=config.min_score() if min_score is None else min_score)
    return RagPipeline(
        retriever,
        provider=provider or config.llm_provider(),
        model=model or config.llm_model(),
        prompt_version=prompt_version or config.prompt_version(),
        temperature=config.llm_temperature(),
        top_p=config.llm_top_p(),
        max_tokens=config.llm_max_tokens(),
        llm_factory=llm_factory,
    )
