# -*- coding: utf-8 -*-
"""
Roda o backtest Rincones1 XAUUSD e grava saida/.

    python rodar.py

Gera:
    saida/resumo.json   TUDO que o relatorio precisa -- e a unica fonte de
                        numeros. relatorio.py, resultados_md.py e plano.py
                        leem daqui, entao numero em documento nunca fica
                        defasado.
    saida/trades_*.csv  operacao a operacao, da configuracao padrao
    saida/console.txt   o mesmo que sai na tela

Depois rode `python relatorio.py` e `python plano.py`.
"""
import contextlib
import io
import json
import os
import warnings

import numpy as np
import pandas as pd

import engine as E

warnings.filterwarnings('ignore', category=RuntimeWarning)

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
BASES = E.BASES
REGIMES = ('ema3', 'kama', 'hma', 't3', 'jma')
STOPS = (7.0, 3.5)     # o medido e o equivalente escalado do WIN [X5]

ROT_BASE = {'COMPLETO': 'amostra inteira',
            'METADE_1': '1ª metade',
            'METADE_2': '2ª metade'}
ROT_SETUP = {'A': 'tendência (pullback na média)',
             'B': 'reversão rápida no afastamento',
             'C': 'reversão em consolidação',
             'L': 'livre (nenhum regime reivindicou)'}

METRICAS_E2 = (0, 2)
ROT_E2 = {0: 'v1 · |delta| / |Close-Open|',
          1: 'v1 · esforço / range',
          2: 'v2 · (|delta|/esforço) × volta',
          3: 'v2 · |delta| × volta',
          4: 'volta pura'}

GEOMETRIAS = ('off', 'corpo', 'classica', 'inversa')
ROT_GEO = {'off': 'sem filtro de forma',
           'corpo': 'só corpo pequeno',
           'classica': 'clássica (corpo do lado da rejeição) — a regra do WIN',
           'inversa': 'inversa (corpo do lado oposto)'}

# os conjuntos de eixos comparados na secao "de que eixo e o indice"
CONJ_EIXOS = ((('E4',), 0.90),
              (('E2', 'E3', 'E4'), 0.80),
              (('E2', 'E4'), 0.85),
              (('E3', 'E4'), 0.85),
              (('E2', 'E3'), 0.80))

_CACHE = {}


def _ind(nome):
    """Indicador da base, com cache. A chave inclui tudo que MUDA o
    indicador -- sem isso as secoes que varrem eixos ou METRICA_E2
    devolveriam o indicador da secao anterior."""
    chave = (nome, E.METRICA_E2)
    if chave not in _CACHE:
        _CACHE[chave] = E.indicador(E.carrega(base=nome))
    return _CACHE[chave]


def _ctx(nome, regime='ema3'):
    # combina() aplica EIXOS sobre os percentis cacheados -- e barato, e e
    # por isso que o cache nao precisa de uma entrada por conjunto de eixos
    return E.contexto(E.combina(_ind(nome)), regime)


def _carteira(d, sig, stop, ativos=None, entrada=None, custo=None):
    """Uma carteira: uma posicao por vez, com os parametros pedidos."""
    st0, c0 = E.STOP, E.CUSTO_PTS
    E.STOP = float(stop)
    if custo is not None:
        E.CUSTO_PTS = float(custo)
    mk = E.setups(d, sig, ativos=ativos)
    m = E.metricas(E.roda(d, mk, sig, carteira=True,
                          entrada=(entrada or E.ENTRADA)))
    E.STOP, E.CUSTO_PTS = st0, c0
    return m


