"""Lista as notícias de 3 estrelas (alta volatilidade) do dia atual do
calendário econômico do br.investing.com, com dia e horário de Brasília.

Uso:
    python noticias_3_estrelas.py                # imprime a lista
    python noticias_3_estrelas.py --csv x.csv    # também salva em CSV
    python noticias_3_estrelas.py --telegram     # envia a lista ao grupo do Telegram
    python noticias_3_estrelas.py --popup        # fica rodando e mostra um aviso no canto
                                                 # superior esquerdo 30 s antes de cada notícia
    python noticias_3_estrelas.py --log x.log    # grava o que acontece num arquivo
                                                 # (útil com pythonw.exe, que não tem console)

Inclui também as aberturas da B3 (10:00) e do Dow Jones (09:30 de Nova York,
ajustado ao horário de verão dos EUA), exceto em fim de semana e feriado.

O aviso some sozinho após alguns segundos e não rouba o foco da janela ativa
(ex.: ProfitChart).

O token do bot é lido de TELEGRAM_TOKEN ou de ~/.config/screener/telegram_token
(o mesmo do screener), para não ficar no repositório.
"""
import argparse
import csv
import ctypes
import html
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from curl_cffi import requests

URL = "https://br.investing.com/economic-calendar/Service/getCalendarFilteredData"
HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://br.investing.com/economic-calendar/",
}
FUSO_BRASILIA = "12"  # id de fuso do Investing para GMT-3 (Brasília)
TZ_BRASILIA = timezone(timedelta(hours=-3))  # Brasil sem horário de verão desde 2019

# Aberturas de mercado incluídas todo dia útil junto com as notícias.
# O horário é no fuso da própria bolsa; a NYSE (Dow Jones) abre 09:30 em
# Nova York, o que dá 10:30 de Brasília no horário de verão dos EUA e 11:30 fora dele.
ABERTURAS = [
    {"evento": "Abertura do mercado de ações (B3)", "moeda": "BRL", "pais": "Brasil",
     "hora": (10, 0), "fuso": "America/Sao_Paulo"},
    {"evento": "Abertura Dow Jones (NYSE)", "moeda": "USD", "pais": "Estados Unidos",
     "hora": (9, 30), "fuso": "America/New_York"},
]

TELEGRAM_CHAT_ID = "-5392865831"
TELEGRAM_TOKEN_FILE = Path.home() / ".config" / "screener" / "telegram_token"

log = logging.getLogger("noticias")


def obter_noticias(tentativas=5, intervalo=60):
    data = {
        "importance[]": "3",
        "timeZone": FUSO_BRASILIA,
        "timeFilter": "timeOnly",
        "currentTab": "today",
        "limit_from": "0",
    }
    for tentativa in range(1, tentativas + 1):
        try:
            # impersonate="chrome" evita o bloqueio do Cloudflare
            r = requests.post(URL, data=data, headers=HEADERS, impersonate="chrome", timeout=30)
            r.raise_for_status()
            break
        except Exception as e:  # rede fora do ar logo após ligar o PC, Cloudflare etc.
            if tentativa == tentativas:
                raise
            log.warning("Falha ao obter o calendário (%s); nova tentativa em %d s", e, intervalo)
            time.sleep(intervalo)
    soup = BeautifulSoup(r.json()["data"], "html.parser")

    feriados = set()
    for tr in soup.find_all("tr"):
        sentimento = tr.select_one("td.sentiment")
        bandeira = tr.select_one("td.flagCur span[title]")
        if sentimento and bandeira and sentimento.get_text(strip=True) == "Feriado":
            feriados.add(bandeira["title"])

    noticias = []
    for tr in soup.select("tr.js-event-item"):
        sentimento = tr.select_one("td.sentiment")
        if sentimento is None or sentimento.get("data-img_key") != "bull3":
            continue

        def texto(seletor):
            td = tr.select_one(seletor)
            return td.get_text(" ", strip=True) if td else ""

        # data-event-datetime vem no fuso pedido (Brasília), ex.: "2026/09/24 04:30:00"
        quando = datetime.strptime(tr["data-event-datetime"], "%Y/%m/%d %H:%M:%S")
        noticias.append({
            "dia": quando.strftime("%d/%m/%Y"),
            "horario": texto("td.time"),
            "moeda": texto("td.flagCur"),
            "pais": tr.select_one("td.flagCur span")["title"],
            "evento": " ".join(texto("td.event").split()),
            "atual": texto("td.act"),
            "projecao": texto("td.fore"),
            "anterior": texto("td.prev"),
            "quando": quando.replace(tzinfo=TZ_BRASILIA),
        })
    return noticias, feriados


