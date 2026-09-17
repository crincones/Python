# -*- coding: utf-8 -*-
"""
Backteste: 2 a 4 candles num sentido + 1 contra, com UMA restricao -- a
Hull 50 inclinada a favor do trade.

    python hull_contra.py            -> saida/hull_contra.json + console

O padrao (compra; venda e o espelho):
  Hull 50 ASCENDENTE no fechamento do candle contra (hma[i] > hma[i-1]),
  2 a 4 candles seguidos de BAIXA, depois 1 candle de ALTA. Compra no
  fechamento dele. Na venda: Hull descendente, 2 a 4 altas, 1 baixa.

Dito de outro jeito: e uma retracao de 2 a 4 candles contra a Hull,
seguida do primeiro candle que volta a favor dela. O trade vai no sentido
do candle contra -- o mesmo dos indicadores magenta e verde --, e a Hull
decide quais desses candles valem.

Perguntas:
  1. A Hull a favor melhora o sinal em relacao ao padrao sem filtro?
  2. Dentro da condicao Hull, quantas barras antes rendem melhor?
  3. Dentro da condicao Hull, os pavios do candle contra (lado da
     abertura e lado do fechamento) separam alguma coisa?

Mesmos controles do estudo pavio_contra.py: o universo sem filtro, a Hull
CONTRA (o complemento), o trade invertido, subconjuntos sorteados, os tres
tercos, e -- aqui -- o periodo da Hull ao redor de 50.
"""
import io
import json
import os
import sys

import numpy as np
import pandas as pd

import engine as E
import pavio_contra as P
import periodos as PR

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
os.makedirs(SAIDA, exist_ok=True)

BARRAS_MIN, BARRAS_MAX = 2, 4
HULL_PER = 50
HULL_TESTE = (21, 34, 50, 80)

ENTRADAS = P.ENTRADAS
ROT_ENTRADA = P.ROT_ENTRADA
GESTOES = P.GESTOES
ROT_GESTAO = P.ROT_GESTAO

CORTES_ABRE = [-0.1, 0.1, 10, 25, 45, 65, 90, 100.1]
ROT_ABRE = ['0%', '5-10%', '10-25%', '25-45%', '45-65%', '65-90%', '90%+']
CORTES_FECH = [-0.1, 0.1, 10, 25, 100.1]
ROT_FECH = ['0%', '5-10%', '10-25%', '25%+']

# Regras de pavio JA DEFINIDAS antes deste estudo -- testadas como estao,
# sem reajustar faixa. Sao as unicas que valem como teste; as faixas do
# estudo por faixa sao exploracao.
REGRAS = {
    'magenta': ('Pavio da abertura 25-90% (magenta)',
                lambda t: t['pav_pct'].between(25, 90)),
    'verde': ('Pavio da abertura 5-25% (verde)',
              lambda t: t['pav_pct'].between(5, 25)),
    'fech10': ('Pavio do fechamento ate 10%',
               lambda t: t['pav_outro_pct'] <= 10),
}

# Combinacoes dos achados, SEMPRE dentro da condicao Hull + 2-4 barras.
# 'h23' vem do "4 barras e ruim" medido em dois estudos; 'f10' do pavio do
# fechamento, que ja pendia para o menor no universo sem Hull.
CANDIDATOS = {
    'h': ('Hull + 2 a 4 barras', lambda t: t['n_fav'] >= 0),
    'h23': ('Hull + 2 a 3 barras', lambda t: t['n_fav'] <= 3),
    'hf10': ('Hull + 2 a 4 + fechamento ate 10%',
             lambda t: t['pav_outro_pct'] <= 10),
    'h23f10': ('Hull + 2 a 3 + fechamento ate 10%',
               lambda t: (t['n_fav'] <= 3) & (t['pav_outro_pct'] <= 10)),
}

_buf = io.StringIO()


def p(*a, **k):
    print(*a, **k)
    print(*a, **k, file=_buf)


