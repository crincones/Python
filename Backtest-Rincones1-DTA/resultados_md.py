# -*- coding: utf-8 -*-
"""
Gera RESULTADOS.md a partir do MESMO contexto que alimenta o relatorio.html.

Nao ha numero escrito a mao aqui: tudo vem de saida/resumo.json, via o
contexto montado em relatorio.py. As frases de conclusao sao as mesmas do
HTML -- cada veredito devolve markdown e html do mesmo calculo.
"""
BASES = ('WINV26', 'WINFUT')

CAB = ('| | n | /pregão | EV | R | total | acerto | t | dias+ | PF | DD |\n'
       '|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|')


def gera(ctx, F, ROT_SU):
    R = ctx['R']
    P = R['parametros']
    n1, n2, t2, p1, p0, f2, d0, mil, vg = (F['n1'], F['n2'], F['t2'], F['p1'],
                                           F['p0'], F['f2'], F['d0'], F['mil'],
                                           F['vg'])
    nivel_rot = F['nivel_rot']
    at = R['nivel']['atual']

    def linha(rot, m):
        if not m:
            return '| %s | — | — | — | — | — | — | — | — | — | — |' % rot
        return ('| %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |'
                % (rot, m['n'], vg('%.1f' % m['por_pregao']), n1(m['ev']),
                   n2(m.get('ev_r')), mil(m['total']), p1(m['acerto']),
                   t2(m['t']), p0(m['dias_pos']), f2(m['pf']), d0(m['dd'])))

    L = []
    w = L.append

    w('# Resultados — Backtest-Rincones1-DTA')
    w('')
    w('> **Gerado por `python rodar.py && python relatorio.py`.** Não edite à mão: '
      'todo número aqui sai de `saida/resumo.json`, e as conclusões são calculadas '
      'a partir dele. A mesma medição em HTML, com o visualizador de trades, está '
      'em [relatorio.html](relatorio.html).')
    w('')
    w('Contexto: **EMA %d** (tendência) · **Hull %d** (força) · **Keltner %s e %s '
      'ATRs** (esticamento). Gatilho: `Ticks_Esforco_Hist_v2.ntsl` nas configurações '
      'padrão dele, índice ≥ **%s**. Gestão: stop **%s**, parcial de **%d%%** na '
      'mesma distância do stop, stop do restante na média da operação, alvo **%s**. '
      'Entrada limitada no meio do candle do gatilho, válida por **%d** barra.'
      % (P['EMA_PER'], P['HMA_PER'], vg(P['KELT_INT']), vg(P['KELT_EXT']),
         nivel_rot(P['NIVEL_MIN']), ctx['stop_rot'], int(100 * P['FRAC_PARCIAL']),
         ctx['alvo'], P['MAX_BARRAS_FILL']))
    w('')

    # ------------------------------------------------------------- 1
    w('## 1. O resultado')
    w('')
    for base in BASES:
        b = R['bases'][base]
        w('**%s** — %d barras · %d pregões no arquivo (%d com pregão cheio) · %s a %s '
          '· ATR mediano %d pontos'
          % (base, b['barras'], b['pregoes'], b['pregoes_cheios'], b['ini'],
             b['fim'], b['atr_mediano']))
        w('')
        w(CAB)
        can = R['canal']['setups'][base]
        w(linha('só D', can['cD']))
        w(linha('**D + T** — padrão', can['cDT']))
        w(linha('D + T + K', can['cDTK']))
        w(linha('D + T + K + KB', can['cDTKKB']))
        w('')

    # ------------------------------------------------------------- 2
    w('## 2. De que lado da Hull vale entrar')
    w('')
    w('Duas distâncias, assinadas pelo lado do trade:')
    w('')
    w('```')
    w('dh = sinal × (close − Hull %d) / ATR      dh < 0 = lado oposto ao da Hull'
      % P['HMA_PER'])
    w('de = sinal × (close − EMA %d) / ATR' % P['EMA_PER'])
    w('```')
    w('')
    for chave, titulo in (('baldes', 'Os baldes'), ('faixas', 'Por faixa de dh'),
                          ('inclinacao', 'Pela inclinação da Hull')):
        w('### %s' % titulo)
        w('')
        w('| | n · V26 | EV | t | n · FUT | EV | t |')
        w('|---|--:|--:|--:|--:|--:|--:|')
        for x, y in zip(R['hull'][chave]['WINV26'], R['hull'][chave]['WINFUT']):
            w('| %s | %d | %s | %s | %d | %s | %s |'
              % (x['rot'].replace('<em>', '*').replace('</em>', '*'),
                 x['n'], n1(x['ev']), t2(x['t']), y['n'], n1(y['ev']), t2(y['t'])))
        w('')
    w(ctx['ver_hull_md'])
    w('')
    w(ctx['ver_incl_md'])
    w('')

    # ------------------------------------------------------------- 3
    w('## 3. Os setups')
    w('')
    w('| setup | | sinais V26 | n | EV | t | sinais FUT | n | EV | t |')
    w('|---|---|--:|--:|--:|--:|--:|--:|--:|--:|')
    for su in R['setups']:
        a = R['nivel']['grid']['WINV26'][at]
        b = R['nivel']['grid']['WINFUT'][at]
        x, y = a['setup_' + su], b['setup_' + su]
        ligado = 'ligado' if su in str(P['SETUPS_ATIVOS']) else 'desligado'
        w('| **%s** | %s (%s) | %d | %s | %s | %s | %d | %s | %s | %s |'
          % (su, R['rot_setup'][su], ligado, a['sinais_' + su],
             x['n'] if x else '—', n1(x['ev']) if x else '—',
             t2(x['t']) if x else '—', b['sinais_' + su],
             y['n'] if y else '—', n1(y['ev']) if y else '—',
             t2(y['t']) if y else '—'))
    w('')
    for su in R['setups']:
        nome, desc = ROT_SU[su]
        w('- **%s** — %s' % (nome, desc.replace('<em>', '*').replace('</em>', '*')
                             .replace('<strong>', '**').replace('</strong>', '**')))
    w('')
    w(ctx['ver_setups_md'])
    w('')

    # ------------------------------------------------------------- 4
    w('## 4. O nível do gatilho')
    w('')
    w('| nível | gatilhos V26 | n | /pregão | EV | R | t | gatilhos FUT | n | '
      '/pregão | EV | R | t |')
    w('|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|')
    for nv in R['nivel']['niveis']:
        x = R['nivel']['grid']['WINV26'][nv]
        y = R['nivel']['grid']['WINFUT'][nv]
        mx, my = x['cDT'], y['cDT']
        rot = nivel_rot(nv) + (' ←' if nv == at else '')
        w('| %s | %d | %s | %s | %s | %s | %s | %d | %s | %s | %s | %s | %s |'
          % (rot, x['gatilhos'], mx['n'] if mx else '—',
             vg('%.1f' % mx['por_pregao']) if mx else '—',
             n1(mx['ev']) if mx else '—', n2(mx.get('ev_r')) if mx else '—',
             t2(mx['t']) if mx else '—', y['gatilhos'], my['n'] if my else '—',
             vg('%.1f' % my['por_pregao']) if my else '—',
             n1(my['ev']) if my else '—', n2(my.get('ev_r')) if my else '—',
             t2(my['t']) if my else '—'))
    w('')
    w(ctx['ver_nivel_md'])
    w('')

    # ------------------------------------------------------------- 5
    w('## 5. O canal de Keltner')
    w('')
    w('| zona | barras V26 | gatilhos V26 | barras FUT | gatilhos FUT |')
    w('|---|--:|--:|--:|--:|')
    rot = {'0': 'dentro do canal', '1': 'entre %s e %s ATR'
           % (vg(P['KELT_INT']), vg(P['KELT_EXT'])),
           '2': 'além de %s ATR' % vg(P['KELT_EXT'])}
    for k in ('0', '1', '2'):
        x = R['canal']['zonas']['WINV26'][k]
        y = R['canal']['zonas']['WINFUT'][k]
        w('| %s | %s | %s | %s | %s |' % (rot[k], p1(x['barras']), p1(x['gatilhos']),
                                          p1(y['barras']), p1(y['gatilhos'])))
    w('')
    w('O veto de zona, ligado e desligado:')
    w('')
    w(CAB)
    for base in BASES:
        for r, ch in (('com o veto — o padrão', 'com'), ('sem o veto', 'sem')):
            w(linha('%s · %s' % (base, r), R['canal']['veto'][base][ch]))
    w('')
    w(ctx['ver_canal_md'])
    w('')

    # ------------------------------------------------------------- 6
    w('## 6. A gestão')
    w('')
    w(CAB)
    for base in BASES:
        for ch in R['gestao']['ordem']:
            m = R['gestao']['grid'][base][ch]
            rot = '%s · %s' % (base, R['gestao']['rotulos'][ch])
            w(linha(rot, m))
    w('')
    w(ctx['ver_gestao_md'])
    w('')
    w('### Grade de stop × alvo, em pontos fixos (EV por trade)')
    w('')
    alvos = (200, 250, 300, 450)
    for base in BASES:
        w('**%s**' % base)
        w('')
        w('| stop | %s |' % ' | '.join('alvo %d' % a for a in alvos))
        w('|---|%s' % ('--:|' * len(alvos)))
        for st in (75, 100, 150, 200):
            w('| %d | %s |' % (st, ' | '.join(
                n1(R['gestao']['grade'][base].get('%d_%d' % (st, a)))
                for a in alvos)))
        w('')
    w('### Grade com o stop pelo ATR (EV em R)')
    w('')
    for base in BASES:
        w('**%s**' % base)
        w('')
        w('| stop | %s |' % ' | '.join('alvo %d' % a for a in alvos))
        w('|---|%s' % ('--:|' * len(alvos)))
        for st in ('0.6', '0.75', '1.0', '1.25', '1.5'):
            cel = []
            for a in alvos:
                v = R['gestao']['grade_atr'][base].get('%s_%d' % (st, a))
                cel.append('—' if not v else '%s (t %s)' % (n2(v['ev_r']), t2(v['t'])))
            w('| %s × ATR | %s |' % (vg(st), ' | '.join(cel)))
        w('')

    # ------------------------------------------------------------- 7
    w('## 7. A entrada')
    w('')
    w(CAB)
    for base in BASES:
        b = R['bases'][base]
        w(linha('%s · **limitada no meio do candle**' % base, b['entrada_meio']))
        w(linha('%s · a mercado no fechamento' % base, b['entrada_fecha']))
        w(linha('%s · limitada válida até o fim do pregão' % base, b['fill_livre']))
    w('')
    w(ctx['ver_entrada_md'])
    w('')

    # ------------------------------------------------------------- 8
    w('## 8. O eixo [E2] e o filtro dele')
    w('')
    w(CAB)
    for base in BASES:
        for met in R['e2']['metricas']:
            g = R['e2']['grid'][base][met]
            w(linha('%s · %s (%d gatilhos)'
                    % (base, R['e2']['rotulos'][met], g['gatilhos']), g['cDT']))
    w('')
    w(ctx['ver_e2_md'])
    w('')
    w(CAB)
    for base in BASES:
        f = R['e2']['filtro'][base]
        for r, ch in (('sem `DESCARTA_E2` — o padrão', 'sem'),
                      ('com `DESCARTA_E2`', 'com')):
            w(linha('%s · %s (%d gatilhos)' % (base, r, f['gatilhos_' + ch]), f[ch]))
    w('')
    w(ctx['ver_filtro_e2_md'])
    w('')

    # ------------------------------------------------------------- 9
    w('## 9. Sensibilidade dos cortes')
    w('')
    S = R['sens']
    w('| corte | valor | EV · V26 | t | EV · FUT | t |')
    w('|---|---|--:|--:|--:|--:|')
    for par in S['ordem']:
        for v in S['valores'][par]:
            x = S['grid']['WINV26'][par][v]
            y = S['grid']['WINFUT'][par][v]
            w('| %s | %s%s | %s | %s | %s | %s |'
              % (par, vg(v), ' ←' if v == S['atual'][par] else '',
                 n1(x['ev']) if x else '—', t2(x['t']) if x else '—',
                 n1(y['ev']) if y else '—', t2(y['t']) if y else '—'))
    w('')
    w(ctx['ver_sens_md'])
    w('')

    # ------------------------------------------------------------ 10
    w('## 10. O custo')
    w('')
    w('| custo | EV · V26 | R | t | EV · FUT | R | t |')
    w('|---|--:|--:|--:|--:|--:|--:|')
    for c in (0, 5, 10, 20):
        x = R['bases']['WINV26']['custo_%d' % c]
        y = R['bases']['WINFUT']['custo_%d' % c]
        w('| %d pts | %s | %s | %s | %s | %s | %s |'
          % (c, n1(x['ev']), n2(x.get('ev_r')), t2(x['t']),
             n1(y['ev']), n2(y.get('ev_r')), t2(y['t'])))
    w('')

    # ------------------------------------------------------------ 11
    w('## 11. Mês a mês')
    w('')
    w('| base | mês | n | EV | total | acerto |')
    w('|---|---|--:|--:|--:|--:|')
    for base in BASES:
        for m in R['bases'][base].get('mes', []):
            w('| %s | %s | %d | %s | %s | %s |'
              % (base, m['mes'], m['n'], n1(m['ev']), mil(m['total']),
                 p1(m['acerto'])))
    w('')
    w(ctx['ver_mes_md'])
    w('')

    # ------------------------------------------------------------ 12
    w('## 12. A forma do desempenho')
    w('')
    w('O que o operador precisa saber para não confundir variância normal com '
      'estratégia quebrada. Com custo de 5 pontos por trade, que é o cenário '
      'realista — o de custo zero é piso otimista.')
    w('')
    w('| | %s |' % ' | '.join(BASES))
    w('|---|%s' % ('--:|' * len(BASES)))
    campos = (('trades', 'n', '%d'), ('trades por pregão', 'por_pregao', '%s'),
              ('EV por trade', 'ev', '%s pts'), ('EV em R', 'ev_r', '%s'),
              ('stop médio', 'stop_medio', '%s pts'),
              ('acerto', 'acerto', '%s'), ('média por pregão', 'media_dia', '%s pts'),
              ('desvio por pregão', 'sd_dia', '%s pts'),
              ('pregões positivos', 'dias_pos', '%s'),
              ('pior pregão', 'pior_dia', '%s pts'),
              ('melhor pregão', 'melhor_dia', '%s pts'),
              ('maior sequência de trades sem ganho', 'seq_trades', '%d'),
              ('maior sequência de pregões negativos', 'seq_dias', '%d'),
              ('chance de 3 perdas seguidas', 'p3', '%s'),
              ('chance de 5 perdas seguidas', 'p5', '%s'),
              ('chance de semana negativa', 'p_semana_neg', '%s'),
              ('chance de mês negativo', 'p_mes_neg', '%s'),
              ('drawdown máximo', 'dd', '%s pts'))
    for rot, k, fmt in campos:
        cel = []
        for base in BASES:
            p = R['bases'][base]['psico']['c5']
            v = p.get(k)
            if v is None:
                cel.append('—')
            elif k in ('acerto', 'dias_pos', 'p3', 'p5', 'p_semana_neg', 'p_mes_neg'):
                cel.append(('%s%%' % vg(v)))
            elif fmt == '%d':
                cel.append('%d' % v)
            else:
                cel.append(fmt % vg(v))
        w('| %s | %s |' % (rot, ' | '.join(cel)))
    w('')
    w('| desfecho | %s |' % ' | '.join(BASES))
    w('|---|%s' % ('--:|' * len(BASES)))
    for rot, k in (('alvo', 'p_alvo'), ('stop', 'p_stop'),
                   ('zero a zero', 'p_zero'), ('fim do pregão', 'p_fim')):
        w('| %s | %s |' % (rot, ' | '.join(
            p1(R['bases'][base]['psico']['c5'][k]) for base in BASES)))
    w('')

    # ------------------------------------------------------------ 13
    w('## 13. O que eu faria')
    w('')
    for k in ('acao_nivel', 'acao_gestao', 'acao_setups', 'acao_hull'):
        w('1. %s' % ctx[k + '_md'])
    w('1. **Não ligar os setups de banda.** O K mede positivo sozinho e mesmo assim '
      'piora a carteira; o KB mede negativo no WINFUT.')
    w('1. **Medir o custo real da corretora** e refazer a seção 10 com o número '
      'verdadeiro antes de dimensionar posição.')
    w('')

    # ------------------------------------------------------------ 14
    w('## 14. Ressalvas')
    w('')
    w('- **Amostra pequena.** %d pregões no WINFUT e %d pregões cheios no WINV26 — '
      'dois meses, um regime só.' % (R['bases']['WINFUT']['pregoes'],
                                     R['bases']['WINV26']['pregoes_cheios']))
    w('- **As bases não são independentes.** WINFUT contém WINV26.')
    w('- **As regras saíram destes mesmos dados.** Não há corte de validação fora '
      'da amostra neste projeto. A seção 9 mostra platôs, mas platô medido na mesma '
      'amostra continua sendo sobreajuste.')
    w('- **O canal quase não trabalha.** O veto dele é inerte e os setups de banda '
      'estão desligados; ele ficou por medir bem *o que não fazer*.')
    w('- **O preenchimento é otimista.** A limitada preenche a preço exato ao '
      'primeiro toque, sem fila.')
    w('- **Sem filtro de horário, rolagem ou vencimento.**')
    w('')
    return '\n'.join(L) + '\n'
