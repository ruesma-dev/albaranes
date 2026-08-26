# domain/models/tipologia.py
"""Reexportacion del catalogo LER de `ruesma_comun` (F-036 R14).

Este modulo fue el hogar del enum `Tipologia` y de las funciones de texto
(`texto_contiene_hormigon`, `texto_contiene_mortero`) con las que el
resolver determinista de sv2 DEDUCIA la familia del albaran y, con ella,
elegia el prompt de fase 2. F-043 lo desmonto entero: la familia la decide
SIEMPRE la IA (decision del humano del 2026-08-25) y viaja en
`data.clasificacion`; el catalogo de familias vive en
`ruesma_comun.contratos.familias` y quien la consolida es
`application/services/clasificacion_resolver.py`, que no deduce nada.

Aqui queda SOLO la reexportacion del catalogo LER: lo consumen sv2 y sv6
(las lineas de INCREMENTO por LER del contrato, en `residuos_incrementos` y
`modifier_contract_matcher`), y sv6 no puede importar el dominio de sv2.
Cero logica duplicada: si algo del catalogo hay que tocar, se toca en
comun. El LER identifica un RESIDUO en una linea; lo que ya NO hace es
clasificar el documento.
"""
from __future__ import annotations

from ruesma_comun.ler import (
    es_ler_valido,
    normalizar_ler,
    texto_contiene_ler,
)

__all__ = [
    "es_ler_valido",
    "normalizar_ler",
    "texto_contiene_ler",
]
