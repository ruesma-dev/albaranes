<!-- specs/F-003-valorados-match-estricto/tasks.md -->
# F-003 · Tanda 2 — Albaranes valorados, match estricto y coherencia · Tareas

Rama: `feature/F-003-valorados-match-estricto`. Un commit por tarea
(`F-003 Tn: ...`). Los tests van junto a su implementación y NO tocan red
ni BBDD. Antes de la primera tarea con tests de cada servicio: comprobar
que su venv tiene `pytest` (crear `tests/` activa la sección 7 bis de
init.sh). Las decisiones P1–P3 están respondidas por el humano
(2026-08-13; ver «Decisiones tomadas» en design.md): no queda ningún
prerrequisito abierto.

- [x] T1: sv2 — schema de extracción (`domain/models/albaran_models.py`):
      `LineaAlbaran.importe`, `LineaAlbaran.descuentos`,
      `CabeceraAlbaran.importe_total`,
      `CabeceraAlbaran.importe_total_incluye_iva` +
      `test_f003_schema_extraccion.py`
      (R2: campos opcionales, default null, el schema sigue validando
      extracciones antiguas).
      | Verificación: `pytest services/albaranes-api/tests -q` en verde
      (tests `test_f003_r2_*`).

- [x] T2: sv2 — prompt `albaran_factura_es` (R1): bloque «transcribir, no
      recomponer», reescritura de `precio`/`descuento`/`precio_neto`
      (eliminar el «calcula cantidad*precio*(1 - descuento/100)»), regla de
      `importe_total` en cabecera (total con IVA → se transcribe y se marca
      `importe_total_incluye_iva=true`, nunca null por incluir IVA) +
      `test_f003_prompt_transcripcion.py`
      (las reglas nuevas presentes en el YAML cargado; la instrucción de
      calcular ha desaparecido).
      | Verificación: pytest sv2 en verde (tests `test_f003_r1_*`).

- [x] T3: sv3 — columnas nuevas (ORM mixins + DDL idempotente
      `ADD COLUMN IF NOT EXISTS` en raw y merge, 4 columnas), mapeo
      extracción→ORM de los campos nuevos y `descuento_cascada.py`
      (`descuento_efectivo`) + `test_f003_descuento_cascada.py` +
      `test_f003_mapeo_campos_leidos.py` (R3: transcritos tal cual;
      efectivo solo con >1 descuento y `descuento` null).
      | Verificación: `pytest services/albaranes-persistencia/tests -q`
      en verde (tests `test_f003_r3_*`). El ALTER real contra PG es
      MANUAL (humano) en T12.

- [x] T4: sv5 — contexto de valoración (R4): SELECT de líneas
      (`importe_leido` + `importe_albaran` con COALESCE), SELECT de
      cabecera (`importe_total`, `importe_total_incluye_iva`),
      `valuation_context.py` y propagación en
      `value_albaran_pipeline.py` (context + los dos `meta`) + crear
      `services/albaran-valoracion-api/tests/` con
      `test_f003_contexto_importe.py` (mapeo fila→DTO: leído presente →
      efectivo = leído; fila antigua → efectivo = derivación actual).
      | Verificación: pytest sv5 en verde (tests `test_f003_r4_*`).

- [x] T5: sv6 — DTOs del envelope (`importe_leido`,
      `meta.importe_total_albaran`, `meta.importe_total_incluye_iva`) +
      flags en `config/settings.py` +
      wiring en `composition.py` + crear
      `services/albaran-valoracion-persist/tests/` con
      `test_f003_sobres_antiguos.py` (R14: envelope sin campos nuevos
      valida y valora como hoy).
      | Verificación: pytest sv6 en verde (tests `test_f003_r14_*`).

- [x] T6: sv6 — descuento no sobre precio de contrato (R5) en
      `valuation_builder._build_line` + `test_f003_dto_no_contrato.py`:
      precio de contrato + dto → sin descuento y reason
      `descuento_albaran_no_aplicado_a_precio_contrato`; precio del
      albarán + dto → fórmula actual (regresión); sintética con padre con
      dto → herencia intacta (según P1/D4).
      | Verificación: pytest sv6 en verde (tests `test_f003_r5_*`).

