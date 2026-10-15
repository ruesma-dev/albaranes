# F-065 · informe del spec-author (spec v1, 2026-10-09)

Feature: **las líneas editadas en sv4 se respetan, cambiar la partida no rompe el vínculo y una línea se reparte**
· prioridad 1 · rigor `critico` · servicio `sv4-front`. Estado: **`spec_ready`** a falta de la PARADA 1 (P1–P9).

## 1. Qué hay en la rama

Rama `feature/F-065-lineas-editadas-y-reparto` (worktree `../albaranes-F-065`, desde `dev` b380b43). Un commit de
spec, sin código:

- `specs/F-065-lineas-editadas-y-reparto/requirements.md` (R1–R32, 142/150 líneas), `design.md` (164/250),
  `tasks.md` (T0–T28 en tres fases). `python -m harness.tamano --feature F-065`: dentro de los topes.
- `harness/features.json`: ficha F-065 (`spec_ready`, prioridad 1, `critico`, `sv4-front`, rama). F-016 con el
  prefijo «[ABSORBIDA POR F-065]» y el motivo (sigue `pending`, como F-013: no hay estado «absorbida»).
- `BACKLOG.md` regenerado; `progress/explore_F-065.md` (diagnóstico del líder) entra en el mismo commit.
- **Conflicto previsible** con la rama de F-064 (`../albaranes-F-064`), que también añade una ficha al final de
  `features.json` y regenera `BACKLOG.md`: al fusionar, conservar las dos y regenerar.

## 2. Hallazgos que añade la spec al diagnóstico

1. **La cantidad de la fila salmón está en la unidad del precio.** La ficha y el PATCH usan
   `cantidad_convertida ?? cantidad_albaran` (`review_repository.py:4705-4720`, `1948-1954`;
   `document_detail.html:943`) y el importe es `precio × esa cantidad`. Por eso «arreglar» `cantidad_convertida`
   no es recalcularla con el factor: lo tecleado YA es la convertida; lo que hay que derivar es la del albarán
   (R5: `Q/factor` si la conversión es reproducible, `Q` si no hay conversión, la de antes si la regla es de sv6).
2. **«Guardar todas» corrompe líneas con conversión aunque nadie las toque** (lectura de código; T1 lo fija en
   RED). Re-guarda todas las filas: copia la convertida en `cantidad_albaran` y anula la convertida
   (`review_repository.py:2083-2100`); el siguiente PUT recalcula con la cantidad de la blanca en la unidad del
   albarán (`3898-3943`): **×1000** en una línea kg→t y **×6** en contenedores de residuos (el bug de F-036 por
   otra puerta). También reetiqueta como `calculated` importes declarados que nadie tocó. R5–R7 y R11 lo cierran.
3. **sigrid-api ya admite lo que pide la usuaria.** `contrato_albaranes.md` (F-009 v8, leído en solo lectura,
   sin editar): una vinculada con `partida` ≠ la del `ctrpro` se graba con `paride` = la pedida y aviso
   informativo `partida_distinta_del_contrato` (M4: el 5,3 % del escritorio ya lo hace); varias líneas al mismo
   `ctrpro` son varias `dcapro`, no se suman. **No hace falta propuesta a sigrid-api.** Lo que lo impide hoy es
   la regla SIGRID→NUEVA de sv4 (junio de 2026).
4. **sv9 y comun no necesitan código**: sv9 ya lee las filas de `merge_line_id` nulo y decide «vinculada» sin
   mirar `line_kind`. Las partes salen al final de la petición (orden de presentación, sin efecto contable).
5. **F-016 se reparte entre dos**: su caso real (Feymaco, anotación compuesta «P4/P5.36.01») lo resuelve F-049 R23
   en sv2 de forma automática; el reparto a mano es la fase 3 de F-065. Por eso se marca absorbida.

## 3. Decisiones abiertas (PARADA 1). Recomendada en negrita

- **P1 · ¿Se admite una línea vinculada a un `ctrpro` imputada a otra partida?** Técnicamente sí (punto 3). Es
  pregunta de negocio: la medición servida del `ctrpro` se consume aunque la línea vaya a otra partida.
  **(A) Sí**: cambiar la partida deja la fila SIGRID y el reparto conserva el vínculo (R13, R24, R25).
  (B) No: cambiar la partida = NUEVA con confirmación en todos los guardados, y el reparto solo dentro de la
  partida de la línea casada (o con NUEVAS); habría que rehacer las fases 2 y 3.
