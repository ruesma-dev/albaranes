# tests/test_f116_cabecera_api.py
"""F-116 · A · el autoguardado de la cabecera: ``PATCH /api/documents/{id}/cabecera``
(R1–R6, D1 = a).

Repositorio real sobre SQLite (``f065_bbdd``: el albarán de METALFIRE), servicio
real y ``build_app`` real, como ``test_f108_guardado.py``. Sin red ni BBDD.
"""
from __future__ import annotations

from typing import Any

import pytest
from f053_sv4_bbdd import foto, poner_alta
from f065_bbdd import CONTRATO, DOC, construir, ejecutar, repositorio
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

CAMPOS = ("fecha", "numero_albaran", "forma_pago", "review_notes")
AVISO_APROBADO = "Albarán aprobado: desapruébalo para editar"
AVISO_NUMERO = "El número de albarán no puede pasar de 128 caracteres"


def _aviso_fecha(texto: str) -> str:
    return (f"Fecha del albarán no válida: «{texto}». Escríbela como dd/mm/aaaa "
            "(p. ej. 28/10/2026) o elígela en el calendario.")


def _documento(motor) -> dict[str, Any]:
    with Session(motor) as s:
        return dict(s.execute(
            text("SELECT * FROM albaran_documents_merge WHERE id = :id"), {"id": DOC},
        ).mappings().one())


def _undo(motor) -> list[dict[str, Any]]:
    with Session(motor) as s:
        return [dict(r) for r in s.execute(text(
            "SELECT action, description, document_id FROM undo_log ORDER BY id"),
        ).mappings().all()]


def _guardar(motor, **campos):
    return repositorio(motor).update_cabecera_campos(document_id=DOC, campos=campos)


# =================================================================== #
# T1 · R5 · el cuerpo: solo los cuatro campos; ausente = no cambia
# =================================================================== #
def test_f116_r5_campo_desconocido_es_error_de_validacion():
    from domain.models.review_models import CabeceraEditBody

    with pytest.raises(ValidationError):
        CabeceraEditBody.model_validate({"fecha": "28/10/2026", "obra_codigo": "0404"})


def test_f116_r5_campos_solo_los_que_vinieron():
    from domain.models.review_models import CabeceraEditBody

    assert CabeceraEditBody.model_validate({}).campos() == {}
    assert CabeceraEditBody.model_validate({"review_notes": None}).campos() == {
        "review_notes": None}
    assert CabeceraEditBody.model_validate(
        {"fecha": "28-10-26", "forma_pago": " giro "}).campos() == {
        "fecha": "28-10-26", "forma_pago": " giro "}


def test_f116_r5_el_cuerpo_no_valida_la_fecha():
    """Sin validador de fecha en el cuerpo (design §4.1): la rechaza el
    repositorio con el texto de F-108, no Pydantic con una lista."""
    from domain.models.review_models import CabeceraEditBody

    assert CabeceraEditBody.model_validate({"fecha": "31/02/2026"}).campos() == {
        "fecha": "31/02/2026"}


# =================================================================== #
# T2 · R1 · solo lo que viene, normalizado, con los sellos
# =================================================================== #
@pytest.mark.parametrize("escrita", ["28/10/2026", "28-10-26", "2026-10-28", " 28.10.2026 "])
def test_f116_r1_la_fecha_se_guarda_en_iso(escrita):
    motor = construir()

    guardado = _guardar(motor, fecha=escrita)

    assert guardado == {"fecha": "2026-10-28"}
    assert _documento(motor)["fecha"] == "2026-10-28"


def test_f116_r1_cada_campo_solo_no_toca_los_otros_tres():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_documents_merge SET forma_pago = 'giro', "
             "review_notes = 'nota' WHERE id = :d", d=DOC)

    assert _guardar(motor, numero_albaran="  ab.12/x ") == {"numero_albaran": "ab.12/x"}

    doc = _documento(motor)
    assert (doc["fecha"], doc["numero_albaran"], doc["forma_pago"], doc["review_notes"]) == (
        "2026-10-08", "ab.12/x", "giro", "nota")


