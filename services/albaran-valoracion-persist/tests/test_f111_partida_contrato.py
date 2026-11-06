# tests/test_f111_partida_contrato.py
"""F-111 parte C · la partida de residuos se toma primero del contrato (R37–R46).

Regla del humano (2026-11-05): «que mire primero en las líneas del contrato si
tiene partida; si es de gestión de residuos que coja esa, y si no que busque».

- Paso 1: partidas del contrato que son del capítulo de residuos.
- Paso 2: si ninguna lo es, todas las del contrato (D1=b).
- Paso 3: si el contrato no aporta ninguna, la parte B tal cual.
- (R43, humano 2026-11-06) Si en el paso 1 o 2 la IA no elige, la línea cae al
  capítulo con el rastro ``partida_residuos_contrato_sin_eleccion``.

Las listas son sintéticas, con las rutas medidas en producción (design §13).
Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import logging

import pytest
from ruesma_comun.sigrid import ListaPartidasObra

from application.services.partida_residuos import (
    MOTIVO_CONTRATO_SIN_ELECCION,
    MOTIVO_IA_FALLO,
    MOTIVO_SIN_CANDIDATA,
    MOTIVO_SIN_CAPITULO,
    MOTIVO_SIN_LISTA,
    PREFIJO_PARTIDA_RESIDUOS,
    PREFIJO_PARTIDA_RESIDUOS_CONTRATO,
    PREFIJO_PARTIDA_RESIDUOS_CONTRATO_HOJA,
    AsignadorPartidaResiduos,
    ResultadoPartidaResiduos,
    partidas_del_contrato,
)
from tests.f036_escenarios_residuos import (
    EscenarioResiduos,
    LineaResiduos,
    construir_envelope,
    linea_contrato,
)

_COLUMNAS = ["ide", "padide", "cod", "res"]

#: Lo común: la maquinaria ajena con los contenedores (CI.03A.7) y una
#: estructura que no es de residuos.
_COMUN = [
    (900, 0, "CI", "COSTES INDIRECTOS"),
    (901, 900, "CI.03A", "MAQUINARIA AJENA"),
    (902, 901, "CI.03A.7", "CONTENEDORES"),
    (800, 0, "05", "ESTRUCTURA"),
    (801, 800, "05.01", "HORMIGÓN"),
]
#: 0686: dos hojas en el capítulo de residuos (32.01 y 37.06.01).
FILAS_0686 = [
    (1, 0, "32", "GESTIÓN RESIDUOS (SEGÚN EGRC)"),
    (2, 1, "32.01", "GRD010 Gestión de residuos"),
    (3, 0, "37", "SEGURIDAD Y SALUD"),
    (4, 3, "37.06", "GESTIÓN DE RESIDUOS"),
    (5, 4, "37.06.01", "OPERARIO EXCLUSIVO PARA CLASIFICACIÓN"),
    *_COMUN,
]
#: 0669: dos hojas del capítulo (31.01 y 102.08.01) y una tercera (31.02).
FILAS_0669 = [
    (1, 0, "31", "GESTIÓN DE RESIDUOS"),
    (2, 1, "31.01", "Residuos de construcción"),
    (3, 1, "31.02", "Residuos peligrosos"),
    (4, 0, "102", "URBANIZACIÓN"),
    (5, 4, "102.08", "GESTIÓN DE RESIDUOS URBANIZACIÓN"),
    (6, 5, "102.08.01", "Tierras"),
    *_COMUN,
]
#: 0694: capítulo de residuos con una hoja (23.01), pero el contrato trae CI.03A.7.
FILAS_0694 = [
    (1, 0, "23", "PLAN DE GESTIÓN DE RESIDUOS"),
    (2, 1, "23.01", "Gestión de residuos de construcción"),
    *_COMUN,
]
#: 0687: una sola hoja en el capítulo (19.01).
FILAS_0687 = [
    (1, 0, "19", "GESTIÓN DE RESIDUOS"),
    (2, 1, "19.01", "Gestión de residuos"),
    *_COMUN,
]
#: 0459: muchas hojas en el capítulo.
FILAS_0459 = [(1, 0, "19", "GESTIÓN DE RESIDUOS")] + [
    (10 + i, 1, f"19.{i:02d}", f"Residuo {i}") for i in range(1, 20)
] + _COMUN
#: Obra sin capítulo de residuos.
FILAS_SIN_CAPITULO = list(_COMUN)


def _lista(filas, obra="0686") -> ListaPartidasObra:
    return ListaPartidasObra.desde_filas(obra, _COLUMNAS, filas)


def _contrato(*partidas):
    return tuple(
        linea_contrato(9000 + i, f"LINEA {i}", 10.0, partida=p) for i, p in enumerate(partidas)
    )


class _Partidas:
    def __init__(self, lista):
        self._lista = lista
        self.consultas = []

    def lista(self, obra):
        self.consultas.append(obra)
        return self._lista


class _Elector:
    """Responde por llamada: ``respuestas[i]`` es el dict o la excepción de la i-ésima."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.llamadas: list[dict] = []

    def elegir(self, *, document_id, lineas, candidatas):
        self.llamadas.append({"document_id": document_id, "lineas": lineas, "candidatas": candidatas})
        respuesta = self.respuestas[len(self.llamadas) - 1] if len(self.llamadas) <= len(self.respuestas) else {}
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    def codigos(self, i):
        return [c["codigo"] for c in self.llamadas[i]["candidatas"]]


