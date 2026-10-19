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


#: Tope de los textos cortos que se guardan de una respuesta (modelo servido,
#: motivo de parada): nunca cabe ahí un trozo del albarán.
TOPE_TEXTO = 60

#: Tokens por unidad de precio: los precios van en USD por millón.
MILLON = Decimal(1_000_000)


class TablaInvalida(ValueError):
    """La tabla de precios no se puede usar tal como está (R2)."""


class TablaCaducada(RuntimeError):
    """Un precio pasó su `vigente_hasta` y no hay precio siguiente (R4)."""


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


# --- Uso de una respuesta (R5, R6) ------------------------------------------


@dataclass(frozen=True)
class Uso:
    """Tokens de una llamada en las cuatro clases que se facturan."""

    entrada: int
    lectura_cache: int
    escritura_cache: int
    salida: int
    incompleto: bool = False

    @property
    def entrada_total(self) -> int:
        """La entrada con la caché: lo que decide el tramo largo (R7)."""
        return self.entrada + self.lectura_cache + self.escritura_cache


def _campo(objeto: object, nombre: str) -> object:
    """Lee por atributo o por clave: los tests pasan `SimpleNamespace` o dict."""
    if isinstance(objeto, dict):
        return objeto.get(nombre)
    return getattr(objeto, nombre, None)


def _recuento(objeto: object, nombre: str, obligatorio: bool) -> tuple[int, bool]:
    """(tokens, falta). Un campo opcional ausente es 0 y no falta: la API lo
    omite cuando vale 0. Uno obligatorio ausente, o cualquiera que no sea un
    entero, es 0 y falta (R6)."""
    valor = _campo(objeto, nombre)
    if valor is None:
        return 0, obligatorio
    if isinstance(valor, bool) or not isinstance(valor, int):
        return 0, True
    return valor, False


#: Campos de uso de cada SDK: (entrada, lectura de caché, escritura de caché,
#: salida, pensamiento). `None` = el SDK no informa esa clase. El booleano dice
#: si el campo es obligatorio (ver `_recuento`).
_CAMPOS_DE_USO = {
    "claude": (
        "usage",
        ("input_tokens", True),
        ("cache_read_input_tokens", False),
        ("cache_creation_input_tokens", False),
        ("output_tokens", True),
        None,
    ),
    "openai": (
        "usage",
        ("input_tokens", True),
        ("input_tokens_details.cached_tokens", False),
        None,
        ("output_tokens", True),
        None,
    ),
    "gemini": (
        "usage_metadata",
        ("prompt_token_count", True),
        ("cached_content_token_count", False),
        None,
        ("candidates_token_count", True),
        ("thoughts_token_count", False),
    ),
}

#: Proveedores cuya entrada informada YA incluye la caché (hay que restarla).
_ENTRADA_INCLUYE_CACHE = frozenset({"openai", "gemini"})


def uso_de_respuesta(proveedor: str, respuesta: object) -> Uso:
    """Normaliza el uso del SDK de cada proveedor (R5); si falta algo, R6."""
    if proveedor not in _CAMPOS_DE_USO:
        return Uso(0, 0, 0, 0, True)
    raiz, *campos = _CAMPOS_DE_USO[proveedor]
    uso = _campo(respuesta, raiz)
    valores = []
    falta = False
    for campo in campos:
        if campo is None:
            valores.append(0)
            continue
        nombre, obligatorio = campo
        objeto = uso
        *ruta, hoja = nombre.split(".")
        for paso in ruta:
            objeto = _campo(objeto, paso)
        valor, ausente = _recuento(objeto, hoja, obligatorio)
        valores.append(valor)
        falta = falta or ausente
    entrada, lectura, escritura, salida, pensamiento = valores
    if proveedor in _ENTRADA_INCLUYE_CACHE:
        falta = falta or lectura > entrada
        entrada = max(entrada - lectura, 0)
    return Uso(entrada, lectura, escritura, salida + pensamiento, falta)


def _texto_corto(valor: object) -> str | None:
    if valor is None:
        return None
    return str(valor)[:TOPE_TEXTO]


