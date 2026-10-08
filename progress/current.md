<!-- progress/current.md -->
# Trabajo en curso

**F-063 · `done` (2026-10-08)**, fusionada en `dev` con `init.sh` en verde. Pendiente del humano: desplegar solo sv3; en los merges `b1d3e179` y `401d9c00`, «Elegir proveedor» FEYMACO a mano.

**F-063 · IMPLEMENTACIÓN EN CURSO (`in_progress`, 2026-10-08, arreglo URGENTE de producción)** en la rama
`feature/F-063-cif-propio-no-es-proveedor` (worktree `../albaranes-F-063`, desde `dev` `ba72f0a`): el CIF de
Construcciones Ruesma (A81873903, el cliente) nunca es el proveedor; sv3 lo descarta y busca por nombre. Propuesta
aprobada por el humano («arregla urgente esto»). Spec en `specs/F-063-cif-propio-no-es-proveedor/`; informe en
`progress/impl_F-063.md`. Entorno: venvs del árbol principal, `PYTHONPATH` al comun del worktree y *junction*
`services/albaranes-front/.venv` → venv de sv4 del árbol principal (quitar con `cmd /c rmdir
services\albaranes-front\.venv` ANTES de `git worktree remove`). F-053 tiene sus suites en pausa mientras tanto.
- **T0–T7 hechas** (2026-10-08, un commit por tarea). Informe: `progress/impl_F-063.md`. Cobertura de lo cambiado
  96,6 % (57/59); mutación completa 14/14 muertos (`progress/mutacion_F-063.md`). Desviación justificada (§3 del
  informe): la nota usa el prefijo propio `[AVISO] CIF del cliente` (con `[AVISO] Proveedor` la borraba la misma pasada).
- **T9 (`init.sh`) sin marcar**: en el worktree da 2 KO de entorno (los de F-062: `test_f052_t19_script_arranca…` y,
  por él, la cobertura); deseleccionando solo ese test, `ENTORNO LISTO`. Repetir en el árbol principal tras fusionar.
  **T8 (MANUAL del humano)**: desplegar solo sv3 y re-procesar el albarán de FEYMACO (comandos en el informe §7).
  **Siguiente paso: review.**

**F-062 · `done` (2026-10-08)**, fusionada en `dev` (`d052106`) con `init.sh` en verde. Pendiente del humano: despliegue de solo sv3 y vigilancia T12 (comandos abajo).

> Podado el 2026-10-01 al cerrar F-052 (C2 de `progress/review_F-052.md`). El `current.md` anterior, íntegro, está
> en `progress/historico/current_2026-10-01_cierre_F-052.md`; el resumen de F-052, en `progress/history.md`.
> Aquí solo queda lo vivo. Lo que manda sobre el estado de cada feature es `harness/features.json`.

**F-053 · IMPLEMENTACIÓN, FASE 1 (`in_progress`, 2026-10-06)** en la rama `feature/F-053-alta-sigrid` (worktree
`../albaranes-F-053`): alta en Sigrid de los albaranes aprobados, servicio nuevo sv9, arranque en simulación. Spec v7,
PARADA 1 aprobada por el humano («adelante», 2026-10-06) con un cambio de orden también aprobado: la fase 1 hace T0a,
T1, T2, T2b y T3–T16 (comun, DDL de sv3 y sv6 y sv9 completo). `dev` fusionado dos veces en la rama: la segunda ya
trae **F-051** (merge `e7d7507`), así que la regla «partida final vacía = almacén» está disponible. T17 en adelante
(sv4, infra, docs, puertas) quedan fuera de esta fase. Informe de la fase: `progress/impl_F-053_fase1.md`.

**Fase 1 TERMINADA (2026-10-06, implementer)**: T0a, T1, T2, T2b y T3–T16 hechas, un commit por tarea
(`618227e`…`ca6dde7`), con fase RED y controles negativos. Suites en verde, una tras otra: comun 374, sv3 444, sv6 289,
sv9 430 (nuevo) y raíz 1083; cobertura de líneas cambiadas 96,1 % (1346/1401). Contrato citado: F-009 v8.2 `13fd99d`
(misma forma que `8a6ecab`). **Desviaciones justificadas** (detalle en el informe, §4): el DDL de
`albaran_altas_sigrid` va en `phase2_ddl._PHASE2_DDL` (lo que sv3 aplica al arrancar; `schema_contribution` lo
exporta), `main.py` en sv9 por el test de estructura, firmas de puertos ampliadas (`accion`, `referencia_externa`,
`ahora`), petición guardada en `en_curso` y reenviada tal cual al retomar un `incierto`. **Pendiente**: verificación
de T0d (`init.sh`; el worktree no tiene el venv de sv4), MANUAL T0b/T0c/T0 (comandos en el informe §8), y T17–T30.
Mutación (T25) no lanzada: es de las puertas finales.

