<#
.SYNOPSIS
    Executa o screener de travas de debito (B3 via MetaTrader 5 / XP).

.DESCRIPTION
    Roda "uv run screener <etapa>" na pasta do projeto e grava a saida em
    logs\execucao_AAAAMMDD.log (alem do log da aplicacao em logs\screener.log).
    Na etapa "run" (padrao) o screener nao faz nada em fim de semana ou feriado da B3.
    Se o terminal MT5 da XP estiver fechado, o screener o abre minimizado (/portable), espera o
    login automatico e, ao terminar, fecha apenas o terminal que ele mesmo abriu.

.PARAMETER Etapa
    run (coleta + analise + relatorio + publicacao), collect, analyze, report, publish ou check.

.PARAMETER SemPublicar
    Nas etapas run e report: nao envia o relatorio para o servidor da tailnet
    (http://100.113.24.44/screening.html).

.PARAMETER Forcar
    Na etapa run, executa mesmo fora de dia de pregao.

.PARAMETER ManterTerminal
    Nas etapas run e collect: se o terminal MT5 estava fechado e o screener o abriu, mantem
    aberto ao terminar (padrao: fecha o que ele mesmo abriu; terminal ja aberto nunca e fechado).

.PARAMETER AbrirRelatorio
    Ao terminar sem erro, abre o relatorio HTML mais recente de output\.

.EXAMPLE
    .\scripts\executar_screener.ps1
    .\scripts\executar_screener.ps1 -Etapa report -AbrirRelatorio
    .\scripts\executar_screener.ps1 -Etapa publish
#>
[CmdletBinding()]
param(
    [ValidateSet('run', 'collect', 'analyze', 'report', 'publish', 'check')]
    [string]$Etapa = 'run',
    [switch]$Forcar,
    [switch]$SemPublicar,
    [switch]$ManterTerminal,
    [switch]$AbrirRelatorio
)

$ErrorActionPreference = 'Stop'
$Projeto = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $Projeto

$PastaLogs = Join-Path $Projeto 'logs'
New-Item -ItemType Directory -Force -Path $PastaLogs | Out-Null
$LogExecucao = Join-Path $PastaLogs ('execucao_{0:yyyyMMdd}.log' -f (Get-Date))

function Escrever([string]$Texto) {
    Write-Host $Texto
    Add-Content -LiteralPath $LogExecucao -Value $Texto -Encoding UTF8
}

$ComandoUv = Get-Command uv -ErrorAction SilentlyContinue
if ($ComandoUv) {
    $Uv = $ComandoUv.Source
} else {
    $Uv = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
}
if (-not (Test-Path -LiteralPath $Uv)) {
    Escrever "ERRO: uv nao encontrado (procurado no PATH e em $Uv)."
    exit 2
}

$Argumentos = @('run', 'screener', $Etapa)
if ($Forcar -and $Etapa -eq 'run') { $Argumentos += '--force' }
if ($ManterTerminal -and $Etapa -in @('run', 'collect')) { $Argumentos += '--keep-terminal' }
if ($SemPublicar -and $Etapa -in @('run', 'report')) { $Argumentos += '--no-publish' }

# Saida do Python em UTF-8 para acentos corretos no console e no log.
$env:PYTHONIOENCODING = 'utf-8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Escrever ('[{0:yyyy-MM-dd HH:mm:ss}] inicio: uv {1}' -f (Get-Date), ($Argumentos -join ' '))
# stderr do uv (mensagens de build) vem como ErrorRecord no PowerShell 5.1: nao interromper.
$ErrorActionPreference = 'Continue'
& $Uv @Argumentos 2>&1 | ForEach-Object { Escrever ([string]$_) }
$Codigo = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
Escrever ('[{0:yyyy-MM-dd HH:mm:ss}] fim: codigo {1}' -f (Get-Date), $Codigo)

if ($AbrirRelatorio -and $Codigo -eq 0) {
    $Relatorio = Get-ChildItem -LiteralPath (Join-Path $Projeto 'output') -Filter 'relatorio_*.html' -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($Relatorio) {
        Escrever "Abrindo $($Relatorio.FullName)"
        Invoke-Item -LiteralPath $Relatorio.FullName
    }
}
exit $Codigo