def aberturas_do_dia(feriados):
    """Aberturas de bolsa de hoje, sem fim de semana nem feriado do país."""
    hoje = datetime.now(TZ_BRASILIA).date()
    if hoje.weekday() >= 5:
        return []
    eventos = []
    for a in ABERTURAS:
        if a["pais"] in feriados:
            log.info("%s: feriado em %s, sem abertura hoje.", a["evento"], a["pais"])
            continue
        local = datetime(hoje.year, hoje.month, hoje.day, *a["hora"], tzinfo=ZoneInfo(a["fuso"]))
        quando = local.astimezone(TZ_BRASILIA)
        eventos.append({
            "dia": quando.strftime("%d/%m/%Y"), "horario": quando.strftime("%H:%M"),
            "moeda": a["moeda"], "pais": a["pais"], "evento": a["evento"],
            "atual": "", "projecao": "", "anterior": "", "quando": quando,
        })
    return eventos


def formatar_linha(n):
    return (f"{n['dia']} {n['horario']:>5}  {n['moeda']:<4} {n['evento']:<55} "
            f"Atual: {n['atual'] or '-':<8} Proj.: {n['projecao'] or '-':<8} "
            f"Ant.: {n['anterior'] or '-'}")


def salvar_csv(noticias, caminho):
    campos = [c for c in noticias[0] if c != "quando"]
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(noticias)


def ler_token():
    token = os.environ.get("TELEGRAM_TOKEN")
    if token:
        return token.strip()
    if TELEGRAM_TOKEN_FILE.exists():
        return TELEGRAM_TOKEN_FILE.read_text(encoding="utf-8").strip()
    raise RuntimeError(f"Token do Telegram não encontrado (TELEGRAM_TOKEN ou {TELEGRAM_TOKEN_FILE})")


def mensagem_telegram(noticias):
    hoje = datetime.now(TZ_BRASILIA).strftime("%d/%m/%Y")
    if not noticias:
        return f"📅 <b>Notícias 3 estrelas — {hoje}</b>\n\nNenhuma notícia de 3 estrelas hoje."
    linhas = [f"📅 <b>Notícias 3 estrelas — {noticias[0]['dia']}</b> (horário de Brasília)", ""]
    for n in noticias:
        linha = f"🕒 <b>{n['horario']}</b> {html.escape(n['moeda'])} — {html.escape(n['evento'])}"
        valores = [f"{rotulo}: {html.escape(n[chave])}"
                   for rotulo, chave in (("Atual", "atual"), ("Proj.", "projecao"), ("Ant.", "anterior"))
                   if n[chave]]
        if valores:
            linha += "\n      " + " | ".join(valores)
        linhas.append(linha)
    return "\n".join(linhas)


def enviar_telegram(texto):
    r = requests.post(
        f"https://api.telegram.org/bot{ler_token()}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": texto, "parse_mode": "HTML",
              "disable_web_page_preview": True},
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(f"Falha ao enviar ao Telegram: {r.status_code} {r.text}")


# --- Aviso na tela -----------------------------------------------------------

GWL_EXSTYLE = -20
WS_EX_TOPMOST, WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = 0x8, 0x80, 0x08000000
SW_SHOWNOACTIVATE = 4
HWND_TOPMOST = -1
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x1, 0x2, 0x10


class Avisos:
    """Janelas sem borda no canto superior esquerdo que somem sozinhas.

    WS_EX_NOACTIVATE + SW_SHOWNOACTIVATE fazem a janela aparecer por cima sem
    tirar o foco de quem está ativo; WS_EX_TOOLWINDOW a esconde da barra de tarefas.
    """

    MARGEM, LARGURA = 12, 380

    def __init__(self, duracao):
        import tkinter as tk
        self.tk = tk
        self.duracao_ms = duracao * 1000
        self.root = tk.Tk()
        self.root.withdraw()
        self.abertas = []  # empilha avisos simultâneos (ex.: duas notícias às 09:30)

    def mostrar(self, titulo, corpo):
        tk = self.tk
        win = tk.Toplevel(self.root)
        win.withdraw()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.95)

        quadro = tk.Frame(win, bg="#1f2430", highlightthickness=2, highlightbackground="#f5a623")
        quadro.pack(fill="both", expand=True)
        tk.Label(quadro, text=titulo, bg="#1f2430", fg="#f5a623", anchor="w",
                 font=("Segoe UI", 10, "bold")).pack(fill="x", padx=12, pady=(10, 2))
        tk.Label(quadro, text=corpo, bg="#1f2430", fg="#ffffff", anchor="w", justify="left",
                 wraplength=self.LARGURA - 24, font=("Segoe UI", 10)).pack(fill="x", padx=12, pady=(0, 10))

        win.update_idletasks()
        y = self.MARGEM + sum(w.winfo_reqheight() + 8 for w in self.abertas)
        win.geometry(f"{self.LARGURA}x{win.winfo_reqheight()}+{self.MARGEM}+{y}")
        win.update_idletasks()

        user32 = ctypes.windll.user32
        hwnd = user32.GetParent(win.winfo_id())
        estilo = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                              estilo | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST)
        user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

        self.abertas.append(win)
        win.after(self.duracao_ms, lambda: self._fechar(win))

    def _fechar(self, win):
        self.abertas.remove(win)
        win.destroy()


