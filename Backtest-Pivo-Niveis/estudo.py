# -*- coding: utf-8 -*-
"""
Mede a hipotese e grava saida/resumo.json - a fonte unica dos numeros.

Tres perguntas, medidas separadamente, sempre contra controle:

  1. ANDAR      - a barra grande no nivel segue na direcao do corpo?
                  Entrada no fechamento dela, e no ROMPIMENTO do extremo.
  2. REVERTER   - ela marca reversao? Entrada contra o corpo, no fechamento,
                  e no rompimento do extremo OPOSTO (a falha da barra).
  3. O NIVEL    - o nivel acrescenta alguma coisa? Cada celula sai em tres
                  versoes: com nivel dentro, SEM nivel dentro, e todas as
                  barras grandes. E a comparacao que separa "barra grande no
                  nivel" de "barra grande".

Tudo medido pela corrida simetrica +X/-X (ver nucleo.py). O numero neutro
e 50%: qualquer celula presa entre 48% e 52% e ruido.
"""
import json
import numpy as np
import pandas as pd

import nucleo as K

BASES = ('WINFUT', 'WINV26')
FATORES = (1.25, 1.50, 2.00)      # "grande" = range >= FATOR x range medio
ALVOS = (100.0, 150.0, 300.0)     # X da corrida simetrica
TOLERANCIAS = (0.00, 0.25)        # folga do toque, em fracoes do range da barra
FAMS = ('medias', 'vwap', 'pivos', 'diant', 'qualquer')
MAX_ROMPE = 5                     # barras de validade do rompimento do extremo

FATOR_VIZ = 1.50                  # a celula que vai para o visualizador
X_VIZ = 150.0


def entradas_fecho(C, ii, lados):
    return ii, lados, C[ii]


def entradas_rompe(H, L, dia, n, ii, lados):
    """Entrada no rompimento do extremo, no lado pedido. Quem nao rompe em
    MAX_ROMPE barras nao vira trade - e essa perda de amostra faz parte do
    resultado, nao e um detalhe de implementacao."""
    idx, lad, ent = [], [], []
    for i, s in zip(ii, lados):
        j, p = K.rompe_extremo(H, L, dia, n, int(i), int(s), MAX_ROMPE)
        if j > 0:
            idx.append(j); lad.append(int(s)); ent.append(p)
    return np.array(idx, int), np.array(lad, int), np.array(ent, float)


def mede_base(nome):
    d, N = K.prepara(nome)
    O, H, L, C = (d[c].to_numpy(float) for c in ('O', 'H', 'L', 'C'))
    dia = d.dia.to_numpy(); n = len(d)
    sb = d.sb.to_numpy(int); tam = d.tam.to_numpy(float)
    valido = ~np.isnan(tam) & (sb != 0)

    out = {'n_barras': int(n), 'pregoes': int(d.dia.nunique()),
           'de': str(d.Data.min().date()), 'ate': str(d.Data.max().date()),
           'range_medio': float((H - L).mean()),
           'celulas': [], 'controles': []}

    # ---- controle absoluto: todas as barras, nos dois sentidos
    for X in ALVOS:
        ii = np.flatnonzero(valido)
        for sen, lados in (('favor', sb[ii]), ('contra', -sb[ii])):
            m = K.celula(H, L, dia, n, ii, lados, C[ii], X)
            if m:
                out['controles'].append(dict(escopo='todas', X=X, sentido=sen, **m))

    # ---- a grade
    for FG in FATORES:
        grande = valido & (tam >= FG)
        for tol in TOLERANCIAS:
            for fam in FAMS:
                t = K.toca(d, N, fam, tol)
                dentro = t['conta'] > 0
                grupos = {
                    'com':  grande & dentro,
                    'sem':  grande & ~dentro,
                    'todas': grande,
                    'corpo': grande & t['no_corpo'],
                    'centrado': grande & dentro & (t['cent'] <= 0.15),
                    'conflu': grande & (t['conta'] >= 2),
                }
                for gr, msk in grupos.items():
                    # 'todas' e 'sem' nao dependem da familia; so uma vez
                    if gr in ('todas', 'sem') and fam != 'qualquer':
                        continue
                    ii = np.flatnonzero(msk)
                    if len(ii) < 25:
                        continue
                    for X in ALVOS:
                        for sen, sgn in (('favor', 1), ('contra', -1)):
                            for ent, arg in (('fecho', None), ('rompe', True)):
                                lados = sgn * sb[ii]
                                if arg is None:
                                    a, b, c = entradas_fecho(C, ii, lados)
                                else:
                                    a, b, c = entradas_rompe(H, L, dia, n, ii, lados)
                                if len(a) < 25:
                                    continue
                                m = K.celula(H, L, dia, n, a, b, c, X)
                                if m and m['n'] >= 25:
                                    out['celulas'].append(dict(
                                        FG=FG, tol=tol, fam=fam, grupo=gr,
                                        X=X, sentido=sen, entrada=ent, **m))
    return d, N, out