- **P2 · Qué hace el PUT con las blancas.** **(a) Recalcula solo las que cambiaron respecto al merge guardado**
  (R1; defensa para cualquier cliente que sí edite la blanca). (b) Deja de recalcular desde el PUT (hoy las
  blancas son de solo lectura en la UI); más simple, pero un cambio real de blanca ya no movería la valoración.
- **P3 · Regla de cantidades al editar la salmón.** **Q = convertida siempre; la del albarán por (a)/(b)/(c) de
  R5.** Alternativa: no dejar editar la cantidad en filas con conversión no reproducible (contenedores).
- **P4 · Modelo de las partes del reparto.** **M1: filas `line_kind = 'reparto'`, `merge_line_id` nulo,
  `parent_merge_line_id` = la blanca; sin DDL**, mismo mecanismo que las líneas `manual` de «Traer líneas
  contrato». M2: igual con columna `reparto_de_id` (DDL en sv6 y sv3, despliegue sv6/sv3 → sv4; trazabilidad
  explícita). M3: partir la blanca en el merge como F-049 R23 (sobrevive a revalorar sin F-058, pero cambia lo
  leído, el re-fetch lo deshace y IA3 vuelve a casar cada parte).
- **P5 · Si la suma no cuadra.** **Al dividir, 422 y sin cambios (R21); después, si se edita una parte, aviso no
  bloqueante en la ficha (R29)**, porque una recepción parcial es legítima. Alternativa: bloquear la aprobación.
- **P6 · Importe de cada parte.** **Prorrateo del importe original; la última absorbe el redondeo y el total del
  albarán no cambia (R26).** Alternativa: fórmula por parte (`precio × qk × (1 − dto)`), que puede mover el total
  unos céntimos frente a un importe declarado.
- **P7 · Revalorar.** **F-065 solo avisa antes de «Valorar ahora» y «Guardar y volver a buscar» (R31) y F-058 se
  amplía a partes y cantidades editadas.** Alternativa: que F-065 haga sobrevivir el reparto (exige M2/M3 y sv6).
- **P8 · F-016.** **Absorbida** (ya aplicado en su ficha; se revierte si el humano prefiere solo referenciarla).
- **P9 · Fases.** **Tres fases dentro de F-065, una review cada una; la fase 1 se despliega sola (solo sv4) antes
  de poner `ALTA_SIGRID_DESDE`.** Alternativa: sacar el reparto (C) a una ficha propia.

## 4. Orden y dependencias

- F-053 sigue `in_progress` (máximo una): F-065 no puede pasar a `in_progress` hasta que F-053 cierre o el humano
  decida otra cosa. **El despliegue de F-053 con `ALTA_SIGRID_DESDE` debería esperar a la fase 1 de F-065.**
- Datos ya dañados (filas editadas antes del despliegue) no se reparan: sv9 las deja en `no_admitido`
  (`cantidad_sin_convertir`, fallo seguro) y basta con volver a guardar la fila. El albarán de METALFIRE lo
  corrige la usuaria a mano.

## 5. Para el líder

- Validar con el humano P1–P9 (P1 es la única de negocio pura; conviene preguntarla a Administración).
- Tras la PARADA 1, si cambia alguna P, reescribir los R que la citan (requirements, cabecera).
- F-058: al especificarla, incluir las partes `reparto`, las `manual` y las cantidades editadas en sv4.

---

## v2 · tras la PARADA 1 (2026-10-09)

La rama trae `dev` fusionado (ae86bfb; F-053 pasó a `blocked`, así que F-065 podrá ir a `in_progress`). Entran en el
commit `progress/propuestas_ficha_detalle.md` (tabla M/X/R/O y modelo del humano) y `progress/explore_front_detalle.md`
(inventario de la ficha, F1–F25). La v1 de arriba queda como historia: **P1 y el bloque B de la v1 están revocados**
(la v1 dejaba la fila vinculada al cambiar la partida; el humano decidió lo contrario).

### Modelo del humano y respuestas

- Origen «Sigrid» ⇒ **«Contrato»**: lo es si cuadran partida, unitario y concepto (equivalencia de significado,
  la decide la IA al valorar); si no, **Nueva**.
- (1) **Cambiar la partida ⇒ Nueva.** (2) Al editar **no se llama a la IA**: la descripción no reevalúa el origen; si
  hace falta, el usuario lo cambia a mano («Origen ✎»). (3) **Aprobar no exige líneas bloqueadas.** (4) Combo con
  **todas las partidas hoja de la obra** + «Almacén»; obra sin partidas ⇒ solo «Almacén».
