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
    saida/barras.json     OHLC comprimido, para os graficos do relatorio
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

# horas (do relogio do arquivo) que sobreviveram a validacao cruzada:
# escolhidas em cada metade da amostra, testadas na outra
HORAS_BOAS = (5, 6, 12, 13, 16, 18)

CUSTOS = (0, 10, 20, 40)     # ticks de ida+volta testados na sensibilidade


# --------------------------------------------------------------------------
# variantes publicadas
# --------------------------------------------------------------------------
def variantes():
    H = HORAS_BOAS
    return [
        (E.Config(nome='V0', rotulo='regra literal'),
         'A regra exatamente como está escrita em ESTRATEGIA.md: leque de EMAs '
         '21/42/72 ordenado, afastamento e volta ao leque, pullback de 2 ou 3 '
         'candles da mesma cor, candle contrário como gatilho, ordem limitada '
         'no meio do range válida por uma barra, stop de 300 ticks, parcial de '
         '50% em 300 com stop no breakeven, saída final em 900.'),

        (E.Config(nome='V1', rotulo='leque aberto', leque_min=400),
         'Acrescenta a restrição que a própria estratégia sugere: só operar '
         'quando as médias NÃO estão emboladas. "Embolado" vira um número — a '
         'distância entre a EMA21 e a EMA72 tem de ser de pelo menos 400 ticks '
         '(4 dólares) na barra do gatilho.'),

        (E.Config(nome='V2', rotulo='teto de range no gatilho', range_max=350),
         'Acrescenta a segunda restrição sugerida: o candle de reversão não '
         'pode ser grande demais para um stop fixo de 300 ticks. Teto de 350 '
         'ticks de range, pouco acima da mediana do ativo (277).'),

        (E.Config(nome='V3', rotulo='gatilho com reconquista', fecha_alem=True),
         'Exige que o candle de gatilho não apenas toque o leque, mas FECHE de '
         'volta além da EMA21, no sentido da tendência. É a versão mais '
         'exigente de "aparece um candle contrário no leque".'),

        (E.Config(nome='V4', rotulo='só nas horas boas', horas=H),
         'Aplica a terceira sugestão da estratégia: segregação por horário. As '
         'horas foram escolhidas por validação cruzada — selecionadas em uma '
         'metade da amostra e testadas na outra, nos dois sentidos.'),

        (E.Config(nome='V5', rotulo='recomendada (horário + reconquista)',
                  horas=H, fecha_alem=True),
         'A combinação dos dois filtros que mediram melhor — horário e '
         'reconquista da EMA21 no fechamento do gatilho — mantendo a gestão '
         'original de parcial mais runner até 900.'),

        (E.Config(nome='V6', rotulo='1:1, sem runner', horas=H,
                  parcial_frac=1.0, parcial_ticks=300, alvo_ticks=300),
         'Mesma entrada da V4, gestão diferente: a posição inteira sai em 300 '
         'ticks, sem parcial e sem runner. Serve de medida limpa da DIREÇÃO do '
         'sinal, sem a distorção do alvo distante.'),

        (E.Config(nome='V7', rotulo='a que mediu melhor (V5 sem runner)',
                  horas=H, fecha_alem=True,
                  parcial_frac=1.0, parcial_ticks=300, alvo_ticks=300),
         'A entrada da V5 com a gestão da V6: horário, reconquista da EMA21, e '
         'a posição inteira saindo em +300 ticks. Foi a configuração de melhor '
         'expectativa e a única que continua positiva com 40 ticks de custo. É '
         'a que o PLANO.md usa como plano principal.'),

        (E.Config(nome='V8', rotulo='controle: lado invertido', inverter=True),
         'Controle estatístico. Mesma detecção de gatilho, mas operando o lado '
         'OPOSTO. Se a estratégia tivesse leitura de direção, esta variante '
         'teria de ser o espelho negativo da V0.'),
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
                     rng.describe(percentiles=[.1, .25, .5, .75, .9, .95, .99]).items()},
        segundos_por_barra={k: float(v) for k, v in
                            dif.describe(percentiles=[.5, .9]).items() if k != 'count'},
        preco_min=float(d.low.min()), preco_max=float(d.high.max()),
        leque_ticks={k: float(np.percentile(d.leque, k)) for k in (10, 25, 50, 75, 90)},
        pct_leque_alta=float(d.up.mean()), pct_leque_baixa=float(d.dn.mean()),
        pct_embolado=float(1 - d.up.mean() - d.dn.mean()),
        horas=[int(h) for h in sorted(d.hora.unique())],
        barras_por_hora={str(int(k)): int(v) for k, v in d.groupby('hora').size().items()},
    )


