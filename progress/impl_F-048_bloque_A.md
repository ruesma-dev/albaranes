<!-- progress/impl_F-048_bloque_A.md -->
# F-048 · Informe del implementer, bloque A completo

Texto íntegro del bloque A y de su pasada 1 de review, tal como lo aprobó el reviewer
(`4a6802b`). Se sacó de `progress/impl_F-048.md` el 2026-09-23 para que el informe
principal quepa en su tope de 220 líneas con el bloque B; allí queda el resumen con las
trazas RED y las evidencias. Aquí no se edita nada.

## Bloque A · comun (T1–T5) — 2026-09-23

**Commits**: `c351b18` T1 contexto (R1) · `57516d6` T2 `correo_blob` (R8, R9) · `bd5a341` T3 bloque del
prompt (R12, R13) · `940031e` T4 logger (R37) · `64eaf13` T5 `origen_datos` (R24, R31) · `172d514` los
5 avisos de ruff que añadí yo (sin cambio de comportamiento).
**Producción**: nuevos `ruesma_comun/correo/{__init__,contexto,prompt}.py` y `contratos/origen_datos.py`;
cambiados `colas/mensajes.py`, `llm/llm_call_logger.py` y `contratos/__init__.py`.
**Tests**: `services/albaranes-comun/tests/test_f048_{r1_contexto,r8_r9_mensaje,r13_prompt,r37_llm_logger,r24_origen_datos}.py`.
Los textos son inventados, con el centinela `CENTINELA-F048`. Sin red ni BBDD.

**`normalizar_codigo`** empezó como desviación, por decisión del humano. Hoy ya no lo es: la v4 la recoge
como R18/D9 (mayúsculas, fuera lo no alfanumérico y los ceros; vacío ⇒ `None`). NFKC, en CR-A4.

### Decisiones donde la spec no llegaba al detalle

1. **Huella** = sha256 de `asunto + "\n\n" + cuerpo recortado`. Con solo el cuerpo, todos los correos
   con `uniqueBody` vacío (R3) compartirían huella. `caracteres_originales` cuenta el cuerpo
   normalizado y antes del recorte, así que `truncado` quiere decir que se perdió texto.
2. **Normalizar** es solo tocar espacios: `\r\n` pasa a `\n`, los espacios horizontales (tabuladores y
   no separables incluidos) se juntan en uno, se recortan los bordes de cada línea y se deja como mucho
   una línea en blanco. El asunto se deja en una línea y no se recorta.
3. **`leer_contexto_correo`** devuelve `None` si el blob falta (`FileNotFoundError`, de la que hereda
   `BlobNoEncontradoError`) o si no valida (JSON, UTF-8, esquema). **Un fallo de red se propaga**, para
   que la cola reintente. El log lleva el nombre del blob y el tipo o número de errores, nunca
   `str(exc)`, porque pydantic cita la entrada.
4. **Bloque del prompt**: `ADVERTENCIA_DATO` va **antes** de `<<<INICIO_CORREO>>>`, así se lee primero
   y sobrevive a la redacción. Dentro van `(huella sha256=…)`, el asunto, el cuerpo (o «sin cuerpo»), una
   nota si está recortado y `<<<FIN_CORREO>>>`. **Toda racha `<<<`/`>>>` del texto pasa a `«`/`»`**, con
   lo que ningún correo puede escribir una marca. Sin tildes, como el catálogo de familias.
5. **`redactar_correo`** deja `[correo omitido: sha256=<huella del contexto>, caracteres=<longitud del
   segmento>]`; si no hay línea de huella, la calcula sobre el segmento. Un bloque sin cerrar se redacta
   hasta el final.
6. **`LlmCallLogger._sin_correo`** hace una copia recursiva (dict, list, tuple) y redacta cada `str`. No
   muta el dict del llamador. Desde CR-A1 se aplica a todo lo que se escribe, no solo a `request_summary`.
7. **`OrigenDatos`/`OrigenCampo`** usan `extra="ignore"`. `fuente` y `motivo` son `Literal` derivados de
   las constantes: un motivo desconocido no valida. `evidencia` junta espacios, se recorta a 160 y,
   vacía, pasa a `None`. `hay_discrepancia` es una propiedad y no se serializa. No hay `partida` (D8).
   Importar `ruesma_comun.correo` no arrastra el SDK de Azure: `CONTENEDOR_INPUT` se importa dentro de
   guardar y de leer.

