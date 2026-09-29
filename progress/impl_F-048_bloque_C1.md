<!-- progress/impl_F-048_bloque_C1.md -->
# F-048 · Informe del implementer, menores del bloque B y bloque C1 completos

Texto íntegro de los menores del bloque B (CR-B1/B3/B5/B6) y del bloque C1 (sv2, T13–T16 bis)
tal como lo revisó el reviewer (`progress/review_F-048_bloque_C1.md`, CHANGES_REQUESTED por un
bloqueante en `prompts.yaml`, resuelto con CR-C1). Se sacó de `progress/impl_F-048.md` el
2026-09-24 para que el informe principal quepa en su tope con el bloque C2; allí queda el
resumen con las trazas RED y las evidencias. Aquí no se edita nada.

## Bloque B · menores de la review (CR-B1, CR-B3, CR-B5, CR-B6) — 2026-09-24

**Commits**: `ecac419` CR-B1 · `8a7a46e` CR-B3 · `79a1485` CR-B5 · `51111b7` CR-B6. Los menores 2
y 4 no se tocan (van a T32 y a la medición de §7), como pidió el líder.

- **CR-B1** `capturar_correo.py`: `ruta_ignorada_por_git(ruta)` = `git check-ignore -q` sobre el
  FICHERO de salida (ruta resuelta, `cwd` = sv1). Solo exit 0 vale: versionada, fuera del
  repositorio, sin git o git que no arranca ⇒ `False`. `main()` lo comprueba ANTES de leer el
  `.env` o hablar con Graph y sale con `argparse.error` (código 2). `capturar()` no lo mira: los
  tests siguen usando `tmp_path` por la función. Ojo: el `.gitignore` de sv1 ignora `*.json`
  en todo el servicio, así que un `--directorio` dentro de sv1 git lo da por ignorado (es el
  criterio de R38); los tests de rechazo usan `docs/` y `specs/` de la raíz.
- **CR-B3** `intake_cola_adapter.py`: el blob lateral se guarda en `_guardar_correo`, y su fallo
  sale como `OrchestratorError("blob correo: <Tipo>")`, SIN el mensaje (que podía repetir el
  cuerpo, como demuestra el RED). El PDF y la cola conservan `blob/cola: {exc}` como hoy. Test con
  un almacén que falla citando lo que guardaba, ciclo completo a DEBUG.
- **CR-B5**: `get_contenido` pide `receivedDateTime` en el MISMO GET
  (`$select=subject,uniqueBody,receivedDateTime`) y lo deja en `ContenidoCorreo.recibido_utc`
  (tal cual, `None` si falta); la captura escribe `recibido_utc` (sigue `version` 1: campo
  añadido). **Desviación de design §5** (`$select=subject,uniqueBody`): un campo más en el mismo
  GET de solo lectura, sin cambiar R2; edité la aserción de `$select` del test de T7.
- **CR-B6** `orchestrator_client.py`: `ContextoCorreo | None` con el import bajo `TYPE_CHECKING`;
  un test compara la anotación con la del puerto.

**RED → GREEN** (`python -m pytest <fichero> -q --tb=line` en `services/albaranes-email`):
```
CR-B1 E   AttributeError: module 'capturar_correo' has no attribute 'ruta_ignorada_por_git'
      E   AssertionError: con la ruta rechazada no se lee el .env ni se habla con Graph (x3)
      E   AttributeError: module 'capturar_correo' has no attribute 'shutil' (x2)
      7 failed, 12 passed in 4.97s                                      -> 19 passed in 1.78s
CR-B3 test_f048_r36_logs.py:170: AssertionError: assert 'CENTINELA-F048' not in 'INFO     ht... a Errores\n'
      (log real: "ERROR sv7: blob/cola: no se pudo guardar <id>.correo.json: {... 'cuerpo': '...CENTINELA-F048 ...'}")
      1 failed, 4 passed in 1.74s                                       -> 69 passed (suite sv1)
CR-B5 E   AssertionError: assert ['subject', 'uniqueBody'] == ['subject', '...ivedDateTime']
      E   AttributeError: 'ContenidoCorreo' object has no attribute 'recibido_utc'
      2 failed, 29 passed in 1.91s; captura: E TypeError: ContenidoCorreo.__init__() got an
      unexpected keyword argument 'recibido_utc' (1 error in 1.75s)      -> 71 passed (suite sv1)
CR-B6 test_f048_r7_r10_intake.py:170: AssertionError: assert 'object | None' == 'ContextoCorreo | None'
      1 failed, 9 passed in 2.97s                                       -> 72 passed (suite sv1)
```

## Bloque C1 · sv2 (T13–T16 bis) — 2026-09-24

