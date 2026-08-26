<!-- progress/impl_F-043_bloque_B.md -->
# F-043 · BLOQUE B (T5-T12) — informe del implementer

Rama `feature/F-043-clasificacion-por-ia1`. Rigor `critico`. Ocho tareas,
ocho commits + uno de refuerzo. Sin `git push`. **Solo sv2.**

`230fc22` T5 · `3d79f64` T6 · `9ff166f` T7 · `bb9c81c` T8 · `9a8eba1` T9 ·
`fd93483` T10 · `5d7a3e4` T11 · `ee27032` T12 · `3a10fce` refuerzo (§5).

## 1 · Qué cambió

**Creado** — `…-api/application/services/clasificacion_resolver.py` (168
líneas): `resolver_clasificacion(data_fase1, data_fase2=None)`. Elige fuente
(fase 2 sobre fase 1, R16), normaliza contra `familias_documento()`, sella
`origen` y registra los dos huecos: fuera de catálogo (R10) y ausente (R11).

**Modificado** — `albaran_extraction_service.py`: `{catalogo_familias}` se
sustituye por `render_catalogo_markdown("documento")` en el `task` de fase 1
(T5). · `config/prompts.yaml` (**RUTA SENSIBLE**, +128 líneas): bloque
«Clasificación del albarán» en `albaran_factura_es` (T6) y sección de
confirmar/corregir en los **cuatro** `albaran_revision_fase2_*` (T7). ·
`phase_merge.py`: `construir_envelope_final` recibe `clasificacion` y la
escribe **en `data`**, `meta.tipologia` queda de espejo (T11). ·
`extract_albaran_pipeline.py`: la caída al prompt genérico cuando la clave no
está registrada deja `WARNING` (T12, R15). · `extraction_worker.py`: resuelve
con fase 1, enruta con `prompt_fase2_de`, re-resuelve con fase 2 (T12). ·
`domain/models/tipologia.py`: podado de 117 a 33 líneas, solo la
reexportación del LER.

**Borrado (T10)** — `tipologia_resolver.py` (187 líneas), el enum
`Tipologia`, `texto_contiene_hormigon`, `texto_contiene_mortero` y el
override por CIF.

## 2 · Decisiones de diseño (y por qué)

1. **Si el YAML no trae el marcador, el catálogo se añade al final**, como
   `{obras_activas}`: un prompt de clasificación sin catálogo no falla,
   clasifica mal. Test de las dos ramas y de que el YAML real lo trae.
2. **Fuera de catálogo ⇒ `confianza_pct = 0`.** R10 pide «marcar a revisión»
   y el mecanismo existente es el umbral de sv3 (60 %); la confianza era
   sobre SU etiqueta, no sobre `generico`, y con el 97 % original nadie
   miraría nunca ese documento.
3. **El resolver acepta el envoltorio de fase 2** además del documento:
   pasar el nivel equivocado degradaría en silencio a la de fase 1.
4. **La confianza se acota (0-100) en vez de reventar**: un valor imposible
   tumbaría el bloque y con él la familia, que es el dato que importa.
5. **`_doc_final` copia `documento_revisado` antes de escribir**: fase 1 y 2
   ya están persistidas y son auditoría forense (regla 1). Con test.
6. **`prompt_fase2_de` en vez del f-string**, y no es cosmético: el f-string
   generaba `albaran_revision_fase2_generico`, clave inexistente que el
   pipeline descartaba sin decir nada. El catálogo devuelve `None` = «usa el
   genérico configurado», y queda en el log.
7. **T10 tocó a los dos consumidores del módulo borrado** lo mínimo para
   dejar el árbol verde; enrutado y re-resolución llegan en T12, como manda
   `tasks.md`.

**Lo que NO se hizo, a propósito**: ni una regla que infiera la familia por
LER, familia de producto, texto o CIF. Dos tests lo vigilan: lista NEGRA de
imports, y que el resolver da el mismo resultado con la cabecera y las líneas
llenas de pistas que sin ellas.

