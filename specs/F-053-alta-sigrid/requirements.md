<!-- specs/F-053-alta-sigrid/requirements.md -->
# F-053 · Alta en Sigrid de los albaranes aprobados · Requisitos

Rigor **critico** (escribe en el ERP de producción). Servicios: **sv9 nuevo**
(`services/albaranes-alta-sigrid`), sv4, sv3 (solo DDL), `ruesma_comun`, `infra`.
Sustituye a F-013. Preguntas abiertas: `progress/spec_F-053.md`. Decisiones del
humano (no se reabren): aprobar ES registrar; solo sigrid-api con endpoints de
dominio, nunca `sql/write`; sigrid-api no se toca.

## Glosario

- **Alta**: la fila de `albaran_altas_sigrid` de un documento (una por documento).
  Solo la escribe sv9. Estados: `en_curso`, `no_admitido`, `ya_en_sigrid`,
  `simulado`, `revisar`, `error`, `incierto`, `registrado`, `anulado`.
- **Bloqueante**: alta en `en_curso`, `incierto` o `registrado`. **Espera**:
  `ALTA_SIGRID_ESPERA_INCIERTO_MIN` (defecto 15) desde el último intento.
- **Modo**: `simulacion` si `ALTA_SIGRID_COMMIT` no es literalmente `true`; si
  lo es, `real`. **DESDE**: `ALTA_SIGRID_DESDE_UTC`; vacía = feature apagada.
- **Línea a registrar**: línea valorada con `cantidad_convertida` > 0. **Previa**:
  `sigrid/albaran` con `commit=false` (dry-run).

## A. Disparo en sv4

R1. CUANDO un documento no aprobado pasa a aprobado (POST `/documents/{id}/approve`
o PUT `/api/documents/{id}` con `approved=true`) y DESDE no está vacía, sv4 debe
publicar en `q-feedback` un `MensajeFeedback` con `accion="alta"`, el
`document_id` y `approved_by`.
R2. CUANDO se guarda o aprueba un documento ya aprobado, sv4 no debe publicar.
R3. MIENTRAS DESDE esté vacía, sv4 debe comportarse como hoy: no publica ni
pinta nada del alta (regresión de aprobar, guardar y desaprobar).
R4. SI falla la publicación de R1, ENTONCES la aprobación debe quedar guardada y
el mensaje al revisor debe decir que el alta en Sigrid no se ha solicitado.

## B. Entrada en sv9

R5. CUANDO sv9 recibe un mensaje de alta, debe, en una transacción con la fila
del merge bloqueada (`FOR UPDATE`), comprobar que el documento existe, está
activo y aprobado con `approved_at_utc` ≥ DESDE, y dejar el alta en `en_curso`
(creándola si falta), guardando `approved_at_utc`, `approved_by` e `intentos + 1`.
R6. SI el documento no existe, no está aprobado, está en la papelera, se aprobó
antes de DESDE o DESDE está vacía, ENTONCES sv9 debe confirmar el mensaje sin
tocar el alta ni llamar a sigrid-api (no hay alta en masa del histórico).
R7. SI el alta está en `registrado` con el adjunto ya colgado, en `ya_en_sigrid`,
o en `en_curso`/`incierto` con menos tiempo que la Espera, ENTONCES sv9 debe
confirmar el mensaje sin cambiar nada.
R8. SI el alta está en `en_curso` con más tiempo que la Espera, ENTONCES sv9
debe pasarla a `incierto` y parar, sin llamar a sigrid-api.
R9. Tras R5, toda salida de sv9 (también por excepción) debe dejar el alta fuera
de `en_curso`: `incierto` si la grabación estaba en vuelo, `error` si no.

## C. Validación local (sin llamar a sigrid-api)

R10. sv9 debe declarar `no_admitido`, con **todos** los motivos a la vez, si se
da cualquiera de estos casos (código del motivo entre paréntesis): falta obra
(`falta_obra`), CIF (`falta_cif`) o número de albarán (`falta_numero_albaran`);
número de más de 128 caracteres (`numero_albaran_largo`); fecha que no es
`AAAA-MM-DD` válida (`fecha_no_valida`); valoración inexistente o con `status`
distinto de `ok` (`valoracion_no_ok`); valoración sin `contrato_codigo`
(`sin_contrato`); ninguna línea a registrar (`sin_lineas`); línea con cantidad
negativa (`cantidad_negativa`) o con cantidad pero sin `cantidad_convertida`
(`cantidad_sin_convertir`); línea a registrar sin `matched_contrato_line_id`
o con `derived_contrato_line_id` (`linea_fuera_de_contrato`); línea de
contrato sin `sigrid_ide` o de otro contrato (`linea_de_contrato_no_valida`);
partida final distinta de la de su línea de contrato (`partida_distinta_de_contrato`).
R11. Para comparar partidas, sv9 debe tratar como iguales el vacío y el nulo,
y una línea en almacén (partida vacía con marca de F-051) solo casa con una
línea de contrato sin partida.
R12. CUANDO el documento es admisible, sv9 debe construir la petición de
`sigrid/albaran` con `cod_contrato` = contrato de la valoración, `cod_obra`,
`cif_proveedor`, `su_referencia` = número de albarán sin espacios sobrantes,
`fecha_albaran` = fecha en `AAAAMMDD`, `empide` = `ALTA_SIGRID_EMPIDE` o nulo, y
una línea recibida por cada `sigrid_ide`, con la suma de sus cantidades convertidas.
R13. sv9 debe dejar fuera de la petición las líneas con cantidad convertida 0.

