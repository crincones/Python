# -*- coding: utf-8 -*-
"""Roda todos os setups sobre a base completa e grava os resultados."""
import os
import json
import csv
import collections
import engine as E

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


def contexto(barras, diario, validos):
    """Pre-computa niveis de cada pregao valido."""
    ctx = {}
    ordem_total = sorted(barras)
    idx = {d: i for i, d in enumerate(ordem_total)}
    for d in validos:
        b = barras[d]
        ab = b[0][1]
        aj = diario[d]['ajuste']
        ant = ordem_total[idx[d] - 1]
        pv = E.pivos(diario, ant, ab)
        lo = min(min(x[3] for x in b), aj, min(p for _, p in pv))
        hi = max(max(x[2] for x in b), aj, max(p for _, p in pv))
        bl = E.bolas(lo, hi)
        ctx[d] = dict(ab=ab, aj=aj, pivos=pv, bolas=bl,
                      fund=E.funde(pv + bl, aj))
    return ctx


def roda(barras, ctx, validos, ema=None, **kw):
    """Executa os setups e devolve dict setup -> lista de trades (com a data)."""
    otim = kw.get('otimista', False)
    stop = kw.get('stop', E.STOP)
    alvo_fixo = kw.get('alvo_fixo', E.ALVO_FIXO)
    alvo_ajuste = kw.get('alvo_ajuste', E.ALVO_NO_AJUSTE)
    a_alvo_ajuste = kw.get('a_alvo_ajuste', False)
    uma = kw.get('uma_posicao', False)
    dist_min = kw.get('dist_min', E.DIST_MIN)
    retracao = kw.get('retracao', E.RETRACAO)
    cruza = kw.get('cruza', E.CRUZA_AJ)
    parcial = kw.get('parcial', None)
    regime = kw.get('regime_exclusivo', None)
    alvo_ema5 = kw.get('alvo_ema5', False)
    fav = kw.get('favoravel_na_entrada', None)
    setups = kw.get('setups', ('A', 'B', 'C', 'D', 'CD'))
    if fav is not None:
        antes = E.FAVORAVEL_NA_ENTRADA
        E.FAVORAVEL_NA_ENTRADA = fav
    try:
        return _roda(barras, ctx, validos, ema, otim, stop, alvo_fixo, alvo_ajuste,
                     a_alvo_ajuste, uma, dist_min, retracao, cruza, parcial, regime,
                     alvo_ema5, setups)
    finally:
        if fav is not None:
            E.FAVORAVEL_NA_ENTRADA = antes


def _roda(barras, ctx, validos, ema, otim, stop, alvo_fixo, alvo_ajuste,
          a_alvo_ajuste, uma, dist_min, retracao, cruza, parcial, regime,
          alvo_ema5, setups):
    out = collections.defaultdict(list)

    for d in validos:
        b, c = barras[d], ctx[d]
        em = ema[d] if ema else None
        if 'A' in setups:
            for t in E.setup_A(b, c['aj'], stop=stop, alvo=alvo_fixo, otimista=otim,
                               alvo_ajuste=a_alvo_ajuste, parcial=parcial,
                               ema=em, alvo_ema5=alvo_ema5):
                t['dia'] = d
                out['A'].append(t)
        if 'B' in setups:
            for t in E.setup_B(b, c['aj'], stop=stop, alvo=alvo_fixo, otimista=otim,
                               parcial=parcial, ema=em, alvo_ema5=alvo_ema5):
                t['dia'] = d
                out['B'].append(t)
        for tag, niveis in (('C', c['pivos']), ('D', c['bolas']), ('CD', c['fund'])):
            if tag not in setups:
                continue
            for t in E.setup_niveis(b, c['aj'], niveis, tag, stop=stop,
                                    alvo_ajuste=alvo_ajuste, alvo_fixo=alvo_fixo,
                                    dist_min=dist_min, retracao=retracao, cruza=cruza,
                                    otimista=otim, uma_posicao=uma, parcial=parcial,
                                    regime_exclusivo=regime, ema=em, alvo_ema5=alvo_ema5):
                t['dia'] = d
                out[tag].append(t)
    return out


NOMES = {
    'A':  'A  - retorno a abertura (1 tick)',
    'B':  'B  - trade seco no ajuste',
    'C':  'C  - pivos -> ajuste',
    'D':  'D  - bolas (mult. 1000) -> ajuste',
    'CD': 'CD - pivos + bolas (fusao 300)',
}
CHAVES = ('A', 'B', 'C', 'D', 'CD')
LARG = 126


