# evals/revision/albaranes.py
"""El puente entre el documento de papel, la fila del Excel y el caso.

Convenio del humano (2026-09-15): del **nombre del fichero** sale el **código
de albarán** —el que él escribe en cada fila del Excel— y de ahí el
`caso_id`. Si el nombre sin extensión trae `_`, el código es lo de después del
último; si no, el nombre entero.

    PROVEEDOR_SS-0003967.pdf ─┐
                              ├─ SS-0003967 ─ RES-004 ─ RES-004.pdf
    SS-0003967.png ───────────┘

**Manda el código del papel, nunca el persistido.** El precedente es
`SS-0801977` leído donde el papel decía `SS-0001977`: si el emparejado se
fiase de lo que el sistema guardó, el caso se casaría con la fila equivocada y
el eval compararía un albarán contra el ground truth de otro.

Y **los cuatro fallos que la regla no cubre salen listados uno a uno** (R21):
ruidoso, nunca silencioso. Una importación que se traga 57 de 59 albaranes sin
decir cuáles faltan es peor que no importar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from evals.revision.reparto import normalizar_codigo

#: Formatos de entrada admitidos. La rama de imágenes de sv2 es de julio de
#: 2026 y hoy no la mide nadie; un original en PNG es un caso legítimo.
EXTENSIONES: tuple[str, ...] = (".pdf", ".png", ".jpg", ".jpeg")

#: Sufijo del gemelo de imagen de un caso que también existe en PDF (R22).
SUFIJO_IMAGEN = "-IMG"


def codigo_desde_nombre(nombre: str) -> str:
    """`PROVEEDOR_SS-0003967.pdf` → `SS-0003967`; `SS-0003967.png` → igual."""
    tronco = Path(nombre).stem.strip()
    return tronco.rsplit("_", 1)[-1].strip() if "_" in tronco else tronco


def formato_de(nombre: str) -> str:
    """`pdf` o `imagen`: es lo que distingue a un caso de su gemelo (R23)."""
    return "pdf" if Path(nombre).suffix.lower() == ".pdf" else "imagen"


def es_admitido(nombre: str) -> bool:
    return Path(nombre).suffix.lower() in EXTENSIONES


@dataclass(frozen=True)
class Copia:
    """Un renombrado pendiente: de qué fichero a qué caso."""

    origen: str
    destino: str
    caso_id: str
    formato: str
    gemelo_de: str = ""


@dataclass(frozen=True)
class Fallo:
    """Uno de los cuatro casos que la regla de nombres no cubre (R21)."""

    tipo: str
    detalle: str


@dataclass
class Emparejado:
    """El plan de renombrado y todo lo que se quedó fuera, con nombre."""

    copias: list[Copia] = field(default_factory=list)
    fallos: list[Fallo] = field(default_factory=list)
    ya_colocados: list[str] = field(default_factory=list)
    ignorados: list[str] = field(default_factory=list)


def emparejar(
    casos_por_codigo: dict[str, str],
    ficheros: list[str],
    caso_ids: set[str] | None = None,
) -> Emparejado:
    """Casa los documentos de entrada con los casos. Nada se cae en silencio.

    `casos_por_codigo` va con el código YA normalizado, que es como se
    comparan: el humano escribe `2.115.714` en el Excel y `2115714` en el
    nombre del fichero, y son el mismo albarán.
    """
    plan = Emparejado()
    caso_ids = caso_ids or set()
    por_codigo: dict[str, list[tuple[str, str]]] = {}

    for fichero in ficheros:
        if not es_admitido(fichero):
            plan.ignorados.append(fichero)
            continue
        if Path(fichero).stem in caso_ids:
            plan.ya_colocados.append(fichero)
            continue
        codigo = normalizar_codigo(codigo_desde_nombre(fichero))
        if not codigo:
            plan.fallos.append(
                Fallo(
                    "nombre_vacio",
                    f"'{fichero}': tras aplicar la regla del nombre no queda "
                    f"ningún código con el que buscarlo en el Excel.",
                )
            )
            continue
        por_codigo.setdefault(codigo, []).append((fichero, formato_de(fichero)))

    casados: set[str] = set()
    for codigo, encontrados in sorted(por_codigo.items()):
        caso_id = casos_por_codigo.get(codigo)
        if caso_id is None:
            plan.fallos.append(
                Fallo(
                    "codigo_sin_fila",
                    f"código '{codigo}' ({', '.join(n for n, _ in encontrados)}): "
                    f"no hay ninguna fila del Excel con ese código de albarán.",
                )
            )
            continue
        if _hay_choque(plan, codigo, encontrados):
            # El caso ya sale listado por su choque; repetirlo como «sin
            # fichero» diluye el informe con el mismo problema contado dos
            # veces, y el humano acaba sin leer ninguno de los dos.
            casados.add(codigo)
            continue
        casados.add(codigo)
        plan.copias.extend(_copias_de(caso_id, encontrados))

    for codigo, caso_id in sorted(casos_por_codigo.items(), key=lambda par: par[1]):
        if codigo not in casados and not _ya_colocado(caso_id, plan):
            plan.fallos.append(
                Fallo(
                    "fila_sin_fichero",
                    f"{caso_id} (código '{codigo}'): el Excel lo trae pero no hay "
                    f"ningún documento suyo en la carpeta de entrada.",
                )
            )
    return plan


def _hay_choque(plan: Emparejado, codigo: str, encontrados: list[tuple[str, str]]) -> bool:
    """Dos ficheros del MISMO formato y código: eso sí es un duplicado."""
    por_formato: dict[str, list[str]] = {}
    for nombre, formato in encontrados:
        por_formato.setdefault(formato, []).append(nombre)
    chocan = {f: n for f, n in por_formato.items() if len(n) > 1}
    if not chocan:
        return False
    detalle = "; ".join(
        f"{formato}: {', '.join(sorted(nombres))}" for formato, nombres in sorted(chocan.items())
    )
    plan.fallos.append(
        Fallo(
            "codigo_duplicado",
            f"código '{codigo}': dos o más ficheros del mismo formato resuelven "
            f"al mismo código ({detalle}). Ninguno entra en el plan.",
        )
    )
    return True


def _copias_de(caso_id: str, encontrados: list[tuple[str, str]]) -> list[Copia]:
    """Un fichero por caso; y si hay PDF e imagen, DOS casos gemelos (R22).

    El mismo albarán en los dos formatos no es un duplicado que deduplicar: es
    el único experimento del banco que aísla el formato. Mismo ground truth,
    distinta entrada; un fallo que solo sale en el gemelo de imagen es un
    hallazgo de FORMATO, no de extracción.
    """
    hay_pareja = len({formato for _, formato in encontrados}) > 1
    copias: list[Copia] = []
    for nombre, formato in sorted(encontrados, key=lambda par: par[1] != "pdf"):
        es_gemelo = hay_pareja and formato == "imagen"
        propio = f"{caso_id}{SUFIJO_IMAGEN}" if es_gemelo else caso_id
        copias.append(
            Copia(
                origen=nombre,
                destino=f"{propio}{Path(nombre).suffix.lower()}",
                caso_id=propio,
                formato=formato,
                gemelo_de=caso_id if es_gemelo else "",
            )
        )
    return copias


def _ya_colocado(caso_id: str, plan: Emparejado) -> bool:
    return any(Path(nombre).stem == caso_id for nombre in plan.ya_colocados)


def renombrar(
    copias: list[Copia], directorio: Path | str, ejecutar: bool = True
) -> list[str]:
    """Aplica el plan. Reproducible: el humano sigue trayendo material.

    Nunca pisa un destino que ya existe: si `RES-001.pdf` está ahí, el que
    manda es el que ya se emparejó, y sobrescribirlo dejaría un caso apuntando
    a un papel distinto del que dice el mapa.
    """
    carpeta = Path(directorio)
    hechos: list[str] = []
    for copia in copias:
        origen = carpeta / copia.origen
        destino = carpeta / copia.destino
        if not origen.is_file() or destino.exists():
            continue
        if ejecutar:
            origen.rename(destino)
        hechos.append(f"{copia.origen} -> {copia.destino}")
    return hechos