def robustez(d, X=X_VIZ, FG=FATOR_VIZ):
    """A celula que sobreviveu, metade a metade do periodo."""
    O, H, L, C = (d[c].to_numpy(float) for c in ('O', 'H', 'L', 'C'))
    dia = d.dia.to_numpy(); n = len(d)
    sb = d.sb.to_numpy(int); tam = d.tam.to_numpy(float)
    grande = ~np.isnan(tam) & (sb != 0) & (tam >= FG)
    dias_u = np.array(sorted(set(dia)))
    corte = dias_u[len(dias_u) // 2]
    saida = []
    for rot, msk in (('1a metade', dia < corte), ('2a metade', dia >= corte)):
        ii = np.flatnonzero(grande & msk)
        if len(ii) < 25:
            continue
        a, b, c = entradas_rompe(H, L, dia, n, ii, -sb[ii])
        if len(a) < 25:
            continue
        m = K.celula(H, L, dia, n, a, b, c, X)
        if m:
            saida.append(dict(metade=rot, corte=str(corte), **m))
    return saida


def trades_viz(d, N, FG=FATOR_VIZ):
    """Os trades que o visualizador mostra: a barra grande que FALHA -
    rompimento do extremo OPOSTO ao corpo - com a gestao da casa.

    Sai marcado com a familia de nivel que a barra alcanca, para o filtro do
    grafico deixar comparar 'com nivel' e 'sem nivel' com o olho."""
    O, H, L, C = (d[c].to_numpy(float) for c in ('O', 'H', 'L', 'C'))
    dia = d.dia.to_numpy(); n = len(d)
    sb = d.sb.to_numpy(int); tam = d.tam.to_numpy(float)
    grande = ~np.isnan(tam) & (sb != 0) & (tam >= FG)

    marca = {f: K.toca(d, N, f, 0.0)['conta'] > 0 for f in FAMS}
    trades = []
    livre = -1
    for i in np.flatnonzero(grande):
        s = -int(sb[i])
        j, p = K.rompe_extremo(H, L, dia, n, int(i), s, MAX_ROMPE)
        if j < 0 or j < livre:
            continue
        t = K.simula(H, L, C, dia, n, j, s, p)
        if t is None:
            continue
        t['gatilho'] = int(i)          # a barra grande
        t['tam'] = float(tam[i])
        t['fams'] = [f for f in FAMS if f != 'qualquer' and marca[f][i]]
        trades.append(t)
        livre = t['saiu'] + 1
    return pd.DataFrame(trades)


def main():
    R = {'bases': {}, 'param': dict(FATORES=list(FATORES), ALVOS=list(ALVOS),
                                    TOLERANCIAS=list(TOLERANCIAS),
                                    MAX_ROMPE=MAX_ROMPE, FATOR_VIZ=FATOR_VIZ,
                                    X_VIZ=X_VIZ, STOP=K.STOP, ALVO=K.ALVO)}
    guarda = {}
    for nome in BASES:
        print('medindo', nome, '...', flush=True)
        d, N, out = mede_base(nome)
        out['robustez'] = robustez(d)
        tr = trades_viz(d, N)
        out['trades'] = K.metricas(tr)
        R['bases'][nome] = out
        guarda[nome] = (d, N, tr)
        print('   %d celulas, %d trades no visualizador'
              % (len(out['celulas']), len(tr)), flush=True)
        tr.to_csv('%s/trades_%s.csv' % (K.SAIDA, nome), index=False)

    with open('%s/resumo.json' % K.SAIDA, 'w', encoding='utf-8') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=str)
    print('-> saida/resumo.json')
    return R, guarda


if __name__ == '__main__':
    main()
