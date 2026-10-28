# F-110 · El alta en Sigrid manda el precio sin descuento, el % de la línea y el importe descontado — requisitos (v1)

Rigor **critico**. Servicios: comun, sv9-alta-sigrid y sv4-front (más `infra/` y documentación). sv3, sv5 y sv6 no
se tocan. **Se implementa DESPUÉS de F-106** y construye sobre ella: sus definiciones (Q, P, d, I, «cuadra»,
`TOLERANCIA_CUADRE_EUR` = 0,02 €), su `linea_a_sigrid` (F-106 R2), su `linea_no_cuadra` (R17), su «A Sigrid» (R15) y
su script de altas (R18) se dan por hechos y no se repiten aquí. Decisiones abiertas D0–D7 en `design.md` §10.

**Depende de un contrato SUPUESTO de sigrid-api (su F-018, sin publicar):** `lineas[].dto?` en la petición, número
de 0 a 100 con 2 decimales y sin cascada, y `lineas[].dto` en la respuesta de la previa (`design.md` §4). Todo lo que
dependa de la forma final queda tras la guarda de R5 y se revisa en la T18.

Origen: el humano, 2026-10-28. En CECOIS A 26018351 la plataforma dice 12 × 0,645 −7 % = 7,20 y Sigrid recibió
12 × 0,60 sin descuento (`design.md` §3). Debe recibir lo mismo que la línea: 0,645, 7 % y 7,20.

## Definiciones

- **Qs**: la cantidad que sv9 manda (F-106 R2: la convertida si vinculada, si no la del albarán), con el signo de I.
- **Con descuento**: `ruesma_comun.importes.clasificar_descuento(d)` da `aplicable` (0 < d ≤ 100).
- **Guarda**: la variable `ALTA_SIGRID_ENVIAR_DTO`; **encendida** solo con el literal `true`.
- **Línea a Sigrid**: cantidad, precio y `dto` (o ninguno) que sv9 pondrá en la petición de la línea.

## Comun · la línea a Sigrid

R1. `alta_sigrid.linea_a_sigrid` (F-106 R2) admite además `precio`, `descuento` y `con_descuento` (por defecto
`False`) y devuelve `LineaASigrid(cantidad, precio, dto)` o `None`; sigue siendo la ÚNICA definición de «a Sigrid»
para sv9 y sv4.

R2. CUANDO `con_descuento` es `False` o la línea no es «con descuento», el resultado es exactamente el de F-106 R2
(`precio = round(|I| / |Qs|, 6)`) con `dto = None`.

R3. CUANDO `con_descuento` es `True` y la línea es «con descuento», `dto = round(d, 2)` y `precio = round(P, 6)` si
`importe_de_linea(|Qs|, round(P, 6), dto)` no difiere de `|I|` (`importes.difieren`, 0,01 €); si no, `precio =
unitario_despejado(|I|, |Qs|, dto)` (bruto, 6 decimales). La cantidad lleva el signo de I, como hoy.

R4. SI falta I, Qs es nula o 0, o el precio de R3 no se puede despejar (d del 100 %), ENTONCES devuelve `None`.
Nunca lanza.

## sv9 · la guarda

R5. sv9 lee `ALTA_SIGRID_ENVIAR_DTO`; solo el literal `true` la enciende y cualquier otro valor, vacío o ausente la
deja apagada. Al arrancar, el log dice si está encendida. El literal y su lectura viven en comun (R14).

R6. MIENTRAS la guarda está apagada, la petición de cualquier albarán es idéntica (mismo `a_dict`) a la que construye
F-106, con o sin descuentos.

## sv9 · la petición con la guarda encendida

R7. DONDE la guarda está encendida, cada línea a registrar «con descuento» lleva `precio` de R3 y la clave `dto`
(después de `precio` en `a_dict`); las que no lo son van como hoy y sin la clave `dto`.

R8. SI una línea con `dto` no cuadra a Sigrid (`cuadra_linea(|Qs|, precio, dto, |I|)` distinto de `True`) o R4 da
`None`, ENTONCES el alta queda `no_admitido` con el motivo `linea_no_cuadra` (el de F-106) y el detalle «a Sigrid:
100000 × 0,132712 × (1 − 7 %) = 12342,22 ≠ 12342,17», sin llamar a sigrid-api. Se evalúa después del de F-106 R17.

R9. Las vinculadas siguen R3 igual que las sin vincular: sv9 no compara el `dto` con el del `ctrpro` (la caché de
albaranes no lo tiene, `design.md` §3); lo valida sigrid-api (D3).

