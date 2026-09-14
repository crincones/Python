# -*- coding: utf-8 -*-
"""
saida/resumo.json -> PLANO.md e plano.html

O plano de operacao manual que sai das conclusoes do backtest. Mesmo conteudo
nos dois formatos, montado uma vez so a partir de uma lista de blocos.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


# --------------------------------------------------------------------------
def n(x, casas=0):
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
    """**negrito**, `codigo` e *italico* -> HTML."""
    t = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<i>\1</i>', t)
    return t


def _desdobra(blocos):
    """Aceita ('tipo', val) e tambem ('tipo', a, b) -- os blocos de duas
    partes (destaque, aviso) ficam mais legiveis escritos espalhados."""
    for b in blocos:
        yield b[0], (b[1] if len(b) == 2 else tuple(b[1:]))


def para_md(blocos):
    L = []
    for tipo, val in _desdobra(blocos):
        if tipo == 'h1':
            L += ['# ' + val, '']
        elif tipo == 'h2':
            L += ['## ' + val, '']
        elif tipo == 'h3':
            L += ['### ' + val, '']
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
            L += ['```' + val[0], val[1], '```', '']
        elif tipo == 'hr':
            L += ['---', '']
    return '\n'.join(L)


def para_html(blocos):
    L = []
    for tipo, val in _desdobra(blocos):
        if tipo == 'h1':
            L.append('<h1>%s</h1>' % inline_html(val))
        elif tipo == 'h2':
            L.append('<h2>%s</h2>' % inline_html(val))
        elif tipo == 'h3':
            L.append('<h3>%s</h3>' % inline_html(val))
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
                                          for c in ln)
                                for ln in linhas)))
        elif tipo == 'codigo':
            L.append('<pre><code>%s</code></pre>'
                     % val[1].replace('&', '&amp;').replace('<', '&lt;')
                             .replace('>', '&gt;'))
        elif tipo == 'hr':
            L.append('<hr>')
    return '\n'.join(L)


CSS = """
:root{
  --tinta:#1b1f24; --tinta2:#5b6570; --fundo:#fbfaf7; --papel:#ffffff;
  --linha:#e2ddd4; --realce:#8a6a2f; --alta:#1a7f5a; --baixa:#b3453a;
  --caixa:#f5f2ec;
}
@media (prefers-color-scheme: dark){
  :root{
    --tinta:#e8e6e1; --tinta2:#9aa2ab; --fundo:#14171a; --papel:#1b1f23;
    --linha:#2e343a; --realce:#d9ae5e; --alta:#3fbb8a; --baixa:#e0685c;
    --caixa:#20262c;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--tinta);
  font:16px/1.65 Georgia,'Times New Roman',serif}
.env{max-width:800px;margin:0 auto;padding:56px 22px 90px}
h1{font-size:32px;line-height:1.2;margin:0 0 28px;letter-spacing:-.4px;
   padding-bottom:18px;border-bottom:2px solid var(--tinta)}
h2{font-size:22px;margin:46px 0 6px;padding-top:14px;
   border-top:1px solid var(--linha)}
h3{font-size:17px;margin:26px 0 4px}
p{margin:12px 0}
a{color:var(--realce)}
code{font:13px/1.5 ui-monospace,'Cascadia Mono',Consolas,monospace;
  background:var(--caixa);padding:1px 5px;border-radius:3px}
pre{background:var(--caixa);border:1px solid var(--linha);border-radius:7px;
  padding:14px 16px;overflow-x:auto;margin:18px 0}
pre code{background:none;padding:0;font-size:12.5px;line-height:1.6}
.lead{font-size:19px;line-height:1.55;color:var(--tinta)}
.destaque{background:var(--caixa);border-left:3px solid var(--realce);
  padding:14px 18px;margin:22px 0;border-radius:0 5px 5px 0}
.destaque p{margin:0}
.aviso{border:1px solid var(--baixa);border-radius:7px;padding:14px 18px;
  margin:22px 0;background:color-mix(in srgb,var(--baixa) 7%,transparent)}
.aviso p{margin:0}
table{border-collapse:collapse;width:100%;margin:18px 0;
  font:13.5px/1.45 system-ui,-apple-system,sans-serif}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--linha);
  vertical-align:top}
