# tests/test_f002_obras_cache.py
"""F-002 · Lista de obras activas para el prompt de IA1 (R1-bis, R3).

La lista se pide a sigrid-api UNA vez por réplica y TTL (R3) y se filtra
con el criterio PROVISIONAL de «obra activa» confirmado por el humano el
2026-08-13: código de 4 dígitos numéricos y mayor que ``cod_min``
(R1-bis, decisión D2).

Sin red: el proveedor es un doble y el filtro se prueba como función.
"""
from __future__ import annotations

import pytest

from config.settings import Settings
from domain.ports.obras_activas_provider import ObraActiva
from infrastructure.sigrid import sigrid_api_obras_client as modulo_cliente
from infrastructure.sigrid.obras_activas_cache import ObrasActivasCacheTTL
from infrastructure.sigrid.sigrid_api_obras_client import (
    SigridApiObrasClient,
    filas_a_obras,
    filtrar_obras_activas,
)


class ProveedorFake:
    """Devuelve la respuesta programada para cada llamada."""

    def __init__(self, *respuestas) -> None:
        self._respuestas = list(respuestas)
        self.llamadas = 0

    def obtener(self):
        self.llamadas += 1
        indice = min(self.llamadas - 1, len(self._respuestas) - 1)
        return self._respuestas[indice]


class RelojFalso:
    """Arranca LEJOS de cero a proposito: con 0.0, sumar o restar el
    instante de obtencion da lo mismo y la comparacion del TTL se
    quedaria sin comprobar."""

    def __init__(self) -> None:
        self.ahora = 5000.0

    def __call__(self) -> float:
        return self.ahora

    def avanzar(self, segundos: float) -> None:
        self.ahora += segundos


def _obras(*codigos: str) -> list[ObraActiva]:
    return [ObraActiva(codigo=c, nombre=f"OBRA {c}") for c in codigos]


# ---------------------------------------------------------------- #
# R3 — una sola llamada dentro del TTL.
# ---------------------------------------------------------------- #
def test_f002_r3_dentro_del_ttl_solo_se_consulta_una_vez() -> None:
    proveedor = ProveedorFake(_obras("0500", "0600"))
    reloj = RelojFalso()
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=reloj)

    resultados = [cache.obtener() for _ in range(10)]

    assert proveedor.llamadas == 1
    assert all(r == _obras("0500", "0600") for r in resultados)


def test_f002_r3_al_expirar_el_ttl_se_refresca() -> None:
    proveedor = ProveedorFake(_obras("0500"), _obras("0500", "0700"))
    reloj = RelojFalso()
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=reloj)

    cache.obtener()
    reloj.avanzar(3601)
    segunda = cache.obtener()

    assert proveedor.llamadas == 2
    assert segunda == _obras("0500", "0700")


def test_f002_r3_justo_en_el_borde_del_ttl_no_se_refresca() -> None:
    proveedor = ProveedorFake(_obras("0500"))
    reloj = RelojFalso()
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=reloj)

    cache.obtener()
    reloj.avanzar(3600)
    cache.obtener()

    assert proveedor.llamadas == 1


def test_f002_r3_la_cache_no_deja_mutar_lo_cacheado() -> None:
    proveedor = ProveedorFake(_obras("0500"))
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=RelojFalso())

    primera = cache.obtener()
    primera.append(ObraActiva(codigo="9999", nombre="INTRUSA"))

    assert cache.obtener() == _obras("0500")


# ---------------------------------------------------------------- #
# R2 — degradación: sin lista, se sirve la vieja o None.
# ---------------------------------------------------------------- #
def test_f002_r2_si_el_proveedor_falla_se_sirve_la_lista_vieja() -> None:
    proveedor = ProveedorFake(_obras("0500"), None)
    reloj = RelojFalso()
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=reloj)

    cache.obtener()
    reloj.avanzar(3601)

    assert cache.obtener() == _obras("0500")


def test_f002_r2_sin_lista_previa_devuelve_none() -> None:
    cache = ObrasActivasCacheTTL(
        ProveedorFake(None), ttl_s=3600, clock=RelojFalso(),
    )

    assert cache.obtener() is None


