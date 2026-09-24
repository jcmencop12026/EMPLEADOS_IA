param([string]$Cloudflared="cloudflared.exe",[string]$Root="")
if([string]::IsNullOrWhiteSpace($Root)){ $Root = Split-Path -Parent $PSScriptRoot }
$Root = $Root.Trim().Trim('"').TrimEnd('\\')
$ErrorActionPreference="Continue"
$runtime=Join-Path $Root "runtime"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$log=Join-Path $runtime "cloudflared-quick.log"
$urlFile=Join-Path $runtime "eiaax_public_url.txt"
$refreshFile=Join-Path $runtime "eiaax_tunnel_refresh.request"
$statusFile=Join-Path $runtime "eiaax_tunnel_status.txt"
$healthUrl="http://127.0.0.1:5180/"
$lockFile=Join-Path $runtime "eiaax_tunnel_monitor.lock"
if(Test-Path $lockFile){
  $existing=Get-Content $lockFile -ErrorAction SilentlyContinue | Select-Object -First 1
  if($existing -and (Get-Process -Id $existing -ErrorAction SilentlyContinue)){ Write-Host "[EIIAX] Monitor remoto ya activo." -ForegroundColor Yellow; exit 0 }
  Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
}
Set-Content -Path $lockFile -Value $PID -Encoding ascii
function Test-TunnelAlive([string]$u){
  if([string]::IsNullOrWhiteSpace($u)){return $false}
  try { $r=Invoke-WebRequest -Uri $u -Method Head -TimeoutSec 6 -UseBasicParsing -ErrorAction Stop; return ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) }
  catch { return $false }
}
try {
while($true){
  Remove-Item $refreshFile -Force -ErrorAction SilentlyContinue
  Set-Content -Path $statusFile -Value "RENOVANDO" -Encoding ascii
  Remove-Item $log -Force -ErrorAction SilentlyContinue
  Write-Host "[EIIAX] Iniciando canal HTTPS remoto..." -ForegroundColor Cyan
  $args=@("tunnel","--no-autoupdate","--url","http://127.0.0.1:5180","--logfile",$log,"--loglevel","info")
  try{$p=Start-Process -FilePath $Cloudflared -ArgumentList $args -PassThru -WindowStyle Hidden}
  catch{Write-Host "[EIIAX] No fue posible iniciar cloudflared: $($_.Exception.Message)" -ForegroundColor Red; Start-Sleep 5; continue}
  $published=$null
  for($i=0;$i -lt 45 -and -not $p.HasExited;$i++){
    Start-Sleep 1
    if(Test-Path $log){
      $m=Select-String -Path $log -Pattern 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' -AllMatches | Select-Object -Last 1
      if($m){$published=$m.Matches.Value | Select-Object -Last 1; Set-Content -Path $urlFile -Value $published -Encoding ascii; Set-Content -Path $statusFile -Value "ACTIVO" -Encoding ascii; Write-Host "[EIIAX] REMOTO LISTO: $published" -ForegroundColor Green; break}
    }
  }
  if(-not $published){Write-Host "[EIIAX] El canal no obtuvo URL; se reintentara automaticamente." -ForegroundColor Yellow}
  if(-not $p.HasExited){
    while(-not $p.HasExited){
      if(Test-Path $refreshFile){ Remove-Item $refreshFile -Force -ErrorAction SilentlyContinue; Set-Content -Path $statusFile -Value "RENOVANDO" -Encoding ascii; Write-Host "[EIIAX] Renovacion solicitada desde la plataforma..." -ForegroundColor Yellow; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; break }
      if($published -and -not (Test-TunnelAlive $published)){ Set-Content -Path $statusFile -Value "CAIDO" -Encoding ascii; Write-Host "[EIIAX] El canal publico dejo de responder. Recuperando..." -ForegroundColor Yellow; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; break }
      Start-Sleep 10
    }
    if(-not $p.HasExited){$p.WaitForExit()}
  }
  Set-Content -Path $statusFile -Value "CAIDO" -Encoding ascii
  Write-Host "[EIIAX] Canal remoto interrumpido. Renovando automaticamente..." -ForegroundColor Yellow
  Start-Sleep 2
}
} finally {
  Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
}
