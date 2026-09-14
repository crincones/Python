# -*- coding: utf-8 -*-
"""
Monta relatorio.html (e RESULTADOS.md) a partir de saida/resumo.json.

    python rodar.py && python relatorio.py

O html sai OFFLINE e num arquivo so: css, kit de graficos, klinecharts e
dados vao todos embutidos.
"""
import json
import os

import molde

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
VENDOR_KC = os.path.join(BASE, 'vendor', 'klinecharts-9.8.10.min.js')

ROT_MODO = {'fecha': 'Fechamento do candle',
            'meio_lim': 'Limitada no meio do corpo',
            'antecipa': 'Stop no meio do corpo (antecipada)'}
ROT_GESTAO = {'parcial': '1:3 com parcial', 'puro': '1:3 sem parcial',
              'r2': '1:2 sem parcial'}


# ------------------------------------------------------------- formatacao
def n(v, c=0):
    if v is None:
        return '&ndash;'
    return f'{v:,.{c}f}'.replace(',', ' ').replace('.', ',').replace(' ', '.')


def sn(v, c=0):
    if v is None:
        return '&ndash;'
    return ('+' if v > 0 else '') + n(v, c)


def cls(v):
    if v is None or abs(v) < 1e-9:
        return ''
    return 'pos' if v > 0 else 'neg'


def tile(rot, num, pe='', c=''):
    return (f'<div class="tile"><div class="rot">{rot}</div>'
            f'<div class="num {c}">{num}</div>'
            + (f'<div class="pe">{pe}</div>' if pe else '') + '</div>')



# =========================================================== o corpo do html
def capa(D):
    a = D['auditoria']; P = D['parametros']
    st = D['variantes'][D['escolhida']]['stats']
    return f"""
<header class="capa">
  <div class="chapeu">Backtest &middot; WINFUT &middot; grafico de 20 PI</div>
  <h1>Momentum de continuacao<br>no grafico de Pontos de Inversao</h1>
  <p class="sub">Retracao seguida de candle de continuacao, com Hull 50, EMA 21
  e canal de Keltner. {n(a['candles'])} candles, {a['dias']} pregoes, de
  {a['de'][8:]}/{a['de'][5:7]}/{a['de'][:4]} a {a['ate'][8:]}/{a['ate'][5:7]}/{a['ate'][:4]}
  &mdash; a base inteira disponivel.</p>
  <div style="margin-top:18px">
    <span class="selo">Hull {P['hull']}</span>
    <span class="selo">EMA {P['ema']}</span>
    <span class="selo">Keltner {P['atr']} &plusmn; {n(P['desvio'], 1)} ATR</span>
    <span class="selo">stop {n(P['stop'])} &middot; alvo {n(P['alvo'])}</span>
    <span class="selo">parcial 50% em +{n(P['parcial_em'])}</span>
    <span class="selo">{st['trades']} trades no padrao Ouro</span>
  </div>
</header>"""


def resumo(D):
    st = D['variantes'][D['escolhida']]['stats']
    base = D['variantes']['fecha|parcial|bronze']['stats']
    mc = D['monte_carlo'][D['escolhida']]
    P = D['parametros']
    tiles = ''.join([
        tile('Resultado, padrao Ouro', sn(st['lucro_liq']) + ' pts',
             f"R$ {sn(st['lucro_liq_rs'])} com 1 contrato", cls(st['lucro_liq'])),
        tile('Expectativa por trade', sn(st['exp_pts'], 1) + ' pts',
             f"R$ {sn(st['exp_rs'], 2)} &middot; {st['trades']} trades",
             cls(st['exp_pts'])),
        tile('Acerto', n(st['winrate'], 1) + '%',
             f"{st['vitorias']} ganhos &middot; {st['zeros']} zerados &middot; "
             f"{st['derrotas']} perdas"),
        tile('Fator de lucro', n(st['fator_lucro'], 2),
             f"rebaixamento maximo {n(st['dd_max'])} pts"),
    ])
    return f"""
<section id="resumo">
  <h2>O que a medicao achou</h2>
  <p class="olho">A regra do CLAUDE.md, medida como esta escrita, ja mede positivo:
  {sn(base['exp_pts'], 1)} pontos por trade em {base['trades']} operacoes. Tres filtros
  &mdash; um veto de exaustao, a exigencia de uma retracao de verdade e a forma do
  candle que retoma &mdash; levam isso a {sn(st['exp_pts'], 1)} pontos por trade, com
  menos de um terco das operacoes. Esse recorte e o <b>padrao Ouro</b>.</p>
  <div class="grade g4">{tiles}</div>

  <div class="grade g3" style="margin-top:16px">
    <div class="card">
      <h3>O que confirmou</h3>
      <ul class="enx">
        <li>O padrao de dois candles funciona, e o alvo de {n(P['alvo'])} com stop de
            {n(P['stop'])} e um <b>otimo local</b> da grade inteira.</li>
        <li>Hull 50 bate Hull 21, 34 e 80 em <b>todas</b> as EMAs testadas.</li>
        <li>A exaustao existe &mdash; so nao e a banda de Keltner sozinha.</li>
      </ul>
    </div>
    <div class="card">
      <h3>O que desmentiu</h3>
      <ul class="enx">
        <li>Exigir a Hull <b>concava</b> mede ao contrario: a metade concava rende
            {sn(D['estudos']['concavidade'][1]['ev'], 1)} pts, a outra
            {sn(D['estudos']['concavidade'][0]['ev'], 1)}.</li>
        <li>Filtro de inclinacao da EMA 21: separa ao contrario, e e a mesma
            informacao do esticamento (correlacao 0,78).</li>
        <li>Entrar no meio do corpo com ordem limitada perde dinheiro no conjunto
            sem filtro.</li>
      </ul>
    </div>
    <div class="card">
      <h3>O tamanho do teste</h3>
      <ul class="enx">
        <li><b>{D['auditoria']['dias']} pregoes.</b> E pouco. Tudo aqui foi medido em
            tercos do periodo justamente por isso.</li>
        <li>Monte Carlo: probabilidade de lucro
            <b>{n(mc['prob_lucro'], 1)}%</b>, faixa de {sn(mc['total_p05'])} a
            {sn(mc['total_p95'])} pts.</li>
        <li>Resultado <b>bruto</b>. A {n(D['custos'][3]['custo'])} pts de custo ele cai
            para {sn(D['custos'][3]['ev'], 1)} pts por trade.</li>
      </ul>
    </div>
  </div>
</section>"""


def base_dados(D):
    a = D['auditoria']
    return f"""
<section id="base">
  <h2>A base, e o que ela e de fato</h2>
  <p class="olho">O grafico de <b>20 PI</b> da Nelogica nao e um grafico de tempo. Cada
  candle fecha exatamente <b>100 pontos</b> (20 ticks &times; 5) acima ou abaixo da sua
  abertura, e abre no fechamento do anterior. O corpo, entao, nao carrega informacao
  nenhuma: <b>a unica forma que um candle de PI tem e o pavio</b> &mdash; e o tempo que
  ele levou para se formar. Isso muda o que faz sentido perguntar sobre "a geometria do
  candle que retoma a tendencia", e e por isso que o estudo da geometria, mais abaixo,
  olha o pavio total e nao a relacao corpo/pavio.</p>
  <div class="grade g4">
    {tile('Candles', n(a['candles']), f"{n(a['barras_dia_media'])} por pregao")}
    {tile('Corpo de 100 pontos', n(a['corpo_100_pct'], 2) + '%',
          'o unico candle fora e o fim de um pregao')}
    {tile('Abre no fechamento anterior', n(a['abre_no_fecha_pct'], 2) + '%',
          'o resto e virada de dia')}
    {tile('ATR 21 mediano', n(a['atr_mediana']) + ' pts',
          f"range mediano {n(a['range_mediano'])} pts")}
  </div>
  <div class="card" style="margin-top:16px">
    <h3>Conferencia dos indicadores</h3>
    <p style="margin-bottom:0">A EMA 21 calculada aqui foi conferida <b>contra a coluna
    de EMA exportada pela propria Nelogica</b> nos {n(a['ema_conferidos'])} candles em
    que ela existe: o erro maximo e de {n(a['ema_erro_p999'], 3)} ponto &mdash; o
    arredondamento das duas casas do csv &mdash; em todos menos
    {a['ema_divergentes']} candles, que sao falhas pontuais do proprio arquivo. A semente
    e a media aritmetica dos 21 primeiros fechamentos, como na Nelogica. A Hull e
    WMA(2&times;WMA(25) &minus; WMA(50), 7) e o canal de Keltner e a EMA 21 &plusmn; 2
    ATR(21) exponencial, com a EMA do canal sendo <b>a mesma</b> media de tendencia,
    como pede o CLAUDE.md.</p>
  </div>
</section>"""


# ------------------------------------------------------------ diagrama do padrao
def _candle(x, o, c, hi, lo, cor, larg=22):
    """Candle esquematico do diagrama. O eixo de preco e invertido a mao:
    y = BASE - valor."""
    y = lambda v: 250 - v
    topo, base = max(o, c), min(o, c)
    return (f'<line x1="{x}" x2="{x}" y1="{y(hi)}" y2="{y(lo)}" '
            f'stroke="var(--{cor})" stroke-width="2"/>'
            f'<rect x="{x - larg / 2}" y="{y(topo)}" width="{larg}" '
            f'height="{max(2, topo - base)}" rx="2" fill="var(--{cor})"/>')


