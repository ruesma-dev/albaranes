# tests/test_f048_r28_red_obra.py
"""F-048 · R28: la red de obra de sv3 (F-002) se aplica igual venga la obra
del correo o del papel.

Test de REGRESION: la red no se toca (design §6). Lee ``obra_codigo`` del
merge, que sale de la cabecera que dejo sv2, y no mira ``origen_datos``. Se
recorre el camino real —envelope de sv2 → normalizador → merge → servicio de
la red— con dobles del repositorio y del cliente de Sigrid:

- Obra del CORREO que no existe en Sigrid (sigrid-api caido en sv2, asi que
  el correo mando sin validar: ``validada = null``) ⇒ se descarta y va a
  revision, IGUAL que si la hubiera leido el papel.
- Obra que existe ⇒ se valida igual, venga de donde venga.
- **Aviso B de la review del bloque C2 (fila 4)**: con ``correo_confirma_papel``
  la cabecera llega con la forma de la LISTA (CR-C5: ``09-45`` ⇒ ``0945``) y
  la red la encuentra. Con la forma del papel —lo que hacia sv2 antes de
  CR-C5— la red la descartaba por codigo invalido.

Sin red, sin BBDD y sin LLM. Codigos inventados.
"""
from __future__ import annotations

import pytest
from application.services.albaran_confidence_service import AlbaranConfidenceService
from application.services.albaran_normalizer import AlbaranNormalizer
from application.services.obra_enrichment_service import ObraEnrichmentService
from domain.models.extraction_models import ExtractionEnvelope
from domain.models.obra_models import ObraEnrichmentResult

_META = {
    "prompt_key": "albaran_revision_fase2_es",
    "schema": "albaran_v2",
    "source_filename": "SS-3.pdf",
    "source_mime_type": "application/pdf",
    "source_sha256": "d" * 64,
    "model": "modelo-de-prueba",
    "processed_at_utc": "2026-09-24T10:00:00Z",
}


def _origen(*, fuente: str, motivo: str, final: str | None, papel: str | None, correo: str | None = None,
            candidatos: list[str] | None = None, discrepancia: bool = False, validada: bool | None = None) -> dict:
    return {
        "version": 1, "correo_presente": motivo != "sin_correo", "correo_sha256": None, "correo_truncado": False,
        "evidencia": None,
        "obra": {"fuente": fuente, "motivo": motivo, "valor_final": final, "valor_correo": correo,
                 "candidatos_correo": candidatos or [], "valor_papel": papel,
                 "discrepancia": discrepancia, "validada": validada},
    }


# El envelope que deja sv2 para cada caso: la cabecera YA es la resuelta.
DEL_CORREO = {  # fila 3 sin lista en sv2: manda el correo sin validar
    "obra_codigo": "0999",
    "origen": _origen(fuente="correo", motivo="correo_unico", final="0999", correo="0999", candidatos=["0999"],
                      papel="0937", discrepancia=True, validada=None),
}
DEL_PAPEL = {  # sin correo: la obra es la que leyo la IA en el papel
    "obra_codigo": "0999",
    "origen": _origen(fuente="papel", motivo="sin_correo", final="0999", papel="0999"),
}


def _obra_del_merge(obra_codigo: str | None, origen: dict) -> str | None:
    """``obra_codigo`` tal y como queda en el merge (lo que lee la red)."""
    envelope = ExtractionEnvelope.model_validate({
        "meta": _META,
        "data": {
            "cabecera": {"proveedor_nombre": "HORMIGONES DEL SUR", "numero_albaran": "SS-3", "obra_codigo": obra_codigo},
            "lineas": [{"concepto": "HA-25/B/20/IIa", "cantidad": 7.5}],
            "origen_datos": origen,
        },
    })
    normalizado = envelope.model_copy(update={
        "data": AlbaranNormalizer().normalize_provider_document(document=envelope.data, provider_origin="openai"),
    })
    analisis = AlbaranConfidenceService().build_merge_analysis(openai=normalizado, gemini=None)
    return analisis.merged_envelope.data.cabecera.obra_codigo


