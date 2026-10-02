# Exploración · sv1 y los «correos encadenados con el PDF al final» (2026-09-30)

Solo lectura. Rutas relativas a `albaranes/services/albaranes-email` (sv1A) y
`partes/services/partes-email` (sv1P) salvo que se diga otra cosa.

## 0. Qué es «encadenado» y qué versión de partes manda

- En partes es **F-020** («correos adjuntos (message/rfc822) encadenados hasta
  el PDF»): el escáner manda un correo cuyo único adjunto es **otro correo**
  (`itemAttachment`, `contentType message/rfc822`) que lleva el PDF dentro,
  con anidamiento posible. Spec: `partes/specs/F-020-correo-adjunto-escaner/`;
  sonda real en `partes/progress/explore_F-020_sonda.md`.
- **Versión vigente: el monorepo `partes`, rama `dev`.** F-020 se fusionó hoy
  (`f5219aa`, 2026-09-30) y **NO está en `main`** (`49f80fd`) ni desplegado
  (pendiente en `e392e8e`). El repo archivado `partes-email` (último commit
  2026-08-13 «Archivado…») descarta los itemAttachment
  (`partes-email/application/pipelines/polling_pipeline.py:51`): no lo hace.
- Otra lectura posible de «encadenado» —un `RV:` normal con el PDF como
  `fileAttachment`— **ya funciona hoy en sv1A** (es un adjunto de fichero).

## 1. Selección de correos: idéntica en los dos

- sv1A `infrastructure/graph/mail_client.py:150-212`; sv1P
  `infrastructure/graph/mail_client.py:189-252`. Mismo `$filter`:
  `isRead eq false and hasAttachments eq true`, `$top`, orden por
  `receivedDateTime desc`, carpeta origen; reintento sin filtro y re-filtrado
  en cliente (A:194-197). sv1P añade `bodyPreview` al `$select` (P:199).
- Un correo cuyo único adjunto es un itemAttachment **sí pasa el filtro**
  (`hasAttachments=true`): la sonda de partes encontró los 4 correos del
  escáner… en `Errores`. El filtro no es el problema.

## 2. Obtención de PDF

| Mecanismo | sv1A (albaranes) | sv1P (partes, dev) |
|---|---|---|
| fileAttachment directo | sí, **cualquier tipo** (A pipeline:405-422) | PDF/imagen (P pipeline:630-668) |
| itemAttachment `message/rfc822` → `GET …/attachments/{id}/$value` (MIME) | **descartado** (A pipeline:58-61, 411) | **sí** (P pipeline:226-233, 318-427) |
| fileAttachment `.eml` (`message/rfc822`) | pasa como fichero opaco a sv2 (splitter no-PDF, `pdf_page_splitter.py:35-45`) | abierto como correo (R1 de F-020, P:701-703) |
| `.msg` (vnd.ms-outlook) | pasa opaco a sv2 | descartado (tipo no soportado) |
| `$expand=…itemattachment/item` | no | no (usa `$value`, más simple) |
| inline | descartado (A:409) | descartado |
| referenceAttachment (enlace OneDrive/SP) | descartado (A:58-61) | descartado con log (P:611-617) |
| mensajes previos del hilo (`conversationId`) | no | no |

**El mecanismo exacto de partes**: clasificar el adjunto por `contentType ==
message/rfc822` (sin mayúsculas, item o file, no reference; P:606-628),
descargarlo con el **mismo** `download_attachment_value` que ya tiene sv1A
(A mail_client:253-269 ≡ P:293-309) y recorrer el MIME con la stdlib
`email` en `infrastructure/document/mime_pdf_extractor.py` (puro, sin red):
recursión propia por niveles (P ext:98-142), tope 5 niveles con «todo o
nada» (ext:41-42, 112-114; pipeline:365-374), PDF = `application/pdf` o
`.pdf` (ext:126-131), cabeceras Subject/From/Date truncadas a 200
(ext:159-187). Cada PDF interior sigue el camino del directo (troceo por
página) y su contexto lleva `embedded_in` (P pipeline:412-423, 601-602).
Límite de tamaño sobre el `size` de Graph del item y otra vez por PDF
interior (P:376-391). Destino: Procesados sii nada falló y entró ≥1
documento (P:259-261); correo adjunto sin PDF = WARNING, no fallo (P:393-402).
Datos de la sonda: el `Content-Type` HTTP del `$value` es `text/plain` (no
sirve para decidir); `@odata.type` ya llega con el `$select` actual; el
listado de sv1A lo guarda en `odata_type` (A mail_client:244-248).