def tabela(res, ndias, titulo):
    print('')
    print('=' * LARG)
    print(titulo)
    print('=' * LARG)
    print(E.CAB)
    print('-' * LARG)
    saida = {}
    for k in CHAVES:
        m = E.metricas(res.get(k, []), ndias)
        saida[k] = m
        print(E.linha_metricas(NOMES[k], m))
    return saida


def por_ano(trades):
    ac = collections.defaultdict(lambda: [0.0, 0])
    for t in trades:
        y = t['dia'][:4]
        ac[y][0] += t['pts']
        ac[y][1] += 1
    return ac


def main():
    os.makedirs(SAIDA, exist_ok=True)
    barras, diario, ordem = E.carrega()
    validos, desc = E.dias_validos(barras, diario, ordem)
    ctx = contexto(barras, diario, validos)
    print('calculando EMA%d de M5 e M60...' % E.EMA_PER)
    ema = E.medias(barras, ordem)
    nd = len(validos)

    print('')
    print('BACKTEST - ESTRATEGIA DO AJUSTE (WINFUT)')
    print('Base M1 ........... %s  (%s a %s)' % (os.path.basename(E.M1_CSV), ordem[0], ordem[-1]))
    print('Pregoes no arquivo  %d | validos %d | descartados %d' % (len(ordem), nd, len(desc)))
    cont = collections.Counter(m.split(' (')[0] for _, m in desc)
    for k, v in cont.most_common():
        print('   descarte: %-45s %d' % (k, v))
    print('Lote .............. %d contratos (pts por contrato; R$ do lote)' % E.CONTRATOS)
    print('Gestao ............ stop %.0f | parcial %d de %d em +%.0f | stop do resto %s (%+.0f) | alvo %s'
          % (E.STOP, E.contratos_parcial(), E.CONTRATOS, E.PARCIAL_PTS,
             'no MEDIO da operacao' if E.PARCIAL_STOP == 'medio' else 'fixo', E.stop_resto(),
             'AJUSTE (C/D/CD)' if E.ALVO_NO_AJUSTE else '%.0f fixos' % E.ALVO_FIXO))
    print('                    ganho maximo = %.0f%%x%.0f + %.0f%%x500 = %.1f pts -> %.2f:1 vs stop %.0f'
          % (100 * E.PARCIAL_FRAC, E.PARCIAL_PTS, 100 * (1 - E.PARCIAL_FRAC),
             E.PARCIAL_FRAC * E.PARCIAL_PTS + (1 - E.PARCIAL_FRAC) * 500,
             (E.PARCIAL_FRAC * E.PARCIAL_PTS + (1 - E.PARCIAL_FRAC) * 500) / E.STOP, E.STOP))
    print('Regime ............ %s' % ('EXCLUSIVO (ao cruzar o ajuste em %.0f pts o lado inicial desliga)' % E.CRUZA_AJ
                                      if E.REGIME_EXCLUSIVO else 'os dois lados podem ficar ativos'))
    print('Niveis ............ dist.min %.0f | retracao %.0f | fusao %.0f | fibs %s'
          % (E.DIST_MIN, E.RETRACAO, E.FUSAO, list(E.FIBS)))

    # ---- validacao do ajuste vs call de fechamento
    print('')
    print('-' * LARG)
    print('VALIDACAO DO AJUSTE CONTRA O CALL DE FECHAMENTO DO DIA ANTERIOR (ESTRATEGIA.md 2.2)')
    print('-' * LARG)
    for jan in (('17:00', '17:15'), ('17:00', '17:30'), ('17:00', '18:00')):
        dentro = fora = 0
        desvios = []
        prev = None
        for d in ordem:
            if prev is not None:
                dv = E.desvio_ajuste(barras, prev, diario[d]['ajuste'], jan)
                if dv is not None:
                    if dv == 0:
                        dentro += 1
                    else:
                        fora += 1
                        desvios.append(dv)
            prev = d
        desvios.sort()
        med = desvios[len(desvios) // 2] if desvios else 0
        print('  janela %s-%s : dentro %4d (%.1f%%) | fora %3d | desvio mediano das falhas %4.0f pts'
              % (jan[0], jan[1], dentro, 100.0 * dentro / (dentro + fora), fora, med))
    print('  -> a janela 17:00-17:15 do spec e estreita demais; 17:00-18:00 valida 96,7%%.')
    print('     Filtro aplicado: descarta o dia se o desvio passar de %.0f pts.' % E.AJ_TOL)

    gaps = sorted(abs(ctx[d]['ab'] - ctx[d]['aj']) for d in validos)
    print('')
    print('Gap |abertura-ajuste|: mediana %.0f | p25 %.0f | p75 %.0f | p95 %.0f'
          % (gaps[len(gaps) // 2], gaps[len(gaps) // 4], gaps[3 * len(gaps) // 4], gaps[int(0.95 * len(gaps))]))
    print('Dias com gap >= %.0f: %d (%.0f%%)'
          % (E.DIST_MIN, sum(1 for g in gaps if g >= E.DIST_MIN),
             100.0 * sum(1 for g in gaps if g >= E.DIST_MIN) / nd))

    # ------------------------------------------------------------- rodadas
    base = roda(barras, ctx, validos, ema)
    tabela(base, nd, 'PRINCIPAL - spec vigente: stop 100 + parcial 2/3 em +45 com stop do resto no medio,'
                     ' regime exclusivo, alvo 500 fixo')

    fav = roda(barras, ctx, validos, ema, favoravel_na_entrada=True)
    tabela(fav, nd, 'CREDITANDO A BARRA DE ENTRADA - parcial/alvo podem sair na propria barra do toque'
                    ' (ARTEFATO: 93% das parciais caem aqui)')

    otm = roda(barras, ctx, validos, ema, otimista=True, favoravel_na_entrada=True)
    tabela(otm, nd, 'LIMITE OTIMISTA - barra de entrada creditada E alvo ganha o empate (teto absoluto)')

    semp = roda(barras, ctx, validos, ema, parcial=False)
    tabela(semp, nd, 'SEM A PARCIAL - stop 100 seco ate o alvo (spec anterior, para medir o efeito da parcial)')

    frac_orig = E.PARCIAL_FRAC
    E.PARCIAL_FRAC = 0.5
    try:
        p50 = roda(barras, ctx, validos, ema)
        tabela(p50, nd, 'PARCIAL DE 50%% (%d de %d contratos) em +%.0f, stop do resto no medio (%+.0f)'
               % (E.contratos_parcial(), E.CONTRATOS, E.PARCIAL_PTS, E.stop_resto()))
    finally:
        E.PARCIAL_FRAC = frac_orig

    ambos = roda(barras, ctx, validos, ema, regime_exclusivo=False)
    tabela(ambos, nd, 'REGIME NAO EXCLUSIVO - os dois lados seguem ativos apos cruzar o ajuste')

    aaj = roda(barras, ctx, validos, ema, a_alvo_ajuste=True, setups=('A',))
    print('')
    print('SETUP A com alvo no AJUSTE em vez de 500 fixos (ESTRATEGIA.md 6):')
    print(E.CAB)
    print(E.linha_metricas(NOMES['A'], E.metricas(aaj['A'], nd)))

    ema5 = roda(barras, ctx, validos, ema, alvo_ema5=True)
    tabela(ema5, nd, 'PREMISSA DAS MEDIAS - alvo na EMA21 de M5 em vez do alvo fixo (ESTRATEGIA.md 1)')

    aju = roda(barras, ctx, validos, ema, alvo_ajuste=True)
    tabela(aju, nd, 'ALVO NO AJUSTE PARA C/D/CD (spec anterior; A e B seguem com 500 fixos)')

    uma = roda(barras, ctx, validos, ema, uma_posicao=True)
    tabela(uma, nd, 'UMA POSICAO POR VEZ (sem sobreposicao de trades no mesmo dia)')

    # ---- por ano
    anos = sorted({d[:4] for d in validos})
    print('')
    print('=' * LARG)
    print('RESULTADO POR ANO (configuracao principal, em pontos)')
    print('=' * LARG)
    print('%-34s %s' % ('SETUP', ''.join('%12s' % a for a in anos)))
    for k in CHAVES:
        pa = por_ano(base.get(k, []))
        print('%-34s %s' % (NOMES[k], ''.join('%+12.0f' % pa[a][0] for a in anos)))
    print('%-34s %s' % ('(pregoes validos no ano)',
                        ''.join('%12d' % sum(1 for d in validos if d[:4] == a) for a in anos)))

    # ---- CD por tipo e distancia
    print('')
    print('=' * LARG)
    print('SETUP CD - por tipo de nivel e por distancia do ajuste')
    print('=' * LARG)
    cd = base['CD']
    porTipo = collections.defaultdict(list)
    for t in cd:
        porTipo['bola' if t['nivel'].startswith('B') else 'pivo ' + t['nivel'][:2]].append(t['pts'])
    print('%-14s %8s %10s %10s' % ('TIPO', 'TRADES', 'PTS', 'PTS/TRADE'))
    for k in sorted(porTipo):
        v = porTipo[k]
        print('%-14s %8d %+10.0f %+10.1f' % (k, len(v), sum(v), sum(v) / len(v)))

    print('')
    print('%-16s %8s %10s %10s %9s' % ('DIST. AJUSTE', 'TRADES', 'PTS', 'PTS/TRADE', 'ACERTO'))
    faixas = [(600, 900), (900, 1200), (1200, 1600), (1600, 2200), (2200, 99999)]
    cd_dist = []
    for a, b_ in faixas:
        v = [t for t in cd if a <= t['dist_ajuste'] < b_]
        if not v:
            continue
        s = sum(t['pts'] for t in v)
        ac = 100.0 * sum(1 for t in v if t['pts'] > 0) / len(v)
        rot = '%d-%d' % (a, b_) if b_ < 99999 else '%d+' % a
        cd_dist.append([rot, len(v), s, ac])
        print('%-16s %8d %+10.0f %+10.1f %8.1f%%' % (rot, len(v), s, s / len(v), ac))

    # ---- premissa das medias: distancia da EMA21 M60 na entrada
    print('')
    print('=' * LARG)
    print('PREMISSA DAS MEDIAS - resultado do CD por distancia da EMA21 de M60 na entrada')
    print('=' * LARG)
    faixas_e = [(0, 300), (300, 600), (600, 1000), (1000, 1500), (1500, 99999)]
    print('%-16s %8s %10s %10s %9s' % ('DIST. EMA60', 'TRADES', 'PTS', 'PTS/TRADE', 'ACERTO'))
    cd_ema = []
    for a, b_ in faixas_e:
        v = []
        for t in cd:
            e60 = ema[t['dia']][t['i']][1]
            if e60 is None:
                continue
            if a <= abs(t['entrada'] - e60) < b_:
                v.append(t)
        if not v:
            continue
        s = sum(t['pts'] for t in v)
        ac = 100.0 * sum(1 for t in v if t['pts'] > 0) / len(v)
        rot = '%d-%d' % (a, b_) if b_ < 99999 else '%d+' % a
        cd_ema.append([rot, len(v), s, ac])
        print('%-16s %8d %+10.0f %+10.1f %8.1f%%' % (rot, len(v), s, s / len(v), ac))

    # ---- sensibilidades
    print('')
    print('=' * LARG)
    print('SENSIBILIDADE DO STOP (alvo 500 fixo, stop do resto no medio)')
    print('=' * LARG)
    stops = [100, 150, 200, 300, 500]
    sens = {k: [] for k in CHAVES}
    for s in stops:
        r = roda(barras, ctx, validos, ema, stop=float(s))
        for k in CHAVES:
            m = E.metricas(r.get(k, []), nd)
            sens[k].append(m['total'] if m else 0.0)
    print('%-34s %s' % ('SETUP', ''.join('%12s' % ('stop %d' % s) for s in stops)))
    for k in CHAVES:
        print('%-34s %s' % (NOMES[k], ''.join('%+12.0f' % x for x in sens[k])))

    print('')
    print('=' * LARG)
    print('SENSIBILIDADE DA PARCIAL (setup CD, stop 100, alvo 500 fixo)')
    print('=' * LARG)
    print('%-34s %8s %10s %10s %9s' % ('PARCIAL', 'TRADES', 'PTS', 'PTS/TRADE', 'ACERTO'))
    orig = (E.USA_PARCIAL, E.PARCIAL_FRAC, E.PARCIAL_PTS, E.PARCIAL_STOP)
    # so fracoes realizaveis no lote de CONTRATOS (1/2 e 2/3 com 6)
    cfgs = [(False, 2.0 / 3, 45, 'medio'), (True, 0.5, 45, 'medio'), (True, 2.0 / 3, 45, 'medio'),
            (True, 2.0 / 3, 45, 0), (True, 2.0 / 3, 45, 45), (True, 0.5, 100, 'medio'),
            (True, 2.0 / 3, 100, 'medio')]
    sens_p = []
    for usa, fr, pt, ps in cfgs:
        E.USA_PARCIAL, E.PARCIAL_FRAC, E.PARCIAL_PTS, E.PARCIAL_STOP = usa, fr, pt, ps
        r = roda(barras, ctx, validos, ema, setups=('CD',))
        m = E.metricas(r['CD'], nd)
        if not usa:
            rot = 'sem parcial'
        else:
            rot = '%d/%d em +%.0f, stop %s (%+.0f)' % (
                E.contratos_parcial(), E.CONTRATOS, pt, 'no medio' if ps == 'medio' else 'fixo',
                E.stop_resto())
        sens_p.append([rot, m['n'], m['total'], m['acerto']])
        print('%-34s %8d %+10.0f %+10.1f %8.1f%%' % (rot, m['n'], m['total'], m['media'], m['acerto']))
    E.USA_PARCIAL, E.PARCIAL_FRAC, E.PARCIAL_PTS, E.PARCIAL_STOP = orig

    print('')
    print('=' * LARG)
    print('EFEITO DA REGRA DE INVALIDACAO POR RETRACAO (setup CD)')
    print('=' * LARG)
    print('%-16s %8s %10s %10s %9s' % ('RETRACAO', 'TRADES', 'PTS', 'PTS/TRADE', 'ACERTO'))
    for rt in (300, 500, 800, 1200, 999999):
        r = roda(barras, ctx, validos, ema, retracao=float(rt), setups=('CD',))
        m = E.metricas(r['CD'], nd)
        rot = 'sem regra' if rt > 99999 else '%d pts' % rt
        print('%-16s %8d %+10.0f %+10.1f %8.1f%%' % (rot, m['n'], m['total'], m['media'], m['acerto']))

    # ---- dump
    dump = dict(
        periodo=[ordem[0], ordem[-1]], ndias=nd, ntotal=len(ordem),
        descartes=cont.most_common(),
        gaps=dict(mediana=gaps[len(gaps) // 2], p25=gaps[len(gaps) // 4],
                  p75=gaps[3 * len(gaps) // 4], p95=gaps[int(0.95 * len(gaps))]),
        principal={k: E.metricas(base.get(k, []), nd) for k in CHAVES},
        otimista={k: E.metricas(otm.get(k, []), nd) for k in CHAVES},
        sem_parcial={k: E.metricas(semp.get(k, []), nd) for k in CHAVES},
        parcial_50={k: E.metricas(p50.get(k, []), nd) for k in CHAVES},
        contratos=E.CONTRATOS,
        regime_ambos={k: E.metricas(ambos.get(k, []), nd) for k in CHAVES},
        alvo_ema5={k: E.metricas(ema5.get(k, []), nd) for k in CHAVES},
        alvo_ajuste={k: E.metricas(aju.get(k, []), nd) for k in CHAVES},
        uma_posicao={k: E.metricas(uma.get(k, []), nd) for k in CHAVES},
        a_alvo_ajuste=E.metricas(aaj['A'], nd),
        por_ano={k: {a: por_ano(base.get(k, []))[a] for a in anos} for k in CHAVES},
        anos=anos, pregoes_ano={a: sum(1 for d in validos if d[:4] == a) for a in anos},
        sens_stop=dict(stops=stops, dados=sens),
        sens_parcial=sens_p,
        cd_por_tipo={k: [len(v), sum(v)] for k, v in porTipo.items()},
        cd_por_dist=cd_dist, cd_por_ema=cd_ema,
    )
    with open(os.path.join(SAIDA, 'resumo.json'), 'w', encoding='utf-8') as f:
        json.dump(dump, f, indent=1, ensure_ascii=False, default=float)

    for k, tr in base.items():
        with open(os.path.join(SAIDA, 'trades_%s.csv' % k), 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(['data', 'setup', 'nivel', 'lado', 'entrada', 'hora', 'saida', 'motivo', 'pts'])
            for t in tr:
                w.writerow([t['dia'], t['setup'], t['nivel'], 'COMPRA' if t['lado'] > 0 else 'VENDA',
                            '%.0f' % t['entrada'], t['hora'], t['hora_saida'], t['motivo'], '%.2f' % t['pts']])
    print('')
    print('Gravado em %s (resumo.json + trades_*.csv)' % SAIDA)


if __name__ == '__main__':
    main()
