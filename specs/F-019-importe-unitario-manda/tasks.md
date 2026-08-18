<!-- specs/F-019-importe-unitario-manda/tasks.md -->
# F-019 · Importe de línea: manda el unitario leído · Tareas

Rama: `feature/F-019-importe-unitario-manda`. Un commit por tarea
(`F-019 Tn: ...`). Rigor **critico**: fase RED con traza pegada en
`progress/impl_F-019.md`, cobertura de las líneas cambiadas ≥ 80 % y campaña
de mutación con **cero supervivientes** sin justificación escrita.

Los unit tests NO tocan red ni BBDD real. El SELECT de sv5 se prueba contra
**SQLite en memoria** (viabilidad comprobada al redactar la spec).

**Aviso de entorno**: al crear `services/albaran-valoracion-api/tests/` y
`services/albaran-valoracion-persist/tests/`, la sección 7 bis de `init.sh`
empieza a ejecutar esas suites (hoy avisa de que NADIE las comprueba). Cada
servicio se ejecuta con `cd` a su ruta y su propio `conftest.py` que ancla
`sys.path` — copiar el patrón de `services/albaranes-api/tests/conftest.py`.
**No mezclar sv5 y sv6 en una misma invocación de pytest**: ambos tienen
paquetes `application`/`domain`/`infrastructure` de primer nivel y colisionan
en `sys.modules`.

---

- [x] **T1**: Crear la rama y la suite de sv5 en **RED**:
      `services/albaran-valoracion-api/tests/conftest.py` (ancla `sys.path`)
      y `tests/test_f019_r4_r7_importe_select.py`, que ejecuta
      `_SQL_ALBARAN_LINES` contra `create_engine("sqlite://")` con la tabla
      `albaran_lines_merge` creada al vuelo y las 5 filas del albarán
      2.137.569 (R16) más los casos de la matriz del design: sin
      `precio_neto` (R5), sin precio ni neto (R6), sin cantidad (R7).
      Debe fallar con `importe_albaran = 3800.52`.
      | Verificación: `python -m pytest services/albaran-valoracion-api/tests -q`
      en ROJO, con la traza pegada en `progress/impl_F-019.md` (fase RED).

- [x] **T2**: sv5 — mover `cantidad *` dentro del `COALESCE` en
      `_SQL_ALBARAN_LINES` y reescribir el bloque de comentarios ~55-125 de
      `sqlalchemy_valuation_context_repository.py` con la semántica de R1
      (fuera la afirmación «precio_neto es el unitario NETO»).
      | Verificación: la suite de T1 en VERDE (`test_f019_r4_*`, `_r5_*`,
      `_r6_*`, `_r7_*`).

- [x] **T3**: Suite de sv6 en **RED**:
      `services/albaran-valoracion-persist/tests/conftest.py` y
      `tests/test_f019_r8_r15_precedencia.py`, con DTOs construidos a mano:
      R8 (declarado manda aunque haya importe), R9 (sin declarado → despeje),
      R10 (discrepan → gana el declarado + `agreement="mismatch"` + motivo),
      R11 (sin valores leídos → cadena de contrato intacta: 4 casos),
      R12 (regresión partida alzada: cinta 18,84 € leídos con `precio_1a`
      8.000 € → final_price 18,84, NUNCA 8.000), R13 (ceros → ausentes),
      R14 (dto 100 %, cantidad 0, cantidad None), R15 (dto fuera de rango).
      | Verificación: `python -m pytest services/albaran-valoracion-persist/tests -q`
      en ROJO (al menos R8, R9, R10), traza pegada en el informe.

- [x] **T4**: sv6 — invertir la precedencia en
      `application/services/price_reconciler.py`: bloque 1 = unitario
      declarado (con contraste contra el derivado y `agreement="mismatch"` si
      discrepa), bloque 2 = despeje del importe, bloque 3 = fallback contrato
      sin tocar. Reescribir el docstring con la regla del humano
      (2026-08-18) y sus dos mitades. Helpers `_no_cero`, `_derivar_bruto` y
      `_match` **sin cambios**.
      | Verificación: suite de sv6 en VERDE (`test_f019_r8_*` … `_r15_*`).

- [x] **T5**: Test de contrato cruzado del monorepo:
      `tests/test_f019_r1_r2_r3_semantica_precio_neto.py`. **Lee ficheros
      como texto** (`yaml.safe_load` del prompt, lectura plana del `.py` de
      sv5) — NO importa paquetes de sv5/sv6, para no romper la suite raíz:
      (a) el prompt de IA1 activo define `precio_neto` como
      `cantidad*precio*(1 - descuento/100)`; (b) el SELECT de sv5 NO
      multiplica el `COALESCE` por la cantidad; (c) `docs/ARCHITECTURE.md`
      contiene la regla de semántica de R3. Con comentario de cabecera
      explicando que si F-003 sustituye el campo, este test debe cambiarse
      **en el mismo trabajo** (esa es su función).
      | Verificación: `python -m pytest tests -q` en verde
      (`test_f019_r1_*`, `_r2_*`, `_r3_*`).

