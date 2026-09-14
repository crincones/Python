# -*- coding: utf-8 -*-
"""
Roda o backtest completo e grava saida/.

    python rodar.py

Gera:
    saida/resumo.json     TUDO que os relatorios precisam. E a unica fonte de
                          numeros: RESULTADOS.md, relatorio.html, PLANO.md e
                          plano.html leem daqui.
    saida/trades_*.csv    operacao a operacao, de cada variante
    saida/barras.json     OHLC + agressao comprimidos, para os graficos
    saida/console.txt     o mesmo que sai na tela

Depois rode `python resultados_md.py`, `python relatorio.py` e `python plano.py`.
"""
import contextlib
import io
import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

import engine as E

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
TICK = E.TICK
RNG = E.RANGE_NOMINAL          # 388 ticks: o range da barra

# a configuracao que o estudo termina recomendando
ESCOLHA = dict(ma_tipo='ema', modo='fixo', leque_min=400.0, stop_ticks=194.0)

CUSTOS = (0, 10, 20, 40)       # ticks de ida+volta testados na sensibilidade

# o grid publicado inteiro
GRID_MA = ('ema', 'hull')
GRID_LEQUE = (0.0, 200.0, 400.0, 600.0)
GRID_STOP = (145.0, 194.0, 291.0, 388.0, 450.0)


# --------------------------------------------------------------------------
# variantes publicadas
# --------------------------------------------------------------------------
def variantes():
    L = 400.0
    return [
        (E.Config(nome='V0', rotulo='só o gatilho, sem contexto de médias',
                  ma_tipo='ema', exige_leque=False, modo='fixo'),
         'O ponto de partida: o sinal do indicador operado a favor da barra, '
         'com stop de 194 ticks (meio range) e alvo de 388 (um range) — 1:2 '
         'fixo, sem nenhuma leitura de tendência. Serve de linha de base para '
         'medir o que as médias acrescentam.'),

        (E.Config(nome='V1', rotulo='EMA em leque ordenado', ma_tipo='ema',
                  modo='fixo'),
         'Acrescenta a primeira metade da ideia: só opera quando as três EMAs '
         '(21/42/72) estão ordenadas na mesma direção do sinal. O gatilho '
         'deixa de ser reversão e vira retomada de tendência.'),

        (E.Config(nome='V2', rotulo='EMA em leque aberto (≥400 t)',
                  ma_tipo='ema', modo='fixo', leque_min=L),
         'Acrescenta a segunda metade: o leque tem de estar ABERTO — a '
         'distância entre a EMA21 e a EMA72 de pelo menos 400 ticks (4 '
         'dólares). É a tradução numérica de "médias não emboladas". '
         'Gestão fixa 1:2. É a configuração recomendada.'),

        (E.Config(nome='V3', rotulo='EMA + parcial 50%, stop na entrada',
                  ma_tipo='ema', modo='parcial', leque_min=L),
         'A mesma seleção da V2 com a segunda gestão pedida: a +1R vende 50% '
         'e leva o stop para a entrada. Desfechos possíveis: −1R, +0,5R ou '
         '+1,5R. O número desta variante depende de uma convenção que o '
         'arquivo não resolve — ver §5.'),

        (E.Config(nome='V4', rotulo='EMA + parcial 50%, breakeven da operação',
                  ma_tipo='ema', modo='parcial_op', leque_min=L),
         'A leitura literal de "breakeven na média da operação": a +1R vende '
         '50% e o stop FICA ONDE ESTÁ — porque, com metade realizada em +1R, '
         'a operação inteira já empata exatamente no stop inicial. Desfechos: '
         '−1R, 0 ou +1,5R. Não depende de convenção nenhuma.'),

        (E.Config(nome='V5', rotulo='EMA + breakeven em 1R, sem parcial',
                  ma_tipo='ema', modo='breakeven', leque_min=L),
         'A terceira gestão pedida: a +1R o stop vai para a entrada, sem '
         'parcial. Desfechos: −1R, 0 ou +2R. É a que mede melhor de todas — e '
         'a que menos se pode acreditar, pelo motivo do §5.'),

        (E.Config(nome='V6', rotulo='Hull em leque ordenado', ma_tipo='hull',
                  modo='fixo'),
         'A V1 com médias de Hull no lugar das exponenciais, mesmos períodos. '
         'A Hull persegue o preço muito mais de perto: vira antes, e o leque '
         'dela abre e fecha muito mais vezes.'),

        (E.Config(nome='V7', rotulo='Hull em leque aberto (≥400 t)',
                  ma_tipo='hull', modo='fixo', leque_min=L),
         'A V2 com Hull. É a comparação direta que responde qual família de '
         'média serve melhor a esta estratégia.'),

        (E.Config(nome='V8', rotulo='Hull + breakeven em 1R', ma_tipo='hull',
                  modo='breakeven', leque_min=L),
         'A melhor gestão aplicada à Hull, para checar se a desvantagem da '
         'Hull vem do contexto ou da gestão.'),

        (E.Config(nome='V9', rotulo='EMA + esforço baixo', ma_tipo='ema',
                  modo='fixo', leque_min=L, esf_max=0.80),
         'A V2 mais o filtro que sobreviveu ao estudo anterior deste gráfico: '
         'esforço total da barra de sinal abaixo de 80% da média das barras '
         'da mesma direção. Testa se os dois filtros se somam ou se brigam.'),

        (E.Config(nome='V10', rotulo='controle: lado invertido', ma_tipo='ema',
                  modo='fixo', leque_min=L, inverter=True),
         'Controle estatístico. Mesma detecção e mesma gestão da V2, operando '
         'o lado OPOSTO. Se a vantagem da V2 for de direção, esta variante '
         'tem de ser claramente negativa.'),
    ]


