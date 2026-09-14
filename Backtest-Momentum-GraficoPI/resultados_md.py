# -*- coding: utf-8 -*-
"""
RESULTADOS.md -- a mesma medicao do relatorio.html, em texto.

Chamado por relatorio.py. O .md existe para ler no terminal, no GitHub e
para caber num diff: e a versao que sobrevive sem navegador.
"""
ROT_MODO = {'fecha': 'fechamento', 'meio_lim': 'limitada no meio',
            'antecipa': 'stop no meio (antecipada)'}
ROT_GESTAO = {'parcial': '1:3 com parcial', 'puro': '1:3 sem parcial',
              'r2': '1:2 sem parcial'}


def n(v, c=0):
    """Numero no padrao brasileiro: ponto no milhar, virgula no decimal."""
    if v is None:
        return '-'
    return f'{v:,.{c}f}'.replace(',', ' ').replace('.', ',').replace(' ', '.')


def sn(v, c=0):
    if v is None:
        return '-'
    return ('+' if v > 0 else '') + n(v, c)


def tabela(cab, linhas, alin=None):
    alin = alin or ['---:'] * len(cab)
    alin[0] = ':---'
    out = ['| ' + ' | '.join(cab) + ' |', '| ' + ' | '.join(alin) + ' |']
    out += ['| ' + ' | '.join(str(c) for c in l) + ' |' for l in linhas]
    return '\n'.join(out)


