# tests/test_f053_t25_supervivientes.py
"""F-053 · T25 · supervivientes de la campaña de mutación en ``ruesma_comun``.

- «Línea a registrar» y «valorado» en el borde exacto del épsilon (1e-9 es cero).
- ``motivos_configuracion`` pide los errores SIN el valor de entrada ni la URL
  de ayuda (R35: pydantic no debe ni siquiera materializarlos para el log).
"""
from __future__ import annotations

from ruesma_comun import alta_sigrid as a
from ruesma_comun.configuracion import motivos_configuracion
from ruesma_comun.valoracion import esta_valorado


def test_f053_t25_importe_igual_al_epsilon_no_se_registra():
    assert a.es_linea_a_registrar(1e-9) is False
    assert a.es_linea_a_registrar(-1e-9) is False


def test_f053_t25_manual_con_importe_igual_al_epsilon_no_esta_valorada():
    assert esta_valorado("manual", [1e-9]) is False
    assert esta_valorado("manual", [1e-9, 2.0]) is True


class _ErrorFalso:
    def __init__(self):
        self.pedidos: list[dict] = []

    def errors(self, **kwargs):
        self.pedidos.append(kwargs)
        return [{"loc": ("clave",), "msg": "Field required"}]


def test_f053_t25_motivos_configuracion_pide_los_errores_sin_valores():
    falso = _ErrorFalso()
    assert motivos_configuracion(falso) == "clave: Field required"  # type: ignore[arg-type]
    assert falso.pedidos == [{"include_input": False, "include_url": False}]
