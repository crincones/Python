# -*- coding: utf-8 -*-
"""
Backteste do indicador ntsl/PavioContra_Magenta.ntsl.

    python pavio_contra.py            -> saida/pavio_contra.json + console

O padrao (venda; compra e o espelho):
  2 a 4 candles seguidos de ALTA, depois 1 candle de BAIXA cujo pavio
  SUPERIOR mede de 25% a 90% do corpo. Venda no fechamento dele.

A pergunta e uma so: OS PAVIOS COMO DEFINIDOS FAZEM SENTIDO? Para
responder, o estudo NAO parte do padrao pronto. Gera todo candle contra
depois de 1 ou mais candles no sentido oposto (o "universo"), mede o
pavio e a contagem em cada um, resolve todos isoladamente com a engine
do projeto -- mesma simulacao, mesma convencao de caminho dentro do
candle -- e so depois compara faixas.

Controles que decidem se o filtro e filtro:
  . o mesmo universo SEM filtro de pavio
  . subconjuntos SORTEADOS do universo com o mesmo tamanho do padrao
  . o trade INVERTIDO (seguir o movimento anterior em vez de vira-lo)
  . os tres tercos do periodo
"""
import io
import json
import os
import sys

import numpy as np
import pandas as pd

import engine as E

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
os.makedirs(SAIDA, exist_ok=True)

# ------------------------------------------------------------ o padrao
BARRAS_MIN, BARRAS_MAX = 2, 4
PAVIO_MIN_PCT, PAVIO_MAX_PCT = 25.0, 90.0

ENTRADAS = ('fecha', 'meio_lim')
ROT_ENTRADA = {'fecha': 'Fechamento', 'meio_lim': 'Limitada no meio do corpo'}
GESTOES = {'parcial': dict(parcial=True),
           'puro': dict(parcial=False),
           'r2': dict(parcial=False, alvo=200.0),
           'r1': dict(parcial=False, alvo=100.0)}
ROT_GESTAO = {'parcial': '1:3 com parcial', 'puro': '1:3 sem parcial',
              'r2': '1:2 sem parcial', 'r1': '1:1 sem parcial'}

CORTES_PAV = [-0.1, 0.1, 10, 25, 45, 65, 90, 100.1]
ROT_PAV = ['0%', '1-10%', '10-25%', '25-45%', '45-65%', '65-90%', '90-100%']

_buf = io.StringIO()


def p(*a, **k):
    print(*a, **k)
    print(*a, **k, file=_buf)


def _lim(x):
    if isinstance(x, (np.floating, float)):
        x = float(x)
        return None if (np.isnan(x) or np.isinf(x)) else round(x, 4)
    if isinstance(x, (np.integer, int)) and not isinstance(x, bool):
        return int(x)
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (list, tuple)):
        return [_lim(v) for v in x]
    if isinstance(x, dict):
        return {str(k): _lim(v) for k, v in x.items()}
    return x


# ============================================================ universo
def universo(d, inverte=False):
    """Todo candle CONTRA depois de 1+ candles no sentido oposto, no mesmo
    pregao. Uma linha por candle, com a leitura do indicador medida.

    lado  = sentido do trade. Normal: o do proprio candle contra (baixa ->
            venda). inverte=True: o do movimento anterior (baixa -> compra),
            que e o controle "e se o sinal for de continuacao?".
    """
    o = d['o'].to_numpy(); h = d['h'].to_numpy()
    l = d['l'].to_numpy(); c = d['c'].to_numpy()
    dia = d['dia'].to_numpy()
    sent = np.sign(c - o).astype(int)
    n = len(d)
    linhas = []
    for b in range(1, n - 1):              # a ultima barra esta em formacao
        s = sent[b]
        if s == 0:
            continue
        k = 0
        for j in range(1, 30):
            if b - j < 0 or dia[b - j] != dia[b] or sent[b - j] != -s:
                break
            k = j
        if k == 0:
            continue
        corpo = abs(c[b] - o[b])
        # pavio do lado de onde veio o movimento = lado da ABERTURA
        pav_lado = (h[b] - o[b]) if s < 0 else (o[b] - l[b])
        pav_outro = (c[b] - l[b]) if s < 0 else (h[b] - c[b])
        ts = d['data'].iat[b]
        linhas.append(dict(
            i=b, data=ts, lado=(-s if inverte else s),
            hora=ts.hour + ts.minute / 60.0,
            n_fav=k,
            pav_pct=pav_lado / corpo * 100.0,
            pav_outro_pct=pav_outro / corpo * 100.0,
        ))
    u = pd.DataFrame(linhas)
    u['no_padrao'] = (u['n_fav'].between(BARRAS_MIN, BARRAS_MAX)
                      & (u['pav_pct'] >= PAVIO_MIN_PCT)
                      & (u['pav_pct'] <= PAVIO_MAX_PCT))
    return u


