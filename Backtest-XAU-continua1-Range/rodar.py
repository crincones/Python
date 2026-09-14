# -*- coding: utf-8 -*-
"""
Roda o backtest completo e grava saida/.

    python rodar.py

Gera:
    saida/resumo.json     TUDO que os relatorios precisam. E a unica fonte de
                          numeros: RESULTADOS.md, relatorio.html, PLANO.md e
                          plano.html leem daqui, entao numero em documento
                          nunca fica defasado.
    saida/trades_*.csv    operacao a operacao, de cada variante
    saida/barras.json     OHLC + agressao comprimidos, para os graficos
    saida/console.txt     o mesmo que sai na tela

Depois rode `python resultados_md.py`, `python relatorio.py` e `python plano.py`.
"""
import contextlib
import io
import json
import math
import os
from datetime import datetime

import numpy as np
import pandas as pd

import engine as E

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
TICK = E.TICK
RNG = E.RANGE_NOMINAL          # 388 ticks: o range da barra, e 1R

# horas escolhidas por validacao cruzada. Ao contrario do estudo do grafico de
# 521 ticks, aqui a intersecao entre as duas metades e de UMA hora so e nem ela
# se confirma fora da amostra -- ver `valida_horario`. A tupla existe para que
# a variante do horario possa ser publicada com o resultado que ela realmente
# tem, e nao para ser recomendada.
HORAS_BOAS = (3, 4, 18)

# o filtro que sobreviveu: esforco total da barra de sinal abaixo de 80% da
# media das barras da mesma direcao
ESF_MAX = 0.80

CUSTOS = (0, 10, 20, 40)       # ticks de ida+volta testados na sensibilidade

# gestao neutra 1:1, usada em toda comparacao de GATILHO. Com alvo e stop
# iguais, a estatistica mede direcao e nada mais.
NEUTRA = dict(parcial_frac=1.0, parcial_ticks=RNG, alvo_ticks=RNG,
              stop_ticks=RNG)

# MEIO RANGE: stop e alvo a 194 ticks, exatamente metade do range da barra.
#
# Esta e a unica gestao deste grafico em que a ambiguidade dentro da barra NAO
# EXISTE. Como high-low = 388 por construcao, uma barra nao consegue percorrer
# 194 ticks para cima E 194 para baixo a partir do proprio open: os dois lados
# somados dariam 388, e um deles teria de ser alcancado exatamente na borda.
# Medido no arquivo, isso acontece em 0,03% das barras. Consequencia: as
# hipoteses 'pessimista' e 'otimista' devolvem o MESMO numero, e a estatistica
# nao depende de nenhuma suposicao sobre a ordem dos toques -- o unico ponto
# cego que resta em qualquer backtest feito sobre OHLC.
MEIO = dict(parcial_frac=1.0, parcial_ticks=RNG / 2, alvo_ticks=RNG / 2,
            stop_ticks=RNG / 2)


