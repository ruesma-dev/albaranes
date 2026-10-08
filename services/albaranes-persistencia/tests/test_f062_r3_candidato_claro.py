# tests/test_f062_r3_candidato_claro.py
"""F-062 · R3, R4, R5 — qué es un «candidato claro» de la obra.

Elegibles: candidatos con contrato en la obra, identificador fiscal válido
y nombre completo (``score >= 1,0`` por defecto), agrupados por CIF
normalizado. Uno solo ⇒ claro. Varios ⇒ gana el de CIF más cercano al
leído si saca al siguiente un margen de distancia (2 por defecto). La
distancia solo desempata; el control del CIF leído no cambia la regla.

T4 al principio: la consulta de candidatos de la obra se hace UNA vez por
pasada (``_candidatos_puntuados``) y la propuesta de F-052 sale de ahí.
"""
from __future__ import annotations

import pytest
from doble_sigrid_api import (
    CIF_ARIDOS_ANFERSA,
    CIF_HORMIGONERA_EMPATE,
    CIF_HORMIGONES_MAT,
    CIF_LEIDO_19394,
    CIF_LEIDO_19407,
    CIF_LEIDO_1790636816,
    DobleSigridApi,
    fixture_f062,
)

from application.services.header_resolver_service import (
    HeaderResolverService,
    _distancia_edicion,
)
from domain.models.header_resolution_models import ProveedorObraResumen


class _Obras:
    def search_obras(self):
        return []


class _Cliente:
    def __init__(self, resumenes=None, *, error: Exception | None = None) -> None:
        self._resumenes = list(resumenes or [])
        self._error = error
        self.consultas: list[str] = []

    def fetch_contratos_resumen_por_obra(self, *, codigo_obra: str):
        self.consultas.append(codigo_obra)
        if self._error is not None:
            raise self._error
        return list(self._resumenes)


def _r(cif: str, nombre: str | None) -> ProveedorObraResumen:
    return ProveedorObraResumen(cif=cif, nombre=nombre, codigos_contratos=("C1",), texto="")


def _resolver(cliente, **kwargs) -> HeaderResolverService:
    return HeaderResolverService(
        obra_client=_Obras(), proveedor_client=cliente, repository=None, **kwargs,
    )


# ------------------------------------------------------------------ #
# T4 · una sola consulta de candidatos por pasada
# ------------------------------------------------------------------ #
def test_f062_t4_candidatos_puntuados_una_consulta_y_todos_con_score():
    cliente = _Cliente([_r(CIF_HORMIGONES_MAT, "HORMIGONES MAT, S.L.U."), _r("B1", "GRUAS, S.L.")])
    puntuados, motivo = _resolver(cliente)._candidatos_puntuados(
        proveedor_nombre="Hormigones Mat SL", obra="0720",
    )
    assert cliente.consultas == ["0720"]
    assert motivo == "propuesta"
    assert [(r.cif, s) for r, s in puntuados] == [(CIF_HORMIGONES_MAT, 1.0), ("B1", 0.0)]


@pytest.mark.parametrize(
    ("nombre", "obra", "cliente", "motivo"),
    [
        ("X", None, _Cliente(), "sin_obra"),
        (None, None, _Cliente(), "sin_obra"),
        ("  ", "0720", _Cliente(), "sin_nombre"),
        ("X", "0720", _Cliente(error=RuntimeError("500")), "consulta_fallida"),
        ("TRANSPORTES MACOTRAN", "0720", _Cliente([_r("B1", "GRUAS, S.L.")]), "nadie_casa"),
    ],
)
def test_f062_t4_candidatos_puntuados_motivos_de_f052(nombre, obra, cliente, motivo):
    puntuados, obtenido = _resolver(cliente)._candidatos_puntuados(
        proveedor_nombre=nombre, obra=obra,
    )
    assert obtenido == motivo
    if motivo != "nadie_casa":
        assert puntuados == []


