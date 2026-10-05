# tests/test_f054_pipeline.py
"""R5 y R13-R24 (F-054): el pipeline de sv1 con correos adjuntos.

Piezas reales (``PdfPageSplitter`` y, desde T7, ``MimeDocumentoExtractor``)
y dobles en memoria para el buzon y el intake (``dobles_sv1``). Los correos
adjuntos se construyen en memoria (``eml_sinteticos``): sin red, sin BBDD,
sin datos reales.
"""
from __future__ import annotations

import hashlib
import logging

import pytest
from dobles_sv1 import (
    BUZON,
    CARPETA_ORIGEN,
    ID_ERRORES,
    ID_PROCESADOS,
    BuzonDoble,
    EnvioRegistrado,
    IntakeDoble,
    adjunto,
    construir_pipeline,
    contenido_inventado,
    ejecutar_ciclo,
    mensaje,
    pdf_de_paginas,
)
from domain.ports.orchestrator_port import OrchestratorAck, OrchestratorError
from eml_sinteticos import (
    Fichero,
    a_bytes,
    correo,
    envolver,
    fichero_jpeg,
    fichero_pdf,
    fichero_png,
    fichero_texto,
    jpeg_bytes,
    png_bytes,
)
from ruesma_comun.correo import construir_contexto_correo

ITEM = "#microsoft.graph.itemAttachment"


def _sha(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


# --- R16 · el meta de un adjunto directo no cambia ------------------------ #
def test_f054_r16_meta_de_adjunto_directo_identico_clave_a_clave():
    pdf = pdf_de_paginas(1)
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1", asunto="Albaran obra")],
        adjuntos={"msg-1": [adjunto("a", "albaran.pdf")]},
        ficheros={"a": pdf},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert [e.meta for e in intake.envios] == [{
        "email_message_id": "msg-1",
        "email_received_at_utc": "2026-09-23T08:00:00Z",
        "from_address": "proveedor@ejemplo.test",
        "subject": "Albaran obra",
        "attachment_filename": "albaran.pdf",
        "attachment_sha256": _sha(pdf),
        "attachment_content_type": "application/pdf",
        "attachment_size_bytes": len(pdf),
        "page_number": 1,
        "total_pages": 1,
        "page_sha256": _sha(pdf),
    }]
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f054_r16_meta_de_una_imagen_directa_identico_clave_a_clave():
    foto = b"\x89PNG\r\n\x1a\nfoto inventada"
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("a", "foto.png", content_type="image/png")]},
        ficheros={"a": foto},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    (envio,) = intake.envios
    assert set(envio.meta) == {
        "email_message_id", "email_received_at_utc", "from_address", "subject",
        "attachment_filename", "attachment_sha256", "attachment_content_type",
        "attachment_size_bytes", "page_number", "total_pages", "page_sha256",
    }
    assert (envio.meta["attachment_filename"], envio.meta["attachment_content_type"]) == ("foto.png", "image/png")
    assert (envio.meta["page_number"], envio.meta["total_pages"]) == (1, 1)
    assert envio.meta["attachment_sha256"] == envio.meta["page_sha256"] == _sha(foto)


def test_f054_r16_paginas_de_un_pdf_directo_multipagina():
    pdf = pdf_de_paginas(3)
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("a", "lote.pdf")]},
        ficheros={"a": pdf},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert [(e.meta["page_number"], e.meta["total_pages"]) for e in intake.envios] == [(1, 3), (2, 3), (3, 3)]
    assert {e.meta["attachment_sha256"] for e in intake.envios} == {_sha(pdf)}
    assert [e.meta["attachment_filename"] for e in intake.envios] == [
        "lote__page_001_of_003.pdf", "lote__page_002_of_003.pdf", "lote__page_003_of_003.pdf"]
    assert all("correo_adjunto_id" not in e.meta for e in intake.envios)


