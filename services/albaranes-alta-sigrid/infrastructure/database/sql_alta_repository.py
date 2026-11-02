# infrastructure/database/sql_alta_repository.py
"""Repositorio SQL de sv9 (F-053, design §6): ``text()`` de SQLAlchemy.

Lee el merge (cabecera, ``tipologia``, ``tipologia_mixta``, ruta del PDF), la
valoración (``status``, ``contrato_codigo``), las líneas valoradas (con
``producto_sigrid``), de ``albaran_lines_merge`` la descripción, el
``line_index`` y el ``contexto_linea_json``, y de ``albaran_contrato_lines_merge``
el ``sigrid_ide``. ESCRIBE solo ``albaran_altas_sigrid`` (R34), que crea sv3.

``reclamar`` va en UNA transacción con la fila del merge bloqueada (``FOR
UPDATE``, el mismo cerrojo que toma sv4 al editar, R26) y en DOS sentencias
(T24b): primero el cerrojo y después, ya con él, la lectura del alta; decide
con ``domain.services.reclamacion.decidir`` y aplica el efecto antes de
soltarlo.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from sqlalchemy import text

from domain.models.alta_models import (
    AccionAlta,
    AdjuntoEstado,
    AltaActual,
    CabeceraAlta,
    DatosAlta,
    Decision,
    EstadoAlta,
    EstadoDocumento,
    LineaAlta,
    Motivo,
    Reclamacion,
    ResultadoAlta,
)
from domain.ports.alta_repository import AltaRepository
from domain.services.reclamacion import decidir

logger = logging.getLogger(__name__)

_COLUMNAS_ALTA = """
    a.estado, a.modo, a.sigrid_con_ide, a.sigrid_cod, a.adjunto_estado, a.sigrid_gra_ide,
    a.motivos_json, a.avisos_json, a.peticion_json, a.respuesta_json, a.historial_json,
    a.intentos, a.ultimo_intento_at_utc
"""

#: (T24b) Primera de las DOS sentencias de ``reclamar``: el cerrojo del merge.
#: Sin el alta a propósito (ver ``SqlAltaRepository.reclamar``).
SQL_RECLAMAR = """
SELECT m.id, m.is_active, m.approved, m.approved_at_utc, m.approved_by
FROM albaran_documents_merge m
WHERE m.id = :document_id
FOR UPDATE
"""

SQL_UPSERT_EN_CURSO = """
INSERT INTO albaran_altas_sigrid (
    document_id, estado, modo, intentos, approved_at_utc, approved_by,
    ultimo_intento_at_utc, creado_at_utc, actualizado_at_utc, historial_json
) VALUES (
    :document_id, 'en_curso', :modo, 1, :approved_at_utc, :approved_by,
    :ahora, :ahora, :ahora, :historial_json
)
ON CONFLICT (document_id) DO UPDATE SET
    estado = 'en_curso',
    modo = EXCLUDED.modo,
    intentos = albaran_altas_sigrid.intentos + 1,
    approved_at_utc = EXCLUDED.approved_at_utc,
    approved_by = EXCLUDED.approved_by,
    ultimo_intento_at_utc = EXCLUDED.ultimo_intento_at_utc,
    actualizado_at_utc = EXCLUDED.actualizado_at_utc,
    historial_json = EXCLUDED.historial_json
"""

SQL_A_INCIERTO = """
UPDATE albaran_altas_sigrid
SET estado = 'incierto', actualizado_at_utc = :ahora, historial_json = :historial_json
WHERE document_id = :document_id
"""

SQL_CABECERA = """
SELECT m.id, m.obra_codigo, m.proveedor_cif, m.numero_albaran, m.fecha,
       m.tipologia, m.tipologia_mixta, m.sharepoint_relative_path,
       v.status AS valoracion_status, v.contrato_codigo
