# tests/test_f043_contexto_clasificacion.py
"""F-043 · sv5 lee la clasificacion, elige prompt con ella y la reenvia.

Tres tareas en un fichero, separadas por la palabra que las selecciona
(``tasks.md`` lo verifica con ``-k``):

* **T18 · ``select``** — el SELECT de la cabecera trae las seis columnas
  que sv3 persiste (R22) y el repositorio las monta en
  ``ContextoValoracion.clasificacion`` (R23).
* **T19 · ``prompt``** — el prompt de valoracion sale del CATALOGO a
  partir de la familia del DOCUMENTO (R24), con caida al generico
  configurado cuando esa clave no esta registrada (R15/R27).
* **T20 · ``envelope``** — la clasificacion viaja dentro de ``context``
  en el sobre que consume sv6 (R23).

Regla 3 de ``docs/ARCHITECTURE.md``: sv5 lee con SQL crudo, asi que
este SELECT es un LECTOR ACOPLADO de las tablas de sv3. Por eso el SQL
no se copia: se importa del modulo de produccion y se ejecuta TAL CUAL
contra SQLite en memoria (fichero temporal, sin red ni PostgreSQL).

Sin red, sin BBDD real y sin LLM (R33): los proveedores son dobles que
devuelven un objeto fijo.
"""
from __future__ import annotations

import json
import logging

import pytest
from sqlalchemy import create_engine, text

from application.services.valuation_extraction_service import (
    ProviderClientSpec,
    ValuationExtractionService,
)
from domain.models.valuation_context import ContextoValoracion
from domain.ports.prompt_repository import PromptSpec
from infrastructure.database.session_factory import SessionFactory
from infrastructure.database.sqlalchemy_valuation_context_repository import (
    _SQL_MERGE_HEADER,
    SqlAlchemyValuationContextRepository,
)
from ruesma_comun.contratos import ClasificacionAlbaran

_DOCUMENTO = "doc-f043"
_CONTRATO = "CTSU24/0228"


# =================================================================== #
# Tablas de sv3 reducidas a lo que este servicio lee. Anadir columnas
# que el SELECT no toca no probaria nada.
# =================================================================== #

_DDL = (
    """
    CREATE TABLE albaran_documents_merge (
        id                          TEXT PRIMARY KEY,
        proveedor_cif               TEXT,
        proveedor_nombre            TEXT,
        obra_codigo                 TEXT,
        obra_nombre                 TEXT,
        selected_contrato_codigo    TEXT,
        fecha                       TEXT,
        numero_albaran              TEXT,
        tipologia                   TEXT,
        tipologia_confianza_pct     REAL,
        tipologia_motivo            TEXT,
        tipologia_origen            TEXT,
        tipologia_mixta             BOOLEAN,
        tipologia_secundarias_json  TEXT
    )
    """,
    """
    CREATE TABLE albaran_lines_merge (
        id                  INTEGER PRIMARY KEY,
        document_id         TEXT,
        line_index          INTEGER,
        codigo              TEXT,
        concepto            TEXT,
        unidad_medida       TEXT,
        cantidad            REAL,
        precio              REAL,
        precio_neto         REAL,
        descuento           REAL,
        codigo_imputacion   TEXT,
        contexto_linea_json TEXT
    )
    """,
    """
    CREATE TABLE albaran_contratos_merge (
        id                            INTEGER PRIMARY KEY,
        codigo_contrato               TEXT,
        nombre_contrato               TEXT,
        cif_proveedor                 TEXT,
        nombre_proveedor              TEXT,
        codigo_obra                   TEXT,
        nombre_obra                   TEXT,
        pdf_sharepoint_relative_path  TEXT,
        pdf_sharepoint_web_url        TEXT,
        md_sharepoint_relative_path   TEXT
    )
    """,
    """
    CREATE TABLE albaran_contrato_lines_merge (
        id                INTEGER PRIMARY KEY,
        contrato_id       INTEGER,
        linea             INTEGER,
        codigo_contrato   TEXT,
        codigo_producto   TEXT,
        descripcion_linea TEXT,
        unidad_medida     TEXT,
        precio_unitario   REAL,
        codigo_partida    TEXT
    )
    """,
)

