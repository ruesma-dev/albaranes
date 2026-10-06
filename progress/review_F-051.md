<!-- progress/review_F-051.md -->
Revisión completa (pasada 1), `dev...1cef691` (rama `feature/F-051-almacen-por-linea`, worktree `albaranes-F-051`).

# F-051 · Almacén por línea · Review

**Veredicto: CHANGES_REQUESTED** (2026-10-05). **Rigor `critico`** (declarado): fase RED, cobertura ≥ 80 %,
mutación completa con 0 supervivientes sin justificar y MANUAL listadas. Las cuatro puertas se cumplen. Bloquean dos
defectos de código (H1, H2), un test que no vigila lo que dice (H3) y tres arreglos de papeleo.

**Entorno (resultado real).** `bash harness/init.sh` en el worktree, tal cual: **EXIT=0, «ENTORNO LISTO»**, sin `[KO]`. Raíz `1067 passed in
273.54s`; las siete suites de servicio `[OK]` (salen de la caché de `init.sh`, así que las relancé yo una detrás de
otra: **sv6 283, sv4 446, sv2 397 passed**). `PUERTA COBERTURA: 98.3% de 117 líneas (115/117, umbral 80%,
nivel critico)`. `PUERTA TAMAÑO` dentro. Avisos: `RUTAS SENSIBLES [evals]` (falta `progress/evals_F-051.md`, T21
del humano), ruff 1181 (deuda previa), infra sin tests y `[ADAPTAR]` F-034/F-035 (ajenos).

## Hallazgos

**H1 · ALTA · Los evals de sv6 no ven F-051.** `evals/procesos/sv6_build.py:568-584` (`_construir_builder`) es un
tercer punto de composición. Por su comentario (`:53-57`) está para «replicar los valores por defecto de sv6», pero
construye `PartidaMatcher` sin `almacen_sin_partida` y el builder sin `familias_destinadas`. Como el constructor
viene apagado por defecto (`6cd3c52`), el modo determinista (IA3 y E2E) **valora como antes de F-051**. La pasada
T21, que se exige justo por tocar rutas sensibles de sv6, mediría la partida sin R1 ni R4, y la comparación con
F-047 en líneas sin partida no diría nada. El implementer encontró el segundo punto (`api/app.py`); este se le pasó.

**H2 · MEDIA · «Guardar» y «Guardar todas» pueden mandar a almacén una línea con partida que nadie tocó.** El input
de partida de una fila no almacén pinta la partida **de la línea de contrato casada**, no la final
(`review_repository.py:1337` y `:1369` → `document_detail.html:713`). La desviación 2 hace que el JS envíe siempre
el valor de ese input, también sin tocarlo (`static/app.js:1168` y `:1230`; antes `v || null` = «no viene»).
Caso real: una complementaria hereda `03.02` de su base (R7, excepción (c)) y casa con una línea de contrato sin
partida (`codigo_partida` es nullable). Su input sale vacío y «Guardar todas» envía `""`, que
`update_line_conciliacion` lee como R12: la deja en almacén sin que nadie lo pida. Si la casada tiene otra partida,
la reescribe con esa y, por la excepción de R20, ahora sin pasar a Nueva. Lo segundo ya existía antes (entonces sí
pasaba a Nueva); lo primero lo trae F-051.

**H3 · MEDIA · El test de R12 en el JS no vigila nada.** Control negativo: devolví las dos líneas de `app.js` a
`body[field] = v || null;` y la suite F-051 de sv4 siguió en verde (**68 passed**). El test
`test_f051_r12_guardar_la_fila_envia_la_partida_vaciada` (`test_f051_almacen_front.py:1066`) busca
`'field === "codigo_partida"'`, una cadena que también está en el filtro de `identityChanged` (`app.js:1145`).

**H4 · BAJA · `azure-apps/albaranes.md` desactualizado.** En `:163-164` enumera `partida_action` como
`existing_matched | new_line_created | inherited_from_base_line | alm_acopio | no_action`. F-051 añade dos valores
y da significado a `codigo_partida_final` NULL (almacén) en una tabla del PostgreSQL compartido. La regla de
mantenimiento de `CLAUDE.md` pide actualizarlo en el mismo trabajo; el design decía «sin cambios» y se equivocó.

**H5 · BAJA · Desviación sin dictaminar.** La excepción de R20 («igual a la de la casada ⇒ sigue Sigrid»,
`review_repository.py:1839-1846`) se aplica a **cualquier** línea, no solo a las que están en almacén (alcance de
R20). Es razonable, pero cambia lo de antes (pasaba a Nueva) y el §2 del informe no lo dice.

