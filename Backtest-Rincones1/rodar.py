# -*- coding: utf-8 -*-
"""
Roda o backtest Rincones1 e grava saida/.

    python rodar.py

Gera:
    saida/resumo.json   TUDO que o relatorio precisa -- e a unica fonte
                        de numeros. relatorio.py le daqui, entao numero
                        no relatorio nunca fica defasado.
    saida/trades_*.csv  operacao a operacao, da configuracao padrao
    saida/console.txt   o mesmo que sai na tela

Depois rode `python relatorio.py` para regerar o relatorio.html.
"""
import contextlib
import io
import json
import os

import numpy as np
import pandas as pd

import engine as E

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
BASES = ('WINV26', 'WINFUT')
REGIMES = ('ema3', 'kama', 'hma', 't3', 'jma')
STOPS = (150, 100)

ROT_SETUP = {'A': 'tendencia (pullback na media)',
             'B': 'reversao rapida no afastamento',
             'C': 'reversao em consolidacao'}

# o eixo [E2] antigo e o novo, para a comparacao da secao "o eixo [E2]"
METRICAS_E2 = (0, 2)
ROT_E2 = {0: 'v1 · |delta| / |Close-Open|',
          1: 'v1 · esforço / range',
          2: 'v2 · (|delta|/esforço) × volta',
          3: 'v2 · |delta| × volta',
          4: 'volta pura'}

_CACHE = {}


def _ind(nome):
    # a chave inclui METRICA_E2: o indicador MUDA com ela
    chave = (nome, E.METRICA_E2)
    if chave not in _CACHE:
        _CACHE[chave] = E.indicador(E.carrega(E.ARQUIVOS[nome]))
    return _CACHE[chave]


def comparativo_e2():
    """O eixo [E2] antigo contra o novo, com TODO o resto congelado.

    Mesma media (ema3), mesmos setups, mesma gestao, mesma janela: a
    unica coisa que muda e a formula que alimenta pD. E a medicao que
    responde "trocar o indicador melhorou o backtest?".

    Mede tambem se o filtro DESCARTA_E2 -- que joga fora o sinal quando
    [E2] e o maior dos tres eixos -- continua valendo com a formula
    nova. Ele existia porque a formula antiga media negativo quando
    mandava; nao era obvio que sobreviveria a troca.
    """
    E.aplica_ma('ema3')
    met0, desc0, stop0 = E.METRICA_E2, E.DESCARTA_E2, E.STOP
    out = {'rotulos': {str(k): ROT_E2[k] for k in METRICAS_E2},
           'metricas': [str(m) for m in METRICAS_E2],
           'atual': str(met0), 'grid': {}, 'filtro': {}}
    for base in BASES:
        bruto = E.carrega(E.ARQUIVOS[base])
        out['grid'][base], out['filtro'][base] = {}, {}
        for met in METRICAS_E2:
            E.METRICA_E2 = met
            d = E.contexto(E.indicador(bruto), 'ema3')

            E.DESCARTA_E2 = True
            sig = E.gatilho(d)
            g = {'gatilhos': int((sig != 0).sum())}
            mk3 = E.setups(d, sig, ativos=('A', 'B', 'C'))
            for stop in STOPS:
                E.STOP = float(stop)
                g[str(stop)] = {}
                for rot, ativos in (('cA', ('A',)), ('cAB', ('A', 'B'))):
                    mk = E.setups(d, sig, ativos=ativos)
                    g[str(stop)][rot] = E.metricas(E.roda(d, mk, sig, carteira=True))
                # os setups ISOLADOS: e neles que da para ver ONDE a formula
                # nova muda alguma coisa -- ela mede exaustao, e exaustao e o
                # que o setup de reversao procura.
                for su in ('A', 'B'):
                    g[str(stop)]['setup_' + su] = E.metricas(
                        E.roda(d, mk3, sig, carteira=False, setup=su))
            out['grid'][base][str(met)] = g

            E.DESCARTA_E2 = False
            sig2 = E.gatilho(d)
            E.STOP = float(STOPS[0])
            mk2 = E.setups(d, sig2, ativos=('A', 'B'))
            out['filtro'][base][str(met)] = {
                'com': g[str(STOPS[0])]['cAB'],
                'sem': E.metricas(E.roda(d, mk2, sig2, carteira=True)),
                'gatilhos_com': g['gatilhos'],
                'gatilhos_sem': int((sig2 != 0).sum())}
            E.DESCARTA_E2 = True
    E.METRICA_E2, E.DESCARTA_E2, E.STOP = met0, desc0, stop0
    return out


