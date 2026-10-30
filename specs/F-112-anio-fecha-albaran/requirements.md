# F-112 · El año del albarán se lee con la fecha del correo como referencia · Requisitos (v1.3)

Servicio: **sv2** (`services/albaranes-api`). Banco de evals (`evals/`) para medir. Rigor `estandar`.
Ficha en `harness/features.json` (F-112). Va **después de F-106**. Medición de partida en `progress/spec_F-112.md` §1.

Principio (decisión del humano): **la fecha la lee la IA**. Ningún componente corrige `cabecera.fecha` de forma
determinista; la referencia solo se le da a la IA para que lea mejor el año. La red de sv3
(`fecha_albaran_fuera_de_rango`) y la de sv9 (`fecha_no_plausible`) siguen como están.

**Enmienda v1.1 (2026-10-30, PARADA 1).** Palabras del humano: «añade que ia2 revisara tambien la fecha. el problema
vendra cuando estemos en un cambio de año (diciembre o enero)». Cambian R3, R17, R18, R19, R21 y R22; nuevos R27–R29.
D7 = 416 llamadas (decidida). **v1.2 (2026-10-30)**: juego A leído en el papel (`progress/juego_a_F-112.md`); cambian el
glosario (Regla del año), R19 y R22 (C7). **v1.3 (2026-10-30)**: el humano elige **D2 = (b)**, día de recepción en
Europe/Madrid; cambian el glosario, R1, R2 y R27 (SIN-006, Nochevieja); nuevo R30. **PARADA 1 cerrada**.

## Glosario
- **Recepción**: `ContextoCorreo.recibido_utc` (el `receivedDateTime` de Graph que sv1 guarda en el blob lateral
  `input/{document_id}.correo.json` desde F-048).
- **Fecha de recepción**: el día (`date`) de la Recepción pasada a la hora de Europe/Madrid (D2 = b), no la fecha
  UTC: un correo de las 23:30 UTC del 31-12 es del 01-01 en Madrid.
- **Bloque de recepción**: el texto que sustituye al marcador `{fecha_recepcion}` del task de fase 1.
- **Nota sin recepción**: el texto fijo que lo sustituye cuando no hay Fecha de recepción.
- **Bloque de revisión de fecha**: el texto que sustituye al marcador `{revision_fecha}` de los prompts de fase 2.
- **Regla del año**: la fecha del albarán es IGUAL o algo ANTERIOR a la de recepción; el año es el que deja la fecha
  del papel (día y mes) en la recepción o poco antes: si día y mes caen DESPUÉS del día y mes de la recepción, el año
  es el ANTERIOR al de la recepción (28-12 con correo del 03-01 ⇒ año anterior). Un año legible y plausible del papel
  manda: no se inventa otro. El año nunca sale de una referencia normativa impresa (R.D., Orden, Ley). Plausible =
  la fecha queda entre un año antes de la recepción y pocos días después.
- **Juegos del comparador**: A (documentos de producción con el año mal), B (banco, referencia realista), C (banco con
  albarán de verdad antiguo), D (sintéticos de cambio de año). Definidos en R19 y R27.

## A. La referencia en sv2
R1. CUANDO `fecha_recepcion_de` reciba un `ContextoCorreo` cuyo `recibido_utc` sea una fecha-hora ISO válida (con `Z`,
con desfase o sin zona, que se toma como UTC), sv2 debe devolver el día en Europe/Madrid: `2026-10-28T07:12:00Z` ⇒
2026-10-28; `2026-12-31T23:30:00Z` ⇒ **2027-01-01** (Nochevieja, CET); `2026-07-15T22:30:00Z` ⇒ 2026-07-16 (CEST);
`2026-12-31T22:59:59Z` ⇒ 2026-12-31. Una fecha sola (`2026-10-28`) se devuelve tal cual.
R2. SI el contexto es `None`, o `recibido_utc` es `None`, vacío o no es una fecha ni fecha-hora ISO válida, ENTONCES
`fecha_recepcion_de` debe devolver `None` sin lanzar excepción.
R3. CUANDO `render_fecha_recepcion` reciba una fecha, sv2 debe devolver un texto fijo que contiene esa fecha en
formato `AAAA-MM-DD` y que dice: que es la fecha de llegada y no la del albarán; que sirve solo para el AÑO; la Regla
del año, con el ejemplo 28-12 / 03-01; que el día y el mes se leen siempre del papel; que un año legible y plausible
del papel manda; y que sin fecha en el papel `cabecera.fecha` es null y nunca se copia la referencia.
R4. CUANDO `render_fecha_recepcion` reciba `None`, sv2 debe devolver la Nota sin recepción.
R5. El Bloque de recepción no debe contener ningún carácter de `recibido_utc` más allá de la fecha ya validada
(un `recibido_utc` con texto añadido detrás de la fecha produce el mismo bloque que la fecha sola).

