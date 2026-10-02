<!-- progress/review_F-052.md -->
Revisión de cierre (pasada 1): incremental desde 07f89cf (Bloques A–D aprobados) hasta 9a06fcf, más barridos transversales sobre `git diff dev...HEAD`

# F-052 · Review de cierre

**Veredicto: APPROVED, condicionado al papeleo de cierre del líder (abajo).** Código, tests, campaña y
MANUAL T20–T22 están bien. No pido cambios de código. Pero F-052 **no puede pasar a `done`** hasta que se cumplan las
condiciones 1–4: C2 (`current.md`) hoy **no** se cumple. Mismo patrón que el cierre de F-048.

**Rigor:** `critico` (declarado en `features.json`). Exige RED, cobertura ≥ 80 %, campaña con 0 supervivientes sin
justificación aceptada por el humano, RM1–RM6 y MANUAL con comando y resultado real.

## Qué ejecuté (resultados reales, 2026-10-01)

- `bash harness/init.sh`: **exit 0, ENTORNO LISTO**. Raíz `1067 passed in 421.21s`. `PUERTA COBERTURA: 98.2 %`
  (590/601). `RUTAS SENSIBLES`: N/A (impreso). `TAMAÑO` OK (requirements 150/150, design 250/250, impl 196/220).
  Avisos previos y ajenos: ruff 1166, `infra` sin tests, `[ADAPTAR]` de F-034/F-035.
- Suites una a una, sin caché (`-p no:cacheprovider`; sv4 con su `.venv`): comun `332 passed`, sv3 `421 passed`,
  sv4 `378 passed`, sv1 `98`, sv2 `374`, sv5 `43`, sv6 `230`. Todas en verde.
- Delta desde la última review aprobada (`07f89cf`): `git diff 07f89cf..HEAD -- services/ ':!**/tests/**'` **vacío**.
  Solo entran los tres `test_f052_t19_supervivientes.py` (`dcca978`, sin red: el subproceso sale con `--obra 12`
  antes de configurar nada; `HTTPTransport` con monkeypatch) y papeleo. `git status` limpio antes y después.

## Campaña de mutación (T19) · RM1–RM6

- **Recálculo independiente** (`alcance_de_feature` + `generar_mutantes`, cálculo puro): 26 ficheros, **1.756
  líneas, 220 mutantes**: igual que el informe, fichero a fichero. Los dos supervivientes existen tal cual
  (`codigo.py:39` `"0" + limpio → "0" - limpio`; script `:48` `insert(0 → insert(1`).
- Ni «⚠ CAMPAÑA NO VÁLIDA» ni base rota (0). 0 `PENDIENTE`. **Tiempo total 1.368,7 s > 60 s ⇒ campaña no
  reejecutada**; en su lugar, recálculo + RM1–RM6 + muestreo.
- **RM1** [x] SHA `dcca97864577…`; desde ahí no cambia ni una línea de `services/`, `harness/`, `docs/`, `tests/` ni
  `infra/` (solo `progress/` y `tasks.md`).
- **RM2** [x] Workers 1. Coste por mutante 1.368,7 × 1 ÷ 220 = 6,2 s (> 1 s), con bases de 5,5 / 9,7 / 19,4 s. Sin
  salto de orden de magnitud.
- **RM3** [x] Recorrí los 218 muertos de la lista. Ninguno es equivalente: los de `retries`, `frozen`, `String(n)`
  y `__main__` los matan tests que observan justo eso.
- **RM4** [x] Sobre una copia en el scratchpad: 4 muertos al azar (semilla 20261001) + 1, con la suite del servicio
  y `-x`, todos **muertos** (`orm_models.py:98` sv4, `header_resolver_service.py:513`, cliente `:250`, script `:529`
  ×2). Línea base sv3 de la copia, `421 passed` (sv4 378). El falso superviviente `codigo.py:39` muere con
  `test_f052_obras_codigo.py`: `2 failed, 13 passed`, los mismos dos tests que cita el informe.
- **RM5** [x] (`critico`, muestra de uno). Reproduje el único equivalente, script `:48`: con el mutante, la suite de
  sv3 da `421 passed`. Lanzado como script desde otra carpeta, `--obra 12` da el mismo mensaje y `exit=2` con y sin
  mutar.
- **RM6** [x] `dcca978` solo añade tests; no se quitó ninguna guarda.
- Supervivientes: 2, **los dos ACEPTADOS por el humano** (2026-10-01, «1, ok»), con su análisis escrito.
  **Sin justificar: 0.**

