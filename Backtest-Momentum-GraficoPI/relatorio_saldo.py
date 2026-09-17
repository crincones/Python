# -*- coding: utf-8 -*-
"""
Monta saldo_agressor.html e SALDO_AGRESSOR.md a partir de
saida/saldo_agressor.json.

    python saldo_agressor.py && python relatorio_saldo.py

Mesmo esqueleto de relatorio_volume.py; no trade a trade, o saldo de agressao
por candle (barra) e a media do saldo em modulo (linha).
"""
import json
import os

import molde
import relatorio_osciladores as RO
import relatorio_volume as RV
from relatorio_pavio import n, sn, cls, tile, md_n, md_sn, GESTOES_JS

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
GES = RO.GES


def fatos(D):
    F = RV.fatos(D)
    R = D['regras_res']
    F['frac_des_pos'] = None
    F['dg'] = lambda k: [R[f'cand|{g}|{k}']['ganho'] for g in GES]
    F['lado'] = lambda k: (R[f'cand|parcial|{k}']['compra'] - R[f'cand|parcial|{k}']['compra_base'],
                           R[f'cand|parcial|{k}']['venda'] - R[f'cand|parcial|{k}']['venda_base'])
    return F


def capa(D, F):
    B = D['base']; P = D['parametros']
    return f"""
<header class="capa">
  <div class="chapeu">Backtest &middot; WINFUT &middot; grafico de 20 PI</div>
  <h1>Saldo de agressao<br>como filtro do Hull + pavios</h1>
  <p class="sub">Agressao compradora menos vendedora, no sentido do trade: o saldo do candle de sinal, com lag de 1 e
  2 barras, somado nas ultimas barras, em variacao percentual e contra a media dos ultimos candles.</p>
  <div style="margin-top:18px">
    <span class="selo">{n(B['barras'])} candles</span>
    <span class="selo">{B['dias']} pregoes, {B['ini']} a {B['fim']}</span>
    <span class="selo">{len(D['feats'])} leituras</span>
    <span class="selo">{len(D['feats']) * len(P['cortes']) * 2} filtros candidatos</span>
    <span class="selo">normalizado pela media |saldo| de {P['jan_ref']} barras</span>
  </div>
</header>"""


