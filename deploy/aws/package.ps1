$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$output = Join-Path $PSScriptRoot 'app.zip'
$staging = Join-Path $env:TEMP ('tecnostock-aws-' + [guid]::NewGuid().ToString('N'))
$items = @('config', 'inventory', 'static', 'templates', 'Dockerfile', 'manage.py', 'package.json', 'package-lock.json', 'requirements.txt')
try {
    New-Item -ItemType Directory -Path $staging | Out-Null
    foreach ($item in $items) {
        Copy-Item -LiteralPath (Join-Path $project $item) -Destination $staging -Recurse -Force
    }
    $deployDir = Join-Path $staging 'deploy\aws'
    New-Item -ItemType Directory -Path $deployDir -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'install-app.sh') -Destination $deployDir
    if (Test-Path -LiteralPath $output) { Remove-Item -LiteralPath $output -Force }
    Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $output -CompressionLevel Optimal
    Write-Host "Paquete creado: $output"
} finally {
    if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
}
