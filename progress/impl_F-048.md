<!-- progress/impl_F-048.md -->
# F-048 · Informe del implementer

Rigor `critico`. Rama `feature/F-048-correo-contexto-ia1`. Se añade una sección por bloque.

## Bloque A · comun (T1–T5) — 2026-09-23

### Commits

| Commit | Tarea | Qué |
|---|---|---|
| `c351b18` | T1 | `ruesma_comun/correo/contexto.py` + `correo/__init__.py` (R1) |
| `57516d6` | T2 | `MensajeExtraccion.correo_blob` (R8, R9) |
| `bd5a341` | T3 | `ruesma_comun/correo/prompt.py` (R12, R13) |
| `940031e` | T4 | `LlmCallLogger` redacta el correo (R37) |
| `64eaf13` | T5 | `ruesma_comun/contratos/origen_datos.py` + reexport (R24, R31) |
| `172d514` | ajuste | los 5 avisos de ruff que añadí yo (orden de `__all__`, `encode` redundante), sin cambio de comportamiento |

Ficheros de producción: `correo/{__init__,contexto,prompt}.py` y `contratos/origen_datos.py` (nuevos);
`colas/mensajes.py`, `llm/llm_call_logger.py` y `contratos/__init__.py` (cambiados).
Tests: `services/albaranes-comun/tests/test_f048_{r1_contexto,r8_r9_mensaje,r13_prompt,r37_llm_logger,r24_origen_datos}.py`.
Todos los textos son inventados, con el centinela `CENTINELA-F048`. Sin red ni BBDD: el almacén es un doble en memoria.

### Desviación respecto a la spec (por decisión del humano)

**`normalizar_codigo`**: implementado según la **decisión del humano del 2026-09-23 que el líder me pasó
durante el bloque**, no según la spec (R18–R20 y design §3 dicen «sin mayúsculas ni espacios» y `-> str`).
Regla: mayúsculas, quitar todo lo que no sea alfanumérico (espacios, guiones, puntos, barras, guion bajo)
y los ceros a la izquierda; si no queda nada, `None` («sin código»). `0945`, `945`, `09-45`, `09.45`,
` 0945 ` → `945`; `0945` ≠ `0946`; `000`, `--` → `None`. No quita palabras (`obra 0945` → `OBRA0945`):
extraer el código es trabajo de IA1. **La spec la actualiza el líder.**

### Decisiones de diseño (donde la spec no bajaba al detalle)

1. **Huella (`sha256`) sobre lo conservado = asunto + `\n\n` + cuerpo recortado.** Con solo el cuerpo,
   todos los correos con `uniqueBody` vacío (R3) tendrían la misma huella.
2. **`caracteres_originales`** cuenta el cuerpo **normalizado y antes del recorte**: así `truncado`
   equivale a que se perdió texto. El recorte quita el espacio que quede colgando al final.
3. **Normalizar** = solo espacios: saltos de línea a `\n`, rachas de espacio horizontal (tabuladores y
   espacios no separables incluidos) a uno, bordes de línea recortados, como mucho una línea en blanco
   seguida. El asunto se deja en una sola línea y no se recorta.
4. **`leer_contexto_correo`** → `None` si el blob falta (`FileNotFoundError`, del que hereda
   `BlobNoEncontradoError`) o si no valida (JSON roto, bytes que no son UTF-8, esquema). **Un fallo de red
   se propaga** para que la cola reintente, en lugar de extraer sin correo por un corte transitorio. El
   aviso del log lleva el nombre del blob y el tipo o número de errores; **nunca** `str(exc)`, porque el
   de pydantic cita la entrada.
5. **El bloque del prompt**: primero `ADVERTENCIA_DATO`, fuera de las marcas (se lee antes que el texto
   del tercero y sobrevive a la redacción). Después `<<<INICIO_CORREO>>>`, `(huella sha256=…)`, asunto,
   cuerpo (o «sin cuerpo»), una nota de recorte si `truncado` y `<<<FIN_CORREO>>>`. **Se neutraliza
   cualquier racha `<<<` / `>>>`** dentro de asunto y cuerpo (pasan a `«` / `»`), con lo que un correo no
   puede escribir ninguna marca. Textos sin tildes, como el catálogo de familias.
