<!-- progress/current.md -->
# Trabajo en curso

## Sesión 2026-08-18 — spec de F-027 escrita (esperando aprobación humana)

> Escrita en el worktree de `dev` (`scratchpad/wt-dev`), porque el árbol
> principal está ocupado por la rama `feature/F-019-importe-unitario-manda`.

- **F-027 `spec_ready`** (era `pending`). Spec en
  `specs/F-027-conversion-kg-tn-muerta/` (`requirements.md` 27 requisitos
  EARS, `design.md`, `tasks.md` 11 tareas). Rigor **critico**. Rama prevista:
  `feature/F-027-conversion-kg-tn-muerta`. Toca **solo sv6**. **NO se ha
  escrito código.**
- Fuente del diagnóstico: `progress/revision_resto_lote_20260818.md` §4.1 y
  hallazgo H-1.

### Qué dice la spec, en corto

- **Causa raíz confirmada de primera mano**, ejecutando el código real de
  `dev` sin BBDD ni red: `ValuationBuilder` llama al conversor con
  `cantidad=None` cuando las categorías de unidad no casan
  (`valuation_builder.py:1020-1025`), y `UnitConverter.convert` sale por la
  guarda `cantidad is None` **antes** de la red de plausibilidad de toneladas.
  Con la cantidad real, el mismo código devuelve `30.38 TN` y factor `0,001`.
- **Diseño elegido: convertir primero, decidir revisión después.** Se elimina
  la rama `else` (cinco líneas) y `category_match=False` pasa a marcar
  revisión sin anular la cantidad. Argumento que decide: el conversor **ya
  se niega** a cruzar categorías incompatibles (`convert(108,'UD','M3')`
  devuelve `None`), así que cegarlo no protegía de nada — solo mataba las
  redes del caso `unknown`. Descartadas: un guard previo de TN (arregla el
  síntoma, deja muertas las demás redes) y pasar `category_match` al conversor
  (amplía su contrato para decir algo que ya sabe decir).
- **Segunda mitad del mismo ×1000, incluida en el alcance**: cuando hay línea
  de contrato derivada, el builder convierte a `unidad_albaran`, pero la
  derivada suele llevar la unidad **y el precio** del contrato
  (`partida_matcher.py:263-266`). Con albarán en `KG` y contrato en `TN` eso
  da factor 1 contra un precio por tonelada: el mismo error, vivo hoy y sin
  que la IA falle. Es además el escenario que **F-024 activa** en cuanto IA1
  extraiga la unidad.
- **Honestidad sobre lo que arregla**: F-027 elimina el factor 1000, no el
  error entero. El 58826 queda en **468,76 €**, no en los 390,99 € del ground
  truth; los 77,77 € que faltan son el precio de contrato equivocado (15,43
  en vez de 12,87), que es **F-031**. Los requisitos fijan los dos números
  para poder distinguir qué feature produce cada euro.
- **Regresión blindada**: hormigones en m³, ferretería en unidades y el
  A261584 de VODALAND (3.393,00 €, el único total correcto del lote) deben
  dar exactamente lo mismo. Medido: en esos casos el conversor devuelve la
  misma cantidad con factor 1; lo que cambia es el motivo, que pasa a ser
  cierto.

### Decisiones abiertas que necesita validar el humano (F-027)

1. **D2** — ¿se acepta convertir también cuando IA3 declaró
   `unidad_category_match=false` pero las unidades son convertibles de verdad
   (`KG`→`TN`)? La alternativa es seguir respetando ciegamente ese juicio, que
   es lo que hoy produce el ×1000.
2. **D3** — ¿se confirma el umbral de 1000 para reinterpretar KG→TN? Riesgo
   aceptado: un albarán legítimo con ≥ 1000 unidades contra un contrato en TN
   se dividiría por 1000 (siempre marcado para revisión). Los dos umbrales ya
   son parámetros de constructor: ajustarlos no exige tocar código.
3. **F-025 pierde su caso principal** — al desaparecer la rama que pasaba
   `cantidad=None`, el motivo falso `no_quantity_in_albaran` deja de emitirse
   solo. ¿F-025 se reduce a comprobar que ningún lector dependía del string, o
   se cierra? Decidir **antes** de arrancarla. F-027 no renombra ni añade
   ningún motivo (R22).