# --------------------------------------------------------------------------
# blocos de analise
# --------------------------------------------------------------------------
def descr_dados(d):
    rng = d['range']
    dif = d.dt.diff().dt.total_seconds()
    return dict(
        barras=int(len(d)),
        inicio=str(d.dt.iloc[0]), fim=str(d.dt.iloc[-1]),
        dias=int(d.data.nunique()),
        barras_por_dia=float(len(d) / d.data.nunique()),
        range_ticks={k: float(v) for k, v in
                     rng.describe(percentiles=[.01, .5, .99]).items()},
        segundos_por_barra={k: float(v) for k, v in
                            dif.describe(percentiles=[.5, .9]).items()
                            if k != 'count'},
        preco_min=float(d.low.min()), preco_max=float(d.high.max()),
        premissa=E.conferir_premissa(d),
        horas=[int(h) for h in sorted(d.hora.unique())],
    )


def descr_indicador(d):
    s = d.sinal.to_numpy()
    return dict(
        parametros={k: (bool(v) if isinstance(v, bool) else v)
                    for k, v in E.Ind().__dict__.items()},
        total=int((s != 0).sum()),
        absorcao=int((np.abs(s) == 1).sum()),
        divergencia=int((np.abs(s) == 2).sum()),
        alta=int((s > 0).sum()), baixa=int((s < 0).sum()),
        pct_barras=float((s != 0).mean()),
        sinais_por_dia=float((s != 0).sum() / d.data.nunique()),
    )


def descr_medias(df):
    """Compara as duas familias de media como CONTEXTO, antes de qualquer
    operacao. E aqui que se ve por que a Hull se comporta diferente."""
    out = {}
    for ma in GRID_MA:
        d = E.medias(df, E.Config(ma_tipo=ma))
        ok = d.ma_ok.to_numpy()
        up, dn = d.leque_up.to_numpy(), d.leque_dn.to_numpy()
        ordenado = up | dn
        # Quantas vezes o leque troca de lado: a medida de "quanto a media muda
        # de ideia". Contar so as viradas DIRETAS de +1 para -1 nao serve --
        # entre uma tendencia e a oposta quase sempre passa um trecho embolado,
        # e a conta daria quase zero para as duas familias. O certo e comprimir
        # a sequencia ignorando os zeros e contar as trocas de sinal ali.
        lado = np.where(up, 1, np.where(dn, -1, 0))[ok]
        nz = lado[lado != 0]
        trocas = int(np.sum(nz[1:] != nz[:-1])) if len(nz) > 1 else 0
        lq = d.leque.to_numpy()[ok]
        # duracao media de um trecho ordenado, em barras
        blocos, atual = [], 0
        for x in ordenado[ok]:
            if x:
                atual += 1
            else:
                if atual:
                    blocos.append(atual)
                atual = 0
        if atual:
            blocos.append(atual)
        out[ma] = dict(
            aquecimento=int(np.argmax(ok)),
            pct_ordenado=float(ordenado[ok].mean()),
            pct_alta=float(up[ok].mean()), pct_baixa=float(dn[ok].mean()),
            pct_embolado=float(1 - ordenado[ok].mean()),
            trocas_de_lado=trocas,
            barras_por_troca=float(ok.sum() / max(1, trocas)),
            duracao_media_tendencia=float(np.mean(blocos)) if blocos else 0.0,
            duracao_mediana_tendencia=float(np.median(blocos)) if blocos else 0.0,
            leque={k: float(v) for k, v in
                   pd.Series(lq).describe(percentiles=[.25, .5, .75, .9]).items()},
            pct_leque_400=float((lq >= 400).mean()),
        )
    return out


