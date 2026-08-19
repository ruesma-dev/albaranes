<!-- specs/F-034-mutacion-is-y-coherencia-evals/requirements.md -->
# F-034 · Requisitos

**Feature**: el mutador del arnés no muta `is` / `is not`, más dos
incoherencias que arrastra la puerta de evals.
**Rigor declarado**: `estandar`. **Prioridad**: 1.
**Rama**: `feature/F-034-mutacion-is-y-coherencia-evals`.
**Fuente**: `progress/review_F-027.md` §12 y la experiencia de F-019.
**Servicios tocados**: NINGUNO. Esta feature toca **el arnés** (`harness/`,
`CHECKPOINTS.md`, `.claude/agents/`) y su copia genérica en el repositorio
`arnes-base`. No entra ni una línea de `services/`.

---

## 0. Por qué esto va primero

`harness/mutacion.py` mide si los tests de una feature son de verdad. Hoy no
sabe mutar `is` / `is not`, que en Python es **la** guarda de ausencia
(`x is None`). Es justo el patrón de los dos defectos más caros del proyecto:

- **F-027** (×1000 kg→TN, 468.763,40 € en un albarán): la línea del defecto es
  `if partida_result.derived_line is not None:`. La campaña automática dio
  **0 mutantes** y hubo que sustituirla por una manual de 7.
- **F-019** (importe de línea): la precedencia se decide con
  `importe_albaran_declarado is not None`.

Mientras no se arregle, cada feature que se cierre se mide con una campaña
**ciega en su punto más delicado**, y un «0 supervivientes» puede significar
«nadie probó la línea que importa».

## 1. Corrección del enunciado (verificado contra el árbol, 2026-08-19)

La descripción de F-034 en `harness/features.json` se escribió desde el
informe del reviewer de F-027. Al comprobarla fichero a fichero, **el punto (2)
está mal diagnosticado** y esta spec lo corrige. Lo verificado:

| Afirmación del enunciado | Realidad comprobada |
|---|---|
| «`evals/ground_truth/` NO EXISTE en este repositorio» | **Falso.** Existe, con sus **seis libros** `.xlsx` (`IA1_extraccion`, `IA2_contexto`, `IA3_valoracion`, `IA4_conciliacion`, `INPUTS`, `RESULTADO_FINAL`), y es una ruta **del código**: `evals/conversor.py:39` la declara como `RUTA_GROUND_TRUTH`. Lo que pasa es que **no se versiona** (`.gitignore:18` → `*.xlsx`), por decisión escrita en `evals/README.md` §«Qué se versiona y qué no». Quien clona el repositorio no la ve. |
| «los casos viven en `evals/fixtures/inputs/`» | **Cierto y es lo que importa**: `evals.runner` consume los fixtures (`evals/runner.py:27,83`), y su propio mensaje de no-evaluable es literalmente `no hay ningún caso en evals/fixtures/inputs/` (`runner.py:94` y `:324`). |
| «la puerta lleva semanas en `aviso` porque el ground truth está vacío» | **Cierto, pero el criterio está escrito sobre el artefacto equivocado.** Los seis `_indice.json` versionados están hoy con `"casos": []`. |

**Conclusión**: el defecto no es un nombre mal escrito, es que la condición de
la puerta se declara sobre un artefacto **no versionado e invisible** (los
libros Excel) en vez de sobre el artefacto **versionado que el runner lee**
(los fixtures). El arreglo es reescribir el criterio, no renombrar una ruta.

Ficheros con la referencia equivocada, **con ruta y línea** (la lista del
enunciado estaba incompleta: `current.md` la trae dos veces):

| Fichero | Línea | Qué dice hoy |
|---|---|---|
| `CHECKPOINTS.md` | 185 | «Mientras los libros de `evals/ground_truth/` no tengan casos, esa pasada da NO_EVALUABLE» |
| `harness/rutas_sensibles.json` | 3 (`_exigencia`) | «Se sube a 'bloqueo' cuando los libros de evals/ground_truth/ tengan casos» |
| `progress/current.md` | 33 | «el `evals/ground_truth/` inexistente» |
| `progress/current.md` | 64 | «F-034 arregla que la documentación diga `evals/ground_truth/`, que no existe» |