FROM albaran_documents_merge m
LEFT JOIN albaran_valuations v ON v.document_id = m.id
WHERE m.id = :document_id
"""

SQL_LINEAS = """
SELECT lv.id, lv.merge_line_id, lv.cantidad_albaran, lv.cantidad_convertida,
       lv.unidad_albaran, lv.importe_calculado, lv.matched_contrato_line_id,
       lv.derived_contrato_line_id, lv.codigo_partida_final, lv.descripcion_linea,
       lv.producto_sigrid, lv.precio_unitario_final, lv.descuento_albaran_aplicado,
       l.line_index, l.concepto AS descripcion_merge, l.contexto_linea_json,
       cl.sigrid_ide AS ctrpro_ide, cl.codigo_contrato AS contrato_linea
FROM albaran_valuations v
JOIN albaran_line_valuations lv ON lv.valuation_id = v.id
LEFT JOIN albaran_lines_merge l ON l.id = lv.merge_line_id
LEFT JOIN albaran_contrato_lines_merge cl ON cl.id = lv.matched_contrato_line_id
WHERE v.document_id = :document_id
ORDER BY lv.id
"""

SQL_BLOQUEAR_ALTA = """
SELECT historial_json FROM albaran_altas_sigrid
WHERE document_id = :document_id
FOR UPDATE
"""

SQL_GUARDAR = """
UPDATE albaran_altas_sigrid SET
    estado = :estado,
    modo = :modo,
    sigrid_con_ide = :sigrid_con_ide,
    sigrid_cod = :sigrid_cod,
    adjunto_estado = :adjunto_estado,
    sigrid_gra_ide = :sigrid_gra_ide,
    motivos_json = :motivos_json,
    avisos_json = :avisos_json,
    peticion_json = :peticion_json,
    respuesta_json = :respuesta_json,
    historial_json = :historial_json,
    actualizado_at_utc = :actualizado_at_utc
WHERE document_id = :document_id
"""

SQL_LEER_ALTA = f"""
SELECT {_COLUMNAS_ALTA}
FROM albaran_altas_sigrid a
WHERE a.document_id = :document_id
"""


class _FabricaSesiones(Protocol):
    def create_session(self) -> Any: ...


# ---------------------------------------------------------------------- #
# Traducción
# ---------------------------------------------------------------------- #
def leer_instante(valor: Any) -> datetime | None:
    """Fecha ISO de la BBDD a instante UTC; ilegible = ``None``."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        instante = valor
    else:
        try:
            instante = datetime.fromisoformat(str(valor).strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)
    return instante.astimezone(UTC)


def _json(valor: Any, defecto: Any) -> Any:
    if valor is None or valor == "":
        return defecto
    try:
        return json.loads(valor)
    except (TypeError, ValueError):
        return defecto


def _volcar(valor: Any) -> str | None:
    return None if valor is None else json.dumps(valor, ensure_ascii=False)


def _entero(valor: Any) -> int | None:
    return None if valor is None else int(valor)


def _real(valor: Any) -> float | None:
    return None if valor is None else float(valor)


def _texto(valor: Any) -> str | None:
    return None if valor is None else str(valor)


def _tipo_familia(contexto_json: Any) -> str | None:
    contexto = _json(contexto_json, {})
    if not isinstance(contexto, dict):
        return None
    familia = contexto.get("tipo_familia")
    return str(familia) if familia else None


def _alta_de_fila(fila: Any) -> AltaActual | None:
    if fila is None or fila.get("estado") is None:
        return None
    motivos = _json(fila.get("motivos_json"), [])
    avisos = _json(fila.get("avisos_json"), [])
    adjunto = fila.get("adjunto_estado")
    return AltaActual(
        estado=EstadoAlta(fila["estado"]),
        modo=_texto(fila.get("modo")),
        sigrid_con_ide=_entero(fila.get("sigrid_con_ide")),
        sigrid_cod=_texto(fila.get("sigrid_cod")),
        adjunto_estado=AdjuntoEstado(adjunto) if adjunto else None,
        sigrid_gra_ide=_entero(fila.get("sigrid_gra_ide")),
        motivos=tuple(Motivo.desde_dict(m) for m in motivos if isinstance(m, dict)),
        avisos=tuple(a for a in avisos if isinstance(a, dict)),
        peticion=_json(fila.get("peticion_json"), None),
        respuesta=_json(fila.get("respuesta_json"), None),
        intentos=int(fila.get("intentos") or 0),
        ultimo_intento_at_utc=leer_instante(fila.get("ultimo_intento_at_utc")),
    )


