# One-shot acceptance: backend tests + contract test + frontend suites + layout audit
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Output '=== 1/5 backend unit tests ==='
Push-Location (Join-Path $root 'backend'); mvn -q test 2>&1 | Select-Object -Last 4; Pop-Location

Write-Output '=== 2/5 backend health ==='
try { (Invoke-WebRequest 'http://127.0.0.1:8080/api/health' -UseBasicParsing -TimeoutSec 6).Content }
catch { Write-Output 'backend not running: cd backend; java -jar target/campusflow-1.0.0.jar' }

Write-Output '=== 3/5 backend contract (29 asserts) ==='
Push-Location (Join-Path $root 'frontend'); node scripts/api.mjs 2>&1 | Select-Object -Last 3; Pop-Location

Write-Output '=== 4/5 frontend asserts ==='
Push-Location (Join-Path $root 'frontend')
node scripts/interact.mjs 2>&1 | Select-String -Pattern 'PASS|FAIL' | Measure-Object | Select-Object -ExpandProperty Count
node scripts/interact.mjs 2>&1 | Select-String -Pattern 'FAIL'
node scripts/keyboard.mjs 2>&1 | Select-String -Pattern 'FAIL'
node scripts/calibrate.mjs 2>&1 | Select-String -Pattern 'FAIL'
Pop-Location

Write-Output '=== 5/5 layout audit ==='
Push-Location (Join-Path $root 'frontend')
node scripts/audit.mjs http://127.0.0.1:5173 1440 dark 2>&1 | Select-String -Pattern 'clipped'
Pop-Location
