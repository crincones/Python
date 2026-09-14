# -*- coding: utf-8 -*-
"""
Monta, a partir de saida/hull_contra.json:

    hull_contra.html   relatorio completo
    HULL_CONTRA.md     o mesmo em markdown
    plano_hull.html    plano de trading do candidato
    PLANO_HULL.md      o plano em markdown

    python hull_contra.py && python relatorio_hull.py
"""
import datetime as dt
import json
import os

import molde
import molde_plano
from relatorio_pavio import n, sn, cls, tile, md_n, md_sn, GESTOES_JS

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
VENDOR_KC = os.path.join(BASE, 'vendor', 'klinecharts-9.8.10.min.js')

GES = ('parcial', 'puro', 'r2', 'r1')
ENT = ('fecha', 'meio_lim')
FINAL = 'h23f10'


# ================================================================= numeros
def fatos(D):
    c = D['comparacao']['fecha|parcial']
    F = dict(hull=c['hull'], sem=c['sem'], contra=c['contra'], inv=c['inverso'])
    F['pct'] = [D['sorteio'][f'fecha|{g}']['percentil'] for g in GES]
    F['lados'] = D['lados']['fecha|parcial']
    F['nb'] = {b['faixa']: b for b in D['barras_antes']['fecha|parcial']}
    F['reg'] = {k: D['regras_res'][f'fecha|parcial|{k}'] for k in D['regras']}
    F['reg_pct'] = {k: [D['regras_res'][f'fecha|{g}|{k}']['sorteio']['percentil'] for g in GES]
                    for k in D['regras']}
    F['fin'] = {g: D['candidatos'][f'fecha|{g}|{FINAL}'] for g in GES}
    F['fin_pct'] = [D['candidatos'][f'fecha|{g}|{FINAL}']['sorteio']['percentil'] for g in GES]
    F['cart'] = D['carteira'][f'fecha|parcial|{FINAL}']
    F['cart_h'] = D['carteira']['fecha|parcial|h']
    F['cart_sem'] = D['carteira']['fecha|parcial|sem']
    F['per'] = {b['faixa']: b for b in D['periodos']['fecha|parcial']}
    F['fech'] = {b['faixa']: b for b in D['pavio_fech']['fecha|parcial']}
    return F



# ============================================================ desenho do pavio
def _painel(lado):
    """Um painel SVG do padrao: compra (lado=+1) ou venda (lado=-1).

    Geometria de PI 20: todo corpo mede 100 pts e cada candle abre no
    fechamento do anterior. Os precos abaixo sao da compra; a venda e o
    espelho vertical. O unico pavio destacado e o do FECHAMENTO do candle
    de sinal -- o que a regra avalia.
    """
    W, H = 560, 340
    esc = 0.62                     # px por ponto
    y0 = 206 if lado > 0 else 150  # y do preco 0
    Y = lambda pr: y0 - lado * pr * esc
    # (abertura, fechamento, maxima, minima), em pontos -- compra
    velas = [(0, 100, 108, -4), (100, 200, 212, 96), (200, 100, 205, 92),
             (100, 0, 104, -8), (0, 100, 107, -48)]
    X = lambda i: 40 + i * 56
    lw = 28
    out = [f'<svg class="viz" viewBox="0 0 {W} {H}" role="img" '
           f'aria-label="Pavio avaliado no candle de sinal, {"compra" if lado > 0 else "venda"}">']
    # Hull 50 inclinada a favor
    pts = ' '.join(f'{X(i) + dx:.0f},{Y(pr):.0f}' for i, dx, pr in
                   ((0, -25, -170), (1, 0, -145), (2, 0, -118), (3, 0, -92), (4, 0, -68), (4, 40, -55)))
    out.append(f'<polyline points="{pts}" fill="none" style="stroke:var(--alerta)" '
               'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    out.append(f'<text x="{X(0) - 25}" y="{Y(-170) + (18 if lado > 0 else -8):.0f}" class="eixo-tx" '
               f'style="fill:var(--tinta2)">Hull 50 {"subindo" if lado > 0 else "descendo"}</text>')
    # faixa das barras contra
    ya, yb = sorted((Y(218), Y(-14)))
    out.append(f'<rect x="{X(2) - 21}" y="{ya:.0f}" width="{X(3) - X(2) + 42}" height="{yb - ya:.0f}" '
               'rx="6" style="fill:var(--prata)" fill-opacity=".12"/>')
    yt = ya - 7 if lado > 0 else yb + 15
    out.append(f'<text x="{(X(2) + X(3)) / 2:.0f}" y="{yt:.0f}" text-anchor="middle" class="eixo-tx" '
               'style="fill:var(--tinta2)">2 ou 3 contra a Hull</text>')
    # velas
    for i, (o, c, hi, lo) in enumerate(velas):
        cor = 'var(--ganho)' if c > o else 'var(--perda)'
        if lado < 0:
            cor = 'var(--perda)' if c > o else 'var(--ganho)'
        x = X(i)
        out.append(f'<line x1="{x}" x2="{x}" y1="{Y(hi):.0f}" y2="{Y(lo):.0f}" '
                   f'style="stroke:{cor}" stroke-width="2"/>')
        yc = min(Y(o), Y(c))
        out.append(f'<rect x="{x - lw / 2}" y="{yc:.0f}" width="{lw}" height="{abs(Y(o) - Y(c)):.0f}" '
                   f'rx="2" style="fill:{cor}" fill-opacity="{1 if i == 4 else .5}"/>')
    x = X(4)
    # corpo
    out.append(f'<text x="{x}" y="{(Y(0) + Y(100)) / 2 + 4:.0f}" text-anchor="middle" '
               'style="fill:#fff;font-size:10px;font-weight:700">100</text>')
    # AVALIADO: lado do fechamento
    a, b = sorted((Y(100), Y(107)))
    out.append(f'<rect x="{x - 10}" y="{a - 6:.0f}" width="20" height="{b - a + 12:.0f}" rx="5" '
               'fill="none" style="stroke:var(--tinta)" stroke-width="2.2"/>')
    ym = (a + b) / 2
    out.append(f'<line x1="{x + 11}" x2="{x + 34}" y1="{ym:.0f}" y2="{ym:.0f}" '
               'style="stroke:var(--tinta)" stroke-width="1.5"/>')
    lab = 'pavio de CIMA' if lado > 0 else 'pavio de BAIXO'
    frm = 'maxima - fechamento' if lado > 0 else 'fechamento - minima'
    out.append(f'<text x="{x + 38}" y="{ym - 11:.0f}" style="fill:var(--tinta);font-size:12.5px;'
               f'font-weight:700">AVALIADO: {lab}</text>')
    out.append(f'<text x="{x + 38}" y="{ym + 4:.0f}" style="fill:var(--tinta);font-size:12px">'
               'lado do fechamento (onde se entra)</text>')
    out.append(f'<text x="{x + 38}" y="{ym + 19:.0f}" style="fill:var(--tinta2);font-size:12px">'
               f'{frm} &#8804; 10% do corpo</text>')
    # NAO avaliado: lado da abertura
    a, b = sorted((Y(0), Y(-48)))
    out.append(f'<rect x="{x - 10}" y="{a - 4:.0f}" width="20" height="{b - a + 8:.0f}" rx="5" '
               'fill="none" style="stroke:var(--mudo)" stroke-width="1.5" stroke-dasharray="4 3"/>')
    ym = (a + b) / 2
    out.append(f'<line x1="{x + 11}" x2="{x + 34}" y1="{ym:.0f}" y2="{ym:.0f}" '
               'style="stroke:var(--mudo)" stroke-width="1.2" stroke-dasharray="3 3"/>')
    out.append(f'<text x="{x + 38}" y="{ym - 3:.0f}" style="fill:var(--mudo);font-size:12px;'
               f'font-weight:600">nao avaliado: pavio de {"baixo" if lado > 0 else "cima"}</text>')
    out.append(f'<text x="{x + 38}" y="{ym + 12:.0f}" class="eixo-tx">lado da abertura, qualquer tamanho</text>')
    out.append('<text x="6" y="18" style="fill:var(--tinta);font-size:13px;font-weight:700">'
               f'{"&#9650; COMPRA" if lado > 0 else "&#9660; VENDA"}</text>')
    out.append('</svg>')
    return ''.join(out)


def diagrama_pavio(titulo=True):
    """Os dois paineis, compra e venda, lado a lado (empilham no celular)."""
    cab = ('<h3 style="margin-bottom:4px">Qual pavio e avaliado</h3>'
           '<p class="nota" style="margin-top:0">So o pavio do lado do FECHAMENTO do candle de sinal '
           '&mdash; o candle que volta a favor da Hull, onde a entrada acontece. O do lado da abertura '
           'foi medido no estudo (secao 3), mas nao entrou na regra.</p>') if titulo else ''
    return (f'<div class="card">{cab}<div class="grade g2">'
            f'<figure>{_painel(1)}</figure><figure>{_painel(-1)}</figure></div></div>')


DIAGRAMA_MD = """COMPRA (Hull 50 subindo, 2 ou 3 candles de baixa antes):

```
      |     <- AVALIADO: pavio de CIMA = maxima - fechamento <= 10% do corpo
    +---+   <- fechamento = entrada
    |   |
    |   |      candle de sinal, de ALTA (corpo 100)
    +---+   <- abertura
      |
      |     <- NAO avaliado: pavio de baixo (lado da abertura), qualquer tamanho
```

VENDA (Hull 50 descendo, 2 ou 3 candles de alta antes):

```
      |
      |     <- NAO avaliado: pavio de cima (lado da abertura), qualquer tamanho
    +---+   <- abertura
    |   |
    |   |      candle de sinal, de BAIXA (corpo 100)
    +---+   <- fechamento = entrada
      |     <- AVALIADO: pavio de BAIXO = fechamento - minima <= 10% do corpo
```

O pavio avaliado e sempre o do lado do **fechamento** do candle de sinal: o de cima na compra, o
de baixo na venda. O pavio do lado da abertura nao entra na regra."""


# =================================================================== corpo
def capa(D, F):
    B = D['base']
    return f"""
<header class="capa">
  <div class="chapeu">Backtest &middot; WINFUT &middot; grafico de 20 PI</div>
  <h1>Hull 50 a favor<br>2 a 4 candles e 1 contra</h1>
  <p class="sub">Uma so restricao: a Hull 50 subindo para comprar, descendo para vender.
  Compra quando, com a Hull subindo, vem 2 a 4 candles de baixa e 1 de alta; venda no
  espelho. Dentro dessa condicao, os pavios do candle contra.</p>
  <div style="margin-top:18px">
    <span class="selo">{n(B['barras'])} candles</span>
    <span class="selo">{B['dias']} pregoes, {B['ini']} a {B['fim']}</span>
    <span class="selo">{n(F['hull']['n'])} sinais com Hull a favor</span>
    <span class="selo">stop 100</span>
    <span class="selo">resultado bruto</span>
  </div>
</header>"""


def resposta(D, F):
    fin = F['fin']['parcial']; ct = F['cart']
    return f"""
<section id="resposta">
  <h2>Resposta curta: a Hull muda o jogo</h2>
  <p class="olho">A inclinacao da Hull 50 e o primeiro filtro deste estudo que separa os
  sinais de forma consistente. Com 2 a 4 candles e 1 contra, entrada no fechamento, 1:3 com
  parcial: <b>{sn(F['hull']['ev'], 1)}</b> pts por sinal com a Hull a favor, contra
  <b>{sn(F['contra']['ev'], 1)}</b> com ela contra e <b>{sn(F['sem']['ev'], 1)}</b> sem
  olhar a Hull.</p>
  <div class="grade g4">
    {tile('Hull a favor', sn(F['hull']['ev'], 1), f"pts por sinal &middot; {n(F['hull']['n'])} sinais", cls(F['hull']['ev']))}
    {tile('Hull contra', sn(F['contra']['ev'], 1), f"pts por sinal &middot; {n(F['contra']['n'])} sinais", cls(F['contra']['ev']))}
    {tile('Percentil contra o sorteio', f"{n(min(F['pct']))}&ndash;{n(max(F['pct']))}", 'nas 4 gestoes, entrada no fechamento')}
    {tile('Com os 2 cortes a mais', sn(fin['ev'], 1), f"pts por sinal &middot; {n(fin['n'])} sinais", cls(fin['ev']))}
  </div>
  <div class="bandeira">
    <h3>O que o estudo encontrou</h3>
    <ul class="enx">
      <li><b>A Hull a favor funciona</b> nas 8 combinacoes de entrada e gestao, nos dois
      lados (compra {sn(F['lados']['compra']['ev'], 1)}, venda {sn(F['lados']['venda']['ev'], 1)}),
      e com Hull 34 tambem. Hull 21 e 80 medem pior.</li>
      <li><b>3 barras antes e o melhor, 4 e ruim</b> ({sn(F['nb']['3']['ev'], 1)} contra
      {sn(F['nb']['4']['ev'], 1)}) &mdash; o mesmo que ja tinha aparecido sem a Hull.</li>
      <li><b>Pavio do lado da abertura: nao entrou.</b> A faixa do magenta (25&ndash;90%) mede bem
      no fechamento, mas so na compra ({sn(F['reg']['magenta']['compra']['ev'], 1)} contra
      {sn(F['reg']['magenta']['venda']['ev'], 1)} na venda) e perde na limitada; a do verde
      (5&ndash;25%) nao separa. Num periodo de alta, efeito so na compra nao e confiavel.</li>
      <li><b>Pavio do lado do fechamento: serve.</b> Ate 10% do corpo mede
      {sn(F['reg']['fech10']['ev'], 1)}; acima disso, {sn(F['reg']['fech10']['fora']['ev'], 1)}.
      Vale nos dois lados e fica entre os percentis {n(min(F['reg_pct']['fech10']))} e
      {n(max(F['reg_pct']['fech10']))} do sorteio.</li>
      <li><b>O tamanho da inclinacao nao e filtro.</b> O que vale e a Hull estar subindo ou
      descendo; subindo forte ou devagar nao separa de forma estavel (secao 5).</li>
      <li><b>Separacao da Hull para EMA e Keltner: nao entrou.</b> Hull alem da banda confirma a
      exaustao no conjunto base, mas o efeito some dentro do candidato; Hull ainda do outro lado da EMA e o melhor
      lugar, mas com gradiente irregular (secao 6).</li>
      <li><b>Juntando tudo</b> (Hull + 2 a 3 barras + pavio do fechamento ate 10%): a carteira
      faz {n(ct['trades'])} operacoes, {sn(ct['lucro_liq'])} pts, fator de lucro
      {n(ct['fator_lucro'], 2)}, rebaixamento de {n(ct['dd_max'])} pts. A 10 pts de custo sobram
      cerca de {sn(fin['ev'] - 10, 1)} pts por sinal.</li>
    </ul>
  </div>
  <p class="nota">Ha um plano de trading para o candidato em <code>plano_hull.html</code>.
  Ele e provisorio: os dois cortes a mais foram escolhidos olhando estes mesmos 26 pregoes.</p>
</section>"""


