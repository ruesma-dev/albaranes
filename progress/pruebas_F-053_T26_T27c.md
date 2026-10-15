<!-- progress/pruebas_F-053_T26_T27c.md -->
# F-053 · MANUAL T26, T27, T27b y T27c ejecutadas en LOCAL (2026-10-15)

Delegadas por el humano («Sí, hazlas tú», 2026-10-15). Árbol principal, rama `dev`, HEAD `ed6b260` (F-053 v8
fusionada). **Sin tocar código, ni `.env`, ni commits en `dev`** (este informe queda sin versionar).

| Tarea | Resultado | Una línea |
|---|---|---|
| T26 | **VERDE** (en la 2.ª pasada; la 1.ª, ROJA por datos de prueba, ver §2.3) | 5 `simulado`, `ya_en_sigrid`, `revisar`/`signo_incoherente`; sin valorar rechazado; desaprobar el simulado, sí |
| T27 | **VERDE** | 10 escrituras/publicaciones rechazadas con el aviso de R25; filas y colas idénticas antes/después |
| T27b | **VERDE** | la mirada de sv3 esperó 8,2 s al cerrojo y devolvió `conservado_por_alta=True` |
| T27c | **VERDE** | «Borrar» esperó 8,3 s; tras el COMMIT, aviso de R25 y `is_active = True` |

## 1. Entorno (todo LOCAL)

- **PostgreSQL local** (`localhost:5432`, BBDD `albaranes`; ya estaba arrancado y se queda arrancado). Copia previa
  con `pg_dump -Fc` en el scratchpad: `.../scratchpad/t26/albaranes_local_antes_T26.dump`.
- **Azurite** (`azurite --silent --skipApiVersionCheck --location C:\azurite`), colas `q-*` vacías al empezar.
- **Solo sv4 y sv9**, lanzados como procesos en segundo plano (no `arrancar_local.ps1 -SinSv1`). Desviación
  justificada: ese script levanta también sv3 (sube a **SharePoint real** al consumir `q-persistencia`), sv6/sv5
  (IA real) y sv2; ninguno hace falta para estas cuatro tareas y una publicación indebida de sv4 habría acabado
  en SharePoint. sv1 nunca se arrancó.
- **sv4**: su `.venv` y su `.env` (PG local, colas = Azurite, comprobado `devstoreaccount1`) más, en el entorno del
  proceso, `ALTA_SIGRID_DESDE_UTC=2026-10-15T14:57:01Z` y `GRAPH_KEY` inservible.
- **sv9**: no tiene `.env` (ni venv): `.venv` raíz y entorno del proceso armado por un script del scratchpad
  (`entorno.py`) con los `PG_*`, `COLAS_CONNECTION_STRING` y `SIGRID_API_*` del `.env` de sv4 (leídos, no
  impresos, no copiados a ningún fichero), `ALTA_SIGRID_DESDE_UTC` (la misma), `ALTA_SIGRID_USUARIO_RESPALDO=pgris`,
  `GRAPH_KEY` y `SHAREPOINT_DRIVE_ID` inservibles a propósito (sin ellos no arranca; en simulación no se usan) y
  **`ALTA_SIGRID_COMMIT` sin poner** (el script lo quita del entorno y lo comprueba con `assert`).
  Log de arranque: `modo=simulacion desde=2026-10-15 14:57:01+00:00 ... avisos_bloqueantes=['producto_sin_historico']`.
- **sigrid-api**: la desplegada (`SIGRID_API_BASE_URL` del `.env` de sv4; URL omitida aquí), solo con
  `sql/read` y la previa `sigrid/albaran` `commit=false`. `grep -c 'commit=True' sv9.out` ⇒ **0**.
- **«Pulsar» en `http://localhost:8004`** = peticiones HTTP a las mismas rutas de sv4 (leídas en
  `interface_adapters/web/app.py`): `POST /documents/{id}/approve` (listado, `approved_by=pgris@ruesma.es`),
  `PUT /api/documents/{id}` («Guardar» / «Guardar y aprobar»), `POST /documents/{id}/unapprove` (con
  `volver=ficha` y sin él), `POST /documents/{id}/delete`, `POST /documents/bulk-delete`, `POST /api/undo`,
  `POST /api/documents/{id}/valuate`, `POST .../re-fetch-contratos`, `PATCH .../lines/{lv}/conciliacion/campos`,
  `POST .../lines/by-merge/{ml}/conciliacion` y `POST .../lineas-valoradas/{lv}/producto-sigrid`. No se usó el
  navegador del humano.