def test_f116_r1_los_cuatro_juntos_recortados():
    motor = construir()

    guardado = _guardar(motor, fecha="05/06/2026", numero_albaran=" B-7 ",
                        forma_pago="  transferencia ", review_notes=" revisar portes ")

    assert guardado == {"fecha": "2026-06-05", "numero_albaran": "B-7",
                        "forma_pago": "transferencia", "review_notes": "revisar portes"}
    doc = _documento(motor)
    assert {c: doc[c] for c in CAMPOS} == guardado


@pytest.mark.parametrize("vacio", [None, "", "   "])
@pytest.mark.parametrize("campo", CAMPOS)
def test_f116_r1_nulo_o_vacio_vacia(campo, vacio):
    motor = construir()
    ejecutar(motor, "UPDATE albaran_documents_merge SET forma_pago = 'giro', "
             "review_notes = 'nota' WHERE id = :d", d=DOC)

    assert _guardar(motor, **{campo: vacio}) == {campo: None}
    assert _documento(motor)[campo] is None


def test_f116_r1_sella_last_modified_y_reviewed():
    motor = construir()
    antes = _documento(motor)

    _guardar(motor, review_notes="nota")

    doc = _documento(motor)
    assert doc["last_modified_at_utc"] and doc["last_modified_at_utc"] != antes[
        "last_modified_at_utc"]
    assert doc["reviewed_at_utc"] and doc["reviewed_at_utc"] != antes["reviewed_at_utc"]


def test_f116_r1_sin_campos_no_escribe_nada():
    motor = construir()
    antes = foto(motor)

    assert _guardar(motor) == {}
    assert foto(motor) == antes


# =================================================================== #
# T2 · R2 · nada más del documento cambia
# =================================================================== #
def test_f116_r2_no_toca_contrato_proveedor_obra_aprobacion_ni_motivos():
    motor = construir()
    # Lo que sv3 escribió DESPUÉS de abrir la ficha (design §1.4): el contrato
    # auto-seleccionado, la dirección de obra y motivos con CIF sellado.
    ejecutar(motor, "UPDATE albaran_documents_merge SET selected_contrato_codigo = :c, "
             "selected_contrato_origen = 'auto', obra_direccion = 'C/ Mayor 1', "
             "obra_nombre = 'OBRA X', proveedor_nombre = 'METALFIRE', "
             "review_reasons_json = :m WHERE id = :d",
             c=CONTRATO, m='["cif_no_encontrado:B00000000"]', d=DOC)
    antes = _documento(motor)
    lineas_antes = {t: v for t, v in foto(motor).items() if t != "albaran_documents_merge"}

    _guardar(motor, fecha="28/10/2026", numero_albaran="Z-9", forma_pago="giro",
             review_notes="nota")

    despues = _documento(motor)
    tocadas = set(CAMPOS) | {"last_modified_at_utc", "reviewed_at_utc"}
    assert {k: v for k, v in despues.items() if k not in tocadas} == {
        k: v for k, v in antes.items() if k not in tocadas}
    assert {t: v for t, v in foto(motor).items() if t != "albaran_documents_merge"} == (
        lineas_antes)


def test_f116_r2_no_relanza_la_busqueda_ni_depura_motivos(monkeypatch):
    repo = repositorio(construir())
    llamadas: list[str] = []
    monkeypatch.setattr(repo, "_depurar_motivos_documento_in_session",
                        lambda **_: llamadas.append("depurar"))
    monkeypatch.setattr(repo, "_es_del_albaran_in_session",
                        lambda *_, **__: llamadas.append("contrato"))

    repo.update_cabecera_campos(document_id=DOC, campos={"review_notes": "x"})

    assert llamadas == []


# =================================================================== #
# T2 · R3 · fecha no admitida o número largo: error y nada cambia
# =================================================================== #
@pytest.mark.parametrize("escrita", ["31/02/2026", "abc"])
def test_f116_r3_fecha_no_admitida_no_cambia_nada(escrita):
    from domain.models.review_models import FechaAlbaranNoValidaError

    motor = construir()
    antes = foto(motor)

    with pytest.raises(FechaAlbaranNoValidaError) as error:
        _guardar(motor, fecha=escrita, review_notes="nota nueva")

    assert error.value.aviso == _aviso_fecha(escrita)
    assert foto(motor) == antes


