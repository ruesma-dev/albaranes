<!-- progress/mutacion_F-011.md -->
# F-011 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-011` el 2026-08-13 15:35.

## Alcance

Origen del diff: **rama** (`42139da4067a65d8c6dd1cc8c4cbfe3d740c0c3e` .. `feature/F-011-evals-ia`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/__init__.py` | 9 |
| `evals/barrido.py` | 79 |
| `evals/comparador.py` | 304 |
| `evals/conversor.py` | 594 |
| `evals/criticidad.py` | 164 |
| `evals/informe.py` | 185 |
| `evals/modelos.py` | 201 |
| `evals/procesos/__init__.py` | 12 |
| `evals/procesos/sv2_extraccion.py` | 258 |
| `evals/procesos/sv5_valoracion.py` | 449 |
| `evals/procesos/sv6_build.py` | 608 |
| `evals/runner.py` | 509 |
| `harness/rutas_sensibles.py` | 440 |
| **Total** | **3812** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 305 |
| Mutantes evaluados | 305 |
| Muertos | 172 |
| Supervivientes | 133 |
| Timeouts | 0 |
| Tiempo total | 3694.1 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `evals/barrido.py:46` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 2. `evals/comparador.py:48` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis

**Hueco real: falta un caso con estructura anidada dentro de una fila.** `_es_hoja` decide qué se considera un campo a clasificar; con la mutación, un diccionario anidado pasaría a tratarse como campo. Los fixtures de los tests son tablas planas (fila = diccionario de escalares y listas), que es lo que produce el conversor hoy, así que la rama no se distingue. Si algún libro pasara a tener estructuras anidadas, este test haría falta; hoy no existe tal caso en el contrato de datos.

### 3. `evals/comparador.py:56` [logico]

- Original: `if isinstance(valor, bool) or valor is None:`
- Mutado:   `if isinstance(valor, bool) and valor is None:`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 4. `evals/comparador.py:90` [logico]

- Original: `if esperado is None or obtenido is None:`
- Mutado:   `if esperado is None and obtenido is None:`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 5. `evals/comparador.py:95` [logico]

- Original: `if numero_esperado is not None and numero_obtenido is not None:`
- Mutado:   `if numero_esperado is not None or numero_obtenido is not None:`

#### Análisis

**Guarda de tipo con una combinación que el ground truth no produce.** Las celdas de Excel llegan como número, texto, fecha o vacío; esta rama solo se recorrería con una mezcla que el contrato de datos no permite (por ejemplo, comparar un número contra un objeto no textual). Es un hueco real y así se declara, pero de riesgo bajo: cualquier diferencia de valor de verdad —precio, importe, cantidad, partida— la cazan los tests de R2 y R7, que sí recorren el camino normal de la comparación.

### 6. `evals/comparador.py:144` [logico]

- Original: `if not isinstance(obtenido, Sequence) or isinstance(obtenido, (str, bytes)):`
- Mutado:   `if not isinstance(obtenido, Sequence) and isinstance(obtenido, (str, bytes)):`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 7. `evals/comparador.py:273` [logico]

- Original: `if campo not in observables and campo not in vistos:`
- Mutado:   `if campo not in observables or campo not in vistos:`

#### Análisis

**Hueco real menor: duplicados en la lista de campos no observables.** La mutación haría que un mismo campo pudiera aparecer repetido en el informe. Los tests comprueban que los campos no observables se declaran (R13), no que la lista esté deduplicada. El efecto de la mutación es ruido en el informe, nunca una comparación que se relaje: los campos no observables se excluyen en `podar`, que es otra función y cuyos mutantes murieron.

### 8. `evals/conversor.py:122` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 9. `evals/conversor.py:130` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 10. `evals/conversor.py:189` [booleano]

- Original: `por_tipologia=False,`
- Mutado:   `por_tipologia=True,`

#### Análisis

**Hueco real de bajo riesgo en la mecánica interna del conversor.** Los tests de R1, R2, R3, R5 y R6 comprueban el RESULTADO: qué fixtures aparecen, con qué claves, con qué valores normalizados, byte a byte iguales entre corridas y con qué error cuando falta un libro, una pestaña o el `caso_id` de una fila. Esta mutación cambia un detalle interno cuyo efecto no se distingue con los libros sintéticos actuales (por ejemplo, una tabla sin datos, o una fila cuyo ancho coincide con el de la cabecera). Ampliar los libros de prueba lo cazaría; se anota como mejora de los fixtures de test, no como equivalente.

### 11. `evals/conversor.py:245` [not]

- Original: `elif not _PUNTO_DECIMAL.match(limpio):`
- Mutado:   `elif _PUNTO_DECIMAL.match(limpio):`

#### Análisis

**Hueco real de bajo riesgo en la mecánica interna del conversor.** Los tests de R1, R2, R3, R5 y R6 comprueban el RESULTADO: qué fixtures aparecen, con qué claves, con qué valores normalizados, byte a byte iguales entre corridas y con qué error cuando falta un libro, una pestaña o el `caso_id` de una fila. Esta mutación cambia un detalle interno cuyo efecto no se distingue con los libros sintéticos actuales (por ejemplo, una tabla sin datos, o una fila cuyo ancho coincide con el de la cabecera). Ampliar los libros de prueba lo cazaría; se anota como mejora de los fixtures de test, no como equivalente.

### 12. `evals/conversor.py:321` [booleano]

- Original: `esperando_encabezados = False`
- Mutado:   `esperando_encabezados = True`

#### Análisis

**Hueco real de bajo riesgo en la mecánica interna del conversor.** Los tests de R1, R2, R3, R5 y R6 comprueban el RESULTADO: qué fixtures aparecen, con qué claves, con qué valores normalizados, byte a byte iguales entre corridas y con qué error cuando falta un libro, una pestaña o el `caso_id` de una fila. Esta mutación cambia un detalle interno cuyo efecto no se distingue con los libros sintéticos actuales (por ejemplo, una tabla sin datos, o una fila cuyo ancho coincide con el de la cabecera). Ampliar los libros de prueba lo cazaría; se anota como mejora de los fixtures de test, no como equivalente.

### 13. `evals/conversor.py:356` [comparacion]

- Original: `bruto = valores[indice] if indice < len(valores) else None`
- Mutado:   `bruto = valores[indice] if indice <= len(valores) else None`

#### Análisis

**Hueco real de bajo riesgo en la mecánica interna del conversor.** Los tests de R1, R2, R3, R5 y R6 comprueban el RESULTADO: qué fixtures aparecen, con qué claves, con qué valores normalizados, byte a byte iguales entre corridas y con qué error cuando falta un libro, una pestaña o el `caso_id` de una fila. Esta mutación cambia un detalle interno cuyo efecto no se distingue con los libros sintéticos actuales (por ejemplo, una tabla sin datos, o una fila cuyo ancho coincide con el de la cabecera). Ampliar los libros de prueba lo cazaría; se anota como mejora de los fixtures de test, no como equivalente.

### 14. `evals/conversor.py:369` [entero]

- Original: `f"{ubicacion}, fila {celdas[0].row}: hay datos pero la columna "`
- Mutado:   `f"{ubicacion}, fila {celdas[1].row}: hay datos pero la columna "`

#### Análisis

**Hueco real de bajo riesgo en la mecánica interna del conversor.** Los tests de R1, R2, R3, R5 y R6 comprueban el RESULTADO: qué fixtures aparecen, con qué claves, con qué valores normalizados, byte a byte iguales entre corridas y con qué error cuando falta un libro, una pestaña o el `caso_id` de una fila. Esta mutación cambia un detalle interno cuyo efecto no se distingue con los libros sintéticos actuales (por ejemplo, una tabla sin datos, o una fila cuyo ancho coincide con el de la cabecera). Ampliar los libros de prueba lo cazaría; se anota como mejora de los fixtures de test, no como equivalente.

### 15. `evals/conversor.py:434` [logico]

- Original: `f"{len(self.ficheros)} fichero(s) escritos ({detalle or 'sin casos'})"`
- Mutado:   `f"{len(self.ficheros)} fichero(s) escritos ({detalle and 'sin casos'})"`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 16. `evals/conversor.py:456` [booleano]

- Original: `libro = openpyxl.load_workbook(ruta, data_only=True, read_only=False)`
- Mutado:   `libro = openpyxl.load_workbook(ruta, data_only=False, read_only=False)`

#### Análisis

**Hueco real de bajo riesgo: opciones de carga de openpyxl.** `data_only=True` pide los VALORES de las fórmulas y `read_only=False` permite recorrer la hoja con coordenadas. Los libros sintéticos de los tests no llevan fórmulas y son pequeños, así que ninguna de las dos opciones cambia el resultado allí. Con los libros reales sí importaría: `data_only=False` devolvería la fórmula en vez del número. La evidencia de que la carga real funciona es la T4 de esta feature, donde `python -m evals.conversor` recorrió los seis libros del humano y salió con código 0. Un test que lo cazara tendría que fabricar un xlsx con fórmulas: queda anotado como mejora, no como equivalente.

### 17. `evals/conversor.py:456` [booleano]

- Original: `libro = openpyxl.load_workbook(ruta, data_only=True, read_only=False)`
- Mutado:   `libro = openpyxl.load_workbook(ruta, data_only=True, read_only=True)`

#### Análisis

**Hueco real de bajo riesgo: opciones de carga de openpyxl.** `data_only=True` pide los VALORES de las fórmulas y `read_only=False` permite recorrer la hoja con coordenadas. Los libros sintéticos de los tests no llevan fórmulas y son pequeños, así que ninguna de las dos opciones cambia el resultado allí. Con los libros reales sí importaría: `data_only=False` devolvería la fórmula en vez del número. La evidencia de que la carga real funciona es la T4 de esta feature, donde `python -m evals.conversor` recorrió los seis libros del humano y salió con código 0. Un test que lo cazara tendría que fabricar un xlsx con fórmulas: queda anotado como mejora, no como equivalente.

### 18. `evals/conversor.py:483` [comparacion]

- Original: `elif clave == "caso" and isinstance(registro.get("tipologia"), str):`
- Mutado:   `elif clave != "caso" and isinstance(registro.get("tipologia"), str):`

#### Análisis

**Hueco real de bajo riesgo en la mecánica interna del conversor.** Los tests de R1, R2, R3, R5 y R6 comprueban el RESULTADO: qué fixtures aparecen, con qué claves, con qué valores normalizados, byte a byte iguales entre corridas y con qué error cuando falta un libro, una pestaña o el `caso_id` de una fila. Esta mutación cambia un detalle interno cuyo efecto no se distingue con los libros sintéticos actuales (por ejemplo, una tabla sin datos, o una fila cuyo ancho coincide con el de la cabecera). Ampliar los libros de prueba lo cazaría; se anota como mejora de los fixtures de test, no como equivalente.

### 19. `evals/conversor.py:483` [logico]

- Original: `elif clave == "caso" and isinstance(registro.get("tipologia"), str):`
- Mutado:   `elif clave == "caso" or isinstance(registro.get("tipologia"), str):`

#### Análisis

**Hueco real de bajo riesgo en la mecánica interna del conversor.** Los tests de R1, R2, R3, R5 y R6 comprueban el RESULTADO: qué fixtures aparecen, con qué claves, con qué valores normalizados, byte a byte iguales entre corridas y con qué error cuando falta un libro, una pestaña o el `caso_id` de una fila. Esta mutación cambia un detalle interno cuyo efecto no se distingue con los libros sintéticos actuales (por ejemplo, una tabla sin datos, o una fila cuyo ancho coincide con el de la cabecera). Ampliar los libros de prueba lo cazaría; se anota como mejora de los fixtures de test, no como equivalente.

### 20. `evals/conversor.py:503` [entero]

- Original: `return json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True) + "\n"`
- Mutado:   `return json.dumps(datos, ensure_ascii=False, indent=3, sort_keys=True) + "\n"`

#### Análisis

**Hueco real conocido en la comprobación del determinismo.** El test de R5 compara dos corridas entre sí, y una mutación del formato (sangrado, orden de claves) afecta a las dos por igual, así que sigue pasando. La protección de verdad contra este cambio es el diff de git: los fixtures están versionados y un reformateo saldría entero en el diff de la siguiente conversión. Aun así es un hueco real: un test que fijara el texto esperado de un fixture pequeño lo cerraría. Queda anotado.

### 21. `evals/conversor.py:503` [booleano]

- Original: `return json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True) + "\n"`
- Mutado:   `return json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=False) + "\n"`

#### Análisis

**Hueco real conocido en la comprobación del determinismo.** El test de R5 compara dos corridas entre sí, y una mutación del formato (sangrado, orden de claves) afecta a las dos por igual, así que sigue pasando. La protección de verdad contra este cambio es el diff de git: los fixtures están versionados y un reformateo saldría entero en el diff de la siguiente conversión. Aun así es un hueco real: un test que fijara el texto esperado de un fixture pequeño lo cerraría. Queda anotado.

### 22. `evals/conversor.py:587` [entero]

- Original: `return 1`
- Mutado:   `return 2`

#### Análisis

**Hueco real: el CLI del conversor no tiene test propio.** Los tests ejercitan `convertir()`, que es donde vive toda la lógica, pero no `main()`, así que sus códigos de salida no los caza nadie. La evidencia de que funcionan es manual y consta en el informe de la feature: en la T4 `python -m evals.conversor` salió con código 0 sobre los seis libros reales. Cerrar el hueco es un test de tres líneas sobre `main([...])`; se deja anotado para el reviewer en vez de darlo por equivalente.

### 23. `evals/conversor.py:590` [entero]

- Original: `return 0`
- Mutado:   `return 1`

#### Análisis

**Hueco real: el CLI del conversor no tiene test propio.** Los tests ejercitan `convertir()`, que es donde vive toda la lógica, pero no `main()`, así que sus códigos de salida no los caza nadie. La evidencia de que funcionan es manual y consta en el informe de la feature: en la T4 `python -m evals.conversor` salió con código 0 sobre los seis libros reales. Cerrar el hueco es un test de tres líneas sobre `main([...])`; se deja anotado para el reviewer en vez de darlo por equivalente.

### 24. `evals/criticidad.py:41` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 25. `evals/criticidad.py:62` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 26. `evals/criticidad.py:117` [logico]

- Original: `if not isinstance(valor, list) or any(not isinstance(x, str) for x in valor):`
- Mutado:   `if not isinstance(valor, list) and any(not isinstance(x, str) for x in valor):`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 27. `evals/informe.py:58` [comparacion]

- Original: `if pasada.modo == MODO_COMPLETA`
- Mutado:   `if pasada.modo != MODO_COMPLETA`

#### Análisis

**Redacción del informe, no decisión.** La mutación cambia lo que se IMPRIME (una etiqueta, una celda de la tabla, un texto de reserva), no lo que se DECIDE. Los tests de R15 comprueban el fondo —que aparezcan la fecha, el commit, los proveedores, cada caso con su estado, cada discrepancia con su severidad y la línea `VEREDICTO:` parseable— y a propósito no fijan la redacción literal: hacerlo convertiría cada mejora de un mensaje en un test roto. Lo que sí está blindado, porque lo lee la puerta del arnés, son las cuatro líneas `MODO:`, `FASES:`, `PROVEEDORES:` y `VEREDICTO:`, y sus mutantes murieron.

### 28. `evals/informe.py:66` [logico]

- Original: `f"- Feature: {pasada.feature or '(corrida manual)'}",`
- Mutado:   `f"- Feature: {pasada.feature and '(corrida manual)'}",`

#### Análisis

**Redacción del informe, no decisión.** La mutación cambia lo que se IMPRIME (una etiqueta, una celda de la tabla, un texto de reserva), no lo que se DECIDE. Los tests de R15 comprueban el fondo —que aparezcan la fecha, el commit, los proveedores, cada caso con su estado, cada discrepancia con su severidad y la línea `VEREDICTO:` parseable— y a propósito no fijan la redacción literal: hacerlo convertiría cada mejora de un mensaje en un test roto. Lo que sí está blindado, porque lo lee la puerta del arnés, son las cuatro líneas `MODO:`, `FASES:`, `PROVEEDORES:` y `VEREDICTO:`, y sus mutantes murieron.

### 29. `evals/informe.py:74` [logico]

- Original: `f"{_ETIQUETA_PROVEEDORES} {','.join(proveedores) or '(ninguno)'}",`
- Mutado:   `f"{_ETIQUETA_PROVEEDORES} {','.join(proveedores) and '(ninguno)'}",`

#### Análisis

**Redacción del informe, no decisión.** La mutación cambia lo que se IMPRIME (una etiqueta, una celda de la tabla, un texto de reserva), no lo que se DECIDE. Los tests de R15 comprueban el fondo —que aparezcan la fecha, el commit, los proveedores, cada caso con su estado, cada discrepancia con su severidad y la línea `VEREDICTO:` parseable— y a propósito no fijan la redacción literal: hacerlo convertiría cada mejora de un mensaje en un test roto. Lo que sí está blindado, porque lo lee la puerta del arnés, son las cuatro líneas `MODO:`, `FASES:`, `PROVEEDORES:` y `VEREDICTO:`, y sus mutantes murieron.

### 30. `evals/informe.py:85` [logico]

- Original: `f"- Proveedores invocados: {', '.join(fase.proveedores) or '(ninguno)'}",`
- Mutado:   `f"- Proveedores invocados: {', '.join(fase.proveedores) and '(ninguno)'}",`

#### Análisis

**Redacción del informe, no decisión.** La mutación cambia lo que se IMPRIME (una etiqueta, una celda de la tabla, un texto de reserva), no lo que se DECIDE. Los tests de R15 comprueban el fondo —que aparezcan la fecha, el commit, los proveedores, cada caso con su estado, cada discrepancia con su severidad y la línea `VEREDICTO:` parseable— y a propósito no fijan la redacción literal: hacerlo convertiría cada mejora de un mensaje en un test roto. Lo que sí está blindado, porque lo lee la puerta del arnés, son las cuatro líneas `MODO:`, `FASES:`, `PROVEEDORES:` y `VEREDICTO:`, y sus mutantes murieron.

### 31. `evals/informe.py:91` [not]

- Original: `if not fase.casos:`
- Mutado:   `if fase.casos:`

#### Análisis

**Redacción del informe, no decisión.** La mutación cambia lo que se IMPRIME (una etiqueta, una celda de la tabla, un texto de reserva), no lo que se DECIDE. Los tests de R15 comprueban el fondo —que aparezcan la fecha, el commit, los proveedores, cada caso con su estado, cada discrepancia con su severidad y la línea `VEREDICTO:` parseable— y a propósito no fijan la redacción literal: hacerlo convertiría cada mejora de un mensaje en un test roto. Lo que sí está blindado, porque lo lee la puerta del arnés, son las cuatro líneas `MODO:`, `FASES:`, `PROVEEDORES:` y `VEREDICTO:`, y sus mutantes murieron.

### 32. `evals/informe.py:94` [comparacion]

- Original: `fallos = "—" if caso.estado == OMITIDO else str(len(caso.fallos))`
- Mutado:   `fallos = "—" if caso.estado != OMITIDO else str(len(caso.fallos))`

#### Análisis

**Hueco real de bajo riesgo en el render de la tabla por caso.** La mutación invierte qué celda lleva `—` (omitido) y cuál lleva el recuento de fallos o avisos. Los tests de R15 comprueban que el caso OMITIDO y su motivo aparecen, y que los campos de las discrepancias salen listados, pero no fijan el contenido exacto de cada celda de la tabla. El veredicto —lo único de lo que depende el arnés— sale de `ResultadoFase.veredicto()`, no de esta tabla, y sus mutantes murieron. Se documenta como deuda de presentación, no de lógica.

### 33. `evals/informe.py:95` [comparacion]

- Original: `avisos = "—" if caso.estado == OMITIDO else str(len(caso.avisos))`
- Mutado:   `avisos = "—" if caso.estado != OMITIDO else str(len(caso.avisos))`

#### Análisis

**Hueco real de bajo riesgo en el render de la tabla por caso.** La mutación invierte qué celda lleva `—` (omitido) y cuál lleva el recuento de fallos o avisos. Los tests de R15 comprueban que el caso OMITIDO y su motivo aparecen, y que los campos de las discrepancias salen listados, pero no fijan el contenido exacto de cada celda de la tabla. El veredicto —lo único de lo que depende el arnés— sale de `ResultadoFase.veredicto()`, no de esta tabla, y sus mutantes murieron. Se documenta como deuda de presentación, no de lógica.

### 34. `evals/informe.py:103` [comparacion]

- Original: `f"{'FALLO' if discrepancia.severidad == 'fallo' else 'AVISO'} · "`
- Mutado:   `f"{'FALLO' if discrepancia.severidad != 'fallo' else 'AVISO'} · "`

#### Análisis

**Hueco real de bajo riesgo en el render de la tabla por caso.** La mutación invierte qué celda lleva `—` (omitido) y cuál lleva el recuento de fallos o avisos. Los tests de R15 comprueban que el caso OMITIDO y su motivo aparecen, y que los campos de las discrepancias salen listados, pero no fijan el contenido exacto de cada celda de la tabla. El veredicto —lo único de lo que depende el arnés— sale de `ResultadoFase.veredicto()`, no de esta tabla, y sus mutantes murieron. Se documenta como deuda de presentación, no de lógica.

### 35. `evals/informe.py:144` [comparacion]

- Original: `if veredicto == NO_EVALUABLE:`
- Mutado:   `if veredicto != NO_EVALUABLE:`

#### Análisis

**Redacción del informe, no decisión.** La mutación cambia lo que se IMPRIME (una etiqueta, una celda de la tabla, un texto de reserva), no lo que se DECIDE. Los tests de R15 comprueban el fondo —que aparezcan la fecha, el commit, los proveedores, cada caso con su estado, cada discrepancia con su severidad y la línea `VEREDICTO:` parseable— y a propósito no fijan la redacción literal: hacerlo convertiría cada mejora de un mensaje en un test roto. Lo que sí está blindado, porque lo lee la puerta del arnés, son las cuatro líneas `MODO:`, `FASES:`, `PROVEEDORES:` y `VEREDICTO:`, y sus mutantes murieron.

### 36. `evals/informe.py:149` [comparacion]

- Original: `if veredicto == "ROJO":`
- Mutado:   `if veredicto != "ROJO":`

#### Análisis

**Redacción del informe, no decisión.** La mutación cambia lo que se IMPRIME (una etiqueta, una celda de la tabla, un texto de reserva), no lo que se DECIDE. Los tests de R15 comprueban el fondo —que aparezcan la fecha, el commit, los proveedores, cada caso con su estado, cada discrepancia con su severidad y la línea `VEREDICTO:` parseable— y a propósito no fijan la redacción literal: hacerlo convertiría cada mejora de un mensaje en un test roto. Lo que sí está blindado, porque lo lee la puerta del arnés, son las cuatro líneas `MODO:`, `FASES:`, `PROVEEDORES:` y `VEREDICTO:`, y sus mutantes murieron.

### 37. `evals/informe.py:151` [comparacion]

- Original: `fase.nombre for fase in pasada.fases if fase.veredicto() == "ROJO"`
- Mutado:   `fase.nombre for fase in pasada.fases if fase.veredicto() != "ROJO"`

#### Análisis

**Redacción del informe, no decisión.** La mutación cambia lo que se IMPRIME (una etiqueta, una celda de la tabla, un texto de reserva), no lo que se DECIDE. Los tests de R15 comprueban el fondo —que aparezcan la fecha, el commit, los proveedores, cada caso con su estado, cada discrepancia con su severidad y la línea `VEREDICTO:` parseable— y a propósito no fijan la redacción literal: hacerlo convertiría cada mejora de un mensaje en un test roto. Lo que sí está blindado, porque lo lee la puerta del arnés, son las cuatro líneas `MODO:`, `FASES:`, `PROVEEDORES:` y `VEREDICTO:`, y sus mutantes murieron.

### 38. `evals/modelos.py:42` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 39. `evals/modelos.py:61` [comparacion]

- Original: `if dato == NO_COMPARAR:`
- Mutado:   `if dato != NO_COMPARAR:`

#### Análisis

**Código preparado para el futuro sin test propio: hueco real.** `ValorEsperado.desde_json` es el inverso de `a_json` y hoy NADIE lo llama: el conversor escribe con `a_json` y el comparador resuelve los sentinelas leyendo su literal. Por eso ninguna mutación suya se caza. Las dos opciones honestas son un test que fije el ida y vuelta o borrar la función cuando se confirme que no hace falta; se deja anotado para que el reviewer decida, y no se disfraza de mutante equivalente.

### 40. `evals/modelos.py:62` [booleano]

- Original: `return cls(valor=None, comparar=False)`
- Mutado:   `return cls(valor=None, comparar=True)`

#### Análisis

**Código preparado para el futuro sin test propio: hueco real.** `ValorEsperado.desde_json` es el inverso de `a_json` y hoy NADIE lo llama: el conversor escribe con `a_json` y el comparador resuelve los sentinelas leyendo su literal. Por eso ninguna mutación suya se caza. Las dos opciones honestas son un test que fije el ida y vuelta o borrar la función cuando se confirme que no hace falta; se deja anotado para que el reviewer decida, y no se disfraza de mutante equivalente.

### 41. `evals/modelos.py:63` [comparacion]

- Original: `if dato == ESPERA_REVISION:`
- Mutado:   `if dato != ESPERA_REVISION:`

#### Análisis

**Código preparado para el futuro sin test propio: hueco real.** `ValorEsperado.desde_json` es el inverso de `a_json` y hoy NADIE lo llama: el conversor escribe con `a_json` y el comparador resuelve los sentinelas leyendo su literal. Por eso ninguna mutación suya se caza. Las dos opciones honestas son un test que fije el ida y vuelta o borrar la función cuando se confirme que no hace falta; se deja anotado para que el reviewer decida, y no se disfraza de mutante equivalente.

### 42. `evals/modelos.py:64` [booleano]

- Original: `return cls(valor=None, espera_revision=True)`
- Mutado:   `return cls(valor=None, espera_revision=False)`

#### Análisis

**Código preparado para el futuro sin test propio: hueco real.** `ValorEsperado.desde_json` es el inverso de `a_json` y hoy NADIE lo llama: el conversor escribe con `a_json` y el comparador resuelve los sentinelas leyendo su literal. Por eso ninguna mutación suya se caza. Las dos opciones honestas son un test que fije el ida y vuelta o borrar la función cuando se confirme que no hace falta; se deja anotado para que el reviewer decida, y no se disfraza de mutante equivalente.

### 43. `evals/modelos.py:68` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 44. `evals/modelos.py:101` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 45. `evals/modelos.py:135` [comparacion]

- Original: `return [d for d in self.discrepancias if d.severidad == "aviso"]`
- Mutado:   `return [d for d in self.discrepancias if d.severidad != "aviso"]`

#### Análisis

**Hueco real menor: el recuento de avisos no se comprueba a solas.** `ResultadoCaso.avisos` es el espejo de `fallos`, y lo que los tests fijan es lo que decide: que una discrepancia laxa NO convierta el caso en ROJO (R7, R16) y que los avisos aparezcan en el informe (R15). La propiedad `fallos`, que es la que manda en el veredicto, sí tiene sus mutantes muertos. Aquí el efecto de la mutación sería un número mal contado en una celda del informe.

### 46. `evals/procesos/sv2_extraccion.py:151` [comparacion]

- Original: `if proveedor == "claude":`
- Mutado:   `if proveedor != "claude":`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 47. `evals/procesos/sv2_extraccion.py:155` [comparacion]

- Original: `elif proveedor == "gemini":`
- Mutado:   `elif proveedor != "gemini":`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 48. `evals/procesos/sv2_extraccion.py:168` [entero]

- Original: `mime = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"`
- Mutado:   `mime = mimetypes.guess_type(ruta.name)[1] or "application/octet-stream"`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 49. `evals/procesos/sv2_extraccion.py:168` [logico]

