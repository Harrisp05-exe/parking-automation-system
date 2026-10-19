$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
javac --release 17 -encoding UTF-8 ParkingKiosk.java
if ($LASTEXITCODE -ne 0) { throw 'Compilation failed. Install JDK 17 or newer.' }
java ParkingKiosk
