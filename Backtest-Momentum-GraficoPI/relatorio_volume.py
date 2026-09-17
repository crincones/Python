# -*- coding: utf-8 -*-
"""
Monta volume_agressor.html e VOLUME_AGRESSOR.md a partir de
saida/volume_agressor.json.

    python volume_agressor.py && python relatorio_volume.py

Mesmo esqueleto de relatorio_osciladores.py, mais a grade leitura x corte e,
no trade a trade, o volume agressor por candle com a media de 20 barras.
"""
import json
import os

import molde
import relatorio_osciladores as RO
from relatorio_pavio import n, sn, cls, tile, md_n, md_sn, GESTOES_JS

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
GES = RO.GES
CORTES_ROT = [('20', 1, '> q20'), ('20', -1, '<= q20'), ('50', 1, '> mediana'), ('50', -1, '<= mediana'),
              ('80', 1, '> q80'), ('80', -1, '<= q80')]


def fatos(D):
    R = D['regras_res']
    F = dict(R=R, busca=D['busca'])
    F['passou'] = [k for k, b in D['busca'].items() if b['p_valor'] <= 0.05]
    G = D['grade']
    F['g'] = lambda f, q, s, cj='cand', g='parcial': G.get(f'{cj}|{g}|C_{f}_q{q}|{s}', {})
    return F


def capa(D, F):
    B = D['base']; P = D['parametros']
    return f"""
<header class="capa">
  <div class="chapeu">Backtest &middot; WINFUT &middot; grafico de 20 PI</div>
  <h1>Volume agressor<br>como filtro do Hull + pavios</h1>
  <p class="sub">Agressao compradora + vendedora de cada candle, em nivel, com lags de 1, 2, 3 e 5 barras, em
  variacao percentual e contra a media das ultimas barras.</p>
  <div style="margin-top:18px">
    <span class="selo">{n(B['barras'])} candles</span>
    <span class="selo">{B['dias']} pregoes, {B['ini']} a {B['fim']}</span>
    <span class="selo">{len(D['feats'])} leituras</span>
    <span class="selo">{len(D['feats']) * len(P['cortes']) * 2} filtros candidatos</span>
    <span class="selo">media de referencia de {P['jan_ref']} barras</span>
  </div>
</header>"""


