# -*- coding: utf-8 -*-
"""
Saldo de agressao (compra - venda) como filtro do Hull + pavios: o saldo do
candle de sinal, com lag de 1 e 2 barras, janelas, variacao percentual e
variacao contra a media dos ultimos candles.

    python saldo_agressor.py        -> saida/saldo_agressor.json + console
    python relatorio_saldo.py       -> saldo_agressor.html + SALDO_AGRESSOR.md

A medicao e a mesma de volume_agressor.py (grade de cortes, busca contra
ruido, escolha fora, horario, vizinhanca, carteira), so troca a familia.

S = agr_compra - agr_venda de cada candle. Toda leitura e ESPELHADA pelo lado
do trade: positivo = agressao a favor da operacao (compradores agredindo numa
compra, vendedores numa venda). Como o saldo tem escala do volume, as leituras
de nivel sao divididas pela media do saldo EM MODULO nas 20 barras anteriores.

A FAMILIA, fechada antes de medir (12 leituras):

  s_lag0   saldo do candle de sinal / media |S| das 20 anteriores
  s_lag1   o mesmo, uma barra antes (o ultimo candle da retracao)
  s_lag2   o mesmo, duas barras antes
  des_0    desequilibrio do candle de sinal, S / (compra + venda), em [-1, +1]
           -- sem escala nenhuma
  sk_k     (k = 2, 3, 5) saldo SOMADO das ultimas k barras, incluindo a de
           sinal, / (k x media |S| das 20 anteriores a janela)
  spct_k   (k = 1, 2) variacao percentual com lag: (S[i] - S[i-k]) / |S[i-k]|.
           O saldo troca de sinal e passa por zero; com o denominador em modulo
           a variacao continua com o sentido certo, mas explode quando S[i-k] e
           pequeno -- por isso os cortes sao por quantil, que so olham a ordem.
  smed_k   (k = 2, 3, 5) saldo do sinal menos a media do saldo das k barras
           anteriores, / media |S| das 20 anteriores. > 0 = o candle de sinal
           virou a agressao a favor em relacao aos candles da retracao.
"""
import sys

import numpy as np
import pandas as pd

import volume_agressor as VA

JAN_REF = 20
KS_SOMA = (2, 3, 5)
KS_PCT = (1, 2)
KS_MED = (2, 3, 5)

FEATS = {
    's_lag0': 'Saldo do candle de sinal (a favor) / media |saldo| das 20 anteriores',
    's_lag1': 'Saldo 1 barra antes (a favor), normalizado',
    's_lag2': 'Saldo 2 barras antes (a favor), normalizado',
    'des_0': 'Desequilibrio do candle de sinal, saldo / volume agressor (a favor)',
}
for k in KS_SOMA:
    FEATS[f'sk_{k}'] = f'Saldo somado das ultimas {k} barras (a favor), normalizado'
for k in KS_PCT:
    FEATS[f'spct_{k}'] = f'Variacao % do saldo contra {k} barra{"s" if k > 1 else ""} atras'
for k in KS_MED:
    FEATS[f'smed_{k}'] = f'Saldo do sinal menos a media das {k} barras anteriores, normalizado'


def leituras(d, jan_ref=JAN_REF):
    """Leituras no ponto de vista da COMPRA; a venda recebe o sinal trocado."""
    ac = d['agr_c'].astype(float); av = d['agr_v'].astype(float)
    S = ac - av
    A = S.abs()
    ref1 = A.rolling(jan_ref).mean().shift(1).replace(0, np.nan)
    out = dict(S=S.to_numpy(), ref=A.rolling(jan_ref).mean().to_numpy())
    s0 = S / ref1
    out['s_lag0'] = s0.to_numpy()
    out['s_lag1'] = s0.shift(1).to_numpy()
    out['s_lag2'] = s0.shift(2).to_numpy()
    out['des_0'] = (S / (ac + av).replace(0, np.nan)).to_numpy()
    for k in KS_SOMA:
        out[f'sk_{k}'] = (S.rolling(k).sum() / (k * A.rolling(jan_ref).mean().shift(k).replace(0, np.nan))).to_numpy()
    for k in KS_PCT:
        ant = S.shift(k)
        out[f'spct_{k}'] = ((S - ant) / ant.abs().replace(0, np.nan)).to_numpy()
    for k in KS_MED:
        out[f'smed_{k}'] = ((S - S.rolling(k).mean().shift(1)) / ref1).to_numpy()
    return out


def cfg_saldo():
    rd0 = lambda arr: [None if not np.isfinite(v) else round(float(v)) for v in arr]
    return dict(nome='saldo_agressor', titulo='SALDO DE AGRESSAO (COMPRA - VENDA) COMO FILTRO DO HULL + PAVIOS',
                familia='Saldo de agressao', feats=FEATS, leituras=leituras, espelha=True,
                parametros=dict(jan_ref=JAN_REF, ks_soma=KS_SOMA, ks_pct=KS_PCT, ks_med=KS_MED, cortes=VA.CORTES),
                viz_prefixo=('s_lag', 'sk_', 'smed_'),
                candles=lambda d, L: dict(saldo=rd0(L['S']), ref=rd0(L['ref'])))


if __name__ == '__main__':
    sys.exit(VA.main(cfg_saldo()))
