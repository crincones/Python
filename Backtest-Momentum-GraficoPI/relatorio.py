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
  &mdash; cinco vezes a base do primeiro estudo, que e o trecho final desta.</p>
  <div style="margin-top:18px">
    <span class="selo">Hull {P['hull']}</span>
    <span class="selo">EMA {P['ema']}</span>
    <span class="selo">Keltner {P['atr']} &plusmn; {n(P['desvio'], 1)} ATR</span>
    <span class="selo">stop {n(P['stop'])} &middot; alvo {n(P['alvo'])}</span>
    <span class="selo">parcial 50% em +{n(P['parcial_em'])}</span>
    <span class="selo">teste fora da amostra</span>
  </div>
</header>"""


def _bl(D, chave, bloco, campo='ev'):
    """Numero de um bloco do teste fora da amostra (sinais isolados)."""
    return D['oos']['blocos'][chave]['sinais'][bloco][campo]


def resumo(D):
    st = D['variantes'][D['escolhida']]['stats']
    base = D['variantes']['fecha|parcial|bronze']['stats']
    mc = D['monte_carlo'][D['escolhida']]
    O = D['oos']
    ou_a = O['blocos']['fecha|parcial|ouro']['sinais']
    pr_a = O['blocos']['fecha|parcial|prata']['sinais']
    br_a = O['blocos']['fecha|parcial|bronze']['sinais']
    an = O['antecipa']['parcial|prata']
    C = D.get('candidato', {}).get('gestoes', {}).get('parcial')
    custo_zero = next((c['custo'] for c in D['custos'] if c['ev'] <= 0), None)
    tiles = ''.join([
        tile('Ouro, na janela em que foi escolhido', sn(ou_a['original']['ev'], 1) + ' pts',
             f"por trade &middot; {n(ou_a['original']['n'])} sinais, 06/08 a 11/09",
             cls(ou_a['original']['ev'])),
        tile('Ouro, nos pregoes nunca vistos', sn(ou_a['fora']['ev'], 1) + ' pts',
             f"por trade &middot; {n(ou_a['fora']['n'])} sinais, t = {sn(ou_a['fora']['t'], 2)}",
             cls(ou_a['fora']['ev'])),
        tile('Ouro, base inteira', sn(st['exp_pts'], 1) + ' pts',
             f"{n(st['trades'])} trades &middot; fator {n(st['fator_lucro'], 2)} &middot; "
             f"rebaix. {n(st['dd_max'])}", cls(st['exp_pts'])),
        tile('Custo que zera o Ouro', (n(custo_zero) + ' pts') if custo_zero is not None else '&ndash;',
             'por operacao, ida e volta', 'perda'),
    ])
    cand = ''
    if C:
        b = C['busca_ampla']
        cand = f"""
        <li><b>Retracao profunda</b> (3+ candles, sem nenhum outro filtro) e o unico recorte
            que mede bem nos dois blocos: {sn(C['blocos']['antes']['ev'], 1)} antes e
            {sn(C['blocos']['original']['ev'], 1)} na janela original. Mas foi achado
            <i>olhando</i> esta base, e a mesma busca em dado embaralhado acha algo tao bom
            {n(b['p_valor'] * 100, 0)}% das vezes. <a href="#candidato">Hipotese, nao setup.</a></li>"""
    return f"""
<section id="resumo">
  <h2>O que a base de {D['auditoria']['dias']} pregoes mostrou</h2>
  <p class="olho">O estudo anterior mediu o padrao Ouro em +34 pontos por trade em 26
  pregoes (06/08 a 11/09; a mesma janela, na base nova, mede {sn(ou_a['original']['ev'], 1)}). A base nova comeca cinco meses antes, e
  esses meses <b>nunca foram vistos</b> quando os filtros foram escolhidos &mdash; sao o
  primeiro teste de verdade do setup. Nesse teste o Ouro mede
  <b>{sn(ou_a['fora']['ev'], 1)} pontos por trade</b>. O Prata, {sn(pr_a['fora']['ev'], 1)}; a
  regra-base do CLAUDE.md, {sn(br_a['fora']['ev'], 1)}. Os filtros que criaram o Ouro nao
  eram propriedade do padrao: eram propriedade de agosto e setembro.</p>
  <div class="grade g4">{tiles}</div>

  <div class="grade g3" style="margin-top:16px">
    <div class="card">
      <h3>O que caiu</h3>
      <ul class="enx">
        <li><b>O padrao Ouro e o Prata.</b> Positivos em agosto e setembro, negativos ou
            zerados de marco a julho. No periodo inteiro, o Ouro nao paga
            {n(custo_zero)} pontos de custo.</li>
        <li><b>O veto de exaustao</b> nao separa mais nada, e a faixa de pavio
            {n(D['parametros']['pavio_min'])}&ndash;{n(D['parametros']['pavio_max'])} mede quase
            igual ao pavio curto: so a ponta acima de {n(D['parametros']['pavio_max'])} continua
            ruim.</li>
        <li><b>O alvo de 300</b> deixou de ser topo local: com stop de 100, o 1:1 mede mais que
            o 1:3.</li>
      </ul>
    </div>
    <div class="card">
      <h3>O que se manteve</h3>
      <ul class="enx">
        <li><b>Hull 21 e o pior periodo</b> em qualquer EMA, como antes.</li>
        <li><b>Pavio grande a favor</b> (acima de 10% do range) continua ruim nos tres
            tercos.</li>
        <li><b>Fluxo e forca de tendencia</b> continuam sem passar no controle de busca &mdash;
            agora com poder para ver ganhos de ~{n(D['fluxo']['poder'][-1]['linhas'][0]['min_ganho'], 0)}
            pts, e nao mais de 40.</li>{cand}
      </ul>
    </div>
    <div class="card">
      <h3>O que nao da para afirmar</h3>
      <ul class="enx">
        <li><b>A entrada antecipada</b> mede {sn(an['ev_conv'], 1)} pts por sinal &mdash; mas
            em {n(an['ambiguos_pct'], 0)}% dos trades o resultado depende de em que ordem os
            precos passaram dentro do candle, e isso o OHLC nao tem. Com um caminho
            aleatorio vai a {sn(an['ev_aleat'], 1)}. <a href="#antecipada">Ver por que.</a></li>
        <li>Monte Carlo do Ouro: probabilidade de lucro <b>{n(mc['prob_lucro'], 1)}%</b>
            &mdash; com os trades todos, inclusive os de agosto e setembro.</li>
      </ul>
    </div>
  </div>
