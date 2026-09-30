# tests/test_f048_t34_supervivientes.py
"""F-048 · T34: los supervivientes de la campaña de mutación de sv1.

Cada test nombra el mutante (numeración de ``progress/mutacion_F-048.md``).
Los que eran huecos reales tienen aquí el test que los mata; los tres
equivalentes (9, 22 y 23) tienen una GUARDA: no los mata —nada puede— pero
fija el invariante del que depende su equivalencia, para que el día que deje
de cumplirse el mutante pase a ser un hueco y se vea. El análisis de los 26
está en ``progress/impl_F-048_T34_supervivientes.md``.

Ningún test sale a la red ni toca el buzón: dobles y textos inventados.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import subprocess

import capturar_correo
import httpx
import pytest
from config.settings import Settings
from dobles_sv1 import (
    BUZON,
    CENTINELA,
    AlmacenDoble,
    BuzonDoble,
    IntakeDoble,
    PublicadorDoble,
    RepositorioDoble,
    adjunto,
    construir_pipeline,
    ejecutar_ciclo,
    mensaje,
    pdf_de_paginas,
)
from domain.models.email_models import ContenidoCorreo
from infrastructure.colas.intake_cola_adapter import IntakeColaClient
from infrastructure.graph.mail_client import GraphMailClient, html_a_texto
from ruesma_comun.correo import construir_contexto_correo

CONTENIDO = ContenidoCorreo(
    asunto="RE: Albarán obra 0945",
    cuerpo_unico=f"Va para la obra nº 0945, camión grúa.\n{CENTINELA}",
    tipo="text",
    recibido_utc="2026-09-23T08:00:00Z",
)


class _BuzonSoloContenido:
    def __init__(self) -> None:
        self.pedidos: list[tuple[str, str]] = []

    def get_contenido(self, mailbox: str, message_id: str) -> ContenidoCorreo:
        self.pedidos.append((mailbox, message_id))
        return CONTENIDO


def _sha8_con_separador(ctx) -> str:
    """La huella abreviada, con lo que la sigue: 8 hex y un espacio, no 9."""
    return f"sha={ctx.sha256[:8]} caracteres={ctx.caracteres_originales}"


# ---------------------------------------------------------------- #
# Mutante 8 · polling_pipeline.py:399 (``[:8]`` -> ``[:9]``). R36: el log
# lleva la huella ABREVIADA, la misma en sv1, sv2 y los scripts.
# ---------------------------------------------------------------- #
def test_f048_r36_el_log_del_pipeline_lleva_la_huella_de_ocho_caracteres(caplog):
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("att-1")]},
        ficheros={"att-1": pdf_de_paginas(1)},
    )
    intake = IntakeDoble()

    with caplog.at_level(logging.INFO):
        ejecutar_ciclo(construir_pipeline(buzon, intake))

    ctx = intake.envios[0].contexto_correo
    assert f"contexto de correo {_sha8_con_separador(ctx)} truncado=" in caplog.text
    assert CENTINELA not in caplog.text


# ---------------------------------------------------------------- #
# Mutantes 20 y 21 · intake_cola_adapter.py:89 y :178 (R10, R36).
# ---------------------------------------------------------------- #
def _intake():
    llamadas: list = []
    repo = RepositorioDoble(llamadas)
    cliente = IntakeColaClient(
        repositorio=repo, almacen=AlmacenDoble(llamadas), publicador=PublicadorDoble(llamadas),
    )
    return cliente, repo


def _enviar(cliente, meta: dict, contexto) -> None:
    cliente.submit_email_received(
        meta=meta, file_bytes=b"%PDF-falso", filename="albaran.pdf",
        content_type="application/pdf", contexto_correo=contexto,
    )


def test_f048_r10_sin_correo_el_payload_es_byte_a_byte_el_de_antes_tambien_con_acentos():
    """Mutante 20: ``payload_json`` se serializaba con ``ensure_ascii=False`` antes de F-048."""
    meta = {"email_message_id": "msg-1", "subject": "Albarán nº 12 — Hormigón", "page_sha256": "a" * 64}
    cliente, repo = _intake()

    _enviar(cliente, dict(meta), None)

    assert repo.payloads == [json.dumps(meta, ensure_ascii=False)]
    assert "Albarán nº 12 — Hormigón" in repo.payloads[0]


def test_f048_r10_con_correo_el_payload_añade_la_huella_sin_escapar_el_resto():
    meta = {"email_message_id": "msg-1", "subject": "Albarán nº 12", "page_sha256": "a" * 64}
    ctx = construir_contexto_correo(CONTENIDO.asunto, CONTENIDO.cuerpo_unico)
    cliente, repo = _intake()

    _enviar(cliente, dict(meta), ctx)

    assert repo.payloads == [json.dumps({**meta, "correo_sha256": ctx.sha256}, ensure_ascii=False)]


def test_f048_r36_el_log_del_intake_lleva_la_huella_de_ocho_caracteres(caplog):
    """Mutante 21."""
    ctx = construir_contexto_correo(CONTENIDO.asunto, CONTENIDO.cuerpo_unico)
    cliente, _ = _intake()

    with caplog.at_level(logging.INFO):
        _enviar(cliente, {"email_message_id": "msg-1", "page_sha256": "a" * 64}, ctx)

    assert f"correo=SI({_sha8_con_separador(ctx)} truncado={ctx.truncado})" in caplog.text
    assert CENTINELA not in caplog.text


# ---------------------------------------------------------------- #
# Mutantes 9, 10 y 11 · capturar_correo.py:69-71, ``git check-ignore``.
# ---------------------------------------------------------------- #
def test_f048_r38_git_check_ignore_no_ensucia_la_consola(tmp_path, capfd):
    """Mutante 10: fuera del repositorio git escribe ``fatal: ...`` en stderr; se captura."""
    if capturar_correo.shutil.which("git") is None:
        pytest.skip("git no disponible")

    assert capturar_correo.ruta_ignorada_por_git(tmp_path / "fuera.json") is False

    salida = capfd.readouterr()
    assert salida.out == ""
    assert salida.err == ""


def test_f048_r38_git_check_ignore_tiene_un_tope_de_30_segundos(monkeypatch):
    """Mutante 11: si git se cuelga, el CLI no espera más de 30 s y rechaza la ruta."""
    llamadas: list[dict] = []

    def _run(orden, **opciones):
        llamadas.append(opciones)
        raise subprocess.TimeoutExpired(orden, opciones["timeout"])

    monkeypatch.setattr(capturar_correo.shutil, "which", lambda nombre: "git")
    monkeypatch.setattr(capturar_correo.subprocess, "run", _run)

    assert capturar_correo.ruta_ignorada_por_git(capturar_correo.ruta_captura("ALB-001")) is False
    assert [opciones["timeout"] for opciones in llamadas] == [30]


@pytest.mark.parametrize(("codigo", "esperado"), [(0, True), (1, False), (128, False)])
def test_f048_r38_guarda_el_resultado_solo_depende_del_codigo_de_git(monkeypatch, codigo, esperado):
    """GUARDA del mutante 9 (``check=False`` -> ``True``), equivalente.

    El doble de ``subprocess.run`` respeta ``check`` como el de verdad: con
    ``check=True`` y un código distinto de 0 lanza ``CalledProcessError``, que
    es un ``SubprocessError`` y cae en el ``except`` que devuelve ``False``.
    Por eso los dos valores de ``check`` dan el mismo resultado para todo
    código: 0 -> ``True``, cualquier otro -> ``False``. Si mañana el
    ``except`` dejara de cubrir ``CalledProcessError``, esta guarda cae.
    """
    assert issubclass(subprocess.CalledProcessError, subprocess.SubprocessError)

    def _run(orden, *, check=False, **opciones):
        if check and codigo != 0:
            raise subprocess.CalledProcessError(codigo, orden)
        return subprocess.CompletedProcess(orden, codigo, b"", b"")

    monkeypatch.setattr(capturar_correo.shutil, "which", lambda nombre: "git")
    monkeypatch.setattr(capturar_correo.subprocess, "run", _run)

    assert capturar_correo.ruta_ignorada_por_git(capturar_correo.ruta_captura("ALB-001")) is esperado


# ---------------------------------------------------------------- #
# Mutantes 12, 13 y 14 · capturar_correo.py:99-100, el fichero de captura.
# ---------------------------------------------------------------- #
def test_f048_r39_la_captura_crea_los_directorios_que_falten(tmp_path):
    """Mutante 12: en un clon limpio ``evals/inputs/correos`` puede no existir, ni su padre."""
    directorio = tmp_path / "evals" / "inputs" / "correos"

    ruta = capturar_correo.capturar(
        _BuzonSoloContenido(), mailbox=BUZON, message_id="msg-1", caso_id="ALB-001", directorio=directorio,
    )

    assert ruta == directorio / "ALB-001.json"
    assert ruta.is_file()


def test_f048_r39_el_fichero_de_captura_es_utf8_legible_con_sangria_2(tmp_path):
    """Mutantes 13 y 14: el texto se mira ABRIENDO el fichero; los acentos, tal cual."""
    ruta = capturar_correo.capturar(
        _BuzonSoloContenido(), mailbox=BUZON, message_id="msg-1", caso_id="ALB-001", directorio=tmp_path,
    )

    texto = ruta.read_text(encoding="utf-8")
    assert "RE: Albarán obra 0945" in texto
    assert "obra nº 0945, camión grúa" in texto
    assert "\\u00" not in texto
    assert texto == json.dumps(json.loads(texto), ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- #
# Mutantes 15, 16 y 17 · capturar_correo.py:117, :118 y :144 (el CLI).
# ---------------------------------------------------------------- #
def _no_se_puede_crear_el_buzon():
    raise AssertionError("sin los argumentos obligatorios no se lee el .env ni se habla con Graph")


@pytest.mark.parametrize(
    ("argumentos", "falta"),
    [
        (["--caso", "ALB-001"], "--message-id"),
        (["--message-id", "msg-1"], "--caso"),
    ],
    ids=["sin_message_id", "sin_caso"],
)
def test_f048_r39_el_cli_exige_message_id_y_caso(tmp_path, monkeypatch, capsys, argumentos, falta):
    """Mutantes 15 y 16: error de uso (código 2) antes de tocar nada."""
    monkeypatch.setattr(capturar_correo, "_buzon_desde_entorno", _no_se_puede_crear_el_buzon)
    monkeypatch.setattr(capturar_correo, "ruta_ignorada_por_git", lambda ruta: True)

    with pytest.raises(SystemExit) as fallo:
        capturar_correo.main([*argumentos, "--directorio", str(tmp_path)])

    assert fallo.value.code == 2
    assert falta in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_f048_r39_por_pantalla_la_huella_de_ocho_caracteres(tmp_path, monkeypatch, capsys):
    """Mutante 17."""
    monkeypatch.setattr(capturar_correo, "_buzon_desde_entorno", lambda: (_BuzonSoloContenido(), BUZON))
    monkeypatch.setattr(capturar_correo, "ruta_ignorada_por_git", lambda ruta: True)
    ctx = construir_contexto_correo(CONTENIDO.asunto, CONTENIDO.cuerpo_unico)

    assert capturar_correo.main(["--message-id", "msg-1", "--caso", "ALB-001", "--directorio", str(tmp_path)]) == 0

    salida = capsys.readouterr().out
    assert f"({_sha8_con_separador(ctx)} tipo=text)" in salida
    assert CENTINELA not in salida


# ---------------------------------------------------------------- #
# Mutante 18 · config/settings.py:48 (``gt=0`` -> ``gt=1``). R1: el máximo
# es configurable y positivo; 1 es positivo.
# ---------------------------------------------------------------- #
def test_f048_r1_correo_max_caracteres_admite_1(monkeypatch):
    monkeypatch.delenv("CORREO_MAX_CARACTERES", raising=False)
    obligatorias = {"MAILBOX_ADDRESS": "b@ejemplo.test", "GRAPH_KEY": "k", "PG_PASSWORD": "p"}

    assert Settings(_env_file=None, CORREO_MAX_CARACTERES="1", **obligatorias).correo_max_caracteres == 1


# ---------------------------------------------------------------- #
# Mutante 19 · email_models.py:26 (``ContenidoCorreo`` deja de ser frozen).
# R6: el MISMO contexto se aplica a todas las páginas de un mensaje; el
# contenido del que sale no se puede tocar por el camino.
# ---------------------------------------------------------------- #
def test_f048_r6_el_contenido_del_correo_es_inmutable():
    contenido = ContenidoCorreo(asunto="Albaran", cuerpo_unico="Obra 0945")

    with pytest.raises(dataclasses.FrozenInstanceError):
        contenido.cuerpo_unico = "otra cosa"  # type: ignore[misc]
    assert hash(contenido) == hash(ContenidoCorreo(asunto="Albaran", cuerpo_unico="Obra 0945"))


# ---------------------------------------------------------------- #
# Mutantes 22 y 23 · mail_client.py:39 y :45, el contador de ``script`` y
# ``style``. EQUIVALENTES: GUARDA del invariante.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("html", "esperado"),
    [
        ("<script><style>x</style>y</script>z", "z"),
        ("<style><script>x</script>y</style>z", "z"),
        ("<style>a</style>b<style>c</style>d", "bd"),
        ("</style>a<style>b", "a"),
        ("<style/>a", "a"),
        ("<STYLE>a</STYLE>b", "b"),
    ],
    ids=["script_con_style", "style_con_script", "dos_seguidos", "cierre_suelto", "autocerrado", "mayusculas"],
)
def test_f048_r4_guarda_dentro_de_script_y_style_no_hay_etiquetas(html, esperado):
    """GUARDA de los mutantes 22 (``+= 1`` -> ``-= 1``) y 23 (``- 1`` -> ``- 2``).

    ``HTMLParser`` trata el contenido de ``script`` y ``style`` como texto
    crudo (CDATA): tras abrir uno, el siguiente evento de etiqueta es SU
    cierre. El contador nunca pasa de 1 (original) ni baja de -1 (mutante 22),
    y 1 y -1 son los dos «verdadero»; y como nunca pasa de 1, restar 1 o 2
    antes del ``max(0, ...)`` deja el mismo 0 (mutante 23). Si el parser
    empezara a anidar etiquetas dentro de ``script``/``style``, la primera
    fila de esta tabla cambiaría y los dos mutantes pasarían a ser huecos.
    """
    assert html_a_texto(html) == esperado


def test_f048_r4_demostracion_los_mutantes_22_y_23_no_cambian_ninguna_salida():
    """Demostración EJECUTABLE de la equivalencia (RM5), diferencial.

    Toma el extractor del ``mail_client.py`` real, fabrica las dos variantes
    mutadas sustituyendo el texto de la línea y compara ``html_a_texto`` de
    las tres sobre TODAS las secuencias de hasta 4 fichas de un alfabeto de
    12 (22.620) y 3.000 aleatorias de 5 a 20: cero discrepancias. La versión larga
    (hasta 5 fichas y 50.000 aleatorias, 321.452 casos) está en el informe
    de T34. El control final prueba que la comparación no es ciega. Si
    alguien reescribe esas líneas y no queda ni la forma original ni la
    mutada, el test avisa: la justificación hay que rehacerla.
    """
    import itertools
    import random
    from pathlib import Path

    import infrastructure.graph.mail_client as modulo

    fuente = Path(modulo.__file__).read_text(encoding="utf-8")
    trozo = fuente[fuente.index("# Etiquetas que separan bloques"):fuente.index("class GraphMailClient")]
    sustituciones = {
        "m22": ("self._dentro_sin_texto += 1", "self._dentro_sin_texto -= 1"),
        "m23": ("self._dentro_sin_texto - 1)", "self._dentro_sin_texto - 2)"),
        "control": ("if not self._dentro_sin_texto:", "if True:"),
    }

    def _cargar(codigo: str):
        espacio: dict = {}
        exec("from html.parser import HTMLParser\n" + codigo, espacio)  # noqa: S102 — fuente propia
        return espacio["html_a_texto"]

    # La variante es «la otra forma» de la línea: el mutante si el fichero
    # trae el original y el original si trae el mutante. Así la demostración
    # sigue comparando original contra mutante cuando una campaña inyecta
    # uno de los dos en el propio ``mail_client.py``, y un equivalente no
    # sale muerto por leer su propia fuente (RM3).
    variantes = {}
    for nombre, (original, mutado) in sustituciones.items():
        forma = {trozo.count(original), trozo.count(mutado)}
        assert forma == {0, 1}, f"{nombre}: la línea cambió; rehacer la justificación"
        de, a = (original, mutado) if original in trozo else (mutado, original)
        variantes[nombre] = _cargar(trozo.replace(de, a))
    fichas = ["<script>", "</script>", "<style>", "</style>", "<style/>", "<SCRIPT>",
              "<p>", "</p>", "<br>", "a", "b", "</div>"]
    azar = random.Random(48)
    secuencias = [s for n in range(1, 5) for s in itertools.product(fichas, repeat=n)]
    secuencias += [tuple(azar.choice(fichas) for _ in range(azar.randint(5, 20))) for _ in range(3000)]

    discrepancias = {"m22": 0, "m23": 0}
    for secuencia in secuencias:
        html = "".join(secuencia)
        esperado = html_a_texto(html)
        for nombre in discrepancias:
            discrepancias[nombre] += variantes[nombre](html) != esperado

    assert len(secuencias) == 25_620
    assert discrepancias == {"m22": 0, "m23": 0}
    assert variantes["control"]("<style>x</style>y") != html_a_texto("<style>x</style>y")


# ---------------------------------------------------------------- #
# Mutantes 24 y 25 · mail_client.py:305 (``>= 300`` -> ``> 300`` y
# ``>= 301``). R5: una respuesta que no es 2xx es un fallo; un 300 (Graph
# sin seguir redirecciones, que httpx no sigue por defecto) no trae el correo.
# ---------------------------------------------------------------- #
class _Token:
    def get_token(self) -> str:
        return "token-de-prueba"


@pytest.mark.parametrize("estado", [300, 301, 302])
def test_f048_r5_un_3xx_al_pedir_el_contenido_es_un_fallo(estado):
    def _graph(request: httpx.Request) -> httpx.Response:
        return httpx.Response(estado, json={"subject": "Albaran", "uniqueBody": {"content": CENTINELA}})

    cliente = GraphMailClient(
        token_provider=_Token(), timeout_s=5,
        http_client=httpx.Client(transport=httpx.MockTransport(_graph)),
    )

    with pytest.raises(RuntimeError) as info:
        cliente.get_contenido(mailbox=BUZON, message_id="msg-1")

    assert str(estado) in str(info.value)
    assert CENTINELA not in str(info.value)
