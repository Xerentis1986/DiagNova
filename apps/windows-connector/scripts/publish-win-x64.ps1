# DiagNova Connector – Self-contained Publish (Windows x64)
# Kein Code-Signing. Keine Fake-Signaturen.
# Installer: build-installer.ps1 (Inno Setup, UNSIGNED).
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

$verFile = Join-Path $out "INSTALLER_NOTE.txt"
@"
DiagNova Connector publish (unsigned).
Build installer on Windows: scripts\build-installer.ps1 (requires Inno Setup 6).
Code signing: NOT performed – BLK-CERT. Do not treat as production-signed.
OEM logos + wordmark without symbol icon must remain.
"@ | Set-Content -Path $verFile -Encoding UTF8

Write-Host "Fertig. UNSIGNED publish. Installer via build-installer.ps1."
Get-ChildItem $out | Select-Object Name, Length