## 2. T26 — siete aprobaciones en simulación

### 2.1 Datos de prueba (copias locales de albaranes reales; todo revertido al final, §6)

Lectura previa R14 (`sql/read`, solo lectura): 10 de los 13 documentos activos ya están en Sigrid con su número
real. Por eso a los que debían llegar a la previa se les cambió el número por uno de prueba (`T26-x-…`) desde sv4.

| Caso | Documento | Preparación (vía sv4 salvo donde se dice) | Aprobado por |
|---|---|---|---|
| A todo vinculado | `32145622` | estaba aprobado antes de DESDE: desaprobar; fecha `2025-09-12`→`2026-09-12` (si no, `fecha_no_plausible`); nº `T26-A-250012` | ficha (PUT) |
| B sin vincular con partida | `03643550` | nº `T26-B-225225` | listado |
| C QA9999 + XA9999 | `20bc59dd` | **SQL directo**: `contexto_linea_json` de la línea 602 = `{"tipo_familia":"alquiler_maquinaria"}` (no hay ruta en sv4 para la familia); producto de la lv 999 = `XA9999` (ruta R41); nº `T26-C-2137569` | ficha (PUT) |
| D línea negativa | `e2c8280f` | lv 985 cantidad `-90` (importe `-3755.7`); nº `T26-D-2674163` | listado |
| E sin contrato, a mano, sin partida | `773a5620` | fecha `2024-11-05`→`2026-10-05`; conciliación «Nueva» sobre la línea 591, precio 15 ⇒ valoración `manual`, importe 135, partida vacía | ficha (PUT) |
| F nº ya en Sigrid | `8759f7fd` | ninguna (nº `1229` = `AC26/16411`) | listado |
| G descuento | `9cfc855c` | lv 984 precio `-15.43` (cantidad 29960 > 0, importe `-462.28`) | listado |
| H sin valorar | `773a5620` antes de E | ninguna | los dos caminos |

### 2.2 Sin valorar (H): rechazado por los dos caminos

```
POST /documents/773a5620-.../approve  HTTP 303 Location: No se puede aprobar un albarán sin valorar
PUT  /api/documents/773a5620-...      HTTP 409 {"detail":"No se puede aprobar un albarán sin valorar"}
  E approved = False ; altas de E = 0 ; q-feedback aprox_mensajes = 0
```

### 2.3 Primera pasada: **ROJO por los datos de prueba, no por el código**

```
32145622 simulado      AC26/29670 []
20bc59dd no_admitido   lineas_no_validas + partida_no_encontrada ×5 ('36.01', 'CI.04.18')
773a5620 simulado      AC26/29670 []
03643550 no_admitido   lineas_no_validas + partida_no_encontrada ('RJ.14.01.02.02')
e2c8280f no_admitido   lineas_no_validas + partida_no_encontrada ('11.10.02.01')
8759f7fd ya_en_sigrid  AC26/16411 [alta_a_mano "AC26/16411 (con.ide 2777427)"]
9cfc855c revisar       [signo_incoherente "cantidad 29960.0, importe -462.28", referencia_linea 984]
```

Causa: las partidas guardadas en esas copias locales **no existen en la obra en Sigrid** (lo dice sigrid-api:
«La obra no tiene ninguna partida 'X'»). Comprobado con la ruta de solo lectura de sv4 `GET /api/sigrid/partidas`:
obra `0696` (2638 partidas hoja) no tiene `RJ.14.01.02.02`, `36.01` ni `CI.04.18`; obra `0695` no tiene
`11.10.02.01` (sí `03.03.07`). sv9 hizo lo que pide design §2 (`partida_no_encontrada` ⇒ `no_admitido`).

