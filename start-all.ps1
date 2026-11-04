# Start MySQL (Docker) + Spring Boot (mysql profile) + Vite dev server
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-Port($port) {
  $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  return [bool]$c
}

Write-Output '[1/3] MySQL container'
$running = docker ps --filter name=campusflow-mysql --filter status=running --format '{{.Names}}'
if ($running -eq 'campusflow-mysql') {
  Write-Output '      already running'
} else {
  $exists = docker ps -a --filter name=campusflow-mysql --format '{{.Names}}'
  if ($exists -eq 'campusflow-mysql') {
    docker start campusflow-mysql | Out-Null
  } else {
    docker run -d --name campusflow-mysql --restart unless-stopped `
      -p 127.0.0.1:3307:3306 `
      -e MYSQL_ROOT_PASSWORD=__MYSQL_PASSWORD_REMOVED__ -e MYSQL_DATABASE=campusflow -e TZ=Asia/Shanghai `
      -v campusflow-mysql-data:/var/lib/mysql `
      mysql:8.4 --character-set-server=utf8mb4 --collation-server=utf8mb4_0900_ai_ci | Out-Null
  }
  Write-Output '      starting...'
  for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 2
    $ok = docker exec campusflow-mysql mysqladmin ping -uroot -p__MYSQL_PASSWORD_REMOVED__ 2>&1 | Select-String 'mysqld is alive'
    if ($ok) { break }
  }
  Write-Output '      ready'
}

Write-Output '[2/3] Backend (Spring Boot, mysql profile) :8080'
if (Test-Port 8080) {
  Write-Output '      already running'
} else {
  Push-Location (Join-Path $root 'backend')
  # 用 cmd /c start 起，脱离调用它的 PowerShell 进程树，脚本退出后服务仍活着
  Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', 'start "" /b java -jar target\campusflow-1.0.0.jar --spring.profiles.active=mysql > run.log 2>&1' -WindowStyle Hidden
  Pop-Location
  for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    try { $r = Invoke-WebRequest 'http://127.0.0.1:8080/api/health' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { break } } catch {}
  }
  Write-Output '      ready'
}

Write-Output '[3/3] Frontend (Vite) :5173'
if (Test-Port 5173) {
  Write-Output '      already running'
} else {
  Push-Location (Join-Path $root 'frontend')
  Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', 'npx vite --host 127.0.0.1 --port 5173 --strictPort > vite.log 2>&1' `
    -WindowStyle Hidden
  Pop-Location
  for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    try { $r = Invoke-WebRequest 'http://127.0.0.1:5173/' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { break } } catch {}
  }
  Write-Output '      ready'
}

Write-Output ''
Write-Output 'URLs'
Write-Output '  frontend  http://127.0.0.1:5173/'
Write-Output '  backend   http://127.0.0.1:8080/api/health'
Write-Output '  h2        http://127.0.0.1:8080/h2-console   (dev profile only)'
try { Write-Output ('  health    ' + (Invoke-WebRequest 'http://127.0.0.1:8080/api/health' -UseBasicParsing -TimeoutSec 5).Content) } catch { Write-Output '  health    DOWN' }