**Commits**: `1f30462` T13 (+ `08e8fd3`, anotación) · `b0483c7` T14 · `8cb9db6` T15 · `adb488d` T16 ·
`1ef98fe` T16 bis. **Producción** (`services/albaranes-api/`): nuevo `domain/models/lectura_correo.py`;
`domain/models/albaran_models.py`, `application/services/albaran_extraction_service.py`,
`config/prompts.yaml` (ruta sensible), `domain/ports/obras_activas_provider.py`,
`infrastructure/sigrid/{sigrid_api_obras_client,obras_activas_cache}.py`. **Tests**: cinco
`test_f048_*.py`. Sin tocar `composition.py`, `api/app.py`, `_SQL_OBRAS` ni `test_f002_obras_cache.py`.

### Decisiones

1. **`LecturaCorreo`** (`StrictSchemaModel`): `obra_codigos: list[str] = []`, `evidencia: str | None`.
   Sin `max_length` en la evidencia: una respuesta larga haría fallar la extracción entera; el
   recorte a 160 lo hace `OrigenDatos` (bloque A) y el prompt lo pide (menor 7).
2. **Orden del render de fase 1**: obras → catálogo → correo, el correo EL ÚLTIMO, para que su
   texto no se recorra (un correo con `{obras_activas}` no recibe la lista). **Sin marcador y
   sin correo no se añade nada** (ni la nota): R12 habla de añadir «el bloque»; con correo, el
   bloque va al final, como hace F-002 con las obras.
3. **Fase 2 en UNA pasada** (regex sobre la plantilla, `_MARCADORES_FASE_2`): antes se encadenaban
   `str.replace` y un correo (o el JSON de fase 1, que lleva la evidencia del correo) que
   escribiera `{json_fase_1}` o `{sigrid_context}` recibía el relleno dentro, y IA2 ya no veía el
   MISMO bloque que IA1 (R14; RED del paso 2). La compatibilidad de `{sigrid_context}` ausente
   se conserva (mira la plantilla) y tiene test.
4. **Logs**: fase 1 y fase 2 añaden `correo=SI(<caracteres>, <sha8>)` o `correo=NO` (design §5).
5. **Prompt (T16)**: sección `## Correo con el que llegó el albarán` justo tras la de obras, con
   las reglas de R15–R16 y la del menor 7; `schema_hint` declara `lectura_correo.obra_codigos` y
   `.evidencia`. Solo el task de fase 1 lleva `{contexto_correo}` (test sobre el YAML crudo).
6. **Catálogo (T16 bis)**: `CatalogoObras(activas, todas)` frozen con tuplas. El cliente devuelve
   `None` si no llega ninguna obra. La caché guarda el catálogo; `obtener()` da `None` si no hay
   activas (antes, un doble que devolviera `[]` recibía `[]`: el render trata igual los dos) y,
   con activas vacías pero `todas` llenas, ya no reconsulta en cada llamada.
7. **`obras_conocidas()`**: colisiones (menor 5) ⇒ la clave ambigua sale del mapa y UN `WARNING`
   por llamada con `clave <- códigos`; si no queda ninguna clave, `None`. Excepción del
   proveedor ⇒ `None` con `logger.exception`.

### Para quien haga T17–T22

- **`AlbaranExtractionService.obras_conocidas() -> dict[str, str] | None`**: `{normalizar_codigo(c): c}`
  sobre TODAS las obras con contrato (`'945' -> '0945'`, `'A12' -> 'A-12'`), de la MISMA caché que
  el prompt (dentro de la TTL no cuesta consulta). `None` = sin lista ⇒ `validada=null` (R18).
  Las claves ambiguas no están: un código que normalice a una de ellas no cuenta.
- **`lectura_correo`**: `DocumentoAlbaran.lectura_correo: LecturaCorreo | None`
  (`domain/models/lectura_correo.py`), en el documento de fase 1 y en `documento_revisado` de
  fase 2 (mismo modelo). Hay que quitarlo del `data` final (R23). **Aviso**: el pipeline mete
  `phase_1_json` en `debug.phase_1_json` del envelope (`extra_debug` de fase 2): la evidencia de
  IA1 viaja ahí; lo mira T19/T21.
- **Render**: `extract_phase_1(..., contexto_correo=None)` y `review_phase_2(..., contexto_correo=None)`,
  keyword con default; ambas llaman a `_render_task_fase_1(task, correo)`, que pone
  `render_bloque_correo(correo)` (o `NOTA_SIN_CORREO`) en `{contexto_correo}`. Falta que
  `extract_albaran_pipeline.py` y el worker pasen el contexto (T20): hoy nadie lo pasa y todo
  va con la nota fija.

### Fase RED → GREEN (`python -m pytest <fichero> -q --tb=line` en `services/albaranes-api`)

