# F-075 · Informe del implementer (2026-10-18) — BLOQUEADA antes de T1

Rama `feature/F-075-importe-leido`, worktree `C:\Users\pgris\PycharmProjects\albaranes-F-075`. Spec v2 con la PARADA 1
v2 aprobada (2026-10-15). Rigor `critico`. **Estado: `blocked`. No se ha escrito código.** Motivo en §2.

## 1. Lo hecho

- **Fusión de `dev`** (`a3c9e6a`, posterior a `1ebc7af`: F-078, F-076, F-077, F-073, F-064) con `git merge dev`, sin
  rebase. Commit `155868e`. Conflictos solo de texto:
  - `harness/features.json`: se conserva todo lo de `dev` y se añade la entrada de F-075 detrás de F-070.
  - `progress/current.md`: se conserva entero el de `dev` y se añade arriba el bloque de F-075.
  - `BACKLOG.md` regenerado con `python harness/backlog.py`.
  - En código no hubo ningún conflicto: la rama solo tenía commits de spec.
- *Junction* `services\albaranes-front\.venv` → venv de sv4 del árbol principal (`mklink /J`). **Hay que quitarla con
  `cmd /c rmdir` antes de `git worktree remove`.**
- He leído las «Notas para quien fusione después» de F-078 y F-076 sobre F-075, y encajan con la spec:
  - el `ValoracionDirectaBuilder` pasa por `completar_registros` antes del `replace_valuation`. Lo exige
    `test_f078_pipeline_todo_replace_valuation_con_lineas_va_tras_completar_registros`;
  - después se llama a `NormalizadorPartidas.anotar(header, lines, normalizacion)`;
  - el sobre ya llega normalizado, porque el pipeline rebinda `envelope` antes de la rama `no_contract`.
- He contrastado la spec con el `dev` fusionado (§3). Encaja todo salvo **un hecho de código que la spec da por
  supuesto y que es falso** (§2). Ese hecho rompe R5, R6 y R8, el design §5 y la T2, y obliga a tocar un servicio que
  la spec deja fuera.

## 2. Bloqueo: el sobre `no_contract` de sv5 no lleva `precio_neto_albaran`

**Lo que dice la spec.**
- design §1: «sv5 no cambia: con `no_contract` ya devuelve `context.lineas_albaran`».
- design §5: `aplica(envelope)` mira `context.lineas_albaran[i].precio_neto_albaran`, «el `precio_neto` puro, no
  `importe_albaran`, que sv5 deriva con la fórmula cuando falta (P3)».
- design §11 y «Fuera de alcance»: «sv5 entero» no se toca y no se cambia sv5.

**Lo que hace el código** (`services/albaran-valoracion-api/application/pipelines/value_albaran_pipeline.py`).
- Sin contrato, sv5 arma el sobre con `_envelope_no_contract`, que serializa cada línea con
  `_raw_albaran_line_to_dict` (l. 56–73). Ese diccionario lleva estos campos: `merge_line_id`, `line_index`, `codigo`,
  `descripcion`, `unidad_medida`, `cantidad`, `precio_unitario_albaran`, `importe_albaran`, `codigo_partida_albaran` y
  `contexto_linea_json`. **No lleva `precio_neto_albaran` ni `descuento_albaran`.**
- `RawAlbaranLine` sí los trae (`precio_neto` y `descuento`). El SELECT del repositorio los lee (l. 177–178). Solo la
  rama con contrato los propaga, a través del prefilter (`unit_category_prefilter.py` l. 164).
- `importe_albaran` del sobre es `COALESCE(precio_neto, cantidad·precio·(1−dto/100))` (SELECT l. 171–174). Es justo
  la cifra derivada que la spec prohíbe usar (P3 aceptada por el humano, D4).

**Consecuencias si se implementa la spec tal cual.**
- En sv6, `AlbaranLineContextDto.precio_neto_albaran` llega siempre `None` en un `no_contract`, porque el campo es
  opcional y vale `None` por defecto. `aplica()` daría siempre `False`.
- Ningún DISCOIN se valoraría: R5 no se cumpliría nunca, y R8 («ninguna línea trae importe») se cumpliría siempre.
- Sin el descuento en el sobre tampoco se puede «despejar el unitario del importe» de R6 cuando la línea trae
  descuento.

**Opciones** (el humano decide; no he implementado ninguna).

| | Opción | Cambia | Coste y riesgo |
|---|---|---|---|
| **A (recomendada)** | sv5 añade `descuento_albaran` y `precio_neto_albaran` en `_raw_albaran_line_to_dict` (dos claves; los datos ya están en `RawAlbaranLine`) | sv5: 2 líneas y un test `test_f075_no_contract_lleva_precio_neto`. Se corrigen design §1, §10 y §11 y «Fuera de alcance» | Es un añadido compatible: el DTO de sv6 ya tiene los dos campos, y un sv6 viejo los parsea y no los usa. Hay que **redesplegar sv5**, con orden comun → sv3 → **sv5** → sv6 → sv4. Si sv6 sale antes que sv5, `aplica()` da `False` y queda la cabecera vacía de hoy, que es inocuo, y un «Revalorar» lo rehace. sv5 no lee ni escribe nada nuevo |
| B | sv6 lee `precio_neto` y `descuento` del merge con una consulta propia (`importes_leidos(document_id)`), como ya lee la obra para F-076 | sv6: puerto, repositorio y test. sv5 sin cambios | Abre una segunda fuente de verdad: lo valorado ya no sale entero del sobre, y `raw_ia_envelope_json` deja de ser la traza completa. Añade una lectura de BBDD por cada `no_contract` |
| C | Usar `importe_albaran` del sobre, la cifra derivada | Nada fuera de sv6 | **Contradice P3/D4**, que el humano aceptó: una línea con precio y sin importe contaría como «con importe» y el documento se podría aprobar con un importe calculado y no leído. Descartada salvo que el humano cambie P3 |

