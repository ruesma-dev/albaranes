<!-- progress/impl_F-034.md -->
# F-034 · Informe de implementación

**Feature**: el mutador del arnés no muta `is` / `is not`, más dos
incoherencias que arrastra la puerta de evals.
**Rama**: `feature/F-034-mutacion-is-y-coherencia-evals` (desde `dev`, HEAD de
partida `9cbe46d`).
**Rigor declarado**: `estandar`. **Spec**: `specs/F-034-mutacion-is-y-coherencia-evals/`.
**Servicios tocados**: NINGUNO. Ni una línea de `services/`.

---

## T0 · Las tres decisiones abiertas, resueltas por el humano

Recogidas del líder (que aplica la recomendación del spec-author). Literal:

1. **D1 — remedir el histórico: opción B.** Se remiden **solo F-019 y F-027**,
   no todas. Motivo: esas dos campañas hay que lanzarlas igual como prueba de
   que el cambio funciona, así que la re-medición sale casi gratis, y son justo
   las dos features cuyo defecto vivía en una guarda `is`. Las demás **no** se
   remiden; en su lugar se deja anotado por escrito que su campaña se midió con
   la vara anterior.
2. **D2 — la versión de `arnes-base` es la 1.6.0**, no 1.5.3.
3. **D3 — sí, se corrige la descripción de F-034 en `harness/features.json`**:
   afirma que `evals/ground_truth/` no existe y **sí existe**. Se corrige la
   premisa sin borrar el resto de la descripción.

## T1 · Medición de partida (el «antes»), con el mutador SIN tocar

Cálculo puro (`harness.alcance` + `harness.mutacion.generar_mutantes`), sin
ejecutar ninguna suite, leyendo cada fichero del alcance en el tip de su rama
con `git show`. El script vive en el scratchpad de la sesión, no en el
repositorio; su lógica es esta, y se puede repetir tal cual:

```python
from harness.alcance import alcance_de_feature
from harness.mutacion import generar_mutantes
alcance = alcance_de_feature(feature, base=<sha>, rama=<rama>)
total = sum(len(generar_mutantes(git_show(rama, f), alcance.lineas[f], f))
            for f in alcance.ficheros())
```

Salida real, con el mutador tal como estaba en `9cbe46d` (arnés 1.5.2):

```
F-019: 31 mutantes  (515 líneas de alcance)
F-027: 0 mutantes  (58 líneas de alcance)
```

**31 y 0 reproducen exactamente los totales históricos** de
`progress/mutacion_F-019.md` y `progress/mutacion_F-027.md`. El método es
fiable, así que el «después» de T5/T6 es comparable con este «antes».

## T2 · Fase RED

`tests/test_mutacion_operadores.py`, nueve casos (uno por requisito de G1 más
el de R14), escritos **antes** de tocar `harness/mutacion.py`.

Comando exacto:

```bash
python -m pytest tests/test_mutacion_operadores.py -q --no-header -p no:cacheprovider --tb=line
```

Salida real del fallo (7 fallan, 2 pasan — R6 y R7 fijan comportamiento actual
que NO debe cambiar, así que pasar en rojo es lo correcto):

```
FFFFF..FF                                                                [100%]
================================== FAILURES ===================================
E   AssertionError: esperado 1 mutante de comparación, hay 0
    assert 0 == 1
     +  where 0 = len([])
tests/test_mutacion_operadores.py:113: AssertionError   [R1]
E   AssertionError: esperado 1 mutante de comparación, hay 0
    assert 0 == 1
     +  where 0 = len([])
tests/test_mutacion_operadores.py:123: AssertionError   [R2]
E   AssertionError: esperados 2 mutantes, hay 0
    assert 0 == 2
     +  where 0 = len([])
tests/test_mutacion_operadores.py:133: AssertionError   [R3]
E   AssertionError: assert [] == ['comparacion']

      Right contains one more item: 'comparacion'
tests/test_mutacion_operadores.py:153: AssertionError   [R4]
E   AssertionError: esperado 1 mutante, hay 0
    assert 0 == 1
     +  where 0 = len([])
tests/test_mutacion_operadores.py:173: AssertionError   [R5]
E   IndexError: list index out of range
tests/test_mutacion_operadores.py:198: IndexError       [R8]
E   AssertionError: la condición de la puerta no nombra los fixtures versionados: "Se sube a 'bloqueo' cuando los libros de evals/ground_truth/ tengan casos: hasta entonces la pasada completa no puede dar VERDE porque no hay nada que evaluar."
    assert 'evals/fixtures/' in "Se sube a 'bloqueo' cuando los libros de evals/ground_truth/ tengan casos: hasta entonces la pasada completa no puede dar VERDE porque no hay nada que evaluar."
tests/test_mutacion_operadores.py:234: AssertionError   [R14]
=========================== short test summary info ===========================
FAILED tests/test_mutacion_operadores.py::test_f034_r1_muta_is_a_is_not
FAILED tests/test_mutacion_operadores.py::test_f034_r2_muta_is_not_a_is
FAILED tests/test_mutacion_operadores.py::test_f034_r3_una_mutacion_por_operador_en_la_misma_linea
FAILED tests/test_mutacion_operadores.py::test_f034_r4_el_operador_declarado_es_comparacion
FAILED tests/test_mutacion_operadores.py::test_f034_r5_no_muta_dentro_de_una_palabra_del_comentario
FAILED tests/test_mutacion_operadores.py::test_f034_r8_el_mutante_compila_y_el_ast_lleva_el_operador_contrario
FAILED tests/test_mutacion_operadores.py::test_f034_r14_la_puerta_de_evals_no_se_declara_sobre_lo_no_versionado
7 failed, 2 passed in 0.08s
```

