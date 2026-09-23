param([string]$Cloudflared="cloudflared.exe",[string]$Root=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference="Continue"
$runtime=Join-Path $Root "runtime"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$log=Join-Path $runtime "cloudflared-quick.log"
$urlFile=Join-Path $runtime "eiaax_public_url.txt"
while($true){
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
      if($m){$published=$m.Matches.Value | Select-Object -Last 1; Set-Content -Path $urlFile -Value $published -Encoding ascii; Write-Host "[EIIAX] REMOTO LISTO: $published" -ForegroundColor Green; break}
    }
  }
  if(-not $published){Write-Host "[EIIAX] El canal no obtuvo URL; se reintentara automaticamente." -ForegroundColor Yellow}
  if(-not $p.HasExited){$p.WaitForExit()}
  Write-Host "[EIIAX] Canal remoto interrumpido. Renovando automaticamente..." -ForegroundColor Yellow
  Start-Sleep 2
}