4. **Histórico (R26)** — los 468.763,40 € del 58826 y los 462.282,80 € del
   58878 siguen persistidos hasta que se re-valoren. ¿Qué documentos se
   reprocesan y cuándo? La spec no trae script de backfill: el mecanismo
   (revalorar desde sv4 → `q-valoracion`) ya existe.
5. **Orden de implementación** — la spec asume `dev` con **F-019 mergeada**.
   Hay solape declarado (`design.md` §5): F-019 toca `importe_calculator.py`,
   `_build_header` del mismo `valuation_builder.py`, `review_repository.py` de
   sv4 y crea la suite de tests de sv6 que F-027 reutiliza. Adelantar F-027
   obliga a crear esa suite y a recalcular los importes esperados.

### Reordenación del backlog (misma sesión)

- **F-024 sube a prioridad 3**, justo detrás de F-027; F-028…F-016 bajan una
  posición cada una (3→4 … 12→13), conservando el orden relativo y sin
  empates. F-026 y siguientes no se mueven.
- **La descripción de F-024 se amplía** con la instrucción del humano del
  2026-08-18 (citada literal en `harness/features.json`): IA2 debe hacer una
  **revisión razonada de unidades** cuando la magnitud sea físicamente
  implausible —30.380 toneladas no caben en un camión, luego son kg—, con el
  razonamiento **explícito y trazable** (motivo de revisión con la
  reinterpretación aplicada), nunca un cambio silencioso del dato. Es
  **defensa en profundidad**, no un duplicado: IA2 detecta arriba, la red
  determinista de sv6 protege abajo. La spec de F-027 lo deja escrito en su
  R24.

### Verificaciones MANUAL (humano) que exigirá el cierre de F-027

Detalle en `specs/F-027-conversion-kg-tn-muerta/tasks.md` T10: reprocesar en
local los dos albaranes de MAHORSA y comprobar en BBDD `cantidad_convertida`
30,38 / 29,96 con `factor_conversion` 0,001 y `total_valorado` en centenas de
euros; comprobar que el warning `[unit-converter] … reinterpretada como KG`
**aparece por fin** en los logs (su ausencia histórica es la prueba de que la
red estaba muerta); verificar que un hormigón del mismo lote da el importe
idéntico al de la corrida del 2026-08-18; y que guardar el 58826 desde sv4 no
mueve el importe.

---

## Sesión 2026-08-18 — F-019 CERRADA (done, APPROVED en cuarta pasada)

> Mergeada a `dev`. Quedan las verificaciones MANUAL del humano (T17) y
> la decisión sobre el histórico ya valorado (R20, sin backfill).

- **F-019 `in_progress`** (era `spec_ready`). Rama
  `feature/F-019-importe-unitario-manda`, base `dev` (`cd904cd`).
  11 tareas de `tasks.md`: **T1-T9 y T11 cerradas con un commit cada una**;
  **T10 es MANUAL y la ejecuta el humano**.
- Informe del implementer: **`progress/impl_F-019.md`** (fase RED con las tres
  trazas reales, decisiones, desviaciones, guion MANUAL y sección
  «Evidencias»).
- `bash harness/init.sh` → **ENTORNO LISTO**. Cobertura de las líneas
  cambiadas **100 % (5/5, umbral 80 %, nivel `critico`)**. Mutación:
  **4 mutantes, 0 supervivientes** (`progress/mutacion_F-019.md`).

### Qué se hizo, en corto

- **sv5**: el `cantidad *` se mueve DENTRO del `COALESCE` de
  `_SQL_ALBARAN_LINES`. `precio_neto` es el IMPORTE de la línea tras
  descuento, no un unitario: multiplicarlo por la cantidad era el defecto que
  valoró en 6.238,14 € un albarán de 139,66 €. Reescrito el comentario que
  afirmaba lo contrario (era parte del bug).