def excursao(d, cfg):
    """MFE/MAE/deriva depois da entrada, sem nenhuma regra de saida, contra
    dois controles aleatorios. E o teste de existencia da vantagem."""
    h, l, c, o = (d[k].to_numpy() for k in ('high', 'low', 'close', 'open'))
    n = len(d)
    sl, ss = E.sinais(d, cfg)
    idx = np.where(sl | ss)[0]
    sig = np.where(sl[idx], 1, -1)
    rng = np.random.default_rng(20260902)

    def medir(ii, ss_, H):
        mfe, mae, dr = [], [], []
        for i, s in zip(ii, ss_):
            j = i + 1
            if j + H >= n:
                continue
            ent = (h[i] + l[i]) / 2
            if (s > 0 and l[j] > ent) or (s < 0 and h[j] < ent):
                continue
            ent = min(ent, o[j]) if s > 0 else max(ent, o[j])
            hi, lo = h[j:j + H].max(), l[j:j + H].min()
            mfe.append((hi - ent) / TICK if s > 0 else (ent - lo) / TICK)
            mae.append((ent - lo) / TICK if s > 0 else (hi - ent) / TICK)
            dr.append(s * (c[j + H - 1] - ent) / TICK)
        return np.array(mfe), np.array(mae), np.array(dr)

    def bloco(ii, ss_):
        out = {}
        for H in (5, 10, 20, 40, 80):
            mfe, mae, dr = medir(ii, ss_, H)
            out[str(H)] = dict(n=int(len(mfe)),
                               mfe_med=float(np.median(mfe)),
                               mae_med=float(np.median(mae)),
                               razao=float(np.median(mfe) / np.median(mae)),
                               deriva_med=float(np.median(dr)),
                               deriva_media=float(dr.mean()))
        return out

    ri = rng.choice(np.arange(80, n - 100), size=len(idx), replace=False)
    return dict(
        sinal=bloco(idx, sig),
        direcao_sorteada=bloco(idx, rng.choice([-1, 1], size=len(idx))),
        barra_e_direcao_sorteadas=bloco(ri, rng.choice([-1, 1], size=len(ri))),
    )


