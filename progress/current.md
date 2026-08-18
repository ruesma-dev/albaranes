<!-- progress/current.md -->
# Trabajo en curso

## Cierre de sesión — 2026-08-19

Sesión larga (18 y 19 de agosto). `dev` al día, árbol limpio, **ninguna feature
`in_progress` ni `blocked`**. El backlog tiene **34 features, 28 abiertas**.

### Lo que se cerró en esta sesión

- **F-019 · Importe de línea** (done, APPROVED en **cuarta** pasada). El fallo
  apareció en tres capas sucesivas: el SELECT de sv5 multiplicaba por la
  cantidad un `precio_neto` que ya era el importe de línea; la precedencia de
  sv6 daba prioridad al importe sobre el unitario leído; y **sv4 recalculaba
  sin descuento y pisaba en BBDD lo que sv6 escribía bien**. La fórmula
  canónica vive ahora en `ruesma_comun/importes.py`, consumida de verdad por
  sv4 y sv6 (fijado con tests de **identidad de objeto**). Al unificarlas se
  descubrió que las dos copias **ya divergían**.
- **F-027 · Error de ×1000 kg→TN** (done, APPROVED a la primera). MAHORSA
  58826: de **468.763,40 €** a **468,76 €**. Incluye la *segunda mitad* del
  error, que se habría activado al implementar F-024.
- **Arnés 1.5.0**: `BACKLOG.md` generado desde `features.json` y regenerado por
  `init.sh`; y la sección de subagentes de `CLAUDE.md` dice ahora que delegar
  es la vía normal. Propagado a `arnes-base` (commit `3b46d55`).
- **Backlog**: altas de F-021 a F-034 desde las dos revisiones del lote.

### Lo primero al abrir la próxima sesión

**F-034 (prioridad 1)**: el mutador del arnés no muta `is` / `is not`. Cambia
la **vara de medir** de todas las features, así que va antes que cualquier otra
cosa: cada feature cerrada hasta que se arregle se mide con una campaña ciega
justo en el patrón (`x is None`) que ha causado los dos defectos más caros del
proyecto. Incluye dos incoherencias más (el `evals/ground_truth/` inexistente y
el rastro de las campañas manuales) y **se porta a `arnes-base`**.

Después, por orden: F-024 (unidad + revisión razonada de unidades en IA2),
F-028 y F-029 (los dos casos en que el albarán **no llega a valorarse**), F-030,
F-031…

### Pendientes del humano (ninguno bloquea, pero varios llevan tiempo)

1. **Prueba local de F-002** — 4 de las 5 verificaciones siguen sin hacer (la K
   ya salió: `obras_activas=275`). Es lo que libera el **merge de F-003**, que
   está implementada y aprobada en su rama desde hace días.
2. **Reconciliar F-003 antes de arrancarla**: su R4 manda conservar el cálculo
   `cantidad × precio_neto` que **F-019 acaba de corregir**, y su R6 es la
   evolución del R10 de F-019. Igual que **F-004**, que tiene absorbidos por
   F-023 su R24 y sus R9/R10, y contradicha por F-018 su regla de «M7 solo con
   señal».
3. **Verificaciones MANUAL de F-019 (T17) y F-027 (T10)**: los números están
   fijados por test, pero los totales de documento completo solo se comprueban
   ahí.
4. **Histórico mal valorado en BBDD**: 468.763,40 € y 462.282,80 € del lote de
   MAHORSA, y los importes sin descuento anteriores a F-019. Por diseño no hay
   backfill: se sanean **revalorando desde sv4**. Falta decidir cuáles y cuándo.
5. **Derivados por IA del lote de Álvaro** (cierran F-014) y las dudas abiertas:
   precios manuscritos de Pavimarsa (¿fuente `ALBARAN` o `MANUSCRITO`?), unidad
   de Vodaland (377 u. en papel frente a MT en el Excel), partidas P4/P5, y las
   erratas del Excel (fecha del 09256 como texto `11/08/20205`, concepto del
   224964).
6. **Rellenar `evals/fixtures/inputs/`**: mientras esté vacío, la puerta de
   rutas sensibles se queda en `aviso` y ninguna feature que toque prompts
   puede demostrar nada. Ojo: F-034 arregla que la documentación diga
   `evals/ground_truth/`, que no existe.
7. **Despliegue**: NADA está desplegado. Producción corre las imágenes
   `r20260724-1632` (24 de julio), es decir **sin F-002, F-019 ni F-027** — el
   ×1000 y el importe sin descuento siguen vivos en Azure. Cuando se autorice:
   secret `SIGRID_API_FUNCTION_KEY` en `ca-sv2-extraccion`, `set_models.ps1
   -Anthropic claude-opus-4-8`, y actualizar `azure-apps/albaranes.md`.
8. **Modelos en local**: sv5 tenía `ENABLE_CLAUDE=false` y `ANTHROPIC_MODEL=
   claude-opus-4-7`; sv2, `claude-sonnet-4-5`. Lo decidido es `claude-opus-4-8`
   en ambos. El humano edita los `.env` (los agentes no los tocan).

### Notas operativas de la sesión (útiles para la siguiente)

- **No lanzar suites ni campañas de mutación en paralelo**: hubo abortos por
  presión de recursos de Windows (`git init` devolviendo `0xC0000142`) y varios
  agentes colgados. En serie, y `--workers 1` si la mutación paralela protesta
  por ficheros sin versionar.
- **Worktree de `dev`** en `scratchpad/wt-dev`: permitió trabajar en el backlog
  y en el arnés mientras el árbol principal estaba ocupado con una rama de
  feature. Vale la pena mantener la costumbre.
- La API dio muchos **529 (sobrecarga)** y cuelgues de watchdog. Los agentes se
  reanudan con el trabajo intacto; si uno acumula demasiadas pasadas, sale más
  barato lanzar uno nuevo con contexto acotado.
