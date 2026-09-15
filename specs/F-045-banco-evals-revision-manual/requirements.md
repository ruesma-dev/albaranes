<!-- specs/F-045-banco-evals-revision-manual/requirements.md -->
# F-045 · Requisitos

Origen, material y los nueve patrones: ficha de `harness/features.json` (F-045).
**Alcance**: sembrar el banco con la revisión manual y catalogar las mejoras;
ningún arreglo de sv2/sv5/sv6 entra aquí (fichas propias, `design.md` §7).

## A. El importador de la revisión

R1. El sistema debe ofrecer `python -m evals.revision --origen <fichero.xlsx>`,
que lee la tabla plana y actualiza los seis libros de `evals/ground_truth/`.

R2. El sistema debe repartir cada columna de la tabla plana entre IA1, IA2, IA3,
IA4, `INPUTS` y `RESULTADO_FINAL` según `design.md` §3, que es normativa.

R3. El sistema debe separar el fallo de EXTRACCIÓN del de VALORACIÓN: lo que el
albarán imprime va al libro de la fase que lo lee (IA1/IA2); lo que el sistema
decide (partida, precio, contrato, obra) va al de la fase que lo decide y a
`RESULTADO_FINAL`.

R4. CUANDO la columna de origen diga que un dato NO viene en el albarán, el
sistema debe dejar la celda de IA1 vacía (`null` afirmado, nunca `?`) y escribir
el valor en el libro de la fase que lo decide.

R5. SI la tabla plana trae una etiqueta de familia, de origen de línea o de
precio que el vocabulario versionado no reconoce, ENTONCES el sistema debe
abortar sin escribir nada y listar las etiquetas con su fila.

R6. El sistema debe traducir la etiqueta del Excel a UNA de las CUATRO familias
de DOCUMENTO del catálogo (`ruesma_comun.contratos.familias`) y a su pestaña con
la tabla de `design.md` §5 bis, en un único fichero de datos. La pestaña NO es la
familia, y esto etiqueta ground truth humano: no clasifica producción (§14).

R7. El sistema debe dar a cada albarán un `caso_id` estable, con el prefijo de
su pestaña (`GEN/HOR/MOR/RES/BOM/COM/ALQ-NNN`), y guardar en un mapa versionado
`caso_id` ↔ código ↔ nombre original ↔ formato ↔ `gemelo_de`: es lo que permite
volver al papel cuando un eval falle.

R8. CUANDO el albarán ya tenga `caso_id` en ese mapa, el sistema debe
reutilizarlo y actualizar sus filas, nunca crear un caso nuevo.

## B. Convenios de celda (qué se compara y qué no)

R9. CUANDO la columna de COMENTARIOS esté vacía, el sistema debe marcar el caso
como **no regresión** y comparar sus valores igual: ese vacío dice que salió
BIEN y hay que seguir comprobándolo. Nunca produce un `?`.

R10. CUANDO la columna de COMENTARIOS traiga texto, el sistema debe marcar el
caso como **defecto conocido**, copiar el texto a `comentario` del libro (laxo,
no comparado) y clasificarlo contra un patrón; el valor se compara igual.

R11. CUANDO la celda de RESULTADO ESPERADO esté vacía, o la fila no permita
decidir a qué fase pertenece un dato, el sistema debe escribir `?` y contarlo
(salvo que su columna diga otra cosa): nunca un valor supuesto.

R12. Un fichero versionado debe declarar qué significa el vacío en CADA columna:
`descuento` = sin descuento (`null`, §13); `LER` = no aplica, sin fila de IA2;
el resto = `?`.

R12 bis. El ground truth de residuos debe seguir los tres criterios de
`design.md` §5 ter: incremento por LER deducido del **canon** por código LER;
**mínimo facturable de 1 tn en lo que se pesa** —canon y tratamiento—, con el
movimiento de contenedor intacto en unidades; e **incremento por año** también
en residuos. Ninguno está implementado: nacen como defecto conocido.

R13. El sistema debe escribir `?` en `numero_albaran`, `obra_codigo` y
`obra_nombre` de IA1 —el código de la tabla plana es la clave del documento, no
el literal impreso, y deducir la obra no es extraer— y la obra en el FINAL.

R14. El informe de importación debe traer: por libro y columna, cuántas celdas
llevan valor, `?` y vacías; el reparto entre **no regresión** y **defecto
conocido**; y las filas descartadas con su motivo (R21).

