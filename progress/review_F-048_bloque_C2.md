Revisión incremental desde d4b51fb (C1 pasada 2: CR-C1 y CR-C2 · bloque C2 pasada 1: T17–T22), HEAD `a9fc7eb`

# F-048 · Review de los cambios de C1 y del bloque C2 (sv2, T17–T22)

**Veredicto: APPROVED**, con tres menores y ningún bloqueante. El resolver sigue D5 fila a fila, el
bloqueante 1 de C1 está cerrado y los tres RED que reproduje coinciden. Conviene cerrar el menor 2 antes
de T34. **Rigor** `critico` (declarado): RED, cobertura ≥ 80 %, mutación (T34) y evals (T40).

## Qué se ejecutó (resultados reales)

- `bash harness/init.sh` tal cual: exit 0, **ENTORNO LISTO**. Raíz `865 passed in 117.17s`, servicios
  de caché, `PUERTA COBERTURA 99.3 % (553/557)`. El `[AVISO]` de evals (5 rutas sensibles, ahora
  también `retry_policy.py`) es el esperado: T40.
- A mano, una detrás de otra: **sv2 `338 passed in 2.92s`** · **comun `259 passed, 3 skipped in
  107.69s`** · sv5 `43 passed`. Ruff: 9 avisos, todos deuda previa. `git status` limpio.

## RED reproducidos en copias del scratchpad (coinciden con el informe)

1. **T18 B** (`origen_datos_resolver.py:108`, `obras_conocidas[c]` → `leidos[c]`): `12 failed, 18 passed`,
   con `'945' == '0945'` (x6), `'09-45'`, `'０９４５'` y `'a12' == 'A-12'`.
2. **T18 C** (`:120`, `len(cuentan)` → `len(leidos)`): `2 failed, 28 passed`, `'correo_ambiguo' == 'correo_unico'`.
3. **T21**: la copia de comun lleva el `retry_policy.py` de `d4b51fb` y va delante en `PYTHONPATH`.
   Resultado: `2 failed, 7 passed`, con el centinela en `retry_policy.py:211` y `:236`. Con HEAD: `9 passed`.

## CR-C1 y CR-C2: el bloqueante 1 de C1, cerrado

`prompts.yaml:70-75`: `obra_codigos` son TODOS los códigos, «estén o no en la lista de obras de
arriba. Esa lista es solo para cabecera.obra_codigo». `:81-83`: sin obra en el papel, `null` «como hasta
ahora». Las cinco frases están en el `parametrize` de `test_f048_r16_prompt_yaml.py`.

## El resolver frente a D5 (`origen_datos_resolver.py`)

| Fila | Código | Tests (`test_f048_r19_r22_tabla_d5.py`) |
|---|---|---|
| 1 | `correo_sin_dato` / `ia_sin_lectura_correo` / `correo_fuera_de_lista`: `validada=false`, leídos en candidatos, cabecera intacta (`:95-115`) | `fila1_*` (5) |
| 2 | un código que cuenta y papel igual o nulo ⇒ código de la lista, sin discrepancia (`:120-131`) | `fila2_*` (4; dos con la obra NO activa `0320`) |
| 3 | papel distinto, aunque no sea obra ⇒ manda el correo, `discrepancia=true` (`:129`) | `fila3_*` (3) |
| 4 | varios, y el del papel entre ellos ⇒ `correo_confirma_papel`, cabecera intacta (`:133`) | `fila4_*` + uno de normalización |
| 5 | varios sin casar, o papel nulo ⇒ `correo_ambiguo`, cabecera intacta (`:133`) | `fila5_*` (3) |

- **D9**: todo pasa por `normalizar_codigo`, sin repetidos ni vacíos (`:70-83`). **Se filtra ANTES
  de contar** (`:104-108`, RED C). Las colisiones se quedan fuera del mapa y su código no cuenta
  (fila 1, `test_f048_r18_normalizacion.py:221-250`).
- **Sin lista** (`None`): cuentan todos, con `validada=None` y la forma de IA1. **Con lista, la
  cabecera se escribe como figura en ella** (`:108`, RED B).
