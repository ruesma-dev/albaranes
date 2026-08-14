# tests/test_f002_red_obra.py
"""F-002 · Red determinista de OBRA (R5, R6, R7, R16, R17).

Una obra que la IA se inventa (caso de referencia: 0937) no puede quedar
persistida como si existiera. Estos tests fijan ese contrato sobre
``ObraEnrichmentService`` con dobles: ni red ni BBDD.
"""
from __future__ import annotations

import pytest

from application.services.obra_enrichment_service import ObraEnrichmentService
from domain.models.obra_models import ObraEnrichmentResult
from infrastructure.database.sqlalchemy_albaran_repository import (
    MOTIVO_OBRA_PREFIJO,
    NOTA_OBRA_PREFIJO,
    anadir_motivo_revision,
    quitar_motivos_con_prefijo,
    sustituir_nota_por_prefijo,
)

DOC = "doc-1"


class RepoObraFake:
    """Doble del puerto ``ObraMergeRepository``: registra lo que le piden."""

    def __init__(self, *, codigo: str | None, falla: bool = False) -> None:
        self._codigo = codigo
        self._falla = falla
        self.campos_actualizados: tuple[str | None, str | None] | None = None
        self.descartes: list[tuple[str | None, str]] = []
        self.retiradas = 0

    def get_merge_obra_codigo(self, *, document_id: str) -> str | None:
        return self._codigo

    def update_merge_obra_fields(
        self, *, document_id: str, obra_nombre, obra_direccion,
    ) -> None:
        self.campos_actualizados = (obra_nombre, obra_direccion)

    def descartar_obra_no_valida(
        self, *, document_id: str, codigo_leido, motivo: str,
    ) -> None:
        if self._falla:
            raise RuntimeError("BBDD caida")
        self.descartes.append((codigo_leido, motivo))

    def retirar_revision_obra(self, *, document_id: str) -> None:
        if self._falla:
            raise RuntimeError("BBDD caida")
        self.retiradas += 1


class ClienteObraFake:
    def __init__(self, *, resultado=None, error: Exception | None = None):
        self._resultado = resultado
        self._error = error
        self.llamadas: list[str] = []

    def fetch_obra_by_codigo(self, *, codigo_obra_normalizado: str):
        self.llamadas.append(codigo_obra_normalizado)
        if self._error is not None:
            raise self._error
        return self._resultado


def _obra(codigo: str = "0695") -> ObraEnrichmentResult:
    return ObraEnrichmentResult(
        codigo_obra=codigo,
        nombre_obra="EDIFICIO EJEMPLO",
        direccion_linea1="CALLE FALSA 1",
        direccion_linea2=None,
        codigo_postal="50001",
        municipio="ZARAGOZA",
        provincia="ZARAGOZA",
    )


def _servicio(repo, cliente, **kwargs) -> ObraEnrichmentService:
    return ObraEnrichmentService(
        client=cliente, repository=repo, **kwargs,
    )


# ---------------------------------------------------------------- #
# R5 — obra normalizable que NO existe en Sigrid.
# ---------------------------------------------------------------- #
def test_f002_r5_obra_inexistente_se_descarta_y_marca_revision() -> None:
    repo = RepoObraFake(codigo="0937")
    cliente = ClienteObraFake(resultado=None)

    resultado = _servicio(repo, cliente).enrich_merge_document(
        merge_document_id=DOC,
    )

    assert resultado is False
    assert repo.descartes == [("0937", "obra_inexistente:0937")]
    assert repo.campos_actualizados is None
    assert repo.retiradas == 0


def test_f002_r5_obra_existente_no_se_descarta() -> None:
    repo = RepoObraFake(codigo="0695")
    cliente = ClienteObraFake(resultado=_obra())

    assert _servicio(repo, cliente).enrich_merge_document(
        merge_document_id=DOC,
    ) is True
    assert repo.descartes == []
    assert repo.campos_actualizados is not None


