<!-- progress/impl_F-043_bloque_A.md -->
# F-043 · BLOQUE A (T1-T4) — informe del implementer

Rama `feature/F-043-clasificacion-por-ia1`. Rigor `critico`. Cuatro tareas,
cuatro commits, fase RED en las cuatro. Sin `git push`.

`af550a2` T1 catálogo · `d5e5994` T2 `familia_efectiva` · `31817bf` T3
contrato `ClasificacionAlbaran` · `44707c5` T4 el campo en sv2 y sv3.
Cambios requeridos de la review: `progress/impl_F-043_bloque_A_cr.md`.

## 1 · Qué cambió

**Creados**

- `…-comun/ruesma_comun/contratos/familias.py` — el catálogo (R1-R5) y
  `familia_efectiva` (R18-R21, R27). 7 familias: `generico`, `hormigon`,
  `mortero` y `residuos` con alcance documento+línea, y `combustible`,
  `alquiler_maquinaria` y `otro` de **solo línea** (duda 1 del humano), cada
  una con `definicion`, `no_es`, `senales`, `alcance` y las dos claves de
  prompt. API: `CATALOGO`, `Familia`, `familias_documento/linea()`,
  `obtener()`, `render_catalogo_markdown()`, `prompt_fase2_de()`,
  `prompt_valoracion_de()` y `familia_efectiva()`.
- `…-comun/ruesma_comun/contratos/clasificacion.py` — `ClasificacionAlbaran`
  (R7) con `familia`, `confianza_pct` (acotada 0-100), `motivo`, `mixto`,
  `familias_secundarias`, `origen`; `extra="ignore"`. Constantes
  `ORIGEN_IA1/IA2/AUSENTE` y `MOTIVO_SIN_CLASIFICACION`.
- `…-comun/tests/test_f043_familias.py` (43 tests, T1-T3),
  `…-api/tests/test_f043_schema_sv2_documento.py` (7) y
  `…-persistencia/tests/test_f043_schema_sv3_documento.py` (6).

**Modificados**

- `ruesma_comun/contratos/__init__.py` — reexporta `ClasificacionAlbaran` y
  `ContextoLinea` con `__all__` (antes estaba vacío).
- `…-api/domain/models/albaran_models.py` y
  `…-persistencia/domain/models/extraction_models.py` —
  `DocumentoAlbaran.clasificacion: Optional[ClasificacionAlbaran] = None`: una
  línea cada uno, más el comentario de por qué va en `data` y no en `meta`.

## 2 · Decisiones de diseño (y por qué)

1. **El enrutado se deriva del catálogo en cada llamada**, no de un índice
   precalculado al importar: así, añadir una familia es de verdad *una
   entrada* (R3), y el test que da de alta `bombeo` en caliente prueba algo.
2. **`obtener` normaliza (`strip().lower()`)**: la IA puede devolver
   `' Hormigon '` y eso no es otra familia. Evita que cada servicio invente su
   propia limpieza, y dos la inventen distinta. **No** es adivinar: no hay
   *fuzzy match* ni sinónimos; lo que no esté devuelve `None` (R10, T8).
3. **`familia_efectiva` acepta objeto o `dict`** (`_campo`): sv5 y sv6 la
   manejan validada, pero el envelope viaja como diccionario antes de
   validarse. Es lo que permite que el criterio viva en UN punto (R20).
4. **`render_catalogo_markdown` revienta con un alcance desconocido**
   (`ValueError`): devolver cadena vacía inyectaría un prompt sin catálogo en
   silencio, que es exactamente el fallo que no se ve.
5. **Los textos van sin tildes**: atraviesan prompt, log y tests.
6. **`origen` es `str`, no `Literal`** (lo pide el diseño §1.2): un `Literal`
   obligaría a tocar el contrato compartido en cada origen nuevo.
7. **`familias_secundarias` con `default_factory`**, con test de que dos
   instancias no comparten lista: una lista de clase haría que marcar un
   albarán mixto contaminase a los demás del mismo proceso.

**Lo que NO se hizo, a propósito**: ni una regla que infiera la familia por
código LER, familia de producto, palabras del texto o CIF. El módulo importa
exactamente dos cosas (`annotations` y `dataclass`), y
`test_f043_r13_familia_efectiva_no_mira_el_ler_ni_el_texto` lo comprueba con
lista NEGRA (cifra y test, ya con los CR aplicados).

