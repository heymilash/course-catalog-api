param(
    [int]$Port = 8008,
    [string]$PgBin = 'C:\Program Files\PostgreSQL\17\bin',
    [switch]$CheckOnly,
    [switch]$Database
)

$ErrorActionPreference = 'Stop'
$labData = Join-Path $env:LOCALAPPDATA 'CodexLab7Postgres\data'
$labLog = Join-Path $env:LOCALAPPDATA 'CodexLab7Postgres\server.log'
$labCtl = Join-Path $PgBin 'pg_ctl.exe'
$labPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$labFastapi = Join-Path $PSScriptRoot '.venv\Scripts\fastapi.exe'

if (!(Test-Path -LiteralPath $labCtl) -or !(Test-Path -LiteralPath "$labData\PG_VERSION")) {
    throw 'The prepared local Lab 8 database was not found. Follow README.md: How to run.'
}
if (!(Test-Path -LiteralPath $labPython) -or !(Test-Path -LiteralPath "$PSScriptRoot\.env")) {
    throw 'Create .venv, install requirements.txt and configure .env first (see README.md).'
}
& $labCtl -D $labData status *> $null
if ($LASTEXITCODE -ne 0) {
    & $labCtl -D $labData -l $labLog -w start
    if ($LASTEXITCODE -ne 0) { throw 'Could not start the Lab 8 database. See server.log.' }
}

$labOldLocation = Get-Location
try {
    Set-Location -LiteralPath $PSScriptRoot
    if ($Database) {
        & $labPython open_db.py --pg-bin $PgBin
    } elseif ($CheckOnly) {
        & $labPython check_db.py
        if ($LASTEXITCODE -ne 0) { throw 'Database connection failed.' }
        & $labPython -m alembic check
    } else {
        Write-Host "Lab 8 Swagger: http://localhost:$Port/docs"
        Write-Host "Lab 8 GraphiQL: http://localhost:$Port/graphql"
        & $labFastapi dev main.py --host 127.0.0.1 --port $Port
    }
    if ($LASTEXITCODE -ne 0) { throw 'Lab 8 command exited with an error.' }
} finally {
    Set-Location -LiteralPath $labOldLocation
}
