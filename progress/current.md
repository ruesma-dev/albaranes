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

## Sesión 2026-08-18 — spec de F-019 escrita (esperando aprobación humana)

- **F-019 `spec_ready`** (era `pending`). Spec en
  `specs/F-019-importe-unitario-manda/` (`requirements.md` 22 requisitos EARS,
  `design.md`, `tasks.md` 11 tareas). Rigor **critico**. Rama prevista:
  `feature/F-019-importe-unitario-manda`. **NO se ha escrito código.**
- Fuente del diagnóstico: `progress/prueba_local_feymaco_20260818.md`.

### Qué dice la spec, en corto

- El número malo lo produce **un solo defecto**: el SELECT de sv5
  (`sqlalchemy_valuation_context_repository.py`) calcula
  `importe_albaran = cantidad × precio_neto` creyendo que `precio_neto` es un
  unitario. Es el **importe** de la línea. Se corrige moviendo el `cantidad *`
  dentro del `COALESCE`; la cascada del «FIX 2 (jul 2026)» se conserva entera.
- **Verificado de primera mano** durante la redacción, ejecutando el código
  real sin BBDD: el SELECT contra SQLite devuelve 3.800,52 para la fila real,
  y `PriceReconciler` devuelve 58,65 con el importe inflado y 0,543 con el
  importe correcto. La cadena causal del informe queda confirmada.
- La precedencia de sv6 se invierte igualmente (regla del humano): manda el
  unitario leído; el importe solo se despeja si falta. El fallback al contrato
  y la protección contra partidas alzadas (cinta 18,84 € / PA 8.000 €) quedan
  con test de regresión propio.
- **sv2 no se toca** (decisión D1): el prompt de IA1 define bien el campo; el
  equivocado era el consumidor. La semántica se ata con un test de contrato
  cruzado que falla si alguien cambia el prompt sin reconciliar sv5/sv6.
- Efecto lateral bueno: `importe_albaran` viaja al prompt de IA3, así que hoy
  el LLM de valoración también está viendo importes × cantidad. Se sanea sin
  tocar ningún prompt.

### Decisiones abiertas que necesita validar el humano

1. **D3 — `agreement="mismatch"`**: ¿se acepta que
   `precio_unitario_agreement="mismatch"` pueda aparecer en líneas cuyo precio
   viene del albarán? Es la vía elegida para que el desacuerdo
   unitario-declarado / derivado-del-importe llegue a revisión sin tocar
   `valuation_builder.py`. Alternativa: condición explícita en el builder.
2. **R20 — histórico**: los albaranes ya valorados conservan sus importes
   inflados hasta que se re-valoren. ¿Cuáles se reprocesan y cuándo? El
   mecanismo ya existe (revalorar desde sv4 → `q-valoracion`); la spec **no**
   incluye script de backfill.
3. **F-003 (`spec_ready`) hay que reconciliarla**: su R4 manda conservar «la
   derivación actual `cantidad × precio_neto` como fallback», que es
   exactamente el bug de F-019; y su R6 (guard aritmético) es la evolución del
   R10 de F-019, no un duplicado. Anotarlo en F-003 antes de arrancarla.
4. **Prompt con nombre no ambiguo** (`importe_linea` propio en IA1): la spec lo
   deja fuera a propósito porque ya está especificado en F-003 R1/R2.
   Confirmar que se prefiere ese reparto y no adelantarlo aquí.

### Verificaciones MANUAL (humano) que exigirá el cierre de F-019

Detalle en `tasks.md` T10: reprocesar en local **2.137.569** (total esperado
139,66 €, cinco líneas con sus unitarios) y **2.139.643** (19,41 €), comprobar
que no queda `unitario_declarado_vs_derivado_mismatch` en `review_reasons`, y
que un albarán de hormigón sin precios impresos sigue valorándose por contrato.

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
  sensibles puede subirse a `bloqueo`; mientras tanto la pasada de F-019 dará
  `NO_EVALUABLE`).
- Del informe del 18-08 salen además F-016 (multipartida, con la lectura del
  separador «/») y la revisión del etiquetado de proveedor (F-020).