## D. Duplicados

R14. Antes de la previa, sv9 debe buscar en Sigrid (`sql/read`) los albaranes
de compra (`con.tip` 14) con el mismo CIF (`dca.entcif`) y referencia
(`dca.entref`); si hay alguno, el alta pasa a `ya_en_sigrid` con sus `ide` y
`cod`, sin previa ni grabación. Aplica en los dos modos.
R15. CUANDO se retoma un alta `incierto` (pasada la Espera), sv9 debe hacer R14
antes que nada; con un único resultado debe pasarla a `registrado` con ese
`ide` y `cod` y seguir con el adjunto (R22), sin crear otro albarán.

## E. Previa y comparación

R16. sv9 debe hacer la previa en los dos modos y guardar petición y respuesta
(código provisional, líneas, totales y avisos).
R17. sv9 debe pasar el alta a `revisar`, con motivo, si en la previa: el total
de una línea difiere de la suma de `importe_calculado` de sus líneas en más de
`ALTA_SIGRID_TOLERANCIA_EUR` (defecto 0,05) (`importe_distinto`); aparece una
línea que no se pidió o falta una pedida (`lineas_distintas`); o algún aviso
contiene un texto de `ALTA_SIGRID_AVISOS_BLOQUEANTES` (`aviso_bloqueante`).
R18. SI la previa responde 400, ENTONCES el alta pasa a `error` con el mensaje
de sigrid-api.
R19. MIENTRAS el modo sea `simulacion`, una previa sin motivos debe dejar el
alta en `simulado`, y sv9 no debe mandar nunca `commit=true` a ningún endpoint.

## F. Grabación real

R20. DONDE el modo sea `real`, tras una previa sin motivos sv9 debe repetir la
misma petición con `commit=true` **una sola vez**, sin reintento automático, y
con `ok` y `committed` guardar `con_ide` y `cod` y pasar a `registrado`.
R21. SI la grabación responde 4xx, ENTONCES el alta pasa a `error`; SI hay
tiempo agotado, error de conexión o 5xx, ENTONCES pasa a `incierto`.
R22. CUANDO un alta queda `registrado` en modo `real`, sv9 debe adjuntar el PDF
del albarán (bajado de SharePoint) con `sigrid/concepto-grafico` (`contip` 14,
`gratipide` 0, `usu` = `ALTA_SIGRID_USUARIO`, `sha256`, `commit=true`) y dar
el adjunto por colgado solo si `ok` y (`committed` o `idempotente`).
R23. SI el adjunto falla, ENTONCES el alta sigue `registrado` con el adjunto en
error, y un nuevo mensaje de alta solo reintenta el adjunto.
R24. sv9 debe reintentar con espera creciente las lecturas, las previas y el
adjunto ante fallos transitorios, y nunca la grabación de R20.

## G. Bloqueo en sv4

R25. MIENTRAS el alta sea bloqueante, sv4 debe rechazar desaprobar, guardar,
deshacer, borrar, purgar, revalorar, volver a buscar contratos y toda edición de
líneas, sin cambiar nada y con el aviso «Registrado en Sigrid como {cod}:
corrígelo en Sigrid y pulsa "Ya lo he anulado en Sigrid"» (sin `cod` si aún no hay).
R26. Las operaciones de R25 que escriben en BBDD deben comprobar el alta dentro
de su transacción, con la fila del merge bloqueada (`FOR UPDATE`).
R27. El borrado múltiple y el vaciado de la papelera deben saltarse los
documentos bloqueantes y decir cuántos se han saltado.
R28. CUANDO el revisor pulsa «Ya lo he anulado en Sigrid» en un alta
`registrado`, sv4 debe publicar `accion="verificar_anulacion"`; sv9 debe pasar
el alta a `anulado` solo si `sql/read` no encuentra ese `con.ide`, y si lo
encuentra dejarla `registrado` con el aviso «sigue en Sigrid».

## H. Visibilidad en sv4

R29. MIENTRAS DESDE no esté vacía, la ficha de un documento aprobado debe
enseñar el alta: estado, modo, `cod` (en simulación, «se habría creado» con el
código provisional), líneas y total de la previa, motivos, avisos y adjunto.
R30. La ficha debe ofrecer «Solicitar alta en Sigrid» (que publica
`accion="alta"`) si el documento aprobado tiene `approved_at_utc` ≥ DESDE y
el alta falta o está en `no_admitido`, `revisar`, `error`, `simulado` o
`anulado`, o en `incierto`/`en_curso` pasada la Espera.
R31. El listado debe mostrar, en cada documento aprobado con alta, su estado.

## I. Contratos y seguridad

R32. `MensajeFeedback` debe aceptar `accion` ∈ {`alta`, `verificar_anulacion`}
con defecto `alta`: un mensaje sin el campo se lee como alta.
R33. sv9 solo debe llamar a `sql/read`, `sigrid/albaran` y
`sigrid/concepto-grafico`; nunca a `sql/write` ni a `sigrid/albaran-directo`.
R34. Solo sv9 debe escribir en `albaran_altas_sigrid`; sv4 solo la lee.
R35. Ni los logs ni el alta deben guardar la clave de sigrid-api ni el PDF.
R36. El DDL de `albaran_altas_sigrid` debe vivir en sv3 y ser idempotente.
