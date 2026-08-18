<!-- progress/current.md -->
# Trabajo en curso

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