def diagrama_padrao():
    """Esquema do padrao de COMPRA. O de venda e o espelho exato.

    As posicoes sao escolhidas a mao para que a figura obedeca a propria
    regra: os dois extremos do par acima da Hull, a EMA 21 cortando o par,
    a Hull subindo e atras do preco.
    """
    y = lambda v: 250 - v
    # x:   60   100  140  |  180  220  |  260        (o par e 220 + 260)
    candles = ''.join([
        _candle(60, 20, 70, 76, 14, 'ganho'),
        _candle(100, 70, 120, 130, 64, 'ganho'),
        _candle(140, 120, 170, 182, 116, 'ganho'),
        _candle(180, 170, 120, 178, 110, 'perda'),
        _candle(220, 120, 70, 128, 58, 'perda'),
        _candle(260, 70, 120, 138, 56, 'ganho'),
    ])
    return f"""
<div style="max-width:780px;margin:0 auto">
<svg class="viz" viewBox="0 0 640 312" role="img"
     aria-label="Esquema do padrao de compra: tres candles de alta, dois candles
     de retracao e o candle de continuacao. A Hull 50 sobe por baixo do preco, a
     EMA 21 corta o par retracao-continuacao e a banda superior do Keltner fica
     bem acima. A entrada e no fechamento do candle de continuacao.">
  <!-- banda superior do Keltner: longe, e por isso nao filtra nada sozinha -->
  <path d="M 34 {y(196)} C 120 {y(214)}, 200 {y(232)}, 296 {y(238)}"
        fill="none" stroke="var(--mudo)" stroke-width="1.2" stroke-dasharray="3 4"/>
  <text x="304" y="{y(236)}" class="eixo-tx">Keltner +2 ATR</text>
  <!-- EMA 21: precisa passar entre os topos e os fundos do par -->
  <path d="M 34 {y(58)} C 120 {y(80)}, 200 {y(102)}, 296 {y(110)}"
        fill="none" stroke="var(--prata)" stroke-width="2" stroke-linecap="round"/>
  <text x="304" y="{y(106)}" class="eixo-tx" fill="var(--prata)"
        font-weight="640">EMA 21</text>
  <!-- Hull 50: subindo, e ATRAS do preco -->
  <path d="M 34 {y(30)} C 120 {y(44)}, 200 {y(66)}, 296 {y(82)}"
        fill="none" stroke="var(--alerta)" stroke-width="2.5" stroke-linecap="round"/>
  <text x="304" y="{y(78)}" class="eixo-tx" fill="var(--alerta)"
        font-weight="640">Hull 50</text>

  <!-- o par que conta: ultimo candle da retracao + candle de continuacao -->
  <rect x="202" y="{y(160)}" width="76" height="{160 - 40}" rx="5"
        fill="var(--prata)" fill-opacity=".10" stroke="var(--prata)"
        stroke-opacity=".35" stroke-dasharray="4 3"/>
  <text x="240" y="{y(166)}" class="eixo-tx" text-anchor="middle"
        font-weight="640" fill="var(--tinta2)">o par que conta</text>

  {candles}

  <!-- os dois extremos do par, acima da Hull -->
  <circle cx="220" cy="{y(128)}" r="5" fill="none" stroke="var(--tinta)" stroke-width="1.5"/>
  <circle cx="260" cy="{y(138)}" r="5" fill="none" stroke="var(--tinta)" stroke-width="1.5"/>

  <!-- rotulos de baixo -->
  <line x1="166" x2="234" y1="{y(4)}" y2="{y(4)}" stroke="var(--eixo)" stroke-width="1"/>
  <text x="200" y="{y(-14)}" class="eixo-tx" text-anchor="middle">retracao (2 candles)</text>
  <line x1="248" x2="272" y1="{y(-24)}" y2="{y(-24)}" stroke="var(--tinta)" stroke-width="1.5"/>
  <text x="278" y="{y(-28)}" class="eixo-tx" font-weight="640" fill="var(--tinta)">
    continuacao &mdash; entra no fechamento dela</text>

  <!-- anotacoes a direita -->
  <text x="304" y="{y(176)}" class="eixo-tx" fill="var(--tinta2)">
    os dois extremos do par</text>
  <text x="304" y="{y(160)}" class="eixo-tx" fill="var(--tinta2)">
    ficam do lado de fora da Hull</text>
  <text x="304" y="{y(136)}" class="eixo-tx" fill="var(--tinta2)">
    e a EMA 21 passa entre</text>
  <text x="304" y="{y(120)}" class="eixo-tx" fill="var(--tinta2)">
    os topos e os fundos deles</text>
</svg>
</div>"""


def padrao(D):
    de = D['descricao']; P = D['parametros']
    nt = {x['nivel']: x for x in D['niveis_terco']}
    cartoes = ''
    for niv in ('ouro', 'prata', 'bronze'):
        v = D['variantes'][f'fecha|parcial|{niv}']['stats']
        r = nt[niv]
        tercos = ' &middot; '.join(
            f"{x['terco']} {sn(x['ev'], 0)}" for x in r['por_terco'])
        cartoes += f"""
    <div class="diag">
      <h3><span class="pt" style="background:var(--{niv})"></span>
          Padrao {D['rotulo'][niv]}</h3>
      <p style="font-size:14px;color:var(--tinta2)">{de[niv]}</p>
      <div class="grade g2 mini" style="gap:10px">
        {tile('Por trade', sn(r['ev'], 1) + ' pts', f"{r['n']} sinais", cls(r['ev']))}
        {tile('Na carteira', sn(v['lucro_liq']) + ' pts',
              f"{v['trades']} trades &middot; acerto {n(v['winrate'], 1)}%",
              cls(v['lucro_liq']))}
      </div>
      <p class="nota">por terco do periodo: {tercos} pts</p>
    </div>"""

    cz = D['estudos']['cruz_exaustao']
    linhas_cz = ''
    for r in cz:
        cels = ''.join(
            f'<td><b class="{cls(c["ev"])}">{sn(c["ev"], 1)}</b> pts'
            f'<br><small style="color:var(--mudo)">{c["n"]} sinais &middot; '
            f'{n(c["wr"], 1)}%</small></td>' for c in r['celulas'])
        linhas_cz += f'<tr><td>{r["lin"]}</td>{cels}</tr>'

    return f"""
<section id="padrao">
  <h2>O padrao, e os tres niveis</h2>
  <p class="olho">A regra-base e a do CLAUDE.md, sem nada acrescentado: uma retracao,
  um candle de continuacao, os dois extremos do par para fora da Hull, a Hull no sentido
  do trade e a EMA 21 atravessando o par. Sobre ela, os filtros que a medicao aprovou
  montam tres niveis <b>encaixados</b> &mdash; todo Ouro e tambem Prata, todo Prata e
  tambem Bronze.</p>
  <div class="card">{diagrama_padrao()}
    <figcaption>Padrao de compra. O de venda e o espelho exato: retracao de alta,
    candle de continuacao de baixa, os dois fundos abaixo de uma Hull descendente.</figcaption>
  </div>
  <div class="grade g3" style="margin-top:16px">{cartoes}</div>

  <h3 style="margin-top:36px">O veto de exaustao, que e o filtro que mais separa</h3>
  <p class="olho">O CLAUDE.md ja desconfiava: <i>"quando a HULL se encontra perto da
  banda superior, indica exaustao"</i>. A banda, sozinha, nao separa nada. Mas a
  intuicao estava certa no alvo errado: o que separa e a <b>combinacao</b> de uma Hull
  que esta abrindo a curva a favor do trade com um preco que <b>ja</b> se afastou da
  EMA 21. Cada metade, isolada, quase nao diz nada; juntas marcam 272 dos
  {D['n_sinais']['confirmados']} sinais e esses 272 nao pagam.</p>
  <div class="card rolo">
    <table>
      <thead><tr><th></th>
        <th>preco perto da EMA<br><small>ate {n(P['estic_exaustao'], 2)} ATR</small></th>
        <th>preco esticado da EMA<br><small>mais de {n(P['estic_exaustao'], 2)} ATR</small></th>
      </tr></thead>
      <tbody>{linhas_cz}</tbody>
    </table>
    <p class="nota">Valor esperado por trade, no conjunto sem filtro nenhum. A celula de
    baixo a direita e o que o veto joga fora.</p>
  </div>
</section>"""


# ------------------------------------------------------- estatisticas padrao MT5
LINHAS_MT5 = [
    ('Lucro liquido total', lambda s: sn(s['lucro_liq']) + ' pts', 'lucro_liq'),
    ('Lucro liquido total (R$, 1 contrato)', lambda s: 'R$ ' + sn(s['lucro_liq_rs']), 'lucro_liq'),
    ('Lucro bruto', lambda s: sn(s['lucro_bruto']) + ' pts', None),
    ('Prejuizo bruto', lambda s: sn(s['prej_bruto']) + ' pts', None),
    ('Fator de lucro', lambda s: n(s['fator_lucro'], 2), None),
    ('Payoff esperado', lambda s: sn(s['exp_pts'], 2) + ' pts', 'exp_pts'),
    ('Indice de Sharpe (por trade)', lambda s: n(s['sharpe'], 3), None),
    ('Correlacao LR', lambda s: n(s['lr_corr'], 3), None),
    ('Erro LR maximo', lambda s: n(s['lr_erro']) + ' pts', None),
    ('Rebaixamento maximo', lambda s: n(s['dd_max']) + ' pts', None),
    ('Rebaixamento maximo (R$)', lambda s: 'R$ ' + n(s['dd_max_rs']), None),
    ('Fator de recuperacao', lambda s: n(s['recovery'], 2), None),
    ('Total de negocios', lambda s: n(s['trades']), None),
    ('Taxa de acerto (winrate)', lambda s: n(s['winrate'], 2) + '%', None),
    ('Negocios vencedores', lambda s: f"{n(s['vitorias'])} ({n(s['vitorias'] / s['trades'] * 100, 2)}%)", None),
    ('Negocios zerados', lambda s: f"{n(s['zeros'])} ({n(s['zeros_pct'], 2)}%)", None),
    ('Negocios perdedores', lambda s: f"{n(s['derrotas'])} ({n(s['derrotas'] / s['trades'] * 100, 2)}%)", None),
    ('Negocios de compra', lambda s: f"{n(s['longs'])} ({n(s['longs_wr'], 1)}% de acerto)", None),
    ('Negocios de venda', lambda s: f"{n(s['shorts'])} ({n(s['shorts_wr'], 1)}% de acerto)", None),
    ('Maior negocio vencedor', lambda s: sn(s['maior_ganho']) + ' pts', None),
    ('Maior negocio perdedor', lambda s: sn(s['maior_perda']) + ' pts', None),
    ('Negocio vencedor medio', lambda s: sn(s['media_ganho'], 1) + ' pts', None),
    ('Negocio perdedor medio', lambda s: sn(s['media_perda'], 1) + ' pts', None),
    ('Maximo de vitorias consecutivas', lambda s: f"{s['max_seq_ganho']} ({sn(s['max_soma_ganho'])} pts)", None),
    ('Maximo de perdas consecutivas', lambda s: f"{s['max_seq_perda']} ({sn(s['max_soma_perda'])} pts)", None),
    ('Saidas no alvo', lambda s: n(s['alvos']), None),
    ('Saidas no stop', lambda s: n(s['stops']), None),
    ('Saidas zero a zero (apos a parcial)', lambda s: n(s['stops_zero']), None),
    ('Saidas por tempo / fim de pregao', lambda s: n(s['timeouts'] + s['fins_dia']), None),
    ('MEP media (excursao a favor)', lambda s: sn(s['mfe_media'], 1) + ' pts', None),
    ('MEN media (excursao contra)', lambda s: sn(s['mae_media'], 1) + ' pts', None),
    ('Duracao mediana', lambda s: n(s['dur_mediana'] / 60, 1) + ' min', None),
    ('Candles por negocio (mediana)', lambda s: n(s['barras_mediana'], 0), None),
    ('Negocios por pregao', lambda s: n(s['trades_dia'], 1), None),
    ('Pontos por pregao', lambda s: sn(s['pts_dia'], 1) + ' pts', 'pts_dia'),
]


