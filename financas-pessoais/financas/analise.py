"""Calculos: resumo mensal, desvios, programados x realizado, recorrencias e projecao."""
import calendar
import sqlite3
from datetime import date

import pandas as pd

from . import db
from .categorias import ENTRE_CONTAS, classificar, norm


def carregar(con: sqlite3.Connection) -> pd.DataFrame:
    """Todas as transacoes ja classificadas (colunas extras: base, categoria, fluxo)."""
    df = db.tabela(con, "transacoes")
    df["data"] = pd.to_datetime(df["data"])
    df = classificar(df, db.tabela(con, "regras"), db.tabela(con, "categorias"), db.tabela(con, "faturas"))
    return df.sort_values(["data", "id"], ascending=[False, True], ignore_index=True)


def meses_entre(inicio: str, fim: str) -> list[str]:
    return [str(p) for p in pd.period_range(inicio, fim, freq="M")]


def somar_mes(mes: str, n: int) -> str:
    return str(pd.Period(mes, freq="M") + n)


def resumo_mensal(df: pd.DataFrame) -> pd.DataFrame:
    """Entradas, saidas e resultado por mes (saidas em valor positivo)."""
    if df.empty:
        return pd.DataFrame(columns=["entradas", "saidas", "resultado"])
    meses = meses_entre(df["mes_ref"].min(), df["mes_ref"].max())
    ent = df[df["fluxo"] == "entrada"].groupby("mes_ref")["valor"].sum()
    sai = -df[df["fluxo"] == "saida"].groupby("mes_ref")["valor"].sum()
    r = pd.DataFrame({"entradas": ent, "saidas": sai}).reindex(meses).fillna(0.0)
    r["resultado"] = r["entradas"] - r["saidas"]
    r.index.name = "mes"
    return r


def matriz_categorias(df: pd.DataFrame, fluxo: str = "saida") -> pd.DataFrame:
    """Categoria x mes, em valor positivo, ordenada pelo total."""
    d = df[df["fluxo"] == fluxo]
    if d.empty:
        return pd.DataFrame()
    sinal = -1 if fluxo == "saida" else 1
    m = (d.pivot_table(index="categoria", columns="mes_ref", values="valor", aggfunc="sum", fill_value=0.0)
         * sinal)
    m = m.reindex(columns=meses_entre(m.columns.min(), m.columns.max()), fill_value=0.0) + 0.0  # tira o -0.0
    return m.loc[m.sum(axis=1).sort_values(ascending=False).index]


def meses_com_fatura(con: sqlite3.Connection) -> set[str]:
    return {v[:7] for (v,) in con.execute("SELECT vencimento FROM faturas")}


def desvios_categoria(df: pd.DataFrame, mes: str, categorias: pd.DataFrame, detalhados: set[str],
                      janela: int = 6) -> pd.DataFrame:
    """Gasto do mes por categoria contra a meta ou a media dos meses anteriores.

    A media usa so meses com o mesmo nivel de detalhe do cartao (com ou sem fatura importada),
    senao 'Mercado' de um mes detalhado seria comparado com zero.
    """
    m = matriz_categorias(df)
    if m.empty or mes not in m.columns:
        return pd.DataFrame()
    anteriores = [c for c in m.columns if c < mes and (c in detalhados) == (mes in detalhados)][-janela:]
    metas = categorias.set_index("nome")["meta"]
    linhas = []
    for cat in m.index:
        real = m.at[cat, mes]
        media = m.loc[cat, anteriores].mean() if anteriores else float("nan")
        meta = metas.get(cat)
        tem_meta = pd.notna(meta) and meta > 0
        ref = meta if tem_meta else media
        if pd.isna(ref) or (real == 0 and ref == 0):
            continue
        dif = real - ref
        tolerancia = max(50.0, 0.2 * ref)
        situacao = "🔺 Acima" if dif > tolerancia else "🔻 Abaixo" if dif < -tolerancia else "✅ Dentro"
        linhas.append({
            "categoria": cat, "realizado": real, "referencia": ref,
            "base": "meta" if tem_meta else f"média {len(anteriores)}m",
            "diferenca": dif, "pct": dif / ref * 100 if ref else float("nan"), "situacao": situacao,
        })
    r = pd.DataFrame(linhas)
    return r.sort_values("diferenca", ascending=False, ignore_index=True) if not r.empty else r


