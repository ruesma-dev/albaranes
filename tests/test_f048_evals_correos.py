# tests/test_f048_evals_correos.py
"""F-048 · T29 — el correo de un caso del banco, y que nunca se versiona (R38, R40).

`evals/correos.py` lee la captura de `capturar_correo.py` (sv1) de
`evals/inputs/correos/{caso_id}.json` y construye el contexto con la MISMA
función de `ruesma_comun` que sv1, para que la huella salga igual que si el
correo hubiera entrado por el buzón. Sin fichero, el caso va sin correo.

R38: un correo real no puede acabar en git. Se comprueba por dos lados: la
carpeta de capturas la ignora git, y NINGÚN fichero versionado bajo `evals/` o
`tests/` tiene la firma de una captura o de un contexto de correo. Los tests
fabrican sus capturas en `tmp_path`: ni siquiera una sintética se versiona.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from ruesma_comun.correo import construir_contexto_correo

from evals import correos

RAIZ = Path(__file__).resolve().parents[1]
CENTINELA = "CENTINELA-CORREO-F048-4417"


def _captura(caso_id: str = "RES-001", **cambios) -> dict:
    """Una captura con la forma exacta que escribe `capturar_correo.py` (version 1)."""
    datos = {
        "version": 1,
        "caso_id": caso_id,
        "message_id": "AAMk-sintetico",
        "asunto": "  RV:  Albarán   obra 0945 ",
        "cuerpo": "Hola,\r\n\r\n\r\n\tadjunto albarán de la obra 0945.\r\nUn saludo",
        "tipo_origen": "text",
        "recibido_utc": "2026-09-20T08:15:00Z",
        "capturado_utc": "2026-09-24T10:00:00Z",
    }
    datos.update(cambios)
    return datos


def _escribir(directorio: Path, caso_id: str, contenido) -> Path:
    ruta = directorio / f"{caso_id}.json"
    if isinstance(contenido, bytes):
        ruta.write_bytes(contenido)
    elif isinstance(contenido, str):
        ruta.write_text(contenido, encoding="utf-8")
    else:
        ruta.write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")
    return ruta


# --- Carga (R40) ---------------------------------------------------------------


def test_f048_r40_sin_fichero_el_caso_va_sin_correo(tmp_path):
    assert correos.cargar_correo("RES-001", tmp_path) is None


def test_f048_r40_la_captura_se_construye_con_la_misma_funcion_que_sv1(tmp_path):
    datos = _captura()
    _escribir(tmp_path, "RES-001", datos)

    ctx = correos.cargar_correo("RES-001", tmp_path)

    esperado = construir_contexto_correo(
        datos["asunto"], datos["cuerpo"], recibido_utc=datos["recibido_utc"]
    )
    assert ctx == esperado
    assert ctx.sha256 == esperado.sha256
    assert ctx.asunto == "RV: Albarán obra 0945"


def test_f048_r40_un_cuerpo_largo_se_recorta_como_en_sv1(tmp_path):
    _escribir(tmp_path, "RES-001", _captura(cuerpo="x" * 5000))
    ctx = correos.cargar_correo("RES-001", tmp_path)
    assert ctx.truncado is True
    assert ctx.caracteres_originales == 5000
    assert len(ctx.cuerpo) == 4000


def test_f048_r40_una_copia_manual_con_solo_asunto_y_cuerpo_vale(tmp_path):
    """§7 del design admite copiar el correo a mano al JSON del caso."""
    _escribir(tmp_path, "HOR-003", {"asunto": "Obra 1203", "cuerpo": None})
    ctx = correos.cargar_correo("HOR-003", tmp_path)
    assert ctx.asunto == "Obra 1203"
    assert ctx.cuerpo == ""
    assert ctx.recibido_utc is None


def test_f048_r40_la_carpeta_por_defecto_es_la_de_capturar_correo():
    assert correos.DIRECTORIO_CORREOS == RAIZ / "evals" / "inputs" / "correos"


@pytest.mark.parametrize("caso", ["", "../RES-001", "a/b", "a\\b", ".oculto"])
def test_f048_r40_un_caso_que_no_es_un_nombre_de_fichero_se_rechaza(tmp_path, caso):
    with pytest.raises(ValueError):
        correos.cargar_correo(caso, tmp_path)


@pytest.mark.parametrize(
    "contenido",
    [
        f'{{"asunto": "{CENTINELA}", "cuerpo": ',  # JSON cortado
        f"[\"{CENTINELA}\"]",  # no es un objeto
        {"asunto": CENTINELA},  # falta el cuerpo
        {"cuerpo": CENTINELA},  # falta el asunto
        {"asunto": CENTINELA, "cuerpo": 7},  # cuerpo que no es texto
        {"asunto": [CENTINELA], "cuerpo": "x"},  # asunto que no es texto
        _captura(version=2, asunto=CENTINELA),  # versión que no se conoce
        _captura(caso_id="OTRO-001", asunto=CENTINELA),  # captura de otro caso
        CENTINELA.encode("utf-16"),  # no es UTF-8
    ],
    ids=[
        "json-roto", "no-objeto", "sin-cuerpo", "sin-asunto", "cuerpo-no-texto",
        "asunto-no-texto", "version-2", "otro-caso", "no-utf8",
    ],
)
def test_f048_r40_un_fichero_mal_formado_da_un_error_claro_sin_volcar_su_contenido(
    tmp_path, contenido
):
    ruta = _escribir(tmp_path, "RES-001", contenido)

    with pytest.raises(correos.CapturaInvalida) as error:
        correos.cargar_correo("RES-001", tmp_path)

    mensaje = str(error.value)
    assert ruta.name in mensaje, "el error tiene que decir qué fichero es"
    assert CENTINELA not in mensaje
    assert error.value.__cause__ is None, "la causa podría citar el contenido"
    assert error.value.__suppress_context__ is True


def test_f048_r40_la_captura_invalida_es_un_valueerror():
    """Quien ya capture ValueError (el CLI) no necesita conocer la clase."""
    assert issubclass(correos.CapturaInvalida, ValueError)


# --- La firma de un correo (R38) -------------------------------------------------


@pytest.mark.parametrize(
    "datos",
    [
        _captura(),
        {"asunto": "a", "cuerpo": "b"},
        construir_contexto_correo("a", "b").model_dump(mode="json"),
        {"casos": [{"id": 1, "correo": {"asunto": "a", "cuerpo": "b"}}]},
    ],
    ids=["captura", "copia-manual", "contexto-del-blob", "anidado"],
)
def test_f048_r38_la_firma_reconoce_capturas_y_contextos(datos):
    assert correos.tiene_firma_de_correo(datos) is True


@pytest.mark.parametrize(
    "datos",
    [
        {"asunto": "a"},
        {"cuerpo": "b"},
        {"cabecera": {"obra_codigo": "0945"}, "lineas": []},
        ["asunto", "cuerpo"],
        "asunto cuerpo",
        None,
    ],
)
def test_f048_r38_la_firma_no_salta_con_lo_que_no_es_un_correo(datos):
    assert correos.tiene_firma_de_correo(datos) is False


def _git(*args, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.mark.skipif(shutil.which("git") is None, reason="sin git no hay índice que mirar")
def test_f048_r38_el_escaner_encuentra_un_correo_versionado_y_solo_ese(tmp_path):
    """Un repositorio de juguete: versionado + firma = hallazgo; lo demás, no."""
    _git("init", "-q", cwd=tmp_path)
    (tmp_path / "evals" / "inputs" / "correos").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    (tmp_path / "otros").mkdir()
    _escribir(tmp_path / "evals", "captura", _captura())
    _escribir(tmp_path / "tests", "contexto", construir_contexto_correo("a", "b").model_dump())
    _escribir(tmp_path / "tests", "limpio", {"cabecera": {}})
    _escribir(tmp_path / "tests", "roto", "{no es json")
    (tmp_path / "evals" / "inputs" / "correos" / "RES-001.txt").write_text("x", encoding="utf-8")
    _escribir(tmp_path / "otros", "fuera", _captura())  # fuera de evals/ y tests/
    _git("add", ".", cwd=tmp_path)
    _escribir(tmp_path / "tests", "sin_versionar", _captura())  # no está en el índice

    hallazgos = correos.versionados_con_correo(tmp_path)

    assert hallazgos == [
        "evals/captura.json",
        "evals/inputs/correos/RES-001.txt",
        "tests/contexto.json",
    ]


@pytest.mark.skipif(shutil.which("git") is None, reason="sin git no hay índice que mirar")
def test_f048_r38_ningun_fichero_versionado_contiene_un_correo():
    assert correos.versionados_con_correo(RAIZ) == []


@pytest.mark.skipif(shutil.which("git") is None, reason="sin git no hay check-ignore")
def test_f048_r38_la_carpeta_de_capturas_la_ignora_git():
    ruta = correos.DIRECTORIO_CORREOS / "RES-001.json"
    resultado = subprocess.run(
        ["git", "check-ignore", "-q", str(ruta.relative_to(RAIZ).as_posix())],
        cwd=RAIZ,
        capture_output=True,
        check=False,
    )
    assert resultado.returncode == 0, "git NO ignora evals/inputs/correos/: un correo real se versionaría"
