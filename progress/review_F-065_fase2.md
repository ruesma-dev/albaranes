<!-- progress/review_F-065_fase2.md -->
Revisión incremental desde 6748c63 (pasada 2) hasta `fb4944c`; la pasada 1 fue completa, de `8c180b0` a `2783230`

# F-065 · fase 2 (R24–R28 + decisiones del humano del 2026-10-11) · review

- **Veredicto (pasada 2, abajo): CHANGES_REQUESTED** por CR3. En la pasada 1 lo fue por CR1 y CR2, ya resueltos.
- **Nivel de rigor:** `critico` (declarado). Exige fase RED, cobertura ≥ 80 %, mutación con 0 supervivientes sin
  justificación aceptada y MANUAL con su comando exacto.
- Servicio: solo sv4. Sin DDL, sin tocar `sigrid_lookup_client.py` ni la ruta `/api/sigrid/partidas` (LÍMITE DE
  SERVICIO respetado: el front consume el endpoint tal cual, con la forma que F-049 conservará).

## Verificación ejecutada por el reviewer (resultado real)
- `bash harness/init.sh`: **exit 0**, `ENTORNO LISTO`; raíz `1083 passed`; `PUERTA COBERTURA: 100.0% de 33 líneas
  cambiadas (33/33, umbral 80%, nivel critico)`. Suites relanzadas sin caché: **sv4 1061 passed**, **sv9 526 passed**.
- **Almacén total se aprueba, falseado en una COPIA** (`sv4_copia2`): hice que `_exigir_lineas_completas` tratara la
  partida final vacía como incompleta. Resultado: **10 failed**: `test_f065_almacen_nunca_impide_aprobar_aunque_esten_todas`
  (listado) y 9 de F-053 (`t19`, `t21b` por las dos vías, aprobar del listado y «Guardar y aprobar», y `t25`), cuyas
  filas ya están en almacén. Las dos vías de aprobar quedan vigiladas.
- **Mutación (RM1)**: recálculo independiente: alcance `8c180b0..feature/F-065` (`8c180b0` = `dev`), **2 ficheros, 147
  líneas, 29 mutantes** (12 + 17). Coincide con el informe. Desde el SHA medido (`488b432`) hasta HEAD solo cambian
  `progress/` y `tasks.md`. **No reejecuté la campaña: el informe declara 695,4 s** (> 60 s).
- **RM2**: 695,4 × 4 ÷ 29 = **95,9 s por mutante** frente a una línea base de 106,5–107,4 s; coherente. No hay
  «CAMPAÑA NO VÁLIDA» y «Sin veredicto» = 0. **RM3/RM5**: sin equivalentes; RM5 es N/A justificado. **RM6**: no se
  quitó ninguna guarda.
- **Prueba de sv9 sobre Contrato → Nueva** (copia `sv4_copia3` + validador real de sv9), de donde sale CR1.

## Cambios requeridos

1. **CR1 · Alta · una fila sin blanca que pasa a Nueva llega a sv9 sin descripción y el alta sale `no_admitido`.**
   Al pasar a Nueva se pone `albaran_line_valuations.descripcion_linea = NULL`; la descripción solo queda en la
   derivada. Pasa en `update_line_conciliacion` (`review_repository.py:2088`, rama Contrato → Nueva, y `:2112`, Nueva
   editada in situ) y, **nuevo en esta fase**, en «Origen ✎» → Nueva (`:1831`; antes `nueva` no tocaba la descripción).
   sv9 no lee la derivada: `_descripcion = descripcion_linea or concepto de la blanca` (`validador_alta.py`).
   - Una fila **traída del contrato** (`line_kind = 'manual'`, sin blanca) se queda sin ninguna de las dos. Es justo
     el caso de METALFIRE (traer 5 y cambiarles la partida) y en esta fase pasa sin confirmación.
   - Lo reproduje. Fila traída de la 503, partida a «09.09»: queda `descripcion_linea=None, concepto=None,
     derived=602`. El validador real de sv9 sobre esa línea devuelve `[Motivo('falta_descripcion', '', '77')]`, es
     decir, **todo el albarán `no_admitido`**.
   - El fallo es seguro (no se escribe nada mal en Sigrid), pero rompe el alta del caso que origina la feature.
   - **Qué hacer:**
     - En sv4, al pasar a Nueva o editar una Nueva **sin blanca** (`merge_line_id` nulo), escribir en
       `descripcion_linea` la descripción de la fila, la que pinta la ficha (`nuevo["descripcion"]` / la de la
       derivada), en vez de NULL. Hacerlo en las tres escrituras.
     - Añadir un test de contrato en sv9 (patrón de T10): una fila traída pasada a Nueva se admite y se manda sin
       vincular con esa descripción.
     - Con la blanca presente, sv9 manda el concepto leído (diseño de F-053, `valuation_builder.py:1407`); si debe
       mandar lo editado, decide el humano (ver H1).
     - Mismo origen: las filas «Añadir línea» (`add_standalone_valuation_line`, derivada sin blanca) están igual desde
       F-053, y el arreglo las cubre si se aplica a la rama in situ.