def lancamentos_atipicos(df: pd.DataFrame, mes: str) -> pd.DataFrame:
    """Saidas do mes fora do padrao: valor muito acima do habitual, favorecido novo de valor alto
    ou possivel duplicidade."""
    saidas = df[(df["fluxo"] == "saida") & (df["valor"] < 0)]
    do_mes = saidas[saidas["mes_ref"] == mes]
    hist = saidas[saidas["mes_ref"] < mes].groupby("base")["valor"].agg(["count", "median"])
    repetidos = do_mes.groupby(["origem", "data", "base", "valor"])["id"].transform("count")
    linhas = []
    for t, rep in zip(do_mes.itertuples(), repetidos):
        v = -t.valor
        motivo = None
        if t.base in hist.index and hist.at[t.base, "count"] >= 3:
            habitual = -hist.at[t.base, "median"]
            if v > 2 * habitual and v - habitual >= 50:
                reais = f"{habitual:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                motivo = f"{v / habitual:.1f}x o valor habitual (R$ {reais})".replace(".", ",", 1)
        elif t.base not in hist.index and v >= 300 and not hist.empty:
            motivo = "Favorecido novo de valor alto"
        if not motivo and rep > 1 and v >= 50:
            motivo = f"Possível duplicidade ({rep} lançamentos iguais no dia)"
        if motivo:
            linhas.append({"data": t.data, "descricao": t.descricao, "categoria": t.categoria,
                           "valor": v, "motivo": motivo})
    r = pd.DataFrame(linhas, columns=["data", "descricao", "categoria", "valor", "motivo"])
    return r.sort_values("valor", ascending=False, ignore_index=True)


def ocorrencias(prog: pd.DataFrame, mes: str) -> pd.DataFrame:
    """Programados ativos que vencem no mes, com a coluna data_prevista."""
    p = pd.Period(mes, freq="M")
    ultimo_dia = calendar.monthrange(p.year, p.month)[1]
    linhas = []
    for r in prog[prog["ativo"] == 1].itertuples():
        inicio = pd.Timestamp(r.inicio)
        fim = pd.Timestamp(r.fim) if isinstance(r.fim, str) and r.fim else None
        if r.frequencia == "unica":
            previsto = inicio
        else:
            dia = min(int(r.dia) if pd.notna(r.dia) and r.dia else inicio.day, ultimo_dia)
            previsto = pd.Timestamp(p.year, p.month, dia)
            if r.frequencia == "anual" and inicio.month != p.month:
                continue
            if inicio.to_period("M") > p or (fim is not None and fim < previsto):
                continue
        if previsto.to_period("M") == p:
            linhas.append({**r._asdict(), "data_prevista": previsto})
    return pd.DataFrame(linhas, columns=["Index", *prog.columns, "data_prevista"]).drop(columns="Index")


def conciliar(df: pd.DataFrame, prog: pd.DataFrame, mes: str, hoje: date) -> pd.DataFrame:
    """Programado x realizado no mes. Realizado = soma dos lancamentos cujo texto contem o padrao."""
    do_mes = df[df["mes_ref"] == mes]
    textos = (do_mes["tipo"].fillna("") + " " + do_mes["descricao"].fillna("")).map(norm)
    linhas = []
    for o in ocorrencias(prog, mes).itertuples():
        despesa = o.tipo == "despesa"
        achados = do_mes[textos.str.contains(norm(o.padrao) or norm(o.descricao), regex=False)
                         & ((do_mes["valor"] < 0) == despesa)]
        realizado = abs(achados["valor"].sum()) if not achados.empty else None
        if realizado is None:
            situacao = "⏰ Atrasado" if o.data_prevista.date() < hoje else "🕓 Pendente"
        elif abs(realizado - o.valor) > max(1.0, 0.1 * o.valor):
            situacao = "⚠️ Pago com diferença"
        else:
            situacao = "✅ Pago"
        linhas.append({
            "data_prevista": o.data_prevista, "descricao": o.descricao, "tipo": o.tipo,
            "categoria": o.categoria, "previsto": o.valor, "realizado": realizado,
            "diferenca": None if realizado is None else realizado - o.valor, "situacao": situacao,
        })
    cols = ["data_prevista", "descricao", "tipo", "categoria", "previsto", "realizado", "diferenca", "situacao"]
    return pd.DataFrame(linhas, columns=cols).sort_values("data_prevista", ignore_index=True)


