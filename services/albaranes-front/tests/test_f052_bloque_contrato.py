# tests/test_f052_bloque_contrato.py
"""F-052 R23–R26 · el bloque de contrato de la ficha dice la verdad.

Hasta F-052 el bloque decía «No se encontró ningún contrato en el ERP para
la combinación CIF X + obra Y» con el CIF y la obra ACTUALES del albarán,
aunque la búsqueda se hubiera hecho con otros datos (el revisor corrigió
el CIF y guardó: SS-0026122) o hubiera fallado. Ahora el mensaje sale de
``busqueda_contratos`` (``estado_busqueda``, R27):

- R23 ``vigente`` + ``ninguno`` y sin contratos: «No se encontró ningún
  contrato» con el CIF, la obra y la FECHA del rastro.
- R24 ``desfasada``: con qué CIF y obra se buscó, que los datos actuales
  todavía no se han buscado y «Solo volver a buscar», también con
  contratos listados.
- R25 ``error``: la última búsqueda falló y eso no significa que no haya
  contrato (también con contratos listados).
- R26 ``sin_rastro``: no consta con qué datos se buscó, sin afirmar que
  no hay contrato.

Jinja2 sobre la plantilla REAL; sin red ni BBDD.
"""
from __future__ import annotations

import re

import pytest
from domain.models.review_models import (
    BUSQUEDA_ENCONTRADOS,
    BUSQUEDA_ERROR,
    BUSQUEDA_NINGUNO,
    BUSQUEDA_SIN_DATOS,
    ESTADO_BUSQUEDA_DESFASADA,
    ESTADO_BUSQUEDA_ERROR,
    ESTADO_BUSQUEDA_SIN_DATOS,
    ESTADO_BUSQUEDA_SIN_RASTRO,
    ESTADO_BUSQUEDA_VIGENTE,
    BusquedaContratosVista,
    ContratoPayload,
)

CIF_ACTUAL = "B82899550"
CIF_BUSCADO = "B82890580"
OBRA = "0691"
FECHA = "2026-09-30T10:15:00+00:00"
NINGUNO_TXT = "No se encontró ningún contrato"
DESFASE_TXT = "todavía no se han buscado"


def _vista(estado, *, cif=CIF_ACTUAL, obra=OBRA, resultado=BUSQUEDA_NINGUNO):
    if estado == ESTADO_BUSQUEDA_SIN_RASTRO:
        return BusquedaContratosVista(estado=estado)
    return BusquedaContratosVista(
        estado=estado, cif=cif, obra=obra, fecha=FECHA, resultado=resultado,
    )


def _contrato(codigo="CTSU24/0402"):
    return ContratoPayload(
        id=1, codigo_contrato=codigo, nombre_contrato="SUMINISTRO ÁRIDOS",
        cif_proveedor=CIF_ACTUAL, codigo_obra=OBRA,
    )


def _bloque(render_detalle, documento_detalle, vista, *, contratos=(), **extra):
    """HTML de la sección «Contrato asociado» (sin el resto de la ficha)."""
    documento = documento_detalle().model_copy(update={
        "proveedor_cif": CIF_ACTUAL,
        "obra_codigo": OBRA,
        "contratos": list(contratos),
        "busqueda_contratos": vista,
    })
    html = render_detalle(documento, **extra)
    inicio = html.index('<section class="contrato-section">')
    fin = html.index("</section>", inicio)
    return re.sub(r"\s+", " ", html[inicio:fin])


def _texto(bloque: str) -> str:
    return re.sub(r"<[^>]+>", "", bloque)


# --- R23 -------------------------------------------------------------- #
def test_f052_r23_ninguno_vigente_dice_cif_obra_y_fecha(
    render_detalle, documento_detalle,
):
    bloque = _bloque(render_detalle, documento_detalle,
                     _vista(ESTADO_BUSQUEDA_VIGENTE))
    texto = _texto(bloque)
    assert NINGUNO_TXT in texto
    assert CIF_ACTUAL in texto and OBRA in texto
    assert FECHA in texto, "R23 exige la fecha de la búsqueda"
    assert DESFASE_TXT not in texto