# --------------------------------------------------------------------------
# variantes publicadas
# --------------------------------------------------------------------------
def variantes():
    return [
        (E.Config(nome='V0', rotulo='regra literal'),
         'Todo sinal do indicador — absorção e divergência, compra e venda — '
         'operado a mercado no fechamento da barra de sinal, a favor da '
         'direção dela. Stop de 388 ticks (um range inteiro = 1R), parcial de '
         '50% em +1R levando o stop a breakeven, saída final do restante em '
         '+3R. É a leitura literal do indicador, sem nenhuma restrição.'),

        (E.Config(nome='V1', rotulo='só absorção', tipos=(1,)),
         'Só o sinal 1, o verde/vermelho: a barra virou o movimento andando '
         'menos que o normal e com menos agressão a favor que o normal. É o '
         'sinal que responde por 87% dos disparos.'),

        (E.Config(nome='V2', rotulo='só divergência', tipos=(2,)),
         'Só o sinal 2, o azul: o pivô de duas barras quase sem pavio cujo '
         'delta somado aponta para o lado contrário ao da resolução. Sinal '
         'raro — vale medir separado justamente porque a lógica dele é outra.'),

        (E.Config(nome='V3', rotulo='entrada limitada no meio do range',
                  entrada='meio'),
         'Mesma seleção da V0, mas em vez de entrar a mercado no fechamento, '
         'deixa uma ordem limitada no MEIO do range da barra de sinal, válida '
         'por uma barra. Compra mais barato quando ativa e abandona pouco mais '
         'da metade dos sinais quando não ativa. O número publicado é o piso '
         'do intervalo: a barra que preencheu a ordem não tem hora marcada no '
         'arquivo, e aqui ela só pode piorar a operação — ver §3.'),

        (E.Config(nome='V4', rotulo='gestão 1:1, sem runner', **NEUTRA),
         'Mesma seleção da V0, gestão diferente: a posição inteira sai em +1R, '
         'sem parcial e sem runner. Com alvo e stop iguais, a taxa de acerto '
         'passa a medir DIREÇÃO e nada mais — é a métrica com que todo filtro '
         'foi julgado neste estudo.'),

        (E.Config(nome='V5', rotulo='só nas horas selecionadas',
                  horas=HORAS_BOAS, **NEUTRA),
         'A segregação por horário que a estratégia pede. As horas foram '
         'escolhidas em uma metade da amostra e testadas na outra, nos dois '
         'sentidos. A variante está publicada para mostrar o resultado real '
         'dessa validação, que foi negativo — não como recomendação.'),

        (E.Config(nome='V6', rotulo='esforço baixo, gestão 1:1',
                  esf_max=ESF_MAX, **NEUTRA),
         'A restrição que sobreviveu: só dispara quando o ESFORÇO TOTAL da '
         'barra de sinal está abaixo de 80% da média das barras da mesma '
         'direção. Uma barra que virou o movimento com pouca gente '
         'negociando é a forma mais pura da tese de absorção. Gestão 1:1 em '
         '+1R.'),

        (E.Config(nome='V7', rotulo='meio range — todos os sinais', **MEIO),
         'Stop e alvo a 194 ticks: exatamente METADE do range da barra. Como '
         'a barra tem 388 ticks por construção, ela não consegue alcançar os '
         'dois lados — a ambiguidade dentro da barra deixa de existir e o '
         'número não depende de nenhuma suposição. É a medida mais limpa que '
         'este gráfico permite, e todo sinal do indicador entra nela.'),

        (E.Config(nome='V8', rotulo='meio range + esforço baixo',
                  esf_max=ESF_MAX, **MEIO),
         'A V7 restrita ao esforço baixo da V6 — a combinação de melhor '
         'estatística de todo o estudo, e a única medida sem ambiguidade '
         'nenhuma. É a que o PLANO.md adota.'),

        (E.Config(nome='V9', rotulo='controle: lado invertido',
                  esf_max=ESF_MAX, inverter=True, **MEIO),
         'Controle estatístico. Mesma detecção e mesma gestão da V8, operando '
         'o lado OPOSTO ao que o indicador aponta. Se a vantagem da V8 for '
         'mesmo de direção, esta variante tem de ser o espelho negativo dela.'),
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
                     rng.describe(percentiles=[.01, .05, .5, .95, .99]).items()},
        segundos_por_barra={k: float(v) for k, v in
                            dif.describe(percentiles=[.5, .9]).items() if k != 'count'},
        preco_min=float(d.low.min()), preco_max=float(d.high.max()),
        premissa=E.conferir_premissa(d),
        esforco={k: float(v) for k, v in
                 d.esf.describe(percentiles=[.1, .5, .9]).items()},
        corpo_frac={k: float(v) for k, v in
                    d.corpo_frac.describe(percentiles=[.1, .5, .9]).items()},
        horas=[int(h) for h in sorted(d.hora.unique())],
        barras_por_hora={str(int(k)): int(v)
                         for k, v in d.groupby('hora').size().items()},
    )


def descr_indicador(d):
    """O que o gatilho produz, antes de qualquer regra de operacao."""
    s = d.sinal.to_numpy()
    sig = d[s != 0]
    q = [.1, .25, .5, .75, .9]

    def dist(col, sub):
        return {k: float(v) for k, v in sub[col].describe(percentiles=q).items()}

    return dict(
        parametros={k: (v if not isinstance(v, bool) else bool(v))
                    for k, v in E.Ind().__dict__.items()},
        total=int((s != 0).sum()),
        absorcao_alta=int((s == 1).sum()), absorcao_baixa=int((s == -1).sum()),
        divergencia_alta=int((s == 2).sum()), divergencia_baixa=int((s == -2).sum()),
        pct_barras=float((s != 0).mean()),
        sinais_por_dia=float((s != 0).sum() / d.data.nunique()),
        barras_entre_sinais=float(len(d) / max(1, (s != 0).sum())),
        por_hora={str(int(k)): int(v)
                  for k, v in d[s != 0].groupby('hora').size().items()},
        # distribuicoes das metricas do indicador NAS BARRAS DE SINAL
        res_rel=dist('res_rel', sig), qual_rel=dist('qual_rel', sig),
        esf_rel=dist('esf_rel', sig), efic=dist('efic', sig),
        corpo_frac=dist('corpo_frac', sig), contra=dist('contra', sig),
        # e no universo inteiro, para comparar
        esf_rel_todas=dist('esf_rel', d), res_rel_todas=dist('res_rel', d),
        pct_esforco_baixo=float((sig.esf_rel <= ESF_MAX).mean()),
    )


