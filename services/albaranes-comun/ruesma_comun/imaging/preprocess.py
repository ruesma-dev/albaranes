# ruesma_comun/imaging/preprocess.py
"""Preprocesado de imagen para la extraccion con IA.

Objetivo: mejorar la lectura de albaranes ESCANEADOS/fotografiados
(copias carbonicas azules/rosas, matricial tenue, manuscritos) ANTES de
mandarlos a la IA. NO toca los PDF con texto embebido (facturas
digitales): esos se mandan tal cual para no perder su capa de texto.

(jul 2026) Rediseno calibrado con albaranes reales problematicos
(Special Concrete rosa, Mostoles azul con calco severo del reverso,
Pinsacon azul manuscrito, Mahorsa matricial tenue):

  1. UNA IMAGEN POR PAGINA en vez de apilar las paginas en una tira
     JPEG. Las APIs de vision reescalan las imagenes grandes hacia
     abajo (p. ej. Anthropic a ~1568 px de lado largo); una tira de N
     paginas llegaba al modelo a una resolucion efectiva ridicula. Es
     LA mejora de mayor impacto. -> ``preparar_adjuntos_para_ia``.
  2. Cadena de realce nueva por pagina:
       canal -> deskew -> iluminacion -> (denoise opc.) -> estirado
       -> nitidez
     - Normalizacion de ILUMINACION (division por el fondo estimado
       con blur gaussiano grande): aplana sombras y ATENUA EL CALCO
       del reverso de las copias carbonicas. Es la segunda gran
       mejora.
     - ESTIRADO de niveles por percentiles: manda el fondo a blanco
       y el trazo a negro (remata el calco residual).
     - DESKEW conservador por lineas de tabla (Hough): solo rota si
       hay >=5 lineas casi-horizontales y el angulo mediano esta en
       [0.4, 7] grados. En documentos rectos se abstiene.
     - CLAHE SE RETIRA de la cadena: tras la normalizacion de
       iluminacion reintroducia el ruido de fondo que esta acababa de
       limpiar (verificado con las muestras). El realce local queda
       cubierto por iluminacion + estirado + unsharp.
     - DENOISE (mediana 3x3) OPCIONAL y por defecto APAGADO: en las
       muestras ablandaba el matricial de puntos sin aportar limpieza
       extra sobre la normalizacion.

Decision de diseno: vive en ruesma_comun para que sv2 (albaranes) y el
sistema de partes lo compartan. sv2 lo llama al construir los adjuntos
de la IA (fase 1 y fase 2 comparten adjuntos).

API:
  - ``preparar_adjuntos_para_ia(pdf_bytes, ...) -> list[(kind, mime, data)]``
    NUEVA. Una tupla por adjunto: [("pdf", ...)] si el PDF tiene texto
    embebido; [("image", ...), ...] (una por pagina) si es escaneado.
  - ``preparar_para_ia(pdf_bytes, ...) -> (kind, mime, data)``
    COMPATIBILIDAD (partes y llamantes antiguos): mismo contrato de
    siempre; si el PDF es escaneado, apila las paginas realzadas en
    una sola JPEG como antes. Preferir la nueva en codigo nuevo.

Deteccion de ESCANEADO por pagina (jul 2026, arreglo del detector
laxo): antes bastaba UN caracter de texto en UNA pagina para mandar
el documento entero como PDF crudo (escaneos con capa OCR, mixtos
digital+escaneo o sellos digitales sobre escaneo se colaban sin
realce). Ahora una pagina cuenta como ESCANEADA si una imagen cubre
>= _UMBRAL_COBERTURA_IMG de su superficie (independiente de la capa
OCR), y el documento va por la ruta de imagenes realzadas si tiene
alguna pagina escaneada o si ninguna pagina alcanza
_UMBRAL_TEXTO_PAGINA caracteres de texto real. Solo se respeta el
PDF tal cual cuando es genuinamente digital (texto real y ninguna
pagina-imagen).

``preparar_imagen_para_ia`` (jul 2026): las IMAGENES SUELTAS
(JPG/PNG de una foto de movil, el caso que MAS necesita realce)
pasan ahora por la misma cadena. Best-effort: formatos que OpenCV
no decodifica (HEIC...) se devuelven tal cual.

Es best-effort: ante cualquier fallo (o si PyMuPDF/OpenCV no estan)
devuelve el PDF crudo, sin romper el flujo.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Ancho objetivo de render (px). ~150-220 dpi para A4.
_DPI_RENDER = 200
# Lado largo maximo (px) de cada PAGINA; si se supera, se reescala.
_MAX_LADO_PX = 2400
# Maximo de paginas convertidas a imagen por documento.
_MAX_PAGINAS = 10
# Alto maximo (px) de la imagen APILADA (solo ruta de compatibilidad).
_MAX_ALTO_PX = 4200
# Calidad JPEG de salida.
_JPEG_QUALITY = 90
# Normalizacion de iluminacion: sigma del blur que estima el fondo.
_ILUM_SIGMA = 25.0
# Estirado de niveles: percentiles (negro, blanco) y separacion minima.
_ESTIRA_LO = 2.0
_ESTIRA_HI = 90.0
_ESTIRA_MIN_RANGO = 10.0
# Deskew conservador: minimo de lineas y rango de angulo aplicable.
_DESKEW_MIN_LINEAS = 5
_DESKEW_ANG_MIN = 0.4
_DESKEW_ANG_MAX = 7.0
# Nitidez (unsharp) final.
_UNSHARP_SIGMA = 1.2
_UNSHARP_PESO = 1.4
# Deteccion de pagina ESCANEADA (jul 2026): cobertura minima de una
# imagen sobre la superficie de la pagina, y minimo de caracteres de
# texto real para considerar una pagina "digital".
_UMBRAL_COBERTURA_IMG = 0.70
_UMBRAL_TEXTO_PAGINA = 150

Adjunto = Tuple[str, str, bytes]  # (kind, mime, data)


# --------------------------------------------------------------------- #
# API publica
# --------------------------------------------------------------------- #
def preparar_adjuntos_para_ia(
    pdf_bytes: bytes,
    *,
    activar: bool = True,
    dpi: int = _DPI_RENDER,
    iluminacion: bool = True,
    denoise: bool = False,
    deskew: bool = True,
    max_paginas: int = _MAX_PAGINAS,
) -> List[Adjunto]:
    """Devuelve la lista de (kind, mime, data) para los LlmAttachment.

    - Si ``activar`` es False -> [("pdf", "application/pdf", pdf_bytes)].
    - Si el PDF tiene TEXTO embebido -> se manda tal cual (PDF).
    - Si el PDF es ESCANEADO (sin texto) -> UNA imagen JPEG realzada
      POR PAGINA (hasta ``max_paginas``; el resto se descarta con
      warning: mas alla de ~10 paginas ya no es un albaran normal).
    - Ante cualquier error -> PDF crudo (best-effort).

    Flags de la cadena de realce (ver docstring del modulo):
    ``iluminacion`` (normalizacion + estirado), ``denoise`` (mediana
    3x3, default OFF), ``deskew`` (enderezado conservador).
    """
    if not activar or not pdf_bytes:
        return [("pdf", "application/pdf", pdf_bytes)]
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            # Deteccion por PAGINA (jul 2026): un PDF solo se respeta tal
            # cual si es genuinamente digital. Una capa OCR sobre un
            # escaneo NO lo convierte en digital (la pagina sigue siendo
            # una imagen que cubre la hoja) y una sola pagina escaneada
            # arrastra el documento entero a la ruta de imagenes (las
            # paginas digitales rasterizadas a 200 dpi siguen siendo
            # perfectamente legibles para la IA).
            hay_escaneada = any(
                _pagina_escaneada(p, cobertura_min=_UMBRAL_COBERTURA_IMG)
                for p in doc
            )
            hay_texto = any(
                len((p.get_text() or "").strip()) >= _UMBRAL_TEXTO_PAGINA
                for p in doc
            )
            if not hay_escaneada and hay_texto:
                logger.info(
                    "[preproceso] PDF digital (texto real y sin "
                    "paginas-imagen); se manda tal cual"
                )
                return [("pdf", "application/pdf", pdf_bytes)]
            logger.info(
                "[preproceso] ruta de imagenes: %s",
                "pagina(s) escaneada(s) detectada(s)" if hay_escaneada
                else "sin texto real en ninguna pagina",
            )

            total = len(doc)
            n = min(total, max(1, int(max_paginas)))
            if total > n:
                logger.warning(
                    "[preproceso] PDF de %s paginas; solo se mandan las "
                    "primeras %s",
                    total, n,
                )
            adjuntos: List[Adjunto] = []
            for i in range(n):
                pix = doc[i].get_pixmap(dpi=dpi)
                im = _mejorar_pixmap(
                    pix,
                    iluminacion=iluminacion,
                    denoise=denoise,
                    deskew=deskew,
                )
                jpeg = _a_jpeg(im)
                if jpeg is None:
                    return [("pdf", "application/pdf", pdf_bytes)]
                adjuntos.append(("image", "image/jpeg", jpeg))
            logger.info(
                "[preproceso] PDF escaneado -> %s imagen(es) realzada(s), "
                "%s bytes en total",
                len(adjuntos), sum(len(a[2]) for a in adjuntos),
            )
            return adjuntos
        finally:
            doc.close()
    except Exception as exc:  # noqa: BLE001 - best-effort
        logger.warning(
            "[preproceso] fallo (%s); se manda el PDF sin realzar", exc
        )
        return [("pdf", "application/pdf", pdf_bytes)]


def preparar_para_ia(
    pdf_bytes: bytes,
    *,
    activar: bool = True,
    dpi: int = _DPI_RENDER,
) -> Adjunto:
    """COMPATIBILIDAD: contrato clasico de UN solo adjunto.

    Igual que siempre: PDF con texto -> PDF tal cual; escaneado ->
    paginas realzadas apiladas en UNA JPEG (con la cadena de realce
    nueva). Los llamantes nuevos deben usar
    ``preparar_adjuntos_para_ia`` (una imagen por pagina rinde mucho
    mejor con las APIs de vision).
    """
    adjuntos = preparar_adjuntos_para_ia(
        pdf_bytes, activar=activar, dpi=dpi
    )
    if len(adjuntos) == 1:
        return adjuntos[0]
    try:
        apilada = _apilar_jpegs([a[2] for a in adjuntos])
        if apilada is not None:
            return "image", "image/jpeg", apilada
    except Exception as exc:  # noqa: BLE001 - best-effort
        logger.warning("[preproceso] fallo apilando (%s)", exc)
    return "pdf", "application/pdf", pdf_bytes


def preparar_imagen_para_ia(
    img_bytes: bytes,
    mime_type: str | None = None,
    *,
    activar: bool = True,
    iluminacion: bool = True,
    denoise: bool = False,
    deskew: bool = True,
) -> Adjunto:
    """Realza una IMAGEN SUELTA (JPG/PNG de una foto de movil) con la
    MISMA cadena que las paginas escaneadas de un PDF (jul 2026).

    Devuelve ("image", mime, data). Best-effort: si ``activar`` es
    False, la imagen no se puede decodificar (HEIC...) o algo falla,
    devuelve los bytes originales con su mime.
    """
    mime_original = mime_type or "image/jpeg"
    if not activar or not img_bytes:
        return ("image", mime_original, img_bytes)
    try:
        import cv2
        import numpy as np

        arr = cv2.imdecode(
            np.frombuffer(img_bytes, dtype=np.uint8), cv2.IMREAD_COLOR
        )
        if arr is None:
            raise ValueError("formato de imagen no soportado por OpenCV")
        # OpenCV decodifica en BGR; _seleccionar_canal asume RGB (canal
        # 0 = rojo, el bueno para copias carbonicas azules/rosas).
        rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        gris = _seleccionar_canal(rgb)
        gris = _realzar_gris(
            gris,
            iluminacion=iluminacion,
            denoise=denoise,
            deskew=deskew,
        )
        jpeg = _a_jpeg(gris)
        if jpeg is None:
            raise ValueError("no se pudo codificar el JPEG")
        logger.info(
            "[preproceso] imagen suelta realzada: %s -> %s bytes",
            len(img_bytes), len(jpeg),
        )
        return ("image", "image/jpeg", jpeg)
    except Exception as exc:  # noqa: BLE001 - best-effort
        logger.warning(
            "[preproceso] imagen suelta sin realzar (%s)", exc
        )
        return ("image", mime_original, img_bytes)


# --------------------------------------------------------------------- #
# Cadena de realce por pagina
# --------------------------------------------------------------------- #
def _pagina_escaneada(page, *, cobertura_min: float) -> bool:
    """True si alguna imagen de la pagina cubre >= ``cobertura_min`` de
    su superficie (tipico de un escaneo, con o sin capa OCR)."""
    try:
        rect = page.rect
        area_pagina = float(abs(rect.width * rect.height)) or 1.0
        mejor = 0.0
        for img in page.get_images(full=True):
            xref = img[0]
            for r in page.get_image_rects(xref):
                area = float(abs(r.width * r.height))
                mejor = max(mejor, area / area_pagina)
                if mejor >= cobertura_min:
                    return True
        return mejor >= cobertura_min
    except Exception as exc:  # noqa: BLE001 - best-effort
        logger.warning(
            "[preproceso] deteccion de pagina escaneada fallo (%s)", exc
        )
        return False


def _mejorar_pixmap(pix, *, iluminacion: bool, denoise: bool, deskew: bool):
    """pixmap de PyMuPDF -> ndarray gris realzado (uint8)."""
    import numpy as np

    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n
    )
    gris = _seleccionar_canal(arr)
    return _realzar_gris(
        gris,
        iluminacion=iluminacion,
        denoise=denoise,
        deskew=deskew,
    )


def _realzar_gris(gris, *, iluminacion: bool, denoise: bool, deskew: bool):
    """Cadena de realce COMPARTIDA (jul 2026): paginas de PDF escaneado
    e imagenes sueltas pasan exactamente por el mismo camino:
    deskew -> iluminacion -> (denoise) -> estirado -> nitidez -> cap."""
    import cv2

    if deskew:
        gris = _enderezar(gris)
    if iluminacion:
        gris = _normalizar_iluminacion(gris)
    if denoise:
        gris = cv2.medianBlur(gris, 3)
    if iluminacion:
        gris = _estirar_niveles(gris)

    # Nitidez suave (unsharp) para reforzar el trazo del manuscrito.
    blur = cv2.GaussianBlur(gris, (0, 0), sigmaX=_UNSHARP_SIGMA)
    gris = cv2.addWeighted(
        gris, _UNSHARP_PESO, blur, 1.0 - _UNSHARP_PESO, 0
    )

    # Cap del lado largo POR PAGINA/IMAGEN.
    lado = max(gris.shape[:2])
    if lado > _MAX_LADO_PX:
        escala = _MAX_LADO_PX / lado
        gris = cv2.resize(
            gris,
            (int(gris.shape[1] * escala), int(gris.shape[0] * escala)),
            interpolation=cv2.INTER_AREA,
        )
    return gris


def _seleccionar_canal(arr):
    """RGB -> gris. En copias carbonicas (azules/rosas) el canal ROJO
    suele dar mas contraste del trazo; se elige el de mayor dispersion."""
    import cv2

    if arr.shape[2] >= 3:
        rojo = arr[:, :, 0]  # PyMuPDF entrega RGB.
        gris_std = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2GRAY)
        return (rojo if rojo.std() >= gris_std.std() else gris_std).copy()
    return arr[:, :, 0].copy()


def _enderezar(gris):
    """Deskew CONSERVADOR: angulo mediano de las lineas casi-horizontales
    (las lineas de tabla de los albaranes). Solo rota con senal clara y
    angulo pequeno; ante la duda devuelve la imagen tal cual."""
    import cv2
    import numpy as np

    try:
        edges = cv2.Canny(gris, 60, 180)
        lineas = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 360,
            threshold=120,
            minLineLength=max(80, gris.shape[1] // 4),
            maxLineGap=8,
        )
        if lineas is None:
            return gris
        angulos = []
        for x1, y1, x2, y2 in lineas[:, 0]:
            a = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if abs(a) <= 10.0:
                angulos.append(a)
        if len(angulos) < _DESKEW_MIN_LINEAS:
            return gris
        angulo = float(np.median(angulos))
        if not (_DESKEW_ANG_MIN <= abs(angulo) <= _DESKEW_ANG_MAX):
            return gris
        alto, ancho = gris.shape[:2]
        m = cv2.getRotationMatrix2D((ancho / 2.0, alto / 2.0), angulo, 1.0)
        logger.info("[preproceso] deskew %.2f grados", angulo)
        return cv2.warpAffine(
            gris,
            m,
            (ancho, alto),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255,
        )
    except Exception as exc:  # noqa: BLE001 - best-effort
        logger.warning("[preproceso] deskew fallo (%s); sin rotar", exc)
        return gris


def _normalizar_iluminacion(gris):
    """Division por el fondo estimado (blur gaussiano grande): aplana
    sombras/vineteo y atenua el calco del reverso de los carbonicos."""
    import cv2
    import numpy as np

    fondo = cv2.GaussianBlur(gris, (0, 0), sigmaX=_ILUM_SIGMA)
    norm = cv2.divide(gris, fondo, scale=255)
    return np.clip(norm, 0, 255).astype(np.uint8)


def _estirar_niveles(gris):
    """Estirado por percentiles: p_lo -> negro, p_hi -> blanco. Tras la
    normalizacion el fondo queda ~blanco, asi que saturar por encima de
    p_hi remata el calco residual sin tocar el trazo."""
    import numpy as np

    p_lo = float(np.percentile(gris, _ESTIRA_LO))
    p_hi = float(np.percentile(gris, _ESTIRA_HI))
    # Guardas: rango minimo y punto blanco no patologicamente bajo.
    if p_hi - p_lo < _ESTIRA_MIN_RANGO:
        return gris
    p_hi = max(p_hi, p_lo + 60.0)
    out = (gris.astype(np.float32) - p_lo) * (255.0 / (p_hi - p_lo))
    return np.clip(out, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------- #
# Codificacion / apilado (compatibilidad)
# --------------------------------------------------------------------- #
def _a_jpeg(imagen):
    import cv2

    ok, buf = cv2.imencode(
        ".jpg", imagen, [int(cv2.IMWRITE_JPEG_QUALITY), _JPEG_QUALITY]
    )
    return buf.tobytes() if ok else None


def _apilar_jpegs(jpegs):
    """Apila verticalmente varias JPEG en una (solo ruta de compat)."""
    import cv2
    import numpy as np

    imagenes = [
        cv2.imdecode(np.frombuffer(j, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        for j in jpegs
    ]
    imagenes = [im for im in imagenes if im is not None]
    if not imagenes:
        return None
    ancho = min(im.shape[1] for im in imagenes)
    norm = [
        (
            im
            if im.shape[1] == ancho
            else cv2.resize(
                im,
                (ancho, int(im.shape[0] * ancho / im.shape[1])),
                interpolation=cv2.INTER_AREA,
            )
        )
        for im in imagenes
    ]
    combinada = norm[0] if len(norm) == 1 else np.vstack(norm)
    if combinada.shape[0] > _MAX_ALTO_PX:
        escala = _MAX_ALTO_PX / combinada.shape[0]
        combinada = cv2.resize(
            combinada,
            (int(combinada.shape[1] * escala), _MAX_ALTO_PX),
            interpolation=cv2.INTER_AREA,
        )
    return _a_jpeg(combinada)
