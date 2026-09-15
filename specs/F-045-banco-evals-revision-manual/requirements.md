<!-- specs/F-045-banco-evals-revision-manual/requirements.md -->
# F-045 · Requisitos

El origen, el material y los nueve patrones de defecto están en la ficha de
`harness/features.json` (id F-045). Aquí va el CÓMO, no el qué.

**Alcance**: SEMBRAR el banco de evals con la revisión manual del humano y
dejar catalogadas las decisiones de mejora. Ningún arreglo de sv2, sv5 o sv6
entra aquí: salen como fichas propias (ver `design.md` §7).

**El origen sigue creciendo**: nada de esta spec depende de valores ni de
recuentos concretos; las cifras de `design.md` van fechadas y son orientativas.

## A. El importador de la revisión

R1. El sistema debe ofrecer `python -m evals.revision --origen <fichero.xlsx>`,
que lee la tabla plana de la revisión manual y actualiza los seis libros de
`evals/ground_truth/`.

R2. El sistema debe repartir cada columna de la tabla plana entre IA1, IA2,
IA3, IA4, `INPUTS` y `RESULTADO_FINAL` según la tabla de reparto de
`design.md` §3, que es normativa.

R3. El sistema debe separar el fallo de EXTRACCIÓN del fallo de VALORACIÓN:
un dato que el albarán imprime va al libro de la fase que lo lee (IA1/IA2) y
un dato que el sistema decide (partida final, precio de contrato o de oferta,
contrato elegido, obra deducida) va al libro de la fase que lo decide
(IA3/IA4) y a `RESULTADO_FINAL`. Ningún dato decidido se escribe en IA1.

R4. CUANDO la columna que declara el origen de un dato diga que ese dato NO
viene en el albarán, el sistema debe escribir la celda correspondiente de IA1
vacía (se espera `null`) y el valor en el libro de la fase que lo decide.

R5. SI la tabla plana trae una etiqueta de familia, de origen de línea o de
origen de precio que el vocabulario versionado no reconoce, ENTONCES el
sistema debe abortar sin escribir ni un libro y listar las etiquetas no
reconocidas con su fila de origen.

R6. El sistema debe traducir la familia escrita por el humano a una de las
familias del catálogo único (`ruesma_comun.contratos.familias`) y a su
pestaña del banco, mediante un fichero de datos versionado. Esa traducción
etiqueta ground truth escrito por una persona; NO es clasificación de
producción y no puede usarse para decidir la familia de ningún albarán.

R7. El sistema debe dar a cada albarán un `caso_id` estable entre pasadas,
con el prefijo de su pestaña (`GEN/HOR/MOR/RES/BOM/COM/ALQ-NNN`), guardado en
un mapa versionado con su clave natural (CIF del proveedor + código de
albarán normalizado).

R8. CUANDO el albarán importado ya tenga `caso_id` en ese mapa, el sistema
debe reutilizarlo y actualizar sus filas, nunca crear un caso nuevo.

## B. Convenios de celda (qué se compara y qué no)

R9. CUANDO una celda de la tabla plana esté vacía, el sistema debe escribir
`?` en el libro destino: vacío en un libro significa «se espera `null`» y el
humano no ha afirmado eso.

R10. MIENTRAS el reparto derive de una columna de origen que el dato no está
en el papel, el sistema debe escribir la celda vacía (R4) y no `?`: ahí el
`null` sí lo afirma el humano.

R11. El sistema debe escribir `?` en `numero_albaran` de IA1 cuando el código
de la tabla plana sea la clave del documento y no el literal impreso, y debe
contar esos casos en su informe como «el patrón 9 no se vigila aquí».

R12. El sistema debe escribir `?` en `obra_codigo` y `obra_nombre` de IA1 y
llevar la obra esperada a `RESULTADO_FINAL`: deducir la obra no es extraer.

