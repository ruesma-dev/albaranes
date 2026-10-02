# tests/test_f048_r18_lista_obras.py
"""F-048 · R18 y D5: la lista de TODAS las obras, sin consulta ni cache nuevas.

El codigo de obra del correo se valida contra TODAS las obras de Sigrid con
contrato, activas o no. Esa lista ya la descarga sv2 para F-002 (una sola
consulta a sigrid-api) y hasta ahora se tiraba tras filtrar las activas.
T16 bis la conserva:

- ``SigridApiObrasClient.obtener_catalogo()``: UNA peticion HTTP da las dos
  listas; ``obtener()`` sigue igual que hoy y ``obtener_todas()`` da todas.
- ``ObrasActivasCacheTTL`` cachea el catalogo: dentro del TTL, cualquier
  mezcla de ``obtener()`` y ``obtener_todas()`` cuesta UNA consulta; si el
  refresco falla se sirve el viejo; con un proveedor que solo tenga
  ``obtener()`` (los dobles de F-002), ``obtener_todas()`` da ``None``.
- ``AlbaranExtractionService.obras_conocidas()``: normalizado -> codigo tal
  como figura en la lista (D9); ``None`` sin lista o sin el metodo. Dos
  codigos distintos que normalizan igual son AMBIGUOS: la clave se queda
  fuera y se avisa con los dos (menor 5 de la review del bloque A).

Sin red: ``httpx.Client`` sustituido y proveedores dobles.
"""
from __future__ import annotations

import dataclasses
import logging
from typing import Self

import pytest
from application.services.albaran_extraction_service import AlbaranExtractionService
from application.services.schema_registry import SchemaRegistry
from domain.ports.obras_activas_provider import CatalogoObras, ObraActiva
from infrastructure.sigrid import sigrid_api_obras_client as modulo_cliente
from infrastructure.sigrid.obras_activas_cache import ObrasActivasCacheTTL
from infrastructure.sigrid.sigrid_api_obras_client import SigridApiObrasClient

FILAS = [
    ["0945", "RESIDENCIAL DEMO"],
    ["0100", "OBRA ANTIGUA"],  # <= 0450: no activa, pero es obra
    ["0450", "EN EL CORTE"],  # = 0450: no activa
    ["A-12", "OTRO FORMATO"],  # no son 4 digitos: no activa
    ["1042", "NAVE DEMO"],
]


def _obras(*codigos: str) -> tuple[ObraActiva, ...]:
    return tuple(ObraActiva(codigo=c, nombre=f"OBRA {c}") for c in codigos)


# ---------------------------------------------------------------- #
# El cliente HTTP: una peticion, dos listas.
# ---------------------------------------------------------------- #
class _Respuesta:
    def __init__(self, status_code: int = 200, cuerpo: dict | None = None) -> None:
        self.status_code = status_code
        self._cuerpo = cuerpo if cuerpo is not None else {"ok": True}
        self.text = ""

    def json(self) -> dict:
        return self._cuerpo


class _ClienteHttp:
    def __init__(self, respuesta: _Respuesta) -> None:
        self.respuesta = respuesta
        self.posts = 0

    def __call__(self, **_: object) -> _ClienteHttp:
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> bool:
        return False

    def post(self, url, json, headers) -> _Respuesta:
        self.posts += 1
        return self.respuesta


@pytest.fixture()
def http(monkeypatch):
    def _instalar(respuesta: _Respuesta) -> _ClienteHttp:
        falso = _ClienteHttp(respuesta)
        monkeypatch.setattr(modulo_cliente.httpx, "Client", falso)
        monkeypatch.setattr(modulo_cliente.httpx, "HTTPTransport", lambda **_: object())
        return falso

    return _instalar


def _cliente() -> SigridApiObrasClient:
    return SigridApiObrasClient(base_url="https://sigrid.example", function_key="clave-de-prueba", database="ruesma")


def _respuesta_obras(filas=FILAS) -> _Respuesta:
    return _Respuesta(cuerpo={"ok": True, "columns": ["codigo_obra", "nombre_obra"], "rows": filas})


def test_f048_r18_una_peticion_da_todas_las_obras_y_las_activas(http):
    falso = http(_respuesta_obras())

    catalogo = _cliente().obtener_catalogo()

    assert falso.posts == 1
    assert [o.codigo for o in catalogo.todas] == ["0945", "0100", "0450", "A-12", "1042"]
    assert [o.codigo for o in catalogo.activas] == ["0945", "1042"]


def test_f048_r18_la_lista_incluye_obras_no_activas_y_de_otro_formato(http):
    http(_respuesta_obras())

    todas = _cliente().obtener_todas()

    assert {"0100", "0450", "A-12"} <= {o.codigo for o in todas}