# ------------------------------------------------------------------ secoes
def comparativo_e2():
    """O eixo [E2] antigo contra o novo, com TODO o resto congelado.

    Aqui a comparacao so faz sentido num indice que USE [E2] -- e o padrao
    do ouro nao usa [X6]. Entao ela roda sobre o indice de tres eixos
    ([E2]+[E3]+[E4]), que e a configuracao mais proxima do backtest do WIN
    que este ativo aceita. E a pergunta continua sendo a mesma: trocar a
    formula do eixo melhora o backtest?
    """
    e0, n0, m0 = E.EIXOS, E.NIVEL_MIN, E.METRICA_E2
    E.EIXOS, E.NIVEL_MIN = ('E2', 'E3', 'E4'), 0.80
    out = {'rotulos': {str(k): ROT_E2[k] for k in METRICAS_E2},
           'metricas': [str(m) for m in METRICAS_E2],
           'atual': str(m0),
           'eixos': '+'.join(E.EIXOS), 'nivel': E.NIVEL_MIN, 'grid': {}}
    for base in BASES:
        out['grid'][base] = {}
        for met in METRICAS_E2:
            E.METRICA_E2 = met
            d = _ctx(base)
            sig = E.gatilho(d)
            g = {'gatilhos': int((sig != 0).sum())}
            for stop in STOPS:
                g[str(stop)] = _carteira(d, sig, stop)
            out['grid'][base][str(met)] = g
    E.EIXOS, E.NIVEL_MIN, E.METRICA_E2 = e0, n0, m0
    return out


def comparativo_geometria():
    """O filtro de FORMA da barra, nos quatro modos.

    E a secao mais importante do porte: a regra que o WIN usa (clássica)
    mede negativo aqui, e a inversa mede. Ver [X7].
    """
    g0 = E.GEOMETRIA
    out = {'rotulos': ROT_GEO, 'ordem': list(GEOMETRIAS),
           'atual': g0, 'pos': E.CORTE_POSICAO, 'grid': {}}
    for base in BASES:
        d = _ctx(base)
        out['grid'][base] = {}
        for geo in GEOMETRIAS:
            E.GEOMETRIA = geo
            sig = E.gatilho(d)
            g = {'gatilhos': int((sig != 0).sum())}
            for stop in STOPS:
                g[str(stop)] = _carteira(d, sig, stop)
            out['grid'][base][geo] = g
    E.GEOMETRIA = g0
    return out


def comparativo_referencia():
    """De quem e a direcao que se le: do delta ou do candle? [X2]"""
    r0 = E.REFERENCIA
    out = {'rotulos': {'candle': 'direção do próprio candle',
                       'delta': 'direção do delta (tick rule)'},
           'ordem': ['candle', 'delta'], 'atual': r0, 'grid': {}}
    for base in BASES:
        d = _ctx(base)
        out['grid'][base] = {}
        for ref in out['ordem']:
            E.REFERENCIA = ref
            sig = E.gatilho(d)
            g = {'gatilhos': int((sig != 0).sum())}
            for stop in STOPS:
                g[str(stop)] = _carteira(d, sig, stop)
            out['grid'][base][ref] = g
    E.REFERENCIA = r0
    return out


def comparativo_eixos():
    """De que eixos e o indice. [E1] nao aparece: o ativo nao o publica."""
    e0, n0 = E.EIXOS, E.NIVEL_MIN
    out = {'ordem': ['+'.join(c) for c, _ in CONJ_EIXOS],
           'niveis': {'+'.join(c): n for c, n in CONJ_EIXOS},
           'atual': '+'.join(e0), 'grid': {}, 'degenerados': {}}
    for base in BASES:
        out['grid'][base] = {}
        for conj, niv in CONJ_EIXOS:
            E.EIXOS, E.NIVEL_MIN = conj, niv
            d = _ctx(base)
            sig = E.gatilho(d)
            g = {'gatilhos': int((sig != 0).sum()),
                 'vivos': list(d.attrs['eixos_vivos']),
                 'mortos': list(d.attrs['eixos_mortos'])}
            for stop in STOPS:
                g[str(stop)] = _carteira(d, sig, stop)
            out['grid'][base]['+'.join(conj)] = g
        # quais eixos o ativo publica, com os QUATRO ligados
        E.EIXOS, E.NIVEL_MIN = ('E1', 'E2', 'E3', 'E4'), 0.80
        d = _ctx(base)
        out['degenerados'][base] = {'vivos': list(d.attrs['eixos_vivos']),
                                    'mortos': list(d.attrs['eixos_mortos'])}
    E.EIXOS, E.NIVEL_MIN = e0, n0
    return out


