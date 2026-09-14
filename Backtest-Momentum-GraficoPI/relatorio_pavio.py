# -*- coding: utf-8 -*-
"""
Monta pavio_contra.html e PAVIO_CONTRA.md a partir de saida/pavio_contra.json.

    python pavio_contra.py && python relatorio_pavio.py

Reaproveita o CSS e o kit de graficos SVG de molde.py e o klinecharts de
vendor/. O html sai offline, num arquivo so.
"""
import json
import os

import molde

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, 'saida')
VENDOR_KC = os.path.join(BASE, 'vendor', 'klinecharts-9.8.10.min.js')

GESTOES_JS = {'parcial': dict(stop=100, alvo=300, parcial=True, parcial_em=100),
              'puro': dict(stop=100, alvo=300, parcial=False, parcial_em=100),
              'r2': dict(stop=100, alvo=200, parcial=False, parcial_em=100),
              'r1': dict(stop=100, alvo=100, parcial=False, parcial_em=100)}


# ------------------------------------------------------------- formatacao
def n(v, c=0):
    if v is None:
        return '&ndash;'
    return f'{v:,.{c}f}'.replace(',', ' ').replace('.', ',').replace(' ', '.')


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


def md_n(v, c=0):
    return n(v, c).replace('&ndash;', '-')


def md_sn(v, c=0):
    return sn(v, c).replace('&ndash;', '-')


# ================================================================= numeros
def fatos(D):
    """Os numeros que o texto cita, tirados do json -- nunca digitados."""
    cp = D['comparacao']
    F = {}
    F['pad'] = cp['fecha|parcial']['padrao']
    F['sem'] = cp['fecha|parcial']['sem_filtro']
    F['fora'] = cp['fecha|parcial']['fora']
    F['inv'] = cp['fecha|parcial']['inverso']
    F['pct'] = [D['sorteio'][f'fecha|{g}']['percentil']
                for g in ('parcial', 'puro', 'r2', 'r1')]
    fx = {b['faixa']: b for b in D['faixas_pavio']['fecha|parcial']}
    F['fx'] = fx
    F['fxc'] = {b['faixa']: b for b in D['faixas_pavio']['fecha|parcial|compra']}
    F['fxv'] = {b['faixa']: b for b in D['faixas_pavio']['fecha|parcial|venda']}
    F['nb'] = {b['faixa']: b for b in D['barras_antes']['fecha|parcial']}
    F['lados'] = D['lados']['fecha|parcial']
    F['cart_r1'] = D['carteira']['fecha|r1|padrao']
    F['cart_p'] = D['carteira']['fecha|parcial|padrao']
    F['custo'] = D['custo']['fecha|parcial']
    F['ev_max'] = max(cp[k]['padrao']['ev'] for k in cp if cp[k]['padrao']['n'])
    return F


# =================================================================== corpo
def capa(D, F):
    B = D['base']
    return f"""
<header class="capa">
  <div class="chapeu">Backtest &middot; WINFUT &middot; grafico de 20 PI</div>
  <h1>Pavio contra<br>o indicador magenta</h1>
  <p class="sub">2 a 4 candles num sentido, depois 1 candle contra com o pavio do lado
  de onde veio o movimento, de 25% a 90% do corpo. O sinal e a favor do candle contra.
  A pergunta: <b>esses pavios fazem sentido?</b></p>
  <div style="margin-top:18px">
    <span class="selo">{n(B['barras'])} candles</span>
    <span class="selo">{B['dias']} pregoes, {B['ini']} a {B['fim']}</span>
    <span class="selo">{n(F['pad']['n'])} sinais no padrao</span>
    <span class="selo">sem Hull, sem EMA</span>
    <span class="selo">resultado bruto</span>
  </div>
</header>"""


def veredito(D, F):
    pct = F['pct']
    return f"""
<section id="veredito">
  <h2>Resposta curta: nao</h2>
  <p class="olho">O filtro de pavio 25&ndash;90% <b>piora</b> o sinal em vez de melhorar.
  Tirado do mesmo conjunto de candles contra depois de 2 a 4 barras, o padrao rende
  <b>{sn(F['pad']['ev'], 1)}</b> pts por sinal; o conjunto inteiro, sem olhar pavio, rende
  <b>{sn(F['sem']['ev'], 1)}</b>; e o que o filtro joga fora rende
  <b>{sn(F['fora']['ev'], 1)}</b>. Entrada no fechamento, 1:3 com parcial.</p>
  <div class="grade g4">
    {tile('Padrao (pavio 25-90%)', sn(F['pad']['ev'], 1), f"pts por sinal &middot; {n(F['pad']['n'])} sinais", cls(F['pad']['ev']))}
    {tile('Mesmo universo, sem filtro', sn(F['sem']['ev'], 1), f"pts por sinal &middot; {n(F['sem']['n'])} sinais", cls(F['sem']['ev']))}
    {tile('O que o filtro descarta', sn(F['fora']['ev'], 1), f"pts por sinal &middot; {n(F['fora']['n'])} sinais", cls(F['fora']['ev']))}
    {tile('Percentil contra o sorteio', n(pct[0], 0), 'de 100 &middot; 50 = igual ao acaso')}
  </div>
  <div class="bandeira">
    <h3>O que sustenta a resposta</h3>
    <ul class="enx">
      <li><b>Contra o sorteio.</b> Sorteando 4.000 vezes subconjuntos do mesmo tamanho,
      o padrao fica no percentil {n(min(pct), 0)} a {n(max(pct), 0)} nas quatro gestoes
      com entrada no fechamento. Um filtro util ficaria acima de 95.</li>
      <li><b>As faixas de pavio andam ao contrario.</b> Pavios pequenos (1&ndash;25%)
      rendem, em geral, mais que os da faixa escolhida, e nenhuma faixa se sustenta nos
      tres tercos do periodo.</li>
      <li><b>Compra e venda discordam.</b> Na compra o pavio grande ajuda; na venda
      atrapalha. Um efeito real apareceria dos dois lados.</li>
      <li><b>O que sobra nao paga custo.</b> O melhor valor esperado entre todas as
      variantes medidas e {sn(F['ev_max'], 1)} pts brutos por sinal; a 10 pts de custo
      por operacao, o padrao na variante principal vai a {sn(F['custo']['10'], 1)}.</li>
    </ul>
  </div>
  <p class="nota">Como nenhuma variante e viavel, este estudo nao traz plano de
  trading.</p>
</section>"""


