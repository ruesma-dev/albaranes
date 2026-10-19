# evals/procesos/medidor.py
"""El medidor de uso y coste de cada llamada a un LLM (F-083, R8–R10).

Entra en los clientes de `ruesma_comun/llm/` por la puerta que ya tienen, su
`call_logger`: así se mide sin tocar ni una línea de lo que corre en
producción. Los tres clientes lo llaman con la firma de
`LlmCallLogger.log_call` al terminar cada llamada (bien, con error de parseo o
sin respuesta) y nunca dejan que una excepción del logger rompa la llamada;
aun así, este medidor no propaga ninguna (R8).

Lo que guarda es solo lo que se mide: proveedor, modelo pedido y servido,
duración, tokens, coste, motivo de parada y si falló. **Nunca** el texto del
prompt, de la respuesta ni del error: el error de pydantic arrastra la
respuesta del LLM, y el prompt lleva el albarán.

Sin imports de servicios: lo cargan los subprocesos de sv2 y de sv5.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from evals.costes import (
    TOPE_TEXTO,
    Tabla,
    Uso,
    coste_usd,
    modelo_servido,
    motivo_parada,
    uso_de_respuesta,
)
from evals.procesos import canal
from evals.procesos.errores import avisar, describir_error

RAIZ_REPO = Path(__file__).resolve().parent.parent.parent


class MedidorDeUso:
    """Un `call_logger` que mide en vez de escribir la llamada a disco."""

    #: Los clientes de comun solo miran si hay logger; `enabled` por si alguno
    #: lo consulta, como el `LlmCallLogger` de verdad.
    enabled = True

    def __init__(
        self,
        etiqueta: str,
        tabla: Tabla | None,
        fecha: dt.date,
        fichero: Path | str | None = None,
    ) -> None:
        self.etiqueta = etiqueta
        self.tabla = tabla
        self.fecha = fecha
        self.fichero = Path(fichero) if fichero is not None else None
        self.registros: list[dict] = []
        self._caso: str | None = None

    def caso(self, caso_id: str | None) -> None:
        """Fija el caso en curso: las llamadas siguientes se le atribuyen."""
        self._caso = caso_id

    def gasto_usd(self) -> Decimal:
        return sum((Decimal(r["coste_usd"]) for r in self.registros), Decimal(0))

    def log_call(
        self,
        *,
        provider: str,
        model: str,
        request_summary: dict,
        response_payload: object = None,
        error: str | None = None,
        document_id: str | None = None,
    ) -> None:
        """Mide una llamada. Nunca propaga y nunca guarda texto (R8)."""
        del document_id
        try:
            registro = self._medir(provider, model, request_summary, response_payload, error)
        except Exception:  # noqa: BLE001 - el medidor no puede romper la llamada
            registro = {
                "caso_id": self._caso,
                "etiqueta": self.etiqueta,
                "proveedor": str(provider)[:TOPE_TEXTO],
                "modelo_pedido": str(model)[:TOPE_TEXTO],
                "fallo_medidor": True,
                "coste_usd": "0",
            }
        self.registros.append(registro)
        self._volcar(registro)

    def _medir(self, proveedor, modelo, resumen, payload, error) -> dict:
        respuesta = payload
        if isinstance(payload, dict) and "raw_sdk_response" in payload:
            respuesta = payload["raw_sdk_response"]
        con_respuesta = respuesta is not None
        uso = uso_de_respuesta(proveedor, respuesta) if con_respuesta else Uso(0, 0, 0, 0)
        entrada_tabla = self.tabla.modelo(modelo)
        # Sin respuesta no se factura nada (R10).
        coste = coste_usd(entrada_tabla, uso, self.fecha) if con_respuesta else Decimal(0)
        duracion = (resumen or {}).get("duration_ms")
        return {
            "caso_id": self._caso,
            "etiqueta": self.etiqueta,
            "proveedor": proveedor,
            "modelo_pedido": modelo,
            "modelo_servido": modelo_servido(proveedor, respuesta) if con_respuesta else None,
            "duracion_ms": duracion if isinstance(duracion, int) else None,
            "entrada": uso.entrada,
            "lectura_cache": uso.lectura_cache,
            "escritura_cache": uso.escritura_cache,
            "salida": uso.salida,
            "uso_incompleto": uso.incompleto,
            "coste_usd": str(coste),
            "motivo_parada": motivo_parada(proveedor, respuesta) if con_respuesta else None,
            "fallo": error is not None,
            "con_respuesta": con_respuesta,
        }

    def _volcar(self, registro: dict) -> None:
        """Una línea por llamada en el fichero del bloque: si el subproceso muere,
        lo ya pagado se recupera de ahí (R26)."""
        if self.fichero is None:
            return
        try:
            self.fichero.parent.mkdir(parents=True, exist_ok=True)
            with self.fichero.open("a", encoding="utf-8") as salida:
                salida.write(json.dumps(registro, ensure_ascii=False) + "\n")
        except OSError:
            return


def procesar(casos: list[dict], llamar, medidor, presupuesto, fase: str) -> list[dict]:
    """Los casos de un bloque (un modelo, una repetición), uno a uno y AISLADOS.

    - Antes de cada caso mira lo gastado: si ya alcanza `presupuesto`, el caso
      queda `no_ejecutado` sin llamar a nada (R19). Se puede pasar como mucho en
      un caso: cortar a mitad tiraría lo ya pagado de ese caso (D4).
    - Un caso que revienta queda con su `error` (fase, tipo y motivo, sin
      valores del albarán) y el bucle sigue (R24).

    `llamar(caso)` devuelve lo que el caso produjo (`documento`, `envelope`,
    `conciliaciones`); el medidor es el `call_logger` de los clientes del bloque.
    """
    presupuesto = Decimal(str(presupuesto))
    resultados = []
    for caso in casos:
        caso_id = caso.get("caso_id")
        if medidor.gasto_usd() >= presupuesto:
            resultados.append({"caso_id": caso_id, "no_ejecutado": True})
            continue
        medidor.caso(caso_id)
        try:
            salida = llamar(caso)
        except Exception as error:  # noqa: BLE001 - se aísla el caso, no se oculta
            fallo = describir_error(error, fase)
            avisar("comparar_modelos", f"caso {caso_id}: error en {fase} · {fallo['motivo']}")
            resultados.append({"caso_id": caso_id, "error": fallo})
            continue
        avisar("comparar_modelos", f"caso {caso_id}: ok")
        resultados.append({"caso_id": caso_id, **salida})
    medidor.caso(None)
    return resultados


def lanzar(
    modulo: str, trabajo: dict, servicio: str, interprete: str | None = None, entorno=None
) -> dict:
    """Ejecuta un bloque en su propio intérprete (R26): sv2 y sv5 no caben juntos.

    El stderr del hijo NO se captura: sus líneas de avance salen en la consola
    al momento, y si muere, su motivo ya está ahí (puede llevar valores del
    albarán, por eso no viaja en la excepción ni al informe).
    """
    proceso = subprocess.run(
        [interprete or sys.executable, "-m", modulo],
        input=json.dumps(trabajo, ensure_ascii=False),
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        cwd=str(RAIZ_REPO),
        env=entorno,
        check=False,
    )
    if proceso.returncode != 0:
        raise RuntimeError(
            f"el subproceso de {servicio} falló con código {proceso.returncode} "
            f"(el detalle está en la salida de error de la consola)"
        )
    return canal.leer(proceso.stdout, servicio)


def registros_de_fichero(ruta: Path | str) -> list[dict]:
    """Los registros que un bloque dejó en su fichero; las líneas rotas se saltan."""
    ruta = Path(ruta)
    if not ruta.is_file():
        return []
    registros = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        try:
            dato = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if isinstance(dato, dict):
            registros.append(dato)
    return registros