# --------------------------------------------------------------------- #
# Ayudas de F-054.
# --------------------------------------------------------------------- #
def _correo_adjunto(att_id: str = "c1", *, size: int = 5000):
    return adjunto(att_id, "RV: albaran inventado", content_type="message/rfc822", odata_type=ITEM, size=size)


class IntakeConDedup(IntakeDoble):
    """Intake que contesta ``duplicate=True`` a la segunda clave igual (R19).

    ``rechazar`` contesta ``accepted=False``; ``fallar_en`` son los numeros de
    envio (1-based) que lanzan ``OrchestratorError``.
    """

    def __init__(self, *, rechazar: bool = False, fallar_en: frozenset[int] = frozenset()) -> None:
        super().__init__()
        self._rechazar = rechazar
        self._fallar_en = fallar_en
        self.claves: list[str] = []

    def submit_email_received(self, *, meta, file_bytes, filename, content_type, contexto_correo=None):
        self.envios.append(EnvioRegistrado(meta, file_bytes, filename, content_type, contexto_correo))
        if len(self.envios) in self._fallar_en:
            raise OrchestratorError("intake doble: fallo pedido por el test")
        clave = f"email:{meta['email_message_id']}:{meta['page_sha256']}"
        duplicado = clave in self.claves
        self.claves.append(clave)
        return OrchestratorAck(
            accepted=not self._rechazar, workflow_id=f"wf-{len(self.envios)}", duplicate=duplicado, message="ok"
        )


def _ciclo(adjuntos, ficheros, *, intake=None, contenido=None, max_bytes=25 * 1024 * 1024):
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")], adjuntos={"msg-1": adjuntos}, ficheros=ficheros, contenido=contenido
    )
    intake = intake if intake is not None else IntakeConDedup()
    construir_pipeline(buzon, intake).run_once(
        mailbox=BUZON,
        source_folder=CARPETA_ORIGEN,
        processed_folder_id=ID_PROCESADOS,
        errors_folder_id=ID_ERRORES,
        top=10,
        max_attachment_bytes=max_bytes,
    )
    return buzon, intake


def _nombres(intake):
    return [e.meta["attachment_filename"] for e in intake.envios]


def _eml_bueno():
    return a_bytes(correo(adjuntos=[fichero_pdf("dentro.pdf")]))


# --- R5 · una sola descarga y ninguna otra llamada a Graph ---------------- #
def test_f054_r5_el_correo_adjunto_se_descarga_una_vez_sin_mas_llamadas():
    eml = a_bytes(envolver(correo(adjuntos=[fichero_pdf("a.pdf", paginas=2)]), 2))

    buzon, intake = _ciclo([_correo_adjunto()], {"c1": eml})

    assert buzon.llamadas == [
        ("list_unread_with_attachments", CARPETA_ORIGEN),
        ("list_attachments", "msg-1"),
        ("get_contenido", "msg-1"),
        ("download_attachment_value", "c1"),
        ("move_message", "msg-1"),
    ]
    assert len(intake.envios) == 2


