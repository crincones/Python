# -*- coding: utf-8 -*-
"""
Monta ortogonais.html e ORTOGONAIS.md a partir de saida/ortogonais.json.

    python ortogonais.py && python relatorio_ortogonais.py

Mesmo esqueleto de relatorio_osciladores.py (tabelas de regra, faixas, busca,
carteira MT5, curvas, MEP/MEN, duracao e trade a trade). No grafico, a Hull e
a VWAP do dia no preco e o ritmo embaixo.
"""
import json
import os

import molde
import relatorio_osciladores as RO
from relatorio_pavio import n, sn, cls, tile, md_n, md_sn, GESTOES_JS

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
GES = RO.GES


def fatos(D):
    R = D['regras_res']
    F = dict(R=R, busca=D['busca'])
    F['passou'] = [k for k, b in D['busca'].items() if b['p_valor'] <= 0.05]
    F['ort'] = {k: max(abs(v) for v in D['ortogonalidade']['valores'][f'cand|{k}'].values()) for k in D['regras']}
    F['menor_p'] = min(D['busca'].items(), key=lambda kv: kv[1]['p_valor'])
    return F


# =================================================================== corpo
def capa(D, F):
    B = D['base']; P = D['parametros']
    return f"""
<header class="capa">
  <div class="chapeu">Backtest &middot; WINFUT &middot; grafico de 20 PI</div>
  <h1>Filtros ortogonais a Hull<br>velocidade, horario e posicao no dia</h1>
  <p class="sub">Tres informacoes que a Hull 50 nao tem, testadas como filtro dos sinais do Hull + pavios,
  com a ortogonalidade medida em vez de suposta.</p>
  <div style="margin-top:18px">
    <span class="selo">{n(B['barras'])} candles</span>
    <span class="selo">{B['dias']} pregoes, {B['ini']} a {B['fim']}</span>
    <span class="selo">6 regras declaradas</span>
    <span class="selo">ritmo em {P['janela_min']} min</span>
    <span class="selo">horario {int(P['h_ini'])}h a {int(P['h_fim'])}h</span>
    <span class="selo">VWAP do dia</span>
  </div>
</header>"""