</section>"""


def fora_amostra(D):
    """O teste que a base nova permite: antes x janela original x depois."""
    O = D['oos']
    lin = ''
    for chave, rot in (('fecha|parcial|ouro', 'Ouro'), ('fecha|parcial|prata', 'Prata'),
                       ('fecha|parcial|bronze', 'Bronze (regra-base)'),
                       ('fecha|puro|ouro', 'Ouro, 1:3 sem parcial'), ('fecha|r2|ouro', 'Ouro, 1:2'),
                       ('meio_lim|parcial|prata', 'Prata, limitada no meio'),
                       ('antecipa|parcial|prata', 'Prata, antecipada*')):
        if chave not in O['blocos']:
            continue
        s = O['blocos'][chave]['sinais']
        cel = ''.join(
            f'<td class="{cls(s[k]["ev"])}">{sn(s[k]["ev"], 1)}<br><small style="color:var(--mudo)">'
            f'{n(s[k]["n"])} sinais &middot; t {sn(s[k]["t"], 1) if s[k]["t"] is not None else "&ndash;"}'
            f'</small></td>' for k in ('antes', 'original', 'depois'))
        lin += f'<tr><td>{rot}</td>{cel}<td class="{cls(s["total"]["ev"])}"><b>{sn(s["total"]["ev"], 1)}</b></td></tr>'
    reg = ''.join(f'<tr><td>{r["mes"][5:]}/{r["mes"][:4]}</td><td>{r["dias"]}</td>'
                  f'<td>{n(r["abre"])}</td><td>{n(r["fecha"])}</td>'
                  f'<td class="{cls(r["var"])}">{sn(r["var"])}</td>'
                  f'<td>{n(r["maxima"] - r["minima"])}</td></tr>' for r in O['regime'])
    ff = O['filtros_fora']
    pav = ' &middot; '.join(f"{r['faixa']}: <b class=\"{cls(r['ev'])}\">{sn(r['ev'], 1)}</b>" for r in ff['pavio'])
    ret = ' &middot; '.join(f"{r['faixa']}: <b class=\"{cls(r['ev'])}\">{sn(r['ev'], 1)}</b>" for r in ff['retracao_candles'])
    cz = {(c['concava'], c['esticado']): c for c in O['cruz_fora']}
    vet = cz[(True, True)]; resto = [c for k, c in cz.items() if k != (True, True)]
    ev_resto = sum(c['ev'] * c['n'] for c in resto) / sum(c['n'] for c in resto)
    return f"""
<section id="oos">
  <h2>Fora da amostra: o teste que faltava</h2>
  <p class="olho">Todos os cortes deste setup &mdash; o veto de exaustao em
  {n(D['parametros']['estic_exaustao'], 2)} ATR, a retracao de {D['parametros']['n_ret_min']}+ candles,
  o pavio de {n(D['parametros']['pavio_min'])} a {n(D['parametros']['pavio_max'])} pontos &mdash;
  foram escolhidos na base antiga, de 06/08 a 11/09. A base nova vai de
  {D['auditoria']['de'][8:]}/{D['auditoria']['de'][5:7]} a
  {D['auditoria']['ate'][8:]}/{D['auditoria']['ate'][5:7]} e a contem inteira. Entao ela se divide
  em tres blocos, e so os das pontas sao teste.</p>

  <div class="card rolo">
    <table>
      <thead><tr><th>Variante</th><th>Antes<br><small>06/03 a 05/08 &middot; nunca vista</small></th>
        <th>Janela original<br><small>06/08 a 11/09 &middot; onde as regras nasceram</small></th>
        <th>Depois<br><small>12/09 em diante</small></th><th>Base inteira</th></tr></thead>
      <tbody>{lin}</tbody>
    </table>
    <p class="nota">Valor esperado por sinal, em pontos, cada sinal resolvido isoladamente;
    <b>t</b> e a estatistica t da media (acima de 2 em modulo, dificil de ser acaso). Na janela
    original os numeros batem com os do estudo anterior (a base e a mesma, a menos de 25 candles
    que a exportacao antiga tinha em ordem trocada). O bloco &ldquo;depois&rdquo; tem um pregao so.
    * A antecipada tem uma ressalva propria, <a href="#antecipada">abaixo</a>.</p>
  </div>

  <div class="card" style="margin-top:16px">
    <h3>Mes a mes</h3>
    <div class="legenda">
      <span><i class="chave q" style="background:var(--ouro)"></i>Ouro</span>
      <span><i class="chave q" style="background:var(--prata)"></i>Prata</span>
      <span><i class="chave q" style="background:var(--bronze)"></i>Bronze</span>
    </div>
    <figure><div id="oos_meses"></div>
      <figcaption>Valor esperado por sinal em cada mes, entrada no fechamento, 1:3 com parcial.
      Agosto e setembro sao os dois meses em que o Ouro passa de +20 &mdash; e sao
      exatamente os meses da base antiga.</figcaption></figure>
  </div>

  <div class="grade g2" style="margin-top:16px">
    <div class="card">
      <h3>O mercado em cada mes</h3>
      <div class="rolo"><table>
        <thead><tr><th>Mes</th><th>Pregoes</th><th>Abertura</th><th>Fechamento</th>
          <th>Variacao</th><th>Amplitude</th></tr></thead>
        <tbody>{reg}</tbody></table></div>
      <p class="nota">Pontos do WINFUT. A base antiga era um trecho so de um mercado; a nova
      tem mes de alta, de queda forte (maio) e de variacao quase nula no fechamento.</p>
    </div>
    <div class="card">
      <h3>Os filtros do Ouro, medidos so fora da janela original</h3>
      <p style="color:var(--tinta2)"><b>Pavio do candle de continuacao</b> &mdash; {pav}.</p>
      <p style="color:var(--tinta2)"><b>Candles de retracao</b> &mdash; {ret}.</p>
      <p style="color:var(--tinta2);margin-bottom:0"><b>Veto de exaustao</b> &mdash; os sinais
      vetados medem <b class="{cls(vet['ev'])}">{sn(vet['ev'], 1)}</b> ({n(vet['n'])}); os que ficam,
      <b class="{cls(ev_resto)}">{sn(ev_resto, 1)}</b>.</p>
      <p class="nota">Pontos por sinal, regra-base inteira, entrada no fechamento com parcial,
      so os pregoes fora de 06/08 a 11/09.</p>
    </div>
  </div>