# --- R13 · cada documento interior va por el camino del directo ----------- #
def test_f054_r13_pdf_interior_multipagina_se_trocea_y_entra_por_el_intake():
    pdf = pdf_de_paginas(3)
    eml = a_bytes(correo(adjuntos=[Fichero(datos=pdf, nombre="lote.pdf")]))

    buzon, intake = _ciclo([_correo_adjunto()], {"c1": eml})

    assert _nombres(intake) == ["lote__page_001_of_003.pdf", "lote__page_002_of_003.pdf", "lote__page_003_of_003.pdf"]
    assert [e.content_type for e in intake.envios] == ["application/pdf"] * 3
    assert {e.meta["attachment_sha256"] for e in intake.envios} == {_sha(pdf)}
    assert intake.claves == [f"email:msg-1:{_sha(e.file_bytes)}" for e in intake.envios]
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f054_r13_correo_adjunto_solo_con_imagenes_entra_y_va_a_procesados():
    png, jpeg = png_bytes(b"foto-1"), jpeg_bytes(b"foto-2")
    eml = a_bytes(correo(adjuntos=[fichero_png("foto1.png", datos=png), fichero_jpeg("foto2.jpg", datos=jpeg)]))

    buzon, intake = _ciclo([_correo_adjunto()], {"c1": eml})

    assert [(e.filename, e.content_type, e.file_bytes) for e in intake.envios] == [
        ("foto1.png", "image/png", png), ("foto2.jpg", "image/jpeg", jpeg)]
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f054_r13_mixto_pdf_e_imagen_en_el_mismo_correo_adjunto():
    eml = a_bytes(correo(adjuntos=[fichero_pdf("a.pdf", paginas=2), fichero_png("foto.png")]))

    buzon, intake = _ciclo([_correo_adjunto()], {"c1": eml})

    assert [(e.meta["attachment_filename"], e.meta["attachment_content_type"]) for e in intake.envios] == [
        ("a__page_001_of_002.pdf", "application/pdf"),
        ("a__page_002_of_002.pdf", "application/pdf"),
        ("foto.png", "image/png"),
    ]
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


# --- R14 · limite por documento interior ---------------------------------- #
def test_f054_r14_documento_interior_que_excede_el_limite_se_descarta(caplog):
    grande, pequena = png_bytes(b"x" * 3000), png_bytes(b"y")
    eml = a_bytes(correo(adjuntos=[fichero_png("grande.png", datos=grande), fichero_png("pequena.png", datos=pequena)]))

    with caplog.at_level(logging.DEBUG):
        buzon, intake = _ciclo([_correo_adjunto(size=1000)], {"c1": eml}, max_bytes=2000)

    assert _nombres(intake) == ["pequena.png"]
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]
    avisos = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING and "excede" in r.getMessage()]
    assert len(avisos) == 1 and "c1" in avisos[0] and "grande.png" in avisos[0]


def test_f054_r14_documento_interior_justo_en_el_limite_entra():
    png = png_bytes(b"z" * 100)
    eml = a_bytes(correo(adjuntos=[fichero_png("justa.png", datos=png)]))

    _, intake = _ciclo([_correo_adjunto(size=10)], {"c1": eml}, max_bytes=len(png))

    assert _nombres(intake) == ["justa.png"]


def test_f054_r14_si_todos_exceden_no_hay_documento_hallado_y_va_a_errores(caplog):
    eml = a_bytes(correo(adjuntos=[fichero_png("grande.png", datos=png_bytes(b"x" * 3000))]))

    with caplog.at_level(logging.DEBUG):
        buzon, intake = _ciclo([_correo_adjunto(size=1000)], {"c1": eml}, max_bytes=2000)

    assert intake.envios == []
    assert buzon.movidos == [("msg-1", ID_ERRORES)]
    assert any("ningun documento" in r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)


# --- R15 · meta de una pagina interior ------------------------------------ #
def test_f054_r15_meta_de_un_pdf_interior():
    pdf = pdf_de_paginas(1)
    eml = a_bytes(envolver(correo(adjuntos=[Fichero(datos=pdf, nombre="albaran.pdf")]), 1))

    _, intake = _ciclo([_correo_adjunto()], {"c1": eml})

    assert [e.meta for e in intake.envios] == [{
        "email_message_id": "msg-1",
        "email_received_at_utc": "2026-09-23T08:00:00Z",
        "from_address": "proveedor@ejemplo.test",
        "subject": "Albaran obra",
        "attachment_filename": "albaran.pdf",
        "attachment_sha256": _sha(pdf),
        "attachment_content_type": "application/pdf",
        "attachment_size_bytes": len(pdf),
        "page_number": 1,
        "total_pages": 1,
        "page_sha256": _sha(pdf),
        "correo_adjunto_id": "c1",
        "correo_adjunto_nivel": 2,
    }]


