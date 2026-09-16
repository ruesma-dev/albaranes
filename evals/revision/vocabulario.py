# evals/revision/vocabulario.py
"""Traduce lo que el humano escribe en el Excel al vocabulario de los libros.

La tabla vive en `vocabulario.json`, no aquí (D1): se corrige sin tocar código.
Este módulo solo la lee y la aplica.

**Lo que no reconoce, aborta** (R5). No es rigidez: el humano escribe las
etiquetas a mano, y una etiqueta nueva que cayera en `generico` por descuido
sembraría ground truth falso —los casos saldrían VERDES contra una familia
equivocada— sin que nadie lo notara. Abortar obliga a decidir; adivinar, no.
Los abortos se ACUMULAN y se listan juntos con su fila: corregir el Excel una
vez por cada valor desconocido es la diferencia entre una tarde y un minuto.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

#: El fichero de datos vive junto a este módulo y se versiona.
RUTA_VOCABULARIO = Path(__file__).resolve().parent / "vocabulario.json"

_NO_ALFANUMERICO = re.compile(r"[^0-9A-Z]+")


class ErrorVocabulario(RuntimeError):
    """Un valor del Excel que el vocabulario versionado no reconoce (R5)."""

    def __init__(self, desconocidos: list[tuple[str, str, int]]) -> None:
        self.desconocidos = desconocidos
        detalle = "\n".join(
            f"  - fila {fila}, columna '{columna}': {valor!r}"
            for columna, valor, fila in desconocidos
        )
        super().__init__(
            f"El vocabulario no reconoce {len(desconocidos)} valor(es) y no se "
            f"ha escrito nada. Añádelos a evals/revision/vocabulario.json o "
            f"corrige el Excel:\n{detalle}"
        )


def normalizar(texto: object | None) -> str:
    """Mayúsculas sin acentos y un solo espacio entre trozos alfanuméricos.

    `CONTRATO "PAPEL"` y `DEDUCIDO. INCREM. CAMBIO AÑO` se cotejan así contra
    entradas legibles del JSON, sin una entrada por cada signo de puntuación.
    """
    if texto is None:
        return ""
    descompuesto = unicodedata.normalize("NFKD", str(texto).upper())
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return _NO_ALFANUMERICO.sub(" ", sin_acentos).strip()


@dataclass(frozen=True)
class DestinoEtiqueta:
    """A dónde manda una etiqueta del Excel: familia, pestaña y prefijo."""

    etiqueta: str
    familia_documento: str
    pestana: str
    prefijo: str
    familia_linea: str | None
    #: La familia ya existe en el catálogo de `ruesma_comun`. Si no, el caso se
    #: escribe igual, nace ROJO a propósito y el informe lo agrupa aparte (R6).
    en_catalogo: bool


@dataclass(frozen=True)
class OrigenPrecio:
    """De dónde sale un precio o un importe, y si viene impreso en el papel."""

    precio_source: str
    impreso: bool


class Vocabulario:
    """El fichero de datos ya cargado, con sus tres ejes de traducción."""

    def __init__(self, datos: dict) -> None:
        self._datos = datos
        self.politica_vacios: dict[str, str] = datos["politica_vacios"]
        self.familias_vigentes: tuple[str, ...] = tuple(
            datos["familias_documento_vigentes"]
        )
        self.unidades_conteo: frozenset[str] = frozenset(
            normalizar(u) for u in datos["unidades_conteo"]
        )
        self.minimo_residuos: float = float(datos["minimo_facturable_residuos"])
        self.criterios_residuos: dict[str, dict] = datos["criterios_residuos"]
        self.deducidas_por_concepto: dict = datos["deducidas_por_concepto"]
        self.sinonimos_concepto: dict[str, str] = datos["sinonimos_concepto"]
        self.factor_descuento: float = float(datos["descuento_factor_porcentaje"])
        self._etiquetas = {
            normalizar(nombre): (nombre, destino)
            for nombre, destino in datos["etiquetas"].items()
        }
        self._prefijos = datos["prefijos_pestana"]
        #: Abortos acumulados: se listan todos juntos al final (R5).
        self.desconocidos: list[tuple[str, str, int]] = []

    # --- Etiqueta -> familia de documento + pestaña (R6) --------------------

    def etiqueta(self, valor: object | None, fila: int) -> DestinoEtiqueta:
        clave = normalizar(valor)
        encontrado = self._etiquetas.get(clave)
        if encontrado is None:
            self._abortar("tipo_albaran", valor, fila)
        nombre, destino = encontrado
        pestana = destino["pestana"]
        familia = destino["familia_documento"]
        return DestinoEtiqueta(
            etiqueta=nombre,
            familia_documento=familia,
            pestana=pestana,
            prefijo=self._prefijos[pestana],
            familia_linea=destino["familia_linea"],
            en_catalogo=familia in self.familias_vigentes,
        )

    # --- Los tres ejes de origen -------------------------------------------

    def origen_linea(self, valor: object | None, fila: int) -> str:
        return self._canonico("origen_linea", valor, fila)["canonico"]

    def origen_contrato(self, valor: object | None, fila: int) -> str:
        return self._canonico("origen_contrato", valor, fila)["canonico"]

    def origen_precio(self, valor: object | None, fila: int) -> OrigenPrecio:
        entrada = self._canonico("origen_precio", valor, fila)
        return OrigenPrecio(
            precio_source=entrada["precio_source"], impreso=bool(entrada["impreso"])
        )

    # --- Política de vacíos por columna (R11, R12) -------------------------

    def politica_vacio(self, columna: str) -> str:
        """Qué significa una celda vacía en esa columna. Sin declaración, `?`."""
        return self.politica_vacios.get(columna, "interrogante")

    def concepto_es_deducido(self, familia: str, concepto: object | None) -> bool:
        """El concepto describe algo que se DEDUCE del contrato, no que se lee.

        En residuos, el incremento por LER no está impreso: sale de mirar el
        contrato con el código LER de la línea de material (decisión del humano
        del 2026-09-16). El Excel las marca las dos `EN ALBARAN` porque
        describe el albarán, no las fases.
        """
        regla = self.deducidas_por_concepto
        if familia not in regla["familias"]:
            return False
        texto = normalizar(concepto)
        return any(normalizar(marca) in texto for marca in regla["marcas"])

    def es_unidad_de_conteo(self, unidad: object | None) -> bool:
        """UD y sus variantes. Lo demás se pesa o se mide (design §5 ter)."""
        return normalizar(unidad) in self.unidades_conteo

    # --- Motor de cotejo ----------------------------------------------------

    def _canonico(self, eje: str, valor: object | None, fila: int) -> dict:
        clave = normalizar(valor)
        entradas = self._datos[eje]
        for entrada in entradas:
            if clave in (normalizar(e) for e in entrada["exactos"]):
                return entrada
        # Los prefijos se prueban del más largo al más corto: si dos entradas
        # solapan, gana la más específica y no el orden del JSON.
        candidatos = sorted(
            (
                (normalizar(prefijo), entrada)
                for entrada in entradas
                for prefijo in entrada["prefijos"]
            ),
            key=lambda par: len(par[0]),
            reverse=True,
        )
        for prefijo, entrada in candidatos:
            if clave.startswith(f"{prefijo} ") or clave == prefijo:
                return entrada
        self._abortar(eje, valor, fila)

    def _abortar(self, columna: str, valor: object | None, fila: int) -> None:
        """Acumula el desconocido y corta ESTA fila; el resto sigue leyéndose."""
        registro = (columna, "" if valor is None else str(valor).strip(), fila)
        if registro not in self.desconocidos:
            self.desconocidos.append(registro)
        raise ErrorVocabulario([registro])

    def comprobar(self) -> None:
        """Lanza UNA vez con todo lo desconocido acumulado (R5)."""
        if self.desconocidos:
            raise ErrorVocabulario(list(self.desconocidos))


def cargar(ruta: Path | str = RUTA_VOCABULARIO) -> Vocabulario:
    """Lee el fichero de datos versionado."""
    return Vocabulario(json.loads(Path(ruta).read_text(encoding="utf-8")))