Corrección como lo haría el administrativo: «Desaprobar para editar» (HTTP 303 «Documento desaprobado: ya se puede
editar», `no_admitido` no bloquea), partida corregida en la fila (B `P4.09.25`, C las cinco `CI.4.20`, D
`03.03.07`) y aprobar de nuevo (C por la ficha, B y D por el listado). sv9 los reprocesó (`intentos=2`).

### 2.4 Segunda pasada: SELECT del criterio — **VERDE**

```
SELECT document_id, estado, modo, sigrid_cod, motivos_json FROM albaran_altas_sigrid;
32145622-b987-49da-ac0b-96f9e000f74b | simulado     | simulacion | AC26/29670 | []
20bc59dd-2f93-41cc-97ac-646daba47870 | simulado     | simulacion | AC26/29670 | []
773a5620-5853-4909-911d-add66e064b7a | simulado     | simulacion | AC26/29670 | []
03643550-e002-4836-af2a-32c619efd79d | simulado     | simulacion | AC26/29670 | []
e2c8280f-6ac8-45b1-9859-142c4bfe77d3 | simulado     | simulacion | AC26/29670 | []
8759f7fd-b929-443a-b526-a1946289fb9f | ya_en_sigrid | simulacion | AC26/16411 | [{"codigo": "alta_a_mano", "detalle": "AC26/16411 (con.ide 2777427)"}]
9cfc855c-5d5e-4029-b4e5-89fe5a459c41 | revisar      | simulacion |            | [{"codigo": "signo_incoherente", "detalle": "cantidad 29960.0, importe -462.28", "referencia_linea": "984"}]
```

Lo pedido en la previa (`peticion_json`; línea = `ctrpro_ide/producto/partida/cantidad/precio`) y lo devuelto:

| Doc | `usu` | Líneas pedidas | Totales de la previa | Avisos |
|---|---|---|---|---|
| A | pgris | `214780/-/(sin)/8/89.3 ; 214825/-/(sin)/8/3.0 ; 214809/-/(sin)/8/3.0` (3 vinculadas; lv 1044/1045 con importe 0 fuera, R13) | 762,40 base, 3 vinculadas | `cod_provisional`, `sin_partida_en_linea_con_partida`×3, `supera_pendiente`×2 |
| C | pgris | `QA9999/CI.4.20/108/0.325833 ; XA9999/CI.4.20/10/2.053 ; MA9999 ×3` | 139,66, 0 vinculadas | `cod_provisional`, `iva_de_otro_proveedor`×2 |
| E | pgris | `MA9999/(sin partida)/9/15.0`, sin `cod_contrato` | 135,00 | `cod_provisional` |
| B | pgris | `MA9999/P4.09.25/7/70.0` | 490,00 | `cod_provisional` |
| D | pgris | `MA9999/03.03.07/-90/41.73` (cantidad con el signo, precio positivo) | −3755,70 | `cod_provisional` |

- Productos: QA9999 por la familia de la línea, XA9999 el elegido en sv4, MA9999 el `*`. Signo: D manda cantidad
  negativa y precio |importe|/|cantidad| (R12). Sin partida: A y E sin clave de partida.
- `ya_en_sigrid` (F) sin previa: solo dos `sql/read` (dbo.usu y R14).
- `revisar` (G) **sin previa ni R14**: la única llamada fue `POST /api/sql/read` de `dbo.usu` (v8, R47; design §5
  paso 3 «sin llamar a sigrid-api salvo `dbo.usu`»). El criterio dice «sin llamada a sigrid-api»: se cumple en lo
  que importa (ni R14 ni `sigrid/albaran`); lo anoto por si el humano lo quiere literal.
- R47: los 6 que construyen petición llevan `usu=pgris` «(quien aprobó)», por los dos caminos (ficha y listado).
- Ficha de C (`GET /documents/20bc59dd…`): panel «Modo: Simulación · se habría creado como AC26/29670 (código
  provisional de la previa) · Intentos: 2 · Usuario de Sigrid: pgris», sin «(respaldo)»; QA9999/XA9999/MA9999 en
  la tabla de líneas (R40).

### 2.5 Desaprobar el primero (no bloqueante)

