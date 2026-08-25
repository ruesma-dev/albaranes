<!-- progress/impl_F-036_cambios_menores.md -->
# F-036 · Los cuatro cambios requeridos de la review (pasada 2)

Cierre de los cuatro pendientes menores que dejó viva
`progress/review_F-036_bloques_BCD_pasada2.md` («Cambios requeridos», no
levantan la aprobación). **Cuatro y solo cuatro**: no se ha implementado nada
más, no se ha tocado `harness/features.json` (la feature sigue `blocked` por
F-043) y **T11 sigue revertida** (la tipología la decide la IA).

Rama `feature/F-036-residuos-contenedores-e-incrementos`. Cuatro commits
locales `F-036 CR-10..CR-13`, ninguno empujado.

| # | Commit | Qué cierra |
|---|---|---|
| 1 | `bf6139f` CR-10 | La última mentira de T11 en una docstring de sv2 |
| 2 | `b7662f7` CR-11 | La sintética muda (guarda de `RAZON_SIN_CANTIDAD`) |
| 3 | `bb203af` CR-12 | `_motivos_de` falla a gritos |
| 4 | `1ebb597` CR-13 | `claves_dedupe` repetía el defecto de la fecha |

Rigor **`critico`**: fase RED con traza pegada en los cambios 2, 3 y 4. El 1
es una línea de documentación y no la lleva (así lo acotaba el encargo).

---

## Cambio 1 — la docstring que aún decía que sv5 consume el catálogo LER

**Fichero:** `services/albaranes-api/tests/test_f036_r14_ler_reexportado.py:4-8`.

Decía «se movieron a `ruesma_comun.ler` porque sv5 tambien los necesita
(R13)». Falso desde `7ca2ffc`, que retiró R13. Ahora dice que los consumen
**sv2 y sv6**, y que **sv5 NO** es consumidor, con el commit y la fecha —
misma redacción que ya tienen `ruesma_comun/ler.py`,
`albaranes-api/domain/models/tipologia.py` y `requirements.md:71-72`.

Sin fase RED: es documentación, no comportamiento.

**Verificación.** `grep -rn "sv5 tambien\|sv5 también" services/ docs/ specs/`
→ **sin resultados** (esta vez el grep cubre las dos grafías; el de la pasada
anterior fue el que se dejó esta línea).
`python -m pytest tests/test_f036_r14_ler_reexportado.py -q` → `2 passed`.

---

## Cambio 2 — la sintética muda

**Ficheros:** `services/albaran-valoracion-persist/application/services/valuation_builder.py`
(`_build_synthetic_line`) y su test.

**El defecto.** La guarda de `RAZON_SIN_CANTIDAD` estaba atada a
`modifier_source == 'gestion_residuos'`. Pero quien deja la cantidad en `None`
es la **herencia del padre de residuos sin contenedores calculables**, y esa
herencia alcanza a **todas** las sintéticas que cuelgan de esa base: las de la
red determinista y las que trae IA3 con otra fuente (portes, esperas...). Con
otra fuente la línea salía con `cantidad=None`, `importe=None`,
`review_required=False` y **sin ninguna razón**: la línea muda que
`RAZON_SIN_CANTIDAD` existe para evitar. No son euros de más (antes heredaba
los 6 m³ crudos, que sí lo eran).

**El arreglo.** `padre_residuos` sube al cuerpo de la función —manda dos cosas
distintas: de qué campo se hereda la cantidad y si hay que explicarla— y la
guarda pasa a ser `if padre_residuos and cantidad is None`. La sintética
`gestion_residuos` cuyo padre no está en el contexto no pierde nada: ya lleva
`synthetic_without_parent` / `synthetic_parent_not_in_context` con su propio
`review_required`. Queda escrito en el comentario del bloque.

### Fase RED

`cd services/albaran-valoracion-persist && python -m pytest tests/test_f036_r16_r19_sinteticas_ler.py -q -k "sintetica_del_padre_se_explica or sintetica_ajena_no_lleva or fuera_de_residuos_una_sintetica"`

