# -*- coding: utf-8 -*-
"""
Monta osciladores.html e OSCILADORES.md a partir de saida/osciladores.json.

    python osciladores.py && python relatorio_osciladores.py

Reaproveita o CSS e o kit de graficos de molde.py e o klinecharts de vendor/.
O html sai offline, num arquivo so. Os numeros do texto saem do json.
"""
import json
import os

import molde
from relatorio_pavio import n, sn, cls, tile, md_n, md_sn, GESTOES_JS

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
VENDOR_KC = os.path.join(BASE, 'vendor', 'klinecharts-9.8.10.min.js')
GES = ('parcial', 'puro', 'r2', 'r1')


# ================================================================= numeros
def fatos(D):
    R = D['regras_res']
    F = dict(R=R)
    F['base_cand'] = R['cand|parcial|M1']['base']
    F['base_h'] = R['h|parcial|M1']['base']
    F['degeneradas'] = [k for k in D['classicas']
                        if D['freq']['cand'][k] < 5 or D['freq']['cand'][k] > 95]
    F['busca'] = D['busca']
    F['passou'] = [k for k, b in D['busca'].items() if b['p_valor'] <= 0.05]
    val = {k: R[f'cand|parcial|{k}'] for k in D['regras'] if R[f'cand|parcial|{k}']['ev'] is not None}
    F['melhor'] = max(val, key=lambda k: val[k]['ganho'])
    F['pior'] = min(val, key=lambda k: val[k]['ganho'])
    # regras de volume razoavel (20% a 80% dos sinais)
    F['uteis'] = [k for k in D['regras'] if 15 <= D['freq']['cand'][k] <= 85]
    F['melhor_util'] = max(F['uteis'], key=lambda k: R[f'cand|parcial|{k}']['ganho'])
    return F


def rot_regra(D, k, sent=1):
    r = D['regras'][k][1]
    return r if sent > 0 else f'NAO ({r})'


# =================================================================== corpo
def capa(D, F):
    B = D['base']; P = D['parametros']
    return f"""
<header class="capa">
  <div class="chapeu">Backtest &middot; WINFUT &middot; grafico de 20 PI</div>
  <h1>MACD, estocastico e IFR<br>como filtro do Hull + pavios</h1>
  <p class="sub">Os tres osciladores com os parametros padrao do Profit, lidos no fechamento do candle
  de sinal, testados como filtro dos sinais do estudo <code>hull_contra</code>.</p>
  <div style="margin-top:18px">
    <span class="selo">{n(B['barras'])} candles</span>
    <span class="selo">{B['dias']} pregoes, {B['ini']} a {B['fim']}</span>
    <span class="selo">MACD {P['macd'][0]}/{P['macd'][1]}/{P['macd'][2]}</span>
    <span class="selo">estocastico lento {P['estoc'][0]},{P['estoc'][1]},{P['estoc'][2]}</span>
    <span class="selo">IFR {P['ifr']}</span>
    <span class="selo">{len(D['regras'])} regras declaradas</span>
  </div>
</header>"""


def resposta(D, F):
    R = F['R']; bc = F['busca']['cand|parcial']; bh = F['busca']['h|parcial']
    mu = F['melhor_util']; ru = R[f'cand|parcial|{mu}']
    m3 = R['cand|parcial|M3']; e3 = R['cand|parcial|E3']; m1 = R['cand|parcial|M1']
    fo = bc['fora']
    titulo = ('Resposta curta: nao' if not F['passou'] else 'Resposta curta: um filtro passou no controle')
    viz_e3 = D["vizinhanca"].get("E3|(8, 3, 3)", {}).get('ganho')
    return f"""
<section id="resposta">
  <h2>{titulo}</h2>
  <p class="olho">Nenhum dos {len(D['regras'])} filtros separa os sinais do Hull + pavios de um jeito
  que resista ao controle de busca. O Hull + pavios mede <b>{sn(F['base_cand'], 1)}</b> pts por sinal
  (1:3 com parcial); o melhor filtro com volume razoavel &mdash; {D['regras'][mu][1].lower()} &mdash;
  leva a <b>{sn(ru['ev'], 1)}</b>, e a mesma busca feita com os resultados embaralhados acha algo tao bom
  em {n(bc['p_valor'] * 100, 0)}% das vezes.</p>
  <div class="grade g4">
    {tile('Hull + pavios, sem filtro', sn(F['base_cand'], 1), f"pts por sinal &middot; {n(D['base']['n_cand'])} sinais", cls(F['base_cand']))}
    {tile('Melhor filtro com volume', sn(ru['ganho'], 1), f"pts de ganho &middot; {mu}, {n(ru['frac'], 0)}% dos sinais", cls(ru['ganho']))}
    {tile('Busca contra ruido', 'p = ' + n(bc['p_valor'], 2), f"t real {sn(bc['t'], 2)} &middot; ruido {sn(bc['ruido_mediana'], 2)}")}
    {tile('Menor ganho detectavel', sn(bc['poder'][0]['min_ganho'], 1), 'pts, filtro que mantem metade')}
  </div>
  <div class="bandeira">
    <h3>O que o estudo encontrou</h3>
    <ul class="enx">
      <li><b>As regras classicas quase nunca disparam neste padrao.</b> {len(F['degeneradas'])} das
      {len(D['classicas'])} ({', '.join(F['degeneradas'])}) aceitam menos de 5% ou mais de 95% dos sinais. Nao
      e defeito do teste: depois de 2 a 4 candles contra, o estocastico lento ainda esta caindo no candle
      que volta ({n(D['freq']['cand']['E1'], 0)}% dos sinais tem %K acima de %D), e a retracao curta com a Hull
      a favor raramente leva o %K abaixo de 20 ou o IFR abaixo de 40. Por isso o estudo acrescentou cinco
      regras por quintil, definidas so pela frequencia.</li>
      <li><b>Tendencia a favor aponta para o lado certo, pouco.</b> O IFR no quintil mais alto
      ({sn(R['cand|parcial|I5']['ganho'], 1)} pts) melhora nos tres tercos, antes e depois de 06/08 e nos dois
      lados. O MACD acima de zero ({sn(m1['ganho'], 1)}) melhora so nos periodos fracos (T1, T2, antes de 06/08)
      e so na compra. Os dois ficam abaixo do que a amostra consegue distinguir
      ({sn(bc['poder'][0]['min_ganho'], 1)} pts) e nao passam na busca.</li>
      <li><b>Histograma do MACD subindo no sinal mede pior</b> ({sn(m3['ganho'], 1)} pts, p =
      {n(m3['p_bi'], 3)} como teste isolado, negativo nas quatro gestoes). Mas descartar esses sinais so
      acrescenta {sn(-m3['ganho'] * m3['frac'] / (100 - m3['frac']), 1)} pts aos que ficam, e na busca contra
      ruido nao se distingue de sorte.</li>
      <li><b>%K abaixo de 20 na retracao mede muito</b> ({sn(e3['ganho'], 1)} pts) &mdash; em
      {n(e3['n'])} sinais em {D['base']['dias']} pregoes. Com o estocastico de 8 periodos o mesmo corte mede
      {sn(viz_e3, 1) if viz_e3 is not None else 'sem amostra'}: nao ha plato, e a amostra nao sustenta regra.</li>
      <li><b>Escolher o filtro fora do periodo de teste piora o resultado.</b> Escolhido so com os meses
      antes de 06/08, o melhor filtro e {rot_regra(D, fo['antes -> original+depois']['regra'], fo['antes -> original+depois']['sentido']).lower()};
      no resto do periodo ele mede {sn(fo['antes -> original+depois']['ev_teste'], 1)} contra
      {sn(fo['antes -> original+depois']['ev_teste_base'], 1)} sem filtro. Escolhido em T1+T2, mede
      {sn(fo['T1+T2 -> T3']['ev_teste'], 1)} em T3 contra {sn(fo['T1+T2 -> T3']['ev_teste_base'], 1)}.</li>
    </ul>
  </div>
  <p class="nota">Como nenhum filtro passou, este estudo nao traz plano novo. O plano provisorio do
  Hull (<code>plano_hull.html</code>) continua valendo como estava, sem oscilador.</p>
</section>"""


