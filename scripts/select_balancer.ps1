param(
    [ValidateSet('round-robin','weighted','least-connections','ip-hash')]
    [string]$Mode = 'round-robin'
)
$root = Split-Path -Parent $PSScriptRoot
$source = Join-Path $root "nginx/$Mode.conf"
$target = Join-Path $root 'nginx/default.conf'
Copy-Item -LiteralPath $source -Destination $target -Force
docker compose -f (Join-Path $root 'compose.yaml') exec -T nginx nginx -t
if ($LASTEXITCODE -ne 0) { throw 'La configuración de Nginx no es válida.' }
docker compose -f (Join-Path $root 'compose.yaml') exec -T nginx nginx -s reload
if ($LASTEXITCODE -ne 0) { throw 'Nginx no pudo recargar la configuración.' }
Write-Output "Balanceador activo: $Mode"
