# tests/test_f048_r40_r41_inyeccion.py
"""F-048 · T31 — la inyección del banco con y sin el correo del caso (R40, R41).

La inyección de F-047 (`evals/inyeccion.py`) entra por la MISMA puerta que
sv1. Con F-048, sv1 guarda además el contexto del correo en el blob lateral
`input/{document_id}.correo.json` ANTES de publicar y pone su nombre en
`MensajeExtraccion.correo_blob`. El banco tiene que hacer exactamente eso y
con la misma función (`guardar_contexto_correo`): si guardara el correo a su
manera, una pasada con correo mediría una entrada que en producción no existe.

R41: el mismo caso se inyecta con y sin correo. `--sin-correo` lo fuerza sin
él aunque el caso tenga fichero, que es la comparación de §7 del design.

Todo contra dobles de blob, cola y repositorio: sin Azurite, sin Postgres.
"""

from __future__ import annotations

import argparse
import json
import logging

import pytest
from ruesma_comun.blobs.conexion import CONTENEDOR_INPUT
from ruesma_comun.colas.conexion import COLA_EXTRACCION
from ruesma_comun.correo import construir_contexto_correo, nombre_blob_correo

from evals import correos, inyeccion

CENTINELA = "CENTINELA-CORREO-F048-9023"


class RepositorioDoble:
    def __init__(self, creado: bool = True) -> None:
        self.creado = creado
        self.llamadas: list[dict] = []

    def crear_si_no_existe(self, **kwargs):
        from ruesma_comun.workflows.repositorio import ResultadoCreacion

        self.llamadas.append(dict(kwargs))
        return ResultadoCreacion(
            workflow_id="wf-1", creado=self.creado, estado_actual="email_received"
        )


class AlmacenDoble:
    """Registra PDF y JSON en el mismo diario que la cola, para ver el orden."""

    def __init__(self, diario: list, fallo_json: Exception | None = None) -> None:
        self.pdfs: list[tuple] = []
        self.jsons: list[tuple] = []
        self._diario = diario
        self._fallo_json = fallo_json

    def put_bytes(self, contenedor, nombre, data, *, content_type=None, metadata=None):
        self.pdfs.append((contenedor, nombre))
        self._diario.append(f"blob {nombre}")

    def put_json(self, contenedor, nombre, objeto):
        if self._fallo_json is not None:
            raise self._fallo_json
        self.jsons.append((contenedor, nombre, objeto))
        self._diario.append(f"blob {nombre}")


class PublicadorDoble:
    def __init__(self, diario: list) -> None:
        self.publicados: list[tuple] = []
        self._diario = diario

    def publicar(self, cola, mensaje):
        self.publicados.append((cola, mensaje))
        self._diario.append(f"cola {cola}")


class Montaje:
    def __init__(self, *, creado=True, sin_correo=False, fallo_json=None, pasada="2026-09-24-01"):
        self.diario: list[str] = []
        self.repo = RepositorioDoble(creado)
        self.almacen = AlmacenDoble(self.diario, fallo_json)
        self.publicador = PublicadorDoble(self.diario)
        self.inyector = inyeccion.Inyector(
            repositorio=self.repo,
            almacen=self.almacen,
            publicador=self.publicador,
            pasada_id=pasada,
            sin_correo=sin_correo,
        )

    def inyectar(self, correo=None, caso_id="RES-001"):
        return self.inyector.inyectar(caso_id, b"%PDF-falso", f"{caso_id}.pdf", correo=correo)

    def payload(self) -> dict:
        return json.loads(self.repo.llamadas[0]["payload_json"])


def _correo(asunto=f"Obra 0945 {CENTINELA}", cuerpo=f"Adjunto albarán. {CENTINELA}"):
    return construir_contexto_correo(asunto, cuerpo)


# --- R40 · con correo, la misma puerta que sv1 ------------------------------------


def test_f048_r40_inyeccion_con_correo_guarda_el_blob_lateral_y_lo_pone_en_el_mensaje():
    m, ctx = Montaje(), _correo()

    resultado = m.inyectar(ctx)

    nombre = nombre_blob_correo(resultado.document_id)
    assert m.almacen.jsons == [(CONTENEDOR_INPUT, nombre, ctx.model_dump(mode="json"))]
    cola, mensaje = m.publicador.publicados[0]
    assert cola == COLA_EXTRACCION
    assert mensaje.correo_blob == nombre
    assert resultado.correo_blob == nombre


def test_f048_r40_inyeccion_el_correo_se_guarda_despues_del_pdf_y_antes_de_publicar():
    m = Montaje()
    resultado = m.inyectar(_correo())
    doc = resultado.document_id
    assert m.diario == [
        f"blob {doc}.pdf",
        f"blob {doc}.correo.json",
        f"cola {COLA_EXTRACCION}",
    ]


