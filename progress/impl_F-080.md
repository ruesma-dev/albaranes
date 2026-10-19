# F-080 · informe del implementer

Tras un empate por nombre, la familia solo elige entre los empatados (H4 de `progress/review_F-073.md`).
Rama `feature/F-080-empate-solo-entre-empatados`, worktree `../albaranes-F-080`. Rigor `critico`, solo sv3.
Variante **(b)** de P1 (decisión del humano, 2026-10-19): el paso por puntos de hoy no cambia; tras un
empate por nombre su ganador solo se acepta si es uno de los empatados (clave de CIF normalizada).

## Qué cambió

- `services/albaranes-persistencia/application/services/header_resolver_service.py` (+24 líneas):
  - `_es_empatado(cif, eleccion)`, función pura junto a `_clave_cif`: ¿la clave de CIF de `cif` es la de
    algún `eleccion.empatados`? (R1, R8; D2).
  - `_resolver_por_obra_y_familia`: la condición de hoy (≥ 3 puntos y margen ≥ 2) pasa a `decide`; si
    `decide and eleccion.empatados and not _es_empatado(mejor.cif, eleccion)` ⇒ log de R6 (`logger.info`)
    y `decide = False`. Con `decide`, la rama «DEDUCIDO» de hoy intacta; sin él, el código de hoy tal cual
    (log «NO deducido», y R11 de F-073 con `eleccion.empatados`, que en el caso del ajeno siempre existe).
  - Docstring de la clase: «tras un empate por nombre, solo si el ganador es uno de los empatados (F-080)».
- `services/albaranes-persistencia/tests/test_f080_empate_solo_entre_empatados.py` (nuevo, 36 casos,
  `test_f080_rN_…`): los cinco casos de design §1 (H4, P1, ajeno cerca, ajeno lejos, penalización) y R1–R12.
  Reutiliza `_paso1`, `_resumen`, `_RepoConLineas` y `_ClienteRed` de `test_f073_eleccion` y `pasada` de
  `f062_dobles`, sin tocarlos.
- `docs/ARCHITECTURE.md`, regla 24, viñeta «Empate» (R15): el ganador por puntos solo se acepta si es uno
  de los empatados (F-080); si gana un ajeno o los puntos no deciden, revisión con `proveedor_nombre_ambiguo`.
- Fusión de `dev` (`f49f1b2`, F-075) en la rama antes de T4/T5 (commit `98b2cee`). Conflictos solo en
  `BACKLOG.md` (generado: se tomó el de `dev` y lo regenera `init.sh`) y `progress/current.md` (se conservan
  los dos bloques, F-080 y F-075). `docs/ARCHITECTURE.md` fusionó solo: la regla 25 de F-075 sigue tras la 24.
- No se tocan: `similitud_proveedor.py`, el paso 2, la red por CIF, el CIF propio, `_resolve_obra`,
  `_nota_empate_nombre`, el constructor, las constantes, comun, DDL, mensajes, `sv3.md` ni `azure-apps/`.

## Decisiones de diseño

- Variante (b) de P1, como en design §2/§4 (D1). P2: «los empatados» = `EleccionPorNombre.empatados`.
  P3: sin cambios en R11 (la nota lista todos los empatados en orden (−puntos, CIF), con el tope).
- El log de R6 va antes del log «NO deducido» de hoy, que sigue saliendo (design §4: «el código de hoy tal
  cual»). Texto exacto: `[header-resolver] proveedor NO deducido por familia+obra: el ganador por puntos B9
  (6 puntos) es AJENO al empate por nombre (2 empatados) obra=0694`.
- R12 en el test: se comprueban las constantes, el defecto de `margen_nombre` y que no hay parámetro nuevo
  en el constructor, sin fijar la lista entera de parámetros (F-049 toca el constructor en otra rama).

## Fase RED (T1)

