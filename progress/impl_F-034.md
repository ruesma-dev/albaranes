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