def resposta(D, F):
    R = F['R']; bc = F['busca']['cand|parcial']; bh = F['busca']['h|parcial']
    g = F['g']
    O_ = D['ortogonalidade']['valores']
    dur_max = max(O_[f'cand|{f}']['dur_sinal'] for f in D['feats'])
    hull_max = max(max(abs(O_[f'cand|{f}'][r]) for r in ('incl_hull', 'sep_hull', 'macd_atr')) for f in D['feats'])
    vm = [R[f'cand|parcial|R_vmed_{k}'] for k in (2, 3, 5)]
    fo = bc['fora']
    v2 = [g(f'vpct_{k}', 20, -1).get('ganho') for k in (1, 2, 3, 5)]
    dc = [R[f'cand|{gs}|R_vmed_{k}']['compra'] - R[f'cand|{gs}|R_vmed_{k}']['compra_base'] for k in (2, 3, 5) for gs in GES]
    dv = [R[f'cand|{gs}|R_vmed_{k}']['venda'] - R[f'cand|{gs}|R_vmed_{k}']['venda_base'] for k in (2, 3, 5) for gs in GES]
    titulo = 'Resposta curta: nao' if not F['passou'] else 'Resposta curta: um filtro passou no controle'
    return f"""
<section id="resposta">
  <h2>{titulo}</h2>
  <p class="olho">Nenhuma das {len(D['feats'])} leituras de volume agressor separa os sinais do Hull + pavios de um jeito
  que resista ao controle. O melhor dos {len(D['feats']) * 6} filtros &mdash; {bc['regra']} &mdash; leva de
  {sn(R['cand|parcial|R_vrel_1']['base'], 1)} a {sn(R['cand|parcial|R_vrel_1']['base'] + bc['ganho'], 1)} pts por sinal,
  e a mesma busca com os resultados embaralhados acha algo tao bom em {n(bc['p_valor'] * 100, 0)}% das vezes.</p>
  <div class="grade g4">
    {tile('Hull + pavios, sem filtro', sn(R['cand|parcial|R_vrel_1']['base'], 1), f"pts por sinal &middot; {n(D['base']['n_cand'])} sinais", cls(R['cand|parcial|R_vrel_1']['base']))}
    {tile('Melhor filtro da busca', sn(bc['ganho'], 1), f"pts de ganho &middot; {n(bc['n'])} sinais")}
    {tile('Busca contra ruido', 'p = ' + n(bc['p_valor'], 2), f"Hull + 2 a 4: p = {n(bh['p_valor'], 2)}")}
    {tile('Menor ganho detectavel', sn(bc['poder'][0]['min_ganho'], 1), 'pts, filtro que mantem metade')}
  </div>
  <div class="bandeira">
    <h3>O que o estudo encontrou</h3>
    <ul class="enx">
      <li><b>A grade tem cara de ruido.</b> O melhor filtro e o volume do sinal no quintil mais baixo contra 2
      barras atras ({sn(v2[1], 1)} pts). Com lag de 1, 3 e 5 barras, o mesmo corte mede {sn(v2[0], 1)},
      {sn(v2[2], 1)} e {sn(v2[3], 1)}. Um efeito de volume nao some ao trocar 2 barras por 3; um acaso, sim.</li>
      <li><b>Escolha fora da amostra: uma a favor, uma neutra.</b> Escolhido so com os meses antes de 06/08, o
      filtro ({fo['antes -> original+depois']['regra']}) mede {sn(fo['antes -> original+depois']['ev_teste'], 1)} no resto,
      contra {sn(fo['antes -> original+depois']['ev_teste_base'], 1)} sem filtro &mdash; em
      {n(fo['antes -> original+depois']['n_teste'])} sinais. Escolhido em T1+T2 ({fo['T1+T2 -> T3']['regra']}), mede
      {sn(fo['T1+T2 -> T3']['ev_teste'], 1)} em T3 contra {sn(fo['T1+T2 -> T3']['ev_teste_base'], 1)}.</li>
      <li><b>&ldquo;Retomada com volume&rdquo; mede ao contrario, e so na venda.</b> O candle de sinal com mais volume
      que a media das 2, 3 ou 5 barras anteriores mede {', '.join(sn(r['ganho'], 1) for r in vm)} pts. A direcao se
      repete nos tres k, mas conforme k e gestao o efeito vai de {sn(min(dc), 1)} a {sn(max(dc), 1)} na compra e de
      {sn(min(dv), 1)} a {sn(max(dv), 1)} na venda: lados que discordam nao fazem regra.</li>
      <li><b>O volume por candle e, em boa parte, tempo.</b> As leituras sao ortogonais a Hull (correlacao ate
      {n(hull_max, 2)}) e ao horario, mas tem correlacao de ate {n(dur_max, 2)} com a <i>duracao</i> do candle de sinal:
      num grafico de PI, candle que demora acumula volume. Duracao ja foi testada no estudo de fluxo e nao passou.</li>
      <li><b>O horario nao explica nem esconde nada aqui.</b> Medidas so das 10h as 15h, as regras mudam pouco e
      continuam sem ordem (secao 3).</li>
    </ul>
  </div>
  <p class="nota">Nao ha plano novo. Se o horario for levado ao plano do Hull, o volume nao acrescenta nada a ele.</p>
</section>"""


