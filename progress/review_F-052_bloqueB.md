Revisión completa (pasada 1) del Bloque B: `git diff f766178..804693e` (lo aprobado del Bloque A, hasta f766178, queda dado por bueno)

# F-052 · Review PARCIAL del Bloque B (T7–T10)

- **Veredicto del bloque:** APROBADO. No es veredicto de cierre de F-052.
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`): fase RED, cobertura
  ≥ 80 % de lo cambiado, mutación con 0 supervivientes sin justificar y MANUAL con comando.
  Mutación (T19) y MANUAL (T20–T23) quedan fuera del bloque por plan de `tasks.md`.

## Verificación propia

| Qué | Resultado real |
|---|---|
| `bash harness/init.sh` (entero) | exit 0, ENTORNO LISTO; raíz `1067 passed in 280.57s`; servicios en verde (caché) |
| Puerta cobertura | `[OK] 100.0% de 148 líneas cambiadas cubiertas (148/148, umbral 80%, nivel critico)` |
| Puerta tamaño | `requirements 150/150, design 250/250, impl 179/220` |
| Rutas sensibles | N/A (F-052 no toca ninguna ruta declarada) |
| sv3 a mano, sin caché, después de init | `357 passed in 4.87s` (incluye `test_f002_red_proveedor`, grounding y refetch) |
| ruff, ficheros de producción tocados (base f766178 → HEAD) | igual en todos salvo `phase2_ddl.py` 17 → 21: los 4 `ISC004` del DDL, mismo estilo que el resto de `_PHASE2_DDL`; tests nuevos `All checks passed!` |
| Árbol tras las pruebas | limpio (copias en el scratchpad con `git archive`) |

**RED reproducida por mí** (test del commit de la tarea sobre el árbol del commit anterior,
comprobado que `application` se cargaba de la copia):

- **T7** (tests de `8085dd4` sobre `f766178`): `19 failed, 9 passed` —
  `TypeError: cannot unpack non-iterable ProveedorObraResumen object`, `assert None ==
  (None, 'sin_obra', 0)`, y las notas antiguas «ningun proveedor ... casa» frente a «no se
  pudo consultar ... 0691 (fallo al consultar Sigrid): no hay propuesta» (con `error_xml`),
  «no hay obra válida», «no se leyó nombre» (con `'—'` y `'   '`) y «ninguno de los
  0|1|3|81». Coincide con el informe.
- **T8** (`-k r6_familia`, tests de `f7e86ef` sobre `8085dd4`): `1 failed, 3 passed` —
  `ValueError: not enough values to unpack (expected 1, got 0)` (no había WARNING). Coincide.
- **T9** (tests de `1df8ef5` sobre `f7e86ef`): `13 failed, 2 passed` — falta el ALTER, el
  ORM no declara la columna, `no attribute 'sellar_busqueda_contratos'`. Coincide.
- **T10** (tests de `fed1bfa` sobre `1df8ef5`): `24 failed, 17 passed`; R13 de punta a punta
  `assert [] == [('doc-f052-r...68', 'error')]` y los 6 `fallo_del_sellado_*`. Coincide.
- **O5 · R1 contra el cliente anterior a T5** (`6d9c795`) con el resolver de T7: `1 failed`,
  pero la nota que sale es «**no se pudo consultar** la lista de proveedores de la obra 0691»
  (la agregada no existía y la consulta antigua lanza truncado): el resolver nuevo ya no
  miente aunque el cliente sea el viejo. La cita del informe («ningún ... casa») es la del
  resolver de `f766178`. Ambas son RED legítimas; ver O-B3.

**Mutantes propios** (copias de HEAD, `test_f052_rastro_busqueda.py` + `test_f052_nota_proveedor.py`):
M1 `_sellar_busqueda_safely` sin `try/except` → **muerto**, `7 failed` (los 6 de fallo del
sellado y el de repositorio sin el método); M2 sellar `sin_datos` con `cif, obra_raw` sin
normalizar → **muerto**, `2 failed`.

## Revisión por tarea

- **T7** (`header_resolver_service.py`): firma `(candidato | None, motivo, n)` según design
  §5; `sin_obra` precede a `sin_nombre` (decisión razonable y testeada); `n = len(resumenes)`
  real en `propuesta` y `nadie_casa`, 0 en el resto. Los cuatro textos son literales de
  design §6 (verificados uno a uno); cabeza y prefijo intactos (R19: `startswith` en las 5
  ramas). Una consulta que lanza —cualquier excepción, incluido `SigridRespuestaTruncada`—
  es `consulta_fallida`, nunca `nadie_casa` (R6/R15 con `error_xml`, truncado, HTTP y red).
  sv4 solo usa el prefijo y el motivo (`review_repository.py:3331-3345`): nadie parsea la cola.
- **T8**: `except SigridRespuestaTruncada` va antes del `except Exception` (es subclase de
  `RuntimeError`), WARNING con obra, etiqueta y filas y degradado idéntico al de hoy
  (`(None, "deterministic")` → fallback global); el resto sigue con `logger.exception`
  (test lo comprueba con `exc_info`). No se traga nada que antes se propagara.
- **T9**: 4 `ALTER ... ADD COLUMN IF NOT EXISTS`, nullable, tipos de design §4; ORM con las
  mismas longitudes (test que los ata); `schema_contribution` los exporta; raw sin tocar.
  Puerto keyword-only; el repositorio valida el resultado antes de tocar la BBDD y pone la
  fecha UTC. Arranque: `repository.initialize()` y luego `apply_phase2_ddl` en
  `composition.py:74` y `app.py:109`, igual que las columnas de fases previas.
  **Compatibilidad**: sv5 lee el merge con columnas explícitas
  (`sqlalchemy_valuation_context_repository.py:40-56`); sv6 solo referencia la FK; sv4 tiene
  su ORM propio sin las columnas (T11) y su `SELECT *` del historial de deshacer restaura
  columnas genéricas: añadir columnas no rompe a nadie. Orden sv3 → sv4 respetado (§9).
- **T10**: sello en las 5 salidas de `tasks.md` más el fallo de `replace_contratos`
  (`error`), un solo sello por búsqueda (test parametrizado sobre las 6), best-effort con
  `logger.exception` y valor devuelto igual (M1 lo confirma). Truncado de `fetch_contratos`
  → `error` con el cliente real sobre el doble (R13 de punta a punta). CIF y obra sellados
  normalizados (M2 lo confirma).

## Checkpoints (en lo aplicable al bloque)

- C1 [x] init.sh exit 0; ficheros del arnés presentes.
- C2 [x] una sola `in_progress`, rama correcta. «current.md solo la sesión activa»: N/A en
  review de bloque — arrastra sesiones previas (ya anotado en la review A); lo poda el líder
  antes del cierre.
- C3 [x] hexagonal: constantes en `domain/models`, puerto en `domain/ports`, SQL en
  `infrastructure`; `application` importa solo la excepción pura de `ruesma_comun.sigrid`
  (ya importaba `ruesma_comun` antes). Primera línea con ruta en los tests nuevos; sin
  `print`, TODO ni secretos (los CIF son de proveedores del fixture, ya aprobado en A); sin
  dependencias nuevas. Trampa (2) de C3: el cambio de schema lista su lector (sv4) en el
  docstring de `phase2_ddl.py`; sv5 revisado arriba.
- C3 bis N/A: no toca `docs/referencia/`. C4 ter N/A: la puerta dice que no toca rutas sensibles.
- C4 [x] R1, R5 (red por nombre), R6, R13 (rastro), R15–R21 con tests `test_f052_rN_*` en
  verde; sin red ni BBDD (doble y fakes). MANUAL T22 (escritura real del rastro) fuera del bloque.
- C4 bis [x] rigor declarado; [x] RED real en el informe y reproducida por mí en T7–T10 y O5;
  [x] cobertura 148/148; [x] sección «Evidencias» con tests, cobertura, mutantes manuales y
  tiempos. N/A mutación y RM1–RM6: la campaña es T19, fuera del bloque; no hay campaña que revisar.
- C5 N/A: review parcial; T11–T24 pendientes por plan.

## Trazabilidad requisito → test (Bloque B)

| Req. | Tests |
|---|---|
| R1 | `test_f052_r1_la_red_por_nombre_propone_salmedina_con_el_cliente_real`, `_r1_mejor_candidato_devuelve_candidato_motivo_y_n` |
| R5 (red) | `test_f052_r5_la_red_por_nombre_no_depende_del_orden_de_llegada[11,22,33]` |
| R6 | `test_f052_r6_error_xml_la_nota_dice_que_no_se_pudo_consultar`, `_r6_familia_error_xml_*`, `_r6_familia_truncado_warning_*`, `_r6_familia_consulta_fallida_no_decide_*` ×2 |
| R13 (rastro) | `test_f052_r13_fetch_contratos_truncado_por_tope_de_paginas_sella_error` |
| R15 | `test_f052_r15_cualquier_fallo_*[truncado,http,red]`, `_r15_mejor_candidato_consulta_fallida_con_n_cero` |
| R16/R17 | `test_f052_r16_sin_obra_valida_*` ×4, `_r16_sin_obra_ni_nombre_manda_la_obra`, `_r17_sin_nombre_leido_*` ×3 |
| R18 | `test_f052_r18_nadie_casa_con_los_81_*`, `_r18_n_es_el_numero_*[0,1,3]`, `_r18_mejor_candidato_nadie_casa_con_n` |
| R19 | `test_f052_r19_motivo_y_prefijo_de_siempre` ×5 |
| R20 | `test_f052_r20_*` (DDL, idempotencia, `schema_contribution`, ORM, raw, puerto, repositorio ×9) |
| R21 | `test_f052_r21_*` (una por salida, fallo del sellado ×6, un sello ×6, repositorio sin el método) |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

- **O-B1 · salidas por excepción sin sello.** Si `get_merge_cif_and_obra` (u otro paso no
  protegido) lanza, `enrich_merge_document` propaga como hoy y el rastro anterior se queda.
  En la práctica solo pasa con la BBDD caída (y entonces el sello también fallaría). Si se
  quiere blindar, un `try/finally` con `error`; no lo pide R21.
- **O-B2 · decisiones para el líder/humano**: `replace_contratos` fallido → `error` y
  `enabled=False` → sin sello. Las comparto (ni `encontrados` ni `ninguno` serían verdad;
  sin búsqueda no hay rastro), pero son extensiones de R21 y deben constar al cerrar.
- **O-B3 · redacción de la traza O5** (`impl_F-052.md`, línea de «R1 contra el cliente
  anterior a T5»): aclarar que se lanzó con el resolver de `f766178`. Con el resolver de T7
  la nota ya dice «no se pudo consultar» (reproducido): conviene decirlo, porque demuestra
  que R15 no depende de T5.
- **O-B4 · para T11–T15 (sv4)**: el historial de deshacer de sv4 (`snapshot_row`,
  `SELECT *` + `UPDATE` de todas las columnas, `review_repository.py:2537-2711`) restaurará
  también `contratos_busqueda_*`. Deshacer un cambio de CIF devuelve CIF y rastro viejos a
  la vez (coherente), pero quien haga T13 bis debe tenerlo en cuenta al comparar CIF/obra
  con el rastro, y el Bloque C debería tener un test que lo fije.
- **O-B5**: cabeza sin tilde («CIF leido») y cola con tildes; fiel a design §6, solo estético.

## Propuesta de automejora (no aplicada)

`reviewer.md`, fase RED: cuando una RED se lanza «contra el cliente anterior» pero sobre un
árbol que no es el del commit previo, pedir que el informe diga el SHA de CADA pieza
combinada (cliente de X, resolver de Y). Aquí las dos combinaciones fallan, pero con textos
distintos, y sin el SHA no se puede reproducir la cita exacta.
