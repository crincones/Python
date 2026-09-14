# -*- coding: utf-8 -*-
"""
Gera PLANO.md e plano.html -- o plano operacional MANUAL.

    python rodar.py     # primeiro, para atualizar saida/resumo.json
    python plano.py     # depois

Como o relatorio, nenhum numero e escrito a mao: tudo sai de
saida/resumo.json. O plano cita poucos numeros de proposito -- ele e um
procedimento, nao um relatorio -- mas os que cita sao os medidos, e com o
custo de 5 pontos por trade ja descontado (o bruto e piso otimista).

A configuracao que o plano descreve e a padrao da engine: setups D + T,
nivel do gatilho em NIVEL_MIN, entrada limitada valida por UMA barra e
stop dimensionado pelo ATR.
"""
import io
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
DEST_MD = os.path.join(BASE, 'PLANO.md')
DEST_HTML = os.path.join(BASE, 'plano.html')

VAL_PONTO = 0.20            # R$ por ponto, 1 contrato WIN
# O plano fala da base MAIOR: o WINFUT tem 44 pregoes cheios contra 14 do
# WINV26, e e dele que saem as expectativas de rotina.
BASE_PLANO = 'WINFUT'


# ------------------------------------------------------------ formatacao
def n1(v):
    return '—' if v is None else ('%+.1f' % v).replace('.', ',')


def p0(v):
    return '—' if v is None else '%d%%' % round(v)


def i0(v):
    return '—' if v is None else '%d' % round(v)


def rs(pontos):
    return ('R$ %.2f' % (pontos * VAL_PONTO)).replace('.', ',')


def vg(v):
    s = str(v)
    if s.endswith('.0'):
        s = s[:-2]
    return s.replace('.', ',')


