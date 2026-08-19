<!-- specs/F-035-instalador-no-pisa-estado/requirements.md -->
# F-035 · Requisitos — el instalador en modo `actualizar` no puede pisar estado del proyecto

> **AVISO DE UBICACIÓN DEL CÓDIGO.** Ningún requisito de esta spec se
> implementa en `albaranes`. El sujeto de todos ellos (**«el instalador»**) es
> `instalar_arnes.ps1`, que vive en la **raíz** del repositorio
> `C:\Users\pgris\PycharmProjects\arnes-base` (hoy en 1.5.2). `albaranes` es
> solo el repositorio **consumidor**: aquí vive la spec y aquí se comprobará el
> resultado la próxima vez que se actualice el arnés. Ver `design.md` §0.

## Glosario (vinculante para leer los requisitos)

| Término | Significado exacto |
|---|---|
| **payload** | El árbol `arnes-base/arnes-base/**`: lo que el instalador copia al proyecto. |
| **destino** | El repositorio que recibe el arnés (`-Destino`). |
| **ruta relativa** | Ruta dentro del payload/destino, con `/` como separador (`harness/features.json`). |
| **categoría (a) arnés puro** | Fichero cuyo contenido es 100 % genérico: la versión del payload siempre es mejor o igual que la del destino. |
| **categoría (b) adaptado** | Fichero que mezcla contenido genérico mejorable con contenido propio del proyecto (marcas `[ADAPTAR]`, `$adaptar`, configuración local). |
| **categoría (c) estado del proyecto** | Fichero cuya versión en el payload es una **plantilla semilla**: aceptarla no aporta nunca nada y destruye siempre trabajo acumulado. |
| **política** | El fichero de datos que declara a qué categoría pertenece cada ruta (ver R1). |

---

## G1 · La política de clasificación

**R1.** El sistema debe declarar la categoría de cada ruta del payload en un
fichero de datos versionado, `politica_ficheros.json`, situado en la **raíz**
de `arnes-base` (junto a `instalar_arnes.ps1`) y **fuera del payload**, de modo
que ese fichero no se copie nunca a ningún proyecto destino.

**R2.** El sistema debe clasificar cada ruta en exactamente una de tres
categorías —`arnes_puro`, `adaptado`, `estado_del_proyecto`— más una cuarta
lista, `excluidos`, de rutas del payload que no se copian nunca.

**R3.** El sistema debe resolver la categoría de una ruta por **especificidad**:
una entrada exacta (`specs/SPECS.md`) gana siempre a una entrada de prefijo
(`specs/**`), y entre dos entradas de prefijo gana la más larga.

**R4.** SI, al recorrer el payload, el instalador encuentra un fichero cuya ruta
relativa no casa con ninguna entrada de la política, ENTONCES el sistema debe
**abortar sin escribir nada** en el destino, nombrar la ruta sin clasificar y
salir con código distinto de 0.

**R5.** El sistema debe admitir en `estado_del_proyecto` rutas que hoy no
existen en el payload (protección preventiva), y no debe tratar su ausencia
como error.

**R6.** El sistema debe clasificar como `estado_del_proyecto`, como mínimo:
`harness/features.json`, `progress/**`, `docs/ARCHITECTURE.md`,
`docs/referencia/**` (con la excepción exacta de su `README.md`, ver R7),
`BACKLOG.md`, `harness/servicios.json`, `harness/rutas_sensibles.json`,
`.claude/settings.local.json` y `.env`.

**R7.** El sistema debe clasificar como `adaptado`: `CLAUDE.md`,
`CHECKPOINTS.md`, `harness/init.sh`, `docs/CONVENTIONS.md`,
`docs/referencia/README.md` y `.claude/settings.json`.

**R8.** El sistema debe clasificar como `arnes_puro` el resto del payload:
`.claude/agents/*.md`, `specs/SPECS.md`, `scripts/*`, `tests/*.py`,
`harness/*.py`, `harness/rigor.json`, `harness/*.ejemplo.json` y
`harness/VERSION`.

---

## G2 · Qué hace el modo `actualizar` con cada categoría

**R9.** MIENTRAS el modo es `actualizar`, CUANDO un fichero de categoría (c)
existe en el destino, el sistema debe **no mostrar su diff, no preguntar y no
escribirlo**, y contabilizarlo como `protegido`.

**R10.** El sistema debe garantizar que **ninguna combinación de parámetros**
—incluidos `-Forzar`, la respuesta `T` (sobrescribir todos) y
`-IgnorarPrecondiciones`— sobrescribe un fichero de categoría (c).

