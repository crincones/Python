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

# NOVO: extrai o valor numérico do campo "last", que pode vir como
# "5900.25", "5,900.25", "5900.25A", "5900.25s", "UNCH", "N/A", etc.
def parse_last_price(value):
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

                    primeiro = contratos[0]

                    if primeiro["month"] != "Total":

                        settle_val = float(primeiro["settle"])
                        last_num = parse_last_price(primeiro["last"])  # NOVO

                        # NOVO: distância = fechamento (last) - ajuste (settle)
                        # positivo = fechamento acima do ajuste
                        # negativo = fechamento abaixo do ajuste
                        distancia = round(last_num - settle_val, 2) if last_num is not None else None

                        registro = {
                            "symbol": SYMBOL,
                            "tradeDate": js["tradeDate"],
                            "contract": primeiro["month"],
                            "settle": settle_val,
                            "last": primeiro["last"],
                            "distancia": distancia,   # NOVO
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
                            f'Dist={registro["distancia"]}'   # NOVO
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

# NOVO: recalcula "distancia" retroativamente para TODAS as linhas
# (inclusive as que já existiam no CSV antes desta coluna existir),
# usando o "last" e "settle" já armazenados.
novo["_last_num"] = novo["last"].apply(parse_last_price)
novo["distancia"] = (novo["_last_num"] - novo["settle"]).round(2)
novo.drop(columns=["_last_num"], inplace=True)

novo.to_csv(
    arquivo,
    index=False
)

# ----------------------------------------------------
# CSV simples (para MT5)
# ----------------------------------------------------
df2 = novo[["symbol", "tradeDate", "settle", "distancia"]].copy()

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

print(f"Target path received: {args.input_path}settlements.csv")

if args.input_path.exists():
    print(f"Saving simple settlements.csv in {args.input_path}\\settlements.csv")
    df2.to_csv(
    fr"{args.input_path}\settlements.csv",
    index=False
    )
else:
    print(f"Error: That path {args.input_path}\\settlements.csv does not exist, saving in execution directory.")
    df2.to_csv(
    "settlements.csv",
    index=False
    )

print()
print(df2)

print("\nArquivos gerados:")
print("  settlements.csv")
print("  settlements_full.csv")