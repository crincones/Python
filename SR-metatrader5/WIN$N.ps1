# lembra de rodar primeiro: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

python C:\Users\Carlos\Documents\GitHub\Python\baixar-ohlc-fx\atualiza-historico.py --symbol 'WIN$N'

python main.py --symbol 'WIN$N' --ref 177375 --sep 100 --desde "2021-01-01" --ate "2026-08-26" --box-ticks 50 --top 50 --faixa 10000 --vao-max 500 --metodo "dbscan" --min-eventos 2