# -*- coding: utf-8 -*-
"""
O molde do plano operacional: plano.html e PLANO.md.

Desde a base de 132 pregoes o plano do padrao Ouro esta SUSPENSO (nao
passou no teste fora da amostra). O molde agora escreve o status, o
motivo e o protocolo de teste em simulador da hipotese que sobrou.

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
<title>Plano Momentum PI</title>
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

SECOES = [('status', 'Status'), ('porque', 'Por que parou'), ('hipotese', 'A hipotese'),
          ('passos', 'Os 5 passos'), ('gestao', 'Gestao'), ('protocolo', 'Protocolo de teste'),
          ('galeria', 'Como se parece'), ('checklist', 'Folha de registro')]


def monta_html(c):
    D, P, n, sn = c['D'], c['P'], c['n'], c['sn']
    O = D['oos']['blocos']
    C = D['candidato']; G = C['gestoes']; g = G['parcial']; s = g['stats']
    pr = c['protocolo']

    lin_bl = ''
    for chave, rot in (('fecha|parcial|ouro', 'Ouro'), ('fecha|parcial|prata', 'Prata'),
                       ('fecha|parcial|bronze', 'Bronze')):
        x = O[chave]['sinais']
        lin_bl += (f"<tr><td>{rot}</td>"
                   + ''.join(f"<td class=\"{'pos' if (x[k]['ev'] or 0) > 0 else 'neg'}\">{sn(x[k]['ev'], 1)}"
                             f"<br><small style=\"color:var(--mudo)\">{n(x[k]['n'])} sinais</small></td>"
                             for k in ('antes', 'original'))
                   + '</tr>')
    lin_g = ''.join(
        f"<tr><td>{C['rot_gestao'][k]}</td><td>{sn(G[k]['stats']['exp_pts'], 1)}</td>"
        f"<td>{n(G[k]['stats']['winrate'], 1)}%</td><td>{n(G[k]['stats']['fator_lucro'], 2)}</td>"
        f"<td>{n(G[k]['stats']['dd_max'])}</td><td>{sn(G[k]['blocos']['antes']['ev'], 1)}</td>"
        f"<td>{sn(G[k]['blocos']['original']['ev'], 1)}</td></tr>" for k in ('parcial', 'puro', 'r2', 'r1'))

    passos = ''
    for p_ in c['gatilhos']:
        passos += f"""
  <div class="passo">
    <div class="n">{p_['num']}</div>
    <div>
      <h3>{p_['titulo']}</h3>
      <p class="regra">{p_['regra']}</p>
      <p class="por">{p_['porque']}</p>
      <p class="nao">Nao vale se: {p_['veta']}</p>
    </div>
  </div>"""

    cartoes_gal = ''
    for k, ex in enumerate(c['galeria']['exemplos']):
        res = 'empatou' if abs(ex['pts']) < 1e-9 else ('ganhou' if ex['pts'] > 0 else 'perdeu')
        cor = '' if abs(ex['pts']) < 1e-9 else ('pos' if ex['pts'] > 0 else 'neg')
        cartoes_gal += f"""
      <figure class="ex">
        <div class="ex-topo">
          <span class="ex-data">{ex['data']} &middot; {'compra' if ex['lado'] > 0 else 'venda'}</span>
          <span class="ex-res {cor}">{sn(ex['pts'])} pts</span>
        </div>
        <div id="gal_{k}" class="ex-viz"></div>
        <figcaption>Retracao de {ex['n_ret']} candles. Saiu no {ex['rot_saida']} &mdash;
          {res}.</figcaption>
      </figure>"""

    chk = ['Data, hora e lado do sinal', 'Quantos candles de retracao (3 ou mais)',
           'Hull 50 no sentido do trade e atras do extremo dos dois candles do par',
           'EMA 21 entre o menor fundo e o maior topo do par',
           'Preco de entrada (fechamento do candle de continuacao) e preco de saida',
           'Motivo da saida: stop, zero a zero, alvo ou fim do pregao',
           'Custo real da operacao (corretagem, emolumentos e escorregamento)',
           'Sinal que apareceu com posicao aberta: anotado como ignorado']
    itens = ''.join(f'<li><span class="cx"></span><span>{t}</span></li>' for t in chk)

    corpo = f"""
