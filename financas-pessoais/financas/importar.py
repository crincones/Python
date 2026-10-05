"""Importadores: extrato do Banco Inter (OFX ou CSV) e fatura do cartao Inter (PDF).

Reimportar o mesmo periodo nao duplica: cada lancamento tem como chave
data + valor + descricao + ordem entre lancamentos identicos.
"""
import hashlib
import re
import sqlite3
from collections import Counter
from pathlib import Path

import pandas as pd

from . import db
from .categorias import ENTRE_CONTAS, norm

MESES = {m: i + 1 for i, m in enumerate("jan fev mar abr mai jun jul ago set out nov dez".split())}
_RE_DATA_FATURA = re.compile(r"(\d{2}) de (\w{3})\. (\d{4})")
_RE_VALOR_FATURA = re.compile(r"(\+ )?R\$ ([\d.]+,\d{2})")
_RE_PARCELA = re.compile(r"\(Parcela (\d+) de (\d+)\)")


def _valor_br(texto: str) -> float:
    return float(texto.replace(".", "").replace(",", "."))


def _com_chaves(linhas: list[dict]) -> list[dict]:
    vistos: Counter = Counter()
    for t in linhas:
        chave = (t["origem"], t.get("fatura_venc"), t.get("cartao"), t["data"], f"{t['valor']:.2f}",
                 norm(t["descricao"]))
        vistos[chave] += 1
        t["id"] = hashlib.sha1(f"{chave}|{vistos[chave]}".encode()).hexdigest()[:16]
    return linhas


def _ler_texto(caminho: Path) -> str:
    dados = caminho.read_bytes()
    try:
        return dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        return dados.decode("cp1252")


def ler_ofx(caminho: Path) -> tuple[list[dict], dict]:
    texto = _ler_texto(caminho)

    def campo(bloco: str, tag: str) -> str:
        m = re.search(rf"<{tag}>([^<\r\n]*)", bloco)
        return m.group(1).strip() if m else ""

    linhas = []
    for bloco in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", texto, flags=re.S):
        d = campo(bloco, "DTPOSTED")
        memo, nome = campo(bloco, "MEMO"), campo(bloco, "NAME")
        tipo = memo.split(":")[0].strip()
        if nome and norm(tipo).endswith(norm(nome)) and len(norm(tipo)) > len(norm(nome)):
            tipo = tipo[: len(tipo) - len(nome)].strip()
        linhas.append({
            "origem": "conta",
            "data": f"{d[:4]}-{d[4:6]}-{d[6:8]}",
            "tipo": tipo,
            "descricao": nome or tipo,
            "valor": float(campo(bloco, "TRNAMT")),
        })
    info = {}
    saldo = re.search(r"<LEDGERBAL>.*?<BALAMT>([-\d.]+).*?<DTASOF>(\d{8})", texto, flags=re.S)
    if saldo:
        d = saldo.group(2)
        info = {"saldo": float(saldo.group(1)), "saldo_data": f"{d[:4]}-{d[4:6]}-{d[6:8]}"}
    return linhas, info


def ler_csv(caminho: Path) -> tuple[list[dict], dict]:
    texto = _ler_texto(caminho).splitlines()
    inicio = next(i for i, linha in enumerate(texto) if linha.startswith("Data Lan"))
    linhas = []
    for linha in texto[inicio + 1:]:
        partes = linha.split(";")
        if len(partes) < 5:
            continue
        dia, mes, ano = partes[0].split("/")
        tipo = partes[1].strip()
        linhas.append({
            "origem": "conta",
            "data": f"{ano}-{mes}-{dia}",
            "tipo": tipo,
            "descricao": partes[2].strip() or tipo,
            "valor": _valor_br(partes[3]),
        })
    info = {}
    if linhas:
        ultimo = texto[inicio + 1].split(";")
        info = {"saldo": _valor_br(ultimo[4]), "saldo_data": linhas[0]["data"]}
    return linhas, info


