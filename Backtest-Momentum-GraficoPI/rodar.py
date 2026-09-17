# -*- coding: utf-8 -*-
"""
Roda o backteste inteiro e escreve tudo em saida/.

    python rodar.py

Produz:
  saida/trades_<modo>_<gestao>_<nivel>.csv   trade a trade
  saida/resumo.json                          tudo o que o relatorio consome
  saida/console.txt                          o que apareceu na tela

Depois, `python relatorio.py` monta o HTML e o RESULTADOS.md, e
`python plano.py` monta o plano de trading.
"""
import io
import json
import os
import numpy as np
import pandas as pd

import engine as E
import estrategia as S
import estudo_fluxo as FX
import periodos as PR

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
os.makedirs(SAIDA, exist_ok=True)

MODOS = ('fecha', 'meio_lim', 'antecipa')
# As tres gestoes comparadas. 'parcial' e 'puro' sao o 1:3 do CLAUDE.md com
# e sem a saida parcial; 'r2' e o 1:2 puro -- stop de 1, alvo de 2 -- que
# troca alvo por taxa de acerto.
GESTOES = {'parcial': dict(parcial=True),
           'puro': dict(parcial=False),
           'r2': dict(parcial=False, alvo=200.0)}

ROT_GESTAO = {'parcial': '1:3 com parcial', 'puro': '1:3 sem parcial',
              'r2': '1:2 sem parcial'}

_buf = io.StringIO()


def p(*a, **k):
    print(*a, **k)
    print(*a, **k, file=_buf)


def _lim(x):
    """Converte para algo que o json aceita."""
    if isinstance(x, (np.floating, float)):
        x = float(x)
        return None if (np.isnan(x) or np.isinf(x)) else round(x, 6)
    if isinstance(x, (np.integer, int)):
        return int(x)
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (list, tuple)):
        return [_lim(v) for v in x]
    if isinstance(x, dict):
        return {str(k): _lim(v) for k, v in x.items()}
    return x



ROT_SAIDA = {'alvo': 'alvo', 'stop': 'stop', 'stop_zero': 'zero a zero',
             'timeout': 'tempo', 'fim_dia': 'fim do dia'}


def dur_texto(seg):
    """Duracao em texto curto -- os trades vao de segundos a horas."""
    seg = float(seg)
    if seg < 60:
        return f'{seg:.0f}s'
    if seg < 3600:
        return f'{seg / 60:.0f}min'
    return f'{seg / 3600:.1f}h'


# ======================================================== blocos de estudo
def estudo_atributo(t, col, cortes, rotulos=None):
    """EV por faixa de um atributo, com a quebra por terco do periodo.

    O terco existe para separar o que e efeito do que e sorte: um filtro
    que so aparece num pedaco do periodo nao e filtro, e ruido.
    """
    s = t[t['aceito']].copy()
    faixa = pd.cut(s[col], cortes, labels=rotulos)
    out = []
    for nome, g in s.groupby(faixa, observed=True):
        if len(g) == 0:
            continue
        por_terco = [float(x.mean()) if len(x) else None
                     for _, x in g.groupby('terco', observed=True)['pts']]
        n_terco = [int(len(x)) for _, x in g.groupby('terco', observed=True)['pts']]
        out.append(dict(faixa=str(nome), n=int(len(g)),
                        ev=float(g['pts'].mean()),
                        wr=float((g['pts'] > 0).mean() * 100),
                        pts=float(g['pts'].sum()),
                        ev_terco=por_terco, n_terco=n_terco))
    return out


