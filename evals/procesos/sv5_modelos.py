# evals/procesos/sv5_modelos.py
"""Subproceso de sv5 del comparador de modelos (F-083): IA3, IA4 o la
preparación de IA3, para UN modelo.

El mismo camino que `sv5_valoracion` —el contexto se construye desde los
fixtures de INPUTS, sin BBDD ni SharePoint—, con los servicios de sv5 montados
sobre **una sola** `ProviderClientSpec` (la del modelo del bloque) y el
`MedidorDeUso` como `call_logger` de su cliente.

- `IA3` y `prep_IA3`: cada caso trae su `contexto`; devuelve el `envelope`
  con las líneas que valoró el modelo (R22, R23).
- `IA4`: cada caso trae además el `envelope` de la preparación (la IA3 de la
  referencia); devuelve las `conciliaciones` del modelo, que el padre aplica
  y evalúa (R23).
"""

from __future__ import annotations

import datetime as dt
import json
import sys

from evals.costes import cargar_tabla
from evals.procesos import canal, sv5_valoracion
from evals.procesos.errores import avisar, describir_error
from evals.procesos.medidor import MedidorDeUso, procesar

FASES = ("IA3", "IA4", "prep_IA3")


def llamador(fase: str, valorar, conciliar, proveedor: str, modelo_id: str):
    """La función que procesa UN caso en la fase pedida."""
    if fase not in FASES:
        raise ValueError(f"fase {fase} desconocida en sv5: {FASES}")

    def ia3(caso: dict) -> dict:
        contexto = caso["contexto"]
        lineas = valorar(contexto)
        return {"envelope": sv5_valoracion.envelope_desde(contexto, lineas, proveedor, modelo_id)}

    def ia4(caso: dict) -> dict:
        return {"conciliaciones": conciliar(caso["envelope"], caso["contexto"])}

    return ia4 if fase == "IA4" else ia3


def ejecutar_trabajo(trabajo: dict, montar=None) -> dict:
    """Mide los casos del bloque. `montar` es la costura de test."""
    fase = trabajo["fase"]
    modelo = trabajo["modelo"]
    medidor = MedidorDeUso(
        "preparación" if fase.startswith("prep") else "candidato",
        cargar_tabla(),
        dt.date.fromisoformat(trabajo["fecha"]),
        fichero=trabajo.get("registros"),
    )
    forzar = modelo.get("herramienta_forzada") is not False
    valorar, conciliar = (montar or _montar_servicios)(
        modelo["id"], modelo["proveedor"], forzar, medidor
    )
    llamar = llamador(fase, valorar, conciliar, modelo["proveedor"], modelo["id"])
    resultados = procesar(
        trabajo.get("casos", []),
        llamar,
        medidor,
        trabajo["presupuesto_usd"],
        "IA4" if fase == "IA4" else "IA3",
    )
    return {"resultados": resultados, "registros": medidor.registros}


def _montar_servicios(modelo_id, proveedor, forzar, medidor):  # pragma: no cover - subproceso
    especificacion = sv5_valoracion._clientes_reales(
        proveedor, modelo=modelo_id, call_logger=medidor, forzar_herramienta=forzar
    )
    return sv5_valoracion.servicios(especificacion, proveedor)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - subproceso
    """Punto de entrada del subproceso: stdin → un bloque de sv5 → stdout."""
    del argv
    canal.blindar_stdout()
    sys.path.insert(0, str(sv5_valoracion.RAIZ_SV5))
    try:
        trabajo = json.loads(sys.stdin.read() or "{}")
        sv5_valoracion.comprobar_claves([trabajo["modelo"]["proveedor"]])
        salida = ejecutar_trabajo(trabajo)
    except Exception as error:  # noqa: BLE001 - la frontera devuelve el motivo
        avisar("sv5_modelos", f"el bloque entero falló · {describir_error(error, '')['motivo']}")
        return 1
    canal.emitir(salida)
    return 0


if __name__ == "__main__":  # pragma: no cover - lo ejerce el subproceso
    raise SystemExit(main())