R10. `PeticionAlbaran.desde_dict` lee igual una `peticion_json` sin `dto` (altas de antes) que con `dto`; retomar un
`incierto` reenvía la petición guardada, con o sin `dto`, sea cual sea la guarda en ese momento.

## sv9 · la previa

R11. CUANDO una línea se pidió con `dto` y la línea de la previa no trae `dto`, no es un número legible o difiere del
pedido en más de 0,005, el comparador añade el motivo `dto_distinto` (detalle «pedido 7, Sigrid —») ⇒ `revisar`.

R12. Las líneas pedidas sin `dto` no comparan `dto` (como hoy, aunque la previa lo traiga); `importe_distinto`,
`partida_distinta` y `idempotente` no cambian (en `idempotente` no se compara `dto`).

R13. Los códigos de error o aviso que publique sigrid-api para el `dto` entran en `CODIGOS_LINEA` (o en los avisos)
solo tras la T18; hasta entonces un código desconocido va a `error`, como hoy (H25).

## sv4

R14. sv4 lee `ALTA_SIGRID_ENVIAR_DTO` con la misma función de comun que sv9 y debe llevar el mismo valor
(`infra/00_capps_vars.ps1`, R20).

R15. El «A Sigrid» de la ficha (F-106 R15) usa `linea_a_sigrid` con `con_descuento` = la guarda de sv4: con `dto`,
«A Sigrid: 12 × 0,645 € −7 %»; se ve bajo el precio si el precio a Sigrid difiere de P en más de 0,000001 o el `dto` a
Sigrid difiere de d; al teclear se repinta con la misma regla de R3 en JS (`precioASigrid`).

R16. La ficha marca la guarda con `data-alta-dto` y la regla JS da lo mismo que la de comun en la tabla de casos de
R22 (los dos tests leen la misma tabla).

R17. El panel del alta (`_alta_sigrid.html`) añade la columna «Dto %» con el `dto` pedido («—» si no se pidió) y, si
la previa devolvió otro, «(Sigrid: x)»; «Precio» es el pedido.

R18. `TEXTOS_MOTIVO_ALTA` tiene el texto de `dto_distinto` («Sigrid no aplica el descuento pedido»); el test que lo
contrasta con las fuentes de sv9 (F-077) lo cubre.

## Script de altas de F-106

R19. El script de F-106 R18 compara, en las líneas pedidas con `dto`, el precio enviado con P y el `dto` con d; en
las pedidas sin `dto`, como F-106 (precio enviado frente a `P × (1 − d)`).

## Infra y documentación

R20. `infra/00_capps_vars.ps1` versiona `ALTA_SIGRID_ENVIAR_DTO = "false"` dentro de `AltaSigridEnvComun` (sv4 y sv9);
`set_alta_sigrid.ps1` la relee en las dos apps; `.env.example` de sv9 la documenta. Ningún script la pone a `true`.

R21. `docs/ARCHITECTURE.md` regla 19, `services/albaranes-alta-sigrid/sv9.md` («Llaves» y «Reglas») y
`azure-apps/albaranes.md` (variables y consumo `lineas[].dto` de `sigrid/albaran`) recogen R1–R20.
`azure-apps/sigrid_api.md` NO se edita: es de sigrid-api.

## Regresión y casos

R22. Casos por fixture, sin red ni BBDD (`design.md` §5): (a) CECOIS 12 × 0,645 −7 % = 7,20 ⇒ 0,645 y `dto` 7 (el
despeje daría 0,645161); (b) 1 × 151,20 −7 % = 140,62 ⇒ 151,2 y 7; (c) un céntimo de más (10 × 26,796 −7 %, I 249,21)
⇒ despejado 26,796774; (d) vinculada FEYMACO 108 × 0,543 −40 % = 35,19 con `ctrpro_ide`; (e) devolución −1 × 18,00
−10 % = −16,20 ⇒ cantidad −1, precio 18, `dto` 10; (f) Qa 100000, Qc 1000, P 13,27115, d 7, I 12342,17 ⇒ R8; (g) d
nulo, 0, −5 y 150 ⇒ como hoy, sin `dto`; (h) d 7,456 ⇒ `dto` 7,46.

R23. Con la guarda apagada (el defecto), los tests de sv9 y sv4 de F-053, F-065, F-069, F-075, F-076, F-077, F-078,
F-098, F-104 y F-106 siguen en verde sin tocar aserciones.

R24. La guarda solo la enciende el humano tras publicarse y desplegarse la F-018 de sigrid-api y tras la T18 en
verde; SI el contrato publicado difiere del supuesto (`design.md` §4), ENTONCES se para y se repropone.
