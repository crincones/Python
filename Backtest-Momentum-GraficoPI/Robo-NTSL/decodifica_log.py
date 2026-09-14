# -*- coding: utf-8 -*-
"""
Decodifica a exportacao do console do LogCandles_Console.ntsl.

    python Robo-NTSL/decodifica_log.py <arquivo exportado> [saida.csv]

Aceita os tres modos do robo, misturados no mesmo arquivo:

  Modo 2 (compacto)  L7;B140;N20|D1260310|1513,186890,75,115,-100,11365,19501,133|...|E7
  Modo 1 (CSV)       10/03/2026;15:13;186890;186965;186775;186790;11365;19501;0,133;2000
  Modo 0 (legivel)   10/03/2026 15:13 | A 186890 | Max 186965 | Min 186775 | F 186790 | ...

A linha pode ter prefixo (hora do console, nome da automacao): o padrao
e procurado em qualquer ponto dela.

Grava um CSV com uma linha por candle, em ordem de barra:

  Barra;Data;Hora;Abertura;Maxima;Minima;Fechamento;AgressionVolBuy;AgressionVolSell;BarDurationF*1000

e confere a integridade: linhas compactas cortadas (sem o fim "E" ou
com N diferente dos candles lidos), numeros de linha faltando, barras
repetidas com valores diferentes e buracos na sequencia de barras.
Sai com codigo 1 se achar corte.
"""
import os
import re
import sys

import pandas as pd

RE_COMPACTO = re.compile(r'L(\d+);B(\d+);N(\d+)((?:\|[^|\r\n]*)*)')
RE_CSV = re.compile(r'(\d{2}/\d{2}/\d{4});(\d{2}:\d{2});(-?\d+);(-?\d+);(-?\d+);(-?\d+);'
                    r'(-?\d+);(-?\d+);([\d.,]+);(\d+)')
RE_LEGIVEL = re.compile(r'(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}) \| A ([\d.]+) \| Max ([\d.]+) \| '
                        r'Min ([\d.]+) \| F ([\d.]+)(?: \| AgrC (-?[\d.]+) \| AgrV (-?[\d.]+) \| '
                        r'Dur ([\d.,]+) min)? \| barra (\d+)')

CAMPOS = ['Barra', 'Data', 'Hora', 'Abertura', 'Maxima', 'Minima', 'Fechamento',
          'AgressionVolBuy', 'AgressionVolSell', 'BarDurationF*1000']


def _int(txt):
    """Inteiro que pode vir com separador de milhar (versoes antigas do robo)."""
    return int(txt.replace('.', ''))


def _dur1000(txt):
    """Duracao em minutos com virgula decimal -> BarDurationF*1000 inteiro."""
    return int(round(float(txt.replace('.', '').replace(',', '.')) * 1000))


def _data(d1aammdd):
    v = int(d1aammdd)
    return f'{v % 100:02d}/{v // 100 % 100:02d}/{1900 + v // 10000}'


def _hora(hhmm):
    v = int(hhmm)
    return f'{v // 100:02d}:{v % 100:02d}'