**R11.** MIENTRAS el modo es `actualizar` y no se ha pasado `-PreguntarTodo`,
CUANDO un fichero de categoría (a) existe en el destino y su contenido difiere
realmente (R21), el sistema debe sobrescribirlo **sin preguntar**, previo
backup (R14), y contabilizarlo como `actualizado`.

**R12.** DONDE se pasa `-PreguntarTodo`, el sistema debe preguntar también por
los ficheros de categoría (a), con el mismo diálogo que usa para los (b).

**R13.** MIENTRAS el modo es `actualizar`, CUANDO un fichero de categoría (b)
existe en el destino y difiere realmente, el sistema debe mostrar el diff y
preguntar, indicando en el propio prompt que la opción por defecto es
**CONSERVAR**.

**R14.** CUANDO el instalador pregunta por un fichero de categoría (b) y recibe
una respuesta vacía (Intro), el sistema debe **conservar** el fichero del
destino.

**R15.** SI el instalador no puede leer una respuesta (consola no interactiva),
ENTONCES el sistema debe conservar el fichero del destino y decirlo, sin
bucle infinito.

**R16.** CUANDO un fichero del payload no existe en el destino, el sistema debe
copiarlo **sea cual sea su categoría**, incluida (c), y contabilizarlo como
`nuevo`: una plantilla semilla en un proyecto que aún no la tiene es
exactamente lo que hay que instalar.

---

## G3 · Backup antes de pisar