def _envelope(*lineas, contrato=(), partidas=None):
    env = construir_envelope(
        EscenarioResiduos(lineas=tuple(lineas) or (LineaResiduos(),), contrato=tuple(contrato))
    )
    for i, ctx in enumerate(env.context.lineas_albaran):
        ctx.codigo_partida_albaran = (partidas or {}).get(i)
    return env


def _asignar(filas, contrato, *, elector=None, lineas=(), partidas=None, activo=True, obra="0686"):
    asignador = AsignadorPartidaResiduos(
        partidas=_Partidas(_lista(filas, obra) if filas is not None else None),
        elector=elector, alm_codigo_partida="ALM", activo=activo,
    )
    env = _envelope(*lineas, contrato=contrato, partidas=partidas)
    return asignador.asignar(envelope=env, obra=obra), env


# ------------------------------------------------------------------ #
# R37 · partidas del contrato
# ------------------------------------------------------------------ #
def test_f111_r37_partidas_del_contrato_descarta_y_deduplica():
    lista = _lista(FILAS_0686)
    contrato = _contrato(*(["32.01"] * 120), "CI.03A.7", "ALM", " alm ", None, "", "99.99", "32.1", "CI.3A.07")
    partidas = partidas_del_contrato(contrato, lista, "ALM")
    assert [p.codigo for p in partidas] == ["32.01", "CI.03A.7"]
    assert partidas[0].descripcion == "GRD010 Gestión de residuos"
    assert partidas[0] is next(h for h in lista.hojas if h.codigo == "32.01")


def test_f111_r37_partidas_del_contrato_respeta_el_orden_de_aparicion():
    lista = _lista(FILAS_0686)
    partidas = partidas_del_contrato(_contrato("CI.03A.7", "37.06.01", "32.01"), lista, "ALM")
    assert [p.codigo for p in partidas] == ["CI.03A.7", "37.06.01", "32.01"]


def test_f111_r37_normalizada_y_completa_valen_con_el_cod_de_la_lista():
    lista = _lista(FILAS_0686)
    assert [p.codigo for p in partidas_del_contrato(_contrato("32.1"), lista, "ALM")] == ["32.01"]


