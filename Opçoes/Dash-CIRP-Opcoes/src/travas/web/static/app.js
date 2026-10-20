// Controlador da interface. Todos os cálculos vêm da API Python; aqui só exibição.
(() => {
  const $ = (id) => document.getElementById(id);
  const state = { defaults: null, analysis: null, detail: null, view: null, size: { mode: "qty" }, sort: null, tf: "d1", side: true, underlying: null, levels: [], tab: "analysis",
    // Cada aba tem o próprio ativo e as próprias linhas no gráfico; nada vaza de uma para outra.
    chart: { analysis: { underlying: null, levels: [] }, tracking: { underlying: null, levels: [] }, heatmap: { underlying: null, levels: [] }, protected: { underlying: null, levels: [] }, simulator: { underlying: null, levels: [] } } };

  const KIND_TEXT = {
    "alta|debito": "Trava de alta com débito: compra call de strike menor e vende call de strike maior. Paga débito; ganha se o ativo subir acima do breakeven.",
    "baixa|debito": "Trava de baixa com débito: compra put de strike maior e vende put de strike menor. Paga débito; ganha se o ativo cair abaixo do breakeven.",
    "alta|credito": "Trava de alta com crédito: vende put de strike maior e compra put de strike menor. Recebe crédito; ganha se o ativo ficar acima do breakeven.",
    "baixa|credito": "Trava de baixa com crédito: vende call de strike menor e compra call de strike maior. Recebe crédito; ganha se o ativo ficar abaixo do breakeven.",
  };
  const PREF_FIELDS = ["underlying", "quantity", "invest_amount", "dte_min", "dte_max", "strike_min", "strike_max", "max_width", "max_loss_total",
    "max_spread_pct_mid", "min_deals", "min_turnover_brl", "max_quote_age_seconds", "vol_override", "rate_annual", "costs_brl",
    "limit_aggressiveness", "min_reward_risk", "w_scenario", "w_reward_risk", "w_pop", "w_liquidity", "w_execution_cost"];

  async function api(path, opts) {
    const res = await fetch(path, opts);
    let body = null;
    try { body = await res.json(); } catch { /* resposta sem JSON */ }
    if (!res.ok) throw new Error((body && body.detail && (typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail))) || `HTTP ${res.status}`);
    return body;
  }
  const radio = (name) => document.querySelector(`input[name=${name}]:checked`).value;
  const num = (id) => { const v = $(id).value; return v === "" ? null : Number(v); };

  // ---------- conexão ----------
  async function pollStatus() {
    const box = $("conn"), text = $("conn-text");
    try {
      const s = await api("/api/status");
      renderMarket(s.market, s.off_hours_source, s.snapshot);
      if (s.broker && s.broker !== state.broker) {
        const changed = state.broker && state.broker !== s.broker;
        state.broker = s.broker;
        // Conta trocada no terminal: recarrega a lista (outra corretora, outras opções).
        if (changed) { state.underlyingsLoaded = false; state.underlying = null; }
      }
      box.className = "conn " + (s.phase === "conectado" && s.server_connected !== false ? "ok" : s.phase === "erro" ? "err" : "wait");
      if (s.phase === "conectado") {
        const t = s.terminal || {};
        text.textContent = s.server_connected === false
          ? "MT5 aberto, SEM conexão com a corretora"
          : `MT5 conectado · ${esc(s.broker || "")} (${t.server || ""})${s.is_session_today ? "" : " · hoje não é pregão"}`;
        if (!state.underlyingsLoaded) loadUnderlyings();
      } else if (s.phase === "erro") {
        text.textContent = `MT5 indisponível: ${s.error}`;
      } else {
        text.textContent = s.phase === "conectando" ? "Conectando ao MT5 (pode abrir o terminal)…" : "MT5 desconectado";
      }
    } catch (e) {
      box.className = "conn err";
      text.textContent = "Servidor local inacessível";
    }
  }

  // Mercado fechado: escolha da fonte (fechamento oficial da B3, capturas do pregão ou snapshot
  // gravado pelo coletor do servidor).
  function renderMarket(m, source, snap) {
    const el = $("market");
    if (!m) { el.hidden = true; return; }
    el.hidden = false;
    el.className = "market-pill " + (m.is_open ? "open" : "closed");
    state.market = m;
    const snapText = !snap ? "" : snap.available
      ? ` <span class="small" title="${esc(snap.note || "Snapshot mais recente do servidor")}">(${esc(snap.label)}${snap.status === "parcial" ? ", parcial" : ""}${snap.note ? ", offline" : ""})</span>`
      : ` <span class="small neg" title="${esc(snap.problem || "")}">(indisponível: usando capturas)</span>`;
    const key = `${m.is_open}|${m.label}|${source}|${snapText}`;
    if (el.dataset.key === key) return;  // não recria o seletor a cada consulta de status
    el.dataset.key = key;
    el.title = `Pregão regular configurado: ${m.session_open}–${m.session_close} (Brasília). Fora dele o app não usa o book do MT5, que fica vazio/distorcido.`;
    if (m.is_open) { el.textContent = `Mercado aberto (${m.session_open}–${m.session_close})`; return; }
    state.offHoursSource = source || "b3";
    el.innerHTML = `${esc(m.label)} · <label>usando <select id="off-hours-source" aria-label="Fonte das cotações com o mercado fechado">
      <option value="b3" title="Último negócio de cada série e fechamento do ativo no pregão (arquivo oficial da B3, como o ProfitChart). Sem bid/ask: preços indicativos">fechamento oficial (B3)</option>
      <option value="capturas" title="Últimas cotações com bid/ask capturadas pelo app durante o pregão (horários diversos)">capturas do pregão (bid/ask)</option>
      <option value="servidor" title="Snapshot mais recente gravado pelo servidor com MT5 (11:00 e 16:30 nos pregões): bid/ask de todas as séries no mesmo horário, 3 próximos vencimentos">snapshot do servidor (bid/ask)</option>
    </select></label>${snapText}`;
    $("off-hours-source").value = state.offHoursSource;
    $("off-hours-source").addEventListener("change", (e) => {
      state.offHoursSource = e.target.value;
      el.dataset.key = "";  // o status seguinte redesenha com o snapshot da nova fonte
      savePrefs(true);
    });
  }

  async function loadUnderlyings() {
    state.underlyingsLoaded = true;
    try {
      const list = await api("/api/underlyings");
      // Ordem por nº de séries (B3). Sem opções no MT5 da corretora: listado, mas sinalizado.
      $("underlyings").innerHTML = list.map((u) => `<option value="${esc(u.underlying)}">${esc(u.underlying)} · ${FMT.int(u.listed_series)} séries${u.category ? " · " + esc(u.category) : ""}${u.has_mt5_options ? "" : " · sem cotações de opções no MT5"}</option>`).join("");
      state.underlyingInfo = Object.fromEntries(list.map((u) => [u.underlying, u]));
      if ($("underlying").value) onUnderlying();
    } catch (e) {
      state.underlyingsLoaded = false;
    }
  }

  async function onUnderlying() {
    const u = $("underlying").value.trim().toUpperCase();
    const ctx = state.chart.analysis;
    if (!u || u === ctx.underlying) return;
    // Novo ativo na análise: as linhas da estrutura anterior não valem mais.
    state.chart.analysis = { underlying: u, levels: [] };
    applyChart();
    $("underlying-icon").innerHTML = tickerIcon(u, 26);
    $("spot-info").textContent = "consultando…";
    try {
      const q = await api(`/api/quote/${encodeURIComponent(u)}`);
      const origin = FMT.origin(q.source);
      const info = (state.underlyingInfo || {})[u];
      const noOpts = info && !info.has_mt5_options ? ` · <span class="neg">opções sem cotação no MT5 da ${esc(state.broker || "corretora")} (${FMT.int(info.listed_series)} séries na B3)</span>` : "";
      $("spot-info").innerHTML = `${tickerIcon(u, 14)}Spot ${FMT.price(q.price)}${origin} · ${FMT.datetime(q.quote_time)}${noOpts}`;
      state.spot = q.price;
    } catch (e) {
      $("spot-info").textContent = e.message;
    }
    savePrefs();
  }

  // O gráfico lateral é compartilhado, mas o conteúdo é por aba: `tab` diz a quem pertence o
  // ativo/linhas. Só a aba ativa aparece; a outra fica guardada até voltar a ela.
  function showUnderlying(u, tab = state.tab) {
    if (!u) return;
    state.chart[tab].underlying = u;
    if (tab === state.tab) applyChart();
  }

  function setLevels(levels, tab = state.tab) {
    state.chart[tab].levels = levels;
    if (tab === state.tab) applyChart();
  }

  function applyChart() {
    const ctx = state.chart[state.tab];
    // Sem ativo próprio (ex.: Acompanhamento sem estrutura selecionada), mantém o ativo exibido,
    // mas sem linhas de outra aba.
    const u = ctx.underlying || state.underlying;
    state.levels = ctx.levels;
    if (u && u !== state.underlying) {
      state.underlying = u;
      $("side-title").innerHTML = tickerIcon(u, 24) + esc(u);
      updateStar();
      Candles.setLevels([]); // não deixa linhas da outra aba à vista enquanto carrega
      loadCandles(); // aplica state.levels ao terminar
    } else if (!candlesLoading) {
      Candles.setLevels(state.levels);
    } // carregando candles: loadCandles aplica as linhas quando o ativo certo estiver na tela
    renderLevelsLegend();
  }

  // ---------- seguimento (estrela) ----------
  function updateStar() {
    const b = $("star-btn"), u = state.underlying, on = !!u && Watch.has(u);
    b.disabled = !u;
    b.textContent = on ? "★" : "☆";
    b.classList.toggle("on", on);
    b.setAttribute("aria-pressed", String(on));
    b.title = !u ? "Selecione um ativo" : on ? `Deixar de seguir ${u}` : `Seguir ${u} (lista na aba Heatmap)`;
  }

  async function onStar() {
    const u = state.underlying;
    if (!u) return;
    const b = $("star-btn");
    b.disabled = true;
    try {
      const price = state.lastClose && state.lastClose.ticker === u ? state.lastClose.price : null;
      await Watch.toggle(u, price);
    } catch (e) {
      $("candle-note").textContent = `Não foi possível atualizar o seguimento: ${e.message}`;
    } finally {
      updateStar();
    }
  }

  // ---------- maximizar gráficos ----------
  let maximized = null;
  function toggleMax(el, button, after) {
    const on = !el.classList.contains("maximized");
    if (maximized && maximized.el !== el) toggleMax(maximized.el, maximized.button, maximized.after);
    el.classList.toggle("maximized", on);
    document.body.classList.toggle("has-maximized", on);
    button.textContent = on ? "✕ Restaurar" : "⤢ Maximizar";
    button.setAttribute("aria-pressed", String(on));
    maximized = on ? { el, button, after } : null;
    setTimeout(after, 30);
  }

  // ---------- largura do gráfico (divisória arrastável) ----------
  const SIDE_DEFAULT = 560, SIDE_MIN = 320;
  function sideMax() { return Math.max(SIDE_MIN, Math.round(window.innerWidth * 0.75)); }
  function setSideWidth(px, save = true) {
    const w = Math.round(Math.min(Math.max(px, SIDE_MIN), sideMax()));
    state.sideWidth = w;
    document.documentElement.style.setProperty("--side-width", `${w}px`);
    $("splitter").setAttribute("aria-valuenow", String(w));
    Candles.resize();
    if (save) savePrefs();
    return w;
  }
  function setupSplitter() {
    const sp = $("splitter");
    let raf = 0;
    sp.addEventListener("pointerdown", (ev) => {
      ev.preventDefault();
      sp.setPointerCapture(ev.pointerId);
      sp.classList.add("dragging");
      document.body.classList.add("resizing");
    });
    sp.addEventListener("pointermove", (ev) => {
      if (!sp.hasPointerCapture(ev.pointerId)) return;
      const right = $("layout").getBoundingClientRect().right - 16; // padding do layout
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => setSideWidth(right - ev.clientX - 5, false));
    });
    const end = (ev) => {
      if (!sp.hasPointerCapture(ev.pointerId)) return;
      sp.releasePointerCapture(ev.pointerId);
      sp.classList.remove("dragging");
      document.body.classList.remove("resizing");
      savePrefs();
      if (state.detail) drawPayoff();
      window.dispatchEvent(new Event("resize")); // redesenha o payoff do acompanhamento
    };
    sp.addEventListener("pointerup", end);
    sp.addEventListener("pointercancel", end);
    sp.addEventListener("dblclick", () => { setSideWidth(SIDE_DEFAULT); window.dispatchEvent(new Event("resize")); });
    sp.addEventListener("keydown", (ev) => {
      const step = ev.shiftKey ? 120 : 40;
      if (ev.key === "ArrowLeft") setSideWidth((state.sideWidth || SIDE_DEFAULT) + step);
      else if (ev.key === "ArrowRight") setSideWidth((state.sideWidth || SIDE_DEFAULT) - step);
      else return;
      ev.preventDefault();
      window.dispatchEvent(new Event("resize"));
    });
    sp.setAttribute("aria-valuemin", String(SIDE_MIN));
  }

  // ---------- abas ----------
  function switchTab(name) {
    state.tab = name;
    document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
    $("tab-analysis").hidden = name !== "analysis";
    $("tab-tracking").hidden = name !== "tracking";
    $("tab-heatmap").hidden = name !== "heatmap";
    $("tab-protected").hidden = name !== "protected";
    $("tab-simulator").hidden = name !== "simulator";
    if (name === "tracking") Tracking.activate();
    if (name === "heatmap") Heatmap.activate();
    if (name === "protected") Protected.activate();
    if (name === "simulator") Simulator.activate();
    applyChart();
    savePrefs();
  }

  // ---------- candles ----------
  let candlesRequest = 0;
  let candlesLoading = false;
  async function loadCandles() {
    const u = state.underlying;
    if (!u || !state.side) return;
    const token = ++candlesRequest;
    candlesLoading = true;
    $("candle-note").textContent = "Carregando candles…";
    const tfName = { mn1: "mensal", w1: "semanal", d1: "diário", h4: "240 min", h1: "60 min" }[state.tf] || state.tf;
    Busy.show($("kchart-host"), `Carregando ${u} (${tfName})…`);
    try {
      const data = await api(`/api/candles/${encodeURIComponent(u)}?tf=${state.tf}`);
      // Resposta atrasada de um pedido anterior (troca rápida de aba/ativo): descarta.
      if (token !== candlesRequest) return;
      candlesLoading = false;
      Candles.setEmaPeriods(data.meta.ema_fast, data.meta.ema_slow);
      $("ema-fast-label").textContent = `EMA ${data.meta.ema_fast}`;
      $("ema-slow-label").textContent = `EMA ${data.meta.ema_slow}`;
      Candles.setData($("kchart"), u, state.tf, data.bars);
      const last = data.bars[data.bars.length - 1];
      state.lastClose = { ticker: u, price: last ? last.close : null };
      Candles.setLevels(state.levels);
      const m = data.meta;
      $("bar-info").textContent = `Última barra: ${FMT.datetime(m.last_bar_time)}${m.last_bar_forming ? " (em formação)" : " (fechada)"}`;
      const short = m.requested && m.bars < m.requested ? ` (pedidas ${m.requested}: o MT5 só tem esse histórico)` : "";
      $("candle-note").textContent = `${m.bars} barras do MT5${short}, todas visíveis ao carregar (roda do mouse: zoom; ⇔ Tudo: volta a mostrar todas). ${m.ema_method}. Breakevens se referem ao vencimento, salvo indicação.` +
        (state.tf === "h4" ? " No 240 min, as barras seguem o relógio do servidor (08h, 12h, 16h): a primeira do dia cobre só parte do pregão." : "");
    } catch (e) {
      if (token !== candlesRequest) return;
      candlesLoading = false;
      $("candle-note").textContent = `Candles indisponíveis: ${e.message}`;
    } finally {
      Busy.hide($("kchart-host"));
    }
  }

  function renderLevelsLegend() {
    $("levels").innerHTML = state.levels.filter((l) => FMT.ok(l.value)).map((l) =>
      `<span><i class="${l.dashed ? "dashed" : ""}" style="border-color:${l.color}"></i>${esc(l.label)}</span><span>${FMT.price(l.value)}</span>`).join("");
  }

  // ---------- formulário ----------
  function updateKindText() {
    $("kind-desc").textContent = KIND_TEXT[`${radio("direction")}|${radio("flow")}`];
    const usesPuts = (radio("direction") === "alta") !== (radio("flow") === "debito");
    $("style-hint").textContent = usesPuts ? "esta estrutura usa puts (na XP todas são europeias)" : "";
    // Filtro Rafael Nobre só existe para travas de débito.
    const debit = radio("flow") === "debito";
    $("nobre-box").classList.toggle("disabled", !debit);
    $("nobre_filter").disabled = !debit;
    $("nobre_target_required").disabled = !debit || !$("nobre_filter").checked;
    $("nobre_fraction").disabled = !debit || !$("nobre_filter").checked;
    $("nobre_prefer_close").disabled = !debit || !$("nobre_filter").checked;
    $("stop-box").classList.toggle("disabled", debit);
    $("credit_stop").disabled = debit;
    $("stop-hint").textContent = debit ? "disponível só para travas de crédito" : "";
    $("nobre-hint").textContent = !debit ? "disponível só para travas de débito"
      : $("nobre_filter").checked && num("target_price") === null && num("target_pct") === null
        ? "informe o preço-alvo (ou a variação) para aplicar o critério do alvo" : "";
  }

  function payload() {
    const pctOrNull = (id) => { const v = num(id); return v === null ? null : v / 100; };
    return {
      underlying: $("underlying").value.trim().toUpperCase(),
      direction: radio("direction"),
      flow: radio("flow"),
      target_price: num("target_price"),
      target_pct: num("target_pct"),
      horizon_date: $("horizon_date").value || null,
      conservative_price: num("conservative_price"),
      optimistic_price: num("optimistic_price"),
      dte_min: num("dte_min"),
      dte_max: num("dte_max"),
      strike_min: num("strike_min"),
      strike_max: num("strike_max"),
      max_width: num("max_width"),
      max_loss_total: num("max_loss_total"),
      quantity: state.size.mode === "qty" ? num("quantity") : null,
      rate_annual: pctOrNull("rate_annual"),
      vol_override: pctOrNull("vol_override"),
      costs_brl: num("costs_brl") || 0,
      limit_aggressiveness: pctOrNull("limit_aggressiveness"),
      min_reward_risk: num("min_reward_risk"),
      include_illiquid: $("include_illiquid").checked,
      nobre_filter: radio("flow") === "debito" && $("nobre_filter").checked,
      nobre_target_required: $("nobre_target_required").checked,
      nobre_max_cost_fraction: Number($("nobre_fraction").value),
      nobre_prefer_close: $("nobre_prefer_close").checked,
      european_short: $("european_short").checked,
      credit_stop: radio("flow") === "credito" && $("credit_stop").checked,
      refresh: $("refresh").checked,
      liquidity: {
        max_spread_pct_mid: pctOrNull("max_spread_pct_mid"),
        min_deals: num("min_deals"),
        min_turnover_brl: num("min_turnover_brl"),
        max_quote_age_seconds: num("max_quote_age_seconds"),
      },
      weights: {
        scenario: num("w_scenario") ?? 0, reward_risk: num("w_reward_risk") ?? 0, pop: num("w_pop") ?? 0,
        liquidity: num("w_liquidity") ?? 0, execution_cost: num("w_execution_cost") ?? 0,
      },
    };
  }

  async function onSubmit(ev) {
    ev.preventDefault();
    const body = payload();
    if (!body.underlying) return;
    const btn = $("btn-analyze"), msg = $("form-msg");
    btn.disabled = true;
    msg.className = "msg";
    msg.textContent = "Coletando a cadeia no MT5 e calculando… (a primeira coleta pode levar até ~1 min)";
    // Carregando sobre os resultados (ou sobre o formulário, na primeira análise).
    const host = $("results-card").hidden ? $("f-title").closest(".card") : $("results-card");
    Busy.show(host, "Coletando a cadeia no MT5 e calculando…");
    try {
      const r = await api("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      state.analysis = r;
      state.sort = null;
      msg.textContent = "";
      $("refresh").checked = false;
      renderResults();
      savePrefs();
    } catch (e) {
      msg.className = "msg err";
      msg.textContent = `Erro: ${e.message}`;
    } finally {
      Busy.hide(host);
      btn.disabled = false;
    }
  }

  // ---------- quantidade x valor a investir ----------
  // Tudo por unidade vem da análise; totais são refeitos aqui para a quantidade escolhida, sem
  // nova coleta nem nova análise. P&L é linear na quantidade, exceto os custos fixos (R$):
  // total(q) = (total(base) + custos) × q ÷ base − custos.
  const costsBrl = () => (state.analysis ? state.analysis.assumptions.costs_brl : num("costs_brl") || 0);
  const lot = () => (state.defaults && state.defaults.analysis.lot_size) || 100;
  // Capital por opção: débito pago (débito) ou garantia estimada (crédito).
  const capitalPerOption = (r) => (r.margin && r.margin.available && r.quantity ? r.margin.capital_estimated / r.quantity : null);

  function qtyFor(r) {
    if (state.size.mode === "amount") {
      const amount = num("invest_amount");
      const cpo = capitalPerOption(r);
      if (amount === null || !(cpo > 0)) return null;
      return Math.max(0, Math.floor((amount - costsBrl()) / cpo / lot()) * lot());
    }
    const q = num("quantity");
    return q !== null && q > 0 ? Math.floor(q) : null;
  }

  function scaler(r) {
    const q = qtyFor(r) ?? r.quantity;
    const f = r.quantity ? q / r.quantity : 1;
    const c = costsBrl();
    const s = String(r.kind || "").startsWith("alta") ? 1 : -1; // inclinação do payoff entre os strikes
    const u = r.units || r.quantity;
    return {
      q, f, c,
      pnl: (v) => (FMT.ok(v) ? (v + c) * f - c : v),
      loss: (v) => (FMT.ok(v) ? (v - c) * f + c : v),
      // Breakeven com custos fixos se desloca c × (1/u − 1/(u·f)) por unidade.
      be: (list) => (list || []).map((x) => (c && f > 0 ? x - s * c * (1 / u - 1 / (u * f)) : x)),
      lin: (v) => (FMT.ok(v) ? v * f : v),
    };
  }

  function scaleMargin(m, f) {
    if (!m || !m.available) return m;
    const out = { ...m };
    for (const k of ["estimated", "conservative", "obligation", "credit", "debit", "capital_estimated", "capital_conservative"]) {
      if (FMT.ok(m[k])) out[k] = m[k] * f;
    }
    return out;
  }

  function scaleRow(r) {
    if (!FMT.ok(r.max_loss)) return r;
    const z = scaler(r);
    const maxP = z.pnl(r.max_profit), maxL = z.loss(r.max_loss);
    const budget = num("max_loss_total");
    return {
      ...r,
      quantity: z.q,
      units: (r.units || r.quantity) * z.f,
      max_profit: maxP,
      max_loss: maxL,
      reward_risk: maxL > 0 ? maxP / maxL : null,
      risk_reward: maxP > 0 ? maxL / maxP : null,
      scenario_pnl: z.pnl(r.scenario_pnl),
      net_premium_total: z.lin(r.net_premium_total),
      entry_total: z.lin(r.entry_total),
      breakevens: z.be(r.breakevens),
      margin: scaleMargin(r.margin, z.f),
      credit_stop: r.credit_stop ? { ...r.credit_stop, expected_pnl_total: z.lin(r.credit_stop.expected_pnl_total), stop_loss_total: z.lin(r.credit_stop.stop_loss_total) } : r.credit_stop,
      _over_budget: budget !== null && z.q > 0 && maxL > budget + 1e-9,
      _scaled: z.f !== 1,
    };
  }

  function zeroCrossings(xs, ys) {
    const out = [];
    for (let i = 0; i < xs.length - 1; i++) {
      const a = ys[i], b = ys[i + 1];
      if (a === 0) out.push(xs[i]);
      else if (a * b < 0) out.push(xs[i] + (xs[i + 1] - xs[i]) * (-a / (b - a)));
    }
    return out;
  }

  // Detalhe na quantidade escolhida (curvas, cenários, gregas, preço-limite, garantia).
  function scaleDetail(d) {
    const row = scaleRow(d);
    const z = scaler(d);
    const sim = d.simulation;
    const g = d.greeks;
    const impacts = {};
    for (const [k, imp] of Object.entries((d.limit && d.limit.impacts) || {})) {
      if (!imp) { impacts[k] = imp; continue; }
      const mp = z.pnl(imp.max_profit), ml = z.loss(imp.max_loss);
      impacts[k] = { ...imp, max_profit: mp, max_loss: ml, breakevens: z.be(imp.breakevens), reward_risk: ml > 0 ? mp / ml : null };
    }
    const expiry = (sim.expiry_pnl || []).map(z.pnl);
    return {
      ...row,
      scenarios: (d.scenarios || []).map((s) => ({ ...s, pnl: z.pnl(s.pnl) })),
      greeks: g ? Object.fromEntries(Object.entries(g).map(([k, v]) => [k, z.lin(v)])) : g,
      limit: d.limit ? { ...d.limit, impacts } : d.limit,
      simulation: {
        ...sim,
        expiry_pnl: expiry,
        expiry_breakevens: z.be(sim.expiry_breakevens),
        entry_cash: z.lin(sim.entry_cash),
        exit_spread_cost: z.lin(sim.exit_spread_cost),
        costs: z.c,
        dates: (sim.dates || []).map((day) => { const pnl = day.pnl.map(z.pnl); return { ...day, pnl, breakevens: zeroCrossings(sim.spots, pnl) }; }),
      },
    };
  }

  // Estrutura de referência para converter quantidade ↔ valor nos campos do formulário.
  function refStructure() {
    if (state.detail && FMT.ok(state.detail.max_loss)) return { r: state.detail, label: "estrutura aberta" };
    const first = state.analysis && state.analysis.results.find((r) => capitalPerOption(r) > 0);
    return first ? { r: first, label: "1ª do ranking" } : null;
  }

  function syncSizeFields() {
    const ref = refStructure();
    const hint = [];
    if (ref) {
      const cpo = capitalPerOption(ref.r);
      if (state.size.mode === "qty") {
        const q = num("quantity");
        $("invest_amount").value = q && cpo > 0 ? +(q * cpo + costsBrl()).toFixed(2) : "";
      } else {
        $("quantity").value = qtyFor(ref.r) ?? "";
      }
      if (cpo > 0) hint.push(`Conversão pela ${ref.label}: capital de ${FMT.price(cpo)} por opção (débito pago ou garantia estimada)${costsBrl() ? ` + custos de ${FMT.brl(costsBrl())}` : ""}.`);
    }
    if (state.size.mode === "amount") hint.push(`Valor a investir: cada trava usa a maior quantidade múltipla de ${lot()} cujo capital cabe no valor.`);
    else if (num("quantity") && num("quantity") % lot()) hint.push(`Atenção: quantidade fora do lote de ${lot()}.`);
    if (state.analysis) hint.push("Mudar quantidade ou valor recalcula os totais na hora, sem nova coleta.");
    $("size-hint").textContent = hint.join(" ");
  }

  // Quantidade/valor mudou: refaz só a exibição (sem nova coleta nem nova análise).
  function onSizeInput(mode) {
    state.size.mode = mode;
    syncSizeFields();
    if (state.analysis) { renderRankingNote(); renderTable(); }
    if (state.detail) renderSized();
    savePrefs();
  }

  // ---------- ranking ----------
  const COLS = [
    { key: "rank", label: "#", val: (r) => r.rank, fmt: (r) => r.rank },
    { key: "score", label: "Score", val: (r) => r.score, fmt: (r) => `${FMT.num(r.score, 0)}${r.score_capped ? "*" : ""}` },
    { key: "expiration", label: "Vencimento", l: true, val: (r) => r.expiration, fmt: (r) => `${FMT.date(r.expiration)} <span class="muted">(${r.dte_business_days} du)</span>` },
    { key: "long", label: "Compra", l: true, val: (r) => r.legs[0].strike, fmt: (r) => `${FMT.price(r.legs[0].strike)} <span class="muted">${esc(r.legs[0].symbol)}</span>${styleTag(r.legs[0])}` },
    { key: "short", label: "Venda", l: true, val: (r) => r.legs[1].strike, fmt: (r) => `${FMT.price(r.legs[1].strike)} <span class="muted">${esc(r.legs[1].symbol)}</span>${styleTag(r.legs[1])}` },
    { key: "size", label: "Qtd · capital", tip: "Opções por perna e capital comprometido (débito pago ou garantia estimada), para a quantidade ou o valor escolhido", val: (r) => (r.margin && r.margin.available ? r.margin.capital_estimated : null), fmt: (r) => `${FMT.int(r.quantity)} <span class="muted">· ${r.margin && r.margin.available ? FMT.brl(r.margin.capital_estimated) : "—"}</span>` },
    { key: "width", label: "Largura", tip: "Distância entre os strikes (R$)", val: (r) => r.width, fmt: (r) => FMT.price(r.width) },
    { key: "entry", label: "Entrada natural", tip: "Por ação: compra no ask, venda no bid", val: (r) => r.entry_natural, fmt: (r) => FMT.price(r.entry_natural) },
    { key: "mid", label: "Mid", val: (r) => r.entry_mid, fmt: (r) => FMT.price(r.entry_mid) },
    { key: "max_loss", label: "Perda máx.", val: (r) => r.max_loss, fmt: (r) => FMT.brl(r.max_loss) },
    { key: "max_profit", label: "Lucro máx.", val: (r) => r.max_profit, fmt: (r) => FMT.brl(r.max_profit) },
    { key: "be", label: "Breakeven", tip: "Breakeven no vencimento", val: (r) => r.breakevens[0], fmt: (r) => r.breakevens.map(FMT.price).join(" / ") },
    { key: "margin", label: "Garantia est.", tip: "Garantia estimada pelo risco no vencimento (crédito: largura − crédito; débito: em geral zero). O valor real é da B3 (CORE)/corretora.", val: (r) => (r.margin && r.margin.available ? r.margin.estimated : null), fmt: (r) => (r.margin && r.margin.available ? FMT.brl(r.margin.estimated) : "—") },
    { key: "rr", label: "Lucro/Perda", tip: "Lucro máximo ÷ perda máxima", val: (r) => r.reward_risk, fmt: (r) => FMT.ratio(r.reward_risk) },
    { key: "pop", label: "POP", tip: "Probabilidade de lucro no vencimento (modelo lognormal). Ver metodologia no detalhe.", val: (r) => r.pop, fmt: (r) => FMT.pct(r.pop, 0) },
    { key: "scenario", label: "No alvo", tip: "Resultado estimado no preço-alvo (no vencimento ou, com horizonte, pelo modelo)", val: (r) => r.scenario_pnl, fmt: (r) => `<span class="${(r.scenario_pnl ?? 0) >= 0 ? "pos" : "neg"}">${FMT.signedBrl(r.scenario_pnl)}</span>` },
    { key: "nobre", label: "R. Nobre", tip: "Filtro Rafael Nobre: custo ≤ 1/4 (ou 1/3) da largura e perna vendida antes do alvo", show: () => state.analysis && state.analysis.nobre && state.analysis.nobre.active, val: (r) => (r.nobre ? (r.nobre.target_ok === false ? 0 : 1) * 10 - r.nobre.cost_ratio : null), fmt: (r) => nobreBadge(r.nobre) },
    { key: "stop_px", label: "Stop (ativo)", tip: "Preço do ativo que aciona o stop 1:1 (o mais próximo do spot até o vencimento) e distância do spot", show: stopActive, val: (r) => (r.credit_stop ? Math.abs(r.credit_stop.stop_distance_pct) : null), fmt: (r) => (r.credit_stop ? `${FMT.price(r.credit_stop.stop_price_nearest)} <span class="muted">(${FMT.pct(r.credit_stop.stop_distance_pct, 1)})</span>` : "—") },
    { key: "stop_prob", label: "P(stop)", tip: "Probabilidade de acionar o stop até o vencimento (Monte Carlo, monitoramento contínuo)", show: stopActive, val: (r) => (r.credit_stop ? r.credit_stop.prob_stop : null), fmt: (r) => (r.credit_stop ? FMT.pct(r.credit_stop.prob_stop, 0) : "—") },
    { key: "stop_ev", label: "Esperado c/ stop", tip: "Resultado esperado com o manejo (stop 1:1), na quantidade escolhida. Modelo; não é garantia", show: stopActive, val: (r) => (r.credit_stop ? r.credit_stop.expected_pnl_total : null), fmt: (r) => (r.credit_stop ? `<span class="${r.credit_stop.expected_pnl_total >= 0 ? "pos" : "neg"}">${FMT.signedBrl(r.credit_stop.expected_pnl_total)}</span>` : "—") },
    { key: "liq", label: "Liquidez", val: (r) => r.liquidity_score, fmt: (r) => liqBadge(r) },
    { key: "alerts", label: "Alertas", l: true, val: (r) => (r.early_exercise || "").startsWith("RISCO") ? 1 : 0, fmt: (r) => alertsCell(r) },
  ];

  function stopActive() { return !!(state.analysis && state.analysis.credit_stop && state.analysis.credit_stop.active); }

  function styleTag(leg) {
    const eur = leg.exercise_style === "european";
    return ` <span class="style-tag ${eur ? "eur" : "amer"}" title="${eur ? "Europeia: só exerce no vencimento" : "Americana: pode ser exercida a qualquer momento"}">${eur ? "E" : "A"}</span>`;
  }

  function nobreBadge(n) {
    if (!n) return "—";
    const cost = `custo ${FMT.pct(n.cost_ratio, 0)}`;
    const target = n.target_ok === null ? "sem alvo" : n.target_ok ? "antes do alvo" : "além do alvo";
    const cls = n.cost_ok && n.target_ok !== false ? "ok" : n.cost_ok ? "mid" : "bad";
    return `<span class="badge ${cls}" title="Custo = ${FMT.pct(n.cost_ratio, 1)} da largura (máx. ${FMT.pct(n.max_cost_fraction, 1)}) · vendida ${target}">${cost} · ${target}</span>`;
  }

  function liqBadge(r) {
    if (!r.liquidity_ok) return `<span class="badge bad" title="${esc(r.data_flags.join(", "))}">reprovada</span>`;
    const s = r.liquidity_score;
    return s >= 0.6 ? `<span class="badge ok">boa ${FMT.num(s * 100, 0)}</span>` : `<span class="badge mid">média ${FMT.num(s * 100, 0)}</span>`;
  }
  function alertsCell(r) {
    const out = [];
    if (r.early_exercise && r.early_exercise.startsWith("RISCO")) out.push(`<span class="badge bad" title="${esc(r.early_exercise)}">exercício antecipado</span>`);
    if (r.data_flags.length) out.push(`<span class="badge mid" title="${esc(r.data_flags.join(", "))}">dados</span>`);
    if (r._over_budget) out.push(`<span class="badge bad" title="Perda máxima acima do orçamento informado nesta quantidade">acima do orçamento</span>`);
    if (r.quantity === 0) out.push(`<span class="badge bad" title="O valor a investir não cobre um lote desta trava">valor insuficiente</span>`);
    return out.join(" ");
  }

  function renderResults() {
    const a = state.analysis;
    $("results-card").hidden = false;
    const c = a.collection;
    $("results-meta").innerHTML = `${tickerIcon(a.underlying, 18)}${esc(a.underlying)} · spot ${FMT.price(a.spot)} · ${esc(a.kind_label)} · coleta ${FMT.datetime(c.collected_at)}${c.from_cache ? " (cache)" : ` em ${FMT.num(c.duration_seconds, 0)} s`} · ${c.series} séries (${c.series_with_book} com book)`;
    const warn = $("data-warning");
    warn.hidden = !c.realtime_warning;
    warn.textContent = c.realtime_warning ? `Atenção: ${c.realtime_warning}.` : "";
    const nobreNote = a.nobre ? `<div class="small"><b>Filtro Rafael Nobre:</b> ${esc(a.nobre.note)}</div>` +
      (a.nobre.warning ? `<div class="warn">${esc(a.nobre.warning)}</div>` : "") : "";
    const stopNote = a.credit_stop ? `<div class="small"><b>Stop 1:1 (Credit Spread Investing):</b> ${esc(a.credit_stop.note)}</div>` : "";
    const styleNote = a.assumptions.exercise_style_filter && a.assumptions.exercise_style_filter.length
      ? `<div class="small"><b>Estilo de exercício:</b> ${esc(a.assumptions.exercise_style_filter.join(" e "))}</div>` : "";
    const disc = Object.entries(a.discarded).map(([k, v]) => `${esc(k)}: ${v}`).join(" · ");
    $("discarded").innerHTML = nobreNote + stopNote + styleNote + `${a.total_ranked} travas ranqueadas de ${a.candidates_evaluated} avaliadas` + (disc ? ` · descartadas — ${disc}` : "") +
      (a.atm_iv.length ? ` · IV ATM: ${a.atm_iv.map((x) => `${FMT.date(x.expiration)} ${FMT.pct(x.atm_iv)}`).join(", ")}` : " · sem IV ATM confiável (POP indisponível)");
    renderRankingNote();
    syncSizeFields();
    renderTable();
    if (!a.results.length) {
      const why = a.empty_reason ? `Nenhuma trava montada: ${esc(a.empty_reason)}.` : "Nenhuma trava passou nos filtros. Afrouxe liquidez, prazo ou largura, ou inclua as ilíquidas.";
      $("ranking").querySelector("tbody").innerHTML = `<tr><td class="l" colspan="${COLS.length}">${why}</td></tr>`;
    }
  }

  function renderRankingNote() {
    const a = state.analysis;
    const base = a.results[0] ? a.results[0].quantity : null;
    const qty = state.size.mode === "amount" ? `a quantidade que cabe em ${FMT.brl(num("invest_amount"))} (por trava)` : `${FMT.int(qtyFor({ quantity: base }) ?? base)} opções por perna`;
    const costs = costsBrl() ? ` O score foi calculado com ${FMT.int(base)} opções; com custos fixos, mudar a quantidade altera os totais exibidos, não a ordem do score.` : "";
    $("ranking-note").textContent = `${a.assumptions.ranking_note} * = score limitado por liquidez/cotação. Valores totais para ${qty}.${costs} ${a.assumptions.entry_basis}.`;
  }

  function renderTable() {
    const a = state.analysis;
    const rows = a.results.map(scaleRow);
    if (state.sort) {
      const col = COLS.find((c) => c.key === state.sort.key);
      rows.sort((x, y) => {
        const vx = col.val(x), vy = col.val(y);
        if (vx === null || vx === undefined) return 1;
        if (vy === null || vy === undefined) return -1;
        return (vx > vy ? 1 : vx < vy ? -1 : 0) * state.sort.dir;
      });
    }
    const cols = COLS.filter((c) => !c.show || c.show());
    const thead = $("ranking").querySelector("thead");
    thead.innerHTML = "<tr>" + cols.map((c) => {
      const cls = ["sortable", c.l ? "l" : "", state.sort && state.sort.key === c.key ? (state.sort.dir > 0 ? "sorted-asc" : "sorted-desc") : ""].join(" ");
      return `<th class="${cls}" data-key="${c.key}" ${c.tip ? `title="${esc(c.tip)}"` : ""}>${c.label}</th>`;
    }).join("") + "</tr>";
    $("ranking").querySelector("tbody").innerHTML = rows.map((r) =>
      `<tr data-id="${esc(r.id)}" class="${r.liquidity_ok ? "" : "illiquid"} ${state.detail && state.detail.id === r.id ? "selected" : ""}">` +
      cols.map((c) => `<td class="${c.l ? "l" : ""}">${c.fmt(r)}</td>`).join("") + "</tr>").join("");
  }

  function onHeaderClick(ev) {
    const th = ev.target.closest("th[data-key]");
    if (!th) return;
    const key = th.dataset.key;
    const ascDefault = ["rank", "expiration", "max_loss", "entry", "mid"].includes(key) ? 1 : -1;
    state.sort = state.sort && state.sort.key === key ? { key, dir: -state.sort.dir } : { key, dir: ascDefault };
    renderTable();
  }

  async function onRowClick(ev) {
    const tr = ev.target.closest("tr[data-id]");
    if (!tr) return;
    try {
      const host = $("detail-card").hidden ? $("results-card") : $("detail-card");
      Busy.show(host, "Abrindo a estrutura…");
      let d;
      try {
        d = await api(`/api/detail/${state.analysis.analysis_id}/${encodeURIComponent(tr.dataset.id)}`);
      } finally {
        Busy.hide(host);
      }
      state.detail = d;
      renderTable();
      renderDetail();
      $("detail-card").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
      $("form-msg").className = "msg err";
      $("form-msg").textContent = `Erro ao abrir a estrutura: ${e.message}`;
    }
  }

  // Garantia estimada (bloco usado na Análise e no Simulador).
  function marginHtml(m, maxProfit) {
    if (!m) return '<span class="muted">—</span>';
    if (!m.available) return `<div class="limit-box margin-box"><b>Garantia: não estimável.</b><br><span class="small">${esc(m.reason || "")}</span><div class="small muted">${esc(m.method)}</div></div>`;
    const ret = (cap) => (FMT.ok(maxProfit) && cap > 0 ? FMT.pct(maxProfit / cap, 1) : "—");
    const lines = [
      ["Garantia estimada", `<b>${FMT.brl(m.estimated)}</b>`],
      ["Garantia conservadora", `${FMT.brl(m.conservative)} <span class="muted">(sem usar o crédito)</span>`],
      [m.debit > 0 ? "Débito pago na entrada" : "Crédito recebido na entrada", FMT.brl(m.debit > 0 ? m.debit : m.credit)],
      ["Capital comprometido", `${FMT.brl(m.capital_estimated)}${m.capital_conservative !== m.capital_estimated ? ` <span class="muted">a ${FMT.brl(m.capital_conservative)}</span>` : ""}`],
      ["Lucro máx. ÷ capital", `${ret(m.capital_estimated)}${m.capital_conservative !== m.capital_estimated ? ` <span class="muted">a ${ret(m.capital_conservative)}</span>` : ""}`],
    ];
    return `<div class="limit-box margin-box"><div class="metrics one">${lines.map(([k, v]) => `<div><span>${k}</span><span>${v}</span></div>`).join("")}</div>
      ${m.notes.map((n) => `<div class="small warn-text">${esc(n)}</div>`).join("")}
      <div class="small muted">${esc(m.method)}</div></div>`;
  }

  // ---------- detalhe ----------
  function renderDetail() {
    const d = state.detail;
    $("detail-card").hidden = false;
    const [L, S] = d.legs;
    $("detail-title").innerHTML = `${tickerIcon(state.analysis.underlying, 24)}${esc(d.kind_label)}: ${esc(L.symbol)} / ${esc(S.symbol)}`;

    const alerts = [];
    if (d.collection.realtime_warning) alerts.push(`<div class="warn">${esc(d.collection.realtime_warning)}</div>`);
    if (!d.liquidity_ok) alerts.push(`<div class="warn">Liquidez/cotação reprovada: ${esc(d.data_flags.join(", "))}. Preços podem não ser executáveis.</div>`);
    if (d.early_exercise) alerts.push(`<div class="warn ${d.early_exercise.startsWith("RISCO") ? "alert-risk" : ""}">${esc(d.early_exercise)}</div>`);
    for (const w of d.warnings || []) alerts.push(`<div class="warn">${esc(w)}</div>`);
    $("detail-alerts").innerHTML = alerts.join("");

    renderLegs(d);
    renderScore(d);
    syncSizeFields();
    state.view = scaleDetail(d);
    renderAssumptions(state.view);
    setupSlider(state.view); // desenha via renderSized
  }

  // Partes do detalhe que dependem da quantidade (refeitas ao mudar quantidade ou valor).
  function renderSized() {
    const d = (state.view = scaleDetail(state.detail));
    const insufficient = d.quantity === 0 ? " · valor insuficiente para um lote" : "";
    $("detail-sub").textContent = `Vencimento ${FMT.date(d.expiration)} · ${d.dte_business_days} dias úteis (${d.dte_calendar_days} corridos) · largura ${FMT.price(d.width)} · ${FMT.int(d.quantity)} opções por perna${d.margin && d.margin.available ? ` · capital ${FMT.brl(d.margin.capital_estimated)}` : ""}${insufficient}`;
    renderLimit(d);
    $("margin-box").innerHTML = marginHtml(d.margin, d.max_profit);
    renderMetrics(d);
    drawPayoff();
  }

  function renderLimit(d) {
    const l = d.limit;
    const word = l.flow === "debito" ? "Débito" : "Crédito";
    if (l.suggested === null) {
      $("limit-box").innerHTML = `<div class="limit-box"><b>Preço-limite: não estimável.</b><br>${esc(l.reason_unavailable || "")}</div>`;
      return;
    }
    const imp = l.impacts;
    const line = (name, label) => imp[name] ? `<tr><td class="l">${label}</td><td>${FMT.price(imp[name].price)}</td><td>${FMT.brl(imp[name].max_profit)}</td><td>${FMT.brl(imp[name].max_loss)}</td><td>${imp[name].breakevens.map(FMT.price).join(" / ")}</td><td>${FMT.ratio(imp[name].reward_risk)}</td></tr>` : "";
    $("limit-box").innerHTML = `<div class="limit-box">
      <div class="muted small">${word} líquido por ação a digitar no ProfitChart (ordem manual)</div>
      <div class="limit-main">${FMT.price(l.suggested)}</div>
      <div class="small">Faixa indicativa: ${FMT.price(l.range_low)} – ${FMT.price(l.range_high)} (mid ↔ natural) · teórico ${FMT.price(l.theoretical)}</div>
      <div class="small muted">Dados de ${FMT.datetime(d.collection.collected_at)}. ${l.notes.map(esc).join(". ")}.</div>
      </div>
      <div class="table-wrap"><table class="legs small"><thead><tr><th class="l">Preço usado</th><th>${word}</th><th>Lucro máx.</th><th>Perda máx.</th><th>Breakeven</th><th>L/P</th></tr></thead>
      <tbody>${line("sugerido", "Sugerido")}${line("mid", "Mid")}${line("natural", "Natural")}${line("teorico", "Teórico")}</tbody></table></div>`;
  }

  function renderMetrics(d) {
    const g = d.greeks || {};
    const items = [
      [d.limit.flow === "debito" ? "Débito natural (por ação)" : "Crédito natural (por ação)", FMT.price(d.entry_per_unit)],
      ["Fluxo total na entrada", FMT.signedBrl(d.net_premium_total)],
      ["Perda máxima", FMT.brl(d.max_loss)],
      ["Lucro máximo", FMT.brl(d.max_profit)],
      ["Breakeven (vencimento)", d.breakevens.map(FMT.price).join(" / ")],
      ["Lucro máx. ÷ perda máx.", FMT.ratio(d.reward_risk)],
      ["Perda máx. ÷ lucro máx.", FMT.ratio(d.risk_reward)],
      ["POP no vencimento", d.pop === null ? `indisponível (${esc(d.pop_unavailable_reason)})` : FMT.pct(d.pop)],
      ["Prob. fechar além do alvo", FMT.pct(d.prob_target_at_expiry)],
      ["Prob. tocar o alvo", FMT.pct(d.prob_touch_target)],
      ...d.scenarios.map((s) => [`Resultado: ${s.name} (${FMT.price(s.price)})`, `<span class="${(s.pnl ?? 0) >= 0 ? "pos" : "neg"}" title="${esc(s.basis)}">${FMT.signedBrl(s.pnl)}</span>`]),
      ["Delta (R$ por R$ 1 no ativo)", FMT.num(g.delta, 2)],
      ["Gamma", FMT.num(g.gamma, 3)],
      ["Theta (R$/dia útil)", FMT.signedBrl(g.theta_per_day)],
      ["Vega (R$ por 1 p.p. de vol)", FMT.signedBrl(g.vega_per_pp)],
      ["Rho (R$ por 1 p.p. de juros)", FMT.signedBrl(g.rho_per_pp)],
      ["Custo de execução (natural − mid)", FMT.pct(d.execution_cost_pct_width) + " da largura"],
      ...(d.nobre ? [
        [`R. Nobre: custo ÷ largura (máx. ${FMT.pct(d.nobre.max_cost_fraction, 1)})`, `${FMT.pct(d.nobre.cost_ratio, 1)} ${d.nobre.cost_ok ? "✓" : "✗ acima"} · teto ${FMT.price(d.nobre.max_cost)}`],
        ["R. Nobre: vendida antes do alvo", d.nobre.target_ok === null ? "sem alvo informado" : d.nobre.target_ok ? "✓ sim" : "✗ não (além do alvo)"],
      ] : []),
      ...(d.credit_stop ? stopMetrics(d.credit_stop) : []),
    ];
    $("metrics").innerHTML = items.map(([k, v]) => `<div><span>${k}</span><span>${v}</span></div>`).join("");
  }

  // Stop 1:1 (Credit Spread Investing): métricas do manejo no detalhe.
  function stopMetrics(s) {
    const tipEv = "Média dos caminhos simulados: stop = −perda no stop; sem stop = crédito − valor no vencimento";
    return [
      ["Stop 1:1: custo para desmontar (gatilho)", `${FMT.price(s.trigger_cost)} por ação (${FMT.num(1 + s.loss_multiple, 0)} × crédito)`],
      ["Stop 1:1: ativo que aciona hoje", s.stop_price_today === null ? "inatingível hoje" : FMT.price(s.stop_price_today)],
      ["Stop 1:1: mais próximo até o vencimento", `${FMT.price(s.stop_price_nearest)} (${FMT.pct(s.stop_distance_pct, 1)} do spot · ${FMT.num(s.stop_distance_sigmas, 2)} σ)`],
      ["Stop 1:1: no vencimento", FMT.price(s.stop_price_expiry)],
      ["Stop 1:1: perda no stop", `${FMT.brl(s.stop_loss_total)} <span class="muted">(crédito + saída ${FMT.price(s.exit_cost_per_unit)}/ação)</span>`],
      ["Prob. de acionar o stop", `${FMT.pct(s.prob_stop, 1)}${s.median_stop_day ? ` <span class="muted">(mediana: ${FMT.num(s.median_stop_day, 0)} du)</span>` : ""}`],
      ["Prob. de ficar com o crédito inteiro", FMT.pct(s.prob_full_credit, 1)],
      ["Prob. de lucro com o manejo", FMT.pct(s.prob_profit, 1)],
      ["Resultado esperado com o stop", `<span class="${s.expected_pnl_total >= 0 ? "pos" : "neg"}" title="${tipEv}">${FMT.signedBrl(s.expected_pnl_total)}</span> <span class="muted">(${FMT.pct(s.ev_on_risk, 1)} da perda no stop)</span>`],
      ["Resultado esperado sem manejo", `<span class="muted">${FMT.signedBrl(s.expected_pnl_no_stop_per_unit * (state.view ? state.view.units : 1))}</span>`],
    ];
  }

  function renderLegs(d) {
    const rows = d.legs.map((l) => `<tr>
      <td class="l">${l.side === "compra" ? "Compra" : "Venda"}</td><td class="l">${esc(l.symbol)}</td><td class="l">${l.option_type} ${l.exercise_style === "american" ? "americana" : "europeia"}</td>
      <td>${FMT.price(l.strike)}</td><td>${FMT.price(l.bid)}</td><td>${FMT.price(l.ask)}</td><td>${FMT.price(l.mid)}</td><td>${FMT.price(l.last)}${l.price_basis === "ultimo_b3" ? ' <span class="badge mid" title="Preço usado: último negócio do pregão (fechamento oficial da B3), indicativo; sem bid/ask">B3</span>' : ""}</td>
      <td>${FMT.pct(l.spread_pct_mid)}</td><td title="${esc(l.volume_source || "")}">${FMT.int(l.deals)}${l.volume_source === "barra D1" ? "*" : ""}</td><td title="${esc(l.volume_source || "")}">${FMT.brl(l.turnover_brl)}${l.volume_source === "barra D1" ? "*" : ""}</td>
      <td>${FMT.datetime(l.quote_time)} <span class="muted">(${FMT.age(l.quote_age_seconds)})</span></td>
      <td title="${esc(l.iv_status)}">${FMT.pct(l.iv)}</td>
      <td class="l">${l.flags.length ? `<span class="badge bad">${esc(l.flags.join(", "))}</span>` : '<span class="badge ok">ok</span>'}${l.ref_note ? ` <span class="badge mid" title="${esc(l.ref_note)}">dado corrigido (B3)</span>` : ""}</td></tr>`).join("");
    $("legs").innerHTML = `<thead><tr><th class="l">Lado</th><th class="l">Ticker</th><th class="l">Tipo</th><th>Strike</th><th>Bid</th><th>Ask</th><th>Mid</th><th>Último</th><th>Spread</th><th>Negócios</th><th>Volume R$</th><th>Último tick</th><th>IV</th><th class="l">Qualidade</th></tr></thead><tbody>${rows}</tbody>`;
  }

  function renderScore(d) {
    const row = state.analysis.results.find((r) => r.id === d.id);
    const comps = row && row.score_components;
    if (!comps) { $("score-box").innerHTML = '<span class="muted">Score disponível na lista ranqueada.</span>'; return; }
    const colors = { scenario: "#1f5fbf", reward_risk: "#7a2fc0", pop: "#157a3c", liquidity: "#e08a00", execution_cost: "#667085", expected: "#1f5fbf", no_stop: "#157a3c", capital: "#7a2fc0", exit_cost: "#667085" };
    const names = { scenario: "Resultado no alvo", reward_risk: "Lucro/perda", pop: "POP", liquidity: "Liquidez", execution_cost: "Custo de execução", expected: "Esperado c/ stop", no_stop: "Sem acionar o stop", capital: "Crédito ÷ garantia", exit_cost: "Custo de saída" };
    const bar = Object.entries(comps).map(([k, c]) => c.percentile === null ? "" : `<span style="width:${c.effective_weight * c.percentile * 100}%;background:${colors[k]}" title="${names[k]}"></span>`).join("");
    const table = Object.entries(comps).map(([k, c]) => `<tr><td class="l"><i style="display:inline-block;width:10px;height:10px;background:${colors[k]}"></i> ${names[k]}</td><td class="l muted">${esc(c.description)}</td><td>${FMT.pct(c.weight, 0)}</td><td>${FMT.pct(c.effective_weight, 0)}</td><td>${c.percentile === null ? "indisponível" : FMT.pct(c.percentile, 0)}</td></tr>`).join("");
    $("score-box").innerHTML = `<div><b>Score ${FMT.num(row.score, 0)}</b>${row.score_capped ? " (limitado por liquidez)" : ""}</div><div class="score-bar">${bar}</div>
      <div class="table-wrap"><table class="legs small"><thead><tr><th class="l">Critério</th><th class="l">Medida</th><th>Peso</th><th>Peso efetivo</th><th>Percentil</th></tr></thead><tbody>${table}</tbody></table></div>`;
  }

  function renderAssumptions(d) {
    const a = state.analysis.assumptions;
    const items = [
      `Entrada calculada pelo ${a.entry_basis}. Mid é só referência.`,
      `POP: ${d.pop_method}${d.pop === null ? ` — indisponível: ${d.pop_unavailable_reason}` : ""}.`,
      `Volatilidade: ${d.vol_source}. IV: ${a.iv_method}.`,
      `Juros: ${FMT.pct(a.rate_annual, 2)} a.a. (contínua ${FMT.pct(a.rate_continuous, 2)}). Custos considerados: ${FMT.brl(a.costs_brl)}.`,
      `Cenário-alvo: ${d.scenario_at_expiry ? "avaliado no vencimento (payoff exato)" : `avaliado em ${FMT.date(a.horizon_date)} pelo modelo (valor teórico, não payoff)`}.`,
      `Probabilidade de toque: princípio da reflexão (monitoramento contínuo); aproximação.`,
      ...(d.credit_stop && state.analysis.credit_stop ? [`Stop 1:1: ${state.analysis.credit_stop.method}.`] : []),
      d.simulation.assumptions,
      a.settlement_note,
      `Open interest não disponível no MT5 (${state.broker || "corretora"}); volume e negócios não equivalem a contratos em aberto.`,
    ];
    $("assumptions").innerHTML = items.map((t) => `<li>${esc(t)}</li>`).join("");
  }

  function setupSlider(d) {
    const sim = d.simulation;
    const slider = $("time-slider");
    $("sim-assumptions").textContent = sim.model_available ? sim.assumptions : `Simulação temporal indisponível: ${sim.model_reason}. Exibindo só o payoff no vencimento.`;
    $("time-control").hidden = !sim.model_available;
    slider.max = Math.max(0, sim.dates.length - 1);
    slider.value = 0;
    renderSized();
  }

  function drawPayoff() {
    const d = state.view;
    if (!d) return;
    const sim = d.simulation;
    const i = Number($("time-slider").value);
    const sel = sim.dates[i];
    const showModel = sel && sel.business_days_left > 0;
    $("time-label").textContent = sel ? `${FMT.date(sel.date)} · ${sel.business_days_left} du até o vencimento${sel.business_days_left === 0 ? " (payoff exato)" : " (modelo)"}` : "";
    $("payoff-legend").innerHTML = Payoff.legend(showModel, sel, sim.expiry_label);
    Payoff.render($("payoff"), d, i, $("tooltip"));
    // Níveis no gráfico do ativo
    const levels = [
      { label: "Atual", value: d.spot, color: "#1d2330", size: 1 },
      ...d.breakevens.map((b) => ({ label: "BE venc.", value: b, color: "#157a3c", dashed: true, size: 1.6, fit: true })),
      ...(showModel ? sel.breakevens.map((b) => ({ label: `Equil. ${FMT.date(sel.date)}`, value: b, color: "#1f5fbf", dashed: true, dash: [2, 3] })) : []),
      ...(d.target_price ? [{ label: "Alvo", value: d.target_price, color: "#7a2fc0", dashed: true, size: 1.4 }] : []),
      ...(d.credit_stop ? [{ label: "Stop 1:1", value: d.credit_stop.stop_price_nearest, color: "#c0262d", dashed: true, size: 1.6, fit: true }] : []),
      ...d.legs.map((l) => ({ label: `Strike ${l.side === "compra" ? "C" : "V"}`, value: l.strike, color: "#98a2b3", dashed: true, dash: [2, 4], fit: true })),
    ];
    setLevels(levels, "analysis");
    ExitPanel.render($("exit-box"), { sim, index: i, spot: d.spot, target: d.target_price, units: d.units });
  }

  // ---------- painel lateral ----------
  function setSide(open) {
    state.side = open;
    $("side").classList.toggle("collapsed", !open);
    $("layout").classList.toggle("side-collapsed", !open);
    $("side-toggle").setAttribute("aria-expanded", String(open));
    $("side-toggle").textContent = open ? "⟩" : "⟨";
    if (open) { setTimeout(() => { loadCandles(); Candles.resize(); }, 60); }
    if (state.detail) setTimeout(drawPayoff, 200);
    setTimeout(Protected.redraw, 200);
    setTimeout(Simulator.redraw, 200);
    savePrefs();
  }

  // ---------- preferências ----------
  let saveTimer = null;
  function savePrefs(now = false) {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      const prefs = { side_width: state.sideWidth || null, nobre_filter: $("nobre_filter").checked, nobre_target_required: $("nobre_target_required").checked, nobre_fraction: $("nobre_fraction").value, nobre_prefer_close: $("nobre_prefer_close").checked, european_short: $("european_short").checked, credit_stop: $("credit_stop").checked, direction: radio("direction"), flow: radio("flow"), tf: state.tf, side: state.side, tab: state.tab, size_mode: state.size.mode, include_illiquid: $("include_illiquid").checked, tracking: Tracking.prefs(), heatmap: Heatmap.prefs(), protected: Protected.prefs(), simulator: Simulator.prefs() };
      if (state.offHoursSource) prefs.off_hours_source = state.offHoursSource;
      for (const f of PREF_FIELDS) prefs[f] = $(f).value;
      fetch("/api/preferences", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(prefs) }).catch(() => {});
    }, now ? 0 : 600);
  }

  function applyDefaults(def, prefs) {
    const a = def.analysis, lq = def.liquidity;
    const base = {
      quantity: a.quantity, dte_min: a.dte_min_business_days, dte_max: a.dte_max_business_days,
      max_spread_pct_mid: lq.max_spread_pct_mid * 100, min_deals: lq.min_deals, min_turnover_brl: lq.min_turnover_brl,
      max_quote_age_seconds: lq.max_quote_age_seconds, rate_annual: +(def.rate_annual * 100).toFixed(2),
      limit_aggressiveness: a.limit_aggressiveness * 100, costs_brl: 0,
      w_scenario: a.weights.scenario * 100, w_reward_risk: a.weights.reward_risk * 100, w_pop: a.weights.pop * 100,
      w_liquidity: a.weights.liquidity * 100, w_execution_cost: a.weights.execution_cost * 100,
    };
    for (const [k, v] of Object.entries(base)) if ($(k)) $(k).value = +(+v).toFixed(4);
    for (const f of PREF_FIELDS) if (prefs[f] !== undefined && prefs[f] !== "") $(f).value = prefs[f];
    if (prefs.direction) document.querySelector(`input[name=direction][value=${prefs.direction}]`).checked = true;
    if (prefs.flow) document.querySelector(`input[name=flow][value=${prefs.flow}]`).checked = true;
    if (prefs.include_illiquid) $("include_illiquid").checked = true;
    if (prefs.size_mode === "amount" || prefs.size_mode === "qty") state.size.mode = prefs.size_mode;
    $("nobre_filter").checked = !!prefs.nobre_filter;
    $("credit_stop").checked = !!prefs.credit_stop;
    $("nobre_target_required").checked = !!prefs.nobre_target_required;
    if (prefs.nobre_fraction) $("nobre_fraction").value = prefs.nobre_fraction;
    $("european_short").checked = !!prefs.european_short;
    if (prefs.nobre_prefer_close !== undefined) $("nobre_prefer_close").checked = !!prefs.nobre_prefer_close;
    if (["mn1", "w1", "d1", "h4", "h1"].includes(prefs.tf)) state.tf = prefs.tf;
    document.querySelectorAll(".tf button").forEach((b) => b.classList.toggle("active", b.dataset.tf === state.tf));
    if (prefs.side_width) setSideWidth(Number(prefs.side_width), false);
    if (prefs.side === false) setSide(false);
    if (prefs.tracking) Tracking.applyPrefs(prefs.tracking);
    if (prefs.heatmap) Heatmap.applyPrefs(prefs.heatmap);
    Protected.init(def, prefs.protected);
    Simulator.init(def, prefs.simulator);
    if (["tracking", "heatmap", "protected", "simulator"].includes(prefs.tab)) switchTab(prefs.tab);
  }

  async function init() {
    const [def, prefs] = await Promise.all([api("/api/defaults"), api("/api/preferences").catch(() => ({}))]);
    state.defaults = def;
    applyDefaults(def, prefs);
    updateKindText();
    document.querySelectorAll("input[name=direction], input[name=flow], #nobre_filter, #target_price, #target_pct, #european_short, #credit_stop").forEach((r) => r.addEventListener("change", () => { updateKindText(); savePrefs(); }));
    $("underlying").addEventListener("change", onUnderlying);
    $("star-btn").addEventListener("click", onStar);
    Watch.on(updateStar);
    Watch.load();
    $("form").addEventListener("submit", onSubmit);
    $("form").addEventListener("change", savePrefs);
    $("quantity").addEventListener("input", () => onSizeInput("qty"));
    $("invest_amount").addEventListener("input", () => onSizeInput("amount"));
    $("costs_brl").addEventListener("input", syncSizeFields);
    $("ranking").querySelector("thead").addEventListener("click", onHeaderClick);
    $("ranking").querySelector("tbody").addEventListener("click", onRowClick);
    let rafPayoff = 0;
    $("time-slider").addEventListener("input", () => { cancelAnimationFrame(rafPayoff); rafPayoff = requestAnimationFrame(drawPayoff); });
    $("side-toggle").addEventListener("click", () => setSide(!state.side));
    document.querySelectorAll(".tf button").forEach((b) => b.addEventListener("click", () => {
      state.tf = b.dataset.tf;
      document.querySelectorAll(".tf button").forEach((x) => x.classList.toggle("active", x === b));
      loadCandles();
      savePrefs();
    }));
    window.addEventListener("resize", () => { if (state.detail) drawPayoff(); });
    document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => switchTab(b.dataset.tab)));
    setupSplitter();
    setupTooltips();
    fullListWhenComplete($("underlying"));
    fullListWhenComplete($("tf-underlying"));
    fullListWhenComplete($("pr-underlying"));
    fullListWhenComplete($("sm-underlying"));
    $("fit-candles").addEventListener("click", () => Candles.fitAll());
    $("max-candles").addEventListener("click", () => {
      if (!state.side) setSide(true);
      toggleMax($("side"), $("max-candles"), () => { Candles.resize(); requestAnimationFrame(Candles.fitAll); });
    });
    $("max-payoff").addEventListener("click", () => toggleMax($("payoff-wrap"), $("max-payoff"), drawPayoff));
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && maximized) toggleMax(maximized.el, maximized.button, maximized.after);
    });
    $("btn-track").addEventListener("click", () => {
      if (!state.detail) return;
      switchTab("tracking");
      Tracking.prefillFromAnalysis(state.view || state.detail, state.analysis);
    });
    await pollStatus();
    setInterval(pollStatus, 5000);
  }

  // Campo de ativo com <datalist>: o Chrome filtra as opções pelo texto digitado, então com um
  // ticker COMPLETO só sobraria ele mesmo. Nesse caso, ao clicar/focar, o campo é esvaziado
  // (o ticker fica como texto de fundo) para listar todos; sem nova escolha, o valor volta.
  // Texto parcial (ex.: "PE") continua filtrando normalmente.
  function fullListWhenComplete(input) {
    const listId = input.getAttribute("list");
    const isComplete = (v) => !!v && [...document.getElementById(listId).options].some((o) => o.value === v);
    let saved = null;
    let savedPlaceholder = input.placeholder;
    const open = () => {
      const v = input.value.trim().toUpperCase();
      if (saved !== null || !isComplete(v)) return;
      saved = v;
      savedPlaceholder = input.placeholder;
      input.placeholder = v;
      input.value = "";
    };
    input.addEventListener("mousedown", open);
    input.addEventListener("focus", open);
    input.addEventListener("blur", () => {
      if (saved === null) return;
      const restore = input.value.trim() === "";
      input.placeholder = savedPlaceholder;
      if (restore) {
        input.value = saved;
        saved = null;
        input.dispatchEvent(new Event("change", { bubbles: true })); // reexibe ícone/estado
      } else {
        saved = null;
      }
    });
    input.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && saved !== null) { input.value = saved; input.blur(); }
    });
  }

  function setupTooltips() {
    const tip = $("tooltip");
    const show = (el, x, y) => {
      tip.innerHTML = el.dataset.tip;
      tip.hidden = false;
      const w = tip.offsetWidth, h = tip.offsetHeight;
      tip.style.left = Math.min(x + 14, window.innerWidth - w - 8) + "px";
      tip.style.top = (y + h + 24 > window.innerHeight ? y - h - 10 : y + 14) + "px";
    };
    document.addEventListener("mouseover", (ev) => {
      const el = ev.target.closest("[data-tip]");
      if (el) show(el, ev.clientX, ev.clientY);
    });
    document.addEventListener("mousemove", (ev) => {
      const el = ev.target.closest("[data-tip]");
      if (el) show(el, ev.clientX, ev.clientY);
    });
    document.addEventListener("mouseout", (ev) => {
      if (ev.target.closest("[data-tip]") && !ev.relatedTarget?.closest?.("[data-tip]")) tip.hidden = true;
    });
    document.addEventListener("focusin", (ev) => {
      const el = ev.target.closest("[data-tip]");
      if (!el) return;
      const r = el.getBoundingClientRect();
      show(el, r.left, r.bottom);
    });
    document.addEventListener("focusout", (ev) => { if (ev.target.closest("[data-tip]")) tip.hidden = true; });
  }

  // Do heatmap: abre a Análise com o ativo escolhido.
  function analyzeTicker(ticker) {
    switchTab("analysis");
    $("underlying").value = ticker;
    $("underlying").dispatchEvent(new Event("change", { bubbles: true }));
    $("tab-analysis").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  window.App = { marginHtml, broker: () => state.broker || "corretora", analyzeTicker, api, showUnderlying, setLevels, toggleMax, savePrefs, tooltip: () => $("tooltip") };
  init();
})();