#: Lo que sv3 escribe en el merge para el caso SS-0003967 (R22).
CLASIFICACION_RESIDUOS = {
    "tipologia": "residuos",
    "tipologia_confianza_pct": 92.0,
    "tipologia_motivo": (
        "gestor autorizado de RCD, codigo LER 170604 y contenedor de 6 m3"
    ),
    "tipologia_origen": "ia2",
    "tipologia_mixta": False,
    "tipologia_secundarias_json": "[]",
}

#: El mismo documento ANTES de F-043: las seis columnas a NULL.
SIN_CLASIFICACION = {clave: None for clave in CLASIFICACION_RESIDUOS}


def _crear_bbdd(ruta, *, columnas_clasificacion: dict) -> str:
    """Monta la BBDD de un albaran con contrato y una linea."""
    url = f"sqlite:///{ruta}"
    engine = create_engine(url)
    try:
        with engine.begin() as conexion:
            for ddl in _DDL:
                conexion.execute(text(ddl))
            conexion.execute(
                text(
                    "INSERT INTO albaran_documents_merge ("
                    " id, proveedor_cif, proveedor_nombre, obra_codigo,"
                    " obra_nombre, selected_contrato_codigo, fecha,"
                    " numero_albaran, tipologia, tipologia_confianza_pct,"
                    " tipologia_motivo, tipologia_origen, tipologia_mixta,"
                    " tipologia_secundarias_json"
                    ") VALUES ("
                    " :id, :cif, :prov, :obra, :obra_n, :contrato, :fecha,"
                    " :numero, :tipologia, :tipologia_confianza_pct,"
                    " :tipologia_motivo, :tipologia_origen, :tipologia_mixta,"
                    " :tipologia_secundarias_json)"
                ),
                {
                    "id": _DOCUMENTO,
                    "cif": "B82899550",
                    "prov": "SALMEDINA",
                    "obra": "0687",
                    "obra_n": "OBRA 687",
                    "contrato": _CONTRATO,
                    "fecha": "2024-07-10",
                    "numero": "SS-0003967",
                    **columnas_clasificacion,
                },
            )
            conexion.execute(
                text(
                    "INSERT INTO albaran_lines_merge ("
                    " id, document_id, line_index, concepto, unidad_medida,"
                    " cantidad, precio) VALUES ("
                    " 1, :doc, 1, 'RETIRADA MATERIALES DE AISLAMIENTO',"
                    " 'M3', 6.0, NULL)"
                ),
                {"doc": _DOCUMENTO},
            )
            conexion.execute(
                text(
                    "INSERT INTO albaran_contratos_merge ("
                    " id, codigo_contrato, nombre_contrato, cif_proveedor"
                    ") VALUES (1, :contrato, 'SALMEDINA', 'B82899550')"
                ),
                {"contrato": _CONTRATO},
            )
            conexion.execute(
                text(
                    "INSERT INTO albaran_contrato_lines_merge ("
                    " id, contrato_id, linea, codigo_contrato,"
                    " descripcion_linea, unidad_medida, precio_unitario"
                    ") VALUES (1, 1, 1, :contrato,"
                    " 'CAMBIO CONTENEDOR 6M3', 'UD', 120.0)"
                ),
                {"contrato": _CONTRATO},
            )
    finally:
        engine.dispose()
    return url


@pytest.fixture
def bbdd_con_clasificacion(tmp_path):
    return _crear_bbdd(
        tmp_path / "con.db",
        columnas_clasificacion=CLASIFICACION_RESIDUOS,
    )


@pytest.fixture
def bbdd_sin_clasificacion(tmp_path):
    return _crear_bbdd(
        tmp_path / "sin.db",
        columnas_clasificacion=SIN_CLASIFICACION,
    )


def _cargar(url: str):
    repo = SqlAlchemyValuationContextRepository(SessionFactory(url))
    return repo.load_context(document_id=_DOCUMENTO)


# =================================================================== #
# T18 · el SELECT del contexto (R23)
# =================================================================== #