class _RepoObra:
    """Doble del puerto ``ObraMergeRepository`` (el mismo contrato que usa F-002)."""

    def __init__(self, codigo: str | None) -> None:
        self._codigo = codigo
        self.descartes: list[tuple[str | None, str]] = []
        self.retiradas = 0
        self.actualizada = False

    def get_merge_obra_codigo(self, *, document_id):
        return self._codigo

    def update_merge_obra_fields(self, *, document_id, obra_nombre, obra_direccion):
        self.actualizada = True

    def descartar_obra_no_valida(self, *, document_id, codigo_leido, motivo):
        self.descartes.append((codigo_leido, motivo))

    def retirar_revision_obra(self, *, document_id):
        self.retiradas += 1


class _Sigrid:
    def __init__(self, existe: bool) -> None:
        self.existe = existe
        self.llamadas: list[str] = []

    def fetch_obra_by_codigo(self, *, codigo_obra_normalizado):
        self.llamadas.append(codigo_obra_normalizado)
        if not self.existe:
            return None
        return ObraEnrichmentResult(
            codigo_obra=codigo_obra_normalizado, nombre_obra="OBRA DEMO", direccion_linea1="CALLE FALSA 1",
            direccion_linea2=None, codigo_postal="50001", municipio="ZARAGOZA", provincia="ZARAGOZA",
        )


def _red(obra_codigo: str | None, *, existe: bool) -> tuple[_RepoObra, _Sigrid]:
    repo, sigrid = _RepoObra(obra_codigo), _Sigrid(existe)
    ObraEnrichmentService(client=sigrid, repository=repo).enrich_merge_document(merge_document_id="merge-1")
    return repo, sigrid


# ---------------------------------------------------------------- #
# Correo o papel: la misma red.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("caso", [DEL_CORREO, DEL_PAPEL], ids=["obra_del_correo", "obra_del_papel"])
def test_f048_r28_obra_inexistente_se_descarta_y_va_a_revision_venga_de_donde_venga(caso):
    obra = _obra_del_merge(caso["obra_codigo"], caso["origen"])
    repo, sigrid = _red(obra, existe=False)

    assert obra == "0999"
    assert sigrid.llamadas == ["0999"]
    assert repo.descartes == [("0999", "obra_inexistente:0999")]
    assert repo.actualizada is False


@pytest.mark.parametrize("caso", [DEL_CORREO, DEL_PAPEL], ids=["obra_del_correo", "obra_del_papel"])
def test_f048_r28_obra_existente_se_valida_igual_venga_de_donde_venga(caso):
    repo, sigrid = _red(_obra_del_merge(caso["obra_codigo"], caso["origen"]), existe=True)

    assert sigrid.llamadas == ["0999"]
    assert repo.descartes == []
    assert repo.actualizada is True
    assert repo.retiradas == 1


# ---------------------------------------------------------------- #
# Aviso B (fila 4) resuelto por CR-C5.
# ---------------------------------------------------------------- #
FILA_4 = _origen(fuente="papel", motivo="correo_confirma_papel", final="0945", papel="09-45",
                 candidatos=["0945", "0320"], validada=True)


def test_f048_r28_fila4_la_cabecera_con_la_forma_de_la_lista_la_encuentra_la_red():
    """Lo que deja sv2 desde CR-C5: ``valor_final`` = forma de la lista."""
    obra = _obra_del_merge(FILA_4["obra"]["valor_final"], FILA_4)
    repo, sigrid = _red(obra, existe=True)

    assert obra == "0945"
    assert sigrid.llamadas == ["0945"]
    assert repo.descartes == []
    assert repo.actualizada is True


def test_f048_r28_fila4_con_la_forma_del_papel_la_red_la_descartaba():
    """Contraste (por que existe CR-C5): el papel ``09-45`` no normaliza en la
    red de sv3, que no se toca, y una obra que el correo CONFIRMA acababa sin
    obra y en revision."""
    obra = _obra_del_merge(FILA_4["obra"]["valor_papel"], FILA_4)
    repo, sigrid = _red(obra, existe=True)

    assert sigrid.llamadas == []
    assert repo.descartes == [("09-45", "obra_codigo_invalido:09-45")]
