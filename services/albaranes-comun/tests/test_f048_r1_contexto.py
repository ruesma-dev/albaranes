# tests/test_f048_r1_contexto.py
"""F-048 · R1 · el contexto de correo se define UNA vez en ``ruesma_comun``.

Un modelo (``ContextoCorreo``) y una funcion que lo construye: normaliza
espacios, recorta el cuerpo a un maximo configurable (defecto 4.000) y
calcula el sha256 sobre lo conservado. Mas el nombre del blob lateral y su
lectura/escritura en ``input/``.

Ningun texto es de un correo real: son inventados, con el centinela
``CENTINELA-F048``. Sin red ni BBDD: el almacen es un doble en memoria.
"""
from __future__ import annotations

import hashlib
import json
import logging

import pytest
from pydantic import ValidationError
from ruesma_comun.blobs import BlobNoEncontradoError
from ruesma_comun.correo import (
    MAX_CARACTERES_DEFECTO,
    ContextoCorreo,
    construir_contexto_correo,
    guardar_contexto_correo,
    leer_contexto_correo,
    nombre_blob_correo,
)

CENTINELA = "CENTINELA-F048"


def _huella(asunto: str, cuerpo: str) -> str:
    """Huella esperada: asunto y cuerpo conservados, separados por linea en blanco."""
    return hashlib.sha256(f"{asunto}\n\n{cuerpo}".encode()).hexdigest()


class AlmacenDoble:
    """Doble en memoria con la forma de ``AlmacenBlobs`` (put_json/get_json)."""

    def __init__(self) -> None:
        self.blobs: dict[tuple[str, str], object] = {}
        self.llamadas: list[tuple[str, str, str]] = []

    def put_json(self, contenedor: str, nombre: str, objeto: object) -> None:
        self.llamadas.append(("put_json", contenedor, nombre))
        # Ida y vuelta por JSON, como el almacen real.
        self.blobs[(contenedor, nombre)] = json.loads(json.dumps(objeto))

    def get_json(self, contenedor: str, nombre: str) -> object:
        self.llamadas.append(("get_json", contenedor, nombre))
        if (contenedor, nombre) not in self.blobs:
            raise BlobNoEncontradoError(f"No existe el blob {contenedor}/{nombre}.")
        valor = self.blobs[(contenedor, nombre)]
        if isinstance(valor, Exception):
            raise valor
        return valor


# ------------------------------------------------------------------ #
# Construccion: campos, normalizacion, recorte y huella
# ------------------------------------------------------------------ #
def test_f048_r1_construye_el_modelo_con_todos_sus_campos():
    ctx = construir_contexto_correo(
        "Albaran obra 1234",
        f"Para la obra 1234. {CENTINELA}",
        recibido_utc="2026-09-23T08:00:00Z",
    )
    assert isinstance(ctx, ContextoCorreo)
    assert ctx.version == 1
    assert ctx.asunto == "Albaran obra 1234"
    assert ctx.cuerpo == f"Para la obra 1234. {CENTINELA}"
    assert ctx.caracteres_originales == len(ctx.cuerpo)
    assert ctx.truncado is False
    assert ctx.recibido_utc == "2026-09-23T08:00:00Z"
    assert ctx.sha256 == _huella(ctx.asunto, ctx.cuerpo)


def test_f048_r1_recibido_utc_es_opcional():
    ctx = construir_contexto_correo("Asunto", "Cuerpo")
    assert ctx.recibido_utc is None


def test_f048_r1_normaliza_espacios_del_asunto_a_uno_solo():
    ctx = construir_contexto_correo("  RE:\t  obra   1234 \n", "x")
    assert ctx.asunto == "RE: obra 1234"


def test_f048_r1_normaliza_espacios_del_cuerpo_y_conserva_parrafos():
    cuerpo = (
        "  Hola,\t\tbuenos   dias \r\n"
        "\r\n\r\n\r\n"
        "   Obra  1234   \r"
        f"{CENTINELA}   \n\n  "
    )
    ctx = construir_contexto_correo("Asunto", cuerpo)
    assert ctx.cuerpo == f"Hola, buenos dias\n\nObra 1234\n{CENTINELA}"


