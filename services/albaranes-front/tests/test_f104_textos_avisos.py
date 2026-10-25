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


# ------------------------------------------------------------------ #
# R8 · avisos_sigrid y «Avisos de Sigrid» (D2)
# ------------------------------------------------------------------ #
RETENCION = {"codigo": "retencion_del_contrato",
             "mensaje": "Retención del contrato (código 3, 5 %): base 120,00, cuota 6,00"}
SIN_DATO = {"codigo": "cabecera_sin_dato", "mensaje": "Columnas de pago vacías: forpag, banco"}
SIN_TEXTO = {"codigo": "stock_negativo", "mensaje": "Stock por debajo de cero", "referencia_linea": "900"}


def test_f104_r8_avisos_sigrid_con_texto_mensaje_y_linea():
    alta = AltaSigridVista(estado="simulado", avisos=[
        RETENCION, {"codigo": "cabecera_sin_dato"}, SIN_TEXTO,
        {"codigo": "retencion_del_contrato", "mensaje": "m", "referencia_linea": "7"},
    ])
    assert alta.avisos_sigrid == [
        {"codigo": "retencion_del_contrato", "texto": TEXTOS_V83["retencion_del_contrato"],
         "mensaje": RETENCION["mensaje"], "referencia_linea": None},
        {"codigo": "cabecera_sin_dato", "texto": TEXTOS_V83["cabecera_sin_dato"],
         "mensaje": None, "referencia_linea": None},
        {"codigo": "stock_negativo", "texto": None, "mensaje": "Stock por debajo de cero",
         "referencia_linea": "900"},
        {"codigo": "retencion_del_contrato", "texto": TEXTOS_V83["retencion_del_contrato"],
         "mensaje": "m", "referencia_linea": "7"},
    ]


def test_f104_r8_avisos_sigrid_ignora_lo_que_no_es_un_objeto():
    """``avisos`` lo valida pydantic; con ``model_construct`` (sin validar) un
    elemento que no sea dict se ignora, como en ``avisos_resolucion``."""
    alta = AltaSigridVista.model_construct(estado="simulado", avisos=["roto", 3, RETENCION])
    assert [a["codigo"] for a in alta.avisos_sigrid] == ["retencion_del_contrato"]


def test_f104_r8_sin_avisos_lista_vacia():
    assert AltaSigridVista(estado="simulado").avisos_sigrid == []


def _panel(html):
    encontrado = re.search(r'<section[^>]*id="alta-sigrid".*?</section>', html, re.DOTALL)
    return encontrado.group(0) if encontrado else None


def _ficha(documento, alta):
    documento.approved = True
    documento.alta_sigrid_activa = True
    documento.alta_sigrid = alta
    documento.alta_fase = "resultado"
    documento.alta_motivos_linea = []
    return documento


def _avisos_del_panel(panel):
    bloque = re.search(r'<ul class="alta-sigrid-avisos">(.*?)</ul>', panel, re.DOTALL).group(1)
    return re.findall(r"<li[^>]*>.*?</li>", bloque, re.DOTALL)


def test_f104_r8_panel_texto_mensaje_y_codigo_en_title(render_detalle, documento_detalle):
    alta = AltaSigridVista(estado="simulado", modo="simulacion", avisos=[
        RETENCION, {"codigo": "cabecera_sin_dato"},
        {"codigo": "cabecera_sin_dato", "mensaje": "m", "referencia_linea": "7"}, SIN_TEXTO,
    ])
    panel = _panel(render_detalle(_ficha(documento_detalle(), alta)))
    assert "Avisos de Sigrid:" in panel
    assert _avisos_del_panel(panel) == [
        f'<li title="retencion_del_contrato">{TEXTOS_V83["retencion_del_contrato"]}'
        f' · {RETENCION["mensaje"]}</li>',
        f'<li title="cabecera_sin_dato">{TEXTOS_V83["cabecera_sin_dato"]}</li>',
        f'<li title="cabecera_sin_dato">{TEXTOS_V83["cabecera_sin_dato"]} · m (línea 7)</li>',
        "<li><code>stock_negativo</code> · Stock por debajo de cero (línea 900)</li>",
    ]
    assert "<code>retencion_del_contrato</code>" not in panel


def test_f104_r8_aviso_sin_texto_como_hoy(render_detalle, documento_detalle):
    alta = AltaSigridVista(estado="simulado", avisos=[{"codigo": "cod_provisional"}, SIN_TEXTO])
    panel = _panel(render_detalle(_ficha(documento_detalle(), alta)))
    assert _avisos_del_panel(panel) == [
        "<li><code>cod_provisional</code></li>",
        "<li><code>stock_negativo</code> · Stock por debajo de cero (línea 900)</li>",
    ]


def test_f104_r8_el_mensaje_se_escapa(render_detalle, documento_detalle):
    alta = AltaSigridVista(estado="simulado", avisos=[
        {"codigo": "retencion_del_contrato", "mensaje": "<b>5 %</b>"}])
    panel = _panel(render_detalle(_ficha(documento_detalle(), alta)))
    assert "&lt;b&gt;5 %&lt;/b&gt;" in panel and "<b>5 %</b>" not in panel


# ------------------------------------------------------------------ #
# R9 · los avisos no cambian estado ni bloqueo
# ------------------------------------------------------------------ #
_DERIVADOS = ("estado", "estado_texto", "es_error", "bloqueante", "aviso", "motivos_documento")


@pytest.mark.parametrize("estado", ["simulado", "registrado", "revisar", "no_admitido"])
def test_f104_r9_los_avisos_no_cambian_estado_ni_bloqueo(estado):
    base = {"estado": estado, "modo": "real", "sigrid_cod": "AC26/0042",
            "motivos": [{"codigo": "importe_distinto", "detalle": "x"}] if estado == "revisar" else []}
    sin = AltaSigridVista(**base)
    con = AltaSigridVista(**base, avisos=[RETENCION, SIN_DATO])
    assert {c: getattr(con, c) for c in _DERIVADOS} == {c: getattr(sin, c) for c in _DERIVADOS}


@pytest.mark.parametrize(("estado", "clase"), [("simulado", "info"), ("registrado", "warning")])
def test_f104_r9_panel_avisos_v83_solo_bajo_avisos_de_sigrid(render_detalle, documento_detalle,
                                                              estado, clase):
    alta = AltaSigridVista(estado=estado, modo="real", sigrid_cod="AC26/0042",
                           avisos=[RETENCION, SIN_DATO])
    panel = _panel(render_detalle(_ficha(documento_detalle(), alta)))
    assert re.search(rf'<section class="alert alta-sigrid {clase}"', panel)
    assert "Error en el alta en Sigrid" not in panel and "alta-sigrid-motivos" not in panel
    assert len(_avisos_del_panel(panel)) == 2
    assert panel.count(TEXTOS_V83["retencion_del_contrato"]) == 1
