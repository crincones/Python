// Aba Acompanhamento: registra estruturas (trava ou qualquer combinação), agrupa e acompanha o
// resultado com cotações do MT5. Cálculos no backend; nada é enviado à corretora.
const Tracking = (() => {
  const $ = (id) => document.getElementById(id);
  const st = {
    data: null, editing: null, closing: null, detail: null, detailKind: null, detailKey: null,
    timer: null, loading: false, options: [], optionsFor: null, ready: false, confirmDelete: null,
  };
  const api = (...a) => App.api(...a);
  const json = (method, body) => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const num = (id) => { const v = $(id).value; return v === "" ? null : Number(v); };
  const today = () => new Date().toLocaleDateString("sv-SE", { timeZone: "America/Sao_Paulo" });
  const pnlSpan = (v) => `<span class="${(v ?? 0) >= 0 ? "pos" : "neg"}">${FMT.signedBrl(v)}</span>`;
  const evalBody = () => ({ vol_override: num("trk-vol") === null ? null : num("trk-vol") / 100 });

  // ---------- carregamento ----------
  function setup() {
    if (st.ready) return;
    st.ready = true;
    $("trk-refresh").addEventListener("click", () => refresh());
    $("trk-new").addEventListener("click", () => openForm(null));
    $("trk-closed").addEventListener("change", () => { render(); App.savePrefs(); });
    $("trk-auto").addEventListener("change", () => { setAuto(); App.savePrefs(); });
    $("trk-vol").addEventListener("change", () => { App.savePrefs(); refresh(); });
    $("tf-add-leg").addEventListener("click", () => addLegRow({}));
    $("tf-cancel").addEventListener("click", () => { $("trk-form-card").hidden = true; });
    $("tf-underlying").addEventListener("change", () => {
      const u = $("tf-underlying").value.trim().toUpperCase();
      $("tf-underlying-icon").innerHTML = tickerIcon(u, 26);
      loadOptions(u);
    });
    $("trk-form").addEventListener("submit", saveForm);
    $("trk-close-form").addEventListener("submit", saveClose);
    $("tc-cancel").addEventListener("click", () => { $("trk-close-card").hidden = true; });
    $("trk-groups").addEventListener("click", onGroupsClick);
    $("tf-legs").addEventListener("click", (ev) => { if (ev.target.matches(".rm-leg")) ev.target.closest("tr").remove(); });
    $("tf-legs").addEventListener("change", (ev) => { if (ev.target.matches(".leg-sym")) describeLeg(ev.target.closest("tr")); });
    let raf = 0;
    $("td-slider").addEventListener("input", () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(drawDetail); });
    $("td-max").addEventListener("click", () => App.toggleMax($("td-payoff-wrap"), $("td-max"), drawDetail));
    window.addEventListener("resize", () => { if (st.detail && !$("tab-tracking").hidden) drawDetail(); });
  }

  function activate() {
    setup();
    if (!st.data && !st.loading) refresh();
  }

  function setAuto() {
    clearInterval(st.timer);
    st.timer = $("trk-auto").checked ? setInterval(() => { if (!$("tab-tracking").hidden) refresh(); }, 60_000) : null;
  }

  async function refresh() {
    if (st.loading) return;
    st.loading = true;
    $("trk-refresh").disabled = true;
    $("trk-meta").textContent = "Atualizando cotações no MT5…";
    try {
      const host = $("trk-groups").closest(".card");
      Busy.show(host, "Atualizando cotações…");
      try {
        st.data = await api("/api/tracking/evaluate", json("POST", evalBody()));
      } finally {
        Busy.hide(host);
      }
      $("trk-meta").textContent = `Atualizado em ${FMT.datetime(st.data.evaluated_at)} · ${st.data.positions.length} estrutura(s). P&L "natural" = zerar agora vendendo no bid e recomprando no ask; "mid" é referência.`;
      const mk = $("trk-market");
      mk.hidden = !st.data.quotes_note;
      mk.textContent = st.data.quotes_note || "";
      const errs = st.data.errors || [];
      $("trk-errors").hidden = !errs.length;
      $("trk-errors").textContent = errs.length ? `Problemas: ${errs.join(" · ")}` : "";
      render();
      if (st.detailKey) openDetail(st.detailKind, st.detailKey, true);
    } catch (e) {
      $("trk-meta").textContent = `Erro ao atualizar: ${e.message}`;
    } finally {
      st.loading = false;
      $("trk-refresh").disabled = false;
    }
  }

  // ---------- lista por grupo ----------
  function legsText(p) {
    return p.legs.map((l) => `${l.side === "compra" ? "C" : "V"} ${l.quantity} ${esc(l.symbol)} <span class="muted">${l.option_type} ${FMT.price(l.strike)}</span>`).join("<br>");
  }

  function render() {
    const d = st.data;
    if (!d) return;
    const showClosed = $("trk-closed").checked;
    $("trk-group-list").innerHTML = d.groups.map((g) => `<option value="${esc(g.group)}">`).join("");
    if (!d.positions.length) {
      $("trk-groups").innerHTML = '<p class="muted">Nenhuma estrutura registrada. Use "+ Nova estrutura" ou, na aba Análise, "Adicionar ao acompanhamento".</p>';
      return;
    }
    $("trk-groups").innerHTML = d.groups.map((g) => {
      const rows = d.positions.filter((p) => p.group === g.group && (showClosed || p.status === "aberta"));
      if (!rows.length) return "";
      return `<div class="group">
        <div class="group-head">
          <h3>${g.underlyings.map((u) => tickerIcon(u, 20)).join("")}${esc(g.group)} <span class="muted small">${g.open} aberta(s) · ${esc(g.underlyings.join(", "))}</span></h3>
          <div class="group-stats">
            <span>P&L natural <b>${pnlSpan(g.pnl_natural)}</b></span>
            <span>P&L mid <b>${pnlSpan(g.pnl_mid)}</b></span>
            <span>Realizado <b>${pnlSpan(g.realized_pnl)}</b></span>
            <span>Risco máx. somado <b>${FMT.brl(g.max_loss_sum)}</b></span>
            ${g.combinable && g.open > 1 ? `<button data-act="group" data-group="${esc(g.group)}">Payoff do grupo</button>` : ""}
          </div>
        </div>
        <div class="table-wrap"><table class="trk-table">
          <thead><tr><th class="l">Estrutura</th><th class="l">Pernas</th><th>Venc.</th><th>Entrada (por un.)</th><th>Zerar agora (natural)</th>
            <th>P&L natural</th><th>P&L mid</th><th title="P&L natural ÷ lucro máximo">% do lucro máx.</th><th>Perda máx.</th><th>Breakeven</th><th class="l">Alertas</th><th></th></tr></thead>
          <tbody>${rows.map(rowHtml).join("")}</tbody>
        </table></div></div>`;
    }).join("");
  }

  // Alertas resumidos num selo; o texto completo aparece ao passar o mouse (ou com foco).
  function alertChip(list) {
    if (!list || !list.length) return "";
    const risk = list.some((a) => /RISCO|STOP/.test(a));
    const hit = !risk && list.some((a) => /ALVO/.test(a));
    const first = list[0].replace(/:.*/, "");
    const short = first.length > 26 ? first.slice(0, 25) + "…" : first;
    const tip = `<ul>${list.map((a) => `<li>${esc(a)}</li>`).join("")}</ul>`;
    return `<span class="alert-chip ${risk ? "risk" : hit ? "hit" : ""}" tabindex="0" data-tip="${esc(tip)}" aria-label="${esc(list.join(". "))}">⚠ ${list.length} · ${esc(short)}</span>`;
  }

  function rowHtml(p) {
    const open = p.status === "aberta";
    const flow = p.entry_flow === "credito" ? "crédito" : "débito";
    const closeFlow = p.value_natural === null ? "" : p.value_natural >= 0 ? "crédito" : "débito";
    const alerts = alertChip(p.alerts);
    const key = `${p.id}`;
    return `<tr data-id="${p.id}" title="Clique para ver no gráfico" class="selectable ${open ? "" : "closed"} ${st.detailKey === key ? "selected" : ""}">
      <td class="l">${tickerIcon(p.underlying, 18)}<b>${esc(p.name)}</b><br><span class="muted small">${esc(p.kind_label)} · ${esc(p.underlying)} · entrada ${FMT.date(p.entry_date)}</span></td>
      <td class="l small">${legsText(p)}</td>
      <td>${FMT.date(p.first_expiration)}<br><span class="muted small">${p.dte_business_days} du</span></td>
      <td>${FMT.price(p.entry_net_per_unit)} <span class="muted small">${flow}</span></td>
      <td>${open ? `${FMT.price(p.close_net_natural_per_unit)} <span class="muted small">${closeFlow}</span>` : "—"}</td>
      <td>${open ? pnlSpan(p.pnl_natural) : `<span class="muted small">realizado</span><br>${pnlSpan(p.realized_pnl)}`}</td>
      <td>${open ? pnlSpan(p.pnl_mid) : "—"}</td>
      <td>${open ? FMT.pct(p.pnl_pct_of_max_profit, 0) : "—"}</td>
      <td>${FMT.brl(p.max_loss)}${p.profile_exact ? "" : '<span class="muted small" title="estimado pelo modelo"> *</span>'}</td>
      <td>${(p.breakevens || []).map(FMT.price).join(" / ") || "—"}</td>
      <td class="l">${alerts}</td>
      <td><div class="acts">
        <button data-act="detail" data-id="${p.id}">Detalhe</button>
        <button data-act="edit" data-id="${p.id}">Editar</button>
        ${open ? `<button data-act="close" data-id="${p.id}">Encerrar</button>` : `<button data-act="reopen" data-id="${p.id}">Reabrir</button>`}
        <button data-act="delete" data-id="${p.id}" class="danger">${st.confirmDelete === p.id ? "Confirmar exclusão" : "Excluir"}</button>
      </div></td></tr>`;
  }

  async function onGroupsClick(ev) {
    const b = ev.target.closest("button[data-act]");
    if (!b) {
      // Clique na linha (fora dos botões) seleciona a estrutura: detalhe + gráfico do ativo.
      const tr = ev.target.closest("tr[data-id]");
      if (tr) {
        try { await openDetail("position", tr.dataset.id); } catch (e) {
          $("trk-errors").hidden = false;
          $("trk-errors").textContent = `Erro: ${e.message}`;
        }
      }
      return;
    }
    const id = b.dataset.id;
    const p = id && st.data.positions.find((x) => x.id === id);
    try {
      if (b.dataset.act === "detail") await openDetail("position", id);
      else if (b.dataset.act === "group") await openDetail("group", b.dataset.group);
      else if (b.dataset.act === "edit") {
        const records = await api("/api/tracking/positions");
        openForm({ ...p, _record: records.find((r) => r.id === id) });
      }
      else if (b.dataset.act === "close") openClose(p);
      else if (b.dataset.act === "reopen") { await api(`/api/tracking/positions/${id}/reopen`, { method: "POST" }); await refresh(); }
      else if (b.dataset.act === "delete") {
        if (st.confirmDelete !== id) {
          st.confirmDelete = id;
          render();
          setTimeout(() => { if (st.confirmDelete === id) { st.confirmDelete = null; render(); } }, 4000);
          return;
        }
        st.confirmDelete = null;
        await api(`/api/tracking/positions/${id}`, { method: "DELETE" });
        if (st.detailKey === id) {
          st.detailKey = null;
          st.detail = null;
          $("trk-detail-card").hidden = true;
          App.setLevels([], "tracking"); // estrutura excluída: some do gráfico
        }
        await refresh();
      }
    } catch (e) {
      $("trk-errors").hidden = false;
      $("trk-errors").textContent = `Erro: ${e.message}`;
    }
  }

  // ---------- formulário ----------
  async function loadOptions(u) {
    if (!u || u === st.optionsFor) return;
    st.optionsFor = u;
    try {
      st.options = await api(`/api/options/${encodeURIComponent(u)}`);
      $("trk-opts").innerHTML = st.options.map((o) => `<option value="${esc(o.symbol)}">${o.option_type} ${FMT.price(o.strike)} · ${FMT.date(o.expiration_date)} · ${o.exercise_style === "american" ? "amer." : "eur."}</option>`).join("");
      document.querySelectorAll("#tf-legs tbody tr").forEach(describeLeg);
    } catch (e) {
      st.options = [];
      $("tf-msg").className = "msg err";
      $("tf-msg").textContent = `Não foi possível listar as opções de ${u}: ${e.message}`;
    }
  }

  function describeLeg(tr) {
    const sym = tr.querySelector(".leg-sym").value.trim().toUpperCase();
    const o = st.options.find((x) => x.symbol === sym);
    tr.querySelector(".leg-desc").innerHTML = !sym ? "" : o
      ? `${o.option_type} ${FMT.price(o.strike)} · venc. ${FMT.date(o.expiration_date)}`
      : '<span class="neg">ticker não encontrado</span>';
  }

  function addLegRow(l) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td><input class="leg-sym upper" list="trk-opts" value="${esc(l.symbol || "")}" placeholder="ticker"></td>
      <td><select class="leg-side"><option value="compra">Compra</option><option value="venda">Venda</option></select></td>
      <td><input class="leg-qty" type="number" min="1" step="1" value="${l.quantity || 100}"></td>
      <td><input class="leg-price" type="number" min="0" step="any" value="${l.entry_price ?? ""}" placeholder="opcional"></td>
      <td class="l small leg-desc"></td>
      <td><button type="button" class="rm-leg" title="Remover perna">✕</button></td>`;
    tr.querySelector(".leg-side").value = l.side || "compra";
    $("tf-legs").querySelector("tbody").appendChild(tr);
    describeLeg(tr);
  }

  function openForm(p, prefill) {
    setup();
    const src = p || prefill || {};
    st.editing = p ? p.id : null;
    $("trk-form-title").textContent = p ? `Editar: ${p.name}` : "Nova estrutura";
    $("tf-name").value = src.name || "";
    $("tf-group").value = src.group || "";
    $("tf-underlying").value = src.underlying || "";
    $("tf-underlying-icon").innerHTML = tickerIcon(src.underlying, 26);
    $("tf-date").value = src.entry_date || today();
    // Na edição, mostra o que foi registrado (não o recalculado).
    const rec = p ? p._record : null;
    $("tf-net").value = rec ? (rec.entry_net ?? "") : (src.entry_net ?? "");
    $("tf-flow").value = rec ? (rec.entry_flow || "debito") : (src.entry_flow || "debito");
    $("tf-costs").value = src.costs_entry ?? 0;
    $("tf-tp").value = src.take_profit_pct ?? "";
    $("tf-sl").value = src.stop_loss_brl ?? "";
    $("tf-notes").value = src.notes || "";
    $("tf-legs").querySelector("tbody").innerHTML = "";
    (rec ? rec.legs : src.legs || [{}, {}]).forEach(addLegRow);
    $("tf-msg").className = "msg";
    $("tf-msg").textContent = prefill ? "Confira e ajuste o preço líquido para o preço efetivamente executado." : "";
    $("trk-form-card").hidden = false;
    $("trk-close-card").hidden = true;
    loadOptions(src.underlying);
    $("trk-form-card").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function saveForm(ev) {
    ev.preventDefault();
    const legs = [...document.querySelectorAll("#tf-legs tbody tr")].map((tr) => ({
      symbol: tr.querySelector(".leg-sym").value.trim().toUpperCase(),
      side: tr.querySelector(".leg-side").value,
      quantity: Number(tr.querySelector(".leg-qty").value),
      entry_price: tr.querySelector(".leg-price").value === "" ? null : Number(tr.querySelector(".leg-price").value),
    })).filter((l) => l.symbol);
    const net = num("tf-net");
    const body = {
      name: $("tf-name").value.trim(),
      group: $("tf-group").value.trim() || "Sem grupo",
      underlying: $("tf-underlying").value.trim().toUpperCase(),
      legs,
      entry_net: net,
      entry_flow: net === null ? null : $("tf-flow").value,
      entry_date: $("tf-date").value,
      costs_entry: num("tf-costs") || 0,
      take_profit_pct: num("tf-tp"),
      stop_loss_brl: num("tf-sl"),
      notes: $("tf-notes").value,
    };
    const msg = $("tf-msg");
    const tp = body.take_profit_pct;
    if (tp !== null && !(tp > 0 && tp <= 100)) {
      msg.className = "msg err";
      msg.textContent = `Alvo — use um percentual do lucro máximo entre 1 e 100 (ex.: 50 = sair com metade do lucro máximo). Você digitou ${FMT.num(tp, 2)}.`;
      $("tf-tp").focus();
      return;
    }
    try {
      const url = st.editing ? `/api/tracking/positions/${st.editing}` : "/api/tracking/positions";
      await api(url, json(st.editing ? "PUT" : "POST", body));
      $("trk-form-card").hidden = true;
      await refresh();
    } catch (e) {
      msg.className = "msg err";
      msg.textContent = `Erro: ${humanError(e.message)}`;
    }
  }

  const FIELD_LABELS = {
    name: "Nome", group: "Grupo", underlying: "Ativo-objeto", entry_date: "Data de entrada",
    entry_net: "Preço líquido", entry_flow: "Sentido", costs_entry: "Custos de entrada",
    take_profit_pct: "Alvo (% do lucro máx.)", stop_loss_brl: "Stop (R$)", notes: "Observações",
    symbol: "Ticker", side: "Lado", quantity: "Quantidade", entry_price: "Preço da perna",
    exit_date: "Data de saída", exit_net: "Preço líquido de saída", exit_flow: "Sentido",
    costs_exit: "Custos de saída", leg_prices: "Preços das pernas", legs: "Pernas",
  };

  function translate(msg) {
    return msg
      .replace(/^Value error, /, "")
      .replace(/Input should be less than or equal to (\S+)/, "deve ser no máximo $1")
      .replace(/Input should be greater than or equal to (\S+)/, "deve ser no mínimo $1")
      .replace(/Input should be greater than (\S+)/, "deve ser maior que $1")
      .replace(/Input should be a valid number.*/, "deve ser um número")
      .replace(/Input should be a valid date.*/, "data inválida")
      .replace(/Field required/, "obrigatório")
      .replace(/List should have at least 1 item.*/, "informe pelo menos uma perna");
  }

  function humanError(text) {
    // Erros de validação do FastAPI vêm como lista JSON: indica o campo (e a perna) de cada um.
    try {
      const items = JSON.parse(text);
      if (Array.isArray(items)) {
        return items.map((i) => {
          const loc = (i.loc || []).filter((x) => x !== "body");
          const field = [...loc].reverse().find((x) => typeof x === "string" && FIELD_LABELS[x]);
          const leg = loc[0] === "legs" && typeof loc[1] === "number" ? `perna ${loc[1] + 1}: ` : "";
          return `${leg}${field ? FIELD_LABELS[field] + " — " : ""}${translate(i.msg || "")}`;
        }).join("; ");
      }
    } catch { /* texto simples */ }
    return text;
  }

  function prefillFromAnalysis(d, analysis) {
    const [L, S] = d.legs;
    const price = d.limit && d.limit.suggested !== null ? d.limit.suggested : d.entry_natural;
    const exp = d.expiration;
    openForm(null, {
      name: `${d.kind_label.replace(/ \(.*\)/, "")} ${FMT.price(L.strike)}/${FMT.price(S.strike)}`,
      group: `${analysis.underlying} ${FMT.date(exp).slice(3)}`,
      underlying: analysis.underlying,
      legs: [
        { symbol: L.symbol, side: "compra", quantity: d.quantity },
        { symbol: S.symbol, side: "venda", quantity: d.quantity },
      ],
      entry_net: price,
      entry_flow: d.limit ? d.limit.flow : "debito",
    });
  }

  // ---------- encerramento ----------
  function openClose(p) {
    st.closing = p.id;
    $("trk-close-title").textContent = `Encerrar: ${p.name}`;
    $("tc-date").value = today();
    $("tc-net").value = p.close_net_natural_per_unit !== null ? +p.close_net_natural_per_unit.toFixed(2) : "";
    $("tc-flow").value = p.value_natural !== null && p.value_natural < 0 ? "debito" : "credito";
    $("tc-costs").value = 0;
    $("tc-legs").innerHTML = p.legs.map((l, i) => `<div class="field"><label for="tc-leg-${i}">${l.side === "compra" ? "Venda de" : "Recompra de"} ${esc(l.symbol)}</label><input id="tc-leg-${i}" class="tc-leg" type="number" step="any" min="0" placeholder="opcional"></div>`).join("");
    $("tc-msg").textContent = "";
    $("trk-close-card").hidden = false;
    $("trk-form-card").hidden = true;
    $("trk-close-card").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function saveClose(ev) {
    ev.preventDefault();
    const legPrices = [...document.querySelectorAll(".tc-leg")].map((i) => (i.value === "" ? null : Number(i.value)));
    const net = num("tc-net");
    const body = {
      exit_date: $("tc-date").value,
      exit_net: net,
      exit_flow: net === null ? null : $("tc-flow").value,
      leg_prices: legPrices.every((x) => x !== null) ? legPrices : null,
      costs_exit: num("tc-costs") || 0,
      reason: $("tc-reason").value,
    };
    try {
      await api(`/api/tracking/positions/${st.closing}/close`, json("POST", body));
      $("trk-close-card").hidden = true;
      await refresh();
    } catch (e) {
      $("tc-msg").className = "msg err";
      $("tc-msg").textContent = `Erro: ${humanError(e.message)}`;
    }
  }

  // ---------- detalhe ----------
  async function openDetail(kind, key, silent) {
    st.detailKind = kind;
    st.detailKey = key;
    const url = kind === "group" ? `/api/tracking/groups/${encodeURIComponent(key)}/detail` : `/api/tracking/positions/${key}/detail`;
    const host = $("trk-detail-card").hidden ? $("trk-groups").closest(".card") : $("trk-detail-card");
    if (!silent) Busy.show(host, kind === "group" ? "Montando o payoff do grupo…" : "Abrindo a estrutura…");
    let d;
    try {
      d = await api(url, json("POST", evalBody()));
    } finally {
      if (!silent) Busy.hide(host);
    }
    st.detail = d;
    render();
    const card = $("trk-detail-card");
    card.hidden = false;
    $("td-title").innerHTML = tickerIcon(d.underlying, 24) + esc(kind === "group" ? `Grupo ${key}: payoff agregado` : `${d.name} — ${d.kind_label}`);
    $("td-sub").textContent = `${d.underlying} · spot ${FMT.price(d.spot)} · 1º vencimento ${FMT.date(d.first_expiration)} (${d.dte_business_days} du) · ${d.vol_source}`;
    const alerts = [...(d.alerts || []), ...(d.warnings || []), ...(d.errors || [])];
    $("td-alerts").innerHTML = alerts.map((a) => `<div class="warn ${/RISCO|STOP/.test(a) ? "alert-risk" : ""}">${esc(a)}</div>`).join("");
    renderMetrics(d);
    renderLegs(d);
    $("td-notes").textContent = d.notes ? `Observações: ${d.notes}` : "";
    const sim = d.simulation;
    $("td-time").hidden = !sim.model_available;
    $("td-slider").max = Math.max(0, sim.dates.length - 1);
    if (!silent) $("td-slider").value = 0;
    $("td-assumptions").textContent = sim.model_available ? sim.assumptions : `Simulação temporal indisponível: ${sim.model_reason}.`;
    App.showUnderlying(d.underlying, "tracking");
    drawDetail();
    if (!silent) card.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function drawDetail() {
    const d = st.detail;
    if (!d) return;
    const sim = d.simulation;
    if (!sim.available) {
      $("td-payoff").innerHTML = `<p class="muted">Payoff indisponível: ${esc(sim.reason)}.</p>`;
      $("td-legend").innerHTML = "";
      return;
    }
    const i = Number($("td-slider").value);
    const sel = sim.dates[i];
    const showModel = sel && sel.business_days_left > 0;
    $("td-time-label").textContent = sel ? `${FMT.date(sel.date)} · ${sel.business_days_left} du até o 1º vencimento${showModel ? " (modelo)" : ""}` : "";
    $("td-legend").innerHTML = Payoff.legend(showModel, sel, sim.expiry_label);
    const view = { ...d, breakevens: d.breakevens || [], target_price: null };
    Payoff.render($("td-payoff"), view, i, App.tooltip());
    // Estrutura no gráfico do ativo: cada perna no seu strike e o(s) breakeven(s).
    const multiExp = new Set(d.legs.map((l) => l.expiration)).size > 1;
    App.setLevels([
      { label: "Atual", value: d.spot, color: "#1d2330", size: 1 },
      ...d.legs.map((l) => ({
        label: `${l.side === "compra" ? "Compra" : "Venda"} ${l.quantity} ${l.option_type} ${l.symbol}${multiExp ? ` (${FMT.date(l.expiration).slice(0, 5)})` : ""} · strike`,
        value: l.strike, color: l.side === "compra" ? "#157a3c" : "#b42318", dashed: true, dash: [5, 3], size: 1.4, fit: true,
      })),
      ...(d.breakevens || []).map((b) => ({ label: d.profile_exact ? "Breakeven no venc." : "Breakeven 1º venc. (modelo)", value: b, color: "#7a2fc0", size: 2, fit: true })),
      ...(showModel ? sel.breakevens.map((b) => ({ label: `Equilíbrio em ${FMT.date(sel.date)} (modelo)`, value: b, color: "#1f5fbf", dashed: true, dash: [2, 3] })) : []),
    ], "tracking");
  }

  function renderMetrics(d) {
    const g = d.greeks || {};
    const items = [
      ["Fluxo na entrada", FMT.signedBrl(d.entry_cash_total)],
      ["Custos de entrada", FMT.brl(d.costs_entry)],
      ["Zerar agora: valor natural", FMT.signedBrl(d.value_natural)],
      ["Zerar agora: valor mid", FMT.signedBrl(d.value_mid)],
      ["P&L não realizado (natural)", pnlSpan(d.pnl_natural)],
      ["P&L não realizado (mid)", pnlSpan(d.pnl_mid)],
      ["P&L teórico (modelo)", pnlSpan(d.pnl_theoretical)],
      ["% do lucro máximo", FMT.pct(d.pnl_pct_of_max_profit, 0)],
      ["% da perda máxima", FMT.pct(d.pnl_pct_of_risk, 0)],
      [d.profile_exact ? "Lucro máximo" : "Lucro máximo (estimado, faixa exibida)", FMT.brl(d.max_profit)],
      [d.profile_exact ? "Perda máxima" : "Perda máxima (estimada, faixa exibida)", FMT.brl(d.max_loss)],
      ["Breakeven", (d.breakevens || []).map(FMT.price).join(" / ") || "—"],
      ["Delta (R$ por R$ 1)", FMT.num(g.delta, 2)],
      ["Theta (R$/dia útil)", FMT.signedBrl(g.theta_per_day)],
      ["Vega (R$ por 1 p.p.)", FMT.signedBrl(g.vega_per_pp)],
      ["Gamma", FMT.num(g.gamma, 3)],
    ];
    if (d.status === "encerrada") items.unshift(["Resultado realizado", pnlSpan(d.realized_pnl)]);
    $("td-metrics").innerHTML = items.map(([k, v]) => `<div><span>${k}</span><span>${v}</span></div>`).join("");
  }

  function renderLegs(d) {
    const perLeg = d.entry_mode === "pernas";
    $("td-legs").innerHTML = `<thead><tr><th class="l">Lado</th><th class="l">Ticker</th><th class="l">Tipo</th><th>Strike</th><th>Venc.</th><th>Qtd</th>
      <th>Entrada</th><th>Bid</th><th>Ask</th><th>Mid</th><th>Zerar (natural)</th><th>P&L perna</th><th>IV</th><th>Último tick</th><th class="l">Qualidade</th></tr></thead><tbody>` +
      d.legs.map((l) => `<tr><td class="l">${l.side === "compra" ? "Compra" : "Venda"}</td><td class="l">${esc(l.symbol)}</td>
        <td class="l">${l.option_type} ${l.exercise_style === "american" ? "americana" : "europeia"}</td><td>${FMT.price(l.strike)}</td><td>${FMT.date(l.expiration)}</td><td>${FMT.int(l.quantity)}</td>
        <td>${perLeg ? FMT.price(l.entry_price_used) : "—"}</td><td>${FMT.price(l.bid)}</td><td>${FMT.price(l.ask)}</td><td>${FMT.price(l.mid)}</td>
        <td>${FMT.price(l.close_price_natural)}</td><td>${perLeg ? pnlSpan(l.pnl_natural) : "—"}</td><td>${FMT.pct(l.iv)}</td>
        <td>${FMT.datetime(l.quote_time)} <span class="muted">(${FMT.age(l.quote_age_seconds)})</span></td>
        <td class="l">${l.flags.length ? `<span class="badge bad">${esc(l.flags.join(", "))}</span>` : '<span class="badge ok">ok</span>'}</td></tr>`).join("") + "</tbody>" +
      (perLeg ? "" : `<caption class="muted small" style="caption-side:bottom;text-align:left">${d.entry_mode === "agregado" ? "Grupo agregado: P&L só no total." : "Só o preço líquido foi informado: P&L por perna indisponível (informe o preço de cada perna para vê-lo)."}</caption>`);
  }

  // ---------- preferências ----------
  function prefs() {
    return { vol: $("trk-vol").value, auto: $("trk-auto").checked, closed: $("trk-closed").checked };
  }
  function applyPrefs(p) {
    if (p.vol !== undefined) $("trk-vol").value = p.vol;
    $("trk-auto").checked = !!p.auto;
    $("trk-closed").checked = !!p.closed;
    setAuto();
  }

  return { activate, prefs, applyPrefs, prefillFromAnalysis };
})();
