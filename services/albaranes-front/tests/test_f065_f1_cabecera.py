# tests/test_f065_f1_cabecera.py
"""F-065 · fase 1 · R1–R5: guardar la cabecera solo guarda la cabecera y un
albarán aprobado es de solo lectura.

El caso que lo origina (METALFIRE, CTSU25/0359): la administrativa dejó 6 y 7
en dos filas Contrato de 8 y 10, trajo una tercera con 5 y «Guardar y
aprobar» devolvió las dos primeras a 8 y 10 (23 puertas en vez de 18): el PUT
reenviaba las blancas y ``_recalc_valuation_importes`` pisaba las filas con
su cantidad (``progress/explore_F-065.md`` §1).

Repositorio real sobre SQLite (``f065_bbdd``), plantilla real y ``build_app``
real con un servicio falso. Sin red ni BBDD.
"""
from __future__ import annotations

import re

import pytest
from domain.models.alta_sigrid_models import AlbaranBloqueadoError
from domain.models.review_models import MergeDocumentUpdatePayload
from f053_sv4_bbdd import foto, poner_alta
from f065_bbdd import (
    DOC,
    construir,
    documento,
    ejecutar,
    fila,
    filas,
    repositorio,
    total,
)

AVISO_APROBADO = "Albarán aprobado: desapruébalo para editar"

#: Las blancas tal como las reenviaba el front viejo (``app.js`` en caché).
BLANCAS = [
    {"id": 701, "cantidad": 8.0, "concepto": "PUERTA EI2-60", "precio": 115.0,
     "precio_neto": 920.0},
    {"id": 702, "cantidad": 10.0, "concepto": "PUERTA EI2-90", "precio": 115.0,
     "precio_neto": 1150.0},
    {"id": 703, "cantidad": 1.0, "concepto": "PORTES", "precio": 50.0, "precio_neto": 50.0},
]


def _guardar(repo, monkeypatch, **campos):
    monkeypatch.setattr(repo, "get_document_detail", lambda document_id: "detalle")
    return repo.update_document_y_transicion(
        document_id=DOC, payload=MergeDocumentUpdatePayload(**campos),
    )


def _editada_a_mano(motor):
    """Las filas 11 y 12 como las dejó el PATCH de la administrativa."""
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = 6, "
             "cantidad_convertida = 6, importe_calculado = 690, "
             "importe_source = 'calculated' WHERE id = 11")
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = 7, "
             "cantidad_convertida = 7, importe_calculado = 805, "
             "importe_source = 'calculated' WHERE id = 12")
    ejecutar(motor, "UPDATE albaran_valuations SET total_valorado = 1545 WHERE id = 'f065-val-1'")


# =================================================================== #
# R1 · el PUT no toca las líneas
# =================================================================== #
def test_f065_r1_put_con_las_blancas_no_toca_las_filas(monkeypatch):
    motor = construir()
    _editada_a_mano(motor)
    antes = foto(motor)

    _guardar(repositorio(motor), monkeypatch, numero_albaran="A-2", lines=BLANCAS)

    despues = foto(motor)
    for tabla in ("albaran_line_valuations", "albaran_valuations",
                  "contrato_lines_derived", "albaran_lines_merge"):
        assert despues[tabla] == antes[tabla], tabla
    assert documento(motor)["numero_albaran"] == "A-2"


def test_f065_r1_put_sin_lineas_no_borra_las_blancas(monkeypatch):
    """Con ``lines`` vacía el PUT viejo borraba las blancas (y, por la FK, la
    valoración). Ahora ``lines`` se ignora."""
    motor = construir()
    antes = foto(motor)

    _guardar(repositorio(motor), monkeypatch, numero_albaran="A-3", lines=[])

    assert foto(motor)["albaran_lines_merge"] == antes["albaran_lines_merge"]
    assert foto(motor)["albaran_line_valuations"] == antes["albaran_line_valuations"]


def test_f065_r1_put_ignora_valuation_line_updates(monkeypatch):
    motor = construir()
    antes = fila(motor, 13)

    _guardar(repositorio(motor), monkeypatch, valuation_line_updates=[{
        "valuation_line_id": 13, "cantidad_albaran": 99.0, "precio_unitario_final": 1.0,
        "importe_calculado": 99.0, "codigo_partida_final": "09.09",
    }])

    assert fila(motor, 13) == antes