def padrao(D, F):
    return f"""
<section id="padrao">
  <h2>O padrao e o pavio avaliado</h2>
  <p class="olho">Hull 50 inclinada, 2 ou 3 candles contra ela, e o candle de sinal que volta a
  favor da Hull. A regra olha <b>um pavio so</b>: o do lado do fechamento desse candle.</p>
  {diagrama_pavio()}
</section>"""


def metodo(D, F):
    return """
<section id="metodo">
  <h2>Como foi medido</h2>
  <div class="grade g2">
    <div class="card">
      <h3>O sinal</h3>
      <p>Todo candle que fecha contra depois de candles no sentido oposto, no mesmo pregao. O
      trade vai no sentido do <b>candle contra</b>: alta depois de baixas = compra. A
      restricao unica: <b>Hull 50 inclinada a favor do trade</b> no fechamento desse candle
      (<code>hma[i] &gt; hma[i-1]</code> na compra). E, na pratica, uma retracao de 2 a 4
      candles contra a Hull seguida do primeiro candle que volta a favor dela.</p>
      <p>Hull 50 sobre o fechamento, calculada continua pela base inteira, como no Profit.</p>
    </div>
    <div class="card">
      <h3>A simulacao e os controles</h3>
      <p>Mesma engine dos estudos anteriores, cada sinal resolvido isoladamente; stop de 100,
      zerando no fim do pregao. Entradas: <b>fechamento</b> e <b>limitada no meio do corpo</b>.
      Gestoes: 1:3 com parcial de 50% em +100, 1:3 sem parcial, 1:2 e 1:1.</p>
      <p>Controles: o mesmo padrao sem olhar a Hull; a Hull <b>contra</b>; o trade invertido;
      4.000 subconjuntos sorteados do mesmo tamanho; os tres tercos do periodo; o periodo da
      Hull (21, 34, 50, 80); e a vizinhanca de cada corte do candidato final.</p>
    </div>
  </div>
</section>"""


def controles(D, F):
    lin = ''
    for ent in ENT:
        for g in GES:
            c = D['comparacao'][f'{ent}|{g}']; s = D['sorteio'][f'{ent}|{g}']

            def cel(b):
                if not b.get('n'):
                    return '<td>n/a</td>'
                return (f'<td class="{cls(b["ev"])}">{sn(b["ev"], 1)} '
                        f'<small style="color:var(--mudo)">({n(b["n"])})</small></td>')
            h = c['hull']
            tt = ' / '.join(sn(v, 0) for v in h['ev_terco'])
            lin += (f'<tr><td>{D["rot_entrada"][ent]}</td><td style="text-align:left">'
                    f'{D["rot_gestao"][g]}</td>{cel(h)}<td>{tt}</td>{cel(c["sem"])}'
                    f'{cel(c["contra"])}{cel(c["inverso"])}<td>{n(s["percentil"])}</td></tr>')
    return f"""
<section id="controles">
  <h2>1. A Hull contra os controles</h2>
  <p class="olho">Pts por sinal, brutos, cada sinal resolvido sozinho. Sempre 2 a 4 candles
  antes do candle contra.</p>
  <div class="card rolo"><table>
    <thead><tr><th>Entrada</th><th>Gestao</th><th>Hull a favor</th><th>Tercos</th>
    <th>Sem olhar a Hull</th><th>Hull contra</th><th>Invertido</th><th>Percentil</th></tr></thead>
    <tbody>{lin}</tbody></table></div>
  <p class="nota"><b>Invertido</b>: o mesmo sinal operado no sentido dos 2 a 4 candles (contra a
  Hull). <b>Percentil</b>: onde a Hull a favor cai entre subconjuntos sorteados do padrao sem
  filtro, com o mesmo tamanho &mdash; 50 seria igual ao acaso.</p>

  <div class="grade g2" style="margin-top:16px">
    <figure class="card"><h3>Periodo da Hull</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--ouro)"></i>a favor</span>
      <span><i class="chave q" style="background:var(--bronze)"></i>contra</span></div>
      <div id="g_per"></div>
      <figcaption>fechamento, gestao escolhida nas abas da secao 3</figcaption></figure>
    <figure class="card"><h3>Compra e venda, Hull a favor x sem Hull</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--ouro)"></i>Hull a favor</span>
      <span><i class="chave q" style="background:var(--bronze)"></i>sem olhar a Hull</span></div>
      <div id="g_lado"></div></figure>
  </div>
</section>"""


def abas_ges(id_, sel='parcial'):
    return (f'<div class="abas" id="{id_}">' + ''.join(
        f'<button class="aba" data-g="{g}" aria-pressed="{str(g == sel).lower()}">'
        f'{ {"parcial": "1:3 com parcial", "puro": "1:3 sem parcial", "r2": "1:2 sem parcial", "r1": "1:1 sem parcial"}[g] }'
        f'</button>' for g in GES) + '</div>')


def barras_pavios(D, F):
    lin = ''
    for ent in ENT:
        for g in GES:
            cel = ''
            for k in D['regras']:
                b = D['regras_res'][f'{ent}|{g}|{k}']
                cel += (f'<td class="{cls(b["ev"])}">{sn(b["ev"], 1)} <small style="color:var(--mudo)">'
                        f'({n(b["n"])})</small></td><td class="{cls(b["fora"]["ev"])}">'
                        f'{sn(b["fora"]["ev"], 1)}</td><td>{n(b["sorteio"]["percentil"])}</td>')
            lin += (f'<tr><td>{D["rot_entrada"][ent]}</td><td style="text-align:left">'
                    f'{D["rot_gestao"][g]}</td>{cel}</tr>')
    cab = ''.join(f'<th colspan="3" style="text-align:center">{D["regras"][k]}</th>' for k in D['regras'])
    sub = '<th></th><th></th>' + '<th>Dentro</th><th>Fora</th><th>Pct</th>' * len(D['regras'])
    return f"""
<section id="barras">
  <h2>2. Barras antes</h2>
  <p class="olho">Hull a favor, entrada no fechamento. As abas da secao 3 trocam a gestao em
  todos os graficos das secoes 1 a 4.</p>
  <div class="grade g2">
    <figure class="card"><h3>Pts por sinal</h3><div id="g_nbar"></div></figure>
    <figure class="card"><h3>Em cada terco</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--bronze)"></i>T1 ate {D['base']['c1']}</span>
      <span><i class="chave q" style="background:var(--prata)"></i>T2 ate {D['base']['c2']}</span>
      <span><i class="chave q" style="background:var(--ouro)"></i>T3</span></div>
      <div id="g_nbar_t"></div></figure>
  </div>
</section>

<section id="pavios">
  <h2>3. Os pavios do candle contra</h2>
  <p class="olho">Hull a favor, 2 a 4 barras, entrada no fechamento. Os dois lados do candle
  contra, em % do corpo. Na compra (candle de alta): lado da abertura = pavio de baixo, lado do
  fechamento = pavio de cima. Na venda, o espelho. A regra final usa so o lado do fechamento
  &mdash; ver o desenho em <a href="#padrao">O padrao e o pavio avaliado</a>.</p>
  {abas_ges('abas_g')}
  <div class="grade g2">
    <figure class="card"><h3>Lado da abertura</h3><div id="g_abre"></div></figure>
    <figure class="card"><h3>Lado do fechamento</h3><div id="g_fech"></div></figure>
    <figure class="card"><h3>Abertura: compra x venda</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--ganho)"></i>compra</span>
      <span><i class="chave q" style="background:var(--perda)"></i>venda</span></div>
      <div id="g_abre_l"></div>
      <figcaption>os lados discordam faixa a faixa: nao ha regra aqui</figcaption></figure>
    <figure class="card"><h3>Fechamento: compra x venda</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--ganho)"></i>compra</span>
      <span><i class="chave q" style="background:var(--perda)"></i>venda</span></div>
      <div id="g_fech_l"></div>
      <figcaption>nos dois lados, 10&ndash;25% e o pior</figcaption></figure>
    <figure class="card"><h3>Abertura, por terco</h3><div id="g_abre_t"></div></figure>
    <figure class="card"><h3>Fechamento, por terco</h3><div id="g_fech_t"></div></figure>
  </div>

  <h3 style="margin-top:28px">As regras de pavio que ja existiam, testadas como estao</h3>
  <div class="card rolo"><table>
    <thead><tr><th></th><th></th>{cab}</tr><tr>{sub}</tr></thead>
    <tbody>{lin}</tbody></table>
    <p class="nota">Dentro da condicao Hull + 2 a 4 barras. <b>Pct</b>: percentil contra
    subconjuntos sorteados dessa mesma condicao. Estas tres regras foram definidas antes deste
    estudo, entao sao teste; as faixas dos graficos acima sao exploracao.</p></div>
</section>"""


def combinacoes(D, F):
    lin = ''
    for ent in ENT:
        for g in GES:
            for k, rot in D['rot_candidatos'].items():
                b = D['candidatos'][f'{ent}|{g}|{k}']
                tt = ' / '.join(sn(v, 0) for v in b['ev_terco'])
                pct = '&ndash;' if k == 'h' else n(b['sorteio']['percentil'])
                d_ = ' class="destaque"' if (k == FINAL and ent == 'fecha' and g == 'parcial') else ''
                lin += (f'<tr{d_}><td>{D["rot_entrada"][ent]}</td><td style="text-align:left">'
                        f'{D["rot_gestao"][g]}</td><td style="text-align:left">{rot}</td>'
                        f'<td>{n(b["n"])}</td><td class="{cls(b["ev"])}">{sn(b["ev"], 1)}</td>'
                        f'<td>{tt}</td><td class="{cls(b["compra"]["ev"])}">{sn(b["compra"]["ev"], 1)}</td>'
                        f'<td class="{cls(b["venda"]["ev"])}">{sn(b["venda"]["ev"], 1)}</td>'
                        f'<td>{pct}</td><td class="{cls(b["ev"] - 10)}">{sn(b["ev"] - 10, 1)}</td></tr>')
    return f"""
<section id="combinacoes">
  <h2>4. Juntando os achados</h2>
  <p class="olho">Sempre dentro de Hull a favor + 2 a 4 barras. <b>2 a 3 barras</b> vem do "4 e
  ruim", que apareceu em dois estudos; <b>fechamento ate 10%</b>, do pavio do fechamento acima.
  Pct = percentil contra sorteios da condicao Hull + 2 a 4.</p>
  <div class="card rolo" style="max-height:520px"><table>
    <thead><tr><th>Entrada</th><th>Gestao</th><th>Regra</th><th>Sinais</th><th>Pts/sinal</th>
    <th>Tercos</th><th>Compra</th><th>Venda</th><th>Pct</th><th>-10 pts custo</th></tr></thead>
    <tbody>{lin}</tbody></table></div>

  <h3 style="margin-top:28px">Vizinhanca do candidato: e plato ou e pico?</h3>
  <p class="olho">Cada corte variado com os outros dois fixos, entrada no fechamento. Se so o
  valor escolhido funcionasse, seria ajuste fino a esta amostra.</p>
  <div class="grade g3">
    <figure class="card"><h3>Pavio do fechamento ate</h3><div id="g_viz_f"></div></figure>
    <figure class="card"><h3>Barras antes</h3><div id="g_viz_b"></div></figure>
    <figure class="card"><h3>Periodo da Hull</h3><div id="g_viz_h"></div></figure>
  </div>
  <p class="nota">O pavio do fechamento forma plato de 5% a 15%; <b>0%</b> (candle que fecha
  exatamente no extremo) mede pior. Barras: 2, 3 e 2&ndash;3 parecidos; incluir 1 ou 4 dilui.
  Hull: 34 e 50 parecidos, 21 e 80 piores.</p>
</section>"""


