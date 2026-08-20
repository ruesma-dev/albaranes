<!-- progress/mutacion_maquinaria_paralela_F-039.md -->
# F-039 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-039` el 2026-08-20 22:44.

> ## CÓMO SE REPRODUCE, Y QUÉ MIDE EXACTAMENTE
>
> ```bash
> python -m harness.mutacion --feature F-039 \
>   --ficheros harness/mutacion.py,harness/mutacion_paralela.py,harness/rigor.py \
>   --workers 1 --timeout 400 \
>   --salida progress/mutacion_maquinaria_paralela_F-039.md
> ```
>
> **Esta campaña mide OTRO código que `progress/mutacion_F-012.md`.** No es
> aquella campaña rehecha, no repone sus números y **no es comparable con
> ellos**. F-012 midió `harness/mutacion.py` tal como estaba en agosto; desde
> entonces ese fichero ha crecido más de mil líneas. Lo que se mide aquí es si
> está protegido **el código que corre hoy**, sobre `HEAD` de la rama de F-039
> y con los tres ficheros del alcance **enteros, en su versión actual**. El
> `⚠ CAMPAÑA NO VÁLIDA` de `mutacion_F-012.md` **no se retira** por esto.
>
> Los 20 mutantes salen del muestreo del nivel `estandar` (20 de 417, semilla
> `20260820`): con los tres ficheros enteros —2.742 líneas— la campaña completa
> no cabe en una sesión, y la semilla fija hace que dos personas obtengan
> exactamente los mismos 20.
>
> **Por qué `--workers 1`**: la campaña paralela sigue sin verificar en esta
> máquina (R8/R9, verificación MANUAL pendiente del humano en
> `progress/verificacion_paralela_F-039.md`). Medir con maquinaria sin
> verificar sería medir dos veces mal.
>
> **Por qué `--timeout 400` y no el 120 de `harness/rigor.json`**: las dos
> primeras pasadas de esta campaña se invalidaron solas —y con razón— porque
> otra sesión estaba corriendo **una campaña de mutación en paralelo de
> `datamart-seg-anual`** en esta misma máquina. La suite de la raíz seguía
> **verde** (409 passed), pero pasó de 51 s a 149 s y ya no cabía en el
> timeout. El detalle, con las dos salidas y el diagnóstico, está en
> `progress/impl_F-039.md`. El 400 no cambia ni un mutante del muestreo: solo
> da aire al reloj.
>
> **Ojo si repites la campaña**: `escribir_informe` conserva los análisis de
> los supervivientes, pero **no esta cabecera**. Vuélvela a pegar.

## Alcance

Origen del diff: **ficheros** (alcance declarado en la orden).

| Fichero | Líneas en alcance |
|---|---|
| `harness/mutacion.py` | 1932 |
| `harness/mutacion_paralela.py` | 541 |
| `harness/rigor.py` | 269 |
| **Total** | **2742** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 417 |
| Mutantes evaluados | 20 |
| Muertos | 13 |
| Supervivientes | 7 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 838.7 s |
| SHA de HEAD medido | `b0761e85d998ac1440173e6e1332c637157cb87a` |
| Línea base (s) — `.` | 57.1 |
| Media por mutante evaluado (s) | 41.9 |
| Muestreo | sí — 20 de 417 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `harness/mutacion.py:1282` [logico]

- Original: `fallidos = ", ".join(resultado.fallidos()) or f"código {resultado.codigo}"`
- Mutado:   `fallidos = ", ".join(resultado.fallidos()) and f"código {resultado.codigo}"`

#### Análisis

**Hueco de test** (grupo B: el informe solo se prueba por su camino feliz).

`_base_rota_al_final` **no tiene ni un test**: `grep -rn "_base_rota_al_final"
tests/` no devuelve nada. Es la comprobación que vuelve a correr la línea base
al cerrar la campaña, y su mensaje es lo único que ve quien lee un informe
inválido. Con `and`, el mensaje pasa a decir `código N` cuando pytest **sí**
nombra tests caídos —justo la información que hace falta— y cadena vacía
cuando no los nombra.

Test que falta: dar a `_base_rota_al_final` un ejecutor falso cuya línea base
salga roja, con y sin `FAILED` en la salida, y comprobar que el aviso nombra
los tests en el primer caso y el código de salida en el segundo.

Esta campaña lo vivió: sus dos primeras pasadas murieron aquí y el aviso decía
`(código -1)`. Ver la nota de `progress/impl_F-039.md` sobre `expirado`.

### 2. `harness/mutacion.py:1348` [logico]

- Original: `elif linea.startswith("- Mutado:") and mutado is None:`
- Mutado:   `elif linea.startswith("- Mutado:") or mutado is None:`

#### Análisis

**Mutante equivalente**, y se justifica recorriendo el bucle.

La condición vive en una cadena `if/elif` que recorre el bloque de un
superviviente. Para **todo informe escrito por `escribir_informe`** —la única
entrada real de `analisis_escritos`, que solo lee informes anteriores— el
orden es fijo: `### cabecera`, línea en blanco, `- Original: \`x\``,
`- Mutado:   \`y\``, línea en blanco, `#### Análisis`.

Con `or`, la rama se toma también en las líneas en blanco previas mientras
`mutado is None`; su cuerpo hace `mutado = ... if "\`" in linea else None`, así
que una línea sin backticks deja `mutado` en `None` y el estado no cambia. La
línea `- Original:` la captura el `if` anterior, que se evalúa primero. Y
cuando llega `- Mutado:`, ambas versiones asignan lo mismo.

