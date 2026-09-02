#Requires -Version 5.1
<#
.SYNOPSIS
    Regression tests for non-blocking service startup orchestration.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$helpers = Join-Path $PSScriptRoot "EiaaxDemo.TestHelpers.ps1"
. $helpers

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$failed = 0

function Assert-Test {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Host ("TEST: " + $Name)
    try {
        & $Action
        Write-Host ("  PASS")
    }
    catch {
        $script:failed++
        Write-Host ("  FAIL: " + $_.Exception.Message)
    }
}

Assert-Test "iniciar_demo uses in-process script invocation for backend/frontend" {
    $content = Get-Content -LiteralPath (Join-Path $PSScriptRoot "iniciar_demo_eiaax.ps1") -Raw
    if ($content -notmatch "Invoke-EiaaxScriptInProcess") {
        throw "iniciar_demo_eiaax.ps1 must use Invoke-EiaaxScriptInProcess"
    }
    if ($content -match 'Invoke-EiaaxPowerShellFile -FilePath \$backendScript') {
        throw "backend must not use nested Invoke-EiaaxPowerShellFile"
    }
    if ($content -notmatch "\[4/7\.3\] Iniciando frontend") {
        throw "missing frontend checkpoint"
    }
}

Assert-Test "arrancar uses in-process invocation for start script" {
    $content = Get-Content -LiteralPath (Join-Path $PSScriptRoot "arrancar_convergencia_windows.ps1") -Raw
    if ($content -notmatch 'Invoke-EiaaxScriptInProcess -FilePath \$startScript') {
        throw "arrancar must start demo in-process"
    }
}

Assert-Test "Start-EiaaxManagedProcess detaches service with start /B" {
    $content = Get-Content -LiteralPath $common -Raw
    if ($content -notmatch 'start "EIAAX_') {
        throw "managed process must detach services with start /B"
    }
    if ($content -notmatch '/B cmd /c') {
        throw "managed process must launch detached cmd"
    }
}

Assert-Test "Invoke-EiaaxPowerShellFile redirects output to avoid nested -Wait deadlock" {
    $content = Get-Content -LiteralPath $common -Raw
    if ($content -notmatch "RedirectStandardOutput") {
        throw "task PowerShell invocations must redirect stdout"
    }
    if ($content -notmatch "RedirectStandardError") {
        throw "task PowerShell invocations must redirect stderr"
    }
}

Assert-Test "frontend refuses npm.ps1 for service start" {
    $content = Get-Content -LiteralPath (Join-Path $PSScriptRoot "iniciar_frontend_demo.ps1") -Raw
    if ($content -notmatch "Refusing npm\.ps1") {
        throw "frontend must refuse npm.ps1 launcher"
    }
}

Assert-Test "health helpers use bounded timeout loops" {
    $content = Get-Content -LiteralPath $common -Raw
    foreach ($name in @("Test-EiaaxHealth", "Test-EiaaxFrontendReady", "Test-EiaaxFrontendProxyHealth", "Wait-EiaaxListenerPid")) {
        if ($content -notmatch ("function " + $name)) {
            throw ("missing function " + $name)
        }
    }
    if ($content -notmatch "Wait-EiaaxListenerPid[\s\S]*TimeoutSec") {
        throw "Wait-EiaaxListenerPid must accept timeout"
    }
}

function Get-EiaaxWrapperStartLine {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Lines
    )

    foreach ($line in $Lines) {
        if ($line -match '^start "EIAAX_') {
            return $line
        }
    }

    throw "wrapper start line not found"
}

Assert-Test "wrapper quotes npm.cmd path with spaces (no outer cmd /c wrap)" {
    $lines = Build-EiaaxManagedProcessWrapperContent `
        -FilePath "C:\Program Files\nodejs\npm.cmd" `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory "D:\EMPLEADOS_IA_CONVERGENCIA\frontend" `
        -LogFile "D:\EMPLEADOS_IA_CONVERGENCIA\.eiaax\frontend.log" `
        -WrapperName "run_frontend"
    $startLine = Get-EiaaxWrapperStartLine -Lines $lines
    $expected = 'start "EIAAX_run_frontend" /B cmd /c call "C:\Program Files\nodejs\npm.cmd" "run" "dev" 1>>"D:\EMPLEADOS_IA_CONVERGENCIA\.eiaax\frontend.log" 2>>&1'
    if ($startLine -ne $expected) {
        throw ("unexpected start line:`n" + $startLine + "`nexpected:`n" + $expected)
    }
    if ($startLine -match 'cmd /c "') {
        throw "start line must not wrap entire command in quotes after cmd /c"
    }
}

Assert-Test "wrapper quotes executable path without spaces" {
    $lines = Build-EiaaxManagedProcessWrapperContent `
        -FilePath "C:\nodejs\npm.cmd" `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory "D:\worktree\frontend" `
        -LogFile "D:\worktree\.eiaax\frontend.log" `
        -WrapperName "run_frontend_plain"
    $startLine = Get-EiaaxWrapperStartLine -Lines $lines
    $expected = 'start "EIAAX_run_frontend_plain" /B cmd /c call "C:\nodejs\npm.cmd" "run" "dev" 1>>"D:\worktree\.eiaax\frontend.log" 2>>&1'
    if ($startLine -ne $expected) {
        throw ("unexpected start line: " + $startLine)
    }
}