**Ficheros donde la referencia es CORRECTA y no se toca**: `evals/README.md`,
`evals/conversor.py`, `tests/conftest.py` (los libros existen de verdad y esos
textos hablan de ellos), y todo `progress/*_F-0XX.md` y `specs/F-0XX-*/`
anteriores, que son **registro histórico**: no se reescribe lo que ya se
escribió. `BACKLOG.md` es un fichero **generado** desde `features.json`: se
regenera solo (ver D3).

---

## 2. Requisitos

### G1 — El mutador muta `is` / `is not`

**R1.** CUANDO `harness.mutacion.generar_mutantes` encuentre, en una línea del
alcance, una comparación con el operador `is`, el sistema debe generar un
mutante que sustituya `is` por `is not` en esa posición.

**R2.** CUANDO encuentre una comparación con el operador `is not`, el sistema
debe generar un mutante que sustituya `is not` por `is`.

**R3.** CUANDO una línea del alcance contenga varias comparaciones
`is`/`is not` —encadenadas (`a is b is not c`) o unidas por `and`/`or`
(`a is None or b is None`)—, el sistema debe generar **un mutante
independiente por cada operador**.

**R4.** El sistema debe etiquetar esos mutantes con el operador `comparacion`,
para que `clave_de_mutante` (fichero, operador, original, mutado) los
identifique entre campañas y `escribir_informe` conserve su análisis.

**R5.** SI la secuencia `is` o `is not` aparece **dentro de una palabra más
larga** en el hueco entre los dos operandos —caso real: un comentario con la
palabra «análisis» dentro de una condición multilínea—, ENTONCES el sistema no
debe mutar esa posición y debe seguir buscando la siguiente ocurrencia
delimitada del mismo hueco.

> Evidencia de que hoy pasa (medida el 2026-08-19 con `COMPARACIONES` parcheada
> en memoria, cálculo puro):
> `if (\n    valor  # el analisis previo\n    is None\n):` produce hoy el
> mutante `'valor  # el analisis previo'` → `'valor  # el analis notis previo'`
> — una mutación **dentro de un comentario**: no cambia el comportamiento,
> sobrevive siempre y ensucia el informe con un falso superviviente.

**R6.** MIENTRAS el delimitador de palabra de R5 esté activo, el sistema debe
seguir mutando los operadores **simbólicos escritos sin espacios**: `x==y`
sigue dando su mutante, y `a+b` el suyo. (Sin este requisito, un delimitador
aplicado a ciegas dejaría de mutar `x==y`, porque el carácter anterior a `==`
es una letra.)

**R7.** SI el operador `is not` está escrito con espaciado no canónico
(`is  not`) o partido entre dos líneas, ENTONCES el sistema no debe generar
mutante para esa comparación, **no debe fallar**, y la limitación debe constar
por escrito en el propio código.

**R8.** CUANDO se aplique un mutante de `is`/`is not` con `aplicar_mutante`, el
código resultante debe **compilar** y su AST debe llevar el operador contrario
en esa comparación (`ast.Is` ↔ `ast.IsNot`).

### G2 — El cambio se demuestra sobre código real, no sobre juguetes

> «Ahora la campaña genera más mutantes» **no es evidencia de nada**. Lo que
> hay que demostrar es que los mutantes nuevos caen en **guardas reales** y que
> **mueren** con los tests que YA existen.

**R9.** CUANDO se relance la campaña de **F-027** sobre su alcance histórico
(`e95549d8880ebdabee45c1ec4fbe20651240428f` .. `feature/F-027-conversion-kg-tn-muerta`),
el sistema debe generar **exactamente 1 mutante** —
`services/albaran-valoracion-persist/application/services/valuation_builder.py:1033`,
`if partida_result.derived_line is not None:` → `if partida_result.derived_line is None:`—
y la suite de sv6 **ya existente** debe declararlo **MUERTO**.

> Ese mutante es exactamente el **M1** de la campaña manual de F-027, que el
> reviewer reprodujo a mano: **17 failed, 93 passed**. Sirve, además, de
> control del propio mutador: un resultado distinto significa que la
> herramienta nueva miente.

**R10.** CUANDO se relance la campaña de **F-019** sobre su alcance histórico
(`cd904cdcecee56311280ee54d81a7158d0529eb5` .. `feature/F-019-importe-unitario-manda`),
el sistema debe generar **exactamente 49 mutantes** (los 31 de la campaña
original más **18 nuevos** de `is`/`is not`), los **18 nuevos deben morir**, y
los supervivientes deben seguir siendo **exactamente los 3** ya analizados como
equivalentes en `progress/mutacion_F-019.md`.

