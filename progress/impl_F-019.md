<!-- progress/impl_F-019.md -->
# F-019 · Informe de implementación

**Feature**: Importe de línea: manda el unitario leído; el importe solo se
despeja si faltan campos.
**Rama**: `feature/F-019-importe-unitario-manda` (base `dev`, HEAD `cd904cd`).
**Rigor declarado**: `critico` (`harness/features.json`).
**Spec**: `specs/F-019-importe-unitario-manda/` (aprobada por el humano).
**Diagnóstico de origen**: `progress/prueba_local_feymaco_20260818.md`.

Documento en construcción: se completa tarea a tarea. La sección
«Evidencias» y las verificaciones MANUAL están al final.

---

## Fase RED — traza real del fallo antes del código

Rigor `critico`: para los requisitos centrales el test se escribió ANTES que
el código y se ejecutó para ver el fallo. Lo que sigue es la salida REAL
pegada, no un resumen.

### RED 1 — sv5, el SELECT infla el importe (R4, R7, tramo sv5 de R16)

Comando exacto (desde `services/albaran-valoracion-api`, como hace la
sección 7 bis de `init.sh`):

```
python -m pytest tests -q --tb=short
```

Salida (con `_SQL_ALBARAN_LINES` todavía sin corregir):

```
F.F...FF.                                                                [100%]
================================== FAILURES ===================================
_________ test_f019_r4_importe_leido_no_se_multiplica_por_la_cantidad _________
tests\test_f019_r4_r7_importe_select.py:156: in test_f019_r4_importe_leido_no_se_multiplica_por_la_cantidad
    assert filas[0]["importe_albaran"] == pytest.approx(35.19)
E   assert 3800.5199999999995 == 35.19 ± 3.5e-05
E
E     comparison failed
E     Obtained: 3800.5199999999995
E     Expected: 35.19 ± 3.5e-05
_____________ test_f019_r16_tramo_sv5_las_cinco_lineas_de_feymaco _____________
tests\test_f019_r4_r7_importe_select.py:204: in test_f019_r16_tramo_sv5_las_cinco_lineas_de_feymaco
    assert fila["importe_albaran"] == pytest.approx(linea[5]), linea[1]
E   AssertionError: PAPEL HIGIENICO (SACO 108)
E   assert 3800.5199999999995 == 35.19 ± 3.5e-05
E
E     comparison failed
E     Obtained: 3800.5199999999995
E     Expected: 35.19 ± 3.5e-05
_______ test_f019_r7_precio_neto_sin_cantidad_conserva_el_importe_leido _______
tests\test_f019_r4_r7_importe_select.py:261: in test_f019_r7_precio_neto_sin_cantidad_conserva_el_importe_leido
    assert filas[0]["importe_albaran"] == pytest.approx(35.19)
E   assert None == 35.19 ± 3.5e-05
E
E     comparison failed
E     Obtained: None
E     Expected: 35.19 ± 3.5e-05
_________ test_f019_r7_precio_neto_sin_precio_unitario_tambien_manda __________
tests\test_f019_r4_r7_importe_select.py:272: in test_f019_r7_precio_neto_sin_precio_unitario_tambien_manda
    assert filas[0]["importe_albaran"] == pytest.approx(35.19)
E   assert 3800.5199999999995 == 35.19 ± 3.5e-05
E
E     comparison failed
E     Obtained: 3800.5199999999995
E     Expected: 35.19 ± 3.5e-05
=========================== short test summary info ===========================
FAILED tests/test_f019_r4_r7_importe_select.py::test_f019_r4_importe_leido_no_se_multiplica_por_la_cantidad
FAILED tests/test_f019_r16_tramo_sv5_las_cinco_lineas_de_feymaco
FAILED tests/test_f019_r4_r7_importe_select.py::test_f019_r7_precio_neto_sin_cantidad_conserva_el_importe_leido
FAILED tests/test_f019_r4_r7_importe_select.py::test_f019_r7_precio_neto_sin_precio_unitario_tambien_manda
4 failed, 5 passed in 0.90s
```

El `3800.5199999999995` es el número del informe del 18-08 (3.800,52 €)
reproducido por el SQL de producción sobre la fila real del albarán. Los
5 tests que pasan en RED son los que describen comportamiento que NO debía
cambiar (R5 cascada, R6 hormigón, columnas del SELECT): que estuvieran ya
verdes es parte de la evidencia de que el fix es quirúrgico.