</section>"""


def antecipada(D):
    A = D['oos']['antecipa']
    lin = ''.join(
        f"<tr><td>{D['rotulo'][k.split('|')[1]]}</td><td>{ROT_GESTAO[k.split('|')[0]]}</td>"
        f"<td>{n(r['n'])}</td><td>{n(r['ambiguos_pct'], 1)}%</td>"
        f"<td class=\"{cls(r['ev_conv'])}\">{sn(r['ev_conv'], 1)}</td>"
        f"<td class=\"{cls(r['ev_aleat'])}\"><b>{sn(r['ev_aleat'], 1)}</b></td>"
        f"<td class=\"{cls(r['ev_pess'])}\">{sn(r['ev_pess'], 1)}</td></tr>" for k, r in A.items())
    a = A['parcial|prata']
    return f"""
<section id="antecipada">
  <h2>A entrada antecipada nao pode ser medida com OHLC</h2>
  <p class="olho">Na base nova, a ordem stop no meio do corpo, colocada no fechamento da
  retracao, e a unica variante que mede bem nos dois blocos. Antes de levar isso a serio e
  preciso olhar de onde vem o numero.</p>
  <div class="bandeira">
    <h3>O problema</h3>
    <p>A ordem dispara 50 pontos a favor, dentro do candle seguinte. Se esse candle fecha a
    favor mas tem um pavio contra de mais de 50 pontos, ha dois caminhos possiveis: o pavio veio
    <b>antes</b> do disparo (o trade sobrevive) ou <b>depois</b> (o trade toma stop na propria
    barra). O OHLC nao diz qual. A engine usa a convencao &ldquo;o pavio contra se forma
    antes&rdquo;, que e conservadora para quem entra no fechamento &mdash; mas para quem entra
    no meio do candle ela e a leitura <b>otimista</b>: nenhum desses trades toma stop.</p>
    <p style="margin-bottom:0">Isso acontece em <b>{n(a['ambiguos_pct'], 0)}%</b> dos trades.
    Um passeio aleatorio de ticks, condicionado ao candle fechar a favor com um pavio dessa
    profundidade, dispara a ordem antes do pavio em 28% a 40% das vezes.</p>
  </div>
  <div class="card rolo" style="margin-top:16px">
    <table>
      <thead><tr><th>Nivel</th><th>Gestao</th><th>Sinais</th><th>Ambiguos</th>
        <th>Convencao da engine</th><th>Caminho aleatorio</th><th>Todo ambiguo toma stop</th></tr></thead>
      <tbody>{lin}</tbody>
    </table>
    <p class="nota">Pontos por sinal, base inteira. A resposta verdadeira esta entre as duas
    ultimas colunas, e o cenario neutro fica perto de zero. Para decidir e preciso o tempo e
    negocio de cada preco dentro do candle (tick a tick, ou um grafico de 1 PI), que esta base
    nao tem. Ate la, a antecipada nao e evidencia de nada.</p>
  </div>
</section>"""


def candidato(D):
    C = D.get('candidato')
    if not C:
        return ''
    G = C['gestoes']; g = G['parcial']; s = g['stats']; b = g['busca']; ba = g['busca_ampla']
    lin = ''
    for gn in ('parcial', 'puro', 'r2', 'r1'):
        x = G[gn]; st = x['stats']; bl = x['blocos']
        lin += (f"<tr><td>{C['rot_gestao'][gn]}</td><td>{n(st['trades'])}</td>"
                f"<td class=\"{cls(st['lucro_liq'])}\">{sn(st['lucro_liq'])}</td>"
                f"<td class=\"{cls(st['exp_pts'])}\">{sn(st['exp_pts'], 1)}</td>"
                f"<td>{n(st['winrate'], 1)}%</td><td>{n(st['fator_lucro'], 2)}</td>"
                f"<td>{n(st['dd_max'])}</td>"
                f"<td class=\"{cls(bl['antes']['ev'])}\">{sn(bl['antes']['ev'], 1)}</td>"
                f"<td class=\"{cls(bl['original']['ev'])}\">{sn(bl['original']['ev'], 1)}</td>"
                f"<td>{n(x['mc'].get('prob_lucro'), 1)}%</td>"
                f"<td class=\"{cls(x['custos'][2]['ev'])}\">{sn(x['custos'][2]['ev'], 1)}</td></tr>")
    nr = ''.join(f"<tr><td>{r['faixa']}</td><td>{n(r['n'])}</td><td class=\"{cls(r['ev'])}\">"
                 f"{sn(r['ev'], 1)}</td><td>{sn(r['t'], 2) if r['t'] is not None else '&ndash;'}</td></tr>"
                 for r in g['n_ret'])
    cortes = ''.join(f"<tr><td>{r['rotulo']}</td><td>{n(r['n'])}</td><td class=\"{cls(r['ev'])}\">"
                     f"{sn(r['ev'], 1)}</td><td>{sn(r['t'], 2)}</td></tr>" for r in b['cortes'])
    m = ba['melhor']
    return f"""
