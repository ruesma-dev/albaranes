# blob_lifecycle.ps1
# Fase 2: lifecycle policy que purga los blobs efímeros del hand-off
# (input/ y envelopes/) a los 14 días. Los datos durables viven en SharePoint
# (PDF) y PostgreSQL (datos), así que esto solo limpia plumbing.
#
# Uso:
#     . .\00_vars.ps1     # da $RG y $STORAGE
#     .\blob_lifecycle.ps1
#
# Los workers NO borran en línea (idempotencia at-least-once); el borrado lo
# hace esta policy pasada la ventana.

$ErrorActionPreference = "Stop"
if (-not $STORAGE) { throw "Falta `$STORAGE. Haz primero:  . .\00_vars.ps1" }

$DIAS = 14   # ventana de retención (7-30 recomendado)

$policy = @"
{
  "rules": [
    {
      "enabled": true,
      "name": "purge-efimeros-handoff",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": [ "blockBlob" ],
          "prefixMatch": [ "input/", "envelopes/" ]
        },
        "actions": {
          "baseBlob": {
            "delete": { "daysAfterModificationGreaterThan": $DIAS }
          }
        }
      }
    }
  ]
}
"@

# En PowerShell Windows el JSON inline rompe az; se escribe a fichero ASCII
# (sin BOM) y se referencia con @ruta.
$tmp = Join-Path $env:TEMP "blob_lifecycle.json"
[System.IO.File]::WriteAllText($tmp, $policy, (New-Object System.Text.ASCIIEncoding))

az storage account management-policy create `
    --account-name $STORAGE -g $RG `
    --policy "@$tmp" --only-show-errors | Out-Null

Remove-Item $tmp -Force
Write-Host "OK lifecycle policy en ${STORAGE}: borra input/ y envelopes/ a los $DIAS dias." -ForegroundColor Green
az storage account management-policy show --account-name $STORAGE -g $RG `
    --query "policy.rules[].name" -o tsv
