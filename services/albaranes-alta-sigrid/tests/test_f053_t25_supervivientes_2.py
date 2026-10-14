# tests/test_f053_t25_supervivientes_2.py
"""F-053 · T25 · segunda tanda: supervivientes de sv9 de la campaña completa.

Validador (orden de la petición H26, bordes de R10/R39, signo de R12),
repositorio (fechas con zona, JSON sin escapar, intentos), cliente de sigrid-api
(topes de filas, reintentos, recortes, estado del 200 inválido, adjunto caído),
composición y ``main_worker`` (visibilidad EXACTA y avisos de arranque).
Los equivalentes se justifican en ``progress/mutacion_F-053.md``.
"""
from __future__ import annotations

import json
import logging
from dataclasses import replace
from datetime import UTC, datetime

import httpx
import pytest

import main_worker
from domain.models.alta_models import ErrorAlta, Motivo, TipoFallo
from domain.services import validador_alta as v
from infrastructure.database import sql_alta_repository as repo
from tests.f053_datos import CONFIG, USU, HOY, datos, sin_vincular, vinculada
from tests.test_f053_cliente_sigrid import (
    PETICION,
    Servidor,
    _cliente,
    _json,
    _lectura,
)
from tests.test_f053_worker import _settings, _visibilidad_con


# ------------------------------------------------------------------ #
# Validador
# ------------------------------------------------------------------ #
def test_f053_t25_config_alta_es_inmutable():
    assert v.ConfigAlta.__dataclass_params__.frozen is True


def test_f053_t25_h26_orden_merge_por_line_index_y_manuales_al_final():
    con_indice_alto = sin_vincular(90, merge_line_id=7, line_index=50)
    manual = sin_vincular(3, merge_line_id=None, line_index=None)
    sin_indice = sin_vincular(4, merge_line_id=8, line_index=None)  # merge sin line_index
    ordenadas = v.lineas_a_registrar(datos(manual, sin_indice, con_indice_alto))
    assert [l.id for l in ordenadas] == [90, 3, 4]


def test_f053_t25_r10_cantidad_en_el_borde_del_cero_no_es_valida():
    linea = sin_vincular(1, cantidad_albaran=1e-9)
    resultado = v.validar_y_construir(datos(linea), CONFIG, HOY, USU)
    assert isinstance(resultado, list)
    assert ("cantidad_no_valida", "1") in [(m.codigo, m.referencia_linea) for m in resultado]


@pytest.mark.parametrize("cantidad, importe, incoherente", [
    (10.0, 0.5, False),     # importe < 1 pero positivo: coherente
    (0.5, 10.0, False),     # cantidad < 1 pero positiva: coherente
    (-2.0, 0.5, True),      # devolución con importe positivo pequeño
    (10.0, -0.5, True),
])
def test_f053_t25_r39_signos_cerca_de_uno(cantidad, importe, incoherente):
    linea = sin_vincular(1, cantidad_albaran=cantidad, importe_calculado=importe)
    resultado = v.validar_y_construir(datos(linea), CONFIG, HOY, USU)
    codigos = [m.codigo for m in resultado] if isinstance(resultado, list) else []
    assert ("signo_incoherente" in codigos) is incoherente


@pytest.mark.parametrize("importe", [-5.0, 5.0])
def test_f053_t25_r39_cantidad_cero_no_es_signo_incoherente(importe):
    """``_motivos_r39`` por sí sola (defensa: R10 ya rechaza la cantidad 0)."""
    linea = sin_vincular(1, cantidad_albaran=0.0, importe_calculado=importe)
    assert v._motivos_r39(datos(linea), HOY) == []


def test_f053_t25_r39_vinculada_sin_convertida_no_rompe():
    """``_motivos_r39`` por sí sola con una vinculada sin cantidad convertida."""
    linea = vinculada(1, cantidad_convertida=None)
    assert v._motivos_r39(datos(linea), HOY) == []


def test_f053_t25_r12_importe_positivo_pequeno_mantiene_el_signo():
    linea = sin_vincular(1, cantidad_albaran=1.0, importe_calculado=0.5)
    peticion = v.validar_y_construir(datos(linea), CONFIG, HOY, USU)
    (pedida,) = peticion.lineas
    assert pedida.cantidad == 1.0 and pedida.precio == 0.5


# ------------------------------------------------------------------ #
# Repositorio
# ------------------------------------------------------------------ #
def test_f053_t25_fecha_con_zona_se_pasa_a_utc():
    assert repo.leer_instante("2026-10-05T12:00:00+02:00") == datetime(2026, 10, 5, 10, 0, tzinfo=UTC)


def test_f053_t25_json_sin_escapar():
    assert repo._volcar({"detalle": "año"}) == '{"detalle": "año"}'
    historial = repo._con_entrada(None, datetime(2026, 10, 8, tzinfo=UTC), v.EstadoAlta.ERROR,
                                  None, (Motivo("ñandú"),))
    assert "ñandú" in historial


def test_f053_t25_intentos_nulos_son_cero():
    alta = repo._alta_de_fila({"estado": "error", "intentos": None})
    assert alta.intentos == 0


# ------------------------------------------------------------------ #
# Cliente de sigrid-api
# ------------------------------------------------------------------ #
def test_f053_t25_topes_de_filas_de_las_lecturas():
    servidor = Servidor(_lectura([]), _lectura([], columnas=("ide",)))
    cliente = _cliente(servidor)
    cliente.buscar_albaranes("B1", "N", "ALB-d")
    cliente.existe_concepto(5)
    assert [c["max_rows"] for c in servidor.cuerpos()] == [50, 2]