def test_f062_t4_el_umbral_de_la_propuesta_es_inclusivo():
    cliente = _Cliente([_r("B66000666", "EBRO CANTERAS")])
    _, motivo = _resolver(cliente)._candidatos_puntuados(
        proveedor_nombre="HORMIGONES DEL EBRO", obra="0720",
    )
    assert motivo == "propuesta"  # 0,5 >= 0,5


# ------------------------------------------------------------------ #
# T5 · distancia de edición (Levenshtein)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("a", "b", "distancia"),
    [
        ("", "", 0),
        ("", "B66056201", 9),
        ("B66056201", "B66056201", 0),
        ("kitten", "sitting", 3),
        ("B6605620", "B66056201", 1),  # inserción
        ("B660562011", "B66056201", 1),  # borrado
        ("AB", "BA", 2),
        (CIF_LEIDO_19407, CIF_HORMIGONES_MAT, 1),
        (CIF_LEIDO_19394, CIF_HORMIGONES_MAT, 4),
        (CIF_LEIDO_1790636816, CIF_ARIDOS_ANFERSA, 1),
        (CIF_LEIDO_19407, CIF_HORMIGONERA_EMPATE, 9),
        (CIF_LEIDO_19394, CIF_HORMIGONERA_EMPATE, 9),
    ],
)
def test_f062_r4_distancia_edicion(a, b, distancia):
    assert _distancia_edicion(a, b) == distancia
    assert _distancia_edicion(b, a) == distancia


# ------------------------------------------------------------------ #
# R3–R5 · candidato claro
# ------------------------------------------------------------------ #
#: CIF con control VÁLIDO (comprobado en T1).
V1 = "B66056201"
V2 = "B18487421"
V3 = "A28123453"
#: Válido y a distancia 2 de V1.
V1_A_2 = "B66056219"
#: Control INVÁLIDO y a distancia 1 de V1.
V1_INVALIDO = "B66056291"


def _claro(cif_leido, puntuados, **kwargs):
    return _resolver(_Cliente(), **kwargs)._candidato_claro(
        cif_leido=cif_leido, puntuados=puntuados,
    )


def test_f062_r4_un_solo_elegible_es_claro_por_unico():
    cand = _r(V1, "HORMIGONES MAT, S.L.U.")
    assert _claro("B86056201", [(cand, 1.0), (_r(V2, "OTRO"), 0.5)]) == (cand, "unico")


def test_f062_r4_unico_aunque_su_cif_quede_lejos_del_leido():
    """La distancia solo desempata: con un elegible, no se mira."""
    cand = _r(V3, "HORMIGONES Y MATERIALES DEL NORTE, S.A.")
    assert _claro("B86056201", [(cand, 1.0)]) == (cand, "unico")


def test_f062_r3_sin_elegibles_no_hay_claro():
    assert _claro("B86056201", []) == (None, None)
    assert _claro("B86056201", [(_r(V1, "HORMIGONES MAT"), 0.99)]) == (None, None)


def test_f062_r3_el_umbral_de_nombre_es_inclusivo_y_configurable():
    cand = _r(V1, "HORMIGONES MAT")
    assert _claro("B86056201", [(cand, 0.5)]) == (None, None)
    assert _claro("B86056201", [(cand, 0.5)], correccion_score_min=0.5) == (cand, "unico")
    assert _claro("B86056201", [(cand, 0.49)], correccion_score_min=0.5) == (None, None)


def test_f062_r3_un_candidato_con_el_control_invalido_no_es_elegible():
    """Ficha de Sigrid mal tecleada: se propone, no se aplica (D2), por
    cerca que quede del leído."""
    assert _claro(V1, [(_r(V1_INVALIDO, "HORMIGONES MAT"), 1.0)]) == (None, None)


def test_f062_r3_extranjero_no_es_elegible():
    assert _claro("B86056201", [(_r("PT123456789", "HORMIGONES MAT"), 1.0)]) == (None, None)


def test_f062_r3_dos_filas_del_mismo_cif_normalizado_son_un_candidato():
    a = _r(V1, "HORMIGONES MAT, S.L.U.")
    b = _r(" b-66056201", "HORMIGONES MAT SLU")
    assert _claro("B86056201", [(a, 1.0), (b, 1.0)]) == (a, "unico")


