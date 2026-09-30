# tests/test_f052_d4a_guardar_relanza.py
"""F-052 T13 bis · D4-A (decisión del humano, 2026-09-30).

Al pulsar «Guardar» con un CIF o una obra DISTINTOS de los del último
rastro de búsqueda, sv4 relanza sola la re-búsqueda de contratos por la
misma vía que «Guardar y volver a buscar» (``q-persistencia``, re-fetch
con ``force=True``). Sin cambio de CIF ni de obra, «Guardar» no busca. El
bloque de contrato sigue diciendo con qué se buscó y marca «buscando…»
mientras llega el resultado.

Qué es «distinto» lo decide ``estado_busqueda`` (R27): estado ``desfasada``.
Decisiones que fija este fichero:

- O-C1 (decisión del humano, 2026-10-01): sin rastro (documento anterior
  al despliegue) el PRIMER «Guardar» busca una vez; a partir de ahí hay
  rastro (aunque sea ``sin_datos``) y rige la regla normal.
- «Aprobar» no es «Guardar»: un guardado que aprueba no relanza.
- Si relanzar falla, el guardado ya está hecho: se informa, no se deshace.
- O-B4 de la review del Bloque B: el deshacer de sv4 restaura la fila
  ENTERA del merge, así que el CIF, la obra y el rastro vuelven juntos y
  el documento no queda «desfasado» por el deshacer.

Sin red ni BBDD real (fakes y SQLite en memoria).
"""
from __future__ import annotations

import logging
import re

import pytest
from application.services.busqueda_contratos import (
    debe_relanzar_busqueda,
    estado_busqueda,
)
from application.services.review_service import ReviewService
from domain.models.contrato_refetch_models import ContratoRefetchOutcome
from domain.models.review_models import (
    BUSQUEDA_ENCONTRADOS,
    BUSQUEDA_ERROR,
    BUSQUEDA_NINGUNO,
    ESTADO_BUSQUEDA_DESFASADA,
    ESTADO_BUSQUEDA_VIGENTE,
    BusquedaContratosVista,
    DocumentDetailPayload,
    MergeDocumentUpdatePayload,
    RastroBusquedaContratos,
)
from infrastructure.colas.colas_refetch_client import ColasRefetchClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DOC_ID = "f052-doc-0000-0000-0000-000026122"
CIF_MAL = "B82890580"  # el que leyó IA1 en SS-0026122
CIF_BUENO = "B82899550"
OBRA = "0691"
FECHA = "2026-09-30T10:15:00+00:00"


# ------------------------------------------------------------------ #
# Dobles
# ------------------------------------------------------------------ #
class _RepositorioFalso:
    """Lo mínimo de ``AlbaranReviewRepository`` que usa ``save_document``."""

    def __init__(self, *, cif, obra, rastro):
        self.cif = cif
        self.obra = obra
        self.rastro = rastro
        self.guardados: list[MergeDocumentUpdatePayload] = []
        self.undo: list[dict] = []

    def snapshot_row(self, *, table, row_id):
        return {"table": table, "values": {"id": row_id}}

    def valuation_header_id(self, *, document_id):
        return None

    def update_document(self, *, document_id, payload):
        self.guardados.append(payload)
        self.cif = payload.proveedor_cif
        self.obra = payload.obra_codigo
        return DocumentDetailPayload(
            id=document_id,
            source_filename="SS-0026122.pdf",
            provider_origin="merge",
            model_name="—",
            created_at_utc="2026-09-29T08:00:00+00:00",
            proveedor_cif=self.cif,
            obra_codigo=self.obra,
            approved=payload.approved,
            busqueda_contratos=estado_busqueda(self.cif, self.obra, self.rastro),
        )

    def doc_label(self, *, document_id):
        return "SS-0026122"

    def record_undo(self, **kwargs):
        self.undo.append(kwargs)


class _RefetchFalso:
    def __init__(self, *, lanza: Exception | None = None):
        self.llamadas: list[str] = []
        self._lanza = lanza

    def refetch(self, *, document_id):
        self.llamadas.append(document_id)
        if self._lanza is not None:
            raise self._lanza
        return ContratoRefetchOutcome(
            status="queued", count=0, selected_contrato_codigo=None,
            message="Re-búsqueda de contratos encolada.", cif=None,
            obra_codigo=None,
        )


class _PublicadorFalso:
    def __init__(self):
        self.publicados: list[tuple[str, object]] = []

    def publicar(self, nombre_cola, mensaje):
        self.publicados.append((nombre_cola, mensaje))
        return True


