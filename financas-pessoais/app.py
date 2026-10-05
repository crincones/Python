"""Financas pessoais - interface Streamlit.  Rodar com: python -m streamlit run app.py"""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from financas import analise, db, importar
from financas.categorias import A_CLASSIFICAR, CARTAO_INTER, CATEGORIAS_PADRAO, norm

st.set_page_config(page_title="Finanças pessoais", page_icon="💰", layout="wide")

MASCARA = "R$ ••••••"
MESES_ABREV = "jan fev mar abr mai jun jul ago set out nov dez".split()
try:
    ESCURO = st.context.theme.type == "dark"
except Exception:
    ESCURO = False
COR = {
    "entrada": "#3987e5" if ESCURO else "#2a78d6",
    "saida": "#d95926" if ESCURO else "#eb6834",
    "negativo": "#e66767" if ESCURO else "#e34948",
    "texto": "#c3c2b7" if ESCURO else "#52514e",
    "mudo": "#898781",
    "grade": "#2c2c2a" if ESCURO else "#e1e0d9",
    "eixo": "#383835" if ESCURO else "#c3c2b7",
}


def brl(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{'-' if v < -0.004 else ''}R$ {s}"


def soma(v) -> str:
    """Valor de saldo/somatoria: mascarado quando o olho da barra lateral esta fechado."""
    return MASCARA if OCULTO else brl(v)


def txt(v, padrao=None):
    """Texto vindo de uma tabela editavel: vazio, None e NaN viram o padrao."""
    return v.strip() if isinstance(v, str) and v.strip() else padrao


def pct(v) -> str:
    return "—" if v is None or pd.isna(v) else f"{v:+.0f}%".replace("+", "+ ").replace("-", "- ")


def rot_mes(mes: str) -> str:
    return f"{MESES_ABREV[int(mes[5:7]) - 1]}/{mes[2:4]}"


def grafico(fig: go.Figure, altura: int = 320, horizontal: bool = False) -> None:
    fig.update_layout(
        height=altura, margin=dict(l=230 if horizontal else 80, r=110 if horizontal else 16, t=28, b=40), separators=",.",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family='system-ui, -apple-system, "Segoe UI", sans-serif', size=13, color=COR["texto"]),
        legend=dict(orientation="h", y=1.12, x=0), bargap=0.32, bargroupgap=0.06,
        hovermode="y unified" if horizontal else "x unified",
    )
    valores = dict(gridcolor=COR["grade"], zerolinecolor=COR["eixo"], tickprefix="R$ ", tickformat=",.0f",
                   tickfont=dict(color=COR["mudo"]))
    categorias = dict(showgrid=False, linecolor=COR["eixo"], tickfont=dict(color=COR["mudo"]))
    fig.update_xaxes(**(valores if horizontal else categorias))
    fig.update_yaxes(**(categorias if horizontal else valores))
    if horizontal:
        fig.update_yaxes(ticksuffix="  ")
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


def barra(x, y, nome: str, cor, horizontal: bool = False, **extra) -> go.Bar:
    return go.Bar(
        x=x, y=y, name=nome, orientation="h" if horizontal else "v",
        marker=dict(color=cor, cornerradius=4),
        hovertemplate="R$ %{x:,.2f}" if horizontal else "R$ %{y:,.2f}", **extra,
    )


def cortar_picos(fig: go.Figure, rotulos: list[str], series: list[pd.Series]) -> None:
    """Se um mes destoa muito (mais que 2x o segundo maior), limita o eixo e anota o valor real."""
    todos = sorted(abs(v) for s in series for v in s)
    if len(todos) < 3 or todos[-2] <= 0 or todos[-1] <= 2 * todos[-2]:
        return
    teto = 1.25 * todos[-2]
    minimo = min(0.0, max(-teto, min(v for s in series for v in s) * 1.1))
    fig.update_yaxes(range=[minimo, teto])
    for s in series:
        for x, v in zip(rotulos, s):
            if v > teto:
                fig.add_annotation(x=x, y=teto, text=f"▲ {brl(v)}", showarrow=False, yanchor="bottom",
                                   font=dict(size=12, color=COR["texto"]))


