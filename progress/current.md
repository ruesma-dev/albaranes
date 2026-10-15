<!-- progress/current.md -->
# Trabajo en curso

**F-064 · `in_progress` (2026-10-15): review pasada 1 APPROVED (`progress/review_F-064.md`), cierre condicionado a
T9, T10 y la aceptación del equivalente #28.** Rama `feature/F-064-proveedor-en-prompts`, worktree `../albaranes-F-064`
(*junction* `services\albaranes-front\.venv`: quitarla con `cmd /c rmdir` ANTES de `git worktree remove`). Decisiones
del humano (2026-10-15): **#28 aceptado por escrito** («Acepto los dos») y **O1 aprobada** (cláusula «emisor
ilegible» en la regla `proveedor_emisor` de IA2). **`dev` (`d79b3d9`) fusionado en la rama** (conflictos en
`features.json`, `BACKLOG.md`, `current.md`, `ARCHITECTURE.md` e inventario de mutación: se conserva todo lo de `dev`
y F-064 queda como única `in_progress`). **Pasada O1 hecha, pendiente de review** (`progress/impl_F-064.md`
§«Pasada O1»). Humano: T9 y T10 (evals con LLM real, tras la review de O1) y T12 (desplegar solo sv2 tras fusionar);
comandos en `progress/impl_F-064.md` §6. Historia de la spec (PARADA 1, Q1–Q6) en `progress/spec_F-064.md`.

**F-070 · `blocked` (2026-10-15): review APPROVED (pasada 2), equivalente #17 aceptado por el humano, fusionada en `dev`.** Espera la MANUAL T13 del humano (desplegar sv4 y luego sv3; comando en el bloque «F-070 · MANUAL T13»). Al verificarla en pantalla, pasa a `done`.

**F-070 · `in_progress` (2026-10-14), urgente, prioridad 1, rigor `critico`** — la obra siempre con el 0 inicial
salvo VAR y POSTV2 (HERMANOS SAN JUAN: merge con `686`, combos de sv4 vacíos). Spec en
`specs/F-070-obra-con-cero-inicial/`, informe en `progress/spec_F-070.md` (PARADA 1 APROBADA: P1 regla tal cual, `900`
⇒ `0900`; P2 solo VAR y POSTV2; P3 sin corregir merges guardados). Rama `feature/F-070-obra-con-cero-inicial`, worktree
`../albaranes-F-070` (*junction* `.venv` de sv4; quitarla con `cmd /c rmdir` antes de `git worktree remove`). `dev`
(`4f1e802`, F-053 v8) fusionado en la rama. **Pasada 2 hecha (2026-10-15, CR1 de `progress/review_F-070.md`), pendiente de review**: campaña a mano rehecha, 17/18 muertos y el #17 superviviente equivalente **pendiente de la aceptación escrita del humano**; O2, O3 y O4 aplicadas (O1 no). Pasada 1: T1–T12 y T14 hechas
(informe `progress/impl_F-070.md`; mutación 4/4 de la herramienta y 18/18 a mano; cobertura 100 % de 28 líneas;
`azure-apps` `0136e1a`, sin push). `init.sh` tal cual en el worktree sale KO solo porque sv3/sv4/sv9 importan la comun
del árbol principal (`dev`); con la comun de la rama, `ENTORNO LISTO` (detalle en el informe, T14). Pendientes del
humano: T0 (opcional) y T13 (despliegue sv4 → sv3 tras fusionar).
Orden de despliegue: sv4 → sv3; sv9 con F-053.

### F-070 · MANUAL T13 del humano (tras el APPROVED, la fusión en `dev` e `init.sh` en verde en el árbol principal)

Desplegar sv4 y después sv3 (design §6; sin DDL, cualquier orden vale). sv9 NO: sale con F-053 desde un `dev` con F-070.
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
. .\00_capps_vars.ps1
Set-DeployTag
.\deploy.ps1 -Only sv4
.\check_deploy.ps1
.\deploy.ps1 -Only sv3
.\check_deploy.ps1
```
VERDE si `check_deploy.ps1` muestra sv4 y sv3 con el tag recién construido y réplicas arriba, y en `https://<sv4>` un
albarán pendiente de HERMANOS SAN JUAN (merge con `686`) ofrece en el combo de partida las partidas de la 0686 (no
solo «Almacén») y «Solo volver a buscar» encuentra CTSU24/0524. ROJO si el combo sigue con solo «Almacén».

