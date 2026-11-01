<!-- progress/verif_F-103.md -->
# F-103 · Cierre sin código: verificación en solo lectura (líder, 2026-10-28)

**Qué era F-103.** Las altas de sv9 heredaban de la plantilla de sigrid-api (último albarán del proveedor) la
facturación y otras fechas de cabecera (`idefac`, `fecfac`/`estfac`, `fecent`, `feclim`, `cocide`, `dcarec`…).
**Quién lo arregló.** sigrid-api con su F-015 (cabecera por lista blanca, ninguna fila se clona), desplegada el
2026-10-24 a las 18:21:18 UTC (`60db955`). El humano decidió el 24-10 no limpiar las altas ya escritas (su R30 no se
ejecuta). Por eso F-103 se reduce a esta verificación; la spec v1 de la rama `feature/F-103-alta-sin-facturacion-heredada`
(`563d264`) no se fusiona, y su Bloque C (códigos v8.3) lo absorbió F-104.

**Fuera de F-103** (propuesta del líder, **confirmada por el humano el 2026-10-28: «todo a»**, opción (a) de la PARADA 2): el **detector**
de altas con facturación heredada (alcance 3, T1–T4/T8 de la spec v1) y que **sv9 mande los campos de cabecera
explícitos** (alcance 4). Caen porque F-015 monta la cabecera por lista blanca y ninguna fila se clona: la causa
desaparece en el origen y sv9 no tiene nada que fijar. Si el humano quiere el detector, F-103 no se cierra y el
detector va a una feature nueva.

## Verificación (PostgreSQL de Azure en solo lectura + `sql/read` de sigrid-api)

Altas de `albaran_altas_sigrid` con último intento desde `2026-10-24T18:21:18Z`: **18** (17 `registrado` y 1
`ya_en_sigrid`, `alta_a_mano`), todas en modo `real`, de la AC26/30675 a la AC26/31027. Cabecera en Sigrid
(`dbo.con` + `dbo.dca`, y recuento de `dbo.dcarec`) de las 17 escritas:

| Campo | Resultado en las 17 |
|---|---|
| `idefac` | 0 en todas |
| `fecent`, `feclim`, `cocide` | 0 en todas |
| `tipgar` | −1 en todas |
| `dcarec` | ninguna fila |
| `empide` | 1363636 (quien aprueba, F-069) |
| `fecfac`/`horfac`/`antestfac`/`estfac` | 0/0/0/0 en las 12 restantes (30819 y las 11 del 28-10); en 30675, 30676, 30770, 30820 y 30821, `fecfac` 26-10 o 27-10 con `horfac` ≠ 0, `antestfac` 3 y `estfac` 1 |

Las cinco con `fecfac` (lectura de `dbo.log`, `tab` = `con`, ordenada por `ide` porque la `hor` de las acciones de la
interfaz es la del reloj del puesto): en las cinco, tras la fila `ope` 1 del alta (la única que deja sigrid-api), hay
filas `ope` 5 (y en 30820 y 30821 también `ope` 30) con `ide` mayor, modificaciones de usuario desde la interfaz:
30675 y 30676 el 26-10 por la tarde (confirmado además por sigrid-api el 27-10), 30770 el 27-10 a media mañana, 30820
y 30821 el 26-10 por la tarde y el 27-10 de madrugada. Además `estfac` = 1 es facturación real, que la herencia nunca
ponía (dejaba `estfac` a 0). Las cinco se facturaron a mano después del alta; ninguna la heredó.

**Conclusión:** desde F-015 ninguna alta hereda facturación, fechas ni retenciones de la plantilla. F-103 se cierra
`done` sin código.