def test_f054_r15_meta_de_una_imagen_interior():
    png = png_bytes(b"albaran-foto")
    eml = a_bytes(correo(adjuntos=[fichero_png("foto.png", datos=png)]))

    _, intake = _ciclo([_correo_adjunto("c7")], {"c7": eml})

    (envio,) = intake.envios
    assert envio.meta == {
        "email_message_id": "msg-1",
        "email_received_at_utc": "2026-09-23T08:00:00Z",
        "from_address": "proveedor@ejemplo.test",
        "subject": "Albaran obra",
        "attachment_filename": "foto.png",
        "attachment_sha256": _sha(png),
        "attachment_content_type": "image/png",
        "attachment_size_bytes": len(png),
        "page_number": 1,
        "total_pages": 1,
        "page_sha256": _sha(png),
        "correo_adjunto_id": "c7",
        "correo_adjunto_nivel": 1,
    }
    assert (envio.filename, envio.content_type) == ("foto.png", "image/png")


def test_f054_r16_en_un_correo_mixto_el_directo_no_lleva_las_claves_nuevas():
    _, intake = _ciclo([adjunto("a", "fuera.pdf"), _correo_adjunto()], {"a": pdf_de_paginas(1), "c1": _eml_bueno()})

    directo, interior = intake.envios
    assert "correo_adjunto_id" not in directo.meta and "correo_adjunto_nivel" not in directo.meta
    assert (interior.meta["correo_adjunto_id"], interior.meta["correo_adjunto_nivel"]) == ("c1", 1)


# --- R17 / R18 · contexto del exterior, pedido una vez -------------------- #
def test_f054_r17_r18_todas_las_paginas_llevan_el_contexto_del_exterior():
    eml = a_bytes(correo(adjuntos=[fichero_pdf("dentro.pdf", paginas=2), fichero_png("foto.png")]))
    contenido = contenido_inventado()

    buzon, intake = _ciclo(
        [adjunto("a", "fuera.pdf"), _correo_adjunto()], {"a": pdf_de_paginas(1), "c1": eml}, contenido=contenido
    )

    esperado = construir_contexto_correo(
        contenido.asunto, contenido.cuerpo_unico, recibido_utc="2026-09-23T08:00:00Z"
    )
    assert len(intake.envios) == 4
    assert {e.contexto_correo.sha256 for e in intake.envios} == {esperado.sha256}
    assert buzon.veces("get_contenido") == 1


def test_f054_r18_solo_un_correo_adjunto_tambien_pide_el_contexto_una_vez():
    buzon, intake = _ciclo([_correo_adjunto()], {"c1": _eml_bueno()})

    assert buzon.veces("get_contenido") == 1
    assert intake.envios[0].contexto_correo is not None


def test_f054_r18_sin_nada_elegible_no_se_pide_el_contexto():
    descartado = adjunto("c1", "RV: x", content_type="message/rfc822", odata_type=ITEM, inline=True)

    buzon, intake = _ciclo([descartado, adjunto("i", "logo.png", inline=True)], {})

    assert buzon.veces("get_contenido") == 0
    assert intake.envios == []


# --- R19 · mismo fichero directo y dentro -------------------------------- #
def test_f054_r19_el_mismo_fichero_directo_y_dentro_es_duplicado_no_fallo():
    pdf = pdf_de_paginas(1)
    eml = a_bytes(correo(adjuntos=[Fichero(datos=pdf, nombre="albaran.pdf")]))

    buzon, intake = _ciclo([adjunto("a", "albaran.pdf"), _correo_adjunto()], {"a": pdf, "c1": eml})

    assert len(intake.envios) == 2
    assert intake.claves[0] == intake.claves[1] == f"email:msg-1:{_sha(pdf)}"
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