def excursao(d):
    """MFE/MAE/deriva depois do sinal, sem NENHUMA regra de saida, contra dois
    controles aleatorios. E o teste de existencia da vantagem: se o gatilho tem
    leitura de direcao, a excursao tem de diferir da de uma entrada sorteada.

    A entrada e sempre o fechamento da barra de sinal, e a medida comeca na
    barra seguinte -- nada aqui olha para dentro da propria barra de sinal.
    """
    h, l, c = (d[k].to_numpy() for k in ('high', 'low', 'close'))
    n = len(d)
    s = d.sinal.to_numpy()
    idx = np.where(s != 0)[0]
    rng = np.random.default_rng(20260906)

    def medir(ii, ss, H):
        mfe, mae, dr = [], [], []
        for i, sg in zip(ii, ss):
            j = i + 1
            if j + H >= n:
                continue
            ent = c[i]
            hi, lo = h[j:j + H].max(), l[j:j + H].min()
            mfe.append((hi - ent) / TICK if sg > 0 else (ent - lo) / TICK)
            mae.append((ent - lo) / TICK if sg > 0 else (hi - ent) / TICK)
            dr.append(sg * (c[j + H - 1] - ent) / TICK)
        return np.array(mfe), np.array(mae), np.array(dr)

    def bloco(ii, ss):
        out = {}
        for H in (3, 5, 10, 20, 40):
            mfe, mae, dr = medir(ii, ss, H)
            ep = float(dr.std(ddof=1) / np.sqrt(len(dr))) if len(dr) > 1 else 0.0
            out[str(H)] = dict(
                n=int(len(mfe)),
                mfe_med=float(np.median(mfe)), mae_med=float(np.median(mae)),
                razao=float(np.median(mfe) / np.median(mae)),
                deriva_med=float(np.median(dr)), deriva_media=float(dr.mean()),
                # sem o erro padrao ao lado, qualquer deriva parece um achado
                deriva_erro=ep,
                deriva_t=float(dr.mean() / ep) if ep > 0 else 0.0)
        return out

    ri = rng.choice(np.arange(80, n - 200), size=len(idx), replace=False)
    out = dict(
        sinal=bloco(idx, np.sign(s[idx])),
        direcao_sorteada=bloco(idx, rng.choice([-1, 1], size=len(idx))),
        barra_e_direcao_sorteadas=bloco(ri, rng.choice([-1, 1], size=len(ri))),
    )
    for tp, nome in ((1, 'so_absorcao'), (2, 'so_divergencia')):
        ii = np.where(np.abs(s) == tp)[0]
        out[nome] = bloco(ii, np.sign(s[ii]))
    # o mesmo, dentro do filtro de esforco que sobreviveu
    ii = np.where((s != 0) & (d.esf_rel.to_numpy() <= ESF_MAX))[0]
    out['esforco_baixo'] = bloco(ii, np.sign(s[ii]))
    return out


def linha_base(d):
    """O controle mais importante do estudo.

    Num grafico de range, a direcao em que a barra seguinte RESOLVE (se ela
    percorre meio range para cima ou para baixo a partir do proprio open) e
    decidivel sem ambiguidade nenhuma -- ver a nota em MEIO. Isso permite medir
    a taxa de continuacao de barra para barra em TODO o arquivo, e nao so nos
    sinais.

    E aqui que o estudo descobre que o proprio grafico ja tem uma inclinacao:
    barras de range continuam na propria direcao mais que 50% das vezes. Um
    gatilho que dispara em barras de virada herda essa inclinacao de graca. Sem
    esta linha de base, os 54%-58% do indicador seriam creditados a ele
    inteiros -- e boa parte deles nao e dele.
    """
    o, h, l = (d[k].to_numpy() for k in ('open', 'high', 'low'))
    # +1 se a barra alcanca meio range para cima antes de meio range para baixo
    resolve = np.where((h - o) > (o - l), 1, -1)
    dirs = d.dir.to_numpy()
    s = d.sinal.to_numpy()
    esf_baixo = d.esf_rel.to_numpy() <= ESF_MAX
    virada = (dirs != 0) & (np.roll(dirs, 1) != 0) & (dirs == -np.roll(dirs, 1))

    def taxa(mask, alvo):
        m = mask[:-1]
        ok = resolve[1:][m] == alvo[:-1][m]
        n = int(len(ok))
        if not n:
            return dict(n=0, acerto=0.0, z=0.0)
        p = float(ok.mean())
        return dict(n=n, acerto=p, z=float((p - 0.5) / math.sqrt(0.25 / n)))

    grupos = [
        ('todas as barras', 'aposta na continuação da barra', taxa(dirs != 0, dirs)),
        ('barras de virada', 'a condição geométrica do gatilho, sozinha',
         taxa(virada, dirs)),
        ('virada + esforço baixo', 'sem as demais condições do indicador',
         taxa(virada & esf_baixo, dirs)),
        ('SINAL do indicador', 'absorção + divergência', taxa(s != 0, np.sign(s))),
        ('SINAL + esforço baixo', 'a seleção da V8',
         taxa((s != 0) & esf_baixo, np.sign(s))),
    ]
    ref = grupos[2][2]      # virada + esforco baixo: o controle emparelhado
    alvo = grupos[4][2]     # o que a V8 opera
    # o indicador so merece credito pelo que ele acrescenta ao controle que ja
    # tem as mesmas condicoes cruas -- barra de virada e esforco baixo
    se = math.sqrt(0.25 / ref['n'] + 0.25 / alvo['n']) if ref['n'] and alvo['n'] else 0
    return dict(
        grupos=[dict(grupo=a, nota=b, **c) for a, b, c in grupos],
        ganho=dict(base=ref['acerto'], com_indicador=alvo['acerto'],
                   diferenca=alvo['acerto'] - ref['acerto'],
                   z=float((alvo['acerto'] - ref['acerto']) / se) if se else 0.0),
    )