<section id="candidato">
  <h2>Uma hipotese: a retracao profunda</h2>
  <p class="olho">O CLAUDE.md pede para avaliar se o tamanho da retracao serve de filtro. Na base
  de {D['auditoria']['dias']} pregoes, ele e o unico atributo da regra-base que mede bem nos tres
  tercos, nos dois blocos e nos dois lados. Retracao de 1 ou 2 candles nao paga; de 3 ou mais,
  paga. O recorte <b>Bronze + retracao de {C['n_ret_min']}+ candles</b>, sem nenhum outro filtro, faz
  {n(s['trades'])} operacoes, {sn(s['lucro_liq'])} pontos, {sn(s['exp_pts'], 1)} por trade.</p>

  <div class="grade g4">
    {tile('Por trade', sn(s['exp_pts'], 1) + ' pts', f"{n(s['trades'])} trades &middot; {n(s['trades_dia'], 1)} por dia com sinal", cls(s['exp_pts']))}
    {tile('Antes / janela original', sn(g['blocos']['antes']['ev'], 1) + ' / ' + sn(g['blocos']['original']['ev'], 1), 'pts por sinal')}
    {tile('Tercos', ' / '.join(sn(x['ev'], 0) for x in g['tercos']), 'pts por sinal')}
    {tile('Fator de lucro', n(s['fator_lucro'], 2), f"rebaixamento {n(s['dd_max'])} pts")}
  </div>

  <div class="bandeira">
    <h3>Por que isto e hipotese e nao setup</h3>
    <p>O corte de 3 candles foi escolhido <b>depois</b> de ver a tabela da retracao nesta mesma
    base. Dois controles medem o quanto disso pode ser a busca:</p>
    <ul class="enx" style="margin-bottom:0">
      <li><b>So entre cortes de retracao</b> (2+, 3+, 4+ candles; mais de 1,0, 1,5 ou 2,0 ATR): o
      melhor mede t = {sn(b['melhor']['t'], 2)}; em {b['perms']} embaralhamentos a mesma busca acha
      t = {sn(b['ruido_mediana'], 2)} na mediana. p = {n(b['p_valor'], 3)}. Passa.</li>
      <li><b>Entre todas as tabelas de filtro que foram olhadas</b> ({ba['atributos']} atributos,
      {ba['cortes']} cortes): o melhor continua sendo a retracao ({m['col']} {m['sentido']} {n(m['thr'], 1)},
      t = {sn(m['t'], 2)}), mas o ruido acha t = {sn(ba['ruido_mediana'], 2)} na mediana e
      {sn(ba['ruido_p95'], 2)} no percentil 95. p = {n(ba['p_valor'], 2)}. <b>Nao passa.</b></li>
    </ul>
  </div>

  <div class="card rolo" style="margin-top:16px">
    <h3>Nas quatro gestoes</h3>
    <table>
      <thead><tr><th>Gestao</th><th>Trades</th><th>Pontos</th><th>Por trade</th><th>Acerto</th>
        <th>Fator</th><th>Rebaix.</th><th>Antes</th><th>Original</th><th>MC lucro</th>
        <th>Com 5 pts de custo</th></tr></thead>
      <tbody>{lin}</tbody>
    </table>
    <p class="nota">Carteira de uma posicao por vez (os sinais quase nunca se sobrepoem).
    Antes/Original: pontos por sinal nos dois blocos.</p>
  </div>

  <div class="grade g2" style="margin-top:16px">
    <div class="card"><h3>Candles de retracao, regra-base</h3>
      <div class="rolo"><table><thead><tr><th>Retracao</th><th>Sinais</th><th>EV</th><th>t</th></tr></thead>
      <tbody>{nr}</tbody></table></div>
      <p class="nota">Com 4 candles o EV e alto, mas sao poucos sinais; o grosso do candidato sao
      os de 3 candles, que sozinhos medem t = {sn(g['n_ret'][2]['t'], 2)}.</p></div>
    <div class="card"><h3>Mes a mes do candidato</h3>
      <figure><div id="cand_meses"></div>
        <figcaption>Pontos por sinal, 1:3 com parcial.</figcaption></figure></div>
  </div>
  <div class="card rolo" style="margin-top:16px"><h3>Os cortes de tamanho de retracao</h3>
    <table><thead><tr><th>Corte</th><th>Sinais</th><th>EV</th><th>t</th></tr></thead>
    <tbody>{cortes}</tbody></table></div>
  <p class="nota">O que falta para virar setup: medir de novo em pregoes posteriores a
  {D['auditoria']['ate'][8:]}/{D['auditoria']['ate'][5:7]}, sem mexer em nada. O plano
  (<b>plano.html</b>) traz esse protocolo. No grafico trade a trade, o botao
  &ldquo;{D['rotulo'].get('r3', 'Retracao 3+')}&rdquo; navega as operacoes do candidato.</p>
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
          f"menor {n(a['corpo_min'])}, maior {n(a['corpo_max'])}")}
    {tile('Abre no fechamento anterior', n(a['abre_no_fecha_pct'], 2) + '%',
          'o resto e virada de dia')}
    {tile('ATR 21 mediano', n(a['atr_mediana']) + ' pts',
          f"range mediano {n(a['range_mediano'])} pts")}
  </div>
  <div class="card" style="margin-top:16px">
    <h3>A base e os indicadores</h3>
    <p>A base e <code>WINFUT/WINFUT_20PI_Robo.csv</code>: o log do robo
    <code>LogCandles_Console.ntsl</code>, um candle por linha, na ordem do proprio Profit
    (<i>CurrentBar</i>). Ela contem a base antiga (<code>WINFUT_20PI.csv</code>) inteira: nos
    10.000 candles em comum o OHLC e identico, a menos de 25 candles que a exportacao antiga
    listava em ordem trocada por terem o mesmo carimbo de milissegundo. Duas diferencas de
    formato: a hora vem so ate o minuto (entao a duracao dos trades tem resolucao de minuto), e
    nao ha a coluna de EMA da Nelogica.</p>
    <p style="margin-bottom:0">Por isso a EMA 21 nao e conferida aqui &mdash; a formula e a
    mesma que foi conferida na base antiga contra a coluna da Nelogica (erro maximo de 0,004
    ponto). A semente e a media aritmetica dos 21 primeiros fechamentos. A Hull e
    WMA(2&times;WMA(25) &minus; WMA(50), 7) e o canal de Keltner e a EMA 21 &plusmn; 2 ATR(21)
    exponencial, com a EMA do canal sendo <b>a mesma</b> media de tendencia, como pede o
    CLAUDE.md.</p>
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

  <h3 style="margin-top:36px">O veto de exaustao</h3>
  <p class="olho">O CLAUDE.md desconfiava: <i>"quando a HULL se encontra perto da
  banda superior, indica exaustao"</i>. Na base antiga o que separava era a
  <b>combinacao</b> de uma Hull abrindo a curva a favor do trade com um preco que ja se
  afastou da EMA 21, e esse foi o veto que criou o Prata. Na base de
  {D['auditoria']['dias']} pregoes ele marca {n(D['estudos']['extra']['n_veto'])} dos
  {n(D['n_sinais']['confirmados'])} sinais, e a tabela abaixo mostra o que sobrou dele.</p>
  <div class="card rolo">
    <table>
      <thead><tr><th></th>
        <th>preco perto da EMA<br><small>ate {n(P['estic_exaustao'], 2)} ATR</small></th>
        <th>preco esticado da EMA<br><small>mais de {n(P['estic_exaustao'], 2)} ATR</small></th>
      </tr></thead>
      <tbody>{linhas_cz}</tbody>
    </table>
    <p class="nota">Valor esperado por trade, no conjunto sem filtro nenhum, base inteira.
    A celula de baixo a direita e o que o veto joga fora. Na base antiga ela media
    &minus;1,5 contra +8 a +27 das outras; agora a diferenca e de poucos pontos, e nao no
    sentido de um veto.</p>
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
             'fecha|parcial|r3', 'meio_lim|parcial|prata', 'antecipa|parcial|prata']
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
      <figcaption>Entrada no fechamento, com parcial. Repare onde as curvas sobem: quase
      tudo o que os tres niveis ganham vem de agosto e setembro.</figcaption></figure>
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
        <figcaption>Nivel Ouro, entrada no fechamento.</figcaption></figure>
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
  <p class="olho">O perfil e o de um alvo distante: erra a maioria das vezes e vive das
  poucas que acerta. Com alvo em {n(D['parametros']['alvo'])}, stop em
  {n(D['parametros']['stop'])} e a parcial, o empate fica perto de 25% de acerto; o Ouro
  acerta {n(s['winrate'], 1)}% na base inteira.</p>
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
     'O CLAUDE.md pede a Hull "preferivelmente concava". Na base antiga ela media ao '
     'contrario do pedido. Na base de 6 meses as duas metades medem quase igual, e nenhuma '
     'e positiva nos tres tercos: a concavidade, sozinha, nao carrega informacao.'),
    ('esticamento', 'A distancia do preco a EMA 21',
     'Na base antiga, entrar com o preco colado na EMA media muito melhor. Agora as '
     'faixas nao guardam ordem, e o terco que paga e sempre o ultimo.'),
    ('pavio', 'A geometria do candle que retoma &mdash; o pavio',
     'Como o corpo e sempre 100 pontos, o pavio total <b>e</b> a forma do candle. O que '
     'sobrevive da ideia do Ouro e so a ponta de cima: pavio acima de 90 pontos continua '
     'ruim. O miolo de 25 a 90 ja nao se destaca do pavio curto.'),
    ('pavio_favor', 'O pavio a favor do movimento',
     'Um pavio grande alem do fechamento significa que o movimento foi e voltou. Acima '
     'de 10% do range o sinal perde nos tres tercos. A base antiga ja apontava isso '
     '(acima de 6% deixava de pagar); a nova confirma com mais forca.'),
    ('pavio_contra', 'O pavio contra o movimento',
     'O candle de continuacao com pouco pavio contra mede melhor, mas o efeito some no '
     'ultimo terco. Nao e filtro.'),
    ('retracao_candles', 'O tamanho da retracao, em candles',
     'O achado mais forte da base nova: retracao de 1 ou 2 candles nao paga nada; de 3, '
     'paga nos tres tercos; de 4, paga muito, com pouca amostra. O corte de 2 candles do '
     'Prata estava no lugar errado. Ver a secao <a href="#candidato">Uma hipotese</a>.'),
    ('retracao_tamanho', 'O tamanho da retracao, em ATRs',
     'A mesma ideia medida em profundidade. A faixa acima de 2 ATR paga nos tres tercos; '
     'o meio nao tem ordem. Diz o mesmo que a contagem de candles.'),
    ('inclinacao_hull', 'A inclinacao da Hull',
     'Hull muito inclinada (acima de 0,16 ATR por candle) mede mal nos dois primeiros '
     'tercos; o resto nao tem ordem. Indicio de exaustao, sem estabilidade para virar regra.'),
    ('inclinacao_ema', 'A inclinacao da EMA 21',
     'O CLAUDE.md pede para avaliar. As faixas nao seguem ordem e mudam de sinal de terco '
     'para terco. E, como na base antiga, a inclinacao da EMA e quase a mesma variavel que '
     'o esticamento do preco (correlacao {corr}). Nao e filtro.'),
    ('banda_keltner', 'A distancia da Hull a banda de Keltner',
     'A leitura literal &mdash; "Hull perto da banda indica exaustao" &mdash; nao aparece '
     'tambem na base nova: nenhuma faixa se destaca e nenhuma e estavel.'),
    ('hull_colada', 'Ha quanto tempo a Hull esta colada na EMA',
     'A outra intuicao do CLAUDE.md &mdash; "quando a hull passa muito tempo perto da EMA '
     '21 e sinal de consolidacao". Na base antiga, mais de 8 candles colada era o pior '
     'balde; na nova, esse balde muda de sinal de terco para terco. Nao se confirma.'),
    ('hora', 'O horario',
     'A hora antes da abertura do mercado a vista (9h-10h) e o fim do dia (depois das '
     '15h) medem negativo nos dois primeiros tercos; das 10h as 12h, positivo. E o desenho '
     'esperado para um padrao de continuacao, mas a diferenca e pequena e o 1&ordm; terco '
     'perde tambem das 10h as 11h. Anotado, nao aplicado.'),
]