# --- R20 · caso mixto en una pasada y en el orden de Graph ---------------- #
def test_f054_r20_mixto_en_el_orden_en_que_graph_lista_los_adjuntos():
    eml = a_bytes(correo(adjuntos=[fichero_pdf("b.pdf"), fichero_png("c.png")]))

    buzon, intake = _ciclo(
        [adjunto("a", "a.pdf"), _correo_adjunto(), adjunto("d", "d.pdf")],
        {"a": pdf_de_paginas(1), "c1": eml, "d": pdf_de_paginas(1)},
    )

    assert _nombres(intake) == ["a.pdf", "b.pdf", "c.png", "d.pdf"]
    assert [a for n, a in buzon.llamadas if n == "download_attachment_value"] == ["a", "c1", "d"]
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


# --- R21 · destino del correo exterior ------------------------------------ #
def _escenario_destino(nombre):
    directo_y_correo = [adjunto("a"), _correo_adjunto()]
    if nombre == "todo_bien":
        return directo_y_correo, {"a": pdf_de_paginas(1), "c1": _eml_bueno()}, None
    if nombre == "falla_descarga_correo":
        return directo_y_correo, {"a": pdf_de_paginas(1), "c1": RuntimeError("x")}, None
    if nombre == "correo_ilegible":
        return directo_y_correo, {"a": pdf_de_paginas(1), "c1": b""}, None
    if nombre == "tope_excedido":
        hondo = a_bytes(envolver(correo(adjuntos=[fichero_pdf()]), 5))
        return directo_y_correo, {"a": pdf_de_paginas(1), "c1": hondo}, None
    if nombre == "troceo_interior_falla":
        roto = a_bytes(correo(adjuntos=[Fichero(datos=b"%PDF-roto", nombre="roto.pdf")]))
        return directo_y_correo, {"a": pdf_de_paginas(1), "c1": roto}, None
    if nombre == "intake_falla_en_interior":
        return directo_y_correo, {"a": pdf_de_paginas(1), "c1": _eml_bueno()}, IntakeConDedup(fallar_en=frozenset({2}))
    if nombre == "intake_rechaza":
        return [_correo_adjunto()], {"c1": _eml_bueno()}, IntakeConDedup(rechazar=True)
    if nombre == "sin_pagina_aceptada":
        return [_correo_adjunto()], {"c1": a_bytes(correo(adjuntos=[fichero_texto()]))}, None
    assert nombre == "directo_falla"
    return directo_y_correo, {"a": RuntimeError("x"), "c1": _eml_bueno()}, None


@pytest.mark.parametrize(
    ("escenario", "destino"),
    [
        ("todo_bien", ID_PROCESADOS),
        ("falla_descarga_correo", ID_ERRORES),
        ("correo_ilegible", ID_ERRORES),
        ("tope_excedido", ID_ERRORES),
        ("troceo_interior_falla", ID_ERRORES),
        ("intake_falla_en_interior", ID_ERRORES),
        ("intake_rechaza", ID_ERRORES),
        ("sin_pagina_aceptada", ID_ERRORES),
        ("directo_falla", ID_ERRORES),
    ],
)
def test_f054_r21_procesados_si_y_solo_si_nada_falla_y_hay_pagina_aceptada(escenario, destino):
    adjuntos, ficheros, intake = _escenario_destino(escenario)

    buzon, _ = _ciclo(adjuntos, ficheros, intake=intake)

    assert buzon.movidos == [("msg-1", destino)]


def test_f054_r9_r21_tope_excedido_no_ingiere_ninguno_ni_los_de_niveles_bajos(caplog):
    hondo = envolver(correo(adjuntos=[fichero_png("hondo.png")]), 5)
    eml = a_bytes(correo(adjuntos=[fichero_pdf("arriba.pdf"), fichero_png("arriba.png"), hondo]))

    with caplog.at_level(logging.DEBUG):
        buzon, intake = _ciclo([adjunto("a", "fuera.pdf"), _correo_adjunto()], {"a": pdf_de_paginas(1), "c1": eml})

    assert _nombres(intake) == ["fuera.pdf"]
    assert buzon.movidos == [("msg-1", ID_ERRORES)]
    (error,) = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert "msg=msg-1" in error and "att=c1" in error and "tope=5" in error


