# Finanças pessoais

App local (Streamlit + SQLite) para analisar gastos a partir do extrato do Banco Inter e das
faturas do cartão Inter: entradas × saídas, categorias, desvios, gastos programados e projeção
de saldo. Nada sai do computador.

## Como usar

1. `pip install -r requirements.txt` (só na primeira vez)
2. Dê dois cliques em `iniciar.bat` (ou `python -m streamlit run app.py`)
3. Para atualizar os dados: baixe no app do Inter o extrato em **OFX** e a fatura do cartão em
   **PDF** e envie pela página **Importar e regras** (ou copie para `extrato/` e
   `faturas-cartao/` e clique em Importar). Períodos sobrepostos não duplicam lançamentos.

## Páginas

| Página | O que faz |
|---|---|
| Resumo | Entradas, saídas e resultado por mês; gasto por categoria; evolução de uma categoria |
| Transações | Fila de classificação por favorecido (cria regras) e edição lançamento a lançamento |
| Desvios | Categoria × meta ou média dos meses anteriores; lançamentos atípicos; programado × realizado |
| Programados | Gastos/receitas futuros (mensal, anual, único), sugestões de recorrentes, projeção do saldo, parcelas do cartão a vencer |
| Importar e regras | Importação, categorias e metas mensais, regras de classificação |

## Como as contas são feitas

- **Cartão de crédito**: cada compra entra no mês de **vencimento da fatura** (quando o dinheiro
  sai da conta). Quando o PDF de uma fatura é importado, o pagamento dela no extrato vira
  transferência, para não contar em dobro. Sem o PDF, o pagamento aparece inteiro em
  "Cartão Inter (fatura sem detalhe)".
- **Transferências** (categorias do tipo `transferencia`: entre contas próprias, investimentos)
  ficam fora de entradas e saídas.
- **Classificação**: categoria escolhida à mão > regra `exata` (favorecido) > regra `contem`
  (o texto mais longo vence) > "A classificar".
- **Desvio de categoria**: fora da faixa quando a diferença para a referência passa de 20% e de
  R$ 50. A referência é a meta mensal da categoria ou a média de até 6 meses anteriores com o
  mesmo nível de detalhe do cartão.
- **Projeção**: saldo do extrato + programados + (opcional) o restante típico, que é a mediana
  dos 6 últimos meses fechados menos o que já está programado como mensal.

## Arquivos

- `app.py` — interface
- `financas/importar.py` — leitura de OFX, CSV e PDF da fatura
- `financas/categorias.py` — categorias e regras iniciais, normalização das descrições
- `financas/analise.py` — resumo, desvios, conciliação, recorrências e projeção
- `financas.db` — banco local (criado na primeira execução). Para recomeçar do zero, apague-o.

`extrato/`, `faturas-cartao/` e `financas.db` estão no `.gitignore`: dados financeiros não vão
para o GitHub.
