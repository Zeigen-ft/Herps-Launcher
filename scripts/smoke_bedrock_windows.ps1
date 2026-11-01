#Requires -Version 7.0
param([Parameter(Mandatory = $true)][string]$PackagePath)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
if (-not $IsWindows) { throw 'Native Bedrock checks require Windows.' }
$package = (Resolve-Path $PackagePath).Path
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('Herspers Bedrock check ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $scratch | Out-Null
$saved = @{}
foreach ($name in @('LOCALAPPDATA', 'CINNABAR_USER_ROOT', 'CINNABAR_UPDATE_CHECK', 'CINNABAR_ACCEPT_MOJANG_EULA', 'CINNABAR_WINDOW_TITLE')) {
    $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}
$setup = $null
function Invoke-Probe {
    param([string]$Program, [string[]]$Arguments)
    $text = (& $Program @Arguments 2>&1 | Out-String)
    $status = $LASTEXITCODE
    if ($status -ne 0) { throw "$Program returned ${status}: $text" }
    return $text
}
try {
    $env:LOCALAPPDATA = Join-Path $scratch 'local app data'
    $env:CINNABAR_USER_ROOT = Join-Path $scratch 'profile'
    $env:CINNABAR_UPDATE_CHECK = '0'
    $env:CINNABAR_WINDOW_TITLE = 'Herspers Bedrock setup check'
    [Environment]::SetEnvironmentVariable('CINNABAR_ACCEPT_MOJANG_EULA', $null, 'Process')
    $launcher = Join-Path $package 'Herspers-Bedrock.exe'
    $version = Invoke-Probe $launcher @('--version')
    if ($version.Trim() -ne 'Herspers Bedrock 0.3.0') { throw 'Unexpected Bedrock product version.' }
    $verify = Invoke-Probe $launcher @('--verify-install') | ConvertFrom-Json
    if ($verify.bedrock_version -ne '1.26.60' -or $verify.wire_protocol -ne 2225 -or -not $verify.payload_hashes_verified) {
        throw 'Incorrect or incomplete Bedrock payload.'
    }
    $engine = Join-Path $package 'engine/cinnabar.exe'
    $identity = Invoke-Probe $engine @('--update-build-info') | ConvertFrom-Json
    if ($identity.version -ne '0.1.31') { throw 'The shipped engine does not identify as the pinned build.' }
    $help = Invoke-Probe $launcher @('--', '--help')
    if (-not $help.Contains('Bedrock Edition')) { throw 'Native engine help did not identify Bedrock.' }
    $coreHelp = Invoke-Probe (Join-Path $package 'engine/bedrock-core.exe') @('-h')
    if (-not $coreHelp.Contains('socket-dir')) { throw 'Native Go networking helper did not start.' }
    $kit = Join-Path $package 'engine/resources/prep-kit'
    $plan = Invoke-Probe (Join-Path $kit 'bin/assetc.exe') @('prepare', '--kit', $kit,
        '--workspace', (Join-Path $scratch 'prepare'), '--out', (Join-Path $scratch 'assets'), '--check')
    $plan | Set-Content (Join-Path $scratch 'resource-plan.txt')

    # Exercise the real first-run window without accepting the EULA or logging in.
    $setup = Start-Process -FilePath $engine -ArgumentList '--first-run-setup' -PassThru `
        -RedirectStandardOutput (Join-Path $PWD 'bedrock-setup.stdout.log') `
        -RedirectStandardError (Join-Path $PWD 'bedrock-setup.stderr.log')
    $consent = $null
    $deadline = [DateTime]::UtcNow.AddSeconds(35)
    while ([DateTime]::UtcNow -lt $deadline) {
        $reports = @(Get-ChildItem -Path $env:CINNABAR_USER_ROOT -Filter first-run-status.json -File -Recurse -ErrorAction SilentlyContinue)
        foreach ($report in $reports) {
            $state = Get-Content -Raw $report.FullName | ConvertFrom-Json
            if ($state.phase -eq 'awaiting_consent') { $consent = $state; break }
            if ($state.phase -eq 'failed') { throw "First-run setup failed: $($state.error)" }
        }
        $setup.Refresh()
        if ($setup.HasExited) {
            $details = (Get-Content 'bedrock-setup.stderr.log' -Tail 20 -ErrorAction SilentlyContinue) -join "`n"
            throw "First-run setup exited before its consent screen ($($setup.ExitCode)): $details"
        }
        if ($consent -and $setup.MainWindowHandle -ne [IntPtr]::Zero -and
            $setup.MainWindowTitle -eq $env:CINNABAR_WINDOW_TITLE) { break }
        Start-Sleep -Milliseconds 250
    }
    if (-not $consent -or $setup.MainWindowHandle -eq [IntPtr]::Zero -or
        $setup.MainWindowTitle -ne $env:CINNABAR_WINDOW_TITLE) {
        throw 'The native in-app resource setup did not open its consent window.'
    }
    Start-Sleep -Seconds 1
    $setup.Refresh()
    if ($setup.HasExited -or $setup.MainWindowHandle -eq [IntPtr]::Zero) {
        throw 'The native setup window closed unexpectedly.'
    }
    $result = @{
        product_version = $verify.product_version
        bedrock_version = $verify.bedrock_version
        wire_protocol = $verify.wire_protocol
        engine_version = $identity.version
        payload_hashes_verified = $true
        launcher_started_native_client = $true
        required_vc_runtime_dlls = $verify.required_vc_runtime_dlls
        prep_kit_plan_succeeded = $true
        native_setup_phase = $consent.phase
        native_setup_window_opened = $true
        eula_accepted_by_test = $false
        gameplay_tested = $false
        account_login_tested = $false
    }
    $result | ConvertTo-Json | Tee-Object -FilePath 'bedrock-startup-results.json'
    Write-Output 'PASS: native Rust Bedrock client, Go helper, resource planner and in-app consent screen.'
} finally {
    if ($null -ne $setup -and -not $setup.HasExited) { Stop-Process -Id $setup.Id -Force }
    foreach ($name in $saved.Keys) { [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process') }
}
exit 0
