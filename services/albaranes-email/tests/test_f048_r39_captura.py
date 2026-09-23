# tests/test_f048_r39_captura.py
"""R38 y R39 (F-048, T12): ``capturar_correo.py`` es de SOLO LECTURA.

Dado un ``message_id``, pide el contenido por el camino de R2
(``get_contenido``) y lo guarda en ``evals/inputs/correos/{caso_id}.json``
sin mover, marcar ni modificar nada: el buzon doble revienta ante
cualquier otro metodo. La ruta de salida la ignora git (R38): un correo
real nunca se versiona. Textos inventados; ningun test sale a la red.
"""
from __future__ import annotations

import json
import shutil
import subprocess

import capturar_correo
import pytest
from dobles_sv1 import BUZON, CENTINELA
from ruesma_comun.correo import construir_contexto_correo

from domain.models.email_models import ContenidoCorreo
from domain.ports.mailbox_client import MailboxClient

CONTENIDO = ContenidoCorreo(
    asunto="RE: Albaran obra 0945",
    cuerpo_unico=f"Va para la 0945.\n{CENTINELA}",
    tipo="html",
)


class BuzonSoloLectura(MailboxClient):
    """Solo admite ``get_contenido``; cualquier otro metodo hace fallar el test."""

    def __init__(self, contenido: ContenidoCorreo | Exception = CONTENIDO) -> None:
        self._contenido = contenido
        self.pedidos: list[tuple[str, str]] = []

    def get_contenido(self, mailbox: str, message_id: str) -> ContenidoCorreo:
        self.pedidos.append((mailbox, message_id))
        if isinstance(self._contenido, Exception):
            raise self._contenido
        return self._contenido

    def _prohibido(self, *args: object, **kwargs: object) -> None:
        raise AssertionError("la captura es de solo lectura: metodo prohibido")

    move_message = _prohibido
    ensure_folder = _prohibido
    assert_folder_accessible = _prohibido
    list_unread_with_attachments = _prohibido
    list_attachments = _prohibido
    download_attachment_value = _prohibido


def test_f048_r39_captura_solo_pide_el_contenido_y_lo_guarda(tmp_path):
    buzon = BuzonSoloLectura()

    ruta = capturar_correo.capturar(
        buzon, mailbox=BUZON, message_id="msg-1", caso_id="ALB-001", directorio=tmp_path
    )

    assert ruta == tmp_path / "ALB-001.json"
    assert buzon.pedidos == [(BUZON, "msg-1")]
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["version"] == capturar_correo.VERSION_CAPTURA == 1
    assert datos["caso_id"] == "ALB-001"
    assert datos["message_id"] == "msg-1"
    assert datos["asunto"] == CONTENIDO.asunto
    assert datos["cuerpo"] == CONTENIDO.cuerpo_unico
    assert datos["tipo_origen"] == "html"
    assert datos["capturado_utc"].endswith("Z")


def test_f048_r39_el_fichero_da_el_mismo_contexto_que_sv1(tmp_path):
    """Asunto y cuerpo SIN normalizar: quien lo lea usa la misma funcion que sv1."""
    ruta = capturar_correo.capturar(
        BuzonSoloLectura(), mailbox=BUZON, message_id="msg-1", caso_id="c1", directorio=tmp_path
    )

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert construir_contexto_correo(datos["asunto"], datos["cuerpo"]) == construir_contexto_correo(
        CONTENIDO.asunto, CONTENIDO.cuerpo_unico
    )


def test_f048_r39_el_buzon_doble_revienta_si_se_intenta_mover():
    """Control del propio doble."""
    with pytest.raises(AssertionError, match="solo lectura"):
        BuzonSoloLectura().move_message(mailbox=BUZON, message_id="m", destination_folder_id="x")


@pytest.mark.parametrize("caso", ["", "../fuera", "a/b", "a\\b", ".oculto", "caso con espacio"])
def test_f048_r39_caso_invalido_no_pide_nada_ni_escribe(tmp_path, caso):
    buzon = BuzonSoloLectura()

    with pytest.raises(ValueError):
        capturar_correo.capturar(
            buzon, mailbox=BUZON, message_id="msg-1", caso_id=caso, directorio=tmp_path
        )

    assert buzon.pedidos == []
    assert list(tmp_path.iterdir()) == []


def test_f048_r39_si_graph_falla_no_escribe_nada(tmp_path):
    with pytest.raises(RuntimeError):
        capturar_correo.capturar(
            BuzonSoloLectura(RuntimeError("Graph 500")),
            mailbox=BUZON, message_id="msg-1", caso_id="c1", directorio=tmp_path,
        )

    assert list(tmp_path.iterdir()) == []


def test_f048_r39_main_captura_con_el_buzon_del_entorno(tmp_path, monkeypatch, capsys):
    buzon = BuzonSoloLectura()
    monkeypatch.setattr(capturar_correo, "_buzon_desde_entorno", lambda: (buzon, BUZON))

    codigo = capturar_correo.main(
        ["--message-id", "msg-9", "--caso", "ALB-009", "--directorio", str(tmp_path)]
    )

    assert codigo == 0
    assert buzon.pedidos == [(BUZON, "msg-9")]
    assert (tmp_path / "ALB-009.json").is_file()
    salida = capsys.readouterr().out
    assert "ALB-009.json" in salida
    assert construir_contexto_correo(CONTENIDO.asunto, CONTENIDO.cuerpo_unico).sha256[:8] in salida
    assert CENTINELA not in salida


def test_f048_r39_buzon_desde_entorno_usa_el_cliente_de_graph(monkeypatch):
    """Sin leer el ``.env`` real: Settings, dotenv y el token son dobles."""

    class _SettingsFalso:
        mailbox_address = BUZON
        graph_key = "clave-falsa"
        graph_timeout_s = 7

    llamadas: list = []
    monkeypatch.setattr(capturar_correo, "load_dotenv", lambda ruta: llamadas.append(("dotenv", ruta)))
    monkeypatch.setattr(capturar_correo, "Settings", _SettingsFalso)
    monkeypatch.setattr(
        capturar_correo, "GraphTokenProvider",
        lambda clave, timeout_s: llamadas.append(("token", clave, timeout_s)) or "proveedor",
    )

    buzon, mailbox = capturar_correo._buzon_desde_entorno()

    assert mailbox == BUZON
    assert isinstance(buzon, capturar_correo.GraphMailClient)
    assert llamadas == [
        ("dotenv", capturar_correo.RAIZ_SERVICIO / ".env"),
        ("token", "clave-falsa", 7),
    ]


def test_f048_r38_la_ruta_de_salida_por_defecto_la_ignora_git():
    esperado = capturar_correo.RAIZ_SERVICIO.parents[1] / "evals" / "inputs" / "correos"
    assert capturar_correo.DIRECTORIO_SALIDA == esperado
    if shutil.which("git") is None:
        pytest.skip("git no disponible")

    resultado = subprocess.run(
        ["git", "check-ignore", "-q", str(esperado / "ALB-001.json")],
        cwd=capturar_correo.RAIZ_SERVICIO,
        check=False,
    )

    assert resultado.returncode == 0, "evals/inputs/correos/ tiene que estar ignorada por git"