def filtrar_texto(tabela: pd.DataFrame, coluna: pd.Series, busca: str | None) -> pd.DataFrame:
    """Linhas cuja coluna contem todas as palavras da busca (sem acento/caixa); '-palavra' exclui."""
    palavras = norm(busca).split()
    if not palavras:
        return tabela
    texto = coluna.map(norm)
    manter = pd.Series(True, index=tabela.index)
    for p in palavras:
        if p.startswith("-") and len(p) > 1:
            manter &= ~texto.str.contains(p[1:], regex=False)
        else:
            manter &= texto.str.contains(p, regex=False)
    return tabela[manter]


def seletor_periodo(meses: list[str], chave: str) -> tuple[str, str]:
    if len(meses) < 2:
        return meses[0], meses[-1]
    return st.select_slider("Período", options=meses, value=(meses[max(0, len(meses) - 12)], meses[-1]),
                            format_func=rot_mes, key=chave)


def salvou(mensagem: str) -> None:
    """Guarda o aviso, zera os editores de tabela e recarrega."""
    st.session_state["aviso"] = mensagem
    st.session_state["versao"] = st.session_state.get("versao", 0) + 1
    st.rerun()


# --------------------------------------------------------------------------- dados
con = db.conectar()
if not con.execute("SELECT 1 FROM transacoes LIMIT 1").fetchone():
    with st.spinner("Importando extrato e faturas…"):
        importar.importar_pastas(con)

HOJE = date.today()
MES_ATUAL = f"{HOJE:%Y-%m}"
V = st.session_state.get("versao", 0)
df = analise.carregar(con)
cats = db.tabela(con, "categorias")
prog = db.tabela(con, "programados")
detalhados = analise.meses_com_fatura(con)
OPCOES_CAT = sorted(cats["nome"], key=norm) + [A_CLASSIFICAR]
saldo = float(db.ler_meta(con, "saldo") or 0)
saldo_data = db.ler_meta(con, "saldo_data")

pagina = st.sidebar.radio(
    "Finanças pessoais", ["Resumo", "Transações", "Desvios", "Programados", "Importar e regras"]
)
OCULTO = db.ler_meta(con, "ocultar") == "1"
if saldo_data:
    st.sidebar.metric(f"Saldo em conta ({pd.Timestamp(saldo_data):%d/%m/%Y})", soma(saldo))
if st.sidebar.button("Mostrar valores" if OCULTO else "Ocultar valores",
                     icon=":material/visibility:" if OCULTO else ":material/visibility_off:",
                     help="Esconde o saldo e as somatórias, como o olho dos apps de banco"):
    db.gravar_meta(con, "ocultar", "0" if OCULTO else "1")
    con.commit()
    st.rerun()
if aviso := st.session_state.pop("aviso", None):
    st.toast(aviso, icon="✅")

if df.empty and pagina != "Importar e regras":
    st.info("Nenhuma transação importada. Coloque o extrato (OFX) em `extrato/` e as faturas (PDF) em "
            "`faturas-cartao/`, depois use a página **Importar e regras**.")
    st.stop()

MESES = analise.meses_entre(df["mes_ref"].min(), df["mes_ref"].max()) if not df.empty else []

