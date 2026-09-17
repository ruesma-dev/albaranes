<!-- specs/F-047-evals-ciclo-completo/tasks.md -->
# F-047 · Tareas

Rigor `critico`: **fase RED obligatoria** (el test antes del código, con su
traza en `progress/impl_F-047.md`), cobertura >= 80 % de lo cambiado y campaña
de mutación SIN tope, sin supervivientes injustificados. Un commit por tarea
(`F-047 Tn: ...`), rama `feature/F-047-evals-ciclo-completo`.

Los tests de T1–T17 corren SIN pipeline levantado: dobles del repositorio, del
publicador y del reloj. Lo que exige la infraestructura real es MANUAL (T21–T24).

Orden por valor, y la ficha del caso (T14) va ANTES que el pulido del informe:
con T1–T8 el ciclo recorre el pipeline y deja informe; **con T14 el humano ya
puede contrastar contra el papel**, que es lo que pidió; T9–T13 y T15–T18 lo
hacen legible y capturan su revisión. Si el trabajo se corta, lo entregado hasta
T8 ya vale, y hasta T14 vale mucho más.

- [ ] T1: `evals/inyeccion.py`: entrada que replica `IntakeColaClient` con `RepositorioWorkflows`, `AlmacenBlobs` y `PublicadorColas`; `pasada_id`, `document_id` por caso y `correlation_key` UNIQUE  |  Verificación: `python -m pytest tests/test_f047_r2_r16_inyeccion.py -q` (dobles, sin Azurite)
- [ ] T2: `evals/lectura_bbdd.py`: los `SELECT` de los cinco hitos y la proyección de lo leído al vocabulario de los libros, reutilizando las `proyectar_*` que ya existen; sesión de solo lectura  |  Verificación: `python -m pytest tests/test_f047_r3_lectura_solo_select.py -q` (con un test que aborta ante cualquier sentencia de escritura)
- [ ] T3: `evals/espera.py`: hitos H1–H5, plazo por hito desde el último avance, retroceso exponencial y vigilancia de las tres colas `-poison`  |  Verificación: `python -m pytest tests/test_f047_r4_espera.py -q` (reloj falso: sin esperas reales)
- [ ] T4: el gesto de revisor de sv4 cuando sv3 no auto-selecciona contrato: fijar el declarado y republicar `MensajeValoracion`, marcando el caso «selección no medida»  |  Verificación: `python -m pytest tests/test_f047_r5_seleccion_contrato.py -q`
- [ ] T5: aislamiento: baja lógica de las pasadas anteriores del banco por la vía del sistema, solo sobre el prefijo `eval/`, y `--limpiar <pasada_id>`  |  Verificación: `python -m pytest tests/test_f047_r16_r17_aislamiento.py -q` (incluye el test de que el filtro nunca corre sin prefijo)
- [ ] T6: `evals/preflight.py`: Azurite, Postgres, sv2/sv3/sv6 consumiendo, sv5 en :8002, claves LLM, `SIGRID_API_*`, ficheros y fixtures; y el guardarraíl que se niega si algo no es local  |  Verificación: `python -m pytest tests/test_f047_r7_r21_preflight.py -q`
- [ ] T7: `evals/ciclo.py`: la pasada entera (preparar → inyectar → esperar → leer → comparar) con concurrencia acotada y `--casos` filtrando TODAS las fases  |  Verificación: `python -m pytest tests/test_f047_r1_r23_ciclo.py -q` (pipeline simulado por dobles)
- [ ] T8: `evals/runner.py`: `corrida_ciclo()`, `corrida_completa()` renombrada a `corrida_por_fases()` sin cambio de conducta, `--por-fases` y `MODO: ciclo` en la línea parseable  |  Verificación: `python -m pytest tests/test_f047_r19_r20_formas.py -q`
- [ ] T9: `evals/atribucion.json` + su carga validada contra las tablas `OBSERVABLES`, que ABORTA ante un campo que ninguna proyección produce  |  Verificación: `python -m pytest tests/test_f047_r12_mapa.py -q`
- [ ] T10: `evals/atribucion.py`: las cuatro reglas en orden (línea ausente, identidad dudosa, dependencia que falló, propio), ganando la fase MÁS TEMPRANA  |  Verificación: `python -m pytest tests/test_f047_r8_r9_r10_atribucion.py -q`
- [ ] T11: `evals/modelos.py`: `Discrepancia` con `atribucion`/`fase_origen`/`causa`, fase ROJA solo por propios y pasada NO_EVALUABLE con indeterminados  |  Verificación: `python -m pytest tests/test_f047_r11_veredicto.py -q`
- [ ] T12: IA4 OMITIDO cuando no llegó a ejecutarse, reconociendo sus líneas en `raw_ia_envelope_json` por `match_method` y el sufijo `| IA4:`, con test atado al código de sv6  |  Verificación: `python -m pytest tests/test_f047_r15_ia4_omitida.py -q`
- [ ] T13: `evals/salidas.py` (volcado fuera de git), `--reutilizar <pasada_id>` y `--desde persistencia|valoracion`; `evals/salidas/` a `.gitignore`  |  Verificación: `python -m pytest tests/test_f047_r24_r25_coste.py -q` y `git check-ignore evals/salidas/x.json`
- [ ] T14: `evals/ficha.py`: ficha por caso con cabecera del papel (desde `mapa_casos.json` + ruta local), tabla por fase con la costura `ENTRÓ | SALIÓ | ESPERADO | ATRIBUCIÓN`, escrita en `evals/salidas/<pasada>/fichas/`  |  Verificación: `python -m pytest tests/test_f047_r26_r27_r28_ficha.py -q`
- [ ] T15: la ficha de UN caso sin ejecutar el ciclo (`python -m evals.ficha --caso HOR-003`) desde el volcado, y el modo por defecto que solo emite ficha de los casos no limpios  |  Verificación: `python -m pytest tests/test_f047_r29_r30_ficha_suelta.py -q`
- [ ] T16: PODA de valores del informe de `progress/`: campo, veredicto y atribución, con puntero a la ficha; ningún importe, precio ni cantidad  |  Verificación: `python -m pytest tests/test_f047_r31_informe_sin_valores.py -q` (test que falla si el informe contiene un valor numérico del albarán)
- [ ] T17: `evals/revision_manual.py` + `.json`: registro versionado por caso/fase/campo con veredicto, nota, arreglo, fecha, pasada y `huella_esperado`; sin valores; CADUCADA cuando la huella deja de casar; y NO cambia ningún veredicto  |  Verificación: `python -m pytest tests/test_f047_r32_a_r35_revision_manual.py -q`
- [ ] T18: `evals/mapa_casos.json` gana `clasificacion`, `familia_en_catalogo` y `criterios_residuos`, escritos por `evals/revision/`, que la ficha y el informe consumen  |  Verificación: `python -m pytest tests/test_f047_r37_mapa_casos.py -q`
- [ ] T19: `evals/informe.py`: cuadro propios/arrastrados/indeterminados/omitidos, «Dónde nace cada fallo», «Entrada que da el sistema», «Costuras que NO vigila», los grupos de expectativa y el estado de la revisión manual (revisados / sin revisar / caducados)  |  Verificación: `python -m pytest tests/test_f047_r13_r33_r36_r37_r38_informe.py -q`
- [ ] T20: `evals/README.md` e `infra/docs/levantar-pipeline-local.md`: cómo se lanza el ciclo, cómo se lee una ficha, cómo se anota una revisión y las costuras declaradas de design §11  |  Verificación: revisión del reviewer contra `design.md` §7, §9, §10 y §11
- [ ] T21: Cobertura de las líneas cambiadas >= 80 % (nivel `critico`)  |  Verificación: `bash harness/init.sh` (sección de cobertura) en verde
- [ ] T22: Campaña de mutación COMPLETA (sin tope): cada superviviente muere con un test nuevo o queda justificado por escrito en `progress/mutacion_F-047.md`, ninguno `PENDIENTE`  |  Verificación: `python -m harness.mutacion --feature F-047`
- [ ] T23: Levantar el pipeline local y pasar un solo caso de punta a punta, comprobando los cinco hitos en la base y leyendo su ficha  |  Verificación: MANUAL (humano) · `powershell -ExecutionPolicy Bypass -File .\infra\local\arrancar_local.ps1 -SinSv1` y `python -m evals.runner --con-llm --feature F-047 --casos RES-001`
- [ ] T24: Pasada ACOTADA a familias distintas: contrastar las fichas contra el papel y anotar la conclusión de al menos un caso en `evals/revision_manual.json` (R39)  |  Verificación: MANUAL (humano) · `python -m evals.runner --con-llm --feature F-047 --casos RES-001,HOR-001,MOR-001,GEN-001,FER-001,COM-001`
- [ ] T25: Corrida de REPROCESO sobre un caso ya procesado: duplicado y re-fetch no pierden `contexto_linea` ni anulan las seis `tipologia*` (R18, R40)  |  Verificación: MANUAL (humano) · `python -m evals.runner --con-llm --feature F-047 --casos RES-001 --reproceso`
- [ ] T26: Pasada de ciclo sobre los 59 casos, cuando el humano decida pagarla (R40)  |  Verificación: MANUAL (humano) · `python -m evals.runner --con-llm --feature F-047`
- [ ] T27: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