def decodifica(caminho):
    with open(caminho, encoding='utf-8', errors='replace') as f:
        linhas = f.read().splitlines()

    regs = []
    prob = dict(cortadas=[], seq_faltando=[], sem_data=[], campos=[], nao_lidas=0)
    seqs = []

    for num, txt in enumerate(linhas, 1):
        if not txt.strip():
            continue
        m = RE_COMPACTO.search(txt)
        if m:
            seq, b0, n = int(m.group(1)), int(m.group(2)), int(m.group(3))
            seqs.append(seq)
            toks = m.group(4).split('|')[1:]
            fim_ok = bool(toks) and toks[-1] == f'E{seq}'
            if fim_ok:
                toks = toks[:-1]
            data = None
            k = 0
            for tok in toks:
                if tok.startswith('D'):
                    data = tok[1:]
                    continue
                c = tok.split(',')
                if len(c) != 8 or not all(re.fullmatch(r'-?\d+', x) for x in c):
                    prob['campos'].append((num, seq, tok[:40]))
                    continue
                if data is None:
                    prob['sem_data'].append((num, seq))
                    continue
                hh, o, dh, dl, dc, ac, av, dur = (int(x) for x in c)
                regs.append(dict(Barra=b0 + k, Data=_data(data), Hora=_hora(hh),
                                 Abertura=o, Maxima=o + dh, Minima=o - dl, Fechamento=o + dc,
                                 AgressionVolBuy=ac, AgressionVolSell=av,
                                 **{'BarDurationF*1000': dur}, _linha=num))
                k += 1
            if not fim_ok or k != n:
                prob['cortadas'].append((num, seq, n, k, fim_ok))
            continue

        m = RE_CSV.search(txt)
        if m:
            g = m.groups()
            regs.append(dict(Barra=int(g[9]), Data=g[0], Hora=g[1], Abertura=_int(g[2]),
                             Maxima=_int(g[3]), Minima=_int(g[4]), Fechamento=_int(g[5]),
                             AgressionVolBuy=_int(g[6]), AgressionVolSell=_int(g[7]),
                             **{'BarDurationF*1000': _dur1000(g[8])}, _linha=num))
            continue

        m = RE_LEGIVEL.search(txt)
        if m:
            g = m.groups()
            regs.append(dict(Barra=int(g[9]), Data=g[0], Hora=g[1], Abertura=_int(g[2]),
                             Maxima=_int(g[3]), Minima=_int(g[4]), Fechamento=_int(g[5]),
                             AgressionVolBuy=_int(g[6]) if g[6] else None,
                             AgressionVolSell=_int(g[7]) if g[7] else None,
                             **{'BarDurationF*1000': _dur1000(g[8]) if g[8] else None},
                             _linha=num))
            continue

        if not txt.startswith('Data;Hora;'):
            prob['nao_lidas'] += 1

    if seqs:
        s = sorted(set(seqs))
        prob['seq_faltando'] = sorted(set(range(s[0], s[-1] + 1)) - set(s))

    df = pd.DataFrame(regs, columns=CAMPOS + ['_linha'])
    return df, prob, len(linhas)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    ent = sys.argv[1]
    sai = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(ent)[0] + '_decod.csv'

    df, prob, n_linhas = decodifica(ent)
    print('=' * 70)
    print(f'DECODIFICA  {os.path.basename(ent)}')
    print('=' * 70)
    print(f'linhas no arquivo: {n_linhas}   candles lidos: {len(df)}')

    # repetidas: iguais sao descartadas; diferentes sao problema
    cols = [c for c in CAMPOS if c != 'Barra']
    dup = df[df.duplicated('Barra', keep=False)]
    conflito = dup.groupby('Barra').apply(lambda g: len(g[cols].drop_duplicates()) > 1,
                                          include_groups=False) if len(dup) else pd.Series(dtype=bool)
    n_conf = int(conflito.sum()) if len(conflito) else 0
    df = df.drop_duplicates('Barra', keep='first').sort_values('Barra').reset_index(drop=True)

    buracos = []
    if len(df):
        b = df['Barra'].to_numpy()
        for x, y in zip(b[:-1], b[1:]):
            if y != x + 1:
                buracos.append((int(x), int(y)))

    print(f'candles unicos: {len(df)}', end='')
    if len(df):
        print(f"   barras {df['Barra'].iat[0]} a {df['Barra'].iat[-1]}   "
              f"{df['Data'].iat[0]} {df['Hora'].iat[0]} a {df['Data'].iat[-1]} {df['Hora'].iat[-1]}")
    else:
        print()
    print(f"linhas compactas cortadas: {len(prob['cortadas'])}")
    for num, seq, n, k, fim in prob['cortadas'][:10]:
        print(f"    linha {num} (L{seq}): N={n}, lidos={k}, fim 'E' {'ok' if fim else 'AUSENTE'}")
    print(f"numeros de linha compacta faltando: {len(prob['seq_faltando'])}"
          + (f"  {prob['seq_faltando'][:10]}" if prob['seq_faltando'] else ''))
    print(f"candles com campos invalidos: {len(prob['campos'])}   sem data: {len(prob['sem_data'])}")
    print(f"barras repetidas: {len(dup)} registros, {n_conf} com valores DIFERENTES")
    print(f"buracos na sequencia de barras: {len(buracos)}"
          + (f"  {buracos[:10]}" if buracos else ''))
    print(f"linhas ignoradas (nao sao do robo): {prob['nao_lidas']}")

    df[CAMPOS].to_csv(sai, sep=';', index=False)
    print(f'\ngravado: {sai}')

    corte = bool(prob['cortadas'] or prob['campos'] or prob['seq_faltando'])
    if corte:
        print('\nATENCAO: ha linhas cortadas ou faltando. Se o corte for no FIM das linhas,')
        print('o texto passou do limite do ConsoleLog: diminua RegistrosPorLinha.')
    return 1 if corte else 0


if __name__ == '__main__':
    sys.exit(main())
