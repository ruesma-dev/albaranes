<!-- progress/impl_F-043_bloque_D.md -->
# F-043 · BLOQUE D (T18-T23) — informe del implementer

Rama `feature/F-043-clasificacion-por-ia1`. Rigor `critico`. Seis tareas, seis
commits + uno de refuerzo. Sin `git push`. **Solo sv5 y sv6.**

`af0846c` T18 · `ed53181` T19 · `b7c9238` T20 · `6196694` T21 · `a3cfde4` T22
· `6f2599a` T23 · `a069640` refuerzo (§6.1).

> **R26 CONSEGUIDO.** SS-0003967 vale **210,00 € en 2 líneas** con la línea
> **sin `tipo_familia`**, por la clasificación del DOCUMENTO. Con el builder
> real, mismo albarán, mismo contrato y mismo match, cambiando SOLO
> `context.clasificacion`: **720,00 € / 1 línea → 210,00 € / 2 líneas**.
> El número y su letra pequeña, en §3.

## 1 · Qué cambió

**Creado** — cuatro ficheros, todos de test:
`…valoracion-api/tests/test_f043_contexto_clasificacion.py` (**25** tests,
T18-T20 y §6.1), `…valoracion-persist/tests/test_f043_envelope_dto.py`
(**5**, T21), `test_f043_familia_efectiva.py` (**15**, T22) y
`test_f043_r26_ss0003967.py` (**7**, T23).

**Modificado · sv5** (`services/albaran-valoracion-api/`)

- `infrastructure/database/sqlalchemy_valuation_context_repository.py` —
  `_SQL_MERGE_HEADER` suma las seis columnas; `_build_clasificacion` (inverso
  exacto de `campos_clasificacion_merge` de sv3) y `_lista_json`.
- `domain/ports/valuation_context_repository.py` y
  `domain/models/valuation_context.py` — el campo en `ValuationContextRaw` y en
  `ContextoValoracion`.
- `application/pipelines/value_albaran_pipeline.py` — lo propaga a las dos
  construcciones del contexto y lo escribe en el `context` de los **dos** sobres
  (`ok` y `no_contract`) con `_clasificacion_a_dict`.
- `application/services/valuation_extraction_service.py` — **se borra**
  `_derivar_tipologia_valoracion`; nace `_prompt_key_de`.
- `domain/models/albaran_models.py` — el aviso heredado del bloque A (§4).

**Modificado · sv6** (`services/albaran-valoracion-persist/`)

- `domain/models/valuation_envelope.py` — `ValuationContextDto.clasificacion`.
- `application/services/valuation_builder.py` — el helper `_familia_de`, el
  sellado de `self._clasificacion` en `build()` y **las ocho puertas**.
- `tests/f036_escenarios_residuos.py` — campo `clasificacion` en
  `EscenarioResiduos`, como F-036 bloque D le añadió `codigo_contrato`.

**NO se tocó, a propósito**: sv2, sv3 y sv4 enteros; el catálogo; `ler.py`,
`residuos_container_calc`, `residuos_incrementos` y `modifier_contract_matcher`
(esta tarea abre la puerta, no rehace lo de dentro); y `_serialize_context` de
sv5, que es lo que ve el LLM — meter ahí la clasificación cambia el prompt de
IA3, o sea ruta sensible y T30. **Ningún fallo encontrado en sv2, sv3, sv4 ni
en el catálogo.**

## 2 · Decisiones de diseño (y por qué)

1. **Las OCHO puertas, no seis.** El diseño listaba seis más el padre de la
   sintética; en el fichero son ocho: `_es_movimiento_residuos` (:305), M1 por
   año (:620), sintéticas por código (:704), red del LER (:847), guarda
   anti-incremento (:986), contenedores (:1166), aviso de horas de descarga
   (:1227) y el padre de la sintética (:1397). Se cambiaron las ocho: dejar una
   fuera crea un albarán que hereda familia en unas reglas y no en otras, que es
   peor que no heredar en ninguna.