def comparativo_entrada():
    """A mercado no fechamento contra a limitada no meio do candle. [X8]"""
    out = {'rotulos': {'fecha': 'a mercado no fechamento do candle',
                       'meio': 'limitada no meio do candle, válida por 1 barra'},
           'ordem': ['fecha', 'meio'], 'atual': E.ENTRADA, 'grid': {}}
    for base in BASES:
        d = _ctx(base)
        sig = E.gatilho(d)
        out['grid'][base] = {}
        for ent in out['ordem']:
            g = {}
            for stop in STOPS:
                g[str(stop)] = _carteira(d, sig, stop, entrada=ent)
            out['grid'][base][ent] = g
        # quantos sinais a limitada ABORTA por nao preencher em 1 barra
        st0 = E.STOP
        E.STOP = float(STOPS[0])
        mk = E.setups(d, sig)
        n_meio = len(E.roda(d, mk, sig, carteira=False, entrada='meio'))
        n_fecha = len(E.roda(d, mk, sig, carteira=False, entrada='fecha'))
        E.STOP = st0
        out['grid'][base]['abortos'] = {'sinais': n_fecha, 'preenchidos': n_meio}
    return out


def comparativo_gestao():
    """As regras possiveis para a parcial e para o stop depois dela.

    Mesma medicao do projeto do WIN: a regra certa (parcial na distancia do
    stop, stop do restante na media da operacao, "zero a zero" que e zero de
    verdade) contra o modelo antigo, que pagava meia parcial e ainda chamava
    o desfecho de zero.
    """
    pa0, ap0 = E.PARCIAL_EM, E.STOP_APOS_PARCIAL
    REGRAS = (
        ('media_stop', 'media', None,
         'parcial na distância do stop · stop na média da operação'),
        ('media_meio', 'media', 'meio',
         'parcial em metade do stop · stop na média da operação'),
        ('entrada_meio', 'entrada', 'meio',
         'parcial em metade do stop · stop na entrada (o modelo antigo)'),
    )
    out = {'rotulos': {k: rot for k, _, _, rot in REGRAS},
           'ordem': [k for k, _, _, _ in REGRAS],
           'atual': 'media_stop' if E.PARCIAL_EM is None else None, 'grid': {}}
    for base in BASES:
        d = _ctx(base)
        sig = E.gatilho(d)
        out['grid'][base] = {}
        for chave, apos, parc, _rot in REGRAS:
            E.STOP_APOS_PARCIAL = apos
            g = {}
            for stop in STOPS:
                # 'meio' quer dizer metade do stop DAQUELA coluna
                E.PARCIAL_EM = None if parc is None else float(stop) / 2.0
                g[str(stop)] = _carteira(d, sig, stop)
                g[str(stop) + '_parcial'] = float(stop if parc is None
                                                  else stop / 2.0)
            out['grid'][base][chave] = g
    E.PARCIAL_EM, E.STOP_APOS_PARCIAL = pa0, ap0
    return out


def estabilidade():
    """O corte do indice x o corte de posicao do corpo, nas duas metades.

    NIVEL_MIN = 0,90 e CORTE_POSICAO = 60 sairam de uma varredura. Publicar a
    varredura inteira e o unico jeito honesto de mostrar se o resultado e uma
    familia ou um pico isolado.
    """
    n0, p0 = E.NIVEL_MIN, E.CORTE_POSICAO
    niveis = (0.80, 0.85, 0.90, 0.95)
    poss = (50.0, 55.0, 60.0, 65.0, 70.0)
    out = {'niveis': list(niveis), 'pos': list(poss),
           'atual': [n0, p0], 'grid': {}}
    for base in BASES:
        d = _ctx(base)
        out['grid'][base] = {}
        for niv in niveis:
            for pos in poss:
                E.NIVEL_MIN, E.CORTE_POSICAO = niv, pos
                sig = E.gatilho(d)
                m = _carteira(d, sig, STOPS[0])
                out['grid'][base]['%.2f_%.0f' % (niv, pos)] = (
                    None if not m else {'n': m['n'], 'ev': round(m['ev'], 3),
                                        't': round(m['t'], 2)})
    E.NIVEL_MIN, E.CORTE_POSICAO = n0, p0
    return out


