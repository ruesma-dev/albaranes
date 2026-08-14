# tests/test_f002_red_proveedor.py
"""F-002 · Red determinista de PROVEEDOR por CIF (R8–R11, R16, R17).

El proveedor es la razón social del bloque fiscal, no la marca del
logotipo. Cuando el CIF leído existe en el maestro ``prv`` de Sigrid, el
nombre se canoniza; cuando no existe, se PROPONE candidato y se marca
revisión, pero NUNCA se sobrescribe lo leído (decisión D3).

Sin red ni BBDD: cliente de sigrid-api y repositorio son dobles.
"""
from __future__ import annotations

import pytest

from application.services.header_resolver_service import (
    _NOTA_PROVEEDOR_PREFIX,
    HeaderResolverService,
)
from domain.models.header_resolution_models import (
    MergeHeaderForResolution,
    ProveedorObraResumen,
)

DOC = "doc-1"
CIF_LEIDO = "B50999888"


class RepoProveedorFake:
    def __init__(self, header: MergeHeaderForResolution, *, falla_marca=False):
        self._header = header
        self._falla_marca = falla_marca
        self.nombre_canonico: str | None = None
        self.marcas: list[tuple[str, str, str]] = []
        self.notas: list[str] = []
        self.prefijos_retirados: list[str] = []
        self.resoluciones: list[tuple[str | None, str | None, str]] = []

    def get_merge_header_for_resolution(self, *, document_id: str):
        return self._header

    def update_merge_resolved_header(
        self,
        *,
        document_id: str,
        obra_codigo_det: str | None,
        proveedor_cif_det: str | None,
        proveedor_origen: str = "deterministic",
    ) -> None:
        self.resoluciones.append(
            (obra_codigo_det, proveedor_cif_det, proveedor_origen),
        )

    def get_merge_lines_for_scoring(self, *, document_id: str) -> list[dict]:
        return []

    def append_review_note(self, *, document_id: str, nota: str) -> None:
        self.notas.append(nota)

    def remove_review_note_prefix(self, *, document_id: str, prefijo: str) -> None:
        self.prefijos_retirados.append(prefijo)

    def set_merge_proveedor_nombre_canonico(
        self, *, document_id: str, nombre: str,
    ) -> None:
        self.nombre_canonico = nombre

    def marcar_revision_cabecera(
        self, *, document_id: str, motivo: str, nota: str, nota_prefijo: str,
    ) -> None:
        if self._falla_marca:
            raise RuntimeError("BBDD caida")
        self.marcas.append((motivo, nota, nota_prefijo))


class ClienteProveedorFake:
    def __init__(
        self,
        *,
        por_cif: tuple[str, str | None] | None = None,
        error_cif: Exception | None = None,
        candidatos_obra: list[ProveedorObraResumen] | None = None,
        globales: list[tuple[str | None, str | None]] | None = None,
    ) -> None:
        self._por_cif = por_cif
        self._error_cif = error_cif
        self._candidatos = candidatos_obra or []
        self._globales = globales or []
        self.cifs_consultados: list[str] = []

    def fetch_proveedor_by_cif(self, *, cif: str):
        self.cifs_consultados.append(cif)
        if self._error_cif is not None:
            raise self._error_cif
        return self._por_cif

    def fetch_contratos_resumen_por_obra(self, *, codigo_obra: str):
        return list(self._candidatos)

    def search_proveedores(self):
        return list(self._globales)


class ClienteObraFake:
    def search_obras(self):
        return []


def _header(
    *,
    cif: str | None = CIF_LEIDO,
    nombre: str | None = "GRUPO OTTO HORPRESOL",
    obra: str | None = "0695",
) -> MergeHeaderForResolution:
    return MergeHeaderForResolution(
        obra_codigo=obra,
        obra_nombre="EDIFICIO EJEMPLO",
        obra_direccion="CALLE FALSA 1",
        proveedor_cif=cif,
        proveedor_nombre=nombre,
    )


def _candidato(cif: str, nombre: str) -> ProveedorObraResumen:
    return ProveedorObraResumen(
        cif=cif, nombre=nombre, codigos_contratos=("C1",), texto="hormigon",
    )


def _servicio(repo, cliente_prov, **kwargs) -> HeaderResolverService:
    return HeaderResolverService(
        obra_client=ClienteObraFake(),
        proveedor_client=cliente_prov,
        repository=repo,
        **kwargs,
    )