def resposta(D, F):
    R = F['R']; bc = F['busca']['cand|parcial']; bh = F['busca']['h|parcial']
    L = D['limites']; O_ = D['ortogonalidade']['valores']
    fo = bc['fora']; foh = F['busca']['cand|puro']['fora']
    base = R['cand|parcial|R_s_lag0']['base']
    sm = [R[f'cand|parcial|R_smed_{k}'] for k in (2, 3, 5)]
    de = R['cand|parcial|R_des_0']; dl = F['lado']('R_des_0')
    hull_max = max(max(abs(O_[f'cand|{f}'][r]) for r in ('incl_hull', 'sep_hull', 'macd_atr')) for f in D['feats'])
    tempo_max = max(max(abs(O_[f'cand|{f}'][r]) for r in ('hora', 'dur_sinal', 'ritmo_r')) for f in D['feats'])
    lim = lambda f, q: L[f][str(q)]
    esc = [x for b in F['busca'].values() for x in b['fora'].values() if x]
    piora = sum(1 for x in esc if x['ev_teste'] < x['ev_teste_base'])
    viz = D['vizinhanca']
    troca_k = [k for k in (2, 3, 5)
               if (viz[f'R_smed_{k}|media 20']['ganho'] > 0) != (viz[f'R_smed_{k}|media 50']['ganho'] > 0)]
    titulo = 'Resposta curta: nao' if not F['passou'] else 'Resposta curta: um filtro passou no controle'
    return f"""
<section id="resposta">
  <h2>{titulo}</h2>
  <p class="olho">Nenhuma das {len(D['feats'])} leituras do saldo de agressao filtra o Hull + pavios. O melhor dos
  {len(D['feats']) * 6} filtros &mdash; {bc['regra']} &mdash; ganha {sn(bc['ganho'], 1)} pts por sinal, e a mesma busca com
  os resultados embaralhados acha algo tao bom em {n(bc['p_valor'] * 100, 0)}% das vezes: o achado real fica
  <i>abaixo</i> do que o acaso produz tipicamente.</p>
  <div class="grade g4">
    {tile('Hull + pavios, sem filtro', sn(base, 1), f"pts por sinal &middot; {n(D['base']['n_cand'])} sinais", cls(base))}
    {tile('Melhor filtro da busca', sn(bc['ganho'], 1), f"pts de ganho &middot; {n(bc['n'])} sinais")}
    {tile('Busca contra ruido', 'p = ' + n(bc['p_valor'], 2), f"Hull + 2 a 4: p = {n(bh['p_valor'], 2)}")}
    {tile('Menor ganho detectavel', sn(bc['poder'][0]['min_ganho'], 1), 'pts, filtro que mantem metade')}
  </div>
  <div class="bandeira">
    <h3>O que o estudo encontrou</h3>
    <ul class="enx">
      <li><b>No PI, o saldo do par ja vem com o sinal escrito.</b> O candle de sinal fecha 100 pontos a favor, e o
      desequilibrio dele e a favor em quase todos os sinais (o quintil de baixo comeca em
      {sn(lim('des_0', 20), 2)}). O ultimo candle da retracao fecha 100 contra, e o saldo dele e contra em quase todos
      (o quintil de cima termina em {sn(lim('s_lag1', 80), 2)}). Por isso a variacao percentual contra 1 barra atras e
      sempre maior que +100% (quintil de baixo: {sn(lim('spct_1', 20) * 100, 0)}%): o saldo troca de sinal por
      construcao. &ldquo;Saldo a favor no candle que retoma&rdquo; nao e filtro, e a definicao do candle.</li>
      <li><b>O que sobra de variacao nao separa.</b> A grade nao tem faixa: cortes vizinhos e lags vizinhos trocam de
      sinal. Escolhido so com os meses antes de 06/08, o filtro ({fo['antes -> original+depois']['regra']}) mede
      {sn(fo['antes -> original+depois']['ev_teste'], 1)} no resto contra {sn(fo['antes -> original+depois']['ev_teste_base'], 1)}
      sem filtro; no 1:3 sem parcial, o escolhido ({foh['antes -> original+depois']['regra']}) mede
      {sn(foh['antes -> original+depois']['ev_teste'], 1)} contra {sn(foh['antes -> original+depois']['ev_teste_base'], 1)}.
      Em {piora} das {len(esc)} escolhas feitas fora do periodo de teste (dois conjuntos, quatro gestoes, dois
      recortes), o filtro escolhido mede pior que nao filtrar.</li>
      <li><b>Desequilibrio forte a favor no sinal mede pior</b> ({sn(de['ganho'], 1)} pts acima da mediana, negativo nas
      quatro gestoes e nos dois lados: compra {sn(dl[0], 1)}, venda {sn(dl[1], 1)}) &mdash; o mesmo desenho da
      &ldquo;retomada com volume&rdquo; do estudo de volume. Mas nao se sustenta nos tercos
      ({' / '.join(sn(v, 0) for v in de['tercos'])} contra {' / '.join(sn(v, 0) for v in de['tercos_base'])}) e p =
      {n(de['p_bi'], 2)} isolado.</li>
      <li><b>Saldo do sinal acima da media da retracao</b> (smed_k) aponta para o outro lado, pouco:
      {', '.join(sn(r['ganho'], 1) for r in sm)} pts com k = 2, 3 e 5. Com k = {' e '.join(str(k) for k in troca_k) or '-'}, troca de
      sinal ao normalizar por 50 barras em vez de 20, e nao se repete nos tercos.</li>
      <li><b>Ortogonal a Hull, nao ao tempo.</b> Correlacao ate {n(hull_max, 2)} com a Hull, mas ate {n(tempo_max, 2)} com a
      hora, a duracao do candle de sinal ou o ritmo: o saldo relativo e maior em candle demorado e em mercado lento.</li>
    </ul>
  </div>
  <p class="nota">Nao ha plano novo. Com isto, o fluxo de agressao &mdash; volume e saldo, em nivel, lag, janela e
  variacao &mdash; esta medido nos sinais do Hull, e nao acrescenta nada.</p>
</section>"""


