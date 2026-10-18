// Aba Ativo protegido: collar e collar + borboleta (ativo + put + calls vendidas) com piso no
// vencimento ≥ custo. Todos os cálculos vêm da API Python; aqui só exibição.
const Protected = (() => {
  const $ = (id) => document.getElementById(id);
  // size: quantidade (mesma para todas) ou valor a investir (quantidade própria por estrutura).
  const st = { scan: null, detail: null, sort: null, underlying: null, spot: null, lot: 100, size: { mode: "qty" } };
  const api = (...a) => App.api(...a);
  const num = (id) => { const v = $(id).value; return v === "" ? null : Number(v); };

  const KIND_SHORT = { collar: "Collar", collar_borboleta: "Collar + borboleta" };
  const PREF_FIELDS = ["pr-underlying", "pr-dte_min", "pr-dte_max", "pr-quantity", "pr-amount", "pr-min_floor", "pr-costs", "pr-rate", "pr-aggr",
    "pr-max_spread", "pr-min_deals", "pr-min_turnover", "pr-max_age",
    "pr-w_floor", "pr-w_unchanged", "pr-w_max", "pr-w_prob_cdi", "pr-w_liquidity", "pr-w_execution_cost"];
  const CHECKS = ["pr-k-collar", "pr-k-fly", "pr-european", "pr-illiquid"];
  const WEIGHTS = ["floor", "unchanged", "max", "prob_cdi", "liquidity", "execution_cost"];
  const W_NAMES = { floor: "Piso", unchanged: "Ativo parado", max: "Máximo", prob_cdi: "Prob. > CDI", liquidity: "Liquidez", execution_cost: "Custo de execução" };
  const W_COLORS = { floor: "#157a3c", unchanged: "#1f5fbf", max: "#7a2fc0", prob_cdi: "#0e7c86", liquidity: "#e08a00", execution_cost: "#667085" };

  const retCell = (ret, pctCdi) => `<span class="${(ret ?? 0) >= 0 ? "pos" : "neg"}">${FMT.pct(ret, 2)}</span> <span class="muted">(${FMT.pct(pctCdi, 0)} CDI)</span>`;
  const styleTag = (leg) => {
    const eur = leg.exercise_style === "european";
    return ` <span class="style-tag ${eur ? "eur" : "amer"}" title="${eur ? "Europeia: só exerce no vencimento" : "Americana: pode ser exercida a qualquer momento"}">${eur ? "E" : "A"}</span>`;
  };
  const legCell = (leg) => leg ? `${leg.ratio > 1 ? `${leg.ratio}× ` : ""}${FMT.price(leg.strike)} <span class="muted">${esc(leg.symbol)}</span>${styleTag(leg)}` : "—";

  // ---------- quantidade x valor a investir ----------
  // Tudo por ação vem do scan (custo, piso, teto…); totais e retornos são refeitos aqui para a
  // quantidade escolhida, sem nova coleta. Custos fixos (R$) pesam menos com mais ações.
  const costsBrl = () => (st.scan ? st.scan.assumptions.costs_brl : num("pr-costs") || 0);

  function qtyFor(costPerShare) {
    if (st.size.mode === "amount") {
      const amount = num("pr-amount");
      if (amount === null || !(costPerShare > 0)) return null;
      return Math.max(0, Math.floor((amount - costsBrl()) / costPerShare / st.lot) * st.lot);
    }
    const q = num("pr-quantity");
    return q !== null && q > 0 ? Math.floor(q) : null;
  }

  // Quantidade enviada ao scan (afeta só o peso dos custos fixos no ranking).
  function scanQuantity() {
    if (st.size.mode === "qty") return qtyFor(null);
    const q = qtyFor(st.spot);
    return q > 0 ? q : null;
  }

  // Totais da estrutura `r` para a quantidade escolhida, com custo por ação `cost`.
  function sized(r, cost = r.cost_natural) {
    const q = qtyFor(cost) ?? r.quantity;
    const costs = costsBrl();
    const profit = (value) => (value - cost) * q - costs;
    const ret = (value) => (q > 0 && cost > 0 ? profit(value) / (cost * q) : null);
    const cdi = (x) => (x === null || !(r.cdi_period > 0) ? null : x / r.cdi_period);
    const z = {
      q, cost, invest: q * cost + costs,
      minProfit: profit(r.floor_value), maxProfit: profit(r.cap_value),
      floorRet: ret(r.floor_value), maxRet: ret(r.cap_value), unchangedRet: ret(r.unchanged_value),
      downRet: ret(r.low_tail_value), upRet: ret(r.high_tail_value),
      annual: (x) => (x === null || x <= -1 ? null : Math.pow(1 + x, 252 / r.dte_business_days) - 1),
    };
    return Object.assign(z, { floorCdi: cdi(z.floorRet), maxCdi: cdi(z.maxRet), unchangedCdi: cdi(z.unchangedRet) });
  }

  // Estrutura de referência para converter quantidade ↔ valor nos campos do formulário.
  function refStructure() {
    if (st.detail) return { cost: st.detail.cost_natural, label: "estrutura aberta" };
    if (st.scan && st.scan.results.length) return { cost: st.scan.results[0].cost_natural, label: "1ª do ranking" };
    if (FMT.ok(st.spot)) return { cost: st.spot, label: "preço do ativo (aprox., antes do scan)" };
    return null;
  }

  function syncSizeFields() {
    const ref = refStructure();
    const hint = [];
    if (ref) {
      if (st.size.mode === "qty") {
        const q = num("pr-quantity");
        $("pr-amount").value = q ? +(q * ref.cost + costsBrl()).toFixed(2) : "";
      } else {
        $("pr-quantity").value = qtyFor(ref.cost) ?? "";
      }
      hint.push(`Conversão pela ${ref.label}: ${FMT.price(ref.cost)} por ação${costsBrl() ? ` + custos de ${FMT.brl(costsBrl())}` : ""}.`);
    }
    if (st.size.mode === "amount") {
      hint.push(`Valor a investir: cada estrutura usa a maior quantidade múltipla de ${st.lot} que cabe no valor.`);
    } else if (num("pr-quantity") && num("pr-quantity") % st.lot) {
      hint.push(`Atenção: quantidade fora do lote de ${st.lot}.`);
    }
    $("pr-size-hint").textContent = hint.join(" ");
  }

  // Quantidade/valor mudou: refaz só a exibição (sem nova coleta nem novo scan).
  function onSizeInput(mode) {
    st.size.mode = mode;
    syncSizeFields();
    if (st.scan) { renderNote(); renderTable(); }
    if (st.detail) { st.detail._chart = null; renderSized(st.detail); }
    App.savePrefs();
  }

  // ---------- formulário ----------
  function applyDefaults(def) {
    const p = def.protected, lq = def.liquidity;
    st.lot = p.lot_size || 100;
    $("pr-quantity").step = st.lot;
    const base = {
      "pr-dte_min": p.dte_min_business_days, "pr-dte_max": p.dte_max_business_days, "pr-quantity": p.quantity,
      "pr-min_floor": p.min_floor_return * 100, "pr-rate": +(def.rate_annual * 100).toFixed(2), "pr-aggr": p.limit_aggressiveness * 100,
      "pr-max_spread": lq.max_spread_pct_mid * 100, "pr-min_deals": lq.min_deals, "pr-min_turnover": lq.min_turnover_brl,
      "pr-max_age": lq.max_quote_age_seconds,
    };
    for (const w of WEIGHTS) base[`pr-w_${w}`] = p.weights[w] * 100;
    for (const [k, v] of Object.entries(base)) $(k).value = +(+v).toFixed(4);
  }

  function payload() {
    const kinds = [];
    if ($("pr-k-collar").checked) kinds.push("collar");
    if ($("pr-k-fly").checked) kinds.push("collar_borboleta");
    const pct = (id) => { const v = num(id); return v === null ? null : v / 100; };
    const weights = {};
    for (const w of WEIGHTS) { const v = num(`pr-w_${w}`); if (v !== null) weights[w] = v; }
    return {
      underlying: $("pr-underlying").value.trim().toUpperCase(),
      kinds,
      dte_min: num("pr-dte_min"),
      dte_max: num("pr-dte_max"),
      quantity: scanQuantity(),
      rate_annual: pct("pr-rate"),
      costs_brl: num("pr-costs") || 0,
      min_floor_return: pct("pr-min_floor"),
      include_illiquid: $("pr-illiquid").checked,
      limit_aggressiveness: pct("pr-aggr"),
      liquidity: {
        max_spread_pct_mid: pct("pr-max_spread"),
        min_deals: num("pr-min_deals"),
        min_turnover_brl: num("pr-min_turnover"),
        max_quote_age_seconds: num("pr-max_age"),
      },
      weights: Object.keys(weights).length ? weights : null,
      refresh: $("pr-refresh").checked,
    };
  }

  async function onUnderlying() {
    const u = $("pr-underlying").value.trim().toUpperCase();
    if (!u || u === st.underlying) return;
    st.underlying = u;
    $("pr-underlying-icon").innerHTML = tickerIcon(u, 26);
    App.setLevels([], "protected");
    App.showUnderlying(u, "protected");
    $("pr-spot").textContent = "consultando…";
    try {
      const q = await api(`/api/quote/${encodeURIComponent(u)}`);
      st.spot = q.price;
      syncSizeFields();
      const origin = q.source === "ultimo_pregao" ? " (último pregão)" : q.source === "mt5_fora_pregao" ? " (MT5 fora do pregão)" : "";
      const book = FMT.ok(q.bid) && FMT.ok(q.ask) ? ` · bid ${FMT.price(q.bid)} / ask ${FMT.price(q.ask)}` : "";
      $("pr-spot").innerHTML = `${tickerIcon(u, 14)}Spot ${FMT.price(q.price)}${origin}${book} · ${FMT.datetime(q.quote_time)}`;
    } catch (e) {
      $("pr-spot").textContent = e.message;
    }
    App.savePrefs();
  }

  async function onSubmit(ev) {
    ev.preventDefault();
    const body = payload();
    const msg = $("pr-msg"), btn = $("pr-btn");
    if (!body.underlying) { msg.className = "msg err"; msg.textContent = "Informe o ativo."; return; }
    if (!body.kinds.length) { msg.className = "msg err"; msg.textContent = "Marque pelo menos uma estrutura."; return; }
    btn.disabled = true;
    msg.className = "msg";
    msg.textContent = "Coletando calls e puts no MT5 e combinando… (a primeira coleta pode levar até ~1 min)";
    const host = $("pr-results-card").hidden ? $("pr-title").closest(".card") : $("pr-results-card");
    Busy.show(host, "Coletando calls e puts no MT5 e combinando…");
    try {
      st.scan = await api("/api/protected/scan", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      st.sort = null;
      st.detail = null;
      $("pr-detail-card").hidden = true;
      msg.textContent = "";
      $("pr-refresh").checked = false;
      App.showUnderlying(st.scan.underlying, "protected");
      App.setLevels([{ label: "Atual", value: st.scan.spot, color: "#1d2330", size: 1 }], "protected");
      st.spot = st.scan.spot;
      renderResults();
      syncSizeFields();
      App.savePrefs();
    } catch (e) {
      msg.className = "msg err";
      msg.textContent = `Erro: ${e.message}`;
    } finally {
      Busy.hide(host);
      btn.disabled = false;
    }
  }

  // ---------- ranking ----------
  // Pacote de opções sem o ativo: débito (paga) ou crédito (recebe). A estrutura inteira é débito.
  const FLOW_WORD = { debito: "Débito", credito: "Crédito", zero: "Zero a zero" };
  function flowBadge(o, withTotal = null) {
    if (!o || !o.flow_natural) return "—";
    const cls = o.flow_natural === "credito" ? "ok" : o.flow_natural === "debito" ? "mid" : "";
    const total = withTotal ? ` · ${FMT.brl(Math.abs(o.net_natural) * withTotal)} no total` : "";
    const differs = o.flow_differs ? ` ⚠` : "";
    const tip = `Só as opções (put + calls), sem o ativo, por ação. Natural: ${FLOW_WORD[o.flow_natural].toLowerCase()} ${FMT.price(Math.abs(o.net_natural))}; mid: ${o.flow_mid ? `${FLOW_WORD[o.flow_mid].toLowerCase()} ${FMT.price(Math.abs(o.net_mid))}` : "—"}.${o.flow_differs ? " O sentido muda entre natural e mid: depende do preço de execução." : ""}`;
    return `<span class="badge ${cls}" title="${esc(tip)}">${FLOW_WORD[o.flow_natural]}${o.flow_natural === "zero" ? "" : ` ${FMT.price(Math.abs(o.net_natural))}`}${total}${differs}</span>`;
  }

  const sizeCell = (r) => { const z = sized(r); return `${FMT.int(z.q)} <span class="muted">· ${FMT.brl(z.invest)}</span>`; };
  const COLS = [
    { key: "rank", label: "#", val: (r) => r.rank, fmt: (r) => r.rank },
    { key: "score", label: "Score", val: (r) => r.score, fmt: (r) => `${FMT.num(r.score, 0)}${r.score_capped ? "*" : ""}` },
    { key: "kind", label: "Estrutura", l: true, val: (r) => r.kind, fmt: (r) => KIND_SHORT[r.kind] || r.kind },
    { key: "expiration", label: "Vencimento", l: true, val: (r) => r.expiration, fmt: (r) => `${FMT.date(r.expiration)} <span class="muted">(${r.dte_business_days} du)</span>` },
    { key: "put", label: "Put comprada", l: true, val: (r) => r.strikes.put, fmt: (r) => legCell(r.legs[0]) },
    { key: "short", label: "Call vendida", l: true, val: (r) => r.strikes.short_call, fmt: (r) => legCell(r.legs[1]) },
    { key: "long", label: "Call comprada", l: true, val: (r) => r.strikes.long_call, fmt: (r) => legCell(r.legs[2]) },
    { key: "size", label: "Qtd · investimento", tip: "Ações (= puts) e custo total da montagem, com os custos informados", val: (r) => sized(r).invest, fmt: sizeCell },
    { key: "flow", label: "Opções", tip: "Pacote de opções sem o ativo, por ação (natural): débito = você paga; crédito = você recebe. A operação completa (com a compra do ativo) é sempre débito. ⚠ = sentido diferente pelo mid.", val: (r) => (r.options ? -r.options.net_natural : null), fmt: (r) => flowBadge(r.options) },
    { key: "cost", label: "Custo/ação", tip: "Custo natural da montagem por ação: ativo e opções compradas no ask, calls vendidas no bid", val: (r) => r.cost_natural, fmt: (r) => FMT.price(r.cost_natural) },
    { key: "floor", label: "Piso", tip: "Retorno mínimo no vencimento (qualquer preço do ativo) e % do CDI do período", val: (r) => sized(r).floorCdi, fmt: (r) => { const z = sized(r); return retCell(z.floorRet, z.floorCdi); } },
    { key: "unchanged", label: "Ativo parado", tip: "Retorno no vencimento se o ativo terminar no preço atual", val: (r) => sized(r).unchangedCdi, fmt: (r) => { const z = sized(r); return retCell(z.unchangedRet, z.unchangedCdi); } },
    { key: "max", label: "Máximo", tip: "Retorno máximo no vencimento e preço do ativo onde ocorre", val: (r) => sized(r).maxCdi, fmt: (r) => { const z = sized(r); return `${retCell(z.maxRet, z.maxCdi)} <span class="muted">em ${FMT.price(r.cap_at)}</span>`; } },
    { key: "prob", label: "Prob. > CDI", tip: "Probabilidade de o resultado no vencimento superar o CDI do período (lognormal com IV ATM). Ver metodologia no detalhe.", val: (r) => r.prob_beat_cdi, fmt: (r) => FMT.pct(r.prob_beat_cdi, 0) },
    { key: "liq", label: "Liquidez", val: (r) => r.liquidity_score, fmt: (r) => liqBadge(r) },
    { key: "alerts", label: "Alertas", l: true, val: (r) => (r.early_exercise || "").startsWith("RISCO") ? 1 : 0, fmt: (r) => alertsCell(r) },
  ];

  function liqBadge(r) {
    if (!r.liquidity_ok) return `<span class="badge bad" title="${esc(r.data_flags.join(", "))}">reprovada</span>`;
    const s = r.liquidity_score;
    return s >= 0.6 ? `<span class="badge ok">boa ${FMT.num(s * 100, 0)}</span>` : `<span class="badge mid">média ${FMT.num(s * 100, 0)}</span>`;
  }
  function alertsCell(r) {
    const out = [];
    if (r.early_exercise && r.early_exercise.startsWith("RISCO")) out.push(`<span class="badge bad" title="${esc(r.early_exercise)}">exercício antecipado</span>`);
    if (r.data_flags.length) out.push(`<span class="badge mid" title="${esc(r.data_flags.join(", "))}">dados</span>`);
    return out.join(" ");
  }

  function renderResults() {
    const a = st.scan;
    $("pr-results-card").hidden = false;
    const c = a.collection || {};
    const s = a.stock;
    $("pr-results-meta").innerHTML = `${tickerIcon(a.underlying, 18)}${esc(a.underlying)} · spot ${FMT.price(a.spot)} · compra do ativo ${FMT.price(s.entry)}${FMT.ok(s.ask) ? " (ask)" : " (último)"} · coleta ${FMT.datetime(c.collected_at)}${c.from_cache ? " (cache)" : FMT.ok(c.duration_seconds) ? ` em ${FMT.num(c.duration_seconds, 0)} s` : ""}${FMT.ok(c.series) ? ` · ${c.series} séries (${c.series_with_book} com book)` : ""}`;
    const warns = [c.realtime_warning, ...(s.flags || [])].filter(Boolean);
    $("pr-warning").hidden = !warns.length;
    $("pr-warning").textContent = warns.length ? `Atenção: ${warns.join("; ")}.` : "";
    const disc = Object.entries(a.discarded).map(([k, v]) => `${esc(k)}: ${FMT.int(v)}`).join(" · ");
    const style = a.assumptions.exercise_style_filter.length ? `<div class="small"><b>Estilo de exercício:</b> ${esc(a.assumptions.exercise_style_filter.join(" e "))}</div>` : "";
    const eur = $("pr-european").checked;
    const total = eur ? a.total_european_short : a.total_ranked;
    const shown = visibleRows().length;
    const count = eur
      ? `${FMT.int(total)} de ${FMT.int(a.total_ranked)} estruturas com piso ≥ custo têm call vendida europeia`
      : `${FMT.int(total)} estruturas com piso ≥ custo (${FMT.int(a.total_european_short)} com call vendida europeia)`;
    $("pr-discarded").innerHTML = style + count + (shown < total ? ` · exibindo as ${FMT.int(shown)} melhores` : "") +
      (disc ? ` · descartadas — ${disc}` : "") +
      (a.atm_iv.length ? ` · IV ATM: ${a.atm_iv.map((x) => `${FMT.date(x.expiration)} ${FMT.pct(x.atm_iv)}`).join(", ")}` : " · sem IV ATM confiável (probabilidade indisponível)");
    renderNote();
    renderTable();
    if (!shown) {
      $("pr-table").querySelector("tbody").innerHTML = `<tr><td class="l" colspan="${COLS.length}">${a.total_ranked && eur
        ? "Nenhuma estrutura com call vendida europeia. Desmarque \"só europeia\" para ver as demais (com risco de exercício antecipado)."
        : "Nenhuma estrutura com piso ≥ custo nos filtros. Com preços de mercado justos isso é comum: tente prazos mais longos, inclua as ilíquidas ou reduza o piso mínimo."}</td></tr>`;
    }
  }

  // Filtro de estilo só na exibição: sem filtro, as `max_results` melhores no geral; com filtro,
  // as melhores com call vendida europeia (a API devolve as duas listas juntas).
  function visibleRows() {
    const a = st.scan;
    if ($("pr-european").checked) return a.results.filter((r) => r.legs[1].exercise_style === "european").slice(0, a.max_results);
    return a.results.slice(0, a.max_results);
  }

  function renderNote() {
    const a = st.scan.assumptions;
    const qty = st.size.mode === "amount"
      ? `a quantidade que cabe em ${FMT.brl(num("pr-amount"))} (por estrutura)`
      : `${FMT.int(qtyFor(null) ?? a.quantity)} ações`;
    const costsNote = a.costs_brl
      ? ` O score foi calculado no scan com ${FMT.int(a.quantity)} ações; com custos fixos, mudar a quantidade altera os retornos exibidos, não a ordem do score.`
      : "";
    $("pr-note").textContent = `${a.ranking_note} * = score limitado por liquidez/cotação. Retornos no vencimento para ${qty}, já descontados custos de ${FMT.brl(a.costs_brl)}.${costsNote} ${a.cdi_note}.`;
  }

  function renderTable() {
    const rows = visibleRows();
    if (st.sort) {
      const col = COLS.find((c) => c.key === st.sort.key);
      rows.sort((x, y) => {
        const vx = col.val(x), vy = col.val(y);
        if (vx === null || vx === undefined) return 1;
        if (vy === null || vy === undefined) return -1;
        return (vx > vy ? 1 : vx < vy ? -1 : 0) * st.sort.dir;
      });
    }
    $("pr-table").querySelector("thead").innerHTML = "<tr>" + COLS.map((c) => {
      const cls = ["sortable", c.l ? "l" : "", st.sort && st.sort.key === c.key ? (st.sort.dir > 0 ? "sorted-asc" : "sorted-desc") : ""].join(" ");
      return `<th class="${cls}" data-key="${c.key}" ${c.tip ? `title="${esc(c.tip)}"` : ""}>${c.label}</th>`;
    }).join("") + "</tr>";
    $("pr-table").querySelector("tbody").innerHTML = rows.map((r) =>
      `<tr data-id="${esc(r.id)}" class="${r.liquidity_ok ? "" : "illiquid"} ${st.detail && st.detail.id === r.id ? "selected" : ""}">` +
      COLS.map((c) => `<td class="${c.l ? "l" : ""}">${c.fmt(r)}</td>`).join("") + "</tr>").join("");
  }

  function onHeaderClick(ev) {
    const th = ev.target.closest("th[data-key]");
    if (!th) return;
    const key = th.dataset.key;
    const ascDefault = ["rank", "expiration", "cost", "kind", "put", "short", "long"].includes(key) ? 1 : -1;
    st.sort = st.sort && st.sort.key === key ? { key, dir: -st.sort.dir } : { key, dir: ascDefault };
    renderTable();
  }

  async function onRowClick(ev) {
    const tr = ev.target.closest("tr[data-id]");
    if (!tr) return;
    const host = $("pr-detail-card").hidden ? $("pr-results-card") : $("pr-detail-card");
    Busy.show(host, "Abrindo a estrutura…");
    try {
      st.detail = await api(`/api/protected/detail/${st.scan.scan_id}/${encodeURIComponent(tr.dataset.id)}`);
      renderTable();
      renderDetail();
      $("pr-detail-card").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
      $("pr-msg").className = "msg err";
      $("pr-msg").textContent = `Erro ao abrir a estrutura: ${e.message}`;
    } finally {
      Busy.hide(host);
    }
  }

  // ---------- detalhe ----------
  function renderDetail() {
    const d = st.detail;
    $("pr-detail-card").hidden = false;
    const k = d.strikes;
    const desc = d.kind === "collar"
      ? `put ${FMT.price(k.put)} · call vendida ${FMT.price(k.short_call)}`
      : `put ${FMT.price(k.put)} · 2 calls vendidas ${FMT.price(k.short_call)} · call comprada ${FMT.price(k.long_call)}`;
    $("pr-detail-title").innerHTML = `${tickerIcon(st.scan.underlying, 24)}${esc(KIND_SHORT[d.kind])}: ${esc(st.scan.underlying)} + ${esc(desc)}`;
    syncSizeFields();
    const alerts = [];
    if (d.collection && d.collection.realtime_warning) alerts.push(`<div class="warn">${esc(d.collection.realtime_warning)}</div>`);
    if (!d.liquidity_ok) alerts.push(`<div class="warn">Liquidez/cotação reprovada: ${esc(d.data_flags.join(", "))}. Preços podem não ser executáveis.</div>`);
    if (d.early_exercise) alerts.push(`<div class="warn ${d.early_exercise.startsWith("RISCO") ? "alert-risk" : ""}">Call vendida: ${esc(d.early_exercise)}</div>`);
    for (const w of d.stock_leg.flags || []) alerts.push(`<div class="warn">${esc(w)}</div>`);
    for (const w of d.warnings || []) alerts.push(`<div class="warn">${esc(w)}</div>`);
    $("pr-alerts").innerHTML = alerts.join("");
    renderScore(d);
    renderAssumptions(d);
    setupSlider(d);
    renderSized(d);
  }

  // Partes do detalhe que dependem da quantidade (refeitas ao mudar quantidade ou valor).
  // Alerta em destaque: o pacote de opções sai a débito ou a crédito (a operação toda é débito).
  function renderFlow(d, q) {
    const o = d.options;
    if (!o || !o.flow_natural) { $("pr-flow").innerHTML = ""; return; }
    const s = d.stock_leg.entry;
    const amount = FMT.price(Math.abs(o.net_natural));
    const total = FMT.brl(Math.abs(o.net_natural) * q);
    const what = {
      credito: `<b>Opções a CRÉDITO:</b> as calls vendidas pagam a put e ainda sobram <b>${amount}</b> por ação (${total} recebidos nas ${FMT.int(q)} ações).`,
      debito: `<b>Opções a DÉBITO:</b> a put custa mais do que as calls vendidas rendem — você paga <b>${amount}</b> por ação (${total}) além do ativo.`,
      zero: `<b>Opções no zero a zero:</b> as calls vendidas pagam a put (diferença menor que meio centavo por ação).`,
    }[o.flow_natural];
    const differs = o.flow_differs
      ? `<br><b>Atenção:</b> pelo mid o pacote sai a ${FLOW_WORD[o.flow_mid].toLowerCase()} (${FMT.price(Math.abs(o.net_mid))}); o sentido depende do preço que você conseguir executar.`
      : "";
    const cls = o.flow_natural === "credito" ? "flow-credit" : o.flow_natural === "debito" ? "flow-debit" : "";
    $("pr-flow").innerHTML = `<div class="warn flow-box ${cls}">${what}
      A operação completa é <b>DÉBITO</b>: ativo ${FMT.price(s)} ${o.net_natural < 0 ? "−" : "+"} opções ${amount} = <b>${FMT.price(d.cost_natural)}</b> por ação.${differs}</div>`;
  }

  function renderSized(d) {
    const z = sized(d);
    $("pr-detail-sub").textContent = `Vencimento ${FMT.date(d.expiration)} · ${d.dte_business_days} dias úteis (${d.dte_calendar_days} corridos) · ${FMT.int(z.q)} ações · investimento ${FMT.brl(z.invest)}`;
    renderFlow(d, z.q);
    renderLimit(d);
    renderMetrics(d);
    renderLegs(d);
    draw();
  }

  function renderLimit(d) {
    const l = d.limit;
    const imp = l.impacts;
    // Mesma quantidade da estrutura (pelo custo natural); muda só o preço de entrada.
    const q = sized(d).q, costs = costsBrl();
    const line = (name, label) => {
      if (!imp[name]) return "";
      const price = imp[name].price;
      const profit = (v) => (v - price) * q - costs;
      return `<tr><td class="l">${label}</td><td>${FMT.price(price)}</td><td>${FMT.pct(profit(d.floor_value) / (price * q), 2)}</td><td>${FMT.pct(profit(d.cap_value) / (price * q), 2)}</td><td>${FMT.signedBrl(profit(d.floor_value))}</td><td>${FMT.signedBrl(profit(d.cap_value))}</td></tr>`;
    };
    $("pr-limit").innerHTML = `<div class="limit-box">
      <div class="muted small">Custo líquido por ação da montagem completa (DÉBITO: ativo + opções), para conferir no ProfitChart (ordem manual)</div>
      <div class="limit-main">${FMT.price(l.suggested)}</div>
      <div class="small">Faixa indicativa: ${FMT.price(l.range_low)} – ${FMT.price(l.range_high)} (mid ↔ natural) · custo máximo que mantém o piso: <b>${FMT.price(l.max_cost)}</b></div>
      <div class="small muted">Dados de ${FMT.datetime(d.collection && d.collection.collected_at)}. ${l.notes.map(esc).join("; ")}.</div>
      </div>
      <div class="table-wrap"><table class="legs small"><thead><tr><th class="l">Custo usado</th><th>Por ação</th><th>Piso</th><th>Máximo</th><th>Lucro mín.</th><th>Lucro máx.</th></tr></thead>
      <tbody>${line("sugerido", "Sugerido")}${line("mid", "Mid")}${line("natural", "Natural")}${line("custo_max", "Custo máx. (piso = custo)")}</tbody></table></div>`;
  }

  function renderMetrics(d) {
    const fly = d.kind === "collar_borboleta";
    const z = sized(d);
    const items = [
      ["Custo natural por ação", FMT.price(d.cost_natural)],
      ["Custo mid por ação", FMT.price(d.cost_mid)],
      ["Opções sem o ativo (por ação)", flowBadge(d.options)],
      [`Investimento total (${FMT.int(z.q)} ações, com custos)`, FMT.brl(z.invest)],
      ["CDI no período", `${FMT.pct(d.cdi_period, 2)} <span class="muted">(${d.dte_business_days} du)</span>`],
      ["Piso (pior caso)", `${FMT.price(d.floor_value)} → ${retCell(z.floorRet, z.floorCdi)}`],
      ["Piso anualizado", FMT.pct(z.annual(z.floorRet), 2)],
      [`Queda forte (abaixo de ${FMT.price(d.strikes.put)})`, `${FMT.price(d.low_tail_value)} → ${FMT.pct(z.downRet, 2)}`],
      [`Ativo parado (${FMT.price(st.scan.spot)})`, retCell(z.unchangedRet, z.unchangedCdi)],
      [`Máximo (ativo em ${FMT.price(d.cap_at)})`, `${FMT.price(d.cap_value)} → ${retCell(z.maxRet, z.maxCdi)}`],
      ["Máximo anualizado", FMT.pct(z.annual(z.maxRet), 2)],
      [fly ? `Alta forte (acima de ${FMT.price(d.strikes.long_call)})` : `Alta (acima de ${FMT.price(d.strikes.short_call)})`, `${FMT.price(d.high_tail_value)} → ${FMT.pct(z.upRet, 2)}`],
      ["Lucro mínimo (total)", `<span class="${z.minProfit >= 0 ? "pos" : "neg"}">${FMT.signedBrl(z.minProfit)}</span>`],
      ["Lucro máximo (total)", `<span class="pos">${FMT.signedBrl(z.maxProfit)}</span>`],
      ["Prob. de superar o CDI", d.prob_beat_cdi === null ? `indisponível (${esc(d.prob_unavailable_reason)})` : `<span title="${esc(d.prob_method)}">${FMT.pct(d.prob_beat_cdi, 0)}</span>`],
      ["Custo de execução (natural − mid)", `${FMT.pct(d.execution_cost_pct_profit, 1)} do lucro máx.`],
    ];
    $("pr-metrics").innerHTML = items.map(([k, v]) => `<div><span>${k}</span><span>${v}</span></div>`).join("");
  }

  function renderLegs(d) {
    const s = d.stock_leg;
    const q = sized(d).q;
    const stockRow = `<tr><td class="l">Compra</td><td class="l">${esc(s.symbol)}</td><td class="l">ativo</td><td>${FMT.int(q)} ações</td><td>—</td>
      <td>${FMT.price(s.bid)}</td><td>${FMT.price(s.ask)}</td><td>${FMT.price(s.mid)}</td><td>${FMT.price(s.last)}</td><td>—</td><td>—</td><td>—</td>
      <td>${FMT.datetime(s.quote_time)}</td><td>—</td>
      <td class="l">${s.flags.length ? `<span class="badge mid">${esc(s.flags.join(", "))}</span>` : '<span class="badge ok">ok</span>'}</td></tr>`;
    const rows = d.legs.map((l) => `<tr>
      <td class="l">${l.side === "compra" ? "Compra" : "Venda"}</td><td class="l">${esc(l.symbol)}</td><td class="l">${l.option_type} ${l.exercise_style === "american" ? "americana" : "europeia"}</td>
      <td>${FMT.int((l.contracts * q) / d.quantity)} opções${l.ratio > 1 ? ` <span class="muted">(${l.ratio}× por ação)</span>` : ""}</td>
      <td>${FMT.price(l.strike)}</td><td>${FMT.price(l.bid)}</td><td>${FMT.price(l.ask)}</td><td>${FMT.price(l.mid)}</td><td>${FMT.price(l.last)}</td>
      <td>${FMT.pct(l.spread_pct_mid)}</td><td title="${esc(l.volume_source || "")}">${FMT.int(l.deals)}${l.volume_source === "barra D1" ? "*" : ""}</td><td title="${esc(l.volume_source || "")}">${FMT.brl(l.turnover_brl)}${l.volume_source === "barra D1" ? "*" : ""}</td>
      <td>${FMT.datetime(l.quote_time)} <span class="muted">(${FMT.age(l.quote_age_seconds)})</span></td>
      <td title="${esc(l.iv_status)}">${FMT.pct(l.iv)}</td>
      <td class="l">${l.flags.length ? `<span class="badge bad">${esc(l.flags.join(", "))}</span>` : '<span class="badge ok">ok</span>'}${l.ref_note ? ` <span class="badge mid" title="${esc(l.ref_note)}">dado corrigido (B3)</span>` : ""}</td></tr>`).join("");
    $("pr-legs").innerHTML = `<thead><tr><th class="l">Lado</th><th class="l">Ticker</th><th class="l">Tipo</th><th>Quantidade</th><th>Strike</th><th>Bid</th><th>Ask</th><th>Mid</th><th>Último</th><th>Spread</th><th>Negócios</th><th>Volume R$</th><th>Último tick</th><th>IV</th><th class="l">Qualidade</th></tr></thead><tbody>${stockRow}${rows}</tbody>`;
  }

  function renderScore(d) {
    const row = st.scan.results.find((r) => r.id === d.id);
    const comps = row && row.score_components;
    if (!comps) { $("pr-score").innerHTML = '<span class="muted">Score disponível na lista ranqueada.</span>'; return; }
    const bar = Object.entries(comps).map(([k, c]) => c.percentile === null ? "" : `<span style="width:${c.effective_weight * c.percentile * 100}%;background:${W_COLORS[k]}" title="${W_NAMES[k]}"></span>`).join("");
    const table = Object.entries(comps).map(([k, c]) => `<tr><td class="l"><i style="display:inline-block;width:10px;height:10px;background:${W_COLORS[k]}"></i> ${W_NAMES[k]}</td><td class="l muted">${esc(c.description)}</td><td>${FMT.pct(c.weight, 0)}</td><td>${FMT.pct(c.effective_weight, 0)}</td><td>${c.percentile === null ? "indisponível" : FMT.pct(c.percentile, 0)}</td></tr>`).join("");
    $("pr-score").innerHTML = `<div><b>Score ${FMT.num(row.score, 0)}</b>${row.score_capped ? " (limitado por liquidez)" : ""}</div><div class="score-bar">${bar}</div>
      <div class="table-wrap"><table class="legs small"><thead><tr><th class="l">Critério</th><th class="l">Medida</th><th>Peso</th><th>Peso efetivo</th><th>Percentil</th></tr></thead><tbody>${table}</tbody></table></div>`;
  }

  function renderAssumptions(d) {
    const a = d.assumptions;
    const items = [
      `"Risco zero" aqui significa: ${a.risk_zero_definition}.`,
      `Custo calculado pelo ${a.entry_basis}. Mid é só referência.`,
      `${a.cdi_note}. Juros/CDI usados: ${FMT.pct(a.rate_annual, 2)} a.a. Custos considerados: ${FMT.brl(a.costs_brl)}.`,
      d.prob_method ? `Probabilidade: ${d.prob_method}. Não é garantia de resultado.` : `Probabilidade indisponível: ${d.prob_unavailable_reason}.`,
      d.simulation.assumptions,
      ...a.notes,
      `Open interest não disponível no MT5; volume e negócios não equivalem a contratos em aberto.`,
    ];
    $("pr-assumptions").innerHTML = items.map((t) => `<li>${esc(t)}</li>`).join("");
  }

  function setupSlider(d) {
    const sim = d.simulation;
    $("pr-sim-note").textContent = sim.model_available ? sim.assumptions : `Simulação temporal indisponível: ${sim.model_reason}. Exibindo só o payoff no vencimento.`;
    $("pr-time").hidden = !sim.model_available;
    $("pr-slider").max = Math.max(0, sim.dates.length - 1);
    $("pr-slider").value = 0; // o desenho vem em renderSized
  }

  // Objeto no formato que o Payoff.render espera (mesmo gráfico da aba Análise).
  // Cruzamentos com zero por interpolação linear (equilíbrio na data simulada).
  function zeroCrossings(xs, ys) {
    const out = [];
    for (let i = 0; i < xs.length - 1; i++) {
      const a = ys[i], b = ys[i + 1];
      if (a === 0) out.push(xs[i]);
      else if (a * b < 0) out.push(xs[i] + (xs[i + 1] - xs[i]) * (-a / (b - a)));
    }
    return out;
  }

  // Curvas do scan (quantidade-base) reescaladas: P&L(q) = (P&L(base) + custos) × q ÷ base − custos.
  function scaledSimulation(d) {
    const base = d.quantity, q = sized(d).q, costs = costsBrl();
    const f = (y) => ((y + costs) * q) / base - costs;
    const sim = d.simulation;
    const expiry = sim.expiry_pnl.map(f);
    return {
      ...sim,
      expiry_pnl: expiry,
      expiry_breakevens: zeroCrossings(sim.spots, expiry),
      dates: sim.dates.map((day) => { const pnl = day.pnl.map(f); return { ...day, pnl, breakevens: zeroCrossings(sim.spots, pnl) }; }),
    };
  }

  function chartData(d) {
    const sim = scaledSimulation(d);
    const z = sized(d);
    return {
      simulation: sim,
      legs: d.legs.map((l) => ({ strike: l.strike, side: l.side })),
      breakevens: sim.expiry_breakevens,
      spot: d.spot,
      target_price: null,
      max_profit: z.maxProfit,
      max_loss: z.minProfit < 0 ? -z.minProfit : null,
      min_profit: z.minProfit >= 0 ? z.minProfit : null,
    };
  }

  function draw() {
    const d = st.detail;
    if (!d || $("tab-protected").hidden) return;
    if (!d._chart) d._chart = chartData(d);
    const sim = d._chart.simulation;
    const i = Number($("pr-slider").value);
    const sel = sim.dates[i];
    const showModel = sel && sel.business_days_left > 0;
    $("pr-time-label").textContent = sel ? `${FMT.date(sel.date)} · ${sel.business_days_left} du até o vencimento${sel.business_days_left === 0 ? " (payoff exato)" : " (modelo)"}` : "";
    $("pr-legend").innerHTML = Payoff.legend(showModel, sel, sim.expiry_label);
    Payoff.render($("pr-payoff"), d._chart, i, App.tooltip());
    const k = d.strikes;
    const levels = [
      { label: "Atual", value: d.spot, color: "#1d2330", size: 1 },
      { label: "Put (piso)", value: k.put, color: "#157a3c", dashed: true, size: 1.6, fit: true },
      { label: d.kind === "collar" ? "Call vendida (teto)" : "Calls vendidas (máximo)", value: k.short_call, color: "#7a2fc0", dashed: true, size: 1.6, fit: true },
      ...(k.long_call ? [{ label: "Call comprada", value: k.long_call, color: "#98a2b3", dashed: true, dash: [2, 4], fit: true }] : []),
      ...(showModel ? sel.breakevens.map((b) => ({ label: `Equil. ${FMT.date(sel.date)}`, value: b, color: "#1f5fbf", dashed: true, dash: [2, 3] })) : []),
    ];
    App.setLevels(levels, "protected");
  }

  // ---------- preferências ----------
  function prefs() {
    const out = {};
    for (const f of PREF_FIELDS) out[f] = $(f).value;
    for (const c of CHECKS) out[c] = $(c).checked;
    out.size_mode = st.size.mode;
    return out;
  }

  function applyPrefs(p) {
    if (!p) return;
    for (const f of PREF_FIELDS) if (p[f] !== undefined && p[f] !== "") $(f).value = p[f];
    for (const c of CHECKS) if (typeof p[c] === "boolean") $(c).checked = p[c];
    if (p.size_mode === "amount" || p.size_mode === "qty") st.size.mode = p.size_mode;
  }

  function activate() {
    const u = $("pr-underlying").value.trim().toUpperCase();
    if (u && u !== st.underlying) onUnderlying();
    else if (st.detail) requestAnimationFrame(draw);
  }

  function init(def, savedPrefs) {
    applyDefaults(def);
    applyPrefs(savedPrefs);
    $("pr-form").addEventListener("submit", onSubmit);
    $("pr-form").addEventListener("change", () => App.savePrefs());
    $("pr-quantity").addEventListener("input", () => onSizeInput("qty"));
    $("pr-amount").addEventListener("input", () => onSizeInput("amount"));
    $("pr-costs").addEventListener("input", syncSizeFields);
    $("pr-european").addEventListener("change", () => { if (st.scan) renderResults(); });
    syncSizeFields();
    $("pr-underlying").addEventListener("change", onUnderlying);
    $("pr-table").querySelector("thead").addEventListener("click", onHeaderClick);
    $("pr-table").querySelector("tbody").addEventListener("click", onRowClick);
    let raf = 0;
    $("pr-slider").addEventListener("input", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(draw); });
    $("pr-max").addEventListener("click", () => App.toggleMax($("pr-payoff-wrap"), $("pr-max"), draw));
    window.addEventListener("resize", () => { if (st.detail) draw(); });
  }

  return { init, activate, prefs, redraw: draw };
})();