def resposta(D, F):
    R = F['R']
    h1c = R['cand|parcial|H1']; h1h = R['h|parcial|H1']; h2c = R['cand|parcial|H2']
    v1 = R['cand|parcial|V1']; v2 = R['cand|parcial|V2']; p1 = R['cand|parcial|P1']; p2 = R['cand|parcial|P2']
    bc = F['busca']['cand|parcial']; bh = F['busca']['h|parcial']; fo = bh['fora']
    hf = {f['faixa']: f for f in D['quintis']['cand|hora_fixa']['faixas']}
    cr = D['horario_ritmo']['cand']['celulas']
    cel = {(c['cedo'], c['rapido']): c for c in cr}
    ch = D['carteira']['h|parcial|base']; ch1 = D['carteira']['h|parcial|H1']
    ort = D['ortogonalidade']['valores']
    titulo = ('Resposta curta: nenhum passa no controle; o horario chega perto'
              if not F['passou'] else 'Resposta curta: um filtro passou no controle')
    return f"""
<section id="resposta">
  <h2>{titulo}</h2>
  <p class="olho">Dos tres filtros, so dois sao de fato ortogonais a Hull: o <b>horario</b> e o <b>ritmo</b>
  (correlacao de posto abaixo de 0,1 com a inclinacao da Hull, a distancia Hull &minus; EMA e o MACD). A
  <b>posicao no dia</b> nao e: estar do lado certo da VWAP tem correlacao de
  {n(ort['cand|P1']['macd_atr'], 2)} com o MACD &mdash; e tendencia de novo. O ritmo mede ao contrario do
  esperado. O horario e o resultado mais consistente de todos os estudos do Hull ate aqui, mas nao se
  separa de sorte no controle de busca.</p>
  <div class="grade g4">
    {tile('Hull + pavios, das 10h as 15h', sn(h1c['ev'], 1), f"pts por sinal, contra {sn(h1c['base'], 1)} sem filtro", cls(h1c['ganho']))}
    {tile('Sinais das 9h as 10h', sn(hf['9h-10h']['ev'], 1), f"pts por sinal &middot; {n(hf['9h-10h']['n'])} sinais", cls(hf['9h-10h']['ev']))}
    {tile('Busca contra ruido', 'p = ' + n(bc['p_valor'], 2), f"Hull + pavios; Hull + 2 a 4: p = {n(bh['p_valor'], 2)}")}
    {tile('Menor ganho detectavel', sn(bc['poder'][0]['min_ganho'], 1), 'pts, filtro que mantem metade')}
  </div>
  <div class="bandeira">
    <h3>O que o estudo encontrou</h3>
    <ul class="enx">
      <li><b>Horario: todos os recortes a favor, sem significancia.</b> Operar so das 10h as 15h leva o Hull +
      pavios de {sn(h1c['base'], 1)} para {sn(h1c['ev'], 1)} pts por sinal (Hull + 2 a 4: {sn(h1h['base'], 1)} para
      {sn(h1h['ev'], 1)}). Melhora nos tres tercos ({' / '.join(sn(v, 0) for v in h1c['tercos'])} contra
      {' / '.join(sn(v, 0) for v in h1c['tercos_base'])}), antes de 06/08 ({sn(h1c['blocos']['antes'], 1)} contra
      {sn(h1c['blocos_base']['antes'], 1)}), na compra e na venda, nas quatro gestoes, e o corte forma plato
      (10h&ndash;14h, 10h&ndash;15h e 10h&ndash;16h medem parecido). No Hull + 2 a 4, a busca feita so com os meses
      antes de 06/08 escolhe justamente este filtro, e no resto do periodo ele mede {sn(fo['antes -> original+depois']['ev_teste'], 1)}
      contra {sn(fo['antes -> original+depois']['ev_teste_base'], 1)} sem filtro. Mas o ganho e de
      {sn(h1c['ganho'], 1)} pts, abaixo do que a amostra separa de sorte, e a busca em ruido acha algo tao bom
      em {n(bc['p_valor'] * 100, 0)}% das vezes.</li>
      <li><b>O que o horario tira e a primeira hora.</b> Das 9h as 10h o Hull + pavios mede
      {sn(hf['9h-10h']['ev'], 1)} pts por sinal em {n(hf['9h-10h']['n'])} sinais &mdash; quase um quarto do total.
      Nao e o ritmo disfarcado: com o ritmo normal, antes das 10h mede {sn(cel[(True, False)]['ev'], 1)} e depois
      {sn(cel[(False, False)]['ev'], 1)}. O estudo principal ja tinha visto a mesma hora negativa.</li>
      <li><b>Ritmo: a hipotese estava errada.</b> Mercado parado nao atrapalha: o ritmo acima da mediana mede
      {sn(v1['ganho'], 1)} e tirar o quartil mais lento, {sn(v2['ganho'], 1)}. O que mede pior e o mercado
      <i>mais rapido</i> (quintil de cima: {sn(D['quintis']['cand|ritmo_r']['faixas'][4]['ev'], 1)}) &mdash; que
      acontece em {n(D['horario_ritmo']['cand']['frac_rapido_cedo'], 0)}% das vezes antes das 10h. Mesmo depois das
      10h, o rapido mede {sn(cel[(False, True)]['ev'], 1)} contra {sn(cel[(False, False)]['ev'], 1)} do normal:
      indicio, nao regra, porque o sentido nao foi o declarado.</li>
      <li><b>Posicao no dia: nao e ortogonal, e nao ajuda.</b> Do lado certo da VWAP: {sn(p1['ganho'], 1)}; do lado
      certo da abertura do pregao: {sn(p2['ganho'], 1)}.</li>
    </ul>
  </div>
  <p class="nota"><b>Por que importa mesmo sem passar no controle:</b> o Hull vive do custo. Na carteira do Hull
  + 2 a 4 (1:3 com parcial), das 10h as 15h o valor por trade vai de {sn(ch['exp_pts'], 1)} para
  {sn(ch1['exp_pts'], 1)} com {n(ch1['trades'])} operacoes em vez de {n(ch['trades'])}; a 5 pts de custo, de
  {sn(ch['exp_pts'] - 5, 1)} para {sn(ch1['exp_pts'] - 5, 1)}. Operar menos no horario ruim reduz custo e
  corretagem sem nenhum indicador a mais. Nenhum plano foi alterado: a decisao de levar o horario ao plano
  provisorio do Hull, como hipotese para o simulador, fica com voce.</p>
</section>"""