- **sv6**: `PriceReconciler` invierte la precedencia **interna** entre los dos
  valores del albarán — manda el **unitario declarado**; el importe solo se
  despeja si no hay unitario. Si ambos existen y discrepan, gana el declarado
  y la línea sale con `agreement="mismatch"`, que es lo que el builder ya
  lleva a `review_required` (D3). El contrato sigue siendo solo fallback: la
  protección contra partidas alzadas tiene test de regresión propio, con el
  960.000 € del incidente.
- **Semántica atada con un test de contrato cruzado**
  (`tests/test_f019_r1_r2_r3_semantica_precio_neto.py`): si alguien cambia la
  definición de `precio_neto` en el prompt de IA1, ese test falla y obliga a
  reconciliar sv5/sv6 en el mismo trabajo.
- **Documentación**: regla 13 nueva en `docs/ARCHITECTURE.md`; `sv5.md` §9;
  `sv6.md` §5.3, §6.1 (tabla reescrita) y §6.4 (llevaba desde jul 2026
  diciendo lo contrario de lo que hace el código).

### Verificaciones MANUAL (humano) que exige el cierre de F-019

Guion completo con comandos y SQL exactos en **`progress/impl_F-019.md`,
sección «T10 · Verificaciones MANUAL»**. Los cuatro puntos:

1. Reprocesar **2.137.569** → total **139,66 €** y cinco líneas con sus
   unitarios (0,543 / 3,422 / 7,726 / 5,497 / 0,252) e importes
   (35,19 / 20,53 / 55,63 / 13,19 / 15,12).
2. Reprocesar **2.139.643** → total **19,41 €** (hoy 970,50 €).
3. Comprobar que ninguna línea de esos dos documentos arrastra
   `unitario_declarado_vs_derivado_mismatch` en `review_reasons_json`.
4. Comprobar que un albarán de **hormigón** (sin precios impresos) sigue
   valorándose por contrato, sin importes vacíos.

### Decisiones que necesita tomar el humano

1. **R20 — histórico**: los albaranes ya valorados conservan sus importes
   inflados hasta que se re-valoren. **No hay script de backfill** (decisión
   cerrada al aprobar la spec): se sanean revalorando desde sv4 →
   `q-valoracion`. Falta decidir **cuáles y cuándo**; hay una consulta para
   dimensionarlo en el guion de T10.
2. **F-003 hay que reconciliarla antes de arrancarla**: su R4 manda conservar
   «la derivación actual `cantidad × precio_neto`», que es exactamente el bug
   que F-019 acaba de corregir; y su R6 (guard aritmético) es la evolución del
   R10 de F-019, no un duplicado.
3. **Puerta de rutas sensibles**: la pasada declarada
   (`python -m evals.runner --con-llm --feature F-019`) no se pudo ejecutar —
   faltan `GEMINI_API_KEY` y `OPENAI_API_KEY` en el entorno local, y son
   secretos. La variante determinista sí corrió y demuestra el motivo de
   fondo: **0 casos en `evals/fixtures/inputs/`**, así que la completa daría
   `NO_EVALUABLE` igual. Exigencia declarada: `aviso`. Detalle en
   `progress/impl_F-019.md` §T9.

## Pendientes del humano (arrastrados de sesiones anteriores)

- Las 5 verificaciones MANUAL locales de F-002 (obra 0937, HORPRESOL,
  fecha 2023, `email_received_datetime` por colas, nº de obras tras el
  filtro >0450) — guion en `progress/impl_F-002.md` §T12.
- Push: `git push origin dev` (albaranes) y `git push origin main`
  (arnes-base).
- Hallazgo lateral de F-002: el `.gitignore` de sv2 ignora `*.example` y su
  `.env.example` actualizado no entra en git — decidir si se corrige.
- Decisión de dominio de F-011 (desviación 1): ¿sv6 descarta las sintéticas
  prohibidas o basta precio null + revisión?
- Rellenar los libros de `evals/ground_truth/` (con casos, la puerta de rutas
  sensibles puede subirse a `bloqueo`).
- Del informe del 18-08 salen además F-016 (multipartida, con la lectura del
  separador «/») y la revisión del etiquetado de proveedor (F-020).

---

## F-019 · ROUND TRIP 2 (2026-08-18) — reabierta y corregida

