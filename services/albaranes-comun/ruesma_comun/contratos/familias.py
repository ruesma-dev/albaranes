# ruesma_comun/contratos/familias.py
"""Catalogo UNICO de familias de albaran (F-043, R1-R5).

Decision del humano del 2026-08-25: **la familia de un albaran la decide
SIEMPRE la IA**. Si clasifica mal se arregla el PROMPT, nunca con un ``if``
aguas abajo. Este modulo es por tanto dos cosas y ninguna mas:

1. El TEXTO que la IA lee para decidir: que ES cada familia (``definicion``),
   en que se DIFERENCIA de sus vecinas (``no_es``) y que SENALES mirar en el
   papel (``senales``). Se inyecta en el prompt de fase 1 con
   ``render_catalogo_markdown()``.
2. El ENRUTADO determinista que viene DESPUES de que la IA haya decidido:
   dada la familia que dijo la IA, que prompt de fase 2 y que prompt de
   valoracion le tocan (``prompt_fase2_de`` / ``prompt_valoracion_de``).

Lo que este modulo NO hace y tiene PROHIBIDO hacer: inferir la familia a
partir del codigo LER, de la familia de producto, del CIF del proveedor o de
palabras del texto. Eso era el lazo cerrado que F-043 desmonta (el
``tipologia_resolver`` deducia la tipologia con reglas y con ella elegia el
prompt, asi que la regla decidia lo que la IA podia concluir).

Anadir una familia = **una entrada en ``CATALOGO``** con sus dos claves de
prompt (R3). Ningun servicio declara lista propia de familias ni tabla propia
de prompts por familia (R2).

Los textos van SIN TILDES a proposito: viajan al prompt, a los tests y al log
atravesando serializaciones varias, y las comparaciones por palabra clave no
se rompen por un acento.

Capa ``domain`` compartida: funciones puras, sin I/O, sin red, sin BBDD.
"""
from __future__ import annotations

from dataclasses import dataclass

ALCANCE_DOCUMENTO = "documento"
ALCANCE_LINEA = "linea"

_ALCANCES_VALIDOS = frozenset({ALCANCE_DOCUMENTO, ALCANCE_LINEA})


@dataclass(frozen=True)
class Familia:
    """Una familia de albaran, tal y como se le explica a la IA.

    ``alcance`` dice si la familia puede ser clasificacion de DOCUMENTO,
    afinado por LINEA (``contexto_linea.tipo_familia``) o ambas cosas.
    ``prompt_fase2`` y ``prompt_valoracion`` son claves del indice de prompts
    del servicio correspondiente; ``None`` significa "cae al prompt generico
    que ese servicio tenga configurado" (R15).
    """

    id: str
    nombre: str
    definicion: str
    no_es: str
    senales: str
    alcance: frozenset[str]
    prompt_fase2: str | None = None
    prompt_valoracion: str | None = None


_DOCUMENTO_Y_LINEA = frozenset({ALCANCE_DOCUMENTO, ALCANCE_LINEA})
_SOLO_LINEA = frozenset({ALCANCE_LINEA})


