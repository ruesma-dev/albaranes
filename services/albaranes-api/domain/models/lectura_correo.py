# domain/models/lectura_correo.py
"""Lectura del CORREO que devuelve IA1 (F-048, R15).

Es la lectura del texto del correo, separada de la del papel
(``cabecera.obra_codigo``): IA1 las hace por separado y las cruza sv2
despues, en el resolver de ``origen_datos`` (D3). Del correo SOLO la obra
(D8): aqui no hay sitio para una partida.

Opcional en ``DocumentoAlbaran`` (R17): sin el bloque, el resolver lo trata
como ``ia_sin_lectura_correo``. No llega al ``data`` final (R23): lo quita
el resolver, y de ``origen_datos`` solo sale la evidencia recortada.

Lectura tolerante (CR-C3 de la review del bloque C2): es un bloque
auxiliar y no puede tumbar la fase 1 entera. Los validadores ``before``
recortan la ``evidencia`` a 160 caracteres en el ORIGEN (R24: asi no llega
entera a ``env1``, a ``debug.phase_1_json``, a los blobs ni a la BBDD) y
aceptan codigos numericos. No se usa ``max_length``: haria fallar la
extraccion y cambiaria el schema que ve el LLM, que sigue siendo el mismo.
Quedan fuera, a proposito: un campo de mas (D8, ``extra='forbid'``) y un
``lectura_correo`` que no sea un objeto; los dos los impide el schema
estructurado (``additionalProperties: false`` y ``type: object``).
"""
from __future__ import annotations

from typing import Any

from domain.models.schema_base import StrictSchemaModel
from pydantic import Field, field_validator
from ruesma_comun.contratos.origen_datos import MAX_EVIDENCIA


def _codigo_como_texto(valor: Any) -> str | None:
    """Un codigo leido, como texto; ``None`` si no es ni texto ni numero.

    ``bool`` es ``int`` en Python y no es un codigo. Un numero entero que
    llega como ``945.0`` se escribe ``945``: con ``.0`` la normalizacion lo
    convertiria en ``9450``.
    """
    if isinstance(valor, bool):
        return None
    if isinstance(valor, str):
        return valor
    if isinstance(valor, int):
        return str(valor)
    if isinstance(valor, float):
        return str(int(valor)) if valor.is_integer() else str(valor)
    return None


class LecturaCorreo(StrictSchemaModel):
    obra_codigos: list[str] = Field(
        default_factory=list,
        description=(
            "Codigos de OBRA que se leen en el asunto o el cuerpo del "
            "correo, tal y como aparecen. Lista vacia si el correo no trae "
            "ninguno. Nunca codigos de partida ni de imputacion."
        ),
    )
    evidencia: str | None = Field(
        default=None,
        description=(
            "SOLO el fragmento corto del correo donde aparece el codigo, "
            "como mucho 160 caracteres. Null si no hay codigo."
        ),
    )

    @field_validator("obra_codigos", mode="before")
    @classmethod
    def _codigos_tolerantes(cls, valor: Any) -> list[str]:
        """Numeros a texto; lo que no es texto ni numero, fuera.

        Un valor suelto que no es lista se ENVUELVE si es un codigo (texto
        o numero: la IA dijo un codigo, aunque sin corchetes) y se descarta
        si no lo es (``None``, un objeto, un booleano ⇒ lista vacia, que el
        resolver trata como ``correo_sin_dato``).
        """
        if not isinstance(valor, list):
            valor = [valor]
        codigos = (_codigo_como_texto(v) for v in valor)
        return [c for c in codigos if c is not None]

    @field_validator("evidencia", mode="before")
    @classmethod
    def _evidencia_recortada(cls, valor: Any) -> str | None:
        """Recortada a 160 en el ORIGEN; un numero pasa a texto, lo demas es null.

        El tope es ``MAX_EVIDENCIA`` de comun, el MISMO de ``OrigenDatos``.
        """
        texto = _codigo_como_texto(valor)
        return None if texto is None else texto[:MAX_EVIDENCIA]
