# lembra de rodar primeiro: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

python C:\Users\Carlos\Documents\GitHub\Python\baixar-ohlc-fx\atualiza-historico.py --symbol NAS100

python main.py --symbol NAS100 --ref 29477 --box-ticks 100 --sep 400 --top 50 --ate "2026-08-26" --faixa 10000 --vao-max 600 --metodo "dbscan" --min-eventos 2