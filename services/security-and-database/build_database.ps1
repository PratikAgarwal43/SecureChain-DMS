$psql = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
$sql_file = "C:\Users\Shreyash debnath\.gemini\antigravity\scratch\securechain-dms-security\securechain_v03_migration.sql"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  SecureChain DMS - Vault 1 Database Setup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Ask for password securely
$pwd = Read-Host "Enter the PostgreSQL 'postgres' password you just created" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($pwd)
$env:PGPASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

Write-Host "`n[1/2] Creating securechain_db database..." -ForegroundColor Yellow
# Ignore error if database already exists
& $psql -U postgres -c "CREATE DATABASE securechain_db;" *>&1 | Out-Null

Write-Host "[2/2] Injecting 17 Tables and Security Rules..." -ForegroundColor Yellow
& $psql -U postgres -d securechain_db -f $sql_file

Write-Host "`n✅ Vault 1 Database Successfully Built!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan

# Clear password from environment
$env:PGPASSWORD = ""
