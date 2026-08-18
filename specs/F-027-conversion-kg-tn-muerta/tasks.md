<!-- specs/F-027-conversion-kg-tn-muerta/tasks.md -->
# F-027 · La red KG→TN de `UnitConverter` es código muerto · Tareas

Rama: `feature/F-027-conversion-kg-tn-muerta`. Un commit por tarea
(`F-027 Tn: ...`). Rigor **critico**: fase RED con la traza pegada en
`progress/impl_F-027.md`, cobertura de las líneas cambiadas ≥ 80 % y campaña
de mutación con **cero supervivientes** sin justificación escrita aceptada por
el humano.

**Punto de partida**: `dev` con **F-019 mergeada** (ver `design.md` §5). De ahí
salen la suite `services/albaran-valoracion-persist/tests/` con su
`conftest.py` y el redondeo del `ImporteCalculator` contra el que se calculan
los importes esperados. Si el humano decide adelantar F-027, la tarea T1 crea
la suite y el implementer recalcula y documenta los números.

Los unit tests NO tocan red, ni BBDD, ni LLM: el único fichero que se lee del
disco es `config/unit_registry.yaml`, dato versionado del propio servicio.

**Aviso de entorno**: sv5 y sv6 no pueden compartir invocación de pytest
(paquetes `application`/`domain`/`infrastructure` de primer nivel que colisionan
en `sys.modules`). La sección 7 bis de `init.sh` ya los ejecuta por separado con
`cd` a su ruta.

---

- [x] **T1**: Crear la rama y la suite del conversor en **RED**:
      `services/albaran-valoracion-persist/tests/test_f027_r3_r9_conversor.py`
      con `YamlUnitRegistry` real sobre `config/unit_registry.yaml`. Cubre
      R3 (30380 y 29960 sin unidad contra TN → 30,38 / 29,96, factor 0,001,
      `ambiguous`, motivo `cantidad_sin_unidad_reinterpretada_kg_a_tn`),
      R4 (500 → sin tocar, `cantidad_tn_implausible_revisar`), R5 (`UD`→`M3`
      → `None` + `unit_category_mismatch_in_conversion`), R8 (`None` →
      `no_quantity_in_albaran`), R9 (`0` → 0,0 con factor 1) y R17 (`SACO`→`UD`
      ambiguo). Si la suite de sv6 no existe todavía, crear también su
      `conftest.py` copiando el patrón de
      `services/albaranes-api/tests/conftest.py`.
      **Estos tests pasan en VERDE desde el primer momento**: la lógica del
      conversor ya es correcta. La fase RED de esta tarea se demuestra según
      CHECKPOINTS.md C4 bis rompiendo deliberadamente el umbral
      `_TN_UMBRAL_CONVERTIR` **en una copia aislada, nunca en el árbol real**,
      y pegando la traza del fallo.
      | Verificación: `python -m pytest tests -q` desde
      `services/albaran-valoracion-persist` en verde, + traza del fallo
      provocado en `progress/impl_F-027.md`.

- [x] **T2**: **RED de verdad** — el defecto, a través del builder:
      `tests/test_f027_r1_r2_r11_r13_builder.py`. Compone `ValuationBuilder`
      con sus cinco colaboradores reales (`UnitCategoryGuard`,
      `PriceReconciler(tolerance_pct=2.0)`, `PartidaMatcher(alm_codigo_partida="ALM")`,
      `UnitConverter`, `ImporteCalculator(tolerance_pct=5.0)`) y un
      `ValuationEnvelope` construido a mano con el albarán **58826**: línea
      `ARIDO M-20/40-S EN 12620:2002H`, `cantidad=30380.0`,
      `unidad_medida=None`, partida `P4.22.01.03.07`; línea de contrato en
      `TN`. Comprueba R1/R2 (se convierte y la línea sigue en revisión),
      R11 (`cantidad_convertida=30.38`, `factor_conversion=0.001`,
      `importe_calculado=390.99` con 12,87 €/TN y `468.76` con 15,43 €/TN),
      R12 (58878: 29.960 → 29,96 → 385,59 / 462,28) y R13
      (`header.total_valorado` del `build` completo ≤ 500 €).
      | Verificación: `python -m pytest tests -q` en **ROJO** con
      `importe_calculado == 468763.4`; traza pegada en
      `progress/impl_F-027.md` (fase RED de los requisitos centrales).

