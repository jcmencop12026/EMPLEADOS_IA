param([string]$Cloudflared="cloudflared.exe",[string]$Root="")
if([string]::IsNullOrWhiteSpace($Root)){ $Root = Split-Path -Parent $PSScriptRoot }
$Root = $Root.Trim().Trim('"').TrimEnd('\')
$ErrorActionPreference="Continue"
$runtime=Join-Path $Root "runtime"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$log=Join-Path $runtime "cloudflared-quick.log"
$urlFile=Join-Path $runtime "eiaax_public_url.txt"
$refreshFile=Join-Path $runtime "eiaax_tunnel_refresh.request"
$statusFile=Join-Path $runtime "eiaax_tunnel_status.txt"
$lockFile=Join-Path $runtime "eiaax_tunnel_monitor.lock"
$cooldownFile=Join-Path $runtime "eiaax_tunnel_cooldown_until.txt"
$healthUrl="http://127.0.0.1:5180/"
$normalBackoff=15
$rateLimitBackoff=300

function Set-TunnelState([string]$state){ Set-Content -LiteralPath $statusFile -Value $state -Encoding ascii }
function Test-TunnelAlive([string]$u){
  if([string]::IsNullOrWhiteSpace($u)){return $false}
  try { $r=Invoke-WebRequest -Uri $u -Method Head -TimeoutSec 6 -UseBasicParsing -ErrorAction Stop; return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) }
  catch { return $false }
}
function Get-PublishedUrl {
  if(-not (Test-Path -LiteralPath $urlFile)){ return $null }
  $value=(Get-Content -LiteralPath $urlFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
  if($value -match '^https://'){ return $value }
  return $null
}
function Test-RateLimited {
  if(-not (Test-Path -LiteralPath $log)){ return $false }
  return [bool](Select-String -LiteralPath $log -Pattern 'status 429|error code:\s*1015|\b1015\b.*rate|rate.?limit' -Quiet)
}
function Stop-OwnedCloudflared($process){
  if($process -and -not $process.HasExited){ Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue; $process.WaitForExit() }
}
function Stop-StaleQuickTunnels {
  Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*tunnel*--url*127.0.0.1:5180*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

if(Test-Path -LiteralPath $lockFile){
  $existing=[int](Get-Content -LiteralPath $lockFile -ErrorAction SilentlyContinue | Select-Object -First 1)
  $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$existing" -ErrorAction SilentlyContinue
  if($proc -and $proc.CommandLine -like "*MONITOR_TUNEL_EIIAX.ps1*"){ Write-Host "[EIIAX] Monitor remoto ya activo." -ForegroundColor Yellow; exit 0 }
  Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
}
try {
  $lockStream=[System.IO.File]::Open($lockFile,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::Read)
  $lockWriter=[System.IO.StreamWriter]::new($lockStream,[System.Text.Encoding]::ASCII,1024,$true)
  $lockWriter.WriteLine($PID); $lockWriter.Flush()
} catch [System.IO.IOException] {
  Write-Host "[EIIAX] Otro monitor obtuvo el lock." -ForegroundColor Yellow
  exit 0
}

try {
  $owned=$null
  while($true){
    $published=Get-PublishedUrl
    if($published -and (Test-TunnelAlive $published)){
      Set-TunnelState "ACTIVO"
      Remove-Item -LiteralPath $refreshFile -Force -ErrorAction SilentlyContinue
      Start-Sleep 10
      continue
    }
    if($published){ Remove-Item -LiteralPath $urlFile -Force -ErrorAction SilentlyContinue }
    $cooldownUntil=[datetime]::MinValue
    if(Test-Path -LiteralPath $cooldownFile){ [datetime]::TryParse((Get-Content -LiteralPath $cooldownFile -Raw),[ref]$cooldownUntil) | Out-Null }
    if($cooldownUntil.ToUniversalTime() -gt [datetime]::UtcNow){ Set-TunnelState "RATE_LIMITED"; Start-Sleep 10; continue }

    Set-TunnelState "RECUPERANDO"
    Remove-Item -LiteralPath $refreshFile -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $log -Force -ErrorAction SilentlyContinue
    Stop-StaleQuickTunnels
    Write-Host "[EIIAX] Iniciando canal HTTPS remoto..." -ForegroundColor Cyan
    $args=@("tunnel","--no-autoupdate","--url",$healthUrl,"--logfile",$log,"--loglevel","info")
    try { $owned=Start-Process -FilePath $Cloudflared -ArgumentList $args -PassThru -WindowStyle Hidden }
    catch { Set-TunnelState "NO_DISPONIBLE"; Write-Host "[EIIAX] cloudflared no inicio: $($_.Exception.Message)" -ForegroundColor Red; Start-Sleep $normalBackoff; continue }

    $candidate=$null
    for($i=0;$i -lt 45 -and -not $owned.HasExited;$i++){
      Start-Sleep 1
      if(Test-RateLimited){ break }
      if(Test-Path -LiteralPath $log){
        $m=Select-String -LiteralPath $log -Pattern 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' -AllMatches | Select-Object -Last 1
        if($m){ $candidate=$m.Matches.Value | Select-Object -Last 1; if(Test-TunnelAlive $candidate){ break } }
      }
    }
    if(Test-RateLimited){
      Stop-OwnedCloudflared $owned
      $until=[datetime]::UtcNow.AddSeconds($rateLimitBackoff)
      Set-Content -LiteralPath $cooldownFile -Value $until.ToString('o') -Encoding ascii
      Set-TunnelState "RATE_LIMITED"
      Write-Host "[EIIAX] Cloudflare 429/1015. Pausa controlada hasta $until UTC; EIIAX local sigue activo." -ForegroundColor Yellow
      continue
    }
    if($candidate -and (Test-TunnelAlive $candidate)){
      Remove-Item -LiteralPath $cooldownFile -Force -ErrorAction SilentlyContinue
      Set-Content -LiteralPath $urlFile -Value $candidate -Encoding ascii
      Set-TunnelState "ACTIVO"
      Write-Host "[EIIAX] REMOTO LISTO: $candidate" -ForegroundColor Green
      continue
    }
    Stop-OwnedCloudflared $owned
    Set-TunnelState "NO_DISPONIBLE"
    Write-Host "[EIIAX] Canal no disponible; nuevo intento controlado en $normalBackoff segundos." -ForegroundColor Yellow
    Start-Sleep $normalBackoff
  }
} finally {
  Stop-OwnedCloudflared $owned
  if($lockWriter){ $lockWriter.Dispose() }
  if($lockStream){ $lockStream.Dispose() }
  Remove-Item -LiteralPath $lockFile -Force -ErrorAction SilentlyContinue
}
