# tests/test_f051_almacen_front.py
"""F-051 · almacén por línea · sv4 pinta, elige y asigna almacén.

Decisión del humano (D1, PARADA 1 del 2026-10-05): «en el visor cuando
una línea no tenga partida que sea almacén […] negocio ya funciona así a
mano». Una línea con valoración y ``codigo_partida_final`` vacío ES
almacén, tenga o no marca en ``partida_action`` (la marca solo deja
rastro de quién o por qué). Vaciar la partida en sv4 es elegir almacén
(R12) y una fila de contrato en almacén sigue siendo de contrato (D4).

Sin red, sin BBDD real y sin LLM: funciones puras, el repositorio sobre
SQLite en memoria (patrón de ``conftest.py``), la plantilla real con
Jinja2 y la API con ``TestClient`` y servicio falso.
"""
from __future__ import annotations

import pytest

# =================================================================== #
# R10 · estado de partida: dos valores, sin mirar la marca
# =================================================================== #


@pytest.mark.parametrize("final", ["03.02", " 03.02 ", "ALM"])
def test_f051_r10_partida_no_vacia_es_partida(final):
    from domain.services.almacen import estado_partida

    assert estado_partida(final) == "partida"


@pytest.mark.parametrize("final", [None, "", "   ", "\t"])
def test_f051_r10_vacia_o_espacios_es_almacen(final):
    from domain.services.almacen import estado_partida

    assert estado_partida(final) == "almacen"


def test_f051_r10_la_firma_no_recibe_la_marca():
    """D1 v4: ninguna marca decide el estado (legado ``no_action``,
    ``almacen_sin_partida``, ``almacen_elegido`` o sin marca)."""
    import inspect

    from domain.services.almacen import estado_partida

    assert list(inspect.signature(estado_partida).parameters) == [
        "codigo_partida_final",
    ]


def test_f051_r10_accion_almacen_elegido():
    from domain.services.almacen import ACCION_ALMACEN_ELEGIDO

    assert ACCION_ALMACEN_ELEGIDO == "almacen_elegido"


def test_f051_r17_contar_con_partida():
    from domain.services.almacen import contar_con_partida

    assert contar_con_partida(["03.02", None, "", "  ", "04.05", "ALM"]) == 3
    assert contar_con_partida([]) == 0
    assert contar_con_partida(iter([None, "01"])) == 1


# =================================================================== #
# R21 · confianza: la partida vacía con valoración está resuelta
# =================================================================== #


def _conciliacion(**campos):
    from domain.models.review_models import ConciliacionDisplay

    return ConciliacionDisplay(**{"kind": "assigned", **campos})


@pytest.mark.parametrize("partida", [None, "", "  "])
def test_f051_r21_almacen_con_valoracion_puntua_1(partida):
    from domain.services.confianza import _partida_factor

    assert _partida_factor(_conciliacion(codigo_partida=partida)) == 1.0


def test_f051_r21_con_partida_sigue_puntuando_1():
    from domain.services.confianza import _partida_factor

    assert _partida_factor(_conciliacion(codigo_partida="03.02")) == 1.0


def test_f051_r21_sin_valoracion_sigue_puntuando_0():
    from domain.services.confianza import _partida_factor

    assert _partida_factor(None) == 0.0


def test_f051_r21_la_linea_en_almacen_no_resta_confianza():
    """Misma línea, con y sin partida: misma puntuación."""
    from domain.services.confianza import _line_score

    con = _conciliacion(codigo_partida="03.02", match_method="exact_concept",
                        match_confidence_pct=95.0, agree_unitario=True,
                        precio_unitario_final=10.0)
    sin = _conciliacion(codigo_partida=None, match_method="exact_concept",
                        match_confidence_pct=95.0, agree_unitario=True,
                        precio_unitario_final=10.0)
    assert _line_score(sin) == _line_score(con)


# =================================================================== #
# Repositorio sobre SQLite en memoria (R12, R14-R16, R19, R20, R23)
# =================================================================== #

DOC = "f051-doc-0000"
DOC_AJENO = "f051-doc-ajeno"
VAL = "f051-val-0000"
VAL_AJENO = "f051-val-ajeno"

