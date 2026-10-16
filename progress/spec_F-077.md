<!-- progress/spec_F-077.md -->
# F-077 · Ficha: guardar y aprobar de una vez · resumen de la spec (spec-author, 2026-10-16)

Spec: `specs/F-077-guardar-y-aprobar/` (v2: requirements 125/150 líneas, design 231/250, tasks T1–T15). Rama
`feature/F-077-guardar-y-aprobar`, worktree `C:\Users\pgris\PycharmProjects\albaranes-F-077`. Estado `spec_ready`,
prioridad 1, rigor **estandar**, servicio **sv4** únicamente.

## 1. Alcance

| Punto | Requisitos | En una frase |
|---|---|---|
| 1 · Guardar y aprobar | R1–R13 | Guarda antes las filas con cambios (mismo PATCH por fila y R27 v5); si una falla, para y no aprueba; «Guardar» igual sin aprobar |
| 2 · Panel del alta | R14–R20 | Fases `en_curso` (solo mientras sv9 procesa, como mucho 5 min), `sin_respuesta` (error de tiempo) y `resultado` (los malos, como error); sondeo cada 3 s de una ruta de solo lectura |
| 3 · ⚠ de la partida | R21–R23 | Solo en filas con lectura del albarán de origen Contrato, con tooltip «No coincide con la partida leída en el albarán (X)» |
| 4 · Motivos del alta | R24–R28 | Todos visibles (los de línea sin fila en la tabla, como «Línea N») y con texto legible, código en el `title` |

## 2. Decisiones (detalle en design §10)

- **D1** Parar al primer PATCH que falla. **D2** Tras un fallo no se recarga: las filas guardadas se consolidan para
  que un reintento no las reenvíe (el servidor daría 409). **D3** El aviso de suma se relee del servidor cuando se
  guardaron filas. **D4** Fases del panel con tope de 5 min desde la aprobación (PARADA 1). **D5** Al cambiar de fase
  se recarga la página entera (la ficha aprobada es de solo lectura). **D6** Una sola función de PATCH de fila en
  `app.js`. **D7** «Línea N» = posición en la tabla de la ficha (como F-065 R20); si no casa, «Línea (ref. <id>)».
- **«Solicitar alta» en `sin_respuesta`**: con la regla de siempre (`puede_solicitar_alta`). Sin fila o con fila
  repetible anterior, sí (a los 5 min lo probable es un mensaje perdido; un duplicado lo ignora sv9 dentro de la
  Espera, F-053 R7); con `en_curso` de la vigente, no hasta la Espera (sv9 lo ignoraría).
- **Long-poll**: evaluado y descartado por ahora (design §4): viable, pero no más sencillo y gana < 3 s.
- `incierto` no se pinta como error: es una grabación sin confirmar que sv9 retoma, con su aviso de bloqueo de hoy.

## 3. Tests existentes que cambian (design §7)

- `test_f065_f1_js.py`: se borran los dos R19 (uno pasa a `test_f077_r1_…`); los dos R18 pasan a `filasConCambios`;
  R21 se mantiene. `test_f065_f3bis_front.py`: `test_f065_r27v5_guardar_y_aprobar_marca_la_partida_mala` espera la
  alerta de partidas no válidas; `_GUARDAR` y `_FICHA` cambian de lista de funciones.
- F-053: ninguno debería cambiar de expectativas (códigos en el `title`, `estado_texto` sigue saliendo); si alguno
  compara dicts de motivos por igualdad, se adapta a la clave `texto`.

## 4. Riesgos

- No atómico (aceptado): si falla la aprobación, las filas guardadas quedan guardadas y bloqueadas.
- «Guardar» con `?buscar_si_cambia=1` puede relanzar la búsqueda y la revaloración descarta lo editado (F-058): hoy.
- «Solicitar alta» sin reaprobar no pasa por `en_curso` hasta que sv9 marca la fila; el listado (F-053 R31) sigue
  pintando el estado guardado. Fuera de alcance.
- El JS no lo mide la campaña de mutación (solo Python); lo cubren los tests con node.
- Rigor `estandar`: no cambia lo que se aprueba ni lo que recibe sv9.

