<!-- progress/review_F-034.md -->
# F-034 · Informe de review

**Veredicto: CHANGES_REQUESTED**

**Rama**: `feature/F-034-mutacion-is-y-coherencia-evals`, HEAD `5e2a2f3`, árbol
limpio. **Revisado**: la feature entera (`git diff dev...HEAD`, 28 ficheros).
**Nivel de rigor**: `estandar` (declarado en `harness/features.json`). Exige
C1–C5, **fase RED**, **cobertura** de las líneas cambiadas y **campaña de
mutación** con los supervivientes analizados. No exige cero supervivientes
(eso es `critico`).

El trabajo del implementer es bueno y su parada en T12 fue correcta. Lo que
rechaza este review no es lo que él hizo: es que el commit `e97f9b9`
(propagación de la 1.6.0, decidida por el humano) metió ~1.000 líneas de
código de producción en esta rama **después** de que se midieran las puertas,
y ni la campaña de mutación ni el cierre documental se rehicieron contra ese
estado. La rama de hoy no es la rama que se midió.

---

## Checkpoints

| | Estado | Nota |
|---|---|---|
| **C1** arnés completo y en verde | `[x]` | `bash harness/init.sh` exit 0, ejecutado tal cual. 302 passed en 101,80 s. Los siete ficheros obligatorios existen. |
| **C2** estado coherente | `[ ]` | Una sola feature `in_progress` y rama correcta, **pero `progress/current.md` está desactualizado** (ver CR-4). |
| **C3** arquitectura y convenciones | `[x]` | Ni una línea de `services/` de producción (solo un test añadido), así que la hexagonal no se toca. Primera línea con ruta verificada en los cinco ficheros nuevos/modificados. Sin secretos (barrido sobre el diff con `password\|secret\|api_key\|token=\|connectionstring\|subscription_id\|tenant_id`: 0 aciertos). Los `print()` del diff son la **CLI** de `harness/mutacion.py`, no debug. |
| **C3 bis** documentos externos | **N/A justificado** | La feature no añade ni modifica nada en `docs/referencia/`. Verificado sobre el diff. |
| **C4** verificación real | `[x]` | R1–R8 y R14 con test trazable `test_f034_rN_*`, los nueve pasan. R11 con test propio. Tests puros: sin red ni BBDD. Sin verificaciones MANUAL propias pendientes. |
| **C4 bis** rigor declarado | `[ ]` | Fase RED y cobertura cumplidas; **la campaña de mutación mide un alcance obsoleto y es irreproducible** (CR-1 y CR-2). |
| **C4 ter** rutas sensibles | **N/A justificado** | `init.sh`: `PUERTA RUTAS SENSIBLES [evals]: N/A (F-034 no toca ninguna ruta sensible declarada)`. La declaración existe, pero el diff no toca ninguna de las 14 rutas. |
| **C5** sesión cerrada | `[ ]` | **T12 sigue en `[~]` y rotulado BLOQUEADO** en `tasks.md` (CR-3). Sin ficheros temporales sospechosos; árbol limpio. |

## Detalle de C4 bis

- **Fase RED** `[x]`. Traza real pegada en `impl_F-034.md` §T2 (`7 failed, 2
  passed`, con R6 y R7 pasando a propósito), **más una segunda fase RED** para
  R5 tras T3 (el mutante cayendo dentro del comentario: `analisis` → `analis
  notis`), **más** la RED del test nuevo de R11. Es más evidencia de la exigible.
- **Cobertura** `[x]`. `PUERTA COBERTURA: 81.9% de 392 líneas cambiadas
  cubiertas (321/392, umbral 80%, nivel estandar)` → `[OK]`.
- **Mutación** `[ ]`. Ver CR-1 y CR-2.
- **Supervivientes analizados** `[x]`. Ningún `PENDIENTE` en los tres informes
  de mutación (`grep` sobre los tres: 0 aciertos).
- **Campaña MANUAL** — N/A: no hubo campaña manual en F-034.
- **Sección «Evidencias»** `[x]`. Presente, con los cuatro números.

## Lo que he verificado ejecutando, no leyendo

**El superviviente declarado equivalente es equivalente de verdad.** El
argumento del implementer (`Pattern.match` anclado, así que `objetivo[:1]` y
`objetivo[:2]` interrogan el mismo byte) se sostiene: `_PARTE_DE_PALABRA =
re.compile(rb"[A-Za-z0-9_\x80-\xff]")` es una clase de **un solo carácter** sin
cuantificador ni anclaje de fin. Prueba exhaustiva sobre todas las cadenas de
bytes de longitud 0 y 1 (los 256 valores) y un barrido amplio de longitud 2 y
3: **0 casos con resultado distinto**. Aceptado.

