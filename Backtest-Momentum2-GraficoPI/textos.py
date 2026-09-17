# -*- coding: utf-8 -*-
"""Textos do relatorio (HTML) e do RESULTADOS.md, montados a partir do estudo.json."""

ESCOLHIDA = 'fecha|otimizado'
SIMPLES = 'fecha|picado400'

CALIBRACAO = [
    # hora, lado, rotulo do print, classificacao do motor, observacao
    ('09:05', 'venda', 'T2', 'T2', 'Hull abaixo do candle'),
    ('09:06', 'venda', 'T2', 'T2', 'Hull abaixo do candle'),
    ('09:38', 'venda', 'T1', 'T1', 'Hull corta o candle'),
    ('09:53', 'compra', 'T1', 'T1', 'quase toque: EMA 12 pts abaixo da minima'),
    ('10:25', 'venda', 'T1', 'T1', 'Hull corta o candle'),
    ('10:27', 'venda', 'T2', 'T2', 'Hull 16 pts abaixo da minima'),
    ('10:43', 'compra', 'T1', 'T1', 'Hull corta o candle'),
]


def n(v, c=0):
    if v is None:
        return '-'
    s = f'{abs(v):,.{c}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return ('−' if v < 0 else '') + s


def rs(v, c=0):
    if v is None:
        return '-'
    return ('+' if v > 0 else '−' if v < 0 else '') + 'R$ ' + n(abs(v), c)


def cls(v):
    return 'pos' if (v or 0) > 0 else 'neg' if (v or 0) < 0 else 'mudo'


def kpi(r, v, c=''):
    return f'<div class="kpi"><div class="r">{r}</div><div class="v {c}">{v}</div></div>'


def gest_txt(R):
    G = R.get('G') or {}
    if not G:
        return 'stop 100, parcial 50% em +100 (stop do restante na media), alvo +300'
    st = G.get('stop')
    s = f"stop {n(st) if st else 'no extremo do candle'}, alvo +{n(G['alvo'])}"
    if G.get('parcial') is False:
        return s + ', sem parcial'
    return s + f", parcial {int(G.get('frac', .5) * 100)}% em +{n(G.get('parcial_em', 100))} (stop do restante na {G.get('apos', 'media')})"