**Fase 1 · pasada 2 HECHA (2026-10-06, implementer)** tras la review CHANGES_REQUESTED
(`progress/review_F-053_fase1.md`). Informe: `progress/impl_F-053_fase1_pasada2.md`. Commits `e7b9c3e`…`604e918`:
H1 (configuración inválida al log sin valores), H2 (`grafico.ide_negocio`), H3 (`branch` de F-053), O1 (visibilidad
de `q-feedback` 1740 s), y las decisiones del humano **D1 = R45** (sv3 no borra un merge con alta bloqueante al
reingresar su PDF) y **D2 = R46** (línea casada con otro contrato ⇒ `revisar` + WARNING `ANOMALIA`; recuento en la
medición). Spec: R45 y R46, T31–T37 `[x]`, topes 150/150 y 250/250. Suites: sv9 448, sv3 461, comun 375, raíz 1083;
cobertura 96,2 % (1409/1464). **Para el humano** (informe §3): la rama de duplicado de un documento ACTIVO sigue
re-enriqueciendo y revalorando aunque el alta esté `registrado` (R45 solo cubre el borrado); sv4 permite conciliar a
mano con una línea de otro contrato (otra fuente de R46). **Pendiente**: re-review de la pasada 2; repetir T0.

**Fase 1 · remate HECHO (2026-10-07, implementer)** con las decisiones del humano sobre esos hallazgos: **D3** (1a y
1c) «un albarán no se puede pisar»: sv3 mira el alta (`buscar_conservado_por_alta`, método nuevo del puerto) al
principio de `run`, antes de SharePoint, y un duplicado con alta bloqueante (activo o en la papelera) se devuelve sin
tocar nada; `save` conserva su mirada para la carrera con sv9. **D4** (1b): sv4 no se cambia, R46 sigue de red. Spec:
R45 reescrito, T38–T39 `[x]`, topes 150/150 y 250/250. Commits `80a3d5d`…`73d9707`. Suites: sv3 477, raíz 1083;
cobertura 96,2 % (1421/1477). Seguridad: ninguna ruta de sv9 graba sin `ALTA_SIGRID_COMMIT=true`. Informe: §8 de
`progress/impl_F-053_fase1_pasada2.md`, con tres hallazgos nuevos para el humano (carrera residual en la rama de
duplicado; la API `/persist` de sv3 escribe metadatos de fase 2 sobre un conservado; el re-fetch de sv3 depende de
T19). **Pendiente**: re-review de la pasada 2 + remate; repetir T0.

**Fase 1 · pasada 3 HECHA (2026-10-07, implementer)** tras la review CHANGES_REQUESTED de la pasada 2
(`progress/review_F-053_fase1_pasada2.md`, **H4**: la mirada de R45 en UNA sentencia no veía el alta que sv9 confirma
mientras sv3 espera el cerrojo). Commits `3963164` (T40: `_conservar_por_alta` en dos sentencias, primero el `FOR
UPDATE` de los merges y luego el alta con `ANY(:ids)`; tests de la carrera, de la papelera (C9) y sin merges) y
`538f746` (T41: design §4 con el motivo, T40 `[x]` y **T27b**, la prueba MANUAL de dos sesiones en el PostgreSQL
LOCAL, con sus comandos). Fase RED 9 failed; controles N1–N5 cazados (9, 9, 2, 2, 1). Suites: sv3 482, raíz 1083;
cobertura 96,2 % (1425/1481); topes 150/150 y 250/250. Informe: `progress/impl_F-053_fase1_pasada3.md`, con dos
observaciones para el líder (§7: el design de sv4 `_exigir_desbloqueado` repite el patrón de H4; `SQL_RECLAMAR` de
sv9 también, cubierto por el consumidor secuencial). **Pendiente**: re-review de la pasada 3; MANUAL T27b (humano).

