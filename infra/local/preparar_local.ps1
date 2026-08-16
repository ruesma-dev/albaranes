# infra/local/preparar_local.ps1
# Crea el .venv de cada servicio del monorepo e instala sus dependencias
# (albaranes-comun editable + requirements.txt). Idempotente: si el venv ya
# existe no lo recrea, solo reinstala dependencias.
# Uso:  powershell -ExecutionPolicy Bypass -File .\infra\local\preparar_local.ps1

$ErrorActionPreference = 'Continue'
$Raiz = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

# manifest = requirements de la imagen Docker (infra/manifests/svN): es la
# lista REAL de producción; el requirements.txt interno del servicio puede
# estar incompleto (p. ej. sv5/sv6 no listan psycopg, sv2 no lista
# google-cloud-documentai). Se instalan AMBOS.
$Servicios = @(
    @{ carpeta = 'albaranes-email';            llm = $false; manifest = 'sv1' },
    @{ carpeta = 'albaranes-api';              llm = $true;  manifest = 'sv2' },
    @{ carpeta = 'albaranes-persistencia';     llm = $false; manifest = 'sv3' },
    @{ carpeta = 'albaranes-front';            llm = $false; manifest = 'sv4' },
    @{ carpeta = 'albaran-valoracion-api';     llm = $true;  manifest = 'sv5' },
    @{ carpeta = 'albaran-valoracion-persist'; llm = $false; manifest = 'sv6' }
)

$Comun = Join-Path $Raiz 'services\albaranes-comun'
$Fallos = 0

foreach ($s in $Servicios) {
    $dir = Join-Path $Raiz "services\$($s.carpeta)"
    Write-Host "=== $($s.carpeta) ===" -ForegroundColor Cyan
    if (-not (Test-Path $dir)) { Write-Warning "no existe $dir"; $Fallos++; continue }

    if (-not (Test-Path "$dir\.venv")) {
        py -3.12 -m venv "$dir\.venv"
        if ($LASTEXITCODE -ne 0) { Write-Warning "fallo creando el venv"; $Fallos++; continue }
        Write-Host "  venv creado"
    } else {
        Write-Host "  venv ya existia"
    }

    $py = "$dir\.venv\Scripts\python.exe"
    if ($s.llm) { & $py -m pip install --quiet -e "$Comun[llm]" } else { & $py -m pip install --quiet -e $Comun }
    if ($LASTEXITCODE -ne 0) { Write-Warning "fallo instalando albaranes-comun"; $Fallos++ }

    if (Test-Path "$dir\requirements.txt") {
        & $py -m pip install --quiet -r "$dir\requirements.txt"
        if ($LASTEXITCODE -ne 0) { Write-Warning "fallo instalando requirements.txt"; $Fallos++ }
    }

    $manifest = Join-Path $Raiz "infra\manifests\$($s.manifest)\requirements.txt"
    if (Test-Path $manifest) {
        & $py -m pip install --quiet -r $manifest
        if ($LASTEXITCODE -ne 0) { Write-Warning "fallo instalando el manifest $($s.manifest)"; $Fallos++ }
    } else {
        Write-Warning "$($s.carpeta): sin manifest en infra/manifests/$($s.manifest)"
    }
    Write-Host "  OK" -ForegroundColor Green
}

if ($Fallos -gt 0) { Write-Host "`nTerminado con $Fallos aviso(s)/fallo(s): revisa arriba." -ForegroundColor Yellow }
else { Write-Host "`nLos 6 servicios preparados." -ForegroundColor Green }