```
POST /documents/32145622-.../unapprove (volver=ficha)  HTTP 303 Location: Documento desaprobado: ya se puede editar
SELECT approved, estado ...  ⇒ False | simulado
```

## 3. T27 — cerrojo real con un alta `registrado` puesta a mano

`UPDATE albaran_altas_sigrid SET estado='registrado', modo='real', sigrid_cod='AC26/T27PRB', adjunto_estado='colgado'
WHERE document_id='20bc59dd-…'` (BBDD local; el documento, aprobado, con 9 entradas de deshacer y líneas sin vincular).
Foto JSON de merge, líneas, valoración, líneas valoradas, derivadas, alta e ids de `undo_log` antes y después.

```
1a Guardar (PUT approved=true, nota nueva)   HTTP 409 {"detail":"Registrado en Sigrid como AC26/T27PRB: corrígelo en Sigrid y pulsa \"Ya lo he anulado en Sigrid\""}
1b Guardar (PUT approved=false)              HTTP 409 (mismo aviso)
2a Desaprobar (ficha)                        HTTP 303 Location: Registrado en Sigrid como AC26/T27PRB: corrígelo en Sigrid y pulsa "Ya lo he anulado en Sigrid"
2b Desaprobar (listado)                      HTTP 303 (mismo aviso)
3  Deshacer                                  HTTP 409 {"ok":false,"error":"Registrado en Sigrid como AC26/T27PRB: ..."}
4a Borrar                                    HTTP 303 (mismo aviso)
4b Borrado múltiple (R27)                    HTTP 303 Location: 0 albarán(es) movidos a la papelera; 1 saltado(s) por estar registrados en Sigrid (o con el alta en curso)
5  Revalorar                                 HTTP 409 (mismo aviso)
5b Volver a buscar contratos                 HTTP 409 (mismo aviso)
6  Cambiar producto lv 1000 → XA9999         HTTP 409 (mismo aviso)
6b Editar fila (cantidad) lv 1000            HTTP 409 (mismo aviso)

sha256 t27_antes.json   = 7a78e6c1…bdbb6d27
sha256 t27_despues.json = 7a78e6c1…bdbb6d27   (cmp: IDÉNTICAS)
q-valoracion = 0, q-persistencia = 0, q-feedback = 0 mensajes después
```

Todas por R25 (el aviso de F-065 «Albarán aprobado: desapruébalo para editar» no llegó a salir: el alta se
comprueba antes). **VERDE.**

## 4. T27b — carrera sv9 ↔ sv3 (R45, H4)

Documento sin alta `cfd43549-6461-4726-bb34-b4d20bc1d373`, SHA `0733e3f3…5b34a0` (único merge con ese hash).
Terminal B = el script de `tasks.md` con una sola diferencia: espera un fichero-bandera en vez de `input()` (no
hay consola); árbol principal (`services/albaranes-persistencia` de `dev`), no el worktree `albaranes-F-053`.
Terminal A = Python con psycopg y transacción explícita (mismas sentencias que el bloque SQL de `tasks.md`).

```
17:13:23 B: DDL aplicado; LISTO (espero la bandera de A)
17:13:40 A: BEGIN ; SELECT ... FOR UPDATE -> [('cfd43549-…',)] ; INSERT en_curso hecho, SIN COMMIT
17:13:40 B: Mirando el alta: debe quedarse esperando hasta el COMMIT de A...
17:13:48 A: pg_stat_activity esperando cerrojo -> (47980, 'active', 'Lock', 'transactionid', 'SELECT id FROM albaran_documents_merge WHERE source_sha256 = $1 FOR UPDATE')
17:13:48 A: COMMIT
[persist][F-053 R45] reingreso del PDF sha256=0733e3f3…: el documento cfd43549-… tiene un alta en Sigrid en_curso (cod=-); se conserva como duplicado (ni se borra ni se reprocesa)
17:13:49 B: respuesta tras 8.2 s:
ExistingDocument(document_id='cfd43549-6461-4726-bb34-b4d20bc1d373', source_sha256='0733e3f3…5b34a0', sharepoint_url='<omitida>', stored_lines=8, conservado_por_alta=True)
```

