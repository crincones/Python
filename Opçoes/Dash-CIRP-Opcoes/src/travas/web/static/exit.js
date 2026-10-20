// Quanto custaria sair (zerar) na data simulada e o saldo que ficaria. Usa as mesmas curvas do
// gráfico de payoff (vindas da API): valor para zerar = P&L − fluxo de entrada + custos.
// Antes do vencimento é valor teórico (modelo); no vencimento, o valor intrínseco (exato).
const ExitPanel = (() => {
  const custom = new WeakMap(); // host → preço digitado pelo usuário

  // P&L interpolado no preço `price` para a data `index` (ou no vencimento).
  function pnlAt(sim, index, price) {
    const sel = sim.dates.length ? sim.dates[index] : null;
    const atExpiry = !sel || sel.business_days_left === 0;
    const ys = atExpiry ? sim.expiry_pnl : sel.pnl;
    const xs = sim.spots;
    if (!ys || !ys.length || !FMT.ok(price) || price < xs[0] || price > xs[xs.length - 1]) return null;
    let i = 0;
    while (i < xs.length - 2 && xs[i + 1] < price) i++;
    const f = (price - xs[i]) / (xs[i + 1] - xs[i] || 1);
    return { pnl: ys[i] + (ys[i + 1] - ys[i]) * f, atExpiry, sel };
  }

  const flowText = (v) => !FMT.ok(v) ? "—" : Math.abs(v) < 0.005 ? "zero a zero"
    : v > 0 ? `<span class="pos">recebe ${FMT.brl(v)}</span>` : `<span class="neg">paga ${FMT.brl(-v)}</span>`;

  // ctx: { sim, index, spot, target, units (para o valor por unidade, opcional) }
  // A curva traz entry_cash/costs/exit_spread_cost da API (já escalados quando é o caso).
  function rowHtml(ctx, label, price) {
    const sim = ctx.sim;
    const r = pnlAt(sim, ctx.index, price);
    if (!r) return `<tr><td class="l">${label}</td><td>${FMT.price(price)}</td><td colspan="4" class="muted l">fora da faixa do gráfico</td></tr>`;
    const exit = r.pnl - sim.entry_cash + (sim.costs || 0);
    const spread = !r.atExpiry && FMT.ok(sim.exit_spread_cost) ? sim.exit_spread_cost : null;
    const net = spread === null ? null : r.pnl - spread;
    const perUnit = ctx.units ? ` <span class="muted">(${FMT.price(Math.abs(exit) / ctx.units)}/un.)</span>` : "";
    const cls = (v) => (v >= 0 ? "pos" : "neg");
    return `<tr><td class="l">${label}</td><td>${FMT.price(price)}</td><td>${flowText(exit)}${perUnit}</td>
      <td><b class="${cls(r.pnl)}">${FMT.signedBrl(r.pnl)}</b></td>
      <td>${spread === null ? (r.atExpiry ? '<span class="muted">sem spread</span>' : "—") : FMT.brl(spread)}</td>
      <td>${net === null ? "—" : `<span class="${cls(net)}">${FMT.signedBrl(net)}</span>`}</td></tr>`;
  }

  function render(host, ctx) {
    if (!host) return;
    const sim = ctx.sim;
    if (!sim || !FMT.ok(sim.entry_cash) || !sim.expiry_pnl || !sim.expiry_pnl.length) { host.innerHTML = ""; return; }
    const sel = sim.dates.length ? sim.dates[ctx.index] : null;
    const atExpiry = !sel || sel.business_days_left === 0;
    const when = sel
      ? `${FMT.date(sel.date)} · ${sel.business_days_left} du até o vencimento${atExpiry ? " (no vencimento: valor intrínseco, exato)" : " (valor teórico do modelo)"}`
      : "no vencimento (valor intrínseco, exato)";
    if (!custom.has(host)) custom.set(host, null);
    const saved = custom.get(host);
    const rows = () => [
      rowHtml(ctx, "Ativo no preço atual", ctx.spot),
      FMT.ok(ctx.target) ? rowHtml(ctx, "Preço-alvo", ctx.target) : "",
      FMT.ok(custom.get(host)) ? rowHtml(ctx, "Preço informado", custom.get(host)) : "",
    ].join("");
    const spreadNote = FMT.ok(sim.exit_spread_cost)
      ? `Spread de saída = meia largura atual do book de cada perna (${FMT.brl(sim.exit_spread_cost)} no total); perto do vencimento ou com o ativo longe dos strikes costuma ser maior.`
      : "Sem book em alguma perna: spread de saída não estimável.";
    host.innerHTML = `<div class="exit-box">
      <div class="exit-head"><b>Sair na data simulada</b> <span class="muted small">${esc(when)}</span>
        <label class="small exit-price">outro preço do ativo <input type="number" step="0.01" min="0" value="${FMT.ok(saved) ? saved : ""}" aria-label="Preço do ativo para simular a saída"></label></div>
      <div class="table-wrap"><table class="legs small"><thead><tr><th class="l">Cenário</th><th>Ativo</th><th>Para zerar</th><th>Saldo (teórico)</th><th>Spread de saída</th><th>Saldo pelo natural</th></tr></thead>
      <tbody>${rows()}</tbody></table></div>
      <p class="muted small">Para zerar: "recebe" = crédito ao desmontar, "paga" = débito. Saldo = resultado total da operação, com a entrada e os custos já descontados. ${spreadNote} Valores antes do vencimento dependem do modelo e das premissas; não são preço garantido.</p>
    </div>`;
    const input = host.querySelector("input");
    input.addEventListener("input", () => {
      const v = input.value === "" ? null : Number(input.value);
      custom.set(host, FMT.ok(v) && v > 0 ? v : null);
      host.querySelector("tbody").innerHTML = rows();
    });
  }

  return { render, pnlAt };
})();
