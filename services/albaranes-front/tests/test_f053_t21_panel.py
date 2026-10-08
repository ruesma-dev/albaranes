# tests/test_f053_t21_panel.py
"""F-053 · T21 · lo que el revisor ve del alta en Sigrid (R3, R29–R31, R40).

- R29: la ficha de un documento aprobado enseña el alta: estado, modo, ``cod``
  (en simulación, «se habría creado» con el código provisional), líneas con su
  producto y el total de la previa, motivos (también los de cada línea), avisos
  y adjunto. R30: «Solicitar alta en Sigrid» cuando procede y «Ya lo he anulado
  en Sigrid» con un ``registrado``.
- R40: columna «Producto Sigrid» en la tabla de líneas valoradas: selector solo
  en las sin vincular a registrar (con «por defecto»), vinculadas sin selector.
- R31: el listado enseña el estado del alta de cada aprobado que la tenga.
- R3: con DESDE vacía, nada de esto se pinta ni se lee.

Servicio con dobles para el enriquecimiento; plantillas reales para el resto.
"""
from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest

from domain.models.alta_sigrid_models import (
    AltaSigridVista,
    ConfigAltaSigrid,
    ProductoLinea,
    ProductoOpcion,
)

DESDE = datetime(2026, 10, 1, tzinfo=UTC)
ESTADOS = ("en_curso", "no_admitido", "ya_en_sigrid", "simulado", "revisar", "error",
           "incierto", "registrado", "anulado")

PETICION = {"lineas": [
    {"referencia_linea": "900", "producto": "QA9999", "descripcion": "GRUA 30T",
     "partida": "03.02", "cantidad": 2.0, "precio": 60.0},
    {"referencia_linea": "901", "ctrpro_ide": 700101, "cantidad": 1.0, "precio": 0.0},
]}
RESPUESTA = {"estado": "previsto", "totales": {"totbas": 120.0, "totdoc": 145.2},
             "lineas": [{"referencia_linea": "900", "total": 120.0}]}


def _alta(estado="simulado", modo="simulacion", **campos):
    base = {
        "estado": estado, "modo": modo, "sigrid_cod": "AC26/0042", "sigrid_con_ide": 42,
        "adjunto_estado": None, "peticion": PETICION, "respuesta": RESPUESTA,
        "motivos": [{"codigo": "importe_distinto", "detalle": "120 frente a 118",
                     "referencia_linea": "900"},
                    {"codigo": "fecha_no_plausible", "detalle": "2025-01-01"}],
        "avisos": [{"codigo": "stock_negativo", "mensaje": "Stock por debajo de cero"}],
        "intentos": 1,
    }
    base.update(campos)
    return AltaSigridVista(**base)


def _con_alta(documento, alta, *, puede=False, aprobado=True, productos=None):
    documento.approved = aprobado
    documento.alta_sigrid_activa = True
    documento.alta_sigrid = alta
    documento.alta_puede_solicitar = puede
    documento.productos_sigrid = productos or {}
    documento.productos_admitidos = [
        ProductoOpcion(codigo="MA9999", nombre="Suministro de materiales"),
        ProductoOpcion(codigo="QA9999", nombre="Alquiler de maquinaria"),
        ProductoOpcion(codigo="XA9999", nombre="Alquiler de medios auxiliares"),
    ]
    return documento


def _panel(html):
    encontrado = re.search(r'<section[^>]*id="alta-sigrid".*?</section>', html, re.DOTALL)
    return encontrado.group(0) if encontrado else None


# =================================================================== #
# R3 · DESDE vacía: nada
# =================================================================== #
def test_f053_r3_sin_desde_la_ficha_no_pinta_ni_panel_ni_producto(render_detalle, documento_detalle,
                                                                  linea_valorada, fila_detalle):
    documento = documento_detalle(lineas_valoracion=[linea_valorada()], display=[fila_detalle()])
    documento.approved = True
    html = render_detalle(documento)
    assert _panel(html) is None
    assert 'data-col="producto"' not in html
    assert "Solicitar alta en Sigrid" not in html


def test_f053_r3_servicio_sin_desde_no_lee_el_alta():
    from application.services.review_service import ReviewService

    class _Repo:
        def get_document_detail(self, document_id, *, view_mode):
            return "detalle"

        def __getattr__(self, nombre):
            raise AssertionError(f"con DESDE vacía no se llama a {nombre}")

    assert ReviewService(_Repo(), "r", None, ConfigAltaSigrid()).get_document("d") == "detalle"