def metodo(D, F):
    V = D['ortogonalidade']['valores']; refs = D['ortogonalidade']['refs']; L = D['limites']
    lin = ''.join(
        f"<tr><td><b>{f}</b></td><td style='text-align:left'>{rot}</td>"
        f"<td>{' / '.join(n(L[f][str(q)], 2) for q in D['parametros']['cortes'])}</td>"
        + ''.join(f"<td class='{'neg' if abs(V[f'cand|{f}'][r]) > 0.3 else ''}'>{sn(V[f'cand|{f}'][r], 2)}</td>" for r in refs)
        + '</tr>' for f, rot in D['feats'].items())
    return f"""
<section id="metodo">
  <h2>Como foi medido</h2>
  <div class="grade g2">
    <div class="card">
      <h3>As leituras</h3>
      <p><b>S</b> = agressao compradora &minus; vendedora do candle, <b>espelhada pelo lado do trade</b>: positivo =
      agressao a favor da operacao. Nivel dividido pela media de |S| nas {D['parametros']['jan_ref']} barras anteriores.</p>
      <ul class="enx" style="margin-bottom:0">
        <li><b>s_lag0, s_lag1, s_lag2</b>: saldo do candle de sinal, de 1 e de 2 barras antes.</li>
        <li><b>des_0</b>: desequilibrio do sinal, S / (compra + venda), sem escala.</li>
        <li><b>sk_2, sk_3, sk_5</b>: saldo somado das ultimas k barras.</li>
        <li><b>spct_1, spct_2</b>: variacao percentual com lag, (S[i] &minus; S[i&minus;k]) / |S[i&minus;k]|.</li>
        <li><b>smed_2, smed_3, smed_5</b>: saldo do sinal menos a media das k barras anteriores.</li>
      </ul>
    </div>
    <div class="card">
      <h3>Os filtros e os controles</h3>
      <p>Cada leitura cortada no quintil de baixo, na mediana e no quintil de cima, nos dois sentidos:
      {len(D['feats']) * 6} filtros. Limites tirados da distribuicao, sem olhar resultado. Sinais de <code>hull_contra</code>:
      Hull + 2 a 4 ({n(D['base']['n_h'])}) e Hull + pavios ({n(D['base']['n_cand'])}).</p>
      <p style="margin-bottom:0">Busca contra 1.000 embaralhamentos dos resultados; escolha fora (antes de 06/08 &rarr;
      resto; T1+T2 &rarr; T3); as 12 leituras &ldquo;acima da mediana&rdquo; com permutacao, tercos, lados, blocos e
      sorteio; as mesmas so das 10h as 15h; e a normalizacao com 50 barras.</p>
    </div>
  </div>
  <div class="card rolo" style="margin-top:16px">
    <h3>Limites e correlacao de posto (Hull + pavios)</h3>
    <table><thead><tr><th></th><th>Leitura</th><th>q20 / mediana / q80</th>
      {''.join(f'<th>{r}</th>' for r in refs.values())}</tr></thead><tbody>{lin}</tbody></table>
    <p class="nota">Em vermelho, acima de 0,3 em modulo. Repare nos limites: des_0 quase todo positivo, s_lag1 todo
    negativo, spct todo acima de +1 &mdash; o formato do candle de PI.</p>
  </div>
</section>"""


def conclusao(D, F):
    bc = F['busca']['cand|parcial']
    return f"""
<section id="conclusao">
  <h2>Conclusao</h2>
  <ul class="enx">
    <li><b>O saldo de agressao nao filtra o Hull + pavios</b> em nenhuma das formas pedidas &mdash; nivel, lag de 1 e
    2 barras, soma, variacao percentual ou contra a media: melhor t = {sn(bc['t'], 2)}, ruido
    {sn(bc['ruido_mediana'], 2)} na mediana, p = {n(bc['p_valor'], 2)}.</li>
    <li><b>O sinal do saldo no par retracao + continuacao e imposto pelo proprio candle de PI</b>, e o que varia alem
    disso nao carrega informacao sobre o trade.</li>
    <li><b>Escolher o filtro olhando o passado piora o resultado</b> no periodo seguinte.</li>
    <li><b>Fluxo, no Hull, esta encerrado:</b> volume agressor e saldo, em todas as formas, nao acrescentam nada. O
    unico candidato vivo para o simulador continua sendo o horario (nao operar antes das 10h).</li>
  </ul>
  <p class="nota">Resultado bruto, um instrumento. Agressao do log do robo; sem volume total nem numero de negocios.</p>
</section>
<footer>Gerado por <code>saldo_agressor.py</code> (via <code>volume_agressor.py</code>) e <code>relatorio_saldo.py</code>.</footer>"""