El único camino en el que difieren es un bloque **sin** `- Mutado:` válido: el
original recogería el análisis y lo descartaría después en
`if analisis and original is not None and mutado is not None`; el mutante ni
lo recoge. **Mismo resultado observable**: no se repone análisis.

No se escribe test: no hay comportamiento distinto que fijar.

### 3. `harness/mutacion.py:1539` [aritmetico]

- Original: `lineas += ["## Timeouts", ""]`
- Mutado:   `lineas -= ["## Timeouts", ""]`

#### Análisis

**Hueco de test** (grupo B: el informe solo se prueba por su camino feliz).

`lineas -= [...]` sobre una lista es un `TypeError` en cuanto se ejecuta, así
que este mutante **revienta `escribir_informe`** para cualquier campaña con
timeouts. Sobrevive porque **ningún test escribe un informe que tenga
timeouts**: `timeouts=` solo aparece en
`tests/test_f012_r3_r4_reparto_agregacion.py`, que prueba la AGREGACIÓN de
informes parciales, no su escritura.

Test que falta: `escribir_informe` de un `InformeMutacion` con al menos un
mutante en `timeouts` y otro en `base_rota`, comprobando que salen sus dos
secciones. Cubre de paso el mismo hueco en el bloque de `base_rota`.

### 4. `harness/mutacion.py:1688` [entero]

- Original: `return 0`
- Mutado:   `return 1`

#### Análisis

**Hueco de test** (grupo A: el CLI de `harness.mutacion` no se ejercita de
punta a punta).

Es el código de salida de `--restaurar` cuando **no hay centinela**: 0 («nada
que restaurar») pasaría a 1. Los tests cubren `restaurar_desde_centinela` por
dentro (`tests/test_mutacion_linea_base.py`), pero nadie llama a
`main(["--restaurar"])` ni comprueba lo que devuelve. `harness/init.sh` sí
mira el código de `--estado`, no el de `--restaurar`.

Test que falta: `main(["--restaurar", "--raiz", str(tmp_repo)]) == 0` sobre un
árbol sin centinela, y `== 0` tras restaurar uno de verdad, y `== 2` cuando
queda un fichero irrecuperable.

### 5. `harness/mutacion.py:1807` [comparacion]

- Original: `if Centinela.leer(opciones.raiz) is not None:`
- Mutado:   `if Centinela.leer(opciones.raiz) is None:`

#### Análisis

**Hueco de test** (grupo A: el CLI de `harness.mutacion` no se ejercita de
punta a punta). **Es el más serio de los siete.**

Invertida, la guarda hace exactamente lo contrario de lo que dice su
comentario: restaura cuando NO hay nada que restaurar y **arranca la campaña
encima del mutante que dejó escrito una campaña anterior muerta a machetazos**.
Es decir, mediría el mutante viejo y llamaría a eso «el código». Sobrevive
porque ningún test arranca `main` con un centinela sucio en disco.

Test que falta: dejar un centinela con un mutante aplicado en un repositorio de
`tmp_path`, llamar a `main` con `--ficheros` y un ejecutor falso, y comprobar
que el fichero vuelve a su contenido original **antes** de que la campaña
empiece.

### 6. `harness/mutacion_paralela.py:257` [entero]

- Original: `if codigo != 0:`
- Mutado:   `if codigo != 1:`

#### Análisis

**Hueco de test** (grupo E: la limpieza de worktrees solo se prueba cuando
`git worktree remove` funciona).

Está en el respaldo de `_retirar`: si `git worktree remove --force` falla
—en Windows, un proceso rezagado con un fichero abierto—, se borra el
directorio a mano y se hace `worktree prune`. Con `!= 1`, ese respaldo se
ejecuta cuando la retirada **fue bien** (inofensivo: `rmtree` con
`ignore_errors` sobre un directorio que ya no está, más un `prune` que no
encuentra nada) y **se salta cuando falla**, que es el único caso para el que
existe. Los tests de F-012 comprueban `git worktree list` con una sola línea
tras la campaña, pero siempre por el camino en que la retirada funciona.

Test que falta: forzar el fallo de `git worktree remove` —por ejemplo,
sustituyendo el `_git` del módulo por uno que devuelva código ≠ 0 para
`worktree remove`— y comprobar que el directorio del worktree acaba borrado y
desregistrado igualmente.

### 7. `harness/rigor.py:118` [logico]

- Original: `if not isinstance(valor, int) or valor <= 0:`
- Mutado:   `if not isinstance(valor, int) and valor <= 0:`

#### Análisis

**Hueco de test** (grupo D: las validaciones de `rigor.py` comprueban el tipo,
pero no el rango).

Con `and`, un `timeout_por_mutante_s` **entero pero no positivo** (`0`, `-30`)
deja de ser un error de configuración y se devuelve tal cual. Consecuencia
real: `subprocess.run(timeout=0)` hace expirar **todos** los mutantes, y la
campaña entera sale «timeout» sin que nadie entienda por qué. Sobrevive porque
ningún test le pasa a `timeout_mutacion` un entero no positivo: `grep -rn
"timeout_mutacion" tests/` no devuelve nada.

Test que falta: `timeout_mutacion({"mutacion": {"timeout_por_mutante_s": 0}})`
y con `-1` deben lanzar `ValueError`, igual que ya se exige para el tipo.
Mismo test para `max_mutantes_nivel` y para el umbral de cobertura, que
validan igual.