def modelo_servido(proveedor: str, respuesta: object) -> str | None:
    """El modelo que dice la respuesta que la sirvió (R9)."""
    if proveedor in ("claude", "openai"):
        return _texto_corto(_campo(respuesta, "model"))
    if proveedor == "gemini":
        return _texto_corto(_campo(respuesta, "model_version"))
    return None


def motivo_parada(proveedor: str, respuesta: object) -> str | None:
    """Por qué dejó de generar: un `max_tokens` es un resultado, no un ruido."""
    if proveedor == "claude":
        return _texto_corto(_campo(respuesta, "stop_reason"))
    if proveedor == "openai":
        estado = _campo(respuesta, "status")
        razon = _campo(_campo(respuesta, "incomplete_details"), "reason")
        return _texto_corto(estado if razon is None else f"{estado}:{razon}")
    if proveedor == "gemini":
        candidatos = _campo(respuesta, "candidates") or []
        if not candidatos:
            return None
        motivo = _campo(candidatos[0], "finish_reason")
        return _texto_corto(getattr(motivo, "name", motivo))
    return None


# --- Precio vigente y coste (R4, R7) -----------------------------------------


def precio_vigente(modelo: Modelo, fecha: dt.date) -> Precio:
    """El precio que rige en `fecha`; `TablaCaducada` si ya no rige ninguno."""
    precio = modelo.precio
    while precio.vigente_hasta is not None and fecha > precio.vigente_hasta:
        if precio.siguiente is None:
            raise TablaCaducada(
                f"la tabla de precios está caducada: el precio de {modelo.id} rige "
                f"hasta {precio.vigente_hasta.isoformat()} y no hay precio siguiente. "
                f"Actualiza evals/precios_modelos.json. No se ha llamado a ningún LLM."
            )
        precio = precio.siguiente
    return precio


def coste_usd(modelo: Modelo, uso: Uso, fecha: dt.date) -> Decimal:
    """Cada clase de tokens por su precio; el del tramo largo si toca (R7)."""
    precio = precio_vigente(modelo, fecha)
    tramo = modelo.tramo_largo
    if tramo is not None and uso.entrada_total > tramo.umbral:
        precio = tramo.precio
    return (
        uso.entrada * precio.entrada
        + uso.lectura_cache * precio.lectura_cache
        + uso.escritura_cache * precio.escritura_cache
        + uso.salida * precio.salida
    ) / MILLON


# --- Estimación antes de gastar (R15) ----------------------------------------


@dataclass(frozen=True)
class Partida:
    """Llamadas previstas de un modelo, con la fase de la que salen sus tokens."""

    modelo: str
    etiqueta: str
    fase: str
    llamadas: int


@dataclass(frozen=True)
class LineaEstimada:
    modelo: str
    etiqueta: str
    fase: str
    llamadas: int
    entrada: int
    salida: int
    origen: str
    usd: Decimal


@dataclass(frozen=True)
class Estimacion:
    lineas: list[LineaEstimada]
    total: Decimal


def estimar(
    partidas: list[Partida],
    tabla: Tabla,
    medidos: dict[tuple[str, str], tuple[int, int]],
    fecha: dt.date,
) -> Estimacion:
    """Coste previsto: tokens medidos en una corrida anterior o, si no los hay,
    los de `estimacion_por_defecto` por su margen; todo como entrada sin caché."""
    lineas = []
    for partida in partidas:
        if (partida.fase, partida.modelo) in medidos:
            entrada, salida = medidos[(partida.fase, partida.modelo)]
            origen = "medido"
        else:
            entrada, salida, margen = tabla.por_defecto(partida.fase)
            entrada, salida = int(entrada * margen), int(salida * margen)
            origen = f"por defecto ×{margen}"
        por_llamada = coste_usd(tabla.modelo(partida.modelo), Uso(entrada, 0, 0, salida), fecha)
        lineas.append(
            LineaEstimada(
                modelo=partida.modelo,
                etiqueta=partida.etiqueta,
                fase=partida.fase,
                llamadas=partida.llamadas,
                entrada=entrada,
                salida=salida,
                origen=origen,
                usd=por_llamada * partida.llamadas,
            )
        )
    return Estimacion(lineas=lineas, total=sum((linea.usd for linea in lineas), Decimal(0)))