def metodo(D, F):
    lin = ''.join(f"<tr><td><b>{k}</b></td><td>{v[0]}</td><td style='text-align:left'>{v[1]}</td>"
                  f"<td>{n(D['freq']['h'][k], 0)}%</td><td>{n(D['freq']['cand'][k], 0)}%</td>"
                  f"<td>{'classica' if k in D['classicas'] else 'por quintil'}</td></tr>"
                  for k, v in D['regras'].items())
    L = D['limites']
    return f"""
<section id="metodo">
  <h2>Como foi medido</h2>
  <div class="grade g2">
    <div class="card">
      <h3>Os sinais</h3>
      <p><b>Hull + 2 a 4</b>: Hull 50 subindo, 2 a 4 candles de baixa, 1 de alta; compra no fechamento dele
      (venda e o espelho). E a regra que passou no teste fora da amostra do estudo <code>hull_contra</code>
      ({n(D['base']['n_h'])} sinais). <b>Hull + pavios</b>: o mesmo com 2 a 3 candles e o pavio do lado do
      fechamento ate 10% do corpo ({n(D['base']['n_cand'])} sinais).</p>
      <p>Mesma engine, cada sinal resolvido isoladamente, stop 100, quatro gestoes, zerando no fim do pregao.</p>
    </div>
    <div class="card">
      <h3>Os osciladores</h3>
      <p><b>MACD</b>: EMA 12 &minus; EMA 26 do fechamento, sinal EMA 9, histograma = linha &minus; sinal.
      <b>Estocastico lento</b>: %K rapido de 14, %K lento = media de 3, %D = media de 3 do %K lento.
      <b>IFR</b> 14 com suavizacao de Wilder. Leitura no fechamento do candle de sinal; na venda, espelhada
      (MACD com sinal trocado, 100 &minus; %K, 100 &minus; IFR).</p>
      <p style="margin-bottom:0"><b>O IFR no PI e outra coisa.</b> Todo fechamento anda exatamente 100 pontos,
      entao o IFR vira a <i>proporcao suavizada de candles de alta</i> &mdash; e por isso, com a Hull a favor,
      ele quase nunca sai da faixa de 40 a 70.</p>
    </div>
  </div>
  <div class="card rolo" style="margin-top:16px">
    <h3>As regras, e quanto de cada conjunto elas deixam passar</h3>
    <table><thead><tr><th></th><th>Oscilador</th><th>Regra (lida como compra)</th><th>Hull + 2 a 4</th>
      <th>Hull + pavios</th><th>Tipo</th></tr></thead><tbody>{lin}</tbody></table>
    <p class="nota">As 11 classicas foram fechadas antes de medir. As 5 por quintil foram acrescentadas depois
    de ver que as classicas quase nao disparam &mdash; olhando so a frequencia, nao o resultado. Limites (no
    Hull + 2 a 4): histograma/ATR &gt; {n(L['hist_atr'], 2)}; menor %K da retracao &lt; {n(L['k_min'], 1)};
    %K &minus; %D &gt; {n(L['kd'], 1)}; menor IFR da retracao &lt; {n(L['ifr_min'], 1)}; IFR &gt; {n(L['ifr'], 1)}.</p>
  </div>
  <div class="card" style="margin-top:16px">
    <h3>Os controles</h3>
    <ul class="enx" style="margin-bottom:0">
      <li><b>Permutacao</b>: o ganho da regra contra o ganho de subconjuntos embaralhados do mesmo tamanho.</li>
      <li><b>Tercos, lados e blocos</b> (antes de 06/08, janela original, depois).</li>
      <li><b>Busca</b>: {len(D['regras'])} regras &times; 2 sentidos (a regra ou o seu complemento). O melhor dos
      candidatos contra o melhor que a mesma busca acha com os resultados embaralhados (500 vezes).</li>
      <li><b>Escolha fora</b>: o filtro escolhido so no bloco &ldquo;antes&rdquo;, medido no resto; e o
      escolhido em T1+T2, medido em T3.</li>
      <li><b>Poder</b> e <b>vizinhanca de parametros</b> (MACD 8/17 e 19/39, estocastico 8 e 21, IFR 9 e 21).</li>
    </ul>
  </div>
</section>"""


def regras_sec(D, F):
    def ab(id_, itens, sel):
        return (f'<div class="abas" id="{id_}" style="margin-bottom:6px">' + ''.join(
            f'<button class="aba" data-v="{k}" aria-pressed="{str(k == sel).lower()}">{r}</button>'
            for k, r in itens) + '</div>')
    return f"""
<section id="regras">
  <h2>1. Cada regra, medida</h2>
  <p class="olho">Pts por sinal com a regra e sem ela, entrada no fechamento. As regras que aceitam menos
  de 20 sinais nao tem numero.</p>
  <div style="position:sticky;top:44px;z-index:20;background:var(--plano);padding:8px 0">
    {ab('abas_rc', [('cand', 'Hull + pavios'), ('h', 'Hull + 2 a 4')], 'cand')}
    {ab('abas_rg', [(g, D['rot_gestao'][g]) for g in GES], 'parcial')}
  </div>
  <div class="grade g2">
    <figure class="card"><h3>Ganho sobre o conjunto sem filtro</h3><div id="g_ganho"></div>
      <figcaption>pts por sinal; apagadas, as regras com menos de 5% ou mais de 95% dos sinais</figcaption></figure>
    <figure class="card"><h3>Com a regra, em cada terco</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--bronze)"></i>T1 ate {D['base']['c1']}</span>
      <span><i class="chave q" style="background:var(--prata)"></i>T2 ate {D['base']['c2']}</span>
      <span><i class="chave q" style="background:var(--ouro)"></i>T3</span></div>
      <div id="g_tercos"></div>
      <figcaption>sem filtro: <span id="tercos_base"></span></figcaption></figure>
  </div>
  <div class="card rolo" style="margin-top:16px"><table id="t_regras"></table>
    <p class="nota"><b>p</b>: permutacao bicaudal do ganho (teste isolado, sem correcao pela busca).
    <b>Pct</b>: percentil do EV da regra entre 4.000 subconjuntos sorteados do mesmo tamanho. <b>Antes</b>:
    06/03 a 05/08, com o valor do conjunto sem filtro entre parenteses.</p></div>
</section>"""


