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
from ruesma_comun.proveedores.identificador import normalizar_cif as _cif_comparable

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

    # (F-115 R19) El CIF se compara con ``normalizar_cif`` de comun en los
    # dos lados: ``b-123``, ``B 123`` y ``ESB123`` son el mismo proveedor y
    # no desfasan la búsqueda.
    coincide = (
        _cif_comparable(cif_actual) == _cif_comparable(rastro.cif)
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


def hay_datos_para_buscar(cif: str | None, obra: str | None) -> bool:
    """¿Hay algo con lo que sv3 pueda buscar (y sellar el rastro)?

    CR-C3: con CIF y obra ambos vacíos, sv3 descarta el mensaje de
    re-búsqueda sin sellar nada, así que relanzar al guardar publicaría en
    cada «Guardar» sin dejar nunca rastro. Basta con que haya uno de los
    dos: sv3 sella ``sin_datos`` y a partir de ahí rige la regla normal.
    """
    return bool((cif or "").strip() or (obra or "").strip())


#: (F-115 R11) Qué dice el aviso cuando el guardado quitó el contrato.
CAMBIO_PROVEEDOR = "proveedor"
CAMBIO_OBRA = "obra"


def cambio_de_cabecera(
    cif_actual: str | None, vista: BusquedaContratosVista | None,
) -> str:
    """(F-115 R11, R15) ¿Qué cambió respecto a la última búsqueda? El CIF
    (comparado con ``normalizar_cif`` de comun) ⇒ ``proveedor``; si no, la
    obra. Sin rastro con CIF, ``proveedor``."""
    if vista is not None and vista.cif and _cif_comparable(cif_actual) == _cif_comparable(vista.cif):
        return CAMBIO_OBRA
    return CAMBIO_PROVEEDOR


def _aviso_contrato_retirado(codigo: str, cambio: str | None) -> str:
    if cambio == CAMBIO_OBRA:
        return (
            f"Obra cambiada: se ha quitado el contrato {codigo} y se buscan los "
            "contratos del mismo proveedor en la nueva obra; después se vuelve a valorar"
        )
    return (
        f"Proveedor cambiado: se ha quitado el contrato {codigo} y se buscan los "
        "contratos del nuevo proveedor; después se vuelve a valorar"
    )


def aviso_de_guardado(
    *,
    aprobado: bool,
    busqueda: ContratoRefetchOutcome | None,
    contrato_retirado: str | None = None,
    cambio: str | None = None,
) -> tuple[str, bool]:
    """Mensaje del «Guardar» del portal y si la ficha debe marcar «buscando…».

    ``busqueda`` es el outcome de la re-búsqueda que relanzó el guardado
    (D4-A) o ``None`` si no se relanzó. «Buscando…» solo tiene sentido
    cuando la búsqueda va por cola (``queued``): con el fallback local
    síncrono el resultado ya está en BBDD al recargar.

    (F-115 R11) Si el guardado quitó un contrato (``contrato_retirado``) y
    relanzó la búsqueda, lo dice: «Proveedor cambiado: …» (u «Obra
    cambiada: …» si lo que cambió fue la obra, ``cambio``).
    """
    mensaje = "Documento guardado y aprobado" if aprobado else "Documento guardado"
    if busqueda is None:
        return mensaje, False
    if contrato_retirado:
        base = f"{mensaje}. {_aviso_contrato_retirado(contrato_retirado, cambio)}"
        if busqueda.status == "queued":
            return base, True
        return f"{base}. {busqueda.message}", False
    if busqueda.status == "queued":
        aviso = f"{mensaje}. Buscando contratos con el CIF y la obra guardados…"
        return aviso, True
    return f"{mensaje}. {busqueda.message}", False