- [ ] **T3**: **RED** de la segunda mitad del ×1000:
      `tests/test_f027_r6_r7_unidad_destino.py`. Mismo albarán pero con
      `unidad_medida='KG'` (el escenario que abre F-024) y partida cruzada que
      fuerza `partida_action='new_line_created'`: hoy convierte `KG→KG` con
      factor 1 y da 468.763,40 €. Comprueba R6 (la unidad de destino es
      `derived_line.unidad_medida`) y R7 (30,38 TN). Añadir el caso de
      compatibilidad: derivada **sin** línea de contrato de referencia →
      `derived_line.unidad_medida == unidad_albaran` → factor 1, comportamiento
      idéntico al de hoy.
      | Verificación: en **ROJO** antes de T5, con la traza pegada.

- [ ] **T4**: **RED** de la no-regresión (R14, R15, R16, R19, R20):
      `tests/test_f027_r14_r20_no_regresion.py`. Fija los importes que hoy
      salen BIEN, medidos antes del cambio y pegados en el informe:
      hormigón/mortero sin unidad contra contrato en `M3` (4, 9, 8 y 3 m³ del
      lote `alvaro_17082026`), ferretería en `UD` (Feymaco, los números de
      F-019 R16/R18) y el total **3.393,00 €** del A261584 de VODALAND. Más
      R19 (la tabla de los cuatro motivos: cada estado emite el suyo y solo el
      suyo) y R20 (`cantidad_albaran=30380` convive con
      `cantidad_convertida=30.38` y `factor_conversion=0.001`).
      | Verificación: en **VERDE antes y después** del cambio para R14-R16
      (es su función: si se pusieran rojos, el cambio habría roto lo bueno);
      en ROJO antes de T5 para R19/R20.

- [ ] **T5**: **El cambio**. En
      `services/albaran-valoracion-persist/application/services/valuation_builder.py`,
      paso «4. Unit conversion»: una sola llamada a `self._converter.convert`
      con la cantidad real (elimina la rama `else` con `cantidad=None`), y
      `unidad_destino_conversion = partida_result.derived_line.unidad_medida`
      cuando hay derivada, si no `unidad_contrato` (fuera el
      `category_match and`). Comentario con el motivo, el caso real y los
      euros, según el bloque literal de `design.md` §2.1.
      | Verificación: las suites de T2, T3 y T4 en VERDE
      (`test_f027_r1_*` … `test_f027_r20_*`), sin tocar T1.

- [ ] **T6**: Documentación del conversor y del servicio (sin cambio
      funcional): ampliar el comentario de cabecera de
      `application/services/unit_converter.py` (líneas 21-33) con el periodo en
      que la red estuvo muerta y el caso 58826/58878; actualizar
      `services/albaran-valoracion-persist/sv6.md` §5.2 (paso 4) y §6.3 (que
      hoy **no documenta** la red de plausibilidad de TN, existente desde jul
      2026), incluyendo la tabla de motivos de R19.
      | Verificación: revisión contra `design.md` §2.2 y §2.3; `git diff` sin
      cambios de código ejecutable en `unit_converter.py`.

- [ ] **T7**: Regla 8 de `docs/ARCHITECTURE.md` §«Semántica de dominio
      imprescindible»: pasar por el conversor significa **pasarle la
      cantidad**; un desacuerdo de categoría marca revisión, nunca anula la
      cantidad; la unidad de destino es la de la línea que pone el precio.
      Añadir un test de contrato en la suite raíz del monorepo
      (`tests/test_f027_r18_r22_contrato.py`) que lea como **texto** —sin
      importar paquetes de sv6, para no romper la suite raíz— y compruebe
      R18 (`_TN_UMBRAL_CONVERTIR = 1000` y `_TN_UMBRAL_AVISAR = 100` intactos,
      `config/unit_registry.yaml` sin cambios en la categoría `mass`), R22
      (`valuation_builder.py` no introduce ningún string de motivo nuevo ni
      retira ninguno) y R23/R24 (el diff no toca `partida_matcher.py` ni
      ningún `prompts*.yaml`).
      | Verificación: `python -m pytest tests -q` desde la raíz, en verde.