def test_f053_t25_un_intento_es_un_intento():
    servidor = Servidor(httpx.ConnectError("caído"), _lectura([]))
    with pytest.raises(Exception):  # noqa: B017 — SigridLecturaError
        _cliente(servidor, intentos=1).buscar_albaranes("B1", "N", "ALB-d")
    assert len(servidor.peticiones) == 1


def test_f053_t25_fila_mas_corta_que_las_columnas_no_rompe():
    servidor = Servidor(_lectura([[8800001, "AC26/1"]]))
    (encontrado,) = _cliente(servidor).buscar_albaranes("B1", "N", "ALB-d")
    assert (encontrado.ide, encontrado.cod, encontrado.fec) == (8800001, "AC26/1", None)


@pytest.mark.parametrize("fallo", [httpx.ConnectTimeout("t"), httpx.ConnectError("c")])
def test_f053_t25_adjunto_caido_no_esta_colgado(fallo):
    servidor = Servidor(fallo, fallo, fallo)
    adjunto = _cliente(servidor).adjuntar_pdf(9, "ALB-d.pdf", b"%PDF", usu="U")
    assert adjunto.colgado is False and adjunto.codigo == type(fallo).__name__


def test_f053_t25_adjunto_rechazado_trae_el_error_recortado():
    servidor = Servidor(_json(400, {"error": "e" * 300, "details": {"codigo": "usuario_no_valido"}}))
    adjunto = _cliente(servidor).adjuntar_pdf(9, "ALB-d.pdf", b"%PDF", usu="U")
    assert adjunto.colgado is False and adjunto.codigo == "usuario_no_valido"
    assert adjunto.mensaje == "e" * 200


def test_f053_t25_200_invalido_es_status_200():
    resultado = _cliente(Servidor(_json(200, {"ok": False}))).alta_albaran(PETICION, commit=True)
    assert isinstance(resultado, ErrorAlta)
    assert (resultado.tipo, resultado.status) == (TipoFallo.RESPUESTA_INVALIDA, 200)


def test_f053_t25_400_trae_el_error_recortado_a_500():
    servidor = Servidor(_json(400, {"error": "x" * 600, "details": {"codigo": "obra_ambigua"}}))
    resultado = _cliente(servidor).alta_albaran(PETICION, commit=True)
    assert resultado.mensaje == "x" * 500


# ------------------------------------------------------------------ #
# Composición
# ------------------------------------------------------------------ #
def test_f053_t25_composicion_crea_el_motor_con_pre_ping(monkeypatch):
    from interface_adapters import composition

    creados = []

    def crear(url, **kwargs):
        creados.append(kwargs)
        return object()

    monkeypatch.setattr(composition, "create_engine", crear)
    composition.construir_servicio(_settings(monkeypatch))
    assert creados == [{"future": True, "pool_pre_ping": True}]


# ------------------------------------------------------------------ #
# main_worker: visibilidad exacta y avisos de arranque
# ------------------------------------------------------------------ #
def test_f053_t25_o1_peor_caso_y_visibilidad_exactos(monkeypatch, tmp_path):
    # 3 × 60 + (1 + 2) = 183 por llamada con reintentos; token 5 × 60 + 4 × 20 = 380;
    # PDF 380 + 4 × 60 = 620; total 183 × 3 + 240 + 620 = 1409; (1409 + 300) → 1740.
    assert main_worker.peor_caso_mensaje_s(_settings(monkeypatch)) == 1409
    assert _visibilidad_con(monkeypatch, tmp_path) == 1740


def test_f053_t25_o1_redondeo_al_minuto(monkeypatch, tmp_path):
    # t_sigrid 71, t_graph 60: 9 × 131 + 329 = 1508; + 300 = 1808 → 31 min = 1860 s.
    ajustes = _settings(monkeypatch, SIGRID_API_TIMEOUT_S="71")
    assert main_worker.peor_caso_mensaje_s(ajustes) == 1508
    assert _visibilidad_con(monkeypatch, tmp_path, SIGRID_API_TIMEOUT_S="71") == 1860


@pytest.mark.parametrize("desde, usuario, aviso_desde, aviso_usuario", [
    ("", "", True, False),
    ("", "USU", True, False),
    ("2026-10-01T00:00:00Z", "", False, True),
    ("2026-10-01T00:00:00Z", "USU", False, False),
])
def test_f053_t25_avisos_de_arranque(monkeypatch, tmp_path, caplog, desde, usuario,
                                     aviso_desde, aviso_usuario):
    ajustes = _settings(monkeypatch, LOG_DIR=str(tmp_path))
    ajustes = ajustes.model_copy(update={"alta_sigrid_desde_utc": desde, "usuario": usuario})
    monkeypatch.setattr(main_worker, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(main_worker, "Settings", lambda: ajustes)
    monkeypatch.setattr(main_worker, "configure_logging", lambda *a, **k: None)
    monkeypatch.setattr(main_worker, "ejecutar_worker", lambda **k: 0)
    caplog.set_level(logging.INFO)
    assert main_worker.main() == 0
    assert ("ALTA_SIGRID_DESDE_UTC vacía" in caplog.text) is aviso_desde
    assert ("ALTA_SIGRID_USUARIO vacío" in caplog.text) is aviso_usuario


def test_f053_t25_vuelca_json_valido():
    assert json.loads(repo._volcar([{"a": "é"}])) == [{"a": "é"}]
    assert replace(Motivo("x"), detalle="y").detalle == "y"


def test_f053_t25_o1_margen_de_cinco_minutos():
    """Review fase 1 · O1: peor caso + 300 s (BBDD y arranque)."""
    assert main_worker.MARGEN_VISIBILIDAD_S == 300