def test_f043_r23_el_select_de_cabecera_trae_las_seis_columnas(
    bbdd_con_clasificacion,
):
    """Las seis columnas de sv3 (R22) salen del SQL de produccion.

    Se ejecuta ``_SQL_MERGE_HEADER`` tal cual, sin copiarlo: si sv3
    renombra una columna, este test es el aviso que la regla 3 de
    ARCHITECTURE promete al lector acoplado.
    """
    engine = create_engine(bbdd_con_clasificacion)
    try:
        with engine.begin() as conexion:
            fila = conexion.execute(
                _SQL_MERGE_HEADER, {"document_id": _DOCUMENTO}
            ).mappings().first()
    finally:
        engine.dispose()

    assert fila is not None
    for columna, valor in CLASIFICACION_RESIDUOS.items():
        assert fila[columna] == valor, columna


def test_f043_r23_el_select_monta_la_clasificacion_en_el_contexto(
    bbdd_con_clasificacion,
):
    """``ContextoValoracion.clasificacion`` sale de esas seis columnas."""
    raw = _cargar(bbdd_con_clasificacion)

    assert raw.clasificacion is not None
    assert raw.clasificacion.familia == "residuos"
    assert raw.clasificacion.confianza_pct == pytest.approx(92.0)
    assert "LER 170604" in raw.clasificacion.motivo
    assert raw.clasificacion.origen == "ia2"
    assert raw.clasificacion.mixto is False
    assert raw.clasificacion.familias_secundarias == []


def test_f043_r23_el_select_recompone_las_secundarias_y_el_mixto(
    tmp_path,
):
    """El JSON de secundarias vuelve a ser lista, y ``mixta`` bool.

    sv3 las escribe con ``json.dumps`` en una columna TEXT
    (``campos_clasificacion_merge``); si sv5 no deshiciera ese dumps,
    ``familias_secundarias`` llegaria como la cadena ``'["hormigon"]'``
    y sv6 heredaria familia en un albaran MIXTO, que es justo lo que
    R19 prohibe.
    """
    url = _crear_bbdd(
        tmp_path / "mixto.db",
        columnas_clasificacion={
            **CLASIFICACION_RESIDUOS,
            "tipologia_mixta": True,
            "tipologia_secundarias_json": json.dumps(
                ["hormigon", "generico"], ensure_ascii=False,
            ),
        },
    )
    raw = _cargar(url)

    assert raw.clasificacion is not None
    assert raw.clasificacion.mixto is True
    assert raw.clasificacion.familias_secundarias == ["hormigon", "generico"]


def test_f043_r27_el_select_sin_clasificacion_la_deja_en_none(
    bbdd_sin_clasificacion,
):
    """Documento anterior a F-043: columnas NULL, clasificacion ``None``.

    Es la mitad sv5 de R27. ``None`` —y no un ``generico`` inventado—
    es lo que hace que ``familia_efectiva`` devuelva ``None`` en sv6 y
    el albaran se comporte EXACTAMENTE como hoy.
    """
    raw = _cargar(bbdd_sin_clasificacion)

    assert raw.clasificacion is None


def test_f043_r10_el_select_no_reinterpreta_una_familia_fuera_de_catalogo(
    tmp_path,
):
    """sv5 entrega lo que sv3 persistio; no reclasifica ni corrige.

    Normalizar la familia es trabajo del resolver de sv2 (R10). Si sv5
    lo repitiera habria DOS criterios y volveriamos al lazo cerrado que
    F-043 desmonta.
    """
    url = _crear_bbdd(
        tmp_path / "rara.db",
        columnas_clasificacion={
            **CLASIFICACION_RESIDUOS,
            "tipologia": "chatarra",
        },
    )
    raw = _cargar(url)

    assert raw.clasificacion is not None
    assert raw.clasificacion.familia == "chatarra"


# =================================================================== #
# T19 · el prompt de valoracion sale del catalogo (R24, R15, R27)
# =================================================================== #

class _PromptRepoDoble:
    """Indice de prompts con las claves que quiera cada test."""

    def __init__(self, claves: tuple[str, ...]) -> None:
        self._claves = set(claves)
        self.pedidos: list[str] = []

    def has(self, prompt_key: str) -> bool:
        return prompt_key in self._claves

    def get(self, prompt_key: str) -> PromptSpec:
        self.pedidos.append(prompt_key)
        return PromptSpec(
            system=f"system::{prompt_key}",
            task=f"task::{prompt_key}",
            schema_hint="",
            schema="documento_valoracion",
        )


