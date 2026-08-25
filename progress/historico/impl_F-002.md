<!-- progress/impl_F-002.md -->
# F-002 · Tanda 1 — Identificación de obra y proveedor · Informe de implementación

- Rama: `feature/F-002-obra-proveedor` (12 commits, uno por tarea).
- Nivel de rigor: **estandar** (`harness/features.json`) → exige fase RED,
  cobertura del diff y campaña de mutación.
- Spec: `specs/F-002-obra-proveedor/` (requirements R1–R17, design, tasks).
- **REGLA DURA respetada: SIN DESPLIEGUE.** No se ha ejecutado `az`,
  `deploy.ps1`, `build_images.ps1`, ni se ha creado ningún secret, ni se ha
  tocado nada de Azure. Contra Sigrid, cero llamadas: los tests usan dobles.

## Qué cambió

### sv2 (`services/albaranes-api`) — la IA1 elige obra de una lista cerrada

| Fichero | Qué hace ahora |
|---|---|
| `domain/ports/obras_activas_provider.py` (nuevo) | Puerto `ObrasActivasProvider` + `ObraActiva(codigo, nombre)` inmutable. `None` = «lista no disponible», que NO es un error. |
| `infrastructure/sigrid/sigrid_api_obras_client.py` (nuevo) | Consulta de solo lectura a `sigrid-api` (`POST /api/sql/read`, `x-functions-key`, `max_rows=10000`, transporte con 1 reintento). Filtro provisional de «obra activa» (R1-bis) y dedupe de `con.cod`. Ante cualquier fallo: `None`, nunca propaga. |
| `infrastructure/sigrid/obras_activas_cache.py` (nuevo) | Caché TTL en memoria (6 h). Dentro del TTL, 1 sola llamada (R3); si al expirar no hay lista nueva, sirve la vieja antes que quedarse sin lista. |
| `config/settings.py` | Bloque `SIGRID_API_*` + `OBRAS_ACTIVAS_{ENABLED,TTL_S,MAX,COD_MIN}` y `sigrid_credentials_present`. |
| `config/prompts.yaml` (**ruta sensible**) | En `albaran_factura_es`: placeholder `{obras_activas}` bajo «Obras entre las que elegir», y reescritura de la regla `proveedor_nombre` (R4): razón social del **bloque fiscal** que acompaña al CIF; la marca del **logotipo NO es el proveedor**. Se elimina el «Puede venir en el logo», que invitaba justo al error. |
| `application/services/albaran_extraction_service.py` | `extract_phase_1` renderiza el bloque (orden ascendente por código, cap `OBRAS_ACTIVAS_MAX`, prohibición explícita de códigos fuera de la lista y permiso explícito de devolver `null`). Sin lista: nota de «no disponible». Compatibilidad: YAML sin placeholder → el bloque se appendea (mismo patrón que `{sigrid_context}` en fase 2). |
| `interface_adapters/{composition,api/app}.py` | Wiring: `ObrasActivasCacheTTL(SigridApiObrasClient(...))`. Sin credenciales → WARN y funcionalidad desactivada; el arranque NO se rompe. |

### sv3 (`services/albaranes-persistencia`) — tres redes deterministas

| Fichero | Qué hace ahora |
|---|---|
| `application/services/obra_enrichment_service.py` | **Red de obra**: obra que Sigrid no reconoce (caso 0937) o código no normalizable → `descartar_obra_no_valida` + revisión (R5/R6); obra válida → retira el aviso previo (R7). Flag `RED_OBRA_ENABLED`. |
| `application/services/header_resolver_service.py` | **Red de proveedor**: CIF que existe en `prv` → `proveedor_nombre` pasa a la razón social canónica (R8); CIF que no existe → nota-propuesta `[AVISO] Proveedor` + motivo `proveedor_cif_no_casa:<cif>` **sin sobrescribir nada** (R9), o marca sin propuesta (R10). Sin CIF, flujo previo intacto (R11). Flag `RED_PROVEEDOR_CIF_ENABLED`. |
| `application/services/fecha_guard_service.py` (nuevo) | **Guard de año**: fecha del albarán a más de `FECHA_GUARD_MAX_DIAS` (365) de la recepción → revisión (R13). Sin fecha de email, referencia = hoy UTC (R14); fecha nula o rota → no-op (R15). |
| `infrastructure/database/sqlalchemy_albaran_repository.py` | `marcar_revision_cabecera`, `descartar_obra_no_valida`, `retirar_revision_obra`, `set_merge_proveedor_nombre_canonico`, `get_merge_fechas_para_guard`. Además, la lógica de las marcas se extrajo a funciones PURAS (`anadir_motivo_revision`, `quitar_motivos_con_prefijo`, `sustituir_nota_por_prefijo`) para poder probar la idempotencia sin BBDD. |
| `interface_adapters/worker/{ports,workflow_context_adapter,persistence_worker}.py` + `main_worker.py` | **Gap R12 cerrado**: el worker reconstruye el contexto de email desde `workflow_runs.payload_json` (lo dejó sv1) y `email_received_datetime` deja de quedar NULL en modo colas. `ruesma_comun` NO se toca: se usa su API pública. |
| `application/pipelines/persist_albaran_pipeline.py` | Paso `_check_fecha_guard_safely` tras el enriquecimiento de obra en las **tres** rutas (run normal, duplicado, `reenrich_by_merge_id`). |
| `config/settings.py` | `RED_OBRA_ENABLED`, `RED_PROVEEDOR_CIF_ENABLED`, `FECHA_GUARD_ENABLED`, `FECHA_GUARD_MAX_DIAS`. Todos activos por defecto (hay test). |

