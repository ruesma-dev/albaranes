# purgar_colas.py
"""Purga (vacia) colas de Azure Storage / Azurite.

Uso tipico: borrar mensajes huerfanos de ``q-valoracion`` que apuntan a
documentos ya eliminados de la BBDD (dan 404 "Documento merge no
encontrado" en bucle).

Lee la cadena de conexion de la MISMA variable que usan los servicios:
``COLAS_CONNECTION_STRING`` (Azurite en local). Configura abajo que colas
purgar.

Requiere:  pip install azure-storage-queue python-dotenv
"""
from __future__ import annotations

import os
import sys

# ============================ CONFIG ============================
# Colas a purgar. Por defecto solo la de valoracion.
COLAS_A_PURGAR = [
    "q-valoracion",
    # "q-extraccion",
    # "q-persistencia",
    # "q-feedback",
]

# Nombre de la variable con la cadena de conexion (Azurite / Storage).
VAR_CONEXION = "COLAS_CONNECTION_STRING"

# Ruta al .env (si esta junto al script, dejalo como esta).
DOTENV_PATH = ".env"

# Pedir confirmacion por teclado antes de borrar (True recomendado).
PEDIR_CONFIRMACION = True

# Cuantos mensajes mostrar (peek) antes de purgar, para ver que hay.
PEEK = 5
# ===============================================================


def _leer_dotenv(path: str = DOTENV_PATH) -> None:
    """Carga el .env a os.environ (sin dependencias si no existe)."""
    try:
        from dotenv import load_dotenv

        if os.path.exists(path):
            load_dotenv(path)
            print(f"[config] .env cargado: {path}")
        else:
            print(f"[config] no hay .env en {path}; uso variables de entorno")
    except ImportError:
        # Fallback minimo si no esta python-dotenv.
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"'))
            print(f"[config] .env cargado (fallback): {path}")


def _conn_str() -> str:
    cs = os.environ.get(VAR_CONEXION, "").strip()
    if not cs:
        # Azurite por defecto (por si no esta en el .env).
        cs = "UseDevelopmentStorage=true"
        print(
            f"[config] {VAR_CONEXION} no definida; uso "
            f"'UseDevelopmentStorage=true' (Azurite por defecto)"
        )
    return cs


def _purgar_una(conn_str: str, nombre: str) -> None:
    from azure.storage.queue import QueueClient

    qc = QueueClient.from_connection_string(conn_str, nombre)

    # Contar (aproximado) y hacer peek de unos pocos.
    try:
        props = qc.get_queue_properties()
        aprox = props.approximate_message_count
    except Exception as exc:  # noqa: BLE001
        print(f"  [!] '{nombre}' no accesible o no existe: {exc}")
        return

    print(f"\n=== cola '{nombre}' ===")
    print(f"  mensajes (aprox): {aprox}")

    if aprox and PEEK > 0:
        try:
            for i, m in enumerate(qc.peek_messages(max_messages=PEEK), 1):
                cuerpo = (m.content or "")[:120]
                print(f"  peek {i}: {cuerpo}")
        except Exception as exc:  # noqa: BLE001
            print(f"  (no se pudo hacer peek: {exc})")

    if not aprox:
        print("  ya esta vacia; nada que purgar.")
        return

    if PEDIR_CONFIRMACION:
        resp = input(f"  ¿Vaciar '{nombre}'? (s/N): ").strip().lower()
        if resp not in ("s", "si", "y", "yes"):
            print("  saltada (sin cambios).")
            return

    qc.clear_messages()
    print(f"  '{nombre}' VACIADA.")


def main() -> int:
    _leer_dotenv()
    conn_str = _conn_str()
    print(f"[config] colas a purgar: {COLAS_A_PURGAR}")
    for nombre in COLAS_A_PURGAR:
        _purgar_una(conn_str, nombre)
    print("\nHecho.")
    return 0


if __name__ == "__main__":
    sys.exit(main())