def _rastro(cif=CIF_MAL, obra=OBRA, resultado=BUSQUEDA_NINGUNO):
    return RastroBusquedaContratos(
        cif=cif, obra=obra, resultado=resultado, at_utc=FECHA,
    )


def _guardar(repo, refetch, *, cif, obra=OBRA, approved=False):
    servicio = ReviewService(repo, default_reviewer="revisor")
    payload = MergeDocumentUpdatePayload(
        proveedor_cif=cif, obra_codigo=obra, approved=approved,
    )
    return servicio.save_document_y_buscar_si_cambia(
        document_id=DOC_ID, payload=payload, refetch_client=refetch,
    )


# ------------------------------------------------------------------ #
# Cambia CIF u obra ⇒ relanza
# ------------------------------------------------------------------ #
def test_f052_d4a_guardar_con_cif_distinto_del_rastro_relanza():
    repo = _RepositorioFalso(cif=CIF_MAL, obra=OBRA, rastro=_rastro())
    refetch = _RefetchFalso()
    detalle, busqueda = _guardar(repo, refetch, cif=CIF_BUENO)
    assert refetch.llamadas == [DOC_ID]
    assert busqueda is not None and busqueda.status == "queued"
    assert detalle.proveedor_cif == CIF_BUENO
    assert len(repo.guardados) == 1, "primero se guarda, luego se busca"


def test_f052_d4a_guardar_con_obra_distinta_del_rastro_relanza():
    repo = _RepositorioFalso(cif=CIF_MAL, obra=OBRA, rastro=_rastro())
    refetch = _RefetchFalso()
    _guardar(repo, refetch, cif=CIF_MAL, obra="0696")
    assert refetch.llamadas == [DOC_ID]


def test_f052_d4a_relanza_por_la_cola_de_persistencia_con_force():
    """La misma vía que «Guardar y volver a buscar»: ``ColasRefetchClient``."""
    from ruesma_comun.colas import COLA_PERSISTENCIA
    from ruesma_comun.colas.mensajes import MensajePersistencia

    repo = _RepositorioFalso(cif=CIF_MAL, obra=OBRA, rastro=_rastro())
    publicador = _PublicadorFalso()
    _, busqueda = _guardar(
        repo, ColasRefetchClient(publicador=publicador), cif=CIF_BUENO,
    )
    [(cola, mensaje)] = publicador.publicados
    assert cola == COLA_PERSISTENCIA
    assert isinstance(mensaje, MensajePersistencia)
    assert mensaje.document_id == DOC_ID and mensaje.force is True
    assert busqueda.status == "queued"


# ------------------------------------------------------------------ #
# Sin cambio ⇒ no busca
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("cif", "obra", "rastro"),
    [
        (CIF_MAL, OBRA, _rastro()),
        ("b 82890580", "691", _rastro()),  # mismo CIF y obra normalizados
        (CIF_MAL, OBRA, _rastro(resultado=BUSQUEDA_ERROR)),
        (CIF_MAL, OBRA, _rastro(resultado=BUSQUEDA_ENCONTRADOS)),
    ],
    ids=["igual", "igual_normalizado", "error_sin_cambio",
         "encontrados_sin_cambio"],
)
def test_f052_d4a_guardar_sin_cambio_de_cif_ni_obra_no_busca(cif, obra, rastro):
    repo = _RepositorioFalso(cif=CIF_MAL, obra=OBRA, rastro=rastro)
    refetch = _RefetchFalso()
    _, busqueda = _guardar(repo, refetch, cif=cif, obra=obra)
    assert refetch.llamadas == []
    assert busqueda is None
    assert len(repo.guardados) == 1


def test_f052_d4a_aprobar_no_relanza_aunque_cambie_el_cif():
    repo = _RepositorioFalso(cif=CIF_MAL, obra=OBRA, rastro=_rastro())
    refetch = _RefetchFalso()
    _, busqueda = _guardar(repo, refetch, cif=CIF_BUENO, approved=True)
    assert refetch.llamadas == [] and busqueda is None


def test_f052_d4a_sin_cliente_de_refetch_solo_guarda():
    """Los otros PUT del front (valorar, elegir contrato, «Guardar y volver
    a buscar») no piden la búsqueda: ya la lanzan ellos o no la quieren."""
    repo = _RepositorioFalso(cif=CIF_MAL, obra=OBRA, rastro=_rastro())
    detalle, busqueda = _guardar(repo, None, cif=CIF_BUENO)
    assert busqueda is None
    assert detalle.busqueda_contratos.estado == ESTADO_BUSQUEDA_DESFASADA