def comparativo_leque():
    """A VARIANTE DO LEQUE: so vale o gatilho que TOCA ou fica ATRAS das medias.

    O gatilho de esforco nao olha onde o preco esta -- ele so mede que
    alguem agrediu e falhou. A restricao aqui diz ONDE isso conta: a barra
    tem de estar encostada no leque ou do lado de TRAS dele. O gatilho que
    dispara com o preco esticado NA FRENTE do leque, fora da tolerancia do
    toque, e descartado.

    O setup A nao muda -- ele ja exige o toque, entao ja esta inteiro
    dentro da restricao. Quem sente e o B, que e por construcao um setup
    de afastamento: sobra dele so a parte que se afastou para TRAS, ou que
    ainda encosta em alguma das tres.

    Mede tambem a distribuicao das posicoes (toca / atras / na frente),
    porque sem ela nao da para saber se a restricao corta pouco ou corta
    quase tudo, e o efeito nos cinco regimes de media -- 'leque' e um
    conceito das TRES EMAs, e com media unica ele degenera.
    """
    fl0, stop0 = E.FILTRO_LEQUE, E.STOP
    out = {'rotulos': {'livre': 'sem restrição — qualquer posição em relação às médias',
                       'leque': 'só gatilho que toca ou fica atrás do leque'},
           'ordem': ['livre', 'leque'],
           'atual': 'leque' if fl0 else 'livre',
           'decomp_rot': {'toca': 'só o toque no leque',
                          'atras': 'só o que fica atrás do leque',
                          'leque': 'os dois — a variante'},
           'decomp_ordem': ['toca', 'atras', 'leque'],
           'posicao': {}, 'grid': {}, 'decomp': {}, 'regimes': {}}

    for base in BASES:
        E.aplica_ma('ema3')
        d = E.contexto(_ind(base), 'ema3')

        # --- onde as barras (e os gatilhos) ficam em relacao ao leque
        E.FILTRO_LEQUE = False
        sig_livre = E.gatilho(d)
        ok = ~np.isnan(d.mrng.to_numpy())
        g = sig_livre != 0
        pos = {}
        for rot, col in (('toca', 'toca_leque'), ('atras', 'atras_leque'),
                         ('frente', 'frente_leque')):
            m = d[col].to_numpy(bool)
            pos[rot] = {'barras': round(100 * float(m[ok].mean()), 1),
                        'gatilhos': round(100 * float(m[g].mean()), 1),
                        'n': int(m[g].sum())}
        out['posicao'][base] = pos

        out['grid'][base] = {}
        for chave in out['ordem']:
            E.FILTRO_LEQUE = (chave == 'leque')
            sig = E.gatilho(d)
            mk3 = E.setups(d, sig, ativos=('A', 'B', 'C'))
            r = {'gatilhos': int((sig != 0).sum())}
            for stop in STOPS:
                E.STOP = float(stop)
                r[str(stop)] = {}
                for rot, ativos in (('cA', ('A',)), ('cAB', ('A', 'B'))):
                    mk = E.setups(d, sig, ativos=ativos)
                    r[str(stop)][rot] = E.metricas(E.roda(d, mk, sig, carteira=True))
                for su in ('A', 'B', 'C'):
                    r[str(stop)]['setup_' + su] = E.metricas(
                        E.roda(d, mk3, sig, carteira=False, setup=su))
                    r[str(stop)]['sinais_' + su] = int((mk3 == su).sum())
            out['grid'][base][chave] = r

        # --- as DUAS METADES da restricao, separadas. A tabela de posicoes
        #     mostra que "atras e fora da tolerancia" e um punhado de barras;
        #     esta e a medicao de se esse punhado paga o proprio lugar.
        out['decomp'][base] = {}
        for chave in out['decomp_ordem']:
            E.FILTRO_LEQUE = True if chave == 'leque' else chave
            sig = E.gatilho(d)
            mk = E.setups(d, sig, ativos=('A', 'B'))
            g = {'gatilhos': int((sig != 0).sum())}
            for stop in STOPS:
                E.STOP = float(stop)
                g[str(stop)] = E.metricas(E.roda(d, mk, sig, carteira=True))
            out['decomp'][base][chave] = g

        # --- a restricao nos cinco regimes de media
        E.STOP = float(STOPS[0])
        out['regimes'][base] = {}
        for regime in REGIMES:
            E.aplica_ma(regime)
            dr = E.contexto(_ind(base), regime)
            okr = ~np.isnan(dr.mrng.to_numpy())
            g_reg = {'toca': round(100 * float(dr.toca.to_numpy()[okr].mean()), 1)}
            for chave in out['ordem']:
                E.FILTRO_LEQUE = (chave == 'leque')
                sig = E.gatilho(dr)
                mk = E.setups(dr, sig, ativos=('A', 'B'))
                g_reg[chave] = E.metricas(E.roda(dr, mk, sig, carteira=True))
                g_reg['gatilhos_' + chave] = int((sig != 0).sum())
            out['regimes'][base][regime] = g_reg
        E.aplica_ma('ema3')

    E.FILTRO_LEQUE, E.STOP = fl0, stop0
    return out


