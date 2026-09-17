# -*- coding: utf-8 -*-
"""
Gera PLANO.md e plano.html -- o plano operacional MANUAL.

    python rodar.py     # primeiro, para atualizar saida/resumo.json
    python plano.py     # depois

Como o relatorio, nenhum numero e escrito a mao: tudo sai de
saida/resumo.json. O plano cita poucos numeros de proposito -- ele e um
procedimento, nao um relatorio -- mas os que cita sao os medidos.

A configuracao que o plano descreve e a recomendada em RESULTADOS.md 11:
so o setup A, entrada limitada valida por UMA barra.

O STOP nao e mais escrito a mao. Ele e ESCOLHIDO PELA MEDICAO, entre os
stops que rodar.py mediu, pelo criterio abaixo -- do contrario o plano
fica dizendo 100 depois de uma rodada em que 150 passou a medir melhor,
que foi exatamente o que aconteceu quando o eixo [E2] do gatilho mudou.
Para fixar um stop a mao (por gestao de risco, nao por medicao), ponha o
valor em STOP_FIXO.
"""
import io
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
DEST_MD = os.path.join(BASE, 'PLANO.md')
DEST_HTML = os.path.join(BASE, 'plano.html')

STOP_FIXO = None            # None = escolhe pela medicao | 100, 150... = fixa
CFG = 'A_c5'                # so A, descontando 5 pts de custo por trade
VAL_PONTO = 0.20            # R$ por ponto, 1 contrato WIN


# ------------------------------------------------------------ formatacao
def n1(v):
    return '—' if v is None else ('%+.1f' % v).replace('.', ',')


def p0(v):
    return '—' if v is None else '%d%%' % round(v)


def t2(v):
    return '—' if v is None or v != v else ('%+.2f' % v).replace('.', ',')


def i0(v):
    return '—' if v is None else '%d' % round(v)


def rs(pontos):
    return ('R$ %.2f' % (pontos * VAL_PONTO)).replace('.', ',')


# ------------------------------------------------------------ os numeros
def escolhe_stop(R):
    """Qual stop o plano descreve.

    Criterio: na configuracao do PLANO (carteira so A, com custo), o stop
    com a maior media diaria SOMADA nas duas bases. Media diaria, e nao
    EV por trade, porque o plano e um procedimento de pregao; somada, e
    nao "vence nas duas", porque as duas bases nao concordam mais desde a
    troca do eixo [E2] -- e quando elas discordam quem manda e a base
    maior, que e o WINFUT.
    """
    if STOP_FIXO is not None:
        return str(STOP_FIXO), None
    pontos = {}
    for st in R['stops']:
        pontos[str(st)] = sum(R['bases'][b]['psico'][str(st)][CFG]['media_dia']
                              for b in ('WINV26', 'WINFUT'))
    melhor = max(pontos, key=pontos.get)
    outro = [k for k in pontos if k != melhor]
    return melhor, (outro[0] if outro else None)


