# -*- coding: utf-8 -*-
"""
Filtros ORTOGONAIS a Hull para o Hull + pavios: velocidade, horario e
posicao do preco no dia.

    python ortogonais.py            -> saida/ortogonais.json + console
    python relatorio_ortogonais.py  -> ortogonais.html + ORTOGONAIS.md

A Hull 50 responde "para que lado o preco andou nos ultimos ~50 candles".
Filtros tirados do mesmo fechamento repetem isso (osciladores.py mostrou:
o que ajudava era tendencia de novo). Aqui entram tres informacoes que a
Hull nao tem, e a ortogonalidade e MEDIDA, nao suposta.

Os mesmos sinais de hull_contra.py / osciladores.py (compra; venda e o
espelho): h = Hull 50 a favor + 2 a 4 candles contra + 1 a favor;
cand = h + 2 a 3 candles + pavio do fechamento ate 10% ("Hull + pavios").

As regras, SEIS, fechadas antes de medir (tudo lido no fechamento do candle
de sinal, com o que ja existia):

  VELOCIDADE -- a gestao e fixa em pontos (stop 100, alvo 300, zera no fim
  do dia); mercado parado quase nunca leva ao alvo a tempo.
    ritmo   candles de 20 PI por minuto na ultima hora do mesmo pregao
            (na primeira hora, no tempo decorrido, com piso de 15 min),
            dividido pela mediana do proprio ritmo nas 5.000 barras
            anteriores (~13 pregoes) -- causal.
    V1  ritmo acima da mediana (ritmo > 1)
    V2  ritmo fora do quartil mais baixo (so descarta o mercado parado)

  HORARIO -- nao depende do preco por construcao. 10h e a abertura do
  mercado a vista.
    H1  sinal entre 10:00 e 15:00
    H2  sinal a partir das 10:00

  POSICAO NO DIA -- a ancora e a sessao, nao os ultimos 50 candles.
    VWAP do dia com o volume AGRESSOR (compra + venda) e o preco tipico
    (max + min + fech) / 3, acumulada do primeiro candle do pregao ate o
    sinal. A base do robo nao tem volume total; na base antiga os dois tem
    correlacao de 0,995.
    P1  compra com o fechamento acima da VWAP do dia (venda: abaixo)
    P2  compra com o fechamento acima da abertura do pregao (venda: abaixo)

Ortogonalidade: correlacao de posto de cada leitura (e de cada regra) com a
inclinacao da Hull, a distancia Hull - EMA 21 e o MACD, dentro dos sinais.
Acima de 0,3 em modulo, a regra nao e informacao nova.

Controles, os mesmos de osciladores.py: permutacao, tercos, lados, blocos
antes/original/depois, sorteio, BUSCA (6 regras x 2 sentidos contra
resultados embaralhados), ESCOLHA FORA (antes -> resto; T1+T2 -> T3), poder,
e uma vizinhanca pequena (janela do ritmo 30/60/120 min; fim do horario
14h/15h/16h).
"""
import io
import json
import os
import sys

import numpy as np
import pandas as pd

import engine as E
import pavio_contra as P
import hull_contra as HC
import periodos as PR
import osciladores as O

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')

JANELA_MIN = 60
REF_BARRAS = 5000
H_INI, H_FIM = 10.0, 15.0

REGRAS = {
    'V1': ('Velocidade', 'Ritmo da ultima hora acima da mediana'),
    'V2': ('Velocidade', 'Ritmo fora do quartil mais baixo'),
    'H1': ('Horario', 'Sinal entre 10:00 e 15:00'),
    'H2': ('Horario', 'Sinal a partir das 10:00'),
    'P1': ('Posicao no dia', 'Fechamento do lado do trade na VWAP do dia'),
    'P2': ('Posicao no dia', 'Fechamento do lado do trade na abertura do pregao'),
}
CONTINUAS = {
    'ritmo_r': 'Ritmo da ultima hora / mediana',
    'hora': 'Hora do sinal',
    'vwap_atr': 'Distancia a VWAP do dia, em ATR (a favor)',
    'abre_atr': 'Distancia a abertura do pregao, em ATR (a favor)',
}
REF_HULL = {'incl_hull': 'Inclinacao da Hull (ATR)', 'sep_hull': 'Hull - EMA 21 (ATR)',
            'macd_atr': 'MACD (ATR)'}