def filtros(D):
    blocos = ''
    for chave, titulo, texto in BLOCOS_FILTRO:
        if chave not in D['estudos']:
            continue
        texto = texto.replace('{corr}', n(D['estudos']['extra']['corr_ema_estic'], 2))
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
  {n(D['n_sinais']['confirmados'])} sinais da regra-base, entrada no fechamento, com
  parcial, nos {D['auditoria']['dias']} pregoes. Ao lado de cada faixa vai o mesmo numero
  quebrado em tercos do periodo (cada terco tem ~{D['auditoria']['dias'] // 3} pregoes, mais
  que a base antiga inteira). Faixa que so paga num terco nao e filtro, e sorte.</p>
  <div class="bandeira">
    <h3>Os tercos, desta vez, contam uma historia</h3>
    <p style="margin-bottom:0">Na regra-base o 3&ordm; terco mede
    {sn(D['niveis_terco'][2]['por_terco'][2]['ev'], 1)} pts por sinal, contra
    {sn(D['niveis_terco'][2]['por_terco'][0]['ev'], 1)} e
    {sn(D['niveis_terco'][2]['por_terco'][1]['ev'], 1)} nos dois primeiros. Nao e o filtro: e o
    periodo. Por isso uma faixa que so fica boa no 3&ordm; terco nao diz nada &mdash; e foi
    exatamente num pedaco desse terco que os filtros do Ouro foram escolhidos.</p>
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
  <p class="olho">A grade abaixo roda o nivel Ouro inteiro em
  {len(D['grade']['stops']) * len(D['grade']['alvos'])} combinacoes de stop e alvo. O
  quadro com contorno e o do CLAUDE.md. Na base antiga ele era um topo local; na base de
  {D['auditoria']['dias']} pregoes a grade inteira fica perto de zero, e o que mede
  melhor e o alvo <b>curto</b> &mdash; {n(D['grade']['alvos'][0])} pontos &mdash; que so
  compensa com acerto alto. Nenhuma celula paga custo com folga.</p>
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
      <p class="nota">Com a parcial o Ouro termina em {sn(o['lucro_liq'])} pts e rebaixamento
      de {n(o['dd_max'])}; sem ela, {sn(pu['lucro_liq'])} e {n(pu['dd_max'])}. Nesta base a
      parcial nao troca lucro por conforto: melhora os dois, porque o alvo de 300 e alcancado
      poucas vezes fora de agosto e setembro.</p>
    </div>
    <div class="card">
      <h3>Periodos de media</h3>
      <p style="color:var(--tinta2)">A EMA e sempre a linha do meio do Keltner, como
      manda o CLAUDE.md &mdash; entao ela e o ATR andam juntos. Na base antiga a Hull 50
      ganhava em todas as EMAs. Na nova, nenhuma combinacao passa de
      {sn(max(m['ev_ouro'] for m in D['medias']), 1)} pts por trade no Ouro, e a unica
      regularidade que sobra e a <b>Hull 21 ser a pior</b> em qualquer EMA. Trocar o periodo
      nao salva o setup.</p>
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
    <p class="nota">Nivel Ouro, sem parcial. Com stop de {n(P['stop'])}: 1:1
    {sn(linha100[0]['ev'], 1)}, 1:2 {sn(linha100[1]['ev'], 1)}, 1:3 {sn(linha100[2]['ev'], 1)},
    1:4 {sn(linha100[3]['ev'], 1)} pts por operacao. Na base antiga o 1:3 era o topo da linha
    por larga margem; agora nenhuma razao risco:retorno transforma o Ouro num setup.</p>
  </div>

  <h3 style="margin-top:34px">As tres gestoes, na carteira</h3>
  <div class="card rolo">
    <table>
      <thead><tr><th>Gestao</th><th>Pontos</th><th>Por trade</th><th>Acerto</th>
        <th>Fator</th><th>Rebaix.</th><th>Recup.</th><th>Por risco</th></tr></thead>
      <tbody>{comp}</tbody>
    </table>
    <p class="nota">Nivel Ouro, entrada no fechamento. O 1:2 termina com
    {sn(o2['lucro_liq'])} pts contra {sn(o3['lucro_liq'])} do 1:3 puro (rebaixamento
    {n(o2['dd_max'])} contra {n(o3['dd_max'])}); acerto de {n(o2['winrate'], 1)}% contra
    {n(o3['winrate'], 1)}%.
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
      <li>{sum(1 for l in D['rr'] for c in l if c['ev'] < 0)} das
      {sum(len(l) for l in D['rr'])} celulas sao negativas. Na base antiga, nenhuma era.</li>
      <li>O melhor resultado por ponto de risco e {n(max(c['ev_risco'] for l in D['rr'] for c in l), 2)}
      &mdash; menos de 5 centesimos de ponto por ponto arriscado, antes do custo.</li>
      <li>Stops largos (250 e 300) medem negativo em todas as razoes.</li>
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
    a mesma informacao). Esse pedaco ja foi medido na secao de filtros. O que restava
    testar era o esforco em <b>volume</b>. As variaveis de numero de negocios
    ({', '.join(x['rotulo'] for x in EFR.get('ausentes', []))}) ficam de fora: a base do robo
    nao traz negocios, e o volume dela ja e o agressor.</p>
  </div>

  <div class="grade g2" style="gap:22px;margin-top:16px">
    <div class="card">
      <h3>Isto e informacao nova?</h3>
      <div class="rolo"><table>
        <thead><tr><th>Variavel</th><th>corr. pavio</th><th>corr. volume</th>
          <th>corr. duracao</th><th></th></tr></thead>
        <tbody>{nov}</tbody></table></div>
      <p class="nota">&ldquo;Esforco do par&rdquo; e sempre <b>continuacao dividida
      pela retracao</b>: acima de 1, andar a favor saiu mais caro que andar contra. Ele e
      ortogonal a tudo que a estrategia ja usa. Ja &ldquo;volume da continuacao&rdquo; e
      literalmente <code>vol_cont</code> (correlacao 1,00), e as outras duas replicam
      volume ou duracao.</p>
    </div>
    <div class="card">
      <h3>A pergunta que decide a historia</h3>
      <div class="rolo"><table>
        <thead><tr><th>Faixa de esforco do par</th><th>Sinais</th><th>EV</th></tr></thead>
        <tbody>{qt}</tbody></table></div>
      <p class="nota">Se menos esforco fosse melhor, o quintil de <b>menor</b> esforco
      seria o maior. Ele mede {sn(q1['ev'], 1)}, contra {sn(EFR['base_ouro'], 1)} da base do
      Ouro. O desenho e de U invertido &mdash; os quintis do meio medem melhor e as duas
      pontas medem mal &mdash;, que nao e a historia de Wyckoff e que, sem ter sido previsto,
      nao vale como filtro.</p>
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
      <p class="nota">Na base antiga este corte parecia o achado mais bonito da
      investigacao de fluxo. Na nova da {sn(EFR['cortes'][1]['ganho'], 1)} pontos no Ouro,
      com p = {n(EFR['cortes'][1]['p_valor'], 2)}; um filtro que mantem {n(pwe['frac'], 0)}% dos
      sinais precisaria de {sn(pwe['min_ganho'], 0)} pontos para aparecer. E ele continua
      <b>dependendo da gestao</b>: no 1:2 o ganho vai a {sn(EFR['cortes'][-1]['ganho'], 1)}.
      Era um balde sortudo, e a base maior confirmou.</p>
    </div>
  </div>"""

    o = pen['ouro']
    return f"""