def metodo(D, F):
    return f"""
<section id="metodo">
  <h2>Como foi medido</h2>
  <p class="olho">Para testar um filtro nao basta medir o padrao pronto: e preciso
  medir o que existe <b>sem</b> o filtro e ver se ele separa alguma coisa.</p>
  <div class="grade g2">
    <div class="card">
      <h3>O universo</h3>
      <p>Todo candle que fecha contra depois de 1 ou mais candles no sentido oposto, no
      mesmo pregao: {n(F['pad']['n'] + F['fora']['n'])} com 2 a 4 barras antes (e mais os
      de 1 e de 5+, para a comparacao da contagem). Cada um recebe a leitura do
      indicador &mdash; barras antes, pavio do lado da abertura em % do corpo &mdash; e e
      resolvido <b>isoladamente</b>.</p>
      <p>O sinal e a favor do candle contra: baixa depois de altas = venda.</p>
    </div>
    <div class="card">
      <h3>A simulacao</h3>
      <p>A mesma engine do estudo Momentum: <code>engine.simula_trade</code>, convencao
      conservadora de caminho dentro do candle (o pavio contra se forma antes), zerando
      no fim do pregao. Stop de 100 pts.</p>
      <p>Duas entradas: <b>fechamento</b> do candle contra, e <b>limitada no meio do
      corpo</b> dele, valida por 1 barra. Quatro gestoes: 1:3 com parcial de 50% em +100
      (stop do restante na media), 1:3 sem parcial, 1:2 e 1:1.</p>
    </div>
  </div>
</section>"""


def controles(D, F):
    linhas = ''
    for ent in ('fecha', 'meio_lim'):
        for ges in ('parcial', 'puro', 'r2', 'r1'):
            c = D['comparacao'][f'{ent}|{ges}']
            s = D['sorteio'][f'{ent}|{ges}']

            def cel(b, c_=1):
                if not b.get('n'):
                    return '<td>n/a</td>'
                return (f'<td class="{cls(b["ev"])}">{sn(b["ev"], c_)} '
                        f'<small style="color:var(--mudo)">({n(b["n"])})</small></td>')
            linhas += (f'<tr><td>{D["rot_entrada"][ent]}</td>'
                       f'<td style="text-align:left">{D["rot_gestao"][ges]}</td>'
                       f'{cel(c["padrao"])}{cel(c["sem_filtro"])}{cel(c["fora"])}'
                       f'{cel(c["inverso"])}'
                       f'<td>{n(s["percentil"], 0)}</td></tr>')
    return f"""
<section id="controles">
  <h2>1. O padrao contra os controles</h2>
  <p class="olho">Valor esperado por sinal, em pontos brutos, cada sinal resolvido
  sozinho. Entre parenteses, quantos sinais.</p>
  <div class="card rolo">
    <table>
      <thead><tr><th>Entrada</th><th>Gestao</th><th>Padrao</th><th>2-4 barras, sem filtro</th>
      <th>Fora da faixa</th><th>Invertido</th><th>Percentil</th></tr></thead>
      <tbody>{linhas}</tbody>
    </table>
  </div>
  <p class="nota"><b>Invertido</b>: o mesmo sinal, operado a favor do movimento anterior
  em vez do candle contra. Ele mede pior que o padrao em todas as gestoes: o candle contra
  tem, sim, um pouco de informacao sobre a barra seguinte &mdash; mas o universo sem filtro
  tem a mesma informacao, entao ela nao vem do pavio. Na limitada o invertido nao
  existe (a ordem ficaria acima do mercado). <b>Percentil</b>: onde o padrao cai entre
  4.000 subconjuntos sorteados do universo 2&ndash;4 com o mesmo tamanho.</p>
</section>"""


def faixas(D, F):
    abas = ''.join(f'<button class="aba" data-g="{g}" aria-pressed="{str(g == "parcial").lower()}">'
                   f'{D["rot_gestao"][g]}</button>' for g in ('parcial', 'puro', 'r2', 'r1'))
    return f"""
<section id="faixas">
  <h2>2. O pavio, faixa por faixa</h2>
  <p class="olho">Candles contra depois de 2 a 4 barras, entrada no fechamento, separados
  pelo tamanho do pavio do lado da abertura, em % do corpo. As faixas <b>cheias</b> sao as
  que o indicador aceita; as <b>apagadas</b>, as que ele descarta.</p>
  <div class="abas" id="abas_faixa">{abas}</div>
  <div class="grade g2">
    <figure class="card"><h3>Valor esperado por faixa</h3><div id="g_faixa"></div>
      <figcaption>pts por sinal; passe o mouse para ver n e acerto</figcaption></figure>
    <figure class="card"><h3>A mesma faixa em cada terco do periodo</h3>
      <div class="legenda"><span><i class="chave q" style="background:var(--bronze)"></i>T1 ate {D['base']['c1']}</span>
      <span><i class="chave q" style="background:var(--prata)"></i>T2 ate {D['base']['c2']}</span>
      <span><i class="chave q" style="background:var(--ouro)"></i>T3</span></div>
      <div id="g_faixa_terco"></div></figure>
  </div>
  <figure class="card" style="margin-top:16px"><h3>Compra e venda separadas</h3>
    <div class="legenda"><span><i class="chave q" style="background:var(--ganho)"></i>compra
    (2-4 baixas, alta com pavio inferior)</span>
    <span><i class="chave q" style="background:var(--perda)"></i>venda
    (2-4 altas, baixa com pavio superior)</span></div>
    <div id="g_faixa_lado"></div>
    <figcaption>Na compra a faixa 25&ndash;90% rende mais que os pavios pequenos; na venda,
    menos. Os dois lados apontam para lados opostos &mdash; e o desenho de ruido, nao de
    regra.</figcaption></figure>
</section>"""


