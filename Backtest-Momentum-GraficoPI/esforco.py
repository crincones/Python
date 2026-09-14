# -*- coding: utf-8 -*-
"""
ESFORCO x RESULTADO no grafico de 20 PI.

A ideia e de Wyckoff e vem do grafico de ticks: compara-se quanto foi
GASTO (volume, negocios, tempo) com quanto o preco ANDOU. Volume alto com
pouco resultado e absorcao; volume baixo com muito resultado e caminho
livre.

-------------------------------------------------- o que o PI muda na conta
Num grafico de ticks o resultado varia, e por isso e preciso dividir. Num
grafico de 20 PI **o resultado esta fixo por construcao**: todo corpo vale
exatamente 100 pontos. Entao

    esforco / resultado  =  esforco / 100  =  esforco, a menos de escala.

Ou seja, **o volume da barra JA E a razao esforco-resultado**, sem
normalizar nada. Isso simplifica, mas tambem avisa: parte do que se
esperaria ganhar aqui ja foi medida antes como `vol_cont` e `dur_cont`.

--------------------------------------------- o que JA ESTA na estrategia
A outra leitura de esforco-resultado -- resultado util sobre deslocamento
total, `100 / range` -- e **exatamente o filtro de pavio do Ouro**, escrito
ao contrario:

    range = 100 + pavio_total   =>   100/range = 1 / (1 + pavio/100)

que e monotonico em `pav_tot`. `engine.sinais()` ja devolve isso como
`corpo_r`. Entao a eficiencia GEOMETRICA nao e novidade: ela ja e o degrau
que separa Ouro de Prata, e e o unico pedaco da familia que mediu algo.

------------------------------------------------------- o que E novo aqui
Sobra o esforco medido em VOLUME, NEGOCIOS e TAMANHO DE NEGOCIO, e --
principalmente -- a comparacao do esforco ENTRE as duas barras do par.
Essa ultima e a forma mais fiel do conceito neste grafico: a retracao e a
continuacao produziram **o mesmo resultado** (100 pontos, cada uma para o
seu lado), entao a razao dos esforcos e uma comparacao limpa, com o
resultado controlado dos dois lados.

  ef_par_vol    volume da continuacao / volume da retracao
                > 1 = a CONTINUACAO custou mais volume que a retracao,
                      isto e, andar a favor saiu mais caro que andar contra
  ef_par_negs   idem, em numero de negocios
  ef_par_agr    idem, em volume agressor total
  ef_vol_rng    volume / range -- esforco por ponto PERCORRIDO (nao pelo
                resultado): mistura as duas leituras numa so
  tam_neg       volume / negocios: tamanho medio do negocio na barra
  tam_neg_r     tamanho medio na continuacao / na retracao
  ef_absoluta   volume da continuacao sobre a mediana das 50 anteriores
                (= vol_cont; entra so para a familia ficar completa)
  gasto_par     volume das duas barras sobre a mediana -- o custo do par
                inteiro para voltar ao ponto de partida (o par retracao +
                continuacao fecha com deslocamento liquido ZERO)
"""
import numpy as np
import pandas as pd

JAN = 50          # janela da mediana que normaliza o volume

# a familia, declarada ANTES de olhar -- e o que torna a peneira honesta
FAMILIA = ['ef_par_vol', 'ef_par_negs', 'ef_par_agr', 'ef_vol_rng',
           'tam_neg', 'tam_neg_r', 'ef_absoluta', 'gasto_par']

ROTULO = {
    'ef_par_vol': 'esforco do par, em volume',
    'ef_par_negs': 'esforco do par, em negocios',
    'ef_par_agr': 'esforco do par, em agressao',
    'ef_vol_rng': 'volume por ponto percorrido',
    'tam_neg': 'tamanho medio do negocio',
    'tam_neg_r': 'tamanho do negocio, continuacao / retracao',
    'ef_absoluta': 'volume da continuacao (x mediana)',
    'gasto_par': 'volume do par inteiro (x mediana)',
    'corpo_r': 'eficiencia geometrica (100/range) -- JA no Ouro',
    'pav_tot': 'pavio total -- JA no Ouro',
}


