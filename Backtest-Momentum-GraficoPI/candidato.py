# -*- coding: utf-8 -*-
"""
O candidato que a base de 6 meses sugere: RETRACAO PROFUNDA (3+ candles).

    python rodar.py && python candidato.py && python relatorio.py && python plano.py

Na base antiga (26 pregoes) o nivel Ouro media +34 pts por trade. Na base
nova ele cai para perto de zero FORA da janela em que foi escolhido. O
unico atributo da regra-base que mede bem nos tres tercos E nos blocos
antes/original e o tamanho da retracao -- que o CLAUDE.md pede para
avaliar. Este modulo mede o recorte "Bronze + retracao de 3 ou mais
candles" como hipotese, com o controle de busca que ele precisa:

  . o corte foi escolhido OLHANDO esta base (3 em vez do 2 do Prata), entao
    a mesma busca -- n_ret >= 2/3/4 e ret_atr > 1,0/1,5/2,0 -- e repetida
    em dados embaralhados, e o t do achado real e comparado com o t que a
    busca acha em ruido;
  . e, porque todas as tabelas de filtro do rodar.py foram vistas antes,
    a busca AMPLA -- 12 atributos, 74 cortes -- tambem em dados
    embaralhados. Resultado medido: a retracao e o melhor corte do espaco,
    mas a busca em ruido acha algo tao bom em ~17% das vezes. Hipotese;
  . os blocos antes / original / depois e os tercos;
  . custo e Monte Carlo.

Acrescenta ao saida/resumo.json a chave 'candidato' e as variantes
'fecha|<gestao>|r3' (que o grafico trade a trade navega).
"""
import json
import os

import numpy as np
import pandas as pd

import engine as E
import estrategia as S
import periodos as PR
import rodar as R

SAIDA = R.SAIDA
GESTOES = dict(R.GESTOES)
GESTOES['r1'] = dict(parcial=False, alvo=100.0)
ROT_GESTAO = dict(R.ROT_GESTAO, r1='1:1 sem parcial')

CORTES = [('n_ret', 2, 'retracao de 2+ candles'), ('n_ret', 3, 'retracao de 3+ candles'),
          ('n_ret', 4, 'retracao de 4+ candles'), ('ret_atr', 1.0, 'retracao maior que 1,0 ATR'),
          ('ret_atr', 1.5, 'retracao maior que 1,5 ATR'), ('ret_atr', 2.0, 'retracao maior que 2,0 ATR')]


def _t(p):
    p = np.asarray(p, float)
    if len(p) < 20 or p.std(ddof=1) == 0:
        return -9e9
    return p.mean() / (p.std(ddof=1) / np.sqrt(len(p)))


def busca_retracao(t, n_perm=2000, semente=20260914):
    """Melhor corte de tamanho de retracao e o mesmo em ruido."""
    p = t['pts'].to_numpy(float)
    X = t[['n_ret', 'ret_atr']].to_numpy(float)

    def melhor(Xm):
        res = []
        for col, thr, rot in CORTES:
            x = Xm[:, 0] if col == 'n_ret' else Xm[:, 1]
            m = (x >= thr) if col == 'n_ret' else (x > thr)
            res.append((_t(p[m]), rot, int(m.sum()), float(p[m].mean()) if m.any() else None))
        return max(res, key=lambda r: r[0]), res

    (bt, brot, bn, bev), todos = melhor(X)
    rng = np.random.default_rng(semente)
    nulo = np.array([melhor(X[rng.permutation(len(X))])[0][0] for _ in range(n_perm)])
    return dict(melhor=dict(rotulo=brot, t=float(bt), n=bn, ev=bev),
                cortes=[dict(rotulo=r, t=float(tt), n=n_, ev=ev) for tt, r, n_, ev in todos],
                ruido_mediana=float(np.median(nulo)), ruido_p95=float(np.quantile(nulo, .95)),
                p_valor=float((nulo >= bt).mean()), perms=n_perm)


