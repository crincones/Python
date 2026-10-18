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

// Indicador de carregamento: camada semitransparente com ícone girando sobre um elemento.
// Contagem por elemento (vários carregamentos simultâneos) e atraso de 150 ms para não piscar
// em respostas instantâneas (cache). Use sempre em pares: show() … finally hide().
const Busy = (() => {
  const state = new WeakMap(); // el → { n, timer, text }
  function show(el, text = "Carregando…") {
    if (!el) return;
    const s = state.get(el) || { n: 0, timer: null };
    s.n += 1;
    s.text = text;
    state.set(el, s);
    el.setAttribute("aria-busy", "true");
    if (s.n === 1) {
      s.timer = setTimeout(() => {
        if (s.n <= 0) return;
        let ov = el.querySelector(":scope > .busy-overlay");
        if (!ov) {
          ov = document.createElement("div");
          ov.className = "busy-overlay";
          ov.setAttribute("role", "status");
          ov.innerHTML = '<div class="busy-box"><span class="spinner" aria-hidden="true"></span><span class="busy-text"></span></div>';
          el.appendChild(ov);
        }
        ov.querySelector(".busy-text").textContent = s.text;
      }, 150);
    } else {
      const t = el.querySelector(":scope > .busy-overlay .busy-text");
      if (t) t.textContent = text;
    }
  }
  function hide(el) {
    if (!el) return;
    const s = state.get(el);
    if (!s) return;
    s.n = Math.max(0, s.n - 1);
    if (s.n === 0) {
      clearTimeout(s.timer);
      const ov = el.querySelector(":scope > .busy-overlay");
      if (ov) ov.remove();
      el.removeAttribute("aria-busy");
    }
  }
  return { show, hide };
})();

// Baixa um arquivo gerado pelo backend mostrando o "carregando" no elemento `host` enquanto isso.
async function downloadFile(url, host, label = "Gerando arquivo…") {
  if (host) Busy.show(host, label);
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
    const name = (/filename="([^"]+)"/.exec(r.headers.get("Content-Disposition") || "") || [])[1] || "arquivo.csv";
    const href = URL.createObjectURL(await r.blob());
    const a = Object.assign(document.createElement("a"), { href, download: name });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(href), 10_000);
  } finally {
    if (host) Busy.hide(host);
  }
}
