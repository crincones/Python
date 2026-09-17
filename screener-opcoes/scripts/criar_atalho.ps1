<#
.SYNOPSIS
    Cria na Area de Trabalho o atalho "Relatorio-Opcoes" para a pasta output\ do projeto.
#>
[CmdletBinding()]
param(
    [string]$Nome = 'Relatorio-Opcoes'
)

$ErrorActionPreference = 'Stop'
$Projeto = Split-Path -Parent $PSScriptRoot
$Output = Join-Path $Projeto 'output'
New-Item -ItemType Directory -Force -Path $Output | Out-Null

# GetFolderPath respeita a Area de Trabalho redirecionada (ex.: OneDrive).
$AreaDeTrabalho = [Environment]::GetFolderPath('Desktop')
$Atalho = Join-Path $AreaDeTrabalho ($Nome + '.lnk')

$Shell = New-Object -ComObject WScript.Shell
$Lnk = $Shell.CreateShortcut($Atalho)
$Lnk.TargetPath = $Output
$Lnk.WorkingDirectory = $Output
$Lnk.Description = 'Relatorios HTML do screener de travas de debito'
$Lnk.Save()

Write-Host "Atalho criado: $Atalho -> $Output"
