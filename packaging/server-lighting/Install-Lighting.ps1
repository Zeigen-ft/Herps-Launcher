# AGPL-3.0-only. See bundled NOTICE.txt and LICENSE.txt.
# Local files only. No elevation, downloads, Java, server start, or settings edits.
[CmdletBinding()]
param([string]$WorldPath, [switch]$ConfirmedDisposableWorld)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$packName = '@PACK_NAME@'
$expectedHash = '@PACK_SHA256@'
$worldLock = $null
$staging = $null

function Assert-OrdinaryPath([string]$Path) {
    $node = Get-Item -LiteralPath $Path -Force
    while ($null -ne $node) {
        if (($node.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Links/junctions are not supported: $($node.FullName)"
        }
        if ($node -is [IO.DirectoryInfo]) { $node = $node.Parent }
        else { $node = $node.Directory }
    }
}

try {
    Write-Host 'Herps 26.3 SERVER lighting - experimental test installation'
    Write-Host 'This is not OptiFine. Use a disposable world; stop the host first.'
    $pack = Join-Path $PSScriptRoot $packName
    Assert-OrdinaryPath $pack
    if ((Get-FileHash -LiteralPath $pack -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
        throw 'Pack checksum failed. Download and extract a fresh complete bundle.'
    }
    if ([string]::IsNullOrWhiteSpace($WorldPath)) {
        $WorldPath = Read-Host 'Paste the full TEST WORLD folder path (the folder containing level.dat)'
    }
    $WorldPath = $WorldPath.Trim().Trim('"')
    $world = (Get-Item -LiteralPath $WorldPath -Force).FullName
    Assert-OrdinaryPath $world
    if (-not (Test-Path -LiteralPath (Join-Path $world 'level.dat') -PathType Leaf)) {
        throw 'Select an existing test WORLD folder containing level.dat, not the server or launcher folder.'
    }
    $lockPath = Join-Path $world 'session.lock'
    if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf)) {
        throw 'session.lock is missing. Start this disposable world once, then type stop and wait for the host to close.'
    }
    Assert-OrdinaryPath $lockPath
    # Match native SessionLock's byte-range lock and hold it for the entire copy
    # and installation. The server cannot start this world while we hold it.
    $worldLock = [IO.File]::Open($lockPath, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::ReadWrite)
    $worldLock.Lock(0, [long]::MaxValue)
    $datapacks = Join-Path $world 'datapacks'
    if (Test-Path -LiteralPath $datapacks) { Assert-OrdinaryPath $datapacks }
    $destination = Join-Path $datapacks $packName
    if ((Test-Path -LiteralPath $destination) -or (Test-Path -LiteralPath (Join-Path $datapacks 'herps-server-dynamic-lighting'))) {
        throw 'This test pack is already installed. No files were replaced.'
    }
    Write-Host "Selected world: $world"
    Write-Host 'A full, hash-verified world backup will be made before installation. Allow enough free disk space.'
    if (-not $ConfirmedDisposableWorld) {
        if ((Read-Host 'If the host is CLOSED and this is a DISPOSABLE test world, type INSTALL TEST PACK') -cne 'INSTALL TEST PACK') {
            throw 'Cancelled. No world files changed.'
        }
    }
    # Validate the entire tree before copying. Never traverse links or junctions.
    $queue = New-Object 'System.Collections.Generic.Queue[string]'
    $queue.Enqueue($world)
    $files = New-Object 'System.Collections.Generic.List[object]'
    while ($queue.Count -gt 0) {
        $directory = $queue.Dequeue()
        foreach ($entry in Get-ChildItem -LiteralPath $directory -Force) {
            if (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Backup refused a link/junction: $($entry.FullName)"
            }
            if ($entry.PSIsContainer) { $queue.Enqueue($entry.FullName) }
            elseif ($entry.FullName -ne $lockPath) { $files.Add($entry) }
        }
    }
    $backupRoot = Join-Path (Split-Path -Parent $world) '.herps-lighting-backups'
    if (Test-Path -LiteralPath $backupRoot) { Assert-OrdinaryPath $backupRoot }
    $backup = Join-Path $backupRoot ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N'))
    $backupWorld = Join-Path $backup 'world'
    [void][IO.Directory]::CreateDirectory($backupWorld)
    $manifest = @()
    foreach ($file in $files) {
        $relative = $file.FullName.Substring($world.Length).TrimStart([char]'\', [char]'/')
        $target = Join-Path $backupWorld $relative
        [void][IO.Directory]::CreateDirectory((Split-Path -Parent $target))
        $before = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        [IO.File]::Copy($file.FullName, $target, $false)
        $after = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        $copied = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
        if ($before -ne $after -or $before -ne $copied) { throw "Backup verification failed: $relative" }
        $manifest += [ordered]@{ path = $relative; sha256 = $copied.ToLowerInvariant(); bytes = $file.Length }
    }
    [ordered]@{ world = $world; skipped = @('session.lock (transient native lock)'); files = @($manifest) } |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $backup 'manifest.json') -Encoding UTF8
    Write-Host "VERIFIED BACKUP: $backup"
    [void][IO.Directory]::CreateDirectory($datapacks)
    Assert-OrdinaryPath $datapacks
    $staging = Join-Path $datapacks ('.herps-lighting-' + [guid]::NewGuid().ToString('N') + '.tmp')
    [IO.File]::Copy($pack, $staging, $false)
    if ((Get-FileHash -LiteralPath $staging -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
        throw 'Copied pack checksum failed.'
    }
    [IO.File]::Move($staging, $destination) # no overwrite
    $staging = $null
    Write-Host "INSTALLED: $destination"
    Write-Host 'Start the SAME test host. In its console type: function herps_dl:enable'
    Write-Host 'To stop lighting: function herps_dl:disable'
    Write-Host 'It starts disabled on the first load. Read README.txt for testing and cleanup.'
} catch {
    Write-Host "INSTALLATION STOPPED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Existing saves were not restored or overwritten. Any completed backup remains available.'
    exit 1
} finally {
    if ($null -ne $staging -and (Test-Path -LiteralPath $staging)) { Remove-Item -LiteralPath $staging }
    if ($null -ne $worldLock) { $worldLock.Dispose() }
}
