<!-- specs/F-047-evals-ciclo-completo/tasks.md -->
# F-047 · Tareas

Rigor `critico`: **fase RED obligatoria** (el test antes del código, con su
traza en `progress/impl_F-047.md`), cobertura >= 80 % de lo cambiado y campaña
de mutación SIN tope y sin supervivientes injustificados. Un commit por tarea
(`F-047 Tn: ...`), rama `feature/F-047-evals-ciclo-completo`.

Orden por valor: T1–T6 dejan el ciclo corriendo y reaprovechable; T7–T11 lo
hacen legible; T12–T14 lo documentan. Si el trabajo se corta a mitad, lo
entregado hasta T6 ya vale.

- [ ] T1: `evals/procesos/sv3_contrato.py`, parte PURA: del envelope de sv2 (`phase_merge`) al `ContextoValoracion`, con `contexto_linea` y clasificación, reutilizando `albaran_normalizer`, `contexto_linea_merger` y `obra_code_normalizer` de sv3  |  Verificación: `python -m pytest tests/test_f047_r2_sv3_contexto.py -q` (fixtures, sin red)
- [ ] T2: `evals/procesos/sv2_extraccion.py`: el subproceso pasa por `resolver_clasificacion` y `phase_merge.construir_envelope_final` y devuelve el envelope de `q-persistencia` además de IA1 e IA2  |  Verificación: `python -m pytest tests/test_f047_r2_r5_envelope_sv2.py -q` (LLM falso)
- [ ] T3: `evals/procesos/sv3_contrato.py`, parte SUBPROCESO: contratos de sigrid-api SOLO lectura, agrupados por (CIF, obra), con `elegir_contrato_probable`; nunca PDF ni escritura  |  Verificación: `python -m pytest tests/test_f047_r26_r27_sigrid_solo_lectura.py -q` (cliente falso que aborta ante cualquier método de escritura)
- [ ] T4: `evals/cadena.py`: encadena IA1 → IA2 → contrato → IA3 → IA4 → build de UN caso con adaptadores inyectados, y corta con OMITIDO heredado cuando una fase no produce  |  Verificación: `python -m pytest tests/test_f047_r1_r3_r4_cadena.py -q` (adaptadores falsos, sin red)
- [ ] T5: `evals/salidas.py`: caché por caso y fase con huella (sha256 del albarán, proveedor, modelo, sha256 del `prompts.yaml`), `--reutilizar` y `--desde`; `evals/salidas/` a `.gitignore`  |  Verificación: `python -m pytest tests/test_f047_r29_r30_r31_r32_cache.py -q` y `git check-ignore evals/salidas/x.json`
- [ ] T6: `evals/runner.py`: `corrida_ciclo()`, `corrida_completa()` renombrada a `corrida_por_fases()` sin cambio de conducta, `--por-fases`, y `--casos` filtrando TODAS las fases  |  Verificación: `python -m pytest tests/test_f047_r19_r20_r28_formas.py -q`
- [ ] T7: `evals/preflight.py`: nombra las dependencias que faltan (claves LLM, `SIGRID_API_*`, ficheros, fixtures) y sale NO_EVALUABLE sin gastar una llamada; caso sin contrato = NO_EVALUABLE, nunca contrato vacío  |  Verificación: `python -m pytest tests/test_f047_r23_r24_r25_preflight.py -q`
- [ ] T8: `evals/atribucion.json` + su carga validada contra las tablas `OBSERVABLES`, que ABORTA ante un campo que ninguna proyección produce  |  Verificación: `python -m pytest tests/test_f047_r13_r14_mapa.py -q`
- [ ] T9: `evals/atribucion.py`: las cuatro reglas en orden (línea ausente, identidad dudosa, dependencia que falló, propio), con la fase MÁS TEMPRANA ganando  |  Verificación: `python -m pytest tests/test_f047_r6_a_r10_atribucion.py -q`
- [ ] T10: `evals/modelos.py`: `Discrepancia` con `atribucion`/`fase_origen`/`causa`, fase ROJA solo por propios, pasada NO_EVALUABLE con indeterminados  |  Verificación: `python -m pytest tests/test_f047_r11_r12_veredicto.py -q`
- [ ] T11: `evals/mapa_casos.json` gana `clasificacion`, `familia_en_catalogo` y `criterios_residuos`, escritos por `evals/revision/`  |  Verificación: `python -m pytest tests/test_f047_r33_mapa_casos.py -q` y `python -m evals.revision --sin-escribir`
- [ ] T12: `evals/informe.py`: `MODO: ciclo`, cuadro propios/arrastrados/indeterminados/omitidos, «Dónde nace cada fallo», «Entrada que ahora produce el sistema» y los grupos de expectativa; no observables y sin clasificar intactos  |  Verificación: `python -m pytest tests/test_f047_r22_r33_a_r36_informe.py -q`
- [ ] T13: `evals/README.md` y `progress/impl_F-047.md`: las dos formas de correr, el eje de atribución y las costuras declaradas que el ciclo NO cubre (colas, SQL, grounding de cabecera, PDF de contrato)  |  Verificación: revisión del reviewer contra `design.md` §1 y §7
- [ ] T14: Cobertura de las líneas cambiadas >= 80 % (nivel `critico`)  |  Verificación: `bash harness/init.sh` (sección de cobertura) en verde
- [ ] T15: Campaña de mutación COMPLETA (sin tope, `critico`): cada superviviente muere con un test nuevo o queda justificado por escrito en `progress/mutacion_F-047.md`, ninguno `PENDIENTE`  |  Verificación: `python -m harness.mutacion --feature F-047`
- [ ] T16: Pasada de ciclo ACOTADA con LLM: `--casos RES-001,HOR-001,MOR-001,GEN-001,FER-001,COM-001 --con-llm`, comprobando que la atribución apunta a la fase correcta (R37)  |  Verificación: MANUAL (humano) · `python -m evals.runner --con-llm --feature F-047 --casos RES-001,HOR-001,MOR-001,GEN-001,FER-001,COM-001`
- [ ] T17: Pasada de ciclo sobre los 59 casos, cuando el humano decida pagarla (R38)  |  Verificación: MANUAL (humano) · `python -m evals.runner --con-llm --feature F-047`
- [ ] T18: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