<section id="fluxo">
  <h2>Agressao, tempo de barra e forca de tendencia</h2>
  <p class="olho">A base do robo traz, por candle, o volume agressor comprador e vendedor e
  a duracao da barra. Nao traz o volume total nem o numero de negocios: aqui o
  &ldquo;volume&rdquo; e o volume <b>agressor</b> (compra + venda), que na base antiga tinha
  correlacao de 0,995 com o volume total. Num grafico de PI a duracao e a unica medida de
  <i>pressa</i>: como todo corpo vale 100 pontos, 100/duracao compara barra com barra. A
  mediana e {n(B['dur_mediana'])}&nbsp;s e o quartil de cima {n(B['dur_p75'])}&nbsp;s.
  <b>Nenhum atributo de fluxo passa no controle de busca</b>, agora com 5 vezes mais
  sinais.</p>

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
    {sn(o['ruido_p90'], 2)} no percentil 90. Nos tres niveis o achado real fica abaixo da
    mediana do ruido (p de {n(min(r['p_valor'] for r in F['peneira']), 2)} a
    {n(max(r['p_valor'] for r in F['peneira']), 2)}).</p>
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
    <p class="nota">As duas ultimas colunas: o corte foi escolhido usando <b>so</b> os dois
    primeiros tercos e aplicado ao terceiro, que ele nunca viu. No Bronze e no Ouro ele piora
    o terceiro terco; no Prata melhora, com {n(pen['prata']['fora']['n_t3'])} sinais &mdash; e
    com um atributo diferente do escolhido no periodo inteiro. Nao ha um atributo que se
    repita.</p>
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
    <p class="nota">Nenhuma hipotese tem p abaixo de 0,05, e todas tem o 1&ordm; terco
    negativo &mdash; o que e o Ouro inteiro, nao a hipotese. A que chega mais perto e
    &ldquo;a favor da deriva de 50 barras&rdquo;, com poucos sinais. Vale lembrar que a
    regra-base <b>ja</b> exige a Hull 50 no sentido do trade: boa parte do filtro de
    tendencia ja esta dentro dela.</p>
  </div>

  <div class="card" style="margin-top:16px">
    <h3>O que esta base conseguiria enxergar</h3>
    <div class="rolo"><table>
      <thead><tr><th>Nivel</th><th>Sinais</th><th>Desvio<br><small>por trade</small></th>
        <th>Filtro que mantem 50%</th><th>mantem 33%</th><th>mantem 25%</th></tr></thead>
      <tbody>{pw}</tbody></table></div>
    <p class="nota">Menor ganho de valor esperado, em pontos por trade, que esta amostra
    distingue de zero com 80% de poder a 5%. Na base antiga, no Ouro, passava de 40 pontos.
    Agora um filtro que mantenha metade do Bronze apareceria a partir de
    {sn(F['poder'][0]['linhas'][0]['min_ganho'], 0)} pontos. <b>Com essa lente, o
    &ldquo;nao&rdquo; ja nao e so falta de amostra:</b> se o fluxo acrescentasse 10 pontos
    por trade a regra-base, esta base veria.</p>
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
  <p class="olho">A base de {D['auditoria']['dias']} pregoes ja respondeu a pergunta mais
  importante &mdash; o Ouro nao se sustenta fora da janela em que foi escolhido (ver
  <a href="#oos">Fora da amostra</a>). O que segue e o resto da bateria de robustez, com o
  periodo inteiro.</p>

  <div class="grade g2">
    <div class="card">
      <h3>Os tres niveis, terco a terco</h3>
      <div class="rolo"><table>
        <thead><tr><th>Nivel</th><th>1&ordm; terco</th><th>2&ordm; terco</th>
          <th>3&ordm; terco</th><th>Periodo</th></tr></thead>
        <tbody>{linhas}</tbody></table></div>
      <p class="nota">Valor esperado por trade, em pontos. Os tres niveis perdem nos dois
      primeiros tercos e ganham no ultimo. O Ouro, que na base antiga era o mais parelho,
      e agora o que mais oscila.</p>
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
      <li><b>Duracao com resolucao de minuto.</b> A base do robo nao tem segundos: a
      duracao dos trades curtos sai arredondada.</li>
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
    b_niv = grupo('nivel', [(k, D['rotulo'][k]) for k in ('ouro', 'prata', 'bronze', 'r3')
                            if k in D['rotulo']], esc[2])
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
    ou = D['oos']['blocos']['fecha|parcial|ouro']['sinais']
    C = D.get('candidato', {}).get('gestoes', {}).get('parcial')
    cand = ''
    if C:
        cand = f"""
        <li><b>Nao ha setup para operar agora.</b> O que existe e uma hipotese &mdash; a
        retracao profunda, {sn(C['stats']['exp_pts'], 1)} pts por trade em
        {n(C['stats']['trades'])} operacoes &mdash; que precisa ser medida em pregoes que ainda
        nao aconteceram. O plano.html virou o protocolo desse teste.</li>"""
    return f"""
<section id="conclusao">
  <h2>Conclusao</h2>
  <p class="olho">O setup Ouro nao sobreviveu a base maior. Com 26 pregoes ele media
  +34 pontos por trade; nos {n(ou['fora']['n'])} sinais que nao participaram da escolha dos
  filtros, mede {sn(ou['fora']['ev'], 1)}. Na base inteira, {sn(s['exp_pts'], 1)} por trade,
  que nao paga custo. Os tres filtros que o criaram &mdash; veto de exaustao, retracao de
  2+ candles, pavio de {n(P['pavio_min'])} a {n(P['pavio_max'])} &mdash; descreviam agosto e
  setembro de 2026, nao o padrao.</p>

  <div class="grade g2">
    <div class="card">
      <h3>O que a base maior ensinou</h3>
      <ul class="enx" style="margin-bottom:0">
        <li><b>Tercos dentro de 26 pregoes nao eram robustez.</b> Os tres tercos da base
        antiga eram tres pedacos do mesmo mes e meio de mercado.</li>
        <li><b>Fora da amostra e o unico teste que conta.</b> Todo filtro escolhido olhando
        os dados precisa ser medido em dados que nao foram olhados.</li>
        <li><b>A regra-base do CLAUDE.md, sem filtros, fica perto de zero</b>
        ({sn(D['variantes']['fecha|parcial|bronze']['stats']['exp_pts'], 1)} pts por trade) na
        base inteira.</li>
        <li><b>A entrada antecipada so parece boa por uma convencao de caminho</b> que o OHLC
        nao consegue confirmar.</li>
      </ul>
    </div>
    <div class="card">
      <h3>O que fazer com isso</h3>
      <ul class="enx" style="margin-bottom:0">
        <li><b>Nao operar o Ouro nem o Prata</b>, e nao ligar o robo
        <code>Robo-NTSL/MomentumPI_OuroPrata_Robo.ntsl</code> em conta real.</li>{cand}
        <li>Para decidir a entrada antecipada, exportar uma base com o caminho dentro do
        candle (tick a tick ou grafico de 1 PI) &mdash; sem ela a pergunta nao tem resposta.</li>
        <li>O estudo <code>hull_contra.html</code> (Hull a favor + retracao de 2 a 4 candles
        contra ela) tambem foi refeito nesta base e e o unico cuja hipotese previa passou no
        teste fora da amostra.</li>
      </ul>
    </div>
  </div>
</section>

<footer>
  <p>Backteste gerado a partir de <code>WINFUT/WINFUT_20PI_Robo.csv</code>
  ({n(D['auditoria']['candles'])} candles, {D['auditoria']['dias']} pregoes).
  Resultados em pontos do WINFUT, brutos, com um contrato. Rodar de novo:
  <code>python rodar.py &amp;&amp; python candidato.py &amp;&amp; python relatorio.py</code>.</p>
  <p>Backteste nao e promessa. Este relatorio e a demonstracao disso: o mesmo setup que
  media +34 pontos por trade em 26 pregoes mede perto de zero em
  {D['auditoria']['dias']}.</p>
</footer>"""