def metodo(D, F):
    V = D['ortogonalidade']['valores']; refs = D['ortogonalidade']['refs']
    lin = ''
    for k, v in D['regras'].items():
        o = V[f'cand|{k}']
        mx = max(abs(z) for z in o.values())
        lin += (f"<tr><td><b>{k}</b></td><td>{v[0]}</td><td style='text-align:left'>{v[1]}</td>"
                f"<td>{n(D['freq']['cand'][k], 0)}%</td>"
                + ''.join(f"<td class='{'neg' if abs(o[r]) > 0.3 else ''}'>{sn(o[r], 2)}</td>" for r in refs)
                + f"<td><b>{'nao' if mx > 0.3 else 'sim'}</b></td></tr>")
    lc = ''
    for k, rot in D['continuas'].items():
        o = V[f'cand|{k}']
        lc += (f"<tr><td style='text-align:left'>{rot}</td>"
               + ''.join(f"<td class='{'neg' if abs(o[r]) > 0.3 else ''}'>{sn(o[r], 2)}</td>" for r in refs) + '</tr>')
    P = D['parametros']
    return f"""
<section id="metodo">
  <h2>Como foi medido</h2>
  <div class="grade g2">
    <div class="card">
      <h3>As seis regras, declaradas antes de medir</h3>
      <p><b>Velocidade</b>: ritmo = candles de 20 PI por minuto na ultima hora do pregao (na primeira hora, no
      tempo decorrido, com piso de 15 min), dividido pela mediana do proprio ritmo nas {n(P['ref_barras'])} barras
      anteriores. <b>V1</b> ritmo acima da mediana; <b>V2</b> fora do quartil mais baixo (&lt; {n(P['q_ritmo'], 2)}).
      A ideia: com stop e alvo fixos em pontos, mercado parado nao chega ao alvo a tempo.</p>
      <p><b>Horario</b>: <b>H1</b> sinal das 10h as 15h; <b>H2</b> a partir das 10h (abertura do mercado a vista).</p>
      <p style="margin-bottom:0"><b>Posicao no dia</b>: <b>P1</b> fechamento do lado do trade na VWAP do dia; <b>P2</b>
      do lado do trade na abertura do pregao. A VWAP usa o volume agressor e o preco tipico, acumulada desde o
      primeiro candle do pregao &mdash; a base do robo nao traz volume total.</p>
    </div>
    <div class="card">
      <h3>Sinais e controles</h3>
      <p>Os sinais de <code>hull_contra</code>: <b>Hull + 2 a 4</b> ({n(D['base']['n_h'])}) e <b>Hull + pavios</b>
      &mdash; 2 a 3 candles e pavio do fechamento ate 10% ({n(D['base']['n_cand'])}). Ficam de fora os sinais dos
      primeiros ~6 pregoes, em que a mediana do ritmo ainda nao existe. Entrada no fechamento, quatro gestoes.</p>
      <p style="margin-bottom:0">Permutacao do ganho, tercos, lados, blocos antes/depois de 06/08, sorteio;
      <b>busca</b> com as 6 regras e seus complementos contra 1.000 embaralhamentos dos resultados; <b>escolha
      fora</b> (escolhe antes de 06/08, mede depois; escolhe em T1+T2, mede em T3); poder; vizinhanca.</p>
    </div>
  </div>
  <div class="card rolo" style="margin-top:16px">
    <h3>Ortogonalidade medida (Hull + pavios)</h3>
    <table><thead><tr><th></th><th>Grupo</th><th>Regra</th><th>Passam</th>
      {''.join(f'<th>corr. com {r}</th>' for r in refs.values())}<th>Ortogonal?</th></tr></thead>
      <tbody>{lin}</tbody></table>
    <table style="margin-top:14px"><thead><tr><th>Leitura continua</th>
      {''.join(f'<th>{r}</th>' for r in refs.values())}</tr></thead><tbody>{lc}</tbody></table>
    <p class="nota">Correlacao de posto dentro dos sinais. Acima de 0,3 em modulo (em vermelho), a regra repete
    informacao de tendencia que a Hull ja tem.</p>
  </div>
</section>"""