### F-070 · MANUAL T0 del humano (opcional, SOLO LECTURA, no bloquea)

Medir en la BBDD `albaranes` de Azure los merges activos con obra de 3 cifras y de dónde salió su obra. Sesión con
`default_transaction_read_only=on` (como `diag_f062.py`, que aborta si `SHOW transaction_read_only` no da `on`):
```sql
SELECT m.id, m.obra_codigo, m.obra_codigo_origen, m.approved, m.created_at_utc,
       COALESCE(j #>> '{data,origen_datos,obra,motivo}',      j #>> '{origen_datos,obra,motivo}')      AS motivo,
       COALESCE(j #>> '{data,origen_datos,obra,validada}',    j #>> '{origen_datos,obra,validada}')    AS validada,
       COALESCE(j #>> '{data,origen_datos,obra,valor_correo}', j #>> '{origen_datos,obra,valor_correo}') AS valor_correo,
       COALESCE(j #>> '{data,origen_datos,obra,valor_papel}', j #>> '{origen_datos,obra,valor_papel}') AS valor_papel
FROM albaran_documents_merge m
CROSS JOIN LATERAL (SELECT m.raw_extraction_json::jsonb AS j) x
WHERE m.is_active AND m.obra_codigo ~ '^[0-9]{3}$'
ORDER BY m.created_at_utc DESC;
```
Anotar los recuentos en `progress/spec_F-070.md` §2 (criterio en su Anexo A). El arreglo no depende del resultado.

**F-053 · `blocked` (2026-10-14) — v8 APROBADA (review pasada 2) y fusionada en `dev` (`4f1e802`); espera la MANUAL
T51 del humano** (despliegue sv6, sv3 → sv9 con `ALTA_SIGRID_COMMIT=false` → sv4, y aprobaciones de prueba; comandos
abajo). Pasada a `blocked` para dejar paso a F-070 (máximo una `in_progress`); el párrafo siguiente es el estado de la
v8 antes de la review.

**F-053 · `in_progress` · v8 (Bloque H) IMPLEMENTADA (2026-10-14), pendiente de review.** T41–T50 y T52 hechas en
`feature/F-053-alta-sigrid` (`usu` del alta = login de quien aprobó o respaldo `pgris`; R49 la cabecera de Easy Auth
manda; «Reintentar adjunto»; R14 normalizado). Informe: `progress/impl_F-053_v8.md`; mutación:
`progress/mutacion_F-053_v8.md` (64 mutantes, 62 muertos, 2 equivalentes). `azure-apps` `77c6bf6` (sin push).
Para el líder: review; propuesta de filas de consumo del contrato para la sesión de sigrid-api en
`progress/propuestas_a_sigrid_api_F-053.md` §C (en sigrid-api no se ha tocado nada). Falta la MANUAL **T51** (abajo),
tras APPROVED y fusión. El bloque «F-053 · `blocked`» de más abajo es anterior a la v8.

### F-053 v8 · MANUAL T51 del humano (comandos exactos, PowerShell)

Cuándo: tras el APPROVED del reviewer, la fusión de `feature/F-053-alta-sigrid` en `dev` y `init.sh` en verde en el
árbol principal. Orden de design §8: sv6 y sv3 → sv9 → sv4, **con DESDE vacía**; DESDE solo después (R6 ignora lo
aprobado antes de DESDE, U3). Nadie toca `ALTA_SIGRID_COMMIT` (sigue `false`: simulación).

