# tests/test_f053_v8_equivalentes.py
"""F-053 v8 · T50 (pasada 2, RM5): demostración EJECUTABLE de los equivalentes de
sv4 de la campaña de la v8 (``progress/mutacion_F-053_v8.md``, #38 y #50).

Patrón de ``services/albaranes-alta-sigrid/tests/test_f053_t25_equivalentes.py``:
se carga el módulo REAL, se fabrica su variante con el texto exacto del mutante
y se comparan las dos sobre un dominio amplio; cada grupo lleva un CONTROL no
equivalente que sí se detecta (la comparación no es ciega). Las dos versiones
salen de la MISMA fuente normalizada: si una campaña ha inyectado el equivalente
en el fichero, primero se devuelve la línea a su forma original.
"""
from __future__ import annotations

import itertools
import sys
import types
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient
from test_f053_t18_publicar import ACTIVA, _Orquestador, _Repo

import domain.services.alta_sigrid as alta_mod
import interface_adapters.web.app as app_mod
from application.services.review_service import ReviewService
from config.settings import Settings
from domain.models.alta_sigrid_models import AltaSigridVista, ConfigAltaSigrid


def fuente_normalizada(modulo: types.ModuleType, original: str, *mutados: str) -> str:
    fuente = Path(modulo.__file__).read_text(encoding="utf-8").replace("\r\n", "\n")
    for mutado in mutados:
        fuente = fuente.replace(mutado, original)
    assert fuente.count(original) == 1, "la línea cambió: rehacer la justificación"
    return fuente


def cargar(modulo: types.ModuleType, fuente: str, *cambios: tuple[str, str]) -> types.ModuleType:
    for de, a in cambios:
        assert fuente.count(de) == 1, f"no está (o se repite): {de!r}"
        fuente = fuente.replace(de, a)
    nombre = f"{modulo.__name__}__variante_{abs(hash(fuente))}"
    nuevo = types.ModuleType(nombre)
    nuevo.__file__ = modulo.__file__
    sys.modules[nombre] = nuevo
    try:
        exec(compile(fuente, modulo.__file__, "exec"), nuevo.__dict__)  # noqa: S102
    finally:
        sys.modules.pop(nombre, None)
    return nuevo


# =================================================================== #
# #50 · domain/services/alta_sigrid.py · quitar ``not config.activa``
# =================================================================== #
ORIGINAL_50 = "    if not config.activa or not aprobado or not activo:\n        return False\n    aprobado_en"
MUTADO_50 = "    if not aprobado or not activo:\n        return False\n    aprobado_en"
CONTROL_50 = ("aprobado_en < config.desde)", "aprobado_en <= config.desde)")

DESDE = datetime(2026, 10, 1, tzinfo=UTC)
FECHAS = [None, "ilegible", "", "2026-09-30T23:59:59+00:00", "2026-10-01T00:00:00+00:00",
          "2026-10-01T00:00:00Z", "2026-10-05T10:00:00+00:00", "2026-10-05T10:00:00"]
ALTAS = [None, AltaSigridVista(estado="registrado", modo="real", adjunto_estado="error"),
         AltaSigridVista(estado="registrado", modo="real", adjunto_estado="colgado"),
         AltaSigridVista(estado="error"), AltaSigridVista(estado="incierto")]
AHORA = datetime(2026, 10, 8, tzinfo=UTC)


def _salidas_50(modulo) -> list:
    salidas = []
    for desde, aprobado, activo, fecha, alta in itertools.product(
            (None, DESDE), (True, False), (True, False), FECHAS, ALTAS):
        config = ConfigAltaSigrid(desde=desde)
        comun = {"aprobado": aprobado, "activo": activo, "approved_at_utc": fecha,
                 "alta": alta, "config": config}
        salidas.append((
            modulo._documento_admite_alta(aprobado=aprobado, activo=activo,
                                          approved_at_utc=fecha, config=config),
            modulo.puede_reintentar_adjunto(**comun),
            modulo.puede_solicitar_alta(**comun, ahora=AHORA),
        ))
    return salidas


