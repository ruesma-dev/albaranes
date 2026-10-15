Revisión incremental desde `550d3bb` (pasada 2): delta `550d3bb..b5d7149` (`e7b9c3e`…`b5d7149`, 13 commits)
<!-- progress/review_F-053_fase1_pasada2.md -->
# Review F-053 · fase 1 · pasada 2 (H1–H3, O1, D1–D4) · reviewer, 2026-10-07

**Veredicto: CHANGES_REQUESTED.** H1, H2, H3 y O1 están bien resueltos, y también D2, 1a y 1c: mis controles negativos
los cazan todos. Pero **D1 no cierra la carrera con sv9 que dice cerrar** (H4). Lo reproduje en un PostgreSQL 16
efímero y local, levantado en el scratchpad y borrado al terminar: si sv3 consulta mientras sv9 tiene abierta la
transacción de `reclamar`, ve el alta como `None`, borra el merge y el `ON DELETE CASCADE` se lleva el alta `en_curso`.
Es justo lo que el humano pidió evitar con D1, y el arreglo es pequeño. Lo aprobado en la pasada 1 (hasta `86ae0ac`)
queda dado por bueno; `86ae0ac..550d3bb` solo contiene la review.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura ≥ 80 % y mutación con cero
supervivientes. En esta review intermedia no se exigen `init.sh` (sv4 no tiene venv en el worktree; decisión del humano
en F-049) ni la mutación (es T25).

## Verificación ejecutada (no copiada del informe)

- **Entorno.** `.venv` del árbol principal, sin tocarlo. Con `PYTHONPATH` a la comun del worktree, `ruesma_comun` se
  importa de `albaranes-F-053\services\albaranes-comun` (comprobado; sin él se importaría la del árbol principal).
- **Suites, una tras otra y bajo `coverage`:** sv9 **448 passed** (42 s) · comun **375** (120 s) · sv3 **477** (45 s) ·
  sv6 **289** (24 s) · raíz **1083** (552 s). Coinciden con el informe.
- **Puertas.** `python -m harness.cobertura --base dev --config harness/rigor.json` → `PUERTA COBERTURA: 96.2% de 1477
  líneas cambiadas cubiertas (1421/1477, umbral 80%, nivel critico)`. `harness.tamano --feature F-053`: 150/150 y
  250/250. `harness.rutas_sensibles --puerta --base dev` → `N/A (F-053 no toca ninguna ruta sensible declarada)`.
- **Lint.** `ruff check .` limpio en sv9; en sv3, cada fichero tocado tiene el mismo número de faltas en `550d3bb` y en
  HEAD.
- **sigrid-api `dev` (`838a94a`), en SOLO LECTURA con `git show`.** `concepto_grafico_models.py` y
  `albaran_compra_models.py` no cambian desde `13fd99d`.
- **Árbol limpio al terminar**, con cada control restaurado byte a byte (ver «Automejora» 2).

## Puntos de la pasada 1 y decisiones del humano

- **H1 [x].** Repasé los otros caminos de sv9 por los que podría salir un secreto y ninguno lo hace:
  - la clave de sigrid-api va solo en la cabecera `x-functions-key` y `__repr__` no la incluye; los reintentos
    registran solo el tipo de la excepción, y `SigridLecturaError` lleva el `repr` de httpx, sin cabeceras;
  - no se registran cuerpos de respuesta ni `Settings`;
  - `database_url` usa `quote_plus`, y con URLs malformadas (SQLAlchemy 2.0.52) el `repr` sale `u:***@` y los errores
    no contienen la contraseña; los errores del token de Graph llevan el cuerpo de Azure AD, nunca el `client_secret`.
- **H2 [x].** `GraficoPreview` (`ide_documental`, `ide_negocio`, sin `ide`) es igual en `dev` y en `13fd99d`. La
  respuesta idempotente devuelve solo `ide_negocio` (= `enlace.gra`, use case :394–:406). Los tests usan la forma real,
  con valores distintos en los dos campos.
