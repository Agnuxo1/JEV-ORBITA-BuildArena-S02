$Root = "E:\Proyecto-concursos"
$env:UV_CACHE_DIR = Join-Path $Root "_cache\uv"
$env:PIP_CACHE_DIR = Join-Path $Root "_cache\pip"
$env:TEMP = Join-Path $Root "_tmp"
$env:TMP = $env:TEMP
$env:ORBITA_BUILDARENA_ROOT = Join-Path $Root "BuildArena-S02"
$env:ORBITA_JEV_ROOT = "E:\TartanIMU-Cognitive-Stack"
$env:ORBITA_JEV_PROFILE = "agnuxo"
New-Item -ItemType Directory -Force -Path $env:UV_CACHE_DIR,$env:PIP_CACHE_DIR,$env:TEMP | Out-Null
Write-Host "JEV-ORBITA environment configured on E:."
