# -*- coding: utf-8 -*-
"""
Volume agressor (compra + venda) como filtro do Hull + pavios, com lags,
janelas, variacao percentual e variacao contra a media das ultimas barras.

    python volume_agressor.py            -> saida/volume_agressor.json + console
    python relatorio_volume.py           -> volume_agressor.html + VOLUME_AGRESSOR.md

V = agr_compra + agr_venda de cada candle de 20 PI. Tudo e lido no
fechamento do candle de sinal (barra i), com barras ja fechadas.

A FAMILIA, fechada antes de medir (11 leituras):

  vrel_k  (k = 1, 2, 3, 5)   nivel: media de V nas ultimas k barras
          (incluindo a de sinal) dividida pela media de V nas 20 barras
          ANTERIORES a essa janela. > 1 = janela com mais volume que o normal.
  vpct_k  (k = 1, 2, 3, 5)   variacao percentual com lag: V[i] / V[i-k] - 1.
  vmed_k  (k = 2, 3, 5)      variacao contra a media: V[i] dividido pela media
          de V nas k barras anteriores (i-k a i-1), menos 1. > 0 = o candle
          de sinal teve mais volume que as barras que o antecederam -- com
          k = 2 ou 3 sao, quase sempre, os proprios candles da retracao.

Cortes, pela distribuicao da propria leitura no conjunto Hull + 2 a 4 (sem
olhar resultado): quintil de baixo (q20), mediana (q50) e quintil de cima
(q80), nos dois sentidos -> 11 x 3 x 2 = 66 filtros candidatos.

Isso e uma BUSCA grande, e o controle esta a altura dela:
  . BUSCA: o melhor dos 66 contra o melhor que a mesma busca acha com os
    resultados embaralhados (1.000 vezes);
  . ESCOLHA FORA: o melhor escolhido so antes de 06/08, medido no resto; e o
    escolhido em T1+T2, medido em T3;
  . PODER, tercos, lados, blocos, sorteio para as 11 regras "acima da mediana";
  . ORTOGONALIDADE: correlacao de posto de cada leitura com a Hull
    (inclinacao, Hull - EMA, MACD) e com o que ja foi medido e e parente do
    volume -- hora do sinal, duracao do candle de sinal, ritmo;
  . HORARIO: o volume tem sazonalidade forte dentro do dia (a primeira hora
    concentra volume), e o horario ja mediu algo (ortogonais.py). O melhor
    filtro e as 11 regras sao medidos de novo SO nos sinais das 10h as 15h;
  . VIZINHANCA: a media de referencia com 50 barras em vez de 20.
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
import ortogonais as T

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')

JAN_REF = 20
KS_NIVEL = (1, 2, 3, 5)
KS_PCT = (1, 2, 3, 5)
KS_MED = (2, 3, 5)
CORTES = (20, 50, 80)

FEATS = {}
for k in KS_NIVEL:
    FEATS[f'vrel_{k}'] = f'Volume medio das ultimas {k} barra{"s" if k > 1 else ""} / media das {JAN_REF} anteriores'
for k in KS_PCT:
    FEATS[f'vpct_{k}'] = f'Variacao % do volume contra {k} barra{"s" if k > 1 else ""} atras'
for k in KS_MED:
    FEATS[f'vmed_{k}'] = f'Volume do sinal contra a media das {k} barras anteriores'

_buf = io.StringIO()


def p(*a, **k):
    print(*a, **k)
    print(*a, **k, file=_buf)


# ============================================================== leituras
def leituras(d, jan_ref=JAN_REF):
    V = (d['agr_c'] + d['agr_v']).astype(float)
    out = dict(V=V.to_numpy())
    for k in KS_NIVEL:
        janela = V.rolling(k).mean()
        ref = V.rolling(jan_ref).mean().shift(k)
        out[f'vrel_{k}'] = (janela / ref.replace(0, np.nan)).to_numpy()
    for k in KS_PCT:
        out[f'vpct_{k}'] = (V / V.shift(k).replace(0, np.nan) - 1).to_numpy()
    for k in KS_MED:
        out[f'vmed_{k}'] = (V / V.rolling(k).mean().shift(1).replace(0, np.nan) - 1).to_numpy()
    out['ref20'] = V.rolling(jan_ref).mean().to_numpy()
    return out


def anexa(u, d, Lv, limites=None, feats=None, espelha=False):
    """Leituras na barra do sinal. Com espelha=True a leitura e multiplicada
    pelo lado do trade (saldo agressor: positivo = a favor da operacao)."""
    feats = feats or FEATS
    i = u['i'].to_numpy(int)
    ld = u['lado'].to_numpy(int) if espelha else 1
    u = u.copy()
    for f in feats:
        u[f] = Lv[f][i] * ld
    if limites is None:
        limites = {f: {q: float(np.nanpercentile(u[f], q)) for q in CORTES} for f in feats}
    for f in feats:
        for q in CORTES:
            u[f'C_{f}_q{q}'] = u[f] > limites[f][q]
        u[f'R_{f}'] = u[f'C_{f}_q50']
    u['ok_vol'] = np.isfinite(u[list(feats)].to_numpy(float)).all(axis=1)
    u.attrs['limites'] = limites
    return u


def cand_nome(c, sent):
    _, f, q = c.split('_', 1)[0], c[2:c.rfind('_q')], c[c.rfind('_q') + 2:]
    lado = {'20': ('acima do quintil de baixo', 'no quintil de baixo'),
            '50': ('acima da mediana', 'abaixo da mediana'),
            '80': ('no quintil de cima', 'abaixo do quintil de cima')}[q]
    return f"{f} {lado[0] if sent > 0 else lado[1]}"


def cfg_volume():
    rd0 = lambda arr: [None if not np.isfinite(v) else round(float(v)) for v in arr]
    return dict(nome='volume_agressor', titulo='VOLUME AGRESSOR (COMPRA + VENDA) COMO FILTRO DO HULL + PAVIOS',
                familia='Volume agressor', feats=FEATS, leituras=leituras, espelha=False,
                parametros=dict(jan_ref=JAN_REF, ks_nivel=KS_NIVEL, ks_pct=KS_PCT, ks_med=KS_MED, cortes=CORTES),
                viz_prefixo=('vrel',),
                candles=lambda d, L: dict(vol=rd0(L['V']), ref20=rd0(L['ref20'])))


# ==================================================================== main
def main(cfg=None):
    cfg = cfg or cfg_volume()
    FEATS = cfg['feats']; esp = cfg['espelha']
    _buf.seek(0); _buf.truncate()
    d = E.indicadores(E.carrega())
    dias = sorted(d['dia'].unique())
    Lv = cfg['leituras'](d)
    Lt = T.leituras(d)
    u = O.universo(d)
    u = T.atributos(u, d, Lt)                       # inclinacao, Hull-EMA, MACD, ritmo, hora
    u['dur_sinal'] = d['dur_s'].to_numpy()[u['i'].to_numpy(int)] if 'dur_s' in d else \
        d['dur_barra_s'].to_numpy()[u['i'].to_numpy(int)]
    u = anexa(u, d, Lv, feats=FEATS, espelha=esp)
    limites = u.attrs['limites']
    u = u[u['ok_vol'] & u['ok']].reset_index(drop=True)
    CAND = [f'C_{f}_q{q}' for f in FEATS for q in CORTES]
    REGRAS = {f'R_{f}': (cfg['familia'], FEATS[f] + ' acima da mediana') for f in FEATS}

    p('=' * 74)
    p(cfg['titulo'])
    p('=' * 74)
    p(f"base: {len(d)} barras, {len(dias)} pregoes; sinais Hull + 2-4: {len(u)}; Hull + pavios: {int(u['cand'].sum())}")
    p(f"{len(FEATS)} leituras x {len(CORTES)} cortes x 2 sentidos = {2 * len(CAND)} filtros candidatos")

    # ------------------------------------------------ 0. ortogonalidade
    refs = dict(T.REF_HULL, hora='Hora do sinal', dur_sinal='Duracao do candle de sinal',
                ritmo_r='Ritmo da ultima hora')
    ort = {}
    for cj in O.CONJ:
        x = u if cj == 'h' else u[u['cand']]
        for f in FEATS:
            ort[f'{cj}|{f}'] = {r: T.spearman(x[f], x[r]) for r in refs}
    p('\n--- 0. correlacao de posto (Hull + pavios) ---')
    p('  ' + ' ' * 8 + ''.join(f"{r[:9]:>10s}" for r in refs))
    for f in FEATS:
        v = ort[f'cand|{f}']
        p(f"  {f:8s}" + ''.join(f"{v[r]:+10.2f}" for r in refs))

    res = {}
    for gn, gg in HC.GESTOES.items():
        t = E.executa(d, u, 'fecha', gg)
        t, c1, c2 = P.marca_tercos(t, dias)
        res[gn] = t

    S = dict(parametros=cfg['parametros'],
             feats=FEATS, regras=REGRAS, classicas=list(REGRAS), conj=O.CONJ, continuas=FEATS,
             limites=limites, rot_gestao=HC.ROT_GESTAO, rot_bloco=PR.ROT_BLOCO,
             ortogonalidade=dict(valores=ort, refs=refs),
             base=dict(barras=len(d), dias=len(dias), ini=f"{d['data'].iat[0]:%d/%m/%Y}",
                       fim=f"{d['data'].iat[-1]:%d/%m/%Y}", c1=c1, c2=c2, n_h=int(len(u)),
                       n_cand=int(u['cand'].sum())))
    S['freq'] = {cj: {k: float((u if cj == 'h' else u[u['cand']])[k].mean() * 100) for k in REGRAS} for cj in O.CONJ}

    # ------------------------------------------------ 1. grade: cada leitura, cada corte
    rng = np.random.default_rng(20260917)
    grade = {}
    for gn in HC.GESTOES:
        t = res[gn]
        for cj in O.CONJ:
            x = t[t['aceito'] & (t['cand'] if cj == 'cand' else True)].reset_index(drop=True)
            pts = x['pts'].to_numpy(float); base = pts.mean()
            for c in CAND:
                m = x[c].to_numpy(bool)
                for sent, mm in ((1, m), (-1, ~m)):
                    if mm.sum() < 30:
                        continue
                    s = pts[mm].std(ddof=1)
                    grade[f'{cj}|{gn}|{c}|{sent}'] = dict(
                        n=int(mm.sum()), ev=float(pts[mm].mean()), ganho=float(pts[mm].mean() - base),
                        t=float((pts[mm].mean() - base) / (s / np.sqrt(mm.sum()))),
                        tercos=[float(pts[mm & (x['terco'].to_numpy() == z)].mean()) for z in ('T1', 'T2', 'T3')])
    S['grade'] = grade
    p('\n--- 1. grade (Hull + pavios, 1:3 com parcial): ganho em pts por filtro ---')
    p(f"  {'leitura':9s}" + ''.join(f"{('>' if s > 0 else '<=') + 'q' + str(q):>9s}" for q in CORTES for s in (1, -1)))
    for f in FEATS:
        p(f"  {f:9s}" + ''.join(
            f"{grade.get(f'cand|parcial|C_{f}_q{q}|{s}', {}).get('ganho', float('nan')):+9.1f}"
            for q in CORTES for s in (1, -1)))

    # ------------------------------------------------ 2. as 11 regras "acima da mediana"
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
    p('\n--- 2. acima da mediana (Hull + pavios, 1:3 com parcial) ---')
    for k in REGRAS:
        r = regras[f'cand|parcial|{k}']
        p(f"  {k:10s} n={r['n']:5d}  dentro {r['ev']:+6.1f}  fora {r['ev_fora']:+6.1f}  ganho {r['ganho']:+5.1f}  "
          f"p {r['p_bi']:.3f}  tercos " + '/'.join(f"{v:+.0f}" for v in r['tercos'])
          + f"  antes {r['blocos']['antes']:+.1f} (base {r['blocos_base']['antes']:+.1f})  pct {r['sorteio_pct']:.0f}")

    # ------------------------------------------------ 3. busca contra ruido
    p(f"\n--- 3. a busca: {2 * len(CAND)} filtros contra resultados embaralhados (1.000x) ---")
    buscas = {}
    for gn in HC.GESTOES:
        t = res[gn]
        for cj in O.CONJ:
            x = t[t['aceito'] & (t['cand'] if cj == 'cand' else True)].reset_index(drop=True)
            bt, bk = O.busca(x, regras=CAND)
            rr = np.random.default_rng(9)
            nulo = np.array([O.busca(x, rr, regras=CAND)[0] for _ in range(1000)])
            nulo = nulo[nulo > -9e8]
            bl = PR.bloco(x['data']); pts = x['pts'].to_numpy(float)
            fora = {}
            for rot, dentro, teste in (('antes -> original+depois', bl == 'antes', bl != 'antes'),
                                       ('T1+T2 -> T3', x['terco'].to_numpy() != 'T3', x['terco'].to_numpy() == 'T3')):
                _, kk = O.busca(x, subset=dentro, regras=CAND)
                if kk is None:
                    fora[rot] = None
                    continue
                m = x[kk[0]].to_numpy(bool); m = m if kk[1] > 0 else ~m
                fora[rot] = dict(regra=cand_nome(kk[0], kk[1]), col=kk[0], sentido=kk[1],
                                 ev_teste=float(pts[m & teste].mean()), n_teste=int((m & teste).sum()),
                                 ev_teste_base=float(pts[teste].mean()), n_teste_base=int(teste.sum()),
                                 ev_escolha=float(pts[m & dentro].mean()), ev_escolha_base=float(pts[dentro].mean()))
            m = x[bk[0]].to_numpy(bool); m = m if bk[1] > 0 else ~m
            hr = x['hora'].to_numpy(float); jan = (hr >= 10) & (hr < 15)
            buscas[f'{cj}|{gn}'] = dict(
                regra=cand_nome(bk[0], bk[1]), col=bk[0], sentido=bk[1], t=float(bt),
                ganho=float(pts[m].mean() - pts.mean()), n=int(m.sum()),
                ruido_mediana=float(np.median(nulo)), ruido_p95=float(np.quantile(nulo, .95)),
                p_valor=float((nulo >= bt).mean()), fora=fora, poder=O.poder(x),
                so_10_15=dict(ganho=float(pts[m & jan].mean() - pts[jan].mean()), n=int((m & jan).sum()),
                              ev=float(pts[m & jan].mean()), base=float(pts[jan].mean())))
            b = buscas[f'{cj}|{gn}']
            p(f"  {cj:5s} {HC.ROT_GESTAO[gn]:16s} melhor: {b['regra']} (n={b['n']}, ganho {b['ganho']:+.1f}) t={b['t']:+.2f}  "
              f"ruido med {b['ruido_mediana']:+.2f} p95 {b['ruido_p95']:+.2f}  p={b['p_valor']:.3f}  | "
              f"so 10h-15h: ganho {b['so_10_15']['ganho']:+.1f}")
            for rot, f_ in fora.items():
                if f_:
                    p(f"        escolha {rot:26s}: {f_['regra']:40s} teste {f_['ev_teste']:+.1f} (n={f_['n_teste']}) "
                      f"x sem filtro {f_['ev_teste_base']:+.1f}")
    S['busca'] = buscas

    # ------------------------------------------------ 4. quintis e horario
    qt = {}; so1015 = {}
    for cj in O.CONJ:
        x = res['parcial']; x = x[x['aceito'] & (x['cand'] if cj == 'cand' else True)].reset_index(drop=True)
        for f in FEATS:
            qt[f'{cj}|{f}'] = O.quintis(x, f)
        hr = x['hora'].to_numpy(float); jan = (hr >= 10) & (hr < 15); pts = x['pts'].to_numpy(float)
        for k in REGRAS:
            m = x[k].to_numpy(bool)
            so1015[f'{cj}|{k}'] = dict(ganho_todos=float(pts[m].mean() - pts.mean()),
                                       ganho_10_15=float(pts[m & jan].mean() - pts[jan].mean()),
                                       frac_cedo_dentro=float((hr[m] < 10).mean() * 100),
                                       frac_cedo_fora=float((hr[~m] < 10).mean() * 100))
    S['quintis'] = qt; S['horario'] = so1015
    p('\n--- 4. quintis (Hull + pavios, 1:3 com parcial) ---')
    for f in FEATS:
        q = qt[f'cand|{f}']
        p(f"  {f:8s} lim " + ' '.join(f"{v:+.2f}" for v in q['limites']) + ' | '
          + '  '.join(f"{z['ev']:+5.1f}" for z in q['faixas']))
    p('\n--- 4b. acima da mediana: todos os sinais x so 10h-15h (Hull + pavios) ---')
    for k in REGRAS:
        h = so1015[f'cand|{k}']
        p(f"  {k:10s} ganho {h['ganho_todos']:+5.1f}  so 10h-15h {h['ganho_10_15']:+5.1f}   "
          f"sinais antes das 10h: {h['frac_cedo_dentro']:.0f}% dentro x {h['frac_cedo_fora']:.0f}% fora")

    # ------------------------------------------------ 5. vizinhanca (media de 50)
    p('\n--- 5. vizinhanca: media de referencia de 50 barras (Hull + pavios, 1:3 com parcial) ---')
    viz = {}
    Lv50 = cfg['leituras'](d, 50)
    tp = res['parcial']
    xc = anexa(tp[['i', 'lado', 'pts', 'aceito', 'cand', 'data', 'terco', 'hora']], d, Lv50, feats=FEATS, espelha=esp)
    xc = xc[xc['aceito'] & xc['cand'] & xc['ok_vol']]
    for f in FEATS:
        if not f.startswith(cfg['viz_prefixo']):
            continue
        for jan, xx in ((20, tp[tp['aceito'] & tp['cand']]), (50, xc)):
            m = xx[f'R_{f}'].to_numpy(bool); pts = xx['pts'].to_numpy(float)
            viz[f'R_{f}|media {jan}'] = dict(regra=f'R_{f}', par=f'media de {jan} barras', n=int(m.sum()),
                                             ganho=float(pts[m].mean() - pts.mean()), padrao=jan == cfg['parametros']['jan_ref'])
    p('  ' + '  '.join(f"{v['regra']}@{v['par']} {v['ganho']:+.1f}" for v in viz.values()))
    S['vizinhanca'] = viz

    # ------------------------------------------------ 6. carteiras
    p('\n--- 6. carteira (1:3 com parcial) ---')
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
    for cj in O.CONJ:
        b = cart[f'{cj}|parcial|base']
        p(f"  {cj:5s} base {b['trades']}tr {b['exp_pts']:+.1f}/tr | " + '  '.join(
            f"{k[2:]} {cart[f'{cj}|parcial|{k}']['exp_pts']:+.1f}" for k in REGRAS))
    S['carteira'] = cart; S['trades'] = trades

    rd = lambda arr, c=0: [None if not np.isfinite(v) else round(float(v), c) for v in arr]
    S['candles'] = dict(o=d['o'].tolist(), h=d['h'].tolist(), l=d['l'].tolist(), c=d['c'].tolist(),
                        hma=rd(d['hma'], 1), **cfg['candles'](d, Lv),
                        dt=d['data'].dt.strftime('%d/%m %H:%M').tolist())

    with open(os.path.join(SAIDA, cfg['nome'] + '.json'), 'w', encoding='utf-8') as f:
        json.dump(P._lim(S), f, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(SAIDA, cfg['nome'] + '_console.txt'), 'w', encoding='utf-8') as f:
        f.write(_buf.getvalue())
    p('\ngravado: saida/' + cfg['nome'] + '.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
