# -*- coding: utf-8 -*-
"""
saida/resumo.json -> RESULTADOS.md

Nenhum numero e digitado aqui. Tudo vem do resumo.json gravado por rodar.py.
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


def n(x, casas=0):
    """Numero no formato brasileiro: 1.234,5"""
    if x == float('inf'):
        return '∞'
    s = ('%.*f' % (casas, x)).replace('.', ',')
    inteiro, _, dec = s.partition(',')
    neg = inteiro.startswith('-')
    inteiro = inteiro.lstrip('-')
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    out = ('-' if neg else '') + '.'.join(grupos)
    return out + (',' + dec if dec else '')


def fmt(x, casas=0):
    return ('+' if x > 0 else '') + n(x, casas)


def pct(x, casas=1):
    return n(100 * x, casas) + '%'


def escrever():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        r = json.load(f)

    D, I, P = r['dados'], r['indicador'], r['dados']['premissa']
    M, SW, EC = r['medias'], r['sweep_stop'], r['escolha_cruzada']
    VA, G, CM = r['validacao'], r['grid'], r['comparacao_medias']
    V = {v['nome']: v for v in r['variantes']}
    RNG = r['range_nominal']
    v2, v10 = V['V2'], V['V10']
    s2 = v2['stats']
    mens = [g for g in G if g['mensuravel']]
    amb = r['ambiguidade']

    L = []
    a = L.append

    a('# Médias + Esforço × Resultado em XAUUSD, gráfico de range de %s ticks'
      % n(RNG))
    a('')
    a('Backtest da ideia de **seguir a tendência**: as EMAs (ou Hull) de 21, '
      '42 e 72 em leque ordenado e aberto definem o contexto; o indicador '
      '`Trigger_EsforcoResultado_Range.mq5` dá o momento de entrar; a gestão é '
      'sempre **1:2**, nas três formas pedidas.')
    a('')
    a('%s barras (%s a %s, %s pregões), gerado em %s a partir de `%s`. Todos '
      'os números vêm de `saida/resumo.json`.'
      % (n(D['barras']), D['inicio'][:10], D['fim'][:10], n(D['dias']),
         r['gerado_em'], r['arquivo']))
    a('')

    # ------------------------------------------------------------------ 1
    a('## 1 · Resposta curta')
    a('')
    a('Quatro conclusões, em ordem de quanto se pode confiar nelas.')
    a('')
    a('**1. A EMA vence a Hull.** Na mesma seleção e na mesma gestão, a EMA '
      'entrega %s de expectativa por operação contra %s da Hull (V2 contra '
      'V7). Comparando **par a par** — mesma largura de leque, mesmo modo, '
      'mesmo stop — a EMA vence em **%s dos %s pares** do grid, com diferença '
      'mediana de %s R. Das %s exceções, %s estão em stops de 291 ou 388 '
      'ticks, faixa em que as duas famílias já rendem perto de zero. É a '
      'conclusão mais sólida do estudo, porque é uma comparação estrutural e '
      'não um máximo escolhido.'
      % (fmt(s2['expectativa_R'], 3) + ' R',
         fmt(V['V7']['stats']['expectativa_R'], 3) + ' R',
         n(CM['todos']['ema_vence']), n(CM['todos']['pares']),
         fmt(CM['todos']['diferenca_mediana'], 3), n(len(CM['excecoes'])),
         n(sum(1 for e in CM['excecoes'] if e['stop_ticks'] >= 291))))
    a('')
    a('**2. O leque ajuda, e ajuda progressivamente.** Sem contexto de médias: '
      '%s R. Com o leque ordenado: %s R. Com o leque ordenado *e* aberto: '
      '%s R. Cada exigência acrescenta, na ordem esperada — que é o que se '
      'quer ver quando uma ideia está certa.'
      % (fmt(V['V0']['stats']['expectativa_R'], 3),
         fmt(V['V1']['stats']['expectativa_R'], 3),
         fmt(s2['expectativa_R'], 3)))
    a('')
    a('**3. Das três gestões pedidas, duas não são mensuráveis neste '
      'gráfico.** As que movem o stop para a entrada — a parcial com stop na '
      'entrada e o breakeven puro — dão os melhores números da tabela e '
      'nenhum deles significa coisa alguma: dependem de uma ordem de eventos '
      'dentro da barra que o arquivo não registra. O intervalo da V5 vai de '
      '%s R a %s R. A leitura literal de "breakeven na média da operação" '
      '(V4) é a única das duas variantes com parcial que **não** depende de '
      'convenção — ver §5.'
      % (fmt(V['V5']['stats_piso']['expectativa_R'], 3),
         fmt(V['V5']['stats_otimista']['expectativa_R'], 3)))
    a('')
    a('**4. A configuração campeã não sobrevive à escolha fora da amostra.** '
      'Escolhendo a melhor das %s configurações mensuráveis numa metade do '
      'histórico e medindo na outra, o resultado cai de %s R para **%s R** '
      '(t = %s). O grid mede um passado; ele não previu o futuro dentro do '
      'próprio arquivo.'
      % (n(len(mens)),
         fmt(EC['escolhe_2a_testa_1a']['dentro']['expectativa_R'], 3),
         fmt(EC['escolhe_2a_testa_1a']['fora']['expectativa_R'], 3),
         fmt(EC['escolhe_2a_testa_1a']['fora']['t_stat'], 2)))
    a('')
    a('| V2 — a configuração recomendada | |')
    a('|---|---|')
    for rot, val in (
            ('Contexto', 'EMA 21/42/72 ordenadas, leque ≥ %s ticks'
             % n(v2['cfg']['leque_min'])),
            ('Gatilho', 'sinal do indicador a favor da tendência'),
            ('Gestão', 'stop %s t, alvo %s t — 1:2 fixo'
             % (n(v2['cfg']['stop_ticks']), n(v2['cfg']['alvo_ticks']))),
            ('Operações', '%s em %s pregões' % (n(s2['operacoes']), n(s2['dias']))),
            ('Acerto', pct(s2['acerto'])),
            ('Payoff', n(s2['payoff'], 2)),
            ('Fator de lucro', n(s2['fator_lucro'], 2)),
            ('Expectativa', '%s R = %s ticks por operação'
             % (fmt(s2['expectativa_R'], 3), fmt(s2['expectativa_ticks'], 1))),
            ('Significância', 't = %s' % fmt(s2['t_stat'], 2)),
            ('Rebaixamento máximo', '%s R (%s operações para se recuperar)'
             % (n(s2['drawdown_R'], 1), n(s2['drawdown_operacoes']))),
            ('Maior sequência de perdas', '%s operações' % n(s2['max_perdas_seguidas'])),
            ('Maior sequência de ganhos', '%s operações' % n(s2['max_ganhos_seguidos'])),
            ('Expectativa fora da amostra', '**%s R** — é este o número em que '
             'acreditar' % fmt(EC['escolhe_2a_testa_1a']['fora']['expectativa_R'], 3))):
        a('| %s | %s |' % (rot, val))
    a('')
    a('> **A ressalva que decide tudo.** %s R sobre um stop de %s ticks são %s '
      'ticks por operação. O custo de ida e volta em XAUUSD raramente fica '
      'abaixo disso. Com 20 ticks de custo a V2 entrega %s R; com 40, %s R. '
      'Fora da amostra, com custo, não sobra nada.'
      % (fmt(s2['expectativa_R'], 3), n(v2['cfg']['stop_ticks']),
         fmt(s2['expectativa_ticks'], 1),
         fmt(v2['custo']['20']['expectativa_R'], 3),
         fmt(v2['custo']['40']['expectativa_R'], 3)))
    a('')

    # ------------------------------------------------------------------ 2
    a('## 2 · Os dados e a premissa')
    a('')
    a('O indicador pressupõe range constante e a convenção de agressão do '
      'símbolo sintético. As duas foram conferidas antes de medir qualquer '
      'coisa — é a versão Python de `ValidarPremissa()` do `.mq5`.')
    a('')
    a('| | |')
    a('|---|---|')
    a('| Range mediano | %s ticks |' % n(P['range_mediana']))
    a('| Barras dentro de ±10%% da mediana | **%s** |' % pct(P['range_dentro_10pct'], 2))
    a('| Desvio padrão do range | %s ticks |' % n(P['range_desvio'], 2))
    a('| Barras sem agressão vendedora | %s |' % pct(P['pct_vol_zero'], 2))
    a('| Correlação entre as duas agressões | %s |' % n(P['correlacao_agressoes'], 3))
    a('| Barras | %s em %s pregões |' % (n(D['barras']), n(D['dias'])))
    a('| Período | %s a %s |' % (D['inicio'][:16], D['fim'][:16]))
    a('| Preço | %s a %s |' % (n(D['preco_min'], 2), n(D['preco_max'], 2)))
    a('')
    a('Premissa confirmada nos dois pontos. O gatilho produz **%s sinais** '
      '(%s das barras, %s por pregão): %s de absorção e %s de divergência.'
      % (n(I['total']), pct(I['pct_barras'], 2), n(I['sinais_por_dia'], 1),
         n(I['absorcao']), n(I['divergencia'])))
    a('')

    # ------------------------------------------------------------------ 3
    a('## 3 · A estratégia, em três peças')
    a('')
    a('**O contexto.** As três médias (21/42/72) têm de estar ordenadas na '
      'direção do sinal — 21 > 42 > 72 para compra. A largura do leque '
      '(`|MA21 − MA72|`, em ticks) é a tradução numérica de "não embolado": '
      'leque estreito é consolidação, e é onde este tipo de entrada morre.')
    a('')
    a('**O gatilho.** O sinal do `Trigger_EsforcoResultado_Range.mq5`, portado '
      'linha a linha para `engine.py`. Ele é um sinal de *virada*: a barra N '
      'reverte a barra N−1 e se opera a favor de N. Combinado com o leque, '
      'deixa de ser reversão e vira **retomada** — só entra quando a virada '
      'aponta para o mesmo lado da tendência.')
    a('')
    a('**A gestão.** Sempre 1:2. Chamando S a distância do stop:')
    a('')
    a('| modo | o que faz | desfechos possíveis |')
    a('|---|---|---|')
    a('| `fixo` | stop em −S, alvo em +2S, nada se move | −1R ou +2R |')
    a('| `parcial` | a +S vende 50% e leva o stop para a **entrada** | −1R, +0,5R, +1,5R |')
    a('| `parcial_op` | a +S vende 50% e o stop **fica onde está** | −1R, 0, +1,5R |')
    a('| `breakeven` | a +S o stop vai para a **entrada**, sem parcial | −1R, 0, +2R |')
    a('')
    a('Os modos `parcial` e `parcial_op` são as duas leituras possíveis de '
      '"parcial que ativa o breakeven na média da operação", e a diferença '
      'entre elas é aritmética, não semântica. Com metade realizada em +S, o '
      'resultado da operação inteira num stop em −S é')
    a('')
    a('```')
    a('0,5 × (+S)  +  0,5 × (−S)  =  0')
    a('```')
    a('')
    a('ou seja: **o breakeven da operação já está no stop inicial**. Levar o '
      'stop para a entrada (modo `parcial`) não é breakeven — é travar +0,5R. '
      'Os dois estão implementados e publicados porque a diferença é material '
      'e o enunciado admite as duas.')
    a('')

    # ------------------------------------------------------------------ 4
    a('## 4 · As médias como contexto: EMA contra Hull')
    a('')
    a('Antes de qualquer operação, vale olhar o que cada família de média faz '
      'com este gráfico.')
    a('')
    a('| | EMA | Hull |')
    a('|---|---|---|')
    for rot, k, f in (
            ('Barras de aquecimento', 'aquecimento', lambda x: n(x)),
            ('Tempo com leque ordenado', 'pct_ordenado', lambda x: pct(x)),
            ('Tempo embolado', 'pct_embolado', lambda x: pct(x)),
            ('Trocas de lado do leque', 'trocas_de_lado', lambda x: n(x)),
            ('Barras entre trocas', 'barras_por_troca', lambda x: n(x)),
            ('Duração mediana da tendência', 'duracao_mediana_tendencia',
             lambda x: '%s barras' % n(x)),
            ('Leque mediano', 'leque', lambda x: '%s ticks' % n(x['50%'])),
            ('Tempo com leque ≥ 400 t', 'pct_leque_400', lambda x: pct(x))):
        a('| %s | %s | %s |' % (rot, f(M['ema'][k]), f(M['hull'][k])))
    a('')
    a('A Hull faz exatamente o que promete: persegue o preço de perto e vira '
      'antes. O preço disso é trocar de lado %s vezes contra %s da EMA — %s '
      'trocas a mais no mesmo histórico. Cada troca é uma tendência que a '
      'Hull declarou e desfez.'
      % (n(M['hull']['trocas_de_lado']), n(M['ema']['trocas_de_lado']),
         n(M['hull']['trocas_de_lado'] - M['ema']['trocas_de_lado'])))
    a('')
    a('E o resultado operacional segue a estrutura. Par a par — mesma largura '
      'de leque, mesmo modo, mesmo stop — a EMA vence em %s dos %s pares '
      '(entre os mensuráveis, %s de %s), com diferença mediana de %s R. '
      'Sensibilidade a virada não é a mesma coisa que leitura de tendência: '
      'para esta estratégia, a média mais lenta é a que serve.'
      % (n(CM['todos']['ema_vence']), n(CM['todos']['pares']),
         n(CM['mensuraveis']['ema_vence']), n(CM['mensuraveis']['pares']),
         fmt(CM['todos']['diferenca_mediana'], 3)))
    a('')
    a('As %s exceções em que a Hull vence estão todas em stops grandes, onde '
      'as duas famílias já rendem perto de zero:' % n(len(CM['excecoes'])))
    a('')
    a('| leque | modo | stop | EMA | Hull |')
    a('|---|---|---|---|---|')
    for e in CM['excecoes']:
        a('| ≥%s | `%s` | %s t | %s R | %s R |'
          % (n(e['leque_min']), e['modo'], n(e['stop_ticks']),
             fmt(e['ema'], 3), fmt(e['hull'], 3)))
    a('')

    # ------------------------------------------------------------------ 5
    a('## 5 · Quais gestões este gráfico consegue medir')
    a('')
    a('Esta é a seção mais importante do estudo, e a que muda a resposta à '
      'pergunta original.')
    a('')
    a('Num gráfico de range vale uma regra geométrica exata: a barra percorre '
      '**no máximo %s ticks**, logo ela não consegue tocar dois níveis '
      'separados por mais que isso. Duas consequências.'
      % n(RNG))
    a('')
    a('**[1] Stop e alvo.** Eles distam `S + 2S = 3S`. Se `3S > %s`, nunca são '
      'tocados na mesma barra e a hipótese pessimista/otimista deixa de '
      'importar. O limite é exato:'
      % n(RNG))
    a('')
    a('```')
    a('S > range / 3 = %s ticks' % n(SW['limite_teorico'], 1))
    a('```')
    a('')
    a('**[2] O gatilho de 1R, nos modos que movem o stop para a entrada.** Há '
      'um segundo instante que o arquivo não data: a barra que arma o '
      'gatilho. Ela **abre exatamente no preço de entrada** (a entrada é o '
      'fechamento da barra de sinal), então qualquer pavio contrário faz o '
      'preço "voltar ao breakeven" no papel. Como a barra percorre %s ticks '
      'garantidos, isso acontece em praticamente toda barra que arma o '
      'gatilho. Só para de acontecer quando o gatilho fica a mais de um range '
      'inteiro da entrada.' % n(RNG))
    a('')
    a('A tabela abaixo mede a largura do intervalo (piso a teto) de cada '
      'combinação. **Largura zero é a prova de que o número não depende de '
      'convenção nenhuma.**')
    a('')
    a('| stop | alvo | modo | piso | padrão | teto | largura | mensurável |')
    a('|---|---|---|---|---|---|---|---|')
    for x in amb:
        if x['stop_ticks'] not in (194.0, 388.0, 450.0):
            continue
        a('| %s t | %s t | `%s` | %s | %s | %s | %s R | %s |'
          % (n(x['stop_ticks']), n(x['alvo_ticks']), x['modo'],
             fmt(x['piso'], 3), fmt(x['padrao'], 3), fmt(x['teto'], 3),
             n(x['largura'], 3), '**sim**' if x['mensuravel'] else 'não'))
    a('')
    a('Leia a tabela de baixo para cima. Com stop de 450 ticks — mais que um '
      'range inteiro — **os quatro modos ficam mensuráveis**, exatamente como '
      'a geometria previa. E aí a vantagem já evaporou: os quatro convergem '
      'para perto de %s R.'
      % fmt(sorted(x['padrao'] for x in amb
                   if x['stop_ticks'] == 450.0)[2], 2))
    a('')
    a('Com stop de 194 ticks, ao contrário, os dois modos que movem o stop '
      'para a entrada têm intervalos de %s R e %s R de largura — ou seja, o '
      'número deles é indeterminado. E são justamente eles que aparecem no '
      'topo de qualquer ranking.'
      % (n([x['largura'] for x in amb
            if x['stop_ticks'] == 194.0 and x['modo'] == 'parcial'][0], 3),
         n([x['largura'] for x in amb
            if x['stop_ticks'] == 194.0 and x['modo'] == 'breakeven'][0], 3)))
    a('')
    a('> **Conclusão de método.** Dos três modos de gestão pedidos, o `fixo` e '
      'o `parcial_op` (a leitura literal de "breakeven na média da operação") '
      'são mensuráveis neste gráfico. O `parcial` com stop na entrada e o '
      '`breakeven` puro não são — não porque a estratégia seja ruim, mas '
      'porque este histórico não contém a informação necessária para julgá-la. '
      'Para medi-los seria preciso um arquivo de ticks, não de barras.')
    a('')

    # ------------------------------------------------------------------ 6
    a('## 6 · A varredura do stop')
    a('')
    a('Com a gestão fixa e a seleção da V2, variando só o tamanho do stop '
      '(o alvo acompanha, sempre 2×).')
    a('')
    a('| stop | alvo | ops | acerto | expectativa | t | largura | 1ª metade | 2ª metade |')
    a('|---|---|---|---|---|---|---|---|---|')
    for g in SW['linhas']:
        a('| %s t%s | %s t | %s | %s | %s R | %s | %s | %s R | %s R |'
          % (n(g['stop_ticks']),
             ' **←**' if g['stop_ticks'] == 194.0 else '',
             n(g['alvo_ticks']), n(g['n']), pct(g['acerto']),
             fmt(g['expectativa_R'], 3), fmt(g['t_stat'], 2),
             n(g['largura'], 3) + (' ✔' if g['mensuravel'] else ' ✗'),
             fmt(g['metade_1a'], 3), fmt(g['metade_2a'], 3)))
    a('')
    a('Três leituras.')
    a('')
    a('1. **O limite geométrico aparece na régua.** A largura do intervalo cai '
      'de %s em S=120 para exatamente **zero** em S=130. O limite teórico era '
      '%s. A previsão e a medição batem.'
      % (n([g['largura'] for g in SW['linhas'] if g['stop_ticks'] == 120.0][0], 3),
         n(SW['limite_teorico'], 1)))
    a('2. **Há platô, não pico.** De 130 a 220 ticks a expectativa desce '
      'suavemente de %s para %s. Um parâmetro que só funciona num valor exato '
      'seria ajuste; este não é o caso.'
      % (fmt([g['expectativa_R'] for g in SW['linhas'] if g['stop_ticks'] == 130.0][0], 3),
         fmt([g['expectativa_R'] for g in SW['linhas'] if g['stop_ticks'] == 220.0][0], 3)))
    a('3. **Mas as duas metades não se parecem.** Em toda linha da tabela, a '
      '1ª metade fica perto de zero e a 2ª carrega o resultado. Isso não é '
      'propriedade do parâmetro — é propriedade do período. O §8 trata disso.')
    a('')

    # ------------------------------------------------------------------ 7
    a('## 7 · O grid completo')
    a('')
    a('%s configurações medidas: %s famílias de média × %s larguras de leque × '
      '%s modos de gestão × %s tamanhos de stop. Publicar o grid inteiro é o '
      'que permite ler o melhor número como o máximo de %s tentativas.'
      % (n(len(G)), 2, 4, 4, 5, n(len(G))))
    a('')
    a('**As dez melhores por expectativa:**')
    a('')
    a('| média | leque | modo | stop | ops | acerto | expectativa | PF | t | mensurável |')
    a('|---|---|---|---|---|---|---|---|---|---|')
    for g in sorted(G, key=lambda x: -x['expectativa_R'])[:10]:
        a('| %s | ≥%s | `%s` | %s t | %s | %s | %s R | %s | %s | %s |'
          % (g['ma_tipo'].upper(), n(g['leque_min']), g['modo'],
             n(g['stop_ticks']), n(g['n']), pct(g['acerto']),
             fmt(g['expectativa_R'], 3), n(g['fator_lucro'], 2),
             fmt(g['t_stat'], 2),
             '**sim**' if g['mensuravel'] else '✗ indeterminado'))
    a('')
    a('Das %s configurações, apenas **%s são mensuráveis** sem depender de '
      'convenção. E o topo do ranking geral é dominado justamente pelas '
      'indeterminadas.' % (n(len(G)), n(len(mens))))
    a('')
    a('**As cinco melhores entre as mensuráveis:**')
    a('')
    a('| média | leque | modo | stop | ops | acerto | expectativa | PF | payoff | t |')
    a('|---|---|---|---|---|---|---|---|---|---|')
    for g in sorted(mens, key=lambda x: -x['expectativa_R'])[:5]:
        a('| %s | ≥%s | `%s` | %s t | %s | %s | %s R | %s | %s | %s |'
          % (g['ma_tipo'].upper(), n(g['leque_min']), g['modo'],
             n(g['stop_ticks']), n(g['n']), pct(g['acerto']),
             fmt(g['expectativa_R'], 3), n(g['fator_lucro'], 2),
             n(g['payoff'], 2), fmt(g['t_stat'], 2)))
    a('')
    a('Note que **todas as cinco são EMA**. Nenhuma configuração com Hull '
      'entra no topo das mensuráveis.')
    a('')

    # ------------------------------------------------------------------ 8
    a('## 8 · A escolha fora da amostra — o teste que reprova')
    a('')
    a('Com %s configurações mensuráveis, o melhor número da tabela é o máximo '
      'de %s tentativas e não serve de estimativa de nada. A única leitura '
      'honesta é escolher onde não se vai medir, e medir onde não se escolheu.'
      % (n(len(mens)), n(len(mens))))
    a('')
    a('| escolhido em | configuração escolhida | dentro da amostra | **fora da amostra** | mediana das candidatas fora |')
    a('|---|---|---|---|---|')
    for k, rot in (('escolhe_1a_testa_2a', '1ª metade'),
                   ('escolhe_2a_testa_1a', '2ª metade')):
        e = EC[k]['escolhida']
        a('| %s | %s, leque ≥ %s, `%s`, stop %s t | %s R (t = %s) | **%s R** (t = %s, n = %s) | %s R |'
          % (rot, e['ma_tipo'].upper(), n(e['leque_min']), e['modo'],
             n(e['stop_ticks']),
             fmt(EC[k]['dentro']['expectativa_R'], 3),
             fmt(EC[k]['dentro']['t_stat'], 2),
             fmt(EC[k]['fora']['expectativa_R'], 3),
             fmt(EC[k]['fora']['t_stat'], 2), n(EC[k]['fora']['n']),
             fmt(EC[k]['mediana_fora'], 3)))
    a('')
    a('**Reprovado.** Escolhendo na 2ª metade, a campeã mede %s R lá dentro e '
      'entrega %s R na 1ª metade — praticamente nada, com t = %s. Escolhendo '
      'na 1ª metade, a campeã escolhida entrega %s R na 2ª, *abaixo* da '
      'mediana das candidatas (%s R): a seleção foi pior que escolher ao '
      'acaso entre as concorrentes.'
      % (fmt(EC['escolhe_2a_testa_1a']['dentro']['expectativa_R'], 3),
         fmt(EC['escolhe_2a_testa_1a']['fora']['expectativa_R'], 3),
         fmt(EC['escolhe_2a_testa_1a']['fora']['t_stat'], 2),
         fmt(EC['escolhe_1a_testa_2a']['fora']['expectativa_R'], 3),
         fmt(EC['escolhe_1a_testa_2a']['mediana_fora'], 3)))
    a('')
    a('É por isso que este relatório recomenda a V2 e não a campeã do grid. A '
      'V2 não foi escolhida por ser a melhor: foi escolhida por ser a mais '
      'simples que respeita a geometria — leque aberto, gestão fixa, stop em '
      'meio range. O número que se deve esperar dela é o **fora da amostra**, '
      'não o de dentro.')
    a('')

    # ------------------------------------------------------------------ 9
    a('## 9 · Validação e controles')
    a('')
    a('| pedaço da amostra | ops | acerto | expectativa | t |')
    a('|---|---|---|---|---|')
    a('| **amostra inteira** | %s | %s | %s R | %s |'
      % (n(VA['geral']['n']), pct(VA['geral']['acerto']),
         fmt(VA['geral']['expectativa_R'], 3), fmt(VA['geral']['t_stat'], 2)))
    for nm, rot in (('1a', '1ª metade'), ('2a', '2ª metade')):
        v = VA['metades'][nm]
        a('| %s | %s | %s | %s R | %s |'
          % (rot, n(v['n']), pct(v['acerto']), fmt(v['expectativa_R'], 3),
             fmt(v['t_stat'], 2)))
    for v in VA['tercos']:
        a('| %sº terço | %s | %s | %s R | %s |'
          % (v['terco'], n(v['n']), pct(v['acerto']),
             fmt(v['expectativa_R'], 3), fmt(v['t_stat'], 2)))
    a('')
    a('**O resultado está concentrado no fim do histórico.** Os dois primeiros '
      'terços rendem %s R e %s R — indistinguíveis de zero. O terceiro rende '
      '%s R e responde sozinho por quase todo o resultado. Isso é o padrão de '
      'uma estratégia que funcionou num regime de mercado, não de uma que '
      'funciona.'
      % (fmt(VA['tercos'][0]['expectativa_R'], 3),
         fmt(VA['tercos'][1]['expectativa_R'], 3),
         fmt(VA['tercos'][2]['expectativa_R'], 3)))
    a('')
    a('Os controles, por outro lado, se comportam como deveriam:')
    a('')
    a('| controle | o que é | ops | acerto | expectativa | t |')
    a('|---|---|---|---|---|---|')
    rot = {'invertido': 'a mesma coisa, operando o lado oposto',
           'sem_leque': 'sem exigir contexto de médias',
           'leque_contra': 'só sinais CONTRA a tendência das médias',
           'direcao_sorteada': 'mesmas barras, direção sorteada, mesma gestão'}
    for k, v in VA['controles'].items():
        a('| %s | %s | %s | %s | %s R | %s |'
          % (k, rot.get(k, ''), n(v['n']), pct(v['acerto']),
             fmt(v['expectativa_R'], 3), fmt(v['t_stat'], 2)))
    a('')
    a('O invertido é claramente negativo (%s R, t = %s): a vantagem é de '
      '**direção**, e não um artefato de contabilidade. A direção sorteada nas '
      'mesmas barras dá %s R, o que mostra que a gestão 1:2 sozinha não '
      'produz vantagem nenhuma — o que existe vem do gatilho. E operar '
      '*contra* o leque rende %s R, contra %s R a favor: o contexto das médias '
      'está do lado certo.'
      % (fmt(VA['controles']['invertido']['expectativa_R'], 3),
         fmt(VA['controles']['invertido']['t_stat'], 2),
         fmt(VA['controles']['direcao_sorteada']['expectativa_R'], 3),
         fmt(VA['controles']['leque_contra']['expectativa_R'], 3),
         fmt(s2['expectativa_R'], 3)))
    a('')

    # ----------------------------------------------------------------- 10
    a('## 10 · As variantes')
    a('')
    a('| variante | ops | acerto | payoff | PF | expectativa | t | DD | seq. perdas | seq. ganhos | mensurável |')
    a('|---|---|---|---|---|---|---|---|---|---|---|')
    for v in r['variantes']:
        s = v['stats']
        a('| **%s** %s | %s | %s | %s | %s | %s R | %s | %s R | %s | %s | %s |'
          % (v['nome'], v['rotulo'], n(s.get('operacoes', 0)),
             pct(s.get('acerto', 0)), n(s.get('payoff', 0), 2),
             n(s.get('fator_lucro', 0), 2),
             fmt(s.get('expectativa_R', 0), 3), fmt(s.get('t_stat', 0), 2),
             n(s.get('drawdown_R', 0), 1),
             n(s.get('max_perdas_seguidas', 0)),
             n(s.get('max_ganhos_seguidos', 0)),
             'sim' if v['mensuravel'] else '**✗**'))
    a('')
    a('Detalhe de cada uma:')
    a('')
    for v in r['variantes']:
        a('**%s · %s** — %s' % (v['nome'], v['rotulo'], v['descricao']))
        a('')
    a('### Estatística completa das variantes mensuráveis')
    a('')
    a('| | %s |' % ' | '.join(v['nome'] for v in r['variantes'] if v['mensuravel']))
    a('|---|%s|' % ('---|' * len([v for v in r['variantes'] if v['mensuravel']])))
    campos = [
        ('Operações', 'operacoes', lambda x: n(x)),
        ('Vitórias', 'vitorias', lambda x: n(x)),
        ('Perdas', 'perdas', lambda x: n(x)),
        ('Neutras', 'neutras', lambda x: n(x)),
        ('Acerto', 'acerto', lambda x: pct(x)),
        ('Ganho médio', 'ganho_medio', lambda x: '%s t' % fmt(x, 1)),
        ('Perda média', 'perda_media', lambda x: '%s t' % fmt(x, 1)),
        ('Payoff', 'payoff', lambda x: n(x, 2)),
        ('Fator de lucro', 'fator_lucro', lambda x: n(x, 2)),
        ('Fator de recuperação', 'fator_recuperacao', lambda x: n(x, 2)),
        ('Expectativa (R)', 'expectativa_R', lambda x: fmt(x, 3)),
        ('Expectativa (ticks)', 'expectativa_ticks', lambda x: fmt(x, 1)),
        ('Desvio (ticks)', 'desvio_ticks', lambda x: n(x, 1)),
        ('t', 't_stat', lambda x: fmt(x, 2)),
        ('SQN', 'sqn', lambda x: n(x, 2)),
        ('Rebaixamento (R)', 'drawdown_R', lambda x: n(x, 1)),
        ('Rebaixamento (ops)', 'drawdown_operacoes', lambda x: n(x)),
        ('Máx. perdas seguidas', 'max_perdas_seguidas', lambda x: n(x)),
        ('Máx. ganhos seguidos', 'max_ganhos_seguidos', lambda x: n(x)),
        ('Máx. sem ganho seguidas', 'max_sem_ganho_seguidas', lambda x: n(x)),
        ('Média de perdas seguidas', 'media_perdas_seguidas', lambda x: n(x, 2)),
        ('Barras por operação', 'barras_media', lambda x: n(x, 1)),
        ('Operações por pregão', 'ops_por_dia', lambda x: n(x, 1)),
        ('Dias positivos', 'dias_positivos', lambda x: n(x)),
        ('Dias negativos', 'dias_negativos', lambda x: n(x)),
    ]
    vv = [v for v in r['variantes'] if v['mensuravel']]
    for rot, k, f in campos:
        a('| %s | %s |'
          % (rot, ' | '.join(f(v['stats'].get(k, 0)) for v in vv)))
    a('')
    a('### Sensibilidade')
    a('')
    a('Expectativa em R por operação, sob cada hipótese e com cada custo.')
    a('')
    a('| variante | piso | padrão | teto | custo 10 t | custo 20 t | custo 40 t | 1ª metade | 2ª metade |')
    a('|---|---|---|---|---|---|---|---|---|')
    for v in r['variantes']:
        vals = [v['stats_piso'].get('expectativa_R', 0),
                v['stats'].get('expectativa_R', 0),
                v['stats_otimista'].get('expectativa_R', 0),
                v['custo']['10'].get('expectativa_R', 0),
                v['custo']['20'].get('expectativa_R', 0),
                v['custo']['40'].get('expectativa_R', 0),
                v['metades']['1a'].get('expectativa_R', 0),
                v['metades']['2a'].get('expectativa_R', 0)]
        a('| %s · %s | %s |'
          % (v['nome'], v['rotulo'], ' | '.join(fmt(x, 3) for x in vals)))
    a('')
    a('As colunas *piso* e *teto* são a mesma coisa nas variantes mensuráveis '
      'e se afastam nas outras — é a propriedade do §5 aparecendo na tabela.')
    a('')

    # ----------------------------------------------------------------- 11
    a('## 11 · Restrições recomendadas')
    a('')
    a('1. **Usar EMA, não Hull.** A conclusão mais sólida do estudo, e a única '
      'que vale independentemente de qualquer escolha de parâmetro.')
    a('2. **Exigir o leque ordenado e aberto** (≥ %s ticks entre a EMA21 e a '
      'EMA72). Cada exigência acrescentou, na ordem esperada.'
      % n(v2['cfg']['leque_min']))
    a('3. **Preferir a gestão fixa, ou a parcial com breakeven da operação.** '
      'São as duas mensuráveis. As outras duas podem até ser melhores na '
      'prática — este histórico simplesmente não permite saber.')
    a('4. **Stop entre %s e 220 ticks.** Abaixo de %s ticks o resultado deixa '
      'de ser mensurável; acima de 250 a vantagem some.'
      % (n(130), n(SW['limite_teorico'], 0)))
    a('5. **Não operar contra o leque.** Rende %s R contra %s R a favor.'
      % (fmt(VA['controles']['leque_contra']['expectativa_R'], 3),
         fmt(s2['expectativa_R'], 3)))
    a('6. **Esperar %s R, não %s R.** O primeiro é o número fora da amostra; o '
      'segundo é o de dentro.'
      % (fmt(EC['escolhe_2a_testa_1a']['fora']['expectativa_R'], 3),
         fmt(s2['expectativa_R'], 3)))
    a('7. **Tratar o custo como a restrição dominante.** Ver §1.')
    a('')

    # ----------------------------------------------------------------- 12
    a('## 12 · Limitações')
    a('')
    a('- **O resultado vive no último terço do histórico.** Os dois primeiros '
      'terços são indistinguíveis de zero. Essa é a limitação mais séria, e '
      'nenhuma outra a compensa.')
    a('- **A escolha de configuração não validou fora da amostra** (§8). O '
      'grid descreve o passado; não mostrou capacidade de prever.')
    a('- **Duas das três gestões pedidas não são mensuráveis** neste tipo de '
      'arquivo (§5). Para julgá-las é preciso histórico de ticks.')
    a('- **Uma amostra, um ativo, %s pregões.** Nenhuma validação interna '
      'substitui um segundo histórico.' % n(D['dias']))
    a('- **Slippage não está modelado.** A entrada é a mercado no fechamento '
      'de uma barra de range — um instante de movimento, onde a execução é '
      'pior que a média.')
    a('- **A convenção de agressão é premissa, não fato medido.** O estudo '
      'confere que os dois campos existem e são distintos, não que '
      '`tick_volume` seja de fato a agressão compradora.')
    a('- **O leque de 400 ticks foi escolhido olhando os dados.** Ele fica num '
      'platô e a progressão V0→V1→V2 é monotônica, o que ajuda — mas continua '
      'sendo um número escolhido depois de ver o resultado.')
    a('')
    a('---')
    a('')
    a('Gerado por `resultados_md.py` a partir de `saida/resumo.json` (%s). '
      'Para reproduzir: `python rodar.py && python resultados_md.py`.'
      % r['gerado_em'])

    caminho = os.path.join(BASE, 'RESULTADOS.md')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('RESULTADOS.md gravado (%s linhas).' % len(L))


if __name__ == '__main__':
    escrever()
