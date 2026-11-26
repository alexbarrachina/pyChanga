# Copyright (C) 2026 Alex Barrachina
# SPDX-License-Identifier: GPL-3.0-only
#
# Installs out\installer\*-setup.exe silently for the current user, runs the
# packaged-app smoke test against the installed copy, then uninstalls it.
# Meant for CI or a clean test account: it refuses to run where pyChangaIDE
# is already installed, because both installs would share one uninstall entry.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$installer = Get-ChildItem (Join-Path $root 'out\installer') -Filter '*-setup.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $installer) { throw 'No installer in out\installer. Run node scripts\make_windows_installer.mjs first.' }

$uninstallKeys = @('HKCU:', 'HKLM:') | ForEach-Object {
  "$_\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D6DF84E2-66F7-4666-97F3-92B739D06A90}_is1"
}
foreach ($key in $uninstallKeys) {
  if (Test-Path $key) { throw "pyChangaIDE is already installed ($key). Run this test on a clean machine." }
}
$results = Join-Path $root 'test-results'
New-Item -ItemType Directory -Force $results | Out-Null
$log = Join-Path $results 'installer.log'

Write-Host "Installing $($installer.Name)"
$install = Start-Process $installer.FullName -Wait -PassThru -ArgumentList @(
  '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CURRENTUSER', '/TASKS=desktopicon', "/LOG=`"$log`"")
if ($install.ExitCode -ne 0) { throw "The installer exited with code $($install.ExitCode); see $log" }
$key = $uninstallKeys[0]
if (-not (Test-Path $key)) { throw "The installer did not register an uninstall entry at $key" }
$dir = (Get-ItemProperty $key).InstallLocation.TrimEnd('\')
$exe = Join-Path $dir 'pyChangaIDE.exe'
$uninstaller = Join-Path $dir 'unins000.exe'
$shortcuts = @([Environment]::GetFolderPath('Programs'), [Environment]::GetFolderPath('Desktop')) |
  ForEach-Object { Join-Path $_ 'pyChangaIDE.lnk' }
Write-Host "Installed to $dir"

$failure = $null
try {
  $expected = @($exe, $uninstaller) + $shortcuts + @('python\python.exe', 'packages\pyChanga', 'packages\pyo', 'native', 'runtime-manifest.json' |
    ForEach-Object { Join-Path $dir "resources\runtime\$_" }) + @(Join-Path $dir 'resources\examples')
  foreach ($path in $expected) {
    if (-not (Test-Path $path)) { throw "The installed copy is missing $path" }
  }
  Push-Location $root
  try {
    node scripts/smoke_desktop.mjs --app $exe
    if ($LASTEXITCODE -ne 0) { throw "The smoke test of the installed app failed with code $LASTEXITCODE" }
  } finally { Pop-Location }
} catch { $failure = $_ }

Write-Host 'Uninstalling'
if (Test-Path $uninstaller) {
  Start-Process $uninstaller -Wait -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' | Out-Null
  # The uninstaller finishes from a temporary copy of itself, so wait for its work.
  $deadline = (Get-Date).AddMinutes(3)
  while (((Test-Path $exe) -or (Test-Path $key)) -and (Get-Date) -lt $deadline) { Start-Sleep -Seconds 2 }
}
if ($failure) { throw $failure }
foreach ($path in @($exe, $key) + $shortcuts) {
  if (Test-Path $path) { throw "The uninstaller left $path" }
}
if (Test-Path $dir) {
  Write-Warning "The uninstaller left files in $dir`n$((Get-ChildItem $dir -Recurse -Force | Select-Object -First 20 -ExpandProperty FullName) -join "`n")"
}
Write-Host 'Installer test passed: installed, ran the packaged smoke test, uninstalled'
