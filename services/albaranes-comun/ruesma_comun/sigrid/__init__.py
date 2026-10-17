# ruesma_comun/sigrid/__init__.py
"""Lectura de sigrid-api compartida (F-052) y partidas de la obra (F-076).

Solo lo que es igual en todos los clientes: qué hacer con ``truncated`` y
cómo encadenar páginas ``OFFSET/FETCH``. La SQL de cada servicio NO vive
aquí (D2), con UNA excepción consciente: la lista de partidas de una obra
(:mod:`ruesma_comun.sigrid.partidas`, subconjunto aprobado de F-049 portado
por F-076), que sv4 y sv6 necesitan con la MISMA consulta y la MISMA
definición de hoja.
"""
from ruesma_comun.sigrid.lectura import (
    MAX_FILAS_POR_PETICION,
    PAGINA_MAXIMA,
    PoliticaTruncado,
    SigridRespuestaTruncada,
    comprobar_truncado,
    con_paginacion,
    leer_paginado,
)
from ruesma_comun.sigrid.partidas import (
    MOTIVOS_PARTIDA,
    SQL_PARTIDAS_POR_OBRA,
    CachePartidasObra,
    CasePartida,
    LectorSql,
    ListaPartidasObra,
    PartidaObra,
    ResolucionPartida,
    casar_partida,
    hojas_de_filas,
    leer_partidas_obra,
    normalizar_partida,
    partes_de_partida,
    resolver_partida_obra,
)

__all__ = [
    "MAX_FILAS_POR_PETICION",
    "MOTIVOS_PARTIDA",
    "PAGINA_MAXIMA",
    "SQL_PARTIDAS_POR_OBRA",
    "CachePartidasObra",
    "CasePartida",
    "LectorSql",
    "ListaPartidasObra",
    "PartidaObra",
    "PoliticaTruncado",
    "ResolucionPartida",
    "SigridRespuestaTruncada",
    "casar_partida",
    "comprobar_truncado",
    "con_paginacion",
    "hojas_de_filas",
    "leer_paginado",
    "leer_partidas_obra",
    "normalizar_partida",
    "partes_de_partida",
    "resolver_partida_obra",
]