Con A o B, el resto de la spec no cambia.

**Lo que hay que corregir en la spec si se elige A:**
- design §1: «sv5 añade dos claves al sobre `no_contract`»;
- design §3: una fila para sv5;
- design §10: el orden de despliegue;
- design §11: quitar «sv5 entero»;
- requirements, «Fuera de alcance»: «cambiar sv5» pasa a «cambiar el cálculo de sv5»;
- tasks: una tarea nueva antes de T2 («sv5: el sobre `no_contract` lleva `precio_neto_albaran` y
  `descuento_albaran`»), y T18 despliega también sv5;
- `features.json`: añadir `sv5-valoracion-api` a `servicios`.

## 3. Lo demás del contraste con `dev` (encaja; dos matices para la misma PARADA)

| Pieza de `dev` | Contraste | Veredicto |
|---|---|---|
| F-078 `completar_registros` / `fila_a_guardar` | Una línea directa es una «Nueva con blanca»: su concepto es el de la fila o, si está vacío, el del papel; la unidad sale de la derivada y el precio de la fila. Es lo que pide R6 | Encaja |
| F-078 R17 (sv4 no aprueba si hay filas sin vincular y sin descripción) | Las líneas directas no están vinculadas y su descripción es la del papel. Un albarán con alguna línea sin concepto no se aprueba hasta que alguien lo escriba, igual que con R37 | Encaja (más estricto, coherente con R9) |
| F-076 normalización y `anotar` | La partida final de la línea directa es la del sobre ya normalizado (`CI.04.18` ⇒ `CI.4.18`). `anotar` devuelve la leída a `codigo_partida_albaran` y deja el motivo | Encaja. Mejora R6: la partida impresa ya llega en su forma de Sigrid |
| F-077 R11 (validación de «Guardar y aprobar») | `_exigir_lineas_completas` no cambia. La línea directa sin importe cae en «Líneas sin cantidad o importe» | Encaja |
| F-053 R37, `esta_valorado` | `no_contract` ya figura en `ESTADOS_VALORACION_MANUAL`. Con todas las líneas con importe no nulo da `True`, y con una nula da `False` | Encaja (R9, R26) |
| F-064 prompt de IA1 | La sección «Pie del albarán» va aparte, detrás de las reglas de cabecera. La regla de líneas «Evita subtotales, totales, IVA…» (l. 102) sigue valiendo para las líneas; la sección nueva tiene que decir que el pie va a la cabecera y no a las líneas | Encaja; cuidado con la redacción |
| F-073 (sv3, proveedor) | No toca el disparo ni los guards | Encaja |
| sv4 revalorar | Sigue el 409 «Elige un contrato antes de valorar» (`app.py` l. 1340). `notify_contract_selected` publica `q-persistencia` con `force` sin usar el código | Encaja con design §3 |

**Matiz M1 (R3).** Hoy el disparo hace SKIP con `has_lines=False` en dos casos: (a) no hay contrato seleccionado; (b)
hay contrato seleccionado con 0 líneas. En el caso (b), publicar con `codigo_contrato=None` no lleva a `no_contract`.
sv5, con el override nulo, toma `codigo_contrato_seleccionado` del merge (`load_context`, l. 243–245) y va por la rama
con contrato, con 0 líneas de contrato y con IA. Si no encuentra la cabecera, lanza un error. **Propuesta:** solo se
publica sin contrato cuando `codigo` es nulo (caso a); el caso (b) sigue con SKIP, como hoy, y un test lo fija.

**Matiz M2.** Ninguno más: R12 se puede calcular en la rama con contrato porque allí el prefilter sí propaga
`precio_neto_albaran`.

## 4. Fase RED, Evidencias y verificaciones MANUAL

No aplica todavía: no hay ni tests ni código de F-075. Las T0, T17 y T18 son del humano y siguen como en `tasks.md`.

## 5. `bash harness/init.sh` tras la fusión (commit `155868e`)

Ejecutado tal cual desde Git Bash, con `PYTHONPATH` apuntando a la comun del worktree, en el worktree: **`ENTORNO LISTO.
Puedes trabajar.`** (código 0). Avisos que no bloquean:
- features `blocked`;
- ruff, 1322 avisos de deuda previa;
- infra sin tests;
- marcas `[ADAPTAR]` de F-034 y F-035.

`PUERTA COBERTURA: N/A` (no hay líneas de producción cambiadas). `PUERTA TAMAÑO` en verde.

## Evidencias

| Evidencia | Valor (medido, `init.sh` del 2026-10-18 tras la fusión) |
|---|---|
| Tests ejecutados | raíz 1317; sv1 205; sv2 468; sv3 1496; sv4 1715 (1 warning); sv5 43; sv6 444 (+1 skipped); sv9 670; comun 818 (+3 skipped). 0 fallos |
| Cobertura de las líneas cambiadas | N/A (`PUERTA COBERTURA`): no hay código de F-075 |
| Mutantes generados / supervivientes | no aplica todavía: no hay código. La campaña completa va en T16 |
| Tiempo de la suite | raíz 490,8 s; sv4 426,8 s; comun 171,5 s; sv6 89,2 s; sv9 89,2 s; sv3 83,1 s; sv1 78,9 s; sv2 78,6 s; sv5 20,4 s |
| Fase RED | no aplica todavía (no hay código) |