def ambiguidade(prep):
    """O bloco de metodo, e o achado principal do estudo.

    Num grafico de range vale uma regra geometrica exata: uma barra percorre
    no maximo `range` ticks, entao ela NAO consegue tocar dois niveis
    separados por mais que isso. Consequencias:

      - stop + alvo > range  ->  stop e alvo nunca sao tocados na mesma barra,
        e a hipotese pessimista/otimista deixa de importar.
      - nos modos que movem o stop para a ENTRADA, ha um segundo instante
        indatado: a barra que arma o gatilho. Ela abre exatamente na entrada,
        entao qualquer pavio contrario "volta ao breakeven" no papel. Isso so
        para de acontecer quando o gatilho fica a mais de um range da entrada.

    Este bloco mede a largura do intervalo (piso..teto) de cada combinacao, e
    a largura zero e a prova de que o numero nao depende de convencao.
    """
    linhas = []
    for st in GRID_STOP:
        for modo in E.MODOS:
            vals = []
            for kw in (dict(be_proxima_barra=False, ordem_intrabar='pessimista'),
                       dict(be_proxima_barra=True, ordem_intrabar='pessimista'),
                       dict(be_proxima_barra=True, ordem_intrabar='otimista')):
                cfg = E.Config(ma_tipo='ema', modo=modo, leque_min=400.0,
                               stop_ticks=st, **kw)
                vals.append(E.estatisticas(E.rodar(prep['ema'], cfg), cfg)
                            .get('expectativa_R', 0.0))
            larg = max(vals) - min(vals)
            linhas.append(dict(
                stop_ticks=st, alvo_ticks=2 * st, modo=modo,
                modo_rotulo=E.MODO_ROTULO[modo],
                piso=vals[0], padrao=vals[1], teto=vals[2],
                largura=float(larg), mensuravel=bool(larg < 0.02),
                # as duas regras geometricas, calculadas e nao chutadas
                soma_maior_que_range=bool(st + 2 * st > RNG),
                gatilho_maior_que_range=bool(st >= RNG),
            ))
    return linhas


def grid(prep):
    """O grid inteiro, publicado. Sem isto, o melhor numero da tabela seria
    lido como descoberta em vez de como o maximo de N tentativas."""
    out = []
    for ma in GRID_MA:
        for lq in GRID_LEQUE:
            for modo in E.MODOS:
                for st in GRID_STOP:
                    cfg = E.Config(ma_tipo=ma, leque_min=lq, modo=modo,
                                   stop_ticks=st)
                    t = E.rodar(prep[ma], cfg)
                    if len(t) < 40:
                        continue
                    s = E.estatisticas(t, cfg)
                    # a largura do intervalo diz se o numero e confiavel
                    cfg_piso = E.com(cfg, be_proxima_barra=False)
                    piso = E.estatisticas(E.rodar(prep[ma], cfg_piso), cfg_piso)
                    out.append(dict(
                        ma_tipo=ma, leque_min=lq, modo=modo, stop_ticks=st,
                        n=s['operacoes'], acerto=s['acerto'],
                        expectativa_R=s['expectativa_R'],
                        expectativa_ticks=s['expectativa_ticks'],
                        fator_lucro=s['fator_lucro'], payoff=s['payoff'],
                        t_stat=s['t_stat'], drawdown_R=s['drawdown_R'],
                        max_perdas_seguidas=s['max_perdas_seguidas'],
                        piso_R=piso.get('expectativa_R', 0.0),
                        mensuravel=bool(abs(s['expectativa_R'] -
                                            piso.get('expectativa_R', 0.0)) < 0.02),
                    ))
    return out


