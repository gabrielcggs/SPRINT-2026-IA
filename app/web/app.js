/* ChargeGrid Intelligence — frontend sem dependências.
   Fala com app/web_server.py (GET /api/config, POST /api/chat).
   Todo texto vindo do modelo ou dos documentos entra no DOM via textContent. */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const STORAGE_KEY = "chargegrid.ajustes.v1";
  const MAX_HISTORICO = 3;
  const SUGESTOES = [
    "Quais carregadores estão disponíveis agora?",
    "Quanto custa uma hora de recarga no CG-02 na tarifa padrão?",
    "Qual é o tempo máximo de uma sessão e a taxa de ociosidade?",
    "Qual é a janela econômica e quanto custa o kWh nela?",
  ];
  const MOTIVOS = {
    entrada_bloqueada: {
      titulo: "Pergunta bloqueada",
      texto: "A pergunta parece tentar mudar as regras do assistente, então nem chegou à base.",
    },
    sem_contexto: {
      titulo: "Sem informação na base",
      texto: (r) => {
        const min = r.min_score_usado != null ? r.min_score_usado.toFixed(2) : "?";
        return `Nenhum trecho da base chegou à relevância mínima (${min}). O modelo não foi consultado.`;
      },
    },
    modelo_sem_contexto: {
      titulo: "Sem informação na base",
      texto: "Havia trechos parecidos com o tema, mas o modelo concluiu que nenhum traz a resposta.",
    },
  };

  const estado = {
    config: null,
    ajustes: null,
    turnos: [],          // {pergunta, respostas:[...], erro, carregando}
    selecao: null,       // {turno, variante, aba}
    enviando: false,
  };

  /* ---------- utilidades ---------- */
  function el(tag, cls, texto) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (texto != null) n.textContent = texto;
    return n;
  }

  function limpar(no) { while (no.firstChild) no.removeChild(no.firstChild); }

  function lerArmazenado() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null"); } catch (_) { return null; }
  }
  function gravarArmazenado(v) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(v)); } catch (_) { /* sem armazenamento: segue em memória */ }
  }

  function padroesAjustes(cfg) {
    const p = cfg.padroes;
    return {
      provider: p.provider, model: p.model, prompt_version: p.prompt_version,
      k: p.k, min_score: p.min_score, temperature: p.temperature, top_p: p.top_p, max_tokens: p.max_tokens,
      comparar: false,
      provider_b: p.provider, model_b: p.model_b, prompt_b: p.prompt_version,
    };
  }

  /* ---------- texto com chips [S#] ---------- */
  function escreverTexto(container, texto, idsValidos, aoClicar) {
    limpar(container);
    const partes = String(texto).split(/(\[S\d+\])/g);
    for (const parte of partes) {
      const m = /^\[(S\d+)\]$/.exec(parte);
      if (m && idsValidos.has(m[1])) {
        const chip = el("button", "cite", m[1]);
        chip.type = "button";
        chip.setAttribute("aria-label", `Ver trecho ${m[1]}`);
        chip.addEventListener("click", () => aoClicar(m[1]));
        container.appendChild(chip);
      } else if (parte) {
        container.appendChild(document.createTextNode(parte));
      }
    }
  }

  /* ---------- medidor de relevância ---------- */
  function medidor(score, minimo) {
    const SEGMENTOS = 10;
    const box = el("div", "medidor");
    box.setAttribute("role", "img");
    box.setAttribute("aria-label", `Relevância ${score.toFixed(2)}${minimo != null ? `, mínimo ${minimo.toFixed(2)}` : ""}`);
    const barras = el("span", "medidor-barras");
    const cheias = Math.round(Math.max(0, Math.min(1, score)) * SEGMENTOS);
    for (let i = 0; i < SEGMENTOS; i++) barras.appendChild(el("i", i < cheias ? "cheia" : ""));
    if (minimo != null && minimo > 0) {
      const marca = el("span", "medidor-minimo");
      // 12px de barra + 3px de espaço por segmento
      marca.style.left = `${Math.max(0, Math.min(1, minimo)) * (SEGMENTOS * 15 - 3)}px`;
      marca.title = `Relevância mínima ${minimo.toFixed(2)}`;
      barras.appendChild(marca);
    }
    box.appendChild(barras);
    box.appendChild(el("span", "medidor-valor", score.toFixed(2)));
    return box;
  }

  /* ---------- estado vazio / pendente ---------- */
  function renderVazio(alvo) {
    const cfg = estado.config;
    const sec = el("section", "vazio");
    if (cfg && !cfg.pronto) {
      const p = el("div", "pendente");
      p.appendChild(el("h2", null, "A base de conhecimento ainda não está pronta"));
      p.appendChild(el("p", null, "O assistente precisa do índice de documentos para responder. No terminal, na pasta do projeto:"));
      p.appendChild(el("pre", null, "ollama pull nomic-embed-text\npython scripts/gerar_base_conhecimento.py\npython scripts/ingest.py --reset"));
      p.appendChild(el("p", null, "Depois é só atualizar esta página."));
      if (cfg.erro) p.appendChild(el("p", null, `Detalhe: ${cfg.erro}`));
      sec.appendChild(p);
      alvo.appendChild(sec);
      return;
    }
    sec.appendChild(el("h2", null, "Pergunte sobre a recarga do seu condomínio"));
    sec.appendChild(el("p", null, "Cada resposta vem com os trechos dos documentos que a sustentam. Se a base não tem a informação, o assistente diz isso em vez de inventar."));
    const lista = el("ul", "sugestoes");
    for (const s of SUGESTOES) {
      const li = el("li");
      const b = el("button", "sugestao", s);
      b.type = "button";
      b.addEventListener("click", () => enviar(s));
      li.appendChild(b);
      lista.appendChild(li);
    }
    sec.appendChild(lista);
    if (cfg && cfg.base) {
      const docs = cfg.base.documentos;
      const n = Array.isArray(docs) ? docs.length : docs;
      sec.appendChild(el("p", "base-info", `Base atual: ${n} documentos, ${cfg.base.chunks} trechos indexados.`));
    }
    alvo.appendChild(sec);
  }

  /* ---------- conversa ---------- */
  function renderConversa() {
    const alvo = $("conversa");
    limpar(alvo);
    if (!estado.turnos.length) { renderVazio(alvo); return; }

    estado.turnos.forEach((t, ti) => {
      const turno = el("article", "turno");
      turno.appendChild(el("h2", "pergunta", t.pergunta));

      if (t.carregando) {
        const c = el("div", "carregando");
        const m = el("span", "carregando-medidor");
        for (let i = 0; i < 5; i++) m.appendChild(el("i"));
        c.appendChild(m);
        c.appendChild(el("span", null, "Buscando na base e consultando o modelo"));
        turno.appendChild(c);
      } else if (t.erro) {
        turno.appendChild(el("p", "erro-msg", t.erro));
      } else {
        const wrap = el("div", "respostas" + (t.respostas.length > 1 ? " dupla" : ""));
        t.respostas.forEach((r, vi) => wrap.appendChild(renderResposta(r, ti, vi, t.respostas.length > 1)));
        turno.appendChild(wrap);
      }
      alvo.appendChild(turno);
    });
  }

  function renderResposta(r, ti, vi, multi) {
    const box = el("section", "resposta");
    if (multi) box.appendChild(el("p", "resposta-rotulo", `Variante ${"AB"[vi] || vi + 1}: ${r.model || "?"} · ${r.prompt_version}`));

    const abrir = (aba, id) => selecionar(ti, vi, aba, id);
    const temRecuperados = (r.recuperados || []).length > 0;

    if (r.erro) {
      box.appendChild(el("p", "erro-msg", mensagemErro(r.erro)));
    } else if (r.recusado) {
      const info = MOTIVOS[r.motivo] || MOTIVOS.modelo_sem_contexto;
      const rec = el("div", "recusa");
      rec.appendChild(el("p", "recusa-titulo", info.titulo));
      rec.appendChild(el("p", "recusa-motivo", typeof info.texto === "function" ? info.texto(r) : info.texto));
      if (temRecuperados) {
        const b = el("button", "link-fontes", "Ver o que foi encontrado");
        b.type = "button";
        b.addEventListener("click", () => abrir("recuperadas"));
        rec.appendChild(b);
      }
      box.appendChild(rec);
    } else {
      const texto = el("p", "resposta-texto");
      const ids = new Set((r.fontes || []).map((f) => f.id));
      escreverTexto(texto, r.resposta, ids, (id) => abrir("citadas", id));
      box.appendChild(texto);
    }

    const sob = el("div", "sob-resposta");
    if (!r.erro && !r.recusado) {
      const n = (r.fontes || []).length;
      const b = el("button", "link-fontes", n ? `${n} ${n === 1 ? "trecho citado" : "trechos citados"}` : "Ver trechos consultados");
      b.type = "button";
      b.addEventListener("click", () => abrir(n && r.citou ? "citadas" : "recuperadas"));
      sob.appendChild(b);
    }
    const meta = el("span", "meta");
    const semModelo = r.motivo === "entrada_bloqueada" || r.motivo === "sem_contexto";
    if (!semModelo && r.latency_ms != null) meta.appendChild(el("span", null, `${(r.latency_ms / 1000).toFixed(1)} s`));
    if (!semModelo && r.model) meta.appendChild(el("span", null, r.model));
    if (!semModelo && r.prompt_version) meta.appendChild(el("span", null, `prompt ${r.prompt_version}`));
    sob.appendChild(meta);
    box.appendChild(sob);
    return box;
  }

  function mensagemErro(txt) {
    const t = String(txt || "");
    if (/connect|refused|11434|timed out|timeout/i.test(t)) {
      return `Não consegui falar com o modelo. Confira se o Ollama está aberto e tente de novo. (${t})`;
    }
    if (/401|unauthor|api[_ ]?key/i.test(t)) {
      return `O provedor recusou a chave de API. Confira o arquivo .env. (${t})`;
    }
    return `Não foi possível gerar a resposta. ${t}`;
  }

  /* ---------- evidência ---------- */
  function selecionar(ti, vi, aba, idDestaque) {
    estado.selecao = { turno: ti, variante: vi, aba };
    renderEvidencia(idDestaque);
    if (window.matchMedia("(max-width: 900px)").matches) abrirFolha(true);
  }

  function abrirFolha(abrir) {
    $("evidencia").classList.toggle("aberta", abrir);
    $("cortina").hidden = !abrir;
  }

  function renderEvidencia(idDestaque) {
    const sel = estado.selecao;
    const corpo = $("evid-corpo");
    const abas = $("evid-abas");
    const seletor = $("evid-variantes");
    limpar(corpo); limpar(abas); limpar(seletor);

    if (!sel) {
      $("evid-pergunta").textContent = "";
      seletor.hidden = true;
      corpo.appendChild(el("p", "evid-vazio", "Os trechos dos documentos que sustentam cada resposta aparecem aqui. Clique em um [S1] na resposta ou em “trechos citados”."));
      return;
    }

    const turno = estado.turnos[sel.turno];
    const r = turno.respostas[sel.variante];
    $("evid-pergunta").textContent = turno.pergunta;

    seletor.hidden = turno.respostas.length < 2;
    if (!seletor.hidden) {
      turno.respostas.forEach((_, i) => {
        const b = el("button", "seletor-botao", `Variante ${"AB"[i] || i + 1}`);
        b.type = "button";
        b.setAttribute("aria-pressed", String(i === sel.variante));
        b.addEventListener("click", () => { estado.selecao.variante = i; renderEvidencia(); });
        seletor.appendChild(b);
      });
    }

    const citadas = r.citou ? (r.fontes || []) : [];
    const idsCitados = new Set(citadas.map((f) => f.id));
    const recuperadas = (r.recuperados || []).map((x) => ({
      id: x.id, documento: x.documento, pagina: x.pagina, secao: x.secao, score: x.score, trecho: x.trecho,
    }));
    // o servidor remove do prompt trechos com instrução suspeita; aqui só sinalizamos os não citados
    const abasDef = [
      { id: "citadas", rotulo: "Citadas", itens: citadas },
      { id: "recuperadas", rotulo: "Recuperadas", itens: recuperadas },
    ];
    abasDef.forEach((a) => {
      const b = el("button", "aba", a.rotulo);
      b.type = "button";
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", String(a.id === sel.aba));
      b.appendChild(el("span", "aba-contagem", String(a.itens.length)));
      b.addEventListener("click", () => { estado.selecao.aba = a.id; renderEvidencia(); });
      abas.appendChild(b);
    });

    const atual = abasDef.find((a) => a.id === sel.aba) || abasDef[0];
    if (atual.id === "recuperadas") {
      const min = r.min_score_usado;
      corpo.appendChild(el("p", "evid-nota",
        `Os ${recuperadas.length} trechos mais próximos da pergunta, antes do filtro de relevância${min != null ? ` (mínimo ${min.toFixed(2)}, marca no medidor)` : ""}.`));
    }
    if (!atual.itens.length) {
      const msg = atual.id === "citadas"
        ? (r.recusado ? "Nenhum trecho foi citado porque não houve resposta." : "A resposta não citou trechos. Veja a aba Recuperadas para o que o modelo recebeu.")
        : "Nada foi recuperado para esta pergunta.";
      corpo.appendChild(el("p", "evid-vazio", msg));
      return;
    }

    let destaque = null;
    atual.itens.forEach((f) => {
      const t = el("article", "trecho");
      if (idsCitados.has(f.id)) t.classList.add("citado");
      if (atual.id === "recuperadas" && r.min_score_usado != null && f.score < r.min_score_usado) t.classList.add("descartado");
      t.dataset.id = f.id;

      const cab = el("div", "trecho-cabecalho");
      cab.appendChild(el("span", "trecho-num", f.id));
      cab.appendChild(el("span", "trecho-doc", f.documento));
      t.appendChild(cab);
      t.appendChild(el("p", "trecho-local", `página ${f.pagina} · ${f.secao}`));
      t.appendChild(medidor(f.score, r.min_score_usado));
      t.appendChild(el("p", "passagem", f.trecho));
      if (atual.id === "recuperadas") {
        const estadoTxt = idsCitados.has(f.id) ? "Citado na resposta"
          : (r.min_score_usado != null && f.score < r.min_score_usado ? "Abaixo da relevância mínima, não enviado ao modelo" : "Enviado ao modelo, não citado");
        t.appendChild(el("p", "trecho-estado", estadoTxt));
      }
      corpo.appendChild(t);
      if (idDestaque && f.id === idDestaque) destaque = t;
    });

    if (destaque) {
      destaque.classList.add("destacado");
      destaque.scrollIntoView({ block: "nearest" });
    } else {
      corpo.scrollTop = 0;
    }
  }

  /* ---------- envio ---------- */
  function montarCorpo(pergunta) {
    const a = estado.ajustes;
    const historico = estado.turnos
      .filter((t) => !t.erro && !t.carregando && t.respostas && t.respostas[0] && !t.respostas[0].erro)
      .slice(-MAX_HISTORICO)
      .map((t) => ({ pergunta: t.pergunta.slice(0, 1000), resposta: String(t.respostas[0].resposta || "").slice(0, 4000) }));

    const corpo = {
      pergunta, historico,
      k: a.k, min_score: a.min_score, temperature: a.temperature, top_p: a.top_p, max_tokens: a.max_tokens,
    };
    if (a.comparar) {
      corpo.variantes = [
        { provider: a.provider, model: a.model || null, prompt_version: a.prompt_version },
        { provider: a.provider_b, model: a.model_b || null, prompt_version: a.prompt_b },
      ];
    } else {
      corpo.provider = a.provider;
      corpo.model = a.model || null;
      corpo.prompt_version = a.prompt_version;
    }
    return corpo;
  }

  async function enviar(textoDireto) {
    if (estado.enviando) return;
    const campo = $("pergunta");
    const pergunta = (textoDireto != null ? textoDireto : campo.value).trim();
    if (!pergunta) return;

    if (estado.config && !estado.config.pronto) {
      await carregarConfig();
      if (!estado.config.pronto) { renderConversa(); return; }
    }

    const corpo = montarCorpo(pergunta);
    const turno = { pergunta, respostas: [], erro: null, carregando: true };
    estado.turnos.push(turno);
    estado.enviando = true;
    campo.value = "";
    ajustarAltura();
    $("btn-enviar").disabled = true;
    renderConversa();
    rolarAoFim();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(corpo),
      });
      let dados = null;
      try { dados = await res.json(); } catch (_) { /* corpo não-JSON */ }
      if (!res.ok) {
        const det = dados && (dados.erro || dados.detail);
        const msg = typeof det === "string" ? det : JSON.stringify(det || res.statusText);
        throw new Error(res.status === 503
          ? `A base de conhecimento ainda não está pronta. ${msg}`
          : `Não foi possível gerar a resposta. ${msg}`);
      }
      turno.respostas = dados.respostas;
      turno.carregando = false;
      renderConversa();
      const vi = 0, r = turno.respostas[0];
      if (r && !r.erro) {
        const aba = r.recusado ? "recuperadas" : (r.citou && (r.fontes || []).length ? "citadas" : "recuperadas");
        estado.selecao = { turno: estado.turnos.length - 1, variante: vi, aba };
        renderEvidencia();
      }
    } catch (e) {
      turno.carregando = false;
      turno.erro = e instanceof TypeError
        ? "Não consegui falar com o servidor. Confira se `python app/web_server.py` continua rodando."
        : e.message;
      renderConversa();
    } finally {
      estado.enviando = false;
      $("btn-enviar").disabled = false;
      rolarAoFim();
      campo.focus();
    }
  }

  function rolarAoFim() {
    const r = $("rolagem");
    r.scrollTop = r.scrollHeight;
  }

  function ajustarAltura() {
    const c = $("pergunta");
    c.style.height = "auto";
    c.style.height = Math.min(c.scrollHeight, 144) + "px";
  }

  /* ---------- ajustes ---------- */
  function preencher(select, valores, atual) {
    limpar(select);
    for (const v of valores) {
      const o = el("option", null, v.rotulo || v);
      o.value = v.id || v;
      select.appendChild(o);
    }
    select.value = atual;
  }

  function montarAjustes() {
    const cfg = estado.config, a = estado.ajustes;
    const prompts = cfg.prompts.map((p) => ({ id: p.id, rotulo: p.id }));
    preencher($("f-provider"), cfg.providers, a.provider);
    preencher($("f-provider-b"), cfg.providers, a.provider_b);
    preencher($("f-prompt"), prompts, a.prompt_version);
    preencher($("f-prompt-b"), prompts, a.prompt_b);
    $("f-model").value = a.model || "";
    $("f-model-b").value = a.model_b || "";
    $("f-k").value = a.k;
    $("f-min").value = a.min_score;
    $("f-temp").value = a.temperature;
    $("f-top").value = a.top_p;
    $("f-max").value = a.max_tokens;
    $("f-comparar").checked = a.comparar;
    atualizarAjustesDerivados();
  }

  function atualizarAjustesDerivados() {
    const a = estado.ajustes;
    $("o-min").textContent = Number(a.min_score).toFixed(2);
    $("o-temp").textContent = Number(a.temperature).toFixed(2);
    $("o-top").textContent = Number(a.top_p).toFixed(2);
    $("grupo-b").hidden = !a.comparar;
    const desc = estado.config.prompts.find((p) => p.id === a.prompt_version);
    $("f-prompt-desc").textContent = desc ? desc.descricao : "";
  }

  function lerCampos() {
    const a = estado.ajustes;
    a.provider = $("f-provider").value;
    a.model = $("f-model").value.trim();
    a.prompt_version = $("f-prompt").value;
    a.k = Math.max(1, Math.min(10, parseInt($("f-k").value, 10) || a.k));
    a.min_score = parseFloat($("f-min").value);
    a.temperature = parseFloat($("f-temp").value);
    a.top_p = parseFloat($("f-top").value);
    a.max_tokens = Math.max(64, Math.min(4096, parseInt($("f-max").value, 10) || a.max_tokens));
    a.comparar = $("f-comparar").checked;
    a.provider_b = $("f-provider-b").value;
    a.model_b = $("f-model-b").value.trim();
    a.prompt_b = $("f-prompt-b").value;
    gravarArmazenado(a);
    atualizarAjustesDerivados();
  }

  /* ---------- inicialização ---------- */
  async function carregarConfig() {
    try {
      const res = await fetch("/api/config");
      estado.config = await res.json();
    } catch (_) {
      estado.config = { pronto: false, erro: "Servidor não respondeu. Rode `python app/web_server.py`.", providers: [], prompts: [], padroes: null, base: null };
    }
    if (estado.config.padroes && !estado.ajustes) {
      const salvo = lerArmazenado();
      estado.ajustes = Object.assign(padroesAjustes(estado.config), salvo || {});
      if (!estado.config.providers.includes(estado.ajustes.provider)) estado.ajustes.provider = estado.config.padroes.provider;
      montarAjustes();
    }
    renderConversa();
    renderEvidencia();
  }

  function ligarEventos() {
    $("form").addEventListener("submit", (e) => { e.preventDefault(); enviar(); });
    $("pergunta").addEventListener("input", ajustarAltura);
    $("pergunta").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); enviar(); }
    });

    $("btn-limpar").addEventListener("click", () => {
      estado.turnos = []; estado.selecao = null;
      abrirFolha(false);
      renderConversa(); renderEvidencia();
      $("pergunta").focus();
    });

    const dlg = $("ajustes");
    $("btn-ajustes").addEventListener("click", () => {
      if (!estado.ajustes) return;
      montarAjustes();
      dlg.showModal();
    });
    dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
    ["f-provider", "f-model", "f-prompt", "f-k", "f-min", "f-temp", "f-top", "f-max", "f-comparar",
     "f-provider-b", "f-model-b", "f-prompt-b"].forEach((id) => {
      $(id).addEventListener("input", () => estado.ajustes && lerCampos());
      $(id).addEventListener("change", () => estado.ajustes && lerCampos());
    });
    $("btn-padroes").addEventListener("click", () => {
      estado.ajustes = padroesAjustes(estado.config);
      gravarArmazenado(estado.ajustes);
      montarAjustes();
    });

    $("evid-fechar").addEventListener("click", () => abrirFolha(false));
    $("cortina").addEventListener("click", () => abrirFolha(false));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && $("evidencia").classList.contains("aberta")) abrirFolha(false);
    });
  }

  ligarEventos();
  carregarConfig();
})();