## Checkpoints

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] una sola `in_progress` (F-052) · [x] rama `feature/F-052-proveedores-truncados` · [x] toda `done` está
  en `history.md` o en `historico/` (comprobado por script). **[ ] `current.md` describe solo la sesión activa: NO.**
  Tiene 937 líneas, y algunas afirman estados falsos: F-045 «sigue `in_progress`» (hoy `done`), F-036 «`blocked`»
  (hoy `done`), y «LO PRIMERO…» dice que la spec de F-052 está «a medias». **Bloquea `done`, no el veredicto.** Es
  papeleo del líder. Poda en la condición 2.
- **C3** [x] Hexagonal: `domain/` no importa nada nuevo; BBDD en los repositorios; `sigrid/` y `obras/` de comun,
  sin HTTP ni SQL. [x] Primera línea con ruta en todos los ficheros nuevos. [x] Sin `print` de producción (el del
  script es su salida), sin TODO, sin secretos ni dependencias nuevas (barrido con grep sobre el diff). [x] Trampas:
  la lógica va sobre el merge; los lectores del cambio de schema están listados (sv4 en `azure-apps` §3); sin
  importes.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R1–R30 con test `test_f052_rN_*` en verde (tabla). R31 lo cubren MANUAL T22 y 21 tests `d4a`/`oc1`/
  `cr_c3`. [x] Sin red ni BBDD (doble `MockTransport`, fakes, SQLite en memoria). [x] MANUAL: T20–T22 **hechas por el
  humano** con su resultado en `tasks.md:30-32`. T23 es post-despliegue y no bloquea por plan. Su comando exacto
  está en `tasks.md:33` y **debe quedar en `current.md` tras la poda**.
- **C4 bis** [x] rigor declarado · [x] RED real por tarea en `impl_F-052.md` (las literales, en `ce6bbd4`), y la de
  T19 en `impl_F-052_T19_supervivientes.md` §3 · [x] cobertura 98,2 % · [x] campaña verificada (arriba) · [x]
  «Evidencias» con tests, cobertura, mutantes, workers y tiempos (véase O-F1).
- **C4 ter** [x] N/A impreso por `init.sh` (F-052 no toca rutas sensibles).
- **C5** [x] árbol limpio (solo ignorados ya existentes) · [x] `features.json` = `in_progress`, que es lo real.
  **Condicionado**: T24 sigue en `[ ]`. Queda cumplida con esta ejecución y el líder la marca al cerrar (precedente:
  T41 de F-048). T23 en `[ ]` por plan. T20–T22 se cerraron con un commit `F-052:` y no `F-052 Tn:`: lo acepto, son
  verificaciones del humano sin código.

## Trazabilidad requisito → test (todos en verde)

| R | Tests |
|---|---|
| R1 · R5 · R6 · R15–R19 | sv3 `test_f052_nota_proveedor.py` (`r1_` 2, `r5_`, `r6_` 4, `r15_`–`r19_` 9), `resumen_obra.py::r5_*` |
| R2 · R3 | sv3 `test_f052_resumen_obra.py` (`r2_` 2, `r3_` 4: una petición, `FOR XML PATH`) |
| R4 | sv3 `test_f052_equivalencia_familias.py` (3) |
| R7–R10 | comun `test_f052_sigrid_lectura.py` + sv3 `test_f052_truncado_cliente.py` (19) |
| R11–R13 | sv3 `test_f052_paginacion_cliente.py`, `rastro_busqueda.py::r13_*`; comun `r13_*` (12) |
| R14 | comun `test_f052_sigrid_lectura.py::r14_*` (9) |
| R20 · R21 | sv3 `test_f052_rastro_busqueda.py` (`r20_` 9, `r21_` 12 entre sv3 y sv4) |
| R22 | sv4 `test_f052_refetch_local_rastro.py` (11) |
| R23–R27 | sv4 `test_f052_bloque_contrato.py` (8), `test_f052_busqueda_contratos.py::r27_*` (6) |
| R28 | sv4 `test_f052_lookup_truncado.py` (5) |
| R29 · R30 | sv3 `test_f052_script_verificacion.py` (13 + 5) + **MANUAL T20/T21 OK** (81 filas, 5/5, 5,47 s; 0 dif.) |
| R31 | **MANUAL T22 hecha** (doc 77a0c01f) + sv4 `test_f052_d4a_*`/`oc1_*`/`cr_c3_*` (21) |

## Documentación y despliegue

- `docs/ARCHITECTURE.md` «Acceso a datos»: 500.000, el 1.000 era el `max_rows` del cliente, las tres reglas de
  lectura, y la excepción de `comun`: `sigrid/` y `obras/` las importan solo sv3 y sv4, **orden sv3 → sv4** porque
  el DDL de sv3 va antes que el ORM de sv4.
- `azure-apps/albaranes.md`: commit `141f9aa`; no ha cambiado después (`git log 141f9aa..HEAD -- albaranes.md`
  vacío). §3 trae las 4 columnas, el dueño (sv3), el lector (sv4) y «**Orden de despliegue OBLIGATORIO: sv3 →
  sv4**». §8 trae `truncated`, `WITH` + `FOR XML PATH`, la página de 499.999 y 0.7.0. El repositorio no tiene remoto.