2. **Se quitó el `ctx is None or …` de las puertas.** Antes, una línea sin
   `contexto_linea` quedaba fuera por definición — y eso taparía justo el caso
   de SS-0003967, cuyo merge real traía `contexto_linea = NULL`. Comprobado que
   lo de detrás aguanta `ctx=None`: `calcular_contenedores_residuos` y las
   reglas de `REGLAS_SINTETICAS_RESIDUOS` leen todo con `getattr(..., None)`;
   sin LER no emiten sintética y sin volumen devuelven `residuos_sin_volumen_m3`
   con la línea a revisión, que es la respuesta correcta y no un fallo.
3. **`self._clasificacion` sellado en `build()`**, igual que
   `_codigo_contrato_actual`, e inicializado a `None` en `__init__`. Descartado
   pasarla por parámetro a `_build_line` y `_build_synthetic_line`, que ya tienen
   siete y nueve argumentos. Quien llame a un privado sin pasar por `build()` ve
   `None`, o sea el comportamiento de hoy.
4. **La herencia NO se escribe** en `contexto_linea` (R21): `_familia_de` es una
   función de lectura, y hay test que lo fija.
5. **`_lista_json` no revienta con un JSON corrupto**: lista vacía y aviso. La
   clasificación entera no se pierde por un campo informativo — el mismo criterio
   defensivo con el que sv3 recorta a `VARCHAR(32)`.
6. **La clasificación también en el sobre `no_contract`**: si faltara solo en esa
   rama, el mismo albarán quedaría clasificado o no según si tenía contrato.

### 2.1 · Un cambio de comportamiento REAL, querido, y que hay que saber

Borrar `_derivar_tipologia_valoracion` (R24) tiene una consecuencia que R27 no
cubre: **un documento anterior a F-043 con líneas de residuos ya no se valora
con `valuation_residuos`, sino con el genérico**. Antes sv5 agregaba las
`contexto_linea.tipo_familia` para deducir la tipología del albarán; ahora, sin
clasificación de DOCUMENTO no hay familia, y adivinarla por las líneas es el lazo
cerrado que la feature desmonta. Está en el diseño («se retira
`_derivar_tipologia_valoracion`… con caída a `self._prompt_key`») y fijado en
`test_f043_r24_el_prompt_ya_no_se_deriva_de_la_familia_de_las_lineas`.

**Consecuencia directa para T31**: revalorar SS-0003967 desde sv4 **no basta**.
Esa vía publica `q-valoracion` y no re-extrae, así que el merge sigue con las
seis columnas a NULL: sin clasificación, ni prompt de residuos ni puertas
abiertas. Hay que volver a pasarlo por sv2 (`q-extraccion`) para que IA1 lo
clasifique. Es coherente con la decisión 5 del humano (sin backfill), pero la
frase «revalorarlo a mano desde sv4» de esa decisión **no alcanza** aquí, y
conviene decidirlo antes de T31.

## 3 · T23 · el número exacto, medido

Builder real con sus cinco colaboradores, contrato CTSU24/0228 (obra 687), LER
170604, 6 m³, línea **sin `tipo_familia` ni `rol_linea`**:

```
SIN clasificacion, match=CONTENEDOR: total=720.0 lineas=1
    from_albaran   cant_alb=6.0 cant_conv=None precio=120.0 importe=720.0
SIN clasificacion, match=INCREMENTO: total=540.0 lineas=1
    from_albaran   cant_alb=6.0 cant_conv=None precio=90.0  importe=540.0
CON clasificacion, match=CONTENEDOR: total=210.0 lineas=2
    from_albaran   cant_alb=6.0 cant_conv=1.0  precio=120.0 importe=120.0
    synthetic      'INCREMENTO LER 170604' cant_conv=1.0 precio=90.0 importe=90.0
CON clasificacion, match=INCREMENTO: total=90.0  lineas=2
    from_albaran   cant_alb=6.0 cant_conv=1.0  precio=None  importe=None
    synthetic      'INCREMENTO LER 170604' cant_conv=1.0 precio=90.0 importe=90.0
```

**210,00 € en 2 líneas**, sin que nadie escriba `tipo_familia` en la línea.

