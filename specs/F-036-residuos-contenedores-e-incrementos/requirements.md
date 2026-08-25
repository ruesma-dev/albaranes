<!-- specs/F-036-residuos-contenedores-e-incrementos/requirements.md -->
# F-036 · Requisitos (EARS)

Diagnóstico CERRADO y confirmado contra la BBDD real: **tres defectos
independientes** (D1 en sv4, D2 en sv3→sv5→matcher, D3 en sv6/sv5). Evidencia
con fichero:línea en `progress/explore_F-036.md` (con su APÉNDICE) y en
`progress/revision_residuos_salmedina_20260819.md` §9.1–§9.4. Fuera de alcance:
F-017 (fuente OFERTA, SS-0026122), F-021 (partida) y F-006 (canon).

## D1 · sv4 no rehace una conversión que no sabe hacer

R1. MIENTRAS sv4 recalcula los importes de una valoración al guardar, debe
clasificar la conversión de cada línea como REPRODUCIBLE solo si
`factor_conversion` y `cantidad_albaran` guardadas no son NULL y la
`cantidad_convertida` guardada equivale a su producto.

R2. SI la conversión NO es reproducible y la `cantidad_convertida` guardada no
es NULL, ENTONCES sv4 debe CONSERVARLA y calcular el importe con ella, nunca
con la cantidad cruda del albarán.

R3. SI además el revisor cambió la cantidad, ENTONCES sv4 debe conservar
igualmente la `cantidad_convertida`, marcar la línea `review_required` y
añadir a sus razones `front_cantidad_editada_sin_conversion_reproducible`.

R4. SI la conversión NO es reproducible y la `cantidad_convertida` guardada es
NULL, ENTONCES sv4 debe mantener el comportamiento actual (importe con la
cantidad cruda) y sellar la razón `front_sin_cantidad_convertida` SOLO en las
líneas que ese guardado ACTUALIZA: una línea que el guardián de R5 deja
intacta tampoco cambia sus razones. Si no, abrir y guardar un documento
sellaría la razón en todas sus líneas y la traza dejaría de significar nada.

R5. El criterio de «la fila no se toca» (guardián de F-019 R24) debe evaluarse
SOLO por las ENTRADAS —`cantidad_albaran` y descuento saneado—. La
`cantidad_convertida` no puede intervenir en esa comparación.

R6. El sistema debe expresar R1–R5 como regla GENERAL de sv4, válida para
cualquier familia con regla de cálculo propia. Prohibido condicionarla a
`tipo_familia == "residuos"`.

R7. R1–R5 deben ser independientes del valor de `factor_conversion`: con
factor `1.0` y una `cantidad_convertida` distinta del producto, la línea sigue
siendo NO reproducible y se conserva (blindaje ante F-024).

R8. CUANDO la vista de detalle pinta el importe de una línea cuya conversión
no es reproducible, debe mostrar el `importe_calculado` persistido, no el
producto `cantidad × unitario × (1 − dto/100)` recalculado en la plantilla.

## D2 · el contexto de residuos se pierde en sv3 y arrastra a sv5 y al matcher

R9. `_score_contexto` debe puntuar los nueve campos de residuos (`codigo_ler`,
`volumen_m3`, `peso_toneladas`, `contenedores`, `contenedores_entregados`,
`contenedores_retirados`, `carga_incompleta`, `m3_no_transportados`,
`exceso_declarado_min`) además de los cinco actuales.

R10. CUANDO un candidato traiga ÚNICAMENTE campos de residuos, debe puntuar
> 0 y no descartarse.

R11. CUANDO ya hay contexto ganador por score, el sistema debe completar los
nueve campos de R9 que estén a `None` en él con el valor del candidato de mayor
score que sí los traiga, y registrar en el log qué completó y desde qué
proveedor. Un campo con valor en el ganador NO se sobrescribe nunca.

R12. Los cinco campos narrativos que ya puntúan hoy NO se fusionan: llegan
íntegros del contexto ganador.

R13. **RETIRADO por el humano el 2026-08-25** (implementado y revertido, ver
`tasks.md` T11): «es la IA1 la que debe decidir cómo clasifica. No puede ser
determinista. Además, los residuos no se deben clasificar solo porque
contengan LER». sv5 deriva la tipología SOLO del `tipo_familia` del contexto.

R14. El validador y el catálogo LER deben vivir en un único sitio compartido
(`ruesma_comun`), consumido por sv2 y sv6 sin copias (sv5 no: R13 retirado).

