# tests/test_f053_t20_rutas.py
"""F-053 · T20 · el portal (``app.py``) con el alta en Sigrid.

- R25: con alta bloqueante, toda ruta que escribe o publica (incluida la del
  producto) se rechaza sin cambiar nada: 409 con el aviso en la API y
  redirección con el aviso en los formularios. Revalorar y volver a buscar
  contratos solo publican: miran el alta (sin cerrojo) ANTES de publicar.
- R27: el borrado múltiple y el vaciado de la papelera se saltan los
  bloqueantes y dicen cuántos.
- R28: «Ya lo he anulado en Sigrid» publica ``verificar_anulacion`` solo con
  un alta ``registrado``.
- R30: «Solicitar alta en Sigrid» publica ``alta`` solo cuando procede.
- R41: la ruta del producto (400 en los rechazos de R41).
- R1/R4/R37 en las rutas: el aviso de alta no pedida y el de no valorado.

Servicio falso detrás de un ``build_app`` real (sin BBDD ni colas), y el
servicio real con dobles para R27, R28 y R30.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from config.settings import Settings
from domain.models.alta_sigrid_models import (
    AVISO_SIN_VALORAR,
    AlbaranBloqueadoError,
    AlbaranSinValorarError,
    AltaSigridVista,
    ConfigAltaSigrid,
    ResultadoAprobacion,
    aviso_bloqueo,
)
from domain.models.review_models import DocumentDetailPayload
from interface_adapters.web import app as modulo_app

DOC = "f053-t20-doc"
AVISO = aviso_bloqueo("AC26/7")
DESDE = datetime(2026, 10, 1, tzinfo=UTC)
AHORA = datetime(2026, 10, 8, 10, 0, tzinfo=UTC)


def _documento(**campos) -> DocumentDetailPayload:
    base = {
        "id": DOC, "source_filename": "x.pdf", "provider_origin": "merge", "model_name": "—",
        "created_at_utc": "2026-10-08T08:00:00+00:00", "selected_contrato_codigo": "CT/1",
        "lines": [{"id": 1, "concepto": "ARIDO"}],
    }
    base.update(campos)
    return DocumentDetailPayload(**base)


class _Publicador:
    def __init__(self):
        self.publicados: list[tuple[str, object]] = []

    def publicar(self, nombre_cola, mensaje):
        self.publicados.append((nombre_cola, mensaje))
        return True


class _ServicioBloqueado:
    """Todo lo que escribe lanza ``AlbaranBloqueadoError`` (como el
    repositorio real dentro de su transacción)."""

    def __init__(self):
        self.llamadas: list[str] = []

    def initialize(self):
        return True

    def get_document(self, document_id, view_mode=None):
        return _documento()

    def list_trash_document_ids(self):
        return [DOC]

    def __getattr__(self, nombre):
        def _lanza(*args, **kwargs):
            self.llamadas.append(nombre)
            raise AlbaranBloqueadoError(DOC, "registrado", "AC26/7")
        return _lanza


def _cliente(monkeypatch, servicio):
    publicador = _Publicador()
    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: publicador)
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    return TestClient(modulo_app.build_app(ajustes), follow_redirects=False), publicador


# =================================================================== #
# R25 · API: 409 con el aviso
# =================================================================== #
RUTAS_API = [
    ("put", f"/api/documents/{DOC}", {"proveedor_cif": "B1"}, "guardar"),
    ("patch", f"/api/documents/{DOC}/lines/12/conciliacion", {"mode": "nueva"},
     "set_line_conciliacion"),
    ("patch", f"/api/documents/{DOC}/lines/12/conciliacion/campos", {"descripcion": "X"},
     "update_line_conciliacion"),
    ("delete", f"/api/documents/{DOC}/lines/12/conciliacion", None, "remove_line_conciliacion"),
    ("post", f"/api/documents/{DOC}/lines/by-merge/703/conciliacion", {"mode": "nueva"},
     "add_conciliacion_for_merge_line"),
    ("post", f"/api/documents/{DOC}/lines/12/almacen", None, "asignar_almacen_linea"),
    ("post", f"/api/documents/{DOC}/almacen-todas", None, "asignar_almacen_todas"),
    ("post", f"/api/documents/{DOC}/lines/standalone", None, "add_standalone_valuation_line"),
    ("post", f"/api/documents/{DOC}/lines/from-contrato", {"contrato_line_ids": [501]},
     "add_valuation_lines_from_contrato"),
    ("post", f"/api/documents/{DOC}/lineas-valoradas/12/producto-sigrid", {"producto": "XA9999"},
     "elegir_producto_sigrid"),
    ("post", f"/api/documents/{DOC}/re-fetch-contratos", None, "comprobar_desbloqueado"),
    ("post", f"/api/documents/{DOC}/valuate", None, "comprobar_desbloqueado"),
]


@pytest.mark.parametrize("metodo, ruta, cuerpo, llamada", RUTAS_API,
                         ids=[r[3] + ":" + r[1].rsplit("/", 1)[-1] for r in RUTAS_API])
def test_f053_r25_api_con_alta_bloqueante_responde_409(monkeypatch, metodo, ruta, cuerpo, llamada):
    servicio = _ServicioBloqueado()
    cliente, publicador = _cliente(monkeypatch, servicio)

    kwargs = {"json": cuerpo} if cuerpo is not None else {}
    respuesta = getattr(cliente, metodo)(ruta, **kwargs)

    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["detail"] == AVISO
    assert servicio.llamadas == [llamada]
    assert publicador.publicados == []  # revalorar / re-buscar no publican


def test_f053_r25_deshacer_con_alta_bloqueante_responde_409(monkeypatch):
    servicio = _ServicioBloqueado()
    cliente, _ = _cliente(monkeypatch, servicio)
    respuesta = cliente.post(f"/api/undo?document_id={DOC}")
    assert respuesta.status_code == 409
    assert respuesta.json() == {"ok": False, "error": AVISO, "detail": AVISO}
    assert servicio.llamadas == ["undo_last"]


# =================================================================== #
# R25 · formularios: redirección con el aviso
# =================================================================== #
@pytest.mark.parametrize("accion, llamada", [
    ("unapprove", "unapprove_document"),
    ("delete", "delete_document"),
    ("purge", "hard_delete_document"),
])
def test_f053_r25_formularios_redirigen_con_el_aviso(monkeypatch, accion, llamada):
    servicio = _ServicioBloqueado()
    cliente, publicador = _cliente(monkeypatch, servicio)

    respuesta = cliente.post(f"/documents/{DOC}/{accion}", data={"redirect_query": "approved=all"})

    assert respuesta.status_code == 303
    destino = respuesta.headers["location"]
    assert destino.startswith("/documents?approved=all&")
    assert "corr%C3%ADgelo+en+Sigrid" in destino and "AC26%2F7" in destino
    assert servicio.llamadas == [llamada]
    assert publicador.publicados == []


# =================================================================== #
# R27 · borrado múltiple y vaciar papelera se saltan los bloqueantes
# =================================================================== #
class _RepoBorrado:
    def __init__(self, bloqueados):
        self.bloqueados = set(bloqueados)
        self.borrados: list[str] = []
        self.purgados: list[str] = []

    def soft_delete_document(self, *, document_id, deleted_by):
        if document_id in self.bloqueados:
            raise AlbaranBloqueadoError(document_id, "registrado", "AC/1")
        if document_id == "roto":
            raise RuntimeError("fila rota")
        self.borrados.append(document_id)

    def hard_delete_document(self, *, document_id):
        if document_id in self.bloqueados:
            raise AlbaranBloqueadoError(document_id, "incierto", None)
        self.purgados.append(document_id)
        return f"sha-{document_id}"

    def list_trash_document_ids(self):
        return ["a", "b", "c"]


def test_f053_r27_borrado_multiple_salta_los_bloqueantes_y_los_cuenta():
    from application.services.review_service import ReviewService

    repo = _RepoBorrado(bloqueados={"b"})
    resultado = ReviewService(repo, "r").bulk_delete_documents_con_saltos(
        document_ids=["a", "b", "roto", "c"], deleted_by="ana",
    )
    assert (resultado.movidos, resultado.saltados) == (2, 1)
    assert repo.borrados == ["a", "c"]


def test_f053_r27_borrado_multiple_compatible_devuelve_los_movidos():
    from application.services.review_service import ReviewService

    repo = _RepoBorrado(bloqueados={"b"})
    assert ReviewService(repo, "r").bulk_delete_documents(
        document_ids=["a", "b"], deleted_by="ana") == 1


class _ServicioPapelera:
    def __init__(self, bloqueados):
        from application.services.review_service import ReviewService

        self._real = ReviewService(_RepoBorrado(bloqueados), "r")

    def initialize(self):
        return True

    def __getattr__(self, nombre):
        return getattr(self._real, nombre)


def test_f053_r27_borrado_multiple_en_la_ruta_dice_cuantos_salto(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _ServicioPapelera({"b"}))
    respuesta = cliente.post("/documents/bulk-delete", data={"ids": "a,b,c"})
    assert respuesta.status_code == 303
    destino = respuesta.headers["location"]
    assert "2+albar%C3%A1n%28es%29+movidos+a+la+papelera" in destino
    assert "1+saltado%28s%29" in destino


def test_f053_r27_vaciar_papelera_salta_los_bloqueantes_y_lo_dice(monkeypatch):
    servicio = _ServicioPapelera({"b"})
    cliente, _ = _cliente(monkeypatch, servicio)
    respuesta = cliente.post("/documents/trash/empty")
    assert respuesta.status_code == 303
    destino = respuesta.headers["location"]
    assert "2+albar%C3%A1n%28es%29+eliminados" in destino
    assert "1+saltado%28s%29" in destino
    assert "fallaron" not in destino
    assert servicio._real._repository.purgados == ["a", "c"]


# =================================================================== #
# R28 · R30 · servicio: solicitar alta y verificar anulación
# =================================================================== #
class _RepoAlta:
    def __init__(self, alta=None, aprobado=True, approved_at="2026-10-05T10:00:00+00:00",
                 activo=True):
        self.alta = alta
        self.estado = {"approved": aprobado, "approved_at_utc": approved_at, "is_active": activo}

    def leer_alta_sigrid(self, document_id):
        return self.alta

    def estado_aprobacion(self, document_id):
        return self.estado


class _Orq:
    def __init__(self, publica=True):
        self.publica = publica
        self.pedidas: list[dict] = []

    def solicitar_alta_sigrid(self, **kwargs):
        self.pedidas.append(kwargs)
        return self.publica


def _alta(estado, ultimo=None):
    return AltaSigridVista(estado=estado, sigrid_cod="AC26/7", ultimo_intento_at_utc=ultimo)


ACTIVA = ConfigAltaSigrid(desde=DESDE)


def _servicio_alta(repo, orq, config=ACTIVA):
    from application.services.review_service import ReviewService

    return ReviewService(repo, "r", orq, config)


@pytest.mark.parametrize("alta", [
    None, _alta("no_admitido"), _alta("revisar"), _alta("error"), _alta("simulado"),
    _alta("anulado"),
    _alta("incierto", (AHORA - timedelta(minutes=15)).isoformat()),
    _alta("en_curso", (AHORA - timedelta(hours=1)).isoformat()),
    _alta("incierto", None),
], ids=lambda a: "sin_alta" if a is None else f"{a.estado}:{a.ultimo_intento_at_utc}")
def test_f053_r30_solicitar_alta_cuando_procede_publica(alta):
    orq = _Orq()
    resultado = _servicio_alta(_RepoAlta(alta), orq).solicitar_alta_sigrid(
        document_id=DOC, solicitado_por="ana", ahora=AHORA,
    )
    assert resultado == "pedida"
    assert orq.pedidas == [{"document_id": DOC, "accion": "alta", "solicitado_por": "ana"}]


@pytest.mark.parametrize("repo", [
    _RepoAlta(_alta("registrado")),
    _RepoAlta(_alta("ya_en_sigrid")),
    _RepoAlta(_alta("incierto", (AHORA - timedelta(minutes=14, seconds=59)).isoformat())),
    _RepoAlta(_alta("en_curso", AHORA.isoformat())),
    _RepoAlta(None, aprobado=False),
    _RepoAlta(None, approved_at="2026-09-30T23:59:59+00:00"),
    _RepoAlta(None, approved_at=None),
    _RepoAlta(None, approved_at="ilegible"),
    _RepoAlta(None, activo=False),
], ids=["registrado", "ya_en_sigrid", "incierto_sin_espera", "en_curso_sin_espera",
        "no_aprobado", "antes_de_desde", "sin_fecha", "fecha_ilegible", "papelera"])
def test_f053_r30_solicitar_alta_cuando_no_procede_no_publica(repo):
    orq = _Orq()
    assert _servicio_alta(repo, orq).solicitar_alta_sigrid(
        document_id=DOC, solicitado_por="ana", ahora=AHORA) == "no_procede"
    assert orq.pedidas == []


def test_f053_r30_solicitar_alta_con_desde_vacia_no_publica():
    orq = _Orq()
    assert _servicio_alta(_RepoAlta(None), orq, ConfigAltaSigrid()).solicitar_alta_sigrid(
        document_id=DOC, solicitado_por="ana", ahora=AHORA) == "apagada"
    assert orq.pedidas == []


def test_f053_r30_solicitar_alta_sin_documento():
    repo = _RepoAlta(None)
    repo.estado = None
    assert _servicio_alta(repo, _Orq()).solicitar_alta_sigrid(
        document_id=DOC, solicitado_por=None, ahora=AHORA) == "no_procede"


def test_f053_r30_solicitar_alta_que_no_se_publica_lo_dice():
    assert _servicio_alta(_RepoAlta(None), _Orq(publica=False)).solicitar_alta_sigrid(
        document_id=DOC, solicitado_por="ana", ahora=AHORA) == "no_publicada"


def test_f053_r28_verificar_anulacion_solo_con_registrado():
    orq = _Orq()
    servicio = _servicio_alta(_RepoAlta(_alta("registrado")), orq)
    assert servicio.verificar_anulacion_sigrid(document_id=DOC, solicitado_por="ana") == "pedida"
    assert orq.pedidas == [
        {"document_id": DOC, "accion": "verificar_anulacion", "solicitado_por": "ana"}]


@pytest.mark.parametrize("alta", [None, _alta("simulado"), _alta("incierto"), _alta("anulado")],
                         ids=lambda a: "sin_alta" if a is None else a.estado)
def test_f053_r28_verificar_anulacion_sin_registrado_no_publica(alta):
    orq = _Orq()
    assert _servicio_alta(_RepoAlta(alta), orq).verificar_anulacion_sigrid(
        document_id=DOC, solicitado_por="ana") == "no_procede"
    assert orq.pedidas == []


def test_f053_r28_verificar_anulacion_con_desde_vacia_no_publica():
    orq = _Orq()
    assert _servicio_alta(_RepoAlta(_alta("registrado")), orq, ConfigAltaSigrid()) \
        .verificar_anulacion_sigrid(document_id=DOC, solicitado_por="ana") == "apagada"
    assert orq.pedidas == []


def test_f053_r25_comprobar_desbloqueado_sin_cerrojo():
    servicio = _servicio_alta(_RepoAlta(_alta("incierto")), _Orq())
    with pytest.raises(AlbaranBloqueadoError) as error:
        servicio.comprobar_desbloqueado(DOC)
    assert error.value.cod == "AC26/7"
    for alta in (None, _alta("simulado")):
        _servicio_alta(_RepoAlta(alta), _Orq()).comprobar_desbloqueado(DOC)


# =================================================================== #
# R28 · R30 · rutas
# =================================================================== #
class _ServicioAlta:
    def __init__(self, resultado):
        self.resultado = resultado
        self.llamadas: list[tuple] = []

    def initialize(self):
        return True

    def solicitar_alta_sigrid(self, *, document_id, solicitado_por, ahora=None):
        self.llamadas.append(("alta", document_id, solicitado_por))
        return self.resultado

    def verificar_anulacion_sigrid(self, *, document_id, solicitado_por):
        self.llamadas.append(("verificar", document_id, solicitado_por))
        return self.resultado


@pytest.mark.parametrize("ruta, llamada", [
    ("solicitar", "alta"), ("verificar-anulacion", "verificar"),
])
@pytest.mark.parametrize("resultado, texto", [
    ("pedida", "pedida"), ("no_publicada", "no+se+pudo"), ("no_procede", "no+procede"),
    ("apagada", "desactivada"),
])
def test_f053_r30_rutas_de_la_ficha(monkeypatch, ruta, llamada, resultado, texto):
    servicio = _ServicioAlta(resultado)
    cliente, _ = _cliente(monkeypatch, servicio)
    respuesta = cliente.post(f"/documents/{DOC}/alta-sigrid/{ruta}",
                             headers={"X-MS-CLIENT-PRINCIPAL-NAME": "ana@ruesma.es"})
    assert respuesta.status_code == 303
    destino = respuesta.headers["location"]
    assert destino.startswith(f"/documents/{DOC}?message=")
    assert texto in destino
    assert servicio.llamadas == [(llamada, DOC, "ana@ruesma.es")]


# =================================================================== #
# R41 · ruta del producto
# =================================================================== #
class _ServicioProducto:
    def __init__(self, resultado):
        self.resultado = resultado
        self.llamadas: list[tuple] = []

    def initialize(self):
        return True

    def elegir_producto_sigrid(self, *, document_id, valuation_line_id, producto):
        self.llamadas.append((document_id, valuation_line_id, producto))
        return self.resultado


@pytest.mark.parametrize("producto", ["XA9999", None])
def test_f053_r41_ruta_producto_guardado(monkeypatch, producto):
    servicio = _ServicioProducto("guardado")
    cliente, _ = _cliente(monkeypatch, servicio)
    respuesta = cliente.post(f"/api/documents/{DOC}/lineas-valoradas/12/producto-sigrid",
                             json={"producto": producto})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json() == {"ok": True, "document_id": DOC, "valuation_line_id": 12,
                                "producto": producto}
    assert servicio.llamadas == [(DOC, 12, producto)]


@pytest.mark.parametrize("resultado", ["no_admitido", "linea_ajena", "vinculada", "apagada"])
def test_f053_r41_ruta_producto_rechazos_400(monkeypatch, resultado):
    cliente, _ = _cliente(monkeypatch, _ServicioProducto(resultado))
    respuesta = cliente.post(f"/api/documents/{DOC}/lineas-valoradas/12/producto-sigrid",
                             json={"producto": "ZZ"})
    assert respuesta.status_code == 400
    assert respuesta.json()["detail"]


def test_f053_r41_ruta_producto_cuerpo_invalido_422(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _ServicioProducto("guardado"))
    respuesta = cliente.post(f"/api/documents/{DOC}/lineas-valoradas/12/producto-sigrid",
                             json={"producto": 7})
    assert respuesta.status_code == 422


# =================================================================== #
# R1/R4 y R37 en las rutas de aprobar
# =================================================================== #
class _ServicioAprobar:
    def __init__(self, resultado=None, lanza=None):
        self.resultado = resultado
        self.lanza = lanza

    def initialize(self):
        return True

    def approve_document(self, *, document_id, approved_by):
        if self.lanza:
            raise self.lanza
        return self.resultado

    def guardar(self, *, document_id, payload, refetch_client):
        from application.services.review_service import ResultadoGuardado

        if self.lanza:
            raise self.lanza
        return ResultadoGuardado(
            detail=_documento(approved=payload.approved), busqueda=None,
            aprobacion=self.resultado,
        )


def test_f053_r4_aprobar_del_listado_avisa_si_el_alta_no_se_pidio(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _ServicioAprobar(
        ResultadoAprobacion(paso_a_aprobado=True, alta_pedida=False)))
    destino = cliente.post(f"/documents/{DOC}/approve").headers["location"]
    assert "Documento+aprobado" in destino and "Solicitar+alta+en+Sigrid" in destino


def test_f053_r1_aprobar_del_listado_sin_aviso_si_se_pidio(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _ServicioAprobar(
        ResultadoAprobacion(paso_a_aprobado=True, alta_pedida=True)))
    destino = cliente.post(f"/documents/{DOC}/approve").headers["location"]
    assert "Documento+aprobado" in destino and "Solicitar" not in destino


def test_f053_r37_aprobar_del_listado_sin_valorar_redirige_con_el_aviso(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _ServicioAprobar(lanza=AlbaranSinValorarError(DOC)))
    respuesta = cliente.post(f"/documents/{DOC}/approve", data={"redirect_query": "approved=pending"})
    assert respuesta.status_code == 303
    destino = respuesta.headers["location"]
    assert destino.startswith("/documents?approved=pending&")
    assert "No+se+puede+aprobar+un+albar%C3%A1n+sin+valorar" in destino


def test_f053_r37_guardar_y_aprobar_sin_valorar_responde_409(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _ServicioAprobar(lanza=AlbaranSinValorarError(DOC)))
    respuesta = cliente.put(f"/api/documents/{DOC}", json={"approved": True})
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == AVISO_SIN_VALORAR


def test_f053_r4_guardar_y_aprobar_avisa_si_el_alta_no_se_pidio(monkeypatch):
    cliente, _ = _cliente(monkeypatch, _ServicioAprobar(
        ResultadoAprobacion(paso_a_aprobado=True, alta_pedida=False)))
    cuerpo = cliente.put(f"/api/documents/{DOC}", json={"approved": True}).json()
    assert "Solicitar alta en Sigrid" in cuerpo["message"]
    assert cuerpo["approved"] is True