def galeria(D):
    """A secao de exemplos: seis padroes de cada nivel, para decorar a forma."""
    blocos = ''
    for niv in ('ouro', 'prata', 'bronze'):
        itens = D['galeria'].get(niv, [])
        if not itens:
            continue
        cartoes = ''
        for k, ex in enumerate(itens):
            res = ('empatou' if abs(ex['pts']) < 1e-9
                   else ('ganhou' if ex['pts'] > 0 else 'perdeu'))
            cartoes += f"""
      <figure class="ex">
        <div class="ex-topo">
          <span class="ex-data">{ex['data']} &middot;
            {'compra' if ex['lado'] > 0 else 'venda'}</span>
          <span class="ex-res {cls(ex['pts'])}">{sn(ex['pts'])} pts</span>
        </div>
        <div id="gal_{niv}_{k}" class="ex-viz"></div>
        <figcaption>{ex['motivo'][0].upper() + ex['motivo'][1:]}.
          Retracao de {ex['n_ret']} candle{'s' if ex['n_ret'] > 1 else ''},
          pavio de {n(ex['pav_tot'])} pts. Saiu no {ex['rot_saida']} &mdash;
          {res}.</figcaption>
      </figure>"""
        v = D['variantes'][f'fecha|parcial|{niv}']['stats']
        blocos += f"""
  <h3 style="margin-top:34px;display:flex;align-items:center;gap:8px">
    <span class="pt" style="background:var(--{niv});width:11px;height:11px"></span>
    Padrao {D['rotulo'][niv]}
    <span style="font-weight:500;color:var(--mudo);font-size:13.5px">
      &middot; {D['descricao'][niv]}</span>
  </h3>
  <div class="grade g3 galeria">{cartoes}</div>"""

    return f"""
<section id="galeria">
  <h2>Galeria: como o padrao se parece</h2>
  <p class="olho">Seis exemplos reais de cada nivel, tirados do proprio backteste e
  espalhados pelo periodo inteiro. A faixa clara e o par <b>retracao + continuacao</b>;
  a seta e a entrada; as linhas sao stop, parcial e alvo. A <b>Hull 50</b> e a linha
  grossa amarela, a <b>EMA 21</b> a azul.</p>
  <div class="bandeira">
    <h3>Leia a forma, nao o resultado</h3>
    <p style="margin-bottom:0">Cada exemplo mostra quanto deu, e a galeria tem
    ganhos e perdas <b>na mesma proporcao em que eles acontecem</b> &mdash; com acerto
    de {n(D['variantes'][D['escolhida']]['stats']['winrate'], 0)}%, a maioria dos
    exemplos de qualquer nivel vai ser de perda. Uma galeria so de acertos ensinaria
    a reconhecer sorte. O que ha para decorar aqui e o <b>desenho</b>: onde a Hull
    passa, quantos candles a retracao tem, e o tamanho do pavio do candle que
    retoma.</p>
  </div>
  {blocos}
</section>"""


def estatisticas(D):

    chaves = list(D['variantes'])
    ordem = ['fecha|parcial|ouro', 'fecha|parcial|prata', 'fecha|parcial|bronze',
             'fecha|puro|ouro', 'fecha|r2|ouro',
             'meio_lim|parcial|prata', 'antecipa|parcial|prata']
    chaves = [k for k in ordem if k in chaves]

    abas = ''.join(
        f'<button class="aba" data-chave="{k}" '
        f'aria-pressed="{str(k == D["escolhida"]).lower()}">'
        f'{D["rotulo"][D["variantes"][k]["nivel"]]} &middot; '
        f'{ROT_MODO[D["variantes"][k]["modo"]].split()[0].lower()} &middot; '
        f'{ROT_GESTAO[D["variantes"][k]["gestao"]]}'
        f'</button>' for k in chaves)

    paineis = ''
    for k in chaves:
        v = D['variantes'][k]; s = v['stats']
        meio = len(LINHAS_MT5) // 2 + 1
        col1 = ''.join(f'<tr><td>{r[0]}</td><td class="{cls(s.get(r[2])) if r[2] else ""}">'
                       f'{r[1](s)}</td></tr>' for r in LINHAS_MT5[:meio])
        col2 = ''.join(f'<tr><td>{r[0]}</td><td class="{cls(s.get(r[2])) if r[2] else ""}">'
                       f'{r[1](s)}</td></tr>' for r in LINHAS_MT5[meio:])
        paineis += f"""
    <div data-painel="stats" data-chave="{k}" {'' if k == D['escolhida'] else 'hidden'}>
      <div class="card">
        <h3>{D['rotulo'][v['nivel']]} &middot; {ROT_MODO[v['modo']]} &middot;
            {ROT_GESTAO[v['gestao']]}</h3>
        <div class="grade g2">
          <div class="rolo"><table><tbody>{col1}</tbody></table></div>
          <div class="rolo"><table><tbody>{col2}</tbody></table></div>
        </div>
      </div>
    </div>"""

    # matriz completa
    linhas = ''
    for k, v in D['variantes'].items():
        s = v['stats']
        d = ' class="destaque"' if k == D['escolhida'] else ''
        linhas += (f'<tr{d}><td>{ROT_MODO[v["modo"]]}</td>'
                   f'<td style="text-align:left">{ROT_GESTAO[v["gestao"]]}</td>'
                   f'<td style="text-align:left"><span class="tag">'
                   f'<span class="pt" style="background:var(--{v["nivel"]})"></span>'
                   f'{D["rotulo"][v["nivel"]]}</span></td>'
                   f'<td>{n(s["trades"])}</td>'
                   f'<td class="{cls(s["lucro_liq"])}">{sn(s["lucro_liq"])}</td>'
                   f'<td class="{cls(s["exp_pts"])}">{sn(s["exp_pts"], 1)}</td>'
                   f'<td>{n(s["winrate"], 1)}%</td>'
                   f'<td>{n(s["fator_lucro"], 2)}</td>'
                   f'<td>{n(s["dd_max"])}</td>'
                   f'<td>{n(s["recovery"], 2)}</td></tr>')

    return f"""
<section id="estatisticas">
  <h2>Estatisticas</h2>
  <p class="olho">O bloco no formato do relatorio do MetaTrader 5, com o winrate
  acrescentado, para cada combinacao de nivel, modo de entrada e gestao. Tudo em pontos
  do WINFUT; a conversao em reais e de 1 contrato a R$ 0,20 por ponto.</p>
  <div class="abas" data-abas="stats">{abas}</div>
  {paineis}

  <h3 style="margin-top:36px">A matriz inteira</h3>
  <div class="card rolo">
    <table>
      <thead><tr><th>Entrada</th><th>Gestao</th><th>Nivel</th><th>Trades</th>
        <th>Pontos</th><th>Por trade</th><th>Acerto</th><th>Fator</th>
        <th>Rebaix.</th><th>Recup.</th></tr></thead>
      <tbody>{linhas}</tbody>
    </table>
    <p class="nota">A linha destacada e a variante levada adiante. O nivel Ouro nao
    existe na entrada antecipada: ele depende da forma do candle de continuacao, que
    nessa entrada ainda nao terminou de se formar na hora da decisao.</p>
  </div>
</section>"""