**R9 — reejecutado entero** (el informe declaraba 2,5 s, por debajo del umbral
de 5 min), con `--salida` al scratchpad y `git status` limpio después:

```
[base] services/albaran-valoracion-persist: en verde
[1/1] muerto  .../valuation_builder.py:1033 [comparacion] if partida_result.derived_line is not None: -> if partida_result.derived_line is None:
1 mutantes evaluados, 1 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto en 4.0 s
```

Coincide al pie de la letra con lo declarado, y es el M1 de la campaña manual
de F-027. La herramienta nueva no miente aquí.

**R10 — recálculo puro** (campaña declarada de 331,5 s, **por encima** del
umbral: campaña **no reejecutada**, y lo digo explícitamente como manda el
protocolo). Recalculado con `harness.alcance` + `generar_mutantes` leyendo cada
fichero en el tip de su rama: **515 líneas, 6 ficheros, 49 mutantes** — coincide
exactamente con el informe. Muestreados dos supervivientes
(`importes.py:72`) y el superviviente nuevo ya cerrado
(`importe_calculator.py:203`): existen como mutantes reales, con el mismo
operador y el mismo texto original→mutado.

**El test nuevo de R11 existe y pasa**
(`test_f019_r15_el_motivo_conserva_el_valor_ilegible_que_llego`, sv6, 1 passed),
y se añadió **sin tocar producción**, como exigía la spec.

**El test de F-012 se reforzó, no se debilitó.** El diff sustituye las
aserciones por su versión sobre el subconjunto de mutantes y **añade**
`assert base, "sin eco de línea base: la campaña no la está comprobando"`. El
eco `[base]` sigue siendo obligatorio. Correcto.

**El porte a `arnes-base` (R18–R21) está hecho y verificado.** Commits
`860902e`, `b7dce9d`, `febb51d`, `3ceb95b`, `89a9ba9`; árbol limpio;
`ARNES_VERSION=1.6.0`, `ARNES_FECHA=2026-08-19`. R19: `diff` de
`harness/mutacion.py` entre los dos repositorios **vacío** (ídem
`mutacion_paralela.py`). R20: `GUIA_INSTALACION.md` trae `## La campaña de
mutación deja de poder mentir, y muta `is` (1.6.0, 2026-08-19)` con el aviso
explícito de que los informes anteriores **no son comparables** y de que una
campaña verde puede volverse roja. `test_mutacion_operadores.py` **no** viaja
byte a byte (el test de R14 se generalizó allí, porque `evals/fixtures/` es de
albaranes): es una adaptación correcta y mejor que la copia literal, aunque se
aparta de la letra de T12. Observación, no defecto.

**El falso verde que documenta §T11 ya no puede ocurrir.** Lancé el CLI a secas
y la 1.6.0 **aborta**: `LÍNEA BASE EN ROJO en .: la suite falla SIN mutar nada.
Campaña abortada sin escribir informe`. La pieza funciona.

## Cobertura requisito → verificación

| Req | Verificación | Estado |
|---|---|---|
| R1, R2 | `test_f034_r1_muta_is_a_is_not`, `test_f034_r2_muta_is_not_a_is` | OK |
| R3 | `test_f034_r3_una_mutacion_por_operador_en_la_misma_linea` | OK |
| R4 | `test_f034_r4_el_operador_declarado_es_comparacion` | OK |
| R5 | `test_f034_r5_no_muta_dentro_de_una_palabra_del_comentario` | OK |
| R6 | `test_f034_r6_los_simbolos_sin_espacios_siguen_mutando` | OK |
| R7 | `test_f034_r7_espaciado_no_canonico_no_genera_mutante_ni_falla` | OK |
| R8 | `test_f034_r8_el_mutante_compila_y_el_ast_lleva_el_operador_contrario` | OK |
| R9 | Campaña F-027 **reejecutada por el reviewer**: 1 mutante, muerto | OK |
| R10 | Campaña F-019, recálculo puro: 49 mutantes, 46 muertos, 3 supervivientes | OK |
| R11 | Superviviente nuevo cerrado con test, cero líneas de producción | OK |
| R12 | Comandos exactos en el informe | **FALLA** para F-034 (CR-2); OK para R9/R10 |
| R13, R15 | `rutas_sensibles.json`, `CHECKPOINTS.md`, `current.md` condicionan a `evals/fixtures/`; las menciones que quedan de `ground_truth` son la aclaración que R15 exige | OK |
| R14 | `test_f034_r14_la_puerta_de_evals_no_se_declara_sobre_lo_no_versionado` | OK |
| R16, R17 | C4 bis de `CHECKPOINTS.md` y punto 4 de `.claude/agents/reviewer.md` exigen fichero, línea, texto exacto original→mutado y nº de fallos | OK |
| R18, R19, R21 | Verificado arriba (`diff` vacío, 1.6.0 en ambos) | OK |
| R20 | Sección de la guía con formato y aviso | OK |