# --------------------------------------------------------------------- #
# El catalogo. Arranca con las CUATRO familias de documento que hoy tienen
# prompt de fase 2 propio (decision del humano del 2026-08-26, duda 1):
# `combustible`, `alquiler_maquinaria` y `otro` siguen siendo familia de
# LINEA porque no hay prompt al que enrutarlas, y una etiqueta sin reglas
# detras no clasifica nada.
# --------------------------------------------------------------------- #
CATALOGO: tuple[Familia, ...] = (
    Familia(
        id="generico",
        nombre="Generico / suministro",
        definicion=(
            "Albaran de suministro de materiales o productos que se valoran "
            "linea a linea contra el contrato, sin reglas de valoracion "
            "propias de familia: prefabricados, ceramica, ferreteria, "
            "siderurgia, aislamiento, material de obra en general."
        ),
        no_es=(
            "NO es el cajon de 'no se pudo clasificar'. 'generico' es una "
            "clase legitima y positiva: el documento SI se entendio y "
            "resulta que no pertenece a ninguna familia con reglas propias. "
            "La duda no se expresa eligiendo 'generico': se expresa bajando "
            "confianza_pct y explicandola en el motivo."
        ),
        senales=(
            "Lineas de producto con cantidad, unidad y precio; sin codigos "
            "LER, sin designacion de central de hormigon o mortero, sin "
            "horas de maquina ni litros de carburante."
        ),
        alcance=_DOCUMENTO_Y_LINEA,
        # Sin prompt propio: cae a `albaran_revision_fase2_es` y a
        # `valuation_es`, los genericos configurados en sv2 y sv5.
        prompt_fase2=None,
        prompt_valoracion=None,
    ),
    Familia(
        id="hormigon",
        nombre="Hormigon",
        definicion=(
            "Albaran de suministro de hormigon fabricado en central y "
            "servido en obra por camion hormigonera, con designacion "
            "normalizada del producto (tipo, resistencia, consistencia, "
            "tamano de arido y ambiente) y metros cubicos servidos."
        ),
        no_es=(
            "NO es mortero. El mortero se designa con codigos propios del "
            "fabricante (serie D-*, M-5, M-7,5) y no sigue la nomenclatura "
            "posicional del hormigon; si el documento llama al producto "
            "mortero, mortero seco, industrial o de albanileria, la familia "
            "es 'mortero' y no 'hormigon', por mucho que el proveedor sea "
            "una central de hormigones."
        ),
        senales=(
            "Designaciones tipo HA-25/B/20/IIa o HM-20/P/20/I; metros "
            "cubicos servidos; horas de llegada, descarga y salida; cargas "
            "incompletas; m3 no transportados; servicio de bomba o cuba."
        ),
        alcance=_DOCUMENTO_Y_LINEA,
        prompt_fase2="albaran_revision_fase2_hormigon",
        prompt_valoracion=None,
    ),
    Familia(
        id="mortero",
        nombre="Mortero",
        definicion=(
            "Albaran de suministro de mortero (seco, humedo, industrial, de "
            "albanileria o de agarre) fabricado en central y servido en obra "
            "en silo, cuba o saco."
        ),
        no_es=(
            "NO es hormigon. Al mortero no se le aplica la nomenclatura "
            "posicional del hormigon ni sus lineas sinteticas (incremento "
            "de arido, plastificante, aditivos): inventarselas fue el fallo "
            "que obligo a separar esta familia."
        ),
        senales=(
            "Codigos de producto de serie D-* o denominaciones 'mortero', "
            "'M-5', 'M-7,5'; suministro en silo, cuba de mortero o sacos; "
            "kilos o metros cubicos de mortero."
        ),
        alcance=_DOCUMENTO_Y_LINEA,
        prompt_fase2="albaran_revision_fase2_mortero",
        # `valuation_mortero` no existe todavia (lo crea F-023): cae al
        # generico `valuation_es`.
        prompt_valoracion=None,
    ),
    Familia(
        id="residuos",
        nombre="Residuos / gestion de RCD",
        definicion=(
            "Albaran de un GESTOR de residuos que documenta la retirada y el "
            "tratamiento de residuos de construccion y demolicion: el "
            "proveedor se hace cargo del residuo, lo identifica por su "
            "codigo LER y lo lleva a planta o vertedero autorizado."
        ),
        no_es=(
            "NO es un albaran de transporte ni el alquiler de un contenedor "
            "sin gestion del residuo. Si el proveedor solo pone el "
            "contenedor, o solo mueve tierra o material de un punto a otro, "
            "sin hacerse cargo del residuo (sin codigo LER, sin destino de "
            "tratamiento, sin condicion de gestor autorizado), la familia no "
            "es 'residuos'."
        ),
        senales=(
            "Codigos LER de seis digitos (170504, 170203); mencion a gestor "
            "autorizado, planta de tratamiento, vertedero o canon de "
            "vertido; contenedores llevados y retirados; volumen en m3 o "
            "peso en toneladas del residuo."
        ),
        alcance=_DOCUMENTO_Y_LINEA,
        prompt_fase2="albaran_revision_fase2_residuos",
        prompt_valoracion="valuation_residuos",
    ),
    Familia(
        id="combustible",
        nombre="Combustible / carburante",
        definicion=(
            "Linea de suministro de combustible o carburante entregado en "
            "obra, en deposito o en maquina (gasoleo A, gasoleo B, AdBlue), "
            "medida en litros."
        ),
        no_es=(
            "NO es familia de DOCUMENTO en este catalogo: todavia no tiene "
            "prompt de fase 2 propio al que enrutarla. Un albaran de "
            "carburante se clasifica como documento 'generico' y son sus "
            "LINEAS las que llevan tipo_familia='combustible'."
        ),
        senales=(
            "Litros servidos y precio por litro; matricula del camion "
            "cisterna; deposito, maquina o vehiculo repostado."
        ),
        alcance=_SOLO_LINEA,
        prompt_fase2=None,
        prompt_valoracion=None,
    ),
    Familia(
        id="alquiler_maquinaria",
        nombre="Alquiler de maquinaria y medios auxiliares",
        definicion=(
            "Linea de alquiler de maquinaria o de medios auxiliares "
            "(retroexcavadora, plataforma, andamio, grupo electrogeno, "
            "contenedor sin gestion del residuo), facturada por tiempo de "
            "posesion o de uso."
        ),
        no_es=(
            "NO es familia de DOCUMENTO en este catalogo (sin prompt de fase "
            "2 propio). Y no es 'residuos' aunque lo alquilado sea un "
            "contenedor: si nadie se hace cargo del residuo, es alquiler."
        ),
        senales=(
            "Periodo de alquiler con fechas de entrega y recogida; dias u "
            "horas de maquina; lectura de horometro; portes de entrega y "
            "retirada."
        ),
        alcance=_SOLO_LINEA,
        prompt_fase2=None,
        prompt_valoracion=None,
    ),
    Familia(
        id="otro",
        nombre="Otro (linea sin reglas de familia)",
        definicion=(
            "Linea que no pertenece a ninguna familia con reglas de "
            "valoracion propias dentro de un albaran que si tiene familia: "
            "transporte suelto, portes, mano de obra, gastos, suplidos."
        ),
        no_es=(
            "NO es un 'no lo se'. Marcar una linea como 'otro' es la forma "
            "de decir que esa linea NO debe recibir las reglas de la familia "
            "del documento: por eso una linea 'otro' nunca hereda la familia "
            "del albaran (si heredara, una linea de transporte dentro de un "
            "albaran de residuos se comeria la regla de contenedores)."
        ),
        senales=(
            "Conceptos de transporte, portes, mano de obra, alquiler "
            "puntual, gastos o suplidos dentro de un albaran de otra "
            "familia."
        ),
        alcance=_SOLO_LINEA,
        prompt_fase2=None,
        prompt_valoracion=None,
    ),
)


