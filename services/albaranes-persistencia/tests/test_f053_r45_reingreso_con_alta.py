# tests/test_f053_r45_reingreso_con_alta.py
"""F-053 · R45 (decisión D1 del humano, 2026-10-06): reingresar un PDF cuyo
merge tiene un alta en Sigrid bloqueante NO lo borra.

``save`` borraba todos los documentos con el mismo ``source_sha256``
(``_delete_existing_records``) y el FK ``ON DELETE CASCADE`` se llevaba la fila
del alta, también ``registrado``. Ahora, si el alta es bloqueante
(``en_curso``, ``incierto`` o ``registrado``; ``ruesma_comun.alta_sigrid``),
sv3 lo trata como duplicado: conserva documento, merge y alta, no lo
reprocesa (ni enriquece ni revalora) y lo deja en el log. Con un alta en otro
estado, o sin alta, todo sigue como hoy.

D3 (decisión del humano, 2026-10-07: «un albarán no se puede pisar»): el
pipeline mira el alta (``buscar_conservado_por_alta``) ANTES de nada, así que
ni el documento activo se reprocesa (rama de duplicado) ni se sube el PDF a
SharePoint en ninguno de los dos caminos. ``save`` conserva su mirada para la
carrera con sv9.

``save`` REAL del repositorio sobre una sesión doble (sin BBDD) y el pipeline
con dobles. Sin red ni BBDD.
"""
from __future__ import annotations

import hashlib
import logging

import pytest

from application.pipelines.persist_albaran_pipeline import (
    PersistAlbaranPipeline,
    PersistAlbaranRequest,
)
from domain.models.extraction_models import ExtractionEnvelope
from domain.models.persistence_models import ExistingDocument, StoredFile
from infrastructure.database.orm_models import (
    AlbaranDocumentMergeOrm,
    AlbaranDocumentOrm,
)
from infrastructure.database.sqlalchemy_albaran_repository import (
    SqlAlchemyAlbaranRepository,
)

_PDF = b"%PDF-1.4 albaran reingresado"
_SHA = hashlib.sha256(_PDF).hexdigest()
_MERGE_ID = "6f1d2c3b-0000-4000-8000-00000000f053"


def _envelope_dict() -> dict:
    return {
        "meta": {
            "prompt_key": "albaran_revision_fase2", "schema": "albaran_v2",
            "source_filename": "ALB.pdf", "source_mime_type": "application/pdf",
            "source_sha256": _SHA, "model": "gpt-5.2",
            "processed_at_utc": "2026-10-06T08:00:00+00:00",
        },
        "data": {
            "cabecera": {"proveedor_nombre": "PROVEEDOR", "proveedor_cif": "B00000000",
                         "numero_albaran": "A-1", "fecha": "2026-10-01"},
            "lineas": [{"codigo": "X", "concepto": "Material", "cantidad": 1.0,
                        "confianza_pct": 90.0}],
        },
        "debug": {},
    }


# ------------------------------------------------------------------ #
# Sesión doble: el merge previo, su alta y lo que se borra o se añade.
# ------------------------------------------------------------------ #
class _Filas:
    def __init__(self, filas) -> None:
        self._filas = list(filas)

    def all(self):
        return list(self._filas)

    def mappings(self):
        return self

    def scalars(self):
        return self

    def __iter__(self):
        return iter(self._filas)

    def scalar(self):
        return self._filas[0] if self._filas else None


_IGUAL = object()


