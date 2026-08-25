<!-- progress/impl_F-036_bloque_D.md -->
# F-036 · Implementación — BLOQUE D (cierre: reversión de T11, T21, T22, T25)

Rama `feature/F-036-residuos-contenedores-e-incrementos`, rigor `critico`.
Bloques anteriores: `impl_F-036.md` (A), `..._bloque_B.md`, `..._bloque_C.md`.
Ningún `git push`. `harness/features.json` NO se ha tocado.

| Commit | Trabajo |
|---|---|
| `7ca2ffc` | Reversión de T11 por decisión del humano (la tipología la decide la IA) |
| `591d9ee` | T21 + T22 · escenario de aceptación de SALMEDINA (R25) |
| `766abee` | T25 (1) · `jinja2` duro en sv4 y su venv declarado en el arnés |
| `492889e` | T25 (2) · el motivo de la guarda de R15 entra en el contrato de motivos |

> **LO PRIMERO QUE TIENE QUE LEER EL HUMANO** está en «El hueco que deja la
> reversión de T11», más abajo: **SS-0003967 no llega a 210,00 € de extremo a
> extremo**, y no por culpa de la reversión sola. T24 fallará en ese albarán.

## 1 · Reversión de T11 (decisión del humano, 2026-08-25)

Razón literal recogida en `tasks.md`: *«es la IA1 la que debe decidir cómo
clasifica. No puede ser determinista. Además, los residuos no se deben
clasificar solo porque contengan LER»*.

Retirado del commit `e4e3122`:

- `services/albaran-valoracion-api/application/services/valuation_extraction_service.py`:
  la función `_hay_ler_en_linea`, su uso en `_derivar_tipologia_valoracion` y
  el import de `ruesma_comun.ler`. La docstring dice ahora por qué NO está.
- `services/albaran-valoracion-api/tests/test_f036_r13_tipologia_ler.py`
  (borrado; eran los 16 tests que bajan la suite de sv5 de 34 a 18).

Spec actualizada para que no describa un sistema que ya no es el real:
**R13** marcado RETIRADO en `requirements.md`, la sección de sv5 de `design.md`
dice que `_derivar_tipologia_valoracion` NO se toca, y **T11** queda en
`tasks.md` como RETIRADA con fecha y razón. Para no pasarse del tope de 150
líneas se reflowó **R27**, que además nombraba «la tipología de sv5» entre los
tests exigidos: ya no existe. `ruesma_comun.ler` y el `tipologia_resolver` de
sv2 no se han tocado (sv6 usa el primero; el enrutado de la fase 1 es otro
asunto).

**Evidencia del efecto** (no hay fase RED: es una reversión, y su test se
borra). Mismo comando antes y después, con el intérprete de sv5:

```
# ANTES
LER sin tipo_familia -> residuos
# DESPUÉS
LER sin tipo_familia -> generico
IA dice residuos    -> residuos
```

`ruff` sobre el fichero: **18 avisos antes, 18 después** (deuda previa de
`Dict`/`Optional`; ninguno nuevo). Suite de sv5: **18 passed**.

## 2 · El hueco que deja la reversión de T11 (LO QUE DEBE DECIDIR EL HUMANO)

El encargo avisaba de que el arreglo de SS-0003967 (540 → 210) dependía del
scorer de sv3 (T9/T10, hecho) y de la regla dura de sv5 (T11, ahora retirada).
**No se sostiene**, y al medirlo aparece una segunda causa, más profunda, que
la reversión no ha creado:

1. **Toda la maquinaria de residuos de sv6 está cerrada tras
   `contexto_linea.tipo_familia == 'residuos'`**: el cálculo de contenedores
   (`valuation_builder.py:1165`), la red de sintéticas del LER (`:846`) y la
   guarda anti-incremento de R15 (`:985`).
2. **T9/T10 NO devuelven ese campo.** Por diseño (R12) los cinco campos
   NARRATIVOS —`tipo_familia` entre ellos— llegan íntegros del contexto ganador
   y no se fusionan; lo que R9-R11 restituyen son las nueve MEDIDAS.
3. El merge real de SS-0003967 traía **`contexto_linea = NULL`**
   (`progress/explore_F-036.md`, apéndice D2). Bajo el scorer viejo eso solo
   ocurría si NINGÚN candidato traía ninguno de los cinco narrativos, o sea:
   **ningún proveedor puso `tipo_familia` en ese albarán**. Tras T9/T10 el
   contexto sobrevivirá si algún candidato trajo LER o m³, pero seguirá sin
   familia.