Sin DDL nuevo: todas las columnas existían. `ruesma_comun`, sv1, sv4, sv5 y
sv6 no se han tocado.

## Fase RED (obligatoria en nivel `estandar`)

Los tests se escribieron ANTES del código en las cinco tareas con lógica.
Salidas reales de los fallos:

**T3 — red de obra** (`cd services/albaranes-persistencia && python -m pytest tests/test_f002_red_obra.py -q`):

```
F.FFFF...FF.............FF.                                              [100%]
FAILED tests/test_f002_red_obra.py::test_f002_r5_obra_inexistente_se_descarta_y_marca_revision
FAILED tests/test_f002_red_obra.py::test_f002_r6_codigo_no_normalizable_se_descarta[1234]
FAILED tests/test_f002_red_obra.py::test_f002_r6_codigo_no_normalizable_se_descarta[12345]
FAILED tests/test_f002_red_obra.py::test_f002_r6_codigo_no_normalizable_se_descarta[abc]
FAILED tests/test_f002_red_obra.py::test_f002_r6_codigo_no_normalizable_se_descarta[09.37]
FAILED tests/test_f002_red_obra.py::test_f002_r7_obra_validada_retira_el_aviso
FAILED tests/test_f002_red_obra.py::test_f002_r7_reproceso_de_obra_invalida_repite_el_mismo_motivo
FAILED tests/test_f002_red_obra.py::test_f002_r17_red_apagada_no_descarta_obra_inexistente
FAILED tests/test_f002_red_obra.py::test_f002_r17_red_apagada_no_retira_avisos
9 failed, 18 passed in 1.51s
```

con el detalle del que sostiene la feature:

```
E   AssertionError: assert [] == [('0937', 'ob...stente:0937')]
      Right contains one more item: ('0937', 'obra_inexistente:0937')
WARNING  [obra-enrichment] Sigrid devolvió 0 filas útiles para codigo=0937
E   TypeError: ObraEnrichmentService.__init__() got an unexpected keyword argument 'enabled_red'
```

**T4 — red de proveedor** (`python -m pytest tests/test_f002_red_proveedor.py -q`):

```
E   AssertionError: assert None == 'HORPRESOL, S.L.'
E   assert 0 == 1
E   assert 0 == 1
E   assert 0 == 1
E   TypeError: HeaderResolverService.__init__() got an unexpected keyword argument 'cif_enabled'
FAILED tests/test_f002_red_proveedor.py::test_f002_r8_cif_existente_canoniza_el_nombre
FAILED tests/test_f002_red_proveedor.py::test_f002_r9_horpresol_deja_propuesta_a_revision
FAILED tests/test_f002_red_proveedor.py::test_f002_r10_sin_candidato_marca_revision_sin_propuesta
FAILED tests/test_f002_red_proveedor.py::test_f002_r10_sin_obra_efectiva_marca_revision_sin_propuesta
FAILED tests/test_f002_red_proveedor.py::test_f002_r17_red_apagada_no_consulta_ni_marca
5 failed, 9 passed in 0.05s
```

**T5 — guard de año** (`python -m pytest tests/test_f002_fecha_guard.py -q`):

```
tests\test_f002_fecha_guard.py:15: in <module>
    from application.services.fecha_guard_service import (
E   ModuleNotFoundError: No module named 'application.services.fecha_guard_service'
ERROR tests/test_f002_fecha_guard.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.28s
```

**T6 — contexto de email** (`python -m pytest tests/test_f002_contexto_email_worker.py -q`):