def quintis_sec(D, F):
    ab = ''.join(f'<button class="aba" data-v="{k}" aria-pressed="{str(k == "ifr").lower()}">{r}</button>'
                 for k, r in D['continuas'].items())
    return f"""
<section id="leituras">
  <h2>2. As leituras em faixas</h2>
  <p class="olho">Sem corte nenhum: cada leitura em quintis (20% dos sinais cada), para ver se ha ordem.
  Um filtro de verdade apareceria como uma escada, e nos tres tercos.</p>
  <div class="abas" id="abas_q" style="margin-bottom:6px">{ab}</div>
  <div class="abas" id="abas_qc">
    <button class="aba" data-v="cand" aria-pressed="true">Hull + pavios</button>
    <button class="aba" data-v="h" aria-pressed="false">Hull + 2 a 4</button></div>
  <p class="nota" id="q_lim"></p>
  <div class="grade g2">
    <figure class="card"><h3>Pts por sinal, por quintil</h3><div id="g_q"></div>
      <figcaption>1:3 com parcial, entrada no fechamento</figcaption></figure>
    <figure class="card"><h3>Em cada terco</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--bronze)"></i>T1</span>
      <span><i class="chave q" style="background:var(--prata)"></i>T2</span>
      <span><i class="chave q" style="background:var(--ouro)"></i>T3</span></div>
      <div id="g_q_t"></div></figure>
  </div>
</section>"""


def busca_sec(D, F):
    lin = ''
    for cj in ('cand', 'h'):
        for g in GES:
            b = D['busca'][f'{cj}|{g}']
            fo = b['fora']
            cel = ''
            for rot in ('antes -> original+depois', 'T1+T2 -> T3'):
                x = fo.get(rot)
                if not x:
                    cel += '<td>&ndash;</td>'
                    continue
                cel += (f"<td style='text-align:left'>{x['regra']}{'' if x['sentido'] > 0 else ' (nao)'}: "
                        f"<b class='{cls(x['ev_teste'] - x['ev_teste_base'])}'>{sn(x['ev_teste'], 1)}</b> "
                        f"<small style='color:var(--mudo)'>sem filtro {sn(x['ev_teste_base'], 1)}</small></td>")
            lin += (f"<tr><td>{D['conj'][cj].split(' (')[0]}</td><td style='text-align:left'>{D['rot_gestao'][g]}</td>"
                    f"<td>{b['regra']}{'' if b['sentido'] > 0 else ' (nao)'}</td><td>{sn(b['t'], 2)}</td>"
                    f"<td style='color:var(--mudo)'>{sn(b['ruido_mediana'], 2)}</td>"
                    f"<td style='color:var(--mudo)'>{sn(b['ruido_p95'], 2)}</td><td><b>{n(b['p_valor'], 2)}</b></td>"
                    f"{cel}<td>{sn(b['poder'][0]['min_ganho'], 1)}</td></tr>")
    return f"""
<section id="busca">
  <h2>3. A busca contra o ruido, e a escolha fora</h2>
  <p class="olho">Olhar {len(D['regras'])} regras nos dois sentidos, em dois conjuntos e quatro gestoes,
  garante que alguma vai parecer boa. Aqui a busca inteira foi repetida 500 vezes com os resultados
  embaralhados: o que ela acha la e sorte por construcao.</p>
  <div class="card rolo"><table>
    <thead><tr><th>Conjunto</th><th>Gestao</th><th>Melhor regra</th><th>t</th><th>t ruido<br><small>mediana</small></th>
      <th>t ruido<br><small>p95</small></th><th>p</th><th>Escolhida antes de 06/08,<br>medida depois</th>
      <th>Escolhida em T1+T2,<br>medida em T3</th><th>Detectavel<br><small>(mantem 50%)</small></th></tr></thead>
    <tbody>{lin}</tbody></table>
    <p class="nota">&ldquo;(nao)&rdquo; = o complemento da regra. <b>t</b>: estatistica t do ganho do subconjunto
    sobre o conjunto. Uma regra que valesse passaria do p95 do ruido; nenhuma passa da mediana com folga.</p></div>
  <figure class="card" style="margin-top:16px"><h3>Melhor t real x melhor t em ruido</h3>
    <div class="legenda"><span><i class="chave q" style="background:var(--ouro)"></i>real</span>
    <span><i class="chave q" style="background:var(--bronze)"></i>ruido, mediana</span>
    <span><i class="chave q" style="background:var(--critico)"></i>ruido, p95</span></div>
    <div id="g_busca"></div></figure>
</section>"""


def vizinhanca_sec(D, F):
    V = D['vizinhanca']
    fam = {'M': 'MACD', 'E': 'Estocastico lento', 'I': 'IFR'}
    blocos = ''
    for letra, nome in fam.items():
        regras = sorted({v['regra'] for v in V.values() if v['regra'][0] == letra})
        pars = []
        for v in V.values():
            if v['regra'][0] == letra and v['par'] not in pars:
                pars.append(v['par'])
        cab = ''.join(f"<th>{p_.strip('[]()').replace(', ', '/')}{' *' if any(V.get(f'{r}|{p_}', {}).get('padrao') for r in regras) else ''}</th>" for p_ in pars)
        lin = ''
        for r in regras:
            lin += f"<tr><td>{r}</td>" + ''.join(
                (lambda x: f"<td class='{cls(x['ganho'])}'>{sn(x['ganho'], 1)}<br><small style='color:var(--mudo)'>{n(x['n'])}</small></td>"
                 if x and x['ganho'] is not None else '<td>&ndash;</td>')(V.get(f'{r}|{p_}')) for p_ in pars) + '</tr>'
        blocos += f"""<div class="card rolo"><h3>{nome}</h3><table><thead><tr><th>Regra</th>{cab}</tr></thead>
          <tbody>{lin}</tbody></table></div>"""
    return f"""
<section id="vizinhanca">
  <h2>4. Vizinhanca dos parametros</h2>
  <p class="olho">Ganho de cada regra no Hull + pavios (1:3 com parcial) com o oscilador mais rapido e mais
  lento que o padrao (*). Nao e para escolher parametro: e para ver se o que aparece e plato ou pico.</p>
  <div class="grade g3">{blocos}</div>
  <p class="nota">Embaixo, sinais com a regra. As regras por quintil recalculam o quintil em cada parametro.</p>
</section>"""