# ---------------------------------------------------------------- #
# R8 — CIF que existe en prv: el nombre pasa a ser la razón social.
# ---------------------------------------------------------------- #
def test_f002_r8_cif_existente_canoniza_el_nombre() -> None:
    repo = RepoProveedorFake(_header())
    cliente = ClienteProveedorFake(por_cif=(CIF_LEIDO, "HORPRESOL, S.L."))

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert repo.nombre_canonico == "HORPRESOL, S.L."
    assert repo.marcas == []
    assert cliente.cifs_consultados == [CIF_LEIDO]


def test_f002_r8_cif_existente_retira_el_aviso_previo() -> None:
    repo = RepoProveedorFake(_header())
    cliente = ClienteProveedorFake(por_cif=(CIF_LEIDO, "HORPRESOL, S.L."))

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert _NOTA_PROVEEDOR_PREFIX in repo.prefijos_retirados


def test_f002_r8_sin_razon_social_no_pisa_el_nombre_leido() -> None:
    """``prv.raz`` vacío no es un nombre canónico: no se sobrescribe."""
    repo = RepoProveedorFake(_header())
    cliente = ClienteProveedorFake(por_cif=(CIF_LEIDO, None))

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert repo.nombre_canonico is None
    assert repo.marcas == []


# ---------------------------------------------------------------- #
# R9 — CIF que no existe pero el nombre leído contiene un proveedor
# con contrato en la obra (caso GRUPO OTTO HORPRESOL).
# ---------------------------------------------------------------- #
def test_f002_r9_horpresol_deja_propuesta_a_revision() -> None:
    repo = RepoProveedorFake(_header())
    cliente = ClienteProveedorFake(
        por_cif=None,
        candidatos_obra=[
            _candidato("B99111222", "HORPRESOL, S.L."),
            _candidato("A11000111", "ARIDOS DEL EBRO SA"),
        ],
    )

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert len(repo.marcas) == 1
    motivo, nota, prefijo = repo.marcas[0]
    assert motivo == f"proveedor_cif_no_casa:{CIF_LEIDO}"
    assert prefijo == _NOTA_PROVEEDOR_PREFIX
    assert nota.startswith(_NOTA_PROVEEDOR_PREFIX)
    # La propuesta lleva CIF y razón social del candidato.
    assert "B99111222" in nota
    assert "HORPRESOL, S.L." in nota


def test_f002_r9_no_sobrescribe_el_cif_ni_el_nombre_leidos() -> None:
    repo = RepoProveedorFake(_header())
    cliente = ClienteProveedorFake(
        por_cif=None,
        candidatos_obra=[_candidato("B99111222", "HORPRESOL, S.L.")],
    )

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert repo.nombre_canonico is None
    assert repo.resoluciones == [(None, None, "deterministic")]


# ---------------------------------------------------------------- #
# R10 — CIF inexistente y ningún candidato que case.
# ---------------------------------------------------------------- #
def test_f002_r10_sin_candidato_marca_revision_sin_propuesta() -> None:
    repo = RepoProveedorFake(_header(nombre="TRANSPORTES MACOTRAN"))
    cliente = ClienteProveedorFake(
        por_cif=None,
        candidatos_obra=[_candidato("A11000111", "ARIDOS DEL EBRO SA")],
    )

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert len(repo.marcas) == 1
    motivo, nota, _ = repo.marcas[0]
    assert motivo == f"proveedor_cif_no_casa:{CIF_LEIDO}"
    assert "A11000111" not in nota
    assert CIF_LEIDO in nota


def test_f002_r10_sin_obra_efectiva_marca_revision_sin_propuesta() -> None:
    """Sin obra no hay «proveedores con contrato en la obra» que
    proponer, por muy bien que casara el nombre."""
    repo = RepoProveedorFake(_header(obra=None))
    cliente = ClienteProveedorFake(
        por_cif=None,
        candidatos_obra=[_candidato("B99111222", "HORPRESOL, S.L.")],
    )

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert len(repo.marcas) == 1
    motivo, nota, _ = repo.marcas[0]
    assert motivo == f"proveedor_cif_no_casa:{CIF_LEIDO}"
    assert "B99111222" not in nota


def test_f002_r10_un_parecido_por_debajo_del_umbral_no_se_propone() -> None:
    """Un token en comun de tres no es «casar»: proponer eso al revisor
    es peor que no proponer nada."""
    repo = RepoProveedorFake(_header(nombre="TRANSPORTES MACOTRAN NORTE"))
    cliente = ClienteProveedorFake(
        por_cif=None,
        candidatos_obra=[_candidato("B77000777", "MACOTRAN LOGISTICA GLOBAL")],
    )

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert "B77000777" not in repo.marcas[0][1]