<header class="capa">
  <div class="chapeu">Plano de trading &middot; WINFUT &middot; grafico de 20 PI</div>
  <h1>Plano suspenso,<br>hipotese em teste</h1>
  <p class="sub">O setup Ouro deste plano nao passou no teste fora da amostra da base de
  {D['auditoria']['dias']} pregoes. Este documento substitui o plano anterior: diz o que nao operar,
  e como testar, sem dinheiro, a unica hipotese que sobrou.</p>
  <div style="margin-top:18px">
    <span class="selo">Ouro e Prata: nao operar</span>
    <span class="selo">retracao de {C['n_ret_min']}+ candles</span>
    <span class="selo">so em simulador</span>
    <span class="selo">stop {n(P['stop'])} &middot; alvo {n(P['alvo'])}</span>
  </div>
</header>

<section id="status">
  <h2>Status</h2>
  <div class="grade g3">
    <div class="tile"><div class="rot">Padrao Ouro</div><div class="num neg">Suspenso</div>
      <div class="pe">{sn(O['fecha|parcial|ouro']['sinais']['antes']['ev'], 1)} pts por trade fora da amostra</div></div>
    <div class="tile"><div class="rot">Robo MomentumPI_OuroPrata</div><div class="num neg">Desligar</div>
      <div class="pe">opera exatamente o Ouro e o Prata</div></div>
    <div class="tile"><div class="rot">Retracao profunda</div><div class="num">Em teste</div>
      <div class="pe">simulador, a partir de {pr['inicio']}</div></div>
  </div>
</section>

<section id="porque">
  <h2>Por que o plano anterior parou</h2>
  <p class="olho">Os filtros do Ouro foram escolhidos em 26 pregoes, de 06/08 a 11/09. A base nova tem
  os cinco meses anteriores, que nunca participaram da escolha. Neles:</p>
  <div class="card rolo"><table>
    <thead><tr><th>Nivel</th><th>Antes (06/03 a 05/08)<br><small>nunca visto</small></th>
      <th>Janela original (06/08 a 11/09)<br><small>onde as regras nasceram</small></th></tr></thead>
    <tbody>{lin_bl}</tbody></table>
    <p class="nota">Pontos por sinal, entrada no fechamento, 1:3 com parcial, brutos. Detalhe completo
    em <code>relatorio.html</code>, secao &ldquo;Fora da amostra&rdquo;.</p></div>
</section>

<section id="hipotese">
  <h2>A hipotese</h2>
  <p class="olho">A mesma regra-base do CLAUDE.md &mdash; retracao, candle de continuacao, Hull 50 atras
  do preco, EMA 21 cortando o par &mdash; com <b>uma</b> exigencia a mais: a retracao tem <b>{C['n_ret_min']} ou
  mais candles</b>. Sem veto de exaustao, sem filtro de pavio, sem horario.</p>
  <div class="grade g4">
    <div class="tile"><div class="rot">Medido por trade</div><div class="num pos">{sn(s['exp_pts'], 1)} pts</div>
      <div class="pe">{n(s['trades'])} trades em {D['auditoria']['dias']} pregoes, bruto</div></div>
    <div class="tile"><div class="rot">Acerto</div><div class="num">{n(s['winrate'], 1)}%</div>
      <div class="pe">fator de lucro {n(s['fator_lucro'], 2)}</div></div>
    <div class="tile"><div class="rot">Frequencia</div><div class="num">{n(s['trades'] / D['auditoria']['dias'], 1)}</div>
      <div class="pe">operacoes por pregao, em media</div></div>
    <div class="tile"><div class="rot">Rebaixamento</div><div class="num">{n(s['dd_max'])} pts</div>
      <div class="pe">Monte Carlo p95: {n(g['mc']['dd_p95'])} pts</div></div>
  </div>
  <div class="bandeira">
    <h3>Por que isto nao e um setup ainda</h3>
    <p style="margin-bottom:0">O corte de {C['n_ret_min']} candles foi escolhido depois de olhar esta mesma base.
    Ele mede bem nos dois blocos ({sn(g['blocos']['antes']['ev'], 1)} antes, {sn(g['blocos']['original']['ev'], 1)}
    na janela original) e nos tres tercos, mas quando a busca e refeita em dados embaralhados, considerando
    todas as tabelas de filtro que foram olhadas, algo tao bom aparece
    {n(g['busca_ampla']['p_valor'] * 100, 0)}% das vezes. So pregoes que ainda nao aconteceram decidem.</p>
  </div>
  <div class="card rolo" style="margin-top:16px"><table>
    <thead><tr><th>Gestao</th><th>Por trade</th><th>Acerto</th><th>Fator</th><th>Rebaix.</th>
      <th>Antes</th><th>Original</th></tr></thead><tbody>{lin_g}</tbody></table>
    <p class="nota">As quatro gestoes medem parecido. O teste usa a do CLAUDE.md (1:3 com parcial) para nao
    escolher gestao olhando o resultado.</p></div>