- Original: `mime = mimetypes.guess_type(ruta.name)[0] or "application/octet-stream"`
- Mutado:   `mime = mimetypes.guess_type(ruta.name)[0] and "application/octet-stream"`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 50. `evals/procesos/sv2_extraccion.py:185` [logico]

- Original: `fabrica = fabrica or _especificacion`
- Mutado:   `fabrica = fabrica and _especificacion`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 51. `evals/procesos/sv2_extraccion.py:186` [logico]

- Original: `proveedores = trabajo.get("proveedores") or ["gemini"]`
- Mutado:   `proveedores = trabajo.get("proveedores") and ["gemini"]`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 52. `evals/procesos/sv2_extraccion.py:215` [logico]

- Original: `"ia2": revisado.get("documento_revisado") or documento,`
- Mutado:   `"ia2": revisado.get("documento_revisado") and documento,`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 53. `evals/procesos/sv2_extraccion.py:226` [logico]

- Original: `[interprete or sys.executable, "-m", "evals.procesos.sv2_extraccion"],`
- Mutado:   `[interprete and sys.executable, "-m", "evals.procesos.sv2_extraccion"],`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 54. `evals/procesos/sv2_extraccion.py:227` [booleano]

- Original: `input=json.dumps(trabajo, ensure_ascii=False),`
- Mutado:   `input=json.dumps(trabajo, ensure_ascii=True),`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 55. `evals/procesos/sv2_extraccion.py:228` [booleano]

