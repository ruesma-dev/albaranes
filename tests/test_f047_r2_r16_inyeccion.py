# tests/test_f047_r2_r16_inyeccion.py
"""F-047 · R2 y R16 — la entrada del banco y el aislamiento entre pasadas.

El banco entra al pipeline por la MISMA puerta que sv1 (R2): fila en
`workflow_runs`, PDF en `input/{document_id}.pdf` y `MensajeExtraccion` en
`q-extraccion`. Aquí se comprueba contra dobles, sin Azurite ni Postgres.

Lo que estos tests defienden, y por qué no es ceremonia:

- **El orden importa**: si se publicara el mensaje antes de subir el blob,
  sv2 podría despertarse y no encontrar el PDF. Es la carrera clásica del
  hand-off por cola y se comprueba con un doble que registra la secuencia.
- **El duplicado no re-sube ni re-encola** (lo que hace sv1): si lo hiciera,
  `--reproceso` dejaría de ejercitar la rama de duplicado de verdad.
- **Dos casos nunca comparten clave ni documento** (R16), que es lo único que
  aisla una pasada de otra cuando la base NO se borra entre pasadas.
"""

from __future__ import annotations

import json
import uuid

import pytest

from evals import inyeccion
from ruesma_comun.blobs.conexion import CONTENEDOR_INPUT
from ruesma_comun.colas.conexion import COLA_EXTRACCION, COLA_PERSISTENCIA, COLA_VALORACION


class RepositorioDoble:
    """`RepositorioWorkflows` de mentira: registra y decide si es duplicado."""

    def __init__(self, creado: bool = True) -> None:
        self.creado = creado
        self.llamadas: list[dict] = []

    def crear_si_no_existe(self, **kwargs):
        self.llamadas.append(dict(kwargs))
        from ruesma_comun.workflows.repositorio import ResultadoCreacion

        return ResultadoCreacion(
            workflow_id="wf-1", creado=self.creado, estado_actual="email_received"
        )


class AlmacenDoble:
    def __init__(self, diario: list | None = None) -> None:
        self.subidas: list[tuple] = []
        self._diario = diario if diario is not None else []

    def put_bytes(self, contenedor, nombre, data, *, content_type=None, metadata=None):
        self.subidas.append((contenedor, nombre, data, content_type, metadata))
        self._diario.append("blob")


class PublicadorDoble:
    def __init__(self, diario: list | None = None) -> None:
        self.publicados: list[tuple] = []
        self._diario = diario if diario is not None else []

    def publicar(self, cola, mensaje):
        self.publicados.append((cola, mensaje))
        self._diario.append("cola")


def _inyector(repositorio=None, almacen=None, publicador=None, diario=None, pasada="2026-09-18-01"):
    diario = diario if diario is not None else []
    return inyeccion.Inyector(
        repositorio=repositorio or RepositorioDoble(),
        almacen=almacen or AlmacenDoble(diario),
        publicador=publicador or PublicadorDoble(diario),
        pasada_id=pasada,
    )


# --- R2 · la entrada replica la de sv1 --------------------------------------


def test_f047_r2_inyectar_crea_workflow_sube_blob_y_publica_extraccion():
    repositorio, diario = RepositorioDoble(), []
    almacen, publicador = AlmacenDoble(diario), PublicadorDoble(diario)
    inyector = _inyector(repositorio, almacen, publicador, diario)

    resultado = inyector.inyectar("RES-001", b"%PDF-falso", "RES-001.pdf")

    assert repositorio.llamadas, "no se creó la fila de workflow_runs"
    assert almacen.subidas[0][0] == CONTENEDOR_INPUT
    assert almacen.subidas[0][1] == f"{resultado.document_id}.pdf"
    cola, mensaje = publicador.publicados[0]
    assert cola == COLA_EXTRACCION
    assert mensaje.tipo == "extraccion"
    assert mensaje.document_id == resultado.document_id
    assert mensaje.correlation_key == resultado.correlation_key


def test_f047_r2_el_blob_se_sube_antes_de_publicar_el_mensaje():
    """Si el mensaje saliera primero, sv2 podría no encontrar el PDF."""
    diario: list[str] = []
    _inyector(diario=diario).inyectar("RES-001", b"%PDF", "RES-001.pdf")
    assert diario == ["blob", "cola"]


def test_f047_r2_el_document_id_es_un_uuid_y_viaja_a_los_tres_sitios():
    repositorio, diario = RepositorioDoble(), []
    almacen, publicador = AlmacenDoble(diario), PublicadorDoble(diario)
    resultado = _inyector(repositorio, almacen, publicador, diario).inyectar(
        "RES-001", b"%PDF", "RES-001.pdf"
    )

    uuid.UUID(resultado.document_id)  # revienta si no lo es
    assert repositorio.llamadas[0]["document_id"] == resultado.document_id
    assert almacen.subidas[0][1].startswith(resultado.document_id)
    assert publicador.publicados[0][1].document_id == resultado.document_id


