# application/services/busqueda_contratos.py
"""Estado de la búsqueda de contratos de un albarán (F-052 R27).

El bloque de contrato de la ficha decía «No se encontró ningún contrato
para CIF X + obra Y» con el CIF y la obra ACTUALES, aunque la búsqueda se
hubiera hecho con otros (el revisor cambió el CIF y guardó) o hubiera
fallado. Aquí se decide, con una función pura, qué puede afirmar el
bloque a partir del rastro de la última búsqueda (R20–R22).
"""
from __future__ import annotations

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
from ruesma_comun.obras import normalizar_codigo_obra

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
        and normalizar_codigo_obra(obra_actual) == rastro.obra
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
    """D4-A: ¿«Guardar» relanza la búsqueda de contratos?

    - ``desfasada``: CIF u obra distintos (normalizados) de los del último
      rastro ⇒ sí.
    - ``sin_rastro`` (O-C1, decisión del humano del 2026-10-01): documento
      anterior al despliegue ⇒ sí, una vez. La búsqueda deja rastro (aunque
      sea ``sin_datos`` si la obra o el CIF no valen), así que el siguiente
      «Guardar» ya sigue la regla normal y no hay bucle.
    - Cualquier otro estado ⇒ no. ``None`` (vistas de proveedor) ⇒ no.
    """
    return vista is not None and vista.estado in (
        ESTADO_BUSQUEDA_DESFASADA,
        ESTADO_BUSQUEDA_SIN_RASTRO,
    )


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
        aviso = f"{mensaje}. Buscando contratos con el CIF y la obra guardados…"
        return aviso, True
    return f"{mensaje}. {busqueda.message}", False