- Lo que cambia el administrativo pisa lo valorado; ningún guardado vuelve a lo valorado. **P2 = separar guardados**:
  el PUT de cabecera no toca las líneas. Guardar una línea la **bloquea**; se desbloquea a mano.
- Alcance: filas «F-065» de la tabla (M1–M4, X1–X3, X5–X11, X22, R6) **menos X4**; sumatorio X12 a F-066.

### Qué cambia en la spec (requirements 149/150, design 159/250, tasks T0–T28)

- **Fase 1 (R1–R23), sv6 → sv4**, se despliega sola antes de pasar F-053 a real: PUT sin líneas y sin
  desaprobar (R1–R3; se retiran `_recalc_valuation_importes` y los mapas del payload, R11); **aprobado = solo
  lectura** con «Desaprobar para editar» y 409 en toda escritura (R4–R5); PATCH **solo de los campos cambiados**,
  con cantidades coherentes (R6–R8, la regla P3 de la v1) y **precio aplicado** en filas Contrato (R9, F3 del
  inventario); **guardar = bloquear** (R13–R17, columna `bloqueada` con DDL en sv6 + sentencia defensiva en sv4);
  «Guardar todas» solo filas sucias (R18); aviso de filas sin guardar (R19); **no se aprueba con filas sin cantidad
  o importe** (R20) y confirmación si la suma no cuadra con lo leído (R21); confirmación antes de revalorar o
  cambiar de contrato (R22); traer líneas de contrato con cantidad (R23).
- **Fase 2 (R24–R28), sv4**: «Contrato»; partida/unitario/unidad ⇒ Nueva **sin confirmación**; combo de partidas de
  la obra; «Origen ✎» única vía de reapuntar (copia partida y precio de la línea elegida); concepto como texto.
- **Fase 3 (R29–R36), sv4 + test de sv9**: F6 dividir (sustituye a F7); partes `reparto` sin DDL (M1); la parte
  con otra partida sale Nueva (respuesta 1), con la misma o en almacén conserva el vínculo.
- **Servicios**: `sv4-front` y `sv6-valoracion-persist` (solo DDL). sv9 y comun sin código.
- **Partidas de la obra (LÍMITE DE SERVICIO)**: se reutiliza el endpoint de sv4 que ya existe
  (`GET /api/sigrid/partidas`, hojas de `obrparpar`, hoy sin uso). No se mueve nada a comun: lo hace F-049 (rama
  sin fusionar, T1/T16/T17), y el endpoint conserva su forma; F-065 no toca `sigrid_lookup_client.py`.

### Decisiones nuevas, tomadas por defecto (design §7; a confirmar por el humano)

- **P10** Vaciar la partida (almacén) o volver a la de la línea casada **no** cambia el origen (F-051 D4 y R20,
  decisiones del humano del 2026-10-05). Si con el modelo nuevo almacén debe ser Nueva, solo cambia `cambia_origen`.
- **P11** El combo solo admite partidas de la lista (sigrid-api rechazaría otra); con Sigrid caído, solo «Almacén».
- **P12** R20 **bloquea** aprobar con filas sin cantidad o importe (hoy sv9 no las manda y se pierden en silencio).
- **P13** Desbloquear una línea no exige permiso especial.

### Backlog (en este commit)

- **F-066** «Edición de líneas tipo hoja de cálculo en la ficha de detalle» (X12–X21, R4): `pending`, prioridad 1,
  `critico`, sin spec; depende de F-065.
- **F-067** «Limpieza de la ficha de detalle» (X25, X26, R1–R3, R5, R7–R12): `pending`, prioridad 1, `estandar`,
  sin spec; lleva las notas de **X4** (fuera de F-065, pendiente de sitio) y **O2** (consulta de solo lectura de
  líneas ya dañadas en producción).
- **F-058** y **F-059** a prioridad 1, con X23 y X24 en su descripción (F-058 incluye ahora líneas bloqueadas,
  cantidades editadas, traídas y partes de F6).
- F-016 sigue absorbida (P8). F-065 sigue `spec_ready` y pasa a `servicios` `sv4-front` + `sv6-valoracion-persist`.

### Para el líder

- Confirmar con el humano P10–P13 en la siguiente conversación (no bloquean empezar la fase 1, salvo P12).
- Conflictos previsibles: `features.json`/`BACKLOG.md` con F-064; `review_models.py`, `app.py` y la plantilla con
  F-049 (bloque C toca sv4).