def patrimonio(D):
    return """
<section id="patrimonio">
  <h2>Evolucao do patrimonio</h2>
  <p class="olho">Curvas em pontos, uma posicao por vez. Sem juros e sem
  reinvestimento: e a soma simples do resultado de cada operacao com um contrato.
  O eixo horizontal e o <b>tempo</b>, nao o numero do trade &mdash; as variantes fazem
  contagens de operacoes bem diferentes, e num eixo de numero de trade a curva mais
  seletiva pareceria parar no meio do grafico.</p>

  <div class="card">
    <h3>Os tres niveis</h3>
    <div class="legenda">
      <span><i class="chave" style="background:var(--ouro)"></i>Ouro</span>
      <span><i class="chave" style="background:var(--prata)"></i>Prata</span>
      <span><i class="chave" style="background:var(--bronze)"></i>Bronze</span>
    </div>
    <figure><div id="eq_niveis"></div>
      <figcaption>Entrada no fechamento, com parcial. O Bronze termina mais alto
      porque faz quase quatro vezes mais trades &mdash; e paga por isso com o dobro do
      rebaixamento.</figcaption></figure>
  </div>

  <div class="grade g2" style="margin-top:16px">
    <div class="card">
      <h3>Os tres modos de entrada</h3>
      <div class="legenda">
        <span><i class="chave" style="background:var(--ouro)"></i>Fechamento</span>
        <span><i class="chave" style="background:var(--prata)"></i>Limitada no meio</span>
        <span><i class="chave" style="background:var(--bronze)"></i>Stop no meio</span>
      </div>
      <figure><div id="eq_modos"></div>
        <figcaption>Nivel Prata, o unico que os tres modos alcancam.</figcaption></figure>
    </div>
    <div class="card">
      <h3>Com e sem a parcial</h3>
      <div class="legenda">
        <span><i class="chave" style="background:var(--ouro)"></i>Com parcial em +100</span>
        <span><i class="chave" style="background:var(--prata)"></i>Sem parcial</span>
      </div>
      <figure><div id="eq_gestao"></div>
        <figcaption>Nivel Ouro. A parcial troca altura por suavidade.</figcaption></figure>
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <h3>Resultado pregao a pregao</h3>
    <figure><div id="diario"></div>
      <figcaption>Padrao Ouro, entrada no fechamento, com parcial. Um contrato.</figcaption></figure>
  </div>
</section>"""


def distribuicao(D):
    s = D['variantes'][D['escolhida']]['stats']
    return f"""
<section id="distribuicao">
  <h2>Distribuicao dos resultados</h2>
  <p class="olho">O perfil da estrategia e o de um alvo distante: erra a maioria das
  vezes e vive das poucas que acerta. Com o alvo em {n(D['parametros']['alvo'])} e o
  stop em {n(D['parametros']['stop'])}, {n(s['winrate'], 1)}% de acerto ja bastam.</p>
  <div class="card">
    <h3>Resultado por operacao</h3>
    <figure><div id="hist_pnl"></div>
      <figcaption>Faixas de 50 pontos. Com a parcial ligada, o desfecho e quase
      sempre um de tres: &minus;100 no stop, 0 no zero a zero depois da parcial, ou
      +200 no alvo (metade em +100 e metade em +300). Os poucos valores fora disso
      sao saidas por fim de pregao.</figcaption></figure>
  </div>
  <div class="grade g2" style="margin-top:16px">
    <div class="card">
      <h3>MEP &mdash; maxima excursao positiva</h3>
      <figure><div id="hist_mep"></div>
        <figcaption>Quanto cada operacao chegou a ter a favor, antes de terminar.
        Media {sn(s['mfe_media'], 1)} pts.</figcaption></figure>
    </div>
    <div class="card">
      <h3>MEN &mdash; maxima excursao negativa</h3>
      <figure><div id="hist_men"></div>
        <figcaption>Quanto cada operacao chegou a ter contra. Media
        {sn(s['mae_media'], 1)} pts &mdash; o stop de {n(D['parametros']['stop'])}
        corta a cauda.</figcaption></figure>
    </div>
  </div>
</section>

<section id="duracao">
  <h2>Duracao das operacoes</h2>
  <p class="olho">No grafico de PI o tempo nao e uniforme: um candle pode levar
  segundos ou minutos. Vale medir a duracao das duas formas &mdash; em relogio e em
  candles.</p>
  <div class="grade g2">
    <div class="card">
      <h3>Em tempo de relogio</h3>
      <figure><div id="hist_dur"></div>
        <figcaption>Mediana de {n(s['dur_mediana'] / 60, 1)} minutos.</figcaption></figure>
    </div>
    <div class="card">
      <h3>Em candles</h3>
      <figure><div id="hist_barras"></div>
        <figcaption>Mediana de {n(s['barras_mediana'])} candles de 20 PI.</figcaption></figure>
    </div>
  </div>
</section>"""


BLOCOS_FILTRO = [
    ('concavidade', 'A concavidade da Hull',
     'O CLAUDE.md pede a Hull "preferivelmente concava". Medida, ela mede ao '
     'contrario: a metade em que a Hull esta <b>fechando</b> a curva rende mais do '
     'que a metade em que ela esta abrindo &mdash; e nos tres tercos do periodo. '
     'Como filtro isolado, portanto, ela nao entra. O que entra e a combinacao dela '
     'com o esticamento, que e o veto de exaustao.'),
    ('esticamento', 'A distancia do preco a EMA 21',
     'Entrar com o preco ainda colado na EMA 21 mede melhor do que entrar esticado. '
     'E a metade util do veto de exaustao.'),
    ('pavio', 'A geometria do candle que retoma &mdash; o pavio',
     'Como o corpo e sempre 100 pontos, o pavio total <b>e</b> a forma do candle. '
     'As duas pontas medem mal: o candle quase sem pavio e fino demais, e o de pavio '
     'enorme e briga, nao continuacao. O miolo paga, e paga nos tres tercos. Este e '
     'o filtro que separa o Ouro do Prata.'),
    ('pavio_favor', 'O pavio a favor do movimento',
     'Um pavio grande alem do fechamento significa que o movimento ja foi e voltou. '
     'Acima de 6% do range o sinal deixa de pagar.'),
    ('pavio_contra', 'O pavio contra o movimento',
     'Aqui o efeito e fraco e nao sobrevive a quebra por tercos: nao virou filtro.'),
    ('retracao_candles', 'O tamanho da retracao, em candles',
     'Um candle so de retracao nao e retracao, e ruido &mdash; e mede menos da '
     'metade do que duas ou tres. Acima de quatro a amostra acaba. Este filtro entra '
     'no nivel Prata.'),
    ('retracao_tamanho', 'O tamanho da retracao, em ATRs',
     'A mesma ideia medida em profundidade em vez de contagem de candles. Diz a '
     'mesma coisa; a contagem ficou por ser mais simples de ver no grafico.'),
    ('inclinacao_hull', 'A inclinacao da Hull',
     'Hull mais inclinada mede melhor, mas o ganho e pequeno e some quando somado '
     'aos outros filtros. Nao entrou.'),
    ('inclinacao_ema', 'A inclinacao da EMA 21',
     'O CLAUDE.md pede para avaliar. A resposta e que ela separa, sim, mas <b>ao contrario</b> do que um filtro de tendencia faria esperar: a EMA menos inclinada mede melhor. E nao ha o que ganhar ai, porque essa inclinacao tem correlacao de <b>0,78</b> com o esticamento do preco &mdash; e a mesma informacao, dita de outro jeito. Aplicado o veto de exaustao, o efeito some: as quatro faixas passam a medir +23,6 / +14,3 / +19,2 / +23,7 pontos, sem ordem nenhuma. Nao entrou.'),
    ('banda_keltner', 'A distancia da Hull a banda de Keltner',
     'A leitura literal &mdash; "Hull perto da banda indica exaustao" &mdash; nao '
     'aparece: a faixa mais perto da banda nao e a pior, e nem ha ordem. O canal, '
     'sozinho, nao e filtro. A intuicao por tras dele sobrevive no veto de exaustao.'),
    ('hull_colada', 'Ha quanto tempo a Hull esta colada na EMA',
     'A outra intuicao do CLAUDE.md &mdash; "quando a hull passa muito tempo perto '
     'da EMA 21 e sinal de consolidacao" &mdash; essa a medicao confirma, e com '
     'forca. Mais de 8 candles colada e o pior balde do estudo inteiro. Nao virou '
     'filtro oficial por causa do tamanho da amostra, mas esta anotado no plano '
     'como veto de mesa.'),
    ('hora', 'O horario',
     'Nenhuma faixa e boa ou ruim em todos os tercos, incluindo a hora seguinte a '
     'abertura do mercado a vista. Com 26 pregoes nao da para separar horario de '
     'sorte, e o filtro nao entrou.'),
]


def filtros(D):
    blocos = ''
    for chave, titulo, texto in BLOCOS_FILTRO:
        if chave not in D['estudos']:
            continue
        blocos += f"""
  <div class="card" style="margin-top:16px">
    <h3>{titulo}</h3>
    <p style="color:var(--tinta2);max-width:76ch">{texto}</p>
    <div class="grade g2" style="gap:22px">
      <figure><div id="t_{chave}"></div>
        <figcaption>Valor esperado por trade, periodo inteiro.</figcaption></figure>
      <figure>
        <div class="legenda">
          <span><i class="chave q" style="background:var(--ouro)"></i>1&ordm; terco</span>
          <span><i class="chave q" style="background:var(--prata)"></i>2&ordm; terco</span>
          <span><i class="chave q" style="background:var(--bronze)"></i>3&ordm; terco</span>
        </div>
        <div id="f_{chave}"></div>
        <figcaption>O mesmo, quebrado em tercos do periodo. Um efeito de verdade
        aparece nos tres.</figcaption></figure>
    </div>
  </div>"""
    return f"""
<section id="filtros">
  <h2>Cada filtro, medido</h2>
  <p class="olho">Tudo aqui foi medido no conjunto <b>sem filtro nenhum</b> &mdash; os
  {D['n_sinais']['confirmados']} sinais da regra-base, entrada no fechamento, com
  parcial. Ao lado de cada faixa vai o mesmo numero quebrado em tercos do periodo: e o
  teste mais duro que 26 pregoes permitem. Faixa que so paga num terco nao e filtro, e
  sorte, e nao entrou em nenhum nivel.</p>
  <div class="bandeira">
    <h3>Por que os filtros nao se somam</h3>
    <p style="margin-bottom:0">Empilhar os quatro melhores filtros ao mesmo tempo deixa
    16 sinais e valor esperado <b>negativo</b>. Nao e paradoxo: cada corte tira sinais,
    e a partir de certo ponto o que sobra e uma amostra pequena demais para significar
    qualquer coisa. Os niveis Ouro e Prata usam tres filtros, nao os oito que mediram
    algo.</p>
  </div>
  {blocos}
</section>"""