1. Desplegar (misma consola; `Set-DeployTag` fija el tag por fecha):
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
. .\00_capps_vars.ps1
Set-DeployTag
.\deploy.ps1 -Only sv6,sv3
.\deploy.ps1 -Only sv9
.\deploy.ps1 -Only sv4
.\check_deploy.ps1
```
   `ca-sv9-alta-sigrid` ya existe (T0c); si no existiera, en vez de `.\deploy.ps1 -Only sv9`:
   `.\build_images.ps1 -Only sv9` y `.\create_capps_sv9.ps1`. `deploy.ps1` enseña `ALTA_SIGRID_COMMIT` de sv9: debe
   decir `simulacion`.
2. Encender en simulación: en `infra\00_capps_vars.ps1` pon `$Global:ALTA_SIGRID_DESDE_UTC` a la hora UTC de ahora
   (p. ej. `"2026-10-20T08:00:00Z"`; `$Global:ALTA_SIGRID_USUARIO_RESPALDO` ya es `"pgris"`) y, en la misma consola:
```powershell
. .\00_capps_vars.ps1
.\set_alta_sigrid.ps1
```
   VERDE si la comprobación final dice `OK` en las tres variables comunes, `ALTA_SIGRID_USUARIO_RESPALDO (sv9):
   'pgris'`, `ALTA_SIGRID_COMMIT (sv9, no se toca): 'false'` y termina en «Ajustes del alta aplicados a sv9 y sv4.».
3. En `https://<sv4>` con tu usuario: aprueba UN albarán valorado desde la ficha («Guardar y aprobar») y OTRO desde
   el listado («Aprobar»). Espera unos segundos y refresca las dos fichas.
4. Lectura (solo lectura, BBDD `albaranes` de Azure, con la URL que uses para `psql`):
```powershell
psql "$env:ALBARANES_DB_URL" -c "SET default_transaction_read_only = on; SELECT document_id, estado, modo, approved_by, peticion_json::json->>'usu' AS usu FROM albaran_altas_sigrid ORDER BY creado_at_utc DESC LIMIT 5;"
```
   VERDE si en las dos filas `approved_by` = tu correo (`pgris@ruesma.es`), `usu` = `pgris`, `modo` = `simulacion`,
   y el panel «Alta en Sigrid» de las dos fichas dice «Usuario de Sigrid: pgris» **sin** «(respaldo)». ROJO si
   `approved_by` sale vacío o con `DEFAULT_REVIEWER` (la ficha no leyó la cabecera, R49), si `usu` no es `pgris`, o
   si el estado es `error` con `usuario_no_resuelto` (lectura de `dbo.usu` caída o respaldo sin poner).
5. Opcional (riesgo 1 de la v8): `SELECT approved_by, COUNT(*) FROM albaran_documents_merge WHERE approved GROUP BY 1;`
   (misma forma, solo lectura) y mirar si la parte antes de la @ de cada uno es un login de Sigrid; los que no, caen al
   respaldo hasta F-069.

**F-065 · CERRADA (`done`, 2026-10-13)**: fases 1, 2, 3 y 3 bis (pasadas 1–5) APROBADAS, en `dev` (`53515de`) con
`init.sh` en verde (raíz 1083, sv4 1287) y sv4 desplegado (`r20261013-1836`). MANUAL T19, T27 y T35 hechas por el
humano (T19 punto 6, obra sin partidas, solo con tests). Resumen en `progress/history.md`. Lo aplazado: **F-068**
(F7 con el foco fuera de la fila abre el diálogo de Edge; O8/O9 de la review). Guía de uso para los administrativos:
borrador en el Outlook del humano (2026-10-13). Siguiente: F-053 (usuario del alta = correo de quien usa la app,
respaldo el del humano; T0b/T0c autorizadas; O1 = botón de reintento; 10 equivalentes aceptados) y revisar con el
humano F-066, F-067, F-058, F-059 y X4.

**F-063 · `done` (2026-10-08)**, fusionada en `dev` con `init.sh` en verde. Pendiente del humano: desplegar solo sv3; en los merges `b1d3e179` y `401d9c00`, «Elegir proveedor» FEYMACO a mano. Comandos de la MANUAL T8 en `progress/impl_F-063.md` §7.

**F-062 · `done` (2026-10-08)**, fusionada en `dev` (`d052106`) con `init.sh` en verde. Pendiente del humano: despliegue de solo sv3 y vigilancia T12 (comandos abajo).

> Podado el 2026-10-01 al cerrar F-052 (C2 de `progress/review_F-052.md`). El `current.md` anterior, íntegro, está
> en `progress/historico/current_2026-10-01_cierre_F-052.md`; el resumen de F-052, en `progress/history.md`.
> Aquí solo queda lo vivo. Lo que manda sobre el estado de cada feature es `harness/features.json`.

### F-062 · MANUAL del humano (comandos exactos, PowerShell)

