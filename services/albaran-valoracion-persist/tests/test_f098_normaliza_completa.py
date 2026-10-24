# tests/test_f098_normaliza_completa.py
"""F-098 · sv6 normaliza la partida escrita en código completo (R29) y la mide (R31).

sv6 no cambia de código para R29: recibe de comun (0.9.0) el motivo ``completa``
como ``normalizada`` (``resolver_partida_obra``). Aquí se comprueba de punta a
punta con el pipeline real (builder de ``tests/f027_escenarios.py``) y una lista
de la 0686 construida desde sus filas, como la lee la caché: la lectura
``CD.99.01.64`` casa con la hoja ``99.01.64`` de CD y con la línea de contrato
de esa partida, y la final guardada es el cod (lo que sv9 manda a Sigrid).

Sin red ni BBDD: sv5, IA4 y repositorio falsos.
"""
from __future__ import annotations

from application.pipelines.run_valuation_pipeline import (
    RunValuationPipeline,
    RunValuationRequest,
)
from application.services.normalizador_partidas import NormalizadorPartidas
from ruesma_comun.sigrid import ListaPartidasObra
from tests.f027_escenarios import construir_builder
from tests.f076_sobres import PuertoFalso, linea_contrato, sobre
from tests.test_f076_pipeline import _Repositorio, _Sv5

_COLUMNAS = ["ide", "padide", "cod", "res"]

#: La 0686 de T0, recortada: CD › 99 › 99.01 › 99.01.64; CI › CI.4.18; ANT. › 98.01.
FILAS_0686 = [
    [1, 0, "ANT.", "AJUSTES ALMACÉN"],
    [2, 1, "98.01", "Anticipos"],
    [10, 0, "CD", "COSTES DIRECTOS"],
    [11, 10, "99", "VARIOS"],
    [12, 11, "99.01", "VARIOS OBRA"],
    [13, 12, "99.01.64", "Material de obra"],
    [20, 0, "CI", "COSTES INDIRECTOS"],
    [21, 20, "CI.4.18", "Costes indirectos de obra"],
]
LISTA_0686 = ListaPartidasObra.desde_filas("0686", _COLUMNAS, FILAS_0686)


def _valorar(envelope):
    repo = _Repositorio(obra="0686")
    pipeline = RunValuationPipeline(
        ia_client=_Sv5(envelope), repository=repo, builder=construir_builder(), conciliacion_client=None,
        normalizador=NormalizadorPartidas(partidas=PuertoFalso(LISTA_0686), alm_codigo_partida="ALM", activo=True),
    )
    pipeline.run(RunValuationRequest(document_id="doc-f098"))
    ((cabecera, lineas),) = repo.guardados
    return cabecera, lineas


# ------------------------------------------------------------------ #
# R29 · CD.99.01.64 ⇒ 99.01.64, casa con la línea de contrato, sin revisión
# ------------------------------------------------------------------ #
def test_f098_r29_lectura_completa_casa_con_la_linea_de_contrato_del_cod():
    envelope = sobre([(1, "CD.99.01.64", 501)], contrato=[linea_contrato(501, "99.01.64")])
    cabecera, (fila,) = _valorar(envelope)
    assert fila.partida_action == "existing_matched"
    assert fila.matched_contrato_line_id == 501
    assert fila.codigo_partida_final == "99.01.64"
    assert fila.codigo_partida_albaran == "CD.99.01.64"
    assert "partida_normalizada:CD.99.01.64>99.01.64" in fila.review_reasons
    assert fila.review_required is False
    assert cabecera.review_required is False
    assert not any(m.startswith("partida_fuera_de_lista") for m in cabecera.review_reasons)


def test_f098_r29_sin_linea_de_contrato_la_derivada_lleva_el_cod():
    envelope = sobre([(1, "cd 99.1.64")], contrato=[linea_contrato(501, "CI.4.18", descripcion="MORTERO")])
    _cabecera, (fila,) = _valorar(envelope)
    assert fila.codigo_partida_final == "99.01.64"
    assert fila.derived_contrato_line_record is not None
    assert fila.derived_contrato_line_record.codigo_partida == "99.01.64"
    assert fila.codigo_partida_albaran == "cd 99.1.64"


