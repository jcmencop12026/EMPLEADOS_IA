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

function ConvertTo-EiaaxPlainShellOutput {
    param(
        [AllowNull()]
        [string]$Text
    )

    if ([string]::IsNullOrEmpty($Text)) {
        return ""
    }
    if ($Text -notmatch '(?s)<Objs Version=') {
        return $Text
    }

    $lines = New-Object System.Collections.Generic.List[string]
    $messageMatches = [regex]::Matches($Text, '<S N="Message">([^<]*)</S>')
    foreach ($match in $messageMatches) {
        if ($match.Groups.Count -gt 1) {
            $line = $match.Groups[1].Value
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                [void]$lines.Add($line)
            }
        }
    }

    $toStringMatches = [regex]::Matches($Text, '<ToString>([^<]*)</ToString>')
    foreach ($match in $toStringMatches) {
        if ($match.Groups.Count -gt 1) {
            $line = $match.Groups[1].Value
            if (-not [string]::IsNullOrWhiteSpace($line) -and -not $lines.Contains($line)) {
                [void]$lines.Add($line)
            }
        }
    }

    if ($lines.Count -gt 0) {
        return ($lines -join "`n")
    }

    return $Text
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
        $stdoutFile = $null
        $stderrFile = $null
        try {
            $stdoutFile = [System.IO.Path]::GetTempFileName()
            $stderrFile = [System.IO.Path]::GetTempFileName()
            $encoded = [Convert]::ToBase64String(
                [System.Text.Encoding]::Unicode.GetBytes($CommandText)
            )
            $process = Start-Process -FilePath $ShellPath `
                -ArgumentList @(
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy", "Bypass",
                    "-EncodedCommand", $encoded
                ) `
                -Wait -PassThru -NoNewWindow `
                -RedirectStandardOutput $stdoutFile `
                -RedirectStandardError $stderrFile
            if ($null -eq $process) {
                throw "Failed to start shell test process"
            }

            $stdout = ""
            $stderr = ""
            if (Test-Path -LiteralPath $stdoutFile) {
                $stdout = Get-Content -LiteralPath $stdoutFile -Raw -ErrorAction SilentlyContinue
            }
            if (Test-Path -LiteralPath $stderrFile) {
                $stderr = Get-Content -LiteralPath $stderrFile -Raw -ErrorAction SilentlyContinue
            }

            $combined = ""
            if (-not [string]::IsNullOrEmpty($stdout)) {
                $combined += $stdout
            }
            if (-not [string]::IsNullOrEmpty($stderr)) {
                if ($combined.Length -gt 0) {
                    $combined += "`n"
                }
                $combined += $stderr
            }

            return [ordered]@{
                ExitCode = [int]$process.ExitCode
                Output   = $combined
            }
        }
        finally {
            $ErrorActionPreference = $previous
            if ($null -ne $stdoutFile) {
                Remove-Item -LiteralPath $stdoutFile -ErrorAction SilentlyContinue
            }
            if ($null -ne $stderrFile) {
                Remove-Item -LiteralPath $stderrFile -ErrorAction SilentlyContinue
            }
        }
    } -ArgumentList $shell, $Script

    $completed = Wait-Job -Job $job -Timeout $TimeoutSec
    if ($null -eq $completed) {
        Stop-Job -Job $job -ErrorAction SilentlyContinue
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
        throw ("Shell test timed out after " + $TimeoutSec + " seconds")
    }

    $result = Receive-Job -Job $job
    $state = $job.State
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    if ($state -eq "Failed") {
        throw ($result | Out-String)
    }

    if ($null -ne $result) {
        $plainOutput = ConvertTo-EiaaxPlainShellOutput -Text $result.Output
        return [ordered]@{
            ExitCode = [int]$result.ExitCode
            Output   = $plainOutput
        }
    }

    return $result
}

$script:EiaaxTestEnvBackup = @{}

function Save-EiaaxTestEnvVar {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $script:EiaaxTestEnvBackup[$Name] = [Environment]::GetEnvironmentVariable($Name, "Process")
}

function Restore-EiaaxTestEnvVar {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not $script:EiaaxTestEnvBackup.ContainsKey($Name)) {
        return
    }

    $previous = $script:EiaaxTestEnvBackup[$Name]
    if ([string]::IsNullOrEmpty($previous)) {
        Remove-Item -Path ("Env:" + $Name) -ErrorAction SilentlyContinue
    }
    else {
        Set-Item -Path ("Env:" + $Name) -Value $previous
    }
}

function Restore-All-EiaaxTestEnvVars {
    foreach ($name in @($script:EiaaxTestEnvBackup.Keys)) {
        Restore-EiaaxTestEnvVar -Name $name
    }
    $script:EiaaxTestEnvBackup = @{}
}

function Clear-EiaaxTestEnvVar {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    Save-EiaaxTestEnvVar -Name $Name
    Remove-Item -Path ("Env:" + $Name) -ErrorAction SilentlyContinue
}

function Set-EiaaxTestEnvVar {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [AllowNull()]
        [string]$Value
    )

    Save-EiaaxTestEnvVar -Name $Name
    if ([string]::IsNullOrEmpty($Value)) {
        Remove-Item -Path ("Env:" + $Name) -ErrorAction SilentlyContinue
    }
    else {
        Set-Item -Path ("Env:" + $Name) -Value $Value
    }
}

function Get-EiaaxKnownWindowsPythonExe {
    foreach ($candidate in @(
            "C:\Python314\python.exe",
            "C:\Python313\python.exe",
            "C:\Python312\python.exe"
        )) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    return $null
}

function Invoke-EiaaxProductionShellTest {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommonPath,
        [Parameter(Mandatory = $true)]
        [string]$Body,
        [int]$TimeoutSec = $script:DefaultTestTimeoutSec
    )

    $escapedCommon = $CommonPath.Replace("'", "''")
    $scriptText = @"
`$ErrorActionPreference = 'Stop'
. '$escapedCommon'
$Body
"@

    return Invoke-EiaaxTestShellCommand -Script $scriptText -TimeoutSec $TimeoutSec
}