def test_f002_r2_un_proveedor_que_revienta_no_propaga() -> None:
    class ProveedorRoto:
        def obtener(self):
            raise RuntimeError("sigrid-api 500")

    cache = ObrasActivasCacheTTL(
        ProveedorRoto(), ttl_s=3600, clock=RelojFalso(),
    )

    assert cache.obtener() is None


# ---------------------------------------------------------------- #
# R1-bis — filtro PROVISIONAL de «obra activa».
# ---------------------------------------------------------------- #
def test_f002_r1bis_descarta_codigos_que_no_son_de_4_digitos() -> None:
    entrada = _obras("0500", "500", "05000", "", "  ")

    assert [o.codigo for o in filtrar_obras_activas(entrada, cod_min=450)] == [
        "0500",
    ]


def test_f002_r1bis_descarta_codigos_no_numericos() -> None:
    entrada = _obras("0500", "A500", "05.0", "OBRA")

    assert [o.codigo for o in filtrar_obras_activas(entrada, cod_min=450)] == [
        "0500",
    ]


def test_f002_r1bis_descarta_los_codigos_por_debajo_del_corte() -> None:
    entrada = _obras("0449", "0450", "0451", "0999")

    assert [o.codigo for o in filtrar_obras_activas(entrada, cod_min=450)] == [
        "0451", "0999",
    ]


def test_f002_r1bis_con_corte_cero_no_se_descarta_ninguna_por_valor() -> None:
    entrada = _obras("0001", "0449", "0450", "0451")

    assert [o.codigo for o in filtrar_obras_activas(entrada, cod_min=0)] == [
        "0001", "0449", "0450", "0451",
    ]


def test_f002_r1bis_con_corte_cero_sigue_exigiendo_4_digitos() -> None:
    entrada = _obras("0001", "1", "12345", "X001")

    assert [o.codigo for o in filtrar_obras_activas(entrada, cod_min=0)] == [
        "0001",
    ]


def test_f002_r1bis_el_corte_es_estricto_mayor_que() -> None:
    """`> 0450`, no `>=`: la obra 0450 queda fuera."""
    assert filtrar_obras_activas(_obras("0450"), cod_min=450) == []


# ---------------------------------------------------------------- #
# Parseo de la respuesta de sigrid-api (sin red).
# ---------------------------------------------------------------- #
def test_f002_r1bis_las_filas_de_sigrid_se_convierten_en_obras() -> None:
    columnas = ["codigo_obra", "nombre_obra"]
    filas = [["0451", "EDIFICIO A"], ["0452", None]]

    assert filas_a_obras(columnas, filas) == [
        ObraActiva(codigo="0451", nombre="EDIFICIO A"),
        ObraActiva(codigo="0452", nombre=None),
    ]


def test_f002_r1bis_las_filas_sin_codigo_se_ignoran() -> None:
    columnas = ["codigo_obra", "nombre_obra"]
    filas = [[None, "SIN CODIGO"], ["", "VACIA"], ["0451", "BUENA"]]

    assert [o.codigo for o in filas_a_obras(columnas, filas)] == ["0451"]


def test_f002_r1bis_sin_las_columnas_esperadas_se_lee_por_posicion() -> None:
    """sigrid-api podria devolver los alias cambiados: el orden del SELECT
    (codigo, nombre) es el respaldo."""
    filas = [["0451", "EDIFICIO A"]]

    assert filas_a_obras(["c0", "c1"], filas) == [
        ObraActiva(codigo="0451", nombre="EDIFICIO A"),
    ]


def test_f002_r1bis_una_fila_sin_columna_de_nombre_no_revienta() -> None:
    assert filas_a_obras(["codigo_obra", "nombre_obra"], [["0451"]]) == [
        ObraActiva(codigo="0451", nombre=None),
    ]


def test_f002_r1bis_la_obra_es_inmutable() -> None:
    """La cache reparte las MISMAS instancias a todas las extracciones:
    si fueran mutables, una podria envenenar el prompt de las demas."""
    obra = ObraActiva(codigo="0451", nombre="EDIFICIO A")

    with pytest.raises(Exception):
        obra.codigo = "9999"