def metodo(D, F):
    V = D['ortogonalidade']['valores']; refs = D['ortogonalidade']['refs']
    L = D['limites']
    lin = ''
    for f, rot in D['feats'].items():
        o = V[f'cand|{f}']
        lin += (f"<tr><td><b>{f}</b></td><td style='text-align:left'>{rot}</td>"
                f"<td>{' / '.join(n(L[f][str(q)] if str(q) in L[f] else L[f][q], 2) for q in D['parametros']['cortes'])}</td>"
                + ''.join(f"<td class='{'neg' if abs(o[r]) > 0.3 else ''}'>{sn(o[r], 2)}</td>" for r in refs) + '</tr>')
    return f"""
<section id="metodo">
  <h2>Como foi medido</h2>
  <div class="grade g2">
    <div class="card">
      <h3>As leituras</h3>
      <p><b>V</b> = agressao compradora + vendedora do candle. Tudo lido no fechamento do candle de sinal.</p>
      <ul class="enx" style="margin-bottom:0">
        <li><b>vrel_k</b> (k = 1, 2, 3, 5): media de V nas ultimas k barras, incluindo a de sinal, sobre a media das
        {D['parametros']['jan_ref']} barras anteriores a janela.</li>
        <li><b>vpct_k</b> (k = 1, 2, 3, 5): variacao percentual com lag, V[i] / V[i&minus;k] &minus; 1.</li>
        <li><b>vmed_k</b> (k = 2, 3, 5): V do sinal contra a media das k barras anteriores &minus; 1 &mdash; com k de 2
        ou 3, quase sempre os proprios candles da retracao.</li>
      </ul>
    </div>
    <div class="card">
      <h3>Os filtros e os controles</h3>
      <p>Cada leitura cortada no quintil de baixo, na mediana e no quintil de cima (limites tirados da distribuicao,
      sem olhar resultado), nos dois sentidos: {len(D['feats']) * 6} filtros. Sinais de <code>hull_contra</code>: Hull +
      2 a 4 ({n(D['base']['n_h'])}) e Hull + pavios ({n(D['base']['n_cand'])}).</p>
      <p style="margin-bottom:0">Busca contra 1.000 embaralhamentos dos resultados; escolha fora (antes de 06/08 &rarr;
      resto; T1+T2 &rarr; T3); as 11 leituras &ldquo;acima da mediana&rdquo; com permutacao, tercos, lados, blocos e
      sorteio; as mesmas so das 10h as 15h; e a media de referencia com 50 barras.</p>
    </div>
  </div>
  <div class="card rolo" style="margin-top:16px">
    <h3>Limites e correlacao de posto com o que ja se sabe (Hull + pavios)</h3>
    <table><thead><tr><th></th><th>Leitura</th><th>q20 / mediana / q80</th>
      {''.join(f'<th>{r}</th>' for r in refs.values())}</tr></thead><tbody>{lin}</tbody></table>
    <p class="nota">Em vermelho, acima de 0,3 em modulo. Ortogonal a Hull e ao horario; nao ortogonal a duracao do
    candle de sinal.</p>
  </div>
</section>"""


def grade_sec(D, F):
    ab_c = ''.join(f'<button class="aba" data-v="{c}" aria-pressed="{str(c == "cand").lower()}">{r}</button>'
                   for c, r in (('cand', 'Hull + pavios'), ('h', 'Hull + 2 a 4')))
    ab_g = ''.join(f'<button class="aba" data-v="{g}" aria-pressed="{str(g == "parcial").lower()}">{D["rot_gestao"][g]}</button>'
                   for g in GES)
    return f"""
<section id="grade">
  <h2>1. A grade: cada leitura, cada corte</h2>
  <p class="olho">Ganho em pts por sinal sobre o conjunto sem filtro, entrada no fechamento. Um efeito de verdade
  apareceria como faixa: parecido entre lags vizinhos (1, 2, 3, 5) e com sinal trocado entre um corte e o seu
  complemento.</p>
  <div class="abas" id="abas_gc" style="margin-bottom:6px">{ab_c}</div>
  <div class="abas" id="abas_gg">{ab_g}</div>
  <div class="card"><figure><div id="g_grade"></div>
    <figcaption>passe o mouse para ver sinais, EV e tercos; o contorno marca o melhor da busca</figcaption></figure></div>
</section>"""


