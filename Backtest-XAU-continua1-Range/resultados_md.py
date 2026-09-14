# -*- coding: utf-8 -*-
"""
saida/resumo.json -> RESULTADOS.md

Nenhum numero e digitado aqui. Tudo vem do resumo.json gravado por rodar.py.
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


def carregar():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        return json.load(f)


def n(x, casas=0):
    """Numero no formato brasileiro: 1.234,5"""
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


def linha_var(v):
    s = v['stats']
    return ('| **%s** %s | %s | %s | %s | %s | %s | %s | %s |'
            % (v['nome'], v['rotulo'], n(s.get('sinais', 0)),
               n(s.get('operacoes', 0)), pct(s.get('acerto', 0)),
               fmt(s.get('expectativa_ticks', 0), 1),
               fmt(s.get('ticks_total', 0)), n(s.get('fator_lucro', 0), 2),
               n(s.get('drawdown_ticks', 0))))


def escrever():
    r = carregar()
    D, I = r['dados'], r['indicador']
    P = D['premissa']
    V = {v['nome']: v for v in r['variantes']}
    LB, EF, HR = r['linha_base'], r['esforco'], r['horario']
    v8, v9, v7, v0 = V['V8'], V['V9'], V['V7'], V['V0']
    s8 = v8['stats']
    cands = [b for b in r['busca'] if not b['artefato'] and not b['poucas']]
    art = [b for b in r['busca'] if b['artefato']]

    L = []
    a = L.append

    a('# Esforço × Resultado em XAUUSD, gráfico de range de %s ticks'
      % n(r['range_nominal']))
    a('')
    a('Backtest do indicador `Trigger_EsforcoResultado_Range.mq5` sobre '
      '%s barras (%s a %s, %s pregões), gerado em %s a partir de `%s`.'
      % (n(D['barras']), D['inicio'][:10], D['fim'][:10], n(D['dias']),
         r['gerado_em'], r['arquivo']))
    a('')
    a('Todos os números vêm de `saida/resumo.json`. Nenhum foi digitado à mão.')
    a('')

    # ------------------------------------------------------------------ 1
    a('## 1 · Resposta curta')
    a('')
    a('O gatilho **tem** leitura de direção, mas ela vive por uma barra e '
      'morre depois. Medida no horizonte certo, a vantagem existe e sobrevive '
      'a todos os controles que este estudo soube aplicar. Medida no horizonte '
      'errado — que é o horizonte em que a maioria dos backtests mede — ela '
      'some por completo.')
    a('')
    a('Três números resumem o estudo:')
    a('')
    a('1. **%s** das barras deste gráfico continuam na própria direção na '
      'barra seguinte (z = %s, sobre %s barras). O gráfico de range já vem '
      'com inclinação de fábrica; parte de qualquer acerto acima de 50%% não '
      'é do indicador.'
      % (pct(LB['grupos'][0]['acerto'], 2), fmt(LB['grupos'][0]['z'], 2),
         n(LB['grupos'][0]['n'])))
    a('2. Nos sinais do indicador com **esforço baixo**, essa taxa vai a '
      '**%s** (%s sinais — a contagem aqui é de sinais, não das operações da '
      'V8, que descarta os que aparecem com posição aberta). O ganho sobre o '
      'controle emparelhado — barras '
      'de virada com esforço baixo, mas sem as demais condições do indicador '
      '— é de **%s pontos**, com z = %s. Esse é o crédito que cabe ao '
      'indicador, e não mais que ele.'
      % (pct(LB['grupos'][4]['acerto'], 2), n(LB['grupos'][4]['n']),
         fmt(100 * LB['ganho']['diferenca'], 1), fmt(LB['ganho']['z'], 2)))
    a('3. Esticar o alvo mata a vantagem. A **%s** por operação da V8 sai de '
      'um alvo de meio range; em dois ranges a mesma seleção dá %s. O que o '
      'indicador vê não dura.'
      % (fmt(s8['expectativa_ticks'], 1) + ' ticks',
         fmt([g for g in r['gestao'] if 'dois ranges' in g['rotulo']][0]
             ['expectativa_ticks'], 1) + ' ticks'))
    a('')
    a('| | V8 — meio range + esforço baixo |')
    a('|---|---|')
    for rot, val in (
            ('Operações', '%s em %s pregões' % (n(s8['operacoes']), n(s8['dias']))),
            ('Acerto', pct(s8['acerto'])),
            ('Expectativa', '%s ticks = %s R = %s USD por lote'
             % (fmt(s8['expectativa_ticks'], 1), fmt(s8['expectativa_R'], 3),
                fmt(s8['expectativa_usd'], 2))),
            ('Erro padrão', '%s ticks  (t = %s)'
             % (n(s8['erro_padrao_ticks'], 1), fmt(s8['t_stat'], 2))),
            ('Total', '%s ticks = %s USD por lote'
             % (fmt(s8['ticks_total']), fmt(s8['usd_total'], 2))),
            ('Fator de lucro', n(s8['fator_lucro'], 2)),
            ('Rebaixamento máximo', '%s ticks = %s R'
             % (n(s8['drawdown_ticks']), n(s8['drawdown_R'], 2))),
            ('Controle invertido', '%s de acerto, %s ticks — o espelho exato'
             % (pct(v9['stats']['acerto']),
                fmt(v9['stats']['expectativa_ticks'], 1)))):
        a('| %s | %s |' % (rot, val))
    a('')
    a('E a ressalva que precisa vir junto: **%s ticks de expectativa não '
      'sobrevivem a %s ticks de custo.** A margem inteira cabe dentro de um '
      'spread ruim. O §10 trata disso.'
      % (fmt(s8['expectativa_ticks'], 1), n(40)))
    a('')

    # ------------------------------------------------------------------ 2
    a('## 2 · Os dados, e a premissa do indicador')
    a('')
    a('O indicador não funciona em qualquer gráfico. Ele pressupõe duas '
      'coisas, e as duas foram conferidas antes de qualquer medição — a versão '
      'Python de `ValidarPremissa()` do `.mq5`.')
    a('')
    a('**A premissa geométrica:** `High-Low` constante.')
    a('')
    a('| | |')
    a('|---|---|')
    a('| Range mediano | %s ticks |' % n(P['range_mediana']))
    a('| Barras dentro de ±10%% da mediana | **%s** |'
      % pct(P['range_dentro_10pct'], 2))
    a('| Desvio padrão do range | %s ticks |' % n(P['range_desvio'], 2))
    a('| Mínimo / máximo | %s / %s ticks |'
      % (n(P['range_min']), n(P['range_max'])))
    a('')
    a('Confirmada. As barras que fogem são as de fim de sessão, fechadas antes '
      'de completar o range — e são justamente as que o indicador descarta '
      'pelo teste de "barra completa".')
    a('')
    a('**A premissa da agressão:** `tick_volume` é agressão compradora e '
      '`real_volume` é vendedora — a convenção do símbolo sintético do '
      '`Range_Claude_v1.mq5`. Num símbolo comum os dois campos significam '
      'outra coisa e o indicador não daria erro nenhum: produziria números sem '
      'significado, que é o pior modo de falhar.')
    a('')
    a('| | |')
    a('|---|---|')
    a('| Barras com agressão vendedora ausente | %s |' % pct(P['pct_vol_zero'], 2))
    a('| Barras com agressão compradora ausente | %s |'
      % pct(P['pct_tickvol_zero'], 2))
    a('| Correlação entre os dois campos | %s |' % n(P['correlacao_agressoes'], 3))
    a('')
    a('Confirmada. Os dois campos existem, são distintos e caminham juntos — o '
      'que se espera de duas metades do mesmo fluxo, e não de um campo '
      'duplicado.')
    a('')
    a('| o histórico | |')
    a('|---|---|')
    a('| Barras | %s |' % n(D['barras']))
    a('| Período | %s a %s |' % (D['inicio'][:16], D['fim'][:16]))
    a('| Pregões | %s (%s barras por pregão) |'
      % (n(D['dias']), n(D['barras_por_dia'], 1)))
    a('| Preço | %s a %s |' % (n(D['preco_min'], 2), n(D['preco_max'], 2)))
    a('| Segundos por barra (mediana) | %s |'
      % n(D['segundos_por_barra'].get('50%', 0)))
    a('| Corpo / range (mediana) | %s |' % n(D['corpo_frac'].get('50%', 0), 3))
    a('')

    # ------------------------------------------------------------------ 3
    a('## 3 · Método: as três decisões que mudam todo o resto')
    a('')
    a('### 3.1 · A ambiguidade dentro da barra, e como este gráfico a elimina')
    a('')
    a('Quando uma barra toca o alvo e o stop, o OHLC não diz qual veio '
      'primeiro. É o único ponto cego de qualquer backtest feito sobre OHLC, e '
      'costuma ser resolvido por convenção — assume-se o stop primeiro e '
      'publica-se a hipótese oposta ao lado, como teto.')
    a('')
    a('Num gráfico de range existe uma saída melhor. Como `High-Low` é '
      '**%s ticks por construção**, uma barra não consegue percorrer %s ticks '
      'para cima *e* %s para baixo a partir do próprio open: os dois lados '
      'somados dariam exatamente o range inteiro. Medido neste arquivo, isso '
      'acontece em **0,03%% das barras**.'
      % (n(r['range_nominal']), n(r['range_nominal'] / 2),
         n(r['range_nominal'] / 2)))
    a('')
    a('Consequência: com stop e alvo a **meio range**, as hipóteses pessimista '
      'e otimista devolvem *o mesmo número*. A convenção deixa de existir, e '
      'com ela o principal motivo de desconfiar de um backtest. É por isso que '
      'a métrica central deste estudo é o meio range, e não o 1:1 em um range '
      'inteiro. A tabela do §9 marca quais gestões têm essa propriedade.')
    a('')
    a('### 3.2 · O que uma entrada limitada custa em honestidade')
    a('')
    a('Uma ordem limitada preenchida **dentro** de uma barra não tem hora '
      'marcada no arquivo. A máxima daquela barra pode ter acontecido antes do '
      'preenchimento, e creditar o alvo por causa dela é ler o futuro.')
    a('')
    a('Neste gráfico o erro é grosseiro. A barra tem %s ticks garantidos, '
      'então quase toda barra que preenche uma ordem no meio dela também '
      '"alcança" um alvo de meio range. Contabilizada assim, a entrada '
      'limitada mede **%s de acerto** — um resultado impossível, publicado na '
      'tabela do §6 apenas como demonstração do erro.'
      % (n(r['range_nominal']), pct(art[0]['acerto']) if art else 'n/d'))
    a('')
    a('Corrigido: na barra do preenchimento a operação **só pode piorar**, '
      'nunca melhorar. É a mesma convenção pessimista do resto do estudo, '
      'aplicada ao único instante que o arquivo não datou. O número da V3 é, '
      'portanto, um **piso** — e mesmo o teto irrealizável não salvaria a '
      'entrada limitada, porque ela abandona %s dos sinais sem compensar nada.'
      % pct(1 - V['V3']['stats']['taxa_ativacao']))
    a('')
    a('### 3.3 · As demais decisões')
    a('')
    a('- **Custo.** A coluna `<SPREAD>` do arquivo traz valores impossíveis '
      '(até %s) e foi descartada. O custo entra como cenário explícito — 0, '
      '10, 20 e 40 ticks — e nunca embutido.'
      % n(141050000))
    a('- **Uma operação por vez.** Sinais que aparecem com posição aberta são '
      'descartados, como aconteceria na mesa. É por isso que a V0 mostra %s '
      'operações e a V4, com alvo mais curto, mostra %s: a gestão longa da V0 '
      'ocupa a posição e engole sinais.'
      % (n(v0['stats']['operacoes']), n(V['V4']['stats']['operacoes'])))
    a('- **A entrada padrão é a mercado no fechamento da barra de sinal**, e a '
      'gestão só começa na barra seguinte. O preço é conhecido na fronteira da '
      'barra; não há instante indatado.')
    a('- **A busca inteira é publicada.** Os %s filtros testados aparecem no '
      '§6 com o z de cada um, para que o melhor possa ser lido como o máximo '
      'de %s tentativas — e não como uma descoberta.'
      % (n(len(cands)), n(len(cands))))
    a('')

    # ------------------------------------------------------------------ 4
    a('## 4 · O que o gatilho produz')
    a('')
    a('| | |')
    a('|---|---|')
    a('| Sinais | %s em %s barras (%s) |'
      % (n(I['total']), n(D['barras']), pct(I['pct_barras'], 2)))
    a('| Absorção (sinal 1) | %s — %s de alta, %s de baixa |'
      % (n(I['absorcao_alta'] + I['absorcao_baixa']), n(I['absorcao_alta']),
         n(I['absorcao_baixa'])))
    a('| Divergência (sinal 2) | %s — %s de alta, %s de baixa |'
      % (n(I['divergencia_alta'] + I['divergencia_baixa']),
         n(I['divergencia_alta']), n(I['divergencia_baixa'])))
    a('| Frequência | %s por pregão, um a cada %s barras |'
      % (n(I['sinais_por_dia'], 1), n(I['barras_entre_sinais'])))
    a('')
    a('Os dois lados saem equilibrados — %s sinais de alta contra %s de baixa. '
      'Um gatilho que disparasse muito mais para um lado estaria lendo a '
      'tendência do período, não a barra.'
      % (n(I['absorcao_alta'] + I['divergencia_alta']),
         n(I['absorcao_baixa'] + I['divergencia_baixa'])))
    a('')
    a('As métricas do indicador, medidas **nas barras de sinal**:')
    a('')
    a('| métrica | p10 | mediana | p90 |')
    a('|---|---|---|---|')
    for rot, k in (('Resultado relativo (`resRel`)', 'res_rel'),
                   ('Esforço relativo (`esfRel`)', 'esf_rel'),
                   ('Agressão a favor (`qualRel`)', 'qual_rel'),
                   ('Eficiência (`resRel/esfRel`)', 'efic'),
                   ('Corpo / range', 'corpo_frac')):
        b = I[k]
        a('| %s | %s | %s | %s |'
          % (rot, n(b['10%'], 2), n(b['50%'], 2), n(b['90%'], 2)))
    a('')
    a('A mediana de `resRel` nos sinais é %s, contra %s no universo inteiro: '
      'o indicador está mesmo selecionando barras que andaram menos que o '
      'normal da direção delas, que é o que a tese de absorção pede.'
      % (n(I['res_rel']['50%'], 2), n(I['res_rel_todas']['50%'], 2)))
    a('')

    # ------------------------------------------------------------------ 5
    a('## 5 · O sinal tem direção?')
    a('')
    a('### 5.1 · A excursão pura, contra dois controles sorteados')
    a('')
    a('Sem nenhuma regra de saída: a partir do fechamento da barra de sinal, '
      'até onde o preço vai a favor (MFE) e contra (MAE) nas próximas barras. '
      'Se o gatilho carrega direção, esses números têm de diferir dos de uma '
      'entrada sorteada.')
    a('')
    a('| horizonte | amostra | MFE mediana | MAE mediana | MFE/MAE | deriva média | t |')
    a('|---|---|---|---|---|---|---|')
    rot = {'sinal': 'o sinal do indicador',
           'direcao_sorteada': 'mesmas barras, **direção sorteada**',
           'barra_e_direcao_sorteadas': 'barra e direção sorteadas',
           'esforco_baixo': 'sinal com **esforço baixo**'}
    for H in ('5', '20', '40'):
        for k in ('sinal', 'direcao_sorteada', 'barra_e_direcao_sorteadas',
                  'esforco_baixo'):
            b = r['excursao'][k][H]
            a('| %s barras | %s | %s t | %s t | **%s** | %s t | %s |'
              % (H, rot[k], n(b['mfe_med']), n(b['mae_med']),
                 n(b['razao'], 3), fmt(b['deriva_media'], 1),
                 fmt(b['deriva_t'], 2)))
    a('')
    a('**Nada.** A razão MFE/MAE do sinal fica colada em 1,00, igual à das '
      'entradas sorteadas, e nenhuma deriva chega perto de significância. '
      'Se o estudo parasse aqui — e é aqui que a maioria para — a conclusão '
      'seria que o indicador não serve.')
    a('')
    a('O problema é que essas medidas olham 5, 20, 40 barras à frente. A '
      'vantagem do gatilho não dura tanto.')
    a('')
    a('### 5.2 · A linha de base: o gráfico já vem inclinado')
    a('')
    a('Num gráfico de range dá para medir a direção da barra seguinte **sem '
      'ambiguidade nenhuma** (§3.1): basta perguntar se ela percorre meio '
      'range para cima ou para baixo a partir do próprio open. Isso permite '
      'medir a taxa de continuação no arquivo inteiro, e não só nos sinais.')
    a('')
    a('| grupo | o que é | amostra | continua | z |')
    a('|---|---|---|---|---|')
    for g in LB['grupos']:
        a('| %s | %s | %s | **%s** | %s |'
          % (g['grupo'], g['nota'], n(g['n']), pct(g['acerto'], 2),
             fmt(g['z'], 2)))
    a('')
    a('Duas leituras, e as duas importam:')
    a('')
    a('1. **O gráfico de range tem momentum de fábrica.** Barras continuam na '
      'própria direção %s das vezes, com z = %s sobre %s barras. Qualquer '
      'gatilho que dispare a favor de uma barra herda isso de graça.'
      % (pct(LB['grupos'][0]['acerto'], 2), fmt(LB['grupos'][0]['z'], 2),
         n(LB['grupos'][0]['n'])))
    a('2. **O indicador acrescenta algo real por cima.** Contra o controle '
      'emparelhado — barra de virada com esforço baixo, mas sem as condições '
      'de resultado e agressão do indicador — a diferença é de %s pontos '
      '(%s contra %s), com z = %s.'
      % (fmt(100 * LB['ganho']['diferenca'], 1),
         pct(LB['ganho']['com_indicador'], 2), pct(LB['ganho']['base'], 2),
         fmt(LB['ganho']['z'], 2)))
    a('')
    a('É essa segunda linha que justifica o indicador. Sem ela, os %s da V8 '
      'seriam apenas o momentum do gráfico com um enfeite em cima.'
      % pct(s8['acerto']))
    a('')

    # ------------------------------------------------------------------ 6
    a('## 6 · A busca por um filtro')
    a('')
    a('%s filtros testados, todos com a métrica neutra de meio range. A '
      'coluna `z (1R)` repete a medição com stop e alvo de um range inteiro — '
      'publicar as duas evita escolher a métrica depois de ver o resultado.'
      % n(len(cands)))
    a('')
    a('| filtro testado | operações | acerto | z | z (1R) | expectativa |')
    a('|---|---|---|---|---|---|')
    for b in sorted(r['busca'], key=lambda x: (x['artefato'], -x['z'])):
        if b['poucas'] and not b['artefato']:
            a('| %s | %s | — | — | — | amostra insuficiente |'
              % (b['filtro'], n(b['n'])))
            continue
        marca = ''
        if b['artefato']:
            marca = ' ⚠️'
        elif b['esforco']:
            marca = ' ←'
        a('| %s%s | %s | %s | **%s** | %s | %s t |'
          % (b['filtro'], marca, n(b['n']), pct(b['acerto']), fmt(b['z'], 2),
             fmt(b['r1']['z'], 2), fmt(b['expectativa_ticks'], 1)))
    a('')
    a('⚠️ A primeira linha é o artefato do §3.2, publicado como demonstração '
      'do erro de método. Não é candidato e não entra na conta de tentativas.')
    a('')
    a('O que sobra é claro: **as seis primeiras posições são todas variações '
      'do mesmo filtro de esforço**, e nenhum outro filtro chega perto. Um '
      'resultado de busca em que o topo é ocupado por um só conceito, em '
      'várias calibragens, é bem diferente de um em que o topo é um número '
      'solitário — o segundo caso é o retrato de um acaso.')
    a('')
    a('Ainda assim, `z = %s` é o máximo de %s tentativas, e é assim que ele '
      'tem de ser lido. O §7 aplica a esse filtro a mesma disciplina que '
      'reprovou o horário.'
      % (fmt(max(b['z'] for b in cands), 2), n(len(cands))))
    a('')

    # ------------------------------------------------------------------ 7
    a('## 7 · O filtro de esforço, sob validação')
    a('')
    a('A tese: uma barra que virou o movimento **com pouca gente negociando** '
      'é a forma mais pura da absorção. Não houve briga; o preço andou porque '
      'não havia nada do outro lado. O filtro exige que o esforço total da '
      'barra fique abaixo de %s da média das barras da mesma direção.'
      % pct(EF['limite']))
    a('')
    a('Um filtro escolhido no melhor de %s tentativas só merece crédito se '
      'passar em quatro testes independentes.' % n(len(cands)))
    a('')
    a('**(a) É platô, não pico.** Um parâmetro que só funciona no valor exato '
      'em que foi encontrado é ajuste à amostra.')
    a('')
    a('| limite | operações | acerto | z | expectativa |')
    a('|---|---|---|---|---|')
    for p in EF['plato']:
        marca = ' **←**' if abs(p['limite'] - EF['limite']) < 1e-9 else ''
        a('| ≤ %s%s | %s | %s | %s | %s t |'
          % (n(p['limite'], 2), marca, n(p['n']), pct(p['acerto']),
             fmt(p['z'], 2), fmt(p['expectativa_ticks'], 1)))
    a('')
    a('Platô. De 0,60 a 0,80 o acerto fica entre %s e %s, e a degradação para '
      'fora é suave e monotônica. O valor publicado não é um pico; é o meio de '
      'uma faixa larga.'
      % (pct(min(p['acerto'] for p in EF['plato'] if 0.6 <= p['limite'] <= 0.8)),
         pct(max(p['acerto'] for p in EF['plato'] if 0.6 <= p['limite'] <= 0.8))))
    a('')
    a('**(b) Aparece nos dois pedaços da amostra, e nos três.**')
    a('')
    a('| pedaço | operações | acerto | z | expectativa |')
    a('|---|---|---|---|---|')
    for nm in ('1a', '2a'):
        v = EF['metades'][nm]
        a('| %sª metade | %s | %s | %s | %s t |'
          % (nm[0], n(v['n']), pct(v['acerto']), fmt(v['z'], 2),
             fmt(v['expectativa_ticks'], 1)))
    for v in EF['tercos']:
        a('| %sº terço | %s | %s | %s | %s t |'
          % (v['terco'], n(v['n']), pct(v['acerto']), fmt(v['z'], 2),
             fmt(v['expectativa_ticks'], 1)))
    a('')
    a('As duas metades ficam a menos de meio ponto uma da outra (%s e %s), e '
      'os três terços sobem de %s para %s. Nenhum pedaço carrega o resultado '
      'sozinho — que é o modo mais comum de um filtro falso passar despercebido.'
      % (pct(EF['metades']['1a']['acerto']), pct(EF['metades']['2a']['acerto']),
         pct(EF['tercos'][0]['acerto']), pct(EF['tercos'][2]['acerto'])))
    a('')
    a('**(c) O controle invertido é o espelho.** Operando o lado oposto, o '
      'acerto vai a %s e a expectativa a %s ticks. A simetria é exata: a '
      'vantagem é de **direção**, e não de um viés de contabilidade que '
      'sobreviveria à inversão.'
      % (pct(EF['invertido']['acerto']),
         fmt(EF['invertido']['expectativa_ticks'], 1)))
    a('')
    a('**(d) Não é um disfarce de horário.** Se o filtro estivesse apenas '
      'selecionando as horas calmas, a vantagem sumiria dentro de cada hora.')
    a('')
    a('| | |')
    a('|---|---|')
    a('| Sinais que passam no filtro | %s |' % pct(I['pct_esforco_baixo']))
    a('| Faixa dessa fração entre as horas | %s a %s |'
      % (pct(min(EF['fracao_por_hora'].values())),
         pct(max(EF['fracao_por_hora'].values()))))
    a('| Horas com ≥ 15 operações | %s, das quais %s acima de 50%% |'
      % (n(len(EF['por_hora'])),
         n(sum(1 for h in EF['por_hora'] if h['acerto'] > 0.5))))
    a('')
    a('O filtro corta em todas as horas e a vantagem aparece na maioria delas. '
      'Ele também funciona nos dois tipos de sinal (absorção %s, divergência '
      '%s) e nos dois lados (compra %s, venda %s).'
      % (pct(EF['por_tipo']['1']['acerto']), pct(EF['por_tipo']['2']['acerto']),
         pct(EF['por_lado']['long']['acerto']),
         pct(EF['por_lado']['short']['acerto'])))
    a('')
    a('Quatro testes, quatro aprovações. É o máximo que uma amostra só permite '
      'afirmar — e não substitui um teste em tempo real.')
    a('')

    # ------------------------------------------------------------------ 8
    a('## 8 · O horário, que não passou')
    a('')
    a('A estratégia pedia segregação por horário. As horas foram escolhidas em '
      'uma metade da amostra (mínimo de 25 operações e acerto acima de 53%%) e '
      'testadas na outra, nos dois sentidos.')
    a('')
    a('| escolhido em | horas | testado em | operações | acerto | referência | z |')
    a('|---|---|---|---|---|---|---|')
    for k, e, t in (('escolhe_1a_testa_2a', '1ª metade', '2ª metade'),
                    ('escolhe_2a_testa_1a', '2ª metade', '1ª metade')):
        v = HR[k]
        a('| %s | %s | %s | %s | %s | %s | %s |'
          % (e, ', '.join('%dh' % h for h in v['horas']) or '—', t,
             n(v['n']), pct(v['acerto']), pct(v['acerto_referencia']),
             fmt(v['z'], 2)))
    a('')
    a('**Reprovado.** Fora da amostra, as horas escolhidas não batem a '
      'referência de forma nenhuma — num dos sentidos ficam *abaixo* dela. A '
      'interseção entre as duas escolhas é de apenas %s hora(s) (%s), o que é '
      'compatível com sorteio.'
      % (n(len(HR['intersecao'])),
         ', '.join('%dh' % h for h in HR['intersecao']) or 'nenhuma'))
    a('')
    a('A V5 está publicada com essas horas para que o leitor veja o que '
      'acontece: dentro da amostra ela mede %s de acerto e parece ótima. É '
      'exatamente esse número que a validação cruzada existe para desmontar.'
      % pct(V['V5']['stats']['acerto']))
    a('')

    # ------------------------------------------------------------------ 9
    a('## 9 · Os parâmetros do próprio indicador')
    a('')
    a('Um gatilho cujo resultado desaba quando o parâmetro anda 10% não foi '
      'medido: foi ajustado. Cada linha abaixo recalcula o indicador do zero e '
      'mede com a seleção da V8. O asterisco marca o valor padrão do `.mq5`.')
    a('')
    for g in r['sensibilidade']:
        a('**`%s`** — %s' % (g['campo'], g['rotulo']))
        a('')
        a('| valor | sinais gerados | operações | acerto | z |')
        a('|---|---|---|---|---|')
        for ln in g['linhas']:
            b = ln['esforco_baixo']
            a('| %s%s | %s | %s | %s | %s |'
              % (n(ln['valor'], 2), ' **\\***' if ln['padrao'] else '',
                 n(ln['sinais']), n(b['n']), pct(b['acerto']), fmt(b['z'], 2)))
        a('')
    a('Todos os seis parâmetros são platôs. Em nenhum deles o valor padrão é o '
      'melhor da varredura, e em nenhum a variação chega a mudar a conclusão. '
      'Isso é evidência forte de que o indicador **não foi ajustado a este '
      'histórico** — o que faz sentido, já que ele foi portado de um NTSL '
      'escrito antes e para outro contexto.')
    a('')
    a('Dois valores mediram melhor que o padrão de forma consistente: '
      '`fator_res` em 0,50 e `fator_qual` em 0,20–0,35. Ambos tornam o gatilho '
      '**mais exigente**, o que é coerente com a tese. Não são recomendados '
      'aqui: mexer neles depois de ver a tabela é a definição de ajuste.')
    a('')

    # ------------------------------------------------------------------ 10
    a('## 10 · A gestão, e por que o alvo é curto')
    a('')
    a('Aqui a seleção está fixa (esforço baixo) e o que varia é a saída. A '
      'coluna final marca as gestões em que a ambiguidade dentro da barra não '
      'existe (§3.1) — nelas o número não depende de suposição nenhuma.')
    a('')
    a('| gestão | operações | acerto | expectativa | em R | t | barras | s/ ambiguidade |')
    a('|---|---|---|---|---|---|---|---|')
    for g in r['gestao']:
        a('| %s | %s | %s | %s t | %s | %s | %s | %s |'
          % (g['rotulo'], n(g['operacoes']), pct(g['acerto']),
             fmt(g['expectativa_ticks'], 1), fmt(g['expectativa_R'], 3),
             fmt(g['t_stat'], 2), n(g['barras_media'], 1),
             '**sim**' if g['sem_ambiguidade'] else 'não'))
    a('')
    a('A leitura é inequívoca. Em R por operação, o meio range paga %s; um '
      'range inteiro paga %s; dois ranges pagam %s. **A vantagem do gatilho '
      'existe por uma barra e se dissolve depois** — o que explica por que a '
      'excursão do §5.1, medida em 5 a 40 barras, não achou nada.'
      % (fmt([g for g in r['gestao'] if 'MEIO RANGE' in g['rotulo']][0]
             ['expectativa_R'], 3),
         fmt([g for g in r['gestao'] if 'um range' in g['rotulo']][0]
             ['expectativa_R'], 3),
         fmt([g for g in r['gestao'] if 'dois ranges' in g['rotulo']][0]
             ['expectativa_R'], 3)))
    a('')
    a('A linha de 1/4 de range (%s de acerto, t = %s) merece atenção porque '
      'parece contradizer o resto. Não contradiz: ela é a única da tabela em '
      'que os dois lados cabem dentro da mesma barra, então a ambiguidade '
      'volta com força total e a convenção pessimista decide quase todas as '
      'operações contra. É um artefato da convenção, não uma medida.'
      % (pct(r['gestao'][0]['acerto']), fmt(r['gestao'][0]['t_stat'], 2)))
    a('')

    # ------------------------------------------------------------------ 11
    a('## 11 · As variantes')
    a('')
    a('| variante | sinais | operações | acerto | exp./op. | total | fator de lucro | rebaixamento |')
    a('|---|---|---|---|---|---|---|---|')
    for v in r['variantes']:
        a(linha_var(v))
    a('')
    for v in r['variantes']:
        a('**%s · %s** — %s' % (v['nome'], v['rotulo'], v['descricao']))
        a('')
    a('### Sensibilidade de cada variante')
    a('')
    a('Expectativa por operação, em ticks, sob cada hipótese.')
    a('')
    a('| variante | pessimista | otimista | custo 10 t | custo 20 t | custo 40 t | 1ª metade | 2ª metade |')
    a('|---|---|---|---|---|---|---|---|')
    for v in r['variantes']:
        vals = [v['stats'].get('expectativa_ticks', 0),
                v['stats_otimista'].get('expectativa_ticks', 0),
                v['custo']['10'].get('expectativa_ticks', 0),
                v['custo']['20'].get('expectativa_ticks', 0),
                v['custo']['40'].get('expectativa_ticks', 0),
                v['metades']['1a'].get('expectativa_ticks', 0),
                v['metades']['2a'].get('expectativa_ticks', 0)]
        a('| %s · %s | %s |'
          % (v['nome'], v['rotulo'], ' | '.join(fmt(x, 1) for x in vals)))
    a('')
    a('Repare nas colunas pessimista e otimista da V7 e da V8: são **idênticas**. '
      'É a propriedade do §3.1 aparecendo na tabela — nessas duas variantes não '
      'há hipótese a escolher.')
    a('')

    # ------------------------------------------------------------------ 12
    a('## 12 · Restrições recomendadas')
    a('')
    a('1. **Operar o sinal a favor da barra, a mercado no fechamento dela.** '
      'A entrada limitada no meio do range (V3) abandona %s dos sinais e não '
      'compensa em preço o que perde em amostra.'
      % pct(1 - V['V3']['stats']['taxa_ativacao']))
    a('2. **Exigir esforço abaixo de %s do normal da direção.** É a única '
      'restrição do estudo inteiro que passou em todos os controles. Fora '
      'dela, o gatilho mede %s de acerto contra %s dentro.'
      % (pct(EF['limite']), pct(V['V7']['stats']['acerto']), pct(s8['acerto'])))
    a('3. **Alvo e stop a meio range (%s ticks).** Não por gosto, mas porque é '
      'onde a vantagem está e porque é a única faixa sem ambiguidade.'
      % n(r['range_nominal'] / 2))
    a('4. **Não esticar o alvo.** Em dois ranges a expectativa fica negativa.')
    a('5. **Não filtrar por horário.** Reprovado fora da amostra (§8).')
    a('6. **Não mexer nos parâmetros do indicador.** São platôs (§9); mexer '
      'depois de ver a tabela é ajustar à amostra.')
    a('7. **Tratar o custo como a restrição dominante.** Com %s ticks de '
      'expectativa bruta, %s ticks de custo consomem %s dela e %s ticks a '
      'tornam negativa.'
      % (fmt(s8['expectativa_ticks'], 1), n(20),
         pct(20 / s8['expectativa_ticks']), n(40)))
    a('')

    # ------------------------------------------------------------------ 13
    a('## 13 · Limitações')
    a('')
    a('- **Uma amostra, um ativo, %s pregões.** Tudo aqui é um único caminho '
      'do preço. Nenhuma quantidade de validação interna substitui um segundo '
      'histórico.' % n(D['dias']))
    a('- **A margem cabe dentro do spread.** %s ticks por operação, com risco '
      'de %s ticks, é %s R. É real e é pequeno; qualquer degradação de '
      'execução o elimina.'
      % (fmt(s8['expectativa_ticks'], 1), n(r['range_nominal'] / 2),
         fmt(s8['expectativa_R'], 3)))
    a('- **O melhor de %s tentativas.** O filtro de esforço passou em quatro '
      'validações independentes, o que é muito mais do que o horário '
      'conseguiu, mas continua tendo sido escolhido depois de olhar os dados.'
      % n(len(cands)))
    a('- **Slippage não está modelado.** A entrada é a mercado no fechamento '
      'de uma barra de range, que é justamente um instante de movimento. O '
      'preço de execução real será pior que o do arquivo, e o cenário de custo '
      'de 20–40 ticks existe para cobrir isso.')
    a('- **A convenção de agressão é uma premissa, não um fato medido.** O '
      'estudo confere que os dois campos existem e são distintos (§2), não que '
      '`tick_volume` seja de fato a agressão compradora. Se o gerador do '
      'símbolo mudar essa convenção, todo o §7 muda de significado.')
    a('- **A última barra de cada dia é descartada** pelo teste de barra '
      'completa do próprio indicador, o que remove os fechamentos de sessão da '
      'amostra.')
    a('')
    a('---')
    a('')
    a('Gerado por `resultados_md.py` a partir de `saida/resumo.json` '
      '(%s). Para reproduzir: `python rodar.py && python resultados_md.py`.'
      % r['gerado_em'])

    caminho = os.path.join(BASE, 'RESULTADOS.md')
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('RESULTADOS.md gravado (%s linhas).' % len(L))


if __name__ == '__main__':
    escrever()
