<!-- specs/F-098-partidas-por-capitulo/requirements.md -->
# F-098 · Partidas por capítulo y con su código completo · Requisitos (v1, 2026-10-23)

Servicios: **comun** (la lista lleva capítulo e `ide`; casar el código completo), **sv4** (selector por capítulo,
pinta el código completo, guarda el de Sigrid), **sv6** (sin código: tests de que normaliza `CD.99.01.64`), **sv9**
(sin código: test de no regresión). Rigor `critico`: lo que se guarda es lo que sv9 manda a Sigrid. Las decisiones
abiertas P1–P8 están en `design.md` §8; cada R se escribe con la opción recomendada.

Origen (humano, 2026-10-23): «que el filtro de partidas funcione igual que el de partes, tenga cd, ci, cp o
cualquier otro sufijo en primer nivel como preselección, y luego las partidas» y «la partida completa […] debe
incluir todo el código […]: he tenido que poner 99.01.64 y no cd.99.01.64». Verificado: en la obra 0686 las 2313
hojas de CD tienen `cod` `99.01.64` (sin el prefijo); las de CI, CP y 98 sí lo llevan (`CI.4.18`). El albarán
`8c4e026a` llevaba `CD.99.01.64` y sigrid-api lo rechazó con «La obra no tiene ninguna partida 'CD.99.01.64'».

Vocabulario: **hoja**, **lista**, **lectura** y **clave** (`normalizar_partida`), como en F-076. **cod** = el
`obrparpar.cod` de Sigrid, tal cual. **Capítulo** = el de primer nivel de la hoja (R2). **Código completo** = el
que ve el humano (R3). Lo que se guarda en `codigo_partida_final` sigue siendo **el cod** (P1).

## A. comun · `ruesma_comun.sigrid.partidas`

- R1. Cada hoja de `ListaPartidasObra` debe llevar, además de lo de hoy, `ide` (`obrparpar.ide`), `capitulo` (código
  de su capítulo, o `None`), `capitulo_descripcion` y `codigo_completo`. `codigo` sigue siendo el cod, sin cambios.
- R2. El capítulo de una hoja debe ser su antecesor de primer nivel: la raíz de su cadena (padre 0, nulo o que no
  está entre las filas). SI la obra tiene una sola raíz y esa raíz tiene hijos, ENTONCES el primer nivel son sus
  hijos (y así mientras quede uno solo). Una hoja de primer nivel es su propio capítulo. Ciclos: como hoy, sin
  bucle. Un capítulo sin `cod` ⇒ `capitulo` = `None`.
- R3. `codigo_completo` debe ser el cod SI el cod ya empieza por el código del capítulo (comparados en mayúsculas,
  NFKC y sin espacios exteriores) seguido de fin, de un carácter no alfanumérico o de un cambio letra↔dígito
  (`CI.4.18` en CI, `CD2.07` en CD, `98.01` en 98); en otro caso, capítulo + `.` + cod (`99.01.64` en CD ⇒
  `CD.99.01.64`; `985.1` en 98 ⇒ `98.985.1`). Sin capítulo ⇒ el cod.
- R4. `ListaPartidasObra.capitulos` debe dar los capítulos con al menos una hoja, ordenados por código, cada uno con
  `codigo`, `descripcion` y número de hojas (`None` = «Sin capítulo», al final).
- R5. La SQL, las hojas, los `no_hojas`, el orden, `leer_partidas_obra` y `CachePartidasObra.lista` no deben cambiar:
  los tests de F-049/F-076 siguen en verde sin tocarlos.
- R6. CUANDO la lectura no es exacta, `casar_partida` debe buscar candidatas por la clave del cod Y por la clave del
  código completo de cada hoja. Con UN cod distinto ⇒ casa con ese cod: `normalizada` si casó por su cod,
  `completa` (motivo nuevo, en `MOTIVOS_CASADOS`) si solo por su código completo. Con dos o más ⇒ `ambigua`.
  `CD.99.01.64`, `cd 99.1.64` y `CD-99-01-64` ⇒ `99.01.64` (`completa`).
- R7. Una lectura literalmente igual a un cod de la lista debe seguir siendo `exacta`, como en F-076, aunque otra hoja
  tenga ese código completo.
- R8. `resolver_partida_obra` debe tratar `completa` como `normalizada` (`RESOLUCION_NORMALIZADA`, código = el cod).
  La guarda de no hoja debe mirar también el código completo de los no hoja: `CD.99.01` (subcapítulo `99.01` de
  CD) ⇒ `fuera_de_lista`.
- R9. Nunca se debe quitar ni añadir un prefijo por parecido: `99.01.64` leído no casa con una hoja de cod
  `CD.99.01.64`; `01.64` no casa con `99.01.64`; `CI.99.01.64` no casa con la de CD (H1 de F-049).
- R10. `misma_partida(lista, a, b)` debe ser `True` solo si `a` y `b` casan (`exacta`, `normalizada` o `completa`)
  con el mismo cod; vacías, `alm` o sin lista ⇒ `False`.
- R11. `mostrar_partida(lista, cod)` debe dar el código completo de la hoja con ese cod; SI varias hojas tienen ese cod
  con códigos completos distintos, el cod no es de la lista o no hay lista, ENTONCES el cod tal cual.
- R12. `ListaPartidasObra.cod_repetido(cod)` debe ser `True` si dos o más hojas tienen ese cod.
- R13. `CachePartidasObra.consultar(obra)` debe dar `(lista, ok)`: la lista vigente o recién leída (con 0 hojas
  también) y `ok=True`; tras un fallo o truncado, la caducada si la hay (o `None`) y `ok=False`. Nunca lanza.