**La letra pequeña, y no se disimula.** R26 pide 210,00 € «y no 540,00 € en 1
línea», pero esas dos mitades **no salen del mismo escenario**: los 540,00 € de
BBDD son la base casada con el INCREMENTO (6 × 90) y los 210,00 € exigen que IA3
case con el CONTENEDOR. Con el match REAL de SS-0003967 —la 26481— la guarda de
F-036 R15 anula el casado, y hace bien (esa línea tarifa el recargo, no la
retirada): el albarán sale en **90,00 € y a revisión**. Es lo que F-036 ya
avisaba («bajo hipótesis») y **F-043 no lo arregla**: ese match es el prompt, o
sea T30. Lo que sí cambia es que el albarán pasa de valorarse **de más en
silencio** (540) a valorarse de menos **y pedir revisión**. Los cuatro casos
están fijados como test, el último en
`test_f043_r26_con_el_match_real_de_ia3_la_guarda_deja_el_albaran_a_90`.

## 4 · El `DocumentoAlbaran` de sv5 (aviso heredado del bloque A) — RESUELTO

`albaran-valoracion-api/domain/models/albaran_models.py` tiene una copia propia
de los schemas de fase 1 y 2 de sv2, `extra='forbid'` y sin `clasificacion`.
Verificado: ese modelo y `revision_models.py` **no los importa nadie** en sv5, y
su `SchemaRegistry` sólo sirve `documento_valoracion` y `documento_conciliacion`
—el albarán se lee con SQL crudo—. Es código muerto.

**Se le añadió el campo, y se escribió por qué hoy no hace falta.** Cuesta dos
líneas y quita un cepo permanente: con `extra='forbid'`, el día que alguien
registre ese schema un documento con `clasificacion` sería **rechazado entero** y
el fallo aparecería lejos de aquí. Es exactamente cómo murió `meta.tipologia` en
el `ExtractionMeta` de sv3 —el defecto que F-043 existe para arreglar— y no se
deja el mismo cepo montado dos veces. Además R8 lo pide literalmente para el
esquema de fase 1 y el `documento_revisado` de fase 2, y sv5 tiene los dos.

Dos tests lo dejan escrito: uno valida un documento con el bloque, y
`test_f043_r8_sv5_no_valida_hoy_documentos_de_fase_1_ni_de_fase_2` fija que el
registro de schemas sólo sirve los dos de valoración. Si algún día se registran
ahí, ese test cae y obliga a decidir si la copia sigue viva o se reexporta de
sv2. **Borrar la copia entera no entra en T18-T20**: es una poda de cuatro
ficheros muertos de sv5 y merece tarea propia.

## 5 · Fase RED → GREEN, tarea a tarea

### T18 · el SELECT (R23)

```
$ (sv5) python -m pytest tests/test_f043_contexto_clasificacion.py -k select -q
E   sqlalchemy.exc.NoSuchColumnError: Could not locate column in row for column 'tipologia'
E   AttributeError: 'ValuationContextRaw' object has no attribute 'clasificacion'   (×4)
5 failed, 13 deselected in 8.55s
```
Verde: `5 passed`.

### T19 · el prompt (R24, R15, R27)

```
$ (sv5) python -m pytest tests/test_f043_contexto_clasificacion.py -k prompt -q
E   AssertionError: assert ['valuation_es'] == ['valuation_residuos']
E   AssertionError: assert ['valuation_residuos'] == ['valuation_es']
2 failed, 4 passed, 12 deselected in 1.68s
```
Los dos fallos son simétricos, y esa simetría es la tarea: el prompt de residuos
salía de las LÍNEAS y no de la clasificación, y no salía de la clasificación
cuando sí la había. Los 4 que pasaban tenían que pasar antes y después (familias
sin prompt propio, y sin clasificación). Verde: `15 passed`.

### T20 · el sobre (R23) y el `DocumentoAlbaran` (R8)

```
$ (sv5) python -m pytest tests -k "envelope or r8" -q
E   KeyError: 'clasificacion'                                            (×3)
E   ValidationError: 1 validation error for DocumentoAlbaran
      clasificacion
        Extra inputs are not permitted [type=extra_forbidden, ...]
4 failed, 1 passed, 31 deselected in 5.04s
```
El `extra_forbidden` es el mismo que mató a `meta.tipologia` (§4). Verde: la
suite entera de sv5.

### T21 · el DTO del sobre (R23, R27)

```
$ (sv6) python -m pytest tests -k f043_envelope -q
E   AttributeError: 'ValuationContextDto' object has no attribute 'clasificacion'  (×3)
E   Failed: DID NOT RAISE ValidationError
5 failed, 185 deselected in 0.93s
```
Verde: `5 passed`.