- **Puro**: sin I/O ni log. Del `ContextoCorreo` solo toma `sha256` y `truncado` (`:164-165`), nunca
  el texto. Copia el envelope, y hay test de que no lo muta. **Aviso A**: el worker pasa la lectura de
  `env1` (FASE 1) y sella el envelope FINAL (`extraction_worker.py:184-189`). La lectura de IA2 se
  ignora y sale del `data` (`test_f048_r25_*`, en resolver y worker).

## Las diez decisiones del implementer: todas correctas

- **3 · `fuente` y candidatos.** Poner `fuente=correo` solo en `correo_unico` es lo único veraz: es la
  única fila donde el correo impone la obra. En la 4 y la 5 la obra final es la del papel (R20: «deja
  la obra del papel»). En candidatos van los que cuentan (R20) y, en la fila 1, lo leído (R21, rastro de §7).
- **5 · `obras_conocidas()` solo con correo.** Sin correo, el resolver sale en `:95` sin mirar la
  lista, así que pedirla solo costaría el timeout con sigrid-api caído. Con correo se pide UNA vez
  (`obras.llamadas == 1`) y sin correo, 0. El servicio atrapa el fallo y devuelve `None`.
- **6 · La red se propaga.** Comprobé la frontera. `BlobNoEncontradoError` hereda de `FileNotFoundError`
  (`blobs/almacen.py:34`), así que un blob ausente da `None`, igual que un JSON ilegible (`ValueError`)
  o uno que no valida; nada de eso va a poison. Un corte justo después de leer el PDF del MISMO almacén
  es transitorio: reintentar es lo correcto.
- 1, 2, 4, 7, 9 y 10: sin objeción. **8**: redactar ANTES de recortar es necesario (RED 3); el riesgo
  que queda (un SDK que citara el cuerpo SIN la marca) está declarado en el informe.

## Worker, R36 y compatibilidad

- Con el blob ausente o roto, se sigue sin correo y se publica. Sin `correo_blob`, no se pide ni el
  blob ni la lista (`getattr` defensivo). Sin correo, el `data` es el de hoy salvo `origen_datos`
  (R22, también con una lectura que la IA se inventa).
- **R36**: el handler completo, con el YAML real y a DEBUG, no deja el centinela en el log (asunto y
  cuerpo). El blob roto no repite su contenido y `retry_policy` redacta en sus tres logs.
- **sv3 ACTUAL**: lo comprobé con su venv. `DocumentoAlbaran` con `origen_datos` da `ValidationError
  [extra_forbidden]`, igual que con `lectura_correo`: el handler lanza y el mensaje acaba en poison.
  **Lo cubren T23 y el orden sv3 → sv2 → sv1 de §8.** `lectura_correo` nunca llega al `data` final, y
  sv3 lee `envelopes/{id}_phase_1.json`, que el worker pisa con el final (`:191`).

## Bloqueantes: ninguno. Menores (no bloquean):

1. **Hay otros sitios con la `evidencia` sin recortar** (aparte del `phase_1_json` que ya se decidió).
   (a) El blob `envelopes/{id}_phase_2.json` (`extraction_worker.py:150`) guarda `debug.phase_1_json`
   y `documento_revisado.lectura_correo` de IA2. `_phase_1.json` también la lleva mientras corre el
   handler (`:114`). La lifecycle los purga a los 14 días (`infra/blob_lifecycle.ps1:28`), la misma que
   al `input/…correo.json`, que ya guarda el cuerpo entero (D1): por eso es menor. (b) Con
   `LLM_CALL_LOG_DIR` (auditoría opt-in), el fichero guarda la respuesta de IA1 y el `{json_fase_1}`
   de IA2, fuera del bloque que redacta `redactar_correo`. **Propuesta para CR-C3**: recortar a 160 en
   el ORIGEN con un `field_validator(mode="before")` en `domain/models/lectura_correo.py:28` (sin
   `max_length`, por la decisión 1 de C1). Así quedan cubiertos `env1`, `phase_1_json`, blobs y BBDD.
   Lo de (b) hay que dejarlo escrito.
2. **`_mensaje_para_log` (`ruesma_comun/llm/retry_policy.py:19-28`, usada en `:229`, `:240` y `:257`)
   no tiene test en la suite de comun**: solo lo prueba sv2 (`test_f048_r36_logs.py:229-254`). T34 muta
   los ficheros de comun contra la suite de comun (`harness/mutacion.py:854-860`), así que quitar la
   redacción sobrevivirá seguro. **Cambio**: `services/albaranes-comun/tests/test_f048_r36_retry_policy.py`,
   con el mismo error que cita el bloque y el centinela, en los tres caminos.