def cenario(nome, regime, stop):
    """Um (base, media, stop): os quatro setups isolados e as carteiras."""
    E.aplica_ma(regime)
    d = _ctx(nome, regime)
    sig = E.gatilho(d)
    mk4 = E.setups(d, sig, ativos=('A', 'B', 'C', 'L'))

    st0 = E.STOP
    E.STOP = float(stop)
    r = {'tend': round(100 * float(d.tendencia.mean()), 1),
         'cons': round(100 * float(d.consolida.mean()), 1),
         'gatilhos': int((sig != 0).sum())}
    for su in ('A', 'B', 'C', 'L'):
        r['setup_' + su] = E.metricas(E.roda(d, mk4, sig, carteira=False, setup=su))
        r['sinais_' + su] = int((mk4 == su).sum())
    for ativos, rot in ((('A',), 'cA'), (('A', 'B'), 'cAB'),
                        (('A', 'B', 'C'), 'cABC'),
                        (('A', 'B', 'C', 'L'), 'cTudo')):
        mk = E.setups(d, sig, ativos=ativos)
        r[rot] = E.metricas(E.roda(d, mk, sig, carteira=True))
    E.STOP = st0
    return r, d, sig


def detalhe(nome, d, sig, stop):
    """Aprofundamento da configuracao padrao: grade, custo, mes, equity."""
    st0, al0, c0 = E.STOP, E.ALVO, E.CUSTO_PTS
    E.STOP = float(stop)
    mk = E.setups(d, sig)
    r = {}

    grade = {}
    for st in (3.5, 5.0, 7.0, 9.0, 12.0):
        for al in (7.0, 10.5, 14.0, 21.0, 28.0):
            E.STOP, E.ALVO = float(st), float(al)
            m = E.metricas(E.roda(d, mk, sig, carteira=True))
            grade['%.1f_%.1f' % (st, al)] = None if not m else round(m['ev'], 3)
    E.STOP, E.ALVO = float(stop), al0
    r['grade'] = grade
    r['grade_stops'] = [3.5, 5.0, 7.0, 9.0, 12.0]
    r['grade_alvos'] = [7.0, 10.5, 14.0, 21.0, 28.0]

    for c in (0.0, 0.10, 0.20, 0.50):
        E.CUSTO_PTS = float(c)
        r['custo_%s' % ('%.2f' % c)] = E.metricas(E.roda(d, mk, sig, carteira=True))
    E.CUSTO_PTS = c0

    r['psico'] = {}
    for st in STOPS:
        r['psico'][str(st)] = {
            'tudo': psicologia(d, sig, st, ('A', 'B', 'C', 'L')),
            'A': psicologia(d, sig, st, ('A',)),
            # o mesmo descontando 0,20 USD por trade -- o spread tipico do
            # ouro. E o numero que vale para o plano; o de custo zero e piso
            # otimista.
            'tudo_c20': psicologia(d, sig, st, ('A', 'B', 'C', 'L'), custo=0.20),
        }

    tr = E.roda(d, mk, sig, carteira=True)
    if len(tr):
        tt = tr.copy()
        tt['mes'] = pd.to_datetime(tt.dia).dt.to_period('M').astype(str)
        r['mes'] = [dict(mes=k, n=len(g), ev=round(g.pnl.mean(), 3),
                         total=round(float(g.pnl.sum()), 1),
                         acerto=round(100 * float((g.pnl > 0).mean()), 1))
                    for k, g in tt.groupby('mes')]
        r['equity'] = [round(x, 2) for x in tr.pnl.cumsum().tolist()]
        r['equity_setup'] = tr.setup.tolist()
    E.STOP, E.ALVO, E.CUSTO_PTS = st0, al0, c0
    return r, tr


