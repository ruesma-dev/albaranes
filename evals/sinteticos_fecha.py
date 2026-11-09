# evals/sinteticos_fecha.py
"""Genera los albaranes sintéticos de cambio de año del juego D (F-112 · R27).

    python -m evals.sinteticos_fecha [--destino <dir>] [--json <fichero>]

Seis albaranes mínimos de un emisor ficticio («PROVEEDOR SINTETICO, S.L.»), con
una línea y la fecha del papel como ÚNICO dato variable. Cubren lo que el
banco no tiene: diciembre con correo de enero, enero con enero, diciembre con
diciembre, año legible, año de dos cifras y Nochevieja (un correo de las 23:30
UTC del 31-12 es del 01-01 en Madrid).

- Las imágenes JPG van a `evals/inputs/albaranes/SIN-00N.jpg` (ignorado por git).
- Los casos van a `evals/casos_fecha_sinteticos.json` (versionado): `caso_id`,
  `tipologia`, `papel`, `recibido_utc` y `fecha_esperada`. El comparador saca
  la referencia de `recibido_utc` con `fecha_recepcion_de` de sv2 (R1).

Determinista: texto fijo, fuente por defecto de Pillow, sin aleatoriedad ni
metadatos de fecha; dos ejecuciones dan los mismos bytes. No llama a ninguna IA.
"""

from __future__ import annotations

import argparse
import io
import json
from dataclasses import asdict, dataclass
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent
RUTA_IMAGENES = RAIZ_REPO / "evals" / "inputs" / "albaranes"
RUTA_JSON = RAIZ_REPO / "evals" / "casos_fecha_sinteticos.json"

#: Sin tildes: la fuente por defecto de Pillow no las trae (saldrían cajas).
EMISOR = "PROVEEDOR SINTETICO, S.L."
TIPOLOGIA = "generico"


@dataclass(frozen=True)
class Sintetico:
    """Un caso del juego D: lo que dice el papel, cuándo llegó y qué fecha se espera."""

    caso_id: str
    papel: str
    recibido_utc: str
    fecha_esperada: str
    tipologia: str = TIPOLOGIA


#: Los seis de R27. Las horas UTC de 1–5 dejan el mismo día en Madrid; la 6, no.
CASOS: tuple[Sintetico, ...] = (
    Sintetico("SIN-001", "28/12", "2027-01-03T08:15:00Z", "2026-12-28"),
    Sintetico("SIN-002", "02/01", "2027-01-05T08:15:00Z", "2027-01-02"),
    Sintetico("SIN-003", "15/12", "2026-12-18T08:15:00Z", "2026-12-15"),
    Sintetico("SIN-004", "28/12/2026", "2027-01-03T08:15:00Z", "2026-12-28"),
    Sintetico("SIN-005", "30/12/25", "2026-01-02T08:15:00Z", "2025-12-30"),
    Sintetico("SIN-006", "01/01", "2026-12-31T23:30:00Z", "2027-01-01"),
)

#: El albarán mínimo; `{papel}` es lo único que cambia de un caso a otro.
LINEAS = (
    EMISOR,
    "C.I.F. B00000000 - Poligono Ficticio, nave 1 - 41000 Sevilla",
    "",
    "ALBARAN DE ENTREGA        N. 0001",
    "Fecha: {papel}",
    "",
    "Cant.   Ud.   Descripcion",
    "  10    UD    SACO DE CEMENTO GRIS 25 KG",
    "",
    "Recibi conforme:",
)


def render_imagen(caso: Sintetico) -> bytes:
    """El JPG del caso: fondo blanco, texto negro, fuente por defecto de Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    fuente = ImageFont.load_default(size=30)
    imagen = Image.new("RGB", (1240, 700), "white")
    dibujo = ImageDraw.Draw(imagen)
    for indice, linea in enumerate(LINEAS):
        dibujo.text((60, 60 + indice * 56), linea.format(papel=caso.papel), fill="black", font=fuente)
    salida = io.BytesIO()
    imagen.save(salida, format="JPEG", quality=92, optimize=False, progressive=False)
    return salida.getvalue()


def render_json(casos: tuple[Sintetico, ...] = CASOS) -> str:
    """`casos_fecha_sinteticos.json`, con el mismo texto en cada ejecución."""
    datos = {
        "version": 1,
        "_descripcion": (
            "F-112 · juego D del comparador de la fecha: albaranes sintéticos de cambio de año, "
            "generados por `python -m evals.sinteticos_fecha` (imágenes en evals/inputs/albaranes/, "
            "ignorado por git). La referencia sale de `recibido_utc` con fecha_recepcion_de (Europe/Madrid)."
        ),
        "casos": [asdict(caso) for caso in casos],
    }
    return json.dumps(datos, ensure_ascii=False, indent=2) + "\n"


def generar(destino: Path = RUTA_IMAGENES, ruta_json: Path = RUTA_JSON) -> list[Path]:
    """Escribe las imágenes y el JSON; devuelve las rutas escritas."""
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    escritas = []
    for caso in CASOS:
        ruta = destino / f"{caso.caso_id}.jpg"
        ruta.write_bytes(render_imagen(caso))
        escritas.append(ruta)
    Path(ruta_json).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta_json).write_bytes(render_json().encode("utf-8"))
    escritas.append(Path(ruta_json))
    return escritas


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(
        prog="python -m evals.sinteticos_fecha",
        description="Genera los albaranes sintéticos de cambio de año del juego D (no llama a ninguna IA).",
    )
    analizador.add_argument("--destino", default=str(RUTA_IMAGENES), help="directorio de las imágenes")
    analizador.add_argument("--json", default=str(RUTA_JSON), help="fichero de los casos")
    opciones = analizador.parse_args(argv)
    for ruta in generar(Path(opciones.destino), Path(opciones.json)):
        print(f"sinteticos_fecha: {ruta}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