def horario_sec(D, F):
    H = D['horario']
    lin = ''.join(f"<tr><td style='text-align:left'>{D['feats'][k[2:]]}</td>"
                  f"<td class='{cls(H[f'cand|{k}']['ganho_todos'])}'>{sn(H[f'cand|{k}']['ganho_todos'], 1)}</td>"
                  f"<td class='{cls(H[f'cand|{k}']['ganho_10_15'])}'>{sn(H[f'cand|{k}']['ganho_10_15'], 1)}</td>"
                  f"<td>{n(H[f'cand|{k}']['frac_cedo_dentro'], 0)}% / {n(H[f'cand|{k}']['frac_cedo_fora'], 0)}%</td></tr>"
                  for k in D['regras'])
    viz = ''.join(f"<tr><td>{v['regra'][2:]}</td><td style='text-align:left'>{v['par']}{' *' if v['padrao'] else ''}</td>"
                  f"<td>{n(v['n'])}</td><td class='{cls(v['ganho'])}'>{sn(v['ganho'], 1)}</td></tr>"
                  for v in D['vizinhanca'].values())
    return f"""
<section id="horario">
  <h2>3. Controle de horario e vizinhanca</h2>
  <div class="grade g2">
    <div class="card rolo"><h3>Acima da mediana: todos os sinais x so 10h&ndash;15h</h3>
      <table><thead><tr><th>Leitura</th><th>Ganho, todos</th><th>Ganho, 10h&ndash;15h</th>
        <th>Antes das 10h<br><small>dentro / fora</small></th></tr></thead><tbody>{lin}</tbody></table>
      <p class="nota">Hull + pavios, 1:3 com parcial. A primeira hora concentra volume, mas os sinais de volume alto
      nao estao mais concentrados nela que os de volume baixo.</p></div>
    <div class="card rolo"><h3>Media de referencia: 20 x 50 barras</h3>
      <table><thead><tr><th>Leitura</th><th>Referencia</th><th>Sinais</th><th>Ganho</th></tr></thead><tbody>{viz}</tbody></table>
      <p class="nota">* = a declarada. Acima da mediana, Hull + pavios, 1:3 com parcial.</p></div>
  </div>
</section>"""


def conclusao(D, F):
    bc = F['busca']['cand|parcial']
    return f"""
<section id="conclusao">
  <h2>Conclusao</h2>
  <ul class="enx">
    <li><b>O volume agressor nao filtra o Hull + pavios</b> em nenhuma das formas pedidas &mdash; nivel, lag, variacao
    percentual ou contra a media: melhor t = {sn(bc['t'], 2)}, ruido {sn(bc['ruido_mediana'], 2)} na mediana, p =
    {n(bc['p_valor'], 2)}.</li>
    <li><b>Os melhores cortes nao conversam entre si</b>: o que funciona com lag de 2 barras falha com 1, 3 e 5.</li>
    <li><b>A leitura mais &ldquo;de livro&rdquo; &mdash; retomada com volume &mdash; mede ao contrario</b>, e so num lado.</li>
    <li><b>No grafico de PI o volume por candle carrega tempo.</b> Se for insistir em fluxo, o proximo passo nao e
    mais volume: e o <i>saldo</i> agressor (compra &minus; venda) na retracao, ou volume por minuto &mdash; e ja se sabe,
    do estudo de fluxo, que a expectativa e baixa.</li>
  </ul>
  <p class="nota">Resultado bruto, um instrumento. Volume agressor do log do robo; sem volume total nem numero de
  negocios.</p>
</section>
<footer>Gerado por <code>volume_agressor.py</code> e <code>relatorio_volume.py</code>.</footer>"""


