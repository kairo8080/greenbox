param(
    [string]$UnityEditor = 'C:\Program Files\Unity\Hub\Editor\6000.2.6f1\Editor\Unity.exe',
    [string]$CaBundle = $env:NODE_EXTRA_CA_CERTS
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $UnityEditor)) { throw "Unity Editor missing: $UnityEditor" }
if ($CaBundle) {
    if (-not (Test-Path -LiteralPath $CaBundle)) { throw "CA bundle missing: $CaBundle" }
    $env:NODE_EXTRA_CA_CERTS = [IO.Path]::GetFullPath($CaBundle)
}
$greenboxProject = Join-Path $PSScriptRoot 'Greenbox'
# This opens the interactive editor for the user, rather than a background helper.
Start-Process -FilePath $UnityEditor -ArgumentList @('-projectPath', ('"' + $greenboxProject + '"'))
