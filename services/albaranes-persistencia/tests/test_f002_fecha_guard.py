# tests/test_f002_fecha_guard.py
"""F-002 · Guard de año: fecha del albarán vs recepción del email
(R13, R14, R15, R16, R17).

Caso de referencia: un albarán fechado en 2023 llegando en un correo de
2026 — casi siempre un error de lectura del año, y hoy se persiste tal
cual. Sin red ni BBDD: el repositorio es un doble.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from application.services.fecha_guard_service import (
    NOTA_FECHA_PREFIJO,
    FechaGuardService,
)

DOC = "doc-1"


class RepoFechasFake:
    def __init__(
        self,
        *,
        fecha: str | None,
        recibido: str | None,
        falla_lectura: bool = False,
        falla_marca: bool = False,
    ) -> None:
        self._fecha = fecha
        self._recibido = recibido
        self._falla_lectura = falla_lectura
        self._falla_marca = falla_marca
        self.lecturas = 0
        self.marcas: list[tuple[str, str, str]] = []

    def get_merge_fechas_para_guard(self, *, document_id: str):
        self.lecturas += 1
        if self._falla_lectura:
            raise RuntimeError("BBDD caida")
        return self._fecha, self._recibido

    def marcar_revision_cabecera(
        self, *, document_id: str, motivo: str, nota: str, nota_prefijo: str,
    ) -> None:
        if self._falla_marca:
            raise RuntimeError("BBDD caida")
        self.marcas.append((motivo, nota, nota_prefijo))


def _servicio(repo, **kwargs) -> FechaGuardService:
    return FechaGuardService(repository=repo, **kwargs)


# ---------------------------------------------------------------- #
# R13 — más de FECHA_GUARD_MAX_DIAS de distancia -> revisión.
# ---------------------------------------------------------------- #
def test_f002_r13_albaran_de_2023_en_correo_de_2026_va_a_revision() -> None:
    repo = RepoFechasFake(fecha="2023-05-10", recibido="2026-08-12T09:00:00Z")

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert len(repo.marcas) == 1
    motivo, nota, prefijo = repo.marcas[0]
    assert motivo == "fecha_albaran_fuera_de_rango:2023-05-10"
    assert prefijo == NOTA_FECHA_PREFIJO
    assert nota.startswith(NOTA_FECHA_PREFIJO)
    assert "2023-05-10" in nota


def test_f002_r13_fecha_muy_posterior_tambien_va_a_revision() -> None:
    """El guard es simétrico: un año leído de más es igual de erróneo."""
    repo = RepoFechasFake(fecha="2028-01-15", recibido="2026-08-12T09:00:00Z")

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert repo.marcas and repo.marcas[0][0] == (
        "fecha_albaran_fuera_de_rango:2028-01-15"
    )


def test_f002_r13_dentro_del_margen_no_marca_nada() -> None:
    repo = RepoFechasFake(fecha="2026-07-30", recibido="2026-08-12T09:00:00Z")

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert repo.marcas == []


def test_f002_r13_el_borde_exacto_no_marca() -> None:
    """`distan MÁS de max_dias`: 365 días justos siguen siendo válidos."""
    repo = RepoFechasFake(fecha="2025-08-12", recibido="2026-08-12T09:00:00Z")

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert repo.marcas == []


def test_f002_r13_un_dia_mas_alla_del_borde_marca() -> None:
    repo = RepoFechasFake(fecha="2025-08-11", recibido="2026-08-12T09:00:00Z")

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert len(repo.marcas) == 1


def test_f002_r13_max_dias_configurable() -> None:
    repo = RepoFechasFake(fecha="2026-06-12", recibido="2026-08-12T09:00:00Z")

    _servicio(repo, max_dias=30).check_merge_document(merge_document_id=DOC)

    assert len(repo.marcas) == 1


@pytest.mark.parametrize(
    "recibido",
    ["2026-08-12", "2026-08-12T09:00:00Z", "2026-08-12T09:00:00+00:00"],
)
def test_f002_r13_acepta_los_formatos_de_recepcion_reales(recibido: str) -> None:
    """``email_received_datetime`` llega de Graph con zona horaria; el
    guard se queda con la parte de fecha."""
    repo = RepoFechasFake(fecha="2023-05-10", recibido=recibido)

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert len(repo.marcas) == 1


# ---------------------------------------------------------------- #
# R14 — sin fecha de email, la referencia es hoy (UTC).
# ---------------------------------------------------------------- #
def test_f002_r14_sin_fecha_de_email_usa_hoy_como_referencia() -> None:
    hace_cinco_anios = (date.today() - timedelta(days=5 * 365)).isoformat()
    repo = RepoFechasFake(fecha=hace_cinco_anios, recibido=None)

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert repo.marcas and repo.marcas[0][0] == (
        f"fecha_albaran_fuera_de_rango:{hace_cinco_anios}"
    )


def test_f002_r14_sin_fecha_de_email_un_albaran_reciente_no_marca() -> None:
    repo = RepoFechasFake(fecha=date.today().isoformat(), recibido=None)

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert repo.marcas == []


def test_f002_r14_fecha_de_email_ilegible_cae_a_hoy() -> None:
    repo = RepoFechasFake(fecha=date.today().isoformat(), recibido="ayer")

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert repo.marcas == []


# ---------------------------------------------------------------- #
# R15 — sin fecha utilizable, el guard no actúa.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    "fecha", [None, "", "   ", "10/05/2023", "no es una fecha", "2023-13-45"],
)
def test_f002_r15_fecha_nula_o_no_parseable_es_no_op(fecha) -> None:
    repo = RepoFechasFake(fecha=fecha, recibido="2026-08-12T09:00:00Z")

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert repo.marcas == []


# ---------------------------------------------------------------- #
# R16 — best-effort.
# ---------------------------------------------------------------- #
def test_f002_r16_error_leyendo_las_fechas_no_rompe() -> None:
    repo = RepoFechasFake(fecha=None, recibido=None, falla_lectura=True)

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert repo.marcas == []


def test_f002_r16_error_marcando_revision_no_rompe() -> None:
    repo = RepoFechasFake(
        fecha="2023-05-10", recibido="2026-08-12T09:00:00Z", falla_marca=True,
    )

    _servicio(repo).check_merge_document(merge_document_id=DOC)

    assert repo.marcas == []


# ---------------------------------------------------------------- #
# R17 — guard apagado.
# ---------------------------------------------------------------- #
def test_f002_r17_guard_apagado_no_lee_ni_marca() -> None:
    repo = RepoFechasFake(fecha="2023-05-10", recibido="2026-08-12T09:00:00Z")

    _servicio(repo, enabled=False).check_merge_document(merge_document_id=DOC)

    assert repo.lecturas == 0
    assert repo.marcas == []


# ---------------------------------------------------------------- #
# El guard tiene que estar EN el pipeline, no solo existir.
# ---------------------------------------------------------------- #
class GuardEspia:
    def __init__(self, *, revienta: bool = False) -> None:
        self.revienta = revienta
        self.llamadas: list[str] = []

    def check_merge_document(self, *, merge_document_id: str) -> None:
        self.llamadas.append(merge_document_id)
        if self.revienta:
            raise RuntimeError("guard roto")


class RepoPipelineFake:
    def get_merge_cif_and_obra(self, *, document_id: str):
        return "B50999888", "0695"


def _pipeline(guard):
    from application.pipelines.persist_albaran_pipeline import (
        PersistAlbaranPipeline,
    )

    return PersistAlbaranPipeline(
        repository=RepoPipelineFake(),
        document_storage=object(),
        normalizer=object(),
        fecha_guard_service=guard,
    )


def test_f002_r13_el_pipeline_ejecuta_el_guard_al_reenriquecer() -> None:
    guard = GuardEspia()

    assert _pipeline(guard).reenrich_by_merge_id(merge_document_id=DOC) is True
    assert guard.llamadas == [DOC]


def test_f002_r16_un_guard_que_revienta_no_rompe_el_pipeline() -> None:
    guard = GuardEspia(revienta=True)

    assert _pipeline(guard).reenrich_by_merge_id(merge_document_id=DOC) is True


def test_f002_r17_sin_guard_cableado_el_pipeline_sigue() -> None:
    assert _pipeline(None).reenrich_by_merge_id(merge_document_id=DOC) is True