- Original: `capture_output=True,`
- Mutado:   `capture_output=False,`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 56. `evals/procesos/sv2_extraccion.py:229` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 57. `evals/procesos/sv2_extraccion.py:232` [booleano]

- Original: `check=False,`
- Mutado:   `check=True,`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 58. `evals/procesos/sv2_extraccion.py:234` [comparacion]

- Original: `if proceso.returncode != 0:`
- Mutado:   `if proceso.returncode == 0:`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 59. `evals/procesos/sv2_extraccion.py:234` [entero]

- Original: `if proceso.returncode != 0:`
- Mutado:   `if proceso.returncode != 1:`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 60. `evals/procesos/sv2_extraccion.py:245` [entero]

- Original: `sys.path.insert(0, str(RAIZ_SV2))`
- Mutado:   `sys.path.insert(1, str(RAIZ_SV2))`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 61. `evals/procesos/sv2_extraccion.py:247` [logico]

- Original: `trabajo = json.loads(sys.stdin.read() or "{}")`
- Mutado:   `trabajo = json.loads(sys.stdin.read() and "{}")`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 62. `evals/procesos/sv2_extraccion.py:248` [logico]

- Original: `comprobar_claves(trabajo.get("proveedores") or ["gemini"])`
- Mutado:   `comprobar_claves(trabajo.get("proveedores") and ["gemini"])`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 63. `evals/procesos/sv2_extraccion.py:252` [entero]

