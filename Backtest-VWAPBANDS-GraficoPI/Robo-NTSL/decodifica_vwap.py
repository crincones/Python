# -*- coding: utf-8 -*-
"""
Decodifica a exportacao do console do LogVWAP_Console.ntsl.

    python Robo-NTSL/decodifica_vwap.py <arquivo exportado> [saida.csv]

Aceita os modos 2 (compacto) e 1 (CSV), misturados e com prefixo de console.
Grava um CSV por candle no formato do WINFUT_20PI_Robo.csv, com tres colunas a mais:

  vol_fin      volume financeiro do candle (R$, precisao de R$ 1.000)
  quantidade   contratos negociados no candle
  preco_medio  Volume / Quantity (o "Media financeira" antes do multiplicador)

e confere: linhas cortadas, numeros de linha faltando, barras repetidas e buracos.
Sai com codigo 1 se achar corte.
"""
import os
import re
import sys

import pandas as pd

RE_COMPACTO = re.compile(r'L(\d+);B(\d+);N(\d+)((?:\|[^|\r\n]*)*)')
RE_CSV = re.compile(r'(\d{2}/\d{2}/\d{4});(\d{2}:\d{2});(-?\d+);(-?\d+);(-?\d+);(-?\d+);'
                    r'(-?\d+);(-?\d+);([\d.,]+);(-?\d+);(-?\d+);(-?\d+);(\d+)')


def _int(t):
    return int(t.replace('.', ''))


def decodifica(caminho):
    linhas = open(caminho, encoding='utf-8', errors='replace').read().splitlines()
    regs = {}
    cortadas = []; seqs = []
    for num, txt in enumerate(linhas, 1):
        m = RE_COMPACTO.search(txt)
        if m:
            seq, b0, n = int(m.group(1)), int(m.group(2)), int(m.group(3))
            seqs.append(seq)
            toks = m.group(4).split('|')[1:]
            fim_ok = bool(toks) and toks[-1] == f'E{seq}'
            if fim_ok:
                toks = toks[:-1]
            data = None; b = b0; lidos = 0
            for t in toks:
                if t.startswith('D'):
                    data = int(t[1:]); continue
                p = t.split(',')
                if len(p) != 11 or data is None:
                    continue
                v = [int(x) for x in p]
                hh = v[0]; o = v[1]
                regs[b] = dict(barra=b, data=f'{1900 + data // 10000}-{data // 100 % 100:02d}-{data % 100:02d}',
                               hora=f'{hh // 100:02d}:{hh % 100:02d}', abertura=o, maxima=o + v[2], minima=o - v[3],
                               fechamento=o + v[4], agr_compra=v[5], agr_venda=v[6], duracao_s=v[7] * 60 / 1000,
                               vol_fin=v[8] * 1000, quantidade=v[9], preco_medio=v[10] / 100)
                b += 1; lidos += 1
            if not fim_ok or lidos != n:
                cortadas.append((num, seq, n, lidos))
            continue
        m = RE_CSV.search(txt)
        if m:
            g = m.groups()
            d, mth, y = g[0].split('/')
            b = int(g[12])
            regs[b] = dict(barra=b, data=f'{y}-{mth}-{d}', hora=g[1], abertura=_int(g[2]), maxima=_int(g[3]),
                           minima=_int(g[4]), fechamento=_int(g[5]), agr_compra=_int(g[6]), agr_venda=_int(g[7]),
                           duracao_s=float(g[8].replace('.', '').replace(',', '.')) * 60,
                           vol_fin=_int(g[9]) * 1000, quantidade=_int(g[10]), preco_medio=_int(g[11]) / 100)
    df = pd.DataFrame(sorted(regs.values(), key=lambda r: r['barra']))
    return df, cortadas, seqs


def main():
    ent = sys.argv[1]
    sai = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(ent)[0] + '_decod.csv'
    df, cortadas, seqs = decodifica(ent)
    if df.empty:
        print('nenhum candle reconhecido'); sys.exit(1)
    df['data_hora'] = df['data'] + ' ' + df['hora']
    df['agr_saldo'] = df['agr_compra'] - df['agr_venda']
    df['duracao_min'] = df['duracao_s'] / 60
    cols = ['barra', 'data_hora', 'data', 'hora', 'abertura', 'maxima', 'minima', 'fechamento', 'agr_compra',
            'agr_venda', 'agr_saldo', 'duracao_min', 'duracao_s', 'vol_fin', 'quantidade', 'preco_medio']
    df[cols].to_csv(sai, index=False)
    falta = sorted(set(range(min(seqs), max(seqs) + 1)) - set(seqs)) if seqs else []
    buracos = int((df['barra'].diff().dropna() != 1).sum())
    print(f'{len(df)} candles, {df["data"].nunique()} pregoes, {df["data"].min()} a {df["data"].max()} -> {sai}')
    print(f'linhas cortadas: {len(cortadas)} | numeros de linha faltando: {len(falta)} | buracos de barra: {buracos}')
    q = df['quantidade']; a = df['agr_compra'] + df['agr_venda']
    print(f'quantidade x (agr compra + venda): mediana da razao {float((q / a.where(a > 0)).median()):.3f}')
    for c in cortadas[:10]:
        print('  cortada: linha do arquivo %d, L%d, N%d, lidos %d' % c)
    sys.exit(1 if cortadas else 0)


if __name__ == '__main__':
    main()
