<!-- progress/review_F-063.md -->
Revisión completa (pasada 1): `git diff dev...HEAD` (`ba72f0a`..`8f01702`)

# F-063 · Review — El CIF de Construcciones Ruesma nunca es el proveedor

- **Veredicto:** APPROVED (condicionado a `init.sh` en verde en `dev` tras fusionar, ver C1)
- **Nivel de rigor:** `critico` (declarado en `features.json`). Exige fase RED, cobertura ≥ 80 % de lo cambiado,
  campaña de mutación completa con 0 supervivientes, RM1–RM6 y sección «Evidencias».
- **Entorno:** venvs del árbol principal sin tocar, `PYTHONPATH` = comun del worktree. Sin `.env`, sin sigrid-api,
  Azure ni BBDD reales. Suites en serie. Sin git en el árbol principal.

## 1. Verificación propia (salidas reales)

| Qué | Resultado |
|---|---|
| sv3 completa (`.venv` raíz) | **583 passed, 1 failed** en 18,5 s: el único KO es `test_f052_t19_script_arranca_como_script_desde_otra_carpeta` (KO de entorno conocido: lanza el script sin `PYTHONPATH` y el venv importa el comun del árbol principal, sin `propios.py`). F-052, F-062 y F-002 en verde |
| comun completa | **433 passed, 3 skipped** (125 s) |
| `bash harness/init.sh` en el worktree (con `PYTHONPATH` al comun del worktree) | exit 1 con los **2 KO de entorno conocidos**: `[KO] sv3: 1 failed, 394 passed` (el mismo `test_f052_t19_...`, y el `-x` corta la suite) y por eso `[KO] PUERTA COBERTURA 50,8 %`. Raíz **1083 passed**; resto de servicios OK; `BACKLOG al día`; `RUTAS SENSIBLES: N/A`; `TAMAÑO` OK; ruff 1190 (= `dev`) |
| Puerta de cobertura rehecha por mí (sv3 bajo `coverage` con ese test deseleccionado: **583 passed, 1 deselected**) | `PUERTA COBERTURA: 96.6% de 59 líneas cambiadas cubiertas (57/59, umbral 80%, nivel critico)` |
| Import real de `interface_adapters/composition.py` y `api/app.py` (venv de sv3, con fastapi) | importan; `Settings.cifs_propios` con alias `CIFS_PROPIOS` |

**Controles negativos re-aplicados por mí** (`tests/test_f063_cif_propio.py`, 35 casos; tras cada uno
`git checkout` del fichero y `git diff | wc -c` = **0 bytes**):

| Control | Cambio | Resultado |
|---|---|---|
| C1 | `_descartar_cif_propio`: `if not es_cif_propio(...)` → `if True:` (sin descarte) | 13 failed (R4/R5/R7/R10/R11/R12, tres rutas) |
| C2 | `_no_es_propio` → `return True` (sin filtro R9) | 4 failed (los cuatro R9) |
| C3 | `== "manual"` → `== "xmanual"` (no respeta al revisor) | 2 failed (R6) |
| C4 | repo `descartar_cif_propio` sin `proveedor_cif = None` | 1 failed (repo R4) |
| C5 | red por CIF ANTES del descarte (orden) | 15 failed |

Caso real: `test_f063_r11_pipeline_...[nuevo|duplicado|reenrich]` con `fixture_f063` (obra 0694, FEYMACO
A28733558, Ruesma en `prv`): el merge acaba en A28733558, contratos buscados SOLO con A28733558, A81873903 nunca
preguntado a sigrid-api. Su control (`cifs_propios=frozenset()`) reproduce la incidencia: Ruesma canonizado,
búsqueda `ninguno`.

## 2. Revisión del diseño frente a producción

- **Punto único correcto.** `_resolve_proveedor` es la única entrada de proveedor de las tres rutas
  (`run` nuevo/duplicado y `reenrich_by_merge_id` llaman a `_resolve_header_deterministic_safely` ANTES de
  `_enrich_contratos_safely`, que relee el CIF del merge con `get_merge_cif_and_obra`). El descarte va antes de
  `_red_proveedor_por_cif` (sin `fetch_proveedor_by_cif`, sin canonizar).