def test_f111_r37_no_hoja_ambigua_y_cod_repetido_fuera():
    filas = [
        (1, 0, "03", "CAPITULO TRES"),     # no hoja «03»
        (2, 1, "03.01", "Hoja"),
        (3, 0, "X", "OTRO"),
        (4, 3, "3", "Hoja que normaliza como el no hoja"),
        (5, 3, "3.1", "Ambigua A"),
        (6, 3, "03.1", "Ambigua B"),
        (7, 0, "CD", "COSTES DIRECTOS"),
        (8, 7, "19.01", "Repetida en CD"),
        (9, 0, "CP", "COSTES PROPIOS"),
        (10, 9, "19.01", "Repetida en CP"),
        (11, 0, "50", "BUENA"),
        (12, 11, "50.01", "Buena"),
    ]
    lista = _lista(filas)
    assert lista.cod_repetido("19.01")
    contrato = _contrato("003", "3.01", "19.01", "03", "50.01")
    assert [p.codigo for p in partidas_del_contrato(contrato, lista, "ALM")] == ["50.01"]


def test_f111_r37_sin_lineas_de_contrato_tupla_vacia():
    assert partidas_del_contrato([], _lista(FILAS_0686), "ALM") == ()
    assert partidas_del_contrato(_contrato(None, "", "ALM"), _lista(FILAS_0686), "ALM") == ()


def test_f111_r37_sin_alm_un_alm_es_una_lectura_mas():
    lista = _lista(FILAS_0686 + [(70, 0, "ALM", "ALMACEN")])
    assert [p.codigo for p in partidas_del_contrato(_contrato("ALM"), lista, None)] == ["ALM"]
    assert partidas_del_contrato(_contrato("ALM"), lista, "ALM") == ()


# ------------------------------------------------------------------ #
# R38 · paso 1: partidas del contrato del capítulo de residuos
# ------------------------------------------------------------------ #
def test_f111_r38_0686_32_01_sin_ia_aunque_el_capitulo_tenga_dos():
    elector = _Elector()
    asignacion, env = _asignar(FILAS_0686, _contrato(*(["32.01"] * 120), "CI.03A.7"), elector=elector)
    r = asignacion.por_linea[700]
    assert r.codigo == "32.01"
    assert r.motivo == f"{PREFIJO_PARTIDA_RESIDUOS_CONTRATO}32.01"
    assert r.revision is False and r.intento is None
    assert elector.llamadas == []
    assert asignacion.envelope.context.lineas_albaran[0].codigo_partida_albaran == "32.01"
    assert env.context.lineas_albaran[0].codigo_partida_albaran is None
    assert asignacion.sin_almacen == frozenset()


def test_f111_r38_0669_la_ia_elige_solo_entre_las_del_contrato_del_capitulo():
    elector = _Elector({700: "102.08.01"})
    asignacion, _ = _asignar(
        FILAS_0669, _contrato("31.01", "102.08.01", "CI.03A.7"), elector=elector, obra="0669",
    )
    assert len(elector.llamadas) == 1
    assert elector.codigos(0) == ["31.01", "102.08.01"]
    assert elector.llamadas[0]["document_id"] == "doc-SS-0000589"
    r = asignacion.por_linea[700]
    assert r.codigo == "102.08.01"
    assert r.motivo == f"{PREFIJO_PARTIDA_RESIDUOS_CONTRATO}102.08.01"
    assert r.intento is None


# ------------------------------------------------------------------ #
# R39 · paso 2: ninguna del capítulo, pero el contrato trae alguna
# ------------------------------------------------------------------ #
def test_f111_r39_0694_ci_03a_7_sin_ia_aunque_haya_capitulo():
    elector = _Elector()
    asignacion, _ = _asignar(FILAS_0694, _contrato("CI.03A.7"), elector=elector, obra="0694")
    r = asignacion.por_linea[700]
    assert r.codigo == "CI.03A.7"
    assert r.motivo == f"{PREFIJO_PARTIDA_RESIDUOS_CONTRATO_HOJA}CI.03A.7"
    assert r.revision is False
    assert elector.llamadas == []


