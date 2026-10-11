<!-- progress/review_F-065_fase2.md -->
Revisión incremental desde 1942485 (pasada 3) hasta `f45d297`; la pasada 2, de `6748c63`; la 1, completa desde `8c180b0`

# F-065 · fase 2 (R24–R28 + decisiones del humano del 2026-10-11) · review

- **Veredicto (pasada 3, abajo): APPROVED.** Antes: pasada 1 CHANGES_REQUESTED (CR1, CR2) y pasada 2 (CR3), corregidos.
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

## Pasada 2 · incremental desde `6748c63` hasta `fb4944c` (resumen)

Íntegra en `git show 1942485:progress/review_F-065_fase2.md`. CHANGES_REQUESTED por **CR3**. CR1 y H1 quedaron
resueltos y verificados: falseado en copias, 8 tests fallan en sv4 y 2 en sv9 contra el validador real; sv9 sin cambios
de código. CR2, H4 y H2 (conversión hacia la unidad del albarán, aviso visible) también quedaron resueltos. CR3: una
fila con la marca «revisa la cantidad» se aprobaba y sv9 la admitía. Caso reproducido: 8 ud mandadas como 8 t,
`PeticionAlbaran [(8.0, 90.0, 700101)]`. Observaciones bajas: P2-1 (`review_required` tras quitar la marca) y P2-2 (fila
sin unidad).

## Pasada 3 · revisión incremental desde `1942485` hasta `f45d297`

- **Veredicto pasada 3: APPROVED.** CR3, P2-1 y P2-2 corregidos; no quedan cambios requeridos de la fase 2.
- **Verificación**:
  - `bash harness/init.sh`: **exit 0**, raíz `1083 passed`, `PUERTA COBERTURA: 100.0% de 66 líneas (66/66)`,
    `ENTORNO LISTO`.
  - Sin caché: **sv4 1104 passed**. sv9 no cambia desde la pasada 2, donde dio 530 passed. Árbol limpio.
- **CR3, mi caso reproducido sobre el código actual** (copia `sv4_copia5`, el mismo 8 ud → 8 t):
  - Aprobar desde el listado ⇒ `LineasIncompletasError` «Líneas con la unidad cambiada: revisa la cantidad: 1».
  - «Guardar y aprobar» (PUT) ⇒ el mismo rechazo.
  - En los dos casos el documento sigue sin aprobar.
  - Tras «Guardar» la fila, la marca se va y `set_approved` ⇒ `True`.
- **CR3 falseado**: quitar la comprobación de `_exigir_lineas_completas` (`review_repository.py:3855-3857`) ⇒ **4
  failed**. Son `test_f065_cr3_con_la_marca_no_se_aprueba[listado|guardar_y_aprobar]` y mis dos casos: las dos vías
  quedan vigiladas.
- **P2-1**: el «Guardar» que quita la marca baja `review_required` solo si no queda ningún otro motivo (`:2045`).
  - En mi caso queda a 1 porque sv6 dejó `ia_match_trusted`, que es lo acordado: sv4 no toca los motivos ajenos.
  - Ese motivo es informativo, así que el humano puede querer que no cuente. Queda anotado, no bloquea.
- **P2-2**: si la actual se desconoce y la nueva no es la del albarán, avisa; si es la del albarán, convierte. Lo
  cubren los tests de dominio y de repositorio, con la traza RED `:426`/`:437`.
- **Mutación (RM1)**:
  - Recalculé `8c180b0..rama`: **2 ficheros, 301 líneas, 58 mutantes** (28 + 30). Coincide con el informe.
  - Desde el SHA medido (`ead57a4`) solo cambian `progress/` y el inventario.
  - **No reejecuté la campaña: dura 1071,2 s según el informe** (> 60 s).
  - RM2: 1071,2 × 4 ÷ 58 = **73,9 s por mutante** frente a una línea base de 66,0–66,5 s (1,1×). No hay salto de orden
    de magnitud.
  - 0 supervivientes, ni «no válida» ni «sin veredicto». RM5 N/A sin equivalentes; RM6 sin guardas quitadas.
- **Checkpoints de la pasada 3**:
  - [x] C1 · [x] C2 · [x] C3: el aviso nuevo vive en el dominio y el repositorio solo lo usa · C3 bis / C4 ter N/A
    (sin `docs/referencia/` ni rutas sensibles).
  - [x] C4: CR3, P2-1 y P2-2 con tests en verde; T19 en `current.md` · [x] C4 bis: RED `8 failed, 35 passed`,
    cobertura 66/66, mutación 58/58 verificada, Evidencias con 4 workers · [x] C5.
- **Para cerrar la fase 2** (humano): la MANUAL T19 de `current.md`. Al paso 4 conviene añadir «Guardar y aprobar» con
  la fila marcada, que debe rechazarse. Después: fusionar, `init.sh` en el árbol principal y desplegar solo sv4.

## Automejora (propuesta, no aplicada)

- `reviewer.md`, entre las comprobaciones de rigor `critico` que afectan a sv9: «pasar la fila resultante por
  `validar_y_construir` de sv9». Aquí destapó CR1, que ningún test de sv4 podía ver.