def js():
    J = RV.js()

    def troca(a, b):
        nonlocal J
        assert a in J, a[:60]
        J = J.replace(a, b)
    i = J.index("klinecharts.registerIndicator({name:'OS_VOL'")
    j = J.index("let kchart=null")
    J = J[:i] + r"""klinecharts.registerIndicator({name:'OS_SALDO',shortName:'Saldo de agressao (compra - venda) / media |saldo| 20',precision:0,
  figures:[{key:'ref',title:'+media |saldo|: ',type:'line'},{key:'refn',title:'-media |saldo|: ',type:'line'},
    {key:'saldo',title:'saldo: ',type:'bar',baseValue:0,
     styles:({data})=>{const c=data.current||{}; return {style:'fill',color:alfa(c.saldo>=0?c_('ganho'):c_('perda'),.6)};}}],
  calc:dl=>dl.map(k=>({saldo:k.saldo,ref:k.ref,refn:k.ref===null?null:-k.ref}))});

""" + J[j:]
    troca("""    hma:C.hma[i],vol:C.vol[i],ref:C.ref20[i]});""", """    hma:C.hma[i],saldo:C.saldo[i],ref:C.ref[i]});""")
    troca("""  kchart.createIndicator('OS_VOL',false,{id:'p_vol',height:140});""",
          """  kchart.createIndicator('OS_SALDO',false,{id:'p_saldo',height:150});""")
    troca("""    `<span>volume do sinal ${fmt(C.vol[ti],0)} &middot; media 20 ${fmt(C.ref20[ti],0)} (${fmt(C.vol[ti]/C.ref20[ti],2)}x)</span>`+""",
          """    `<span>saldo do sinal ${sinal(C.saldo[ti]*ld,0)} a favor &middot; barra anterior ${sinal(C.saldo[ti-1]*ld,0)} &middot; media |saldo| ${fmt(C.ref[ti],0)}</span>`+""")
    troca("let qM='vmed_3', qC='cand';", "let qM='smed_3', qC='cand';")
    return J


HTML = RO.HTML.replace('<title>Osciladores no Hull</title>', '<title>Saldo Agressao Hull</title>')


def md_corpo(D, F):
    R = F['R']; g = F['g']; CR = RV.CORTES_ROT
    L = ['## 1. Grade de ganho (pts por sinal), Hull + pavios', '']
    for gst in GES:
        L += [f"**{D['rot_gestao'][gst]}**", '', '| Leitura | ' + ' | '.join(c[2] for c in CR) + ' |', '|:--|' + '--:|' * len(CR)]
        for f in D['feats']:
            L.append(f"| {f} | " + ' | '.join(md_sn(g(f, q, s_, 'cand', gst).get('ganho'), 1) for q, s_, _ in CR) + ' |')
        L.append('')
    L += ['## 2. Acima da mediana (Hull + pavios, 1:3 com parcial)', '',
          '| Leitura | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 | Antes (sem filtro) | Compra | Venda | Pct | So 10h-15h |',
          '|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|--:|']
    for k in D['regras']:
        r = R[f'cand|parcial|{k}']; h = D['horario'][f'cand|{k}']
        L.append(f"| {k[2:]} | {r['n']} | {md_sn(r['ev'], 1)} | {md_sn(r['ev_fora'], 1)} | **{md_sn(r['ganho'], 1)}** | "
                 f"{md_n(r['p_bi'], 3)} | " + ' / '.join(md_sn(x, 0) for x in r['tercos'])
                 + f" | {md_sn(r['blocos']['antes'], 1)} ({md_sn(r['blocos_base']['antes'], 1)}) | "
                 f"{md_sn(r['compra'], 1)} | {md_sn(r['venda'], 1)} | {md_n(r['sorteio_pct'])} | {md_sn(h['ganho_10_15'], 1)} |")
    L += ['', '## 3. Quintis (Hull + pavios, 1:3 com parcial)', '', '| Leitura | Limites | Q1 | Q2 | Q3 | Q4 | Q5 |',
          '|:--|:--|--:|--:|--:|--:|--:|']
    for f in D['feats']:
        q = D['quintis'][f'cand|{f}']
        L.append(f"| {f} | " + ' / '.join(md_n(x, 2) for x in q['limites']) + ' | ' + ' | '.join(md_sn(z['ev'], 1) for z in q['faixas']) + ' |')
    L += ['', '## 4. Busca contra ruido e escolha fora', '',
          '| Conjunto | Gestao | Melhor | Ganho | t | ruido med | ruido p95 | p | Escolhida antes, medida depois | Escolhida T1+T2, medida T3 |',
          '|:--|:--|:--|--:|--:|--:|--:|--:|:--|:--|']
    for cj in ('cand', 'h'):
        for gst in GES:
            b = D['busca'][f'{cj}|{gst}']
            cel = []
            for rot in ('antes -> original+depois', 'T1+T2 -> T3'):
                x = b['fora'].get(rot)
                cel.append('-' if not x else f"{x['regra']}: {md_sn(x['ev_teste'], 1)} (sem filtro {md_sn(x['ev_teste_base'], 1)}, n={x['n_teste']})")
            L.append(f"| {cj} | {D['rot_gestao'][gst]} | {b['regra']} | {md_sn(b['ganho'], 1)} | {md_sn(b['t'], 2)} | "
                     f"{md_sn(b['ruido_mediana'], 2)} | {md_sn(b['ruido_p95'], 2)} | {md_n(b['p_valor'], 2)} | {cel[0]} | {cel[1]} |")
    refs = D['ortogonalidade']['refs']
    L += ['', '## 5. Ortogonalidade (correlacao de posto, Hull + pavios)', '',
          '| Leitura | ' + ' | '.join(refs.values()) + ' |', '|:--|' + '--:|' * len(refs)]
    for f in D['feats']:
        o = D['ortogonalidade']['valores'][f'cand|{f}']
        L.append(f"| {f} | " + ' | '.join(md_sn(o[r], 2) for r in refs) + ' |')
    L += ['', '## 6. Carteira (Hull + pavios)', '',
          '| Gestao | Leitura acima da mediana | Trades | Pts | Pts/trade | Acerto | Fator | Rebaix. |', '|:--|:--|--:|--:|--:|--:|--:|--:|']
    for gst in GES:
        for k in ['base'] + list(D['regras']):
            st = D['carteira'][f'cand|{gst}|{k}']
            L.append(f"| {D['rot_gestao'][gst]} | {'sem filtro' if k == 'base' else k[2:]} | {md_n(st['trades'])} | {md_sn(st['lucro_liq'])} | "
                     f"{md_sn(st['exp_pts'], 1)} | {md_n(st['winrate'], 1)}% | {md_n(st['fator_lucro'], 2)} | {md_n(st['dd_max'])} |")
    L.append('')
    return '\n'.join(L)