## C. Escritura de los libros

R15. El sistema debe escribir cada fila en la pestaña de su familia, respetando
las tablas que el conversor declara y sin mover sus filas de título.

R16. CUANDO vaya a escribir un libro, debe copiarlo antes a
`evals/ground_truth/copias/<fichero>.<AAAAMMDD-HHMM>.xlsx`.

R17. El sistema NO debe tocar las filas cuyo `caso_id` no sea de esta
importación: la revisión no pisa lo que el humano escribió a mano.

R18. CUANDO se ejecute dos veces seguidas sobre el mismo origen, el sistema debe
dejar los mismos libros y los mismos fixtures (salvo la copia de R16).

R19. `python -m evals.conversor` debe convertir los libros resultantes sin error
y sin hallazgos del barrido de datos sensibles.

## D. Los documentos de entrada (PDF **e imagen**)

R20. El sistema debe sacar el código del nombre del fichero —si trae `_`, lo de
después del último; si no, el nombre entero—, admitir `.pdf`, `.png`, `.jpg` y
`.jpeg` y copiar a `evals/inputs/albaranes/<caso_id><extensión>`. Manda el código
del papel, NUNCA el persistido (precedente: `SS-0801977` por `SS-0001977`).

R21. SI dos ficheros resuelven al mismo código, un código no está en el Excel,
una fila no tiene fichero, o un nombre queda vacío tras la regla, ENTONCES el
caso sale del plan y el informe lo lista uno a uno: ruidoso, nunca silencioso.

R22. CUANDO el mismo albarán exista en PDF y en imagen, los dos nombres dan el
MISMO código y el sistema debe crear DOS casos, `<caso_id>` y `<caso_id>-IMG`,
mismo ground truth y distinta entrada, hermanados por `gemelo_de`: no es un
choque de duplicados, es el par que aísla el formato.

R23. El sistema debe MEDIR en cada corrida el camino de lectura de cada caso
—`pdf_texto`, `pdf_escaneado` o `imagen`— y agrupar por él el informe: se mide,
NO se afirma en un libro. Un fallo solo en el gemelo de imagen es FORMATO.

R24. El sistema NO debe versionar ningún documento de entrada, PDF o imagen:
`.gitignore` debe cubrir `evals/inputs/albaranes/` (hoy solo cubre `*.pdf`).

## E. Lo que ya falla hoy en el banco (deuda declarada)

R25. El sistema debe comparar IA1 e IA2 solo por sus campos observables, como ya
hacen IA3 e IA4: `caso_id`, `fichero_albaran` y `comentario` dejan de contar.

R26. El informe de la pasada debe declarar los campos de IA1 e IA2 que hoy no
son observables (p. ej. `unidad`, F-024), en vez de darlos por buenos o malos.

## F. El catálogo de patrones y el filtro de robustez

R27. El sistema debe mantener `evals/patrones.json`, versionado: un registro por
patrón (id, título, fase, casos, decisión, estado) más los casos de **no
regresión**, los que hoy deben salir en VERDE.

R28. El sistema debe exigir que cada caso citado en `evals/patrones.json` exista
en `evals/fixtures/`, y que cada patrón cite al menos un caso.

R29. CUANDO se registre una decisión candidata de mejora, el sistema debe
exigirle respuesta a las dos preguntas del filtro de robustez: ¿sigue
funcionando si el proveedor cambia el formato del papel? ¿y si aparece uno
nuevo? SI alguna es «no», ENTONCES queda `descartada` y no genera ficha.
Estrechar el espacio de búsqueda (la partida entre las de la obra; la obra entre
las del proveedor) pasa el filtro; una regla atada a un formato o proveedor, no.

R30. Las fichas de arreglo se proponen en `harness/features.json` ordenadas por
cuántas líneas toca cada patrón, en estado `pending`.

## G. Verificaciones que solo puede hacer el humano

R31. El humano debe validar, antes de sembrar, la tabla de reparto (§3) y la
política de vacíos por columna (R12). El mapa de etiquetas (§5 bis) y el alcance
del mínimo de 1 tn (§5 ter) los cerró el 2026-09-15.

R32. La pasada `--con-llm` cuesta dinero y la lanza el humano; su informe queda
en `progress/evals_F-045.md`, con los casos de no regresión en VERDE y el
resumen agrupado por camino de lectura.
