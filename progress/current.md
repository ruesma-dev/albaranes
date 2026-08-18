<!-- progress/current.md -->
# Trabajo en curso

## Sesión 2026-08-19 — F-027 implementada (pendiente de reviewer)

> Trabajada en el worktree de `dev` (`scratchpad/wt-dev`), rama
> `feature/F-027-conversion-kg-tn-muerta`, base `dev` (`e95549d`, con F-019
> ya mergeada). El árbol principal no se ha tocado.

- **F-027 `in_progress`** (era `spec_ready`). **T1-T9 y T11 cerradas con un
  commit cada una**; **T10 es MANUAL y la ejecuta el humano**.
- Informe del implementer: **`progress/impl_F-027.md`** (fase RED con las
  cinco trazas reales, decisiones, la desviación única, el guion MANUAL y la
  sección «Evidencias»).
- `bash harness/init.sh` → **ENTORNO LISTO**. Cobertura de las líneas
  cambiadas **100 % (4/4, umbral 80 %, nivel `critico`)**.

### Qué se hizo, en corto

El `ValuationBuilder` llamaba al conversor de unidades **con la cantidad
puesta a `None`** siempre que el guard de categoría decía que no, y convertía
hacia **la unidad del albarán** cuando había línea derivada. Lo primero mataba
la red de plausibilidad de toneladas —escrita en jul 2026 justo para este
caso y **nunca ejecutada**—; lo segundo daba factor 1 contra un precio por
tonelada. Ahora se convierte **siempre con la cantidad real** y **hacia la
unidad de la línea que pone el precio**. Son **cuatro líneas ejecutables** en
un solo fichero de producción.

- **58826**: 468.763,40 € → **468,76 €** (30.380 kg → 30,38 TN, factor 0,001).
  **58878**: 462.282,80 € → **462,28 €**.
- **La otra mitad del ×1000, la que está viva hoy sin que ninguna IA falle**:
  con el albarán en `KG` y el contrato en `TN` el importe salía igual de
  inflado **y ni siquiera iba a revisión**. Es el escenario que **F-024
  activa** en cuanto IA1 extraiga la unidad.
- **Sin mover un euro de lo que ya salía bien**, con test que lo vigila:
  hormigones 399,60 / 899,10 / 799,20, mortero 210,00, Feymaco 139,66 y 19,41,
  VODALAND 3.393,00.
- **66 tests nuevos** (57 en sv6, 9 de contrato en la suite raíz). Los dos
  riesgos asumidos del diseño (D2 y D3) van **con test propio**, para que se
  lean como decisiones y no como efectos colaterales.

### Decisiones que necesita tomar el humano

1. **La herramienta de mutación tiene un punto ciego caro: `is` / `is not`.**
   `python -m harness.mutacion --feature F-027` devuelve **0 mutantes**, no
   porque el cambio sea intocable sino porque `harness/mutacion.py` no tiene
   `ast.Is` ni `ast.IsNot` en su tabla `COMPARACIONES`, y las cuatro líneas de
   F-027 son un `is not None`, dos asignaciones y un `IfExp`. En Python, `is
   not None` es **la** guarda de ausencia: el punto ciego afecta a cualquier
   feature de cualquier proyecto. Se hizo en su lugar una campaña **manual**
   de 7 mutantes (7 muertos, 0 supervivientes) que **encontró un agujero
   real** — ver abajo. **Propuesta: ampliar `COMPARACIONES` con `ast.Is` y
   `ast.IsNot` y portarlo a `arnes-base`.** No se ha hecho dentro de F-027
   porque cambia la herramienta que mide a todas las features: lo decide el
   humano.
2. **F-025 se queda sin su caso principal.** Proponía emitir
   `conversion_skipped_unit_category_mismatch` en la rama `else` que F-027
   elimina. Al no haber ya conversión omitida a propósito,
   `no_quantity_in_albaran` vuelve a significar lo que dice. ¿F-025 se reduce
   a comprobar que ningún lector dependía del string, o se cierra? **Decidir
   antes de arrancarla.**
3. **Histórico (R26).** Los 468.763,40 € del 58826 y los 462.282,80 € del
   58878 siguen persistidos hasta que se re-valoren. No hay script de backfill
   (decisión cerrada al aprobar la spec): se sanean revalorando desde sv4 →
   `q-valoracion`. Falta decidir **cuáles y cuándo**.
4. **F-031 sigue debiendo 77,77 €.** Tras F-027 el 58826 queda en 468,76 €, no
   en los 390,99 € del administrativo: la diferencia es el precio de contrato
   equivocado (15,43 €/TN de caliza en vez de 12,87 de grava) y es F-031, no
   esta feature. Los tests fijan **los dos** números para poder separarlas en
   la prueba local.

