# evals/modelos.py
"""Modelos puros de los evals: casos, valores esperados y resultados.

Sin dependencias externas y sin imports de `services/`: estos objetos viajan
entre el conversor, el comparador, los adaptadores de servicio (que corren en
otro proceso) y el informe, y tienen que poder serializarse a JSON tal cual.

Los dos **sentinelas** son el corazón del contrato de datos:

- `NO_COMPARAR` traduce el convenio `?` del Excel («no lo sé / me da igual»).
  Se escribe explícitamente en el fixture, nunca como ausencia de la clave:
  una clave que falta no se distingue de un descuido del conversor.
- `ESPERA_REVISION` traduce el literal `REVISIÓN` de `RESULTADO_FINAL`. No es
  un hueco del ground truth: es un resultado esperado legítimo («lo correcto
  es que el sistema no invente y lo deje para revisión humana»).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

#: Sentinela del convenio `?`: ese campo NO se compara en este caso.
NO_COMPARAR = "@@NO_COMPARAR@@"

#: Sentinela del literal `REVISIÓN`: se espera que el sistema deje el valor a
#: revisión humana en vez de inventarlo.
ESPERA_REVISION = "@@ESPERA_REVISION@@"

#: Veredictos posibles de una fase o de una pasada completa.
VERDE = "VERDE"
ROJO = "ROJO"
NO_EVALUABLE = "NO_EVALUABLE"

#: Estado de un caso concreto. `OMITIDO` no es un fallo: es «no había con qué
#: evaluarlo» (por ejemplo, falta el fichero del albarán, que no se versiona).
OMITIDO = "OMITIDO"

Severidad = Literal["fallo", "aviso"]


@dataclass(frozen=True)
class ValorEsperado:
    """Un valor del ground truth ya normalizado, con sus dos sentinelas."""

    valor: object | None = None
    comparar: bool = True
    espera_revision: bool = False

    def a_json(self) -> object | None:
        """Representación versionable: los sentinelas viajan como texto."""
        if not self.comparar:
            return NO_COMPARAR
        if self.espera_revision:
            return ESPERA_REVISION
        return self.valor

    @classmethod
    def desde_json(cls, dato: object | None) -> ValorEsperado:
        """Inverso de `a_json`: reconstruye el valor y sus sentinelas."""
        if dato == NO_COMPARAR:
            return cls(valor=None, comparar=False)
        if dato == ESPERA_REVISION:
            return cls(valor=None, espera_revision=True)
        return cls(valor=dato)


@dataclass(frozen=True)
class Caso:
    """Un caso del banco de pruebas, tal como queda en `evals/fixtures/`."""

    caso_id: str
    fase: str
    tipologia: str
    libro: str
    sha256_libro: str
    tablas: dict[str, list[dict[str, object | None]]] = field(default_factory=dict)

    def a_json(self) -> dict[str, object]:
        return {
            "caso_id": self.caso_id,
            "fase": self.fase,
            "libro": self.libro,
            "sha256_libro": self.sha256_libro,
            "tablas": self.tablas,
            "tipologia": self.tipologia,
        }

    @classmethod
    def desde_json(cls, dato: dict[str, object]) -> Caso:
        return cls(
            caso_id=str(dato["caso_id"]),
            fase=str(dato["fase"]),
            tipologia=str(dato.get("tipologia", "")),
            libro=str(dato.get("libro", "")),
            sha256_libro=str(dato.get("sha256_libro", "")),
            tablas=dict(dato.get("tablas", {})),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class Discrepancia:
    """Diferencia entre lo esperado y lo obtenido en UN campo."""

    campo: str
    esperado: object | None
    obtenido: object | None
    severidad: Severidad
    motivo: str = ""

    def descripcion(self) -> str:
        cola = f" ({self.motivo})" if self.motivo else ""
        return (
            f"{self.campo}: esperado {self.esperado!r}, "
            f"obtenido {self.obtenido!r}{cola}"
        )


@dataclass
class ResultadoCaso:
    """Veredicto de un caso: VERDE, ROJO u OMITIDO, con sus discrepancias."""

    caso_id: str
    fase: str
    estado: str = VERDE
    discrepancias: list[Discrepancia] = field(default_factory=list)
    motivo: str = ""

    @property
    def fallos(self) -> list[Discrepancia]:
        return [d for d in self.discrepancias if d.severidad == "fallo"]

    @property
    def avisos(self) -> list[Discrepancia]:
        return [d for d in self.discrepancias if d.severidad == "aviso"]

    @classmethod
    def desde_discrepancias(
        cls, caso_id: str, fase: str, discrepancias: list[Discrepancia]
    ) -> ResultadoCaso:
        """Un caso es ROJO si tiene al menos un fallo crítico; los avisos no."""
        resultado = cls(caso_id=caso_id, fase=fase, discrepancias=discrepancias)
        resultado.estado = ROJO if resultado.fallos else VERDE
        return resultado

    @classmethod
    def omitido(cls, caso_id: str, fase: str, motivo: str) -> ResultadoCaso:
        return cls(caso_id=caso_id, fase=fase, estado=OMITIDO, motivo=motivo)


@dataclass
class ResultadoFase:
    """Todos los casos de una fase (IA1…IA4) o del extremo-a-extremo."""

    nombre: str
    casos: list[ResultadoCaso] = field(default_factory=list)
    proveedores: list[str] = field(default_factory=list)
    motivo: str = ""

    @property
    def evaluados(self) -> list[ResultadoCaso]:
        return [c for c in self.casos if c.estado != OMITIDO]

    @property
    def omitidos(self) -> list[ResultadoCaso]:
        return [c for c in self.casos if c.estado == OMITIDO]

    def veredicto(self) -> str:
        """Sin casos evaluados no hay evidencia: NO_EVALUABLE, nunca VERDE."""
        if not self.evaluados:
            return NO_EVALUABLE
        if any(c.estado == ROJO for c in self.evaluados):
            return ROJO
        return VERDE


@dataclass
class ResultadoPasada:
    """Una corrida entera del runner, con todas sus fases."""

    modo: str
    fases: list[ResultadoFase] = field(default_factory=list)
    feature: str = ""
    commit: str = ""
    fecha: str = ""

    def veredicto(self) -> str:
        """ROJO manda sobre NO_EVALUABLE: un fallo detectado no se disfraza.

        Sin ninguna fase, NO_EVALUABLE: un informe vacío no es evidencia (R18).
        """
        veredictos = [fase.veredicto() for fase in self.fases]
        if ROJO in veredictos:
            return ROJO
        if not veredictos or NO_EVALUABLE in veredictos:
            return NO_EVALUABLE
        return VERDE

    def codigo_salida(self) -> int:
        """0 VERDE, 1 ROJO, 2 NO_EVALUABLE (R16)."""
        return {VERDE: 0, ROJO: 1, NO_EVALUABLE: 2}[self.veredicto()]