```
>       assert RAZON_SIN_CANTIDAD in ajena.review_reasons
E       AssertionError: assert 'residuos_sintetica_sin_cantidad' in ['inherited_from_base_line']
E        +  where ['inherited_from_base_line'] = LineValuationRecord(merge_line_id=None, ...
E            modifier_source='portes', ... ).review_reasons

tests\test_f036_r16_r19_sinteticas_ler.py:585: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f036_r16_r19_sinteticas_ler.py::test_f036_r19_sin_contenedores_CUALQUIER_sintetica_del_padre_se_explica
1 failed, 2 passed, 27 deselected in 0.67s
```

Los dos que pasaban en rojo son los de no-regresión, escritos a la vez y a
propósito: fijan que el motivo **no** se convierta en etiqueta de familia (con
contenedores, la sintética ajena hereda 1 UD y no lo lleva) y que **no** se
extienda fuera de residuos (padre de hormigón sin cantidad, tampoco).

### Verde

`python -m pytest tests/test_f036_r16_r19_sinteticas_ler.py -q` →
`30 passed in 1.22s`. Suite de sv6 completa → `183 passed in 3.00s`.

---

## Cambio 3 — `_motivos_de` falla a gritos

**Fichero:** `tests/test_f027_r18_r22_contrato.py` (helpers de análisis +
bloque de tests «El portero del portero»).

**El defecto.** Ante un `reasons.append(<expresión que no sabe resolver>)` el
analizador se la saltaba **en silencio**: el motivo no entraba en el conjunto,
la comparación con `MOTIVOS_DEL_BUILDER` seguía cuadrando y la congelación
daba el visto bueno sobre un vocabulario que no había visto entero. Ya ocurrió
con `residuos_ler_sin_tarifa_en_contrato` y el test aguantó verde una feature
completa.

**El arreglo.** `MotivoIlegible(AssertionError)` con el fichero, la línea, la
forma (`reasons.append(...)`, `reasons = [...]`, `reasons=[...]`) y el nodo sin
resolver. Cubre las cuatro formas que enumeró la review:

- `ri.RAZON_X` — atributo de módulo: además de fallar cuando no resuelve, ahora
  **se resuelve** siguiendo el import (`_alias_de_modulo`);
- constantes de fuera de sv6 → revienta;
- locales de función → revienta;
- `extend` / `insert`, que antes ni se miraban → entran en el análisis
  (`_METODOS_QUE_ANADEN`) y sus literales se recogen.

Lo que se sigue aceptando en silencio, documentado: la **propagación** del
valor entero (`reasons.append(result.reason)` en `unit_converter.py:146`,
`reasons.extend(guard_reasons)` en el builder). No es vocabulario del módulo
que lo reenvía; lo congela el test de su módulo. Dentro de una **lista
literal** no hay excusa y también revienta (`admite_propagacion`).

Ninguna de las formas ilegibles se usa hoy: es preventivo, y la congelación
sigue verde con el código actual.

Mensaje real que produce:

```
MotivoIlegible -> sonda.py:3 · reasons.append(...): el analizador de motivos
no sabe resolver un Name a un literal — 'RAZON_QUE_VIVE_FUERA'. Si es un
motivo nuevo, escríbelo como literal o como constante de módulo de sv6 y
añádelo a la lista congelada; si son motivos que llegan de otro módulo,
propágalos con `reasons.extend(...)` sobre el valor entero, no elemento a
elemento.
```

### Fase RED

`python -m pytest tests/test_f027_r18_r22_contrato.py -q`