6. **`redactar_correo`** pone en lugar de cada bloque `[correo omitido: sha256=<huella del contexto>,
   caracteres=<longitud del segmento omitido>]`. La huella sale de la línea `(huella …)` y, si falta, se
   calcula sobre el segmento. Un bloque sin cerrar se redacta hasta el final del texto.
7. **`LlmCallLogger._sin_correo`**: copia recursiva (dict, list, tuple) que aplica la redacción a cada
   `str` de `request_summary`. No muta el dict del llamador. Si algo falla dentro, el `try` que ya
   existía hace que no se escriba nada.
8. **`OrigenDatos` / `OrigenCampo`**: `extra="ignore"`; `fuente` y `motivo` son `Literal` derivados de
   las constantes (un motivo nuevo se añade solo en `MOTIVOS`; uno desconocido no valida). `evidencia`
   junta los espacios, se recorta a 160 y si queda vacía pasa a `None`. `hay_discrepancia` es una
   propiedad y no se serializa. Sin `partida` (D8). El import de `ruesma_comun.correo` no arrastra
   el SDK de Azure: `CONTENEDOR_INPUT` se importa dentro de guardar/leer.

### Fase RED → GREEN (salidas reales)

Comando de cada tarea, desde `services/albaranes-comun`: `python -m pytest tests/<fichero> -q --tb=line`.

**T1** `test_f048_r1_contexto.py`, RED (antes de `correo/`):
```
    from ruesma_comun.correo import (
E   ModuleNotFoundError: No module named 'ruesma_comun.correo'
ERROR tests/test_f048_r1_contexto.py
1 error in 1.10s
```
GREEN: `35 passed in 1.39s`.

**T2** `test_f048_r8_r9_mensaje.py`, RED (antes del campo):
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
Los 2 que ya pasaban son de compatibilidad: el JSON sin correo no cambia, y un modelo sin el campo
acepta un mensaje que lo trae, cosa que hoy ya ocurre. GREEN: `7 passed`.

**T3** `test_f048_r13_prompt.py`, RED:
```
    from ruesma_comun.correo.prompt import (
E   ModuleNotFoundError: No module named 'ruesma_comun.correo.prompt'
ERROR tests/test_f048_r13_prompt.py
1 error in 0.95s
```
La primera ejecución con el código dio `1 failed, 16 passed`. El fallo estaba en el propio test: el
bloque sin cerrar se cortaba desde el principio, advertencia incluida, en vez de desde la marca. Corregí
el test y dio GREEN: `17 passed in 0.56s`.

**T4** `test_f048_r37_llm_logger.py`, RED (logger sin redactar):
```
E   assert 'CENTINELA-F048' not in '{\n  "times...true\n  }\n}'
E   assert 'CENTINELA-F048' not in '{\n  "times...true\n  }\n}'
FAILED ...::test_f048_r37_instructions_y_user_text_sin_el_cuerpo
FAILED ...::test_f048_r37_redacta_a_cualquier_profundidad
2 failed, 3 passed in 4.07s
```
Los 3 que ya pasaban vigilan cosas que el cambio no debe romper: lo que no es correo queda igual, no se
muta el dict del llamador y el logger deshabilitado no escribe. La primera ejecución con el código dio
1 fallo por el mismo error de test que en T3 (un `startswith` que no contaba con la advertencia); lo
corregí. GREEN: `5 passed in 4.39s`.

**T5** `test_f048_r24_origen_datos.py`, RED:
```
    from ruesma_comun.contratos import OrigenCampo, OrigenDatos
E   ImportError: cannot import name 'OrigenCampo' from 'ruesma_comun.contratos'
ERROR tests/test_f048_r24_origen_datos.py
1 error in 1.34s
```
GREEN: `44 passed in 0.60s`, casos nuevos de `normalizar_codigo` incluidos.

Suite F-048 del bloque tras el ajuste de ruff: `108 passed in 4.04s`.

### `bash harness/init.sh` (resultado real, tras T5)

