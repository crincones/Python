# -*- coding: utf-8 -*-
"""Gera RESULTADOS.md a partir do mesmo contexto do relatorio.html.

Existe para que markdown e HTML nunca discordem: os dois saem de
saida/resumo.json, pelo mesmo caminho.
"""
BASES = ('WINV26', 'WINFUT')
REGIMES = ('ema3', 'kama', 'hma', 't3', 'jma')


def gera(ctx, fmt, ROT_REG, ROT_SU):
    """ctx: contexto montado por relatorio.monta(); fmt: modulo de formatacao."""
    n1, p0, p1, t2, f2, mil = fmt['n1'], fmt['p0'], fmt['p1'], fmt['t2'], fmt['f2'], fmt['mil']
    R, sp = ctx['R'], ctx['stop_pad']
    L = []
    A = L.append

    def lm(rot, m):
        if not m:
            return '| %s | — | — | — | — | — | — | — | — |' % rot
        return ('| %s | %d | %s | %s | %s | %s | %s | %s | %d |'
                % (rot, m['n'], ('%.1f' % m['por_pregao']).replace('.', ','),
                   n1(m['ev']), mil(m['total']), p1(m['acerto']), t2(m['t']),
                   f2(m['pf']), round(m['dd'])))

    CAB = ('| | n | /pregão | EV | total | acerto | t | PF | DD |\n'
           '|---|---|---|---|---|---|---|---|---|')

    A('# Resultados — Rincones1\n')
    A('> **Este arquivo é gerado.** Rode `python rodar.py && python relatorio.py`.')
    A('> Não edite à mão: a fonte de todos os números é `saida/resumo.json`, e o')
    A('> [relatorio.html](relatorio.html) sai do mesmo lugar, pelo mesmo caminho.\n')
    A('**Gestão:** parcial de %d%% **na mesma distância do stop** · o stop do restante '
      'vai para a **média da operação**, que com meia posição é o próprio stop inicial '
      '— então o stop **não anda** e o trade que volta morre em **zero de verdade** · '
      'alvo %d · entrada por ordem limitada no meio do candle, **válida por uma barra** '
      '· **sem custo**. Stop de %d (padrão) e de 100 (variante), lado a lado; a parcial '
      'acompanha os dois.\n' % (ctx['frac'], ctx['alvo'], sp))

    # --- 1
    A('---\n\n## 1. As duas bases\n')
    A('| | barras | pregões | período |\n|---|---|---|---|')
    for b in BASES:
        d = R['bases'][b]
        com_trade = R['variantes'][b]['ema3'][str(sp)]['cAB']['pregoes']
        preg = ('%d (%d com trade)' % (d['pregoes'], com_trade)
                if com_trade < d['pregoes'] else '%d' % d['pregoes'])
        A('| **%s** | %s | %s | %s a %s |'
          % (b, '{:,}'.format(d['barras']).replace(',', '.'), preg,
             d['ini'], d['fim']))
    A('\n> **Elas não são independentes.** O WINFUT contém a janela inteira do WINV26 e')
    A('> mais julho. Quando as duas concordam, isso é menos confirmação do que parece.\n')

    # --- 2: o eixo [E2]
    e2 = R.get('e2')
    A('---\n\n## 2. O eixo [E2]: o deslocamento virou vaivém\n')
    A('O índice de esforço tem três eixos — volume, deslocamento e tempo. O eixo do')
    A('**deslocamento** era `|delta| / |Close−Open|`: agressão por ponto de *saldo*. Saldo')
    A('não é caminho — uma barra que sobe 60, cai 65 e fecha 30 acima da abertura tem o')
    A('mesmo `|Close−Open|` de uma que sobe 30 em linha reta, e as duas contavam igual.\n')
    if e2:
        A('O eixo novo é `%s`, com `percurso = 2·(High−Low) − |Close−Open|` (o menor caminho'
          % e2['rotulos'][e2['atual']])
        A('compatível com o OHLC) e `volta = 1 − |Close−Open|/percurso` (a fração dele que foi')
        A('desfeita). É **produto de duas frações entre 0 e 1, não razão**: razão entre peças')
        A('de dispersão muito diferente mede só a mais volátil das duas. A derivação e a')
        A('medição do eixo estão em `Ticks_Esforco_Hist_v2.ntsl`.\n')
        A('Com **todo o resto congelado** — mesma média, mesmos setups, mesma gestão:\n')
        A('| fórmula | stop | | WINV26 · n / EV / t / PF | WINFUT · n / EV / t / PF |')
        A('|---|---|---|---|---|')
        for met in e2['metricas']:
            for stop in R['stops']:
                for ch, rot in (('setup_A', 'setup A isolado'),
                                ('setup_B', 'setup B isolado'),
                                ('cA', 'carteira só A'), ('cAB', 'carteira A + B')):
                    def cel(b):
                        m = e2['grid'][b][met][str(stop)][ch]
                        return ('%d · %s · %s · %s'
                                % (m['n'], n1(m['ev']), t2(m['t']), f2(m['pf']))
                                if m else '—')
                    primeira = (stop == R['stops'][0] and ch == 'setup_A')
                    marca = '**' if (met == e2['atual'] and ch == 'cAB'
                                     and stop == R['stops'][0]) else ''
                    A('| %s | %d | %s%s%s | %s | %s |'
                      % (e2['rotulos'][met].replace('|', '\\|') if primeira else '',
                         stop, marca, rot, marca, cel('WINV26'), cel('WINFUT')))
        A('')
        A(ctx['ver_e2_md'] + '\n')
        A(ctx['ver_filtro_e2_md'] + '\n')

    # --- 2
    A('---\n\n## 3. A regra da barra seguinte\n')
    A('A ordem limitada no meio do candle do gatilho vale por **uma barra**. Não')
    A('preencheu na barra seguinte, o trade é **abortado** -- não se persegue o preço,')
    A('não se deixa ordem esquecida no livro. Todo número deste arquivo já está sob')
    A('essa regra.\n')
    A(ctx['ver_abortos_md'] + '\n')
    A('---\n\n## 4. Cada setup isolado (stop %d)\n' % sp)
    for b in BASES:
        A('### %s\n' % b)
        A(CAB)
        for su in ('A', 'B', 'C'):
            A(lm('**%s** — %s' % (su, ROT_SU[su][0].split('· ')[1]),
                 R['variantes'][b]['ema3'][str(sp)]['setup_' + su]))
        A('')
    A(ctx['ver_setups_md'] + '\n')
    A('O setup C mede negativo nas duas, em toda configuração testada. Invertendo o')
    A('sinal sobram 0 e 8 trades: a combinação "médias emboladas **e** preço longe')
    A('delas" quase não existe. Fica desligado por padrão.\n')

    # --- 3
    A('---\n\n## 5. A média que dá a direção\n')
    A('Com média única a direção vira o **sinal da inclinação** dela nas últimas %d'
      % R['parametros']['MA_SLOPE'])
    A('barras, normalizada pelo range médio; o toque vira encostar nessa linha. Cada')
    A('família teve período e corte de inclinação varridos, e o valor escolhido foi o')
    A('que mede bem **nas duas bases**, não o pico de uma.\n')
    for stop in R['stops']:
        A('### Carteira só A · stop %d\n' % stop)
        A('| média | % barras em tendência | WINV26 · n / EV / t / PF | WINFUT · n / EV / t / PF |')
        A('|---|---|---|---|')
        for reg in REGIMES:
            def cel(b):
                m = R['variantes'][b][reg][str(stop)]['cA']
                return ('%d · %s · %s · %s' % (m['n'], n1(m['ev']), t2(m['t']), f2(m['pf']))
                        if m else '—')
            tend = R['variantes']['WINFUT'][reg][str(stop)]['tend']
            rot = ROT_REG[reg][0]
            A('| %s%s | %s | %s | %s |'
              % ('**%s**' % rot if reg == 'ema3' else rot,
                 ' ← padrão' if reg == 'ema3' else '', p0(tend), cel('WINV26'), cel('WINFUT')))
        A('')
    A(ctx['ver_ma_md'] + '\n')
    A('O empilhamento exige **concordância entre três escalas de tempo**, e isso é')
    A('informação que a inclinação de uma linha só não carrega. Uma média adaptativa')
    A('resolve o atraso; não resolve a falta de confirmação.\n')
    A('> **Sobre a "Jurik":** o JMA da Jurik Research é proprietário e não publicado. O')
    A('> que está aqui é uma aproximação pública do estilo — adaptativa com correção de')
    A('> fase. Leia aquela linha como "uma adaptativa muito suavizada", **não** como "o')
    A('> JMA foi testado". Se o resultado dela pesasse na decisão, o certo seria')
    A('> licenciar o indicador de verdade e refazer.\n')

    # --- 4
    A('---\n\n## 6. O stop: 100 contra %d\n' % sp)
    A('| stop | carteira | WINV26 · EV / t / PF / DD | WINFUT · EV / t / PF / DD |')
    A('|---|---|---|---|')
    for stop in (sp, 100):
        for ch, rot in (('cA', 'só A'), ('cAB', 'A + B')):
            def cel(b):
                m = R['variantes'][b]['ema3'][str(stop)][ch]
                return '%s · %s · %s · %d' % (n1(m['ev']), t2(m['t']), f2(m['pf']),
                                              round(m['dd']))
            neg = '**' if stop == 100 else ''
            A('| %s%d%s | %s | %s | %s |' % (neg, stop, neg, rot, cel('WINV26'), cel('WINFUT')))
    A('\n' + ctx['ver_stop_md'])
    A('\nO preço do stop curto é acerto: você é parado mais vezes, mas cada perda é menor.')
    A('E como a parcial acompanha o stop, trocar o stop troca as duas linhas de uma vez:')
    A('com stop 150 a parcial sai em +150 e o alvo cheio paga +225 por contrato de lote')
    A('cheio; com stop 100 a parcial sai em +100 e o alvo paga +200.\n')

    g = R.get('gestao')
    if g and g.get('atual'):
        A('### A regra da parcial\n')
        A('| regra | stop | carteira | WINV26 · n / EV / t / zero | WINFUT · n / EV / t / zero |')
        A('|---|---|---|---|---|')
        for chave in g['ordem']:
            for stop in R['stops']:
                for ch, rot in (('cA', 'só A'), ('cAB', 'A + B')):
                    def cel(b):
                        m = g['grid'][b][chave][str(stop)][ch]
                        return ('%d · %s · %s · %s'
                                % (m['n'], n1(m['ev']), t2(m['t']), p0(m['p_zero']))
                                if m else '—')
                    primeira = (stop == R['stops'][0] and ch == 'cA')
                    marca = '**' if (chave == g['atual'] and ch == 'cAB'
                                     and stop == R['stops'][0]) else ''
                    A('| %s | %d | %s%s%s | %s | %s |'
                      % (g['rotulos'][chave] if primeira else '', stop,
                         marca, rot, marca, cel('WINV26'), cel('WINFUT')))
        A('')
        A(ctx['ver_gestao_md'] + '\n')

    # --- 5
    A('---\n\n## 7. Carteira — uma posição por vez (stop %d)\n' % sp)
    for b in BASES:
        A('### %s\n' % b)
        A(CAB)
        for ch, rot in (('cA', 'só A'), ('cAB', '**A + B** — padrão'), ('cABC', 'A + B + C')):
            A(lm(rot, R['variantes'][b]['ema3'][str(sp)][ch]))
        A('')
    A('Se o seu limite é drawdown, é **só A**; se é aproveitar o dia, é **A + B**.')
    A('Adicionar C piora tudo nas duas bases.\n')

    # --- 6
    A('---\n\n## 8. Alvo e parcial\n')
    A('EV em pontos, carteira A + B, com a **parcial acompanhando o stop de cada linha**.')
    A('**Negrito** = melhor da linha.\n')
    for b in BASES:
        g = R['bases'][b]['grade']
        A('### %s\n' % b)
        A('| stop \\ alvo | +200 | +300 | +400 | +500 |\n|---|---|---|---|---|')
        for st in (100, 150, 200):
            vals = [g.get('%d_%d' % (st, al)) for al in (200, 300, 400, 500)]
            mx = max(range(4), key=lambda i: vals[i] if vals[i] is not None else -1e9)
            A('| %d | %s |' % (st, ' | '.join(
                ('**%s**' % n1(v)) if i == mx else n1(v) for i, v in enumerate(vals))))
        A('')
    A('**O alvo de %d é o melhor da linha nas seis linhas das duas tabelas.** Não é um'
      % ctx['alvo'])
    A('pico isolado: 200 é pior, 400 e 500 são piores.\n')

    # --- 7
    A('---\n\n## 9. Entrada, fora da amostra e custos\n')
    A('### Tipo de entrada (carteira A + B, stop %d)\n' % sp)
    A('| | WINV26 | WINFUT |\n|---|---|---|')
    for ch, rot in (('entrada_meio', 'limitada no meio do candle'),
                    ('entrada_fecha', 'a mercado no fechamento')):
        A('| %s | %s · t %s | %s · t %s |'
          % (rot, n1(R['bases']['WINV26'][ch]['ev']), t2(R['bases']['WINV26'][ch]['t']),
             n1(R['bases']['WINFUT'][ch]['ev']), t2(R['bases']['WINFUT'][ch]['t'])))
    A('\n' + ctx['ver_entrada_md'] + '\n')
    A('Isso **não** quer dizer trocar a limitada pela ordem a mercado: as duas linhas')
    A('medem carteiras diferentes — a mercado faz ~15% mais trades porque nunca')
    A('aborta. Quer dizer que **perder o preenchimento não é valor esperado perdido**,')
    A('e que entrar a mercado no fechamento é um plano B legítimo se você preferir')
    A('volume de operações a preço de entrada.\n')
    A('### Mês a mês (WINFUT, carteira A + B)\n')
    A('| mês | n | EV | total | acerto |\n|---|---|---|---|---|')
    for m in R['bases']['WINFUT']['mes']:
        A('| %s%s | %d | %s | %s | %s |'
          % (m['mes'], ' — **fora da amostra**' if m['mes'] == '2026-07' else '',
             m['n'], n1(m['ev']), mil(m['total']), p1(m['acerto'])))
    A('\nJulho é o único mês do WINFUT que não está no WINV26. **Não é um walk-forward**:')
    A('são dois meses, e os parâmetros foram varridos olhando os dois arquivos.\n')
    A('### Custos (carteira A + B, stop %d)\n' % sp)
    A('| custo | WINV26 · EV / t | WINFUT · EV / t |\n|---|---|---|')
    for c in (0, 5, 10, 20):
        A('| %d pts | %s · %s | %s · %s |'
          % (c, n1(R['bases']['WINV26']['custo_%d' % c]['ev']),
             t2(R['bases']['WINV26']['custo_%d' % c]['t']),
             n1(R['bases']['WINFUT']['custo_%d' % c]['ev']),
             t2(R['bases']['WINFUT']['custo_%d' % c]['t'])))
    A('\nA ~5 trades por pregão o custo é uma fração material do EV, não um detalhe. E há')
    A('um custo que **não** está aqui: a ordem limitada é assumida preenchida a preço')
    A('exato assim que o preço toca o nível. Na prática existe fila, e nem todo toque')
    A('preenche.\n')

    # --- 8
    A('---\n\n## 10. Ressalvas\n')
    A('- **Amostra pequena.** %d pregões no WINFUT, %s com trade no WINV26. Vários `t`'
      % (R['bases']['WINFUT']['pregoes'], ctx['preg26tr']))
    A('  ficam entre +1 e +2, que não é evidência forte. O setup C tem 7 e 19 trades — a')
    A('  conclusão sobre ele é "não há evidência a favor", não "está provado que perde".')
    A('- **As bases não são independentes.** WINFUT ⊃ WINV26.')
    A('- **Parâmetros varridos nas mesmas bases** — inclusive o período e a inclinação de')
    A('  cada média adaptativa. A comparação da § 5 carrega sobreajuste: cada família')
    A('  ganhou uma varredura própria.')
    A('- **O leque mínimo mede melhor quanto menor** e o toque na média é quase')
    A('  indiferente. O que carrega o setup A é o alinhamento das médias mais o gatilho a')
    A('  favor, não a geometria fina do pullback.')
    A('- **O filtro de "movimento rápido" do setup B é inerte** — o gatilho já exige')
    A('  índice ≥ 0,80 e o índice já contém o eixo do tempo.')
    A('- **Sem filtro de horário, rolagem ou vencimento.**\n')

    # --- 9
    A('---\n\n## 11. O que eu faria\n')
    A('1. ' + ctx['acao_stop_md'])
    A('2. ' + ctx['acao_carteira_md'])
    A('3. ' + ctx['acao_ma_md'])
    A('4. **Manter o alvo em %d.**' % ctx['alvo'])
    A('5. **Não ligar o setup C.**')
    A('6. **Medir o custo real da corretora** e refazer a § 8 antes de dimensionar posição.')
    return '\n'.join(L) + '\n'
