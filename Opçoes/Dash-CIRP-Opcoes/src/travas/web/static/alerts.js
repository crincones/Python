// Alertas de stop 1:1 (aba Carteira): estado dos canais (Telegram, e-mail), do servidor de
// alertas no Debian e botão de teste. O checkbox por estrutura fica na tabela (tracking.js).
const Alerts = (() => {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  let testResult = "";

  const chip = (ok, text, tip) => `<span class="badge ${ok ? "ok" : "bad"}" title="${esc(tip || "")}">${esc(text)}</span>`;

  function channels(c) {
    if (!c) return "";
    return Object.entries(c).map(([k, v]) => `${k}: ${v === "ok" ? "✓" : esc(v)}`).join(" · ");
  }

  function render(s) {
    const box = $("alerts-box");
    if (!s || !s.enabled) { box.hidden = true; return; }
    box.hidden = false;
    const tip = "Marque o 🔔 de uma estrutura aberta para receber Telegram + e-mail quando o ativo chegar ao preço em que o prejuízo iguala o lucro máximo (stop 1:1, pelo modelo). O app confere quando recebe cotações com o mercado aberto (ao atualizar esta aba); o servidor Debian confere a cada 15 min de pregão, mesmo com o app fechado. Cada alerta sai uma vez; desmarcar e marcar de novo rearma.";
    const tg = chip(s.telegram, s.telegram ? "Telegram ✓" : "Telegram ✗", s.telegram ? "" : `bot/chat não encontrados em ${s.contacts_file}`);
    let mail;
    if (!s.email) mail = chip(false, "e-mail ✗", `e-mail não encontrado em ${s.contacts_file}`);
    else if (s.gmail) mail = chip(true, `e-mail ✓ ${s.email}`, "enviado pela Gmail API da conexão Google");
    else mail = `${chip(false, "e-mail: falta autorizar", "a conexão Google precisa da permissão de enviar e-mail (gmail.send)")} <button id="alerts-gmail">${s.google_connected ? "Reconectar Google (autorizar e-mail)" : "Conectar Google (Agenda e e-mail)"}</button>`;
    let server;
    if (!s.server_url) server = '<span class="muted">servidor: desativado</span>';
    else if (s.server_error && !s.server) server = chip(false, "servidor inacessível", s.server_error);
    else if (s.server) {
      const c = s.server.last_check;
      const check = c ? ` · última checagem ${FMT.datetime(c.at)}${c.skipped ? ` (${esc(c.skipped)})` : ""}` : " · ainda sem checagem";
      const creds = [s.server.telegram ? "Telegram" : "", s.server.email ? "e-mail" : ""].filter(Boolean).join(" + ") || "sem canais";
      server = `${chip(!s.server_error, `servidor ✓ ${s.server.watch} vigiada(s)`, s.server_error || `canais no servidor: ${creds}`)}<span class="muted small">${check}</span>`;
    } else server = '<span class="muted">servidor: aguardando a 1ª atualização</span>';
    const err = s.last_error ? ` <span class="neg">${esc(s.last_error)}</span>` : "";
    const last = s.last_sent ? ` <span class="muted small">último alerta: ${esc(s.last_sent.name)} ${FMT.datetime(s.last_sent.at)}</span>` : "";
    box.innerHTML = `<span class="strong small">Alertas de stop 1:1:</span> ${tg} ${mail} ${server} <span class="muted small">${s.armed} marcada(s)</span>
      <button id="alerts-test">Testar envio</button>${last}${err} <span class="tip" title="${esc(tip)}">?</span>${testResult}`;
    $("alerts-test").addEventListener("click", test);
    $("alerts-gmail")?.addEventListener("click", () => { Gcal.connect(); setTimeout(refresh, 3000); });
  }

  async function refresh() {
    try { render(await App.api("/api/alerts/status")); } catch (e) { /* servidor local indisponível */ }
  }

  async function test() {
    $("alerts-test").disabled = true;
    testResult = ' <span class="muted small">enviando teste…</span>';
    refresh();
    try {
      const r = await App.api("/api/alerts/test", { method: "POST" });
      const server = r.server.error ? esc(r.server.error) : channels(r.server);
      testResult = `<div class="small">Teste — app: ${channels(r.local)} · servidor: ${server}</div>`;
    } catch (e) {
      testResult = ` <span class="neg">${esc(e.message)}</span>`;
    }
    refresh();
  }

  return { refresh };
})();
