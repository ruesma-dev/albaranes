# add_secrets.ps1
# Carga en Key Vault los secretos de la app, pedidos de forma SEGURA (no se
# guardan en disco ni se imprimen). Córrelo DESPUÉS de fase1_infra.ps1 y
# DESPUÉS de rotar las claves.
#
# Uso:
#     . .\00_vars.ps1
#     .\add_secrets.ps1
#
# PG-PASSWORD ya la dejó fase1_infra.ps1; aquí van el resto.

$ErrorActionPreference = "Stop"

# Nombre de secreto en KV  ->  descripción de lo que tienes que pegar.
$secretos = [ordered]@{
    "GRAPH-KEY"               = "JSON de Graph {tenant_id,client_id,client_secret} (SharePoint/correo)"
    "SIGRID-API-FUNCTION-KEY" = "function key de sigrid-api (rotada)"
    "ANTHROPIC-API-KEY"       = "clave de Anthropic (sv2/sv5)"
    "OPENAI-API-KEY"          = "clave de OpenAI (sv2/sv5)"
    "GEMINI-API-KEY"          = "clave de Gemini (sv2/sv5)"
}

foreach ($nombre in $secretos.Keys) {
    Write-Host "`n$nombre  ->  $($secretos[$nombre])" -ForegroundColor Cyan
    $sec = Read-Host "  Pega el valor (vacío para SALTAR)" -AsSecureString
    $val = [System.Net.NetworkCredential]::new("", $sec).Password
    if ([string]::IsNullOrWhiteSpace($val)) {
        Write-Host "  (saltado)" -ForegroundColor DarkGray
        continue
    }
    az keyvault secret set --vault-name $KV --name $nombre --value $val --only-show-errors | Out-Null
    Write-Host "  OK guardado en $KV" -ForegroundColor Green
}

Write-Host "`nSecretos en Key Vault:" -ForegroundColor Yellow
az keyvault secret list --vault-name $KV --query "[].name" -o tsv
