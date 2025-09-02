param(
    [switch]$RunAPI,
    [string]$BindHost = '127.0.0.1',
    [int]$Port = 8000
)
$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$src = Join-Path $repo 'src'

# venv activate (ရှိရင်)
$venv = Join-Path $repo '.venv\Scripts\Activate.ps1'
if (Test-Path $venv) { . $venv }

function Find-ASGIModule([string]$srcDir) {
    $srcName = Split-Path $srcDir -Leaf   # -> 'src'

    # 1) files directly under src/
    foreach ($n in @('router.py', 'main.py', 'app.py')) {
        $p = Join-Path $srcDir $n
        if (Test-Path $p) {
            $mod = [IO.Path]::GetFileNameWithoutExtension($p)   # e.g. 'app'
            return "$srcName.$mod"                              # e.g. 'src.app'
        }
    }

    # 2) package-style: src/<pkg>/<file>.py
    foreach ($d in Get-ChildItem -Path $srcDir -Directory -ErrorAction SilentlyContinue) {
        foreach ($n in @('router.py', 'main.py', 'app.py')) {
            $p = Join-Path $d.FullName $n
            if (Test-Path $p) {
                $mod = [IO.Path]::GetFileNameWithoutExtension($p)
                return "$srcName.$($d.Name).$mod"                 # e.g. 'src.api.app'
            }
        }
    }
    return $null
}

if ($RunAPI) {
    $app = Find-ASGIModule $src
    if (-not $app) { throw "Couldn't find ASGI app under src/ (router|main|app)" }

    Write-Host ("Uvicorn starting on http://{0}:{1}" -f $BindHost, $Port) -ForegroundColor Cyan
    uvicorn "$app:app" --host $BindHost --port $Port --reload
    return
}