def barras_horas(D, F):
    return f"""
<section id="contagem">
  <h2>3. Barras antes e horario</h2>
  <p class="olho">Com o pavio na faixa 25&ndash;90%, entrada no fechamento, 1:3 com
  parcial. A contagem tem um achado mais firme que o pavio: <b>4 barras antes</b> mede
  {sn(F['nb']['4']['ev'], 1)} pts por sinal, contra {sn(F['nb']['2']['ev'], 1)} com 2 e
  {sn(F['nb']['3']['ev'], 1)} com 3.</p>
  <div class="grade g2">
    <figure class="card"><h3>Por barras no sentido anterior</h3><div id="g_nbar"></div></figure>
    <figure class="card"><h3>Por hora do sinal</h3><div id="g_horas"></div>
      <figcaption>10h e a abertura do mercado a vista</figcaption></figure>
  </div>
</section>"""


def operacoes(D, F):
    ab_e = ''.join(f'<button class="aba" data-e="{e}" aria-pressed="{str(e == "fecha").lower()}">'
                   f'{D["rot_entrada"][e]}</button>' for e in ('fecha', 'meio_lim'))
    ab_g = ''.join(f'<button class="aba" data-g="{g}" aria-pressed="{str(g == "parcial").lower()}">'
                   f'{D["rot_gestao"][g]}</button>' for g in ('parcial', 'puro', 'r2', 'r1'))
    return f"""
<section id="operacoes">
  <h2>4. A carteira, uma posicao por vez</h2>
  <p class="olho">Agora como na mesa: sinais que aparecem com posicao aberta sao
  descartados. Os botoes abaixo valem para as estatisticas, as curvas, as distribuicoes e o
  grafico trade a trade.</p>
  <div id="sel_var" style="position:sticky;top:44px;z-index:20;background:var(--plano);padding:8px 0">
    <div class="abas" id="abas_ent">{ab_e}</div>
    <div class="abas" id="abas_ges" style="margin-bottom:0">{ab_g}</div>
  </div>

  <h3 style="margin-top:22px">Estatisticas no formato MetaTrader 5</h3>
  <div class="card rolo"><table id="t_mt5"></table>
    <p class="nota">Em pontos do WINFUT, brutos. R$ para 1 contrato a R$ 0,20 por ponto.
    "Sem filtro" e a mesma carteira com todo candle contra depois de 2 a 4 barras, sem
    olhar o pavio.</p></div>

  <h3 style="margin-top:32px">Evolucao do patrimonio</h3>
  <figure class="card"><div class="legenda" id="leg_eq"></div><div id="g_eq"></div>
    <figcaption>eixo horizontal no tempo, de {D['base']['ini']} a {D['base']['fim']}</figcaption></figure>
  <figure class="card" style="margin-top:16px"><h3>As quatro gestoes do padrao, na entrada escolhida</h3>
    <div id="g_eq_ges"></div></figure>

  <h3 style="margin-top:32px">Distribuicoes</h3>
  <div class="grade g2">
    <figure class="card"><h3>Resultado por trade</h3><div id="g_pts"></div></figure>
    <figure class="card"><h3>Duracao</h3><div id="g_dur"></div>
      <figcaption>minutos entre a entrada e a saida</figcaption></figure>
    <figure class="card"><h3>MEP &mdash; maxima excursao positiva</h3><div id="g_mep"></div>
      <figcaption>ate onde o trade chegou a favor, em pts</figcaption></figure>
    <figure class="card"><h3>MEN &mdash; maxima excursao negativa</h3><div id="g_men"></div>
      <figcaption>ate onde o trade chegou contra, em pts</figcaption></figure>
  </div>
</section>

<section id="custo">
  <h2>5. Custo</h2>
  <p class="olho">Valor esperado do padrao por sinal com custo de ida e volta descontado.</p>
  <div class="card rolo"><table>{tabela_custo(D)}</table></div>
</section>

<section id="kline">
  <h2>6. Trade a trade</h2>
  <p class="olho">Carteira do padrao na variante escolhida acima. A faixa magenta e o candle
  contra &mdash; o que o indicador pinta &mdash;, a faixa clara sao as barras no sentido
  anterior. Setas do teclado navegam.</p>
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


def tabela_custo(D):
    cab = '<thead><tr><th>Entrada</th><th>Gestao</th><th>Bruto</th><th>5 pts</th><th>10 pts</th></tr></thead>'
    lin = ''
    for ent in ('fecha', 'meio_lim'):
        for ges in ('parcial', 'puro', 'r2', 'r1'):
            c = D['custo'][f'{ent}|{ges}']
            lin += (f'<tr><td>{D["rot_entrada"][ent]}</td><td style="text-align:left">'
                    f'{D["rot_gestao"][ges]}</td>'
                    + ''.join(f'<td class="{cls(c[k])}">{sn(c[k], 1)}</td>' for k in ('0', '5', '10'))
                    + '</tr>')
    return cab + '<tbody>' + lin + '</tbody>'


def conclusao(D, F):
    return f"""
<section id="conclusao">
  <h2>Conclusao</h2>
  <ul class="enx">
    <li><b>O pavio de 25&ndash;90% nao e filtro.</b> Ele seleciona candles que rendem um
    pouco <i>menos</i> que o conjunto de onde sairam, em todas as gestoes com entrada no
    fechamento, e nenhuma faixa de pavio e estavel nos tres tercos.</li>
    <li><b>No PI, esse pavio e o normal.</b> O pavio do lado da abertura aparece em quase
    todo candle (mediana de 35% do corpo); exigir 25&ndash;90% deixa passar
    {n(F['pad']['n'] / (F['pad']['n'] + F['fora']['n']) * 100, 0)}% dos candles contra
    depois de 2 a 4 barras. O que ele descarta sao sobretudo os pavios pequenos &mdash;
    justamente os que mediram melhor.</li>
    <li><b>Se algo merece ser olhado, e a contagem:</b> com 4 barras antes o sinal mede
    {sn(F['nb']['4']['ev'], 1)} pts. So que isso vem de uma base de 26 pregoes e nao foi
    confirmado fora dela.</li>
    <li><b>A diferenca entre compra e venda e o mercado, nao o padrao.</b> O periodo foi de
    alta: a compra rende {sn(F['lados']['compra']['ev'], 1)} e a venda
    {sn(F['lados']['venda']['ev'], 1)} &mdash; e sem filtro nenhum a diferenca ja e parecida
    ({sn(F['lados']['compra_sem']['ev'], 1)} contra {sn(F['lados']['venda_sem']['ev'], 1)}).</li>
    <li><b>Nenhuma variante paga custo.</b> O melhor valor esperado bruto por sinal e
    {sn(F['ev_max'], 1)} pts, e com a variante 1:1 a carteira faz
    {n(F['cart_r1']['trades'])} operacoes em {F['cart_r1']['dias']} pregoes: cerca de
    {n(F['cart_r1']['trades_dia'], 0)} por dia, cada uma pagando corretagem e
    escorregamento.</li>
  </ul>
  <p class="nota">Ressalva de sempre: 26 pregoes, um instrumento, um regime de mercado,
  resultado bruto. O estudo diz que o filtro nao funcionou <i>aqui</i>; nao prova que
  nenhum filtro de pavio funcione.</p>
