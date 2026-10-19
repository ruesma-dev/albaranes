# evals/costes.py
"""Precios, uso y coste de las llamadas a los LLM (F-083).

Puro: sin red, sin SDK y sin imports de servicios. Lo usan el comparador de
modelos (`evals/comparar_modelos.py`), que estima antes de gastar, y el medidor
(`evals/procesos/medidor.py`), que mide lo gastado llamada a llamada.

La tabla `evals/precios_modelos.json` está versionada: cada precio lleva su
fuente oficial y la fecha en que se consultó. Una entrada a la que le falte
algo no se carga (R2): un coste calculado con un precio inventado parece una
cifra y no lo es.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

#: La tabla versionada.
RUTA_PRECIOS = Path(__file__).resolve().parent / "precios_modelos.json"

PROVEEDORES = ("claude", "gemini", "openai")
PAPELES = ("referencia", "candidato", "excluido")
FASES = ("IA1", "IA2", "IA3", "IA4")
CLASES_DE_PRECIO = ("entrada", "lectura_cache", "escritura_cache", "salida")


class TablaInvalida(ValueError):
    """La tabla de precios no se puede usar tal como está (R2)."""


@dataclass(frozen=True)
class Precio:
    """USD por millón de tokens de cada clase, con su vigencia."""

    entrada: Decimal
    lectura_cache: Decimal
    escritura_cache: Decimal
    salida: Decimal
    vigente_hasta: dt.date | None = None
    siguiente: Precio | None = None


@dataclass(frozen=True)
class TramoLargo:
    """Precios cuando la entrada total supera `umbral` tokens."""

    umbral: int
    precio: Precio


@dataclass(frozen=True)
class Modelo:
    id: str
    proveedor: str
    precio: Precio
    fuente: str
    fecha_consulta: dt.date
    imagen: bool | None
    pdf: bool | None
    herramienta_forzada: bool | None
    papel: str
    motivo: str = ""
    tramo_largo: TramoLargo | None = None


@dataclass(frozen=True)
class Tabla:
    modelos: dict[str, Modelo]
    referencias: dict[str, str]
    estimacion: dict[str, tuple[int, int, Decimal]]

    def modelo(self, modelo_id: str) -> Modelo:
        """El modelo por su id de API; `KeyError` si no está en la tabla."""
        return self.modelos[modelo_id]

    def referencia(self, fase: str) -> str:
        """El modelo que la fase usa hoy en producción."""
        return self.referencias[fase]

    def por_defecto(self, fase: str) -> tuple[int, int, Decimal]:
        """Tokens de entrada y salida supuestos por llamada, y su margen."""
        return self.estimacion[fase]

    def validos(self) -> list[str]:
        """Los modelos que se pueden pedir: todos menos los excluidos (R13)."""
        return [m.id for m in self.modelos.values() if m.papel != "excluido"]


# --- Carga y validación (R1, R2) ---------------------------------------------


def cargar_tabla(ruta: Path | str = RUTA_PRECIOS) -> Tabla:
    """Lee y valida la tabla; `TablaInvalida` nombra el modelo y el campo."""
    try:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"), parse_float=Decimal)
    except json.JSONDecodeError as error:
        raise TablaInvalida(f"{ruta}: no es JSON válido ({error})") from error

    modelos: dict[str, Modelo] = {}
    for crudo in datos.get("modelos", []):
        modelo = _modelo(crudo)
        if modelo.id in modelos:
            raise TablaInvalida(f"modelo {modelo.id}: id repetido en la tabla")
        modelos[modelo.id] = modelo

    referencias = dict(datos.get("referencias") or {})
    estimacion = {}
    crudas = datos.get("estimacion_por_defecto") or {}
    for fase in FASES:
        referencia = referencias.get(fase)
        if referencia not in modelos or modelos[referencia].papel == "excluido":
            raise TablaInvalida(
                f"referencias.{fase}: {referencia} no es un modelo válido de la tabla"
            )
        if fase not in crudas:
            raise TablaInvalida(f"estimacion_por_defecto: falta la fase {fase}")
        cruda = crudas[fase]
        estimacion[fase] = (
            int(cruda["entrada"]),
            int(cruda["salida"]),
            _decimal(cruda, "margen", f"estimacion_por_defecto.{fase}"),
        )
    return Tabla(modelos=modelos, referencias=referencias, estimacion=estimacion)


def _modelo(crudo: dict) -> Modelo:
    modelo_id = str(crudo.get("id") or "").strip()
    if not modelo_id:
        raise TablaInvalida("hay un modelo sin id")
    donde = f"modelo {modelo_id}"

    for campo in ("fuente", "fecha_consulta", "imagen", "pdf", "proveedor", "papel"):
        if campo not in crudo or (isinstance(crudo[campo], str) and not crudo[campo].strip()):
            raise TablaInvalida(f"{donde}: falta el campo {campo}")
    if crudo["proveedor"] not in PROVEEDORES:
        raise TablaInvalida(f"{donde}: proveedor {crudo['proveedor']!r} no es {PROVEEDORES}")
    if crudo["papel"] not in PAPELES:
        raise TablaInvalida(f"{donde}: papel {crudo['papel']!r} no es {PAPELES}")
    motivo = str(crudo.get("motivo") or "").strip()
    if crudo["papel"] == "excluido" and not motivo:
        raise TablaInvalida(f"{donde}: un modelo excluido necesita su motivo")
    herramienta = crudo.get("herramienta_forzada")
    if crudo["proveedor"] == "claude" and not isinstance(herramienta, bool):
        raise TablaInvalida(f"{donde}: herramienta_forzada tiene que ser true o false en Claude")

    tramo = None
    if crudo.get("tramo_largo") is not None:
        tramo_crudo = crudo["tramo_largo"]
        tramo = TramoLargo(
            umbral=int(tramo_crudo["umbral_entrada"]),
            precio=_precio(tramo_crudo.get("precio") or {}, f"{donde}: tramo_largo"),
        )
    return Modelo(
        id=modelo_id,
        proveedor=crudo["proveedor"],
        precio=_precio(crudo.get("precio") or {}, donde),
        fuente=crudo["fuente"].strip(),
        fecha_consulta=_fecha(crudo["fecha_consulta"], f"{donde}: fecha_consulta"),
        imagen=crudo["imagen"],
        pdf=crudo["pdf"],
        herramienta_forzada=herramienta,
        papel=crudo["papel"],
        motivo=motivo,
        tramo_largo=tramo,
    )


def _precio(crudo: dict, donde: str) -> Precio:
    valores = {clase: _decimal(crudo, clase, donde) for clase in CLASES_DE_PRECIO}
    siguiente = None
    if crudo.get("siguiente") is not None:
        siguiente = _precio(crudo["siguiente"], f"{donde}: siguiente")
    vigente_hasta = None
    if crudo.get("vigente_hasta") is not None:
        vigente_hasta = _fecha(crudo["vigente_hasta"], f"{donde}: vigente_hasta")
    return Precio(**valores, vigente_hasta=vigente_hasta, siguiente=siguiente)


def _decimal(crudo: dict, campo: str, donde: str) -> Decimal:
    if campo not in crudo:
        raise TablaInvalida(f"{donde}: falta el precio {campo}")
    try:
        valor = Decimal(str(crudo[campo]))
    except InvalidOperation as error:
        raise TablaInvalida(f"{donde}: {campo} no es un número") from error
    if valor < 0:
        raise TablaInvalida(f"{donde}: {campo} es negativo ({valor})")
    return valor


def _fecha(texto: object, donde: str) -> dt.date:
    try:
        return dt.date.fromisoformat(str(texto))
    except ValueError as error:
        raise TablaInvalida(f"{donde}: {texto!r} no es una fecha AAAA-MM-DD") from error
