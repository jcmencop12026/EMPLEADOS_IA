#Requires -Version 5.1
<#
.SYNOPSIS
    Regression tests for parser aggregate consistency and UTF-8 BOM policy.
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

Assert-Test "validate_ps_parse reports FAILED FILES when aggregate fails" {
    $content = Get-Content -LiteralPath (Join-Path $PSScriptRoot "validate_ps_parse.ps1") -Raw
    foreach ($needle in @("FAILED FILES:", "PARSER VALIDATION: FAIL", "Get-EiaaxCollectionCount", "parseFailures")) {
        if ($content -notmatch [regex]::Escape($needle)) {
            throw ("Missing parser aggregate token: " + $needle)
        }
    }
}

Assert-Test "all tracked scripts have UTF-8 BOM for Windows PowerShell 5.1" {
    $files = Get-EiaaxParserValidationFiles -ScriptsDir $PSScriptRoot
    $missing = New-Object System.Collections.Generic.List[string]
    foreach ($file in $files) {
        if (-not (Test-EiaaxScriptUtf8Bom -Path $file.FullName)) {
            [void]$missing.Add($file.Name)
        }
    }
    if ($missing.Count -gt 0) {
        throw ("Missing UTF-8 BOM: " + ($missing -join ", "))
    }
}

Assert-Test "Invoke-EiaaxPowerShellFile returns explicit exit code" {
    $content = Get-Content -LiteralPath $common -Raw
    if ($content -notmatch 'Start-Process -FilePath \$shell') {
        throw "Invoke-EiaaxPowerShellFile must use Start-Process exit code"
    }
    if ($content -match 'Invoke-EiaaxPowerShellFile -FilePath \$validator[\s\S]*if \(\$LASTEXITCODE') {
        throw "Parser validation must not rely on stale LASTEXITCODE"
    }
}

Assert-Test "parser aggregate exit code matches visible failures" {
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("eiaax-parser-" + [Guid]::NewGuid().ToString("N"))
    $scriptsDir = Join-Path $tempRoot "scripts\windows"
    New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "validate_ps_parse.ps1") -Destination (Join-Path $scriptsDir "validate_ps_parse.ps1")
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1") -Destination (Join-Path $scriptsDir "EiaaxDemo.Common.ps1")
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot "EiaaxDemo.TestHelpers.ps1") -Destination (Join-Path $scriptsDir "EiaaxDemo.TestHelpers.ps1")

    $goodScript = Join-Path $scriptsDir "good.ps1"
    Set-Content -LiteralPath $goodScript -Value "# good`nWrite-Host ok" -Encoding utf8BOM

    $badScript = Join-Path $scriptsDir "bad.ps1"
    Set-Content -LiteralPath $badScript -Value "function {" -Encoding utf8BOM

    $stdoutFile = Join-Path $tempRoot "parser.out.txt"
    $stderrFile = Join-Path $tempRoot "parser.err.txt"
    $shell = (Get-Command pwsh).Source
    $validator = Join-Path $scriptsDir "validate_ps_parse.ps1"
    $process = Start-Process -FilePath $shell -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $validator
    ) -Wait -PassThru -NoNewWindow -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile

    try {
        if ($process.ExitCode -eq 0) {
            throw "expected parser fail"
        }
        if ($process.ExitCode -ne 1) {
            throw ("unexpected exit " + $process.ExitCode)
        }
        $output = ""
        if (Test-Path -LiteralPath $stdoutFile) {
            $output += Get-Content -LiteralPath $stdoutFile -Raw
        }
        if (Test-Path -LiteralPath $stderrFile) {
            $output += Get-Content -LiteralPath $stderrFile -Raw
        }
        if ($output -notmatch "FAILED FILES:") {
            throw "Expected FAILED FILES summary in parser output"
        }
        if ($output -notmatch "bad\.ps1") {
            throw "Expected bad.ps1 in FAILED FILES summary"
        }
    }
    finally {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
if ($failed -gt 0) {
    Write-Host ("PARSER AGGREGATE TESTS: FAIL (" + $failed + ")")
    exit 1
}

Write-Host "PARSER AGGREGATE TESTS: PASS"
Write-Host "AUTOTESTS INTERACTIVE: 0"
exit 0
