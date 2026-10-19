# F-080 · informe del implementer

Tras un empate por nombre, la familia solo elige entre los empatados (H4 de `progress/review_F-073.md`).
Rama `feature/F-080-empate-solo-entre-empatados`, worktree `../albaranes-F-080`. Rigor `critico`, solo sv3.
Variante **(b)** de P1 (decisión del humano, 2026-10-19): el paso por puntos de hoy no cambia; tras un
empate por nombre su ganador solo se acepta si es uno de los empatados (clave de CIF normalizada).

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
