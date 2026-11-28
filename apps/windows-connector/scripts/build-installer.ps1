# Build unsigned Inno Setup installer (Windows). Requires ISCC.exe.
# No fake code-signing. Mark artifact as UNSIGNED.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

& "$PSScriptRoot\publish-win-x64.ps1"

$iscc = $env:INNO_ISCC
if (-not $iscc) {
  $candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
  )
  foreach ($c in $candidates) { if (Test-Path $c) { $iscc = $c; break } }
}
if (-not $iscc -or -not (Test-Path $iscc)) {
  Write-Error "Inno Setup ISCC.exe not found. Install Inno Setup 6 or set INNO_ISCC. UNSIGNED MSI/EXE build skipped."
}

$iss = Join-Path $root "installer\DiagNovaConnector.iss"
$outDir = Join-Path $root "publish\installer"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

& $iscc "/DPublishDir=$($root)\publish\win-x64" $iss
Write-Host "UNSIGNED installer written under publish\installer (no SignTool)."
Get-ChildItem $outDir | Select-Object Name, Length