def psicologia(d, sig, stop, ativos=('A', 'B', 'C', 'L'), custo=0.0):
    """O que o operador MANUAL precisa saber e o relatorio nao media.

    Nao e desempenho: e a FORMA do desempenho. Quantos pregoes negativos
    esperar, qual a maior sequencia ruim que ja aconteceu, e qual a chance de
    uma semana fechar no vermelho mesmo com a vantagem intacta. Sem isso o
    operador confunde variancia normal com estrategia quebrada.
    """
    st0, c0 = E.STOP, E.CUSTO_PTS
    E.STOP, E.CUSTO_PTS = float(stop), float(custo)
    mk = E.setups(d, sig, ativos=ativos)
    tr = E.roda(d, mk, sig, carteira=True)
    E.STOP, E.CUSTO_PTS = st0, c0
    if not len(tr):
        return None

    g = tr.groupby('dia').pnl.sum()
    dia = g.to_numpy(float)

    def maior_seq(mask):
        b = c = 0
        for v in mask:
            c = c + 1 if v else 0
            b = max(b, c)
        return int(b)

    rng = np.random.default_rng(20260902)
    if len(dia) >= 3:
        am = rng.choice(dia, size=(20000, 5), replace=True).sum(axis=1)
        p_sem_neg = float((am < 0).mean())
        am4 = rng.choice(dia, size=(20000, 20), replace=True).sum(axis=1)
        p_mes_neg = float((am4 < 0).mean())
    else:
        p_sem_neg = p_mes_neg = None

    q = 1.0 - float((tr.pnl > 0).mean())
    return dict(
        custo=float(custo),
        n=int(len(tr)), pregoes=int(len(g)),
        por_pregao=round(len(tr) / len(g), 1),
        acerto=round(100 * float((tr.pnl > 0).mean()), 1),
        ev=round(float(tr.pnl.mean()), 3),
        sd_trade=round(float(tr.pnl.std()), 2),
        media_dia=round(float(g.mean()), 2),
        sd_dia=round(float(g.std()), 2),
        dias_pos=round(100 * float((g > 0).mean()), 0),
        pior_dia=round(float(g.min()), 1), melhor_dia=round(float(g.max()), 1),
        seq_trades=maior_seq(tr.pnl.to_numpy() <= 0),
        seq_dias=maior_seq(dia < 0),
        p_alvo=round(100 * float((tr.res == 'alvo').mean()), 1),
        p_stop=round(100 * float((tr.res == 'stop').mean()), 1),
        p_zero=round(100 * float((tr.res == 'zero').mean()), 1),
        p_fim=round(100 * float((tr.res == 'fim').mean()), 1),
        p3=round(100 * q ** 3, 1), p4=round(100 * q ** 4, 1), p5=round(100 * q ** 5, 1),
        p_semana_neg=None if p_sem_neg is None else round(100 * p_sem_neg),
        p_mes_neg=None if p_mes_neg is None else round(100 * p_mes_neg),
        dd=round(float((np.maximum.accumulate(tr.pnl.cumsum().to_numpy())
                        - tr.pnl.cumsum().to_numpy()).max()), 1),
    )


# ------------------------------------------------------------------- saida
def _l(rot, m, larg=32):
    if not m:
        return '  %-*s  sem trades' % (larg, rot)
    return ('  %-*s %4d %5.1f %+8.3f %+9.1f %5.1f%% %+6.2f %4.0f%% %5.2f %6.1f'
            % (larg, rot, m['n'], m['por_pregao'], m['ev'], m['total'],
               m['acerto'], m['t'], m['dias_pos'], m['pf'], m['dd']))


def _cab(larg=32):
    return ('  %-*s %4s %5s %8s %9s %6s %6s %5s %5s %6s'
            % (larg, '', 'n', '/preg', 'EV', 'total', 'acerto', 't',
               'dias+', 'PF', 'DD'))


def _resumo_linha(g, chave='7.0'):
    m = g[chave] if isinstance(g, dict) and chave in g else g
    return ('sem trades' if not m
            else 'n=%-4d EV %+6.3f t %+5.2f PF %4.2f' % (m['n'], m['ev'],
                                                         m['t'], m['pf']))


