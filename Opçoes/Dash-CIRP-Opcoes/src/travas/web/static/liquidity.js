// Aba "Liquidez de Opções": ranking dos ativos pelo volume financeiro médio das opções nos
// últimos pregões (fechamento oficial da B3) e exportação em CSV.
const Liquidity = (() => {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  // Ordenação: coluna e sentido; null = sentido padrão da coluna (o do backend em SORT_KEYS).
  const st = { ready: false, data: null, loading: false, sort: "rank", desc: null };
  const COLS = [
    { key: "rank", label: "#", tip: "Posição pelo volume financeiro das opções", defaultDesc: false },
    { key: "ticker", label: "Ativo", l: true, defaultDesc: false },
    { key: "turnover", label: "Volume financeiro/dia", tip: "Volume financeiro médio por pregão das OPÇÕES do ativo (prêmio negociado), somando todas as séries (calls e puts)", defaultDesc: true },
    { key: "deals", label: "Negócios/dia", tip: "Número médio de negócios por pregão em opções do ativo", defaultDesc: true },
    { key: "book", label: "Book perto do dinheiro", tip: "Do snapshot mais recente do servidor: séries com strike a até ±10% do spot; spread mediano (ask − bid)/mid das que têm bid e ask, e quantas têm book. Menor spread = mais fácil montar e desmontar a trava. Só ativos coletados no snapshot", defaultDesc: false },
    { key: "ivhv", label: "IV/HV", tip: "Opções baratas ou caras: IV ATM do 1º vencimento mensal (com IV calculável) ÷ vol histórica do ativo (janela = pregões até o vencimento). Abaixo de 0,90 = barata, acima de 1,20 = cara. Passe o mouse sobre o valor para ver os 3 próximos vencimentos mensais. Indicativo: eventos (balanço, dividendos) podem justificar IV alta", defaultDesc: false },
    { key: "series", label: "Séries B3", tip: "Séries de opções vigentes na B3", defaultDesc: true },
    { key: "mt5", label: "MT5", tip: "Opções com cotação no MT5 da corretora logada", defaultDesc: true },
  ];
  const sortParams = () => `sort=${st.sort}${st.desc === null ? "" : `&desc=${st.desc}`}`;
  const csvParams = () => `sessions=${$("lq-sessions").value}&top=${$("lq-top").value}&${sortParams()}`;
  const mi = (v) => `R$ ${FMT.num(v / 1e6, 1)} mi`;

  function setup() {
    if (st.ready) return;
    st.ready = true;
    $("lq-sessions").addEventListener("change", () => { App.savePrefs(); load(); });
    $("lq-top").addEventListener("change", () => { App.savePrefs(); render(); });
    $("lq-csv").addEventListener("click", () => {
      downloadFile(`/api/liquidity.csv?${csvParams()}`, $("lq-host"), "Gerando CSV…")
        .catch((e) => { $("lq-error").hidden = false; $("lq-error").textContent = `CSV falhou: ${e.message}`; });
    });
    $("lq-table").addEventListener("click", (ev) => {
      const th = ev.target.closest("th[data-sort]");
      if (th) { sortBy(th.dataset.sort); return; }
      const btn = ev.target.closest("[data-analyze]");
      if (btn) { App.analyzeTicker(btn.dataset.analyze); return; }
      const row = ev.target.closest("tr[data-u]");
      if (row) App.showUnderlying(row.dataset.u, "liquidity");
    });
  }

  function activate() {
    setup();
    if (!st.data && !st.loading) load();
  }

  // Texto da etapa em andamento (consultada no backend enquanto a lista é montada).
  function stepText(p) {
    const n = Math.min(p.done + 1, p.total);
    if (p.phase === "baixando") return `Baixando da B3 o fechamento de ${FMT.date(p.day)} (pregão ${n} de ${p.total})… ~5 s por pregão na 1ª vez`;
    if (p.phase === "lendo") return `Lendo o pregão de ${FMT.date(p.day)} (${n} de ${p.total})…`;
    if (p.phase === "cadastro") return "Conferindo o cadastro de opções da B3…";
    if (p.phase === "calculando") return "Calculando o ranking…";
    return "Preparando…";
  }

  function showProgress(p) {
    const box = $("lq-host").querySelector(".busy-box");
    if (!box) return;
    box.querySelector(".busy-text").textContent = stepText(p);
    let bar = box.querySelector(".lq-progress");
    if (!bar) {
      bar = Object.assign(document.createElement("div"), { className: "lq-progress", innerHTML: "<span></span>" });
      box.appendChild(bar);
    }
    const frac = p.phase === "calculando" ? 1 : p.phase === "cadastro" ? 0.95 : (p.done || 0) / (p.total || 1);
    bar.firstElementChild.style.width = `${Math.round(frac * 100)}%`;
  }

  function setLoading(on) {
    st.loading = on;
    $("lq-host").classList.toggle("lq-loading", on);
    for (const id of ["lq-sessions", "lq-top", "lq-csv"]) $(id).disabled = on;
    if (on) $("lq-meta").textContent = "Montando a lista com o fechamento oficial da B3… aguarde.";
  }

  async function load() {
    if (st.loading) return;
    setLoading(true);
    $("lq-error").hidden = true;
    Busy.show($("lq-host"), "Preparando…");
    const poll = setInterval(async () => {
      const p = await App.api("/api/liquidity/progress").catch(() => null);
      if (p && p.active) showProgress(p);
    }, 600);
    try {
      // Lista completa: ordenação e "top N" são aplicados na tela (top N depois de ordenar).
      st.data = await App.api(`/api/liquidity?sessions=${$("lq-sessions").value}&top=0`);
      render();
    } catch (e) {
      $("lq-error").hidden = false;
      $("lq-error").textContent = `Não foi possível montar a lista: ${e.message}`;
      $("lq-meta").textContent = "";
    } finally {
      clearInterval(poll);
      Busy.hide($("lq-host"));
      setLoading(false);
    }
  }

  function sortBy(key) {
    const col = COLS.find((c) => c.key === key);
    const current = st.desc === null ? col.defaultDesc : st.desc;
    st.desc = st.sort === key ? !current : col.defaultDesc;
    st.sort = key;
    App.savePrefs();
    render();
  }

  // Mesma regra do backend (sort_rows): vazios sempre no fim.
  const FIELD = { rank: "rank", ticker: "underlying", turnover: "turnover_brl", deals: "deals", book: "book_spread", ivhv: "ivhv", series: "b3_series", mt5: "has_mt5_options" };
  function sorted(rows) {
    const field = FIELD[st.sort];
    const desc = st.desc === null ? COLS.find((c) => c.key === st.sort).defaultDesc : st.desc;
    const value = (r) => (r[field] === true ? 1 : r[field] === false ? 0 : r[field]);
    const present = rows.filter((r) => r[field] !== null && r[field] !== undefined);
    const missing = rows.filter((r) => r[field] === null || r[field] === undefined);
    present.sort((a, b) => {
      const x = value(a), y = value(b);
      const c = typeof x === "string" ? x.localeCompare(y) : x - y;
      return desc ? -c : c;
    });
    return present.concat(missing);
  }

  function bookCell(r) {
    if (r.book_spread === null || r.book_spread === undefined) {
      return r.book_series ? `<span class="muted" title="${r.book_series} séries perto do dinheiro, nenhuma com bid e ask">sem book</span>` : '<span class="muted" title="Ativo fora do snapshot do servidor">—</span>';
    }
    const s = r.book_spread;
    const cls = s <= 0.05 ? "ok" : s <= 0.15 ? "mid" : "bad";
    return `<span class="badge ${cls}">${FMT.pct(s, 1)}</span> <span class="muted small">${r.book_with_quotes}/${r.book_series} com book</span>`;
  }

  const IVHV_CLASS = { barata: "ok", neutra: "neutral", cara: "bad" };
  // Selo do 1º vencimento mensal; tooltip com os próximos mensais, a fonte e a metodologia.
  function ivhvCell(r, d) {
    if (r.ivhv === null || r.ivhv === undefined) {
      return `<span class="muted" title="${esc(r.ivhv_reason || "sem dados")}">—</span>`;
    }
    const vp = d.vol_premium || {};
    const lines = (r.ivhv_items || []).map((it) => {
      const head = `${it.expiration === r.ivhv_expiration ? "▸ " : "  "}${FMT.date(it.expiration)} · ${it.dte_business_days} du · `;
      if (it.atm_iv === null) return head + "sem IV ATM (book sem bid e ask aceitáveis)";
      return head + `IV ${FMT.pct(it.atm_iv, 0)} · HV${it.hv_window} ${FMT.pct(it.hv, 0)} · ` +
        (it.ratio === null ? "sem HV" : `${FMT.num(it.ratio, 2)} ${it.label}`);
    });
    const tip = [
      "IV ATM ÷ vol histórica, próximos vencimentos mensais (▸ = o da tabela):", ...lines, "",
      r.ivhv_weak ? `Pouco confiável: ${r.ivhv_weak}.` : null,
      `Barata < ${FMT.num(vp.cheap_below, 2)} · cara > ${FMT.num(vp.expensive_above, 2)}.`,
      vp.method || null,
      d.book_source ? `Snapshot do servidor de ${d.book_source}.` : null,
      "Indicativo, não é recomendação: a HV olha para trás e eventos podem justificar IV alta.",
    ].filter((x) => x !== null).join("\n");
    const cls = r.ivhv_weak ? "neutral weak" : IVHV_CLASS[r.ivhv_label] || "neutral";
    return `<span class="badge ${cls}" title="${esc(tip)}">${FMT.num(r.ivhv, 2)} ${esc(r.ivhv_label)}${r.ivhv_weak ? " ?" : ""}</span>`;
  }

  function render() {
    const d = st.data;
    if (!d) return;
    const days = d.sessions;
    const top = Number($("lq-top").value);
    const all = sorted(d.rows);
    const rows = top ? all.slice(0, top) : all;
    const col = COLS.find((c) => c.key === st.sort);
    const period = days.length ? `${FMT.date(days[0])} a ${FMT.date(days[days.length - 1])}` : "—";
    $("lq-meta").textContent = `${rows.length} de ${d.total} ativos com negócios em opções, ordenados por ${col.label.toLowerCase() === "#" ? "volume financeiro" : col.label.toLowerCase()} · média de ${days.length} pregão(ões): ${period}` +
      (days.length < d.sessions_requested ? ` (pedidos ${d.sessions_requested}; os demais ainda não publicados ou indisponíveis na B3)` : "") +
      (d.book_source ? ` · book: snapshot do servidor de ${d.book_source}` : " · book: snapshot do servidor indisponível") +
      (d.mt5_checked ? "" : " · MT5 desconectado: coluna \"MT5\" indisponível");
    const max = Math.max(1, ...d.rows.map((r) => r.turnover_brl));
    const body = rows.map((r) => {
      const mt5 = r.has_mt5_options === null ? "—" : r.has_mt5_options ? '<span class="badge ok">sim</span>' : '<span class="badge mid" title="Sem cotações das opções no MT5 da corretora logada">não</span>';
      const bar = `<span class="lq-bar" style="width:${Math.max(2, (100 * r.turnover_brl) / max)}%"></span>`;
      return `<tr data-u="${esc(r.underlying)}" title="Clique para ver o gráfico do ativo">
        <td>${r.rank}</td>
        <td class="l">${tickerIcon(r.underlying, 18)}<b>${esc(r.underlying)}</b> <span class="muted small">${esc(r.category || "")}</span></td>
        <td class="lq-turnover">${bar}<span>${mi(r.turnover_brl)}</span></td>
        <td>${FMT.int(Math.round(r.deals))}</td>
        <td class="l">${bookCell(r)}</td>
        <td class="l">${ivhvCell(r, d)}</td>
        <td>${r.b3_series === null ? "—" : FMT.int(r.b3_series)}</td>
        <td>${mt5}</td>
        <td><button type="button" class="small" data-analyze="${esc(r.underlying)}" ${r.has_mt5_options === false ? 'disabled title="Opções sem cotação no MT5 da corretora"' : ""}>Analisar travas</button></td>
      </tr>`;
    }).join("");
    const desc = st.desc === null ? col.defaultDesc : st.desc;
    const heads = COLS.map((c) => {
      const arrow = c.key === st.sort ? (desc ? " ▼" : " ▲") : "";
      const aria = c.key === st.sort ? (desc ? "descending" : "ascending") : "none";
      return `<th data-sort="${c.key}" class="sortable${c.l ? " l" : ""}" aria-sort="${aria}" title="${esc(c.tip || "Ordenar")} (clique para ordenar)">${c.label}${arrow}</th>`;
    }).join("");
    $("lq-table").innerHTML = `<thead><tr>${heads}<th></th></tr></thead><tbody>${body || `<tr><td colspan="${COLS.length + 1}" class="l muted">Sem dados.</td></tr>`}</tbody>`;
  }

  function prefs() {
    return { sessions: $("lq-sessions").value, top: $("lq-top").value, sort: st.sort, desc: st.desc };
  }

  function applyPrefs(p) {
    if (p.sessions) $("lq-sessions").value = p.sessions;
    if (p.top !== undefined) $("lq-top").value = p.top;
    if (p.sort && COLS.some((c) => c.key === p.sort)) { st.sort = p.sort; st.desc = p.desc ?? null; }
  }

  return { activate, prefs, applyPrefs };
})();