#  Todas as tabelas de filtro do rodar.py [4] foram VISTAS antes de este
#  candidato ser formulado. O controle honesto e, portanto, a busca em
#  todas elas: cada fronteira de faixa vira um corte, nos dois sentidos.
ESPACO_AMPLO = {
    'curva': [0], 'estic': [0.15, 0.45, 0.8], 'pav_tot': [25, 45, 65, 90],
    'pav_fav_r': [0.03, 0.06, 0.10], 'pav_con_r': [0.15, 0.30, 0.45],
    'n_ret': [1.5, 2.5, 3.5], 'ret_atr': [1.0, 1.5, 2.0],
    'incl_hma': [0.05, 0.10, 0.16], 'incl_ema': [0.0, 0.13, 0.30],
    'folga_banda': [1.8, 2.3, 2.9], 'barras_colada': [0.5, 3.5, 8.5],
    'hora': [10, 11, 12, 13, 15],
}
N_MIN_AMPLO = 200


def busca_ampla(t, n_perm=1000, semente=914):
    p = t['pts'].to_numpy(float)
    cols = list(ESPACO_AMPLO)
    X = t[cols].to_numpy(float)

    def melhor(Xm):
        bt, bd = -9e9, None
        for j, c in enumerate(cols):
            x = Xm[:, j]
            for thr in ESPACO_AMPLO[c]:
                for sent in (1, -1):
                    m = (x > thr) if sent > 0 else (x <= thr)
                    if m.sum() < N_MIN_AMPLO:
                        continue
                    tt = _t(p[m])
                    if tt > bt:
                        bt, bd = tt, (c, thr, '>' if sent > 0 else '<=', int(m.sum()),
                                      float(p[m].mean()))
        return bt, bd

    bt, bd = melhor(X)
    rng = np.random.default_rng(semente)
    # embaralha as LINHAS dos atributos juntas: preserva a correlacao entre
    # eles e destroi a ligacao com o resultado
    nulo = np.array([melhor(X[rng.permutation(len(X))])[0] for _ in range(n_perm)])
    n_cortes = sum(len(v) for v in ESPACO_AMPLO.values()) * 2
    return dict(melhor=dict(col=bd[0], thr=bd[1], sentido=bd[2], n=bd[3], ev=bd[4], t=float(bt)),
                ruido_mediana=float(np.median(nulo)), ruido_p90=float(np.quantile(nulo, .90)),
                ruido_p95=float(np.quantile(nulo, .95)), p_valor=float((nulo >= bt).mean()),
                perms=n_perm, atributos=len(cols), cortes=n_cortes, n_min=N_MIN_AMPLO)