def comparativo_gestao():
    """As regras possiveis para a parcial e para o stop depois dela.

    O backtest antigo punha o stop do restante na ENTRADA e tirava a
    parcial em +100 com stop de 150. Isso e otimista de um jeito que nao
    aparece no nome: o desfecho chamado "zero a zero" pagava +50 pontos.

    A regra certa -- a que o Carlos opera -- e a parcial na MESMA
    distancia do stop e o stop do restante na MEDIA DA OPERACAO, que com
    meia posicao cai exatamente em cima do stop inicial. Ai "zero a zero"
    e zero de verdade, e o stop nunca precisa andar.

    As tres linhas medem: a regra certa, a regra certa com a parcial mais
    perto, e o modelo antigo.
    """
    E.aplica_ma('ema3')
    st0, pa0, ap0 = E.STOP, E.PARCIAL_EM, E.STOP_APOS_PARCIAL
    REGRAS = (
        ('media_stop', 'media', None,
         'parcial na distância do stop · stop na média da operação'),
        ('media_100', 'media', 100.0,
         'parcial em +100 · stop na média da operação'),
        ('entrada_100', 'entrada', 100.0,
         'parcial em +100 · stop na entrada (o modelo antigo)'),
    )
    out = {'rotulos': {k: rot for k, _, _, rot in REGRAS},
           'ordem': [k for k, _, _, _ in REGRAS],
           'atual': 'media_stop' if E.PARCIAL_EM is None else None,
           'grid': {}}
    for base in BASES:
        d = E.contexto(_ind(base), 'ema3')
        sig = E.gatilho(d)
        out['grid'][base] = {}
        for chave, apos, parc, _rot in REGRAS:
            E.STOP_APOS_PARCIAL, E.PARCIAL_EM = apos, parc
            g = {}
            for stop in STOPS:
                E.STOP = float(stop)
                g[str(stop)] = {}
                for rot, ativos in (('cA', ('A',)), ('cAB', ('A', 'B'))):
                    mk = E.setups(d, sig, ativos=ativos)
                    g[str(stop)][rot] = E.metricas(E.roda(d, mk, sig, carteira=True))
                g[str(stop)]['parcial'] = float(stop if parc is None else parc)
            out['grid'][base][chave] = g
    E.STOP, E.PARCIAL_EM, E.STOP_APOS_PARCIAL = st0, pa0, ap0
    return out


def cenario(nome, regime, stop):
    """Um (base, media, stop): os tres setups isolados e as carteiras."""
    E.aplica_ma(regime)
    E.STOP = float(stop)
    d = E.contexto(_ind(nome), regime)
    sig = E.gatilho(d)
    mk3 = E.setups(d, sig, ativos=('A', 'B', 'C'))

    r = {'tend': round(100 * float(d.tendencia.mean()), 1),
         'cons': round(100 * float(d.consolida.mean()), 1),
         'gatilhos': int((sig != 0).sum())}
    for su in ('A', 'B', 'C'):
        r['setup_' + su] = E.metricas(E.roda(d, mk3, sig, carteira=False, setup=su))
        # quantos sinais o setup deu, contra quantos viraram trade. A
        # diferenca sao os ABORTADOS pela regra da barra seguinte -- o
        # numero que o operador manual precisa esperar na tela.
        r['sinais_' + su] = int((mk3 == su).sum())
    for ativos, rot in ((('A',), 'cA'), (('A', 'B'), 'cAB'), (('A', 'B', 'C'), 'cABC')):
        mk = E.setups(d, sig, ativos=ativos)
        r[rot] = E.metricas(E.roda(d, mk, sig, carteira=True))
    return r, d, sig


