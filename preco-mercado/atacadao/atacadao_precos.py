"""
Sondagem de preços do Atacadão (loja da região do CEP configurado).

Para cada categoria monitorada:
  - busca os produtos na Intelligent Search (preço de vitrine);
  - simula o carrinho no seller da loja para obter o preço real unitário
    e o preço de atacado (por faixa de quantidade);
  - refrigerados (queijo, ovos, iogurte) não têm preço no carrinho online,
    então para eles vale o preço de vitrine (fonte = "vitrine");
  - grava tudo em SQLite e compara com a sondagem anterior.

Os preços são públicos: não é necessário login.

Uso:
    python atacadao_precos.py            # faz uma sondagem e mostra o relatório
    python atacadao_precos.py --historico "mussarela"   # histórico de um produto
    python atacadao_precos.py --html     # só regera o painel precos.html a partir do banco
"""
import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

CEP = "13840110"
BASE = "https://www.atacadao.com.br"
DB_PATH = Path(__file__).with_name("precos.db")
TEMPLATE_PATH = Path(__file__).with_name("painel_template.html")
HTML_PATH = Path(__file__).with_name("precos.html")
QUANTIDADES = [1, 3, 6, 12, 24, 48]  # faixas testadas para achar o preço de atacado

# categoria -> (termo de busca, regex obrigatória no nome, regex de exclusão)
CATEGORIAS = {
    "Queijo mussarela 1kg": ("queijo mussarela", r"(mussarela|mucarela).*(1\s?kg|quilo|kg)", r"ralad"),
    # os "líquidos" são as garrafas de 800g a 1,25kg
    "Iogurte líquido": ("iogurte", r"^iogurte.*(liquido|(8\d\d|9\d\d)\s?g|\d[,.]?\d*\s?kg)", r"grego|polpa|pedaco|pote"),
    "Café 500g": ("cafe 500g", r"^cafe.*500\s?g", r"capsula|soluvel"),
    "Leite 1L": ("leite longa vida integral", r"^leite.*1\s?l\b", r"condensado|\bpo\b|fermentado|coco"),
    "Ovos": ("ovos", r"^ovos?\b", r"codorna|conserva|pascoa|chocolate|surpresa|kids"),
    "Pasta de amendoim 1kg": ("pasta de amendoim", r"pasta de amendoim.*1[,.]?\d*\s?kg", None),
}

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0"


