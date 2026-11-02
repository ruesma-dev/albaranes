# tests/test_f114_plantilla.py
"""F-114 · plantilla y CSS del check «Solo de la obra» (R1, R9).

El combo de proveedor pasa de un ``<label>`` a un ``div.campo-combo`` con una
cabecera (rótulo + check): dentro de un ``<label>`` el check sería su primer
control y un clic en el rótulo lo conmutaría (design §4). Render real con
``render_detalle`` (conftest) y texto del CSS.
"""
from __future__ import annotations

import re
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[1]


def _bloque_combo(html: str) -> str:
    inicio = html.index('class="full-width campo-combo"')
    return html[inicio:html.index('id="proveedor_nombre"', inicio)]


def test_f114_r1_editable_pinta_el_check_marcado(render_detalle, documento_detalle):
    html = render_detalle(documento_detalle())
    bloque = _bloque_combo(html)
    assert re.search(
        r'<input type="checkbox" id="proveedor_solo_obra" checked>\s*Solo de la obra', bloque
    )
    assert '<label class="check-inline">' in bloque
    assert 'id="proveedor_combo_rotulo"' in bloque
    assert "Elegir proveedor (con contrato en la obra · Sigrid) — escribe para buscar" in bloque
    assert 'data-solo-obra-check="proveedor_solo_obra"' in bloque
    assert 'data-endpoint-todos="/api/sigrid/proveedores/todos"' in bloque
    # Lo de hoy sigue igual (R2).
    assert 'data-kind="proveedor"' in bloque
    assert 'data-endpoint="/api/sigrid/proveedores"' in bloque
    assert 'data-obra-input="obra_codigo"' in bloque


def test_f114_r1_el_check_no_va_dentro_de_un_label_con_el_combo(render_detalle, documento_detalle):
    html = render_detalle(documento_detalle())
    bloque = _bloque_combo(html)
    cabecera = bloque[:bloque.index('<div class="combo"')]
    # El único <label> de la cabecera es el del check; el combo queda fuera.
    assert cabecera.count("<label") == 1
    assert "</label>" in cabecera
    # Y el envoltorio ya no es el <label class="full-width"> de antes.
    assert '<label class="full-width">\n                        <span>Elegir proveedor' not in html


def test_f114_r1_solo_lectura_no_pinta_ni_check_ni_combo(render_detalle, documento_detalle):
    html = render_detalle(documento_detalle(is_editable=False))
    assert "proveedor_solo_obra" not in html
    assert "campo-combo" not in html
    assert 'data-kind="proveedor"' not in html


def test_f114_r9_el_check_sale_marcado_en_cada_carga():
    """R9: marcado en el HTML (nada de plantilla condicional ni estado guardado)."""
    plantilla = (_RAIZ / "templates" / "document_detail.html").read_text(encoding="utf-8")
    (linea,) = [l for l in plantilla.splitlines() if 'id="proveedor_solo_obra"' in l]
    assert " checked" in linea and "{%" not in linea and "{{" not in linea


def test_f114_css_campo_combo_y_check_inline():
    css = (_RAIZ / "static" / "styles.css").read_text(encoding="utf-8")
    assert re.search(r"\.campo-combo\s*\{[^}]*display:\s*flex;[^}]*flex-direction:\s*column;", css)
    assert re.search(r"\.campo-combo-cabecera\s*\{[^}]*justify-content:\s*space-between;", css)
    assert re.search(r"\.check-inline\s*\{[^}]*display:\s*inline-flex;", css)
    # El check no hereda el width:100% de los input del formulario.
    assert re.search(r"\.check-inline input\s*\{[^}]*width:\s*auto;", css)
