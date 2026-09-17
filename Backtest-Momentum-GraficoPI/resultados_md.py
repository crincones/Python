# -*- coding: utf-8 -*-
"""
RESULTADOS.md -- a mesma medicao do relatorio.html, em texto.

Chamado por relatorio.py. O .md existe para ler no terminal, no GitHub e
para caber num diff: e a versao que sobrevive sem navegador.
"""
ROT_MODO = {'fecha': 'fechamento', 'meio_lim': 'limitada no meio',
            'antecipa': 'stop no meio (antecipada)'}
ROT_GESTAO = {'parcial': '1:3 com parcial', 'puro': '1:3 sem parcial',
              'r2': '1:2 sem parcial', 'r1': '1:1 sem parcial'}


def n(v, c=0):
    """Numero no padrao brasileiro: ponto no milhar, virgula no decimal."""
    if v is None:
        return '-'
    return f'{v:,.{c}f}'.replace(',', ' ').replace('.', ',').replace(' ', '.')


def sn(v, c=0):
    if v is None:
        return '-'
    return ('+' if v > 0 else '') + n(v, c)


def tabela(cab, linhas, alin=None):
    alin = alin or ['---:'] * len(cab)
    alin[0] = ':---'
    out = ['| ' + ' | '.join(cab) + ' |', '| ' + ' | '.join(alin) + ' |']
    out += ['| ' + ' | '.join(str(c) for c in l) + ' |' for l in linhas]
    return '\n'.join(out)


