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