def _documento_de_fila(fila: Any) -> EstadoDocumento | None:
    if fila is None:
        return None
    return EstadoDocumento(
        activo=bool(fila.get("is_active")),
        aprobado=bool(fila.get("approved")),
        approved_at_utc=leer_instante(fila.get("approved_at_utc")),
        approved_by=_texto(fila.get("approved_by")),
    )


def _linea_de_fila(fila: Any) -> LineaAlta:
    return LineaAlta(
        id=int(fila["id"]),
        merge_line_id=_entero(fila.get("merge_line_id")),
        line_index=_entero(fila.get("line_index")),
        cantidad_albaran=_real(fila.get("cantidad_albaran")),
        cantidad_convertida=_real(fila.get("cantidad_convertida")),
        unidad_albaran=_texto(fila.get("unidad_albaran")),
        importe_calculado=_real(fila.get("importe_calculado")),
        matched_contrato_line_id=_entero(fila.get("matched_contrato_line_id")),
        derived_contrato_line_id=_entero(fila.get("derived_contrato_line_id")),
        ctrpro_ide=_entero(fila.get("ctrpro_ide")),
        contrato_linea=_texto(fila.get("contrato_linea")),
        codigo_partida_final=_texto(fila.get("codigo_partida_final")),
        descripcion_linea=_texto(fila.get("descripcion_linea")),
        descripcion_merge=_texto(fila.get("descripcion_merge")),
        tipo_familia=_tipo_familia(fila.get("contexto_linea_json")),
        producto_sigrid=_texto(fila.get("producto_sigrid")),
        precio_unitario_final=_real(fila.get("precio_unitario_final")),
        descuento_albaran_aplicado=_real(fila.get("descuento_albaran_aplicado")),
    )


def _con_entrada(historial_json: Any, ahora: datetime, estado: EstadoAlta,
                 cod: str | None = None, motivos: tuple[Motivo, ...] = ()) -> str:
    """Historial con ``{ts, estado, cod, motivos}`` añadido al final."""
    historial = _json(historial_json, [])
    if not isinstance(historial, list):
        historial = []
    historial.append({
        "ts": ahora.isoformat(), "estado": estado.value, "cod": cod,
        "motivos": [m.codigo for m in motivos],
    })
    return json.dumps(historial, ensure_ascii=False)