def busca(d):
    """Toda a busca por filtro que foi feita, com o z de cada tentativa.
    Publicar a lista inteira e o que permite ler o melhor z como o maximo de N
    tentativas, e nao como uma descoberta. Metrica neutra 1:1 sempre."""
    testes = [
        ('sem filtro nenhum', {}),
        ('só absorção (sinal 1)', dict(tipos=(1,))),
        ('só divergência (sinal 2)', dict(tipos=(2,))),
        ('só compras', dict(lados=('long',))),
        ('só vendas', dict(lados=('short',))),
        ('resultado da barra <= 30% do normal', dict(res_max=0.30)),
        ('resultado da barra <= 50% do normal', dict(res_max=0.50)),
        ('agressão a favor <= 0 (delta contra)', dict(qual_max=0.0)),
        ('agressão a favor <= 25% do normal', dict(qual_max=0.25)),
        ('eficiência <= 0,30', dict(efic_max=0.30)),
        ('eficiência <= 0,50', dict(efic_max=0.50)),
        ('esforço >= 100% do normal', dict(esf_min=1.0)),
        ('esforço >= 130% do normal', dict(esf_min=1.3)),
        ('esforço <= 60% do normal', dict(esf_max=0.60)),
        ('esforço <= 70% do normal', dict(esf_max=0.70)),
        ('esforço <= 80% do normal', dict(esf_max=0.80)),
        ('esforço <= 90% do normal', dict(esf_max=0.90)),
        ('esforço <= 100% do normal', dict(esf_max=1.00)),
        ('corpo >= 50% do range', dict(corpo_min=0.5)),
        ('corpo >= 70% do range', dict(corpo_min=0.7)),
        ('corpo <= 50% do range', dict(corpo_max=0.5)),
        ('vira no máximo 1 barra contrária', dict(contra_max=1)),
        ('vira no máximo 2 barras contrárias', dict(contra_max=2)),
        ('vira no máximo 3 barras contrárias', dict(contra_max=3)),
        ('entrada limitada no meio do range (piso)', dict(entrada='meio')),
        ('entrada limitada no meio do range (teto irrealizável)',
         dict(entrada='meio', trava_barra_fill=False), True),
        ('esforço <= 80% + só absorção', dict(esf_max=0.80, tipos=(1,))),
        ('esforço <= 80% + corpo <= 50%', dict(esf_max=0.80, corpo_max=0.5)),
        ('esforço <= 80% + vira <= 2 barras',
         dict(esf_max=0.80, contra_max=2)),
        ('esforço <= 80% + resultado <= 50%',
         dict(esf_max=0.80, res_max=0.50)),
        ('só nas horas selecionadas', dict(horas=HORAS_BOAS)),
    ]
    # Cada filtro e medido nas DUAS gestoes neutras: 1R (que depende da
    # hipotese pessimista) e meio range (que nao depende de hipotese nenhuma).
    # Publicar as duas evita a tentacao de escolher a metrica depois de ver o
    # resultado -- e mostra que o filtro que sobrou lidera em ambas.
    out = []
    for teste in testes:
        tag, kw = teste[0], teste[1]
        # artefato = linha publicada para mostrar um erro de metodo, nao um
        # candidato. Nao entra na conta de "melhor de N tentativas".
        artefato = len(teste) > 2 and teste[2]
        linha = dict(filtro=tag, horario=('horas' in kw),
                     esforco=('esf_max' in kw), poucas=False,
                     artefato=bool(artefato))
        for metrica, base in (('r1', NEUTRA), ('meio', MEIO)):
            cfg = E.Config(**dict(base, **kw))
            t = E.rodar(d, cfg)
            t = t[t.ativou]
            n = len(t)
            if n < 40:
                linha['poucas'] = True
                linha[metrica] = dict(n=int(n), acerto=0.0, z=0.0,
                                      expectativa_ticks=0.0)
                continue
            p = float((t.ticks > 0).mean())
            linha[metrica] = dict(
                n=int(n), acerto=p,
                z=float((p - 0.5) / math.sqrt(0.25 / n)),
                expectativa_ticks=float(t.ticks.mean()))
        # o ranking do relatorio usa o meio range: e a medida sem ambiguidade
        linha.update(n=linha['meio']['n'], acerto=linha['meio']['acerto'],
                     z=linha['meio']['z'],
                     expectativa_ticks=linha['meio']['expectativa_ticks'])
        out.append(linha)
    return out