</section>

<section id="passos">
  <h2>Os cinco passos</h2>
  <p class="olho">Na ordem em que se olha para a tela. Qualquer &ldquo;nao&rdquo;, o sinal nao existe.</p>
  {passos}
</section>

<section id="gestao">
  <h2>Gestao</h2>
  <div class="regua">
    <div class="faixa"><div class="vlr">Entrada</div><div>A mercado, no <b>fechamento</b> do candle de
      continuacao. Nao antecipe: a entrada antecipada nao pode ser medida com a base disponivel.</div></div>
    <div class="faixa"><div class="vlr neg">Stop {n(P['stop'])}</div><div>{n(P['stop'])} pontos, junto com
      a entrada.</div></div>
    <div class="faixa"><div class="vlr pos">+{n(P['parcial_em'])}</div><div>Sai <b>metade</b>. O stop do
      restante fica na media da operacao &mdash; com metade realizada em +{n(P['parcial_em'])}, e o proprio stop
      inicial: se voltar, zero a zero.</div></div>
    <div class="faixa"><div class="vlr pos">Alvo {n(P['alvo'])}</div><div>Sai o restante.</div></div>
    <div class="faixa"><div class="vlr">Fim do dia</div><div>Zera o que estiver aberto no ultimo candle do
      pregao.</div></div>
    <div class="faixa"><div class="vlr">1 por vez</div><div>Sinal com posicao aberta e ignorado (e
      anotado).</div></div>
  </div>
</section>

<section id="protocolo">
  <h2>Protocolo de teste</h2>
  <p class="olho">As regras acima ficam <b>congeladas</b> durante o teste. Mudar um corte no meio
  zera a contagem: o teste passa a ser de outra hipotese.</p>
  <div class="regua">
    <div class="faixa"><div class="vlr">Onde</div><div>Simulador, 1 contrato, a partir de
      {pr['inicio']}. Em paralelo, exportar a base do robo toda semana e rodar
      <code>python rodar.py &amp;&amp; python candidato.py</code>: o bloco &ldquo;depois&rdquo; mede a mesma
      regra nos pregoes novos, sem erro de execucao.</div></div>
    <div class="faixa"><div class="vlr">Quanto</div><div><b>{n(pr['n_conf'])} operacoes</b> (cerca de
      {n(pr['pregoes_conf'])} pregoes). E o numero em que um valor real de {sn(pr['ev_min'], 0)} pontos por trade
      apareceria com t acima de 2, com o desvio medido de {n(pr['desvio'])} pontos.</div></div>
    <div class="faixa"><div class="vlr pos">Confirma</div><div>Depois de {n(pr['n_conf'])} operacoes: valor
      por trade <b>ja descontado o custo real</b> acima de zero, com t &ge; 2. So entao vale escrever um plano
      de dinheiro real &mdash; com os numeros do teste, nao os do backteste.</div></div>
    <div class="faixa"><div class="vlr neg">Abandona</div><div>Qualquer um: valor por trade &le; 0 depois de
      {n(pr['n_parcial'])} operacoes (se a hipotese fosse verdadeira, isso aconteceria
      {n(pr['p_falso_abandono'], 0)}% das vezes); rebaixamento acima de {n(pr['dd_limite'])} pontos (p95 do
      Monte Carlo); mais de {pr['seq_limite']} perdas seguidas (o dobro do maximo medido).</div></div>
    <div class="faixa"><div class="vlr">Inconclusivo</div><div>Positivo mas com t &lt; 2 em
      {n(pr['n_conf'])} operacoes: continua em simulador ate {n(2 * pr['n_conf'])}.</div></div>
  </div>