def test_f002_r9_el_umbral_es_inclusivo() -> None:
    """Justo en el umbral (0.5) SI se propone: es el valor que el humano
    acepto reutilizar de HEADER_RESOLVER_MIN_SCORE."""
    repo = RepoProveedorFake(_header(nombre="HORMIGONES DEL EBRO"))
    cliente = ClienteProveedorFake(
        por_cif=None,
        candidatos_obra=[_candidato("B66000666", "EBRO CANTERAS")],
    )

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert "B66000666" in repo.marcas[0][1]


def test_f002_r9_ante_un_empate_gana_el_primer_candidato() -> None:
    """La propuesta tiene que ser estable: dos pasadas sobre el mismo
    documento no pueden proponer proveedores distintos."""
    repo = RepoProveedorFake(_header(nombre="HORMIGONES DEL EBRO"))
    cliente = ClienteProveedorFake(
        por_cif=None,
        candidatos_obra=[
            _candidato("B66000666", "EBRO CANTERAS"),
            _candidato("B55000555", "EBRO ARIDOS"),
        ],
    )

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    nota = repo.marcas[0][1]
    assert "B66000666" in nota
    assert "B55000555" not in nota


def test_f002_r10_sin_nombre_leido_la_nota_no_escupe_none() -> None:
    """La nota la lee una persona en el portal: 'None' ahí es una fuga
    de la implementación."""
    repo = RepoProveedorFake(_header(nombre=None))
    cliente = ClienteProveedorFake(por_cif=None)

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert "None" not in repo.marcas[0][1]


def test_f002_r9_la_propuesta_nombra_el_cif_leido_y_el_candidato() -> None:
    """La nota tiene que dar los dos datos: qué se leyó y qué se
    propone. Con uno solo, el revisor no puede decidir."""
    repo = RepoProveedorFake(_header())
    cliente = ClienteProveedorFake(
        por_cif=None,
        candidatos_obra=[_candidato("B99111222", "HORPRESOL, S.L.")],
    )

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    nota = repo.marcas[0][1]
    assert CIF_LEIDO in nota
    assert "GRUPO OTTO HORPRESOL" in nota
    assert "None" not in nota


# ---------------------------------------------------------------- #
# R11 — sin CIF, el flujo previo intacto (regresión).
# ---------------------------------------------------------------- #
def test_f002_r11_sin_cif_deduce_por_nombre_como_siempre() -> None:
    repo = RepoProveedorFake(_header(cif=None, nombre="ARIDOS DEL EBRO", obra=None))
    cliente = ClienteProveedorFake(
        globales=[("A11000111", "ARIDOS DEL EBRO SA")],
    )

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert repo.resoluciones == [(None, "A11000111", "deterministic")]
    assert repo.marcas == []
    assert cliente.cifs_consultados == []


@pytest.mark.parametrize("cif", [None, "", "   "])
def test_f002_r11_sin_cif_no_consulta_el_maestro_prv(cif) -> None:
    repo = RepoProveedorFake(_header(cif=cif, nombre=None, obra=None))
    cliente = ClienteProveedorFake()

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert cliente.cifs_consultados == []
    assert repo.marcas == []


# ---------------------------------------------------------------- #
# R16 — best-effort.
# ---------------------------------------------------------------- #
def test_f002_r16_error_consultando_el_cif_no_rompe_ni_marca() -> None:
    repo = RepoProveedorFake(_header())
    cliente = ClienteProveedorFake(error_cif=RuntimeError("sigrid-api 500"))

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    # Un fallo de red NO es un CIF inexistente: no se marca revisión.
    assert repo.marcas == []
    assert repo.resoluciones == [(None, None, "deterministic")]


def test_f002_r16_error_marcando_revision_no_rompe_la_persistencia() -> None:
    repo = RepoProveedorFake(_header(), falla_marca=True)
    cliente = ClienteProveedorFake(por_cif=None)

    _servicio(repo, cliente).resolve_merge_document(merge_document_id=DOC)

    assert repo.resoluciones == [(None, None, "deterministic")]


# ---------------------------------------------------------------- #
# R17 — red apagada: comportamiento EXACTO al previo.
# ---------------------------------------------------------------- #
def test_f002_r17_red_apagada_no_consulta_ni_marca() -> None:
    repo = RepoProveedorFake(_header())
    cliente = ClienteProveedorFake(por_cif=None)

    _servicio(repo, cliente, cif_enabled=False).resolve_merge_document(
        merge_document_id=DOC,
    )

    assert cliente.cifs_consultados == []
    assert repo.marcas == []
    assert repo.nombre_canonico is None
    # Comportamiento previo: con CIF presente solo se retiraba el aviso.
    assert repo.prefijos_retirados == [_NOTA_PROVEEDOR_PREFIX]
