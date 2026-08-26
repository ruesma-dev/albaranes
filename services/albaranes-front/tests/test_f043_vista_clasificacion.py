# tests/test_f043_vista_clasificacion.py
"""F-043 · R30: lo que decidio IA1, el revisor lo VE.

sv3 persiste en ``albaran_documents_merge`` seis columnas nuevas
(``tipologia``, ``tipologia_confianza_pct``, ``tipologia_motivo``,
``tipologia_origen``, ``tipologia_mixta``,
``tipologia_secundarias_json``) y sella tres motivos de revision nuevos
(``clasificacion_confianza_baja``, ``clasificacion_mixta``,
``clasificacion_ausente``) mas uno por linea
(``linea_sin_familia_en_albaran_mixto:N``).

Hasta esta tarea nadie los leia: era exactamente el agujero de F-036 R23
—el dato existe en BBDD y el revisor tiene que abrir psql para verlo— y
aqui duele mas, porque la familia decide QUE PRECIO se aplica.

**sv4 PINTA, no decide.** No hay en este servicio una sola regla que
infiera, corrija o complete la familia por codigo LER, designacion de
producto, palabras clave ni CIF: eso es el lazo cerrado que F-043 existe
para desmontar (R12, R13). Varios tests de aqui abajo lo fijan por
inspeccion, para que no vuelva a entrar por la puerta del front.

Sin red, sin BBDD real y sin LLM (R33): modelos Pydantic y Jinja2 sobre
las plantillas reales del servicio.
"""
from __future__ import annotations

import json

import pytest
from ruesma_comun.contratos import ClasificacionAlbaran

MOTIVO_CONFIANZA_BAJA = "clasificacion_confianza_baja"
MOTIVO_MIXTA = "clasificacion_mixta"
MOTIVO_AUSENTE = "clasificacion_ausente"
MOTIVO_LINEA_SIN_FAMILIA = "linea_sin_familia_en_albaran_mixto:3"

#: Los nombres EXACTOS de las seis columnas que escribe sv3
#: (``campos_clasificacion_merge`` en
#: ``services/albaranes-persistencia/infrastructure/database/
#: sqlalchemy_albaran_repository.py``). Se fijan aqui como literal
#: porque sv4 no puede importar de sv3: los dos servicios tienen un
#: paquete ``infrastructure`` de primer nivel y en un mismo proceso uno
#: tapa al otro.
COLUMNAS_SV3 = (
    "tipologia",
    "tipologia_confianza_pct",
    "tipologia_motivo",
    "tipologia_origen",
    "tipologia_mixta",
    "tipologia_secundarias_json",
)

MOTIVO_IA = (
    "Gestor autorizado de residuos en el membrete, codigos LER 170504 "
    "y 170604 en las lineas y retirada de contenedor de 6 m3."
)


def _columnas_clasificacion(**cambios):
    """Las seis columnas del merge tal cual las dejaria sv3."""
    base = {
        "tipologia": "residuos",
        "tipologia_confianza_pct": 82.0,
        "tipologia_motivo": MOTIVO_IA,
        "tipologia_origen": "ia1",
        "tipologia_mixta": False,
        "tipologia_secundarias_json": json.dumps([], ensure_ascii=False),
    }
    base.update(cambios)
    return base


def _payload(**campos):
    """``DocumentDetailPayload`` minimo, con las seis columnas puestas."""
    from domain.models.review_models import DocumentDetailPayload

    base = {
        "id": "f043-doc-0000-0000-000000003967",
        "source_filename": "SS-0003967.pdf",
        "provider_origin": "merge",
        "model_name": "—",
        "created_at_utc": "2026-08-26T10:00:00Z",
    }
    base.update(_columnas_clasificacion())
    base.update(campos)
    return DocumentDetailPayload(**base)


# ------------------------------------------------------------------ #
# R30 · el modelo de vista expone la clasificacion
# ------------------------------------------------------------------ #
def test_f043_r30_el_payload_monta_la_clasificacion_desde_las_seis_columnas():
    """Inverso exacto de ``campos_clasificacion_merge`` de sv3."""
    documento = _payload(
        tipologia_mixta=True,
        tipologia_secundarias_json=json.dumps(["hormigon"], ensure_ascii=False),
    )

    clasificacion = documento.clasificacion

    assert isinstance(clasificacion, ClasificacionAlbaran)
    assert clasificacion.familia == "residuos"
    assert clasificacion.confianza_pct == 82.0
    assert clasificacion.motivo == MOTIVO_IA
    assert clasificacion.origen == "ia1"
    assert clasificacion.mixto is True
    assert clasificacion.familias_secundarias == ["hormigon"]