def test_f048_r18_obtener_sigue_dando_solo_las_activas_como_hoy(http):
    http(_respuesta_obras())

    assert [o.codigo for o in _cliente().obtener()] == ["0945", "1042"]


def test_f048_r18_sin_activas_obtener_da_none_pero_todas_siguen(http):
    http(_respuesta_obras([["0100", "OBRA ANTIGUA"]]))
    cliente = _cliente()

    assert cliente.obtener() is None
    assert [o.codigo for o in cliente.obtener_todas()] == ["0100"]


@pytest.mark.parametrize(
    "respuesta",
    [_Respuesta(status_code=500), _Respuesta(cuerpo={"ok": False}), _respuesta_obras([])],
    ids=["http_500", "ok_false", "sin_filas"],
)
def test_f048_r18_sin_respuesta_util_no_hay_catalogo(http, respuesta):
    http(respuesta)
    cliente = _cliente()

    assert cliente.obtener_catalogo() is None
    assert cliente.obtener_todas() is None
    assert cliente.obtener() is None


def test_f048_r18_el_catalogo_es_inmutable():
    catalogo = CatalogoObras(activas=_obras("0945"), todas=_obras("0945", "0100"))

    with pytest.raises(dataclasses.FrozenInstanceError):
        catalogo.todas = ()
    assert isinstance(catalogo.activas, tuple)
    assert isinstance(catalogo.todas, tuple)


# ---------------------------------------------------------------- #
# La cache: el catalogo entero, con la misma TTL y la misma lista vieja.
# ---------------------------------------------------------------- #
class _Reloj:
    def __init__(self) -> None:
        self.ahora = 5000.0

    def __call__(self) -> float:
        return self.ahora


class _ProveedorCatalogo:
    """Proveedor con ``obtener_catalogo``; cuenta las consultas."""

    def __init__(self, *respuestas: CatalogoObras | None) -> None:
        self._respuestas = list(respuestas)
        self.consultas = 0

    def obtener_catalogo(self) -> CatalogoObras | None:
        self.consultas += 1
        return self._respuestas[min(self.consultas, len(self._respuestas)) - 1]

    def obtener(self):  # pragma: no cover - la cache no debe usarlo
        raise AssertionError("con obtener_catalogo, la cache no llama a obtener()")


class _ProveedorSoloObtener:
    """Como los dobles de F-002: solo ``obtener()``."""

    def __init__(self, obras) -> None:
        self._obras = obras
        self.consultas = 0

    def obtener(self):
        self.consultas += 1
        return self._obras


CATALOGO = CatalogoObras(activas=_obras("0945"), todas=_obras("0945", "0100"))


def test_f048_r18_n_obtener_y_obtener_todas_dentro_del_ttl_son_una_consulta():
    proveedor = _ProveedorCatalogo(CATALOGO)
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=_Reloj())

    for _ in range(5):
        assert cache.obtener() == list(CATALOGO.activas)
        assert cache.obtener_todas() == list(CATALOGO.todas)

    assert proveedor.consultas == 1


def test_f048_r18_al_expirar_se_refresca_el_catalogo_entero():
    nuevo = CatalogoObras(activas=_obras("0945", "1042"), todas=_obras("0945", "1042", "0100"))
    proveedor = _ProveedorCatalogo(CATALOGO, nuevo)
    reloj = _Reloj()
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=reloj)

    cache.obtener_todas()
    reloj.ahora += 3601

    assert cache.obtener_todas() == list(nuevo.todas)
    assert cache.obtener() == list(nuevo.activas)
    assert proveedor.consultas == 2


def test_f048_r18_si_el_refresco_falla_se_sirve_el_catalogo_viejo():
    proveedor = _ProveedorCatalogo(CATALOGO, None)
    reloj = _Reloj()
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=reloj)

    cache.obtener()
    reloj.ahora += 3601

    assert cache.obtener_todas() == list(CATALOGO.todas)
    assert cache.obtener() == list(CATALOGO.activas)


def test_f048_r18_sin_catalogo_previo_todo_es_none():
    cache = ObrasActivasCacheTTL(_ProveedorCatalogo(None), ttl_s=3600, clock=_Reloj())

    assert cache.obtener() is None
    assert cache.obtener_todas() is None


def test_f048_r18_la_cache_no_deja_mutar_la_lista_de_todas():
    cache = ObrasActivasCacheTTL(_ProveedorCatalogo(CATALOGO), ttl_s=3600, clock=_Reloj())

    cache.obtener_todas().append(ObraActiva(codigo="9999", nombre="INTRUSA"))

    assert cache.obtener_todas() == list(CATALOGO.todas)