---

## Cambios requeridos

### CR-1 · La campaña de mutación mide un alcance que ya no existe (bloqueante)

`progress/mutacion_F-034.md` declara, en su sección «Alcance»:

| Fichero | Líneas |
|---|---|
| `harness/mutacion.py` | 56 |
| **Total** | **56** |

y **19 mutantes generados**. El alcance de la rama **hoy** es otro. Recalculado
de forma independiente con `harness.alcance.alcance_de_feature('F-034')` y
`harness.mutacion.generar_mutantes`, y confirmado por la propia salida del CLI
(`F-034: 2 fichero(s), 1057 línea(s) de producción`):

| Fichero | Líneas en alcance | Mutantes |
|---|---|---|
| `harness/mutacion.py` | 964 | 158 |
| `harness/mutacion_paralela.py` | 93 | 14 |
| **Total** | **1057** | **172** |

La causa está identificada y no es un descuido del implementer: el commit
`e97f9b9` reemplazó `harness/mutacion.py` (+1037 líneas) y
`harness/mutacion_paralela.py` (+107) desde `arnes-base`, **después** de que se
lanzara la campaña. La misma señal aparece en la puerta de cobertura, que hoy
mide **392** líneas cambiadas donde el informe declaraba **12**.

Consecuencia: **el 89 % del código de producción de esta rama no ha pasado la
puerta de mutación**. C4 bis pide la campaña sobre el alcance de la feature, y
esta no lo es.

Qué hace falta (elegir, con el humano, porque afecta al coste):

1. **Rehacer la campaña completa** sobre los 172 mutantes — honrado, pero caro:
   a ~60 s de suite por mutante son horas, y hoy ni siquiera arranca (CR-2).
2. **Rehacer la campaña muestreada** con `--max-mutantes` y `--semilla` fija, y
   decirlo en el informe (la fila «Muestreo» del informe ya lo contempla). Es
   exactamente la palanca (2) que F-038 propone; adelantarla aquí sería
   coherente.
3. **Acotar el alcance**: si el humano considera que el código propagado desde
   `arnes-base` ya viene medido por su propia campaña allí y por los 792 líneas
   de test que lo acompañan (`test_mutacion_linea_base.py`,
   `test_mutacion_prueba_de_verdad.py`), eso puede valer — pero **tiene que
   quedar escrito** en el informe de mutación como exclusión razonada, no
   quedarse en un informe que declara 56 líneas sin decir que hay 1057.

Cualquiera de las tres cierra el punto. Lo que no puede quedarse es el informe
actual, que describe un árbol que ya no es este.

### CR-2 · La campaña de F-034 es irreproducible: el método que documenta hoy aborta (bloqueante)

El aviso al reviewer de `progress/mutacion_F-034.md` dice que los números
buenos salen de pasar el ejecutor por API:

```python
main(["--feature","F-034","--workers","1","--salida","progress/mutacion_F-034.md"],
     ejecutor=EjecutorPytest(raiz=".", argumentos=["tests","-x","-q","--tb=no","-p","no:cacheprovider"]))
```

Lo ejecuté tal cual (con `--max-mutantes 4 --semilla 7` y salida al scratchpad).
**No reproduce nada: aborta.**

```
LÍNEA BASE EN ROJO en .: la suite falla SIN mutar nada.
Campaña abortada sin escribir informe: sobre una base roja TODO mutante saldría
«muerto» y el cero de supervivientes sería falso.
  Tests que fallan sin mutar:
    - services/albaran-valoracion-persist/tests/test_f019_r8_r15_precedencia.py
    - services/albaranes-api/tests/test_f002_obras_cache.py
    ... (9 ficheros de tests de servicios)
```

El `ejecutor` pasado por `main(...)` **no llega a la comprobación de línea
base**, que sigue invocando `pytest` sin ruta desde la raíz y recogiendo
`services/**/tests`. Es la misma causa raíz que el implementer midió en §T11,
solo que ahora la 1.6.0 la detecta y para en vez de mentir — lo cual es bueno,
pero deja la campaña de esta feature sin forma de repetirse.

