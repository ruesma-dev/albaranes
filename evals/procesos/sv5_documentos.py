# evals/procesos/sv5_documentos.py
"""Documento y cabecera del contrato, como los lee sv5 (F-084 · R29–R31, R34).

En producción, IA3 recibe en la misma llamada el Markdown del contrato que sv3
dejó en SharePoint (o, si no hay, el PDF como adjunto) y la cabecera del
contrato de `albaran_contratos_merge`. Este subproceso lee ESO mismo, en solo
lectura y con las piezas de sv5:

- la fila: `_SQL_CONTRATO_HEADER` de sv5 (la más reciente del código), en una
  sesión con `default_transaction_read_only=on`;
- el documento: `SharePointContratoPdfDownloader` de sv5, con la preferencia
  MD > PDF y el tope `MAX_PDF_MB` de `ValueAlbaranPipeline`.

Dos papeles, como los demás adaptadores de `evals/procesos/`:

1. **Subproceso** (`python -m evals.procesos.sv5_documentos`): sv5 en
   `sys.path`, un trabajo JSON por stdin y los resultados por stdout. Las
   credenciales llegan por el ENTORNO del proceso, nunca por el trabajo.
2. **Biblioteca pura** (el resto): qué hacer con una fila y un descargador,
   la caché y el entorno. Los tests la ejercen con dobles (R25).

No escribe en ningún sistema: el padre (`evals/contratos.py`) deja el
documento en la caché local no versionada y su huella en el índice.
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote_plus

from evals.procesos import canal
from evals.procesos.errores import avisar, describir_error

RAIZ_REPO = Path(__file__).resolve().parent.parent.parent
RAIZ_SV5 = RAIZ_REPO / "services" / "albaran-valoracion-api"

#: Caché local de los documentos (no versionada: `evals/inputs/` está en
#: `.gitignore`) e índice versionado, sin contenido (R30).
RUTA_CACHE = RAIZ_REPO / "evals" / "inputs" / "contratos"
RUTA_INDICE = RAIZ_REPO / "evals" / "fixtures" / "contratos" / "_indice.json"

#: El tope de sv5 (`Settings.max_pdf_mb`, `MAX_PDF_MB`): un PDF mayor no se
#: adjunta en producción y aquí tampoco (R31).
MAX_PDF_MB = 40

#: Tipos de documento del índice.
TIPOS = ("md", "pdf", "ninguno")

#: Columnas de la cabecera que lee sv5 y que el banco pasa a IA3 (R17, R30).
CAMPOS_CABECERA = (
    "nombre_contrato",
    "cif_proveedor",
    "nombre_proveedor",
    "codigo_obra",
    "nombre_obra",
)

#: Variables obligatorias (R34). `SHAREPOINT_MODE` vale `drive_id` si falta,
#: como en sv5; cada modo exige las suyas.
VARIABLES_BBDD = ("PG_HOST", "PG_DB", "PG_USER", "PG_PASSWORD")
VARIABLES_POR_MODO = {
    "drive_id": ("SHAREPOINT_DRIVE_ID",),
    "folder_url": ("SHAREPOINT_FOLDER_URL",),
    "site_path": ("SHAREPOINT_HOSTNAME", "SHAREPOINT_SITE_PATH"),
}
MODO_POR_DEFECTO = "drive_id"

#: Opción de conexión de PostgreSQL: toda la sesión es de solo lectura.
OPCIONES_SOLO_LECTURA = {"options": "-c default_transaction_read_only=on"}


def nombre_en_cache(codigo: str, tipo: str) -> str:
    """`CTSU24/0454` + `md` → `CTSU24_0454.md` (sin barras ni espacios)."""
    return f"{re.sub(r'[^A-Za-z0-9_-]+', '_', codigo)}.{tipo}"


def leer_indice(ruta: Path | str = RUTA_INDICE) -> dict:
    """El índice de documentos; vacío si todavía no existe (antes de T12)."""
    ruta = Path(ruta)
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else {}


def faltan_variables(entorno: dict) -> list[str]:
    """(R34) Las variables de BBDD y de Graph/SharePoint que no están."""

    def falta(variable: str) -> bool:
        return not (entorno.get(variable) or "").strip()

    faltan = [variable for variable in (*VARIABLES_BBDD, "GRAPH_KEY") if falta(variable)]
    modo = (entorno.get("SHAREPOINT_MODE") or MODO_POR_DEFECTO).strip()
    if modo not in VARIABLES_POR_MODO:
        return [*faltan, f"SHAREPOINT_MODE (válido: {', '.join(VARIABLES_POR_MODO)})"]
    return [*faltan, *(variable for variable in VARIABLES_POR_MODO[modo] if falta(variable))]


def conexion_de_solo_lectura(entorno: dict) -> tuple[str, dict]:
    """(R34) URL de SQLAlchemy (la de sv5) y la opción de solo lectura."""
    usuario = quote_plus(entorno["PG_USER"])
    clave = quote_plus(entorno["PG_PASSWORD"])
    base = quote_plus(entorno["PG_DB"])
    puerto = (entorno.get("PG_PORT") or "5432").strip()
    url = f"postgresql+psycopg://{usuario}:{clave}@{entorno['PG_HOST']}:{puerto}/{base}"
    return url, dict(OPCIONES_SOLO_LECTURA)


# --- Una fila y un descargador: lo que haría el pipeline de sv5 -------------


def _texto(dato: object | None) -> str | None:
    if dato is None:
        return None
    texto = str(dato).strip()
    return texto or None


def _ninguno(codigo: str, motivo: str, cabecera: dict | None = None) -> dict:
    return {
        "codigo": codigo,
        "tipo": "ninguno",
        "motivo": motivo,
        "cabecera": cabecera or {},
        "contenido_b64": None,
    }


def _con_contenido(codigo: str, tipo: str, contenido: bytes, cabecera: dict) -> dict:
    return {
        "codigo": codigo,
        "tipo": tipo,
        "motivo": "",
        "cabecera": cabecera,
        "contenido_b64": base64.b64encode(contenido).decode("ascii"),
    }


def documento_de_contrato(codigo: str, sesion, descargador, sql, max_pdf_mb: int) -> dict:
    """(R29, R31) La cabecera y el documento de UN contrato, como en sv5.

    Preferencia y tope de `ValueAlbaranPipeline`: el MD si hay ruta y llega
    con texto; si no, el PDF si hay ruta, se descarga y no pasa de
    `max_pdf_mb`. Lo que falle deja `tipo = ninguno` con su motivo, sin el
    texto del error (puede traer rutas o valores).
    """
    fila = sesion.execute(sql, {"codigo_contrato": codigo}).mappings().first()
    if fila is None:
        return _ninguno(codigo, "el contrato no está en albaran_contratos_merge")
    cabecera = {campo: _texto(fila.get(campo)) for campo in CAMPOS_CABECERA}

    motivo_md = ""
    ruta_md = _texto(fila.get("md_sharepoint_relative_path"))
    if ruta_md:
        try:
            markdown = (descargador.download_markdown_by_relative_path(relative_path=ruta_md) or "").strip()
        except Exception as error:  # noqa: BLE001 - como sv5: se intenta el PDF
            markdown, motivo_md = "", f"falló la descarga del MD ({type(error).__name__})"
        if markdown:
            return _con_contenido(codigo, "md", markdown.encode("utf-8"), cabecera)
        motivo_md = motivo_md or "el MD llegó vacío"

    ruta_pdf = _texto(fila.get("pdf_sharepoint_relative_path"))
    if not ruta_pdf:
        return _ninguno(codigo, motivo_md or "sin ruta de documento (md ni pdf)", cabecera)
    try:
        descargado = descargador.download_by_relative_path(relative_path=ruta_pdf)
    except Exception as error:  # noqa: BLE001 - como sv5: se sigue sin documento
        return _ninguno(codigo, f"falló la descarga del PDF ({type(error).__name__})", cabecera)
    if len(descargado.data) / (1024 * 1024) > max_pdf_mb:
        return _ninguno(codigo, f"el PDF pasa de MAX_PDF_MB ({max_pdf_mb})", cabecera)
    return _con_contenido(codigo, "pdf", bytes(descargado.data), cabecera)


def ejecutar_trabajo(trabajo: dict, sesion=None, descargador=None, sql=None) -> dict:
    """Cada contrato del trabajo, EN SECUENCIA y AISLADO (R31).

    `sesion`, `descargador` y `sql` son las costuras de los tests; sin ellas
    se montan las reales de sv5 (solo dentro del subproceso).
    """
    max_pdf_mb = int(trabajo.get("max_pdf_mb") or MAX_PDF_MB)
    sql = sql if sql is not None else _sql_de_sv5()
    sesion = sesion if sesion is not None else _sesion_real(os.environ)
    descargador = descargador if descargador is not None else _descargador_real(os.environ)
    resultados = []
    for codigo in trabajo.get("contratos", []):
        try:
            resultado = documento_de_contrato(codigo, sesion, descargador, sql, max_pdf_mb)
        except Exception as error:  # noqa: BLE001 - se aísla el contrato, no se oculta
            fallo = describir_error(error, "documentos")
            resultado = _ninguno(codigo, f"falló la lectura ({fallo['tipo']})")
        avisar("sv5_documentos", f"contrato {codigo}: {resultado['tipo']}")
        resultados.append(resultado)
    return {"resultados": resultados}


# --- Lo que necesita sv5 importado (solo en el subproceso) -----------------


def sql_contrato() -> str:
    """El texto de `_SQL_CONTRATO_HEADER` de sv5. Requiere sv5 en `sys.path`."""
    return str(_sql_de_sv5())


def _sql_de_sv5():
    from infrastructure.database.sqlalchemy_valuation_context_repository import (
        _SQL_CONTRATO_HEADER,
    )

    return _SQL_CONTRATO_HEADER


def _sesion_real(entorno: dict, crear=None, abrir=None):
    """La sesión de solo lectura de BBDD. No conecta hasta la primera consulta.

    `crear` y `abrir` son costuras de test (por defecto, `create_engine` y
    `Session` de SQLAlchemy).
    """
    if crear is None:  # pragma: no cover - la real
        from sqlalchemy import create_engine as crear
    if abrir is None:  # pragma: no cover - la real
        from sqlalchemy.orm import Session as abrir
    url, argumentos = conexion_de_solo_lectura(entorno)
    return abrir(crear(url, connect_args=argumentos))


def _descargador_real(entorno: dict, clase=None):
    """El descargador de sv5 con las `SHAREPOINT_*` del entorno; `clase`, costura de test."""
    if clase is None:  # pragma: no cover - el real, solo con sv5 en sys.path
        from infrastructure.storage.sharepoint_contrato_pdf_downloader import (
            SharePointContratoPdfDownloader as clase,
        )

    return clase(
        graph_key=entorno["GRAPH_KEY"],
        timeout_s=int(entorno.get("HTTP_TIMEOUT_S") or 60),
        mode=(entorno.get("SHAREPOINT_MODE") or MODO_POR_DEFECTO).strip(),
        hostname=entorno.get("SHAREPOINT_HOSTNAME"),
        site_path=entorno.get("SHAREPOINT_SITE_PATH"),
        drive_name=entorno.get("SHAREPOINT_DRIVE_NAME") or "Documentos compartidos",
        drive_id=entorno.get("SHAREPOINT_DRIVE_ID"),
        folder_url=entorno.get("SHAREPOINT_FOLDER_URL"),
    )


def ejecutar_en_subproceso(trabajo: dict, entorno: dict, interprete: str | None = None) -> dict:
    """Lanza este módulo con `entorno` como su entorno; las claves no van por stdin."""
    proceso = subprocess.run(
        [interprete or sys.executable, "-m", "evals.procesos.sv5_documentos"],
        input=json.dumps(trabajo, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(RAIZ_REPO),
        env=entorno,
        check=False,
    )
    if proceso.returncode != 0:
        raise RuntimeError(
            f"el subproceso de documentos de sv5 falló con código {proceso.returncode}:\n"
            f"{proceso.stderr.strip()}"
        )
    return canal.leer(proceso.stdout, "sv5-documentos")


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - subproceso
    """Punto de entrada del subproceso: stdin → fila y documento → stdout."""
    del argv
    canal.blindar_stdout()
    # sv5 delante de todo, como en `sv5_modelos`.
    sys.path = [str(RAIZ_SV5), *sys.path]
    try:
        trabajo = json.loads(sys.stdin.read() or "{}")
        salida = ejecutar_trabajo(trabajo)
    except Exception as error:  # noqa: BLE001 - la frontera devuelve el motivo
        avisar("sv5_documentos", f"la lectura entera falló · {describir_error(error, '')['motivo']}")
        return 1
    canal.emitir(salida)
    return 0


if __name__ == "__main__":  # pragma: no cover - lo ejerce el subproceso
    raise SystemExit(main())
