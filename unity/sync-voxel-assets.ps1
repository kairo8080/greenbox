$ErrorActionPreference = 'Stop'
$greenboxRepo = Split-Path $PSScriptRoot -Parent
$greenboxVoxelDestination = Join-Path $PSScriptRoot 'Greenbox\Assets\Resources\Voxels'
$greenboxAssetRecords = foreach ($greenboxAssetName in @('rasta_bedroom.glb','rasta_character.glb','starter_props.glb')) {
    $greenboxAssetSource = Join-Path $greenboxRepo "game\assets\$greenboxAssetName"
    $greenboxAssetBytes = [IO.File]::ReadAllBytes($greenboxAssetSource)
    if ($greenboxAssetBytes.Length -lt 20 -or [Text.Encoding]::ASCII.GetString($greenboxAssetBytes,0,4) -ne 'glTF' -or [BitConverter]::ToUInt32($greenboxAssetBytes,4) -ne 2 -or [BitConverter]::ToUInt32($greenboxAssetBytes,8) -ne $greenboxAssetBytes.Length) { throw "Invalid GLB export: $greenboxAssetSource" }
    Copy-Item -LiteralPath $greenboxAssetSource -Destination (Join-Path $greenboxVoxelDestination $greenboxAssetName) -Force
    [pscustomobject]@{asset=$greenboxAssetName;sha256=(Get-FileHash -LiteralPath $greenboxAssetSource -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$greenboxAssetBytes.Length;source="game/assets/$greenboxAssetName"}
}
[pscustomobject]@{schema='greenbox-unity-voxel-import-v1';meters_per_voxel=0.05;source_axes='glTF Y-up, right-handed';unity_conversion='glTFast mirrors X';assets=@($greenboxAssetRecords)} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'voxel-imports.json') -Encoding utf8
Write-Output 'Voxel exports synchronized. Unity reimports the three GLB prefabs automatically.'