# --------------------------------------------------------------------------- resumo
if pagina == "Resumo":
    st.title("Entradas × saídas")
    ini, fim = seletor_periodo(MESES, "periodo_resumo")
    d = df[df["mes_ref"].between(ini, fim)]
    r = analise.resumo_mensal(d).reindex(analise.meses_entre(ini, fim), fill_value=0.0)
    n = len(r)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entradas", soma(r["entradas"].sum()), f"{soma(r['entradas'].mean())} / mês", delta_color="off", delta_arrow="off")
    c2.metric("Saídas", soma(r["saidas"].sum()), f"{soma(r['saidas'].mean())} / mês", delta_color="off", delta_arrow="off")
    c3.metric("Resultado", soma(r["resultado"].sum()), f"{soma(r['resultado'].mean())} / mês", delta_color="off", delta_arrow="off")
    negativos = int((r["resultado"] < 0).sum())
    c4.metric("Meses no vermelho", f"{negativos} de {n}")

    pend = d[d["categoria"] == A_CLASSIFICAR]
    if not pend.empty:
        st.info(f"{len(pend)} lançamentos ({soma(pend['valor'].abs().sum())}) do período ainda estão sem "
                "categoria. Classifique-os na página **Transações** para a análise ficar completa.")

    rotulos = [rot_mes(m) for m in r.index]
    st.subheader("Por mês")
    fig = go.Figure([barra(rotulos, r["entradas"], "Entradas", COR["entrada"]),
                     barra(rotulos, r["saidas"], "Saídas", COR["saida"])])
    cortar = st.toggle("Limitar o eixo quando um mês destoa muito (o valor real aparece anotado)", value=True)
    if cortar:
        cortar_picos(fig, rotulos, [r["entradas"], r["saidas"]])
    grafico(fig)

    st.subheader("Resultado do mês (entradas − saídas)")
    cores = [COR["entrada"] if v >= 0 else COR["negativo"] for v in r["resultado"]]
    fig = go.Figure(barra(rotulos, r["resultado"], "Resultado", cores))
    if cortar:
        cortar_picos(fig, rotulos, [r["resultado"]])
    grafico(fig, altura=240)

    with st.expander("Ver tabela mensal"):
        t = r.rename(index=rot_mes, columns={"entradas": "Entradas", "saidas": "Saídas", "resultado": "Resultado"})
        st.dataframe(t.style.format(brl), width="stretch")

    st.subheader("Para onde foi o dinheiro")
    m = analise.matriz_categorias(d)
    if not m.empty:
        tot = m.sum(axis=1)
        topo = tot.head(14)
        if len(tot) > 14:
            topo = pd.concat([topo, pd.Series({"Demais categorias": tot.iloc[14:].sum()})])
        topo = topo.iloc[::-1]
        fig = go.Figure(barra(topo.values, topo.index, "Saídas", COR["saida"], horizontal=True,
                              text=[brl(v) for v in topo.values], textposition="outside", cliponaxis=False))
        grafico(fig, altura=80 + 28 * len(topo), horizontal=True)

        cat = st.selectbox("Evolução de uma categoria", list(m.index))
        serie = m.loc[cat].reindex(r.index, fill_value=0.0)
        grafico(go.Figure(barra(rotulos, serie, cat, COR["saida"])), altura=240)

        with st.expander("Ver tabela categoria × mês"):
            t = m.rename(columns=rot_mes)
            t.insert(0, "Total", tot)
            st.dataframe(t.style.format(lambda v: brl(v) if v else ""), width="stretch")

    e = analise.matriz_categorias(d, "entrada")
    if not e.empty:
        with st.expander("De onde veio o dinheiro (entradas por categoria × mês)"):
            t = e.rename(columns=rot_mes)
            t.insert(0, "Total", e.sum(axis=1))
            st.dataframe(t.style.format(lambda v: brl(v) if v else ""), width="stretch")

    st.caption("Compras no cartão entram no mês de vencimento da fatura (quando o dinheiro sai da conta). "
               "Transferências entre contas próprias, investimentos e o pagamento de faturas já detalhadas "
               "ficam fora de entradas e saídas.")

