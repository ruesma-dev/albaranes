<!-- specs/F-045-banco-evals-revision-manual/requirements.md -->
# F-045 · Requisitos

El origen, el material y los nueve patrones de defecto están en la ficha de
`harness/features.json` (id F-045). Aquí va el CÓMO. **Alcance**: SEMBRAR el
banco de evals con la revisión manual y catalogar las decisiones de mejora;
ningún arreglo de sv2, sv5 o sv6 entra aquí (fichas propias, `design.md` §7).
El origen sigue creciendo: nada aquí depende de valores ni de recuentos
concretos; las cifras de `design.md` van fechadas y son orientativas.

## A. El importador de la revisión

R1. El sistema debe ofrecer `python -m evals.revision --origen <fichero.xlsx>`,
que lee la tabla plana de la revisión y actualiza los seis libros de
`evals/ground_truth/`.

R2. El sistema debe repartir cada columna de la tabla plana entre IA1, IA2,
IA3, IA4, `INPUTS` y `RESULTADO_FINAL` según la tabla de reparto de
`design.md` §3, que es normativa.

R3. El sistema debe separar el fallo de EXTRACCIÓN del de VALORACIÓN: lo que el
albarán imprime va al libro de la fase que lo lee (IA1/IA2); lo que el sistema
decide (partida final, precio de contrato o de oferta, contrato elegido, obra
deducida) va al de la fase que lo decide (IA3/IA4) y a `RESULTADO_FINAL`.

R4. CUANDO la columna que declara el origen de un dato diga que ese dato NO
viene en el albarán, el sistema debe escribir la celda correspondiente de IA1
vacía (se espera `null`) y el valor en el libro de la fase que lo decide.

R5. SI la tabla plana trae una etiqueta de familia, de origen de línea o de
origen de precio que el vocabulario versionado no reconoce, ENTONCES el sistema
debe abortar sin escribir ni un libro y listar las etiquetas con su fila.

R6. El sistema debe traducir la familia escrita por el humano a una del
catálogo único (`ruesma_comun.contratos.familias`) y a su pestaña, mediante un
fichero de datos versionado. Esa traducción etiqueta ground truth escrito por
una persona: NO es clasificación de producción (§14 de la arquitectura).

R7. El sistema debe dar a cada albarán un `caso_id` estable entre pasadas, con
el prefijo de su pestaña (`GEN/HOR/MOR/RES/BOM/COM/ALQ-NNN`), guardado en un
mapa versionado con su clave natural (CIF + código de albarán normalizado).

R8. CUANDO el albarán ya tenga `caso_id` en ese mapa, el sistema debe
reutilizarlo y actualizar sus filas, nunca crear un caso nuevo.

## B. Convenios de celda (qué se compara y qué no)

R9. CUANDO la columna de COMENTARIOS esté vacía, el sistema debe marcar el caso
como **no regresión** y comparar sus valores como cualquier otro: ese vacío
significa que eso salió BIEN y hay que seguir comprobando en cada pasada que lo
sigue haciendo. Un comentario vacío NUNCA produce un `?`.

R10. CUANDO la columna de COMENTARIOS traiga texto, el sistema debe marcar el
caso como **defecto conocido**, copiar el texto a la columna `comentario` del
libro (campo laxo, no comparado) y clasificarlo contra un patrón de
`evals/patrones.json`. El valor esperado se compara exactamente igual.

R11. CUANDO la celda de RESULTADO ESPERADO esté vacía, el sistema debe escribir
`?` —el humano no ha afirmado el valor bueno— salvo que su columna diga otra.

R12. El sistema debe leer de un fichero de datos versionado qué significa el
vacío en CADA columna: `descuento` = sin descuento (`null`, factor 1 de §13);
`LER` = no aplica a esa familia, sin fila de IA2; `partida`, `precio unitario`
e `importe` = `?`.

R13. MIENTRAS el reparto derive de una columna de origen que el dato no está en
el papel, el sistema debe escribir la celda vacía (R4) y no `?`: ahí el `null`
sí lo afirma el humano.

