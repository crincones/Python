// Relatório das operações encerradas (aba Acompanhamento): estatísticas calculadas no backend
// (/api/tracking/report) e gráficos em canvas. Só usa os registros; não consulta o MT5.
const Report = (() => {
  const $ = (id) => document.getElementById(id);
  const st = { data: null, period: "all", group: "", open: false, sort: { key: "exit_date", dir: -1 }, ready: false, token: 0 };
  const POS = "#157a3c", NEG = "#b42318", POS_FILL = "rgba(21,122,60,.16)", NEG_FILL = "rgba(180,35,24,.18)", GRID = "#e4e7ec", AXIS = "#667085";
  const signed = (v) => `<span class="${FMT.ok(v) ? (v > 0 ? "pos" : v < 0 ? "neg" : "") : "muted"}">${FMT.signedBrl(v)}</span>`;
  const num2 = (v) => (FMT.ok(v) ? FMT.num(v, 2) : "—");
  const iso = (d) => d.toLocaleDateString("sv-SE", { timeZone: "America/Sao_Paulo" });
  const REASONS = { zerada: "Zerada", vencida: "Vencida", exercida: "Exercida" };

  // ---------- período ----------
  function range() {
    const today = new Date(iso(new Date()) + "T12:00:00");
    const back = (months) => { const d = new Date(today); d.setMonth(d.getMonth() - months); d.setDate(d.getDate() + 1); return iso(d); };
    switch (st.period) {
      case "ytd": return { start: `${today.getFullYear()}-01-01`, end: null };
      case "mtd": return { start: iso(today).slice(0, 8) + "01", end: null };
      case "12m": return { start: back(12), end: null };
      case "6m": return { start: back(6), end: null };
      case "3m": return { start: back(3), end: null };
      case "custom": return { start: $("rp-start").value || null, end: $("rp-end").value || null };
      default: return { start: null, end: null };
    }
  }
  function query() {
    const r = range(), q = new URLSearchParams();
    if (r.start) q.set("start", r.start);
    if (r.end) q.set("end", r.end);
    if (st.group) q.set("group", st.group);
    return q;
  }

  // ---------- carga ----------
  async function load() {
    const token = ++st.token;
    Busy.show($("rp-host"), "Calculando o relatório…");
    try {
      const d = await App.api(`/api/tracking/report?${query()}`);
      if (token !== st.token) return;
      st.data = d;
      render();
    } catch (e) {
      if (token === st.token) $("rp-body").innerHTML = `<p class="neg">Erro ao gerar o relatório: ${esc(e.message)}</p>`;
    } finally {
      Busy.hide($("rp-host"));
    }
  }

  function refresh() { if (st.open) load(); }

  function setSummary(totals) {
    if (!totals) return;
    $("rp-summary").innerHTML = totals.closed_count
      ? `· ${totals.closed_count} encerrada(s) · realizado ${signed(totals.realized_pnl)}`
      : "· nenhuma encerrada ainda";
  }

  // ---------- desenho ----------
  const kpi = (label, value, tip, cls = "") => `<div class="rp-kpi ${cls}" ${tip ? `data-tip="${esc(tip)}" tabindex="0"` : ""}><span>${label}</span><b>${value}</b></div>`;
  const row = (label, value, tip) => `<div ${tip ? `data-tip="${esc(tip)}"` : ""}><span>${label}</span><span>${value}</span></div>`;

  function render() {
    const d = st.data;
    if (!d) return;
    const groupSel = $("rp-group");
    const groups = ["", ...d.groups];
    if (groupSel.options.length !== groups.length || [...groupSel.options].some((o, i) => o.value !== groups[i])) {
      groupSel.innerHTML = groups.map((g) => `<option value="${esc(g)}">${g ? esc(g) : "Todos"}</option>`).join("");
    }
    groupSel.value = st.group;
    const s = d.stats;
    if (!s.trades) {
      $("rp-body").innerHTML = `<p class="muted">Nenhuma operação encerrada ${st.period !== "all" || st.group ? "no filtro escolhido" : "ainda"}. Use "Encerrar" numa estrutura para registrar a saída.</p>`;
      return;
    }
    const period = s.first_exit ? `${FMT.date(s.first_exit)} a ${FMT.date(s.last_exit)}` : "—";
    $("rp-body").innerHTML = `
      <div class="rp-kpis">
        ${kpi("P&L líquido", signed(s.net_pnl), "Soma do P&L realizado (após custos informados)", s.net_pnl >= 0 ? "good" : "bad")}
        ${kpi("Operações", `${s.trades}`, `${s.wins} vencedora(s), ${s.losses} perdedora(s), ${s.breakeven} no zero`)}
        ${kpi("Taxa de acerto", FMT.pct(s.win_rate, 1), "Operações com P&L > 0 ÷ total")}
        ${kpi("Fator de lucro", num2(s.profit_factor), "Lucro bruto ÷ |prejuízo bruto|. Acima de 1: ganhos superam perdas. Sem perdas: indefinido")}
        ${kpi("Expectativa", signed(s.avg_trade), "P&L médio por operação = acerto × ganho médio + erro × perda média")}
        ${kpi("Drawdown máx.", FMT.ok(s.max_drawdown) && s.max_drawdown > 0 ? `<span class="neg">${FMT.brl(-s.max_drawdown)}</span>` : FMT.brl(0), "Maior queda do P&L acumulado desde um pico (ordem das saídas)")}
      </div>
      <div class="rp-charts">
        <figure class="rp-chart wide"><figcaption>P&L acumulado e drawdown <span class="muted small">(por operação, na ordem de saída)</span></figcaption><canvas id="rp-equity"></canvas></figure>
        <figure class="rp-chart"><figcaption>P&L por mês <span class="muted small">(mês da saída)</span></figcaption><canvas id="rp-monthly"></canvas></figure>
        <figure class="rp-chart"><figcaption>P&L por operação</figcaption><canvas id="rp-trades"></canvas></figure>
        <figure class="rp-chart"><figcaption>Distribuição do R <span class="muted small" data-tip="R = P&L ÷ perda máxima da estrutura na entrada. −1R = perdeu o risco todo.">(P&L ÷ perda máx.) ⓘ</span></figcaption><canvas id="rp-hist"></canvas></figure>
        <figure class="rp-chart"><figcaption>Resultado por ativo</figcaption><canvas id="rp-und"></canvas></figure>
      </div>
      <div class="rp-stats">
        <section><h4>Resultado</h4><div class="metrics one">
          ${row("Lucro bruto", signed(s.gross_profit), "Soma das operações vencedoras")}
          ${row("Prejuízo bruto", signed(s.gross_loss), "Soma das operações perdedoras")}
          ${row("P&L líquido", signed(s.net_pnl))}
          ${row("Custos informados", FMT.brl(s.costs_total), "Corretagem/emolumentos registrados na entrada e na saída (já descontados do P&L)")}
          ${row("Retorno sobre o risco", FMT.pct(s.return_on_risk, 1), "P&L líquido ÷ soma das perdas máximas das operações")}
          ${row("Risco total assumido", FMT.brl(s.total_risk), "Soma das perdas máximas na entrada")}
        </div></section>
        <section><h4>Acerto e tamanho</h4><div class="metrics one">
          ${row("Vencedoras / perdedoras / zero", `${s.wins} / ${s.losses} / ${s.breakeven}`)}
          ${row("Ganho médio", signed(s.avg_win))}
          ${row("Perda média", signed(s.avg_loss))}
          ${row("Payoff (ganho médio ÷ perda média)", num2(s.payoff_ratio), "Quanto se ganha, em média, para cada R$ 1 perdido em média")}
          ${row("Maior ganho", signed(s.largest_win))}
          ${row("Maior perda", signed(s.largest_loss))}
        </div></section>
        <section><h4>Risco e consistência</h4><div class="metrics one">
          ${row("Drawdown máx.", FMT.ok(s.max_drawdown) && s.max_drawdown > 0 ? `${FMT.brl(-s.max_drawdown)} <span class="muted small">${FMT.date(s.max_drawdown_from)} → ${FMT.date(s.max_drawdown_to)}</span>` : "—")}
          ${row("Fator de recuperação", num2(s.recovery_factor), "P&L líquido ÷ drawdown máximo")}
          ${row("R médio", num2(s.avg_r), "Média de P&L ÷ perda máxima por operação")}
          ${row("SQN", num2(s.sqn), "System Quality Number = √n × média(R) ÷ desvio-padrão(R). Com poucas operações, pouco significativo")}
          ${row("Sequência máx. de ganhos", s.max_consecutive_wins)}
          ${row("Sequência máx. de perdas", s.max_consecutive_losses)}
        </div></section>
        <section><h4>Tempo</h4><div class="metrics one">
          ${row("Período (saídas)", period)}
          ${row("Dias médios na operação", FMT.ok(s.avg_days_held) ? FMT.num(s.avg_days_held, 1) : "—", "Dias corridos entre entrada e saída")}
          ${row("… nas vencedoras", FMT.ok(s.avg_days_held_wins) ? FMT.num(s.avg_days_held_wins, 1) : "—")}
          ${row("… nas perdedoras", FMT.ok(s.avg_days_held_losses) ? FMT.num(s.avg_days_held_losses, 1) : "—")}
          ${s.without_pnl ? row("Sem P&L calculável", `<span class="neg">${s.without_pnl}</span>`, "Encerradas cujo P&L não pôde ser calculado; ficam fora das estatísticas") : ""}
        </div></section>
      </div>
      <div class="rp-breakdowns">
        ${breakdown("Por estrutura", d.by_kind)}
        ${breakdown("Por sentido", d.by_flow)}
        ${breakdown("Por motivo de saída", d.by_reason)}
        ${breakdown("Por grupo", d.by_group)}
        ${breakdown("Por ativo", d.by_underlying)}
      </div>
      <h4 class="rp-h">Operações encerradas</h4>
      <div class="table-wrap"><table class="rp-table" id="rp-trades-table"></table></div>
      <p class="muted small">${esc(d.methodology)}</p>`;
    renderTrades();
    drawCharts();
  }

  function breakdown(title, rows) {
    if (!rows || !rows.length) return "";
    const max = Math.max(...rows.map((r) => Math.abs(r.net_pnl)), 1e-9);
    return `<section class="rp-bd"><h4>${title}</h4><table><thead><tr><th class="l"></th><th>Ops</th><th>Acerto</th><th>P&L</th><th>Médio</th></tr></thead><tbody>
      ${rows.map((r) => `<tr><td class="l">${esc(r.label)}</td><td>${r.trades}</td><td>${FMT.pct(r.win_rate, 0)}</td>
        <td class="rp-bar-cell"><span class="rp-bar ${r.net_pnl >= 0 ? "p" : "n"}" style="width:${(Math.abs(r.net_pnl) / max) * 100}%"></span><span class="rp-bar-v">${signed(r.net_pnl)}</span></td>
        <td>${signed(r.avg_pnl)}</td></tr>`).join("")}</tbody></table></section>`;
  }

  const COLS = [
    ["exit_date", "Saída", (t) => FMT.date(t.exit_date)],
    ["entry_date", "Entrada", (t) => FMT.date(t.entry_date)],
    ["days_held", "Dias", (t) => (FMT.ok(t.days_held) ? t.days_held : "—")],
    ["name", "Nome", (t) => `${tickerIcon(t.underlying, 16)}${esc(t.name || "")}`, "l"],
    ["kind_label", "Estrutura", (t) => esc(t.kind_label || ""), "l"],
    ["group", "Grupo", (t) => esc(t.group || ""), "l"],
    ["reason", "Motivo", (t) => esc(REASONS[t.reason] || t.reason || "—"), "l"],
    ["max_loss", "Perda máx.", (t) => FMT.brl(t.max_loss)],
    ["costs", "Custos", (t) => FMT.brl(t.costs)],
    ["pnl", "P&L", (t) => signed(t.pnl)],
    ["r_multiple", "R", (t) => (FMT.ok(t.r_multiple) ? `<span class="${t.r_multiple >= 0 ? "pos" : "neg"}">${FMT.num(t.r_multiple, 2)}R</span>` : "—")],
  ];

  function renderTrades() {
    const { key, dir } = st.sort;
    const rows = [...st.data.trades].sort((a, b) => {
      const x = a[key], y = b[key];
      if (x === y) return 0;
      if (x === null || x === undefined) return 1;
      if (y === null || y === undefined) return -1;
      return (x < y ? -1 : 1) * dir;
    });
    $("rp-trades-table").innerHTML =
      `<thead><tr>${COLS.map(([k, label, , cls]) => `<th class="${cls || ""} sortable" data-k="${k}">${label}${k === key ? (dir > 0 ? " ▲" : " ▼") : ""}</th>`).join("")}</tr></thead>
       <tbody>${rows.map((t) => `<tr>${COLS.map(([, , fn, cls]) => `<td class="${cls || ""}">${fn(t)}</td>`).join("")}</tr>`).join("")}</tbody>`;
  }

  // ---------- gráficos (canvas) ----------
  function prep(cv) {
    const dpr = window.devicePixelRatio || 1;
    const w = cv.clientWidth, h = cv.clientHeight;
    cv.width = Math.round(w * dpr);
    cv.height = Math.round(h * dpr);
    const c = cv.getContext("2d");
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    c.clearRect(0, 0, w, h);
    c.font = `11px ${getComputedStyle(document.body).fontFamily}`;
    c.textBaseline = "middle";
    return { c, w, h };
  }

  function niceTicks(min, max, count = 5) {
    if (min === max) { min -= 1; max += 1; }
    const raw = (max - min) / count, mag = 10 ** Math.floor(Math.log10(raw));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || 10 * mag;
    const ticks = [];
    for (let v = Math.floor(min / step) * step; v <= max + step * 1e-9; v += step) ticks.push(Math.abs(v) < step * 1e-9 ? 0 : v);
    if (ticks[ticks.length - 1] < max) ticks.push(ticks[ticks.length - 1] + step);
    return ticks;
  }

  const shortBrl = (v) => {
    const a = Math.abs(v);
    if (a >= 1e6) return `${FMT.num(v / 1e6, 1)} mi`;
    if (a >= 1e4) return `${FMT.num(v / 1e3, 0)} mil`;
    if (a >= 1e3) return `${FMT.num(v / 1e3, 1)} mil`;
    return FMT.num(v, a >= 100 ? 0 : a >= 10 ? 0 : 1);
  };

  function yAxis(c, ticks, y, left, right, fmt) {
    c.textAlign = "right";
    for (const t of ticks) {
      const yy = Math.round(y(t)) + 0.5;
      c.strokeStyle = t === 0 ? "#98a2b3" : GRID;
      c.lineWidth = 1;
      c.beginPath(); c.moveTo(left, yy); c.lineTo(right, yy); c.stroke();
      c.fillStyle = AXIS;
      c.fillText(fmt(t), left - 6, yy);
    }
  }

  function xLabels(c, labels, xOf, bottom, plotW) {
    if (!labels.length) return;
    const widest = Math.max(...labels.map((l) => c.measureText(l).width)) + 10;
    const every = Math.max(1, Math.ceil(labels.length / Math.max(1, Math.floor(plotW / widest))));
    c.textAlign = "center";
    c.fillStyle = AXIS;
    labels.forEach((l, i) => { if (i % every === 0) c.fillText(l, xOf(i), bottom + 12); });
  }

  function bars(cv, items, opts = {}) {
    const { c, w, h } = prep(cv);
    const L = 54, R = 10, T = 10, B = 26;
    const pw = w - L - R, ph = h - T - B;
    const vals = items.map((i) => i.value);
    const ticks = niceTicks(Math.min(0, ...vals), Math.max(0, ...vals), 4);
    const lo = ticks[0], hi = ticks[ticks.length - 1];
    const y = (v) => T + ph * (1 - (v - lo) / (hi - lo));
    yAxis(c, ticks, y, L, w - R, opts.yfmt || shortBrl);
    const slot = pw / Math.max(items.length, 1), bw = Math.max(2, Math.min(42, slot * 0.7));
    const xOf = (i) => L + slot * (i + 0.5);
    cv._hits = [];
    items.forEach((it, i) => {
      const x = xOf(i) - bw / 2, y0 = y(0), y1 = y(it.value);
      c.fillStyle = it.color || (it.value >= 0 ? POS : NEG);
      c.fillRect(x, Math.min(y0, y1), bw, Math.max(1, Math.abs(y1 - y0)));
      cv._hits.push({ x0: L + slot * i, x1: L + slot * (i + 1), tip: it.tip });
    });
    xLabels(c, items.map((i) => i.label), xOf, T + ph, pw);
  }

  function equity(cv, pts) {
    const { c, w, h } = prep(cv);
    const L = 64, R = 12, T = 10, B = 24, gap = 30;
    const pw = w - L - R, total = h - T - B - gap;
    const h1 = total * 0.7, h2 = total - h1, t2 = T + h1 + gap;
    const series = [{ cum: 0, dd: 0, date: null }, ...pts];
    const n = series.length;
    const xOf = (i) => L + (n > 1 ? (pw * i) / (n - 1) : pw / 2);
    // painel de cima: P&L acumulado
    const cums = series.map((p) => p.cum);
    const ticks = niceTicks(Math.min(0, ...cums), Math.max(0, ...cums), 4);
    const lo = ticks[0], hi = ticks[ticks.length - 1];
    const y = (v) => T + h1 * (1 - (v - lo) / (hi - lo));
    yAxis(c, ticks, y, L, w - R, shortBrl);
    const path = () => { c.beginPath(); series.forEach((p, i) => (i ? c.lineTo(xOf(i), y(p.cum)) : c.moveTo(xOf(i), y(p.cum)))); };
    const area = (fill, clipTop) => {
      c.save();
      c.beginPath();
      if (clipTop) c.rect(L, T, pw, y(0) - T); else c.rect(L, y(0), pw, T + h1 - y(0));
      c.clip();
      path(); c.lineTo(xOf(n - 1), y(0)); c.lineTo(xOf(0), y(0)); c.closePath();
      c.fillStyle = fill; c.fill();
      c.restore();
    };
    area(POS_FILL, true);
    area(NEG_FILL, false);
    path(); c.strokeStyle = "#1f5fbf"; c.lineWidth = 2; c.stroke();
    c.fillStyle = "#1f5fbf";
    series.forEach((p, i) => { if (i && n <= 80) { c.beginPath(); c.arc(xOf(i), y(p.cum), 2.5, 0, Math.PI * 2); c.fill(); } });
    // painel de baixo: drawdown
    const dds = series.map((p) => p.dd);
    const ddMin = Math.min(...dds);
    const dTicks = ddMin < 0 ? niceTicks(ddMin, 0, 2) : [0];
    const dlo = dTicks[0] < 0 ? dTicks[0] : -1;
    const y2 = (v) => t2 + h2 * (v / dlo);
    yAxis(c, dTicks.filter((t) => t <= 0), y2, L, w - R, shortBrl);
    c.beginPath(); c.moveTo(xOf(0), y2(0));
    series.forEach((p, i) => c.lineTo(xOf(i), y2(p.dd)));
    c.lineTo(xOf(n - 1), y2(0)); c.closePath();
    c.fillStyle = NEG_FILL; c.fill();
    c.strokeStyle = NEG; c.lineWidth = 1.2;
    c.beginPath(); series.forEach((p, i) => (i ? c.lineTo(xOf(i), y2(p.dd)) : c.moveTo(xOf(i), y2(p.dd)))); c.stroke();
    c.fillStyle = AXIS; c.textAlign = "left";
    c.fillText("Drawdown (queda desde o pico)", L + 4, t2 - 12);
    xLabels(c, series.map((p) => (p.date ? FMT.date(p.date).slice(0, 5) : "início")), xOf, t2 + h2, pw);
    cv._hits = series.map((p, i) => ({
      x0: xOf(i) - pw / Math.max(n - 1, 1) / 2, x1: xOf(i) + pw / Math.max(n - 1, 1) / 2,
      tip: i ? `<b>${esc(p.name || "")}</b> · saída ${FMT.date(p.date)}<br>P&L da operação ${FMT.signedBrl(p.pnl)}<br>Acumulado <b>${FMT.signedBrl(p.cum)}</b><br>Drawdown ${FMT.brl(p.dd)}` : "Início (P&L acumulado 0)",
    }));
  }

  function histogram(cv, rs) {
    if (!rs.length) { const { c, w, h } = prep(cv); c.fillStyle = AXIS; c.textAlign = "center"; c.fillText("Sem R calculável (perda máxima indefinida)", w / 2, h / 2); cv._hits = []; return; }
    const step = 0.25;
    const lo = Math.max(-2, Math.floor(Math.min(...rs) / step) * step), hi = Math.min(5, Math.ceil(Math.max(...rs) / step) * step + (Math.max(...rs) % step === 0 ? step : 0));
    const bins = [];
    for (let b = lo; b < hi - 1e-9; b += step) bins.push({ from: b, to: b + step, n: 0 });
    for (const r of rs) {
      const i = Math.min(bins.length - 1, Math.max(0, Math.floor((Math.min(Math.max(r, lo), hi - 1e-9) - lo) / step)));
      bins[i].n += 1;
    }
    bars(cv, bins.map((b) => ({
      label: `${FMT.num(b.from, 2)}`, value: b.n, color: b.from + step / 2 >= 0 ? POS : NEG,
      tip: `R de ${FMT.num(b.from, 2)} a ${FMT.num(b.to, 2)}: <b>${b.n}</b> operação(ões)`,
    })), { yfmt: (v) => (Number.isInteger(v) ? String(v) : "") });
  }

  function drawCharts() {
    const d = st.data;
    if (!d || !d.stats.trades || !$("rp-equity")) return;
    equity($("rp-equity"), d.equity);
    const monthName = (k) => { const [y, m] = k.split("-"); return `${["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][Number(m) - 1]}/${y.slice(2)}`; };
    bars($("rp-monthly"), d.monthly.map((m) => ({
      label: monthName(m.key), value: m.net_pnl,
      tip: `<b>${monthName(m.key)}</b><br>P&L ${FMT.signedBrl(m.net_pnl)}<br>${m.trades} operação(ões), acerto ${FMT.pct(m.win_rate, 0)}`,
    })));
    const tr = d.trades.filter((t) => FMT.ok(t.pnl));
    bars($("rp-trades"), tr.map((t, i) => ({
      label: String(i + 1), value: t.pnl,
      tip: `<b>${esc(t.name || "")}</b> · ${esc(t.underlying)}<br>${esc(t.kind_label || "")}<br>${FMT.date(t.entry_date)} → ${FMT.date(t.exit_date)}<br>P&L <b>${FMT.signedBrl(t.pnl)}</b>${FMT.ok(t.r_multiple) ? ` (${FMT.num(t.r_multiple, 2)}R)` : ""}`,
    })));
    histogram($("rp-hist"), d.trades.map((t) => t.r_multiple).filter(FMT.ok));
    bars($("rp-und"), d.by_underlying.map((u) => ({
      label: u.key, value: u.net_pnl,
      tip: `<b>${esc(u.key)}</b><br>P&L ${FMT.signedBrl(u.net_pnl)}<br>${u.trades} operação(ões), acerto ${FMT.pct(u.win_rate, 0)}`,
    })));
  }

  function hover(ev) {
    const cv = ev.target;
    if (!(cv instanceof HTMLCanvasElement) || !cv._hits) return;
    const x = ev.clientX - cv.getBoundingClientRect().left;
    const hit = cv._hits.find((hh) => x >= hh.x0 && x < hh.x1);
    const tip = App.tooltip();
    if (!hit || !hit.tip) { tip.hidden = true; return; }
    tip.innerHTML = hit.tip;
    tip.hidden = false;
    const r = tip.getBoundingClientRect();
    tip.style.left = `${Math.min(ev.clientX + 14, window.innerWidth - r.width - 8)}px`;
    tip.style.top = `${Math.min(ev.clientY + 14, window.innerHeight - r.height - 8)}px`;
  }

  // ---------- integração ----------
  function setup() {
    if (st.ready) return;
    st.ready = true;
    const det = $("trk-report");
    det.open = st.open;
    det.addEventListener("toggle", () => {
      st.open = det.open;
      App.savePrefs();
      if (st.open) load();
    });
    $("rp-period").value = st.period;
    document.querySelectorAll(".rp-custom").forEach((el) => { el.hidden = st.period !== "custom"; });
    $("rp-period").addEventListener("change", () => {
      st.period = $("rp-period").value;
      document.querySelectorAll(".rp-custom").forEach((el) => { el.hidden = st.period !== "custom"; });
      App.savePrefs();
      load();
    });
    $("rp-start").addEventListener("change", load);
    $("rp-end").addEventListener("change", load);
    $("rp-group").addEventListener("change", () => { st.group = $("rp-group").value; load(); });
    $("rp-export").addEventListener("click", () => {
      const q = query();
      q.delete("group");
      q.set("scope", "encerradas");
      downloadFile(`/api/tracking/export.csv?${q}`, $("rp-host"), "Gerando CSV…")
        .catch((e) => { $("rp-body").insertAdjacentHTML("afterbegin", `<p class="neg">Exportação falhou: ${esc(e.message)}</p>`); });
    });
    $("rp-body").addEventListener("click", (ev) => {
      const th = ev.target.closest("th[data-k]");
      if (!th) return;
      const k = th.dataset.k;
      st.sort = { key: k, dir: st.sort.key === k ? -st.sort.dir : ["exit_date", "entry_date", "pnl", "r_multiple", "max_loss", "days_held", "costs"].includes(k) ? -1 : 1 };
      renderTrades();
    });
    $("rp-body").addEventListener("mousemove", hover);
    $("rp-body").addEventListener("mouseleave", () => { App.tooltip().hidden = true; });
    let raf = 0, lastW = 0;
    new ResizeObserver(() => {
      const w = $("rp-body").clientWidth;
      if (!st.open || w === lastW) return;
      lastW = w;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(drawCharts);
    }).observe($("rp-body")); // abrir o <details> dispara "toggle", que carrega
  }

  const prefs = () => ({ open: st.open, period: st.period });
  function applyPrefs(p) {
    if (!p) return;
    st.open = !!p.open;
    if (["all", "ytd", "12m", "6m", "3m", "mtd", "custom"].includes(p.period)) st.period = p.period;
  }

  return { setup, refresh, setSummary, prefs, applyPrefs };
})();
