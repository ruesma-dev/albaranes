# infrastructure/database/sqlalchemy_valuation_repository.py
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from ruesma_comun.edicion_manual import (
    COLUMNAS_DE_CAMPO,
    EdicionManual,
    aplicar_edicion,
    es_fila_manual,
    leer_edicion,
)
from sqlalchemy import select, text

from domain.models.valuation_records import (
    DerivedContratoLineRecord,
    LineValuationRecord,
    ValuationHeaderRecord,
)
from domain.ports.valuation_repository import (
    ExistingValuationSummary,
    PersistedValuation,
    ValuationRepository,
)
from infrastructure.database.orm_valuation_models import (
    AlbaranLineValuationOrm,
    AlbaranValuationOrm,
    ContratoLineDerivedOrm,
)
from infrastructure.database.schema_contribution import (
    get_ddl_statements,
    get_external_table_dependencies,
    get_owned_table_names,
)
from infrastructure.database.session_factory import SessionFactory

logger = logging.getLogger(__name__)

#: (F-076, design §4) Única lectura de sv6 sobre una columna de sv3: la obra
#: del merge, para pedir la lista de partidas de la obra. Solo lectura.
SQL_OBRA_DEL_DOCUMENTO = (
    "SELECT obra_codigo FROM albaran_documents_merge WHERE id = :document_id"
)