def fatos_incl(I):
    """Numeros do estudo de inclinacao que o texto cita."""
    def q(conj, m, g='parcial', e='fecha'):
        return I['quintis'][f'{conj}|{m}|{e}|{g}']
    G = ('parcial', 'puro', 'r2', 'r1')
    X = {}
    X['q1_5_pct_h'] = [q('h', 'incl5', g)[0]['sorteio']['percentil'] for g in G]
    X['q1_5_pct_c'] = [q('cand', 'incl5', g)[0]['sorteio']['percentil'] for g in G]
    X['q1_5_h'] = q('h', 'incl5')[0]; X['q1_5_c'] = q('cand', 'incl5')[0]
    X['q1_1_h'] = q('h', 'incl1')[0]; X['q5_1_h'] = q('h', 'incl1')[4]
    X['q3_1_h'] = q('h', 'incl1')[2]; X['q4_1_h'] = q('h', 'incl1')[3]
    X['min5_c'] = I['cortes_min']['cand|incl5|fecha|parcial']
    X['min1_c'] = I['cortes_min']['cand|incl1|fecha|parcial']
    X['lim5_c'] = I['quintis']['cand|incl5|limites']
    X['lim1_h'] = I['quintis']['h|incl1|limites']
    return X


def inclinacao(D, F):
    I = D.get('incl')
    if not I:
        return ''
    X = fatos_incl(I)
    ab_m = ''.join(f'<button class="aba" data-m="{k}" aria-pressed="{str(k == "incl1").lower()}">{r}</button>'
                   for k, r in (('incl1', '1 barra (pts)'), ('incl5', 'media de 5 barras'),
                                ('incl1_atr', '1 barra / ATR')))
    ab_c = ''.join(f'<button class="aba" data-c="{k}" aria-pressed="{str(k == "cand").lower()}">{r}</button>'
                   for k, r in (('cand', 'Candidato'), ('h', 'Hull + 2-4')))
    ab_g = ''.join(f'<button class="aba" data-g="{g}" aria-pressed="{str(g == "parcial").lower()}">'
                   f'{D["rot_gestao"][g]}</button>' for g in GES)
    lim = ' / '.join(n(v, 0) for v in X['lim1_h'])
    return f"""
<section id="inclinacao">
  <h2>5. O grau de inclinacao da Hull</h2>
  <p class="olho">A regra usa o <b>sinal</b> da inclinacao (subindo ou descendo). A pergunta aqui e o
  <b>tamanho</b>: Hull subindo forte e melhor que Hull subindo devagar &mdash; ou muito inclinada ja
  e exaustao?</p>
  <div class="bandeira">
    <h3>Resposta: o tamanho da inclinacao nao e filtro</h3>
    <ul class="enx">
      <li><b>As faixas nao seguem ordem.</b> Na inclinacao de 1 barra, a faixa mais plana mede
      {sn(X['q1_1_h']['ev'], 1)}, a do meio {sn(X['q3_1_h']['ev'], 1)}, a quarta
      {sn(X['q4_1_h']['ev'], 1)} e a mais inclinada {sn(X['q5_1_h']['ev'], 1)} (Hull + 2&ndash;4,
      1:3 com parcial). Sobe e desce, e muda de forma em cada gestao e em cada medida.</li>
      <li><b>Compra e venda discordam de novo.</b> Hull muito inclinada rende
      {sn(X['q5_1_h']['compra'], 1)} na compra e {sn(X['q5_1_h']['venda'], 1)} na venda &mdash; o
      desenho de um periodo de alta, nao de uma regra.</li>
      <li><b>Cortar pela inclinacao quase nao muda nada.</b> No candidato, descartar os 20%, 40% ou
      60% de Hull mais plana leva de {sn(X['min1_c'][0]['ev'], 1)} para
      {sn(X['min1_c'][1]['ev'], 1)}, {sn(X['min1_c'][2]['ev'], 1)} e {sn(X['min1_c'][3]['ev'], 1)}
      pts por sinal, jogando fora ate 60% das operacoes.</li>
      <li><b>O unico indicio:</b> a Hull quase plana <i>na media de 5 barras</i> (menos de
      ~{n(X['lim5_c'][0], 0)} pts por barra) e a faixa mais fraca em todas as gestoes, no percentil
      {n(min(X['q1_5_pct_c']))}&ndash;{n(max(X['q1_5_pct_c']))} do sorteio no candidato. Mas nos
      tercos ela oscila, sao so {n(X['q1_5_c']['n'])} sinais, e a mesma faixa medida em 1 barra nao
      e fraca. Fica como hipotese para testar fora desta amostra, nao como regra.</li>
    </ul>
  </div>
  <p class="nota">"Grau" em angulo nao tem medida objetiva &mdash; o angulo na tela depende da escala do
  grafico. A inclinacao e medida em pontos por barra, no sentido do trade. As faixas sao quintis (20%
  dos sinais cada), definidos antes de olhar o resultado. Limites dos quintis em 1 barra, Hull + 2&ndash;4:
  {lim} pts.</p>

  <div style="margin-top:14px">
    <div class="abas" id="abas_im" style="margin-bottom:6px">{ab_m}</div>
    <div class="abas" id="abas_ic" style="margin-bottom:6px">{ab_c}</div>
    <div class="abas" id="abas_ig">{ab_g}</div>
  </div>
  <div class="grade g2">
    <figure class="card"><h3>Pts por sinal, por quintil de inclinacao</h3><div id="g_iq"></div>
      <figcaption>entrada no fechamento; passe o mouse para ver n, acerto e percentil</figcaption></figure>
    <figure class="card"><h3>Em cada terco</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--bronze)"></i>T1</span>
      <span><i class="chave q" style="background:var(--prata)"></i>T2</span>
      <span><i class="chave q" style="background:var(--ouro)"></i>T3</span></div>
      <div id="g_iq_t"></div></figure>
    <figure class="card"><h3>Compra x venda</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--ganho)"></i>compra</span>
      <span><i class="chave q" style="background:var(--perda)"></i>venda</span></div>
      <div id="g_iq_l"></div></figure>
    <figure class="card"><h3>Cortando pela inclinacao</h3><div id="g_icorte"></div>
      <figcaption>descartando os X% mais planos (cheio) ou os X% mais inclinados (apagado)</figcaption></figure>
  </div>
</section>"""


def fatos_dist(T):
    G = ('parcial', 'puro', 'r2', 'r1')
    q = lambda c, m, g='parcial', e='fecha': T['quintis'][f'{c}|{m}|{e}|{g}']
    X = dict(B=T['base'])
    X['zona_h'] = q('h', 'sep_atr'); X['zona_c'] = q('cand', 'sep_atr')
    X['alem_h'] = [q('h', 'sep_atr', g)[3]['ev'] for g in G]
    X['alem_h_pct'] = [q('h', 'sep_atr', g)[3]['sorteio']['percentil'] for g in G]
    X['alem_c'] = q('cand', 'sep_atr')[3]
    X['fino_h'] = q('h', 'sep_fino'); X['fino_c'] = q('cand', 'sep_fino')
    X['m1_h'] = [q('h', 'sep_fino', g)[0]['ev'] for g in G]
    X['m1_c'] = [q('cand', 'sep_fino', g)[0]['ev'] for g in G]
    X['m1_c_lim'] = q('cand', 'sep_fino', 'parcial', 'meio_lim')[0]['ev']
    X['abs_h'] = q('h', 'sep_abs'); X['col_h'] = q('h', 'colada')
    X['banda_h'] = q('h', 'banda_pts'); X['lim_banda_h'] = T['limites']['h|banda_pts']
    X['corte_c'] = T['cortes_max']['cand|sep_atr|fecha|parcial']
    return X


def distancias(D, F):
    T = D.get('dist')
    if not T:
        return ''
    X = fatos_dist(T)
    Z = X['zona_h']; fh = X['fino_h']; fc = X['fino_c']; ab = X['abs_h']; co = X['col_h']; bd = X['banda_h']
    MED = (('sep_atr', 'Hull-EMA em ATR (zonas do canal)'), ('sep_fino', 'Hull-EMA em ATR (faixas finas)'),
           ('sep_pts', 'Hull-EMA em pontos'), ('banda_pts', 'Hull-banda em pontos'),
           ('sep_abs', 'Proximidade sem sinal'), ('colada', 'Tempo colada na EMA'))
    ab_m = ''.join(f'<button class="aba" data-m="{k}" aria-pressed="{str(k == "sep_atr").lower()}">{r}</button>'
                   for k, r in MED)
    ab_c = ''.join(f'<button class="aba" data-c="{k}" aria-pressed="{str(k == "h").lower()}">{r}</button>'
                   for k, r in (('h', 'Hull + 2-4'), ('cand', 'Candidato')))
    ab_g = ''.join(f'<button class="aba" data-g="{g}" aria-pressed="{str(g == "parcial").lower()}">'
                   f'{D["rot_gestao"][g]}</button>' for g in GES)
    return f"""
<section id="distancias">
  <h2>6. A separacao da Hull: EMA 21 e bandas de Keltner</h2>
  <p class="olho">Duas intuicoes do projeto: Hull <b>perto da banda</b> a favor indica exaustao; Hull
  <b>muito tempo perto da EMA 21</b> indica consolidacao. Medidas dentro de Hull a favor + 2&ndash;4
  barras ({n(X['B']['n_h'])} sinais) e do candidato ({n(X['B']['n_cand'])}).</p>

  <div class="bandeira">
    <h3>Primeiro: as duas perguntas sao uma so</h3>
    <p style="margin:0">As bandas sao <b>EMA 21 &plusmn; 2 ATR</b>. Medida em ATR e no sentido do trade,
    a distancia da Hull a banda a favor e <b>2 menos</b> a distancia da Hull a EMA &mdash; conferido
    em todos os sinais. "Perto da banda" e "longe da EMA" sao a mesma variavel. Elas so diferem medidas
    em pontos (o ATR muda) ou sem sinal (so proximidade). O estudo mede as tres formas.</p>
  </div>

  <div class="bandeira">
    <h3>Resposta</h3>
    <ul class="enx">
      <li><b>Hull alem da banda a favor: confirma a exaustao &mdash; so no conjunto base.</b> Com a Hull
      mais de 2 ATR alem da EMA ({n(X['B']['pct_alem'], 0)}% dos sinais) o resultado e negativo nas 4
      gestoes ({', '.join(sn(v, 1) for v in X['alem_h'])}), percentil
      {n(min(X['alem_h_pct']))}&ndash;{n(max(X['alem_h_pct']))} do sorteio. Mas dentro do candidato essa
      faixa mede {sn(X['alem_c']['ev'], 1)} ({n(X['alem_c']['n'])} sinais): o efeito some quando os
      outros filtros estao aplicados. Nao acrescenta nada a regra.</li>
      <li><b>Hull ainda do lado oposto da EMA e o melhor lugar.</b> {n(X['B']['pct_errado'], 0)}% dos
      sinais tem a Hull virada a favor mas ainda do outro lado da EMA (compra com a Hull abaixo dela):
      {sn(Z[0]['ev'], 1)} pts por sinal, contra {sn(Z[1]['ev'], 1)}, {sn(Z[2]['ev'], 1)} e
      {sn(Z[3]['ev'], 1)} nas zonas seguintes. A faixa mais extrema (mais de 1 ATR do outro lado) mede
      {', '.join(sn(v, 1) for v in X['m1_c'])} no candidato, positiva nos tres tercos e nos dois lados.
      <i>Porem</i>: nas faixas finas o gradiente vai e volta (0 a 0,5 ATR mede
      {sn(fc[3]['ev'], 1)}, 0,5 a 1 ATR {sn(fc[4]['ev'], 1)}), e na limitada a faixa extrema inverte
      ({sn(X['m1_c_lim'], 1)}). E um indicio forte de "Hull que acabou de virar", nao uma regra pronta.</li>
      <li><b>Em pontos, nao ha ordem.</b> A distancia a banda em pontos vai de {sn(bd[0]['ev'], 1)} (mais
      perto) a {sn(bd[1]['ev'], 1)}, {sn(bd[2]['ev'], 1)}, {sn(bd[3]['ev'], 1)}, {sn(bd[4]['ev'], 1)}
      &mdash; zigue-zague.</li>
      <li><b>Consolidacao: nao confirmada.</b> A Hull mais proxima da EMA (sem olhar o lado) mede
      {sn(ab[0]['ev'], 1)}, melhor que a mais afastada ({sn(ab[4]['ev'], 1)}). Tempo colada: 6 a 10
      barras mede {sn(co[3]['ev'], 1)}, na direcao da intuicao, mas sao {n(co[3]['n'])} sinais, e 11+
      barras mede {sn(co[4]['ev'], 1)} ({n(co[4]['n'])} sinais).</li>
      <li><b>O corte tentador.</b> No candidato, ficar so com os 40% de Hull mais "atrasada" em relacao a
      EMA leva de {sn(X['corte_c'][0]['ev'], 1)} para {sn(X['corte_c'][3]['ev'], 1)} pts por sinal
      ({n(X['corte_c'][3]['n'])} sinais). Escolhido olhando esta amostra, com o gradiente irregular:
      hipotese para o proximo teste, fora destes 26 pregoes.</li>
    </ul>
  </div>

  <div style="margin-top:14px">
    <div class="abas" id="abas_dm" style="margin-bottom:6px">{ab_m}</div>
    <div class="abas" id="abas_dc" style="margin-bottom:6px">{ab_c}</div>
    <div class="abas" id="abas_dg">{ab_g}</div>
  </div>
  <p class="nota" id="d_desc"></p>
  <div class="grade g2">
    <figure class="card"><h3>Pts por sinal, por faixa</h3><div id="g_dq"></div>
      <figcaption>entrada no fechamento; passe o mouse para ver n, acerto e percentil</figcaption></figure>
    <figure class="card"><h3>Em cada terco</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--bronze)"></i>T1</span>
      <span><i class="chave q" style="background:var(--prata)"></i>T2</span>
      <span><i class="chave q" style="background:var(--ouro)"></i>T3</span></div>
      <div id="g_dq_t"></div></figure>
    <figure class="card"><h3>Compra x venda</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--ganho)"></i>compra</span>
      <span><i class="chave q" style="background:var(--perda)"></i>venda</span></div>
      <div id="g_dq_l"></div></figure>
    <figure class="card"><h3>Cortando pela medida</h3><div id="g_dcorte"></div>
      <figcaption id="d_corte_cap">descartando os X% menores (cheio) ou maiores (apagado)</figcaption></figure>
  </div>
</section>"""