**H6 · BAJA · Instrucción peligrosa para quitar la junction.** La junction `services/albaranes-front/.venv` está
ignorada (`.gitignore:132`), no está versionada y no afecta al código: correcto. Pero el §2.6 del informe aconseja
`Remove-Item services\albaranes-front\.venv`. En PowerShell 5.1, `Remove-Item` sobre una junction con hijos pide
confirmación y, si se acepta (o con `-Recurse`), **borra el contenido del destino**, que aquí es el venv de sv4 del
árbol principal. Lo seguro es `cmd /c rmdir services\albaranes-front\.venv`, y antes de `git worktree remove`.

## Preguntas del líder

- **`ALMACEN_SIN_PARTIDA_ENABLED`, «apagado por defecto».** Cumple la spec: en `Settings` vale `True`
  (`settings.py:74-77`, R8), y si se pone a `False` cae `test_f051_r8_interruptor_encendido_por_defecto_y_apagable`.
  Lo apagado es el parámetro del constructor de `PartidaMatcher`, como pide el design. Al desplegar no hay que
  encender nada: ningún script de `infra/` fija variables de sv6, así que vale el `True`. No hay paso de despliegue
  que documentar; `sv6.md` y ARCHITECTURE nombran el interruptor. Coste oculto: todo punto de composición que no se
  toque se queda en el comportamiento viejo sin avisar (H1).
- **Junction**: H6. **JS** (`""`): H2 y H3. **Prompt de IA1**: las cuatro viñetas coinciden literalmente con el
  design y van tras la de «cercanía…». La viñeta del código único ya no está y el resto queda intacto (R26). Con
  el YAML de `dev`, 11 tests en rojo. No he lanzado evals. **F-027 R22**: el cambio está justificado (motivo escrito
  con una constante, consumidores revisados) y su test R23/R24 sigue midiendo solo commits de F-027.
- **F-049** (solo lectura): su `origen_partida.py` define `ACCIONES_ALMACEN = {"almacen_sin_partida"}`. Su bloque C
  tendrá que usar `estado_partida(final) == "almacen"` (`domain/services/almacen.py`). No hay ficheros en conflicto.
  **F-053**: su spec aún dice «vacía con marca» y `linea_sin_partida` (`requirements.md:22,62`). Hay que
  reescribirla antes de implementarla, como anota el design de F-051.

**Controles negativos re-aplicados** (todos restaurados; árbol limpio): `Settings` por defecto `False` → 1 failed (R8) · `partida_matcher.py:98` → `if False:` → 16 failed (R1–R4, R7,
R28) · `prompts.yaml` de `dev` → 11 failed · `app.js:1168,1230` → `v || null` → **0 failed (H3)** · sin anular la
partida en almacén (`review_repository.py:~1402`) → 3 failed (R11).

## Checkpoints

- C1 [x] init.sh EXIT 0 · [x] ficheros base.
- C2 [x] solo F-051 `in_progress` · [x] rama de la feature · [x] `current.md` coherente · [x] `done` en history.
- C3 [x] hexagonal (`almacen_politica.py` y `domain/services/almacen.py`, puros) · [x] primera línea con ruta ·
  [x] sin prints ni secretos (`PG_PASSWORD="p"` son dobles de test) · [ ] **reglas de dominio**: H1 (el banco de
  evals no aplica la regla nueva) y H2 (rompe la herencia de R7). Trampas: merge sí; sin DDL; importes intactos.
- C3 bis N/A: no entra ningún documento de fuera (solo un cambio interno en `dominio_negocio_albaranes.md`). Aun
  así barrí el diff (correos, IPv4, GUID, password/secret/token/key=): nada; `git log --diff-filter=A`: ningún
  pdf/docx/xlsx/pptx.
- C4 [x] cada requisito tiene test y pasan · [x] sin red ni BBDD (sqlite y sesión simulada) · [x] T21–T24 en
  `current.md`, con comandos en el informe §6 · [ ] **verificación real**: H3.