### T22 · las ocho puertas (R20, R25)

```
$ (sv6) python -m pytest tests/test_f043_familia_efectiva.py -q
E   assert None == 1.0            (contenedores no se calculan)
E   assert 0 == 1                 (no se emite la sintetica del LER)
E   AssertionError: 'residuos_base_casada_con_incremento' in [...]
E   AssertionError: 'movimiento_residuos_sin_cantidad_asumido_1' in [...]
E   IndexError: list index out of range        (no hay sintetica que heredar)
E   assert set() (hormigon sin sinteticas) / 'horas_descarga_incompletas' in [...]
E   AssertionError: [] (el builder aun compara tipo_familia a pelo)   (R20 ×2)
9 failed, 6 passed in 1.40s
```
Los **6 que pasaban** son los límites que tenían que pasar antes y después: mixto
no hereda (R19), línea `otro` no hereda, `generico` no abre nada, sin
clasificación se valora como hoy (R27 ×2) y la herencia no se escribe (R21).
Verde: `15 passed`.

### T23 · la aceptación (R26)

RED **provocada de verdad**: se restauró `valuation_builder.py` a `HEAD~1` (el
estado anterior a T22, con el DTO de T21 ya declarado), se lanzó el test nuevo y
después se restauró el fichero.

```
$ (sv6) git show HEAD~1:…/valuation_builder.py > …/valuation_builder.py
$ (sv6) python -m pytest tests/test_f043_r26_ss0003967.py -q
E   assert 720.0 == 210.0 ± 2.1e-04        (el numero de R26)
E   assert 0 == 1                          (ni base a 1 contenedor ni sintetica)
E   AssertionError: 'residuos_base_casada_con_incremento' in [...]
6 failed, 1 passed in 0.79s
```
El único que pasaba es el que fija los **540,00 € de BBDD**, el estado anterior,
que tenía que seguir saliendo igual. Verde: `7 passed`.

## 6 · Mutación y refuerzo

`harness.mutacion.generar_mutantes` sobre las líneas cambiadas de los ocho
ficheros de producción (generación, **sin campaña**: mutar el árbol es T28, del
humano): **17 mutantes** — 9 en `valuation_builder`, 6 en el repositorio de sv5,
1 en el servicio de extracción y 1 en el pipeline. Cero en los cuatro ficheros de
modelos, que son declaraciones.

Se **inyectaron uno a uno**, con la suite entera del servicio en cada uno y el
fichero restaurado después: **17 MUERTOS, 0 supervivientes** (de 1 a 40 tests
caídos por mutante). Árbol restaurado y verificado con `git status`.

### 6.1 · El commit de refuerzo (`a069640`)

Midiendo la cobertura fichero a fichero aparecieron **seis líneas cambiadas sin
cubrir**, todas en las ramas defensivas de `_lista_json`: el `None`, la lista ya
deserializada, el JSON corrupto y el JSON que no es lista. Son las que nadie
ejecuta hasta el día que hacen falta —y sv3 **no normaliza** esa columna contra
el catálogo, así que puede llegar cualquier cosa—. Siete casos parametrizados, y
**ninguna línea cambiada de los ocho ficheros de producción del bloque queda sin
cubrir**.

## 7 · Fuera de alcance, avisos y MANUAL

- **T24-T27, T29 y T33 no se tocaron** (bloque E): sv4 sigue sin pintar la
  clasificación, `harness/rutas_sensibles.json` sin las dos rutas del catálogo y
  `docs/ARCHITECTURE.md` sin la regla nueva.
- **Las seis verificaciones de `tasks.md` pasan tal cual**, lanzadas desde el
  directorio de cada servicio como hace `init.sh`. Para que `-k prompt` cogiera
  los cinco tests de T19 se renombraron dos; los tres ficheros de sv6 llevan el
  nombre que pide su verificación.
- **`PUERTA RUTAS SENSIBLES` pasa de 8 a 11 rutas en aviso.** Este bloque SÍ tocó
  tres: `valuation_context.py` y `albaran_models.py` de sv5 y
  `valuation_envelope.py` de sv6. Las tres son **declaraciones de campo con
  default `None`**, sin lógica; no se tocó ningún prompt ni ninguna red
  determinista de las que ya estaban en la lista. Sigue en aviso, no bloquea, y
  su evidencia es **T30**, que autoriza el humano.
