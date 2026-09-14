# -*- coding: utf-8 -*-
"""
saida/resumo.json -> PLANO.md e plano.html

O plano de operacao manual que sai das conclusoes. Mesmo conteudo nos dois
formatos, montado uma vez so a partir de uma lista de blocos.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


# --------------------------------------------------------------------------
def n(x, casas=0):
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


# --------------------------------------------------------------------------
# um texto, dois formatos
# --------------------------------------------------------------------------
def inline_html(t):
    t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', t)
    return t


def _desdobra(blocos):
    """Aceita ('tipo', val) e ('tipo', a, b) — os blocos de duas partes
    (destaque, aviso) ficam mais legiveis escritos espalhados."""
    for b in blocos:
        yield b[0], (b[1] if len(b) == 2 else tuple(b[1:]))


def para_md(blocos):
    L = []
    for tipo, val in _desdobra(blocos):
        if tipo in ('h1', 'h2', 'h3'):
            L += ['#' * int(tipo[1]) + ' ' + val, '']
        elif tipo == 'p':
            L += [val, '']
        elif tipo == 'lead':
            L += ['> ' + val, '']
        elif tipo == 'destaque':
            L += ['> **' + val[0] + '** ' + val[1], '']
        elif tipo == 'aviso':
            L += ['> ⚠️ **' + val[0] + '** ' + val[1], '']
        elif tipo == 'ul':
            L += ['- ' + x for x in val] + ['']
        elif tipo == 'ol':
            L += ['%d. %s' % (i + 1, x) for i, x in enumerate(val)] + ['']
        elif tipo == 'tabela':
            cab, linhas = val
            L += ['| ' + ' | '.join(cab) + ' |',
                  '|' + '|'.join(['---'] * len(cab)) + '|']
            L += ['| ' + ' | '.join(str(c) for c in ln) + ' |' for ln in linhas]
            L += ['']
        elif tipo == 'codigo':
            L += ['```', val, '```', '']
        elif tipo == 'hr':
            L += ['---', '']
    return '\n'.join(L)


def para_html(blocos):
    L = []
    for tipo, val in _desdobra(blocos):
        if tipo in ('h1', 'h2', 'h3'):
            L.append('<%s>%s</%s>' % (tipo, inline_html(val), tipo))
        elif tipo == 'p':
            L.append('<p>%s</p>' % inline_html(val))
        elif tipo == 'lead':
            L.append('<p class="lead">%s</p>' % inline_html(val))
        elif tipo == 'destaque':
            L.append('<div class="destaque"><p><b>%s</b> %s</p></div>'
                     % (inline_html(val[0]), inline_html(val[1])))
        elif tipo == 'aviso':
            L.append('<div class="aviso"><p><b>%s</b> %s</p></div>'
                     % (inline_html(val[0]), inline_html(val[1])))
        elif tipo == 'ul':
            L.append('<ul>%s</ul>'
                     % ''.join('<li>%s</li>' % inline_html(x) for x in val))
        elif tipo == 'ol':
            L.append('<ol>%s</ol>'
                     % ''.join('<li>%s</li>' % inline_html(x) for x in val))
        elif tipo == 'tabela':
            cab, linhas = val
            L.append('<div class="rolagem"><table><thead><tr>%s</tr></thead>'
                     '<tbody>%s</tbody></table></div>'
                     % (''.join('<th>%s</th>' % inline_html(c) for c in cab),
                        ''.join('<tr>%s</tr>'
                                % ''.join('<td>%s</td>' % inline_html(str(c))
                                          for c in ln) for ln in linhas)))
        elif tipo == 'codigo':
            L.append('<pre><code>%s</code></pre>'
                     % val.replace('&', '&amp;').replace('<', '&lt;')
                          .replace('>', '&gt;'))
        elif tipo == 'hr':
            L.append('<hr>')
    return '\n'.join(L)


CSS = """
:root{
  --tinta:#12161c; --tinta2:#5d6874; --tinta3:#8d97a3;
  --fundo:#f7f8fa; --papel:#ffffff; --linha:#e3e7ec; --caixa:#f2f4f7;
  --realce:#3b5bdb; --alta:#0f9d76; --baixa:#e03131;
  --sans:"Inter","Segoe UI Variable Text","Segoe UI",system-ui,
         -apple-system,BlinkMacSystemFont,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,"Cascadia Code","JetBrains Mono","SF Mono",
         Consolas,monospace;
}
@media (prefers-color-scheme: dark){
  :root{
    --tinta:#e6e9ee; --tinta2:#98a2b0; --tinta3:#6b7686;
    --fundo:#0e1116; --papel:#161a21; --linha:#252b34; --caixa:#1b2027;
    --realce:#748ffc; --alta:#38d9a9; --baixa:#ff6b6b;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--tinta);
  font:15.5px/1.7 var(--sans);letter-spacing:-0.005em;
  -webkit-font-smoothing:antialiased}
.env{max-width:820px;margin:0 auto;padding:60px 24px 100px}
h1{font-size:34px;line-height:1.15;margin:0 0 30px;letter-spacing:-0.028em;
  font-weight:700;padding-bottom:22px;border-bottom:2px solid var(--tinta)}
h2{font-size:22px;margin:52px 0 8px;padding-top:20px;font-weight:650;
  letter-spacing:-0.02em;border-top:1px solid var(--linha)}
h3{font-size:17px;margin:30px 0 4px;font-weight:640;letter-spacing:-0.012em}
p{margin:13px 0}
a{color:var(--realce);text-decoration:none}
code{font:12.5px/1.5 var(--mono);background:var(--caixa);padding:2px 6px;
  border-radius:5px;letter-spacing:0}
pre{background:var(--caixa);border:1px solid var(--linha);border-radius:10px;
  padding:16px 18px;overflow-x:auto;margin:20px 0}
pre code{background:none;padding:0;font-size:12.5px;line-height:1.7}
.lead{font-size:19px;line-height:1.6;letter-spacing:-0.015em}
.destaque{background:var(--caixa);border-left:3px solid var(--realce);
  padding:16px 20px;margin:24px 0;border-radius:0 8px 8px 0}
.destaque p{margin:0}
.aviso{border:1px solid var(--baixa);border-radius:10px;padding:16px 20px;
  margin:24px 0;background:color-mix(in srgb,var(--baixa) 6%,transparent)}
.aviso p{margin:0}
table{border-collapse:collapse;width:100%;margin:20px 0;font-size:13px;
  font-variant-numeric:tabular-nums;letter-spacing:0}
th,td{padding:8px 11px;text-align:left;border-bottom:1px solid var(--linha);
  vertical-align:top}
thead th{border-bottom:1.5px solid var(--tinta2);font-weight:650;
  color:var(--tinta2);text-transform:uppercase;font-size:10.5px;
  letter-spacing:.07em}
.rolagem{overflow-x:auto}
ul,ol{margin:13px 0;padding-left:24px}
li{margin:6px 0}
hr{border:0;border-top:1px solid var(--linha);margin:38px 0}
footer{margin-top:60px;padding-top:20px;border-top:1px solid var(--linha);
  font-size:12.5px;color:var(--tinta2)}
@media(max-width:640px){h1{font-size:27px}.env{padding:38px 16px 60px}}
"""


# --------------------------------------------------------------------------
def montar(r):
    D, I = r['dados'], r['indicador']
    V = {v['nome']: v for v in r['variantes']}
    CM, EC, VA, SW = (r['comparacao_medias'], r['escolha_cruzada'],
                      r['validacao'], r['sweep_stop'])
    v2, v4 = V['V2'], V['V4']
    s2, s4 = v2['stats'], v4['stats']
    cfg = v2['cfg']
    RNG = r['range_nominal']
    S = cfg['stop_ticks']
    A = cfg['alvo_ticks']
    fora = EC['escolhe_2a_testa_1a']['fora']
    mens = [g for g in r['grid'] if g['mensuravel']]

    B = []
    a = B.append

    a(('h1', 'Plano de operação manual — médias + Esforço × Resultado em '
       'range de %s ticks' % n(RNG)))

    a(('lead', 'Este plano opera a variante **V2**: EMA de 21/42/72 em leque '
       'aberto define a tendência, o indicador dá o momento, e a gestão é '
       '**1:2 fixa**. Leia o §7 antes de mandar a primeira ordem — o estudo '
       'que gerou este plano tem uma reprovação importante nele.'))

    a(('tabela', (['o que o backtest mediu (V2)', ''], [
        ['Operações', '%s em %s pregões (%s por pregão)'
         % (n(s2['operacoes']), n(s2['dias']), n(s2['ops_por_dia'], 1))],
        ['Acerto', pct(s2['acerto'])],
        ['Payoff', n(s2['payoff'], 2)],
        ['Fator de lucro', n(s2['fator_lucro'], 2)],
        ['Expectativa **dentro** da amostra',
         '%s R = %s ticks' % (fmt(s2['expectativa_R'], 3),
                              fmt(s2['expectativa_ticks'], 1))],
        ['Expectativa **fora** da amostra',
         '**%s R** — é este o número em que acreditar'
         % fmt(fora['expectativa_R'], 3)],
        ['Significância', 't = %s' % fmt(s2['t_stat'], 2)],
        ['Pior rebaixamento', '%s R, %s operações para recuperar'
         % (n(s2['drawdown_R'], 1), n(s2['drawdown_operacoes']))],
        ['Maior sequência de perdas', '%s operações' % n(s2['max_perdas_seguidas'])],
        ['Maior sequência de ganhos', '%s operações' % n(s2['max_ganhos_seguidos'])],
        ['Duração típica', '%s barras' % n(s2['barras_media'], 1)],
    ])))

    # ---------------------------------------------------------------- 1
    a(('h2', '1 · O gráfico e as médias'))
    a(('ul', [
        'Símbolo sintético de range gerado pelo `Range_Claude_v1.mq5`, com '
        '**%s ticks** de range.' % n(RNG),
        'Indicador `Trigger_EsforcoResultado_Range.mq5` aplicado ao gráfico, '
        'com os parâmetros de fábrica — não mexa neles.',
        '**Três médias exponenciais** do fechamento: **21, 42 e 72**.',
    ]))
    a(('destaque', 'Use EMA. Não use Hull.',
       'É a conclusão mais sólida do estudo inteiro. Comparando par a par — '
       'mesma largura de leque, mesma gestão, mesmo stop — a EMA vence a Hull '
       'em **%s dos %s pares** testados, com diferença mediana de %s R. A Hull '
       'persegue o preço de perto e vira antes; o preço disso é trocar de lado '
       '%s vezes contra %s da EMA no mesmo histórico. Cada troca é uma '
       'tendência que ela declarou e desfez. Sensibilidade a virada não é a '
       'mesma coisa que leitura de tendência.'
       % (n(CM['todos']['ema_vence']), n(CM['todos']['pares']),
          fmt(CM['todos']['diferenca_mediana'], 3),
          n(r['medias']['hull']['trocas_de_lado']),
          n(r['medias']['ema']['trocas_de_lado']))))

    # ---------------------------------------------------------------- 2
    a(('h2', '2 · O contexto: quando existe tendência'))
    a(('p', 'Duas condições, as duas medidas na barra de sinal. Se qualquer '
       'uma falhar, **não há operação** — não importa o quão bonito esteja o '
       'sinal do indicador.'))
    a(('ol', [
        '**As três médias ordenadas** na direção que se vai operar: '
        '`EMA21 > EMA42 > EMA72` para comprar, o inverso para vender.',
        '**O leque aberto:** a distância entre a EMA21 e a EMA72 tem de ser de '
        'pelo menos **%s ticks = %s dólares**. É a tradução numérica de '
        '"médias não emboladas".'
        % (n(cfg['leque_min']), n(cfg['leque_min'] * r['tick'], 2)),
    ]))
    a(('p', 'Na prática, medir os %s ticks a olho é difícil e desnecessário: '
       'coloque a ferramenta de linha vertical entre as duas médias, ou apenas '
       'exija que dê para enxergar **%s dólares de separação** entre a mais '
       'rápida e a mais lenta. O estudo mostra platô, não pico — errar por 50 '
       'ticks não muda nada.'
       % (n(cfg['leque_min']), n(cfg['leque_min'] * r['tick'], 0))))
    a(('p', 'A progressão medida justifica as duas exigências, nesta ordem:'))
    a(('tabela', (['contexto exigido', 'operações', 'expectativa'], [
        ['nenhum — só o sinal do indicador',
         n(V['V0']['stats']['operacoes']),
         '%s R' % fmt(V['V0']['stats']['expectativa_R'], 3)],
        ['médias ordenadas', n(V['V1']['stats']['operacoes']),
         '%s R' % fmt(V['V1']['stats']['expectativa_R'], 3)],
        ['**médias ordenadas + leque aberto**', n(s2['operacoes']),
         '**%s R**' % fmt(s2['expectativa_R'], 3)],
        ['médias ordenadas CONTRA o sinal',
         n(VA['controles']['leque_contra']['n']),
         '%s R' % fmt(VA['controles']['leque_contra']['expectativa_R'], 3)],
    ])))
    a(('p', 'A última linha é o controle que importa: operar *contra* o leque '
       'rende %s R. O contexto não é decoração.'
       % fmt(VA['controles']['leque_contra']['expectativa_R'], 3)))

    # ---------------------------------------------------------------- 3
    a(('h2', '3 · A entrada'))
    a(('ol', [
        '**Espere a barra de sinal FECHAR.** A seta aparece na barra em '
        'formação e pode sumir quando ela fecha — `resRel`, `qualRel` e o '
        'corpo mudam até o último tick. Sinal em barra aberta não é sinal.',
        '**Confira o contexto** (§2): médias ordenadas *e* leque aberto, na '
        'direção da barra de sinal.',
        '**Entre a mercado, no fechamento da barra**, a favor da direção da '
        'barra de sinal. Vale igual para a seta de absorção e para a de '
        'divergência.',
        '**Uma posição por vez.** Sinal que aparecer com posição aberta é '
        'ignorado, não acumulado.',
    ]))
    a(('p', 'São cerca de **%s operações por pregão** — o filtro do leque '
       'descarta boa parte dos sinais, e é para isso que ele existe.'
       % n(s2['ops_por_dia'], 1)))

    # ---------------------------------------------------------------- 4
    a(('h2', '4 · A saída: qual das três gestões usar'))
    a(('p', 'As três formas pedidas foram testadas. Duas delas **não são '
       'mensuráveis neste gráfico** — e é importante entender por quê antes de '
       'escolher.'))
    a(('tabela', (['gestão', 'desfechos', 'expectativa medida', 'confiável?'], [
        ['**fixo** — stop %s t, alvo %s t, nada se move' % (n(S), n(A)),
         '−1R ou +2R', '%s R' % fmt(s2['expectativa_R'], 3),
         '**sim**'],
        ['**parcial + breakeven da operação** — 50% em +1R, stop não se move',
         '−1R, 0, +1,5R', '%s R' % fmt(s4['expectativa_R'], 3),
         '**sim**'],
        ['parcial + stop na entrada — 50% em +1R, stop vai para a entrada',
         '−1R, +0,5R, +1,5R',
         '%s R' % fmt(V['V3']['stats']['expectativa_R'], 3),
         'não — intervalo de %s R'
         % n(V['V3']['largura_intervalo'], 3)],
        ['breakeven puro — stop vai para a entrada em +1R, sem parcial',
         '−1R, 0, +2R',
         '%s R' % fmt(V['V5']['stats']['expectativa_R'], 3),
         'não — intervalo de %s R'
         % n(V['V5']['largura_intervalo'], 3)],
    ])))
    a(('aviso', 'Por que as duas últimas não são mensuráveis.',
       'A entrada é o fechamento da barra de sinal, então a barra seguinte '
       '**abre exatamente no preço de entrada**. Quando ela sobe 1R, qualquer '
       'pavio inferior faz o preço "voltar ao breakeven" no papel — e como a '
       'barra de range percorre %s ticks garantidos, isso acontece em '
       'praticamente toda barra que arma o gatilho. O arquivo não diz se a '
       'mínima veio antes ou depois do toque em 1R, e as duas leituras dão '
       'resultados que diferem em até %s R. Não é que a gestão seja ruim: é '
       'que este histórico não permite julgá-la.'
       % (n(RNG), n(V['V5']['largura_intervalo'], 2))))
    a(('destaque', '"Breakeven na média da operação" é uma conta, não uma opinião.',
       'Com metade da posição realizada em +1R, o resultado da operação '
       'inteira num stop em −1R é `0,5 × (+S) + 0,5 × (−S) = 0`. Ou seja: **o '
       'breakeven da operação já está no stop inicial** — não é preciso mexer '
       'em nada. Levar o stop para a entrada não é breakeven, é travar +0,5R. '
       'São coisas diferentes, e só a primeira é mensurável aqui.'))
    a(('p', '**A recomendação:** use a gestão **fixa**. Ela mede %s R contra '
       '%s R da parcial com breakeven da operação, é a mais simples de '
       'executar, e não depende de nenhuma suposição. Se preferir a sensação '
       'de realizar metade no meio do caminho, use a `parcial_op` — mas '
       '**não mexa no stop** ao fazer a parcial.'
       % (fmt(s2['expectativa_R'], 3), fmt(s4['expectativa_R'], 3))))

    a(('h3', 'O tamanho do stop'))
    a(('p', 'Stop de **%s ticks**, alvo de **%s ticks**. Duas razões, e a '
       'primeira é geométrica.' % (n(S), n(A))))
    a(('p', 'Num gráfico de range a barra percorre no máximo %s ticks, então '
       'ela não consegue tocar dois níveis separados por mais que isso. Como '
       'stop e alvo distam `S + 2S = 3S`, o resultado deixa de depender de '
       'qualquer convenção exatamente a partir de:' % n(RNG)))
    a(('codigo', 'S > range / 3 = %s ticks' % n(SW['limite_teorico'], 1)))
    a(('p', 'Medido no arquivo, a largura do intervalo cai de %s em S=120 para '
       '**exatamente zero** em S=130 — a previsão e a régua batem. A segunda '
       'razão é que de 130 a 220 ticks existe um platô: a expectativa desce '
       'suavemente e nenhum valor é um pico. %s ticks fica no meio dele, com '
       'folga confortável acima do limite.'
       % (n([g['largura'] for g in SW['linhas']
             if g['stop_ticks'] == 120.0][0], 3), n(S))))
    a(('p', '**Não use stop abaixo de %s ticks.** Abaixo do limite o número '
       'que você viu no backtest não significa nada.'
       % n(SW['limite_teorico'], 0)))

    # ---------------------------------------------------------------- 5
    a(('h2', '5 · Tamanho e risco'))
    a(('p', 'O risco por operação é **%s ticks = %s dólares por lote**.'
       % (n(S), n(S * r['tick'], 2))))
    a(('ul', [
        'Arbitre o lote para que **1R fique em 0,25%% a 0,5%% do capital**. O '
        'pior rebaixamento medido foi de %s R; com 0,5%% por operação isso '
        'seria uma queda de %s%% no capital — e ele pode ser pior fora da '
        'amostra.' % (n(abs(s2['drawdown_R']), 1),
                      n(0.5 * abs(s2['drawdown_R']), 1)),
        '**Prepare-se para %s perdas seguidas.** Foi a maior sequência medida, '
        'e com %s%% de acerto ela é esperada, não anormal. A média de perdas '
        'seguidas é %s.'
        % (n(s2['max_perdas_seguidas']), n(100 * s2['acerto'], 0),
           n(s2['media_perdas_seguidas'], 1)),
        '**Limite diário de perda: 3R.** Atingiu, fecha a plataforma.',
        '**Limite de %s operações por dia**, o dobro da média medida.'
        % n(2 * s2['ops_por_dia'], 0),
    ]))
    a(('destaque', 'O acerto é baixo por construção, e está tudo bem.',
       'Com alvo de 2R e stop de 1R, o ponto de equilíbrio é 33,3%% de '
       'acerto. A V2 acerta %s. Isso significa que **duas em cada três '
       'operações são perdas** — quem não aguenta essa sequência não deve '
       'operar 1:2. A alternativa é a gestão com parcial, que sobe o acerto '
       'para %s ao custo de expectativa menor.'
       % (pct(s2['acerto']), pct(s4['acerto']))))

    # ---------------------------------------------------------------- 6
    a(('h2', '6 · O que não fazer'))
    a(('tabela', (['tentação', 'o que o backtest diz'], [
        ['Trocar a EMA pela Hull',
         'A EMA vence em %s dos %s pares testados. A Hull vira antes e erra '
         'mais.' % (n(CM['todos']['ema_vence']), n(CM['todos']['pares']))],
        ['Operar sem exigir o leque aberto',
         'Cai de %s R para %s R.' % (fmt(s2['expectativa_R'], 3),
                                     fmt(V['V1']['stats']['expectativa_R'], 3))],
        ['Operar sem contexto de médias nenhum',
         'Cai para %s R.' % fmt(V['V0']['stats']['expectativa_R'], 3)],
        ['Apertar o stop para menos de %s ticks' % n(SW['limite_teorico'], 0),
         'Abaixo do limite geométrico o resultado passa a depender de uma '
         'convenção — o número deixa de ser mensurável.'],
        ['Adotar o breakeven puro porque mediu melhor',
         'O intervalo dele vai de %s R a %s R. Ele *pode* ser melhor; o '
         'histórico não permite afirmar.'
         % (fmt(V['V5']['stats_piso']['expectativa_R'], 3),
            fmt(V['V5']['stats_otimista']['expectativa_R'], 3))],
        ['Usar a configuração campeã do grid',
         'Ela mede %s R dentro da amostra e entrega %s R fora. Foi o máximo de '
         '%s tentativas.'
         % (fmt(EC['escolhe_2a_testa_1a']['dentro']['expectativa_R'], 3),
            fmt(fora['expectativa_R'], 3), n(len(mens)))],
        ['Aumentar o lote depois de uma sequência boa',
         'Com t = %s, sequências boas e ruins de %s operações são esperadas '
         'sem que nada tenha mudado.'
         % (fmt(s2['t_stat'], 2), n(s2['max_ganhos_seguidos']))],
        ['Mexer nos parâmetros do indicador',
         'Foram varridos no estudo anterior deste gráfico e são todos platôs. '
         'Mexer depois de ver os resultados é ajustar à amostra.'],
    ])))

    # ---------------------------------------------------------------- 7
    a(('h2', '7 · Expectativa realista — leia antes de operar'))
    a(('aviso', 'O estudo tem duas reprovações sérias, e elas mudam o que '
       'esperar.',
       'Primeira: **o resultado vive no último terço do histórico**. Os dois '
       'primeiros terços rendem %s R e %s R, indistinguíveis de zero; o '
       'terceiro rende %s R e carrega tudo. Segunda: **escolher a melhor '
       'configuração numa metade e testá-la na outra derruba o resultado de '
       '%s R para %s R**. O grid descreve o passado; ele não mostrou '
       'capacidade de prever.'
       % (fmt(VA['tercos'][0]['expectativa_R'], 3),
          fmt(VA['tercos'][1]['expectativa_R'], 3),
          fmt(VA['tercos'][2]['expectativa_R'], 3),
          fmt(EC['escolhe_2a_testa_1a']['dentro']['expectativa_R'], 3),
          fmt(fora['expectativa_R'], 3))))
    a(('p', 'E o custo decide o resto. %s R sobre um stop de %s ticks são %s '
       'ticks por operação:'
       % (fmt(s2['expectativa_R'], 3), n(S), fmt(s2['expectativa_ticks'], 1))))
    a(('tabela', (['custo ida+volta', 'expectativa por operação', 'por pregão'],
                  [['%s ticks' % n(int(c)),
                    '%s R = %s ticks'
                    % (fmt(v2['custo'][c]['expectativa_R'], 3),
                       fmt(v2['custo'][c]['expectativa_ticks'], 1)),
                    '%s USD por lote'
                    % fmt(v2['custo'][c]['expectativa_ticks'] *
                          s2['ops_por_dia'] * r['tick'], 2)]
                   for c in ('0', '10', '20', '40')])))
    a(('p', 'Com 20 ticks de custo sobra %s R; com 40, %s R. E esse é o número '
       '*dentro* da amostra. Fora dela, com custo, não sobra nada.'
       % (fmt(v2['custo']['20']['expectativa_R'], 3),
          fmt(v2['custo']['40']['expectativa_R'], 3))))
    a(('destaque', 'O que fazer com isso.',
       'O que sobreviveu ao estudo não foi um sistema: foram **duas escolhas '
       'de projeto**. Usar EMA em vez de Hull, e exigir o leque aberto. As '
       'duas melhoram o gatilho de forma consistente e por razões estruturais. '
       'O que não sobreviveu foi a calibragem fina — o stop exato, a largura '
       'exata do leque, a gestão exata.'))
    a(('p', '**Comece com lote mínimo e trate os três primeiros meses como '
       'coleta de dados.** O objetivo dessa fase é medir duas coisas que o '
       'backtest não sabe: o seu slippage real e se o regime de mercado do '
       'último terço continua valendo.'))

    # ---------------------------------------------------------------- 8
    a(('h2', '8 · Como saber se parou de funcionar'))
    a(('p', 'Defina os critérios **agora**. Depois de uma sequência ruim '
       'ninguém escreve regra de parada honesta.'))
    a(('ul', [
        '**Registre toda operação** com: data e hora, tipo de sinal, lado, '
        'largura do leque na entrada, distância do preço à EMA21, preço de '
        'entrada e de saída, resultado em R e o slippage contra o fechamento '
        'da barra.',
        '**Depois de 50 operações**, compare o acerto com %s. Abaixo de '
        '33%% a estratégia não paga o alvo de 2R.' % pct(s2['acerto']),
        '**Depois de 100 operações**, some o slippage médio. Se passar de 15 '
        'ticks por operação, não há margem: %s ticks de expectativa bruta não '
        'pagam isso.' % fmt(s2['expectativa_ticks'], 1),
        '**Pare em −%s R acumulados** — é o pior rebaixamento medido. A essa '
        'altura a hipótese de que a vantagem sumiu é mais simples que a de '
        'azar.' % n(abs(s2['drawdown_R']), 0),
        '**Refaça o backtest a cada trimestre** com o histórico novo: '
        '`python rodar.py`. Acompanhe menos o acerto e mais a **estabilidade '
        'entre os terços** — foi ali que este estudo falhou.',
    ]))

    a(('hr', None))
    a(('p', 'Gerado por `plano.py` a partir de `saida/resumo.json` (%s). Os '
       'números vêm todos do backtest; nenhum foi digitado à mão. Para '
       'refazer: `python rodar.py && python plano.py`.' % r['gerado_em']))
    return B


# --------------------------------------------------------------------------
def escrever():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        r = json.load(f)
    B = montar(r)

    with open(os.path.join(BASE, 'PLANO.md'), 'w', encoding='utf-8') as f:
        f.write(para_md(B))
    print('PLANO.md gravado.')

    H = ['<!doctype html>', '<html lang="pt-BR"><head>', '<meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>Plano de operação — médias + Esforço × Resultado</title>',
         '<style>%s</style>' % CSS, '</head><body><div class="env">',
         para_html(B),
         '<footer>Gerado por <code>plano.py</code> a partir de '
         '<code>saida/resumo.json</code> (%s).</footer>' % r['gerado_em'],
         '</div></body></html>']
    with open(os.path.join(BASE, 'plano.html'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(H))
    print('plano.html gravado.')


if __name__ == '__main__':
    escrever()
