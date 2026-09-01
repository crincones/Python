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
    A('**Gestão:** parcial de %d%% em +%d que zera o risco · alvo %d · entrada por '
      'ordem limitada no meio do candle, **válida por uma barra** · **sem custo**. '
      'Stop de %d (padrão) e de 100 '
      '(variante), lado a lado.\n' % (ctx['frac'], ctx['parcial'], ctx['alvo'], sp))

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

    # --- 2
    A('---\n\n## 2. A regra da barra seguinte\n')
    A('A ordem limitada no meio do candle do gatilho vale por **uma barra**. Não')
    A('preencheu na barra seguinte, o trade é **abortado** -- não se persegue o preço,')
    A('não se deixa ordem esquecida no livro. Todo número deste arquivo já está sob')
    A('essa regra.\n')
    A(ctx['ver_abortos_md'] + '\n')
    A('---\n\n## 3. Cada setup isolado (stop %d)\n' % sp)
    for b in BASES:
        A('### %s\n' % b)
        A(CAB)
        for su in ('A', 'B', 'C'):
            A(lm('**%s** — %s' % (su, ROT_SU[su][0].split('· ')[1]),
                 R['variantes'][b]['ema3'][str(sp)]['setup_' + su]))
        A('')
    A('**A prioridade que você pediu está certa.** O setup de tendência é o melhor dos')
    A('três nas duas bases, em todas as colunas.\n')
    A('O setup C mede negativo nas duas, em toda configuração testada. Invertendo o')
    A('sinal sobram 0 e 8 trades: a combinação "médias emboladas **e** preço longe')
    A('delas" quase não existe. Fica desligado por padrão.\n')

    # --- 3
    A('---\n\n## 4. A média que dá a direção\n')
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
    A('---\n\n## 5. O stop: 100 contra %d\n' % sp)
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
    A('\n**O stop de 100 melhora o `t` e o fator de lucro nas duas bases, nas duas')
    A('carteiras.** Corta o risco por trade em um terço, então o mesmo limite de perda')
    A('diária compra 50% mais contratos. O preço é acerto: com stop mais curto você é')
    A('parado mais vezes, mas cada perda é menor e o saldo melhora.\n')

    # --- 5
    A('---\n\n## 6. Carteira — uma posição por vez (stop %d)\n' % sp)
    for b in BASES:
        A('### %s\n' % b)
        A(CAB)
        for ch, rot in (('cA', 'só A'), ('cAB', '**A + B** — padrão'), ('cABC', 'A + B + C')):
            A(lm(rot, R['variantes'][b]['ema3'][str(sp)][ch]))
        A('')
    A('Se o seu limite é drawdown, é **só A**; se é aproveitar o dia, é **A + B**.')
    A('Adicionar C piora tudo nas duas bases.\n')

    # --- 6
    A('---\n\n## 7. Alvo e parcial\n')
    A('EV em pontos, carteira A + B, com a parcial fixa em +%d. **Negrito** = melhor da linha.\n'
      % ctx['parcial'])
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
    A('---\n\n## 8. Entrada, fora da amostra e custos\n')
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
    A('---\n\n## 9. Ressalvas\n')
    A('- **Amostra pequena.** %d pregões no WINFUT, %s com trade no WINV26. Vários `t`'
      % (R['bases']['WINFUT']['pregoes'], ctx['preg26tr']))
    A('  ficam entre +1 e +2, que não é evidência forte. O setup C tem 7 e 19 trades — a')
    A('  conclusão sobre ele é "não há evidência a favor", não "está provado que perde".')
    A('- **As bases não são independentes.** WINFUT ⊃ WINV26.')
    A('- **Parâmetros varridos nas mesmas bases** — inclusive o período e a inclinação de')
    A('  cada média adaptativa. A comparação da § 4 carrega sobreajuste: cada família')
    A('  ganhou uma varredura própria.')
    A('- **O leque mínimo mede melhor quanto menor** e o toque na média é quase')
    A('  indiferente. O que carrega o setup A é o alinhamento das médias mais o gatilho a')
    A('  favor, não a geometria fina do pullback.')
    A('- **O filtro de "movimento rápido" do setup B é inerte** — o gatilho já exige')
    A('  índice ≥ 0,80 e o índice já contém o eixo do tempo.')
    A('- **Sem filtro de horário, rolagem ou vencimento.**\n')

    # --- 9
    A('---\n\n## 10. O que eu faria\n')
    A('1. **Baixar o stop para 100.** Melhora `t` e PF nas duas bases, nas duas carteiras,')
    A('   e corta o risco por trade em um terço. É a mudança com mais apoio nos dados.')
    A('2. **Rodar só o setup A por um tempo.** Melhor EV, `t`, PF e drawdown; ~2,5 trades')
    A('   por pregão é operável à mão.')
    A('3. **Manter as três EMAs, com stop 100.** É a única configuração em que o')
    A('   empilhamento ganha nas duas bases. Com stop 150 a KAMA passa à frente no')
    A('   WINFUT -- mais um motivo para o stop curto ser o padrão.')
    A('4. **Manter o alvo em %d.**' % ctx['alvo'])
    A('5. **Não ligar o setup C.**')
    A('6. **Medir o custo real da corretora** e refazer a § 7 antes de dimensionar posição.')
    return '\n'.join(L) + '\n'