(Las rutas absolutas de la salida original se han acortado a rutas relativas y
se ha añadido `[Rn]` al final de cada línea para poder leerla; el resto es
literal.)

**PENDIENTE hasta T4**: la segunda fase RED, la de R5. Con `ast.Is` ya en la
tabla pero sin delimitador de palabra, R5 falla por un motivo **distinto** —el
mutante cae dentro del comentario— y esa traza es la que demuestra el segundo
defecto.

## T3 y T4 · El cambio en `harness/mutacion.py`, en dos pasos

**T3 — la tabla.** `COMPARACIONES` gana `ast.Is: ("is", "is not")` y
`ast.IsNot: ("is not", "is")`, con el comentario que declara el límite de R7.
No hizo falta tocar `_candidatos`: ya recorre `nodo.ops` emitiendo un candidato
por operador, así que R3 (encadenadas y unidas por `and`/`or`) salió sola.

Tras T3: R1, R2, R3, R4, R7 y R8 en verde; suite de la raíz **275 passed, 2
failed** (R5 y R14, que aún no tocaban turno). Ninguna regresión.

**Segunda fase RED, la de R5.** Con la tabla ya cargada pero sin delimitador de
palabra, R5 falla por el motivo que la spec predijo — y esta es la traza que lo
demuestra:

```
tests/test_mutacion_operadores.py:174: in test_f034_r5_no_muta_dentro_de_una_palabra_del_comentario
    assert mutantes[0].linea == 4, (
E   AssertionError: el mutante cayó en la línea 3 ('valor  # el analis notis previo'); el operador está en la 4
E   assert 3 == 4
E    +  where 3 = Mutante(fichero='modulo.py', linea=3, col=24, original='valor  # el analisis previo', mutado='valor  # el analis notis previo', operador='comparacion', longitud=2, sustituto='is not').linea
```

El mutante caía **dentro de un comentario**: `analisis` → `analis notis`. No
cambia el comportamiento, sobrevive siempre y ensucia el informe con un falso
superviviente.

**T4 — el delimitador.** `_PARTE_DE_PALABRA`, `_es_palabra`, `_delimitado` y el
paso de «primera coincidencia» a «primera coincidencia **válida**» dentro del
mismo hueco. Se aplica **solo** a tokens que empiezan y acaban en carácter de
palabra (`is`, `is not`, `not`, `and`, `or`, `True`, `False`, enteros); los
símbolos se quedan como estaban, o `x==y` dejaría de mutar (R6 lo fija).

Tras T4: `tests/test_mutacion_operadores.py` con **8 de 9** en verde (R14 es de
T8); suite de la raíz **276 passed, 1 failed** (solo R14). Sin regresión de
`not`, `and`, `or`, booleanos ni enteros.

Cálculo puro sobre los mismos alcances históricos, ya con el mutador cambiado:

```
F-019: 49 mutantes  (515 líneas de alcance)
F-027: 1 mutantes  (58 líneas de alcance)
```

**Antes → después: F-019 de 31 a 49 (+18) y F-027 de 0 a 1 (+1)**, exactamente
lo que R9 y R10 exigen.

## T5 · Campaña real sobre F-027 — el mutante nuevo cae en una guarda de verdad

Comando exacto, reproducible tal cual (R12):

```bash
python -m harness.mutacion --feature F-027 \
  --base e95549d8880ebdabee45c1ec4fbe20651240428f \
  --rama feature/F-027-conversion-kg-tn-muerta \
  --workers 1 --salida progress/mutacion_F-027_remedida.md
```

Salida real:

```
F-027: 2 fichero(s), 58 línea(s) de producción (origen rama, e95549d8880ebdabee45c1ec4fbe20651240428f..feature/F-027-conversion-kg-tn-muerta)
[1/1] muerto        services/albaran-valoracion-persist/application/services/valuation_builder.py:1033 [comparacion] if partida_result.derived_line is not None: -> if partida_result.derived_line is None:
1 mutantes evaluados, 1 muertos, 0 supervivientes, 0 timeouts en 2.5 s
Informe: progress/mutacion_F-027_remedida.md
```

**R9 cumplido al pie de la letra**: 1 mutante, en
`valuation_builder.py:1033`, con el texto exacto que la spec anticipaba, y
**MUERTO**. Es el **M1** de la campaña manual de F-027, la que el reviewer
reprodujo a mano con 17 fallos: la herramienta nueva coincide con el resultado
medido antes de que existiera. F-027 pasa de un «0 mutantes» que no demostraba
nada a un mutante real cazado por los tests que ya había.

## T6 · Campaña real sobre F-019 — y un superviviente NUEVO que hubo que cerrar

Comando exacto (R12), precedido del `cp` que repone los análisis ya escritos:

```bash
cp progress/mutacion_F-019.md progress/mutacion_F-019_remedida.md
python -m harness.mutacion --feature F-019 \
  --base cd904cdcecee56311280ee54d81a7158d0529eb5 \
  --rama feature/F-019-importe-unitario-manda \
  --workers 1 --salida progress/mutacion_F-019_remedida.md
```

### Primera pasada: 49 generados, 45 muertos, **4** supervivientes

Los 3 conocidos volvieron a salir **con su análisis repuesto** por el mecanismo
de la 1.5.1 (`analisis_escritos` + `AVISO_REPUESTO`), que queda así ejercitado
sobre un caso real. Y apareció **uno nuevo**, de los de `is`:

```
[5/49] superviviente services/albaran-valoracion-persist/application/services/importe_calculator.py:203 [comparacion] leido = valor if valor is not None else descuento_pct -> leido = valor if valor is None else descuento_pct
```

### Análisis del superviviente nuevo: **hueco real de la suite**, no equivalente