## 3 · Fase RED → GREEN, tarea a tarea

### T1 · catálogo

```
$ pytest services/albaranes-comun/tests/test_f043_familias.py -k "catalogo or render or prompt"
services\albaranes-comun\tests\test_f043_familias.py:17: in <module>
    from ruesma_comun.contratos import familias as cat
E   ImportError: cannot import name 'familias' from 'ruesma_comun.contratos'
ERROR services\albaranes-comun\tests\test_f043_familias.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.34s
```

Tras escribir `familias.py`, la primera pasada dejó **1 fallo real y útil**:

```
E   AssertionError: assert 'otro' not in '- `generico...del residuo.'
E     'otro' is contained here:
E       n punto a otro, sin hacerse cargo del residuo (sin codigo LER, ...
```

El test buscaba la palabra suelta `otro`, corriente en castellano y presente
en las definiciones. **Se corrigió el test, no el código**: ahora busca el id
entrecomillado (`` `otro` ``), como lo lista el render. Verde: `21 passed`.

### T2 · `familia_efectiva`

```
$ pytest services/albaranes-comun/tests/test_f043_familias.py -k efectiva
E   AttributeError: module 'ruesma_comun.contratos.familias' has no attribute 'familia_efectiva'
FAILED ...::test_f043_r18_familia_efectiva_rama1_la_de_la_linea_manda
FAILED ...::test_f043_r18_familia_efectiva_rama1_la_linea_otro_no_hereda
FAILED ...::test_f043_r27_familia_efectiva_rama2_sin_clasificacion_es_none
FAILED ...::test_f043_r19_familia_efectiva_rama3_en_mixto_no_se_hereda
FAILED ...::test_f043_r18_familia_efectiva_rama4_hereda_la_del_documento
  (12 failed, 21 deselected in 0.17s — listado completo en el commit d5e5994)
```

Verde: `12 passed, 21 deselected in 0.06s`. Un test por rama del diseño §1.1,
más el de que en mixto la línea con familia propia sigue valiendo (el mixto
bloquea la HERENCIA, no lo que la IA dijo de esa línea) y el de que no se
escribe nada en `contexto_linea` (R21).

### T3 · contrato

```
$ pytest services/albaranes-comun/tests/test_f043_familias.py -k contrato
E   ModuleNotFoundError: No module named 'ruesma_comun.contratos.clasificacion'
ERROR services\albaranes-comun\tests\test_f043_familias.py
1 error in 0.60s
```

Verde después: `10 passed, 32 deselected in 0.41s`.

### T4 · el campo en los dos schemas (suites por separado, ver §4)

```
$ (sv2) pytest tests -k f043_schema
      Extra inputs are not permitted [type=extra_forbidden,
      input_value={'familia': 'generico', '...milias_secundarias': []}]
E   AssertionError: assert 'clasificacion' in {'cabecera': {...}, 'lineas': {...}}
5 failed, 2 passed, 58 deselected in 0.71s

$ (sv3) pytest tests -k f043_schema
    data.clasificacion
      Extra inputs are not permitted [type=extra_forbidden,
      input_value={'familia': 'residuos', '...ores.', 'origen': 'ia1'}]
4 failed, 2 passed, 125 deselected in 2.33s
```

Los 2 que ya pasaban en cada uno **tenían que pasar antes y después**, y lo
hicieron. Corregido tras la review: en **sv3** sí son los dos de no-regresión,
pero en **sv2** el segundo es `..._rechaza_una_clasificacion_mal_formada`, que
en RED pasaba por el `extra_forbidden` del bloque entero y no por el `le=100`
que comprueba de verdad. Verde: sv2 `7 passed`; sv3 `6 passed`.

## 4 · Desviación respecto a `tasks.md` (una, y no es opcional)

**La verificación de T4 no puede ejecutarse como está escrita.** `pytest
services/albaranes-api/tests services/albaranes-persistencia/tests -k
f043_schema` muere al RECOGER, en un test ajeno a F-043:

```
services\albaranes-api\tests\test_f002_obras_cache.py:17: in <module>
    from infrastructure.sigrid import sigrid_api_obras_client as modulo_cliente
E   ImportError: cannot import name 'sigrid_api_obras_client' from
    'infrastructure.sigrid' (C:\...\albaranes-persistencia\infrastructure\sigrid\__init__.py)
```

Causa: sv2 y sv3 tienen **ambos** un paquete real `infrastructure/sigrid`, y
en un único proceso de pytest el `sys.path` de uno tapa al del otro. Es
**previo a F-043** (se reprodujo ignorando los dos ficheros nuevos). No se
tocó nada para sortearlo, sería un workaround en código ajeno: las dos suites
se lanzan **por separado**, como en `init.sh`. Igual en T13-T17.

## 5 · Fuera de alcance y verificaciones MANUAL

- `tipologia_resolver`, prompts, workers, DDL, sv4, sv5 y sv6: intactos. El
  catálogo existe pero **todavía no lo llama nadie**; el campo `clasificacion`
  existe pero **nadie lo rellena**. Eso es T5-T24. T25-T29 también pendientes.
- **Aviso para el bloque D**: sv5 conserva su propio `DocumentoAlbaran`
  (`albaran-valoracion-api/domain/models/albaran_models.py`) con
  `extra='forbid'` y **sin** el campo. Hoy no valida documentos de sv2, pero
  si lo hiciera tras el bloque B los rechazaría. Decidirlo en T18-T20.
- **MANUAL de este bloque: ninguna.** T1-T4 son código puro, sin red, sin
  BBDD y sin LLM. Las de la feature son T30 (evals), T31 y T32.

## 6 · Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests nuevos de F-043 | **56** (43 comun, 7 sv2, 6 sv3), todos en verde |
| Suites ejecutadas | raíz **556 passed** (131,90 s) · comun **117 passed, 3 skipped** (123,38 s) · sv2 **65 passed** (2,22 s) · sv3 **131 passed** (3,50 s) |
| Cobertura de líneas cambiadas | **98,7 %** (367/372, umbral 80 %, nivel `critico`) — **medida sobre el diff contra `dev`, que arrastra F-036**, no solo sobre el bloque A |
| Mutantes generados / evaluados / supervivientes | **12 / 12 / 0** (campaña completa, sin muestreo; 239,4 s, línea base 109,4 s, 1 worker) |

Informe: `progress/mutacion_F-043_bloque_A.md`, inventariado `VÁLIDA` en
`progress/inventario_mutacion_F-039.md`.

**Alcance de la campaña.** Se lanzó con `--ficheros` sobre los dos módulos
nuevos, no con `--feature F-043` a secas: esta rama sale de la de F-036 y no
de `dev`, así que `git diff dev...HEAD` son **32 ficheros**, toda F-036
incluida. Con ese alcance ni terminó en 10 minutos y dejó un mutante escrito
en el árbol principal (recuperado con `--restaurar`). La entera es **T28**.

Los 12 mutantes cayeron sobre lo que decide: los límites `ge=0` / `le=100` de
la confianza, el `default=False` de `mixto`, el `@dataclass(frozen=True)`, los
dos `not` de la normalización, la comparación de `obtener`, los ternarios de
los `prompt_*_de` y las tres guardas de `familia_efectiva`. **Ninguno
sobrevivió.**

Las 5 líneas cambiadas sin cubrir (367/372) **no son de este bloque**: la
puerta mide el diff completo contra `dev`, que arrastra F-036.

## 7 · `bash harness/init.sh` — resultado real

Primera pasada: **KO**. El guardián de F-039 R2 exige que **todo** informe de
mutación figure en el inventario:

```
E   AssertionError: estos informes de mutación no figuran en
    progress/inventario_mutacion_F-039.md: ['progress/mutacion_F-043_bloque_A.md'].
1 failed, 387 passed in 100.42s   (387 = los que cupieron antes del corte de -x)
```

Se añadió la fila con su veredicto. Segunda pasada, **verde**: `ENTORNO LISTO.
Puedes trabajar.` — **556 passed** en la raíz, las seis suites de servicio en
verde, puerta de cobertura y puerta de tamaño en verde.

Sigue el **aviso** —no bloqueante— de rutas sensibles: al declararse el campo,
`albaranes-api/domain/models/albaran_models.py` entra en la lista de rutas
sensibles tocadas (schemas Pydantic de extracción). Esa evidencia es **T30**,
la pasada de evals con LLM real que autoriza el humano.