# ---------------------------------------------------------------- #
# R6 — codigo NO nulo que no normaliza.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("codigo", ["1234", "12345", "abc", "09.37"])
def test_f002_r6_codigo_no_normalizable_se_descarta(codigo: str) -> None:
    repo = RepoObraFake(codigo=codigo)
    cliente = ClienteObraFake(resultado=_obra())

    assert _servicio(repo, cliente).enrich_merge_document(
        merge_document_id=DOC,
    ) is False
    assert repo.descartes == [(codigo, f"obra_codigo_invalido:{codigo}")]
    # Sin codigo valido no se molesta a Sigrid.
    assert cliente.llamadas == []


@pytest.mark.parametrize("codigo", [None, "", "   "])
def test_f002_r6_sin_codigo_leido_no_marca_revision(codigo) -> None:
    """Que el albaran no traiga obra no es un error de identificacion:
    lo resuelve el HeaderResolver y, si no, lo ve el revisor."""
    repo = RepoObraFake(codigo=codigo)
    cliente = ClienteObraFake(resultado=_obra())

    assert _servicio(repo, cliente).enrich_merge_document(
        merge_document_id=DOC,
    ) is False
    assert repo.descartes == []
    assert cliente.llamadas == []


# ---------------------------------------------------------------- #
# R7 — retirada del aviso e idempotencia.
# ---------------------------------------------------------------- #
def test_f002_r7_obra_validada_retira_el_aviso() -> None:
    repo = RepoObraFake(codigo="0695")
    cliente = ClienteObraFake(resultado=_obra())

    _servicio(repo, cliente).enrich_merge_document(merge_document_id=DOC)

    assert repo.retiradas == 1


def test_f002_r7_reproceso_de_obra_invalida_repite_el_mismo_motivo() -> None:
    repo = RepoObraFake(codigo="0937")
    cliente = ClienteObraFake(resultado=None)
    servicio = _servicio(repo, cliente)

    servicio.enrich_merge_document(merge_document_id=DOC)
    servicio.enrich_merge_document(merge_document_id=DOC)

    # El servicio no inventa motivos nuevos en cada pasada: es el mismo,
    # y el repositorio lo deduplica (tests de abajo).
    assert repo.descartes == [
        ("0937", "obra_inexistente:0937"),
        ("0937", "obra_inexistente:0937"),
    ]


def test_f002_r7_motivo_no_se_duplica_al_reprocesar() -> None:
    primero = anadir_motivo_revision(None, "obra_inexistente:0937")
    segundo = anadir_motivo_revision(primero, "obra_inexistente:0937")

    assert segundo == primero
    assert primero.count("obra_inexistente:0937") == 1


def test_f002_r7_motivo_nuevo_se_suma_a_los_existentes() -> None:
    con_uno = anadir_motivo_revision(None, "obra_inexistente:0937")
    con_dos = anadir_motivo_revision(con_uno, "fecha_albaran_fuera_de_rango:2023-01-01")

    assert "obra_inexistente:0937" in con_dos
    assert "fecha_albaran_fuera_de_rango:2023-01-01" in con_dos


@pytest.mark.parametrize("roto", ["no soy json", "{}", "[", "12"])
def test_f002_r7_motivos_con_json_roto_no_revientan(roto: str) -> None:
    salida = anadir_motivo_revision(roto, "obra_inexistente:0937")

    assert "obra_inexistente:0937" in salida


def test_f002_r7_retirada_quita_solo_los_motivos_de_obra() -> None:
    reasons = anadir_motivo_revision(
        anadir_motivo_revision(None, "obra_inexistente:0937"),
        "fecha_albaran_fuera_de_rango:2023-01-01",
    )

    quedan = quitar_motivos_con_prefijo(reasons, MOTIVO_OBRA_PREFIJO)

    assert "obra_inexistente" not in quedan
    assert "fecha_albaran_fuera_de_rango:2023-01-01" in quedan