def test_f111_r39_varias_del_contrato_fuera_del_capitulo_la_ia_solo_entre_esas():
    elector = _Elector({700: "05.01"})
    asignacion, _ = _asignar(FILAS_0694, _contrato("CI.03A.7", "05.01"), elector=elector, obra="0694")
    assert elector.codigos(0) == ["CI.03A.7", "05.01"]
    assert asignacion.por_linea[700].motivo == f"{PREFIJO_PARTIDA_RESIDUOS_CONTRATO_HOJA}05.01"


# ------------------------------------------------------------------ #
# R40 · paso 3: el contrato no aporta ninguna
# ------------------------------------------------------------------ #
def test_f111_r40_0687_sin_partidas_en_el_contrato_19_01():
    elector = _Elector()
    asignacion, _ = _asignar(FILAS_0687, _contrato(None, "99.99"), elector=elector, obra="0687")
    r = asignacion.por_linea[700]
    assert r.motivo == f"{PREFIJO_PARTIDA_RESIDUOS}19.01" and r.intento is None
    assert elector.llamadas == []


def test_f111_r40_0459_ia_entre_las_del_capitulo():
    elector = _Elector({700: "19.07"})
    asignacion, _ = _asignar(FILAS_0459, (), elector=elector, obra="0459")
    assert len(elector.llamadas) == 1
    assert len(elector.codigos(0)) == 19
    assert asignacion.por_linea[700].motivo == f"{PREFIJO_PARTIDA_RESIDUOS}19.07"


def test_f111_r40_sin_capitulo_y_contrato_sin_partidas_a_revision():
    asignacion, _ = _asignar(FILAS_SIN_CAPITULO, _contrato("ALM"), elector=_Elector())
    r = asignacion.por_linea[700]
    assert r.motivo == MOTIVO_SIN_CAPITULO and r.revision is True and r.intento is None
    assert asignacion.sin_almacen == frozenset({700})


def test_f111_r39_sin_capitulo_pero_con_partida_del_contrato_la_usa():
    asignacion, _ = _asignar(FILAS_SIN_CAPITULO, _contrato("CI.03A.7"))
    assert asignacion.por_linea[700].motivo == f"{PREFIJO_PARTIDA_RESIDUOS_CONTRATO_HOJA}CI.03A.7"


# ------------------------------------------------------------------ #
# R41, R43 · caída al capítulo, como mucho dos llamadas
# ------------------------------------------------------------------ #
_DOS_LINEAS = (LineaResiduos(merge_line_id=700), LineaResiduos(merge_line_id=701))


@pytest.mark.parametrize(
    "primera",
    [{700: None}, {700: "37.06.01"}, {700: "05.01"}, {}, RuntimeError("sv5 caído")],
    ids=["null", "fuera_del_conjunto", "otra_hoja", "sin_respuesta", "fallo"],
)
def test_f111_r43_0669_la_ia_no_elige_cae_al_capitulo(primera):
    elector = _Elector(primera, {700: "31.02"})
    asignacion, _ = _asignar(
        FILAS_0669, _contrato("31.01", "102.08.01", "CI.03A.7"), elector=elector, obra="0669",
    )
    assert len(elector.llamadas) == 2
    assert elector.codigos(1) == ["102.08.01", "31.01", "31.02"]  # el capítulo, en el orden de la lista
    r = asignacion.por_linea[700]
    assert r.codigo == "31.02"
    assert r.motivo == f"{PREFIJO_PARTIDA_RESIDUOS}31.02"
    assert r.intento == f"{MOTIVO_CONTRATO_SIN_ELECCION}:31.01,102.08.01"
    assert r.revision is False
    assert asignacion.envelope.context.lineas_albaran[0].codigo_partida_albaran == "31.02"