def principal():
    resumo = {'parametros': {k: getattr(E, k) for k in (
        'TICK', 'VAL_PONTO', 'STOP', 'ALVO', 'PARCIAL_EM', 'STOP_APOS_PARCIAL',
        'FRAC_PARCIAL', 'CUSTO_PTS', 'PERIODO_REF', 'METRICA_E2', 'EIXOS',
        'MIN_VARIACAO', 'NIVEL_MIN', 'REFERENCIA', 'GEOMETRIA', 'CORTE_POSICAO',
        'CORPO_MAX', 'DESCARTA_E2', 'EMA_R', 'EMA_M', 'EMA_L', 'PERIODO_RANGE',
        'LEQUE_MIN', 'TOL_TOQUE', 'CONSOL_MAX', 'AFAST_MIN_B', 'AFAST_MIN_C',
        'ENTRADA', 'MAX_BARRAS_FILL', 'MA_SLOPE', 'SETUPS_ATIVOS')},
        'params_ma': E.PARAMS_MA, 'regimes': list(REGIMES),
        'stops': list(STOPS), 'bases': {}, 'variantes': {},
        'rot_base': ROT_BASE, 'rot_setup': ROT_SETUP}

    print('=' * 110)
    print('BACKTEST RINCONES1 XAUUSD  -  ouro, barras de 521 ticks')
    print('gestao: parcial %.0f%% %s | stop apos a parcial: %s | alvo %.2f | stop: %s'
          % (100 * E.FRAC_PARCIAL,
             ('na distancia do stop' if E.PARCIAL_EM is None
              else 'em +%.2f' % E.PARCIAL_EM),
             E.STOP_APOS_PARCIAL, E.ALVO,
             ' e '.join('%.2f' % s for s in STOPS)))
    print('gatilho: indice [%s] >= %.2f | direcao do %s | geometria %s (pos %.0f) '
          '| corpo <= %.0f%%'
          % ('+'.join(E.EIXOS), E.NIVEL_MIN, E.REFERENCIA, E.GEOMETRIA,
             E.CORTE_POSICAO, E.CORPO_MAX))
    print('entrada: %s | custo: %.2f USD | 1 USD de movimento = %.0f USD por lote'
          % (E.ENTRADA, E.CUSTO_PTS, E.VAL_PONTO))
    print('=' * 110)

    for chave, fn, titulo in (
            ('eixos', comparativo_eixos, 'DE QUE EIXO E O INDICE'),
            ('referencia', comparativo_referencia,
             'A DIRECAO E DO CANDLE OU DO DELTA?'),
            ('geometria', comparativo_geometria, 'O FILTRO DE FORMA DA BARRA'),
            ('entrada', comparativo_entrada, 'A ENTRADA'),
            ('e2', comparativo_e2, 'O EIXO [E2]: FORMULA ANTIGA x NOVA'),
            ('gestao', comparativo_gestao, 'A REGRA DA PARCIAL')):
        resumo[chave] = fn()
        print('\n  %s  (carteira completa, stop %.2f)' % (titulo, STOPS[0]))
        R = resumo[chave]
        ordem = R.get('ordem') or R.get('metricas')
        for base in BASES:
            for k in ordem:
                g = R['grid'][base].get(k)
                if g is None:
                    continue
                rot = (R['rotulos'][k] if 'rotulos' in R
                       else '%s (nível %.2f)' % (k, R['niveis'][k]))
                print('    %-9s %-52s | %s'
                      % (base, rot[:52], _resumo_linha(g, str(STOPS[0]))))

    resumo['estabilidade'] = estabilidade()
    print('\n  ESTABILIDADE  nivel do indice x corte de posicao do corpo '
          '(stop %.2f, EV)' % STOPS[0])
    Rs = resumo['estabilidade']
    print('    %-9s %-6s %s' % ('base', 'nivel',
                                ' '.join('pos%2.0f' % p for p in Rs['pos'])))
    for base in BASES:
        for niv in Rs['niveis']:
            cel = []
            for pos in Rs['pos']:
                c = Rs['grid'][base]['%.2f_%.0f' % (niv, pos)]
                cel.append('%+6.2f' % c['ev'] if c else '     -')
            print('    %-9s %-6.2f %s' % (base, niv, ' '.join(cel)))

    for base in BASES:
        resumo['variantes'][base] = {}
        print('\n' + '#' * 110)
        print('# %s  (%s)' % (base, ROT_BASE[base]))
        print('#' * 110)

        d_pad = sig_pad = None
        for regime in REGIMES:
            resumo['variantes'][base][regime] = {}
            for stop in STOPS:
                r, d, sig = cenario(base, regime, stop)
                resumo['variantes'][base][regime][str(stop)] = r
                if regime == 'ema3' and stop == STOPS[0]:
                    d_pad, sig_pad = d, sig

        for stop in STOPS:
            print('\n  MEDIA DE REGIME x DESEMPENHO  (stop %.2f)' % stop)
            print('    %-6s %6s | %-24s %-24s' %
                  ('media', '%tend', 'setup A isolado', 'carteira A+B+C+L'))
            for regime in REGIMES:
                v = resumo['variantes'][base][regime][str(stop)]
                fmt = (lambda m: ('n=%-4d %+7.3f t%+5.2f' % (m['n'], m['ev'], m['t']))
                       if m else 'sem trades')
                print('    %-6s %5.0f%% | %-24s %-24s'
                      % (regime, v['tend'], fmt(v['setup_A']), fmt(v['cTudo'])))

        E.aplica_ma('ema3')
        det, tr_out = detalhe(base, d_pad, sig_pad, STOPS[0])
        v_pad = resumo['variantes'][base]['ema3']
        det['gatilhos'] = v_pad[str(STOPS[0])]['gatilhos']
        det['barras'] = int(len(d_pad))
        det['pregoes'] = int(d_pad.dia.nunique())
        det['ini'] = str(d_pad.Data.min().date())
        det['fim'] = str(d_pad.Data.max().date())
        det['eixos_vivos'] = list(d_pad.attrs['eixos_vivos'])
        det['eixos_mortos'] = list(d_pad.attrs['eixos_mortos'])
        resumo['bases'][base] = det

        print('\n  CONFIGURACAO PADRAO (ema3) -- por carteira')
        print(_cab())
        for stop in STOPS:
            for rot, ch in (('só A', 'cA'), ('A + B', 'cAB'),
                            ('A + B + C', 'cABC'), ('tudo (A+B+C+L)', 'cTudo')):
                print(_l('stop %.2f · %s' % (stop, rot),
                         resumo['variantes'][base]['ema3'][str(stop)][ch]))
        print('\n  SETUPS ISOLADOS (stop %.2f)' % STOPS[0])
        for su in ('A', 'B', 'C', 'L'):
            print(_l('%s · %s' % (su, ROT_SETUP[su]),
                     resumo['variantes'][base]['ema3'][str(STOPS[0])]['setup_' + su]))
        print('\n  CUSTO POR TRADE (stop %.2f, carteira completa)' % STOPS[0])
        for c in (0.0, 0.10, 0.20, 0.50):
            print(_l('custo de %.2f USD' % c, det['custo_%.2f' % c]))

        if len(tr_out):
            tt = tr_out.copy()
            tt['data'] = d_pad.Data.to_numpy()[tt.i.to_numpy()]
            tt['lado'] = np.where(tt.s == 1, 'compra', 'venda')
            tt['pnl_usd'] = tt.pnl * E.VAL_PONTO
            tt[['data', 'dia', 'setup', 'lado', 'ent', 'res', 'pnl',
                'pnl_usd', 'barras']].to_csv(
                os.path.join(SAIDA, 'trades_%s.csv' % base),
                index=False, sep=';', decimal=',')

    print('\n' + '=' * 110)
    print('Rode `python relatorio.py` e `python plano.py` para regerar os '
          'documentos a partir destes numeros.')
    print('=' * 110)
    return resumo


if __name__ == '__main__':
    os.makedirs(SAIDA, exist_ok=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        resumo = principal()
    texto = buf.getvalue()
    print(texto)
    with open(os.path.join(SAIDA, 'console.txt'), 'w', encoding='utf-8') as f:
        f.write(texto)
    with open(os.path.join(SAIDA, 'resumo.json'), 'w', encoding='utf-8') as f:
        json.dump(resumo, f, indent=1, default=str, ensure_ascii=False)