def roda(d, p=print):
    dias = np.sort(d['dia'].unique())
    sc = E.sinais(d, antecipado=False)
    t_ini, t_fim = d['data'].iloc[0], d['data'].iloc[-1]
    out = dict(gestoes={}, rot_gestao=ROT_GESTAO, n_ret_min=S.N_RET_R3)
    variantes = {}
    p('\n' + '=' * 72)
    p(f'CANDIDATO: Bronze + retracao de {S.N_RET_R3}+ candles (entrada no fechamento)')
    p('=' * 72)
    for gn, g in GESTOES.items():
        t = S.anota(E.executa(d, sc, 'fecha', g))
        t, _, _ = R.marca_tercos(t, dias)
        ac = t[t['aceito']]
        sel = S.seleciona(ac, 'r3')
        ca = E.carteira(sel)
        st = E.estatisticas(ca)
        st['eq_t'] = (((ca['data'] - t_ini) / (t_fim - t_ini)).astype(float).round(5).tolist())
        st['eq_d'] = ca['data'].dt.strftime('%d/%m').tolist()
        custos = []
        for cp in (0, 2, 5, 10):
            c2 = E.estatisticas(ca.assign(pts=ca['pts'] - cp))
            custos.append(dict(custo=cp, ev=c2['exp_pts'], total=c2['lucro_liq'],
                               fl=c2['fator_lucro'], dd=c2['dd_max']))
        bronze = E.carteira(ac)
        r = dict(
            stats={k: v for k, v in st.items() if k not in ('equity', 'eq_t', 'eq_d')},
            sinais=dict(n=int(len(sel)), ev=float(sel['pts'].mean()),
                        wr=float((sel['pts'] > 0).mean() * 100)),
            bronze_sinais=dict(n=int(len(ac)), ev=float(ac['pts'].mean())),
            bronze_cart=dict(trades=int(len(bronze)), pts=float(bronze['pts'].sum()),
                             ev=float(bronze['pts'].mean())),
            tercos=[dict(terco=k, n=int((sel['terco'] == k).sum()),
                         ev=float(sel.loc[sel['terco'] == k, 'pts'].mean()))
                    for k in ('T1', 'T2', 'T3')],
            blocos=PR.por_bloco(sel), blocos_cart=PR.por_bloco(ca),
            meses=PR.por_mes(sel), custos=custos, mc=R.monte_carlo(ca['pts'].to_numpy()),
            lados=dict(compra=PR._res(sel.loc[sel['lado'] > 0, 'pts']),
                       venda=PR._res(sel.loc[sel['lado'] < 0, 'pts'])),
            n_ret=[dict(faixa=('1 candle' if k == 1 else f'{k} candles') if k < 5 else '5 ou mais',
                        **PR._res(ac.loc[(ac['n_ret'] == k) if k < 5 else (ac['n_ret'] >= 5), 'pts']))
                   for k in (1, 2, 3, 4, 5)],
            horas=[dict(faixa=f'{h}h', **PR._res(sel.loc[sel['hora'].astype(int) == h, 'pts']))
                   for h in range(9, 19)],
        )
        if gn == 'parcial':
            r['busca'] = busca_retracao(ac)
            b = r['busca']
            p(f"  busca de corte de retracao (Bronze): melhor {b['melhor']['rotulo']} "
              f"t={b['melhor']['t']:+.2f}  ruido mediana t={b['ruido_mediana']:+.2f} "
              f"p95 t={b['ruido_p95']:+.2f}  p={b['p_valor']:.3f}")
            r['busca_ampla'] = busca_ampla(ac)
            b = r['busca_ampla']; m = b['melhor']
            p(f"  busca AMPLA ({b['atributos']} atributos, {b['cortes']} cortes): melhor "
              f"{m['col']} {m['sentido']} {m['thr']} t={m['t']:+.2f} (n={m['n']}, EV {m['ev']:+.1f})  "
              f"ruido mediana t={b['ruido_mediana']:+.2f} p95 t={b['ruido_p95']:+.2f}  "
              f"p={b['p_valor']:.3f}")
        out['gestoes'][gn] = r
        bl = r['blocos']
        p(f"  {ROT_GESTAO[gn]:16s} sinais {r['sinais']['n']:4d} EV {r['sinais']['ev']:+6.1f} | "
          f"carteira {st['trades']:4d} trades {st['lucro_liq']:+7.0f} pts FL {st['fator_lucro']:.2f} "
          f"DD {st['dd_max']:.0f} | antes {PR.linha_txt(bl['antes'])} | original "
          f"{PR.linha_txt(bl['original'])} | MC lucro {r['mc'].get('prob_lucro', 0):.1f}%")
        p('      custo: ' + '  '.join(f"{c['custo']} pts -> {c['ev']:+.1f}" for c in custos))
        if gn in R.GESTOES:
            exp = ca.assign(
                data=ca['data'].dt.strftime('%d/%m/%Y %H:%M'),
                nivel='r3',
                i_ret=(ca['i'] - ca['n_ret']).clip(lower=0), i_sin=ca['i'],
                rot_saida=ca['motivo'].map(R.ROT_SAIDA), dur_txt=ca['dur_s'].map(R.dur_texto),
            )[['data', 'lado', 'nivel', 'preco_ent', 'preco_sai', 'pts', 'mfe', 'mae', 'dur_s',
               'dur_txt', 'barras', 'motivo', 'rot_saida', 'hora', 'i_ret', 'i_sin', 'i_ent',
               'i_sai', 'n_ret', 'pav_tot', 'exaustao', 'ret_ok', 'geom_ok']]
            variantes[f'fecha|{gn}|r3'] = dict(modo='fecha', gestao=gn, nivel='r3', stats=st,
                                               trades=exp.to_dict('records'))
    return out, variantes


def main():
    d = E.indicadores(E.carrega())
    caminho = os.path.join(SAIDA, 'resumo.json')
    with open(caminho, encoding='utf-8') as f:
        D = json.load(f)
    buf = []

    def p(*a):
        print(*a)
        buf.append(' '.join(str(x) for x in a))
    cand, var = roda(d, p)
    D['candidato'] = R._lim(cand)
    D['variantes'].update(R._lim(var))
    D['rotulo']['r3'] = f'Retracao {S.N_RET_R3}+'
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(D, f, ensure_ascii=False)
    with open(os.path.join(SAIDA, 'candidato_console.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(buf) + '\n')
    print('[OK] candidato anexado a saida/resumo.json')


if __name__ == '__main__':
    main()