def sugerir_recorrentes(df: pd.DataFrame, prog: pd.DataFrame, hoje: date) -> pd.DataFrame:
    """Favorecidos da conta presentes em pelo menos 3 dos ultimos 4 meses fechados."""
    atual = f"{hoje:%Y-%m}"
    ultimos = [somar_mes(atual, -i) for i in range(4, 0, -1)]
    conta = df[(df["origem"] == "conta") & df["mes_ref"].isin(ultimos) & (df["categoria"] != ENTRE_CONTAS)]
    ja = [norm(p) or norm(d) for p, d in zip(prog["padrao"], prog["descricao"])]
    linhas = []
    for (b, despesa), g in conta.groupby(["base", conta["valor"] < 0]):
        por_mes = g.groupby("mes_ref")["valor"].sum().abs()
        if len(por_mes) < 3 or len(g) > 2 * len(por_mes) or any(p in b for p in ja):
            continue
        linhas.append({
            "adicionar": False, "descricao": g["descricao"].iloc[0],
            "tipo": "despesa" if despesa else "receita", "categoria": g["categoria"].iloc[0],
            "valor": round(float(por_mes.tail(3).median()), 2), "dia": int(g["data"].dt.day.median()),
            "meses": len(por_mes), "padrao": b,
        })
    cols = ["adicionar", "descricao", "tipo", "categoria", "valor", "dia", "meses", "padrao"]
    return pd.DataFrame(linhas, columns=cols).sort_values("valor", ascending=False, ignore_index=True)


def parcelas_abertas(df: pd.DataFrame, hoje: date) -> pd.DataFrame:
    """Compras parceladas da ultima fatura importada que ainda tem parcelas a vencer."""
    cartao = df[(df["origem"] == "cartao") & df["parcela"].notna()]
    cols = ["descricao", "parcela", "valor_parcela", "restantes", "saldo", "ultima_parcela"]
    if cartao.empty:
        return pd.DataFrame(columns=cols)
    ultima = cartao["mes_ref"].max()
    linhas = []
    for t in cartao[cartao["mes_ref"] == ultima].itertuples():
        k, n = (int(x) for x in t.parcela.split("/"))
        fim = somar_mes(ultima, n - k)
        restantes = min(n - k, (pd.Period(fim, freq="M") - pd.Period(f"{hoje:%Y-%m}", freq="M")).n + 1)
        if restantes > 0:
            linhas.append({"descricao": t.descricao, "parcela": f"{n - restantes}/{n} pagas",
                           "valor_parcela": -t.valor, "restantes": restantes,
                           "saldo": -t.valor * restantes, "ultima_parcela": fim})
    return pd.DataFrame(linhas, columns=cols).sort_values("saldo", ascending=False, ignore_index=True)


def projecao(df: pd.DataFrame, prog: pd.DataFrame, saldo: float, hoje: date, meses: int = 6,
             estimar: bool = True) -> pd.DataFrame:
    """Fluxo previsto mes a mes: programados + (opcional) o restante tipico, estimado pela
    mediana dos 6 ultimos meses fechados menos o que ja esta programado como mensal."""
    atual = f"{hoje:%Y-%m}"
    r = resumo_mensal(df)
    fechados = r[r.index < atual].tail(6)
    mensal = prog[(prog["ativo"] == 1) & (prog["frequencia"] == "mensal")]
    resto_sai = resto_ent = 0.0
    if estimar and not fechados.empty:
        resto_sai = max(0.0, fechados["saidas"].median() - mensal.loc[mensal["tipo"] == "despesa", "valor"].sum())
        resto_ent = max(0.0, fechados["entradas"].median() - mensal.loc[mensal["tipo"] == "receita", "valor"].sum())
    linhas = []
    for i in range(meses):
        mes = somar_mes(atual, i)
        if i == 0:  # mes corrente: so o que ainda nao aconteceu
            c = conciliar(df, prog, mes, hoje)
            oc = c[c["realizado"].isna()].rename(columns={"previsto": "valor"})
            dias = calendar.monthrange(hoje.year, hoje.month)[1]
            fracao = (dias - hoje.day) / dias
        else:
            oc, fracao = ocorrencias(prog, mes), 1.0
        ent_prog = oc.loc[oc["tipo"] == "receita", "valor"].sum()
        sai_prog = oc.loc[oc["tipo"] == "despesa", "valor"].sum()
        ent, sai = ent_prog + resto_ent * fracao, sai_prog + resto_sai * fracao
        saldo += ent - sai
        linhas.append({"mes": mes, "entradas_programadas": ent_prog, "outras_entradas": resto_ent * fracao,
                       "saidas_programadas": sai_prog, "outras_saidas": resto_sai * fracao,
                       "resultado": ent - sai, "saldo_final": saldo})
    return pd.DataFrame(linhas).set_index("mes")