### Fase RED → GREEN (salidas reales; `python -m pytest tests/<fichero> -q --tb=line` en `services/albaranes-comun`)

**T1** `test_f048_r1_contexto.py`. RED → GREEN `35 passed in 1.39s`
```
E   ModuleNotFoundError: No module named 'ruesma_comun.correo'
ERROR tests/test_f048_r1_contexto.py
1 error in 1.10s
```
**T2** `test_f048_r8_r9_mensaje.py`. RED → GREEN `7 passed`
```
E   AttributeError: 'MensajeExtraccion' object has no attribute 'correo_blob'
E   AssertionError: assert set() == {'correo_blob'}
FAILED ...::test_f048_r9_correo_blob_es_nulo_por_defecto
FAILED ...::test_f048_r9_con_correo_el_campo_viaja_y_vuelve
FAILED ...::test_f048_r9_mensaje_viejo_sin_campo_valida_en_el_modelo_nuevo
FAILED ...::test_f048_r8_con_60000_caracteres_el_mensaje_mide_menos_de_1_kb
FAILED ...::test_f048_r8_el_mensaje_no_declara_campos_de_texto_del_correo
5 failed, 2 passed in 1.00s
```
Los 2 que ya pasaban vigilan la compatibilidad de hoy: el JSON sin correo es igual y un modelo sin el
campo ignora el campo.

**T3** `test_f048_r13_prompt.py`. RED → GREEN `17 passed in 0.56s`
```
E   ModuleNotFoundError: No module named 'ruesma_comun.correo.prompt'
ERROR tests/test_f048_r13_prompt.py
1 error in 0.95s
```
La primera ejecución con el código dio 1 fallo, pero el error era del test: cortaba el bloque sin cerrar
desde el principio y no desde la marca. Corregí el test.

**T4** `test_f048_r37_llm_logger.py`. RED → GREEN `5 passed in 4.39s`
```
E   assert 'CENTINELA-F048' not in '{\n  "times...true\n  }\n}'
E   assert 'CENTINELA-F048' not in '{\n  "times...true\n  }\n}'
FAILED ...::test_f048_r37_instructions_y_user_text_sin_el_cuerpo
FAILED ...::test_f048_r37_redacta_a_cualquier_profundidad
2 failed, 3 passed in 4.07s
```
Los 3 que ya pasaban vigilan lo que el cambio no debe romper: lo que no es correo queda igual, no se muta
el dict y el logger deshabilitado no escribe. La primera ejecución con el código dio 1 fallo por el mismo
error de test que en T3 (un `startswith` sin la advertencia).

**T5** `test_f048_r24_origen_datos.py`. RED → GREEN `44 passed in 0.60s` (incluye los casos de `normalizar_codigo`)
```
E   ImportError: cannot import name 'OrigenCampo' from 'ruesma_comun.contratos'
ERROR tests/test_f048_r24_origen_datos.py
1 error in 1.34s
```

### `bash harness/init.sh` tras T5 (real)

`ENTORNO LISTO`. Raíz `865 passed in 250.45s`; comun `251 passed, 3 skipped in 144.32s`; el resto de
servicios salió de caché (sin cambios en su árbol). **`PUERTA COBERTURA: 100.0% de 167 líneas cambiadas
cubiertas (167/167, umbral 80%, nivel critico)`**. Siguen los dos avisos que ya había: sv1 sin tests (lo
resuelve T6) e infra. Ruff da 0 avisos en los ficheros nuevos; los que quedan en `llm_call_logger.py` y
`mensajes.py` ya estaban.

### API que dejo para los bloques siguientes

**B · sv1**
- `construir_contexto_correo(asunto, cuerpo, *, max_caracteres=MAX_CARACTERES_DEFECTO, recibido_utc=None)`
  acepta `None`. Con `uniqueBody` vacío se pasa `cuerpo=""` (R3) y **nunca** el `body`. Con `max <= 0`
  lanza `ValueError`, así que conviene validar `CORREO_MAX_CARACTERES` en settings.
