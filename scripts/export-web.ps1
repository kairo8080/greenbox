[CmdletBinding()]
param(
    [string]$GodotExecutable = $env:GODOT_BIN
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepositoryPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$GamePath = [System.IO.Path]::GetFullPath((Join-Path $RepositoryPath 'game'))
$PublicPath = [System.IO.Path]::GetFullPath((Join-Path $RepositoryPath 'public'))
$ExportPath = [System.IO.Path]::GetFullPath((Join-Path $PublicPath 'index.html'))

if ([string]::IsNullOrWhiteSpace($GodotExecutable)) {
    $GodotCommand = Get-Command 'godot' -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $GodotCommand) {
        throw 'Godot was not found. Set GODOT_BIN or pass -GodotExecutable with the path to Godot 4.7.2.'
    }
    $GodotPath = $GodotCommand.Source
} elseif (Test-Path -LiteralPath $GodotExecutable -PathType Leaf) {
    $GodotPath = (Resolve-Path -LiteralPath $GodotExecutable).Path
} else {
    $GodotCommand = Get-Command $GodotExecutable -CommandType Application -ErrorAction SilentlyContinue
    if ($null -eq $GodotCommand) {
        throw "Godot executable was not found: $GodotExecutable"
    }
    $GodotPath = $GodotCommand.Source
}
$GodotPath = [System.IO.Path]::GetFullPath($GodotPath)

if (-not (Test-Path -LiteralPath (Join-Path $GamePath 'project.godot') -PathType Leaf)) {
    throw "Godot project was not found at $GamePath"
}

$VersionText = (& $GodotPath --version 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "Godot version check failed with exit code $LASTEXITCODE." }
if ($VersionText -notmatch '^4\.7\.2[.\s-]') {
    throw "This project exports with Godot 4.7.2 and matching templates. Detected: $VersionText"
}
Write-Host "Using Godot $VersionText"
New-Item -ItemType Directory -Path $PublicPath -Force | Out-Null

Write-Host 'Importing game resources...'
& $GodotPath --headless --editor --path $GamePath --import
if ($LASTEXITCODE -ne 0) { throw "Godot import failed with exit code $LASTEXITCODE." }

Write-Host 'Exporting Web...'
& $GodotPath --headless --path $GamePath --export-release 'Web' $ExportPath
if ($LASTEXITCODE -ne 0) {
    throw "Godot Web export failed with exit code $LASTEXITCODE. Install matching 4.7.2 Web export templates (web_nothreads_release.zip)."
}

foreach ($Filename in @('index.html', 'index.js', 'index.wasm', 'index.pck')) {
    $OutputFile = Get-Item -LiteralPath (Join-Path $PublicPath $Filename) -ErrorAction Stop
    if ($OutputFile.PSIsContainer -or $OutputFile.Length -eq 0) {
        throw "Web export is missing a nonempty file: $Filename"
    }
}

$NodeCommand = Get-Command 'node' -CommandType Application -ErrorAction SilentlyContinue
if ($null -ne $NodeCommand) {
    & $NodeCommand.Source (Join-Path $PSScriptRoot 'verify-web.mjs')
    if ($LASTEXITCODE -ne 0) { throw "Web verification failed with exit code $LASTEXITCODE." }
}
Write-Host "Web export complete: $ExportPath"
Write-Host 'Run npm run build, test the browser build, then commit the updated public/ files with your source changes.'
