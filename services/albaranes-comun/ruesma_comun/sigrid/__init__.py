# ruesma_comun/sigrid/__init__.py
"""Lectura de sigrid-api compartida (F-052) y partidas de la obra (F-076, F-098).

Solo lo que es igual en todos los clientes: qué hacer con ``truncated`` y
cómo encadenar páginas ``OFFSET/FETCH``. La SQL de cada servicio NO vive
aquí (D2), con UNA excepción consciente: la lista de partidas de una obra
(:mod:`ruesma_comun.sigrid.partidas`, subconjunto aprobado de F-049 portado
por F-076), que sv4 y sv6 necesitan con la MISMA consulta y la MISMA
definición de hoja. F-098 le añade el capítulo y el código completo de cada
hoja (``CD.99.01.64`` para el cod ``99.01.64`` de CD), con qué casar una
lectura escrita en completo y cómo enseñar el cod guardado.
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
    MOTIVO_COMPLETA,
    MOTIVOS_PARTIDA,
    SQL_PARTIDAS_POR_OBRA,
    CachePartidasObra,
    CapituloObra,
    CasePartida,
    LectorSql,
    ListaPartidasObra,
    PartidaObra,
    ResolucionPartida,
    candidatas_residuos,
    casar_partida,
    codigo_completo,
    hojas_de_filas,
    leer_partidas_obra,
    misma_partida,
    mostrar_partida,
    normalizar_partida,
    partes_de_partida,
    resolver_partida_obra,
)

__all__ = [
    "MAX_FILAS_POR_PETICION",
    "MOTIVOS_PARTIDA",
    "MOTIVO_COMPLETA",
    "PAGINA_MAXIMA",
    "SQL_PARTIDAS_POR_OBRA",
    "CachePartidasObra",
    "CapituloObra",
    "CasePartida",
    "LectorSql",
    "ListaPartidasObra",
    "PartidaObra",
    "PoliticaTruncado",
    "ResolucionPartida",
    "SigridRespuestaTruncada",
    "candidatas_residuos",
    "casar_partida",
    "codigo_completo",
    "comprobar_truncado",
    "con_paginacion",
    "hojas_de_filas",
    "leer_paginado",
    "leer_partidas_obra",
    "misma_partida",
    "mostrar_partida",
    "normalizar_partida",
    "partes_de_partida",
    "resolver_partida_obra",
]
