@echo off
rem Gera lista_opcoes_liquidez.csv: top 20 ativos por liquidez das opcoes (dados publicos da B3).
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
where uv >nul 2>nul
if %errorlevel%==0 (
    uv run --no-project python gerar_lista.py %*
) else (
    python gerar_lista.py %*
)
echo.
pause