- [x] T7: sv6 — `guard_aritmetico.py` + integración en builder (línea,
      total, ORE OIL) + `test_f003_guard_aritmetico.py`: R6 (caso ×120:
      cantidad 120,55 / precio 1,5877 / importe leído 191,40 → se
      persiste 191,40, mismatch → revisión; jamás 23.073,60), R7 (Σ
      from_albaran vs total BASE → revisión si descuadra; total CON IVA o
      desconocido → solo aviso `guard_aritmetico_total_con_iva`, sin
      revisión; sintéticas fuera; total null → no-op), R8 (ORE OIL: línea
      única sin importe + total base → importe = total con reason; total
      con IVA → no se inyecta), R13 (flag a false → comportamiento previo).
      | Verificación: pytest sv6 en verde (tests `test_f003_r6_*`,
      `_r7_*`, `_r8_*`, `_r13_*`).

- [ ] T8: sv6 — `atributo_sustantivo_guard.py` + integración en `build()`
      (tras IA4/saneo de años, antes de las pasadas) +
      `test_f003_atributo_sustantivo.py`: R11 (0,5 mm vs 0,6 mm anula
      match y precios; 0,5 = 0.50 y D-300 = D300 no anulan; hormigón y
      mortero excluidos; sintéticas excluidas), R12 (línea anulada →
      derivada `nueva_no_match` SIN precio + `review_required`), R13
      (flag).
      | Verificación: pytest sv6 en verde (tests `test_f003_r11_*`,
      `_r12_*`).

- [ ] T9: sv5 — prompts `valuation_es` y `conciliacion_es` (R9, R10):
      regla de atributo sustantivo + casos CETOSA / elemento base 0,5 mm /
      bolsa de cuñas + máxima «mejor línea nueva sin precio», excepción
      tipográfica conservada + `test_f003_prompts_match_estricto.py`.
      | Verificación: pytest sv5 en verde (tests `test_f003_r9_*`,
      `_r10_*`).

- [ ] T10: evals (R15, puerta de rutas sensibles de F-011) — actualizar el
      ground truth con los casos de esta feature: IA1 (campos
      importe/descuentos/importe_total del caso ×120), IA3/IA4 (CETOSA,
      elemento base 0,5 mm, bolsa de cuñas → no casar; ORE OIL). Si F-011
      ya está implementada: regenerar fixtures y ejecutar el runner
      (IA3/IA4 en modo determinista). Si no: actualización de los libros
      `evals/ground_truth/*.xlsx`, que rellena el humano.
      | Verificación: runner de evals en verde si existe; si no, MANUAL
      (humano) con constancia en `progress/impl_F-003.md`.

- [ ] T11: docs — `docs/referencia/dominio_negocio_albaranes.md`: pasar de
      🔶 a ✅ las reglas de §10.4 y el punto de matching estricto de §10.5
      que esta feature implementa (el de líneas manuscritas NO: queda 🔶);
      §3.4/§3.3 mencionan las columnas nuevas. `.env.example` de sv6 con
      los flags nuevos (sin valores sensibles). `azure-apps/albaranes.md`
      NO cambia (no varía lo expuesto/consumido entre proyectos); la nota
      de despliegue (4 imágenes: sv2, sv3, sv5, sv6; orden sv3 → sv5 →
      sv6) va en `progress/impl_F-003.md`.
      | Verificación: revisión del diff; ningún secreto.

- [ ] T12: Ejecutar `bash harness/init.sh` en verde (incluye pytest de
      todos los servicios con tests y cobertura del diff).
      | Verificación: `bash harness/init.sh` → ENTORNO LISTO.

- [ ] T13: MANUAL (humano) — verificación integrada en local (Azurite +
      PG local): 1) arrancar sv3 → columnas nuevas creadas
      (`\d albaran_lines_merge`); 2) reprocesar el albarán del caso ×120 →
      línea con importe 191,40 persistido y sin importe disparatado;
      3) albarán ORE OIL → importe de la línea = total del documento;
      4) albarán CETOSA (o equivalente con espesores distintos) → línea
      NUEVA sin precio a revisión, no casada; 5) pegar resultados en
      `progress/impl_F-003.md`. Despliegue en Azure: lo aplica el humano
      con el orden anotado en T11.
      | Verificación: MANUAL (humano), resultados en
      `progress/impl_F-003.md`.