def test_f116_r3_numero_largo_no_cambia_nada():
    from domain.models.review_models import NumeroAlbaranNoValidoError

    motor = construir()
    antes = foto(motor)

    with pytest.raises(NumeroAlbaranNoValidoError) as error:
        _guardar(motor, numero_albaran="x" * 129, forma_pago="giro")

    assert error.value.aviso == AVISO_NUMERO
    assert foto(motor) == antes


def test_f116_r3_numero_de_128_si_se_guarda():
    motor = construir()

    assert _guardar(motor, numero_albaran="x" * 128) == {"numero_albaran": "x" * 128}


# =================================================================== #
# T2 · R4 · aprobado, alta bloqueante, no existe
# =================================================================== #
def test_f116_r4_aprobado_no_cambia_nada():
    from domain.models.review_models import AlbaranAprobadoError

    motor = construir(aprobado=True)
    antes = foto(motor)

    with pytest.raises(AlbaranAprobadoError):
        _guardar(motor, review_notes="nota", fecha="31/02/2026")

    assert foto(motor) == antes


def test_f116_r4_alta_bloqueante_no_cambia_nada():
    from domain.models.alta_sigrid_models import AlbaranBloqueadoError

    motor = construir(con_altas=True)
    poner_alta(motor, "registrado", document_id=DOC)
    antes = foto(motor)

    with pytest.raises(AlbaranBloqueadoError):
        _guardar(motor, review_notes="nota")

    assert foto(motor) == antes


def test_f116_r4_documento_que_no_existe():
    motor = construir()

    with pytest.raises(KeyError):
        repositorio(motor).update_cabecera_campos(
            document_id="no-existe", campos={"review_notes": "x"})


# =================================================================== #
# T3 · R6 · servicio: una entrada de deshacer que devuelve la cabecera
# =================================================================== #
def _servicio(motor):
    from application.services.review_service import ReviewService

    return ReviewService(repositorio(motor), "ana")


def test_f116_r6_deja_una_entrada_de_deshacer_y_deshace():
    from test_f106_fila import _deshacer

    motor = construir()
    ejecutar(motor, "UPDATE albaran_documents_merge SET review_notes = 'vieja' WHERE id = :d",
             d=DOC)
    antes = _documento(motor)

    guardado = _servicio(motor).editar_cabecera(
        document_id=DOC, campos={"review_notes": "nueva", "fecha": "28/10/2026"})

    assert guardado == {"fecha": "2026-10-28", "review_notes": "nueva"}
    (entrada,) = _undo(motor)
    assert entrada["action"] == "cabecera"
    assert entrada["document_id"] == DOC
    assert entrada["description"] == "Editar cabecera · Fecha, Notas (alb A-1)"

    _deshacer(motor)

    assert _documento(motor) == antes


def test_f116_r6_etiquetas_de_los_cuatro_en_orden_de_la_ficha():
    motor = construir()

    _servicio(motor).editar_cabecera(document_id=DOC, campos={
        "review_notes": "n", "forma_pago": "g", "numero_albaran": "A-2", "fecha": None})

    (entrada,) = _undo(motor)
    assert entrada["description"] == (
        "Editar cabecera · Fecha, Número, Forma de pago, Notas (alb A-2)")


def test_f116_r6_sin_campos_no_deja_entrada():
    motor = construir()

    assert _servicio(motor).editar_cabecera(document_id=DOC, campos={}) == {}
    assert _undo(motor) == []


def test_f116_r6_un_error_no_deja_entrada():
    from domain.models.review_models import FechaAlbaranNoValidaError

    motor = construir()

    with pytest.raises(FechaAlbaranNoValidaError):
        _servicio(motor).editar_cabecera(document_id=DOC, campos={"fecha": "abc"})
    assert _undo(motor) == []


# =================================================================== #
# T3 · R1–R5 en el portal (build_app real, servicio y repositorio reales)
# =================================================================== #
class _PublicadorFalso:
    def publicar(self, nombre_cola, mensaje):
        return True


