<!-- specs/F-048-correo-contexto-ia1/requirements.md -->
# F-048 · El texto del correo llega a IA1 como contexto (solo OBRA) — Requisitos (EARS)

Rigor `critico`. Servicios: **sv1, sv2, sv3 (modelo, merge, motivos), sv4
(solo pintar), `comun`**, más `evals/`. Decisiones: `design.md` §2. **Contexto
de correo** = asunto + parte ÚNICA del cuerpo (`uniqueBody`). **Origen de
datos** = bloque que sella sv2 con la fuente de la OBRA. Del correo, SOLO la
obra: «la partida de momento no se indica en correo. solo obra» (2026-09-23).

## A · Transporte del texto (comun + sv1)

- **R1.** El sistema debe definir en `ruesma_comun` UN modelo de contexto de
  correo (asunto, cuerpo, sha256, caracteres originales, `truncado`, fecha de
  recepción, versión) y UNA función que lo construye: normaliza espacios,
  recorta el cuerpo a un máximo configurable (defecto 4.000) y calcula el
  sha256 sobre lo conservado.
- **R2.** CUANDO sv1 procesa un mensaje con adjuntos elegibles, debe pedir a
  Graph asunto y `uniqueBody` en texto con UNA petición GET por mensaje, sin
  más escrituras sobre el buzón que las de hoy.
- **R3.** SI `uniqueBody` llega vacío, ENTONCES el contexto lleva solo el
  asunto (nunca el `body`, con la cadena de respuestas).
- **R4.** SI Graph devuelve HTML pese a pedir texto, ENTONCES sv1 lo reduce a
  texto plano sin interpretar su contenido.
- **R5.** SI la petición del contexto falla, ENTONCES sv1 sigue con los
  adjuntos sin contexto, sin mover el correo a `Errores` por ese motivo, y
  con un aviso en el log sin texto del correo.
- **R6.** El contexto de un mensaje se aplica a TODOS sus documentos: cada
  página nueva de cada adjunto recibe el mismo (mismo sha256) (2026-09-22).
- **R7.** CUANDO sv1 encola una página NUEVA con contexto, debe guardarlo en
  `input/{document_id}.correo.json` ANTES de publicar `MensajeExtraccion`, que
  lleva el nombre del blob en el campo nuevo `correo_blob`. En la rama de
  duplicado no se escribe nada.
- **R8.** El texto no viaja en el mensaje: con 60.000 caracteres mide < 1 KB.
- **R9.** `correo_blob` es opcional y nulo por defecto: un mensaje sin el campo
  valida, y uno con el campo valida en un modelo que no lo declare.
- **R10.** `workflow_runs.payload_json` guarda el sha256, nunca el cuerpo.

## B · Inyección en IA1 y en IA2 (sv2)

- **R11.** CUANDO el mensaje trae `correo_blob`, sv2 lee el contexto; SI el
  blob no existe o no valida, ENTONCES extrae sin él, con aviso en el log y
  `origen_datos.correo_presente = false`.
- **R12.** El task de fase 1 lleva el marcador `{contexto_correo}`; sv2 lo
  sustituye por un bloque delimitado con asunto y cuerpo; sin contexto, por
  una nota fija; y SI el YAML desplegado no trae el marcador, ENTONCES el
  bloque se añade al final del task.
- **R13.** El bloque declara que el texto es DATO y no instrucciones, y sv2
  neutraliza dentro del texto las marcas de apertura y cierre.
- **R14.** El MISMO bloque llega a la fase 2 dentro de `{prompt_fase_1}`:
  ningún prompt de ninguna fase contiene el literal `{contexto_correo}`
  (comprobado sobre el `config/prompts.yaml` real, todos los de fase 2).
- **R15.** IA1 devuelve `lectura_correo` con los códigos de OBRA que lee en el
  correo (lista) y la frase donde los lee. `cabecera.obra_codigo` sigue siendo
  lectura del PAPEL; `lineas[].codigo_imputacion` sale solo del papel.
- **R16.** El prompt le dice a IA1 que del correo solo toma el código de obra
  (nunca la partida) y que la obra del PAPEL la lee o deduce SIEMPRE como hoy,
  traiga o no obra el correo: son dos lecturas independientes que cruza sv2.
- **R17.** SI la respuesta no trae `lectura_correo`, ENTONCES se trata como
  correo sin dato (motivo `ia_sin_lectura_correo`) y la extracción sigue.

## C · Qué manda y el cruce: lo sella sv2, no la IA

- **R18.** Todo código se compara con `normalizar_codigo` (mayúsculas, fuera lo
  no alfanumérico y los ceros a la izquierda; vacío ⇒ sin código: «sí,
  normaliza todo», 2026-09-23) y se valida contra la lista de TODAS las obras
  de Sigrid con contrato, activas o no, que sv2 ya descarga para F-002, sin
  llamada nueva. Del correo CUENTAN solo los que están en ella; SI la lista no
  está disponible, ENTONCES cuentan todos, con `validada = null`.
- **R19.** CUANDO del correo cuenta UN código, sv2 fija `cabecera.obra_codigo`
  a ese código —escrito como figura en la lista— con `fuente = correo` (motivo
  `correo_unico`) aunque el papel diga otra cosa: el correo manda. SI el papel
  trae OTRO código, ENTONCES `obra.discrepancia = true` con las dos lecturas;
  sin código en el papel, o el mismo, no hay discrepancia.