def test_f065_r1_el_payload_viejo_sigue_validando():
    """Un ``app.js`` en caché manda ``lines`` y ``valuation_line_updates``: el
    modelo los acepta (y el repositorio los ignora) en vez de dar un 422."""
    payload = MergeDocumentUpdatePayload(
        lines=BLANCAS, valuation_line_updates=[{"valuation_line_id": 13}],
    )
    assert payload.lines[0].id == 701


def test_f065_r11_el_recalculo_del_put_ya_no_existe():
    from infrastructure.database.review_repository import AlbaranReviewRepository

    for nombre in ("_recalc_valuation_importes", "_cantidades_del_payload",
                   "_descuentos_del_payload", "_apply_valuation_line_updates_in_session"):
        assert not hasattr(AlbaranReviewRepository, nombre), nombre


# =================================================================== #
# R2 · METALFIRE
# =================================================================== #
def test_f065_r2_metalfire_seis_siete_y_cinco_tras_guardar_y_aprobar(monkeypatch):
    motor = construir()
    repo = repositorio(motor)

    assert repo.update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos={"cantidad": 6.0}, bloquear=True)
    assert repo.update_line_conciliacion(
        document_id=DOC, valuation_line_id=12, campos={"cantidad": 7.0}, bloquear=True)
    nuevas = repo.add_valuation_lines_from_contrato(document_id=DOC, lineas=[(503, 5.0)])
    _, paso = _guardar(repo, monkeypatch, approved=True, approved_by="ana", lines=BLANCAS)

    assert paso is True
    cantidades = {f["id"]: (f["cantidad_albaran"], f["cantidad_convertida"])
                  for f in filas(motor)}
    assert cantidades[11] == (6.0, 6.0)
    assert cantidades[12] == (7.0, 7.0)
    assert cantidades[nuevas[0]] == (5.0, 5.0)
    puertas = sum(cc for vid, (_, cc) in cantidades.items() if vid != 13)
    assert puertas == 18.0
    assert total(motor) == pytest.approx(sum(f["importe_calculado"] for f in filas(motor)))
    assert total(motor) == pytest.approx(690 + 805 + 575 + 50)


# =================================================================== #
# R3 · el PUT nunca desaprueba
# =================================================================== #
def test_f065_r3_put_sin_aprobar_sobre_un_aprobado_no_lo_desaprueba(monkeypatch):
    motor = construir(aprobado=True)
    antes = documento(motor)

    from domain.models.review_models import AlbaranAprobadoError

    with pytest.raises(AlbaranAprobadoError):
        _guardar(repositorio(motor), monkeypatch, numero_albaran="OTRO", approved=False)

    assert documento(motor) == antes
    assert antes["approved"] in (1, True)


def test_f065_r3_put_aprobando_un_pendiente_guarda_y_aprueba(monkeypatch):
    motor = construir()

    _, paso = _guardar(repositorio(motor), monkeypatch, numero_albaran="A-9",
                       approved=True, approved_by="ana")

    assert paso is True
    doc = documento(motor)
    assert doc["approved"] in (1, True) and doc["numero_albaran"] == "A-9"


def test_f065_r3_put_sin_aprobar_de_un_pendiente_no_toca_la_aprobacion(monkeypatch):
    motor = construir()
    ejecutar(motor, "UPDATE albaran_documents_merge SET approved_by = 'nadie' WHERE id = :d",
             d=DOC)

    _guardar(repositorio(motor), monkeypatch, numero_albaran="A-8", approved=False)

    assert documento(motor)["approved_by"] == "nadie"


