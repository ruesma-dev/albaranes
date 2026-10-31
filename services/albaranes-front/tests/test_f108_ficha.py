# tests/test_f108_ficha.py
"""F-108 · D/E · la ficha pinta la fecha en dd/mm/aaaa, editable y con
calendario (R12, R13), y en solo lectura sin él (R22); las vistas crudas,
con la fecha de la IA tal cual (R23).

Jinja2 sobre la plantilla REAL (``render_detalle`` de ``conftest.py``, con el
filtro ``fecha_albaran_ver`` del dominio) y, para el cableado del filtro en
``build_app``, la ficha servida por el portal con un servicio falso. Sin red
ni BBDD.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from domain.models.review_models import ProviderSnapshot

_RAIZ = Path(__file__).resolve().parent.parent


def _ficha(render_detalle, documento_detalle, *, fecha, aprobado=False, numero="A-1",
           is_editable=True, snapshots=()):
    doc = documento_detalle(is_editable=is_editable).model_copy(update={
        "fecha": fecha, "numero_albaran": numero, "approved": aprobado,
        "provider_snapshots": list(snapshots),
    })
    return render_detalle(doc)


def _input(html, id_):
    encontrado = re.search(rf'<input[^>]*\bid="{id_}"[^>]*>', html)
    assert encontrado, f"no está #{id_}"
    return encontrado.group(0)


# =================================================================== #
# R12, R13 · ficha editable
# =================================================================== #
def test_f108_r12_fecha_editable_en_dd_mm_aaaa(render_detalle, documento_detalle):
    html = _ficha(render_detalle, documento_detalle, fecha="2026-10-09")

    fecha = _input(html, "fecha")
    assert 'type="text"' in fecha
    assert 'value="09/10/2026"' in fecha
    assert 'placeholder="dd/mm/aaaa"' in fecha
    assert 'autocomplete="off"' in fecha
    assert 'aria-describedby="fecha-error"' in fecha
    assert "readonly" not in fecha and "disabled" not in fecha


def test_f108_r12_numero_editable_con_su_tope(render_detalle, documento_detalle):
    html = _ficha(render_detalle, documento_detalle, fecha="2026-10-09", numero="AB-12")

    numero = _input(html, "numero_albaran")
    assert 'value="AB-12"' in numero
    assert 'maxlength="128"' in numero
    assert 'autocomplete="off"' in numero
    assert "readonly" not in numero and "disabled" not in numero


def test_f108_r13_boton_calendario_y_selector(render_detalle, documento_detalle):
    html = _ficha(render_detalle, documento_detalle, fecha="2026-10-09")

    boton = re.search(r'<button[^>]*js-fecha-calendario[^>]*>([^<]*)</button>', html)
    assert boton, "no está el botón del calendario"
    assert boton.group(1).strip() == "Calendario"
    assert 'type="button"' in boton.group(0)
    assert 'title="Elegir la fecha en el calendario"' in boton.group(0)
    assert 'aria-label="Elegir la fecha en el calendario"' in boton.group(0)
    selector = _input(html, "fecha_calendario")
    assert 'type="date"' in selector
    assert 'class="fecha-calendario"' in selector
    assert 'tabindex="-1"' in selector
    error = re.search(r'<small[^>]*\bid="fecha-error"[^>]*>', html)
    assert error and "hidden" in error.group(0)
    # El botón, el texto y el selector van juntos (el calendario se ancla ahí).
    campo = re.search(r'<span class="campo-fecha">(.*?)</span>', html, re.DOTALL)
    assert campo and 'id="fecha"' in campo.group(1) and "js-fecha-calendario" in campo.group(1)
    assert 'id="fecha_calendario"' in campo.group(1)


def test_f108_r12_sin_fecha_el_campo_vacio(render_detalle, documento_detalle):
    html = _ficha(render_detalle, documento_detalle, fecha=None)

    assert 'value=""' in _input(html, "fecha")


def test_f108_r4_fecha_guardada_ilegible_se_ve_tal_cual(render_detalle, documento_detalle):
    html = _ficha(render_detalle, documento_detalle, fecha="ayer por la tarde")

    assert 'value="ayer por la tarde"' in _input(html, "fecha")


def test_f108_r4_fecha_guardada_dd_mm_se_ve_en_dd_mm(render_detalle, documento_detalle):
    html = _ficha(render_detalle, documento_detalle, fecha="5/6/2026")

    assert 'value="05/06/2026"' in _input(html, "fecha")


# =================================================================== #
# R22 · aprobado: solo lectura, sin calendario
# =================================================================== #
def test_f108_r22_aprobado_en_solo_lectura_sin_calendario(render_detalle, documento_detalle):
    html = _ficha(render_detalle, documento_detalle, fecha="2026-10-09", aprobado=True)

    fecha = _input(html, "fecha")
    assert "readonly" in fecha and 'value="09/10/2026"' in fecha
    assert "readonly" in _input(html, "numero_albaran")
    assert "js-fecha-calendario" not in html
    assert 'id="fecha_calendario"' not in html
    assert 'id="fecha-error"' not in html


# =================================================================== #
# R23 · vistas crudas: la fecha que leyó la IA
# =================================================================== #
def test_f108_r23_vista_cruda_con_la_fecha_de_la_ia(render_detalle, documento_detalle):
    snapshot = ProviderSnapshot(id="s1", provider_origin="openai", model_name="m",
                                fecha="2026-10-09", numero_albaran="A-1")
    html = _ficha(render_detalle, documento_detalle, fecha="2026-10-09", is_editable=False,
                  snapshots=[snapshot])

    assert "<dd>2026-10-09</dd>" in html
    assert "<strong>Fecha:</strong> 2026-10-09" in html
    assert "09/10/2026" not in html
    assert "js-fecha-calendario" not in html


# =================================================================== #
# El filtro, cableado en build_app (sin él, la ficha real daría 500)
# =================================================================== #
def test_f108_r4_build_app_registra_el_filtro(monkeypatch, documento_detalle):
    from test_f108_guardado import _ServicioFalso, _PublicadorFalso
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.web import app as modulo_app

    servicio = _ServicioFalso()
    servicio.documento = documento_detalle().model_copy(update={"fecha": "2026-10-09"})
    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: _PublicadorFalso())
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    cliente = TestClient(modulo_app.build_app(ajustes))

    respuesta = cliente.get(f"/documents/{servicio.documento.id}")

    assert respuesta.status_code == 200, respuesta.text[:500]
    assert 'value="09/10/2026"' in _input(respuesta.text, "fecha")


# =================================================================== #
# CSS: el selector, oculto sin display:none (showPicker lo necesita pintado)
# =================================================================== #
def test_f108_r14_css_del_selector_y_de_la_marca():
    css = (_RAIZ / "static" / "styles.css").read_text(encoding="utf-8")

    for regla in (".campo-fecha", ".fecha-calendario", ".campo-no-valido",
                  ".fecha-calendario.visible"):
        assert re.search(rf"(^|[\s,}}]){re.escape(regla)}\s*[{{,]", css, re.MULTILINE), regla
    bloque = re.search(r"\.fecha-calendario\s*\{([^}]*)\}", css)
    assert bloque and "display: none" not in bloque.group(1) and "opacity: 0" in bloque.group(1)


@pytest.mark.parametrize("plantilla", ["documents_list.html"])
def test_f108_r24_el_listado_no_cambia(plantilla):
    """R24 (D3): el listado sigue con la fecha guardada (AAAA-MM-DD)."""
    texto = (_RAIZ / "templates" / plantilla).read_text(encoding="utf-8")

    assert "fecha_albaran_ver" not in texto