def marca_tercos(t, dias):
    c1, c2 = dias[len(dias) // 3], dias[2 * len(dias) // 3]
    t = t.copy()
    t['terco'] = np.where(t['data'] < c1, 'T1',
                          np.where(t['data'] < c2, 'T2', 'T3'))
    return t, str(pd.Timestamp(c1).date()), str(pd.Timestamp(c2).date())


def resumo_grupo(g):
    """EV, acerto e EV por terco de um grupo de sinais resolvidos."""
    g = g[g['aceito']]
    if len(g) == 0:
        return dict(n=0, ev=None, wr=None, pts=0.0,
                    ev_terco=[None] * 3, n_terco=[0] * 3)
    ev_t = []; n_t = []
    for tt in ('T1', 'T2', 'T3'):
        x = g.loc[g['terco'] == tt, 'pts']
        ev_t.append(float(x.mean()) if len(x) else None)
        n_t.append(int(len(x)))
    return dict(n=int(len(g)), ev=float(g['pts'].mean()),
                wr=float((g['pts'] > 0).mean() * 100),
                pts=float(g['pts'].sum()), ev_terco=ev_t, n_terco=n_t)


def sorteio(t, mascara, n_iter=4000, semente=20260913):
    """Subconjuntos sorteados do universo com o tamanho do padrao.

    Devolve em que percentil o EV do padrao cai. Se um filtro de pavio
    fosse inutil, o padrao seria so mais um sorteio: percentil perto de 50.
    """
    s = t[t['aceito']].reset_index(drop=True)
    m = mascara.loc[t['aceito']].to_numpy()
    ev_pad = float(s.loc[m, 'pts'].mean())
    k = int(m.sum())
    pts = s['pts'].to_numpy()
    rng = np.random.default_rng(semente)
    evs = np.array([pts[rng.choice(len(pts), k, replace=False)].mean()
                    for _ in range(n_iter)])
    return dict(ev_padrao=ev_pad, k=k, n_universo=int(len(pts)),
                ev_medio=float(evs.mean()),
                p5=float(np.percentile(evs, 5)),
                p95=float(np.percentile(evs, 95)),
                percentil=float((evs < ev_pad).mean() * 100))


def monte_carlo(pts, n=4000, semente=20260913):
    rng = np.random.default_rng(semente)
    m = len(pts)
    if m < 10:
        return {}
    tot = np.empty(n); dd = np.empty(n)
    for k in range(n):
        am = rng.choice(pts, size=m, replace=True)
        eq = np.r_[0.0, np.cumsum(am)]
        tot[k] = eq[-1]
        dd[k] = (np.maximum.accumulate(eq) - eq).max()
    return dict(p_lucro=float((tot > 0).mean() * 100),
                tot_p5=float(np.percentile(tot, 5)),
                tot_p50=float(np.percentile(tot, 50)),
                tot_p95=float(np.percentile(tot, 95)),
                dd_p50=float(np.percentile(dd, 50)),
                dd_p95=float(np.percentile(dd, 95)))


# ============================================================ principal
def main():
    d = E.carrega()
    dias = sorted(d['dia'].unique())
    p('=' * 74)
    p('BACKTESTE  PavioContra_Magenta  --  os pavios fazem sentido?')
    p('=' * 74)
    p(f"base: {len(d)} barras PI 20, {d['data'].iat[0]:%d/%m/%Y} a "
      f"{d['data'].iat[-1]:%d/%m/%Y}, {len(dias)} pregoes")

    u = universo(d)
    ui = universo(d, inverte=True)
    p(f"universo: {len(u)} candles contra depois de 1+ no sentido oposto; "
      f"{int(u['no_padrao'].sum())} no padrao "
      f"({int((u['no_padrao'] & (u['lado'] < 0)).sum())} vendas, "
      f"{int((u['no_padrao'] & (u['lado'] > 0)).sum())} compras)")

    # ------------------------------------------------ resolve tudo isolado
    res = {}
    for ent in ENTRADAS:
        for ges, gg in GESTOES.items():
            for nome, base in (('normal', u), ('inverso', ui)):
                # o inverso so existe no fechamento: a 'meio_lim' da engine
                # poe a limitada no meio do corpo A FAVOR do candle do sinal;
                # invertido, isso vira uma compra limitada ACIMA do mercado,
                # que preenche na hora e mede um prejuizo que nao e do padrao
                if nome == 'inverso' and ent != 'fecha':
                    continue
                t = E.executa(d, base, ent, gg)
                t, c1, c2 = marca_tercos(t, dias)
                res[(ent, ges, nome)] = t
    p(f"tercos: T1 ate {c1}, T2 ate {c2}, T3 depois")

    saida = dict(parametros=dict(barras_min=BARRAS_MIN, barras_max=BARRAS_MAX,
                                 pav_min=PAVIO_MIN_PCT, pav_max=PAVIO_MAX_PCT,
                                 stop=E.STOP, alvo=E.ALVO,
                                 parcial_em=E.PARCIAL_EM),
                 base=dict(barras=len(d), dias=len(dias),
                           ini=f"{d['data'].iat[0]:%d/%m/%Y}",
                           fim=f"{d['data'].iat[-1]:%d/%m/%Y}",
                           c1=c1, c2=c2),
                 rot_entrada=ROT_ENTRADA, rot_gestao=ROT_GESTAO,
                 rot_pav=ROT_PAV)

    # ------------------------------------------------ 1. o padrao x controles
    p('\n--- 1. EV por sinal (pts, isolado, bruto) ---------------------------')
    p(f"{'entrada':9s} {'gestao':16s} {'padrao':>16s} {'2-4 sem pavio':>16s} "
      f"{'2-4 fora faixa':>16s} {'inverso':>16s}")
    comp = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges, 'normal')]
            ti = res.get((ent, ges, 'inverso'))
            n24 = t['n_fav'].between(BARRAS_MIN, BARRAS_MAX)
            blocos = dict(padrao=resumo_grupo(t[t['no_padrao']]),
                          sem_filtro=resumo_grupo(t[n24]),
                          fora=resumo_grupo(t[n24 & ~t['no_padrao']]),
                          inverso=(resumo_grupo(ti[ti['no_padrao']])
                                   if ti is not None else dict(n=0)),
                          universo=resumo_grupo(t))
            comp[f'{ent}|{ges}'] = blocos

            def f(b):
                return f"{b['ev']:+6.1f} ({b['n']:4d})" if b['n'] else 'n/a'
            p(f"{ent:9s} {ROT_GESTAO[ges]:16s} {f(blocos['padrao']):>16s} "
              f"{f(blocos['sem_filtro']):>16s} {f(blocos['fora']):>16s} "
              f"{f(blocos['inverso']):>16s}")
    saida['comparacao'] = comp

    # ------------------------------------------------ 2. faixas de pavio
    p('\n--- 2. EV por faixa de pavio (2 a 4 barras antes, fechamento) -------')
    faixas = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges, 'normal')]
            s = t[t['n_fav'].between(BARRAS_MIN, BARRAS_MAX)].copy()
            s['faixa'] = pd.cut(s['pav_pct'], CORTES_PAV, labels=ROT_PAV)
            for chave, sub in (('', s), ('|compra', s[s['lado'] > 0]),
                               ('|venda', s[s['lado'] < 0])):
                linhas = []
                for rot in ROT_PAV:
                    b = resumo_grupo(sub[sub['faixa'] == rot]); b['faixa'] = rot
                    linhas.append(b)
                faixas[f'{ent}|{ges}{chave}'] = linhas
    for ges in GESTOES:
        p(f"  [{ROT_GESTAO[ges]}]")
        for b in faixas[f'fecha|{ges}']:
            if b['n'] == 0:
                p(f"    {b['faixa']:8s}    -")
                continue
            tt = ' / '.join('   -  ' if v is None else f'{v:+6.1f}'
                            for v in b['ev_terco'])
            p(f"    {b['faixa']:8s} n={b['n']:4d}  EV {b['ev']:+6.1f}  "
              f"acerto {b['wr']:4.1f}%   tercos {tt}")
    for lado in ('compra', 'venda'):
        p(f"  [1:3 com parcial, so {lado}]")
        for b in faixas[f'fecha|parcial|{lado}']:
            if b['n']:
                p(f"    {b['faixa']:8s} n={b['n']:4d}  EV {b['ev']:+6.1f}")
    saida['faixas_pavio'] = faixas

    # ------------------------------------------------ 3. barras antes
    p('\n--- 3. EV por barras antes (pavio 25-90%, fechamento) ---------------')
    nbar = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges, 'normal')]
            pav_ok = t['pav_pct'].between(PAVIO_MIN_PCT, PAVIO_MAX_PCT)
            linhas = []
            for rot, m in (('1', t['n_fav'] == 1), ('2', t['n_fav'] == 2),
                           ('3', t['n_fav'] == 3), ('4', t['n_fav'] == 4),
                           ('5+', t['n_fav'] >= 5)):
                b = resumo_grupo(t[pav_ok & m]); b['faixa'] = rot
                linhas.append(b)
            nbar[f'{ent}|{ges}'] = linhas
    for b in nbar['fecha|parcial']:
        p(f"    {b['faixa']:3s} n={b['n']:4d}  EV {b['ev']:+6.1f}  "
          f"acerto {b['wr']:4.1f}%")
    saida['barras_antes'] = nbar

    # ------------------------------------------------ 4. sorteio
    p('\n--- 4. o padrao contra subconjuntos SORTEADOS do universo 2-4 -------')
    sort = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges, 'normal')]
            s = t[t['n_fav'].between(BARRAS_MIN, BARRAS_MAX)].reset_index(drop=True)
            r = sorteio(s, s['no_padrao'])
            sort[f'{ent}|{ges}'] = r
            p(f"  {ent:9s} {ROT_GESTAO[ges]:16s} padrao {r['ev_padrao']:+6.1f}  "
              f"sorteio {r['ev_medio']:+6.1f} [{r['p5']:+6.1f} a {r['p95']:+6.1f}]"
              f"  percentil {r['percentil']:5.1f}")
    saida['sorteio'] = sort

    # ------------------------------------------------ 5. lado
    p('\n--- 5. compra x venda (padrao, fechamento) --------------------------')
    lados = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges, 'normal')]; pad = t[t['no_padrao']]
            n24 = t['n_fav'].between(BARRAS_MIN, BARRAS_MAX)
            lados[f'{ent}|{ges}'] = dict(
                compra=resumo_grupo(pad[pad['lado'] > 0]),
                venda=resumo_grupo(pad[pad['lado'] < 0]),
                compra_sem=resumo_grupo(t[n24 & (t['lado'] > 0)]),
                venda_sem=resumo_grupo(t[n24 & (t['lado'] < 0)]))
    for ges in GESTOES:
        x = lados[f'fecha|{ges}']
        p(f"  {ROT_GESTAO[ges]:16s} compra {x['compra']['ev']:+6.1f} "
          f"({x['compra']['n']}) [sem pavio {x['compra_sem']['ev']:+6.1f}]   "
          f"venda {x['venda']['ev']:+6.1f} ({x['venda']['n']}) "
          f"[sem pavio {x['venda_sem']['ev']:+6.1f}]")
    saida['lados'] = lados

    # ------------------------------------------------ 6. horario
    horas = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges, 'normal')]; pad = t[t['no_padrao']].copy()
            pad['h'] = pad['hora'].astype(int)
            linhas = []
            for hh in range(9, 19):
                b = resumo_grupo(pad[pad['h'] == hh]); b['faixa'] = f'{hh}h'
                linhas.append(b)
            horas[f'{ent}|{ges}'] = linhas
    saida['horas'] = horas

    # ------------------------------------------------ 7. carteira (1 por vez)
    p('\n--- 6. carteira, uma posicao por vez (padrao) -----------------------')
    cart = {}
    trades_json = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            for rot_var, filtro in (('padrao', 'no_padrao'), ('sem_filtro', None)):
                t = res[(ent, ges, 'normal')]
                if filtro:
                    sel = t[t[filtro]]
                else:
                    sel = t[t['n_fav'].between(BARRAS_MIN, BARRAS_MAX)]
                c = E.carteira(sel)
                st = E.estatisticas(c)
                if len(c):
                    ini = d['data'].iat[0]; fim = d['data'].iat[-1]
                    xs = ((c['data_sai'] - ini) / (fim - ini)).tolist()
                    st['xs'] = xs
                    st['dt'] = [f'{x:%d/%m %H:%M}' for x in c['data_sai']]
                    st['mc'] = monte_carlo(c['pts'].to_numpy())
                    st['mfe'] = c['mfe'].tolist(); st['mae'] = c['mae'].tolist()
                    st['pts'] = c['pts'].tolist()
                    st['dur_s'] = c['dur_s'].tolist()
                    st['barras'] = c['barras'].tolist()
                    st['motivos'] = c['motivo'].value_counts().to_dict()
                cart[f'{ent}|{ges}|{rot_var}'] = st
                if rot_var == 'padrao':
                    trades_json[f'{ent}|{ges}'] = [
                        dict(i=int(r.i), i_ent=int(r.i_ent), i_sai=int(r.i_sai),
                             lado=int(r.lado), ent=float(r.preco_ent),
                             sai=float(r.preco_sai), pts=float(r.pts),
                             mfe=float(r.mfe), mae=float(r.mae),
                             motivo=r.motivo, n_fav=int(r.n_fav),
                             pav=float(r.pav_pct),
                             data=f'{r.data:%d/%m/%Y %H:%M:%S}')
                        for r in c.itertuples()]
                if rot_var == 'padrao' and ent == 'fecha':
                    p(f"  {ent:9s} {ROT_GESTAO[ges]:16s} trades {st['trades']:4d}  "
                      f"liq {st['lucro_liq']:+8.0f}  FL {st['fator_lucro']:.2f}  "
                      f"acerto {st['winrate']:4.1f}%  DD {st['dd_max']:6.0f}")
    saida['carteira'] = cart
    saida['trades'] = trades_json

    # ------------------------------------------------ candles para o kline
    saida['candles'] = dict(
        t=[int(x.value // 10**6) for x in d['data']],
        o=d['o'].tolist(), h=d['h'].tolist(),
        l=d['l'].tolist(), c=d['c'].tolist())

    # ------------------------------------------------ sensibilidade a custo
    custo = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges, 'normal')]
            pad = t[t['no_padrao'] & t['aceito']]
            custo[f'{ent}|{ges}'] = {str(cc): float(pad['pts'].mean() - cc)
                                     for cc in (0, 5, 10)}
    saida['custo'] = custo

    with open(os.path.join(SAIDA, 'pavio_contra.json'), 'w', encoding='utf-8') as f:
        json.dump(_lim(saida), f, ensure_ascii=False)
    with open(os.path.join(SAIDA, 'pavio_contra_console.txt'), 'w',
              encoding='utf-8') as f:
        f.write(_buf.getvalue())
    p('\ngravado: saida/pavio_contra.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