```
T13 test_f048_r15_schema.py
    E   ModuleNotFoundError: No module named 'domain.models.lectura_correo'   1 error in 0.66s -> 7 passed
T14 test_f048_r12_render_fase1.py
    E   TypeError: AlbaranExtractionService._render_task_fase_1() takes 2 positional arguments but 3 were given (x5)
    E   TypeError: AlbaranExtractionService.extract_phase_1() got an unexpected keyword argument 'contexto_correo' (x2)
    test_f048_r12_render_fase1.py:164: AssertionError: assert '(Este albaran no trae texto de correo: ...)' in 'SYSTEM...HINT'
    8 failed in 0.65s                                                      -> 8 passed in 0.66s
T15 test_f048_r14_fase2_sin_marcadores.py, paso 1 (sin el parámetro):
    E   TypeError: AlbaranExtractionService.review_phase_2() got an unexpected keyword argument 'contexto_correo' (x17)
    17 failed, 1 passed in 1.13s
    paso 2 (con el parámetro, antes de la pasada única):
    E   assert 'ATENCION: ... Texto con {json_fase_1}, {sigrid_context}, {revision_rules} y {prompt_fase_1}\n<<<FIN_CORREO>>>'
        in 'Eres un revisor experto de albaranes y factu...'
    1 failed, 17 passed in 1.27s                                           -> 21 passed in 1.49s
T16 test_f048_r16_prompt_yaml.py
    E   AssertionError: assert 0 == 1                                   (el task no trae el marcador)
    E   AssertionError: assert 'del correo solo se lee el código de obra' in '## convenciones generales ...' (y 8 frases más)
    E   AssertionError: assert 'lectura_correo.obra_codigos' in 'devuelve null cuando falte información ...'
    E   AssertionError: assert [] == ['albaran_factura_es.task']
    13 failed, 1 passed in 0.90s                                           -> 14 passed in 0.92s
T16 bis test_f048_r18_lista_obras.py
    E   ImportError: cannot import name 'CatalogoObras' from 'domain.ports.obras_activas_provider'   1 error in 0.94s
    con el puerto, sin cliente, caché ni servicio:
    E   AttributeError: 'AlbaranExtractionService' object has no attribute 'obras_conocidas' (x11)
    E   AttributeError: 'SigridApiObrasClient' object has no attribute 'obtener_catalogo' (x4) / 'obtener_todas' (x2)
    E   AssertionError: assert None == [ObraActiva(codigo='0945', ...)] (x3, caché)
    22 failed, 4 passed in 0.75s                                           -> 26 passed in 0.71s
    y test_f002_obras_cache.py SIN editar: 39 passed (junto con T16 bis: 65 passed in 1.12s)
```
Los 4 que ya pasaban en T16 bis (reproducido en una copia aislada) vigilan lo de hoy: `obtener()`
solo da activas, catálogo inmutable, sin catálogo todo `None` y proveedor de solo `obtener()` ⇒
`todas=None`. El de T15 paso 1: hay prompts de fase 2 que recorrer. El de T16: el fallback de T14.

### Verificaciones MANUAL y lo que queda fuera

Sin MANUAL propia de este bloque. `prompts.yaml`, `albaran_models.py` y `lectura_correo.py` son
rutas sensibles: la evidencia de evals es **T40** (LLM real, se factura, visto bueno del humano).
Que IA1 devuelva de verdad `lectura_correo` con evidencia corta solo lo dirá T40. Fuera: T17–T22
(resolver, worker, logs de sv2, `encolar_extraccion.py`), bloques D–G.

## Resultados reales

- Suites a mano, una detrás de otra: sv2 `226 passed in 3.71s`; sv1 `72 passed in 5.60s`;
  F-048 de sv2 `76 passed` (5 ficheros); comun sin cambios en este encargo.
- `bash harness/init.sh` (tras `1ef98fe`): `ENTORNO LISTO`, exit 0. Raíz `865 passed in 164.83s`;
  **sv1 `72 passed in 21.89s` y sv2 `226 passed in 12.36s` corrieron de verdad** (sin caché); el
  resto, de caché (árbol sin cambios). `PUERTA COBERTURA: 99.5% de 427 líneas cambiadas
  cubiertas (425/427)`. `[AVISO]` de rutas sensibles: ahora 4 (`prompts.yaml`,
  `albaran_models.py`, `lectura_correo.py`, `llm_call_logger.py`), sin `progress/evals_F-048.md`
  (T40). Ruff de la raíz: 1161 avisos, los mismos de antes (el +1 de ese init lo quitó `08e8fd3`).
- `bash harness/init.sh` final (con este informe ya commiteado): exit 0, `ENTORNO LISTO`; raíz
  `865 passed in 182.62s`, sv2 `226 passed in 15.06s`, cobertura 99.5 % (425/427), impl 206/220.

## Evidencias (menores del bloque B y bloque C1)

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv1 72 passed (5.60 s); sv2 226 passed (3.71 s), 76 de ellos F-048; raíz 865 passed |
| Cobertura de las líneas cambiadas | 99.5 % (425/427), `PUERTA COBERTURA` de init.sh |
| Mutación | N/A en un bloque intermedio: campaña completa en T34 (`python -m harness.mutacion --feature F-048`) |
| Tiempo de las suites | sv1 5.60 s (21.89 s bajo coverage); sv2 3.71 s (12.36 s bajo coverage) |