**R11.** SI algún mutante nuevo sobrevive en R9 o R10, ENTONCES la feature no
puede cerrarse sin una de estas dos cosas, por escrito y en el informe de esa
campaña: (a) un **test nuevo** que lo mate, o (b) el **análisis** de por qué es
equivalente. Un superviviente nuevo es un **hueco real de la suite**, que es
justo lo que esta feature existe para destapar.

**R12.** El informe `progress/impl_F-034.md` debe traer los **comandos exactos**
de R9 y R10, con sus referencias fijadas, de forma que el reviewer pueda
repetir ambas campañas sin adivinar nada.

### G3 — La puerta de evals dice dónde hay que mirar

**R13.** El sistema debe condicionar la subida de la puerta de rutas sensibles
de `aviso` a `bloqueo` a que **los fixtures versionados de `evals/fixtures/`
tengan casos** (hoy los seis `_indice.json` están con `"casos": []`), y no a los
libros `.xlsx` no versionados.

**R14.** SI alguien vuelve a escribir la condición de la puerta en
`harness/rutas_sensibles.json` apuntando a los libros no versionados de
`evals/ground_truth/`, ENTONCES la suite de la raíz debe fallar.

**R15.** CUANDO alguien lea `CHECKPOINTS.md` (C4 ter),
`harness/rutas_sensibles.json` o `progress/current.md`, debe encontrar la misma
condición que R13 y la aclaración de que los libros Excel de
`evals/ground_truth/` **existen pero no se versionan** (`*.xlsx` en
`.gitignore`), y que lo que consume `evals.runner` son los fixtures.

### G4 — Una campaña manual tiene que ser reproducible

**R16.** CUANDO la campaña automática dé **0 mutantes** y se sustituya por una
**manual**, `CHECKPOINTS.md` (C4 bis) debe exigir que el informe traiga una
tabla con **una fila por mutante** y, en cada fila: fichero y línea, el **texto
exacto original → mutado** de la sustitución, y el resultado con su número de
fallos. Sin ese texto exacto el punto no se marca.

**R17.** `.claude/agents/reviewer.md` debe pedir lo mismo en su protocolo de
mutación, para que el reviewer lo exija donde de verdad lo lee.

### G5 — Porte a `arnes-base` (parte de la feature, no un después)

**R18.** CUANDO el trabajo esté terminado en `albaranes`, el repositorio
`C:\Users\pgris\PycharmProjects\arnes-base` debe llevar el mismo cambio en
`arnes-base/harness/mutacion.py`, `arnes-base/tests/`,
`arnes-base/CHECKPOINTS.md` y `arnes-base/.claude/agents/reviewer.md`.

**R19.** `arnes-base/harness/mutacion.py` y `harness/mutacion.py` (albaranes)
deben quedar **idénticos** salvo finales de línea, comprobado con `diff`.

**R20.** `arnes-base/GUIA_INSTALACION.md` debe traer la sección de la versión
nueva con el mismo formato que las anteriores (`## Título (X.Y.Z, fecha)`), y
debe **avisar explícitamente** de que al actualizar a esa versión los informes
de mutación anteriores de cualquier proyecto dejan de ser comparables: la vara
de medir cambia y una campaña que estaba en verde puede pasar a rojo.

**R21.** `arnes-base/harness/VERSION` y, en albaranes, `harness/VERSION` y
`harness/ARNES_VERSION.md`, deben declarar la misma versión nueva y la fecha.

---

## 3. DECISIÓN PENDIENTE DEL HUMANO · D1 — ¿Se remide el histórico?

> **Esta decisión no la cierra el spec-author.** Se plantea aquí con su coste
> medido y una recomendación razonada; el implementer no arranca la parte
> condicionada hasta que el humano elija.

### El problema

En cuanto el mutador aprenda `is` / `is not`, los informes de mutación de
**todas las features ya cerradas** quedan desfasados: se midieron con una
campaña ciega justo en el patrón donde vivían los dos defectos más caros del
proyecto. Sus «N supervivientes» no son falsos, pero **no son comparables** con
los de cualquier feature posterior.

### Los números, medidos (no estimados a ojo)

Calculado el 2026-08-19 con `harness.alcance` + `harness.mutacion` en **cálculo
puro** (sin ejecutar ninguna suite), leyendo cada fichero en el tip de su rama
con `git show`, y parcheando `COMPARACIONES` en memoria. El método reproduce
**exactamente** los totales históricos (F-019: 31; F-027: 0), así que las
columnas «nuevos» son fiables:

| Feature | Mutantes hoy | Con `is`/`is not` | Nuevos | Tiempo de la campaña original | Tiempo estimado al remedir |
|---|---|---|---|---|---|
| F-001 | 0 | 0 | **0** | 0,0 s | nada que remedir |
| F-002 | 108 | 126 | **+18** | 54,8 s | ≈ 1,1 min |
| F-011 | 305 | 347 | **+42** | 3.694,1 s (**61,6 min**) | ≈ **70 min** |
| F-012 | 61 | 71 | **+10** | 1.234,0 s (**20,6 min**) | ≈ **24 min** |
| F-019 | 31 | 49 | **+18** | 219,2 s | ≈ **5,8 min** |
| F-027 | 0 | 1 | **+1** | 0,0 s | ≈ **< 1 min** (una pasada de la suite de sv6) |

Dos condicionantes operativos verificados:

- Para remedir hay que **fijar las referencias**: hoy `merge-base(dev, rama)`
  es el propio tip de cada rama ya integrada, así que sin `--base <sha>` el
  alcance sale **vacío**. Los seis SHA están en la cabecera de cada
  `progress/mutacion_F-0XX.md`.
- Los ficheros del alcance de **F-002, F-011, F-019 y F-027 son idénticos a
  `dev`** hoy (comprobado con `git diff --stat dev <rama> -- <ficheros>`), así
  que se pueden remedir sobre el árbol principal. **F-012 no**: su alcance
  incluye `harness/mutacion.py`, que ha cambiado con las versiones 1.5.1 y
  1.5.2 y volverá a cambiar con esta feature. Remedir F-012 honradamente exige
  un `git worktree` en su tip y mide una versión del mutador **que ya no
  existe**.

### Las tres opciones

| | Qué se hace | Coste de máquina | Coste de agente/humano | Qué se gana |
|---|---|---|---|---|
| **A · No remedir** | Se anota el cambio de vara en `GUIA_INSTALACION.md`, `ARNES_VERSION.md` y `progress/current.md`; el histórico se deja tal cual | 0 | ~10 min de redacción | Coste mínimo; el histórico queda **etiquetado** como medido con la vara vieja |
| **B · Remedir solo las críticas (F-019 y F-027)** | Las dos campañas de R9/R10 se convierten además en re-medición **oficial**: informe propio (`progress/mutacion_F-0XX_remedida.md`) y puntero desde el informe histórico | **≈ 7 min**, y **ya están pagados**: R9 y R10 obligan a lanzarlas igual como evidencia de la feature | ~20 min (redactar y revisar) | Las dos features cuyo defecto vivía en una guarda `is` quedan medidas con la vara nueva, y F-027 pasa de un «0 mutantes» que no demostraba nada a un mutante real muerto |
| **C · Remedir todas las cerradas** | A+B más F-002, F-011 y F-012 | **≈ 101 min** en serie (y no se pueden paralelizar: Windows tumba el portero) | Indeterminado: hasta **89 mutantes nuevos** que analizar uno a uno si sobreviven, más re-review de cinco features | Histórico homogéneo… salvo F-012, que mide un mutador que ya no existe |

### Recomendación del spec-author: **opción B**

1. **Es casi gratis.** R9 y R10 obligan a lanzar esas dos campañas de todos
   modos, porque son la única forma honrada de demostrar que el cambio sirve.
   La opción B solo añade escribir el resultado donde se pueda encontrar.
2. **Es donde está el valor.** F-019 y F-027 son, literalmente, las dos
   features cuyo defecto vivía en una guarda `is`. F-002, F-011 y F-012 no:
   sus defectos y sus tests no giran alrededor de la ausencia.
3. **La relación coste/valor de C es mala.** F-011 sola cuesta más de una hora
   de máquina en serie, sobre un alcance de 3.812 líneas de código de evals que
   ninguna feature futura va a tocar, y F-012 mide una versión del mutador que
   ya no existe. Es trabajo que no cambia ninguna decisión.
4. **La opción A pierde la mejor prueba disponible.** El mutante de F-027 ya
   tiene resultado conocido y verificado a mano por el reviewer (17 fallos):
   es el único caso del proyecto donde se puede contrastar la herramienta nueva
   contra un resultado medido antes de existir.