def ler_fatura_pdf(caminho: Path) -> tuple[list[dict], dict]:
    import pymupdf

    with pymupdf.open(caminho) as doc:
        texto = "\n".join(pagina.get_text() for pagina in doc)
    total = re.search(r"Total da sua fatura\s*\n\s*R\$ ([\d.,]+)", texto)
    venc = re.search(r"Data de Vencimento\s*\n\s*(\d{2})/(\d{2})/(\d{4})", texto)
    if not total or not venc:
        raise ValueError("não parece uma fatura do cartão Inter")
    vencimento = f"{venc.group(3)}-{venc.group(2)}-{venc.group(1)}"
    titular = re.search(r"\n([^\n]+)\n\d{4}\*{4}\d{4}\n", texto)

    linhas, cartao = [], ""
    bruto = [linha.strip() for linha in texto.split("\n")]
    i = 0
    while i < len(bruto):
        if m := re.fullmatch(r"CARTÃO (\d{4}\*{4}\d{4})", bruto[i]):
            cartao = m.group(1)
        if m := _RE_DATA_FATURA.fullmatch(bruto[i]):
            # data / movimentacao (1+ linhas) / beneficiario / valor
            j = i + 1
            while j < len(bruto) and j < i + 8 and not _RE_VALOR_FATURA.fullmatch(bruto[j]):
                j += 1
            v = _RE_VALOR_FATURA.fullmatch(bruto[j]) if j < len(bruto) else None
            if v and j >= i + 3:
                desc = " ".join(bruto[i + 1:j - 1])
                valor = _valor_br(v.group(2)) * (1 if v.group(1) else -1)
                if not norm(desc).startswith(("PAGTO", "PAGAMENTO")):  # quitacao da fatura anterior
                    parcela = _RE_PARCELA.search(desc)
                    linhas.append({
                        "origem": "cartao",
                        "data": f"{m.group(3)}-{MESES[m.group(2)]:02d}-{m.group(1)}",
                        "tipo": "Estorno no cartão" if valor > 0 else "Compra no cartão",
                        "descricao": desc,
                        "valor": valor,
                        "cartao": cartao,
                        "parcela": f"{int(parcela.group(1))}/{int(parcela.group(2))}" if parcela else None,
                        "fatura_venc": vencimento,
                    })
                i = j
        i += 1
    info = {
        "vencimento": vencimento,
        "total": _valor_br(total.group(1)),
        "titular": titular.group(1).strip() if titular else None,
    }
    return linhas, info


def _gravar(con: sqlite3.Connection, linhas: list[dict], arquivo: str) -> int:
    antes = con.total_changes
    con.executemany(
        """INSERT OR IGNORE INTO transacoes
           (id, origem, data, mes_ref, tipo, descricao, valor, cartao, parcela, fatura_venc, arquivo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(t["id"], t["origem"], t["data"], (t.get("fatura_venc") or t["data"])[:7], t["tipo"],
          t["descricao"], t["valor"], t.get("cartao"), t.get("parcela"), t.get("fatura_venc"), arquivo)
         for t in _com_chaves(linhas)],
    )
    return con.total_changes - antes


def importar_arquivo(con: sqlite3.Connection, caminho: Path) -> dict:
    """Importa um arquivo e devolve {'arquivo', 'lidos', 'novos', 'aviso'}."""
    res = {"arquivo": caminho.name, "lidos": 0, "novos": 0, "aviso": ""}
    try:
        ext = caminho.suffix.lower()
        if ext == ".pdf":
            linhas, info = ler_fatura_pdf(caminho)
            soma = -sum(t["valor"] for t in linhas)
            if abs(soma - info["total"]) > 0.01:
                res["aviso"] = f"soma dos itens ({soma:.2f}) difere do total da fatura ({info['total']:.2f})"
            con.execute("INSERT OR REPLACE INTO faturas VALUES (?, ?, ?)",
                        (info["vencimento"], info["total"], caminho.name))
            if info["titular"]:  # Pix de/para o proprio titular = transferencia entre contas
                con.execute("INSERT OR IGNORE INTO regras VALUES (?, 'exata', '', ?)",
                            (norm(info["titular"]), ENTRE_CONTAS))
        elif ext in (".ofx", ".csv"):
            linhas, info = (ler_ofx if ext == ".ofx" else ler_csv)(caminho)
            if info and info["saldo_data"] >= (db.ler_meta(con, "saldo_data") or ""):
                db.gravar_meta(con, "saldo", str(info["saldo"]))
                db.gravar_meta(con, "saldo_data", info["saldo_data"])
        else:
            res["aviso"] = "formato não suportado"
            return res
        res["lidos"] = len(linhas)
        res["novos"] = _gravar(con, linhas, caminho.name)
        con.commit()
    except Exception as e:  # arquivo fora do padrao nao deve derrubar os demais
        con.rollback()
        res["aviso"] = f"erro: {e}"
    return res


def importar_pastas(con: sqlite3.Connection) -> pd.DataFrame:
    """Importa tudo de extrato/ (OFX; CSV so se nao houver OFX de mesmo nome) e faturas-cartao/."""
    arquivos = sorted(db.PASTA_EXTRATO.glob("*.ofx"))
    com_ofx = {a.stem.upper().replace("OFX", "") for a in arquivos}
    arquivos += [a for a in sorted(db.PASTA_EXTRATO.glob("*.csv"))
                 if a.stem.upper().replace("CSV", "") not in com_ofx]
    arquivos += sorted(db.PASTA_FATURAS.glob("*.pdf"))
    return pd.DataFrame([importar_arquivo(con, a) for a in arquivos],
                        columns=["arquivo", "lidos", "novos", "aviso"])
