<#
.SYNOPSIS
    Cria (ou remove) a tarefa do Agendador de Tarefas do Windows que roda o screener.

.DESCRIPTION
    Uma tarefa com um disparo por horario, de segunda a sexta, executando
    scripts\executar_screener.ps1 (etapa run). Feriados da B3 sao tratados pelo proprio
    screener, que encerra sem fazer nada. Roda apenas com o usuario logado: se o terminal MT5
    estiver fechado, o screener o abre na sessao do usuario e fecha ao terminar. Execucoes
    perdidas (PC desligado ou suspenso) nao sao repetidas depois.

.PARAMETER Horarios
    Horarios no formato HH:mm. Padrao: 10:30, 13:00 e 16:30.

.PARAMETER Remover
    Remove a tarefa.

.EXAMPLE
    .\scripts\agendar_tarefas.ps1
    .\scripts\agendar_tarefas.ps1 -Horarios 11:00,15:00
    .\scripts\agendar_tarefas.ps1 -Remover
#>
[CmdletBinding()]
param(
    [string[]]$Horarios = @('10:30', '13:00', '16:30'),
    [string]$NomeTarefa = 'Screener Opcoes B3',
    [switch]$Remover
)

$ErrorActionPreference = 'Stop'

if ($Remover) {
    Unregister-ScheduledTask -TaskName $NomeTarefa -Confirm:$false
    Write-Host "Tarefa '$NomeTarefa' removida."
    return
}

$Projeto = Split-Path -Parent $PSScriptRoot
$Script = Join-Path $PSScriptRoot 'executar_screener.ps1'
$Argumento = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}"' -f $Script
$Acao = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $Argumento -WorkingDirectory $Projeto

$DiasUteis = 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'
$Disparos = foreach ($Horario in $Horarios) {
    $Hora = [datetime]::ParseExact($Horario, 'HH:mm', [Globalization.CultureInfo]::InvariantCulture)
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DiasUteis -At $Hora
}

$Config = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries
$Usuario = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $NomeTarefa -Action $Acao -Trigger $Disparos -Settings $Config `
    -Principal $Usuario -Force `
    -Description 'Screener de travas de debito B3 (MT5/XP): coleta, analise e relatorio em output\.' | Out-Null

$Tarefa = Get-ScheduledTask -TaskName $NomeTarefa
$Info = $Tarefa | Get-ScheduledTaskInfo
Write-Host "Tarefa '$NomeTarefa' registrada. Horarios (seg-sex): $($Horarios -join ', ')"
Write-Host "Proxima execucao: $($Info.NextRunTime)"