def test_f002_r1bis_los_codigos_se_deduplican_conservando_el_primero() -> None:
    """``con.cod`` se repite en Sigrid (varias filas por obra): el prompt
    no puede listar la misma obra dos veces."""
    columnas = ["codigo_obra", "nombre_obra"]
    filas = [["0451", "EDIFICIO A"], ["0451", "EDIFICIO A (bis)"]]

    assert filas_a_obras(columnas, filas) == [
        ObraActiva(codigo="0451", nombre="EDIFICIO A"),
    ]


# ---------------------------------------------------------------- #
# Configuración: los defaults son parte del contrato (R17, D2, D6).
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    "campo,esperado",
    [
        ("obras_activas_enabled", True),
        ("obras_activas_ttl_s", 21600),
        ("obras_activas_max", 300),
        ("obras_activas_cod_min", 450),
        ("sigrid_api_timeout_s", 30.0),
    ],
)
def test_f002_r1bis_defaults_de_configuracion(campo: str, esperado) -> None:
    assert Settings.model_fields[campo].default == esperado


def test_f002_r2_sin_las_tres_credenciales_sigrid_no_esta_disponible() -> None:
    incompleta = Settings.model_construct(
        sigrid_api_base_url="https://sigrid.example",
        sigrid_api_function_key="",
        sigrid_api_database="ruesma",
    )
    completa = Settings.model_construct(
        sigrid_api_base_url="https://sigrid.example",
        sigrid_api_function_key="clave-de-prueba",
        sigrid_api_database="ruesma",
    )

    assert incompleta.sigrid_credentials_present is False
    assert completa.sigrid_credentials_present is True


# ---------------------------------------------------------------- #
# El cliente HTTP, sin tocar la red: httpx.Client sustituido.
# ---------------------------------------------------------------- #
class RespuestaFake:
    def __init__(self, *, status_code: int = 200, cuerpo=None, texto: str = ""):
        self.status_code = status_code
        self._cuerpo = cuerpo if cuerpo is not None else {"ok": True}
        self.text = texto

    def json(self):
        return self._cuerpo


class ClientFake:
    """Sustituto de ``httpx.Client``: registra la petición y responde."""

    def __init__(self, respuesta: RespuestaFake) -> None:
        self.respuesta = respuesta
        self.peticiones: list[dict] = []
        self.transportes: list[dict] = []

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        return self

    def transporte(self, **kwargs):
        self.transportes.append(kwargs)
        return object()

    def __enter__(self):
        return self

    def __exit__(self, *excepcion) -> bool:
        return False

    def post(self, url, json, headers):
        self.peticiones.append({"url": url, "json": json, "headers": headers})
        return self.respuesta


@pytest.fixture()
def cliente_http(monkeypatch):
    def _instalar(respuesta: RespuestaFake) -> ClientFake:
        fake = ClientFake(respuesta)
        monkeypatch.setattr(modulo_cliente.httpx, "Client", fake)
        monkeypatch.setattr(
            modulo_cliente.httpx, "HTTPTransport", fake.transporte,
        )
        return fake

    return _instalar


def _cliente(**kwargs) -> SigridApiObrasClient:
    parametros = {
        "base_url": "https://sigrid.example/",
        "function_key": "clave-de-prueba",
        "database": "ruesma",
    }
    parametros.update(kwargs)
    return SigridApiObrasClient(**parametros)


@pytest.mark.parametrize(
    "falta", ["base_url", "function_key", "database"],
)
def test_f002_r2_el_cliente_exige_sus_tres_credenciales(falta: str) -> None:
    with pytest.raises(ValueError):
        _cliente(**{falta: ""})


def test_f002_r1bis_el_cliente_pide_las_obras_y_las_filtra(cliente_http) -> None:
    http = cliente_http(RespuestaFake(cuerpo={
        "ok": True,
        "columns": ["codigo_obra", "nombre_obra"],
        "rows": [["0451", "EDIFICIO A"], ["0100", "OBRA VIEJA"]],
    }))

    obras = _cliente().obtener()

    assert obras == [ObraActiva(codigo="0451", nombre="EDIFICIO A")]
    peticion = http.peticiones[0]
    assert peticion["url"] == "https://sigrid.example/api/sql/read"
    assert peticion["headers"]["x-functions-key"] == "clave-de-prueba"
    assert peticion["json"]["database"] == "ruesma"
    assert peticion["json"]["max_rows"] == 10000
    assert "FROM obr" in peticion["json"]["sql"]


