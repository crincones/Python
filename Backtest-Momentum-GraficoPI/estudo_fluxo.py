# -*- coding: utf-8 -*-
"""
Duas perguntas, medidas com o mesmo rigor do resto do backteste:

  1. A agressao e o tempo de barra (WINFUT_20PI_Agr_Tempo.csv) melhoram
     a filtragem?
  2. Um filtro de FORCA DE TENDENCIA melhora? Em particular: operacoes
     contra uma tendencia forte falham mais? E a retracao logo depois de
     um cruzamento contundente da EMA 21 funciona melhor?

A resposta e NAO para as duas, e o que da valor a resposta nao e ter
olhado -- e o CONTROLE DA BUSCA. Olhar dezessete atributos em cinco cortes
e dois sentidos sao 170 comparacoes; nesse tamanho de amostra alguma
sempre parece boa. Entao aqui cada achado passa por tres peneiras:

  [P1] ESTABILIDADE       o ganho aparece nos tres tercos do periodo?
  [P2] BUSCA EM RUIDO     a MESMA busca, rodada sobre versoes
                          EMBARALHADAS do atributo (que preservam a
                          distribuicao e destroem a ligacao com o
                          resultado), acha algo tao bom quanto? Se acha,
                          o achado e a busca, nao o atributo.
  [P3] FORA DA AMOSTRA    o corte escolhido nos dois primeiros tercos
                          ainda funciona no terceiro?

Nenhum atributo novo passou de [P2]. O melhor filtro achado no Ouro tem
t = +3,5; a mesma busca em ruido acha t = +4,1 na MEDIANA. E em [P3] o
filtro escolhido em T1+T2 entrega EV NEGATIVO em T3, contra +30 sem
filtro nenhum -- ele nao so nao ajuda, atrapalha.

Isso NAO prova que fluxo e tendencia nao importam no WINFUT. Prova que
com 173 sinais Ouro esta base so enxergaria um ganho maior que ~40 pontos
por trade (secao PODER), e nenhum dos atributos chega perto disso.
"""
import numpy as np
import pandas as pd

import engine as E
import estrategia as S
import features as X
import fluxo as FL
import esforco as EFR

# ------------------------------------------------------------ espaco de busca
#  Fechado e declarado ANTES de olhar: e o que torna [P2] honesto.
FEATS = ['er10', 'er20', 'er30', 'er50', 'lado_ema', 'barras_cruz',
         'forca_cruz', 'agr_cont', 'agr_ret', 'agr_ret_acu', 'vel_cont',
         'vel_ret', 'vel_r', 'vol_cont', 'vol_ret', 'dur_cont', 'dur_ret']
QS = (0.20, 0.33, 0.50, 0.67, 0.80)     # cortes tentados, em quantis
MIN_FRAC = 0.20                          # o filtro precisa manter 20% dos sinais
N_PERM = 400                             # embaralhamentos de [P2]

ROTULO_F = {
    'er10': 'deriva de 10 barras', 'er20': 'deriva de 20 barras',
    'er30': 'deriva de 30 barras', 'er50': 'deriva de 50 barras',
    'lado_ema': 'lado da EMA 21', 'barras_cruz': 'idade do cruzamento',
    'forca_cruz': 'forca do cruzamento', 'agr_cont': 'agressao na continuacao',
    'agr_ret': 'agressao na retracao',
    'agr_ret_acu': 'agressao acumulada da retracao',
    'vel_cont': 'velocidade da continuacao', 'vel_ret': 'velocidade da retracao',
    'vel_r': 'razao de velocidade', 'vol_cont': 'volume da continuacao',
    'vol_ret': 'volume da retracao', 'dur_cont': 'duracao da continuacao',
    'dur_ret': 'duracao da retracao',
}


# ================================================================== montagem
def monta(gestao=None, entrada='fecha'):
    """Base com fluxo anexado, sinais confirmados, resolvidos e classificados."""
    d = E.indicadores(FL.anexa())
    t = E.executa(d, E.sinais(d, False), entrada, gestao or dict(parcial=True))
    t = S.anota(X.anexa_sinais(t, d, False))
    t = t[t['aceito']].reset_index(drop=True)
    t['terco'] = pd.qcut(t['i'], 3, labels=['T1', 'T2', 'T3'])
    return d, t


def _ev(p):
    if len(p) < 2:
        return dict(n=int(len(p)), ev=float('nan'), wr=float('nan'),
                    t=float('nan'))
    s = p.std(ddof=1)
    return dict(n=int(len(p)), ev=float(p.mean()),
                wr=float(100 * (p > 0).mean()),
                t=float(p.mean() / (s / np.sqrt(len(p)))) if s > 0 else float('nan'))


