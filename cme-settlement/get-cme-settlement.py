import argparse
import re
from curl_cffi import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# ----------------------------------------------------
# Configurações
# ----------------------------------------------------

PRODUCTS = {
    "ES": 133,     # E-mini S&P 500
    "YM" : 318,    # E-mini Dow
    "NQ": 146,     # E-mini Nasdaq 100
    "GC": 437,     # NOVO: COMEX Gold (ouro) -> XAUUSD
}

NUM_DAYS = 5              # Quantos pregões deseja obter

URL = "https://www.cmegroup.com/CmeWS/mvc/Settlements/Futures/Settlements/{}/FUT"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.cmegroup.com/",
    "Origin": "https://www.cmegroup.com",
    "Connection": "keep-alive",
}

# ----------------------------------------------------

# Extrai o valor numérico de um campo da CME ("last", "high", "low"...),
# que pode vir como "5900.25", "5,900.25", "5900.25A", "5900.25s",
# "UNCH", "N/A", etc.
def parse_num(value):
    if value is None:
        return None

    s = str(value).strip()

    if s == "" or s.upper() in ("UNCH", "N/A", "NA", "-", "UNCHANGED"):
        return None

    s = s.replace(",", "")

    m = re.match(r"^-?\d+(\.\d+)?", s)

    if not m:
        return None

    try:
        return float(m.group())
    except ValueError:
        return None


# NOVO: posição do ajuste dentro do range (máxima/mínima) do dia, em %:
#     0% = ajuste exatamente na mínima do dia
#   100% = ajuste exatamente na máxima do dia
#    50% = ajuste no meio do range
# Pode sair da faixa 0..100 quando o settlement da CME cai fora do range
# efetivamente negociado (acontece eventualmente).
def calc_pct(settle, high, low):
    if settle is None or high is None or low is None:
        return None

    amplitude = high - low

    if amplitude <= 0:
        return None

    return round((settle - low) / amplitude * 100.0, 4)


# NOVO: escolhe o contrato de referência do dia.
#
# Não dá para usar simplesmente o primeiro da lista: nos índices (ES/NQ/YM)
# o primeiro é o mais líquido, mas no ouro (GC) a CME lista todos os meses
# e o primeiro costuma ser um mês quase sem negócio. Ex.: em 25/08/2026 o
# primeiro era AUG 26 (volume 321, range de 5,8 pts, com o ajuste FORA do
# range -> pct de 205%), enquanto o contrato real era DEZ 26 (volume 176.784).
#
# Critério: maior volume e, em caso de empate, maior contratos em aberto,
# considerando só os meses com máxima/mínima válidas.
def escolhe_contrato(contratos):
    candidatos = [
        c for c in contratos
        if c.get("month") != "Total"
        and parse_num(c.get("high")) is not None
        and parse_num(c.get("low")) is not None
        and parse_num(c.get("settle")) is not None
    ]

    if not candidatos:
        return None

    return max(
        candidatos,
        key=lambda c: (parse_num(c.get("volume")) or 0.0,
                       parse_num(c.get("openInterest")) or 0.0)
    )


def consulta_data(product_id, data):

    params = {
        "strategy": "DEFAULT",
        "tradeDate": data.strftime("%m/%d/%Y"),
        "pageSize": 500,
        "isProtected": "",
        "_t": int(datetime.now().timestamp()*1000)
    }

    r = requests.get(
        URL.format(product_id),
        params=params,
        impersonate="chrome"
    )

    r.raise_for_status()

    return r.json()


# ----------------------------------------------------

resultado = []

data = datetime.today()

print("Obtendo settlements...")

for SYMBOL, PRODUCT_ID in PRODUCTS.items():

    print(f"\n====================")
    print(f"Ativo: {SYMBOL}")
    print(f"====================")

    data = datetime.today()

    tentativas = 0
    max_tentativas = max(7, NUM_DAYS * 2)

    while len([r for r in resultado if r["symbol"] == SYMBOL]) < NUM_DAYS and tentativas < max_tentativas:

        tentativas += 1

        try:

            print(f"Consultando {data.strftime('%Y-%m-%d')}...")

            js = consulta_data(PRODUCT_ID, data)

            if not js.get("empty", True):

                contratos = js["settlements"]

                if contratos:

                    # NOVO: contrato mais líquido do dia, não o primeiro da lista
                    primeiro = escolhe_contrato(contratos)

                    if primeiro is not None:

                        settle_val = parse_num(primeiro["settle"])
                        last_num = parse_num(primeiro["last"])
                        high_num = parse_num(primeiro["high"])   # NOVO
                        low_num  = parse_num(primeiro["low"])    # NOVO

                        # distância = fechamento (last) - ajuste (settle)
                        # mantida apenas como diagnóstico/compatibilidade
                        distancia = round(last_num - settle_val, 2) if last_num is not None else None

                        # NOVO: posição do ajuste dentro do range do dia (0..100%)
                        pct = calc_pct(settle_val, high_num, low_num)

                        registro = {
                            "symbol": SYMBOL,
                            "tradeDate": js["tradeDate"],
                            "contract": primeiro["month"],
                            "settle": settle_val,
                            "last": primeiro["last"],
                            "distancia": distancia,
                            "pct": pct,               # NOVO
                            "open": primeiro["open"],
                            "high": primeiro["high"],
                            "low": primeiro["low"],
                            "volume": primeiro["volume"],
                            "openInterest": primeiro["openInterest"]
                        }

                        resultado.append(registro)

                        print(
                            f'OK {registro["tradeDate"]} '
                            f'{registro["contract"]} '
                            f'Settle={registro["settle"]} '
                            f'Dist={registro["distancia"]} '
                            f'Pct={registro["pct"]}'   # NOVO
                        )

        except Exception as e:
            print(e)

        data -= timedelta(days=1)