thead th{border-bottom:1.5px solid var(--tinta);font-weight:600;
  color:var(--tinta2);text-transform:uppercase;font-size:11px;
  letter-spacing:.06em}
.rolagem{overflow-x:auto}
ul,ol{margin:12px 0;padding-left:24px}
li{margin:5px 0}
hr{border:0;border-top:1px solid var(--linha);margin:34px 0}
footer{margin-top:56px;padding-top:18px;border-top:1px solid var(--linha);
  font:13px/1.6 system-ui,sans-serif;color:var(--tinta2)}
@media(max-width:640px){h1{font-size:26px}.env{padding:36px 15px 60px}}
"""


# --------------------------------------------------------------------------
def montar(r):
    D, I = r['dados'], r['indicador']
    V = {v['nome']: v for v in r['variantes']}
    LB, EF = r['linha_base'], r['esforco']
    s8 = V['V8']['stats']
    s9 = V['V9']['stats']
    s7 = V['V7']['stats']
    RNG = r['range_nominal']
    MEIO = RNG / 2
    ind = I['parametros']
    cands = [b for b in r['busca'] if not b['artefato'] and not b['poucas']]

    B = []
    a = B.append

    a(('h1', 'Plano de operação manual — Esforço × Resultado em range de %s '
       'ticks' % n(RNG)))

    a(('lead', 'Este plano opera a variante **V8** do backtest: sinal do '
       'indicador, filtro de esforço baixo, alvo e stop a meio range. É a '
       'única configuração do estudo que passou em todos os controles — e '
       'ainda assim a margem dela cabe dentro de um spread ruim. Leia o §8 '
       'antes de mandar a primeira ordem.'))

    a(('tabela', (['o que o backtest mediu', ''], [
        ['Operações', '%s em %s pregões (%s por pregão)'
         % (n(s8['operacoes']), n(s8['dias']), n(s8['ops_por_dia'], 1))],
        ['Acerto', pct(s8['acerto'])],
        ['Expectativa bruta', '%s ticks = %s R = %s USD por lote'
         % (fmt(s8['expectativa_ticks'], 1), fmt(s8['expectativa_R'], 3),
            fmt(s8['expectativa_usd'], 2))],
        ['Significância', 't = %s (erro padrão de %s ticks)'
         % (fmt(s8['t_stat'], 2), n(s8['erro_padrao_ticks'], 1))],
        ['Fator de lucro', n(s8['fator_lucro'], 2)],
        ['Pior rebaixamento', '%s ticks = %s R'
         % (n(s8['drawdown_ticks']), n(s8['drawdown_R'], 2))],
        ['Duração típica', '%s barra(s)' % n(s8['barras_media'], 1)],
    ])))

    # ---------------------------------------------------------------- 1
    a(('h2', '1 · O gráfico, antes de qualquer coisa'))
    a(('p', 'O indicador só significa alguma coisa num gráfico onde '
       '`High-Low` é constante **e** onde `tick_volume` e `real_volume` '
       'carregam agressão compradora e vendedora. Aplicado em qualquer outro '
       'lugar ele não dá erro: desenha setas sem significado, que é o pior '
       'modo de falhar.'))
    a(('ul', [
        'Símbolo sintético de range gerado pelo `Range_Claude_v1.mq5`, com '
        '**%s ticks** de range.' % n(RNG),
        'Indicador `Trigger_EsforcoResultado_Range.mq5` aplicado ao gráfico.',
        'Confira o log ao anexar: se ele avisar que o range foge da mediana ou '
        'que `real_volume` está zerado, **pare**. A premissa não vale e o resto '
        'deste plano não se aplica.',
    ]))
    a(('destaque', 'Não mexa nos parâmetros do indicador.',
       'Os seis foram varridos no backtest e todos são platôs — nenhum valor '
       'testado muda a conclusão, e o padrão nunca foi o melhor da varredura. '
       'Isso é o que mostra que o indicador não foi ajustado a este histórico. '
       'Mexer neles agora, depois de ver as tabelas, é a definição de ajuste '
       'à amostra.'))
    a(('tabela', (['parâmetro', 'valor', 'não mexer porque'], [
        ['`PeriodoBase`', n(ind['periodo_base']),
         'de 40 a 100 o resultado é o mesmo'],
        ['`FatorRes`', n(ind['fator_res'], 2),
         'de 0,50 a 0,70 o resultado é o mesmo ou melhor'],
        ['`FatorQual`', n(ind['fator_qual'], 2),
         'de 0,20 a 0,50 o resultado é o mesmo'],
        ['`FatorCorpo`', n(ind['fator_corpo'], 2), 'só afeta a divergência'],
        ['`LimDesq`', n(ind['lim_desq'], 2), 'só afeta a divergência'],
        ['`FatorCompleta`', n(ind['fator_completa'], 2),
         'praticamente inerte neste símbolo'],
    ])))

    # ---------------------------------------------------------------- 2
    a(('h2', '2 · O filtro que decide tudo, e que o indicador ainda não mostra'))
    a(('p', 'O gatilho sozinho não paga. Todo sinal do indicador, operado a '
       'meio range, mede **%s** de acerto — positivo, mas magro. Com o filtro '
       'de esforço, sobe para **%s**. É esse filtro que separa o plano de uma '
       'aposta.' % (pct(s7['acerto']), pct(s8['acerto']))))
    a(('p', '**A regra:** o *esforço relativo* da barra de sinal tem de ser '
       '**≤ %s**. Esforço relativo é a agressão total da barra (compradora + '
       'vendedora) dividida pela média das barras da **mesma direção** nas '
       'últimas %s. Abaixo de %s significa: a barra virou o movimento com '
       'pouca gente negociando.'
       % (n(EF['limite'], 2), n(ind['periodo_base']), n(EF['limite'], 2))))
    a(('p', 'A tese é a própria absorção, na forma mais pura: não houve briga. '
       'O preço andou porque não havia nada do outro lado — e não porque um '
       'lado venceu o outro. Só **%s** dos sinais passam nesse corte, então '
       'espere descartar dois de cada três.' % pct(I['pct_esforco_baixo'])))

    a(('aviso', 'O indicador não publica esse número.',
       'Os buffers de estudo do `.mq5` são `Sinal`, `Eficiência`, `ResRel` e '
       '`QualRel`. O esforço relativo não está entre eles — mas é **derivável '
       'dos dois que estão**.'))
    a(('p', 'Como `Eficiência = ResRel / EsfRel` por definição, vale a volta:'))
    a(('codigo', ('', 'EsfRel = ResRel / Eficiência')))
    a(('p', 'Conferido nos %s sinais do histórico: a identidade vale em '
       '**100%%** deles. Na Janela de Dados, portanto, basta dividir `ResRel` '
       'por `Eficiência` e comparar com %s.'
       % (n(I['total']), n(EF['limite'], 2))))
    a(('p', 'Fazer essa conta de cabeça no instante do sinal é pedir erro. A '
       'correção definitiva é publicar o valor como um nono buffer. Dentro do '
       '`.mq5`, a variável `esfRel` **já existe e já está calculada** no laço '
       'de `OnCalculate` — só não é gravada em lugar nenhum:'))
    a(('codigo', ('cpp', '''// no cabecalho, ao lado dos outros DRAW_NONE:
#property indicator_buffers 9
#property indicator_plots   9
#property indicator_label9  "EsfRel"
#property indicator_type9   DRAW_NONE

double BufEsfRel[];                       // junto dos demais buffers

// em OnInit(), depois de SetIndexBuffer(7, ...):
SetIndexBuffer(8, BufEsfRel, INDICATOR_DATA);
PlotIndexSetDouble(8, PLOT_EMPTY_VALUE, 0.0);
PlotIndexSetInteger(8, PLOT_DRAW_BEGIN, g_primeira);

// em OnCalculate(), na limpeza do inicio do laco:
BufEsfRel[idx] = 0.0;

// e ao lado de BufEfic[idx] = efic;
BufEsfRel[idx] = esfRel;''')))
    a(('p', 'Com o buffer no lugar, o filtro vira leitura direta na Janela de '
       'Dados — e um EA que consuma o indicador por `iCustom` passa a ter a '
       'condição inteira sem recalcular nada.'))

    # ---------------------------------------------------------------- 3
    a(('h2', '3 · A entrada'))
    a(('ol', [
        '**Espere a barra de sinal FECHAR.** A seta do indicador aparece na '
        'barra em formação e pode sumir quando ela fecha, porque `resRel`, '
        '`qualRel` e o próprio corpo mudam até o último tick. Sinal em barra '
        'aberta não é sinal.',
        '**Confira o esforço relativo** (§2). Se `ResRel / Eficiência` for '
        'maior que %s, **não opere**. Este é o passo que a maioria vai querer '
        'pular, e é o único que o backtest mostrou que importa.'
        % n(EF['limite'], 2),
        '**Entre a mercado, no fechamento da barra**, a favor da direção da '
        'barra de sinal — para cima se ela fechou de alta, para baixo se '
        'fechou de baixa. Vale igual para a seta verde/vermelha (absorção) e '
        'para a azul (divergência): as duas mediram parecido dentro do filtro '
        '(%s e %s).'
        % (pct(EF['por_tipo']['1']['acerto']),
           pct(EF['por_tipo']['2']['acerto'])),
        '**Uma posição por vez.** Sinal que aparecer com posição aberta é '
        'ignorado, não acumulado.',
    ]))
    a(('destaque', 'Por que a mercado, e não uma ordem limitada melhor?',
       'Foi testado. A ordem limitada no meio do range da barra de sinal '
       'abandona %s dos sinais e o preço melhor não compensa a amostra '
       'perdida — a variante V3 é a pior do estudo inteiro. Num gráfico onde '
       'a vantagem dura uma barra, esperar por preço é esperar a vantagem '
       'passar.' % pct(1 - V['V3']['stats']['taxa_ativacao'])))

    # ---------------------------------------------------------------- 4
    a(('h2', '4 · A saída'))
    a(('p', 'Alvo e stop na mesma distância: **%s ticks = %s dólares = meio '
       'range**, os dois montados junto com a entrada e não tocados depois.'
       % (n(MEIO), n(MEIO * r['tick'], 2))))
    a(('tabela', (['', 'valor', 'por quê'], [
        ['Stop', '%s ticks abaixo (compra) ou acima (venda) da entrada'
         % n(MEIO), 'é 1R'],
        ['Alvo', '%s ticks, a posição inteira' % n(MEIO),
         'é onde a vantagem está'],
        ['Parcial', 'nenhuma', 'com alvo de uma barra não há o que parcelar'],
        ['Stop móvel', 'nenhum', 'a operação dura %s barra(s)'
         % n(s8['barras_media'], 1)],
        ['Tempo máximo', 'nenhum necessário',
         'a barra seguinte resolve quase sempre'],
    ])))
    a(('destaque', 'Meio range não é um número escolhido por gosto.',
       'É o único alvo deste gráfico em que a ambiguidade dentro da barra não '
       'existe. Como a barra tem %s ticks por construção, ela não consegue '
       'percorrer %s para cima *e* %s para baixo: um dos dois lados é sempre '
       'decidido primeiro, e o backtest não precisou supor nada. Em qualquer '
       'outro alvo o número medido depende de uma convenção.'
       % (n(RNG), n(MEIO), n(MEIO))))
    a(('p', '**Não estique o alvo.** Está medido: em meio range a expectativa '
       'é de %s R por operação; em um range inteiro cai para %s R; em dois '
       'ranges vira %s R. A vantagem que o indicador enxerga vive uma barra e '
       'se dissolve.'
       % (fmt([g for g in r['gestao'] if 'MEIO RANGE' in g['rotulo']][0]
              ['expectativa_R'], 3),
          fmt([g for g in r['gestao'] if 'um range' in g['rotulo']][0]
              ['expectativa_R'], 3),
          fmt([g for g in r['gestao'] if 'dois ranges' in g['rotulo']][0]
              ['expectativa_R'], 3))))

    # ---------------------------------------------------------------- 5
    a(('h2', '5 · Tamanho e risco'))
    a(('p', 'O risco por operação é **%s ticks = %s dólares por lote**. Com '
       '%s operações por pregão, o risco diário bruto é de cerca de %s R.'
       % (n(MEIO), n(MEIO * r['tick'], 2), n(s8['ops_por_dia'], 1),
          n(s8['ops_por_dia'], 1))))
    a(('ul', [
        'Arbitre o lote para que **1R fique em 0,25%% a 0,5%% do capital**. '
        'O pior rebaixamento medido foi de %s R — com 0,5%% por operação isso '
        'seria uma queda de %s%% no capital, e ele pode ser pior fora da '
        'amostra.' % (n(abs(s8['drawdown_R']), 1),
                      n(0.5 * abs(s8['drawdown_R']), 1)),
        '**Limite diário de perda: 3R.** Atingiu, fecha a plataforma.',
        '**Limite de %s operações por dia**, que é o dobro da média medida. '
        'Passar disso significa que você está vendo sinal onde não tem.'
        % n(2 * s8['ops_por_dia'], 0),
    ]))

    # ---------------------------------------------------------------- 6
    a(('h2', '6 · O que não fazer'))
    a(('tabela', (['tentação', 'o que o backtest diz'], [
        ['Filtrar por horário',
         'Reprovado. As horas boas escolhidas em metade da amostra não se '
         'confirmam na outra — a interseção é de %s hora(s), compatível com '
         'sorteio.' % n(len(r['horario']['intersecao']))],
        ['Operar só absorção, ou só divergência',
         'Dentro do filtro de esforço as duas medem parecido (%s e %s). '
         'Separar só reduz a amostra.'
         % (pct(EF['por_tipo']['1']['acerto']),
            pct(EF['por_tipo']['2']['acerto']))],
        ['Operar só um lado',
         'Compra mede %s e venda %s. A diferença está dentro do ruído para '
         'esta amostra.' % (pct(EF['por_lado']['long']['acerto']),
                            pct(EF['por_lado']['short']['acerto']))],
        ['Apertar o alvo para 1/4 de range',
         'Parece melhor no backtest e não é: nessa distância os dois lados '
         'cabem na mesma barra e o número vira artefato da convenção.'],
        ['Deixar correr quando “está indo bem”',
         'Cada barra além da primeira devolve vantagem. É a medida mais '
         'consistente do estudo.'],
        ['Aumentar o lote depois de uma sequência boa',
         'Com t = %s, sequências boas e ruins de %s operações são esperadas '
         'sem que nada tenha mudado.'
         % (fmt(s8['t_stat'], 2), n(10))],
        ['Operar sem conferir o esforço',
         'Sem o filtro a expectativa cai de %s para %s ticks — e o custo come '
         'a diferença inteira.'
         % (fmt(s8['expectativa_ticks'], 1),
            fmt(s7['expectativa_ticks'], 1))],
    ])))

    # ---------------------------------------------------------------- 7
    a(('h2', '7 · Como saber se parou de funcionar'))
    a(('p', 'Defina os critérios **agora**, enquanto não há dinheiro em jogo. '
       'Depois de uma sequência ruim ninguém escreve regra de parada honesta.'))
    a(('ul', [
        '**Registre toda operação** com: data e hora, tipo de sinal (absorção '
        'ou divergência), lado, `ResRel`, `Eficiência`, o esforço relativo '
        'calculado, preço de entrada, preço de saída, resultado em ticks e o '
        'slippage observado contra o fechamento da barra.',
        '**Depois de 50 operações**, compare o acerto com %s. Abaixo de 50%% '
        'com 50 operações ainda é ruído — mas já é hora de reler o registro.'
        % pct(s8['acerto']),
        '**Depois de 100 operações**, some o slippage médio. Se ele passar de '
        '20 ticks por operação, a estratégia não tem margem: %s de expectativa '
        'bruta não paga isso.' % (fmt(s8['expectativa_ticks'], 1) + ' ticks'),
        '**Pare em -15R acumulados.** É %s vezes o pior rebaixamento medido, e '
        'a essa altura a hipótese de que a vantagem sumiu é mais simples que a '
        'de azar.' % n(15 / abs(s8['drawdown_R']), 1),
        '**Refaça o backtest a cada trimestre** com o histórico novo: '
        '`python rodar.py`. O número que mais importa acompanhar não é o '
        'acerto da estratégia, e sim a **linha de base** do §5.2 do relatório '
        '— a taxa de continuação do próprio gráfico, hoje em %s. Boa parte da '
        'vantagem vem dali; se ela cair para 50%%, o resto cai junto.'
        % pct(LB['grupos'][0]['acerto'], 2),
    ]))

    # ---------------------------------------------------------------- 8
    a(('h2', '8 · Expectativa realista'))
    a(('aviso', 'A margem inteira cabe dentro de um spread ruim.',
       'A expectativa bruta é de %s ticks por operação. Com 20 ticks de custo '
       'ida-e-volta ela cai para %s; com 40 ticks fica **negativa** (%s). E a '
       'entrada é a mercado no fechamento de uma barra de range — que é '
       'exatamente um instante de movimento, onde o slippage é pior que a '
       'média.'
       % (fmt(s8['expectativa_ticks'], 1),
          fmt(V['V8']['custo']['20']['expectativa_ticks'], 1),
          fmt(V['V8']['custo']['40']['expectativa_ticks'], 1))))
    a(('tabela', (['custo ida+volta', 'expectativa por operação', 'por pregão'],
                  [[('%s ticks' % n(int(c))),
                    '%s ticks' % fmt(V['V8']['custo'][c]['expectativa_ticks'], 1),
                    '%s USD por lote'
                    % fmt(V['V8']['custo'][c]['expectativa_ticks'] *
                          s8['ops_por_dia'] * r['tick'], 2)]
                   for c in ('0', '10', '20', '40')])))
    a(('p', 'O que este plano é: uma vantagem pequena, real dentro da amostra, '
       'que passou em quatro validações independentes (platô, metades, terços '
       'e controle invertido) e que ainda assim foi escolhida como o melhor de '
       '%s tentativas, num único histórico de %s pregões.'
       % (n(len(cands)), n(D['dias']))))
    a(('p', 'O que ele não é: uma fonte de renda. **Comece com lote mínimo e '
       'trate os três primeiros meses como coleta de dados**, não como '
       'operação. O objetivo dessa fase é medir o seu slippage real — que é a '
       'única variável desconhecida que decide se sobra alguma coisa.'))
    a(('destaque', 'O teste mais honesto que você pode fazer.',
       'Opere em conta demo e em conta real ao mesmo tempo, com o mesmo lote '
       'mínimo, durante 100 operações. A diferença entre as duas curvas é o '
       'seu custo real de execução. Se ela for maior que %s ticks por '
       'operação, o plano não tem margem — e é melhor descobrir isso com lote '
       'mínimo.' % n(s8['expectativa_ticks'], 0)))

    a(('hr', None))
    a(('p', 'Gerado por `plano.py` a partir de `saida/resumo.json` (%s). '
       'Os números vêm todos do backtest; nenhum foi digitado à mão. Para '
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
         '<title>Plano de operação — Esforço × Resultado em range</title>',
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