- [ ] **T8**: Campaña de mutación y análisis de supervivientes.
      | Verificación: `python -m harness.mutacion --feature F-027` →
      `progress/mutacion_F-027.md` con **cero supervivientes** (nivel
      `critico`) o justificación escrita por superviviente aceptada por el
      humano. Nota para el implementer: el cambio **elimina** una rama, así que
      el alcance mutable es pequeño; los mutantes interesantes son los del
      operador `is not None` de la derivada y los del argumento `cantidad`.

- [ ] **T9**: Puerta de rutas sensibles (R25).
      `valuation_builder.py` cae bajo
      `services/albaran-valoracion-persist/application/services/**`.
      | Verificación: `python -m evals.runner --con-llm --feature F-027` →
      `progress/evals_F-027.md`. Con el ground truth vacío la pasada dará
      `NO_EVALUABLE`: la exigencia es `aviso`, así que **el motivo se escribe
      en el informe** y el reviewer lo recoge en C4 ter. No se marca N/A a
      secas.

- [ ] **T10**: MANUAL (humano) — prueba local de extremo a extremo con Azurite
      + PostgreSQL local (`infra/docs/levantar-pipeline-local.md`), con los
      PDFs del lote `alvaro_17082026`. Comandos exactos y consultas SQL en la
      sección «T10 · Verificaciones MANUAL» de `progress/impl_F-027.md`:
      1. Reprocesar **Mahorsa_58826.pdf** y comprobar en
         `albaran_line_valuations`: `cantidad_albaran = 30380`,
         `cantidad_convertida = 30.38`, `factor_conversion = 0.001`,
         `review_reasons_json` con `cantidad_sin_unidad_reinterpretada_kg_a_tn`
         y **sin** `no_quantity_in_albaran` (R10); y en `albaran_valuations`
         que `total_valorado` está en centenas de euros, no en cientos de
         miles.
      2. Ídem con **Mahorsa_58878.pdf** (29.960 → 29,96).
      3. Comprobar que el warning
         «[unit-converter] cantidad … reinterpretada como KG» **aparece ahora**
         en `services/albaran-valoracion-persist/logs/` (R21): su ausencia
         histórica es la prueba de que la red estaba muerta.
      4. Reprocesar un albarán de **hormigón** del mismo lote (224964 o 1167) y
         verificar que su importe es **idéntico** al de la corrida del
         2026-08-18 (R14).
      5. Abrir el 58826 en sv4, **guardar sin cambiar nada** y comprobar que el
         importe no se mueve (R27, con la fórmula que dejó F-019).
      | Verificación: MANUAL (humano); resultados pegados en
      `progress/impl_F-027.md`.

- [ ] **T11**: Ejecutar `bash harness/init.sh` en verde (incluye la suite de
      sv6 y la puerta de cobertura del diff).
      | Verificación: `bash harness/init.sh` → ENTORNO LISTO.

---

## Trazabilidad requisito → tarea

| R | Tarea |
|---|---|
| R1, R2 | T2 (RED) → T5 |
| R3, R4, R5, R8, R9, R17 | T1 |
| R6, R7 | T3 (RED) → T5 |
| R10 | T2 + T10 punto 1 (MANUAL) |
| R11, R12, R13 | T2 (RED) → T5 |
| R14, R15, R16 | T4 (regresión) + T10 punto 4 (MANUAL) |
| R18 | T7 |
| R19, R20 | T4 (RED) → T5 |
| R21 | T6 + T10 punto 3 (MANUAL) |
| R22, R23, R24 | T7 (test de contrato) + nota en `progress/current.md` |
| R25 | T9 |
| R26 | sin código; decisión del humano anotada en `progress/current.md` |
| R27 | T10 punto 5 (MANUAL) |