2. **CR2 · Menor · C4: la MANUAL T19 no está en `progress/current.md` con su comando exacto**, solo «comandos de §7
   del informe». Copiar allí los pasos y las dos consultas de solo lectura, como se hizo con T13.

## Checkpoints

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés.
- **C2** [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md` podado (O7: el bloque viejo de F-053 ya
  no está) · [x] sin `done` nuevos.
- **C3** [x] hexagonal: `cambia_origen` es pura en el dominio y el repositorio la usa · [x] primera línea con ruta ·
  [x] sin debug, secretos ni dependencias nuevas · [x] trampas (1) merge (2) sin cambio de esquema (3) ver H2.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: según la puerta, no toca rutas sensibles.
- **C4** [x] R24–R28 y O1/O2/O3/O5/almacén con tests `test_f065_*` en verde (tabla abajo) · [x] sin red ni BBDD ·
  **[ ] MANUAL T19 listada con su comando exacto en `current.md` (CR2).**
- **C4 bis** [x] rigor declarado · [x] fase RED con traza real (`29 failed, 13 passed`, §4) · [x] cobertura [OK] ·
  [x] mutación verificada · [x] muertos: recálculo puro + RM1–RM6, dicho arriba · [x] coste por mutante 95,9 s ·
  [x] sin «no válida» · [x] RM1 · [x] RM2 · [x] RM5 N/A justificado · [x] RM6 · N/A campaña manual · [x] 0
  supervivientes · [x] «Evidencias» con 4 workers. Nota: dice «1059 passed» y §5 «1061»; lo real es **1061**.
  Corregirlo de paso. La herramienta no muta el JS ni la plantilla: los vigilan los tests con node y de render (H3).
- **C5** [x] T15–T18 `[x]` con commits `F-065 Tn:` · [x] árbol limpio · [x] `features.json` = `in_progress`.

## Pasada 1: cobertura, puntos del líder y observaciones (resumen)

Íntegro en `git show 6748c63:progress/review_F-065_fase2.md`. R24–R28 y O1/O2/O3/O5/almacén con tests trazables;
`cambia_origen` correcta (P10); almacén sigue vinculada; combo solo de la lista con «Almacén» primero; «Origen ✎» única
vía; F-051/F-053 adaptados con motivo; E1, E3, E5, E6 razonables, E2 y E4 con matiz. Observaciones: H1 (descripción
editada con blanca), H2 (Origen ✎ a otra unidad sin convertir Q), H3 (combo DOM solo estructural), H4 (caché sin obra).

## Pasada 2 · revisión incremental desde `6748c63` hasta `fb4944c`

- **Veredicto pasada 2: CHANGES_REQUESTED**: CR1, CR2, H1 y H4 están resueltos; H2 queda a medias (**CR3**, alta).
- **Verificación**:
  - `bash harness/init.sh`: exit 0, raíz `1083 passed`, `PUERTA COBERTURA: 100.0% de 61 líneas (61/61)`.
  - Sin caché: **sv4 1091 passed**, **sv9 530 passed**. Árbol limpio.
- **CR1 resuelto, falseado en copias**:
  - `descripcion_para_valoracion` se aplica en las tres escrituras (`review_repository.py:1863`, `:2107` → `:2150` y
    `:2174`). «Añadir línea» queda cubierta por la rama in situ (`sin_blanca`).
  - Falseo en sv4 (la función devuelve siempre `None`): `test_f065_f2_pasada2.py` ⇒ **8 failed**.
  - Falseo en sv9 (`_descripcion` solo con el concepto): `test_f065_partes.py` ⇒ **2 failed**. Uno es `no admitida:
    [Motivo('falta_descripcion', ...)]` y el otro `'PORTES' == 'PORTES URGENTES'`. El validador es el real.
- **H1 resuelto sin tocar sv9**:
  - El diff de sv9 es solo `tests/test_f065_partes.py`. `_descripcion` ya prefería `descripcion_linea`.
  - `SQL_LINEAS`, la previa y el comparador de F-053 no cambian, y sus 530 tests están en verde.
  - Con blanca y sin editar sigue yendo lo leído (`ya_fijada` / `editada`).
- **H4 resuelto**: caché por obra, sin obra no se guarda y otra obra se vuelve a pedir; test con node. **CR2 resuelto**:
  T19 está en `current.md` con pasos, las dos consultas de solo lectura y el criterio.
- **H2, lo que está bien**:
  - `cantidades_tras_reapuntar`: con la unidad nueva = la del albarán, Q = ca y factor 1. Misma unidad o desconocida:
    nada cambia.
  - Otra unidad: cantidad intacta, fila sin bloquear, `review_required` y el motivo
    `front_unidad_cambiada_revisa_cantidad` (los de sv6 se conservan). El aviso es visible en la celda de cantidad y se
    limpia al cambiar la cantidad o al «Guardar».
- **Mutación (RM1)**:
  - Recalculé `8c180b0..rama`: **2 ficheros, 276 líneas, 54 mutantes** (28 + 26). Coincide con el informe.
  - Desde `9da7e4b` solo cambia `progress/`. **No reejecuté la campaña: dura 1138,4 s según el informe**.
  - RM2: 1138,4 × 4 ÷ 54 = **84,3 s por mutante** frente a una línea base de 87,0–87,5 s; coherente.
  - Ni «no válida» ni «sin veredicto». Los 4 supervivientes de la campaña intermedia eran huecos de test, no
    equivalentes. RM5 N/A, RM6 sin guardas quitadas.

### CR3 · Alta · una fila marcada «revisa la cantidad» se aprueba y sv9 la manda con la cantidad incoherente

- **Lo pedido**: que sv9 no admita una fila marcada así si la cantidad quedó incoherente. Nadie mira la marca:
  - ni `_exigir_lineas_completas` (los dos aprobar);
  - ni sv9 (`validador_alta` no lee `review_required` ni `review_reasons_json`).
- **Reproducido en una copia** (`sv4_copia4`):
  - Fila 11, `unidad_albaran = 'KG'` y `unidad_contrato = 'UD'`. «Origen ✎» a la 503, que va en `TN` a 90.
  - Queda `cc = 8`, `importe = 720`, `review_required = 1` y el motivo puesto, sin bloquear.
  - `set_approved(True)` ⇒ **`True`**. El validador real de sv9, con esa fila vinculada, devuelve
    `PeticionAlbaran [(8.0, 90.0, 700101)]`: 8 t donde había 8 ud.
- **Qué hacer**:
  - En sv4, igual que R20/O2: mientras alguna fila tenga `MOTIVO_UNIDAD_CAMBIADA`, aprobar (ficha y listado) lanza
    `LineasIncompletasError` con su posición y un aviso propio, p. ej. «Líneas con la unidad cambiada: revisa la
    cantidad: 3».
  - Tests por las dos vías, y otro de que, quitada la marca (cantidad cambiada o «Guardar»), se aprueba.
  - sv9 no cambia: aprobar es la puerta de entrada al alta.

### Observaciones de la pasada 2 (no bloquean)

- **P2-1 · Baja.** Un «Guardar» sin cambios quita el motivo pero deja `review_required = TRUE`
  (`review_repository.py:2037-2047`). Con cambios sí lo baja. Conviene bajarlo también.
- **P2-2 · Baja.** Si la fila no tiene unidad (ni la suya ni la de su línea), reapuntar a otra unidad no avisa
  (`cantidades_tras_reapuntar`, «desconocida»). Es raro, pero es justo el caso silencioso. Propuesta: avisar también
  cuando la actual es desconocida y la nueva no es la del albarán.
- **C4 / C4 bis de la pasada 2**:
  - [x] RED con traza (`13 failed, 8 passed`, sv9 roto en copia: `2 failed`); [x] cobertura; [x] mutación;
    [x] Evidencias; [x] T19 en `current.md`.
  - **[ ] H2 incompleto (CR3)**.

## Automejora (propuesta, no aplicada)

- `reviewer.md`, entre las comprobaciones de rigor `critico` que afectan a sv9: «pasar la fila resultante por
  `validar_y_construir` de sv9». Aquí destapó CR1, que ningún test de sv4 podía ver.
