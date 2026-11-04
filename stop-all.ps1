# Stop backend and frontend (MySQL container is left running on purpose)
$ErrorActionPreference = 'Continue'

foreach ($port in 8080, 5173) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if ($conns) {
    $conns | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Write-Output ("stopped port " + $port)
  } else {
    Write-Output ("port " + $port + " not listening")
  }
}
Write-Output 'MySQL container left running. Use: docker stop campusflow-mysql'
