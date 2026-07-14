import yfinance as yf

ticker = yf.Ticker("ES=F")
print(ticker.info)        # Aqui pode aparecer informações de settlement