## B. sv4 · lista, selector y ficha

- R14. `GET /api/sigrid/partidas?obra=` debe leer por la caché de sv4 (R27) y devolver, por hoja, `ide`, `codigo`
  (cod), `codigo_completo`, `capitulo`, `descripcion`, `descripcion_agregada` y `cod_repetido`, y `capitulos`
  (`codigo`, `descripcion`, `n`). `ok=false` como hoy si no hay cliente, falta la obra, falla o trunca.
- R15. El combo de partida (fila y «Dividir») debe pintar arriba una barra de chips: «Todas» y uno por capítulo que
  tenga la obra (CD, CI, CP, 98 o el que sea; `title` = descripción y nº de hojas). «Almacén (sin partida)» va
  siempre primera, con cualquier chip.
- R16. CUANDO hay un chip de capítulo elegido, el combo debe ofrecer solo las hojas de ese capítulo y el texto
  tecleado filtrar sobre ellas (por palabras, como hoy).
- R17. El capítulo elegido debe valer para todos los combos de la ficha y de «Dividir» y recordarse por obra en el
  navegador (con `try/catch`; sin almacenamiento, «Todas»). Por defecto, «Todas» (P3).
- R18. La etiqueta de cada opción debe ser `código completo · descripción agregada`; buscar `cd.99.01` o `99.01.64`
  debe encontrar la `99.01.64` de CD.
- R19. El combo debe pintar como mucho 100 partidas y, si hay más, la línea «N partidas más: escribe para afinar».
- R20. SI una hoja tiene `cod_repetido`, ENTONCES su opción debe llevar «(código repetido en la obra)» (P2).
- R21. CUANDO se elige una partida, la casilla debe enseñar su código completo, y «Guardar», «Guardar todas»,
  «Guardar y aprobar» y «Dividir» deben mandar su cod (`99.01.64`), nunca el completo.
- R22. Una partida tecleada debe valer si está vacía (almacén) o es igual a un código completo o a un cod de la
  lista; si no, en rojo y sin enviarse, como F-065 R27 v5. Al salir, como hoy (vuelve a la de antes).
- R23. La ficha debe pintar la partida final con `mostrar_partida` en la casilla editable, la de solo lectura, el
  panel «Líneas a Sigrid», las opciones de «Origen ✎» y «Traer líneas contrato»; el `defaultValue` es lo pintado,
  así una fila sin tocar no manda partida. Sin lista, el cod, como hoy.
- R24. El aviso de partida debe dar ✓ cuando la leída y la de su línea de contrato son `misma_partida`
  (`CD.99.01.64` frente a `99.01.64` de CD), con la nota «Normalizada: X → Y» solo si la leída difiere de lo pintado;
  nunca convierte un ✓ en ⚠. El ⚠ de F-077 sale solo cuando no son la misma.
- R25. CUANDO un PATCH de fila o un «Dividir» trae una partida no vacía y hay lista de la obra, sv4 debe guardar el cod
  de la lista si la partida casa `exacta`, `normalizada` o `completa`; si no casa o no hay lista, tal cual (como hoy:
  el servidor no la rechaza). `CD.99.01.64` nunca se guarda en una obra que tiene la hoja `99.01.64` de CD.
- R26. Cambiar la partida a la misma que la de su línea de contrato escrita en completo no debe pasar la fila a Nueva
  (`cambia_origen` recibe el cod ya traducido).
- R27. sv4 debe leer la lista por una `CachePartidasObra` propia: `PARTIDAS_OBRA_TTL_S` (defecto 600),
  `PARTIDAS_OBRA_MAX_OBRAS` (64), `PARTIDAS_OBRA_FALLO_TTL_S` (60); sin `SIGRID_API_*`, sin caché y todo como hoy.
- R28. SI la lista no está disponible al pintar la ficha, ENTONCES la ficha debe salir igual que hoy (cod, aviso por
  la clave de F-076), sin error ni espera añadida tras el primer fallo.

## C. sv6 y sv9

- R29. sv6 debe valorar una lectura `CD.99.01.64` en una obra con la hoja `99.01.64` de CD con partida final
  `99.01.64`, `codigo_partida_albaran` = `CD.99.01.64`, motivo `partida_normalizada:CD.99.01.64>99.01.64` y sin
  revisión, sin cambiar su código (solo tests). Casa con la línea de contrato de partida `99.01.64`.
- R30. sv9 debe seguir mandando `codigo_partida_final` tal cual como `partida` (`99.01.64`), sin `paride` (P2).

## D. Lo ya guardado

- R31. `scripts/medir_f076_partidas.py` de sv6 debe contar aparte la clase `completa` (final que casa solo por el
  código completo) por estado del documento, en solo lectura y sin códigos ni importes en la salida más allá del
  `document_id` y el par leída → cod de las de esa clase.
- R32. (Solo con P4 = a) `scripts/corregir_partidas_f098.py` de sv6 debe, en seco por defecto, listar las líneas de
  documentos NO aprobados y sin alta bloqueante cuya partida final casa `completa`, y con `--aplicar` (humano)
  poner su cod en `codigo_partida_final`, una transacción por documento, sin tocar nada más.

## E. Transversales

- R33. Sin DDL, sin cambios de mensajes de cola ni de sigrid-api. comun pasa a 0.9.0.
- R34. Los tests no tocan red ni BBDD; el JS se ejecuta con node y `tests/dom_falso.js` (patrón de F-065).
- R35. `docs/ARCHITECTURE.md` (regla 23) y `azure-apps/albaranes.md` (variables nuevas de sv4) deben recoger el
  cambio en el mismo trabajo.