# ------------------------------------------------------------ os numeros
def contexto():
    R = json.load(io.open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8'))
    P = R['parametros']
    fu = R['bases'][BASE_PLANO]['psico']['c5']
    v26 = R['bases']['WINV26']['psico']['c5']

    # abortos: quantos sinais nao viram trade por causa da regra da barra
    ab = {}
    for b in ('WINV26', 'WINFUT'):
        d = R['bases'][b]
        ab[b] = (d['sinais'], d['entrada_meio']['n'])
    tot_s = sum(x[0] for x in ab.values())
    tot_n = sum(x[1] for x in ab.values())

    stop_tipico = int(round(fu['stop_medio'] / 5.0) * 5)
    at = R['nivel']['atual']
    seletivo = R['nivel']['niveis'][R['nivel']['niveis'].index(at) + 1] \
        if R['nivel']['niveis'].index(at) + 1 < len(R['nivel']['niveis']) else None

    return dict(
        R=R, fu=fu, v26=v26, base=BASE_PLANO,
        stop=stop_tipico,
        stop_min=int(fu['stop_min']), stop_max=int(fu['stop_max']),
        stop_atr=vg(P['STOP_ATR']),
        stop_rot='%s × ATR' % vg(P['STOP_ATR']),
        alvo=int(P['ALVO']), frac=int(100 * P['FRAC_PARCIAL']),
        nivel=('%.2f' % P['NIVEL_MIN']).replace('.', ','),
        seletivo=None if seletivo is None else ('%.2f' % float(seletivo)).replace('.', ','),
        corpo=int(P['CORPO_MAX']),
        ema_per=P['EMA_PER'], hma_per=P['HMA_PER'], atr_per=P['ATR_PER'],
        kelt=vg(P['KELT_INT']), prof=vg(P['PROF_MAX']),
        abort_pct=round(100.0 * (tot_s - tot_n) / tot_s),
        ab=ab,
        risco_rs=rs(stop_tipico),
        limite_pts=3 * stop_tipico,
        limite_rs=rs(3 * stop_tipico),
        dd_rs=rs(fu['dd']),
    )


# =========================================================== o texto (md)
def markdown(C):
    fu, v26 = C['fu'], C['v26']
    L = []
    A = L.append

    A('# Plano operacional — WIN, gráfico de 10.000 ticks (DTA)\n')
    A('> **Este arquivo é gerado.** Rode `python rodar.py && python plano.py`.')
    A('> Os números saem de `saida/resumo.json`, os mesmos do')
    A('> [relatorio.html](relatorio.html). Os números de desempenho das §§ 4, 7 e 10')
    A('> **descontam 5 pontos de custo por trade**; os de comparação entre regras são')
    A('> brutos, como no relatório. O texto do procedimento é fixo; se você mudar uma')
    A('> regra, mude aqui')
    A('> **e** em [ESTRATEGIA.md](ESTRATEGIA.md).\n')
    A('Companheiro operacional de [RESULTADOS.md](RESULTADOS.md). O relatório diz')
    A('**o que foi medido**; este arquivo diz **o que eu faço na frente da tela**.\n')

    # ---------------------------------------------------------------- 0
    A('---\n\n## 0. O contrato\n')
    A('Eu opero **um** setup principal, com **um** tamanho de risco, seguindo as')
    A('regras 1 a 6 deste arquivo. As regras não mudam durante o pregão. Não mudam')
    A('depois de uma perda. Não mudam depois de um ganho. Mudam apenas na **revisão')
    A('mensal** da § 10, com os dados na mão.\n')
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
    A('| **Contexto na tela** | EMA %d · Hull %d · Keltner ±%s ATR(%d) em volta da EMA |'
      % (C['ema_per'], C['hma_per'], C['kelt'], C['atr_per']))
    A('| **Setup** | **D — descolamento da Hull**. O T entra pelas mesmas regras de gestão e é raro |')
    A('| **Lado** | compra e venda |')
    A('| **Posições** | **uma por vez**. Sinal que chega com posição aberta é ignorado |\n')
    A('**O que eu NÃO opero:**\n')
    A('- **Reversão na banda de Keltner.** É o uso de manual do canal e foi medido:')
    A('  negativo no WINFUT em toda configuração testada. Preço esticado é onde eu')
    A('  **não** opero, não onde eu vendo topo.')
    A('- **Rejeição de banda (setup K).** Mede positivo sozinho e mesmo assim piora a')
    A('  carteira, porque ocupa a vaga de um trade melhor. Fora até uma revisão')
    A('  decidir o contrário.')
    A('- **Qualquer coisa que o indicador não marcou.** Se não saiu a seta, não existe')
    A('  trade — por mais óbvio que o gráfico pareça.\n')
    A('> **A leitura econômica, em uma frase:** o indicador acende quando alguém')
    A('> gastou muito e não levou o preço. Isso é absorção, e absorção se desfaz. A')
    A('> Hull diz se havia movimento para desfazer (inclinada) e de que lado o preço')
    A('> está em relação a ele. Eu entro do lado de quem **não** falhou.\n')

    # ---------------------------------------------------------------- 2
    A('---\n\n## 2. O gatilho — quando existe trade\n')
    A('O indicador faz a conta; eu confiro o contexto. **Todos os seis** têm de')
    A('estar verdadeiros. Um único "não" e não há trade.\n')
    A('| # | Verificação | |')
    A('|---|---|---|')
    A('| 1 | O indicador marcou a seta, com índice ≥ **%s** | ☐ |' % C['nivel'])
    A('| 2 | A **Hull %d está inclinada** — subindo ou descendo, mas nunca deitada | ☐ |'
      % C['hma_per'])
    A('| 3 | O close está do lado **oposto** ao da Hull: eu compro **abaixo** dela, vendo **acima** | ☐ |')
    A('| 4 | O preço está **dentro do canal** — não encostou na banda de %s ATR | ☐ |' % C['kelt'])
    A('| 5 | O mergulho até a EMA %d é de no máximo **%s ATR** — não é queda livre | ☐ |'
      % (C['ema_per'], C['prof']))
    A('| 6 | Estou dentro do horário e **sem posição aberta** | ☐ |\n')
    A('O item 1 já embute o que o indicador mede e eu não preciso conferir a olho:')
    A('índice de esforço ≥ %s, corpo ≤ %d%% do range, e o meio do corpo do lado certo.'
      % (C['nivel'], C['corpo']))
    A('Os itens 2 e 3 são a regra que o backtest achou e que **contraria a leitura de')
    A('manual**: não é "comprar acima de uma Hull que sobe", é comprar **abaixo** dela')
    A('quando ela está inclinada. Se isso soar errado na hora, releia a § 3 do')
    A('relatório antes de improvisar.\n')
    A('> **O item 2 é o mais importante da lista.** Hull deitada é o pior contexto')
    A('> medido: %s pontos por trade no WINV26 e %s no WINFUT. Se só uma linha deste'
      % (n1(C['R']['hull']['baldes']['WINV26'][4]['ev']),
         n1(C['R']['hull']['baldes']['WINFUT'][4]['ev'])))
    A('> plano sobreviver, que seja esta.\n')

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
    A('Cerca de **%s dos sinais serão abortados** — no WINV26, %d de %d; no WINFUT,'
      % (p0(C['abort_pct']), C['ab']['WINV26'][0] - C['ab']['WINV26'][1],
         C['ab']['WINV26'][0]))
    A('%d de %d. Isso não é falha de execução: é **o plano funcionando**. Um sinal'
      % (C['ab']['WINFUT'][0] - C['ab']['WINFUT'][1], C['ab']['WINFUT'][0]))
    A('abortado entra no diário como *aderência cumprida*, exatamente como um trade')
    A('vencedor.\n')
    e = C['R']['bases'][C['base']]
    A('> **Aqui a regra não é só disciplina — ela paga.** A limitada mede %s por'
      % n1(e['entrada_meio']['ev']))
    A('> trade contra %s da entrada a mercado, e contra %s da limitada deixada viva'
      % (n1(e['entrada_fecha']['ev']), n1(e['fill_livre']['ev'])))
    A('> até o fim do pregão. Entrar no meio do candle do gatilho **é** parte da')
    A('> vantagem.\n')

    # ---------------------------------------------------------------- 4
    A('---\n\n## 4. A gestão — decidida antes, executada sem opinião\n')
    A('O stop **não é um número fixo**: ele é %s da barra do sinal, com piso de %d e'
      % (C['stop_rot'], C['R']['parametros']['STOP_MIN']))
    A('teto de %d pontos. Em pregão parado ele encolhe, em pregão violento ele abre —'
      % C['R']['parametros']['STOP_MAX'])
    A('e é isso que faz o risco por trade ser o mesmo em regimes diferentes. Na')
    A('amostra medida ele ficou entre **%d e %d pontos**, com média de **%d**.\n'
      % (C['stop_min'], C['stop_max'], round(fu['stop_medio'])))
    A('| | |')
    A('|---|---|')
    A('| **Stop inicial** | **%s** da barra do gatilho ≈ %d pontos |'
      % (C['stop_rot'], C['stop']))
    A('| **Parcial** | **%d%% da posição na MESMA distância do stop** |' % C['frac'])
    A('| **No momento da parcial** | **nada a fazer.** O stop já está na média da '
      'operação: com meia posição realizada na distância do stop, o stop inicial '
      '**é** o zero a zero |')
    A('| **Alvo do restante** | **+%d pontos** |' % C['alvo'])
    A('| **Saída forçada** | fechamento do pregão |\n')
    A('**Tabela de conversão — leia o ATR e use a linha:**\n')
    A('| ATR na hora do sinal | stop e parcial | alvo |')
    A('|---|---|---|')
    for atr in (80, 100, 120, 150, 200):
        st = int(round(float(C['stop_atr'].replace(',', '.')) * atr / 5.0) * 5)
        A('| %d | %d pts (%s) | +%d |' % (atr, st, rs(st), C['alvo']))
    A('')
    A('Resultado por trade, por contrato de lote cheio, com o stop típico de %d:\n'
      % C['stop'])
    A('| desfecho | pontos | R$ | frequência medida |')
    A('|---|---|---|---|')
    A('| stop antes da parcial | −%d | −%s | %s |'
      % (C['stop'], rs(C['stop']).replace('R$ ', ''), p0(fu['p_stop'])))
    A('| parcial e depois o stop | 0 | R$ 0,00 | %s |' % p0(fu['p_zero']))
    alvo_pts = (C['frac'] * C['stop'] + (100 - C['frac']) * C['alvo']) / 100.0
    A('| parcial e depois alvo | +%d | +%s | %s |'
      % (round(alvo_pts), rs(alvo_pts).replace('R$ ', ''), p0(fu['p_alvo'])))
    A('| fim de pregão | o que estiver | — | %s |' % p0(fu['p_fim']))
    A('')
    A('**O stop não anda — nunca.** Ele entra na distância do ATR e fica lá até o')
    A('trade acabar. Com a parcial saindo na **mesma distância**, o stop inicial **já')
    A('é** a média da operação, e o trade que volta depois da parcial morre em zero.')
    A('Não há nada para arrastar, e arrastar seria estragar.\n')
    A('**A parcial não é opcional.** Ela é o que compra o direito de deixar o resto')
    A('correr até +%d sem risco. Sem ela o plano é outro, e os números são outros.\n'
      % C['alvo'])

    # ---------------------------------------------------------------- 5
    A('---\n\n## 5. Tamanho e limites do dia\n')
    A('**Risco por trade** = o stop do trade = **%s por contrato** no stop típico'
      % C['risco_rs'])
    A('de %d pontos.\n' % C['stop'])
    A('Regra de dimensionamento:\n')
    A('```')
    A('contratos = (1% do capital) / (stop do trade em pontos x R$ 0,20)')
    A('')
    A('com o stop lido da tabela da § 4, ANTES de enviar a ordem')
    A('```\n')
    A('Como o stop varia, o **número de contratos varia junto** — é assim que o risco')
    A('em reais fica constante. Em pregão de ATR alto eu opero menos contratos, não')
    A('o mesmo lote com stop maior.\n')
    A('**Limites rígidos do pregão** — atingiu, o dia acabou, sem discussão:\n')
    A('| limite | valor | por quê |')
    A('|---|---|---|')
    A('| **3 stops no dia** | ≈ −%d pts (%s / contrato) | o pior pregão medido foi %s pts |'
      % (C['limite_pts'], C['limite_rs'], i0(fu['pior_dia'])))
    A('| **1 violação de regra** | — | erro de processo fecha o dia, mesmo no lucro |\n')
    A('O segundo limite é o mais importante e o mais fácil de ignorar. Um erro de')
    A('processo num dia de lucro é **mais perigoso** que um num dia de prejuízo,')
    A('porque o resultado o recompensa.\n')

    # ---------------------------------------------------------------- 6
    A('---\n\n## 6. A rotina do pregão\n')
    A('**Antes de abrir (5 minutos)**\n')
    A('- Gráfico em 10.000 ticks; EMA %d, Hull %d e o canal de Keltner na tela;'
      % (C['ema_per'], C['hma_per']))
    A('  o histograma de esforço na subjanela')
    A('- **Ler o ATR(%d) e anotar o stop do dia** pela tabela da § 4' % C['atr_per'])
    A('- Definir o número de contratos **antes** do primeiro sinal')
    A('- Reler as regras 1 a 4 deste arquivo. Sim, todo dia.\n')
    A('**Durante**\n')
    A('- Só existe ação quando a seta imprime. O resto do tempo eu **espero**.')
    A('- Em ~%s trades por pregão, a maior parte do dia é espera. Isso é o trabalho,'
      % ('%.1f' % fu['por_pregao']).replace('.', ','))
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
    A('Carteira D + T, gestão padrão, **descontando 5 pontos de custo por trade** —')
    A('a leitura honesta, não a bruta:\n')
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
    A('%s. O ruído é várias vezes maior que o sinal em cada operação isolada. Isso'
      % n1(fu['ev']))
    A('não é um defeito da estratégia — é como toda vantagem pequena se parece de')
    A('perto.\n')
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
    A('| 4 | O stop entrou na distância do ATR, imediatamente |')
    A('| 5 | A parcial saiu na mesma distância (e o stop ficou onde estava) |')
    A('| 6 | Não mexi em nada depois disso |\n')
    A('**Por pregão** — quatro itens, cada um vale 1:\n')
    A('| # | item |')
    A('|---|---|')
    A('| 7 | Não operei nenhum sinal fora dos setups D e T |')
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
    A('**1. Operar a Hull como manual manda.** Comprar acima de uma Hull que sobe é a')
    A('leitura natural, e é a que mede **pior** com este gatilho. Quando a mão coçar')
    A('para entrar "a favor", é exatamente o momento em que o backtest diz não.\n')
    A('**2. Perseguir o sinal abortado.** "Ele foi embora sem mim." Vai acontecer com')
    A('%s dos sinais, todo mês. A regra da barra seguinte existe para tirar essa'
      % p0(C['abort_pct']))
    A('decisão da minha mão no momento em que eu estou menos apto a tomá-la.\n')
    A('**3. Afastar o stop.** É o erro que muda a distribuição inteira: troca uma')
    A('perda planejada por uma perda de tamanho desconhecido. Todos os números deste')
    A('arquivo deixam de valer no instante em que isso acontece uma vez.\n')
    A('**4. Vender topo na banda.** O canal de Keltner está na tela como **régua de')
    A('esticamento**, não como gatilho. Reversão na banda foi medida e perde. Se eu me')
    A('pegar operando a banda, eu estou operando outro plano — sem backtest.\n')
    A('**5. Mexer no lote pelo resultado.** Dobrar depois de perder é tentar')
    A('recuperar num trade o que a distribuição devolve em vinte. Aumentar depois de')
    A('ganhar é a mesma aposta, com o disfarce de confiança. O lote sai da conta da')
    A('§ 5, com o ATR do dia, e não muda dentro do pregão.\n')

    # ---------------------------------------------------------------- 9
    A('---\n\n## 9. O diário\n')
    A('Uma linha por **sinal** — inclusive os abortados.\n')
    A('| campo | o que anotar |')
    A('|---|---|')
    A('| data / hora | do fechamento da barra do gatilho |')
    A('| lado | compra ou venda |')
    A('| ATR e stop usado | o que a tabela da § 4 mandou |')
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
    A('   trade que os números desta página já descontam')
    if C['seletivo']:
        A('5. Se o ritmo está cansativo, **subir o nível do gatilho de %s para %s** —'
          % (C['nivel'], C['seletivo']))
        A('   é a alavanca medida para ter menos sinais e mais qualidade, e está na')
        A('   § 05 do relatório')
    A('')
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
    A('Ler antes de dimensionar posição. Está tudo em')
    A('[RESULTADOS.md § 14](RESULTADOS.md).\n')
    A('- **Amostra pequena.** %d e %d pregões com trade, dois meses de mercado.'
      % (v26['pregoes'], fu['pregoes']))
    A('- **As duas bases não são independentes** — o WINFUT contém o WINV26 inteiro.')
    A('  Concordarem é menos confirmação do que parece.')
    A('- **As regras saíram destas mesmas bases.** O lado da Hull, o veto da Hull')
    A('  plana, o nível do gatilho e o tamanho do stop foram escolhidos olhando estes')
    A('  dois arquivos. Há sobreajuste embutido, e o desempenho real tende a ser pior')
    A('  que o medido.')
    A('- **A ordem limitada é dada por preenchida assim que o preço toca o nível.** Na')
    A('  prática existe fila, e nem todo toque preenche — este é o otimismo que mais')
    A('  pesa contra os números acima.')
    A('- **Sem filtro de horário, rolagem ou vencimento.**\n')
    A('Nada disso é motivo para não operar o plano. É motivo para operá-lo **pequeno**')
    A('até que os seus próprios registros, e não os meus, digam que ele funciona.\n')

    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    C = contexto()
    md = markdown(C)
    with io.open(DEST_MD, 'w', encoding='utf-8') as f:
        f.write(md)
    print('gravado: %s  (%.1f KB)' % (DEST_MD, len(md) / 1024.0))

    try:
        import molde_plano
    except ImportError:
        print('molde_plano.py ausente -- so o markdown foi gerado')
    else:
        pagina = molde_plano.render(C, md)
        with io.open(DEST_HTML, 'w', encoding='utf-8') as f:
            f.write(pagina)
        print('gravado: %s  (%.1f KB)' % (DEST_HTML, len(pagina) / 1024.0))
