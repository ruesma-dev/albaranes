# tests/test_f048_r42_encolar.py
"""F-048 · R42: ``encolar_extraccion.py --correo <json>``.

El script de pruebas locales encola un documento en ``q-extraccion``. Con
``--correo`` lee un fichero de captura (el formato de
``capturar_correo.py`` de sv1: ``asunto`` y ``cuerpo`` tal cual) y:

- construye el contexto con ``construir_contexto_correo`` y lo guarda con
  ``guardar_contexto_correo``: las MISMAS funciones de ``ruesma_comun`` que
  usa sv1, asi la huella sale igual que si hubiera entrado por el buzon;
- guarda el blob lateral ANTES de publicar, y el mensaje lleva
  ``correo_blob``;
- por pantalla solo la huella abreviada y los caracteres, nunca el texto.

Sin ``--correo``, el mensaje es el de siempre y no se toca Blob. Sin red: el
publicador y el almacen son dobles.
"""
from __future__ import annotations

import json

import encolar_extraccion
import pytest
from ruesma_comun.blobs import CONTENEDOR_INPUT
from ruesma_comun.colas import COLA_EXTRACCION, MensajeExtraccion
from ruesma_comun.correo import construir_contexto_correo, nombre_blob_correo

CENTINELA = "CENTINELA-F048"
ASUNTO = "RV: albaran obra 945"
CUERPO = f"Buenos dias,\n\nOs paso el albaran de la 945.   {CENTINELA}\n"


class Diario:
    """Registra en orden lo que se escribe y lo que se publica."""

    def __init__(self) -> None:
        self.eventos: list[tuple] = []


class AlmacenDoble:
    def __init__(self, diario: Diario) -> None:
        self._diario = diario
        self.blobs: dict = {}

    def put_json(self, contenedor, nombre, objeto):
        self._diario.eventos.append(("blob", contenedor, nombre))
        self.blobs[(contenedor, nombre)] = objeto

    def get_json(self, contenedor, nombre):  # pragma: no cover
        return self.blobs[(contenedor, nombre)]


class PublicadorDoble:
    def __init__(self, diario: Diario) -> None:
        self._diario = diario
        self.publicados: list[tuple[str, MensajeExtraccion]] = []

    def publicar(self, cola, mensaje):
        self._diario.eventos.append(("cola", cola, mensaje.document_id))
        self.publicados.append((cola, mensaje))


@pytest.fixture
def entorno(monkeypatch):
    """Dobles del publicador y del almacen; el ``.env`` real no se carga."""
    diario = Diario()
    publicador, almacen = PublicadorDoble(diario), AlmacenDoble(diario)
    almacenes: list[AlmacenDoble] = []

    def _almacen():
        almacenes.append(almacen)
        return almacen

    monkeypatch.setattr(encolar_extraccion, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(encolar_extraccion, "construir_publicador", lambda **k: publicador)
    monkeypatch.setattr(encolar_extraccion, "construir_almacen_desde_entorno", _almacen)
    return diario, publicador, almacen, almacenes


def _captura(tmp_path, **datos) -> str:
    contenido = {"version": 1, "caso_id": "caso-1", "asunto": ASUNTO, "cuerpo": CUERPO,
                 "tipo_origen": "text", "recibido_utc": "2026-09-22T08:00:00Z", **datos}
    ruta = tmp_path / "caso-1.json"
    ruta.write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")
    return str(ruta)


def test_f048_r42_con_correo_guarda_el_blob_con_la_funcion_de_comun_y_lo_pone_en_el_mensaje(entorno, tmp_path):
    diario, publicador, almacen, _ = entorno

    assert encolar_extraccion.main(["DOC-1", "--correo", _captura(tmp_path)]) == 0

    esperado = construir_contexto_correo(ASUNTO, CUERPO, recibido_utc="2026-09-22T08:00:00Z")
    nombre = nombre_blob_correo("DOC-1")
    assert almacen.blobs == {(CONTENEDOR_INPUT, nombre): esperado.model_dump(mode="json")}
    cola, mensaje = publicador.publicados[0]
    assert cola == COLA_EXTRACCION
    assert mensaje.document_id == "DOC-1"
    assert mensaje.correo_blob == nombre
    # El blob, ANTES de publicar (R7): el worker no puede ir a buscarlo antes.
    assert diario.eventos == [("blob", CONTENEDOR_INPUT, nombre), ("cola", COLA_EXTRACCION, "DOC-1")]


def test_f048_r42_la_huella_es_la_que_calcula_sv1(entorno, tmp_path):
    _, _, almacen, _ = entorno

    encolar_extraccion.main(["DOC-1", "--correo", _captura(tmp_path)])

    (guardado,) = almacen.blobs.values()
    assert guardado["sha256"] == construir_contexto_correo(ASUNTO, CUERPO).sha256


def test_f048_r42_por_pantalla_solo_la_huella_y_los_caracteres(entorno, tmp_path, capsys):
    encolar_extraccion.main(["DOC-1", "--correo", _captura(tmp_path)])

    salida = capsys.readouterr()
    ctx = construir_contexto_correo(ASUNTO, CUERPO)
    assert ctx.sha256[:8] in salida.out
    assert str(ctx.caracteres_originales) in salida.out
    assert CENTINELA not in salida.out + salida.err
    assert ASUNTO not in salida.out + salida.err


def test_f048_r42_sin_correo_el_mensaje_es_el_de_siempre_y_no_se_toca_blob(entorno):
    _, publicador, almacen, almacenes = entorno

    assert encolar_extraccion.main(["DOC-2"]) == 0

    _, mensaje = publicador.publicados[0]
    assert mensaje.document_id == "DOC-2"
    assert mensaje.correlation_key == "corr-DOC-2"
    assert mensaje.correo_blob is None
    assert almacenes == []
    assert almacen.blobs == {}


def test_f048_r42_sin_argumentos_sigue_el_documento_de_prueba(entorno):
    _, publicador, _, _ = entorno

    encolar_extraccion.main([])

    assert publicador.publicados[0][1].document_id == "DOC-PRUEBA-1"


@pytest.mark.parametrize(
    "fichero",
    ["no_existe.json", "roto.json", "sin_cuerpo.json", "no_es_objeto.json"],
)
def test_f048_r42_un_fichero_de_correo_malo_para_sin_escribir_ni_publicar(entorno, tmp_path, capsys, fichero):
    _, publicador, almacen, _ = entorno
    (tmp_path / "roto.json").write_text(f"{{ no es json {CENTINELA}", encoding="utf-8")
    (tmp_path / "sin_cuerpo.json").write_text(json.dumps({"asunto": ASUNTO}), encoding="utf-8")
    (tmp_path / "no_es_objeto.json").write_text(json.dumps([ASUNTO, CUERPO]), encoding="utf-8")

    with pytest.raises(SystemExit) as salida:
        encolar_extraccion.main(["DOC-3", "--correo", str(tmp_path / fichero)])

    assert salida.value.code == 2
    assert publicador.publicados == []
    assert almacen.blobs == {}
    assert CENTINELA not in capsys.readouterr().err