- **H3 [x].** Se añadió `branch` y se regeneró `BACKLOG.md`; la puerta de rutas sensibles ya resuelve la feature.
- **O1 [x].** Rehíce el cálculo: 3 × 183 s (sigrid-api con reintentos) + 240 s (grabación) + 380 s (token de Graph) +
  240 s (cuatro peticiones de Graph) = **1409 s**. Con 300 s de margen y redondeado al minuto, **1740 s**. Comprobé el
  modo `site_path` y el camino hasta `ConsumidorCola.visibility_timeout`. Supone que cada intento termina dentro de su
  timeout, aunque httpx lo aplica por operación; está escrito como supuesto y lo acepto.
- **D2 / R46 [x].** Solo cuentan las líneas a registrar, se normaliza con `_texto` y una casada sin código no cuenta;
  `revisar` sin llamar a sigrid-api; WARNING `ANOMALIA` con documento, línea y los dos contratos, sin importes, también
  con `no_admitido`; la medición solo lee la BBDD.
- **D4 [x].** sv4 no se toca. **1a [x].** `run` mira el alta antes de nada: devuelve `duplicate=True` sin reescribir, sin enriquecer y sin revalorar,
  incluso con `force_refetch`.
- **1c [x].** La mirada va antes de `get_by_sha256` y de `upload` (los tests comprueban el orden `buscar → upload →
  save`).
- **D1 [ ] → H4.**

## Seguridad: la llave de escritura (todo el diff `dev...HEAD`)

- **Dos únicas escrituras, las dos tras la llave:** `alta_albaran(commit=True)` (`alta_sigrid_service.py:282`, tras el
  corte `ModoAlta.SIMULACION` de :273–:278) y `concepto-grafico` (solo con `ModoAlta.REAL`, :329 y :390). `REAL` exige
  el literal `true` (`settings.py:159`); mi control C4 (`strip().lower()`) lo cazan 4 tests.
- **Ningún test ni script llama a sigrid-api real:** `MockTransport` o fakes con `http://sigrid.invalid`, `_settings`
  con `_env_file=None`, `main()` con `ejecutar_worker` parcheado, sin `.env` de sv9 en ningún árbol; la medición no
  abre HTTP.

## Controles negativos propios (suite entera del servicio tras cada uno)

C1 H1 vuelve `input_value` al log: **4 failed** · C2 O1 el peor caso sin el adjunto: **2** · C3 O1
`GRAPH_PETICIONES_DESCARGA = 1`: **2** · C4 llave con `strip().lower()`: **4** · C5 R46 ANOMALIA sin el contrato de la
valoración: **2** · C6 R46 sin `_texto`: **1** · C7 R45 sin `rollback`: **3** · C8 1a `duplicate=False`: **4** · C10 1a
el conservado activo se revalora: **3** · **C9 1c `AND m.is_active` en `_SQL_ALTAS_DEL_SHA`: 0 failed (sobrevive)**.
C9 sobrevive porque la sesión doble ignora el SQL: ningún test comprueba la parte «o en la papelera» de R45.

## Hallazgos

**H4 · MEDIA · R45: `FOR UPDATE OF m` con `LEFT JOIN` en la MISMA sentencia no ve el alta que sv9 acaba de confirmar**
(`sqlalchemy_albaran_repository.py:57-63` y `:2110-2116`). En READ COMMITTED la instantánea se toma al empezar la
sentencia. Si sv3 espera el cerrojo de `m` y sv9 confirma sin modificar `m`, PostgreSQL no reevalúa la fila, y `a` se
sigue leyendo de la instantánea vieja.

Reproducido en PostgreSQL 16.4 con la DDL real (`_PHASE2_DDL`) y la sentencia importada del módulo: (1) sv9 hace
`FOR UPDATE OF m` e inserta `en_curso` sin confirmar; (2) sv3 lanza `_SQL_ALTAS_DEL_SHA` y espera; (3) sv9 confirma;
(4) sv3 recibe `estado: None`. Una **segunda** sentencia lanzada ya con el cerrojo sí ve `en_curso`.

Consecuencia: `save` borra el merge y el CASCADE se lleva el alta mientras sv9 sigue hacia la grabación. La ventana es
de milisegundos y el FK suele hacer fallar el `_guardar` de sv9, pero no siempre: puede quedar un albarán grabado en
Sigrid sin rastro, que es justo el caso D1. No se cumple lo que prometen el design §4 («`save` repite con `FOR UPDATE
OF m`») ni el informe («cierra la carrera»). El test solo comprueba que el texto contiene `FOR UPDATE`.