## 5. Solapes con otras ramas

- **F-076** (spec en curso): R15 (`/api/sigrid/partidas`, mismos `items`: sin conflicto); **R23** (`agree_partida`
  por clave normalizada) y **R24** (nota «Normalizada: X → Y» en el mismo `title`) tocan las mismas líneas de
  `review_repository.py` (~L4641, ~L4787) y `document_detail.html` (~L742, ~L750). Semántica compatible (el ⚠ de F-077
  se deriva de `agree_partida`; la nota y el ⚠ son excluyentes); conflicto de texto: quien fusione segundo deja el
  `title` como «descripción ⏎ [nota F-076] ⏎ [aviso F-077]». F-077 no toca nada de F-076.
- **F-068**: `wireDividir`/F7, otra zona de `app.js`. `azure-apps/albaranes.md` no cambia (la ruta nueva es interna).

## Anexo A · Textos legibles de los motivos del alta (R26, R27)

Origen de los códigos (leído en `services/albaranes-alta-sigrid`, 2026-10-16): `validador_alta.py` (`Motivo("…")`),
`comparador_previa.py`, `clasificador.py` (`CODIGOS_CABECERA`, `CODIGO_LINEAS_NO_VALIDAS`, `CODIGOS_LINEA`),
`alta_sigrid_service.py` y `TipoFallo` (`alta_models.py`). Además, `http_<NNN>` ⇒ «sigrid-api respondió con HTTP
<NNN>»; un código desconocido se enseña tal cual. El detalle de sv9 se añade siempre detrás (« · <detalle>»).

| Código | Texto |
|---|---|
| `falta_obra` | Falta la obra |
| `falta_cif` | Falta el CIF del proveedor |
| `cif_no_valido` | El CIF del proveedor no es válido |
| `falta_numero_albaran` | Falta el número de albarán |
| `fecha_ilegible` | La fecha del albarán no se entiende |
| `fecha_no_plausible` | La fecha del albarán no es plausible (futura o demasiado antigua) |
| `no_valorado` | El albarán no está valorado |
| `sin_lineas` | No hay líneas que dar de alta |
| `campo_demasiado_largo` | Un campo es demasiado largo para Sigrid |
| `falta_descripcion` | La línea no tiene descripción |
| `cantidad_no_valida` | La línea no tiene cantidad (o es 0) |
| `cantidad_sin_convertir` | La línea no tiene la cantidad en la unidad del contrato |
| `producto_no_admitido` | Producto de Sigrid no admitido |
| `signo_incoherente` | La cantidad y el importe tienen signos distintos |
| `linea_de_otro_contrato` | La línea es de otro contrato |
| `lineas_distintas` | Las líneas no coinciden con lo que devolvió Sigrid |
| `importe_distinto` | El importe no coincide con el que calcula Sigrid |
| `registrado_distinto` | Lo registrado en Sigrid no coincide con lo aprobado |
| `partida_distinta` | Sigrid devolvió otra partida |
| `aviso_bloqueante` | Sigrid dio un aviso que impide el alta |
| `alta_a_mano` | Ya hay un alta a mano en Sigrid para este albarán |
| `respuesta_inesperada` | Sigrid devolvió una respuesta inesperada |
| `excepcion` | Fallo interno al dar de alta (sv9) |
| `obra_no_encontrada` | La obra no existe en Sigrid |
| `obra_ambigua` | La obra es ambigua en Sigrid |
| `contrato_no_encontrado` | El contrato no existe en Sigrid |
| `contrato_ambiguo` | El contrato es ambiguo en Sigrid |
| `proveedor_sin_albaran_previo` | El proveedor no tiene ningún albarán previo en Sigrid |
| `almacen_de_obra_no_resuelto` | Sigrid no encuentra el almacén de la obra |
| `demasiadas_lineas` | El albarán tiene más líneas de las que admite Sigrid |
| `referencia_en_conflicto` | Otro albarán de Sigrid ya lleva este número |
| `escritura_albaranes_deshabilitada` | La escritura de albaranes está deshabilitada en sigrid-api |
| `base_de_datos_no_permitida` | sigrid-api no permite escribir en esa base de datos |
| `referencia_no_permitida` | sigrid-api no admite esa referencia |
| `obra_de_empresa_no_permitida` | La obra es de una empresa en la que no se puede dar de alta |
| `usuario_no_valido` | El usuario de Sigrid no es válido |
| `estado_inicial_no_encontrado` | Sigrid no encuentra el estado inicial del albarán |
| `peticion_mixta` | Petición no válida: mezcla líneas de contrato y sueltas de forma no admitida |
| `colision_de_clave` | Colisión de clave en Sigrid: vuelve a solicitar el alta |
| `filas_afectadas_inesperadas` | Sigrid escribió un número de filas inesperado |
| `lineas_no_validas` | Sigrid rechazó alguna línea |
| `linea_no_es_del_contrato` | La línea no es del contrato |
| `partida_no_encontrada` | La partida no existe en la obra en Sigrid |
| `partida_ambigua` | La partida es ambigua en la obra |
| `partida_no_imputable` | La partida no admite imputaciones |
| `paride_no_valido` | Identificador de partida no válido |
| `analitica_no_resuelta` | Sigrid no encuentra la analítica de la obra |
| `producto_no_permitido` | Producto no permitido en Sigrid |
| `producto_no_encontrado` | El producto no existe en Sigrid |
| `naturaleza_no_valida` | Naturaleza no válida (configuración de sigrid-api) |
| `precio_negativo` | Precio negativo |
| `rechazo` | Sigrid rechazó el alta |
| `autorizacion` | sigrid-api no autorizó la petición |
| `cliente` | Petición no válida para sigrid-api |
| `servidor` | Error del servidor de sigrid-api |
| `tiempo_agotado` | sigrid-api no respondió a tiempo |
| `conexion` | No se pudo conectar con sigrid-api |
| `respuesta_invalida` | Respuesta no válida de sigrid-api |

