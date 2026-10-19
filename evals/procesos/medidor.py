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
