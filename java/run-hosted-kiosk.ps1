$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$env:PARKING_SERVER_URL = 'https://parking-automation-system-ten.vercel.app'
$keyPath = Join-Path $PSScriptRoot '../.vercel/kiosk-key.txt'
if (Test-Path -LiteralPath $keyPath) {
    $env:KIOSK_API_KEY = (Get-Content -LiteralPath $keyPath -Raw).Trim()
}
if (!$env:KIOSK_API_KEY -or $env:KIOSK_API_KEY -eq 'local-kiosk-key') {
    throw 'Set KIOSK_API_KEY to the production kiosk key before launching. Do not commit the key.'
}
& ./run-kiosk.ps1