# ---------------------------------------------------------------------- #
# Repositorio
# ---------------------------------------------------------------------- #
class SqlAltaRepository(AltaRepository):
    def __init__(self, session_factory: _FabricaSesiones) -> None:
        self._sesiones = session_factory

    def reclamar(
        self,
        document_id: str,
        *,
        accion: AccionAlta,
        ahora: datetime,
        desde: datetime,
        espera: timedelta,
        modo: str,
    ) -> Reclamacion:
        with self._sesiones.create_session() as sesion, sesion.begin():
            # T24b (decisión del humano, 2026-10-07): DOS sentencias, como T40
            # en sv3 y T19 en sv4. En READ COMMITTED la instantánea se toma al
            # EMPEZAR cada sentencia: una sola con FOR UPDATE + LEFT JOIN que
            # esperase el cerrojo de otro ``reclamar`` del mismo documento (dos
            # réplicas en un relevo de revisión) no vería su ``en_curso`` y
            # volvería a procesar. Primero el cerrojo; después, el alta.
            merge = sesion.execute(
                text(SQL_RECLAMAR), {"document_id": document_id},
            ).mappings().first()
            fila_alta = None if merge is None else sesion.execute(
                text(SQL_LEER_ALTA), {"document_id": document_id},
            ).mappings().first()
            fila = None if merge is None else {**dict(merge), **dict(fila_alta or {})}
            alta = _alta_de_fila(fila)
            reclamacion = decidir(
                _documento_de_fila(fila), alta, accion=AccionAlta(accion), ahora=ahora,
                desde=desde, espera=espera,
            )
            historial = None if fila is None else fila.get("historial_json")
            if reclamacion.decision is Decision.PROCESAR:
                sesion.execute(text(SQL_UPSERT_EN_CURSO), {
                    "document_id": document_id,
                    "modo": modo,
                    "approved_at_utc": _texto(fila.get("approved_at_utc")),
                    "approved_by": _texto(fila.get("approved_by")),
                    "ahora": ahora.isoformat(),
                    "historial_json": _con_entrada(historial, ahora, EstadoAlta.EN_CURSO),
                })
            elif reclamacion.decision is Decision.A_INCIERTO:
                sesion.execute(text(SQL_A_INCIERTO), {
                    "document_id": document_id,
                    "ahora": ahora.isoformat(),
                    "historial_json": _con_entrada(historial, ahora, EstadoAlta.INCIERTO),
                })
        return reclamacion

    def leer_datos(self, document_id: str) -> DatosAlta:
        parametros = {"document_id": document_id}
        with self._sesiones.create_session() as sesion:
            cab = sesion.execute(text(SQL_CABECERA), parametros).mappings().first()
            if cab is None:
                raise LookupError(f"documento {document_id} no encontrado")
            filas = sesion.execute(text(SQL_LINEAS), parametros).mappings().all()
        mixta = cab.get("tipologia_mixta")
        cabecera = CabeceraAlta(
            document_id=str(cab["id"]),
            obra_codigo=_texto(cab.get("obra_codigo")),
            proveedor_cif=_texto(cab.get("proveedor_cif")),
            numero_albaran=_texto(cab.get("numero_albaran")),
            fecha=_texto(cab.get("fecha")),
            valoracion_status=_texto(cab.get("valoracion_status")),
            contrato_codigo=_texto(cab.get("contrato_codigo")),
            tipologia=_texto(cab.get("tipologia")),
            tipologia_mixta=None if mixta is None else bool(mixta),
            sharepoint_relative_path=_texto(cab.get("sharepoint_relative_path")),
        )
        return DatosAlta(cabecera=cabecera, lineas=tuple(_linea_de_fila(f) for f in filas))

    def guardar(self, document_id: str, resultado: ResultadoAlta, *, ahora: datetime) -> None:
        with self._sesiones.create_session() as sesion, sesion.begin():
            fila = sesion.execute(
                text(SQL_BLOQUEAR_ALTA), {"document_id": document_id},
            ).mappings().first()
            if fila is None:
                raise LookupError(f"no hay alta de {document_id} que guardar")
            sesion.execute(text(SQL_GUARDAR), {
                "document_id": document_id,
                "estado": resultado.estado.value,
                "modo": resultado.modo,
                "sigrid_con_ide": resultado.sigrid_con_ide,
                "sigrid_cod": resultado.sigrid_cod,
                "adjunto_estado": (
                    None if resultado.adjunto_estado is None else resultado.adjunto_estado.value
                ),
                "sigrid_gra_ide": resultado.sigrid_gra_ide,
                "motivos_json": _volcar([m.a_dict() for m in resultado.motivos]),
                "avisos_json": _volcar(list(resultado.avisos)),
                "peticion_json": _volcar(resultado.peticion),
                "respuesta_json": _volcar(resultado.respuesta),
                "historial_json": _con_entrada(
                    fila.get("historial_json"), ahora, resultado.estado,
                    resultado.sigrid_cod, resultado.motivos,
                ),
                "actualizado_at_utc": ahora.isoformat(),
            })

    def leer_alta(self, document_id: str) -> AltaActual | None:
        with self._sesiones.create_session() as sesion:
            fila = sesion.execute(
                text(SQL_LEER_ALTA), {"document_id": document_id},
            ).mappings().first()
        return _alta_de_fila(fila)