def valida_horario(d):
    """Escolhe as horas em uma metade e testa na outra, nos dois sentidos."""
    cfg = E.Config(**MEIO)
    t = E.rodar(d, cfg)
    t = t[t.ativou].copy()
    t['win'] = (t.ticks > 0).astype(int)
    meio = len(d) // 2
    A, B = t[t.sinal_i < meio], t[t.sinal_i >= meio]

    def escolhe(tr):
        g = tr.groupby('hora').agg(n=('win', 'size'), p=('win', 'mean'))
        return sorted(int(x) for x in g[(g.n >= 25) & (g.p > 0.53)].index)

    def mede(te, hs):
        sub = te[te.hora.isin(hs)]
        n = len(sub)
        p = float(sub.win.mean()) if n else 0.0
        return dict(n=int(n), acerto=p,
                    z=float((p - 0.5) / math.sqrt(0.25 / n)) if n else 0.0,
                    expectativa_ticks=float(sub.ticks.mean()) if n else 0.0,
                    acerto_referencia=float(te.win.mean()),
                    n_referencia=int(len(te)))

    hA, hB = escolhe(A), escolhe(B)
    tabela = t.groupby('hora').agg(n=('win', 'size'), acerto=('win', 'mean'),
                                   exp=('ticks', 'mean'))
    return dict(
        escolhe_1a_testa_2a=dict(horas=hA, **mede(B, hA)),
        escolhe_2a_testa_1a=dict(horas=hB, **mede(A, hB)),
        intersecao=sorted(set(hA) & set(hB)),
        publicadas=list(HORAS_BOAS),
        aprovado=False,
        por_hora=[dict(hora=int(k), n=int(v.n), acerto=float(v.acerto),
                       expectativa_ticks=float(v.exp))
                  for k, v in tabela.iterrows()],
    )


def valida_esforco(d):
    """A mesma disciplina aplicada ao filtro que sobreviveu.

    Um filtro escolhido no melhor de 30 tentativas so merece credito se for
    PLATO (e nao pico), se aparecer nos dois pedacos da amostra separadamente,
    e se o controle invertido for o espelho dele. As tres coisas sao medidas
    aqui, e as tres saem publicadas, boas ou ruins.
    """
    meio, terco = len(d) // 2, len(d) // 3

    def corre(**kw):
        t = E.rodar(d, E.Config(**dict(MEIO, **kw)))
        return t[t.ativou]

    def stat(t):
        n = len(t)
        if not n:
            return dict(n=0, acerto=0.0, z=0.0, expectativa_ticks=0.0)
        p = float((t.ticks > 0).mean())
        return dict(n=int(n), acerto=p,
                    z=float((p - 0.5) / math.sqrt(0.25 / n)),
                    expectativa_ticks=float(t.ticks.mean()))

    plato = [dict(limite=lim, **stat(corre(esf_max=lim)))
             for lim in (0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 1.0, 1.1, 1.2)]

    t = corre(esf_max=ESF_MAX)
    metades = {nm: stat(t[(t.sinal_i >= lo) & (t.sinal_i < hi)])
               for nm, lo, hi in (('1a', 0, meio), ('2a', meio, len(d)))}
    tercos = [dict(terco=k + 1, **stat(t[(t.sinal_i >= k * terco) &
                                         (t.sinal_i < (k + 1) * terco)]))
              for k in range(3)]
    por_hora = t.groupby('hora').agg(n=('ticks', 'size'),
                                     acerto=('ticks', lambda s: float((s > 0).mean())))
    frac_hora = d[d.sinal != 0].groupby('hora').apply(
        lambda x: float((x.esf_rel <= ESF_MAX).mean()), include_groups=False)

    return dict(
        limite=ESF_MAX,
        plato=plato, metades=metades, tercos=tercos,
        invertido=stat(corre(esf_max=ESF_MAX, inverter=True)),
        por_tipo={str(tp): stat(t[t.tipo == tp]) for tp in (1, 2)},
        por_lado={ld: stat(t[t.lado == ld]) for ld in ('long', 'short')},
        # o filtro e um disfarce de horario? se fosse, a fracao filtrada se
        # concentraria em poucas horas e a vantagem sumiria dentro delas
        por_hora=[dict(hora=int(k), n=int(v.n), acerto=float(v.acerto))
                  for k, v in por_hora.iterrows() if v.n >= 15],
        fracao_por_hora={str(int(k)): float(v) for k, v in frac_hora.items()},
    )


def sensibilidade_indicador(df):
    """Varre os PROPRIOS parametros do indicador.

    Um gatilho cujo resultado desaba quando o parametro anda 10% nao foi
    medido: foi ajustado. Cada varredura recalcula o indicador do zero e mede
    com a gestao neutra 1:1, com e sem o filtro de esforco.
    """
    campos = [
        ('periodo_base', 'barras da janela de referência',
         [20, 30, 40, 60, 80, 100, 140]),
        ('fator_res', 'teto de resultado relativo (absorção)',
         [0.5, 0.6, 0.7, 0.8, 0.9]),
        ('fator_qual', 'teto de agressão a favor (absorção)',
         [0.2, 0.35, 0.5, 0.65, 0.8]),
        ('fator_corpo', 'corpo mínimo no pivô (divergência)',
         [0.6, 0.7, 0.8, 0.9]),
        ('lim_desq', 'desequilíbrio mínimo do delta (divergência)',
         [0.02, 0.05, 0.10, 0.20]),
        ('fator_completa', 'fração do range para a barra contar',
         [0.5, 0.7, 0.9, 0.98]),
    ]
    out = []
    for campo, rotulo, valores in campos:
        linhas = []
        for v in valores:
            ind = E.Ind(**{**E.Ind().__dict__, campo: v})
            d = E.esforco_resultado(df, ind)
            linha = dict(valor=v, padrao=(v == getattr(E.Ind(), campo)),
                         sinais=int((d.sinal != 0).sum()))
            for tag, kw in (('todos', {}), ('esforco_baixo', dict(esf_max=ESF_MAX))):
                t = E.rodar(d, E.Config(**dict(MEIO, **kw)))
                t = t[t.ativou]
                n = len(t)
                p = float((t.ticks > 0).mean()) if n else 0.0
                linha[tag] = dict(
                    n=int(n), acerto=p,
                    z=float((p - 0.5) / math.sqrt(0.25 / n)) if n >= 20 else 0.0,
                    expectativa_ticks=float(t.ticks.mean()) if n else 0.0)
            linhas.append(linha)
        out.append(dict(campo=campo, rotulo=rotulo, linhas=linhas))
    return out


