# tests/f076_sobres.py
"""Sobres y dobles compartidos por los tests de F-076 (no es una suite).

Arma ``ValuationEnvelope`` de varias líneas como los entrega sv5, una lista
de partidas de obra y un puerto falso que cuenta las consultas. Sin red ni
BBDD.
"""
from __future__ import annotations

from ruesma_comun.sigrid import ListaPartidasObra, PartidaObra

CONTRATO = "CTSU26/0313"
OBRA = "0678"


def lista_obra(*hojas: str, no_hojas: tuple[str, ...] = (), obra: str = OBRA) -> ListaPartidasObra:
    return ListaPartidasObra(
        obra=obra,
        hojas=tuple(PartidaObra(codigo=h, descripcion=f"desc {h}", descripcion_agregada=None) for h in hojas),
        no_hojas=no_hojas,
    )


#: La 0678 de T51 (simplificada): la hoja CI.4.18 y su capítulo CI.
LISTA_0678 = lista_obra("CI.4.18", "CI.03A.2", "3.02", "01.05.07", no_hojas=("CI", "03.02"))


class PuertoFalso:
    """``PartidasObraPort`` que devuelve una lista fija y cuenta las peticiones."""

    def __init__(self, lista: ListaPartidasObra | None = LISTA_0678) -> None:
        self._lista = lista
        self.pedidas: list[str | None] = []

    def lista(self, obra):
        self.pedidas.append(obra)
        return self._lista


class PuertoRoto:
    """Un puerto que (contra su contrato) lanza: el pipeline debe aguantarlo."""

    def lista(self, obra):
        raise RuntimeError("caché rota")


def linea_contrato(contrato_line_id: int, partida: str, *, descripcion="COSTES INDIRECTOS", precio=10.0,
                   unidad="UD"):
    from domain.models.valuation_envelope import ContratoLineContextDto

    return ContratoLineContextDto(
        contrato_line_id=contrato_line_id, codigo_contrato=CONTRATO, codigo_producto="MA9999",
        descripcion=descripcion, unidad_medida=unidad, precio_unitario=precio, codigo_partida=partida,
    )


def sobre(lineas, *, contrato=(), status="ok", sinteticas=()):
    """``lineas``: tuplas ``(merge_line_id, partida_leida[, matched_contrato_line_id])``.

    ``sinteticas``: tuplas ``(parent_merge_line_id, modifier_source)``.
    """
    from domain.models.valuation_envelope import (
        AlbaranLineContextDto,
        DocumentoValoracionDto,
        LineValuationDto,
        ValuationContextDto,
        ValuationEnvelope,
        ValuationEnvelopeMeta,
    )

    ia, contexto = [], []
    for i, linea in enumerate(lineas):
        merge_line_id, partida = linea[0], linea[1]
        casada = linea[2] if len(linea) > 2 else None
        ia.append(LineValuationDto(
            merge_line_id=merge_line_id, line_kind="from_albaran",
            match_method="semantic" if casada else "no_match", matched_contrato_line_id=casada,
            match_confidence_pct=90.0 if casada else 0.0, unidad_categoria_albaran="count",
            unidad_category_match=True, precio_unitario_contrato_db=10.0 if casada else None,
            precio_unitario_pdf_inferido=10.0, descripcion_linea="COSTES INDIRECTOS",
        ))
        contexto.append(AlbaranLineContextDto(
            merge_line_id=merge_line_id, line_index=i, descripcion="COSTES INDIRECTOS", unidad_medida="UD",
            unidad_categoria="count", cantidad=2.0, precio_unitario_albaran=10.0, importe_albaran=20.0,
            codigo_partida_albaran=partida,
        ))
    for parent, fuente in sinteticas:
        ia.append(LineValuationDto(
            merge_line_id=None, line_kind="synthetic_modifier", parent_merge_line_id=parent,
            modifier_source=fuente, match_method="no_match", unidad_categoria_albaran="count",
            precio_unitario_pdf_inferido=5.0, descripcion_linea="RECARGO", cantidad_override=1.0,
        ))
    return ValuationEnvelope(
        status=status,
        meta=ValuationEnvelopeMeta(document_id="doc-f076", codigo_contrato=CONTRATO, numero_albaran="A27244"),
        data=DocumentoValoracionDto(lineas=ia),
        context=ValuationContextDto(lineas_albaran=contexto, lineas_contrato=list(contrato)),
    )


def leidas(envelope) -> dict[int, str | None]:
    return {ln.merge_line_id: ln.codigo_partida_albaran for ln in envelope.context.lineas_albaran}
