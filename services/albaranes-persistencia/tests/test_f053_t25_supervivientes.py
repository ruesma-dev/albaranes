# tests/test_f053_t25_supervivientes.py
"""F-053 · T25 · supervivientes de la campaña de mutación en sv3.

- R45: el conservado cuenta las líneas DE ESE documento (y 0 si no hay).
- Script de medición de solo lectura (T0a, T37): fechas, cantidades nulas,
  negativas, recuento de albaranes sin líneas valoradas, CSV y salida de
  ``main``. El script es puntual (la MANUAL T0 lo ejecuta); aun así, lo que
  cuenta tiene que estar fijado: de su recuento sale la decisión de alcance.
"""
from __future__ import annotations

import csv
import dataclasses

import pytest
from sqlalchemy.dialects import postgresql

from scripts import medir_admisibilidad_f053 as m
from tests.test_f053_medicion_admisibilidad import _evaluar, _fila
from tests.test_f053_r45_reingreso_con_alta import _MERGE_ID, _buscar, _Sesion


# ------------------------------------------------------------------ #
# R45 · líneas del conservado
# ------------------------------------------------------------------ #
class _SesionSinLineas(_Sesion):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.recuentos: list[str] = []

    def scalar(self, consulta):
        self.recuentos.append(str(consulta.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True},
        )))


def test_f053_t25_r45_conservado_cuenta_las_lineas_de_su_documento():
    sesion = _SesionSinLineas(estado_alta="registrado")
    conservado = _buscar(sesion)
    assert conservado.stored_lines == 0
    (recuento,) = sesion.recuentos
    assert f"albaran_lines_merge.document_id = '{_MERGE_ID}'" in recuento


# ------------------------------------------------------------------ #
# Script de medición
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("valor, valida", [
    ("2026-09-01", True), ("", False), (None, False), ("2026-9-1", False),
    ("01/09/2026", False), ("2026-02-30", False),
])
def test_f053_t25_medicion_fecha_valida(valor, valida):
    assert m.fecha_valida(valor) is valida


def test_f053_t25_medicion_linea_es_inmutable():
    assert m.Linea.__dataclass_params__.frozen is True
    linea = m.Linea(cantidad=1.0, importe=1.0, partida=None, casa=False)
    with pytest.raises(dataclasses.FrozenInstanceError):
        linea.cantidad = 2.0  # type: ignore[misc]


def test_f053_t25_medicion_cantidad_nula_en_valoracion_y_en_merge():
    sin_convertida = m.linea_desde_valoracion(_fila("d", 1, cantidad_convertida=None,
                                                    cantidad_albaran=3.0))
    assert sin_convertida.cantidad == 3.0
    sin_ninguna = m.linea_desde_valoracion(_fila("d", 1, cantidad_convertida=None,
                                                 cantidad_albaran=None))
    assert sin_ninguna.cantidad is None
    convertida = m.linea_desde_valoracion(_fila("d", 1, cantidad_convertida=7, cantidad_albaran=3))
    assert convertida.cantidad == 7.0
    del_merge = m.linea_desde_merge({"cantidad": 2, "precio_neto": 5.0, "codigo_imputacion": None})
    assert del_merge.cantidad == 2.0
    assert m.linea_desde_merge({"cantidad": None, "precio_neto": 5.0}).cantidad is None


def test_f053_t25_medicion_importe_igual_al_epsilon_no_cuenta():
    assert m.con_importe(m.Linea(cantidad=1.0, importe=1e-9, partida=None, casa=False)) is False


@pytest.mark.parametrize("cantidad, importe, negativa", [
    (2.0, 10.0, False),
    (0.5, 0.5, False),       # positivas por debajo de 1
    (-2.0, 10.0, True),
    (2.0, -10.0, True),
    (None, 10.0, False),     # sin cantidad: no es negativa
    (-2.0, -10.0, True),
])
def test_f053_t25_medicion_lineas_negativas(cantidad, importe, negativa):
    ev = _evaluar(_fila("d1", 1, cantidad_convertida=cantidad, cantidad_albaran=cantidad,
                        importe_calculado=importe))
    assert ev["lineas_negativas"] == (1 if negativa else 0)


def test_f053_t25_medicion_cantidad_cero_no_es_negativa():
    ev = _evaluar(_fila("d1", 1, cantidad_convertida=0.0, cantidad_albaran=0.0,
                        importe_calculado=10.0))
    assert ev["lineas_negativas"] == 0


def test_f053_t25_medicion_cuenta_los_albaranes_sin_lineas_valoradas():
    merge = [{"document_id": "d2", "cantidad": 1, "precio_neto": 5.0, "codigo_imputacion": None}]
    filas = [_fila("d1", 1), _fila("d2", None), _fila("d3", 1)]
    evaluaciones = [m.evaluar(a) for a in m.agrupar(filas, merge)]
    resumen = m.resumir(evaluaciones)
    assert resumen["sin_lineas_valoradas"] == 1


def test_f053_t25_medicion_csv_con_las_columnas_de_la_primera_evaluacion(tmp_path):
    ruta = tmp_path / "uno.csv"
    m.escribir_csv(str(ruta), [_evaluar(_fila("d1", 1))])
    filas = list(csv.DictReader(ruta.open(encoding="utf-8-sig"), delimiter=";"))
    assert [f["document_id"] for f in filas] == ["d1"]


def test_f053_t25_medicion_main_devuelve_cero_y_describe_el_script(monkeypatch, capsys):
    monkeypatch.setattr(m, "leer_filas", lambda todos, env: ([_fila("d1", 1)], []))
    assert m.main([]) == 0
    with pytest.raises(SystemExit):
        m.main(["--help"])
    assert m.__doc__.splitlines()[0] in capsys.readouterr().out