# --------------------------------------------------------------------------- transacoes
elif pagina == "Transações":
    st.title("Transações")

    fila = df[df["categoria"] == A_CLASSIFICAR].copy()
    if not fila.empty:
        fila["sinal"] = fila["valor"].map(lambda v: "+" if v > 0 else "-")
        grupos = (fila.groupby(["base", "sinal"])
                  .agg(exemplo=("descricao", "first"), qtd=("id", "count"), total=("valor", "sum"))
                  .reset_index())
        grupos = grupos.reindex(grupos["total"].abs().sort_values(ascending=False).index).reset_index(drop=True)
        grupos["categoria"] = None
        with st.expander(f"Fila de classificação — {len(grupos)} favorecidos sem categoria "
                         f"({len(fila)} lançamentos, {soma(fila['valor'].abs().sum())})", expanded=True):
            st.caption("Escolha a categoria por favorecido. Vira uma regra: vale para todos os lançamentos "
                       "dele, inclusive os que forem importados depois.")
            busca_fila = st.text_input("Favorecido contém", key="busca_fila", placeholder="ex.: shopee")
            grupos = filtrar_texto(grupos, grupos["exemplo"], busca_fila).reset_index(drop=True)
            ed = st.data_editor(
                grupos[["exemplo", "qtd", "total", "categoria", "base", "sinal"]],
                key=f"fila_{V}_{busca_fila}", hide_index=True, width="stretch", height=320,
                disabled=["exemplo", "qtd", "total"], column_order=["exemplo", "qtd", "total", "categoria"],
                column_config={
                    "exemplo": st.column_config.TextColumn("Favorecido", width="large"),
                    "qtd": st.column_config.NumberColumn("Lançamentos"),
                    "total": st.column_config.NumberColumn("Total (R$)", format="%.2f"),
                    "categoria": st.column_config.SelectboxColumn("Categoria", options=OPCOES_CAT[:-1], width="medium"),
                },
            )
            escolhidos = ed[ed["categoria"].notna()]
            if st.button(f"Salvar {len(escolhidos)} regra(s)", disabled=escolhidos.empty, type="primary"):
                con.executemany("INSERT OR REPLACE INTO regras VALUES (?, 'exata', ?, ?)",
                                [(g.base, g.sinal, g.categoria) for g in escolhidos.itertuples()])
                con.commit()
                salvou(f"{len(escolhidos)} regra(s) criada(s)")

    st.subheader("Todos os lançamentos")
    ini, fim = seletor_periodo(MESES, "periodo_trans")
    st.caption("Filtros por coluna (vazio = sem filtro). No texto, separe palavras por espaço para exigir "
               "todas e use `-palavra` para excluir.")
    f1, f2, f3 = st.columns([2, 2, 2])
    busca = f1.text_input("Descrição contém", placeholder="ex.: mercado  ou  pix -luana")
    filtro_cat = f2.multiselect("Categoria", OPCOES_CAT)
    filtro_tipo = f3.multiselect("Tipo", sorted(df["tipo"].dropna().unique(), key=norm))
    f4, f5, f6, f7, f8 = st.columns([2, 1, 1, 1, 1])
    sentido = f4.segmented_control("Sentido", ["Entradas", "Saídas", "Transferências"], selection_mode="multi")
    origem = f5.selectbox("Origem", ["Todas", "conta", "cartao"])
    filtro_cartao = f6.multiselect("Cartão", sorted(df["cartao"].dropna().unique()))
    v_min = f7.number_input("Valor mínimo (R$)", min_value=0.0, value=None, step=50.0, placeholder="sem mínimo")
    v_max = f8.number_input("Valor máximo (R$)", min_value=0.0, value=None, step=50.0, placeholder="sem máximo")

    d = df[df["mes_ref"].between(ini, fim)]
    d = filtrar_texto(d, d["descricao"], busca)
    if filtro_cat:
        d = d[d["categoria"].isin(filtro_cat)]
    if filtro_tipo:
        d = d[d["tipo"].isin(filtro_tipo)]
    if filtro_cartao:
        d = d[d["cartao"].isin(filtro_cartao)]
    if origem != "Todas":
        d = d[d["origem"] == origem]
    if sentido:
        nomes = {"Entradas": "entrada", "Saídas": "saida", "Transferências": "transferencia"}
        d = d[d["fluxo"].isin([nomes[x] for x in sentido])]
    if v_min is not None:
        d = d[d["valor"].abs() >= v_min]
    if v_max is not None:
        d = d[d["valor"].abs() <= v_max]

    st.caption(f"{len(d)} lançamentos · entradas {soma(d.loc[d['fluxo'] == 'entrada', 'valor'].sum())} · "
               f"saídas {soma(-d.loc[d['fluxo'] == 'saida', 'valor'].sum())} · "
               f"transferências {soma(d.loc[d['fluxo'] == 'transferencia', 'valor'].sum())}")
    visao = d[["id", "data", "descricao", "valor", "categoria", "tipo", "origem", "cartao", "parcela", "mes_ref", "base"]]
    filtros = (ini, fim, busca, filtro_cat, filtro_tipo, sentido, origem, filtro_cartao, v_min, v_max)
    ed = st.data_editor(
        visao.set_index("id"), key=f"trans_{V}_{filtros}", width="stretch", height=560, hide_index=True,
        disabled=["data", "descricao", "valor", "tipo", "origem", "cartao", "parcela", "mes_ref"],
        column_order=["data", "descricao", "valor", "categoria", "tipo", "origem", "cartao", "parcela", "mes_ref"],
        column_config={
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "descricao": st.column_config.TextColumn("Descrição", width="large"),
            "valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f"),
            "categoria": st.column_config.SelectboxColumn("Categoria", options=OPCOES_CAT, required=True, width="medium"),
            "tipo": "Tipo", "origem": "Origem", "cartao": "Cartão", "parcela": "Parcela", "mes_ref": "Mês de referência",
        },
    )
    mudou = ed[ed["categoria"] != visao.set_index("id")["categoria"]]
    todos = st.checkbox("Aplicar também aos demais lançamentos com a mesma descrição (cria regra)", value=True)
    if st.button(f"Salvar {len(mudou)} alteração(ões)", disabled=mudou.empty, type="primary"):
        for id_, t in mudou.iterrows():
            if todos and t["categoria"] != A_CLASSIFICAR:
                con.execute("INSERT OR REPLACE INTO regras VALUES (?, 'exata', ?, ?)",
                            (t["base"], "+" if t["valor"] > 0 else "-", t["categoria"]))
                con.execute("UPDATE transacoes SET categoria_manual = NULL WHERE id = ?", (id_,))
            else:
                manual = None if t["categoria"] == A_CLASSIFICAR else t["categoria"]
                con.execute("UPDATE transacoes SET categoria_manual = ? WHERE id = ?", (manual, id_))
        con.commit()
        salvou(f"{len(mudou)} alteração(ões) salva(s)")

