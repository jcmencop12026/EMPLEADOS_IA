#Requires -Version 5.1
<#
.SYNOPSIS
    Validate all EIAAX Windows PowerShell scripts with the real parser.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($scriptRoot)) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$files = Get-ChildItem -LiteralPath $scriptRoot -Filter "*.ps1" |
    Where-Object { $_.Name -ne "validate_ps_parse.ps1" } |
    Sort-Object Name

$failed = $false

foreach ($file in $files) {
    $errors = $null
    $tokens = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
    $errorCount = 0
    if ($null -ne $errors) {
        $errorCount = @($errors).Count
    }

    Write-Host ("FILE: " + $file.Name)
    Write-Host ("PARSE ERRORS: " + $errorCount)
    if ($errorCount -gt 0) {
        $failed = $true
        foreach ($err in $errors) {
            $line = $err.Extent.StartLineNumber
            $column = $err.Extent.StartColumnNumber
            $message = $err.ErrorId + ": " + $err.Message
            Write-Host ("  line " + $line + " col " + $column + " - " + $message)
        }
    }
    Write-Host ("RESULT: " + ($(if ($errorCount -eq 0) { "PASS" } else { "FAIL" })))
    Write-Host ""
}

if ($failed) {
    Write-Host "PARSER VALIDATION: FAIL"
    exit 1
}

Write-Host "PARSER VALIDATION: PASS"
exit 0