def test_f098_r29_subcapitulo_en_completo_no_se_normaliza():
    """``CD.99.01`` es el subcapítulo ``99.01`` de CD: a revisión, sin tocar."""
    envelope = sobre([(1, "CD.99.01")], contrato=[linea_contrato(501, "99.01.64")])
    cabecera, (fila,) = _valorar(envelope)
    assert fila.codigo_partida_final == "CD.99.01"
    assert "partida_fuera_de_lista" in fila.review_reasons
    assert cabecera.review_required is True


# ------------------------------------------------------------------ #
# R31 · la medición cuenta aparte la clase «completa»
# ------------------------------------------------------------------ #
class _LectorR31:
    """Lector falso de sigrid-api: la 0686 de T0 (``FILAS_0686``) para cualquier obra."""

    def __init__(self) -> None:
        self.obras: list[str] = []

    def __call__(self, sql, parametros, etiqueta, politica, max_rows):
        self.obras.append(parametros[0])
        return list(_COLUMNAS), [list(f) for f in FILAS_0686]


def _fila_r31(final, *, doc="doc-1", aprobado=False, leida=None):
    return {"document_id": doc, "codigo_partida_albaran": leida, "codigo_partida_final": final,
            "obra_codigo": "0686", "approved": aprobado, "review_reasons_json": None}


def _medir_r31(filas):
    from scripts import medir_f076_partidas as medir
    from tests.test_f076_medicion import _Conexion

    return medir, medir.medir(_Conexion(filas=filas), _LectorR31(), alm="ALM")


def test_f098_r31_completa_cuenta_aparte_por_estado():
    medir, resultado = _medir_r31([
        _fila_r31("CD.99.01.64", doc="8c4e026a"),
        _fila_r31("cd.99.01.64", doc="8c4e026a", aprobado=True),
        _fila_r31("99.01.64"),              # exacta
        _fila_r31("99.1.64"),               # normalizada por el cod, no por el completo
        _fila_r31("ANT.98.01", doc="d-2"),  # completa en otro capítulo
        _fila_r31("CD.99.01"),              # completo de un NO hoja: fuera de lista
    ])
    assert resultado.clases == {
        ("completa", "pendiente"): 2,
        ("completa", "aprobado"): 1,
        ("exacta", "pendiente"): 1,
        ("normalizada", "pendiente"): 1,
        ("fuera_de_lista", "pendiente"): 1,
    }
    assert resultado.completas == [
        ("8c4e026a", "pendiente", "CD.99.01.64", "99.01.64"),
        ("8c4e026a", "aprobado", "cd.99.01.64", "99.01.64"),
        ("d-2", "pendiente", "ANT.98.01", "98.01"),
    ]
    assert "completa" in medir.ETIQUETAS


def test_f098_r31_informe_solo_el_documento_y_el_par_de_las_completas():
    medir, resultado = _medir_r31([
        _fila_r31("CD.99.01.64", doc="8c4e026a"),
        _fila_r31("99.1.64", doc="otro-doc"),
        _fila_r31("CI.04.18", doc="tercero"),
    ])
    informe = medir.formatear(resultado)
    lineas = [ln.split() for ln in informe.splitlines()]
    assert ["casa", "solo", "por", "el", "código", "completo", "1", "/", "0"] in lineas
    assert ["8c4e026a", "(pendiente)", "CD.99.01.64", "→", "99.01.64"] in lineas
    # Las demás clases, solo recuentos: ni su documento ni sus códigos.
    for prohibido in ("otro-doc", "tercero", "99.1.64", "CI.04.18", "CI.4.18", "Material", "0686"):
        assert prohibido not in informe


def test_f098_r31_sin_completas_no_hay_listado():
    medir, resultado = _medir_r31([_fila_r31("99.01.64", doc="d-9")])
    informe = medir.formatear(resultado)
    assert resultado.completas == []
    assert "d-9" not in informe and "99.01.64" not in informe
    assert ["casa", "solo", "por", "el", "código", "completo", "0", "/", "0"] in [
        ln.split() for ln in informe.splitlines()]


def test_f098_r31_la_consulta_lee_el_documento_y_sigue_solo_leyendo():
    from scripts import medir_f076_partidas as medir

    sql = " ".join(medir.SQL_LINEAS.split()).upper()
    assert "D.ID AS DOCUMENT_ID" in sql
    assert sql.startswith("SELECT ") and "PRECIO" not in sql and "IMPORTE" not in sql
