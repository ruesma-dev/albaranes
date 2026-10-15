# F-070 · La obra siempre con el 0 inicial (salvo VAR y POSTV2) — requisitos

Rigor **critico** (producción, y sv9 escribe en el ERP). Servicios: **comun**, **sv3-persistencia**,
**sv4-front** y **sv9-alta-sigrid**. Urgente, prioridad 1. Informe de spec: `progress/spec_F-070.md`.

## Origen (diagnóstico del líder, 2026-10-14, producción, solo lectura)

Albaranes de HERMANOS SAN JUAN (obra 0686, contrato CTSU24/0524): el combo de partida de sv4 solo
ofrece «Almacén». El merge tiene `obra_codigo = "686"` y sv4 pregunta a sigrid-api con «686»:
partidas 0 (con 0686, 2412), contratos 0 (117) y proveedores 0 (115). En la bandeja hay 5
pendientes con obra de 3 cifras (686, 711, 723). sv9 mandaría `cod_obra = "686"` y el alta fallaría.

Regla del humano (literal): «es crucial que añada el 0 inicial si no es VAR ni POSTV2». VAR y
POSTV2 son códigos válidos y se dejan tal cual.

Comprobado en Sigrid (sigrid-api, solo lectura, 2026-10-14; detalle en `progress/spec_F-070.md` §2):
VAR («OBRAS VARIAS») y POSTV2 («POSTVENTA 2») existen como `con.cod` de obra en la empresa 1 (y en
la 28); con «686», «711» o «723» no hay obra, con «0686», «0711» y «0723» sí.

## Definiciones

- **Código canónico**: el que devuelve `normalizar_codigo_obra` (R1–R3).
- **Canonizar**: `canonizar_codigo_obra` (R4): el canónico si lo hay; si no, el valor tal cual.
- **Códigos sin cero**: VAR y POSTV2 (R2), en una sola constante de comun.

## Comun · un único punto (`ruesma_comun.obras`)

R1. `normalizar_codigo_obra(valor)` debe devolver, sobre el valor recortado: con 3 dígitos, `0`
delante (`686` ⇒ `0686`, también el entero `686`); con 4 dígitos que empiezan por `0`, el mismo
(`0686`). Sin cambios respecto a hoy.

R2. CUANDO el valor recortado sea VAR o POSTV2 en cualquier combinación de mayúsculas y minúsculas
(`var`, ` Postv2 `), `normalizar_codigo_obra` debe devolver `VAR` o `POSTV2` en mayúsculas.

R3. SI el valor es cualquier otra cosa (vacío, `None`, 1–2 dígitos, 4 dígitos sin `0` inicial,
5 o más dígitos, `GG`, `0578-B`, `POSTV`…), ENTONCES `normalizar_codigo_obra` debe devolver `None`,
como hoy.

R4. `canonizar_codigo_obra(valor)` debe devolver el código canónico si existe y, si no, el valor
recortado (`None` si queda vacío o es `None`). Es idempotente: canonizar dos veces da lo mismo.

R5. VAR y POSTV2 deben estar definidos UNA sola vez, en `ruesma_comun.obras`; ningún módulo de
producción de otro servicio debe repetir esos literales.

## sv3 · donde se guarda la obra

R6. CUANDO sv3 persiste un albarán, el `obra_codigo` de la cabecera (del merge y de cada proveedor)
debe guardarse canonizado sobre la forma limpia de hoy (espacios colapsados y mayúsculas): `686` ⇒
`0686`, `var` ⇒ `VAR`. Un código que no encaja (`1234`) se guarda como hoy, y la red de obra lo sigue
descartando como `obra_codigo_invalido`. Cubre la obra que viene del correo (F-048) y la del papel.

R7. CUANDO el resolver determinista de cabecera deduzca la obra por texto, debe escribir el código
canonizado (una obra de Sigrid `227` se escribe `0227`).

R8. MIENTRAS el merge tenga obra VAR o POSTV2, sv3 debe tratarla como válida: la red de obra la
consulta en Sigrid con ese código y no la descarta por código inválido, el resolver no la sustituye
por una deducida por texto y la usa como obra efectiva para el proveedor, y la búsqueda de contratos
busca en esa obra y sella el rastro con `VAR`/`POSTV2`.

R9. sv3 no debe reescribir el `obra_codigo` de merges ya guardados fuera de los caminos de R6 y R7
(sin migración, sin UPDATE masivo), ni cambiar `obra_codigo_origen` al canonizar.

## sv4 · consultas a Sigrid y guardado

R10. CUANDO sv4 consulte a sigrid-api los proveedores, los contratos o las partidas de una obra
(combos de cabecera, búsqueda de contratos en vivo y combo de partida), debe mandar el código
canonizado: con `686` pregunta por `0686`, con ` var ` por `VAR`.

R11. SI el código no encaja (`GG`, `1234`), ENTONCES sv4 debe mandarlo tal cual, recortado, como hoy;
y SI está vacío, no debe consultar, como hoy.

R12. CUANDO el revisor guarde la cabecera de un albarán, sv4 debe guardar el `obra_codigo`
canonizado (`686` ⇒ `0686`); un código que no encaja se guarda recortado, como hoy.

R13. El estado de la búsqueda de contratos de sv4 (vigente o desfasada) debe compararse con la misma
normalización: un merge con `VAR` y un rastro sellado con `VAR` coinciden, y uno con `686` coincide
con un rastro `0686`.

## sv9 · alta en Sigrid

R14. CUANDO sv9 construya la petición de alta, `cod_obra` debe ir canonizado: `686` ⇒ `0686`,
`var` ⇒ `VAR`, `POSTV2` ⇒ `POSTV2`; un código que no encaja va recortado, como hoy (y Sigrid responde
como hoy).

R15. Los motivos locales de la obra (`falta_obra`, `campo_demasiado_largo` de `cod_obra`) deben
evaluarse sobre el código canonizado; el resto de la petición no cambia.

## Datos ya guardados y fronteras

R16. La feature no debe escribir en producción. Los merges guardados con obra de 3 cifras quedan
cubiertos por R10 (consultas), R12 (al guardarlos) y R14 (alta). Medirlos es opcional y solo de
lectura (T0, MANUAL del humano).

R17. sv2 (resolver de `origen_datos` y su `normalizar_codigo` de COMPARACIÓN), sv1, sv5 y sv6 no deben
cambiar; tampoco las SQL de Sigrid ni ningún esquema de BBDD.

## Documentación

R18. `docs/ARCHITECTURE.md` debe recoger la regla (código canónico, excepciones y dónde se aplica) y
que `ruesma_comun.obras` lo importan sv3, sv4 y sv9; `azure-apps/albaranes.md`, el formato de
`obra_codigo` del merge.

## Trazabilidad

Cada R tiene al menos un test `test_f070_rN_*`; los de comun, sv3, sv4 y sv9 sin red ni BBDD real
(MockTransport, dobles y el SQLite de los tests de sv4). R16 se verifica con la MANUAL T0 y T13.