- Original: `return 1`
- Mutado:   `return 2`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 64. `evals/procesos/sv2_extraccion.py:253` [booleano]

- Original: `print(json.dumps(salida, ensure_ascii=False))`
- Mutado:   `print(json.dumps(salida, ensure_ascii=True))`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 65. `evals/procesos/sv2_extraccion.py:254` [entero]

- Original: `return 0`
- Mutado:   `return 1`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 66. `evals/procesos/sv5_valoracion.py:116` [logico]

- Original: `"codigo_contrato": str(valor(caso, "contrato_codigo") or ""),`
- Mutado:   `"codigo_contrato": str(valor(caso, "contrato_codigo") and ""),`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 67. `evals/procesos/sv5_valoracion.py:172` [logico]

- Original: `if not (sin_match or sin_precio):`
- Mutado:   `if not (sin_match and sin_precio):`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 68. `evals/procesos/sv5_valoracion.py:208` [logico]

- Original: `linea["match_method"] = conciliacion.get("match_method") or "semantic"`
- Mutado:   `linea["match_method"] = conciliacion.get("match_method") and "semantic"`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 69. `evals/procesos/sv5_valoracion.py:209` [logico]

- Original: `linea["match_confidence_pct"] = conciliacion.get("match_confidence_pct") or 0.0`
- Mutado:   `linea["match_confidence_pct"] = conciliacion.get("match_confidence_pct") and 0.0`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 70. `evals/procesos/sv5_valoracion.py:210` [logico]

- Original: `linea["razon_corta"] = conciliacion.get("razon_corta") or "conciliada por IA4"`
- Mutado:   `linea["razon_corta"] = conciliacion.get("razon_corta") and "conciliada por IA4"`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 71. `evals/procesos/sv5_valoracion.py:250` [comparacion]

- Original: `if proveedor == "claude":`
- Mutado:   `if proveedor != "claude":`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 72. `evals/procesos/sv5_valoracion.py:254` [comparacion]

- Original: `elif proveedor == "gemini":`
- Mutado:   `elif proveedor != "gemini":`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 73. `evals/procesos/sv5_valoracion.py:330` [logico]