R14. El sistema debe escribir `?` en `numero_albaran`, `obra_codigo` y
`obra_nombre` de IA1 —el código de la tabla plana es la clave del documento, no
el literal impreso, y deducir la obra no es extraer—, llevar la obra esperada a
`RESULTADO_FINAL` y contar en su informe que el patrón 9 no se vigila.

R15. SI una fila no permite decidir a qué fase pertenece un dato, ENTONCES el
sistema debe escribir `?` y contarlo: nunca un valor supuesto.

R16. El sistema debe emitir un informe de importación con: por libro y columna,
cuántas celdas llevan valor, cuántas `?` y cuántas vacías; el reparto de casos
entre **no regresión** y **defecto conocido**; y las filas descartadas con su
motivo. Los `?` son la única ceguera del banco.

## C. Escritura de los libros

R17. El sistema debe escribir cada fila en la pestaña de su familia, respetando
las tablas que el conversor declara y sin mover sus filas de título.

R18. CUANDO el sistema vaya a escribir un libro, debe copiarlo antes a
`evals/ground_truth/copias/<fichero>.<AAAAMMDD-HHMM>.xlsx`.

R19. El sistema NO debe tocar las filas cuyo `caso_id` no sea de esta
importación: la revisión no pisa lo que el humano escribió a mano.

R20. CUANDO se ejecute dos veces seguidas sobre el mismo origen, el sistema
debe dejar los mismos libros y los mismos fixtures (salvo la copia de R18).

R21. `python -m evals.conversor` debe convertir los libros resultantes sin
error y sin hallazgos del barrido de datos sensibles.

## D. Los albaranes de entrada

R22. El sistema debe emparejar cada caso con su PDF por el código de albarán
normalizado contenido en el nombre del fichero, y emitir el plan de copia a
`evals/inputs/albaranes/<caso_id>.pdf`.

R23. SI un caso no tiene PDF, o un nombre encaja con más de un caso, ENTONCES
debe quedar fuera del plan y listado como huérfano, sin adivinar.

R24. El sistema NO debe versionar ni los PDF ni los `.xlsx`: al repositorio
entran solo los fixtures JSON y los ficheros de datos del importador.

## E. Lo que ya falla hoy en el banco (deuda declarada)

R25. El sistema debe comparar IA1 e IA2 solo por sus campos observables, como
ya hacen IA3 e IA4, de modo que `caso_id`, `fichero_albaran` y `comentario`
dejen de contar como discrepancia.

R26. El sistema debe declarar en el informe de la pasada los campos de IA1 e
IA2 que hoy no son observables (p. ej. `unidad`, pendiente de F-024), en vez de
darlos por buenos o por fallidos.

## F. El catálogo de patrones y el filtro de robustez

R27. El sistema debe mantener `evals/patrones.json`, versionado, con un
registro por patrón (id, título, fase, casos que lo vigilan, decisión candidata
y estado) más la lista de casos de **no regresión**: los que hoy deben salir en
VERDE y no pertenecen a ningún patrón.

R28. El sistema debe exigir que cada caso citado en `evals/patrones.json`
exista en `evals/fixtures/`, y que cada patrón cite al menos un caso.

R29. CUANDO se registre una decisión candidata de mejora, el sistema debe
exigirle respuesta a las dos preguntas del filtro de robustez: ¿sigue
funcionando si el proveedor cambia el formato del papel? ¿y si aparece un
proveedor nuevo sin histórico? SI alguna respuesta es «no», ENTONCES queda
`descartada` con su motivo y no genera ficha. Estrechar el espacio de búsqueda
(la partida entre las de la obra; la obra entre las que tienen contrato con ese
proveedor) pasa el filtro; una regla atada a un formato o a un proveedor, no.

R30. El sistema debe proponer las fichas de arreglo en `harness/features.json`
ordenadas por cuántas líneas toca cada patrón, y en estado `pending`.

## G. Verificaciones que solo puede hacer el humano

R31. El humano debe validar la tabla de reparto de `design.md` §3, la política
de vacíos por columna (R12) y el mapa de familias antes de sembrar.

R32. La pasada `python -m evals.runner --con-llm --feature F-045` cuesta dinero
y la lanza el humano; su informe queda en `progress/evals_F-045.md`, y en él
los casos de no regresión deben salir en VERDE.