def _normalizar(id_familia: object) -> str:
    """Deja el identificador como lo escribe el catalogo.

    La IA puede devolver ' Hormigon ' o 'RESIDUOS'; eso no es una familia
    distinta. Normalizar aqui evita que cada servicio invente su propia
    limpieza (y que dos servicios la inventen distinta).
    """
    if not id_familia:
        return ""
    return str(id_familia).strip().lower()


def familias_documento() -> tuple[str, ...]:
    """Familias que pueden ser clasificacion de DOCUMENTO (R2)."""
    return tuple(f.id for f in CATALOGO if ALCANCE_DOCUMENTO in f.alcance)


def familias_linea() -> tuple[str, ...]:
    """Familias que pueden ser afinado por LINEA (R2)."""
    return tuple(f.id for f in CATALOGO if ALCANCE_LINEA in f.alcance)


def obtener(id_familia: str | None) -> Familia | None:
    """Devuelve la familia del catalogo, o ``None`` si esta fuera de el.

    ``None`` es una respuesta legitima y esperada: es lo que ocurre cuando
    la IA se inventa una etiqueta (R10). Quien llama decide que hacer con
    ello; este modulo no adivina.
    """
    clave = _normalizar(id_familia)
    if not clave:
        return None
    for familia in CATALOGO:
        if familia.id == clave:
            return familia
    return None