# =================================================================== #
# R4 · aprobado ⇒ toda escritura de sv4 responde 409, sin cambios
# =================================================================== #
ESCRITURAS = {
    "guardar": lambda r: r.update_document_y_transicion(
        document_id=DOC, payload=MergeDocumentUpdatePayload(numero_albaran="OTRO")),
    "guardar_y_aprobar": lambda r: r.update_document_y_transicion(
        document_id=DOC, payload=MergeDocumentUpdatePayload(approved=True)),
    "editar": lambda r: r.update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos={"descripcion": "OTRA"}),
    "reapuntar": lambda r: r.set_line_conciliacion(
        document_id=DOC, valuation_line_id=13, mode="contract_line",
        matched_contrato_line_id=501),
    "borrar_linea": lambda r: r.remove_line_valuation(document_id=DOC, valuation_line_id=12),
    "casar_blanca": lambda r: r.add_conciliacion_for_merge_line(
        document_id=DOC, merge_line_id=703, mode="nueva"),
    "anadir": lambda r: r.add_standalone_valuation_line(document_id=DOC),
    "traer": lambda r: r.add_valuation_lines_from_contrato(
        document_id=DOC, lineas=[(503, 5.0)]),
    "almacen": lambda r: r.asignar_almacen(document_id=DOC, valuation_line_ids=[12]),
    "almacen_todas": lambda r: r.asignar_almacen(document_id=DOC, valuation_line_ids=None),
    "deshacer": lambda r: r.undo_last(document_id=DOC),
    "producto": lambda r: r.guardar_producto_sigrid(
        document_id=DOC, valuation_line_id=13, producto="MA9999"),
    "bloquear": lambda r: r.bloquear_linea(document_id=DOC, valuation_line_id=11),
    "desbloquear": lambda r: r.desbloquear_linea(document_id=DOC, valuation_line_id=11),
}


@pytest.mark.parametrize("operacion", sorted(ESCRITURAS))
def test_f065_r4_escribir_en_un_aprobado_se_rechaza_sin_cambios(operacion):
    from domain.models.review_models import AlbaranAprobadoError

    motor = construir(aprobado=True)
    antes = foto(motor)

    with pytest.raises(AlbaranAprobadoError) as error:
        ESCRITURAS[operacion](repositorio(motor))

    assert error.value.document_id == DOC
    assert error.value.aviso == AVISO_APROBADO == str(error.value)
    assert foto(motor) == antes


@pytest.mark.parametrize("operacion", ["guardar", "editar", "almacen_todas", "deshacer"])
def test_f065_r4_con_alta_bloqueante_manda_el_aviso_del_alta(operacion):
    """El cerrojo de F-053 va primero: con alta bloqueante el aviso es el suyo."""
    motor = construir(aprobado=True, con_altas=True)
    poner_alta(motor, "registrado", document_id=DOC, cod="AC26/9")

    with pytest.raises(AlbaranBloqueadoError):
        ESCRITURAS[operacion](repositorio(motor))


def test_f065_r4_desaprobar_un_aprobado_si_se_puede():
    motor = construir(aprobado=True)

    repositorio(motor).set_approved(document_id=DOC, approved=False, approved_by=None)

    assert documento(motor)["approved"] in (0, False)


def test_f065_r4_el_cerrojo_comprueba_aprobado_en_todos_los_metodos_que_escriben():
    """Guardián estructural: cada método que escribe pasa por
    ``_exigir_editable`` (que incluye el cerrojo de F-053)."""
    import inspect

    from infrastructure.database.review_repository import AlbaranReviewRepository

    for metodo in (
        "update_document_y_transicion", "undo_last", "update_line_conciliacion",
        "set_line_conciliacion", "remove_line_valuation", "add_conciliacion_for_merge_line",
        "add_standalone_valuation_line", "add_valuation_lines_from_contrato",
        "asignar_almacen", "guardar_producto_sigrid", "_marcar_bloqueada",
    ):
        fuente = inspect.getsource(getattr(AlbaranReviewRepository, metodo))
        assert "self._exigir_editable(session, document_id" in fuente, metodo


# --- R4 en el portal: 409 con el aviso ------------------------------- #
class _ServicioAprobado:
    def __init__(self):
        self.llamadas: list[str] = []

    def initialize(self):
        return True

    def get_document(self, document_id, view_mode=None):
        from domain.models.review_models import DocumentDetailPayload

        return DocumentDetailPayload(
            id=DOC, source_filename="x.pdf", provider_origin="merge", model_name="m",
            created_at_utc="2026-10-09", selected_contrato_codigo="CT/1",
            lines=[{"id": 1, "concepto": "X"}], approved=True,
        )

    def __getattr__(self, nombre):
        def _lanza(*args, **kwargs):
            from domain.models.review_models import AlbaranAprobadoError

            self.llamadas.append(nombre)
            raise AlbaranAprobadoError(DOC)
        return _lanza