**R17.** MIENTRAS el modo es `actualizar` y no se ha pasado `-SoloDiff`, el
sistema debe crear, **antes de recorrer el payload**, un directorio de backup
con sello de fecha, situado **fuera del repositorio destino**, por defecto en
`%LOCALAPPDATA%\arnes-base\backups\<nombre-del-destino>\<yyyyMMdd-HHmmss>\`, y
admitir `-DirBackup <ruta>` para cambiar la raíz.

**R18.** SI el directorio de backup no puede crearse, ENTONCES el sistema debe
abortar **antes de escribir nada** en el destino y salir con código distinto
de 0.

**R19.** CUANDO el instalador va a sobrescribir un fichero existente del
destino, el sistema debe copiar antes la versión del destino al backup,
conservando su ruta relativa.

**R20.** SI la copia al backup de un fichero concreto falla, ENTONCES el sistema
debe **conservar** ese fichero (no sobrescribirlo), seguir con los demás,
contabilizarlo aparte y terminar con código distinto de 0.

**R21.** El sistema debe escribir en el directorio de backup un
`MANIFIESTO.md` con: ruta absoluta del destino, versión del arnés de origen y
la que había en el destino, modo y parámetros, rama y commit `HEAD` del destino
(si es un repo git), y la lista de ficheros respaldados.

**R22.** CUANDO el instalador termina habiendo respaldado al menos un fichero,
el sistema debe imprimir la ruta absoluta del directorio de backup.

---

## G4 · Ruido de comparación

**R23.** El sistema debe considerar que dos ficheros de texto tienen el mismo
contenido cuando coinciden tras normalizar los finales de línea (CRLF/LF) y
descartar el BOM inicial, y no debe ofrecerlos ni contarlos como distintos.

> Motivo medido el 2026-08-19 sobre este mismo repositorio: de los 13 ficheros
> que el instalador 1.5.2 marca como distintos entre payload y `albaranes`,
> **8 son idénticos salvo el final de línea** (el destino no tiene
> `.gitattributes` y hace checkout en CRLF; el payload está en LF). Ese ruido
> es lo que empuja a pulsar `T`, que es la tecla que provocó el incidente.

**R24.** El sistema debe excluir del recorrido del payload los artefactos de
herramienta: `**/__pycache__/**`, `**/*.pyc`, `**/*.pyo` y `**/.pytest_cache/**`.

---

## G5 · Precondiciones de ejecución

**R25.** MIENTRAS el modo es `actualizar` y el destino es un repositorio git,
SI hay cambios sin commitear (incluidos ficheros sin seguimiento) **en alguna
de las rutas que el instalador va a tocar en esta pasada**, ENTONCES el sistema
debe abortar antes de escribir nada, listar esas rutas y salir con código
distinto de 0.

> El criterio es «sucio **en lo que voy a tocar**», no «sucio en cualquier
> parte». Exigir el árbol entero limpio haría el instalador inusable en un repo
> con trabajo legítimo en curso —el caso normal—, y la gente acabaría pasando
> siempre la vía de escape, que es tanto como no tenerla. Ver `design.md` §6.

**R26.** El sistema debe ofrecer `-IgnorarPrecondiciones` como única vía de
escape de R25, y debe dejar constancia de su uso en el `MANIFIESTO.md` del
backup.

**R27.** MIENTRAS el modo es `actualizar` y el destino es un repositorio git, el
sistema debe **avisar sin bloquear** de la rama actual y, si existe una rama
local `dev`, de cuántos commits está `HEAD` por detrás de ella.

> No se bloquea por nombre de rama: el instalador no puede saber cuál es la
> rama de integración de cada proyecto (`dev`, `main`, `master`, `trunk`).
> Adivinarlo produce falsos bloqueos; avisar con el número real de commits de
> retraso da al humano el dato que le faltó el 2026-08-19 (25 commits).

**R28.** SI el destino no es un repositorio git, ENTONCES el sistema debe
avisarlo explícitamente (no hay red de seguridad de git; solo el backup) y
continuar.

---

## G6 · Resumen y trazabilidad

**R29.** CUANDO el instalador termina, el sistema debe imprimir un resumen que
cuente por separado: `nuevos`, `ya iguales`, `iguales salvo finales de línea`,
`actualizados`, `conservados`, `saltados` y **`protegidos`**.

**R30.** CUANDO hay al menos un fichero `protegido`, el sistema debe listar sus
rutas y explicar en una línea que son estado del proyecto y que el instalador
no los toca por diseño.

**R31.** MIENTRAS se pasa `-SoloDiff`, el sistema debe no escribir nada en el
destino (ni backup, ni `harness/ARNES_VERSION.md`, ni `.gitignore`) y debe
mostrar igualmente qué ficheros quedarían `protegidos`.

---

## G7 · Lo que no puede cambiar (no regresión)

**R32.** MIENTRAS el modo es `instalar`, el sistema debe mantener el
comportamiento actual: copia lo que falta y no sobrescribe nada existente.

**R33.** El sistema debe seguir escribiendo `harness/ARNES_VERSION.md` con la
versión instalada, y seguir añadiendo de forma aditiva e idempotente el bloque
del arnés al `.gitignore` del destino.

**R34.** El sistema debe seguir funcionando en **PowerShell 5.1 sin
dependencias externas** (sin módulos que haya que instalar).

---

## G8 · Documentación y versión

**R35.** El sistema debe documentar en `GUIA_INSTALACION.md` las tres
categorías, dónde vive la política, cómo se clasifica un fichero nuevo del
payload, el backup y las precondiciones, en una sección propia de la versión
nueva.

**R36.** El sistema debe corregir en `GUIA_INSTALACION.md` el texto de la
sección C que hoy dice «qué conservar casi siempre» sobre `features.json` y
`docs/ARCHITECTURE.md`: esos ficheros ya no se ofrecen, luego no hay nada que
conservar a mano.

**R37.** El sistema debe subir `arnes-base/arnes-base/harness/VERSION` al
siguiente número **MINOR** disponible en el momento de implementar (ver
`design.md` §8: 1.7.0 si F-034 ya cerró como 1.6.0), con su `ARNES_FECHA`.

**R38.** El texto que `instalar_arnes.ps1` escribe en
`harness/ARNES_VERSION.md` debe dejar de afirmar que «los ficheros con marcas
de adaptación casi siempre hay que conservarlos» como si fuera trabajo del
humano, y decir qué protege el instalador por sí mismo.

---

## G9 · Verificación

**R39.** El sistema debe incluir en `arnes-base` una prueba ejecutable,
reproducible y sin dependencias externas, que cree un repositorio de mentira,
le instale el arnés, le ponga un `harness/features.json` con **N** features
(N ≥ 2), ejecute el instalador en modo `actualizar` **con `-Forzar`** y
compruebe que ese fichero sigue teniendo exactamente N features.

**R40.** La prueba debe cubrir además: (i) ARCHITECTURE.md y `progress/*`
intactos, (ii) un fichero de categoría (a) sí actualizado, (iii) un fichero de
categoría (b) conservado ante respuesta vacía, (iv) existencia y contenido del
backup y su manifiesto, (v) el bloqueo por precondición sucia y su vía de
escape, (vi) que sucio fuera de las rutas tocadas **no** bloquea, (vii) que el
modo `instalar` no pisa nada, (viii) integridad de la política (R4).

**R41.** CUANDO alguna comprobación de la prueba falla, el sistema debe salir
con código distinto de 0 y nombrar la comprobación fallida.