#: Tablas de contrato que lee ``update_line_conciliacion`` (subconjunto:
#: el schema real lo gobiernan sv3 y sv6).
_DDL_CONTRATO = (
    """
    CREATE TABLE albaran_contrato_lines_merge (
        id                  INTEGER PRIMARY KEY,
        codigo_contrato     VARCHAR(64),
        codigo_producto     VARCHAR(64),
        codigo_partida      VARCHAR(64),
        descripcion_partida TEXT,
        descripcion_linea   TEXT,
        unidad_medida       VARCHAR(32),
        precio_unitario     DOUBLE PRECISION,
        uds                 DOUBLE PRECISION,
        pendiente_servir    DOUBLE PRECISION
    )
    """,
    """
    CREATE TABLE contrato_lines_derived (
        id                       INTEGER PRIMARY KEY,
        created_by_valuation_id  VARCHAR(64),
        source_document_id       VARCHAR(64),
        codigo_contrato          VARCHAR(64),
        codigo_producto          VARCHAR(64),
        descripcion_linea        TEXT,
        unidad_medida            VARCHAR(32),
        precio_unitario          DOUBLE PRECISION,
        codigo_partida           VARCHAR(64),
        origen                   VARCHAR(32),
        created_at_utc           VARCHAR(40)
    )
    """,
)

_COLUMNAS_LINEA = (
    "id, valuation_id, merge_line_id, matched_contrato_line_id, "
    "derived_contrato_line_id, precio_unitario_final, unidad_contrato, "
    "cantidad_albaran, importe_calculado, importe_source, "
    "descuento_albaran_aplicado, codigo_partida_final, partida_action, "
    "line_kind, review_required, review_reasons_json"
)


class _Factoria:
    """``SessionFactory`` mínima: sesiones nuevas sobre el mismo motor."""

    def __init__(self, motor):
        self._motor = motor

    def create_session(self):
        from sqlalchemy.orm import Session

        return Session(self._motor)


def _linea_valoracion(sesion, **campos):
    from sqlalchemy import text

    fila = {
        "valuation_id": VAL,
        "merge_line_id": None,
        "matched_contrato_line_id": None,
        "derived_contrato_line_id": None,
        "precio_unitario_final": 12.5,
        "unidad_contrato": "TN",
        "cantidad_albaran": 2.0,
        "importe_calculado": 25.0,
        "importe_source": "calculated",
        "descuento_albaran_aplicado": None,
        "codigo_partida_final": None,
        "partida_action": "existing_matched",
        "line_kind": "from_albaran",
        "review_required": True,
        "review_reasons_json": '["ia_match_trusted"]',
        **campos,
    }
    sesion.execute(
        text(
            f"INSERT INTO albaran_line_valuations ({_COLUMNAS_LINEA}) VALUES ("
            + ", ".join(f":{c.strip()}" for c in _COLUMNAS_LINEA.split(","))
            + ")"
        ),
        fila,
    )


