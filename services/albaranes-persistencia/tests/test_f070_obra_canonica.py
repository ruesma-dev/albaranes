# tests/test_f070_obra_canonica.py
"""F-070 · sv3 sella la obra canónica (R6–R9).

Regla del humano: todo código de obra lleva el 0 inicial salvo VAR y POSTV2.
sv3 es donde se SELLA el merge: el normalizador de cabecera canoniza la obra
(correo y papel) antes de ``repository.save``; el resolver determinista
escribe la obra deducida canonizada; VAR y POSTV2 pasan a ser obras válidas
para la red de obra, el resolver y la búsqueda de contratos. Nada reescribe
los merges ya guardados (sin migración).

Sin red ni BBDD: dobles.
"""
from __future__ import annotations

import hashlib

import pytest

from application.pipelines.persist_albaran_pipeline import (
    PersistAlbaranPipeline,
    PersistAlbaranRequest,
)
from application.services.albaran_normalizer import AlbaranNormalizer
from application.services.obra_enrichment_service import ObraEnrichmentService
from domain.models.extraction_models import CabeceraAlbaran
from domain.models.obra_models import ObraEnrichmentResult
from domain.models.persistence_models import ExistingDocument, StoredFile

DOC = "doc-f070"
PDF = b"%PDF-1.4 albaran F-070 HERMANOS SAN JUAN"
SHA = hashlib.sha256(PDF).hexdigest()


# ================================================================ #
# R6 — el normalizador de cabecera canoniza la obra
# ================================================================ #
@pytest.mark.parametrize(
    ("leido", "sellado"),
    [
        ("686", "0686"),
        (" 686 ", "0686"),
        ("0686", "0686"),
        ("var", "VAR"),
        (" Var ", "VAR"),
        ("postv2", "POSTV2"),
        ("1234", "1234"),        # no encaja: como hoy (la red lo descarta)
        ("gg", "GG"),            # no encaja: como hoy (mayúsculas)
        ("06  86", "06 86"),     # no encaja: espacios colapsados, como hoy
        (None, None),
        ("   ", None),
    ],
)
def test_f070_r6_normalize_obra_codigo(leido, sellado):
    assert AlbaranNormalizer.normalize_obra_codigo(leido) == sellado


def test_f070_r6_normalize_header_sella_la_obra_canonica():
    cabecera = CabeceraAlbaran(obra_codigo=" 686 ", numero_albaran="ss-1")
    normalizada = AlbaranNormalizer().normalize_header(cabecera)
    assert normalizada.obra_codigo == "0686"
    assert normalizada.numero_albaran == "SS-1"


# --- R6 de punta a punta: lo que llega a ``repository.save`` -------- #
_META = {
    "prompt_key": "albaran_revision_fase2_es",
    "schema": "albaran_v2",
    "source_filename": "SS-1.pdf",
    "source_mime_type": "application/pdf",
    "source_sha256": SHA,
    "model": "modelo-de-prueba",
    "processed_at_utc": "2026-10-14T10:00:00Z",
}


def _bloque(obra: str | None) -> dict:
    return {
        "meta": dict(_META),
        "data": {
            "cabecera": {
                "proveedor_nombre": "HERMANOS SAN JUAN",
                "numero_albaran": "SS-1",
                "obra_codigo": obra,
            },
            "lineas": [{"concepto": "ARIDO 0/4", "cantidad": 7.5}],
        },
    }


def _envelope(merge: str | None, proveedores: dict[str, str | None]) -> dict:
    envelope = _bloque(merge)
    for nombre, obra in proveedores.items():
        envelope[nombre] = _bloque(obra)
    return envelope


class _Repositorio:
    """Documento nuevo; ``save`` guarda el envelope que recibe."""

    def __init__(self) -> None:
        self.guardados: list = []

    def get_by_sha256(self, sha256):
        return None

    def buscar_conservado_por_alta(self, sha256):
        return None

    def save(self, *, envelope, context, stored_file):
        self.guardados.append(envelope)
        return ExistingDocument(
            document_id=DOC, source_sha256=SHA, sharepoint_url=None, stored_lines=1,
        )

    def get_selected_contrato_codigo(self, *, document_id):
        return None


class _Almacen:
    def upload(self, **kwargs):
        return StoredFile(
            drive_id="d", item_id="i", relative_path="albaranes/SS-1.pdf",
            web_url=None, share_url=None,
        )


def _persistir(envelope: dict):
    repositorio = _Repositorio()
    pipeline = PersistAlbaranPipeline(
        repository=repositorio, document_storage=_Almacen(), normalizer=AlbaranNormalizer(),
    )
    pipeline.run(
        PersistAlbaranRequest(
            filename="SS-1.pdf", mime_type="application/pdf", file_bytes=PDF,
            extraction_envelope=envelope, context={},
        )
    )
    (guardado,) = repositorio.guardados
    return guardado