def carteira(D, F):
    def grupo(id_, attr, itens, sel):
        return (f'<div class="abas" id="{id_}" style="margin-bottom:6px">' + ''.join(
            f'<button class="aba" data-{attr}="{k}" aria-pressed="{str(k == sel).lower()}">{r}</button>'
            for k, r in itens) + '</div>')
    return f"""
<section id="carteira">
  <h2>7. A carteira, uma posicao por vez</h2>
  <p class="olho">Sinais que aparecem com posicao aberta sao descartados. Os botoes valem para
  as estatisticas, as curvas, as distribuicoes e o grafico trade a trade.</p>
  <div style="position:sticky;top:44px;z-index:20;background:var(--plano);padding:8px 0">
    {grupo('abas_c', 'c', [('h23f10', 'Candidato: Hull + 2-3 + fech ate 10%'), ('h', 'Hull + 2-4')], FINAL)}
    {grupo('abas_e', 'e', [('fecha', 'Fechamento'), ('meio_lim', 'Limitada no meio')], 'fecha')}
    {grupo('abas_gc', 'g', [(g, D['rot_gestao'][g]) for g in GES], 'parcial')}
  </div>

  <h3 style="margin-top:18px">Estatisticas no formato MetaTrader 5</h3>
  <div class="card rolo"><table id="t_mt5"></table>
    <p class="nota">Pontos do WINFUT, brutos; R$ para 1 contrato a R$ 0,20 por ponto. Monte Carlo:
    4.000 reamostragens dos trades com reposicao.</p></div>

  <h3 style="margin-top:32px">Evolucao do patrimonio</h3>
  <figure class="card"><div class="legenda">
      <span><i class="chave" style="background:var(--ouro)"></i>Hull + 2-3 + fech ate 10%</span>
      <span><i class="chave" style="background:var(--prata)"></i>Hull + 2-3</span>
      <span><i class="chave" style="background:var(--alerta)"></i>Hull + 2-4</span>
      <span><i class="chave" style="background:var(--bronze)"></i>sem Hull</span></div>
    <div id="g_eq"></div><figcaption>entrada e gestao escolhidas; eixo no tempo</figcaption></figure>

  <h3 style="margin-top:32px">Distribuicoes</h3>
  <div class="grade g2">
    <figure class="card"><h3>Resultado por trade</h3><div id="g_pts"></div></figure>
    <figure class="card"><h3>Duracao</h3><div id="g_dur"></div><figcaption>minutos</figcaption></figure>
    <figure class="card"><h3>MEP &mdash; maxima excursao positiva</h3><div id="g_mep"></div></figure>
    <figure class="card"><h3>MEN &mdash; maxima excursao negativa</h3><div id="g_men"></div></figure>
  </div>

  <h3 style="margin-top:32px">Horario do sinal</h3>
  <figure class="card"><div id="g_horas"></div>
    <figcaption>Hull + 2 a 4, fechamento, gestao escolhida. 10h e a abertura do mercado a vista.
    O horario nao entrou como regra: com esta base, cada hora tem poucas dezenas de sinais
    depois das 12h.</figcaption></figure>
</section>

<section id="kline">
  <h2>8. Trade a trade</h2>
  <p class="olho">A linha amarela e a Hull 50. Faixa clara: os candles antes do sinal; faixa
  forte: o candle contra, onde a entrada acontece. Setas do teclado navegam.</p>
  <div id="kwrap">
    <div class="knav">
      <button id="kant">&larr; anterior</button><button id="kprox">proximo &rarr;</button>
      <button id="kganho">proximo ganho</button><button id="kperda">proxima perda</button>
      <select id="ksel"></select>
    </div>
    <div id="kchart"></div>
    <div class="kinfo" id="kinfo"></div>
  </div>
</section>"""


def conclusao(D, F):
    fin = F['fin']
    return f"""
<section id="conclusao">
  <h2>Conclusao</h2>
  <ul class="enx">
    <li><b>A Hull 50 a favor e o filtro que faltava.</b> Ela sozinha praticamente dobra o valor
    por sinal em relacao ao padrao sem filtro, em todas as entradas e gestoes e nos dois lados;
    com entrada no fechamento, tambem nos tres tercos. E a Hull contra quase zera o resultado: a
    informacao esta na inclinacao.</li>
    <li><b>Pavio do lado da abertura continua sem regra confiavel</b>: a faixa do magenta so
    funciona na compra e se inverte na limitada.</li>
    <li><b>Pavio do lado do fechamento serve</b>: o candle contra que deixa um pavio de mais de
    10% alem do fechamento &mdash; rejeitado no fim &mdash; rende menos nos dois lados.</li>
    <li><b>O candidato</b> (Hull + 2 a 3 barras + fechamento ate 10%, entrada no fechamento)
    mede {sn(fin['parcial']['ev'], 1)} pts por sinal no 1:3 com parcial e
    {sn(fin['r1']['ev'], 1)} no 1:1, positivo nos tres tercos e nos dois lados, e os cortes
    formam plato.</li>
    <li><b>Vale o sentido da Hull, nao o grau.</b> O tamanho da inclinacao &mdash; em 1 barra, em 5
    barras ou relativo ao ATR &mdash; nao ordena os resultados, e compra e venda discordam.</li>
    <li><b>EMA 21 e Keltner nao acrescentam regra ao candidato.</b> A exaustao (Hull alem da banda)
    existe no conjunto base mas some dentro do candidato; a consolidacao (Hull colada na EMA) nao se
    confirma. Fica uma hipotese: sinais com a Hull ainda do lado oposto da EMA.</li>
    <li><b>Entrada no fechamento, nao na limitada.</b> A limitada perde o primeiro terco em
    quase todas as combinacoes.</li>
  </ul>
  <div class="bandeira">
    <h3>O que ainda falta</h3>
    <p style="margin:0">26 pregoes, um instrumento, periodo de alta (a compra rende mais que a
    venda em tudo). Os dois cortes a mais foram escolhidos nesta mesma amostra, entao o numero
    do candidato e otimista. A Hull a favor &mdash; que era hipotese sua, definida antes de
    medir &mdash; e a parte mais confiavel. O proximo passo e rodar o plano em simulador e
    medir de novo com pregoes que nao entraram aqui.</p>
  </div>
</section>
<footer>Gerado por <code>hull_contra.py</code> e <code>relatorio_hull.py</code>.</footer>"""


