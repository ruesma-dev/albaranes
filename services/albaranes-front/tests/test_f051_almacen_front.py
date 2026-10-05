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


# =================================================================== #
# Servicio: una entrada de deshacer por acción (R18)
# =================================================================== #

class _RepoEspia:
    """Doble del repositorio: guarda lo que el servicio le pide."""

    def __init__(self, tocadas):
        self.tocadas = tocadas
        self.asignaciones: list[dict] = []
        self.deshacer: list[dict] = []

    def snapshot_row(self, *, table, row_id):
        return {"table": table, "values": {"id": row_id, "estado": "antes"}}

    def snapshot_lineas_valoracion(self, *, document_id):
        return [
            {"table": "albaran_line_valuations",
             "values": {"id": vid, "estado": "antes"}}
            for vid in (11, 12, 13, 14)
        ]

    def asignar_almacen(self, *, document_id, valuation_line_ids):
        self.asignaciones.append(
            {"document_id": document_id, "ids": valuation_line_ids},
        )
        return list(self.tocadas)

    def record_undo(self, **kwargs):
        self.deshacer.append(kwargs)

    def doc_label(self, *, document_id):
        return "alb F051"

    def line_brief(self, *, valuation_line_id):
        return {"codigo_partida_final": "03.02", "descripcion_linea": "ARIDO"}


def _servicio(repo):
    from application.services.review_service import ReviewService

    return ReviewService(repo, None)


def test_f051_r18_almacen_en_una_linea_deja_una_entrada_de_deshacer():
    repo = _RepoEspia(tocadas=[11])

    assert _servicio(repo).asignar_almacen_linea(
        document_id=DOC, valuation_line_id=11,
    ) is True

    assert repo.asignaciones == [{"document_id": DOC, "ids": [11]}]
    assert len(repo.deshacer) == 1
    entrada = repo.deshacer[0]
    assert entrada["action"] == "almacen"
    assert entrada["document_id"] == DOC
    assert entrada["restore"] == [
        {"table": "albaran_line_valuations",
         "values": {"id": 11, "estado": "antes"}},
    ]
    assert "Almacén" in entrada["description"]


def test_f051_r18_almacen_a_todas_deja_una_sola_entrada_con_todas(
):
    repo = _RepoEspia(tocadas=[11, 12, 13, 14])

    assert _servicio(repo).asignar_almacen_todas(document_id=DOC) == 4

    assert repo.asignaciones == [{"document_id": DOC, "ids": None}]
    assert len(repo.deshacer) == 1
    entrada = repo.deshacer[0]
    assert entrada["action"] == "almacen"
    assert [s["values"]["id"] for s in entrada["restore"]] == [
        11, 12, 13, 14,
    ]


def test_f051_r18_solo_se_guardan_las_lineas_que_se_tocaron():
    repo = _RepoEspia(tocadas=[12, 14])

    assert _servicio(repo).asignar_almacen_todas(document_id=DOC) == 2

    assert [s["values"]["id"] for s in repo.deshacer[0]["restore"]] == [
        12, 14,
    ]


@pytest.mark.parametrize("accion", ["linea", "todas"])
def test_f051_r18_si_no_toca_nada_no_hay_entrada_de_deshacer(accion):
    repo = _RepoEspia(tocadas=[])
    servicio = _servicio(repo)

    if accion == "linea":
        resultado = servicio.asignar_almacen_linea(
            document_id=DOC, valuation_line_id=21,
        )
        assert resultado is False
    else:
        assert servicio.asignar_almacen_todas(document_id=DOC) == 0
    assert repo.deshacer == []


def test_f051_r18_el_snapshot_restaura_las_lineas_tocadas(repo_sqlite):
    """El formato del snapshot es el que ``undo_last`` sabe restaurar."""
    antes = {vid: _fila(repo_sqlite, vid) for vid in (11, 12, 13, 14)}
    instantaneas = repo_sqlite.snapshot_lineas_valoracion(document_id=DOC)
    assert [s["values"]["id"] for s in instantaneas] == [11, 12, 13, 14]

    repo_sqlite.asignar_almacen(document_id=DOC, valuation_line_ids=None)
    with repo_sqlite._session_factory.create_session() as s:
        for instantanea in instantaneas:
            repo_sqlite._undo_apply_restore(s, instantanea)
        s.commit()

    for vid in (11, 12, 13, 14):
        assert _fila(repo_sqlite, vid) == antes[vid]