def gestao(d):
    """Varre a gestao, com a selecao da V7 fixa. O gatilho ja esta decidido
    aqui: o que se mede e ate onde vale segurar."""
    def sim(frac):
        return dict(stop_ticks=frac * RNG, parcial_frac=1.0,
                    parcial_ticks=frac * RNG, alvo_ticks=frac * RNG)

    out = []
    for rot, kw in (
            ('1:1 a 1/4 do range (97 t)', sim(0.25)),
            ('1:1 a MEIO RANGE (194 t)', sim(0.5)),
            ('1:1 a 3/4 do range (291 t)', sim(0.75)),
            ('1:1 a um range (388 t = 1R)', sim(1.0)),
            ('1:1 a dois ranges (776 t)', sim(2.0)),
            ('stop 1R, alvo 1,5R', dict(stop_ticks=RNG, parcial_frac=1.0,
                                        parcial_ticks=1.5 * RNG,
                                        alvo_ticks=1.5 * RNG)),
            ('stop 1R, alvo 2R', dict(stop_ticks=RNG, parcial_frac=1.0,
                                      parcial_ticks=2 * RNG,
                                      alvo_ticks=2 * RNG)),
            ('stop 1R, parcial em 1R, runner até 2R',
             dict(stop_ticks=RNG, parcial_frac=0.5, parcial_ticks=RNG,
                  alvo_ticks=2 * RNG)),
            ('stop 1R, parcial em 1R, runner até 3R',
             dict(stop_ticks=RNG, parcial_frac=0.5, parcial_ticks=RNG,
                  alvo_ticks=3 * RNG)),
            ('meio range, saída forçada em 5 barras',
             dict(max_barras=5, **sim(0.5))),
    ):
        cfg = E.Config(esf_max=ESF_MAX, **kw)
        t = E.rodar(d, cfg)
        s = E.estatisticas(t, cfg)
        otim = E.estatisticas(E.rodar(d, E.com(cfg, ordem_intrabar='otimista')), cfg)
        exp_p = s.get('expectativa_ticks', 0)
        exp_o = otim.get('expectativa_ticks', 0)
        out.append(dict(
            rotulo=rot, stop_ticks=cfg.stop_ticks, alvo_ticks=cfg.alvo_ticks,
            parcial_frac=cfg.parcial_frac,
            expectativa_otimista=exp_o,
            # a gestao onde as duas hipoteses coincidem e a que nao depende de
            # suposicao nenhuma sobre a ordem dos toques dentro da barra
            sem_ambiguidade=bool(abs(exp_o - exp_p) < 1e-9),
            **{k: s.get(k, 0) for k in
               ('operacoes', 'acerto', 'expectativa_ticks', 'expectativa_R',
                'erro_padrao_ticks', 't_stat', 'ticks_total', 'fator_lucro',
                'drawdown_ticks', 'barras_media')}))
    return out


def curva(t):
    a = t[t.ativou]
    if not len(a):
        return []
    cum = a.ticks.cumsum().to_numpy()
    return [[str(pd.Timestamp(x).date()), round(float(y), 1)]
            for x, y in zip(a.dt.to_numpy(), cum)]


def por_hora(t):
    a = t[t.ativou]
    if not len(a):
        return []
    g = a.groupby('hora').agg(n=('ticks', 'size'), soma=('ticks', 'sum'),
                              exp=('ticks', 'mean'),
                              acerto=('ticks', lambda s: float((s > 0).mean())))
    return [dict(hora=int(k), n=int(v.n), ticks=float(v.soma),
                 expectativa_ticks=float(v.exp), acerto=float(v.acerto))
            for k, v in g.iterrows()]


def trades_json(t, limite=400):
    """Operacoes para o grafico. Guarda so o que o desenho precisa."""
    a = t[t.ativou].copy()
    if len(a) > limite:                       # amostra regular, sem escolher
        a = a.iloc[np.linspace(0, len(a) - 1, limite).astype(int)]
    cols = ['sinal_i', 'saida_i', 'lado', 'tipo', 'preco_ordem', 'entrada',
            'motivo', 'ticks', 'barras', 'hora', 'res_rel', 'qual_rel',
            'esf_rel', 'efic', 'contra', 'parcial']
    out = []
    for _, r in a.iterrows():
        out.append([int(r.sinal_i), int(r.saida_i), r.lado, int(r.tipo),
                    round(float(r.preco_ordem), 2), round(float(r.entrada), 2),
                    r.motivo, round(float(r.ticks), 1), int(r.barras),
                    int(r.hora), round(float(r.res_rel), 2),
                    round(float(r.qual_rel), 2), round(float(r.esf_rel), 2),
                    round(float(r.efic), 2), int(r.contra), bool(r.parcial)])
    return dict(colunas=cols, linhas=out, total=int(len(t[t.ativou])))