def test_f111_r41_solo_las_que_caen_van_a_la_segunda_llamada():
    elector = _Elector({700: "31.01", 701: None}, {701: "31.02"})
    asignacion, _ = _asignar(
        FILAS_0669, _contrato("31.01", "102.08.01"), elector=elector, lineas=_DOS_LINEAS, obra="0669",
    )
    assert len(elector.llamadas) == 2
    assert [l["line_ref"] for l in elector.llamadas[0]["lineas"]] == [700, 701]
    assert [l["line_ref"] for l in elector.llamadas[1]["lineas"]] == [701]
    assert asignacion.por_linea[700].motivo == f"{PREFIJO_PARTIDA_RESIDUOS_CONTRATO}31.01"
    assert asignacion.por_linea[700].intento is None
    assert asignacion.por_linea[701].motivo == f"{PREFIJO_PARTIDA_RESIDUOS}31.02"
    assert asignacion.por_linea[701].intento == f"{MOTIVO_CONTRATO_SIN_ELECCION}:31.01,102.08.01"
    lineas = asignacion.envelope.context.lineas_albaran
    assert [l.codigo_partida_albaran for l in lineas] == ["31.01", "31.02"]


def test_f111_r41_con_todas_elegidas_una_sola_llamada():
    elector = _Elector({700: "31.01", 701: "102.08.01"})
    _asignar(FILAS_0669, _contrato("31.01", "102.08.01"), elector=elector, lineas=_DOS_LINEAS, obra="0669")
    assert len(elector.llamadas) == 1


def test_f111_r43_cae_al_capitulo_de_una_sin_segunda_llamada():
    elector = _Elector({700: None})
    asignacion, _ = _asignar(FILAS_0687, _contrato("CI.03A.7", "05.01"), elector=elector, obra="0687")
    assert len(elector.llamadas) == 1
    r = asignacion.por_linea[700]
    assert r.motivo == f"{PREFIJO_PARTIDA_RESIDUOS}19.01"
    assert r.intento == f"{MOTIVO_CONTRATO_SIN_ELECCION}:CI.03A.7,05.01"


def test_f111_r43_cae_y_el_capitulo_tambien_falla_a_revision():
    elector = _Elector({700: None}, {700: None})
    asignacion, _ = _asignar(
        FILAS_0669, _contrato("31.01", "102.08.01"), elector=elector, obra="0669",
    )
    r = asignacion.por_linea[700]
    assert r.revision is True
    assert r.motivo == f"{MOTIVO_SIN_CANDIDATA}:102.08.01,31.01,31.02"
    assert r.intento == f"{MOTIVO_CONTRATO_SIN_ELECCION}:31.01,102.08.01"
    assert asignacion.sin_almacen == frozenset({700})


def test_f111_r43_cae_y_la_ia_del_capitulo_falla_a_revision():
    elector = _Elector(RuntimeError("x"), RuntimeError("y"))
    asignacion, _ = _asignar(FILAS_0669, _contrato("31.01", "102.08.01"), elector=elector, obra="0669")
    assert asignacion.por_linea[700].motivo.startswith(f"{MOTIVO_IA_FALLO}:")


def test_f111_r43_cae_a_una_obra_sin_capitulo_a_revision():
    elector = _Elector({700: None})
    asignacion, _ = _asignar(FILAS_SIN_CAPITULO, _contrato("CI.03A.7", "05.01"), elector=elector)
    r = asignacion.por_linea[700]
    assert r.motivo == MOTIVO_SIN_CAPITULO and r.revision is True
    assert r.intento == f"{MOTIVO_CONTRATO_SIN_ELECCION}:CI.03A.7,05.01"
    assert len(elector.llamadas) == 1


def test_f111_r43_sin_elector_cae_y_con_un_capitulo_de_una_se_asigna():
    asignacion, _ = _asignar(FILAS_0687, _contrato("CI.03A.7", "05.01"), elector=None, obra="0687")
    r = asignacion.por_linea[700]
    assert r.motivo == f"{PREFIJO_PARTIDA_RESIDUOS}19.01"
    assert r.intento == f"{MOTIVO_CONTRATO_SIN_ELECCION}:CI.03A.7,05.01"