class _SchemaRegistryDoble:
    def get(self, schema_name: str):
        from domain.models.valuation_models import DocumentoValoracion

        return DocumentoValoracion


class _LlmDoble:
    """Cliente LLM que no llama a nadie: devuelve un documento vacio."""

    def extract_document(self, **_kwargs):
        from domain.models.valuation_models import DocumentoValoracion

        return DocumentoValoracion(lineas=[])


def _contexto(clasificacion, *, lineas=()) -> ContextoValoracion:
    return ContextoValoracion(
        document_id=_DOCUMENTO,
        codigo_contrato=_CONTRATO,
        nombre_contrato="SALMEDINA",
        cif_proveedor="B82899550",
        nombre_proveedor="SALMEDINA",
        codigo_obra="0687",
        nombre_obra="OBRA 687",
        pdf_relative_path=None,
        pdf_filename=None,
        lineas_albaran=list(lineas),
        lineas_contrato=[],
        fecha_albaran="2024-07-10",
        numero_albaran="SS-0003967",
        clasificacion=clasificacion,
    )


def _servicio(claves: tuple[str, ...]) -> tuple:
    repo = _PromptRepoDoble(claves)
    servicio = ValuationExtractionService(
        providers=[
            ProviderClientSpec(
                provider="claude",
                model_name="modelo-de-prueba",
                client=_LlmDoble(),
            )
        ],
        prompt_repo=repo,
        schema_registry=_SchemaRegistryDoble(),
        prompt_key="valuation_es",
    )
    return servicio, repo


CLAVES_REALES = ("valuation_es", "valuation_residuos")


def test_f043_r24_el_prompt_sale_del_catalogo_por_la_familia_del_documento():
    """Familia ``residuos`` -> ``valuation_residuos``, sin mirar lineas."""
    servicio, repo = _servicio(CLAVES_REALES)

    resultados = servicio.extract(
        context=_contexto(
            ClasificacionAlbaran(
                familia="residuos",
                confianza_pct=92.0,
                motivo="gestor autorizado",
            )
        ),
        pdf_attachment=None,
    )

    assert repo.pedidos == ["valuation_residuos"]
    assert resultados["claude"].prompt_key == "valuation_residuos"


@pytest.mark.parametrize("familia", ["generico", "hormigon", "mortero"])
def test_f043_r24_una_familia_sin_prompt_propio_usa_el_prompt_generico(
    familia,
):
    """Solo ``residuos`` tiene prompt de valoracion propio hoy.

    El catalogo lo dice (``prompt_valoracion=None`` en las otras tres) y
    esto lo fija: ``valuation_mortero`` lo creara F-023, y hasta
    entonces mortero se valora con el generico, no con el de hormigon.
    """
    servicio, repo = _servicio(CLAVES_REALES)

    servicio.extract(
        context=_contexto(
            ClasificacionAlbaran(
                familia=familia, confianza_pct=80.0, motivo="lo dice la IA",
            )
        ),
        pdf_attachment=None,
    )

    assert repo.pedidos == ["valuation_es"]


def test_f043_r15_si_la_clave_del_catalogo_no_esta_registrada_el_prompt_cae(
    caplog,
):
    """Catalogo con clave que el YAML aun no tiene: cae y lo deja en log.

    Es la red de R15/R3: anadir una familia al catalogo antes que su
    prompt no puede reventar la valoracion, pero tampoco puede pasar
    en silencio.
    """
    servicio, repo = _servicio(("valuation_es",))

    with caplog.at_level(logging.WARNING):
        servicio.extract(
            context=_contexto(
                ClasificacionAlbaran(
                    familia="residuos",
                    confianza_pct=92.0,
                    motivo="gestor autorizado",
                )
            ),
            pdf_attachment=None,
        )

    assert repo.pedidos == ["valuation_es"]
    assert "valuation_residuos" in caplog.text


def test_f043_r27_sin_clasificacion_el_prompt_es_el_generico_configurado():
    """Sobre anterior a F-043: el prompt es el que ya venia configurado."""
    servicio, repo = _servicio(CLAVES_REALES)

    servicio.extract(context=_contexto(None), pdf_attachment=None)

    assert repo.pedidos == ["valuation_es"]


