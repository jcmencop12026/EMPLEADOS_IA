# Common helpers for V1 CERT Docker scripts (ASCII only).
# Dot-source from other scripts: . "$PSScriptRoot\_V1CertCommon.ps1"

function Get-V1CertDockerExe {
    $candidates = @(
        "C:\Program Files\Docker\Docker\resources\bin\docker.exe",
        "docker.exe",
        "docker"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -eq "docker.exe" -or $candidate -eq "docker") {
            $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
            if ($cmd) { return $cmd.Source }
        } elseif (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    throw "Docker executable not found."
}

function Resolve-V1CertHotfixRoot {
    param([string]$HotfixRoot)
    if ($HotfixRoot) {
        return (Resolve-Path -LiteralPath $HotfixRoot).Path
    }
    # INTERCAMBIO/SALIDA/V1_CERT -> repo root (3 levels up)
    $auto = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..")
    return $auto.Path
}

function Assert-V1CertContainerRunning {
    param(
        [string]$Docker,
        [string]$ContainerName
    )
    $state = & $Docker inspect -f "{{.State.Running}}" $ContainerName 2>$null
    if ($state -ne "true") {
        throw "Container not running: $ContainerName"
    }
}

function Get-V1CertContainerNetwork {
    param(
        [string]$Docker,
        [string]$ReferenceContainer = "empleados_ia_cert-backend-1"
    )
    $network = & $Docker inspect -f "{{range `$k,`$v := .NetworkSettings.Networks}}{{$k}}{{end}}" $ReferenceContainer 2>$null
    if (-not $network) {
        throw "Could not detect Docker network for $ReferenceContainer"
    }
    return $network.Trim()
}

function Invoke-V1CertCopiedPython {
    param(
        [string]$Docker,
        [string]$ContainerName,
        [string]$LocalPythonFile,
        [string[]]$PythonArgs = @(),
        [switch]$Interactive
    )
    if (-not (Test-Path -LiteralPath $LocalPythonFile)) {
        throw "Python file not found: $LocalPythonFile"
    }
    $remoteName = "v1cert_" + [Guid]::NewGuid().ToString("N") + ".py"
    $remotePath = "/tmp/$remoteName"
    & $Docker cp $LocalPythonFile "${ContainerName}:${remotePath}"
    if ($LASTEXITCODE -ne 0) {
        throw "docker cp failed for $LocalPythonFile"
    }
    try {
        if ($Interactive) {
            if ($PythonArgs.Count -gt 0) {
                & $Docker exec -it $ContainerName python $remotePath @PythonArgs
            } else {
                & $Docker exec -it $ContainerName python $remotePath
            }
        } else {
            if ($PythonArgs.Count -gt 0) {
                & $Docker exec -i $ContainerName python $remotePath @PythonArgs
            } else {
                & $Docker exec -i $ContainerName python $remotePath
            }
        }
        return $LASTEXITCODE
    } finally {
        & $Docker exec -i $ContainerName rm -f $remotePath 2>$null | Out-Null
    }
}