def test_f048_r18_con_un_proveedor_de_solo_obtener_todas_es_none():
    proveedor = _ProveedorSoloObtener(list(_obras("0945")))
    cache = ObrasActivasCacheTTL(proveedor, ttl_s=3600, clock=_Reloj())

    assert cache.obtener() == list(_obras("0945"))
    assert cache.obtener_todas() is None
    assert proveedor.consultas == 1


def test_f048_r18_cache_sobre_el_cliente_real_una_sola_peticion(http):
    falso = http(_respuesta_obras())
    cache = ObrasActivasCacheTTL(_cliente(), ttl_s=3600, clock=_Reloj())

    activas = cache.obtener()
    todas = cache.obtener_todas()

    assert falso.posts == 1
    assert [o.codigo for o in activas] == ["0945", "1042"]
    assert len(todas) == len(FILAS)


# ---------------------------------------------------------------- #
# El servicio: normalizado -> codigo de la lista.
# ---------------------------------------------------------------- #
class _Reglas:
    count = 0
    rule_ids: tuple[str, ...] = ()

    def render_for_prompt(self) -> str:
        return ""


def _servicio(proveedor) -> AlbaranExtractionService:
    return AlbaranExtractionService(
        providers=[],
        prompt_repo=None,
        schema_registry=SchemaRegistry(),
        revision_rules_repo=_Reglas(),
        prompt_key_phase_1="albaran_factura_es",
        obras_activas_provider=proveedor,
    )


class _ProveedorTodas:
    def __init__(self, todas) -> None:
        self._todas = todas

    def obtener(self):
        return None

    def obtener_todas(self):
        if isinstance(self._todas, Exception):
            raise self._todas
        return self._todas


def test_f048_r18_obras_conocidas_normaliza_y_devuelve_el_codigo_de_la_lista():
    servicio = _servicio(_ProveedorTodas(list(_obras("0945", "0100", "A-12", "1042"))))

    assert servicio.obras_conocidas() == {"945": "0945", "100": "0100", "A12": "A-12", "1042": "1042"}


def test_f048_r18_obras_conocidas_desde_la_cache_y_el_cliente(http):
    http(_respuesta_obras())
    servicio = _servicio(ObrasActivasCacheTTL(_cliente(), ttl_s=3600, clock=_Reloj()))

    conocidas = servicio.obras_conocidas()

    assert conocidas["945"] == "0945"
    assert conocidas["100"] == "0100"  # no activa: cuenta igual (D5)
    assert conocidas["450"] == "0450"


@pytest.mark.parametrize(
    "proveedor",
    [None, _ProveedorSoloObtener(list(_obras("0945"))), _ProveedorTodas(None), _ProveedorTodas([])],
    ids=["sin_proveedor", "sin_el_metodo", "lista_no_disponible", "lista_vacia"],
)
def test_f048_r18_sin_lista_obras_conocidas_es_none(proveedor):
    assert _servicio(proveedor).obras_conocidas() is None


def test_f048_r18_si_la_lista_revienta_obras_conocidas_es_none(caplog):
    with caplog.at_level(logging.WARNING):
        assert _servicio(_ProveedorTodas(RuntimeError("sigrid-api 500"))).obras_conocidas() is None


def test_f048_r18_codigos_que_no_normalizan_a_nada_no_entran():
    servicio = _servicio(_ProveedorTodas(list(_obras("0945", "0000", "--"))))

    assert servicio.obras_conocidas() == {"945": "0945"}


def test_f048_r18_colision_de_dos_codigos_distintos_queda_fuera_y_avisa(caplog):
    """Menor 5 (bloque A): ``0945-1`` y ``9451`` normalizan igual. No se elige en silencio."""
    servicio = _servicio(_ProveedorTodas(list(_obras("0945-1", "0945", "9451", "1042"))))

    with caplog.at_level(logging.WARNING):
        conocidas = servicio.obras_conocidas()

    assert conocidas == {"945": "0945", "1042": "1042"}
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    assert "0945-1" in avisos[0].getMessage()
    assert "9451" in avisos[0].getMessage()


def test_f048_r18_el_mismo_codigo_repetido_no_es_colision(caplog):
    servicio = _servicio(_ProveedorTodas(list(_obras("0945", "0945"))))

    with caplog.at_level(logging.WARNING):
        assert servicio.obras_conocidas() == {"945": "0945"}
    assert not [r for r in caplog.records if r.levelno == logging.WARNING]


def test_f048_r18_una_colision_triple_nombra_los_tres_y_sin_claves_no_hay_lista(caplog):
    servicio = _servicio(_ProveedorTodas(list(_obras("0945-1", "9451", "09.451"))))

    with caplog.at_level(logging.WARNING):
        assert servicio.obras_conocidas() is None

    (aviso,) = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert all(codigo in aviso for codigo in ("0945-1", "9451", "09.451"))