def _portal(monkeypatch, motor):
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.web import app as modulo_app

    servicio = _servicio(motor)
    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: _PublicadorFalso())
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    return TestClient(modulo_app.build_app(ajustes), follow_redirects=False)


URL = f"/api/documents/{DOC}/cabecera"


@pytest.fixture
def construir_compartido(monkeypatch):
    """``construir`` con UNA conexión para todos los hilos: el ``TestClient``
    ejecuta la ruta en otro hilo y un SQLite en memoria es por conexión."""
    import f065_bbdd
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    monkeypatch.setattr(f065_bbdd, "create_engine", lambda url: create_engine(
        url, poolclass=StaticPool, connect_args={"check_same_thread": False}))
    return construir


def test_f116_r1_ruta_responde_lo_guardado(monkeypatch, construir_compartido):
    motor = construir_compartido()

    r = _portal(monkeypatch, motor).patch(URL, json={"fecha": "28-10-26"})

    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "document_id": DOC, "cabecera": {"fecha": "2026-10-28"}}
    assert _documento(motor)["fecha"] == "2026-10-28"
    assert [e["action"] for e in _undo(motor)] == ["cabecera"]


def test_f116_r1_ruta_null_vacia(monkeypatch, construir_compartido):
    motor = construir_compartido()

    r = _portal(monkeypatch, motor).patch(URL, json={"numero_albaran": None})

    assert r.status_code == 200, r.text
    assert r.json()["cabecera"] == {"numero_albaran": None}
    assert _documento(motor)["numero_albaran"] is None


@pytest.mark.parametrize("cuerpo, aviso", [
    ({"fecha": "31/02/2026"}, _aviso_fecha("31/02/2026")),
    ({"numero_albaran": "x" * 129}, AVISO_NUMERO),
], ids=["fecha", "numero"])
def test_f116_r3_ruta_422_con_texto_sin_cambiar_nada(monkeypatch, construir_compartido,
                                                     cuerpo, aviso):
    motor = construir_compartido()
    antes = foto(motor)

    r = _portal(monkeypatch, motor).patch(URL, json=cuerpo)

    assert r.status_code == 422, r.text
    assert r.json() == {"detail": aviso}
    assert foto(motor) == antes


def test_f116_r4_ruta_aprobado_409(monkeypatch, construir_compartido):
    motor = construir_compartido(aprobado=True)
    antes = foto(motor)

    r = _portal(monkeypatch, motor).patch(URL, json={"review_notes": "x"})

    assert r.status_code == 409, r.text
    assert r.json() == {"detail": AVISO_APROBADO}
    assert foto(motor) == antes


def test_f116_r4_ruta_alta_bloqueante_409(monkeypatch, construir_compartido):
    motor = construir_compartido(con_altas=True)
    poner_alta(motor, "registrado", document_id=DOC)
    antes = foto(motor)

    r = _portal(monkeypatch, motor).patch(URL, json={"review_notes": "x"})

    assert r.status_code == 409, r.text
    assert foto(motor) == antes


def test_f116_r4_ruta_no_existe_404(monkeypatch, construir_compartido):
    motor = construir_compartido()

    r = _portal(monkeypatch, motor).patch("/api/documents/no-existe/cabecera",
                                          json={"review_notes": "x"})

    assert r.status_code == 404, r.text


def test_f116_r5_ruta_campo_extra_422_sin_cambiar_nada(monkeypatch, construir_compartido):
    motor = construir_compartido()
    antes = foto(motor)

    r = _portal(monkeypatch, motor).patch(URL, json={"review_notes": "x",
                                                     "selected_contrato_codigo": None})

    assert r.status_code == 422, r.text
    assert foto(motor) == antes


def test_f116_r5_ruta_cuerpo_vacio_200_sin_escribir(monkeypatch, construir_compartido):
    motor = construir_compartido()
    antes = foto(motor)

    r = _portal(monkeypatch, motor).patch(URL, json={})

    assert r.status_code == 200, r.text
    assert r.json() == {"ok": True, "document_id": DOC, "cabecera": {}}
    assert foto(motor) == antes
