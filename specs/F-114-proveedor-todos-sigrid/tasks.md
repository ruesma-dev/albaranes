<!-- specs/F-114-proveedor-todos-sigrid/tasks.md -->
# F-114 · Tareas (v1)

Rama `feature/F-114-proveedor-todos-sigrid`, worktree `../albaranes-F-114`. Rigor `estandar`: **fase RED** en cada tarea con test (traza en `progress/impl_F-114.md`), cobertura de líneas cambiadas y mutación muestreada (20, semilla de `harness/rigor.json`). Un commit por tarea, `F-114 Tn: ...`. Sin `git push`. Tests sin red ni BBDD. Precondición de `in_progress`: D1–D7 (`design.md` §8) validadas por el humano y la T0 hecha.

## Bloque 0 · medición (MANUAL, solo lectura, antes de implementar)

- [x] T0: Medir `prv` y validar la SQL de la búsqueda con las tres lecturas de abajo por `sql/read` (sigrid-api, solo lectura); resultados en `progress/spec_F-114.md` §T0; si la C falla (R-3) o tarda > 5 s (R-4), PARAR y re-proponer  |  Verificación: MANUAL (humano o líder) — comando de abajo

Comando (PowerShell, desde una consola con `$env:SIGRID_API_BASE_URL`, `$env:SIGRID_API_FUNCTION_KEY` y `$env:SIGRID_API_DATABASE` ya cargadas; ninguna se escribe en fichero):

```powershell
function Leer($sql, $params) {
  $cuerpo = @{ database = $env:SIGRID_API_DATABASE; sql = $sql; parameters = $params; max_rows = 100; timeout_seconds = 30 } | ConvertTo-Json -Depth 5
  $t = Measure-Command { $script:r = Invoke-RestMethod -Method Post -Uri "$($env:SIGRID_API_BASE_URL)/api/sql/read" -Headers @{ 'x-functions-key' = $env:SIGRID_API_FUNCTION_KEY } -ContentType 'application/json' -Body $cuerpo }
  "{0:N0} ms · truncated={1}" -f $t.TotalMilliseconds, $r.truncated; $r.columns -join ' | '; $r.rows | ForEach-Object { $_ -join ' | ' }
}
# A · tamaño: fichas, CIF distintos, vivas, CIF vivos, CIF vivos repetidos, vivas con espacios/minúsculas en el CIF (R-1)
Leer "SELECT COUNT(*) AS fichas, COUNT(DISTINCT v.cif) AS cifs, SUM(CASE WHEN c.fecbaj = 0 THEN 1 ELSE 0 END) AS vivas, COUNT(DISTINCT CASE WHEN c.fecbaj = 0 THEN v.cif END) AS cifs_vivos, (SELECT COUNT(*) FROM (SELECT v2.cif FROM prv v2 JOIN con c2 ON c2.ide = v2.ide WHERE c2.tip = ? AND c2.emp = ? AND c2.fecbaj = 0 GROUP BY v2.cif HAVING COUNT(*) > 1) x) AS cifs_vivos_repetidos, SUM(CASE WHEN c.fecbaj = 0 AND v.cif <> REPLACE(UPPER(v.cif), ' ', '') COLLATE Latin1_General_CS_AS THEN 1 ELSE 0 END) AS vivas_cif_no_normal FROM prv v JOIN con c ON c.ide = v.ide WHERE c.tip = ? AND c.emp = ?" @(5, 1, 5, 1)
# B · bloqueos activos (D3): proveedores vivos con algún prvblo de la empresa 1 sin fecha de baja
Leer "SELECT COUNT(DISTINCT b.prvide) AS vivos_bloqueados FROM prvblo b JOIN con c ON c.ide = b.prvide WHERE b.emp = ? AND ISNULL(b.fecbaj, 0) = 0 AND c.tip = ? AND c.emp = ? AND c.fecbaj = 0" @(1, 5, 1)
# C · la SQL de la búsqueda de design §3, tal cual, con «cera»
Leer "SELECT TOP (?) v.cif AS cif, MIN(v.raz) AS nombre, COUNT(*) AS fichas FROM prv AS v JOIN con AS c ON c.ide = v.ide WHERE c.tip = ? AND c.emp = ? AND c.fecbaj = ? AND v.cif IS NOT NULL AND LTRIM(RTRIM(v.cif)) <> '' AND (v.raz COLLATE Latin1_General_CI_AI LIKE ? ESCAPE '!' OR REPLACE(REPLACE(UPPER(v.cif), ' ', ''), '-', '') LIKE ? ESCAPE '!') GROUP BY v.cif ORDER BY MIN(v.raz), v.cif" @(51, 5, 1, 0, '%cera%', '%CERA%')
```