## 3 · Fase RED → GREEN, tarea a tarea

### T5 · el catálogo en el prompt de fase 1

```
$ (sv2) python -m pytest tests/test_f043_prompt_fase1.py -q
E   AssertionError: assert '`residuos`' in 'SYSTEM\n\nREGLAS SIN MARCADOR\n\nHINT'
FAILED ...::test_f043_r6_el_catalogo_se_inyecta_en_el_marcador
FAILED ...::test_f043_r6_entran_las_cuatro_familias_de_documento_enteras
FAILED ...::test_f043_r6_sin_marcador_el_catalogo_se_anade_igual
3 failed, 1 passed in 1.37s
```
El que pasa lo hacía por la razón mala (no entraba nada). Verde: `4 passed`.

### T6 · bloque «Clasificación del albarán»

```
$ (sv2) python -m pytest tests/test_f043_prompt_fase1.py -k bloque -q
E   AssertionError: assert 'Clasificación del albarán' in 'Eres un administrativo
    de obra en España que registra albaranes y facturas...'
FAILED ...::test_f043_r6_el_prompt_real_de_fase1_trae_el_marcador_del_bloque
FAILED ...::test_f043_r7_el_bloque_de_clasificacion_exige_los_cinco_campos
   (+4: motivo citando el documento, generico legitimo, instructions reales
    y schema_hint; el listado entero, en el commit 3d79f64)
6 failed, 1 passed in 1.47s
```
El que pasa es no-regresión de R2. Verde: `11 passed`. Los cinco campos se
leen de `ClasificacionAlbaran.model_fields`, no de una lista a mano.

### T7 · los cuatro prompts de fase 2

```
$ (sv2) python -m pytest tests/test_f043_prompt_fase1.py -k fase2 -q
E   ValueError: substring not found   ("## clasificación del albarán")
FAILED ...::test_f043_r16_los_prompts_de_fase2_piden_confirmar_o_corregir
FAILED ...::test_f043_r16_los_prompts_de_fase2_exigen_explicar_el_cambio
2 failed, 2 passed in 1.29s
```
Los 2 que pasan son no-regresión. Verde: `4 passed`.

### T8 · el resolver

```
$ (sv2) python -m pytest tests/test_f043_clasificacion_resolver.py -q
E   ModuleNotFoundError: No module named
    'application.services.clasificacion_resolver'
ERROR tests/test_f043_clasificacion_resolver.py
1 error in 1.20s
```
Verde: `27 passed`, y `29` con los dos de lista negra.

### T9 · la prohibición (no-regresión: RED provocada)

El código correcto ya estaba: se **reintrodujo a mano** la regla LER →
residuos dentro del resolver.

```
$ (sv2) python -m pytest tests/test_f043_clasificacion_resolver.py -k prohibicion -q
E       AssertionError: assert 'residuos' == 'generico'
E         - generico
E         + residuos
FAILED ...::test_f043_r13_prohibicion_ler_en_todas_las_lineas_no_fuerza_residuos
FAILED ...::test_f043_r13_prohibicion_la_familia_dominante_de_lineas_no_manda
FAILED ...::test_f043_r13_prohibicion_el_cif_del_proveedor_no_fuerza_nada
3 failed, 3 passed, 29 deselected in 0.97s
```
Los 3 que aguantaron son los que la regla inyectada no tocaba. Regla
retirada y árbol restaurado byte a byte. Verde: `6 passed`.

### T10 · el borrado

```
$ (sv2) python -m pytest tests/test_f043_clasificacion_resolver.py -k "ya_no_existe or existen_ya or no_queda_rastro" -q
E   AssertionError: el lazo cerrado sigue vivo: ['clasificacion_resolver.py:
    tipologia_resolver', 'tipologia_resolver.py: tipologia_resolver',
    'tipologia_resolver.py: override_por_cif', 'tipologia.py: tipologia_resolver',
    'extraction_worker.py: tipologia_resolver']
FAILED ...::test_f043_r12_el_resolver_de_tipologia_ya_no_existe
FAILED ...::test_f043_r12_ni_el_enum_ni_las_funciones_de_texto_existen_ya
FAILED ...::test_f043_r14_no_queda_rastro_en_el_codigo_de_sv2
3 failed, 35 deselected in 1.27s
```
Verde: `3 passed`, y la verificación literal de `tasks.md`:
```
$ grep -rn "tipologia_resolver\|override_por_cif" services/albaranes-api --include=*.py
$ (sin resultados)
```