def comparacao_medias(grade):
    """EMA contra Hull, par a par: mesma largura de leque, mesmo modo, mesmo
    stop. Comparar so os campeoes de cada familia seria comparar dois maximos;
    o pareamento mede a familia, e nao a sorte de uma celula.
    """
    def chave(g):
        return (g['leque_min'], g['modo'], g['stop_ticks'])
    ema = {chave(g): g for g in grade if g['ma_tipo'] == 'ema'}
    hull = {chave(g): g for g in grade if g['ma_tipo'] == 'hull'}
    pares = [k for k in ema if k in hull]

    def conta(ks):
        v = sum(1 for k in ks if ema[k]['expectativa_R'] > hull[k]['expectativa_R'])
        dif = [ema[k]['expectativa_R'] - hull[k]['expectativa_R'] for k in ks]
        return dict(pares=len(ks), ema_vence=v, hull_vence=len(ks) - v,
                    diferenca_media=float(np.mean(dif)) if dif else 0.0,
                    diferenca_mediana=float(np.median(dif)) if dif else 0.0)

    mens = [k for k in pares if ema[k]['mensuravel'] and hull[k]['mensuravel']]
    excecoes = sorted(
        (dict(leque_min=k[0], modo=k[1], stop_ticks=k[2],
              ema=ema[k]['expectativa_R'], hull=hull[k]['expectativa_R'])
         for k in pares if ema[k]['expectativa_R'] <= hull[k]['expectativa_R']),
        key=lambda x: x['stop_ticks'])
    return dict(todos=conta(pares), mensuraveis=conta(mens),
                excecoes=excecoes)


def sweep_stop(prep, n):
    """Varredura fina do stop, com a gestao fixa e a selecao da escolha.

    Duas coisas aparecem de uma vez nesta tabela:

    [1] O LIMITE DE MENSURABILIDADE. Com alvo = 2 x stop, os dois niveis
        distam 3 x stop um do outro. A barra percorre no maximo `range`, entao
        ela so consegue tocar os dois se 3*stop <= range -- ou seja, o numero
        deixa de depender de convencao exatamente a partir de
            stop > range/3 = %.1f ticks.
        A coluna `largura` cai de meio R para ZERO nesse ponto.

    [2] O PLATO. Depois do limite, o resultado desce suavemente com o stop.
        Nao ha pico estreito, o que e bom sinal -- mas o topo do plato nao
        sobrevive a escolha fora da amostra (ver `escolha_cruzada`).
    """ % (RNG / 3)
    meio = n // 2
    out = []
    for st in (110.0, 120.0, 130.0, 135.0, 145.0, 160.0, 175.0, 194.0,
               220.0, 250.0, 291.0, 388.0):
        cfg = E.Config(ma_tipo='ema', modo='fixo', leque_min=400.0,
                       stop_ticks=st)
        t = E.rodar(prep['ema'], cfg)
        s = E.estatisticas(t, cfg)
        c2 = E.com(cfg, ordem_intrabar='otimista')
        so = E.estatisticas(E.rodar(prep['ema'], c2), c2)
        h1 = E.estatisticas(t[t.sinal_i < meio], cfg)
        h2 = E.estatisticas(t[t.sinal_i >= meio], cfg)
        out.append(dict(
            stop_ticks=st, alvo_ticks=2 * st, n=s['operacoes'],
            acerto=s['acerto'], expectativa_R=s['expectativa_R'],
            expectativa_ticks=s['expectativa_ticks'],
            fator_lucro=s['fator_lucro'], t_stat=s['t_stat'],
            drawdown_R=s['drawdown_R'],
            largura=float(abs(so['expectativa_R'] - s['expectativa_R'])),
            mensuravel=bool(abs(so['expectativa_R'] - s['expectativa_R']) < 0.02),
            metade_1a=h1.get('expectativa_R', 0.0),
            metade_2a=h2.get('expectativa_R', 0.0)))
    return dict(limite_teorico=RNG / 3, linhas=out)