_buf = io.StringIO()


def p(*a, **k):
    print(*a, **k)
    print(*a, **k, file=_buf)


# ============================================================== leituras
def ritmo(d, janela=JANELA_MIN, ref=REF_BARRAS):
    """Candles por minuto na janela, dividido pela mediana causal."""
    # minutos desde uma origem fixa -- independente da resolucao interna do datetime
    t = ((d['data'] - pd.Timestamp('2000-01-01')) // pd.Timedelta(minutes=1)).to_numpy()
    dia = d['dia'].to_numpy()
    n = len(d)
    taxa = np.full(n, np.nan)
    ini_dia = 0
    for i in range(n):
        if i == 0 or dia[i] != dia[i - 1]:
            ini_dia = i
        a = np.searchsorted(t[ini_dia:i + 1], t[i] - janela, side='right') + ini_dia
        decorrido = t[i] - t[ini_dia] + 1
        taxa[i] = (i - a + 1) / max(15, min(janela, decorrido))
    med = pd.Series(taxa).rolling(ref, min_periods=ref // 2).median().shift(1).to_numpy()
    return taxa, taxa / med


def vwap_dia(d):
    tip = (d['h'] + d['l'] + d['c']) / 3.0
    vol = (d['agr_c'] + d['agr_v']).astype(float)
    g = d['dia']
    num = (tip * vol).groupby(g).cumsum()
    den = vol.groupby(g).cumsum()
    return (num / den.replace(0, np.nan)).to_numpy()


def leituras(d, janela=JANELA_MIN):
    taxa, rr = ritmo(d, janela)
    ab = d.groupby('dia')['o'].transform('first').to_numpy()
    return dict(taxa=taxa, ritmo_r=rr, vwap=vwap_dia(d), abertura=ab)


def atributos(u, d, L, h_fim=H_FIM, q_ritmo=None):
    i = u['i'].to_numpy(int); ld = u['lado'].to_numpy(int)
    at = d['atr'].to_numpy(float); c = d['c'].to_numpy(float)
    hu = d['hma'].to_numpy(float); em = d['ema'].to_numpy(float)
    u = u.copy()
    u['ritmo_r'] = L['ritmo_r'][i]
    u['vwap_atr'] = (c[i] - L['vwap'][i]) * ld / at[i]
    u['abre_atr'] = (c[i] - L['abertura'][i]) * ld / at[i]
    u['incl_hull'] = (hu[i] - hu[i - 1]) * ld / at[i]
    u['sep_hull'] = (hu[i] - em[i]) * ld / at[i]
    ema12 = E._ema(c, 12); ema26 = E._ema(c, 26)
    u['macd_atr'] = (ema12[i] - ema26[i]) * ld / at[i]
    if q_ritmo is None:
        q_ritmo = float(np.nanpercentile(u['ritmo_r'], 25))
    u['V1'] = u['ritmo_r'] > 1
    u['V2'] = u['ritmo_r'] > q_ritmo
    u['H1'] = (u['hora'] >= H_INI) & (u['hora'] < h_fim)
    u['H2'] = u['hora'] >= H_INI
    u['P1'] = u['vwap_atr'] > 0
    u['P2'] = u['abre_atr'] > 0
    u['ok'] = np.isfinite(u[['ritmo_r', 'vwap_atr', 'abre_atr', 'incl_hull', 'sep_hull']].to_numpy(float)).all(axis=1)
    u.attrs['q_ritmo'] = q_ritmo
    return u


def spearman(a, b):
    a = pd.Series(np.asarray(a, float)); b = pd.Series(np.asarray(b, float))
    ok = a.notna() & b.notna()
    return float(a[ok].rank().corr(b[ok].rank()))


# ==================================================================== main
def main():
    d = E.indicadores(E.carrega())
    dias = sorted(d['dia'].unique())
    L = leituras(d)
    u = O.universo(d)
    u = atributos(u, d, L)
    q_ritmo = u.attrs['q_ritmo']
    u = u[u['ok']].reset_index(drop=True)

    p('=' * 74)
    p('FILTROS ORTOGONAIS A HULL: VELOCIDADE, HORARIO, POSICAO NO DIA')
    p('=' * 74)
    p(f"base: {len(d)} barras, {len(dias)} pregoes; sinais Hull + 2-4: {len(u)}; Hull + pavios: {int(u['cand'].sum())}")
    p(f"ritmo: janela {JANELA_MIN} min, mediana das {REF_BARRAS} barras anteriores; quartil de baixo < {q_ritmo:.2f}")

    # ------------------------------------------------ 0. ortogonalidade
    ort = {}
    for cj in O.CONJ:
        x = u if cj == 'h' else u[u['cand']]
        for col in list(CONTINUAS) + list(REGRAS):
            ort[f'{cj}|{col}'] = {r: spearman(x[col], x[r]) for r in REF_HULL}
    S_ort = dict(valores=ort, refs=REF_HULL)
    p('\n--- 0. ortogonalidade: correlacao de posto com a leitura de tendencia (Hull + pavios) ---')
    for col in list(CONTINUAS) + list(REGRAS):
        v = ort[f'cand|{col}']
        p(f"  {col:9s} " + '  '.join(f"{r} {v[r]:+.2f}" for r in REF_HULL)
          + ('   <- NAO e ortogonal' if max(abs(z) for z in v.values()) > 0.3 else ''))

    res = {}
    for gn, gg in HC.GESTOES.items():
        t = E.executa(d, u, 'fecha', gg)
        t, c1, c2 = P.marca_tercos(t, dias)
        res[gn] = t

    S = dict(parametros=dict(janela_min=JANELA_MIN, ref_barras=REF_BARRAS, h_ini=H_INI, h_fim=H_FIM,
                             q_ritmo=q_ritmo),
             regras=REGRAS, classicas=list(REGRAS), conj=O.CONJ, continuas=CONTINUAS,
             rot_gestao=HC.ROT_GESTAO, rot_bloco=PR.ROT_BLOCO, ortogonalidade=S_ort,
             base=dict(barras=len(d), dias=len(dias), ini=f"{d['data'].iat[0]:%d/%m/%Y}",
                       fim=f"{d['data'].iat[-1]:%d/%m/%Y}", c1=c1, c2=c2, n_h=int(len(u)),
                       n_cand=int(u['cand'].sum())))

    # ------------------------------------------------ 1. frequencia
    S['freq'] = {cj: {k: float((u if cj == 'h' else u[u['cand']])[k].mean() * 100) for k in REGRAS}
                 for cj in O.CONJ}
    p('\n--- 1. quanto de cada conjunto a regra deixa passar (%) ---')
    for cj in O.CONJ:
        p(f"  {cj:5s} " + '  '.join(f"{k} {v:4.0f}" for k, v in S['freq'][cj].items()))

    # ------------------------------------------------ 2. cada regra
    rng = np.random.default_rng(20260916)
    regras = {}
    for gn in HC.GESTOES:
        t = res[gn]
        for cj in O.CONJ:
            x = t[t['aceito'] & (t['cand'] if cj == 'cand' else True)].reset_index(drop=True)
            for k in REGRAS:
                r = O.mede_regra(x, x[k], rng)
                r['sorteio_pct'] = (P.sorteio(x.assign(aceito=True), x[k])['percentil']
                                    if 20 <= x[k].sum() < len(x) else None)
                regras[f'{cj}|{gn}|{k}'] = r
    S['regras_res'] = regras
    for cj in O.CONJ:
        p(f"\n--- 2. {O.CONJ[cj]}  (fechamento, 1:3 com parcial) ---")
        p(f"  base: EV {regras[f'{cj}|parcial|V1']['base']:+.1f}")
        for k, (fam, rot) in REGRAS.items():
            r = regras[f'{cj}|parcial|{k}']
            if r['ev'] is None:
                p(f"  {k} {rot:48s} n={r['n']}  -")
                continue
            p(f"  {k} {rot:48s} n={r['n']:5d} ({r['frac']:3.0f}%)  dentro {r['ev']:+6.1f}  fora {r['ev_fora']:+6.1f}  "
              f"ganho {r['ganho']:+5.1f}  p {r['p_bi']:.3f}  tercos " + '/'.join(f"{v:+.0f}" for v in r['tercos'])
              + f" (base " + '/'.join(f"{v:+.0f}" for v in r['tercos_base']) + ")"
              + f"  antes {r['blocos']['antes']:+.1f} (base {r['blocos_base']['antes']:+.1f})"
              + f"  C {r['compra']:+.1f} V {r['venda']:+.1f}  pct {r['sorteio_pct']:.0f}")
        p('  ganho nas 4 gestoes: ' + '  '.join(
            f"{k} " + '/'.join(f"{regras[f'{cj}|{g}|{k}'].get('ganho') or 0:+.1f}" for g in HC.GESTOES)
            for k in REGRAS))

    # ------------------------------------------------ 3. busca
    p('\n--- 3. a busca: 6 regras x 2 sentidos, contra resultados embaralhados ---')
    buscas = {}
    for gn in HC.GESTOES:
        t = res[gn]
        for cj in O.CONJ:
            x = t[t['aceito'] & (t['cand'] if cj == 'cand' else True)].reset_index(drop=True)
            bt, bk = O.busca(x, regras=list(REGRAS))
            rr = np.random.default_rng(8)
            nulo = np.array([O.busca(x, rr, regras=list(REGRAS))[0] for _ in range(1000)])
            nulo = nulo[nulo > -9e8]
            bl = PR.bloco(x['data']); pts = x['pts'].to_numpy(float)
            fora = {}
            for rot, dentro, teste in (('antes -> original+depois', bl == 'antes', bl != 'antes'),
                                       ('T1+T2 -> T3', x['terco'].to_numpy() != 'T3', x['terco'].to_numpy() == 'T3')):
                _, kk = O.busca(x, subset=dentro, regras=list(REGRAS))
                if kk is None:
                    fora[rot] = None
                    continue
                m = x[kk[0]].to_numpy(bool); m = m if kk[1] > 0 else ~m
                fora[rot] = dict(regra=kk[0], sentido=kk[1], ev_teste=float(pts[m & teste].mean()),
                                 n_teste=int((m & teste).sum()), ev_teste_base=float(pts[teste].mean()),
                                 n_teste_base=int(teste.sum()), ev_escolha=float(pts[m & dentro].mean()),
                                 ev_escolha_base=float(pts[dentro].mean()))
            buscas[f'{cj}|{gn}'] = dict(regra=bk[0] if bk else None, sentido=bk[1] if bk else None, t=float(bt),
                                        ruido_mediana=float(np.median(nulo)), ruido_p95=float(np.quantile(nulo, .95)),
                                        p_valor=float((nulo >= bt).mean()), fora=fora, poder=O.poder(x))
            b = buscas[f'{cj}|{gn}']
            p(f"  {cj:5s} {HC.ROT_GESTAO[gn]:16s} melhor {b['regra']}{'' if b['sentido'] == 1 else ' (complemento)'} "
              f"t={b['t']:+.2f}  ruido med {b['ruido_mediana']:+.2f} p95 {b['ruido_p95']:+.2f}  p={b['p_valor']:.3f}")
            for rot, f_ in fora.items():
                if f_:
                    p(f"        escolha {rot:26s}: {f_['regra']}{'' if f_['sentido'] > 0 else '~'} "
                      f"teste {f_['ev_teste']:+.1f} (n={f_['n_teste']}) x sem filtro {f_['ev_teste_base']:+.1f}")
    S['busca'] = buscas

    # ------------------------------------------------ 4. quintis
    qt = {}
    for cj in O.CONJ:
        x = res['parcial']; x = x[x['aceito'] & (x['cand'] if cj == 'cand' else True)].reset_index(drop=True)
        for col in CONTINUAS:
            qt[f'{cj}|{col}'] = O.quintis(x, col)
        # horario em faixas fixas, que e como se opera
        pts = x['pts'].to_numpy(float); ter = x['terco'].to_numpy(); hh = x['hora'].to_numpy(float)
        faixas = []
        for a, b, rot in ((9, 10, '9h-10h'), (10, 11, '10h-11h'), (11, 12, '11h-12h'), (12, 13, '12h-13h'),
                          (13, 14, '13h-14h'), (14, 15, '14h-15h'), (15, 16, '15h-16h'), (16, 19, '16h em diante')):
            m = (hh >= a) & (hh < b)
            faixas.append(dict(faixa=rot, n=int(m.sum()), ev=float(pts[m].mean()) if m.any() else None,
                               tercos=[float(pts[m & (ter == z)].mean()) if (m & (ter == z)).any() else None
                                       for z in ('T1', 'T2', 'T3')]))
        qt[f'{cj}|hora_fixa'] = dict(limites=[], faixas=faixas)
    S['quintis'] = qt
    p('\n--- 4. leituras em quintis (Hull + pavios, 1:3 com parcial) ---')
    for col, rot in CONTINUAS.items():
        q = qt[f'cand|{col}']
        p(f"  {rot:44s} lim " + ' '.join(f"{v:.2f}" for v in q['limites']) + ' | '
          + '  '.join(f"{f['ev']:+5.1f}" for f in q['faixas']))
    p('  hora (faixas fixas): ' + '  '.join(f"{f['faixa']} {f['ev']:+.1f}({f['n']})" for f in qt['cand|hora_fixa']['faixas']))

    # ------------------------------------------------ 4b. horario x ritmo
    #  a primeira hora e a mais rapida do dia: o efeito do horario e o do ritmo
    #  podem ser o mesmo. Cruzamento 2x2, com o corte de ritmo no quintil de cima.
    cruz = {}
    p(chr(10) + '--- 4b. horario x ritmo (1:3 com parcial) ---')
    for cj in O.CONJ:
        x = res['parcial']; x = x[x['aceito'] & (x['cand'] if cj == 'cand' else True)]
        q80 = float(np.nanpercentile(x['ritmo_r'], 80))
        cel = []
        for cedo in (True, False):
            for rapido in (True, False):
                m = ((x['hora'] < H_INI) == cedo) & ((x['ritmo_r'] > q80) == rapido)
                cel.append(dict(cedo=cedo, rapido=rapido, n=int(m.sum()),
                                ev=float(x.loc[m, 'pts'].mean()) if m.any() else None))
        cruz[cj] = dict(q80=q80, celulas=cel,
                        frac_rapido_cedo=float(((x['ritmo_r'] > q80) & (x['hora'] < H_INI)).sum()
                                               / max(1, (x['ritmo_r'] > q80).sum()) * 100))
        p(f"  {cj:5s} ritmo > {q80:.2f}: " + '  '.join(
            f"{'antes 10h' if c['cedo'] else 'depois 10h'} {'rapido' if c['rapido'] else 'normal'} "
            f"{c['ev']:+.1f} ({c['n']})" for c in cel)
          + f"   | {cruz[cj]['frac_rapido_cedo']:.0f}% dos sinais rapidos sao antes das 10h")
    S['horario_ritmo'] = cruz

    # ------------------------------------------------ 5. vizinhanca
    p('\n--- 5. vizinhanca (ganho no Hull + pavios, 1:3 com parcial) ---')
    viz = {}
    tp = res['parcial']
    cols = ['i', 'lado', 'pts', 'aceito', 'cand', 'n_fav', 'data', 'terco', 'hora']
    for jan in (30, 60, 120):
        L2 = leituras(d, jan)
        x2 = atributos(tp[cols], d, L2)
        x2 = x2[x2['aceito'] & x2['cand'] & x2['ok']]
        pts = x2['pts'].to_numpy(float)
        for k in ('V1', 'V2'):
            m = x2[k].to_numpy(bool)
            viz[f'{k}|janela {jan} min'] = dict(regra=k, par=f'janela {jan} min', n=int(m.sum()),
                                                ganho=float(pts[m].mean() - pts.mean()), padrao=jan == JANELA_MIN)
    xc = tp[tp['aceito'] & tp['cand']]
    ptc = xc['pts'].to_numpy(float)
    for fim in (14.0, 15.0, 16.0):
        m = ((xc['hora'] >= H_INI) & (xc['hora'] < fim)).to_numpy()
        viz[f'H1|10h a {fim:.0f}h'] = dict(regra='H1', par=f'10h a {fim:.0f}h', n=int(m.sum()),
                                          ganho=float(ptc[m].mean() - ptc.mean()), padrao=fim == H_FIM)
    for ini in (9.5, 10.0, 10.5):
        m = (xc['hora'] >= ini).to_numpy()
        viz[f'H2|a partir de {ini}'] = dict(regra='H2', par=f"a partir de {int(ini)}h{'30' if ini % 1 else ''}",
                                           n=int(m.sum()), ganho=float(ptc[m].mean() - ptc.mean()), padrao=ini == H_INI)
    p('  ' + '  '.join(f"{v['regra']}@{v['par']} {v['ganho']:+.1f}" for v in viz.values()))
    S['vizinhanca'] = viz

    # ------------------------------------------------ 6. carteiras
    p('\n--- 6. carteira, uma posicao por vez ---')
    cart = {}; trades = {}
    for gn in HC.GESTOES:
        t = res[gn]
        for cj in O.CONJ:
            x = t[t['aceito'] & (t['cand'] if cj == 'cand' else True)]
            for k in ['base'] + list(REGRAS):
                sel = x if k == 'base' else x[x[k]]
                c = E.carteira(sel)
                st = O.stats_cart(c, d)
                if gn != 'parcial':
                    for campo in ('pts', 'mfe', 'mae', 'dur_s', 'barras'):
                        st.pop(campo, None)
                st['blocos'] = PR.por_bloco(c)
                cart[f'{cj}|{gn}|{k}'] = st
                if gn == 'parcial':
                    trades[f'{cj}|{gn}|{k}'] = O.compacta(c, d)
            b = cart[f'{cj}|{gn}|base']
            p(f"  {cj:5s} {HC.ROT_GESTAO[gn]:16s} base {b['trades']:5d} tr {b['exp_pts']:+5.1f}/tr FL {b['fator_lucro']:.2f} DD {b['dd_max']:5.0f} | "
              + '  '.join(f"{k} {cart[f'{cj}|{gn}|{k}']['trades']}tr {cart[f'{cj}|{gn}|{k}']['exp_pts']:+.1f}" for k in REGRAS))
    S['carteira'] = cart; S['trades'] = trades

    rd = lambda arr, c=1: [None if not np.isfinite(v) else round(float(v), c) for v in arr]
    S['candles'] = dict(o=d['o'].tolist(), h=d['h'].tolist(), l=d['l'].tolist(), c=d['c'].tolist(),
                        hma=rd(d['hma']), vwap=rd(L['vwap']), abertura=d.groupby('dia')['o'].transform('first').tolist(),
                        ritmo=rd(L['ritmo_r'], 2), dt=d['data'].dt.strftime('%d/%m %H:%M').tolist())

    with open(os.path.join(SAIDA, 'ortogonais.json'), 'w', encoding='utf-8') as f:
        json.dump(P._lim(S), f, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(SAIDA, 'ortogonais_console.txt'), 'w', encoding='utf-8') as f:
        f.write(_buf.getvalue())
    p('\ngravado: saida/ortogonais.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