def js():
    J = RO.JS

    def troca(a, b):
        nonlocal J
        assert a in J, a[:60]
        J = J.replace(a, b)
    i = J.index("klinecharts.registerIndicator({name:'OS_HULL'")
    j = J.index("let kchart=null")
    J = J[:i] + r"""klinecharts.registerIndicator({name:'OS_HULL',shortName:'Hull 50',series:'price',precision:0,
  figures:[{key:'hma',title:'Hull 50: ',type:'line'}],calc:dl=>dl.map(k=>({hma:k.hma}))});
klinecharts.registerIndicator({name:'OS_VOL',shortName:'Volume agressor (compra + venda) / media 20',precision:0,minValue:0,
  figures:[{key:'ref',title:'media 20: ',type:'line'},
    {key:'vol',title:'volume: ',type:'bar',baseValue:0,
     styles:({data})=>{const c=data.current||{}; return {style:'fill',color:alfa(c.vol>=c.ref?c_('prata'):c_('mudo'),.6)};}}],
  calc:dl=>dl.map(k=>({vol:k.vol,ref:k.ref}))});

""" + J[j:]
    troca("""    hma:C.hma[i],macd:C.macd[i],sinal:C.sinal[i],hist:C.hist[i],k:C.k[i],d:C.d[i],ifr:C.ifr[i]});""",
          """    hma:C.hma[i],vol:C.vol[i],ref:C.ref20[i]});""")
    troca("""  kchart.createIndicator('OS_MACD',false,{id:'p_macd',height:110});
  kchart.createIndicator('OS_ESTOC',false,{id:'p_estoc',height:100});
  kchart.createIndicator('OS_IFR',false,{id:'p_ifr',height:100});""",
          """  kchart.createIndicator('OS_VOL',false,{id:'p_vol',height:140});""")
    troca("""    `<span>MACD ${fmt(C.macd[ti],0)} &middot; %K ${fmt(C.k[ti],0)} / %D ${fmt(C.d[ti],0)} &middot; IFR ${fmt(C.ifr[ti],0)}</span>`+""",
          """    `<span>volume do sinal ${fmt(C.vol[ti],0)} &middot; media 20 ${fmt(C.ref20[ti],0)} (${fmt(C.vol[ti]/C.ref20[ti],2)}x)</span>`+""")
    troca("let qM='ifr', qC='cand';", "let qM='vmed_3', qC='cand';")
    J += r"""
/* ------------------------------------------------ grade leitura x corte */
let gC='cand', gG='parcial';
grupoAbas('abas_gc',v=>{gC=v; desenhaGrade();});
grupoAbas('abas_gg',v=>{gG=v; desenhaGrade();});
const CORTES=[['20',1,'> q20'],['20',-1,'<= q20'],['50',1,'> mediana'],['50',-1,'<= mediana'],['80',1,'> q80'],['80',-1,'<= q80']];
function desenhaGrade(){
  const F=Object.keys(D.feats), b=D.busca[gC+'|'+gG];
  calor('#g_grade',{cols:CORTES.map(c=>c[2]),lins:F,
    cel:F.map(f=>CORTES.map(c=>{const r=D.grade[gC+'|'+gG+'|C_'+f+'_q'+c[0]+'|'+c[1]]||{ganho:0,n:0,ev:0,tercos:[]};
      return {v:r.ganho, melhor:(b.col==='C_'+f+'_q'+c[0]&&b.sent_orig===c[1]),
        dica:`<b>${f} ${c[2]}</b><br>${D.feats[f]}<br><span class="l">sinais</span> ${r.n} &middot; <span class="l">EV</span> ${sinal(r.ev,1)} &middot; <span class="l">ganho</span> ${sinal(r.ganho,1)} &middot; <span class="l">t</span> ${fmt(r.t,2)}<br><span class="l">tercos</span> ${(r.tercos||[]).map(v=>sinal(v,0)).join(' / ')}`};}))},
    {rotX:'corte',casas:1,esq:80,cel:32});
}
desenhaGrade();
bt.addEventListener('click',()=>desenhaGrade());
addEventListener('resize',()=>{clearTimeout(window._rzg); window._rzg=setTimeout(desenhaGrade,200);});
"""
    return J


