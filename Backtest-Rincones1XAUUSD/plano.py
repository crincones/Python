# -*- coding: utf-8 -*-
"""
Gera PLANO.md e plano.html -- o plano operacional MANUAL, para o XAUUSD.

    python rodar.py     # primeiro, para atualizar saida/resumo.json
    python plano.py     # depois

Como o relatorio, nenhum numero e escrito a mao: tudo sai de
saida/resumo.json. O plano cita poucos numeros de proposito -- ele e um
procedimento, nao um relatorio -- mas os que cita sao os medidos.

A configuracao que o plano descreve e a recomendada em RESULTADOS.md 13:
o gatilho INTEIRO, sem filtro de regime, entrada A MERCADO.

O STOP e ESCOLHIDO PELA MEDICAO entre os stops que rodar.py mediu, e nao
escrito a mao -- do contrario o plano continuaria dizendo um numero depois
de uma rodada em que o outro passou a medir melhor. Para fixar um stop por
gestao de risco (e nao por medicao), ponha o valor em STOP_FIXO.
"""
import io
import json
import os

import molde_plano

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
DEST_MD = os.path.join(BASE, 'PLANO.md')
DEST_HTML = os.path.join(BASE, 'plano.html')

STOP_FIXO = None            # None = escolhe pela medicao | 7.0, 3.5... = fixa
CFG = 'tudo_c20'            # carteira completa, descontando 0,20 USD por trade
PRINC = 'COMPLETO'
HALVES = ('METADE_1', 'METADE_2')


# ------------------------------------------------------------ formatacao
def br(s):
    return s.replace('.', ',')


def n2(v):
    return '—' if v is None else br('%+.2f' % v)


def d2(v):
    return '—' if v is None else br('%.2f' % v)


def p0(v):
    return '—' if v is None else '%d%%' % round(v)


def dol(usd_por_onca, val_ponto):
    return br('USD %.2f' % (usd_por_onca * val_ponto))


# ------------------------------------------------------------ os numeros
def escolhe_stop(R):
    """Qual stop o plano descreve.

    Criterio: na configuracao do PLANO (carteira completa, com custo), o stop
    com a maior media diaria SOMADA nas duas metades. Media diaria, e nao EV
    por trade, porque o plano e um procedimento de pregao. As duas metades, e
    nao a amostra inteira, porque a amostra inteira contem as duas e escolher
    por ela deixaria uma metade decidir sozinha se a outra fosse fraca.
    """
    if STOP_FIXO is not None:
        return str(STOP_FIXO), None
    pontos = {}
    for st in R['stops']:
        pontos[str(st)] = sum(R['bases'][b]['psico'][str(st)][CFG]['media_dia']
                              for b in HALVES)
    melhor = max(pontos, key=pontos.get)
    outro = [k for k in pontos if k != melhor]
    return melhor, (outro[0] if outro else None)