def test_f111_r43_el_intento_cita_hasta_5_codigos():
    filas = FILAS_0687 + [(60, 0, "60", "VARIOS")] + [(60 + i, 60, f"60.0{i}", f"V{i}") for i in range(1, 8)]
    elector = _Elector({700: None})
    asignacion, _ = _asignar(filas, _contrato(*(f"60.0{i}" for i in range(1, 8))), elector=elector, obra="0687")
    assert asignacion.por_linea[700].intento == (
        f"{MOTIVO_CONTRATO_SIN_ELECCION}:60.01,60.02,60.03,60.04,60.05(+2)"
    )


# ------------------------------------------------------------------ #
# R44, R45 · sin lista, con lectura, apagado
# ------------------------------------------------------------------ #
def test_f111_r44_sin_lista_no_usa_el_contrato_sin_validar():
    asignacion, env = _asignar(None, _contrato("32.01"))
    r = asignacion.por_linea[700]
    assert r.motivo == MOTIVO_SIN_LISTA and r.codigo is None and r.intento is None
    assert asignacion.envelope is env


def test_f111_r45_con_lectura_y_apagado_no_se_toca():
    elector = _Elector()
    asignacion, env = _asignar(FILAS_0686, _contrato("32.01"), elector=elector, partidas={0: "05.01"})
    assert asignacion.por_linea == {} and asignacion.envelope is env
    asignacion, env = _asignar(FILAS_0686, _contrato("32.01"), partidas={0: "ALM"})
    assert asignacion.por_linea == {}
    asignacion, env = _asignar(FILAS_0686, _contrato("32.01"), activo=False)
    assert asignacion.por_linea == {} and asignacion.envelope is env
    otra, env = _asignar(FILAS_0686, _contrato("32.01"), lineas=(LineaResiduos(tipo_familia="hormigon"),))
    assert otra.por_linea == {}
    assert elector.llamadas == []


# ------------------------------------------------------------------ #
# R42, R43 · anotar: motivo e intento en la línea, nunca en cabecera
# ------------------------------------------------------------------ #
def _registros(envelope):
    from tests.f027_escenarios import construir_builder

    return construir_builder().build(envelope=envelope, existing_document_already_valued=False)


def test_f111_r42_anotar_contrato_sin_revision_y_lectura_de_vuelta():
    asignacion, _ = _asignar(FILAS_0686, _contrato("32.01"))
    cab, regs = _registros(asignacion.envelope)
    base = next(r for r in regs if r.line_kind == "from_albaran")
    revision_antes, motivos_cab = base.review_required, list(cab.review_reasons)
    AsignadorPartidaResiduos.anotar(cab, regs, asignacion)
    assert base.codigo_partida_albaran is None
    assert f"{PREFIJO_PARTIDA_RESIDUOS_CONTRATO}32.01" in base.review_reasons
    assert base.review_required is revision_antes
    assert cab.review_reasons == motivos_cab


def test_f111_r43_anotar_intento_antes_del_motivo_y_sin_cabecera():
    elector = _Elector({700: None}, {700: "31.02"})
    asignacion, _ = _asignar(FILAS_0669, _contrato("31.01", "102.08.01"), elector=elector, obra="0669")
    cab, regs = _registros(asignacion.envelope)
    cab.review_required, cab.review_reasons = False, []
    base = next(r for r in regs if r.line_kind == "from_albaran")
    base.review_required, base.review_reasons = False, []
    AsignadorPartidaResiduos.anotar(cab, regs, asignacion)
    intento = f"{MOTIVO_CONTRATO_SIN_ELECCION}:31.01,102.08.01"
    assert base.review_reasons == [intento, f"{PREFIJO_PARTIDA_RESIDUOS}31.02"]
    assert base.review_required is False
    assert cab.review_required is False and cab.review_reasons == []
    AsignadorPartidaResiduos.anotar(cab, regs, asignacion)
    assert base.review_reasons.count(intento) == 1


