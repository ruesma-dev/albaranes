<!-- specs/F-045-banco-evals-revision-manual/tasks.md -->
# F-045 · Tareas

Rigor `critico`: **fase RED obligatoria** (el test falla ANTES de la
implementación y la traza va al informe), cobertura >= 80 % de lo tocado y
campaña de mutación **completa** sin supervivientes injustificados.

Orden pensado para que la **capa 1** (el banco sembrado) dé valor aunque la
capa 2 se quede a medias: T1–T12 cierran el volcado; T13 salda la deuda del
banco; T14–T16 son el catálogo de decisiones. Un commit por tarea
(`F-045 Tn: ...`).

- [ ] T1: Crear `evals/revision/vocabulario.json` y `vocabulario.py` (familias, orígenes de línea y de precio, con sus sinónimos) y que un valor no reconocido aborte.  |  Verificación: `pytest tests/test_f045_r5_r6_vocabulario.py` (R5, R6); traza RED en el informe
- [ ] T2: Crear `evals/revision/modelos.py` y `lectura.py`: del Excel plano a `list[FilaPlana]`, con las 20 columnas por nombre y no por posición.  |  Verificación: `pytest tests/test_f045_r1_lectura.py` con un `.xlsx` fabricado en el propio test (sin red ni BBDD)
- [ ] T3: `reparto.clave_natural`, `agrupar_por_albaran` y `asignar_casos_id` contra `evals/mapa_casos.json`, sembrado con los 7 casos RES existentes.  |  Verificación: `pytest tests/test_f045_r7_r8_casos_id.py` (R7, R8: reimportar no crea caso nuevo)
- [ ] T4: Discriminación de fila impresa vs deducida a partir de la columna de origen de línea; la deducida NUNCA va a IA1.  |  Verificación: `pytest tests/test_f045_r3_impresa_vs_deducida.py` (R3)
- [ ] T5: Convenios de celda: vacío copiado -> `?`, celda derivada de «no viene en el albarán» -> vacía, y el recuento por columna.  |  Verificación: `pytest tests/test_f045_r9_r10_r13_celdas.py` (R9, R10, R13)
- [ ] T6: Reparto a IA1 (cabeceras y líneas) e IA2 (contexto, con el LER de residuos), incluidos los `?` de `numero_albaran`, `obra_codigo`, `obra_nombre` y `cif`.  |  Verificación: `pytest tests/test_f045_r2_r11_r12_ia1_ia2.py` (R2, R11, R12)
- [ ] T7: Reparto a IA3 (líneas valoradas y sintéticas esperadas) y a IA4 (`concilia` de las líneas `NUEVA`), con `precio_source` según la columna de origen.  |  Verificación: `pytest tests/test_f045_r2_r4_ia3_ia4.py` (R2, R4)
- [ ] T8: Reparto a `INPUTS.CASOS` y a `RESULTADO_FINAL` (datos generales, líneas y líneas añadidas).  |  Verificación: `pytest tests/test_f045_r2_inputs_final.py` (R2)
- [ ] T9: `escritura.py`: copia de seguridad previa, escritura por pestaña respetando las filas de título y sin tocar `caso_id` ajenos.  |  Verificación: `pytest tests/test_f045_r15_r16_r17_escritura.py` (R15, R16, R17)
- [ ] T10: CLI `python -m evals.revision --origen <xlsx> [--dry-run]` con el informe de importación de R14 a `progress/import_F-045.md`.  |  Verificación: `pytest tests/test_f045_r14_r18_cli.py` (R14, R18: dos pasadas dejan lo mismo)
- [ ] T11: `albaranes.py`: normalización del código y emparejado caso <-> PDF, con la lista de huérfanos y ambiguos.  |  Verificación: `pytest tests/test_f045_r20_r21_albaranes.py` (R20, R21)
- [ ] T12: Pasada real del importador sobre el Excel del humano y `python -m evals.conversor`; commit SOLO de los fixtures, el mapa y los datos.  |  Verificación: `python -m evals.conversor` termina en 0 y `git status` no muestra ni `.pdf` ni `.xlsx` (R19, R22)
- [ ] T13: `OBSERVABLES` de IA1/IA2 en `evals/procesos/sv2_extraccion.py` y su uso en `evals/runner.py`, con los campos no observables en el informe.  |  Verificación: `pytest tests/test_f045_r23_r24_observables.py` (R23, R24)
- [ ] T14: Crear `evals/patrones.json` con los nueve patrones, sus casos, la decisión candidata y las dos respuestas del filtro de robustez.  |  Verificación: `pytest tests/test_f045_r25_r28_patrones.py` (R25–R28: casos existentes, filtro obligatorio, descartadas sin ficha)
- [ ] T15: Actualizar `evals/README.md`: comando nuevo, catálogo de patrones, qué se versiona y qué no.  |  Verificación: `pytest tests/test_f039_r1_r2_r23_r25_documentos.py` y revisión del humano
- [ ] T16: Añadir a `harness/features.json` las fichas de arreglo de `design.md` §7, en el orden de prioridad allí fijado y en estado `pending`.  |  Verificación: `python -m harness.backlog` regenera `BACKLOG.md` y `bash harness/init.sh` valida el JSON (R29)
- [ ] T17: Cerrar cobertura >= 80 % sobre lo tocado.  |  Verificación: `python -m harness.cobertura --feature F-045`
- [ ] T18: Campaña de mutación COMPLETA (sin tope) sobre `evals/revision/` y el diff de `evals/runner.py`; cada superviviente, test nuevo o justificación escrita.  |  Verificación: `python -m harness.mutacion --feature F-045` y análisis en `progress/impl_F-045.md`
- [ ] T19: Validar con el humano la tabla de reparto de `design.md` §3, el mapa de familias (D1) y el campo `servicios` de la ficha (D6).  |  Verificación: MANUAL (humano)
- [ ] T20: Pasada de evals con LLM sobre los casos nuevos.  |  Verificación: MANUAL (humano) — `python -m evals.runner --con-llm --feature F-045`, informe en `progress/evals_F-045.md`
- [ ] T21: Ejecutar `bash harness/init.sh` en verde.  |  Verificación: `bash harness/init.sh` termina con exit code 0