def detalhe(nome, d, sig, stop):
    """Aprofundamento da configuracao padrao: entrada, grade, custo, mes."""
    E.STOP = float(stop)
    mk = E.setups(d, sig, ativos=('A', 'B'))
    r = {}

    for modo in ('meio', 'fecha'):
        r['entrada_' + modo] = E.metricas(E.roda(d, mk, sig, entrada=modo, carteira=True))

    # A REGRA DA BARRA SEGUINTE, lado a lado com a limitada valida ate o
    # fim do pregao. Nao e uma variante que se possa escolher no dia a dia:
    # e a medicao do que a regra custa. Ver ESTRATEGIA.md 5.
    mkA = E.setups(d, sig, ativos=('A',))
    for mf, rot in ((E.MAX_BARRAS_FILL, 'regra'), (99999, 'livre')):
        r['fill_%s_A' % rot] = E.metricas(
            E.roda(d, mkA, sig, carteira=True, max_fill=mf))
        r['fill_%s_AB' % rot] = E.metricas(
            E.roda(d, mk, sig, carteira=True, max_fill=mf))

    grade = {}
    st0, al0 = E.STOP, E.ALVO
    for st in (100, 150, 200):
        for al in (200, 300, 400, 500):
            E.STOP, E.ALVO = float(st), float(al)
            m = E.metricas(E.roda(d, mk, sig, carteira=True))
            grade['%d_%d' % (st, al)] = None if not m else round(m['ev'], 1)
    E.STOP, E.ALVO = st0, al0
    r['grade'] = grade

    c0 = E.CUSTO_PTS
    for c in (0, 5, 10, 20):
        E.CUSTO_PTS = float(c)
        r['custo_%d' % c] = E.metricas(E.roda(d, mk, sig, carteira=True))
    E.CUSTO_PTS = c0

    # o bloco do plano manual: a FORMA do desempenho, nao o desempenho
    r['psico'] = {}
    for stop in (100, 150):
        r['psico'][str(stop)] = {
            'A': psicologia(d, sig, stop, ('A',)),
            'AB': psicologia(d, sig, stop, ('A', 'B')),
            # a mesma coisa descontando 5 pontos por trade. E o numero
            # que vale para o plano: o de custo zero e piso otimista.
            'A_c5': psicologia(d, sig, stop, ('A',), custo=5.0),
        }

    r['janela'] = janela(d, sig)

    tr = E.roda(d, mk, sig, carteira=True)
    if len(tr):
        tt = tr.copy()
        tt['mes'] = pd.to_datetime(tt.dia).dt.to_period('M').astype(str)
        tt['per'] = _periodo(tt.dia)
        r['mes'] = [dict(mes=k, n=len(g), ev=round(g.pnl.mean(), 1),
                         total=round(float(g.pnl.sum())),
                         acerto=round(100 * float((g.pnl > 0).mean()), 1),
                         calib=int((g.per == 'dentro').sum()),
                         pregoes=int(g.dia.nunique()))
                    for k, g in tt.groupby('mes')]
        r['equity'] = [round(x) for x in tr.pnl.cumsum().tolist()]
        r['equity_setup'] = tr.setup.tolist()
    return r, tr



PERIODOS = ('antes', 'dentro', 'depois', 'fora')


def _periodo(dias):
    """'antes' / 'dentro' / 'depois' da JANELA_CALIBRACAO, por pregao."""
    ini, fim = (pd.Timestamp(x).date() for x in E.JANELA_CALIBRACAO)
    dias = pd.Series(list(dias))
    return np.where(dias < ini, 'antes', np.where(dias > fim, 'depois', 'dentro'))