- [x] **T6**: Caso Feymaco completo en la suite de sv6:
      `tests/test_f019_r16_r17_feymaco.py`. Las 5 líneas del 2.137.569
      encadenando `PriceReconciler` + `ImporteCalculator` con el importe
      efectivo que produce sv5 tras T2 (35,19 / 20,53 / 55,63 / 13,19 /
      15,12): cada línea con su unitario exacto, su importe, y la suma
      **139,66 €**. Incluir R17 explícito: el derivado
      `35,19 / (108 × 0,6) = 0,543055…` coincide con el declarado `0,543`
      dentro de `PRICE_TOLERANCE_PCT` → `agreement != "mismatch"`.
      La fixture de las 5 líneas se repite a propósito en la suite de sv5
      (T1) con los mismos números y un comentario cruzado: es la unión de los
      dos tramos de la cadena, que no pueden importarse en la misma sesión de
      pytest.
      | Verificación: `python -m pytest services/albaran-valoracion-persist/tests -q`
      en verde (`test_f019_r16_*`, `_r17_*`).

- [x] **T7**: Documentación normativa (R3): regla nueva en
      `docs/ARCHITECTURE.md` §«Semántica de dominio imprescindible»;
      `services/albaran-valoracion-api/sv5.md` (propagación del campo);
      `services/albaran-valoracion-persist/sv6.md` §6.1 (tabla de
      precedencia nueva) y §6.4 (que además está desactualizada desde jul
      2026: dice «se usa el calculado» y el código usa el declarado).
      | Verificación: revisión contra `design.md` §«Documentación normativa»;
      `test_f019_r3_*` de T5 cubre la regla de `ARCHITECTURE.md`.

- [x] **T8**: Campaña de mutación y análisis de supervivientes.
      | Verificación: `python -m harness.mutacion --feature F-019` →
      `progress/mutacion_F-019.md` con **cero supervivientes** (nivel
      `critico`) o justificación escrita por superviviente, aceptada por el
      humano. Ojo: el SQL vive dentro de un `text("""…""")` y no genera
      mutantes; el código mutable real es `price_reconciler.py`.

- [x] **T9**: Puerta de rutas sensibles (R22). `price_reconciler.py` cae bajo
      `services/albaran-valoracion-persist/application/services/**`.
      | Verificación: `python -m evals.runner --con-llm --feature F-019` →
      `progress/evals_F-019.md`. Con el ground truth vacío la pasada dará
      `NO_EVALUABLE`: la exigencia es `aviso`, así que **el motivo se escribe
      en el informe** y el reviewer lo recoge en C4 ter (no se marca N/A a
      secas).

- [ ] **T10**: MANUAL (humano) — **PENDIENTE del humano**; comandos y
      consultas exactas en la sección «T10 · Verificaciones MANUAL» de
      `progress/impl_F-019.md`. — prueba local con los dos PDFs del lote
      `alvaro_17082026` (Azurite + PG local, `infra/docs/levantar-pipeline-local.md`):
      1) reprocesar **2.137.569** → 5 líneas con los unitarios e importes de
         R16 y total **139,66 €**;
      2) reprocesar **2.139.643** → total **19,41 €** (R18);
      3) comprobar en `albaran_valuation_lines` que ninguna línea trae
         `unitario_declarado_vs_derivado_mismatch` en `review_reasons`;
      4) comprobar que un albarán de **hormigón** (sin precios impresos)
         sigue valorándose por contrato, sin importes vacíos (R6).
      | Verificación: MANUAL (humano); resultados pegados en
      `progress/impl_F-019.md`.

- [ ] **T11**: Ejecutar `bash harness/init.sh` en verde (incluye las suites
      nuevas de sv5 y sv6 y la puerta de cobertura del diff).
      | Verificación: `bash harness/init.sh` → ENTORNO LISTO.

---

## Trazabilidad requisito → tarea

| R | Tarea |
|---|---|
| R1, R2, R3 | T5 (+ T2, T7 escriben la semántica) |
| R4, R5, R6, R7 | T1 (RED) → T2 |
| R8, R9, R10 | T3 (RED) → T4 |
| R11, R12, R13, R14, R15 | T3 → T4 (regresión) |
| R16, R17 | T1 (tramo sv5) + T6 (tramo sv6) |
| R18 | T10 (MANUAL) |
| R19, R20, R21 | T10 punto 4 + nota en `progress/current.md` (sin código) |
| R22 | T9 |