def aguardar_popups(noticias, antecedencia, duracao):
    agora = datetime.now(TZ_BRASILIA)
    pendentes = sorted((n for n in noticias if n["quando"] - timedelta(seconds=antecedencia) > agora),
                       key=lambda n: n["quando"])
    if not pendentes:
        log.info("Nenhuma notícia futura hoje para avisar.")
        return

    log.info("Avisos agendados para %d notícia(s), %d s antes.", len(pendentes), antecedencia)
    avisos = Avisos(duracao)

    # Confere o relógio a cada segundo em vez de um after() longo, que atrasaria
    # se o PC entrasse em suspensão.
    def verificar():
        agora = datetime.now(TZ_BRASILIA)
        while pendentes and pendentes[0]["quando"] - timedelta(seconds=antecedencia) <= agora:
            n = pendentes.pop(0)
            corpo = f"{n['moeda']} ({n['pais']})\n{n['evento']}"
            valores = [f"{r}: {n[c]}" for r, c in (("Proj.", "projecao"), ("Ant.", "anterior")) if n[c]]
            if valores:
                corpo += "\n" + "   ".join(valores)
            log.info("Aviso: %s %s", n["horario"], n["evento"])
            avisos.mostrar(f"⚠ {n['horario']} — notícia 3★ em {antecedencia} s", corpo)
        if pendentes or avisos.abertas:
            avisos.root.after(1000, verificar)
        else:
            avisos.root.destroy()

    verificar()
    avisos.root.mainloop()
    log.info("Todos os avisos do dia foram exibidos.")


def configurar_log(caminho):
    handlers = []
    if sys.stderr is not None:  # pythonw.exe não tem console
        handlers.append(logging.StreamHandler())
    if caminho:
        handlers.append(logging.FileHandler(caminho, encoding="utf-8"))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%d/%m/%Y %H:%M:%S", handlers=handlers or [logging.NullHandler()])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", help="caminho do arquivo CSV de saída")
    parser.add_argument("--telegram", action="store_true", help="envia a lista ao grupo do Telegram")
    parser.add_argument("--popup", action="store_true",
                        help="fica rodando e mostra um aviso antes de cada notícia")
    parser.add_argument("--antecedencia", type=int, default=30,
                        help="segundos de antecedência do aviso (padrão: 30)")
    parser.add_argument("--duracao", type=int, default=5,
                        help="segundos que o aviso fica na tela (padrão: 5)")
    parser.add_argument("--log", help="arquivo de log")
    args = parser.parse_args()
    configurar_log(args.log)

    try:
        noticias, feriados = obter_noticias()
    except Exception:
        log.exception("Não foi possível obter o calendário")
        sys.exit(1)
    noticias = sorted(noticias + aberturas_do_dia(feriados), key=lambda n: n["quando"])

    if noticias:
        for n in noticias:
            log.info(formatar_linha(n))
    else:
        log.info("Nenhuma notícia de 3 estrelas hoje.")

    if args.csv and noticias:
        salvar_csv(noticias, args.csv)
        log.info("%d notícias salvas em %s", len(noticias), args.csv)

    if args.telegram:
        # Falha no Telegram não impede os avisos na tela.
        try:
            enviar_telegram(mensagem_telegram(noticias))
            log.info("Lista enviada ao Telegram.")
        except Exception as e:
            log.error("%s", e)

    if args.popup:
        try:
            aguardar_popups(noticias, args.antecedencia, args.duracao)
        except KeyboardInterrupt:
            log.info("Encerrado.")


if __name__ == "__main__":
    main()