@pytest.fixture
def repo_sqlite(sesion, monkeypatch):
    """Repositorio real sobre SQLite con un albarán de cuatro líneas:

    - 11 · Sigrid (casada con la 501, partida 03.02).
    - 12 · Nueva (derivada 601, partida 04.05).
    - 13 · Sigrid EN ALMACÉN (casada con la 501, partida final vacía).
    - 14 · sintética que hereda 03.02.

    Y otro albarán (``DOC_AJENO``) con la línea 21, que nadie debe tocar.
    """
    from sqlalchemy import text

    from infrastructure.database.review_repository import (
        AlbaranReviewRepository,
    )

    for sentencia in _DDL_CONTRATO:
        sesion.execute(text(sentencia))
    sesion.execute(text(
        "INSERT INTO albaran_valuations (id, document_id, contrato_codigo, "
        "status, total_valorado, review_required) VALUES "
        "(:v1, :d1, 'CTSU25/0051', 'ok', 100.0, 1), "
        "(:v2, :d2, 'CTSU25/0051', 'ok', 50.0, 0)"
    ), {"v1": VAL, "d1": DOC, "v2": VAL_AJENO, "d2": DOC_AJENO})
    sesion.execute(text(
        "INSERT INTO albaran_contrato_lines_merge (id, codigo_contrato, "
        "codigo_partida, descripcion_partida, descripcion_linea, "
        "unidad_medida, precio_unitario) VALUES "
        "(501, 'CTSU25/0051', '03.02', 'Cimentación', 'ARIDO 20/40', "
        "'TN', 12.5)"
    ))
    sesion.execute(text(
        "INSERT INTO contrato_lines_derived (id, created_by_valuation_id, "
        "codigo_contrato, descripcion_linea, unidad_medida, precio_unitario, "
        "codigo_partida, origen) VALUES "
        "(601, :v1, 'CTSU25/0051', 'PORTE', 'UD', 40.0, '04.05', "
        "'missing_partida')"
    ), {"v1": VAL})
    _linea_valoracion(sesion, id=11, merge_line_id=701,
                      matched_contrato_line_id=501,
                      codigo_partida_final="03.02",
                      descuento_albaran_aplicado=5.0)
    _linea_valoracion(sesion, id=12, merge_line_id=702,
                      derived_contrato_line_id=601,
                      precio_unitario_final=40.0, unidad_contrato="UD",
                      importe_calculado=80.0,
                      codigo_partida_final="04.05",
                      partida_action="new_line_created")
    _linea_valoracion(sesion, id=13, merge_line_id=703,
                      matched_contrato_line_id=501,
                      codigo_partida_final=None,
                      partida_action="almacen_sin_partida")
    _linea_valoracion(sesion, id=14, merge_line_id=None,
                      matched_contrato_line_id=501,
                      codigo_partida_final="03.02",
                      partida_action="inherited_from_base_line",
                      line_kind="synthetic_modifier")
    _linea_valoracion(sesion, id=21, valuation_id=VAL_AJENO,
                      merge_line_id=801, matched_contrato_line_id=501,
                      codigo_partida_final="03.02")
    sesion.commit()

    repo = AlbaranReviewRepository(_Factoria(sesion.get_bind()))
    monkeypatch.setattr(repo, "initialize", lambda: True)
    return repo


def _fila(repo, vid):
    from sqlalchemy import text

    with repo._session_factory.create_session() as s:
        return dict(s.execute(
            text(f"SELECT {_COLUMNAS_LINEA} FROM albaran_line_valuations "
                 "WHERE id = :id"),
            {"id": vid},
        ).mappings().one())


def _derivadas(repo):
    from sqlalchemy import text

    with repo._session_factory.create_session() as s:
        return [dict(r) for r in s.execute(text(
            "SELECT id, codigo_partida, origen FROM contrato_lines_derived "
            "ORDER BY id"
        )).mappings().all()]


_INTOCABLES = (
    "matched_contrato_line_id", "derived_contrato_line_id",
    "precio_unitario_final", "cantidad_albaran", "importe_calculado",
    "importe_source", "descuento_albaran_aplicado", "review_required",
    "review_reasons_json", "unidad_contrato", "line_kind",
)


def test_f051_r14_asignar_almacen_a_una_linea(repo_sqlite):
    antes = _fila(repo_sqlite, 11)

    tocadas = repo_sqlite.asignar_almacen(
        document_id=DOC, valuation_line_ids=[11],
    )

    despues = _fila(repo_sqlite, 11)
    assert tocadas == [11]
    assert despues["codigo_partida_final"] is None
    assert despues["partida_action"] == "almacen_elegido"
    for campo in _INTOCABLES:
        assert despues[campo] == antes[campo], campo
    # Las demás líneas del documento, igual.
    assert _fila(repo_sqlite, 12)["codigo_partida_final"] == "04.05"


def test_f051_r15_la_fila_sigrid_sigue_casada_con_su_linea_de_contrato(
    repo_sqlite,
):
    repo_sqlite.asignar_almacen(document_id=DOC, valuation_line_ids=[11])

    fila = _fila(repo_sqlite, 11)
    assert fila["matched_contrato_line_id"] == 501
    assert fila["derived_contrato_line_id"] is None
    assert _derivadas(repo_sqlite) == [
        {"id": 601, "codigo_partida": "04.05", "origen": "missing_partida"},
    ]