def janela(d, sig):
    """O TESTE FORA DA AMOSTRA: a mesma configuracao, cortada pela janela em
    que os parametros foram escolhidos.

    Os trades sao simulados na base inteira e so depois separados pelo
    pregao do sinal -- nenhum trade atravessa pregao, entao o corte nao
    muda trade nenhum. 'fora' = 'antes' + 'depois'.
    """
    st0, c0 = E.STOP, E.CUSTO_PTS
    dias = d.dia.to_numpy()
    per = _periodo(dias)
    out = {'janela': list(E.JANELA_CALIBRACAO), 'ordem': list(PERIODOS),
           'pregoes': {p: int(len(set(dias[per == p] if p != 'fora'
                                       else dias[per != 'dentro'])))
                       for p in PERIODOS}}
    mk3 = E.setups(d, sig, ativos=('A', 'B', 'C'))
    mkA = E.setups(d, sig, ativos=('A',))
    mkAB = E.setups(d, sig, ativos=('A', 'B'))
    for stop in STOPS:
        E.STOP = float(stop)
        g = {}
        for rot, custo, kw in (
                ('cA', 0.0, dict(marca=mkA, carteira=True)),
                ('cAB', 0.0, dict(marca=mkAB, carteira=True)),
                ('cA_c5', 5.0, dict(marca=mkA, carteira=True)),
                ('cAB_c5', 5.0, dict(marca=mkAB, carteira=True)),
                ('setup_A', 0.0, dict(marca=mk3, carteira=False, setup='A')),
                ('setup_B', 0.0, dict(marca=mk3, carteira=False, setup='B'))):
            E.CUSTO_PTS = custo
            tr = E.roda(d, kw['marca'], sig, carteira=kw['carteira'],
                        setup=kw.get('setup'))
            p = _periodo(tr.dia) if len(tr) else np.array([])
            g[rot] = {q: E.metricas(tr[(p != 'dentro') if q == 'fora' else (p == q)]
                                    if len(tr) else None)
                      for q in PERIODOS}
        out[str(stop)] = g
    E.STOP, E.CUSTO_PTS = st0, c0
    return out