def test_f052_d4a_si_relanzar_falla_el_guardado_se_queda_y_se_avisa(caplog):
    repo = _RepositorioFalso(cif=CIF_MAL, obra=OBRA, rastro=_rastro())
    refetch = _RefetchFalso(lanza=RuntimeError("cola caída"))
    with caplog.at_level(logging.ERROR):
        detalle, busqueda = _guardar(repo, refetch, cif=CIF_BUENO)
    assert detalle.proveedor_cif == CIF_BUENO
    assert busqueda.status == "sigrid_error"
    assert "cola caída" in busqueda.message
    assert "no se pudo relanzar" in busqueda.message
    assert any(r.exc_info for r in caplog.records)


def test_f052_d4a_guardado_normal_sigue_igual():
    """``save_document`` no cambia: devuelve el detalle y nunca busca."""
    repo = _RepositorioFalso(cif=CIF_MAL, obra=OBRA, rastro=_rastro())
    servicio = ReviewService(repo, default_reviewer="revisor")
    detalle = servicio.save_document(
        document_id=DOC_ID,
        payload=MergeDocumentUpdatePayload(proveedor_cif=CIF_BUENO,
                                           obra_codigo=OBRA),
    )
    assert isinstance(detalle, DocumentDetailPayload)


@pytest.mark.parametrize(
    ("vista", "esperado"),
    [
        (None, False),
        (BusquedaContratosVista(estado="sin_rastro"), True),
        (BusquedaContratosVista(estado="vigente"), False),
        (BusquedaContratosVista(estado="error"), False),
        (BusquedaContratosVista(estado="sin_datos"), False),
        (BusquedaContratosVista(estado="desfasada"), True),
    ],
)
def test_f052_d4a_solo_el_desfase_o_la_falta_de_rastro_relanzan(vista, esperado):
    assert debe_relanzar_busqueda(vista) is esperado


# ------------------------------------------------------------------ #
# La vista marca «buscando…»
# ------------------------------------------------------------------ #
def _bloque(render_detalle, documento_detalle, vista, **extra):
    documento = documento_detalle().model_copy(update={
        "proveedor_cif": CIF_BUENO, "obra_codigo": OBRA,
        "contratos": [], "busqueda_contratos": vista,
    })
    html = render_detalle(documento, **extra)
    inicio = html.index('<section class="contrato-section">')
    return re.sub(r"\s+", " ", html[inicio:html.index("</section>", inicio)])


def test_f052_d4a_la_vista_marca_buscando_y_sigue_diciendo_con_que_se_busco(
    render_detalle, documento_detalle,
):
    vista = BusquedaContratosVista(
        estado=ESTADO_BUSQUEDA_DESFASADA, cif=CIF_MAL, obra=OBRA,
        fecha=FECHA, resultado=BUSQUEDA_NINGUNO,
    )
    bloque = _bloque(render_detalle, documento_detalle, vista, buscando=True)
    assert 'id="busqueda-buscando"' in bloque
    assert "Buscando" in bloque
    assert CIF_MAL in bloque and "todavía no se han buscado" in bloque


def test_f052_d4a_sin_busqueda_en_marcha_no_marca_buscando(
    render_detalle, documento_detalle,
):
    desfasada = BusquedaContratosVista(
        estado=ESTADO_BUSQUEDA_DESFASADA, cif=CIF_MAL, obra=OBRA,
        fecha=FECHA, resultado=BUSQUEDA_NINGUNO,
    )
    assert 'id="busqueda-buscando"' not in _bloque(
        render_detalle, documento_detalle, desfasada,
    )
    # Ya llegó el resultado (rastro = datos actuales): aunque la URL traiga
    # todavía ``buscando=1``, no se marca nada.
    vigente = BusquedaContratosVista(
        estado=ESTADO_BUSQUEDA_VIGENTE, cif=CIF_BUENO, obra=OBRA,
        fecha=FECHA, resultado=BUSQUEDA_NINGUNO,
    )
    assert 'id="busqueda-buscando"' not in _bloque(
        render_detalle, documento_detalle, vigente, buscando=True,
    )


# ------------------------------------------------------------------ #
# O-B4: el deshacer restaura CIF, obra y rastro a la vez
# ------------------------------------------------------------------ #
class _FactoriaSqlite:
    def __init__(self, motor):
        self._motor = motor

    def create_session(self):
        return Session(self._motor)