def test_f048_r1_cuerpo_vacio_o_nulo_da_cuerpo_vacio():
    assert construir_contexto_correo("Asunto", "").cuerpo == ""
    assert construir_contexto_correo("Asunto", None).cuerpo == ""
    assert construir_contexto_correo("Asunto", "  \r\n \t ").cuerpo == ""


def test_f048_r1_asunto_nulo_da_asunto_vacio():
    assert construir_contexto_correo(None, "cuerpo").asunto == ""


def test_f048_r1_recorta_al_maximo_por_defecto_de_4000():
    assert MAX_CARACTERES_DEFECTO == 4000
    cuerpo = "a" * 5000
    ctx = construir_contexto_correo("Asunto", cuerpo)
    assert len(ctx.cuerpo) == 4000
    assert ctx.truncado is True
    assert ctx.caracteres_originales == 5000


def test_f048_r1_el_maximo_es_configurable():
    ctx = construir_contexto_correo("Asunto", "0123456789ABCDEF", max_caracteres=10)
    assert ctx.cuerpo == "0123456789"
    assert ctx.truncado is True
    assert ctx.caracteres_originales == 16


def test_f048_r1_justo_en_el_maximo_no_esta_truncado():
    ctx = construir_contexto_correo("Asunto", "0123456789", max_caracteres=10)
    assert ctx.cuerpo == "0123456789"
    assert ctx.truncado is False
    assert ctx.caracteres_originales == 10


def test_f048_r1_uno_mas_del_maximo_si_esta_truncado():
    ctx = construir_contexto_correo("Asunto", "0123456789X", max_caracteres=10)
    assert ctx.cuerpo == "0123456789"
    assert ctx.truncado is True


def test_f048_r1_el_recorte_no_deja_espacios_colgando():
    ctx = construir_contexto_correo("Asunto", "abcd efgh", max_caracteres=5)
    assert ctx.cuerpo == "abcd"
    assert ctx.truncado is True


def test_f048_r1_caracteres_originales_se_cuentan_tras_normalizar():
    ctx = construir_contexto_correo("Asunto", "  a    b  ")
    assert ctx.cuerpo == "a b"
    assert ctx.caracteres_originales == 3


@pytest.mark.parametrize("maximo", [0, -1])
def test_f048_r1_maximo_no_positivo_es_error(maximo):
    with pytest.raises(ValueError):
        construir_contexto_correo("Asunto", "cuerpo", max_caracteres=maximo)


def test_f048_r1_sha256_sobre_lo_conservado_no_sobre_lo_recortado():
    base = "x" * 20
    uno = construir_contexto_correo("Asunto", base + "COLA-UNO", max_caracteres=20)
    dos = construir_contexto_correo("Asunto", base + "COLA-DOS", max_caracteres=20)
    assert uno.sha256 == dos.sha256 == _huella("Asunto", base)


def test_f048_r1_sha256_cambia_con_el_asunto_y_con_el_cuerpo():
    base = construir_contexto_correo("Asunto", "cuerpo")
    otro_asunto = construir_contexto_correo("Asunto 2", "cuerpo")
    otro_cuerpo = construir_contexto_correo("Asunto", "cuerpo 2")
    assert len({base.sha256, otro_asunto.sha256, otro_cuerpo.sha256}) == 3


def test_f048_r1_sha256_estable_ante_espacios_de_mas():
    uno = construir_contexto_correo("Asunto", "Obra 1234")
    dos = construir_contexto_correo("  Asunto ", "  Obra    1234 \r\n")
    assert uno.sha256 == dos.sha256


# ------------------------------------------------------------------ #
# Nombre del blob lateral
# ------------------------------------------------------------------ #
def test_f048_r1_nombre_blob_correo():
    assert nombre_blob_correo("doc-123") == "doc-123.correo.json"


@pytest.mark.parametrize("vacio", ["", "   "])
def test_f048_r1_nombre_blob_correo_exige_document_id(vacio):
    with pytest.raises(ValueError):
        nombre_blob_correo(vacio)


# ------------------------------------------------------------------ #
# Guardar y leer en input/
# ------------------------------------------------------------------ #
def test_f048_r1_guardar_escribe_en_input_y_devuelve_el_nombre():
    almacen = AlmacenDoble()
    ctx = construir_contexto_correo("Asunto", f"Obra 1234 {CENTINELA}")
    nombre = guardar_contexto_correo(almacen, "doc-1", ctx)
    assert nombre == "doc-1.correo.json"
    assert almacen.llamadas == [("put_json", "input", "doc-1.correo.json")]
    assert ContextoCorreo.model_validate(almacen.blobs[("input", nombre)]) == ctx