Test escrito antes del código: `services/albaranes-persistencia/tests/test_f080_empate_solo_entre_empatados.py`
(36 casos). Comando, desde `services/albaranes-persistencia`, con HEAD `0eaec26` (código de `dev` `bee817d`):

```
python -m pytest tests/test_f080_empate_solo_entre_empatados.py -q -p no:cacheprovider --tb=short
```

Resultado: **26 failed, 10 passed in 2.14s**. Fallan los esperados por tasks.md (R2, R3, R4, R6, R7, R9) y
pasan R1, R5, R8 (el caso de la grafía), R10, R11 y R12. Los 8 casos unitarios de `_es_empatado` (R8) fallan
con `AttributeError: module 'application.services.header_resolver_service' has no attribute '_es_empatado'`:
la función aún no existe (desviación anotada abajo). Trazas reales de los requisitos centrales:

```
_ test_f080_r3_el_caso_de_h4_va_a_revision_con_la_nota_de_los_dos_hormigones __
tests\test_f080_empate_solo_entre_empatados.py:96: in _en_revision_r11
    assert decision == (None, "deterministic")
E   AssertionError: assert ('B9', 'det_familia_obra') == (None, 'deterministic')
E     At index 0 diff: 'B9' != None
WARNING  ...header_resolver_service.py:1023 [header-resolver] proveedor B9 DEDUCIDO por familia+obra (6 puntos, segundo=2, nombre=0.00) obra=0694 -> origen=det_familia_obra

____________ test_f080_r4_p1_ni_el_empatado_de_7_ni_el_ajeno_de_9 _____________
tests\test_f080_empate_solo_entre_empatados.py:96: in _en_revision_r11
    assert decision == (None, "deterministic")
E   AssertionError: assert ('B9', 'det_familia_obra') == (None, 'deterministic')
E     At index 0 diff: 'B9' != None
WARNING  ...header_resolver_service.py:1023 [header-resolver] proveedor B9 DEDUCIDO por familia+obra (9 puntos, segundo=7, nombre=0.00) obra=0694 -> origen=det_familia_obra

____________ test_f080_r6_log_del_ajeno_descartado_y_sin_deducido _____________
tests\test_f080_empate_solo_entre_empatados.py:201: in test_f080_r6_log_del_ajeno_descartado_y_sin_deducido
    [linea] = [m for m in mensajes if "AJENO" in m]
E   ValueError: not enough values to unpack (expected 1, got 0)
INFO     ...:1120 [header-resolver] proveedor por NOMBRE dentro de la obra 0694: EMPATE, no se elige: mejor cif=B1 similitud=1.00 segunda=1.00 margen=0.25 empatados=2
WARNING  ...:1023 [header-resolver] proveedor B9 DEDUCIDO por familia+obra (6 puntos, segundo=2, nombre=0.00) obra=0694 -> origen=det_familia_obra

_____ test_f080_r9_h4_entero_queda_sin_cif_con_motivo_y_la_nota_del_paso1 _____
tests\test_f080_empate_solo_entre_empatados.py:296: in test_f080_r9_h4_entero_queda_sin_cif_con_motivo_y_la_nota_del_paso1
    assert repo.cif is None
E   AssertionError: assert 'B9' is None
```

Los 10 casos de R7 (H4 y P1, semillas 1–5) y los 3 de R2 (tope, idempotencia, sustitución) fallan con el
mismo `('B9', 'det_familia_obra') == (None, 'deterministic')`.

## T2 · verde

Mismo comando tras el cambio: **36 passed in 2.17s**. Un caso de mi propio test estaba mal planteado:
`normalizar_cif("es-b1")` da `ESB1` (el prefijo `ES` solo se quita en un CIF de longitud completa), así
que «es-b1» no es la grafía de «B1». Se cambió por «b-1» (`normalizar_cif("b-1")` = `B1`, el mismo que
usa F-073). No toca la spec ni ningún test existente.

## T3 · la suite de sv3 y R13/R14

