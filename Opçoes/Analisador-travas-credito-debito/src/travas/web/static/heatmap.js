// Aba Heatmap: treemap (squarified) dos ativos com opções listadas. Cor = métrica escolhida;
// tamanho = volume médio 20d, valor de mercado aproximado ou igual; agrupado por setor (B3).
const Heatmap = (() => {
  const $ = (id) => document.getElementById(id);
  const st = { data: null, metric: "1d", size: "turnover", group: true, selected: null, ready: false, loading: false };
  const api = (...a) => App.api(...a);

  const METRICS = {
    "1d": { label: "Dia", cap: 0.03, kind: "chg", period: "1 pregão" },
    "1w": { label: "Semana", cap: 0.06, kind: "chg", period: "5 pregões" },
    "1m": { label: "Mês", cap: 0.12, kind: "chg", period: "21 pregões" },
    "1y": { label: "Ano", cap: 0.40, kind: "chg", period: "252 pregões" },
    vol: { label: "Volume", kind: "vol" },
    deals: { label: "Negócios", kind: "deals" },
  };
  const NEG = [198, 40, 40], NEU = [206, 211, 220], POS = [27, 138, 58];
  const VLOW = [233, 236, 242], VHIGH = [31, 95, 191];

  const mix = (a, b, t) => a.map((v, i) => Math.round(v + (b[i] - v) * t));
  const rgb = (c) => `rgb(${c.join(",")})`;
  const textOn = (c) => (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] > 150 ? "#1d2330" : "#ffffff");
  const compact = (v) => {
    if (!FMT.ok(v)) return "—";
    const a = Math.abs(v);
    if (a >= 1e9) return `R$ ${FMT.num(v / 1e9, 1)} bi`;
    if (a >= 1e6) return `R$ ${FMT.num(v / 1e6, 1)} mi`;
    if (a >= 1e3) return `R$ ${FMT.num(v / 1e3, 0)} mil`;
    return FMT.brl(v);
  };
  const signedPct = (v, d = 2) => (FMT.ok(v) ? (v > 0 ? "+" : "") + FMT.pct(v, d) : "—");

  // ---------- squarified treemap ----------
  function worst(row, side) {
    const s = row.reduce((a, r) => a + r.area, 0);
    const max = Math.max(...row.map((r) => r.area)), min = Math.min(...row.map((r) => r.area));
    return Math.max((side * side * max) / (s * s), (s * s) / (side * side * min));
  }
  function squarify(items, x, y, w, h) {
    // items: [{value, ...}] (value > 0). Devolve [{item, x, y, w, h}].
    const total = items.reduce((a, i) => a + i.value, 0);
    if (!total || w <= 0 || h <= 0) return [];
    const nodes = items.map((i) => ({ item: i, area: (i.value / total) * w * h })).sort((a, b) => b.area - a.area);
    const out = [];
    let rect = { x, y, w, h };
    let row = [];
    const layoutRow = (r) => {
      const s = r.reduce((a, n) => a + n.area, 0);
      if (rect.w >= rect.h) { // coluna à esquerda
        const cw = s / rect.h;
        let cy = rect.y;
        for (const n of r) { const nh = n.area / cw; out.push({ item: n.item, x: rect.x, y: cy, w: cw, h: nh }); cy += nh; }
        rect = { x: rect.x + cw, y: rect.y, w: rect.w - cw, h: rect.h };
      } else { // linha no topo
        const rh = s / rect.w;
        let cx = rect.x;
        for (const n of r) { const nw = n.area / rh; out.push({ item: n.item, x: cx, y: rect.y, w: nw, h: rh }); cx += nw; }
        rect = { x: rect.x, y: rect.y + rh, w: rect.w, h: rect.h - rh };
      }
    };
    for (const n of nodes) {
      const side = Math.min(rect.w, rect.h);
      if (!row.length || worst([...row, n], side) <= worst(row, side)) row.push(n);
      else { layoutRow(row); row = [n]; }
    }
    if (row.length) layoutRow(row);
    return out;
  }

  // ---------- valores por métrica ----------
  // Escala da cor recalculada a cada desenho, a partir dos próprios ativos:
  // - variações: limite = máx(limite-base do período, percentil 85 de |variação|), para não
  //   saturar quase tudo num período forte (ex.: ano com várias altas de +100%);
  // - volume: razão "hoje ÷ média 20d" comparada à MEDIANA dos ativos; durante o pregão o dia é
  //   parcial e todos ficam abaixo de 1×, então o que informa é quem está acima/abaixo dos pares.
  const quantile = (vals, q) => {
    const v = vals.filter(FMT.ok).sort((a, b) => a - b);
    if (!v.length) return null;
    const pos = (v.length - 1) * q, lo = Math.floor(pos);
    return v[lo] + (v[Math.min(lo + 1, v.length - 1)] - v[lo]) * (pos - lo);
  };
  function scaleFor(all) {
    const m = METRICS[st.metric];
    if (m.kind === "chg") {
      const p85 = quantile(all.map((i) => Math.abs(i.changes[st.metric].pct)), 0.85) || 0;
      const raw = Math.max(m.cap, p85);
      const step = raw < 0.1 ? 0.01 : raw < 0.5 ? 0.05 : 0.1; // limite "redondo"
      return { cap: Math.ceil(raw / step) * step };
    }
    if (m.kind === "vol") return { median: quantile(all.map((i) => i.turnover_ratio).filter((r) => r > 0), 0.5) || 1 };
    return {};
  }

  function colorOf(item, all) {
    const m = METRICS[st.metric];
    const sc = st.scale || {};
    if (m.kind === "chg") {
      const v = item.changes[st.metric].pct;
      if (!FMT.ok(v)) return [235, 237, 241];
      const t = Math.max(-1, Math.min(1, v / (sc.cap || m.cap)));
      return t < 0 ? mix(NEU, NEG, -t) : mix(NEU, POS, t);
    }
    if (m.kind === "vol") {
      const r = item.turnover_ratio;
      if (!FMT.ok(r) || r <= 0) return [235, 237, 241];
      const rel = Math.log2(r / (sc.median || 1)); // 0 = igual à mediana dos ativos
      const t = Math.max(0, Math.min(1, (rel + 1.5) / 3)); // ≤ 0,35× a ≥ 2,8× a mediana
      return mix(VLOW, VHIGH, t);
    }
    // negócios: percentil entre os ativos (não há histórico para comparar com a média)
    const vals = all.map((i) => i.deals_session).filter(FMT.ok).sort((a, b) => a - b);
    const v = item.deals_session;
    if (!FMT.ok(v) || !vals.length) return [235, 237, 241];
    const t = vals.findIndex((x) => x >= v) / Math.max(1, vals.length - 1);
    return mix(VLOW, VHIGH, t);
  }

  function lines(item) {
    const m = METRICS[st.metric];
    if (m.kind === "chg") {
      const c = item.changes[st.metric];
      return [signedPct(c.pct), FMT.ok(c.abs) ? `${c.abs > 0 ? "+" : ""}${FMT.price(c.abs)} · ${FMT.price(item.price)}` : FMT.price(item.price)];
    }
    if (m.kind === "vol") return [compact(item.turnover_today), FMT.ok(item.turnover_ratio) ? `${FMT.num(item.turnover_ratio, 2)}× média 20d` : "sem média"];
    return [FMT.ok(item.deals_session) ? FMT.int(item.deals_session) : "—", "negócios na sessão"];
  }

  function sizeOf(item) {
    const v = st.size === "cap" ? item.market_cap_approx : st.size === "turnover" ? item.turnover_avg20 : 1;
    return FMT.ok(v) && v > 0 ? v : null;
  }

  function tip(item) {
    const c = item.changes;
    const row = (k, v) => `<tr><td>${k}</td><td style="text-align:right;padding-left:1rem"><b>${v}</b></td></tr>`;
    return `<div><b>${esc(item.ticker)}</b> · ${esc(item.name)}</div><div class="muted">${esc(item.sector)}${item.subsector ? " / " + esc(item.subsector) : ""}</div>
      <table style="margin-top:.3rem">${row("Preço", FMT.price(item.price))}${row("Dia", signedPct(c["1d"].pct))}${row("Semana", signedPct(c["1w"].pct))}${row("Mês", signedPct(c["1m"].pct))}${row("Ano", signedPct(c["1y"].pct))}
      ${row("Volume hoje", compact(item.turnover_today))}${row("Média 20d", compact(item.turnover_avg20))}${row("Negócios (sessão)", FMT.int(item.deals_session))}
      ${row("Vol. histórica 20d", FMT.pct(item.hv20))}${row("Valor de mercado (aprox.)", compact(item.market_cap_approx))}</table>
      <div class="muted">Clique para ver o resumo</div>`;
  }

  // ---------- desenho ----------
  function render() {
    const d = st.data;
    if (!d) return;
    const box = $("hm-map");
    const W = box.clientWidth, H = box.clientHeight;
    const items = d.items.map((i) => ({ ...i, value: sizeOf(i) })).filter((i) => i.value);
    st.scale = scaleFor(items);
    const missing = d.items.length - items.length;
    const groups = {};
    for (const i of items) (groups[st.group ? i.sector : "Todos"] ||= []).push(i);
    const groupList = Object.entries(groups).map(([name, list]) => ({ name, list, value: list.reduce((a, i) => a + i.value, 0) }));
    let html = "";
    const HEAD = st.group ? 18 : 0, GAP = 2;
    for (const g of squarify(groupList, 0, 0, W, H)) {
      const { x, y, w, h } = g;
      if (st.group) html += `<div class="hm-group" style="left:${x}px;top:${y}px;width:${w - GAP}px;height:${h - GAP}px"><span>${esc(w > 60 ? g.item.name : "")}</span></div>`;
      for (const t of squarify(g.item.list, x + 1, y + HEAD, w - GAP - 2, h - HEAD - GAP - 1)) {
        const it = t.item;
        const c = colorOf(it, items);
        const fg = textOn(c);
        const minSide = Math.min(t.w, t.h);
        const fs = Math.max(9, Math.min(26, Math.sqrt(t.w * t.h) / 6.5));
        const [l1, l2] = lines(it);
        const showIcon = minSide > 44, showL1 = t.h > 34 && t.w > 40, showL2 = t.h > 62 && t.w > 70;
        html += `<button class="hm-tile${st.selected === it.ticker ? " sel" : ""}" data-t="${esc(it.ticker)}" data-tip="${esc(tip(it))}"
          style="left:${t.x}px;top:${t.y}px;width:${Math.max(0, t.w - 1)}px;height:${Math.max(0, t.h - 1)}px;background:${rgb(c)};color:${fg};font-size:${fs}px"
          aria-label="${esc(it.ticker)} ${esc(l1)}">
          ${minSide > 22 ? `<span class="hm-head">${showIcon ? tickerIcon(it.ticker, Math.round(Math.min(28, fs * 1.2))) : ""}<b>${esc(it.ticker)}</b></span>` : ""}
          ${showL1 ? `<span class="hm-v1">${esc(l1)}</span>` : ""}${showL2 ? `<span class="hm-v2">${esc(l2)}</span>` : ""}</button>`;
      }
    }
    box.innerHTML = html;
    renderLegend(missing);
  }

  function renderLegend(missing) {
    const m = METRICS[st.metric];
    let grad, labels, title;
    if (m.kind === "chg") {
      const cap = (st.scale && st.scale.cap) || m.cap;
      grad = `linear-gradient(90deg, ${rgb(NEG)}, ${rgb(NEU)}, ${rgb(POS)})`;
      labels = [signedPct(-cap, 0), "0%", signedPct(cap, 0)];
      title = `Variação em ${m.period} (cor satura em ±${FMT.pct(cap, 0)})`;
    } else if (m.kind === "vol") {
      grad = `linear-gradient(90deg, ${rgb(VLOW)}, ${rgb(VHIGH)})`;
      const med = (st.scale && st.scale.median) || 1;
      labels = ["menos ativo", `mediana ${FMT.num(med, 2)}×`, "mais ativo"];
      title = "Volume do dia ÷ média de 20 pregões, comparado à mediana dos ativos" +
        (st.data.market && st.data.market.is_open ? " (dia parcial)" : "");
    } else {
      grad = `linear-gradient(90deg, ${rgb(VLOW)}, ${rgb(VHIGH)})`;
      labels = ["menos", "", "mais"];
      title = "Negócios na sessão, ordenados entre os ativos (sem histórico no MT5)";
    }
    const sizeTxt = { turnover: "volume médio 20d", cap: "valor de mercado aprox.", equal: "igual" }[st.size];
    $("hm-legend").innerHTML = `<span class="hm-legend-title">${esc(title)}</span>
      <span class="hm-scale"><span class="hm-grad" style="background:${grad}"></span><span class="hm-legend-labels">${labels.map((l) => `<span>${esc(l)}</span>`).join("")}</span></span>
      <span class="muted small">Tamanho: ${sizeTxt}${missing ? ` · ${missing} ativo(s) sem dado de tamanho omitido(s)` : ""}</span>`;
  }

  // ---------- dados ----------
  async function load() {
    if (st.loading) return;
    st.loading = true;
    $("hm-meta").textContent = "Coletando barras diárias no MT5 e cadastro na B3… (a 1ª carga pode levar alguns segundos)";
    $("hm-refresh").disabled = true;
    try {
      Busy.show($("hm-map-host"), st.data ? "Atualizando…" : "Carregando o heatmap (MT5 + B3)…");
      try {
        st.data = await api("/api/heatmap");
      } finally {
        Busy.hide($("hm-map-host"));
      }
      const d = st.data;
      $("hm-meta").innerHTML = `${d.items.length} ativos com opções · dados de ${FMT.datetime(d.collected_at)}${d.from_cache ? " (cache)" : ""} · ${esc(d.market.label)}` +
        (d.b3_errors.length ? ` · <span class="neg">B3 indisponível para ${esc(d.b3_errors.join(", "))}</span>` : "") +
        (d.excluded.length ? ` · fora: ${esc(d.excluded.join(", "))} (índice)` : "");
      $("hm-notes").textContent = d.notes.join(" ");
      render();
    } catch (e) {
      $("hm-meta").innerHTML = `<span class="neg">Erro: ${esc(e.message)}</span>`;
    } finally {
      st.loading = false;
      $("hm-refresh").disabled = false;
    }
  }

  // ---------- detalhe do ativo ----------
  async function select(ticker) {
    st.selected = ticker;
    render();
    const card = $("hm-detail");
    card.hidden = false;
    card.innerHTML = `<div class="busy-host" style="min-height:120px"><p class="muted">Carregando ${esc(ticker)}…</p></div>`;
    Busy.show(card.firstElementChild, `Carregando ${ticker}…`);
    App.showUnderlying(ticker, "heatmap");
    try {
      const d = await api(`/api/heatmap/${encodeURIComponent(ticker)}`);
      if (st.selected !== ticker) return;
      renderDetail(d);
      const t = d.metrics.technical;
      App.setLevels([
        { label: "Máx. 52 sem.", value: t.high52, color: "#157a3c", dashed: true, dash: [4, 3] },
        { label: "Mín. 52 sem.", value: t.low52, color: "#b42318", dashed: true, dash: [4, 3] },
        { label: "SMA 200", value: t.sma200, color: "#667085", dashed: true, dash: [2, 3] },
      ], "heatmap");
      card.scrollIntoView({ behavior: "smooth", block: "start" });
      loadIv(ticker, d);
    } catch (e) {
      card.innerHTML = `<p class="neg">Erro ao carregar ${esc(ticker)}: ${esc(e.message)}</p>`;
    }
  }

  const kv = (rows) => `<div class="metrics">${rows.map(([k, v]) => `<div><span>${k}</span><span>${v}</span></div>`).join("")}</div>`;

  function renderDetail(d) {
    const m = d.metrics, c = m.changes, t = m.technical, p = d.profile || {}, ev = d.events || {};
    const ok = (b) => (b === null || b === undefined ? "—" : b ? "✓ acima" : "✗ abaixo");
    const signals = [t.ema_trend === "alta", t.above_sma50, t.above_sma200, t.rsi14 > 50].filter((x) => x !== null && x !== undefined);
    const bull = signals.filter(Boolean).length;
    const company = p.is_company
      ? `${esc(p.trading_name || "")} · ${esc(p.company_name || "")}`
      : p.is_company === false ? "ETF / fundo de índice (sem cadastro de empresa na B3)" : "cadastro da B3 indisponível";
    const sector = [p.sector, p.subsector, p.segment].filter(Boolean).map(esc).join(" / ");
    const cashRows = (ev.cash || []).slice(0, 10).map((e) => `<tr><td class="l">${esc(e.type)}</td><td>${FMT.date(e.ex_date)}</td><td>${FMT.date(e.payment_date)}</td><td>${FMT.num(e.value, 4)}</td><td>${FMT.ok(e.value) && m.price ? FMT.pct(e.value / m.price, 2) : "—"}</td></tr>`).join("");
    const stockRows = [...(ev.stock || []), ...(ev.subscriptions || [])].map((e) => `<tr><td class="l">${esc(e.type)}</td><td>${FMT.date(e.ex_date)}</td><td>${FMT.date(e.approved_on)}</td><td>${FMT.ok(e.factor) ? FMT.num(e.factor, 4) : FMT.ok(e.percentage) ? FMT.pct(e.percentage / 100, 2) : "—"}</td></tr>`).join("");
    const upcoming = (ev.upcoming || []).map((e) => `${esc(e.type)} de ${FMT.num(e.value, 4)} (data-com ${FMT.date(e.ex_date)}, pagamento ${FMT.date(e.payment_date)})`);
    $("hm-detail").innerHTML = `
      <div class="card-head">
        <h2>${tickerIcon(d.ticker, 28)}${esc(d.ticker)} <span class="muted small">${company}</span></h2>
        <button id="hm-analyze" class="primary">Analisar travas de ${esc(d.ticker)}</button>
      </div>
      <p class="small">${sector ? `<b>Setor (B3):</b> ${sector}` : ""}${p.listing_segment ? ` · <b>Listagem:</b> ${esc(p.listing_segment)}` : ""}${p.website ? ` · <a href="https://${esc(p.website.replace(/^https?:\/\//, ""))}" target="_blank" rel="noopener noreferrer">${esc(p.website)}</a>` : ""}</p>
      ${p.activity ? `<p class="small muted">${esc(p.activity)}</p>` : ""}
      <div class="hm-detail-grid">
        <div><h3>Preço e variações</h3>${kv([
          ["Preço", `${FMT.price(m.price)}${m.last_bar_forming ? " (pregão em curso)" : ""}`],
          ["Dia (1 pregão)", `${signedPct(c["1d"].pct)} · ${FMT.ok(c["1d"].abs) ? FMT.price(c["1d"].abs) : "—"}`],
          ["Semana (5)", `${signedPct(c["1w"].pct)} · ${FMT.ok(c["1w"].abs) ? FMT.price(c["1w"].abs) : "—"}`],
          ["Mês (21)", `${signedPct(c["1m"].pct)} · ${FMT.ok(c["1m"].abs) ? FMT.price(c["1m"].abs) : "—"}`],
          ["Ano (252)", `${signedPct(c["1y"].pct)} · ${FMT.ok(c["1y"].abs) ? FMT.price(c["1y"].abs) : "—"}`],
          ["Volume hoje", `${compact(m.turnover_today)}${FMT.ok(m.turnover_ratio) ? ` (${FMT.num(m.turnover_ratio, 2)}× média)` : ""}`],
          ["Média 20 pregões", compact(m.turnover_avg20)],
          ["Negócios (sessão)", FMT.int(m.deals_session)],
          ["Valor de mercado (aprox.)", compact(d.market_cap_approx)],
        ])}</div>
        <div><h3>Volatilidade: implícita × histórica</h3>${kv([
          ["Histórica 20 pregões", FMT.pct(m.hv["20"])],
          ["Histórica 60 pregões", FMT.pct(m.hv["60"])],
          ["Histórica 252 pregões", FMT.pct(m.hv["252"])],
        ])}<div id="hm-iv" class="small"><p class="muted">Calculando IV ATM a partir da cadeia de opções…</p></div></div>
        <div><h3>Resumo técnico (D1) <span class="muted small">${bull} de ${signals.length} sinais de alta</span></h3>${kv([
          ["RSI 14", `${FMT.num(t.rsi14, 1)} · ${esc(t.rsi_label || "—")}`],
          ["EMA 17 × EMA 34", t.ema_trend ? `tendência de ${esc(t.ema_trend)} (${FMT.price(t.ema17)} × ${FMT.price(t.ema34)})` : "—"],
          ["Preço × SMA 50", `${ok(t.above_sma50)} (${FMT.price(t.sma50)})`],
          ["Preço × SMA 200", `${ok(t.above_sma200)} (${FMT.price(t.sma200)})`],
          ["Máxima 52 semanas", `${FMT.price(t.high52)} (${signedPct(t.from_high52_pct, 1)})`],
          ["Mínima 52 semanas", `${FMT.price(t.low52)} (${signedPct(t.from_low52_pct, 1)})`],
        ])}<p class="muted small">Calculado localmente com ${t.bars_used} barras diárias do MT5. Indicadores não são recomendação.</p></div>
      </div>
      <h3>Proventos em dinheiro <span class="muted small">(B3; data-com = último dia com direito)</span></h3>
      ${ev.available === false ? `<p class="muted small">${esc(ev.reason)}</p>` : `
        <p class="small">${upcoming.length ? `<b>Próximos:</b> ${upcoming.join("; ")}` : "Nenhum provento com data-com futura anunciado."}
        · Últimos 12 meses: ${FMT.num(ev.sum_last12m, 4)} por ação (${FMT.pct(ev.yield_last12m, 2)} do preço atual)</p>
        <div class="table-wrap"><table class="legs small"><thead><tr><th class="l">Tipo</th><th>Data-com</th><th>Pagamento</th><th>Valor/ação</th><th>% do preço atual</th></tr></thead><tbody>${cashRows || '<tr><td class="l" colspan="5">Sem registros</td></tr>'}</tbody></table></div>`}
      <h3>Eventos societários <span class="muted small">(desdobramentos, grupamentos, bonificações, subscrições)</span></h3>
      ${ev.available === false ? "" : `<div class="table-wrap"><table class="legs small"><thead><tr><th class="l">Evento</th><th>Data-com</th><th>Aprovação</th><th>Fator / %</th></tr></thead><tbody>${stockRows || '<tr><td class="l" colspan="4">Sem registros</td></tr>'}</tbody></table></div>`}
      <p class="muted small">${esc(d.mergers_note)} Dados de mercado: MT5 (${FMT.datetime(d.collected_at)}); cadastro e proventos: API pública da B3.</p>`;
    $("hm-analyze").addEventListener("click", () => App.analyzeTicker(d.ticker));
  }

  async function loadIv(ticker, d) {
    try {
      const iv = await api(`/api/heatmap/${encodeURIComponent(ticker)}/iv`);
      if (st.selected !== ticker || !$("hm-iv")) return;
      const hv20 = d.metrics.hv["20"];
      const rows = iv.atm_iv.map((r) => `<tr><td>${FMT.date(r.expiration)}</td><td>${r.dte_business_days}</td><td>${FMT.pct(r.atm_iv)}</td><td>${FMT.ok(hv20) && hv20 > 0 ? FMT.num(r.atm_iv / hv20, 2) + "×" : "—"}</td></tr>`).join("");
      $("hm-iv").innerHTML = (iv.warning ? `<div class="warn">${esc(iv.warning)}</div>` : "") +
        (rows ? `<table class="legs small"><thead><tr><th>Vencimento</th><th>du</th><th>IV ATM</th><th>IV ÷ HV20</th></tr></thead><tbody>${rows}</tbody></table>`
          : `<p class="muted">Sem IV ATM confiável (book largo ou sem opções perto do dinheiro).</p>`) +
        `<p class="muted small">${esc(iv.method)}</p>`;
    } catch (e) {
      if ($("hm-iv")) $("hm-iv").innerHTML = `<p class="neg">IV indisponível: ${esc(e.message)}</p>`;
    }
  }

  // ---------- integração ----------
  function setup() {
    if (st.ready) return;
    st.ready = true;
    document.querySelectorAll("#hm-metric button").forEach((b) => b.addEventListener("click", () => {
      st.metric = b.dataset.m;
      document.querySelectorAll("#hm-metric button").forEach((x) => x.classList.toggle("active", x === b));
      render(); App.savePrefs();
    }));
    $("hm-size").addEventListener("change", () => { st.size = $("hm-size").value; render(); App.savePrefs(); });
    $("hm-group").addEventListener("change", () => { st.group = $("hm-group").checked; render(); App.savePrefs(); });
    $("hm-refresh").addEventListener("click", load);
    $("hm-map").addEventListener("click", (ev) => {
      const tile = ev.target.closest(".hm-tile");
      if (tile) select(tile.dataset.t);
    });
    // Redesenha quando o CONTÊINER muda de tamanho (janela, divisória, barra de rolagem que surge).
    let raf = 0, lastW = 0, lastH = 0;
    new ResizeObserver(() => {
      const box = $("hm-map");
      if ($("tab-heatmap").hidden || (box.clientWidth === lastW && box.clientHeight === lastH)) return;
      lastW = box.clientWidth; lastH = box.clientHeight;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(render);
    }).observe($("hm-map"));
  }

  function activate() {
    setup();
    document.querySelectorAll("#hm-metric button").forEach((x) => x.classList.toggle("active", x.dataset.m === st.metric));
    $("hm-size").value = st.size;
    $("hm-group").checked = st.group;
    if (!st.data) load();
    else render();
  }

  const prefs = () => ({ metric: st.metric, size: st.size, group: st.group });
  function applyPrefs(p) {
    if (p.metric && METRICS[p.metric]) st.metric = p.metric;
    if (p.size) st.size = p.size;
    if (p.group !== undefined) st.group = !!p.group;
  }

  return { activate, prefs, applyPrefs, squarify };
})();