# ======================================================================= JS
JS = r"""
const bt=document.getElementById('btema');
function temaAtual(){const t=document.documentElement.dataset.tema;
  if(t==='claro'||t==='escuro') return t;
  return matchMedia('(prefers-color-scheme: dark)').matches?'escuro':'claro';}
bt.addEventListener('click',()=>{
  document.documentElement.dataset.tema=temaAtual()==='escuro'?'claro':'escuro';
  desenha(); if(typeof desenhaIncl==='function') desenhaIncl(); if(typeof desenhaDist==='function') desenhaDist(); pintaKline();});

let gG='parcial', sC='h23f10', sE='fecha', sG='parcial';
function grupoAbas(id,attr,fn){
  const g=document.getElementById(id);
  g.addEventListener('click',ev=>{const b=ev.target.closest('.aba'); if(!b) return;
    g.querySelectorAll('.aba').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
    fn(b.dataset[attr]);});
}
grupoAbas('abas_g','g',v=>{gG=v; desenha();});
grupoAbas('abas_c','c',v=>{sC=v; desenha(); trocaLista();});
grupoAbas('abas_e','e',v=>{sE=v; desenha(); trocaLista();});
grupoAbas('abas_gc','g',v=>{sG=v; desenha(); trocaLista();});

function ex(b){return b.n?`<span class="l">n</span> ${b.n} &middot; <span class="l">acerto</span> ${fmt(b.wr,1)}%`:'';}
function clsv(v){return v>0?'pos':(v<0?'neg':'');}
function barrasB(sel,lista,op){
  barrasH(sel,lista.filter(b=>b.n).map(b=>({nome:b.faixa,v:b.ev,extra:ex(b),fraco:op&&op.fraco?op.fraco(b):false})),
    Object.assign({rotV:'por sinal',casas:1,esq:100},op||{}));}
function tercos(sel,lista){grupos(sel,lista.filter(b=>b.n).map(b=>({nome:b.faixa,v:b.ev_terco,n:b.n_terco})),
  ['T1','T2','T3'],{cores:['bronze','prata','ouro'],esq:90});}
function ladoAlado(sel,c,v){grupos(sel,c.map((b,i)=>({nome:b.faixa,v:[b.ev,v[i].ev],n:[b.n,v[i].n]})),
  ['compra','venda'],{cores:['ganho','perda'],esq:90});}

function histo(vals,passo,corFixa){
  if(!vals||!vals.length) return [];
  const lo=Math.floor(Math.min(...vals)/passo)*passo, hi=Math.ceil(Math.max(...vals)/passo)*passo;
  const k=Math.max(1,Math.round((hi-lo)/passo)), c=new Array(k).fill(0);
  vals.forEach(v=>{let i=Math.floor((v-lo)/passo); if(i>=k)i=k-1; if(i<0)i=0; c[i]++;});
  return c.map((q,i)=>({nome:fmt(lo+i*passo),v:q,cor:corFixa||((lo+i*passo)>=0?'ganho':'perda'),
    extra:'<span class="l">faixa</span> '+fmt(lo+i*passo)+' a '+fmt(lo+(i+1)*passo)+' pts'}));
}
function duracao(ds){
  const cortes=[0,60,180,300,600,1200,2400,1e12], rot=['ate 1','1 a 3','3 a 5','5 a 10','10 a 20','20 a 40','40+'];
  const c=new Array(rot.length).fill(0);
  (ds||[]).forEach(s=>{for(let i=0;i<cortes.length-1;i++) if(s>=cortes[i]&&s<cortes[i+1]){c[i]++;break;}});
  return c.map((q,i)=>({nome:rot[i],v:q,cor:'prata'}));
}

const MT5=[
 ['Lucro liquido',s=>sinal(s.lucro_liq)+' pts','lucro_liq'],
 ['Lucro liquido (R$)',s=>'R$ '+sinal(s.lucro_liq_rs,2),'lucro_liq'],
 ['Lucro bruto / prejuizo bruto',s=>fmt(s.lucro_bruto)+' / '+fmt(s.prej_bruto),null],
 ['Fator de lucro',s=>fmt(s.fator_lucro,2),null],
 ['Payoff esperado',s=>sinal(s.exp_pts,1)+' pts','exp_pts'],
 ['Fator de recuperacao',s=>fmt(s.recovery,2),null],
 ['Indice de Sharpe (por trade)',s=>fmt(s.sharpe,3),null],
 ['Correlacao LR',s=>fmt(s.lr_corr,2),null],
 ['Rebaixamento maximo',s=>fmt(s.dd_max)+' pts (R$ '+fmt(s.dd_max_rs)+')',null],
 ['Total de negociacoes',s=>fmt(s.trades),null],
 ['Winrate',s=>fmt(s.winrate,1)+'%',null],
 ['Compras (acerto)',s=>fmt(s.longs)+' ('+fmt(s.longs_wr,1)+'%)',null],
 ['Vendas (acerto)',s=>fmt(s.shorts)+' ('+fmt(s.shorts_wr,1)+'%)',null],
 ['Pontos em compras / vendas',s=>sinal(s.longs_pts)+' / '+sinal(s.shorts_pts),null],
 ['Maior ganho / maior perda',s=>sinal(s.maior_ganho)+' / '+sinal(s.maior_perda),null],
 ['Ganho medio / perda media',s=>sinal(s.media_ganho,1)+' / '+sinal(s.media_perda,1),null],
 ['Maximo de ganhos / perdas seguidas',s=>fmt(s.max_seq_ganho)+' / '+fmt(s.max_seq_perda),null],
 ['Negociacoes por dia',s=>fmt(s.trades_dia,1),null],
 ['Pontos por dia',s=>sinal(s.pts_dia,1),'pts_dia'],
 ['Duracao mediana',s=>fmt(s.dur_mediana/60,1)+' min',null],
 ['Saidas: alvo / stop / zero / fim do dia',s=>[s.alvos,s.stops,s.stops_zero,s.fins_dia+s.timeouts].map(x=>fmt(x)).join(' / '),null],
 ['Monte Carlo: chance de lucro',s=>s.mc&&s.mc.p_lucro!==undefined?fmt(s.mc.p_lucro,1)+'%':'-',null],
 ['Monte Carlo: lucro p5 / p95',s=>s.mc&&s.mc.tot_p5!==undefined?sinal(s.mc.tot_p5)+' / '+sinal(s.mc.tot_p95):'-',null],
 ['Monte Carlo: rebaixamento p95',s=>s.mc&&s.mc.dd_p95!==undefined?fmt(s.mc.dd_p95)+' pts':'-',null],
];

function desenha(){
  const k='fecha|'+gG;
  /* periodo e lados */
  grupos('#g_per',D.periodos[k].map(b=>({nome:b.faixa,v:[b.ev,b.contra.ev],n:[b.n,b.contra.n]})),
    ['a favor','contra'],{cores:['ouro','bronze'],esq:70});
  const L=D.lados[k];
  grupos('#g_lado',[{nome:'compra',v:[L.compra.ev,L.compra_sem.ev],n:[L.compra.n,L.compra_sem.n]},
    {nome:'venda',v:[L.venda.ev,L.venda_sem.ev],n:[L.venda.n,L.venda_sem.n]}],
    ['Hull a favor','sem Hull'],{cores:['ouro','bronze'],esq:70});
  /* barras */
  barrasB('#g_nbar',D.barras_antes[k].map(b=>Object.assign({},b,{faixa:b.faixa+(b.faixa==='1'?' barra':' barras')})),
    {fraco:b=>!['2 barras','3 barras','4 barras'].includes(b.faixa)});
  tercos('#g_nbar_t',D.barras_antes[k]);
  /* pavios */
  barrasB('#g_abre',D.pavio_abre[k]); barrasB('#g_fech',D.pavio_fech[k]);
  ladoAlado('#g_abre_l',D.pavio_abre[k+'|compra'],D.pavio_abre[k+'|venda']);
  ladoAlado('#g_fech_l',D.pavio_fech[k+'|compra'],D.pavio_fech[k+'|venda']);
  tercos('#g_abre_t',D.pavio_abre[k]); tercos('#g_fech_t',D.pavio_fech[k]);
  /* vizinhanca */
  const V=D.vizinhanca[k];
  const pinta=(sel,eixo,esc)=>barrasB(sel,V.filter(b=>b.eixo===eixo),{esq:95,fraco:b=>b.faixa!==esc});
  pinta('#g_viz_f','pavio do fechamento','fech <= 10%');
  pinta('#g_viz_b','barras antes','2 a 3 barras');
  pinta('#g_viz_h','periodo da Hull','Hull 50');

  /* carteira */
  const base=sE+'|'+sG+'|';
  const sp=D.carteira[base+sC], s2=D.carteira[base+(sC==='h'?'h23f10':'h')], ss=D.carteira[base+'sem'];
  const nomes={h23f10:'Candidato',h:'Hull + 2-4'};
  document.getElementById('t_mt5').innerHTML=
    `<thead><tr><th>Estatistica</th><th>${nomes[sC]}</th><th>${nomes[sC==='h'?'h23f10':'h']}</th><th>Sem Hull (2-4)</th></tr></thead><tbody>`+
    MT5.map(r=>`<tr><td>${r[0]}</td>`+[sp,s2,ss].map(s=>`<td class="${r[2]&&s.trades?clsv(s[r[2]]):''}">${s.trades?r[1](s):'-'}</td>`).join('')+'</tr>').join('')+'</tbody>';
  const ser=[['h23f10','Candidato','ouro'],['h23','Hull 2-3','prata'],['h','Hull 2-4','alerta'],['sem','Sem Hull','bronze']]
    .map(([c,nm,cr])=>{const s=D.carteira[base+c]; return s.trades?{nome:nm,cor:cr,dados:s.equity,xs:s.xs,dt:s.dt,area:c==='h23f10'}:null;}).filter(Boolean);
  linhas('#g_eq',ser,{alt:320});
  colunas('#g_pts',histo(sp.pts,50),{alt:230,rotula:true,rotV:'trades',un:'trades'});
  colunas('#g_mep',histo(sp.mfe,50,'ganho'),{alt:230,rotula:true,rotV:'trades',un:'trades'});
  colunas('#g_men',histo(sp.mae,25,'perda'),{alt:230,rotula:true,rotV:'trades',un:'trades'});
  colunas('#g_dur',duracao(sp.dur_s),{alt:230,rotula:true,rotV:'trades',un:'trades'});
  barrasB('#g_horas',D.horas[sE+'|'+sG],{esq:60});
}
addEventListener('resize',()=>{clearTimeout(window._rz);
  window._rz=setTimeout(()=>{desenha(); desenhaIncl(); desenhaDist(); if(kchart) kchart.resize();},180);});

/* ================================================================ kline */
const SANS='system-ui,-apple-system,"Segoe UI",sans-serif';
function c_(k){return getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim();}
function alfa(hex,a){const h=hex.replace('#','').trim();
  const x=h.length===3?h.split('').map(y=>y+y).join(''):h; const i=parseInt(x,16);
  return 'rgba('+((i>>16)&255)+','+((i>>8)&255)+','+(i&255)+','+a+')';}
klinecharts.registerOverlay({name:'hc-nivel',totalStep:2,lock:true,
  needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{const e=overlay.extendData,y=coordinates[0].y;
    return [{type:'line',ignoreEvent:true,attrs:{coordinates:[{x:0,y:y},{x:bounding.width,y:y}]},
      styles:{color:e.cor,size:1,style:e.cheia?'solid':'dashed',dashedValue:[4,4]}},
     {type:'text',ignoreEvent:true,attrs:{x:4,y:y-3,text:e.rot,align:'left',baseline:'bottom'},
      styles:{color:e.cor,size:10,family:SANS,weight:'600',backgroundColor:alfa(c_('card'),.78),
      paddingLeft:4,paddingRight:4,paddingTop:1,paddingBottom:1,borderRadius:3}}];}});
klinecharts.registerOverlay({name:'hc-zona',totalStep:3,lock:true,
  needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{if(coordinates.length<2) return [];
    const a=Math.min(coordinates[0].x,coordinates[1].x), b=Math.max(coordinates[0].x,coordinates[1].x);
    const w=overlay.extendData.meia||0;
    return [{type:'rect',ignoreEvent:true,attrs:{x:a-w,y:0,width:Math.max(2,b-a+2*w),height:bounding.height},
      styles:{style:'fill',color:overlay.extendData.cor}}];}});
klinecharts.registerIndicator({name:'HULL50',shortName:'Hull 50',series:'price',precision:0,
  figures:[{key:'hma',title:'Hull 50: ',type:'line'}],calc:dl=>dl.map(k=>({hma:k.hma}))});

let kchart=null,kidx=0,KTR=[],KL=[];
const T0=Date.UTC(2000,0,1),TB=60000;
function linK(cor){return {color:cor,size:2,smooth:false,style:'solid',dashedValue:[3,4]};}
function estilo(){const g=c_('grade'),m=c_('mudo'),card=c_('card'),up=c_('ganho'),dn=c_('perda');
  return {grid:{horizontal:{color:g},vertical:{color:g}},
    candle:{bar:{upColor:up,downColor:dn,noChangeColor:m,upBorderColor:up,downBorderColor:dn,
      noChangeBorderColor:m,upWickColor:up,downWickColor:dn,noChangeWickColor:m},
      priceMark:{last:{show:false}},
      tooltip:{showRule:'follow_cross',text:{color:c_('tinta'),family:SANS,size:11},
        rect:{color:alfa(card,.94),borderColor:c_('eixo')}}},
    indicator:{lines:[linK(c_('alerta'))],tooltip:{showRule:'follow_cross',showName:true,showParams:false,
      text:{color:c_('tinta2'),family:SANS,size:11}}},
    xAxis:{axisLine:{color:c_('eixo')},tickLine:{color:c_('eixo')},tickText:{color:m,family:SANS,size:11}},
    yAxis:{axisLine:{color:c_('eixo')},tickLine:{color:c_('eixo')},tickText:{color:m,family:SANS,size:11}},
    crosshair:{horizontal:{line:{color:m},text:{backgroundColor:c_('tinta2')}},
      vertical:{line:{color:m},text:{backgroundColor:c_('tinta2')}}}};}
function pintaKline(){if(!kchart) return; const st=estilo(); kchart.setStyles(st);
  kchart.overrideIndicator({name:'HULL50',styles:st.indicator},'candle_pane'); mostra_(kidx);}
function iniciaKline(){
  const C=D.candles,N=C.o.length;
  for(let i=0;i<N;i++) KL.push({timestamp:T0+i*TB,open:C.o[i],high:C.h[i],low:C.l[i],close:C.c[i],volume:0,hma:C.hma[i]});
  kchart=klinecharts.init('kchart',{styles:estilo(),customApi:{formatDate:(f,ts,fm,tipo)=>{
    const i=Math.round((ts-T0)/TB); const s=(i>=0&&i<N)?C.dt[i]:''; return tipo===2?s.slice(6):s;}}});
  kchart.setPriceVolumePrecision(0,0);
  kchart.createIndicator({name:'HULL50',styles:estilo().indicator},true,{id:'candle_pane'});
  kchart.applyNewData(KL,false,()=>mostra_(0));
}
function mostra_(i){
  if(!kchart||!KTR.length) return;
  kidx=Math.max(0,Math.min(KTR.length-1,i)); const t=KTR[kidx], G=D.gestoes[sG], ld=t.lado;
  kchart.removeOverlay();
  const de=Math.max(0,t.i-t.n_fav-20), ate=Math.min(KL.length-1,t.i_sai+12), jan=Math.max(14,ate-de+1);
  const larg=(kchart.getSize('candle_pane','main')||{}).width||760;
  const esp=Math.max(1.2,Math.min(40,larg/jan)); kchart.setBarSpace(esp); kchart.scrollToDataIndex(ate+2);
  const meia=esp/2;
  kchart.createOverlay({name:'hc-zona',lock:true,points:[{timestamp:KL[t.i-t.n_fav].timestamp},
    {timestamp:KL[t.i-1].timestamp}],extendData:{cor:alfa(c_('prata'),.12),meia:meia}});
  kchart.createOverlay({name:'hc-zona',lock:true,points:[{timestamp:KL[t.i].timestamp},
    {timestamp:KL[t.i].timestamp}],extendData:{cor:alfa(c_('ouro'),.28),meia:meia}});
  kchart.createOverlay({name:'hc-zona',lock:true,points:[{timestamp:KL[t.i_ent].timestamp},
    {timestamp:KL[t.i_sai].timestamp}],extendData:{cor:alfa(t.pts>=0?c_('ganho'):c_('perda'),.07),meia:meia}});
  const nv=[{v:t.ent,rot:'entrada '+fmt(t.ent),cor:c_('tinta'),cheia:true},
    {v:t.ent-ld*G.stop,rot:'stop',cor:c_('perda'),cheia:true},
    {v:t.ent+ld*G.alvo,rot:'alvo +'+G.alvo,cor:c_('ganho'),cheia:true}];
  if(G.parcial) nv.push({v:t.ent+ld*G.parcial_em,rot:'parcial +'+G.parcial_em,cor:c_('ganho'),cheia:false});
  nv.forEach(L=>kchart.createOverlay({name:'hc-nivel',lock:true,points:[{timestamp:KL[t.i_ent].timestamp,value:L.v}],extendData:L}));
  document.getElementById('ksel').value=String(kidx);
  const ROT={alvo:'alvo',stop:'stop',stop_zero:'zero a zero',timeout:'tempo',fim_dia:'fim do dia'};
  document.getElementById('kinfo').innerHTML=
    `<span><b>#${kidx+1}</b> de ${KTR.length}</span><span>${t.data}</span>`+
    `<span><b>${ld>0?'▲ compra':'▼ venda'}</b></span>`+
    `<span>${t.n_fav} barras antes &middot; pavio abertura <b>${fmt(t.pav,0)}%</b> &middot; fechamento <b>${fmt(t.pavf,0)}%</b></span>`+
    `<span>entrada <b>${fmt(t.ent)}</b></span><span>saida <b>${fmt(t.sai)}</b> (${ROT[t.motivo]||t.motivo})</span>`+
    `<span>resultado <b class="${clsv(t.pts)}">${sinal(t.pts)} pts</b></span>`+
    `<span>MEP <b>${sinal(t.mfe)}</b> &middot; MEN <b>${sinal(t.mae)}</b></span>`;
}
function preencheLista(){
  KTR=D.trades[sE+'|'+sG+'|'+sC]||[];
  document.getElementById('ksel').innerHTML=KTR.map((t,i)=>
    `<option value="${i}">#${i+1} · ${t.data} · ${t.lado>0?'compra':'venda'} · ${sinal(t.pts)} pts</option>`).join('');
}
function trocaLista(){preencheLista(); mostra_(0);}
document.getElementById('ksel').addEventListener('change',e=>mostra_(+e.target.value));
document.getElementById('kant').addEventListener('click',()=>mostra_(kidx-1));
document.getElementById('kprox').addEventListener('click',()=>mostra_(kidx+1));
function busca(f){for(let k=kidx+1;k<KTR.length;k++) if(f(KTR[k])) return mostra_(k);
  for(let k=0;k<KTR.length;k++) if(f(KTR[k])) return mostra_(k);}
document.getElementById('kganho').addEventListener('click',()=>busca(t=>t.pts>0));
document.getElementById('kperda').addEventListener('click',()=>busca(t=>t.pts<0));
addEventListener('keydown',ev=>{if(['SELECT','BUTTON'].includes(ev.target.tagName)) return;
  if(ev.key==='ArrowLeft') mostra_(kidx-1); if(ev.key==='ArrowRight') mostra_(kidx+1);});


let iM='incl1', iC='cand', iG='parcial';
if(D.incl){
  grupoAbas('abas_im','m',v=>{iM=v; desenhaIncl();});
  grupoAbas('abas_ic','c',v=>{iC=v; desenhaIncl();});
  grupoAbas('abas_ig','g',v=>{iG=v; desenhaIncl();});
}
function desenhaIncl(){
  if(!D.incl) return;
  const Q=D.incl.quintis[iC+'|'+iM+'|fecha|'+iG];
  barrasH('#g_iq',Q.map(b=>({nome:b.faixa,v:b.ev,
    extra:ex(b)+(b.sorteio?' &middot; <span class="l">percentil</span> '+fmt(b.sorteio.percentil):'')})),
    {rotV:'por sinal',casas:1,esq:130});
  grupos('#g_iq_t',Q.map(b=>({nome:b.faixa,v:b.ev_terco,n:b.n_terco})),['T1','T2','T3'],
    {cores:['bronze','prata','ouro'],esq:130});
  grupos('#g_iq_l',Q.map(b=>({nome:b.faixa,v:[b.compra,b.venda]})),['compra','venda'],
    {cores:['ganho','perda'],esq:130});
  const mn=D.incl.cortes_min[iC+'|'+iM+'|fecha|'+iG], mx=D.incl.cortes_max[iC+'|'+iM+'|fecha|'+iG];
  barrasH('#g_icorte',mn.map(b=>({nome:b.faixa,v:b.ev,extra:ex(b)}))
    .concat(mx.slice(1).map(b=>({nome:b.faixa,v:b.ev,extra:ex(b),fraco:true}))),
    {rotV:'por sinal',casas:1,esq:200});
}

let dM='sep_atr', dC='h', dG='parcial';
if(D.dist){
  grupoAbas('abas_dm','m',v=>{dM=v; desenhaDist();});
  grupoAbas('abas_dc','c',v=>{dC=v; desenhaDist();});
  grupoAbas('abas_dg','g',v=>{dG=v; desenhaDist();});
}
function desenhaDist(){
  if(!D.dist) return;
  const T=D.dist, Q=T.quintis[dC+'|'+dM+'|fecha|'+dG], lim=T.limites[dC+'|'+dM];
  document.getElementById('d_desc').innerHTML='<b>'+T.medidas[dM]+'</b> &middot; limites: '+
    lim.map(v=>fmt(v,Math.abs(v)<10?2:0)).join(' / ');
  const esq=Math.max(...Q.map(b=>b.faixa.length))*6+10;
  barrasH('#g_dq',Q.filter(b=>b.n).map(b=>({nome:b.faixa,v:b.ev,
    extra:ex(b)+(b.sorteio?' &middot; <span class="l">percentil</span> '+fmt(b.sorteio.percentil):'')})),
    {rotV:'por sinal',casas:1,esq:esq});
  grupos('#g_dq_t',Q.filter(b=>b.n).map(b=>({nome:b.faixa,v:b.ev_terco,n:b.n_terco})),['T1','T2','T3'],
    {cores:['bronze','prata','ouro'],esq:esq});
  grupos('#g_dq_l',Q.filter(b=>b.n).map(b=>({nome:b.faixa,v:[b.compra,b.venda]})),['compra','venda'],
    {cores:['ganho','perda'],esq:esq});
  const box=document.getElementById('g_dcorte'), cap=document.getElementById('d_corte_cap');
  const mn=T.cortes_min[dC+'|'+dM+'|fecha|'+dG], mx=T.cortes_max[dC+'|'+dM+'|fecha|'+dG];
  if(!mn){box.innerHTML='<p class="nota">Medida em faixas fixas: sem varredura de cortes.</p>'; cap.hidden=true; return;}
  cap.hidden=false;
  barrasH('#g_dcorte',mn.map(b=>({nome:b.faixa,v:b.ev,extra:ex(b)}))
    .concat(mx.slice(1).map(b=>({nome:b.faixa,v:b.ev,extra:ex(b),fraco:true}))),
    {rotV:'por sinal',casas:1,esq:170});
}

desenha(); desenhaIncl(); desenhaDist(); preencheLista(); iniciaKline();
"""