</section>
<footer>Gerado por <code>pavio_contra.py</code> e <code>relatorio_pavio.py</code>.
Indicador: <code>ntsl/PavioContra_Magenta.ntsl</code>.</footer>"""


# ======================================================================= JS
JS = r"""
const bt=document.getElementById('btema');
function temaAtual(){const t=document.documentElement.dataset.tema;
  if(t==='claro'||t==='escuro') return t;
  return matchMedia('(prefers-color-scheme: dark)').matches?'escuro':'claro';}
bt.addEventListener('click',()=>{
  document.documentElement.dataset.tema=temaAtual()==='escuro'?'claro':'escuro';
  desenha(); pintaKline();});

let gFaixa='parcial', sEnt='fecha', sGes='parcial';
function grupoAbas(id,attr,fn){
  const g=document.getElementById(id);
  g.addEventListener('click',ev=>{const b=ev.target.closest('.aba'); if(!b) return;
    g.querySelectorAll('.aba').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
    fn(b.dataset[attr]);});
}
grupoAbas('abas_faixa','g',v=>{gFaixa=v; desenha();});
grupoAbas('abas_ent','e',v=>{sEnt=v; desenha(); trocaLista();});
grupoAbas('abas_ges','g',v=>{sGes=v; desenha(); trocaLista();});

const DENTRO=new Set(['25-45%','45-65%','65-90%']);
function extraB(b){return b.n?`<span class="l">n</span> ${b.n} &middot; <span class="l">acerto</span> ${fmt(b.wr,1)}%`:'';}

function histo(vals,passo,corFixa){
  if(!vals.length) return [];
  const lo=Math.floor(Math.min(...vals)/passo)*passo, hi=Math.ceil(Math.max(...vals)/passo)*passo;
  const k=Math.max(1,Math.round((hi-lo)/passo)), c=new Array(k).fill(0);
  vals.forEach(v=>{let i=Math.floor((v-lo)/passo); if(i>=k)i=k-1; if(i<0)i=0; c[i]++;});
  return c.map((q,i)=>({nome:fmt(lo+i*passo),v:q,cor:corFixa||((lo+i*passo)>=0?'ganho':'perda'),
    extra:'<span class="l">faixa</span> '+fmt(lo+i*passo)+' a '+fmt(lo+(i+1)*passo)+' pts'}));
}
function duracao(ds){
  const cortes=[0,60,180,300,600,1200,2400,1e12];
  const rot=['ate 1','1 a 3','3 a 5','5 a 10','10 a 20','20 a 40','40+'];
  const c=new Array(rot.length).fill(0);
  ds.forEach(s=>{for(let i=0;i<cortes.length-1;i++) if(s>=cortes[i]&&s<cortes[i+1]){c[i]++;break;}});
  return c.map((q,i)=>({nome:rot[i],v:q,cor:'prata'}));
}

const MT5=[
 ['Lucro liquido',s=>sinal(s.lucro_liq)+' pts','lucro_liq'],
 ['Lucro liquido (R$)',s=>'R$ '+sinal(s.lucro_liq_rs,2),'lucro_liq'],
 ['Lucro bruto',s=>fmt(s.lucro_bruto),null],
 ['Prejuizo bruto',s=>fmt(s.prej_bruto),null],
 ['Fator de lucro',s=>fmt(s.fator_lucro,2),null],
 ['Payoff esperado',s=>sinal(s.exp_pts,1)+' pts','exp_pts'],
 ['Fator de recuperacao',s=>fmt(s.recovery,2),null],
 ['Indice de Sharpe (por trade)',s=>fmt(s.sharpe,3),null],
 ['Correlacao LR',s=>fmt(s.lr_corr,2),null],
 ['Rebaixamento maximo',s=>fmt(s.dd_max)+' pts',null],
 ['Total de negociacoes',s=>fmt(s.trades),null],
 ['Winrate',s=>fmt(s.winrate,1)+'%',null],
 ['Zero a zero',s=>fmt(s.zeros)+' ('+fmt(s.zeros_pct,1)+'%)',null],
 ['Compras (acerto)',s=>fmt(s.longs)+' ('+fmt(s.longs_wr,1)+'%)',null],
 ['Vendas (acerto)',s=>fmt(s.shorts)+' ('+fmt(s.shorts_wr,1)+'%)',null],
 ['Pontos em compras',s=>sinal(s.longs_pts),'longs_pts'],
 ['Pontos em vendas',s=>sinal(s.shorts_pts),'shorts_pts'],
 ['Maior ganho / maior perda',s=>sinal(s.maior_ganho)+' / '+sinal(s.maior_perda),null],
 ['Ganho medio / perda media',s=>sinal(s.media_ganho,1)+' / '+sinal(s.media_perda,1),null],
 ['Maximo de ganhos seguidos',s=>fmt(s.max_seq_ganho),null],
 ['Maximo de perdas seguidas',s=>fmt(s.max_seq_perda),null],
 ['Negociacoes por dia',s=>fmt(s.trades_dia,1),null],
 ['Pontos por dia',s=>sinal(s.pts_dia,1),'pts_dia'],
 ['Duracao mediana',s=>fmt(s.dur_mediana/60,1)+' min',null],
 ['Saidas: alvo / stop / zero / fim do dia',s=>[s.alvos,s.stops,s.stops_zero,s.fins_dia+s.timeouts].map(x=>fmt(x)).join(' / '),null],
 ['Monte Carlo: chance de lucro',s=>s.mc&&s.mc.p_lucro!==undefined?fmt(s.mc.p_lucro,0)+'%':'-',null],
 ['Monte Carlo: rebaixamento p95',s=>s.mc&&s.mc.dd_p95!==undefined?fmt(s.mc.dd_p95)+' pts':'-',null],
];
function clsv(v){return v>0?'pos':(v<0?'neg':'');}