def test_f051_r18_snapshot_de_un_documento_sin_valoracion_es_vacio(
    repo_sqlite,
):
    assert repo_sqlite.snapshot_lineas_valoracion(document_id="no") == []


# =================================================================== #
# API: los dos POST nuevos (404 si no toca nada, R23)
# =================================================================== #

class _ServicioApi:
    def __init__(self, *, linea=True, todas=3):
        self.linea = linea
        self.todas = todas
        self.llamadas: list[tuple] = []

    def initialize(self):
        return True

    def asignar_almacen_linea(self, *, document_id, valuation_line_id):
        self.llamadas.append(("linea", document_id, valuation_line_id))
        return self.linea

    def asignar_almacen_todas(self, *, document_id):
        self.llamadas.append(("todas", document_id))
        return self.todas


def _cliente(monkeypatch, servicio):
    from fastapi.testclient import TestClient

    from config.settings import Settings
    from interface_adapters.web import app as modulo_app

    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(
        modulo_app, "AlbaranReviewRepository", lambda *_: object(),
    )
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    return TestClient(modulo_app.build_app(ajustes))


def test_f051_endpoint_almacen_de_una_linea(monkeypatch):
    servicio = _ServicioApi(linea=True)
    respuesta = _cliente(monkeypatch, servicio).post(
        f"/api/documents/{DOC}/lines/11/almacen",
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["ok"] is True
    assert servicio.llamadas == [("linea", DOC, 11)]


def test_f051_endpoint_linea_ajena_da_404(monkeypatch):
    servicio = _ServicioApi(linea=False)
    respuesta = _cliente(monkeypatch, servicio).post(
        f"/api/documents/{DOC}/lines/21/almacen",
    )

    assert respuesta.status_code == 404


def test_f051_endpoint_almacen_a_todas(monkeypatch):
    servicio = _ServicioApi(todas=4)
    respuesta = _cliente(monkeypatch, servicio).post(
        f"/api/documents/{DOC}/almacen-todas",
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json() == {"ok": True, "document_id": DOC, "lineas": 4}
    assert servicio.llamadas == [("todas", DOC)]


def test_f051_endpoint_almacen_a_todas_sin_lineas_da_404(monkeypatch):
    respuesta = _cliente(monkeypatch, _ServicioApi(todas=0)).post(
        f"/api/documents/{DOC}/almacen-todas",
    )

    assert respuesta.status_code == 404


# =================================================================== #
# Plantilla real (R11, R22) y JS servido (R13, R17)
# =================================================================== #

import re as _re

_ALMACEN = {"codigo_partida": None, "descripcion_partida": None,
            "estado_partida": "almacen"}


def _input_partida(html):
    encontrado = _re.search(r"<input[^>]*js-partida-combo[^>]*>", html)
    assert encontrado, "no hay input de partida en la fila salmón"
    return encontrado.group(0)


def test_f051_r11_plantilla_celda_editable_en_almacen(
    render_detalle, documento_detalle, fila_detalle, linea_valorada,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(codigo_partida_final=None)],
        display=[fila_detalle(conciliacion=_ALMACEN,
                              codigo_imputacion="03.02")],
    ))
    entrada = _input_partida(html)

    assert 'value=""' in entrada
    assert 'placeholder="Almacén"' in entrada
    assert "partida-almacen" in entrada
    assert 'data-valuation-line-id="900"' in entrada
    assert "03.02" not in entrada