### El agujero que encontró la mutación manual (para el reviewer)

El mutante `if albaran_line else None` → `else 0.0` **sobrevivió a los 109
tests** en la primera pasada: ningún test ejercitaba el caso de que **no
exista contexto de línea de albarán** (el de R8 lo construía CON contexto y
`cantidad=None`). Con ese mutante vivo, una línea huérfana se habría valorado
en **0,00 € con `importe_source='calculated'`** — un importe inventado con
pinta de calculado. Se añadió
`test_f027_r8_una_linea_sin_contexto_de_albaran_no_inventa_cantidad` y el
mutante muere.

### Puerta de rutas sensibles (aviso, no bloquea)

El diff toca 2 rutas sensibles (`unit_converter.py` y `valuation_builder.py`,
«redes deterministas de sv6»). La pasada declarada
`python -m evals.runner --con-llm --feature F-027` **no se pudo ejecutar**:
faltan `GEMINI_API_KEY` y `OPENAI_API_KEY`, que son secretos. La variante
determinista sí corrió y demuestra la causa de fondo: **0 casos en
`evals/fixtures/inputs/`**, así que la completa daría `NO_EVALUABLE` igual.
Informe en `progress/evals_F-027.md`. Exigencia declarada: `aviso`. Mismo
estado que F-019.

### Verificaciones MANUAL (humano) que exige el cierre de F-027 — T10

Guion completo con las consultas SQL exactas en **`progress/impl_F-027.md`,
sección «8. Verificaciones MANUAL pendientes»**. Los seis puntos:

1. Reprocesar **`Mahorsa_58826.pdf`** → `cantidad_albaran = 30380`,
   `cantidad_convertida = 30.38`, `factor_conversion = 0.001`, motivo
   `cantidad_sin_unidad_reinterpretada_kg_a_tn` y **sin**
   `no_quantity_in_albaran`; `total_valorado` en centenas de euros
   (**468,76 €**, no 390,99: eso es F-031).
2. Ídem con **`Mahorsa_58878.pdf`** (29.960 → 29,96 TN, 462,28 €).
3. Comprobar que el warning `[unit-converter] … reinterpretada como KG`
   **aparece por fin** en los logs de sv6. Su ausencia histórica es la prueba
   de que la red estaba muerta.
4. Reprocesar un **hormigón** del lote (224964 o 1167) y verificar que su
   importe es **idéntico** al de la corrida del 2026-08-18 (475,60 € y
   871,20 €).
5. Abrir el 58826 en sv4, **guardar sin cambiar nada** y comprobar que el
   importe no se mueve (R27). Es el paso que destapó el fallo de F-019.
6. Decidir el reproceso del histórico (punto 3 de las decisiones de arriba).

## Pendientes del humano (arrastrados de sesiones anteriores)

- **F-019**: las verificaciones MANUAL de T10/T17 (revalorar los dos albaranes
  de Feymaco y, sobre todo, **guardar el 2.137.569 desde el front** y volver a
  mirar el total) — guion en `progress/impl_F-019.md`. Y decidir si se
  revalora la fila que quedó en 232,76 € en la BBDD local.
- **F-019 R20 · histórico**: no hay backfill; falta decidir qué documentos se
  revaloran y cuándo.
- **F-003 hay que reconciliarla antes de arrancarla**: su R4 manda conservar
  «la derivación actual `cantidad × precio_neto`», que es el bug que F-019
  corrigió; y su R6 es la evolución del R10 de F-019, no un duplicado.
- Las 5 verificaciones MANUAL locales de **F-002** (obra 0937, HORPRESOL,
  fecha 2023, `email_received_datetime` por colas, nº de obras tras el filtro
  >0450) — guion en `progress/impl_F-002.md` §T12.
- Push: `git push origin dev` (albaranes) y `git push origin main`
  (arnes-base).
- Hallazgo lateral de F-002: el `.gitignore` de sv2 ignora `*.example` y su
  `.env.example` actualizado no entra en git — decidir si se corrige.
- Decisión de dominio de **F-011** (desviación 1): ¿sv6 descarta las sintéticas
  prohibidas o basta precio null + revisión?
- **Rellenar los libros de `evals/ground_truth/`**. Con casos, la puerta de
  rutas sensibles puede subirse de `aviso` a `bloqueo`; sin ellos, toda
  feature que toque una ruta sensible cierra con `NO_EVALUABLE`.
- Del informe del 18-08 salen además **F-016** (multipartida, con la lectura
  del separador «/») y la revisión del etiquetado de proveedor (**F-020**).