# --------------------------------------------------------------------------- desvios
elif pagina == "Desvios":
    st.title("Desvios")
    fechados = [m for m in MESES if m < MES_ATUAL] or MESES
    mes = st.selectbox("Mês analisado", fechados[::-1] if MES_ATUAL not in MESES else [*fechados[::-1], MES_ATUAL],
                       format_func=rot_mes)
    if mes not in detalhados and (df[df["mes_ref"] == mes]["categoria"] == CARTAO_INTER).any():
        st.warning(f"A fatura do cartão de {rot_mes(mes)} não foi importada: os gastos do cartão aparecem em um "
                   "bloco só, sem categoria. Baixe o PDF da fatura e importe para ver o detalhe.")

    r = analise.resumo_mensal(df)
    ant = r[r.index < mes].tail(6)
    c1, c2, c3 = st.columns(3)
    for col, nome, chave, inverso in ((c1, "Entradas", "entradas", "normal"), (c2, "Saídas", "saidas", "inverse"),
                                      (c3, "Resultado", "resultado", "normal")):
        atual = r.at[mes, chave] if mes in r.index else 0.0
        delta = f"{brl(atual - ant[chave].mean())} vs média {len(ant)}m" if len(ant) and not OCULTO else None
        col.metric(nome, soma(atual), delta, delta_color=inverso)

    st.subheader("Gasto por categoria × referência")
    dv = analise.desvios_categoria(df, mes, cats, detalhados)
    if dv.empty:
        st.info("Ainda não há meses anteriores comparáveis para calcular a média.")
    else:
        st.caption("Referência = meta mensal da categoria (se definida em **Importar e regras**) ou a média dos "
                   "meses anteriores comparáveis. Fora da faixa quando passa de 20% e de R$ 50.")
        fora = dv[~dv["situacao"].str.contains("Dentro")]
        if not fora.empty:
            fora = fora.iloc[::-1]
            cores = [COR["negativo"] if v > 0 else COR["entrada"] for v in fora["diferenca"]]
            fig = go.Figure(barra(fora["diferenca"], fora["categoria"], "Diferença", cores, horizontal=True,
                                  text=[brl(v) for v in fora["diferenca"]], textposition="auto",
                                  cliponaxis=False))
            grafico(fig, altura=90 + 30 * len(fora), horizontal=True)
        st.dataframe(
            dv.style.format({"realizado": brl, "referencia": brl, "diferenca": brl, "pct": pct}),
            hide_index=True, width="stretch",
            column_config={"categoria": "Categoria", "realizado": "Realizado", "referencia": "Referência",
                           "base": "Base", "diferenca": "Diferença", "pct": "%", "situacao": "Situação"},
        )

    st.subheader("Lançamentos fora do padrão")
    at = analise.lancamentos_atipicos(df, mes)
    if at.empty:
        st.write("Nenhum lançamento atípico neste mês.")
    else:
        st.dataframe(at.style.format({"valor": brl}), hide_index=True, width="stretch", column_config={
            "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"), "descricao": "Descrição",
            "categoria": "Categoria", "valor": "Valor", "motivo": "Por que chamou atenção"})

    st.subheader("Programado × realizado")
    cz = analise.conciliar(df, prog, mes, HOJE)
    if cz.empty:
        st.write("Nenhum gasto programado para este mês. Cadastre na página **Programados**.")
    else:
        st.dataframe(cz.style.format({"previsto": brl, "realizado": brl, "diferenca": brl}), hide_index=True,
                     width="stretch", column_config={
                         "data_prevista": st.column_config.DateColumn("Previsto para", format="DD/MM/YYYY"),
                         "descricao": "Descrição", "tipo": "Tipo", "categoria": "Categoria",
                         "previsto": "Previsto", "realizado": "Realizado", "diferenca": "Diferença",
                         "situacao": "Situação"})