def anexa(sig, d, antecipado=False):
    """Acrescenta a familia esforco-resultado a tabela de sinais.

    Tudo medido ate a barra da decisao: no modo confirmado a continuacao e
    `i` e a retracao `i-1`; no antecipado a continuacao nao existe ainda e
    as colunas que dependem dela saem NaN.
    """
    sig = sig.copy()
    i = sig['i'].to_numpy(int)
    i_ret = i if antecipado else i - 1

    qtd = d['qtd'].to_numpy(float)
    negs = d['negs'].to_numpy(float)
    agr = (d['agr_c'] + d['agr_v']).to_numpy(float)
    h = d['h'].to_numpy(float)
    l = d['l'].to_numpy(float)

    medq = pd.Series(qtd).rolling(JAN, min_periods=10).median().to_numpy()

    def raz(a, b):
        with np.errstate(invalid='ignore', divide='ignore'):
            return np.where(b > 0, a / b, np.nan)

    if antecipado:
        nan = np.full(len(sig), np.nan)
        sig['ef_par_vol'] = nan
        sig['ef_par_negs'] = nan
        sig['ef_par_agr'] = nan
        sig['ef_vol_rng'] = nan
        sig['tam_neg'] = raz(qtd[i_ret], negs[i_ret])
        sig['tam_neg_r'] = nan
        sig['ef_absoluta'] = nan
        sig['gasto_par'] = nan
        return sig

    #  As duas barras do par produziram o MESMO resultado -- 100 pontos,
    #  cada uma para o seu lado. A razao dos esforcos e, portanto, uma
    #  comparacao com o resultado controlado dos dois lados.
    sig['ef_par_vol'] = raz(qtd[i], qtd[i_ret])
    sig['ef_par_negs'] = raz(negs[i], negs[i_ret])
    sig['ef_par_agr'] = raz(agr[i], agr[i_ret])

    #  esforco por ponto PERCORRIDO (range), nao pelo resultado (100)
    sig['ef_vol_rng'] = raz(qtd[i], h[i] - l[i])

    #  quem esta negociando: volume medio por negocio
    sig['tam_neg'] = raz(qtd[i], negs[i])
    sig['tam_neg_r'] = raz(raz(qtd[i], negs[i]), raz(qtd[i_ret], negs[i_ret]))

    sig['ef_absoluta'] = raz(qtd[i], medq[i])
    #  o par inteiro fecha com deslocamento liquido ZERO (-100 depois +100):
    #  aqui o esforco e puro, sem resultado nenhum do outro lado
    sig['gasto_par'] = raz(qtd[i] + qtd[i_ret], 2.0 * medq[i])
    return sig