def escreve(D, destino):
    a = D['auditoria']; P = D['parametros']; R = D['rotulo']
    esc = D['variantes'][D['escolhida']]; s = esc['stats']
    base = D['variantes']['fecha|parcial|bronze']['stats']
    mc = D['monte_carlo'][D['escolhida']]
    nt = {x['nivel']: x for x in D['niveis_terco']}
    O = D['oos']; B = O['blocos']
    ou = B['fecha|parcial|ouro']['sinais']
    C = D.get('candidato')
    L = []
    w = L.append

    w('# Resultados -- momentum no grafico de 20 PI (WINFUT)\n')
    w(f"Base: `WINFUT/WINFUT_20PI_Robo.csv`, {n(a['candles'])} candles de 20 PI, "
      f"{a['dias']} pregoes, de {a['de']} a {a['ate']}. Contem inteira a base do primeiro "
      f"estudo (`WINFUT_20PI.csv`, 26 pregoes, 06/08 a 11/09/2026).  ")
    w('Resultados em **pontos do WINFUT**, brutos, com um contrato '
      '(R$ 0,20 por ponto). Graficos e trade a trade em `relatorio.html`.\n')

    w('> **O resumo.** No primeiro estudo o padrao Ouro media +34 pontos por trade. Os '
      f"filtros dele foram escolhidos em 06/08 a 11/09; nos {n(ou['antes']['n'])} sinais "
      f"de 06/03 a 05/08, que nunca tinham sido vistos, ele mede **{sn(ou['antes']['ev'], 1)}** "
      f"(t = {sn(ou['antes']['t'], 2)}). Na base inteira, {sn(s['exp_pts'], 1)} por trade -- nao "
      f"paga custo. A regra-base do CLAUDE.md, sem filtros, mede {sn(base['exp_pts'], 1)}. "
      '**Nao ha setup para operar.** Ha uma hipotese (retracao de 3+ candles) para medir em '
      'pregoes futuros.\n')

    # ------------------------------------------------------- fora da amostra
    w('## 1. Fora da amostra: o teste que faltava\n')
    w('A base nova se divide em tres blocos: **antes** (06/03 a 05/08, nunca visto quando as '
      'regras foram feitas), **original** (06/08 a 11/09, onde as regras nasceram) e '
      '**depois** (12/09 em diante, um pregao). Pontos por sinal, cada sinal resolvido '
      'isoladamente, com a estatistica t entre parenteses.\n')
    linhas = []
    for chave, rot in (('fecha|parcial|ouro', 'Ouro'), ('fecha|parcial|prata', 'Prata'),
                       ('fecha|parcial|bronze', 'Bronze (regra-base)'),
                       ('fecha|puro|ouro', 'Ouro, 1:3 sem parcial'), ('fecha|r2|ouro', 'Ouro, 1:2'),
                       ('meio_lim|parcial|prata', 'Prata, limitada no meio'),
                       ('antecipa|parcial|prata', 'Prata, antecipada (ver secao 7)')):
        x = B[chave]['sinais']
        linhas.append([rot] + [f"{sn(x[k]['ev'], 1)} ({sn(x[k]['t'], 1)}; n={x[k]['n']})"
                               for k in ('antes', 'original', 'depois')]
                      + [f"**{sn(x['total']['ev'], 1)}**"])
    w(tabela(['Variante', 'Antes', 'Original', 'Depois', 'Base inteira'], linhas))
    w('')
    w('**Mes a mes** (fechamento, 1:3 com parcial, pontos por sinal):\n')
    meses = [m['mes'] for m in O['meses']['fecha|parcial|ouro']]
    w(tabela(['Nivel'] + [m[5:] + '/' + m[2:4] for m in meses],
             [[R[k]] + [sn(next((x['ev'] for x in O['meses'][f'fecha|parcial|{k}'] if x['mes'] == m), None), 1)
                        for m in meses] for k in ('ouro', 'prata', 'bronze')]))
    w('')
    w('Agosto e setembro -- os meses da base antiga -- sao os unicos em que o Ouro passa de '
      '+20. O mercado nos meses:\n')
    w(tabela(['Mes', 'Pregoes', 'Variacao', 'Amplitude'],
             [[r['mes'], r['dias'], sn(r['var']), n(r['maxima'] - r['minima'])] for r in O['regime']]))
    w('')
    ff = O['filtros_fora']
    cz = {(c['concava'], c['esticado']): c for c in O['cruz_fora']}
    vet = cz[(True, True)]
    resto = [c for k_, c in cz.items() if k_ != (True, True)]
    ev_resto = sum(c['ev'] * c['n'] for c in resto) / sum(c['n'] for c in resto)
    w('**Os filtros do Ouro medidos so fora da janela original** (regra-base inteira):\n')
    w('- Pavio do candle de continuacao: ' + ' / '.join(f"{r['faixa']} {sn(r['ev'], 1)}" for r in ff['pavio']) + '.')
    w('- Candles de retracao: ' + ' / '.join(f"{r['faixa']} {sn(r['ev'], 1)}" for r in ff['retracao_candles']) + '.')
    w(f"- Veto de exaustao: vetados {sn(vet['ev'], 1)} ({vet['n']}); os que ficam {sn(ev_resto, 1)}.\n")

    # ------------------------------------------------------------ a base
    w('## 2. A base\n')
    w(tabela(['Conferencia', 'Resultado'], [
        ['Candles / pregoes', f"{n(a['candles'])} / {a['dias']} "
                              f"({n(a['barras_dia_media'])} por pregao)"],
        ['Corpo de exatamente 100 pontos', f"{n(a['corpo_100_pct'], 2)}%"],
        ['Abre no fechamento anterior', f"{n(a['abre_no_fecha_pct'], 2)}%"],
        ['ATR 21 mediano', f"{n(a['atr_mediana'])} pts"],
        ['Range mediano do candle', f"{n(a['range_mediano'])} pts"],
    ]))
    w('')
    w('A base vem do log do robo `LogCandles_Console.ntsl`, na ordem do proprio Profit. Nos '
      '10.000 candles em comum com a base antiga o OHLC e identico, a menos de 25 candles que a '
      'exportacao antiga listava em ordem trocada (mesmo carimbo de milissegundo). A hora vem so '
      'ate o minuto e nao ha a coluna de EMA da Nelogica: a EMA 21 usa a mesma formula conferida '
      'na base antiga (erro maximo de 0,004 ponto).\n')

    # ------------------------------------------------------------ o padrao
    w('## 3. O padrao e os tres niveis\n')
    w('**Regra-base** (compra; venda e o espelho), no fechamento do candle de continuacao: o '
      'candle fecha a favor e o anterior fechou contra; a Hull 50 no sentido do trade e atras do '
      'extremo; os dois extremos do par fora da Hull; a EMA 21 entre os topos e os fundos do par.\n')
    w(f"{n(D['n_sinais']['confirmados'])} sinais. Niveis encaixados, definidos no primeiro estudo "
      'e mantidos sem alteracao:\n')
    w(tabela(['Nivel', 'O que acrescenta', 'Sinais', 'Por trade', 'Acerto', 'T1', 'T2', 'T3'], [
        [f"**{R[k]}**", D['descricao'][k].replace('\n', ' '), nt[k]['n'],
         sn(nt[k]['ev'], 1), n(nt[k]['wr'], 1) + '%'] + [sn(x['ev'], 1) for x in nt[k]['por_terco']]
        for k in ('bronze', 'prata', 'ouro')
    ], [':---', ':---'] + ['---:'] * 6))
    w('')
    cz = D['estudos']['cruz_exaustao']
    w('**O veto de exaustao** (base inteira). Na base antiga a celula "abrindo a curva x '
      'esticado" media -1,5 contra +8 a +27 das outras:\n')
    w(tabela(['', f"preco perto da EMA (ate {n(P['estic_exaustao'], 2)} ATR)", 'preco esticado'],
             [[r['lin']] + [f"{sn(c['ev'], 1)} pts ({c['n']} sinais)" for c in r['celulas']]
              for r in cz]))
    w('')

    # ---------------------------------------------------------- estatisticas
    w('## 4. Estatisticas\n')
    w(f"**{R[esc['nivel']]} / entrada no {ROT_MODO[esc['modo']]} / "
      f"{ROT_GESTAO[esc['gestao']]}** -- formato do relatorio do MetaTrader 5, com winrate.\n")
    w(tabela(['Metrica', 'Valor'], [
        ['Lucro liquido total', f"{sn(s['lucro_liq'])} pts (R$ {sn(s['lucro_liq_rs'])})"],
        ['Lucro bruto / prejuizo bruto', f"{sn(s['lucro_bruto'])} / {sn(s['prej_bruto'])} pts"],
        ['Fator de lucro', n(s['fator_lucro'], 2)],
        ['Payoff esperado', f"{sn(s['exp_pts'], 2)} pts (R$ {sn(s['exp_rs'], 2)})"],
        ['Indice de Sharpe (por trade)', n(s['sharpe'], 3)],
        ['Correlacao LR', n(s['lr_corr'], 3)],
        ['Rebaixamento maximo', f"{n(s['dd_max'])} pts (R$ {n(s['dd_max_rs'])})"],
        ['Fator de recuperacao', n(s['recovery'], 2)],
        ['Total de negocios', n(s['trades'])],
        ['**Taxa de acerto (winrate)**', f"**{n(s['winrate'], 2)}%**"],
        ['Vencedores / zerados / perdedores', f"{s['vitorias']} / {s['zeros']} / {s['derrotas']}"],
        ['Compras (acerto)', f"{s['longs']} ({n(s['longs_wr'], 1)}%)"],
        ['Vendas (acerto)', f"{s['shorts']} ({n(s['shorts_wr'], 1)}%)"],
        ['Maior ganho / maior perda', f"{sn(s['maior_ganho'])} / {sn(s['maior_perda'])} pts"],
        ['Max. vitorias / perdas consecutivas', f"{s['max_seq_ganho']} / {s['max_seq_perda']}"],
        ['Saidas: alvo / stop / zero a zero / tempo',
         f"{s['alvos']} / {s['stops']} / {s['stops_zero']} / {s['timeouts'] + s['fins_dia']}"],
        ['MEP media / MEN media', f"{sn(s['mfe_media'], 1)} / {sn(s['mae_media'], 1)} pts"],
        ['Duracao mediana', f"{n(s['dur_mediana'] / 60, 1)} min ({n(s['barras_mediana'])} candles)"],
        ['Negocios por pregao', n(s['trades_dia'], 1)],
        ['Monte Carlo: probabilidade de lucro', f"{n(mc['prob_lucro'], 1)}%"],
    ]))
    w('')
    w('### A matriz inteira (base inteira, carteira de uma posicao por vez)\n')
    w(tabela(['Entrada', 'Gestao', 'Nivel', 'Trades', 'Pontos', 'Por trade', 'Acerto', 'Fator', 'Rebaix.'],
             [[ROT_MODO[v['modo']], ROT_GESTAO[v['gestao']], R[v['nivel']],
               v['stats']['trades'], sn(v['stats']['lucro_liq']), sn(v['stats']['exp_pts'], 1),
               n(v['stats']['winrate'], 1) + '%', n(v['stats']['fator_lucro'], 2), n(v['stats']['dd_max'])]
              for v in D['variantes'].values()],
             [':---', ':---', ':---'] + ['---:'] * 6))
    w('')

    # ---------------------------------------------------------- filtros
    w('## 5. Cada filtro, medido (base inteira)\n')
    w(f"Conjunto **sem filtro nenhum** -- os {n(D['n_sinais']['confirmados'])} sinais da regra-base, "
      'fechamento, com parcial. Cada terco tem ~44 pregoes. Atencao: na regra-base o 3o terco '
      f"mede {sn(nt['bronze']['por_terco'][2]['ev'], 1)} contra {sn(nt['bronze']['por_terco'][0]['ev'], 1)} "
      f"e {sn(nt['bronze']['por_terco'][1]['ev'], 1)} -- faixa que so e boa no 3o terco e o periodo, "
      'nao o filtro.\n')
    rotulos = {
        'concavidade': 'Concavidade da Hull -- as duas metades medem quase igual',
        'esticamento': 'Distancia do preco a EMA 21 -- sem ordem',
        'pavio': 'Pavio total do candle de continuacao -- so a ponta acima de 90 continua ruim',
        'pavio_favor': 'Pavio a favor do movimento -- acima de 10% perde nos tres tercos',
        'pavio_contra': 'Pavio contra o movimento -- some no ultimo terco',
        'retracao_candles': 'Tamanho da retracao em candles -- **3+ paga nos tres tercos**',
        'retracao_tamanho': 'Tamanho da retracao em ATRs -- acima de 2 ATR paga nos tres tercos',
        'inclinacao_hull': 'Inclinacao da Hull -- muito inclinada mede mal, sem estabilidade',
        'inclinacao_ema': 'Inclinacao da EMA 21 -- sem ordem; e quase o esticamento '
                          f"(correlacao {n(D['estudos']['extra']['corr_ema_estic'], 2)})",
        'banda_keltner': 'Distancia da Hull a banda de Keltner -- nao separa nada',
        'hull_colada': 'Hull colada na EMA -- nao se confirma',
        'hora': 'Horario -- 10h-12h melhor, 9h-10h e depois das 15h piores; pequeno e instavel',
    }
    for k, rot in rotulos.items():
        if k not in D['estudos']:
            continue
        w(f'### {rot}\n')
        w(tabela(['Faixa', 'Sinais', 'Por trade', 'Acerto', '1o terco', '2o terco', '3o terco'],
                 [[r['faixa'], r['n'], sn(r['ev'], 1), n(r['wr'], 1) + '%']
                  + [sn(x, 1) if x is not None else '-' for x in r['ev_terco']]
                  for r in D['estudos'][k]]))
        w('')

    # ---------------------------------------------------------- gestao
    w('## 6. Stop, alvo, parcial e medias (nivel Ouro)\n')
    g = D['grade']
    w('Grade sem parcial -- valor esperado por trade e, entre parenteses, por **ponto de risco**:\n')
    w(tabela(['stop \\ alvo'] + [f"{x} pts" for x in g['alvos']],
             [[f"**{l[0]['stop']}**"] +
              [f"{sn(c['ev'], 1)} ({c['ev_risco']:.2f})"
               + ('  <-' if c['stop'] == P['stop'] and c['alvo'] == P['alvo'] else '')
               for c in l] for l in g['puro']]))
    w('')
    w('Na base antiga toda a grade era positiva e o 300/100 era topo local. Agora a grade fica '
      'perto de zero e o que mede melhor e o alvo curto (100 pontos).\n')
    w('Diagonal risco:retorno (sem parcial) -- por ponto de risco (valor esperado):\n')
    w(tabela(['stop'] + [f"1:{c['razao']}" for c in D['rr'][0]],
             [[f"**{l[0]['stop']}**"] +
              [f"{n(c['ev_risco'], 2)} ({sn(c['ev'], 0)})" + ('  <-' if c['padrao'] else '') for c in l]
              for l in D['rr']]))
    w('')
    o = D['variantes']['fecha|parcial|ouro']['stats']
    pu = D['variantes']['fecha|puro|ouro']['stats']
    r2 = D['variantes']['fecha|r2|ouro']['stats']
    w(tabela(['Ouro, carteira', '1:3 com parcial', '1:3 sem parcial', '1:2 sem parcial'], [
        ['Total', sn(o['lucro_liq']), sn(pu['lucro_liq']), sn(r2['lucro_liq'])],
        ['Por trade', sn(o['exp_pts'], 1), sn(pu['exp_pts'], 1), sn(r2['exp_pts'], 1)],
        ['Acerto', n(o['winrate'], 1) + '%', n(pu['winrate'], 1) + '%', n(r2['winrate'], 1) + '%'],
        ['Fator de lucro', n(o['fator_lucro'], 2), n(pu['fator_lucro'], 2), n(r2['fator_lucro'], 2)],
        ['Rebaixamento', n(o['dd_max']), n(pu['dd_max']), n(r2['dd_max'])],
    ]))
    w('')
    w('**Periodos de media** (a EMA e sempre o meio do Keltner):\n')
    w(tabela(['EMA / ATR', 'Hull', 'Sinais base', 'Por trade (base)', 'Sinais Ouro', 'Por trade (Ouro)'],
             [[m['ema'], m['hull'], m['n_base'], sn(m['ev_base'], 1), m['n_ouro'],
               sn(m['ev_ouro'], 1) + ('  <- CLAUDE.md' if m['padrao'] else '')] for m in D['medias']]))
    w('')
    w('A Hull 50 deixou de ser a melhor; a unica regularidade e a Hull 21 ser a pior em qualquer EMA.\n')
    w('**Custo por operacao** (Ouro, carteira):\n')
    w(tabela(['Custo ida e volta', 'Por trade', 'Total', 'Fator de lucro'],
             [[f"{c['custo']} pts (R$ {n(c['custo'] * P['val_ponto'], 2)})", sn(c['ev'], 1),
               sn(c['total']), n(c['fl'], 2)] for c in D['custos']]))
    w('')

    # ---------------------------------------------------------- antecipada
    w('## 7. A entrada antecipada nao pode ser medida com OHLC\n')
    w('A ordem stop no meio do corpo dispara dentro do candle seguinte. Quando esse candle fecha '
      'a favor mas tem pavio contra que alcanca o stop, o OHLC nao diz se o pavio veio antes ou '
      'depois do disparo. A engine assume "antes" -- a leitura otimista para esta entrada.\n')
    w(tabela(['Gestao / nivel', 'Sinais', 'Ambiguos', 'Convencao', 'Caminho aleatorio', 'Todo ambiguo toma stop'],
             [[f"{ROT_GESTAO[k.split('|')[0]]} / {R[k.split('|')[1]]}", r['n'], n(r['ambiguos_pct'], 1) + '%',
               sn(r['ev_conv'], 1), f"**{sn(r['ev_aleat'], 1)}**", sn(r['ev_pess'], 1)]
              for k, r in O['antecipa'].items()]))
    w('')
    w('"Caminho aleatorio": probabilidade de o stop ter vindo depois do disparo tirada de um '
      'passeio aleatorio de ticks condicionado a forma do candle (28% a 40%). O cenario neutro fica '
      'perto de zero. Decidir exige o caminho dentro do candle (tick a tick ou grafico de 1 PI).\n')

    # ------------------------------------------------------ fluxo
    F = D.get('fluxo')
    if F:
        esp = F['espaco']
        pen = {r['nivel']: r for r in F['peneira']}
        w('## 8. Agressao, tempo de barra e forca de tendencia\n')
        w('A base do robo traz agressao compradora/vendedora e duracao da barra; nao traz volume '
          'total nem numero de negocios (o "volume" aqui e o agressor, correlacao 0,995 com o '
          f"total na base antiga). {esp['feats']} atributos x {esp['cortes']} cortes x 2 sentidos "
          f"= {esp['total']} comparacoes, e a mesma busca repetida {esp['perms']} vezes em dados "
          'embaralhados:\n')
        w(tabela(['Nivel', 'Melhor filtro', 'n', 'EV', 't', 't ruido (mediana)', 'p',
                  '3o terco com filtro', '3o terco sem filtro'],
                 [[R[k], f"{pen[k]['melhor']['rotulo']} {pen[k]['melhor']['sentido']}",
                   n(pen[k]['melhor']['n']), sn(pen[k]['melhor']['ev'], 1), sn(pen[k]['melhor']['t'], 2),
                   sn(pen[k]['ruido_mediana'], 2), n(pen[k]['p_valor'], 2),
                   sn(pen[k]['fora']['ev_t3'], 1), sn(pen[k]['fora']['ev_t3_base'], 1)]
                  for k in ('ouro', 'prata', 'bronze')]))
        w('')
        w('**Nenhum passa.** Hipoteses declaradas, no Ouro:\n')
        w(tabela(['Hipotese', 'n', 'EV', 'ganho', '1o', '2o', '3o', 'p'],
                 [[h['rotulo'], n(h['n']), sn(h['ev'], 1), sn(h['ganho'], 1),
                   sn(h['tercos'][0], 0), sn(h['tercos'][1], 0), sn(h['tercos'][2], 0), n(h['p_valor'], 2)]
                  for h in F['hipoteses'] if h['nivel'] == 'ouro']))
        w('')
        w('Poder (menor ganho detectavel, 80% de poder a 5%):\n')
        w(tabela(['Nivel', 'n', 'Mantem 50%', 'Mantem 33%', 'Mantem 25%'],
                 [[R[r['nivel']], n(r['n'])] + [sn(x['min_ganho'], 0) for x in r['linhas']]
                  for r in F['poder']]))
        w('')
        w('Na base antiga o limiar do Ouro passava de 40 pontos; agora um filtro que mantenha metade '
          'do Bronze apareceria a partir de ~6. O "nao" ja nao e so falta de amostra.\n')
        EFR = F.get('esforco')
        if EFR:
            w('**Esforco x resultado.** A leitura geometrica (`100/range`) e o filtro de pavio '
              f"(correlacao de posto {sn(EFR['geom']['rho'], 4)}). O esforco em volume nao tem relacao "
              f"monotonica com o resultado (rho no Ouro {sn(EFR['rho'][-1]['rho'], 3)}); o corte "
              f"'continuacao mais barata que a retracao' da {sn(EFR['cortes'][1]['ganho'], 1)} pts no "
              f"Ouro (p = {n(EFR['cortes'][1]['p_valor'], 2)}), contra +15,9 na base antiga. Sem numero "
              'de negocios, as variaveis de tamanho de negocio ficaram de fora.\n')

    # ------------------------------------------------------ candidato
    if C:
        G = C['gestoes']; g = G['parcial']; st = g['stats']; b = g['busca']; ba = g['busca_ampla']
        w(f"## 9. Uma hipotese: retracao de {C['n_ret_min']}+ candles\n")
        w('O unico atributo da regra-base que mede bem nos tres tercos, nos dois blocos e nos dois '
          f"lados. Recorte: **Bronze + retracao de {C['n_ret_min']} ou mais candles**, sem outro filtro.\n")
        w(tabela(['Gestao', 'Trades', 'Pontos', 'Por trade', 'Acerto', 'Fator', 'Rebaix.', 'Antes', 'Original',
                  'MC lucro', 'Com 5 pts de custo'],
                 [[C['rot_gestao'][k], G[k]['stats']['trades'], sn(G[k]['stats']['lucro_liq']),
                   sn(G[k]['stats']['exp_pts'], 1), n(G[k]['stats']['winrate'], 1) + '%',
                   n(G[k]['stats']['fator_lucro'], 2), n(G[k]['stats']['dd_max']),
                   sn(G[k]['blocos']['antes']['ev'], 1), sn(G[k]['blocos']['original']['ev'], 1),
                   n(G[k]['mc'].get('prob_lucro'), 1) + '%', sn(G[k]['custos'][2]['ev'], 1)]
                  for k in ('parcial', 'puro', 'r2', 'r1')]))
        w('')
        w('Tercos (1:3 com parcial): ' + ' / '.join(f"{x['terco']} {sn(x['ev'], 1)} ({x['n']})" for x in g['tercos'])
          + '. Meses: ' + ' / '.join(f"{m['mes'][5:]} {sn(m['ev'], 1)}" for m in g['meses']) + '.\n')
        w('**Por que e hipotese e nao setup.** O corte foi escolhido depois de ver a tabela de '
          'retracao nesta base.\n')
        w(f"- Busca so entre cortes de retracao: melhor t = {sn(b['melhor']['t'], 2)}; em ruido, mediana "
          f"{sn(b['ruido_mediana'], 2)}; p = {n(b['p_valor'], 3)}. Passa.")
        w(f"- Busca entre todas as tabelas olhadas ({ba['atributos']} atributos, {ba['cortes']} cortes): "
          f"o melhor ainda e a retracao (t = {sn(ba['melhor']['t'], 2)}), mas o ruido acha "
          f"{sn(ba['ruido_mediana'], 2)} na mediana e {sn(ba['ruido_p95'], 2)} no p95; p = "
          f"{n(ba['p_valor'], 2)}. **Nao passa.**\n")
        w('O protocolo para medir a hipotese em pregoes futuros esta em [PLANO.md](PLANO.md).\n')

    # ---------------------------------------------------------- limites
    w('## 10. O que este backteste nao mediu\n')
    w('- **Slippage.** Entradas no preco exato do fechamento, saidas no preco exato do stop/alvo.\n'
      '- **Caminho dentro do candle.** So OHLC; convencao conservadora para a entrada no fechamento '
      '(e otimista para a antecipada, secao 7).\n'
      '- **Duracao com resolucao de minuto.** A base do robo nao tem segundos.\n'
      '- **Um instrumento, um contrato.**\n')

    # ---------------------------------------------------------- conclusao
    w('## 11. Conclusao\n')
    w(f"O setup Ouro nao sobreviveu a base maior: {sn(ou['antes']['ev'], 1)} pts por trade nos pregoes "
      f"que nao participaram da escolha dos filtros, {sn(s['exp_pts'], 1)} na base inteira. Os tercos "
      'de 26 pregoes eram tres pedacos do mesmo mes e meio de mercado, e nao robustez.\n')
    w('- **Nao operar o Ouro nem o Prata**, e nao ligar `Robo-NTSL/MomentumPI_OuroPrata_Robo.ntsl` em conta real.\n'
      '- **A antecipada** so parece boa por uma convencao de caminho; precisa de dado intra-candle.\n'
      '- **A retracao profunda** e a hipotese a medir daqui para frente, sem mexer em nada.\n'
      '- **O estudo `hull_contra`** (Hull a favor + 2 a 4 candles contra) foi refeito e e o unico cuja '
      'hipotese previa passou no teste fora da amostra -- ver `HULL_CONTRA.md`.\n')
    w('---\n')
    w(f"*Gerado por `python rodar.py && python candidato.py && python relatorio.py`. Base: "
      f"{n(a['candles'])} candles, {a['dias']} pregoes. Backteste nao e promessa.*")

    with open(destino, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