- `sv4.md`: normalizador → `ruesma_comun.obras` (§árbol, §refetch, §7, deuda 3). `sv3.md`: quita
  `obra_code_normalizer`. `comun/README.md` + `pyproject` 0.7.0; `packages.find include=["ruesma_comun*"]` incluye
  los subpaquetes, y las dos imágenes instalan `comun/` fresco (Dockerfile de sv3 y de sv4).
- Nada a medias en el código. Quedan pendientes, todos del humano o posteriores: merge a `dev` (lleva dentro el
  arreglo `fix/F-048-comparar-obra-base`), despliegue sv3 → sv4, T23 y push de `azure-apps`.

## Condiciones para pasar F-052 a `done` (papeleo del líder, sin código)

1. **`tasks.md`**: T24 `[x]` citando esta ejecución (`init.sh` exit 0, `1067 passed`, 98,2 %); T23 sigue `[ ]`.
2. **Poda de `current.md` (C2)**, mínima obligatoria:
   - (a) las seis secciones de F-052 (líneas 8–111) pasan a un resumen en `history.md`;
   - (b) en `current.md` queda solo lo vivo tras el cierre: merge a `dev` y despliegue sv3 → sv4 (humano), T23 con su
     comando exacto (`tasks.md:33` y el SELECT de `spec_F-052.md` §Anexo), la mejora menor de T22, el PENDIENTE de
     `arnes-base` y las observaciones de la lista de abajo;
   - (c) «LO PRIMERO AL ABRIR…» reescrito, y a `progress/historico/` lo que contradice `features.json` (F-045
     `in_progress`, F-036 `blocked`, F-043 como vivo). El resto del arrastre (heredado de `dev`, 833 líneas al
     cerrar F-048): recomendable moverlo, no lo atribuyo a F-052.
3. **`history.md`**: resumen de F-052 con las decisiones del humano (D1–D7, D4-A, O-C1, CR-C1, página de 499.999,
   0.7.0, los 2 supervivientes aceptados) y las observaciones marcadas «history».
4. `features.json` → `done` en ese mismo commit, y `init.sh` en verde después.

## Observaciones abiertas: dónde deben constar al cerrar

| Obs. | Qué | Dónde |
|---|---|---|
| O-B2 | Extensiones de R21: `replace_contratos` fallido → `error`; `enabled=False` → sin sello. | **history** como decisión; enseñarla al humano en el resumen de cierre (nunca la aceptó por escrito) |
| O-B1 | Si `get_merge_cif_and_obra` lanza, se queda el rastro anterior (BBDD caída). | history (límite conocido) |
| O-C2 + mejora T22 + O-C8 | Re-búsqueda doble (combo; «Guardar» durante «Buscando…»); «Solo volver a buscar» vacío publica sin sello. | **current** → proponer **una** ficha de backlog |
| O-C4 + D6 | `header_and_lines` de sv4 (`max_rows=1000`, sin `comprobar_truncado`) y `SigridApiObraClient` de sv3. | **current**: D6 decía «ficha aparte» y **no existe**; registrarla |
| O-C5 | 8 scripts `diagnose_*`/`trace_*` con su copia del normalizador. | history (no son runtime) |
| O-D1 | `timeout_s` es por operación en httpx, no plazo total. | history |
| O-D2 · O-D3 · O-D4 | Fecha de 500.000; «sv7 → sv3» en `azure-apps` §8; R29 no compara solo. | history (cosméticas) |
| Falsos supervivientes | `harness/mutacion.py` cuenta a veces un muerto como vivo (3 casos, sin causa). | **current** + feature de arnés / `arnes-base` (regla de propagación) |
| «1.000» ajeno | `PycharmProjects/CLAUDE.md` («como máximo 1.000 filas») y otros docs de `azure-apps`. | **current**, para el humano (otros dueños) |
| O-F1 (nueva) | La fila «`init.sh` final» de «Evidencias» dice 97,5 %; hoy es 98,2 % (ya en §T19). | history o ignorar (cosmética) |
| O-F2 (nueva) | `sv3.md` §6.3 y `sv4.md` §9.1 no citan `contratos_busqueda_*`; la fuente vigente es `azure-apps` §3. | history (`sv3.md` es documentación heredada, ninguna feature lo mantiene) |

## Propuesta de automejora (no aplicada)

C2 se salta en cada review de bloque y llega al cierre arrastrado: que `init.sh` avise si `current.md` cita como
vivo (`in_progress`/`blocked`) un ID que `features.json` tiene `done`. Es barato y caza lo de hoy (F-045, F-036).