def marca_tercos(t, dias):
    c1, c2 = dias[len(dias) // 3], dias[2 * len(dias) // 3]
    t = t.copy()
    t['terco'] = np.where(t['data'] < c1, 'T1',
                          np.where(t['data'] < c2, 'T2', 'T3'))
    return t, str(pd.Timestamp(c1).date()), str(pd.Timestamp(c2).date())


def monte_carlo(pts, n=4000, semente=20260911):
    """Reamostra os trades COM reposicao e devolve a distribuicao do
    resultado e do drawdown. Responde 'quanto disso foi ordem de chegada'."""
    rng = np.random.default_rng(semente)
    m = len(pts)
    if m < 10:
        return {}
    tot = np.empty(n); dd = np.empty(n)
    for k in range(n):
        am = rng.choice(pts, size=m, replace=True)
        eq = np.cumsum(am)
        tot[k] = eq[-1]
        dd[k] = (np.maximum.accumulate(np.r_[0.0, eq]) - np.r_[0.0, eq]).max()
    return dict(
        total_p05=float(np.percentile(tot, 5)),
        total_p25=float(np.percentile(tot, 25)),
        total_mediana=float(np.median(tot)),
        total_p75=float(np.percentile(tot, 75)),
        total_p95=float(np.percentile(tot, 95)),
        prob_lucro=float((tot > 0).mean() * 100),
        dd_mediana=float(np.median(dd)),
        dd_p95=float(np.percentile(dd, 95)),
        hist_total=np.histogram(tot, bins=40)[0].tolist(),
        hist_total_bins=np.histogram(tot, bins=40)[1].tolist(),
    )



def galeria(ref, n_por_nivel=6):
    """Escolhe exemplos de cada nivel para a galeria do relatorio.

    O objetivo e MEMORIZAR a forma, nao vender o resultado. Por isso os
    exemplos sao espalhados ao longo do periodo e a escolha garante, em
    cada nivel, os dois lados (compra e venda) e pelo menos um trade que
    deu errado -- uma galeria so de acertos ensinaria a reconhecer sorte,
    nao padrao.
    """
    out = {}
    for niv in S.NIVEIS:
        # cada nivel mostra SO os sinais daquele nivel (nao os encaixados),
        # senao a galeria do Bronze viraria a galeria do Ouro
        pool = ref[ref['nivel'] == niv].sort_values('i').reset_index(drop=True)
        if len(pool) == 0:
            out[niv] = []
            continue
        # 1. espalhar no tempo e o criterio principal: a galeria tem de
        #    cobrir o periodo, nao um pedaco dele
        n = min(n_por_nivel, len(pool))
        escolhidos = sorted({int(round(k * (len(pool) - 1) / max(1, n - 1)))
                             for k in range(n)})

        def garante(cond, rotulo):
            """Se nenhum escolhido satisfaz `cond`, troca o mais proximo."""
            if any(cond(pool.loc[i]) for i in escolhidos):
                return
            cands = [i for i in pool.index if cond(pool.loc[i])]
            if not cands:
                return
            # sacrifica o escolhido que estiver mais perto de um candidato,
            # para mexer o menos possivel no espalhamento
            alvo = min(cands, key=lambda c: min(abs(c - e) for e in escolhidos))
            fora = min(escolhidos, key=lambda e: abs(e - alvo))
            escolhidos.remove(fora)
            escolhidos.append(alvo)
            escolhidos.sort()

        # 2. e a galeria precisa mostrar as duas pontas: os dois lados, e
        #    pelo menos um trade que deu errado
        garante(lambda r: r['lado'] > 0, 'compra')
        garante(lambda r: r['lado'] < 0, 'venda')
        garante(lambda r: r['pts'] < 0, 'perda')
        garante(lambda r: r['pts'] > 0, 'ganho')

        itens = []
        for k in sorted(escolhidos)[:n_por_nivel]:
            r = pool.loc[k]
            # por que este sinal nao subiu de nivel -- o que a galeria ensina
            if niv == 'ouro':
                motivo = 'cumpre os seis passos'
            elif niv == 'prata':
                motivo = (f"pavio de {r['pav_tot']:.0f} pts, fora da faixa de "
                          f"{S.PAVIO_MIN:.0f} a {S.PAVIO_MAX:.0f}")
            else:
                falhas = []
                if r['exaustao']:
                    falhas.append('em exaustao (Hull acelerando + preco esticado)')
                if not r['ret_ok']:
                    falhas.append(f"retracao de {int(r['n_ret'])} candle so")
                motivo = ' e '.join(falhas) if falhas else 'fora dos filtros'
            # a tabela crua traz `i` (o candle de continuacao) e a contagem
            # da retracao; o primeiro candle dela sai dos dois
            i_sin = int(r['i']); i_ret = i_sin - int(r['n_ret'])
            itens.append(dict(
                de=int(max(0, i_ret - 11)),
                ate=int(r['i_sai'] + 3),
                i_ret=i_ret, i_sin=i_sin,
                i_ent=int(r['i_ent']), i_sai=int(r['i_sai']),
                lado=int(r['lado']), pts=float(r['pts']),
                preco_ent=float(r['preco_ent']),
                data=r['data'].strftime('%d/%m %H:%M'),
                rot_saida=ROT_SAIDA.get(r['motivo'], r['motivo']),
                n_ret=int(r['n_ret']), pav_tot=float(r['pav_tot']),
                motivo=motivo, nivel=niv))
        out[niv] = itens
    return out


def p_stop_aleatorio(prof):
    """Probabilidade de a ordem stop ter disparado ANTES do pavio contra.

    Candle de PI que fechou a favor com o pavio contra alcancando o stop
    (entrada no meio do corpo, stop 100 abaixo = 50 abaixo da abertura).
    Com OHLC nao da para saber a ordem. Um passeio aleatorio de ticks de 5
    pontos, que abre em 0 e fecha ao tocar +100 ou -100, condicionado a
    fechar em +100 com a minima nessa profundidade, dispara em +50 e depois
    toma o stop em -50 com esta frequencia (simulacao de 200 mil caminhos):
    28% com minima em -50 ate 40% com minima em -95.
    """
    prof = np.clip(np.asarray(prof, dtype=float), 50, 95)
    return 0.276 + (prof - 50) / 45 * (0.397 - 0.276)


def cenarios_antecipa(d, tabelas, p):
    """A antecipada depende de uma convencao que as outras entradas nao usam.

    A engine assume que, num candle que fechou a favor, o pavio contra se
    formou ANTES de a ordem stop disparar -- entao a propria barra de
    entrada nunca toma stop. Quando esse pavio chega ao stop, isso e uma
    aposta, nao um dado. Tres cenarios por sinal:
      convencao    o da engine
      aleatorio    o stop acontece com a probabilidade do passeio aleatorio
      pessimista   todo candle ambiguo tomou stop
    """
    o = d['o'].to_numpy(); h = d['h'].to_numpy()
    l = d['l'].to_numpy(); c = d['c'].to_numpy()
    out = {}
    for gn in GESTOES:
        t = tabelas[('antecipa', gn)]
        t = t[t['aceito']]
        ie = t['i_ent'].to_numpy(int); ld = t['lado'].to_numpy(int)
        pe = t['preco_ent'].to_numpy(float)
        fav = np.sign(c[ie] - o[ie]) == ld
        adv = np.where(ld > 0, l[ie], h[ie])
        amb = fav & ((adv - (pe - ld * E.STOP)) * ld <= 0)
        prof = (o[ie] - adv) * ld
        pr = np.where(amb, p_stop_aleatorio(prof), 0.0)
        pts = t['pts'].to_numpy(float)
        ale = (1 - pr) * pts + pr * (-E.STOP)
        pes = np.where(amb, -E.STOP, pts)
        for niv in ('prata', 'bronze'):
            m = S.seleciona(t.assign(_k=np.arange(len(t))), niv)['_k'].to_numpy()
            r = dict(n=int(len(m)), ambiguos_pct=float(amb[m].mean() * 100),
                     ev_conv=float(pts[m].mean()), ev_aleat=float(ale[m].mean()),
                     ev_pess=float(pes[m].mean()))
            out[f'{gn}|{niv}'] = r
            p(f"    {gn:<8}{niv:<7} n={r['n']:>5}  candles ambiguos {r['ambiguos_pct']:4.1f}%   "
              f"EV convencao {r['ev_conv']:+6.1f}  aleatorio {r['ev_aleat']:+6.1f}  "
              f"pessimista {r['ev_pess']:+6.1f}")
    return out


# ================================================================== main
def main():
    p('=' * 72)
    p('BACKTEST MOMENTUM -- GRAFICO PI (Pontos de Inversao)')
    p('=' * 72)

    d0 = E.carrega()
    d = E.indicadores(d0)
    dias = np.sort(d['dia'].unique())

    # ---------------------------------------------------------- auditoria
    p('\n[1] BASE E AUDITORIA')
    corpo = (d['c'] - d['o']).abs()
    ema_ok = d['ema_nl'].notna()
    erro_ema = (d['ema'] - d['ema_nl'])[ema_ok].abs()
    # o csv publica a EMA com 2 casas, entao erro de arredondamento e
    # esperado; divergencia DE VERDADE e acima de 1 ponto inteiro.
    grosso = int((erro_ema > 1.0).sum())
    aud = dict(
        candles=int(len(d)), dias=int(len(dias)),
        de=str(pd.Timestamp(dias[0]).date()), ate=str(pd.Timestamp(dias[-1]).date()),
        corpo_min=float(corpo.min()), corpo_max=float(corpo.max()),
        corpo_100_pct=float((corpo == 100).mean() * 100),
        abre_no_fecha_pct=float((d['o'].iloc[1:].to_numpy()
                                 == d['c'].iloc[:-1].to_numpy()).mean() * 100),
        ema_conferidos=int(ema_ok.sum()),
        ema_erro_p999=float(erro_ema[erro_ema <= 1.0].max()),
        ema_divergentes=grosso,
        atr_mediana=float(d['atr'].median()),
        range_mediano=float((d['h'] - d['l']).median()),
        barras_dia_media=float(len(d) / len(dias)),
    )
    p(f"    {aud['candles']} candles, {aud['dias']} pregoes, "
      f"{aud['de']} a {aud['ate']} ({aud['barras_dia_media']:.0f} candles/dia)")
    p(f"    corpo = 100 pontos em {aud['corpo_100_pct']:.2f}% dos candles "
      f"(min {aud['corpo_min']:.0f}, max {aud['corpo_max']:.0f})")
    p(f"    abertura = fechamento anterior em {aud['abre_no_fecha_pct']:.2f}%")
    p(f"    EMA 21 conferida contra a da Nelogica em {aud['ema_conferidos']} "
      f"candles: erro max {aud['ema_erro_p999']:.3f} ponto (arredondamento "
      f"das 2 casas do csv), {grosso} candles com divergencia real")
    p(f"    ATR 21 mediano {aud['atr_mediana']:.0f} pontos, "
      f"range mediano {aud['range_mediano']:.0f}")

    # ------------------------------------------------------------ sinais
    p('\n[2] SINAIS DA REGRA-BASE')
    sc = E.sinais(d, antecipado=False)
    sa = E.sinais(d, antecipado=True)
    p(f"    confirmados (candle de continuacao fechado): {len(sc)}")
    p(f"    antecipados (ordem no fechamento da retracao): {len(sa)}")

    # ------------------------------------------- matriz modo x gestao x nivel
    p('\n[3] MATRIZ  modo de entrada  x  gestao  x  nivel')
    p(f"    {'modo':<10}{'gestao':<9}{'nivel':<8}{'N':>5}{'pts':>8}{'R$':>9}"
      f"{'EV':>7}{'win%':>7}{'FL':>6}{'DD':>7}{'Rec':>6}")
    variantes = {}
    tabelas = {}
    t_ini = d['data'].iloc[0]
    t_fim = d['data'].iloc[-1]
    for modo in MODOS:
        s = sa if modo == 'antecipa' else sc
        for gn, g in GESTOES.items():
            t = S.anota(E.executa(d, s, modo, g))
            t, c1, c2 = marca_tercos(t, dias)
            tabelas[(modo, gn)] = t
            for niv in S.NIVEIS:
                if modo == 'antecipa' and niv == 'ouro':
                    continue     # geometria do candle nao existe ainda
                sel = S.seleciona(t[t['aceito']], niv)
                ca = E.carteira(sel)
                if len(ca) == 0:
                    continue
                st = E.estatisticas(ca)
                # Posicao de cada trade DENTRO DO PERIODO, de 0 a 1. As tres
                # variantes tem contagens de trade diferentes; num eixo de
                # "numero do trade" a curva de 170 pontos pareceria parar no
                # meio do grafico. No eixo de tempo elas sao comparaveis.
                st['eq_t'] = (((ca['data'] - t_ini) / (t_fim - t_ini))
                              .astype(float).round(5).tolist())
                st['eq_d'] = ca['data'].dt.strftime('%d/%m').tolist()
                chave = f'{modo}|{gn}|{niv}'
                exp = ca.assign(
                    data=ca['data'].dt.strftime('%d/%m/%Y %H:%M:%S'),
                    i_ret=(ca['i'] - ca['n_ret']).clip(lower=0),
                    i_sin=ca['i'],
                    rot_saida=ca['motivo'].map(ROT_SAIDA),
                    dur_txt=ca['dur_s'].map(dur_texto),
                )[['data', 'lado', 'nivel', 'preco_ent', 'preco_sai', 'pts',
                   'mfe', 'mae', 'dur_s', 'dur_txt', 'barras', 'motivo',
                   'rot_saida', 'hora', 'i_ret', 'i_sin', 'i_ent', 'i_sai',
                   'n_ret', 'pav_tot', 'exaustao', 'ret_ok', 'geom_ok']]
                variantes[chave] = dict(
                    modo=modo, gestao=gn, nivel=niv, stats=st,
                    # o grafico trade a trade so navega o fechamento e a
                    # antecipada; a limitada entra so nas tabelas, e para
                    # isso bastam as estatisticas
                    trades=([] if modo == 'meio_lim' else exp.to_dict('records')),
                )
                p(f"    {modo:<10}{gn:<9}{niv:<8}{st['trades']:>5}"
                  f"{st['lucro_liq']:>8.0f}{st['lucro_liq_rs']:>9.0f}"
                  f"{st['exp_pts']:>7.1f}{st['winrate']:>6.1f}%"
                  f"{st['fator_lucro']:>6.2f}{st['dd_max']:>7.0f}"
                  f"{st['recovery']:>6.2f}")
                ca.assign(data=ca['data'].astype(str)).to_csv(
                    os.path.join(SAIDA, f'trades_{modo}_{gn}_{niv}.csv'),
                    index=False, sep=';', decimal=',')

    # a variante de referencia para todos os estudos de filtro
    ref = tabelas[('fecha', 'parcial')]
    ref_ac = ref[ref['aceito']].copy()

    # ------------------------------------------------------- filtros, um a um
    p('\n[4] FILTROS, MEDIDOS UM A UM (entrada no fechamento, com parcial)')
    estudos = {}

    estudos['concavidade'] = estudo_atributo(
        ref, 'curva', [-9, 0, 9], ['Hull fechando a curva', 'Hull abrindo a curva (concava)'])
    estudos['esticamento'] = estudo_atributo(
        ref, 'estic', [-9, 0.15, 0.45, 0.8, 9],
        ['ate 0,15 ATR', '0,15 a 0,45', '0,45 a 0,80', 'acima de 0,80'])
    estudos['pavio'] = estudo_atributo(
        ref, 'pav_tot', [-1, 25, 45, 65, 90, 999],
        ['ate 25 pts', '25 a 45', '45 a 65', '65 a 90', 'acima de 90'])
    estudos['pavio_favor'] = estudo_atributo(
        ref, 'pav_fav_r', [-0.01, 0.03, 0.06, 0.10, 1],
        ['ate 3% do range', '3 a 6%', '6 a 10%', 'acima de 10%'])
    estudos['pavio_contra'] = estudo_atributo(
        ref, 'pav_con_r', [-0.01, 0.15, 0.30, 0.45, 1],
        ['ate 15% do range', '15 a 30%', '30 a 45%', 'acima de 45%'])
    estudos['retracao_candles'] = estudo_atributo(
        ref, 'n_ret', [0, 1, 2, 3, 99], ['1 candle', '2 candles', '3 candles', '4 ou mais'])
    estudos['retracao_tamanho'] = estudo_atributo(
        ref, 'ret_atr', [-1, 1.0, 1.5, 2.0, 99],
        ['ate 1,0 ATR', '1,0 a 1,5', '1,5 a 2,0', 'acima de 2,0'])
    estudos['inclinacao_hull'] = estudo_atributo(
        ref, 'incl_hma', [-9, 0.05, 0.10, 0.16, 9],
        ['ate 0,05 ATR', '0,05 a 0,10', '0,10 a 0,16', 'acima de 0,16'])
    estudos['inclinacao_ema'] = estudo_atributo(
        ref, 'incl_ema', [-9, 0.0, 0.13, 0.30, 9],
        ['EMA contra', '0 a 0,13 ATR', '0,13 a 0,30', 'acima de 0,30'])
    estudos['banda_keltner'] = estudo_atributo(
        ref, 'folga_banda', [-9, 1.8, 2.3, 2.9, 99],
        ['Hull a menos de 1,8 ATR da banda', '1,8 a 2,3', '2,3 a 2,9', 'acima de 2,9'])
    estudos['hull_colada'] = estudo_atributo(
        ref, 'barras_colada', [-1, 0, 3, 8, 99],
        ['solta da EMA', '1 a 3 candles colada', '4 a 8', 'mais de 8'])
    estudos['hora'] = estudo_atributo(
        ref, 'hora', [8, 10, 11, 12, 13, 15, 19],
        ['9h-10h (pre-abertura a vista)', '10h-11h', '11h-12h', '12h-13h',
         '13h-15h', 'depois das 15h'])

    for nome, bl in estudos.items():
        p(f"\n    -- {nome}")
        for r in bl:
            tt = ' '.join(f"{v:6.1f}" if v is not None else '     .'
                          for v in r['ev_terco'])
            p(f"       {r['faixa']:<32} n={r['n']:>4}  EV={r['ev']:>6.1f}  "
              f"win={r['wr']:>5.1f}%   por terco: {tt}")

    # ------------------------------------------------- o veto de exaustao 2D
    p('\n[5] O VETO DE EXAUSTAO (concavidade x esticamento)')
    cruz = []
    for cv, rcv in ((False, 'Hull fechando a curva'), (True, 'Hull abrindo a curva')):
        linha = []
        for es, res in ((False, f'perto da EMA (ate {S.ESTIC_EXAUSTAO:.2f} ATR)'),
                        (True, 'esticado da EMA')):
            g = ref_ac[((ref_ac['curva'] > 0) == cv) &
                       ((ref_ac['estic'] > S.ESTIC_EXAUSTAO) == es)]
            linha.append(dict(col=res, n=int(len(g)),
                              ev=float(g['pts'].mean()) if len(g) else None,
                              wr=float((g['pts'] > 0).mean() * 100) if len(g) else None))
        cruz.append(dict(lin=rcv, celulas=linha))
    for r in cruz:
        for c in r['celulas']:
            p(f"    {r['lin']:<24} x {c['col']:<34} n={c['n']:>4}  EV={c['ev']:>6.1f}")
    estudos['cruz_exaustao'] = cruz

    # ------------------------------------------------------- niveis por terco
    p('\n[6] OS TRES NIVEIS, TERCO A TERCO (entrada no fechamento, com parcial)')
    niveis_terco = []
    for niv in S.NIVEIS:
        sel = S.seleciona(ref_ac, niv)
        por = []
        for tn, g in sel.groupby('terco', observed=True):
            por.append(dict(terco=tn, n=int(len(g)), ev=float(g['pts'].mean())))
        niveis_terco.append(dict(nivel=niv, n=int(len(sel)),
                                 ev=float(sel['pts'].mean()),
                                 wr=float((sel['pts'] > 0).mean() * 100),
                                 por_terco=por))
        tt = ' | '.join(f"{x['terco']} n={x['n']:>3} EV={x['ev']:>6.1f}" for x in por)
        p(f"    {S.ROTULO[niv]:<8} n={len(sel):>4}  EV={sel['pts'].mean():>6.1f}  {tt}")

    # ------------------------------------------------------ grade stop x alvo
    p('\n[7] GRADE STOP x ALVO (nivel Ouro, entrada no fechamento)')
    stops = [50, 75, 100, 125, 150, 200, 250, 300]
    alvos = [100, 150, 200, 250, 300, 400, 500, 600]
    grade = {'stops': stops, 'alvos': alvos, 'parcial': [], 'puro': []}
    for gn, gcfg in (('puro', dict(parcial=False)), ('parcial', dict(parcial=True))):
        p(f"\n    -- {gn}   (EV em pontos | win% | EV por ponto de risco)")
        p('      stop  ' + ''.join(f'{a:>17}' for a in alvos))
        for st in stops:
            linha = []
            txt = f'      {st:>4}  '
            for al in alvos:
                cfg = dict(gcfg); cfg.update(stop=st, alvo=al,
                                             parcial_em=min(100.0, st))
                t = S.anota(E.executa(d, sc, 'fecha', cfg))
                sel = S.seleciona(t[t['aceito']], 'ouro')
                ev = float(sel['pts'].mean()); wr = float((sel['pts'] > 0).mean() * 100)
                linha.append(dict(stop=st, alvo=al, ev=ev, wr=wr,
                                  ev_risco=ev / st, n=int(len(sel)),
                                  pts=float(sel['pts'].sum())))
                txt += f'{ev:>7.1f}|{wr:>3.0f}|{ev / st:>5.2f}'
            grade[gn].append(linha)
            p(txt)

    # ------------------------------------------ relacao risco : retorno
    # O CLAUDE.md pede o 1:3 com parcial; o 1:2 sem parcial foi pedido
    # depois. A diagonal abaixo mede o mesmo alvo RELATIVO em varios
    # tamanhos de stop -- e a unica forma justa de comparar 1:1, 1:2 e 1:3,
    # porque o alvo em pontos nao quer dizer nada sem o stop ao lado.
    p('\n[7b] RELACAO RISCO : RETORNO (nivel Ouro, sem parcial)')
    p(f"      {'stop':>6}" + ''.join(f"{('1:' + str(r)):>26}" for r in (1, 2, 3, 4)))
    rr = []
    for st in stops:
        linha = []
        txt = f'      {st:>6}'
        for razao in (1, 2, 3, 4):
            t = S.anota(E.executa(d, sc, 'fecha',
                                  dict(parcial=False, stop=st, alvo=st * razao)))
            t, _, _ = marca_tercos(t, dias)
            sel = S.seleciona(t[t['aceito']], 'ouro')
            ca = E.carteira(sel)
            st_ = E.estatisticas(ca)
            por = [dict(terco=tn, n=int(len(gg)), ev=float(gg['pts'].mean()))
                   for tn, gg in sel.groupby('terco', observed=True)]
            linha.append(dict(stop=st, razao=razao, alvo=st * razao,
                              ev=float(sel['pts'].mean()),
                              wr=float((sel['pts'] > 0).mean() * 100),
                              ev_risco=float(sel['pts'].mean()) / st,
                              n=int(len(sel)), pts=st_['lucro_liq'],
                              dd=st_['dd_max'], fl=st_['fator_lucro'],
                              por_terco=por,
                              padrao=(st == int(E.STOP) and razao == 3)))
            txt += (f"  EV{linha[-1]['ev']:7.1f} w{linha[-1]['wr']:3.0f}%"
                    f" r{linha[-1]['ev_risco']:5.2f}")
        rr.append(linha)
        p(txt)
    p('      (r = pontos ganhos por ponto de risco -- o unico numero'
      ' comparavel entre stops diferentes)')


    # ------------------------------------------------ periodos de media movel
    p('\n[8] PERIODOS DE MEDIA (a EMA e sempre o meio do Keltner)')
    p(f"      {'EMA/ATR':>8}{'Hull':>6}{'N base':>8}{'EV base':>9}"
      f"{'N ouro':>8}{'EV ouro':>9}{'pts ouro':>10}")
    medias = []
    ema0, hma0, atr0 = E.EMA_PER, E.HMA_PER, E.ATR_PER
    for ep in (14, 21, 34):
        for hp in (21, 34, 50, 80):
            E.EMA_PER, E.HMA_PER, E.ATR_PER = ep, hp, ep
            dd = E.indicadores(d0)
            ss = E.sinais(dd, False)
            tt = S.anota(E.executa(dd, ss, 'fecha', dict(parcial=True)))
            tt = tt[tt['aceito']]
            oo = S.seleciona(tt, 'ouro')
            r = dict(ema=ep, hull=hp, n_base=int(len(tt)),
                     ev_base=float(tt['pts'].mean()),
                     n_ouro=int(len(oo)), ev_ouro=float(oo['pts'].mean()),
                     pts_ouro=float(oo['pts'].sum()),
                     padrao=(ep == 21 and hp == 50))
            medias.append(r)
            p(f"      {ep:>8}{hp:>6}{r['n_base']:>8}{r['ev_base']:>9.1f}"
              f"{r['n_ouro']:>8}{r['ev_ouro']:>9.1f}{r['pts_ouro']:>10.0f}"
              + ('   <- o do CLAUDE.md' if r['padrao'] else ''))
    E.EMA_PER, E.HMA_PER, E.ATR_PER = ema0, hma0, atr0

    # ---------------------------------------------------------- custos
    p('\n[9] CUSTO POR TRADE (ida e volta, em pontos)')
    custos = []
    for cp in (0, 2, 5, 10, 15, 20):
        t = S.anota(E.executa(d, sc, 'fecha', dict(parcial=True, custo=float(cp))))
        ca = E.carteira(S.seleciona(t[t['aceito']], 'ouro'))
        st = E.estatisticas(ca)
        custos.append(dict(custo=cp, ev=st['exp_pts'], total=st['lucro_liq'],
                           total_rs=st['lucro_liq_rs'], fl=st['fator_lucro'],
                           dd=st['dd_max']))
        p(f"      {cp:>3} pts (R$ {cp * E.VAL_PONTO:>5.2f})   "
          f"EV={st['exp_pts']:>6.1f}  total={st['lucro_liq']:>7.0f} pts  "
          f"FL={st['fator_lucro']:>5.2f}")

    # ----------------------------------------------------------- monte carlo
    p('\n[10] MONTE CARLO (4.000 reamostragens dos trades)')
    mc = {}
    for chave in ('fecha|parcial|ouro', 'fecha|parcial|prata', 'fecha|parcial|bronze',
                  'fecha|puro|ouro', 'fecha|r2|ouro'):
        if chave not in variantes:
            continue
        pts = np.array([r['pts'] for r in variantes[chave]['trades']])
        mc[chave] = monte_carlo(pts)
        m = mc[chave]
        p(f"      {chave:<24} mediana={m['total_mediana']:>7.0f} pts   "
          f"p05={m['total_p05']:>7.0f}   p95={m['total_p95']:>7.0f}   "
          f"prob. de lucro={m['prob_lucro']:>5.1f}%   DD p95={m['dd_p95']:>6.0f}")

    # ------------------------------------------------------------ galeria
    p('\n[12] GALERIA DE EXEMPLOS')
    gal = galeria(E.carteira(ref_ac), 6)
    for niv, itens in gal.items():
        p(f"      {S.ROTULO[niv]:<8} {len(itens)} exemplos: "
          + ', '.join(f"{x['data']} {'C' if x['lado'] > 0 else 'V'} "
                      f"{x['pts']:+.0f}" for x in itens))

    # ------------------------------------------------------- resultado diario
    escolhida = 'fecha|parcial|ouro'
    tr = pd.DataFrame(variantes[escolhida]['trades'])
    tr['data'] = pd.to_datetime(tr['data'], format='%d/%m/%Y %H:%M:%S')
    diario = tr.groupby(tr['data'].dt.date)['pts'].agg(['count', 'sum'])
    p(f'\n[11] DIA A DIA DA VARIANTE ESCOLHIDA ({escolhida})')
    p(f"      pregoes com trade: {len(diario)} de {len(dias)}")
    p(f"      dias positivos: {int((diario['sum'] > 0).sum())}  "
      f"negativos: {int((diario['sum'] < 0).sum())}  "
      f"zerados: {int((diario['sum'] == 0).sum())}")
    p(f"      melhor dia: {diario['sum'].max():.0f} pts   "
      f"pior dia: {diario['sum'].min():.0f} pts   "
      f"media: {diario['sum'].mean():.1f} pts")

    # ------------------------------------------------ fora da amostra original
    #  Os cortes de estrategia.py foram escolhidos na base antiga (06/08 a
    #  11/09). Tudo o que esta fora dessa janela e teste de verdade.
    p('\n[13] FORA DA AMOSTRA ORIGINAL (regras escolhidas em 06/08 a 11/09)')
    oos = dict(blocos={}, meses={}, regime=PR.regime(d), rot=PR.ROT_BLOCO,
               orig_ini=str(PR.ORIG_INI.date()), orig_fim=str(PR.ORIG_FIM.date()))
    for (modo, gn), t in tabelas.items():
        for niv in S.NIVEIS:
            if modo == 'antecipa' and niv == 'ouro':
                continue
            sel = S.seleciona(t[t['aceito']], niv)
            chave = f'{modo}|{gn}|{niv}'
            oos['blocos'][chave] = dict(sinais=PR.por_bloco(sel),
                                        carteira=PR.por_bloco(E.carteira(sel)))
            oos['meses'][chave] = PR.por_mes(sel)
    for modo in MODOS:
        for niv in S.NIVEIS:
            b = oos['blocos'].get(f'{modo}|parcial|{niv}')
            if b:
                s_ = b['sinais']
                p(f"    {modo:<9}{niv:<7} antes {PR.linha_txt(s_['antes'])} | "
                  f"original {PR.linha_txt(s_['original'])} | depois {PR.linha_txt(s_['depois'])}")
    p('    por mes (fecha, parcial):')
    for niv in S.NIVEIS:
        p(f"      {niv:<7}" + '  '.join(f"{m['mes'][5:]} {m['ev']:+5.1f}({m['n']})"
                                   for m in oos['meses'][f'fecha|parcial|{niv}']))
    #  os filtros medidos SO fora da amostra original
    fora_ref = ref_ac[PR.bloco(ref_ac['data']) != 'original']
    oos['filtros_fora'] = {
        'pavio': estudo_atributo(fora_ref.assign(aceito=True), 'pav_tot',
                                 [-1, 25, 45, 65, 90, 999],
                                 ['ate 25 pts', '25 a 45', '45 a 65', '65 a 90', 'acima de 90']),
        'retracao_candles': estudo_atributo(fora_ref.assign(aceito=True), 'n_ret', [0, 1, 2, 3, 99],
                                            ['1 candle', '2 candles', '3 candles', '4 ou mais']),
    }
    cz_f = []
    for cv in (False, True):
        for es in (False, True):
            g = fora_ref[((fora_ref['curva'] > 0) == cv) & ((fora_ref['estic'] > S.ESTIC_EXAUSTAO) == es)]
            cz_f.append(dict(concava=cv, esticado=es, n=int(len(g)),
                             ev=float(g['pts'].mean()) if len(g) else None))
    oos['cruz_fora'] = cz_f

    # ------------------------------------------ a entrada antecipada e o caminho
    p('\n[14] ANTECIPADA: SENSIBILIDADE AO CAMINHO DENTRO DO CANDLE DE ENTRADA')
    oos['antecipa'] = cenarios_antecipa(d, tabelas, p)

    # --------------------------------------------------------------- numeros
    #  que o texto do relatorio cita -- calculados, nunca digitados
    sem_veto = ref.assign(aceito=ref['aceito'] & ~ref['exaustao'])
    estudos['extra'] = dict(
        n_veto=int(cruz[1]['celulas'][1]['n']),
        corr_ema_estic=float(ref_ac['incl_ema'].corr(ref_ac['estic'])),
        incl_ema_sem_veto=estudo_atributo(sem_veto, 'incl_ema', [-9, 0.0, 0.13, 0.30, 9],
                                          ['EMA contra', '0 a 0,13 ATR', '0,13 a 0,30', 'acima de 0,30']),
    )

    # --------------------------------------------------------------- candles
    # amostra de candles com indicadores, para o grafico Kline do relatorio
    # O eixo do grafico de candles e SINTETICO -- um minuto por barra. No
    # grafico de PI duas barras podem fechar no mesmo milissegundo, e o
    # klinecharts exige carimbo estritamente crescente. O horario de
    # verdade vai junto, em texto, e e o que aparece no eixo e na dica.
    cols = ['o', 'h', 'l', 'c', 'hma', 'ema', 'kc_sup', 'kc_inf']
    candles = d[cols].round(2).astype(object).where(pd.notna(d[cols]), None)
    candles = candles.to_dict('list')
    candles['dt'] = d['data'].dt.strftime('%d/%m %H:%M').tolist()

    # ------------------------------------------------- agressao e tendencia
    #  As duas perguntas do estudo de fluxo, com controle de busca. Roda por
    #  ultimo porque nao alimenta nenhuma outra secao -- e um veredito, nao
    #  um insumo.
    p('')
    p('=' * 72)
    p('FLUXO (agressao/tempo) E FORCA DE TENDENCIA')
    p('=' * 72)
    fluxo = FX.roda(p)

    saida = dict(
        auditoria=aud, fluxo=fluxo, oos=oos,
        parametros=dict(
            ema=E.EMA_PER, hull=E.HMA_PER, atr=E.ATR_PER, desvio=E.KELT_DESV,
            stop=E.STOP, alvo=E.ALVO, parcial_em=E.PARCIAL_EM,
            frac=E.FRAC_PARCIAL, apos=E.STOP_APOS_PARCIAL,
            max_barras=E.MAX_BARRAS, fecha_dia=E.FECHA_NO_DIA,
            val_ponto=E.VAL_PONTO, pi=E.PI_PONTOS,
            estic_exaustao=S.ESTIC_EXAUSTAO, n_ret_min=S.N_RET_MIN,
            pavio_min=S.PAVIO_MIN, pavio_max=S.PAVIO_MAX,
        ),
        n_sinais=dict(confirmados=int(len(sc)), antecipados=int(len(sa))),
        variantes=variantes, estudos=estudos, niveis_terco=niveis_terco,
        grade=grade, rr=rr, medias=medias, custos=custos, monte_carlo=mc,
        escolhida=escolhida,
        diario=[dict(dia=str(k), n=int(v['count']), pts=float(v['sum']))
                for k, v in diario.iterrows()],
        descricao=S.descricao(), rotulo=S.ROTULO, galeria=gal,
        # o que cada gestao vale em pontos -- o grafico desenha os niveis
        # a partir daqui, entao trocar a gestao troca as linhas na tela
        gestoes={k: dict(stop=g.get('stop', E.STOP), alvo=g.get('alvo', E.ALVO),
                         parcial=g.get('parcial', E.PARCIAL),
                         parcial_em=g.get('parcial_em', E.PARCIAL_EM),
                         rot=ROT_GESTAO[k])
                 for k, g in GESTOES.items()},
        candles=candles,
    )

    with open(os.path.join(SAIDA, 'resumo.json'), 'w', encoding='utf-8') as f:
        json.dump(_lim(saida), f, ensure_ascii=False)
    p(f"\n[OK] saida/resumo.json  ({os.path.getsize(os.path.join(SAIDA, 'resumo.json')) / 1e6:.1f} MB)")

    with open(os.path.join(SAIDA, 'console.txt'), 'w', encoding='utf-8') as f:
        f.write(_buf.getvalue())
    p('[OK] saida/console.txt')


if __name__ == '__main__':
    main()