def _cliente(monkeypatch, servicio):
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.web import app as modulo_app

    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    return TestClient(modulo_app.build_app(ajustes), follow_redirects=False)


RUTAS = [
    ("put", f"/api/documents/{DOC}", {"numero_albaran": "B"}, "guardar"),
    ("patch", f"/api/documents/{DOC}/lines/12/conciliacion/campos?bloquear=1",
     {"cantidad": 3}, "update_line_conciliacion"),
    ("patch", f"/api/documents/{DOC}/lines/12/conciliacion", {"mode": "nueva"},
     "set_line_conciliacion"),
    ("delete", f"/api/documents/{DOC}/lines/12/conciliacion", None, "remove_line_conciliacion"),
    ("post", f"/api/documents/{DOC}/lines/12/almacen", None, "asignar_almacen_linea"),
    ("post", f"/api/documents/{DOC}/almacen-todas", None, "asignar_almacen_todas_con_saltos"),
    ("post", f"/api/documents/{DOC}/lines/standalone", None, "add_standalone_valuation_line"),
    ("post", f"/api/documents/{DOC}/lines/from-contrato",
     {"lineas": [{"contrato_line_id": 503, "cantidad": 5}]},
     "add_valuation_lines_from_contrato"),
    ("post", f"/api/documents/{DOC}/lines/12/bloquear", None, "bloquear_linea"),
    ("post", f"/api/documents/{DOC}/lines/12/desbloquear", None, "desbloquear_linea"),
    ("post", f"/api/documents/{DOC}/re-fetch-contratos", None, "comprobar_editable"),
    ("post", f"/api/documents/{DOC}/valuate", None, "comprobar_editable"),
]


@pytest.mark.parametrize("metodo, ruta, cuerpo, llamada", RUTAS,
                         ids=[r[3] + ":" + r[1].split("?")[0].rsplit("/", 1)[-1] for r in RUTAS])
def test_f065_r4_el_portal_responde_409_con_el_aviso(monkeypatch, metodo, ruta, cuerpo, llamada):
    servicio = _ServicioAprobado()
    kwargs = {"json": cuerpo} if cuerpo is not None else {}

    respuesta = getattr(_cliente(monkeypatch, servicio), metodo)(ruta, **kwargs)

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["detail"] == AVISO_APROBADO
    assert servicio.llamadas == [llamada]


def test_f065_r4_deshacer_en_un_aprobado_responde_409(monkeypatch):
    servicio = _ServicioAprobado()

    respuesta = _cliente(monkeypatch, servicio).post(f"/api/undo?document_id={DOC}")

    assert respuesta.status_code == 409
    assert respuesta.json() == {"ok": False, "error": AVISO_APROBADO, "detail": AVISO_APROBADO}


def test_f065_r4_el_producto_en_un_aprobado_responde_409(monkeypatch):
    servicio = _ServicioAprobado()

    respuesta = _cliente(monkeypatch, servicio).post(
        f"/api/documents/{DOC}/lineas-valoradas/12/producto-sigrid", json={"producto": None})

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == AVISO_APROBADO


# =================================================================== #
# R5 · ficha aprobada en solo lectura con «Desaprobar para editar»
# =================================================================== #
def _ficha(render_detalle, documento_detalle, linea_valorada, fila_detalle, aprobado):
    doc = documento_detalle(lineas_valoracion=[linea_valorada()], display=[fila_detalle()])
    doc = doc.model_copy(update={"approved": aprobado})
    return render_detalle(doc)