## Bloque A · cliente y endpoint

- [x] T1: `ProveedorOption.fichas` y `BusquedaProveedores` en `review_models.py`; `_patron_like`, constantes, `_SQL_PROVEEDORES_TODOS` y `buscar_proveedores` en `sigrid_lookup_client.py` (design §3); tests de parámetros y SQL (R15), patrones y escape (R16), agrupado y dedupe por CIF normalizado (R17), límite + 1 y `mas` (R18), propios y vacíos fuera (R19), `NO_TOLERA` y log (R20), mínimo sin llamar, y `fetch_proveedores_por_obra` intacto (R21)  |  Verificación: `pytest services/albaranes-front/tests/test_f114_cliente.py -k "f114_r15 or f114_r16 or f114_r17 or f114_r18 or f114_r19 or f114_r20 or f114_r21"`
- [ ] T2: Endpoint `GET /api/sigrid/proveedores/todos` en `app.py` (design §3); tests: respuesta `{ok, items:[{cif,nombre,fichas}], mas}` (R12), `q` corto sin llamar al cliente (R13), sin cliente y con excepción ⇒ 200 `ok=false` (R14), `/api/sigrid/proveedores` con la misma respuesta de antes (R21)  |  Verificación: `pytest services/albaranes-front/tests/test_f114_endpoint.py`

## Bloque B · ficha

- [ ] T3: Plantilla y CSS (design §4): `div.campo-combo` con el check `#proveedor_solo_obra` marcado, `data-solo-obra-check` y `data-endpoint-todos`, nada en solo lectura; tests sobre el texto de plantilla y CSS (R1, R9: `checked` en el HTML)  |  Verificación: `pytest services/albaranes-front/tests/test_f114_plantilla.py`
- [ ] T4: Funciones puras de `app.js` (`textoBusquedaProveedor`, `urlProveedoresTodos`, `etiquetaProveedorGlobal`, `mensajeListaObraVacia`) y tests con node (R3 mínimo, R6 etiqueta y fichas, R10 mensaje)  |  Verificación: `pytest services/albaranes-front/tests/test_f114_js.py -k "f114_r3 or f114_r6 or f114_r10"`
- [ ] T5: Modo global en `initCombo` (design §5): debounce 300 ms y secuencia (R4), «Hay más» (R5), `title` de varias fichas (R6), `choose` sin cambios (R7), `change` del check (R8), sin `localStorage` (R9), mensaje de lista vacía o sin obra (R10), errores (R11), modo marcado idéntico (R2); tests con `dom_falso.js` y `fetch` falso  |  Verificación: `pytest services/albaranes-front/tests/test_f114_js.py` y `pytest services/albaranes-front -k "f051 or f065_f1_js or f065_f3bis"`

## Bloque C · documentación, calidad y cierre

- [ ] T6: Viñeta en la regla 17 de `docs/ARCHITECTURE.md`, fila del endpoint en `sv4.md` y viñeta en §8 de `azure-apps/albaranes.md` (commit local en `azure-apps`, sin push) (R23); `git diff --stat` sin ficheros fuera de sv4, `docs/` y `azure-apps` (R22)  |  Verificación: revisión del reviewer contra R22 y R23
- [ ] T7: Campaña de mutación muestreada sobre `sigrid_lookup_client.py`; supervivientes con test nuevo o justificación en `progress/mutacion_F-114.md`  |  Verificación: `python -m harness.mutacion --feature F-114`
- [ ] T8: Prueba de navegador con sv4 local y Sigrid de lectura: el documento `097191e9-…` si está en la BBDD a la que apunte sv4 local (si no, otro cualquiera; ver la memoria de entorno), desmarcar, buscar por nombre y por CIF, ver «Hay más» y «N fichas»; elegir NO se hace (guardaría en la BBDD real; solo con autorización del humano)  |  Verificación: MANUAL (líder, Chrome, solo lectura) — resultado en `progress/impl_F-114.md`
- [ ] T9: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`

Despliegue (humano, tras APPROVED y fusión en `dev`): solo sv4, `Set-DeployTag; .\deploy.ps1 -Only sv4` desde `infra/`; sin variables nuevas.