- **`update_merge_resolved_header` no resucita el CIF**: tras el descarte el merge tiene CIF y origen NULL; con
  CIF deducido lo escribe (origen ≠ `manual`); sin él no hace nada. R7 (escritura fallida) también sale bien
  si el camino «sin CIF» deduce; si no deduce, el CIF del cliente queda como estaba y se marca `ia`, pero sin
  canonizar ni candidatos: aceptable como best-effort con la BBDD caída.
- **Nota y motivo sobreviven**: nadie borra por prefijo `[AVISO] CIF del cliente` ni `proveedor_cif_propio:`
  (buscado en sv3). D1 es correcto y necesario: con `[AVISO] Proveedor` la propia pasada la borraría
  (`_remove_nota_proveedor_safely`). `review_required` no lo baja nadie después en el pipeline.
- **R6 · manual**: comparación con `strip()`; la red sigue como antes. Justificado (D2).
- **R9** en los tres puntos de entrada de candidatos (obra con familia, `_candidatos_puntuados` de la red y
  global). Hexagonal respetada: constantes en dominio, puerto en `domain/ports`, SQL en infraestructura, regla
  pura en comun; comun se empaqueta en la imagen de sv3 (`Dockerfile`: `COPY comun/`), así que desplegar SOLO
  sv3 basta.
- **Sin interruptor (D4)**: la vuelta atrás es la revisión anterior de la Container App. Aceptado.

## 3. Checkpoints

- C1 `[x]` init.sh, **condicionado**: en el worktree sale exit 1 solo por el KO de entorno conocido (comun del
  árbol principal sin `propios.py`) y su arrastre en la cobertura, ambos demostrados en verde en §1. El
  APPROVED vale **si y solo si** `bash harness/init.sh` en `dev` tras fusionar sale en verde (lo ejecuta el
  líder); si no, la feature no se cierra · `[x]` ficheros del arnés presentes.
- C2 `[x]` una sola `in_progress` (F-063) · `[x]` rama `feature/F-063-cif-propio-no-es-proveedor` · `[x]`
  `current.md` de la sesión · `[x]` features `done` con su historia (sin cambios aquí).
- C3 `[x]` hexagonal · `[x]` primera línea con ruta en todos los nuevos · `[x]` sin `print`, TODOs ni secretos
  (el CIF de Ruesma es dato público de empresa, no secreto) · `[x]` reglas de ARCHITECTURE: regla 18 nueva,
  coherente con la 17 (F-062).
- C3 bis `N/A`: la feature no trae documentos de fuera.
- C4 `[x]` cada requisito con test (tabla §4) · `[x]` sin red ni BBDD (dobles) · `[x]` MANUAL listada (T8).
- C4 bis `[x]` rigor declarado · `[x]` **RED** con salida real por tarea (T1–T5; T5 contra el resolver de `dev`
  en bytes) · `[x]` **cobertura** 96,6 % (57/59; las 2 sin cubrir son los `import` de composición, cuyo cableado
  fija un test y yo importé de verdad) · `[x]` **mutación** completa: recalculé con `harness.alcance` y
  `generar_mutantes`: **9 ficheros, 228 líneas, 14 mutantes**, coinciden · `[x]` muertos comprobados: «Tiempo
  total» 322 s > 60 s ⇒ **campaña no reejecutada (322 s según el informe)**; recálculo puro + RM1–RM6 + mis
  controles C1–C5, que tocan los mismos puntos que 10 de los 14 mutantes · `[x]` sin cabecera de campaña no
  válida, 0 sin veredicto, línea base declarada · `[x]` **RM1**: SHA medido `9af7766`; desde ahí solo cambian
  `progress/`, `tasks.md` y el orden de imports de los dos tests: ningún fichero del alcance · `[x]` **RM2**:
  14 × 23,0 = 322 s, cuadra; media por debajo de la base de comun por `-x` y porque 13/14 mutantes son de sv3
  (base 12 s) · `[x]` **RM3**: revisé los 14; ninguno equivalente (p. ej. `cif_leido and` → `or` descarta todo
  CIF; `extra or ""` → `and` anula los añadidos o rompe con `None`) · `[x]` **RM5**: no hay supervivientes ni
  equivalentes declarados · `[x]` **RM6**: no se quitó ninguna guarda · `[x]` campaña automática, no manual ·
  `[x]` sin supervivientes pendientes · `[x]` «Evidencias» con los cuatro números · `[x]` ningún N/A sin motivo.