# =================================================================== #
# Servicio: enriquecimiento de la ficha
# =================================================================== #
class _RepoFicha:
    def __init__(self, documento, alta):
        self.documento = documento
        self.alta = alta

    def get_document_detail(self, document_id, *, view_mode):
        return self.documento

    def leer_alta_sigrid(self, document_id):
        return self.alta

    def estado_aprobacion(self, document_id):
        return {"approved": True, "approved_at_utc": "2026-10-05T10:00:00+00:00",
                "is_active": True}

    def lineas_producto_sigrid(self, document_id):
        return [{"id": 900, "producto_sigrid": None, "importe_calculado": 120.0,
                 "matched_contrato_line_id": None, "derived_contrato_line_id": None,
                 "sigrid_ide": None, "contrato_linea": None, "codigo_producto": None,
                 "contexto_linea_json": None, "contrato_valoracion": "C-001"}]


def test_f053_r29_servicio_completa_la_ficha_con_el_alta(documento_detalle):
    from application.services.review_service import ReviewService

    documento = documento_detalle(clasificacion={"tipologia": "alquiler_maquinaria",
                                                 "tipologia_mixta": False})
    documento.approved = True
    alta = _alta("error")
    servicio = ReviewService(_RepoFicha(documento, alta), "r", None,
                             ConfigAltaSigrid(desde=DESDE))

    ficha = servicio.get_document(documento.id)

    assert ficha.alta_sigrid_activa is True
    assert ficha.alta_sigrid == alta
    assert ficha.alta_puede_solicitar is True  # error: se puede repetir
    assert ficha.productos_sigrid[900].codigo == "QA9999"  # familia del documento
    assert ficha.productos_sigrid[900].defecto == "QA9999"
    assert [o.codigo for o in ficha.productos_admitidos] == ["MA9999", "QA9999", "XA9999"]
    assert ficha.productos_admitidos[1].nombre == "Alquiler de maquinaria"


def test_f053_r29_servicio_no_toca_las_vistas_de_proveedor(documento_detalle):
    from application.services.review_service import ReviewService

    documento = documento_detalle()
    documento.view_mode = "openai"
    servicio = ReviewService(_RepoFicha(documento, _alta()), "r", None,
                             ConfigAltaSigrid(desde=DESDE))
    assert servicio.get_document(documento.id, view_mode="openai").alta_sigrid_activa is False


def test_f053_r29_servicio_documento_inexistente():
    from application.services.review_service import ReviewService

    servicio = ReviewService(_RepoFicha(None, None), "r", None, ConfigAltaSigrid(desde=DESDE))
    assert servicio.get_document("no") is None


# =================================================================== #
# R29 · R30 · panel
# =================================================================== #
@pytest.mark.parametrize("estado", ESTADOS)
@pytest.mark.parametrize("modo", ["simulacion", "real"])
def test_f053_r29_panel_con_cada_estado_y_modo(render_detalle, documento_detalle, estado, modo):
    alta = _alta(estado, modo)
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    assert panel is not None
    assert f'data-estado="{estado}"' in panel
    assert alta.estado_texto in panel
    assert ("Simulación" in panel) is (modo == "simulacion")
    assert ("Real" in panel) is (modo == "real")
    assert "AC26/0042" in panel


def test_f053_r29_panel_en_simulacion_dice_se_habria_creado(render_detalle, documento_detalle):
    panel = _panel(render_detalle(_con_alta(documento_detalle(), _alta("simulado"))))
    assert "se habría creado" in panel and "AC26/0042" in panel
    assert "provisional" in panel


def test_f053_r29_panel_registrado_dice_el_cod_y_el_aviso_de_bloqueo(render_detalle, documento_detalle):
    panel = _panel(render_detalle(_con_alta(documento_detalle(), _alta("registrado", "real"))))
    assert "Registrado en Sigrid como AC26/0042" in panel
    assert "Ya lo he anulado en Sigrid" in panel