`_sanitize_descuento` deja traza auditable de un descuento fuera de rango:
`descuento_fuera_de_rango_ignorado:{leido}`. `clasificar_descuento` devuelve
`(estado, valor)`, y para `invalido` hay **dos casos distintos**:

| Entrada | `valor` | `leido` original | `leido` mutado |
|---|---|---|---|
| `150.0` (fuera de rango, numérico) | `150.0` | `150.0` | `150.0` — **idéntico** |
| `"15%"` o `nan` (ilegible) | `None` | `"15%"` / `nan` | **`None`** |

El único test que tocaba ese motivo usaba `150.0`, justo el caso en que ambas
ramas coinciden: por eso el mutante sobrevivía. En el caso ilegible —el que de
verdad importa, porque es cuando el motivo es la **única** pista de qué llegó
del PDF— el mutante borra la evidencia y deja `:None`.

Aplico **R11 opción (a): test nuevo que lo mata**. Ni una línea de producción
(la spec lo prohíbe expresamente, y el código está bien: es la suite la que
tenía el hueco):
`services/albaran-valoracion-persist/tests/test_f019_r8_r15_precedencia.py::test_f019_r15_el_motivo_conserva_el_valor_ilegible_que_llego`.

Fase RED del test nuevo — mutante aplicado a mano sobre una copia respaldada
del fichero, y restaurado inmediatamente después (`git status` limpio de
producción, verificado):

```
.F                                                                       [100%]
________ test_f019_r15_el_motivo_conserva_el_valor_ilegible_que_llego _________
tests\test_f019_r8_r15_precedencia.py:510: in test_f019_r15_el_motivo_conserva_el_valor_ilegible_que_llego
    assert "descuento_fuera_de_rango_ignorado:15%" in resultado.reasons
E   AssertionError: assert 'descuento_fuera_de_rango_ignorado:15%' in ['descuento_fuera_de_rango_ignorado:None']
E    +  where ['descuento_fuera_de_rango_ignorado:None'] = ImporteResult(importe_calculado=100.0, importe_source='calculated', reasons=['descuento_fuera_de_rango_ignorado:None'], descuento_aplicado=None).reasons
WARNING  application.services.importe_calculator:importe_calculator.py:207 [importe] descuento_pct fuera de rango [0,100]: None. Se ignora.
1 failed, 1 passed, 27 deselected in 0.21s
```

El `1 passed` de esa línea es el test viejo (el de `150.0`) **pasando con el
mutante puesto**: la demostración de por qué no lo cazaba.

### Segunda pasada, la definitiva: 49 generados, **46 muertos, 3 supervivientes**

```
49 mutantes evaluados, 46 muertos, 3 supervivientes, 0 timeouts en 331.5 s
Informe: progress/mutacion_F-019_remedida.md
```

**R10 cumplido**: 49 mutantes (31 + 18 nuevos), los **18 nuevos muertos**, y los
supervivientes son **exactamente los 3** ya analizados como equivalentes en
`progress/mutacion_F-019.md`, con su análisis repuesto y ninguno en `PENDIENTE`.

## T7 · El histórico queda etiquetado con la vara con la que se midió (D1 = B)

En `progress/mutacion_F-019.md` y `progress/mutacion_F-027.md`, **una sola
línea** que apunta a su re-medición oficial (`git diff` de esos dos ficheros:
exactamente `1 +` en cada uno; nada más se tocó, porque llevan secciones
escritas a mano que `escribir_informe` no conserva).

D1 exige además dejar anotado por escrito que las campañas **no** remedidas se
midieron con la vara anterior. Lo he hecho donde de verdad se va a leer: **una
línea en cada uno** de `mutacion_F-001.md`, `F-002.md`, `F-011.md` y
`F-012.md`, diciendo con qué versión se midieron, cuántos mutantes de más
darían hoy (0, +18, +42, +10) y que la decisión del humano fue no remedirlos.

> **Extensión sobre la letra de T7**, que solo pedía los dos punteros. Sin esta
> nota, la parte de D1 que dice «lo que hay que anotar pase lo que pase» se
> quedaba solo en `ARNES_VERSION.md`, y nadie que abra `mutacion_F-011.md`
> dentro de dos meses va a mirar ahí.

## T8 · La puerta de evals dice dónde hay que mirar

`harness/rutas_sensibles.json` (solo la clave `_exigencia`), `CHECKPOINTS.md`
(C4 ter) y `progress/current.md` (las dos frases). La condición pasa a los
**fixtures versionados de `evals/fixtures/`**, con la aclaración de que los
libros `.xlsx` de `evals/ground_truth/` existen pero `.gitignore` los excluye.

Verificaciones, con su salida real:

```
$ python -m pytest tests/test_mutacion_operadores.py -q
9 passed in 0.08s

$ python -m harness.rutas_sensibles --validar
    1 verificación(es), 14 ruta(s) sensible(s) declaradas: evals (aviso)

$ grep -rn "ground_truth" CHECKPOINTS.md harness/rutas_sensibles.json progress/current.md
```
El `grep` sigue devolviendo líneas, y **debe** hacerlo: las que quedan son la
**aclaración** que R15 exige («existen pero no se versionan»), no la condición
de la puerta. Ninguna condiciona ya la subida a `bloqueo`.

## T9 · Rastro de la campaña manual

Punto nuevo en C4 bis de `CHECKPOINTS.md` y la misma exigencia en el punto 4
del protocolo de `.claude/agents/reviewer.md`: una fila por mutante, con
fichero y línea, **texto exacto original → mutado** y resultado con su número
de fallos; y el reviewer reproduce al menos dos filas al pie de la letra.

## T10 · Arnés 1.6.0 (D2)