- C4 ter `N/A`: `init.sh` imprime `PUERTA RUTAS SENSIBLES [evals]: N/A (F-063 no toca ninguna ruta sensible declarada)`.
- C5 `[x]` `tasks.md` T0–T7 `[x]` con un commit `F-063 Tn:` cada una. T8 (MANUAL, despliegue de sv3) y T9
  (`init.sh` en `dev`) `N/A` en esta pasada, justificado: son posteriores a la fusión por diseño del flujo y las
  cierra el líder/humano (encargo: «la verificación definitiva es `init.sh` en `dev` tras fusionar») · `[x]` sin
  temporales sin trackear (`git status` limpio salvo este informe) · `[x]` `features.json` en `in_progress`, real.

## 4. Trazabilidad requisito → test

| Req. | Test(s) |
|---|---|
| R1, R2 | `services/albaranes-comun/tests/test_f063_cifs_propios.py` (16) |
| R3 | `test_f063_r3_resolver_usa_la_lista_que_recibe`, `..._setting_con_su_alias_y_defecto_vacio`, `..._los_dos_puntos_de_composicion_...` |
| R4 | `test_f063_r4_repo_*` (3), `test_f063_r4_r5_resolver_descarta_...` (3 variantes de CIF) |
| R5 | `test_f063_r4_r5_*`, `test_f063_r11_pipeline_*` |
| R6 | `test_f063_r6_resolver_respeta_el_cif_propio_elegido_por_el_revisor` (`manual`, ` manual `) |
| R7 | `test_f063_r7_resolver_con_la_escritura_fallida_...` |
| R8 | `test_f063_r8_control_negativo_un_cif_normal_...`, `..._sin_cif_no_hay_descarte`, `..._control_un_albaran_con_el_cif_de_feymaco_no_cambia` (3 rutas) |
| R9 | `test_f063_r9_candidato_*` (5) |
| R10 | `test_f063_r10_*` (prefijos, repo dos veces, re-pasada) |
| R11 | `test_f063_r11_pipeline_*` (3 rutas) + control negativo (3 rutas) |
| R12 | `test_f063_r12_*` (resolver y pipeline, 3 rutas) |
| R13 | `test_f063_r4_repo_descarta_...` (nombre intacto; motivo y nota con el CIF) |

## 5. Observaciones (no bloquean)

1. **Los dos merges ya canonizados (`b1d3e179-…`, `401d9c00-…`).** Su nombre es «CONSTRUCCIONES RUESMA, S.A.».
   Un «Solo volver a buscar» descarta el CIF y busca POR ESE NOMBRE: `_match_score` da **0,67** (≥ 0,5) contra
   cualquier «CONSTRUCCIONES <X>, S.A.» (medido: «CONSTRUCCIONES SARRION, S.A.» → 0,67), así que el paso 2
   global puede fijar un proveedor equivocado con origen `deterministic`. No es silencioso (queda
   `review_required` y la nota `[AVISO] CIF del cliente`) y la spec lo deja fuera, pero **para T8 conviene ir
   directo a «Elegir proveedor» (FEYMACO) en esos dos merges** y usar el re-proceso solo en un albarán nuevo o
   con el nombre leído. Lo mismo valdría si un día la IA lee también el NOMBRE del cliente (fuera de alcance):
   propongo ficha aparte para excluir el nombre propio de la resolución por nombre.
2. **`POST /v1/sigrid/header-grounding` (sv3, `HeaderGroundingService`)** valida por CIF exacto contra `prv` y
   devolvería A81873903 como `validated` con la razón social de Ruesma a quien lo consuma (sv7, fuera del
   monorepo). En la incidencia no intervino (el nombre llegó bien a sv3), pero es el mismo principio: propongo
   ficha aparte para aplicar `es_cif_propio` también ahí.
3. `reenrich_by_merge_id` trata como «no existe» un merge con CIF **y** obra NULL. F-063 hace más frecuente el CIF
   NULL; con obra presente (el caso real) no afecta. Previo a esta feature.

## 6. Automejora (propuesta, no aplicada)

Ninguna al protocolo: los controles negativos propios bastaron para dar por buenos los muertos sin repetir 322 s.