**F-062 · IMPLEMENTACIÓN EN CURSO (`in_progress`, desde 2026-10-07)** en la rama `feature/F-062-proveedor-aplicado`
(worktree `../albaranes-F-062`): sv3 aplica el proveedor propuesto (candidato claro con contrato en la obra) antes de
buscar contratos. PARADA 1 aprobada por el humano (Q0–Q6 con la recomendación, `progress/spec_F-062.md` §4). Spec en
`specs/F-062-proveedor-aplicado/`; informe del implementer en `progress/impl_F-062.md`. Convivencia autorizada por el
humano: **F-053 sigue `in_progress` en su rama** (fase 1 aprobada) y F-062 se fusiona en `dev` antes; F-051 y F-049
están `blocked` en las suyas. Entorno del worktree: venvs del árbol principal con `PYTHONPATH` al comun del worktree;
*junction* `services/albaranes-front/.venv` → venv de sv4 del árbol principal (ignorada por git; se quita con
`cmd /c rmdir services\albaranes-front\.venv` ANTES de `git worktree remove`).
- Tarea en curso y desviaciones: sección «F-062 · estado de la implementación» (abajo, se actualiza por tarea).

### F-062 · estado de la implementación

- Arranque: `bash harness/init.sh` en verde en el worktree (2026-10-07). F-062 → `in_progress`, `BACKLOG.md` regenerado.
- **T1–T11 hechas** (2026-10-08, un commit por tarea). Informe: `progress/impl_F-062.md`. Cobertura de líneas
  cambiadas 100 % (203/203); mutación completa en serie 104/104 muertos, 0 supervivientes (`progress/mutacion_F-062.md`,
  fila añadida al inventario de F-039). Review pasada 1 hecha (abajo).
- **T13 (`init.sh`) sin marcar**: en el worktree da 2 KO, ambos de entorno (el test de abajo y, por él, la puerta de
  cobertura a 59,6 % porque `-x` corta antes de los `test_f062_*`); deseleccionando solo ese test, `ENTORNO LISTO`.
  Repetir `bash harness/init.sh` en el árbol principal tras fusionar. Pendientes del humano: T0b (opcional) y T12,
  con sus comandos en «F-062 · MANUAL del humano» (abajo).
- **Desviaciones (justificadas en `progress/impl_F-062.md` §2)**: (1) los tests de la nota de F-052
  (`test_f052_nota_proveedor.py`) también pasan a `correccion_enabled=False`, como los de D3 de F-002 (el design solo
  nombraba F-002; SALMEDINA en la 0691 es candidato claro y con la corrección encendida esos tests pasaban por el
  camino «aplicar falla»); (2) R15 también en la rama «sin candidato claro» (se retiran correcciones caducadas);
  (3) con el interruptor apagado no se retira nada ni se añade la frase del control (R12 «exactamente como antes»);
  (4) `.env.example` de sv3 documenta los tres `RED_PROVEEDOR_CORRECCION_*`.
- **KO de entorno conocido**: `test_f052_t19_script_arranca_como_script_desde_otra_carpeta` lanza el script SIN
  `PYTHONPATH` y el venv del árbol principal importa `ruesma_comun` de `../albaranes` (sin `proveedores`): falla solo
  en el worktree; en `dev`/árbol principal con comun fusionado pasa.
- **Review pasada 1 (2026-10-08): CHANGES_REQUESTED** (`progress/review_F-062.md`: H1 y M1). **H1 = opción B**
  por decisión del humano (2026-10-08): la comparación no cambia, F-062 es la red de seguridad de F-055; se
  corrigieron R3, D2, ARCHITECTURE 17, dominio §10.1 y la nota, con test que lo fija. M1: comandos abajo.
  Correcciones en `progress/impl_F-062_pasada2.md`. **Siguiente paso: review pasada 2.**

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

**F-051 · `blocked` (2026-10-06) y FUSIONADA en `dev`.** Implementación APROBADA por el reviewer (pasada 2) e `init.sh`
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

- **F-053 `in_progress`**, fase 1 terminada (bloque de arriba e informe `progress/impl_F-053_fase1.md`). Es la única
  `in_progress`. Siguiente: fase 2 (T17–T30: sv4, infra, docs, puertas). `dev` ya fusionado con F-051 y comprobadas
  sus rutas `asignar_almacen_linea_api` / `asignar_almacen_todas_api` para R25 (T19–T20); falta la verificación de
  T0d con `init.sh`. Para el líder: añadir «producto elegido» al alcance de **F-058** y corregir en F-051 R24
  «`almacen: true`» (el campo no existe en F-009).
- **F-051 `blocked`** y fusionada en `dev`: solo esperan T22–T24 (pruebas manuales del humano, aplazadas).
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