def test_f047_r2_el_duplicado_no_sube_blob_ni_publica():
    repositorio = RepositorioDoble(creado=False)
    almacen, publicador = AlmacenDoble(), PublicadorDoble()
    resultado = _inyector(repositorio, almacen, publicador).inyectar(
        "RES-001", b"%PDF", "RES-001.pdf"
    )

    assert resultado.duplicado is True
    assert almacen.subidas == []
    assert publicador.publicados == []


def test_f047_r2_el_sha256_del_contenido_viaja_al_workflow():
    repositorio = RepositorioDoble()
    resultado = _inyector(repositorio).inyectar("RES-001", b"%PDF", "RES-001.pdf")
    assert repositorio.llamadas[0]["attachment_sha256"] == resultado.sha256
    assert len(resultado.sha256) == 64


def test_f047_r2_el_payload_declara_caso_y_pasada_sin_datos_del_albaran():
    repositorio = RepositorioDoble()
    _inyector(repositorio).inyectar("RES-001", b"%PDF", "RES-001.pdf")
    payload = json.loads(repositorio.llamadas[0]["payload_json"])
    assert payload["caso_id"] == "RES-001"
    assert payload["pasada_id"] == "2026-09-18-01"
    assert payload["origen"] == "evals"


# --- R16 · aislamiento ------------------------------------------------------


def test_f047_r16_la_clave_lleva_prefijo_pasada_y_caso():
    assert (
        inyeccion.clave_correlacion("2026-09-18-01", "RES-001")
        == "eval/2026-09-18-01/RES-001"
    )


def test_f047_r16_dos_casos_de_la_misma_pasada_no_comparten_clave_ni_documento():
    inyector = _inyector()
    uno = inyector.inyectar("RES-001", b"%PDF", "RES-001.pdf")
    otro = inyector.inyectar("HOR-003", b"%PDF", "HOR-003.pdf")

    assert uno.correlation_key != otro.correlation_key
    assert uno.document_id != otro.document_id


def test_f047_r16_dos_pasadas_del_mismo_caso_no_comparten_clave():
    uno = _inyector(pasada="2026-09-18-01").inyectar("RES-001", b"%PDF", "a.pdf")
    otro = _inyector(pasada="2026-09-18-02").inyectar("RES-001", b"%PDF", "a.pdf")
    assert uno.correlation_key != otro.correlation_key


def test_f047_r16_el_id_de_pasada_numera_dentro_del_dia():
    assert inyeccion.nuevo_pasada_id("2026-09-18", 1) == "2026-09-18-01"
    assert inyeccion.nuevo_pasada_id("2026-09-18", 12) == "2026-09-18-12"


def test_f047_r16_reconocer_una_clave_del_banco_y_su_caso():
    clave = inyeccion.clave_correlacion("2026-09-18-01", "RES-001")
    assert inyeccion.es_del_banco(clave) is True
    assert inyeccion.es_del_banco("email:AAA:bbb") is False
    assert inyeccion.partes_de_clave(clave) == ("2026-09-18-01", "RES-001")
    assert inyeccion.partes_de_clave("email:AAA:bbb") is None


@pytest.mark.parametrize("sucio", ["RES/001", "eval/x", "RES 001/"])
def test_f047_r16_un_caso_con_barra_no_puede_fabricar_una_clave_ambigua(sucio):
    """Sin esto, `partes_de_clave` devolvería un caso que no es el inyectado."""
    with pytest.raises(inyeccion.ClaveAmbigua):
        inyeccion.clave_correlacion("2026-09-18-01", sucio)


# --- Reentradas por los puntos que el sistema ya ofrece (R24) ----------------


def test_f047_r2_republicar_persistencia_pide_refetch_con_force():
    publicador = PublicadorDoble()
    inyector = _inyector(publicador=publicador)
    inyector.republicar_persistencia("doc-1", "eval/2026-09-18-01/RES-001")

    cola, mensaje = publicador.publicados[0]
    assert cola == COLA_PERSISTENCIA
    assert mensaje.tipo == "persistencia"
    assert mensaje.force is True


def test_f047_r2_republicar_valoracion_lleva_el_contrato_declarado():
    publicador = PublicadorDoble()
    inyector = _inyector(publicador=publicador)
    inyector.republicar_valoracion(
        "doc-1", "eval/2026-09-18-01/RES-001", codigo_contrato="CTSU24/0228"
    )

    cola, mensaje = publicador.publicados[0]
    assert cola == COLA_VALORACION
    assert mensaje.codigo_contrato == "CTSU24/0228"


def test_f047_r16_republicar_con_una_clave_ajena_al_banco_es_un_error():
    """El banco no reencola documentos que no son suyos, ni por error."""
    inyector = _inyector()
    with pytest.raises(inyeccion.ClaveAjena):
        inyector.republicar_valoracion("doc-1", "email:AAA:bbb")
