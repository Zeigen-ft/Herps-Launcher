#Requires -Version 7.0
param([Parameter(Mandatory = $true)][string]$PackagePath)
$ErrorActionPreference = 'Stop'
# The missing-resources case below deliberately expects a nonzero child status.
$PSNativeCommandUseErrorActionPreference = $false
if (-not $IsWindows) { throw 'Native executable checks require Windows.' }
$package = (Resolve-Path $PackagePath).Path
$scratch = Join-Path ([System.IO.Path]::GetTempPath()) ('Herspers Windows smoke ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $scratch | Out-Null
Write-Output "Isolated startup test folder: $scratch"
$saved = @{}
foreach ($name in @('LOCALAPPDATA', 'APPDATA', 'HORIZON_HOME', 'HORIZON_LAUNCHER_HOME', 'HORIZON_LAUNCHER_NO_SELF_UPDATE', 'HORIZON_NO_AUDIO')) {
    $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

function Invoke-Probe {
    param([string]$Program, [string[]]$Arguments, [int]$Expected = 0)
    $output = (& $Program @Arguments 2>&1 | Out-String)
    $status = $LASTEXITCODE
    if ($status -ne $Expected) { throw "$Program returned $status, expected ${Expected}: $output" }
    return $output
}

try {
    $env:LOCALAPPDATA = Join-Path $scratch 'local'
    $env:APPDATA = Join-Path $scratch 'roaming'
    $env:HORIZON_HOME = Join-Path $scratch 'horizon'
    $env:HORIZON_LAUNCHER_HOME = Join-Path $scratch 'launcher'
    $env:HORIZON_LAUNCHER_NO_SELF_UPDATE = '1'
    $env:HORIZON_NO_AUDIO = '1'
    foreach ($path in @($env:LOCALAPPDATA, $env:APPDATA, $env:HORIZON_HOME, $env:HORIZON_LAUNCHER_HOME)) {
        New-Item -ItemType Directory -Force $path | Out-Null
    }
    $launcher = Join-Path $package 'Herspers-Minecraft.exe'
    $bin = Join-Path $package 'bin'
    $help = Invoke-Probe $launcher @('--help')
    if (-not $help.Contains('--setup')) { throw 'Packaged launcher help is incomplete.' }
    $version = Invoke-Probe $launcher @('--version')
    if ($version.Trim() -ne 'Herspers Minecraft 0.2.2') { throw "Unexpected launcher version: $version" }
    if (-not $help.Contains('--host-tailscale') -or -not $help.Contains('--join-tailscale')) { throw 'Private multiplayer help is missing.' }
    foreach ($name in @('Host-Tailscale.cmd', 'Join-Tailscale.cmd', 'HOSTING-TAILSCALE.txt')) {
        if (-not (Test-Path (Join-Path $package $name))) { throw "Missing private multiplayer helper: $name" }
    }
    $clientHelp = Invoke-Probe (Join-Path $bin 'horizon-client.exe') @('--help')
    if (-not $clientHelp.Contains('--resources')) { throw 'Client help is incomplete.' }
    $api = Invoke-Probe (Join-Path $bin 'horizon-client.exe') @('--launch-api') | ConvertFrom-Json
    if ($api.minecraft -ne '26.3' -or -not $api.launch_api) { throw 'Unexpected native client Launch API.' }
    $ctl = Invoke-Probe (Join-Path $bin 'horizon-ctl.exe') @('--help')
    if (-not $ctl.Contains('horizon-ctl')) { throw 'Control tool did not print its help.' }
    $prepare = Invoke-Probe (Join-Path $bin 'horizon-prepare.exe') @('--help')
    if (-not $prepare.Contains('--server-jar')) { throw 'Preparer help is incomplete.' }
    $prepareVersion = Invoke-Probe (Join-Path $bin 'horizon-prepare.exe') @('--version')
    if ($prepareVersion.Trim() -ne 'horizon-prepare 0.7.6') { throw "Unexpected preparer version: $prepareVersion" }
    $missing = Invoke-Probe -Program $launcher -Arguments @() -Expected 1
    if (-not $missing.Contains('--setup')) { throw 'Missing-resource startup gave no setup instructions.' }
    $support = Join-Path $env:LOCALAPPDATA 'Herspers Minecraft'
    if (-not (Test-Path (Join-Path $support 'logs/resources-check.log'))) { throw 'Resource check log was not written.' }
    if (Test-Path (Join-Path $support 'game')) { throw 'The game was started without resources.' }
    # Validate the native helper's output with the real engine's properties
    # parser, without accepting an EULA, opening a port, or needing game assets.
    $probe = Join-Path $scratch 'private-config-probe.exe'
    $fixture = Join-Path (Split-Path -Parent $PSScriptRoot) 'tests/fixtures/private_server_probe.rs'
    Invoke-Probe 'rustc' @('+1.95.0', '--edition=2021', $fixture, '-o', $probe) | Out-Null
    $server = Join-Path $scratch 'private-server'
    Invoke-Probe $probe @($server) | Out-Null
    Invoke-Probe (Join-Path $bin 'horizon-client.exe') @('--game-dir', $server, '--home', $server, '--dedicated', '--initSettings') | Out-Null
    $properties = Get-Content -Raw (Join-Path $server 'server.properties')
    if ($properties -notmatch '(?m)^online-mode=false\r?$' -or $properties -notmatch '(?m)^server-ip=100\.64\.1\.2\r?$') {
        throw 'The real server did not preserve private authentication and Tailscale-only binding.'
    }
    if ((Get-Content -Raw (Join-Path $server 'eula.txt')) -match '(?m)^eula=true\r?$') { throw 'The probe unexpectedly accepted an EULA.' }
    Invoke-Probe $probe @($server) | Out-Null
    if ((Get-Content -Raw (Join-Path $server 'server.properties')) -ne $properties) {
        throw 'The private helper rewrote an already-correct native server configuration.'
    }
    $report = @{
        native_executables_started = $true
        launcher_version = $version.Trim()
        launch_api = $api.launch_api
        minecraft = $api.minecraft
        missing_resources_expected_exit = 1
        tailscale_config_real_engine_parsed = $true
        game_rendering_tested = $false
        gameplay_tested = $false
    }
    $report | ConvertTo-Json | Set-Content (Join-Path $scratch 'startup-report.json')
    $report | ConvertTo-Json
    Write-Output 'PASS: native Windows startup and missing-resource handling. Rendering/gameplay not exercised.'
} finally {
    foreach ($name in $saved.Keys) {
        [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process')
    }
}
# The deliberate missing-resource probe exited 1. All assertions above passed;
# report the test suite's result rather than that expected child exit status.
exit 0
