<!-- progress/impl_F-040_porte_1.7.2.md -->
# F-040 · P1: porte a `arnes-base` 1.7.2

Regla de propagación del `CLAUDE.md`. Origen: `albaranes` en `dev`, merge
`1167534`. Destino: `arnes-base` en `main`, que estaba en **1.7.1** y queda en
**1.7.2**. Cinco commits locales, **sin `git push`**. `albaranes` no se ha
tocado salvo este informe (`git status` limpio antes y después).

## Cómo se hizo el porte (y por qué así)

Antes de aplicar nada se comparó el 1.7.1 con el estado de `albaranes`
**anterior** a F-040 (`2ccb8ac`), no con el actual: era la única forma de saber
qué es porte y qué es divergencia previa. Los cuatro ficheros de código eran
idénticos salvo dos cosas, ambas **de `arnes-base` y conservadas**:

1. `mutacion.py`: `arnes-base` lleva el bloque `PYTHONDONTWRITEBYTECODE=1` (la
   1.6.3, venida de `postventa-incidencias`) que `albaranes` **no** tiene. De
   ahí que los 25 *hunks* entraran con offset +13.
2. El comentario de `FILAS_DE_RELOJ` está genérico en `arnes-base` («un test de
   paridad serie/paralelo», «una versión posterior») donde `albaranes` nombra
   F-012 y F-038. Ese único *hunk* falló y se integró **a mano**, conservando la
   redacción del destino y añadiendo encima lo de F-040.

`CHECKPOINTS.md` sí había divergido de verdad, y ahí el porte **no fue copiar**
(ver «Desviaciones», punto 1).

## Qué entró, punto por punto del encargo

| Punto | Qué se portó | Dónde |
|---|---|---|
| **D1** | `MARGEN_TIMEOUT = 2.0` y `FACTOR_HOLGURA_BASE = 5` **en el código**, `timeout_derivado`, `timeout_de_linea_base`, `comprobar_linea_base(..., workers=)`, `mensaje_base_expirada_al_arrancar`, `ejecutar_campania(timeout_base_s, timeout_fijado, workers)`, y la línea base de cierre con el timeout de base | `harness/mutacion.py` |
| **D2** | `TOPE_WORKERS` 16 → **4** y `workers_por_defecto` con `(núcleos - 2) // 2`, con el argumento de recurso en el docstring. `mutacion.workers` **sigue sin declararse** en `rigor.json` | `harness/mutacion.py`, `harness/rigor.json` |
| **D3** | `_base_rota_al_final` distingue **expirada** de **fallida**; `mensaje_base_expirada_al_final` dice que la suite **no falló** y manda bajar workers o subir el suelo | `harness/mutacion.py` |
| **D4** | `NADA_JUZGADO = 3` y las dos guardas en el **embudo** (`main`): alcance vacío y cero mutantes generados. La guarda de entrada de `alcance_de_ficheros` (1.7.1, código 2) **se queda** | `harness/mutacion.py` |
| **D5** | Rango de `timeout_por_mutante_s` **con el booleano rechazado** y mensajes separados; `--timeout <= 0` y `--workers < 1` con código 2; sección `## Timeouts` sin duplicar `fichero:línea`; respaldo `rmtree` + `prune`; `main` deja de tirar el código de `_modo_restaurar` | `harness/rigor.py`, `harness/mutacion.py`, `harness/mutacion_paralela.py` |
| **R27** | RM2 corregido (ver «Desviaciones» 1) | `CHECKPOINTS.md` |
| **Tests** | Los tres ficheros, renombrados a la nomenclatura temática del destino | `tests/test_mutacion_{dimensionado,honestidad,huecos}.py` |
| **Versión** | `ARNES_VERSION=1.7.2` y entrada nueva en la guía, con los dos avisos y el defecto conocido | `harness/VERSION`, `GUIA_INSTALACION.md` |

También entraron, por arrastre: las filas nuevas del informe (timeout efectivo,
suelo, workers), `FILAS_DE_RELOJ` ampliada con las dos que dependen del reloj,
la propagación de `timeout_base_s`/`timeout_fijado`/`workers` a la campaña
paralela y `fusionar(workers=)` con el máximo de los parciales.

**No se portó nada específico de `albaranes`**: ni el inventario de campañas,
ni los informes, ni cabeceras. `harness/features.json` del destino, intacto.

## Fase RED

El código estaba ya aplicado cuando se copiaron los tests, así que la fase RED
se produjo **a propósito y midiéndola**: se revirtieron los cinco ficheros a
`HEAD` (1.7.1), se lanzaron los tres ficheros nuevos contra ese código y se
restauró el porte después. Comandos exactos y salida real.

`python -m pytest tests/test_mutacion_dimensionado.py tests/test_mutacion_honestidad.py tests/test_mutacion_huecos.py -q --no-header -p no:cacheprovider`:

```
tests\test_mutacion_dimensionado.py:31: in <module>
    from harness.mutacion import (
E   ImportError: cannot import name 'FACTOR_HOLGURA_BASE' from 'harness.mutacion'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.25s
```