3. **Un `obra_codigos` malformado tumba la fase 1 entera.** `LecturaCorreo` es `list[str]` estricto, y
   `[945]` da `ValidationError string_type` (comprobado). R17 cubre la ausencia del bloque, no un bloque
   mal formado, y un código de obra se presta a salir como número. Pesa lo mismo que hoy
   `cabecera.obra_codigo` y el schema estructurado lo mitiga, pero un bloque auxiliar no debería poder
   tumbar el documento. **Propuesta**, en el mismo validador del menor 1: número → `str`, y lo que no sea
   lista, fuera. Vigilarlo en T40.

## Avisos para el líder (no son hallazgos de C2)
- A. **sv5** guarda una copia muerta de `DocumentoAlbaran` con `forbid`
  (`albaran-valoracion-api/domain/models/albaran_models.py:57-77`). F-043 le declaró `clasificacion`
  «para no dejar el cepo montado dos veces», pero `origen_datos` no está. Design §6 excluye sv5:
  decidirlo en T32.
- B. En la fila 4, la cabecera se queda como la leyó el papel (`945`), no con la forma de la lista.
  Es lo que dicen D4 bis y D5. Pero si la red de sv3 (R28) busca el código literal, un albarán que el
  correo CONFIRMA acabaría en revisión sin obra. Es igual que hoy para el papel, pero merece una línea en T25.

## Checkpoints (bloque intermedio)

- **C1** [x] init.sh exit 0 · [x] ficheros · **C2** [x] una `in_progress` · [x] rama · [x] `current.md` · N/A `history.md` (nada pasa a `done`).
- **C3** [x] hexagonal: resolver puro en `application`, puerto y adaptador en `interface_adapters/worker`,
  cableado en `main_worker.py` · [x] primera línea con la ruta en los 15 `.py` · [x] sin prints de debug
  (el de `encolar_extraccion.py` es la salida del CLI), sin secretos ni dependencias nuevas · [x] la
  obra la cruza sv2 sobre las listas de IA1, sin reglas sobre el texto.
- **C3 bis** N/A: no se toca `docs/referencia/` · **C4** [x] R11, R17–R25, R36 (sv2) y R42 con `test_f048_rN_*` en verde · [x] sin red ni BBDD · [x]
  sin MANUAL propia: el extremo a extremo es T37.
- **C4 bis** [x] rigor declarado · [x] RED real, 3 reproducidos · [x] cobertura 99.3 % · **N/A mutación
  y RM1–RM6**: la campaña es T34, sobre la feature completa, y medirla ahora dejaría de valer (RM1)
  en cuanto entren T23–T28 · [x] «Evidencias» con los cuatro números.
- **C4 ter** [x] exigencia `aviso`, con motivo: la evidencia de las 5 rutas sensibles es T40 (se factura,
  necesita el visto bueno del humano). **Bloqueará la review final** si falta.
- **C5** [x] T17–T22 `[x]` con commits `F-048 Tn:`, más CR-C1 y CR-C2 · [x] árbol limpio · [x] `in_progress`.

## Trazabilidad (`services/albaranes-api/tests/`)
| R | Tests |
|---|---|
| R11 | `test_f048_r11_worker.py` (22) |
| R17, R19–R22, R24 | `test_f048_r19_r22_tabla_d5.py` (23) |
| R18 (cruce, D9, colisiones) | `test_f048_r18_normalizacion.py` (30), `r19_r22 ::r18_*` (3) |
| R23, R25 | `test_f048_r23_r25_sellado.py` (14), `r11_worker ::r25_*` |
| R36 (sv2 y `retry_policy`) | `test_f048_r36_logs.py` (9) |
| R42 | `test_f048_r42_encolar.py` (9) |
| R15/R16 (CR-C1/C2) | `test_f048_r16_prompt_yaml.py::test_f048_r16_*` |

**Automejora** (propuesta, no aplicada; vale para `arnes-base`): en C4 de `CHECKPOINTS.md`, «un cambio
en una librería compartida del monorepo lleva su test en la suite de ESA librería». La mutación y la caché
de `init.sh` van por servicio, y un test de otra suite no mata nada (menor 2).