**T0b (opcional, recomendable antes de desplegar) · Anexo A.1 de `progress/spec_F-062.md`, SOLO LECTURA.** El
script del líder `diag_f062.py` abre la sesión con `default_transaction_read_only=on`, comprueba que
`SHOW transaction_read_only` da `on` antes de consultar (si no, aborta), no imprime credenciales ni precios y
lanza A.1, A.2 y A.3 seguidas. Con el venv de sv3 del árbol principal (trae `psycopg`) y el mismo `.env` con los
`PG_*` de la BBDD `albaranes` de Azure que usaste para `diag_proveedor.py` (6.1–6.3):
```powershell
& "C:\Users\pgris\PycharmProjects\albaranes\services\albaranes-persistencia\.venv\Scripts\python.exe" "C:\Users\pgris\AppData\Local\Temp\claude\C--Users-pgris-PycharmProjects-albaranes\f36c80f5-0cba-463e-95e9-161d51e3f583\scratchpad\diag_f062.py" "<ruta del .env con los PG_* de Azure>"
```
Si el scratchpad ya no existe, el SQL íntegro está en el Anexo de `progress/spec_F-062.md`. Criterio: en
`==== A.1`, ningún `otro_proveedor` en un documento que la regla de R3–R4 habría dado por candidato claro (eso
sería una corrección equivocada). Anotar el resultado en `progress/spec_F-062.md` §2; si sale alguno, volver a
la spec antes de desplegar.

