"""Interface web do ChargeGrid Intelligence (Aula 08) - Streamlit.

    streamlit run app/streamlit_app.py

Mostra a resposta do RAG com as FONTES VISIVEIS (documento, pagina, secao, trecho)
e permite trocar modelo, prompt e parametros na barra lateral. O modo "Comparar"
consulta duas variantes (modelo + prompt) sobre a mesma recuperacao (bonus multi-provider).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag import config, prompt_rag  # noqa: E402
from rag.embeddings import build_embeddings  # noqa: E402
from rag.ingest import ingerir  # noqa: E402
from rag.llm import PROVEDORES  # noqa: E402
from rag.pipeline import RagResposta, abrir_pipeline  # noqa: E402
from rag.vector_store import ler_manifesto  # noqa: E402

st.set_page_config(page_title="ChargeGrid Intelligence", page_icon="⚡", layout="wide")

EXEMPLOS = [
    "Quais carregadores estão disponíveis agora?",
    "Quanto custa uma hora de recarga no CG-02?",
    "Qual o tempo máximo de uma sessão e a taxa de ociosidade?",
    "Quando o sistema envia o alerta de sobrecarga?",
]


@st.cache_resource(show_spinner="Abrindo o índice ChromaDB...")
def carregar_pipeline():
    return abrir_pipeline()


def mostrar_resposta(r: RagResposta, titulo: str | None = None) -> None:
    if titulo:
        st.markdown(f"**{titulo}**")
    if r.recusado:
        st.warning(r.resposta)
    else:
        st.markdown(r.resposta)

    if r.fontes:
        rotulo = "Fontes citadas" if r.citou else "Trechos consultados (o modelo não citou)"
        with st.expander(f"📎 {rotulo} ({len(r.fontes)})", expanded=r.citou):
            for f in r.fontes:
                st.markdown(f"**[{f['id']}] {f['documento']}** — p. {f['pagina']}, seção {f['secao']} · relevância {f['score']:.2f}")
                st.caption(f["trecho"])
    elif not r.recusado:
        st.caption("Sem fontes associadas a esta resposta.")

    meta = [f"{r.provider}:{r.model}", f"prompt {r.prompt_version}", f"{r.latency_ms:.0f} ms"]
    if r.top1_score is not None:
        meta.append(f"melhor trecho {r.top1_score:.2f}")
    if r.trechos_removidos:
        meta.append(f"⚠ {r.trechos_removidos} frase(s) suspeita(s) removida(s) dos documentos")
    if r.erro:
        meta.append(f"erro: {r.erro}")
    st.caption(" · ".join(meta))


# ----------------------------- barra lateral -----------------------------
with st.sidebar:
    st.header("Configuração")
    provider = st.selectbox("Provedor", PROVEDORES, index=PROVEDORES.index(config.llm_provider()) if config.llm_provider() in PROVEDORES else 0)
    modelo = st.text_input("Modelo", value=config.llm_model())
    versao = st.selectbox("Versão do prompt RAG", prompt_rag.versoes(), index=prompt_rag.versoes().index(config.prompt_version()))
    st.caption(prompt_rag.PROMPTS[versao]["descricao"])
    k = st.slider("k (trechos recuperados)", 1, 8, config.top_k())
    min_score = st.slider("Relevância mínima", 0.0, 1.0, config.min_score(), 0.01)
    temperature = st.slider("temperature", 0.0, 1.0, config.llm_temperature(), 0.05)
    top_p = st.slider("top_p", 0.1, 1.0, config.llm_top_p(), 0.05)
    max_tokens = st.number_input("max_tokens", 128, 4096, config.llm_max_tokens(), 64)

    st.divider()
    comparar = st.toggle("Comparar com outra variante (multi-provider)")
    if comparar:
        provider2 = st.selectbox("Provedor B", PROVEDORES, index=0, key="p2")
        modelo2 = st.text_input("Modelo B", value=os.getenv("OLLAMA_MODEL_2", "gpt-oss:20b-cloud"), key="m2")
        versao2 = st.selectbox("Prompt B", prompt_rag.versoes(), index=0, key="v2")

    st.divider()
    cfg = config.chunking_padrao()
    manifesto = ler_manifesto(config.persist_dir(), config.nome_colecao(cfg))
    if manifesto:
        st.caption(f"Base: {len(manifesto['documentos'])} documentos · {manifesto['chunks_na_colecao']} chunks · {manifesto['chunking']['chunk_size']}/{manifesto['chunking']['chunk_overlap']} ({manifesto['chunking']['modo']})")
    if st.button("Reindexar base de conhecimento"):
        with st.spinner("Indexando..."):
            ingerir(config.kb_dir(), config.persist_dir(), config.nome_colecao(cfg), cfg,
                    build_embeddings(config.embedding_provider(), config.embedding_model()), reset=True,
                    log=lambda m: st.toast(m))
        st.cache_resource.clear()
        st.rerun()
    if st.button("Limpar conversa"):
        st.session_state.mensagens = []
        st.rerun()

# ----------------------------- conversa -----------------------------
st.title("⚡ ChargeGrid Intelligence")
st.caption("Assistente RAG da GoodWe Brasil para recarga de veículos elétricos · responde só com a base de conhecimento e cita a fonte")

try:
    pipeline = carregar_pipeline()
except Exception as exc:  # noqa: BLE001
    st.error(f"Não foi possível abrir o pipeline: {exc}")
    st.info("Passos: `python scripts/gerar_base_conhecimento.py` → `python scripts/ingest.py` → configure OLLAMA_API_KEY no .env")
    st.stop()

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            for i, r in enumerate(msg["respostas"]):
                mostrar_resposta(r, msg["titulos"][i] if len(msg["respostas"]) > 1 else None)

if not st.session_state.mensagens:
    st.write("Experimente:")
    colunas = st.columns(len(EXEMPLOS))
    for col, exemplo in zip(colunas, EXEMPLOS):
        if col.button(exemplo, use_container_width=True):
            st.session_state.pergunta_pendente = exemplo
            st.rerun()

pergunta = st.chat_input("Pergunte sobre carregadores, tarifas, regras de recarga...") or st.session_state.pop("pergunta_pendente", None)

if pergunta:
    historico = [
        {"pergunta": a["content"], "resposta": b["respostas"][0].resposta}
        for a, b in zip(st.session_state.mensagens[::2], st.session_state.mensagens[1::2])
    ]
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Buscando na base e gerando a resposta..."):
            variante_a = {"provider": provider, "model": modelo, "prompt_version": versao,
                          "temperature": temperature, "top_p": top_p, "max_tokens": int(max_tokens)}
            if comparar:
                variante_b = {**variante_a, "provider": provider2, "model": modelo2, "prompt_version": versao2}
                respostas = pipeline.responder_multi(pergunta, [variante_a, variante_b], historico, k=k, min_score=min_score)
                titulos = [f"A · {provider}:{modelo} · prompt {versao}", f"B · {provider2}:{modelo2} · prompt {versao2}"]
                colunas = st.columns(2)
                for col, r, t in zip(colunas, respostas, titulos):
                    with col:
                        mostrar_resposta(r, t)
            else:
                r = pipeline.responder(pergunta, historico, k=k, min_score=min_score, **variante_a)
                respostas, titulos = [r], [""]
                mostrar_resposta(r)
    st.session_state.mensagens.append({"role": "assistant", "respostas": respostas, "titulos": titulos})