Los textos de `peticion_mixta`, `estado_inicial_no_encontrado` y `referencia_no_permitida` son interpretaciones del
código: si el implementer encuentra en `azure-apps/sigrid_api.md` una definición mejor, la usa y lo anota.

## PARADA 1: APROBADA (2026-10-16)

El humano aprobó la PARADA 1 con estos cambios sobre las opciones por defecto (ya incorporados en la spec v2):

- **P1 + P4** (palabras del humano: «alta en curso es solo durante el proceso de alta (escritura en sigrid)… si sale
  bien lo que tarde, si sale mal dará error en lugar de alta en curso… que espere respuesta, si no cada 3 s, y si
  pasan más de 5 min sin respuesta entonces que dé error de tiempo, la escritura en sigrid es rápida»):
  · «Alta en curso…» solo mientras sv9 procesa el alta de la aprobación vigente (sin fila, resultado anterior en estado
  repetible, o `en_curso` de la vigente). Con resultado: bueno se muestra; malo (`no_admitido`/`revisar`/`error`) como
  ERROR con sus motivos, nunca «en curso» (R14–R17).
  · Sondeo cada 3 s fijos (R19). Long-poll evaluado como alternativa en design §4; la spec va con sondeo.
  · Tope de 5 min desde la aprobación (sustituye a la cota de 15 min de la Espera): error de tiempo honesto, sin
  sondear; «Solicitar alta» según `puede_solicitar_alta` (justificado en §2) (R16).
  · Se mantiene: no quedarse «en curso» cuando sv9 va a ignorar la aprobación (`ya_en_sigrid`, `registrado`…).
- **P2**: el ⚠ de partida NO se pinta en filas sin línea del albarán (manual, sintética, reparto) ni en las Nueva;
  solo en filas Contrato cuya lectura del papel no coincide; tooltip solo ahí (R21–R23). Solape con F-076 R23–R25
  anotado en §5 y design §9, sin tocar F-076.
- **P3**: sí, ya: texto legible también para los motivos del DOCUMENTO, con el código en el `title`; tabla completa en
  el Anexo A y test que la contrasta con las fuentes de sv9 (R26, R27).
- D1–D7, como estaban.