def gestao(D):
    P = D['parametros']
    o = D['variantes']['fecha|parcial|ouro']['stats']
    pu = D['variantes']['fecha|puro|ouro']['stats']
    return f"""
<section id="gestao">
  <h2>Stop, alvo e a parcial</h2>
  <p class="olho">A grade abaixo roda o nivel Ouro inteiro em 36 combinacoes de stop e
  alvo. O quadro com contorno e o do CLAUDE.md. Ele nao e o maior numero da grade, mas
  esta num <b>topo local</b> em alvo &mdash; 300 mede melhor que 250 e que 400 &mdash;
  e e o melhor da coluna quando o resultado e dividido pelo risco assumido.</p>
  <div class="abas" data-abas="grade">
    <button class="aba" data-chave="puro" aria-pressed="true">Sem parcial</button>
    <button class="aba" data-chave="parcial" aria-pressed="false">Com parcial</button>
  </div>
  <div data-painel="grade" data-chave="puro">
    <div class="card"><figure><div id="grade_puro"></div>
      <figcaption>Valor esperado por trade, em pontos. Passe o mouse para ver acerto,
      total e o resultado por ponto de risco.</figcaption></figure></div>
  </div>
  <div data-painel="grade" data-chave="parcial" hidden>
    <div class="card"><figure><div id="grade_parcial"></div>
      <figcaption>A mesma grade com a parcial de 50% ligada.</figcaption></figure></div>
  </div>

  <div class="grade g2" style="margin-top:16px">
    <div class="card">
      <h3>A parcial, em numeros</h3>
      <p style="color:var(--tinta2)">Com a parcial em +{n(P['parcial_em'])} e o stop do
      restante na <b>media da operacao</b>, o stop na verdade <b>nao anda</b>: com meia
      posicao e a parcial na mesma distancia do stop, o preco em que o lucro ja
      realizado cancela a perda do restante <i>e</i> o stop inicial. O que muda nao e
      o preco &mdash; e o fato de que so metade da posicao ainda corre risco. Por isso
      "zero a zero" aqui e zero de verdade, e nao um ganho disfarcado.</p>
      <div class="rolo"><table>
        <thead><tr><th></th><th>Com parcial</th><th>Sem parcial</th></tr></thead>
        <tbody>
          <tr><td>Total</td><td class="{cls(o['lucro_liq'])}">{sn(o['lucro_liq'])} pts</td>
              <td class="{cls(pu['lucro_liq'])}">{sn(pu['lucro_liq'])} pts</td></tr>
          <tr><td>Por trade</td><td>{sn(o['exp_pts'], 1)}</td><td>{sn(pu['exp_pts'], 1)}</td></tr>
          <tr><td>Fator de lucro</td><td>{n(o['fator_lucro'], 2)}</td><td>{n(pu['fator_lucro'], 2)}</td></tr>
          <tr><td>Rebaixamento maximo</td><td>{n(o['dd_max'])} pts</td><td>{n(pu['dd_max'])} pts</td></tr>
          <tr><td>Fator de recuperacao</td><td>{n(o['recovery'], 2)}</td><td>{n(pu['recovery'], 2)}</td></tr>
          <tr><td>Operacoes zeradas</td><td>{n(o['zeros'])}</td><td>{n(pu['zeros'])}</td></tr>
          <tr><td>Maior perda</td><td>{sn(o['maior_perda'])} pts</td><td>{sn(pu['maior_perda'])} pts</td></tr>
        </tbody></table></div>
      <p class="nota">A parcial entrega {n(abs(pu['lucro_liq'] - o['lucro_liq']) / pu['lucro_liq'] * 100, 0)}%
      do lucro em troca de um rebaixamento {n((1 - o['dd_max'] / pu['dd_max']) * 100, 0)}%
      menor e de um fator de lucro melhor. E uma troca de conforto, e e uma escolha
      de quem opera, nao um resultado do backteste.</p>
    </div>
    <div class="card">
      <h3>Periodos de media</h3>
      <p style="color:var(--tinta2)">A EMA e sempre a linha do meio do Keltner, como
      manda o CLAUDE.md &mdash; entao ela e o ATR andam juntos. A Hull 50 ganha de
      21, 34 e 80 em <b>todas</b> as EMAs testadas: o pico nao e uma celula sortuda,
      e uma crista.</p>
      <figure><div id="medias"></div>
        <figcaption>Valor esperado por trade no nivel Ouro.</figcaption></figure>
    </div>
  </div>
</section>"""


def risco_retorno(D):
    """A secao do 1:2 sem parcial -- e por que o 1:3 continua ganhando."""
    P = D['parametros']
    o3 = D['variantes']['fecha|puro|ouro']['stats']
    o2 = D['variantes']['fecha|r2|ouro']['stats']
    op = D['variantes']['fecha|parcial|ouro']['stats']
    mc2 = D['monte_carlo'].get('fecha|r2|ouro', {})

    # a linha do stop de 100, que e a comparacao direta pedida
    linha100 = next(l for l in D['rr'] if l[0]['stop'] == int(P['stop']))
    cels = ''.join(
        f'<td{" class=destaque" if c["razao"] == 3 else ""}>'
        f'<b class="{cls(c["ev"])}">{sn(c["ev"], 1)}</b> pts<br>'
        f'<small style="color:var(--mudo)">acerto {n(c["wr"], 1)}% &middot; '
        f'por risco {n(c["ev_risco"], 2)}</small></td>' for c in linha100)

    comp = ''
    for rot, st in (('1:3 com parcial', op), ('1:3 sem parcial', o3),
                    ('1:2 sem parcial', o2)):
        d = ' class="destaque"' if rot == '1:3 sem parcial' else ''
        comp += (f'<tr{d}><td>{rot}</td>'
                 f'<td class="{cls(st["lucro_liq"])}">{sn(st["lucro_liq"])}</td>'
                 f'<td class="{cls(st["exp_pts"])}">{sn(st["exp_pts"], 1)}</td>'
                 f'<td>{n(st["winrate"], 1)}%</td>'
                 f'<td>{n(st["fator_lucro"], 2)}</td>'
                 f'<td>{n(st["dd_max"])}</td>'
                 f'<td>{n(st["recovery"], 2)}</td>'
                 f'<td>{n(st["exp_pts"] / P["stop"], 2)}</td></tr>')

    return f"""
<section id="rr">
  <h2>Risco : retorno &mdash; o 1:2 sem parcial</h2>
  <p class="olho">Alvo em pontos nao quer dizer nada sem o stop ao lado: 300 pontos
  com stop de 100 e 300 com stop de 300 sao apostas completamente diferentes. A
  comparacao justa e o alvo <b>relativo</b> ao stop, e a medida que a torna
  comparavel entre stops e o resultado <b>por ponto de risco</b>.</p>

  <h3>Com o stop de {n(P['stop'])} pontos, lado a lado</h3>
  <div class="card rolo">
    <table>
      <thead><tr><th>Alvo</th>
        {''.join(f'<th>1:{c["razao"]} &middot; {n(c["alvo"])} pts</th>' for c in linha100)}
      </tr></thead>
      <tbody><tr><td>Por operacao</td>{cels}</tr></tbody>
    </table>
    <p class="nota">Nivel Ouro, sem parcial. O 1:2 mede <b>positivo</b> &mdash; nao e
    uma opcao ruim &mdash; mas ao mesmo stop ele entrega
    {sn(linha100[1]['ev'], 1)} pts contra {sn(linha100[2]['ev'], 1)} do 1:3, quase a
    metade, e compra com isso {n(linha100[1]['wr'] - linha100[2]['wr'], 1)} pontos
    percentuais de acerto. O 1:3 e o topo da linha, e por larga margem.</p>
  </div>

  <h3 style="margin-top:34px">As tres gestoes, na carteira</h3>
  <div class="card rolo">
    <table>
      <thead><tr><th>Gestao</th><th>Pontos</th><th>Por trade</th><th>Acerto</th>
        <th>Fator</th><th>Rebaix.</th><th>Recup.</th><th>Por risco</th></tr></thead>
      <tbody>{comp}</tbody>
    </table>
    <p class="nota">Nivel Ouro, entrada no fechamento. O 1:2 termina com
    {sn(o2['lucro_liq'])} pts contra {sn(o3['lucro_liq'])} do 1:3 puro, e com
    rebaixamento maior ({n(o2['dd_max'])} contra {n(o3['dd_max'])}). Ele ganha em
    uma coisa so: acerto, {n(o2['winrate'], 1)}% contra {n(o3['winrate'], 1)}%.
    {('Monte Carlo do 1:2: probabilidade de lucro ' + n(mc2['prob_lucro'], 1) + '%.'
      ) if mc2 else ''}</p>
  </div>

  <h3 style="margin-top:34px">A diagonal inteira</h3>
  <p class="olho">A mesma pergunta em oito tamanhos de stop, de {n(D['rr'][0][0]['stop'])}
  a {n(D['rr'][-1][0]['stop'])} pontos. Cada celula e o valor esperado por trade; a cor
  segue o resultado <b>por ponto de risco</b>, que e o unico numero comparavel entre
  linhas.</p>
  <div class="card">
    <figure><div id="rr_calor"></div>
      <figcaption>Nivel Ouro, sem parcial. Passe o mouse para ver acerto, total,
      rebaixamento e a quebra por tercos do periodo.</figcaption></figure>
  </div>
  <div class="bandeira">
    <h3>O que a diagonal mostra</h3>
    <ul class="enx" style="margin-bottom:0">
      <li>Nenhuma celula da tabela e negativa. O setup nao depende de acertar a
      relacao risco:retorno &mdash; ele paga em todas.</li>
      <li>Por ponto de risco, o melhor da tabela inteira e o <b>1:3 com stop
      curto</b> ({n(P['stop'])} ou menos). Stops largos rendem mais em pontos
      absolutos e menos por unidade de risco &mdash; e exigem mais capital para o
      mesmo numero de contratos.</li>
      <li>O 1:1 e o que tem melhor acerto (perto de 60%) e o pior resultado por
      risco em quase toda a tabela. Acerto alto nao e o objetivo.</li>
    </ul>
  </div>
</section>"""