def quintis_sec(D, F):
    ab = ''.join(f'<button class="aba" data-v="{k}" aria-pressed="{str(k == "hora_fixa").lower()}">{r}</button>'
                 for k, r in [('hora_fixa', 'Hora (faixas fixas)')] + list(D['continuas'].items()))
    lin = ''
    for cj in ('cand', 'h'):
        c = D['horario_ritmo'][cj]
        cel = {(x['cedo'], x['rapido']): x for x in c['celulas']}
        for cedo in (True, False):
            lin += (f"<tr><td>{D['conj'][cj].split(' (')[0]}</td><td>{'antes das 10h' if cedo else 'a partir das 10h'}</td>"
                    + ''.join(f"<td class='{cls(cel[(cedo, r)]['ev'])}'>{sn(cel[(cedo, r)]['ev'], 1)}"
                              f"<br><small style='color:var(--mudo)'>{n(cel[(cedo, r)]['n'])} sinais</small></td>"
                              for r in (False, True)) + '</tr>')
    return f"""
<section id="leituras">
  <h2>2. As leituras em faixas</h2>
  <p class="olho">Sem corte: cada leitura em quintis (e a hora tambem em faixas fixas de uma hora). Um filtro de
  verdade apareceria como escada, nos tres tercos.</p>
  <div class="abas" id="abas_q" style="margin-bottom:6px">{ab}</div>
  <div class="abas" id="abas_qc">
    <button class="aba" data-v="cand" aria-pressed="true">Hull + pavios</button>
    <button class="aba" data-v="h" aria-pressed="false">Hull + 2 a 4</button></div>
  <p class="nota" id="q_lim"></p>
  <div class="grade g2">
    <figure class="card"><h3>Pts por sinal, por faixa</h3><div id="g_q"></div>
      <figcaption>1:3 com parcial, entrada no fechamento</figcaption></figure>
    <figure class="card"><h3>Em cada terco</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--bronze)"></i>T1</span>
      <span><i class="chave q" style="background:var(--prata)"></i>T2</span>
      <span><i class="chave q" style="background:var(--ouro)"></i>T3</span></div>
      <div id="g_q_t"></div></figure>
  </div>
  <div class="card rolo" style="margin-top:16px">
    <h3>Horario x ritmo: e a mesma coisa?</h3>
    <table><thead><tr><th>Conjunto</th><th>Horario</th><th>Ritmo normal</th><th>Ritmo rapido<br>
      <small>(quintil de cima)</small></th></tr></thead><tbody>{lin}</tbody></table>
    <p class="nota">A primeira hora e a mais rapida do dia, entao os dois efeitos podiam ser um so. Nao sao: com o
    ritmo normal, antes das 10h continua pior; e depois das 10h, o ritmo rapido continua pior que o normal.</p>
  </div>
</section>"""


def vizinhanca_sec(D, F):
    lin = ''.join(f"<tr><td>{v['regra']}</td><td style='text-align:left'>{v['par']}{' *' if v['padrao'] else ''}</td>"
                  f"<td>{n(v['n'])}</td><td class='{cls(v['ganho'])}'><b>{sn(v['ganho'], 1)}</b></td></tr>"
                  for v in D['vizinhanca'].values())
    return f"""
<section id="vizinhanca">
  <h2>4. Vizinhanca</h2>
  <p class="olho">Ganho de cada regra no Hull + pavios (1:3 com parcial) mexendo so no parametro dela. * = o
  declarado.</p>
  <div class="card rolo" style="max-width:640px"><table><thead><tr><th>Regra</th><th>Parametro</th><th>Sinais</th>
    <th>Ganho</th></tr></thead><tbody>{lin}</tbody></table>
    <p class="nota">O horario forma plato no fim da janela (14h, 15h ou 16h) e cresce ao atrasar o inicio (9h30,
    10h, 10h30): o que pesa e tirar a primeira hora. O ritmo acima da mediana muda de sinal com a janela: nao ha regra ali.</p></div>
</section>"""