def test_f002_r2_una_lista_vacia_tras_el_filtro_es_no_disponible(
    cliente_http,
) -> None:
    cliente_http(RespuestaFake(cuerpo={
        "ok": True,
        "columns": ["codigo_obra", "nombre_obra"],
        "rows": [["0100", "OBRA VIEJA"]],
    }))

    assert _cliente().obtener() is None


def test_f002_r2_un_error_http_no_propaga_y_devuelve_none(cliente_http) -> None:
    cliente_http(RespuestaFake(status_code=500, texto="boom"))

    assert _cliente().obtener() is None


def test_f002_r2_un_ok_false_no_propaga_y_devuelve_none(cliente_http) -> None:
    cliente_http(RespuestaFake(cuerpo={"ok": False, "error": "sql"}))

    assert _cliente().obtener() is None


def test_f002_r1bis_el_max_rows_es_configurable(cliente_http) -> None:
    http = cliente_http(RespuestaFake(cuerpo={
        "ok": True,
        "columns": ["codigo_obra", "nombre_obra"],
        "rows": [["0451", "EDIFICIO A"], ["0452", "EDIFICIO B"]],
    }))

    # Con max_rows=2 y 2 filas devueltas, la lista puede venir truncada:
    # se sirve igual, pero queda avisado en el log.
    assert _cliente(max_rows=2).obtener() == [
        ObraActiva(codigo="0451", nombre="EDIFICIO A"),
        ObraActiva(codigo="0452", nombre="EDIFICIO B"),
    ]
    assert http.peticiones[0]["json"]["max_rows"] == 2


def test_f002_r1bis_avisa_cuando_la_lista_puede_venir_truncada(
    cliente_http, caplog,
) -> None:
    """Si llegan EXACTAMENTE max_rows filas, faltan obras y nadie lo
    sabria: el aviso es la unica pista operativa."""
    cliente_http(RespuestaFake(cuerpo={
        "ok": True,
        "columns": ["codigo_obra", "nombre_obra"],
        "rows": [["0451", "A"], ["0452", "B"]],
    }))

    with caplog.at_level("WARNING"):
        _cliente(max_rows=2).obtener()

    assert "truncada" in caplog.text


def test_f002_r1bis_con_una_fila_menos_no_avisa_de_truncado(
    cliente_http, caplog,
) -> None:
    cliente_http(RespuestaFake(cuerpo={
        "ok": True,
        "columns": ["codigo_obra", "nombre_obra"],
        "rows": [["0451", "A"]],
    }))

    with caplog.at_level("WARNING"):
        _cliente(max_rows=2).obtener()

    assert "truncada" not in caplog.text


def test_f002_r2_un_400_se_trata_como_error_aunque_traiga_cuerpo(
    cliente_http,
) -> None:
    """400 es el codigo tipico de una query mal formada: si se colase
    como respuesta buena, el prompt se quedaria sin obras SIN error."""
    cliente_http(RespuestaFake(status_code=400, cuerpo={
        "ok": True,
        "columns": ["codigo_obra", "nombre_obra"],
        "rows": [["0451", "EDIFICIO A"]],
    }, texto="bad request"))

    assert _cliente().obtener() is None


def test_f002_r2_una_respuesta_sin_ok_no_se_da_por_buena(cliente_http) -> None:
    cliente_http(RespuestaFake(cuerpo={
        "columns": ["codigo_obra", "nombre_obra"],
        "rows": [["0451", "EDIFICIO A"]],
    }))

    assert _cliente().obtener() is None


def test_f002_r2_el_transporte_reintenta_una_vez(cliente_http) -> None:
    """Errores transitorios de red: un reintento, nunca bucle desnudo."""
    http = cliente_http(RespuestaFake(cuerpo={
        "ok": True, "columns": ["codigo_obra", "nombre_obra"], "rows": [],
    }))

    _cliente().obtener()

    assert http.transportes == [{"retries": 1}]
