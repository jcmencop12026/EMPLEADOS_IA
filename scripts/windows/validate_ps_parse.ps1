#Requires -Version 5.1
<#
.SYNOPSIS
    Validate all EIAAX Windows PowerShell scripts with the real parser.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$common = Join-Path $PSScriptRoot "EiaaxDemo.Common.ps1"
. $common

$scriptRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptRoot)) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}

function Get-EiaaxScriptParseTargetPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (Test-EiaaxScriptUtf8Bom -Path $Path) {
        return $Path
    }

    $text = [System.IO.File]::ReadAllText($Path, [System.Text.UTF8Encoding]::new($false))
    $tempPath = [System.IO.Path]::Combine(
        [System.IO.Path]::GetTempPath(),
        ("eiaax-parse-" + [Guid]::NewGuid().ToString("N") + "-" + [System.IO.Path]::GetFileName($Path))
    )
    [System.IO.File]::WriteAllText($tempPath, $text, [System.Text.UTF8Encoding]::new($true))
    return $tempPath
}

$files = Get-EiaaxParserValidationFiles -ScriptsDir $scriptRoot
$parseFailures = New-Object System.Collections.Generic.List[object]
$tempParseFiles = New-Object System.Collections.Generic.List[string]

try {
    foreach ($file in $files) {
        $parseTarget = Get-EiaaxScriptParseTargetPath -Path $file.FullName
        if ($parseTarget -ne $file.FullName) {
            [void]$tempParseFiles.Add($parseTarget)
        }

        $errors = $null
        $tokens = $null
        [void][System.Management.Automation.Language.Parser]::ParseFile($parseTarget, [ref]$tokens, [ref]$errors)
        $errorCount = Get-EiaaxCollectionCount $errors
        $encodingNote = ""
        if (-not (Test-EiaaxScriptUtf8Bom -Path $file.FullName)) {
            $encodingNote = " (UTF-8 BOM missing; parsed via temp copy)"
        }

        Write-Host ("FILE: " + $file.Name + $encodingNote)
        Write-Host ("PARSE ERRORS: " + $errorCount)
        if ($errorCount -gt 0) {
            foreach ($err in @($errors)) {
                $line = $err.Extent.StartLineNumber
                $column = $err.Extent.StartColumnNumber
                $message = $err.ErrorId + ": " + $err.Message
                Write-Host ("  line " + $line + " col " + $column + " - " + $message)
            }
            [void]$parseFailures.Add([ordered]@{
                File       = $file.Name
                ErrorCount = $errorCount
            })
        }
        Write-Host ("RESULT: " + ($(if ($errorCount -eq 0) { "PASS" } else { "FAIL" })))
        Write-Host ""
    }
}
finally {
    foreach ($tempPath in $tempParseFiles) {
        Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
    }
}

if ((Get-EiaaxCollectionCount $parseFailures) -gt 0) {
    Write-Host "PARSER VALIDATION: FAIL"
    Write-Host "FAILED FILES:"
    foreach ($failure in $parseFailures) {
        Write-Host ("  - " + $failure.File + " (" + $failure.ErrorCount + " parse error(s))")
    }
    exit 1
}

Write-Host "PARSER VALIDATION: PASS"
Write-Host ("FILES CHECKED: " + (Get-EiaaxCollectionCount $files))
exit 0