def test_f043_r24_el_prompt_ya_no_se_deriva_de_la_familia_de_las_lineas():
    """La familia de las LINEAS ya no elige el prompt del DOCUMENTO.

    ``_derivar_tipologia_valoracion`` agregaba las
    ``contexto_linea.tipo_familia`` para deducir la tipologia del
    albaran. R24 la retira: la clasificacion es propiedad del DOCUMENTO
    (R17) y quien la decide es IA1. Con lineas de residuos pero sin
    clasificacion de documento, el prompt es el generico.
    """
    from domain.models.contexto_linea import ContextoLinea
    from domain.models.valuation_context import AlbaranLineForValuation

    linea = AlbaranLineForValuation(
        merge_line_id=700,
        line_index=1,
        codigo=None,
        descripcion="RETIRADA MATERIALES DE AISLAMIENTO",
        unidad_medida="M3",
        unidad_categoria="volume",
        cantidad=6.0,
        precio_unitario_albaran=None,
        importe_albaran=None,
        codigo_partida_albaran="32.01",
        contexto_linea=ContextoLinea(
            tipo_familia="residuos", rol_linea="base", codigo_ler="170604",
        ),
    )
    servicio, repo = _servicio(CLAVES_REALES)

    servicio.extract(
        context=_contexto(None, lineas=(linea,)), pdf_attachment=None,
    )

    assert repo.pedidos == ["valuation_es"]


def test_f043_r24_el_prompt_ya_no_tiene_derivacion_propia_de_tipologia():
    """El decisor viejo no queda ahi "por si acaso" (R12, R24).

    Un modulo puede dejar de llamarse y seguir invitando a volver a
    usarse. Se comprueba por AUSENCIA del simbolo, que es lo unico que
    no se puede saltar sin darse cuenta.
    """
    from application.services import valuation_extraction_service as modulo

    assert not hasattr(modulo, "_derivar_tipologia_valoracion")


# =================================================================== #
# T20 · la clasificacion viaja en el ``context`` del sobre (R23)
# =================================================================== #

class _DescargaDoble:
    def download_markdown_by_relative_path(self, *, relative_path):
        return None

    def download_by_relative_path(self, *, relative_path):
        return None


def _pipeline(url: str):
    from application.pipelines.value_albaran_pipeline import (
        ValueAlbaranPipeline,
    )
    from application.services.unit_category_prefilter import (
        UnitCategoryPrefilter,
    )

    servicio, _repo = _servicio(CLAVES_REALES)
    return ValueAlbaranPipeline(
        context_repository=SqlAlchemyValuationContextRepository(
            SessionFactory(url)
        ),
        pdf_downloader=_DescargaDoble(),
        prefilter=UnitCategoryPrefilter(),
        extraction_service=servicio,
        max_pdf_mb=10,
        service_version="test",
    )


def _envelope(url: str) -> dict:
    from application.pipelines.value_albaran_pipeline import ValueAlbaranRequest

    return _pipeline(url).run(ValueAlbaranRequest(document_id=_DOCUMENTO))


def test_f043_r23_el_envelope_hacia_sv6_lleva_la_clasificacion(
    bbdd_con_clasificacion,
):
    """``context.clasificacion``: el sitio del que sv6 la lee (T21).

    Va en ``context`` y no en ``meta`` por la misma razon que en sv2 iba
    en ``data``: los modelos estrictos de la otra punta descartan lo que
    no declaran, y asi es como se perdio ``meta.tipologia`` (R9).
    """
    envelope = _envelope(bbdd_con_clasificacion)

    clasificacion = envelope["context"]["clasificacion"]
    assert clasificacion["familia"] == "residuos"
    assert clasificacion["confianza_pct"] == pytest.approx(92.0)
    assert clasificacion["origen"] == "ia2"
    assert clasificacion["mixto"] is False
    assert clasificacion["familias_secundarias"] == []


def test_f043_r27_el_envelope_sin_clasificacion_la_deja_en_none(
    bbdd_sin_clasificacion,
):
    """Sobre de un documento anterior a F-043: ``clasificacion`` a None."""
    envelope = _envelope(bbdd_sin_clasificacion)

    assert envelope["context"]["clasificacion"] is None


