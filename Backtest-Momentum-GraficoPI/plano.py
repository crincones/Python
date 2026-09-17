# -*- coding: utf-8 -*-
"""
Escreve plano.html e PLANO.md.

    python rodar.py && python candidato.py && python relatorio.py && python plano.py

O relatorio responde "isso funciona?". O plano responde "o que eu faco na
frente da tela?". Na base de 132 pregoes a resposta mudou: o padrao Ouro
nao passou no teste fora da amostra, entao o plano virou (1) o aviso de
suspensao e (2) o protocolo de teste, em simulador, da hipotese da
retracao profunda (candidato.py). Nada aqui e digitado: os numeros saem
de saida/resumo.json.
"""
import json
import math
import os

import pandas as pd

import molde_plano

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')


def n(v, c=0):
    if v is None:
        return '-'
    return f'{v:,.{c}f}'.replace(',', ' ').replace('.', ',').replace(' ', '.')


def sn(v, c=0):
    return ('+' if v and v > 0 else '') + n(v, c)


# ============================================================== o conteudo
def gatilhos(P, C):
    """Os passos, na ordem em que se olha para a tela."""
    return [
        dict(num=1, titulo='A Hull 50 esta no sentido do trade?',
             regra='Para comprar, a Hull tem de estar <b>subindo</b> e <b>abaixo</b> da maxima do '
                   'candle. Para vender, descendo e acima da minima.',
             porque='Define de que lado se opera. No estudo hull_contra, refeito na base nova, a Hull a '
                    'favor foi a unica hipotese previa que passou no teste fora da amostra.',
             veta='Hull plana, ou do lado errado do preco.'),
        dict(num=2, titulo=f"Houve uma retracao de {C['n_ret_min']} ou mais candles?",
             regra=f"Conte os candles <b>seguidos contra</b> a Hull, no mesmo pregao, antes do candle atual. "
                   f"Precisa de <b>{C['n_ret_min']} ou mais</b>.",
             porque='E a hipotese em teste. Com 1 ou 2 candles de retracao a regra-base mediu perto de zero '
                    'nos 132 pregoes; com 3 ou mais, positivo nos dois blocos e nos tres tercos.',
             veta=f"Retracao de 1 ou 2 candles, ou que atravessa a virada do dia."),
        dict(num=3, titulo='O candle atual FECHOU a favor?',
             regra='Espere o candle <b>fechar</b>: alta na compra, baixa na venda. E o candle de continuacao.',
             porque='Antes do fechamento o sinal nao existe, e a entrada antecipada nao pode ser medida com a '
                    'base disponivel.',
             veta='Candle ainda aberto.'),
        dict(num=4, titulo='Os dois extremos do par estao fora da Hull?',
             regra='O topo do ultimo candle da retracao <b>e</b> o topo do candle de continuacao acima da Hull '
                   '(numa compra). Na venda, os dois fundos abaixo dela.',
             porque='Separa um recuo dentro da tendencia de uma virada que ja atravessou a media.',
             veta='Qualquer um dos dois extremos do lado de dentro da Hull.'),
        dict(num=5, titulo='A EMA 21 passa entre os topos e os fundos do par?',
             regra='A EMA 21 tem de estar <b>dentro</b> da faixa do menor fundo ao maior topo dos dois candles.',
             porque='Exige que a retracao tenha ido ate a media.',
             veta='EMA acima do par inteiro ou abaixo dele.'),
    ]


def galeria_r3(D, k=6):
    """Seis operacoes do candidato espalhadas no tempo, com os candles do recorte."""
    tr = D['variantes']['fecha|parcial|r3']['trades']
    if not tr:
        return dict(candles={}, exemplos=[])
    idx = sorted({round(j * (len(tr) - 1) / (k - 1)) for j in range(k)})
    if not any(tr[i]['pts'] < 0 for i in idx):
        idx[-2] = next(i for i in range(idx[-2], len(tr)) if tr[i]['pts'] < 0)
    if not any(tr[i]['pts'] > 0 for i in idx):
        idx[1] = next(i for i in range(idx[1], len(tr)) if tr[i]['pts'] > 0)
    exs = []
    for i in sorted(set(idx)):
        t = tr[i]
        exs.append(dict(de=max(0, t['i_ret'] - 11), ate=t['i_sai'] + 3, i_ret=t['i_ret'], i_sin=t['i_sin'],
                        i_ent=t['i_ent'], i_sai=t['i_sai'], lado=t['lado'], pts=t['pts'],
                        preco_ent=t['preco_ent'], data=t['data'][:5] + ' ' + t['data'][-5:],
                        rot_saida=t['rot_saida'], n_ret=t['n_ret'], pav_tot=t['pav_tot'], nivel='r3'))
    ordem = sorted({j for e in exs for j in range(e['de'], e['ate'] + 1)})
    mapa = {v: j for j, v in enumerate(ordem)}
    C = D['candles']
    comp = {c: [C[c][j] for j in ordem] for c in ('o', 'h', 'l', 'c', 'hma', 'ema', 'dt')}
    comp['kc_sup'] = comp['kc_inf'] = None
    for e in exs:
        for c in ('de', 'ate', 'i_ret', 'i_sin', 'i_ent', 'i_sai'):
            e[c] = mapa[e[c]]
    return dict(candles=comp, exemplos=exs)


def protocolo(D, custo_suposto=5.0):
    """Tamanho do teste e criterios de parada, calculados do proprio backteste."""
    g = D['candidato']['gestoes']['parcial']
    s = g['stats']
    desvio = s['exp_pts'] / s['sharpe']
    ev_min = s['exp_pts'] - custo_suposto          # o que sobraria depois de um custo tipico
    # t = ev * sqrt(n) / desvio >= 2  =>  n >= (2 * desvio / ev)^2, arredondado para cima
    n_conf = int(math.ceil(math.ceil((2 * desvio / ev_min) ** 2) / 25.0) * 25)
    freq = s['trades'] / D['auditoria']['dias']
    n_parcial = 100
    z = s['exp_pts'] * math.sqrt(n_parcial) / desvio
    p_falso = 0.5 * (1 + math.erf(-z / math.sqrt(2))) * 100
    inicio = (pd.Timestamp(D['auditoria']['ate']) + pd.Timedelta(days=1)).strftime('%d/%m/%Y')
    return dict(desvio=desvio, ev_min=ev_min, custo_suposto=custo_suposto, n_conf=n_conf,
                pregoes_conf=n_conf / freq, n_parcial=n_parcial, p_falso_abandono=p_falso,
                dd_limite=g['mc']['dd_p95'], seq_limite=2 * s['max_seq_perda'], inicio=inicio)


def main():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        D = json.load(f)
    if 'candidato' not in D:
        raise SystemExit('rode antes: python candidato.py')
    P = D['parametros']
    ctx = dict(D=D, P=P, n=n, sn=sn, gatilhos=gatilhos(P, D['candidato']),
               galeria=galeria_r3(D), protocolo=protocolo(D))

    html = molde_plano.monta_html(ctx)
    with open(os.path.join(BASE, 'plano.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[OK] plano.html  ({os.path.getsize(os.path.join(BASE, 'plano.html')) / 1e3:.0f} KB)")

    md = molde_plano.monta_md(ctx)
    with open(os.path.join(BASE, 'PLANO.md'), 'w', encoding='utf-8') as f:
        f.write(md)
    print('[OK] PLANO.md')


if __name__ == '__main__':
    main()
