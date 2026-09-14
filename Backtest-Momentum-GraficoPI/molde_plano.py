# -*- coding: utf-8 -*-
"""
O molde do plano operacional: plano.html e PLANO.md.

Reaproveita o CSS do relatorio (molde.CSS) e acrescenta so o que e do
plano: os cartoes de passo, a regua de gestao e a folha de checagem.
"""
import json

import molde

CSS_EXTRA = r"""
.passo{display:grid; grid-template-columns:44px 1fr; gap:16px; align-items:start;
  background:var(--card); border:1px solid var(--borda); border-radius:12px;
  padding:18px 20px; box-shadow:var(--sombra); margin-bottom:12px}
.passo .n{width:34px; height:34px; border-radius:50%; display:grid; place-items:center;
  background:var(--prata); color:var(--card); font-weight:680; font-size:15px}
.passo.veto .n{background:var(--critico)}
.passo h3{font-size:17px; margin-bottom:6px}
.passo .regra{margin:0 0 10px}
.passo .por{font-size:13.5px; color:var(--tinta2); border-left:2px solid var(--grade);
  padding-left:12px; margin:0 0 8px}
.passo .nao{font-size:13px; color:var(--critico); font-weight:600; margin:0}
.passo.veto{border-left:3px solid var(--critico)}

.regua{display:grid; grid-template-columns:1fr; gap:0; background:var(--card);
  border:1px solid var(--borda); border-radius:12px; overflow:hidden;
  box-shadow:var(--sombra)}
.regua .faixa{display:grid; grid-template-columns:120px 1fr; gap:14px;
  padding:14px 18px; border-bottom:1px solid var(--grade); align-items:baseline}
.regua .faixa:last-child{border-bottom:none}
.regua .vlr{font-weight:680; font-size:18px; letter-spacing:-.02em}

.lista-chk{list-style:none; padding:0; margin:0}
.lista-chk li{display:grid; grid-template-columns:22px 1fr; gap:10px;
  padding:9px 0; border-bottom:1px solid var(--grade); align-items:start}
.lista-chk li:last-child{border-bottom:none}
.lista-chk .cx{width:16px; height:16px; border:1.5px solid var(--eixo);
  border-radius:4px; margin-top:3px}
.lista-chk .cx.x{border-color:var(--critico)}

@media print{
  body{background:#fff}
  .card,.passo,.regua{box-shadow:none; break-inside:avoid}
  section{padding-top:24px}
}
"""

HTML = r"""<!doctype html>
<html lang="pt-BR" data-tema="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plano de trading &middot; momentum no grafico PI</title>
<style>__CSS__</style>
</head>
<body>
<nav class="indice"><div class="wrap"><ul>__MENU__</ul></div></nav>
<div class="wrap">
__CORPO__
</div>
<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>
<script>const D=__DADOS__;</script>
<script>__KIT__</script>
<script>
function desenha(){
  (D.galeria_ex||[]).forEach((ex,k)=>miniPadrao('#gal_'+k,ex));
}
desenha();
addEventListener('resize',()=>{clearTimeout(window._rz);
  window._rz=setTimeout(desenha,180);});
const bt=document.getElementById('btema');
function temaAtual(){const t=document.documentElement.dataset.tema;
  if(t==='claro'||t==='escuro') return t;
  return matchMedia('(prefers-color-scheme: dark)').matches?'escuro':'claro';}
bt.addEventListener('click',()=>{
  document.documentElement.dataset.tema = temaAtual()==='escuro'?'claro':'escuro';
  desenha();});
</script>
</body>
</html>
"""

SECOES = [('setup', 'O setup'), ('gatilhos', 'Os 6 passos'),
          ('niveis', 'Ouro, Prata, Bronze'), ('gestao', 'Gestao'),
          ('regras', 'Regras de mesa'), ('galeria', 'Como se parece'),
          ('checklist', 'Folha de checagem')]


