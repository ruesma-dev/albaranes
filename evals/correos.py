# evals/correos.py
"""El correo de un caso del banco (F-048, R38 y R40).

`capturar_correo.py` (sv1, R39) deja el asunto y la parte única del cuerpo de
un correo real en `evals/inputs/correos/{caso_id}.json`, carpeta que git
ignora. Este módulo la lee y construye el contexto con
`ruesma_comun.correo.construir_contexto_correo`, la MISMA función que usa sv1
al ingerir: así el recorte y la huella salen iguales que si el correo hubiera
entrado por el buzón, y la inyección (`evals/inyeccion.py`) lo guarda después
con `guardar_contexto_correo`, la misma puerta que sv1.

- **Sin fichero** el caso va sin correo (`None`): hoy ningún caso lo trae.
- **Un fichero mal formado** es un error (`CapturaInvalida`), no un «sin
  correo» silencioso: medir con correo y quedarse sin él sin avisar daría por
  buena una pasada que no midió lo que dice. El mensaje dice qué fichero es y
  qué le pasa, NUNCA su contenido, y sin encadenar la causa, que podría
  citarlo.
- **Una copia manual** (§7 del design) con solo `asunto` y `cuerpo` vale.

R38 se defiende con `versionados_con_correo`: la firma de un correo es un
objeto JSON con `asunto` y `cuerpo` (lo mínimo que acepta la carga, y lo que
comparten la captura y el contexto del blob lateral) o con `subject` y
`uniqueBody` (un mensaje tal como lo devuelve Graph), a cualquier
profundidad. Con esa firma, ningún fichero versionado bajo `evals/` o `tests/`
puede tener un correo, y tampoco un `.eml` ni un `.msg`, que son correos
por definición; bajo `evals/inputs/correos/`, ningún fichero en absoluto.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from ruesma_comun.correo import ContextoCorreo, construir_contexto_correo

#: La carpeta donde `capturar_correo.py` deja las capturas. Ignorada por git.
DIRECTORIO_CORREOS = Path(__file__).resolve().parent / "inputs" / "correos"

#: La versión del formato de `capturar_correo.py` que se sabe leer.
VERSION_CAPTURA = 1

#: Lo que se revisa en R38, relativo a la raíz del repositorio.
PREFIJOS_R38 = ("evals", "tests")
_CARPETA_CAPTURAS = "evals/inputs/correos/"

#: Extensiones de un correo guardado tal cual (CR-E3): nunca se versionan.
EXTENSIONES_CORREO = (".eml", ".msg")

#: Pares de claves que delatan un correo: el de la captura y el de Graph.
FIRMAS_CORREO = (("asunto", "cuerpo"), ("subject", "uniqueBody"))

# El mismo nombre de caso que admite `capturar_correo.py`: un nombre de
# fichero sencillo, sin separadores, sin `..` y sin ocultos.
_CASO_VALIDO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class CapturaInvalida(ValueError):
    """El fichero de correo de un caso existe pero no se puede usar."""


def ruta_correo(caso_id: str, directorio: Path = DIRECTORIO_CORREOS) -> Path:
    """`{directorio}/{caso_id}.json`; `ValueError` si el caso no es un nombre válido."""
    if not _CASO_VALIDO.fullmatch(caso_id or ""):
        raise ValueError(f"caso no válido: {caso_id!r} (letras, dígitos, '_', '.' o '-')")
    return Path(directorio) / f"{caso_id}.json"


def _es_texto_o_nulo(valor) -> bool:
    return valor is None or isinstance(valor, str)


def cargar_correo(
    caso_id: str, directorio: Path = DIRECTORIO_CORREOS
) -> ContextoCorreo | None:
    """El contexto del correo del caso, o `None` si el caso no tiene fichero."""
    ruta = ruta_correo(caso_id, directorio)
    if not ruta.is_file():
        return None
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        # ValueError cubre JSONDecodeError y UnicodeDecodeError; su texto
        # puede citar el contenido: solo el tipo.
        raise CapturaInvalida(
            f"{ruta}: no se pudo leer como JSON UTF-8 ({type(exc).__name__})"
        ) from None
    if not isinstance(datos, dict):
        raise CapturaInvalida(f"{ruta}: no es un objeto JSON") from None
    if "asunto" not in datos or "cuerpo" not in datos:
        raise CapturaInvalida(f"{ruta}: no es una captura de correo: faltan 'asunto' y 'cuerpo'") from None
    if "version" in datos and datos["version"] != VERSION_CAPTURA:
        raise CapturaInvalida(
            f"{ruta}: versión de captura desconocida (se lee la {VERSION_CAPTURA})"
        ) from None
    if "caso_id" in datos and datos["caso_id"] != caso_id:
        raise CapturaInvalida(f"{ruta}: la captura declara otro caso_id") from None
    for campo in ("asunto", "cuerpo", "recibido_utc"):
        if not _es_texto_o_nulo(datos.get(campo)):
            raise CapturaInvalida(f"{ruta}: '{campo}' no es texto") from None
    return construir_contexto_correo(
        datos["asunto"], datos["cuerpo"], recibido_utc=datos.get("recibido_utc")
    )


def tiene_firma_de_correo(datos) -> bool:
    """¿Hay, a cualquier profundidad, un objeto con una de las `FIRMAS_CORREO`?"""
    pendientes = [datos]
    while pendientes:
        actual = pendientes.pop()
        if isinstance(actual, dict):
            if any(a in actual and b in actual for a, b in FIRMAS_CORREO):
                return True
            pendientes.extend(actual.values())
        elif isinstance(actual, list):
            pendientes.extend(actual)
    return False


def _json_con_firma(ruta: Path) -> bool:
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False  # no es JSON legible: no puede ser una captura
    return tiene_firma_de_correo(datos)


def versionados_con_correo(raiz: Path, prefijos: tuple[str, ...] = PREFIJOS_R38) -> list[str]:
    """Ficheros del índice de git que tienen, o pueden tener, un correo (R38).

    Cuenta todo lo versionado bajo `evals/inputs/correos/`, todo `.eml` y
    `.msg` y todo `.json` con la firma de un correo. Rutas relativas a `raiz`,
    con `/`, ordenadas.
    """
    salida = subprocess.run(
        ["git", "ls-files", "-z", "--", *prefijos],
        cwd=raiz,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    return sorted(
        ruta
        for ruta in filter(None, salida.split("\0"))
        if ruta.startswith(_CARPETA_CAPTURAS)
        or ruta.lower().endswith(EXTENSIONES_CORREO)
        or (ruta.endswith(".json") and _json_con_firma(Path(raiz) / ruta))
    )