HTML = r"""<!doctype html>
<html lang="pt-BR" data-tema="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITULO__</title>
<style>__CSS__</style>
</head>
<body>
<nav class="indice"><div class="wrap"><ul>__MENU__</ul></div></nav>
<div class="wrap">
__CORPO__
</div>
<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>
__SCRIPTS__
</body>
</html>
"""

MENU = [('resposta', 'Resposta'), ('padrao', 'Pavio avaliado'), ('metodo', 'Metodo'), ('controles', 'Hull'),
        ('barras', 'Barras'), ('pavios', 'Pavios'), ('combinacoes', 'Combinacoes'), ('inclinacao', 'Inclinacao'), ('distancias', 'EMA e Keltner'),
        ('carteira', 'Carteira'), ('kline', 'Trade a trade'), ('conclusao', 'Conclusao')]


def monta(titulo, css, menu, corpo, scripts):
    return (HTML.replace('__TITULO__', titulo).replace('__CSS__', css)
            .replace('__MENU__', ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in menu))
            .replace('__SCRIPTS__', scripts).replace('__CORPO__', corpo))


# ======================================================================= MD
def markdown(D, F):
    B = D['base']; fin = F['fin']; ct = F['cart']
    L = ['# Hull 50 a favor + 2 a 4 candles + 1 contra', '',
         f"WINFUT, grafico de 20 PI, {n(B['barras'])} candles, {B['dias']} pregoes "
         f"({B['ini']} a {B['fim']}). Resultado bruto. Graficos, curvas, MEP/MEN, duracao e trade a "
         'trade em `hull_contra.html`; plano em `PLANO_HULL.md`.', '',
         '**O padrao** (compra; venda e o espelho): Hull 50 subindo no fechamento do candle contra, '
         '2 a 4 candles de baixa, depois 1 de alta. Compra no fechamento dele.', '',
         '## Qual pavio e avaliado', '', DIAGRAMA_MD, '',
         '## Resposta curta: a Hull muda o jogo', '',
         '| Entrada no fechamento, 1:3 com parcial | Sinais | Pts/sinal |', '|:--|--:|--:|',
         f"| Hull a favor | {md_n(F['hull']['n'])} | {md_sn(F['hull']['ev'], 1)} |",
         f"| Sem olhar a Hull | {md_n(F['sem']['n'])} | {md_sn(F['sem']['ev'], 1)} |",
         f"| Hull contra | {md_n(F['contra']['n'])} | {md_sn(F['contra']['ev'], 1)} |",
         f"| Invertido | {md_n(F['inv']['n'])} | {md_sn(F['inv']['ev'], 1)} |",
         f"| **Candidato: Hull + 2-3 barras + pavio do fechamento ate 10%** | {md_n(fin['parcial']['n'])} | **{md_sn(fin['parcial']['ev'], 1)}** |",
         '',
         f"- **Hull a favor:** percentil {md_n(min(F['pct']))} a {md_n(max(F['pct']))} contra o sorteio nas 4 gestoes; "
         f"dois lados (compra {md_sn(F['lados']['compra']['ev'], 1)}, venda {md_sn(F['lados']['venda']['ev'], 1)}).",
         f"- **Barras:** 3 antes {md_sn(F['nb']['3']['ev'], 1)}, 4 antes {md_sn(F['nb']['4']['ev'], 1)}.",
         f"- **Pavio do lado da abertura:** a faixa do magenta so funciona na compra ({md_sn(F['reg']['magenta']['compra']['ev'], 1)} "
         f"contra {md_sn(F['reg']['magenta']['venda']['ev'], 1)} na venda) e perde na limitada; a do verde nao separa.",
         f"- **Pavio do lado do fechamento ate 10%:** {md_sn(F['reg']['fech10']['ev'], 1)} contra "
         f"{md_sn(F['reg']['fech10']['fora']['ev'], 1)} acima disso; percentil "
         f"{md_n(min(F['reg_pct']['fech10']))} a {md_n(max(F['reg_pct']['fech10']))}.",
         f"- **Carteira do candidato** (1:3 com parcial): {md_n(ct['trades'])} trades, {md_sn(ct['lucro_liq'])} pts "
         f"(R$ {md_sn(ct['lucro_liq_rs'], 2)}), fator {md_n(ct['fator_lucro'], 2)}, acerto {md_n(ct['winrate'], 1)}%, "
         f"rebaixamento {md_n(ct['dd_max'])} pts.",
         '', '## 1. Hull contra os controles', '',
         '| Entrada | Gestao | Hull a favor | Tercos | Sem Hull | Hull contra | Invertido | Percentil |',
         '|:--|:--|--:|:--|--:|--:|--:|--:|']
    for ent in ENT:
        for g in GES:
            c = D['comparacao'][f'{ent}|{g}']

            def cel(b):
                return f"{md_sn(b['ev'], 1)} ({md_n(b['n'])})" if b.get('n') else 'n/a'
            L.append(f"| {D['rot_entrada'][ent]} | {D['rot_gestao'][g]} | {cel(c['hull'])} | "
                     + ' / '.join(md_sn(v, 0) for v in c['hull']['ev_terco'])
                     + f" | {cel(c['sem'])} | {cel(c['contra'])} | {cel(c['inverso'])} | "
                     f"{md_n(D['sorteio'][f'{ent}|{g}']['percentil'])} |")
    L += ['', '**Periodo da Hull** (fechamento, 1:3 com parcial, 2-4 barras):', '',
          '| Hull | A favor | Contra |', '|:--|--:|--:|']
    for b in D['periodos']['fecha|parcial']:
        L.append(f"| {b['faixa']} | {md_sn(b['ev'], 1)} ({md_n(b['n'])}) | "
                 f"{md_sn(b['contra']['ev'], 1)} ({md_n(b['contra']['n'])}) |")
    L += ['', '## 2. Barras antes (Hull a favor, fechamento, 1:3 com parcial)', '',
          '| Barras | Sinais | Pts/sinal | T1 | T2 | T3 |', '|:--|--:|--:|--:|--:|--:|']
    for b in D['barras_antes']['fecha|parcial']:
        L.append(f"| {b['faixa']} | {md_n(b['n'])} | {md_sn(b['ev'], 1)} | "
                 + ' | '.join(md_sn(v, 1) for v in b['ev_terco']) + ' |')
    for lado_, chave, rot in (('abre', 'pavio_abre', 'lado da abertura'),
                              ('fech', 'pavio_fech', 'lado do fechamento')):
        L += ['', f'## 3{"a" if lado_ == "abre" else "b"}. Pavio do {rot} do candle contra '
              '(Hull, 2-4, fechamento, 1:3 com parcial)', '',
              '| Pavio | Sinais | Pts/sinal | T1 | T2 | T3 | Compra | Venda |',
              '|:--|--:|--:|--:|--:|--:|--:|--:|']
        cc = {b['faixa']: b for b in D[chave]['fecha|parcial|compra']}
        vv = {b['faixa']: b for b in D[chave]['fecha|parcial|venda']}
        for b in D[chave]['fecha|parcial']:
            if b['n']:
                L.append(f"| {b['faixa']} | {md_n(b['n'])} | {md_sn(b['ev'], 1)} | "
                         + ' | '.join(md_sn(v, 1) for v in b['ev_terco'])
                         + f" | {md_sn(cc[b['faixa']]['ev'], 1)} | {md_sn(vv[b['faixa']]['ev'], 1)} |")
    L += ['', '**Regras de pavio que ja existiam** (dentro de Hull + 2-4):', '',
          '| Entrada | Gestao | ' + ' | '.join(D['regras'][k] for k in D['regras']) + ' |',
          '|:--|:--|' + '--:|' * len(D['regras'])]
    for ent in ENT:
        for g in GES:
            L.append(f"| {D['rot_entrada'][ent]} | {D['rot_gestao'][g]} | " + ' | '.join(
                f"{md_sn(D['regras_res'][f'{ent}|{g}|{k}']['ev'], 1)} (fora {md_sn(D['regras_res'][f'{ent}|{g}|{k}']['fora']['ev'], 1)}, "
                f"pct {md_n(D['regras_res'][f'{ent}|{g}|{k}']['sorteio']['percentil'])})" for k in D['regras']) + ' |')
    L += ['', '## 4. Combinacoes (fechamento)', '',
          '| Gestao | Regra | Sinais | Pts/sinal | Tercos | Compra | Venda | Pct | -10 custo |',
          '|:--|:--|--:|--:|:--|--:|--:|--:|--:|']
    for g in GES:
        for k, rot in D['rot_candidatos'].items():
            b = D['candidatos'][f'fecha|{g}|{k}']
            L.append(f"| {D['rot_gestao'][g]} | {rot} | {md_n(b['n'])} | {md_sn(b['ev'], 1)} | "
                     + ' / '.join(md_sn(v, 0) for v in b['ev_terco'])
                     + f" | {md_sn(b['compra']['ev'], 1)} | {md_sn(b['venda']['ev'], 1)} | "
                     f"{'-' if k == 'h' else md_n(b['sorteio']['percentil'])} | {md_sn(b['ev'] - 10, 1)} |")
    L += ['', '**Vizinhanca do candidato** (fechamento, 1:3 com parcial):', '',
          '| Eixo | Valor | Sinais | Pts/sinal | T1 | T2 | T3 |', '|:--|:--|--:|--:|--:|--:|--:|']
    for b in D['vizinhanca']['fecha|parcial']:
        L.append(f"| {b['eixo']} | {b['faixa']} | {md_n(b['n'])} | {md_sn(b['ev'], 1)} | "
                 + ' | '.join(md_sn(v, 1) for v in b['ev_terco']) + ' |')
    I = D.get('incl')
    if I:
        X = fatos_incl(I)
        L += ['', '## 5. O grau de inclinacao da Hull', '',
              '**Resposta: o tamanho da inclinacao nao e filtro.** Vale o sentido (subindo/descendo), nao o grau. '
              'Inclinacao medida em pontos por barra, no sentido do trade; faixas = quintis (20% dos sinais cada).', '']
        for conj, rot in (('h', 'Hull + 2-4'), ('cand', 'Candidato')):
            for m, mr in (('incl1', '1 barra'), ('incl5', 'media de 5 barras'), ('incl1_atr', '1 barra / ATR')):
                L += [f'**{rot} -- {mr}** (fechamento; pts por sinal por gestao; compra/venda no 1:3 com parcial)', '',
                      '| Quintil | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct (parcial) |',
                      '|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|']
                Qs = {g: I['quintis'][f'{conj}|{m}|fecha|{g}'] for g in GES}
                for k in range(5):
                    b = Qs['parcial'][k]
                    L.append(f"| {b['faixa']} | {md_n(b['n'])} | " + ' | '.join(md_sn(Qs[g][k]['ev'], 1) for g in GES)
                             + ' | ' + ' / '.join(md_sn(v, 0) for v in b['ev_terco'])
                             + f" | {md_sn(b['compra'], 1)} | {md_sn(b['venda'], 1)} | {md_n(b['sorteio']['percentil'])} |")
                L.append('')
        L += ['**Cortando pela inclinacao** (candidato, fechamento, 1:3 com parcial):', '',
              '| Medida | Todos | Sem os 20% mais planos | Sem os 40% | Sem os 60% |', '|:--|--:|--:|--:|--:|']
        for m, mr in (('incl1', '1 barra'), ('incl5', 'media de 5 barras'), ('incl1_atr', '1 barra / ATR')):
            r = I['cortes_min'][f'cand|{m}|fecha|parcial']
            L.append(f'| {mr} | ' + ' | '.join(f"{md_sn(b['ev'], 1)} ({md_n(b['n'])})" for b in r) + ' |')
        L += ['',
              f"- As faixas nao seguem ordem, e compra e venda discordam (Hull muito inclinada: compra "
              f"{md_sn(X['q5_1_h']['compra'], 1)}, venda {md_sn(X['q5_1_h']['venda'], 1)}).",
              f"- Unico indicio: Hull quase plana na media de 5 barras (menos de ~{md_n(X['lim5_c'][0])} pts/barra) "
              f"e a faixa mais fraca em todas as gestoes (percentil {md_n(min(X['q1_5_pct_c']))}-"
              f"{md_n(max(X['q1_5_pct_c']))}), mas oscila nos tercos e so tem {md_n(X['q1_5_c']['n'])} sinais. "
              'Hipotese para testar fora da amostra, nao regra.', '']
    T = D.get('dist')
    if T:
        X = fatos_dist(T)
        L += ['', '## 6. A separacao da Hull: EMA 21 e bandas de Keltner', '',
              '> As bandas sao EMA 21 +/- 2 ATR. Em ATR e no sentido do trade, distancia da Hull a banda a favor = '
              '2 - distancia da Hull a EMA (conferido em todos os sinais): "perto da banda" e "longe da EMA" sao a '
              'mesma variavel. So diferem em pontos ou sem sinal.', '']
        MEDS = (('sep_atr', 'Hull - EMA em ATR, zonas do canal'), ('sep_fino', 'Hull - EMA em ATR, faixas finas'),
                ('sep_pts', 'Hull - EMA em pontos (quintis)'), ('banda_pts', 'Hull - banda a favor em pontos (quintis)'),
                ('sep_abs', '|Hull - EMA| em ATR, sem sinal (quintis)'), ('colada', 'Barras seguidas com Hull colada na EMA'))
        for conj, rot in (('h', 'Hull + 2-4'), ('cand', 'Candidato')):
            for m, mr in MEDS:
                Qs = {g: T['quintis'][f'{conj}|{m}|fecha|{g}'] for g in GES}
                L += [f'**{rot} -- {mr}** (fechamento)', '',
                      '| Faixa | Sinais | 1:3 parcial | 1:3 puro | 1:2 | 1:1 | Tercos (parcial) | Compra | Venda | Pct |',
                      '|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|']
                for k, b in enumerate(Qs['parcial']):
                    if not b['n']:
                        continue
                    L.append(f"| {b['faixa']} | {md_n(b['n'])} | " + ' | '.join(md_sn(Qs[g][k]['ev'], 1) for g in GES)
                             + ' | ' + ' / '.join(md_sn(v, 0) for v in b['ev_terco'])
                             + f" | {md_sn(b['compra'], 1)} | {md_sn(b['venda'], 1)} | "
                             + (md_n(b['sorteio']['percentil']) if b['sorteio'] else '-') + ' |')
                L.append('')
        L += [f"- **Hull alem da banda a favor** ({md_n(X['B']['pct_alem'])}% dos sinais): negativa nas 4 gestoes no "
              f"conjunto base ({', '.join(md_sn(v, 1) for v in X['alem_h'])}); no candidato, {md_sn(X['alem_c']['ev'], 1)}. "
              'Confirma exaustao no conjunto base, mas o efeito some dentro do candidato.',
              f"- **Hull ainda do lado oposto da EMA** ({md_n(X['B']['pct_errado'])}% dos sinais): a melhor zona "
              f"({md_sn(X['zona_h'][0]['ev'], 1)}). A faixa mais extrema (< -1 ATR) mede {', '.join(md_sn(v, 1) for v in X['m1_c'])} "
              f"no candidato, mas o gradiente fino vai e volta e na limitada inverte ({md_sn(X['m1_c_lim'], 1)}). Hipotese, nao regra.",
              '- **Em pontos:** sem ordem (zigue-zague).',
              f"- **Consolidacao:** nao confirmada; Hull mais proxima da EMA mede {md_sn(X['abs_h'][0]['ev'], 1)}, "
              f"mais afastada {md_sn(X['abs_h'][4]['ev'], 1)}; tempo colada tem poucos casos.", '']
    L += ['', '## 7. Carteira, uma posicao por vez', '',
          '| Entrada | Gestao | Regra | Trades | Pts | Fator | Acerto | Rebaix. | MC lucro | MC rebaix. p95 |',
          '|:--|:--|:--|--:|--:|--:|--:|--:|--:|--:|']
    for ent in ENT:
        for g in GES:
            for k, rot in (('h23f10', 'Candidato'), ('h', 'Hull 2-4'), ('sem', 'Sem Hull')):
                s = D['carteira'][f'{ent}|{g}|{k}']
                L.append(f"| {D['rot_entrada'][ent]} | {D['rot_gestao'][g]} | {rot} | {md_n(s['trades'])} | "
                         f"{md_sn(s['lucro_liq'])} | {md_n(s['fator_lucro'], 2)} | {md_n(s['winrate'], 1)}% | "
                         f"{md_n(s['dd_max'])} | {md_n(s['mc'].get('p_lucro'), 0)}% | {md_n(s['mc'].get('dd_p95'))} |")
    L += ['', '## Conclusao', '',
          '- **A Hull 50 a favor e o filtro que faltava:** praticamente dobra o valor por sinal, em todas as entradas '
          'e gestoes e nos dois lados (no fechamento, tambem nos tres tercos); com a Hull contra o resultado quase zera.',
          '- **Pavio do lado da abertura:** sem regra confiavel; a faixa do magenta so funciona na compra e se inverte na limitada.',
          '- **Pavio do lado do fechamento ate 10%:** serve, nos dois lados.',
          f"- **Candidato** (Hull + 2-3 + fechamento ate 10%, entrada no fechamento): {md_sn(fin['parcial']['ev'], 1)} pts "
          f"por sinal no 1:3 com parcial, {md_sn(fin['r1']['ev'], 1)} no 1:1; cortes em plato.",
          '- **Vale o sentido da Hull, nao o grau:** o tamanho da inclinacao nao ordena os resultados.',
          '- **EMA 21 e Keltner nao acrescentam regra ao candidato:** exaustao (alem da banda) some dentro do candidato; consolidacao nao confirmada; hipotese aberta: Hull ainda do lado oposto da EMA.',
          '- **Entrada no fechamento**, nao na limitada (que perde o primeiro terco).',
          '',
          '> 26 pregoes, um instrumento, periodo de alta, resultado bruto. Os dois cortes a mais foram escolhidos '
          'nesta amostra; a Hull a favor, hipotese definida antes de medir, e a parte mais confiavel.',
          '', 'Reproduzir: `python hull_contra.py && python relatorio_hull.py`.', '']
    return '\n'.join(L)


