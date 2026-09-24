# evals/inyeccion.py
"""La puerta de entrada del banco al pipeline real, y sus reentradas.

El banco hace de sv1 SIN buzón M365 (R2): crea la fila de `workflow_runs`,
sube el PDF a `input/{document_id}.pdf` y publica `MensajeExtraccion`. No se
copia la lógica de `IntakeColaClient`: se llaman las MISMAS piezas
(`RepositorioWorkflows`, `AlmacenBlobs`, `PublicadorColas`), de modo que si
mañana cambia el contrato de entrada, el banco se entera rompiéndose.

**El orden no es casual**: primero el blob, después el mensaje. Al revés, sv2
podría despertarse antes de que el PDF exista y el caso fallaría por una
carrera del banco, no por un defecto del sistema.

**La identidad** (R16) es lo único que aísla una pasada de otra, porque la
base NO se borra entre pasadas: `correlation_key = eval/{pasada_id}/{caso_id}`
—UNIQUE en `workflow_runs`— y un `document_id` UUID por caso. El prefijo
`eval/` es además lo que permite a §4 dar de baja SOLO lo del banco: si un
`caso_id` pudiera traer una barra, ese prefijo dejaría de ser reconocible y la
baja lógica podría alcanzar documentos del humano. Por eso se rechaza.

Las **reentradas** (`republicar_*`) no inventan capacidad nueva: son los dos
puntos que sv4 ya ofrece —re-fetch de contratos y revaloración—, y el gesto del
revisor de §3 es el segundo con `codigo_contrato`. Publicar ese mensaje BASTA:
`MensajeValoracion.codigo_contrato` lo honra el worker de sv6, así que el banco
no necesita escribir en la base y R3 —«el banco no altera lo que mide»— queda
intacta.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass

from ruesma_comun.blobs.conexion import CONTENEDOR_INPUT
from ruesma_comun.colas.conexion import (
    COLA_EXTRACCION,
    COLA_PERSISTENCIA,
    COLA_VALORACION,
)
from ruesma_comun.colas.mensajes import (
    MensajeExtraccion,
    MensajePersistencia,
    MensajeValoracion,
)

logger = logging.getLogger(__name__)

#: Prefijo de toda `correlation_key` del banco. Es lo que distingue sus
#: documentos de los del humano en una base compartida, y lo que acota la baja
#: lógica de `evals/ciclo.py`.
PREFIJO_BANCO = "eval/"

#: Quién firma los mensajes que publica el banco, para que se vea en los logs
#: de los workers que ese documento no vino de un correo.
EMITIDO_POR = "evals-ciclo"


class ClaveAmbigua(ValueError):
    """Un `pasada_id` o `caso_id` que rompería la lectura de la clave."""


class ClaveAjena(ValueError):
    """Se ha pedido actuar sobre un documento que no es del banco."""


@dataclass(frozen=True)
class Inyeccion:
    """Lo que quedó de meter un caso por la puerta del pipeline."""

    caso_id: str
    document_id: str
    correlation_key: str
    workflow_id: str | None
    duplicado: bool
    sha256: str


def nuevo_pasada_id(fecha: str, contador: int) -> str:
    """`2026-09-18-01`: la fecha y el número de pasada dentro del día."""
    return f"{fecha}-{contador:02d}"


def clave_correlacion(pasada_id: str, caso_id: str) -> str:
    """`eval/{pasada_id}/{caso_id}`, la clave UNIQUE del caso en la pasada."""
    for parte, nombre in ((pasada_id, "pasada_id"), (caso_id, "caso_id")):
        if not parte or "/" in parte:
            raise ClaveAmbigua(
                f"{nombre}={parte!r}: ni vacío ni con '/'. La barra es el "
                f"separador de la clave del banco y partiría la lectura."
            )
    return f"{PREFIJO_BANCO}{pasada_id}/{caso_id}"


def es_del_banco(correlation_key: str | None) -> bool:
    """¿Esta clave la escribió el banco? Nada más la distingue."""
    return bool(correlation_key) and str(correlation_key).startswith(PREFIJO_BANCO)


def partes_de_clave(correlation_key: str | None) -> tuple[str, str] | None:
    """`(pasada_id, caso_id)` de una clave del banco; `None` si no lo es."""
    if not es_del_banco(correlation_key):
        return None
    resto = str(correlation_key)[len(PREFIJO_BANCO) :]
    partes = resto.split("/")
    if len(partes) != 2 or not all(partes):
        return None
    return partes[0], partes[1]


def _exigir_del_banco(correlation_key: str | None) -> None:
    if not es_del_banco(correlation_key):
        raise ClaveAjena(
            f"correlation_key={correlation_key!r} no lleva el prefijo "
            f"{PREFIJO_BANCO!r}: el banco no toca documentos que no son suyos."
        )


class Inyector:
    """Mete casos en el pipeline local y reentra por donde entra sv4."""

    def __init__(
        self,
        *,
        repositorio,  # RepositorioWorkflows o doble
        almacen,  # AlmacenBlobs o doble
        publicador,  # PublicadorColas o doble
        pasada_id: str,
        generador_id=None,  # inyectable para hacer tests deterministas
    ) -> None:
        self._repo = repositorio
        self._almacen = almacen
        self._pub = publicador
        self._pasada_id = pasada_id
        self._generar_id = generador_id or (lambda: str(uuid.uuid4()))

    @property
    def pasada_id(self) -> str:
        return self._pasada_id

    # --- La entrada (R2, R16) ----------------------------------------------

    def inyectar(
        self,
        caso_id: str,
        contenido: bytes,
        nombre_fichero: str,
        content_type: str = "application/pdf",
    ) -> Inyeccion:
        """Un caso por la puerta de sv1: workflow, blob y `q-extraccion`."""
        correlation_key = clave_correlacion(self._pasada_id, caso_id)
        document_id = self._generar_id()
        sha256 = hashlib.sha256(contenido).hexdigest()

        resultado = self._repo.crear_si_no_existe(
            correlation_key=correlation_key,
            payload_json=json.dumps(
                {
                    "origen": "evals",
                    "pasada_id": self._pasada_id,
                    "caso_id": caso_id,
                    "nombre_fichero": nombre_fichero,
                },
                ensure_ascii=False,
            ),
            document_id=document_id,
            attachment_sha256=sha256,
        )

        if not resultado.creado:
            # Igual que sv1: el duplicado ya se subió y se encoló en su día.
            logger.info("[evals] duplicado %s (%s)", caso_id, correlation_key)
            return Inyeccion(
                caso_id=caso_id,
                document_id=document_id,
                correlation_key=correlation_key,
                workflow_id=resultado.workflow_id,
                duplicado=True,
                sha256=sha256,
            )

        # Blob ANTES que mensaje: sv2 no puede despertarse sin el PDF.
        self._almacen.put_bytes(
            CONTENEDOR_INPUT,
            f"{document_id}.pdf",
            contenido,
            content_type=content_type,
            metadata={"filename": nombre_fichero},
        )
        self._pub.publicar(
            COLA_EXTRACCION,
            MensajeExtraccion(
                document_id=document_id,
                correlation_key=correlation_key,
                emitido_por=EMITIDO_POR,
            ),
        )
        logger.info("[evals] inyectado %s → %s", caso_id, document_id)
        return Inyeccion(
            caso_id=caso_id,
            document_id=document_id,
            correlation_key=correlation_key,
            workflow_id=resultado.workflow_id,
            duplicado=False,
            sha256=sha256,
        )

    # --- Las reentradas que el sistema ya ofrece (R5, R24) ------------------

    def republicar_persistencia(
        self, document_id: str, correlation_key: str, *, force: bool = True
    ) -> None:
        """Re-fetch de contratos: el botón «Volver a buscar» de sv4."""
        _exigir_del_banco(correlation_key)
        self._pub.publicar(
            COLA_PERSISTENCIA,
            MensajePersistencia(
                document_id=document_id,
                correlation_key=correlation_key,
                emitido_por=EMITIDO_POR,
                force=force,
            ),
        )

    def republicar_valoracion(
        self,
        document_id: str,
        correlation_key: str,
        *,
        codigo_contrato: str | None = None,
        force: bool = True,
    ) -> None:
        """Revaloración; con `codigo_contrato`, el gesto del revisor de §3."""
        _exigir_del_banco(correlation_key)
        self._pub.publicar(
            COLA_VALORACION,
            MensajeValoracion(
                document_id=document_id,
                correlation_key=correlation_key,
                emitido_por=EMITIDO_POR,
                codigo_contrato=codigo_contrato,
                force=force,
            ),
        )


class GestoRevisor:
    """Lo que haría el revisor en sv4 cuando sv3 deja el contrato sin elegir.

    sv3 solo auto-selecciona cuando encuentra UN contrato; con varios deja
    `selected_contrato_codigo` a null y el caso se quedaría esperando a una
    persona para siempre. El banco hace ese gesto con el código declarado en
    `INPUTS.CASOS.contrato_codigo` y **declara que ese caso no midió la
    selección** (R5): si lo callara, una elección del banco pasaría por una
    del sistema.

    No escribe en la base: publica `MensajeValoracion` con `codigo_contrato`,
    que es lo que el worker de sv6 honra. Así R3 sigue entera.
    """

    def __init__(
        self,
        inyector: Inyector,
        *,
        caso_id: str,
        correlation_key: str,
        codigo_contrato: str | None,
    ) -> None:
        self._inyector = inyector
        self.caso_id = caso_id
        self.correlation_key = correlation_key
        self.codigo_contrato = (codigo_contrato or "").strip()
        self.realizado = False
        self.motivo = ""
        self.contratos_disponibles: list[str] = []
        #: El contrato declarado NO está entre los que sv3 trajo. No es lo
        #: mismo «sv3 no eligió» que «sv3 ni siquiera lo tenía»: lo segundo es
        #: un defecto de la fase de contrato, y sin esta marca se confundiría
        #: con un fallo de valoración de aguas abajo.
        self.contrato_ausente = False

    @property
    def seleccion_no_medida(self) -> bool:
        """Solo cuando el gesto se hizo: sin gesto, la selección es del sistema."""
        return self.realizado

    def __call__(self, lectura) -> None:  # LecturaCaso
        if self.realizado:
            return
        _exigir_del_banco(self.correlation_key)

        self.contratos_disponibles = [
            str(fila.get("codigo_contrato"))
            for fila in lectura.contratos
            if fila.get("codigo_contrato")
        ]
        if not self.codigo_contrato:
            self.motivo = (
                f"{self.caso_id}: sv3 dejó {len(self.contratos_disponibles)} "
                f"contrato(s) sin elegir y INPUTS.CASOS.contrato_codigo está "
                f"vacío. El banco NO elige por su cuenta: el caso se quedará "
                f"sin llegar a H4."
            )
            logger.warning("[evals] %s", self.motivo)
            return

        self.contrato_ausente = (
            bool(self.contratos_disponibles)
            and self.codigo_contrato not in self.contratos_disponibles
        )
        self._inyector.republicar_valoracion(
            lectura.document_id,
            self.correlation_key,
            codigo_contrato=self.codigo_contrato,
        )
        self.realizado = True
        self.motivo = (
            f"{self.caso_id}: la selección de contrato NO se midió; la hizo el "
            f"banco con el código declarado en INPUTS ({self.codigo_contrato}) "
            f"entre {len(self.contratos_disponibles)} que trajo sv3"
        )
        if self.contrato_ausente:
            self.motivo += "; además, sv3 no trajo ese contrato"
        logger.info("[evals] %s", self.motivo)