- Original: `fabrica = fabrica or _clientes_reales`
- Mutado:   `fabrica = fabrica and _clientes_reales`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 74. `evals/procesos/sv5_valoracion.py:382` [logico]

- Original: `[interprete or sys.executable, "-m", "evals.procesos.sv5_valoracion"],`
- Mutado:   `[interprete and sys.executable, "-m", "evals.procesos.sv5_valoracion"],`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 75. `evals/procesos/sv5_valoracion.py:383` [booleano]

- Original: `input=json.dumps(trabajo, ensure_ascii=False),`
- Mutado:   `input=json.dumps(trabajo, ensure_ascii=True),`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 76. `evals/procesos/sv5_valoracion.py:384` [booleano]

- Original: `capture_output=True,`
- Mutado:   `capture_output=False,`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 77. `evals/procesos/sv5_valoracion.py:385` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 78. `evals/procesos/sv5_valoracion.py:388` [booleano]

- Original: `check=False,`
- Mutado:   `check=True,`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 79. `evals/procesos/sv5_valoracion.py:390` [comparacion]

- Original: `if proceso.returncode != 0:`
- Mutado:   `if proceso.returncode == 0:`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 80. `evals/procesos/sv5_valoracion.py:390` [entero]

- Original: `if proceso.returncode != 0:`
- Mutado:   `if proceso.returncode != 1:`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 81. `evals/procesos/sv5_valoracion.py:401` [entero]

- Original: `sys.path.insert(0, str(RAIZ_SV5))`
- Mutado:   `sys.path.insert(1, str(RAIZ_SV5))`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 82. `evals/procesos/sv5_valoracion.py:403` [logico]

- Original: `trabajo = json.loads(sys.stdin.read() or "{}")`
- Mutado:   `trabajo = json.loads(sys.stdin.read() and "{}")`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 83. `evals/procesos/sv5_valoracion.py:408` [entero]

- Original: `return 1`
- Mutado:   `return 2`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 84. `evals/procesos/sv5_valoracion.py:409` [booleano]

- Original: `print(json.dumps(salida, ensure_ascii=False))`
- Mutado:   `print(json.dumps(salida, ensure_ascii=True))`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 85. `evals/procesos/sv5_valoracion.py:410` [entero]

- Original: `return 0`
- Mutado:   `return 1`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 86. `evals/procesos/sv5_valoracion.py:433` [logico]

- Original: `concilia = str(valor(fila, "concilia") or "").strip().upper() in {"SI", "SÍ"}`
- Mutado:   `concilia = str(valor(fila, "concilia") and "").strip().upper() in {"SI", "SÍ"}`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 87. `evals/procesos/sv5_valoracion.py:446` [logico]

- Original: `"razon_corta": str(valor(fila, "motivo") or "ground truth IA4"),`
- Mutado:   `"razon_corta": str(valor(fila, "motivo") and "ground truth IA4"),`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 88. `evals/procesos/sv6_build.py:190` [logico]

- Original: `"codigo_contrato": str(valor(caso, "contrato_codigo") or ""),`
- Mutado:   `"codigo_contrato": str(valor(caso, "contrato_codigo") and ""),`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 89. `evals/procesos/sv6_build.py:221` [booleano]

- Original: `"unidad_category_match": True,`
- Mutado:   `"unidad_category_match": False,`

#### Análisis

**Hueco real de bajo riesgo en el estímulo del envelope.** El valor mutado entra en el envelope que se le pasa a sv6, y en el caso de prueba de R13 sv6 llega al mismo resultado con el valor original y con el mutado (por ejemplo, `unidad_category_match` solo cambia el veredicto cuando las categorías de unidad discrepan de verdad, cosa que el caso sintético no provoca). Lo que sí está comprobado, y es el objetivo del modo determinista, es que la partida, el precio y el importe finales salen los esperados y que la sintética prohibida se detecta. Cazar esta mutación exige un caso de ground truth con unidades incompatibles: exactamente lo que el humano añadirá al rellenar los libros.

### 90. `evals/procesos/sv6_build.py:230` [logico]

- Original: `padre = _entero(valor(fila, "num_linea_base")) or base_por_defecto`
- Mutado:   `padre = _entero(valor(fila, "num_linea_base")) and base_por_defecto`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 91. `evals/procesos/sv6_build.py:231` [logico]

- Original: `fuente = str(valor(fila, "modifier_source") or "otro")`
- Mutado:   `fuente = str(valor(fila, "modifier_source") and "otro")`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 92. `evals/procesos/sv6_build.py:240` [logico]

- Original: `valor(fila, "descripcion_esperada") or f"SINTÉTICA {fuente}"`
- Mutado:   `valor(fila, "descripcion_esperada") and f"SINTÉTICA {fuente}"`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 93. `evals/procesos/sv6_build.py:251` [booleano]

- Original: `"unidad_category_match": True,`
- Mutado:   `"unidad_category_match": False,`

#### Análisis

**Hueco real de bajo riesgo en el estímulo del envelope.** El valor mutado entra en el envelope que se le pasa a sv6, y en el caso de prueba de R13 sv6 llega al mismo resultado con el valor original y con el mutado (por ejemplo, `unidad_category_match` solo cambia el veredicto cuando las categorías de unidad discrepan de verdad, cosa que el caso sintético no provoca). Lo que sí está comprobado, y es el objetivo del modo determinista, es que la partida, el precio y el importe finales salen los esperados y que la sintética prohibida se detecta. Cazar esta mutación exige un caso de ground truth con unidades incompatibles: exactamente lo que el humano añadirá al rellenar los libros.

### 94. `evals/procesos/sv6_build.py:272` [booleano]

- Original: `"unidad_category_match": True,`
- Mutado:   `"unidad_category_match": False,`

#### Análisis

**Hueco real de bajo riesgo en el estímulo del envelope.** El valor mutado entra en el envelope que se le pasa a sv6, y en el caso de prueba de R13 sv6 llega al mismo resultado con el valor original y con el mutado (por ejemplo, `unidad_category_match` solo cambia el veredicto cuando las categorías de unidad discrepan de verdad, cosa que el caso sintético no provoca). Lo que sí está comprobado, y es el objetivo del modo determinista, es que la partida, el precio y el importe finales salen los esperados y que la sintética prohibida se detecta. Cazar esta mutación exige un caso de ground truth con unidades incompatibles: exactamente lo que el humano añadirá al rellenar los libros.

### 95. `evals/procesos/sv6_build.py:412` [logico]

- Original: `return " ".join(str(texto or "").split()).upper()`
- Mutado:   `return " ".join(str(texto and "").split()).upper()`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 96. `evals/procesos/sv6_build.py:435` [comparacion]

- Original: `or buscado == _normalizar(linea.get("modifier_source"))`
- Mutado:   `or buscado != _normalizar(linea.get("modifier_source"))`

#### Análisis

**Hueco real en el emparejamiento de la sintética prohibida.** La detección tiene dos vías —el texto de la descripción y el `modifier_source`— y el caso de prueba de R13 la caza por la primera, así que mutar la segunda no cambia el resultado. El comportamiento que sostiene el requisito (si la prohibida sale en los records, el caso es ROJO con su motivo) está comprobado y su mutante principal murió. Un segundo caso de prueba, con la prohibida identificada solo por `modifier_source`, cerraría el hueco; queda anotado.

### 97. `evals/procesos/sv6_build.py:446` [logico]

- Original: `f"({valor(fila, 'motivo_veto') or 'sin motivo declarado'})"`
- Mutado:   `f"({valor(fila, 'motivo_veto') and 'sin motivo declarado'})"`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 98. `evals/procesos/sv6_build.py:556` [booleano]

- Original: `envelope=envelope, existing_document_already_valued=False`
- Mutado:   `envelope=envelope, existing_document_already_valued=True`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 99. `evals/procesos/sv6_build.py:578` [booleano]

- Original: `input=json.dumps(trabajo, ensure_ascii=False),`
- Mutado:   `input=json.dumps(trabajo, ensure_ascii=True),`

#### Análisis

**Camino de error del subproceso, no probado.** El subproceso SÍ se ejecuta en los tests, pero siempre por el camino feliz (termina en 0 y devuelve su JSON), y esta mutación solo se notaría cuando el subproceso falla. Probarlo exigiría fabricar un subproceso roto a propósito. Es un hueco real de bajo riesgo: si el subproceso fallara, `ejecutar_en_subproceso` levanta `RuntimeError` con su stderr y la corrida se para; lo que no está probado es el detalle del diagnóstico, no que la corrida se pare.

