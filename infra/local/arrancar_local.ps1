# infra/local/arrancar_local.ps1
# Arranca el pipeline local completo, cada servicio en su propia ventana de
# PowerShell, en el orden correcto (consumidores antes que el productor).
# Requiere: Azurite y PostgreSQL locales arrancados, y preparar_local.ps1
# ejecutado al menos una vez.
# Uso:  powershell -ExecutionPolicy Bypass -File .\infra\local\arrancar_local.ps1
#       -SinSv1  para no arrancar el intake del buzon (pruebas sin email)

param([switch]$SinSv1)

$ErrorActionPreference = 'Stop'
$Raiz = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

# --- Guardarrail 1: el .env de sv4 NO puede apuntar a las colas reales ------
$envSv4 = Join-Path $Raiz 'services\albaranes-front\.env'
$colas = (Get-Content $envSv4 -ErrorAction SilentlyContinue) | Where-Object { $_ -match '^COLAS_CONNECTION_STRING=' } | Select-Object -First 1
if ($colas -and $colas -notmatch 'devstoreaccount1') {
    Write-Error "PELIGRO: el .env de sv4 apunta a colas REALES de Azure. Cambia COLAS_CONNECTION_STRING a la cadena de Azurite antes de arrancar."
    exit 1
}

# --- Guardarrail 2: Azurite y PostgreSQL escuchando -------------------------
foreach ($p in @(@{n='Azurite (colas)'; port=10001}, @{n='PostgreSQL'; port=5432})) {
    $t = New-Object Net.Sockets.TcpClient
    try { $t.Connect('127.0.0.1', $p.port); $t.Close() }
    catch { Write-Error "$($p.n) no responde en 127.0.0.1:$($p.port). Arrancalo primero."; exit 1 }
}

$Orden = @(
    @{ nombre = 'sv5 valuation-api'; carpeta = 'albaran-valoracion-api';     cmd = 'main.py' },
    @{ nombre = 'sv6 valorador';     carpeta = 'albaran-valoracion-persist'; cmd = 'main_worker.py' },
    @{ nombre = 'sv3 persistencia';  carpeta = 'albaranes-persistencia';     cmd = 'main_worker.py' },
    @{ nombre = 'sv2 extractor';     carpeta = 'albaranes-api';              cmd = 'main_worker.py' },
    @{ nombre = 'sv4 portal';        carpeta = 'albaranes-front';            cmd = 'main.py' },
    @{ nombre = 'sv1 intake';        carpeta = 'albaranes-email';            cmd = 'main.py' }
)

foreach ($s in $Orden) {
    if ($SinSv1 -and $s.carpeta -eq 'albaranes-email') { Write-Host 'sv1 omitido (-SinSv1)'; continue }
    $dir = Join-Path $Raiz "services\$($s.carpeta)"
    if (-not (Test-Path "$dir\.venv\Scripts\python.exe")) {
        Write-Warning "$($s.nombre): sin venv (ejecuta preparar_local.ps1). Omitido."
        continue
    }
    Start-Process powershell -ArgumentList '-NoExit', '-Command',
        "`$host.UI.RawUI.WindowTitle = '$($s.nombre)'; Set-Location '$dir'; & .\.venv\Scripts\python.exe $($s.cmd)"
    Write-Host "lanzado: $($s.nombre)" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

Write-Host "`nPipeline local en marcha. Portal: http://127.0.0.1:8004/documents" -ForegroundColor Cyan
Write-Host 'Para parar: cierra las ventanas de cada servicio.'