def barras_json(d):
    """OHLC + agressao comprimidos: close em ticks inteiros, o/h/l como desvio
    do close, tempo como delta em segundos. A agressao vai inteira porque e ela
    que o painel de baixo desenha -- e o indicador nao existe sem ela."""
    c = np.round(d.close.to_numpy() / TICK).astype(np.int64)
    o = np.round(d.open.to_numpy() / TICK).astype(np.int64) - c
    h = np.round(d.high.to_numpy() / TICK).astype(np.int64) - c
    l = np.round(d.low.to_numpy() / TICK).astype(np.int64) - c
    # segundos desde a epoca. Nao usar astype('int64'): a unidade do datetime64
    # muda entre versoes do pandas (ns em 2.x, us em 3.x).
    ts = (d.dt - pd.Timestamp('1970-01-01')).dt.total_seconds() \
        .to_numpy().astype('int64')
    s = d.sinal.to_numpy()
    marcas = [[int(i), int(s[i])] for i in np.where(s != 0)[0]]
    return dict(t0=int(ts[0]), dt=np.diff(ts, prepend=ts[0]).tolist(),
                c=c.tolist(), o=o.tolist(), h=h.tolist(), l=l.tolist(),
                cv=d.tickvol.to_numpy().astype(int).tolist(),
                vv=d.vol.to_numpy().astype(int).tolist(),
                sinais=marcas)