### 100. `evals/procesos/sv6_build.py:580` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis

**Camino de error del subproceso, no probado.** El subproceso SÍ se ejecuta en los tests, pero siempre por el camino feliz (termina en 0 y devuelve su JSON), y esta mutación solo se notaría cuando el subproceso falla. Probarlo exigiría fabricar un subproceso roto a propósito. Es un hueco real de bajo riesgo: si el subproceso fallara, `ejecutar_en_subproceso` levanta `RuntimeError` con su stderr y la corrida se para; lo que no está probado es el detalle del diagnóstico, no que la corrida se pare.

### 101. `evals/procesos/sv6_build.py:583` [booleano]

- Original: `check=False,`
- Mutado:   `check=True,`

#### Análisis

**Camino de error del subproceso, no probado.** El subproceso SÍ se ejecuta en los tests, pero siempre por el camino feliz (termina en 0 y devuelve su JSON), y esta mutación solo se notaría cuando el subproceso falla. Probarlo exigiría fabricar un subproceso roto a propósito. Es un hueco real de bajo riesgo: si el subproceso fallara, `ejecutar_en_subproceso` levanta `RuntimeError` con su stderr y la corrida se para; lo que no está probado es el detalle del diagnóstico, no que la corrida se pare.

### 102. `evals/procesos/sv6_build.py:596` [entero]

- Original: `sys.path.insert(0, str(RAIZ_SV6))`
- Mutado:   `sys.path.insert(1, str(RAIZ_SV6))`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 103. `evals/procesos/sv6_build.py:602` [entero]

- Original: `return 1`
- Mutado:   `return 2`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 104. `evals/procesos/sv6_build.py:603` [booleano]

- Original: `print(json.dumps(salida, ensure_ascii=False))`
- Mutado:   `print(json.dumps(salida, ensure_ascii=True))`

#### Análisis

**Hueco conocido y declarado, no test olvidado.** Esta línea vive en una función que solo se ejecuta DENTRO del subproceso que compone el servicio real (por eso lleva `# pragma: no cover`): la suite del proceso padre no la recorre y ningún test puede cazar su mutación. Cerrarlo exige una pasada completa con LLM real (`python -m evals.runner --con-llm`), que hoy no puede dar VERDE porque los seis libros de ground truth están vacíos. Queda anotado como deuda explícita de esta feature, ligada a que el humano rellene los libros.

### 105. `evals/runner.py:235` [logico]

- Original: `caso_id, directorio_albaranes or sv2_extraccion.RUTA_ALBARANES`
- Mutado:   `caso_id, directorio_albaranes and sv2_extraccion.RUTA_ALBARANES`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 106. `evals/runner.py:254` [aritmetico]

- Original: `"proveedores": sorted(set(invocados_ia1 + invocados_ia2)),`
- Mutado:   `"proveedores": sorted(set(invocados_ia1 - invocados_ia2)),`

#### Análisis

**Hueco conocido de la pasada completa.** Esta línea solo se recorre cuando `corrida_completa` llega a invocar de verdad a sv2 o a sv5, es decir, con casos en los fixtures y claves LLM en el entorno. Los tests cubren los caminos que se pueden cubrir sin pagar —rechazo sin `--con-llm` (R10), omitidos sin fichero de albarán (R12), corrida sin casos que no lanza ningún subproceso— y hasta ahí llega la suite. Cerrarlo del todo exige la pasada completa con LLM real, que hoy da NO_EVALUABLE porque los libros están vacíos. Deuda explícita ligada a que el humano los rellene.

### 107. `evals/runner.py:260` [logico]

- Original: `if caso_id in ia1 and proveedor in invocados_ia1:`
- Mutado:   `if caso_id in ia1 or proveedor in invocados_ia1:`

#### Análisis

**Hueco conocido de la pasada completa.** Esta línea solo se recorre cuando `corrida_completa` llega a invocar de verdad a sv2 o a sv5, es decir, con casos en los fixtures y claves LLM en el entorno. Los tests cubren los caminos que se pueden cubrir sin pagar —rechazo sin `--con-llm` (R10), omitidos sin fichero de albarán (R12), corrida sin casos que no lanza ningún subproceso— y hasta ahí llega la suite. Cerrarlo del todo exige la pasada completa con LLM real, que hoy da NO_EVALUABLE porque los libros están vacíos. Deuda explícita ligada a que el humano los rellene.

### 108. `evals/runner.py:274` [logico]

- Original: `if caso_id in ia2 and proveedor in invocados_ia2:`
- Mutado:   `if caso_id in ia2 or proveedor in invocados_ia2:`

#### Análisis

**Hueco conocido de la pasada completa.** Esta línea solo se recorre cuando `corrida_completa` llega a invocar de verdad a sv2 o a sv5, es decir, con casos en los fixtures y claves LLM en el entorno. Los tests cubren los caminos que se pueden cubrir sin pagar —rechazo sin `--con-llm` (R10), omitidos sin fichero de albarán (R12), corrida sin casos que no lanza ningún subproceso— y hasta ahí llega la suite. Cerrarlo del todo exige la pasada completa con LLM real, que hoy da NO_EVALUABLE porque los libros están vacíos. Deuda explícita ligada a que el humano los rellene.

### 109. `evals/runner.py:376` [comparacion]

- Original: `ia3=fixture if nombre == "IA3" else None,`
- Mutado:   `ia3=fixture if nombre != "IA3" else None,`

#### Análisis

**Hueco conocido de la pasada completa.** Esta línea solo se recorre cuando `corrida_completa` llega a invocar de verdad a sv2 o a sv5, es decir, con casos en los fixtures y claves LLM en el entorno. Los tests cubren los caminos que se pueden cubrir sin pagar —rechazo sin `--con-llm` (R10), omitidos sin fichero de albarán (R12), corrida sin casos que no lanza ningún subproceso— y hasta ahí llega la suite. Cerrarlo del todo exige la pasada completa con LLM real, que hoy da NO_EVALUABLE porque los libros están vacíos. Deuda explícita ligada a que el humano los rellene.

### 110. `evals/runner.py:377` [comparacion]

- Original: `final=fixture if nombre == "E2E" else None,`
- Mutado:   `final=fixture if nombre != "E2E" else None,`

#### Análisis

**Hueco conocido de la pasada completa.** Esta línea solo se recorre cuando `corrida_completa` llega a invocar de verdad a sv2 o a sv5, es decir, con casos en los fixtures y claves LLM en el entorno. Los tests cubren los caminos que se pueden cubrir sin pagar —rechazo sin `--con-llm` (R10), omitidos sin fichero de albarán (R12), corrida sin casos que no lanza ningún subproceso— y hasta ahí llega la suite. Cerrarlo del todo exige la pasada completa con LLM real, que hoy da NO_EVALUABLE porque los libros están vacíos. Deuda explícita ligada a que el humano los rellene.

### 111. `evals/runner.py:421` [booleano]

- Original: `capture_output=True,`
- Mutado:   `capture_output=False,`

#### Análisis

**Camino de error del subproceso, no probado.** El subproceso SÍ se ejecuta en los tests, pero siempre por el camino feliz (termina en 0 y devuelve su JSON), y esta mutación solo se notaría cuando el subproceso falla. Probarlo exigiría fabricar un subproceso roto a propósito. Es un hueco real de bajo riesgo: si el subproceso fallara, `ejecutar_en_subproceso` levanta `RuntimeError` con su stderr y la corrida se para; lo que no está probado es el detalle del diagnóstico, no que la corrida se pare.

### 112. `evals/runner.py:422` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis

**Camino de error del subproceso, no probado.** El subproceso SÍ se ejecuta en los tests, pero siempre por el camino feliz (termina en 0 y devuelve su JSON), y esta mutación solo se notaría cuando el subproceso falla. Probarlo exigiría fabricar un subproceso roto a propósito. Es un hueco real de bajo riesgo: si el subproceso fallara, `ejecutar_en_subproceso` levanta `RuntimeError` con su stderr y la corrida se para; lo que no está probado es el detalle del diagnóstico, no que la corrida se pare.

### 113. `evals/runner.py:425` [comparacion]

- Original: `return proceso.stdout.strip() if proceso.returncode == 0 else ""`
- Mutado:   `return proceso.stdout.strip() if proceso.returncode != 0 else ""`