function desenha(){
  /* ---- faixas de pavio */
  const fx=D.faixas_pavio['fecha|'+gFaixa];
  barrasH('#g_faixa',fx.filter(b=>b.n).map(b=>({nome:b.faixa+(DENTRO.has(b.faixa)?' ●':''),v:b.ev,
    fraco:!DENTRO.has(b.faixa),extra:extraB(b)})),{rotV:'por sinal',casas:1,esq:90});
  grupos('#g_faixa_terco',fx.filter(b=>b.n).map(b=>({nome:b.faixa,v:b.ev_terco,n:b.n_terco})),
    ['T1','T2','T3'],{cores:['bronze','prata','ouro'],esq:90});
  const fc=D.faixas_pavio['fecha|'+gFaixa+'|compra'], fv=D.faixas_pavio['fecha|'+gFaixa+'|venda'];
  grupos('#g_faixa_lado',fc.map((b,i)=>({nome:b.faixa,v:[b.ev,fv[i].ev],n:[b.n,fv[i].n]})),
    ['compra','venda'],{cores:['ganho','perda'],esq:90});

  /* ---- contagem e hora */
  barrasH('#g_nbar',D.barras_antes['fecha|'+gFaixa].map(b=>({nome:b.faixa+' barra'+(b.faixa==='1'?'':'s'),
    v:b.ev,fraco:!['2','3','4'].includes(b.faixa),extra:extraB(b)})),{rotV:'por sinal',casas:1,esq:90});
  barrasH('#g_horas',D.horas['fecha|'+gFaixa].filter(b=>b.n).map(b=>({nome:b.faixa,v:b.ev,extra:extraB(b)})),
    {rotV:'por sinal',casas:1,esq:60});

  /* ---- MT5 */
  const kp=sEnt+'|'+sGes+'|padrao', ks=sEnt+'|'+sGes+'|sem_filtro';
  const sp=D.carteira[kp], ss=D.carteira[ks];
  document.getElementById('t_mt5').innerHTML=
    '<thead><tr><th>Estatistica</th><th>Padrao</th><th>Sem filtro de pavio</th></tr></thead><tbody>'+
    MT5.map(r=>`<tr><td>${r[0]}</td><td class="${r[2]?clsv(sp[r[2]]):''}">${sp.trades?r[1](sp):'-'}</td>`+
      `<td class="${r[2]?clsv(ss[r[2]]):''}">${ss.trades?r[1](ss):'-'}</td></tr>`).join('')+'</tbody>';

  /* ---- patrimonio */
  linhas('#g_eq',[
    {nome:'Padrao',cor:'ouro',dados:sp.equity,xs:sp.xs,dt:sp.dt,area:true},
    {nome:'Sem filtro',cor:'bronze',dados:ss.equity,xs:ss.xs,dt:ss.dt}],{alt:320});
  document.getElementById('leg_eq').innerHTML=
    '<span><i class="chave" style="background:var(--ouro)"></i>Padrao (pavio 25-90%)</span>'+
    '<span><i class="chave" style="background:var(--bronze)"></i>Sem filtro de pavio</span>';
  const cores={parcial:'ouro',puro:'prata',r2:'bronze',r1:'alerta'};
  linhas('#g_eq_ges',['parcial','puro','r2','r1'].map(g=>{const s=D.carteira[sEnt+'|'+g+'|padrao'];
    return s.trades?{nome:D.rot_gestao[g],cor:cores[g],dados:s.equity,xs:s.xs,dt:s.dt}:null;}).filter(Boolean),{alt:300});

  /* ---- distribuicoes */
  colunas('#g_pts',histo(sp.pts,50),{alt:230,rotula:true,rotV:'trades',un:'trades'});
  colunas('#g_mep',histo(sp.mfe,50,'ganho'),{alt:230,rotula:true,rotV:'trades',un:'trades'});
  colunas('#g_men',histo(sp.mae,25,'perda'),{alt:230,rotula:true,rotV:'trades',un:'trades'});
  colunas('#g_dur',duracao(sp.dur_s),{alt:230,rotula:true,rotV:'trades',un:'trades'});
}
addEventListener('resize',()=>{clearTimeout(window._rz);
  window._rz=setTimeout(()=>{desenha(); if(kchart) kchart.resize();},180);});

/* ================================================================ kline */
const SANS='system-ui,-apple-system,"Segoe UI",sans-serif';
const MAGENTA='#ff00ff';
function c_(k){return getComputedStyle(document.documentElement).getPropertyValue('--'+k).trim();}
function alfa(hex,a){const h=hex.replace('#','').trim();
  const x=h.length===3?h.split('').map(y=>y+y).join(''):h; const i=parseInt(x,16);
  return 'rgba('+((i>>16)&255)+','+((i>>8)&255)+','+(i&255)+','+a+')';}

klinecharts.registerOverlay({name:'pc-nivel',totalStep:2,lock:true,
  needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{const e=overlay.extendData,y=coordinates[0].y;
    return [{type:'line',ignoreEvent:true,attrs:{coordinates:[{x:0,y:y},{x:bounding.width,y:y}]},
      styles:{color:e.cor,size:1,style:e.cheia?'solid':'dashed',dashedValue:[4,4]}},
     {type:'text',ignoreEvent:true,attrs:{x:4,y:y-3,text:e.rot,align:'left',baseline:'bottom'},
      styles:{color:e.cor,size:10,family:SANS,weight:'600',backgroundColor:alfa(c_('card'),.78),
      paddingLeft:4,paddingRight:4,paddingTop:1,paddingBottom:1,borderRadius:3}}];}});
