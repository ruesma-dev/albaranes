<!-- progress/spec_F-048_v4.md -->
# F-048 · Spec v4 (2026-09-23, tarde): todas las obras y normalizar todo

Autor: spec-author. Rama `feature/F-048-correo-contexto-ia1`. Aplica sobre la
v3 dos decisiones del humano del 2026-09-23 sin rehacerla. Tamaños:
requirements 150/150, design 249/250, tasks 42 tareas (T1–T41 + T16 bis), una
por línea.

## Decisiones aplicadas

1. **D5 revisada: validar contra TODAS las obras.** Las palabras del humano
   están en design D5, junto con la tabla que ha validado (5 filas). Los códigos
   del correo que no están en la lista se descartan ANTES de contar; esto revoca
   la duda 5 de la v3. Si no queda ninguno, manda la IA con lo que lea del
   papel, **sin revisión**; queda rastro en `obra.motivo = correo_fuera_de_lista`,
   con `validada=false` y los códigos leídos en `candidatos_correo`. Sin lista
   (sigrid-api caído o desactivado) cuentan todos, con `validada=null`, como en la v3.
2. **D9 nueva: «sí, normaliza todo».** Recoge la `normalizar_codigo` del bloque
   A (`-> str | None`). Se usa para validar, contar y cruzar. Cierra la duda 2
   de la v3.

## Verificado en el código (dato del líder: correcto)

`SigridApiObrasClient._SQL_OBRAS` trae todas las obras con contrato
(`WHERE con.cod IS NOT NULL`, hasta 10.000 filas). `filtrar_obras_activas`
aplica el corte `cod_min` (4 dígitos > 0450) en Python, dentro de `obtener()`.
`ObrasActivasCacheTTL` cachea solo lo filtrado. Matiz documentado: una obra sin
contrato no está en la lista.

## Diseño de la lista completa (sv2, T16 bis)

Se hace sin consulta nueva y sin caché nueva:

- `CatalogoObras(activas, todas)` va en el puerto.
- El cliente gana `obtener_catalogo()`: una sola petición da las dos listas.
  `obtener()` sigue devolviendo lo mismo que hoy, y se añade `obtener_todas()`.
- La caché guarda el catálogo. Con un proveedor que solo tenga `obtener()`,
  `todas=None`, así que los tests de F-002 siguen valiendo sin editarlos.
- `AlbaranExtractionService.obras_conocidas()` devuelve un mapa de código
  normalizado a código de la lista.
- El resolver recibe `obras_conocidas`. Al fijar la obra escribe el código tal
  como figura en la lista (`945` ⇒ `0945`), para que la red de sv3 lo encuentre.
  Esta decisión es mía; sin ella, la normalización rompería la búsqueda de sv3.
- `composition.py`, `api/app.py` y `_SQL_OBRAS` no se tocan.

## Cambios por fichero

- **requirements.md**: la sección C se reescribe sin renumerar.
  - **R18** (nuevo contenido): normalización, lista completa y «cuentan solo
    los que están».
  - **R19**: el código único y la discrepancia (antes R18 y R19).
  - **R20**: varios códigos, ya contados tras descartar.
  - **R21**: ninguno está en la lista ⇒ sin código, sin revisión.
  - **R31** enumera los casos sin revisión y **R33** marca como informativos
    `fuera_de_lista` y `confirma_papel`.
  - Para caber en 150 líneas se condensaron R3, R6, R25, R29, R32 y R42.
- **design.md**:
  - §1: la lista de obras de sv2 y que `obra_codigo` no es obligatorio en sv3.
  - §2: D5 reescrita con la tabla, D9 nueva y D4 bis «de la lista».
  - §3: se compacta lo que ya hizo el bloque A.
  - §4: la firma del resolver pasa a `obras_conocidas`.
  - §5: puerto, cliente, caché y servicio de sv2; sv3 con SOLO dos disparadores.
  - §6: `_SQL_OBRAS`, el cableado y los tests de F-002 no se tocan.
  - La antigua §7 (partida) queda absorbida en D8, así que §8 y §9 pasan a
    ser §7 (medida) y §8 (riesgos).
  - Riesgos: habrá menos revisiones de las previstas en la v3, la lista es la
    que manda, y R16 interactúa con los falsos códigos. Desaparece la duda de
    `fuera_de_lista`.
- **tasks.md**:
  - **T16 bis nueva**: la lista completa. Se valida con su test y con
    `test_f002_obras_cache.py` en verde, sin editarlo.
  - **T17 reescrita**: RED fila a fila de la tabla, más los casos sin lista y
    sin correo.
  - **T18 reescrita**: normalización, filtrado previo y código escrito en la
    forma de la lista.
  - T20 pasa `obras_conocidas()`.
  - T26: motivos solo en las filas 3 y 5.
  - T28: `warning` solo con motivo.
  - T37 comprueba el caso de un número que no es obra.
  - T40 cuenta los `correo_fuera_de_lista`.
- **Trazabilidad** comprobada con un script: 44 R, todas con alguna tarea.
- **harness/features.json**: la descripción de F-048 lleva los puntos (5) y
  (6) de la tarde del 23. `status` no cambia.
- **progress/current.md**: entrada de la v4, las dudas 1 y 2 cerradas y las
  referencias a § renumeradas.

## Bloque A frente a la v4

No hay choques. `normalizar_codigo`, `MOTIVO_CORREO_FUERA_DE_LISTA`,
`OrigenCampo.validada` y `candidatos_correo` sirven tal cual. No hace falta
ninguna tarea correctiva ni T5-bis.

## Dudas nuevas para el humano (no bloquean)

1. **R16 y el falso código.** El prompt dice a IA1 que, si el correo trae obra,
   no la deduzca del papel. Si lo que IA1 tomó por obra es un pedido, el
   resolver lo descarta y la cabecera puede quedar sin la obra que antes se
   deducía. Además no hay motivo de revisión, porque `obra_codigo` no es
   obligatorio en sv3. Propuesta: medirlo en la muestra (§7) antes de aflojar R16.
2. **Códigos descartados cuando otros sí cuentan.** No se guardan aparte:
   `candidatos_correo` lleva solo los que cuentan. Si se quiere medir cuántos
   falsos códigos lee IA1, haría falta un campo `descartados_correo`. Eso
   exigiría tocar el bloque A (compatible: `extra="ignore"`).
3. **Caché con activas vacías.** Si la lista completa llega pero no hay
   ninguna obra activa, `obtener()` devuelve `None` en vez de servir la lista
   activa anterior. Es un cambio mínimo frente a F-002 y sin efecto real con
   `cod_min=450`.
4. Siguen abiertas las dudas 3 y 4 de la v3: quién captura la muestra y cómo
   llegan los correos, y `origen_datos.partida` en F-049.