`harness/VERSION` (`ARNES_VERSION=1.6.0`, `ARNES_FECHA=2026-08-19`) y
`harness/ARNES_VERSION.md`, con el aviso de que los informes de mutación de
1.5.2 o anterior **no son comparables** con los posteriores.

```
$ bash harness/init.sh
[OK] Arnés v1.6.0 (2026-08-19)
```

## T11 · Puertas propias de F-034 — y un FALSO VERDE que hay que contar

### La campaña, tal como la lanza el comando de `tasks.md`, MIENTE aquí

`python -m harness.mutacion --feature F-034 --workers 1` dio **19 mutantes, 19
muertos, 0 supervivientes en 35,5 s**. Ese resultado **no vale**, y lo digo yo
que lo generé. El motivo, medido:

El alcance de F-034 es `harness/mutacion.py`, que **no pertenece a ningún
servicio**. `ejecutor_para` manda esos ficheros a `EjecutorPytest(raiz=".")`,
que lanza `python -m pytest` **sin ruta**. Este repositorio **no tiene
configuración de pytest en la raíz** (no hay `pytest.ini`, `setup.cfg`,
`pyproject.toml` ni `tox.ini`), así que esa invocación recoge también
`services/**/tests`, que dependen de su propio `rootdir` y `sys.path`:

```
$ python -m pytest -x -q --tb=no -p no:cacheprovider
ERROR services/albaran-valoracion-persist/tests/test_f019_r8_r15_precedencia.py
1 error in 0.81s
EXIT=1
```

La suite **revienta en la recolección en 0,81 s, haga lo que haga el mutante**.
`EjecutorPytest.ejecutar` cuenta como MUERTO todo código de salida distinto de
0 y de 5, así que **los 19 salían «muertos» sin que ningún test los juzgara**.
El promedio de 1,87 s por mutante era la prueba a la vista: la suite de la raíz
tarda ~75 s.

### La campaña buena

Relanzada con la suite de la raíz de verdad (`pytest tests`), pasando el
ejecutor por la API en vez de por el CLI, que no tiene flag para esto:

```python
from harness.mutacion import EjecutorPytest, main
main(["--feature", "F-034", "--workers", "1", "--salida", "progress/mutacion_F-034.md"],
     ejecutor=EjecutorPytest(raiz=".",
                             argumentos=["tests", "-x", "-q", "--tb=no", "-p", "no:cacheprovider"]))
```

Salida real:

```
F-034: 1 fichero(s), 56 línea(s) de producción (origen rama, 28971321108528484c52c5c91108afc02af59084..feature/F-034-mutacion-is-y-coherencia-evals)
...
19 mutantes evaluados, 18 muertos, 1 supervivientes, 0 timeouts en 111.0 s
Informe: progress/mutacion_F-034.md
```

**19 generados, 18 muertos, 1 superviviente** — y el superviviente es de verdad,
no un artefacto: `harness/mutacion.py:207` `[entero]`,
`_PARTE_DE_PALABRA.match(objetivo[:1])` → `...(objetivo[:2])`. Está analizado y
cerrado como **mutante equivalente** en `progress/mutacion_F-034.md`, sin
ningún `PENDIENTE`: `_PARTE_DE_PALABRA` es una sola clase de carácter y
`Pattern.match` está anclado al principio, así que las dos rodajas interrogan
**el mismo byte 0**. Su gemelo de la línea 208 (`objetivo[-1:]` →
`objetivo[-2:]`), que sí cambia el byte interrogado, **muere** con
`test_f034_r7`.

> El contraste entre las dos campañas es la propia evidencia: la invocación del
> CLI daba **19/19 muertos en 35,5 s**; la buena, **18 muertos y 1 superviviente
> en 111 s**. Un «0 supervivientes» que tarda tres veces menos de lo que tarda
> la suite es la señal de que nadie ha corrido la suite.

### Comprobación de que un muerto es un fallo de test, no un error de suite

Mutante 1/19 aplicado a mano (`_es_palabra`: `and` → `or`), suite de la raíz:

```
FAILED tests/test_mutacion_operadores.py::test_f034_r6_los_simbolos_sin_espacios_siguen_mutando
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 273 passed in 53.01s
```

53 s, y lo caza un test con nombre y apellidos. Fichero restaurado acto seguido
(`git status` limpio, verificado).

### Lo que esto significa más allá de F-034

**Toda campaña de mutación sobre ficheros de la raíz en este repositorio está
afectada**: `progress/mutacion_F-012.md` (61 mutantes sobre `harness/`) se midió
con esa misma invocación rota. Las de F-019 y F-027 **no**: sus ficheros son de
servicios, y `ejecutor_para` les da la suite de su servicio, en su directorio y
con su intérprete — por eso T5 y T6 sí valen.

No lo arreglo aquí: cambiar `ejecutor_para` o añadir configuración de pytest a
la raíz está **fuera del alcance declarado** de F-034 y toca la puerta de todas
las features. Queda escrito, con el número medido, para que el humano decida.

## T12 · Porte a `arnes-base` — **BLOQUEADO**, y por qué no lo he forzado

> **NOTA DE CIERRE, añadida el 2026-08-19 al atender el review.** Todo lo que
> sigue en este §T12 es **registro histórico**: describe con exactitud lo que
> el implementer se encontró y por qué paró, y esa parada fue correcta. Pero
> **el bloqueo ya no existe y la feature SÍ se puede cerrar**. Lo resolvió el
> humano incorporando los dos encargos a la misma versión: la **1.6.0 de
> `arnes-base`** lleva el porte de F-034. **T12 está en `[x]`.** El desenlace
> completo, con commits y con lo que pasó después (una propagación de vuelta
> que hubo que revertir), en **§T15**. No leas este §T12 como el estado final.

**No he escrito ni un byte en `C:\Users\pgris\PycharmProjects\arnes-base`.** No
hay ningún commit mío allí, y por eso este informe no puede traer los hashes
que el reviewer espera.

