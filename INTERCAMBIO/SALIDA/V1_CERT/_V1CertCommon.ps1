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

function Get-DockerContainerInspectObject {
    param(
        [string]$Docker,
        [string]$ContainerName
    )
    $raw = & $Docker inspect $ContainerName 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "docker inspect failed for ${ContainerName}: $raw"
    }
    $items = @($raw | ConvertFrom-Json)
    if ($items.Count -lt 1 -or -not $items[0]) {
        throw "docker inspect returned no data for ${ContainerName}"
    }
    return $items[0]
}

function Assert-V1CertContainerRunning {
    param(
        [string]$Docker,
        [string]$ContainerName
    )
    $info = Get-DockerContainerInspectObject -Docker $Docker -ContainerName $ContainerName
    if (-not $info.State.Running) {
        throw "Container not running: $ContainerName"
    }
}

function Get-V1CertContainerNetwork {
    param(
        [string]$Docker,
        [string]$ReferenceContainer = "empleados_ia_cert-backend-1"
    )
    $info = Get-DockerContainerInspectObject -Docker $Docker -ContainerName $ReferenceContainer
    $networks = $info.NetworkSettings.Networks
    if (-not $networks) {
        throw "Could not detect Docker network for $ReferenceContainer (no NetworkSettings.Networks)"
    }

    $names = @($networks.PSObject.Properties | ForEach-Object { $_.Name })
    if ($names.Count -eq 0) {
        throw "Could not detect Docker network for $ReferenceContainer (empty network list)"
    }

    $preferred = $names | Where-Object { $_ -like '*empleados_ia_cert*' } | Select-Object -First 1
    if ($preferred) {
        return $preferred
    }
    return $names[0]
}

function Get-V1CertContainerHealthLabel {
    param(
        [string]$Docker,
        [string]$ContainerName
    )
    try {
        $info = Get-DockerContainerInspectObject -Docker $Docker -ContainerName $ContainerName
        if (-not $info.State.Running) {
            return "NOT RUNNING"
        }
        $health = $info.State.Health
        if ($health -and $health.Status) {
            return [string]$health.Status
        }
        return "RUNNING (no healthcheck)"
    } catch {
        return "UNKNOWN"
    }
}

function Test-V1CertDockerImageExists {
    param(
        [string]$Docker,
        [string]$ImageRef
    )
    & $Docker image inspect $ImageRef 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Get-V1CertFrontendPort {
    param([string]$CertDir)
    $frontendPort = "5180"
    $envPath = Join-Path $CertDir ".env"
    if (Test-Path -LiteralPath $envPath) {
        $portLine = Get-Content -LiteralPath $envPath | Where-Object { $_ -match '^\s*FRONTEND_PORT\s*=' } | Select-Object -First 1
        if ($portLine -match '=\s*(\d+)') {
            $frontendPort = $Matches[1]
        }
    }
    return $frontendPort
}

function Wait-V1CertHttpReady {
    param(
        [string]$Url,
        [int]$MaxAttempts = 30,
        [int]$DelaySec = 2
    )
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                return $response
            }
        } catch {
            # retry
        }
        Start-Sleep -Seconds $DelaySec
    }
    throw "HTTP not ready after ${MaxAttempts} attempts: $Url"
}

function Test-V1CertLoginHotfixContent {
    param([string]$BaseUrl)
    $base = $BaseUrl.TrimEnd("/")
    $loginUrl = "$base/login"
    $page = Invoke-WebRequest -Uri $loginUrl -UseBasicParsing -TimeoutSec 15
    if ($page.StatusCode -ne 200) {
        throw "Login page HTTP status $($page.StatusCode)"
    }

    $bundle = $page.Content
    $matches = [regex]::Matches($bundle, 'src="(/assets/[^"]+\.js)"')
    foreach ($match in $matches) {
        $assetPath = $match.Groups[1].Value
        $asset = Invoke-WebRequest -Uri ($base + $assetPath) -UseBasicParsing -TimeoutSec 15
        $bundle += $asset.Content
    }

    $requiredMarkers = @(
        'password-toggle',
        'login-forgot',
        'Sistema empresarial de IA',
        'Usuario',
        'Contrase'
    )
    foreach ($marker in $requiredMarkers) {
        if ($bundle -notlike "*$marker*") {
            throw "Hotfix marker missing in frontend bundle: $marker"
        }
    }

    if ($bundle -notmatch 'Olvid') {
        throw 'Hotfix marker missing: forgot password link'
    }
    if ($bundle -notmatch 'Ocultar|Mostrar') {
        throw 'Hotfix marker missing: password visibility aria-label'
    }

    return $true
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