- **R20.** CUANDO cuentan DOS O MÁS códigos distintos y el del papel es uno de
  ellos, sv2 deja la obra del papel (motivo `correo_confirma_papel`, sin
  discrepancia). SI no lo es o el papel no trae código, ENTONCES deja la del
  papel —o ninguna— sin imponer ninguno (motivo `correo_ambiguo`). En los dos
  casos los que cuentan quedan en `candidatos_correo`.
- **R21.** SI la lista está disponible y NINGÚN código del correo está en ella,
  ENTONCES el correo se trata como sin código (será un pedido, un teléfono):
  manda la IA con lo que lea del papel, motivo `correo_fuera_de_lista`,
  `validada = false`, los leídos en `candidatos_correo`, sin discrepancia y
  sin motivo de revisión («si no está manda IA», 2026-09-23).
- **R22.** SI el mensaje no trae contexto, ENTONCES el `data` final es idéntico
  al de hoy salvo `origen_datos` (`fuente = papel`, motivo `sin_correo`).
- **R23.** `origen_datos` lo sella el resolver: lo que ponga la IA se ignora, y
  `lectura_correo` no llega al `data` final.
- **R24.** `origen_datos` no contiene el cuerpo: solo sha256, `truncado`,
  códigos y la frase de evidencia recortada a 160 caracteres.
- **R25.** La precedencia y el cruce se aplican al documento FINAL (fase 2).

## D · Persistencia y revisión (sv3)

- **R26.** sv3 acepta `data.origen_datos` opcional; sin él valida como hoy.
- **R27.** El merge conserva `origen_datos` dentro del `raw_extraction_json`
  de `albaran_documents_merge` (el defecto que F-043 cazó con `clasificacion`).
- **R28.** La red de obra de sv3 (inexistente ⇒ sin obra + revisión) se aplica
  igual venga la obra del correo o del papel.
- **R29.** CUANDO `origen_datos.obra.discrepancia` es true, sv3 añade el motivo
  `obra_correo_distinta_papel` a los de revisión (`review_required = true`),
  sin cambiar la obra ni la confianza.
- **R30.** CUANDO `origen_datos.obra.motivo` es `correo_ambiguo`, sv3 debe
  añadir el motivo `obra_correo_ambigua`, con el mismo efecto.
- **R31.** SI `origen_datos` falta o su obra no cumple R29 ni R30 (sin correo,
  sin código, fuera de lista, único sin discrepancia o confirmado por el papel),
  ENTONCES los motivos de revisión son los de hoy. Los nombres de los dos
  motivos se definen UNA vez en `ruesma_comun` (los importan sv3 y sv4).

## E · Lo que ve el revisor (sv4, solo lectura)

- **R32.** CUANDO el merge trae `origen_datos` con discrepancia, sv4 muestra en
  la ficha (`document_detail.html`), junto a la clasificación y los motivos de
  revisión, un aviso con el campo, el código del correo y el del papel.
- **R33.** CUANDO la obra trae `correo_ambiguo`, `correo_confirma_papel` o
  `correo_fuera_de_lista`, el aviso muestra `candidatos_correo` y el motivo
  (los dos últimos, informativos: no llevan motivo de revisión).
- **R34.** Los motivos de R29–R30 aparecen en el bloque «Motivos de revisión»
  que ya existe, y el aviso de R32–R33 se pinta como advertencia cuando el
  documento trae alguno de ellos (como la clasificación en duda de F-043).
- **R35.** sv4 no escribe nada nuevo: ni DDL, ni `review_notes` (que es del
  revisor), ni motivos. SI `raw_extraction_json` falta, está roto o no trae
  `origen_datos`, ENTONCES la ficha abre igual que hoy, sin aviso.

## F · Datos personales y logs

- **R36.** Ningún log de sv1 ni de sv2 contiene el cuerpo: solo sha256
  abreviado, caracteres y `truncado` (comprobado con un centinela).
- **R37.** `LlmCallLogger` sustituye el bloque del correo por un resumen
  (sha256, caracteres) en todo texto de `request_summary` antes de escribir.
- **R38.** Ningún fixture versionado contiene texto de un correo real; los
  correos reales viven en rutas que `git check-ignore` confirma ignoradas.

## G · Medición y verificación real

- **R39.** Script de SOLO LECTURA en sv1 que, dado un `message_id`, pide el
  contexto por el camino de R2 y lo guarda en `evals/inputs/correos/{caso_id}.json`
  sin mover, marcar ni modificar nada.
- **R40.** CUANDO un caso del banco tiene ese fichero, la inyección de F-047 lo
  guarda con la MISMA función de `ruesma_comun` que sv1 y pone `correo_blob`.
- **R41.** El ciclo admite inyectar el mismo caso con y sin correo.
- **R42.** `encolar_extraccion.py` de sv2 admite un contexto desde fichero (misma función).
- **R43.** La feature no se cierra sin una verificación extremo a extremo con
  un correo REAL y su albarán en el pipeline local, incluida la ficha de sv4.
- **R44.** Cada R tiene test trazable (`test_f048_rN_...`) con fase RED;
  cobertura ≥ 80 %; mutación completa sin supervivientes injustificados.

**Fuera de alcance**: **la partida en el correo, de momento** (2026-09-23,
`design.md` D8); validar la partida contra la lista de la obra (F-049); **bajar
el % de fiabilidad** (D6 bis, ficha futura); que RES-001…004 y ALQ-001 lleguen
a contrato (el CIF que falta es otro problema).