def test_f065_r5_plantilla_aprobado_en_solo_lectura(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = _ficha(render_detalle, documento_detalle, linea_valorada, fila_detalle, True)

    assert 'id="save-btn"' not in html
    assert 'id="approve-btn"' not in html
    assert "js-cedit" not in html
    assert 'id="valuate-btn"' not in html
    assert 'id="add-line-btn"' not in html
    assert 'id="save-all-lines-btn"' not in html
    formulario = re.search(r'<form id="([^"]+)"[^>]*action="/documents/[^"]*/unapprove"'
                           r'[^>]*>.*?</form>', html, re.DOTALL)
    assert formulario, "no está el formulario de desaprobar"
    assert 'name="volver" value="ficha"' in formulario.group(0)
    # El botón va en la cabecera de la ficha (un form no puede ir dentro de
    # otro): apunta al formulario con ``form=``.
    boton = re.search(rf'<button[^>]*form="{formulario.group(1)}"[^>]*>([^<]*)</button>', html)
    assert boton and boton.group(1) == "Desaprobar para editar"
    assert re.search(r'<input[^>]*id="numero_albaran"[^>]*readonly', html)


def test_f065_r5_plantilla_pendiente_sigue_editable(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = _ficha(render_detalle, documento_detalle, linea_valorada, fila_detalle, False)

    assert 'id="save-btn"' in html and 'id="approve-btn"' in html
    assert "js-cedit" in html
    assert "Desaprobar para editar" not in html


class _ServicioDesaprobar:
    def __init__(self):
        self.desaprobados: list[str] = []

    def initialize(self):
        return True

    def unapprove_document(self, *, document_id):
        self.desaprobados.append(document_id)


def test_f065_r5_desaprobar_desde_la_ficha_vuelve_a_la_ficha(monkeypatch):
    servicio = _ServicioDesaprobar()

    respuesta = _cliente(monkeypatch, servicio).post(
        f"/documents/{DOC}/unapprove", data={"volver": "ficha"})

    assert respuesta.status_code == 303
    assert respuesta.headers["location"].startswith(f"/documents/{DOC}?message=")
    assert servicio.desaprobados == [DOC]


def test_f065_r5_desaprobar_desde_el_listado_vuelve_al_listado(monkeypatch):
    servicio = _ServicioDesaprobar()

    respuesta = _cliente(monkeypatch, servicio).post(
        f"/documents/{DOC}/unapprove", data={"redirect_query": "approved=all"})

    assert respuesta.headers["location"].startswith("/documents?approved=all&")


# --- R4 en lo que solo publica (revalorar, volver a buscar) ---------- #
class _RepoEstado:
    def __init__(self, estado):
        self.estado = estado

    def leer_alta_sigrid(self, document_id):
        return None

    def estado_aprobacion(self, document_id):
        return self.estado


@pytest.mark.parametrize("estado, lanza", [
    ({"approved": True}, True), ({"approved": False}, False), (None, False),
])
def test_f065_r4_comprobar_editable_mira_si_esta_aprobado(estado, lanza):
    from application.services.review_service import ReviewService
    from domain.models.review_models import AlbaranAprobadoError

    servicio = ReviewService(_RepoEstado(estado), "ana")
    if lanza:
        with pytest.raises(AlbaranAprobadoError):
            servicio.comprobar_editable(DOC)
    else:
        servicio.comprobar_editable(DOC)


def test_f065_r5_desaprobar_desde_la_ficha_con_alta_bloqueante_vuelve_a_la_ficha(monkeypatch):
    class _Servicio:
        def initialize(self):
            return True

        def unapprove_document(self, *, document_id):
            raise AlbaranBloqueadoError(document_id, "registrado", "AC26/7")

    respuesta = _cliente(monkeypatch, _Servicio()).post(
        f"/documents/{DOC}/unapprove", data={"volver": "ficha"})

    destino = respuesta.headers["location"]
    assert destino.startswith(f"/documents/{DOC}?message=")
    assert "AC26%2F7" in destino


@pytest.mark.parametrize("accion", ["bloquear", "desbloquear"])
@pytest.mark.parametrize("ok, codigo", [(True, 200), (False, 404)])
def test_f065_r13_el_portal_bloquea_y_desbloquea(monkeypatch, accion, ok, codigo):
    class _Servicio:
        def __init__(self):
            self.llamadas = []

        def initialize(self):
            return True

        def bloquear_linea(self, *, document_id, valuation_line_id):
            self.llamadas.append(("bloquear", document_id, valuation_line_id))
            return ok

        def desbloquear_linea(self, *, document_id, valuation_line_id):
            self.llamadas.append(("desbloquear", document_id, valuation_line_id))
            return ok

    servicio = _Servicio()

    respuesta = _cliente(monkeypatch, servicio).post(f"/api/documents/{DOC}/lines/12/{accion}")

    assert respuesta.status_code == codigo
    assert servicio.llamadas == [(accion, DOC, 12)]
    if ok:
        assert respuesta.json() == {"ok": True, "document_id": DOC, "valuation_line_id": 12}