### Lo que me encontré, con fecha y hora

Al empezar la sesión (≈ 13:50) comprobé el repositorio y estaba **limpio**, en
`9224a5a` («1.5.2: la mejora del reviewer…»), al día con su remoto. Al ir a
portar (≈ 14:50) tenía **tres ficheros modificados y sin commitear**:

```
$ git -C C:/Users/pgris/PycharmProjects/arnes-base status --short
 M arnes-base/harness/init.sh
 M arnes-base/harness/mutacion.py
 M arnes-base/harness/mutacion_paralela.py

$ git -C ... diff --stat HEAD
 arnes-base/harness/init.sh              |  27 +
 arnes-base/harness/mutacion.py          | 904 ++++++++++++++++++++++++++++---
 arnes-base/harness/mutacion_paralela.py | 100 +-
 3 files changed, 949 insertions(+), 82 deletions(-)
```

Con mtime **2026-08-19 14:31 y 14:45**, es decir escritos **durante** mi
sesión. `harness/VERSION` y `CHECKPOINTS.md` siguen con fecha de ayer.

### Qué son esos 949 cambios: NO son mi porte

Lo comprobé antes de tocar nada:

```
$ grep -c "ast.Is\|_PARTE_DE_PALABRA" arnes-base/harness/mutacion.py
0
```

Su `COMPARACIONES` sigue con seis entradas y sin `is`/`is not`. Es un trabajo
**distinto y ortogonal**, que se autodenomina **1.5.3** en sus propios
docstrings: línea base de la suite antes de juzgar, veredictos `INDETERMINADO`
y `BASE_ROTA`, manejadores de SIGINT/SIGTERM y centinela en disco. Textualmente,
en su cabecera: *«Si no está verde, la campaña se aborta: sobre una base roja
todo mutante sale “muerto” y el cero de supervivientes es mentira. Pasó de
verdad el 2026-08-19»* — que es, palabra por palabra, el mismo defecto que yo
he medido en T11.

### Por qué he parado en vez de seguir

Cualquier forma de completar T12 ahora hace daño:

| Si hiciera… | Qué pasaría |
|---|---|
| Sobrescribir `mutacion.py` con el de `albaranes` | **Destruyo 949 líneas** de trabajo sin commitear de otro. Irrecuperable. |
| Aplicar mi cambio **encima** del suyo y commitear | Commiteo el 1.5.3 **inacabado de otro** dentro de un commit «F-034», y R19 (`diff` idéntico entre repos) sale **falso**. |
| Portar solo lo que no colisiona (test, C4 bis, VERSION, guía) | El test nuevo **pone roja la suite de `arnes-base`**: su `mutacion.py` no muta `is`. Y `VERSION 1.6.0` + sección en `GUIA_INSTALACION.md` describirían un cambio **que no está en su código**: un registro falso. |
| `git stash` de su trabajo, portar, `unstash` | Manipular el árbol de otro agente que puede estar escribiendo ahora mismo. |

Ninguna es aceptable, y **no es una decisión que me toque a mí**. `CLAUDE.md`
lo dice sin matices: si el cambio toca otro trabajo, no se improvisa un
workaround — se marca `blocked`, se anota el motivo y se para. Es lo que hago.

### Lo que hay que decidir (humano) y lo que queda hecho para cuando se decida

1. **Quién aterriza primero.** Los dos cambios tocan el mismo fichero y son
   compatibles en el fondo (uno añade operadores, otro verifica la línea base);
   lo que no es automático es el orden ni la numeración.
2. **La numeración.** D2 fijó **1.6.0** para F-034. El trabajo en vuelo se
   llama **1.5.3**. Si aterriza antes, F-034 sería 1.6.0 igualmente; si aterriza
   después, alguien tiene que renumerar. `harness/VERSION` de `arnes-base` sigue
   en 1.5.2: **la subida no está hecha allí**, a propósito.
3. **La ironía útil**: el 1.5.3 en vuelo arregla exactamente el falso verde que
   T11 documenta. Si se integran los dos, la campaña de F-034 habría abortado
   sola en vez de dar 19 muertos falsos.

Del lado de `albaranes` **todo lo que el porte necesita está listo y
commiteado**: `harness/mutacion.py`, `tests/test_mutacion_operadores.py`, el
punto de C4 bis, la frase de `reviewer.md` y el texto del aviso de R20 (está en
`harness/ARNES_VERSION.md`, listo para copiar a `GUIA_INSTALACION.md`). El porte
es un `cp` y cuatro pegados **en cuanto el otro trabajo esté commiteado**.

## T13-T14 · Cierre

`bash harness/init.sh` **en verde**, ejecutado tal cual, en serie y sin nadie
más en el árbol. Salida relevante:

```
[OK] Arnés v1.6.0 (2026-08-19)
[OK] features.json válido
[AVISO] BACKLOG.md regenerado desde features.json: inclúyelo en el commit
[OK] compileall: sin errores de sintaxis
277 passed in 63.18s (0:01:03)
[OK] pytest en verde (con medición de cobertura)
111 passed in 2.87s
[OK] servicio sv6-valoracion-persist (services/albaran-valoracion-persist): pytest en verde
[OK] PUERTA COBERTURA: 100.0% de 12 líneas cambiadas cubiertas (12/12, umbral 80%, nivel estandar)
[OK] PUERTA RUTAS SENSIBLES [evals]: N/A (F-034 no toca ninguna ruta sensible declarada)
[OK] Rama actual: feature/F-034-mutacion-is-y-coherencia-evals
ENTORNO LISTO. Puedes trabajar.
```