# ============================================================ a busca fechada
def busca(sub, feats=FEATS, rng=None, min_frac=MIN_FRAC):
    """Melhor filtro do espaco, pelo t do subconjunto que ele deixa passar.

    Exige EV positivo nos tres tercos -- que e exatamente o criterio que um
    humano usa de olho ao varrer uma tabela de quintis. Por isso e ELE que
    precisa ser confrontado com ruido, e nao um t nu.
    """
    p = sub['pts'].to_numpy(float)
    terco = sub['terco'].to_numpy()
    nmin = max(20, int(len(sub) * min_frac))
    melhor_t, melhor = -9e9, None
    for c in feats:
        x = sub[c].to_numpy(float)
        if rng is not None:
            x = rng.permutation(x)
        for q in QS:
            thr = float(np.nanquantile(x, q))
            for sinal in (+1, -1):
                m = (x >= thr) if sinal > 0 else (x <= thr)
                if m.sum() < nmin:
                    continue
                pp = p[m]
                if pp.std(ddof=1) == 0:
                    continue
                t = pp.mean() / (pp.std(ddof=1) / np.sqrt(len(pp)))
                if t <= melhor_t:
                    continue
                if not all(p[m & (terco == k)].mean() > 0
                           for k in ('T1', 'T2', 'T3') if (m & (terco == k)).any()):
                    continue
                melhor_t = t
                melhor = dict(col=c, rotulo=ROTULO_F.get(c, c), q=q, thr=thr,
                              sentido='>=' if sinal > 0 else '<=', **_ev(pp))
    return melhor_t, melhor


def peneira(t, semente=20260912):
    """[P2] e [P3] em cada nivel. Devolve lista pronta para o relatorio."""
    rng = np.random.default_rng(semente)
    out = []
    for niv in S.NIVEIS[::-1]:                       # bronze, prata, ouro
        sub = S.seleciona(t, niv).reset_index(drop=True)
        p = sub['pts'].to_numpy(float)
        bt, bd = busca(sub)
        nulo = np.array([busca(sub, rng=rng)[0] for _ in range(N_PERM)])
        nulo = nulo[nulo > -9e8]

        # [P3] escolhe nos dois primeiros tercos, mede no terceiro
        tr = sub[sub['terco'] != 'T3'].reset_index(drop=True)
        te = sub[sub['terco'] == 'T3']
        _, fd = busca(tr)
        fora = None
        if fd is not None and len(te):
            x = te[fd['col']].to_numpy(float)
            m = (x >= fd['thr']) if fd['sentido'] == '>=' else (x <= fd['thr'])
            fora = dict(col=fd['col'], rotulo=ROTULO_F[fd['col']],
                        sentido=fd['sentido'], thr=fd['thr'],
                        ev_dentro=fd['ev'], n_dentro=fd['n'],
                        n_t3=int(m.sum()),
                        ev_t3=(float(te['pts'].to_numpy()[m].mean())
                               if m.any() else float('nan')),
                        ev_t3_base=float(te['pts'].mean()),
                        n_t3_base=int(len(te)))
        out.append(dict(
            nivel=niv, n=int(len(p)), ev=float(p.mean()),
            t_base=_ev(p)['t'], melhor=bd,
            ruido_mediana=float(np.median(nulo)),
            ruido_p90=float(np.quantile(nulo, .90)),
            ruido_p99=float(np.quantile(nulo, .99)),
            p_valor=float((nulo >= bt).mean()), fora=fora))
    return out


# ======================================================= as duas hipoteses
def hipoteses(t):
    """[P1] nas hipoteses do usuario, cada uma com UM teste de permutacao."""
    rng = np.random.default_rng(11)

    def um(sub, m, n=4000):
        p = sub['pts'].to_numpy(float)
        m = np.asarray(m, bool)
        if m.sum() < 10:
            return None
        obs = p[m].mean() - p.mean()
        nulo = np.array([p[rng.permutation(m)].mean() - p.mean()
                         for _ in range(n)])
        r = _ev(p[m])
        r.update(ganho=float(obs), p_valor=float((nulo >= obs).mean()),
                 base=float(p.mean()),
                 tercos=[float(p[m & (sub['terco'] == k).to_numpy()].mean())
                         if (m & (sub['terco'] == k).to_numpy()).any()
                         else float('nan')
                         for k in ('T1', 'T2', 'T3')])
        return r

    testes = []
    for niv in S.NIVEIS[::-1]:
        sub = S.seleciona(t, niv).reset_index(drop=True)
        casos = [
            ('H1 a favor da deriva de 20 barras', sub['er20'] > 0),
            ('H1 a favor da deriva de 50 barras', sub['er50'] > 0),
            ('H1 fechamento do lado do trade na EMA 21', sub['lado_ema'] > 0),
            ('H1- contra uma deriva grande de 50 barras', sub['er50'] <= -0.12),
            ('H2 primeiro sinal depois do cruzamento', sub['ordem_cruz'] == 1),
            ('H2 primeiro sinal e cruzamento contundente',
             (sub['ordem_cruz'] == 1) & (sub['forca_cruz'] >= 0.7)),
            ('fluxo confirma a continuacao (sem absorcao)', ~sub['absorcao']),
            ('fluxo: retracao vendida (agressao contra < -0,23)',
             sub['agr_ret'] <= -0.23),
            ('fluxo: continuacao com volume acima da mediana',
             sub['vol_cont'] >= 1.0),
        ]
        for rot, m in casos:
            r = um(sub, m.to_numpy())
            if r:
                r.update(nivel=niv, rotulo=rot)
                testes.append(r)
    return testes


