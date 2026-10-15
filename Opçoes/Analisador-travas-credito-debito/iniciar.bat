@echo off
rem Inicia o Analisador de Travas (http://127.0.0.1:8765) e abre o navegador.
cd /d "%~dp0"
uv run travas serve
pause
