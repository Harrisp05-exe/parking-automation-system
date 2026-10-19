$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Could not create virtual environment.' }
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
if (!(Test-Path .env)) { Copy-Item .env.example .env }
& ./.venv/Scripts/python.exe manage.py migrate
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
& ./.venv/Scripts/python.exe manage.py seed_spots --count 24
if ($LASTEXITCODE -ne 0) { throw 'Spot initialization failed.' }
Write-Host 'Ready. Start the server with: .\.venv\Scripts\python.exe manage.py runserver'
