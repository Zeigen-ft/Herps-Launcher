# Automated filesystem fixtures, NOT a real server or gameplay test.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$root = Join-Path ([IO.Path]::GetTempPath()) ('herps-lighting-test-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($root)
$script:checks = 0
function Check([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "FAIL: $Message" }
    $script:checks++
}
function Fixture([string]$Name) {
    $world = Join-Path $root $Name
    [void][IO.Directory]::CreateDirectory((Join-Path $world 'region'))
    [IO.File]::WriteAllText((Join-Path $world 'level.dat'), 'world sentinel')
    [IO.File]::WriteAllBytes((Join-Path $world 'session.lock'), [byte[]]@(38,3))
    [IO.File]::WriteAllText((Join-Path $world 'region/r.0.0.mca'), 'region sentinel')
    [IO.File]::WriteAllText((Join-Path $world 'options.txt'), 'keep me')
    return $world
}
function Install([string]$World) {
    $output = & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $installer -WorldPath $World -ConfirmedDisposableWorld 2>&1
    Write-Host ($output -join "`n")
    return $LASTEXITCODE
}
try {
    $bundle = Join-Path $root 'bundle'
    Expand-Archive -LiteralPath '.cache/server-lighting/Herps-Server-Dynamic-Lighting-0.1.0-Windows-Test.zip' -DestinationPath $bundle
    $installer = Join-Path $bundle 'Install-Lighting.ps1'
    $packName = 'Herps-Server-Dynamic-Lighting-0.1.0.zip'
    $world = Fixture 'stopped-disposable-world'
    $before = (Get-FileHash -LiteralPath (Join-Path $world 'level.dat')).Hash
    Check ((Install $world) -eq 0) 'stopped fixture installation succeeds'
    Check (Test-Path -LiteralPath (Join-Path $world "datapacks/$packName")) 'pack installed'
    Check ((Get-FileHash -LiteralPath (Join-Path $world 'level.dat')).Hash -eq $before) 'level.dat unchanged'
    Check ((Get-Content -LiteralPath (Join-Path $world 'options.txt') -Raw) -eq 'keep me') 'existing settings unchanged'
    $backups = @(Get-ChildItem -LiteralPath (Join-Path $root '.herps-lighting-backups'))
    Check ($backups.Count -eq 1) 'one backup'
    $backup = $backups[0].FullName
    $manifest = Get-Content -LiteralPath (Join-Path $backup 'manifest.json') -Raw | ConvertFrom-Json
    Check ($manifest.files.Count -eq 3) 'every persistent fixture file is backed up'
    foreach ($file in $manifest.files) {
        Check ((Get-FileHash -LiteralPath (Join-Path $backup "world/$($file.path)")).Hash.ToLowerInvariant() -eq $file.sha256) 'backup matches manifest'
    }
    Check (-not (Test-Path -LiteralPath (Join-Path $backup 'world/session.lock'))) 'transient lock excluded'
    # Independent extraction/copy to a NEW fixture; never restore over the source.
    $restore = Join-Path $root 'independent-restored-world'
    Copy-Item -LiteralPath (Join-Path $backup 'world') -Destination $restore -Recurse
    Check ((Get-FileHash -LiteralPath (Join-Path $restore 'level.dat')).Hash -eq $before) 'independent restore preserves bytes (no gameplay claim)'
    Check ((Install $world) -ne 0) 'duplicate refused'
    Check (@(Get-ChildItem -LiteralPath (Join-Path $root '.herps-lighting-backups')).Count -eq 1) 'duplicate makes no new backup'
    $active = Fixture 'active-lock'
    $lock = [IO.File]::Open((Join-Path $active 'session.lock'), 'Open', 'ReadWrite', 'ReadWrite')
    try {
        $lock.Lock(0, [long]::MaxValue)
        Check ((Install $active) -ne 0) 'active native-style byte-range lock refused'
        Check (-not (Test-Path -LiteralPath (Join-Path $active 'datapacks'))) 'locked world unchanged'
    } finally { $lock.Dispose() }
    $linked = Fixture 'junction-test'
    $outside = Join-Path $root 'outside'
    [void][IO.Directory]::CreateDirectory($outside)
    [IO.File]::WriteAllText((Join-Path $outside 'sentinel.txt'), 'outside untouched')
    $junction = Join-Path $linked 'linked-region'
    New-Item -ItemType Junction -Path $junction -Target $outside | Out-Null
    try {
        Check ((Install $linked) -ne 0) 'nested junction refused'
        Check (-not (Test-Path -LiteralPath (Join-Path $linked 'datapacks'))) 'junction world unchanged'
        Check ((Get-Content -LiteralPath (Join-Path $outside 'sentinel.txt') -Raw) -eq 'outside untouched') 'external files unchanged'
    } finally { [IO.Directory]::Delete($junction) }
    $bad = Fixture 'corrupt-pack'
    [IO.File]::AppendAllText((Join-Path $bundle $packName), 'corruption')
    Check ((Install $bad) -ne 0) 'corrupt pack refused'
    Check (-not (Test-Path -LiteralPath (Join-Path $bad 'datapacks'))) 'corruption makes no installation'
    Write-Host "PASS: $script:checks Windows filesystem/installer checks. Native server and multiplayer gameplay NOT RUN."
} finally {
    Remove-Item -LiteralPath $root -Recurse -Force
}
# Expected child-process refusals leave LASTEXITCODE=1. The fixture suite itself
# succeeds only after every assertion and cleanup above completed successfully.
exit 0