def normalizar(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def resolver_seller(cep):
    r = session.get(f"{BASE}/api/checkout/pub/regions",
                    params={"country": "BRA", "postalCode": cep, "sc": 1}, timeout=30)
    r.raise_for_status()
    seller = r.json()[0]["sellers"][0]
    return seller["id"], seller["name"]


def buscar(termo, paginas=2):
    produtos = []
    for pagina in range(1, paginas + 1):
        r = session.get(f"{BASE}/api/io/_v/api/intelligent-search/product_search/",
                        params={"query": termo, "count": 50, "page": pagina, "locale": "pt-BR"},
                        timeout=30)
        r.raise_for_status()
        lote = r.json().get("products", [])
        produtos.extend(lote)
        if len(lote) < 50:
            break
    return produtos


def simular(item_ids, seller, quantidade):
    """Retorna {item_id: (preco_unitario_em_reais, disponibilidade)} para a quantidade dada."""
    r = session.post(f"{BASE}/api/checkout/pub/orderForms/simulation?sc=1",
                     json={"items": [{"id": i, "quantity": quantidade, "seller": seller} for i in item_ids],
                           "country": "BRA", "postalCode": CEP},
                     timeout=60)
    r.raise_for_status()
    resultado = {}
    for item in r.json().get("items", []):
        preco = item.get("sellingPrice") or item.get("price")
        resultado[item["id"]] = (preco / 100 if preco else None, item.get("availability"))
    return resultado


def coletar():
    seller, nome_loja = resolver_seller(CEP)
    print(f"Loja: {nome_loja} ({seller}) - CEP {CEP}\n")

    itens = {}  # item_id -> dados
    for categoria, (termo, obrigatoria, exclusao) in CATEGORIAS.items():
        for p in buscar(termo):
            nome = p["productName"]
            nome_n = normalizar(nome)
            if not re.search(obrigatoria, nome_n) or (exclusao and re.search(exclusao, nome_n)):
                continue
            item = p["items"][0]
            oferta = item["sellers"][0]["commertialOffer"]
            itens.setdefault(item["itemId"], {
                "categoria": categoria,
                "nome": nome,
                "ean": item.get("ean"),
                "link": BASE + p["link"],
                "preco_vitrine": oferta.get("Price") or None,
            })

    if not itens:
        return seller, []

    ids = list(itens)
    faixas = {q: simular(ids, seller, q) for q in QUANTIDADES}

    linhas = []
    for item_id, d in itens.items():
        preco_un, disponib = faixas[1].get(item_id, (None, None))
        fonte = "carrinho"
        if preco_un is None:
            preco_un, fonte = d["preco_vitrine"], "vitrine"
        if preco_un is None:
            continue  # sem preço nenhum: não há o que comparar
        preco_atac, qtd_atac = preco_un, 1
        for q in QUANTIDADES[1:]:
            preco_q, _ = faixas[q].get(item_id, (None, None))
            if preco_q and (preco_atac is None or preco_q < preco_atac - 1e-9):
                preco_atac, qtd_atac = preco_q, q
        linhas.append({**d, "item_id": item_id, "preco_un": preco_un,
                       "preco_atacado": preco_atac, "qtd_atacado": qtd_atac,
                       "disponibilidade": disponib, "fonte": fonte})
    return seller, linhas


def abrir_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS precos (
            data TEXT, seller TEXT, categoria TEXT, item_id TEXT, nome TEXT, ean TEXT,
            preco_vitrine REAL, preco_un REAL, preco_atacado REAL, qtd_atacado INTEGER,
            disponibilidade TEXT, link TEXT, fonte TEXT
        )""")
    con.execute("CREATE INDEX IF NOT EXISTS ix_item_data ON precos(item_id, data)")
    return con


def ultimo_preco(con, item_id):
    return con.execute(
        "SELECT preco_un, preco_atacado, data FROM precos WHERE item_id=? AND preco_un IS NOT NULL "
        "ORDER BY data DESC LIMIT 1", (item_id,)).fetchone()


def fmt(v):
    return f"R$ {v:7.2f}".replace(".", ",") if v is not None else "      -   "


def variacao(atual, anterior):
    if atual is None or anterior is None:
        return "novo" if anterior is None and atual is not None else ""
    if abs(atual - anterior) < 0.005:
        return "="
    pct = (atual / anterior - 1) * 100
    seta = "▲" if pct > 0 else "▼"
    return f"{seta} {pct:+.1f}% (era {fmt(anterior).strip()})"


def sondar():
    seller, linhas = coletar()
    agora = datetime.now().isoformat(timespec="seconds")
    con = abrir_db()

    categoria_atual = None
    for l in sorted(linhas, key=lambda x: (x["categoria"], x["preco_un"])):
        if l["categoria"] != categoria_atual:
            categoria_atual = l["categoria"]
            print(f"\n=== {categoria_atual} ===")
        anterior = ultimo_preco(con, l["item_id"])
        atacado = (f" | {fmt(l['preco_atacado'])} a partir de {l['qtd_atacado']} un"
                   if l["qtd_atacado"] > 1 else "")
        estoque = " [sem estoque online]" if l["disponibilidade"] != "available" and l["fonte"] == "carrinho" else ""
        estoque += " (vitrine)" if l["fonte"] == "vitrine" else ""
        var = variacao(l["preco_un"], anterior[0] if anterior else None)
        print(f"  {fmt(l['preco_un'])}{atacado}  {l['nome'][:60]}{estoque}  {var}")

    con.executemany(
        "INSERT INTO precos VALUES (:data, :seller, :categoria, :item_id, :nome, :ean, :preco_vitrine, "
        ":preco_un, :preco_atacado, :qtd_atacado, :disponibilidade, :link, :fonte)",
        [{**l, "data": agora, "seller": seller} for l in linhas])
    con.commit()
    print(f"\n{len(linhas)} itens gravados em {DB_PATH.name} ({agora}).")
    gerar_html(con)


def gerar_html(con=None):
    con = con or abrir_db()
    linhas = con.execute(
        "SELECT data, categoria, item_id, nome, preco_un, preco_atacado, qtd_atacado, "
        "disponibilidade, fonte, link FROM precos ORDER BY data").fetchall()
    seller = con.execute("SELECT seller FROM precos ORDER BY data DESC LIMIT 1").fetchone()
    dados = {
        "loja": f"Loja do CEP {CEP} ({seller[0] if seller else '?'})",
        "gerado": datetime.now().isoformat(timespec="seconds"),
        "linhas": linhas,
    }
    # "</" escapado para o JSON não fechar a tag <script>
    js = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE_PATH.read_text(encoding="utf-8").replace("/*__DADOS__*/", js)
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"Painel atualizado: {HTML_PATH}")


def historico(filtro):
    con = abrir_db()
    rows = con.execute(
        "SELECT data, nome, preco_un, preco_atacado, qtd_atacado FROM precos "
        "WHERE nome LIKE ? ORDER BY nome, data", (f"%{filtro}%",)).fetchall()
    nome_atual = None
    for data, nome, un, atac, qtd in rows:
        if nome != nome_atual:
            nome_atual = nome
            print(f"\n{nome}")
        extra = f"  (atacado {fmt(atac).strip()} >= {qtd} un)" if qtd and qtd > 1 else ""
        print(f"  {data[:16]}  {fmt(un)}{extra}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--historico", metavar="TEXTO", help="mostra o histórico dos produtos cujo nome contém TEXTO")
    ap.add_argument("--html", action="store_true", help="só regera o painel precos.html")
    args = ap.parse_args()
    if args.historico:
        historico(args.historico)
    elif args.html:
        gerar_html()
    else:
        sondar()
