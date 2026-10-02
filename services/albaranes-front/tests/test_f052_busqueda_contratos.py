# tests/test_f052_busqueda_contratos.py
"""F-052 R27 · qué mensaje toca en el bloque de contrato lo decide una función pura.

``estado_busqueda(cif_actual, obra_actual, rastro)`` compara los datos que
hay HOY en el albarán con el rastro de la última búsqueda de contratos que
sella sv3 (o el fallback local de sv4) y devuelve uno de cinco estados:

- ``sin_rastro``: documento anterior a F-052 (las cuatro columnas a NULL)
  o un resultado que sv4 no conoce: no consta con qué se buscó.
- ``desfasada``: el CIF o la obra actuales NO son los del rastro; los datos
  actuales todavía no se han buscado. Manda sobre el resultado.
- ``error``: coinciden y la última búsqueda falló.
- ``sin_datos``: coinciden y no se buscó porque faltaba CIF u obra.
- ``vigente``: coinciden y la búsqueda funcionó (``encontrados``/``ninguno``).

Normalización, la misma con la que sella sv3: CIF sin espacios y en
mayúsculas; obra con ``ruesma_comun.obras.normalizar_codigo_obra``, la de sv3 (``691`` = ``0691``).

Sin red ni BBDD.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from application.services.busqueda_contratos import estado_busqueda
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

FECHA = "2026-09-30T10:15:00+00:00"


def _rastro(cif, obra, resultado, at_utc=FECHA):
    return RastroBusquedaContratos(
        cif=cif, obra=obra, resultado=resultado, at_utc=at_utc,
    )


# (cif_actual, obra_actual, rastro, estado esperado)
CASOS = [
    # --- sin rastro --------------------------------------------------- #
    ("B82899550", "0691", None, ESTADO_BUSQUEDA_SIN_RASTRO),
    ("B82899550", "0691", _rastro(None, None, None, None),
     ESTADO_BUSQUEDA_SIN_RASTRO),
    ("B82899550", "0691", _rastro("B82899550", "0691", "desconocido"),
     ESTADO_BUSQUEDA_SIN_RASTRO),
    # --- vigente: coinciden normalizados ------------------------------ #
    ("B82899550", "0691", _rastro("B82899550", "0691", BUSQUEDA_NINGUNO),
     ESTADO_BUSQUEDA_VIGENTE),
    ("B 82899550", "0691", _rastro("B82899550", "0691", BUSQUEDA_NINGUNO),
     ESTADO_BUSQUEDA_VIGENTE),
    ("b82899550 ", " 691", _rastro("B82899550", "0691", BUSQUEDA_NINGUNO),
     ESTADO_BUSQUEDA_VIGENTE),
    ("B82899550", "691", _rastro("B82899550", "0691", BUSQUEDA_ENCONTRADOS),
     ESTADO_BUSQUEDA_VIGENTE),
    # --- desfasada: cambia el CIF o la obra --------------------------- #
    ("B82890580", "0691", _rastro("B82899550", "0691", BUSQUEDA_NINGUNO),
     ESTADO_BUSQUEDA_DESFASADA),
    ("B82899550", "0696", _rastro("B82899550", "0691", BUSQUEDA_NINGUNO),
     ESTADO_BUSQUEDA_DESFASADA),
    ("B82899550", None, _rastro("B82899550", "0691", BUSQUEDA_ENCONTRADOS),
     ESTADO_BUSQUEDA_DESFASADA),
    (None, "0691", _rastro("B82899550", "0691", BUSQUEDA_ENCONTRADOS),
     ESTADO_BUSQUEDA_DESFASADA),
    # el desfase manda sobre el resultado (los datos de hoy no se buscaron)
    ("B82890580", "0691", _rastro("B82899550", "0691", BUSQUEDA_ERROR),
     ESTADO_BUSQUEDA_DESFASADA),
    # se buscó sin datos y ahora sí los hay
    ("B82899550", "0691", _rastro("B82899550", None, BUSQUEDA_SIN_DATOS),
     ESTADO_BUSQUEDA_DESFASADA),
    # --- error y sin_datos, coincidiendo ------------------------------- #
    ("B82899550", "0691", _rastro("B82899550", "0691", BUSQUEDA_ERROR),
     ESTADO_BUSQUEDA_ERROR),
    ("B82899550", "abc", _rastro("B82899550", None, BUSQUEDA_SIN_DATOS),
     ESTADO_BUSQUEDA_SIN_DATOS),
    ("  ", "", _rastro(None, None, BUSQUEDA_SIN_DATOS),
     ESTADO_BUSQUEDA_SIN_DATOS),
]


@pytest.mark.parametrize(
    ("cif_actual", "obra_actual", "rastro", "esperado"),
    CASOS,
    ids=[f"{i:02d}-{c[3]}" for i, c in enumerate(CASOS)],
)
def test_f052_r27_estado_busqueda_tabla_de_casos(
    cif_actual, obra_actual, rastro, esperado,
):
    vista = estado_busqueda(cif_actual, obra_actual, rastro)
    assert isinstance(vista, BusquedaContratosVista)
    assert vista.estado == esperado


def test_f052_r27_b_82899550_es_b82899550_y_691_es_0691():
    """Los dos ejemplos literales de ``tasks.md`` (T12)."""
    rastro = _rastro("B82899550", "0691", BUSQUEDA_NINGUNO)
    assert estado_busqueda("B 82899550", "691", rastro).estado == (
        ESTADO_BUSQUEDA_VIGENTE
    )


def test_f052_r27_la_vista_lleva_lo_que_se_busco_no_lo_actual():
    """El bloque dice CON QUÉ se buscó: CIF, obra, fecha y resultado del rastro."""
    rastro = _rastro("B82899550", "0691", BUSQUEDA_NINGUNO)
    vista = estado_busqueda("B82890580", "0696", rastro)
    assert vista == BusquedaContratosVista(
        estado=ESTADO_BUSQUEDA_DESFASADA,
        cif="B82899550",
        obra="0691",
        fecha=FECHA,
        resultado=BUSQUEDA_NINGUNO,
    )


def test_f052_r27_sin_rastro_no_inventa_datos():
    vista = estado_busqueda("B82899550", "0691", None)
    assert vista == BusquedaContratosVista(estado=ESTADO_BUSQUEDA_SIN_RASTRO)


def test_f052_r27_sin_fecha_pero_con_resultado_sigue_siendo_rastro():
    """La fecha no decide el estado: el resultado sí."""
    rastro = _rastro("B82899550", "0691", BUSQUEDA_ERROR, at_utc=None)
    vista = estado_busqueda("B82899550", "0691", rastro)
    assert vista.estado == ESTADO_BUSQUEDA_ERROR
    assert vista.fecha is None


def test_f052_r27_los_resultados_se_escriben_como_los_sella_sv3():
    """sv4 no puede importar sv3 (dos paquetes ``domain`` de primer nivel):
    lo que ata las dos puntas es el literal. Si sv3 renombra un resultado,
    cae este test en vez del mensaje del bloque de contrato."""
    fuente = (
        Path(__file__).resolve().parents[2]
        / "albaranes-persistencia" / "domain" / "models" / "contrato_models.py"
    ).read_text(encoding="utf-8")
    literales = dict(re.findall(r'^(BUSQUEDA_[A-Z_]+) = "([a-z_]+)"', fuente, re.MULTILINE))
    assert literales == {
        "BUSQUEDA_ENCONTRADOS": BUSQUEDA_ENCONTRADOS,
        "BUSQUEDA_NINGUNO": BUSQUEDA_NINGUNO,
        "BUSQUEDA_ERROR": BUSQUEDA_ERROR,
        "BUSQUEDA_SIN_DATOS": BUSQUEDA_SIN_DATOS,
    }


# --------------------------------------------------------------------- #
# CR-C1 (review del Bloque C): la obra se compara con la MISMA
# normalización con la que sv3 sella el rastro (`ruesma_comun.obras`).
# Antes sv4 usaba la suya (`^\d{1,4}$` + zfill): `12` era `0012` para sv4
# y `None` para sv3, así que un rastro `sin_datos` salía `desfasada` y cada
# «Guardar» volvía a publicar en q-persistencia.
# --------------------------------------------------------------------- #
@pytest.mark.parametrize("obra", ["12", "7", "1234", "1001", "12345", "abc", ""])
def test_f052_cr_c1_obra_que_sv3_no_admite_es_sin_datos_no_desfase(obra):
    from application.services.busqueda_contratos import debe_relanzar_busqueda

    rastro = _rastro("B82899550", None, BUSQUEDA_SIN_DATOS)
    vista = estado_busqueda("B82899550", obra, rastro)
    assert vista.estado == ESTADO_BUSQUEDA_SIN_DATOS
    assert not debe_relanzar_busqueda(vista)


@pytest.mark.parametrize("obra", ["0691", "691", " 0691 "])
def test_f052_cr_c1_obra_valida_coincide_con_el_sello_de_sv3(obra):
    rastro = _rastro("B82899550", "0691", BUSQUEDA_NINGUNO)
    assert estado_busqueda("B82899550", obra, rastro).estado == (
        ESTADO_BUSQUEDA_VIGENTE
    )


def test_f052_cr_c1_sv3_y_sv4_usan_la_misma_pieza_de_ruesma_comun():
    """Una sola normalización de obra: sin copias locales en sv3 ni en sv4."""
    servicios = Path(__file__).resolve().parents[2]
    for copia in (
        servicios / "albaranes-front" / "application" / "services" / "obra_code_normalizer.py",
        servicios / "albaranes-persistencia" / "application" / "services" / "obra_code_normalizer.py",
    ):
        assert not copia.exists(), f"copia local de la normalización: {copia}"
    for usuario in (
        servicios / "albaranes-persistencia" / "application" / "services" / "contrato_enrichment_service.py",
        servicios / "albaranes-front" / "application" / "services" / "busqueda_contratos.py",
        servicios / "albaranes-front" / "infrastructure" / "sigrid" / "local_refetch_client.py",
    ):
        fuente = usuario.read_text(encoding="utf-8")
        assert "from ruesma_comun.obras import normalizar_codigo_obra" in fuente, usuario
