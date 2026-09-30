# application/services/busqueda_contratos.py
"""Estado de la búsqueda de contratos de un albarán (F-052 R27).

El bloque de contrato de la ficha decía «No se encontró ningún contrato
para CIF X + obra Y» con el CIF y la obra ACTUALES, aunque la búsqueda se
hubiera hecho con otros (el revisor cambió el CIF y guardó) o hubiera
fallado. Aquí se decide, con una función pura, qué puede afirmar el
bloque a partir del rastro de la última búsqueda (R20–R22).
"""
from __future__ import annotations

from application.services.obra_code_normalizer import normalize_obra_code
from domain.models.contrato_refetch_models import ContratoRefetchOutcome
from domain.models.review_models import (
    BUSQUEDA_ENCONTRADOS,
    BUSQUEDA_ERROR,
    BUSQUEDA_NINGUNO,
    BUSQUEDA_SIN_DATOS,
    ESTADO_BUSQUEDA_DESFASADA,
    ESTADO_BUSQUEDA_ERROR,
    ESTADO_BUSQUEDA_SIN_DATOS,
    ESTADO_BUSQUEDA_SIN_RASTRO,
    ESTADO_BUSQUEDA_VIGENTE,
    BusquedaContratosVista,
    RastroBusquedaContratos,
)

_ESTADO_POR_RESULTADO = {
    BUSQUEDA_ENCONTRADOS: ESTADO_BUSQUEDA_VIGENTE,
    BUSQUEDA_NINGUNO: ESTADO_BUSQUEDA_VIGENTE,
    BUSQUEDA_ERROR: ESTADO_BUSQUEDA_ERROR,
    BUSQUEDA_SIN_DATOS: ESTADO_BUSQUEDA_SIN_DATOS,
}


def normalizar_cif(cif: str | None) -> str | None:
    """CIF como lo sella sv3 en el rastro: sin espacios y en mayúsculas."""
    return (cif or "").strip().upper().replace(" ", "") or None


def estado_busqueda(
    cif_actual: str | None,
    obra_actual: str | None,
    rastro: RastroBusquedaContratos | None,
) -> BusquedaContratosVista:
    """Qué mensaje toca en el bloque de contrato.

    - Sin rastro, o con un resultado que sv4 no conoce: ``sin_rastro``
      (no consta con qué se buscó; nunca se afirma que no hay contrato).
    - CIF u obra actuales (normalizados) distintos de los del rastro:
      ``desfasada``, sea cual sea el resultado: los datos de hoy no se
      han buscado.
    - Si coinciden, lo dice el resultado: ``error``, ``sin_datos`` o
      ``vigente`` (``encontrados`` y ``ninguno``).
    """
    if rastro is None or rastro.resultado not in _ESTADO_POR_RESULTADO:
        return BusquedaContratosVista(estado=ESTADO_BUSQUEDA_SIN_RASTRO)

    coincide = (
        normalizar_cif(cif_actual) == rastro.cif
        and normalize_obra_code(obra_actual) == rastro.obra
    )
    estado = (
        _ESTADO_POR_RESULTADO[rastro.resultado]
        if coincide
        else ESTADO_BUSQUEDA_DESFASADA
    )
    return BusquedaContratosVista(
        estado=estado,
        cif=rastro.cif,
        obra=rastro.obra,
        fecha=rastro.at_utc,
        resultado=rastro.resultado,
    )


def debe_relanzar_busqueda(vista: BusquedaContratosVista | None) -> bool:
    """D4-A: «Guardar» relanza la búsqueda solo si CIF u obra cambiaron.

    «Cambiaron» = distintos (normalizados) de los del último rastro, es
    decir, estado ``desfasada``. Sin rastro no hay con qué comparar y no
    se relanza: el bloque ya dice que no consta con qué se buscó y ofrece
    «Solo volver a buscar».
    """
    return vista is not None and vista.estado == ESTADO_BUSQUEDA_DESFASADA


def aviso_de_guardado(
    *,
    aprobado: bool,
    busqueda: ContratoRefetchOutcome | None,
) -> tuple[str, bool]:
    """Mensaje del «Guardar» del portal y si la ficha debe marcar «buscando…».

    ``busqueda`` es el outcome de la re-búsqueda que relanzó el guardado
    (D4-A) o ``None`` si no se relanzó. «Buscando…» solo tiene sentido
    cuando la búsqueda va por cola (``queued``): con el fallback local
    síncrono el resultado ya está en BBDD al recargar.
    """
    mensaje = "Documento guardado y aprobado" if aprobado else "Documento guardado"
    if busqueda is None:
        return mensaje, False
    if busqueda.status == "queued":
        aviso = (
            f"{mensaje}. CIF u obra cambiados: buscando contratos con los "
            "datos nuevos…"
        )
        return aviso, True
    return f"{mensaje}. {busqueda.message}", False