## B. Montaje del prompt
R6. CUANDO el task de fase 1 contenga `{fecha_recepcion}`, `_render_task_fase_1` debe sustituirlo por el Bloque de
recepción o, sin fecha, por la Nota sin recepción.
R7. La sustitución de `{fecha_recepcion}` debe hacerse ANTES que la de `{contexto_correo}`: un correo cuyo texto
contenga el literal `{fecha_recepcion}` debe llegar a la IA con el literal intacto (F-048 R12).
R8. SI el task de fase 1 no contiene `{fecha_recepcion}`, ENTONCES el task renderizado debe ser idéntico, byte a byte,
al que se obtiene sin fecha de recepción (no se añade nada al final).
R9. `extract_phase_1` y `review_phase_2` deben aceptar `fecha_recepcion: date | None = None`; con el mismo valor, las
instrucciones de IA1 y el `{prompt_fase_1}` que recibe IA2 deben llevar el MISMO Bloque de recepción.
R10. Las líneas de log de fase 1 y de fase 2 deben incluir `fecha_recepcion=AAAA-MM-DD` o `fecha_recepcion=NO`.
R11. CUANDO la IA devuelva una `cabecera.fecha` (cualquiera, también una a más de un año de la referencia), el
envelope de fase 1 y el de fase 2 deben llevar exactamente la fecha devuelta por la IA: sv2 no la toca.

## C. Pipeline y worker
R12. `ExtractAlbaranRequest` y `ReviewAlbaranRequest` deben tener `fecha_recepcion: date | None = None`, y el pipeline
debe pasarla tal cual a `extract_phase_1` y a `review_phase_2`.
R13. CUANDO el worker procese un mensaje con correo, debe calcular la Fecha de recepción con `fecha_recepcion_de` una
sola vez y pasar la MISMA a la fase 1 y a la fase 2.
R14. SI el mensaje no trae correo (sin `correo_blob`, blob ausente o ilegible), ENTONCES el worker debe pasar
`fecha_recepcion=None` a las dos fases y seguir como hoy (sin fallo, sin poison).

## D. Prompts y checklist (YAML)
R15. El task de `albaran_factura_es` (`config/prompts.yaml`) debe contener `{fecha_recepcion}` exactamente una vez,
dentro de «Reglas para la cabecera», justo después de la regla de `fecha`.
R16. La regla de `fecha` de ese task debe decir que el día y el mes salen siempre del papel y que el año se contrasta
con la fecha de recepción (texto en design §4.1).
R17. IA2 debe revisar SIEMPRE la fecha, no como una regla más de la checklist: cada uno de los cuatro prompts
`albaran_revision_fase2_*` debe contener `{revision_fecha}` exactamente una vez, en una sección propia «Fecha del
albarán (revisión obligatoria)», y `review_phase_2` debe sustituirlo en la misma pasada única que los demás marcadores
de fase 2 (F-048 R14) por `render_revision_fecha(fecha_recepcion)` (texto en design §4.2).
R18. CUANDO haya Fecha de recepción, el Bloque de revisión de fecha debe llevarla en `AAAA-MM-DD` y ordenar: comparar
`cabecera.fecha` de fase 1 con ella aplicando la Regla del año; corregir solo el año cuando el papel lo admita, con un
razonamiento de campo `cabecera.fecha` y `patron_aplicado` `anio_fecha_recepcion`; no tocarla si el papel trae un año
legible y plausible. SIN Fecha de recepción, debe ser una nota fija («revisa la fecha solo contra el papel»). Los cuatro
prompts deben seguir conteniendo `{prompt_fase_1}`; `revision_rules.yaml` no gana regla de fecha.