def test_f051_r11_plantilla_celda_editable_con_partida(
    render_detalle, documento_detalle, fila_detalle, linea_valorada,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(codigo_partida_final="01.01")],
        display=[fila_detalle(conciliacion={"estado_partida": "partida"})],
    ))
    entrada = _input_partida(html)

    assert 'value="01.01"' in entrada
    assert "partida-almacen" not in entrada


def test_f051_r11_plantilla_celda_de_solo_lectura_en_almacen(
    render_detalle, documento_detalle, fila_detalle, linea_valorada,
):
    """Fila sin ``valuation_line_id``: no editable, texto «Almacén»."""
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(codigo_partida_final=None)],
        display=[fila_detalle(conciliacion=_ALMACEN,
                              valuation_line_id=None)],
    ))
    celda = _re.search(
        r'<td class="concilia-td" data-col="partida".*?</td>', html, _re.S,
    ).group(0)

    assert "js-partida-combo" not in celda
    assert "Almacén" in celda
    assert "partida-almacen" in celda


def _documento_lectura(documento_detalle, linea_valorada, final):
    from domain.models.review_models import MergeLinePayload

    documento = documento_detalle(
        lineas_valoracion=(
            [linea_valorada(codigo_partida_final=final)]
            if final is not False else []
        ),
        is_editable=False,
    )
    documento.view_mode = "openai"
    documento.lines = [
        MergeLinePayload(id=500, codigo_imputacion="03.02",
                         concepto="RETIRADA CONTENEDOR RCD", cantidad=6.0),
    ]
    return documento


def _celda_imputacion_lectura(html):
    fila = _re.search(
        r"<td>1</td>\s*<td>(.*?)</td>\s*<td>RETIRADA", html, _re.S,
    )
    assert fila, "no se encuentra la tabla de líneas de solo lectura"
    return fila.group(1).strip()


@pytest.mark.parametrize("final", [None, "", "  "])
def test_f051_r11_tabla_de_lineas_valoradas_dice_almacen(
    render_detalle, documento_detalle, linea_valorada, final,
):
    html = render_detalle(
        _documento_lectura(documento_detalle, linea_valorada, final),
    )

    assert _celda_imputacion_lectura(html) == "Almacén"


def test_f051_r11_tabla_de_lineas_valoradas_con_partida_la_pinta(
    render_detalle, documento_detalle, linea_valorada,
):
    html = render_detalle(
        _documento_lectura(documento_detalle, linea_valorada, "04.05"),
    )

    assert _celda_imputacion_lectura(html) == "04.05"


def test_f051_r11_tabla_sin_valoracion_pinta_lo_leido(
    render_detalle, documento_detalle, linea_valorada,
):
    html = render_detalle(
        _documento_lectura(documento_detalle, linea_valorada, False),
    )

    assert _celda_imputacion_lectura(html) == "03.02"


def test_f051_plantilla_nunca_dice_sin_partida(
    render_detalle, documento_detalle, fila_detalle, linea_valorada,
):
    """D1 v4: no existe un estado «Sin partida» distinto de almacén."""
    editable = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(codigo_partida_final=None)],
        display=[fila_detalle(conciliacion=_ALMACEN)],
    ))
    lectura = render_detalle(
        _documento_lectura(documento_detalle, linea_valorada, None),
    )

    for html in (editable, lectura):
        assert "Sin partida" not in html
        assert "sin_partida" not in html


def _boton_todas(html):
    return _re.search(r"<button[^>]*id=\"almacen-todas-btn\"[^>]*>", html)


def test_f051_r22_boton_todas_con_el_recuento(
    render_detalle, documento_detalle, fila_detalle, linea_valorada,
):
    documento = documento_detalle(
        lineas_valoracion=[linea_valorada(codigo_partida_final="01.01")],
        display=[fila_detalle()],
    )
    documento.lineas_con_partida = 3
    boton = _boton_todas(render_detalle(documento))

    assert boton, "falta el botón «Almacén a todas las líneas»"
    assert 'data-con-partida="3"' in boton.group(0)


def test_f051_r22_sin_valoracion_no_hay_boton(
    render_detalle, documento_detalle,
):
    assert _boton_todas(render_detalle(documento_detalle())) is None


