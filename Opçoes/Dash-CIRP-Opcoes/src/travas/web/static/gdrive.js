// Google Drive (aba Carteira): estado da cópia da Carteira e dos favoritos. O envio é feito
// pelo backend a cada mudança nas estruturas; a conexão é a mesma do Google Agenda.
const Gdrive = (() => {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  let poll = null;

  function render(s) {
    const box = $("gdrive-box");
    if (!s || !s.enabled) { box.hidden = true; return; }
    box.hidden = false;
    const tip = `Cópia de ${s.files.join(" e ")} na pasta "${s.folder_name}" do seu Drive, a cada mudança na Carteira. O Drive guarda as versões anteriores${s.history ? "; a subpasta Histórico tem uma cópia por dia" : ""}. O app só enxerga os arquivos que ele criou (permissão drive.file). O arquivo local continua sendo o principal.`;
    let body;
    if (!s.connected) {
      body = `<span class="muted">conecte o Google no quadro acima</span>`;
    } else if (!s.authorized) {
      body = `<span class="muted">a conexão atual não inclui o Drive</span> <button id="gdrive-auth">Reconectar Google (autorizar o Drive)</button>`;
    } else {
      const r = s.last_result;
      const back = r && r.restored && r.restored.length ? ` · <b>restaurado do Drive: ${esc(r.restored.join(", "))}</b>` : "";
      const sent = r && r.uploaded.length ? ` · enviado: ${esc(r.uploaded.join(", "))}` : r ? " · sem mudanças" : "";
      const sync = s.last_sync ? `verificado ${FMT.datetime(s.last_sync)}${sent}${back}` : "enviando…";
      const link = s.folder_url ? ` <a href="${esc(s.folder_url)}" target="_blank" rel="noopener">abrir pasta</a>` : "";
      body = `<span class="badge ok">ativo</span> <span class="muted">${esc(s.folder_name)} · ${sync}</span>${link} <button id="gdrive-sync">Enviar agora</button> <button id="gdrive-open-restore">Restaurar do Drive…</button>`;
    }
    const err = s.last_error ? ` <span class="neg">${esc(s.last_error)}</span>` : "";
    box.innerHTML = `<span class="strong small">Google Drive:</span> ${body}${err} <span class="tip" title="${esc(tip)}">?</span>`;
    $("gdrive-auth")?.addEventListener("click", () => { Gcal.connect(); watch(320); });
    $("gdrive-sync")?.addEventListener("click", sync);
    $("gdrive-open-restore")?.addEventListener("click", openRestore);
  }

  async function refresh() {
    try { render(await App.api("/api/drive/status")); } catch (e) { /* servidor local indisponível */ }
  }

  function watch(seconds) {
    clearInterval(poll);
    const until = Date.now() + seconds * 1000;
    poll = setInterval(async () => {
      const s = await App.api("/api/drive/status").catch(() => null);
      if (s) render(s);
      if (!s || (s.authorized && s.last_sync) || Date.now() > until) clearInterval(poll);
    }, 2000);
  }

  async function sync() {
    try { await App.api("/api/drive/sync", { method: "POST" }); } catch (e) { /* erro aparece no estado */ }
    refresh();
  }

  // Restaurar: escolher uma cópia (atual ou do Histórico) e confirmar com um 2º clique.
  function versionLabel(v) {
    const when = v.modified ? FMT.datetime(v.modified) : "—";
    const kb = v.size ? ` · ${FMT.num(v.size / 1024, 1)} KB` : "";
    return v.kind === "atual" ? `Versão atual de ${v.target} (${when}${kb})` : `Histórico: ${v.name} (${when}${kb})`;
  }

  async function openRestore() {
    const box = $("gdrive-restore");
    box.hidden = false;
    box.innerHTML = '<span class="muted">buscando as cópias no Drive…</span>';
    let list;
    try { list = await App.api("/api/drive/versions"); } catch (e) { box.innerHTML = `<span class="neg">${esc(e.message)}</span> <button id="gdrive-r-close">Fechar</button>`; $("gdrive-r-close").onclick = closeRestore; return; }
    if (!list.length) { box.innerHTML = '<span class="muted">nenhuma cópia no Drive ainda.</span> <button id="gdrive-r-close">Fechar</button>'; $("gdrive-r-close").onclick = closeRestore; return; }
    const opts = list.map((v) => `<option value="${esc(v.id)}" data-target="${esc(v.target)}">${esc(versionLabel(v))}</option>`).join("");
    box.innerHTML = `<span class="strong small">Restaurar do Drive:</span> <select id="gdrive-r-sel">${opts}</select> <button id="gdrive-r-go">Restaurar</button> <button id="gdrive-r-close">Cancelar</button> <span class="muted small" id="gdrive-r-msg">O arquivo local é substituído; o atual fica guardado como .pre-restauracao.bak.</span>`;
    const go = $("gdrive-r-go");
    let armed = false;
    $("gdrive-r-sel").addEventListener("change", () => { armed = false; go.textContent = "Restaurar"; go.classList.remove("primary"); });
    go.addEventListener("click", async () => {
      const sel = $("gdrive-r-sel");
      const target = sel.selectedOptions[0].dataset.target;
      if (!armed) { armed = true; go.textContent = `Confirmar: substituir ${target} deste computador`; go.classList.add("primary"); return; }
      go.disabled = true;
      try {
        const r = await App.api(`/api/drive/restore/${encodeURIComponent(sel.value)}`, { method: "POST" });
        box.innerHTML = `<span class="badge ok">restaurado</span> ${esc(r.target)} ← ${esc(r.restored)}${r.backup ? ` · anterior guardado como ${esc(r.backup)}` : ""} <button id="gdrive-r-close">Fechar</button>`;
        $("gdrive-r-close").onclick = closeRestore;
        Tracking.refresh();
        setTimeout(refresh, 8000);
      } catch (e) {
        go.disabled = false;
        $("gdrive-r-msg").innerHTML = `<span class="neg">${esc(e.message)}</span>`;
      }
    });
    $("gdrive-r-close").onclick = closeRestore;
  }

  function closeRestore() { const box = $("gdrive-restore"); box.hidden = true; box.innerHTML = ""; }

  return { refresh, watch };
})();