def test_f053_r29_panel_lineas_producto_total_motivos_avisos(render_detalle, documento_detalle):
    panel = _panel(render_detalle(_con_alta(
        documento_detalle(), _alta("revisar", adjunto_estado="error"))))
    assert "QA9999" in panel and "GRUA 30T" in panel and "03.02" in panel
    assert "ctrpro 700101" in panel
    assert "120,00 €" in panel and "145,20 €" in panel          # total y total con IVA
    assert "importe_distinto" in panel and "120 frente a 118" in panel   # motivo de línea
    assert "fecha_no_plausible" in panel                      # motivo del documento
    assert "stock_negativo" in panel and "Stock por debajo de cero" in panel
    assert "Adjunto" in panel and "error" in panel


def test_f053_r29_panel_linea_sin_partida_es_almacen(render_detalle, documento_detalle):
    peticion = {"lineas": [{"referencia_linea": "9", "producto": "MA9999", "cantidad": 1,
                            "precio": 1}]}
    panel = _panel(render_detalle(_con_alta(documento_detalle(), _alta(peticion=peticion))))
    assert "almacén" in panel


def test_f053_r29_panel_sin_alta_todavia(render_detalle, documento_detalle):
    panel = _panel(render_detalle(_con_alta(documento_detalle(), None, puede=True)))
    assert panel is not None and "Sin alta en Sigrid" in panel
    assert "Solicitar alta en Sigrid" in panel


def test_f053_r29_panel_solo_en_aprobados(render_detalle, documento_detalle):
    html = render_detalle(_con_alta(documento_detalle(), None, aprobado=False, puede=False))
    assert _panel(html) is None


@pytest.mark.parametrize("puede", [True, False])
def test_f053_r30_boton_solicitar_solo_cuando_procede(render_detalle, documento_detalle, puede):
    panel = _panel(render_detalle(_con_alta(documento_detalle(), _alta("error"), puede=puede)))
    formulario = re.search(r'<form[^>]*action="/documents/[^"]+/alta-sigrid/solicitar"', panel)
    assert (formulario is not None) is puede


@pytest.mark.parametrize("estado", ESTADOS)
def test_f053_r28_boton_anulado_solo_con_registrado(render_detalle, documento_detalle, estado):
    panel = _panel(render_detalle(_con_alta(documento_detalle(), _alta(estado))))
    formulario = re.search(r'action="/documents/[^"]+/alta-sigrid/verificar-anulacion"', panel)
    assert (formulario is not None) is (estado == "registrado")


@pytest.mark.parametrize("estado", ["en_curso", "incierto", "registrado"])
def test_f053_r25_panel_avisa_del_bloqueo(render_detalle, documento_detalle, estado):
    panel = _panel(render_detalle(_con_alta(documento_detalle(), _alta(estado))))
    assert "corrígelo en Sigrid" in panel


# =================================================================== #
# R40 · columna «Producto Sigrid»
# =================================================================== #
def _celda_producto(html, vid):
    fila = re.search(
        rf'<tr[^>]*data-for-valuation-line-id="{vid}"[^>]*>.*?</tr>', html, re.DOTALL,
    ).group(0)
    celda = re.search(r'<td[^>]*data-col="producto"[^>]*>(.*?)</td>', fila, re.DOTALL)
    return celda.group(1) if celda else None


def _ficha_con_producto(documento_detalle, linea_valorada, fila_detalle, producto):
    documento = documento_detalle(lineas_valoracion=[linea_valorada()], display=[fila_detalle()])
    return _con_alta(documento, None, productos={900: producto})


def test_f053_r40_sin_vincular_a_registrar_tiene_selector(render_detalle, documento_detalle,
                                                         linea_valorada, fila_detalle):
    producto = ProductoLinea(valuation_line_id=900, vinculada=False, a_registrar=True,
                             codigo="QA9999", defecto="QA9999", por_defecto=True)
    html = render_detalle(_ficha_con_producto(documento_detalle, linea_valorada, fila_detalle,
                                              producto))
    assert '<th data-col="producto"' in html
    celda = _celda_producto(html, 900)
    assert 'class="cell-input js-producto-sigrid"' in celda
    assert 'data-valuation-line-id="900"' in celda
    assert re.search(r'<option value="" selected>Por defecto \(QA9999', celda)
    for codigo in ("MA9999", "QA9999", "XA9999"):
        assert f'<option value="{codigo}"' in celda