# --------------------------------------------------------------------------- programados
elif pagina == "Programados":
    st.title("Próximos gastos e projeção")

    st.subheader("Projeção do saldo")
    p1, p2 = st.columns([1, 2])
    n_meses = p1.slider("Meses à frente", 3, 12, 6)
    estimar = p2.toggle("Incluir o restante típico (mediana dos últimos 6 meses fechados, menos o que já "
                        "está programado como mensal)", value=True)
    pj = analise.projecao(df, prog, saldo, HOJE, n_meses, estimar)
    fig = go.Figure(go.Scatter(
        x=["hoje", *[rot_mes(m) for m in pj.index]], y=[saldo, *pj["saldo_final"]], name="Saldo projetado",
        mode="lines+markers", line=dict(color=COR["entrada"], width=2), marker=dict(size=8),
        hovertemplate="R$ %{y:,.2f}"))
    if OCULTO:  # mostra so a tendencia, sem os numeros
        fig.update_traces(hoverinfo="skip", hovertemplate=None)
        fig.update_yaxes(showticklabels=False)
    grafico(fig, altura=280)
    st.dataframe(
        pj.rename(index=rot_mes).style.format(brl).format(soma, subset=["saldo_final"]), width="stretch",
        column_config={"mes": "Mês", "entradas_programadas": "Entradas programadas",
                       "outras_entradas": "Outras entradas (estim.)", "saidas_programadas": "Saídas programadas",
                       "outras_saidas": "Outras saídas (estim.)", "resultado": "Resultado",
                       "saldo_final": "Saldo no fim do mês"})
    st.caption(f"Parte do saldo do extrato ({soma(saldo)}). No mês corrente conta só o que ainda não aconteceu.")

    st.subheader("Gastos e receitas programados")
    st.caption("Use a última linha para incluir. **Texto no extrato** é o trecho da descrição usado para "
               "reconhecer o pagamento quando ele acontecer (página Desvios).")
    edp = prog.drop(columns="id").assign(
        ativo=prog["ativo"].astype(bool), inicio=pd.to_datetime(prog["inicio"]).dt.date,
        fim=pd.to_datetime(prog["fim"]).dt.date)
    novo = st.data_editor(
        edp, key=f"prog_{V}", num_rows="dynamic", hide_index=True, width="stretch",
        column_config={
            "ativo": st.column_config.CheckboxColumn("Ativo", default=True),
            "descricao": st.column_config.TextColumn("Descrição", required=True, width="medium"),
            "tipo": st.column_config.SelectboxColumn("Tipo", options=["despesa", "receita"], default="despesa", required=True),
            "categoria": st.column_config.SelectboxColumn("Categoria", options=OPCOES_CAT[:-1]),
            "valor": st.column_config.NumberColumn("Valor (R$)", min_value=0.0, format="%.2f", required=True),
            "frequencia": st.column_config.SelectboxColumn("Frequência", options=["mensal", "anual", "unica"], default="mensal", required=True),
            "dia": st.column_config.NumberColumn("Dia", min_value=1, max_value=31, step=1),
            "inicio": st.column_config.DateColumn("Início / data", format="DD/MM/YYYY", default=HOJE, required=True),
            "fim": st.column_config.DateColumn("Fim", format="DD/MM/YYYY"),
            "padrao": st.column_config.TextColumn("Texto no extrato"),
        },
    )
    if st.button("Salvar programados", type="primary"):
        validos = novo.dropna(subset=["descricao", "valor", "inicio"])
        con.execute("DELETE FROM programados")
        con.executemany(
            "INSERT INTO programados (ativo, descricao, tipo, categoria, valor, frequencia, dia, inicio, fim, padrao) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(int(x.ativo is not False), x.descricao, txt(x.tipo, "despesa"), txt(x.categoria), float(x.valor),
              txt(x.frequencia, "mensal"), int(x.dia) if pd.notna(x.dia) else None, str(x.inicio)[:10],
              str(x.fim)[:10] if pd.notna(x.fim) else None, txt(x.padrao)) for x in validos.itertuples()])
        con.commit()
        salvou(f"{len(validos)} programado(s) salvo(s)")

    sg = analise.sugerir_recorrentes(df, prog, HOJE)
    if not sg.empty:
        st.subheader("Sugestões a partir do seu histórico")
        st.caption("Favorecidos que apareceram em pelo menos 3 dos últimos 4 meses fechados. Marque os que "
                   "quer programar como mensais; o valor é a mediana recente e pode ser ajustado aqui.")
        eds = st.data_editor(
            sg, key=f"sug_{V}", hide_index=True, width="stretch", disabled=["descricao", "tipo", "meses", "padrao"],
            column_order=["adicionar", "descricao", "tipo", "categoria", "valor", "dia", "meses"],
            column_config={
                "adicionar": st.column_config.CheckboxColumn("Programar"),
                "descricao": st.column_config.TextColumn("Favorecido", width="large"), "tipo": "Tipo",
                "categoria": st.column_config.SelectboxColumn("Categoria", options=OPCOES_CAT),
                "valor": st.column_config.NumberColumn("Valor mensal (R$)", format="%.2f"),
                "dia": st.column_config.NumberColumn("Dia", min_value=1, max_value=31),
                "meses": "Meses (de 4)",
            })
        marcados = eds[eds["adicionar"]]
        if st.button(f"Programar {len(marcados)} selecionado(s)", disabled=marcados.empty):
            con.executemany(
                "INSERT INTO programados (descricao, tipo, categoria, valor, frequencia, dia, inicio, padrao) "
                "VALUES (?, ?, ?, ?, 'mensal', ?, ?, ?)",
                [(x.descricao, x.tipo, None if x.categoria == A_CLASSIFICAR else txt(x.categoria), float(x.valor),
                  int(x.dia), f"{MES_ATUAL}-01", x.padrao) for x in marcados.itertuples()])
            con.commit()
            salvou(f"{len(marcados)} programado(s) adicionado(s)")

    pa = analise.parcelas_abertas(df, HOJE)
    if not pa.empty:
        st.subheader("Parcelas do cartão ainda a vencer")
        st.caption(f"Com base na última fatura importada. Total comprometido: {soma(pa['saldo'].sum())}. "
                   "Já estão dentro do valor da fatura; não somam de novo na projeção.")
        st.dataframe(pa.assign(ultima_parcela=pa["ultima_parcela"].map(rot_mes))
                     .style.format({"valor_parcela": brl, "saldo": brl}), hide_index=True, width="stretch",
                     column_config={"descricao": "Compra", "parcela": "Situação", "valor_parcela": "Parcela",
                                    "restantes": "Faltam", "saldo": "Saldo a pagar", "ultima_parcela": "Termina em"})