```
>       assert _motivos_de(_modulo(tmp_path, cuerpo)) == esperado
E       AssertionError: assert set() == {'motivo_a'}
E         Extra items in the right set: 'motivo_a'
tests\test_f027_r18_r22_contrato.py:555: AssertionError
=========================== short test summary info ===========================
FAILED ...::test_f027_r22_el_analizador_revienta_ante_lo_que_no_sabe_leer[atributo_de_modulo_inexistente]
FAILED ...::test_f027_r22_el_analizador_revienta_ante_lo_que_no_sabe_leer[constante_de_fuera_de_sv6]
FAILED ...::test_f027_r22_el_analizador_revienta_ante_lo_que_no_sabe_leer[extend_con_lista_ilegible]
FAILED ...::test_f027_r22_el_analizador_revienta_ante_lo_que_no_sabe_leer[insert_ilegible]
FAILED ...::test_f027_r22_el_analizador_revienta_ante_lo_que_no_sabe_leer[keyword_reasons_ilegible]
FAILED ...::test_f027_r22_el_analizador_revienta_ante_lo_que_no_sabe_leer[lista_literal_ilegible]
FAILED ...::test_f027_r22_el_analizador_revienta_ante_lo_que_no_sabe_leer[llamada]
FAILED ...::test_f027_r22_el_analizador_revienta_ante_lo_que_no_sabe_leer[local_de_funcion]
FAILED ...::test_f027_r22_el_fallo_dice_QUE_forma_vio_y_DONDE[... las 8 mismas ...]
FAILED ...::test_f027_r22_lo_que_sabe_leer_lo_recoge_entero[atributo_de_modulo_resuelto]
FAILED ...::test_f027_r22_lo_que_sabe_leer_lo_recoge_entero[extend_lista_de_literales]
FAILED ...::test_f027_r22_lo_que_sabe_leer_lo_recoge_entero[insert_literal]
19 failed, 15 passed in 2.84s
```

(«DID NOT RAISE AssertionError» en las 16 primeras: el silencio, medido.)

### Verde

`python -m pytest tests/test_f027_r18_r22_contrato.py -q` → `34 passed in
3.73s`, **incluidos los dos tests de congelación sobre los ficheros reales**
(`_motivos_de(VALUATION_BUILDER) == MOTIVOS_DEL_BUILDER` y el del conversor):
el endurecimiento no cambia lo que ve del código actual.

---

## Cambio 4 — `claves_dedupe` repetía el defecto de la fecha

**Fichero:** `services/albaran-valoracion-persist/application/services/residuos_incrementos.py:146`.

Llamaba a `normalizar_ler` sobre la descripción de la sintética, que es
**texto libre**: `"INCREMENTO TARIFA DESDE 01-01-25"` daba la clave `010125`.
Es el mismo defecto que CR-3 corrigió al lado en `es_linea_incremento_ler`.
Una clave inventada dispara el dedupe donde no debe, y lo que se pierde es una
sintética que **sí** había que emitir. Ahora usa `ler_creible`.

Los dos `normalizar_ler` que quedan en el fichero (`:125`, `:221`) son sobre
`contexto_linea.codigo_ler`, que es un **campo de código** y no texto libre:
ahí `normalizar_ler` es lo correcto según su propio contrato.

**Límite conocido, escrito en el test** (no lo abre este cambio, es la
contrapartida deliberada de `ler_creible`): si el texto trae además contexto de
residuos —`"CANON DE VERTEDERO TARIFA 01-01-25"`, y `vertedero` está en
`_PALABRAS_CONTEXTO_LER`— la fecha sí cuenta como LER. Lo comprobé al escribir
el test conductual y corregí el escenario a uno sin palabra de contexto, que
es el caso que el cambio realmente cierra.

### Fase RED

`cd services/albaran-valoracion-persist && python -m pytest tests/test_f036_r16_r19_sinteticas_ler.py -q -k "clave_de_dedupe or fecha_en_la_regla_nueva"`
(el segundo test, ya en su redacción final, con el fuente revertido vía
`git stash push` para medir el rojo de verdad):

```
>       assert claves_dedupe(
            _sintetica_de_ia3("INCREMENTO TARIFA DESDE 01-01-25")
        ) == ()
E       AssertionError: assert ('010125',) == ()
E         Left contains one more item: '010125'
tests\test_f036_r16_r19_sinteticas_ler.py:338: AssertionError

>       assert "RECARGO TARIFA DESDE 01-01-25" in descripciones
E       AssertionError: assert 'RECARGO TARIFA DESDE 01-01-25' in ['TARIFA 010125', 'INCREMENTO LER 170802']
tests\test_f036_r16_r19_sinteticas_ler.py:386: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_f036_r16_r19_sinteticas_ler.py::test_f036_r18_la_clave_de_dedupe_no_lee_una_fecha_como_LER
FAILED tests/test_f036_r18_una_fecha_en_la_regla_nueva_no_le_come_la_sintetica
2 failed, 30 deselected in 1.00s
```