### T11 · la clasificación en `data`

```
$ (sv2) python -m pytest tests -k phase_merge -q
E   TypeError: construir_envelope_final() got an unexpected keyword argument
    'clasificacion'
6 failed, 1 passed, 117 deselected in 1.48s
```
El que pasa es el de R27 (sin clasificación, el envelope de antes): tenía
que pasar antes y después. Verde: `7 passed`.

### T12 · el worker

```
$ (sv2) python -m pytest tests -k worker -q
E   AssertionError: assert 'albaran_revision_fase2_generico' is None
FAILED ...::test_f043_r15_el_worker_enruta_la_fase2_por_el_catalogo[generico-None]
FAILED ...::test_f043_r15_una_familia_sin_prompt_propio_cae_al_generico
   (+3: familia inventada, re-resolucion con fase 2 y hueco sin clasificar;
    listado entero en el commit ee27032)
5 failed, 7 passed, 124 deselected in 2.89s
...
FAILED ...::test_f043_r15_el_pipeline_cae_al_generico_y_lo_deja_en_el_log
1 failed, 13 passed, 124 deselected in 3.18s
```
Los 3 casos que ya pasaban son los que el f-string acertaba por casualidad.
Verde: `15 passed`.

## 4 · Test viejo retirado (uno) y contra qué requisito

`test_f036_r14_el_resolver_de_tipologia_sigue_funcionando`
(`tests/test_f036_r14_ler_reexportado.py`) exigía que el resolver
determinista siguiera importándose. Lo sustituye **R12** («retirar el
resolver como DECISOR») y su test
`test_f043_r12_el_resolver_de_tipologia_ya_no_existe`, que exige lo
contrario; lo que ese test protegía de verdad —que sv2 no reimplemente el
catálogo LER, que es de lo que trata F-036 R14— lo sigue cubriendo su test
hermano, intacto. La retirada queda escrita en el propio fichero. **Ningún
otro test se retiró ni se relajó.**

## 5 · El commit de refuerzo (`3a10fce`)

`generar_mutantes` (generación, sin campaña: mutar el árbol es T28) dio 16
mutantes en el alcance del bloque. **Dos habrían sobrevivido**, los dos sobre
el aviso de R15 en `extraction_worker.py` (`:80`, invertir el `if
prompt_fase2 is None` que lo emite; `:145`, el `or` del mensaje final): el
test buscaba la palabra `generico` en cualquier registro y la línea final
también la lleva, así que **el aviso entero podía desaparecer sin que nadie
se enterara**, y R15 lo pide literalmente. Los dos, cazados ahora —verificado
inyectando cada mutación: 2 tests caídos cada una—. Además se retiró un `or
"-"` cosmético del log del resolver (`:166`) cuyo único mutante no se podía
cazar sin fijar el formato del log en un assert. Detalle en el commit.

## 6 · Fuera de alcance y MANUAL

- **sv3, sv4, sv5 y sv6: intactos** (son T13-T24); sus suites se ejecutaron
  enteras y siguen verdes (§7). **El catálogo del bloque A no se tocó**: no
  hizo falta, no se encontró ningún fallo en él.
- **Aviso heredado, comprobado**: sv5 conserva su `DocumentoAlbaran` con
  `extra='forbid'` y sin `clasificacion`
  (`albaran-valoracion-api/domain/models/albaran_models.py:56`). Con sv2 ya
  emitiendo `clasificacion` en `data`, **la suite de sv5 sigue verde (18
  passed)**: hoy no valida documentos de sv2. Decisión, en T18-T20.