HTML = RO.HTML.replace('<title>Osciladores no Hull</title>', '<title>Volume Agressor Hull</title>')
MENU = [('resposta', 'Resposta'), ('metodo', 'Metodo'), ('grade', 'Grade'), ('regras', 'Acima da mediana'),
        ('horario', 'Horario e vizinhanca'), ('leituras', 'Faixas'), ('busca', 'Busca'), ('carteira', 'Carteira'),
        ('kline', 'Trade a trade'), ('conclusao', 'Conclusao')]


def markdown(D, F):
    B = D['base']; R = F['R']; bc = F['busca']['cand|parcial']; g = F['g']
    L = ['# Volume agressor como filtro do Hull + pavios', '',
         f"WINFUT, grafico de 20 PI, {n(B['barras'])} candles, {B['dias']} pregoes ({B['ini']} a {B['fim']}). "
         'Resultado bruto. Graficos, grade interativa, curvas, MEP/MEN, duracao e trade a trade em `volume_agressor.html`.', '',
         '**V = agressao compradora + vendedora.** Leituras no fechamento do candle de sinal: vrel_k (media das ultimas k '
         f"barras / media das {D['parametros']['jan_ref']} anteriores), vpct_k (V[i]/V[i-k] - 1), vmed_k (V[i] / media das k "
         'barras anteriores - 1). Cortes q20 / mediana / q80, nos dois sentidos: '
         f"{len(D['feats']) * 6} filtros.", '',
         '## Resposta curta: ' + ('nao' if not F['passou'] else 'um filtro passou no controle'), '',
         f"- Melhor da busca: **{bc['regra']}**, ganho {md_sn(bc['ganho'], 1)} pts; busca contra ruido p = {md_n(bc['p_valor'], 2)}.",
         f"- O mesmo corte com lag de 1, 3 e 5 barras: {', '.join(md_sn(g(f'vpct_{k}', 20, -1).get('ganho'), 1) for k in (1, 3, 5))} -- cara de ruido.",
         f"- 'Retomada com volume' (vmed_k acima da mediana): {', '.join(md_sn(R[f'cand|parcial|R_vmed_{k}']['ganho'], 1) for k in (2, 3, 5))}, "
         'e so na venda.',
         '- Ortogonal a Hull e ao horario; correlacionado com a duracao do candle de sinal (ate '
         f"{md_n(max(D['ortogonalidade']['valores'][f'cand|{f}']['dur_sinal'] for f in D['feats']), 2)}).", '',
         '## 1. Grade de ganho (pts por sinal), Hull + pavios', '']
    for gst in GES:
        L += [f"**{D['rot_gestao'][gst]}**", '', '| Leitura | ' + ' | '.join(c[2] for c in CORTES_ROT) + ' |',
              '|:--|' + '--:|' * len(CORTES_ROT)]
        for f in D['feats']:
            L.append(f"| {f} | " + ' | '.join(md_sn(g(f, q, s, 'cand', gst).get('ganho'), 1) for q, s, _ in CORTES_ROT) + ' |')
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
    L += ['', '## 5. Ortogonalidade (correlacao de posto, Hull + pavios)', '',
          '| Leitura | ' + ' | '.join(D['ortogonalidade']['refs'].values()) + ' |', '|:--|' + '--:|' * len(D['ortogonalidade']['refs'])]
    for f in D['feats']:
        o = D['ortogonalidade']['valores'][f'cand|{f}']
        L.append(f"| {f} | " + ' | '.join(md_sn(o[r], 2) for r in D['ortogonalidade']['refs']) + ' |')
    L += ['', '## 6. Carteira (Hull + pavios)', '',
          '| Gestao | Leitura acima da mediana | Trades | Pts | Pts/trade | Acerto | Fator | Rebaix. |', '|:--|:--|--:|--:|--:|--:|--:|--:|']
    for gst in GES:
        for k in ['base'] + list(D['regras']):
            s = D['carteira'][f'cand|{gst}|{k}']
            L.append(f"| {D['rot_gestao'][gst]} | {'sem filtro' if k == 'base' else k[2:]} | {md_n(s['trades'])} | {md_sn(s['lucro_liq'])} | "
                     f"{md_sn(s['exp_pts'], 1)} | {md_n(s['winrate'], 1)}% | {md_n(s['fator_lucro'], 2)} | {md_n(s['dd_max'])} |")
    L += ['', '## Conclusao', '',
          '- **O volume agressor nao filtra o Hull + pavios** em nenhuma das formas pedidas.',
          '- **Os melhores cortes nao conversam entre lags vizinhos** -- assinatura de acaso.',
          '- **Retomada com volume mede ao contrario, e so na venda.**',
          '- **No PI o volume por candle carrega tempo.** Proximo passo, se houver: saldo agressor na retracao ou volume por minuto.',
          '', '> Resultado bruto, um instrumento. Volume agressor, sem volume total nem numero de negocios.',
          '', 'Reproduzir: `python volume_agressor.py && python relatorio_volume.py`.', '']
    return '\n'.join(L)