def fluxo_sec(D):
    """Agressao, tempo de barra e forca de tendencia -- e por que nada entrou."""
    F = D.get('fluxo')
    if not F:
        return ''
    B, esp = F['base'], F['espaco']
    pen = {r['nivel']: r for r in F['peneira']}

    lin = ''
    for niv in ('ouro', 'prata', 'bronze'):
        r = pen[niv]
        m, fo = r['melhor'], r['fora']
        lin += (f'<tr><td><span class="tag"><span class="pt" '
                f'style="background:var(--{niv})"></span>{D["rotulo"][niv]}</span></td>'
                f'<td>{m["rotulo"]} {m["sentido"]}</td>'
                f'<td>{n(m["n"])}</td>'
                f'<td class="{cls(m["ev"])}">{sn(m["ev"], 1)}</td>'
                f'<td><b>{sn(m["t"], 2)}</b></td>'
                f'<td style="color:var(--mudo)">{sn(r["ruido_mediana"], 2)}</td>'
                f'<td style="color:var(--mudo)">{sn(r["ruido_p90"], 2)}</td>'
                f'<td><b>{n(r["p_valor"], 2)}</b></td>'
                f'<td class="{cls(fo["ev_t3"])}">{sn(fo["ev_t3"], 1)}</td>'
                f'<td style="color:var(--mudo)">{sn(fo["ev_t3_base"], 1)}</td></tr>')

    hp = ''
    base_ouro = 0.0
    for h in F['hipoteses']:
        if h['nivel'] != 'ouro':
            continue
        base_ouro = h['base']
        te = ''.join(f'<td class="{cls(v)}">{sn(v, 0)}</td>' for v in h['tercos'])
        hp += (f'<tr><td style="max-width:34ch">{h["rotulo"]}</td>'
               f'<td>{n(h["n"])}</td>'
               f'<td class="{cls(h["ev"])}">{sn(h["ev"], 1)}</td>'
               f'<td>{sn(h["ganho"], 1)}</td>{te}'
               f'<td><b>{n(h["p_valor"], 2)}</b></td></tr>')

    pw = ''
    for r in F['poder']:
        cel = ''.join(f'<td>{sn(x["min_ganho"], 0)}<br>'
                      f'<small style="color:var(--mudo)">n={x["n"]}</small></td>'
                      for x in r['linhas'])
        pw += (f'<tr><td><span class="tag"><span class="pt" '
               f'style="background:var(--{r["nivel"]})"></span>'
               f'{D["rotulo"][r["nivel"]]}</span></td>'
               f'<td>{n(r["n"])}</td><td>{n(r["desvio"])}</td>{cel}</tr>')

    # ---------------------------------------------- esforco x resultado
    EFR = F.get('esforco')
    bloco_ef = ''
    if EFR:
        nov = ''
        for r in EFR['novidade']:
            novo = abs(r['corr_pav']) < .25 and abs(r['corr_vol']) < .25 \
                and abs(r['corr_dur']) < .25
            nov += (f'<tr><td>{r["rotulo"]}</td>'
                    f'<td>{sn(r["corr_pav"], 2)}</td>'
                    f'<td>{sn(r["corr_vol"], 2)}</td>'
                    f'<td>{sn(r["corr_dur"], 2)}</td>'
                    f'<td>{"<b>nova</b>" if novo else "ja medida"}</td></tr>')

        qt = ''
        for k, r in enumerate(EFR['quintis']):
            rot = ('menor esforco' if k == 0 else
                   ('maior esforco' if k == len(EFR['quintis']) - 1 else ''))
            qt += (f'<tr><td>{r["faixa"]}'
                   + (f' <small style="color:var(--mudo)">{rot}</small>' if rot else '')
                   + f'</td>'
                   f'<td>{n(r["n"])}</td>'
                   f'<td class="{cls(r["ev"] - EFR["base_ouro"])}">{sn(r["ev"], 1)}</td></tr>')

        rh = ''.join(f'<tr><td>{D["rotulo"][r["nivel"]]}</td><td>{n(r["n"])}</td>'
                     f'<td><b>{sn(r["rho"], 3)}</b></td>'
                     f'<td>{n(r["p_valor"], 2)}</td></tr>'
                     for r in EFR['rho'])

        ct = ''.join(f'<tr><td>{D["rotulo"][r["nivel"]]}</td>'
                     f'<td style="color:var(--mudo)">{r.get("gestao", "")}</td>'
                     f'<td>{n(r["n"])}</td>'
                     f'<td class="{cls(r["ev"])}">{sn(r["ev"], 1)}</td>'
                     f'<td style="color:var(--mudo)">{sn(r["base"], 1)}</td>'
                     f'<td>{sn(r["ganho"], 1)}</td>'
                     + ''.join(f'<td class="{cls(v)}">{sn(v, 0)}</td>'
                               for v in r['tercos'])
                     + f'<td><b>{n(r["p_valor"], 2)}</b></td></tr>'
                     for r in EFR['cortes'])

        pwe = EFR['poder']
        q1 = EFR['quintis'][0]
        ro = EFR['rho'][-1]
        bloco_ef = f"""
  <h3 style="margin-top:30px">Esforco x resultado, na versao que o PI permite</h3>
  <p class="olho">No grafico de ticks a razao esforco/resultado precisa da divisao
  porque o resultado varia. <b>No PI o resultado esta fixo por construcao</b> &mdash;
  todo corpo vale 100 pontos &mdash; entao o esforco sozinho ja <i>e</i> a razao. A
  conta fica mais limpa; o que ela responde, infelizmente, nao muda.</p>

  <div class="bandeira">
    <h3>Metade da pergunta ja estava respondida</h3>
    <p style="margin-bottom:0">A leitura geometrica de esforco-resultado &mdash;
    resultado util sobre deslocamento total, <code>100 / range</code> &mdash; e
    <b>exatamente o filtro de pavio do Ouro</b>, escrito ao contrario:
    <code>range = 100 + pavio</code>, entao <code>100/range</code> e monotonico em
    pavio (correlacao de posto medida: <b>{sn(EFR['geom']['rho'], 4)}</b>, ou seja,
    a mesma informacao). Esse pedaco ja foi medido, ja paga, e ja e o degrau que
    separa Ouro de Prata. O que restava testar era o esforco em <b>volume, negocios
    e tempo</b>.</p>
  </div>

  <div class="grade g2" style="gap:22px;margin-top:16px">
    <div class="card">
      <h3>Isto e informacao nova?</h3>
      <div class="rolo"><table>
        <thead><tr><th>Variavel</th><th>corr. pavio</th><th>corr. volume</th>
          <th>corr. duracao</th><th></th></tr></thead>
        <tbody>{nov}</tbody></table></div>
      <p class="nota">&ldquo;Esforco do par&rdquo; e sempre <b>continuacao dividida
      pela retracao</b>: acima de 1, andar a favor saiu mais caro que andar contra.
      As tres razoes do par sao ortogonais a tudo que a estrategia ja usa &mdash;
      correlacao abaixo de 0,05 em modulo. Valia medir. Ja
      &ldquo;volume da continuacao&rdquo; e literalmente <code>vol_cont</code>
      (correlacao 1,00) e as outras duas replicam volume ou duracao, que reprovaram
      na secao anterior.</p>
    </div>
    <div class="card">
      <h3>A pergunta que decide a historia</h3>
      <div class="rolo"><table>
        <thead><tr><th>Faixa de esforco do par</th><th>Sinais</th><th>EV</th></tr></thead>
        <tbody>{qt}</tbody></table></div>
      <p class="nota">Se menos esforco fosse melhor, o quintil de <b>menor</b> esforco
      seria o maior. Ele mede {sn(q1['ev'], 1)} &mdash; <b>abaixo</b> da base do Ouro,
      que e {sn(EFR['base_ouro'], 1)}. Quem carrega o resultado e o segundo quintil,
      sozinho.</p>
    </div>
  </div>

  <div class="grade g2" style="gap:22px;margin-top:16px">
    <div class="card">
      <h3>Monotonicidade</h3>
      <div class="rolo"><table>
        <thead><tr><th>Nivel</th><th>Sinais</th><th>Correlacao de posto</th>
          <th>p <small>(unicaudal)</small></th></tr></thead>
        <tbody>{rh}</tbody></table></div>
      <p class="nota">Esforco do par contra resultado do trade. A tese de Wyckoff
      exige uma relacao monotonica; o que ha e {sn(ro['rho'], 3)} no Ouro, com
      p = {n(ro['p_valor'], 2)}. Nao ha relacao.</p>
    </div>
    <div class="card">
      <h3>O corte mais fiel: continuacao mais barata que a retracao</h3>
      <div class="rolo"><table>
        <thead><tr><th>Nivel</th><th>Gestao</th><th>n</th><th>EV</th><th>base</th>
          <th>ganho</th><th>1&ordm;</th><th>2&ordm;</th><th>3&ordm;</th>
          <th>p</th></tr></thead>
        <tbody>{ct}</tbody></table></div>
      <p class="nota">E o achado mais bonito de tres rodadas de investigacao: no Ouro
      com parcial da {sn(EFR['cortes'][1]['ganho'], 1)} pontos, positivo nos tres
      tercos. Mesmo
      assim <b>nao entra</b>: a analise de poder diz que um filtro que mantem
      {n(pwe['frac'], 0)}% dos sinais so seria detectavel acima de
      {sn(pwe['min_ganho'], 0)} pontos, e este alega {sn(pwe['observado'], 0)} &mdash;
      metade do limiar. E ele <b>depende da gestao</b>: trocar o alvo 1:3 pelo 1:2
      derruba o ganho para {sn(EFR['cortes'][-1]['ganho'], 1)} pontos. Um efeito de
      fluxo nao pode depender de qual alvo se usa &mdash; a gestao muda o desfecho do
      trade, nao a leitura do esforco. Somado a ausencia de monotonicidade, e um
      balde sortudo, nao um efeito.</p>
    </div>
  </div>"""

    o = pen['ouro']
    return f"""
<section id="fluxo">
  <h2>Agressao, tempo de barra e forca de tendencia</h2>
  <p class="olho">A base ganhou quatro colunas novas &mdash; volume agressor comprador e
  vendedor, duracao da barra, volume e numero de negocios. Num grafico de PI a duracao e
  a unica medida de <i>pressa</i> que existe: como todo corpo vale 100 pontos,
  100/duracao compara barra com barra direto. A mediana e {n(B['dur_mediana'])}&nbsp;s e
  o quartil de cima {n(B['dur_p75'])}&nbsp;s. <b>Nenhuma das quatro entrou em nenhum
  nivel</b>, e a razao esta abaixo.</p>

  <div class="grade g3">
    {tile('Atributos testados', n(esp['feats']),
          f"em {n(esp['cortes'])} cortes e 2 sentidos = {n(esp['total'])} comparacoes")}
    {tile('Melhor t no Ouro', sn(o['melhor']['t'], 2),
          f"a mesma busca em ruido acha {sn(o['ruido_mediana'], 2)}", 'perda')}
    {tile('Fora da amostra', sn(o['fora']['ev_t3'], 0) + ' pts',
          f"contra {sn(o['fora']['ev_t3_base'], 0)} sem filtro nenhum", 'perda')}
  </div>

  <div class="bandeira">
    <h3>Por que uma tabela bonita nao basta</h3>
    <p>Olhar {n(esp['total'])} combinacoes em {n(D['n_sinais']['confirmados'])} sinais
    garante que alguma vai parecer excelente &mdash; inclusive passando no teste dos
    tercos, que e o mais duro que este relatorio usa nas outras secoes. Entao a busca
    inteira foi repetida {n(esp['perms'])} vezes sobre versoes <b>embaralhadas</b> dos
    mesmos atributos: o embaralhamento preserva a distribuicao e destroi qualquer ligacao
    com o resultado, de modo que tudo o que a busca achar ali e, por construcao, sorte.</p>
    <p style="margin-bottom:0">O melhor filtro real do Ouro mede
    t&nbsp;=&nbsp;{sn(o['melhor']['t'], 2)}. A busca em ruido acha
    t&nbsp;=&nbsp;{sn(o['ruido_mediana'], 2)} na <b>mediana</b> e
    {sn(o['ruido_p90'], 2)} no percentil 90. O achado real e <i>pior</i> que o achado
    tipico em ruido puro.</p>
  </div>

  <div class="card" style="margin-top:16px">
    <h3>O veredito, nivel a nivel</h3>
    <div class="rolo"><table>
      <thead><tr><th>Nivel</th><th>Melhor filtro do espaco</th><th>Sinais</th>
        <th>EV</th><th>t</th><th>t em ruido<br><small>mediana</small></th>
        <th>t em ruido<br><small>p90</small></th><th>p</th>
        <th>3&ordm; terco<br><small>com o filtro</small></th>
        <th>3&ordm; terco<br><small>sem filtro</small></th></tr></thead>
      <tbody>{lin}</tbody></table></div>
    <p class="nota">As duas ultimas colunas sao a prova mais direta: o corte foi escolhido
    usando <b>so</b> os dois primeiros tercos e depois aplicado ao terceiro, que ele nunca
    viu. Nos dois niveis que importam ele transforma um terco lucrativo em prejuizo. Um
    filtro inutil seria inofensivo; estes atrapalham.</p>
  </div>

  <div class="grade g2" style="gap:22px;margin-top:16px">
    <figure>
      <div class="legenda">
        <span><i class="chave q" style="background:var(--ouro)"></i>melhor filtro real</span>
        <span><i class="chave q" style="background:var(--bronze)"></i>melhor em ruido (mediana)</span>
      </div>
      <div id="fx_ruido"></div>
      <figcaption>Estatistica t do melhor filtro que a busca acha, no dado real e em dado
      embaralhado. Barra clara maior que a escura = o achado e a busca, nao o atributo.</figcaption>
    </figure>
    <figure>
      <div class="legenda">
        <span><i class="chave q" style="background:var(--prata)"></i>sem filtro</span>
        <span><i class="chave q" style="background:var(--critico)"></i>com o filtro escolhido</span>
      </div>
      <div id="fx_fora"></div>
      <figcaption>Valor esperado por trade no 3&ordm; terco &mdash; o pedaco que nao
      participou da escolha do corte.</figcaption>
    </figure>
  </div>

  <div class="card" style="margin-top:16px">
    <h3>As duas hipoteses, uma a uma, no Ouro</h3>
    <p style="color:var(--tinta2);max-width:76ch">Aqui nao ha busca: cada linha e <b>um</b>
    teste, declarado antes de olhar, com o seu proprio p por permutacao. O Ouro sem filtro
    vale {sn(base_ouro, 1)} pontos por trade; a coluna &ldquo;ganho&rdquo; e a diferenca
    para essa base.</p>
    <div class="rolo"><table>
      <thead><tr><th>Hipotese</th><th>Sinais</th><th>EV</th><th>ganho</th>
        <th>1&ordm;</th><th>2&ordm;</th><th>3&ordm;</th><th>p</th></tr></thead>
      <tbody>{hp}</tbody></table></div>
    <p class="nota">&ldquo;Operacao contra a tendencia forte falha&rdquo; nao se confirma:
    exigir o trade a favor da deriva de 20 ou de 50 barras nao paga, e o unico corte com p
    baixo aponta para o lado <b>contrario</b> &mdash; o que, com 170 comparacoes ja feitas,
    e exatamente o que o acaso produz. &ldquo;A retracao logo depois de um cruzamento
    contundente&rdquo; tambem nao: o primeiro sinal apos o cruzamento mede praticamente
    igual a base. Vale lembrar que a regra-base <b>ja</b> exige a Hull 50 no sentido do
    trade &mdash; boa parte do filtro de tendencia que faltaria ja esta dentro dela.</p>
  </div>

  <div class="card" style="margin-top:16px">
    <h3>O que esta base conseguiria enxergar</h3>
    <div class="rolo"><table>
      <thead><tr><th>Nivel</th><th>Sinais</th><th>Desvio<br><small>por trade</small></th>
        <th>Filtro que mantem 50%</th><th>mantem 33%</th><th>mantem 25%</th></tr></thead>
      <tbody>{pw}</tbody></table></div>
    <p class="nota">Menor ganho de valor esperado, em pontos por trade, que esta amostra
    distingue de zero com 80% de poder a 5%. No Ouro, um filtro que corte dois tercos dos
    sinais precisaria valer mais de 40 pontos por trade para aparecer &mdash; mais que o
    proprio salto de Bronze para Ouro. <b>O resultado negativo desta secao nao e
    &ldquo;fluxo nao importa&rdquo;; e &ldquo;26 pregoes nao respondem&rdquo;.</b> Com
    alguns meses de agressao a pergunta volta a valer a pena, e o codigo que a responde
    ja esta pronto em estudo_fluxo.py.</p>
  </div>
  {bloco_ef}
</section>"""


