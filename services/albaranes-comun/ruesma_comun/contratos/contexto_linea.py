# ruesma_comun/contratos/contexto_linea.py
"""Modelo compartido del bloque ``contexto_linea``.

Representa la información estructural de una línea de albarán cuando
pertenece a una familia compleja (hormigón, combustible, alquiler de
maquinaria). Este fichero se copia IDÉNTICO en los servicios 2, 3 y 5
que manipulan el envelope de extracción.

Campos (ver prompts V2 para semántica completa):
  - tipo_familia: una de las familias de LÍNEA del catálogo único
    (``ruesma_comun.contratos.familias.familias_linea()``), o null.
  - rol_linea: 'base' | 'extra_tiempo' | 'transporte' | 'recargo_horario'
               | 'desplazamiento' | 'operario' | 'otro' | null
  - descripcion_extendida: string con la descripción técnica completa
    (incluye modificadores del producto base). La usa el valorador para
    buscar recargos en el PDF del contrato.
  - notas_tiempo: string libre con info temporal del albarán (horas
    de carga/descarga, minutos netos, tiempo máximo libre declarado).
  - ref_linea_base: int con el ``line_index`` de la línea base asociada
    cuando esta línea es complementaria (extra_tiempo, transporte,
    operario...). Null para líneas base o sin contexto.

Por construcción el bloque es OPCIONAL — si la línea no es de una
familia especial, el OCR lo omite y los servicios downstream lo
tratan como None. Decisión explícita: usamos ``extra="ignore"`` aquí
para que el LLM pueda devolver campos adicionales sin romper la
validación (mayor robustez frente a versiones evolutivas del prompt).
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# F-043 R2: esta lista debe coincidir EXACTAMENTE con
# ``familias.familias_linea()``, el catálogo único. El test
# ``test_f043_r2_las_familias_de_linea_del_catalogo_coinciden_con_tipo_familia``
# lo vigila: si divergen, dar de alta una familia en el catálogo la enruta en
# fase 2 y valoración pero la validación de ``ContextoLinea`` rechaza la línea
# que la lleve, y vuelven a ser dos sitios.
#
# ``generico`` es familia de documento Y de línea (diseño §1.1): una línea de
# suministro corriente —un porte de material, una pieza suelta— puede ser
# genérica dentro de un albarán de otra familia, y la IA tiene que poder
# decirlo sin que la validación se lo tumbe.
TipoFamilia = Literal[
    "generico",
    "hormigon",
    "mortero",
    "combustible",
    "alquiler_maquinaria",
    "residuos",
    "otro",
]

RolLinea = Literal[
    "base",
    "extra_tiempo",
    "transporte",
    "recargo_horario",
    "desplazamiento",
    "operario",
    "otro",
]


class ContextoLinea(BaseModel):
    """Bloque opcional con info estructural de la línea.

    A diferencia de ``StrictSchemaModel`` (que usa ``extra='forbid'``),
    este modelo tolera campos extra para que variaciones del prompt o
    respuestas "creativas" del LLM no invaliden toda la línea.
    """

    model_config = ConfigDict(extra="ignore")

    tipo_familia: Optional[TipoFamilia] = Field(default=None)
    rol_linea: Optional[RolLinea] = Field(default=None)
    descripcion_extendida: Optional[str] = Field(default=None)
    notas_tiempo: Optional[str] = Field(default=None)
    ref_linea_base: Optional[int] = Field(default=None)

    # --- Familia 'residuos' (gestor de contenedores / RCD) ---
    # Solo se rellenan cuando tipo_familia == "residuos". El
    # documento de residuos (Art. 5 RD 553/2020) trae por línea un
    # código LER y, a veces, volumen y/o peso. La valoración va por
    # CONTENEDOR (tamaño en m³ definido en el contrato); m³ y Tn se
    # guardan para trabajos posteriores. Ver estrategia de residuos.
    codigo_ler: Optional[str] = Field(
        default=None,
        description=(
            "Código LER de 6 dígitos del residuo (p.ej. '170504', "
            "'170203'). Su sola presencia identifica la línea como "
            "residuos. Sin espacios ni puntos."
        ),
    )
    volumen_m3: Optional[float] = Field(
        default=None,
        description="Volumen del residuo en metros cúbicos (m³).",
    )
    peso_toneladas: Optional[float] = Field(
        default=None,
        description="Peso del residuo en toneladas (Tn).",
    )

    # --- Familia 'mortero' / 'hormigon' (central de mortero u
    # hormigon). Muchos albaranes marcan si el camion salio con la
    # CARGA INCOMPLETA (sello/casilla "CARGAS INCOMPLETAS"), lo que
    # puede afectar a la valoracion. True si el albaran lo indica.
    # (jul 2026, residuos) Contenedores del albaran: el numero
    # EXPLICITO si el documento lo imprime, y las "unidades
    # llevadas/entregadas" y "retiradas" cuando aparecen (la resta
    # llevadas-retiradas puede dar el numero; ESA cuenta la hace la
    # valoracion, aqui solo se capturan los datos).
    contenedores: Optional[float] = Field(
        default=None,
        description=(
            "Numero de contenedores EXPLICITO impreso en el albaran "
            "de residuos. null si el documento no lo indica."
        ),
    )
    contenedores_entregados: Optional[float] = Field(
        default=None,
        description=(
            "Unidades de contenedor LLEVADAS/ENTREGADAS en obra segun "
            "el albaran ('unidad llevada'). null si no consta."
        ),
    )
    contenedores_retirados: Optional[float] = Field(
        default=None,
        description=(
            "Unidades de contenedor RETIRADAS de obra segun el "
            "albaran ('unidad retirada'). null si no consta."
        ),
    )
    carga_incompleta: Optional[bool] = Field(
        default=None,
        description=(
            "True si el albaran indica que el camion salio con la "
            "carga incompleta (sello/casilla 'cargas incompletas'). "
            "null si no aplica o no consta."
        ),
    )
    # (jul 2026, feedback JO Horpresol) m3 del pedido que el camion
    # NO llego a transportar ("M3 NO TRANSPORTADOS" del cuadro del
    # albaran de hormigon). Sirve a la valoracion (M7-C) cuando el
    # contrato tarifa expresamente los m3 no transportados.
    m3_no_transportados: Optional[float] = Field(
        default=None,
        description=(
            "m3 no transportados declarados por el albaran de "
            "hormigon/mortero (cuadro 'M3 NO TRANSPORTADOS'). "
            "null si no consta o es 0."
        ),
    )
    # (jul 2026) Minutos de exceso de descarga DECLARADOS por el
    # propio albaran ("HORA DE EXCESO 01:43:00" -> 103). Cuando
    # existe, la valoracion (M6.0) lo usa tal cual, sin recalcular.
    exceso_declarado_min: Optional[float] = Field(
        default=None,
        description=(
            "Minutos de exceso de descarga que el albaran declara "
            "explicitamente (convertidos de HH:MM(:SS)). null si "
            "el albaran no declara exceso."
        ),
    )