def monta_html(c):
    D, P, s, n, sn = c['D'], c['P'], c['s'], c['n'], c['sn']
    pu = D['variantes']['fecha|puro|ouro']['stats']
    r2 = dict(D['variantes']['fecha|r2|ouro']['stats'])
    r2['alvo_pts'] = D['gestoes']['r2']['alvo']

    passos = ''
    for g in c['gatilhos']:
        passos += f"""
  <div class="passo{' veto' if g.get('veto') else ''}">
    <div class="n">{'&times;' if g.get('veto') else g['num']}</div>
    <div>
      <h3>{g['titulo']}</h3>
      <p class="regra">{g['regra']}</p>
      <p class="por">{g['porque']}</p>
      <p class="nao">Nao vale se: {g['veta']}</p>
    </div>
  </div>"""

    linhas_niv = ''
    for x in c['niveis']:
        linhas_niv += (
            f'<tr><td><span class="tag"><span class="pt" '
            f'style="background:var(--{x["nivel"]})"></span>{x["rot"]}</span></td>'
            f'<td style="text-align:left">{x["passos"]}</td>'
            f'<td>{sn(x["ev"], 1)} pts</td><td>{n(x["wr"], 1)}%</td>'
            f'<td>{n(x["dia"], 1)}</td><td>{n(x["dd"])} pts</td>'
            f'<td style="text-align:left"><b>{x["acao"]}</b></td></tr>')

    chk = [
        ('Hull 50 no sentido do trade e atras do preco', False),
        ('Retracao de 2 ou mais candles', False),
        ('Os dois extremos do par fora da Hull', False),
        ('EMA 21 entre os topos e os fundos do par', False),
        ('NAO e exaustao (Hull acelerando + preco esticado)', True),
        (f"Pavio total do candle entre {n(P['pavio_min'])} e "
         f"{n(P['pavio_max'])} pontos", False),
        ('Stop de 100 pontos ja posicionado ANTES de entrar', False),
        ('Nao ha posicao aberta neste momento', False),
    ]
    itens = ''.join(f'<li><span class="cx{" x" if x else ""}"></span>'
                    f'<span>{t}</span></li>' for t, x in chk)

    cartoes_gal = ''
    for k, ex in enumerate(c['galeria']['exemplos']):
        res = ('empatou' if abs(ex['pts']) < 1e-9
               else ('ganhou' if ex['pts'] > 0 else 'perdeu'))
        cor = '' if abs(ex['pts']) < 1e-9 else ('pos' if ex['pts'] > 0 else 'neg')
        cartoes_gal += f"""
      <figure class="ex">
        <div class="ex-topo">
          <span class="ex-data">{ex['data']} &middot;
            {'compra' if ex['lado'] > 0 else 'venda'}</span>
          <span class="ex-res {cor}">{sn(ex['pts'])} pts</span>
        </div>
        <div id="gal_{k}" class="ex-viz"></div>
        <figcaption>Retracao de {ex['n_ret']} candle{'s' if ex['n_ret'] > 1 else ''},
          pavio de {n(ex['pav_tot'])} pts. Saiu no {ex['rot_saida']} &mdash;
          {res}.</figcaption>
      </figure>"""

    corpo = f"""
<header class="capa">
  <div class="chapeu">Plano de trading &middot; WINFUT &middot; grafico de 20 PI</div>
  <h1>Momentum de continuacao</h1>
  <p class="sub">Seis perguntas de sim ou nao, na ordem em que se olha para a tela.
  Se qualquer uma der nao, o trade nao existe &mdash; nao ha "quase".</p>
  <div style="margin-top:18px">
    <span class="selo">Hull {P['hull']}</span>
    <span class="selo">EMA {P['ema']}</span>
    <span class="selo">Keltner {P['atr']} &plusmn; {n(P['desvio'], 1)} ATR</span>
    <span class="selo">stop {n(P['stop'])}</span>
    <span class="selo">alvo {n(P['alvo'])}</span>
    <span class="selo">parcial 50% em +{n(P['parcial_em'])}</span>
  </div>
  <div class="bandeira" style="margin-top:24px">
    <h3>Leia isto antes</h3>
    <p style="margin-bottom:0">Este plano sai de um backteste de
    <b>{D['auditoria']['dias']} pregoes</b> &mdash; pouco mais de um mes, todo ele em
    mercado de alta. Os numeros sao <b>brutos</b>, sem corretagem e sem slippage.
    Rode em simulador por pelo menos um mes antes de qualquer dinheiro real, e refaca
    a medicao quando houver base maior. Ver <code>RESULTADOS.md</code> para o que o
    teste nao mediu.</p>
  </div>
</header>

<section id="setup">
  <h2>O setup</h2>
  <p class="olho">No grafico de <b>20 PI</b> do WINFUT, todo candle fecha exatamente
  100 pontos acima ou abaixo da sua abertura. O que se procura e uma <b>retracao</b>
  contra a tendencia seguida de um candle de <b>continuacao</b> a favor, com a Hull 50
  atras do preco e a EMA 21 cortando o par. A venda e o espelho exato da compra.</p>
  <div class="grade g4">
    <div class="tile"><div class="rot">Por operacao</div>
      <div class="num pos">{sn(s['exp_pts'], 1)} pts</div>
      <div class="pe">R$ {sn(s['exp_rs'], 2)} com 1 contrato</div></div>
    <div class="tile"><div class="rot">Acerto</div>
      <div class="num">{n(s['winrate'], 1)}%</div>
      <div class="pe">alvo de 300 com stop de 100</div></div>
    <div class="tile"><div class="rot">Frequencia</div>
      <div class="num">{n(s['trades_dia'], 1)}</div>
      <div class="pe">operacoes por pregao</div></div>
    <div class="tile"><div class="rot">Rebaixamento maximo</div>
      <div class="num">{n(s['dd_max'])} pts</div>
      <div class="pe">R$ {n(s['dd_max_rs'])} &middot; a pior sequencia medida</div></div>
  </div>
  <p class="nota">Padrao Ouro, entrada no fechamento, com parcial. Medido em
  {s['trades']} operacoes ao longo de {s['dias']} pregoes.</p>
</section>

<section id="gatilhos">
  <h2>Os seis passos</h2>
  <p class="olho">Na ordem. O passo 5 e o unico <b>veto</b>: ele nao aprova nada,
  so reprova &mdash; e e o que mais separa trade bom de trade ruim.</p>
  {passos}
</section>

<section id="niveis">
  <h2>Ouro, Prata e Bronze</h2>
  <p class="olho">Quando um passo falha, o sinal nao vira lixo automaticamente: ele
  cai de nivel. A tabela diz o que fazer com cada um.</p>
  <div class="card rolo">
    <table>
      <thead><tr><th>Nivel</th><th>Passos que cumpre</th><th>Por operacao</th>
        <th>Acerto</th><th>Por dia</th><th>Rebaix.</th><th>O que fazer</th></tr></thead>
      <tbody>{linhas_niv}</tbody>
    </table>
    <p class="nota">"Por operacao" e o valor esperado medido no backteste, em pontos.
    O Bronze aparece na tabela para que fique claro <b>quanto</b> se perde operando
    tudo: quatro vezes mais trades para ganhar o mesmo, com o dobro do rebaixamento
    &mdash; e isso antes de custo, que multiplica por quatro tambem.</p>
  </div>
</section>

<section id="gestao">
  <h2>Gestao da operacao</h2>
  <p class="olho">Fixa. Nao se negocia stop no meio do trade.</p>
  <div class="regua">
    <div class="faixa"><div class="vlr">Entrada</div>
      <div>A mercado, no <b>fechamento</b> do candle de continuacao. Nao antecipe:
      entrar no meio do corpo com ordem limitada mede pior, porque perde justamente
      os trades que nao voltam &mdash; e sao eles que pagam.</div></div>
    <div class="faixa"><div class="vlr">Stop {n(P['stop'])}</div>
      <div>{n(P['stop'])} pontos da entrada, posicionado <b>antes</b> de a ordem de
      entrada ser enviada. Um candle de PI inteiro e 100 pontos: o stop equivale a
      um candio contra.</div></div>
    <div class="faixa"><div class="vlr">Parcial +{n(P['parcial_em'])}</div>
      <div>Sai <b>metade</b> da posicao em +{n(P['parcial_em'])}. O stop do restante
      <b>nao se move</b>: com meia posicao e a parcial na mesma distancia do stop, o
      preco em que o lucro ja realizado cancela a perda do restante <i>e</i> o stop
      inicial. Mudou o risco, nao o preco &mdash; e por isso o "zero a zero" aqui e
      zero de verdade.</div></div>
    <div class="faixa"><div class="vlr">Alvo {n(P['alvo'])}</div>
      <div>O restante sai em +{n(P['alvo'])}. Nao mexa no alvo com a operacao aberta:
      a grade inteira de stop e alvo foi medida, e 300 e um topo local &mdash; 250 e
      400 medem pior.</div></div>
    <div class="faixa"><div class="vlr">1:2, se quiser</div>
      <div>Trocar o alvo de {n(P['alvo'])} por <b>{n(r2['alvo_pts'])}</b> sem parcial
      sobe o acerto de {n(s['winrate'], 1)}% para <b>{n(r2['winrate'], 1)}%</b> &mdash;
      e derruba a expectativa de {sn(s['exp_pts'], 1)} para
      <b>{sn(r2['exp_pts'], 1)}</b> pontos por operacao, com rebaixamento
      <b>maior</b> ({n(r2['dd_max'])} contra {n(s['dd_max'])}). Mede positivo, mas
      paga para errar menos. Se a sequencia de perdas do 1:3 for o que te tira do
      plano, o 1:2 e um preco honesto por isso; fora dessa razao, nao compensa.</div></div>
    <div class="faixa"><div class="vlr">Fim do pregao</div>
      <div>Zera no ultimo candle do dia. Day trade, sem excecao.</div></div>
    <div class="faixa"><div class="vlr">Uma por vez</div>
      <div>Enquanto houver posicao aberta, sinal novo e ignorado. Todos os numeros
      deste plano foram medidos assim.</div></div>
  </div>
</section>

<section id="regras">
  <h2>Regras de mesa</h2>
  <div class="grade g2">
    <div class="card">
      <h3>O que o backteste apoia</h3>
      <ul class="enx" style="margin-bottom:0">
        <li>Operar compra e venda &mdash; os dois lados medem parecido
        ({n(s['longs_wr'], 1)}% de acerto na compra, {n(s['shorts_wr'], 1)}% na venda).</li>
        <li>Operar o dia inteiro. Nenhuma faixa de horario se mostrou boa ou ruim de
        forma estavel, inclusive a hora seguinte a abertura do mercado a vista.</li>
        <li>Tamanho de posicao constante. Nada no teste apoia aumentar depois de ganho
        ou depois de perda.</li>
      </ul>
    </div>
    <div class="card">
      <h3>O que fica a criterio, com medicao a favor</h3>
      <ul class="enx" style="margin-bottom:0">
        <li><b>Hull colada na EMA.</b> Quando a Hull passa mais de 8 candles colada na
        EMA 21, o setup mediu muito mal &mdash; e a consolidacao. A amostra e pequena
        (31 sinais) e por isso o filtro nao entrou na regra, mas se voce ve o cacho
        embolado na tela, tem medicao a seu favor para deixar passar.</li>
        <li><b>Sem a parcial.</b> Rende mais ({sn(pu['exp_pts'], 1)}
        contra {sn(s['exp_pts'], 1)} por trade) e balanca mais
        ({n(pu['dd_max'])} contra {n(s['dd_max'])} pontos de rebaixamento). E
        escolha de conforto, nao de backteste.</li>
      </ul>
    </div>
  </div>
</section>

<section id="galeria">
  <h2>Como o Ouro se parece</h2>
  <p class="olho">Seis exemplos reais, espalhados pelo periodo do backteste. A faixa
  clara e o par <b>retracao + continuacao</b>; a seta e a entrada; as linhas sao stop,
  parcial e alvo. A <b>Hull 50</b> e a linha amarela, a <b>EMA 21</b> a azul. Todos os
  seis cumprem os seis passos &mdash; o que muda de um para o outro e so o desfecho,
  que nao se sabe na hora de entrar.</p>
  <div class="grade g3 galeria">{cartoes_gal}</div>
  <p class="nota">Com acerto de {n(s['winrate'], 0)}%, a maioria dos exemplos de
  qualquer amostra honesta vai ser de perda &mdash; e por isso eles estao aqui. O que
  ha para decorar e o <b>desenho</b>: onde a Hull passa, quantos candles a retracao
  tem, e o tamanho do pavio do candle que retoma.</p>
</section>

<section id="checklist">
  <h2>Folha de checagem</h2>
  <p class="olho">Para imprimir e deixar do lado do monitor. Todas marcadas, envia.
  Uma so em branco, nao envia.</p>
  <div class="card">
    <ul class="lista-chk">{itens}</ul>
  </div>
  <div class="bandeira">
    <h3>Os tres erros que este plano tenta impedir</h3>
    <ol class="enx" style="margin-bottom:0">
      <li><b>Entrar esticado.</b> O passo 5 existe so para isso, e e o filtro que
      mais separa.</li>
      <li><b>Chamar um candle de retracao.</b> O passo 2 pede dois.</li>
      <li><b>Operar todo sinal que aparece.</b> O Bronze existe na tabela para
      mostrar o preco disso.</li>
    </ol>
  </div>
</section>

<footer>
  <p>Plano gerado do backteste em <code>relatorio.html</code> / <code>RESULTADOS.md</code>.
  Base: {n(D['auditoria']['candles'])} candles de 20 PI, {D['auditoria']['dias']}
  pregoes ({D['auditoria']['de']} a {D['auditoria']['ate']}).</p>
  <p>Backteste nao e promessa. {D['auditoria']['dias']} pregoes de mercado em alta
  nao garantem resultado nenhum.</p>
</footer>"""

    menu = ''.join(f'<li><a href="#{i}">{r}</a></li>' for i, r in SECOES)
    # o plano leva so os candles das seis miniaturas -- nao os 10.000 do
    # relatorio, que existem la por causa do grafico trade a trade
    dados = dict(candles=c['galeria']['candles'], parametros=P,
                 galeria_ex=c['galeria']['exemplos'])
    return (HTML.replace('__CSS__', molde.CSS + CSS_EXTRA)
            .replace('__MENU__', menu).replace('__CORPO__', corpo)
            .replace('__KIT__', molde.JS_KIT)
            .replace('__DADOS__', json.dumps(dados, ensure_ascii=False,
                                             separators=(',', ':'))))