# --------------------------------------------------------------------------
def principal():
    os.makedirs(SAIDA, exist_ok=True)
    print('lendo', os.path.basename(E.ARQUIVO))
    bruto = E.carregar()
    d = E.esforco_resultado(bruto)
    print('%d barras, %s a %s' % (len(d), d.dt.iloc[0], d.dt.iloc[-1]))

    prem = E.conferir_premissa(d)
    print('premissa: range mediano %.0f t, %.1f%% das barras dentro de +-10%%; '
          'agressao vendedora presente em %.1f%% das barras'
          % (prem['range_mediana'], 100 * prem['range_dentro_10pct'],
             100 * (1 - prem['pct_vol_zero'])))
    if not prem['e_range'] or not prem['tem_agressao']:
        print('  ATENCAO: a premissa do indicador NAO se confirma neste arquivo.')

    res = dict(gerado_em=datetime.now().strftime('%Y-%m-%d %H:%M'),
               arquivo=os.path.basename(E.ARQUIVO),
               tick=TICK, range_nominal=RNG,
               horas_boas=list(HORAS_BOAS), esf_max=ESF_MAX,
               dados=descr_dados(d))

    print('\n--- o que o gatilho produz ---')
    res['indicador'] = descr_indicador(d)
    I = res['indicador']
    print('  %d sinais em %d barras (%.1f%%): absorcao %d, divergencia %d'
          % (I['total'], len(d), 100 * I['pct_barras'],
             I['absorcao_alta'] + I['absorcao_baixa'],
             I['divergencia_alta'] + I['divergencia_baixa']))
    print('  %.1f sinais por pregao, um a cada %.0f barras'
          % (I['sinais_por_dia'], I['barras_entre_sinais']))

    print('\n--- excursao pura depois do sinal (sem regra de saida) ---')
    res['excursao'] = excursao(d)
    for k in ('sinal', 'direcao_sorteada', 'barra_e_direcao_sorteadas',
              'esforco_baixo'):
        b = res['excursao'][k]['20']
        print('  %-28s H20  MFE %4.0f  MAE %4.0f  razao %.3f  deriva %+6.1f (t %+.2f)'
              % (k, b['mfe_med'], b['mae_med'], b['razao'], b['deriva_media'],
                 b['deriva_t']))

    print('\n--- linha de base: o proprio grafico ja tem inclinacao? ---')
    res['linha_base'] = linha_base(d)
    for g in res['linha_base']['grupos']:
        print('  %-24s n %6d  continua %5.2f%%  z %+5.2f'
              % (g['grupo'], g['n'], 100 * g['acerto'], g['z']))
    gh = res['linha_base']['ganho']
    print('  o indicador acrescenta %+.1f pontos sobre o controle emparelhado '
          '(z %+.2f)' % (100 * gh['diferenca'], gh['z']))

    print('\n--- busca por filtro (metrica neutra, meio range) ---')
    res['busca'] = busca(d)
    cands = [b for b in res['busca'] if not b['artefato']]
    for b in sorted(cands, key=lambda x: -x['z'])[:8]:
        print('  %-38s n %5d  acerto %5.1f%%  z %+5.2f  (1R: z %+5.2f)'
              % (b['filtro'], b['n'], 100 * b['acerto'], b['z'], b['r1']['z']))
    validos = [b for b in cands if not b['poucas']]
    print('  ... %d filtros testados; o maior z tem de ser lido como o maximo '
          'de %d tentativas' % (len(validos), len(validos)))

    print('\n--- validacao cruzada do horario ---')
    res['horario'] = valida_horario(d)
    for k in ('escolhe_1a_testa_2a', 'escolhe_2a_testa_1a'):
        v = res['horario'][k]
        print('  %-20s horas %s -> n %d  acerto %.1f%% (referencia %.1f%%)  z %+.2f'
              % (k, v['horas'], v['n'], 100 * v['acerto'],
                 100 * v['acerto_referencia'], v['z']))
    print('  horas em comum: %s  -> o filtro de horario NAO se confirma'
          % res['horario']['intersecao'])

    print('\n--- validacao do filtro de esforco ---')
    res['esforco'] = valida_esforco(d)
    Ef = res['esforco']
    print('  plato:', '  '.join('%.2f:%.1f%%' % (p['limite'], 100 * p['acerto'])
                                for p in Ef['plato']))
    for nm in ('1a', '2a'):
        v = Ef['metades'][nm]
        print('  metade %s  n %4d  acerto %.1f%%  z %+.2f  exp %+.1f t'
              % (nm, v['n'], 100 * v['acerto'], v['z'], v['expectativa_ticks']))
    for v in Ef['tercos']:
        print('  terco %d   n %4d  acerto %.1f%%  z %+.2f  exp %+.1f t'
              % (v['terco'], v['n'], 100 * v['acerto'], v['z'],
                 v['expectativa_ticks']))
    print('  controle invertido: acerto %.1f%%  exp %+.1f t'
          % (100 * Ef['invertido']['acerto'], Ef['invertido']['expectativa_ticks']))

    print('\n--- sensibilidade aos parametros do PROPRIO indicador ---')
    res['sensibilidade'] = sensibilidade_indicador(bruto)
    for g in res['sensibilidade']:
        celulas = '  '.join('%s%s:%.1f%%%s' % (
            g['campo'][:0], ln['valor'], 100 * ln['esforco_baixo']['acerto'],
            '*' if ln['padrao'] else '') for ln in g['linhas'])
        print('  %-16s %s' % (g['campo'], celulas))

    print('\n--- gestao (selecao do esforco baixo fixa) ---')
    res['gestao'] = gestao(d)
    for g in res['gestao']:
        print('  %-38s n %4d  acerto %5.1f%%  exp %+7.1f t = %+.3fR  (t %+.2f)%s'
              % (g['rotulo'], g['operacoes'], 100 * g['acerto'],
                 g['expectativa_ticks'], g['expectativa_R'], g['t_stat'],
                 '  <- sem ambiguidade' if g['sem_ambiguidade'] else ''))

    print('\n--- variantes ---')
    print('  %-4s %-34s %5s %5s %7s %8s %9s %6s %8s' %
          ('', 'variante', 'sin', 'ops', 'acerto', 'exp/op', 'total', 'FL', 'DD'))
    res['variantes'] = []
    for cfg, desc in variantes():
        t = E.rodar(d, cfg)
        s = E.estatisticas(t, cfg)
        t.to_csv(os.path.join(SAIDA, 'trades_%s.csv' % cfg.nome),
                 index=False, sep=';', decimal=',')

        otim = E.estatisticas(E.rodar(d, E.com(cfg, ordem_intrabar='otimista')), cfg)
        custo = {}
        for cst in CUSTOS:
            cc = E.com(cfg, custo_ticks=cst)
            custo[str(cst)] = E.estatisticas(E.rodar(d, cc), cc)

        meio = len(d) // 2
        metades = {}
        for nm, lo, hi in (('1a', 0, meio), ('2a', meio, len(d))):
            sub = t[(t.sinal_i >= lo) & (t.sinal_i < hi)]
            metades[nm] = E.estatisticas(sub, cfg)

        res['variantes'].append(dict(
            nome=cfg.nome, rotulo=cfg.rotulo, descricao=desc,
            cfg=E.resumo_cfg(cfg), stats=s, stats_otimista=otim,
            custo=custo, metades=metades, curva=curva(t),
            por_hora=por_hora(t), trades=trades_json(t)))
        print('  %-4s %-34s %5d %5d %6.1f%% %+8.1f %+9.0f %6.2f %+8.0f' %
              (cfg.nome, cfg.rotulo, s.get('sinais', 0), s.get('operacoes', 0),
               100 * s.get('acerto', 0), s.get('expectativa_ticks', 0),
               s.get('ticks_total', 0), s.get('fator_lucro', 0),
               s.get('drawdown_ticks', 0)))

    with open(os.path.join(SAIDA, 'resumo.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(SAIDA, 'barras.json'), 'w', encoding='utf-8') as f:
        json.dump(barras_json(d), f, separators=(',', ':'))
    print('\nsaida/resumo.json e saida/barras.json gravados.')


if __name__ == '__main__':
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        principal()
    texto = buf.getvalue()
    print(texto, end='')
    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(SAIDA, 'console.txt'), 'w', encoding='utf-8') as f:
        f.write(texto)
