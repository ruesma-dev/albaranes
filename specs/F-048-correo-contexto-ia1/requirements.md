<!-- specs/F-048-correo-contexto-ia1/requirements.md -->
# F-048 · El texto del correo llega a IA1 como contexto — Requisitos (EARS)

Rigor `critico`. Servicios: **sv1, sv2, sv3 (solo modelo y merge), `comun`**,
más `evals/`. El porqué y las decisiones del humano, en la ficha; el CÓMO, en
`design.md`. **Contexto de correo** = asunto + parte ÚNICA del cuerpo
(`uniqueBody`). **Origen de datos** = bloque que sella sv2 con la fuente de la
obra y de la partida.

## A · Transporte del texto (comun + sv1)

- **R1.** El sistema debe definir en `ruesma_comun` UN único modelo de contexto
  de correo (asunto, cuerpo, sha256, caracteres originales, `truncado`,
  documentos del correo, fecha de recepción, versión) y UNA función que lo
  construye: normaliza espacios, recorta el cuerpo a un máximo configurable
  (defecto 4.000 caracteres) y calcula el sha256 sobre lo que se conserva.
- **R2.** CUANDO sv1 procesa un mensaje con adjuntos elegibles, sv1 debe pedir
  a Graph el asunto y el `uniqueBody` en texto con UNA petición GET por
  mensaje, sin ninguna escritura sobre el buzón además de las que ya hace hoy.
- **R3.** SI `uniqueBody` llega vacío, ENTONCES el contexto lleva solo el
  asunto (nunca el `body` completo, con la cadena de respuestas).
- **R4.** SI Graph devuelve el cuerpo en HTML pese a pedirlo en texto,
  ENTONCES sv1 debe reducirlo a texto plano sin interpretar su contenido.
- **R5.** SI la petición del contexto falla, ENTONCES sv1 debe seguir
  procesando los adjuntos sin contexto, sin mover el correo a `Errores` por
  ese motivo, y dejar un aviso en el log que no contenga texto del correo.
- **R6.** sv1 debe registrar en el contexto cuántos documentos (páginas de
  todos los adjuntos elegibles) salen del mensaje; SI algún adjunto no se pudo
  descargar o trocear, ENTONCES ese número debe ser nulo (desconocido). El
  destino final del correo (`Procesados`/`Errores`) no debe cambiar respecto
  a hoy para ninguna combinación de adjuntos buenos y fallidos.
- **R7.** CUANDO sv1 encola una página NUEVA con contexto, sv1 debe guardar el
  contexto en el blob `input/{document_id}.correo.json` ANTES de publicar
  `MensajeExtraccion`, y el mensaje debe llevar el nombre de ese blob en el
  campo nuevo `correo_blob`. En la rama de duplicado no se escribe nada.
- **R8.** El texto no viaja en el mensaje: con un cuerpo de 60.000 caracteres
  el mensaje serializado mide menos de 1 KB.
- **R9.** `MensajeExtraccion.correo_blob` debe ser opcional con valor nulo por
  defecto: un mensaje sin el campo debe validar, y un mensaje con el campo
  debe validar en un modelo que no lo declare (orden de despliegue libre para
  el mensaje).
- **R10.** `workflow_runs.payload_json` guarda el sha256 del correo, nunca el
  cuerpo.

## B · Inyección en IA1 y en IA2 (sv2)

- **R11.** CUANDO el mensaje trae `correo_blob`, sv2 debe leer el contexto;
  SI el blob no existe o no valida, ENTONCES sv2 debe extraer sin contexto,
  con un aviso en el log y `origen_datos.correo_presente = false`.
- **R12.** El task de fase 1 debe llevar el marcador `{contexto_correo}` y sv2
  debe sustituirlo por un bloque delimitado con el asunto y el cuerpo; sin
  contexto, por una nota fija de «no disponible»; y SI el YAML desplegado no
  trae el marcador, ENTONCES el bloque debe añadirse al final del task.
- **R13.** El bloque debe declarar que el texto es DATO y no instrucciones, y
  sv2 debe neutralizar dentro del texto cualquier aparición de las marcas de
  apertura y cierre, de forma que el correo no pueda cerrar el bloque.
- **R14.** El MISMO bloque renderizado debe llegar a la fase 2 dentro de
  `{prompt_fase_1}`: ningún prompt de ninguna fase debe contener el literal
  `{contexto_correo}` (comprobado contra el `config/prompts.yaml` real, en
  todos los prompts de fase 2 del catálogo).
- **R15.** IA1 debe devolver un bloque `lectura_correo` con los códigos de
  obra y de partida que lee en el correo (listas) y la frase exacta donde los
  lee. `cabecera.obra_codigo` y `lineas[].codigo_imputacion` siguen siendo
  lectura del PAPEL.
- **R16.** CUANDO el correo trae obra, el prompt debe decirle a IA1 que NO la
  deduzca del papel (dirección, nombre, destinatario): solo la transcribe si
  está impresa. Lo mismo para la partida.