def carteira_sec(D, F):
    op_regra = '<option value="base">Sem filtro</option>' + ''.join(
        f'<option value="{k}">{k} &middot; {v[1]}</option>' for k, v in D['regras'].items())
    return f"""
<section id="carteira">
  <h2>5. A carteira, uma posicao por vez</h2>
  <p class="olho">Qualquer regra sobre qualquer conjunto e gestao, como na mesa. As estatisticas, as curvas e o
  grafico trade a trade seguem os seletores.</p>
  <div style="position:sticky;top:44px;z-index:20;background:var(--plano);padding:8px 0">
    <div class="abas" id="abas_cc" style="margin-bottom:6px">
      <button class="aba" data-v="cand" aria-pressed="true">Hull + pavios</button>
      <button class="aba" data-v="h" aria-pressed="false">Hull + 2 a 4</button></div>
    <div class="abas" id="abas_cg" style="margin-bottom:6px">{''.join(
        f'<button class="aba" data-v="{g}" aria-pressed="{str(g == "parcial").lower()}">{D["rot_gestao"][g]}</button>' for g in GES)}</div>
    <select id="sel_regra" aria-label="Regra">{op_regra}</select>
  </div>
  <h3 style="margin-top:18px">Estatisticas no formato MetaTrader 5</h3>
  <div class="card rolo"><table id="t_mt5"></table>
    <p class="nota">Pontos do WINFUT, brutos; R$ para 1 contrato a R$ 0,20 por ponto. Monte Carlo: 4.000
    reamostragens dos trades com reposicao.</p></div>
  <h3 style="margin-top:28px">Evolucao do patrimonio</h3>
  <figure class="card"><div class="legenda" id="leg_eq"></div><div id="g_eq"></div>
    <figcaption>eixo no tempo, {D['base']['ini']} a {D['base']['fim']}</figcaption></figure>
  <h3 style="margin-top:28px">Distribuicoes</h3>
  <p class="nota" id="nota_dist"></p>
  <div class="grade g2">
    <figure class="card"><h3>Resultado por trade</h3><div id="g_pts"></div></figure>
    <figure class="card"><h3>Duracao</h3><div id="g_dur"></div><figcaption>minutos (a base tem hora so ate o minuto)</figcaption></figure>
    <figure class="card"><h3>MEP &mdash; maxima excursao positiva</h3><div id="g_mep"></div></figure>
    <figure class="card"><h3>MEN &mdash; maxima excursao negativa</h3><div id="g_men"></div></figure>
  </div>
</section>

<section id="kline">
  <h2>6. Trade a trade</h2>
  <p class="olho">Hull 50 no preco; MACD, estocastico lento e IFR embaixo. Faixa clara: os candles contra; faixa
  forte: o candle de sinal. Segue o conjunto e a regra escolhidos acima, na gestao 1:3 com parcial. Setas do
  teclado navegam.</p>
  <div id="kwrap">
    <div class="knav">
      <button id="kant">&larr; anterior</button><button id="kprox">proximo &rarr;</button>
      <button id="kganho">proximo ganho</button><button id="kperda">proxima perda</button>
      <select id="ksel"></select>
    </div>
    <div id="kchart" style="height:640px"></div>
    <div class="kinfo" id="kinfo"></div>
  </div>
</section>"""


def conclusao(D, F):
    R = F['R']; bc = F['busca']['cand|parcial']
    return f"""
<section id="conclusao">
  <h2>Conclusao</h2>
  <ul class="enx">
    <li><b>Nenhum oscilador melhora o Hull + pavios de forma demonstravel.</b> O melhor candidato da busca
    tem t = {sn(bc['t'], 2)}; a mesma busca em ruido acha {sn(bc['ruido_mediana'], 2)} na mediana.</li>
    <li><b>Os cortes classicos nao conversam com este padrao.</b> Cruzamento do estocastico, sobrevenda e
    sobrecompra quase nunca acontecem no candle que volta a favor da Hull depois de 2 a 4 candles contra:
    a retracao e curta demais para os osciladores chegarem aos extremos, e o estocastico lento ainda esta
    virando.</li>
    <li><b>O que aparece de consistente e pequeno, e e tendencia, nao oscilacao:</b> IFR alto mede um pouco
    melhor em todos os recortes ({sn(R['cand|parcial|I5']['ganho'], 1)} pts); MACD acima de zero, menos e so em
    parte ({sn(R['cand|parcial|M1']['ganho'], 1)}). E a mesma informacao que ja esta na Hull a favor e na distancia da Hull a EMA
    (<code>hull_contra.html</code>, secao 6), e fica abaixo do que {n(D['base']['dias'])} pregoes conseguem
    separar de sorte.</li>
    <li><b>Nao ha plano novo.</b> O plano provisorio do Hull continua sem oscilador. Se for testar um deles em
    simulador, o candidato menos ruim e o IFR no quintil mais alto (acima de {n(D['limites']['ifr'], 0)}),
    como hipotese, sem mexer no resto.</li>
  </ul>
  <p class="nota">Resultado bruto, um instrumento. Os osciladores foram calculados aqui e nao conferidos contra
  uma exportacao do Profit: a formula do padrao pode diferir em detalhe (semente das medias), o que muda pouco
  as leituras mas pode mudar sinais no limite de um corte.</p>
</section>
<footer>Gerado por <code>osciladores.py</code> e <code>relatorio_osciladores.py</code>.</footer>"""