# --------------------------------------------------------------------------- importar e regras
else:
    st.title("Importar e regras")
    st.subheader("Importar extrato e faturas")
    st.caption("Extrato do Inter em **OFX** (ou CSV) e fatura do cartão Inter em **PDF**. Pode reimportar "
               "períodos que se sobrepõem: lançamentos já existentes não são duplicados.")
    enviados = st.file_uploader("Arquivos", type=["ofx", "csv", "pdf"], accept_multiple_files=True,
                                key=f"up_{V}", label_visibility="collapsed")
    b1, b2 = st.columns([1, 3])
    if b1.button("Importar", type="primary"):
        for a in enviados or []:
            pasta = db.PASTA_FATURAS if a.name.lower().endswith(".pdf") else db.PASTA_EXTRATO
            pasta.mkdir(exist_ok=True)
            (pasta / a.name).write_bytes(a.getvalue())
        st.session_state["ultimo_import"] = importar.importar_pastas(con)
        salvou("Importação concluída")
    b2.caption("Grava os arquivos enviados e relê as pastas `extrato/` e `faturas-cartao/`.")
    if (ult := st.session_state.get("ultimo_import")) is not None:
        st.dataframe(ult, hide_index=True, width="stretch", column_config={
            "arquivo": "Arquivo", "lidos": "Lançamentos lidos", "novos": "Novos", "aviso": "Aviso"})

    if not df.empty:
        conta = df[df["origem"] == "conta"]
        st.write(f"**{len(df)}** lançamentos · conta de {conta['data'].min():%d/%m/%Y} a "
                 f"{conta['data'].max():%d/%m/%Y} · **{len(detalhados)}** fatura(s) de cartão importada(s)")
        sem = df[df["categoria"] == CARTAO_INTER]
        if not sem.empty:
            with st.expander(f"{len(sem)} pagamento(s) de fatura sem o PDF correspondente"):
                st.caption("Importe a fatura com vencimento nessas datas para ver as compras por categoria.")
                st.dataframe(sem[["data", "descricao", "valor"]].style.format({"valor": brl}), hide_index=True,
                             column_config={"data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                                            "descricao": "Descrição", "valor": "Valor"})

    st.subheader("Categorias e metas mensais")
    st.caption("Tipo **transferencia** fica fora de entradas e saídas. A meta mensal (opcional) passa a ser a "
               "referência da página Desvios. Renomear uma categoria aqui não renomeia as regras que a usam.")
    edc = st.data_editor(
        cats, key=f"cats_{V}", num_rows="dynamic", hide_index=True, width="stretch", height=320,
        column_config={
            "nome": st.column_config.TextColumn("Categoria", required=True),
            "tipo": st.column_config.SelectboxColumn("Tipo", options=["despesa", "receita", "transferencia"], default="despesa", required=True),
            "meta": st.column_config.NumberColumn("Meta mensal (R$)", min_value=0.0, format="%.2f"),
        })
    if st.button("Salvar categorias"):
        novas = edc.dropna(subset=["nome"]).drop_duplicates("nome")
        fixas = {n: t for n, t in CATEGORIAS_PADRAO if t == "transferencia" or n == CARTAO_INTER}
        con.execute("DELETE FROM categorias")
        con.executemany("INSERT INTO categorias VALUES (?, ?, ?)",
                        [(x.nome.strip(), txt(x.tipo, "despesa"), float(x.meta) if pd.notna(x.meta) else None)
                         for x in novas.itertuples()])
        con.executemany("INSERT OR IGNORE INTO categorias VALUES (?, ?, NULL)", list(fixas.items()))
        con.commit()
        salvou("Categorias salvas")

    st.subheader("Regras de classificação")
    st.caption("**contem**: o texto aparece na descrição (vence o texto mais longo). **exata**: o favorecido é "
               "exatamente esse (tem prioridade). Sinal `+` vale só para entradas, `-` só para saídas. "
               "Uma categoria escolhida à mão num lançamento vence qualquer regra.")
    regras = db.tabela(con, "regras").sort_values(["modo", "padrao"], ignore_index=True)
    edr = st.data_editor(
        regras, key=f"regras_{V}", num_rows="dynamic", hide_index=True, width="stretch", height=360,
        column_config={
            "padrao": st.column_config.TextColumn("Texto", required=True, width="large"),
            "modo": st.column_config.SelectboxColumn("Modo", options=["contem", "exata"], default="contem", required=True),
            "sinal": st.column_config.SelectboxColumn("Sinal", options=["", "+", "-"], default=""),
            "categoria": st.column_config.SelectboxColumn("Categoria", options=OPCOES_CAT[:-1], required=True),
        })
    if st.button("Salvar regras"):
        novas = edr.dropna(subset=["padrao", "categoria"])
        con.execute("DELETE FROM regras")
        con.executemany("INSERT OR REPLACE INTO regras VALUES (?, ?, ?, ?)",
                        [(norm(x.padrao), txt(x.modo, "contem"), txt(x.sinal, ""), x.categoria) for x in novas.itertuples()])
        con.commit()
        salvou("Regras salvas")

con.close()