def test_f002_r7_retirada_del_ultimo_motivo_deja_la_columna_nula() -> None:
    reasons = anadir_motivo_revision(None, "obra_codigo_invalido:1234")

    assert quitar_motivos_con_prefijo(reasons, MOTIVO_OBRA_PREFIJO) is None


def test_f002_r7_la_nota_de_obra_no_se_acumula() -> None:
    nota = f"{NOTA_OBRA_PREFIJO} el codigo leido '0937' no existe."
    una = sustituir_nota_por_prefijo(None, prefijo=NOTA_OBRA_PREFIJO, nota=nota)
    dos = sustituir_nota_por_prefijo(una, prefijo=NOTA_OBRA_PREFIJO, nota=nota)

    assert dos == una
    assert dos.count(NOTA_OBRA_PREFIJO) == 1


def test_f002_r7_la_nota_de_obra_no_pisa_las_de_otras_redes() -> None:
    previas = "[AVISO] Proveedor sin CIF: no deducible."
    nota = f"{NOTA_OBRA_PREFIJO} el codigo leido '0937' no existe."

    con_obra = sustituir_nota_por_prefijo(
        previas, prefijo=NOTA_OBRA_PREFIJO, nota=nota,
    )
    sin_obra = sustituir_nota_por_prefijo(
        con_obra, prefijo=NOTA_OBRA_PREFIJO, nota=None,
    )

    assert previas in con_obra and nota in con_obra
    assert sin_obra == previas


# ---------------------------------------------------------------- #
# R16 — best-effort: nada de esto puede romper la persistencia.
# ---------------------------------------------------------------- #
def test_f002_r16_excepcion_del_cliente_no_rompe_ni_descarta() -> None:
    repo = RepoObraFake(codigo="0937")
    cliente = ClienteObraFake(error=RuntimeError("sigrid-api 500"))

    assert _servicio(repo, cliente).enrich_merge_document(
        merge_document_id=DOC,
    ) is False
    # El documento queda como estaba: un fallo de red NO es una obra
    # inexistente.
    assert repo.descartes == []


def test_f002_r16_fallo_del_repositorio_al_descartar_no_rompe() -> None:
    repo = RepoObraFake(codigo="0937", falla=True)
    cliente = ClienteObraFake(resultado=None)

    assert _servicio(repo, cliente).enrich_merge_document(
        merge_document_id=DOC,
    ) is False


def test_f002_r16_fallo_del_repositorio_al_retirar_no_rompe() -> None:
    repo = RepoObraFake(codigo="0695", falla=True)
    cliente = ClienteObraFake(resultado=_obra())

    # El enriquecimiento del nombre/direccion debe seguir su curso.
    assert _servicio(repo, cliente).enrich_merge_document(
        merge_document_id=DOC,
    ) is True


# ---------------------------------------------------------------- #
# R17 — con la red apagada, comportamiento EXACTO al previo.
# ---------------------------------------------------------------- #
def test_f002_r17_red_apagada_no_descarta_obra_inexistente() -> None:
    repo = RepoObraFake(codigo="0937")
    cliente = ClienteObraFake(resultado=None)

    assert _servicio(repo, cliente, enabled_red=False).enrich_merge_document(
        merge_document_id=DOC,
    ) is False
    assert repo.descartes == []
    assert repo.retiradas == 0


def test_f002_r17_red_apagada_no_retira_avisos() -> None:
    repo = RepoObraFake(codigo="0695")
    cliente = ClienteObraFake(resultado=_obra())

    assert _servicio(repo, cliente, enabled_red=False).enrich_merge_document(
        merge_document_id=DOC,
    ) is True
    assert repo.retiradas == 0
    assert repo.campos_actualizados is not None


def test_f002_r17_servicio_deshabilitado_no_toca_nada() -> None:
    repo = RepoObraFake(codigo="0937")
    cliente = ClienteObraFake(resultado=None)

    assert _servicio(repo, cliente, enabled=False).enrich_merge_document(
        merge_document_id=DOC,
    ) is False
    assert repo.descartes == []
    assert cliente.llamadas == []