# ======================================================================= JS
JS = r"""
const bt=document.getElementById('btema');
function temaAtual(){const t=document.documentElement.dataset.tema;
  if(t==='claro'||t==='escuro') return t;
  return matchMedia('(prefers-color-scheme: dark)').matches?'escuro':'claro';}
bt.addEventListener('click',()=>{
  document.documentElement.dataset.tema=temaAtual()==='escuro'?'claro':'escuro';
  desenhaTudo(); pintaKline();});
function grupoAbas(id,fn){
  const g=document.getElementById(id);
  g.addEventListener('click',ev=>{const b=ev.target.closest('.aba'); if(!b) return;
    g.querySelectorAll('.aba').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
    fn(b.dataset.v);});
}
function clsv(v){return v>0?'pos':(v<0?'neg':'');}
const REG=Object.keys(D.regras);

/* ------------------------------------------------ 1. regras */
let rC='cand', rG='parcial';
grupoAbas('abas_rc',v=>{rC=v; desenhaRegras();});
grupoAbas('abas_rg',v=>{rG=v; desenhaRegras();});
function desenhaRegras(){
  const L=REG.map(k=>Object.assign({k},D.regras_res[rC+'|'+rG+'|'+k]));
  const fq=D.freq[rC];
  barrasH('#g_ganho',L.filter(r=>r.ev!==null).map(r=>({nome:r.k+' '+D.regras[r.k][1],v:r.ganho,
    fraco:fq[r.k]<5||fq[r.k]>95,
    extra:`<span class="l">sinais</span> ${r.n} (${fmt(r.frac,0)}%) &middot; <span class="l">com</span> ${sinal(r.ev,1)} &middot; <span class="l">sem</span> ${sinal(r.ev_fora,1)} &middot; <span class="l">p</span> ${fmt(r.p_bi,3)}`})),
    {rotV:'ganho',casas:1,esq:230});
  const ok=L.filter(r=>r.ev!==null);
  grupos('#g_tercos',ok.map(r=>({nome:r.k,v:r.tercos})),['T1','T2','T3'],{cores:['bronze','prata','ouro'],esq:40,altBarra:30});
  const b0=ok[0]; document.getElementById('tercos_base').textContent=b0?b0.tercos_base.map(v=>sinal(v,1)).join(' / '):'';
  const cab='<thead><tr><th></th><th>Regra</th><th>Sinais</th><th>Com</th><th>Sem</th><th>Ganho</th><th>p</th>'+
    '<th>T1 / T2 / T3</th><th>Antes</th><th>Compra</th><th>Venda</th><th>Pct</th></tr></thead>';
  document.getElementById('t_regras').innerHTML=cab+'<tbody>'+L.map(r=>{
    if(r.ev===null) return `<tr><td><b>${r.k}</b></td><td style="text-align:left">${D.regras[r.k][1]}</td><td>${r.n} (${fmt(r.frac,0)}%)</td><td colspan="9" style="color:var(--mudo)">amostra pequena demais</td></tr>`;
    return `<tr><td><b>${r.k}</b></td><td style="text-align:left">${D.regras[r.k][1]}</td><td>${r.n} (${fmt(r.frac,0)}%)</td>`+
      `<td class="${clsv(r.ev)}">${sinal(r.ev,1)}</td><td>${sinal(r.ev_fora,1)}</td><td class="${clsv(r.ganho)}"><b>${sinal(r.ganho,1)}</b></td>`+
      `<td>${fmt(r.p_bi,3)}</td><td>${r.tercos.map(v=>sinal(v,0)).join(' / ')}</td>`+
      `<td>${sinal(r.blocos.antes,1)} <small style="color:var(--mudo)">(${sinal(r.blocos_base.antes,1)})</small></td>`+
      `<td>${sinal(r.compra,1)}</td><td>${sinal(r.venda,1)}</td><td>${r.sorteio_pct===null?'-':fmt(r.sorteio_pct,0)}</td></tr>`;
  }).join('')+'</tbody>';
}

/* ------------------------------------------------ 2. quintis */
let qM='ifr', qC='cand';
grupoAbas('abas_q',v=>{qM=v; desenhaQ();});
grupoAbas('abas_qc',v=>{qC=v; desenhaQ();});
function desenhaQ(){
  const Q=D.quintis[qC+'|'+qM];
  document.getElementById('q_lim').innerHTML='<b>'+D.continuas[qM]+'</b> &middot; limites dos quintis: '+Q.limites.map(v=>fmt(v,2)).join(' / ');
  barrasH('#g_q',Q.faixas.map(f=>({nome:f.faixa,v:f.ev,extra:'<span class="l">sinais</span> '+f.n})),{rotV:'por sinal',casas:1,esq:90});
  grupos('#g_q_t',Q.faixas.map(f=>({nome:f.faixa,v:f.tercos})),['T1','T2','T3'],{cores:['bronze','prata','ouro'],esq:90});
}

/* ------------------------------------------------ 3. busca */
function desenhaBusca(){
  const itens=[];
  ['cand','h'].forEach(c=>['parcial','puro','r2','r1'].forEach(g=>{const b=D.busca[c+'|'+g];
    itens.push({nome:(c==='cand'?'pavios':'2 a 4')+' '+D.rot_gestao[g],v:[b.t,b.ruido_mediana,b.ruido_p95]});}));
  grupos('#g_busca',itens,['real','ruido mediana','ruido p95'],{cores:['ouro','bronze','critico'],esq:170,altBarra:40});
}

/* ------------------------------------------------ 5. carteira */
let cC='cand', cG='parcial', cR='base';
grupoAbas('abas_cc',v=>{cC=v; desenhaCart(); trocaLista();});
grupoAbas('abas_cg',v=>{cG=v; desenhaCart();});
document.getElementById('sel_regra').addEventListener('change',e=>{cR=e.target.value; desenhaCart(); trocaLista();});
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
 ['Maior ganho / maior perda',s=>sinal(s.maior_ganho)+' / '+sinal(s.maior_perda),null],
 ['Ganho medio / perda media',s=>sinal(s.media_ganho,1)+' / '+sinal(s.media_perda,1),null],
 ['Maximo de ganhos / perdas seguidas',s=>fmt(s.max_seq_ganho)+' / '+fmt(s.max_seq_perda),null],
 ['Negociacoes por dia',s=>fmt(s.trades_dia,1),null],
 ['Duracao mediana',s=>fmt(s.dur_mediana/60,1)+' min',null],
 ['Saidas: alvo / stop / zero / fim do dia',s=>[s.alvos,s.stops,s.stops_zero,s.fins_dia+s.timeouts].map(x=>fmt(x)).join(' / '),null],
 ['Antes de 06/08: pts por trade',s=>s.blocos&&s.blocos.antes.n?sinal(s.blocos.antes.ev,1)+' ('+s.blocos.antes.n+')':'-',null],
 ['Janela 06/08 a 11/09: pts por trade',s=>s.blocos&&s.blocos.original.n?sinal(s.blocos.original.ev,1)+' ('+s.blocos.original.n+')':'-',null],
 ['Monte Carlo: chance de lucro',s=>s.mc&&s.mc.p_lucro!==undefined?fmt(s.mc.p_lucro,1)+'%':'-',null],
 ['Monte Carlo: rebaixamento p95',s=>s.mc&&s.mc.dd_p95!==undefined?fmt(s.mc.dd_p95)+' pts':'-',null],
];
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
function desenhaCart(){
  const sb=D.carteira[cC+'|'+cG+'|base'], sr=D.carteira[cC+'|'+cG+'|'+cR];
  const nomeR=cR==='base'?'Sem filtro':cR+' '+D.regras[cR][1];
  document.getElementById('t_mt5').innerHTML=`<thead><tr><th>Estatistica</th><th>${nomeR}</th><th>Sem filtro</th></tr></thead><tbody>`+
    MT5.map(r=>`<tr><td>${r[0]}</td>`+[sr,sb].map(s=>`<td class="${r[2]&&s.trades?clsv(s[r[2]]):''}">${s.trades?r[1](s):'-'}</td>`).join('')+'</tr>').join('')+'</tbody>';
  const ser=[{nome:'Sem filtro',cor:'bronze',dados:sb.equity,xs:sb.xs}];
  if(cR!=='base'&&sr.trades) ser.unshift({nome:cR,cor:'ouro',dados:sr.equity,xs:sr.xs,area:true});
  linhas('#g_eq',ser,{alt:320});
  document.getElementById('leg_eq').innerHTML=(cR!=='base'?'<span><i class="chave" style="background:var(--ouro)"></i>'+nomeR+'</span>':'')+
    '<span><i class="chave" style="background:var(--bronze)"></i>Sem filtro</span>';
  const temDist=!!sr.pts;
  document.getElementById('nota_dist').textContent=temDist?(nomeR+', '+D.rot_gestao[cG]+'.'):'As distribuicoes estao na gestao 1:3 com parcial.';
  const s=temDist?sr:D.carteira[cC+'|parcial|'+cR];
  colunas('#g_pts',histo(s.pts,50),{alt:230,rotula:true,rotV:'trades',un:'trades'});
  colunas('#g_mep',histo(s.mfe,50,'ganho'),{alt:230,rotula:true,rotV:'trades',un:'trades'});
  colunas('#g_men',histo(s.mae,25,'perda'),{alt:230,rotula:true,rotV:'trades',un:'trades'});
  colunas('#g_dur',duracao(s.dur_s),{alt:230,rotula:true,rotV:'trades',un:'trades'});
}

function desenhaTudo(){desenhaRegras(); desenhaQ(); desenhaBusca(); desenhaCart();}
addEventListener('resize',()=>{clearTimeout(window._rz);
  window._rz=setTimeout(()=>{desenhaTudo(); if(kchart) kchart.resize();},180);});

/* ================================================================ kline */
const SANS='system-ui,-apple-system,"Segoe UI",sans-serif';
function c_(k){return getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim();}
function alfa(hex,a){const h=hex.replace('#','').trim();
  const x=h.length===3?h.split('').map(y=>y+y).join(''):h; const i=parseInt(x,16);
  return 'rgba('+((i>>16)&255)+','+((i>>8)&255)+','+(i&255)+','+a+')';}
klinecharts.registerOverlay({name:'os-nivel',totalStep:2,lock:true,
  needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{const e=overlay.extendData,y=coordinates[0].y;
    return [{type:'line',ignoreEvent:true,attrs:{coordinates:[{x:0,y:y},{x:bounding.width,y:y}]},
      styles:{color:e.cor,size:1,style:e.cheia?'solid':'dashed',dashedValue:[4,4]}},
     {type:'text',ignoreEvent:true,attrs:{x:4,y:y-3,text:e.rot,align:'left',baseline:'bottom'},
      styles:{color:e.cor,size:10,family:SANS,weight:'600',backgroundColor:alfa(c_('card'),.78),
      paddingLeft:4,paddingRight:4,paddingTop:1,paddingBottom:1,borderRadius:3}}];}});
klinecharts.registerOverlay({name:'os-zona',totalStep:3,lock:true,
  needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{if(coordinates.length<2) return [];
    const a=Math.min(coordinates[0].x,coordinates[1].x), b=Math.max(coordinates[0].x,coordinates[1].x);
    const w=overlay.extendData.meia||0;
    return [{type:'rect',ignoreEvent:true,attrs:{x:a-w,y:0,width:Math.max(2,b-a+2*w),height:bounding.height},
      styles:{style:'fill',color:overlay.extendData.cor}}];}});
klinecharts.registerIndicator({name:'OS_HULL',shortName:'Hull 50',series:'price',precision:0,
  figures:[{key:'hma',title:'Hull 50: ',type:'line'}],calc:dl=>dl.map(k=>({hma:k.hma}))});
klinecharts.registerIndicator({name:'OS_MACD',shortName:'MACD 12 26 9',precision:1,
  figures:[{key:'macd',title:'MACD: ',type:'line'},{key:'sinal',title:'sinal: ',type:'line'},
    {key:'hist',title:'hist: ',type:'bar',baseValue:0,
     styles:({data})=>{const v=(data.current||{}).hist; return {style:'fill',color:alfa(v>=0?c_('ganho'):c_('perda'),.55)};}}],
  calc:dl=>dl.map(k=>({macd:k.macd,sinal:k.sinal,hist:k.hist}))});
klinecharts.registerIndicator({name:'OS_ESTOC',shortName:'Estoc. lento 14 3 3',precision:1,minValue:0,maxValue:100,
  figures:[{key:'k',title:'%K: ',type:'line'},{key:'d',title:'%D: ',type:'line'}],
  calc:dl=>dl.map(k=>({k:k.k,d:k.d}))});
klinecharts.registerIndicator({name:'OS_IFR',shortName:'IFR 14',precision:1,minValue:0,maxValue:100,
  figures:[{key:'ifr',title:'IFR: ',type:'line'}],calc:dl=>dl.map(k=>({ifr:k.ifr}))});

let kchart=null,kidx=0,KTR=[],KL=[];
const T0=Date.UTC(2000,0,1),TB=60000, MOT=['alvo','stop','zero a zero','tempo','fim do dia'];
function lk(cor){return {color:cor,size:1.5,smooth:false,style:'solid',dashedValue:[3,4]};}
function estilo(){const g=c_('grade'),m=c_('mudo'),card=c_('card'),up=c_('ganho'),dn=c_('perda');
  return {grid:{horizontal:{color:g},vertical:{color:g}},
    candle:{bar:{upColor:up,downColor:dn,noChangeColor:m,upBorderColor:up,downBorderColor:dn,
      noChangeBorderColor:m,upWickColor:up,downWickColor:dn,noChangeWickColor:m},
      priceMark:{last:{show:false}},
      tooltip:{showRule:'follow_cross',text:{color:c_('tinta'),family:SANS,size:11},
        rect:{color:alfa(card,.94),borderColor:c_('eixo')}}},
    indicator:{lines:[lk(c_('alerta')),lk(c_('prata')),lk(c_('bronze'))],
      tooltip:{showRule:'follow_cross',showName:true,showParams:false,text:{color:c_('tinta2'),family:SANS,size:11}}},
    xAxis:{axisLine:{color:c_('eixo')},tickLine:{color:c_('eixo')},tickText:{color:m,family:SANS,size:11}},
    yAxis:{axisLine:{color:c_('eixo')},tickLine:{color:c_('eixo')},tickText:{color:m,family:SANS,size:11}},
    separator:{color:c_('grade')},
    crosshair:{horizontal:{line:{color:m},text:{backgroundColor:c_('tinta2')}},
      vertical:{line:{color:m},text:{backgroundColor:c_('tinta2')}}}};}
function pintaKline(){if(!kchart) return; kchart.setStyles(estilo()); mostra_(kidx);}
function iniciaKline(){
  const C=D.candles,N=C.o.length;
  for(let i=0;i<N;i++) KL.push({timestamp:T0+i*TB,open:C.o[i],high:C.h[i],low:C.l[i],close:C.c[i],volume:0,
    hma:C.hma[i],macd:C.macd[i],sinal:C.sinal[i],hist:C.hist[i],k:C.k[i],d:C.d[i],ifr:C.ifr[i]});
  kchart=klinecharts.init('kchart',{styles:estilo(),customApi:{formatDate:(f,ts,fm,tipo)=>{
    const i=Math.round((ts-T0)/TB); const s=(i>=0&&i<N)?C.dt[i]:''; return tipo===2?s.slice(6):s;}}});
  kchart.setPriceVolumePrecision(0,0);
  kchart.createIndicator('OS_HULL',true,{id:'candle_pane'});
  kchart.createIndicator('OS_MACD',false,{id:'p_macd',height:110});
  kchart.createIndicator('OS_ESTOC',false,{id:'p_estoc',height:100});
  kchart.createIndicator('OS_IFR',false,{id:'p_ifr',height:100});
  kchart.applyNewData(KL,false,()=>mostra_(0));
}
function mostra_(i){
  if(!kchart||!KTR.length) return;
  kidx=Math.max(0,Math.min(KTR.length-1,i));
  const t=KTR[kidx], ti=t[0], ie=t[1], is=t[2], ld=t[3], ent=t[4], G=D.gestoes.parcial, nf=t[10];
  kchart.removeOverlay();
  const de=Math.max(0,ti-nf-25), ate=Math.min(KL.length-1,is+12), jan=Math.max(14,ate-de+1);
  const larg=(kchart.getSize('candle_pane','main')||{}).width||760;
  const esp=Math.max(1.2,Math.min(40,larg/jan)); kchart.setBarSpace(esp); kchart.scrollToDataIndex(ate+2);
  const meia=esp/2;
  kchart.createOverlay({name:'os-zona',lock:true,points:[{timestamp:KL[ti-nf].timestamp},{timestamp:KL[ti-1].timestamp}],
    extendData:{cor:alfa(c_('prata'),.12),meia:meia}});
  kchart.createOverlay({name:'os-zona',lock:true,points:[{timestamp:KL[ti].timestamp},{timestamp:KL[ti].timestamp}],
    extendData:{cor:alfa(c_('ouro'),.28),meia:meia}});
  kchart.createOverlay({name:'os-zona',lock:true,points:[{timestamp:KL[ie].timestamp},{timestamp:KL[is].timestamp}],
    extendData:{cor:alfa(t[6]>=0?c_('ganho'):c_('perda'),.07),meia:meia}});
  [{v:ent,rot:'entrada '+fmt(ent),cor:c_('tinta'),cheia:true},{v:ent-ld*G.stop,rot:'stop',cor:c_('perda'),cheia:true},
   {v:ent+ld*G.alvo,rot:'alvo +'+G.alvo,cor:c_('ganho'),cheia:true},{v:ent+ld*G.parcial_em,rot:'parcial +'+G.parcial_em,cor:c_('ganho'),cheia:false}]
    .forEach(L=>kchart.createOverlay({name:'os-nivel',lock:true,points:[{timestamp:KL[ie].timestamp,value:L.v}],extendData:L}));
  document.getElementById('ksel').value=String(kidx);
  const C=D.candles, esp_=v=>v===null?'-':fmt(ld>0?v:(100-v),0);
  document.getElementById('kinfo').innerHTML=
    `<span><b>#${kidx+1}</b> de ${KTR.length}</span><span>${C.dt[ti]}</span>`+
    `<span><b>${ld>0?'▲ compra':'▼ venda'}</b></span><span>${nf} candles contra &middot; pavio do fechamento ${fmt(t[11],0)}%</span>`+
    `<span>MACD ${fmt(C.macd[ti],0)} &middot; %K ${fmt(C.k[ti],0)} / %D ${fmt(C.d[ti],0)} &middot; IFR ${fmt(C.ifr[ti],0)}</span>`+
    `<span>entrada <b>${fmt(ent)}</b></span><span>saida <b>${fmt(t[5])}</b> (${MOT[t[9]]})</span>`+
    `<span>resultado <b class="${clsv(t[6])}">${sinal(t[6])} pts</b></span><span>MEP <b>${sinal(t[7])}</b> &middot; MEN <b>${sinal(t[8])}</b></span>`;
}
function trocaLista(){
  KTR=D.trades[cC+'|parcial|'+cR]||[];
  document.getElementById('ksel').innerHTML=KTR.map((t,i)=>
    `<option value="${i}">#${i+1} · ${D.candles.dt[t[0]]} · ${t[3]>0?'compra':'venda'} · ${sinal(t[6])} pts</option>`).join('');
  mostra_(0);
}
document.getElementById('ksel').addEventListener('change',e=>mostra_(+e.target.value));
document.getElementById('kant').addEventListener('click',()=>mostra_(kidx-1));
document.getElementById('kprox').addEventListener('click',()=>mostra_(kidx+1));
function busca(f){for(let k=kidx+1;k<KTR.length;k++) if(f(KTR[k])) return mostra_(k);
  for(let k=0;k<KTR.length;k++) if(f(KTR[k])) return mostra_(k);}
document.getElementById('kganho').addEventListener('click',()=>busca(t=>t[6]>0));
document.getElementById('kperda').addEventListener('click',()=>busca(t=>t[6]<0));
addEventListener('keydown',ev=>{if(['SELECT','BUTTON'].includes(ev.target.tagName)) return;
  if(ev.key==='ArrowLeft') mostra_(kidx-1); if(ev.key==='ArrowRight') mostra_(kidx+1);});

desenhaTudo();
KTR=D.trades['cand|parcial|base'];
document.getElementById('ksel').innerHTML=KTR.map((t,i)=>
  `<option value="${i}">#${i+1} · ${D.candles.dt[t[0]]} · ${t[3]>0?'compra':'venda'} · ${sinal(t[6])} pts</option>`).join('');
iniciaKline();
"""

