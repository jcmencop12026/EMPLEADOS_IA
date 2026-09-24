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

function Get-EiaaxWrapperServiceLine {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Lines
    )

    foreach ($line in $Lines) {
        if ($line -match '>>\s+".*" 2>>&1$') {
            return $line
        }
    }

    throw "wrapper service command line not found"
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

Assert-Test "managed process uses proven direct batch execution (no start /B cmd /c)" {
    $content = Get-Content -LiteralPath $common -Raw
    if ($content -match 'start "EIAAX_') {
        throw "managed process must not use fragile start /B cmd /c wrapper"
    }
    if ($content -notmatch 'echo \[EIAAX\] EXIT_CODE=%ERRORLEVEL%>>') {
        throw "managed process must record exit code in log"
    }
    if ($content -notmatch '>> "') {
        throw "managed process must redirect output directly in batch"
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

Assert-Test "BACKEND wrapper: EXE direct execution (84d5330 semantics)" {
    $lines = Build-EiaaxManagedProcessWrapperContent `
        -FilePath "D:\EMPLEADOS_IA_CONVERGENCIA\.venv\Scripts\python.exe" `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory "D:\EMPLEADOS_IA_CONVERGENCIA\backend" `
        -LogFile "D:\EMPLEADOS_IA_CONVERGENCIA\logs\demo\backend.log" `
        -WrapperName "run_backend" `
        -Environment @{ DATABASE_URL = "sqlite:///D:/EMPLEADOS_IA_CONVERGENCIA/data/demo.db" }
    $serviceLine = Get-EiaaxWrapperServiceLine -Lines $lines
    $expected = '"D:\EMPLEADOS_IA_CONVERGENCIA\.venv\Scripts\python.exe" "-m" "uvicorn" "app.main:app" "--host" "127.0.0.1" "--port" "8000" >> "D:\EMPLEADOS_IA_CONVERGENCIA\logs\demo\backend.log" 2>>&1'
    if ($serviceLine -ne $expected) {
        throw ("unexpected backend service line:`n" + $serviceLine + "`nexpected:`n" + $expected)
    }
    if ($serviceLine -match 'cmd /c|start "') {
        throw "backend wrapper must not use cmd /c or start"
    }
    if ($lines -notcontains 'set DATABASE_URL=sqlite:///D:/EMPLEADOS_IA_CONVERGENCIA/data/demo.db') {
        throw "backend wrapper must set runtime environment"
    }
}

Assert-Test "FRONTEND wrapper: npm.cmd with spaces uses call (no outer cmd /c wrap)" {
    $lines = Build-EiaaxManagedProcessWrapperContent `
        -FilePath "C:\Program Files\nodejs\npm.cmd" `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory "D:\EMPLEADOS_IA_CONVERGENCIA\frontend" `
        -LogFile "D:\EMPLEADOS_IA_CONVERGENCIA\logs\demo\frontend.log" `
        -WrapperName "run_frontend"
    $serviceLine = Get-EiaaxWrapperServiceLine -Lines $lines
    $expected = 'call "C:\Program Files\nodejs\npm.cmd" "run" "dev" >> "D:\EMPLEADOS_IA_CONVERGENCIA\logs\demo\frontend.log" 2>>&1'
    if ($serviceLine -ne $expected) {
        throw ("unexpected frontend service line:`n" + $serviceLine + "`nexpected:`n" + $expected)
    }
    if ($serviceLine -match 'cmd /c "') {
        throw "frontend wrapper must not wrap entire command in quotes after cmd /c"
    }
}

Assert-Test "FRONTEND wrapper: npm.cmd path without spaces" {
    $lines = Build-EiaaxManagedProcessWrapperContent `
        -FilePath "C:\nodejs\npm.cmd" `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory "D:\worktree\frontend" `
        -LogFile "D:\worktree\logs\demo\frontend.log" `
        -WrapperName "run_frontend_plain"
    $serviceLine = Get-EiaaxWrapperServiceLine -Lines $lines
    $expected = 'call "C:\nodejs\npm.cmd" "run" "dev" >> "D:\worktree\logs\demo\frontend.log" 2>>&1'
    if ($serviceLine -ne $expected) {
        throw ("unexpected service line: " + $serviceLine)
    }
}

Assert-Test "FRONTEND wrapper: arguments with spaces" {
    $lines = Build-EiaaxManagedProcessWrapperContent `
        -FilePath "C:\Program Files\nodejs\npm.cmd" `
        -ArgumentList @("run", "dev --strictPort") `
        -WorkingDirectory "D:\EMPLEADOS_IA_CONVERGENCIA\frontend" `
        -LogFile "D:\EMPLEADOS_IA_CONVERGENCIA\logs\demo\frontend.log" `
        -WrapperName "run_frontend_args"
    $serviceLine = Get-EiaaxWrapperServiceLine -Lines $lines
    if ($serviceLine -notmatch '"dev --strictPort"') {
        throw ("argument with spaces not quoted: " + $serviceLine)
    }
}

Assert-Test "wrapper keeps resident service in-process (no premature exit /b 0)" {
    $lines = Build-EiaaxManagedProcessWrapperContent `
        -FilePath "C:\Program Files\nodejs\npm.cmd" `
        -ArgumentList @("run", "dev") `
        -WorkingDirectory "D:\EMPLEADOS_IA_CONVERGENCIA\frontend" `
        -LogFile "D:\EMPLEADOS_IA_CONVERGENCIA\logs\demo\frontend.log" `
        -WrapperName "run_frontend_detach"
    if ($lines -contains "exit /b 0") {
        throw "wrapper must not exit before resident service completes"
    }
    if ($lines[-1] -notmatch 'EXIT_CODE=%ERRORLEVEL%') {
        throw "wrapper must end with exit code logging"
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

Assert-Test "Windows: backend-equivalent wrapper executes EXE and stays resident" {
    if (-not $IsWindows) {
        Write-Host "  SKIP: Windows only (remote validates structure only)"
        return
    }

    $toolRoot = Join-Path $env:TEMP "EIAAX Backend Test"
    $stateDir = Join-Path $toolRoot ".eiaax-state"
    $logFile = Join-Path $stateDir "backend.log"
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null

    $ping = Join-Path $env:WINDIR "System32\ping.exe"
    if (-not (Test-Path -LiteralPath $ping)) {
        throw "ping.exe not found for backend wrapper execution test"
    }

    $launcher = $null
    try {
        $launcher = Start-EiaaxManagedProcess `
            -FilePath $ping `
            -ArgumentList @("127.0.0.1", "-n", "120") `
            -WorkingDirectory $toolRoot `
            -LogFile $logFile `
            -StateDir $stateDir `
            -WrapperName "run_backend_ping" `
            -Environment @{}
        if ($null -eq $launcher) {
            throw "Start-EiaaxManagedProcess returned null launcher"
        }

        Start-Sleep -Seconds 2
        $stillRunning = Get-Process -Id $launcher.Id -ErrorAction SilentlyContinue
        if ($null -eq $stillRunning) {
            $tail = if (Test-Path -LiteralPath $logFile) { Get-Content -LiteralPath $logFile -Raw } else { "(no log)" }
            throw ("backend wrapper exited prematurely. Log:`n" + $tail)
        }

        $logDeadline = [DateTime]::UtcNow.AddSeconds(5)
        $logReady = $false
        while ([DateTime]::UtcNow -lt $logDeadline) {
            if ((Test-Path -LiteralPath $logFile) -and ((Get-Content -LiteralPath $logFile -Raw) -match "Ping")) {
                $logReady = $true
                break
            }
            Start-Sleep -Milliseconds 200
        }
        if (-not $logReady) {
            throw ("backend wrapper log missing ping output: " + $logFile)
        }
    }
    finally {
        if ($null -ne $launcher) {
            Stop-Process -Id $launcher.Id -Force -ErrorAction SilentlyContinue
        }
        Get-CimInstance Win32_Process -Filter "Name='ping.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like ("*" + $toolRoot + "*") } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Remove-Item -LiteralPath $toolRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Assert-Test "Windows: frontend-equivalent wrapper executes npm.cmd in path with spaces" {
    if (-not $IsWindows) {
        Write-Host "  SKIP: Windows only (remote validates structure only)"
        return
    }

    $toolRoot = Join-Path $env:TEMP "EIAAX Program Files Test"
    $stateDir = Join-Path $toolRoot ".eiaax-state"
    $logFile = Join-Path $stateDir "frontend.log"
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    $toolCmd = Join-Path $toolRoot "npm.cmd"
    Set-Content -LiteralPath $toolCmd -Value "@echo off`r`necho EIAAX_NPM_RAN`r`nping 127.0.0.1 -n 120 >nul`r`n" -Encoding ASCII

    $launcher = $null
    try {
        $launcher = Start-EiaaxManagedProcess `
            -FilePath $toolCmd `
            -ArgumentList @("run", "dev") `
            -WorkingDirectory $toolRoot `
            -LogFile $logFile `
            -StateDir $stateDir `
            -WrapperName "run_frontend_npm" `
            -Environment @{}
        if ($null -eq $launcher) {
            throw "Start-EiaaxManagedProcess returned null launcher"
        }

        Start-Sleep -Seconds 2
        $stillRunning = Get-Process -Id $launcher.Id -ErrorAction SilentlyContinue
        if ($null -eq $stillRunning) {
            $tail = if (Test-Path -LiteralPath $logFile) { Get-Content -LiteralPath $logFile -Raw } else { "(no log)" }
            throw ("frontend wrapper exited prematurely. Log:`n" + $tail)
        }

        $logDeadline = [DateTime]::UtcNow.AddSeconds(5)
        $logReady = $false
        while ([DateTime]::UtcNow -lt $logDeadline) {
            if ((Test-Path -LiteralPath $logFile) -and ((Get-Content -LiteralPath $logFile -Raw) -match "EIAAX_NPM_RAN")) {
                $logReady = $true
                break
            }
            Start-Sleep -Milliseconds 200
        }
        if (-not $logReady) {
            throw ("frontend wrapper log missing npm output: " + $logFile)
        }
    }
    finally {
        if ($null -ne $launcher) {
            Stop-Process -Id $launcher.Id -Force -ErrorAction SilentlyContinue
        }
        Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like ("*" + $toolRoot + "*") } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        Get-CimInstance Win32_Process -Filter "Name='ping.exe'" -ErrorAction SilentlyContinue |
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