Los 41 tests del dimensionado ni se recogen: sobre el 1.7.1 no existen ni las
constantes ni las dos funciones. Sin ese fichero, los otros dos
(`python -m pytest tests/test_mutacion_honestidad.py tests/test_mutacion_huecos.py -q --no-header -p no:cacheprovider --tb=line`):

```
25 failed, 35 passed in 0.69s
```

Con las causas reales, una por defecto portado:

```
honestidad.py:125: AssertionError: assert ('no falló' in 'La línea base estaba VERDE al
   empezar y ROJA al terminar en wk_0 (código -1). ... Arregla la suite y repite la campaña.'
honestidad.py:136: AssertionError: el aviso tiene que decir cuánto tiempo se concedió
honestidad.py:186: AssertionError: fichero:línea duplicado en la fila de timeouts:
   '- `harness/mutacion.py:42` harness/mutacion.py:42 [comparacion] a == b -> a != b'
honestidad.py:234: AssertionError: con el alcance vacío no se arranca ni una línea base:
   el aborto va antes de tocar nada
honestidad.py:334: assert 0 == 3
honestidad.py:453: AssertionError: RM2 tiene que dar la corrección: el coste real por
   mutante es media × W
huecos.py:53: Failed: DID NOT RAISE ValueError        (el booleano colaba como entero)
huecos.py:67: assert 'no vale' in "Falta 'mutacion.timeout_por_mutante_s' en la
   configuración de rigor."
```

Ese `assert 0 == 3` es el defecto que más importa del lote: sobre el 1.7.1 una
campaña de **cero mutantes** salía con **0**, en verde, escribiendo informe.

El `RM2 tiene que dar la corrección` se midió además **aislado**: fue el único
test en rojo tras aplicar todo el código y antes de tocar `CHECKPOINTS.md`
(`1 failed, 262 passed`), lo que confirma que la parte documental del porte no
viajaba de gorra con la de código.

## Verificación final

Las **dos** suites del destino, en verde, con el porte aplicado y el árbol
limpio:

```
python -m pytest tests -q --no-header -p no:cacheprovider
263 passed, 1 skipped in 29.31s

powershell tests_instalador\prueba_instalador.ps1
TODO VERDE: 65 comprobaciones.
```

La 1.7.1 dejaba `153 passed, 1 skipped`: **+110** casos (87 funciones nuevas,
el resto parametrizaciones). El instalador se mantiene clavado en 65, y se
relanzó **después** de subir `VERSION` porque el instalador lo lee.

Comprobado también lo que pedía el encargo: `.coverage` y `coverage.json`
siguen en la lista `excluidos` de `politica_ficheros.json`, sin tocar. Los tres
tests nuevos caen bajo `tests/**`, que ya es `arnes_puro`, así que la política
no necesitaba cambio (si lo hubiera necesitado, el instalador habría abortado
con código 3 por payload sin clasificar; P10 lo prueba).

Humo funcional en el destino, sobre la máquina real de 22 núcleos:

```
nucleos 22 -> workers 4 tope 4          (antes: 16)
timeout_derivado(120, {'wk': 68.3}) = 137     (max(suelo, ceil(68.3 × 2.0)))
timeout_derivado(120, {'wk': 10.0}) = 120     (el suelo manda)
timeout_de_linea_base(120) = 600
python -m harness.mutacion --feature F-999 --timeout 0   ->  EXIT 2
  «--timeout tiene que ser un entero de segundos mayor que cero, y es 0.»
```

## Desviaciones respecto al encargo

1. **R27 no se pudo copiar: `CHECKPOINTS.md` había divergido y en sentido
   contrario.** `arnes-base` ya traía dos párrafos sobre workers que
   `albaranes` no tiene: uno correcto (la regla del coste por mutante,
   `Tiempo total × W ÷ mutantes`) y **uno equivocado**, que mandaba multiplicar
   el «Tiempo total» por W para compararlo con `mutantes × media`. Es
   justamente el error que F-040 identificó: `mutantes × media` **es** el
   Tiempo total por construcción, porque la media es tiempo de pared entre los
   mutantes. Copiar el texto de `albaranes` habría dejado los dos párrafos
   contradiciéndose en el mismo checkbox. Se **sustituyó** el párrafo erróneo
   por el corregido, enganchado con la regla de más arriba («el mismo número de
   la regla del coste por mutante»), y con los dos añadidos que pide R27: el
   coste real es `media × W`, y hay que leer el «Timeout efectivo por mutante
   (s)» antes de comparar tiempos. El test de RM2 portado lo verifica y pasa.
