# tests/test_f062_r14_repasadas_y_motivos.py
"""F-062 · R14, R15, R16 — re-pasadas idempotentes y motivos caducados.

Tres capas:

- ``depurar_motivos_proveedor`` (función pura del repositorio): qué motivos
  de proveedor siguen vivos para el CIF actual del merge.
- ``SqlAlchemyAlbaranRepository.aplicar_correccion_proveedor`` y
  ``retirar_motivos_proveedor`` sobre una sesión doble (sin BBDD).
- El resolver en pasadas sucesivas sobre un merge en memoria (T7).
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from domain.models.header_resolution_models import (
    NOTA_PROVEEDOR_CORREGIDO_PREFIJO,
)
from infrastructure.database.sqlalchemy_albaran_repository import (
    depurar_motivos_proveedor,
)

LEIDO = "B86056201"
REAL = "B66056201"
OTRO = "B18487421"
CORREGIDO = f"proveedor_cif_corregido:{LEIDO}>{REAL}"
NO_CASA = f"proveedor_cif_no_casa:{LEIDO}"


def _json(*motivos: str) -> str:
    return json.dumps(list(motivos), ensure_ascii=False, indent=2)


# ------------------------------------------------------------------ #
# Función pura · depurar_motivos_proveedor
# ------------------------------------------------------------------ #
def test_f062_r16_puro_retira_no_casa_de_otro_cif():
    nuevos, retiro_correccion = depurar_motivos_proveedor(
        _json("obra_no_existe:0937", NO_CASA), REAL,
    )
    assert json.loads(nuevos) == ["obra_no_existe:0937"]
    assert retiro_correccion is False


def test_f062_r16_puro_conserva_no_casa_del_cif_actual_normalizado():
    """La comparación es entre CIF normalizados: ``b-86056201`` es el
    mismo CIF que ``B86056201``."""
    original = _json("proveedor_cif_no_casa:b-86056201 ")
    assert depurar_motivos_proveedor(original, LEIDO) == (original, False)


def test_f062_r15_puro_retira_la_correccion_de_otro_cif_y_lo_dice():
    nuevos, retiro_correccion = depurar_motivos_proveedor(
        _json(CORREGIDO, "fecha_fuera_de_rango"), OTRO,
    )
    assert json.loads(nuevos) == ["fecha_fuera_de_rango"]
    assert retiro_correccion is True


def test_f062_r14_puro_conserva_la_correccion_del_cif_actual():
    original = _json(CORREGIDO)
    assert depurar_motivos_proveedor(original, REAL) == (original, False)
    assert depurar_motivos_proveedor(original, " b66056201") == (original, False)


def test_f062_r15_puro_lo_que_queda_vacio_es_none():
    assert depurar_motivos_proveedor(_json(CORREGIDO, NO_CASA), OTRO) == (None, True)


def test_f062_r16_puro_sin_motivos_de_proveedor_no_cambia_nada():
    original = _json("obra_no_existe:0937", "fecha_fuera_de_rango")
    assert depurar_motivos_proveedor(original, REAL) == (original, False)
    assert depurar_motivos_proveedor(None, REAL) == (None, False)
    assert depurar_motivos_proveedor("no es json", REAL) == ("no es json", False)


def test_f062_r15_puro_el_aplicado_es_lo_que_va_tras_el_ultimo_mayor_que():
    """El motivo sella ``<leído>><aplicado>``; un leído raro con ``>`` no
    confunde cuál es el aplicado."""
    original = _json(f"proveedor_cif_corregido:B8>6>{REAL}")
    assert depurar_motivos_proveedor(original, REAL) == (original, False)


# ------------------------------------------------------------------ #
# Repositorio · sesión doble
# ------------------------------------------------------------------ #
class _Resultado:
    def __init__(self, fila) -> None:
        self._fila = fila

    def first(self):
        return self._fila


class _Sesion:
    """Lo justo de una sesión SQLAlchemy para las escrituras de la red:
    ``get`` del merge (ORM) y SELECT/UPDATE crudos de ``review_notes``."""

    def __init__(self, documento) -> None:
        self.documento = documento
        self.confirmaciones = 0
        self.vaciados = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, _orm, document_id):
        if self.documento is None or document_id != self.documento.id:
            return None
        return self.documento

    def execute(self, sentencia, parametros=None):
        sql = " ".join(str(sentencia).split())
        if sql.startswith("SELECT review_notes"):
            return _Resultado((self.documento.review_notes,))
        if sql.startswith("UPDATE albaran_documents_merge SET review_notes"):
            self.documento.review_notes = parametros["notas"]
            return _Resultado(None)
        raise AssertionError(f"SQL inesperada: {sql}")

    def flush(self):
        self.vaciados += 1

    def commit(self):
        self.confirmaciones += 1


class _Fabrica:
    generation = 1

    def __init__(self, sesion) -> None:
        self.sesion = sesion

    def ensure_database_and_engine(self):
        pass

    def create_session(self):
        return self.sesion


def _documento(**campos):
    base = dict(
        id="doc-f062", obra_codigo="0720", obra_nombre=None, obra_direccion=None,
        proveedor_cif=LEIDO, proveedor_nombre="Hormigones Mat SL",
        proveedor_cif_origen="ia", review_required=False,
        review_reasons_json=None, review_notes=None,
    )
    base.update(campos)
    return SimpleNamespace(**base)


def _repo(documento):
    from infrastructure.database.sqlalchemy_albaran_repository import (
        SqlAlchemyAlbaranRepository,
    )

    sesion = _Sesion(documento)
    fabrica = _Fabrica(sesion)
    repo = SqlAlchemyAlbaranRepository(session_factory=fabrica)
    repo._initialized_generation = fabrica.generation  # sin crear tablas
    return repo, sesion


_NOTA = f"{NOTA_PROVEEDOR_CORREGIDO_PREFIJO}: leído {LEIDO} → {REAL}"


def _aplicar(repo, *, cif=REAL, nota=_NOTA, motivo=CORREGIDO):
    repo.aplicar_correccion_proveedor(
        document_id="doc-f062", cif=cif, nombre="HORMIGONES MAT, S.L.U.",
        motivo=motivo, nota=nota,
    )


def test_f062_r6_repo_aplica_cif_nombre_origen_revision_motivo_y_nota():
    doc = _documento(
        review_reasons_json=_json("obra_no_existe:0937", NO_CASA),
        review_notes="[AVISO] Obra algo\n[AVISO] Proveedor el CIF leido ...",
    )
    repo, sesion = _repo(doc)

    _aplicar(repo)

    assert (doc.proveedor_cif, doc.proveedor_nombre) == (REAL, "HORMIGONES MAT, S.L.U.")
    assert doc.proveedor_cif_origen == "deterministic"
    assert doc.review_required is True
    # R16: el no_casa del leído cae; los demás motivos se quedan.
    assert json.loads(doc.review_reasons_json) == ["obra_no_existe:0937", CORREGIDO]
    assert doc.review_notes.splitlines() == [
        "[AVISO] Obra algo", "[AVISO] Proveedor el CIF leido ...", _NOTA,
    ]
    assert sesion.confirmaciones == 1  # una sola transacción


def test_f062_r14_repo_aplicar_dos_veces_no_duplica_motivo_ni_nota():
    doc = _documento()
    repo, _ = _repo(doc)

    _aplicar(repo)
    _aplicar(repo)

    assert json.loads(doc.review_reasons_json) == [CORREGIDO]
    assert doc.review_notes == _NOTA


def test_f062_r15_repo_aplicar_otro_candidato_sustituye_motivo_y_nota():
    doc = _documento()
    repo, _ = _repo(doc)
    _aplicar(repo)

    otra_nota = f"{NOTA_PROVEEDOR_CORREGIDO_PREFIJO}: leído {LEIDO} → {OTRO}"
    otro_motivo = f"proveedor_cif_corregido:{LEIDO}>{OTRO}"
    _aplicar(repo, cif=OTRO, nota=otra_nota, motivo=otro_motivo)

    assert json.loads(doc.review_reasons_json) == [otro_motivo]
    assert doc.review_notes == otra_nota


def test_f062_r6_repo_aplicar_sobre_un_merge_que_no_existe_lanza():
    repo, sesion = _repo(None)
    with pytest.raises(KeyError):
        _aplicar(repo)
    assert sesion.confirmaciones == 0


def test_f062_r15_repo_retirar_quita_la_correccion_y_su_nota_sin_bajar_revision():
    doc = _documento(
        proveedor_cif=OTRO, review_required=True,
        review_reasons_json=_json(CORREGIDO, "fecha_fuera_de_rango"),
        review_notes=f"[AVISO] Obra algo\n{_NOTA}",
    )
    repo, sesion = _repo(doc)

    repo.retirar_motivos_proveedor(document_id="doc-f062", cif_actual=OTRO)

    assert json.loads(doc.review_reasons_json) == ["fecha_fuera_de_rango"]
    assert doc.review_notes == "[AVISO] Obra algo"
    assert doc.review_required is True
    assert sesion.confirmaciones == 1


def test_f062_r14_repo_retirar_con_el_cif_aplicado_no_toca_nada():
    doc = _documento(
        proveedor_cif=REAL, review_required=True,
        review_reasons_json=_json(CORREGIDO), review_notes=_NOTA,
    )
    antes = dict(vars(doc))
    repo, sesion = _repo(doc)

    repo.retirar_motivos_proveedor(document_id="doc-f062", cif_actual=REAL)

    assert vars(doc) == antes
    assert sesion.vaciados == 0


def test_f062_r16_repo_retirar_quita_no_casa_caducado_y_conserva_la_nota_corregida():
    """Sin motivo de corrección retirado, la nota ``[CORREGIDO]`` no se toca
    (aunque la hubiera): solo se retira junto a su motivo."""
    doc = _documento(
        proveedor_cif=REAL, review_required=True,
        review_reasons_json=_json(NO_CASA), review_notes=_NOTA,
    )
    repo, _ = _repo(doc)

    repo.retirar_motivos_proveedor(document_id="doc-f062", cif_actual=REAL)

    assert doc.review_reasons_json is None
    assert doc.review_notes == _NOTA
    assert doc.review_required is True


def test_f062_r15_repo_retirar_sobre_un_merge_que_no_existe_no_hace_nada():
    repo, sesion = _repo(None)
    repo.retirar_motivos_proveedor(document_id="doc-f062", cif_actual=REAL)
    assert sesion.confirmaciones == 0


def test_f062_r13_repo_la_cabecera_trae_el_origen_del_cif():
    repo, _ = _repo(_documento(proveedor_cif_origen="manual"))
    hdr = repo.get_merge_header_for_resolution(document_id="doc-f062")
    assert hdr.proveedor_cif_origen == "manual"
    assert hdr.proveedor_cif == LEIDO


# ------------------------------------------------------------------ #
# Resolver · pasadas sucesivas sobre un merge en memoria (T7)
# ------------------------------------------------------------------ #
from doble_sigrid_api import (  # noqa: E402
    CIF_HORMIGONERA_EMPATE,
    CIF_HORMIGONES_MAT,
    CIF_LEIDO_19407,
    RAZ_HORMIGONES_MAT,
    DobleSigridApi,
    fixture_f062,
)
from f062_dobles import RepoRed, pasada  # noqa: E402

_CORREGIDO_19407 = f"proveedor_cif_corregido:{CIF_LEIDO_19407}>{CIF_HORMIGONES_MAT}"


def _cliente():
    return DobleSigridApi(fixture_f062()).cliente()


def _merge_19407(**kwargs) -> RepoRed:
    return RepoRed(cif=CIF_LEIDO_19407, nombre="Hormigones Mat SL", obra="0720", **kwargs)


def _notas_corregido(repo: RepoRed) -> list[str]:
    return [n for n in repo.lineas_notas() if n.startswith(NOTA_PROVEEDOR_CORREGIDO_PREFIJO)]


def test_f062_r14_la_repasada_no_duplica_y_conserva_la_nota_corregida():
    repo = _merge_19407()
    pasada(_cliente(), repo)
    nota = _notas_corregido(repo)

    pasada(_cliente(), repo)  # duplicado o «Solo volver a buscar»
    pasada(_cliente(), repo)

    assert len(repo.aplicadas) == 1  # la 2.ª y la 3.ª encuentran el CIF en prv
    assert (repo.cif, repo.nombre) == (CIF_HORMIGONES_MAT, RAZ_HORMIGONES_MAT)
    assert repo.lista_motivos() == [_CORREGIDO_19407]
    assert _notas_corregido(repo) == nota and len(nota) == 1
    assert repo.review_required is True
    assert repo.marcas == []


def test_f062_r14_la_nota_corregida_sobrevive_al_borrado_de_avisos_de_proveedor():
    """D6: cada pasada borra lo que empieza por «[AVISO] Proveedor»; la
    nota de la corrección lleva prefijo propio y no cae."""
    repo = _merge_19407()
    pasada(_cliente(), repo)
    repo.notas = f"[AVISO] Proveedor algo viejo\n{repo.notas}"

    pasada(_cliente(), repo)

    assert repo.lineas_notas() == _notas_corregido(repo)
    assert len(repo.lineas_notas()) == 1


def test_f062_r15_el_revisor_elige_otro_y_se_retira_la_correccion():
    repo = _merge_19407()
    pasada(_cliente(), repo)
    # «Elegir proveedor» en sv4: escribe un prv.cif (existe) y relanza.
    repo.cif, repo.nombre = CIF_HORMIGONERA_EMPATE, "otra"
    repo.notas = f"{repo.notas}\n[AVISO] Obra algo"

    pasada(_cliente(), repo)

    assert repo.lista_motivos() == []
    assert _notas_corregido(repo) == []
    assert repo.lineas_notas() == ["[AVISO] Obra algo"]
    assert repo.review_required is True  # D7 de F-002: no se baja
    assert len(repo.aplicadas) == 1


def test_f062_r15_tambien_sin_candidato_claro_se_retira_la_correccion_caducada():
    """Un merge cuyo CIF (manual, inexistente) ya no es el aplicado: la
    corrección vieja cae y queda la marca de hoy."""
    repo = _merge_19407(origen="manual")
    repo.motivos = _json(_CORREGIDO_19407)
    repo.notas = f"{NOTA_PROVEEDOR_CORREGIDO_PREFIJO}: leído X → Y"

    pasada(_cliente(), repo)

    assert repo.aplicadas == []
    assert repo.lista_motivos() == [f"proveedor_cif_no_casa:{CIF_LEIDO_19407}"]
    assert _notas_corregido(repo) == []


def test_f062_r16_aplicar_retira_el_no_casa_y_el_aviso_de_una_pasada_anterior():
    repo = _merge_19407()
    pasada(_cliente(), repo, correccion_enabled=False)  # antes de F-062
    assert repo.lista_motivos() == [f"proveedor_cif_no_casa:{CIF_LEIDO_19407}"]

    pasada(_cliente(), repo)  # con F-062

    assert repo.lista_motivos() == [_CORREGIDO_19407]
    assert repo.lineas_notas() == _notas_corregido(repo)


def test_f062_r16_cif_existente_retira_no_casa_de_otro_cif():
    repo = RepoRed(cif=CIF_HORMIGONES_MAT, nombre="x", obra="0720")
    repo.motivos = _json(
        f"proveedor_cif_no_casa:{CIF_LEIDO_19407}", "obra_no_existe:0937",
        f"proveedor_cif_no_casa:{CIF_HORMIGONES_MAT.lower()}",
    )
    repo.review_required = True

    pasada(_cliente(), repo)

    assert repo.retiradas == [CIF_HORMIGONES_MAT]
    assert repo.lista_motivos() == [
        "obra_no_existe:0937", f"proveedor_cif_no_casa:{CIF_HORMIGONES_MAT.lower()}",
    ]
    assert repo.review_required is True


def test_f062_r14_sin_candidato_claro_dos_pasadas_un_motivo_y_una_nota():
    repo = RepoRed(cif=CIF_LEIDO_19407, nombre="TRANSPORTES MACOTRAN", obra="0720")
    pasada(_cliente(), repo)
    pasada(_cliente(), repo)
    assert repo.lista_motivos() == [f"proveedor_cif_no_casa:{CIF_LEIDO_19407}"]
    assert len(repo.lineas_notas()) == 1


def test_f062_r15_si_retirar_falla_la_pasada_sigue():
    class _RepoQueFallaAlRetirar(RepoRed):
        def retirar_motivos_proveedor(self, *, document_id, cif_actual):
            raise RuntimeError("BBDD caida")

    repo = _RepoQueFallaAlRetirar(cif=CIF_HORMIGONES_MAT, nombre="x", obra="0720")
    pasada(_cliente(), repo)
    assert repo.canonizados == [RAZ_HORMIGONES_MAT]
    assert repo.resoluciones == [(None, None, "deterministic")]


# ------------------------------------------------------------------ #
# T11 · supervivientes de la 1.ª campaña de mutación (función pura)
# ------------------------------------------------------------------ #
def test_f062_r16_puro_escribe_el_json_con_el_formato_de_la_columna():
    """Mismo formato que ``anadir_motivo_revision`` (UTF-8 sin escapar y
    sangría 2): el repositorio compara el JSON nuevo con el guardado para
    decidir si escribe, y sv4 lo enseña tal cual en el detalle."""
    nuevos, _ = depurar_motivos_proveedor(
        _json("obra_no_válida:0937", "partida_ausente_familia_destinada", NO_CASA), REAL,
    )
    assert nuevos == (
        '[\n  "obra_no_válida:0937",\n  "partida_ausente_familia_destinada"\n]'
    )


def test_f062_r15_puro_un_leido_con_mayor_que_no_se_toma_por_el_aplicado():
    """Con ``>`` dentro del leído, el aplicado sigue siendo lo que va tras
    el ÚLTIMO ``>``: ni el trozo del medio ni el leído entero."""
    motivo = f"proveedor_cif_corregido:B8>{OTRO}>{REAL}"
    assert depurar_motivos_proveedor(_json(motivo), REAL) == (_json(motivo), False)
    assert depurar_motivos_proveedor(_json(motivo), OTRO) == (None, True)