def conclusao(D, F):
    R = F['R']; bc = F['busca']['cand|parcial']
    h1 = R['cand|parcial|H1']
    return f"""
<section id="conclusao">
  <h2>Conclusao</h2>
  <ul class="enx">
    <li><b>Nenhum filtro passa no controle de busca</b> (Hull + pavios: melhor t = {sn(bc['t'], 2)}, ruido
    {sn(bc['ruido_mediana'], 2)} na mediana, p = {n(bc['p_valor'], 2)}).</li>
    <li><b>Posicao no dia nao e ortogonal.</b> Do lado certo da VWAP ou da abertura e, na maior parte das vezes,
    o mesmo que a Hull a favor &mdash; e nao acrescenta nada.</li>
    <li><b>Ritmo e ortogonal, mas a hipotese estava ao contrario:</b> o mercado lento nao atrapalha; o
    rapidissimo, sim, e nao so na primeira hora. Fica anotado como hipotese nova, no sentido oposto ao declarado.</li>
    <li><b>O horario e o melhor candidato de todos os estudos do Hull.</b> Declarado antes, ortogonal, a favor em
    todos os recortes, com plato, e escolhido corretamente fora da amostra &mdash; mas com {sn(h1['ganho'], 1)} pts de
    ganho, pequeno demais para esta base provar. Na pratica, <b>nao operar antes das 10h</b> e a regra mais barata de
    testar no simulador: corta um quarto dos trades, e justamente os que pagam menos.</li>
  </ul>
  <p class="nota">Resultado bruto, um instrumento. A VWAP usa o volume agressor, nao o total. O ritmo depende de
  horarios com resolucao de minuto.</p>
</section>
<footer>Gerado por <code>ortogonais.py</code> e <code>relatorio_ortogonais.py</code>.</footer>"""


# ======================================================================= JS
def js():
    J = RO.JS

    def troca(a, b):
        nonlocal J
        assert a in J, a[:60]
        J = J.replace(a, b)
    i = J.index("klinecharts.registerIndicator({name:'OS_HULL'")
    j = J.index("let kchart=null")
    J = J[:i] + r"""klinecharts.registerIndicator({name:'OS_HULL',shortName:'Hull 50 / VWAP / abertura',series:'price',precision:0,
  figures:[{key:'hma',title:'Hull 50: ',type:'line'},{key:'vwap',title:'VWAP: ',type:'line'},{key:'abre',title:'abertura: ',type:'line'}],
  calc:dl=>dl.map(k=>({hma:k.hma,vwap:k.vwap,abre:k.abre}))});
klinecharts.registerIndicator({name:'OS_RITMO',shortName:'Ritmo / mediana',precision:2,minValue:0,
  figures:[{key:'ritmo',title:'ritmo: ',type:'bar',baseValue:1,
    styles:({data})=>{const v=(data.current||{}).ritmo; return {style:'fill',color:alfa(v>=1?c_('prata'):c_('mudo'),.6)};}}],
  calc:dl=>dl.map(k=>({ritmo:k.ritmo}))});

""" + J[j:]
    troca("""    hma:C.hma[i],macd:C.macd[i],sinal:C.sinal[i],hist:C.hist[i],k:C.k[i],d:C.d[i],ifr:C.ifr[i]});""",
          """    hma:C.hma[i],vwap:C.vwap[i],abre:C.abertura[i],ritmo:C.ritmo[i]});""")
    troca("""  kchart.createIndicator('OS_MACD',false,{id:'p_macd',height:110});
  kchart.createIndicator('OS_ESTOC',false,{id:'p_estoc',height:100});
  kchart.createIndicator('OS_IFR',false,{id:'p_ifr',height:100});""",
          """  kchart.createIndicator('OS_RITMO',false,{id:'p_ritmo',height:120});""")
    troca("""    `<span>MACD ${fmt(C.macd[ti],0)} &middot; %K ${fmt(C.k[ti],0)} / %D ${fmt(C.d[ti],0)} &middot; IFR ${fmt(C.ifr[ti],0)}</span>`+""",
          """    `<span>ritmo ${fmt(C.ritmo[ti],2)} &middot; ${ld*(C.c[ti]-C.vwap[ti])>0?'lado certo':'lado errado'} da VWAP (${fmt(C.vwap[ti],0)})</span>`+""")
    troca("""  document.getElementById('q_lim').innerHTML='<b>'+D.continuas[qM]+'</b> &middot; limites dos quintis: '+Q.limites.map(v=>fmt(v,2)).join(' / ');""",
          """  document.getElementById('q_lim').innerHTML=qM==='hora_fixa'?'<b>Hora do sinal</b>, faixas de uma hora':
    '<b>'+D.continuas[qM]+'</b> &middot; limites dos quintis: '+Q.limites.map(v=>fmt(v,2)).join(' / ');""")
    troca("let qM='ifr', qC='cand';", "let qM='hora_fixa', qC='cand';")
    troca("barrasH('#g_ganho',L.filter(r=>r.ev!==null).map(r=>({nome:r.k+' '+D.regras[r.k][1],v:r.ganho,",
          "barrasH('#g_ganho',L.filter(r=>r.ev!==null).map(r=>({nome:r.k+' '+D.regras[r.k][1],v:r.ganho,")
    return J