def contexto():
    R = json.load(io.open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8'))
    P = R['parametros']
    STOP_PLANO, STOP_OUTRO = escolhe_stop(R)

    ps = R['bases'][PRINC]['psico'][STOP_PLANO][CFG]
    ps0 = R['bases'][PRINC]['psico'][STOP_PLANO]['tudo']   # sem custo
    h = {b: R['bases'][b]['psico'][STOP_PLANO][CFG] for b in HALVES}
    det = R['bases'][PRINC]
    st = float(STOP_PLANO)
    eixos = ('+'.join(P['EIXOS']) if isinstance(P['EIXOS'], (list, tuple))
             else str(P['EIXOS']).strip("()',").replace("', '", '+'))

    return dict(
        R=R, P=P, ps=ps, ps0=ps0, h=h, det=det,
        stop=d2(st), stop_v=st,
        stop_outro=(d2(float(STOP_OUTRO)) if STOP_OUTRO else None),
        stop_fixo=(STOP_FIXO is not None),
        parcial=d2(float(P['PARCIAL_EM'] or st)), alvo=d2(P['ALVO']),
        frac=int(100 * P['FRAC_PARCIAL']),
        nivel=d2(P['NIVEL_MIN']), corpo=int(P['CORPO_MAX']),
        pos=int(P['CORTE_POSICAO']), eixos=eixos,
        gatilho='[%s] ≥ %s' % (eixos, d2(P['NIVEL_MIN'])),
        gatilho_s='percentil do range · geometria invertida · corpo ≤ %d%%'
                  % int(P['CORPO_MAX']),
        emas='%d / %d / %d' % (P['EMA_R'], P['EMA_M'], P['EMA_L']),
        custo=d2(ps['custo']),
        risco_rs=dol(st, P['VAL_PONTO']),
        limite=d2(3 * st), limite_rs=dol(3 * st, P['VAL_PONTO']),
        dd_rs=dol(ps['dd'], P['VAL_PONTO']),
        val_ponto=int(P['VAL_PONTO']),
    )


# =========================================================== o texto (md)
def markdown(C):
    ps, ps0, h, P = C['ps'], C['ps0'], C['h'], C['P']
    L = []
    A = L.append

    A('# Plano operacional — XAUUSD, gráfico de 521 ticks\n')
    A('> **Este arquivo é gerado.** Rode `python rodar.py && python plano.py`.')
    A('> Os números saem de `saida/resumo.json`, os mesmos do')
    A('> [relatorio.html](relatorio.html). O texto do procedimento é fixo; se')
    A('> você mudar uma regra, mude aqui **e** em [ESTRATEGIA.md](ESTRATEGIA.md).\n')
    A('Companheiro operacional de [RESULTADOS.md](RESULTADOS.md). O relatório diz')
    A('**o que foi medido**; este arquivo diz **o que eu faço na frente da tela**.\n')
    A('Todos os valores em **USD por onça**. Um movimento de 1,00 vale %d USD num'
      % C['val_ponto'])
    A('lote padrão de 100 oz; num lote de 0,01 vale 1 USD. Os números abaixo já')
    A('descontam **%s USD de custo por trade**.\n' % C['custo'])

    # ---------------------------------------------------------------- 0
    A('---\n\n## 0. O contrato\n')
    A('Eu opero **um** gatilho, com **um** tamanho de risco, seguindo as regras 1 a')
    A('6 deste arquivo. As regras não mudam durante o pregão. Não mudam depois de')
    A('uma perda. Não mudam depois de um ganho. Mudam apenas na **revisão mensal**')
    A('da § 9, com os dados na mão.\n')
    A('A única coisa que eu avalio ao fim do dia é **se segui o plano** — não quanto')
    A('ganhei. A § 7 explica por quê, com os números que tornam isso não uma frase')
    A('bonita, mas a leitura correta dos dados.\n')
    A('Assinado: ____________________   Data: __ / __ / ____\n')

    # ---------------------------------------------------------------- 1
    A('---\n\n## 1. O que eu opero — e o que eu não opero\n')
    A('| | |')
    A('|---|---|')
    A('| **Ativo** | XAUUSD (ouro à vista) |')
    A('| **Gráfico** | candle de **521 ticks** |')
    A('| **Gatilho** | índice de esforço `%s`, lido **contra o candle** |'
      % C['gatilho'])
    A('| **Filtro de forma** | corpo ≤ %d%% do range, meio do corpo **do lado '
      'oposto ao pavio** |' % C['corpo'])
    A('| **Lado** | compra e venda |')
    A('| **Posições** | **uma por vez**. Sinal que chega com posição aberta é '
      'ignorado |\n')
    A('**O que eu NÃO faço:**\n')
    A('- **Não filtro por regime de média.** Medido, o filtro subtrai neste ativo:')
    A('  a carteira que pega todo gatilho mede mais que qualquer subconjunto A/B/C,')
    A('  e nas duas metades da amostra. Se o gatilho saiu, eu opero.')
    A('- **Não uso a geometria clássica.** No WIN a barra de exaustão tem o pavio em')
    A('  cima numa alta. **No ouro é o contrário**, e operar a forma clássica aqui')
    A('  mede negativo. Se eu me pegar procurando o shooting star, parei de operar')
    A('  este plano.')
    A('- **Não uso ordem limitada.** Ver § 3 — é o erro mais caro possível aqui, e é')
    A('  exatamente o hábito que vem do plano do WIN.')
    A('- **Qualquer coisa que o indicador não marcou.** Se não saiu a seta, não')
    A('  existe trade — por mais óbvio que o gráfico pareça.\n')
    A('> São **%s trades por pregão**, mais que o dobro do plano do WIN. O gráfico'
      % br('%.1f' % ps['por_pregao']))
    A('> de 521 ticks do ouro faz cerca de 800 barras por pregão e roda quase 24')
    A('> horas: **escolha uma janela de horário fixa** e opere só dentro dela. O')
    A('> backtest não a impõe, e por isso ela é uma decisão sua — mas operar 24h à')
    A('> mão não é o mesmo procedimento que foi medido.\n')

    # ---------------------------------------------------------------- 2
    A('---\n\n## 2. O gatilho — quando existe trade\n')
    A('O indicador faz a conta; eu confiro o contexto. **Todos os cinco** têm de')
    A('estar verdadeiros. Um único "não" e não há trade.\n')
    A('| # | Verificação | |')
    A('|---|---|---|')
    A('| 1 | O indicador marcou a seta | ☐ |')
    A('| 2 | A barra do gatilho é visivelmente **larga** para o trecho recente | ☐ |')
    A('| 3 | O **corpo é pequeno** e está do lado do fechamento, com o pavio grande '
      'do lado oposto | ☐ |')
    A('| 4 | A seta aponta **contra** a direção do candle | ☐ |')
    A('| 5 | Estou dentro do horário e **sem posição aberta** | ☐ |\n')
    A('Os itens 1 a 4 já embutem o que o indicador mede: percentil de range ≥ %s'
      % C['nivel'])
    A('nas últimas %d barras válidas, corpo ≤ %d%% do range, e meio do corpo além'
      % (P['PERIODO_REF'], C['corpo']))
    A('de %d%% do range no lado do fechamento.\n' % C['pos'])
    A('**A leitura econômica, em uma frase:** a barra andou muito para o tamanho')
    A('recente, fechou colada no extremo, e o caminho todo foi feito de um lado só —')
    A('e é justamente essa barra que o ouro devolve. Eu entro contra ela.\n')
    A('> **Por que a forma é invertida aqui, e não no WIN.** Não há explicação')
    A('> confirmada, e o plano não finge que há. O que existe é a medição, repetida')
    A('> três vezes em gráficos sintéticos diferentes do mesmo ativo')
    A('> (`Delta_Fraqueza.mqh`, `Ticks_Esforco_v2.mqh` e este backtest). Eu opero o')
    A('> que mede.\n')

    # ---------------------------------------------------------------- 3
    A('---\n\n## 3. A entrada — a mercado, e só\n')
    A('```')
    A('barra t      o gatilho fecha. Eu entro A MERCADO, imediatamente.')
    A('             Sem ordem limitada. Sem esperar repique.')
    A('barra t+1    se eu não entrei na barra t, o sinal morreu.')
    A('```\n')
    A('**Esta é a regra que eu mais vou querer quebrar**, porque o plano do WIN faz')
    A('o contrário: lá a entrada é uma limitada no meio do candle, válida por uma')
    A('barra. Aqui essa mesma ordem custa **%s por trade** e vira o resultado de'
      % n2((C['R']['entrada']['grid'][PRINC]['fecha'][str(C['stop_v'])]['ev'] or 0)
           - (C['R']['entrada']['grid'][PRINC]['meio'][str(C['stop_v'])]['ev'] or 0)))
    A('positivo para negativo.\n')
    A('O motivo é geométrico, não estatístico. A barra do gatilho fecha colada num')
    A('extremo (é o filtro da § 2). O meio dela fica, portanto, do lado **errado** do')
    A('fechamento: numa barra de alta, o meio está **abaixo** do fechamento, e uma')
    A('venda limitada ali é meio range de desconto entregue de graça. E a ordem')
    A('preenche quase sempre — o preço já está do lado dela. Não é uma ordem que')
    A('espera um preço melhor: é uma ordem que garante um preço pior.\n')
    A('> No plano do WIN a mesma regra é boa, pela mesma geometria de cabeça para')
    A('> baixo: lá o corpo está embaixo numa barra de alta, o meio fica **acima** do')
    A('> fechamento, e a limitada de fato espera um repique. **A regra não é boa nem')
    A('> ruim — ela depende de onde o candle fecha.**\n')

    # ---------------------------------------------------------------- 4
    A('---\n\n## 4. A gestão — o que já está decidido antes de entrar\n')
    A('| | valor | por lote de 100 oz |')
    A('|---|---:|---:|')
    A('| **Stop inicial** | %s | %s |' % (C['stop'], C['risco_rs']))
    A('| **Parcial** (%d%% da posição) | +%s | — |' % (C['frac'], C['parcial']))
    A('| **Alvo** (restante) | +%s | — |' % C['alvo'])
    A('| **Limite do dia** | 3 stops = %s | %s |' % (C['limite'], C['limite_rs']))
    A('')
    A('A parcial sai na **mesma distância do stop**. Isso não é gosto: com meia')
    A('posição realizada a essa distância, a **média da operação** cai exatamente em')
    A('cima do stop inicial. O stop **não anda** — a operação é que passou a valer')
    A('zero ali. Se o preço voltar e pegar o stop depois da parcial, o trade fecha')
    A('em **zero de verdade**, não em "zero a zero" que paga alguma coisa.\n')
    A('**O stop nunca se afasta e nunca se move para fora.** Se eu estiver com')
    A('vontade de dar mais espaço, a operação já acabou.\n')
    if C['stop_outro'] and not C['stop_fixo']:
        A('> **Por que %s e não %s.** Os dois foram medidos com todo o resto igual.'
          % (C['stop'], C['stop_outro']))
        A('> O escolhido é o que soma a maior média diária nas duas metades da')
        A('> amostra. O motivo estrutural: a barra do gatilho é, por construção, uma')
        A('> barra de range extremo — um stop pequeno demais **cabe dentro dela** e')
        A('> é acionado pelo próprio ruído da barra que gerou o sinal.\n')

    # ---------------------------------------------------------------- 5
    A('---\n\n## 5. Os limites do dia\n')
    A('| Disjuntor | Ação |')
    A('|---|---|')
    A('| **3 stops no dia** | Fecho a plataforma. Não há "recuperar". |')
    A('| **1 violação de regra** | Fecho a plataforma, mesmo no lucro. |')
    A('| **Pior pregão medido: %s** | Se o dia passar disso, algo está errado com a '
      'execução, não com o mercado. |' % n2(ps['pior_dia']))
    A('')
    A('O pior pregão da amostra foi **%s** (%s por lote) e o maior rebaixamento'
      % (n2(ps['pior_dia']), dol(ps['pior_dia'], P['VAL_PONTO'])))
    A('acumulado foi **%s** (%s). Dimensione a posição por esse número, não pela'
      % (br('%.2f' % ps['dd']), C['dd_rs']))
    A('média.\n')

    # ---------------------------------------------------------------- 6
    A('---\n\n## 6. O registro — cinco linhas por trade\n')
    A('```')
    A('data / hora     __________     lado  compra / venda')
    A('entrada         __________     stop  __________   alvo __________')
    A('desfecho        alvo / stop / zero a zero / fim do pregão')
    A('resultado       __________ USD')
    A('aderência       segui as 5 verificações?   sim / não')
    A('```\n')
    A('**Um trade vencedor tomado fora das regras conta como falha.** Ele vale zero')
    A('na nota de aderência e entra em vermelho no diário. Sem esta regra a nota vira')
    A('enfeite, e o resultado volta a mandar justamente nos dias em que o plano mais')
    A('importa.\n')

    # ---------------------------------------------------------------- 7
    A('---\n\n## 7. O que esperar — a forma do desempenho\n')
    A('| | amostra inteira | 1ª metade | 2ª metade |')
    A('|---|---:|---:|---:|')
    for rot, k, fmt in (
            ('trades por pregão', 'por_pregao', lambda v: br('%.1f' % v)),
            ('acerto', 'acerto', lambda v: br('%.1f%%' % v)),
            ('resultado médio por trade', 'ev', lambda v: n2(v)),
            ('resultado médio por pregão', 'media_dia', lambda v: n2(v)),
            ('pregões positivos', 'dias_pos', lambda v: p0(v)),
            ('pior pregão', 'pior_dia', lambda v: n2(v)),
            ('maior sequência sem ganhar', 'seq_trades', lambda v: '%d trades' % v),
            ('maior sequência de pregões negativos', 'seq_dias',
             lambda v: '%d pregões' % v),
            ('chance de uma semana negativa', 'p_semana_neg', lambda v: p0(v)),
            ('chance de um mês negativo', 'p_mes_neg', lambda v: p0(v))):
        A('| %s | %s | %s | %s |'
          % (rot, fmt(ps[k]), fmt(h['METADE_1'][k]), fmt(h['METADE_2'][k])))
    A('')
    A('**Leia a linha do acerto antes de operar.** São %s: a maioria das operações'
      % br('%.1f%%' % ps['acerto']))
    A('**perde**, e o resultado vem do tamanho dos ganhos, não da frequência deles.')
    A('Já houve **%d trades seguidos sem ganhar** e **%d pregões negativos seguidos**'
      % (ps['seq_trades'], ps['seq_dias']))
    A('dentro de uma amostra em que a vantagem estava intacta o tempo todo. Uma')
    A('semana fecha no vermelho em %s das vezes e um mês em %s.\n'
      % (p0(ps['p_semana_neg']), p0(ps['p_mes_neg'])))
    A('Se eu abandonar o plano depois de %d perdas seguidas, eu vou abandoná-lo num'
      % ps['seq_trades'])
    A('intervalo que o próprio backtest previa que aconteceria.\n')
    A('Desfechos: **%s** batem o alvo, **%s** morrem no stop, **%s** saem em zero a'
      % (br('%.1f%%' % ps['p_alvo']), br('%.1f%%' % ps['p_stop']),
         br('%.1f%%' % ps['p_zero'])))
    A('zero e **%s** fecham no fim do pregão.\n' % br('%.1f%%' % ps['p_fim']))

    # ---------------------------------------------------------------- 8
    A('---\n\n## 8. O que este plano NÃO tem\n')
    A('- **Confirmação fora da amostra.** As duas metades são o mesmo histórico de')
    A('  %d pregões partido ao meio, não dois instrumentos. No plano do WIN havia'
      % C['det']['pregoes'])
    A('  dois contratos, e a concordância entre eles valia como evidência; aqui não')
    A('  vale — vale só como evidência de que o resultado não vem de um pedaço do')
    A('  período.')
    A('- **Um corte validado.** O nível %s e o corte de posição %d saíram de uma'
      % (C['nivel'], C['pos']))
    A('  varredura sobre esta mesma amostra. A região é larga (§ 10 do relatório),')
    A('  mas larga não é validada.')
    A('- **Margem folgada para custo.** Com %s USD por trade a vantagem sobrevive;'
      % C['custo'])
    A('  com o dobro ela encolhe muito. **Meça o seu spread real** antes de')
    A('  dimensionar, e não opere isto em horário de spread alargado.')
    A('- **Uma janela de horário.** O ouro roda quase 24 horas e o backtest opera o')
    A('  pregão inteiro. Escolher a janela é decisão sua, e ela muda os números.\n')

    # ---------------------------------------------------------------- 9
    A('---\n\n## 9. A revisão mensal\n')
    A('Uma vez por mês, com o diário na mão, e **nunca** durante o pregão:\n')
    A('1. Rodar `python rodar.py && python relatorio.py && python plano.py` com o')
    A('   histórico atualizado.')
    A('2. Comparar a **nota de aderência** do mês com a do anterior. Ela vem antes')
    A('   do resultado.')
    A('3. Comparar o acerto e o EV medidos com os da § 7. Divergência grande com')
    A('   aderência alta é sinal de que o mercado mudou; divergência grande com')
    A('   aderência baixa é sinal de que **eu** mudei.')
    A('4. Só então decidir se alguma regra muda — e escrever a mudança aqui e em')
    A('   `ESTRATEGIA.md` antes do próximo pregão.\n')
    A('> Sem custo nenhum a estratégia mede %s por trade; com %s de custo, %s. A'
      % (n2(ps0['ev']), C['custo'], n2(ps['ev'])))
    A('> diferença entre esses dois números é o que a execução decide, e é a única')
    A('> parte do resultado que está sob meu controle.\n')

    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    C = contexto()
    md = markdown(C)
    with open(DEST_MD, 'w', encoding='utf-8') as f:
        f.write(md)
    html = molde_plano.render(C, md)
    with open(DEST_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    print('PLANO.md e plano.html gravados (%.1f KB / %.1f KB)'
          % (len(md.encode('utf-8')) / 1024, len(html.encode('utf-8')) / 1024))
