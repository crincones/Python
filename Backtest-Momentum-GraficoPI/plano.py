# -*- coding: utf-8 -*-
"""
Escreve plano.html e PLANO.md -- o plano operacional do setup.

    python rodar.py && python relatorio.py && python plano.py

O relatorio responde "isso funciona?". O plano responde "o que eu faco na
frente da tela?". Por isso ele e curto, esta na ordem em que se olha para
o grafico, e nao repete estatistica que nao muda decisao.
"""
import json
import os

import molde
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
def gatilhos(P):
    """Os passos, na ordem em que se olha para a tela.

    Cada passo e uma pergunta de sim ou nao. Se qualquer uma der nao, o
    trade nao existe -- nao ha 'quase'.
    """
    return [
        dict(
            num=1, titulo='A Hull 50 esta no sentido do trade?',
            regra='Para comprar, a Hull tem de estar <b>subindo</b> e ficar '
                  '<b>abaixo</b> do preco. Para vender, descendo e acima.',
            porque='E a unica coisa que define de que lado se opera. Sem ela nao '
                   'ha "continuacao" de coisa nenhuma.',
            veta='Hull plana, ou preco do lado errado dela.'),
        dict(
            num=2, titulo='Houve uma retracao de 2 ou mais candles?',
            regra='Conte os candles <b>contra</b> a tendencia antes do candle atual. '
                  f"Precisa de <b>{P['n_ret_min']} ou mais</b>.",
            porque='Um candle so de retracao mede menos da metade de dois. '
                   'Um candle contra e ruido; dois ja sao um movimento.',
            veta='Retracao de um candle so. Espere a proxima.'),
        dict(
            num=3, titulo='Os dois extremos do par estao fora da Hull?',
            regra='O topo do ultimo candle da retracao <b>e</b> o topo do candle de '
                  'continuacao, os dois acima da Hull (numa compra). Na venda, os '
                  'dois fundos abaixo dela.',
            porque='E o que separa um pullback dentro da tendencia de uma virada '
                   'que ja atravessou a media.',
            veta='Qualquer um dos dois extremos do lado de dentro da Hull.'),
        dict(
            num=4, titulo='A EMA 21 passa entre os topos e os fundos do par?',
            regra='A EMA 21 tem de estar <b>dentro</b> da faixa que vai do menor '
                  'fundo ao maior topo dos dois candles.',
            porque='E a forma de exigir que a retracao tenha ido ate a media -- nem '
                   'menos (nao retraiu), nem mais (nao e mais retracao).',
            veta='EMA acima do par inteiro ou abaixo dele.'),
        dict(
            num=5, titulo='NAO e exaustao?', veto=True,
            regra='Descarte se as <b>duas</b> coisas forem verdade ao mesmo tempo: a '
                  'Hull esta <b>abrindo a curva</b> a favor do trade (acelerando) '
                  '<b>e</b> o fechamento ja esta a mais de '
                  f"<b>{n(P['estic_exaustao'], 2)} ATR</b> da EMA 21 "
                  f"(com ATR perto de 150, isso e mais ou menos "
                  f"<b>{n(P['estic_exaustao'] * 150)} pontos</b>).",
            porque='E o filtro que mais separa. Sozinha, nenhuma das duas metades '
                   'diz quase nada; juntas marcam 4 de cada 10 sinais, e esses 4 '
                   'nao pagam. E a intuicao da "Hull perto da banda", so que medida '
                   'no lugar certo.',
            veta='Hull acelerando E preco ja esticado. E o unico veto obrigatorio.'),
        dict(
            num=6, titulo='O candle de continuacao tem a forma certa?',
            regra='Pavio total (range menos os 100 pontos do corpo) entre '
                  f"<b>{n(P['pavio_min'])}</b> e <b>{n(P['pavio_max'])}</b> pontos. "
                  'Na pratica: o range do candle entre '
                  f"{n(100 + P['pavio_min'])} e {n(100 + P['pavio_max'])} pontos.",
            porque='No grafico de PI o corpo e sempre 100 pontos, entao o pavio E a '
                   'forma. Candle liso demais e fino demais para pagar; candle de '
                   'pavio enorme e briga, nao continuacao.',
            veta='Este e o que separa Ouro de Prata. Falhando so ele, o sinal ainda '
                 'e Prata -- opere menor, ou nao opere.'),
    ]


def niveis_tabela(D):
    out = []
    for k in ('ouro', 'prata', 'bronze'):
        v = D['variantes'][f'fecha|parcial|{k}']['stats']
        nt = {x['nivel']: x for x in D['niveis_terco']}[k]
        out.append(dict(
            nivel=k, rot=D['rotulo'][k],
            passos={'ouro': '1 a 6, todos', 'prata': '1 a 5 (falha so o 6)',
                    'bronze': '1 a 4 (falha o veto de exaustao)'}[k],
            ev=nt['ev'], n=nt['n'], wr=v['winrate'], dd=v['dd_max'],
            dia=v['trades_dia'],
            acao={'ouro': 'Opere.',
                  'prata': 'Opere com metade do tamanho, ou deixe passar.',
                  'bronze': 'Nao opere.'}[k]))
    return out



def galeria_enxuta(D, nivel='ouro'):
    """So os candles que a galeria do plano precisa, reindexados.

    O relatorio embute os 10.000 candles porque tem o grafico trade a
    trade; o plano nao tem, e nao ha razao para ele carregar 1,3 MB para
    desenhar seis miniaturas. Aqui ficam so as janelas dos exemplos, com
    os indices remapeados para o recorte.
    """
    exs = D['galeria'].get(nivel, [])
    if not exs:
        return dict(candles={}, exemplos=[])

    precisa = []
    for ex in exs:
        precisa.extend(range(ex['de'], ex['ate'] + 1))
    ordem = sorted(set(precisa))
    mapa = {velho: novo for novo, velho in enumerate(ordem)}

    C = D['candles']
    campos = ['o', 'h', 'l', 'c', 'hma', 'ema', 'dt']
    compacto = {k: [C[k][i] for i in ordem] for k in campos}
    compacto['kc_sup'] = compacto['kc_inf'] = None

    saida = []
    for ex in exs:
        e = dict(ex)
        for k in ('de', 'ate', 'i_ret', 'i_sin', 'i_ent', 'i_sai'):
            e[k] = mapa[ex[k]]
        saida.append(e)
    return dict(candles=compacto, exemplos=saida)


def main():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        D = json.load(f)
    P = D['parametros']
    s = D['variantes'][D['escolhida']]['stats']
    ctx = dict(D=D, P=P, s=s, gatilhos=gatilhos(P), niveis=niveis_tabela(D),
               n=n, sn=sn, galeria=galeria_enxuta(D))

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