R12 exige comandos exactos «de forma que el reviewer pueda repetir las campañas
sin adivinar nada». Para F-034 no se cumple. Hace falta un procedimiento que
**funcione hoy**: o se arregla el ejecutor de raíz (dar a la raíz configuración
de pytest con `testpaths`, o que `ejecutor_para` use `tests` como ruta para los
ficheros que no caen en ningún servicio), o se documenta la vía que sí
reproduzca. Nótese que CR-1 depende de esto: sin base verde no hay campaña que
rehacer.

Esto es infraestructura del arnés y afecta a todas las features (también a
`progress/mutacion_F-012.md`, medido con la invocación rota). Si el humano
prefiere sacarlo a una feature propia, es razonable — pero entonces F-034 no
puede cerrar declarando su puerta de mutación cumplida.

### CR-3 · `tasks.md` no refleja el estado real de T12 (bloqueante, C5)

`specs/F-034-mutacion-is-y-coherencia-evals/tasks.md:100` sigue así:

```
- [~] **T12: Porte a `arnes-base` — BLOQUEADO (ver progress/impl_F-034.md §T12)**
```

El porte **está hecho y lo he verificado**. El commit de desbloqueo `5e2a2f3`
solo tocó `BACKLOG.md` y `harness/features.json`. C5 exige todas las tareas en
`[x]`. Marcar T12 `[x]` y anotar cómo se resolvió (la 1.6.0 de `arnes-base`
absorbió el porte junto al encargo de mutación fiable; commits `860902e`..
`89a9ba9`, propagados aquí en `e97f9b9`).

### CR-4 · `progress/current.md` describe una situación que ya no existe (bloqueante, C2)

Titula **«F-034 · BLOQUEADA en el porte a `arnes-base`»** y afirma:

> `arnes-base/harness/VERSION` sigue en 1.5.2 **a propósito**: no se ha tocado
> nada allí.

Hoy `arnes-base` está en **1.6.0** con árbol limpio y el porte dentro. C2 pide
que `current.md` describa solo la sesión activa. Reescribir la entrada al estado
real: T12 resuelto, y lo que queda abierto es CR-1/CR-2.

### CR-5 · El informe del implementer da la feature por no cerrable (menor, documental)

`progress/impl_F-034.md` §T12 («**BLOQUEADO**… La feature no puede cerrarse sin
esto (R18)») y la sección «Verificaciones MANUAL pendientes» («las **dos
decisiones de §T12**, sin las cuales la feature no puede cerrarse») ya no son
ciertas. No hay que reescribir el §T12 —es registro histórico válido y bien
argumentado—, pero sí **añadir una nota de cierre** que diga cómo se resolvió,
para que quien lo lea dentro de dos meses no crea que quedó bloqueada.

---

## Observaciones que NO bloquean

1. **El aviso `[ADAPTAR]` de `init.sh` sobre `design.md` es un falso positivo**,
   como el implementer anotó: la marca aparece dentro de una frase que *habla*
   de una marca resuelta (`design.md:55`). Confirmado leyendo la línea. Hizo
   bien en no tocar una spec aprobada para acallar un aviso. **Propuesta**: que
   la comprobación de `init.sh` ignore las marcas que van dentro de comillas
   invertidas — hoy penaliza documentar el propio mecanismo.
2. **`e97f9b9` no lleva formato `F-034 Tn:`** siendo materialmente T12. Menor,
   pero rompe la correspondencia tarea↔commit que C5 usa.
3. **T7 se extendió** más allá de su letra (una línea en los otros cuatro
   informes de mutación). La extensión cumple D1 mejor que la letra de T7.
   Correcta.

## Automejora del protocolo (propuesta, no aplicada)

Esta review destapa un hueco del arnés que ningún checkpoint cubría, y que ha
sido la causa de dos de los cinco cambios requeridos:

> **Las puertas se miden sobre un árbol, y el árbol puede cambiar después.**
> Nada obliga hoy a comprobar que la campaña de mutación y la cobertura se
> midieron contra el **HEAD que se revisa**. Aquí un commit posterior multiplicó
> el alcance por 19 y las tres puertas siguieron pareciendo verdes.

Propuesta para `CHECKPOINTS.md` C4 bis y `.claude/agents/reviewer.md`, a portar
a `arnes-base` si el humano la acepta: **el informe de mutación debe declarar el
SHA de HEAD contra el que se midió, y el reviewer comprueba que el alcance
recalculado hoy coincide con el que el informe declara** (nº de ficheros y de
líneas, que es barato: cálculo puro). Si no coincide, la campaña está caduca y
hay que rehacerla. Es una comprobación de dos segundos que aquí habría saltado
sola, y encaja con el reviewer incremental que propone F-038.
