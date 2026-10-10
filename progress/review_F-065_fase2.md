<!-- progress/review_F-065_fase2.md -->
Revisión completa (pasada 1) de la fase 2, desde `8c180b0` (dev con la fase 1) hasta `2783230` (HEAD)

# F-065 · fase 2 (R24–R28 + decisiones del humano del 2026-10-11) · review

- **Veredicto: CHANGES_REQUESTED.** Dos cambios: CR1, alta, y CR2, menor. Lo demás está bien hecho y verificado.
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

## Cobertura requisito → test

| R / decisión | Tests (`test_f065_f2_origen.py` salvo indicación) |
|---|---|
| R24 «Contrato» | `test_f065_r24_plantilla_*` (editable y solo lectura) |
| R25 partida/precio/unidad ⇒ Nueva, sin confirm | `test_f065_r25_dominio_cambia_origen` (10 casos), `..._hacen_nueva_la_fila_contrato` (×3), `..._ya_no_pregunta_si_pasa_a_nueva` |
| R26 almacén / la de su línea / lo demás no cambia | `test_f065_r26_*` (×4, incl. `cambia_origen(` en el repositorio) |
| R27 combo de la obra | `test_f065_r27_js_*` (respuesta, Almacén primero y filtro, solo de la lista, flechas) y estructurales (endpoint, aviso, Enter antes que Guardar) |
| R28 «Origen ✎» única vía | `test_f065_r28_*` (×7: copia partida/unidad/precio, Nueva con valores actuales, bordes, concepto sin combo) |
| O1, O2, O3, O5, almacén | `test_f065_o1_*`, `test_f065_o2_*` (×2), `test_f065_o3_*` (×2), `test_f065_o5_*`, `test_f065_almacen_*` |

## Lo que pidió el líder

- **`cambia_origen`**: correcta y exhaustiva. Partida distinta de la de su línea, precio o unidad ⇒ Nueva. Vaciar
  (almacén) o volver a la de su línea no cambia el origen (P10), ni descripción, cantidad, descuento o código. Una
  Nueva sigue Nueva.
- **Para sv9**:
  - La Contrato que pasa a Nueva queda sin vincular (`matched` nulo, derivada `manual_override` con partida, unidad y
    precio), con el producto genérico de F-053 y `precio = importe / ca`. Falla la descripción en las filas sin
    blanca (**CR1**).
  - La fila en almacén conserva `matched_contrato_line_id`: sigue vinculada con `partida = None` (F-051).
- **Combo de partidas**:
  - Solo admite valores de la lista: con otro texto, al salir vuelve al de antes. «Almacén» siempre va primero.
  - Obra sin partidas, `ok: false` o red caída ⇒ solo «Almacén». En los dos últimos casos sale además el aviso.
  - Una sola carga por ficha.
- **«Origen ✎» única vía**: el combo de concepto y el reapunte desde la partida desaparecen. Las únicas llamadas
  `PATCH .../conciliacion` con `mode` son el selector de «Origen ✎» y el «+» de una blanca sin fila (que crea, no
  reapunta).
- **Almacén total se aprueba**: lo falseé arriba. Las huérfanas (O2) bloquean con «revalora», y sv6 garantiza que no
  nacen (`valuation_builder.py:1131-1180`).
- **Tests adaptados**:
  - F-051: los de `cambiaIdentidad` y `data-partida-casada` se retiran con la regla. Sus casos (la de la casada,
    otra, vaciar, casada sin partida, unidad) los cubren `cambia_origen` y sus tests.
  - F-053: el fixture pone su derivada a las sin vincular, como hace sv6. `t25` deja claro que «valorado» y «aprobable»
    ya no coinciden con una huérfana.
  - Todo está justificado.
- **E1–E5**:
  - Razonables: E1 (coherente con guardar = bloquear y con «solo manda `codigo_partida`»), E3 (como D3), E5 (fallo
    seguro, igual que `SQL_LINEAS` de sv9) y E6 (SQLite ≥ 3.43 suma con compensación; vale el estructural).
  - Razonables con matiz: E2 (H2) y E4 (H4).

## Observaciones (no bloquean)

1. **H1 · Decisión del humano.** Con blanca, sv9 manda como descripción de una sin vincular el concepto leído del
   albarán, no la descripción editada en la ficha. Así lo diseñó F-053 y la fase no lo cambia. Decidir si «lo aprobado
   es lo que se ve» incluye la descripción.
2. **H2 · Media · E2.** «Origen ✎» a una línea de otra unidad copia la unidad y el precio, pero **no convierte Q**
   (`review_repository.py:1753-1773`). Si la fila tenía kg y la línea elegida va en t, el importe sale ×1000. Es un
   riesgo previo: antes ni siquiera se cambiaba la unidad. R21 lo avisaría al aprobar. Propuesta: si la unidad cambia,
   avisar en la ficha o dejar la fila marcada para revisar la cantidad.
3. **H3 · Baja.** El comportamiento DOM del combo (blur que revierte, Esc, Enter) se vigila solo con tests
   estructurales; la lógica pura sí corre con node. La MANUAL T19 cubre lo demás. Opcional: un test de «Guardar y
   aprobar» con todo en almacén por la vía del PUT, aunque hoy ya lo cazan los de F-053.
4. **H4 · Baja · E4.** `cargarPartidasObra` guarda en caché la primera respuesta de la página. Si el combo se abre
   antes de elegir la obra, se queda solo con «Almacén» hasta recargar. Basta con no guardar la carga «sin obra».

## Automejora (propuesta, no aplicada)

- `reviewer.md`, entre las comprobaciones de rigor `critico` que afectan a sv9: «pasar la fila resultante por
  `validar_y_construir` de sv9». Aquí destapó CR1, que ningún test de sv4 podía ver.