- `guardar_contexto_correo(almacen, document_id, ctx) -> nombre` escribe `input/{id}.correo.json` con
  `put_json(contenedor, nombre, objeto)`, compatible con `AlmacenBlobs`, cuyo log no lleva texto. El
  nombre que devuelve va en `MensajeExtraccion(..., correo_blob=nombre)`. `ctx.sha256` sirve para
  `correo_sha256` en meta (R10) y para el `sha8` de los logs. **Nunca loguear `ctx.asunto` ni `ctx.cuerpo`.**

**C · sv2**
- `leer_contexto_correo(almacen, msg.correo_blob)` devuelve `ContextoCorreo | None`, y el aviso del
  `None` ya va logueado sin texto. **Los errores de red se propagan**: T20 decide qué hacer con ellos
  (R11 no dice nada).
- `render_bloque_correo(ctx | None)` es el texto de `{contexto_correo}`; con `None` devuelve
  `NOTA_SIN_CORREO`, sin marcas. `redactar_correo(texto)` sirve para cualquier log de prompts;
  `LlmCallLogger` ya lo aplica, y sv2 y sv5 lo heredan por su reexport.
- Resolver: `from ruesma_comun.contratos import OrigenDatos, OrigenCampo, normalizar_codigo`, más
  `FUENTE_*` y `MOTIVO_*` de `ruesma_comun.contratos.origen_datos`. **`normalizar_codigo` devuelve
  `str | None`**, y `None` significa sin código: un papel sin código no crea discrepancia. Para
  meterlo en `data`, `model_dump(mode="json")`.

**D · sv3 / D bis · sv4**: `MOTIVO_REVISION_OBRA_CORREO_{DISTINTA,AMBIGUA}` y `MOTIVOS_REVISION_ORIGEN`
se importan de `ruesma_comun.contratos`, sin copiarlos.

### Evidencias (bloque A)

| Evidencia | Valor real |
|---|---|
| Tests F-048 del bloque | 108 passed (5 ficheros), 4.04 s |
| Suite comun / raíz | 251 passed + 3 skipped, 144.32 s / 865 passed, 250.45 s (init.sh) |
| Cobertura de las líneas cambiadas | 100.0 % (167/167), `PUERTA COBERTURA` |
| Mutación | se lanza en T34, con la feature completa (`python -m harness.mutacion --feature F-048`) |

Este bloque no tiene verificaciones MANUAL: las de la feature son T36–T40. Queda fuera todo lo demás (T6–T41).

## Bloque A · cambios de la review (pasada 1) — 2026-09-23

Respuesta a `progress/review_F-048_bloque_A.md` (CHANGES_REQUESTED). Los menores 5 y 7 son avisos
para el bloque C y no se tocan aquí. El 6 no pide cambio y el 8 lo hizo el líder.

**Commits**: `32b3a57` CR-A1 logger (R37, bloqueante 1; T4 vuelve a `[x]`) · `87972da` CR-A2 renombra
`r19`→`r18` (menor 2) · `606da58` CR-A3 los docstrings citan R18 y D9 (menor 3) · `56ad7f0` CR-A4 NFKC
(menor 4) · `8568cec` quita una línea en blanco entre imports que puse en CR-A1 y que el ruff de la raíz rechaza.

### CR-A1 · R37 en todo lo que escribe el logger

`log_call` pasa por `_sin_correo` el **payload entero** que va a disco: petición, respuesta (después
de `_serializable`) y error. También redacta las **claves** `str` de los dicts, y `json.dumps` usa
`default=_str_sin_correo`, así que un objeto que no es JSON sale por su `str` ya redactado. Este último
era un cuarto hueco, de la misma familia que los tres de la review: un objeto opaco en `request_summary`
saltaba `_sin_correo` y llegaba entero a `default=str`. Tests nuevos, con el centinela buscado en **todo
lo que hay en `tmp_path`** (`rglob`): (a) `_RespuestaSdk`, un modelo pydantic con `instructions`;
(b) el bloque anidado en la respuesta: `output[].content[].text`, una tupla y una clave de dict; (c) un
`error` que lo contiene; (d) un objeto que no es JSON. Además, con el `Response` real de `openai`
(3.0.0 en el venv, creado con `model_construct`) y `{"raw_sdk_response": resp}`, sale `centinela en
disco: False`. La review había reproducido `True`.