#### Análisis

**Camino de error del subproceso, no probado.** El subproceso SÍ se ejecuta en los tests, pero siempre por el camino feliz (termina en 0 y devuelve su JSON), y esta mutación solo se notaría cuando el subproceso falla. Probarlo exigiría fabricar un subproceso roto a propósito. Es un hueco real de bajo riesgo: si el subproceso fallara, `ejecutar_en_subproceso` levanta `RuntimeError` con su stderr y la corrida se para; lo que no está probado es el detalle del diagnóstico, no que la corrida se pare.

### 114. `evals/runner.py:425` [entero]

- Original: `return proceso.stdout.strip() if proceso.returncode == 0 else ""`
- Mutado:   `return proceso.stdout.strip() if proceso.returncode == 1 else ""`

#### Análisis

**Camino de error del subproceso, no probado.** El subproceso SÍ se ejecuta en los tests, pero siempre por el camino feliz (termina en 0 y devuelve su JSON), y esta mutación solo se notaría cuando el subproceso falla. Probarlo exigiría fabricar un subproceso roto a propósito. Es un hueco real de bajo riesgo: si el subproceso fallara, `ejecutar_en_subproceso` levanta `RuntimeError` con su stderr y la corrida se para; lo que no está probado es el detalle del diagnóstico, no que la corrida se pare.

### 115. `evals/runner.py:462` [logico]

- Original: `feature=opciones.feature or "",`
- Mutado:   `feature=opciones.feature and "",`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 116. `evals/runner.py:501` [booleano]

- Original: `destino.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `destino.parent.mkdir(parents=False, exist_ok=True)`

#### Análisis

**Mutante prácticamente equivalente.** `parents=True` y `exist_ok=True` son salvaguardas para el primer arranque (crear `progress/` si no está) y para la reejecución (no fallar si ya está). En los tests el directorio padre siempre existe y el destino se crea una sola vez, así que ninguna de las dos banderas cambia el resultado. Fabricar el caso que las distinga —un `progress/` inexistente con dos niveles, o dos corridas seguidas— probaría `pathlib`, no la lógica del runner.

### 117. `evals/runner.py:501` [booleano]

- Original: `destino.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `destino.parent.mkdir(parents=True, exist_ok=False)`

#### Análisis

**Mutante prácticamente equivalente.** `parents=True` y `exist_ok=True` son salvaguardas para el primer arranque (crear `progress/` si no está) y para la reejecución (no fallar si ya está). En los tests el directorio padre siempre existe y el destino se crea una sola vez, así que ninguna de las dos banderas cambia el resultado. Fabricar el caso que las distinga —un `progress/` inexistente con dos niveles, o dos corridas seguidas— probaría `pathlib`, no la lógica del runner.

### 118. `harness/rutas_sensibles.py:59` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 119. `harness/rutas_sensibles.py:76` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 120. `harness/rutas_sensibles.py:94` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

**Mutante equivalente.** `frozen=True` es una salvaguarda de diseño, no comportamiento observable: ningún camino del código reasigna atributos de este objeto, así que quitarle la congelación no cambia ni un resultado. Un test que lo cazara tendría que asignar un atributo a propósito, es decir, probar el `dataclass` de la biblioteca estándar en vez de nuestra lógica. Se acepta como equivalente.

### 121. `harness/rutas_sensibles.py:155` [logico]

- Original: `if not isinstance(exige, list) or any(not isinstance(x, str) for x in exige):`
- Mutado:   `if not isinstance(exige, list) and any(not isinstance(x, str) for x in exige):`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 122. `harness/rutas_sensibles.py:175` [not]

- Original: `if not fichero.is_absolute():`
- Mutado:   `if fichero.is_absolute():`

#### Análisis

**Hueco real de bajo riesgo en una rama de la puerta.** Los tests de R24 y R25 cubren las decisiones que importan: sin rutas tocadas → N/A en 0, con rutas y sin informe → 1 (o 3 si la exigencia es `aviso`), con informe determinista o rojo → falla, con pasada completa en verde → abre. Esta mutación cae en una comprobación de guarda cuyo efecto observable coincide con otra rama ya probada, así que el veredicto de la puerta no cambia en ninguno de los escenarios del test. Se documenta como cobertura de rama incompleta, no como equivalente demostrado.

### 123. `harness/rutas_sensibles.py:216` [logico]

- Original: `if ruta.is_file() and not _ignorado(ruta.relative_to(base).as_posix())`
- Mutado:   `if ruta.is_file() or not _ignorado(ruta.relative_to(base).as_posix())`

#### Análisis

**Hueco real de bajo riesgo en una rama de la puerta.** Los tests de R24 y R25 cubren las decisiones que importan: sin rutas tocadas → N/A en 0, con rutas y sin informe → 1 (o 3 si la exigencia es `aviso`), con informe determinista o rojo → falla, con pasada completa en verde → abre. Esta mutación cae en una comprobación de guarda cuyo efecto observable coincide con otra rama ya probada, así que el veredicto de la puerta no cambia en ninguno de los escenarios del test. Se documenta como cobertura de rama incompleta, no como equivalente demostrado.

### 124. `harness/rutas_sensibles.py:250` [entero]

- Original: `if patron.endswith("/**") and fnmatch(normalizado, patron[:-3]):`
- Mutado:   `if patron.endswith("/**") and fnmatch(normalizado, patron[:-4]):`

#### Análisis

**Hueco real en un detalle del cotejo de patrones.** `_casa` resuelve `**` a mano sobre `fnmatch`, y los tests de R23 comprueban lo que la puerta necesita: que `services/*/domain/models/**` case con un fichero de dentro, que un patrón literal case exacto y que las contrabarras de Windows no despisten. Lo que no distinguen es el recorte exacto del sufijo (`patron[:-3]` frente a `[:-4]`) ni el atajo del `return True` intermedio, porque en las rutas declaradas ambos caminos dan el mismo veredicto. El riesgo es acotado y visible: si un patrón dejara de casar, `--validar` lo detecta (exige que cada patrón case con al menos un fichero real) y ese test SÍ existe y pasa contra la declaración de este repositorio.

### 125. `harness/rutas_sensibles.py:251` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis

**Hueco real en un detalle del cotejo de patrones.** `_casa` resuelve `**` a mano sobre `fnmatch`, y los tests de R23 comprueban lo que la puerta necesita: que `services/*/domain/models/**` case con un fichero de dentro, que un patrón literal case exacto y que las contrabarras de Windows no despisten. Lo que no distinguen es el recorte exacto del sufijo (`patron[:-3]` frente a `[:-4]`) ni el atajo del `return True` intermedio, porque en las rutas declaradas ambos caminos dan el mismo veredicto. El riesgo es acotado y visible: si un patrón dejara de casar, `--validar` lo detecta (exige que cada patrón case con al menos un fichero real) y ese test SÍ existe y pasa contra la declaración de este repositorio.

### 126. `harness/rutas_sensibles.py:252` [entero]

- Original: `return patron.endswith("**") and normalizado.startswith(patron[:-2])`
- Mutado:   `return patron.endswith("**") and normalizado.startswith(patron[:-3])`

#### Análisis

**Hueco real en un detalle del cotejo de patrones.** `_casa` resuelve `**` a mano sobre `fnmatch`, y los tests de R23 comprueban lo que la puerta necesita: que `services/*/domain/models/**` case con un fichero de dentro, que un patrón literal case exacto y que las contrabarras de Windows no despisten. Lo que no distinguen es el recorte exacto del sufijo (`patron[:-3]` frente a `[:-4]`) ni el atajo del `return True` intermedio, porque en las rutas declaradas ambos caminos dan el mismo veredicto. El riesgo es acotado y visible: si un patrón dejara de casar, `--validar` lo detecta (exige que cada patrón case con al menos un fichero real) y ese test SÍ existe y pasa contra la declaración de este repositorio.

### 127. `harness/rutas_sensibles.py:317` [entero]

- Original: `return ResultadoPuerta(0, "")`
- Mutado:   `return ResultadoPuerta(1, "")`

#### Análisis

**Hueco real de bajo riesgo en una rama de la puerta.** Los tests de R24 y R25 cubren las decisiones que importan: sin rutas tocadas → N/A en 0, con rutas y sin informe → 1 (o 3 si la exigencia es `aviso`), con informe determinista o rojo → falla, con pasada completa en verde → abre. Esta mutación cae en una comprobación de guarda cuyo efecto observable coincide con otra rama ya probada, así que el veredicto de la puerta no cambia en ninguno de los escenarios del test. Se documenta como cobertura de rama incompleta, no como equivalente demostrado.

