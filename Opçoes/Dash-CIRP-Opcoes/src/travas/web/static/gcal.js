// Google Agenda (aba Carteira): conectar, estado da sincronização e desconectar. Os eventos
// de vencimento são criados/apagados pelo backend a cada mudança nas estruturas.
const Gcal = (() => {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  let poll = null;

  function reminderText(s) {
    const r = s.reminders.map((x) => (x.business_days_before === 0 ? `no dia ${x.time}` : `D-${x.business_days_before} ${x.time}`));
    return `evento às ${s.event_time} do vencimento; lembretes: ${r.join(", ")}`;
  }

  function render(s) {
    const box = $("gcal-box");
    if (!s || !s.enabled) { box.hidden = true; return; }
    box.hidden = false;
    const tip = `Um evento por vencimento de cada estrutura aberta, na agenda "${s.calendar_name}" (criada pelo app; ele só altera essa agenda). Encerrar ou excluir a estrutura apaga o evento. ${reminderText(s)}.`;
    let body;
    if (!s.configured) {
      body = `<span class="muted">credencial OAuth (client_secret*.json) não encontrada na pasta do projeto</span>`;
    } else if (s.connecting) {
      body = `<span class="muted">aguardando a autorização no navegador (faça login no Google e permita o acesso)…</span>`;
    } else if (!s.connected) {
      body = `<button id="gcal-connect">Conectar Google (Agenda, e-mail e Drive)</button>`;
    } else {
      const r = s.last_result;
      const sync = s.last_sync ? `sincronizado ${FMT.datetime(s.last_sync)}${r ? ` · ${r.events} evento(s)${r.created || r.updated || r.deleted ? ` (+${r.created} ~${r.updated} −${r.deleted})` : ""}` : ""}` : "sincronizando…";
      body = `<span class="badge ok">conectado</span> <span class="muted">${esc(s.calendar_name)} · ${sync}</span> <button id="gcal-sync">Sincronizar agora</button> <button id="gcal-disconnect">Desconectar</button>`;
    }
    const err = s.last_error ? ` <span class="neg">${esc(s.last_error)}</span>` : "";
    box.innerHTML = `<span class="strong small">Google Agenda:</span> ${body}${err} <span class="tip" title="${esc(tip)}">?</span>`;
    $("gcal-connect")?.addEventListener("click", connect);
    $("gcal-sync")?.addEventListener("click", sync);
    $("gcal-disconnect")?.addEventListener("click", disconnect);
  }

  async function refresh() {
    try { render(await App.api("/api/calendar/status")); } catch (e) { /* servidor local indisponível */ }
  }

  function watch(seconds) {
    clearInterval(poll);
    const until = Date.now() + seconds * 1000;
    poll = setInterval(async () => {
      const s = await App.api("/api/calendar/status").catch(() => null);
      if (s) render(s);
      if (!s || (!s.connecting && s.last_sync) || Date.now() > until) clearInterval(poll);
    }, 2000);
  }

  async function connect() {
    try {
      const r = await App.api("/api/calendar/connect", { method: "POST" });
      // O login e a autorização são feitos pelo usuário na página do Google.
      window.open(r.auth_url, "_blank", "noopener");
      watch(320);
      refresh();
    } catch (e) {
      $("gcal-box").insertAdjacentHTML("beforeend", ` <span class="neg">${esc(e.message)}</span>`);
    }
  }

  async function sync() {
    try { await App.api("/api/calendar/sync", { method: "POST" }); } catch (e) { /* erro aparece no estado */ }
    refresh();
  }

  async function disconnect() {
    await App.api("/api/calendar/disconnect", { method: "POST" }).catch(() => null);
    refresh();
  }

  return { refresh, watch, connect };
})();