- **`ruff` +11** (1127 → 1138) y **cero en `valuation_builder.py`**, que es donde
  está el cambio de verdad: 7 son `UP045`/`UP006` (`Optional`, `Dict`) en cinco
  ficheros que ya llevan entre 7 y 41 avisos de esa misma regla, y 4 son `I001`
  de los cuatro ficheros de test nuevos —la misma forma de import que ya tienen 8
  de los 11 tests de sv6 y 2 de los 3 de sv5—. Escribirlos con otro estilo los
  dejaría cantando en medio del fichero; cerrarlo es podar el fichero entero.
- **MANUAL de este bloque: ninguna** (sin red, sin BBDD, sin LLM). Las de la
  feature siguen siendo T30, T31 y T32 — con el aviso de §2.1 sobre T31.
- **Lo que este bloque NO demuestra**: que el número salga contra la BBDD real
  (T31) y que IA3 case la base contra el contenedor en SS-0003967 (T30, §3).

## 8 · Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests nuevos de F-043 en el bloque | **52**, todos en verde (25 sv5 · 27 sv6). Ningún test viejo retirado ni relajado |
| Suites (una a una, nada en paralelo) | raíz **556 passed** · sv2 **139** · sv3 **169** · sv4 **131** · sv5 **43** (antes 18) · sv6 **212** (antes 185) · comun **118 passed, 3 skipped**. **Cero fallos, cero skips nuevos** |
| Cobertura de líneas cambiadas | **98,8 %** (558/565, umbral 80 %, nivel `critico`). De los **ocho ficheros de producción de este bloque, ninguna línea cambiada queda sin cubrir** (medido fichero a fichero contra `420618e`); lo que falta está fuera del bloque |
| Mutantes generados en el alcance | **17** (9 `valuation_builder` · 6 repositorio sv5 · 1 servicio de extracción · 1 pipeline; **0** en los cuatro ficheros de modelos) |
| Mutantes ejecutados / supervivientes | **17 inyectados uno a uno, 0 supervivientes.** No es la campaña —esa es T28— sino la inyección manual de cada mutante con la suite completa del servicio cada vez |
| Tiempo de ejecución | sv5 **3,0 s** · sv6 **2,4 s**; el resto, en §9 |
| `ruff` | **+11** sobre 1127; **0 nuevos** en `valuation_builder.py`; desglose en §7 |
| **R26 · SS-0003967** | **210,00 € en 2 líneas** (120,00 contenedor + 90,00 incremento LER 170604), con la línea SIN `tipo_familia`. Antes: 720,00 € en 1 línea con el mismo sobre; 540,00 € en 1 línea con el match real de BBDD |

## 9 · `bash harness/init.sh` — resultado real

**Verde**: `ENTORNO LISTO. Puedes trabajar.` (exit 0) — raíz **556 passed in
243.48s**, los seis servicios con tests en verde, `PUERTA COBERTURA [OK] 98.8%`
(558/565, umbral 80 %, nivel `critico`), `PUERTA TAMAÑO [OK]`, rama correcta y
árbol limpio tras los siete commits.

Avisos, **ninguno bloqueante**: F-036 en `blocked` (a la espera de esta feature);
`ruff` 1138 (§7); sv1-email e `infra` sin tests; marcas `[ADAPTAR]` en las specs
de F-034/F-035; y `PUERTA RUTAS SENSIBLES` con **11** rutas en aviso —tres de
ellas de este bloque, explicadas en §7—, cuya evidencia es T30 y la autoriza el
humano.

---

*Tamaño*: **321** líneas frente al tope de 220. La puerta mide
`progress/impl_F-043.md` (nombre exacto), no los informes por bloque, y sale
`[OK]`; el bloque A quedó en 221, el B en 261 y el C en 245 por lo mismo. Lo que
no se recortó, por norma del rol: las trazas de la fase RED (§5), la sección
«Evidencias» (§8) y el resultado real de `init.sh`. Lo que sí, en dos pasadas: la
prosa de las decisiones y del aviso heredado, que está entera en sus commits.