def test_f070_r6_pipeline_sella_0686_en_el_merge_y_en_cada_proveedor():
    guardado = _persistir(
        _envelope("686", {"gemini": " 686", "claude": "0686", "google_document_ai": "686 "}),
    )
    assert guardado.data.cabecera.obra_codigo == "0686"
    assert guardado.gemini.data.cabecera.obra_codigo == "0686"
    assert guardado.claude.data.cabecera.obra_codigo == "0686"
    assert guardado.google_document_ai.data.cabecera.obra_codigo == "0686"


def test_f070_r6_pipeline_sella_var_y_postv2_en_mayusculas():
    guardado = _persistir(_envelope("var", {"gemini": "Postv2"}))
    assert guardado.data.cabecera.obra_codigo == "VAR"
    assert guardado.gemini.data.cabecera.obra_codigo == "POSTV2"


def test_f070_r6_pipeline_deja_como_hoy_lo_que_no_encaja():
    guardado = _persistir(_envelope("1234", {"gemini": None, "claude": "gg"}))
    assert guardado.data.cabecera.obra_codigo == "1234"
    assert guardado.gemini.data.cabecera.obra_codigo is None
    assert guardado.claude.data.cabecera.obra_codigo == "GG"


# ================================================================ #
# Red de obra: dobles del puerto y del cliente (R6, R8, R9)
# ================================================================ #
class RepoObraFake:
    """Doble de ``ObraMergeRepository``: registra lo que le piden."""

    def __init__(self, *, codigo: str | None) -> None:
        self._codigo = codigo
        self.campos_actualizados: tuple | None = None
        self.descartes: list[tuple[str | None, str]] = []
        self.retiradas = 0

    def get_merge_obra_codigo(self, *, document_id: str) -> str | None:
        return self._codigo

    def update_merge_obra_fields(self, *, document_id, obra_nombre, obra_direccion) -> None:
        self.campos_actualizados = (obra_nombre, obra_direccion)

    def descartar_obra_no_valida(self, *, document_id, codigo_leido, motivo) -> None:
        self.descartes.append((codigo_leido, motivo))

    def retirar_revision_obra(self, *, document_id: str) -> None:
        self.retiradas += 1


class ClienteObraFake:
    def __init__(self, resultado: ObraEnrichmentResult | None) -> None:
        self._resultado = resultado
        self.llamadas: list[str] = []

    def fetch_obra_by_codigo(self, *, codigo_obra_normalizado: str):
        self.llamadas.append(codigo_obra_normalizado)
        return self._resultado


def _obra(codigo: str, nombre: str) -> ObraEnrichmentResult:
    return ObraEnrichmentResult(
        codigo_obra=codigo, nombre_obra=nombre, direccion_linea1="CALLE FALSA 1",
        direccion_linea2=None, codigo_postal="50001", municipio="ZARAGOZA",
        provincia="ZARAGOZA",
    )


def test_f070_r6_la_red_sigue_descartando_lo_que_no_encaja():
    repo = RepoObraFake(codigo="1234")
    cliente = ClienteObraFake(_obra("1234", "NO"))
    assert ObraEnrichmentService(client=cliente, repository=repo).enrich_merge_document(
        merge_document_id=DOC,
    ) is False
    assert repo.descartes == [("1234", "obra_codigo_invalido:1234")]
    assert cliente.llamadas == []


# ================================================================ #
# R9 — sin migración: la red no reescribe la obra de un merge guardado
# ================================================================ #
def test_f070_r9_la_red_no_reescribe_un_686_guardado():
    """Un merge viejo con ``686``: la red consulta ``0686`` y rellena nombre
    y dirección, pero el puerto ni siquiera tiene con qué reescribir el
    código: ``update_merge_obra_fields`` solo lleva nombre y dirección."""
    repo = RepoObraFake(codigo="686")
    cliente = ClienteObraFake(_obra("0686", "OBRA HSJ"))
    assert ObraEnrichmentService(client=cliente, repository=repo).enrich_merge_document(
        merge_document_id=DOC,
    ) is True
    assert cliente.llamadas == ["0686"]
    assert repo.campos_actualizados[0] == "OBRA HSJ"
    assert repo.descartes == []


def test_f070_r9_el_normalizador_solo_cambia_la_obra():
    """Canonizar no toca ningún otro campo de la cabecera (ni el origen de la
    obra, que no viaja en la cabecera de la extracción)."""
    cabecera = CabeceraAlbaran(
        proveedor_nombre=" hermanos  san juan ", proveedor_cif="b-12",
        numero_albaran=" ss-1 ", obra_codigo="686", obra_nombre=" obra ",
    )
    normalizador = AlbaranNormalizer()
    antes = normalizador.normalize_header(cabecera.model_copy(update={"obra_codigo": "0686"}))
    despues = normalizador.normalize_header(cabecera)
    assert despues == antes
    assert "obra_codigo_origen" not in CabeceraAlbaran.model_fields
