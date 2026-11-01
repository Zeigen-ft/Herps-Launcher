#Requires -Version 7.0
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
if (-not $IsWindows) { throw 'This packaging step requires Windows.' }
$projectRoot = Split-Path -Parent $PSScriptRoot
$pin = Get-Content -Raw (Join-Path $projectRoot 'bedrock-upstream.lock.json') | ConvertFrom-Json

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}

# The original Windows MSI is verified before extraction. The MSI is never
# installed: WiX reads its cabinets without registration or installer actions.
$download = & python (Join-Path $projectRoot 'tools/fetch_bedrock_upstream.py')
if ($LASTEXITCODE -ne 0) { throw 'Pinned Bedrock source/package download failed.' }
$inputs = $download | ConvertFrom-Json
$tools = Join-Path $projectRoot '.cache/bedrock-tools'
New-Item -ItemType Directory -Force $tools | Out-Null
$wix = Join-Path $tools 'wix.exe'
if (-not (Test-Path $wix)) {
    Invoke-Checked 'dotnet' @('tool', 'install', '--tool-path', $tools, 'wix', '--version', $pin.wix_version)
}
$wixVersion = & $wix --version
if ($LASTEXITCODE -ne 0 -or -not $wixVersion.StartsWith($pin.wix_version)) { throw "Unexpected WiX tool version: $wixVersion" }
$image = Join-Path $projectRoot ('.cache/bedrock-image-' + [guid]::NewGuid().ToString('N'))
& (Join-Path $inputs.source 'packaging/windows/extract-msi.ps1') -Msi $inputs.msi -Out $image -Wix $wix
if ($LASTEXITCODE -ne 0) { throw 'Read-only MSI extraction failed.' }
$clients = @(Get-ChildItem -LiteralPath $image -Filter cinnabar.exe -File -Recurse)
if ($clients.Count -ne 1) { throw 'Expected exactly one native Bedrock client in the MSI.' }
$engine = $clients[0].Directory.FullName

Invoke-Checked 'rustup' @('toolchain', 'install', $pin.launcher_rust_toolchain, '--profile', 'minimal')
Invoke-Checked 'rustup' @('target', 'add', '--toolchain', $pin.launcher_rust_toolchain, 'x86_64-pc-windows-msvc')
$env:CARGO_TARGET_DIR = Join-Path $projectRoot '.cache/bedrock-launcher-target'
$env:RUSTFLAGS = '-C target-feature=+crt-static'
Invoke-Checked 'cargo' @("+$($pin.launcher_rust_toolchain)", 'build', '--locked', '--release',
    '--target', 'x86_64-pc-windows-msvc', '--manifest-path', (Join-Path $projectRoot 'bedrock/launcher/Cargo.toml'))
$launcher = Join-Path $env:CARGO_TARGET_DIR 'x86_64-pc-windows-msvc/release/Herspers-Bedrock.exe'
$output = Join-Path $projectRoot 'dist/bedrock-windows-x64'
if (Test-Path $output) { $output = Join-Path $output ('build-' + [guid]::NewGuid().ToString('N')) }
Invoke-Checked 'python' @((Join-Path $projectRoot 'tools/package_bedrock_windows.py'),
    '--engine', $engine, '--source', $inputs.source, '--launcher', $launcher, '--output', $output)
Write-Output "Bedrock Windows package: $output"
