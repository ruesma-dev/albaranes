# tests/test_f110_avisos_v84.py
"""F-110 · T19 · los avisos de línea del contrato v8.4 de sigrid-api (R13).

Contrato v8.4 (F-018 de sigrid-api, desplegada el 2026-10-30; resumen en
``azure-apps/sigrid_api.md`` §8.6): una vinculada con ``dto`` pedido se escribe
como se pide y cada diferencia con el contrato es un aviso INFORMATIVO de línea:

- ``precio_distinto_del_contrato``: el bruto frente a ``ctrpro.tar``.
- ``dto_distinto_del_contrato``: el porcentaje frente al del ``ctrpro``.

No son errores ni bloquean (no están en ``ALTA_SIGRID_AVISOS_BLOQUEANTES`` por
defecto): sv4 los enseña en «Avisos de Sigrid» con su texto. Un ``dto`` mal
formado es un 400 sin código ⇒ ``error``, como hoy (H25): no hay códigos nuevos
de error que añadir a ``CODIGOS_LINEA``.
"""
from __future__ import annotations

import pytest

from domain.models import alta_sigrid_models as modelos
from domain.models.alta_sigrid_models import AltaSigridVista

TEXTOS_V84 = {
    "precio_distinto_del_contrato": "Sigrid avisa: el precio no es el del contrato",
    "dto_distinto_del_contrato": "Sigrid avisa: el descuento no es el del contrato",
}


@pytest.mark.parametrize(("codigo", "texto"), sorted(TEXTOS_V84.items()))
def test_f110_r13_texto_de_los_avisos_v84(codigo, texto):
    assert modelos.TEXTOS_MOTIVO_ALTA[codigo] == texto


def test_f110_r13_avisos_v84_en_avisos_de_sigrid_sin_cambiar_el_estado():
    alta = AltaSigridVista(estado="registrado", avisos=[
        {"codigo": "dto_distinto_del_contrato", "mensaje": "pedido 40%, contrato 0%",
         "referencia_linea": "9"},
    ])
    assert alta.avisos_sigrid == [
        {"codigo": "dto_distinto_del_contrato", "texto": TEXTOS_V84["dto_distinto_del_contrato"],
         "mensaje": "pedido 40%, contrato 0%", "referencia_linea": "9"},
    ]
    assert alta.estado == "registrado" and alta.motivos_documento == []


def test_f110_r13_sv9_no_los_bloquea_por_defecto():
    from pathlib import Path

    settings = (Path(__file__).resolve().parents[2] / "albaranes-alta-sigrid" / "config"
                / "settings.py").read_text(encoding="utf-8")
    for codigo in TEXTOS_V84:
        assert codigo not in settings