klinecharts.registerOverlay({name:'pc-zona',totalStep:3,lock:true,
  needDefaultPointFigure:false,needDefaultXAxisFigure:false,needDefaultYAxisFigure:false,
  createPointFigures:({overlay,coordinates,bounding})=>{if(coordinates.length<2) return [];
    const a=Math.min(coordinates[0].x,coordinates[1].x), b=Math.max(coordinates[0].x,coordinates[1].x);
    const w=overlay.extendData.meia||0;
    return [{type:'rect',ignoreEvent:true,attrs:{x:a-w,y:0,width:Math.max(2,b-a+2*w),height:bounding.height},
      styles:{style:'fill',color:overlay.extendData.cor}}];}});

let kchart=null,kidx=0,KTR=[],KL=[];
const T0=Date.UTC(2000,0,1),TB=60000;
function estilo(){const g=c_('grade'),m=c_('mudo'),card=c_('card'),up=c_('ganho'),dn=c_('perda');
  return {grid:{horizontal:{color:g},vertical:{color:g}},
    candle:{bar:{upColor:up,downColor:dn,noChangeColor:m,upBorderColor:up,downBorderColor:dn,
      noChangeBorderColor:m,upWickColor:up,downWickColor:dn,noChangeWickColor:m},
      priceMark:{last:{show:false}},
      tooltip:{showRule:'follow_cross',text:{color:c_('tinta'),family:SANS,size:11},
        rect:{color:alfa(card,.94),borderColor:c_('eixo')}}},
    xAxis:{axisLine:{color:c_('eixo')},tickLine:{color:c_('eixo')},tickText:{color:m,family:SANS,size:11}},
    yAxis:{axisLine:{color:c_('eixo')},tickLine:{color:c_('eixo')},tickText:{color:m,family:SANS,size:11}},
    crosshair:{horizontal:{line:{color:m},text:{backgroundColor:c_('tinta2')}},
      vertical:{line:{color:m},text:{backgroundColor:c_('tinta2')}}}};}
function pintaKline(){if(!kchart) return; kchart.setStyles(estilo()); mostra_(kidx);}

function iniciaKline(){
  const C=D.candles,N=C.o.length;
  for(let i=0;i<N;i++) KL.push({timestamp:T0+i*TB,open:C.o[i],high:C.h[i],low:C.l[i],close:C.c[i],volume:0});
  kchart=klinecharts.init('kchart',{styles:estilo(),customApi:{formatDate:(f,ts,fm,tipo)=>{
    const i=Math.round((ts-T0)/TB); const s=(i>=0&&i<N)?C.dt[i]:''; return tipo===2?s.slice(6):s;}}});
  kchart.setPriceVolumePrecision(0,0);
  kchart.applyNewData(KL,false,()=>mostra_(0));
}
function mostra_(i){
  if(!kchart||!KTR.length) return;
  kidx=Math.max(0,Math.min(KTR.length-1,i)); const t=KTR[kidx], G=D.gestoes[sGes], ld=t.lado;
  kchart.removeOverlay();
  const de=Math.max(0,t.i-t.n_fav-20), ate=Math.min(KL.length-1,t.i_sai+12), jan=Math.max(14,ate-de+1);
  const larg=(kchart.getSize('candle_pane','main')||{}).width||760;
  const esp=Math.max(1.2,Math.min(40,larg/jan));
  kchart.setBarSpace(esp); kchart.scrollToDataIndex(ate+2);
  const meia=esp/2;
  kchart.createOverlay({name:'pc-zona',lock:true,points:[{timestamp:KL[t.i-t.n_fav].timestamp},
    {timestamp:KL[t.i-1].timestamp}],extendData:{cor:alfa(c_('prata'),.12),meia:meia}});
  kchart.createOverlay({name:'pc-zona',lock:true,points:[{timestamp:KL[t.i].timestamp},
    {timestamp:KL[t.i].timestamp}],extendData:{cor:alfa(MAGENTA,.22),meia:meia}});
  kchart.createOverlay({name:'pc-zona',lock:true,points:[{timestamp:KL[t.i_ent].timestamp},
    {timestamp:KL[t.i_sai].timestamp}],extendData:{cor:alfa(t.pts>=0?c_('ganho'):c_('perda'),.08),meia:meia}});
  const nv=[{v:t.ent,rot:'entrada '+fmt(t.ent),cor:c_('tinta'),cheia:true},
    {v:t.ent-ld*G.stop,rot:'stop',cor:c_('perda'),cheia:true},
    {v:t.ent+ld*G.alvo,rot:'alvo +'+G.alvo,cor:c_('ganho'),cheia:true}];
  if(G.parcial) nv.push({v:t.ent+ld*G.parcial_em,rot:'parcial +'+G.parcial_em,cor:c_('ganho'),cheia:false});
  nv.forEach(L=>kchart.createOverlay({name:'pc-nivel',lock:true,points:[{timestamp:KL[t.i_ent].timestamp,value:L.v}],extendData:L}));
  document.getElementById('ksel').value=String(kidx);
  const ROT={alvo:'alvo',stop:'stop',stop_zero:'zero a zero',timeout:'tempo',fim_dia:'fim do dia'};
  document.getElementById('kinfo').innerHTML=
    `<span><b>#${kidx+1}</b> de ${KTR.length}</span><span>${t.data}</span>`+
    `<span><b style="color:${MAGENTA}">${ld>0?'▲ compra':'▼ venda'}</b></span>`+
    `<span>${t.n_fav} barras antes &middot; pavio <b>${fmt(t.pav,0)}%</b> do corpo</span>`+
    `<span>entrada <b>${fmt(t.ent)}</b></span><span>saida <b>${fmt(t.sai)}</b> (${ROT[t.motivo]||t.motivo})</span>`+
    `<span>resultado <b class="${clsv(t.pts)}">${sinal(t.pts)} pts</b></span>`+
    `<span>MEP <b>${sinal(t.mfe)}</b> &middot; MEN <b>${sinal(t.mae)}</b></span>`;
}
function trocaLista(){
  KTR=D.trades[sEnt+'|'+sGes]||[];
  document.getElementById('ksel').innerHTML=KTR.map((t,i)=>
    `<option value="${i}">#${i+1} · ${t.data} · ${t.lado>0?'compra':'venda'} · ${sinal(t.pts)} pts</option>`).join('');
  mostra_(0);
}
document.getElementById('ksel').addEventListener('change',e=>mostra_(+e.target.value));
document.getElementById('kant').addEventListener('click',()=>mostra_(kidx-1));
document.getElementById('kprox').addEventListener('click',()=>mostra_(kidx+1));
function busca(f){for(let k=kidx+1;k<KTR.length;k++) if(f(KTR[k])) return mostra_(k);
  for(let k=0;k<KTR.length;k++) if(f(KTR[k])) return mostra_(k);}