# ==================================================================== PLANO
def plano(D, F):
    ct = F['cart']; fin = F['fin']['parcial']; mc = ct['mc']
    passos = [
        ('1', 'A Hull 50 esta inclinada a favor do trade?',
         'Para <b>comprar</b>, a Hull 50 tem de estar <b>subindo</b> no fechamento do candle de sinal '
         '(valor atual maior que o do candle anterior). Para <b>vender</b>, descendo. Nao importa se o '
         'preco esta acima ou abaixo dela.',
         f"E o filtro que sustenta o setup: com a Hull contra, o mesmo padrao mede "
         f"{sn(F['contra']['ev'], 1)} pts por sinal; a favor, {sn(F['hull']['ev'], 1)}.",
         'Hull plana ou inclinada contra.'),
        ('2', 'Vieram 2 ou 3 candles seguidos CONTRA a Hull?',
         'Na compra: 2 ou 3 candles seguidos de <b>baixa</b>, no mesmo pregao, imediatamente antes do '
         'candle de sinal. Na venda: 2 ou 3 de alta.',
         f"3 antes mediu {sn(F['nb']['3']['ev'], 1)}, 2 antes {sn(F['nb']['2']['ev'], 1)}; 1 so e fraco "
         f"({sn(F['nb']['1']['ev'], 1)}) e 4 perde ({sn(F['nb']['4']['ev'], 1)}).",
         '1 candle, ou 4 ou mais. Retracao que atravessa a virada do dia.'),
        ('3', 'O candle de sinal fechou A FAVOR da Hull?',
         'O candle atual fecha no sentido da Hull: <b>alta</b> na compra, <b>baixa</b> na venda. Espere o '
         'candle <b>fechar</b>: antes disso o lado dele nao esta definido.',
         'E o primeiro candle que devolve o movimento para o lado da Hull.',
         'Candle ainda aberto.'),
        ('4', 'O pavio do lado do fechamento e pequeno?',
         'Na compra, o pavio de <b>cima</b> do candle de sinal (maxima menos fechamento) ate <b>10 pontos</b> '
         '(10% do corpo). Na venda, o de <b>baixo</b> (fechamento menos minima). O pavio do outro lado '
         '(o da abertura) nao importa.',
         f"Ate 10% mediu {sn(F['reg']['fech10']['ev'], 1)} pts por sinal; acima, "
         f"{sn(F['reg']['fech10']['fora']['ev'], 1)}. Pavio grande alem do fechamento e o preco rejeitado "
         'justamente no sentido do trade.',
         'Pavio do lado do fechamento acima de 10 pontos.'),
    ]
    html_passos = ''.join(f"""
  <div class="passo"><div class="n">{p_[0]}</div><div>
    <h3>{p_[1]}</h3><p class="regra">{p_[2]}</p><p class="por">{p_[3]}</p>
    <p class="nao">Nao vale se: {p_[4]}</p></div></div>""" for p_ in passos)
    chk = ['Hull 50 inclinada a favor do trade', '2 ou 3 candles seguidos contra a Hull, no mesmo pregao',
           'Candle de sinal FECHADO a favor da Hull', 'Pavio do lado do fechamento ate 10 pontos',
           'Nenhuma posicao aberta agora', 'Stop de 100 pontos definido ANTES de entrar']
    itens = ''.join(f'<li><span class="cx"></span><span>{t}</span></li>' for t in chk)
    B = D['base']
    corpo = f"""
<header class="capa">
  <div class="chapeu">Plano de trading &middot; WINFUT &middot; grafico de 20 PI &middot; provisorio</div>
  <h1>Hull a favor, retracao curta</h1>
  <p class="sub">Quatro perguntas de sim ou nao, na ordem em que se olha para a tela. Se qualquer
  uma der nao, o trade nao existe.</p>
  <div style="margin-top:18px">
    <span class="selo">Hull 50</span><span class="selo">2 ou 3 candles contra</span>
    <span class="selo">entrada no fechamento</span><span class="selo">stop 100 &middot; alvo 300</span>
    <span class="selo">parcial 50% em +100</span>
  </div>
  <div class="bandeira" style="margin-top:24px">
    <h3>Leia isto antes</h3>
    <p style="margin-bottom:0">Sai de um backteste de <b>{B['dias']} pregoes</b> ({B['ini']} a
    {B['fim']}), todo em mercado de alta, <b>bruto</b>. A Hull a favor era hipotese definida antes
    de medir; os passos 2 e 4 foram ajustados nesta mesma amostra, entao os numeros abaixo sao um
    teto. <b>Rode em simulador</b> antes de dinheiro real e compare com a tabela da secao
    "Quando parar".</p>
  </div>
</header>

<section id="setup">
  <h2>O setup</h2>
  <p class="olho">Com a Hull 50 inclinada, o preco devolve 2 ou 3 candles contra ela. O primeiro
  candle que volta a favor da Hull, fechando sem rejeicao, e a entrada.</p>
  <div class="grade g4">
    {tile('Por operacao', sn(ct['exp_pts'], 1) + ' pts', f"R$ {sn(ct['exp_rs'], 2)} por contrato, bruto", 'pos')}
    {tile('Acerto', n(ct['winrate'], 1) + '%', 'alvo 300, stop 100, parcial em +100')}
    {tile('Frequencia', n(ct['trades_dia'], 1), 'operacoes por pregao')}
    {tile('Rebaixamento maximo', n(ct['dd_max']) + ' pts', f"Monte Carlo p95: {n(mc['dd_p95'])} pts")}
  </div>
  <p class="nota">Carteira de uma posicao por vez, {n(ct['trades'])} operacoes. Com 10 pts de custo
  por operacao, o valor por sinal cai de {sn(fin['ev'], 1)} para {sn(fin['ev'] - 10, 1)}.</p>
</section>

<section id="pavio">
  <h2>Qual pavio olhar</h2>
  {diagrama_pavio(titulo=False)}
</section>

<section id="passos">
  <h2>As 4 perguntas</h2>
  {html_passos}
</section>

<section id="gestao">
  <h2>A gestao</h2>
  <div class="regua">
    <div class="faixa"><div class="vlr">Entrada</div><div>A mercado, no <b>fechamento</b> do candle de
      sinal. Nao use limitada no meio do corpo: ela perdeu o primeiro terco do periodo.</div></div>
    <div class="faixa"><div class="vlr neg">Stop 100</div><div>100 pontos contra a entrada, colocado junto
      com a entrada.</div></div>
    <div class="faixa"><div class="vlr pos">+100</div><div>Sai <b>metade</b>. O stop do restante fica na
      media da operacao &mdash; que, com metade realizada a +100, e o proprio stop inicial: se voltar,
      a operacao sai no zero a zero.</div></div>
    <div class="faixa"><div class="vlr pos">Alvo 300</div><div>Sai o restante.</div></div>
    <div class="faixa"><div class="vlr">Fim do dia</div><div>Zera o que estiver aberto no ultimo candle
      do pregao.</div></div>
    <div class="faixa"><div class="vlr">1 por vez</div><div>Sinal que aparece com posicao aberta e
      ignorado.</div></div>
  </div>
  <p class="nota">Sem parcial (1:3 puro) o valor por sinal sobe para {sn(F['fin']['puro']['ev'], 1)}, mas o
  rebaixamento vai de {n(ct['dd_max'])} para {n(D['carteira']['fecha|puro|h23f10']['dd_max'])} pts e a
  maior sequencia de perdas de {ct['max_seq_perda']} para
  {D['carteira']['fecha|puro|h23f10']['max_seq_perda']}.</p>
</section>

<section id="checklist">
  <h2>Checklist antes de clicar</h2>
  <div class="card"><ul class="lista-chk">{itens}</ul></div>
</section>

<section id="parar">
  <h2>Quando parar</h2>
  <div class="card rolo"><table>
    <thead><tr><th>Sinal de alerta</th><th>Referencia do backteste</th></tr></thead>
    <tbody>
      <tr><td>Rebaixamento acima de</td><td>{n(mc['dd_p95'])} pts (p95 do Monte Carlo)</td></tr>
      <tr><td>Perdas seguidas acima de</td><td>{ct['max_seq_perda']} (maximo medido)</td></tr>
      <tr><td>Acerto, depois de 100 operacoes, abaixo de</td><td>25% (medido: {n(ct['winrate'], 1)}%)</td></tr>
      <tr><td>Valor por operacao, depois de 100, abaixo de</td><td>o custo real por operacao</td></tr>
    </tbody></table>
    <p class="nota">Qualquer um desses: pare, volte ao simulador e meca de novo com a base nova.</p></div>
</section>

<section id="naofazer">
  <h2>O que nao fazer</h2>
  <ul class="enx">
    <li><b>Entrar antes do candle fechar.</b> O lado do candle e o pavio so existem no fechamento.</li>
    <li><b>Filtrar pelo pavio da abertura.</b> O efeito medido aparece so na compra e se inverte
    na limitada &mdash; nao e regra.</li>
    <li><b>Aceitar 4 candles de retracao.</b> Mediu negativo.</li>
    <li><b>Operar com a Hull plana ou contra.</b> E o que tira o resultado do zero.</li>
  </ul>
</section>
<footer>Gerado por <code>relatorio_hull.py</code> a partir de <code>saida/hull_contra.json</code>.
Estudo completo em <code>hull_contra.html</code>.</footer>"""

    md = ['# Plano de trading -- Hull a favor, retracao curta (provisorio)', '',
          f"WINFUT, grafico de 20 PI. Backteste de {B['dias']} pregoes ({B['ini']} a {B['fim']}), bruto, "
          'mercado de alta. A Hull a favor era hipotese previa; os passos 2 e 4 foram ajustados nesta amostra. '
          '**Rode em simulador antes de dinheiro real.**', '',
          '## O setup', '',
          f"- Por operacao: {md_sn(ct['exp_pts'], 1)} pts brutos (R$ {md_sn(ct['exp_rs'], 2)} por contrato); "
          f"com 10 pts de custo, {md_sn(fin['ev'] - 10, 1)} por sinal",
          f"- Acerto: {md_n(ct['winrate'], 1)}%",
          f"- Frequencia: {md_n(ct['trades_dia'], 1)} operacoes por pregao",
          f"- Rebaixamento maximo: {md_n(ct['dd_max'])} pts (Monte Carlo p95: {md_n(mc['dd_p95'])})", '',
          '## Qual pavio olhar', '', DIAGRAMA_MD, '',
          '## As 4 perguntas (compra; venda e o espelho)', '']
    for p_ in passos:
        strip = lambda s: s.replace('<b>', '**').replace('</b>', '**')
        md += [f"### {p_[0]}. {p_[1]}", '', strip(p_[2]), '', f"> {strip(p_[3])}", '',
               f"**Nao vale se:** {p_[4]}", '']
    md += ['## Gestao', '',
           '- **Entrada:** a mercado, no fechamento do candle de sinal (nao usar limitada no meio do corpo).',
           '- **Stop:** 100 pontos, junto com a entrada.',
           '- **+100:** sai metade; o stop do restante fica na media da operacao (= stop inicial: se voltar, zero a zero).',
           '- **Alvo:** 300 pontos no restante.',
           '- **Fim do dia:** zera no ultimo candle do pregao. Uma posicao por vez.', '',
           '## Checklist', ''] + [f'- [ ] {t}' for t in chk] + [
           '', '## Quando parar', '',
           f"- Rebaixamento acima de {md_n(mc['dd_p95'])} pts (p95 do Monte Carlo)",
           f"- Mais de {ct['max_seq_perda']} perdas seguidas",
           f"- Acerto abaixo de 25% depois de 100 operacoes (medido: {md_n(ct['winrate'], 1)}%)",
           '- Valor por operacao abaixo do custo real depois de 100 operacoes', '',
           '## O que nao fazer', '',
           '- Entrar antes do candle fechar.', '- Filtrar pelo pavio da abertura (efeito so na compra, se inverte na limitada).',
           '- Aceitar 4 candles de retracao.', '- Operar com a Hull plana ou contra.', '']
    return corpo, '\n'.join(md)