class _Sesion:
    """Simula READ COMMITTED lo justo para la carrera con sv9 (H4): la
    instantánea de una sentencia se toma AL EMPEZAR, también si luego espera
    un cerrojo. ``estado_antes_del_cerrojo`` es el alta que ve una sentencia
    que arranca antes de tener el cerrojo de los merges (sv9 aún sin
    confirmar); ``estado_alta``, la que ve una sentencia lanzada ya con él.
    ``en_papelera``: el merge tiene ``is_active = false`` y una sentencia que
    filtre por ``is_active`` no lo ve (C9)."""

    def __init__(self, *, estado_alta: str | None, hay_tabla_altas: bool = True,
                 estado_antes_del_cerrojo=_IGUAL, en_papelera: bool = False,
                 hay_merge: bool = True) -> None:
        self.estado_alta = estado_alta
        self.estado_antes_del_cerrojo = (
            estado_alta if estado_antes_del_cerrojo is _IGUAL else estado_antes_del_cerrojo
        )
        self.hay_tabla_altas = hay_tabla_altas
        self.en_papelera = en_papelera
        self.hay_merge = hay_merge
        self.con_cerrojo = False
        self.merge_previo = AlbaranDocumentMergeOrm(
            id=_MERGE_ID, source_sha256=_SHA, sharepoint_share_url="https://sp/albaran.pdf",
        )
        self.raw_previo = AlbaranDocumentOrm(id="raw-1", source_sha256=_SHA)
        self.sql: list[str] = []
        self.borrados: list = []
        self.anadidos: list = []
        self.confirmada = False
        self.deshecha = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sentencia, parametros=None):
        texto = str(sentencia)
        self.sql.append(texto)
        if "to_regclass" in texto:
            return _Filas([self.hay_tabla_altas])
        bloquea = "FOR UPDATE" in texto and "albaran_documents_merge" in texto
        lee_alta = "albaran_altas_sigrid" in texto
        if not (bloquea or lee_alta):
            return _Filas([])  # el DELETE de contratos
        # Instantánea del ARRANQUE de la sentencia (antes de esperar el cerrojo).
        estado = self.estado_alta if self.con_cerrojo else self.estado_antes_del_cerrojo
        if bloquea:
            self.con_cerrojo = True
        visible = self.hay_merge and not (self.en_papelera and "is_active" in texto)
        if not lee_alta:  # solo el cerrojo de los merges: sus ``id``
            assert parametros == {"sha": _SHA}
            return _Filas([_MERGE_ID] if visible else [])
        assert parametros in ({"sha": _SHA}, {"ids": [_MERGE_ID]}), parametros
        return _Filas([{"document_id": _MERGE_ID, "estado": estado,
                        "sigrid_cod": "AC26/0001"}] if visible else [])

    def scalars(self, consulta):
        entidad = consulta.column_descriptions[0]["entity"]
        if entidad is AlbaranDocumentMergeOrm:
            return _Filas([self.merge_previo])
        if entidad is AlbaranDocumentOrm:
            return _Filas([self.raw_previo])
        return _Filas([])

    def scalar(self, consulta):  # nº de líneas del conservado
        return 4

    def get(self, entidad, clave):
        assert entidad is AlbaranDocumentMergeOrm and clave == _MERGE_ID
        return self.merge_previo

    def delete(self, objeto):
        self.borrados.append(objeto)

    def flush(self):
        pass

    def add(self, objeto):
        self.anadidos.append(objeto)

    def commit(self):
        self.confirmada = True

    def rollback(self):
        self.deshecha = True


class _Fabrica:
    generation = 1

    def __init__(self, sesion: _Sesion) -> None:
        self.sesion = sesion

    def ensure_database_and_engine(self):
        pass

    def create_session(self):
        return self.sesion


def _guardar(sesion: _Sesion) -> ExistingDocument:
    repositorio = SqlAlchemyAlbaranRepository(session_factory=_Fabrica(sesion))
    repositorio._initialized_generation = _Fabrica.generation  # sin crear tablas
    return repositorio.save(
        envelope=ExtractionEnvelope.model_validate(_envelope_dict()), context={},
        stored_file=StoredFile(drive_id="d", item_id="i", relative_path="albaranes/A-1.pdf",
                               web_url=None, share_url="https://sp/nuevo.pdf"),
    )


def _buscar(sesion: _Sesion):
    repositorio = SqlAlchemyAlbaranRepository(session_factory=_Fabrica(sesion))
    repositorio._initialized_generation = _Fabrica.generation  # sin crear tablas
    return repositorio.buscar_conservado_por_alta(_SHA)


def _sentencias_r45(sql: list[str]) -> tuple[list[int], list[int]]:
    """Posiciones del cerrojo de los merges y de la lectura del alta."""
    cerrojos = [i for i, s in enumerate(sql) if "FOR UPDATE" in s and "albaran_documents_merge" in s]
    lecturas = [i for i, s in enumerate(sql) if "albaran_altas_sigrid" in s and "to_regclass" not in s]
    return cerrojos, lecturas