def test_f053_r40_elegido_sale_seleccionado(render_detalle, documento_detalle,
                                            linea_valorada, fila_detalle):
    producto = ProductoLinea(valuation_line_id=900, vinculada=False, a_registrar=True,
                             elegido="XA9999", codigo="XA9999", defecto="MA9999")
    celda = _celda_producto(render_detalle(_ficha_con_producto(
        documento_detalle, linea_valorada, fila_detalle, producto)), 900)
    assert '<option value="XA9999" selected>' in celda
    assert '<option value="" >Por defecto (MA9999' in celda


def test_f053_r40_vinculada_sin_selector(render_detalle, documento_detalle,
                                         linea_valorada, fila_detalle):
    producto = ProductoLinea(valuation_line_id=900, vinculada=True, a_registrar=True,
                             codigo="HA25")
    celda = _celda_producto(render_detalle(_ficha_con_producto(
        documento_detalle, linea_valorada, fila_detalle, producto)), 900)
    assert "<select" not in celda and "HA25" in celda and "contrato" in celda


def test_f053_r40_sin_importe_no_se_registra(render_detalle, documento_detalle,
                                             linea_valorada, fila_detalle):
    producto = ProductoLinea(valuation_line_id=900, vinculada=False, a_registrar=False,
                             codigo="MA9999", defecto="MA9999", por_defecto=True)
    celda = _celda_producto(render_detalle(_ficha_con_producto(
        documento_detalle, linea_valorada, fila_detalle, producto)), 900)
    assert "<select" not in celda and "no se registra" in celda


def test_f053_r40_el_js_publica_el_producto_elegido():
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "static" / "app.js").read_text(encoding="utf-8")
    assert ".js-producto-sigrid" in js
    assert "/lineas-valoradas/" in js and "/producto-sigrid" in js
    assert "producto: sel.value || null" in js


# =================================================================== #
# R31 · listado
# =================================================================== #
def _listado(monkeypatch, *, desde, alta_estado, aprobado=True):
    from fastapi.testclient import TestClient

    from config.settings import Settings
    from domain.models.review_models import DocumentListItem, PaginatedDocuments
    from interface_adapters.web import app as modulo_app

    item = DocumentListItem(id="d1", source_filename="a.pdf", provider_origin="merge",
                            created_at_utc="2026-10-08T08:00:00+00:00", approved=aprobado,
                            valorado=True, alta_estado=alta_estado)

    class _Servicio:
        def initialize(self):
            return True

        def list_documents(self, filters):
            return PaginatedDocuments(items=[item], total=1, page=1, page_size=25,
                                      total_pages=1, approved_count=1, pending_count=0,
                                      review_required_count=0)

    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: _Servicio())
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x",
                                       alta_sigrid_desde_utc=desde)
    return TestClient(modulo_app.build_app(ajustes)).get("/documents?approved=all").text


@pytest.mark.parametrize("estado", ESTADOS)
def test_f053_r31_listado_ensena_el_estado_del_alta(monkeypatch, estado):
    html = _listado(monkeypatch, desde="2026-10-01T00:00:00Z", alta_estado=estado)
    pastilla = re.search(r'<span class="alta-sigrid-pill[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    assert pastilla is not None
    assert f"estado-{estado}" in pastilla.group(0)
    assert "Sigrid" in pastilla.group(1)


def test_f053_r31_listado_sin_alta_no_pinta_nada(monkeypatch):
    html = _listado(monkeypatch, desde="2026-10-01T00:00:00Z", alta_estado=None)
    assert "alta-sigrid-pill" not in html


def test_f053_r3_listado_sin_desde_no_pinta_el_alta(monkeypatch):
    html = _listado(monkeypatch, desde="", alta_estado="registrado")
    assert "alta-sigrid-pill" not in html


def test_f053_r31_textos_de_cada_estado():
    from domain.models.review_models import DocumentListItem

    textos = set()
    for estado in ESTADOS:
        texto = _alta(estado).estado_texto
        assert texto and texto != estado
        assert DocumentListItem(id="d", source_filename="a", provider_origin="m",
                                created_at_utc="t", alta_estado=estado).alta_estado_texto == texto
        textos.add(texto)
    assert len(textos) == len(ESTADOS)
    assert _alta("desconocido").estado_texto == "desconocido"