HTML = RO.HTML.replace('<title>Osciladores no Hull</title>', '<title>Filtros Ortogonais Hull</title>')
MENU = [('resposta', 'Resposta'), ('metodo', 'Metodo'), ('regras', 'Regras'), ('leituras', 'Faixas'),
        ('busca', 'Busca'), ('vizinhanca', 'Vizinhanca'), ('carteira', 'Carteira'), ('kline', 'Trade a trade'),
        ('conclusao', 'Conclusao')]


# ======================================================================= MD
def markdown(D, F):
    B = D['base']; R = F['R']; bc = F['busca']['cand|parcial']; bh = F['busca']['h|parcial']
    V = D['ortogonalidade']['valores']; refs = D['ortogonalidade']['refs']
    L = ['# Filtros ortogonais a Hull: velocidade, horario e posicao no dia', '',
         f"WINFUT, grafico de 20 PI, {n(B['barras'])} candles, {B['dias']} pregoes ({B['ini']} a {B['fim']}). "
         'Resultado bruto. Graficos, curvas, MEP/MEN, duracao e trade a trade em `ortogonais.html`.', '',
         f"**Sinais**: Hull + 2 a 4 ({n(B['n_h'])}) e Hull + pavios ({n(B['n_cand'])}).", '',
         '## Resposta curta: ' + ('nenhum passa no controle; o horario chega perto' if not F['passou']
                                  else 'um filtro passou no controle'), '',
         f"- **Ortogonais de fato:** horario e ritmo (|corr| < 0,1 com Hull, Hull-EMA e MACD). **Nao ortogonal:** "
         f"posicao no dia (VWAP x MACD {md_n(V['cand|P1']['macd_atr'], 2)}).",
         f"- **Horario 10h-15h** (H1): {md_sn(R['cand|parcial|H1']['base'], 1)} -> {md_sn(R['cand|parcial|H1']['ev'], 1)} "
         f"pts por sinal no Hull + pavios; a favor nos tres tercos, antes de 06/08, nos dois lados, nas 4 gestoes, com "
         f"plato; escolhido fora da amostra e confirmado. Mas busca contra ruido: p = {md_n(bc['p_valor'], 2)} "
         f"(Hull + 2 a 4: {md_n(bh['p_valor'], 2)}).",
         f"- **Ritmo:** hipotese ao contrario -- mercado lento nao atrapalha (V1 {md_sn(R['cand|parcial|V1']['ganho'], 1)}, "
         f"V2 {md_sn(R['cand|parcial|V2']['ganho'], 1)}); o mais rapido mede pior.",
         f"- **Posicao no dia:** P1 {md_sn(R['cand|parcial|P1']['ganho'], 1)}, P2 {md_sn(R['cand|parcial|P2']['ganho'], 1)}.",
         '', '## Ortogonalidade (correlacao de posto, Hull + pavios)', '',
         '| Regra / leitura | ' + ' | '.join(refs.values()) + ' |', '|:--|' + '--:|' * len(refs)]
    for k in list(D['regras']) + list(D['continuas']):
        o = V[f'cand|{k}']
        L.append(f"| {k} | " + ' | '.join(md_sn(o[r], 2) for r in refs) + ' |')
    L += ['', '## Cada regra (fechamento)', '']
    for cj in ('cand', 'h'):
        for g in GES:
            L += [f"**{D['conj'][cj]} -- {D['rot_gestao'][g]}** (sem filtro: {md_sn(R[f'{cj}|{g}|H1']['base'], 1)})", '',
                  '| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 (sem filtro) | Antes (sem filtro) | Compra | Venda | Pct |',
                  '|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|']
            for k, v in D['regras'].items():
                r = R[f'{cj}|{g}|{k}']
                if r['ev'] is None:
                    continue
                L.append(f"| {k} | {v[1]} | {r['n']} ({md_n(r['frac'])}%) | {md_sn(r['ev'], 1)} | {md_sn(r['ev_fora'], 1)} | "
                         f"**{md_sn(r['ganho'], 1)}** | {md_n(r['p_bi'], 3)} | " + ' / '.join(md_sn(x, 0) for x in r['tercos'])
                         + ' (' + ' / '.join(md_sn(x, 0) for x in r['tercos_base']) + ')'
                         + f" | {md_sn(r['blocos']['antes'], 1)} ({md_sn(r['blocos_base']['antes'], 1)}) | "
                         f"{md_sn(r['compra'], 1)} | {md_sn(r['venda'], 1)} | {md_n(r['sorteio_pct'])} |")
            L.append('')
    L += ['## Faixas (Hull + pavios, 1:3 com parcial)', '',
          'Hora: ' + ' / '.join(f"{f['faixa']} {md_sn(f['ev'], 1)} ({f['n']})" for f in D['quintis']['cand|hora_fixa']['faixas']), '']
    for col, rot in D['continuas'].items():
        q = D['quintis'][f'cand|{col}']
        L.append(f"- {rot}: limites " + ' / '.join(md_n(x, 2) for x in q['limites']) + ' -> '
                 + ' / '.join(md_sn(f['ev'], 1) for f in q['faixas']))
    L += ['', '**Horario x ritmo** (ritmo rapido = quintil de cima):', '',
          '| Conjunto | Horario | Ritmo normal | Ritmo rapido |', '|:--|:--|--:|--:|']
    for cj in ('cand', 'h'):
        cel = {(x['cedo'], x['rapido']): x for x in D['horario_ritmo'][cj]['celulas']}
        for cedo in (True, False):
            L.append(f"| {cj} | {'antes das 10h' if cedo else 'a partir das 10h'} | "
                     f"{md_sn(cel[(cedo, False)]['ev'], 1)} ({cel[(cedo, False)]['n']}) | "
                     f"{md_sn(cel[(cedo, True)]['ev'], 1)} ({cel[(cedo, True)]['n']}) |")
    L += ['', '## Busca contra ruido e escolha fora', '',
          '| Conjunto | Gestao | Melhor | t | ruido med | ruido p95 | p | Escolhida antes, medida depois | Escolhida T1+T2, medida T3 |',
          '|:--|:--|:--|--:|--:|--:|--:|:--|:--|']
    for cj in ('cand', 'h'):
        for g in GES:
            b = D['busca'][f'{cj}|{g}']
            cel = []
            for rot in ('antes -> original+depois', 'T1+T2 -> T3'):
                x = b['fora'].get(rot)
                cel.append('-' if not x else f"{x['regra']}{'' if x['sentido'] > 0 else ' (nao)'} {md_sn(x['ev_teste'], 1)} "
                           f"(sem filtro {md_sn(x['ev_teste_base'], 1)})")
            L.append(f"| {cj} | {D['rot_gestao'][g]} | {b['regra']}{'' if b['sentido'] == 1 else ' (nao)'} | {md_sn(b['t'], 2)} | "
                     f"{md_sn(b['ruido_mediana'], 2)} | {md_sn(b['ruido_p95'], 2)} | {md_n(b['p_valor'], 2)} | {cel[0]} | {cel[1]} |")
    L += ['', '## Vizinhanca (ganho, Hull + pavios, 1:3 com parcial)', '',
          '| Regra | Parametro | Sinais | Ganho |', '|:--|:--|--:|--:|']
    for v in D['vizinhanca'].values():
        L.append(f"| {v['regra']} | {v['par']}{' (declarado)' if v['padrao'] else ''} | {v['n']} | {md_sn(v['ganho'], 1)} |")
    L += ['', '## Carteira, uma posicao por vez', '',
          '| Conjunto | Gestao | Regra | Trades | Pts | Pts/trade | Acerto | Fator | Rebaix. | Antes (pts/trade) |',
          '|:--|:--|:--|--:|--:|--:|--:|--:|--:|--:|']
    for cj in ('cand', 'h'):
        for g in GES:
            for k in ['base'] + list(D['regras']):
                s = D['carteira'][f'{cj}|{g}|{k}']
                L.append(f"| {cj} | {D['rot_gestao'][g]} | {'sem filtro' if k == 'base' else k} | {md_n(s['trades'])} | "
                         f"{md_sn(s['lucro_liq'])} | {md_sn(s['exp_pts'], 1)} | {md_n(s['winrate'], 1)}% | "
                         f"{md_n(s['fator_lucro'], 2)} | {md_n(s['dd_max'])} | {md_sn(s['blocos']['antes']['ev'], 1)} |")
    h1 = R['cand|parcial|H1']
    L += ['', '## Conclusao', '',
          '- **Nenhum filtro passa no controle de busca.**',
          '- **Posicao no dia nao e ortogonal** a Hull e nao acrescenta nada.',
          '- **Ritmo e ortogonal, mas a hipotese estava ao contrario**: o mercado mais rapido e que mede pior. '
          'Hipotese nova, no sentido oposto ao declarado.',
          f"- **Horario e o melhor candidato de todos os estudos do Hull**: declarado antes, ortogonal, a favor em "
          f"todos os recortes, com plato e confirmado na escolha fora da amostra, mas com {md_sn(h1['ganho'], 1)} pts "
          'de ganho, pequeno demais para esta base provar. Regra mais barata para o simulador: nao operar antes das 10h.',
          '', '> Resultado bruto, um instrumento. VWAP com volume agressor. Nenhum plano foi alterado.',
          '', 'Reproduzir: `python ortogonais.py && python relatorio_ortogonais.py`.', '']
    return '\n'.join(L)