2. **Los tests se renombraron.** `arnes-base` nombra por tema
   (`test_mutacion_linea_base.py`, `test_mutacion_prueba_de_verdad.py`) y sus
   funciones no llevan prefijo `fXXX_rN_`: un `test_f040_r14_...` en un arnés
   genérico apunta a una spec que allí no existe. Se comprobó que al quitar el
   prefijo no había colisiones de nombre (41 + 19 + 27 funciones, cero
   duplicados). Las referencias `F-040` y `(R14)` **dentro** de docstrings y
   comentarios **sí se conservaron**: `arnes-base` ya arrastra `(F-038, R1–R3)`,
   `(R9)` y `(R11)` de portes anteriores, y son la única traza de por qué el
   código es como es.
3. **Un test previo del destino, adaptado.** `test_mutacion_alcance_por_ficheros.py`
   usaba un doble que devolvía un informe de **cero mutantes en verde**, que es
   lo que la guarda nueva prohíbe. Se le pone un recuento real (`generados=5`)
   con el motivo escrito: su sujeto era **qué alcance** recibió la campaña, no
   el recuento. Mismo cambio que F-040 hizo en `albaranes`, y fue el único fallo
   de la suite del destino al aplicar el código.
4. **Fechas y feature en el texto de la guía y de RM2**: donde `albaranes`
   escribe «desde F-040» o «anteriores al 2026-08-21», en el destino se escribe
   «desde la 1.7.2», que es la referencia que un proyecto instalado puede
   comprobar en su `harness/ARNES_VERSION.md`. La procedencia (`albaranes`,
   F-040) queda declarada al pie de la entrada de la guía, como en la 1.7.1.

## Lo que NO entra, y consta por escrito

El **quinto defecto** (`ResultadoSuite.verde` cuenta `PYTEST_SIN_TESTS = 5`
como verde, así que un mutante sin tests recogidos sale SUPERVIVIENTE en vez de
«no juzgado») **no se ha tocado ni arreglado**. Sí se **menciona** en la entrada
de la guía, en su propia sección, con la consecuencia operativa: mientras viva,
**una campaña de una sola pasada no vale como evidencia sin contraste**. Tiene
ficha F-041 (rigor `critico`) en `albaranes`.

## Commits en `arnes-base` (locales, `main`, sin push)

```
c36ac5c 1.7.2: VERSION y la entrada de la guia, con sus dos avisos
8e7cc6b 1.7.2: los tests del dimensionado, la honestidad y los huecos
2c582a7 1.7.2: RM2 corrige la aritmetica de los workers y manda leer el timeout
d56aa41 1.7.2: la campana se dimensiona sola y deja de mentir sobre lo que ha medido
29969a2 1.7.2: el suelo del timeout se valida, y el booleano deja de valer 1 segundo
```

## Para el humano

1. **Falta el `git push` de `arnes-base`**, que no hacen los agentes. Los cinco
   commits están en local sobre `main`.
2. **Propagar la 1.7.2 a los demás repositorios** es decisión suya: quien tenga
   campañas paralelas que «no terminaban» o salían inválidas, la causa es el
   default de 16 workers y se arregla al actualizar. La guía lleva los pasos.
3. Si algún proyecto declaró `mutacion.workers` en su `rigor.json` para esquivar
   el 16, **hay que borrarla** al actualizar: ahora estorba.
4. **Verificaciones MANUAL pendientes: ninguna.**

## Evidencias

| Evidencia | Valor (medido, no estimado) |
|---|---|
| Tests ejecutados (destino, suite del arnés) | **263 passed, 1 skipped** en 29,31 s. Antes del porte: 153 passed, 1 skipped |
| Tests ejecutados (destino, instalador) | **65 comprobaciones**, TODO VERDE (16 pruebas P1–P16), relanzado tras subir `VERSION` |
| Fase RED | 1 error de recolección + **25 failed, 35 passed** sobre el código 1.7.1; trazas pegadas arriba |
| Cobertura de las líneas cambiadas | **N/A en este porte**: `arnes-base` no tiene `harness/init.sh` gobernando su propio desarrollo (es el payload que se instala en otros), así que no hay puerta `PUERTA COBERTURA` que leer. La cobertura del mismo código en origen fue **100 % (79/79)**, `progress/impl_F-040.md` |
| Mutantes generados y supervivientes | **No se lanzó campaña en el destino.** El código es el mismo que ya midió F-040 en origen —20 evaluados, 17/3 en paralela y 18/2 en serie, los 3 supervivientes analizados— en `progress/mutacion_F-040.md`. Además, con el defecto de F-041 vivo, una campaña de una sola pasada no sería evidencia: repetirla aquí habría costado horas para producir un número que el propio arnés declara no fiable |
| Tiempo de ejecución de la suite | **29,31 s** (destino, 264 casos, sin medición de cobertura) |
| Ruff | `mutacion.py` **8** y `rigor.py` **4**, exactamente los mismos que en origen: el porte no añade ninguno. Los 3 tests nuevos traen 1 `I001` cada uno, **deuda previa del destino y no del porte**: `arnes-base` no declara `harness` como paquete de primera parte, así que sus 9 ficheros de test con imports de `harness` dan el mismo aviso. Se deja como está para no separarlos del resto del repositorio |