def markdown(D, F):
    B = D['base']; R = F['R']; bc = F['busca']['cand|parcial']; L = D['limites']
    topo = '\n'.join([
        '# Saldo de agressao como filtro do Hull + pavios', '',
        f"WINFUT, grafico de 20 PI, {n(B['barras'])} candles, {B['dias']} pregoes ({B['ini']} a {B['fim']}). Resultado bruto. "
        'Grade interativa, curvas, MEP/MEN, duracao e trade a trade em saldo_agressor.html.', '',
        '**S = agressao compradora - vendedora, espelhada pelo lado do trade** (positivo = a favor). Leituras: s_lag0/1/2 '
        f"(saldo do sinal e de 1 e 2 barras antes, / media |S| de {D['parametros']['jan_ref']} barras), des_0 (S / volume "
        'agressor), sk_2/3/5 (soma das ultimas k barras), spct_1/2 ((S[i]-S[i-k]) / |S[i-k]|), smed_2/3/5 (S do sinal menos a '
        f"media das k anteriores). Cortes q20 / mediana / q80, nos dois sentidos: {len(D['feats']) * 6} filtros.", '',
        '## Resposta curta: ' + ('nao' if not F['passou'] else 'um filtro passou no controle'), '',
        f"- Melhor da busca: **{bc['regra']}**, ganho {md_sn(bc['ganho'], 1)} pts; busca contra ruido p = {md_n(bc['p_valor'], 2)} "
        '-- abaixo do acaso tipico.',
        f"- **O PI impoe o sinal do saldo**: desequilibrio do sinal com quintil de baixo em {md_sn(L['des_0']['20'], 2)}, saldo "
        f"do ultimo candle da retracao com quintil de cima em {md_sn(L['s_lag1']['80'], 2)}, variacao % contra 1 barra sempre "
        f"acima de +{md_n(L['spct_1']['20'] * 100)}%.",
        f"- Desequilibrio forte a favor no sinal mede pior ({md_sn(R['cand|parcial|R_des_0']['ganho'], 1)}), nas 4 gestoes e "
        'nos dois lados, mas sem tercos estaveis.',
        '- Escolhido antes de 06/08, o filtro nao ajuda ou piora o periodo seguinte.', '', ''])
    fim = '\n'.join([
        '## Conclusao', '',
        '- **O saldo de agressao nao filtra o Hull + pavios** em nenhuma das formas pedidas.',
        '- **O sinal do saldo no par retracao + continuacao e imposto pelo candle de PI**; o resto nao carrega informacao.',
        '- **Fluxo, no Hull, esta encerrado**: volume e saldo nao acrescentam. Candidato vivo: horario (nao operar antes das 10h).',
        '', '> Resultado bruto, um instrumento. Agressao do log do robo.', '',
        'Reproduzir: python saldo_agressor.py && python relatorio_saldo.py', ''])
    return topo + md_corpo(D, F) + fim