**Lo que le falta a sv1A**: exactamente eso — la rama de clasificación
«correo adjunto» y el extractor MIME. El cliente Graph no necesita cambios.

## 3. Qué hace hoy sv1A con un correo así

`_process_message` (A pipeline:198-215): lista adjuntos, `_is_eligible`
descarta el itemAttachment por `odata_type` (A:411), `eligible` queda vacío →
WARNING «sin adjuntos elegibles» → **se mueve a `Errores`** (A:204-215), sin
pedir contenido ni encolar. No se marca leído explícitamente (el move lo
saca de la carpeta origen; queda no leído en `Errores`, igual que vio la
sonda de partes). Si el itemAttachment viene **junto a** un PDF directo, se
ignora en silencio y el correo va a `Procesados` (A:231-238): se pierde el
PDF interior sin rastro. Los que ya están en `Errores` no se reprocesan
solos: hay que devolverlos a la carpeta origen tras desplegar.

## 4. Encaje con F-048 (blob `input/{id}.correo.json`)

- Hoy el contexto es asunto + `uniqueBody` del mensaje **exterior**, UNA vez
  por mensaje y el mismo para todas las páginas de todos los adjuntos
  (A pipeline:217-219, 363-403; `ruesma_comun/correo/contexto.py:97-119`).
- En un correo con correo adjunto: el exterior es quien lo reenvía (a menudo
  jefe de obra o administración: su nota puede traer la obra); el interior es
  el del proveedor (su asunto suele traer el nº de albarán). **Propuesta
  mínima**: mantener el contexto del exterior sin tocar el contrato
  (`ContextoCorreo`, `VERSION_CONTEXTO=1`, contexto.py:50, 67-78). Fase 2
  opcional: añadir al contexto las cabeceras del interior (subject/sender/
  date, como `embedded_in` de partes); `extra="ignore"` (contexto.py:70)
  hace tolerante la lectura, pero `render_bloque_correo`
  (`ruesma_comun/correo/prompt.py:63-80`) y la huella tendrían que cambiar →
  toca sv2 y los evals: decisión del humano. El **cuerpo** del interior no
  (sería meter texto citado por la puerta de atrás, contra F-048 R3).
- Aviso: en un `RV:` normal (sin adjuntar como correo) el texto del
  proveedor está en la parte citada y `uniqueBody` lo excluye por diseño
  (A mail_client:293-297). No es de esta feature, pero es la misma queja.
- **Duplicados**: la clave es `email:{message_id}:{page_sha256}`
  (`infrastructure/colas/intake_cola_adapter.py:69-71`), con `message_id`
  del exterior. Mismo PDF directo + dentro del item en el mismo correo →
  misma clave → `duplicate=True`, bien. Mismo PDF en varios mensajes del hilo
  (o un correo re-movido: Graph cambia el id al mover) → claves distintas →
  sv2 extrae otra vez (coste IA); sv3 lo caza por sha256 del fichero
  (`albaranes-persistencia/application/pipelines/persist_albaran_pipeline.py:100-103`)
  pero re-dispara valoración. Y la dedup de `workflow_runs` es opcional
  (vestigio, intake:96-101). Riesgo existente, que F-020 no agrava.
- **Firmas/logos**: el extractor de partes solo saca PDF; imágenes interiores
  se ignoran (buen defecto). Un PDF de «condiciones generales» o firma
  entraría, igual que hoy como adjunto directo. Decidir si las imágenes
  interiores (foto del albarán) deben entrar: sv1A acepta imágenes directas.
