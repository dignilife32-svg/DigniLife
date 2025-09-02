param(
    [string] $ApiHost = '127.0.0.1',
    [int]    $Port = 8000,
    [string] $UserId = 'A1',
    [int]    $Minutes = 60,
    [ValidateSet('http', 'https')]
    [string] $Scheme = 'http',
    [int]    $TimeoutSec = 12
)

$ErrorActionPreference = 'Stop'

# ---- build base URL safely ----
$ub = [System.UriBuilder]::new()
$ub.Scheme = $Scheme
$ub.Host = $ApiHost
$ub.Port = $Port
$base = $ub.Uri.AbsoluteUri.TrimEnd('/')

$hdr = @{ 'x-user_id' = $UserId; 'Content-Type' = 'application/json' }

Write-Host ("BASE => {0}" -f $base) -ForegroundColor Yellow

# ---- tiny helper: JSON REST call ----
function Invoke-Json {
    param(
        [string]   $Method = 'GET',
        [string]   $Uri,
        [hashtable]$Headers,
        $Body
    )
    if ($PSBoundParameters.ContainsKey('Body') -and $null -ne $Body -and -not ($Body -is [string])) {
        $Body = $Body | ConvertTo-Json -Compress
    }
    return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $Headers -Body $Body
}

# ---- wait until API is ready ----
function Test-ServerReady([int]$timeoutSec = 12) {
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
        if ((Test-NetConnection $ApiHost -Port $Port).TcpTestSucceeded) {
            try {
                $uri = ($base.TrimEnd('/') + '/health')
                $r = Invoke-Json -Uri $uri
                if ($r.status -eq 'ok') { return $true }
            }
            catch { }
        }
        Start-Sleep -Milliseconds 300
    }
    throw ('API not reachable on {0}' -f $base)
}

function Get-DailyPrefix {
    $candidates = @('/learn/daily', '/learn', '/daily')
    foreach ($p in $candidates) {
        try {
            $uri = $base.TrimEnd('/') + $p + '/health'
            $r = Invoke-Json -Uri $uri -ErrorAction Stop
            if ($r.status -eq 'ok') { return $p }
        }
        catch { }
    }
    throw ("No daily prefix found under {0}. Checked: {1}" -f $base, ($candidates -join ', '))
}


# ================= MAIN =================
Write-Host "== Health check ==" -ForegroundColor Cyan
Test-ServerReady -TimeoutSec $TimeoutSec | Out-Null
Invoke-Json -Uri ("{0}/health" -f $base) | ConvertTo-Json | Out-Host

$prefix = Get-DailyPrefix
# (PS5-safe) show '/' when prefix is empty
$prefixShow = if ([string]::IsNullOrEmpty($prefix)) { '/' } else { $prefix }
Write-Host ("Using prefix: {0}" -f $prefixShow) -ForegroundColor Cyan
Invoke-Json -Uri ("{0}{1}/health" -f $base, $prefix) | ConvertTo-Json | Out-Host

# Step 1: start bundle
Write-Host "== POST /bundle/start ==" -ForegroundColor Cyan
$startUri = ('{0}{1}/bundle/start?minutes={2}' -f $base, $prefix, $Minutes)
$startRes = Invoke-Json -Method 'POST' -Uri $startUri -Headers $hdr
$startRes | ConvertTo-Json | Out-Host

# bundle_id
$bundleId = $null
if ($startRes.PSObject.Properties.Name -contains 'bundle_id') { $bundleId = $startRes.bundle_id }
elseif ($startRes.PSObject.Properties.Name -contains 'bundleId') { $bundleId = $startRes.bundleId }
elseif ($startRes.PSObject.Properties.Name -contains 'id') { $bundleId = $startRes.id }
if (-not $bundleId) { throw "bundle_id not found in start response." }

Write-Host ("bundle_id => {0}" -f $bundleId) -ForegroundColor Yellow

# Step 2: submit
Write-Host "== POST /bundle/submit ==" -ForegroundColor Cyan
$submitUri = ('{0}{1}/bundle/submit?bundle_id={2}' -f $base, $prefix, [uri]::EscapeDataString($bundleId))
$body = @{ decisions = 1; correct = 1; seconds_spent = 1 }
Invoke-Json -Method 'POST' -Uri $submitUri -Headers $hdr -Body $body | ConvertTo-Json | Out-Host

# Step 3: bundles
Write-Host "== GET /bundles ==" -ForegroundColor Cyan
$bundlesUri = ('{0}{1}/bundles?limit={2}' -f $base, $prefix, 5)
Invoke-Json -Uri $bundlesUri -Headers $hdr | ConvertTo-Json | Out-Host

# Step 4: summary
Write-Host "== GET /summary ==" -ForegroundColor Cyan
$summaryUri = ('{0}{1}/summary?user_id={2}' -f $base, $prefix, [uri]::EscapeDataString($UserId))
Invoke-Json -Uri $summaryUri -Headers $hdr | ConvertTo-Json | Out-Host

Write-Host "Smoke test: DONE ✅" -ForegroundColor Green
