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

## Desviaciones respecto a la spec, todas justificadas

1. **T12 (porte a `arnes-base`) NO se ha hecho: BLOQUEADO.** Motivo completo en
   §T12. No hay ningún commit mío en `arnes-base` y por eso este informe no trae
   hashes de allí: no los hay. **La feature no puede cerrarse sin esto** (R18).
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

Ninguna propia de F-034: sus nueve requisitos de G1 y el de R14 son tests puros.
Lo que queda pendiente **del humano** son las **dos decisiones de §T12** (orden
de aterrizaje en `arnes-base` y numeración 1.5.3 / 1.6.0), sin las cuales la
feature no puede cerrarse.

### Confirmación final (al cerrar la sesión)

`git -C C:/Users/pgris/PycharmProjects/arnes-base status --short` en el último
minuto de la sesión:

```
 M arnes-base/harness/init.sh
 M arnes-base/harness/mutacion.py
 M arnes-base/harness/mutacion_paralela.py
?? arnes-base/tests/test_mutacion_linea_base.py
```

Al fichero de test **nuevo y sin versionar** —`test_mutacion_linea_base.py`, que
es el test del 1.5.3 de la línea base— no lo he escrito yo, y no estaba cuando
empezó la sesión. **Hay alguien trabajando ahí ahora mismo.** Confirma el
diagnóstico de §T12 y confirma que parar era lo correcto.