# ===================================================================== main
def main():
    with open(os.path.join(SAIDA, 'hull_contra.json'), encoding='utf-8') as f:
        D = json.load(f)
    F = fatos(D)
    D['gestoes'] = GESTOES_JS
    pi = os.path.join(SAIDA, 'hull_inclinacao.json')
    if os.path.exists(pi):
        with open(pi, encoding='utf-8') as f:
            D['incl'] = json.load(f)
    pd_ = os.path.join(SAIDA, 'hull_distancias.json')
    if os.path.exists(pd_):
        with open(pd_, encoding='utf-8') as f:
            D['dist'] = json.load(f)
    D['candles']['dt'] = [dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).strftime('%d/%m %H:%M:%S')
                          for t in D['candles']['t']]
    del D['candles']['t']

    corpo = ''.join([capa(D, F), resposta(D, F), padrao(D, F), metodo(D, F), controles(D, F),
                     barras_pavios(D, F), combinacoes(D, F), inclinacao(D, F), distancias(D, F), carteira(D, F), conclusao(D, F)])
    with open(VENDOR_KC, encoding='utf-8') as f:
        kline = f.read()
    dados = json.dumps(D, ensure_ascii=False, separators=(',', ':'))
    scripts = ('<script>' + kline + '</script>\n<script>const D=' + dados + ';</script>\n'
               '<script>' + molde.JS_KIT + '</script>\n<script>' + JS + '</script>')
    html = monta('Hull Contra Retracao', molde.CSS, MENU, corpo, scripts)
    with open(os.path.join(BASE, 'hull_contra.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(BASE, 'HULL_CONTRA.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(D, F))

    pc, pmd = plano(D, F)
    js_tema = r"""<script>
const bt=document.getElementById('btema');
bt.addEventListener('click',()=>{const t=document.documentElement.dataset.tema;
  const escuro=(t==='escuro')||(t!=='claro'&&matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.dataset.tema=escuro?'claro':'escuro';});
</script>"""
    ph = monta('Plano Hull Retracao', molde.CSS + molde_plano.CSS_EXTRA,
               [('setup', 'Setup'), ('pavio', 'Qual pavio'), ('passos', '4 perguntas'), ('gestao', 'Gestao'),
                ('checklist', 'Checklist'), ('parar', 'Quando parar'), ('naofazer', 'Nao fazer')],
               pc, js_tema)
    with open(os.path.join(BASE, 'plano_hull.html'), 'w', encoding='utf-8') as f:
        f.write(ph)
    with open(os.path.join(BASE, 'PLANO_HULL.md'), 'w', encoding='utf-8') as f:
        f.write(pmd)
    print(f'gravado: hull_contra.html ({len(html) / 1e6:.1f} MB), HULL_CONTRA.md, '
          'plano_hull.html, PLANO_HULL.md')


if __name__ == '__main__':
    main()
