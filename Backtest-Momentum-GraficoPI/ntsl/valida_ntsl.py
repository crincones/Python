# -*- coding: utf-8 -*-
"""
Confere MomentumPI_OuroPrata.ntsl contra a engine do backteste.

    python ntsl/valida_ntsl.py

O indicador foi escrito a mao a partir de estrategia.py. Este script
transcreve o NTSL de volta para Python -- linha a linha, na mesma ordem,
com os mesmos [p+j] -- e compara barra a barra com o que a engine
classificou. Se os dois discordarem em uma unica barra, o script diz
qual e por que.

Nao e teste de estrategia: e teste de TRADUCAO.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import engine as E          # noqa: E402
import estrategia as S      # noqa: E402


# ======================================================== o NTSL, em python
def porta_ntsl(d, hull, ema, atrV, p=0,
               retracao_min=S.N_RET_MIN, estic_exaustao=S.ESTIC_EXAUSTAO,
               pavio_min=S.PAVIO_MIN, pavio_max=S.PAVIO_MAX):
    """Transcricao literal do bloco `begin ... end` do .ntsl.

    `x[p + j]` no NTSL e a barra p+j candles ATRAS da atual, entao aqui
    vira `x[i - p - j]` com i correndo do presente para o passado. O
    resto e copia: mesma ordem de testes, mesmos nomes.

    Espelha a v2 do .ntsl: ATR so como ESCALA (multiplicacao, nunca
    divisao) e `atrOk` degradando o veto em vez de calar o indicador.
    """
    O = d['o'].to_numpy(); H = d['h'].to_numpy()
    L = d['l'].to_numpy(); C = d['c'].to_numpy()
    DIA = d['dia'].to_numpy()
    n = len(d)

    nivel = np.zeros(n, dtype=int)
    lado_ = np.zeros(n, dtype=int)
    minimo = 50 + 21 + 21 + 12          # PeriodoHull + EMA + ATR + 12

    for i in range(minimo, n):
        b = i - p                        # a barra [p] do NTSL
        if b - 10 < 0 or np.isnan(hull[b - 2]):
            continue
        atrOk = (not np.isnan(atrV[b])) and atrV[b] > 0

        gatC = (C[b] > O[b]) and (C[b - 1] < O[b - 1]) and (DIA[b] == DIA[b - 1])
        gatV = (C[b] < O[b]) and (C[b - 1] > O[b - 1]) and (DIA[b] == DIA[b - 1])
        if not (gatC or gatV):
            continue
        lado = 1 if gatC else -1

        if gatC:
            hullOk = (hull[b] > hull[b - 1]) and (H[b] > hull[b]) \
                     and (H[b - 1] > hull[b - 1])
        else:
            hullOk = (hull[b] < hull[b - 1]) and (L[b] < hull[b]) \
                     and (L[b - 1] < hull[b - 1])

        topo = H[b]
        if H[b - 1] > topo:
            topo = H[b - 1]
        fundo = L[b]
        if L[b - 1] < fundo:
            fundo = L[b - 1]
        emaOk = (ema[b] >= fundo) and (ema[b] <= topo)

        # retracao: barras contra consecutivas terminando em [p+1]
        k = 0
        contando = True
        for j in range(1, 9):
            if contando:
                if DIA[b - j] != DIA[b]:
                    contando = False
                elif gatC and (C[b - j] < O[b - j]):
                    k = j
                elif gatV and (C[b - j] > O[b - j]):
                    k = j
                else:
                    contando = False
        retOk = (k >= retracao_min)

        curva_a_favor = (hull[b] - 2 * hull[b - 1] + hull[b - 2]) * lado
        dist = (C[b] - ema[b]) * lado
        exaustao = ((curva_a_favor > 0) and atrOk
                    and (dist > estic_exaustao * atrV[b]))

        pavio = (H[b] - L[b]) - abs(C[b] - O[b])
        geomOk = (pavio >= pavio_min) and (pavio <= pavio_max)

        if hullOk and emaOk:
            if retOk and (not exaustao):
                nivel[b] = 2 if geomOk else 1
        lado_[b] = lado if (gatC or gatV) else 0

    return nivel, lado_


# ================================================================ conferencia
def main():
    d = E.indicadores(E.carrega())
    hull = d['hma'].to_numpy()
    ema = d['ema'].to_numpy()
    # o .ntsl usa Media(PeriodoATR, TrueRange) -- a media ARITMETICA, que
    # e o idioma comprovado do acervo. A engine usa a exponencial. Medido:
    # correlacao 0,90, diferenca mediana de 2,6 pts. Na base antiga (26
    # pregoes) nenhuma barra mudava de nivel; na de 132 pregoes, 5 em ~1.290,
    # todas com o esticamento a menos de 0,03 ATR do corte do veto.
    H = d['h'].to_numpy(); L = d['l'].to_numpy(); C = d['c'].to_numpy()
    pc = np.r_[C[0], C[:-1]]
    tr = np.maximum(H - L, np.maximum(np.abs(H - pc), np.abs(L - pc)))
    atrV = pd.Series(tr).rolling(E.ATR_PER).mean().to_numpy()

    print('=' * 70)
    print('CONFERENCIA  MomentumPI_OuroPrata.ntsl  x  engine.py')
    print('=' * 70)

    # --- o que a engine diz -------------------------------------------
    sig = S.anota(E.executa(d, E.sinais(d, False), 'fecha', dict(parcial=True)))
    sig = sig[sig['aceito']]
    eng = {}
    for r in sig.itertuples(index=False):
        eng[(int(r.i), int(r.lado))] = 2 if r.e_ouro else (1 if r.e_prata else 0)

    # --- o que o indicador diz ----------------------------------------
    nivel, lado = porta_ntsl(d, hull, ema, atrV, p=0)
    ind = {(i, int(lado[i])): int(nivel[i])
           for i in np.nonzero(lado)[0] if nivel[i] > 0}

    eng_marcado = {k: v for k, v in eng.items() if v > 0}

    print(f"\nengine     : {len(eng)} sinais da regra-base, "
          f"{sum(1 for v in eng.values() if v == 2)} Ouro + "
          f"{sum(1 for v in eng.values() if v == 1)} Prata")
    print(f"indicador  : {len(ind)} setas, "
          f"{sum(1 for v in ind.values() if v == 2)} Ouro + "
          f"{sum(1 for v in ind.values() if v == 1)} Prata")

    so_eng = set(eng_marcado) - set(ind)
    so_ind = set(ind) - set(eng_marcado)
    ambos = set(eng_marcado) & set(ind)
    dif_nivel = {k for k in ambos if eng_marcado[k] != ind[k]}

    print(f"\nem comum             : {len(ambos)}")
    print(f"so na engine         : {len(so_eng)}")
    print(f"so no indicador      : {len(so_ind)}")
    print(f"nivel divergente     : {len(dif_nivel)}")

    problemas = 0
    for rot, conj in (('so na engine', so_eng), ('so no indicador', so_ind)):
        if not conj:
            continue
        print(f"\n--- {rot} ({len(conj)}):")
        for i, ld in sorted(conj)[:12]:
            # por que? a unica diferenca prevista e a contagem da retracao
            # atravessando o fim do pregao
            r = sig[(sig['i'] == i) & (sig['lado'] == ld)]
            n_eng = int(r['n_ret'].iloc[0]) if len(r) else -1
            b = i
            k = 0
            cont = True
            for j in range(1, 9):
                if cont:
                    if d['dia'].iat[b - j] != d['dia'].iat[b]:
                        cont = False
                    elif (ld > 0 and d['c'].iat[b - j] < d['o'].iat[b - j]) or \
                         (ld < 0 and d['c'].iat[b - j] > d['o'].iat[b - j]):
                        k = j
                    else:
                        cont = False
            # o veto de exaustao usa ATR aritmetico no .ntsl e exponencial na
            # engine: um sinal com o esticamento colado no corte pode cair de
            # um lado numa e do outro na outra
            dist = (d['c'].iat[i] - ema[i]) * ld
            lim = S.ESTIC_EXAUSTAO
            atr_troca = (np.isfinite(atrV[i]) and
                         (dist > lim * atrV[i]) != (dist > lim * d['atr'].iat[i]))
            if n_eng != k:
                causa = 'retracao cruza o fim do pregao'
            elif i < 50 + 21 + 21 + 12:
                causa = 'aquecimento: o indicador so comeca na barra 104'
            elif atr_troca:
                causa = (f"ATR aritmetico x exponencial no corte do veto "
                         f"(esticamento {dist / atrV[i]:.3f} x {dist / d['atr'].iat[i]:.3f} ATR)")
            else:
                causa = 'DIVERGENCIA NAO EXPLICADA'
            if causa.startswith('DIVERG'):
                problemas += 1
            print(f"    barra {i:5d} lado {ld:+d}  "
                  f"n_ret engine={n_eng} indicador={k}  -> {causa}")

    for i, ld in sorted(dif_nivel)[:12]:
        print(f"    barra {i:5d} lado {ld:+d}  "
              f"engine={eng_marcado[(i, ld)]} indicador={ind[(i, ld)]}")
        problemas += 1

    # --- a versao defasada, que e a que nunca repinta -----------------
    nivel1, lado1 = porta_ntsl(d, hull, ema, atrV, p=1)
    ind1 = {(i - 1, int(lado1[i - 1])): int(nivel1[i - 1])
            for i in range(1, len(d)) if lado1[i - 1] != 0 and nivel1[i - 1] > 0}
    print(f"\nDefasar(1) marca as mesmas barras: "
          f"{set(ind1) == set(ind)}  ({len(ind1)} setas)")

    print('\n' + '=' * 70)
    if problemas == 0 and len(dif_nivel) == 0:
        print('OK -- o indicador e a engine classificam as MESMAS barras,')
        print('     com o mesmo nivel. As unicas diferencas de conjunto, se')
        print('     houver acima, sao a contagem da retracao parando no fim')
        print('     do pregao, o aquecimento das primeiras barras ou o ATR')
        print('     aritmetico do indicador no corte exato do veto.')
    else:
        print(f'ATENCAO -- {problemas} divergencias sem explicacao.')
    print('=' * 70)
    return 0 if problemas == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