# --- R22 · correo adjunto sin documento valido ---------------------------- #
def _eml_sin_documentos():
    return a_bytes(correo(adjuntos=[fichero_texto(), fichero_png("logo.png", disposicion="inline")]))


def test_f054_r22_sin_documento_junto_a_un_directo_va_a_procesados_con_warning(caplog):
    with caplog.at_level(logging.DEBUG):
        buzon, intake = _ciclo(
            [adjunto("a", "fuera.pdf"), _correo_adjunto()], {"a": pdf_de_paginas(1), "c1": _eml_sin_documentos()}
        )

    assert _nombres(intake) == ["fuera.pdf"]
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]
    avisos = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    (aviso,) = [m for m in avisos if "ningun documento" in m]
    assert "msg=msg-1" in aviso and "att=c1" in aviso and "partes_ignoradas=3" in aviso


def test_f054_r22_sin_documento_y_solo_el_va_a_errores():
    buzon, intake = _ciclo([_correo_adjunto()], {"c1": _eml_sin_documentos()})

    assert intake.envios == []
    assert buzon.movidos == [("msg-1", ID_ERRORES)]


# --- R23 · nada elegible -------------------------------------------------- #
def test_f054_r23_sin_directos_ni_correos_adjuntos_elegibles_va_a_errores(caplog):
    descartado = adjunto("c1", "RV: x", content_type="message/rfc822", odata_type=ITEM, inline=True)

    with caplog.at_level(logging.DEBUG):
        buzon, intake = _ciclo([descartado], {})

    assert buzon.movidos == [("msg-1", ID_ERRORES)]
    assert buzon.veces("get_contenido") == 0 and intake.envios == []
    (aviso,) = [r.getMessage() for r in caplog.records if "sin adjuntos elegibles" in r.getMessage()]
    assert "directos" in aviso and "correos adjuntos" in aviso


# --- R24 · un correo adjunto que falla no para a los demas --------------- #
@pytest.mark.parametrize("fallo", [RuntimeError("Graph 500"), b""], ids=["descarga", "vacio"])
def test_f054_r24_fallo_del_correo_adjunto_se_registra_y_sigue_con_los_demas(caplog, fallo):
    with caplog.at_level(logging.DEBUG):
        buzon, intake = _ciclo(
            [_correo_adjunto("c1"), _correo_adjunto("c2"), adjunto("d", "d.pdf")],
            {"c1": fallo, "c2": _eml_bueno(), "d": pdf_de_paginas(1)},
        )

    assert _nombres(intake) == ["dentro.pdf", "d.pdf"]
    assert buzon.movidos == [("msg-1", ID_ERRORES)]
    errores = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errores) == 1 and "msg=msg-1" in errores[0] and "att=c1" in errores[0]


# --- Supervivientes de la campana de mutacion (T10) ----------------------- #
def test_f054_r2_sin_limite_configurado_no_se_descarta_por_tamano():
    """Superviviente 2: ``max_bytes`` 0 es «sin limite», como en los directos."""
    buzon, intake = _ciclo([_correo_adjunto(size=10_000)], {"c1": _eml_bueno()}, max_bytes=0)

    assert _nombres(intake) == ["dentro.pdf"]
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f054_r21_el_log_final_cuenta_directos_correos_adjuntos_y_paginas(caplog):
    """Superviviente 1: el recuento del log final de destino."""
    eml = a_bytes(correo(adjuntos=[fichero_pdf("b.pdf", paginas=2)]))

    with caplog.at_level(logging.DEBUG):
        _ciclo(
            [adjunto("a", "a.pdf"), _correo_adjunto(), adjunto("d", "d.pdf")],
            {"a": pdf_de_paginas(1), "c1": eml, "d": pdf_de_paginas(1)},
        )

    (final,) = [r.getMessage() for r in caplog.records if "movido a" in r.getMessage()]
    assert final == "msg=msg-1 movido a Procesados (directos=2 correos_adjuntos=1 paginas_aceptadas=4)"