def robustez(D):

    mc = D['monte_carlo'][D['escolhida']]
    nt = {x['nivel']: x for x in D['niveis_terco']}
    linhas = ''
    for niv in ('ouro', 'prata', 'bronze'):
        r = nt[niv]
        cel = ''.join(f'<td class="{cls(x["ev"])}">{sn(x["ev"], 1)}'
                      f'<br><small style="color:var(--mudo)">{x["n"]} sinais</small></td>'
                      for x in r['por_terco'])
        linhas += (f'<tr><td><span class="tag"><span class="pt" '
                   f'style="background:var(--{niv})"></span>{D["rotulo"][niv]}</span></td>'
                   f'{cel}<td class="{cls(r["ev"])}"><b>{sn(r["ev"], 1)}</b></td></tr>')

    mcl = ''
    for k in ('fecha|parcial|ouro', 'fecha|parcial|prata', 'fecha|parcial|bronze'):
        m = D['monte_carlo'].get(k)
        if not m:
            continue
        v = D['variantes'][k]
        mcl += (f'<tr><td>{D["rotulo"][v["nivel"]]}</td>'
                f'<td>{sn(m["total_p05"])}</td><td>{sn(m["total_mediana"])}</td>'
                f'<td>{sn(m["total_p95"])}</td><td>{n(m["prob_lucro"], 1)}%</td>'
                f'<td>{n(m["dd_p95"])}</td></tr>')

    return f"""
<section id="robustez">
  <h2>Robustez, e o tamanho do que nao da para saber</h2>
  <p class="olho">Vinte e seis pregoes sao pouco. Nada aqui substitui uma base maior; o
  que da para fazer e ser explicito sobre o que ainda nao foi testado, e e isso que esta
  nesta secao.</p>

  <div class="grade g2">
    <div class="card">
      <h3>Os tres niveis, terco a terco</h3>
      <div class="rolo"><table>
        <thead><tr><th>Nivel</th><th>1&ordm; terco</th><th>2&ordm; terco</th>
          <th>3&ordm; terco</th><th>Periodo</th></tr></thead>
        <tbody>{linhas}</tbody></table></div>
      <p class="nota">Valor esperado por trade, em pontos. Os tres niveis medem
      positivo nos tres tercos &mdash; e o Ouro e o mais parelho dos tres, apesar de
      ser o de menor amostra.</p>
    </div>
    <div class="card">
      <h3>Monte Carlo</h3>
      <div class="rolo"><table>
        <thead><tr><th>Nivel</th><th>p05</th><th>mediana</th><th>p95</th>
          <th>prob. de lucro</th><th>rebaix. p95</th></tr></thead>
        <tbody>{mcl}</tbody></table></div>
      <p class="nota">4.000 reamostragens dos trades com reposicao. Responde
      "quanto disso foi a ordem de chegada" &mdash; nao responde se o padrao continua
      valendo no mes que vem.</p>
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <figure><div id="mc"></div>
      <figcaption>Distribuicao do resultado total do padrao Ouro em 4.000
      reamostragens. Probabilidade de terminar no lucro: {n(mc['prob_lucro'], 1)}%.</figcaption>
    </figure>
  </div>

  <div class="card" style="margin-top:16px">
    <h3>Custo operacional</h3>
    <p style="color:var(--tinta2)">Todos os numeros deste relatorio sao <b>brutos</b>.
    Corretagem e emolumentos de um WIN giram perto de 5 pontos por operacao de ida e
    volta; a escala abaixo mostra o que cada nivel de custo faz com a expectativa.</p>
    <figure><div id="custos"></div>
      <figcaption>Valor esperado por trade no padrao Ouro, em pontos.</figcaption></figure>
  </div>

  <div class="bandeira">
    <h3>O que este backteste nao mediu</h3>
    <ul class="enx" style="margin-bottom:0">
      <li><b>Slippage.</b> As entradas saem no preco exato do fechamento do candle e as
      saidas no preco exato do stop ou do alvo. No stop, na pratica, escorrega.</li>
      <li><b>Caminho dentro do candle.</b> Como so existe OHLC, assume-se que o pavio
      contra o sentido do candle se forma antes &mdash; a convencao conservadora. Num
      candle que bate stop e alvo, isso decide qual vale.</li>
      <li><b>Outros regimes.</b> Agosto e setembro de 2026 no WINFUT foram um periodo
      de alta. O padrao e de continuacao de tendencia; e de esperar que ele sofra em
      mercado lateral, e a base nao tem lateral suficiente para medir isso.</li>
      <li><b>Um instrumento so, um contrato so.</b> Sem variacao de tamanho de posicao
      e sem outro ativo para confirmar.</li>
    </ul>
  </div>
</section>"""