class SqlAlchemyValuationRepository(ValuationRepository):
    """Repositorio con inicialización PEREZOSA y DDL por sentencia.

    El DDL ya NO vive en este archivo. Se carga del módulo
    ``infrastructure/database/schema_contribution.py``, que es la
    fuente única de verdad y el contrato público que el orquestador
    (servicio 7) consume para crear las tablas. Así, cuando añadimos
    una columna, basta con tocar ``schema_contribution.py``: el repo
    de este servicio y el sv7 leen del mismo sitio.

    Cada sentencia DDL se ejecuta en su propia transacción (autocommit)
    para que un fallo puntual no invalide el resto. Al final, se
    comprueba que todas las tablas declaradas como propias existen en
    la BBDD; si no, se levanta un error claro.
    """

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    # ------------------------------------------------------------------ #
    # Init — perezosa, por sentencia, con verificación final
    # ------------------------------------------------------------------ #
    def initialize(self) -> None:
        if self._initialized:
            return

        # Prerequisito: tablas externas (servicio 3) presentes — porque
        # nuestras FKs apuntan a ellas.
        missing_external = self._missing_tables(
            get_external_table_dependencies()
        )
        if missing_external:
            raise RuntimeError(
                "No se pueden crear las tablas del servicio 6 porque "
                f"faltan tablas externas (servicio 3): {missing_external}. "
                "Arranca el servicio 3 (o el orquestador sv7) contra la "
                "misma base de datos y reintenta."
            )

        ddl_statements = get_ddl_statements()
        engine = self._session_factory.engine
        logger.info(
            "[valuation-repo] Ejecutando %s sentencias DDL "
            "(autocommit) desde schema_contribution ...",
            len(ddl_statements),
        )
        # AUTOCOMMIT: cada sentencia DDL se confirma por separado. Así un
        # fallo puntual no invalida la transacción entera, y además
        # hacemos imposible "la transacción silenciosa abortada".
        autocommit_engine = engine.execution_options(
            isolation_level="AUTOCOMMIT",
        )
        for idx, (label, ddl) in enumerate(ddl_statements, start=1):
            try:
                with autocommit_engine.connect() as conn:
                    conn.execute(text(ddl))
                logger.info(
                    "[valuation-repo]   [%2s/%2s] OK %s",
                    idx, len(ddl_statements), label,
                )
            except Exception as exc:
                logger.error(
                    "[valuation-repo]   [%2s/%2s] FALLO %s -> %s",
                    idx, len(ddl_statements), label, exc,
                )
                raise

        # Verificación: todas las tablas propias tienen que existir.
        still_missing = self._missing_tables(get_owned_table_names())
        if still_missing:
            raise RuntimeError(
                "Tras ejecutar la DDL, siguen faltando tablas: "
                f"{still_missing}. Esto no debería pasar. Revisa los "
                "permisos del usuario de BBDD y los logs anteriores."
            )

        self._initialized = True
        logger.info(
            "[valuation-repo] Inicialización completa y VERIFICADA. "
            "Tablas propias: %s",
            ", ".join(get_owned_table_names()),
        )

    def _missing_tables(self, required: list[str]) -> list[str]:
        missing: list[str] = []
        try:
            with self._session_factory.create_session() as session:
                for table_name in required:
                    row = session.execute(
                        text("SELECT to_regclass(:qualified)"),
                        {"qualified": f"public.{table_name}"},
                    ).first()
                    if row is None or row[0] is None:
                        missing.append(table_name)
        except Exception:
            logger.exception(
                "[valuation-repo] No se pudo comprobar existencia de tablas."
            )
            return required
        return missing

    # ------------------------------------------------------------------ #
    # Lectura
    # ------------------------------------------------------------------ #
    def get_by_document_id(
        self,
        *,
        document_id: str,
    ) -> ExistingValuationSummary | None:
        self.initialize()
        with self._session_factory.create_session() as session:
            row = session.scalar(
                select(AlbaranValuationOrm).where(
                    AlbaranValuationOrm.document_id == document_id,
                )
            )
            if row is None:
                return None
            return ExistingValuationSummary(
                valuation_id=row.id,
                document_id=row.document_id,
                contrato_codigo=row.contrato_codigo,
                status=row.status,  # type: ignore[arg-type]
                total_valorado=float(row.total_valorado or 0.0),
                total_lines=int(row.total_lines or 0),
                review_required=bool(row.review_required),
                created_at_utc=row.created_at_utc,
                updated_at_utc=row.updated_at_utc,
            )

    def obra_del_documento(self, *, document_id: str) -> str | None:
        """(F-076 R7) Obra del merge, en solo lectura (design §4).

        Lector acoplado a una columna de sv3 (``albaran_documents_merge``,
        regla 3 de ARCHITECTURE). No inicializa el schema de sv6: es una
        lectura de una tabla ajena. La obra sale tal cual; la canoniza la
        caché de comun. Sin fila o sin obra ⇒ ``None``.
        """
        with self._session_factory.create_session() as session:
            valor = session.execute(
                text(SQL_OBRA_DEL_DOCUMENTO), {"document_id": document_id},
            ).scalar()
        if valor is None:
            return None
        return str(valor)

    def read_full_valuation_json(
        self,
        *,
        document_id: str,
    ) -> dict:
        self.initialize()
        with self._session_factory.create_session() as session:
            header = session.scalar(
                select(AlbaranValuationOrm).where(
                    AlbaranValuationOrm.document_id == document_id,
                )
            )
            if header is None:
                raise KeyError(
                    f"No hay valoración para document_id={document_id}"
                )
            lines = session.scalars(
                select(AlbaranLineValuationOrm)
                .where(AlbaranLineValuationOrm.valuation_id == header.id)
                .order_by(AlbaranLineValuationOrm.id)
            ).all()
            derived = session.scalars(
                select(ContratoLineDerivedOrm)
                .where(
                    ContratoLineDerivedOrm.created_by_valuation_id == header.id
                )
                .order_by(ContratoLineDerivedOrm.id)
            ).all()

            return {
                "header": self._header_to_dict(header),
                "lines": [self._line_to_dict(line) for line in lines],
                "derived_contract_lines": [
                    self._derived_to_dict(d) for d in derived
                ],
            }

    # ------------------------------------------------------------------ #
    # Escritura
    # ------------------------------------------------------------------ #
    def replace_valuation(
        self,
        *,
        header: ValuationHeaderRecord,
        lines: list[LineValuationRecord],
    ) -> PersistedValuation:
        self.initialize()
        now = datetime.now(timezone.utc).isoformat()

        with self._session_factory.create_session() as session:
            # (F-106 R28) La cabecera bloqueada antes de leer sus ediciones: un
            # PATCH de sv4 a la vez espera; si después su fila ya no existe, 409.
            existing = session.scalar(
                select(AlbaranValuationOrm).where(
                    AlbaranValuationOrm.document_id == header.document_id,
                ).with_for_update()
            )
            # (F-106 R23, R27) Lo editado a mano y las legadas, antes de borrar.
            previas = (
                self._ediciones_previas(session, existing) if existing is not None else []
            )
            if existing is not None:
                session.delete(existing)
                session.flush()

            valuation_id = str(uuid.uuid4())
            valuation_orm = AlbaranValuationOrm(
                id=valuation_id,
                document_id=header.document_id,
                contrato_codigo=header.contrato_codigo,
                status=header.status,
                provider_ia=header.provider_ia,
                model_name=header.model_name,
                prompt_key=header.prompt_key,
                total_valorado=float(header.total_valorado),
                total_lines=int(header.total_lines),
                lines_matched_exact=int(header.lines_matched_exact),
                lines_matched_semantic=int(header.lines_matched_semantic),
                lines_matched_price_only=int(header.lines_matched_price_only),
                lines_unmatched=int(header.lines_unmatched),
                review_required=bool(header.review_required),
                review_reasons_json=json.dumps(
                    header.review_reasons, ensure_ascii=False,
                ),
                raw_ia_envelope_json=header.raw_ia_envelope_json,
                created_at_utc=now,
                updated_at_utc=now,
            )
            session.add(valuation_orm)
            session.flush()

            derived_by_record: dict[int, int] = {}
            for idx, line in enumerate(lines):
                if line.derived_contrato_line_record is None:
                    continue
                derived_orm = self._build_derived_orm(
                    valuation_id=valuation_id,
                    document_id=header.document_id,
                    record=line.derived_contrato_line_record,
                    created_at_utc=now,
                )
                session.add(derived_orm)
                session.flush()
                derived_by_record[idx] = derived_orm.id

            line_orms: list[AlbaranLineValuationOrm] = []
            for idx, line in enumerate(lines):
                derived_id = derived_by_record.get(idx)
                line_orms.append(self._build_line_orm(
                    valuation_id=valuation_id,
                    line=line,
                    derived_contrato_line_id=derived_id,
                    created_at_utc=now,
                ))

            externos: list[tuple[AlbaranLineValuationOrm, Any]] = []
            if previas:
                # (F-106 R24–R28) Reaplicar lo editado; total y contadores con
                # las filas finales.
                line_orms, externos, perdidas = self._reaplicar(
                    session=session,
                    header=header,
                    valuation_id=valuation_id,
                    line_orms=line_orms,
                    previas=previas,
                    now=now,
                )
                valuation_orm.total_lines = len(line_orms)
                valuation_orm.total_valorado = float(round(sum(
                    float(lo.importe_calculado or 0.0) for lo in line_orms
                ), 2))
                if perdidas:
                    motivos = list(header.review_reasons) + [f"ediciones_perdidas:{perdidas}"]
                    valuation_orm.review_reasons_json = json.dumps(motivos, ensure_ascii=False)

            for line_orm in line_orms:
                session.add(line_orm)
            session.flush()
            self._escribir_codigo_externo(session, externos)

            session.commit()

            logger.info(
                "[valuation-repo] persistida document_id=%s valuation_id=%s "
                "lines=%s derived=%s total=%.2f",
                header.document_id,
                valuation_id,
                len(lines),
                len(derived_by_record),
                header.total_valorado,
            )
            return PersistedValuation(
                valuation_id=valuation_id,
                document_id=header.document_id,
                status=header.status,
                total_valorado=float(valuation_orm.total_valorado),
                total_lines=int(valuation_orm.total_lines),
                review_required=bool(header.review_required),
            )

    # ------------------------------------------------------------------ #
    # F-106 fase B · reaplicar lo editado a mano (design §5)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _columnas_de_fila(orm: AlbaranLineValuationOrm) -> dict[str, Any]:
        return {
            c.key: getattr(orm, c.key)
            for c in AlbaranLineValuationOrm.__table__.columns
        }

    def _ediciones_previas(
        self, session: Any, existing: AlbaranValuationOrm,
    ) -> list[dict[str, Any]]:
        """(R23, R27) Las filas de la valoración anterior que hay que conservar:
        con edición, o legadas (sin edición y ``es_fila_manual``, que cuentan
        como ``fila_entera``). Cada una con sus columnas, su edición, su
        derivada (si tiene) y su ``codigo_externo`` (columna de sv4)."""
        externos = self._leer_codigo_externo(session, [lo.id for lo in existing.lines])
        previas: list[dict[str, Any]] = []
        for lo in existing.lines:
            derivada = lo.derived_contrato_line
            edicion = leer_edicion(lo.edicion_manual_json)
            legada = edicion is None and es_fila_manual(
                line_kind=lo.line_kind,
                bloqueada=bool(lo.bloqueada),
                derivada_origen=derivada.origen if derivada is not None else None,
                precio_unitario_agreement=lo.precio_unitario_agreement,
                partida_action=lo.partida_action,
            )
            if edicion is None and not legada:
                continue
            fila = self._columnas_de_fila(lo)
            fila["codigo_externo"] = externos.get(lo.id)
            previas.append({
                "fila": fila,
                "edicion": edicion,
                "legada": legada,
                "derivada": (
                    {c.key: getattr(derivada, c.key)
                     for c in ContratoLineDerivedOrm.__table__.columns}
                    if derivada is not None else None
                ),
            })
        return previas

    @staticmethod
    def _leer_codigo_externo(session: Any, ids: list[int]) -> dict[int, Any]:
        """``codigo_externo`` es columna de sv4 (sv6 no la declara): se lee
        aparte y se tolera que no exista."""
        if not ids:
            return {}
        marcas = ", ".join(f":i{n}" for n in range(len(ids)))
        try:
            with session.begin_nested():
                filas = session.execute(
                    text(f"SELECT id, codigo_externo FROM albaran_line_valuations WHERE id IN ({marcas})"),
                    {f"i{n}": v for n, v in enumerate(ids)},
                ).all()
        except Exception:  # noqa: BLE001 - BBDD sin la columna de sv4
            return {}
        return {int(i): c for i, c in filas}

    @staticmethod
    def _escribir_codigo_externo(
        session: Any, externos: list[tuple[AlbaranLineValuationOrm, Any]],
    ) -> None:
        for orm, valor in externos:
            try:
                with session.begin_nested():
                    session.execute(
                        text("UPDATE albaran_line_valuations SET codigo_externo = :c WHERE id = :i"),
                        {"c": valor, "i": orm.id},
                    )
            except Exception:  # noqa: BLE001 - BBDD sin la columna de sv4
                logger.warning("[valuation-repo] sin columna codigo_externo; no se reaplica")
                return

    @staticmethod
    def _contrato_de_linea(session: Any, contrato_line_id: int | None) -> str | None:
        if contrato_line_id is None:
            return None
        return session.execute(
            text("SELECT codigo_contrato FROM albaran_contrato_lines_merge WHERE id = :i"),
            {"i": contrato_line_id},
        ).scalar()

    @staticmethod
    def _blancas_del_documento(session: Any, document_id: str) -> set[int]:
        return {
            int(i) for i in session.execute(
                text("SELECT id FROM albaran_lines_merge WHERE document_id = :d"),
                {"d": document_id},
            ).scalars()
        }

    def _nueva_derivada(
        self,
        session: Any,
        *,
        header: ValuationHeaderRecord,
        valuation_id: str,
        fila: AlbaranLineValuationOrm,
        codigo_producto: str | None,
        now: str,
    ) -> int:
        """(R27) La derivada ``manual_override`` de una fila Nueva con su P."""
        derivada = ContratoLineDerivedOrm(
            created_by_valuation_id=valuation_id,
            source_document_id=header.document_id,
            codigo_contrato=header.contrato_codigo or "",
            codigo_producto=codigo_producto,
            descripcion_linea=fila.descripcion_linea,
            unidad_medida=fila.unidad_contrato,
            precio_unitario=fila.precio_unitario_final,
            codigo_partida=fila.codigo_partida_final,
            origen="manual_override",
            created_at_utc=now,
        )
        session.add(derivada)
        session.flush()
        return int(derivada.id)

    @staticmethod
    def _anadir_motivo(fila: AlbaranLineValuationOrm, motivo: str) -> None:
        motivos = json.loads(fila.review_reasons_json or "[]")
        if motivo not in motivos:
            motivos.append(motivo)
        fila.review_reasons_json = json.dumps(motivos, ensure_ascii=False)

    def _poner_origen(
        self,
        session: Any,
        *,
        header: ValuationHeaderRecord,
        valuation_id: str,
        fila: AlbaranLineValuationOrm,
        origen: dict[str, Any] | None,
        codigo_producto: str | None,
        now: str,
    ) -> None:
        """(R27) ``nueva`` ⇒ derivada ``manual_override`` con su P; ``contrato``
        con una línea del contrato nuevo ⇒ esa línea; con una que no lo es ⇒
        Nueva con su P y ``front_contrato_cambiado``. Sin origen, nada."""
        if not isinstance(origen, dict):
            return
        linea = origen.get("linea") if origen.get("tipo") == "contrato" else None
        if linea is not None and self._contrato_de_linea(session, linea) == header.contrato_codigo:
            fila.matched_contrato_line_id = linea
            fila.derived_contrato_line_id = None
            return
        if linea is not None:
            self._anadir_motivo(fila, "front_contrato_cambiado")
        fila.matched_contrato_line_id = None
        fila.derived_contrato_line_id = self._nueva_derivada(
            session, header=header, valuation_id=valuation_id, fila=fila,
            codigo_producto=codigo_producto, now=now,
        )

    def _reaplicar(
        self,
        *,
        session: Any,
        header: ValuationHeaderRecord,
        valuation_id: str,
        line_orms: list[AlbaranLineValuationOrm],
        previas: list[dict[str, Any]],
        now: str,
    ) -> tuple[list[AlbaranLineValuationOrm], list[tuple[AlbaranLineValuationOrm, Any]], int]:
        """(R24–R27, design §5 pasos 2–5) Las filas finales: las nuevas con
        la edición aplicada a su pareja y las conservadas enteras; los
        ``codigo_externo`` a escribir; y cuántas ediciones se perdieron.

        Una fila conservada entera con blanca sustituye a la nueva de esa
        misma blanca (si no, la blanca tendría dos filas)."""
        por_blanca = {
            lo.merge_line_id: lo for lo in line_orms
            if lo.merge_line_id is not None and lo.line_kind == "from_albaran"
        }
        sinteticas: dict[tuple[Any, Any], list[AlbaranLineValuationOrm]] = {}
        for lo in line_orms:
            if lo.merge_line_id is None and lo.parent_merge_line_id is not None:
                sinteticas.setdefault((lo.parent_merge_line_id, lo.modifier_source), []).append(lo)
        blancas = self._blancas_del_documento(session, header.document_id)
        finales = list(line_orms)
        externos: list[tuple[AlbaranLineValuationOrm, Any]] = []
        perdidas = 0
        for previa in previas:
            fila, edicion = previa["fila"], previa["edicion"]
            derivada = previa["derivada"] or {}
            entera = previa["legada"] or (edicion is not None and edicion.fila_entera)
            pareja = None
            if not entera and fila["merge_line_id"] is not None:
                pareja = por_blanca.get(fila["merge_line_id"])
            elif not entera and fila["parent_merge_line_id"] is not None:
                candidatas = sinteticas.get((fila["parent_merge_line_id"], fila["modifier_source"]), [])
                pareja = candidatas[0] if len(candidatas) == 1 else None
            if pareja is not None:
                self._aplicar_a_pareja(
                    session, header=header, valuation_id=valuation_id, pareja=pareja,
                    edicion=edicion, codigo_producto=derivada.get("codigo_producto"), now=now,
                )
                if "codigo_externo" in edicion.campos:
                    externos.append((pareja, edicion.campos["codigo_externo"].get("codigo_externo")))
                continue
            blanca = fila["merge_line_id"] if fila["merge_line_id"] is not None else fila["parent_merge_line_id"]
            if (blanca is not None and blanca not in blancas) or (blanca is None and not entera):
                perdidas += 1
                continue
            copia = self._copiar_fila(
                session, header=header, valuation_id=valuation_id, fila=fila,
                derivada=previa["derivada"], now=now,
            )
            if fila["merge_line_id"] is not None and fila["merge_line_id"] in por_blanca:
                sustituida = por_blanca.pop(fila["merge_line_id"])
                finales.remove(sustituida)
            finales.append(copia)
            if fila.get("codigo_externo") is not None:
                externos.append((copia, fila["codigo_externo"]))
        return finales, externos, perdidas

    def _aplicar_a_pareja(
        self,
        session: Any,
        *,
        header: ValuationHeaderRecord,
        valuation_id: str,
        pareja: AlbaranLineValuationOrm,
        edicion: EdicionManual,
        codigo_producto: str | None,
        now: str,
    ) -> None:
        """(R25, R27) La edición encima de la fila nueva (``aplicar_edicion``) y
        su origen."""
        nueva = aplicar_edicion(self._columnas_de_fila(pareja), edicion)
        columnas = {c for campo in edicion.campos for c in COLUMNAS_DE_CAMPO.get(campo, ())}
        columnas |= {"precio_unitario_final", "importe_calculado", "importe_source", "edicion_manual_json"}
        for columna in columnas - {"codigo_externo"}:
            setattr(pareja, columna, nueva[columna])
        self._poner_origen(
            session, header=header, valuation_id=valuation_id, fila=pareja,
            origen=edicion.campos.get("origen"), codigo_producto=codigo_producto, now=now,
        )

    def _copiar_fila(
        self,
        session: Any,
        *,
        header: ValuationHeaderRecord,
        valuation_id: str,
        fila: dict[str, Any],
        derivada: dict[str, Any] | None,
        now: str,
    ) -> AlbaranLineValuationOrm:
        """(R26, R27) La fila anterior entera en la valoración nueva: con su
        derivada copiada (si tenía) y, si estaba vinculada a una línea que no es
        del contrato nuevo, Nueva con su P y ``front_contrato_cambiado``."""
        datos = {
            k: v for k, v in fila.items()
            if k not in ("id", "valuation_id", "derived_contrato_line_id", "codigo_externo")
        }
        copia = AlbaranLineValuationOrm(**{**datos, "valuation_id": valuation_id})
        if derivada is not None:
            nueva = ContratoLineDerivedOrm(**{
                **{k: v for k, v in derivada.items() if k not in ("id", "created_by_valuation_id")},
                "created_by_valuation_id": valuation_id,
                "source_document_id": header.document_id,
            })
            session.add(nueva)
            session.flush()
            copia.derived_contrato_line_id = int(nueva.id)
        elif (
            copia.matched_contrato_line_id is not None
            and self._contrato_de_linea(session, copia.matched_contrato_line_id) != header.contrato_codigo
        ):
            self._poner_origen(
                session, header=header, valuation_id=valuation_id, fila=copia,
                origen={"tipo": "contrato", "linea": copia.matched_contrato_line_id},
                codigo_producto=None, now=now,
            )
        return copia

    # ------------------------------------------------------------------ #
    # Builders ORM
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_derived_orm(
        *,
        valuation_id: str,
        document_id: str,
        record: DerivedContratoLineRecord,
        created_at_utc: str,
    ) -> ContratoLineDerivedOrm:
        return ContratoLineDerivedOrm(
            created_by_valuation_id=valuation_id,
            source_document_id=document_id,
            codigo_contrato=record.codigo_contrato,
            codigo_producto=record.codigo_producto,
            descripcion_linea=record.descripcion_linea,
            unidad_medida=record.unidad_medida,
            precio_unitario=record.precio_unitario,
            codigo_partida=record.codigo_partida,
            origen=record.origen,
            created_at_utc=created_at_utc,
        )

    @staticmethod
    def _build_line_orm(
        *,
        valuation_id: str,
        line: LineValuationRecord,
        derived_contrato_line_id: int | None,
        created_at_utc: str,
    ) -> AlbaranLineValuationOrm:
        return AlbaranLineValuationOrm(
            valuation_id=valuation_id,
            merge_line_id=line.merge_line_id,
            matched_contrato_line_id=line.matched_contrato_line_id,
            derived_contrato_line_id=derived_contrato_line_id,
            precio_unitario_contrato_db=line.precio_unitario_contrato_db,
            precio_unitario_pdf_inferido=line.precio_unitario_pdf_inferido,
            precio_unitario_final=line.precio_unitario_final,
            precio_unitario_source=line.precio_unitario_source,
            precio_unitario_agreement=line.precio_unitario_agreement,
            unidad_albaran=line.unidad_albaran,
            unidad_contrato=line.unidad_contrato,
            unidad_categoria=line.unidad_categoria,
            unidad_category_match=line.unidad_category_match,
            cantidad_albaran=line.cantidad_albaran,
            cantidad_convertida=line.cantidad_convertida,
            factor_conversion=line.factor_conversion,
            importe_calculado=line.importe_calculado,
            importe_albaran_declarado=line.importe_albaran_declarado,
            importe_source=line.importe_source,
            codigo_partida_albaran=line.codigo_partida_albaran,
            codigo_partida_final=line.codigo_partida_final,
            partida_action=line.partida_action,
            match_confidence_pct=float(line.match_confidence_pct),
            match_method=line.match_method,
            review_required=bool(line.review_required),
            review_reasons_json=json.dumps(
                line.review_reasons, ensure_ascii=False,
            ),
            ia_reasoning=line.ia_reasoning,
            created_at_utc=created_at_utc,
            # Sub-tanda 2C: contexto de línea.
            rol_linea=line.rol_linea,
            ref_linea_base_merge_id=line.ref_linea_base_merge_id,
            tarifa_pdf_encontrada=line.tarifa_pdf_encontrada,
            modifiers_applied_json=(
                json.dumps(line.modifiers_applied, ensure_ascii=False)
                if line.modifiers_applied is not None
                else None
            ),
            # Sub-tanda 2D: líneas sintéticas.
            line_kind=line.line_kind,
            parent_merge_line_id=line.parent_merge_line_id,
            modifier_source=line.modifier_source,
            modifier_reason=line.modifier_reason,
            descripcion_linea=line.descripcion_linea,
            # Tanda descuento — abr 2026
            descuento_albaran_aplicado=line.descuento_albaran_aplicado,
        )

    # ------------------------------------------------------------------ #
    # To dict
    # ------------------------------------------------------------------ #
    @staticmethod
    def _header_to_dict(header: AlbaranValuationOrm) -> dict[str, Any]:
        return {
            "valuation_id": header.id,
            "document_id": header.document_id,
            "contrato_codigo": header.contrato_codigo,
            "status": header.status,
            "provider_ia": header.provider_ia,
            "model_name": header.model_name,
            "prompt_key": header.prompt_key,
            "total_valorado": float(header.total_valorado or 0.0),
            "total_lines": int(header.total_lines or 0),
            "lines_matched_exact": int(header.lines_matched_exact or 0),
            "lines_matched_semantic": int(header.lines_matched_semantic or 0),
            "lines_matched_price_only": int(
                header.lines_matched_price_only or 0
            ),
            "lines_unmatched": int(header.lines_unmatched or 0),
            "review_required": bool(header.review_required),
            "review_reasons": json.loads(header.review_reasons_json or "[]"),
            "created_at_utc": header.created_at_utc,
            "updated_at_utc": header.updated_at_utc,
        }

    @staticmethod
    def _line_to_dict(line: AlbaranLineValuationOrm) -> dict[str, Any]:
        return {
            "id": line.id,
            "valuation_id": line.valuation_id,
            "merge_line_id": line.merge_line_id,
            "matched_contrato_line_id": line.matched_contrato_line_id,
            "derived_contrato_line_id": line.derived_contrato_line_id,
            "precio_unitario_contrato_db": line.precio_unitario_contrato_db,
            "precio_unitario_pdf_inferido": line.precio_unitario_pdf_inferido,
            "precio_unitario_final": line.precio_unitario_final,
            "precio_unitario_source": line.precio_unitario_source,
            "precio_unitario_agreement": line.precio_unitario_agreement,
            "unidad_albaran": line.unidad_albaran,
            "unidad_contrato": line.unidad_contrato,
            "unidad_categoria": line.unidad_categoria,
            "unidad_category_match": bool(line.unidad_category_match),
            "cantidad_albaran": line.cantidad_albaran,
            "cantidad_convertida": line.cantidad_convertida,
            "factor_conversion": line.factor_conversion,
            "importe_calculado": line.importe_calculado,
            "importe_albaran_declarado": line.importe_albaran_declarado,
            "importe_source": line.importe_source,
            "codigo_partida_albaran": line.codigo_partida_albaran,
            "codigo_partida_final": line.codigo_partida_final,
            "partida_action": line.partida_action,
            "match_confidence_pct": float(line.match_confidence_pct or 0.0),
            "match_method": line.match_method,
            "review_required": bool(line.review_required),
            "review_reasons": json.loads(line.review_reasons_json or "[]"),
            "ia_reasoning": line.ia_reasoning,
            "created_at_utc": line.created_at_utc,
            # Sub-tanda 2C: contexto estructural.
            "rol_linea": line.rol_linea,
            "ref_linea_base_merge_id": line.ref_linea_base_merge_id,
            "tarifa_pdf_encontrada": (
                bool(line.tarifa_pdf_encontrada)
                if line.tarifa_pdf_encontrada is not None
                else None
            ),
            "modifiers_applied": (
                json.loads(line.modifiers_applied_json)
                if line.modifiers_applied_json
                else None
            ),
            # Sub-tanda 2D: líneas sintéticas.
            "line_kind": line.line_kind,
            "parent_merge_line_id": line.parent_merge_line_id,
            "modifier_source": line.modifier_source,
            "modifier_reason": line.modifier_reason,
            "descripcion_linea": line.descripcion_linea,
            # Tanda descuento — abr 2026
            "descuento_albaran_aplicado": line.descuento_albaran_aplicado,
        }

    @staticmethod
    def _derived_to_dict(d: ContratoLineDerivedOrm) -> dict[str, Any]:
        return {
            "id": d.id,
            "created_by_valuation_id": d.created_by_valuation_id,
            "source_document_id": d.source_document_id,
            "codigo_contrato": d.codigo_contrato,
            "codigo_producto": d.codigo_producto,
            "descripcion_linea": d.descripcion_linea,
            "unidad_medida": d.unidad_medida,
            "precio_unitario": d.precio_unitario,
            "codigo_partida": d.codigo_partida,
            "origen": d.origen,
            "created_at_utc": d.created_at_utc,
        }
