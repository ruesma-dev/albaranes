# tests/test_f053_t3_esqueleto.py
"""F-053 · T3 · esqueleto de sv9: configuración (R19, R44) y estructura.

- R19: el modo es ``real`` SOLO con ``ALTA_SIGRID_COMMIT`` igual al literal
  ``true``; cualquier otro valor (o ninguno) es ``simulacion``.
- R44: un ``ALTA_SIGRID_PRODUCTO_POR_DEFECTO`` mal formado impide arrancar.
- Defectos de design §7 y ficheros del esqueleto (sin secretos).

Sin red ni BBDD: ``Settings`` se construye con variables de entorno de mentira
y sin ``.env``.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

RAIZ = Path(__file__).resolve().parents[1]

#: Mínimo para construir ``Settings`` sin ``.env`` (valores de mentira).
ENTORNO_MINIMO = {
    "PG_USER": "usuario",
    "PG_PASSWORD": "clave-de-mentira",
    "GRAPH_KEY": "{}",
    "SIGRID_API_BASE_URL": "http://sigrid.invalid",
    "SIGRID_API_FUNCTION_KEY": "clave-de-mentira",
}

VARIABLES_ALTA = (
    "ALTA_SIGRID_DESDE_UTC", "ALTA_SIGRID_COMMIT", "ALTA_SIGRID_ESPERA_INCIERTO_MIN",
    "ALTA_SIGRID_TOLERANCIA_EUR", "ALTA_SIGRID_AVISOS_BLOQUEANTES", "ALTA_SIGRID_USUARIO",
    "ALTA_SIGRID_USUARIO_RESPALDO",
    "ALTA_SIGRID_EMPIDE", "ALTA_SIGRID_PRODUCTO_POR_DEFECTO", "SIGRID_API_DATABASE",
    "ALTA_SIGRID_EQUIVALENCIAS_USUARIO",
)


def _settings(monkeypatch, **extra):
    from config.settings import Settings

    for nombre in VARIABLES_ALTA:
        monkeypatch.delenv(nombre, raising=False)
    for nombre, valor in {**ENTORNO_MINIMO, **extra}.items():
        monkeypatch.setenv(nombre, valor)
    return Settings(_env_file=None)


# ------------------------------------------------------------------ #
# R19 · modo
# ------------------------------------------------------------------ #
def test_f053_r19_modo_simulacion_por_defecto(monkeypatch):
    ajustes = _settings(monkeypatch)
    assert ajustes.modo == "simulacion"
    assert ajustes.commit_real is False


def test_f053_r19_modo_real_solo_con_el_literal_true(monkeypatch):
    ajustes = _settings(monkeypatch, ALTA_SIGRID_COMMIT="true")
    assert ajustes.modo == "real" and ajustes.commit_real is True


@pytest.mark.parametrize(
    "valor", ["True", "TRUE", "1", "yes", "si", " true", "true ", "false", ""],
)
def test_f053_r19_modo_cualquier_otro_valor_es_simulacion(monkeypatch, valor):
    ajustes = _settings(monkeypatch, ALTA_SIGRID_COMMIT=valor)
    assert ajustes.modo == "simulacion" and ajustes.commit_real is False


# ------------------------------------------------------------------ #
# Defectos de design §7
# ------------------------------------------------------------------ #
def test_f053_t3_defectos_del_diseno(monkeypatch):
    ajustes = _settings(monkeypatch)
    assert ajustes.desde is None  # vacía = feature apagada
    assert ajustes.espera_incierto_min == 15
    assert ajustes.tolerancia_eur == pytest.approx(0.05)
    assert ajustes.avisos_bloqueantes == frozenset({"producto_sin_historico"})
    assert ajustes.usuario_respaldo == ""
    assert ajustes.equivalencias == {}  # F-069 R1 (ALTA_SIGRID_EMPIDE ya no existe, R4)
    assert ajustes.sigrid_api_database == "ruesma"
    assert ajustes.mapeo_producto == {
        "alquiler_maquinaria": "QA9999", "medios_auxiliares": "XA9999", "*": "MA9999",
    }


def test_f053_r17_precio_distinto_del_contrato_es_informativo_por_defecto(monkeypatch):
    """Aviso previo de sigrid-api (2026-10-06): con el precio neto de sv9 saldrán
    más ``precio_distinto_del_contrato``; es informativo y no manda a revisar.
    (``plantilla_de_otro_proveedor`` ya no existe en F-009, H25: fuera del defecto.)"""
    from domain.models.alta_models import LineaPeticion, PeticionAlbaran, RespuestaAlta
    from domain.services.comparador_previa import comparar

    ajustes = _settings(monkeypatch)
    assert "precio_distinto_del_contrato" not in ajustes.avisos_bloqueantes
    assert "plantilla_de_otro_proveedor" not in ajustes.avisos_bloqueantes
    peticion = PeticionAlbaran(
        cod_obra="0404", cif_proveedor="B1", cod_contrato="C", referencia_externa="ALB-d",
        su_referencia="1", usu="U", fecha_albaran=20261001, empide=None,
        lineas=(LineaPeticion(referencia_linea="1", cantidad=3.0, precio=33.333333,
                              ctrpro_ide=7),),
    )
    aviso = {"codigo": "precio_distinto_del_contrato", "mensaje": "pre = tar = precio"}
    respuesta = RespuestaAlta(estado="previsto", lineas=({
        "referencia_linea": "1", "total": round(3.0 * 33.333333, 2), "partida": None,
        "avisos": [aviso],
    },))
    assert comparar(peticion, respuesta, {"1": 100.0}, ajustes.tolerancia_eur,
                    ajustes.avisos_bloqueantes) == []


def test_f053_t3_desde_se_lee_como_instante_utc(monkeypatch):
    ajustes = _settings(monkeypatch, ALTA_SIGRID_DESDE_UTC="2026-10-01T00:00:00Z")
    assert ajustes.desde == datetime(2026, 10, 1, tzinfo=UTC)
    sin_zona = _settings(monkeypatch, ALTA_SIGRID_DESDE_UTC="2026-10-01T08:30:00")
    assert sin_zona.desde == datetime(2026, 10, 1, 8, 30, tzinfo=UTC)
    vacia = _settings(monkeypatch, ALTA_SIGRID_DESDE_UTC="   ")
    assert vacia.desde is None


def test_f053_t3_desde_ilegible_no_arranca(monkeypatch):
    with pytest.raises(ValidationError, match="ALTA_SIGRID_DESDE_UTC"):
        _settings(monkeypatch, ALTA_SIGRID_DESDE_UTC="mañana")


def test_f053_t3_avisos_bloqueantes_y_respaldo(monkeypatch):
    """F-069 R4: ``ALTA_SIGRID_EMPIDE`` ya no se lee (lo prueba test_f069_config)."""
    ajustes = _settings(
        monkeypatch,
        ALTA_SIGRID_AVISOS_BLOQUEANTES=" producto_sin_historico , stock_negativo ,",
        ALTA_SIGRID_USUARIO_RESPALDO="USU_ALTA",
    )
    assert ajustes.avisos_bloqueantes == frozenset(
        {"producto_sin_historico", "stock_negativo"},
    )
    assert ajustes.usuario_respaldo == "USU_ALTA"
    # Vacías valen su defecto (env_ignore_empty), como en .env.example.
    vacio = _settings(monkeypatch, ALTA_SIGRID_AVISOS_BLOQUEANTES="")
    assert vacio.avisos_bloqueantes == frozenset({"producto_sin_historico"})
    ninguno = _settings(monkeypatch, ALTA_SIGRID_AVISOS_BLOQUEANTES=" , ")
    assert ninguno.avisos_bloqueantes == frozenset()


# ------------------------------------------------------------------ #
# R44 · mapeo
# ------------------------------------------------------------------ #
def test_f053_r44_mapeo_valido_se_lee(monkeypatch):
    mapeo = {"*": "MA9999", "residuos": "MA9999"}
    ajustes = _settings(monkeypatch, ALTA_SIGRID_PRODUCTO_POR_DEFECTO=json.dumps(mapeo))
    assert ajustes.mapeo_producto == mapeo


@pytest.mark.parametrize(
    "texto", ["{roto", "[]", '{"alquiler_maquinaria": "QA9999"}', '{"*": 3}'],
)
def test_f053_r44_mapeo_invalido_no_arranca(monkeypatch, texto):
    with pytest.raises(ValidationError, match="ALTA_SIGRID_PRODUCTO_POR_DEFECTO"):
        _settings(monkeypatch, ALTA_SIGRID_PRODUCTO_POR_DEFECTO=texto)


# ------------------------------------------------------------------ #
# Ficheros del esqueleto
# ------------------------------------------------------------------ #
def test_f053_t3_ficheros_del_esqueleto_existen():
    for relativo in ("main.py", "Dockerfile", "requirements.txt", "sv9.md", ".env.example",
                     "config/settings.py", "config/logging_config.py"):
        assert (RAIZ / relativo).is_file(), relativo


def test_f053_t3_env_example_sin_valores():
    texto = (RAIZ / ".env.example").read_text(encoding="utf-8")
    nombres = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        nombre, _, valor = linea.partition("=")
        nombres.append(nombre)
        assert valor == "", f"{nombre} lleva valor en .env.example"
    for obligatorio in ("ALTA_SIGRID_DESDE_UTC", "ALTA_SIGRID_COMMIT",
                        "SIGRID_API_FUNCTION_KEY", "ALTA_SIGRID_PRODUCTO_POR_DEFECTO"):
        assert obligatorio in nombres, obligatorio


def test_f053_t3_requirements_declara_sus_dependencias():
    texto = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    for paquete in ("httpx", "tenacity", "sqlalchemy", "pydantic-settings", "psycopg"):
        assert paquete in texto, paquete


def test_f053_t3_primera_linea_de_cada_fichero_es_su_ruta():
    for fichero in RAIZ.rglob("*.py"):
        if ".venv" in fichero.parts or "__pycache__" in fichero.parts:
            continue
        if fichero.name == "__init__.py" and not fichero.read_text(encoding="utf-8").strip():
            continue
        relativo = fichero.relative_to(RAIZ).as_posix()
        primera = fichero.read_text(encoding="utf-8").splitlines()[0]
        assert primera == f"# {relativo}", f"{relativo}: {primera!r}"


def test_f053_t3_sv9_declarado_en_servicios_json():
    ruta = RAIZ.parents[1] / "harness" / "servicios.json"
    servicios = json.loads(ruta.read_text(encoding="utf-8"))
    rutas = {s["nombre"]: s["ruta"] for s in servicios["servicios"]}
    assert rutas.get("sv9-alta-sigrid") == "services/albaranes-alta-sigrid"