`ENTORNO LISTO`. Raíz: `865 passed in 250.45s`; comun: `251 passed, 3 skipped in 144.32s`.
Del resto de servicios, init.sh sirvió el verde de caché (sus árboles no cambiaron).
**`PUERTA COBERTURA: 100.0% de 167 líneas cambiadas cubiertas (167/167, umbral 80%, nivel critico)`**.
Tamaño en verde. Siguen dos avisos que ya estaban: sv1 sin tests, que se resuelve en T6, e infra.
Ruff marca 0 avisos en los ficheros nuevos de la feature. Los que quedan en `llm_call_logger.py` y
`mensajes.py` (BLE001, S110, RUF100) ya estaban antes.

### Lo que tienen que saber los bloques siguientes

**B · sv1**
- `construir_contexto_correo(asunto, cuerpo, *, max_caracteres=MAX_CARACTERES_DEFECTO, recibido_utc=None)`
  acepta `None`. Con `uniqueBody` vacío hay que pasar `cuerpo=""` (R3) y **nunca** el `body`.
  `max_caracteres <= 0` lanza `ValueError`, así que `CORREO_MAX_CARACTERES` conviene validarlo en settings.
- `guardar_contexto_correo(almacen, document_id, ctx) -> nombre` escribe `input/{id}.correo.json` con
  `put_json(contenedor, nombre, objeto)`, compatible con `AlmacenBlobs`. Su log solo lleva nombre y bytes.
  El valor que devuelve es el que va en `MensajeExtraccion(..., correo_blob=nombre)`.
- `ctx.sha256` sirve para `correo_sha256` en meta (R10) y para el `sha8` de los logs.
  **Nunca loguear `ctx.asunto` ni `ctx.cuerpo`.**

**C · sv2**
- `leer_contexto_correo(almacen, msg.correo_blob)` devuelve `ContextoCorreo | None`. `None` = falta o
  no valida, y el aviso ya queda logueado sin texto. **Los errores de red se propagan**: T20 decide si
  los captura o deja que la cola reintente. Esta es la única zona donde R11 no dice nada.
- `render_bloque_correo(ctx | None)` es exactamente el texto que va en `{contexto_correo}`; con `None`
  devuelve `NOTA_SIN_CORREO`, sin marcas. Para el test de R14 (T15), el bloque contiene
  `ADVERTENCIA_DATO` + `MARCA_INICIO`…`MARCA_FIN`.
- `redactar_correo(texto)` sirve para cualquier log de sv2 que vuelque prompts. `LlmCallLogger` ya lo
  aplica, y sv2 y sv5 lo heredan por su reexport en `infrastructure/llm/llm_call_logger.py`.
- Resolver (T17–T19): `from ruesma_comun.contratos import OrigenDatos, OrigenCampo, normalizar_codigo`,
  más las constantes `FUENTE_*` y `MOTIVO_*` de `ruesma_comun.contratos.origen_datos`.
  **`normalizar_codigo` devuelve `str | None`**, y `None` = sin código: el papel sin código no crea
  discrepancia. Hay que comparar siempre los normalizados. `evidencia` se recorta sola a 160 caracteres.
  Para meterlo en `data`, `model_dump(mode="json")`.

**D / D bis · sv3 y sv4**: `MOTIVO_REVISION_OBRA_CORREO_DISTINTA`, `MOTIVO_REVISION_OBRA_CORREO_AMBIGUA`
y `MOTIVOS_REVISION_ORIGEN` se importan de `ruesma_comun.contratos`, sin copiarlos.

### Evidencias (bloque A)

| Evidencia | Valor real |
|---|---|
| Tests F-048 del bloque | 108 passed (5 ficheros), 4.04 s |
| Suite comun completa | 251 passed, 3 skipped, 144.32 s (init.sh) |
| Suite raíz | 865 passed, 250.45 s (init.sh) |
| Cobertura de las líneas cambiadas | 100.0 % (167/167), `PUERTA COBERTURA` de init.sh |
| Mutación | no lanzada en este bloque: es la T34, con la feature completa (`python -m harness.mutacion --feature F-048`) |

Verificaciones MANUAL de este bloque: ninguna. Las de la feature son T36–T40.
Fuera de este bloque: todo lo de sv1, sv2, sv3, sv4, evals y documentación (T6–T41).
