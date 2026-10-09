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