def main():
    with open(os.path.join(SAIDA, 'ortogonais.json'), encoding='utf-8') as f:
        D = json.load(f)
    F = fatos(D)
    md = markdown(D, F)
    D = RO.enxuga(D)
    D['gestoes'] = GESTOES_JS
    corpo = ''.join([capa(D, F), resposta(D, F), metodo(D, F), RO.regras_sec(D, F), quintis_sec(D, F),
                     RO.busca_sec(D, F), vizinhanca_sec(D, F), RO.carteira_sec(D, F), conclusao(D, F)])
    corpo = corpo.replace('Hull 50 no preco; MACD, estocastico lento e IFR embaixo.',
                          'Hull 50, VWAP do dia e abertura do pregao no preco; ritmo / mediana embaixo.')
    corpo = corpo.replace("Uma regra que valesse passaria do p95 do ruido; nenhuma passa da mediana com folga.",
                          "Uma regra que valesse passaria do p95 do ruido.")
    corpo = corpo.replace("foi repetida 500 vezes", "foi repetida 1.000 vezes")
    with open(RO.VENDOR_KC, encoding='utf-8') as f:
        kline = f.read()
    scripts = ('<script>' + kline + '</script>\n<script>const D=' +
               json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';</script>\n'
               '<script>' + molde.JS_KIT + '</script>\n<script>' + js() + '</script>')
    html = (HTML.replace('__CSS__', molde.CSS)
            .replace('__MENU__', ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU))
            .replace('__SCRIPTS__', scripts).replace('__CORPO__', corpo))
    with open(os.path.join(BASE, 'ortogonais.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(BASE, 'ORTOGONAIS.md'), 'w', encoding='utf-8') as f:
        f.write(md)
    print(f'gravado: ortogonais.html ({len(html) / 1e6:.1f} MB) e ORTOGONAIS.md')


if __name__ == '__main__':
    main()
