#Requires -Version 7.0
# Build and package the pinned engine for Windows 10/11 x64.
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Program failed with exit code $LASTEXITCODE"
    }
}

if (-not $IsWindows) {
    throw 'This build requires Windows, Visual Studio C++ Build Tools and the Windows SDK.'
}
$projectRoot = Split-Path -Parent $PSScriptRoot
$lock = Get-Content -Raw (Join-Path $projectRoot 'upstream.lock.json') | ConvertFrom-Json
$toolchain = $lock.rust_toolchain
$target = 'x86_64-pc-windows-msvc'
$env:HORIZON_VERSION = $lock.horizon_version
$env:RUSTFLAGS = '-C target-feature=+crt-static'
$env:CARGO_TARGET_DIR = Join-Path $projectRoot '.cache/target'
if (-not $env:CARGO_BUILD_JOBS) { $env:CARGO_BUILD_JOBS = '3' }

Invoke-Checked 'rustup' @('toolchain', 'install', $toolchain, '--profile', 'minimal')
Invoke-Checked 'rustup' @('target', 'add', '--toolchain', $toolchain, $target)
$sourceRoot = & python (Join-Path $projectRoot 'tools/fetch_upstream.py')
if ($LASTEXITCODE -ne 0 -or -not $sourceRoot) { throw 'Pinned source fetch failed.' }
$sourceRoot = ([string]$sourceRoot).Trim()

Invoke-Checked 'cargo' @("+$toolchain", 'build', '--locked', '--release',
    '--manifest-path', (Join-Path $sourceRoot 'Cargo.toml'), '--target', $target,
    '-p', 'horizon-client', '-p', 'horizon-prepare',
    '--bin', 'horizon-client', '--bin', 'horizon-ctl', '--bin', 'horizon-prepare',
    '--features', 'horizon-client/mods')

$launcherDir = Join-Path $projectRoot '.cache/windows-launcher'
New-Item -ItemType Directory -Force $launcherDir | Out-Null
$launcher = Join-Path $launcherDir 'Herspers-Minecraft.exe'
Invoke-Checked 'rustc' @("+$toolchain", '--edition=2021', '--target', $target,
    '-C', 'target-feature=+crt-static', '-O',
    (Join-Path $projectRoot 'packaging/launcher_windows.rs'), '-o', $launcher)

$packageOutput = Join-Path $projectRoot 'dist/windows-x86_64'
if (Test-Path $packageOutput) {
    $packageOutput = Join-Path $packageOutput ('build-' + [guid]::NewGuid().ToString('N'))
}
Invoke-Checked 'python' @((Join-Path $projectRoot 'tools/package_windows.py'),
    '--source', $sourceRoot, '--binaries', (Join-Path $env:CARGO_TARGET_DIR "$target/release"),
    '--launcher', $launcher, '--output', $packageOutput)
Write-Output "Windows package output: $packageOutput"