def main():
    with open(os.path.join(SAIDA, 'saldo_agressor.json'), encoding='utf-8') as f:
        D = json.load(f)
    F = fatos(D)
    md = markdown(D, F)
    D = RO.enxuga(D)
    D['gestoes'] = GESTOES_JS
    for b in D['busca'].values():
        b['sent_orig'] = b['sentido']; b['sentido'] = 1
        for x in b['fora'].values():
            if x:
                x['sentido'] = 1
    corpo = ''.join([capa(D, F), resposta(D, F), metodo(D, F), RV.grade_sec(D, F), RO.regras_sec(D, F),
                     RV.horario_sec(D, F), RO.quintis_sec(D, F), RO.busca_sec(D, F), RO.carteira_sec(D, F), conclusao(D, F)])
    corpo = (corpo.replace('<h2>1. Cada regra, medida</h2>', '<h2>2. Cada leitura acima da mediana</h2>')
             .replace('<h2>2. As leituras em faixas</h2>', '<h2>4. As leituras em faixas</h2>')
             .replace('<h2>3. A busca contra o ruido, e a escolha fora</h2>', '<h2>5. A busca contra o ruido, e a escolha fora</h2>')
             .replace('<h2>5. A carteira, uma posicao por vez</h2>', '<h2>6. A carteira, uma posicao por vez</h2>')
             .replace('<h2>6. Trade a trade</h2>', '<h2>7. Trade a trade</h2>')
             .replace('foi repetida 500 vezes', 'foi repetida 1.000 vezes')
             .replace('Uma regra que valesse passaria do p95 do ruido; nenhuma passa da mediana com folga.',
                      'Uma regra que valesse passaria do p95 do ruido.')
             .replace('&ldquo;(nao)&rdquo; = o complemento da regra. ', 'O nome do filtro ja diz o sentido do corte. ')
             .replace('parecido entre lags vizinhos (1, 2, 3, 5)', 'parecido entre lags e janelas vizinhos')
             .replace('A primeira hora concentra volume, mas os sinais de volume alto\n      nao estao mais concentrados nela que os de volume baixo.',
                      'Os sinais de saldo alto estao um pouco menos concentrados na primeira hora, e medir so das 10h as 15h\n      nao cria ordem nenhuma.')
             .replace('<h3>Media de referencia: 20 x 50 barras</h3>', '<h3>Normalizacao: media |saldo| de 20 x 50 barras</h3>')
             .replace('Hull 50 no preco; MACD, estocastico lento e IFR embaixo.',
                      'Hull 50 no preco; saldo de agressao por candle (verde a comprador, vermelho a vendedor) e a media do saldo em modulo embaixo.'))
    with open(RO.VENDOR_KC, encoding='utf-8') as f:
        kline = f.read()
    MENU = [(a, r if a != 'regras' else 'Acima da mediana') for a, r in RV.MENU]
    scripts = ('<script>' + kline + '</script>\n<script>const D=' +
               json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';</script>\n'
               '<script>' + molde.JS_KIT + '</script>\n<script>' + js() + '</script>')
    html = (HTML.replace('__CSS__', molde.CSS)
            .replace('__MENU__', ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU))
            .replace('__SCRIPTS__', scripts).replace('__CORPO__', corpo))
    with open(os.path.join(BASE, 'saldo_agressor.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(BASE, 'SALDO_AGRESSOR.md'), 'w', encoding='utf-8') as f:
        f.write(md)
    print(f'gravado: saldo_agressor.html ({len(html) / 1e6:.1f} MB) e SALDO_AGRESSOR.md')


if __name__ == '__main__':
    main()
