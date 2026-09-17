@echo off
rem Screener de travas de debito: coleta + analise + relatorio, e abre o relatorio ao final.
rem Se o terminal MT5 da XP estiver fechado, ele e aberto e fechado automaticamente.
rem Parametros opcionais repassados ao PowerShell, por exemplo:
rem   executar_screener.bat -Forcar            (roda mesmo em fim de semana/feriado)
rem   executar_screener.bat -Etapa report      (so regera o relatorio do ultimo snapshot)
rem   executar_screener.bat -ManterTerminal    (nao fecha o MT5 que o script abriu)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\executar_screener.ps1" -AbrirRelatorio %*
echo.
pause
