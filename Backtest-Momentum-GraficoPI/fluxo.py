# -*- coding: utf-8 -*-
"""
Anexa as colunas de AGRESSAO e TEMPO DE BARRA a base do backteste.

A base nova (WINFUT_20PI_Agr_Tempo.csv) e a MESMA serie de 20 PI, com
quatro colunas a mais e 88 barras a mais no fim. Duas armadilhas:

  1. 43 timestamps se repetem (barras fechadas no mesmo milissegundo).
     Dentro de um grupo desses os dois arquivos listam as MESMAS barras
     em ORDEM DIFERENTE. Casar por timestamp faria produto cartesiano e
     embaralharia agressao com a barra errada. Aqui o alinhamento e
     POSICIONAL e, dentro de cada grupo repetido, permuta-se a base nova
     para casar o OHLC da base velha -- que e a que manda, porque e sobre
     ela que todo o backteste ja foi medido.

  2. `BarDurationF*1000` esta em MINUTOS x 1000 (conferido: correlacao
     1,0000 com o intervalo real ate a barra seguinte). dur_s = dur_f*0.06.
"""
import os, sys
import numpy as np, pandas as pd

BASE = r'C:\Users\Carlos\Documents\GitHub\Python\Backtest-Momentum-GraficoPI'
if BASE not in sys.path:
    sys.path.insert(0, BASE)
import engine as E

ARQ_FLUXO = os.path.join(BASE, 'WINFUT', 'WINFUT_20PI_Agr_Tempo.csv')


def carrega_fluxo(caminho=ARQ_FLUXO):
    n = pd.read_csv(caminho, sep='\t', decimal=',', thousands='.')
    n.columns = ['data', 'o', 'h', 'l', 'c', 'agr_c', 'agr_v',
                 'dur_f', 'qtd', 'negs']
    n['data'] = pd.to_datetime(n['data'], format='%d/%m/%Y %H:%M:%S.%f')
    return n.sort_values('data', kind='stable').reset_index(drop=True)


def _casa(v, n):
    """Devolve, para cada linha de `v`, o indice da linha de `n`.

    Alinhamento posicional; dentro de cada grupo de timestamp repetido,
    permuta para casar o OHLC. Levanta se sobrar alguma barra sem par.
    """
    assert (v['data'].to_numpy() == n['data'].to_numpy()[:len(v)]).all(), \
        'os timestamps nao batem posicionalmente'
    idx = np.arange(len(v))
    chave = lambda df, i: (df['o'].iat[i], df['h'].iat[i],
                           df['l'].iat[i], df['c'].iat[i])
    # grupos de timestamp repetido
    g = v.groupby('data', sort=False).indices
    trocas = 0
    for _, pos in g.items():
        if len(pos) == 1:
            continue
        alvo = [chave(v, i) for i in pos]
        disp = {chave(n, i): i for i in pos}
        if len(disp) != len(pos):
            continue                      # barras identicas: ordem indiferente
        novo = []
        for k in alvo:
            if k not in disp:
                raise ValueError('grupo %s nao casa o OHLC' % v['data'].iat[pos[0]])
            novo.append(disp[k])
        if list(novo) != list(pos):
            trocas += 1
        idx[pos] = novo
    return idx, trocas


def anexa(d=None, verbose=False):
    """Devolve a base do backteste com as colunas de fluxo anexadas.

    Colunas novas, todas medidas NA PROPRIA BARRA (nada do futuro):
      agr_c, agr_v  volume agressor comprador / vendedor
      agr_liq       (agr_c - agr_v), em contratos
      agr_des       desequilibrio normalizado: (c-v)/(c+v), em [-1, +1]
      qtd, negs     volume total e numero de negocios
      dur_s         duracao da barra, em segundos
      vel           pontos por segundo: 100 / dur_s (corpo do PI = 100)
    """
    if d is None:
        d = E.carrega()
    n = carrega_fluxo()
    idx, trocas = _casa(d, n)
    f = n.iloc[idx].reset_index(drop=True)

    # A ULTIMA barra da base antiga estava EM FORMACAO quando o arquivo foi
    # exportado (fecha a 40 pts da abertura, nao a 100). A base nova, mais
    # recente, ja a tem fechada. E a unica divergencia tolerada -- e so na
    # ultima barra, onde nenhum trade chega a ser resolvido.
    for col in 'ohlc':
        dif = np.abs(d[col].to_numpy() - f[col].to_numpy())
        ruim = np.nonzero(dif > 1e-9)[0]
        assert list(ruim) in ([], [len(d) - 1]),             'OHLC divergente em %s nas barras %s' % (col, ruim[:5])

    d = d.copy()
    d['agr_c'] = f['agr_c'].to_numpy()
    d['agr_v'] = f['agr_v'].to_numpy()
    d['qtd'] = f['qtd'].to_numpy()
    d['negs'] = f['negs'].to_numpy()
    d['dur_s'] = f['dur_f'].to_numpy() * 0.06      # minutos*1000 -> segundos

    tot = d['agr_c'] + d['agr_v']
    d['agr_liq'] = d['agr_c'] - d['agr_v']
    d['agr_des'] = np.where(tot > 0, d['agr_liq'] / tot.replace(0, np.nan), 0.0)
    d['agr_des'] = d['agr_des'].fillna(0.0)
    # velocidade: o corpo do PI e sempre 100 pts, entao 100/dur e
    # comparavel entre barras. Barras de duracao 0 (rajada) viram o teto.
    d['vel'] = np.where(d['dur_s'] > 0, E.PI_PONTOS / d['dur_s'].replace(0, np.nan),
                        np.nan)
    d['vel'] = d['vel'].fillna(d['vel'].max())

    if verbose:
        print('fluxo anexado: %d barras, %d grupos reordenados' % (len(d), trocas))
    return d


if __name__ == '__main__':
    d = anexa(verbose=True)
    print(d[['agr_c','agr_v','agr_des','qtd','negs','dur_s','vel']]
          .describe().T.to_string(float_format=lambda x: '%.3f' % x))
    print('\ndur_s: p05=%.1f p50=%.1f p95=%.1f  zeros=%d'
          % (d['dur_s'].quantile(.05), d['dur_s'].median(),
             d['dur_s'].quantile(.95), int((d['dur_s']==0).sum())))