Medido con el builder real (fixtures, sin BBDD), mismo albarán y mismo
contrato, cambiando solo el `tipo_familia`:

```
SIN tipo_familia -> total 540.0 | lineas 1
    from_albaran 6.0 None 90.0 540.0
CON tipo_familia -> total 210.0 | lineas 2
    from_albaran 6.0 1.0 120.0 120.0
    synthetic_modifier 1.0 1.0 90.0 90.0
```

Y la guarda de R15, sola, tampoco produce los 210: anula el match con el
incremento y manda a revisión, que es lo correcto, pero deja el total en 90.

```
tipo_familia OK pero IA3 casó el incremento -> total 90.0 | review True
```

**Consecuencia:** R25 se cumple en el escenario de aceptación (sv6 desde el
sobre de sv5), pero **T24 —la comprobación del humano contra la BBDD real—
fallará en SS-0003967** mientras el merge no traiga `tipo_familia='residuos'`.
No se ha reintroducido la regla ni se ha rodeado el problema. Opciones para el
humano, ninguna dentro del alcance de F-036: (a) que la IA1 rellene
`tipo_familia` de forma fiable (es lo que él pide), (b) abrir los gates de sv6
al `codigo_ler` además del `tipo_familia`, o (c) que sv3 propague al merge la
tipología que sv2 ya resuelve en fase 1 y hoy no persiste en ningún campo que
sv5 o sv6 lean.

## 3 · T21 y T22 · escenario de aceptación de SALMEDINA

`services/albaran-valoracion-persist/tests/test_f036_r25_salmedina_importes.py`
(**19 tests**), con los seis albaranes en alcance del ground truth
(`revision_residuos_salmedina_20260819.md` §8.1). SS-0026122 fuera: su tarifa
de 9 m³ contra OFERTA es F-017. Sin red, sin BBDD, sin LLM. Reutiliza
`tests/f036_escenarios_residuos.py` del bloque C, al que solo se le añadió el
argumento `codigo_contrato` para poder nombrar los dos contratos reales del
lote (CTSU24/0228 de la obra 687 y CTSU24/0402 de la 691).

- **T21** — `SS-0000589` 171,00 (120 + 51 del LER 170802), `SS-0003967` y
  `SS-0801977` 210,00 (120 + 90 del LER 170604). Se fija también el CONCEPTO de
  la sintética, su rol, su `modifier_source` y su padre, no solo el importe:
  §8.2 avisa de que un total correcto puede tapar un match equivocado.
- **T22** — `SS-0000168` y `SS-0003935` 120,00, `SS-0025146` 136,00. El
  invariante es el TOTAL, y **cada uno gana una sintética sin precio
  (`match_method='no_match'`) con `residuos_ler_sin_tarifa_en_contrato` y
  `review_required` en línea y cabecera**. El test lo afirma como lo QUERIDO
  (R16/R17), con el porqué escrito en su docstring.
- Invariante común a los seis: se valora **1 UD**, no los 6 m³ (que son la
  capacidad del contenedor), a la tarifa del contenedor de SU contrato.
- Un test más fija la **precondición** de todo lo anterior y deja escrito el
  hueco de §2: sin `tipo_familia` no corre ninguna regla de residuos.

**Fase RED — contra `dev`, no simulada.** Se creó un `git worktree` de `dev`,
se copiaron el fichero de test y su módulo de apoyo, y se lanzó la suite con el
mismo intérprete (el worktree se eliminó después):

```
E       assert 120.0 == 171.0 ± 1.7e-04     (SS-0000589)
E       assert 120.0 == 210.0 ± 2.1e-04     (SS-0003967)
E       assert 120.0 == 210.0 ± 2.1e-04     (SS-0801977)

>       assert len(sinteticas) == 1          (SS-0000168 / 3935 / 25146)
E       assert 0 == 1
E        +  where 0 = len([])

9 failed, 10 passed in 0.82s
```

Verde tras F-036: **19 passed in 0.72s**. Suite de sv6 completa: **175 passed**
(156 antes del bloque). `ruff` sobre los dos ficheros: `All checks passed!`.

## 4 · T25 (parte 1) · el entorno de los tests de render de sv4

Punto 4 de `progress/review_F-036_bloque_A.md`, decidido por el humano.