def escreve(D, destino):
    a = D['auditoria']; P = D['parametros']; R = D['rotulo']
    esc = D['variantes'][D['escolhida']]; s = esc['stats']
    base = D['variantes']['fecha|parcial|bronze']['stats']
    mc = D['monte_carlo'][D['escolhida']]
    nt = {x['nivel']: x for x in D['niveis_terco']}
    L = []
    w = L.append

    w('# Resultados -- momentum no grafico de 20 PI (WINFUT)\n')
    w(f"Base: `WINFUT/WINFUT_20PI.csv`, {n(a['candles'])} candles de 20 PI, "
      f"{a['dias']} pregoes, de {a['de']} a {a['ate']}.  ")
    w('Resultados em **pontos do WINFUT**, brutos, com um contrato '
      '(R$ 0,20 por ponto).\n')

    w('> **O resumo em tres linhas.** A regra do CLAUDE.md, medida exatamente como '
      f"esta escrita, ja mede positivo: {sn(base['exp_pts'], 1)} pontos por trade em "
      f"{base['trades']} operacoes. Tres filtros levam isso a {sn(s['exp_pts'], 1)} "
      f"pontos por trade em {s['trades']} operacoes -- o **padrao Ouro**. Um dos "
      'filtros que o CLAUDE.md pedia (a Hull concava) mede **ao contrario** e nao '
      'entrou.\n')

    # ------------------------------------------------------------ a base
    w('## 1. A base, e o que ela e de fato\n')
    w('O grafico de **20 PI** da Nelogica nao e grafico de tempo. Cada candle fecha '
      'exatamente **100 pontos** (20 ticks x 5) acima ou abaixo da sua abertura, e abre '
      'no fechamento do anterior.\n')
    w(tabela(['Conferencia', 'Resultado'], [
        ['Candles / pregoes', f"{n(a['candles'])} / {a['dias']} "
                              f"({n(a['barras_dia_media'])} por pregao)"],
        ['Corpo de exatamente 100 pontos', f"{n(a['corpo_100_pct'], 2)}%"],
        ['Abre no fechamento anterior', f"{n(a['abre_no_fecha_pct'], 2)}%"],
        ['ATR 21 mediano', f"{n(a['atr_mediana'])} pts"],
        ['Range mediano do candle', f"{n(a['range_mediano'])} pts"],
        ['EMA 21 conferida contra a da Nelogica',
         f"{n(a['ema_conferidos'])} candles, erro max {n(a['ema_erro_p999'], 3)} pt, "
         f"{a['ema_divergentes']} divergencias reais"],
    ]))
    w('')
    w('**Consequencia que muda o estudo:** o corpo nao carrega informacao nenhuma. A '
      'unica forma que um candle de PI tem e o **pavio**. Por isso o estudo da '
      '"geometria do candle que retoma a tendencia" olha o pavio total, e nao a '
      'relacao corpo/pavio, que aqui seria so o inverso do range.\n')

    # ------------------------------------------------------------ o padrao
    w('## 2. O padrao e os tres niveis\n')
    w('**Regra-base** (compra; venda e o espelho), avaliada no fechamento do candle '
      'de continuacao:\n')
    w('- o candle fecha a favor e o anterior fechou contra (a retracao);\n'
      '- a Hull 50 esta no sentido do trade e **atras** do extremo do candle;\n'
      '- os **dois** extremos do par ficam do lado de fora da Hull;\n'
      '- a EMA 21 passa entre os topos e os fundos do par.\n')
    w(f"Isso da **{D['n_sinais']['confirmados']} sinais** em {a['dias']} pregoes. Os "
      'tres niveis sao encaixados -- todo Ouro e Prata, todo Prata e Bronze:\n')
    w(tabela(['Nivel', 'O que acrescenta', 'Sinais', 'Por trade', 'Acerto'], [
        [f"**{R[k]}**", D['descricao'][k].replace('\n', ' '), nt[k]['n'],
         sn(nt[k]['ev'], 1) + ' pts', n(nt[k]['wr'], 1) + '%']
        for k in ('bronze', 'prata', 'ouro')
    ], [':---', ':---', '---:', '---:', '---:']))
    w('')

    w('### O veto de exaustao\n')
    w('O CLAUDE.md desconfiava: *"quando a HULL se encontra perto da banda superior, '
      'indica exaustao"*. A banda, sozinha, nao separa nada (secao 4). A intuicao '
      'estava certa no alvo errado: o que separa e a **combinacao** de uma Hull '
      'abrindo a curva a favor do trade com um preco que **ja** se afastou da EMA 21.\n')
    cz = D['estudos']['cruz_exaustao']
    w(tabela(['', f"preco perto da EMA (ate {n(P['estic_exaustao'], 2)} ATR)",
              'preco esticado da EMA'],
             [[r['lin']] + [f"{sn(c['ev'], 1)} pts ({c['n']} sinais)"
                            for c in r['celulas']] for r in cz]))
    w('')
    w('A celula de baixo a direita -- Hull abrindo a curva **e** preco esticado -- e '
      'o que o veto joga fora. Cada metade isolada quase nao diz nada; juntas marcam '
      f"272 dos {D['n_sinais']['confirmados']} sinais, e esses 272 nao pagam.\n")

    # ---------------------------------------------------------- estatisticas
    w('## 3. Estatisticas da variante escolhida\n')
    w(f"**{R[esc['nivel']]} / entrada no {ROT_MODO[esc['modo']]} / "
      f"{ROT_GESTAO[esc['gestao']]}** -- no formato do relatorio do MetaTrader 5, "
      'com o winrate acrescentado.\n')
    w(tabela(['Metrica', 'Valor'], [
        ['Lucro liquido total', f"{sn(s['lucro_liq'])} pts (R$ {sn(s['lucro_liq_rs'])})"],
        ['Lucro bruto', f"{sn(s['lucro_bruto'])} pts"],
        ['Prejuizo bruto', f"{sn(s['prej_bruto'])} pts"],
        ['Fator de lucro', n(s['fator_lucro'], 2)],
        ['Payoff esperado', f"{sn(s['exp_pts'], 2)} pts (R$ {sn(s['exp_rs'], 2)})"],
        ['Indice de Sharpe (por trade)', n(s['sharpe'], 3)],
        ['Correlacao LR', n(s['lr_corr'], 3)],
        ['Rebaixamento maximo', f"{n(s['dd_max'])} pts (R$ {n(s['dd_max_rs'])})"],
        ['Fator de recuperacao', n(s['recovery'], 2)],
        ['Total de negocios', n(s['trades'])],
        ['**Taxa de acerto (winrate)**', f"**{n(s['winrate'], 2)}%**"],
        ['Vencedores / zerados / perdedores',
         f"{s['vitorias']} / {s['zeros']} / {s['derrotas']}"],
        ['Compras (acerto)', f"{s['longs']} ({n(s['longs_wr'], 1)}%)"],
        ['Vendas (acerto)', f"{s['shorts']} ({n(s['shorts_wr'], 1)}%)"],
        ['Maior ganho / maior perda',
         f"{sn(s['maior_ganho'])} / {sn(s['maior_perda'])} pts"],
        ['Ganho medio / perda media',
         f"{sn(s['media_ganho'], 1)} / {sn(s['media_perda'], 1)} pts"],
        ['Max. vitorias consecutivas',
         f"{s['max_seq_ganho']} ({sn(s['max_soma_ganho'])} pts)"],
        ['Max. perdas consecutivas',
         f"{s['max_seq_perda']} ({sn(s['max_soma_perda'])} pts)"],
        ['Saidas: alvo / stop / zero a zero / tempo',
         f"{s['alvos']} / {s['stops']} / {s['stops_zero']} / "
         f"{s['timeouts'] + s['fins_dia']}"],
        ['MEP media / MEN media',
         f"{sn(s['mfe_media'], 1)} / {sn(s['mae_media'], 1)} pts"],
        ['Duracao mediana', f"{n(s['dur_mediana'] / 60, 1)} min "
                            f"({n(s['barras_mediana'])} candles)"],
        ['Negocios por pregao', n(s['trades_dia'], 1)],
        ['Pontos por pregao', sn(s['pts_dia'], 1)],
    ]))
    w('')

    w('### A matriz inteira\n')
    w(tabela(['Entrada', 'Gestao', 'Nivel', 'Trades', 'Pontos', 'Por trade',
              'Acerto', 'Fator', 'Rebaix.'],
             [[ROT_MODO[v['modo']], ROT_GESTAO[v['gestao']], R[v['nivel']],
               v['stats']['trades'], sn(v['stats']['lucro_liq']),
               sn(v['stats']['exp_pts'], 1), n(v['stats']['winrate'], 1) + '%',
               n(v['stats']['fator_lucro'], 2), n(v['stats']['dd_max'])]
              for v in D['variantes'].values()],
             [':---', ':---', ':---'] + ['---:'] * 6))
    w('')
    w('O nivel Ouro nao existe na entrada antecipada: ele depende da forma do candle '
      'de continuacao, que nessa entrada ainda nao terminou de se formar na hora da '
      'decisao.\n')

    # ---------------------------------------------------------- filtros
    w('## 4. Cada filtro, medido\n')
    w(f"Tudo medido no conjunto **sem filtro nenhum** -- os "
      f"{D['n_sinais']['confirmados']} sinais da regra-base, entrada no fechamento, "
      'com parcial. A coluna dos tercos e o teste mais duro que 26 pregoes permitem: '
      'faixa que so paga num terco nao e filtro, e sorte.\n')
    rotulos = {
        'concavidade': 'Concavidade da Hull -- **mede ao contrario do pedido**',
        'esticamento': 'Distancia do preco a EMA 21 -- **entrou** (metade do veto)',
        'pavio': 'Pavio total do candle de continuacao -- **entrou** (separa o Ouro)',
        'pavio_favor': 'Pavio a favor do movimento',
        'pavio_contra': 'Pavio contra o movimento -- nao sobrevive aos tercos',
        'retracao_candles': 'Tamanho da retracao em candles -- **entrou** (nivel Prata)',
        'retracao_tamanho': 'Tamanho da retracao em ATRs -- diz o mesmo, forma menos pratica',
        'inclinacao_hull': 'Inclinacao da Hull -- ganho pequeno, some no conjunto',
        'inclinacao_ema': ('Inclinacao da EMA 21 -- separa **ao contrario**, e '
                           'e a mesma informacao do esticamento'),
        'banda_keltner': 'Distancia da Hull a banda de Keltner -- **nao separa nada**',
        'hull_colada': 'Hull colada na EMA -- **confirma a intuicao**, amostra pequena',
        'hora': 'Horario -- nenhuma faixa e estavel nos tres tercos',
    }
    for k, rot in rotulos.items():
        if k not in D['estudos']:
            continue
        w(f'### {rot}\n')
        w(tabela(['Faixa', 'Sinais', 'Por trade', 'Acerto', '1o terco', '2o terco',
                  '3o terco'],
                 [[r['faixa'], r['n'], sn(r['ev'], 1), n(r['wr'], 1) + '%']
                  + [sn(x, 1) if x is not None else '-' for x in r['ev_terco']]
                  for r in D['estudos'][k]]))
        w('')

    w('Sobre a **inclinacao da EMA 21**, que o CLAUDE.md pede para avaliar: ela '
      'separa, mas ao contrario do que um filtro de tendencia faria esperar -- a EMA '
      'menos inclinada mede melhor. E nao ha o que ganhar ai: essa inclinacao tem '
      'correlacao de **0,78** com o esticamento do preco, e a mesma informacao dita '
      'de outro jeito. Aplicado o veto de exaustao, o efeito some (as quatro faixas '
      'passam a +23,6 / +14,3 / +19,2 / +23,7, sem ordem nenhuma). Nao entrou.\n')

    w('> **Por que os filtros nao se somam.** Empilhar os quatro melhores ao mesmo '
      'tempo deixa 16 sinais e valor esperado **negativo**. Cada corte tira sinais, e '
      'a partir de certo ponto o que sobra e uma amostra pequena demais para '
      'significar qualquer coisa. Os niveis usam tres filtros, nao os oito que '
      'mediram algo.\n')

    # ---------------------------------------------------------- gestao
    w('## 5. Stop, alvo, parcial e medias\n')
    w('### Grade stop x alvo (nivel Ouro, sem parcial)\n')
    w('Valor esperado por trade, em pontos. Entre parenteses, o resultado por **ponto '
      'de risco** -- que e o que compara stops diferentes de forma justa.\n')
    g = D['grade']
    w(tabela(['stop \\ alvo'] + [f"{x} pts" for x in g['alvos']],
             [[f"**{l[0]['stop']}**"] +
              [f"{sn(c['ev'], 1)} ({c['ev_risco']:.2f})"
               + ('  <-' if c['stop'] == P['stop'] and c['alvo'] == P['alvo'] else '')
               for c in l] for l in g['puro']]))
    w('')
    w(f"A combinacao do CLAUDE.md ({n(P['stop'])} / {n(P['alvo'])}) esta marcada. Ela "
      'nao e o maior numero da grade -- stops mais largos medem mais em valor '
      'absoluto -- mas e um **topo local em alvo** (300 mede melhor que 250 e que '
      '400) e e a melhor da coluna quando o resultado e dividido pelo risco. Vale '
      'registrar que a grade inteira mede positivo, inclusive nos stops de 250 e 300 '
      'pontos: o resultado nao depende de ter '
      'acertado o stop e o alvo.\n')

    o = D['variantes']['fecha|parcial|ouro']['stats']
    pu = D['variantes']['fecha|puro|ouro']['stats']
    # ------------------------------------------- risco : retorno (1:2 vs 1:3)
    w('### Relacao risco : retorno -- o 1:2 sem parcial\n')
    w('Alvo em pontos nao quer dizer nada sem o stop ao lado: 300 pontos com stop de '
      '100 e 300 com stop de 300 sao apostas completamente diferentes. A tabela mede o '
      'alvo **relativo** ao stop, e a linha que compara stops diferentes e o resultado '
      '**por ponto de risco**.\n')
    linha100 = next(l for l in D['rr'] if l[0]['stop'] == int(P['stop']))
    w(tabela(['Com stop de ' + n(P['stop']) + ' pts'] +
             [f"1:{c['razao']} (alvo {n(c['alvo'])})" for c in linha100],
             [['Por operacao'] + [sn(c['ev'], 1) + ' pts' for c in linha100],
              ['Acerto'] + [n(c['wr'], 1) + '%' for c in linha100],
              ['**Por ponto de risco**'] + ['**' + n(c['ev_risco'], 2) + '**'
                                            for c in linha100]]))
    w('')
    r2 = D['variantes']['fecha|r2|ouro']['stats']
    p3 = D['variantes']['fecha|puro|ouro']['stats']
    w(f"O **1:2 mede positivo** -- nao e uma opcao ruim. Mas ao mesmo stop ele entrega "
      f"{sn(linha100[1]['ev'], 1)} pontos por operacao contra {sn(linha100[2]['ev'], 1)} "
      f"do 1:3, quase a metade, e o que compra com isso e "
      f"{n(linha100[1]['wr'] - linha100[2]['wr'], 1)} pontos percentuais de acerto. Na "
      f"carteira inteira: {sn(r2['lucro_liq'])} pts contra {sn(p3['lucro_liq'])} do 1:3 "
      f"puro, com rebaixamento **maior** ({n(r2['dd_max'])} contra {n(p3['dd_max'])} "
      f"pontos) e fator de lucro menor ({n(r2['fator_lucro'], 2)} contra "
      f"{n(p3['fator_lucro'], 2)}).\n")
    w('A diagonal inteira, em oito tamanhos de stop. Cada celula e o resultado **por '
      'ponto de risco** e, entre parenteses, o valor esperado por operacao:\n')
    w(tabela(['stop'] + [f"1:{c['razao']}" for c in D['rr'][0]],
             [[f"**{l[0]['stop']}**"] +
              [f"{n(c['ev_risco'], 2)} ({sn(c['ev'], 0)})"
               + ('  <-' if c['padrao'] else '') for c in l] for l in D['rr']]))
    w('')
    w('Tres leituras:\n')
    w('1. **Nenhuma celula e negativa.** O setup nao depende de acertar a relacao '
      'risco:retorno -- ele paga nas trinta e duas.\n'
      '2. **O 1:3 com stop curto e o melhor por unidade de risco** de toda a tabela. '
      'Stops largos rendem mais em pontos absolutos e menos por ponto arriscado, e '
      'ainda exigem mais capital para o mesmo numero de contratos.\n'
      '3. **O 1:1 tem o melhor acerto e o pior resultado por risco** em quase toda a '
      'tabela. Taxa de acerto alta nao e o objetivo: e o que se compra vendendo '
      'expectativa.\n')

    w('### A parcial\n')
    w(f"Com a parcial em +{n(P['parcial_em'])} e o stop do restante na **media da "
      'operacao**, o stop na verdade **nao anda**: com meia posicao e a parcial na '
      'mesma distancia do stop, o preco em que o lucro ja realizado cancela a perda do '
      'restante *e* o stop inicial. O que muda nao e o preco, e o fato de que so '
      'metade da posicao ainda corre risco. Por isso o desfecho "zero a zero" aqui e '
      'zero de verdade, e nao um ganho disfarcado de empate.\n')
    w(tabela(['', 'Com parcial', 'Sem parcial'], [
        ['Total', f"{sn(o['lucro_liq'])} pts", f"{sn(pu['lucro_liq'])} pts"],
        ['Por trade', sn(o['exp_pts'], 1), sn(pu['exp_pts'], 1)],
        ['Fator de lucro', n(o['fator_lucro'], 2), n(pu['fator_lucro'], 2)],
        ['Rebaixamento maximo', f"{n(o['dd_max'])} pts", f"{n(pu['dd_max'])} pts"],
        ['Fator de recuperacao', n(o['recovery'], 2), n(pu['recovery'], 2)],
        ['Operacoes zeradas', n(o['zeros']), n(pu['zeros'])],
    ]))
    w('')
    w('A parcial entrega '
      f"{n(abs(pu['lucro_liq'] - o['lucro_liq']) / pu['lucro_liq'] * 100, 0)}% do lucro "
      f"em troca de um rebaixamento {n((1 - o['dd_max'] / pu['dd_max']) * 100, 0)}% "
      'menor e de um fator de lucro melhor. E uma troca de conforto -- escolha de quem '
      'opera, nao resultado do backteste.\n')

    w('### Periodos de media\n')
    w('A EMA e sempre a linha do meio do Keltner, como manda o CLAUDE.md -- entao ela '
      'e o ATR andam juntos.\n')
    w(tabela(['EMA / ATR', 'Hull', 'Sinais base', 'Por trade (base)', 'Sinais Ouro',
              'Por trade (Ouro)'],
             [[m['ema'], m['hull'], m['n_base'], sn(m['ev_base'], 1), m['n_ouro'],
               sn(m['ev_ouro'], 1) + ('  <- CLAUDE.md' if m['padrao'] else '')]
              for m in D['medias']]))
    w('')
    w('**A Hull 50 ganha de 21, 34 e 80 em todas as EMAs testadas.** O pico nao e uma '
      'celula sortuda, e uma crista -- o tipo de evidencia que mais tranquiliza num '
      'estudo de parametro.\n')

    # ---------------------------------------------------------- robustez
    w('## 6. Robustez\n')
    w('### Terco a terco\n')
    w(tabela(['Nivel', '1o terco', '2o terco', '3o terco', 'Periodo'],
             [[R[k]] + [f"{sn(x['ev'], 1)} ({x['n']})" for x in nt[k]['por_terco']]
              + [f"**{sn(nt[k]['ev'], 1)}**"] for k in ('ouro', 'prata', 'bronze')]))
    w('')
    w('Os tres niveis medem positivo nos tres tercos. O Ouro e o mais parelho dos '
      'tres, apesar de ser o de menor amostra.\n')

    w('### Monte Carlo (4.000 reamostragens com reposicao)\n')
    w(tabela(['Nivel', 'p05', 'mediana', 'p95', 'prob. de lucro', 'rebaix. p95'],
             [[R[D['variantes'][k]['nivel']], sn(m['total_p05']),
               sn(m['total_mediana']), sn(m['total_p95']),
               n(m['prob_lucro'], 1) + '%', n(m['dd_p95'])]
              for k, m in D['monte_carlo'].items() if m and 'parcial' in k]))
    w('')
    w('Isso responde "quanto do resultado foi a ordem de chegada dos trades". **Nao** '
      'responde se o padrao continua valendo no mes que vem.\n')

    w('### Custo operacional\n')
    w('Todos os numeros deste documento sao **brutos**.\n')
    w(tabela(['Custo ida e volta', 'Por trade', 'Total', 'Fator de lucro'],
             [[f"{c['custo']} pts (R$ {n(c['custo'] * P['val_ponto'], 2)})",
               sn(c['ev'], 1), sn(c['total']), n(c['fl'], 2)]
              for c in D['custos']]))
    w('')

    w('### O que este backteste NAO mediu\n')
    w('- **Slippage.** Entradas saem no preco exato do fechamento do candle, saidas no '
      'preco exato do stop ou do alvo. No stop, na pratica, escorrega.\n'
      '- **Caminho dentro do candle.** So existe OHLC; assume-se que o pavio contra o '
      'sentido do candle se forma antes (convencao conservadora). Num candle que bate '
      'stop e alvo, isso decide qual vale.\n'
      '- **Outros regimes.** Agosto e setembro de 2026 no WINFUT foram periodo de '
      'alta. O padrao e de continuacao; e de esperar que sofra em mercado lateral, e a '
      'base nao tem lateral suficiente para medir.\n'
      '- **Um instrumento, um contrato.** Sem variacao de tamanho de posicao e sem '
      'outro ativo para confirmar.\n')

    # ------------------------------------------- agressao e tendencia
    F = D.get('fluxo')
    if F:
        esp = F['espaco']
        pen = {r['nivel']: r for r in F['peneira']}
        o = pen['ouro']
        w('## 6b. Agressao, tempo de barra e forca de tendencia\n')
        w('A base ganhou quatro colunas: volume agressor comprador e vendedor, '
          'duracao da barra, volume e numero de negocios. Num grafico de PI a '
          'duracao e a unica medida de *pressa* que existe -- todo corpo vale 100 '
          f"pontos, entao 100/duracao compara barra com barra direto (mediana "
          f"{n(F['base']['dur_mediana'])} s, quartil de cima "
          f"{n(F['base']['dur_p75'])} s).\n")
        w('**Nenhum dos atributos novos entrou em nenhum nivel.** O que da valor a '
          'esse "nao" e o controle da busca.\n')
        w(f"Foram {esp['feats']} atributos x {esp['cortes']} cortes x 2 sentidos = "
          f"**{esp['total']} comparacoes**. Nesse tamanho de amostra alguma sempre "
          f"parece boa -- inclusive passando no teste dos tercos, que e o mais duro "
          f"usado nas outras secoes. Entao a busca inteira foi repetida "
          f"{esp['perms']} vezes sobre versoes **embaralhadas** dos mesmos "
          f"atributos: o embaralhamento preserva a distribuicao e destroi a ligacao "
          f"com o resultado, de modo que tudo o que a busca achar ali e, por "
          f"construcao, sorte.\n")
        w(tabela(['Nivel', 'Melhor filtro do espaco', 'n', 'EV', 't',
                  't em ruido (mediana)', 't em ruido (p90)', 'p',
                  '3o terco com filtro', '3o terco sem filtro'],
                 [[R[k], f"{pen[k]['melhor']['rotulo']} {pen[k]['melhor']['sentido']}",
                   n(pen[k]['melhor']['n']), sn(pen[k]['melhor']['ev'], 1),
                   sn(pen[k]['melhor']['t'], 2), sn(pen[k]['ruido_mediana'], 2),
                   sn(pen[k]['ruido_p90'], 2), n(pen[k]['p_valor'], 2),
                   sn(pen[k]['fora']['ev_t3'], 1),
                   sn(pen[k]['fora']['ev_t3_base'], 1)]
                  for k in ('ouro', 'prata', 'bronze')]))
        w('')
        w(f"O melhor filtro real do Ouro mede t = {sn(o['melhor']['t'], 2)}. A busca "
          f"em ruido acha t = {sn(o['ruido_mediana'], 2)} na **mediana**. O achado "
          f"real e *pior* que o achado tipico em ruido puro.\n")
        w('As duas ultimas colunas sao a prova mais direta: o corte foi escolhido '
          'usando **so** os dois primeiros tercos e depois aplicado ao terceiro, que '
          'ele nunca viu. Nos dois niveis que importam ele transforma um terco '
          'lucrativo em prejuizo. Um filtro inutil seria inofensivo; estes '
          'atrapalham.\n')

        w('### As duas hipoteses, uma a uma, no Ouro\n')
        w('Sem busca: cada linha e **um** teste, declarado antes de olhar, com o seu '
          'proprio p por permutacao.\n')
        w(tabela(['Hipotese', 'n', 'EV', 'ganho', '1o', '2o', '3o', 'p'],
                 [[h['rotulo'], n(h['n']), sn(h['ev'], 1), sn(h['ganho'], 1),
                   sn(h['tercos'][0], 0), sn(h['tercos'][1], 0),
                   sn(h['tercos'][2], 0), n(h['p_valor'], 2)]
                  for h in F['hipoteses'] if h['nivel'] == 'ouro']))
        w('')
        w('- **"Operacao contra a tendencia forte falha"** nao se confirma. Exigir o '
          'trade a favor da deriva de 20 ou de 50 barras nao paga; o unico corte com '
          'p baixo aponta para o lado **contrario**, o que com 170 comparacoes ja '
          'feitas e exatamente o que o acaso produz. Vale lembrar que a regra-base '
          '**ja** exige a Hull 50 no sentido do trade: boa parte do filtro de '
          'tendencia que faltaria ja esta dentro dela.\n'
          '- **"A retracao logo depois de um cruzamento contundente da EMA 21 '
          'funciona bem"** tambem nao. O primeiro sinal apos o cruzamento mede '
          'praticamente igual a base, e exigir alem disso um cruzamento forte nao '
          'muda nada.\n'
          '- **A agressao tem o sinal certo, so nao tem tamanho.** O candle de '
          f"continuacao tem desequilibrio agressor medio de "
          f"{sn(F['base']['agr_medio_cont'], 3)} a favor e o de retracao "
          f"{sn(F['base']['agr_medio_ret'], 3)} contra -- as colunas medem o que "
          f"deviam medir, e o efeito simplesmente nao sobrevive a peneira.\n")

        w('### O que esta base conseguiria enxergar\n')
        w(tabela(['Nivel', 'n', 'Desvio por trade', 'Filtro que mantem 50%',
                  'mantem 33%', 'mantem 25%'],
                 [[R[r['nivel']], n(r['n']), n(r['desvio'])] +
                  [sn(x['min_ganho'], 0) for x in r['linhas']]
                  for r in F['poder']]))
        w('')
        w('Menor ganho de valor esperado, em pontos por trade, que esta amostra '
          'distingue de zero com 80% de poder a 5%. No Ouro, um filtro que corte dois '
          'tercos dos sinais precisaria valer mais de 40 pontos por trade para '
          'aparecer -- mais que o proprio salto de Bronze para Ouro.\n')
        w('> O resultado negativo desta secao nao e "fluxo nao importa"; e '
          '"26 pregoes nao respondem". Com alguns meses de agressao a pergunta volta '
          'a valer a pena, e o codigo que a responde ja esta pronto em '
          '`estudo_fluxo.py`.\n')

        EFR = F.get('esforco')
        if EFR:
            w('### Esforco x resultado, na versao que o PI permite\n')
            w('No grafico de ticks a razao esforco/resultado precisa da divisao '
              'porque o resultado varia. **No PI o resultado esta fixo por '
              'construcao** -- todo corpo vale 100 pontos -- entao o esforco '
              'sozinho ja *e* a razao.\n')
            w('**Metade da pergunta ja estava respondida.** A leitura geometrica '
              '-- resultado util sobre deslocamento total, `100 / range` -- e '
              'exatamente o filtro de pavio do Ouro, escrito ao contrario: '
              '`range = 100 + pavio`, entao `100/range` e monotonico em pavio. '
              f"Correlacao de posto medida entre os dois: "
              f"**{sn(EFR['geom']['rho'], 4)}** -- a mesma informacao. Esse pedaco "
              f"ja paga e ja e o degrau que separa Ouro de Prata. O que restava "
              f"testar era o esforco em volume, negocios e tempo.\n")
            w(tabela(['Variavel', 'corr. pavio', 'corr. volume', 'corr. duracao',
                      ''],
                     [[r['rotulo'], sn(r['corr_pav'], 2), sn(r['corr_vol'], 2),
                       sn(r['corr_dur'], 2),
                       '**nova**' if (abs(r['corr_pav']) < .25
                                      and abs(r['corr_vol']) < .25
                                      and abs(r['corr_dur']) < .25)
                       else 'ja medida']
                      for r in EFR['novidade']]))
            w('')
            w('"Esforco do par" e sempre **continuacao dividida pela retracao**: '
              'acima de 1, andar a favor saiu mais caro que andar contra. As '
              'tres razoes do par sao ortogonais a tudo que a estrategia ja '
              'usa. Valia medir.\n')

            w('**A pergunta que decide a historia.** Se menos esforco fosse '
              'melhor, o quintil de menor esforco seria o maior:\n')
            w(tabela(['Faixa de esforco do par (Ouro)', 'Sinais', 'EV'],
                     [[r['faixa'] + (' <- menor esforco' if k == 0 else
                                     (' <- maior esforco'
                                      if k == len(EFR['quintis']) - 1 else '')),
                       n(r['n']), sn(r['ev'], 1)]
                      for k, r in enumerate(EFR['quintis'])]))
            w('')
            w(f"Ele mede {sn(EFR['quintis'][0]['ev'], 1)} -- **abaixo** da base do "
              f"Ouro, que e {sn(EFR['base_ouro'], 1)}. Quem carrega o resultado e o "
              f"segundo quintil, sozinho.\n")
            w(tabela(['Nivel', 'Sinais', 'Correlacao de posto esforco x resultado',
                      'p (unicaudal)'],
                     [[R[r['nivel']], n(r['n']), sn(r['rho'], 3),
                       n(r['p_valor'], 2)] for r in EFR['rho']]))
            w('')
            w('A tese de Wyckoff exige relacao monotonica. Nao ha.\n')

            w('**O corte mais fiel:** a continuacao custou menos volume que a '
              'retracao (as duas produziram o mesmo resultado de 100 pontos, '
              'entao a comparacao e limpa).\n')
            w(tabela(['Nivel', 'Gestao', 'n', 'EV', 'base', 'ganho', '1o', '2o', '3o', 'p'],
                     [[R[r['nivel']], r.get('gestao', ''), n(r['n']), sn(r['ev'], 1), sn(r['base'], 1),
                       sn(r['ganho'], 1)] +
                      [sn(v, 0) for v in r['tercos']] + [n(r['p_valor'], 2)]
                      for r in EFR['cortes']]))
            w('')
            pw = EFR['poder']
            w(f"E o achado mais bonito de tres rodadas de investigacao: no Ouro "
              f"com parcial da {sn(EFR['cortes'][1]['ganho'], 1)} pontos, positivo nos tres "
              f"tercos. Mesmo assim **nao entra**. Um filtro que mantem "
              f"{n(pw['frac'], 0)}% dos sinais so seria detectavel acima de "
              f"{sn(pw['min_ganho'], 0)} pontos e este alega "
              f"{sn(pw['observado'], 0)} -- metade do limiar. Somado a ausencia de "
              f"monotonicidade e ao quintil mais eficiente ser o segundo PIOR, e um "
              f"balde sortudo, nao um efeito. E ele **depende da gestao**: trocar o "
              f"alvo 1:3 pelo 1:2 derruba o ganho para "
              f"{sn(EFR['cortes'][-1]['ganho'], 1)} pontos -- e uma leitura "
              f"de fluxo nao pode depender de qual alvo se usa.\n")

    # ---------------------------------------------------------- conclusao
    w('## 7. Conclusao\n')
    w('Ha um setup. Ele nao e exatamente o que o CLAUDE.md descreve -- um dos filtros '
      'pedidos mede ao contrario -- mas o esqueleto da ideia mede positivo **antes** '
      'de qualquer ajuste, e e esse o achado mais importante aqui.\n')
    w(f"> Compra quando a Hull 50 esta subindo e atras do preco, depois de uma "
      f"retracao de **dois ou mais** candles cujos topos ficaram acima da Hull, com a "
      f"EMA 21 cortando o par, no fechamento do candle de continuacao -- desde que o "
      f"preco **nao** esteja esticado da EMA com a Hull acelerando, e que esse candle "
      f"tenha pavio total entre {n(P['pavio_min'])} e {n(P['pavio_max'])} pontos. "
      f"Stop {n(P['stop'])}, parcial de 50% em +{n(P['parcial_em'])}, alvo "
      f"{n(P['alvo'])}. Venda e o espelho.\n")
    w(f"{sn(s['exp_pts'], 1)} pontos por operacao, {s['trades']} operacoes em "
      f"{s['dias']} pregoes ({n(s['trades_dia'], 1)} por dia), acerto de "
      f"{n(s['winrate'], 1)}%, rebaixamento maximo de {n(s['dd_max'])} pontos, "
      f"probabilidade de lucro no Monte Carlo de {n(mc['prob_lucro'], 1)}%.\n")
    w('O plano operacional esta em [PLANO.md](PLANO.md) e em `plano.html`. O relatorio '
      'completo, com os graficos e a navegacao trade a trade, esta em '
      '`relatorio.html`.\n')
    w('---\n')
    w(f"*Gerado por `python rodar.py && python relatorio.py`. Base: "
      f"{n(a['candles'])} candles, {a['dias']} pregoes. Backteste nao e promessa.*")

    with open(destino, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
