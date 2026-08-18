<!-- progress/current.md -->
# Trabajo en curso

## Sesión 2026-08-18 — F-019 implementada (esperando review y prueba MANUAL)

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
