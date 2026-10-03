$ErrorActionPreference = 'Stop'
$greenboxCsc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $greenboxCsc)) { throw 'The Windows .NET Framework C# compiler is unavailable.' }
$greenboxTestExe = Join-Path ([IO.Path]::GetTempPath()) ('greenbox-domain-' + [Guid]::NewGuid().ToString('N') + '.exe')
try {
    & $greenboxCsc /nologo /warnaserror+ /reference:System.Web.Extensions.dll "/out:$greenboxTestExe" (Join-Path $PSScriptRoot 'Greenbox\Assets\Scripts\SimState.cs') (Join-Path $PSScriptRoot 'tests\SimStateTests.cs')
    if ($LASTEXITCODE -ne 0) { throw 'C# gameplay compilation failed.' }
    & $greenboxTestExe
    if ($LASTEXITCODE -ne 0) { throw 'Gameplay checks failed.' }
} finally {
    if (Test-Path -LiteralPath $greenboxTestExe) { Remove-Item -LiteralPath $greenboxTestExe -Force }
}