# ------------------------------------------------------------------ markdown
def monta_md(c):
    D, P, s, n, sn = c['D'], c['P'], c['s'], c['n'], c['sn']
    r2 = D['variantes']['fecha|r2|ouro']['stats']
    alvo_r2 = D['gestoes']['r2']['alvo']
    L = []
    w = L.append
    w('# Plano de trading -- momentum no grafico de 20 PI (WINFUT)\n')
    w('Seis perguntas de sim ou nao, na ordem em que se olha para a tela. Se '
      'qualquer uma der nao, o trade nao existe -- nao ha "quase".\n')
    w(f"> **Leia isto antes.** Este plano sai de um backteste de "
      f"**{D['auditoria']['dias']} pregoes** ({D['auditoria']['de']} a "
      f"{D['auditoria']['ate']}) -- pouco mais de um mes, todo em mercado de alta. Os "
      'numeros sao **brutos**, sem corretagem e sem slippage. Rode em simulador por '
      'pelo menos um mes antes de dinheiro real. Ver [RESULTADOS.md](RESULTADOS.md) '
      'para o que o teste nao mediu.\n')

    w('## O setup\n')
    w('No grafico de **20 PI** do WINFUT todo candle fecha exatamente 100 pontos '
      'acima ou abaixo da sua abertura. Procura-se uma **retracao** contra a '
      'tendencia seguida de um candle de **continuacao** a favor, com a Hull 50 atras '
      'do preco e a EMA 21 cortando o par. A venda e o espelho exato da compra.\n')
    w(f"| | |\n| :--- | ---: |\n"
      f"| Por operacao | {sn(s['exp_pts'], 1)} pts (R$ {sn(s['exp_rs'], 2)}) |\n"
      f"| Acerto | {n(s['winrate'], 1)}% |\n"
      f"| Operacoes por pregao | {n(s['trades_dia'], 1)} |\n"
      f"| Rebaixamento maximo medido | {n(s['dd_max'])} pts |\n"
      f"| Medido em | {s['trades']} operacoes, {s['dias']} pregoes |\n")

    w('## Os seis passos\n')
    for g in c['gatilhos']:
        lim = lambda t: (t.replace('<b>', '**').replace('</b>', '**')
                         .replace('<i>', '*').replace('</i>', '*'))
        marca = 'VETO' if g.get('veto') else str(g['num'])
        w(f"### {marca}. {g['titulo']}\n")
        w(lim(g['regra']) + '\n')
        w('> *Por que:* ' + lim(g['porque']) + '\n')
        w('**Nao vale se:** ' + lim(g['veta']) + '\n')

    w('## Ouro, Prata e Bronze\n')
    w('Quando um passo falha, o sinal cai de nivel em vez de virar lixo.\n')
    w('| Nivel | Passos que cumpre | Por operacao | Acerto | Por dia | Rebaix. | '
      'O que fazer |\n| :--- | :--- | ---: | ---: | ---: | ---: | :--- |')
    for x in c['niveis']:
        w(f"| **{x['rot']}** | {x['passos']} | {sn(x['ev'], 1)} pts | "
          f"{n(x['wr'], 1)}% | {n(x['dia'], 1)} | {n(x['dd'])} pts | {x['acao']} |")
    w('')
    w('O Bronze esta na tabela para deixar claro **quanto** se perde operando tudo: '
      'quatro vezes mais trades para ganhar o mesmo, com o dobro do rebaixamento -- '
      'e isso antes do custo, que multiplica por quatro tambem.\n')

    w('## Gestao da operacao\n')
    w('Fixa. Nao se negocia stop no meio do trade.\n')
    w('- **Entrada:** a mercado, no **fechamento** do candle de continuacao. Nao '
      'antecipe: entrar no meio do corpo com limitada mede pior, porque perde '
      'justamente os trades que nao voltam -- e sao eles que pagam.\n'
      f"- **Stop:** {n(P['stop'])} pontos, posicionado **antes** de enviar a entrada. "
      'Um candle de PI inteiro e 100 pontos: o stop equivale a um candle contra.\n'
      f"- **Parcial:** metade da posicao em +{n(P['parcial_em'])}. O stop do restante "
      '**nao se move** -- com meia posicao e a parcial na mesma distancia do stop, o '
      'preco em que o lucro ja realizado cancela a perda do restante *e* o stop '
      'inicial. Mudou o risco, nao o preco.\n'
      f"- **Alvo:** o restante em +{n(P['alvo'])}. Nao mexa com a operacao aberta: a "
      'grade inteira foi medida e 300 e topo local (250 e 400 medem pior).\n'
      f"- **1:2, se quiser:** trocar o alvo de {n(P['alvo'])} por "
      f"**{n(alvo_r2)}** sem parcial sobe o acerto de {n(s['winrate'], 1)}% para "
      f"**{n(r2['winrate'], 1)}%** e derruba a expectativa de {sn(s['exp_pts'], 1)} "
      f"para **{sn(r2['exp_pts'], 1)}** pontos por operacao, com rebaixamento "
      f"**maior** ({n(r2['dd_max'])} contra {n(s['dd_max'])}). Mede positivo, mas "
      'paga para errar menos. Se a sequencia de perdas do 1:3 for o que te tira do '
      'plano, e um preco honesto por isso; fora dessa razao, nao compensa.\n'
      '- **Fim do pregao:** zera no ultimo candle do dia. Day trade, sem excecao.\n'
      '- **Uma por vez:** enquanto houver posicao aberta, sinal novo e ignorado. '
      'Todos os numeros foram medidos assim.\n')

    w('## Regras de mesa\n')
    w('**O que o backteste apoia**\n')
    w(f"- Operar os dois lados ({n(s['longs_wr'], 1)}% de acerto na compra, "
      f"{n(s['shorts_wr'], 1)}% na venda).\n"
      '- Operar o dia inteiro: nenhuma faixa de horario se mostrou boa ou ruim de '
      'forma estavel, inclusive a hora seguinte a abertura do mercado a vista.\n'
      '- Tamanho de posicao constante.\n')
    w('**O que fica a criterio, com medicao a favor**\n')
    pu = D['variantes']['fecha|puro|ouro']['stats']
    w('- **Hull colada na EMA.** Mais de 8 candles colada na EMA 21 mediu muito mal '
      '-- e a consolidacao. Amostra pequena (31 sinais), por isso nao entrou na '
      'regra; mas se o cacho esta embolado na tela, ha medicao a favor de deixar '
      'passar.\n'
      f"- **Sem a parcial.** Rende mais ({sn(pu['exp_pts'], 1)} contra "
      f"{sn(s['exp_pts'], 1)} por trade) e balanca mais ({n(pu['dd_max'])} contra "
      f"{n(s['dd_max'])} pontos de rebaixamento). Escolha de conforto.\n")

    w('## Como o Ouro se parece\n')
    w('Seis exemplos reais, espalhados pelo periodo do backteste, estao em '
      '`plano.html` (secao *Como se parece*) e no relatorio, que tem tambem as '
      'galerias do Prata e do Bronze com o motivo de cada um nao ter subido de '
      'nivel. Em texto nao da para desenhar candle; o que da para deixar escrito e '
      'o que procurar neles:\n')
    w(f"- a **Hull 50** passando por baixo do par inteiro (numa compra), ja "
      'inclinada;\n'
      '- **dois ou tres** candles de retracao, nao um;\n'
      '- a **EMA 21** cortando o par, nem acima nem abaixo dele;\n'
      f"- o candle de continuacao com pavio **visivel mas nao enorme** -- entre "
      f"{n(P['pavio_min'])} e {n(P['pavio_max'])} pontos, num candle cujo corpo e "
      'sempre 100.\n')
    w(f"Com acerto de {n(s['winrate'], 0)}%, a maioria dos exemplos de qualquer "
      'amostra honesta vai ser de perda. O que ha para decorar e o desenho, nao o '
      'desfecho.\n')

    w('## Folha de checagem\n')
    w('Todas marcadas, envia. Uma so em branco, nao envia.\n')
    for t in ['Hull 50 no sentido do trade e atras do preco',
              'Retracao de 2 ou mais candles',
              'Os dois extremos do par fora da Hull',
              'EMA 21 entre os topos e os fundos do par',
              'NAO e exaustao (Hull acelerando + preco esticado)',
              f"Pavio total do candle entre {n(P['pavio_min'])} e "
              f"{n(P['pavio_max'])} pontos",
              'Stop de 100 pontos ja posicionado ANTES de entrar',
              'Nao ha posicao aberta neste momento']:
        w(f'- [ ] {t}')
    w('')
    w('### Os tres erros que este plano tenta impedir\n')
    w('1. **Entrar esticado.** O passo 5 existe so para isso, e e o filtro que mais '
      'separa.\n'
      '2. **Chamar um candle de retracao.** O passo 2 pede dois.\n'
      '3. **Operar todo sinal que aparece.** O Bronze existe na tabela para mostrar '
      'o preco disso.\n')
    w('---\n')
    w(f"*Gerado de `relatorio.html` / `RESULTADOS.md`. Base: "
      f"{n(D['auditoria']['candles'])} candles de 20 PI, {D['auditoria']['dias']} "
      'pregoes. Backteste nao e promessa.*')
    return '\n'.join(L)