document.getElementById('kganho').addEventListener('click',()=>busca(t=>t.pts>0));
document.getElementById('kperda').addEventListener('click',()=>busca(t=>t.pts<0));
addEventListener('keydown',ev=>{if(['SELECT','BUTTON'].includes(ev.target.tagName)) return;
  if(ev.key==='ArrowLeft') mostra_(kidx-1); if(ev.key==='ArrowRight') mostra_(kidx+1);});

desenha();
KTR=D.trades['fecha|parcial'];
document.getElementById('ksel').innerHTML=KTR.map((t,i)=>
  `<option value="${i}">#${i+1} · ${t.data} · ${t.lado>0?'compra':'venda'} · ${sinal(t.pts)} pts</option>`).join('');
iniciaKline();
"""


HTML = r"""<!doctype html>
<html lang="pt-BR" data-tema="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pavio Contra Magenta</title>
<style>__CSS__</style>
</head>
<body>
<nav class="indice"><div class="wrap"><ul>__MENU__</ul></div></nav>
<div class="wrap">
__CORPO__
</div>
<button class="tema" id="btema" title="Alternar tema" aria-label="Alternar tema">&#9681;</button>
<script>__KLINE__</script>
<script>const D=__DADOS__;</script>
<script>__KIT__</script>
<script>__JS__</script>
</body>
</html>
"""

MENU = [('veredito', 'Resposta'), ('metodo', 'Metodo'), ('controles', 'Controles'),
        ('faixas', 'Faixas de pavio'), ('contagem', 'Barras e horario'),
        ('operacoes', 'Carteira'), ('custo', 'Custo'), ('kline', 'Trade a trade'),
        ('conclusao', 'Conclusao')]


# ======================================================================= MD
def markdown(D, F):
    L = []
    B = D['base']
    L += ['# Pavio contra -- o indicador magenta',
          '',
          f"Backteste do `ntsl/PavioContra_Magenta.ntsl` no WINFUT, grafico de 20 PI, "
          f"{n(B['barras'])} candles, {B['dias']} pregoes ({B['ini']} a {B['fim']}). "
          'Resultado bruto. Graficos, curvas de patrimonio, MEP/MEN, duracao e trade a '
          'trade em `pavio_contra.html`.',
          '',
          '**O padrao** (venda; compra e o espelho): 2 a 4 candles de alta, depois 1 de '
          'baixa com pavio superior de 25% a 90% do corpo. Sinal a favor do candle contra.',
          '',
          '## Resposta curta: nao',
          '',
          f"O filtro de pavio 25-90% **piora** o sinal. Entrada no fechamento, 1:3 com parcial:",
          '',
          '| Conjunto | Sinais | Pts por sinal |',
          '|:--|--:|--:|',
          f"| Padrao (pavio 25-90%) | {md_n(F['pad']['n'])} | {md_sn(F['pad']['ev'], 1)} |",
          f"| Mesmo universo (2-4 barras), sem filtro | {md_n(F['sem']['n'])} | {md_sn(F['sem']['ev'], 1)} |",
          f"| O que o filtro descarta | {md_n(F['fora']['n'])} | {md_sn(F['fora']['ev'], 1)} |",
          f"| Padrao invertido (a favor do movimento anterior) | {md_n(F['inv']['n'])} | {md_sn(F['inv']['ev'], 1)} |",
          '',
          f"- **Contra o sorteio:** entre 4.000 subconjuntos sorteados do mesmo universo, com o "
          f"mesmo tamanho, o padrao cai no percentil {md_n(min(F['pct']))} a {md_n(max(F['pct']))} "
          'nas quatro gestoes com entrada no fechamento. Um filtro util ficaria acima de 95.',
          '- **As faixas andam ao contrario:** pavios de 1-25% rendem, em geral, mais que os de 25-90%, e '
          'nenhuma faixa se sustenta nos tres tercos do periodo.',
          '- **Compra e venda discordam:** na compra o pavio grande ajuda, na venda atrapalha.',
          f"- **Nao paga custo:** o melhor valor esperado bruto entre todas as variantes e "
          f"{md_sn(F['ev_max'], 1)} pts; a 10 pts de custo a variante principal vai a "
          f"{md_sn(F['custo']['10'], 1)}.",
          '',
          'Nenhuma variante e viavel, entao nao ha plano de trading.',
          '',
          '## 1. Controles',
          '',
          '| Entrada | Gestao | Padrao | 2-4 sem filtro | Fora da faixa | Invertido | Percentil |',
          '|:--|:--|--:|--:|--:|--:|--:|']
    for ent in ('fecha', 'meio_lim'):
        for ges in ('parcial', 'puro', 'r2', 'r1'):
            c = D['comparacao'][f'{ent}|{ges}']; s = D['sorteio'][f'{ent}|{ges}']

            def cel(b):
                return f"{md_sn(b['ev'], 1)} ({md_n(b['n'])})" if b.get('n') else 'n/a'
            L.append(f"| {D['rot_entrada'][ent]} | {D['rot_gestao'][ges]} | {cel(c['padrao'])} | "
                     f"{cel(c['sem_filtro'])} | {cel(c['fora'])} | {cel(c['inverso'])} | "
                     f"{md_n(s['percentil'])} |")
    L += ['', 'Pts por sinal, cada sinal resolvido isoladamente; entre parenteses, o numero de '
          'sinais. Na limitada o invertido nao existe (a ordem ficaria acima do mercado).',
          '', '## 2. Faixas de pavio (2-4 barras antes, fechamento)', '']
    for ges in ('parcial', 'r1'):
        L += [f"**{D['rot_gestao'][ges]}**", '',
              '| Pavio | Sinais | Pts/sinal | Acerto | T1 | T2 | T3 | Compra | Venda |',
              '|:--|--:|--:|--:|--:|--:|--:|--:|--:|']
        fc = {b['faixa']: b for b in D['faixas_pavio'][f'fecha|{ges}|compra']}
        fv = {b['faixa']: b for b in D['faixas_pavio'][f'fecha|{ges}|venda']}
        for b in D['faixas_pavio'][f'fecha|{ges}']:
            if not b['n']:
                continue
            marca = ' *' if b['faixa'] in ('25-45%', '45-65%', '65-90%') else ''
            L.append(f"| {b['faixa']}{marca} | {md_n(b['n'])} | {md_sn(b['ev'], 1)} | "
                     f"{md_n(b['wr'], 1)}% | " + ' | '.join(md_sn(v, 1) for v in b['ev_terco'])
                     + f" | {md_sn(fc[b['faixa']]['ev'], 1)} | {md_sn(fv[b['faixa']]['ev'], 1)} |")
        L.append('')
    L += ['`*` = faixa aceita pelo indicador.', '',
          '## 3. Barras antes (pavio 25-90%, fechamento, 1:3 com parcial)', '',
          '| Barras | Sinais | Pts/sinal | Acerto |', '|:--|--:|--:|--:|']
    for b in D['barras_antes']['fecha|parcial']:
        L.append(f"| {b['faixa']} | {md_n(b['n'])} | {md_sn(b['ev'], 1)} | {md_n(b['wr'], 1)}% |")
    L += ['', '## 4. Carteira, uma posicao por vez (padrao)', '',
          '| Entrada | Gestao | Trades | Pts | R$ | Pts/trade | Acerto | Fator | Rebaix. | Sem filtro: pts |',
          '|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|']
    for ent in ('fecha', 'meio_lim'):
        for ges in ('parcial', 'puro', 'r2', 'r1'):
            s = D['carteira'][f'{ent}|{ges}|padrao']; s2 = D['carteira'][f'{ent}|{ges}|sem_filtro']
            L.append(f"| {D['rot_entrada'][ent]} | {D['rot_gestao'][ges]} | {md_n(s['trades'])} | "
                     f"{md_sn(s['lucro_liq'])} | {md_sn(s['lucro_liq_rs'], 2)} | {md_sn(s['exp_pts'], 1)} | "
                     f"{md_n(s['winrate'], 1)}% | {md_n(s['fator_lucro'], 2)} | {md_n(s['dd_max'])} | "
                     f"{md_sn(s2['lucro_liq'])} |")
    L += ['', '## 5. Custo (pts por sinal, padrao)', '',
          '| Entrada | Gestao | Bruto | 5 pts | 10 pts |', '|:--|:--|--:|--:|--:|']
    for ent in ('fecha', 'meio_lim'):
        for ges in ('parcial', 'puro', 'r2', 'r1'):
            c = D['custo'][f'{ent}|{ges}']
            L.append(f"| {D['rot_entrada'][ent]} | {D['rot_gestao'][ges]} | "
                     + ' | '.join(md_sn(c[k], 1) for k in ('0', '5', '10')) + ' |')
    L += ['', '## Conclusao', '',
          '- **O pavio de 25-90% nao e filtro.** Ele seleciona candles que rendem um pouco menos '
          'que o conjunto de onde sairam, e nenhuma faixa e estavel nos tres tercos.',
          f"- **No PI, esse pavio e o normal.** O lado da abertura tem pavio em quase todo candle; "
          f"a faixa 25-90% aceita {md_n(F['pad']['n'] / (F['pad']['n'] + F['fora']['n']) * 100)}% "
          'dos candles contra depois de 2-4 barras, e descarta sobretudo os pavios pequenos, '
          'que mediram melhor.',
          f"- **A contagem merece mais atencao que o pavio:** com 4 barras antes o sinal mede "
          f"{md_sn(F['nb']['4']['ev'], 1)} pts. Nao confirmado fora desta base.",
          f"- **Compra x venda e o mercado:** periodo de alta. Compra {md_sn(F['lados']['compra']['ev'], 1)}, "
          f"venda {md_sn(F['lados']['venda']['ev'], 1)}; sem filtro, {md_sn(F['lados']['compra_sem']['ev'], 1)} "
          f"e {md_sn(F['lados']['venda_sem']['ev'], 1)}.",
          f"- **Nenhuma variante paga custo.** A 1:1 faz {md_n(F['cart_r1']['trades'])} operacoes em "
          f"{F['cart_r1']['dias']} pregoes (~{md_n(F['cart_r1']['trades_dia'])} por dia).",
          '',
          '> 26 pregoes, um instrumento, um regime de mercado, resultado bruto. O estudo diz que '
          'o filtro nao funcionou aqui; nao prova que nenhum filtro de pavio funcione.',
          '',
          'Reproduzir: `python pavio_contra.py && python relatorio_pavio.py`.', '']
    return '\n'.join(L)


# ===================================================================== main
def main():
    with open(os.path.join(SAIDA, 'pavio_contra.json'), encoding='utf-8') as f:
        D = json.load(f)
    F = fatos(D)
    D['gestoes'] = GESTOES_JS
    import datetime as _dt
    D['candles']['dt'] = [_dt.datetime.fromtimestamp(t / 1000, _dt.timezone.utc)
                          .strftime('%d/%m %H:%M:%S') for t in D['candles']['t']]
    del D['candles']['t']

    corpo = ''.join([capa(D, F), veredito(D, F), metodo(D, F), controles(D, F),
                     faixas(D, F), barras_horas(D, F), operacoes(D, F), conclusao(D, F)])
    menu = ''.join(f'<li><a href="#{a}">{r}</a></li>' for a, r in MENU)
    with open(VENDOR_KC, encoding='utf-8') as f:
        kline = f.read()
    html = (HTML.replace('__CSS__', molde.CSS).replace('__MENU__', menu)
            .replace('__KLINE__', kline).replace('__KIT__', molde.JS_KIT)
            .replace('__JS__', JS)
            .replace('__DADOS__', json.dumps(D, ensure_ascii=False, separators=(',', ':')))
            .replace('__CORPO__', corpo))
    with open(os.path.join(BASE, 'pavio_contra.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    with open(os.path.join(BASE, 'PAVIO_CONTRA.md'), 'w', encoding='utf-8') as f:
        f.write(markdown(D, F))
    print(f'gravado: pavio_contra.html ({len(html) / 1e6:.1f} MB) e PAVIO_CONTRA.md')


if __name__ == '__main__':
    main()