def anexa_hull(u, d, per, col='hull_ok'):
    """Hull a favor do trade no fechamento do candle contra."""
    h = E.hma(d['c'].to_numpy(), per)
    i = u['i'].to_numpy()
    incl = (h[i] - h[i - 1]) * u['lado'].to_numpy()
    u = u.copy()
    u[col] = incl > 0
    u[col + '_valida'] = ~np.isnan(h[i - 1])
    return u


def ev_linha(b):
    if not b['n']:
        return '   -'
    tt = ' / '.join('   -  ' if v is None else f'{v:+6.1f}' for v in b['ev_terco'])
    return (f"n={b['n']:4d}  EV {b['ev']:+6.1f}  acerto {b['wr']:4.1f}%  "
            f"tercos {tt}")


def main():
    d = E.carrega()
    dias = sorted(d['dia'].unique())
    p('=' * 74)
    p('BACKTESTE  Hull 50 a favor + 2 a 4 candles + 1 contra')
    p('=' * 74)
    p(f"base: {len(d)} barras PI 20, {d['data'].iat[0]:%d/%m/%Y} a "
      f"{d['data'].iat[-1]:%d/%m/%Y}, {len(dias)} pregoes")

    u = P.universo(d)
    for per in HULL_TESTE:
        u = anexa_hull(u, d, per, f'hull{per}')
    u['hull_ok'] = u[f'hull{HULL_PER}']
    u = u[u[f'hull{max(HULL_TESTE)}_valida']].reset_index(drop=True)
    ui = u.copy(); ui['lado'] = -ui['lado']

    n24 = u['n_fav'].between(BARRAS_MIN, BARRAS_MAX)
    u['no_padrao'] = n24 & u['hull_ok']
    ui['no_padrao'] = u['no_padrao']
    p(f"universo: {len(u)} candles contra; {int(n24.sum())} com 2-4 barras antes; "
      f"{int(u['no_padrao'].sum())} com Hull a favor "
      f"({int((u['no_padrao'] & (u['lado'] > 0)).sum())} compras, "
      f"{int((u['no_padrao'] & (u['lado'] < 0)).sum())} vendas)")

    res = {}
    for ent in ENTRADAS:
        for ges, gg in GESTOES.items():
            t = E.executa(d, u, ent, gg)
            t, c1, c2 = P.marca_tercos(t, dias)
            res[(ent, ges)] = t
            if ent == 'fecha':
                ti = E.executa(d, ui, ent, gg)
                ti, _, _ = P.marca_tercos(ti, dias)
                res[(ent, ges, 'inv')] = ti
    p(f"tercos: T1 ate {c1}, T2 ate {c2}, T3 depois")

    S = dict(parametros=dict(barras_min=BARRAS_MIN, barras_max=BARRAS_MAX,
                             hull=HULL_PER, stop=E.STOP),
             base=dict(barras=len(d), dias=len(dias),
                       ini=f"{d['data'].iat[0]:%d/%m/%Y}",
                       fim=f"{d['data'].iat[-1]:%d/%m/%Y}", c1=c1, c2=c2),
             rot_entrada=ROT_ENTRADA, rot_gestao=ROT_GESTAO,
             rot_abre=ROT_ABRE, rot_fech=ROT_FECH,
             regras={k: v[0] for k, v in REGRAS.items()})

    def pad(t):
        return t[t['n_fav'].between(BARRAS_MIN, BARRAS_MAX) & t['hull_ok']]

    # ------------------------------------------------ 1. Hull x controles
    p('\n--- 1. EV por sinal (pts, isolado, bruto) ---------------------------')
    p(f"{'entrada':9s} {'gestao':16s} {'Hull a favor':>15s} {'sem filtro':>15s} "
      f"{'Hull contra':>15s} {'invertido':>15s} {'pct':>4s}")
    comp = {}; sort = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges)]
            m24 = t['n_fav'].between(BARRAS_MIN, BARRAS_MAX)
            ti = res.get((ent, ges, 'inv'))
            b = dict(hull=P.resumo_grupo(t[m24 & t['hull_ok']]),
                     sem=P.resumo_grupo(t[m24]),
                     contra=P.resumo_grupo(t[m24 & ~t['hull_ok']]),
                     inverso=(P.resumo_grupo(ti[ti['no_padrao']])
                              if ti is not None else dict(n=0)))
            comp[f'{ent}|{ges}'] = b
            s24 = t[m24].reset_index(drop=True)
            sort[f'{ent}|{ges}'] = P.sorteio(s24, s24['hull_ok'])

            def f(x):
                return f"{x['ev']:+6.1f} ({x['n']:4d})" if x.get('n') else 'n/a'
            p(f"{ent:9s} {ROT_GESTAO[ges]:16s} {f(b['hull']):>15s} {f(b['sem']):>15s} "
              f"{f(b['contra']):>15s} {f(b['inverso']):>15s} "
              f"{sort[f'{ent}|{ges}']['percentil']:4.0f}")
    S['comparacao'] = comp; S['sorteio'] = sort

    # ------------------------------------------------ 2. lados
    lados = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges)]; x = pad(t)
            m24 = t['n_fav'].between(BARRAS_MIN, BARRAS_MAX)
            lados[f'{ent}|{ges}'] = dict(
                compra=P.resumo_grupo(x[x['lado'] > 0]),
                venda=P.resumo_grupo(x[x['lado'] < 0]),
                compra_sem=P.resumo_grupo(t[m24 & (t['lado'] > 0)]),
                venda_sem=P.resumo_grupo(t[m24 & (t['lado'] < 0)]))
    S['lados'] = lados
    p('\n--- 2. compra x venda (Hull a favor) --------------------------------')
    for ent in ENTRADAS:
        for ges in GESTOES:
            x = lados[f'{ent}|{ges}']
            p(f"  {ent:9s} {ROT_GESTAO[ges]:16s} compra {x['compra']['ev']:+6.1f} "
              f"({x['compra']['n']}) [sem {x['compra_sem']['ev']:+6.1f}]  "
              f"venda {x['venda']['ev']:+6.1f} ({x['venda']['n']}) "
              f"[sem {x['venda_sem']['ev']:+6.1f}]")

    # ------------------------------------------------ 3. barras antes
    nbar = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges)]; h = t[t['hull_ok']]
            linhas = []
            for rot, m in (('1', h['n_fav'] == 1), ('2', h['n_fav'] == 2),
                           ('3', h['n_fav'] == 3), ('4', h['n_fav'] == 4),
                           ('5+', h['n_fav'] >= 5)):
                b = P.resumo_grupo(h[m]); b['faixa'] = rot
                linhas.append(b)
            nbar[f'{ent}|{ges}'] = linhas
    S['barras_antes'] = nbar
    p('\n--- 3. barras antes (Hull a favor, fechamento) ---------------------')
    for ges in GESTOES:
        p(f"  [{ROT_GESTAO[ges]}]")
        for b in nbar[f'fecha|{ges}']:
            p(f"    {b['faixa']:3s} {ev_linha(b)}")

    # ------------------------------------------------ 4. pavios do candle contra
    def por_faixa(x, col, cortes, rotulos):
        fx = pd.cut(x[col], cortes, labels=rotulos)
        out = []
        for r in rotulos:
            b = P.resumo_grupo(x[fx == r]); b['faixa'] = r
            out.append(b)
        return out

    wa = {}; wf = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            x = pad(res[(ent, ges)])
            for chave, sub in (('', x), ('|compra', x[x['lado'] > 0]),
                               ('|venda', x[x['lado'] < 0])):
                wa[f'{ent}|{ges}{chave}'] = por_faixa(sub, 'pav_pct', CORTES_ABRE, ROT_ABRE)
                wf[f'{ent}|{ges}{chave}'] = por_faixa(sub, 'pav_outro_pct', CORTES_FECH, ROT_FECH)
    S['pavio_abre'] = wa; S['pavio_fech'] = wf
    p('\n--- 4a. pavio do lado da ABERTURA do candle contra (Hull, fechamento)')
    for ges in GESTOES:
        p(f"  [{ROT_GESTAO[ges]}]")
        for b in wa[f'fecha|{ges}']:
            p(f"    {b['faixa']:7s} {ev_linha(b)}")
    p('\n--- 4b. pavio do lado do FECHAMENTO do candle contra (Hull, fechamento)')
    for ges in GESTOES:
        p(f"  [{ROT_GESTAO[ges]}]")
        for b in wf[f'fecha|{ges}']:
            p(f"    {b['faixa']:7s} {ev_linha(b)}")
    p('\n  por lado, 1:3 com parcial:')
    for lado in ('compra', 'venda'):
        p(f"    abertura  {lado:6s} " + '  '.join(
            f"{b['faixa']} {b['ev']:+.1f}({b['n']})" for b in wa[f'fecha|parcial|{lado}'] if b['n']))
        p(f"    fechamen. {lado:6s} " + '  '.join(
            f"{b['faixa']} {b['ev']:+.1f}({b['n']})" for b in wf[f'fecha|parcial|{lado}'] if b['n']))

    # ------------------------------------------------ 5. regras de pavio pre-definidas
    p('\n--- 5. regras de pavio JA DEFINIDAS, dentro da condicao Hull ---------')
    reg = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            x = pad(res[(ent, ges)]).reset_index(drop=True)
            for k, (rot, fn) in REGRAS.items():
                m = fn(x)
                b = P.resumo_grupo(x[m])
                b['sorteio'] = P.sorteio(x, m) if m.sum() else None
                b['compra'] = P.resumo_grupo(x[m & (x['lado'] > 0)])
                b['venda'] = P.resumo_grupo(x[m & (x['lado'] < 0)])
                b['fora'] = P.resumo_grupo(x[~m])
                reg[f'{ent}|{ges}|{k}'] = b
    S['regras_res'] = reg
    for ent in ENTRADAS:
        for ges in GESTOES:
            linha = []
            for k in REGRAS:
                b = reg[f'{ent}|{ges}|{k}']
                linha.append(f"{k} {b['ev']:+6.1f} ({b['n']:3d}) fora {b['fora']['ev']:+6.1f} "
                             f"pct {b['sorteio']['percentil']:3.0f}")
            p(f"  {ent:9s} {ROT_GESTAO[ges]:16s} " + ' | '.join(linha))

    # ------------------------------------------------ 6. periodo da Hull
    p('\n--- 6. periodo da Hull (2-4 barras, fechamento) ---------------------')
    per = {}
    for ges in GESTOES:
        for ent in ENTRADAS:
            t = res[(ent, ges)]
            m24 = t['n_fav'].between(BARRAS_MIN, BARRAS_MAX)
            linhas = []
            for hp in HULL_TESTE:
                b = P.resumo_grupo(t[m24 & t[f'hull{hp}']]); b['faixa'] = f'Hull {hp}'
                b['contra'] = P.resumo_grupo(t[m24 & ~t[f'hull{hp}']])
                linhas.append(b)
            per[f'{ent}|{ges}'] = linhas
        p(f"  [{ROT_GESTAO[ges]}] " + '  '.join(
            f"{b['faixa']}: {b['ev']:+.1f} ({b['n']}) contra {b['contra']['ev']:+.1f}"
            for b in per[f'fecha|{ges}']))
    S['periodos'] = per

    # ------------------------------------------------ 7. horario
    horas = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            x = pad(res[(ent, ges)]).copy()
            x['h'] = x['hora'].astype(int)
            linhas = []
            for hh in range(9, 19):
                b = P.resumo_grupo(x[x['h'] == hh]); b['faixa'] = f'{hh}h'
                linhas.append(b)
            horas[f'{ent}|{ges}'] = linhas
    S['horas'] = horas

    # ------------------------------------------------ 8. combinacoes
    p('\n--- 8. combinacoes dentro da condicao Hull (2-4 barras = base) --------')
    cand = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges)]
            base = pad(t).reset_index(drop=True)
            for k, (rot, fn) in CANDIDATOS.items():
                m = fn(base)
                b_ = P.resumo_grupo(base[m])
                b_['sorteio'] = P.sorteio(base, m)
                b_['compra'] = P.resumo_grupo(base[m & (base['lado'] > 0)])
                b_['venda'] = P.resumo_grupo(base[m & (base['lado'] < 0)])
                b_['custo10'] = (b_['ev'] - 10) if b_['n'] else None
                cand[f'{ent}|{ges}|{k}'] = b_
    for ent in ENTRADAS:
        for ges in GESTOES:
            p(f"  [{ent} {ROT_GESTAO[ges]}]")
            for k in CANDIDATOS:
                b_ = cand[f'{ent}|{ges}|{k}']
                p(f"    {k:8s} {ev_linha(b_)}  C {b_['compra']['ev']:+6.1f} "
                  f"V {b_['venda']['ev']:+6.1f}  pct {b_['sorteio']['percentil']:3.0f}")
    S['candidatos'] = cand
    S['rot_candidatos'] = {k: v[0] for k, v in CANDIDATOS.items()}

    # ------------------------------------------------ 8b. vizinhanca do candidato
    #  Se o resultado so existir exatamente em "2 a 3 barras, fechamento ate
    #  10%, Hull 50", e pico de ajuste. Variando cada corte com os outros
    #  fixos, o que se procura e um PLATO.
    p('\n--- 8b. vizinhanca de h23f10 (fechamento) ---------------------------')
    viz = {}
    for ges in GESTOES:
        t = res[('fecha', ges)]
        linhas = []
        def add(rot, eixo, m):
            b_ = P.resumo_grupo(t[m]); b_['faixa'] = rot; b_['eixo'] = eixo
            linhas.append(b_)
        hb = t['hull_ok']; nb = t['n_fav'].between(2, 3); fb = t['pav_outro_pct'] <= 10
        for lim in (0, 5, 10, 15, 25, 100):
            add(f'fech <= {lim}%', 'pavio do fechamento', hb & nb & (t['pav_outro_pct'] <= lim))
        for a_, b2 in ((1, 3), (2, 2), (2, 3), (2, 4), (3, 3), (1, 4)):
            add(f'{a_} a {b2} barras', 'barras antes', hb & t['n_fav'].between(a_, b2) & fb)
        for hp in HULL_TESTE:
            add(f'Hull {hp}', 'periodo da Hull', t[f'hull{hp}'] & nb & fb)
        viz[f'fecha|{ges}'] = linhas
        p(f"  [{ROT_GESTAO[ges]}]")
        for b_ in linhas:
            p(f"    {b_['eixo']:20s} {b_['faixa']:14s} {ev_linha(b_)}")
    S['vizinhanca'] = viz

    # ------------------------------------------------ 9. carteira
    p('\n--- 7. carteira, uma posicao por vez --------------------------------')
    cart = {}; trades = {}
    ini = d['data'].iat[0]; fim = d['data'].iat[-1]
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges)]
            m24 = t['n_fav'].between(BARRAS_MIN, BARRAS_MAX)
            ph = t[m24 & t['hull_ok']]
            vars_ = [('sem', t[m24])] + [(k, ph[fn(ph)]) for k, (_, fn) in CANDIDATOS.items()]
            for var, sel in vars_:
                c = E.carteira(sel)
                st = E.estatisticas(c)
                if len(c):
                    st['xs'] = ((c['data_sai'] - ini) / (fim - ini)).tolist()
                    st['dt'] = [f'{x:%d/%m %H:%M}' for x in c['data_sai']]
                    st['mc'] = P.monte_carlo(c['pts'].to_numpy())
                    st['mfe'] = c['mfe'].tolist(); st['mae'] = c['mae'].tolist()
                    st['pts'] = c['pts'].tolist(); st['dur_s'] = c['dur_s'].tolist()
                cart[f'{ent}|{ges}|{var}'] = st
                if var in ('h', 'h23f10'):
                    trades[f'{ent}|{ges}|{var}'] = [
                        dict(i=int(r.i), i_ent=int(r.i_ent), i_sai=int(r.i_sai),
                             lado=int(r.lado), ent=float(r.preco_ent),
                             sai=float(r.preco_sai), pts=float(r.pts),
                             mfe=float(r.mfe), mae=float(r.mae), motivo=r.motivo,
                             n_fav=int(r.n_fav), pav=float(r.pav_pct),
                             pavf=float(r.pav_outro_pct),
                             data=f'{r.data:%d/%m/%Y %H:%M:%S}')
                        for r in c.itertuples()]
                    p(f"  {ent:9s} {ROT_GESTAO[ges]:16s} {var:7s} trades {st['trades']:4d}  "
                      f"liq {st['lucro_liq']:+8.0f}  FL {st['fator_lucro']:.2f}  "
                      f"acerto {st['winrate']:4.1f}%  DD {st['dd_max']:6.0f}  "
                      f"MC lucro {st['mc'].get('p_lucro', 0):.0f}%")
    S['carteira'] = cart; S['trades'] = trades

    custo = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            x = pad(res[(ent, ges)]); x = x[x['aceito']]
            custo[f'{ent}|{ges}'] = {str(cc): float(x['pts'].mean() - cc) for cc in (0, 5, 10)}
    S['custo'] = custo

    # ------------------------------------------------ fora da amostra original
    #  A Hull a favor era hipotese previa; '2 a 3 barras' e 'fechamento ate
    #  10%' foram escolhidos na base antiga (06/08 a 11/09). O resto e teste.
    p('\n--- 9. fora da amostra original (regras escolhidas em 06/08 a 11/09) ---')
    blocos = {}
    for ent in ENTRADAS:
        for ges in GESTOES:
            t = res[(ent, ges)]
            m24 = t['n_fav'].between(BARRAS_MIN, BARRAS_MAX)
            ph = t[m24 & t['hull_ok']]
            vars_ = ([('sem', t[m24]), ('contra', t[m24 & ~t['hull_ok']])]
                     + [(k, ph[fn(ph)]) for k, (_, fn) in CANDIDATOS.items()])
            for var, sel in vars_:
                blocos[f'{ent}|{ges}|{var}'] = dict(
                    sinais=PR.por_bloco(sel), carteira=PR.por_bloco(E.carteira(sel)),
                    meses=PR.por_mes(sel))
    for ges in GESTOES:
        p(f"  [fecha {ROT_GESTAO[ges]}]")
        for var in ('sem', 'contra', 'h', 'h23f10'):
            b = blocos[f'fecha|{ges}|{var}']['sinais']
            p(f"    {var:7s} antes {PR.linha_txt(b['antes'])} | original {PR.linha_txt(b['original'])}"
              f" | depois {PR.linha_txt(b['depois'])}")
    S['blocos'] = blocos
    S['regime'] = PR.regime(d)
    S['rot_bloco'] = PR.ROT_BLOCO

    dh = E.indicadores(d)
    S['candles'] = dict(t=[int(x.value // 10**6) for x in d['data']],
                        o=d['o'].tolist(), h=d['h'].tolist(),
                        l=d['l'].tolist(), c=d['c'].tolist(),
                        hma=[None if np.isnan(v) else round(float(v), 1)
                             for v in dh['hma']])

    with open(os.path.join(SAIDA, 'hull_contra.json'), 'w', encoding='utf-8') as f:
        json.dump(P._lim(S), f, ensure_ascii=False)
    with open(os.path.join(SAIDA, 'hull_contra_console.txt'), 'w', encoding='utf-8') as f:
        f.write(_buf.getvalue())
    p('\ngravado: saida/hull_contra.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