def test_f043_r30_un_documento_anterior_a_f043_no_tiene_clasificacion():
    """Las seis columnas a NULL ⇒ ``None``, no un ``generico`` inventado.

    Es la mitad sv4 de R27, y el mismo criterio que sv5 aplica en
    ``_build_clasificacion``: fabricar aqui una familia que nadie tomo
    haria que el revisor viera una decision de IA donde no la hubo.
    """
    documento = _payload(**dict.fromkeys(COLUMNAS_SV3, None))

    assert documento.clasificacion is None


def test_f043_r30_los_seis_campos_se_llaman_como_las_columnas_de_sv3():
    """Si sv3 renombra una columna, este test cae en vez de la ficha."""
    from domain.models.review_models import DocumentDetailPayload

    campos = DocumentDetailPayload.model_fields
    for columna in COLUMNAS_SV3:
        assert columna in campos, f"el payload no expone {columna}"


def test_f043_r30_el_orm_del_merge_declara_las_seis_columnas():
    """Sin esto el SELECT del ORM no las trae y el payload va vacio."""
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    columnas = set(AlbaranDocumentMergeOrm.__table__.columns.keys())
    for columna in COLUMNAS_SV3:
        assert columna in columnas, f"el ORM de sv4 no declara {columna}"


def test_f043_r30_sv4_no_escribe_ddl_de_las_columnas_de_sv3():
    """sv3 es el dueno del schema: sv4 solo LEE estas seis columnas.

    Los ALTER defensivos de ``_review_schema_statements`` existen para
    las columnas que sv4 ESCRIBE (``approved``, el soft-delete...). Si
    sv4 declarase aqui su propio ALTER con sus propias longitudes, una
    base creada por sv3 y otra parcheada por sv4 acabarian con schemas
    distintos segun por donde entro el sistema — el mismo riesgo que el
    bloque C dejo cazado entre el ORM y el DDL de sv3.
    """
    from infrastructure.database.review_repository import (
        AlbaranReviewRepository,
    )

    ddl = " ".join(AlbaranReviewRepository._review_schema_statements())
    assert "tipologia" not in ddl


# ------------------------------------------------------------------ #
# R30 · el dato de BBDD no puede tumbar la ficha
# ------------------------------------------------------------------ #
def test_f043_r30_secundarias_ilegibles_no_rompen_la_clasificacion():
    """Basura en una columna informativa no puede costar la ficha entera.

    Mismo criterio defensivo que ``motivos_de_json`` (F-036 R23) y que
    el ``_lista_json`` de sv5: la familia, la confianza y el motivo —lo
    que el revisor necesita— se conservan.
    """
    documento = _payload(tipologia_secundarias_json="{esto no es JSON")

    clasificacion = documento.clasificacion

    assert clasificacion is not None
    assert clasificacion.familia == "residuos"
    assert clasificacion.familias_secundarias == []


def test_f043_r30_una_confianza_fuera_de_rango_no_rompe_la_ficha():
    """``ClasificacionAlbaran`` acota 0..100; la columna es un DOUBLE.

    Un valor imposible en BBDD haria saltar la validacion de Pydantic al
    montar el payload y el revisor no podria ni ABRIR el documento. Se
    recorta al rango, como sv3 recorta ``tipologia`` a VARCHAR(32).
    """
    documento = _payload(tipologia_confianza_pct=150.0)

    assert documento.clasificacion is not None
    assert documento.clasificacion.confianza_pct == 100.0

    documento = _payload(tipologia_confianza_pct=-5.0)

    assert documento.clasificacion is not None
    assert documento.clasificacion.confianza_pct == 0.0


def test_f043_r30_sin_motivo_ni_origen_la_clasificacion_sigue_viva():
    """La familia es lo que decide el precio: no se pierde por un NULL."""
    documento = _payload(tipologia_motivo=None, tipologia_origen=None)

    clasificacion = documento.clasificacion

    assert clasificacion is not None
    assert clasificacion.familia == "residuos"
    assert clasificacion.motivo == ""
    assert clasificacion.origen == "ia1"


# ------------------------------------------------------------------ #
# R30 · el nombre de la familia sale del CATALOGO, no de una copia
# ------------------------------------------------------------------ #
def test_f043_r30_el_nombre_legible_sale_del_catalogo_compartido():
    """sv4 no mantiene lista propia de familias (R2).

    Dos listas divergen siempre: es la trampa de F-023 que esta feature
    existe para cerrar.
    """
    from ruesma_comun.contratos.familias import obtener

    documento = _payload()

    assert documento.clasificacion_nombre == obtener("residuos").nombre