def test_f052_r23_vigente_con_contratos_no_pinta_aviso(
    render_detalle, documento_detalle,
):
    bloque = _bloque(render_detalle, documento_detalle,
                     _vista(ESTADO_BUSQUEDA_VIGENTE, resultado=BUSQUEDA_ENCONTRADOS),
                     contratos=[_contrato()])
    assert NINGUNO_TXT not in bloque
    assert 'id="refetch-only-btn"' not in bloque


# --- R24 -------------------------------------------------------------- #
def test_f052_r24_desfase_dice_con_que_se_busco_y_no_el_cif_actual(
    render_detalle, documento_detalle,
):
    """SS-0026122: rastro con el CIF mal leído, CIF actual ya corregido."""
    bloque = _bloque(render_detalle, documento_detalle,
                     _vista(ESTADO_BUSQUEDA_DESFASADA, cif=CIF_BUSCADO))
    texto = _texto(bloque)
    assert DESFASE_TXT in texto
    assert CIF_BUSCADO in texto, "debe decir con qué CIF se buscó"
    assert NINGUNO_TXT not in texto, "no puede afirmar nada del CIF actual"
    assert 'id="refetch-only-btn"' in bloque
    assert "Solo volver a buscar" in texto


def test_f052_r24_desfase_tambien_con_contratos_listados(
    render_detalle, documento_detalle,
):
    bloque = _bloque(render_detalle, documento_detalle,
                     _vista(ESTADO_BUSQUEDA_DESFASADA, cif=CIF_BUSCADO,
                            resultado=BUSQUEDA_ENCONTRADOS),
                     contratos=[_contrato()])
    texto = _texto(bloque)
    assert DESFASE_TXT in texto
    assert CIF_BUSCADO in texto
    assert 'id="refetch-only-btn"' in bloque


def test_f052_r24_desfase_por_obra_dice_la_obra_buscada(
    render_detalle, documento_detalle,
):
    bloque = _bloque(render_detalle, documento_detalle,
                     _vista(ESTADO_BUSQUEDA_DESFASADA, obra="0696"))
    assert "0696" in _texto(bloque)
    assert DESFASE_TXT in _texto(bloque)


# --- R25 -------------------------------------------------------------- #
@pytest.mark.parametrize("con_contratos", [False, True])
def test_f052_r25_error_dice_que_fallo_y_que_no_significa_sin_contrato(
    render_detalle, documento_detalle, con_contratos,
):
    bloque = _bloque(render_detalle, documento_detalle,
                     _vista(ESTADO_BUSQUEDA_ERROR, resultado=BUSQUEDA_ERROR),
                     contratos=[_contrato()] if con_contratos else [])
    texto = _texto(bloque)
    assert "falló" in texto
    assert "no significa que no haya contrato" in texto
    assert NINGUNO_TXT not in texto
    assert 'id="refetch-only-btn"' in bloque


# --- R26 -------------------------------------------------------------- #
@pytest.mark.parametrize("vista", [None, _vista(ESTADO_BUSQUEDA_SIN_RASTRO)],
                         ids=["payload_sin_campo", "sin_rastro"])
def test_f052_r26_sin_rastro_no_consta_y_no_afirma_que_no_hay(
    render_detalle, documento_detalle, vista,
):
    bloque = _bloque(render_detalle, documento_detalle, vista)
    texto = _texto(bloque)
    assert "no consta" in texto
    assert NINGUNO_TXT not in texto
    assert 'id="refetch-only-btn"' in bloque


# --- sin_datos (R21: faltaba CIF u obra) ------------------------------ #
def test_f052_r21_sin_datos_dice_que_no_se_busco(
    render_detalle, documento_detalle,
):
    bloque = _bloque(render_detalle, documento_detalle,
                     _vista(ESTADO_BUSQUEDA_SIN_DATOS, obra=None,
                            resultado=BUSQUEDA_SIN_DATOS))
    texto = _texto(bloque)
    assert "no se buscaron contratos" in texto
    assert NINGUNO_TXT not in texto


def test_f052_r24_los_botones_no_se_duplican(render_detalle, documento_detalle):
    """El JS los busca por id: un solo juego por ficha."""
    bloque = _bloque(render_detalle, documento_detalle,
                     _vista(ESTADO_BUSQUEDA_DESFASADA, cif=CIF_BUSCADO))
    assert bloque.count('id="refetch-only-btn"') == 1
    assert bloque.count('id="save-and-refetch-btn"') == 1
    assert bloque.count('id="refetch-status"') == 1