def test_f051_r16_almacen_a_todas_las_lineas_del_documento(repo_sqlite):
    antes = {vid: _fila(repo_sqlite, vid) for vid in (11, 12, 13, 14)}

    tocadas = repo_sqlite.asignar_almacen(
        document_id=DOC, valuation_line_ids=None,
    )

    assert sorted(tocadas) == [11, 12, 13, 14]
    for vid in (11, 12, 13, 14):
        fila = _fila(repo_sqlite, vid)
        assert fila["codigo_partida_final"] is None, vid
        assert fila["partida_action"] == "almacen_elegido", vid
        for campo in _INTOCABLES:
            assert fila[campo] == antes[vid][campo], (vid, campo)
    # El otro albarán no se toca.
    ajena = _fila(repo_sqlite, 21)
    assert ajena["codigo_partida_final"] == "03.02"
    assert ajena["partida_action"] == "existing_matched"


def test_f051_r16_todas_en_un_unico_update(repo_sqlite):
    """Una sola sentencia UPDATE: todo o nada (una transacción)."""
    from sqlalchemy import event

    motor = repo_sqlite._session_factory._motor
    sentencias: list[str] = []

    def _espia(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("UPDATE"):
            sentencias.append(statement)

    event.listen(motor, "before_cursor_execute", _espia)
    try:
        repo_sqlite.asignar_almacen(document_id=DOC, valuation_line_ids=None)
    finally:
        event.remove(motor, "before_cursor_execute", _espia)

    assert len(sentencias) == 1
    assert "albaran_line_valuations" in sentencias[0]


def test_f051_r23_linea_de_otro_documento_no_se_toca(repo_sqlite):
    tocadas = repo_sqlite.asignar_almacen(
        document_id=DOC, valuation_line_ids=[21],
    )

    assert tocadas == []
    assert _fila(repo_sqlite, 21)["codigo_partida_final"] == "03.02"
    assert _fila(repo_sqlite, 21)["partida_action"] == "existing_matched"


def test_f051_r23_mezcla_de_propias_y_ajenas_solo_toca_las_propias(
    repo_sqlite,
):
    tocadas = repo_sqlite.asignar_almacen(
        document_id=DOC, valuation_line_ids=[11, 21],
    )

    assert tocadas == [11]
    assert _fila(repo_sqlite, 21)["codigo_partida_final"] == "03.02"


def test_f051_r23_documento_sin_valoracion_no_toca_nada(repo_sqlite):
    assert repo_sqlite.asignar_almacen(
        document_id="no-existe", valuation_line_ids=None,
    ) == []
    assert repo_sqlite.asignar_almacen(
        document_id="no-existe", valuation_line_ids=[11],
    ) == []
    assert _fila(repo_sqlite, 11)["codigo_partida_final"] == "03.02"


def test_f051_r23_lista_vacia_no_toca_nada(repo_sqlite):
    assert repo_sqlite.asignar_almacen(
        document_id=DOC, valuation_line_ids=[],
    ) == []
    assert _fila(repo_sqlite, 11)["codigo_partida_final"] == "03.02"


# ---- update_line_conciliacion (guardar la fila salmón) ------------- #

def _guardar(repo, vid, **campos):
    return repo.update_line_conciliacion(
        document_id=DOC, valuation_line_id=vid, **campos,
    )


def test_f051_r12_vaciar_la_partida_de_una_fila_sigrid_es_almacen(
    repo_sqlite,
):
    assert _guardar(repo_sqlite, 11, codigo_partida="") is True

    fila = _fila(repo_sqlite, 11)
    assert fila["codigo_partida_final"] is None
    assert fila["partida_action"] == "almacen_elegido"
    # Sigue Sigrid: ni derivada manual_override ni pierde su casada (D4).
    assert fila["matched_contrato_line_id"] == 501
    assert fila["derived_contrato_line_id"] is None
    assert [d["origen"] for d in _derivadas(repo_sqlite)] == [
        "missing_partida",
    ]


def test_f051_r12_vaciar_con_espacios_tambien_es_almacen(repo_sqlite):
    _guardar(repo_sqlite, 11, codigo_partida="   ")

    fila = _fila(repo_sqlite, 11)
    assert fila["codigo_partida_final"] is None
    assert fila["partida_action"] == "almacen_elegido"
    assert fila["matched_contrato_line_id"] == 501


def test_f051_r12_vaciar_la_partida_de_una_fila_nueva_es_almacen(
    repo_sqlite,
):
    _guardar(repo_sqlite, 12, codigo_partida="")

    fila = _fila(repo_sqlite, 12)
    assert fila["codigo_partida_final"] is None
    assert fila["partida_action"] == "almacen_elegido"
    assert fila["derived_contrato_line_id"] == 601
    assert _derivadas(repo_sqlite)[0]["codigo_partida"] is None


def test_f051_r12_no_enviar_la_partida_no_la_vacia(repo_sqlite):
    """``None`` = el campo no viene en la petición: la partida no cambia."""
    _guardar(repo_sqlite, 11, cantidad=3.0)

    fila = _fila(repo_sqlite, 11)
    assert fila["codigo_partida_final"] == "03.02"
    assert fila["partida_action"] == "existing_matched"


@pytest.mark.parametrize("partida", ["", None])
def test_f051_r19_guardar_otros_campos_en_almacen_no_la_vuelve_nueva(
    repo_sqlite, partida,
):
    _guardar(repo_sqlite, 13, codigo_partida=partida, cantidad=3.0,
             descuento=2.0)

    fila = _fila(repo_sqlite, 13)
    assert fila["codigo_partida_final"] is None
    assert fila["matched_contrato_line_id"] == 501
    assert fila["derived_contrato_line_id"] is None
    assert fila["cantidad_albaran"] == 3.0
    assert len(_derivadas(repo_sqlite)) == 1


def test_f051_r20_partida_igual_a_la_de_la_casada_sale_de_almacen_y_sigue_sigrid(
    repo_sqlite,
):
    _guardar(repo_sqlite, 13, codigo_partida="03.02")

    fila = _fila(repo_sqlite, 13)
    assert fila["codigo_partida_final"] == "03.02"
    assert fila["matched_contrato_line_id"] == 501
    assert fila["derived_contrato_line_id"] is None
    assert len(_derivadas(repo_sqlite)) == 1


def test_f051_r20_partida_distinta_sale_de_almacen_como_nueva(repo_sqlite):
    """Como hoy al cambiar la partida de una fila Sigrid: pasa a Nueva."""
    _guardar(repo_sqlite, 13, codigo_partida="09.09")

    fila = _fila(repo_sqlite, 13)
    assert fila["codigo_partida_final"] == "09.09"
    assert fila["matched_contrato_line_id"] is None
    derivada = _derivadas(repo_sqlite)[-1]
    assert fila["derived_contrato_line_id"] == derivada["id"]
    assert derivada == {
        "id": derivada["id"], "codigo_partida": "09.09",
        "origen": "manual_override",
    }


def test_f051_r20_cambiar_partida_real_de_sigrid_sigue_volviendola_nueva(
    repo_sqlite,
):
    """Regresión: fuera de almacén, cambiar la partida es como hoy."""
    _guardar(repo_sqlite, 11, codigo_partida="04.05")

    fila = _fila(repo_sqlite, 11)
    assert fila["codigo_partida_final"] == "04.05"
    assert fila["matched_contrato_line_id"] is None
    assert _derivadas(repo_sqlite)[-1]["origen"] == "manual_override"


# =================================================================== #
# Montaje de la ficha (R11, R17)
# =================================================================== #

def _valoracion_y_mapa(repo):
    """Carga la valoración y el mapa de conciliación de ``DOC`` con el
    código real del repositorio (los mismos pasos que la ficha)."""
    with repo._session_factory.create_session() as s:
        valoracion = repo._load_valuation_in_session(
            session=s, document_id=DOC,
        )
        mapa = repo._load_conciliation_map_in_session(
            session=s, valuation=valoracion,
        )
    return valoracion, mapa


def test_f051_r11_el_mapa_rellena_el_estado_de_partida(repo_sqlite):
    _valoracion, mapa = _valoracion_y_mapa(repo_sqlite)

    assert mapa[11].estado_partida == "partida"
    assert mapa[12].estado_partida == "partida"
    assert mapa[13].estado_partida == "almacen"


def test_f051_r11_en_almacen_no_se_pinta_la_partida_de_la_casada(
    repo_sqlite,
):
    _valoracion, mapa = _valoracion_y_mapa(repo_sqlite)
    almacen = mapa[13]

    assert almacen.codigo_partida is None
    assert almacen.descripcion_partida is None
    # Sigue siendo Sigrid y conserva el precio de su línea (D4, R15).
    assert almacen.kind == "assigned"
    assert almacen.unitario == 12.5
    # La que tiene partida, como siempre: la de su línea de contrato.
    assert mapa[11].codigo_partida == "03.02"
    assert mapa[11].descripcion_partida == "Cimentación"


def test_f051_r11_valoracion_legada_sin_marca_tambien_es_almacen(
    repo_sqlite, sesion,
):
    """D1 v4: una valoración anterior a F-051 con partida final vacía
    (``existing_matched`` o ``no_action``, sin marca de almacén) sale
    «Almacén» en cuanto se despliega sv4."""
    _linea_valoracion(sesion, id=15, merge_line_id=705,
                      matched_contrato_line_id=501,
                      codigo_partida_final="",
                      partida_action="existing_matched")
    _linea_valoracion(sesion, id=16, merge_line_id=706,
                      derived_contrato_line_id=601,
                      codigo_partida_final=None,
                      partida_action="no_action")
    sesion.commit()

    _valoracion, mapa = _valoracion_y_mapa(repo_sqlite)

    assert mapa[15].estado_partida == "almacen"
    assert mapa[15].codigo_partida is None
    assert mapa[16].estado_partida == "almacen"
    assert mapa[16].codigo_partida is None  # ni la de la derivada


def test_f051_r11_la_fila_del_detalle_no_pinta_la_partida_leida_por_ia1(
    repo_sqlite,
):
    """Tras elegir almacén, la partida que IA1 leyó (``codigo_imputacion``
    del merge) NO vuelve a salir como partida de la línea valorada."""
    from domain.models.review_models import MergeLinePayload
    from infrastructure.database.review_repository import (
        AlbaranReviewRepository,
    )

    repo_sqlite.asignar_almacen(document_id=DOC, valuation_line_ids=[11])
    valoracion, mapa = _valoracion_y_mapa(repo_sqlite)
    filas = AlbaranReviewRepository._build_display_lines(
        merge_lines=[
            MergeLinePayload(id=701, codigo_imputacion="03.02",
                             concepto="ARIDO 20/40", cantidad=2.0),
            MergeLinePayload(id=702, codigo_imputacion="04.05",
                             concepto="PORTE", cantidad=2.0),
            MergeLinePayload(id=799, codigo_imputacion="07.07",
                             concepto="SIN VALORAR", cantidad=1.0),
        ],
        valuation=valoracion,
        conciliation_by_valuation_line_id=mapa,
    )
    por_merge = {f.merge_line_id: f for f in filas if f.merge_line_id}

    assert por_merge[701].codigo_imputacion is None
    assert por_merge[701].concilia.codigo_partida is None
    assert por_merge[701].concilia.estado_partida == "almacen"
    # Con partida: como hoy, lo leído.
    assert por_merge[702].codigo_imputacion == "04.05"
    # Sin valoración: como hoy, lo leído (no es almacén: no hay valoración).
    assert por_merge[799].codigo_imputacion == "07.07"


def _detalle(repo):
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    valoracion, mapa = _valoracion_y_mapa(repo)
    doc = AlbaranDocumentMergeOrm(
        id=DOC, provider_origin="merge", source_filename="F051.pdf",
        source_mime_type="application/pdf", source_sha256="0" * 64,
        prompt_key="p", schema_name="s", model_name="m",
        raw_extraction_json="{}", created_at_utc="2026-10-05T08:00:00+00:00",
        is_active=True, approved=False,
    )
    return repo._build_merge_detail(
        merge_doc=doc, available_views=[], provider_snapshots=[],
        contratos=[], selected_contrato_codigo=None,
        valuation=valoracion, conciliation_by_valuation_line_id=mapa,
    )


def test_f051_r17_la_ficha_sirve_cuantas_lineas_tienen_partida(repo_sqlite):
    """11, 12 y 14 (sintética) tienen partida; 13 está en almacén."""
    assert _detalle(repo_sqlite).lineas_con_partida == 3


def test_f051_r17_tras_almacen_a_todas_no_queda_ninguna_con_partida(
    repo_sqlite,
):
    repo_sqlite.asignar_almacen(document_id=DOC, valuation_line_ids=None)

    assert _detalle(repo_sqlite).lineas_con_partida == 0


def test_f051_r17_sin_valoracion_es_cero():
    from domain.models.review_models import DocumentDetailPayload

    assert DocumentDetailPayload(
        id="x", source_filename="x.pdf", provider_origin="merge",
        model_name="m", created_at_utc="2026-10-05",
    ).lineas_con_partida == 0
