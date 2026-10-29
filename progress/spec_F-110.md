# F-110 · spec v1 (spec-author, 2026-10-28)

Spec en `specs/F-110-descuento-linea-sigrid/` (requirements 116/150, design 187/250, tasks T0–T23), rama
`feature/F-110-descuento-linea-sigrid` (worktree `../albaranes-F-110`, desde `dev` 43e87e5). Rigor `critico`.
Servicios: comun, sv9, sv4, `infra/` y documentación. Sin DDL ni colas. **Va después de F-106** (T0 lo exige) y no
repite sus requisitos: cambia solo su `linea_a_sigrid`, reutiliza su `linea_no_cuadra` y su «A Sigrid».

## Qué propone

- comun: `linea_a_sigrid(..., precio, descuento, con_descuento)` devuelve cantidad, precio y `dto`. Sin descuento o con
  la guarda apagada, igual que F-106. Con descuento y la guarda encendida, `dto = round(d, 2)` y el precio es P si da
  el importe al céntimo con la cantidad enviada; si no, el bruto despejado (design §5).
- sv9: la guarda `ALTA_SIGRID_ENVIAR_DTO` (solo el literal `true`, apagada por defecto, mismo valor en sv4 por
  `AltaSigridEnvComun`). Con ella encendida, la petición lleva `dto` en las líneas con descuento. Antes de llamar a
  sigrid-api se comprueba que la línea cuadra a Sigrid (`linea_no_cuadra`). En la previa, el motivo `dto_distinto` va a
  `revisar` si Sigrid no devuelve el `dto` pedido.
- sv4: «A Sigrid: 12 × 0,645 € −7 %» en la ficha, la columna «Dto %» en el panel y el texto de `dto_distinto`.
- El script R18 de F-106 entiende el `dto`. Documentación: `ARCHITECTURE` regla 19, `sv9.md` y `azure-apps/albaranes.md`.
  `sigrid_api.md` no se toca: es de sigrid-api.

## Medición en producción (solo lectura, `default_transaction_read_only=on`; contraseña de Key Vault solo en variable de entorno)

- 100 líneas con descuento (39 documentos), todas con un d en (0, 100) y como mucho 2 decimales. Por proveedor:
  FEYMACO 42, IBERFERRETERIA 28, CECOIS 22, RONDÓN 4 y TEYMO 4. **No es solo CECOIS.**
- 91 de las 100 dan el importe exacto al céntimo con P. Hay 2 a 1–2 céntimos y 7 que no cuadran (esas las para F-106).
  Ejemplo: CECOIS A 26018351, 12 × 0,645 −7 % = 7,20, se mandó 0,60; el despeje puro daría 0,645161.
- Las 9 vinculadas con descuento son de FEYMACO (d 40). Su `ctrpro` tiene `dto` vacío y un precio que no es el del
  albarán (4500, 1000 y 3000, bolsas).
- `albaran_contrato_lines_merge.descuentos` está a nulo en sus 3198 líneas: albaranes no puede validar el `dto` del contrato.
- 11 altas reales `registrado` y 1 `ya_en_sigrid` llevan líneas con descuento, todas mandadas en neto.

## Decisiones para la PARADA 1 (design §10; recomendada la (a) en todas)

- **D0**: F-095 es el mismo problema ⇒ propuesta: queda absorbida por F-110. Si se acepta, la marca el líder en
  `features.json`.
- **D1**: precio con `dto` = P si da el importe al céntimo; si no, el despejado.
- **D2**: la guarda, con el mismo valor en sv4 y sv9. Apagarla es la vuelta atrás.
- **D3**: las vinculadas siguen la misma regla. Valida sigrid-api, y solo cuando el precio cuadre con el contrato.
- **D4**: si se pidió `dto` y la previa no lo devuelve, `dto_distinto`.
- **D5**: las 11 altas ya grabadas no se reenvían. Las lista el líder (T20) y el humano decide.
- **D6**: un descuento inválido va como hoy, sin `dto`; uno con más de 2 decimales se redondea.
- **D7**: no se pide a sigrid-api un `importe` por línea.