def test_f111_r43_anotar_intento_y_revision_del_capitulo():
    elector = _Elector({700: None}, {700: None})
    asignacion, _ = _asignar(FILAS_0669, _contrato("31.01", "102.08.01"), elector=elector, obra="0669")
    cab, regs = _registros(asignacion.envelope)
    cab.review_required, cab.review_reasons = False, []
    base = next(r for r in regs if r.line_kind == "from_albaran")
    base.review_reasons = []
    AsignadorPartidaResiduos.anotar(cab, regs, asignacion)
    assert base.review_reasons[0] == f"{MOTIVO_CONTRATO_SIN_ELECCION}:31.01,102.08.01"
    assert base.review_reasons[1].startswith(MOTIVO_SIN_CANDIDATA)
    assert base.review_required is True and cab.review_required is True
    assert MOTIVO_CONTRATO_SIN_ELECCION not in cab.review_reasons
    assert not any(m.startswith(MOTIVO_CONTRATO_SIN_ELECCION) for m in cab.review_reasons)
    assert MOTIVO_SIN_CANDIDATA in cab.review_reasons


# ------------------------------------------------------------------ #
# R46 · constantes congeladas y paso en el log
# ------------------------------------------------------------------ #
def test_f111_r46_constantes_congeladas():
    assert PREFIJO_PARTIDA_RESIDUOS_CONTRATO == "partida_residuos_contrato:"
    assert PREFIJO_PARTIDA_RESIDUOS_CONTRATO_HOJA == "partida_residuos_contrato_hoja:"
    assert MOTIVO_CONTRATO_SIN_ELECCION == "partida_residuos_contrato_sin_eleccion"
    assert ResultadoPartidaResiduos("x", "m").intento is None


@pytest.mark.parametrize(
    "filas, contrato, paso",
    [
        (FILAS_0686, ("32.01",), "contrato"),
        (FILAS_0694, ("CI.03A.7",), "contrato_hoja"),
        (FILAS_0687, (), "capitulo"),
    ],
)
def test_f111_r46_el_log_dice_el_paso(caplog, filas, contrato, paso):
    with caplog.at_level(logging.INFO, logger="application.services.partida_residuos"):
        _asignar(filas, _contrato(*contrato))
    mensajes = [r.getMessage() for r in caplog.records]
    assert any(
        f"paso={paso} " in m and "asignadas=1 a_revision=0 caidas_al_capitulo=0" in m for m in mensajes
    )


def test_f111_r46_el_log_cuenta_las_caidas_al_capitulo(caplog):
    elector = _Elector({700: "31.01", 701: None}, {701: "31.02"})
    with caplog.at_level(logging.INFO, logger="application.services.partida_residuos"):
        _asignar(FILAS_0669, _contrato("31.01", "102.08.01"), elector=elector, lineas=_DOS_LINEAS, obra="0669")
    mensajes = [r.getMessage() for r in caplog.records]
    assert any(
        "paso=contrato candidatas=2 asignadas=2 a_revision=0 caidas_al_capitulo=1" in m for m in mensajes
    )


def test_f111_r37_lineas_de_contrato_none_tupla_vacia():
    assert partidas_del_contrato(None, _lista(FILAS_0686), "ALM") == ()


def test_f111_r37_asignar_pasa_el_alm_un_alm_del_contrato_no_es_hoja():
    """Aunque la obra tuviera una hoja ``ALM``, un ``ALM`` del contrato es almacén: paso 3."""
    filas = FILAS_0687 + [(70, 0, "ALM", "ALMACEN")]
    asignacion, _ = _asignar(filas, _contrato("ALM"), obra="0687")
    assert asignacion.por_linea[700].motivo == f"{PREFIJO_PARTIDA_RESIDUOS}19.01"
