# tests/test_f011_r7_r8_criticidad.py
"""F-011 · R7 y R8 — Criticidad de los campos comparados.

R7: campo crítico (partida, cantidades, precios, importes, códigos) →
discrepancia = FALLO; campo laxo (descripción, comentarios) → AVISO.
R8: campo sin clasificar → crítico + aviso de «campo sin clasificar»: la
omisión no relaja nada.
"""

import json

import pytest

from evals.criticidad import (
    RUTA_CRITICIDAD,
    ErrorCriticidad,
    cargar_criticidad,
)


@pytest.fixture(scope="module")
def criticidad():
    return cargar_criticidad()


@pytest.mark.parametrize(
    "campo",
    [
        "codigo_partida_final",
        "partida_final",
        "cantidad",
        "cantidad_final",
        "precio_unitario_final",
        "importe_calculado",
        "importe_final",
        "codigo_producto_contrato",
        "codigo_obra",
        "contrato_elegido",
        "cif",
        "codigo_ler",
        "review_required",
    ],
)
def test_f011_r7_campos_criticos_fallan(criticidad, campo):
    assert criticidad.severidad(campo) == "fallo"
    assert criticidad.clasificar(campo).clasificado is True


@pytest.mark.parametrize(
    "campo",
    ["descripcion", "descripcion_esperada", "comentario", "motivo_revision"],
)
def test_f011_r7_campos_laxos_solo_avisan(criticidad, campo):
    assert criticidad.severidad(campo) == "aviso"
    assert criticidad.clasificar(campo).clasificado is True


def test_f011_r7_la_ruta_del_campo_no_cambia_su_criticidad(criticidad):
    """En el informe el campo va con su camino; la criticidad es del campo."""
    assert criticidad.severidad("lineas[2].precio_unitario_final") == "fallo"
    assert criticidad.severidad("tablas.lineas[0].comentario") == "aviso"


def test_f011_r8_campo_sin_clasificar_es_critico_y_avisa(criticidad):
    clasificacion = criticidad.clasificar("invento_que_nadie_declaro")

    assert clasificacion.severidad == "fallo"
    assert clasificacion.clasificado is False
    assert "sin clasificar" in clasificacion.regla


def test_f011_r7_el_ajuste_por_campo_manda_sobre_los_patrones(tmp_path):
    """Subir un campo laxo a crítico es UNA línea de configuración."""
    ruta = tmp_path / "criticidad.json"
    ruta.write_text(
        json.dumps(
            {
                "por_defecto": "critico",
                "criticos": ["descripcion"],
                "laxos": ["importe_final"],
                "patrones_criticos": ["*importe*"],
                "patrones_laxos": ["descripcion*"],
            }
        ),
        encoding="utf-8",
    )

    criticidad = cargar_criticidad(ruta)

    assert criticidad.severidad("descripcion") == "fallo"
    assert criticidad.severidad("importe_final") == "aviso"


def test_f011_r7_configuracion_incoherente_no_se_carga(tmp_path):
    ruta = tmp_path / "criticidad.json"
    ruta.write_text(
        json.dumps({"por_defecto": "critico", "criticos": ["x"], "laxos": ["x"]}),
        encoding="utf-8",
    )

    with pytest.raises(ErrorCriticidad) as error:
        cargar_criticidad(ruta)

    assert "'x'" in str(error.value)


def test_f011_r7_configuracion_rota_falla_diciendo_que_falla(tmp_path):
    ruta = tmp_path / "criticidad.json"
    ruta.write_text("{esto no es json", encoding="utf-8")

    with pytest.raises(ErrorCriticidad) as error:
        cargar_criticidad(ruta)

    assert "criticidad.json" in str(error.value)


def test_f011_r7_la_configuracion_del_repositorio_existe_y_es_valida():
    assert RUTA_CRITICIDAD.is_file()
    assert cargar_criticidad(RUTA_CRITICIDAD).por_defecto == "critico"