# ============================================================== a medicao
#  Spearman por rank + permutacao: nao vale acrescentar scipy ao projeto
#  so por uma correlacao.
def _rho(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 10:
        return float('nan')
    rx = pd.Series(x[ok]).rank().to_numpy()
    ry = pd.Series(y[ok]).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def roda(t, d, S, FX, p=print, semente=4242):
    """A familia inteira, com as mesmas peneiras do estudo de fluxo.

    Devolve dict pronto para o relatorio. `t` ja precisa vir de
    estudo_fluxo.monta() e ter passado por `anexa()`.
    """
    rng = np.random.default_rng(semente)
    NOVAS = ['ef_par_vol', 'ef_par_negs', 'ef_par_agr', 'tam_neg', 'tam_neg_r']

    # --- [0] isto e informacao nova, ou e o pavio de novo? --------------
    novidade = []
    for c in FAMILIA:
        novidade.append(dict(
            col=c, rotulo=ROTULO[c],
            corr_pav=float(t[c].corr(t['pav_tot'])),
            corr_vol=float(t[c].corr(t['vol_cont'])),
            corr_dur=float(t[c].corr(t['dur_cont'])),
        ))
    # a prova de que a eficiencia geometrica JA e o filtro do Ouro
    geom = dict(rho=_rho(t['corpo_r'].to_numpy(float),
                         t['pav_tot'].to_numpy(float)))

    # --- [1] monotonicidade: a historia de Wyckoff exige ---------------
    rho = []
    for niv in ('bronze', 'prata', 'ouro'):
        sub = S.seleciona(t, niv)
        r = _rho(sub['ef_par_vol'].to_numpy(float), sub['pts'].to_numpy(float))
        # p por permutacao, bicaudal no sentido esperado (rho negativo = bom)
        x = sub['ef_par_vol'].to_numpy(float); y = sub['pts'].to_numpy(float)
        nulo = np.array([_rho(x, rng.permutation(y)) for _ in range(2000)])
        rho.append(dict(nivel=niv, n=int(len(sub)), rho=r,
                        p_valor=float((nulo <= r).mean())))

    # --- [2] os quintis, no Ouro: o de MENOR esforco e o melhor? -------
    sub = S.seleciona(t, 'ouro')
    q = pd.qcut(sub['ef_par_vol'], 5, duplicates='drop')
    quint = []
    for k, g in sub.groupby(q, observed=True):
        quint.append(dict(faixa=str(k), n=int(len(g)),
                          ev=float(g['pts'].mean()),
                          wr=float(100 * (g['pts'] > 0).mean())))
    base_ouro = float(sub['pts'].mean())

    # --- [3] a peneira de busca, so nesta familia ----------------------
    pen = []
    for niv in ('bronze', 'prata', 'ouro'):
        sub = S.seleciona(t, niv).reset_index(drop=True)
        bt, bd = FX.busca(sub, feats=NOVAS)
        if bd is None:
            continue
        nulo = np.array([FX.busca(sub, feats=NOVAS, rng=rng)[0]
                         for _ in range(400)])
        nulo = nulo[nulo > -9e8]
        pen.append(dict(nivel=niv, melhor=bd,
                        ruido_mediana=float(np.median(nulo)),
                        ruido_p90=float(np.quantile(nulo, .90)),
                        p_valor=float((nulo >= bt).mean())))

    # --- [4] o corte mais fiel (<1), em cada nivel e em cada gestao ----
    #  Um efeito de verdade nao pode depender de qual alvo se usa: a
    #  gestao muda o desfecho de cada trade, nao a leitura do fluxo.
    def _corte(tt, niv, rot):
        sub = S.seleciona(tt, niv).reset_index(drop=True)
        pts = sub['pts'].to_numpy(float)
        m = (sub['ef_par_vol'] < 1).to_numpy()
        obs = pts[m].mean() - pts.mean()
        nulo = np.array([pts[rng.permutation(m)].mean() - pts.mean()
                         for _ in range(4000)])
        return dict(
            nivel=niv, gestao=rot, n=int(m.sum()), ev=float(pts[m].mean()),
            base=float(pts.mean()), ganho=float(obs),
            p_valor=float((nulo >= obs).mean()),
            tercos=[float(pts[m & (sub['terco'] == z).to_numpy()].mean())
                    if (m & (sub['terco'] == z).to_numpy()).any() else float('nan')
                    for z in ('T1', 'T2', 'T3')])

    cortes = [_corte(t, niv, '1:3 com parcial') for niv in ('prata', 'ouro')]
    for rot, g in (('1:3 sem parcial', dict(parcial=False)),
                   ('1:2 sem parcial', dict(parcial=False, alvo=200.0))):
        _, t2 = FX.monta(gestao=g)
        t2 = anexa(t2, d, False)
        cortes.append(_corte(t2, 'ouro', rot))

    # --- [5] poder: o ganho alegado e detectavel? ----------------------
    sub = S.seleciona(t, 'ouro')
    pts = sub['pts'].to_numpy(float)
    n1 = int((sub['ef_par_vol'] < 1).sum())
    se = pts.std(ddof=1) * np.sqrt(1.0 / n1 - 1.0 / len(pts))
    pod = dict(n=int(len(pts)), n1=n1, frac=100.0 * n1 / len(pts),
               min_ganho=float(2.8 * se),
               observado=float(pts[(sub['ef_par_vol'] < 1).to_numpy()].mean()
                               - pts.mean()))

    p('  esforco: rho(esforco, resultado) no Ouro = %+.3f  |  quintil de MENOR '
      'esforco = %+.1f (base %+.1f)' % (rho[-1]['rho'], quint[0]['ev'], base_ouro))
    for c in cortes:
        p('           corte<1 %-7s %-16s ganho %+6.1f  p=%.3f'
          % (c['nivel'], c['gestao'], c['ganho'], c['p_valor']))
    p('           corte <1: ganho %+.1f pts, detectavel so acima de %+.0f'
      % (pod['observado'], pod['min_ganho']))

    return dict(novidade=novidade, geom=geom, rho=rho, quintis=quint,
                base_ouro=base_ouro, peneira=pen, cortes=cortes, poder=pod,
                espaco=dict(feats=len(NOVAS), cortes=5, sentidos=2,
                            total=len(NOVAS) * 5 * 2, perms=400))
