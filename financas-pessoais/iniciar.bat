@echo off
rem Abre o app de financas pessoais no navegador (http://localhost:8501).
rem Feche esta janela para encerrar.
cd /d "%~dp0"
python -m streamlit run app.py --browser.gatherUsageStats false
pause
