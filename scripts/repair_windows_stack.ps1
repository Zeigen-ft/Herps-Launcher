#Requires -Version 5.1
<#
Repair the main-thread stack reserve in an existing unsigned Herspers Java package.
Only the PE header's SizeOfStackReserve changes. The original executable is kept
beside it; prepared resources, settings and saves are not touched.
#>
param([string]$PackagePath = '.')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-OrdinaryPath {
    param([string]$Path)
    $item = Get-Item -LiteralPath $Path -Force
    while ($null -ne $item) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Links/reparse points are unsupported: $($item.FullName)"
        }
        if ($item -is [IO.FileInfo]) { $item = $item.Directory }
        else { $item = $item.Parent }
    }
}

function Write-NewFile {
    param([string]$Path, [byte[]]$Bytes)
    $stream = $null
    $complete = $false
    try {
        $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        $stream.Write($Bytes, 0, $Bytes.Length)
        $stream.Flush($true)
        $complete = $true
    } finally {
        if ($null -ne $stream) {
            $stream.Dispose()
            if (-not $complete) { [IO.File]::Delete($Path) }
        }
    }
}

try {
    $package = Get-Item -LiteralPath $PackagePath -Force
    if (-not $package.PSIsContainer) { throw 'PackagePath must be the extracted Herspers-Minecraft folder.' }
    $path = Join-Path $package.FullName 'bin/horizon-client.exe'
    Assert-OrdinaryPath $path
    $item = Get-Item -LiteralPath $path -Force
    if ($item.PSIsContainer -or $item.Length -gt 512MB) { throw 'Expected an ordinary game executable under 512 MiB.' }
    [byte[]]$original = [IO.File]::ReadAllBytes($path)
    if ($original.Length -lt 64 -or $original[0] -ne 0x4d -or $original[1] -ne 0x5a) {
        throw 'Not a Windows executable (missing MZ header).'
    }
    [long]$pe = [BitConverter]::ToUInt32($original, 60)
    if ($pe -lt 64 -or $pe + 24 -gt $original.Length -or [BitConverter]::ToUInt32($original, $pe) -ne 0x4550) {
        throw 'Invalid PE header.'
    }
    $flags = [BitConverter]::ToUInt16($original, $pe + 22)
    if ([BitConverter]::ToUInt16($original, $pe + 4) -ne 0x8664 -or ($flags -band 2) -eq 0 -or ($flags -band 0x2000) -ne 0) {
        throw 'Expected an x64 executable, not a DLL.'
    }
    [long]$optional = $pe + 24
    $size = [BitConverter]::ToUInt16($original, $pe + 20)
    if ($size -lt 112 -or $optional + $size -gt $original.Length -or [BitConverter]::ToUInt16($original, $optional) -ne 0x20b) {
        throw 'Invalid or truncated PE32+ optional header.'
    }
    $directories = [BitConverter]::ToUInt32($original, $optional + 108)
    if ($directories -gt [Math]::Floor(($size - 112) / 8)) { throw 'Invalid PE directory count.' }
    if ($directories -gt 4 -and [BitConverter]::ToUInt64($original, $optional + 112 + 4 * 8) -ne 0) {
        throw 'This executable is signed; changing it would invalidate its signature. Use a rebuilt package.'
    }
    [UInt64]$reserve = [BitConverter]::ToUInt64($original, $optional + 72)
    [UInt64]$commit = [BitConverter]::ToUInt64($original, $optional + 80)
    if ($reserve -eq 0 -or $commit -eq 0 -or $commit -gt $reserve) { throw 'Invalid stack reserve/commit values.' }
    [UInt64]$required = 16MB
    if ($reserve -ge $required) {
        Write-Output "No change needed: the game already reserves $reserve bytes for its main stack."
        exit 0
    }
    $metadataPath = Join-Path $package.FullName 'build-metadata.json'
    Assert-OrdinaryPath $metadataPath
    $metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
    $expected = $metadata.binaries.'horizon-client.exe'.sha256
    if ($expected -notmatch '^[0-9a-fA-F]{64}$') { throw 'Missing valid game checksum in build-metadata.json.' }
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $actual = [BitConverter]::ToString($sha.ComputeHash($original)).Replace('-', '') }
    finally { $sha.Dispose() }
    if ($actual -ine $expected) { throw 'Game checksum does not match build-metadata.json; re-extract the original package before repair.' }
    $backup = "$path.before-stack-fix.bak"
    if (Test-Path -LiteralPath $backup) { throw "Backup already exists; it will not be overwritten: $backup" }
    [byte[]]$patched = $original.Clone()
    [BitConverter]::GetBytes($required).CopyTo($patched, $optional + 72)
    $temporary = "$path.stack-fix-$([Guid]::NewGuid().ToString('N')).tmp"
    try {
        Write-NewFile $temporary $patched
        Write-NewFile $backup $original
        # Replace only after both complete files have been flushed. Failure to
        # replace (for example, because the game is running) leaves the original.
        [IO.File]::Replace($temporary, $path, [NullString]::Value)
    } finally {
        if (Test-Path -LiteralPath $temporary) { [IO.File]::Delete($temporary) }
    }
    Write-Output "Repaired main stack reserve: $reserve -> $required bytes (16 MiB)."
    Write-Output "Original executable saved as: $backup"
    Write-Output 'Open Play.cmd to test startup. Saves and resources were preserved.'
    Write-Output 'The repaired executable differs from its original build-metadata.json checksum.'
} catch {
    [Console]::Error.WriteLine("Stack repair stopped: $($_.Exception.Message)")
    exit 1
}
