# evals/barrido.py
"""Barrido de datos sensibles sobre el contenido que se va a versionar.

Es el checkpoint C3 bis aplicado dentro del conversor, no un paso manual
posterior: los fixtures entran en git y el historial de git no suelta lo que
entra. Si aparece cualquiera de estos patrones, el conversor aborta sin
escribir nada (R4).

Qué NO barre, a propósito (decisión D1 de la spec): precios, razones sociales
y CIF. Son el ground truth del eval y se versionan en un repositorio privado;
tratarlos como secretos dejaría el banco de casos sin lo único que evalúa.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Un octeto de IPv4: 0-255, sin ceros a la izquierda de más de tres cifras.
_OCTETO = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"

#: Patrones prohibidos, en el orden en que se informan. Son los de C3 bis:
#: correos, IPs, GUID de suscripción o tenant, credenciales y tokens.
PATRONES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("correo", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]*\w")),
    ("ip", re.compile(rf"\b{_OCTETO}(?:\.{_OCTETO}){{3}}\b")),
    (
        "guid",
        re.compile(
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
        ),
    ),
    (
        "credencial",
        re.compile(
            r"(?i)\b(?:password|passwd|pwd|contrase[nñ]a|secret|client[_-]?secret"
            r"|api[_-]?key|account[_-]?key|shared[_-]?access[_-]?key|token"
            r"|connection[_ -]?string)\b\s*[:=]"
        ),
    ),
    ("token", re.compile(r"\b[A-Za-z0-9_\-]{40,}\b")),
)


@dataclass(frozen=True)
class Hallazgo:
    """Un patrón prohibido encontrado, con dónde estaba y qué se encontró."""

    patron: str
    fragmento: str
    ubicacion: str = ""

    def descripcion(self) -> str:
        donde = self.ubicacion or "(sin ubicación)"
        return f"{donde}: patrón '{self.patron}' → {self.fragmento}"


def barrer(valor: object, ubicacion: str = "") -> list[Hallazgo]:
    """Busca patrones prohibidos en `valor`; lista vacía si está limpio.

    Acepta cualquier objeto porque las celdas de un Excel llegan como número,
    fecha o `None`: lo que no es texto no puede esconder un secreto, pero
    tampoco debe romper el barrido.
    """
    if not isinstance(valor, str):
        return []

    hallazgos: list[Hallazgo] = []
    for nombre, patron in PATRONES:
        for coincidencia in patron.finditer(valor):
            hallazgos.append(
                Hallazgo(
                    patron=nombre,
                    fragmento=coincidencia.group(0),
                    ubicacion=ubicacion,
                )
            )
    return hallazgos