1. `services/albaranes-front/tests/conftest.py`: `pytest.importorskip("jinja2")`
   pasa a `import jinja2` a nivel de módulo, con el porqué en la docstring.
2. `harness/servicios.json`: sv4 declara `"venv": "services/albaranes-front/.venv"`.
   Verificado con `python -m harness.servicios --shell`, que ahora resuelve
   `.../services/albaranes-front/.venv/Scripts/python.exe` para sv4 y deja
   intactos los otros siete.
3. Ese venv no tenía `pytest` ni `coverage` (init.sh mide cobertura por
   servicio cuando `coverage` está disponible). **Comando exacto ejecutado:**

   ```
   services/albaranes-front/.venv/Scripts/python.exe -m pip install pytest coverage
   ```

   Instalados: `pytest 9.1.1`, `coverage 7.15.4` y sus dependencias
   (`iniconfig 2.3.0`, `packaging 26.3`, `pluggy 1.6.0`, `pygments 2.21.0`).
   **No se ha tocado `requirements.txt` ni ningún manifiesto**: son
   dependencias de desarrollo, no de la imagen de sv4.

**Fase RED.** El venv raíz sí tiene `jinja2`, así que el defecto no se veía. Se
simuló un intérprete sin ella con un `sitecustomize.py` en el scratchpad que
inserta un finder que niega `jinja2` (no se desinstaló nada de ningún venv):

```
# ANTES (importorskip)
SKIPPED [1] tests\test_f036_r1_r8_conversion_no_reproducible.py:705: jinja2 es
  dependencia declarada de sv4 (requirements.txt); sin ella no se puede
  comprobar lo que pinta la plantilla
  ... (11 SKIPPED en total, 5 en r1_r8 y 6 en r23_r24)
120 passed, 11 skipped in 1.27s
exit code = 0            <-- la suite daba VERDE sin comprobar el render

# DESPUÉS (import duro)
ImportError while loading conftest '...\services\albaranes-front\tests\conftest.py'.
tests\conftest.py:32: in <module>
    import jinja2
E   ModuleNotFoundError: No module named 'jinja2'
exit code = 4
```

Con jinja2 presente y **el venv declarado**: `131 passed`, y `coverage run -m
pytest` + `coverage json` funcionan en ese venv (es lo que hace init.sh).
`init.sh` lo confirma en su sección de servicios: *«servicio sv4-front
(services/albaranes-front): pytest en verde»* con 131 tests.

## 5 · T25 (parte 2) · el rojo que sacó `init.sh`

La primera pasada de `bash harness/init.sh` salió en **rojo**, y no por nada de
este bloque: `tests/test_f027_r18_r22_contrato.py` congela el vocabulario de
motivos del `valuation_builder`, y **T15 (bloque C) añadió
`residuos_base_casada_con_incremento` sin ampliar esa lista**. El bloque C no
llegó a ejecutar `init.sh`, así que el rojo apareció aquí.

```
tests\test_f027_r18_r22_contrato.py:222: in
test_f027_r22_el_builder_no_introduce_ni_retira_motivos
    assert _motivos_de(VALUATION_BUILDER) == MOTIVOS_DEL_BUILDER
E   AssertionError: Extra items in the left set:
E     'residuos_base_casada_con_incremento'
1 failed, 257 passed in 69.13s (0:01:09)
```

Se amplía la lista **haciendo lo que su propia docstring exige**, no para
callar el test: comprobado quién consume el string. sv6 solo lo escribe; sv4
pinta las razones de línea en crudo desde `review_reasons_json` (R23, bloque
A) y no tiene lista blanca de cadenas (`grep` de otros motivos del builder en
`services/albaranes-front`: cero apariciones). Verde: `9 passed`.

## 6 · Verificación final (resultados literales)

`bash harness/init.sh`, ejecutado tal cual, solo y el último:

