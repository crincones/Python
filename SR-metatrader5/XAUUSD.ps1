# lembra de rodar primeiro: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

python C:\Users\Carlos\Documents\GitHub\Python\baixar-ohlc-fx\atualiza-historico.py --symbol XAUUSD

python main.py --symbol XAUUSD --ref 4641 --box-ticks 200 --sep 500 --top 50 --ate "2026-08-25" --faixa 80000 --vao-max 1500 --metodo "dbscan" --min-eventos 2