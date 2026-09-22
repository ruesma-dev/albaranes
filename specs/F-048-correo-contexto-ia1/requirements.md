<!-- specs/F-048-correo-contexto-ia1/requirements.md -->
# F-048 · El texto del correo llega a IA1 como contexto — Requisitos (EARS)

Rigor `critico`. Servicios: **sv1, sv2, sv3 (modelo y merge), sv4 (solo
pintar), `comun`**, más `evals/`. Porqué y decisiones, en la ficha y en
`design.md` §2 (validadas por el humano el 2026-09-22). **Contexto de correo**
= asunto + parte ÚNICA del cuerpo (`uniqueBody`). **Origen de datos** = bloque
que sella sv2 con la fuente de la obra y de la partida.

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
  asunto (nunca el `body` completo, con la cadena de respuestas).
- **R4.** SI Graph devuelve HTML pese a pedir texto, ENTONCES sv1 lo reduce a
  texto plano sin interpretar su contenido.
- **R5.** SI la petición del contexto falla, ENTONCES sv1 sigue con los
  adjuntos sin contexto, sin mover el correo a `Errores` por ese motivo, y
  con un aviso en el log sin texto del correo.
- **R6.** El contexto de un mensaje debe aplicarse a TODOS sus documentos:
  cada página nueva de cada adjunto recibe el mismo contexto (mismo sha256),
  sea uno o sean varios albaranes (decisión del humano, 2026-09-22).
- **R7.** CUANDO sv1 encola una página NUEVA con contexto, debe guardarlo en
  `input/{document_id}.correo.json` ANTES de publicar `MensajeExtraccion`, que
  lleva el nombre del blob en el campo nuevo `correo_blob`. En la rama de
  duplicado no se escribe nada.
- **R8.** El texto no viaja en el mensaje: con un cuerpo de 60.000 caracteres
  el mensaje serializado mide menos de 1 KB.
- **R9.** `correo_blob` es opcional y nulo por defecto: un mensaje sin el campo
  valida, y uno con el campo valida en un modelo que no lo declare.
- **R10.** `workflow_runs.payload_json` guarda el sha256 del correo, nunca el
  cuerpo.

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
- **R15.** IA1 devuelve `lectura_correo` con los códigos de obra y de partida
  que lee en el correo (listas) y la frase donde los lee.
  `cabecera.obra_codigo` y `lineas[].codigo_imputacion` siguen siendo lectura
  del PAPEL.
- **R16.** CUANDO el correo trae obra, el prompt le dice a IA1 que NO la
  deduzca del papel (dirección, nombre, destinatario): solo la transcribe si
  está impresa. Igual con la partida.
- **R17.** SI la respuesta no trae `lectura_correo`, ENTONCES se trata como
  correo sin dato (motivo `ia_sin_lectura_correo`) y la extracción sigue.

## C · Qué manda: la precedencia la sella sv2, no la IA

- **R18.** CUANDO el correo trae UN código de obra y está en la lista de obras
  activas (o la lista no está disponible), sv2 fija `cabecera.obra_codigo` a
  ese código con `fuente = correo`, aunque el papel diga otra cosa.
- **R19.** SI el correo trae DOS O MÁS códigos de obra distintos, ENTONCES
  decide el papel (motivo `correo_ambiguo`), los candidatos quedan
  registrados y el revisor lo ve (R40). *Propuesta pendiente de validar por
  el humano: `design.md` D4.*
- **R20.** SI la lista está disponible y el código del correo no está en ella,
  ENTONCES decide el papel (motivo `correo_fuera_de_lista`), el código leído
  queda registrado y el revisor lo ve.
- **R21.** CUANDO el correo trae UNA partida, sv2 la fija como
  `codigo_imputacion` de TODAS las líneas; con dos o más, decide el papel
  (`correo_ambiguo`, misma propuesta que R19). `validada = null` hasta F-049.
