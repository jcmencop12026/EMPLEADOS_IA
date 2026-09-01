#Requires -Version 5.1
<#
.SYNOPSIS
    Shared non-interactive helpers for EIAAX Windows autotests.
#>

Set-StrictMode -Version Latest

$script:DefaultTestTimeoutSec = 30

function Invoke-EiaaxTestWithTimeout {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action,
        [int]$TimeoutSec = $script:DefaultTestTimeoutSec
    )

    $job = Start-Job -Name $Name -ScriptBlock $Action
    $completed = Wait-Job -Job $job -Timeout $TimeoutSec
    if ($null -eq $completed) {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        throw ("Timed out after " + $TimeoutSec + " seconds")
    }

    $output = Receive-Job -Job $job
    $state = $job.State
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue

    if ($state -eq "Failed") {
        throw ($output | Out-String)
    }

    return $output
}

function Get-EiaaxNonInteractiveTestExecutable {
    if (-not [string]::IsNullOrWhiteSpace($env:WINDIR)) {
        $hostname = Join-Path $env:WINDIR "System32\hostname.exe"
        if (Test-Path -LiteralPath $hostname) {
            return $hostname
        }

        $cmd = Join-Path $env:WINDIR "System32\cmd.exe"
        if (Test-Path -LiteralPath $cmd) {
            return $cmd
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($env:ComSpec) -and (Test-Path -LiteralPath $env:ComSpec)) {
        return $env:ComSpec
    }

    foreach ($candidate in @("/bin/true", "/usr/bin/true", "/bin/hostname", "/usr/bin/hostname")) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

function Invoke-EiaaxAutotestNativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommonPath,
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [AllowEmptyCollection()]
        [string[]]$ArgumentList = @(),
        [string]$FailureMessage = "Native command failed.",
        [int]$TimeoutSec = $script:DefaultTestTimeoutSec
    )

    $job = Start-Job -ScriptBlock {
        param($CommonPath, $FilePath, $ArgumentList, $FailureMessage)
        $ErrorActionPreference = "Stop"
        . $CommonPath
        Invoke-EiaaxNativeCommand -FilePath $FilePath -ArgumentList $ArgumentList -FailureMessage $FailureMessage
    } -ArgumentList $CommonPath, $FilePath, $ArgumentList, $FailureMessage

    $completed = Wait-Job -Job $job -Timeout $TimeoutSec
    if ($null -eq $completed) {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        throw ("Native command test timed out after " + $TimeoutSec + " seconds: " + $FilePath)
    }

    $output = Receive-Job -Job $job
    $state = $job.State
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    if ($state -eq "Failed") {
        throw ($output | Out-String)
    }
}

function Get-EiaaxTestShellExecutable {
    $windowsPowerShell = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    if (Test-Path -LiteralPath $windowsPowerShell) {
        return $windowsPowerShell
    }

    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($null -ne $pwsh) {
        return $pwsh.Source
    }

    $powershell = Get-Command powershell -ErrorAction SilentlyContinue
    if ($null -ne $powershell) {
        return $powershell.Source
    }

    return $null
}

function Invoke-EiaaxTestShellCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Script,
        [int]$TimeoutSec = $script:DefaultTestTimeoutSec
    )

    $shell = Get-EiaaxTestShellExecutable
    if ($null -eq $shell) {
        throw "No PowerShell executable available for shell test"
    }

    $job = Start-Job -ScriptBlock {
        param($ShellPath, $CommandText)
        $previous = $ErrorActionPreference
        $ErrorActionPreference = "Stop"
        try {
            $output = & $ShellPath -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command $CommandText 2>&1 | Out-String
            return [ordered]@{
                ExitCode = $LASTEXITCODE
                Output   = $output
            }
        }
        finally {
            $ErrorActionPreference = $previous
        }
    } -ArgumentList $shell, $Script

    $completed = Wait-Job -Job $job -Timeout $TimeoutSec
    if ($null -eq $completed) {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        throw ("Shell test timed out after " + $TimeoutSec + " seconds")
    }

    $result = Receive-Job -Job $job
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    return $result
}
