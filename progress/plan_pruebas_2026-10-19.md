<!-- progress/plan_pruebas_2026-10-19.md -->
# Plan de pruebas en la app (Chrome) · 2026-10-19

Valida en producción lo desplegado entre el 18 y el 19-10: F-078, F-077, F-076 (sv4 `r20261019-0955`, sv6
`r20261019-0949`), F-075 (sv5, sv6, sv3, sv4, sv2), F-073 y F-080 (sv3 `r20261019-1114`). Lo ejecuta el líder en
Chrome; las consultas a la BBDD van en solo lectura (`default_transaction_read_only=on`).

**Marcas.** [LECTURA]: solo mira, sin pedir permiso. [ESCRIBE · sí]: escribe en producción y necesita el sí expreso
del humano en el chat para esa acción, salvo que ya conste dado (se indica). `ALTA_SIGRID_COMMIT=false` en sv9 se
comprueba antes de cualquier paso que acabe en un alta.

**Precondición:** la ventana de Chrome restaurada y visible (minimizada, las capturas no responden).

## Hecho ya (18–19-10)

| Prueba | Resultado |
|---|---|
| F-078 T12–T14 (relleno, relectura, «Solicitar alta» en `86c13097`) | VERDE: `simulado`, sin motivos |
| F-077 T14 puntos 1–2 (panel rojo con «Línea 2…», luego «Simulado») | VERDE |
| F-077 T14 punto 3, mitad negativa (12/12 albaranes con filas Contrato) | VERDE; no hay caso positivo hoy |
| Arranque de los servicios (logs) y DDL del pie (4 columnas × 2 tablas) | VERDE |

## Bloque A · F-073: corregir el 0694 (paso 0) — [ESCRIBE · sí dado el 2026-10-19]

En la ficha de `54b82479`, `dedf011a` y `53337da7` (los tres con HIERROS RODRIGO y CTSU26/0001, pendientes):
«Elegir proveedor» → **A28733558 FEYMACO** → «Guardar y volver a buscar».
VERDE: proveedor FEYMACO (origen `manual`) y contrato **CTSU24/0466**, el mismo que tienen los otros dos merges del
correo (`2792cf3b`, `aad8bdc5`). Comprobación en BBDD [LECTURA]: `proveedor_cif`, `proveedor_cif_origen` y
`selected_contrato_codigo` de los tres.

## Bloque B · F-075: el importe del albarán manda

1. [LECTURA] Bandeja: columna «Importe» con el rótulo «albarán · sin IVA».
2. [LECTURA] Ficha de `dfdc8aab` (DISCOIN, sin contrato, 13/13 líneas con importe, sin valoración): columna Importe en
   las líneas y «Valorar ahora» **habilitado** sin contrato (`puedeValorar`).
3. [ESCRIBE · sí] «Valorar ahora» en `dfdc8aab`. VERDE: valoración directa con los importes del albarán; «Aprobar»
   habilitado. Comprobación en BBDD [LECTURA]: `albaran_valuations` del documento.
4. [ESCRIBE · sí] «Aprobar» `dfdc8aab`. VERDE: panel del alta `simulado`; revisar en la previa la analítica
   `<obra>.<sufijo>` (D6, una de las tres altas directas a mirar antes de `COMMIT=true`).
5. [LECTURA, cuando llegue un albarán nuevo] Sección «Pie del albarán» en la ficha y columnas del pie rellenas en BBDD.
   Hoy no hay ninguno: 0 merges con pie y 0 merges creados el 19-10. Si el pie no cuadra con las líneas, motivo
   `pie_no_cuadra:` (un solo motivo vivo).

## Bloque C · F-076 T19: revalorar los pendientes — [ESCRIBE · sí, uno por albarán o la lista entera]

Después del Bloque A. «Valorar ahora» en `2792cf3b`, `53337da7`, `54b82479`, `dedf011a` (0694); `41ab0dc1` (0711);
`09643c2b`, `89e463a7`, `bef66bce`, `f96c6dbe` (0720); `ca609aee` (0723); `25c5d647` (0724).
**`355449d9` NO**: corregir sus partidas a mano (`CI.04.18` ⇒ `CI.4.18`, `CI.03A.02` ⇒ `CI.03A.2`) [ESCRIBE · sí].
VERDE en pantalla: partidas normalizadas con ✓ y nota «Normalizada: X → Y» en el title. Después: log de sv6 con
`[partidas-obra]` [LECTURA] y la medición `medir_f076_partidas` (la lanza el humano, comando en `current.md`).
Ojo: `41ab0dc1` enseñaba «Deshacer (1)» el 18-10 (pila local de otra sesión): no se pulsa.

## Bloque D · F-077 T14, puntos 4 y 5

4. [LECTURA si sale verde] En una ficha pendiente **que elija el humano**: `zzzz` en una partida y «Guardar y aprobar».
   VERDE: aviso «Hay partidas no válidas…», casilla en rojo y **ninguna** petición PATCH/PUT en la red (lo mira el
   líder con `read_network_requests`); después recargar sin guardar.
5. [ESCRIBE · sí] Solo si el humano tiene un albarán que necesite de verdad corregir filas.

## Bloque E · F-073 y F-080 con albaranes nuevos — [LECTURA]

Sin tocar nada: cuando entren albaranes nuevos, log de sv3 (`proveedor_nombre_ambiguo`, «es AJENO al empate por
nombre») y, en la bandeja, los que vayan a revisión por empate de nombre. F-080 no tiene un caso reproducible en
producción sin escribir: su validación es la suite (36 tests) y este log.

## Bloque F · F-064 T12 (vigilancia hasta el 2026-10-25) — [LECTURA]

Merges con `proveedor_cif_propio:` creados desde `2026-10-18T12:22:00Z`. VERDE si 0 al cierre del plazo.

## Orden propuesto

A → B1–B2 → C → B3–B4 → D → E/F (cuando haya albaranes nuevos). Cada [ESCRIBE] se para a pedir el sí salvo el A.