- `python -m pytest -q -p no:cacheprovider` en `services/albaranes-persistencia` (antes de fusionar
  `dev`): **1532 passed in 13.46s** = 1496 de antes + 36 nuevos. Ningún test existente tocado (R13).
- `git diff bee817d -- …/similitud_proveedor.py`: vacío (0 líneas). El diff de
  `header_resolver_service.py` frente a la base tiene 3 *hunks*: `_es_empatado` (nueva, tras
  `_clave_cif`), una línea del docstring de la clase y el bloque de decisión por puntos de
  `_resolver_por_obra_y_familia`. Sin diff en `_resolve_proveedor`, `_red_proveedor_por_cif`,
  `_candidato_claro`, `_descartar_cif_propio`, `_resolve_obra`, `_nota_empate_nombre`, `_log_eleccion`,
  constructor ni constantes (R12, R14).

## T4 · docs

`docs/ARCHITECTURE.md`, regla 24, viñeta «Empate», con el texto de design §4 (R15). Lo contrasta el reviewer
con R1–R5.

## T5 · cobertura y mutación

- `PUERTA COBERTURA` de `bash harness/init.sh` (tras fusionar `dev`): **100.0 % de 8 líneas cambiadas
  cubiertas (8/8, umbral 80 %, nivel critico)**.
- `python -m harness.mutacion --feature F-080 --workers 1` (en serie, para no correr dos suites a la vez):
  **5 mutantes generados, 5 evaluados, 5 muertos, 0 supervivientes, 0 timeouts, 66.8 s**. Informe:
  `progress/mutacion_F-080.md` (HEAD medido `00c52db`). Los tres mutantes de pertenencia de design §6
  están entre los muertos: `==`→`!=` en la clave (l. 160), `not _es_empatado`→`_es_empatado` y
  `and`→`or` en los dos sitios de la condición (l. 1031); también `decide = False`→`True` (l. 1042).
  Sin supervivientes, no hay nada que justificar.
- Fila de `progress/mutacion_F-080.md` en `progress/inventario_mutacion_F-039.md` (la exige
  `test_f039_r2_…`: la primera pasada final de `init.sh` dio KO por eso). Se rehízo el recuento: 46
  informes (faltaban las dos de F-075, que trae `dev`) y 10 con alcance fuera de `services/`.

## T7 · `bash harness/init.sh`

En verde en el worktree tras la fusión de `dev` y T4 (todas las líneas `[OK]`; un `[AVISO]` heredado: sv3
importa `ruesma_comun` del árbol principal, fuera del worktree, y no se cachea; comun no cambia en F-080).
Suites: sv3 **1576 passed** (1532 + los 44 de F-075 que trae `dev`), raíz 1328, sv1 205, sv2 485,
sv4 1774, sv5 46, sv6 473 (+1 skipped), sv9 673, comun 859 (+3 skipped). Puerta de tamaño: impl en tope.

## Pendiente

- **T6 · MANUAL del humano** (tras APPROVED, fusión en `dev` y la T12 de F-073): desplegar sv3 y mirar el
  log. Comando en `progress/current.md`, sin ejecutar.
- Fuera de alcance (requirements): revisar albaranes ya deducidos con un ajeno, O1 del paso 2 global,
  retirar `proveedor_nombre_ambiguo` al fijar a mano (F-059), `_proposeBest` y la propuesta de F-052.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests de F-080 | 36 passed in 2.17 s (RED: 26 failed, 10 passed) |
| Suite de sv3 | 1576 passed in 27.26 s (tras fusionar `dev`); 1532 passed in 13.46 s antes de fusionar |
| Tests existentes con expectativa cambiada | 0 (R13) |
| Cobertura de las líneas cambiadas | 100.0 % (8/8) — `PUERTA COBERTURA` |
| Mutantes generados / supervivientes | 5 / 0 (5 muertos, 66.8 s) — `progress/mutacion_F-080.md` |
| `bash harness/init.sh` | verde (sin `[KO]`) |