def render_catalogo_markdown(alcance: str = ALCANCE_DOCUMENTO) -> str:
    """Renderiza el catalogo para inyectarlo en un prompt (R6).

    Sale una entrada por familia con las tres cosas que la IA necesita para
    decidir: que es, en que se diferencia de sus vecinas y que senales mirar
    en el papel. Las senales son EVIDENCIA que la IA debe leer, nunca una
    regla que la obligue a concluir una familia.
    """
    if alcance not in _ALCANCES_VALIDOS:
        raise ValueError(
            f"alcance desconocido: {alcance!r}; "
            f"esperado uno de {sorted(_ALCANCES_VALIDOS)}"
        )

    bloques: list[str] = []
    for familia in CATALOGO:
        if alcance not in familia.alcance:
            continue
        bloques.append(
            f"- `{familia.id}` ({familia.nombre})\n"
            f"  - Que es: {familia.definicion}\n"
            f"  - En que se diferencia: {familia.no_es}\n"
            f"  - Senales en el documento: {familia.senales}"
        )
    return "\n".join(bloques)


def prompt_fase2_de(familia: str | None) -> str | None:
    """Clave del prompt de fase 2 de esa familia, o ``None`` (R15).

    ``None`` significa "usa el prompt generico configurado en el servicio":
    tanto para las familias que no tienen prompt propio (``generico``) como
    para una familia fuera de catalogo. Nunca revienta el enrutado.
    """
    entrada = obtener(familia)
    return entrada.prompt_fase2 if entrada is not None else None


def prompt_valoracion_de(familia: str | None) -> str | None:
    """Clave del prompt de valoracion de esa familia, o ``None`` (R24)."""
    entrada = obtener(familia)
    return entrada.prompt_valoracion if entrada is not None else None


def _campo(clasificacion: object, nombre: str, defecto: object) -> object:
    """Lee un campo de la clasificacion venga como objeto o como dict.

    sv5 y sv6 la manejan ya validada (``ClasificacionAlbaran``), pero el
    envelope viaja como diccionario antes de validarse. Un solo lector para
    los dos casos es lo que permite que el criterio viva en UN punto (R20).
    """
    if isinstance(clasificacion, dict):
        valor = clasificacion.get(nombre, defecto)
    else:
        valor = getattr(clasificacion, nombre, defecto)
    return defecto if valor is None else valor


def familia_efectiva(
    tipo_familia_linea: str | None,
    clasificacion: object,
) -> str | None:
    """Familia con la que hay que tratar UNA linea (R18-R21, R27).

    Las cuatro ramas, en este orden:

    1. La linea trae ``tipo_familia``: manda esa. Lo que la IA dijo de la
       linea gana siempre a lo que dijo del documento — incluido ``otro``,
       que es precisamente la forma de decir "a esta linea no le apliques
       las reglas del albaran".
    2. No hay clasificacion de documento (envelope anterior a F-043):
       ``None``, es decir, exactamente el comportamiento de hoy (R27).
    3. El documento esta marcado ``mixto``: ``None``. En un albaran mixto
       NO se hereda (R19); esas lineas se quedan sin familia efectiva y sv3
       les anade el motivo ``linea_sin_familia_en_albaran_mixto``.
    4. Si no, la familia del documento, siempre que sea familia de LINEA.

    Esto NO es una regla que infiera la familia: propaga a la linea la
    decision que la IA tomo sobre el documento. No mira el codigo LER, ni el
    texto del concepto, ni el CIF del proveedor. Y no ESCRIBE nada: la
    herencia se resuelve en lectura, para no borrar la diferencia entre "lo
    dijo la IA por linea" y "se heredo del documento" (R21).
    """
    # Rama 1
    de_la_linea = _normalizar(tipo_familia_linea)
    if de_la_linea:
        return de_la_linea

    # Rama 2
    if clasificacion is None:
        return None

    # Rama 3
    if bool(_campo(clasificacion, "mixto", False)):
        return None

    # Rama 4
    del_documento = _normalizar(_campo(clasificacion, "familia", ""))
    if del_documento in familias_linea():
        return del_documento
    return None