def main():
    with open(os.path.join(SAIDA, 'volume_agressor.json'), encoding='utf-8') as f:
        D = json.load(f)
    F = fatos(D)
    md = markdown(D, F)
    D = RO.enxuga(D)
    D['gestoes'] = GESTOES_JS
    # o nome do filtro ja diz o sentido ("no quintil de baixo"); a tabela da busca
    # de relatorio_osciladores acrescentaria "(nao)" em cima disso
    for b in D['busca'].values():
        b['sent_orig'] = b['sentido']; b['sentido'] = 1
        for x in b['fora'].values():
            if x:
                x['sentido'] = 1
    corpo = ''.join([capa(D, F), resposta(D, F), metodo(D, F), grade_sec(D, F), RO.regras_sec(D, F),
                     horario_sec(D, F), RO.quintis_sec(D, F), RO.busca_sec(D, F), RO.carteira_sec(D, F), conclusao(D, F)])
    corpo = (corpo.replace('<h2>1. Cada regra, medida</h2>', '<h2>2. Cada leitura acima da mediana</h2>')
             .replace('<h2>2. As leituras em faixas</h2>', '<h2>4. As leituras em faixas</h2>')
             .replace('<h2>3. A busca contra o ruido, e a escolha fora</h2>', '<h2>5. A busca contra o ruido, e a escolha fora</h2>')
             .replace('<h2>5. A carteira, uma posicao por vez</h2>', '<h2>6. A carteira, uma posicao por vez</h2>')
             .replace('<h2>6. Trade a trade</h2>', '<h2>7. Trade a trade</h2>')
             .replace('foi repetida 500 vezes', 'foi repetida 1.000 vezes')
             .replace('&ldquo;(nao)&rdquo; = o complemento da regra. ', 'O nome do filtro ja diz o sentido do corte. ')
             .replace('Uma regra que valesse passaria do p95 do ruido; nenhuma passa da mediana com folga.',
                      'Uma regra que valesse passaria do p95 do ruido.')
             .replace('Hull 50 no preco; MACD, estocastico lento e IFR embaixo.',
                      'Hull 50 no preco; volume agressor por candle e media de 20 barras embaixo.'))
    with open(RO.VENDOR_KC, encoding='utf-8') as f:
        kline = f.read()
    scripts = ('<script>' + kline + '</script>\n<script>const D=' +
               json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';</script>\n'
               '<script>' + molde.JS_KIT + '</script>\n<script>' + js() + '</script>')
    html = (HTML.replace('__CSS__', molde.CSS)
            .replace('__MENU__', ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU))
            .replace('__SCRIPTS__', scripts).replace('__CORPO__', corpo))
    with open(os.path.join(BASE, 'volume_agressor.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(BASE, 'VOLUME_AGRESSOR.md'), 'w', encoding='utf-8') as f:
        f.write(md)
    print(f'gravado: volume_agressor.html ({len(html) / 1e6:.1f} MB) e VOLUME_AGRESSOR.md')


if __name__ == '__main__':
    main()