def _comprobar_cerrojo_antes_de_leer_el_alta(sql: list[str]) -> None:
    """H4: el cerrojo de los merges va en una sentencia ANTERIOR y DISTINTA a
    la lectura de ``albaran_altas_sigrid``. En READ COMMITTED la instantánea
    se toma al empezar la sentencia: si una sola esperase el cerrojo, no vería
    el alta que sv9 confirma mientras tanto."""
    cerrojos, lecturas = _sentencias_r45(sql)
    assert len(cerrojos) == 1 and len(lecturas) == 1, sql
    assert cerrojos[0] < lecturas[0], sql


@pytest.mark.parametrize("estado", ["en_curso", "incierto", "registrado"])
def test_f053_r45_reingreso_con_alta_bloqueante_no_borra_y_conserva(estado, caplog):
    caplog.set_level(logging.WARNING)
    sesion = _Sesion(estado_alta=estado)
    guardado = _guardar(sesion)
    # Nada borrado (ni merge, ni crudo, ni contratos), nada nuevo, nada confirmado.
    assert sesion.borrados == [] and sesion.anadidos == []
    assert not sesion.confirmada and sesion.deshecha
    assert not any(s.lstrip().upper().startswith("DELETE") for s in sesion.sql)
    # Devuelve el documento conservado, marcado para que el pipeline no lo toque.
    assert guardado == ExistingDocument(
        document_id=_MERGE_ID, source_sha256=_SHA, sharepoint_url="https://sp/albaran.pdf",
        stored_lines=4, conservado_por_alta=True,
    )
    # El merge queda bloqueado ANTES de mirar el alta (carrera con sv9, H4).
    _comprobar_cerrojo_antes_de_leer_el_alta(sesion.sql)
    # Log claro: documento, estado y código de Sigrid.
    assert _MERGE_ID in caplog.text and estado in caplog.text and "AC26/0001" in caplog.text


@pytest.mark.parametrize("estado", [
    None, "no_admitido", "ya_en_sigrid", "simulado", "revisar", "error", "anulado",
])
def test_f053_r45_sin_alta_o_no_bloqueante_se_borra_y_se_guarda_como_hoy(estado):
    sesion = _Sesion(estado_alta=estado)
    guardado = _guardar(sesion)
    assert sesion.merge_previo in sesion.borrados and sesion.raw_previo in sesion.borrados
    assert sesion.confirmada and not sesion.deshecha
    assert any(isinstance(d, AlbaranDocumentMergeOrm) for d in sesion.anadidos)
    assert guardado.document_id != _MERGE_ID and guardado.conservado_por_alta is False


@pytest.mark.parametrize("mirada", ["save", "buscar"])
def test_f053_r45_h4_alta_confirmada_mientras_espera_el_cerrojo_se_conserva(mirada):
    """H4 (review pasada 2): sv9 bloquea el merge e inserta ``en_curso`` sin
    confirmar; sv3 lanza la mirada y espera el cerrojo; sv9 confirma. sv3
    tiene que ver ``en_curso`` y conservar, no borrar (el CASCADE se llevaría
    el alta mientras sv9 sigue hacia la grabación)."""
    sesion = _Sesion(estado_alta="en_curso", estado_antes_del_cerrojo=None)
    resultado = _guardar(sesion) if mirada == "save" else _buscar(sesion)
    assert resultado is not None and resultado.conservado_por_alta is True
    assert resultado.document_id == _MERGE_ID
    assert sesion.borrados == [] and sesion.anadidos == [] and not sesion.confirmada
    _comprobar_cerrojo_antes_de_leer_el_alta(sesion.sql)


@pytest.mark.parametrize("mirada", ["save", "buscar"])
def test_f053_r45_c9_merge_en_la_papelera_con_alta_se_conserva(mirada):
    """C9 (review pasada 2): R45 cubre también el merge en la papelera
    (``is_active = false``, D3). Ni el cerrojo ni la lectura del alta filtran
    por ``is_active``."""
    sesion = _Sesion(estado_alta="registrado", en_papelera=True)
    resultado = _guardar(sesion) if mirada == "save" else _buscar(sesion)
    assert resultado is not None and resultado.conservado_por_alta is True
    assert resultado.document_id == _MERGE_ID
    assert sesion.borrados == [] and not sesion.confirmada
    cerrojos, lecturas = _sentencias_r45(sesion.sql)
    assert cerrojos and lecturas
    assert not any("is_active" in sesion.sql[i] for i in cerrojos + lecturas), sesion.sql


