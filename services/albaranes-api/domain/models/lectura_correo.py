# domain/models/lectura_correo.py
"""Lectura del CORREO que devuelve IA1 (F-048, R15).

Es la lectura del texto del correo, separada de la del papel
(``cabecera.obra_codigo``): IA1 las hace por separado y las cruza sv2
despues, en el resolver de ``origen_datos`` (D3). Del correo SOLO la obra
(D8): aqui no hay sitio para una partida.

Opcional en ``DocumentoAlbaran`` (R17): sin el bloque, el resolver lo trata
como ``ia_sin_lectura_correo``. No llega al ``data`` final (R23): lo quita
el resolver, y de ``origen_datos`` solo sale la evidencia recortada.
"""
from __future__ import annotations

from domain.models.schema_base import StrictSchemaModel
from pydantic import Field


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