R13. El sistema NO debe inventar ground truth. SI una fila no permite decidir
a qué fase pertenece un dato, ENTONCES escribe `?` y lo cuenta en su informe,
nunca un valor supuesto.

R14. El sistema debe emitir un informe de importación con, por libro y
columna, cuántas celdas se escribieron con valor, cuántas con `?` y cuántas
vacías, y la lista de filas descartadas con su motivo.

## C. Escritura de los libros

R15. El sistema debe escribir cada fila en la pestaña de su familia,
respetando las tablas que el conversor declara y sin mover sus filas de
título.

R16. CUANDO el sistema vaya a escribir un libro, debe copiarlo antes a
`evals/ground_truth/copias/<fichero>.<AAAAMMDD-HHMM>.xlsx`.

R17. El sistema NO debe tocar las filas cuyo `caso_id` no pertenezca a esta
importación: la revisión no pisa lo que el humano escribió a mano.

R18. CUANDO se ejecute dos veces seguidas sobre el mismo origen, el sistema
debe dejar los mismos libros y los mismos fixtures (salvo la copia de R16).

R19. `python -m evals.conversor` debe convertir los libros resultantes sin
error y sin hallazgos del barrido de datos sensibles.

## D. Los albaranes de entrada

R20. El sistema debe emparejar cada caso con su PDF de origen por el código
de albarán normalizado contenido en el nombre del fichero, y emitir el plan de
copia a `evals/inputs/albaranes/<caso_id>.pdf`.

R21. SI un caso no tiene PDF, o un nombre de fichero encaja con más de un
caso, ENTONCES el sistema debe dejarlo fuera del plan y listarlo como
huérfano, sin adivinar.

R22. El sistema NO debe versionar ni los PDF ni los `.xlsx`: al repositorio
entran solo los fixtures JSON y los ficheros de datos del importador.

## E. Lo que ya falla hoy en el banco (deuda declarada)

R23. El sistema debe comparar IA1 e IA2 solo por sus campos observables, como
ya hacen IA3 e IA4, de modo que `caso_id`, `fichero_albaran` y `comentario`
dejen de contar como discrepancia.

R24. El sistema debe declarar en el informe de la pasada los campos del
ground truth de IA1 e IA2 que hoy no son observables (p. ej. `unidad`,
pendiente de F-024), en vez de darlos por buenos o por fallidos.

## F. El catálogo de patrones y el filtro de robustez

R25. El sistema debe mantener `evals/patrones.json`, versionado, con un
registro por patrón de defecto: id, título, fase donde se detecta, casos del
banco que lo vigilan, decisión candidata y estado.

R26. El sistema debe exigir que cada caso citado en `evals/patrones.json`
exista en `evals/fixtures/`, y que cada patrón cite al menos un caso.

R27. CUANDO se registre una decisión candidata de mejora, el sistema debe
exigirle respuesta a las dos preguntas del filtro de robustez: ¿sigue
funcionando si el proveedor cambia el formato del papel? ¿y si aparece un
proveedor nuevo sin histórico?

R28. SI alguna de las dos respuestas es «no», ENTONCES la decisión debe
quedar con estado `descartada` y su motivo, y no genera ficha de arreglo.
Una decisión que estrecha el espacio de búsqueda (buscar la partida entre las
de la obra; deducir la obra solo entre las que tienen contrato con ese
proveedor) pasa el filtro; una regla atada a un formato o a un proveedor
concreto, no.

R29. El sistema debe proponer las fichas de arreglo en `harness/features.json`
ordenadas por cuántas líneas de la revisión toca cada patrón, y con estado
`pending`.

## G. Verificaciones que solo puede hacer el humano

R30. El humano debe validar la tabla de reparto de `design.md` §3 y el mapa
de familias antes de que los libros se den por sembrados.

R31. La pasada `python -m evals.runner --con-llm --feature F-045` cuesta
dinero y la lanza el humano; su informe queda en `progress/evals_F-045.md`.