def test_f053_v8_equivalente_50_activa_es_desde_no_vacia():
    fuente = fuente_normalizada(alta_mod, ORIGINAL_50, MUTADO_50)
    original = cargar(alta_mod, fuente)
    mutante = cargar(alta_mod, fuente, (ORIGINAL_50, MUTADO_50))
    control = cargar(alta_mod, fuente, CONTROL_50)
    base = _salidas_50(original)
    assert len(base) == 2 * 2 * 2 * len(FECHAS) * len(ALTAS)
    assert any(any(fila) for fila in base)            # el dominio no es todo «no»
    assert _salidas_50(mutante) == base               # equivalente
    distintas = sum(a != b for a, b in zip(_salidas_50(control), base, strict=True))
    assert distintas > 0                              # el control sí se nota


# =================================================================== #
# #38 · interface_adapters/web/app.py · ``if propuesto and propuesto.strip()``
# → ``if propuesto`` (con DEFAULT_REVIEWER recortado, cambio 3 de la review)
# =================================================================== #
ORIGINAL_38 = "        if propuesto and propuesto.strip():\n            return propuesto.strip()"
MUTADO_38 = "        if propuesto:\n            return propuesto.strip()"
CONTROL_38 = (ORIGINAL_38, "        if propuesto and propuesto.strip():\n            return propuesto")


class _RepoEq(_Repo):
    def initialize(self):
        return True


class _Publicador:
    def publicar(self, nombre_cola, mensaje):
        return True


def _salidas_38(modulo) -> list:
    """Lo que queda en el merge y lo que se publica, por los dos caminos, sobre
    cabecera × formulario/cuerpo × ``DEFAULT_REVIEWER``."""
    salidas = []
    cabeceras = [None, "", "   ", "ana@ruesma.es", " ana@ruesma.es "]
    propuestos = [None, "", "   ", "pepe", "  pepe  "]
    defectos = [None, "", "   ", "revisor", " revisor "]
    for defecto in defectos:
        repo, orq = _RepoEq(paso=True), _Orquestador()
        servicio = ReviewService(repo, defecto, orq, ACTIVA)
        modulo.SessionFactory = lambda **_: object()
        modulo.AlbaranReviewRepository = lambda *_: object()
        modulo.WorkflowRunsPurger = lambda *_: object()
        modulo.ReviewService = lambda *_: servicio
        modulo.construir_publicador = lambda **_: _Publicador()
        ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x",
                                           default_reviewer=defecto)
        cliente = TestClient(modulo.build_app(ajustes), follow_redirects=False)
        for cabecera, propuesto in itertools.product(cabeceras, propuestos):
            cabeceras_http = {} if cabecera is None else {"X-MS-CLIENT-PRINCIPAL-NAME": cabecera}
            datos = {} if propuesto is None else {"approved_by": propuesto}
            cuerpo = {"approved": True, **datos}
            cliente.post("/documents/d/approve", data=datos, headers=cabeceras_http)
            cliente.put("/api/documents/d", json=cuerpo, headers=cabeceras_http)
        salidas.append((
            [a[2] for a in repo.aprobaciones],
            [p.approved_by for p in repo.guardados],
            [a["approved_by"] for a in orq.aprobados],
        ))
    return salidas


def test_f053_v8_equivalente_38_propuesto_en_blanco_acaba_en_el_defecto():
    fuente = fuente_normalizada(app_mod, ORIGINAL_38, MUTADO_38)
    base = _salidas_38(cargar(app_mod, fuente))
    assert all(len(merge) == 25 and len(mensajes) == 50 for merge, _, mensajes in base)
    assert _salidas_38(cargar(app_mod, fuente, (ORIGINAL_38, MUTADO_38))) == base
    control = _salidas_38(cargar(app_mod, fuente, CONTROL_38))
    assert sum(a != b for a, b in zip(control, base, strict=True)) > 0