Avisos que **ya venían de antes** y no los introduce esta feature: los 1.102 de
`ruff` (deuda previa), sv1-email e infra sin tests, y las marcas `[ADAPTAR]` de
las specs de F-034 y F-035 — en el caso de F-034 es un **falso positivo**: la
palabra aparece dentro de una frase de `design.md` §8 que *habla* de una marca
`[ADAPTAR]` resuelta, no es una marca sin resolver. No toco una spec aprobada
para acallar un aviso.

**D3 aplicado**: corregida la frase del punto (2) de la descripción de F-034 en
`harness/features.json`. Decía literalmente *«`CHECKPOINTS.md` C4 ter habla de
`evals/ground_truth/`, que NO EXISTE en este repositorio: los casos viven en
`evals/fixtures/inputs/`. La misma referencia equivocada aparece en
`progress/current.md` y en `harness/rutas_sensibles.json`»*. Ahora dice que el
directorio **sí existe** con sus seis libros, que `.gitignore` los excluye y que
el defecto real era condicionar la puerta a un artefacto invisible. `BACKLOG.md`
lo regenera `init.sh`.

## T15 · Lo que pasó DESPUÉS: T12 desbloqueado, una propagación y su revert

Esta sección se escribe al atender `progress/review_F-034.md` (veredicto
CHANGES_REQUESTED, cinco cambios requeridos). Cuenta lo ocurrido entre el
cierre de §T14 y hoy, para que nadie lea el §T12 dentro de dos meses y crea
que la feature quedó bloqueada.

### 1. T12 resuelto: la 1.6.0 de `arnes-base` absorbió los dos encargos

Las dos decisiones que §T12 dejaba en manos del humano —orden de aterrizaje y
numeración— las tomó el humano de la única forma que no obligaba a elegir:
**una sola versión con los dos encargos dentro**. La **1.6.0 de `arnes-base`**
lleva las cuatro piezas de «mutación fiable» **y** el porte de `is` / `is not`
de F-034. Commits allí, ya **pusheados** a `origin/main`:

| Commit | Qué trae |
|---|---|
| `860902e` | 1.6.0 (1/4): la campaña de mutación deja de poder contar muertos falsos |
| `b7dce9d` | 1.6.0 (2/4): la prueba de verdad, y dos defectos más que ha destapado |
| `febb51d` | 1.6.0 (3/4): **el mutador muta `is` / `is not` (porte de F-034)** |
| `3ceb95b` | 1.6.0 (4/4): entrega — `VERSION`, entrada en la guía y el §5 ampliado |
| `89a9ba9` | 1.6.0: `ruff` ordena los imports de los tres tests de mutación |

Verificado hoy en **solo lectura** (hay otro agente trabajando en `arnes-base`,
así que desde aquí no se escribe una línea en él):

```
$ git -C C:/Users/pgris/PycharmProjects/arnes-base log --oneline 860902e -1
860902e 1.6.0 (1/4): la campana de mutacion deja de poder contar muertos falsos

$ git -C ... branch -r --contains 89a9ba9
  origin/main

$ grep -n "ARNES_VERSION=" arnes-base/harness/VERSION
6:ARNES_VERSION=1.6.0

$ grep -c "ast.Is" arnes-base/harness/mutacion.py
2
```

Las dos entradas de `ast.Is` son las de `COMPARACIONES` que añade F-034: el
porte está dentro. **R18–R21 cumplidos.** La desviación respecto a la letra de
T12 (`mutacion.py` y el test no viajan byte a byte, porque allí conviven con el
encargo de línea base y el test de R14 se generalizó) ya la verificó y la
aceptó el reviewer: «adaptación correcta y mejor que la copia literal».

### 2. La propagación de vuelta a `albaranes`: hecha, y REVERTIDA a propósito

Cerrada la 1.6.0 en `arnes-base`, se propagó de vuelta a `albaranes` **dentro
de esta rama** (commit `e97f9b9`). Fue un error de encaje, no de contenido: esa
propagación mete **~1.000 líneas de producción ajenas a F-034** (`mutacion.py`
+1037, `mutacion_paralela.py` +107, más dos ficheros de test) en el **alcance
de la feature**, y las puertas ya se habían medido antes. El resultado fue
exactamente lo que rechazó el review:

| Puerta | Lo que declara el informe | Lo que medía la rama con `e97f9b9` |
|---|---|---|
| Alcance de mutación | 56 líneas, 19 mutantes | 1.057 líneas, 172 mutantes |
| Cobertura de líneas cambiadas | 12 líneas | 392 líneas |

Y además dejaba la campaña **irreproducible**: la 1.6.0 comprueba la línea base
antes de juzgar, así que el método documentado en el aviso de
`progress/mutacion_F-034.md` abortaba con `LÍNEA BASE EN ROJO` (por el mismo
defecto del ejecutor de la raíz que §T11 midió, que ahora la herramienta
detecta en vez de tragarse).

**El commit `e97f9b9` se ha revertido** (`163846b`). La rama recupera su alcance
real, y **CR-1 y CR-2 quedan cerrados por construcción**, no por un parche.
La propagación **se rehará después del merge de F-034, en su propia rama
`chore/`** — no aquí.

**Incoherencia consciente que se deja en pie**: `harness/VERSION` de
`albaranes` dice `ARNES_VERSION=1.6.0` (lo puso T10, y es correcto: F-034 *es*
la 1.6.0) mientras el código de `harness/mutacion.py` es el de la 1.5.2 más el
cambio de F-034. Lo cuadra la rama de propagación. **No se toca aquí.**

### 3. Verificación de que este informe y el de mutación siguen siendo válidos

No basta con que me lo digan: lo he recalculado tras el revert. Cálculo puro,
sin ejecutar ninguna suite (`harness.alcance.alcance_de_feature` +
`harness.mutacion.generar_mutantes`, leyendo cada fichero en el tip de la rama
con `git show`; el script vive en el scratchpad, no en el repositorio):