def test_f051_r22_vista_no_editable_no_ofrece_ni_boton_ni_combo(
    render_detalle, documento_detalle, linea_valorada,
):
    html = render_detalle(
        _documento_lectura(documento_detalle, linea_valorada, "01.01"),
    )

    assert _boton_todas(html) is None
    assert "js-partida-combo" not in html


def _app_js():
    from pathlib import Path

    return (
        Path(__file__).resolve().parents[1] / "static" / "app.js"
    ).read_text(encoding="utf-8")


def test_f051_r13_el_combo_de_partida_ofrece_almacen_primero():
    js = _app_js()

    assert "Almacén (sin partida)" in js
    # Solo en el combo de PARTIDA (no en el de concepto) y como primer
    # ítem fijo, fuera del filtro por texto.
    assert 'classList.contains("js-partida-combo")' in js
    assert _re.search(r"shown\s*=\s*\[ITEM_ALMACEN\]\.concat\(", js)


def test_f051_r13_elegir_almacen_llama_al_post_de_la_linea():
    js = _app_js()

    assert "/almacen`" in js
    assert 'method: "POST"' in js


def test_f051_r17_el_boton_todas_confirma_con_el_recuento_y_recarga():
    js = _app_js()

    bloque = js[js.index('getElementById("almacen-todas-btn")'):]
    bloque = bloque[:bloque.index("window.location.reload()") + 30]
    assert "dataset.conPartida" in bloque
    assert "window.confirm(" in bloque
    assert "/almacen-todas`" in bloque


def test_f051_r12_guardar_la_fila_envia_la_partida_vaciada():
    """Vaciar la partida y «Guardar» envía ``""`` (elegir almacén, R12),
    no ``null`` (que el backend trata como «no viene»)."""
    js = _app_js()

    assert 'field === "codigo_partida"' in js


def test_f051_r17_sin_valoracion_el_repositorio_cuenta_cero():
    """Superviviente 1 de la campaña de mutación (``return 0`` -> 1): el
    recuento que el repositorio sirve sin valoración es 0, no el valor
    por defecto del payload."""
    from infrastructure.database.review_repository import (
        AlbaranReviewRepository,
    )

    assert AlbaranReviewRepository._lineas_con_partida(None) == 0


# =================================================================== #
# Review, pasada 2 · decisión del humano (2026-10-05): fuera de almacén
# el input de partida pinta la partida FINAL de la línea, no la de la
# línea de contrato casada (origen del hallazgo H2).
# =================================================================== #

def _casada_sin_partida(sesion):
    from sqlalchemy import text

    sesion.execute(text(
        "INSERT INTO albaran_contrato_lines_merge (id, codigo_contrato, "
        "codigo_partida, descripcion_partida, descripcion_linea, "
        "unidad_medida, precio_unitario) VALUES "
        "(502, 'CTSU25/0051', NULL, NULL, 'PORTE', 'UD', 30.0)"
    ))


def test_f051_p2_fuera_de_almacen_se_pinta_la_partida_final(
    repo_sqlite, sesion,
):
    """Complementaria que hereda 07.07 (R7, excepción c) casada con una
    línea de contrato de 03.02, otra casada con una línea SIN partida y
    una Nueva cuya derivada tiene otra partida: el input pinta la final."""
    _casada_sin_partida(sesion)
    _linea_valoracion(sesion, id=17, merge_line_id=707,
                      matched_contrato_line_id=501,
                      codigo_partida_final="07.07",
                      partida_action="inherited_from_base_line")
    _linea_valoracion(sesion, id=18, merge_line_id=708,
                      matched_contrato_line_id=502,
                      codigo_partida_final="03.02",
                      partida_action="inherited_from_base_line")
    _linea_valoracion(sesion, id=19, merge_line_id=709,
                      derived_contrato_line_id=601,
                      codigo_partida_final="08.08",
                      partida_action="new_line_created")
    sesion.commit()

    _valoracion, mapa = _valoracion_y_mapa(repo_sqlite)

    assert mapa[17].codigo_partida == "07.07"
    assert mapa[18].codigo_partida == "03.02"
    assert mapa[19].codigo_partida == "08.08"
    # La descripción de la casada es de OTRA partida: no se pinta.
    assert mapa[17].descripcion_partida is None
    # Siguen siendo lo que eran (Sigrid / Nueva) y con partida.
    assert (mapa[17].kind, mapa[18].kind, mapa[19].kind) == (
        "assigned", "assigned", "derived",
    )
    assert {mapa[v].estado_partida for v in (17, 18, 19)} == {"partida"}


