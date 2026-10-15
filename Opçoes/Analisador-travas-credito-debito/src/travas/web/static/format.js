// Formatação pt-BR. null/undefined/NaN → "—" (dado ausente nunca vira zero).
const FMT = (() => {
  const nf = (min, max) => new Intl.NumberFormat("pt-BR", { minimumFractionDigits: min, maximumFractionDigits: max });
  const n2 = nf(2, 2), n0 = nf(0, 0), n1 = nf(1, 1);
  const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  const ok = (v) => v !== null && v !== undefined && Number.isFinite(v);
  const dash = "—";
  return {
    ok,
    num: (v, d = 2) => (ok(v) ? nf(d, d).format(v) : dash),
    price: (v) => (ok(v) ? n2.format(v) : dash),
    int: (v) => (ok(v) ? n0.format(v) : dash),
    brl: (v) => (ok(v) ? brl.format(v) : v === Infinity ? "ilimitado" : dash),
    pct: (v, d = 1) => (ok(v) ? nf(d, d).format(v * 100) + "%" : dash),
    ratio: (v) => (ok(v) ? n2.format(v) : dash),
    signedBrl: (v) => (ok(v) ? (v > 0 ? "+" : "") + brl.format(v) : dash),
    date: (iso) => {
      if (!iso) return dash;
      const [y, m, d] = iso.slice(0, 10).split("-");
      return `${d}/${m}/${y}`;
    },
    datetime: (iso) => {
      if (!iso) return dash;
      const t = new Date(iso);
      return t.toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" });
    },
    age: (s) => {
      if (!ok(s)) return dash;
      if (s < 120) return `${n0.format(s)} s`;
      if (s < 7200) return `${n0.format(s / 60)} min`;
      if (s < 172800) return `${n1.format(s / 3600)} h`;
      return `${n0.format(s / 86400)} dias`;
    },
  };
})();

function esc(text) {
  return String(text ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

// Ícone do ativo (servido pela API, baixado sob demanda). Sem ícone, ficam as iniciais.
function tickerIcon(ticker, size = 20) {
  const t = String(ticker || "").toUpperCase();
  if (!t) return "";
  return `<span class="tk" style="width:${size}px;height:${size}px;font-size:${Math.round(size * 0.38)}px" aria-hidden="true">` +
    `<span>${esc(t.slice(0, 2))}</span><img src="/api/icon/${encodeURIComponent(t)}" alt="" decoding="async" onerror="this.remove()"></span>`;
}