**Estado**: `in_progress`, rama `feature/F-019-importe-unitario-manda`,
pendiente de reviewer. Informe completo en `progress/impl_F-019.md`
§«Round trip 2».

**Por qué se reabrió**: la prueba local del humano midió en la BBDD
`total_valorado = 232,76 €` en el albarán Feymaco 2.137.569 (debe ser
139,66 €), con la rama ya en ejecución. El criterio de aceptación de la
feature no se cumplía.

**Causa real**: NO era sv5 ni sv6 —los dos escribían lo correcto—, sino
**sv4**: `review_repository::_recalc_valuation_importes` recalculaba
`cantidad × precio` **sin el descuento** en cada guardado del revisor y
pisaba el importe y el total que había escrito sv6. La pinza que lo
demuestra: el 2.137.569 tiene `updated_at_utc` seis minutos posterior a su
`created_at_utc`; el 2.139.643, valorado 22 s después con el mismo código y
nunca abierto en el front, conserva sus 19,41 € correctos.

**Qué se hizo**: alcance ampliado a sv4 (G6 de la spec, R23-R26); fórmula
canónica única `_importe_de_linea` para los **cuatro** puntos del servicio
que escribían un importe (tres se dejaban el descuento); el recálculo ya no
toca las filas que nadie ha cambiado (dejaba de degradar `declared_albaran`
a `calculated`); el total de la cabecera se redondea a 2 decimales.

**Suite nueva de sv4**: el servicio no tenía tests y `init.sh` lo avisaba en
cada pasada. Ahora tiene 44, incluido un **guardián estructural** que falla
si alguien vuelve a escribir la multiplicación a mano.

**Pendiente del humano (T17)**: revalorar los dos albaranes y, sobre todo,
**guardar el 2.137.569 desde el front y volver a mirar el total** — que es
justo el paso que destapó el fallo. Guion con las consultas en
`progress/impl_F-019.md`. Y decidir si se revalora la fila que quedó en
232,76 € en la BBDD local (no se ha escrito backfill: regla R20).

**Aviso para quien retome esto**: `progress/revision_hormigones_20260818.md`
es un fichero sin versionar de OTRA sesión. Se coló en un commit por un
`git add -A` y se sacó acto seguido; sigue intacto en disco, sin versionar.
Obliga a lanzar la mutación con `--workers 1`.

### F-019 · round trip 3 (CHANGES_REQUESTED del reviewer) — aplicado

Los **tres** cambios del reviewer, no dos (el humano decidió arreglar también
el que quedaba a elección):

1. **R24 se decidía por el RESULTADO y no por las entradas** (bloqueante). Una
   línea que sv6 dejó en `declared_albaran` con el importe declarado
   discrepando del calculado —cosa que sv6 hace **a propósito**— se pisaba en
   el primer guardado aunque el revisor no la tocara. Ahora `sin_cambios`
   compara cantidad, cantidad convertida y descuento **saneado**.
2. **La fórmula duplicada ENTRE servicios** → `services/albaranes-comun`
   (`ruesma_comun/importes.py`, nuevo). sv4 y sv6 la importan; la **política**
   de cada uno se queda donde estaba. Tests de **identidad** en ambos para que
   nadie reintroduzca una copia.
3. **El cableado `payload → descuento`** pasa a dos métodos con nombre y 7
   tests, que fijan la asimetría: las cantidades filtran los `None`, los
   descuentos no.

`init.sh` en verde; cobertura **93,1 %** (81/87); mutación **31/28/3**, los 3
supervivientes equivalentes y verificados. Todo ejecutado **en serie**: el
reviewer midió que lanzarlo en paralelo tumba `init.sh` en Windows
(`0xC0000142`).

**Ojo para el reviewer**: la puerta de rutas sensibles pasa de **2 a 3** rutas
señaladas, porque este round trip sí toca sv6
(`application/services/importe_calculator.py`). El estado sigue en `aviso` y la
causa de fondo es la misma de siempre (claves LLM ausentes y
`evals/ground_truth/` vacío).

Detalle completo en `progress/impl_F-019.md` §«Round trip 3».