def busca(d):
    """Toda a busca por filtro que foi feita, com o z de cada tentativa.
    Publicar a lista inteira e o que permite ler o melhor z como o maximo de
    N tentativas, e nao como uma descoberta."""
    NEU = dict(parcial_frac=1.0, parcial_ticks=300, alvo_ticks=300)
    testes = [
        ('regra literal, sem filtro nenhum', {}),
        ('gatilho fecha além da EMA21 (reconquista)', dict(fecha_alem=True)),
        ('gatilho toca a EMA21 mas não fura a EMA72', dict(exige_dentro=True)),
        ('corpo do gatilho >= 50% do range', dict(corpo_min=0.5)),
        ('corpo do gatilho >= 60% do range', dict(corpo_min=0.6)),
        ('pullback de exatamente 2 candles', dict(pull_min=2, pull_max=2)),
        ('pullback de exatamente 3 candles', dict(pull_min=3, pull_max=3)),
        ('pullback de 4 a 6 candles', dict(pull_min=4, pull_max=6)),
        ('EMA21 avança 30t ou mais em 10 barras', dict(inclin_min=30)),
        ('EMA21 avança 60t ou mais em 10 barras', dict(inclin_min=60)),
        ('EMA21 avança 100t ou mais em 10 barras', dict(inclin_min=100)),
        ('EMA21 avança 150t ou mais em 10 barras', dict(inclin_min=150)),
        ('afastamento prévio >= 100t', dict(afast_min=100)),
        ('afastamento prévio >= 200t', dict(afast_min=200)),
        ('afastamento prévio >= 300t', dict(afast_min=300)),
        ('afastamento prévio >= 400t', dict(afast_min=400)),
        ('leque >= 200t', dict(leque_min=200)),
        ('leque >= 300t', dict(leque_min=300)),
        ('leque >= 400t', dict(leque_min=400)),
        ('leque <= 300t (médias emboladas)', dict(leque_max=300)),
        ('leque entre 150t e 600t', dict(leque_min=150, leque_max=600)),
        ('range do gatilho <= 250t', dict(range_max=250)),
        ('range do gatilho <= 350t', dict(range_max=350)),
        ('range do gatilho >= 250t', dict(range_min=250)),
        ('range do gatilho >= 350t', dict(range_min=350)),
        ('só operações de compra', dict(lados=('long',))),
        ('só operações de venda', dict(lados=('short',))),
        ('reconquista + corpo 50% + sem furar a EMA72',
         dict(fecha_alem=True, corpo_min=0.5, exige_dentro=True)),
        ('reconquista + inclinação 100t + afastamento 200t',
         dict(fecha_alem=True, inclin_min=100, afast_min=200)),
        ('inclinação 150t + leque 300t + afastamento 300t',
         dict(inclin_min=150, leque_min=300, afast_min=300)),
        ('só nas horas selecionadas', dict(horas=HORAS_BOAS)),
    ]
    out = []
    for tag, kw in testes:
        cfg = E.Config(**dict(NEU, **kw))
        t = E.rodar(d, cfg)
        t = t[t.ativou]
        n = len(t)
        if n < 40:
            continue
        p = float((t.ticks > 0).mean())
        z = (p - 0.5) / math.sqrt(0.25 / n)
        out.append(dict(filtro=tag, n=int(n), acerto=p, z=float(z),
                        expectativa_ticks=float(t.ticks.mean()),
                        horario=('horas' in kw)))
    return out


def valida_horario(d):
    """Escolhe as horas em uma metade e testa na outra, nos dois sentidos."""
    cfg = E.Config(parcial_frac=1.0, parcial_ticks=300, alvo_ticks=300)
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
                    acerto_referencia=float(te.win.mean()), n_referencia=int(len(te)))

    hA, hB = escolhe(A), escolhe(B)
    tabela = t.groupby('hora').agg(n=('win', 'size'), acerto=('win', 'mean'),
                                   exp=('ticks', 'mean'))
    return dict(
        escolhe_1a_testa_2a=dict(horas=hA, **mede(B, hA)),
        escolhe_2a_testa_1a=dict(horas=hB, **mede(A, hB)),
        intersecao=sorted(set(hA) & set(hB)),
        publicadas=list(HORAS_BOAS),
        por_hora=[dict(hora=int(k), n=int(v.n), acerto=float(v.acerto),
                       expectativa_ticks=float(v.exp))
                  for k, v in tabela.iterrows()],
    )


def curva(t, cfg):
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
    cols = ['sinal_i', 'saida_i', 'lado', 'preco_ordem', 'entrada', 'motivo',
            'ticks', 'barras', 'hora', 'leque', 'range_gatilho', 'parcial']
    out = []
    for _, r in a.iterrows():
        out.append([int(r.sinal_i), int(r.saida_i), r.lado,
                    round(float(r.preco_ordem), 2), round(float(r.entrada), 2),
                    r.motivo, round(float(r.ticks), 1), int(r.barras),
                    int(r.hora), round(float(r.leque)), round(float(r.range_gatilho)),
                    bool(r.parcial)])
    return dict(colunas=cols, linhas=out, total=int(len(t[t.ativou])))


def barras_json(d):
    """OHLC comprimido: close em ticks inteiros, o/h/l como desvio do close,
    tempo como delta em segundos. As EMAs o navegador recalcula."""
    c = np.round(d.close.to_numpy() / TICK).astype(np.int64)
    o = np.round(d.open.to_numpy() / TICK).astype(np.int64) - c
    h = np.round(d.high.to_numpy() / TICK).astype(np.int64) - c
    l = np.round(d.low.to_numpy() / TICK).astype(np.int64) - c
    # segundos desde a epoca. Nao usar astype('int64'): a unidade do
    # datetime64 muda entre versoes do pandas (ns em 2.x, us em 3.x).
    ts = (d.dt - pd.Timestamp('1970-01-01')).dt.total_seconds() \
        .to_numpy().astype('int64')
    return dict(t0=int(ts[0]), dt=np.diff(ts, prepend=ts[0]).tolist(),
                c=c.tolist(), o=o.tolist(), h=h.tolist(), l=l.tolist())