- C4 bis [x] rigor declarado · [x] fase RED con trazas reales por tarea (R28 contra `dev`; dos tests de T15
  nacieron verdes, declarado) · [x] cobertura 98,3 % · [x] mutación: recalculé alcance y mutantes con
  `harness.alcance` y `generar_mutantes` → **13 ficheros, 456 líneas, 57 mutantes**, lo mismo que el informe; los de
  sv6 que miré (`settings.py:75`, `partida_matcher.py:54/98/106`, `valuation_builder.py:1279-1344`) existen con
  ese operador y ese texto · [x] campaña de 857,5 s (> 60 s): **no la reejecuté**; recálculo puro + RM1–RM6 · [x]
  coste por mutante 857,5 × 1 / 57 = 15,0 s · [x] sin «NO VÁLIDA», 0 sin veredicto · [x] RM1: medida en
  `d707e9c`; hasta HEAD solo cambian `progress/` y `tasks.md` · [x] RM2: 57 × 15,0 ≈ 857,5; media 15,0 s frente a
  bases de 8,8/24,7 s, en serie: coherente · RM3: no hay equivalentes · [x] RM5 N/A (0 supervivientes,
  0 equivalentes) · [x] RM6: el superviviente de la primera campaña se cerró con un test, sin quitar guardas.
- tasks.md: T1–T20 y T25 `[x]` con commits `F-051 Tn:`; T21–T24, del humano.

## Cobertura requisito → test (`test_f051_*`)

| R | Test |
|---|---|
| R1–R9, R28 (sv6) | `r1_*`, `r2_*`, `r3_*`, `r4_*` (5), `r5_*` (4), `r6_*`, `r7_*` (4), `r8_*` (con `r8_r9_worker_y_api_cablean_los_ajustes`), `r9_*` (4), `r28_hermana_con_partida_no_se_copia` |
| R10–R23 (sv4) | `r10_*`, `r21_*`, `r11_*` (mapa, legado, detalle, plantilla), `r12_*` (+ el de JS débil, H3), `r19_*`, `r20_*` (3), `r13_*`, `r17_*` (4), `r22_*` (3), `r14_*`–`r16_*`, `r18_*` (6), `r23_*` (4), `endpoint_*` (4) |
| R25–R27, R29, R30 | `test_f051_prompt_partida.py` (23) + evals T21 y MANUAL T23 (del humano) |
| R24 | ARCHITECTURE regla 16 y dominio §10.8 dicen lo que hace el código (comprobado) |

## Cambios requeridos

1. **H1** — `evals/procesos/sv6_build.py:53-57`: añadir `ALMACEN_SIN_PARTIDA = True` y `FAMILIAS_DESTINADAS =
   "hormigon,mortero,combustible,alquiler_maquinaria,residuos"` y pasarlos en `_construir_builder`
   (`almacen_sin_partida=` y `familias_destinadas=familias_destinadas_de_csv(...)`). Añadir un test que falle si se
   separan de los valores por defecto de `Settings`, o meter el fichero en la parametrización de
   `test_f051_r8_r9_worker_y_api_cablean_los_ajustes`. RED en el informe.
2. **H2** — `static/app.js:1168` y `:1230`: enviar `codigo_partida` solo si el input cambió respecto a su
   `defaultValue` (vaciado ⇒ `""`; sin tocar ⇒ `null`). R12 se mantiene y guardar sin tocar no mueve la partida.
3. **H3** — Reescribir `test_f051_r12_guardar_la_fila_envia_la_partida_vaciada` para que falle con `v || null` en
   cualquiera de los dos sitios y con el envío sin condición. Control negativo en rojo pegado en el informe.
4. **H4** — `azure-apps/albaranes.md:163-164`: la lista correcta de `partida_action` (`alm_new_line_created`,
   `almacen_sin_partida`, `almacen_elegido`; `alm_acopio` es el `origen` de la derivada) y «`codigo_partida_final`
   vacío = almacén (F-051)». Commit en `azure-apps`.
5. **H5** — Una línea en `impl_F-051.md` §2 que dictamine la excepción de R20 fuera de almacén (o limitarla).
6. **H6** — `impl_F-051.md` §2.6: la instrucción pasa a ser `cmd /c rmdir services\albaranes-front\.venv`, que se
   ejecuta antes de borrar el worktree.

## Para el humano (decisiones; no bloquean)

- **Input de partida en filas no almacén**: hoy pinta la de la casada, no la final (es el origen de H2).
  Recomiendo pintar la final, como ya se hace en almacén. Es un cambio aparte.
- **O1**: elegir una línea de contrato en una línea en almacén la deja en almacén. **O2**: el `confirm()` «pasará a
  NUEVA» puede saltar sin motivo. Probarlo en T24.
- Guardar una fila (también al vaciarla, R12) pone `review_required = FALSE`, como todo guardado de antes; la
  opción y el botón de almacén no tocan la revisión (R14).
- La spec de F-053 hay que reescribirla con D1 v4 antes de implementarla. F-049 bloque C: ver arriba.

**Automejora (propuesta):** si una feature añade un ajuste o un parámetro de constructor, el design lista todos los
puntos de composición (`composition.py`, `api/app.py`, `evals/procesos/*`) y un test los recorre (H1).