def psicologia(d, sig, stop, ativos=('A',), custo=0.0):
    """O que o operador MANUAL precisa saber e o relatorio nao media.

    Nao e desempenho: e a FORMA do desempenho. Quantos pregoes negativos
    esperar, qual a maior sequencia ruim que ja aconteceu, e qual a chance
    de uma semana fechar no vermelho mesmo com a vantagem intacta. Sem
    isso o operador confunde variancia normal com estrategia quebrada.
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

    # chance de uma semana (5 pregoes) fechar negativa, reamostrando os
    # pregoes medidos com reposicao. Nao e previsao -- e a forma do ruido.
    rng = np.random.default_rng(20260830)
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
        ev=round(float(tr.pnl.mean()), 1),
        sd_trade=round(float(tr.pnl.std()), 1),
        media_dia=round(float(g.mean()), 1),
        sd_dia=round(float(g.std()), 1),
        dias_pos=round(100 * float((g > 0).mean()), 0),
        pior_dia=round(float(g.min())), melhor_dia=round(float(g.max())),
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
                        - tr.pnl.cumsum().to_numpy()).max())),
    )


def _l(rot, m, larg=30):
    if not m:
        return '  %-*s  sem trades' % (larg, rot)
    return ('  %-*s %4d %5.1f %+8.1f %+9.0f %5.1f%% %+6.2f %4.0f%% %5.2f %6.0f'
            % (larg, rot, m['n'], m['por_pregao'], m['ev'], m['total'],
               m['acerto'], m['t'], m['dias_pos'], m['pf'], m['dd']))


def _cab(larg=30):
    return ('  %-*s %4s %5s %8s %9s %6s %6s %5s %5s %6s'
            % (larg, '', 'n', '/preg', 'EV', 'total', 'acerto', 't',
               'dias+', 'PF', 'DD'))


def principal():
    resumo = {'parametros': {k: getattr(E, k) for k in (
        'PARCIAL_EM', 'STOP_APOS_PARCIAL', 'FRAC_PARCIAL', 'ALVO', 'CUSTO_PTS',
        'NIVEL_MIN',
        'CORTE_POSICAO', 'CORPO_MAX', 'DESCARTA_E2', 'FILTRO_LEQUE', 'PERIODO_REF',
        'EMA_R', 'EMA_M', 'EMA_L', 'PERIODO_RANGE', 'LEQUE_MIN', 'TOL_TOQUE',
        'CONSOL_MAX', 'AFAST_MIN_B', 'AFAST_MIN_C', 'VEL_MIN_B', 'ENTRADA',
        'MA_SLOPE', 'MAX_BARRAS_FILL', 'METRICA_E2')},
        'params_ma': E.PARAMS_MA, 'regimes': list(REGIMES), 'stops': list(STOPS),
        'variantes': {}, 'bases': {}}

    print('=' * 104)
    print('BACKTEST RINCONES1  -  WIN, barras de 10.000 ticks')
    print('gestao: parcial %.0f%% %s | stop apos a parcial: %s | alvo %.0f | stop: %s'
          % (100 * E.FRAC_PARCIAL,
             ('na distancia do stop' if E.PARCIAL_EM is None
              else 'em +%.0f' % E.PARCIAL_EM),
             E.STOP_APOS_PARCIAL, E.ALVO, ' e '.join(str(s) for s in STOPS)))
    print('entrada: ordem limitada no meio do candle, valida por %d barra(s) '
          '| custo: %.1f pts' % (E.MAX_BARRAS_FILL, E.CUSTO_PTS))
    print('=' * 104)

    resumo['gestao'] = comparativo_gestao()
    print('')
    print('  A REGRA DA PARCIAL  (ema3, carteira A + B)')
    for base in BASES:
        for chave in resumo['gestao']['ordem']:
            g = resumo['gestao']['grid'][base][chave]
            print('    %-7s %-52s | %s'
                  % (base, resumo['gestao']['rotulos'][chave],
                     ' | '.join('stop %d: EV %+6.1f t%+5.2f'
                                % (st, g[str(st)]['cAB']['ev'], g[str(st)]['cAB']['t'])
                                for st in STOPS)))

    resumo['leque'] = comparativo_leque()
    print('')
    print('  A VARIANTE DO LEQUE: so gatilho que TOCA ou fica ATRAS das medias')
    for base in BASES:
        p = resumo['leque']['posicao'][base]
        print('    %-7s posicao dos gatilhos: toca %4.1f%% · atras %4.1f%% · '
              'na frente %4.1f%%'
              % (base, p['toca']['gatilhos'], p['atras']['gatilhos'],
                 p['frente']['gatilhos']))
        for chave in resumo['leque']['ordem']:
            g = resumo['leque']['grid'][base][chave]
            print('    %-7s %-46s gatilhos=%4d | %s'
                  % (base, resumo['leque']['rotulos'][chave], g['gatilhos'],
                     ' | '.join('stop %d: EV %+6.1f t%+5.2f n=%3d DD %4.0f'
                                % (st, g[str(st)]['cAB']['ev'], g[str(st)]['cAB']['t'],
                                   g[str(st)]['cAB']['n'], g[str(st)]['cAB']['dd'])
                                for st in STOPS)))
        b = resumo['leque']['grid'][base]
        print('    %-7s setup B isolado (stop %d): livre %s -> leque %s'
              % (base, STOPS[0],
                 'n=%3d EV %+6.1f t%+5.2f' % (b['livre'][str(STOPS[0])]['setup_B']['n'],
                                              b['livre'][str(STOPS[0])]['setup_B']['ev'],
                                              b['livre'][str(STOPS[0])]['setup_B']['t']),
                 'n=%3d EV %+6.1f t%+5.2f' % (b['leque'][str(STOPS[0])]['setup_B']['n'],
                                              b['leque'][str(STOPS[0])]['setup_B']['ev'],
                                              b['leque'][str(STOPS[0])]['setup_B']['t'])))
        for chave in resumo['leque']['decomp_ordem']:
            g = resumo['leque']['decomp'][base][chave]
            print('    %-7s %-32s gatilhos=%4d | %s'
                  % (base, resumo['leque']['decomp_rot'][chave], g['gatilhos'],
                     ' | '.join('stop %d: EV %+6.1f t%+5.2f n=%3d'
                                % (st, g[str(st)]['ev'], g[str(st)]['t'],
                                   g[str(st)]['n']) for st in STOPS)))
        for regime in REGIMES:
            rg = resumo['leque']['regimes'][base][regime]
            fm = lambda m: ('sem trades' if not m else
                            'n=%3d EV %+6.1f t%+5.2f' % (m['n'], m['ev'], m['t']))
            print('      %-5s toca %4.1f%% das barras | livre %-24s | leque %-24s'
                  % (regime, rg['toca'], fm(rg['livre']), fm(rg['leque'])))

    resumo['e2'] = comparativo_e2()
    print('')
    print('  O EIXO [E2]: FORMULA ANTIGA x NOVA  (ema3, carteira A + B)')
    for base in BASES:
        for met in METRICAS_E2:
            g = resumo['e2']['grid'][base][str(met)]
            print('    %-7s %-32s gatilhos=%5d | %s'
                  % (base, ROT_E2[met], g['gatilhos'],
                     ' | '.join('stop %d: %s' % (st, (
                         'EV %+6.1f t%+5.2f n=%3d' % (g[str(st)]['cAB']['ev'],
                                                      g[str(st)]['cAB']['t'],
                                                      g[str(st)]['cAB']['n'])
                         if g[str(st)]['cAB'] else 'sem trades'))
                         for st in STOPS)))

    for base in BASES:
        resumo['variantes'][base] = {}
        print('\n' + '#' * 104)
        print('# %s' % base)
        print('#' * 104)

        for regime in REGIMES:
            resumo['variantes'][base][regime] = {}
            for stop in STOPS:
                r, d, sig = cenario(base, regime, stop)
                resumo['variantes'][base][regime][str(stop)] = r
                if regime == 'ema3' and stop == STOPS[0]:
                    d_pad, sig_pad = d, sig

        # --- tabela de variantes na tela
        for stop in STOPS:
            print('\n  MEDIA DE REGIME x DESEMPENHO  (stop %d)' % stop)
            print('    %-6s %6s | %-21s %-21s' %
                  ('media', '%tend', 'setup A isolado', 'carteira so A'))
            for regime in REGIMES:
                v = resumo['variantes'][base][regime][str(stop)]
                a, ca = v['setup_A'], v['cA']
                f = lambda m: ('n=%-4d %+6.1f t%+5.2f' % (m['n'], m['ev'], m['t'])
                               if m else 'sem trades')
                print('    %-6s %5.0f%% | %-21s %-21s'
                      % (regime, v['tend'], f(a), f(ca)))

        # --- detalhe da configuracao padrao
        E.aplica_ma('ema3')
        det, tr_out = detalhe(base, d_pad, sig_pad, STOPS[0])
        v_pad = resumo['variantes'][base]['ema3']
        det['gatilhos'] = v_pad[str(STOPS[0])]['gatilhos']
        det['barras'] = int(len(d_pad))
        det['pregoes'] = int(d_pad.dia.nunique())
        det['ini'] = str(d_pad.Data.min().date())
        det['fim'] = str(d_pad.Data.max().date())
        resumo['bases'][base] = det

        print('\n  CONFIGURACAO PADRAO (ema3, stop %d) -- carteira A + B' % STOPS[0])
        print(_cab())
        for stop in STOPS:
            for rot, ch in (('so A', 'cA'), ('A + B', 'cAB'), ('A + B + C', 'cABC')):
                print(_l('stop %d · %s' % (stop, rot),
                         resumo['variantes'][base]['ema3'][str(stop)][ch]))
        print('\n  entrada limitada x a mercado (stop %d)' % STOPS[0])
        print(_l('limitada no meio do candle', det['entrada_meio']))
        print(_l('a mercado no fechamento', det['entrada_fecha']))
        print('\n  custo por trade (stop %d)' % STOPS[0])
        for c in (0, 5, 10, 20):
            print(_l('custo de %d pts' % c, det['custo_%d' % c]))

        jn = det['janela']
        print('\n  FORA DA AMOSTRA -- janela de calibracao %s a %s  (pregoes: %s)'
              % (jn['janela'][0], jn['janela'][1],
                 ' · '.join('%s %d' % (p, jn['pregoes'][p]) for p in PERIODOS)))
        print(_cab(34))
        for stop in STOPS:
            for rot, ch in (('so A', 'cA'), ('A + B', 'cAB'),
                            ('so A, custo 5', 'cA_c5'), ('setup B isolado', 'setup_B')):
                for p in PERIODOS:
                    print(_l('stop %d · %s · %s' % (stop, rot, p), jn[str(stop)][ch][p], 34))

        if len(tr_out):
            tt = tr_out.copy()
            tt['data'] = d_pad.Data.to_numpy()[tt.i.to_numpy()]
            tt['lado'] = np.where(tt.s == 1, 'compra', 'venda')
            tt['pnl_rs'] = tt.pnl * E.VAL_PONTO
            tt[['data', 'dia', 'setup', 'lado', 'ent', 'res', 'pnl',
                'pnl_rs', 'barras']].to_csv(
                os.path.join(SAIDA, 'trades_%s.csv' % base),
                index=False, sep=';', decimal=',')

    print('\n' + '=' * 104)
    print('Rode `python relatorio.py` para regerar o relatorio.html a partir '
          'destes numeros.')
    print('=' * 104)
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