def escolha_cruzada(prep, n, grade):
    """Escolhe a configuracao numa metade da amostra e testa na outra.

    Com 160 configuracoes no grid, o melhor numero da tabela e o maximo de 160
    tentativas e nao serve de estimativa. A unica leitura honesta e: escolher
    onde nao se vai medir, e medir onde nao se escolheu. So entram no concurso
    as configuracoes MENSURAVEIS -- de nada adianta escolher a melhor entre
    numeros que dependem de uma convencao.
    """
    meio = n // 2
    cands = [g for g in grade if g['mensuravel']]

    def mede(g, lo, hi):
        cfg = E.Config(ma_tipo=g['ma_tipo'], modo=g['modo'],
                       leque_min=g['leque_min'], stop_ticks=g['stop_ticks'])
        t = E.rodar(prep[g['ma_tipo']], cfg)
        sub = t[(t.sinal_i >= lo) & (t.sinal_i < hi)]
        s = E.estatisticas(sub, cfg)
        return dict(n=s.get('operacoes', 0), acerto=s.get('acerto', 0.0),
                    expectativa_R=s.get('expectativa_R', 0.0),
                    fator_lucro=s.get('fator_lucro', 0.0),
                    t_stat=s.get('t_stat', 0.0))

    out = {}
    for rot, (alo, ahi), (blo, bhi) in (
            ('escolhe_1a_testa_2a', (0, meio), (meio, n)),
            ('escolhe_2a_testa_1a', (meio, n), (0, meio))):
        pontuado = []
        for g in cands:
            m = mede(g, alo, ahi)
            if m['n'] >= 80:
                pontuado.append((m['expectativa_R'], g, m))
        if not pontuado:
            continue
        pontuado.sort(key=lambda x: -x[0])
        _, melhor, dentro = pontuado[0]
        fora = mede(melhor, blo, bhi)
        # a referencia: como se sai a mediana das candidatas, fora da amostra
        medianas = sorted(mede(g, blo, bhi)['expectativa_R']
                          for _, g, _ in pontuado)
        out[rot] = dict(
            escolhida=dict(ma_tipo=melhor['ma_tipo'], modo=melhor['modo'],
                           leque_min=melhor['leque_min'],
                           stop_ticks=melhor['stop_ticks']),
            candidatas=len(pontuado), dentro=dentro, fora=fora,
            mediana_fora=float(medianas[len(medianas) // 2]))
    return out


def validacao(prep, n):
    """A disciplina de sempre, aplicada a configuracao escolhida."""
    cfg = E.Config(**ESCOLHA)
    d = prep[cfg.ma_tipo]
    t = E.rodar(d, cfg)
    meio, terco = n // 2, n // 3

    def st(sub):
        s = E.estatisticas(sub, cfg)
        return dict(n=s.get('operacoes', 0), acerto=s.get('acerto', 0.0),
                    expectativa_R=s.get('expectativa_R', 0.0),
                    expectativa_ticks=s.get('expectativa_ticks', 0.0),
                    fator_lucro=s.get('fator_lucro', 0.0),
                    t_stat=s.get('t_stat', 0.0))

    metades = {nm: st(t[(t.sinal_i >= lo) & (t.sinal_i < hi)])
               for nm, lo, hi in (('1a', 0, meio), ('2a', meio, n))}
    tercos = [dict(terco=k + 1,
                   **st(t[(t.sinal_i >= k * terco) & (t.sinal_i < (k + 1) * terco)]))
              for k in range(3)]

    # controles
    contr = {}
    for rot, kw in (('invertido', dict(inverter=True)),
                    ('sem_leque', dict(exige_leque=False, leque_min=0.0)),
                    ('leque_contra', None)):
        if kw is None:
            dd = d.copy()
            lados = np.sign(dd.sinal.to_numpy())
            up, dn = dd.leque_up.to_numpy(), dd.leque_dn.to_numpy()
            contra = np.where(lados > 0, dn, np.where(lados < 0, up, False))
            dd.loc[~contra, 'sinal'] = 0
            c2 = E.com(cfg, exige_leque=False, leque_min=0.0)
            contr[rot] = st(E.rodar(dd, c2))
            continue
        c2 = E.com(cfg, **kw)
        contr[rot] = st(E.rodar(d, c2))

    # entradas com direcao sorteada nas MESMAS barras e a MESMA gestao:
    # o controle que separa "o gatilho le direcao" de "a gestao 1:2 e boa"
    rng = np.random.default_rng(20260906)
    dd = d.copy()
    lados = E.sinais(dd, cfg)
    idx = np.where(lados != 0)[0]
    sorte = rng.choice([-1, 1], size=len(idx))
    dd['sinal'] = 0
    dd.loc[dd.index[idx], 'sinal'] = sorte
    c2 = E.com(cfg, exige_leque=False, leque_min=0.0)
    contr['direcao_sorteada'] = st(E.rodar(dd, c2))

    return dict(escolha=ESCOLHA, metades=metades, tercos=tercos,
                controles=contr, geral=st(t))


def curva(t):
    if not len(t):
        return []
    cum = t.ticks.cumsum().to_numpy()
    return [[str(pd.Timestamp(x).date()), round(float(y), 1)]
            for x, y in zip(t.dt.to_numpy(), cum)]


def por_hora(t):
    if not len(t):
        return []
    g = t.groupby('hora').agg(n=('ticks', 'size'), soma=('ticks', 'sum'),
                              exp=('ticks', 'mean'),
                              acerto=('ticks', lambda s: float((s > 0).mean())))
    return [dict(hora=int(k), n=int(v.n), ticks=float(v.soma),
                 expectativa_ticks=float(v.exp), acerto=float(v.acerto))
            for k, v in g.iterrows()]


def trades_json(t, limite=400):
    a = t.copy()
    if len(a) > limite:
        a = a.iloc[np.linspace(0, len(a) - 1, limite).astype(int)]
    cols = ['sinal_i', 'saida_i', 'lado', 'tipo', 'entrada', 'motivo', 'ticks',
            'barras', 'hora', 'leque', 'dist_ma1', 'esf_rel', 'parcial']
    out = []
    for _, r in a.iterrows():
        out.append([int(r.sinal_i), int(r.saida_i), r.lado, int(r.tipo),
                    round(float(r.entrada), 2), r.motivo, round(float(r.ticks), 1),
                    int(r.barras), int(r.hora), round(float(r.leque)),
                    round(float(r.dist_ma1)), round(float(r.esf_rel), 2),
                    bool(r.parcial)])
    return dict(colunas=cols, linhas=out, total=int(len(t)))


def barras_json(d):
    """OHLC + agressao comprimidos. As MEDIAS o navegador recalcula -- sao
    seis series de 39 mil pontos, e mandar prontas dobraria o arquivo."""
    c = np.round(d.close.to_numpy() / TICK).astype(np.int64)
    o = np.round(d.open.to_numpy() / TICK).astype(np.int64) - c
    h = np.round(d.high.to_numpy() / TICK).astype(np.int64) - c
    l = np.round(d.low.to_numpy() / TICK).astype(np.int64) - c
    ts = (d.dt - pd.Timestamp('1970-01-01')).dt.total_seconds() \
        .to_numpy().astype('int64')
    s = d.sinal.to_numpy()
    return dict(t0=int(ts[0]), dt=np.diff(ts, prepend=ts[0]).tolist(),
                c=c.tolist(), o=o.tolist(), h=h.tolist(), l=l.tolist(),
                cv=d.tickvol.to_numpy().astype(int).tolist(),
                vv=d.vol.to_numpy().astype(int).tolist(),
                sinais=[[int(i), int(s[i])] for i in np.where(s != 0)[0]])


# --------------------------------------------------------------------------
def principal():
    os.makedirs(SAIDA, exist_ok=True)
    print('lendo', os.path.basename(E.ARQUIVO))
    bruto = E.carregar()
    base = E.esforco_resultado(bruto)
    prep = {ma: E.medias(base, E.Config(ma_tipo=ma)) for ma in GRID_MA}
    d = prep['ema']
    n = len(d)
    print('%d barras, %s a %s' % (n, d.dt.iloc[0], d.dt.iloc[-1]))

    prem = E.conferir_premissa(d)
    print('premissa: range mediano %.0f t, %.1f%% das barras dentro de +-10%%'
          % (prem['range_mediana'], 100 * prem['range_dentro_10pct']))

    res = dict(gerado_em=datetime.now().strftime('%Y-%m-%d %H:%M'),
               arquivo=os.path.basename(E.ARQUIVO),
               tick=TICK, range_nominal=RNG, escolha=ESCOLHA,
               modos={k: v for k, v in E.MODO_ROTULO.items()},
               dados=descr_dados(d), indicador=descr_indicador(d))

    I = res['indicador']
    print('\n--- o gatilho ---')
    print('  %d sinais (%.1f%% das barras): absorcao %d, divergencia %d'
          % (I['total'], 100 * I['pct_barras'], I['absorcao'], I['divergencia']))

    print('\n--- as medias como contexto ---')
    res['medias'] = descr_medias(base)
    for ma, m in res['medias'].items():
        print('  %-5s ordenado %.1f%% do tempo | embolado %.1f%% | troca de lado '
              'a cada %.0f barras | tendencia dura %.0f barras (mediana) | '
              'leque mediano %.0f t'
              % (ma, 100 * m['pct_ordenado'], 100 * m['pct_embolado'],
                 m['barras_por_troca'], m['duracao_mediana_tendencia'],
                 m['leque']['50%']))

    print('\n--- ambiguidade: quais gestoes sao mensuraveis neste grafico ---')
    res['ambiguidade'] = ambiguidade(prep)
    for a in res['ambiguidade']:
        if a['stop_ticks'] in (194.0, 388.0, 450.0):
            print('  S=%3.0f %-11s piso %+.3f  padrao %+.3f  teto %+.3f  '
                  'largura %.3f R%s'
                  % (a['stop_ticks'], a['modo'], a['piso'], a['padrao'],
                     a['teto'], a['largura'],
                     '   <- MENSURAVEL' if a['mensuravel'] else ''))

    print('\n--- grid completo ---')
    res['grid'] = grid(prep)
    print('  %d configuracoes medidas' % len(res['grid']))
    for g in sorted(res['grid'], key=lambda x: -x['expectativa_R'])[:8]:
        print('  %-5s leque>=%3.0f %-11s S=%3.0f n=%4d acerto %5.1f%% '
              'expR %+.3f PF %.2f t=%+.2f %s'
              % (g['ma_tipo'], g['leque_min'], g['modo'], g['stop_ticks'],
                 g['n'], 100 * g['acerto'], g['expectativa_R'],
                 g['fator_lucro'], g['t_stat'],
                 'mensuravel' if g['mensuravel'] else 'INDETERMINADO'))
    mens = [g for g in res['grid'] if g['mensuravel']]
    print('  ... das %d, apenas %d sao mensuraveis sem convencao'
          % (len(res['grid']), len(mens)))
    print('  melhor MENSURAVEL:')
    for g in sorted(mens, key=lambda x: -x['expectativa_R'])[:3]:
        print('    %-5s leque>=%3.0f %-11s S=%3.0f n=%4d expR %+.3f t=%+.2f'
              % (g['ma_tipo'], g['leque_min'], g['modo'], g['stop_ticks'],
                 g['n'], g['expectativa_R'], g['t_stat']))

    print('\n--- EMA contra Hull, par a par ---')
    res['comparacao_medias'] = comparacao_medias(res['grid'])
    CM = res['comparacao_medias']
    for k, rot in (('todos', 'todos os pares'), ('mensuraveis', 'só os mensuráveis')):
        c = CM[k]
        print('  %-18s %d pares: EMA vence %d, Hull vence %d | diferenca '
              'mediana %+.3f R' % (rot, c['pares'], c['ema_vence'],
                                   c['hull_vence'], c['diferenca_mediana']))
    print('  as %d excecoes acontecem com stop de: %s'
          % (len(CM['excecoes']),
             sorted(set(int(e['stop_ticks']) for e in CM['excecoes']))))

    print('\n--- varredura do stop (ema, leque>=400, fixo) ---')
    res['sweep_stop'] = sweep_stop(prep, n)
    print('  limite teorico de mensurabilidade: stop > range/3 = %.1f t'
          % res['sweep_stop']['limite_teorico'])
    for g in res['sweep_stop']['linhas']:
        print('  S=%3.0f alvo=%3.0f n=%4d acerto %5.1f%% expR %+.3f t=%+.2f  '
              'largura %.3f%s  | 1a %+.3f  2a %+.3f'
              % (g['stop_ticks'], g['alvo_ticks'], g['n'], 100 * g['acerto'],
                 g['expectativa_R'], g['t_stat'], g['largura'],
                 '  MENSURAVEL' if g['mensuravel'] else '  indeterminado',
                 g['metade_1a'], g['metade_2a']))

    print('\n--- escolha cruzada: escolhe numa metade, testa na outra ---')
    res['escolha_cruzada'] = escolha_cruzada(prep, n, res['grid'])
    for k, v in res['escolha_cruzada'].items():
        e = v['escolhida']
        print('  %s: escolheu %s / %s / leque>=%.0f / S=%.0f (entre %d candidatas)'
              % (k, e['ma_tipo'], e['modo'], e['leque_min'], e['stop_ticks'],
                 v['candidatas']))
        print('      dentro expR %+.3f (t %+.2f)  ->  FORA expR %+.3f (t %+.2f, '
              'n=%d) | mediana das candidatas fora: %+.3f'
              % (v['dentro']['expectativa_R'], v['dentro']['t_stat'],
                 v['fora']['expectativa_R'], v['fora']['t_stat'],
                 v['fora']['n'], v['mediana_fora']))

    print('\n--- validacao da escolha ---')
    res['validacao'] = validacao(prep, n)
    V = res['validacao']
    print('  geral      n=%4d acerto %5.1f%% expR %+.3f t=%+.2f'
          % (V['geral']['n'], 100 * V['geral']['acerto'],
             V['geral']['expectativa_R'], V['geral']['t_stat']))
    for nm in ('1a', '2a'):
        v = V['metades'][nm]
        print('  %s metade  n=%4d acerto %5.1f%% expR %+.3f t=%+.2f'
              % (nm[0], v['n'], 100 * v['acerto'], v['expectativa_R'],
                 v['t_stat']))
    for v in V['tercos']:
        print('  %do terco   n=%4d acerto %5.1f%% expR %+.3f t=%+.2f'
              % (v['terco'], v['n'], 100 * v['acerto'], v['expectativa_R'],
                 v['t_stat']))
    for k, v in V['controles'].items():
        print('  %-18s n=%4d acerto %5.1f%% expR %+.3f t=%+.2f'
              % (k, v['n'], 100 * v['acerto'], v['expectativa_R'], v['t_stat']))

    print('\n--- variantes ---')
    print('  %-4s %-38s %5s %7s %8s %6s %6s %7s %6s' %
          ('', 'variante', 'ops', 'acerto', 'expR', 'PF', 'payoff', 'DD(R)', 'seqL'))
    res['variantes'] = []
    for cfg, desc in variantes():
        d_ = prep[cfg.ma_tipo]
        t = E.rodar(d_, cfg)
        s = E.estatisticas(t, cfg)
        t.to_csv(os.path.join(SAIDA, 'trades_%s.csv' % cfg.nome),
                 index=False, sep=';', decimal=',')

        otim = E.estatisticas(E.rodar(d_, E.com(cfg, ordem_intrabar='otimista')), cfg)
        piso_cfg = E.com(cfg, be_proxima_barra=False)
        piso = E.estatisticas(E.rodar(d_, piso_cfg), piso_cfg)
        custo = {}
        for c in CUSTOS:
            cc = E.com(cfg, custo_ticks=c)
            custo[str(c)] = E.estatisticas(E.rodar(d_, cc), cc)
        meio = n // 2
        metades = {nm: E.estatisticas(t[(t.sinal_i >= lo) & (t.sinal_i < hi)], cfg)
                   for nm, lo, hi in (('1a', 0, meio), ('2a', meio, n))}

        res['variantes'].append(dict(
            nome=cfg.nome, rotulo=cfg.rotulo, descricao=desc,
            cfg=E.resumo_cfg(cfg), stats=s, stats_otimista=otim,
            stats_piso=piso,
            largura_intervalo=float(abs(otim.get('expectativa_R', 0) -
                                        piso.get('expectativa_R', 0))),
            mensuravel=bool(abs(otim.get('expectativa_R', 0) -
                                piso.get('expectativa_R', 0)) < 0.02),
            custo=custo, metades=metades, curva=curva(t),
            por_hora=por_hora(t), trades=trades_json(t)))
        print('  %-4s %-38s %5d %6.1f%% %+8.3f %6.2f %6.2f %+7.1f %6d' %
              (cfg.nome, cfg.rotulo, s.get('operacoes', 0),
               100 * s.get('acerto', 0), s.get('expectativa_R', 0),
               s.get('fator_lucro', 0), s.get('payoff', 0),
               s.get('drawdown_R', 0), s.get('max_perdas_seguidas', 0)))

    with open(os.path.join(SAIDA, 'resumo.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(SAIDA, 'barras.json'), 'w', encoding='utf-8') as f:
        json.dump(barras_json(d), f, separators=(',', ':'))
    print('\nsaida/resumo.json e saida/barras.json gravados.')


if __name__ == '__main__':
    # o console do Windows abre em cp1252 e engasga em '>=' tipografico e nos
    # acentos; o arquivo de saida e sempre UTF-8
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        principal()
    texto = buf.getvalue()
    print(texto, end='')
    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(SAIDA, 'console.txt'), 'w', encoding='utf-8') as f:
        f.write(texto)
