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


# ================================================================ #
# Resolver determinista de cabecera: dobles (R7, R8)
# ================================================================ #
class RepoResolverFake:
    """Doble de ``HeaderMergeRepository``: cabecera fija y registro de lo
    que el resolver escribe. Cualquier otro método del puerto, no-op."""

    def __init__(self, hdr) -> None:
        self._hdr = hdr
        self.resueltos: list[dict] = []

    def get_merge_header_for_resolution(self, *, document_id):
        return self._hdr

    def update_merge_resolved_header(self, **kwargs) -> None:
        self.resueltos.append(kwargs)

    def get_merge_lines_for_scoring(self, *, document_id):
        return [{"codigo": "", "concepto": "ARIDO 0/4", "contexto_linea_json": None}]

    def __getattr__(self, nombre):
        def _no_op(**kwargs):
            return None
        return _no_op


class ObraClientFake:
    def __init__(self, candidatos) -> None:
        self._candidatos = candidatos
        self.busquedas = 0

    def search_obras(self):
        self.busquedas += 1
        return list(self._candidatos)


class ProveedorClientFake:
    def __init__(self) -> None:
        self.obras_consultadas: list[str] = []

    def search_proveedores(self):
        return []

    def fetch_contratos_resumen_por_obra(self, *, codigo_obra):
        self.obras_consultadas.append(codigo_obra)
        return []

    def fetch_proveedor_by_cif(self, *, cif):
        return None


def _hdr(obra_codigo, obra_nombre="CONSERVATORIO MARIEMMA", proveedor_cif=None):
    from domain.models.header_resolution_models import MergeHeaderForResolution

    return MergeHeaderForResolution(
        obra_codigo=obra_codigo, obra_nombre=obra_nombre, obra_direccion=None,
        proveedor_cif=proveedor_cif, proveedor_nombre="HERMANOS SAN JUAN",
    )


def _resolver(hdr, candidatos):
    from application.services.header_resolver_service import HeaderResolverService

    repo = RepoResolverFake(hdr)
    obras = ObraClientFake(candidatos)
    proveedores = ProveedorClientFake()
    servicio = HeaderResolverService(
        obra_client=obras, proveedor_client=proveedores, repository=repo,
    )
    servicio.resolve_merge_document(merge_document_id=DOC)
    return repo, obras, proveedores


# ================================================================ #
# R7 — la obra deducida por texto se escribe canonizada
# ================================================================ #
@pytest.mark.parametrize(
    ("de_sigrid", "escrito"),
    [
        ("227", "0227"),
        (" 227 ", "0227"),
        ("0691", "0691"),
        ("var", "VAR"),
        ("GG", "GG"),          # no encaja: tal cual, recortado (como hoy)
        (" 0578-B ", "0578-B"),
    ],
)
def test_f070_r7_obra_deducida_por_texto_canonizada(de_sigrid, escrito):
    repo, obras, proveedores = _resolver(
        _hdr(None), [_obra(de_sigrid, "CONSERVATORIO MARIEMMA")],
    )
    assert obras.busquedas == 1
    [resuelto] = repo.resueltos
    assert resuelto["obra_codigo_det"] == escrito
    # y es la obra efectiva con la que se buscan los proveedores de la obra
    assert proveedores.obras_consultadas == [escrito]


def test_f070_r7_sin_coincidencia_no_escribe_obra():
    repo, _, _ = _resolver(_hdr(None, obra_nombre="NADA PARECIDO"), [_obra("227", "ZZZ QQQ")])
    [resuelto] = repo.resueltos
    assert resuelto["obra_codigo_det"] is None


# ================================================================ #
# R8 — VAR y POSTV2 son obras válidas para sv3 (sin código nuevo en sv3:
# lo heredan de ``normalizar_codigo_obra``)
# ================================================================ #
@pytest.mark.parametrize(
    ("en_merge", "consultado"),
    [("VAR", "VAR"), ("POSTV2", "POSTV2"), ("var", "VAR"), (" Postv2 ", "POSTV2")],
)
def test_f070_r8_la_red_de_obra_consulta_var_y_no_la_descarta(en_merge, consultado):
    repo = RepoObraFake(codigo=en_merge)
    cliente = ClienteObraFake(_obra(consultado, "OBRAS VARIAS"))
    assert ObraEnrichmentService(client=cliente, repository=repo).enrich_merge_document(
        merge_document_id=DOC,
    ) is True
    assert cliente.llamadas == [consultado]
    assert repo.descartes == []
    assert repo.campos_actualizados[0] == "OBRAS VARIAS"


@pytest.mark.parametrize("obra", ["VAR", "POSTV2"])
def test_f070_r8_el_resolver_respeta_var_y_la_usa_como_obra_efectiva(obra):
    """Con VAR la obra ya es válida: no se deduce otra por texto (aunque el
    nombre case con una obra de Sigrid) y es la obra en la que se buscan los
    proveedores."""
    repo, obras, proveedores = _resolver(
        _hdr(obra), [_obra("0900", "CONSERVATORIO MARIEMMA")],
    )
    assert obras.busquedas == 0
    [resuelto] = repo.resueltos
    assert resuelto["obra_codigo_det"] is None
    assert proveedores.obras_consultadas == [obra]


class RepoContratosFake:
    """Lo que ``ContratoEnrichmentService.enrich_merge_document`` usa del
    repositorio; el resto del puerto, no-op."""

    def __init__(self, cif: str, obra: str | None) -> None:
        self._cif, self._obra = cif, obra
        self.sellos: list[tuple] = []
        self.notas: list[str] = []

    def get_merge_cif_and_obra(self, *, document_id):
        return self._cif, self._obra

    def get_merge_fecha(self, *, document_id):
        return "2026-10-14"

    def append_review_note(self, *, document_id, nota):
        self.notas.append(nota)

    def get_existing_pdf_paths(self, *, document_id):
        return {}

    def get_selected_contrato_codigo(self, *, document_id):
        return None

    def get_merge_lines_for_scoring(self, *, document_id):
        return []

    def update_merge_proveedor_nombre(self, *, document_id, nombre_proveedor):
        return True

    def sellar_busqueda_contratos(self, *, document_id, cif, obra, resultado):
        self.sellos.append((cif, obra, resultado))

    def __getattr__(self, nombre):
        def _no_op(**kwargs):
            return None
        return _no_op


class ClienteContratosFake:
    def __init__(self) -> None:
        self.llamadas: list[tuple[str, str]] = []

    def fetch_contratos(self, *, cif_proveedor, codigo_obra_normalizado):
        self.llamadas.append((cif_proveedor, codigo_obra_normalizado))
        return []


@pytest.mark.parametrize(
    ("en_merge", "sellada"),
    [("VAR", "VAR"), ("POSTV2", "POSTV2"), (" var ", "VAR"), ("686", "0686")],
)
def test_f070_r8_la_busqueda_de_contratos_busca_en_var_y_lo_sella(en_merge, sellada):
    from application.services.contrato_enrichment_service import (
        ContratoEnrichmentService,
    )

    repo = RepoContratosFake("B82899550", en_merge)
    cliente = ClienteContratosFake()
    ContratoEnrichmentService(client=cliente, repository=repo).enrich_merge_document(
        merge_document_id=DOC,
    )
    assert cliente.llamadas == [("B82899550", sellada)]
    assert repo.sellos == [("B82899550", sellada, "ninguno")]
    assert not any("[ACCION REQUERIDA]" in n for n in repo.notas)
