# -*- coding: utf-8 -*-
"""
Os tres padroes -- OURO, PRATA e BRONZE -- e os filtros que os separam.

O CLAUDE.md pede para "avaliar e mostrar graficamente quais sao as
melhores operacoes, conforme a forma encontrada, Padrao Ouro, Prata e
Bronze, para simplificar". Este modulo e a resposta: tres niveis
ENCAIXADOS, cada um acrescentando UMA ideia ao anterior.

  BRONZE  a regra-base do CLAUDE.md, sem nenhum filtro extra.
  PRATA   Bronze - exaustao + retracao de pelo menos 2 candles.
  OURO    Prata com o candle de continuacao na geometria certa.

O que cada filtro e, e por que ele esta aqui, esta em RESULTADOS.md; o
resumo e este:

VETO DE EXAUSTAO  -- descarta (Hull acelerando) E (preco esticado da EMA).
    O CLAUDE.md ja desconfiava disso ao escrever que "quando a HULL se
    encontra perto da banda superior, indica exaustao". A medicao mostra
    que a banda em si nao separa nada, mas a COMBINACAO separa muito: a
    Hull abrindo a curva PARA CIMA numa compra (a tal concavidade) so e
    ruim quando o preco ja esta longe da EMA. Sozinha, cada metade nao
    diz quase nada; juntas marcam 272 dos 655 sinais com EV de -1,5 ponto.

RETRACAO DE 2 OU MAIS CANDLES -- um candle so de retracao nao e retracao,
    e ruido. Com 2+ o EV sobe de 10 para 34 pontos, e e o filtro que mais
    ESTABILIZA o resultado ao longo do periodo.

GEOMETRIA DO CANDLE (o pavio) -- no grafico PI o corpo e sempre 100
    pontos, entao o range do candle E o tamanho do pavio. Tanto o candle
    sem pavio nenhum (< 25 pontos) quanto o de pavio enorme (> 90) medem
    mal; a faixa do meio mede bem. O primeiro e fino demais para pagar,
    o segundo e briga, nao continuacao.

NAO entram como filtro, porque foram medidos e nao pagam: a inclinacao da
EMA 21, a distancia da Hull a banda de Keltner isolada, o horario, e a
concavidade da Hull tomada sozinha (essa, sozinha, mede ao CONTRARIO do
esperado -- ver RESULTADOS.md).
"""
import numpy as np

# ------------------------------------------------------------------ cortes
ESTIC_EXAUSTAO = 0.45    # ATRs de distancia do fechamento a EMA 21
N_RET_MIN = 2            # candles de retracao exigidos
PAVIO_MIN = 25.0         # pontos de pavio total no candle de continuacao
PAVIO_MAX = 90.0

NIVEIS = ('ouro', 'prata', 'bronze')   # do mais exigente ao menos
ROTULO = {'ouro': 'Ouro', 'prata': 'Prata', 'bronze': 'Bronze'}


def anota(t):
    """Anexa as colunas derivadas e a classificacao Ouro/Prata/Bronze.

    `t` e a tabela devolvida por engine.executa(). Trabalha em copia.

    `pav_tot` e o pavio total do candle de continuacao. Como no grafico PI
    o corpo vale sempre 100 pontos, pav_tot = range - 100 e a unica
    informacao de forma que o candle carrega. No conjunto ANTECIPADO esse
    candle ainda nao existe na hora da decisao: pav_tot vem NaN, o filtro
    de geometria nao pode ser aplicado e o nivel Ouro fica indisponivel --
    o teto e o Prata.
    """
    t = t.copy()
    t['pav_tot'] = t['pav_fav'] + t['pav_con']

    exaustao = (t['curva'] > 0) & (t['estic'] > ESTIC_EXAUSTAO)
    ret_ok = t['n_ret'] >= N_RET_MIN
    geom_ok = t['pav_tot'].between(PAVIO_MIN, PAVIO_MAX)

    t['exaustao'] = exaustao
    t['ret_ok'] = ret_ok
    t['geom_ok'] = geom_ok
    t['e_prata'] = (~exaustao) & ret_ok
    t['e_ouro'] = t['e_prata'] & geom_ok

    t['nivel'] = np.where(t['e_ouro'], 'ouro',
                          np.where(t['e_prata'], 'prata', 'bronze'))
    return t


def seleciona(t, nivel):
    """Recorta a tabela no nivel pedido. Os niveis sao ENCAIXADOS:
    'bronze' devolve tudo, 'prata' devolve Prata+Ouro, 'ouro' so o Ouro."""
    if nivel == 'bronze':
        return t
    if nivel == 'prata':
        return t[t['e_prata']]
    if nivel == 'ouro':
        return t[t['e_ouro']]
    raise ValueError(nivel)


def descricao():
    """Texto curto de cada nivel, para o relatorio e o plano."""
    return {
        'bronze': ('Regra-base: retracao + candle de continuacao, os dois '
                   'extremos fora da Hull, Hull no sentido do trade e EMA 21 '
                   'atravessando o par. Sem nenhum filtro extra.'),
        'prata': ('Bronze mais duas exigencias: a retracao tem 2 ou mais '
                  'candles, e o sinal NAO esta em exaustao (Hull abrindo a '
                  f"curva a favor com o preco a mais de "
                  f"{('%.2f' % ESTIC_EXAUSTAO).replace('.', ',')} ATR da EMA 21)."),
        'ouro': ('Prata com o candle de continuacao na forma certa: pavio '
                 f'total entre {PAVIO_MIN:.0f} e {PAVIO_MAX:.0f} pontos. '
                 'Nem o candle liso demais, nem o candle de briga.'),
    }
