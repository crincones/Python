# -*- coding: utf-8 -*-
"""
Confere Robo-NTSL/MomentumPI_OuroPrata_Robo.ntsl contra a engine.

    python Robo-NTSL/valida_robo.py

Nao e teste de estrategia: e teste de TRADUCAO. Duas partes:

  1. SINAL. As secoes 1 a 3 do .ntsl transcritas linha a linha -- mesmo
     laco barra a barra, mesmas series proprias (ATR recursivo a partir
     de zero, contagem incremental de candles), mesma ordem de testes --
     e comparadas com o que engine.sinais() + estrategia.anota()
     classificaram como Ouro e Prata.

  2. SEQUENCIAMENTO. A maquina de estados da secao 4 (tinhaPos,
     nBarraSaida, uma posicao por vez) rodada sobre os DESFECHOS da
     propria engine e comparada com a carteira do relatorio. O
     preenchimento de ordem em si so o Profit simula; o que se confere
     aqui e se o robo escolheria os mesmos trades.
"""
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import engine as E          # noqa: E402
import estrategia as S      # noqa: E402

# inputs do .ntsl
PERIODO_HULL, PERIODO_EMA, PERIODO_ATR = 50, 21, 21
RETRACAO_MIN, ESTIC, PAV_MIN, PAV_MAX = 2, 0.45, 25, 90


def porta_sinal(d):
    """Secoes 1 a 3 do .ntsl. Devolve nivel (0/1/2) e lado por barra."""
    O = d['o'].to_numpy(); H = d['h'].to_numpy()
    L = d['l'].to_numpy(); C = d['c'].to_numpy()
    DIA = d['dia'].to_numpy()
    hull = E.hma(C, PERIODO_HULL)
    ema = d['ema'].to_numpy()              # MediaExp(21, Close) -- conferida contra a Nelogica
    n = len(d)
    pc = np.r_[C[0], C[:-1]]
    TR = np.maximum(H - L, np.maximum(np.abs(H - pc), np.abs(L - pc)))

    nivel = np.zeros(n, dtype=int); lado_ = np.zeros(n, dtype=int)
    atrE = 0.0; sent = 0; corrida = 0
    k_atr = 2 / (PERIODO_ATR + 1)
    for b in range(n):
        # --- 2. series proprias
        atrAnt = atrE
        atrE = TR[b] * k_atr + atrAnt * (1 - k_atr)
        sentAnt, corridaAnt = sent, corrida
        sent = 1 if C[b] > O[b] else (-1 if C[b] < O[b] else 0)
        corrida = corridaAnt + 1 if sent == sentAnt else 1

        # --- 3. sinal
        if b < PERIODO_HULL + 10:
            continue
        lado = 0
        if C[b] > O[b] and C[b - 1] < O[b - 1]:
            lado = 1
        elif C[b] < O[b] and C[b - 1] > O[b - 1]:
            lado = -1
        if lado == 0 or DIA[b] != DIA[b - 1]:
            continue
        h0, h1, h2 = hull[b], hull[b - 1], hull[b - 2]
        if np.isnan(h2):
            continue
        if lado == 1:
            hullOk = (h0 > h1) and (H[b] > h0) and (H[b - 1] > h1)
        else:
            hullOk = (h0 < h1) and (L[b] < h0) and (L[b - 1] < h1)
        topo = max(H[b], H[b - 1]); fundo = min(L[b], L[b - 1])
        emaOk = fundo <= ema[b] <= topo
        if not (hullOk and emaOk):
            continue
        retOk = corridaAnt >= RETRACAO_MIN
        curva = (h0 - 2 * h1 + h2) * lado
        dist = (C[b] - ema[b]) * lado
        exaustao = (curva > 0) and (atrE > 0) and (dist > ESTIC * atrE)
        pavio = (H[b] - L[b]) - abs(C[b] - O[b])
        geomOk = PAV_MIN <= pavio <= PAV_MAX
        if retOk and not exaustao:
            nivel[b] = 2 if geomOk else 1
            lado_[b] = lado
    return nivel, lado_