def corpo_html(D):
    M = D['meta']; R = D['robustez']
    E_ = R[ESCOLHIDA]; S_ = R[SIMPLES]
    B = D['base']
    s = E_['stats']; so = E_['stats_oos']; si = E_['stats_is']
    bf = B['fecha']['blocos']
    g_sel = D['selecao']['fecha']['passos']
    fg = R['fecha|gestao']

    H = []
    H.append(f"""
<h1>EMA 21 + Hull + MACD no grafico PI</h1>
<p class="sub">WINFUT, grafico de 20 PI &middot; {n(M['candles'])} candles, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}) &middot;
{M['contratos']} contratos de mini indice, R$ {n(M['custo'], 2)} por contrato ida e volta &middot; treino ate {M['corte']}, teste depois</p>

<section id="resumo"><h2>Resumo</h2>
<div class="kpis">
{kpi('Regra pura (CLAUDE.md)', rs(bf['todos']['stats']['liquido']), cls(bf['todos']['stats']['liquido']))}
{kpi('Fator de lucro regra pura', n(bf['todos']['stats']['fator_lucro'], 2))}
{kpi('Recomendada: liquido', rs(s['liquido']), cls(s['liquido']))}
{kpi('Recomendada: fora da amostra', rs(so['liquido']), cls(so['liquido']))}
{kpi('Recomendada: fator / winrate', n(s['fator_lucro'], 2) + ' / ' + n(s['winrate'], 0) + '%')}
{kpi('Recomendada: rebaixamento', rs(-s['dd_max']), 'neg')}
</div>
<div class="card ruim"><b>A regra como esta escrita tem vantagem fina demais.</b>
{n(bf['todos']['stats']['trades'])} trades em {M['pregoes']} pregoes (~{n(bf['todos']['stats']['trades_dia'], 0)} por dia), {rs(bf['todos']['stats']['liquido'])} liquido,
fator de lucro {n(bf['todos']['stats']['fator_lucro'], 2)}, rebaixamento {rs(-bf['todos']['stats']['dd_max'])}. E o resultado depende de a parcial e o alvo executarem
<b>no toque exato</b> dos niveis redondos (+100/+300), onde os candles PI fecham: exigindo que o preco atravesse o nivel em 5 pts,
o liquido cai para {rs(R['fecha|base']['atravessa']['liquido'])}; com 10 pts de escorregamento por trade vira {rs(R['fecha|base']['estresse'][2]['liquido'])}.
Vendas sozinhas nao pagaram os custos ({rs(bf['todos']['stats']['shorts_rs'])}).</div>
<div class="card ok"><b>Um filtro sobreviveu fora da amostra: movimento picado antes do recuo.</b>
Com 11 ou mais inversoes de cor nos 20 candles anteriores ao recuo, o valor por sinal no teste sobe de {rs(g_sel[0]['ev_oos'], 1)} para {rs(g_sel[1]['ev_oos'], 1)}
(escolhido so com o treino, onde foi de {rs(g_sel[0]['ev_is'], 1)} para {rs(g_sel[1]['ev_is'], 1)}). E o contrario da hipotese do CLAUDE.md: o picado <i>ajuda</i>.
O fator de lucro sobe de forma regular com o limiar, compra e venda ficam positivas, e o sorteio de entradas aleatorias com a mesma gestao nunca chegou perto.</div>
<div class="card"><b>Recomendada: {E_['nome']}.</b> Filtros: {' &middot; '.join(E_['filtros'])}. Gestao: {gest_txt(E_)} (escolhida no treino).
{n(s['trades'])} trades (~{n(s['trades_dia'], 1)} por pregao), {rs(s['liquido'])}, fator {n(s['fator_lucro'], 2)}, winrate {n(s['winrate'], 1)}%, rebaixamento {rs(-s['dd_max'])}.
Treino {rs(si['liquido'])} / teste {rs(so['liquido'])} ({rs(so['exp_rs'], 2)} por trade no teste).
Monte Carlo: {n(E_['mc']['p_prejuizo'], 1)}% de chance de prejuizo. Atravessando 5 pts: {rs(E_['atravessa']['liquido'])}. Com 10 pts de escorregamento: {rs(E_['estresse'][2]['liquido'])}.
A versao so com o filtro picado ({S_['nome'].split(' - ')[1]}) da {rs(S_['stats']['liquido'])} (teste {rs(S_['stats_oos']['liquido'])}) e e mais simples de operar.</div>
<div class="card alerta"><b>Cuidado com a parcial em +50.</b> A grade de gestao acha {rs(fg['stats']['liquido'])} com parcial de 50% em +50 e stop na entrada, mas
<b>entradas aleatorias</b> com essa gestao tambem ganham ({rs(fg['aleatorio']['ev_aleat'], 2)} por trade, percentil {n(fg['aleatorio']['percentil'], 0)}): o lucro vem da geometria
dos pavios do grafico PI, nao do setup, e sai de uma aproximacao do caminho do preco dentro do candle. Nao use esse numero sem confirmar em replay/tick a tick.</div>
<p class="nota">Entrada limitada no meio do corpo: {rs(B['meio']['blocos']['todos']['stats']['liquido'])}. So executa quando o preco volta 50 pts contra, e esses sao
justamente os sinais piores; os que disparam direto ficam de fora. Stop no extremo do candle: {rs(B['extremo']['blocos']['todos']['stats']['liquido'])}, com o treino negativo.</p>
</section>

<section id="regras"><h2>Regras como foram programadas</h2>
<div class="card"><ol>
<li><b>Trigger</b> = <code>HullRetracao_Azul.ntsl</code> com os parametros da pasta: Hull 50 subindo (compra), candle fechando em alta,
precedido por <b>2 a 3</b> candles de baixa no mesmo pregao, <b>pavio do lado do fechamento ate 10% do corpo</b>. Venda e o espelho.</li>
<li><b>Ponto de virada em contato com a EMA 21</b>: algum candle da virada (os contra + o trigger) com minima &le; EMA &le; maxima, com
<b>tolerancia de 15 pts</b> (o T1 rotulado das 09:53 de 14/09 ficou a 12 pts; "quase toque, dava para tomar").</li>
<li><b>MACD (9, 14, sinal 9) acima de zero</b> para compra, abaixo para venda, no fechamento do trigger.</li>
<li><b>T1 / T2</b> pela Hull em relacao ao <b>candle do trigger</b>: na compra, Hull acima da maxima = T2; tocando ou abaixo = T1.</li>
<li>Uma posicao por vez; sinais durante um trade aberto sao ignorados; zera no fim do pregao.</li>
</ol>
<p><b>Sistemas de entrada</b> (todos com stop 100 / parcial 50% em +100 com stop na media / alvo +300, salvo na grade de gestao):</p>
<ul><li><b>Seca no fechamento</b> do trigger.</li>
<li><b>Limitada no meio do corpo</b> (50 pts de recuo), valida por 3 candles.</li>
<li><b>Stop no extremo oposto</b> do candle do trigger (minima na compra), parcial em +100 e alvo +300 contados da entrada.</li></ul>
<p class="nota">Parcial: 3 contratos saem em +100 (+300 pts-contrato); o stop dos outros 3 fica no preco em que o trade zera, 100 pts atras da entrada, que e o proprio stop original.
Caminho dentro do candle: no grafico PI o candle de alta vai abertura &rarr; minima &rarr; maxima &rarr; fechamento (o pavio contra se forma antes do fechamento).</p></div>
<h3>Calibracao com os prints de 14/09 (unico dia dos exemplos que esta na base)</h3>
<div class="card"><div class="tab"><table><thead><tr><th>Hora</th><th>Lado</th><th>Rotulo no print</th><th>Motor</th><th class="l">Observacao</th></tr></thead><tbody>
""" + ''.join(f"<tr><td>{h}</td><td>{l}</td><td>{a}</td><td class=\"{'pos' if a == b else 'neg'}\">{b}</td><td class=\"l\">{o}</td></tr>" for h, l, a, b, o in CALIBRACAO) + """
</tbody></table></div>
<p class="nota">Os 7 rotulos batem. Classificar pela Hull em relacao a <i>todos</i> os candles da virada errava 3 deles (09:05, 09:06 e 10:27 viravam T1).
As setas dos prints de 14/09 batem com o indicador em 2-3 candles e pavio ate 10%; a versao 2-4 sem corte de pavio criaria setas as 09:04
que o grafico nao mostra. A seta das 10:24 fica fora pela EMA (108 pts longe). Os prints de 15 e 16/09 sao posteriores a base.</p></div>
</section>

<section id="base"><h2>Resultado base: os tres sistemas de entrada</h2>
<div id="t_modos"></div>
<div class="card"><div class="abas" id="abas_base"></div><div id="g_base" class="graf"></div></div>
<div class="card"><h3>Estatisticas (padrao MetaTrader 5, com winrate), 6 contratos</h3><div id="t_base"></div></div>
</section>

<section id="filtros"><h2>Filtros do CLAUDE.md, um a um</h2>
<p>Cada sinal resolvido isoladamente (sem concorrencia entre sinais), em R$ por sinal com 6 contratos e custo. <b>Treino</b> = ate """ + M['corte'] + """, <b>teste</b> = depois.
Faixas numericas em quintis definidos no treino. "Melhor nos dois" = acima da media geral no treino e no teste. Com ~2.000 sinais e dezenas de faixas,
varias vao parecer boas por acaso; so vale o que se repete nas duas metades.</p>
<div class="card nota">
<b>Como cada filtro foi medido.</b> Tendencia geral: preco contra a abertura do dia, contra a EMA 200, inclinacao da EMA 21, MACD alem da Bollinger 1000.
Segundos recuos: quantas vezes o preco ja tocou a EMA desde que o MACD mudou de lado. Fraqueza de continuacao: o impulso anterior ao recuo fez novo extremo
(10 candles recentes contra os anteriores) e o tamanho do impulso. Segundas entradas: ja houve trigger valido no mesmo lado a ate 100 pts nos 60 candles anteriores.
Abertura do Dow: 10:30 de Brasilia no horario de verao dos EUA (11:30 em 06/03). Picado: inversoes de cor nos 20 candles antes do recuo (maximo 19).
Volume: agressao compra + venda, relativa a mediana dos 200 candles anteriores; saldo = compra &minus; venda no sentido do trade. Tempo: duracao do candle
relativa a mediana dos 200 anteriores.</div>
<div class="abas" id="abas_filtro"></div>
<div id="filtros_corpo"></div>
</section>

<section id="selecao"><h2>Selecao de filtros so no treino</h2>
<p>Busca gulosa, ate 3 filtros, maximizando a estatistica t do lucro no treino (minimo de 25% dos sinais). O teste so e olhado depois.</p>
<div id="t_selecao"></div>
<p class="nota">Na entrada seca, o 1o passo (picado) melhora o teste; o 2o (fora da janela 5 min antes a 15 min depois da abertura do Dow) melhora o treino e piora
um pouco o teste, e por isso a versao so com o picado tambem e mostrada. Na limitada no meio, a selecao escolheu filtros sem sentido operacional e o teste nao confirma.</p>
</section>

<section id="gestao"><h2>Gestao: stop, alvo e parciais</h2>
<p>Grade com stop 50-200 (ou no extremo do candle), alvo +100 a +500, parcial de 50% em +50/+100/+150/+200 com o stop do restante na media ou na entrada.
Passe o mouse sobre a celula para ver treino, teste, carteira e rebaixamento.</p>
<div class="abas" id="abas_gmodo"></div><div class="abas" id="abas_gconj"></div><div class="abas" id="abas_gmetr"></div>
<h3>As 12 melhores pelo treino</h3><div id="gestao_top"></div>
<div id="gestao_corpo"></div>
</section>

<section id="variantes"><h2>Variantes comparadas</h2>
<p>Carteira real (uma posicao por vez), 6 contratos, custo incluido. "Gestao do treino" e "filtros do treino" foram escolhidos so com dados ate """ + M['corte'] + """.</p>
<div id="t_variantes"></div>
<div class="card"><div id="g_variantes" class="graf"></div></div>
<h3>Execucao: a vantagem sobrevive a ordens que nao executam no toque?</h3>
<div class="tab"><table><thead><tr><th>Variante</th><th>Como testado</th><th>Atravessar 5 pts</th><th>Teste</th><th>Niveis 1 tick antes (+95/+295) e atravessar 5</th><th>Teste</th><th>Escorregamento 10 pts</th><th>Sem os 5% melhores</th></tr></thead><tbody>
""" + ''.join(
        f"<tr class=\"{'dest' if k == ESCOLHIDA else ''}\"><td>{V['nome']}</td><td>{rs(V['stats']['liquido'])}</td>"
        f"<td class=\"{cls(V['atravessa']['liquido'])}\">{rs(V['atravessa']['liquido'])}</td><td class=\"{cls(V['atravessa']['oos'])}\">{rs(V['atravessa']['oos'])}</td>"
        f"<td class=\"{cls(V['atravessa']['tick_liq'])}\">{rs(V['atravessa']['tick_liq'])}</td><td class=\"{cls(V['atravessa']['tick_oos'])}\">{rs(V['atravessa']['tick_oos'])}</td>"
        f"<td class=\"{cls(V['estresse'][2]['liquido'])}\">{rs(V['estresse'][2]['liquido'])}</td><td class=\"{cls(V['sem_top'][2]['liquido'])}\">{rs(V['sem_top'][2]['liquido'])}</td></tr>"
        for k, V in R.items()) + """
</tbody></table></div>
<p class="nota">"Atravessar 5 pts": parcial, alvo e entrada limitada so executam se o preco passar 1 tick alem do nivel (fila cheia no numero redondo).
"1 tick antes": a ordem fica em +95/+295, e basta o preco tocar +100/+300. Escorregamento: 10 pts a menos por contrato em cada trade (R$ 12 por trade com 6 contratos).</p>
</section>

<section id="carteira"><h2>Carteira: curva de patrimonio e distribuicoes</h2>
<div class="card"><select id="rsel"></select><p id="r_nome" style="margin:8px 0 0"></p></div>
<div class="kpis" id="r_kpis"></div>
<div class="card"><h3>Patrimonio acumulado (R$, 6 contratos, liquido de custos)</h3><div id="g_eq" class="graf"></div>
<h3>Rebaixamento</h3><div id="g_dd" class="graf"></div></div>
<div class="card"><h3>Estatisticas: base inteira, treino e teste</h3><div id="t_mt5"></div></div>
<div class="grid2">
<div class="card"><h3>Resultado por trade (R$)</h3><div id="g_res" class="graf"></div></div>
<div class="card"><h3>Duracao dos trades (minutos)</h3><div id="g_dur" class="graf"></div></div>
<div class="card"><h3>MEP: maxima excursao positiva (pts)</h3><div id="g_mep" class="graf"></div></div>
<div class="card"><h3>MEN: maxima excursao negativa (pts)</h3><div id="g_men" class="graf"></div></div>
</div>
<div class="card"><h3>Liquido por hora de entrada</h3><div id="g_hora" class="graf"></div><div id="t_hora"></div></div>
</section>

<section id="robustez"><h2>Robustez</h2>
<p class="nota">Tudo abaixo se refere a variante escolhida no seletor da secao Carteira.</p>
<div class="grid2">
<div class="card"><h3>Mes a mes</h3><div id="t_meses"></div></div>
<div class="card"><h3>Contra entradas aleatorias</h3><div id="t_aleat"></div>
<p class="nota">12.000 candles sorteados, trade no sentido do proprio candle, mesma gestao. 3.000 sorteios com o mesmo numero de trades da variante.</p></div>
</div>
<div class="card"><h3>Monte Carlo</h3><div id="t_mc"></div>
<div class="grid2"><div><p class="nota">Resultado final</p><div id="g_mc" class="graf"></div></div><div><p class="nota">Rebaixamento maximo</p><div id="g_mcdd" class="graf"></div></div></div></div>
<div class="card"><h3>Custos e dependencia dos melhores trades</h3><div id="t_estresse"></div></div>
<h3>Vizinhanca dos parametros da regra (entrada seca, gestao do CLAUDE.md, sem filtros)</h3>
<div id="t_viz"></div>
<p class="nota">A primeira linha e a regra calibrada. Relaxar a EMA (tolerancia maior ou sem EMA) aumenta o resultado: o toque na EMA 21, como condicao, nao agrega.
1 candle contra ou 3 contra sao negativos; 2 contra e o melhor.</p>
</section>

<section id="kline"><h2>Trade a trade</h2>
<div class="card">
<div class="kbar"><select id="kvar"></select>
<select id="kfiltro"><option value="todos">todos</option><option value="T1">so T1</option><option value="T2">so T2</option>
<option value="ganho">so ganhos</option><option value="perda">so perdas</option><option value="zero">so zerados</option></select></div>
<div class="kbar" style="margin-top:8px"><button class="btn" id="kant">&larr; anterior</button><select id="ksel"></select><button class="btn" id="kprox">proximo &rarr;</button></div>
<div class="kinfo" id="kinfo"></div>
<div id="kchart"></div>
<p class="nota">Laranja tracejada: EMA 21. Linha solida: Hull 50 (azul subindo, vermelha descendo). Cinza tracejadas: Keltner 21 / 2,5 ATR em volta da EMA 21.
Setas azuis cheias: triggers que passam EMA + MACD (rotulo T1/T2 no trigger do trade); setas cinza vazadas: seta do HullRetracao_Azul sem EMA ou MACD.
Faixa azul: candles da virada. Painel de baixo: MACD 9/14 (verde acima de zero), sinal 9 (laranja) e Bollinger 1000 / 1,0 (cinza). Setas do teclado navegam.</p>
</div>
</section>

<section id="conclusao"><h2>Conclusao e proximos passos</h2>
<div class="card">
<ol>
<li><b>O setup existe, mas sozinho nao paga a operacao.</b> Contra entradas aleatorias ele fica no percentil """ + n(R['fecha|base']['aleatorio']['percentil'], 0) + """
(ha informacao no sinal), mas sao ~""" + n(bf['todos']['stats']['trades_dia'], 0) + """ trades por dia com """ + rs(bf['todos']['stats']['exp_rs'], 2) + """ cada, e isso some com 1 tick de fila ou escorregamento.</li>
<li><b>T1 x T2 nao separa.</b> T2 foi melhor no treino e T1 no teste; nenhum dos dois e consistentemente melhor.</li>
<li><b>Filtro que funcionou: movimento picado antes do recuo</b> (11+ inversoes em 20 candles). Os demais filtros do CLAUDE.md nao se repetiram nas duas metades,
com excecoes pequenas: evitar o 1o horario (09h) e depois das 17h, e evitar o MACD ja alem da Bollinger 1000 (poucos sinais, todos ruins).</li>
<li><b>Gestao:</b> sobre os sinais filtrados, stop 100 sem parcial e alvo +400 foi a melhor no treino e continuou positiva no teste. A parcial em +100 com stop na
media transforma boa parte dos trades em zero e depende de execucao no toque. Se for manter a parcial, coloque a ordem 1 tick antes (+95).</li>
<li><b>Entrada:</b> seca no fechamento. A limitada no meio do corpo perde os melhores trades; o stop no extremo sobe o acerto (31% contra 27%), mas a perda media cresce mais e o treino fica negativo.</li>
<li><b>Limites:</b> 132 pregoes e um unico regime (mar-set/2026, alta de ~182 mil para ~187 mil). O caminho do preco dentro do candle PI e reconstruido, nao observado.
Os horarios dos primeiros candles do dia vem truncados (dezenas de candles as 09:03). Rode a variante recomendada em replay ou simulador por algumas semanas antes de dinheiro real.</li>
</ol>
</div>
<div class="card ok"><b>Plano sugerido para validar em simulador</b>
<ul><li>Sinal: HullRetracao_Azul (2-3 candles, pavio ate 10%) + virada tocando a EMA 21 (tolerancia 15 pts) + MACD do lado do trade.</li>
<li>Filtro: 11 ou mais trocas de cor nos 20 candles antes do primeiro candle do recuo.</li>
<li>Entrada seca no fechamento do trigger. Stop 100. Alvo +400 (ou +395 para garantir a execucao). Sem parcial. Zerar no fim do pregao. Uma posicao por vez.</li>
<li>Opcional (escolhido no treino, nao confirmado no teste): nao entrar de 5 min antes a 15 min depois da abertura do Dow Jones (10:25-10:45).</li>
<li>Referencia para comparar com o simulador: """ + rs(S_['stats']['exp_rs'], 2) + """ por trade e ~""" + n(S_['stats']['trades_dia'], 1) + """ trades por pregao (so com o filtro picado).</li></ul>
</div>
</section>
"""
    )
    return ''.join(H)