RED (`python -m pytest tests/test_f048_r37_llm_logger.py -q --tb=line`, con el logger de HEAD):
```
E   assert 'CENTINELA-F048' not in '{\n  "times..."{}"\n  }\n}'
        bra 1234. CENTINELA-F048\n<<<FIN_CORREO>>>",
E   assert 'CENTINELA-F048' not in '{\n  "times...   }\n  }\n}'
E   assert 'CENTINELA-F048' not in '{\n  "times...se": null\n}'
E   assert 'CENTINELA-F048' not in '{\n  "times...se": null\n}'
FAILED ...::test_f048_r37_respuesta_pydantic_con_instructions_sin_el_cuerpo
FAILED ...::test_f048_r37_bloque_anidado_en_la_respuesta_sin_el_cuerpo
FAILED ...::test_f048_r37_error_con_el_bloque_sin_el_cuerpo
FAILED ...::test_f048_r37_objeto_no_json_se_escribe_sin_el_cuerpo
4 failed, 5 passed in 0.90s
```
GREEN: `9 passed in 0.69s`. Con el código ya escrito, la primera ejecución dio 2 fallos por un error
del test: esperaba `[correo omitido` justo después del prefijo, pero la advertencia va **antes** de la
marca y se queda (el mismo tropiezo que en T3/T4). Corregí la aserción (`{ADVERTENCIA_DATO}\n[correo
omitido: `) y repetí el RED contra el logger de HEAD (`git stash` solo del logger): son los 4 fallos de
arriba. Ruff del logger: 10 avisos antes y 10 después, todos previos (BLE001, S110, UP017).

### CR-A4 · NFKC en `normalizar_codigo`

`unicodedata.normalize("NFKC", str(codigo))` va antes de las mayúsculas, la limpieza y los ceros.
**Decisión sobre `'0945²'`**: da `'9452'`. NFKC convierte el superíndice en `2`, y no añado una regla
para quitarlo, porque D9 no la recoge y sería una regla nueva. Si `9452` no es una obra de la lista,
R18 lo descarta y no cuenta. Si lo fuera, se asignaría esa obra (improbable: IA1 devuelve ASCII). La
alternativa de antes, `'945²'`, tampoco casaba con nada. Queda en el docstring y fijado por un test.

RED (`python -m pytest tests/test_f048_r24_origen_datos.py -q --tb=line -k "nfkc or superindice"`):
```
E   AssertionError: assert '０９４５' == '945'
E   AssertionError: assert 'ＡＢ12' == 'AB12'
E   AssertionError: assert '０００' == None
E   AssertionError: assert '945²' == '9452'
4 failed, 44 deselected in 1.73s
```
GREEN: `48 passed in 1.08s` (el fichero entero).

### Resultados reales

- `bash harness/init.sh`: `ENTORNO LISTO` (cifras en «Evidencias»; esta vez comun corrió sin caché).
  Avisos previos: sv1 sin tests (T6), infra y ruff de la raíz (1161, deuda).
- **`PUERTA RUTAS SENSIBLES [evals]`**: ahora se aplica y da `[AVISO]`, que no bloquea. Falta
  `progress/evals_F-048.md` para `llm/llm_call_logger.py` (propone `python -m evals.runner --con-llm
  --feature F-048`). **No hay evidencia de evals**: es T40, se factura y requiere el visto bueno del humano.

### Evidencias (review del bloque A)

| Evidencia | Valor real |
|---|---|
| Tests F-048 del bloque | 116 passed (5 ficheros; eran 108), 8.06 s |
| Suite comun / raíz | 259 passed + 3 skipped, 155.95 s / 865 passed, 362.91 s (init.sh) |
| Cobertura de las líneas cambiadas | 100.0 % (173/173), `PUERTA COBERTURA` |
| Mutación | sigue en T34, con la feature completa (`python -m harness.mutacion --feature F-048`) |

Sin verificaciones MANUAL nuevas. Queda fuera: los menores 5 y 7 (bloque C) y T6–T41.