def porta_sequencia(sinais, desfecho, n_barras):
    """Secao 4.1, 4.2 e 4.4 do .ntsl sobre os desfechos da engine.

    sinais: {barra: lado} das barras com sinal operavel.
    desfecho: {barra do sinal: barra de saida} (i_sai da engine).
    A posicao existe no FECHAMENTO da barra b se i_ent+1 <= b < i_sai
    (entra na abertura de i_ent+1, sai durante i_sai).
    """
    aceitos = []
    tinhaPos = False; nBarraSaida = -1
    pos_ate = None; pos_de = None
    for b in range(n_barras):
        hasPos = pos_de is not None and pos_de <= b < pos_ate
        if tinhaPos and not hasPos:
            nBarraSaida = b
        if pos_ate is not None and b >= pos_ate:
            pos_de = pos_ate = None
        if (not hasPos) and (not tinhaPos) and (b in sinais) and b > nBarraSaida:
            aceitos.append(b)
            pos_de, pos_ate = b + 1, desfecho[b]
            if pos_ate <= pos_de:            # abre e fecha na mesma barra
                nBarraSaida = pos_ate        # o robo nunca "ve" essa posicao
                pos_de = pos_ate = None
        tinhaPos = hasPos
    return aceitos


def main():
    d = E.indicadores(E.carrega())
    print('=' * 70)
    print('CONFERENCIA  MomentumPI_OuroPrata_Robo.ntsl  x  engine.py')
    print('=' * 70)

    # ---------------------------------------------------------- 1. sinal
    t = S.anota(E.executa(d, E.sinais(d, False), 'fecha', dict(parcial=True)))
    eng = {}
    for r in t.itertuples(index=False):
        if r.e_prata:
            eng[(int(r.i), int(r.lado))] = 2 if r.e_ouro else 1
    niv, lado = porta_sinal(d)
    rob = {(int(i), int(lado[i])): int(niv[i]) for i in np.nonzero(niv)[0]}

    comum = set(eng) & set(rob)
    so_eng = sorted(set(eng) - set(rob)); so_rob = sorted(set(rob) - set(eng))
    dif = sorted(k for k in comum if eng[k] != rob[k])
    print(f"\n[1] SINAL (Ouro + Prata)")
    print(f"    engine {len(eng)} ({sum(v == 2 for v in eng.values())} Ouro)   "
          f"robo {len(rob)} ({sum(v == 2 for v in rob.values())} Ouro)")
    print(f"    em comum {len(comum)}   so na engine {len(so_eng)}   "
          f"so no robo {len(so_rob)}   nivel diferente {len(dif)}")
    for rot, lista in (('so na engine', so_eng), ('so no robo', so_rob), ('nivel diferente', dif)):
        for k in lista[:10]:
            print(f"      {rot}: barra {k[0]} lado {k[1]:+d}  "
                  f"engine={eng.get(k)} robo={rob.get(k)}")

    # ---------------------------------------------------- 2. sequenciamento
    print(f"\n[2] SEQUENCIAMENTO (uma posicao por vez)")
    for nivel_min, rot in ((2, 'Ouro'), (1, 'Ouro + Prata')):
        sel = t[t['e_ouro']] if nivel_min == 2 else t[t['e_prata']]
        cart = E.carteira(sel)
        sinais = {int(r.i): int(r.lado) for r in sel.itertuples()}
        desf = {int(r.i): int(r.i_sai) for r in sel.itertuples()}
        aceitos = porta_sequencia(sinais, desf, len(d))
        ce = [int(x) for x in cart['i']]
        igual = aceitos == ce
        print(f"    {rot:13s} carteira da engine {len(ce)} trades   robo {len(aceitos)}   "
              f"mesma lista: {igual}")
        if not igual:
            a, b = set(aceitos), set(ce)
            print(f"      so no robo: {sorted(a - b)[:10]}   so na engine: {sorted(b - a)[:10]}")
        # o que o horario do robo tira [R4d]
        horas = d['data'].to_numpy()[ce]
        tarde = sum(1 for h in horas if (h.astype('datetime64[m]').astype(object).hour * 100 +
                                         h.astype('datetime64[m]').astype(object).minute) >= 1815)
        print(f"      sinais da carteira com carimbo a partir das 18:15: {tarde}")

    ok = not so_eng and not so_rob and not dif
    print('\n' + '=' * 70)
    print('OK -- o robo sinaliza as MESMAS barras que a engine.' if ok else
          'ATENCAO -- ha divergencias de sinal; ver acima.')
    print('=' * 70)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