def test_f053_r45_sin_merges_del_sha_no_lee_el_alta():
    """Sin merges con ese ``source_sha256`` no hay alta que mirar: no se lanza
    la segunda sentencia."""
    sesion = _Sesion(estado_alta="registrado", hay_merge=False)
    assert _buscar(sesion) is None
    cerrojos, lecturas = _sentencias_r45(sesion.sql)
    assert len(cerrojos) == 1 and lecturas == []


def test_f053_r45_sin_tabla_de_altas_se_borra_como_hoy():
    """Si el DDL de la fase 2 no se aplicó, la consulta del alta no se lanza
    (abortaría la transacción) y ``save`` sigue como hoy."""
    sesion = _Sesion(estado_alta="registrado", hay_tabla_altas=False)
    guardado = _guardar(sesion)
    assert not any("albaran_altas_sigrid" in s and "to_regclass" not in s for s in sesion.sql)
    assert sesion.merge_previo in sesion.borrados and sesion.confirmada
    assert guardado.conservado_por_alta is False


# ------------------------------------------------------------------ #
# Pipeline: el conservado no se reprocesa.
# ------------------------------------------------------------------ #
class _RepoConservado:
    """Carrera con sv9: la mirada previa (D3) no ve alta bloqueante, el alta
    empieza antes de ``save`` y ``save`` lo conserva en su transacción.
    Cualquier otro método del repositorio es un fallo."""

    def __init__(self) -> None:
        self.guardados = 0

    def buscar_conservado_por_alta(self, source_sha256: str):
        return None

    def get_by_sha256(self, source_sha256: str):
        return None

    def save(self, **_kwargs) -> ExistingDocument:
        self.guardados += 1
        return ExistingDocument(document_id=_MERGE_ID, source_sha256=_SHA,
                                sharepoint_url="https://sp/albaran.pdf", stored_lines=4,
                                conservado_por_alta=True)

    def __getattr__(self, nombre):
        raise AssertionError(f"el documento conservado no se toca: {nombre}")


class _Almacen:
    def upload(self, **_kwargs) -> StoredFile:
        return StoredFile(drive_id="d", item_id="i", relative_path="albaranes/A-1.pdf",
                          web_url=None, share_url=None)


class _Normalizador:
    def normalize_provider_document(self, *, document, provider_origin):
        return document


class _Valoracion:
    def trigger_async(self, **_kwargs):
        raise AssertionError("el documento conservado no se revalora")

    def trigger_sync(self, **_kwargs):  # pragma: no cover
        raise AssertionError("el documento conservado no se revalora")


def test_f053_r45_el_pipeline_no_reprocesa_el_documento_conservado(caplog):
    caplog.set_level(logging.INFO)
    repo = _RepoConservado()
    pipeline = PersistAlbaranPipeline(
        repository=repo, document_storage=_Almacen(), normalizer=_Normalizador(),
        valuation_trigger=_Valoracion(),
    )
    resultado = pipeline.run(PersistAlbaranRequest(
        filename="ALB.pdf", mime_type="application/pdf", file_bytes=_PDF,
        extraction_envelope=_envelope_dict(), context={},
    ))
    assert repo.guardados == 1
    assert resultado.ok and resultado.duplicate is True
    assert resultado.document_id == _MERGE_ID and resultado.stored_lines == 4
    assert _MERGE_ID in caplog.text


# ------------------------------------------------------------------ #
# D3 (decisión del humano, 2026-10-07): «un albarán no se puede pisar».
# La mirada del alta tiene su propio método del repositorio, para que el
# pipeline la haga ANTES de tocar nada (también en la rama de duplicado).
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("estado", ["en_curso", "incierto", "registrado"])
def test_f053_r45_buscar_conservado_con_alta_bloqueante_lo_devuelve_sin_escribir(estado, caplog):
    caplog.set_level(logging.WARNING)
    sesion = _Sesion(estado_alta=estado)
    conservado = _buscar(sesion)
    assert conservado == ExistingDocument(
        document_id=_MERGE_ID, source_sha256=_SHA, sharepoint_url="https://sp/albaran.pdf",
        stored_lines=4, conservado_por_alta=True,
    )
    # Solo lectura: ni borra, ni añade, ni confirma; la misma consulta que ``save``.
    assert sesion.borrados == [] and sesion.anadidos == [] and not sesion.confirmada
    assert not any(s.lstrip().upper().startswith(("DELETE", "UPDATE", "INSERT")) for s in sesion.sql)
    _comprobar_cerrojo_antes_de_leer_el_alta(sesion.sql)
    assert _MERGE_ID in caplog.text and estado in caplog.text and "AC26/0001" in caplog.text


