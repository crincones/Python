// Gráfico de payoff em SVG: payoff exato no vencimento + valor teórico (modelo) na data simulada.
const Payoff = (() => {
  const NS = "http://www.w3.org/2000/svg";
  const M = { l: 78, r: 16, t: 54, b: 38 };
  const COLORS = {
    expiry: "#1d2330", model: "#1f5fbf", zero: "#667085", spot: "#1d2330",
    target: "#7a2fc0", strike: "#98a2b3", be: "#157a3c", beModel: "#1f5fbf",
    profit: "rgba(21,122,60,0.13)", loss: "rgba(180,35,24,0.11)",
  };

  function el(tag, attrs, text) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function niceTicks(lo, hi, count) {
    const span = hi - lo || 1;
    const raw = span / count;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= count) || 10 * mag;
    const out = [];
    for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10));
    return out;
  }

  // Divide a curva nos cruzamentos com zero para preencher lucro/prejuízo sem invadir o eixo.
  function withCrossings(xs, ys) {
    const px = [xs[0]], py = [ys[0]];
    for (let i = 1; i < xs.length; i++) {
      const a = ys[i - 1], b = ys[i];
      if (a * b < 0) {
        const x = xs[i - 1] + (xs[i] - xs[i - 1]) * (-a / (b - a));
        px.push(x); py.push(0);
      }
      px.push(xs[i]); py.push(ys[i]);
    }
    return [px, py];
  }

  function render(container, d, dateIndex, tooltip) {
    container.innerHTML = "";
    const W = container.clientWidth || 700, H = container.clientHeight || 380;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, "font-size": 11, "font-family": "inherit" });
    container.appendChild(svg);
    const sim = d.simulation;
    const xs = sim.spots, ye = sim.expiry_pnl;
    const sel = sim.dates.length ? sim.dates[dateIndex] : null;
    const showModel = sel && sel.business_days_left > 0;
    const ym = showModel ? sel.pnl : null;

    // Escala fixa para a estrutura inteira (vencimento + todas as datas simuladas): ao arrastar
    // o controle de tempo o gráfico não muda de escala a cada dia.
    if (!sim._yrange) {
      let lo = Math.min(0, ...ye), hi = Math.max(0, ...ye);
      for (const day of sim.dates) { lo = Math.min(lo, ...day.pnl); hi = Math.max(hi, ...day.pnl); }
      sim._yrange = [lo, hi];
    }
    let [ylo, yhi] = sim._yrange;
    const pad = (yhi - ylo) * 0.12 || 1;
    ylo -= pad; yhi += pad;
    const x0 = xs[0], x1 = xs[xs.length - 1];
    const X = (v) => M.l + ((v - x0) / (x1 - x0)) * (W - M.l - M.r);
    const Y = (v) => M.t + ((yhi - v) / (yhi - ylo)) * (H - M.t - M.b);

    // Grade e eixos
    const g = el("g", {});
    svg.appendChild(g);
    for (const t of niceTicks(ylo, yhi, 6)) {
      g.appendChild(el("line", { x1: M.l, x2: W - M.r, y1: Y(t), y2: Y(t), stroke: "#eef0f4" }));
      g.appendChild(el("text", { x: M.l - 6, y: Y(t) + 4, "text-anchor": "end", fill: "#667085" }, FMT.brl(t)));
    }
    for (const t of niceTicks(x0, x1, 9)) {
      g.appendChild(el("line", { x1: X(t), x2: X(t), y1: H - M.b, y2: H - M.b + 4, stroke: "#667085" }));
      g.appendChild(el("text", { x: X(t), y: H - M.b + 16, "text-anchor": "middle", fill: "#667085" }, FMT.price(t)));
    }
    g.appendChild(el("text", { x: (M.l + W - M.r) / 2, y: H - 4, "text-anchor": "middle", fill: "#667085" }, "Preço do ativo-objeto (R$)"));

    // Regiões de lucro e prejuízo (payoff no vencimento)
    const [px, py] = withCrossings(xs, ye);
    const area = (sign) => {
      let p = `M ${X(px[0])} ${Y(0)}`;
      for (let i = 0; i < px.length; i++) p += ` L ${X(px[i])} ${Y(sign > 0 ? Math.max(py[i], 0) : Math.min(py[i], 0))}`;
      return p + ` L ${X(px[px.length - 1])} ${Y(0)} Z`;
    };
    svg.appendChild(el("path", { d: area(1), fill: COLORS.profit }));
    svg.appendChild(el("path", { d: area(-1), fill: COLORS.loss }));
    svg.appendChild(el("line", { x1: M.l, x2: W - M.r, y1: Y(0), y2: Y(0), stroke: COLORS.zero, "stroke-width": 1.2 }));

    // Rótulos das regiões (texto, não só cor)
    const iMax = ye.indexOf(Math.max(...ye)), iMin = ye.indexOf(Math.min(...ye));
    if (ye[iMax] > 0) svg.appendChild(el("text", { x: Math.min(X(xs[iMax]), W - M.r - 40), y: Y(ye[iMax] / 2) + 4, "text-anchor": "middle", fill: "#157a3c", "font-weight": 600 }, "LUCRO"));
    if (ye[iMin] < 0) svg.appendChild(el("text", { x: Math.max(X(xs[iMin]), M.l + 40), y: Y(ye[iMin] / 2) + 4, "text-anchor": "middle", fill: "#b42318", "font-weight": 600 }, "PREJUÍZO"));

    // Linhas verticais: strikes, spot, alvo, breakevens
    // Rótulos no topo distribuídos em linhas para não se sobreporem.
    const rowsEnd = [];
    const vline = (x, color, dash, label, width = 1.2) => {
      if (!FMT.ok(x) || x < x0 || x > x1) return;
      svg.appendChild(el("line", { x1: X(x), x2: X(x), y1: M.t, y2: H - M.b, stroke: color, "stroke-width": width, "stroke-dasharray": dash || "none" }));
      const half = label.length * 3.1 + 4;
      const cx = Math.min(Math.max(X(x), M.l + half), W - M.r - half);
      let r = rowsEnd.findIndex((end) => end < cx - half);
      if (r < 0) { r = rowsEnd.length; rowsEnd.push(0); }
      rowsEnd[r] = cx + half;
      svg.appendChild(el("text", { x: cx, y: 11 + r * 12, "text-anchor": "middle", fill: color, "font-weight": 600 }, label));
    };
    const marks = [];
    for (const leg of d.legs) {
      marks.push([leg.strike, COLORS.strike, "2 3", `K ${leg.side === "compra" ? "C" : "V"} ${FMT.price(leg.strike)}`]);
    }
    for (const be of d.breakevens || []) marks.push([be, COLORS.be, "7 3 2 3", `BE venc. ${FMT.price(be)}`, 1.6]);
    marks.push([d.spot, COLORS.spot, "none", `Atual ${FMT.price(d.spot)}`, 1.4]);
    if (d.target_price) marks.push([d.target_price, COLORS.target, "6 4", `Alvo ${FMT.price(d.target_price)}`, 1.4]);
    marks.sort((a, b) => a[0] - b[0]).forEach((m) => vline(...m));

    // Curvas
    const path = (ys) => ys.map((y, i) => `${i ? "L" : "M"} ${X(xs[i])} ${Y(y)}`).join(" ");
    svg.appendChild(el("path", { d: path(ye), fill: "none", stroke: COLORS.expiry, "stroke-width": 2.4 }));
    if (showModel) {
      svg.appendChild(el("path", { d: path(ym), fill: "none", stroke: COLORS.model, "stroke-width": 2, "stroke-dasharray": "6 4" }));
      for (const be of sel.breakevens) {
        svg.appendChild(el("circle", { cx: X(be), cy: Y(0), r: 4, fill: "#fff", stroke: COLORS.beModel, "stroke-width": 2 }));
      }
    }

    // Lucro e perda máximos (texto)
    if (FMT.ok(d.max_profit)) {
      svg.appendChild(el("text", { x: W - M.r - 4, y: Y(d.max_profit) - 5, "text-anchor": "end", fill: "#157a3c" }, `Lucro máx. ${FMT.brl(d.max_profit)}`));
    }
    if (FMT.ok(d.max_loss)) {
      svg.appendChild(el("text", { x: M.l + 4, y: Y(-d.max_loss) + 14, fill: "#b42318" }, `Perda máx. ${FMT.brl(-d.max_loss)}`));
    }

    // Interação: cursor e tooltip
    const cross = el("line", { y1: M.t, y2: H - M.b, stroke: "#98a2b3", visibility: "hidden" });
    svg.appendChild(cross);
    const hit = el("rect", { x: M.l, y: M.t, width: W - M.l - M.r, height: H - M.t - M.b, fill: "transparent" });
    svg.appendChild(hit);
    hit.addEventListener("mousemove", (ev) => {
      const r = svg.getBoundingClientRect();
      const sx = ((ev.clientX - r.left) / r.width) * W;
      const price = x0 + ((sx - M.l) / (W - M.l - M.r)) * (x1 - x0);
      let i = 0;
      while (i < xs.length - 1 && xs[i + 1] < price) i++;
      const f = (xs[i + 1] - xs[i]) ? (price - xs[i]) / (xs[i + 1] - xs[i]) : 0;
      const lerp = (ys) => ys[i] + (ys[Math.min(i + 1, ys.length - 1)] - ys[i]) * f;
      cross.setAttribute("x1", sx); cross.setAttribute("x2", sx); cross.setAttribute("visibility", "visible");
      const ve = lerp(ye);
      let html = `Ativo: <b>${FMT.price(price)}</b><br>No vencimento: <b class="${ve >= 0 ? "pos" : "neg"}">${FMT.signedBrl(ve)}</b>`;
      if (showModel) {
        const vm = lerp(ym);
        html += `<br>Em ${FMT.date(sel.date)} (modelo): <b class="${vm >= 0 ? "pos" : "neg"}">${FMT.signedBrl(vm)}</b>`;
      }
      tooltip.innerHTML = html;
      tooltip.hidden = false;
      tooltip.style.left = ev.clientX + 14 + "px";
      tooltip.style.top = ev.clientY + 10 + "px";
    });
    hit.addEventListener("mouseleave", () => { tooltip.hidden = true; cross.setAttribute("visibility", "hidden"); });
  }

  function legend(showModel, sel, expiryLabel) {
    const items = [
      `<span><i style="border-color:${COLORS.expiry}"></i>${esc(expiryLabel || "Payoff no vencimento (exato)")}</span>`,
      showModel ? `<span><i style="border-color:${COLORS.model};border-top-style:dashed"></i>Valor teórico em ${FMT.date(sel.date)} (modelo)</span>` : "",
      `<span><i class="box" style="background:${COLORS.profit}"></i>Lucro</span>`,
      `<span><i class="box" style="background:${COLORS.loss}"></i>Prejuízo</span>`,
      `<span><i style="border-color:${COLORS.be};border-top-style:dashed"></i>Breakeven no venc.</span>`,
      showModel ? `<span>○ Equilíbrio na data (modelo)</span>` : "",
    ];
    return items.join("");
  }

  return { render, legend };
})();