def trades(D):
    def grupo(eixo, opcoes, atual):
        return ''.join(
            f'<button class="aba" type="button" data-k="{eixo}" data-v="{v}" '
            f'aria-pressed="{str(v == atual).lower()}">{r}</button>'
            for v, r in opcoes)

    esc = D['escolhida'].split('|')
    b_niv = grupo('nivel', [(k, D['rotulo'][k]) for k in ('ouro', 'prata', 'bronze')],
                  esc[2])
    b_modo = grupo('modo', [('fecha', 'No fechamento'),
                            ('antecipa', 'No meio do corpo (ordem stop)')], esc[0])
    b_ges = grupo('gestao', [(k, v['rot']) for k, v in D['gestoes'].items()], esc[1])

    return f"""
<section id="trades">
  <h2>Trade a trade</h2>
  <p class="olho">Cada operacao no grafico, com a Hull 50, a EMA 21 e o canal de
  Keltner. A faixa clara marca o par retracao + continuacao; a faixa colorida, o tempo
  em que a posicao ficou aberta. Os tres grupos de botoes trocam a carteira inteira
  &mdash; nao e um recorte da lista, e o backteste refeito com aquele filtro, uma
  posicao por vez. Setas do teclado tambem navegam.</p>
  <div id="kwrap">
    <div id="kfiltros">
      <div class="linha-f"><span class="rot-f">Padrao</span>
        <div class="abas">{b_niv}</div></div>
      <div class="linha-f"><span class="rot-f">Entrada</span>
        <div class="abas">{b_modo}</div></div>
      <div class="linha-f"><span class="rot-f">Gestao</span>
        <div class="abas">{b_ges}</div></div>
      <p class="kresumo" id="kresumo"></p>
    </div>
    <div class="knav">
      <button id="kant" type="button">&larr; anterior</button>
      <button id="kprox" type="button">proximo &rarr;</button>
      <button id="kganho" type="button">proximo ganho</button>
      <button id="kperda" type="button">proxima perda</button>
      <select id="ksel" aria-label="Escolher operacao"></select>
    </div>
    <div id="kchart"></div>
    <div class="kinfo" id="kinfo"></div>
  </div>
  <p class="nota">Na entrada <b>no meio do corpo</b> o nivel Ouro fica desligado, e
  nao por descuido: ele depende do pavio do candle de continuacao, que ainda nao
  terminou de se formar quando a ordem stop e colocada. Medir no lugar dele a
  geometria do candle da <i>retracao</i> &mdash; essa sim conhecida na hora &mdash;
  foi testado e nao substitui: as faixas nao ficam em ordem e o primeiro terco do
  periodo zera.</p>
</section>"""


def conclusao(D):
    s = D['variantes'][D['escolhida']]['stats']
    P = D['parametros']
    return f"""
<section id="conclusao">
  <h2>Conclusao</h2>
  <p class="olho">Ha um setup aqui. Ele nao e exatamente o que o CLAUDE.md descreve
  &mdash; um dos filtros pedidos mede ao contrario &mdash; mas o esqueleto da ideia,
  retracao mais candle de continuacao com a Hull atras do preco, mede positivo antes
  de qualquer ajuste, e isso e o mais importante deste relatorio.</p>

  <div class="grade g2">
    <div class="card">
      <h3>O setup, em uma frase</h3>
      <p>Compra quando a Hull 50 esta subindo e atras do preco, depois de uma retracao
      de <b>dois ou mais</b> candles cujos topos ficaram acima da Hull, com a EMA 21
      cortando o par, no fechamento do candle de continuacao &mdash; desde que o preco
      <b>nao</b> esteja esticado da EMA com a Hull acelerando, e que esse candle tenha
      pavio total entre {n(P['pavio_min'])} e {n(P['pavio_max'])} pontos. Stop
      {n(P['stop'])}, parcial de 50% em +{n(P['parcial_em'])}, alvo {n(P['alvo'])}.
      Venda e o espelho.</p>
      <p style="margin-bottom:0">Isso deu <b>{sn(s['exp_pts'], 1)} pontos por
      operacao</b> em {s['trades']} operacoes ao longo de {s['dias']} pregoes,
      {n(s['trades_dia'], 1)} operacoes por dia, com acerto de {n(s['winrate'], 1)}% e
      rebaixamento maximo de {n(s['dd_max'])} pontos.</p>
    </div>
    <div class="card">
      <h3>O que fazer com isso</h3>
      <ul class="enx" style="margin-bottom:0">
        <li>O plano operacional esta em <b>plano.html</b>, com os gatilhos na ordem em
        que se olha para eles na tela.</li>
        <li>Rodar em simulador por <b>pelo menos um mes</b> antes de qualquer dinheiro
        real. A base testada nao chega a um trimestre.</li>
        <li>Refazer esta medicao com uma base maior assim que houver &mdash; o roteiro
        inteiro roda com <code>python rodar.py &amp;&amp; python relatorio.py</code>.</li>
        <li>Se for operar, operar o <b>Ouro</b>. O Bronze faz quatro vezes mais trades
        para ganhar o mesmo, com o dobro do rebaixamento e muito mais custo.</li>
      </ul>
    </div>
  </div>
</section>

<footer>
  <p>Backteste gerado a partir de <code>WINFUT/WINFUT_20PI.csv</code>
  ({n(D['auditoria']['candles'])} candles, {D['auditoria']['dias']} pregoes).
  Resultados em pontos do WINFUT, brutos, com um contrato.
  Rodar de novo: <code>python rodar.py &amp;&amp; python relatorio.py</code>.</p>
  <p>Backteste nao e promessa. Resultado passado, ainda por cima medido em
  {D['auditoria']['dias']} pregoes, nao garante resultado nenhum.</p>
</footer>"""


SECOES = [
    ('resumo', 'Resumo'), ('base', 'A base'), ('padrao', 'O padrao'),
    ('galeria', 'Galeria'), ('estatisticas', 'Estatisticas'),
    ('patrimonio', 'Patrimonio'),
    ('distribuicao', 'Distribuicao'), ('duracao', 'Duracao'),
    ('filtros', 'Filtros'), ('gestao', 'Stop e alvo'),
    ('rr', 'Risco : retorno'), ('fluxo', 'Agressao e tendencia'),
    ('robustez', 'Robustez'), ('trades', 'Trade a trade'),
    ('conclusao', 'Conclusao'),
]


def monta(D):
    corpo = (capa(D) + resumo(D) + base_dados(D) + padrao(D) + galeria(D)
             + estatisticas(D) + patrimonio(D) + distribuicao(D) + filtros(D)
             + gestao(D) + risco_retorno(D) + fluxo_sec(D)
             + robustez(D) + trades(D)
             + conclusao(D))
    menu = ''.join(f'<li><a href="#{i}">{r}</a></li>' for i, r in SECOES)
    pag = (molde.HTML
           .replace('{{titulo}}', 'Momentum no grafico PI &middot; backtest WINFUT')
           .replace('{{menu}}', menu)
           .replace('{{corpo}}', corpo)
           .replace('__CSS__', molde.CSS)
           .replace('__KIT__', molde.JS_KIT)
           .replace('__PAG__', molde.JS_PAG)
           .replace('__KAPP__', molde.JS_KLINE_APP)
           .replace('__KLINE__', open(VENDOR_KC, encoding='utf-8').read())
           .replace('__DADOS__', json.dumps(D, ensure_ascii=False, separators=(',', ':'))))
    return pag


def main():
    with open(os.path.join(SAIDA, 'resumo.json'), encoding='utf-8') as f:
        D = json.load(f)
    pag = monta(D)
    destino = os.path.join(BASE, 'relatorio.html')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write(pag)
    print(f'[OK] relatorio.html  ({os.path.getsize(destino) / 1e6:.1f} MB)')

    import resultados_md
    resultados_md.escreve(D, os.path.join(BASE, 'RESULTADOS.md'))
    print('[OK] RESULTADOS.md')


if __name__ == '__main__':
    main()
