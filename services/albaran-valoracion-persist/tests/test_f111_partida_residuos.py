# tests/test_f111_partida_residuos.py
"""F-111 parte B · una línea de residuos sin partida no va a almacén (R20–R29).

Se le busca partida entre las hojas del capítulo de gestión de residuos de su
obra (``ruesma_comun.sigrid.candidatas_residuos``): con una, esa; con dos o
más, la IA elige por significado (sv5, con elector falso aquí); sin capítulo,
sin candidata, con la IA caída o sin lista, a revisión y NUNCA a almacén.
Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest

from application.services.partida_residuos import (
    MOTIVO_IA_FALLO,
    MOTIVO_SIN_CANDIDATA,
    MOTIVO_SIN_CAPITULO,
    MOTIVO_SIN_LISTA,
    PREFIJO_PARTIDA_RESIDUOS,
    AsignacionResiduos,
    AsignadorPartidaResiduos,
)
from ruesma_comun.contratos.clasificacion import ClasificacionAlbaran
from ruesma_comun.sigrid import ListaPartidasObra
from tests.f036_escenarios_residuos import (
    EscenarioResiduos,
    LineaResiduos,
    construir_envelope,
)

_COLUMNAS = ["ide", "padide", "cod", "res"]

#: Obra con UNA candidata (0694) y su hoja de ajuste.
FILAS_UNA = [
    (1, 0, "CD", "COSTES DIRECTOS"),
    (2, 1, "23", "PLAN DE GESTIÓN DE RESIDUOS"),
    (3, 2, "23.01", "Gestión de residuos de construcción"),
    (4, 2, "23.03", "AJUSTE DECIMALES"),
    (5, 1, "05", "ESTRUCTURA"),
    (6, 5, "05.01", "HORMIGÓN"),
]
#: Obra con DOS candidatas (0686).
FILAS_DOS = [
    (1, 0, "CD", "COSTES DIRECTOS"),
    (10, 1, "32", "GESTIÓN RESIDUOS (SEGÚN EGRC)"),
    (11, 10, "32.01", "GRD010 Gestión de residuos"),
    (20, 1, "37", "SEGURIDAD Y SALUD"),
    (21, 20, "37.06", "GESTIÓN DE RESIDUOS"),
    (22, 21, "37.06.01", "OPERARIO EXCLUSIVO PARA CLASIFICACIÓN"),
]
#: Obra SIN capítulo de residuos.
FILAS_NINGUNA = [
    (1, 0, "CD", "COSTES DIRECTOS"),
    (2, 1, "05", "ESTRUCTURA"),
    (3, 2, "05.01", "HORMIGÓN"),
]


def _lista(filas) -> ListaPartidasObra:
    return ListaPartidasObra.desde_filas("0686", _COLUMNAS, filas)


class _Partidas:
    """``PartidasObraPort`` falso que cuenta las consultas."""

    def __init__(self, lista: ListaPartidasObra | None) -> None:
        self._lista = lista
        self.consultas: list[str | None] = []

    def lista(self, obra):
        self.consultas.append(obra)
        return self._lista


class _Elector:
    """``EligePartidaPort`` falso."""

    def __init__(self, respuesta=None, error: Exception | None = None) -> None:
        self.respuesta = respuesta or {}
        self.error = error
        self.llamadas: list[dict] = []

    def elegir(self, *, document_id, lineas, candidatas):
        self.llamadas.append(
            {"document_id": document_id, "lineas": lineas, "candidatas": candidatas}
        )
        if self.error is not None:
            raise self.error
        return self.respuesta


def _envelope(*lineas: LineaResiduos, partidas=None, clasificacion=None):
    """Sobre de residuos; ``partidas`` = lectura por línea (por defecto, vacía)."""
    env = construir_envelope(
        EscenarioResiduos(lineas=tuple(lineas) or (LineaResiduos(),), clasificacion=clasificacion)
    )
    for i, ctx in enumerate(env.context.lineas_albaran):
        ctx.codigo_partida_albaran = (partidas or {}).get(i)
    return env


def _asignador(lista=None, *, elector=None, activo=True, partidas="defecto"):
    puerto = _Partidas(lista) if partidas == "defecto" else partidas
    return AsignadorPartidaResiduos(
        partidas=puerto, elector=elector, alm_codigo_partida="ALM", activo=activo,
    ), puerto


# ------------------------------------------------------------------ #
# R20 · qué líneas se buscan
# ------------------------------------------------------------------ #
def test_f111_r20_necesita_obra_solo_con_residuos_sin_lectura():
    asignador, _ = _asignador(_lista(FILAS_UNA))
    assert asignador.necesita_obra(_envelope()) is True
    assert asignador.necesita_obra(_envelope(partidas={0: "32.01"})) is False
    assert asignador.necesita_obra(_envelope(partidas={0: "ALM"})) is False
    assert asignador.necesita_obra(_envelope(partidas={0: " alm "})) is False
    assert asignador.necesita_obra(_envelope(partidas={0: "   "})) is True
    otra = LineaResiduos(tipo_familia="hormigon")
    assert asignador.necesita_obra(_envelope(otra)) is False


def test_f111_r20_la_familia_puede_venir_del_documento():
    asignador, _ = _asignador(_lista(FILAS_UNA))
    sin_familia = LineaResiduos(tipo_familia=None)
    doc_residuos = ClasificacionAlbaran(familia="residuos", confianza_pct=90, motivo="LER")
    assert asignador.necesita_obra(_envelope(sin_familia)) is False
    assert asignador.necesita_obra(_envelope(sin_familia, clasificacion=doc_residuos)) is True
    sin_ctx = LineaResiduos(sin_contexto=True)
    assert asignador.necesita_obra(_envelope(sin_ctx, clasificacion=doc_residuos)) is True


# ------------------------------------------------------------------ #
# R21 · una candidata: esa, sin IA
# ------------------------------------------------------------------ #
def test_f111_r21_una_candidata_se_usa_sin_llamar_a_la_ia():
    elector = _Elector()
    asignador, puerto = _asignador(_lista(FILAS_UNA), elector=elector)
    env = _envelope()
    asignacion = asignador.asignar(envelope=env, obra="0694")

    assert asignacion.envelope.context.lineas_albaran[0].codigo_partida_albaran == "23.01"
    assert env.context.lineas_albaran[0].codigo_partida_albaran is None  # el de sv5 no se muta
    assert asignacion.por_linea[700].codigo == "23.01"
    assert asignacion.por_linea[700].revision is False
    assert asignacion.sin_almacen == frozenset()
    assert elector.llamadas == []
    assert puerto.consultas == ["0694"]


# ------------------------------------------------------------------ #
# R22, R34 · dos o más: la IA elige, en UNA llamada por documento
# ------------------------------------------------------------------ #
def test_f111_r22_con_dos_candidatas_elige_la_ia_en_una_llamada():
    elector = _Elector({700: "32.01", 701: "37.06.01"})
    asignador, _ = _asignador(_lista(FILAS_DOS), elector=elector)
    env = _envelope(
        LineaResiduos(merge_line_id=700, descripcion="CONTENEDOR MADERA", codigo_ler="170201"),
        LineaResiduos(merge_line_id=701, descripcion="CLASIFICACION", codigo_ler=None),
        LineaResiduos(merge_line_id=702, descripcion="CON PARTIDA"),
        partidas={2: "32.01"},
    )
    asignacion = asignador.asignar(envelope=env, obra="0686")

    assert len(elector.llamadas) == 1
    llamada = elector.llamadas[0]
    assert llamada["document_id"] == "doc-SS-0000589"
    assert llamada["lineas"] == [
        {"line_ref": 700, "descripcion": "CONTENEDOR MADERA", "codigo_ler": "170201"},
        {"line_ref": 701, "descripcion": "CLASIFICACION", "codigo_ler": None},
    ]
    assert [c["codigo"] for c in llamada["candidatas"]] == ["32.01", "37.06.01"]
    assert llamada["candidatas"][0]["descripcion"] == "GRD010 Gestión de residuos"
    assert "GESTIÓN RESIDUOS" in llamada["candidatas"][0]["descripcion_agregada"]
    lineas = asignacion.envelope.context.lineas_albaran
    assert [l.codigo_partida_albaran for l in lineas] == ["32.01", "37.06.01", "32.01"]
    assert set(asignacion.por_linea) == {700, 701}


def test_f111_r26_la_ia_no_elige_va_a_revision_con_las_candidatas():
    elector = _Elector({700: None})
    asignador, _ = _asignador(_lista(FILAS_DOS), elector=elector)
    asignacion = asignador.asignar(envelope=_envelope(), obra="0686")
    r = asignacion.por_linea[700]
    assert r.codigo is None and r.revision is True
    assert r.motivo == f"{MOTIVO_SIN_CANDIDATA}:32.01,37.06.01"
    assert asignacion.sin_almacen == frozenset({700})
    assert asignacion.envelope.context.lineas_albaran[0].codigo_partida_albaran is None


def test_f111_r26_codigo_que_no_es_candidata_va_a_revision():
    elector = _Elector({700: "05.01"})
    asignador, _ = _asignador(_lista(FILAS_DOS), elector=elector)
    r = asignador.asignar(envelope=_envelope(), obra="0686").por_linea[700]
    assert r.codigo is None
    assert r.motivo.startswith(MOTIVO_SIN_CANDIDATA)


def test_f111_r26_linea_sin_respuesta_de_la_ia_va_a_revision():
    elector = _Elector({999: "32.01"})
    asignador, _ = _asignador(_lista(FILAS_DOS), elector=elector)
    assert asignador.asignar(envelope=_envelope(), obra="0686").por_linea[700].revision


def test_f111_r26_la_ia_falla_va_a_revision():
    elector = _Elector(error=RuntimeError("404"))
    asignador, _ = _asignador(_lista(FILAS_DOS), elector=elector)
    asignacion = asignador.asignar(envelope=_envelope(), obra="0686")
    assert asignacion.por_linea[700].motivo == f"{MOTIVO_IA_FALLO}:32.01,37.06.01"
    assert asignacion.sin_almacen == frozenset({700})


def test_f111_r26_sin_elector_con_dos_candidatas_es_fallo_de_ia():
    asignador, _ = _asignador(_lista(FILAS_DOS), elector=None)
    r = asignador.asignar(envelope=_envelope(), obra="0686").por_linea[700]
    assert r.motivo.startswith(MOTIVO_IA_FALLO)


def test_f111_r26_el_motivo_lleva_hasta_5_candidatas():
    filas = [(1, 0, "CD", "COSTES"), (2, 1, "32", "GESTION DE RESIDUOS")]
    filas += [(10 + i, 2, f"32.0{i}", f"Hoja {i}") for i in range(1, 8)]
    asignador, _ = _asignador(_lista(filas), elector=_Elector({}))
    r = asignador.asignar(envelope=_envelope(), obra="0459").por_linea[700]
    assert r.motivo == f"{MOTIVO_SIN_CANDIDATA}:32.01,32.02,32.03,32.04,32.05(+2)"


# ------------------------------------------------------------------ #
# R25, R27 · sin capítulo o sin lista: revisión, nunca almacén
# ------------------------------------------------------------------ #
def test_f111_r25_sin_capitulo_de_residuos_a_revision():
    elector = _Elector()
    asignador, _ = _asignador(_lista(FILAS_NINGUNA), elector=elector)
    asignacion = asignador.asignar(envelope=_envelope(), obra="0700")
    assert asignacion.por_linea[700].motivo == MOTIVO_SIN_CAPITULO
    assert asignacion.por_linea[700].revision is True
    assert asignacion.sin_almacen == frozenset({700})
    assert elector.llamadas == []


@pytest.mark.parametrize("obra", [None, "", "   "])
def test_f111_r27_sin_obra_a_revision_sin_consultar(obra):
    asignador, puerto = _asignador(_lista(FILAS_UNA))
    asignacion = asignador.asignar(envelope=_envelope(), obra=obra)
    assert asignacion.por_linea[700].motivo == MOTIVO_SIN_LISTA
    assert asignacion.sin_almacen == frozenset({700})
    assert puerto.consultas == []


def test_f111_r27_lista_none_o_sin_puerto_a_revision():
    asignador, _ = _asignador(None)
    assert asignador.asignar(envelope=_envelope(), obra="0686").por_linea[700].motivo == MOTIVO_SIN_LISTA
    asignador, _ = _asignador(partidas=None)
    assert asignador.asignar(envelope=_envelope(), obra="0686").por_linea[700].motivo == MOTIVO_SIN_LISTA


def test_f111_r27_degradada_marca_todas_las_lineas_sin_lista():
    asignador, _ = _asignador(_lista(FILAS_UNA))
    env = _envelope(LineaResiduos(merge_line_id=1), LineaResiduos(merge_line_id=2))
    asignacion = asignador.degradada(env)
    assert asignacion.envelope is env
    assert {k: v.motivo for k, v in asignacion.por_linea.items()} == {
        1: MOTIVO_SIN_LISTA, 2: MOTIVO_SIN_LISTA,
    }
    assert asignacion.sin_almacen == frozenset({1, 2})


# ------------------------------------------------------------------ #
# R28, R29 · lo que no cambia
# ------------------------------------------------------------------ #
def test_f111_r28_con_lectura_alm_u_otra_familia_no_se_toca():
    asignador, puerto = _asignador(_lista(FILAS_UNA))
    env = _envelope(
        LineaResiduos(merge_line_id=1),
        LineaResiduos(merge_line_id=2),
        LineaResiduos(merge_line_id=3, tipo_familia="hormigon"),
        partidas={0: "05.01", 1: "ALM"},
    )
    asignacion = asignador.asignar(envelope=env, obra="0694")
    assert asignacion.envelope is env
    assert asignacion.por_linea == {}
    assert asignacion.sin_almacen == frozenset()
    assert puerto.consultas == []


def test_f111_r29_apagado_no_hace_nada():
    asignador, puerto = _asignador(_lista(FILAS_UNA), activo=False)
    env = _envelope()
    assert asignador.necesita_obra(env) is False
    asignacion = asignador.asignar(envelope=env, obra="0694")
    assert asignacion.envelope is env and asignacion.por_linea == {}
    assert puerto.consultas == []


def test_f111_asignacion_vacia_por_defecto():
    env = _envelope()
    vacia = AsignacionResiduos(envelope=env)
    assert vacia.por_linea == {} and vacia.sin_almacen == frozenset()


# ------------------------------------------------------------------ #
# R23, R25–R27 · el rastro en los registros (anotar)
# ------------------------------------------------------------------ #
def _registros(envelope):
    from tests.f027_escenarios import construir_builder

    return construir_builder().build(envelope=envelope, existing_document_already_valued=False)


def test_f111_r23_anotar_asignada_motivo_y_lectura_de_vuelta():
    asignador, _ = _asignador(_lista(FILAS_UNA))
    asignacion = asignador.asignar(envelope=_envelope(), obra="0694")
    cab, regs = _registros(asignacion.envelope)
    base = next(r for r in regs if r.line_kind == "from_albaran")
    assert base.codigo_partida_albaran == "23.01"  # antes de anotar
    revision_antes = base.review_required
    AsignadorPartidaResiduos.anotar(cab, regs, asignacion)
    assert base.codigo_partida_albaran is None  # leída ≠ decisión
    assert f"{PREFIJO_PARTIDA_RESIDUOS}23.01" in base.review_reasons
    assert base.review_required is revision_antes
    assert f"{PREFIJO_PARTIDA_RESIDUOS}23.01" not in cab.review_reasons
    # Dos veces no duplica.
    AsignadorPartidaResiduos.anotar(cab, regs, asignacion)
    assert base.review_reasons.count(f"{PREFIJO_PARTIDA_RESIDUOS}23.01") == 1


def test_f111_r25_anotar_no_asignada_revision_en_linea_y_cabecera():
    asignador, _ = _asignador(_lista(FILAS_NINGUNA))
    asignacion = asignador.asignar(envelope=_envelope(), obra="0700")
    cab, regs = _registros(asignacion.envelope)
    cab.review_required = False
    cab.review_reasons = []
    base = next(r for r in regs if r.line_kind == "from_albaran")
    base.review_required = False
    AsignadorPartidaResiduos.anotar(cab, regs, asignacion)
    assert MOTIVO_SIN_CAPITULO in base.review_reasons
    assert base.review_required is True
    assert cab.review_required is True
    assert MOTIVO_SIN_CAPITULO in cab.review_reasons
    assert "at_least_one_line_requires_review" in cab.review_reasons
    AsignadorPartidaResiduos.anotar(cab, regs, asignacion)
    assert cab.review_reasons.count(MOTIVO_SIN_CAPITULO) == 1


def test_f111_r23_anotar_solo_toca_las_lineas_de_la_asignacion():
    asignador, _ = _asignador(_lista(FILAS_UNA))
    env = _envelope(LineaResiduos(merge_line_id=1), LineaResiduos(merge_line_id=2), partidas={1: "05.01"})
    asignacion = asignador.asignar(envelope=env, obra="0694")
    cab, regs = _registros(asignacion.envelope)
    otra = next(r for r in regs if r.merge_line_id == 2)
    motivos = list(otra.review_reasons)
    AsignadorPartidaResiduos.anotar(cab, regs, asignacion)
    assert otra.review_reasons == motivos
    assert otra.codigo_partida_albaran == "05.01"
    for r in regs:
        if r.line_kind != "from_albaran":
            assert not any(m.startswith(PREFIJO_PARTIDA_RESIDUOS) for m in r.review_reasons)


def test_f111_r35_motivos_congelados():
    assert PREFIJO_PARTIDA_RESIDUOS == "partida_residuos:"
    assert MOTIVO_SIN_CAPITULO == "partida_residuos_sin_capitulo"
    assert MOTIVO_SIN_CANDIDATA == "partida_residuos_sin_candidata"
    assert MOTIVO_IA_FALLO == "partida_residuos_ia_fallo"
    assert MOTIVO_SIN_LISTA == "partida_residuos_sin_lista"


# ------------------------------------------------------------------ #
# T9 · R25 el matcher no manda a almacén lo que F-111 no pudo asignar
# ------------------------------------------------------------------ #
def _linea_ia(matched_id):
    from domain.models.valuation_envelope import LineValuationDto

    return LineValuationDto(
        merge_line_id=700, line_kind="from_albaran", match_method="semantic",
        matched_contrato_line_id=matched_id, match_confidence_pct=90.0,
        unidad_categoria_albaran="count", unidad_category_match=True,
        precio_unitario_contrato_db=120.0,
    )


def _match(matched_id, partida, *, sin_almacen, almacen=True):
    from application.services.partida_matcher import PartidaMatcher
    from tests.f036_escenarios_residuos import CONTRATO_SALMEDINA

    return PartidaMatcher(alm_codigo_partida="ALM", almacen_sin_partida=almacen).match(
        line=_linea_ia(matched_id), codigo_partida_albaran=partida,
        precio_unitario_final=120.0, unidad_albaran="UD",
        contrato_lines=list(CONTRATO_SALMEDINA), albaran_descripcion="x",
        albaran_codigo_producto=None, sin_almacen=sin_almacen,
    )


def test_f111_r25_matcher_sin_almacen_conserva_la_casada_sin_partida():
    r = _match(9001, None, sin_almacen=True)
    assert r.partida_action == "existing_matched"
    assert r.matched_contrato_line_id == 9001
    assert r.codigo_partida_final is None  # nunca la del contrato (F-051)
    assert r.derived_line is None
    assert r.reasons == ["ia_match_trusted_sin_partida"]


def test_f111_r25_matcher_sin_almacen_y_sin_casada_no_action():
    r = _match(None, None, sin_almacen=True)
    assert r.partida_action == "no_action"
    assert r.codigo_partida_final is None
    assert r.matched_contrato_line_id is None


def test_f111_r25_matcher_sin_almacen_con_casada_inexistente_no_action():
    r = _match(123456, None, sin_almacen=True)
    assert r.partida_action == "no_action"


def test_f111_r28_matcher_sin_marca_sigue_mandando_a_almacen():
    assert _match(9001, None, sin_almacen=False).partida_action == "almacen_sin_partida"
    # Con F-051 apagado, lo de antes de F-051 (sin cambios).
    assert _match(9001, None, sin_almacen=False, almacen=False).codigo_partida_final == "32.01"


def test_f111_r28_matcher_sin_almacen_no_toca_las_lecturas():
    assert _match(9001, "32.01", sin_almacen=True).codigo_partida_final == "32.01"
    assert _match(9001, "ALM", sin_almacen=True).partida_action == "alm_new_line_created"


def _builder_almacen():
    """El builder del escenario con F-051 encendido (como en producción)."""
    from application.services.partida_matcher import PartidaMatcher
    from tests.f027_escenarios import construir_builder

    builder = construir_builder()
    builder._partida_matcher = PartidaMatcher(alm_codigo_partida="ALM", almacen_sin_partida=True)
    return builder


def test_f111_r25_matcher_el_builder_pasa_sin_almacen():
    builder = _builder_almacen()
    env = _envelope()
    _cab, regs = builder.build(envelope=env, existing_document_already_valued=False)
    base = next(r for r in regs if r.line_kind == "from_albaran")
    assert base.partida_action == "almacen_sin_partida"

    _cab, regs = builder.build(
        envelope=env, existing_document_already_valued=False, sin_almacen=frozenset({700}),
    )
    base = next(r for r in regs if r.line_kind == "from_albaran")
    assert base.partida_action != "almacen_sin_partida"
    assert base.codigo_partida_final is None
    # La marca es de UNA valoración: la siguiente sin ella vuelve a almacén.
    _cab, regs = builder.build(envelope=env, existing_document_already_valued=False)
    assert next(r for r in regs if r.line_kind == "from_albaran").partida_action == "almacen_sin_partida"


#: Obra con una candidata, la del contrato del escenario (32.01).
FILAS_32 = [
    (1, 0, "CD", "COSTES DIRECTOS"),
    (10, 1, "32", "GESTIÓN RESIDUOS (SEGÚN EGRC)"),
    (11, 10, "32.01", "GRD010 Gestión de residuos"),
]


def test_f111_r24_sintetica_ler_hereda_la_partida_asignada():
    builder = _builder_almacen()
    asignador, _ = _asignador(_lista(FILAS_32))
    asignacion = asignador.asignar(envelope=_envelope(), obra="0686")
    cab, regs = builder.build(
        envelope=asignacion.envelope, existing_document_already_valued=False,
        sin_almacen=asignacion.sin_almacen,
    )
    AsignadorPartidaResiduos.anotar(cab, regs, asignacion)
    base = next(r for r in regs if r.line_kind == "from_albaran")
    sinteticas = [r for r in regs if r.line_kind == "synthetic_modifier"]
    assert base.codigo_partida_final == "32.01"
    assert base.codigo_partida_albaran is None
    assert sinteticas, "el escenario debe inyectar el incremento LER 170802"
    assert all(s.codigo_partida_final == "32.01" for s in sinteticas)


def test_f111_r24_sintetica_sin_asignacion_va_con_la_base_a_almacen():
    """Contraste: sin F-111, base y sintética van a almacén (partida vacía)."""
    builder = _builder_almacen()
    _cab, regs = builder.build(envelope=_envelope(), existing_document_already_valued=False)
    sinteticas = [r for r in regs if r.line_kind == "synthetic_modifier"]
    assert sinteticas and all(s.codigo_partida_final is None for s in sinteticas)


# ------------------------------------------------------------------ #
# T12 · supervivientes de la campaña de mutación
# ------------------------------------------------------------------ #
def _capitulo_con(n):
    filas = [(1, 0, "CD", "COSTES"), (2, 1, "32", "GESTION DE RESIDUOS")]
    return _lista(filas + [(10 + i, 2, f"32.0{i}", f"Hoja {i}") for i in range(1, n + 1)])


def test_f111_t12_con_5_candidatas_no_hay_resto_y_con_6_uno():
    asignador, _ = _asignador(_capitulo_con(5), elector=_Elector({}))
    assert asignador.asignar(envelope=_envelope(), obra="x").por_linea[700].motivo == (
        f"{MOTIVO_SIN_CANDIDATA}:32.01,32.02,32.03,32.04,32.05"
    )
    asignador, _ = _asignador(_capitulo_con(6), elector=_Elector({}))
    assert asignador.asignar(envelope=_envelope(), obra="x").por_linea[700].motivo.endswith("(+1)")


def test_f111_t12_los_resultados_son_inmutables():
    import dataclasses

    asignador, _ = _asignador(_lista(FILAS_UNA))
    asignacion = asignador.asignar(envelope=_envelope(), obra="0694")
    with pytest.raises(dataclasses.FrozenInstanceError):
        asignacion.sin_almacen = frozenset({1})
    with pytest.raises(dataclasses.FrozenInstanceError):
        asignacion.por_linea[700].codigo = "x"


def test_f111_t12_el_log_cuenta_asignadas_y_a_revision(caplog):
    import logging

    elector = _Elector({700: "32.01", 701: None})
    asignador, _ = _asignador(_lista(FILAS_DOS), elector=elector)
    env = _envelope(LineaResiduos(merge_line_id=700), LineaResiduos(merge_line_id=701))
    with caplog.at_level(logging.INFO, logger="application.services.partida_residuos"):
        asignador.asignar(envelope=env, obra="0686")
    assert any("asignadas=1 a_revision=1" in r.getMessage() for r in caplog.records)