```
tests\test_f002_contexto_email_worker.py:23: in <module>
    from interface_adapters.worker.workflow_context_adapter import (
E   ModuleNotFoundError: No module named 'interface_adapters.worker.workflow_context_adapter'
ERROR tests/test_f002_contexto_email_worker.py
1 error in 2.42s
```

**T7/T8 — sv2** (`cd services/albaranes-api && python -m pytest tests -q`):

```
tests\test_f002_obras_cache.py:16: in <module>
    from domain.ports.obras_activas_provider import ObraActiva
E   ModuleNotFoundError: No module named 'domain.ports.obras_activas_provider'
1 error in 1.10s
```

y, con el módulo ya creado, el prompt todavía sin tocar:

```
FAILED tests/test_f002_prompt_obras.py::test_f002_r1_el_prompt_real_tiene_el_placeholder
FAILED tests/test_f002_prompt_obras.py::test_f002_r2_sin_lista_se_pone_la_nota_de_no_disponible[None]
FAILED tests/test_f002_prompt_obras.py::test_f002_r4_el_prompt_exige_la_razon_social_del_bloque_fiscal
FAILED tests/test_f002_prompt_obras.py::test_f002_r4_el_prompt_veta_la_marca_del_logotipo
15 failed in 0.81s
```

## Decisiones de diseño (y dos desviaciones justificadas)

1. **`_score_razon_social`, simétrico y tolerante a puntuación (desviación).**
   El design decía «el mejor `_match_score` de nombre >= `min_score`». Con
   `_match_score` tal cual, el caso de referencia de R9 —«GRUPO OTTO
   HORPRESOL» leído frente a «HORPRESOL, S.L.» en el maestro— puntúa 0,33
   (un token de tres) y **no** habría generado propuesta: la spec se
   contradecía con su propio caso. Se añadió un scorer LOCAL de la red que
   (a) puntúa en los dos sentidos y se queda con el mejor —el sentido que
   describe la feature es «el nombre leído CONTIENE un proveedor con
   contrato»— y (b) trata la puntuación como separador, para que «S.L.» no
   arrastre el score a cero. Con eso, el caso de referencia da 1,0 y hay
   propuesta. **Los caminos previos del resolver siguen usando
   `_match_score` sin tocar**: cero regresión.
2. **Lógica de marcas extraída a funciones puras (desviación menor).** El
   design avisaba de que los métodos nuevos de repositorio no se podían
   probar sin BBDD. Se separó lo que tiene reglas (idempotencia del motivo,
   dedupe de la nota por prefijo, JSON histórico roto) de lo que solo tiene
   transacción. Las reglas quedan probadas; la transacción, no (ver
   supervivientes).
3. **`conftest.py` de tests con `sys.path` explícito**, no vacío como decía
   el design: un conftest vacío en `tests/` no hace importables
   `application/`, `domain/` ni `infrastructure/` cuando la suite se lanza
   desde otro directorio. El portero las ejecuta desde la raíz del servicio;
   con esto también funcionan desde la raíz del monorepo.
4. `set_merge_proveedor_nombre_canonico` delega en el
   `update_merge_proveedor_nombre` existente: mismo UPDATE, una sola
   implementación.
5. El guard de año **no retira** su nota cuando la fecha vuelve a estar en
   rango (R7 solo lo pide para obra). Queda anotado como límite consciente:
   si el revisor corrige la fecha y se reprocesa, la nota `[AVISO] Fecha`
   sigue ahí hasta que él cierre la revisión.

## Tests: qué se comprueba

- **sv3, 88 tests** (`services/albaranes-persistencia/tests/`): red de obra
  (R5, R6, R7, R16, R17), red de proveedor (R8–R11, R16, R17), guard de año
  (R13–R15, R16, R17) incluido su paso REAL por el pipeline, y contexto de
  email (R12).
- **sv2, 56 tests** (`services/albaranes-api/tests/`): bloque de obras en el
  prompt (R1: orden, cap, prohibición; R2: degradación), filtro provisional
  (R1-bis), caché TTL (R3), cliente HTTP con `httpx.Client` sustituido, y las
  reglas R4 leídas del `prompts.yaml` REAL.
- Ninguno toca red, BBDD ni LLM.

## Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | **242** raíz + **56** sv2 + **88** sv3 + comun (caché) — **todos en verde**, 0 fallos |
| **Tiempo de las suites** | raíz 46,6 s · sv2 0,6 s · sv3 1,8 s |
| **Cobertura de líneas cambiadas** | **82,1 %** (385/469), umbral 80 % → `PUERTA COBERTURA` en verde |
| **Mutación** | **108 mutantes, 95 muertos, 13 supervivientes, 0 timeouts, 54,8 s** (`python -m harness.mutacion --feature F-002 --workers 8`) → `progress/mutacion_F-002.md` |
| **Supervivientes analizados** | 13/13, ninguno en PENDIENTE |
| **Puerta de rutas sensibles** | AVISO (esperado, ver abajo) |
| `bash harness/init.sh` | **ENTORNO LISTO** |

### Campaña de mutación: de 33 supervivientes a 13

La primera pasada dejó **33** supervivientes. **20 eran huecos reales** y se
cazaron con tests nuevos (no borrando mutantes: escribiendo lo que faltaba):
comparación del TTL con un reloj que ya no arranca en cero, inmutabilidad de
`ObraActiva`, cap por defecto de 300 y guarda del cap absurdo, mapeo por
nombre de columna en vez de por posición, aviso de lista truncada, un 400 con
cuerpo válido tratado como error, respuesta sin `ok`, reintento del
transporte, umbral inclusivo (0,5 propone) y exclusivo por debajo, empate
resuelto por el primer candidato (propuesta estable entre pasadas), notas que
no escupen `None`, y «sin fuente de contexto no es un error».

Los **13 restantes están analizados uno a uno** en
`progress/mutacion_F-002.md`. En resumen:

- **7 mutantes equivalentes**: texto de mensajes de error (2), guarda
  defensiva redundante en el scorer (1) y formato de serialización JSON
  —`ensure_ascii` / `indent`— que no cambia el valor que lee sv4 (4).
- **6 huecos reales, todos en `sqlalchemy_albaran_repository.py`**, dentro de
  las transacciones PostgreSQL. **No son alcanzables por un test unitario**:
  el `SessionFactory` de sv3 CREA la base de datos al construirse y la
  columna `review_notes` ni siquiera vive en el ORM (la añade un `ALTER
  TABLE` con SQL de PostgreSQL), así que no hay forma de levantarlo sobre
  SQLite en memoria. `design.md` ya declaró este riesgo y lo compensó con
  verificación MANUAL. **El más importante es
  `review_required = True` (dos ocurrencias): es la línea de la que depende
  que algo llegue al revisor, y es el primer dato a mirar en la prueba local
  del humano.**

### Puerta de rutas sensibles: AVISO (salida esperada)

`config/prompts.yaml` de sv2 es ruta sensible, así que la puerta pide la
pasada completa de evals. Salida real de
`python -m evals.runner --con-llm --feature F-002`:

```
no se puede lanzar la pasada completa: faltan en el entorno GEMINI_API_KEY, OPENAI_API_KEY. No se ha consumido ningún caso.
```

(el arnés corre con `REQUIERE_ENV=0`, sin `.env` global). En modo
determinista sí genera informe:

```
NO_EVALUABLE · informe en progress/evals_F-002.md
VEREDICTO: NO_EVALUABLE
Motivo: no hay ningún caso en evals/fixtures/inputs/
```

Es **la salida esperada** mientras los libros de `evals/ground_truth/` estén
vacíos (decisión D5 de F-011): la puerta está declarada en `aviso` justo por
esto y **no bloquea**. La evaluación real del prompt de IA1 llegará cuando el
humano rellene los libros.

## Acciones del humano AL DESPLEGAR (nada de esto se ha ejecutado)

sv2 pasa a consumir `sigrid-api` (decisión D1). En `ca-sv2-extraccion` hacen
falta:

| Variable | Valor | Cómo |
|---|---|---|
| `SIGRID_API_BASE_URL` | el mismo que ya usa `ca-sv3-persistencia` | env var normal |
| `SIGRID_API_DATABASE` | el mismo que ya usa sv3 (`ruesma`) | env var normal |
| `SIGRID_API_FUNCTION_KEY` | **secret** con referencia a Key Vault (ya existe la de sv3) | `--secrets` + `secretref:` |
| `OBRAS_ACTIVAS_ENABLED` | `true` (default; explicitar si se quiere apagar) | opcional |
| `OBRAS_ACTIVAS_TTL_S` / `OBRAS_ACTIVAS_MAX` / `OBRAS_ACTIVAS_COD_MIN` | `21600` / `300` / `450` | opcionales, son los defaults |

En `ca-sv3-persistencia` no hace falta nada nuevo: los cuatro flags
(`RED_OBRA_ENABLED`, `RED_PROVEEDOR_CIF_ENABLED`, `FECHA_GUARD_ENABLED`,
`FECHA_GUARD_MAX_DIAS`) vienen activos por defecto.