## E. Medición: `python -m evals.comparar_fecha`
R19. El comparador debe construir los juegos así: **A**, de `evals/casos_fecha.json` (caso, tipología, `clase` `anio`,
`dudoso` o `antigua`, fecha esperada y fecha de recepción reales); **B**, los casos de `evals/fixtures/IA1/` con fecha esperada, con referencia = esperada +
7 días; **C**, los casos del banco con fecha esperada anterior a 2025-01-01, con referencia = esperada + 730 días;
**D**, los sintéticos de R27. B va muestreado a 20 casos con semilla fija (D7: 416 llamadas en total con A, B y C a
2 repeticiones, más las de D).
R20. Por caso, variante (`base`: YAML de `--base`, por defecto `dev`; `rama`: los de la rama) y repetición, debe
ejecutar IA1 y luego IA2 (prompt de fase 2 según la tipología), con la referencia del juego, sin correo, sin lista de
obras y sin Sigrid, con los proveedores de `IA_PRIMERA_FASE` e `IA_SEGUNDA_FASE`.
R21. Cada fecha devuelta tras IA1 y tras IA2 debe clasificarse en `exacta`, `referencia` (igual a la referencia y
distinta de la esperada), `solo_anio` (mismo día y mes que la esperada, otro año), `otra`, `nula` o `error`; con
varias repeticiones, la categoría del caso es la mayoritaria y un empate es `inestable`. Además, por ejecución, el
**efecto de IA2** (fecha de IA1 frente a la final): `corrige` (IA1 no exacta, final exacta), `estropea` (IA1 exacta,
final no), `cambia` (las dos no exactas y distintas) o `igual`, con recuento propio por juego y variante (R29).
R22. El veredicto debe ser VERDE solo si se cumplen todos: **C1** en A, casos con mayoría `exacta` tras IA2 en rama
≥ el umbral de design §7 y ≥ base; **C2** en B, ningún caso con mayoría `exacta` en base la pierde en rama; **C3** en C,
ningún caso con mayoría `exacta` en base pasa a `solo_anio` o `referencia` en rama; **C4** 0 ejecuciones `referencia`
en rama, en cualquier juego y fase; **C5** en rama, 0 ejecuciones `estropea` de IA2 en cualquier juego; **C6** en D,
todos los casos con mayoría `exacta` tras IA2 en rama; **C7** en A, los casos `antigua`, todos con mayoría `exacta`
tras IA2 en rama. C1 cuenta solo los `anio` (un `dudoso` entra si el humano lo pasa a `anio`). Sin las dos variantes, el veredicto es NO APLICA.
R23. SI falta la clave de un proveedor, ningún caso tiene albarán, `casos_fecha.json` no valida (campos, formato de
fecha, `caso_id` repetido) o el `git show` de la base falla, ENTONCES el comparador debe parar con código 2 antes de
llamar a ninguna IA, con un mensaje que no cite el contenido de ningún fichero. Con `--solo-validar` hace esas
comprobaciones y sale sin llamar a ninguna IA (código 0 si todo valida).
R24. El comparador debe escribir el detalle en `evals/salidas/comparar_fecha/<fecha-hora>/` (ignorado por git) y el
resumen en `progress/comparar_fecha_F-112.md`: recuentos por juego, variante, fase y categoría, `caso_id` por
categoría y veredicto, **sin** proveedor, CIF, número de albarán ni fechas leídas.

R27. `python -m evals.sinteticos_fecha` debe generar, de forma determinista, las imágenes de los casos sintéticos en
`evals/inputs/albaranes/` (ignorado por git) y `evals/casos_fecha_sinteticos.json` (versionado) con: **SIN-001** papel
«28/12» sin año, correo 2027-01-03 ⇒ 2026-12-28; **SIN-002** papel «02/01» sin año, correo 2027-01-05 ⇒ 2027-01-02;
**SIN-003** papel «15/12» sin año, correo 2026-12-18 ⇒ 2026-12-15; **SIN-004** papel «28/12/2026» legible, correo
2027-01-03 ⇒ 2026-12-28 (no se pasa a 2027); **SIN-005** papel «30/12/25» con año de dos cifras, correo 2026-01-02 ⇒
2025-12-30; **SIN-006** (Nochevieja) papel «01/01» sin año, correo `2026-12-31T23:30:00Z` ⇒ referencia 2027-01-01 ⇒
2027-01-01. Los casos D guardan `recibido_utc` y el comparador saca su referencia con `fecha_recepcion_de` (R1). Dos
ejecuciones dan los mismos bytes.
R28. CUANDO `render_fecha_recepcion` y `render_revision_fecha` reciban una fecha de enero, el texto debe ser el mismo
que con cualquier otra fecha salvo la propia fecha (la Regla del año va siempre, no solo en enero).
R29. El resumen de R24 debe traer una tabla propia del efecto de IA2 (R21) por juego y variante, y la lista de
`caso_id` con `estropea`.

R30. La conversión a Europe/Madrid debe funcionar igual en Windows y en el contenedor: sv2 declara `tzdata` en
`infra/manifests/sv2/requirements.txt`, y un test fija los cuatro ejemplos de R1 sin depender de la zona del sistema.

## F. Declaraciones y documentación
R25. `harness/rutas_sensibles.json` debe declarar `services/albaranes-api/application/services/fecha_recepcion.py`
en la verificación `evals`.
R26. `docs/ARCHITECTURE.md` debe recoger la regla 26 (la recepción es referencia del año, la fecha la lee la IA y
nadie la corrige), y `services/albaranes-api/sv2.md` y `evals/README.md`, el marcador y el comparador.

## Verificación manual (fuera de los tests)
- M1 (líder, solo lectura en PostgreSQL y en Blob, con permiso del humano): montar el juego A (design §7.1).
- M2 (humano, de pago): `python -m evals.comparar_fecha --variante ambas` (A, B a 20, C y D) y veredicto VERDE.
- M3 (humano): despliegue de sv2. M4 (líder, solo lectura): medición en producción a las dos semanas (design §8).
