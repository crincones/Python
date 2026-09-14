# -*- coding: utf-8 -*-
"""
Converte a exportacao do console do LogCandles_Console.ntsl num CSV
estruturado, um candle por linha, em ordem cronologica.

    python Robo-NTSL/estrutura_export.py [entrada] [saida]

    padrao: WINFUT/WINFUT_20PI_Robo-Export  ->  WINFUT/WINFUT_20PI_Robo.csv

Colunas (separador ",", ponto decimal, datas ISO):

  barra         CurrentBar no Profit (0 = primeiro candle carregado)
  data_hora     abertura do candle, AAAA-MM-DD HH:MM (o NTSL nao da segundos)
  data, hora    o mesmo, separado
  abertura, maxima, minima, fechamento     pontos
  agr_compra    AgressionVolBuy
  agr_venda     AgressionVolSell
  agr_saldo     agr_compra - agr_venda
  duracao_min   BarDurationF, minutos
  duracao_s     a mesma duracao em segundos

A decodificacao e a de decodifica_log.py (qualquer modo do robo, blocos
colados, repeticoes descartadas). Se existir WINFUT/WINFUT_20PI_Agr_Tempo.csv
(exportacao direta do Profit), o trecho em comum e comparado campo a campo.
"""
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import decodifica_log as DL      # noqa: E402

ENTRADA = os.path.join(BASE, 'WINFUT', 'WINFUT_20PI_Robo-Export')
SAIDA = os.path.join(BASE, 'WINFUT', 'WINFUT_20PI_Robo.csv')
PROFIT = os.path.join(BASE, 'WINFUT', 'WINFUT_20PI_Agr_Tempo.csv')


def estrutura(df):
    df = df.drop_duplicates('Barra', keep='first').sort_values('Barra').reset_index(drop=True)
    dt = pd.to_datetime(df['Data'] + ' ' + df['Hora'], format='%d/%m/%Y %H:%M')
    out = pd.DataFrame({
        'barra': df['Barra'].astype(int),
        'data_hora': dt.dt.strftime('%Y-%m-%d %H:%M'),
        'data': dt.dt.strftime('%Y-%m-%d'),
        'hora': dt.dt.strftime('%H:%M'),
        'abertura': df['Abertura'].astype(int),
        'maxima': df['Maxima'].astype(int),
        'minima': df['Minima'].astype(int),
        'fechamento': df['Fechamento'].astype(int),
        'agr_compra': df['AgressionVolBuy'].astype(int),
        'agr_venda': df['AgressionVolSell'].astype(int),
    })
    out['agr_saldo'] = out['agr_compra'] - out['agr_venda']
    out['duracao_min'] = (df['BarDurationF*1000'] / 1000).round(3)
    out['duracao_s'] = (df['BarDurationF*1000'] * 0.06).round(2)
    return out


def compara_profit(out):
    """Trecho em comum com a exportacao direta do Profit, campo a campo."""
    if not os.path.exists(PROFIT):
        return None
    p = pd.read_csv(PROFIT, sep='\t', decimal=',', thousands='.')
    p.columns = ['data', 'o', 'h', 'l', 'c', 'ac', 'av', 'dur', 'q', 't']
    p['data'] = pd.to_datetime(p['data'], format='%d/%m/%Y %H:%M:%S.%f')
    p = p.iloc[::-1].reset_index(drop=True)
    P = p[['o', 'h', 'l', 'c', 'ac', 'av', 'dur']].round().astype(int).to_numpy()
    R = np.column_stack([out[c].to_numpy() for c in
                         ('abertura', 'maxima', 'minima', 'fechamento', 'agr_compra', 'agr_venda')]
                        + [np.rint(out['duracao_min'].to_numpy() * 1000).astype(int)])
    # alinha pela primeira sequencia de 5 candles identicos
    k = next((k for k in range(len(R) - 5) if (R[k:k + 5] == P[:5]).all()), None)
    if k is None:
        return dict(alinhou=False)
    n = min(len(R) - k, len(P))
    iguais = (R[k:k + n] == P[:n]).all(axis=1)
    hora_ok = (p['data'].iloc[:n].dt.strftime('%Y-%m-%d %H:%M').to_numpy()
               == out['data_hora'].iloc[k:k + n].to_numpy())
    return dict(alinhou=True, barra_ini=int(out['barra'].iat[k]), n=int(n),
                iguais=int(iguais.sum()), hora_iguais=int(hora_ok.sum()),
                de=out['data_hora'].iat[k], ate=out['data_hora'].iat[k + n - 1])


def main():
    ent = sys.argv[1] if len(sys.argv) > 1 else ENTRADA
    sai = sys.argv[2] if len(sys.argv) > 2 else SAIDA

    df, prob, n_linhas = DL.decodifica(ent)
    out = estrutura(df)
    b = out['barra'].to_numpy()
    buracos = int((np.diff(b) != 1).sum())

    print('=' * 70)
    print(f'ESTRUTURA  {os.path.basename(ent)}  ->  {os.path.basename(sai)}')
    print('=' * 70)
    print(f'linhas lidas: {n_linhas}   candles: {len(out)}   '
          f'barras {b[0]} a {b[-1]}   buracos: {buracos}')
    print(f"periodo: {out['data_hora'].iat[0]} a {out['data_hora'].iat[-1]}   "
          f"pregoes: {out['data'].nunique()}")
    print(f"linhas cortadas: {len(prob['cortadas'])}   campos invalidos: {len(prob['campos'])}   "
          f"linhas compactas faltando: {len(prob['seq_faltando'])}")
    corpo = (out['fechamento'] - out['abertura']).abs()
    print(f"corpo = 100 pts: {(corpo == 100).mean() * 100:.2f}% dos candles   "
          f"maxima >= max(abertura, fechamento) e minima <= min: "
          f"{((out['maxima'] >= out[['abertura', 'fechamento']].max(axis=1)) & (out['minima'] <= out[['abertura', 'fechamento']].min(axis=1))).all()}")

    c = compara_profit(out)
    if c is None:
        print('\nsem WINFUT_20PI_Agr_Tempo.csv para comparar')
    elif not c['alinhou']:
        print('\nWINFUT_20PI_Agr_Tempo.csv: nenhum trecho em comum encontrado')
    else:
        print(f"\ncomparado com WINFUT_20PI_Agr_Tempo.csv (exportacao direta do Profit):")
        print(f"  trecho em comum: {c['n']} candles, {c['de']} a {c['ate']} (a partir da barra {c['barra_ini']})")
        print(f"  OHLC + agressao + duracao identicos: {c['iguais']} de {c['n']}")
        print(f"  mesma data/hora ate o minuto: {c['hora_iguais']} de {c['n']}")

    out.to_csv(sai, index=False)
    print(f'\ngravado: {sai}  ({os.path.getsize(sai) / 1e6:.1f} MB)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