def test_f062_r4_empate_desempatado_por_el_cif_mas_cercano():
    bueno = _r(V1, "HORMIGONES MAT, S.L.U.")
    otro = _r(V3, "HORMIGONES Y MATERIALES DEL NORTE, S.A.")
    # 19407: distancias 1 y 9; 19394: 4 y 9. El orden de llegada no cuenta.
    assert _claro(CIF_LEIDO_19407, [(otro, 1.0), (bueno, 1.0)]) == (bueno, "cif_cercano")
    assert _claro(CIF_LEIDO_19394, [(bueno, 1.0), (otro, 1.0)]) == (bueno, "cif_cercano")


def test_f062_r4_margen_exacto_es_claro():
    a = _r(V1, "HORMIGONES MAT")
    b = _r(V1_A_2, "HORMIGONES MAT")
    # leído = V1: 0 frente a 2 ⇒ margen 2 (inclusivo) ⇒ claro.
    assert _claro(V1, [(b, 1.0), (a, 1.0)]) == (a, "cif_cercano")


def test_f062_r4_sin_margen_suficiente_no_hay_claro():
    a = _r(V1, "HORMIGONES MAT")
    b = _r(V1_A_2, "HORMIGONES MAT")
    # leído = V1_INVALIDO: 1 frente a 2 ⇒ margen 1 < 2 ⇒ nadie.
    assert _claro(V1_INVALIDO, [(a, 1.0), (b, 1.0)]) == (None, None)
    # Empate exacto de distancia (9 y 9).
    c = _r(V3, "X")
    d = _r("A28123461", "X")
    assert _distancia_edicion("ZZZZZZZZZ", V3) == _distancia_edicion("ZZZZZZZZZ", "A28123461")
    assert _claro("ZZZZZZZZZ", [(c, 1.0), (d, 1.0)]) == (None, None)


def test_f062_r4_el_margen_es_configurable():
    a = _r(V1, "HORMIGONES MAT")
    b = _r(V1_A_2, "HORMIGONES MAT")
    puntuados = [(a, 1.0), (b, 1.0)]
    assert _claro(V1_INVALIDO, puntuados, correccion_margen_distancia=1) == (a, "cif_cercano")
    assert _claro(V1, puntuados, correccion_margen_distancia=3) == (None, None)


def test_f062_r4_con_tres_elegibles_compara_el_primero_con_el_segundo():
    a = _r(V1, "X")
    b = _r(V1_A_2, "X")
    c = _r(V3, "X")
    # leído = V1: 0, 2 y 9 ⇒ margen 2 con el segundo ⇒ claro.
    assert _claro(V1, [(c, 1.0), (b, 1.0), (a, 1.0)]) == (a, "cif_cercano")
    # leído a 1 de V1 y a 2 de V1_A_2: margen 1 con el segundo ⇒ nadie,
    # aunque el tercero quede lejísimos.
    assert _claro(V1_INVALIDO, [(c, 1.0), (b, 1.0), (a, 1.0)]) == (None, None)


def test_f062_r4_la_distancia_no_hace_elegible_a_quien_no_lo_es():
    lejano = _r(V3, "HORMIGONES Y MATERIALES DEL NORTE, S.A.")
    cercano_debil = _r(V1, "HORMIGONES MAT")
    assert _claro(CIF_LEIDO_19407, [(lejano, 1.0), (cercano_debil, 0.5)]) == (lejano, "unico")


@pytest.mark.parametrize("leido", [CIF_LEIDO_19407, V1_A_2], ids=["control-invalido", "control-valido"])
def test_f062_r5_el_control_del_leido_no_cambia_la_regla(leido):
    """Q4: con el control del leído válido o inválido, el claro es el mismo."""
    cand = _r(V1, "HORMIGONES MAT, S.L.U.")
    otro = _r(V3, "HORMIGONES Y MATERIALES DEL NORTE, S.A.")
    assert _claro(leido, [(cand, 1.0)]) == (cand, "unico")
    assert _claro(leido, [(otro, 1.0), (cand, 1.0)]) == (cand, "cif_cercano")