def markdown(D):
    M = D['meta']; R = D['robustez']; B = D['base']
    E_ = R[ESCOLHIDA]; S_ = R[SIMPLES]
    L = ['# EMA 21 + Hull + MACD no grafico PI: resultados', '',
         f"WINFUT, grafico de 20 PI, {n(M['candles'])} candles, {M['pregoes']} pregoes ({M['inicio']} a {M['fim']}). "
         f"{M['contratos']} contratos de mini indice, custo R$ {n(M['custo'], 2)} por contrato ida e volta. Treino ate {M['corte']}, teste depois. "
         'Graficos, filtros, grade de gestao, Monte Carlo e trade a trade (KLineCharts) em `relatorio.html`.', '',
         '## Regras programadas', '',
         '- **Trigger**: `HullRetracao_Azul.ntsl` como esta na pasta (Hull 50 a favor, 2-3 candles contra no mesmo pregao, pavio do fechamento ate 10% do corpo).',
         '- **Virada tocando a EMA 21**: algum candle da virada (contra + trigger) com minima <= EMA <= maxima, tolerancia 15 pts.',
         '- **MACD 9/14/9** acima de zero na compra, abaixo na venda.',
         '- **T1/T2** pela Hull em relacao ao candle do trigger (compra: Hull acima da maxima = T2). Bate com os 7 rotulos de 14/09.',
         '- Uma posicao por vez, zera no fim do pregao.', '',
         '| Calibracao 14/09 | Lado | Print | Motor | Obs. |', '|:--|:--|:-:|:-:|:--|']
    L += [f'| {h} | {l} | {a} | {b} | {o} |' for h, l, a, b, o in CALIBRACAO]
    L += ['', '## Resultado base (gestao do CLAUDE.md: stop 100, parcial 50% em +100 com stop na media, alvo +300)', '',
          '| Entrada | Bloco | Trades | Liquido | Fator | Winrate | Rebaixamento |', '|:--|:--|--:|--:|--:|--:|--:|']
    for m in ('fecha', 'meio', 'extremo'):
        for k in ('todos', 'T1', 'T2'):
            s = B[m]['blocos'][k]['stats']
            L.append(f"| {B[m]['nome'] if k == 'todos' else ''} | {k} | {n(s['trades'])} | {rs(s['liquido'])} | {n(s['fator_lucro'], 2)} | "
                     f"{n(s['winrate'], 1)}% | {rs(-s['dd_max'])} |")
    L += ['', '## Filtros (entrada seca, R$ por sinal: base / treino / teste)', '',
          'Media geral por sinal: ' + rs(D['filtros']['fecha'][0]['geral'], 2) + '. Faixas com pelo menos 30 sinais no treino.', '',
          '| Grupo | Filtro | Faixa | Sinais | R$/sinal | Treino | Teste |', '|:--|:--|:--|--:|--:|--:|--:|']
    for f in D['filtros']['fecha']:
        for l in f['linhas']:
            if l['n_is'] < 30:
                continue
            L.append(f"| {f['grupo']} | {f['desc']} | {l['faixa']} | {n(l['n'])} | {rs(l['ev'], 1)} | {rs(l['ev_is'], 1)} | {rs(l['ev_oos'], 1)} |")
    L += ['', '## Selecao de filtros so no treino', '']
    for m in ('fecha', 'meio', 'extremo'):
        L += [f"**{B[m]['nome']}**", '', '| Passo | R$/sinal treino | R$/sinal teste | Sinais teste |', '|:--|--:|--:|--:|']
        L += [f"| {p['filtro']} | {rs(p['ev_is'], 2)} | {rs(p['ev_oos'], 2)} | {n(p['n_oos'])} |" for p in D['selecao'][m]['passos']]
        L.append('')
    L += ['## Variantes (carteira, 6 contratos, liquido)', '',
          '| Variante | Gestao | Trades | Liquido | Fator | Rebaix. | Treino | Teste | MC p(prej.) | Percentil vs aleatorio | Atravessar 5 pts | 1 tick antes | Escorreg. 10 pts |',
          '|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|']
    for k, V in R.items():
        s = V['stats']
        L.append(f"| {'**' + V['nome'] + '**' if k == ESCOLHIDA else V['nome']} | {gest_txt(V)} | {n(s['trades'])} | {rs(s['liquido'])} | {n(s['fator_lucro'], 2)} | "
                 f"{rs(-s['dd_max'])} | {rs(V['stats_is']['liquido'])} | {rs(V['stats_oos']['liquido'])} | {n(V['mc']['p_prejuizo'], 1)}% | "
                 f"{n(V['aleatorio']['percentil'], 0)} | {rs(V['atravessa']['liquido'])} | {rs(V['atravessa']['tick_liq'])} | {rs(V['estresse'][2]['liquido'])} |")
    s = E_['stats']
    L += ['', f"## Recomendada: {E_['nome']}", '',
          f"Filtros: {', '.join(E_['filtros'])}. Gestao: {gest_txt(E_)}.", '',
          '| Estatistica | Base | Treino | Teste |', '|:--|--:|--:|--:|']
    for rot, key, f in [('Trades', 'trades', lambda v: n(v)), ('Liquido', 'liquido', rs), ('Fator de lucro', 'fator_lucro', lambda v: n(v, 2)),
                        ('Payoff', 'payoff', lambda v: n(v, 2)), ('R$ por trade', 'exp_rs', lambda v: rs(v, 2)),
                        ('Winrate', 'winrate', lambda v: n(v, 1) + '%'), ('Maior ganho', 'maior_ganho', rs), ('Maior perda', 'maior_perda', rs),
                        ('Max. perdas seguidas', 'max_seq_perda', lambda v: n(v)), ('Rebaixamento maximo', 'dd_max', lambda v: rs(-v)),
                        ('Fator de recuperacao', 'recovery', lambda v: n(v, 2)), ('Sharpe por trade', 'sharpe', lambda v: n(v, 3)),
                        ('Pregoes positivos', 'dias_pos', lambda v: n(v, 0) + '%'), ('Compras R$', 'longs_rs', rs), ('Vendas R$', 'shorts_rs', rs)]:
        L.append(f"| {rot} | {f(s[key])} | {f(E_['stats_is'].get(key))} | {f(E_['stats_oos'].get(key))} |")
    mc = E_['mc']
    L += ['', f"Monte Carlo (5.000 reamostragens): resultado p5 {rs(mc['final']['5'])}, mediana {rs(mc['final']['50'])}; rebaixamento p95 {rs(-mc['dd']['95'])}; "
              f"prejuizo em {n(mc['p_prejuizo'], 1)}% dos sorteios. Contra entradas aleatorias com a mesma gestao: percentil {n(E_['aleatorio']['percentil'], 1)}.", '',
          'Mes a mes: ' + '; '.join(f"{x['data']} {rs(x['sum'])} ({x['count']})" for x in E_['meses']) + '.', '',
          f"Versao so com o filtro picado ({S_['nome']}): {n(S_['stats']['trades'])} trades, {rs(S_['stats']['liquido'])}, fator {n(S_['stats']['fator_lucro'], 2)}, "
          f"treino {rs(S_['stats_is']['liquido'])} / teste {rs(S_['stats_oos']['liquido'])}.", '',
          '## Conclusoes', '',
          f"1. **A regra pura tem vantagem fina demais**: {rs(B['fecha']['blocos']['todos']['stats']['liquido'])} em {n(B['fecha']['blocos']['todos']['stats']['trades'])} trades, "
          f"e o resultado depende de a parcial e o alvo executarem no toque exato: atravessando 5 pts cai para {rs(R['fecha|base']['atravessa']['liquido'])}; com 10 pts de escorregamento, {rs(R['fecha|base']['estresse'][2]['liquido'])}.",
          '2. **T1 x T2 nao separa** de forma consistente (T2 melhor no treino, T1 no teste).',
          '3. **Movimento picado antes do recuo (11+ inversoes em 20 candles) e o unico filtro que se confirmou fora da amostra**, ao contrario da hipotese. '
          'Pequenos e consistentes: evitar 09h e 17h+, e MACD ja alem da Bollinger 1000.',
          '4. **Entrada seca no fechamento** e a melhor; a limitada no meio do corpo so executa nos sinais piores.',
          '5. **Gestao**: nos sinais filtrados, stop 100 / alvo +400 sem parcial. A parcial em +50 com stop na entrada "funciona" ate com entradas aleatorias: '
          'e efeito da reconstrucao dos pavios do grafico PI, nao do setup.',
          '6. **Limites**: 132 pregoes de um so regime (alta), caminho dentro do candle reconstruido. Validar em replay ou simulador antes de operar.', '']
    return '\n'.join(L)