</section>

<section id="galeria">
  <h2>Como a hipotese se parece</h2>
  <p class="olho">Seis operacoes reais do backteste, espalhadas pelo periodo. A faixa clara vai do primeiro
  candle da retracao ao candle de continuacao; a seta e a entrada; as linhas sao stop, parcial e alvo. A
  <b>Hull 50</b> e a linha amarela, a <b>EMA 21</b> a azul.</p>
  <div class="grade g3 galeria">{cartoes_gal}</div>
  <p class="nota">Com acerto perto de {n(s['winrate'], 0)}%, a maioria das operacoes de qualquer amostra honesta
  e de perda. O que ha para decorar e o desenho.</p>
</section>

<section id="checklist">
  <h2>Folha de registro, por operacao</h2>
  <div class="card"><ul class="lista-chk">{itens}</ul></div>
</section>

<footer>
  <p>Gerado por <code>plano.py</code> a partir de <code>saida/resumo.json</code>. Base:
  {n(D['auditoria']['candles'])} candles de 20 PI, {D['auditoria']['dias']} pregoes
  ({D['auditoria']['de']} a {D['auditoria']['ate']}).</p>
  <p>Backteste nao e promessa. O plano anterior e a prova.</p>
</footer>"""

    menu = ''.join(f'<li><a href="#{i}">{r}</a></li>' for i, r in SECOES)
    dados = dict(candles=c['galeria']['candles'], parametros=P, galeria_ex=c['galeria']['exemplos'])
    return (HTML.replace('__CSS__', molde.CSS + CSS_EXTRA)
            .replace('__MENU__', menu).replace('__CORPO__', corpo)
            .replace('__KIT__', molde.JS_KIT)
            .replace('__DADOS__', json.dumps(dados, ensure_ascii=False, separators=(',', ':'))))


# ------------------------------------------------------------------ markdown
def monta_md(c):
    D, P, n, sn = c['D'], c['P'], c['n'], c['sn']
    O = D['oos']['blocos']
    C = D['candidato']; G = C['gestoes']; g = G['parcial']; s = g['stats']
    pr = c['protocolo']
    lim = lambda t: (t.replace('<b>', '**').replace('</b>', '**').replace('<i>', '*')
                     .replace('</i>', '*').replace('&ldquo;', '"').replace('&rdquo;', '"'))
    L = []
    w = L.append
    w('# Plano de trading -- SUSPENSO, hipotese em teste (WINFUT, 20 PI)\n')
    w(f"> **Status.** O padrao Ouro deste plano **nao passou** no teste fora da amostra da base de "
      f"{D['auditoria']['dias']} pregoes. **Nao operar o Ouro nem o Prata**, e desligar o robo "
      '`Robo-NTSL/MomentumPI_OuroPrata_Robo.ntsl`. O que segue e o protocolo para testar, em simulador, '
      'a unica hipotese que sobrou.\n')
    w('## Por que o plano anterior parou\n')
    w('Os filtros do Ouro foram escolhidos em 26 pregoes (06/08 a 11/09). Nos cinco meses anteriores, que '
      'nunca participaram da escolha (pontos por sinal, fechamento, 1:3 com parcial):\n')
    w('| Nivel | Antes (06/03 a 05/08) | Janela original (06/08 a 11/09) |\n| :--- | ---: | ---: |')
    for chave, rot in (('fecha|parcial|ouro', 'Ouro'), ('fecha|parcial|prata', 'Prata'),
                       ('fecha|parcial|bronze', 'Bronze')):
        x = O[chave]['sinais']
        w(f"| {rot} | {sn(x['antes']['ev'], 1)} ({x['antes']['n']}) | {sn(x['original']['ev'], 1)} ({x['original']['n']}) |")
    w('')
    w('## A hipotese\n')
    w(f"A regra-base do CLAUDE.md com **uma** exigencia a mais: retracao de **{C['n_ret_min']} ou mais "
      'candles**. Sem veto de exaustao, sem filtro de pavio, sem horario.\n')
    w(f"- Medido: {sn(s['exp_pts'], 1)} pts por trade brutos, {s['trades']} trades em {D['auditoria']['dias']} pregoes, "
      f"acerto {n(s['winrate'], 1)}%, fator de lucro {n(s['fator_lucro'], 2)}, rebaixamento {n(s['dd_max'])} pts "
      f"(Monte Carlo p95 {n(g['mc']['dd_p95'])}).")
    w(f"- Antes: {sn(g['blocos']['antes']['ev'], 1)}; janela original: {sn(g['blocos']['original']['ev'], 1)}.")
    w(f"- **Nao e setup ainda:** o corte foi escolhido olhando esta base; refeita a busca em dados embaralhados "
      f"sobre todas as tabelas olhadas, algo tao bom aparece {n(g['busca_ampla']['p_valor'] * 100, 0)}% das vezes.\n")
    w('## Os cinco passos (compra; venda e o espelho)\n')
    for p_ in c['gatilhos']:
        w(f"### {p_['num']}. {p_['titulo']}\n")
        w(lim(p_['regra']) + '\n')
        w('> *Por que:* ' + lim(p_['porque']) + '\n')
        w('**Nao vale se:** ' + lim(p_['veta']) + '\n')
    w('## Gestao\n')
    w(f"- **Entrada:** a mercado, no fechamento do candle de continuacao (nao antecipar).\n"
      f"- **Stop:** {n(P['stop'])} pontos, junto com a entrada.\n"
      f"- **+{n(P['parcial_em'])}:** sai metade; stop do restante na media da operacao (= stop inicial).\n"
      f"- **Alvo:** {n(P['alvo'])} no restante.\n"
      '- **Fim do dia:** zera no ultimo candle do pregao. Uma posicao por vez.\n')
    w('## Protocolo de teste\n')
    w('Regras **congeladas** durante o teste.\n')
    w(f"- **Onde:** simulador, 1 contrato, a partir de {pr['inicio']}. Toda semana, exportar a base do robo e "
      'rodar `python rodar.py && python candidato.py` (bloco "depois").')
    w(f"- **Quanto:** {pr['n_conf']} operacoes (~{n(pr['pregoes_conf'])} pregoes) -- onde um valor real de "
      f"{sn(pr['ev_min'], 0)} pts por trade apareceria com t > 2 (desvio medido {n(pr['desvio'])} pts).")
    w(f"- **Confirma:** apos {pr['n_conf']} operacoes, valor por trade descontado o custo real > 0 com t >= 2.")
    w(f"- **Abandona:** valor por trade <= 0 depois de {pr['n_parcial']} operacoes (com a hipotese verdadeira, "
      f"{n(pr['p_falso_abandono'], 0)}% de chance); rebaixamento > {n(pr['dd_limite'])} pts; mais de "
      f"{pr['seq_limite']} perdas seguidas.")
    w(f"- **Inconclusivo:** positivo com t < 2 -- continua ate {2 * pr['n_conf']} operacoes.\n")
    w('## Folha de registro, por operacao\n')
    for t in ['Data, hora e lado', 'Candles de retracao (3 ou mais)', 'Hull 50 no sentido e atras do par',
              'EMA 21 entre o menor fundo e o maior topo do par', 'Preco de entrada e de saida',
              'Motivo da saida', 'Custo real', 'Sinais ignorados por posicao aberta']:
        w(f'- [ ] {t}')
    w('')
    w('---\n')
    w(f"*Gerado por `plano.py`. Base: {n(D['auditoria']['candles'])} candles, {D['auditoria']['dias']} pregoes. "
      'Graficos e exemplos em `plano.html`.*')
    return '\n'.join(L)