R15. SI una línea `from_albaran` de residuos queda casada con una línea de
contrato que tarifa un INCREMENTO por LER, ENTONCES sv6 debe anular ese match,
marcar `review_required` y añadir `residuos_base_casada_con_incremento`.

## D3 · los incrementos por LER no se emiten nunca

R16. CUANDO una línea base de residuos trae `codigo_ler` válido, sv6 debe
inyectar SIEMPRE —tarifada o no— una sintética con
`line_kind='synthetic_modifier'`, `modifier_source='gestion_residuos'`,
`rol_linea='incremento_residuos'`, `descripcion_linea='INCREMENTO LER
<codigo>'` y `parent_merge_line_id` = la línea base.

R17. SI el contrato tarifa ese LER, ENTONCES la sintética lleva su precio. SI
NO lo tarifa, ENTONCES se emite igualmente SIN precio —la «forma C» de la red
M1, con la que queda alineada—, con la razón
`residuos_ler_sin_tarifa_en_contrato`, y esa línea SÍ activa `review_required`:
existe justamente para que el revisor ponga el importe a mano.

R18. SI IA3 ya emitió una sintética equivalente para esa base (mismo LER o rol
`incremento_residuos`), ENTONCES no se duplica.

R19. La cantidad de la sintética de LER se hereda de la línea base (el nº de
contenedores), nunca de los m³ del albarán.

R20. CUANDO el `ModifierContractMatcher` construye el predicado del rol
`incremento_residuos`, SI la descripción de la sintética nombra un código LER,
ENTONCES debe exigir ese código en la descripción de la línea de contrato; si
no lo nombra, mantiene el predicado actual (`RESIDUOS`).

R21. El sistema debe separar el recorrido de líneas base de residuos de la
regla que produce cada sintética, de modo que añadir una regla nueva (el canon
de vertedero de F-006) no obligue a modificar el recorrido.

## Cálculo de contenedores y trazabilidad (decisiones 1 y 4)

R22. El nº de contenedores debe calcularse en este orden: 1) contenedores
EXPLÍCITOS del albarán; 2) `ceil(volumen_m3 / tamaño)`; 3) resta
`contenedores_entregados − contenedores_retirados` cuando ambas vienen y es
>= 1. SI no hay volumen ni resta utilizables, ENTONCES `num_contenedores =
None`, razón `residuos_sin_volumen_m3` y línea a revisión. La docstring de
`residuos_container_calc.py` y el prompt `valuation_residuos` deben
documentar ese orden nuevo, no el anterior.

R23. CUANDO el revisor abre una ficha, sv4 debe mostrarle las razones de cada
línea de valoración (`albaran_line_valuations.review_reasons_json`, hoy ni
leída ni pintada) —incluidas las `residuos_*`— y los motivos de revisión del
documento (`albaran_documents_merge.review_reasons_json`, leído y no pintado).

R24. CUANDO sv4 guarda una revisión, SI el CIF del proveedor en el merge ya no
coincide con el `<cif>` sellado en un motivo `proveedor_cif_no_casa:<cif>`,
ENTONCES debe retirar ese motivo de `review_reasons_json`.

## Aceptación medible y regresión

R25. Con los 7 albaranes de SALMEDINA: SS-0000589 → 171,00 €, SS-0003967 →
210,00 € y SS-0801977 → 210,00 €. En SS-0000168, SS-0003935 y SS-0025146 el
invariante es el TOTAL —120,00 / 120,00 / 136,00—: por R16/R17 los tres GANAN
una línea sintética sin precio y pasan a `review_required`, y eso NO es una
regresión. SS-0026122 queda fuera (F-017).

R26. Los tests de `services/albaranes-front/tests/test_f019_r23_r26_recalculo_importe.py`
deben seguir pasando **sin modificarlos**, en particular el «round trip 2»: el
recálculo del front no puede pisar en BBDD lo que sv6 escribió bien.

R27. Deben existir tests propios, hoy inexistentes, de `contexto_linea_merger`,
`residuos_container_calc`, la sintética LER de sv6 y el predicado del matcher.

## Decisiones confirmadas por el humano (2026-08-22)

Las cinco dudas de la primera versión están RESUELTAS y ya incorporadas:
**R3** confirmado (conservar + marcar revisión; no se re-encola a
`q-valoracion`); **R8** confirmado (la plantilla deja de recalcular en Jinja);
**R14** confirmado, con el coste de reconstruir las imágenes de sv2, sv3, sv5
y sv6 aceptado; **R17 CAMBIÓ** (la sintética se emite siempre, tarifada o no)
y con él R16 y R25; **R24** acotado a `proveedor_cif_no_casa`, el resto de
motivos sellados por sv3 van en ficha aparte.