def test_f043_r30_una_familia_fuera_del_catalogo_se_ensena_tal_cual():
    """No se traduce ni se corrige lo que no esta en el catalogo.

    sv2 ya normaliza a ``generico`` lo que la IA se invente (R10). Si
    aun asi llegara aqui una etiqueta desconocida, el revisor tiene que
    VERLA: taparla con 'generico' seria decidir, y sv4 no decide.
    """
    documento = _payload(tipologia="pladur")

    assert documento.clasificacion_nombre == "pladur"


def test_f043_r13_sv4_no_infiere_la_familia_de_ninguna_senal():
    """Test de no-regresion de la PROHIBICION (R13), por inspeccion.

    El front es el sitio mas tentador para 'arreglar' una clasificacion
    mala con un ``if``: tiene delante el LER, el producto y el CIF. Si
    alguien lo intenta, este test cae.
    """
    import inspect

    from domain.models import review_models

    fuente = inspect.getsource(review_models)
    for prohibido in ("ler", "codigo_ler", "hormigon", "mortero", "cif_"):
        assert f"def {prohibido}" not in fuente
    assert "from ruesma_comun.ler" not in fuente
    assert "import ler" not in fuente


# ------------------------------------------------------------------ #
# R30 · la DUDA la sella sv3, sv4 no aplica el umbral
# ------------------------------------------------------------------ #
def test_f043_r30_la_duda_viene_de_los_motivos_que_sello_sv3():
    """El umbral (defecto 60) vive en sv3, que es quien lo aplica."""
    documento = _payload(
        review_reasons_json=json.dumps([MOTIVO_CONFIANZA_BAJA]),
    )

    assert documento.clasificacion_en_duda is True


def test_f043_r30_sv4_no_aplica_el_umbral_por_su_cuenta():
    """Confianza bajisima pero sin motivo de sv3 ⇒ sv4 NO marca duda.

    Parece contraintuitivo y es deliberado: si sv4 tuviera su propio
    umbral, el numero viviria en dos sitios y el dia que el humano
    cambie el de sv3 la ficha diria una cosa y la BBDD otra (F-023).
    """
    documento = _payload(tipologia_confianza_pct=5.0, review_reasons_json=None)

    assert documento.clasificacion_en_duda is False


@pytest.mark.parametrize(
    "motivo",
    [MOTIVO_CONFIANZA_BAJA, MOTIVO_MIXTA, MOTIVO_AUSENTE],
)
def test_f043_r30_los_tres_motivos_de_sv3_marcan_duda(motivo):
    documento = _payload(review_reasons_json=json.dumps([motivo]))

    assert documento.clasificacion_en_duda is True


def test_f043_r30_un_motivo_ajeno_a_la_clasificacion_no_marca_duda():
    documento = _payload(review_reasons_json=json.dumps(["obra_no_resuelta"]))

    assert documento.clasificacion_en_duda is False


# ------------------------------------------------------------------ #
# R30 · el lector del merge lleva las columnas al payload
# ------------------------------------------------------------------ #
def _orm_merge(**cambios):
    """Instancia TRANSITORIA del ORM del merge (sin sesion ni BBDD)."""
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    campos = {
        "id": "f043-doc-0000-0000-000000003967",
        "provider_origin": "merge",
        "source_filename": "SS-0003967.pdf",
        "source_mime_type": "application/pdf",
        "source_sha256": "0" * 64,
        "prompt_key": "albaran_factura_es",
        "schema_name": "documento_albaran",
        "model_name": "gpt-4.1",
        "raw_extraction_json": "{}",
        "created_at_utc": "2026-08-26T10:00:00Z",
        "approved": False,
    }
    campos.update(_columnas_clasificacion())
    campos.update(cambios)
    return AlbaranDocumentMergeOrm(**campos)


def test_f043_r30_el_lector_del_merge_lleva_las_seis_columnas_al_payload(
    repositorio,
):
    """De la fila del merge a lo que ve el revisor, sin BBDD de por medio."""
    detalle = repositorio._build_merge_detail(
        merge_doc=_orm_merge(),
        available_views=["merge"],
        provider_snapshots=[],
        contratos=[],
        selected_contrato_codigo=None,
    )

    assert detalle.clasificacion is not None
    assert detalle.clasificacion.familia == "residuos"
    assert detalle.clasificacion.confianza_pct == 82.0
    assert detalle.clasificacion.motivo == MOTIVO_IA