@pytest.fixture
def repositorio_sqlite(monkeypatch):
    from infrastructure.database.orm_models import Base
    from infrastructure.database.review_repository import (
        AlbaranReviewRepository,
    )

    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    repo = AlbaranReviewRepository(_FactoriaSqlite(motor))
    monkeypatch.setattr(repo, "initialize", lambda: True)
    with Session(motor) as sesion:
        sesion.execute(text(
            "INSERT INTO albaran_documents_merge (id, provider_origin, "
            "source_filename, source_mime_type, source_sha256, prompt_key, "
            "schema_name, model_name, raw_extraction_json, created_at_utc, "
            "is_active, approved, proveedor_cif, obra_codigo, "
            "contratos_busqueda_cif, contratos_busqueda_obra, "
            "contratos_busqueda_resultado, contratos_busqueda_at_utc) VALUES "
            "(:id, 'merge', 'SS-0026122.pdf', 'application/pdf', :sha, 'p', "
            "'s', 'm', '{}', '2026-09-29', 1, 0, :cif, :obra, :cif, :obra, "
            "'ninguno', :fecha)"
        ), {"id": DOC_ID, "sha": "0" * 64, "cif": CIF_MAL, "obra": OBRA,
            "fecha": FECHA})
        sesion.commit()
    yield repo, motor
    motor.dispose()


def _vista_actual(repo, motor):
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    with Session(motor) as sesion:
        doc = sesion.get(AlbaranDocumentMergeOrm, DOC_ID)
        return repo._build_merge_detail(
            merge_doc=doc, available_views=[], provider_snapshots=[],
            contratos=[], selected_contrato_codigo=None,
        ).busqueda_contratos


def test_f052_d4a_ob4_deshacer_restaura_cif_obra_y_rastro_juntos(
    repositorio_sqlite,
):
    repo, motor = repositorio_sqlite
    # 1) «Guardar» toma la foto ANTES de guardar (como `save_document`).
    foto = repo.snapshot_row(table="albaran_documents_merge", row_id=DOC_ID)
    assert foto["values"]["contratos_busqueda_cif"] == CIF_MAL

    # 2) El revisor corrige el CIF: desfase ⇒ se relanzaría la búsqueda.
    with Session(motor) as sesion:
        sesion.execute(text(
            "UPDATE albaran_documents_merge SET proveedor_cif = :c WHERE id = :i"
        ), {"c": CIF_BUENO, "i": DOC_ID})
        sesion.commit()
    assert debe_relanzar_busqueda(_vista_actual(repo, motor))

    # 3) sv3 sella el rastro nuevo: vigente, ya no hay nada que relanzar.
    with Session(motor) as sesion:
        sesion.execute(text(
            "UPDATE albaran_documents_merge SET contratos_busqueda_cif = :c, "
            "contratos_busqueda_resultado = 'encontrados' WHERE id = :i"
        ), {"c": CIF_BUENO, "i": DOC_ID})
        sesion.commit()
    assert _vista_actual(repo, motor).estado == ESTADO_BUSQUEDA_VIGENTE

    # 4) Deshacer el guardado: vuelven el CIF viejo Y su rastro viejo.
    with Session(motor) as sesion:
        repo._undo_apply_restore(sesion, foto)
        sesion.commit()
    vista = _vista_actual(repo, motor)
    assert vista == BusquedaContratosVista(
        estado=ESTADO_BUSQUEDA_VIGENTE, cif=CIF_MAL, obra=OBRA, fecha=FECHA,
        resultado=BUSQUEDA_NINGUNO,
    )
    assert not debe_relanzar_busqueda(vista), (
        "tras deshacer, CIF y rastro coinciden: el siguiente «Guardar» sin "
        "cambios no debe buscar"
    )


# ------------------------------------------------------------------ #
# Lo que el endpoint devuelve al portal tras «Guardar»
# ------------------------------------------------------------------ #
def _outcome(status, message="m"):
    return ContratoRefetchOutcome(
        status=status, count=0, selected_contrato_codigo=None,
        message=message, cif=None, obra_codigo=None,
    )