def contexto():
    R = json.load(io.open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8'))
    P = R['parametros']
    STOP_PLANO, STOP_OUTRO = escolhe_stop(R)
    fu = R['bases']['WINFUT']['psico'][STOP_PLANO][CFG]
    v26 = R['bases']['WINV26']['psico'][STOP_PLANO][CFG]
    # sem custo, para mostrar a diferenca que o custo faz
    fu0 = R['bases']['WINFUT']['psico'][STOP_PLANO]['A']
    va = R['variantes']

    # abortos: quantos sinais do setup A nao viram trade
    ab = {}
    for b in ('WINV26', 'WINFUT'):
        v = va[b]['ema3'][str(R['stops'][0])]
        ab[b] = (v['sinais_A'], v['setup_A']['n'])
    tot_s = sum(x[0] for x in ab.values())
    tot_n = sum(x[1] for x in ab.values())

    # o teste fora da amostra, na configuracao do plano (so A, custo 5)
    jn = R['bases']['WINFUT']['janela']
    oos = dict(janela=jn['janela'], pregoes=jn['pregoes'],
               A=jn[STOP_PLANO]['cA_c5'], AB=jn[STOP_PLANO]['cAB_c5'])
    fa = oos['A']['fora']
    oos['falhou'] = (fa is None) or (fa['t'] != fa['t']) or fa['t'] < 1.0

    return dict(
        R=R, fu=fu, v26=v26, fu0=fu0, oos=oos,
        stop=int(STOP_PLANO), stop_outro=(int(STOP_OUTRO) if STOP_OUTRO else None),
        stop_fixo=(STOP_FIXO is not None),
        parcial=int(P['PARCIAL_EM'] or STOP_PLANO), alvo=int(P['ALVO']),
        frac=int(100 * P['FRAC_PARCIAL']),
        nivel=P['NIVEL_MIN'], corpo=int(P['CORPO_MAX']),
        emas='%d / %d / %d' % (P['EMA_R'], P['EMA_M'], P['EMA_L']),
        abort_pct=round(100.0 * (tot_s - tot_n) / tot_s),
        ab=ab,
        risco_rs=rs(int(STOP_PLANO)),
        limite_pts=3 * int(STOP_PLANO),
        limite_rs=rs(3 * int(STOP_PLANO)),
        dd_rs=rs(fu['dd']),
    )


# =========================================================== o texto (md)
def markdown(C):
    fu, v26, fu0 = C['fu'], C['v26'], C['fu0']
    L = []
    A = L.append

    A('# Plano operacional — WIN, gráfico de 10.000 ticks\n')
    A('> **Este arquivo é gerado.** Rode `python rodar.py && python plano.py`.')
    A('> Os números saem de `saida/resumo.json`, os mesmos do')
    A('> [relatorio.html](relatorio.html). O texto do procedimento é fixo; se')
    A('> você mudar uma regra, mude aqui **e** em [ESTRATEGIA.md](ESTRATEGIA.md).\n')
    A('Companheiro operacional de [RESULTADOS.md](RESULTADOS.md). O relatório diz')
    A('**o que foi medido**; este arquivo diz **o que eu faço na frente da tela**.\n')

    oos = C['oos']
    if oos['falhou']:
        jn = oos['janela']
        dmy = lambda x: '/'.join(reversed(x.split('-')))
        A('---\n\n## Antes de assinar: o teste fora da amostra\n')
        A('> **Este plano ainda não passou no único teste independente que existe.**')
        A('> Os parâmetros foram escolhidos olhando os pregões de %s a %s. Nos %d'
          % (dmy(jn[0]), dmy(jn[1]), oos['pregoes']['fora']))
        A('> pregões do WINFUT fora dessa janela, o setup A com stop %d e 5 pontos de'
          % C['stop'])
        A('> custo mede **%s pontos por trade (t %s, %d trades)** — contra %s dentro dela.'
          % (n1(oos['A']['fora']['ev']), t2(oos['A']['fora']['t']),
             oos['A']['fora']['n'], n1(oos['A']['dentro']['ev'])))
        A('> Antes da janela: %s em %d trades. Depois: %s em %d.'
          % (n1(oos['A']['antes']['ev']), oos['A']['antes']['n'],
             (n1(oos['A']['depois']['ev']) if oos['A']['depois'] else '—'),
             (oos['A']['depois']['n'] if oos['A']['depois'] else 0)))
        A('>')
        A('> O procedimento abaixo continua valendo como procedimento. **Dinheiro, não**:')
        A('> só em simulador, ou no tamanho mínimo, até que registros novos digam outra')
        A('> coisa. Detalhe em [RESULTADOS.md § 10](RESULTADOS.md).\n')

    # ---------------------------------------------------------------- 0
    A('---\n\n## 0. O contrato\n')
    A('Eu opero **um** setup, com **um** tamanho de risco, seguindo as regras 1 a 6')
    A('deste arquivo. As regras não mudam durante o pregão. Não mudam depois de uma')
    A('perda. Não mudam depois de um ganho. Mudam apenas na **revisão mensal** da')
    A('§ 10, com os dados na mão.\n')
    A('A única coisa que eu avalio ao fim do dia é **se segui o plano** — não quanto')
    A('ganhei. A § 7 explica por que, com os números que tornam isso não uma frase')
    A('bonita, mas a leitura correta dos dados.\n')
    A('Assinado: ____________________   Data: __ / __ / ____\n')

    # ---------------------------------------------------------------- 1
    A('---\n\n## 1. O que eu opero — e o que eu não opero\n')
    A('| | |')
    A('|---|---|')
    A('| **Ativo** | WIN (mini índice) |')
    A('| **Gráfico** | candle de **10.000 ticks** |')
    A('| **Setup** | **A — tendência (pullback na média)**, e só ele |')
    A('| **Direção** | pelo empilhamento das EMAs %s |' % C['emas'])
    A('| **Lado** | compra e venda |')
    A('| **Posições** | **uma por vez**. Sinal que chega com posição aberta é ignorado |\n')
    A('**O que eu NÃO opero:**\n')
    A('- **Setup C (reversão em consolidação).** Mede negativo nas duas bases, em')
    A('  toda configuração testada. Não está no plano e não entra por exceção.')
    A('- **Setup B (reversão no afastamento).** É positivo, mas mais fraco e com o')
    A('  dobro de rebaixamento. Fica **fora** até uma revisão decidir promovê-lo. Se')
    A('  eu quiser operá-lo, é uma decisão de revisão mensal, não de pregão.')
    A('- **Qualquer coisa que o indicador não marcou.** Se não saiu a seta A, não')
    A('  existe trade — por mais óbvio que o gráfico pareça.\n')
    A('> Por que só o A: é o setup com o melhor valor esperado por trade e o menor')
    A('> rebaixamento nas duas bases. E a %.1f trades por pregão ele é operável à'
      % fu['por_pregao'])
    A('> mão sem pressa.\n')

    # ---------------------------------------------------------------- 2
    A('---\n\n## 2. O gatilho — quando existe trade\n')
    A('O indicador faz a conta; eu confiro o contexto. **Todos os seis** têm de')
    A('estar verdadeiros. Um único "não" e não há trade.\n')
    A('| # | Verificação | |')
    A('|---|---|---|')
    A('| 1 | As três médias estão **empilhadas na ordem** (21 acima de 42 acima de 72, ou o inverso) | ☐ |')
    A('| 2 | O leque entre elas está **aberto** — não emboladas | ☐ |')
    A('| 3 | A barra do gatilho **toca** uma das três médias | ☐ |')
    A('| 4 | O indicador marcou a seta do **setup A** | ☐ |')
    A('| 5 | A seta aponta **a favor** do empilhamento | ☐ |')
    A('| 6 | Estou dentro do horário e **sem posição aberta** | ☐ |\n')
    A('Os itens 4 e 5 já embutem o que o indicador mede e eu não preciso conferir a')
    A('olho: índice de esforço ≥ %s, corpo ≤ %d%% do range, meio do corpo do lado'
      % (str(C['nivel']).replace('.', ','), C['corpo']))
    A('certo, e o eixo do deslocamento não sendo o dominante.\n')
    A('**A leitura econômica, em uma frase:** o preço voltou para a média, alguém')
    A('agrediu contra a tendência exatamente ali, e **falhou**. Eu entro do lado de')
    A('quem não falhou.\n')

    # ---------------------------------------------------------------- 3
    A('---\n\n## 3. A entrada — a regra da barra seguinte\n')
    A('```')
    A('barra t      o gatilho fecha. Eu envio a limitada no MEIO do candle,')
    A('             (máxima + mínima) / 2, arredondado ao tick.')
    A('barra t+1    ou ela preenche AQUI, ou eu CANCELO.')
    A('barra t+2    não existe. O sinal morreu.')
    A('```\n')
    A('**Não preencheu, acabou.** Não persigo o preço, não entro a mercado "para não')
    A('perder", não deixo a ordem no livro para ver no que dá. Cancelo e volto a')
    A('esperar.\n')
    A('Cerca de **%s dos sinais serão abortados** — no WINV26, %d de %d sinais do'
      % (p0(C['abort_pct']), C['ab']['WINV26'][0] - C['ab']['WINV26'][1], C['ab']['WINV26'][0]))
    A('setup A; no WINFUT, %d de %d. Isso não é falha de execução: é **o plano'
      % (C['ab']['WINFUT'][0] - C['ab']['WINFUT'][1], C['ab']['WINFUT'][0]))
    A('funcionando**. Um sinal abortado entra no diário como *aderência cumprida*,')
    A('exatamente como um trade vencedor.\n')
    A('> **Por que esta regra existe.** Medida, ela quase não muda o resultado —')
    A('> melhora uma base, piora a outra, pouco dos dois lados. Ela existe pelo que')
    A('> impede: que eu fique com uma ordem esquecida no livro, e que eu negocie um')
    A('> sinal de dez minutos atrás como se fosse de agora. Ela é uma **regra de')
    A('> disciplina que custa quase nada** — o melhor tipo de regra que existe.\n')

    # ---------------------------------------------------------------- 4
    A('---\n\n## 4. A gestão — decidida antes, executada sem opinião\n')
    A('| | |')
    A('|---|---|')
    A('| **Stop inicial** | **%d pontos** da entrada |' % C['stop'])
    A('| **Parcial** | **%d%% da posição em +%d pontos** — a mesma distância do stop |'
      % (C['frac'], C['parcial']))
    A('| **No momento da parcial** | **nada a fazer.** O stop já está na média da '
      'operação: com meia posição realizada a +%d, o stop de −%d é o zero a zero |'
      % (C['parcial'], C['stop']))
    A('| **Alvo do restante** | **+%d pontos** |' % C['alvo'])
    A('| **Saída forçada** | fechamento do pregão |\n')
    A('Resultado por trade, por contrato de lote cheio:\n')
    A('| desfecho | pontos | R$ | frequência medida |')
    A('|---|---|---|---|')
    A('| stop antes da parcial | −%d | −%s | %s |'
      % (C['stop'], rs(C['stop']).replace('R$ ', ''), p0(fu['p_stop'])))
    zero_pts = (C['frac'] * C['parcial'] - (100 - C['frac']) * C['stop']) / 100.0
    alvo_pts = (C['frac'] * C['parcial'] + (100 - C['frac']) * C['alvo']) / 100.0
    A('| parcial e depois o stop | %s%d | %s | %s |'
      % ('+' if zero_pts > 0 else '', round(zero_pts),
         rs(zero_pts).replace('R$ ', ''), p0(fu['p_zero'])))
    A('| parcial e depois alvo | +%d | +%s | %s |'
      % (round(alvo_pts), rs(alvo_pts).replace('R$ ', ''), p0(fu['p_alvo'])))
    if C.get('stop_outro') and not C.get('stop_fixo'):
        A('\n> **De onde vem esse stop.** Ele não é escolhido, é medido: entre %d e %d, o'
          % (C['stop'], C['stop_outro']))
        A('> de **%d** é o que dá a maior média diária somada nas duas bases nesta'
          % C['stop'])
        A('> configuração (só o setup A, com custo). Ele **mudou** na rodada em que o eixo')
        A('> do deslocamento do gatilho virou vaivém — antes dela o stop curto media melhor')
        A('> em tudo, e agora não mede mais. Se você preferir fixar um stop por gestão de')
        A('> risco em vez de por medição, é `STOP_FIXO` em `plano.py`.\n')
    A('\n**O stop não anda — nunca.** Ele entra a %d pontos e fica lá até o trade' % C['stop'])
    A('acabar. Isso não é descuido: com a parcial saindo na **mesma distância**, o stop')
    A('inicial **já é** a média da operação, e o trade que volta depois da parcial morre')
    A('em zero. Não há nada para arrastar, e arrastar seria estragar. Mover o stop para')
    A('longe continua sendo o erro que transforma uma perda planejada numa perda que não')
    A('estava no plano.\n')
    A('**A parcial não é opcional.** Ela é o que compra o direito de deixar o resto')
    A('correr até +%d sem risco. Sem ela o plano é outro, e os números são outros.\n'
      % C['alvo'])

    # ---------------------------------------------------------------- 5
    A('---\n\n## 5. Tamanho e limites do dia\n')
    A('**Risco por trade** = %d pontos = **%s por contrato**.\n'
      % (C['stop'], C['risco_rs']))
    A('Regra de dimensionamento:\n')
    A('```')
    A('contratos = (risco máximo por trade em R$) / %s' % C['risco_rs'])
    A('')
    A('com risco máximo por trade = 1% do capital da conta')
    A('```\n')
    A('**Limites rígidos do pregão** — atingiu, o dia acabou, sem discussão:\n')
    A('| limite | valor | por quê |')
    A('|---|---|---|')
    A('| **3 stops no dia** | −%d pts (%s / contrato) | o pior pregão medido foi %s pts |'
      % (C['limite_pts'], C['limite_rs'].replace('R$ ', 'R$ '), i0(fu['pior_dia'])))
    A('| **1 violação de regra** | — | erro de processo fecha o dia, mesmo no lucro |\n')
    A('O segundo limite é o mais importante e o mais fácil de ignorar. Um erro de')
    A('processo num dia de lucro é **mais perigoso** que um num dia de prejuízo,')
    A('porque o resultado o recompensa.\n')

    # ---------------------------------------------------------------- 6
    A('---\n\n## 6. A rotina do pregão\n')
    A('**Antes de abrir (5 minutos)**\n')
    A('- Gráfico em 10.000 ticks, indicadores da família carregados, EMAs %s visíveis'
      % C['emas'])
    A('- Anotar no diário: o regime de ontem, e onde as médias estão hoje')
    A('- Reler as regras 1 a 4 deste arquivo. Sim, todo dia.')
    A('- Definir o número de contratos **antes** do primeiro sinal\n')
    A('**Durante**\n')
    A('- Só existe ação quando a seta A imprime. O resto do tempo eu **espero**.')
    A('- Em ~%.1f trades por pregão, a maior parte do dia é espera. Isso é o trabalho,'
      % fu['por_pregao'])
    A('  não uma pausa dele.')
    A('- Enviada a ordem: uma barra. Preencheu ou cancelou.')
    A('- Aberta a posição: stop, parcial e alvo já estão definidos. Nada a decidir.\n')
    A('**Depois**\n')
    A('- Preencher o diário da § 9, **incluindo os sinais abortados**')
    A('- Calcular a **nota de aderência** do dia (§ 7)')
    A('- Não olhar o resultado acumulado. Ele é olhado uma vez por mês, na revisão.\n')

    # ---------------------------------------------------------------- 7
    A('---\n\n## 7. Como eu meço sucesso: aderência, não resultado\n')
    A('### 7.1 A razão, com os números\n')
    A('Estes são os números do setup A, stop %d, **descontando 5 pontos de custo por'
      % C['stop'])
    A('trade** — a leitura honesta, não a bruta:\n')
    A('| | WINV26 | WINFUT |')
    A('|---|---|---|')
    A('| acerto por trade | %s | %s |' % (p0(v26['acerto']), p0(fu['acerto'])))
    A('| valor esperado por trade | %s pts | %s pts |' % (n1(v26['ev']), n1(fu['ev'])))
    A('| **desvio** por trade | %s pts | %s pts |'
      % (i0(v26['sd_trade']), i0(fu['sd_trade'])))
    A('| pregões positivos | %s | %s |' % (p0(v26['dias_pos']), p0(fu['dias_pos'])))
    A('| pior pregão | %s pts | %s pts |' % (i0(v26['pior_dia']), i0(fu['pior_dia'])))
    A('| maior sequência de pregões negativos | %d | %d |'
      % (v26['seq_dias'], fu['seq_dias']))
    A('| chance de uma **semana** fechar negativa | %s | %s |'
      % (p0(v26['p_semana_neg']), p0(fu['p_semana_neg'])))
    A('| rebaixamento máximo | %s pts (%s) | %s pts (%s) |'
      % (i0(v26['dd']), rs(v26['dd']), i0(fu['dd']), rs(fu['dd'])))
    A('')
    A('Olhe a linha do **desvio**: %s pontos por trade, contra um valor esperado de'
      % i0(fu['sd_trade']))
    A('%s. O ruído é **três vezes maior que o sinal** em cada operação isolada.'
      % n1(fu['ev']))
    A('Isso não é um defeito da estratégia — é como toda vantagem pequena se parece')
    A('de perto.\n')
    A('As consequências, que eu preciso ter aceitado **antes** de elas acontecerem:\n')
    A('- **%s dos pregões fecham no vermelho.** Um dia negativo é o caso comum, não'
      % p0(100 - fu['dias_pos']))
    A('  um sinal de nada.')
    A('- **%d pregões negativos seguidos já aconteceram** na amostra medida. Vão'
      % fu['seq_dias'])
    A('  acontecer de novo.')
    A('- **%s de chance de uma semana inteira fechar negativa**, com a vantagem'
      % p0(fu['p_semana_neg']))
    A('  totalmente intacta.')
    A('- Duas perdas seguidas: %s de chance. Três: %s. Não é raro.'
      % (p0(100 * (1 - fu['acerto'] / 100.0) ** 2), p0(fu['p3'])))
    A('')
    A('**Conclusão operacional:** o resultado de um dia, e mesmo de uma semana, **não')
    A('contém informação** sobre se eu operei bem. Julgar o processo pelo resultado')
    A('diário é ler ruído como se fosse mensagem — e a reação a esse ruído é o que')
    A('destrói planos que funcionavam.\n')
    A('A aderência, ao contrário, eu **observo diretamente**, todo dia, sem erro de')
    A('medição. É a única coisa que eu controlo. Então é a única coisa que eu meço.\n')

    # ---------------------------------------------------------------- 7.2
    A('### 7.2 A nota de aderência\n')
    A('**Por trade** — seis itens, cada um vale 1:\n')
    A('| # | item |')
    A('|---|---|')
    A('| 1 | O contexto tinha as seis marcas da § 2, todas |')
    A('| 2 | Entrei pela limitada no meio do candle, no preço certo |')
    A('| 3 | A ordem valeu **uma barra**, e eu cancelei quando não preencheu |')
    A('| 4 | O stop entrou a %d pontos, imediatamente |' % C['stop'])
    A('| 5 | A parcial saiu a +%d (e o stop ficou onde estava) |' % C['parcial'])
    A('| 6 | Não mexi em nada depois disso |\n')
    A('**Por pregão** — quatro itens, cada um vale 1:\n')
    A('| # | item |')
    A('|---|---|')
    A('| 7 | Não operei nenhum sinal fora do setup A |')
    A('| 8 | Respeitei o limite de perda do dia |')
    A('| 9 | Registrei tudo no diário, inclusive os abortados |')
    A('| 10 | Não mudei o tamanho da posição no meio do pregão |\n')
    A('```')
    A('nota do dia = (pontos obtidos) / (pontos possíveis) × 100')
    A('```\n')
    A('**A regra que dá sentido a tudo isto:**\n')
    A('> **Um trade vencedor tomado fora das regras conta como FALHA.**')
    A('> Ele vale 0 na nota, e vale um registro em vermelho no diário.\n')
    A('Se essa regra não valer, a nota de aderência vira um enfeite: o resultado')
    A('volta a mandar, e o plano deixa de existir nos dias em que ele mais importa.\n')
    A('**Metas:**\n')
    A('- **≥ 95% na semana** — é o padrão de operação')
    A('- **< 90% na semana** — parar de operar e reler o plano; o problema é de')
    A('  execução, e mexer em parâmetro nesse estado só troca um problema por dois')
    A('- **100% num dia de prejuízo** — isso é um **dia bem-sucedido**. Anotar como tal.\n')

    # ---------------------------------------------------------------- 8
    A('---\n\n## 8. Os cinco erros que este plano existe para impedir\n')
    A('**1. Perseguir o sinal abortado.** "Ele foi embora sem mim." Vai acontecer com')
    A('%s dos sinais, todo mês. A regra da barra seguinte existe exatamente para'
      % p0(C['abort_pct']))
    A('tirar essa decisão da minha mão no momento em que eu estou menos apto a')
    A('tomá-la.\n')
    A('**2. Afastar o stop.** É o erro que muda a distribuição inteira: troca uma')
    A('perda de %d pontos, que estava no plano, por uma perda de tamanho'
      % C['stop'])
    A('desconhecido. Todos os números deste arquivo deixam de valer no instante em')
    A('que isso acontece uma vez.\n')
    A('**3. "Este aqui é diferente."** Setup C, sinal contra a tendência, entrada')
    A('sem gatilho. O setup C foi medido e perde nas duas bases; a intuição de que')
    A('*este* é diferente não tem como ser distinguida, no momento, do desejo de')
    A('operar.\n')
    A('**4. Mexer no lote pelo resultado.** Dobrar depois de perder é tentar')
    A('recuperar num trade o que a distribuição devolve em vinte. Aumentar depois de')
    A('ganhar é a mesma aposta, com o disfarce de confiança. O lote é definido antes')
    A('do pregão e não muda dentro dele.\n')
    A('**5. Operar por tédio.** São ~%.1f trades por pregão. A maior parte do dia é'
      % fu['por_pregao'])
    A('espera, e o tédio é uma sensação — não um sinal. Se eu não consigo esperar,')
    A('o problema não é a estratégia.\n')

    # ---------------------------------------------------------------- 9
    A('---\n\n## 9. O diário\n')
    A('Uma linha por **sinal** — inclusive os abortados.\n')
    A('| campo | o que anotar |')
    A('|---|---|')
    A('| data / hora | do fechamento da barra do gatilho |')
    A('| lado | compra ou venda |')
    A('| preço da limitada | o meio do candle, arredondado |')
    A('| preencheu? | sim / **abortado** |')
    A('| desfecho | alvo / zero a zero / stop / fim de pregão |')
    A('| pontos | resultado, em pontos |')
    A('| **nota de aderência** | 0 a 6 |')
    A('| **o que eu senti** | uma linha, honesta |\n')
    A('A última coluna é a que descobre os padrões. "Entrei com pressa porque o')
    A('anterior tinha stopado" é a informação que nenhuma métrica de desempenho')
    A('captura, e é onde estão os erros repetidos.\n')
    A('No fim do mês: contar quantos trades tiveram **nota 6**. Essa contagem é o')
    A('placar do mês. O resultado em reais é uma consequência, e será olhado depois')
    A('dela.\n')

    # ---------------------------------------------------------------- 10
    A('---\n\n## 10. Revisão e disjuntores\n')
    A('**A revisão é mensal, em data marcada.** Nunca no meio de uma sequência ruim,')
    A('nunca no meio de uma boa. Na revisão eu olho, nesta ordem:\n')
    A('1. A **nota de aderência** média do mês')
    A('2. Quantos sinais foram abortados, e se isso ficou perto de %s' % p0(C['abort_pct']))
    A('3. O resultado, em pontos, contra o valor esperado de %s por trade' % n1(fu['ev']))
    A('4. O **custo real** cobrado pela corretora, comparado com os 5 pontos por')
    A('   trade que os números desta página já descontam\n')
    A('**Disjuntores** — automáticos, não opinativos:\n')
    A('| gatilho | ação |')
    A('|---|---|')
    A('| rebaixamento de **%s pts** (%s) | reduzir o lote à metade |'
      % (i0(fu['dd']), rs(fu['dd'])))
    A('| rebaixamento de **%s pts** (%s) | parar de operar e reabrir o backtest |'
      % (i0(2 * fu['dd']), rs(2 * fu['dd'])))
    A('| aderência < 90%% na semana | parar de operar; treinar em simulador |')
    A('| 5 pregões negativos seguidos | parar por um dia e reler este arquivo |\n')
    A('O primeiro disjuntor está no **pior rebaixamento já medido**. Chegar nele é')
    A('normal. O segundo é o dobro dele: chegar lá já é evidência de que alguma')
    A('coisa mudou — no mercado ou em mim — e merece medição, não persistência.\n')
    A('O último é sobre estado mental, não sobre estatística: %d pregões negativos'
      % fu['seq_dias'])
    A('seguidos já aconteceram na amostra, então 5 não prova nada. Mas depois de 5 eu')
    A('não sou a mesma pessoa na frente da tela, e é essa pessoa que o disjuntor')
    A('protege.\n')

    # ---------------------------------------------------------------- 11
    A('---\n\n## 11. O que este plano herda de incerto\n')
    A('Ler antes de dimensionar posição. Está tudo em [RESULTADOS.md § 10](RESULTADOS.md).\n')
    A('- **Amostra pequena.** %d e %d pregões com trade. Os `t` medidos são bons, mas'
      % (v26['pregoes'], fu['pregoes']))
    A('  sobre poucas observações.')
    A('- **As duas bases não são independentes** — o WINFUT contém o WINV26 inteiro.')
    A('  Concordarem é menos confirmação do que parece.')
    A('- **Os parâmetros foram varridos nas mesmas bases** em que são avaliados. Há')
    A('  sobreajuste embutido, e o desempenho real tende a ser pior que o medido.')
    A('- **Fora da janela de calibração o setup A mede %s por trade** (t %s), com custo.'
      % (n1(C['oos']['A']['fora']['ev']), t2(C['oos']['A']['fora']['t'])))
    A('  É o número mais honesto deste arquivo.')
    A('- **A ordem limitada é dada por preenchida assim que o preço toca o nível.** Na')
    A('  prática existe fila, e nem todo toque preenche — este é o otimismo que mais')
    A('  pesa contra os números acima.')
    A('- **Sem filtro de horário, rolagem ou vencimento.**\n')
    if C['oos']['falhou']:
        A('O teste fora da amostra **não** foi passado. Isso é motivo para operar o plano')
        A('**sem dinheiro** — simulador ou tamanho mínimo — até que os seus próprios')
        A('registros, e não os meus, digam que ele funciona.\n')
    else:
        A('Nada disso é motivo para não operar o plano. É motivo para operá-lo **pequeno**')
        A('até que os seus próprios registros, e não os meus, digam que ele funciona.\n')

    return '\n'.join(L) + '\n'


# ============================================================ o texto (html)
def html(C, md_texto):
    """Converte as secoes em uma pagina de campo -- ver comentario no topo."""
    import molde_plano
    return molde_plano.render(C, md_texto)


if __name__ == '__main__':
    C = contexto()
    md = markdown(C)
    with io.open(DEST_MD, 'w', encoding='utf-8') as f:
        f.write(md)
    print('gravado: %s  (%.1f KB)' % (DEST_MD, len(md) / 1024.0))

    try:
        pagina = html(C, md)
    except ImportError:
        print('molde_plano.py ausente -- so o markdown foi gerado')
    else:
        with io.open(DEST_HTML, 'w', encoding='utf-8') as f:
            f.write(pagina)
        print('gravado: %s  (%.1f KB)' % (DEST_HTML, len(pagina) / 1024.0))
