// Aba Simulador: monta qualquer estrutura (opções e o próprio ativo) de um ativo-objeto e simula
// payoff, passagem do tempo, saída e garantia. Todos os cálculos vêm da API Python.
const Simulator = (() => {
  const $ = (id) => document.getElementById(id);
  const api = (...a) => App.api(...a);
  const num = (id) => { const v = $(id).value; return v === "" ? null : Number(v); };
  const st = { underlying: null, spot: null, options: [], byId: {}, exp: null, chain: null, legs: [], result: null, token: 0, timer: null, centered: false };
  const PREF_FIELDS = ["sm-underlying", "sm-qty", "sm-target", "sm-vol", "sm-rate", "sm-costs"];

  // ---------- ativo e vencimentos ----------
  async function onUnderlying(force = false) {
    const u = $("sm-underlying").value.trim().toUpperCase();
    if (!u || (u === st.underlying && !force)) return;
    const changed = st.underlying && st.underlying !== u;
    st.underlying = u;
    $("sm-underlying-icon").innerHTML = tickerIcon(u, 26);
    App.setLevels([], "simulator");
    App.showUnderlying(u, "simulator");
    if (changed) { st.legs = []; st.result = null; $("sm-result").hidden = true; renderLegs(); }
    $("sm-spot").textContent = "consultando…";
    try {
      const [q, opts] = await Promise.all([
        api(`/api/quote/${encodeURIComponent(u)}`),
        api(`/api/options/${encodeURIComponent(u)}`),
      ]);
      st.spot = q.price;
      const origin = FMT.origin(q.source);
      $("sm-spot").innerHTML = `${tickerIcon(u, 14)}Spot ${FMT.price(q.price)}${origin} · ${FMT.datetime(q.quote_time)}`;
      st.options = opts;
      st.byId = Object.fromEntries(opts.map((o) => [o.symbol, o]));
      $("sm-opts").innerHTML = opts.map((o) => `<option value="${esc(o.symbol)}">${o.option_type} ${FMT.price(o.strike)} · ${FMT.date(o.expiration_date)} · ${o.exercise_style === "american" ? "amer." : "eur."}</option>`).join("");
      const exps = [...new Set(opts.map((o) => o.expiration_date))].sort();
      $("sm-exp").innerHTML = exps.map((e) => `<option value="${e}">${FMT.date(e)}</option>`).join("");
      if (!exps.includes(st.exp)) st.exp = exps[0] || null;
      $("sm-exp").value = st.exp || "";
      st.centered = false;
      await loadChain(false);
      if (st.legs.length) schedule(0);
    } catch (e) {
      $("sm-spot").textContent = e.message;
    }
    App.savePrefs();
  }

  // ---------- grade do vencimento ----------
  async function loadChain(refresh) {
    if (!st.underlying || !st.exp) { st.chain = null; renderChain(); return; }
    const host = $("sm-chain-host");
    Busy.show(host, "Lendo as cotações do vencimento…");
    try {
      st.chain = await api(`/api/simulator/chain/${encodeURIComponent(st.underlying)}?expiration=${st.exp}${refresh ? "&refresh=true" : ""}`);
      if (FMT.ok(st.chain.spot)) st.spot = st.chain.spot;
      const m = st.chain.market;
      $("sm-chain-meta").textContent = `lida ${FMT.datetime(st.chain.read_at)}${m && !m.is_open ? " · mercado fechado: últimas cotações do pregão" : ""}`;
    } catch (e) {
      st.chain = null;
      $("sm-chain-meta").textContent = `Grade indisponível: ${e.message}`;
    } finally {
      Busy.hide(host);
    }
    renderChain();
  }

  // Quantidade líquida já montada em cada série (positivo = comprado), para marcar na grade.
  function netBySymbol() {
    const out = {};
    for (const l of st.legs) if (l.kind === "opcao") out[l.symbol] = (out[l.symbol] || 0) + (l.side === "compra" ? 1 : -1) * l.quantity;
    return out;
  }

  function renderChain() {
    const table = $("sm-chain");
    if (!st.chain || !st.chain.rows.length) {
      table.querySelector("thead").innerHTML = "";
      table.querySelector("tbody").innerHTML = `<tr><td class="muted l">${st.underlying ? "Sem opções neste vencimento." : "Escolha o ativo-objeto."}</td></tr>`;
      return;
    }
    const byStrike = new Map();
    for (const r of st.chain.rows) {
      if (!byStrike.has(r.strike)) byStrike.set(r.strike, {});
      byStrike.get(r.strike)[r.option_type] = r;
    }
    const strikes = [...byStrike.keys()].sort((a, b) => a - b);
    const atm = strikes.reduce((best, k) => (Math.abs(k - st.spot) < Math.abs(best - st.spot) ? k : best), strikes[0]);
    const net = netBySymbol();
    // Dentro do dinheiro (ITM) com fundo leve, para orientar a leitura.
    const cell = (r, itm) => {
      const c = itm ? "sm-itm" : "";
      if (!r) return `<td colspan="3" class="muted ${c}">—</td><td class="${c}"></td><td class="sm-pos ${c}"></td>`;
      const bad = r.flags && r.flags.length;
      const pos = net[r.symbol];
      const mark = pos ? `<span class="badge ${pos > 0 ? "ok" : "bad"}" title="Posição montada nesta série">${pos > 0 ? "+" : ""}${FMT.int(pos)}</span>` : "";
      const q = `${c}${bad ? " muted" : ""}`;
      // Fechamento da B3: sem bid/ask; mostra o último negócio do pregão nas duas colunas.
      const book = r.price_basis === "ultimo_b3"
        ? `<td colspan="2" class="${q}" title="${esc(r.symbol)} · último negócio do pregão (fechamento B3), indicativo${bad ? ` · ${esc(r.flags.join(", "))}` : ""}">últ. ${FMT.price(r.last)}</td>`
        : `<td class="${q}" title="${esc(r.symbol)}${bad ? ` · ${esc(r.flags.join(", "))}` : ""}">${FMT.price(r.bid)}</td><td class="${q}">${FMT.price(r.ask)}</td>`;
      return `${book}<td class="${c} muted">${FMT.pct(r.iv, 0)}</td>
        <td class="sm-act ${c}"><button type="button" class="sm-b" data-sym="${esc(r.symbol)}" data-side="compra" title="Comprar ${esc(r.symbol)}">C</button><button type="button" class="sm-s" data-sym="${esc(r.symbol)}" data-side="venda" title="Vender ${esc(r.symbol)}">V</button></td><td class="sm-pos ${c}">${mark}</td>`;
    };
    table.querySelector("thead").innerHTML = `<tr><th colspan="5" class="sm-side-h">Calls</th><th></th><th colspan="5" class="sm-side-h">Puts</th></tr>
      <tr><th>Bid</th><th>Ask</th><th>IV</th><th></th><th></th><th>Strike</th><th>Bid</th><th>Ask</th><th>IV</th><th></th><th></th></tr>`;
    table.querySelector("tbody").innerHTML = strikes.map((k) => {
      const row = byStrike.get(k);
      return `<tr class="${k === atm ? "sm-atm" : ""}">${cell(row.call, k < st.spot)}<th class="sm-strike">${FMT.price(k)}${k === atm ? ' <span class="muted small">ATM</span>' : ""}</th>${cell(row.put, k > st.spot)}</tr>`;
    }).join("");
    if (!st.centered) {
      const atmRow = table.querySelector("tr.sm-atm");
      const scroller = table.closest(".sm-chain-scroll");
      if (atmRow && scroller) scroller.scrollTop = atmRow.offsetTop - scroller.clientHeight / 2;
      st.centered = true;
    }
  }

  // ---------- pernas ----------
  // Mesma série e lado: soma a quantidade; lado oposto: reduz (zerou, sai).
  function addLeg(leg) {
    const same = st.legs.find((l) => l.kind === leg.kind && (l.kind === "ativo" || l.symbol === leg.symbol));
    if (same && same.side === leg.side) same.quantity += leg.quantity;
    else if (same) {
      same.quantity -= leg.quantity;
      if (same.quantity === 0) st.legs.splice(st.legs.indexOf(same), 1);
      else if (same.quantity < 0) { same.quantity = -same.quantity; same.side = leg.side; same.price = null; }
    } else st.legs.push(leg);
    afterLegsChange();
  }

  function addOption(symbol, side) {
    const info = st.byId[symbol];
    if (!info) { msg(`${symbol}: ticker não encontrado nas opções de ${st.underlying || "—"} no MT5.`, true); return; }
    const qty = Math.max(1, Math.floor(num("sm-qty") || 100));
    addLeg({ kind: "opcao", symbol, side, quantity: qty, price: null, sigma: null, info });
  }

  function addStock(side) {
    if (!st.underlying) return;
    addLeg({ kind: "ativo", symbol: st.underlying, side, quantity: Math.max(1, Math.floor(num("sm-qty") || 100)), price: null, sigma: null });
  }

  function afterLegsChange() {
    msg("");
    renderLegs();
    renderChain();
    schedule();
    App.savePrefs();
  }

  function legLabel(l) {
    if (l.kind === "ativo") return `<b>${esc(l.symbol)}</b> <span class="muted">ativo-objeto (ações)</span>`;
    const i = l.info || st.byId[l.symbol] || {};
    const style = i.exercise_style === "european" ? "E" : i.exercise_style === "american" ? "A" : "";
    return `<b>${esc(l.symbol)}</b> <span class="muted">${esc(i.option_type || "")} ${FMT.price(i.strike)} · ${FMT.date(i.expiration_date).slice(0, 5)}</span>${style ? ` <span class="style-tag ${style === "E" ? "eur" : "amer"}">${style}</span>` : ""}`;
  }

  function renderLegs() {
    const body = $("sm-legs").querySelector("tbody");
    if (!st.legs.length) {
      body.innerHTML = `<tr><td colspan="8" class="l muted">Nenhuma perna. Clique em C/V na grade, digite um ticker ou adicione o ativo.</td></tr>`;
      return;
    }
    body.innerHTML = st.legs.map((l, i) => `<tr data-i="${i}">
      <td class="l"><select class="sm-side" aria-label="Lado"><option value="compra" ${l.side === "compra" ? "selected" : ""}>Compra</option><option value="venda" ${l.side === "venda" ? "selected" : ""}>Venda</option></select></td>
      <td><input class="sm-q" type="number" min="1" step="1" value="${l.quantity}" aria-label="Quantidade" style="width:5.2rem"></td>
      <td class="l">${legLabel(l)}</td>
      <td data-f="book">—</td>
      <td><input class="sm-p" type="number" min="0" step="0.01" value="${FMT.ok(l.price) ? l.price : ""}" aria-label="Preço de entrada" style="width:5.2rem"></td>
      <td>${l.kind === "ativo" ? '<span class="muted">—</span>' : `<input class="sm-v" type="number" min="0" step="any" value="${FMT.ok(l.sigma) ? l.sigma : ""}" aria-label="Volatilidade" style="width:4.6rem">`}</td>
      <td class="l" data-f="quality"></td>
      <td><button type="button" class="sm-del" title="Remover perna" aria-label="Remover perna">✕</button></td></tr>`).join("");
    updateLegQuotes();
  }

  // Atualiza só as células de cotação (sem refazer os campos em edição).
  function updateLegQuotes() {
    const out = st.result ? st.result.legs : [];
    $("sm-legs").querySelectorAll("tbody tr[data-i]").forEach((tr) => {
      const r = out[Number(tr.dataset.i)];
      const set = (f, html) => { const td = tr.querySelector(`[data-f=${f}]`); if (td) td.innerHTML = html; };
      if (!r) { set("book", "—"); set("quality", ""); return; }
      set("book", r.price_basis === "ultimo_b3"
        ? `últ. ${FMT.price(r.last)} <span class="badge mid" title="Último negócio do pregão (fechamento oficial da B3), indicativo; sem bid/ask">B3</span>`
        : `${FMT.price(r.bid)} / ${FMT.price(r.ask)}`);
      const p = tr.querySelector(".sm-p");
      if (p) {
        p.placeholder = r.price_given === null && FMT.ok(r.price_used) ? FMT.price(r.price_used) : "natural";
        p.title = r.price_given === null ? `Vazio: ${r.price_source}` : "Preço informado por você";
      }
      const v = tr.querySelector(".sm-v");
      if (v) v.placeholder = FMT.ok(r.iv) ? FMT.num(r.iv * 100, 1) : "sem IV";
      const flags = r.flags || [];
      const when = r.quote_time ? `Último tick ${FMT.datetime(r.quote_time)}${FMT.ok(r.quote_age_seconds) ? ` (idade ${FMT.age(r.quote_age_seconds)})` : ""}` : "";
      const tip = [flags.join(", "), when, r.ref_note].filter(Boolean).join(" · ");
      set("quality", (flags.length ? `<span class="badge bad" title="${esc(tip)}">${esc(flags[0])}${flags.length > 1 ? " +" : ""}</span>` : `<span class="badge ok" title="${esc(tip)}">ok</span>`) +
        (r.ref_note ? ` <span class="badge mid" title="${esc(r.ref_note)}">B3</span>` : ""));
    });
  }

  function onLegsInput(ev) {
    const tr = ev.target.closest("tr[data-i]");
    if (!tr) return;
    const l = st.legs[Number(tr.dataset.i)];
    const t = ev.target;
    const val = t.value === "" ? null : Number(t.value);
    if (t.classList.contains("sm-side")) { l.side = t.value; l.price = null; renderLegs(); renderChain(); }
    else if (t.classList.contains("sm-q")) { if (!(val > 0)) return; l.quantity = Math.floor(val); renderChain(); }
    else if (t.classList.contains("sm-p")) l.price = FMT.ok(val) && val >= 0 ? val : null;
    else if (t.classList.contains("sm-v")) l.sigma = FMT.ok(val) && val > 0 ? val : null;
    else return;
    schedule();
    App.savePrefs();
  }

  // ---------- avaliação ----------
  function msg(text, err = false) {
    $("sm-msg").className = "msg" + (err ? " err" : "");
    $("sm-msg").textContent = text;
  }

  function schedule(delay = 350, refresh = false) {
    clearTimeout(st.timer);
    st.timer = setTimeout(() => evaluate(refresh), delay);
  }

  async function evaluate(refresh = false) {
    if (!st.underlying || !st.legs.length) { st.result = null; $("sm-result").hidden = true; App.setLevels([], "simulator"); return; }
    const token = ++st.token;
    const pct = (id) => { const v = num(id); return v === null ? null : v / 100; };
    const body = {
      underlying: st.underlying,
      legs: st.legs.map((l) => ({ kind: l.kind, symbol: l.kind === "opcao" ? l.symbol : null, side: l.side, quantity: l.quantity, price: l.price, sigma: FMT.ok(l.sigma) ? l.sigma / 100 : null })),
      rate_annual: pct("sm-rate"),
      vol_override: pct("sm-vol"),
      costs_brl: num("sm-costs") || 0,
      target_price: num("sm-target"),
      refresh,
    };
    const host = $("sm-result").hidden ? $("sm-legs").closest(".card") : $("sm-result");
    Busy.show(host, "Simulando…");
    try {
      const r = await api("/api/simulator/evaluate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      if (token !== st.token) return; // resposta atrasada de uma edição anterior
      st.result = r;
      msg("");
      updateLegQuotes();
      renderResult();
    } catch (e) {
      if (token !== st.token) return;
      msg(`Erro: ${e.message}`, true);
    } finally {
      Busy.hide(host);
    }
  }

  // ---------- resultado ----------
  function renderResult() {
    const r = st.result;
    $("sm-result").hidden = false;
    $("sm-res-title").innerHTML = `${tickerIcon(r.underlying, 24)}${esc(r.kind_label)} · ${esc(r.underlying)}`;
    const flowWord = { credito: "crédito", debito: "débito", zero: "zero a zero" }[r.entry_flow];
    $("sm-res-sub").textContent = `${r.legs.length} perna(s) · 1º vencimento ${FMT.date(r.first_expiration)} (${r.dte_business_days} du) · entrada a ${flowWord} ${FMT.brl(Math.abs(r.entry_cash_total))}${FMT.ok(r.entry_net_per_unit) ? ` (${FMT.price(r.entry_net_per_unit)} por unidade)` : ""} · avaliado ${FMT.datetime(r.evaluated_at)}`;
    const alerts = [];
    if (r.quotes_note) alerts.push(`<div class="warn">${esc(r.quotes_note)}</div>`);
    for (const a of r.alerts || []) alerts.push(`<div class="warn ${a.startsWith("RISCO") ? "alert-risk" : ""}">${esc(a)}</div>`);
    for (const w of r.warnings || []) alerts.push(`<div class="warn">${esc(w)}</div>`);
    $("sm-alerts").innerHTML = alerts.join("");
    renderMetrics(r);
    $("sm-margin").innerHTML = App.marginHtml(r.margin, r.max_profit_unbounded ? null : r.max_profit);
    renderAssumptions(r);
    const sim = r.simulation;
    const slider = $("sm-slider");
    const keep = Number(slider.value);
    $("sm-time").hidden = !sim.model_available;
    slider.max = Math.max(0, sim.dates.length - 1);
    slider.value = Math.min(keep, Number(slider.max)); // mantém a data ao editar as pernas
    $("sm-sim-note").textContent = sim.model_available ? sim.assumptions : `Simulação temporal indisponível: ${sim.model_reason}. Informe a vol. geral ou a vol. da perna. Exibindo só o payoff no vencimento.`;
    draw();
  }

  function renderMetrics(r) {
    const g = r.greeks || {};
    const cls = (v) => ((v ?? 0) >= 0 ? "pos" : "neg");
    const items = [
      ["Fluxo na entrada", `<span class="${cls(r.entry_cash_total)}">${FMT.signedBrl(r.entry_cash_total)}</span> <span class="muted">(${r.entry_cash_total >= 0 ? "crédito" : "débito"})</span>`],
      ["Lucro máximo", r.max_profit_unbounded ? "ilimitado" : FMT.brl(r.max_profit)],
      ["Perda máxima", r.max_loss_unbounded ? '<span class="neg">ilimitada</span>' : FMT.brl(r.max_loss)],
      [`Breakeven ${r.profile_exact ? "(vencimento)" : "(1º venc., modelo)"}`, r.breakevens.length ? r.breakevens.map(FMT.price).join(" / ") : "—"],
      ["Lucro máx. ÷ perda máx.", FMT.ratio(r.reward_risk)],
      ["POP no vencimento", r.pop === null ? `indisponível <span class="muted">(${esc(r.pop_unavailable_reason || "")})</span>` : `<span title="${esc(r.pop_method || "")}">${FMT.pct(r.pop)}</span>`],
      ["Zerar agora pelo natural", r.close_natural_now === null ? "sem book" : `${exitWord(r.close_natural_now)} → saldo <b class="${cls(r.pnl_close_natural_now)}">${FMT.signedBrl(r.pnl_close_natural_now)}</b>`],
      ["Zerar agora pelo mid", r.close_mid_now === null ? "sem book" : `${exitWord(r.close_mid_now)} → saldo <span class="${cls(r.pnl_close_mid_now)}">${FMT.signedBrl(r.pnl_close_mid_now)}</span>`],
      ["Valor teórico agora (modelo)", r.theoretical_value_now === null ? "—" : `${exitWord(r.theoretical_value_now)} → saldo ${FMT.signedBrl(r.pnl_theoretical_now)}`],
      ["Delta (R$ por R$ 1 no ativo)", FMT.num(g.delta, 2)],
      ["Gamma", FMT.num(g.gamma, 3)],
      ["Theta (R$/dia útil)", FMT.signedBrl(g.theta_per_day)],
      ["Vega (R$ por 1 p.p. de vol)", FMT.signedBrl(g.vega_per_pp)],
    ];
    $("sm-metrics").innerHTML = items.map(([k, v]) => `<div><span>${k}</span><span>${v}</span></div>`).join("");
  }

  const exitWord = (v) => (Math.abs(v) < 0.005 ? "zero a zero" : v > 0 ? `recebe ${FMT.brl(v)}` : `paga ${FMT.brl(-v)}`);

  function renderAssumptions(r) {
    const prices = r.legs.map((l) => `${l.symbol}: ${FMT.price(l.price_used)} (${l.price_source})${l.kind === "opcao" ? ` · σ ${FMT.pct(l.sigma_used)} (${l.sigma_source})` : ""}`);
    const items = [
      `Preços de entrada — ${prices.join("; ")}.`,
      r.simulation.assumptions,
      r.pop_method ? `POP: ${r.pop_method.replace(/\.+$/, "")}. Não é garantia de resultado.` : `POP indisponível: ${r.pop_unavailable_reason}.`,
      `Juros: ${FMT.pct(r.rate_annual, 2)} a.a. Custos considerados: ${FMT.brl(r.costs_brl)}.`,
      "Zerar pelo natural: vende as compradas no bid e recompra as vendidas no ask (book atual). Mid é só referência.",
      "Opções americanas avaliadas como europeias (calls sem proventos valem igual; puts americanas ficam aproximadas).",
      "Open interest não disponível no MT5; volume e negócios não equivalem a contratos em aberto.",
    ];
    $("sm-assumptions").innerHTML = items.map((t) => `<li>${esc(t)}</li>`).join("");
  }

  function chartData(r) {
    return {
      simulation: r.simulation,
      legs: r.legs.filter((l) => l.kind === "opcao").map((l) => ({ strike: l.strike, side: l.side })),
      breakevens: r.breakevens,
      spot: r.spot,
      target_price: r.target_price,
      max_profit: r.max_profit_unbounded ? null : r.max_profit,
      max_loss: r.max_loss_unbounded ? null : r.max_loss,
    };
  }

  function draw() {
    const r = st.result;
    if (!r || $("tab-simulator").hidden) return;
    const sim = r.simulation;
    const i = Number($("sm-slider").value);
    const sel = sim.dates[i];
    const showModel = sel && sel.business_days_left > 0;
    $("sm-time-label").textContent = sel ? `${FMT.date(sel.date)} · ${sel.business_days_left} du até o 1º vencimento${sel.business_days_left === 0 ? (sim.multi_expiry ? " (pernas posteriores pelo modelo)" : " (payoff exato)") : " (modelo)"}` : "";
    $("sm-legend").innerHTML = Payoff.legend(showModel, sel, sim.expiry_label);
    Payoff.render($("sm-payoff"), chartData(r), i, App.tooltip());
    const strikes = [...new Set(r.legs.filter((l) => l.kind === "opcao").map((l) => l.strike))];
    App.setLevels([
      { label: "Atual", value: r.spot, color: "#1d2330", size: 1 },
      ...r.breakevens.map((b) => ({ label: "BE venc.", value: b, color: "#157a3c", dashed: true, size: 1.6, fit: true })),
      ...(showModel ? sel.breakevens.map((b) => ({ label: `Equil. ${FMT.date(sel.date)}`, value: b, color: "#1f5fbf", dashed: true, dash: [2, 3] })) : []),
      ...(r.target_price ? [{ label: "Alvo", value: r.target_price, color: "#7a2fc0", dashed: true, size: 1.4 }] : []),
      ...strikes.map((k) => ({ label: "Strike", value: k, color: "#98a2b3", dashed: true, dash: [2, 4], fit: true })),
    ], "simulator");
    const units = r.entry_net_per_unit !== null && r.legs.length ? r.legs[0].quantity * (r.legs[0].multiplier || 1) : null;
    ExitPanel.render($("sm-exit-box"), { sim, index: i, spot: r.spot, target: r.target_price, units });
  }

  // ---------- preferências ----------
  function prefs() {
    const out = {};
    for (const f of PREF_FIELDS) out[f] = $(f).value;
    out.exp = st.exp;
    out.legs = st.legs.map(({ kind, symbol, side, quantity, price, sigma, info }) => ({ kind, symbol, side, quantity, price, sigma, info }));
    return out;
  }

  function applyPrefs(p) {
    if (!p) return;
    for (const f of PREF_FIELDS) if (p[f] !== undefined && p[f] !== "") $(f).value = p[f];
    if (p.exp) st.exp = p.exp;
    if (Array.isArray(p.legs)) st.legs = p.legs.filter((l) => l && l.side && l.quantity > 0);
  }

  function activate() {
    const u = $("sm-underlying").value.trim().toUpperCase();
    if (u && u !== st.underlying) {
      // Pernas salvas pertencem ao ativo salvo: carrega sem descartá-las.
      st.underlying = st.underlying || u;
      onUnderlying(true);
    } else if (st.result) requestAnimationFrame(draw);
  }

  function init(def, savedPrefs) {
    $("sm-rate").value = +(def.rate_annual * 100).toFixed(2);
    applyPrefs(savedPrefs);
    renderLegs();
    $("sm-underlying").addEventListener("change", () => onUnderlying());
    $("sm-exp").addEventListener("change", () => { st.exp = $("sm-exp").value; st.centered = false; loadChain(false); App.savePrefs(); });
    $("sm-chain").addEventListener("click", (ev) => {
      const b = ev.target.closest("button[data-sym]");
      if (b) addOption(b.dataset.sym, b.dataset.side);
    });
    const addTyped = (side) => {
      const sym = $("sm-ticker").value.trim().toUpperCase();
      if (!sym) return;
      addOption(sym, side);
      $("sm-ticker").value = "";
    };
    $("sm-ticker").addEventListener("keydown", (ev) => { if (ev.key === "Enter") { ev.preventDefault(); addTyped(ev.shiftKey ? "venda" : "compra"); } });
    $("sm-add-buy").addEventListener("click", () => addTyped("compra"));
    $("sm-add-sell").addEventListener("click", () => addTyped("venda"));
    $("sm-stock-buy").addEventListener("click", () => addStock("compra"));
    $("sm-stock-sell").addEventListener("click", () => addStock("venda"));
    $("sm-legs").addEventListener("change", onLegsInput);
    $("sm-legs").addEventListener("click", (ev) => {
      const b = ev.target.closest(".sm-del");
      if (!b) return;
      st.legs.splice(Number(b.closest("tr").dataset.i), 1);
      afterLegsChange();
    });
    $("sm-flip").addEventListener("click", () => {
      st.legs.forEach((l) => { l.side = l.side === "compra" ? "venda" : "compra"; l.price = null; });
      afterLegsChange();
    });
    $("sm-clear").addEventListener("click", () => { st.legs = []; afterLegsChange(); });
    $("sm-refresh").addEventListener("click", () => { loadChain(true); schedule(0, true); });
    for (const id of ["sm-target", "sm-vol", "sm-rate", "sm-costs"]) $(id).addEventListener("change", () => { schedule(); App.savePrefs(); });
    $("sm-qty").addEventListener("change", () => App.savePrefs());
    let raf = 0;
    $("sm-slider").addEventListener("input", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(draw); });
    $("sm-max").addEventListener("click", () => App.toggleMax($("sm-payoff-wrap"), $("sm-max"), draw));
    window.addEventListener("resize", () => { if (st.result) draw(); });
  }

  return { init, activate, prefs, redraw: draw };
})();
