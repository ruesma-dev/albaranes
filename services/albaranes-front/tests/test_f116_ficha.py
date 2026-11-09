# tests/test_f116_ficha.py
"""F-116 · B · la ficha editable trae lo que necesita el autoguardado: el
aviso ``#autoguardado-estado`` (R10) y ``data-guardado`` en los cuatro Campos
de cabecera (la fecha en ISO); la de solo lectura, nada de eso (R12). Y las
marcas discretas en ``styles.css`` (R10, R11, R16).

Jinja2 sobre la plantilla REAL (``render_detalle`` de ``conftest.py``). Sin red
ni BBDD.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parent.parent


def _ficha(render_detalle, documento_detalle, *, aprobado=False, is_editable=True, **campos):
    doc = documento_detalle(is_editable=is_editable).model_copy(update={
        "fecha": "2026-10-09", "numero_albaran": "AB-12", "forma_pago": "giro 60",
        "review_notes": "revisar portes", "approved": aprobado, **campos,
    })
    return render_detalle(doc)


def _etiqueta(html, tag, id_):
    encontrado = re.search(rf'<{tag}[^>]*\bid="{id_}"[^>]*>', html)
    assert encontrado, f"no está #{id_}"
    return encontrado.group(0)


def _estado(html):
    return re.search(r'<[a-z]+[^>]*\bid="autoguardado-estado"[^>]*>', html)


# =================================================================== #
# R10 · ficha editable
# =================================================================== #
def test_f116_r10_estado_del_autoguardado_en_la_ficha_editable(render_detalle,
                                                              documento_detalle):
    html = _ficha(render_detalle, documento_detalle)

    estado = _estado(html)
    assert estado, "no está #autoguardado-estado"
    assert 'aria-live="polite"' in estado.group(0)
    # Junto a los botones de la cabecera.
    (acciones,) = [bloque for bloque in re.findall(
        r'<div class="header-actions">(.*?)</div>', html, re.DOTALL) if 'id="save-btn"' in bloque]
    assert 'id="autoguardado-estado"' in acciones


@pytest.mark.parametrize("tag, id_, guardado", [
    ("input", "fecha", "2026-10-09"),
    ("input", "numero_albaran", "AB-12"),
    ("input", "forma_pago", "giro 60"),
    ("textarea", "review_notes", "revisar portes"),
])
def test_f116_r10_lo_guardado_de_cada_campo(render_detalle, documento_detalle, tag, id_,
                                            guardado):
    html = _ficha(render_detalle, documento_detalle)

    assert f'data-guardado="{guardado}"' in _etiqueta(html, tag, id_)


def test_f116_r10_lo_guardado_vacio_si_no_hay(render_detalle, documento_detalle):
    html = _ficha(render_detalle, documento_detalle, fecha=None, numero_albaran=None,
                  forma_pago=None, review_notes=None)

    for tag, id_ in (("input", "fecha"), ("input", "numero_albaran"),
                     ("input", "forma_pago"), ("textarea", "review_notes")):
        assert 'data-guardado=""' in _etiqueta(html, tag, id_)


def test_f116_r10_la_fecha_guardada_tal_cual_aunque_sea_vieja(render_detalle,
                                                             documento_detalle):
    """Lo guardado es lo del servidor: una fecha vieja ``dd/mm/aaaa`` se queda
    así, y el primer autoguardado la deja en ISO (F-108 R25)."""
    html = _ficha(render_detalle, documento_detalle, fecha="05/06/2026")

    assert 'data-guardado="05/06/2026"' in _etiqueta(html, "input", "fecha")


# =================================================================== #
# R12 · solo lectura: nada de autoguardado
# =================================================================== #
@pytest.mark.parametrize("aprobado, is_editable", [(True, True), (False, False)],
                         ids=["aprobado", "vista_cruda"])
def test_f116_r12_sin_autoguardado_fuera_de_la_ficha_editable(render_detalle,
                                                              documento_detalle,
                                                              aprobado, is_editable):
    html = _ficha(render_detalle, documento_detalle, aprobado=aprobado,
                  is_editable=is_editable)

    assert _estado(html) is None
    assert "data-guardado" not in html


# =================================================================== #
# R10, R11, R16 · las marcas, discretas
# =================================================================== #
@pytest.mark.parametrize("selector", [".campo-guardado", ".campo-no-guardado",
                                      "tr.fila-autoguardada"])
def test_f116_r10_marcas_en_la_hoja_de_estilos(selector):
    css = (_RAIZ / "static" / "styles.css").read_text(encoding="utf-8")

    assert re.search(rf"(^|[\s,}}]){re.escape(selector)}[\s,{{>:]", css), selector