@pytest.mark.parametrize("estado", [
    None, "no_admitido", "ya_en_sigrid", "simulado", "revisar", "error", "anulado",
])
def test_f053_r45_buscar_conservado_sin_alta_bloqueante_es_none(estado):
    sesion = _Sesion(estado_alta=estado)
    assert _buscar(sesion) is None
    assert sesion.borrados == [] and sesion.anadidos == [] and not sesion.confirmada


def test_f053_r45_buscar_conservado_sin_tabla_de_altas_es_none():
    sesion = _Sesion(estado_alta="registrado", hay_tabla_altas=False)
    assert _buscar(sesion) is None
    assert not any("albaran_altas_sigrid" in s and "to_regclass" not in s for s in sesion.sql)


class _Espia:
    """Doble que apunta cualquier método al que se le llame (los pasos del
    pipeline son best-effort: una excepción se la tragarían)."""

    def __init__(self, nombre: str, llamadas: list[str]) -> None:
        self._nombre = nombre
        self._llamadas = llamadas

    def __getattr__(self, metodo):
        def _apuntar(*_args, **_kwargs):
            self._llamadas.append(f"{self._nombre}.{metodo}")
        return _apuntar


class _RepoActivoConservado:
    """El documento está ACTIVO (``get_by_sha256`` lo ve) y tiene un alta
    bloqueante. Apunta todo lo que el pipeline le pida además de mirar."""

    def __init__(self, llamadas: list[str], *, activo: bool = True,
                 conservado: bool = True) -> None:
        self.llamadas = llamadas
        self.activo = activo
        self.conservado = conservado

    def get_by_sha256(self, source_sha256: str):
        assert source_sha256 == _SHA
        if not self.activo:
            return None
        return ExistingDocument(document_id=_MERGE_ID, source_sha256=_SHA,
                                sharepoint_url="https://sp/albaran.pdf", stored_lines=4)

    def buscar_conservado_por_alta(self, source_sha256: str):
        assert source_sha256 == _SHA
        if not self.conservado:
            return None
        return ExistingDocument(document_id=_MERGE_ID, source_sha256=_SHA,
                                sharepoint_url="https://sp/albaran.pdf", stored_lines=4,
                                conservado_por_alta=True)

    def has_selected_contrato_with_lines(self, *, document_id: str):
        self.llamadas.append("repo.has_selected_contrato_with_lines")
        return True, "CTSU24/0228"

    def save(self, **_kwargs) -> ExistingDocument:
        """Como el ``save`` real: lo conservaría dentro de su transacción."""
        self.llamadas.append("repo.save")
        return self.buscar_conservado_por_alta(_SHA)

    def __getattr__(self, nombre):
        def _apuntar(*_args, **_kwargs):
            self.llamadas.append(f"repo.{nombre}")
        return _apuntar


def _pipeline_espiado(repo, llamadas: list[str]) -> PersistAlbaranPipeline:
    return PersistAlbaranPipeline(
        repository=repo, document_storage=_Espia("sharepoint", llamadas),
        normalizer=_Normalizador(),
        header_resolver_service=_Espia("cabecera", llamadas),
        obra_enrichment_service=_Espia("obra", llamadas),
        contrato_enrichment_service=_Espia("contratos", llamadas),
        valuation_trigger=_Espia("valoracion", llamadas),
        fecha_guard_service=_Espia("fecha", llamadas),
    )


def _reingresar(pipeline: PersistAlbaranPipeline, *, force_refetch: bool = False):
    envelope = _envelope_dict()
    envelope["data"]["clasificacion"] = {"familia": "residuos", "confianza_pct": 100.0, "motivo": "LER",
                                         "mixto": False, "familias_secundarias": [], "origen": "ia2"}
    envelope["data"]["lineas"][0]["contexto_linea"] = {"tipo_familia": "residuos", "rol_linea": "base",
                                                       "codigo_ler": "170604", "volumen_m3": 6.0}
    return pipeline.run(PersistAlbaranRequest(
        filename="ALB.pdf", mime_type="application/pdf", file_bytes=_PDF,
        extraction_envelope=envelope, context={}, force_refetch=force_refetch,
    ))


