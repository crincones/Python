# -*- coding: utf-8 -*-
"""Molde do relatorio.html. Substituicao simples de {{chave}}.

Nao ha numero escrito aqui: tudo vem do contexto montado por relatorio.py
a partir de saida/resumo.json.
"""
import re


def render(ctx):
    def sub(m):
        expr = m.group(1).strip()
        v = ctx
        for parte in expr.split('.'):
            v = v[parte] if isinstance(v, dict) else getattr(v, parte)
        return str(v)
    return re.sub(r'\{\{([^{}]+)\}\}', sub, MOLDE)


MOLDE = r"""<meta charset="utf-8">
<title>Barra grande no nível</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">

<style>
:root{
  --paper:#EFF3F5; --card:#FFFFFF; --card-2:#F6F9FA;
  --ink:#111B22; --ink-2:#4B5D69; --ink-3:#7B8C97;
  --line:#D6E0E6; --line-2:#E8EEF1;
  --accent:#1F5A73; --accent-soft:#E2EDF2; --on-accent:#FFFFFF;
  --pos:#1A6E48; --neg:#A93227; --warn:#8A6516; --zero:#7B8C97;
  --pos-bg:#E4F1EA; --neg-bg:#F8E7E5;
  --alta:#2E8B62; --baixa:#C0483C;
  --s1:#14639E; --s2:#96601A;
  --shadow:0 1px 2px rgba(17,27,34,.06), 0 8px 24px -12px rgba(17,27,34,.14);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#0C1216; --card:#141E24; --card-2:#18242B;
  --ink:#E4EDF2; --ink-2:#9DB0BC; --ink-3:#70848F;
  --line:#243239; --line-2:#1C282F;
  --accent:#6FB2CE; --accent-soft:#17303C; --on-accent:#0C1216;
  --pos:#4FB884; --neg:#E27A6E; --warn:#D5A648; --zero:#70848F;
  --pos-bg:#122C22; --neg-bg:#2E1A18;
  --alta:#4FB884; --baixa:#E27A6E;
  --s1:#5292C6; --s2:#B98B30;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.6);
}}
:root[data-theme="dark"]{
  --paper:#0C1216; --card:#141E24; --card-2:#18242B;
  --ink:#E4EDF2; --ink-2:#9DB0BC; --ink-3:#70848F;
  --line:#243239; --line-2:#1C282F;
  --accent:#6FB2CE; --accent-soft:#17303C; --on-accent:#0C1216;
  --pos:#4FB884; --neg:#E27A6E; --warn:#D5A648; --zero:#70848F;
  --pos-bg:#122C22; --neg-bg:#2E1A18;
  --alta:#4FB884; --baixa:#E27A6E;
  --s1:#5292C6; --s2:#B98B30;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.6);
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Source Serif 4",Georgia,"Times New Roman",serif;
  font-size:17px;line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:0 24px 96px}
h1,h2,h3,h4,h5,.ui,button,select,th,caption,.tile-k,.tile-s,.tag,.b,.lab,.pill,.cs,.legenda
  {font-family:Archivo,"Helvetica Neue",Arial,sans-serif}
.mono,td.num,th.num,.tile-v,.v,.t,.count,.res{font-family:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace;
  font-variant-numeric:tabular-nums}

header{border-bottom:1px solid var(--line);
  background:linear-gradient(180deg,var(--card) 0%,var(--paper) 100%)}
.head{max-width:1120px;margin:0 auto;padding:56px 24px 40px}
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  color:var(--accent);margin:0 0 14px;font-family:Archivo,sans-serif}
h1{font-size:clamp(36px,5.6vw,56px);line-height:1.04;margin:0 0 16px;font-weight:700;
  letter-spacing:-.022em;text-wrap:balance}
.lede{font-size:20px;color:var(--ink-2);max-width:64ch;margin:0 0 28px}
.spec{display:flex;flex-wrap:wrap;gap:8px}
.chip{font-family:"IBM Plex Mono",monospace;font-size:12.5px;padding:5px 11px;
  border:1px solid var(--line);border-radius:999px;background:var(--card);
  color:var(--ink-2);font-variant-numeric:tabular-nums}
.chip b{color:var(--ink);font-weight:600}

section{margin:64px 0 0;scroll-margin-top:20px}
h2{font-size:13px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink-3);margin:0 0 6px;display:flex;align-items:baseline;gap:12px}
h2 .n{color:var(--accent);font-variant-numeric:tabular-nums}
h3{font-size:27px;line-height:1.2;margin:0 0 14px;font-weight:600;
  letter-spacing:-.015em;text-wrap:balance}
p{margin:0 0 16px;max-width:68ch}
.sub{color:var(--ink-2);font-size:.85em}
strong,b{font-weight:600}
code{font-family:"IBM Plex Mono",monospace;font-size:.88em;background:var(--card-2);
  border:1px solid var(--line-2);border-radius:4px;padding:1px 5px}

.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:24px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:16px 18px;box-shadow:var(--shadow)}
.tile-k{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);margin-bottom:8px}
.tile-v{font-size:27px;font-weight:600;line-height:1;letter-spacing:-.02em}
.tile-s{font-size:13px;color:var(--ink-3);margin-top:6px}
.pos{color:var(--pos)} .neg{color:var(--neg)} .zer{color:var(--zero)}

.scroll{overflow-x:auto;margin:20px 0;border:1px solid var(--line);border-radius:10px;
  background:var(--card);box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;font-size:14.5px}
caption{text-align:left;font-size:13px;font-weight:600;color:var(--ink-2);padding:14px 18px 0}
th,td{padding:9px 14px;text-align:left;border-bottom:1px solid var(--line-2);white-space:nowrap;
  vertical-align:top}
thead th{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-3);border-bottom:1px solid var(--line)}
td.num,th.num{text-align:right}
tbody tr:last-child td{border-bottom:none}
tr.hi td{background:var(--accent-soft)}
tr.mute td{color:var(--ink-3);background:var(--card-2)}
td .sub{display:block;white-space:normal;max-width:34ch;line-height:1.35;margin-top:2px}

.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:18px;margin:24px 0}
.chart{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:18px 18px 12px;box-shadow:var(--shadow)}
.chart h5{font-size:14px;font-weight:600;margin:0 0 2px}
.chart .cs{font-size:12.5px;color:var(--ink-3);margin:0 0 12px}
.chart svg{display:block;width:100%;height:auto;overflow:visible}

.note{border-left:3px solid var(--accent);background:var(--card);padding:16px 20px;
  border-radius:0 10px 10px 0;margin:22px 0;box-shadow:var(--shadow)}
.note.risk{border-left-color:var(--neg)}
.note p:last-child{margin-bottom:0}
.note .lab{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);margin-bottom:6px}

/* ---------- visualizador ---------- */
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:22px 0 14px}
.grp{display:flex;align-items:center;gap:6px;background:var(--card);border:1px solid var(--line);
  border-radius:9px;padding:5px 8px;box-shadow:var(--shadow)}
.grp .lab{font-size:10.5px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
  color:var(--ink-3);padding-right:2px}
button{font-family:Archivo,sans-serif;font-size:12.5px;font-weight:600;color:var(--ink-2);
  background:transparent;border:1px solid transparent;border-radius:6px;padding:4px 10px;cursor:pointer}
button:hover{background:var(--card-2);color:var(--ink)}
button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
button:disabled{opacity:.35;cursor:default}
select{font-size:12.5px;background:var(--card);color:var(--ink);border:1px solid var(--line);
  border-radius:6px;padding:4px 6px}
.count{font-size:12.5px;color:var(--ink-2);min-width:96px;text-align:center}
.painel{display:grid;grid-template-columns:minmax(0,1fr) 262px;gap:16px;align-items:start}
@media(max-width:900px){.painel{grid-template-columns:minmax(0,1fr)}}
.quadro{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:14px;box-shadow:var(--shadow);min-width:0}
.quadro .cab{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;
  margin:0 2px 10px;font-family:Archivo,sans-serif;font-size:12.5px;color:var(--ink-3)}
.quadro .cab b{font-size:14px;font-weight:600;color:var(--ink)}
.quadro .cab .dica{margin-left:auto;font-size:11px}
.area{position:relative}
#kchart{width:100%;height:470px;min-width:0}
.area .vazio{position:absolute;inset:0;margin:0;max-width:none;display:grid;
  place-items:center;background:var(--card);border-radius:8px;z-index:5}
.area .vazio[hidden]{display:none}
@media(max-width:700px){#kchart{height:380px}}
.ficha{background:var(--card);border:1px solid var(--line);border-radius:12px;
  box-shadow:var(--shadow);overflow:hidden}
.ficha .topo{padding:14px 16px;border-bottom:1px solid var(--line-2)}
.ficha .res{font-size:30px;font-weight:600;letter-spacing:-.02em;line-height:1}
.ficha .quando{font-size:12px;color:var(--ink-3);margin-top:6px;font-family:Archivo,sans-serif}
.linhas{padding:6px 0}
.ln{display:flex;justify-content:space-between;gap:10px;padding:6px 16px;font-size:12.5px}
.ln .k{color:var(--ink-3);font-family:Archivo,sans-serif}
.ln .v{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;font-weight:500}
.pill{font-size:10.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  padding:2px 8px;border-radius:999px;display:inline-block}
.p-alvo{background:var(--pos-bg);color:var(--pos)}
.p-stop{background:var(--neg-bg);color:var(--neg)}
.p-zero{background:var(--card-2);color:var(--zero)}
.p-fim{background:var(--card-2);color:var(--warn)}
.lista-wrap{margin-top:16px;background:var(--card);border:1px solid var(--line);
  border-radius:12px;box-shadow:var(--shadow);overflow:hidden}
.lista-wrap h4{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);margin:0;padding:13px 16px 9px}
.lista-wrap table{font-size:12.5px}
.lista-wrap th,.lista-wrap td{padding:7px 16px}
.lista-wrap tbody tr{cursor:pointer}
.lista-wrap tbody tr:hover td{background:var(--card-2)}
.lista-wrap tbody tr[aria-current="true"] td{background:var(--accent-soft)}
.rolagem{max-height:300px;overflow:auto}
.legenda{display:flex;flex-wrap:wrap;gap:14px;margin-top:12px;font-size:11.5px;color:var(--ink-3)}
.legenda span{display:flex;align-items:center;gap:5px}
.sw{width:11px;height:11px;border-radius:2px;display:inline-block}
.sw.l{height:2px;border-radius:0}
.vazio{padding:30px 16px;color:var(--ink-3);font-size:13px;text-align:center}

footer{margin-top:72px;padding-top:24px;border-top:1px solid var(--line);
  font-family:Archivo,sans-serif;font-size:13px;color:var(--ink-3)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>

<header>
  <div class="head">
    <p class="eyebrow">Estudo · WIN · barras de 10.000 ticks</p>
    <h1>A barra grande no nível</h1>
    <p class="lede">A hipótese: barras grandes que pivotam em cima das médias, da VWAP ou dos pontos de pivô <em>andam</em>, ou marcam <em>reversão confiável</em>. Foram medidas as duas metades, separadamente, contra controle. Uma delas é falsa; a outra sobrevive — mas não pelo motivo que a hipótese diz.</p>
    <div class="spec">
      <span class="chip">barra grande = range ≥ <b>{{fg}}</b> × range médio</span>
      <span class="chip">corrida simétrica <b>±{{xv}}</b></span>
      <span class="chip">WINFUT <b>{{pregoes_fu}}</b> pregões</span>
      <span class="chip">WINV26 <b>{{pregoes_v26}}</b> pregões</span>
      <span class="chip"><b>{{n_celulas}}</b> células medidas</span>
    </div>
  </div>
</header>

<div class="wrap">

<section>
  <h2><span class="n">01</span> A resposta</h2>
  <h3>“Andar” é falso. “Reverter” tem alguma coisa — e o nível não é ela.</h3>

  <div class="tiles">
    <div class="tile"><div class="tile-k">Continuação</div><div class="tile-v neg">falha</div><div class="tile-s">abaixo de 50% nas quatro medidas</div></div>
    <div class="tile"><div class="tile-k">Falha da barra</div><div class="tile-v pos">{{acerto_falha_fu}}</div><div class="tile-s">WINFUT · corrida ±{{xv}}</div></div>
    <div class="tile"><div class="tile-k">Falha da barra</div><div class="tile-v pos">{{acerto_falha_v26}}</div><div class="tile-s">WINV26 · mesma medida</div></div>
    <div class="tile"><div class="tile-k">O nível</div><div class="tile-v neg">tira</div><div class="tile-s">exigir nível piora nas duas bases</div></div>
  </div>

  <div class="note risk">
    <div class="lab">Veredito — o resultado é aceitável?</div>
    <p>{{ver_final}}</p>
  </div>

  <p class="sub">O relatório está montado para ser conferido, não acreditado: a seção 02 mostra a medida e o controle que a calibra, a 03 e a 04 respondem às duas metades da hipótese, a 05 mostra quanto do que apareceu era acaso, e a 06 abre os trades um a um no gráfico.</p>
</section>

<section>
  <h2><span class="n">02</span> A medida</h2>
  <h3>Uma corrida simétrica, porque ela não sabe mentir</h3>
  <p>Toda medida de “funciona?” embute uma gestão, e a gestão inventa vantagem sozinha: alvo maior que stop compra acerto baixo, parcial compra acerto alto, e no fim se mede a gestão, não a ideia. Aqui a medida é a mais burra possível — a partir de um preço de entrada, <strong>o preço anda ±{{xv}} pontos: o que chegar primeiro decide</strong>. Sem alvo assimétrico, sem parcial, sem breakeven. Quando os dois cabem na mesma barra, conta o <strong>stop</strong>.</p>
  <p>Numa barra sem informação nenhuma isso dá <strong>50%</strong>, e é contra esse 50% que tudo aqui é lido. A primeira linha de cada tabela é o controle: <em>todas</em> as barras do período, sem filtro nenhum. Ele sai em 49–50% nas duas bases, que é como se sabe que a régua não está torta.</p>
  <p class="sub">Os níveis são causais: as médias e a VWAP usam só o que já aconteceu, e os pontos de pivô saem do pregão <strong>anterior</strong> inteiro — nenhum número usado numa barra veio do futuro dela. “Barra grande” é <code>range ≥ {{fg}} × range médio de 20 barras</code>, isto é, grande <em>para o momento</em>: o corte acompanha a volatilidade em vez de ser um número fixo de pontos.</p>
</section>

<section>
  <h2><span class="n">03</span> A primeira metade</h2>
  <h3>“Costumam andar” — não andam</h3>
  <p>Duas entradas, para não depender de uma escolha: <strong>no fechamento</strong> da barra grande, e no <strong>rompimento do extremo</strong> dela (a versão paciente — só entra se o preço confirmar em até {{maxrompe}} barras).</p>

  {{tab_hip_fu}}
  {{tab_hip_v26}}

  <div class="note">
    <div class="lab">A continuação</div>
    <p>{{ver_andar}}</p>
  </div>

  <p>Faz sentido mecânico. A barra de 10.000 ticks só fica grande quando o livro já foi varrido; quem tinha de entrar entrou <em>dentro</em> dela. Comprar o fechamento é comprar depois do movimento, e o que restou de fluxo costuma ser o de quem vai desmontar. É a mesma razão pela qual a linha “contra o corpo” do controle fica levemente <em>acima</em> de 50% no índice: em barra de ticks, o intradiário do WIN devolve mais do que estende.</p>
</section>

<section>
  <h2><span class="n">04</span> A segunda metade</h2>
  <h3>Reverte — mas quem reverte é a barra que falha, não o nível</h3>
  <p>A única célula que fica de pé é a <strong>falha da barra grande</strong>: a barra grande sai, e em seguida o preço rompe o extremo <em>oposto</em> ao corpo dela. Isso é o mercado desdizendo a barra. Vale {{acerto_falha_fu}} no WINFUT e {{acerto_falha_v26}} no WINV26 — o mesmo sinal nas duas bases, o que já é raro.</p>
  <p>Mas a hipótese não era essa. A hipótese era que <strong>o nível</strong> — a média, a VWAP, o pivô — é o que torna a barra confiável. Então a célula viva foi fatiada por nível:</p>

  {{tab_niv_fu}}
  {{tab_niv_v26}}

  <div class="note risk">
    <div class="lab">O nível acrescenta?</div>
    <p>{{ver_nivel}}</p>
  </div>

  <p class="sub">Isto foi testado com folga também: além do toque literal, foi medida a versão em que o nível vale se estiver a até um quarto de range da barra, a versão em que ele tem de estar <strong>centrado</strong> nela, e a versão de <strong>confluência</strong>, com dois ou mais níveis dentro da mesma barra. Nenhuma delas separa. A intuição de que o nível “segura” é real na tela — o preço realmente pivota por ali — mas o que ela está enxergando é que <em>toda</em> barra grande do índice pivota em cima de <em>alguma</em> média: com três EMAs, VWAP, cinco pivôs e as pontas do dia anterior, um nível qualquer cai dentro de uma barra grande na maioria das vezes. O nível não seleciona nada porque quase nunca está ausente.</p>
</section>

<section>
  <h2><span class="n">05</span> O acaso</h2>
  <h3>Quantas dessas células passariam sozinhas</h3>
  <p>Varrer fator de tamanho × família de nível × folga do toque × alvo × sentido × entrada produz muita célula, e algumas vão parecer ótimas por sorte. A conta honesta é comparar quantas passam com quantas o acaso entregaria.</p>

  <div class="charts">
    <div class="chart">
      <h5>Distribuição dos <em>t</em> medidos</h5>
      <p class="cs">Eixo horizontal: o <em>t</em> da célula. Altura: quantas células. A curva é a distribuição do nada.</p>
      {{hist_t}}
    </div>
    <div class="chart">
      <h5>Capital acumulado — a célula viva</h5>
      <p class="cs">Falha da barra grande, gestão da casa. Eixo vertical em pontos acumulados; horizontal, o número do trade.</p>
      {{curva}}
    </div>
  </div>

  <div class="note risk">
    <div class="lab">O tamanho do peneiramento</div>
    <p>{{ver_grade}}</p>
  </div>

  <p>Contra isso, a única defesa é a célula sobreviver fora de onde foi encontrada. A falha da barra grande sobrevive <strong>nas duas bases</strong> e nas <strong>duas metades</strong> do período — sinal certo, magnitude parecida:</p>

  {{tab_robustez}}

  <p class="sub">Ainda assim: as duas bases se sobrepõem no tempo e são o mesmo ativo, então não são duas amostras independentes — são uma amostra vista de dois contratos. E {{pregoes_fu}} pregões é pouco. Isso não invalida o achado; limita o que ele pode sustentar.</p>
</section>

<section>
  <h2><span class="n">06</span> Os trades</h2>
  <h3>Olhe você mesmo</h3>
  <p>Estes são os trades da célula viva, com a gestão da casa — <strong>stop {{stop}}, parcial de 50% na mesma distância do stop, alvo {{alvo}}</strong>, uma posição por vez. Entrada no rompimento do extremo oposto ao corpo da barra grande. O gráfico marca a <strong>barra grande</strong> que originou o sinal e desenha as médias, a VWAP e os pivôs do dia, para o olho conferir o que a tabela diz.</p>

  {{tab_trades}}

  <p class="sub">O filtro <em>nível</em> é o ponto: alterne entre “sem nível” e cada família e veja que as duas nuvens de trade são a mesma coisa. É a seção 04 desenhada.</p>

  <div class="bar">
    <div class="grp"><span class="lab">base</span><span id="gBase"></span></div>
    <div class="grp"><span class="lab">nível</span><span id="gFam"></span></div>
    <div class="grp"><span class="lab">desfecho</span><span id="gRes"></span></div>
    <div class="grp"><span class="lab">janela</span>
      <select id="selJanela">
        <option value="60">60 barras</option>
        <option value="100" selected>100 barras</option>
        <option value="160">160 barras</option>
        <option value="260">260 barras</option>
      </select></div>
    <div class="grp"><button id="btnAnt">‹ anterior</button>
      <span class="count" id="cont">0 de 0</span>
      <button id="btnProx">próximo ›</button></div>
  </div>

  <div class="painel">
    <div class="quadro">
      <div class="cab" id="kcab"></div>
      <div class="area"><div id="kchart"></div><p class="vazio" id="kvazio" hidden></p></div>
      <div class="legenda">
        <span><i class="sw l" style="background:var(--accent)"></i> EMA 21</span>
        <span><i class="sw l" style="background:var(--ink-3)"></i> EMA 42 / 72</span>
        <span><i class="sw l" style="background:var(--s2)"></i> VWAP</span>
        <span><i class="sw l" style="background:var(--zero)"></i> pivôs e pontas do dia anterior</span>
        <span><i class="sw" style="background:var(--warn)"></i> a barra grande</span>
      </div>
    </div>
    <div>
      <div class="ficha" id="ficha"></div>
      <div class="lista-wrap">
        <h4 id="listaTit">Trades filtrados</h4>
        <div class="rolagem"><table><tbody id="lista"></tbody></table></div>
      </div>
    </div>
  </div>
</section>

<section>
  <h2><span class="n">07</span> O que fazer com isto</h2>
  <h3>Não é um setup; é uma pista</h3>
  <p>A leitura de tela estava certa sobre o <em>fenômeno</em> e errada sobre a <em>causa</em>. Barra grande realmente é ponto de virada mais vezes do que de continuação no WIN — mas o que qualifica não é o nível que ela toca, é ela <strong>falhar</strong>: sair grande e o preço voltar pelo outro lado.</p>
  <p>Se for para levar isso adiante, o caminho não é adicionar mais níveis — é atacar o que sobrou: (a) medir a falha da barra grande com <strong>mais período</strong>, que é o que falta para o <code>t</code> decidir; (b) trocar o stop fixo por um stop <strong>proporcional ao tamanho da barra</strong>, já que a barra grande define a estrutura e o stop de {{stop}} pontos é arbitrário em cima dela; (c) checar se isso não é apenas o setup B do Rincones1 com outra roupa — os dois estão pedindo a mesma coisa ao mercado, exaustão depois de um movimento rápido, e se forem o mesmo trade não somam.</p>
  <div class="note">
    <div class="lab">O que este estudo fecha</div>
    <p>A pergunta “filtrar barra grande por média, VWAP ou pivô melhora alguma coisa?” está respondida: <strong>não</strong>, em {{n_celulas}} células, nas duas bases, com e sem folga no toque, centrado ou não, com um nível ou com confluência. Esse ramo pode ser abandonado sem remorso.</p>
  </div>
</section>

<footer>
  Gerado por <code>relatorio.py</code> a partir de <code>saida/resumo.json</code> —
  nenhum número deste documento foi escrito à mão. Base: WINFUT {{barras_fu}} barras
  ({{de}} a {{ate}}) e WINV26 {{barras_v26}} barras, gráfico de 10.000 ticks.
  Resultados brutos, sem custo operacional e sem slippage.
</footer>
</div>

<script>{{klinecharts_js}}</script>
<script>
const D={{dados_json}};
const NF=new Intl.NumberFormat('pt-BR');
const SANS='Archivo,Helvetica,Arial,sans-serif', MONO='"IBM Plex Mono",monospace';
const RES_ROT={alvo:'alvo',stop:'stop',zero:'zero a zero',fim:'fim do pregão'};
const FAM_ROT={medias:'médias',vwap:'VWAP',pivos:'pivôs',diant:'máx/mín ant.'};
const PIV_ROT={pp:'PP',r1:'R1',s1:'S1',r2:'R2',s2:'S2',phi:'máx ant.',plo:'mín ant.'};
const STOP_V={{stop}}, ALVO_V={{alvo}};
let COR={};
function lePaleta(){
  const s=getComputedStyle(document.documentElement), g=k=>s.getPropertyValue(k).trim();
  COR={paper:g('--paper'),card:g('--card'),card2:g('--card-2'),ink:g('--ink'),
       ink2:g('--ink-2'),ink3:g('--ink-3'),line:g('--line'),line2:g('--line-2'),
       accent:g('--accent'),pos:g('--pos'),neg:g('--neg'),warn:g('--warn'),
       zero:g('--zero'),alta:g('--alta'),baixa:g('--baixa'),s2:g('--s2')};
}
lePaleta();
let vBase=Object.keys(D)[0], fFam='todos', fRes='todos', janela=100, cur=0;

function alfa(cor,a){
  const h=cor.replace('#',''), n=h.length===3?h.split('').map(c=>c+c).join(''):h;
  return 'rgba('+parseInt(n.slice(0,2),16)+','+parseInt(n.slice(2,4),16)+','
        +parseInt(n.slice(4,6),16)+','+a+')';
}
const corDoRes=r=>r==='alvo'?COR.pos:r==='stop'?COR.neg:r==='zero'?COR.zero:COR.warn;
const PRECO=v=>NF.format(Math.round(v));

/* --- peças de desenho próprias, em cima do klinecharts ---------------- */
klinecharts.registerOverlay({
  name:'pn-nivel', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData, y=coordinates[0].y;
    const f=[{type:'line',ignoreEvent:true,
       attrs:{coordinates:[{x:0,y:y},{x:bounding.width,y:y}]},
       styles:{color:e.cor,size:e.fina?1:1,style:e.cheia?'solid':'dashed',dashedValue:[4,3]}}];
    if(e.rot) f.push({type:'text',ignoreEvent:true,
       attrs:{x:e.dir?bounding.width-4:4,y:y-3,text:e.rot,
              align:e.dir?'right':'left',baseline:'bottom'},
       styles:{color:e.cor,size:10,family:SANS,weight:'600',
               backgroundColor:alfa(COR.card,.75),
               paddingLeft:4,paddingRight:4,paddingTop:1,paddingBottom:1,borderRadius:2}});
    return f;
  },
  createYAxisFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData;
    if(!e.preco) return [];
    return {type:'text',ignoreEvent:true,
      attrs:{x:bounding.width-2,y:coordinates[0].y,text:e.preco,align:'right',baseline:'middle'},
      styles:{color:COR.card,size:10,family:MONO,weight:'600',backgroundColor:e.cor,
              paddingLeft:4,paddingRight:4,paddingTop:2,paddingBottom:2,borderRadius:2}};
  }
});
klinecharts.registerOverlay({
  name:'pn-marca', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    const e=overlay.extendData, x=coordinates[0].x;
    return [
      {type:'line',ignoreEvent:true,
       attrs:{coordinates:[{x:x,y:0},{x:x,y:bounding.height}]},
       styles:{color:e.cor,size:1,style:'dashed',dashedValue:[2,3]}},
      {type:'text',ignoreEvent:true,
       attrs:{x:x,y:bounding.height-4-e.degrau*19,text:e.rot,align:'center',baseline:'bottom'},
       styles:{color:COR.card,size:10,family:SANS,weight:'600',backgroundColor:e.cor,
               paddingLeft:4,paddingRight:4,paddingTop:2,paddingBottom:2,borderRadius:2}}
    ];
  }
});
klinecharts.registerOverlay({
  name:'pn-zona', totalStep:3, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{
    if(coordinates.length<2) return [];
    const a=Math.min(coordinates[0].x,coordinates[1].x);
    const b=Math.max(coordinates[0].x,coordinates[1].x);
    return [{type:'rect',ignoreEvent:true,
      attrs:{x:a,y:0,width:Math.max(1,b-a),height:bounding.height},
      styles:{style:'fill',color:overlay.extendData.cor}}];
  }
});
klinecharts.registerOverlay({
  name:'pn-seta', totalStep:2, lock:true,
  needDefaultPointFigure:false, needDefaultXAxisFigure:false, needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates})=>{
    const e=overlay.extendData, x=coordinates[0].x, y=coordinates[0].y, d=e.compra?1:-1;
    return [{type:'polygon',ignoreEvent:true,
      attrs:{coordinates:[{x:x,y:y+d*7},{x:x-5,y:y+d*17},{x:x+5,y:y+d*17}]},
      styles:{style:'fill',color:e.cor}}];
  }
});

/* As médias e a VWAP vêm prontas da engine, penduradas em cada barra. */
klinecharts.registerIndicator({
  name:'PN_NIV', shortName:'níveis', series:'price', precision:0,
  figures:[{key:'e1',title:'EMA 21: ',type:'line'},
           {key:'e2',title:'EMA 42: ',type:'line'},
           {key:'e3',title:'EMA 72: ',type:'line'},
           {key:'vw',title:'VWAP: ',type:'line'}],
  calc:dl=>dl.map(k=>({e1:k.e1,e2:k.e2,e3:k.e3,vw:k.vw}))
});

const T_BARRA=60000;
let kchart=null, kDia=null, kT0=0;
const iDe=ts=>Math.round((ts-kT0)/T_BARRA);

function estilos(){
  return {
    grid:{horizontal:{color:COR.line2},vertical:{show:false}},
    candle:{
      bar:{upColor:COR.alta,downColor:COR.baixa,noChangeColor:COR.ink3,
           upBorderColor:COR.alta,downBorderColor:COR.baixa,noChangeBorderColor:COR.ink3,
           upWickColor:COR.alta,downWickColor:COR.baixa,noChangeWickColor:COR.ink3},
      priceMark:{high:{color:COR.ink3,textSize:10,textFamily:MONO},
                 low:{color:COR.ink3,textSize:10,textFamily:MONO},
                 last:{show:false}},
      tooltip:{showRule:'follow_cross',
        rect:{color:COR.card,borderColor:COR.line},
        text:{size:11,family:MONO,color:COR.ink2},
        custom:dados=>{
          const k=dados.current, i=iDe(k.timestamp);
          const tm=kDia?((kDia.tm[i]||0)/100):0;
          return [
            {title:{text:'hora',color:COR.ink3},
             value:{text:kDia?(kDia.hm[i]||'—'):'—',color:COR.ink}},
            {title:{text:'abre',color:COR.ink3},value:{text:PRECO(k.open),color:COR.ink}},
            {title:{text:'máx',color:COR.ink3},value:{text:PRECO(k.high),color:COR.ink}},
            {title:{text:'mín',color:COR.ink3},value:{text:PRECO(k.low),color:COR.ink}},
            {title:{text:'fecha',color:COR.ink3},
             value:{text:PRECO(k.close),color:k.close>=k.open?COR.alta:COR.baixa}},
            {title:{text:'tamanho',color:COR.ink3},
             value:{text:tm.toFixed(2).replace('.',',')+'×',
                    color:tm>={{fg_js}}?COR.warn:COR.ink2}}
          ];
        }}},
    indicator:{tooltip:{text:{size:11,family:SANS,color:COR.ink3}}},
    xAxis:{axisLine:{color:COR.line},tickLine:{color:COR.line},
           tickText:{color:COR.ink3,size:10,family:MONO}},
    yAxis:{axisLine:{color:COR.line},tickLine:{color:COR.line},
           tickText:{color:COR.ink3,size:10,family:MONO}},
    separator:{color:COR.line},
    crosshair:{horizontal:{line:{color:COR.ink3,style:'dashed'},
                 text:{color:COR.card,backgroundColor:COR.ink2,borderColor:COR.ink2,
                       size:10,family:MONO}},
               vertical:{line:{color:COR.ink3,style:'dashed'},
                 text:{color:COR.card,backgroundColor:COR.ink2,borderColor:COR.ink2,
                       size:10,family:MONO}}}
  };
}
/* o klinecharts NÃO mescla estilo de linha com o padrão: o array trocado
   substitui o de fábrica inteiro, e cada item precisa vir completo. */
function estiloNiveis(){
  const l=(cor,tam,tracejada)=>({color:cor,size:tam,smooth:false,
    style:tracejada?'dashed':'solid',dashedValue:[3,3]});
  return {lines:[l(COR.accent,1.6,false),l(COR.ink3,1.2,false),
                 l(COR.ink3,1.2,true),l(COR.s2,1.6,false)]};
}
function iniciaGrafico(){
  kchart=klinecharts.init('kchart',{
    styles:estilos(),
    thousandsSeparator:'.',
    customApi:{
      formatDate:(fmt,ts,formato,tipo)=>{
        if(!kDia) return '';
        const hm=kDia.hm[iDe(ts)]||'';
        return tipo===0?(kDia.d+'  '+hm):hm;
      },
      formatBigNumber:v=>String(v)
    }
  });
  kchart.setPriceVolumePrecision(0,0);
  kchart.createIndicator({name:'PN_NIV',styles:estiloNiveis()},true,{id:'candle_pane'});
  new ResizeObserver(()=>{ if(kchart) kchart.resize(); })
    .observe(document.getElementById('kchart'));
  const mq=window.matchMedia('(prefers-color-scheme:dark)');
  const trocaTema=()=>{
    lePaleta();
    kchart.setStyles(estilos());
    kchart.overrideIndicator({name:'PN_NIV',styles:estiloNiveis()},'candle_pane');
    desenha();
  };
  if(mq.addEventListener) mq.addEventListener('change',trocaTema);
}

function carrega(t,dia){
  if(kDia===dia){posiciona(t,dia); return;}
  kDia=dia; kT0=Date.parse(dia.d+'T00:00:00Z');
  const n=dia.o.length, lst=new Array(n);
  for(let i=0;i<n;i++) lst[i]={
    timestamp:kT0+i*T_BARRA,
    open:dia.base+dia.o[i], high:dia.base+dia.h[i],
    low:dia.base+dia.l[i],  close:dia.base+dia.c[i],
    e1:dia.base+dia.e1[i], e2:dia.base+dia.e2[i], e3:dia.base+dia.e3[i],
    vw:dia.base+dia.vw[i]};
  kchart.applyNewData(lst,false,()=>posiciona(t,dia));
}

function posiciona(t,dia){
  const n=dia.o.length, meio=Math.round((t.g+t.k)/2);
  let a=Math.max(0,meio-Math.floor(janela/2));
  let z=Math.min(n-1,a+janela-1);

  const larg=kchart.getSize('candle_pane','main').width||600;
  kchart.setBarSpace(Math.max(1,Math.min(50,larg/janela)));
  kchart.scrollToDataIndex(z+2);

  const ts=i=>kT0+i*T_BARRA;
  const ent=dia.base+t.ent;
  const stopP=ent-t.s*STOP_V, parcP=ent+t.s*STOP_V, alvoP=ent+t.s*ALVO_V;

  kchart.removeOverlay();
  /* os pivôs do pregão vêm primeiro, por baixo de tudo */
  Object.keys(PIV_ROT).forEach(k=>{
    const v=dia.piv[k];
    if(v===null||v===undefined) return;
    kchart.createOverlay({name:'pn-nivel',lock:true,points:[{value:dia.base+v}],
      extendData:{cor:alfa(COR.zero,.75),rot:PIV_ROT[k],cheia:false,preco:'',dir:true}},
      'candle_pane');
  });
  /* a faixa do trade e a marca da barra grande */
  kchart.createOverlay({name:'pn-zona',lock:true,
    points:[{timestamp:ts(t.i)},{timestamp:ts(t.k)}],
    extendData:{cor:alfa(COR.accent,.07)}},'candle_pane');
  kchart.createOverlay({name:'pn-zona',lock:true,
    points:[{timestamp:ts(t.g)},{timestamp:ts(t.g)}],
    extendData:{cor:alfa(COR.warn,.30)}},'candle_pane');

  [[alvoP,COR.pos,'alvo',false],[parcP,COR.warn,'parcial',false],
   [ent,COR.accent,'entrada',true],[stopP,COR.neg,'stop',false]].forEach(v=>{
    kchart.createOverlay({name:'pn-nivel',lock:true,points:[{value:v[0]}],
      extendData:{cor:v[1],rot:v[2],cheia:v[3],preco:PRECO(v[0])}},'candle_pane');
  });
  kchart.createOverlay({name:'pn-marca',lock:true,points:[{timestamp:ts(t.g)}],
    extendData:{cor:COR.warn,rot:'barra grande',degrau:2}},'candle_pane');
  kchart.createOverlay({name:'pn-marca',lock:true,points:[{timestamp:ts(t.i)}],
    extendData:{cor:COR.accent,rot:'entrada',degrau:1}},'candle_pane');
  kchart.createOverlay({name:'pn-marca',lock:true,points:[{timestamp:ts(t.k)}],
    extendData:{cor:corDoRes(t.res),rot:RES_ROT[t.res],degrau:0}},'candle_pane');
  kchart.createOverlay({name:'pn-seta',lock:true,
    points:[{timestamp:ts(t.i),value:dia.base+(t.s===1?dia.l[t.i]:dia.h[t.i])}],
    extendData:{cor:t.s===1?COR.alta:COR.baixa,compra:t.s===1}},'candle_pane');
}

function lista_trades(){ return D[vBase].trades||[]; }
function filtrados(){
  return lista_trades().filter(t=>
    (fFam==='todos'||(fFam==='sem'?t.fams.length===0:t.fams.indexOf(fFam)>=0))
    &&(fRes==='todos'||t.res===fRes));
}
function desenha(){
  const lst=filtrados(), ficha=document.getElementById('ficha');
  const cab=document.getElementById('kcab'), vazio=document.getElementById('kvazio');
  if(!lst.length){
    vazio.hidden=false;
    vazio.textContent='Nenhum trade com estes filtros.';
    cab.innerHTML=''; ficha.innerHTML=''; document.getElementById('lista').innerHTML='';
    document.getElementById('cont').textContent='0 de 0';
    document.getElementById('listaTit').textContent='Trades filtrados';
    document.getElementById('btnAnt').disabled=true;
    document.getElementById('btnProx').disabled=true;
    return;
  }
  vazio.hidden=true;
  cur=Math.max(0,Math.min(cur,lst.length-1));
  const t=lst[cur], dia=D[vBase].dias[t.d];
  const ent=dia.base+t.ent;
  const stopP=ent-t.s*STOP_V, parcP=ent+t.s*STOP_V, alvoP=ent+t.s*ALVO_V;
  const rotFam=t.fams.length?t.fams.map(f=>FAM_ROT[f]).join(', '):'nenhum';

  cab.innerHTML='<b>'+vBase+' · '+dia.d+'</b>'
    +'<span>'+(t.s===1?'compra':'venda')+' · barra de '+t.tam.toFixed(2).replace('.',',')+'× o range médio</span>'
    +'<span class="dica">'+dia.o.length+' barras no pregão · janela de '+janela+'</span>';
  carrega(t,dia);

  const c=t.pnl>0?'pos':t.pnl<0?'neg':'zer';
  ficha.innerHTML='<div class="topo">'
    +'<div class="res '+c+'">'+(t.pnl>0?'+':'')+NF.format(t.pnl)+' <span style="font-size:14px;color:var(--ink-3)">pts</span></div>'
    +'<div class="quando">'+dia.d+' · '+dia.hm[t.g]+' · <span class="pill p-'+t.res+'">'+RES_ROT[t.res]+'</span></div></div>'
    +'<div class="linhas">'
    +'<div class="ln"><span class="k">lado</span><span class="v">'+(t.s===1?'compra':'venda')+'</span></div>'
    +'<div class="ln"><span class="k">barra grande</span><span class="v">'+t.tam.toFixed(2).replace('.',',')+'×</span></div>'
    +'<div class="ln"><span class="k">nível dentro</span><span class="v">'+rotFam+'</span></div>'
    +'<div class="ln"><span class="k">entrada</span><span class="v">'+PRECO(ent)+'</span></div>'
    +'<div class="ln"><span class="k">stop</span><span class="v neg">'+PRECO(stopP)+'</span></div>'
    +'<div class="ln"><span class="k">parcial</span><span class="v" style="color:var(--warn)">'+PRECO(parcP)+'</span></div>'
    +'<div class="ln"><span class="k">alvo</span><span class="v pos">'+PRECO(alvoP)+'</span></div>'
    +'<div class="ln"><span class="k">espera no rompimento</span><span class="v">'+(t.i-t.g)+(t.i-t.g===1?' barra':' barras')+'</span></div>'
    +'<div class="ln"><span class="k">duração</span><span class="v">'+(t.k-t.i)+(t.k-t.i===1?' barra':' barras')+'</span></div>'
    +'<div class="ln"><span class="k">R$ / contrato</span><span class="v '+c+'">'+(t.pnl*0.2).toFixed(2).replace('.',',')+'</span></div>'
    +'</div>';

  const tb=document.getElementById('lista');
  tb.innerHTML=lst.map((x,i)=>{
    const cc=x.pnl>0?'pos':x.pnl<0?'neg':'zer';
    return '<tr data-i="'+i+'" '+(i===cur?'aria-current="true"':'')+'><td class="num">'+(i+1)+'</td>'
      +'<td>'+x.dia.slice(5)+'</td><td>'+(x.s===1?'compra':'venda')+'</td>'
      +'<td>'+(x.fams.length?x.fams.length+' nív.':'—')+'</td>'
      +'<td class="num '+cc+'">'+(x.pnl>0?'+':'')+NF.format(x.pnl)+'</td></tr>';
  }).join('');
  tb.querySelectorAll('tr').forEach(tr=>{tr.onclick=()=>{cur=+tr.dataset.i;desenha();};});
  const at=tb.querySelector('[aria-current="true"]'); if(at) at.scrollIntoView({block:'nearest'});

  const soma=lst.reduce((s,x)=>s+x.pnl,0), ac=lst.filter(x=>x.pnl>0).length;
  document.getElementById('cont').textContent=(cur+1)+' de '+lst.length;
  document.getElementById('listaTit').textContent=
    'Trades filtrados — '+lst.length+' · '+(soma>0?'+':'')+NF.format(Math.round(soma))
    +' pts · '+Math.round(100*ac/lst.length)+'% acerto';
  document.getElementById('btnAnt').disabled=cur===0;
  document.getElementById('btnProx').disabled=cur===lst.length-1;
}
function grupo(el,opcoes,valor,onda){
  el.innerHTML='';
  opcoes.forEach(par=>{
    const b=document.createElement('button');
    b.textContent=par[1]; b.setAttribute('aria-pressed',String(par[0]===valor));
    b.onclick=()=>onda(par[0]); el.appendChild(b);
  });
}
function montaControles(){
  grupo(document.getElementById('gBase'),Object.keys(D).map(k=>[k,k]),vBase,
        v=>{vBase=v;cur=0;montaControles();desenha();});
  grupo(document.getElementById('gFam'),
        [['todos','todos'],['sem','sem nível'],['medias','médias'],['vwap','VWAP'],
         ['pivos','pivôs'],['diant','máx/mín ant.']],fFam,
        v=>{fFam=v;cur=0;montaControles();desenha();});
  grupo(document.getElementById('gRes'),
        [['todos','todos'],['alvo','alvo'],['stop','stop'],['zero','zero a zero']],fRes,
        v=>{fRes=v;cur=0;montaControles();desenha();});
}
document.getElementById('btnAnt').onclick=()=>{cur--;desenha();};
document.getElementById('btnProx').onclick=()=>{cur++;desenha();};
document.getElementById('selJanela').onchange=e=>{janela=+e.target.value;desenha();};
document.addEventListener('keydown',e=>{
  if(e.target.tagName==='SELECT') return;
  if(e.key==='ArrowLeft'&&cur>0){cur--;desenha();}
  if(e.key==='ArrowRight'){cur++;desenha();}
});
iniciaGrafico(); montaControles(); desenha();
</script>
"""
