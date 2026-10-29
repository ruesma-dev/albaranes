# F-112 · El año del albarán se lee con la fecha del correo como referencia · Requisitos (v1)

Servicio: **sv2** (`services/albaranes-api`). Banco de evals (`evals/`) para medir. Rigor `estandar`.
Ficha en `harness/features.json` (F-112). Va **después de F-106**. Medición de partida en `progress/spec_F-112.md` §1.

Principio (decisión del humano): **la fecha la lee la IA**. Ningún componente corrige `cabecera.fecha` de forma
determinista; la referencia solo se le da a la IA para que lea mejor el año. La red de sv3
(`fecha_albaran_fuera_de_rango`) y la de sv9 (`fecha_no_plausible`) siguen como están.

## Glosario
- **Recepción**: `ContextoCorreo.recibido_utc` (el `receivedDateTime` de Graph que sv1 guarda en el blob lateral
  `input/{document_id}.correo.json` desde F-048).
- **Fecha de recepción**: la fecha (`date`) de los 10 primeros caracteres de la Recepción, en UTC.
- **Bloque de recepción**: el texto que sustituye al marcador `{fecha_recepcion}` del task de fase 1.
- **Nota sin recepción**: el texto fijo que lo sustituye cuando no hay Fecha de recepción.
- **Juegos del comparador**: A (documentos de producción con el año mal), B (banco, referencia realista), C (banco con
  albarán de verdad antiguo). Definidos en R19.

## A. La referencia en sv2
R1. CUANDO `fecha_recepcion_de` reciba un `ContextoCorreo` cuyo `recibido_utc` empiece por una fecha ISO válida
(`2026-10-28T07:12:00Z`, `2026-10-28`), sv2 debe devolver esa fecha como `date`.
R2. SI el contexto es `None`, o `recibido_utc` es `None`, vacío o no empieza por una fecha ISO válida, ENTONCES
`fecha_recepcion_de` debe devolver `None` sin lanzar excepción.
R3. CUANDO `render_fecha_recepcion` reciba una fecha, sv2 debe devolver un texto fijo que contiene esa fecha en
formato `AAAA-MM-DD` y que dice: que es la fecha de llegada y no la del albarán; que sirve solo para el AÑO; que el día y
el mes se leen siempre del papel; y que sin fecha en el papel `cabecera.fecha` es null y nunca se copia la referencia.
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
R17. `config/revision_rules.yaml` debe tener la regla `anio_fecha_recepcion` (titulo, descripcion y ejemplo, design
§4.2), y `RevisionRulesRepository.render_for_prompt()` debe incluirla.
R18. Los cuatro prompts `albaran_revision_fase2_*` deben seguir conteniendo `{prompt_fase_1}` y `{revision_rules}`
(así reciben el Bloque y la regla sin tocarlos).

## E. Medición: `python -m evals.comparar_fecha`
R19. El comparador debe construir los juegos así: **A**, de `evals/casos_fecha.json` (caso, tipología, fecha esperada
y fecha de recepción reales); **B**, los casos de `evals/fixtures/IA1/` con fecha esperada, con referencia = esperada +
7 días; **C**, los casos del banco con fecha esperada anterior a 2025-01-01, con referencia = esperada + 730 días.
R20. Por caso, variante (`base`: YAML de `--base`, por defecto `dev`; `rama`: los de la rama) y repetición, debe
ejecutar IA1 y luego IA2 (prompt de fase 2 según la tipología), con la referencia del juego, sin correo, sin lista de
obras y sin Sigrid, con los proveedores de `IA_PRIMERA_FASE` e `IA_SEGUNDA_FASE`.
R21. Cada fecha devuelta tras IA1 y tras IA2 debe clasificarse en `exacta`, `referencia` (igual a la referencia y
distinta de la esperada), `solo_anio` (mismo día y mes que la esperada, otro año), `otra`, `nula` o `error`; con
varias repeticiones, la categoría del caso es la mayoritaria y un empate es `inestable`.
R22. El veredicto debe ser VERDE solo si se cumplen todos: **C1** en A, casos con mayoría `exacta` tras IA2 en rama
≥ el umbral de design §7 y ≥ base; **C2** en B, ningún caso con mayoría `exacta` en base la pierde en rama; **C3** en C,
ningún caso con mayoría `exacta` en base pasa a `solo_anio` o `referencia` en rama; **C4** 0 ejecuciones `referencia`
en rama, en cualquier juego y fase. Sin las dos variantes, el veredicto es NO APLICA.
R23. SI falta la clave de un proveedor, ningún caso tiene albarán, `casos_fecha.json` no valida (campos, formato de
fecha, `caso_id` repetido) o el `git show` de la base falla, ENTONCES el comparador debe parar con código 2 antes de
llamar a ninguna IA, con un mensaje que no cite el contenido de ningún fichero. Con `--solo-validar` hace esas
comprobaciones y sale sin llamar a ninguna IA (código 0 si todo valida).
R24. El comparador debe escribir el detalle en `evals/salidas/comparar_fecha/<fecha-hora>/` (ignorado por git) y el
resumen en `progress/comparar_fecha_F-112.md`: recuentos por juego, variante, fase y categoría, `caso_id` por
categoría y veredicto, **sin** proveedor, CIF, número de albarán ni fechas leídas.

## F. Declaraciones y documentación
R25. `harness/rutas_sensibles.json` debe declarar `services/albaranes-api/application/services/fecha_recepcion.py`
en la verificación `evals`.
R26. `docs/ARCHITECTURE.md` debe recoger la regla 26 (la recepción es referencia del año, la fecha la lee la IA y
nadie la corrige), y `services/albaranes-api/sv2.md` y `evals/README.md`, el marcador y el comparador.

## Verificación manual (fuera de los tests)
- M1 (líder, solo lectura; humano): montar el juego A (design §7.1).
- M2 (humano, de pago): `python -m evals.comparar_fecha --variante ambas` y veredicto VERDE.
- M3 (humano): despliegue de sv2. M4 (líder, solo lectura): medición en producción a las dos semanas (design §8).