**T12 (tras fusionar en `dev` y con `init.sh` en verde en el árbol principal) · desplegar SOLO sv3:**
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
.\deploy.ps1 -Only sv3
.\check_deploy.ps1
```
Criterio: `check_deploy.ps1` muestra sv3 con la revisión y el tag recién construidos, réplicas arriba, y el resto
de apps sin cambios. Después, **unos días de vigilancia con la consulta A.3** (solo lectura, mismo script y mismo
comando que T0b: su bloque `==== A.3 correcciones F-062` lista cada merge activo con `proveedor_cif_corregido`).
Revisar en sv4 cada documento listado: CIF aplicado = proveedor real y `contratos_busqueda_resultado` =
`encontrados`. Un caso mal aplicado ⇒ `RED_PROVEEDOR_CORRECCION_ENABLED=false` en la Container App de sv3 (la
decide y la aplica el humano) y volver a la spec. No bloquea el `done`.

**F-053 · `blocked` (2026-10-09) — esperando al humano, código terminado y en `dev`.** Fases 1 y 2 APROBADAS
(`progress/review_F-053_fase2.md`), fusionada en `dev` (`039a118`, `cb125af`) con `init.sh` en verde (T0d, T30).
O1, los equivalentes, T0b y T0c quedaron resueltos el 2026-10-13 (abajo, v8). Falta: aprobar la v8 e implementarla
(Bloque H), despliegue en simulación (sv6, sv3 → sv9 con `ALTA_SIGRID_COMMIT=false` → sv4 → DESDE), T26–T28, T51 y,
con autorización, T29. F-065 fase 1 ya está desplegada (2026-10-11). Se bloqueó para dejar paso a F-065 (máximo una
`in_progress`).
- **2026-10-13 · spec v8 escrita (spec-author), PARADA 1 pendiente** (`progress/spec_F-053.md` §«v8»; rama
  `feature/F-053-alta-sigrid` con `dev` fusionado, `53515de`). El humano resolvió: `usu` = usuario del correo de
  Ruesma de quien usa la app (respaldo, el suyo), O1 = a (botón «Reintentar adjunto»), 10 equivalentes aceptados,
  permiso para T0b/T0c. **Hechas T0b y T0c** (solo lectura): `pgris` existe en `dbo.usu` y `pgros` no; App Settings
  de sigrid-api conformes; `entref` sí es el número del proveedor pero con formato libre (U6: normalizar en R14).
  Hallazgo: la ficha de sv4 nunca guarda quién aprueba (el PUT no lee la cabecera de Easy Auth); el listado sí.
  Propuesta: cambian R12, R14, R22, R23, R29, R30; nuevas R47–R49; Bloque H (T41–T50), MANUAL T51, T52.
  **Decisiones del humano U1–U7** en esa sección. Sin código tocado; F-053 sigue `blocked` en `features.json`.
- MANUAL pendientes y comandos: `specs/F-053-alta-sigrid/tasks.md` (T0, T22, T26, T27, T27b, T27c, T28, T29, T51).
- Para el líder: Parte B de `progress/propuestas_a_sigrid_api_F-053.md` con sigrid-api; propuesta de `CLAUDE.md` de
  design §9 sin aplicar; el hallazgo R23/R30 (adjunto en error sin botón) lo cierra la v8 (O1 = a, T47).
  (Podado el 2026-10-11 el bloque viejo «`in_progress`» de F-053, O7 de `progress/review_F-065_fase1.md`.)

**F-051 · CERRADA (`done`, 2026-10-09): T22–T24 hechas por el humano (`progress/impl_F-051.md` §6 bis).** Antes: `blocked` (2026-10-06) y FUSIONADA en `dev`. Implementación APROBADA por el reviewer (pasada 2) e `init.sh`
en verde. **T21 hecha** (evals con LLM, 2026-10-06 11:07 UTC, informe local `progress/evals_F-051.md`): frente a F-048,
IA3 417→397 fallos, E2E 545→522, partida final 102→85; IA1 e IA4 iguales; los 4 casos que empeoran son variación del
modelo o recuento (GEN-005, RES-009, MOR-004). **Bloqueo:** T22, T23 y T24 (pruebas manuales en local y navegador)
aplazadas por decisión del humano «hasta que terminemos la escritura» (F-053); se fusiona en `dev` para que F-053 use
la regla de almacén. Pasa a `done` cuando el humano haga T22–T24. No desplegar sv6/sv4/sv2 con F-051 hasta entonces
salvo decisión expresa del humano.

**F-051 · implementación (histórico: `in_progress` del 2026-10-05 al 2026-10-06)** en la rama `feature/F-051-almacen-por-linea`
(worktree `../albaranes-F-051`, con `dev` fusionado el 2026-10-05, que trae F-054): almacén por línea, spec v4
aprobada por el humano en la PARADA 1 («si», 2026-10-05). Informe de spec en `progress/spec_F-051.md` §v4; el del
implementer, en `progress/impl_F-051.md` (la tarea en curso, en «F-051 · estado de la implementación», abajo).
**Todas las decisiones cerradas por el humano, sin preguntas abiertas.** D1 rehecha: «en el visor cuando una línea
no tenga partida que sea almacén» ⇒ almacén = partida final vacía, tenga o no marca (`partida_action` solo
trazabilidad); desaparece el estado «sin partida»; vaciar la partida en sv4 = elegir almacén (sin derivada, la fila
Sigrid sigue Sigrid); la confianza ya no resta por partida vacía. D2: cualquier familia; revisión no bloqueante en
destinadas. D3, D4, D5 (se pierde al revalorar ⇒ **F-058**) y D7 (**F-007 a `pending`**) confirmadas.
**Para otras ramas (no tocadas desde aquí)**: F-053 debe dar de alta como almacén toda partida final vacía
(desaparece `linea_sin_partida`); F-049 bloque C (T31): «Sin partida → almacén» = partida final vacía sin mirar la
marca (cierra su O4). Ambas cosas en `specs/F-051-almacen-por-linea/design.md`, «Contrato con F-053 y con F-049».
**Fichas nuevas en esta rama** (`pending`): **F-058** revalorar no pierde partidas ni almacén a mano (p2, `critico`),
**F-059** etiquetas legibles de motivos de revisión en sv4 (p3, `estandar`), **F-060** tipología de líneas
acopiables (p2, `critico`; decidir junto con la nueva spec de F-007 o fusionarlas).

### F-051 · estado de la implementación

- **T1–T20 y T25 hechas** (2026-10-05); informe en `progress/impl_F-051.md`. **T21–T24 son del humano**
  (evals con LLM y MANUAL; comandos en el informe, §6).
- **Review pasada 1: CHANGES_REQUESTED** (`progress/review_F-051.md`). **Pasada 2 hecha** (2026-10-05), informe en
  `progress/impl_F-051_pasada2.md`: H1 (el banco de evals compone sv6 con almacén y familias destinadas + test que
  recorre todos los puntos de composición), H2 (guardar solo envía la partida si cambió), H3 (test de R12 que
  ejecuta el JS con node), H4 (`azure-apps/albaranes.md`, commit en azure-apps), H5 (dictamen: R20 vale en
  cualquier fila Sigrid), H6 (quitar la junction con `cmd /c rmdir`, nunca `Remove-Item`), O2 (el aviso «pasará a
  NUEVA» no salta con la partida de la casada) y la **decisión del humano**: fuera de almacén el input pinta la
  partida FINAL. Falta la review de la pasada 2.
- **Para el humano**: ¿los ✓/⚠ de partida deben comparar con la final pintada o con la de la casada (hoy, la de la
  casada)? O1 se queda como está (decisión del humano).
- **T21 (previa) hecha** (2026-10-05, opción a del humano): RES-001…007 esperan almacén (`null`) en la línea 1, y
  (2.ª tanda, decisión del humano) las 12 líneas con el literal `ALMACEN`/`almacen` también. Libros
  `IA3_valoracion.xlsx` y `RESULTADO_FINAL.xlsx` del árbol principal ya corregidos (copia previa
  `*.20261005-1759.xlsx`) y fixtures regenerados desde ellos: sincronizados. Evals deterministas: 1025 → 972
  entradas FALLO/AVISO, ninguna nueva. Detalle y comandos de T21/T23: `progress/impl_F-051_t21_previa.md`.
- Entorno del worktree: *junction* `services/albaranes-front/.venv` → venv de sv4 del árbol principal (ignorada
  por git). Se quita con `cmd /c rmdir services\albaranes-front\.venv` ANTES de `git worktree remove`.

**F-054 · CERRADA (`done`, 2026-10-02)**, review de cierre APROBADA: sv1 ingiere los PDF **e imágenes** de correos
adjuntos (`message/rfc822`). Fusionada en `dev` (`639afbb`). Pendiente del humano: despliegue de sv1 y la
verificación MANUAL T12 (sección «F-054 · lo que queda» al final). Resumen en `progress/history.md`.

## LO PRIMERO AL ABRIR LA PRÓXIMA SESIÓN

- **F-053 `in_progress`**, fases 1 y 2 implementadas (bloque de arriba, `progress/impl_F-053_fase2.md`). Es la única
  `in_progress`. Siguiente: review de la fase 2; luego fusionar en `dev` e `init.sh` en el árbol principal.
- **F-051 · CERRADA (`done`, 2026-10-09)** tras T22–T24. Despliegue (lo pide el humano): sv6 → sv4 → sv2, junto con F-053.
- **F-054 · CERRADA (`done`, 2026-10-02)** y fusionada en `dev`. Pendiente del humano: `.\deploy.ps1 -Only sv1` +
  `.\check_deploy.ps1` desde `infra/` y la **T12 MANUAL** (procedimiento al final). La T12 no bloquea el `done`.
- **F-052 · CERRADA (`done`, 2026-10-01)**, fusionada en `dev` y desplegada (sección de abajo).
- **F-055** (IA2 elige el proveedor entre los de la obra): `pending`, prioridad 1. Depende de F-052.
- **Fichas nuevas del cierre de F-052** (`pending`, prioridad 2): **F-056** re-búsqueda doble en sv4 y **F-057**
  truncado sin comprobar en los clientes colindantes de sv4 y sv3.
- Crédito de OpenAI: resuelto. Los 3 albaranes del 2026-09-30 se procesaron hacia las 14:07 (nada en poison).

F-051 (con F-058, F-059, F-060 y el cambio de F-007) está en `dev`. F-053 y F-061 (familia `medios_auxiliares`, de
la P1 de F-053) están registradas en la rama de F-053.

## F-052 · cerrada, fusionada y desplegada (2026-10-01)

- Merge a `dev` por el humano (`a7a53ef`, subido a `origin/dev`). Despliegue del humano: sv3 `r20261001-1654`
  (DDL `contratos_busqueda_*` OK en producción, comprobado en Log Analytics) → sv4 `r20261001-1657` (100 % del
  tráfico; la revisión vieja seguía activa: `fix_revisiones.ps1 -Only sv4`).
- **T23 cerrada por el humano (2026-10-01)**: «hemos estado probando, no hace migrar nada de albaranes antiguos.
  da t23 por cerrada». Sin saneamiento de históricos (D5): si aparece alguno, se corrige a mano en sv4 con «Solo
  volver a buscar» o cambiando el CIF y guardando. Comando y SELECT de sospechosos, por si se necesitan: T23 en
  `specs/F-052-proveedores-truncados/tasks.md` y `progress/spec_F-052.md` §Anexo.

### 3. Observaciones de la review de cierre que siguen vivas

- **Re-búsqueda doble en sv4 → ficha F-056** (O-C2 + mejora menor de T22 + O-C8). La mejora de T22, tal como la
  anotó el humano: un «Guardar» pulsado mientras la ficha está en «Buscando…» relanza otra búsqueda, porque el
  rastro aún tiene el CIF/obra de antes. Inocuo (sv3 y sv6 reemplazan), pero es trabajo doble. Arreglo barato:
  mientras busca, sv4 no relanza si CIF y obra son los mismos con los que lanzó la búsqueda en curso. O-C2: el
  autoguardado del combo (obra y luego proveedor) publica dos re-búsquedas. O-C8: «Solo volver a buscar» con CIF y
  obra vacíos publica un mensaje que sv3 descarta sin sellar.
- **Truncado sin comprobar en los clientes colindantes → ficha F-057** (O-C4 + D6, que decía «ficha aparte» y no
  existía): `header_and_lines` de sv4 (`max_rows=1000`, sin `comprobar_truncado`) y `SigridApiObraClient` de sv3.
- **O-B2 · enseñar al humano** (nunca la aceptó por escrito): extensiones de R21, `replace_contratos` fallido →
  rastro `error`; `enabled=False` → sin sello. Consta en `history.md` como decisión.
- **El «1.000» ajeno, para el humano (otros dueños)**: `PycharmProjects/CLAUDE.md` dice que sigrid-api sirve «como
  máximo 1.000 filas por petición» y otros documentos de `azure-apps` lo repiten. El 1.000 era el `max_rows` del
  cliente; sigrid-api admite 500.000 (`docs/ARCHITECTURE.md` «Acceso a datos»).

### 4. PENDIENTE · portar a `arnes-base` (regla de propagación)

`harness/mutacion.py` cuenta a veces como VIVO un mutante muerto. 3 casos en F-052, sin causa encontrada: en
paralelo (4 workers, `07f89cf`) `sigrid_api_contrato_client.py:1081` y `verificar_f052_proveedores_obra.py:331`;
en serie (`dcca978`) `ruesma_comun/obras/codigo.py:39`. Los tres mueren reevaluados aislados con
`ejecutar_campania` en un worktree limpio (mismo intérprete y comando, `.pyc` purgado). Siempre en la dirección
conservadora. Abrir feature de arnés para reproducir y corregir, y portarla a `arnes-base`. Relacionada: F-041.

Propuesta de automejora de la review de cierre (no aplicada): que `init.sh` avise si `current.md` cita como vivo
(`in_progress`/`blocked`) un ID que `features.json` tiene `done`. Genérica: si se aplica, va también a `arnes-base`.

## Arrastre heredado (anterior a F-052; sin verificar desde su fecha)

Resumido del `current.md` anterior; el detalle, en el archivo de `historico/`. Antes de actuar, comprobar que sigue
vigente.

- **F-047** (`spec_ready`, aparcada el 2026-09-24): al retomarla, cablear `anadir_opcion_sin_correo` en el CLI del
  ciclo, pasar `correo=correos.cargar_correo(caso_id)` desde `ciclo.py` y traer
  `tests/test_f047_r5_seleccion_contrato.py`; nota al final de `specs/F-047-evals-ciclo-completo/tasks.md`. Faltan
  además los 130 supervivientes de `progress/mutacion_F-047.md`, T24–T26 y limpiar 28 worktrees huérfanos.
- **F-048**: confirmar que su despliegue (sv3 → sv2 → sv1 → sv4) está hecho; si no, va junto con el de F-052.
- **Pendientes del humano** (2026-09-24 y anteriores): meter un albarán por producción; decidir si se versionan los
  libros de `evals/ground_truth/`; MANUAL arrastradas de F-002 (liberan el merge de F-003), F-019 y F-027;
  reconciliar F-003 y F-004 antes de arrancarlas; histórico mal valorado en BBDD (sin backfill, se sanea
  revalorando desde sv4); actualizar los otros proyectos al arnés vigente; `mutacion_F-011.md` invalidada y
  `mutacion_F-002.md` en cuarentena (en `historico/`); un PDF versionado que incumple la norma
  (`services/albaranes-api/worker_input/0695 - Albaranes 2026.03.09-13-16.pdf`).
- **Mejoras del arnés propuestas y no aplicadas** (genéricas, irían a `arnes-base`): la caché de `init.sh` no se
  invalida cuando cambia `comun`; `PUERTA RUTAS SENSIBLES` sale `N/A` con la ficha en `blocked`; `CHECKPOINTS.md`
  no contempla la review por bloques; falso verde de `harness.cobertura --feature`; `harness.mutacion` no muta
  `in`/`not in`; avisar cuando el alcance de una feature arrastra el de otra.
- **Deudas menores**: RM2 solo dispara a 10×; marcas `[ADAPTAR]` en las specs de F-034 y F-035; ~1166 avisos de
  `ruff`; sv1-email e `infra` sin tests.

## Notas operativas (valen para cualquier sesión)

- **Los `impl_`, `review_` y `evals_` de features cerradas viven en `progress/historico/`**. Las **campañas de
  mutación NO se archivan**: F-039 las vigila por ruta fija y moverlas pone 8 tests en rojo. El porqué, en
  `progress/historico/README.md`.
- **Nada en paralelo**: dos suites a la vez tumban el proceso en Windows (`0xC0000142`). Y **una campaña de
  mutación muta el árbol principal**: mientras corra, no lanzar `init.sh` ni tests.
- **Un agente con demasiado contexto se cuelga en bucle.** Lanzar uno **nuevo y acotado** —diciéndole exactamente
  qué leer— lo resuelve y sale más barato. Un agente que se cuelga no pierde el trabajo commiteado: commit por tarea.
- **No ensuciar el árbol mientras un agente trabaja**: C5 exige árbol limpio, y tus cambios pueden colarse en el
  commit de otro.
- **Los agentes no deben usar scripts que reescriban ficheros versionados**; copias en el scratchpad.
- **Cuidado con las rutas de Windows en heredocs de Python**: `\U` de `C:\Users` se interpreta como escape unicode.
- **La máquina es compartida y se nota**: otra sesión corriendo triplica los tiempos y puede invalidar una campaña.
- **Un comando de verificación guardado en `progress/` puede caducar**: guarda también de qué depende.
- **El humano ejecuta él mismo** los `push`, los merges y las verificaciones MANUAL. Dale el comando listo para
  **PowerShell**, con `git -C <ruta>`, sin `&&` (su PowerShell 5.1 da error de parser) y con el criterio de verde.

## F-054 · lo que queda (cerrada el 2026-10-02)

- Informes archivados: `progress/historico/impl_F-054.md` y `progress/historico/review_F-054.md`; la campaña
  sigue en `progress/mutacion_F-054.md` (19/20 muertos, 1 equivalente). Resumen y decisiones en `history.md`.
- Al humano: merge de `feature/F-054-correo-adjunto-encadenado` a `dev`; luego, desde `infra/`,
  `.\deploy.ps1 -Only sv1` y `.\check_deploy.ps1`; después la T12 de abajo.
- Log de R23 nuevo en sv1: `sin adjuntos elegibles: ni directos ni correos adjuntos (total=N) → Errores` (sigue
  conteniendo «sin adjuntos elegibles», el texto que busca la T12 en los logs viejos).
- Al leer los logs de la T12 (O1 de la review): unos bytes basura no vacíos en un correo adjunto se leen como
  `text/plain` y salen como WARNING «sin ningun documento interior valido», no como ERROR «ilegible»; el
  destino es el mismo.

### PENDIENTE DEL HUMANO · verificación MANUAL de F-054 (T12, tras merge a `dev` y despliegue de sv1)

No bloquea el `done`. Procedimiento (design §10 y `tasks.md` T12):

1. Desde `infra/`: `.\deploy.ps1 -Only sv1` y `.\check_deploy.ps1`.
2. En Outlook, carpeta `Errores` del buzón de albaranes: localizar los correos cuyo único adjunto es un correo
   (icono de sobre; en los logs viejos de sv1: «sin adjuntos elegibles»).
3. Mover **uno** a la carpeta origen y **marcarlo como no leído** (el filtro de sv1 es `isRead eq false`).
4. Esperar un ciclo de polling y comprobar en los logs de la Container App de sv1: la línea INFO
   `att=<id> documentos interiores: N PDF y M imagen(es)`, el `intake encolado` de cada página y
   `movido a Procesados`; y el albarán en el front (sv4).
5. Si cuadra, repetir con el resto por tandas pequeñas.
6. Los mixtos que están en `Procesados` con el interior perdido **no** se mueven en bloque (re-ingerirían los
   PDF directos con otra `correlation_key`): uno a uno, si el humano lo decide.
7. Anotar aquí el resultado.