JS_OOS = r"""
/* ----------------------------------------------- fora da amostra e candidato */
function desenhaOOS(){
  if(!D.oos) return;
  const M=D.oos.meses, ks=['ouro','prata','bronze'].map(n=>'fecha|parcial|'+n);
  const meses=M[ks[0]].map(m=>m.mes);
  grupos('#oos_meses',meses.map((mes,i)=>({nome:mes.slice(5)+'/'+mes.slice(2,4),
    v:ks.map(k=>{const r=M[k].find(x=>x.mes===mes); return r?r.ev:null;}),
    n:ks.map(k=>{const r=M[k].find(x=>x.mes===mes); return r?r.n:0;})})),
    ['Ouro','Prata','Bronze'],{cores:['ouro','prata','bronze'],altBarra:40,esq:60});
  if(D.candidato&&document.querySelector('#cand_meses')){
    const g=D.candidato.gestoes.parcial;
    barrasH('#cand_meses',g.meses.map(m=>({nome:m.mes.slice(5)+'/'+m.mes.slice(2,4),v:m.ev,
      cor:m.ev>=0?'ganho':'perda',
      extra:'<span class="l">sinais</span> '+m.n+' &middot; <span class="l">acerto</span> '+fmt(m.wr,1)+'%'})),
      {altBarra:26,esq:60});
  }
}
desenhaOOS();
document.getElementById('btema').addEventListener('click',()=>desenhaOOS());
addEventListener('resize',()=>{clearTimeout(window._rzo);window._rzo=setTimeout(desenhaOOS,200);});
"""