def test_f062_r4_leido_sin_caracteres_utiles_no_rompe():
    cand = _r(V1, "X")
    assert _claro("---", [(cand, 1.0)]) == (cand, "unico")
    assert _claro("---", [(cand, 1.0), (_r(V3, "X"), 1.0)]) == (None, None)


# ------------------------------------------------------------------ #
# Los tres casos medidos, con el cliente real sobre el doble
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("leido", "nombre", "obra", "esperado", "via"),
    [
        (CIF_LEIDO_19407, "Hormigones Mat SL", "0720", CIF_HORMIGONES_MAT, "cif_cercano"),
        (CIF_LEIDO_19394, "Hormigones Mat SL", "0720", CIF_HORMIGONES_MAT, "cif_cercano"),
        (CIF_LEIDO_1790636816, "ARIDOS ANFERSA SL", "0678", CIF_ARIDOS_ANFERSA, "unico"),
    ],
    ids=["19407", "19394", "1790636816"],
)
def test_f062_r4_los_tres_casos_medidos_tienen_candidato_claro(leido, nombre, obra, esperado, via):
    resolver = _resolver(DobleSigridApi(fixture_f062()).cliente())
    puntuados, motivo = resolver._candidatos_puntuados(proveedor_nombre=nombre, obra=obra)
    candidato, obtenida = resolver._candidato_claro(cif_leido=leido, puntuados=puntuados)
    assert (candidato.cif, obtenida) == (esperado, via)
    assert motivo == "propuesta"


# ------------------------------------------------------------------ #
# T11 · supervivientes de la 1.ª campaña de mutación
# ------------------------------------------------------------------ #
def test_f062_t4_con_umbral_cero_un_score_cero_no_es_propuesta():
    """Equivalencia con F-052: «propuesta» exige que alguien case algo
    (score > 0), aunque ``HEADER_RESOLVER_MIN_SCORE`` sea 0. Sin esa
    condición, ``_mejor_de`` no tendría a quién proponer."""
    cliente = _Cliente([_r("B1", "GRUAS, S.L.")])
    resolver = _resolver(cliente, min_score=0.0)
    puntuados, motivo = resolver._candidatos_puntuados(
        proveedor_nombre="TRANSPORTES MACOTRAN", obra="0720",
    )
    assert [s for _, s in puntuados] == [0.0]
    assert motivo == "nadie_casa"
    assert resolver._mejor_candidato_por_nombre(
        proveedor_nombre="TRANSPORTES MACOTRAN", obra_codigo_efectiva="0720",
    ) == (None, "nadie_casa", 1)


def test_f062_t4_el_log_de_nadie_casa_solo_sale_cuando_nadie_casa(caplog):
    """El INFO «ningun candidato de la obra … casa» es el rastro de F-052
    para «nadie casa»; con una consulta fallida o sin obra no se emite
    (eso lo cuentan sus propios logs)."""
    import logging

    from application.services import header_resolver_service as modulo

    def _logs(cliente, **kwargs) -> list[str]:
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=modulo.logger.name):
            _resolver(cliente)._mejor_candidato_por_nombre(**kwargs)
        return [r.getMessage() for r in caplog.records if "casa con el nombre leido" in r.getMessage()]

    nadie = _logs(_Cliente([_r("B1", "GRUAS, S.L.")]),
                  proveedor_nombre="TRANSPORTES MACOTRAN", obra_codigo_efectiva="0720")
    assert nadie == [(
        "[header-resolver] ningun candidato de la obra 0720 casa con el nombre leido "
        "(mejor score=0.00 < 0.50, 1 candidatos)."
    )]
    assert _logs(_Cliente(error=RuntimeError("500")),
                 proveedor_nombre="X", obra_codigo_efectiva="0720") == []
    assert _logs(_Cliente(), proveedor_nombre="X", obra_codigo_efectiva=None) == []
