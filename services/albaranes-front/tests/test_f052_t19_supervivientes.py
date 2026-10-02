# tests/test_f052_t19_supervivientes.py
"""F-052 T19 · supervivientes de la campaña de mutación en sv4.

Cada test fija un valor que la campaña (``progress/mutacion_F-052.md``)
demostró que ningún test leía. Los de las rutas pasan por FastAPI
(``build_app`` con sus piezas de infraestructura sustituidas por dobles:
sin BBDD, sin colas y sin leer el ``.env``), porque lo que sobrevivía eran
los valores por defecto de los parámetros de la ruta y lo que la ruta
responde, que un test del servicio no ve.
"""
from __future__ import annotations

import pytest
from config.settings import Settings
from domain.models.contrato_refetch_models import ContratoRefetchOutcome
from domain.models.review_models import (
    BUSQUEDA_NINGUNO,
    ESTADO_BUSQUEDA_DESFASADA,
    BusquedaContratosVista,
    DocumentDetailPayload,
    SaveResponse,
)
from fastapi.testclient import TestClient
from interface_adapters.web import app as modulo_app
from test_f052_d4a_guardar_relanza import (
    CIF_BUENO,
    CIF_MAL,
    OBRA,
    _guardar,
    _rastro,
    _RefetchFalso,
    _RepositorioFalso,
)

DOC = "f052-t19-doc"


# ------------------------------------------------------------------ #
# ReviewService.save_document_y_buscar_si_cambia
# ------------------------------------------------------------------ #
def test_f052_t19_si_relanzar_falla_el_outcome_no_trae_contratos():
    """El outcome de un relanzado fallido dice 0 contratos y ninguno
    elegido: la búsqueda no llegó a hacerse."""
    repo = _RepositorioFalso(cif=CIF_MAL, obra=OBRA, rastro=_rastro())
    _, busqueda = _guardar(repo, _RefetchFalso(lanza=RuntimeError("x")), cif=CIF_BUENO)
    assert busqueda.status == "sigrid_error"
    assert busqueda.count == 0
    assert busqueda.selected_contrato_codigo is None


def test_f052_t19_save_response_por_defecto_no_relanzo_la_busqueda():
    """Un ``SaveResponse`` que no lo dice no afirma que se relanzó nada
    (contrato de la API: el campo es opcional y por defecto ``False``)."""
    respuesta = SaveResponse(
        ok=True, document_id="d", approved=False, redirect_url="/", message="m",
    )
    assert respuesta.busqueda_relanzada is False


# ------------------------------------------------------------------ #
# Rutas: PUT /api/documents/{id} y GET /documents/{id}
# ------------------------------------------------------------------ #
class _ServicioFalso:
    """Lo que las dos rutas usan de ``ReviewService``; anota con qué
    ``refetch_client`` se pidió el guardado."""

    def __init__(self) -> None:
        self.refetch_recibidos: list[object] = []
        self.busqueda: ContratoRefetchOutcome | None = None
        self.documento: DocumentDetailPayload | None = None

    def initialize(self) -> bool:
        return True

    def save_document_y_buscar_si_cambia(self, *, document_id, payload, refetch_client):
        self.refetch_recibidos.append(refetch_client)
        detalle = DocumentDetailPayload(
            id=document_id, source_filename="x.pdf", provider_origin="merge",
            model_name="—", created_at_utc="2026-10-01T08:00:00+00:00",
            proveedor_cif=payload.proveedor_cif, obra_codigo=payload.obra_codigo,
            approved=payload.approved,
        )
        return detalle, self.busqueda

    def get_document(self, document_id, view_mode=None):
        return self.documento

    def get_neighbor_ids(self, *, document_id, filters):
        return None, None


class _PublicadorFalso:
    def publicar(self, nombre_cola, mensaje):
        return True


@pytest.fixture
def portal(monkeypatch):
    """``(cliente HTTP, servicio falso, refetch cableado)`` de un sv4 real
    sin BBDD ni colas."""
    servicio = _ServicioFalso()
    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: _PublicadorFalso())
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    app = modulo_app.build_app(ajustes)
    return TestClient(app), servicio, app.state.sv3_refetch_client


def _put(cliente, consulta: str = ""):
    respuesta = cliente.put(
        f"/api/documents/{DOC}{consulta}",
        json={"proveedor_cif": CIF_BUENO, "obra_codigo": OBRA},
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_f052_t19_put_sin_buscar_si_cambia_no_pasa_cliente_de_refetch(portal):
    """Los PUT del portal que no son «Guardar» no llevan
    ``buscar_si_cambia``: por defecto, nunca se relanza la búsqueda."""
    cliente, servicio, _ = portal
    cuerpo = _put(cliente)
    assert servicio.refetch_recibidos == [None]
    assert cuerpo["busqueda_relanzada"] is False


def test_f052_t19_put_con_buscar_si_cambia_relanza_y_lo_dice(portal):
    cliente, servicio, refetch = portal
    servicio.busqueda = ContratoRefetchOutcome(
        status="queued", count=0, selected_contrato_codigo=None,
        message="encolada", cif=None, obra_codigo=None,
    )
    cuerpo = _put(cliente, "?buscar_si_cambia=1")
    assert servicio.refetch_recibidos == [refetch]
    assert cuerpo["busqueda_relanzada"] is True
    assert "buscando=1" in cuerpo["redirect_url"]


def test_f052_t19_put_con_buscar_si_cambia_sin_relanzar_no_lo_dice(portal):
    """Sin cambio de CIF ni de obra el servicio no relanza (``None``): la
    respuesta no puede decir que sí."""
    cliente, servicio, refetch = portal
    cuerpo = _put(cliente, "?buscar_si_cambia=1")
    assert servicio.refetch_recibidos == [refetch]
    assert cuerpo["busqueda_relanzada"] is False


def test_f052_t19_detalle_sin_buscando_en_la_url_no_marca_buscando(portal, documento_detalle):
    """``?buscando=1`` solo llega tras un «Guardar» que relanzó; sin él,
    un documento desfasado NO se pinta como «buscando…»."""
    cliente, servicio, _ = portal
    servicio.documento = documento_detalle().model_copy(update={
        "id": DOC, "proveedor_cif": CIF_BUENO, "obra_codigo": OBRA, "contratos": [],
        "busqueda_contratos": BusquedaContratosVista(
            estado=ESTADO_BUSQUEDA_DESFASADA, cif=CIF_MAL, obra=OBRA,
            fecha="2026-09-30T10:15:00+00:00", resultado=BUSQUEDA_NINGUNO,
        ),
    })
    sin = cliente.get(f"/documents/{DOC}")
    con = cliente.get(f"/documents/{DOC}?buscando=1")
    assert sin.status_code == con.status_code == 200
    assert 'id="busqueda-buscando"' not in sin.text
    assert 'id="busqueda-buscando"' in con.text