@pytest.mark.parametrize("force_refetch", [False, True])
def test_f053_r45_d3_reingreso_de_un_activo_con_alta_no_toca_nada(force_refetch, caplog):
    """1a: la rama de duplicado no reescribe clasificación ni contexto de
    líneas, no resuelve cabecera, no re-enriquece obra ni contratos y no
    revalora (aunque el reingreso venga con ``force_refetch``)."""
    caplog.set_level(logging.INFO)
    llamadas: list[str] = []
    resultado = _reingresar(
        _pipeline_espiado(_RepoActivoConservado(llamadas), llamadas), force_refetch=force_refetch,
    )
    assert llamadas == []
    assert resultado.ok and resultado.duplicate is True
    assert resultado.document_id == _MERGE_ID and resultado.stored_lines == 4
    assert resultado.sharepoint_url == "https://sp/albaran.pdf"
    assert resultado.contratos_count == 0 and resultado.selected_contrato_codigo is None
    assert any(_MERGE_ID in r.getMessage() and "conservado_por_alta=True" in r.getMessage()
               for r in caplog.records)


def test_f053_r45_d3_reingreso_de_un_activo_sin_alta_bloqueante_se_reprocesa_como_hoy():
    llamadas: list[str] = []
    resultado = _reingresar(
        _pipeline_espiado(_RepoActivoConservado(llamadas, conservado=False), llamadas),
    )
    assert resultado.duplicate is True
    for paso in ("repo.update_merge_clasificacion", "repo.update_merge_lineas_contexto",
                 "cabecera.resolve_merge_document", "obra.enrich_merge_document",
                 "valoracion.trigger_async"):
        assert paso in llamadas, (paso, llamadas)
    assert not any(c.startswith("sharepoint.") for c in llamadas)


# ------------------------------------------------------------------ #
# D3 · 1c: la mirada va ANTES de subir el PDF a SharePoint, y también
# para el documento en la papelera (``get_by_sha256`` no lo ve).
# ------------------------------------------------------------------ #
def test_f053_r45_d3_reingreso_de_uno_en_la_papelera_con_alta_no_sube_nada(caplog):
    caplog.set_level(logging.INFO)
    llamadas: list[str] = []
    resultado = _reingresar(
        _pipeline_espiado(_RepoActivoConservado(llamadas, activo=False), llamadas),
    )
    # Ni SharePoint, ni ``save``, ni enriquecer, ni revalorar.
    assert llamadas == []
    assert resultado.ok and resultado.duplicate is True
    assert resultado.document_id == _MERGE_ID and resultado.stored_lines == 4
    assert resultado.sharepoint_url == "https://sp/albaran.pdf"
    assert any(_MERGE_ID in r.getMessage() and "conservado_por_alta=True" in r.getMessage()
               for r in caplog.records)


class _RepoNuevo(_RepoActivoConservado):
    """Sin documento activo; apunta también la mirada del alta y ``save``."""

    def __init__(self, llamadas: list[str]) -> None:
        super().__init__(llamadas, activo=False, conservado=False)

    def buscar_conservado_por_alta(self, source_sha256: str):
        self.llamadas.append("repo.buscar_conservado_por_alta")
        return super().buscar_conservado_por_alta(source_sha256)

    def save(self, **_kwargs) -> ExistingDocument:
        self.llamadas.append("repo.save")
        return ExistingDocument(document_id="merge-nuevo", source_sha256=_SHA,
                                sharepoint_url=None, stored_lines=1)


def test_f053_r45_d3_la_mirada_va_antes_de_sharepoint_y_sin_alta_se_guarda_como_hoy():
    llamadas: list[str] = []
    resultado = _reingresar(_pipeline_espiado(_RepoNuevo(llamadas), llamadas))
    assert resultado.duplicate is False and resultado.document_id == "merge-nuevo"
    assert llamadas[:3] == ["repo.buscar_conservado_por_alta", "sharepoint.upload", "repo.save"]
    assert llamadas.count("repo.buscar_conservado_por_alta") == 1