- **R22.** CUANDO gana el correo y el papel traía otro valor, el sistema
  registra la discrepancia con las dos lecturas y su fuente —obra: correo y
  papel; partida: una entrada por línea con índice, papel y correo—. La
  comparación ignora mayúsculas y espacios. El valor usado sigue siendo el
  del correo, y la discrepancia NO añade motivo de revisión.
- **R23.** SI el mensaje no trae contexto, ENTONCES el `data` final es idéntico
  al de hoy salvo `origen_datos` (`fuente = papel`, motivo `sin_correo`).
- **R24.** `origen_datos` lo sella el resolver: lo que ponga la IA se ignora, y
  `lectura_correo` no llega al `data` final.
- **R25.** `origen_datos` no contiene el cuerpo: solo sha256, `truncado`,
  códigos y la frase de evidencia recortada a 160 caracteres.
- **R26.** La precedencia se aplica sobre el documento FINAL (tras la fase 2).

## D · Persistencia (sv3, solo modelo y merge)

- **R27.** sv3 acepta `data.origen_datos` opcional; sin él valida como hoy.
- **R28.** El merge conserva `origen_datos` dentro del `raw_extraction_json`
  de `albaran_documents_merge` (el defecto que F-043 cazó con `clasificacion`).
- **R29.** La red de obra de sv3 (inexistente ⇒ sin obra + revisión) se aplica
  igual venga la obra del correo o del papel.

## E · Lo que ve el revisor (sv4, solo lectura)

- **R39.** CUANDO el revisor abre un albarán cuyo merge trae `origen_datos` con
  alguna discrepancia, sv4 debe mostrar en la ficha (`document_detail.html`),
  junto a la clasificación y los motivos de revisión, un aviso visible con
  cada discrepancia: campo, valor del correo, valor del papel y, en partidas,
  la línea.
- **R40.** CUANDO `origen_datos` trae `correo_ambiguo` o `correo_fuera_de_lista`,
  sv4 debe mostrar en el mismo aviso los códigos del correo que no se
  aplicaron y por qué.
- **R41.** sv4 no escribe nada nuevo: ni DDL, ni `review_notes` (que es del
  revisor), ni motivos. SI `raw_extraction_json` falta, está roto o no trae
  `origen_datos`, ENTONCES la ficha abre igual que hoy, sin aviso.

## F · Datos personales y logs

- **R30.** Ningún log de sv1 ni de sv2 contiene el cuerpo: solo sha256
  abreviado, caracteres y `truncado` (comprobado con un centinela).
- **R31.** `LlmCallLogger` sustituye el bloque del correo por un resumen
  (sha256, caracteres) en todo texto de `request_summary` antes de escribir.
- **R32.** Ningún fixture versionado contiene texto de un correo real; los
  correos reales viven en rutas que `git check-ignore` confirma ignoradas.

## G · Medición y verificación real

- **R33.** Script de SOLO LECTURA en sv1 que, dado un `message_id`, pide el
  contexto por el camino de R2 y lo guarda en
  `evals/inputs/correos/{caso_id}.json`, sin mover, marcar ni modificar nada.
- **R34.** CUANDO un caso del banco tiene ese fichero, la inyección de F-047 lo
  guarda con la MISMA función de `ruesma_comun` que sv1 y pone `correo_blob`.
- **R35.** El ciclo admite inyectar el mismo caso con y sin correo.
- **R36.** `encolar_extraccion.py` de sv2 admite un contexto desde fichero, por
  la misma función de `ruesma_comun`.
- **R37.** La feature no se cierra sin una verificación extremo a extremo con
  un correo REAL y su albarán en el pipeline local, incluida la ficha de sv4.
- **R38.** Cada R tiene test trazable (`test_f048_rN_...`) con fase RED;
  cobertura ≥ 80 %; mutación completa sin supervivientes injustificados.

**Fuera de alcance**: validar la partida contra la lista de la obra (F-049);
**bajar el % de fiabilidad por discrepancia** («en el futuro», dijo el humano:
el dato queda guardado para ello, `design.md` D6, ficha futura); prometer que
RES-001…004 y ALQ-001 lleguen a contrato (el CIF que falta es otro problema).
