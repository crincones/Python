# -*- coding: utf-8 -*-
"""
Escreve PLANO.md e plano.html a partir de saida/resumo.json.

    python plano.py

O plano e escrito UMA vez, numa lista de blocos, e renderizado nos dois
formatos. Assim os dois arquivos nunca divergem, e nenhum numero e digitado
a mao: todos vem do resumo.json gravado por rodar.py.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


# --------------------------------------------------------------------------
def n(x, casas=0):
    return format(float(x), ',.%df' % casas) \
        .replace(',', '@').replace('.', ',').replace('@', '.')


def fmt(x, casas=0):
    return format(float(x), '+,.%df' % casas) \
        .replace(',', '@').replace('.', ',').replace('@', '.')


def pct(x, casas=1):
    return n(100 * x, casas) + '%'


# --------------------------------------------------------------------------
# conversao do texto embutido (markdown simples) para HTML
# --------------------------------------------------------------------------
def inline_html(t):
    t = (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])_([^_]+)_(?![\w*])', r'<em>\1</em>', t)
    return t


def para_md(blocos):
    L = []
    for tipo, x in blocos:
        if tipo == 'h1':
            L += ['# ' + x, '']
        elif tipo == 'h2':
            L += ['## ' + x, '']
        elif tipo == 'h3':
            L += ['### ' + x, '']
        elif tipo == 'p':
            L += [x, '']
        elif tipo == 'nota':
            L += ['> ' + x.replace('\n', '\n> '), '']
        elif tipo == 'aviso':
            L += ['> ⚠️ ' + x.replace('\n', '\n> '), '']
        elif tipo == 'ul':
            L += ['- ' + i for i in x] + ['']
        elif tipo == 'ol':
            L += ['%d. %s' % (i + 1, v) for i, v in enumerate(x)] + ['']
        elif tipo == 'tabela':
            cab, linhas = x
            L += ['| ' + ' | '.join(cab) + ' |',
                  '|' + '|'.join(['---'] * len(cab)) + '|']
            L += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in linhas]
            L += ['']
        elif tipo == 'hr':
            L += ['---', '']
        elif tipo == 'campo':
            L += ['`%s`  ' % ('_' * 40), '']
    return '\n'.join(L) + '\n'


def para_html(blocos):
    L = []
    for tipo, x in blocos:
        if tipo == 'h1':
            L.append('<h1>%s</h1>' % inline_html(x))
        elif tipo == 'h2':
            L.append('<h2 id="%s">%s</h2>'
                     % (re.sub(r'[^a-z0-9]+', '-', x.lower())[:40], inline_html(x)))
        elif tipo == 'h3':
            L.append('<h3>%s</h3>' % inline_html(x))
        elif tipo == 'p':
            L.append('<p>%s</p>' % inline_html(x))
        elif tipo == 'nota':
            L.append('<div class="destaque"><p>%s</p></div>' % inline_html(x))
        elif tipo == 'aviso':
            L.append('<div class="aviso"><p>%s</p></div>' % inline_html(x))
        elif tipo == 'ul':
            L.append('<ul>%s</ul>'
                     % ''.join('<li>%s</li>' % inline_html(i) for i in x))
        elif tipo == 'ol':
            L.append('<ol>%s</ol>'
                     % ''.join('<li>%s</li>' % inline_html(i) for i in x))
        elif tipo == 'tabela':
            cab, linhas = x
            def cel(c, tag='td'):
                c = str(c)
                # numero curto vai alinhado a direita; texto corrido, a esquerda
                k = ' class="num"' if re.fullmatch(
                    r'[\s\-−+0-9.,%RtUSDonçaslote()]{0,22}', c) else ''
                return '<%s%s>%s</%s>' % (tag, k, inline_html(c), tag)
            L.append('<div class="rolagem"><table><thead><tr>%s</tr></thead><tbody>%s'
                     '</tbody></table></div>'
                     % (''.join(cel(c, 'th') for c in cab),
                        ''.join('<tr>%s</tr>' % ''.join(cel(c) for c in r)
                                for r in linhas)))
        elif tipo == 'hr':
            L.append('<hr>')
        elif tipo == 'campo':
            L.append('<div class="campo"></div>')
    return '\n'.join(L)


CSS = """
:root{--tinta:#1b1f24;--tinta2:#5b6570;--fundo:#fbfaf7;--papel:#fff;
 --linha:#e2ddd4;--realce:#8a6a2f;--alta:#1a7f5a;--baixa:#b3453a;--caixa:#f5f2ec}
@media (prefers-color-scheme:dark){:root{--tinta:#e8e6e1;--tinta2:#9aa2ab;
 --fundo:#14171a;--papel:#1b1f23;--linha:#2e343a;--realce:#d9ae5e;
 --alta:#3fbb8a;--baixa:#e0685c;--caixa:#20262c}}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--tinta);
 font:16px/1.62 Georgia,'Times New Roman',serif}
.env{max-width:820px;margin:0 auto;padding:52px 22px 90px}
h1{font-size:32px;line-height:1.2;margin:0 0 6px;letter-spacing:-.4px}
h2{font-size:22px;margin:46px 0 6px;padding-top:15px;
 border-top:1px solid var(--linha)}
h3{font-size:17px;margin:26px 0 4px}
p{margin:11px 0}
ul,ol{margin:11px 0;padding-left:22px}li{margin:5px 0}
code{font:13px ui-monospace,Consolas,monospace;background:var(--caixa);
 padding:1px 5px;border-radius:3px}
a{color:var(--realce)}
.destaque{background:var(--caixa);border-left:3px solid var(--realce);
 padding:13px 17px;margin:20px 0;border-radius:0 5px 5px 0}
.destaque p{margin:0}
.aviso{border:1px solid var(--baixa);border-radius:7px;padding:13px 17px;
 margin:20px 0;background:color-mix(in srgb,var(--baixa) 7%,transparent)}
.aviso p{margin:0}
.rolagem{overflow-x:auto;margin:16px 0}
table{border-collapse:collapse;width:100%;min-width:420px;
 font:13.5px/1.45 system-ui,-apple-system,sans-serif}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--linha);
 vertical-align:top}