**Lo que hay que anotar pase lo que pase** (va en las tres opciones): que las
campañas anteriores a esta versión del arnés **no midieron `is`/`is not`**, y
que por eso no son comparables con las posteriores. Sin esa nota, dentro de dos
meses alguien comparará dos números que no significan lo mismo.

---

## 4. Decisiones menores (también del humano, pero sin bloqueo)

**D2 · ¿1.5.3 o 1.6.0?** — **Recomendación: 1.6.0.** Las versiones 1.5.1 y
1.5.2 mejoraron cómo se **informa** y cómo se **verifica** una campaña: ninguna
podía volver roja una campaña que estaba verde. Esta sí: cambia **qué se mide**,
puede hacer aparecer supervivientes nuevos en cualquier proyecto que actualice,
y deja los informes anteriores fuera de escala. Eso no es un parche, es un
cambio de contrato de la puerta, y el número tiene que hacerlo visible en
`ARNES_VERSION.md`. **Consecuencia**: F-035, que su ficha declara como «1.5.3»,
pasaría a ser **1.6.1** si F-034 entra antes (que es el orden de prioridad
acordado).

**D3 · ¿Se corrige la descripción de F-034 en `features.json`?** — La
descripción afirma que `evals/ground_truth/` no existe, y §1 demuestra que sí
existe. `BACKLOG.md` se genera desde ahí, así que el error queda publicado en
la raíz del repositorio para siempre. **Recomendación: corregir la frase**
(solo esa) al cerrar la feature, dejando constancia en `progress/impl_F-034.md`
de qué decía antes. Es estado del proyecto, no del arnés: por eso se pregunta.

---

## 5. Fuera de alcance (explícito)

- **Rehacer el mutador** o añadir operadores más allá de `ast.Is` / `ast.IsNot`
  (`in`/`not in`, mutaciones de retorno, borrado de sentencias…). Se rechaza
  aquí y se propone como backlog aparte si el humano lo quiere.
- **Soportar el espaciado no canónico** `is  not` o el operador partido en dos
  líneas (R7 lo declara como limitación conocida, con test que la fija).
- **Rellenar `evals/fixtures/`** o subir la puerta de rutas sensibles a
  `bloqueo`: sigue siendo pendiente del humano, y esta feature solo arregla que
  el criterio diga dónde mirar.
- **Tocar código de `services/`**: ni una línea. Si una campaña de G2 destapa
  un superviviente, lo que se añade es un **test** (R11), nunca un cambio de
  producción; y si el superviviente exigiera cambiar producción, se marca la
  feature `blocked` y se propone al humano como feature nueva.
- **Reescribir los informes históricos** de `progress/` y las specs anteriores.

## 6. Trazabilidad requisito → verificación

| Req | Verificación |
|---|---|
| R1, R2 | `tests/test_mutacion_operadores.py::test_f034_r1_*`, `::test_f034_r2_*` |
| R3 | `::test_f034_r3_una_mutacion_por_operador_en_la_misma_linea` |
| R4 | `::test_f034_r4_el_operador_declarado_es_comparacion` |
| R5 | `::test_f034_r5_no_muta_dentro_de_una_palabra_del_comentario` |
| R6 | `::test_f034_r6_los_simbolos_sin_espacios_siguen_mutando` |
| R7 | `::test_f034_r7_espaciado_no_canonico_no_genera_mutante_ni_falla` |
| R8 | `::test_f034_r8_el_mutante_compila_y_el_ast_lleva_el_operador_contrario` |
| R9, R10, R11, R12 | Campañas reales de G2 + `progress/impl_F-034.md` (T5, T6) |
| R13, R15 | Revisión del reviewer sobre los tres ficheros (comando `grep` en `tasks.md`) |
| R14 | `tests/test_mutacion_operadores.py::test_f034_r14_la_puerta_de_evals_no_se_declara_sobre_lo_no_versionado` |
| R16, R17 | Revisión del reviewer sobre `CHECKPOINTS.md` y `.claude/agents/reviewer.md` |
| R18, R19, R21 | `diff` entre los dos repositorios (T12) |
| R20 | Lectura de `arnes-base/GUIA_INSTALACION.md` |

Todos los tests son **puros** (AST y lectura de ficheros del repositorio): sin
red, sin BBDD y sin subprocesos. Las campañas de G2 sí ejecutan suites de
servicio, pero solo suites **ya existentes**, y siempre en serie.