def ordem_desde_cruz(t):
    """Este sinal e o 1o, 2o, 3o... desde que o fechamento cruzou a EMA 21
    para o lado do trade. 0 = o fechamento esta do lado oposto."""
    t = t.sort_values('i').copy()
    ic = t['i'].to_numpy(int) - t['barras_cruz'].to_numpy(int)
    lado = t['lado'].to_numpy(int)
    favor = t['lado_ema'].to_numpy() > 0
    ordem = np.zeros(len(t), int)
    visto = {}
    for k in range(len(t)):
        if not favor[k]:
            continue
        ch = (int(ic[k]), int(lado[k]))
        visto[ch] = visto.get(ch, 0) + 1
        ordem[k] = visto[ch]
    t['ordem_cruz'] = ordem
    return t.sort_index()


# ================================================================== quintis
def quintis(t, cols, q=5):
    """Tabela de EV por faixa, com a quebra por terco -- a vista crua."""
    out = []
    for niv in ('ouro', 'bronze'):
        sub = S.seleciona(t, niv)
        for c in cols:
            try:
                b = pd.qcut(sub[c], q, duplicates='drop')
            except ValueError:
                continue
            faixas = []
            for k, g in sub.groupby(b, observed=True):
                r = _ev(g['pts'].to_numpy(float))
                r['faixa'] = str(k)
                r['tercos'] = [float(g.loc[g['terco'] == x, 'pts'].mean())
                               if (g['terco'] == x).any() else float('nan')
                               for x in ('T1', 'T2', 'T3')]
                faixas.append(r)
            out.append(dict(nivel=niv, col=c, rotulo=ROTULO_F.get(c, c),
                            faixas=faixas))
    return out


# =================================================================== poder
def poder(t):
    """Menor ganho de EV que esta amostra distingue de zero (80%, 5%)."""
    out = []
    for niv in S.NIVEIS[::-1]:
        sub = S.seleciona(t, niv)
        p = sub['pts'].to_numpy(float)
        s = float(p.std(ddof=1))
        linhas = []
        for frac in (0.50, 0.33, 0.25):
            n1 = int(len(p) * frac)
            if n1 < 10:
                continue
            se = s * np.sqrt(1.0 / n1 - 1.0 / len(p))
            linhas.append(dict(mantem=frac, n=n1, min_ganho=float(2.8 * se)))
        out.append(dict(nivel=niv, n=int(len(p)), desvio=s, linhas=linhas))
    return out


# ==================================================================== tudo
def _eu():
    """O proprio modulo, para o esforco.py reusar `busca()` sem importar
    em circulo."""
    import sys
    return sys.modules[__name__]


def roda(p=print):
    d, t = monta()
    t = ordem_desde_cruz(t)

    dur = d['dur_s']
    base = dict(
        barras=int(len(d)),
        dur_p25=float(dur.quantile(.25)), dur_mediana=float(dur.median()),
        dur_p75=float(dur.quantile(.75)), dur_p95=float(dur.quantile(.95)),
        agr_medio_cont=float(t['agr_cont'].mean()),
        agr_medio_ret=float(t['agr_ret'].mean()),
        vol_mediano=float(d['qtd'].median()),
        negs_mediano=float(d['negs'].median()),
    )
    p('  fluxo: %d barras, duracao mediana %.0f s'
      % (base['barras'], base['dur_mediana']))

    res = dict(
        base=base,
        peneira=peneira(t),
        hipoteses=hipoteses(t),
        quintis=quintis(t, ['er50', 'agr_cont', 'agr_ret', 'vel_cont',
                            'vol_cont', 'dur_cont']),
        poder=poder(t),
        espaco=dict(feats=len(FEATS), cortes=len(QS), sentidos=2,
                    total=len(FEATS) * len(QS) * 2, perms=N_PERM,
                    min_frac=MIN_FRAC),
        esforco=EFR.roda(EFR.anexa(t, d, False), d, S, _eu(), p),
    )
    for r in res['peneira']:
        m = r['melhor']
        p('  %-7s melhor t=%+.2f (%s %s)  ruido mediana t=%+.2f  p=%.3f  %s'
          % (r['nivel'], m['t'], m['col'], m['sentido'], r['ruido_mediana'],
             r['p_valor'], 'passa' if r['p_valor'] <= 0.10 else 'NAO passa'))
        if r['fora']:
            f = r['fora']
            p('          fora da amostra: T3 sem filtro %+.1f -> com filtro %+.1f'
              % (f['ev_t3_base'], f['ev_t3']))
    return res


if __name__ == '__main__':
    roda()