## Depende de la forma final del contrato de sigrid-api (F-018, sin publicar)

El contrato está SUPUESTO en design §4: `lineas[].dto?` es un número con 0 < dto < 100 y 2 decimales, y la previa
devuelve `dto` por línea. La T18 lo contrasta cuando se publique. La T19 añade los códigos nuevos. Si el contrato
cambia una R, se para.

**Para que el líder lo traslade a sigrid-api** (este agente no ha hablado con su sesión):

1. Las 9 vinculadas de FEYMACO: validar el `dto` contra el `ctrpro` sin la condición H14 C las rechazaría.
2. ¿Con cuántos decimales guarda Sigrid el precio? Se manda con 6.
3. Que la previa devuelva `dto`.
4. ¿El bruto va a `pre` o a `tar`? `sigrid_tablas.md` dice `pre` «Precio» y `tar` «P.Bruto». Su F-018 dice `pre`, y
   nuestra caché lee `ctrpro.tar` como precio bruto.

## MANUAL

Todas las del líder son de solo lectura:

- T1: repetir la medición.
- T17: Chrome con el pipeline local.
- T18: contrastar el contrato.
- T20: listar las altas grabadas en neto (SQL en design §9).
- T22: la primera alta real (PostgreSQL y `dcapro` por `sql/read`).

Del humano es la T21: desplegar con la guarda apagada y, después de la T18, encenderla.

## Notas

- No se ha tocado `features.json` ni `progress/current.md`, para no chocar con el árbol del líder. La entrada de F-110
  en `current.md` la pone el líder.
- El script de la medición quedó en el scratchpad de la sesión y no se versiona.

## Respuesta de sigrid-api a las 4 preguntas (2026-10-28, su F-018, sin aprobar todavía: NO es contrato)

- **`tar` es el bruto** («P.Bruto») y `pre` el neto = `tot`/`can` (medido por ellos en 24.000 líneas con dto, 99,99 %).
  Propuesta con `dto` > 0: `tar` = nuestro `precio`; `dto` = texto «40%» / «1,5%» (coma decimal); `tot` =
  ROUND_HALF_UP(cantidad·precio·(1 − dto/100), 2); `pre` = `tot`/`cantidad`; `mov` y PMP con el neto. Es su P1.
- **Vinculadas con dto**: nunca rechazan por diferencias con el contrato; avisos informativos de línea
  `precio_distinto_del_contrato` (bruto frente a `ctrpro.tar`) y `dto_distinto_del_contrato` (frente a `ctrpro.dto`,
  vacío = 0). Nuestra propuesta de comparar el dto solo si el bruto cuadra va a su humano (con su P3).
- **Decimales**: no redondean el precio; `tot` sobre el producto exacto (Decimal), redondeado a 2 al final.
- **Previa**: cada línea de `previsto` y `creado` trae `dto` (número) y `precio_bruto` (= `tar`); `precio` es el neto y
  `total` el importe; en `idempotente`, `dto` y `precio_bruto` a `null`. Contrato **v8.4** antes de implementar.
- Consecuencia para la spec: D4 (`dto_distinto`) puede leer `dto` de la previa; los dos avisos nuevos van a la tabla de
  textos de sv4 en la T19. Se contrasta todo en la T18 cuando publiquen v8.4.

## Contrato v8.4 de sigrid-api (F-018 v1.2, `02dc4ad`), acusado por albaranes el 2026-10-29

Confirmado por el humano («Sí, y actualizo lo nuestro»). sv9 compara la previa por `total` (0,05 €) y no lee el `precio`
de la respuesta, así que el neto y el céntimo del punto 4 no la rompen. Los avisos desconocidos se ven con su código en sv4
hasta la T19. Falta nuestra parte del contrato (punto 6: «Origen en albaranes» de `precio` y `dto` en §2.2 y regla 4 de
§2.4), coordinada con la sesión de sigrid-api porque el fichero está en su rama.
