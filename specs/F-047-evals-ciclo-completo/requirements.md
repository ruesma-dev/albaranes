<!-- specs/F-047-evals-ciclo-completo/requirements.md -->
# F-047 · Requisitos — el banco recorre el ciclo completo

Notación EARS. Cada R se traduce a >= 1 test. El porqué está en la ficha
(`harness/features.json`); aquí va solo lo exigible.

## A · El ciclo

**R1.** El sistema debe ofrecer una corrida en CICLO COMPLETO que, por cada
caso, encadene IA1 → IA2 → contrato → IA3 → IA4 → build final alimentando cada
fase con la salida real de la anterior.

**R2.** El ciclo debe encadenar por los MISMOS hand-off de producción —envelope
de sv2, `ContextoValoracion`, envelope de sv5— y no por estructuras inventadas
para el eval.

**R3.** CUANDO el ciclo ejecuta un caso, el sistema debe guardar la salida de
las CUATRO fases y del build, y comparar cada una contra el ground truth ya
volcado de esa fase, sin regenerar ni tocar los libros de `evals/ground_truth/`.

**R4.** SI una fase no produce salida para un caso, ENTONCES las fases
posteriores de ese caso deben quedar OMITIDO con el motivo heredado, y nunca
VERDE.

**R5.** El ciclo debe obtener la clasificación (familia/tipología) del propio
sistema, y comparar la obtenida con la que declara `INPUTS.CASOS.tipologia`, en
vez de inyectarla como entrada.

## B · Atribución del fallo (la decisión crítica)

**R6.** El sistema debe atribuir cada discrepancia a UNA de tres etiquetas:
`PROPIO` (nace en esta fase), `ARRASTRADO` (nace aguas arriba) o
`INDETERMINADO` (no se puede ligar con fiabilidad).

**R7.** El sistema debe marcar una discrepancia `ARRASTRADO` si —y solo si— el
campo tiene dependencias declaradas Y al menos una de ellas falló, en la misma
corrida, para el MISMO caso y la MISMA línea. La discrepancia debe llevar la
fase de origen y el campo concreto que la causó.

**R8.** SI la fase anterior falló pero ninguna dependencia declarada del campo
lo hizo, ENTONCES la discrepancia es `PROPIO`: no basta con que falle la fase.

**R9.** CUANDO una línea del ground truth no aparece en la salida de IA1, el
sistema debe marcar `ARRASTRADO` a IA1 toda discrepancia posterior de esa misma
línea, con motivo «línea ausente en IA1».

**R10.** SI la identidad de una línea discrepa en IA1 (su descripción difiere,
aunque sea como aviso), ENTONCES toda discrepancia posterior de esa línea debe
ser `INDETERMINADO`: el emparejado por `num_linea` deja de ser fiable.

**R11.** Una fase debe ser ROJA solo por sus fallos `PROPIO`. Los `ARRASTRADO`
no cuentan como defecto de la fase que los exhibe, pero constan en su informe.

**R12.** MIENTRAS haya `INDETERMINADO` y ningún fallo `PROPIO`, el veredicto de
la pasada debe ser NO_EVALUABLE, nunca VERDE.

**R13.** El mapa de dependencias debe ser un fichero versionado y legible.

**R14.** SI el mapa declara una dependencia sobre un campo que ninguna
proyección produce, ENTONCES la carga debe ABORTAR nombrando el campo.

## C · Qué ground truth se reutiliza

**R15.** El ciclo debe comparar contra los seis libros tal como están: IA1, IA2,
IA3, IA4 y RESULTADO_FINAL siguen siendo la expectativa de su fase.

**R16.** El sistema debe tratar `INPUTS.LINEAS_ALBARAN`, `INPUTS.CONTRATO_LINEAS`
y las condiciones que produce una IA como entrada que en ciclo YA NO se inyecta,
y declararlas en el informe bajo «entrada que ahora produce el sistema».

**R17.** `INPUTS.CASOS.contrato_codigo` debe pasar de entrada a expectativa: el
sistema debe comparar el contrato que eligió con el declarado, y ese fallo es
`PROPIO` de la fase de contrato.

**R18.** SI una condición del libro no la produce ninguna fase ni el contrato
leído —caso de `tamano_contenedor_contrato`—, ENTONCES el criterio que dependa
de ella debe quedar NO_EVALUABLE y declararse; nunca inyectarse a mano.

## D · Las dos formas de correr

**R19.** El sistema debe conservar las corridas por fase con entradas de los
libros, pedibles explícitamente, para aislar un defecto sin pagar el ciclo.

**R20.** CUANDO se pide una pasada con LLM sin decir la forma, el sistema debe
ejecutar el CICLO: es la forma por defecto.

**R21.** El modo determinista debe seguir sin hacer ni una llamada de red y sin
cambiar su veredicto respecto de hoy.

**R22.** El informe debe declarar en línea parseable qué forma se corrió; solo
la del ciclo vale como evidencia de pasada completa.

## E · Dependencias del entorno

**R23.** ANTES de consumir ningún caso, el sistema debe comprobar claves LLM,
credenciales de sigrid-api, ficheros de albarán y fixtures de los casos pedidos.

**R24.** SI falta alguna dependencia, ENTONCES el sistema debe nombrar CUÁL falta
y salir NO_EVALUABLE, sin haber gastado una sola llamada.

**R25.** SI sigrid-api no responde, corta o devuelve error para un caso,
ENTONCES ese caso debe quedar NO_EVALUABLE por «contrato no disponible»: jamás
se valora contra un contrato vacío.

**R26.** El sistema debe usar sigrid-api SOLO en lectura de contratos: ni
descarga de PDF, ni escritura, ni SQL directo contra Sigrid.

**R27.** El sistema debe agrupar la consulta de contratos por (CIF, obra) para
no repetirla por caso, y respetar los topes de sigrid-api (1.000 filas, 230 s).

## F · El coste

**R28.** `--casos` debe acotar el ciclo entero, no solo sus primeras fases.

**R29.** El sistema debe guardar la salida cruda de cada caso y fase fuera de
git, y reaprovecharla cuando se le pida.

**R30.** SI cambia el sha256 del albarán, el proveedor, el modelo o el prompt,
ENTONCES la salida reaprovechable debe descartarse y el informe debe decir por
qué se reejecutó.

**R31.** El sistema debe permitir reejecutar desde una fase concreta hacia
adelante reutilizando las anteriores.

**R32.** Las salidas crudas llevan precios de proveedor: NUNCA se versionan y
NUNCA entran en `evals/fixtures/`, cuya única puerta sigue siendo el conversor.

## G · El informe

**R33.** El informe del ciclo debe conservar los ejes de hoy —no regresión
frente a defecto conocido, y los rojos que nacen esperados agrupados aparte— y
sumarles el de atribución.

**R34.** Cada fase debe traer su cuadro de casos con fallos propios,
arrastrados, indeterminados y omitidos, contados por separado.

**R35.** El informe debe traer un apartado con los fallos ordenados por fase de
ORIGEN, para leer de un vistazo dónde nace cada cosa.

**R36.** Las secciones de campos no observables y de campos sin clasificar deben
seguir separadas y con su texto de hoy.

## H · Verificación manual

**R37.** MANUAL (humano): una pasada de ciclo acotada a un subconjunto de casos
de familias distintas, revisando que la atribución apunta a la fase correcta.

**R38.** MANUAL (humano): la pasada de ciclo sobre los 59 casos, que cuesta API
real y decide el humano cuándo se lanza.
