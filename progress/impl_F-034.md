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