- **Tamaño**: `MAX_ATTACHMENT_MB` (`config/settings.py:40`, 25 MB) sobre el
  `size` de Graph y por PDF interior; el `$value` pesa ~1,33× por base64 y va
  entero a memoria; tope de 5 niveles contra bombas de anidamiento.

## 5. ruesma_comun y portabilidad

- En `ruesma_comun` hay: `graph/token_provider.py` y
  `sharepoint/graph_client.py`; **no** hay cliente de buzón ni nada MIME. El
  cliente de buzón vive en sv1A (único consumidor).
- partes **no usa `ruesma_comun`** (es otro monorepo, sin ese import): no
  hay pieza que «portar» entre ambos; hay que traer la lógica.
- Recomendación: el extractor es puro y solo lo usa sv1 → ponerlo en sv1A
  `infrastructure/document/` + puerto en `domain/ports/`, como en partes
  (la regla del monorepo prohíbe copiar **entre servicios de albaranes**, y
  esto no se compartiría). Alternativa si el humano quiere que también lo
  usen `capturar_correo.py`/evals/`encolar_extraccion.py`:
  `ruesma_comun/correo/mime.py`. Decisión a enseñar en la PARADA 1.
- Hallazgo colateral: `infrastructure/graph/token_provider.py` de sv1A es
  **copia literal** de `ruesma_comun/graph/token_provider.py` (solo difiere
  la línea 1; `main.py:16` importa la local). Viola la regla; fuera de
  alcance, apuntarlo al backlog.

## 6. Tests existentes de sv1A

8 ficheros `tests/test_f048_*.py` (~70 tests), dobles en
`tests/dobles_sv1.py` (`BuzonDoble`, `adjunto()` en :51-58 **sin**
`content_type`/`odata_type` configurables). Relacionados con este caso:
`test_f048_humo_pipeline.py:37` (sin elegibles → Errores),
`test_f048_r3_r5_pipeline.py:65` (sin elegibles no pide contenido),
`test_f048_r6_todos_los_albaranes.py:110-130` (tabla de destinos; hoy
`sin_elegibles` = adjunto inline). **Ninguno** cubre itemAttachment,
referenceAttachment ni `message/rfc822`. En partes hay 62 tests de F-020 y
un generador de `.eml` sintéticos en memoria (`tests/eml_sinteticos.py`),
reaprovechables como patrón.

## Propuesta de alcance mínimo (feature nueva en sv1A)

1. Clasificar adjuntos en una pasada: `message/rfc822` no inline, no
   reference, bajo límite → «correo adjunto»; si no, la regla actual de
   `_is_eligible` **sin cambios** (no restringir tipos directos: regresión).
2. Descargar `$value` con el cliente actual; extractor MIME puro con tope de
   5 niveles, solo PDF; tamaño por PDF interior.
3. Cada PDF interior → mismo `_process_attachment`/troceo/intake, mismo
   `ContextoCorreo` del exterior (F-048 intacto), `attachment_filename` del
   PDF interior.
4. Destino: Procesados sii nada falló y ≥1 página encolada; correo adjunto
   sin PDF = WARNING. Log sin cabeceras ni texto (R36 de F-048).
5. Fuera: `conversationId`, enlaces SharePoint, `.msg`, imágenes interiores,
   cabeceras del interior en el contexto (fase 2), reproceso de `Errores`.
   Verificación real contra el buzón: la hace el humano tras desplegar.

Ficheros a tocar (sv1A): `application/pipelines/polling_pipeline.py`,
`domain/models/email_models.py` (modelos del extractor),
`domain/ports/extractor_correo_adjunto.py` (nuevo),
`infrastructure/document/mime_pdf_extractor.py` (nuevo), `main.py`
(inyección), `tests/dobles_sv1.py`, `tests/eml_sinteticos.py` (nuevo),
`tests/test_fXXX_*.py` (nuevos), `docs/ARCHITECTURE.md` (sección de sv1).
No cambian sv2–sv6, ni colas, ni contrato del blob → `azure-apps/albaranes.md`
no requiere cambio salvo que se haga la fase 2.
