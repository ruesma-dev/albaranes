# ruesma_comun/contratos/origen_datos.py
"""Contrato compartido del bloque ``origen_datos`` (F-048, R24, R31).

Dice de DONDE sale la obra de un albaran —del correo o del papel— y como
cruzan las dos lecturas. Lo sella el resolver de sv2 sobre el documento
final (lo que ponga la IA se ignora), viaja dentro de ``data`` del envelope,
sv3 lo conserva en el merge y deriva de el dos motivos de revision, y sv4 lo
pinta. Un solo modelo para los tres: nadie copia los nombres.

Lo que NO lleva, a proposito:

- **El cuerpo ni el asunto del correo** (R24): solo la huella, si se
  recorto, los codigos leidos y una frase de evidencia de 160 caracteres
  como mucho. ``extra="ignore"`` descarta cualquier campo de texto de mas.
- **La partida** (D8, 2026-09-23: «la partida de momento no se indica en
  correo. solo obra»). F-049 anadira ``partida`` como campo opcional nuevo:
  con ``extra="ignore"`` y ``version`` es compatible en los dos sentidos.

``normalizar_codigo`` es la UNICA forma de comparar codigos de obra entre
correo, papel y lista de obras (R18, D9 «si, normaliza todo»). Primero se
pliega el Unicode con NFKC (los digitos y letras de ancho completo pasan a
ASCII); luego se pasa a mayusculas, se quita todo caracter que no sea
alfanumerico (espacios, guiones, puntos, barras...) y los ceros a la
izquierda, de modo que ``0945``, ``945``, ``09-45``, ``09.45``, `` 0945 `` y
``０９４５`` son el mismo codigo. Si no queda nada (``000``, ``--``), no hay
codigo: ``None``. No quita palabras: extraer el codigo del texto es trabajo
de IA1, nunca de una regla sobre el texto.

Efecto de NFKC que se acepta a proposito: un superindice es un digito
(``0945²`` da ``9452``). No hay regla aparte para quitarlo: si el resultado
no es una obra de la lista, R18 lo descarta y no cuenta.

Capa ``domain`` compartida: modelos y funciones puras, sin I/O.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

VERSION_ORIGEN_DATOS = 1
MAX_EVIDENCIA = 160

FUENTE_CORREO = "correo"
FUENTE_PAPEL = "papel"

# Por que la obra final es la que es. Los sella el resolver de sv2.
MOTIVO_SIN_CORREO = "sin_correo"
MOTIVO_IA_SIN_LECTURA_CORREO = "ia_sin_lectura_correo"
MOTIVO_CORREO_SIN_DATO = "correo_sin_dato"
MOTIVO_CORREO_UNICO = "correo_unico"
MOTIVO_CORREO_CONFIRMA_PAPEL = "correo_confirma_papel"
MOTIVO_CORREO_AMBIGUO = "correo_ambiguo"
MOTIVO_CORREO_FUERA_DE_LISTA = "correo_fuera_de_lista"

MOTIVOS = (
    MOTIVO_SIN_CORREO,
    MOTIVO_IA_SIN_LECTURA_CORREO,
    MOTIVO_CORREO_SIN_DATO,
    MOTIVO_CORREO_UNICO,
    MOTIVO_CORREO_CONFIRMA_PAPEL,
    MOTIVO_CORREO_AMBIGUO,
    MOTIVO_CORREO_FUERA_DE_LISTA,
)

# Motivos de REVISION que sv3 anade a ``review_reasons`` (R29, R30) y sv4
# reconoce (R34). Definidos UNA vez (R31).
MOTIVO_REVISION_OBRA_CORREO_DISTINTA = "obra_correo_distinta_papel"
MOTIVO_REVISION_OBRA_CORREO_AMBIGUA = "obra_correo_ambigua"
MOTIVOS_REVISION_ORIGEN = (
    MOTIVO_REVISION_OBRA_CORREO_DISTINTA,
    MOTIVO_REVISION_OBRA_CORREO_AMBIGUA,
)

# Derivados de las constantes para no repetir los literales: un motivo
# nuevo se anade en UN sitio (``MOTIVOS``).
Fuente = Literal[FUENTE_CORREO, FUENTE_PAPEL]  # type: ignore[valid-type]
Motivo = Literal[MOTIVOS]  # type: ignore[valid-type]

# Todo lo que no sea letra o digito (el guion bajo cuenta como \w: se quita aparte).
_NO_ALFANUMERICO = re.compile(r"[\W_]+")


def normalizar_codigo(codigo: str | None) -> str | None:
    """Forma canonica de un codigo de obra para compararlo; ``None`` si no hay codigo."""
    if codigo is None:
        return None
    plegado = unicodedata.normalize("NFKC", str(codigo))
    canonico = _NO_ALFANUMERICO.sub("", plegado.upper()).lstrip("0")
    return canonico or None


class OrigenCampo(BaseModel):
    """Origen y cruce de UN campo (hoy solo la obra)."""

    model_config = ConfigDict(extra="ignore")

    fuente: Fuente
    motivo: Motivo
    valor_final: str | None = None
    valor_correo: str | None = None
    candidatos_correo: list[str] = Field(default_factory=list)
    valor_papel: str | None = None
    discrepancia: bool = False
    validada: bool | None = None


class OrigenDatos(BaseModel):
    """De donde sale la obra del albaran y como cruzan correo y papel."""

    model_config = ConfigDict(extra="ignore")

    version: int = VERSION_ORIGEN_DATOS
    correo_presente: bool
    correo_sha256: str | None = None
    correo_truncado: bool = False
    evidencia: str | None = None
    obra: OrigenCampo

    @field_validator("evidencia", mode="before")
    @classmethod
    def _recortar_evidencia(cls, valor: object) -> object:
        if not isinstance(valor, str):
            return valor
        compacta = " ".join(valor.split())
        return compacta[:MAX_EVIDENCIA] or None

    @property
    def hay_discrepancia(self) -> bool:
        """El correo y el papel dicen obras distintas (R19): va a revision."""
        return self.obra.discrepancia