**O2 · para el humano, no bloquea.** `POST /v1/albaranes/persist` (`app.py:397-401`) escribe `review_phase2_*` y
`source_phase` sobre un conservado (hallazgo 2 del §8). Nadie lo llama en el código (`Service3HttpClient` de sv1 no se
instancia): solo es alcanzable con un curl manual. `reenrich_by_merge_id` (mensajes de sv4) depende de R25/T19.

**O3 · observación.** Los commits se titulan `F-053 (review fase 1): …` y no `F-053 Tn:`. La correspondencia con
T31–T39 está en el informe (§1 y §8) y lo acepto así; en la pasada 3, `F-053 T40:`.

## Cambios requeridos

1. **H4.** En `_conservar_por_alta` (las dos miradas), dos sentencias: primero `SELECT id FROM
   albaran_documents_merge WHERE source_sha256 = :sha FOR UPDATE`; después, ya con el cerrojo, `SELECT document_id,
   estado, sigrid_cod FROM albaran_altas_sigrid WHERE document_id = ANY(:ids)`, con instantánea nueva. Motivo en una
   línea del design §4.
2. **Tests de H4** en `test_f053_r45_reingreso_con_alta.py`: el cerrojo de los merges va en una sentencia ANTERIOR y
   distinta a la lectura de `albaran_altas_sigrid`. Control negativo: volver a la sentencia única ⇒ falla. Fase RED
   con su salida real.
3. **C9.** Un test que fije que la consulta del alta NO filtra por `is_active` (R45 incluye la papelera, D3). Control
   negativo: añadir `AND m.is_active` ⇒ falla.
4. **MANUAL en T26/T27.** La prueba de dos sesiones en el PostgreSQL local (la secuencia de H4), con su comando.

## Checkpoints (alcance de la pasada)

- **C1 · N/A justificado.** `init.sh` no se exige en esta fase intermedia: lo sustituyen las 5 suites y la cobertura,
  y se exige en T30.
- **C2 · [x]** Solo F-053 está `in_progress`, con `branch`; `current.md` al día.
- **C3 · [x]** Hexagonal: puerto abstracto, implementación en infraestructura, comun pura. Primera línea [x]. Sin prints
  [x]. Sin secretos [x] (H1).
- **C3 bis · N/A.** No toca `docs/referencia/`.
- **C4 · [ ]** Los tests de R45 no cubren la carrera que pretende cerrar ni la papelera a nivel de SQL (H4, C9). El
  resto [x], según la tabla de abajo.
- **C4 bis · [x]** `rigor` declarado, fase RED con su salida real (informe §4 y §8), cobertura 96,2 % medida por mí y
  sección «Evidencias» presente. Mutación, RM1–RM6 y supervivientes: N/A justificado, porque la campaña es T25.
- **C4 ter · N/A.** El diff no toca rutas sensibles.
- **C5 · [x]** T31–T39 `[x]` en `tasks.md` y sin temporales trackeados. Commits: ver O3.

## Cobertura requisito → tests (delta)

| Requisito | Tests |
|---|---|
| R35 (H1) | `test_f053_r35_configuracion_invalida*` y `test_f053_r35_secreto_solo*` ×3 |
| R22 (H2) | `test_f053_r22_adjunto_*` ×4 |
| O1 | `test_f053_o1_*` ×3 |
| R46 | `test_f053_r46_*` (×10) y `test_f053_medicion*` de sv3 (×5) |
| R45 | `test_f053_r45_*` (sv3 ×28, comun ×1, sv9 ×1) |

## Automejora (propuesta, no aplicada)

1. **`CHECKPOINTS.md` C4, para cualquier proyecto (`arnes-base`).** Un requisito de concurrencia no se da por cubierto
   con un test sobre el texto del SQL: exige una prueba de dos sesiones en un motor real, aunque sea MANUAL.
2. **Para este reviewer.** Con `core.autocrlf=true`, `git checkout --` devuelve en CRLF un fichero que estaba en LF:
   `git diff` sale limpio, pero los bytes cambian. Hay que restaurar escribiendo los bytes originales. Me pasó en C4
   con `settings.py`: lo devolví a LF desde `HEAD` y lo verifiqué.