El segundo es conductual: con una regla ficticia (el enganche de F-006) cuya
descripción nombra una fecha, la sintética **desaparecía** del documento
porque el dedupe la daba por emitida contra una línea de IA3 que solo
nombraba esos seis dígitos.

### Verde

Suite de sv6 completa → `185 passed in 1.75s`.

---

## Evidencias

| Evidencia | Valor real |
|---|---|
| **Tests ejecutados** | sv6 `185 passed in 1.75s`; sv2 `58 passed in 1.38s`; raíz `556 passed in 116,13s`. Suites en SERIE, nunca en paralelo. |
| **Tests nuevos** | 3 (cambio 2) + 20 casos parametrizados en 4 tests (cambio 3) + 2 (cambio 4) = **25 casos nuevos**, todos con RED pegada arriba. |
| **Cobertura de las líneas cambiadas** | línea `PUERTA COBERTURA` de `bash harness/init.sh`, ver abajo. |
| **Mutantes generados y supervivientes** | **NO ejecutado por instrucción explícita del líder**: la campaña de mutación es **T23**, tarea abierta del humano. No es un N/A del lenguaje ni una omisión: sigue bloqueando el cierre de F-036 y este encargo no la cubría. |
| **Tiempo de ejecución de la suite** | raíz 116,13 s; sv6 1,75 s; sv2 1,38 s. |
| **Evals con LLM** | NO ejecutadas (`--con-llm` gasta LLM real), por instrucción explícita. |

### `bash harness/init.sh` — el último y solo, **exit 0**

Lanzado tal cual, sin pipes ni decoración. Líneas que importan:

```
[OK] Arnés v1.7.2 (2026-08-21)
     43 features, 32 abiertas, en curso: ninguna, bloqueadas: ['F-036']
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 1113 avisos (deuda previa, no bloquea)
556 passed in 153.08s (0:02:33)
[OK] pytest en verde (con medición de cobertura)
[OK] servicio sv2-api: pytest en verde                    (58 passed in 1.99s)
[OK] servicio sv6-valoracion-persist: pytest en verde    (185 passed in 6.62s)
[OK] sv3, sv4, sv5, comun: en verde (caché: árbol sin cambios)
[OK] PUERTA COBERTURA: 98.2% de 283 líneas cambiadas cubiertas (278/283,
     umbral 80%, nivel critico)
[OK] PUERTA RUTAS SENSIBLES: N/A (sin feature en curso con rama)
[OK] PUERTA TAMAÑO: F-036 dentro de los topes (requirements 149/150,
     design 228/250, impl 220/220)
[OK] Rama actual: feature/F-036-residuos-contenedores-e-incrementos
ENTORNO LISTO. Puedes trabajar.
```

Segunda pasada para el código de salida: `exit=0`.

Los tres `[AVISO]` son deuda previa y ninguno lo abre este trabajo: `ruff`,
sv1-email sin directorio de tests, `infra` sin `comando_tests`, marcas
`[ADAPTAR]` en specs de F-034/F-035, y el aviso de que hay una feature
`blocked` (F-036, esperando F-043: lo querido).

**Cobertura de líneas cambiadas: 98.2 % (278/283)**, umbral 80 %, nivel
`critico` — el mismo 98.2 %/283 que midió el reviewer en la pasada 2, así que
las líneas de estos cuatro cambios entran cubiertas.

**PUERTA RUTAS SENSIBLES sale N/A** por lo que ya observó el reviewer: con
F-036 en `blocked` no hay «feature en curso con rama» y esa puerta se apaga.
Es exactamente la automejora que él propone (`--feature F-XXX` explícito) y
que sigue sin aplicar por no estar entre los cuatro.

## Fuera de alcance / qué falta

- **No** se tocó `harness/features.json`: F-036 sigue `blocked` a la espera de
  F-043.
- **No** se restauró T11.
- Pendientes de cierre, ajenos a este encargo y del humano: **T23** (campaña de
  mutación), **T24** y el desbloqueo por **F-043**.
- La automejora que propone la review (`harness.rutas_sensibles --feature
  F-XXX` explícito) sigue **sin aplicar**: no estaba entre los cuatro.
