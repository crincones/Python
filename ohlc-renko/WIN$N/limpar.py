import pandas as pd

# 1. Carrega o CSV especificando o separador ';'
df = pd.read_csv('Renko11R.csv', sep=';')

# 2. Lista das colunas que deseja apagar
colunas_para_remover = ['AgressionVolBuy', 'AgressionVolSell', 'VolIndefinido']

# 3. Remove as colunas (errors='ignore' evita erro caso alguma coluna não exista)
df = df.drop(columns=colunas_para_remover, errors='ignore')

# 4. Salva o resultado em um novo arquivo CSV
df.to_csv('resultado.csv', sep=';', index=False)

print("Colunas removidas com sucesso!")