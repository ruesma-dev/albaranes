# evals/criticidad.py
"""Criticidad de los campos comparados: qué discrepancia falla y cuál avisa.

Decisión D4 de la spec: no hay umbral porcentual de «verde». Lo que decide es
QUÉ campo discrepa. Los campos que pagan facturas —partida, cantidades,
precios, importes, códigos— hacen FALLAR el caso; los redactados —descripción,
comentarios, motivos— dejan un AVISO que consta en el informe pero no tumba
nada.

La configuración es versionada y ajustable campo a campo
(`evals/criticidad.json`): subir un campo de laxo a crítico es una línea.

Regla que sostiene R8: un campo que la configuración no clasifica NO se relaja.
Se trata como crítico y además se marca «sin clasificar» para que aparezca en
el informe; si no, olvidar una entrada sería la vía fácil para que un campo
importante dejara de fallar sin que nadie lo note.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path

from evals.modelos import Severidad

#: Configuración versionada de este repositorio.
RUTA_CRITICIDAD = Path(__file__).resolve().parent / "criticidad.json"

#: Los dos niveles declarables. `critico` → fallo; `laxo` → aviso.
NIVELES: tuple[str, ...] = ("critico", "laxo")

_SEVERIDAD_DE_NIVEL: dict[str, Severidad] = {"critico": "fallo", "laxo": "aviso"}


class ErrorCriticidad(ValueError):
    """La configuración de criticidad no se puede usar tal como está."""


@dataclass(frozen=True)
class Clasificacion:
    """Cómo quedó clasificado un campo y por qué regla."""

    campo: str
    severidad: Severidad
    clasificado: bool
    regla: str


def nombre_de_campo(campo: str) -> str:
    """Deja el nombre del campo sin el camino ni los índices que lleva.

    En el informe un campo viaja con su sitio (`lineas[2].precio_unitario_final`)
    para que se sepa dónde falló, pero su criticidad es la del campo, no la de
    la fila en la que apareció.
    """
    ultimo = campo.replace("]", "").split(".")[-1]
    return ultimo.split("[")[0].strip()


@dataclass(frozen=True)
class Criticidad:
    """Clasificador de campos ya validado, listo para usar."""

    por_defecto: str = "critico"
    criticos: frozenset[str] = field(default_factory=frozenset)
    laxos: frozenset[str] = field(default_factory=frozenset)
    patrones_criticos: tuple[str, ...] = ()
    patrones_laxos: tuple[str, ...] = ()

    def clasificar(self, campo: str) -> Clasificacion:
        """Resuelve la criticidad de un campo en el orden documentado."""
        nombre = nombre_de_campo(campo)

        if nombre in self.criticos:
            return self._clasificacion(campo, "critico", True, "ajuste 'criticos'")
        if nombre in self.laxos:
            return self._clasificacion(campo, "laxo", True, "ajuste 'laxos'")

        for patron in self.patrones_criticos:
            if fnmatchcase(nombre, patron):
                return self._clasificacion(
                    campo, "critico", True, f"patrón crítico '{patron}'"
                )
        for patron in self.patrones_laxos:
            if fnmatchcase(nombre, patron):
                return self._clasificacion(
                    campo, "laxo", True, f"patrón laxo '{patron}'"
                )

        return self._clasificacion(
            campo,
            self.por_defecto,
            False,
            f"campo sin clasificar: se aplica '{self.por_defecto}' por defecto",
        )

    def severidad(self, campo: str) -> Severidad:
        """Severidad de una discrepancia en `campo`: 'fallo' o 'aviso'."""
        return self.clasificar(campo).severidad

    @staticmethod
    def _clasificacion(
        campo: str, nivel: str, clasificado: bool, regla: str
    ) -> Clasificacion:
        return Clasificacion(
            campo=campo,
            severidad=_SEVERIDAD_DE_NIVEL[nivel],
            clasificado=clasificado,
            regla=regla,
        )


def _lista_de_textos(datos: dict, clave: str, ruta: Path) -> list[str]:
    valor = datos.get(clave, [])
    if not isinstance(valor, list) or any(not isinstance(x, str) for x in valor):
        raise ErrorCriticidad(
            f"{ruta.name}: '{clave}' debe ser una lista de textos, y es {valor!r}"
        )
    return valor


def cargar_criticidad(ruta: Path | str = RUTA_CRITICIDAD) -> Criticidad:
    """Carga y valida la configuración de criticidad.

    Falla —nunca degrada a «todo crítico» en silencio— porque una
    configuración rota que se ignora deja el informe diciendo que todo va bien
    con reglas que nadie ha revisado.
    """
    ruta = Path(ruta)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except OSError as error:
        raise ErrorCriticidad(f"no se puede leer {ruta.name}: {error}") from error
    except ValueError as error:
        raise ErrorCriticidad(f"{ruta.name} no es JSON válido: {error}") from error

    if not isinstance(datos, dict):
        raise ErrorCriticidad(f"{ruta.name}: se esperaba un objeto JSON")

    por_defecto = datos.get("por_defecto", "critico")
    if por_defecto not in NIVELES:
        raise ErrorCriticidad(
            f"{ruta.name}: 'por_defecto' debe ser uno de {list(NIVELES)}, "
            f"y es {por_defecto!r}"
        )

    criticos = _lista_de_textos(datos, "criticos", ruta)
    laxos = _lista_de_textos(datos, "laxos", ruta)
    ambos = sorted(set(criticos) & set(laxos))
    if ambos:
        raise ErrorCriticidad(
            f"{ruta.name}: hay campos declarados a la vez crítico y laxo: "
            f"{', '.join(repr(c) for c in ambos)}"
        )

    return Criticidad(
        por_defecto=por_defecto,
        criticos=frozenset(criticos),
        laxos=frozenset(laxos),
        patrones_criticos=tuple(_lista_de_textos(datos, "patrones_criticos", ruta)),
        patrones_laxos=tuple(_lista_de_textos(datos, "patrones_laxos", ruta)),
    )
