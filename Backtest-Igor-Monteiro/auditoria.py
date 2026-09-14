# -*- coding: utf-8 -*-
"""
Auditoria da engine:
  1. dump detalhado de um pregao (niveis, gatilhos, invalidacoes, trades)
  2. teste da premissa: depois de tocar o nivel, o preco chega ao ajuste?
  3. MAE: quanto o preco anda contra antes de voltar
"""
import sys
import os
import collections
import engine as E
import rodar as R


def dump_dia(barras, diario, ctx, d):
    b, c = barras[d], ctx[d]
    aj, ab = c['aj'], c['ab']
    lado = 'COMPRA' if ab < aj else 'VENDA'
    hi = max(x[2] for x in b)
    lo = min(x[3] for x in b)
    print('=' * 90)
    print('PREGAO %s   abertura %.0f   ajuste %.0f   gap %+.0f   vies %s'
          % (d, ab, aj, ab - aj, lado))
    print('range do dia: %.0f - %.0f   (%d barras, %s a %s)' % (lo, hi, len(b), b[0][0], b[-1][0]))
    print('-' * 90)
    print('%-8s %10s %10s %8s   %s' % ('NIVEL', 'PRECO', 'D.AJUSTE', 'LADO', 'STATUS'))
    fund = dict(c['fund'])
    todos = sorted(set(c['pivos'] + c['bolas']), key=lambda x: -x[1])
    for nome, px in todos:
        d_aj = px - aj
        if abs(d_aj) < E.DIST_MIN:
            st = 'descartado: a %.0f do ajuste (< %.0f)' % (abs(d_aj), E.DIST_MIN)
            ld = '-'
        elif nome not in fund:
            st = 'descartado pela fusao de %.0f pts (existe vizinho mais afastado)' % E.FUSAO
            ld = '-'
        else:
            ld = 'COMPRA' if d_aj < 0 else 'VENDA'
            tocou = lo <= px <= hi
            st = 'candidato (%s)' % ('preco alcancou' if tocou else 'preco nao alcancou')
        print('%-8s %10.0f %+10.0f %8s   %s' % (nome, px, d_aj, ld, st))

    print('-' * 90)
    for tag, niveis in (('C', c['pivos']), ('D', c['bolas']), ('CD', c['fund'])):
        tr = E.setup_niveis(b, aj, niveis, tag)
        print('SETUP %-3s %d trade(s)' % (tag, len(tr)))
        for t in tr:
            print('   %s %-6s nivel %-6s @%.0f -> %s as %s : %+.0f pts (alvo %.0f, stop %.0f)'
                  % (t['hora'], 'COMPRA' if t['lado'] > 0 else 'VENDA', t['nivel'], t['entrada'],
                     t['motivo'], t['hora_saida'], t['pts'], t['alvo'],
                     t['entrada'] - E.STOP if t['lado'] > 0 else t['entrada'] + E.STOP))
    print('')


def premissa(barras, ctx, validos):
    """Sem stop: depois de entrar no nivel, o preco chega ao ajuste no mesmo dia?"""
    chega = 0
    total = 0
    maes = []
    tempo = []
    for d in validos:
        b, c = barras[d], ctx[d]
        aj = c['aj']
        for t in E.setup_niveis(b, aj, c['fund'], 'CD', stop=1e9, parcial=False, alvo_ajuste=True):
            total += 1
            if t['motivo'] == 'ALVO':
                chega += 1
            # MAE ate o desfecho
            i0 = next(i for i, x in enumerate(b) if x[0] == t['hora'])
            mae = 0.0
            for j in range(i0, len(b)):
                hm, o, h, l, cl = b[j]
                mae = max(mae, (t['entrada'] - l) if t['lado'] > 0 else (h - t['entrada']))
                atingiu = (h >= aj) if t['lado'] > 0 else (l <= aj)
                if atingiu:
                    tempo.append(j - i0)
                    break
            maes.append(mae)
    maes.sort()
    tempo.sort()
    print('=' * 90)
    print('PREMISSA: o preco volta ao ajuste depois de tocar o nivel? (setup CD, SEM stop)')
    print('=' * 90)
    print('  entradas ............................ %d' % total)
    print('  chegaram ao ajuste no mesmo pregao .. %d (%.1f%%)' % (chega, 100.0 * chega / total))
    print('  MAE (quanto anda contra antes disso):')
    for p in (25, 50, 75, 90, 95):
        print('     p%-3d %6.0f pts' % (p, maes[int((len(maes) - 1) * p / 100)]))
    for s in (100, 150, 200, 300, 500, 800):
        n = sum(1 for m in maes if m >= s)
        print('     stop de %4d pts seria acionado em %5.1f%% das entradas' % (s, 100.0 * n / len(maes)))
    if tempo:
        print('  tempo ate o ajuste (minutos): mediana %d | p75 %d | p90 %d'
              % (tempo[len(tempo) // 2], tempo[3 * len(tempo) // 4], tempo[int(len(tempo) * 0.9)]))

    # matriz stop x resultado, alvo sempre no ajuste
    print('')
    print('  Resultado do setup CD por stop, alvo sempre no ajuste (pts totais):')
    for s in (100, 150, 200, 300, 500, 800, 1200):
        tot = 0.0
        n = 0
        for d in validos:
            b, c = barras[d], ctx[d]
            for t in E.setup_niveis(b, c['aj'], c['fund'], 'CD', stop=float(s), parcial=False,
                                    alvo_ajuste=True):
                tot += t['pts']
                n += 1
        print('     stop %4d -> %+9.0f pts em %d trades (%.1f pts/trade)' % (s, tot, n, tot / n))


def main():
    barras, diario, ordem = E.carrega()
    validos, desc = E.dias_validos(barras, diario, ordem)
    ctx = R.contexto(barras, diario, validos)

    if len(sys.argv) > 1 and sys.argv[1] == 'premissa':
        premissa(barras, ctx, validos)
        return

    if len(sys.argv) > 1:
        for d in sys.argv[1:]:
            if d in ctx:
                dump_dia(barras, diario, ctx, d)
            else:
                print('%s nao e pregao valido' % d)
        return

    # sem argumento: 3 dias de gap grande com trades
    cands = sorted(validos, key=lambda d: -abs(ctx[d]['ab'] - ctx[d]['aj']))
    for d in cands[:2]:
        dump_dia(barras, diario, ctx, d)
    for d in validos[-1:]:
        dump_dia(barras, diario, ctx, d)


if __name__ == '__main__':
    main()
