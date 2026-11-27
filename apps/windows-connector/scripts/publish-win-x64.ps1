# DiagNova Connector – Self-contained Publish (Windows x64)
# Kein Code-Signing in diesem Skript. Keine Fake-Signaturen.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$out = Join-Path $root "publish\win-x64"
Write-Host "Publishing to $out"
dotnet publish DiagNova.Connector\DiagNova.Connector.csproj `
  -c Release -r win-x64 --self-contained true `
  -p:PublishSingleFile=true `
  -o $out

Write-Host "Probe tool..."
dotnet publish DiagNova.CdpProbe\DiagNova.CdpProbe.csproj `
  -c Release -r win-x64 --self-contained true `
  -p:PublishSingleFile=true `
  -o (Join-Path $root "publish\cdp-probe")

Write-Host "Fertig. Installer/MSI: manuell oder WiX später. Signing: BLK-CERT."
Get-ChildItem $out | Select-Object Name, Length