SECOES = [
    ('resumo', 'Resumo'), ('oos', 'Fora da amostra'), ('base', 'A base'), ('padrao', 'O padrao'),
    ('galeria', 'Galeria'), ('estatisticas', 'Estatisticas'),
    ('patrimonio', 'Patrimonio'),
    ('distribuicao', 'Distribuicao'), ('duracao', 'Duracao'),
    ('filtros', 'Filtros'), ('gestao', 'Stop e alvo'),
    ('rr', 'Risco : retorno'), ('fluxo', 'Agressao e tendencia'),
    ('antecipada', 'Antecipada'), ('candidato', 'Hipotese'),
    ('robustez', 'Robustez'), ('trades', 'Trade a trade'),
    ('conclusao', 'Conclusao'),
]


def monta(D):
    corpo = (capa(D) + resumo(D) + fora_amostra(D) + base_dados(D) + padrao(D) + galeria(D)
             + estatisticas(D) + patrimonio(D) + distribuicao(D) + filtros(D)
             + gestao(D) + risco_retorno(D) + fluxo_sec(D)
             + antecipada(D) + candidato(D)
             + robustez(D) + trades(D)
             + conclusao(D))
    menu = ''.join(f'<li><a href="#{i}">{r}</a></li>' for i, r in SECOES)
    pag = (molde.HTML
           .replace('{{titulo}}', 'Momentum no grafico PI &middot; backtest WINFUT')
           .replace('{{menu}}', menu)
           .replace('{{corpo}}', corpo)
           .replace('__CSS__', molde.CSS)
           .replace('__KIT__', molde.JS_KIT)
           .replace('__PAG__', molde.JS_PAG + JS_OOS)
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