# --------------------------------------------------------------------------
def principal():
    os.makedirs(SAIDA, exist_ok=True)
    print('lendo', os.path.basename(E.ARQUIVO))
    d = E.indicadores(E.carregar())
    print('%d barras, %s a %s' % (len(d), d.dt.iloc[0], d.dt.iloc[-1]))

    res = dict(gerado_em=datetime.now().strftime('%Y-%m-%d %H:%M'),
               arquivo=os.path.basename(E.ARQUIVO),
               tick=TICK, horas_boas=list(HORAS_BOAS),
               dados=descr_dados(d))

    print('\n--- excursao pura depois da entrada (sem regra de saida) ---')
    res['excursao'] = excursao(d, E.Config())
    for k in ('sinal', 'direcao_sorteada', 'barra_e_direcao_sorteadas'):
        b = res['excursao'][k]['20']
        print('  %-28s H20  MFE %4.0f  MAE %4.0f  razao %.3f  deriva %+5.1f'
              % (k, b['mfe_med'], b['mae_med'], b['razao'], b['deriva_media']))

    print('\n--- busca por filtro (metrica neutra 1:1) ---')
    res['busca'] = busca(d)
    for b in sorted(res['busca'], key=lambda x: -x['z'])[:8]:
        print('  %-38s n %5d  acerto %5.1f%%  z %+5.2f'
              % (b['filtro'], b['n'], 100 * b['acerto'], b['z']))
    zmax = max(abs(b['z']) for b in res['busca'] if not b['horario'])
    print('  ... %d filtros testados; maior |z| fora do horario: %.2f'
          % (len(res['busca']), zmax))

    print('\n--- validacao cruzada do horario ---')
    res['horario'] = valida_horario(d)
    for k in ('escolhe_1a_testa_2a', 'escolhe_2a_testa_1a'):
        v = res['horario'][k]
        print('  %-20s horas %s -> n %d  acerto %.1f%% (referencia %.1f%%)  z %+.2f'
              % (k, v['horas'], v['n'], 100 * v['acerto'],
                 100 * v['acerto_referencia'], v['z']))
    print('  horas em comum:', res['horario']['intersecao'])

    print('\n--- variantes ---')
    print('  %-4s %-34s %5s %5s %7s %8s %9s %6s %8s' %
          ('', 'variante', 'sin', 'ops', 'acerto', 'exp/op', 'total', 'FL', 'DD'))
    res['variantes'] = []
    for cfg, desc in variantes():
        t = E.rodar(d, cfg)
        s = E.estatisticas(t, cfg)
        t.to_csv(os.path.join(SAIDA, 'trades_%s.csv' % cfg.nome),
                 index=False, sep=';', decimal=',')

        otim = E.estatisticas(E.rodar(d, E.Config(**dict(E.resumo_cfg(cfg),
                              ordem_intrabar='otimista',
                              horas=cfg.horas, lados=cfg.lados))), cfg)
        custo = {}
        for cst in CUSTOS:
            cc = E.Config(**dict(E.resumo_cfg(cfg), custo_ticks=cst,
                                 horas=cfg.horas, lados=cfg.lados))
            custo[str(cst)] = E.estatisticas(E.rodar(d, cc), cc)

        meio = len(d) // 2
        metades = {}
        for nm, lo, hi in (('1a', 0, meio), ('2a', meio, len(d))):
            sub = t[(t.sinal_i >= lo) & (t.sinal_i < hi)]
            metades[nm] = E.estatisticas(sub, cfg)

        res['variantes'].append(dict(
            nome=cfg.nome, rotulo=cfg.rotulo, descricao=desc,
            cfg=E.resumo_cfg(cfg), stats=s, stats_otimista=otim,
            custo=custo, metades=metades, curva=curva(t, cfg),
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
