# tests/test_f069_worker.py
"""F-069 · T11 · el peor caso de un mensaje cuenta las lecturas de la
resolución (R19).

Una petición nueva lee ``dbo.usu`` hasta dos veces (Entrada y Login) y
``dbo.emp`` hasta dos (Entrada y correo), cada una con sus reintentos (R24).
F-053 no contaba la de ``dbo.usu``. Sin red ni BBDD.
"""
from __future__ import annotations

import main_worker
from tests.test_f053_worker import _settings, _visibilidad_con


def _con_reintentos(t_sigrid: float) -> float:
    """3 intentos y esperas de 1 s y 2 s (tenacity), contado a mano."""
    return 3 * t_sigrid + 1 + 2


def _peor_caso_f053(t_sigrid: float, t_graph: float) -> float:
    pdf = (5 * t_graph + 4 * 20) + 4 * t_graph
    return 3 * _con_reintentos(t_sigrid) + 240 + pdf


def test_f069_r19_peor_caso_con_dos_lecturas_de_usu_y_dos_de_emp(monkeypatch):
    # 1409 de F-053 + 4 × 183 = 2141.
    esperado = _peor_caso_f053(60, 60) + 4 * _con_reintentos(60)
    assert esperado == 2141
    assert main_worker.peor_caso_mensaje_s(_settings(monkeypatch)) == esperado


def test_f069_r19_visibilidad_con_los_defectos(monkeypatch, tmp_path):
    # (2141 + 300) = 2441 → 41 min = 2460 s.
    assert _visibilidad_con(monkeypatch, tmp_path) == 2460


def test_f069_r19_sigue_al_timeout_configurado(monkeypatch, tmp_path):
    # t_sigrid 71: 1508 de F-053 + 4 × 216 = 2372; + 300 = 2672 → 45 min = 2700 s.
    ajustes = _settings(monkeypatch, SIGRID_API_TIMEOUT_S="71")
    assert main_worker.peor_caso_mensaje_s(ajustes) == 2372
    assert _visibilidad_con(monkeypatch, tmp_path, SIGRID_API_TIMEOUT_S="71") == 2700
