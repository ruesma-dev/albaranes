# tests/test_f104_textos_avisos.py
"""F-104 · sv4 entiende los códigos del contrato v8.3 de sigrid-api.

Contrato v8.3: ``sigrid-api`` ``871cc0c`` (§3.2 avisos, §3.3 errores).

- R7: los tres Errores v8.3 y los dos Avisos v8.3 tienen el texto de design
  §3.2 en ``TEXTOS_MOTIVO_ALTA``, no vacío y distinto del código (F-077 R27
  sigue en verde: lo prueba ``test_f077_motivos_alta.py``).
- R10 (parte de sv4): el texto de ``proveedor_sin_albaran_previo`` se conserva
  siempre (las altas antiguas lo llevan en ``motivos_json``).
- R8: «Avisos de Sigrid» enseña el texto, el ``mensaje`` de sigrid-api y la
  línea, con el código en el ``title`` (D2); un aviso sin texto, como hoy.
- R9: los avisos no cambian el estado del alta ni el bloqueo del documento.
"""
from __future__ import annotations

import re

import pytest

from domain.models import alta_sigrid_models as modelos
from domain.models.alta_sigrid_models import AltaSigridVista

#: design §3.2, literal.
TEXTOS_V83 = {
    "proveedor_no_encontrado": "El proveedor no existe en Sigrid en la empresa de la obra",
    "proveedor_ambiguo": "Hay varios proveedores en Sigrid con ese CIF",
    "retencion_no_soportada": "La retención del contrato no la admite el alta automática: alta a mano",
    "retencion_del_contrato": "Sigrid aplicó la retención del contrato",
    "cabecera_sin_dato": "Sigrid dejó vacío algún dato de pago de la cabecera",
}
RETIRADO = "proveedor_sin_albaran_previo"


# ------------------------------------------------------------------ #
# R7 · textos de los cinco códigos
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(("codigo", "texto"), sorted(TEXTOS_V83.items()))
def test_f104_r7_texto_de_cada_codigo_v83(codigo, texto):
    assert modelos.TEXTOS_MOTIVO_ALTA[codigo] == texto
    assert modelos.texto_motivo_alta(codigo) == texto


@pytest.mark.parametrize("codigo", sorted(TEXTOS_V83))
def test_f104_r7_texto_no_vacio_y_distinto_del_codigo(codigo):
    texto = modelos.TEXTOS_MOTIVO_ALTA[codigo]
    assert texto.strip() and texto != codigo


@pytest.mark.parametrize("codigo", ["proveedor_no_encontrado", "retencion_no_soportada"])
def test_f104_r7_un_motivo_v83_sale_con_su_texto(codigo):
    alta = AltaSigridVista(estado="no_admitido", motivos=[{"codigo": codigo, "detalle": "d"}])
    assert alta.motivos_documento == [{"codigo": codigo, "detalle": "d", "texto": TEXTOS_V83[codigo]}]


# ------------------------------------------------------------------ #
# R10 · el texto del Código retirado se conserva
# ------------------------------------------------------------------ #
def test_f104_r10_el_retirado_conserva_su_texto():
    assert modelos.TEXTOS_MOTIVO_ALTA[RETIRADO] == (
        "El proveedor no tiene ningún albarán previo en Sigrid")