```
harness/mutacion.py: 56 lineas, 19 mutantes
TOTAL: 1 fichero(s), 56 lineas, 19 mutantes
```

**Coincide al pie de la letra con la sección «Alcance» de
`progress/mutacion_F-034.md`** (56 líneas) y con sus totales (19 generados).

Y el método documentado en el aviso de ese informe **vuelve a reproducirse**.
Comprobado con una muestra, para no pagar los 111 s enteros:

```python
main(["--feature", "F-034", "--workers", "1",
      "--max-mutantes", "3", "--semilla", "7", "--salida", "<scratchpad>"],
     ejecutor=EjecutorPytest(raiz=".",
         argumentos=["tests", "-x", "-q", "--tb=no", "-p", "no:cacheprovider"]))
```

```
F-034: 1 fichero(s), 56 línea(s) de producción (origen rama, 28971321108528484c52c5c91108afc02af59084..feature/F-034-mutacion-is-y-coherencia-evals)
[1/3] muerto        harness/mutacion.py:220 [aritmetico] anterior = bruta[ini - 1 : ini] if ini > 0 else b"" -> anterior = bruta[ini + 1 : ini] if ini > 0 else b""
[3/3] muerto        harness/mutacion.py:246 [comparacion] while posicion != -1: -> while posicion == -1:
3 mutantes evaluados, 3 muertos, 0 supervivientes, 0 timeouts en 82.7 s
```

No aborta, juzga con la suite de la raíz de verdad y los mutantes son mutantes
reales del alcance de F-034. `git status` limpio después. Este mismo párrafo
está copiado en `progress/mutacion_F-034.md`, que es donde lo va a buscar quien
dude del informe.

### 4. Los cinco cambios requeridos del review, uno a uno

| CR | Estado | Cómo se cierra |
|---|---|---|
| **CR-1** alcance obsoleto de la campaña | cerrado | Revert de `e97f9b9`. Alcance recalculado: 56 líneas / 19 mutantes = lo declarado |
| **CR-2** campaña irreproducible | cerrado | El mismo revert repone el `mutacion.py` sin línea base; método reproducido arriba con una muestra de 3 |
| **CR-3** `tasks.md` no refleja T12 | cerrado | T12 pasa a `[x]` con la tabla de commits de `arnes-base` y la desviación aceptada |
| **CR-4** `current.md` desactualizado | cerrado | Sección reescrita al estado real (T12 resuelto, propagación revertida, F-038) |
| **CR-5** informe da la feature por no cerrable | cerrado | Nota de cierre en §T12, este §T15, y corregidas las secciones «Desviaciones» y «Verificaciones MANUAL pendientes» |

### 5. Las observaciones que NO bloqueaban

1. **`[ADAPTAR]` en `design.md` es un falso positivo de `init.sh`** — la marca
   aparece dentro de una frase que *habla* de una marca ya resuelta. El
   reviewer lo confirmó y propone que la comprobación ignore lo que va entre
   comillas invertidas. **La acepto como buena, pero NO la aplico aquí**:
   tocar `harness/init.sh` en esta rama es exactamente el error que acabamos de
   revertir (meter arnés genérico en el alcance de F-034), y además la mejora
   es del arnés, así que su sitio es `arnes-base` y de ahí a todos. Queda
   propuesta por escrito; no la implemento en F-034.
2. **`e97f9b9` no llevaba formato `F-034 Tn:`** siendo materialmente T12.
   Cierto. **Sin efecto**: ese commit está revertido y el trabajo que
   describía no pertenece a esta rama. La correspondencia tarea↔commit de C5
   ya no lo incluye.
3. **T7 se extendió** más allá de su letra. El reviewer la califica de
   correcta. **Se mantiene tal cual**, sin cambios.

Y la **automejora del protocolo** que propone el review —que el informe de
mutación declare el SHA de HEAD contra el que se midió, y que el reviewer
compruebe que el alcance recalculado coincide— es, en mi opinión, la lección
más valiosa de este ciclo: es la comprobación que he hecho en el punto 3 de
esta sección y habría saltado sola. **No la aplico en esta rama** por lo mismo
que la observación 1: toca `CHECKPOINTS.md` y `.claude/agents/reviewer.md`, es
arnés genérico, y su sitio es `arnes-base` con propagación posterior. La dejo
propuesta para que el humano decida si abre feature.

---

## Evidencias

| Evidencia | Valor real medido |
|---|---|
| **Tests ejecutados y resultado** | Suite de la raíz: **277 passed**, 0 failed. Suite de sv6: **111 passed**, 0 failed. Resto de servicios en verde por caché (árbol sin cambios). Tests nuevos: **9** en `tests/test_mutacion_operadores.py` + **1** en `services/albaran-valoracion-persist/tests/test_f019_r8_r15_precedencia.py` |
| **Cobertura de las líneas cambiadas** | **100,0 %** (12/12 líneas, umbral 80 %, nivel `estandar`) — línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados y supervivientes** | F-034: **19 generados, 18 muertos, 1 superviviente**, analizado y cerrado como equivalente (`progress/mutacion_F-034.md`). Ojo: el CLI a secas da 19/19 falsos, ver §T11 |
| **Tiempo de ejecución de la suite** | Raíz **63,18 s**; sv6 **2,87 s**; campaña de mutación de F-034 **111,0 s** |

Evidencias adicionales de esta feature, que son su razón de ser:

| Campaña | Antes (arnés 1.5.2) | Después (1.6.0) |
|---|---|---|
| **F-027** | 0 mutantes | **1** generado, **1 muerto**, 0 supervivientes (2,5 s) |
| **F-019** | 31 mutantes, 28 muertos, 3 supervivientes | **49** generados, **46 muertos**, **3** supervivientes (los mismos 3, ya analizados) — 331,5 s |