HTML = r"""<!doctype html>
<html lang="pt-BR" data-tema="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Osciladores no Hull</title>
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

MENU = [('resposta', 'Resposta'), ('metodo', 'Metodo'), ('regras', 'Regras'), ('leituras', 'Faixas'),
        ('busca', 'Busca'), ('vizinhanca', 'Parametros'), ('carteira', 'Carteira'), ('kline', 'Trade a trade'),
        ('conclusao', 'Conclusao')]


# ======================================================================= MD
def markdown(D, F):
    B = D['base']; R = F['R']; bc = F['busca']['cand|parcial']
    L = ['# MACD, estocastico lento e IFR como filtro do Hull + pavios', '',
         f"WINFUT, grafico de 20 PI, {n(B['barras'])} candles, {B['dias']} pregoes ({B['ini']} a {B['fim']}). "
         'Resultado bruto. Graficos, curvas, MEP/MEN, duracao e trade a trade (com os tres osciladores) em '
         '`osciladores.html`.', '',
         f"**Osciladores** (padrao do Profit): MACD {'/'.join(map(str, D['parametros']['macd']))}, estocastico lento "
         f"{','.join(map(str, D['parametros']['estoc']))}, IFR {D['parametros']['ifr']}. Lidos no fechamento do candle de "
         'sinal; na venda, espelhados.', '',
         f"**Sinais**: Hull + 2 a 4 ({n(B['n_h'])}) e Hull + pavios -- 2 a 3 candles e pavio do fechamento ate 10% "
         f"({n(B['n_cand'])}).", '',
         '## Resposta curta: ' + ('nao' if not F['passou'] else 'um filtro passou no controle'), '',
         f"- Hull + pavios sem filtro: {md_sn(F['base_cand'], 1)} pts por sinal (1:3 com parcial).",
         f"- Busca ({len(D['regras'])} regras x 2 sentidos) contra resultados embaralhados: melhor t = "
         f"{md_sn(bc['t'], 2)}, ruido mediana {md_sn(bc['ruido_mediana'], 2)}, p95 {md_sn(bc['ruido_p95'], 2)}; "
         f"p = {md_n(bc['p_valor'], 2)}.",
         f"- {len(F['degeneradas'])} das {len(D['classicas'])} regras classicas ({', '.join(F['degeneradas'])}) aceitam menos "
         'de 5% ou mais de 95% dos sinais: depois de 2 a 4 candles contra, o estocastico lento ainda esta caindo e os '
         'osciladores quase nunca chegam aos extremos.',
         f"- IFR no quintil mais alto ({md_sn(R['cand|parcial|I5']['ganho'], 1)}) melhora nos tres tercos, nos dois "
         f"blocos e nos dois lados; MACD acima de zero ({md_sn(R['cand|parcial|M1']['ganho'], 1)}) so nos periodos fracos "
         f"e na compra. Os dois abaixo do detectavel ({md_sn(bc['poder'][0]['min_ganho'], 1)} pts) e sem passar na busca.",
         f"- Histograma do MACD subindo no sinal mede pior ({md_sn(R['cand|parcial|M3']['ganho'], 1)}, p = "
         f"{md_n(R['cand|parcial|M3']['p_bi'], 3)} isolado), sem passar na busca.",
         f"- %K abaixo de 20 na retracao: {md_sn(R['cand|parcial|E3']['ganho'], 1)} em {R['cand|parcial|E3']['n']} "
         'sinais, sem plato de parametro.',
         '- Nao ha plano novo; o plano provisorio do Hull continua sem oscilador.', '',
         '## 1. Cada regra (Hull + pavios, fechamento)', '']
    for g in GES:
        L += [f"**{D['rot_gestao'][g]}** (sem filtro: {md_sn(R[f'cand|{g}|M1']['base'], 1)})", '',
              '| | Regra | Sinais | Com | Sem | Ganho | p | T1 / T2 / T3 | Antes (sem filtro) | Compra | Venda | Pct |',
              '|:--|:--|--:|--:|--:|--:|--:|:--|--:|--:|--:|--:|']
        for k, v in D['regras'].items():
            r = R[f'cand|{g}|{k}']
            if r['ev'] is None:
                L.append(f"| {k} | {v[1]} | {r['n']} ({md_n(r['frac'])}%) | - | - | - | - | - | - | - | - | - |")
                continue
            L.append(f"| {k} | {v[1]} | {r['n']} ({md_n(r['frac'])}%) | {md_sn(r['ev'], 1)} | {md_sn(r['ev_fora'], 1)} | "
                     f"**{md_sn(r['ganho'], 1)}** | {md_n(r['p_bi'], 3)} | " + ' / '.join(md_sn(x, 0) for x in r['tercos'])
                     + f" | {md_sn(r['blocos']['antes'], 1)} ({md_sn(r['blocos_base']['antes'], 1)}) | {md_sn(r['compra'], 1)} | "
                     f"{md_sn(r['venda'], 1)} | {md_n(r['sorteio_pct']) if r['sorteio_pct'] is not None else '-'} |")
        L.append('')
    L += ['**Hull + 2 a 4, 1:3 com parcial**', '',
          '| | Sinais | Com | Ganho | p | T1 / T2 / T3 | Antes |', '|:--|--:|--:|--:|--:|:--|--:|']
    for k in D['regras']:
        r = R[f'h|parcial|{k}']
        if r['ev'] is None:
            continue
        L.append(f"| {k} | {r['n']} | {md_sn(r['ev'], 1)} | {md_sn(r['ganho'], 1)} | {md_n(r['p_bi'], 3)} | "
                 + ' / '.join(md_sn(x, 0) for x in r['tercos']) + f" | {md_sn(r['blocos']['antes'], 1)} |")
    L += ['', '## 2. As leituras em quintis (Hull + pavios, 1:3 com parcial)', '',
          '| Leitura | Limites | Q1 | Q2 | Q3 | Q4 | Q5 |', '|:--|:--|--:|--:|--:|--:|--:|']
    for col, rot in D['continuas'].items():
        q = D['quintis'][f'cand|{col}']
        L.append(f"| {rot} | " + ' / '.join(md_n(x, 2) for x in q['limites']) + ' | '
                 + ' | '.join(md_sn(f['ev'], 1) for f in q['faixas']) + ' |')
    L += ['', '## 3. Busca contra ruido e escolha fora', '',
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
            L.append(f"| {cj} | {D['rot_gestao'][g]} | {b['regra']}{'' if b['sentido'] > 0 else ' (nao)'} | {md_sn(b['t'], 2)} | "
                     f"{md_sn(b['ruido_mediana'], 2)} | {md_sn(b['ruido_p95'], 2)} | {md_n(b['p_valor'], 2)} | {cel[0]} | {cel[1]} |")
    L += ['', '## 4. Vizinhanca dos parametros (ganho, Hull + pavios, 1:3 com parcial)', '',
          '| Regra | Parametros | Sinais | Ganho |', '|:--|:--|--:|--:|']
    for v in D['vizinhanca'].values():
        L.append(f"| {v['regra']} | {v['par']}{' (padrao)' if v['padrao'] else ''} | {v['n']} | "
                 f"{md_sn(v['ganho'], 1) if v['ganho'] is not None else '-'} |")
    L += ['', '## 5. Carteira, uma posicao por vez (Hull + pavios)', '',
          '| Gestao | Regra | Trades | Pts | Pts/trade | Acerto | Fator | Rebaix. | Antes (pts/trade) | MC lucro |',
          '|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|']
    for g in GES:
        for k in ['base'] + list(D['regras']):
            s = D['carteira'][f'cand|{g}|{k}']
            if not s.get('trades') or s['trades'] < 20:
                continue
            L.append(f"| {D['rot_gestao'][g]} | {'sem filtro' if k == 'base' else k} | {md_n(s['trades'])} | "
                     f"{md_sn(s['lucro_liq'])} | {md_sn(s['exp_pts'], 1)} | {md_n(s['winrate'], 1)}% | "
                     f"{md_n(s['fator_lucro'], 2)} | {md_n(s['dd_max'])} | "
                     f"{md_sn(s['blocos']['antes']['ev'], 1) if s['blocos']['antes']['n'] else '-'} | "
                     f"{md_n(s['mc'].get('p_lucro'), 0)}% |")
    L += ['', '## Conclusao', '',
          '- **Nenhum oscilador melhora o Hull + pavios de forma demonstravel.**',
          '- **Os cortes classicos nao conversam com este padrao:** a retracao de 2 a 4 candles e curta demais para '
          'os osciladores chegarem aos extremos, e o estocastico lento ainda esta virando no candle de sinal.',
          '- **O que aparece de consistente e pequeno e e tendencia** (IFR alto; MACD acima de zero, menos) -- a mesma '
          'informacao que ja esta na Hull a favor.',
          f"- **Nao ha plano novo.** Candidato menos ruim para simulador, como hipotese: IFR acima de "
          f"{md_n(D['limites']['ifr'], 0)} no sinal.",
          '',
          '> Osciladores calculados aqui, nao conferidos contra exportacao do Profit. Resultado bruto, um instrumento.',
          '', 'Reproduzir: `python osciladores.py && python relatorio_osciladores.py`.', '']
    return '\n'.join(L)


# ===================================================================== main
def enxuga(D):
    """Tira do json o que o html nao usa, para o arquivo nao passar de 20 MB."""
    for k, s in D['carteira'].items():
        s.pop('dt', None)
        if 'equity' in s:
            s['equity'] = [round(v) for v in s['equity']]
        for campo in ('barras',):
            s.pop(campo, None)
    D['trades'] = {k: [t[:12] for t in v] for k, v in D['trades'].items() if '|parcial|' in k}
    return D


def main():
    with open(os.path.join(SAIDA, 'osciladores.json'), encoding='utf-8') as f:
        D = json.load(f)
    F = fatos(D)
    md = markdown(D, F)
    D = enxuga(D)
    D['gestoes'] = GESTOES_JS
    corpo = ''.join([capa(D, F), resposta(D, F), metodo(D, F), regras_sec(D, F), quintis_sec(D, F),
                     busca_sec(D, F), vizinhanca_sec(D, F), carteira_sec(D, F), conclusao(D, F)])
    with open(VENDOR_KC, encoding='utf-8') as f:
        kline = f.read()
    scripts = ('<script>' + kline + '</script>\n<script>const D=' +
               json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';</script>\n'
               '<script>' + molde.JS_KIT + '</script>\n<script>' + JS + '</script>')
    html = (HTML.replace('__CSS__', molde.CSS)
            .replace('__MENU__', ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU))
            .replace('__SCRIPTS__', scripts).replace('__CORPO__', corpo))
    with open(os.path.join(BASE, 'osciladores.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(BASE, 'OSCILADORES.md'), 'w', encoding='utf-8') as f:
        f.write(md)
    print(f'gravado: osciladores.html ({len(html) / 1e6:.1f} MB) e OSCILADORES.md')


if __name__ == '__main__':
    main()