**T9 queda pendiente-de-despliegue**: `azure-apps/albaranes.md` describe lo
que HAY desplegado; escribir allí que sv2 consume sigrid-api antes de que el
secret exista dejaría el documento mintiendo. Se actualiza en el mismo
trabajo en que el humano despliegue.

**Nota sobre T10**: `services/albaranes-api/.gitignore` ignora `*.example`,
así que el `.env.example` de sv2 se ha actualizado **en disco pero no
aparece en el diff**. Parece un descuido de ese `.gitignore` (un
`.env.example` está para versionarse); no lo he cambiado por mi cuenta.

## Verificaciones MANUAL del humano (T12) — todas en LOCAL, solo lectura

Pipeline local con Azurite según `infra/docs/levantar-pipeline-local.md`; PG
local; `sigrid-api` en solo lectura (túnel `127.0.0.1:11433` si aplica).
Antes de nada, en el `.env` de sv2: `SIGRID_API_BASE_URL`,
`SIGRID_API_FUNCTION_KEY` y `SIGRID_API_DATABASE` (sin ellas, la lista de
obras no se inyecta y verás el WARN del wiring).

1. **Obra inventada (caso 0937).** Reprocesar el albarán. En
   `albaran_documents_merge`:
   ```sql
   SELECT obra_codigo, obra_codigo_origen, review_required,
          review_reasons_json, review_notes
   FROM albaran_documents_merge WHERE id = '<merge_id>';
   ```
   Esperado: `obra_codigo` y `obra_codigo_origen` **NULL**, `review_required`
   **true**, motivo `obra_inexistente:0937`, nota que empieza por
   `[AVISO] Obra`. `obra_nombre`/`obra_direccion` leídos se conservan.
   **Segunda parte (R7)**: corregir la obra en el portal y pulsar «Guardar y
   volver a buscar» → la nota `[AVISO] Obra` y los motivos `obra_*` deben
   desaparecer (`review_required` puede seguir a true si hay otros motivos).
2. **HORPRESOL.** Albarán con CIF que no existe en `prv` y nombre «GRUPO OTTO
   HORPRESOL». Esperado: `proveedor_cif` y `proveedor_nombre` **sin tocar**,
   motivo `proveedor_cif_no_casa:<cif>` y nota `[AVISO] Proveedor` con el CIF
   y la razón social del candidato con contrato en la obra.
   Contraprueba (R8): un albarán con CIF que SÍ existe → `proveedor_nombre`
   debe quedar con la razón social de `prv.raz`.
3. **Fecha de 2023 en correo de 2026.** Esperado: motivo
   `fecha_albaran_fuera_de_rango:2023-xx-xx` y nota `[AVISO] Fecha`.
4. **`email_received_datetime` (R12).** Procesar por COLAS (no por la API) y
   comprobar que la columna deja de ser NULL:
   ```sql
   SELECT email_id, email_sender, email_received_datetime
   FROM albaran_documents_merge ORDER BY created_at_utc DESC LIMIT 5;
   ```
5. **Nº real de obras tras el filtro provisional `>0450`.** En el log de sv2
   al arrancar la primera extracción:
   `[obras-activas][sigrid-client] obras: N filas -> M codigos unicos -> K
   activas (cod_min=450)`. Anotar K: es el dato para calibrar
   `OBRAS_ACTIVAS_MAX` (hoy 300; si K > 300 el prompt se está recortando).
   Comprobar también que NO aparece el aviso de «lista PUEDE estar truncada».

Estas cinco verificaciones son las que cubren los 6 supervivientes de
mutación del repositorio: **son la prueba de que las escrituras a BBDD hacen
lo que los tests unitarios solo pueden comprobar con dobles.**

## Qué queda fuera / qué falta

- **Fuera de alcance por la spec**: `ruesma_comun`, el scoring de confianza,
  el `HeaderGroundingService` y el endpoint del difunto sv7, los prompts de
  fase 2, sv1/sv4/sv5/sv6, y cualquier DDL.
- **Falta (del humano)**: las 5 verificaciones MANUAL de arriba; el
  despliegue con sus variables y el secret; la actualización de
  `azure-apps/albaranes.md` en ese mismo trabajo; y decidir cuándo negocio
  define el criterio real de «obra activa» para retirar el corte provisional
  `>0450` (`OBRAS_ACTIVAS_COD_MIN=0`).
- **Falta (del sistema)**: los libros de `evals/ground_truth/` siguen vacíos,
  así que el cambio del prompt de IA1 no está evaluado por evals. Es la razón
  de que la puerta de rutas sensibles esté en `aviso` y no en `bloqueo`.