def test_f048_r40_inyeccion_usa_guardar_contexto_correo_de_ruesma_comun(monkeypatch):
    """La MISMA función que sv1, no una copia: si cambia el formato, cambia para los dos."""
    from ruesma_comun.correo import contexto

    llamadas = []
    original = contexto.guardar_contexto_correo

    def espia(almacen, document_id, ctx):
        llamadas.append((document_id, ctx.sha256))
        return original(almacen, document_id, ctx)

    monkeypatch.setattr(inyeccion, "guardar_contexto_correo", espia)
    m, ctx = Montaje(), _correo()
    resultado = m.inyectar(ctx)
    assert llamadas == [(resultado.document_id, ctx.sha256)]


def test_f048_r40_inyeccion_la_huella_va_al_payload_y_el_texto_no():
    m, ctx = Montaje(), _correo()
    m.inyectar(ctx)
    payload = m.payload()
    assert payload["correo_sha256"] == ctx.sha256
    assert CENTINELA not in m.repo.llamadas[0]["payload_json"]


def test_f048_r40_inyeccion_si_no_se_puede_guardar_el_correo_no_se_publica(caplog):
    """Como en sv1: sin blob lateral no hay mensaje, y el error no cita nada."""
    m = Montaje(fallo_json=OSError(f"no se pudo escribir {CENTINELA}"))

    with caplog.at_level(logging.DEBUG), pytest.raises(inyeccion.ErrorCorreo) as error:
        m.inyectar(_correo())

    assert m.publicador.publicados == []
    assert "OSError" in str(error.value)
    assert CENTINELA not in str(error.value)
    assert error.value.__cause__ is None and error.value.__suppress_context__ is True
    assert CENTINELA not in caplog.text


def test_f048_r40_inyeccion_el_duplicado_con_correo_no_guarda_ni_publica():
    m = Montaje(creado=False)
    resultado = m.inyectar(_correo())
    assert resultado.duplicado is True
    assert resultado.correo_blob is None
    assert m.almacen.jsons == [] and m.publicador.publicados == []


def test_f048_r40_inyeccion_sin_correo_se_comporta_como_en_f047():
    m = Montaje()
    resultado = m.inyectar(None)
    assert m.almacen.jsons == []
    assert m.publicador.publicados[0][1].correo_blob is None
    assert resultado.correo_blob is None
    assert "correo_sha256" not in m.payload()


def test_f048_r40_inyeccion_el_log_lleva_la_huella_y_nunca_el_texto(caplog):
    m, ctx = Montaje(), _correo()
    with caplog.at_level(logging.DEBUG, logger=inyeccion.logger.name):
        m.inyectar(ctx)
    assert ctx.sha256[:8] in caplog.text
    assert CENTINELA not in caplog.text


def test_f048_r40_inyeccion_de_la_captura_del_caso_al_blob_lateral(tmp_path):
    """La cadena entera del banco: fichero del caso → contexto → blob de sv2."""
    (tmp_path / "RES-001.json").write_text(
        json.dumps({"version": 1, "caso_id": "RES-001", "asunto": "RV: obra 0945",
                    "cuerpo": "hola\r\n\r\n\r\nadios", "recibido_utc": None}),
        encoding="utf-8",
    )
    m = Montaje()

    m.inyectar(correos.cargar_correo("RES-001", tmp_path))

    guardado = m.almacen.jsons[0][2]
    assert guardado["sha256"] == construir_contexto_correo("RV: obra 0945", "hola\n\nadios").sha256


# --- R41 · con y sin correo -------------------------------------------------------


def test_f048_r41_inyeccion_sin_correo_forzado_ignora_el_correo_del_caso(caplog):
    m = Montaje(sin_correo=True)
    with caplog.at_level(logging.INFO, logger=inyeccion.logger.name):
        resultado = m.inyectar(_correo())

    assert m.almacen.jsons == []
    assert m.publicador.publicados[0][1].correo_blob is None
    assert resultado.correo_blob is None
    assert "correo_sha256" not in m.payload()
    assert "--sin-correo" in caplog.text


def test_f048_r41_inyeccion_el_mismo_caso_con_y_sin_correo_en_dos_pasadas():
    ctx = _correo()
    con = Montaje(pasada="2026-09-24-01").inyectar(ctx)
    sin = Montaje(pasada="2026-09-24-02", sin_correo=True).inyectar(ctx)

    assert con.correlation_key != sin.correlation_key
    assert con.document_id != sin.document_id
    assert con.correo_blob == nombre_blob_correo(con.document_id)
    assert sin.correo_blob is None


def test_f048_r41_inyeccion_el_inyector_dice_si_va_sin_correo():
    assert Montaje().inyector.sin_correo is False
    assert Montaje(sin_correo=True).inyector.sin_correo is True


def test_f048_r41_inyeccion_la_opcion_sin_correo_del_cli():
    analizador = argparse.ArgumentParser()
    inyeccion.anadir_opcion_sin_correo(analizador)
    assert analizador.parse_args([]).sin_correo is False
    assert analizador.parse_args(["--sin-correo"]).sin_correo is True