def test_f043_r30_la_vista_cruda_de_un_proveedor_no_trae_clasificacion(
    repositorio,
):
    """La clasificacion es del MERGE, y ahi es donde se ensena.

    Las vistas por proveedor son trazabilidad de la extraccion cruda:
    ahi no hay clasificacion resuelta, igual que no hay motivos de
    revision ni confianza calculada.
    """
    from infrastructure.database.orm_models import AlbaranDocumentBaseOrm

    provider_doc = AlbaranDocumentBaseOrm(
        id="f043-openai-0000-0000-00000003967",
        provider_origin="openai",
        source_filename="SS-0003967.pdf",
        source_sha256="0" * 64,
        model_name="gpt-4.1",
        raw_extraction_json="{}",
        created_at_utc="2026-08-26T10:00:00Z",
    )

    detalle = repositorio._build_provider_detail(
        merge_doc=_orm_merge(),
        provider_doc=provider_doc,
        provider_lines=[],
        available_views=["merge", "openai"],
        provider_snapshots=[],
        view_mode="openai",
        contratos=[],
        selected_contrato_codigo=None,
    )

    assert detalle.clasificacion is None


# ------------------------------------------------------------------ #
# R30 · la FICHA lo pinta (Jinja2 sobre la plantilla real)
# ------------------------------------------------------------------ #
def test_f043_r30_la_ficha_pinta_familia_confianza_y_motivo(
    render_detalle, documento_detalle
):
    """Las tres cosas que R30 exige, en la ficha del documento."""
    html = render_detalle(documento_detalle(clasificacion=_columnas_clasificacion()))

    assert "Clasificación" in html
    assert "Residuos / gestion de RCD" in html
    assert "residuos" in html
    assert "82" in html
    assert "codigos LER 170504" in html


def test_f043_r30_sin_clasificacion_no_se_pinta_el_bloque(
    render_detalle, documento_detalle
):
    """Un documento anterior a F-043 no ensena un bloque vacio."""
    html = render_detalle(documento_detalle())

    assert "Clasificación del albarán" not in html


def test_f043_r30_el_albaran_mixto_se_ve_marcado(
    render_detalle, documento_detalle
):
    """Mixto ⇒ las lineas sin familia NO heredan (R19), y eso se ve."""
    html = render_detalle(
        documento_detalle(
            clasificacion=_columnas_clasificacion(
                tipologia_mixta=True,
                tipologia_secundarias_json=json.dumps(["hormigon"]),
            ),
            motivos_documento=[MOTIVO_MIXTA, MOTIVO_LINEA_SIN_FAMILIA],
        )
    )

    assert "mixto" in html.lower()
    assert "hormigon" in html


def test_f043_r30_los_motivos_nuevos_salen_en_el_bloque_de_f036(
    render_detalle, documento_detalle
):
    """Los cuatro motivos nuevos usan el bloque que ya existe (F-036 R23)."""
    motivos = [
        MOTIVO_CONFIANZA_BAJA,
        MOTIVO_MIXTA,
        MOTIVO_AUSENTE,
        MOTIVO_LINEA_SIN_FAMILIA,
    ]
    html = render_detalle(
        documento_detalle(
            clasificacion=_columnas_clasificacion(),
            motivos_documento=motivos,
        )
    )

    assert "Motivos de revisión" in html
    for motivo in motivos:
        assert motivo in html


def test_f043_r30_la_clasificacion_en_duda_se_ensena_como_aviso(
    render_detalle, documento_detalle
):
    """Confianza baja: el revisor tiene que notar que hay que mirarlo."""
    html_duda = render_detalle(
        documento_detalle(
            clasificacion=_columnas_clasificacion(tipologia_confianza_pct=35.0),
            motivos_documento=[MOTIVO_CONFIANZA_BAJA],
        )
    )
    html_solida = render_detalle(
        documento_detalle(clasificacion=_columnas_clasificacion())
    )

    assert "clasificacion-duda" in html_duda
    assert "clasificacion-duda" not in html_solida


def test_f043_r30_el_motivo_de_la_ia_se_escapa_como_texto(
    render_detalle, documento_detalle
):
    """El motivo lo escribe un LLM: entra en el HTML como TEXTO.

    Jinja2 autoescapa, y esta ficha se la come el revisor entera: un
    motivo con markup no puede inyectar nada en la pagina.
    """
    html = render_detalle(
        documento_detalle(
            clasificacion=_columnas_clasificacion(
                tipologia_motivo="<script>alert(1)</script>",
            )
        )
    )

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
