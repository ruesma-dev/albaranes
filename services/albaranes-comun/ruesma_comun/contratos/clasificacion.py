# ruesma_comun/contratos/clasificacion.py
"""Contrato compartido del bloque ``clasificacion`` (F-043, R7).

Es lo que IA1 devuelve SIEMPRE a nivel de DOCUMENTO al leer un albaran: a
que familia pertenece, con cuanta confianza, por que lo dice, si el albaran
mezcla familias y cuales son las secundarias.

Dos decisiones de las que depende que esto funcione:

- **Viaja dentro de ``data``, nunca en ``meta``** (R9). sv3 filtra ``meta``
  contra un modelo estricto (``ExtractionMeta`` es ``extra='forbid'``) y hoy
  descarta ``meta.tipologia``; por eso sv5 y sv6 la exigian sin recibirla.
- **``origen`` lo sella el resolver, no la IA**: ``ia1`` cuando la puso la
  fase 1, ``ia2`` cuando la fase 2 la confirmo o corrigio (R16) y ``ausente``
  cuando el envelope no traia clasificacion y hubo que registrar el hueco
  (R11). Si la IA rellena el campo, el resolver lo pisa.

``extra="ignore"`` igual que ``ContextoLinea``: que el prompt evolucione y
devuelva un campo de mas no puede invalidar la clasificacion entera.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

ORIGEN_IA1 = "ia1"
ORIGEN_IA2 = "ia2"
ORIGEN_AUSENTE = "ausente"

# Motivo que sella el resolver cuando el envelope no trae clasificacion
# (R11). No se adivina la familia: se deja constancia del hueco.
MOTIVO_SIN_CLASIFICACION = "ia_sin_clasificacion"


class ClasificacionAlbaran(BaseModel):
    """Clasificacion de DOCUMENTO decidida por la IA."""

    model_config = ConfigDict(extra="ignore")

    familia: str = Field(
        description=(
            "Id de la familia del catalogo (ruesma_comun.contratos."
            "familias). 'generico' es una respuesta legitima, no un fallo."
        ),
    )
    confianza_pct: float = Field(
        ge=0,
        le=100,
        description=(
            "Cuanta seguridad tiene la IA en la familia elegida, de 0 a 100. "
            "Es AQUI donde se expresa la duda, no eligiendo 'generico'. Por "
            "debajo del umbral configurado, sv3 manda el documento a "
            "revision."
        ),
    )
    motivo: str = Field(
        description=(
            "Por que esa familia, citando lo LEIDO en el documento (gestor "
            "autorizado, designacion del producto, codigos LER...). Es lo "
            "que permite al revisor decidir si fiarse."
        ),
    )
    mixto: bool = Field(
        default=False,
        description=(
            "True si el albaran mezcla familias con reglas distintas. "
            "Cuando lo es, las lineas sin tipo_familia propio NO heredan la "
            "del documento (R19)."
        ),
    )
    familias_secundarias: list[str] = Field(
        default_factory=list,
        description=(
            "Otras familias presentes en el albaran cuando es mixto, por "
            "orden de peso. Vacio en el caso normal."
        ),
    )
    origen: str = Field(
        default=ORIGEN_IA1,
        description=(
            "Quien puso esta clasificacion: 'ia1' (fase 1), 'ia2' (la fase 2 "
            "la corrigio) o 'ausente' (no vino ninguna y se registro el "
            "hueco). Lo sella el resolver, no la IA."
        ),
    )