- **`ruff` +3 en el contador de `init.sh`** (1115 → 1118) y no es deuda nueva
  de código: −1 por el borrado del resolver y **+4 `I001`** en los cuatro
  tests nuevos, que desde el servicio dan `All checks passed` y desde la raíz
  no (esa configuración no sabe que `application` y `domain` son first-party
  de sv2; **los dos órdenes son mutuamente excluyentes**, comprobado). Se
  mantuvo el del servicio, como el bloque A. Cerrarlo pide un
  `known-first-party` en el `pyproject` de la raíz: fuera de alcance.
- **MANUAL de este bloque: ninguna** (sin red, sin BBDD, sin LLM). Las de la
  feature siguen siendo T30 (evals), T31 y T32.
- **Lo que este bloque NO demuestra**: que la IA clasifique bien con el
  prompt nuevo — `config/prompts.yaml` es RUTA SENSIBLE y su evidencia es
  **T30**. Aquí se comprueba lo comprobable sin LLM: que el marcador se
  renderiza, que el catálogo entra entero con sus tres textos, que el prompt
  pide los campos que el contrato espera y que ninguno de los cinco prompts
  enumera familias a mano.

## 7 · Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests nuevos de F-043 en el bloque | **75** (15 prompt fase 1 · 38 resolver · 7 phase_merge · 15 worker), todos en verde; 1 test viejo retirado |
| Suites (una a una, nada en paralelo) | raíz **556 passed** (255,8 s) · sv2 **139 passed** (12,5 s) · sv3 **131 passed** (4,1 s) · sv4 **131 passed** (6,3 s) · sv5 **18 passed** (1,2 s) · sv6 **185 passed** (4,3 s) · comun **118 passed, 3 skipped** (132,1 s). **Cero fallos, cero skips nuevos.** |
| Cobertura de líneas cambiadas | **98,9 %** (454/459, umbral 80 %, nivel `critico`) — sobre el diff contra `dev`, que arrastra F-036 y el bloque A, no solo este bloque |
| Mutantes **generados** en el alcance | **16** (9 resolver · 2 phase_merge · 5 worker; 0 en `tipologia.py`, `albaran_extraction_service.py` y el pipeline). Tras `3a10fce`, **15** |
| Mutantes ejecutados / supervivientes | **no ejecutados**: la campaña muta el árbol principal y la completa es **T28**, del humano. Los 16 se revisaron uno a uno y los 2 que habrían sobrevivido se cerraron (§5) |
| Tiempo de la suite | el de cada suite, fila 2 |
| `ruff` en los ficheros nuevos | **0** desde el servicio; 4 `I001` desde la raíz, explicados en §6 |

## 8 · `bash harness/init.sh` — resultado real

**Verde**: `ENTORNO LISTO. Puedes trabajar.` — raíz **556 passed in
255.82s**, las seis suites de servicio en verde, `PUERTA COBERTURA [OK]
98.9%` (454/459, umbral 80 %, nivel `critico`), `PUERTA TAMAÑO [OK]`, rama
correcta y árbol limpio tras los nueve commits.

Avisos, **todos previos y ninguno bloqueante**: F-036 en `blocked`; `ruff`
1118 de deuda (§6); sv1-email e `infra` sin tests; marcas `[ADAPTAR]` en las
specs de F-034/F-035; y `PUERTA RUTAS SENSIBLES` en aviso, ahora con **8**
rutas en vez de 7 — la nueva es `services/albaranes-api/config/prompts.yaml`,
tocada por T6 y T7. Su evidencia es **T30**, reservada al humano.

---

*Tamaño*: este informe queda en **261** líneas frente al tope de 220. La
puerta mide `progress/impl_F-043.md` (nombre exacto), no los informes por
bloque, y sale `[OK]`; el bloque A quedó en 221 por la misma razón. Lo que no
se recortó, por norma del rol: las trazas de la fase RED, la sección
«Evidencias» y el resultado real de `init.sh`. Lo que sí: dos listados
`FAILED` largos, resumidos y enlazados a su commit.