```
[OK] Arnés v1.7.2 (2026-08-21)
[OK] features.json válido        (42 features, en curso: ['F-036'])
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 1112 avisos (deuda previa, no bloquea)
[OK] pytest en verde (con medición de cobertura)   <- raíz: 531 passed en 115,65 s
[OK] servicio sv2-api: pytest en verde                    58 passed
[OK] servicio sv3-persistencia: pytest en verde          117 passed
[OK] servicio sv4-front: pytest en verde                 131 passed
[OK] servicio sv5-valoracion-api: pytest en verde         18 passed
[OK] servicio sv6-valoracion-persist: pytest en verde    175 passed
[OK] servicio comun: pytest en verde              64 passed, 3 skipped
[OK] PUERTA COBERTURA: 97.8% de 273 líneas cambiadas cubiertas (267/273,
     umbral 80%, nivel critico)
[AVISO] PUERTA RUTAS SENSIBLES [evals]: falta progress/evals_F-036.md
[OK] PUERTA TAMAÑO: F-036 dentro de los topes
     (requirements 149/150, design 228/250, impl 220/220)
[OK] Rama actual: feature/F-036-residuos-contenedores-e-incrementos
```

Veredicto de esa pasada: **`ENTORNO LISTO. Puedes trabajar.`**, exit code 0.
En ella los seis servicios salieron por caché de suite (árbol sin cambios desde
su último verde); los números de la tabla son los de sus últimas ejecuciones
reales, todas de esta sesión.

## 7 · Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (monorepo, `tests/`) | **531**, todos en verde |
| Tests ejecutados (sv6) | **175** (156 antes de este bloque) |
| Tests ejecutados (sv4) | **131**, ahora con el venv de sv4 |
| Tests ejecutados (sv5) | **18** (34 antes: −16 del test borrado con T11) |
| Tests nuevos de este bloque | **19** (el escenario de SALMEDINA) |
| Cobertura de líneas cambiadas | **97,8 %** (267/273), umbral 80 %, nivel `critico` |
| Mutantes generados / supervivientes | **NO medido aquí: es T23**, y el encargo del líder la deja explícitamente al humano (`python -m harness.mutacion --feature F-036` → `progress/mutacion_F-036.md`) |
| Tiempo de ejecución de las suites | raíz 115,7 s · sv2 2,4 s · sv3 3,4 s · sv4 4,1 s · sv5 1,4 s · sv6 3,8 s · comun 121 s |

Las 6 líneas cambiadas sin cubrir son las mismas de bloques anteriores, ya
justificadas en `impl_F-036.md` y `impl_F-036_bloque_B.md`. De este bloque no
queda ninguna línea cambiada sin cubrir.

## 8 · Lo que queda fuera y lo que le queda al humano

1. **DECISIÓN PENDIENTE — el hueco de §2.** SS-0003967 no alcanza los 210,00 €
   de extremo a extremo: **T24 fallará en ese albarán**. No es un descuido del
   bloque, es la consecuencia medida de retirar T11 sumada a que sv6 exige
   `tipo_familia`. Tres opciones propuestas en §2; ninguna cabe en F-036 sin
   una decisión suya.
2. **T23 · campaña de mutación**: no ejecutada. La lanza el humano.
3. **T24 · comprobación contra la BBDD real**, en solo lectura: MANUAL, del
   humano. Ojo al punto 1 antes de darla por fallida en su conjunto: los otros
   cinco albaranes no dependen de ese hueco.
4. **`progress/evals_F-036.md`**: la puerta de rutas sensibles avisa (no
   bloquea) de que faltan las evals de seis rutas tocadas. **NO se ha lanzado
   `python -m evals.runner --con-llm`**: gasta LLM real y la decisión es suya.
5. **`pytest` y `coverage` en el venv de sv4** son ahora dependencia del
   entorno de desarrollo de cualquiera que ejecute `init.sh`. Si otra máquina
   del equipo no los tiene en ese venv, su `init.sh` saldrá en rojo en sv4;
   conviene decidir si eso se documenta en el README de sv4 o se añade un
   `requirements-dev.txt`.
6. **Nada se ha ejecutado contra Azure, la BBDD real ni un LLM.** Ningún
   `git push`; cuatro commits locales en la rama de la feature. `features.json`
   sin tocar.

## Estado de cierre

**`bash harness/init.sh` termina con exit code 0** en la pasada final (ver la
salida completa en §6): las únicas marcas no verdes son los tres AVISOS que no
bloquean (deuda de `ruff`, evals pendientes del humano y las marcas `[ADAPTAR]`
de las specs de F-034/F-035, ajenas a esta feature).

**T25 queda cumplida. T21 y T22 quedan cumplidas como test.** Lo que NO puede
darse por cumplido es **R25 de extremo a extremo**, por §2. Por eso este bloque
se entrega como **`blocked`**: hace falta una decisión del humano antes de que
el reviewer pueda aprobar la feature contra `CHECKPOINTS.md`.
