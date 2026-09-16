# evals/revision/modelos.py
"""Modelos puros del importador: la fila plana, el caso y el informe.

Sin openpyxl y sin disco: es la parte que lleva cobertura y mutación. Todo lo
que toca ficheros vive en `lectura.py` y `escritura.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Columnas de la tabla plana: clave interna -> encabezados admitidos, ya
#: normalizados (`lectura.normalizar_encabezado`). Se localizan por NOMBRE y no
#: por posición: el humano añade columnas y las posiciones se mueven. El primer
#: encabezado de cada lista es el que hoy trae el Excel —«codigo alabran» lleva
#: la errata de origen a propósito: el fichero es suyo, no nuestro—.
COLUMNAS: dict[str, tuple[str, ...]] = {
    "codigo_albaran": ("codigo alabran", "codigo albaran"),
    "tipo_albaran": ("tipo de albaran",),
    "cif": ("cif",),
    "nombre_empresa": ("nombre empresa",),
    "codigo_obra": ("codigo obra",),
    "fecha": ("fecha",),
    "codigo_contrato": ("codigo contrato",),
    "partida": ("partida",),
    "origen_linea": ("linea esta en albaran o deducida",),
    "origen_contrato": ("linea en contrato de sigrid o nueva",),
    "concepto": ("concepto",),
    "cantidad": ("cantidad",),
    "unidad": ("unidad",),
    "precio_unitario": ("precio unitario",),
    "origen_precio": ("unitario viene en albaran o valorado en contrato",),
    "importe": ("importe",),
    "origen_importe": ("importe viene en albaran o valorado en contrato",),
    "descuento": ("descuento",),
    "ler": ("ler o codigo linea o producto",),
    "comentarios": ("comentarios",),
}

#: Columnas sin las cuales no se puede repartir nada.
COLUMNAS_OBLIGATORIAS: tuple[str, ...] = (
    "codigo_albaran",
    "tipo_albaran",
    "cif",
    "origen_linea",
    "origen_contrato",
)

#: El caso salió BIEN en la revisión y hay que seguir comprobando que sigue
#: saliendo bien. Es la mitad más valiosa del banco: avisa de regresiones.
NO_REGRESION = "no_regresion"

#: El humano escribió un comentario: hoy falla. Rojo esperado hasta su ficha.
DEFECTO_CONOCIDO = "defecto_conocido"

#: Sentinela `?` de los libros: «no compares este campo en este caso».
INTERROGANTE = "?"


@dataclass(frozen=True)
class FilaPlana:
    """Una fila del Excel, ya localizada por nombre de columna.

    `numero_fila` es la fila REAL del Excel (1 = encabezados): sin ella un
    aborto por vocabulario desconocido obliga a buscar a ojo entre 142 filas.
    """

    numero_fila: int
    valores: dict[str, object | None]

    def bruto(self, columna: str) -> object | None:
        return self.valores.get(columna)

    def texto(self, columna: str) -> str:
        valor = self.valores.get(columna)
        if valor is None:
            return ""
        return str(valor).strip()

    def vacia(self, columna: str) -> bool:
        return not self.texto(columna)


@dataclass(frozen=True)
class LineaRevisada:
    """Una fila plana ya interpretada: de qué fase es cada dato suyo."""

    fila: FilaPlana
    #: `impresa` (existe en el papel) o `deducida` (la decide la valoración).
    origen_linea: str
    #: `contrato`, `nueva` u `oferta`.
    origen_contrato: str
    #: `precio_source` de los libros: albaran | contrato_db | oferta | deducido.
    precio_source: str
    #: El unitario está IMPRESO en el papel (y por tanto es de IA1).
    precio_impreso: bool
    importe_source: str
    #: El importe está IMPRESO en el papel (y por tanto es de IA1).
    importe_impreso: bool
    #: Número de línea dentro del caso: propio si es impresa, de su línea base
    #: si es deducida (`None` cuando una deducida no tiene línea base delante).
    num_linea: int | None

    @property
    def es_impresa(self) -> bool:
        return self.origen_linea == "impresa"


@dataclass
class CasoRevisado:
    """Un albarán de la revisión: su cabecera, sus líneas y su clasificación."""

    codigo: str
    clave: str
    destino: object  # vocabulario.DestinoEtiqueta (evita el import circular)
    lineas: list[LineaRevisada] = field(default_factory=list)
    caso_id: str = ""
    #: Nombre del documento de entrada ya renombrado, cuando existe (R20).
    fichero: str = ""
    #: Caso del que este es gemelo de formato (R22); vacío si no lo es.
    gemelo_de: str = ""

    @property
    def clasificacion(self) -> str:
        """R9/R10: el comentario NO dice qué se espera, dice qué falla hoy."""
        return DEFECTO_CONOCIDO if self.comentarios else NO_REGRESION

    @property
    def comentarios(self) -> list[str]:
        vistos: list[str] = []
        for linea in self.lineas:
            texto = linea.fila.texto("comentarios")
            if texto and texto not in vistos:
                vistos.append(texto)
        return vistos

    @property
    def impresas(self) -> list[LineaRevisada]:
        return [linea for linea in self.lineas if linea.es_impresa]

    @property
    def deducidas(self) -> list[LineaRevisada]:
        return [linea for linea in self.lineas if not linea.es_impresa]


@dataclass
class InformeImportacion:
    """Lo que hay que poder leer sin abrir el Excel ni los libros (R14)."""

    filas_leidas: int = 0
    casos: list[CasoRevisado] = field(default_factory=list)
    caso_ids_nuevos: list[str] = field(default_factory=list)
    #: {libro: {tabla: {columna: {"valor": n, "interrogante": n, "vacia": n}}}}
    celdas: dict[str, dict[str, dict[str, dict[str, int]]]] = field(default_factory=dict)
    #: Casos que cambian de bando respecto a la importación anterior.
    cambios_de_grupo: list[tuple[str, str, str]] = field(default_factory=list)
    #: Fallos ruidosos del emparejado de documentos de entrada (R21).
    fallos_documentos: list[str] = field(default_factory=list)
    #: El plan de renombrado, con la estrategia de cada emparejado: el
    #: humano lo revisa ANTES de renombrar, porque deshacer un renombrado
    #: sobre una asignación equivocada es caro.
    plan_renombrado: list[str] = field(default_factory=list)
    renombrados: list[str] = field(default_factory=list)
    #: Casos cuya familia de documento aún no existe en el catálogo (R6).
    familias_pendientes: dict[str, list[str]] = field(default_factory=dict)
    #: Criterios de residuos aún sin implementar que tocan a cada caso (R12 bis).
    criterios_residuos: dict[str, list[str]] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    #: La pasada fue `--dry-run`. Distingue «no se escribió porque no se
    #: quiso» de «no se escribió porque nada cambiaba», que es R18.
    en_seco: bool = False
    libros_escritos: list[str] = field(default_factory=list)
    #: Los que la pasada miró, escribiera o no: sin esto, un «ninguno»
    #: no distingue «no cambiaba nada» de «no llegó a mirarlos».
    libros_comprobados: list[str] = field(default_factory=list)
    copias: list[str] = field(default_factory=list)

    def contar(self, libro: str, tabla: str, columna: str, valor: object | None) -> None:
        """Clasifica UNA celda escrita en valor, `?` o vacía."""
        cubo = (
            self.celdas.setdefault(libro, {})
            .setdefault(tabla, {})
            .setdefault(columna, {"valor": 0, "interrogante": 0, "vacia": 0})
        )
        if valor == INTERROGANTE:
            cubo["interrogante"] += 1
        elif valor is None or (isinstance(valor, str) and not valor.strip()):
            cubo["vacia"] += 1
        else:
            cubo["valor"] += 1

    @property
    def por_clasificacion(self) -> dict[str, int]:
        reparto = {NO_REGRESION: 0, DEFECTO_CONOCIDO: 0}
        for caso in self.casos:
            reparto[caso.clasificacion] += 1
        return reparto