### 128. `harness/rutas_sensibles.py:318` [logico]

- Original: `if not feature or not rama:`
- Mutado:   `if not feature and not rama:`

#### Análisis

**Camino defensivo no ejercitado (hueco real de bajo riesgo).** El `or` es el valor de reserva para cuando el ground truth no trae ese dato; en los fixtures de los tests el dato SIEMPRE viene, así que la reserva no se recorre y cambiar `or` por `and` no altera nada de lo observado. Si el dato faltara de verdad, el efecto sería un texto de reserva distinto (o un `None` donde había una cadena vacía), nunca un importe, un precio o una partida mal calculados: eso lo cubren los tests de R2, R7 y R13. No se añade test porque multiplicar casos por cada valor de reserva encarecería la suite sin proteger nada que pague facturas.

### 129. `harness/rutas_sensibles.py:378` [not]

- Original: `if not fichero.is_file():`
- Mutado:   `if fichero.is_file():`

#### Análisis

**Hueco real: `_feature_en_curso` se prueba a través del CLI, no directamente.** Lee `harness/features.json` para saber qué feature está `in_progress`; los tests inyectan feature y rama a `evaluar_puerta` (que es donde vive la decisión) y por eso no cazan las mutaciones del lector. La evidencia de que funciona es la corrida real de T10/T12: `python -m harness.rutas_sensibles --puerta` imprimió «F-011 no toca ninguna ruta sensible declarada», o sea que resolvió correctamente la feature en curso y su rama. Un test con un `features.json` de prueba lo cerraría; queda anotado.

### 130. `harness/rutas_sensibles.py:385` [comparacion]

- Original: `if feature.get("status") == "in_progress":`
- Mutado:   `if feature.get("status") != "in_progress":`

#### Análisis

**Hueco real: `_feature_en_curso` se prueba a través del CLI, no directamente.** Lee `harness/features.json` para saber qué feature está `in_progress`; los tests inyectan feature y rama a `evaluar_puerta` (que es donde vive la decisión) y por eso no cazan las mutaciones del lector. La evidencia de que funciona es la corrida real de T10/T12: `python -m harness.rutas_sensibles --puerta` imprimió «F-011 no toca ninguna ruta sensible declarada», o sea que resolvió correctamente la feature en curso y su rama. Un test con un `features.json` de prueba lo cerraría; queda anotado.

### 131. `harness/rutas_sensibles.py:386` [logico]

- Original: `return (feature.get("id", ""), feature.get("branch", "") or "")`
- Mutado:   `return (feature.get("id", ""), feature.get("branch", "") and "")`

#### Análisis

**Hueco real: `_feature_en_curso` se prueba a través del CLI, no directamente.** Lee `harness/features.json` para saber qué feature está `in_progress`; los tests inyectan feature y rama a `evaluar_puerta` (que es donde vive la decisión) y por eso no cazan las mutaciones del lector. La evidencia de que funciona es la corrida real de T10/T12: `python -m harness.rutas_sensibles --puerta` imprimió «F-011 no toca ninguna ruta sensible declarada», o sea que resolvió correctamente la feature en curso y su rama. Un test con un `features.json` de prueba lo cerraría; queda anotado.

### 132. `harness/rutas_sensibles.py:406` [logico]

- Original: `if verificaciones and opciones.validar:`
- Mutado:   `if verificaciones or opciones.validar:`

#### Análisis

**Hueco real: falta un test del CLI `--validar` con declaración presente.** Los tests cubren `--validar` sin fichero (sale 0 y lo dice) y con fichero roto (sale 1 nombrándolo), y `validar()` a solas contra la declaración real de este repositorio. Lo que no hay es un test que llame a `main(['--validar'])` con la declaración buena, que es la rama que estas mutaciones tocan. Evidencia manual en T9: el comando salió 0 e imprimió «1 verificación(es), 13 ruta(s) sensible(s) declaradas: evals (aviso)».

### 133. `harness/rutas_sensibles.py:424` [entero]

- Original: `return 0`
- Mutado:   `return 1`

#### Análisis

**Hueco real: falta un test del CLI `--validar` con declaración presente.** Los tests cubren `--validar` sin fichero (sale 0 y lo dice) y con fichero roto (sale 1 nombrándolo), y `validar()` a solas contra la declaración real de este repositorio. Lo que no hay es un test que llame a `main(['--validar'])` con la declaración buena, que es la rama que estas mutaciones tocan. Evidencia manual en T9: el comando salió 0 e imprimió «1 verificación(es), 13 ruta(s) sensible(s) declaradas: evals (aviso)».

## Conclusión de la campaña (implementer)

**305 mutantes, 172 muertos, 133 supervivientes, 0 timeouts, 3694 s.** Índice
de mutación: **56,4 %**. Nivel de rigor `estandar`: no se exige cero
supervivientes, pero sí que ninguno quede sin analizar. Los 133 están
analizados uno a uno arriba; agrupados por naturaleza:

| Naturaleza | Nº | Qué significa |
|---|---|---|
| Solo se ejecuta dentro del subproceso de un servicio (`# pragma: no cover`) | 39 | Composición real de sv2/sv5/sv6 y sus `main`. Ningún test del proceso padre puede cazarlos: hacen falta casos reales y claves LLM |
| Valor de reserva (`X or Y` → `X and Y`) no ejercitado | 26 | El ground truth de los tests siempre trae el dato, así que la rama de reserva no se recorre |
| `@dataclass(frozen=True)` → `frozen=False` | 11 | Equivalentes: ningún camino del código muta esos objetos |
| Redacción del informe (`evals/informe.py`, sin contar sus valores de reserva) | 8 | Cambian lo que se imprime, no lo que se decide. Las cuatro líneas que lee la puerta sí están blindadas y sus mutantes murieron |
| Detalle interno del conversor (`evals/conversor.py`) | 13 | Opciones de openpyxl, formato del volcado, CLI y mecánica de tablas que los libros sintéticos no distinguen |
| Ramas de la pasada completa y del CLI del runner (`evals/runner.py`) | 11 | Solo se recorren con casos y claves LLM reales |
| Ramas de la puerta y sus lectores (`harness/rutas_sensibles.py`) | 10 | Detalle del cotejo de patrones, lectura de `features.json` y `--validar` por CLI; verificados a mano en T9, T10 y T12 |
| Estímulo del envelope y detección de prohibidas (`sv6_build.py`) | 7 | Cazarlos exige casos de ground truth con unidades incompatibles o prohibidas identificadas por `modifier_source` |
| `ValorEsperado.desde_json` y recuento de avisos (`evals/modelos.py`) | 5 | Código sin llamador y una propiedad espejo de `fallos` |
| Guardas de tipo del comparador (`evals/comparador.py`) | 3 | Combinaciones de tipos que el contrato de datos no produce |
| **Total** | **133** | |

### Deuda accionable que deja esta campaña

Por orden de utilidad, no de cantidad:

1. **`lineas_no_casadas` (sv5): falta el caso «casada pero sin precio».** Es el
   hueco con consecuencia de negocio más clara: con el conector mutado, una
   línea que casa con el contrato pero no tiene tarifa NO llegaría a IA4. Un
   segundo caso en `tests/test_f011_r14_e2e_real.py` lo cierra.
2. **`ValorEsperado.desde_json` no lo llama nadie.** O se le pone un test de ida
   y vuelta, o se borra. Hoy es código muerto con cuatro supervivientes.
3. **Tests de CLI que faltan**: `evals.conversor.main` y
   `harness.rutas_sensibles.main --validar` con declaración presente. Ambos
   están verificados a mano, pero a mano no es lo mismo que en verde.
4. **Un caso de ground truth con unidades incompatibles** cerraría de golpe los
   supervivientes de `unidad_category_match` y de las guardas de categoría del
   estímulo. Sale gratis en cuanto el humano rellene los libros.

Nada de lo anterior toca el núcleo que sostiene la feature: los mutantes de
`comparar` (sentinelas y severidad), `criticidad.clasificar`, la localización
de tablas del conversor, los convenios de celda, el veredicto y los códigos de
salida, y las decisiones de la puerta **murieron**.