- **R17.** SI la respuesta no trae `lectura_correo` (proveedor sin prompt,
  envelope antiguo), ENTONCES el sistema debe tratarlo como correo sin dato,
  con motivo `ia_sin_lectura_correo`, y la extracción debe seguir.

## C · Qué manda: la precedencia la sella sv2, no la IA

- **R18.** CUANDO la lectura del correo trae EXACTAMENTE un código de obra y
  ese código está en la lista de obras activas (o la lista no está
  disponible), sv2 debe fijar `cabecera.obra_codigo` a ese código con
  `fuente = correo`, aunque el papel diga otra cosa.
- **R19.** SI el correo trae DOS O MÁS códigos de obra distintos, ENTONCES
  decide el papel (`fuente = papel`, motivo `correo_ambiguo`) y los
  candidatos del correo quedan registrados.
- **R20.** SI la lista de obras activas está disponible y el código del correo
  no está en ella, ENTONCES decide el papel (motivo `correo_fuera_de_lista`) y
  el código leído queda registrado.
- **R21.** CUANDO el correo trae EXACTAMENTE una partida, sv2 debe fijarla como
  `codigo_imputacion` de TODAS las líneas; con dos o más, decide el papel
  (motivo `correo_ambiguo`). La partida del correo queda con
  `validada = null`: sv2 no tiene la lista de partidas de la obra (ver
  `design.md` §7, propuesta F-049).
- **R22.** CUANDO gana el correo y el papel traía un valor distinto, el
  sistema debe registrar la discrepancia —obra: valor del papel; partida: una
  entrada por línea con su índice, papel y correo—. La comparación ignora
  mayúsculas y espacios. La discrepancia NO debe añadir motivo de revisión ni
  frenar el documento.
- **R23.** SI el mensaje no trae contexto, ENTONCES el `data` final debe ser
  idéntico al de hoy salvo el bloque `origen_datos` (`fuente = papel`, motivo
  `sin_correo`).
- **R24.** `origen_datos` lo sella el resolver de sv2: lo que la IA ponga en
  ese campo se ignora, y `lectura_correo` no debe llegar al `data` final.
- **R25.** `origen_datos` no debe contener el cuerpo del correo: solo el
  sha256, `truncado`, los documentos del correo, los códigos y la frase de
  evidencia recortada a 160 caracteres.
- **R26.** La precedencia debe aplicarse sobre el documento FINAL (tras la
  fase 2): si IA2 cambia la obra o la partida, el correo sigue mandando.

## D · Persistencia (sv3, solo modelo y merge)

- **R27.** sv3 acepta `data.origen_datos` opcional; sin él valida como hoy.
- **R28.** El merge de sv3 debe conservar `origen_datos`: el
  `raw_extraction_json` de `albaran_documents_merge` debe contenerlo (mismo
  defecto que F-043 cazó con `clasificacion`).
- **R29.** La red de obra de sv3 (inexistente ⇒ sin obra + revisión) se
  aplica igual venga la obra del correo o del papel.

## E · Datos personales y logs

- **R30.** Ninguna línea de log de sv1 ni de sv2 debe contener el cuerpo del
  correo: solo sha256 abreviado, caracteres y `truncado` (comprobado con un
  centinela en el cuerpo que no debe aparecer en ningún registro capturado).
- **R31.** `LlmCallLogger` debe sustituir el bloque del correo por un resumen
  (`sha256`, caracteres) en todo texto de `request_summary` antes de escribir
  a disco.
- **R32.** Ningún fixture versionado debe contener texto de un correo real:
  los tests usan textos inventados, y los correos reales viven en rutas que
  `git check-ignore` confirma ignoradas.

## F · Medición y verificación real

- **R33.** El sistema debe ofrecer un script de SOLO LECTURA en sv1 que, dado
  un `message_id`, pida a Graph el contexto por el mismo camino que R2 y lo
  guarde en `evals/inputs/correos/{caso_id}.json`, sin mover, marcar ni
  modificar el mensaje.
- **R34.** CUANDO un caso del banco tiene `evals/inputs/correos/{caso_id}.json`,
  la inyección del ciclo de F-047 debe guardarlo con la MISMA función de
  `ruesma_comun` que usa sv1 y poner `correo_blob`; sin fichero, como hoy.
- **R35.** El ciclo debe admitir inyectar el mismo caso con y sin correo, para
  medir obra y partida en las dos condiciones sobre la misma muestra.
- **R36.** El script local `encolar_extraccion.py` de sv2 debe admitir un
  contexto de correo desde fichero, por la misma función de `ruesma_comun`.
- **R37.** La feature no se cierra sin una verificación de extremo a extremo
  con un correo REAL y su albarán real en el pipeline local, leyendo el
  resultado de `albaran_documents_merge` con SELECT.

## G · Calidad

- **R38.** Cada R tiene test trazable (`test_f048_rN_...`) con fase RED;
  cobertura ≥ 80 %; mutación completa sin supervivientes injustificados.

**Fuera de alcance**: validar la partida contra la lista de la obra (diseño
§7, F-049); mostrar `origen_datos` en sv4; prometer que RES-001…004 y ALQ-001
lleguen a contrato (el correo da la obra; el CIF que falta es otro problema).