# ----------------------------------------------------
# Ordena cronologicamente
# ----------------------------------------------------

resultado.reverse()

df = pd.DataFrame(resultado)

# ----------------------------------------------------
# CSV completo
# ----------------------------------------------------

arquivo = Path("settlements_full.csv")

if arquivo.exists():
    antigo = pd.read_csv(arquivo)
else:
    antigo = pd.DataFrame()

novo = pd.concat([antigo, df], ignore_index=True)

# Converte qualquer formato para datetime
novo["tradeDate"] = pd.to_datetime(
    novo["tradeDate"],
    format="mixed"
)

# Padroniza
novo["tradeDate"] = novo["tradeDate"].dt.strftime("%Y-%m-%d")

# Agora remove duplicados
novo.drop_duplicates(
    subset=["symbol", "tradeDate"],
    keep="last",
    inplace=True
)

mask = novo["tradeDate"].str.contains("/", na=False)

novo.loc[mask, "tradeDate"] = pd.to_datetime(
    novo.loc[mask, "tradeDate"],
    format="%m/%d/%Y"
).dt.strftime("%Y-%m-%d")

novo["tradeDate"] = pd.to_datetime(novo["tradeDate"])

novo.sort_values(
    ["symbol", "tradeDate"],
    inplace=True
)

novo["tradeDate"] = novo["tradeDate"].dt.strftime("%Y-%m-%d")

# NOVO: recalcula "distancia" e "pct" retroativamente para TODAS as linhas
# (inclusive as que já existiam no CSV antes destas colunas existirem),
# usando "last", "settle", "high" e "low" já armazenados.
novo["_last_num"] = novo["last"].apply(parse_num)
novo["_high_num"] = novo["high"].apply(parse_num)
novo["_low_num"]  = novo["low"].apply(parse_num)

novo["distancia"] = (novo["_last_num"] - novo["settle"]).round(2)

novo["pct"] = [
    calc_pct(s, h, l)
    for s, h, l in zip(novo["settle"], novo["_high_num"], novo["_low_num"])
]

novo.drop(columns=["_last_num", "_high_num", "_low_num"], inplace=True)

# Ordem estável das colunas
colunas = ["symbol", "tradeDate", "contract", "settle", "last",
           "distancia", "pct", "open", "high", "low",
           "volume", "openInterest"]
novo = novo[[c for c in colunas if c in novo.columns]]

novo.to_csv(
    arquivo,
    index=False
)

# ----------------------------------------------------
# CSV simples (para MT5)
# ----------------------------------------------------
df2 = novo[["symbol", "tradeDate", "settle", "distancia", "pct"]].copy()

# NOVO: sem "pct" o indicador não consegue projetar o ajuste no ativo cash
faltando = int(df2["pct"].isna().sum())

if faltando:
    print(f"\nAviso: {faltando} linha(s) sem 'pct' (range do dia indisponível).")

df2.sort_values(
    ["symbol", "tradeDate"],
    inplace=True
)

df2['tradeDate'] = pd.to_datetime(df2['tradeDate'], errors='coerce')
df2['tradeDate'] = df2['tradeDate'].dt.strftime('%Y/%m/%d')

parser = argparse.ArgumentParser(description="A script that processes a file path.")
parser.add_argument(
    "input_path",
    type=Path,
    help="The path to the file or directory you want to process"
)
args = parser.parse_args()

# NOVO: junta o caminho com "/" do pathlib (funciona no Windows e no Linux)
destino = args.input_path / "settlements.csv"

print(f"Target path received: {destino}")

if args.input_path.exists():
    print(f"Saving simple settlements.csv in {destino}")
    df2.to_csv(
    destino,
    index=False
    )
else:
    print(f"Error: That path {destino} does not exist, saving in execution directory.")
    df2.to_csv(
    "settlements.csv",
    index=False
    )

print()
print(df2)

print("\nArquivos gerados:")
print("  settlements.csv")
print("  settlements_full.csv")