Assert-Test "wrapper quotes arguments with spaces" {
    $lines = Build-EiaaxManagedProcessWrapperContent `
        -FilePath "C:\Program Files\nodejs\npm.cmd" `
        -ArgumentList @("run", "dev --strictPort") `
        -WorkingDirectory "D:\EMPLEADOS_IA_CONVERGENCIA\frontend" `
        -LogFile "D:\EMPLEADOS_IA_CONVERGENCIA\.eiaax\frontend.log" `
        -WrapperName "run_frontend_args"
    $startLine = Get-EiaaxWrapperStartLine -Lines $lines
    if ($startLine -notmatch '"dev --strictPort"') {
        throw ("argument with spaces not quoted: " + $startLine)
    }
}

Assert-Test "wrapper detaches resident service without blocking script" {
    $lines = Build-EiaaxManagedProcessWrapperContent `
        -FilePath "C:\Program Files\nodejs\npm.cmd" `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory "D:\EMPLEADOS_IA_CONVERGENCIA\frontend" `
        -LogFile "D:\EMPLEADOS_IA_CONVERGENCIA\.eiaax\frontend.log" `
        -WrapperName "run_frontend_detach"
    $startLine = Get-EiaaxWrapperStartLine -Lines $lines
    if ($startLine -notmatch ' /B cmd /c ') {
        throw "wrapper must use start /B for detached service"
    }
    if ($lines[-1] -ne "exit /b 0") {
        throw "wrapper must exit immediately after detached start"
    }
}

Assert-Test "startup failure message includes log tail when wrapper exits" {
    $tempLog = [System.IO.Path]::GetTempFileName()
    try {
        Set-Content -LiteralPath $tempLog -Value @("line1", "EIAAX_TOOL_RAN", "line3") -Encoding UTF8
        $message = New-EiaaxStartupFailureMessage -Summary "Frontend process did not open port 5180 in time." -LogFile $tempLog -WrapperPid 0
        if ($message -notmatch "EIAAX_TOOL_RAN") {
            throw "failure message must include recent log output"
        }
        if ($message -notmatch "Recent log output:") {
            throw "failure message must label log tail section"
        }
    }
    finally {
        Remove-Item -LiteralPath $tempLog -ErrorAction SilentlyContinue
    }
}

Assert-Test "managed process launches executable in path with spaces (Windows)" {
    if (-not $IsWindows) {
        Write-Host "  SKIP: Windows only"
        return
    }

    $toolRoot = Join-Path $env:TEMP "EIAAX Program Files Test"
    $stateDir = Join-Path $toolRoot ".eiaax-state"
    $logFile = Join-Path $stateDir "tool.log"
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    $toolCmd = Join-Path $toolRoot "tool.cmd"
    Set-Content -LiteralPath $toolCmd -Value "@echo off`r`necho EIAAX_TOOL_RAN`r`n" -Encoding ASCII

    $launcher = $null
    try {
        $launcher = Start-EiaaxManagedProcess `
            -FilePath $toolCmd `
            -ArgumentList @() `
            -WorkingDirectory $toolRoot `
            -LogFile $logFile `
            -StateDir $stateDir `
            -WrapperName "eiaax_tool_spaces"
        if ($null -eq $launcher) {
            throw "Start-EiaaxManagedProcess returned null launcher"
        }

        $deadline = [DateTime]::UtcNow.AddSeconds(5)
        while ([DateTime]::UtcNow -lt $deadline) {
            $proc = Get-Process -Id $launcher.Id -ErrorAction SilentlyContinue
            if ($null -eq $proc) {
                break
            }
            Start-Sleep -Milliseconds 100
        }

        $stillRunning = Get-Process -Id $launcher.Id -ErrorAction SilentlyContinue
        if ($null -ne $stillRunning) {
            throw ("wrapper launcher still running after detached start (PID " + $launcher.Id + ")")
        }

        $logDeadline = [DateTime]::UtcNow.AddSeconds(5)
        $logReady = $false
        while ([DateTime]::UtcNow -lt $logDeadline) {
            if ((Test-Path -LiteralPath $logFile) -and ((Get-Content -LiteralPath $logFile -Raw) -match "EIAAX_TOOL_RAN")) {
                $logReady = $true
                break
            }
            Start-Sleep -Milliseconds 100
        }
        if (-not $logReady) {
            throw ("tool log missing expected output: " + $logFile)
        }
    }
    finally {
        if ($null -ne $launcher) {
            Stop-Process -Id $launcher.Id -Force -ErrorAction SilentlyContinue
        }
        Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like ("*" + $toolRoot + "*") } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Remove-Item -LiteralPath $toolRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("SERVICE STARTUP TESTS: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "SERVICE STARTUP TESTS: PASS"
Write-Host "AUTOTESTS INTERACTIVE: 0"
exit 0
