param(
    [string]$UnityEditor = 'C:\Program Files\Unity\Hub\Editor\6000.2.6f1\Editor\Unity.exe',
    [string]$Output,
    [string]$CaBundle = $env:NODE_EXTRA_CA_CERTS
)
$ErrorActionPreference = 'Stop'
$greenboxProject = Join-Path $PSScriptRoot 'Greenbox'
if ($CaBundle) {
    if (-not (Test-Path -LiteralPath $CaBundle)) { throw "CA bundle missing: $CaBundle" }
    $env:NODE_EXTRA_CA_CERTS = [IO.Path]::GetFullPath($CaBundle)
}
if (-not (Test-Path -LiteralPath $UnityEditor)) { throw "Unity Editor missing: $UnityEditor. Install Unity 6000.2.6f1 plus Web Build Support in Unity Hub." }
if (-not $Output) { $Output = Join-Path (Split-Path $PSScriptRoot -Parent) 'unity-build' }
$Output = [IO.Path]::GetFullPath($Output)
$greenboxBuildLogDir = Join-Path $greenboxProject 'Logs'
New-Item -ItemType Directory -Path $greenboxBuildLogDir -Force | Out-Null
$greenboxBuildLog = Join-Path $greenboxBuildLogDir 'web-build.log'
$greenboxBuildArguments = @('-batchmode', '-quit', '-projectPath', ('"' + $greenboxProject + '"'), '-buildTarget', 'WebGL', '-executeMethod', 'Greenbox.Editor.GreenboxBuild.BuildWeb', '-greenboxOutput', ('"' + $Output + '"'), '-logFile', ('"' + $greenboxBuildLog + '"'))
$greenboxBuildProcess = Start-Process -FilePath $UnityEditor -ArgumentList $greenboxBuildArguments -WindowStyle Hidden -PassThru
$greenboxBuildProcess.WaitForExit()
if ($greenboxBuildProcess.ExitCode -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $Output 'index.html'))) { throw "Greenbox export failed. Read $greenboxBuildLog" }
Write-Output "Greenbox browser export ready at $Output"
