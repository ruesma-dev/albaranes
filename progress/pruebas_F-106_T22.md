<!-- progress/pruebas_F-106_T22.md -->
# F-106 · T22 · prueba en Chrome con el pipeline local (líder, 2026-10-31)

Pipeline local sobre `dev` `aa1f1dd` (F-106 + F-113 + F-114): Azurite, sv5 (IA real, autorizada por el humano el
31-10: «1, te autorizo»), worker de sv6, worker de sv3 con la clave de Graph anulada en el proceso (para que no pudiera
subir nada a SharePoint: las subidas de PDF de contrato dieron 401 y ninguna escritura en Graph) y sv4. Sin sv1 ni sv2.
BBDD local; columna `edicion_manual_json` creada al arrancar sv6. Documento local `20bc59dd` (obra 0696, sin aprobar).
La T22 está escrita con un ejemplo (10 × 11,20); se hizo sobre una fila real de ese documento (10 × 3,422 − 40 %).

| Paso | Esperado | Resultado |
|---|---|---|
| Q 10, P 11,20, dto 7 | I 104,16 | 104,16 · «A Sigrid: 10 × 10,416 €» |
| Q ⇒ 48 | 499,97 y «≠ albarán» | 499,97 · «≠ albarán: 20,53» |
| I ⇒ 104,16 | P 2,333333 y «A Sigrid: 48 × 2,17 €» | igual |
| Guardar la fila | «✋» y «Volver a lo calculado» | igual (PATCH `bloquear=1` 200) |
| «Valorar ahora» | aviso de R30 y la fila conservada | «Revalorar conserva 1 línea puesta a mano. ¿Continuar?»; tras sv6 (IA4 real), la fila sigue 48 × 2,333333 − 7 % = 104,16 con «✋» |
| Cambiar la obra (0696 ⇒ 0691) y guardar | la fila conservada | sv3 re-enriquece (contrato nuevo `CTSU24/0403`) y sv6 revalora; la fila sigue igual con «✋» |
| «Volver a lo calculado» | vuelve a lo valorado | 10 × 3,422 − 40 % = 20,53, editable |
| Fila que no cuadra (importe 99,99 puesto a mano en la BBDD local) | rojo, no aprueba | rojo con `title` «12 × 7,726 × (1 − 40 %) = 55,63 ≠ 99,99» y los dos botones; aprobar ⇒ 409 «Líneas que no cuadran (cantidad × precio × (1 − dto) ≠ importe): 3» |
| «Recalcular precio» | aprueba | P 13,8875 y «✋»; «Documento guardado y aprobado» (solo a la cola de Azurite; sv9 no estaba arrancado) |

**Veredicto: VERDE.** Nota: los avisos de `window.confirm` bloquean la extensión de Chrome; en la prueba se aceptaron
desde la propia página, sobrescribiendo `confirm` para que devolviera «sí» y guardara el texto (el primero lo vio el humano).

## T23 (humano, 2026-10-31, solo lectura contra Azure)

`listar_altas_descuadradas_f106`: 99 altas reales registradas; 3 líneas descuadradas en 3 altas. En las tres Sigrid recibió el importe de la fila con un precio despejado: una es redondeo del precio (0,27 €), otra tiene el importe casi exactamente el doble de Q × P y la tercera es el caso que originó F-106 (cantidad cambiada sin recalcular). **Decisión del humano (D6): no se tocan desde aquí; se corregirán a mano en Sigrid** («no toques ya se corregiran»). El CSV no se versiona (lleva datos de proveedor).