def test_f043_r23_el_envelope_no_contract_tambien_lleva_la_clasificacion(
    tmp_path,
):
    """Sin contrato no hay IA, pero la clasificacion no se pierde.

    sv6 persiste igualmente ese sobre; si la clasificacion faltara solo
    en esta rama, el mismo albaran quedaria clasificado o no segun si
    tenia contrato seleccionado.
    """
    url = _crear_bbdd(
        tmp_path / "sin_contrato.db",
        columnas_clasificacion=CLASIFICACION_RESIDUOS,
    )
    engine = create_engine(url)
    try:
        with engine.begin() as conexion:
            conexion.execute(
                text(
                    "UPDATE albaran_documents_merge"
                    " SET selected_contrato_codigo = NULL"
                )
            )
    finally:
        engine.dispose()

    envelope = _envelope(url)

    assert envelope["status"] == "no_contract"
    assert envelope["context"]["clasificacion"]["familia"] == "residuos"


# =================================================================== #
# El `DocumentoAlbaran` propio de sv5 (aviso heredado del bloque A)
# =================================================================== #

def test_f043_r8_el_documento_de_sv5_acepta_el_bloque_clasificacion():
    """El ``DocumentoAlbaran`` de sv5 declara ``clasificacion`` (R8).

    sv5 tiene su PROPIA copia de los schemas de fase 1 y fase 2
    (``domain/models/albaran_models.py``, ``revision_models.py``), hoy
    sin registrar en el ``SchemaRegistry`` — ver el test siguiente. Es
    ``extra='forbid'``: sin declarar el campo, el dia que alguien la
    registre rechazaria el documento entero. Es exactamente como murio
    ``meta.tipologia`` en ``ExtractionMeta``, y no se deja el mismo
    cepo montado dos veces.
    """
    from domain.models.albaran_models import DocumentoAlbaran

    documento = DocumentoAlbaran.model_validate(
        {
            "cabecera": {"numero_albaran": "SS-0003967"},
            "lineas": [],
            "clasificacion": {
                "familia": "residuos",
                "confianza_pct": 92.0,
                "motivo": "gestor autorizado de RCD",
            },
        }
    )

    assert documento.clasificacion is not None
    assert documento.clasificacion.familia == "residuos"


def test_f043_r8_sv5_no_valida_hoy_documentos_de_fase_1_ni_de_fase_2():
    """Por que ese campo no cambia nada HOY, escrito como test.

    sv5 solo sirve dos schemas —valoracion y conciliacion— y lee el
    albaran con SQL crudo: ningun documento de fase 1 o 2 pasa por sus
    modelos. Si algun dia se registran ahi, este test cae y obliga a
    mirar si la copia debe seguir viva o reexportarse de sv2.
    """
    from application.services.schema_registry import SchemaRegistry

    registro = SchemaRegistry()

    assert set(registro._schemas) == {
        "documento_valoracion",
        "documento_conciliacion",
    }


# =================================================================== #
# Las ramas defensivas del lector de secundarias
# =================================================================== #

@pytest.mark.parametrize(
    ("guardado", "esperado"),
    [
        (None, []),
        ("[]", []),
        ('["hormigon"]', ["hormigon"]),
        (["mortero"], ["mortero"]),
        ("esto no es json", []),
        ('"hormigon"', []),
        ("{}", []),
    ],
    ids=[
        "null", "vacia", "json-lista", "ya-es-lista",
        "json-corrupto", "json-que-no-es-lista", "json-objeto",
    ],
)
def test_f043_r23_el_select_lee_las_secundarias_sin_romperse(
    guardado, esperado,
):
    """Un campo informativo no puede tumbar la clasificacion entera.

    sv3 escribe esta columna con ``json.dumps`` y **no normaliza** las
    familias secundarias contra el catalogo: puede llegar cualquier
    cosa. Las ramas defensivas se prueban una a una porque son
    precisamente las que nadie ejecuta hasta el dia que hacen falta;
    mismo criterio con el que sv3 recorta ``tipologia`` a VARCHAR(32).
    """
    from infrastructure.database import (
        sqlalchemy_valuation_context_repository as repositorio,
    )

    _lista_json = repositorio._lista_json

    assert _lista_json(guardado) == esperado
