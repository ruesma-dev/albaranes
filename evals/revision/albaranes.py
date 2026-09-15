# evals/revision/albaranes.py
"""El puente entre el documento de papel, la fila del Excel y el caso.

Convenio del humano (2026-09-15): del **nombre del fichero** sale el **código
de albarán** —el que él escribe en cada fila del Excel— y de ahí el `caso_id`.

    PROVEEDOR_SS-0003967.pdf ─┐
                              ├─ SS-0003967 ─ RES-004 ─ RES-004.pdf
    SS-0003967.png ───────────┘

Pero el material real no se deja emparejar con una sola regla. Medido sobre
los 133 ficheros que el humano tiene en OneDrive (2026-09-15): la regla de la
spec —lo que va tras el último `_`— deja **24 de 59 códigos sin fichero**,
porque los nombres que llegan de obra son de la forma

    ALB. C.T.C 2025-01-27  Vertedero Arecosur 188048-24385 - 0669 BLOSSOM.pdf

donde el código va EN MEDIO y no hay ni un `_`. De ahí una **escalera de
estrategias**, de la más específica a la más laxa (`exacto` → `subcadena` →
`sin_ceros`), con tres cosas que no se negocian:

- **La ambigüedad no se resuelve sola: se lista.** Un fichero que contiene dos
  códigos conocidos —los hay: un PDF con dos albaranes de fechas distintas— no
  se asigna a ninguno. Asignar en silencio dejaría un caso comparándose contra
  el papel de otro, y eso no lo detecta nadie.
- **Manda el código del papel, nunca el persistido.** El precedente es
  `SS-0801977` leído donde el papel decía `SS-0001977`; por eso `sin_ceros`
  solo quita los ceros de la IZQUIERDA, que no cambian el número, y jamás los
  de dentro, que sí distinguen dos albaranes.
- **Cada emparejado anota con qué estrategia se hizo.** Renombrar sobre una
  asignación equivocada es difícil de deshacer, así que el humano tiene que
  poder revisar el plan antes: por eso renombrar es un paso aparte y opcional.

Y **los fallos que la regla no cubre salen listados uno a uno** (R21):
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

#: Longitud mínima para buscar un código DENTRO de un nombre. Por debajo, la
#: subcadena deja de ser evidencia: un código de tres cifras aparece dentro de
#: cualquier fecha del nombre, y emparejar por eso es peor que no emparejar.
MINIMO_SUBCADENA = 5

#: De la más específica a la más laxa. El orden importa: la primera que
#: encuentra algo decide, y así una coincidencia exacta nunca pierde contra
#: una subcadena casual.
ESTRATEGIAS: tuple[str, ...] = ("exacto", "subcadena", "sin_ceros")


def codigo_desde_nombre(nombre: str) -> str:
    """`PROVEEDOR_SS-0003967.pdf` → `SS-0003967`; `SS-0003967.png` → igual."""
    tronco = Path(nombre).stem.strip()
    return tronco.rsplit("_", 1)[-1].strip() if "_" in tronco else tronco


def formato_de(nombre: str) -> str:
    """`pdf` o `imagen`: es lo que distingue a un caso de su gemelo (R23)."""
    return "pdf" if Path(nombre).suffix.lower() == ".pdf" else "imagen"


def es_admitido(nombre: str) -> bool:
    return Path(nombre).suffix.lower() in EXTENSIONES


def sin_ceros(codigo: str) -> str:
    """Quita los ceros de la IZQUIERDA, que no cambian el número.

    Los de dentro NO se tocan: `SS-0801977` y `SS-0001977` son dos albaranes
    distintos y confundirlos ya costó una valoración equivocada.
    """
    return codigo.lstrip("0") or codigo


def candidatos(nombre: str, codigos: set[str]) -> tuple[str, list[str]]:
    """Qué códigos podría ser este fichero, y con qué estrategia.

    Devuelve la PRIMERA estrategia que encuentra algo y todos sus candidatos:
    si son varios, quien decide es el humano, no esta función.
    """
    tronco = normalizar_codigo(Path(nombre).stem)
    propio = normalizar_codigo(codigo_desde_nombre(nombre))

    exacto = [codigo for codigo in codigos if codigo == propio]
    if exacto:
        return "exacto", sorted(exacto)

    dentro = [
        codigo
        for codigo in codigos
        if len(codigo) >= MINIMO_SUBCADENA and codigo in tronco
    ]
    if dentro:
        return "subcadena", sorted(dentro)

    pelados = [
        codigo
        for codigo in codigos
        if sin_ceros(codigo) == sin_ceros(propio)
        or (len(sin_ceros(codigo)) >= MINIMO_SUBCADENA and sin_ceros(codigo) in tronco)
    ]
    if pelados:
        return "sin_ceros", sorted(pelados)
    return "", []


@dataclass(frozen=True)
class Copia:
    """Un renombrado pendiente: de qué fichero a qué caso, y por qué."""

    origen: str
    destino: str
    caso_id: str
    formato: str
    #: Con qué estrategia se casó. Va al informe: antes de renombrar, el
    #: humano tiene que poder ver POR QUÉ se emparejó cada fichero.
    estrategia: str = "exacto"
    gemelo_de: str = ""


@dataclass(frozen=True)
class Fallo:
    """Algo que la regla de nombres no resuelve y que nadie debe adivinar."""

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
    codigos = set(casos_por_codigo)
    por_codigo: dict[str, list[tuple[str, str, str]]] = {}

    for fichero in sorted(ficheros):
        if not es_admitido(fichero):
            plan.ignorados.append(fichero)
            continue
        if Path(fichero).stem in caso_ids:
            plan.ya_colocados.append(fichero)
            continue
        if not normalizar_codigo(codigo_desde_nombre(fichero)):
            plan.fallos.append(
                Fallo(
                    "nombre_vacio",
                    f"'{fichero}': tras aplicar la regla del nombre no queda "
                    f"ningún código con el que buscarlo en el Excel.",
                )
            )
            continue
        estrategia, encontrados = candidatos(fichero, codigos)
        if not encontrados:
            plan.fallos.append(
                Fallo(
                    "codigo_sin_fila",
                    f"'{fichero}': ninguna de las estrategias "
                    f"({', '.join(ESTRATEGIAS)}) encuentra en el Excel un "
                    f"código de albarán que case con este nombre.",
                )
            )
            continue
        if len(encontrados) > 1:
            plan.fallos.append(
                Fallo(
                    "fichero_varios_codigos",
                    f"'{fichero}': el nombre contiene {len(encontrados)} códigos "
                    f"del Excel ({', '.join(encontrados)}). O es un PDF con "
                    f"varios albaranes —hay que partirlo, 1 albarán = 1 "
                    f"documento— o el nombre es ambiguo. No se asigna a ninguno.",
                )
            )
            continue
        por_codigo.setdefault(encontrados[0], []).append(
            (fichero, formato_de(fichero), estrategia)
        )

    casados: set[str] = set()
    for codigo, encontrados in sorted(por_codigo.items()):
        casados.add(codigo)
        if _hay_choque(plan, codigo, encontrados):
            # El caso ya sale listado por su choque; repetirlo como «sin
            # fichero» diluye el informe con el mismo problema contado dos
            # veces, y el humano acaba sin leer ninguno de los dos.
            continue
        plan.copias.extend(_copias_de(casos_por_codigo[codigo], encontrados))

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


def _hay_choque(
    plan: Emparejado, codigo: str, encontrados: list[tuple[str, str, str]]
) -> bool:
    """Dos ficheros DISTINTOS con el mismo código y formato: eso no se elige."""
    por_formato: dict[str, list[str]] = {}
    for nombre, formato, _ in encontrados:
        por_formato.setdefault(formato, []).append(nombre)
    chocan = {f: n for f, n in por_formato.items() if len(n) > 1}
    if not chocan:
        return False
    detalle = "; ".join(
        f"{formato}: {', '.join(sorted(nombres))}"
        for formato, nombres in sorted(chocan.items())
    )
    plan.fallos.append(
        Fallo(
            "codigo_duplicado",
            f"código '{codigo}': dos o más ficheros del mismo formato resuelven "
            f"al mismo código ({detalle}). Ninguno entra en el plan.",
        )
    )
    return True


def _copias_de(caso_id: str, encontrados: list[tuple[str, str, str]]) -> list[Copia]:
    """Un fichero por caso; y si hay PDF e imagen, DOS casos gemelos (R22).

    El mismo albarán en los dos formatos no es un duplicado que deduplicar: es
    el único experimento del banco que aísla el formato. Mismo ground truth,
    distinta entrada; un fallo que solo sale en el gemelo de imagen es un
    hallazgo de FORMATO, no de extracción.
    """
    hay_pareja = len({formato for _, formato, _ in encontrados}) > 1
    copias: list[Copia] = []
    for nombre, formato, estrategia in sorted(
        encontrados, key=lambda trio: trio[1] != "pdf"
    ):
        es_gemelo = hay_pareja and formato == "imagen"
        propio = f"{caso_id}{SUFIJO_IMAGEN}" if es_gemelo else caso_id
        copias.append(
            Copia(
                origen=nombre,
                destino=f"{propio}{Path(nombre).suffix.lower()}",
                caso_id=propio,
                formato=formato,
                estrategia=estrategia,
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