def test_f048_r1_ida_y_vuelta_guardar_leer():
    almacen = AlmacenDoble()
    ctx = construir_contexto_correo(
        "Asunto", f"Obra 1234 {CENTINELA}", recibido_utc="2026-09-23T08:00:00Z"
    )
    nombre = guardar_contexto_correo(almacen, "doc-1", ctx)
    assert leer_contexto_correo(almacen, nombre) == ctx
    assert almacen.llamadas[-1] == ("get_json", "input", "doc-1.correo.json")


def test_f048_r1_leer_blob_inexistente_devuelve_none():
    assert leer_contexto_correo(AlmacenDoble(), "no-existe.correo.json") is None


def test_f048_r1_leer_json_roto_devuelve_none():
    almacen = AlmacenDoble()
    almacen.blobs[("input", "roto.correo.json")] = json.JSONDecodeError("x", "{", 0)
    assert leer_contexto_correo(almacen, "roto.correo.json") is None


def test_f048_r1_leer_bytes_no_utf8_devuelve_none():
    almacen = AlmacenDoble()
    almacen.blobs[("input", "b.correo.json")] = UnicodeDecodeError(
        "utf-8", b"\xff", 0, 1, "invalid start byte"
    )
    assert leer_contexto_correo(almacen, "b.correo.json") is None


@pytest.mark.parametrize(
    "contenido",
    [
        [],
        "texto",
        {"asunto": "a"},
        {
            "asunto": "a", "cuerpo": "b", "sha256": "no-es-hex",
            "caracteres_originales": 1, "truncado": False,
        },
        {
            "asunto": "a", "cuerpo": "b", "sha256": "a" * 64,
            "caracteres_originales": -1, "truncado": False,
        },
    ],
)
def test_f048_r1_leer_contenido_que_no_valida_devuelve_none(contenido):
    almacen = AlmacenDoble()
    almacen.blobs[("input", "malo.correo.json")] = contenido
    assert leer_contexto_correo(almacen, "malo.correo.json") is None


def test_f048_r1_leer_ignora_campos_de_mas():
    almacen = AlmacenDoble()
    ctx = construir_contexto_correo("Asunto", "Cuerpo")
    datos = ctx.model_dump(mode="json") | {"campo_futuro": 1}
    almacen.blobs[("input", "x.correo.json")] = datos
    assert leer_contexto_correo(almacen, "x.correo.json") == ctx


def test_f048_r1_leer_propaga_errores_que_no_son_de_contenido():
    """Un fallo de red no es «falta» ni «no valida»: se propaga para que la
    cola reintente, en vez de extraer sin correo por un corte transitorio."""
    almacen = AlmacenDoble()
    almacen.blobs[("input", "red.correo.json")] = ConnectionError("corte")
    with pytest.raises(ConnectionError):
        leer_contexto_correo(almacen, "red.correo.json")


def test_f048_r1_leer_invalido_avisa_sin_texto_del_correo(caplog):
    almacen = AlmacenDoble()
    almacen.blobs[("input", "malo.correo.json")] = {
        "asunto": CENTINELA, "cuerpo": CENTINELA, "sha256": CENTINELA,
        "caracteres_originales": 1, "truncado": False,
    }
    with caplog.at_level(logging.DEBUG):
        assert leer_contexto_correo(almacen, "malo.correo.json") is None
    assert "malo.correo.json" in caplog.text
    assert CENTINELA not in caplog.text


def test_f048_r1_leer_inexistente_avisa_en_el_log(caplog):
    with caplog.at_level(logging.WARNING):
        assert leer_contexto_correo(AlmacenDoble(), "falta.correo.json") is None
    assert "falta.correo.json" in caplog.text


def test_f048_r1_modelo_rechaza_sha256_que_no_es_hex_de_64():
    with pytest.raises(ValidationError):
        ContextoCorreo(
            asunto="a", cuerpo="b", sha256="ABC",
            caracteres_originales=1, truncado=False,
        )