@pytest.mark.parametrize(
    ("aprobado", "busqueda", "mensaje", "buscando"),
    [
        (False, None, "Documento guardado", False),
        (True, None, "Documento guardado y aprobado", False),
        (False, _outcome("queued"),
         "Documento guardado. Buscando contratos con el CIF y la obra guardados…",
         True),
        # fallback local síncrono: el resultado ya está al recargar
        (False, _outcome("found_single", "1 contrato encontrado."),
         "Documento guardado. 1 contrato encontrado.", False),
        (False, _outcome("sigrid_error", "no se pudo relanzar: x"),
         "Documento guardado. no se pudo relanzar: x", False),
    ],
    ids=["sin_busqueda", "aprobado", "encolada", "local", "fallo"],
)
def test_f052_d4a_aviso_de_guardado(aprobado, busqueda, mensaje, buscando):
    from application.services.busqueda_contratos import aviso_de_guardado

    assert aviso_de_guardado(aprobado=aprobado, busqueda=busqueda) == (
        mensaje, buscando,
    )


@pytest.mark.parametrize("obra", ["12", "1234"])
def test_f052_cr_c1_guardar_con_obra_que_sv3_no_admite_no_relanza_en_bucle(obra):
    """CR-C1: sv3 ya selló `sin_datos` para esa obra; guardar sin cambios no busca."""
    rastro = _rastro(cif=CIF_MAL, obra=None, resultado="sin_datos")
    repo = _RepositorioFalso(cif=CIF_MAL, obra=obra, rastro=rastro)
    refetch = _RefetchFalso()
    _, busqueda = _guardar(repo, refetch, cif=CIF_MAL, obra=obra)
    assert refetch.llamadas == [] and busqueda is None


# ------------------------------------------------------------------ #
# O-C1 (decisión del humano, 2026-10-01): sin rastro, el primer «Guardar»
# busca una vez; después rige la regla normal.
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("rastro", [None, RastroBusquedaContratos()],
                         ids=["sin_rastro", "rastro_vacio"])
def test_f052_oc1_sin_rastro_el_primer_guardar_busca(rastro):
    repo = _RepositorioFalso(cif=CIF_BUENO, obra=OBRA, rastro=rastro)
    refetch = _RefetchFalso()
    _, busqueda = _guardar(repo, refetch, cif=CIF_BUENO)
    assert refetch.llamadas == [DOC_ID]
    assert busqueda.status == "queued"


def test_f052_oc1_sin_rastro_y_obra_invalida_busca_una_vez_y_no_en_bucle():
    """sv3 sella `sin_datos` con la obra a None; desde ahí hay rastro y un
    «Guardar» sin cambios no vuelve a publicar."""
    repo = _RepositorioFalso(cif=CIF_BUENO, obra="12", rastro=None)
    refetch = _RefetchFalso()
    _guardar(repo, refetch, cif=CIF_BUENO, obra="12")
    assert refetch.llamadas == [DOC_ID]
    # sv3 procesa el mensaje y sella (CIF normalizado, obra inválida ⇒ None)
    repo.rastro = _rastro(cif=CIF_BUENO, obra=None, resultado="sin_datos")
    _, busqueda = _guardar(repo, refetch, cif=CIF_BUENO, obra="12")
    _, busqueda = _guardar(repo, refetch, cif=CIF_BUENO, obra="12")
    assert refetch.llamadas == [DOC_ID], "una sola búsqueda"
    assert busqueda is None


def test_f052_oc1_sin_rastro_la_vista_marca_buscando_tambien_con_contratos(
    render_detalle, documento_detalle,
):
    """Documento antiguo con contratos listados: al relanzar, el aviso sale
    con «Buscando…» aunque normalmente no se pinte."""
    from domain.models.review_models import ContratoPayload

    sin_rastro = BusquedaContratosVista(estado="sin_rastro")
    documento = documento_detalle().model_copy(update={
        "proveedor_cif": CIF_BUENO, "obra_codigo": OBRA,
        "contratos": [ContratoPayload(id=1, codigo_contrato="CTSU24/0402")],
        "busqueda_contratos": sin_rastro,
    })
    html = render_detalle(documento, buscando=True)
    assert 'id="busqueda-buscando"' in html
    assert 'data-estado-inicial="sin_rastro"' in html
    assert 'id="busqueda-buscando"' not in render_detalle(documento)


def test_f052_oc1_sin_rastro_y_sin_contratos_marca_buscando(
    render_detalle, documento_detalle,
):
    bloque = _bloque(render_detalle, documento_detalle,
                     BusquedaContratosVista(estado="sin_rastro"), buscando=True)
    assert 'id="busqueda-buscando"' in bloque
    assert "no consta" in bloque