### Re-verificación de las Evidencias tras el revert (2026-08-19, al atender el review)

Las cuatro filas de arriba se midieron antes del episodio de §T15 punto 2. Tras
revertir la propagación, **vuelven a ser exactas**. Comprobado ejecutando, no
leyendo:

```
$ bash harness/init.sh
    38 features, 32 abiertas, en curso: ['F-034'], bloqueadas: ninguna
277 passed in 68.00s (0:01:07)
[OK] pytest en verde (con medición de cobertura)
[OK] servicio sv6-valoracion-persist (...): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 100.0% de 12 líneas cambiadas cubiertas (12/12, umbral 80%, nivel estandar)
[OK] PUERTA RUTAS SENSIBLES [evals]: N/A (F-034 no toca ninguna ruta sensible declarada)
[OK] Rama actual: feature/F-034-mutacion-is-y-coherencia-evals
ENTORNO LISTO. Puedes trabajar.
```

- **Cobertura**: `100.0% de 12 líneas cambiadas` — las **12** que declara la
  tabla, no las 392 que medía la rama con `e97f9b9`. Coincide.
- **Mutación**: alcance recalculado **56 líneas / 19 mutantes**, idéntico al
  informe (§T15 punto 3).
- **Tests**: 277 en la raíz, 0 fallos. El tiempo de la suite sube de 63,18 s a
  **68,00 s** entre las dos ejecuciones; es ruido de máquina, no un cambio.
- Los avisos siguen siendo los de siempre y ninguno lo introduce esta feature:
  1.102 de `ruff` (deuda previa), sv1-email e infra sin tests, y las marcas
  `[ADAPTAR]` de las specs de F-034 (falso positivo, §T13-T14) y F-035.
- El backlog pasa de 34 a **38 features** porque entre medias se dieron de alta
  F-035 a F-038. Ninguna toca esta rama salvo F-038, que solo añade su entrada.

## Desviaciones respecto a la spec, todas justificadas

1. **T12 (porte a `arnes-base`): el implementer paró, y lo resolvió el humano.**
   Durante la sesión estaba **BLOQUEADO** por otro trabajo en vuelo sobre el
   mismo fichero (motivo completo en §T12, que se conserva como registro). **Ya
   no lo está**: la 1.6.0 de `arnes-base` absorbió los dos encargos y lleva el
   porte dentro (commits `860902e`, `b7dce9d`, `febb51d`, `3ceb95b`, `89a9ba9`,
   pusheados). **R18 cumplido y T12 en `[x]`.** Desenlace en §T15.
2. **T11 relanzado con un ejecutor distinto** del comando de `tasks.md`, porque
   ese comando produce un falso verde aquí (§T11). El comando de `tasks.md` no
   es incorrecto en general: lo es para un alcance que cae en la raíz.
3. **Un superviviente NUEVO en la campaña de F-019** (R11), cerrado con un test
   nuevo en sv6 y **cero líneas de producción tocadas**, como manda la spec.
4. **T7 extendido** a los otros cuatro informes de mutación con una línea cada
   uno (§T7). D1 lo pide («anotar pase lo que pase»); T7 solo nombraba dos.
5. **El test de R14 se salta** en un repositorio sin `harness/rutas_sensibles.json`
   (`pytest.skip`), para que el fichero pueda viajar byte a byte a `arnes-base`
   como exige T12 sin poner roja su suite.

## Verificaciones MANUAL pendientes

**Ninguna.** Los nueve requisitos de G1 y el de R14 son tests puros.

Las **dos decisiones de §T12** que esta sección declaraba pendientes (orden de
aterrizaje en `arnes-base` y numeración 1.5.3 / 1.6.0) **ya están tomadas por
el humano**: una sola versión, la **1.6.0**, con los dos encargos dentro. Ver
§T15. **Nada bloquea el cierre de F-034.**

Lo único que queda apuntado, y **no bloquea porque no es de esta feature**:

1. **Rehacer la propagación de la 1.6.0 a `albaranes`** en su propia rama
   `chore/`, después del merge de F-034. Hasta entonces `harness/VERSION` dice
   1.6.0 con el código de la 1.5.2 (§T15, punto 2). Es a propósito.
2. **F-038** recoge el defecto del ejecutor de mutación de la raíz (§T11), que
   invalida `progress/mutacion_F-012.md`.
3. Dos mejoras del arnés propuestas y **no aplicadas aquí a propósito**, porque
   su sitio es `arnes-base`: que `init.sh` ignore las marcas `[ADAPTAR]` entre
   comillas invertidas, y que el informe de mutación declare el SHA de HEAD
   contra el que se midió (§T15, punto 5).

### Confirmación de por qué §T12 paró — y qué pasó luego

`git -C C:/Users/pgris/PycharmProjects/arnes-base status --short` en el último
minuto de la sesión de implementación:

```
 M arnes-base/harness/init.sh
 M arnes-base/harness/mutacion.py
 M arnes-base/harness/mutacion_paralela.py
?? arnes-base/tests/test_mutacion_linea_base.py
```

Al fichero de test **nuevo y sin versionar** —`test_mutacion_linea_base.py`, que
es el test de la línea base— no lo escribió el implementer, y no estaba cuando
empezó la sesión. **Había alguien trabajando ahí en ese momento.** Confirma el
diagnóstico de §T12 y confirma que parar era lo correcto: ese trabajo terminó
commiteado como parte de la 1.6.0 (`860902e`, `b7dce9d`), junto al porte de
F-034 (`febb51d`). Si el implementer hubiera forzado el porte, lo habría
destruido.
