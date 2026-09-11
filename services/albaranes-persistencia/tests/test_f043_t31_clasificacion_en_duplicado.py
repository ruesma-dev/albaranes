# tests/test_f043_t31_clasificacion_en_duplicado.py
"""F-043 · R22 — la clasificacion se persiste TAMBIEN en el re-proceso.

Defecto REAL medido el 2026-09-11 ejecutando T31 contra el pipeline
local con LLM de verdad (albaran SS-0003967, document_id
``1dc06154-00ce-4c80-9de3-7a41cc0a08c3``):

- sv2 clasifico bien: ``data.clasificacion`` = residuos / 100.0 / ia2, y
  el envelope quedo en ``envelopes/1dc06154-..._phase_1.json``.
- sv3 lo proceso y dejo las SEIS columnas ``tipologia*`` a NULL.

Causa: el PDF ya estaba persistido (mismo ``source_sha256``), asi que
``PersistAlbaranPipeline.run`` tomo la rama de DUPLICADO —«Documento
duplicado detectado», linea 26 del log de sv3—, que re-enriquece obra,
cabecera y contratos y dispara la valoracion, pero NO llama a
``repository.save``. Y la unica escritura de las seis columnas vivia
dentro de ``save``. Resultado: todo documento ya existente —y eso
incluye CUALQUIER re-publicacion en ``q-persistencia``— se queda sin
clasificacion aunque el envelope la traiga sellada.

Los tests que ya existian (``test_f043_persistencia_clasificacion.py``)
no lo veian porque atacan ``build_merge_analysis`` y
``campos_clasificacion_merge`` por separado: nadie recorria ``run()``.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import hashlib

import pytest

from application.pipelines.persist_albaran_pipeline import (
    PersistAlbaranPipeline,
    PersistAlbaranRequest,
)
from domain.models.persistence_models import ExistingDocument

_PDF = b"%PDF-1.4 SS-0003967"
_SHA256 = hashlib.sha256(_PDF).hexdigest()
_MERGE_ID = "1dc06154-00ce-4c80-9de3-7a41cc0a08c3"

_CLASIFICACION = {
    "familia": "residuos",
    "confianza_pct": 100.0,
    "motivo": "Gestor autorizado de RCD, LER 170604 y contenedores.",
    "mixto": False,
    "familias_secundarias": [],
    "origen": "ia2",
}


def _envelope(
    *,
    con_clasificacion: bool = True,
    model: str = "gemini-3.7-flash",
) -> dict:
    """El envelope FINAL de sv2, ya saneado por el worker de sv3.

    Es plano (``{meta, data, debug}``): ``phase_merge`` nunca cuelga
    sub-envelopes por proveedor, asi que ``model`` es lo unico que dice
    que IA lo produjo. De ahi el parametro: la clasificacion tiene que
    llegar sea cual sea el proveedor.
    """
    data: dict = {
        "cabecera": {
            "proveedor_nombre": "SALMEDINA",
            "proveedor_cif": "B82899550",
            "numero_albaran": "SS-0003967",
            "fecha": "2024-07-10",
        },
        "lineas": [{"concepto": "Contenedor RCD 6 m3", "cantidad": 1.0}],
    }
    if con_clasificacion:
        data["clasificacion"] = dict(_CLASIFICACION)
    return {
        "meta": {
            "prompt_key": "albaran_revision_fase2_residuos",
            "schema": "albaran_v2",
            "source_filename": "SALMEDINA_0003967.pdf",
            "source_mime_type": "application/pdf",
            "source_sha256": _SHA256,
            "model": model,
            "processed_at_utc": "2026-09-11T08:55:12+00:00",
        },
        "data": data,
        "debug": {"phase_1": {}},
    }


class RepoDuplicadoFake:
    """Repositorio que ya tiene el documento (misma huella del PDF)."""

    def __init__(self, *, falla_escritura: bool = False) -> None:
        self.falla_escritura = falla_escritura
        self.clasificaciones: list[tuple[str, object]] = []
        self.guardados = 0

    def initialize(self) -> None:
        return None

    def get_by_sha256(self, source_sha256: str) -> ExistingDocument:
        return ExistingDocument(
            document_id=_MERGE_ID,
            source_sha256=source_sha256,
            sharepoint_url=None,
            stored_lines=1,
        )

    def save(self, **_kwargs):  # pragma: no cover — el duplicado no guarda
        self.guardados += 1
        raise AssertionError("La rama de duplicado no debe llamar a save().")

    def update_merge_clasificacion(self, *, document_id, clasificacion):
        if self.falla_escritura:
            raise RuntimeError("UPDATE roto")
        self.clasificaciones.append((document_id, clasificacion))

    def get_merge_cif_and_obra(self, *, document_id: str):
        return "B82899550", "0687"

    def get_selected_contrato_codigo(self, *, document_id: str):
        return "CTSU24/0228"

    def has_selected_contrato_with_lines(self, *, document_id: str):
        return True, "CTSU24/0228"


def _pipeline(repo: RepoDuplicadoFake) -> PersistAlbaranPipeline:
    """Pipeline pelado: en la rama de duplicado no hay upload ni merge."""
    return PersistAlbaranPipeline(
        repository=repo,
        document_storage=object(),
        normalizer=object(),
    )


def _run(repo: RepoDuplicadoFake, envelope: dict):
    return _pipeline(repo).run(
        PersistAlbaranRequest(
            filename="SALMEDINA_0003967.pdf",
            mime_type="application/pdf",
            file_bytes=_PDF,
            extraction_envelope=envelope,
            context={},
        )
    )


# ------------------------------------------------------------------ #
# R22 — el defecto: un documento ya persistido pierde la clasificacion.
# ------------------------------------------------------------------ #

def test_f043_r22_el_duplicado_persiste_la_clasificacion_del_envelope():
    """El caso SS-0003967 exacto: re-proceso de un PDF ya conocido."""
    repo = RepoDuplicadoFake()

    resultado = _run(repo, _envelope())

    assert resultado.duplicate is True
    assert len(repo.clasificaciones) == 1
    document_id, clasificacion = repo.clasificaciones[0]
    assert document_id == _MERGE_ID
    assert clasificacion.familia == "residuos"
    assert clasificacion.confianza_pct == 100.0
    assert clasificacion.origen == "ia2"
    assert clasificacion.mixto is False
    assert clasificacion.familias_secundarias == []


@pytest.mark.parametrize(
    "model",
    ["gemini-3.7-flash", "gpt-5.2", "claude-opus-4-20250514"],
)
def test_f043_r22_el_duplicado_la_persiste_sea_cual_sea_el_proveedor(model):
    """La clasificacion la sella el resolver de sv2 sobre el envelope
    FINAL, que llega plano. Ninguna rama de sv3 puede depender de que la
    extraccion la hiciera OpenAI."""
    repo = RepoDuplicadoFake()

    _run(repo, _envelope(model=model))

    assert [doc for doc, _ in repo.clasificaciones] == [_MERGE_ID]


def test_f043_r22_la_escribe_antes_de_disparar_la_valoracion():
    """Orden obligatorio: sv6 lee las seis columnas al valorar. Si la
    escritura fuera despues del trigger, sv6 podria leer NULL."""
    orden: list[str] = []

    class RepoOrdenado(RepoDuplicadoFake):
        def update_merge_clasificacion(self, *, document_id, clasificacion):
            orden.append("clasificacion")
            super().update_merge_clasificacion(
                document_id=document_id,
                clasificacion=clasificacion,
            )

    class TriggerEspia:
        def trigger_async(self, **_kwargs) -> bool:
            orden.append("valoracion")
            return True

        def trigger_sync(self, **_kwargs):  # pragma: no cover
            raise AssertionError("el duplicado dispara en async")

    pipeline = PersistAlbaranPipeline(
        repository=RepoOrdenado(),
        document_storage=object(),
        normalizer=object(),
        valuation_trigger=TriggerEspia(),
    )
    pipeline.run(
        PersistAlbaranRequest(
            filename="SALMEDINA_0003967.pdf",
            mime_type="application/pdf",
            file_bytes=_PDF,
            extraction_envelope=_envelope(),
            context={},
        )
    )

    assert orden.index("clasificacion") < orden.index("valoracion")


# ------------------------------------------------------------------ #
# R27 — un envelope SIN clasificacion se comporta exactamente como hoy.
# ------------------------------------------------------------------ #

def test_f043_r27_el_duplicado_sin_clasificacion_no_escribe_nada():
    """Documento anterior a la feature: las columnas siguen a NULL. NO se
    infiere la familia por LER, producto, texto ni CIF."""
    repo = RepoDuplicadoFake()

    resultado = _run(repo, _envelope(con_clasificacion=False))

    assert resultado.duplicate is True
    assert repo.clasificaciones == []


# ------------------------------------------------------------------ #
# Best-effort: la escritura nunca puede tumbar el re-proceso.
# ------------------------------------------------------------------ #

def test_f043_r22_una_escritura_que_revienta_no_rompe_el_duplicado():
    repo = RepoDuplicadoFake(falla_escritura=True)

    resultado = _run(repo, _envelope())

    assert resultado.ok is True
    assert resultado.duplicate is True


def test_f043_r22_un_repositorio_sin_el_metodo_no_rompe_el_duplicado():
    """Duck-typing: el puerto ``AlbaranRepository`` solo declara
    ``save`` y ``get_by_sha256``. Un doble viejo no puede reventar."""

    class RepoSinMetodo:
        def initialize(self) -> None:
            return None

        def get_by_sha256(self, source_sha256: str) -> ExistingDocument:
            return ExistingDocument(
                document_id=_MERGE_ID,
                source_sha256=source_sha256,
                sharepoint_url=None,
                stored_lines=1,
            )

    resultado = _pipeline(RepoSinMetodo()).run(
        PersistAlbaranRequest(
            filename="SALMEDINA_0003967.pdf",
            mime_type="application/pdf",
            file_bytes=_PDF,
            extraction_envelope=_envelope(),
            context={},
        )
    )

    assert resultado.ok is True
    assert resultado.duplicate is True


# ------------------------------------------------------------------ #
# La escritura en si (repositorio), sin BBDD.
# ------------------------------------------------------------------ #

class _SesionFake:
    """Lo justo que usa ``update_merge_clasificacion``."""

    def __init__(self, documento) -> None:
        self.documento = documento
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> bool:
        return False

    def get(self, _orm, _document_id):
        return self.documento

    def commit(self) -> None:
        self.commits += 1


class _FabricaSesionFake:
    """Fábrica de sesiones sin BBDD, ya «inicializada» (no hay DDL)."""

    generation = 1

    def __init__(self, documento) -> None:
        self.sesion = _SesionFake(documento)

    def ensure_database_and_engine(self) -> None:
        return None

    def create_session(self):
        return self.sesion


def _repositorio(documento):
    from infrastructure.database.sqlalchemy_albaran_repository import (
        SqlAlchemyAlbaranRepository,
    )

    fabrica = _FabricaSesionFake(documento)
    repo = SqlAlchemyAlbaranRepository(fabrica)
    # El DDL no pinta en un test sin BBDD: se da por aplicado.
    repo._initialized_generation = fabrica.generation
    return repo, fabrica


class _MergeOrmFake:
    tipologia = None
    tipologia_confianza_pct = None
    tipologia_motivo = None
    tipologia_origen = None
    tipologia_mixta = None
    tipologia_secundarias_json = None


def _clasificacion_de(envelope: dict):
    from domain.models.extraction_models import ExtractionEnvelope

    return ExtractionEnvelope.model_validate(envelope).data.clasificacion


def test_f043_r22_update_merge_clasificacion_escribe_las_seis_columnas():
    documento = _MergeOrmFake()
    repo, fabrica = _repositorio(documento)

    assert repo.update_merge_clasificacion(
        document_id=_MERGE_ID,
        clasificacion=_clasificacion_de(_envelope()),
    ) is True
    assert documento.tipologia == "residuos"
    assert documento.tipologia_confianza_pct == 100.0
    assert documento.tipologia_origen == "ia2"
    assert documento.tipologia_mixta is False
    assert documento.tipologia_secundarias_json == "[]"
    assert fabrica.sesion.commits == 1


def test_f043_r27_update_merge_clasificacion_sin_clasificacion_no_escribe():
    documento = _MergeOrmFake()
    repo, fabrica = _repositorio(documento)

    assert repo.update_merge_clasificacion(
        document_id=_MERGE_ID,
        clasificacion=None,
    ) is False
    assert documento.tipologia is None
    assert fabrica.sesion.commits == 0


def test_f043_r22_update_merge_clasificacion_con_merge_inexistente():
    """Si el merge no está, no se inventa nada y tampoco revienta."""
    repo, fabrica = _repositorio(None)

    assert repo.update_merge_clasificacion(
        document_id=_MERGE_ID,
        clasificacion=_clasificacion_de(_envelope()),
    ) is False
    assert fabrica.sesion.commits == 0