th.num,td.num{text-align:right;font-variant-numeric:tabular-nums;
 white-space:nowrap}
th:first-child,td:first-child{text-align:left}
thead th{border-bottom:1.5px solid var(--tinta);color:var(--tinta2);
 text-transform:uppercase;font-size:11px;letter-spacing:.06em}
.campo{border-bottom:1px solid var(--linha);height:26px;margin:8px 0}
hr{border:0;border-top:1px solid var(--linha);margin:34px 0}
.sub{color:var(--tinta2);font:14px/1.5 system-ui,sans-serif;margin:0 0 6px}
@media print{body{background:#fff;color:#000}.env{padding:0}
 h2{page-break-after:avoid}table{page-break-inside:avoid}}
"""


# --------------------------------------------------------------------------
def montar(r):
    V = {v['nome']: v for v in r['variantes']}
    P = V['V7']                       # o plano opera a V7
    A = V['V5']                       # a alternativa que mantem o runner
    D = r['dados']
    s = P['stats']
    rg = D['range_ticks']
    horas = r['horas_boas']
    horas_txt = ', '.join('%02dh' % h for h in horas)
    B = []
    b = B.append

    b(('h1', 'Plano de operação manual — leque de EMAs em XAUUSD 521 ticks'))
    b(('p', 'Versão de %s. Baseado em `RESULTADOS.md`, que mede %s barras em '
            '%s pregões. Este plano descreve a variante **V7** do backtest — a '
            'única que continuou positiva depois de descontar custo.'
      % (r['gerado_em'][:10], n(D['barras']), n(D['dias']))))

    # ---------------------------------------------------------------- 0
    b(('h2', '0 · Leia isto antes de tudo'))
    b(('aviso',
       'A estratégia original, como está escrita em `ESTRATEGIA.md`, **perde '
       'dinheiro** neste histórico: %s por operação em %s operações. E o gatilho '
       'não tem leitura de direção — a excursão do preço depois da entrada é '
       'estatisticamente igual à de uma entrada sorteada. Este plano não é a '
       'estratégia validada; é o **resto que sobrou** depois de tirar o que '
       'estava medindo negativo, e ele se sustenta sobre %s operações apenas.'
       % (fmt(V['V0']['stats']['expectativa_ticks'], 1) + ' ticks',
          n(V['V0']['stats']['operacoes']), n(s['operacoes']))))
    b(('p', 'O que mudou em relação ao texto original, e por quê:'))
    b(('tabela', (['no texto original', 'neste plano', 'por quê'], [
        ['opera a qualquer hora',
         'só em %s' % horas_txt,
         'é a única restrição que passou em validação fora da amostra, '
         'nos dois sentidos'],
        ['o candle de gatilho só precisa aparecer no leque',
         'ele tem de **fechar** além da EMA21',
         'elimina o caso ambíguo da barra que encosta na média e fecha do lado '
         'errado'],
        ['parcial de 50% em 300 e o resto até 900',
         '**100% da posição sai em 300**',
         'só %s das operações chegavam aos 900; o runner era o que consumia o '
         'resultado' % pct(V['V0']['stats']['motivos'].get('alvo', 0) /
                           V['V0']['stats']['operacoes'])],
        ['limitar o tamanho do candle de reversão',
         'sem limite',
         'medido: as barras grandes mediram melhor que as pequenas, não pior'],
    ])))

    # ---------------------------------------------------------------- 1
    b(('h2', '1 · A configuração da tela'))
    b(('ul', [
        'Ativo **XAUUSD**, gráfico de **521 ticks**.',
        'Três médias móveis **exponenciais** sobre o fechamento: '
        '**21**, **42** e **72**. Cores distintas; a de 21 é a que importa.',
        'Escala vertical em dólares. Marque no papel que **1 tick = 0,01 USD** '
        'e que **300 ticks = 3,00 USD = 1R**.',
        'Relógio do gráfico configurado no mesmo fuso do arquivo usado no '
        'backtest. **Confirme isso antes da primeira operação** — se o fuso for '
        'outro, todo o filtro de horário deste plano aponta para as horas '
        'erradas.',
    ]))
    b(('nota',
       'Referência de tamanho, para calibrar o olho: a barra mediana deste '
       'gráfico anda **%s ticks**. O stop de 300 ticks é pouco mais de **uma** '
       'barra mediana. Se um candle de gatilho tem 600 ticks de range, o stop '
       'cabe dentro dele — isso não impede a operação, mas explica por que ela '
       'morre rápido.' % n(rg['50%'])))

    # ---------------------------------------------------------------- 2
    b(('h2', '2 · Quando olhar — a janela de operação'))
    b(('p', 'Opere **somente** dentro destas horas. Fora delas, o gráfico fica '
            'fechado: %s.' % horas_txt))
    tab = []
    for p in r['horario']['por_hora']:
        if p['hora'] in horas:
            tab.append(['%02dh' % p['hora'], n(p['n']),
                        pct(p['acerto']), fmt(p['expectativa_ticks'], 0) + ' t'])
    b(('tabela', (['hora', 'sinais no histórico', 'acerto', 'expectativa'], tab)))
    b(('p', '_Medido sobre a regra literal com a métrica neutra de 1:1 — é o '
            'corte que define a janela, e não o desempenho da V7 hora a hora, '
            'que teria poucas operações por hora para significar algo._'))
    b(('p', 'São %s horas de %s. Na prática isso significa **%s operações por '
            'pregão**, em média — e vários pregões sem nenhuma. A disciplina de '
            'não operar fora da janela é a parte mais valiosa e a mais difícil '
            'deste plano.'
      % (n(len(horas)), n(len(D['horas'])), n(s['ops_por_dia'], 1))))

    # ---------------------------------------------------------------- 3
    b(('h2', '3 · O setup, passo a passo'))
    b(('p', 'As cinco condições abaixo têm de valer **todas**, na ordem. Se uma '
            'falhar, não há operação — não existe "quase".'))
    b(('ol', [
        '**Leque formado.** As três EMAs ordenadas: 21 acima de 42 acima de 72 '
        '(vou comprar), ou 21 abaixo de 42 abaixo de 72 (vou vender). Se as '
        'médias estão cruzadas ou coladas, não há leque — passe.',
        '**O preço se afastou.** Nas últimas ~12 barras houve pelo menos uma '
        'barra **inteira** do lado de fora da EMA21, no sentido da tendência. '
        'Se o preço está grudado nas médias há dez barras, não houve '
        'afastamento — passe.',
        '**Voltou ao leque com 2 ou 3 candles da mesma cor.** O recuo é '
        'contrário à tendência: em leque de alta, 2 ou 3 candles vermelhos '
        'seguidos; em leque de baixa, 2 ou 3 verdes. **Nem 1, nem 4.** '
        'Quatro candles seguidos não é pullback, é reversão — passe.',
        '**O candle de gatilho aparece.** O primeiro candle de cor contrária ao '
        'recuo (ou seja, da cor da tendência), que **toca a EMA21** e '
        '**fecha do lado da tendência** — acima da EMA21 para comprar, abaixo '
        'para vender. Se ele toca mas fecha do lado errado, não é gatilho.',
        '**A hora está na janela** (§ 2). Este é o filtro que se esquece de '
        'checar; cheque.',
    ]))
    b(('nota',
       'Nenhuma condição envolve o tamanho do candle de gatilho. Foi testado e '
       'medido: pôr teto no range da barra de reversão **piorou** o resultado. '
       'Deixe passar o candle grande.'))

    # ---------------------------------------------------------------- 4
    b(('h2', '4 · A ordem'))
    b(('ol', [
        'Meça o **meio do range do candle de gatilho**: `(máxima + mínima) / 2`.',
        'Coloque uma ordem **limitada** nesse preço — compra se o leque é de '
        'alta, venda se é de baixa.',
        'A ordem vale por **uma barra**. Se a barra seguinte não tocar o preço, '
        '**cancele**. Não persiga, não role para a barra seguinte, não entre a '
        'mercado.',
        'Se ela ativar, monte imediatamente o stop e o alvo da § 5.',
    ]))
    b(('p', 'No histórico, **%s** dos gatilhos não ativam e viram nada. Isso é '
            'o desenho funcionando, não uma oportunidade perdida: a ordem '
            'limitada é o que faz o preço de entrada ser melhor que o '
            'fechamento do gatilho.'
      % pct(1 - V['V0']['stats']['taxa_ativacao'])))

    # ---------------------------------------------------------------- 5
    b(('h2', '5 · Stop e alvo'))
    b(('tabela', (['', 'distância', 'em dólares', 'em R'], [
        ['**Stop**', '%s ticks' % n(P['cfg']['stop_ticks']),
         '%s USD' % n(P['cfg']['stop_ticks'] * 0.01, 2), '−1R'],
        ['**Alvo**', '%s ticks' % n(P['cfg']['parcial_ticks']),
         '%s USD' % n(P['cfg']['parcial_ticks'] * 0.01, 2), '+1R'],
    ])))
    b(('ul', [
        '**A posição inteira sai no alvo.** Sem parcial, sem runner, sem mover '
        'o stop para o breakeven.',
        'Stop e alvo entram na corretora **assim que a ordem ativa**, os dois '
        'juntos, como OCO. Depois disso a operação é da máquina, não sua.',
        'Não existe saída manual "porque o candle ficou feio". A vantagem '
        'medida é pequena; ela desaparece inteira se você fechar as vencedoras '
        'antes do alvo.',
    ]))
    b(('nota',
       'Esta é a mudança mais importante em relação ao plano original, e a mais '
       'contraintuitiva: **o alvo de 900 ticks era o que quebrava a '
       'estratégia**. Ele exige %s barras medianas de continuação, e só chegava '
       'lá em %s das operações. A parcial em 300 com stop no breakeven, por sua '
       'vez, transformava a maioria das vencedoras em meio ganho. Sair inteiro '
       'em 300 é feio no papel — relação 1:1 — mas é o que mede positivo.'
       % (n(900 / rg['50%'], 1),
          pct(V['V0']['stats']['motivos'].get('alvo', 0) /
              V['V0']['stats']['operacoes']))))
    b(('h3', 'Se quiser manter o 2:1 do plano original'))
    b(('p', 'A variante V5 mantém a parcial de 50%% em 300 com stop no '
            'breakeven e o runner até 900. Ela também mede positivo, mas menos: '
            '%s ticks por operação contra %s da V7, e — o que mais importa — '
            'ela **fica negativa** (%s ticks) com 40 ticks de custo, enquanto a '
            'V7 continua em %s. Se optar pela V5, saiba que está trocando '
            'expectativa por uma estética de relação risco/retorno.'
      % (fmt(A['stats']['expectativa_ticks'], 1),
         fmt(s['expectativa_ticks'], 1),
         fmt(A['custo']['40'].get('expectativa_ticks', 0), 1),
         fmt(P['custo']['40'].get('expectativa_ticks', 0), 1))))

    # ---------------------------------------------------------------- 6
    b(('h2', '6 · Tamanho da posição'))
    b(('p', 'Regra única: **arrisque 0,25% da conta por operação** enquanto este '
            'plano estiver em teste. Não 1%, não 2%. O motivo está na § 8: a '
            'vantagem medida é pequena e a amostra é curta, então o tamanho tem '
            'de ser o de um experimento, não o de uma convicção.'))
    risco_onca = P['cfg']['stop_ticks'] * 0.01
    b(('p', 'A conta é direta, porque o stop é fixo em %s ticks: **cada onça de '
            'ouro na posição arrisca %s USD**. Divida o risco da operação por '
            'esse número e terá o tamanho em onças.'
      % (n(P['cfg']['stop_ticks']), n(risco_onca, 2))))
    linhas = []
    for conta in (1000, 5000, 10000, 25000):
        risco = conta * 0.0025
        oncas = risco / risco_onca
        dia = s['expectativa_R'] * s['ops_por_dia'] * risco
        linhas.append(['%s USD' % n(conta), '%s USD' % n(risco, 2),
                       n(oncas, 2), n(oncas / 100, 3),
                       '%s USD' % fmt(dia, 2)])
    b(('tabela', (['conta', 'risco por operação (0,25%)', 'tamanho em onças',
                   'em lotes padrão (100 oz)',
                   'resultado esperado por pregão'], linhas)))
    b(('aviso', 'Confirme com a sua corretora quantas onças tem um lote. Em '
                'MetaTrader o lote padrão de XAUUSD costuma ser **100 onças** e '
                'o mínimo, 0,01 lote = 1 onça — mas há corretoras que usam 10. '
                'Errar essa conversão multiplica ou divide o risco por dez.'))
    b(('p', '_A última coluna usa a expectativa medida de %s por operação, ou '
            '%s de R, e %s operações por pregão. É uma projeção da média, não '
            'uma promessa: a distribuição real tem desvio-padrão de %s ticks por '
            'operação, dez vezes a média._'
      % (fmt(s['expectativa_ticks'], 1) + ' ticks',
         fmt(s['expectativa_R'], 3), n(s['ops_por_dia'], 1),
         n(s['desvio_ticks'], 0))))

    # ---------------------------------------------------------------- 7
    b(('h2', '7 · Limites do dia e da semana'))
    b(('ul', [
        '**Três stops no mesmo pregão: encerra o dia.** Sem exceção, sem '
        '"recuperar".',
        '**Perda de 2R no dia: encerra o dia**, mesmo que sejam duas operações.',
        '**Perda de 6R na semana: encerra a semana.** Volta na segunda-feira '
        'seguinte.',
        '**Nenhuma operação nova a menos de 10 minutos do fim da janela** da '
        'hora — a operação típica dura %s barras, e barra de 521 ticks não tem '
        'duração fixa.' % n(s['barras_media'], 1),
        '**Nada de operar em dia de dado macro de peso** (decisão de juros, '
        'payroll, CPI) na hora do anúncio. O backtest inclui esses dias e não '
        'os separa; o slippage real deles não está medido em lugar nenhum '
        'deste estudo.',
    ]))
    b(('p', 'No histórico o pior dia da variante foi de %s ticks e o maior '
            'rebaixamento acumulado foi de %s ticks, ou %s R. Um rebaixamento '
            'dessa ordem **vai** acontecer; o limite acima existe para que ele '
            'aconteça com você ainda na cadeira.'
      % (fmt(s['pior_dia'], 0), fmt(s['drawdown_ticks'], 0),
         fmt(s['drawdown_R'], 1))))

    # ---------------------------------------------------------------- 8
    b(('h2', '8 · O que esperar — números honestos'))
    b(('tabela', (['', 'V7 (este plano)', 'V5 (com runner)', 'V0 (regra original)'], [
        ['Operações no histórico'] + [n(x['stats']['operacoes']) for x in (P, A, V['V0'])],
        ['Operações por pregão'] + [n(x['stats']['ops_por_dia'], 1) for x in (P, A, V['V0'])],
        ['Acerto'] + [pct(x['stats']['acerto']) for x in (P, A, V['V0'])],
        ['Expectativa por operação'] +
        ['%s t' % fmt(x['stats']['expectativa_ticks'], 1) for x in (P, A, V['V0'])],
        ['Expectativa em R'] +
        [fmt(x['stats']['expectativa_R'], 3) for x in (P, A, V['V0'])],
        ['Fator de lucro'] + [n(x['stats']['fator_lucro'], 2) for x in (P, A, V['V0'])],
        ['Rebaixamento máximo'] +
        ['%s t' % fmt(x['stats']['drawdown_ticks'], 0) for x in (P, A, V['V0'])],
        ['Com 20 ticks de custo'] +
        ['%s t' % fmt(x['custo']['20'].get('expectativa_ticks', 0), 1)
         for x in (P, A, V['V0'])],
        ['Com 40 ticks de custo'] +
        ['%s t' % fmt(x['custo']['40'].get('expectativa_ticks', 0), 1)
         for x in (P, A, V['V0'])],
        ['1ª metade da amostra'] +
        ['%s t' % fmt(x['metades']['1a'].get('expectativa_ticks', 0), 1)
         for x in (P, A, V['V0'])],
        ['2ª metade da amostra'] +
        ['%s t' % fmt(x['metades']['2a'].get('expectativa_ticks', 0), 1)
         for x in (P, A, V['V0'])],
    ])))
    b(('p', 'Duas leituras que valem mais que a linha da expectativa:'))
    b(('ul', [
        '**O custo decide.** A vantagem inteira cabe dentro do spread. Antes de '
        'operar, meça o custo real da sua corretora em ouro: some spread médio '
        'e comissão, em ticks, ida e volta. Se der acima de 40, este plano não '
        'tem margem — não opere.',
        '**A amostra é curta.** %s operações dão um erro-padrão de expectativa '
        'de cerca de %s ticks por operação, sobre uma expectativa de %s. Ou '
        'seja: o intervalo de confiança encosta perto do zero.'
        % (n(s['operacoes']),
           n(s['desvio_ticks'] / (s['operacoes'] ** 0.5), 0),
           n(s['expectativa_ticks'], 0)),
    ]))

    # ---------------------------------------------------------------- 9
    b(('h2', '9 · Rotina do pregão'))
    b(('h3', 'Antes (5 minutos)'))
    b(('ul', [
        'Confirmar o fuso do gráfico e escrever no papel as horas de hoje.',
        'Conferir a agenda de indicadores e riscar as horas que caem em cima de '
        'um anúncio.',
        'Escrever o risco em dólares por operação (0,25% da conta de hoje) e o '
        'tamanho em onças correspondente (§ 6).',
        'Escrever os limites: 3 stops, −2R no dia.',
    ]))
    b(('h3', 'Durante'))
    b(('ul', [
        'Fora da janela, o gráfico fica fechado. Literalmente: minimize.',
        'Dentro da janela, olhar só o fechamento das barras. A regra é toda de '
        'fechamento — não há decisão a tomar com a barra em formação.',
        'Ao ver um gatilho: conferir as cinco condições da § 3 **em voz alta** '
        'antes de mandar a ordem.',
        'Ordem enviada: anotar na planilha antes de qualquer outra coisa.',
        'Ordem não ativada na barra seguinte: cancelar e anotar como abortada. '
        'Elas contam.',
    ]))
    b(('h3', 'Depois (5 minutos)'))
    b(('ul', [
        'Fechar a linha de cada operação na planilha, inclusive as abortadas.',
        'Uma frase sobre qualquer momento em que a regra foi quebrada. Se não '
        'houve, escrever "nenhuma".',
        'Uma vez por semana: comparar acerto e expectativa acumulados com a '
        'tabela da § 8.',
    ]))

    # --------------------------------------------------------------- 10
    b(('h2', '10 · A planilha'))
    b(('p', 'Uma linha por sinal — **inclusive os que não ativaram**, porque a '
            'taxa de ativação é uma das coisas que este plano precisa verificar '
            'em tempo real.'))
    b(('tabela', (['data', 'hora', 'lado', 'preço da ordem', 'ativou?',
                   'entrada', 'saída', 'ticks', 'R', 'regra quebrada?'],
                  [['', '', '', '', '', '', '', '', '', ''] for _ in range(3)])))
    b(('p', 'Colunas calculadas ao fim de cada semana: número de sinais, taxa de '
            'ativação, acerto, expectativa em ticks e em R, e o acumulado em R.'))

    # --------------------------------------------------------------- 11
    b(('h2', '11 · Critério de parada — escrito antes de começar'))
    b(('p', 'Este plano é um **teste**, e teste precisa de um critério de '
            'encerramento definido antes, quando ainda não dói. Os três abaixo '
            'valem simultaneamente:'))
    b(('ol', [
        '**Ao fim de 100 operações**, comparar a expectativa medida com a do '
        'backtest (%s ticks). Se estiver negativa, o teste terminou: a vantagem '
        'não existia. Se estiver positiva mas abaixo da metade, ela existe e é '
        'menor do que o custo de operar — o que dá no mesmo.'
        % fmt(s['expectativa_ticks'], 1),
        '**Rebaixamento de 10R** desde o pico da curva: parar e revisar. É mais '
        'que o rebaixamento máximo do backtest (%s R), então indica que alguma '
        'coisa mudou ou que o backtest era otimista.' % n(abs(s['drawdown_R']), 1),
        '**Taxa de ativação muito diferente de %s**: se as ordens estão '
        'ativando muito mais, você está entrando a mercado sem perceber; muito '
        'menos, e o preço da ordem está sendo calculado errado. Nos dois casos '
        'o que você opera não é o que foi medido.'
        % pct(P['stats']['taxa_ativacao'], 0),
    ]))
    b(('hr', ''))
    b(('p', '_Gerado por `plano.py` a partir de `saida/resumo.json`. Os números '
            'vêm todos do backtest documentado em `RESULTADOS.md` e '
            '`relatorio.html`._'))
    return B


# --------------------------------------------------------------------------
def escrever():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        r = json.load(f)
    B = montar(r)

    md = os.path.join(BASE, 'PLANO.md')
    with open(md, 'w', encoding='utf-8') as f:
        f.write(para_md(B))

    corpo = para_html(B)
    html = ('<!doctype html>\n<html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Plano de operação — XAUUSD 521 ticks</title>'
            '<style>%s</style></head><body><div class="env">%s</div>'
            '</body></html>' % (CSS, corpo))
    with open(os.path.join(BASE, 'plano.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print('PLANO.md e plano.html gravados.')


if __name__ == '__main__':
    escrever()
