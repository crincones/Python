// Ativos com estrela ("seguimento"): lista local em data/favoritos.json via /api/watchlist.
// A estrela fica no gráfico do ativo; a lista, num painel recolhível da aba Heatmap.
const Watch = (() => {
  let items = [];
  const subs = [];
  const emit = () => subs.forEach((fn) => { try { fn(items); } catch (e) { console.error(e); } });

  async function call(method, ticker, body) {
    const r = await fetch(`/api/watchlist${ticker ? "/" + encodeURIComponent(ticker) : ""}`, {
      method, headers: body ? { "Content-Type": "application/json" } : undefined, body: body ? JSON.stringify(body) : undefined,
    });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `HTTP ${r.status}`);
    return r.json();
  }

  async function load() {
    try { items = (await call("GET")).items; } catch (e) { console.warn("Seguimento indisponível:", e.message); }
    emit();
  }

  const has = (t) => items.some((i) => i.ticker === t);

  async function toggle(ticker, price) {
    if (has(ticker)) await call("DELETE", ticker);
    else await call("PUT", ticker, { price: FMT.ok(price) && price > 0 ? price : null });
    await load();
    return has(ticker);
  }

  async function remove(ticker) {
    await call("DELETE", ticker);
    await load();
  }

  return { load, has, toggle, remove, items: () => items, on: (fn) => subs.push(fn) };
})();