Esperó y no imprimió `None`. Después: `DELETE FROM albaran_altas_sigrid WHERE document_id = 'cfd43549-…'` ⇒ `DELETE 1`.
**VERDE.**

## 5. T27c — carrera sv9 ↔ sv4 al borrar (R26)

Mismo documento (no aprobado, sin alta). A como en T27b; con la transacción abierta, `POST /documents/cfd43549-…/delete`
(= «Borrar») en otro hilo:

```
17:15:01 A: BEGIN ; FOR UPDATE -> [('cfd43549-…',)] ; INSERT en_curso, SIN COMMIT
17:15:01 sv4: POST /documents/cfd43549-…/delete lanzado (= pulsar «Borrar»)
17:15:10 A: tras 8 s, ¿ha respondido sv4? NO (sigue esperando)
17:15:10 A: pg_stat_activity esperando cerrojo -> (35632, 'Lock', 'transactionid', 'SELECT albaran_documents_merge.id FROM albaran_documents_merge WHERE …')
17:15:10 A: COMMIT
17:15:10 sv4: «Borrar» respondió tras 8.3 s: HTTP 303 -> 'Registrado en Sigrid: corrígelo en Sigrid y pulsa "Ya lo he anulado en Sigrid"'
17:15:10 is_active = True
log sv4: [alta-sigrid][R25] rechazado: document_id=cfd43549-… alta=en_curso cod=None
```

Alta de prueba borrada (`DELETE 1`); foto de las filas de `cfd43549` antes/después: idéntica. **VERDE.**

## 6. Limpieza

- Servicios parados: sv4 (pid 20740) y sv9 (pid 30896) con `Stop-Process`; Azurite (node pid 42548) parado;
  puertos 8004, 10000 y 10001 cerrados. PostgreSQL local sigue arrancado (ya lo estaba).
- Datos: `restaurar.py` devolvió los 8 documentos al estado de la foto inicial: 7 altas borradas, 20 entradas de
  `undo_log` nuevas borradas, la valoración manual de E (1 valoración, 1 línea valorada, 1 derivada) borrada, y
  merge, líneas, valoraciones, líneas valoradas y derivadas restauradas campo a campo. Foto final **idéntica** a la
  inicial (`cmp`); `SELECT count(*) FROM albaran_altas_sigrid` ⇒ 0. Únicos rastros: las secuencias de ids avanzaron
  y sv3 aplicó su DDL idempotente (`initialize` + `apply_phase2_ddl`) en T27b.
- Colas: `q-feedback` consumida por sv9; `q-valoracion`/`q-persistencia` sin mensajes. Nada salió de Azurite.
- Copia completa previa, por si acaso: `pg_dump` citado en §1.
- Scripts y salidas: `C:\Users\pgris\AppData\Local\Temp\claude\C--Users-pgris-PycharmProjects-albaranes\f36c80f5-0cba-463e-95e9-161d51e3f583\scratchpad\t26\`
  (`sv4.out`, `sv9.out`, `t26_select*.txt`, `t26_peticiones.txt`, `t27_*.json|txt`, `t27b_*.out`, `t27c.out`).
- `git status` en `dev`: sin cambios (salvo este informe y `progress/pruebas_F-051_T22_T24.md`, ajeno, sin versionar).

## 7. Para el líder / el humano

1. **T26 en la primera pasada falló por datos**: tres copias locales llevan partidas que su obra no tiene en Sigrid.
   No es un defecto de sv9/sv4 (sigrid-api lo rechaza y sv9 lo clasifica como manda design §2), pero avisa de que en
   simulación real veremos `no_admitido` `partida_no_encontrada` cuando la IA o el contrato traigan partidas que la
   obra no tiene: conviene contarlas en T28.
2. G (`revisar`) hace una `sql/read` de `dbo.usu` antes de validar (v8). Si el criterio de T26 «sin llamada a
   sigrid-api» se quiere literal, habría que retocar el enunciado de T26 (no el código).
3. Caso C forzado: la familia `alquiler_maquinaria` se puso por SQL en el contexto de una línea (no hay ruta en sv4).
4. `ALTA_SIGRID_COMMIT` nunca se puso; 0 `commit=True` en el log de sv9.