def test_f051_p2_si_la_final_es_la_de_la_casada_nada_cambia(repo_sqlite):
    _valoracion, mapa = _valoracion_y_mapa(repo_sqlite)

    assert mapa[11].codigo_partida == "03.02"
    assert mapa[11].descripcion_partida == "Cimentación"
    assert mapa[12].codigo_partida == "04.05"


def test_f051_p2_la_partida_de_la_casada_se_conserva_aparte(
    repo_sqlite, sesion,
):
    """Para el aviso «pasará a NUEVA» (O2) y para los avisos ✓/⚠ contra
    el contrato: la de la casada, también en almacén (no se pinta)."""
    _linea_valoracion(sesion, id=17, merge_line_id=707,
                      matched_contrato_line_id=501,
                      codigo_partida_final="07.07")
    sesion.commit()

    _valoracion, mapa = _valoracion_y_mapa(repo_sqlite)

    assert mapa[17].codigo_partida_casada == "03.02"
    assert mapa[13].codigo_partida is None
    assert mapa[13].codigo_partida_casada == "03.02"


def test_f051_p2_el_input_de_la_ficha_lleva_la_partida_final(
    repo_sqlite, sesion, render_detalle, documento_detalle, fila_detalle,
    linea_valorada,
):
    """Del mapa real al HTML: el ``value`` inicial del input (el que H2
    usa para saber si el revisor lo cambió) es la partida final."""
    _linea_valoracion(sesion, id=17, merge_line_id=707,
                      matched_contrato_line_id=501,
                      codigo_partida_final="07.07")
    sesion.commit()
    _valoracion, mapa = _valoracion_y_mapa(repo_sqlite)

    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(codigo_partida_final="07.07")],
        display=[fila_detalle(conciliacion=mapa[17].model_dump())],
    ))
    entrada = _input_partida(html)

    assert 'value="07.07"' in entrada
    assert "partida-almacen" not in entrada


def test_f051_p2_el_aviso_de_partida_sigue_comparando_con_el_contrato(
    repo_sqlite, sesion,
):
    """Los ✓/⚠ comparan lo leído del albarán con la partida del
    CONTRATO (la de la casada), como antes; en almacén, sin aviso."""
    from domain.models.review_models import MergeLinePayload
    from infrastructure.database.review_repository import (
        AlbaranReviewRepository,
    )

    _linea_valoracion(sesion, id=17, merge_line_id=707,
                      matched_contrato_line_id=501,
                      codigo_partida_final="07.07")
    sesion.commit()
    valoracion, mapa = _valoracion_y_mapa(repo_sqlite)
    filas = AlbaranReviewRepository._build_display_lines(
        merge_lines=[
            MergeLinePayload(id=701, codigo_imputacion="03.02",
                             concepto="ARIDO 20/40", cantidad=2.0),
            MergeLinePayload(id=703, codigo_imputacion="03.02",
                             concepto="ARIDO 20/40", cantidad=2.0),
            MergeLinePayload(id=707, codigo_imputacion="07.07",
                             concepto="PORTE", cantidad=1.0),
        ],
        valuation=valoracion,
        conciliation_by_valuation_line_id=mapa,
    )
    por_merge = {f.merge_line_id: f for f in filas if f.merge_line_id}

    assert por_merge[701].concilia.agree_partida is True
    assert por_merge[707].concilia.agree_partida is False
    assert por_merge[703].concilia.agree_partida is None
