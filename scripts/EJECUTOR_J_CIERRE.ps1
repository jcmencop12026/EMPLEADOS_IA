$ErrorActionPreference = "Stop"
$ROOT = "D:\EMPLEADOS_IA"
$LOGDIR = Join-Path $ROOT "INTERCAMBIO"
$STAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$OUT = Join-Path $LOGDIR ("CIERRE_EJECUTOR_J_" + $STAMP + ".txt")
$SUMMARY = Join-Path $LOGDIR ("CIERRE_EJECUTOR_J_" + $STAMP + "_RESUMEN.txt")
New-Item -ItemType Directory -Force -Path $LOGDIR | Out-Null
Set-Location $ROOT

function Write-Log([string]$text) {
    $text | Out-File -FilePath $OUT -Append -Encoding utf8
    Write-Host $text
}

function Run-Native([string]$name,[string]$exe,[string[]]$arguments,[string]$cwd=$ROOT) {
    Write-Log ""
    Write-Log ("=== " + $name + " ===")
    Push-Location $cwd
    try {
        # PowerShell 5.1: invocación nativa directa. Evita ProcessStartInfo/ArgumentList.
        # Redirigir a archivo temporal conserva stdout/stderr y el exit code real.
        $tmp = Join-Path $env:TEMP ("ejecutor_j_" + [guid]::NewGuid().ToString("N") + ".log")
        if ($exe -like "*.cmd" -or $exe -like "*.bat") {
            & cmd.exe /d /s /c "`"$exe`" $($arguments -join ' ')" *> $tmp
        } else {
            & $exe @arguments *> $tmp
        }
        $code = $LASTEXITCODE
        if (Test-Path $tmp) {
            Get-Content $tmp | Tee-Object -FilePath $OUT -Append | Write-Host
            Remove-Item $tmp -Force -ErrorAction SilentlyContinue
        }
    } catch {
        $_ | Out-File -FilePath $OUT -Append -Encoding utf8
        Write-Host $_
        $code = 1
    } finally {
        Pop-Location
    }
    Write-Log ("EXIT=" + $code)
    return $code
}

"=== EJECUTOR-J CIERRE EIIAX ===" | Out-File $OUT -Encoding utf8
(Get-Date).ToString("s") | Out-File $OUT -Append -Encoding utf8
$results = [ordered]@{}
$py = Join-Path $ROOT ".venv\Scripts\python.exe"
$git = "git.exe"
$cmd = "cmd.exe"

$results["GIT_PRE"] = Run-Native "GIT PRE" $git @("status","--short")
$results["CONTROL_MIGRACIONES"] = Run-Native "CONTROL MIGRACIONES" $py @("-m","pytest","tests\test_migration_control.py","tests\test_convergencia_c1.py","tests\test_scim_1380.py","-q")
$results["EIIAX_FOCAL"] = Run-Native "EIIAX DEMO + REUNION + PRESENTACION + FLUJO" $py @("-m","pytest","backend\tests\test_demo_reunion_contract.py","tests\test_demo_comercial_ficticia.py","tests\test_demo_reunion_copilot.py","tests\test_reunion_demo_room.py","tests\test_presentacion_real_v1.py","tests\test_flujo_comercial_v1_1730.py","tests\test_vistas_comercial_api_contract.py","-q")
$results["REGRESION_FALLOS_PREVIOS"] = Run-Native "REGRESION FALLOS PREVIOS" $py @("-m","pytest","tests\test_agent_factory_e2e.py::test_deny_blocks_orchestrator_execution","tests\test_bloque_1230_centro_control.py","tests\test_bloque_1250c_centro_control_integrado.py","tests\test_convergencia_cierre_v1.py::test_centro_control_consola_maestra","tests\test_convergencia_maestro_v1.py","tests\test_correccion_focal_post6e_p1.py::test_p1_cc_01_centro_control_resumen_structure","tests\test_macrointegral_v1_correcciones.py::test_login_usa_brand_corporativo_no_hero","tests\test_macrointegral_v1_correcciones.py::test_espacio_externo_no_crear_entidad_si_existe","tests\test_orchestrator_e2e.py::test_unexpected_execution_error_publishes_system_error","tests\test_publicable_cliente_v1.py::test_permiso_insuficiente_rechaza_publicable","-q")
$results["AUDITOR_CONVERGENCIA"] = Run-Native "AUDITOR CONVERGENCIA" $py @("-m","pytest","tests\test_convergencia_c2.py","tests\test_convergencia_final_1250.py","tests\test_convergencia_final_fase2.py","tests\test_cierre_comercial_valor_pre_fase2.py","-q")
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npm) { $npm = "npm.cmd" }
$results["FRONTEND_BUILD"] = Run-Native "FRONTEND BUILD" $npm @("run","build") (Join-Path $ROOT "frontend")
$results["GIT_POST"] = Run-Native "GIT POST / NO-DANO" $git @("status","--short")

$pass = ($results.Values | Where-Object { $_ -ne 0 }).Count -eq 0
"=== RESUMEN EJECUTOR-J ===" | Out-File $SUMMARY -Encoding utf8
foreach ($k in $results.Keys) { ($k + "=" + $results[$k]) | Out-File $SUMMARY -Append -Encoding utf8 }
("RESULTADO=" + $(if ($pass){"PASS"}else{"FAIL"})) | Out-File $SUMMARY -Append -Encoding utf8
("LOG=" + $OUT) | Out-File $SUMMARY -Append -Encoding utf8
Write-Host ""
Write-Host "==============================================="
Write-Host ("EJECUTOR-J TERMINADO: " + $(if ($pass){"PASS"}else{"FAIL"}))
Write-Host ("LOG: " + $OUT)
Write-Host ("RESUMEN: " + $SUMMARY)
Write-Host "==============================================="
if (-not $pass) { exit 1 }
