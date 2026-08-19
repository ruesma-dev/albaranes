<!-- specs/F-035-instalador-no-pisa-estado/design.md -->
# F-035 · Diseño — el instalador en modo `actualizar` no puede pisar estado del proyecto

## 0. Dónde vive el código (leer antes que nada)

Esta feature es **inter-repositorio**. Lo escribo explícito porque es la
trampa principal para el implementer y para el reviewer:

| Repositorio | Qué se toca |
|---|---|
| `C:\Users\pgris\PycharmProjects\arnes-base` | **Todo el código.** `instalar_arnes.ps1` (raíz), `politica_ficheros.json` (raíz, nuevo), `tests_instalador/prueba_instalador.ps1` (nuevo), `GUIA_INSTALACION.md` (raíz), `arnes-base/harness/VERSION` (payload). |
| `C:\Users\pgris\PycharmProjects\albaranes` | **Solo `specs/F-035-instalador-no-pisa-estado/`** (esta spec) y las anotaciones de `progress/`. Ni una línea de código. |

Consecuencias que el reviewer debe tener presentes:

- **No hay líneas Python ni SQL cambiadas en `albaranes`.** La puerta de
  cobertura de líneas cambiadas de `harness/init.sh` y la campaña
  `python -m harness.mutacion --feature F-035` **no tienen alcance que medir en
  este repositorio**: darán 0 líneas y 0 mutantes. Eso no es «puerta pasada»,
  es «puerta sin sujeto». La evidencia equivalente para el rigor `estandar`
  declarado está en §7 (fase RED real + campaña de mutación manual sobre el
  script PowerShell).
- **`bash harness/init.sh` en verde en `albaranes` sigue siendo obligatorio**,
  pero aquí demuestra únicamente que la spec no ha roto nada, no que el
  instalador funcione.
- El trabajo en `arnes-base` se hace en su propio repositorio, con sus propios
  commits. `arnes-base` está hoy en 1.5.2 y al día con su remoto
  (`9224a5a`). No se hace `push` sin petición del humano.

**Encaje en la arquitectura de `albaranes`**: ninguno. F-035 no toca ningún
servicio del pipeline (sv1..sv6) ni `services/albaranes-comun`, así que la
estructura hexagonal de `docs/ARCHITECTURE.md` no aplica. El límite de
microservicio se respeta de la forma más limpia posible: la responsabilidad
—instalar y actualizar el arnés— ya vive en otro repositorio y ahí se queda.

---

## 1. Cómo decide hoy `instalar_arnes.ps1` qué pisar (lectura del código real)

Fuente: `arnes-base/instalar_arnes.ps1`, 269 líneas, versión 1.5.2.

**No existe ninguna lista de ficheros del payload.** El payload es
implícito: es el árbol `arnes-base/arnes-base/**` y se descubre por barrido
del sistema de ficheros.

```powershell
# línea 34
$Origen = Join-Path $PSScriptRoot 'arnes-base'
# línea 112
$ficheros = Get-ChildItem -Path $OrigenAbs -Recurse -File | Sort-Object FullName
```

La **única** lista declarada es la de exclusiones, con **una sola entrada**:

```powershell
# línea 32
$Excluidos = @('harness/gitignore.arnes')
```

Es decir: **todo fichero que exista bajo el payload se ofrece al destino**, sin
distinción de ninguna clase. Dos consecuencias verificadas hoy:

1. `arnes-base/harness/features.json` (la plantilla con la feature de ejemplo
   `F-001`, 27 líneas) y `arnes-base/docs/ARCHITECTURE.md` (37 líneas, puro
   esqueleto `[ADAPTAR]`) se ofrecen como si fueran mejoras del arnés. Los
   destinos reales tienen 387 y 192 líneas respectivamente.
2. El payload arrastra artefactos no versionados que el barrido sí ve:
   `arnes-base/.pytest_cache/**`, `arnes-base/harness/__pycache__/*.pyc`,
   `arnes-base/tests/__pycache__/*.pyc`. `git ls-files` no los lista, pero
   `Get-ChildItem -Recurse -File` sí, y se copian al destino.

**El instalador no distingue en absoluto los ficheros con marcas de
adaptación.** El literal `ADAPTAR` no aparece en `instalar_arnes.ps1`. La única
mención a las marcas es prosa: la coletilla que el script escribe dentro de
`harness/ARNES_VERSION.md` (líneas 252-254) diciendo que «casi siempre hay que
conservarlos», y la tabla de `GUIA_INSTALACION.md` (líneas 128-137). Ninguna de
las dos es ejecutable. Los ficheros del payload que hoy llevan marcas
`[ADAPTAR]` son seis: `CHECKPOINTS.md`, `CLAUDE.md`, `docs/ARCHITECTURE.md`,
`docs/referencia/README.md`, `harness/features.json`, `harness/init.sh`
(`.claude/settings.json` lleva una clave `"$adaptar"` en minúscula, que ni
siquiera casa con ese grep).

**Igualdad de contenido** — `Test-MismoContenido`, líneas 102-106: SHA-256
byte a byte. No normaliza finales de línea. Medido hoy entre el payload y
`albaranes`: 13 ficheros «distintos», de los cuales **8 son idénticos salvo
CRLF** (`harness/rigor.json`, `harness/backlog.py`, `harness/rigor.py`,
`harness/rutas_sensibles.py`, `harness/mutacion_paralela.py`,
`tests/test_backlog_md.py`, `tests/test_mutacion_informe.py`,
`.claude/agents/reviewer.md`). El payload está en LF (`arnes-base` tiene
`.gitattributes` con `* text=auto eol=lf`); `albaranes` **no tiene
`.gitattributes`**, así que hace checkout en CRLF. Ese ruido es una causa
contribuyente directa del incidente: 13 diffs, de los cuales 8 aparentemente
vacíos, invitan a pulsar `T`.

**Dónde se separan los dos modos** — línea 136:

```powershell
if ($Modo -eq 'instalar') {
    Write-Host "[SALTADO]  $relBar (ya existe y es distinto; ...)"
```

El modo `instalar` es seguro por construcción: si el fichero existe y difiere,
lo salta. El modo `actualizar` cae al diálogo de las líneas 142-185.

**El `Copy-Item -Force`** — **línea 179**, dentro de la rama
`if ($respuesta -eq 's')`:

```powershell
    if ($respuesta -eq 's') {
        Copy-Item $f.FullName $dest -Force      # <-- línea 179: sin backup
```

Es la única escritura destructiva del script (la copia de la línea 123 es
para ficheros que no existen, y `Write-Utf8SinBom` solo escribe `.gitignore` y
`ARNES_VERSION.md`). `$respuesta` vale `'s'` por cuatro caminos distintos:
`-Forzar` (línea 147), `$aplicarATodos -eq 'si'` (línea 148, puesto por la
tecla `T` en la línea 167), y la tecla `S` (línea 165). El caso del 2026-08-19
fue el de la tecla `T`.

**Guardarraíl existente** (líneas 151-160): sin consola interactiva,
`Read-Host` devuelve vacío; tras 5 intentos conserva. O sea, hoy **una
respuesta vacía suelta vuelve a preguntar**; solo la quinta conserva. R14 lo
cambia: el Intro conserva a la primera.

---

## 2. Las tres categorías, y el criterio que las separa

El criterio discriminante entre (b) y (c) no es «tiene marcas `[ADAPTAR]`»
—`features.json` y `ARCHITECTURE.md` las tienen y son estado— sino este:

> **Un fichero es (c) estado del proyecto cuando su versión en el payload es
> una plantilla semilla y no una versión mejorable: aceptarla no aporta nunca
> nada y destruye siempre trabajo acumulado.**

Es un criterio objetivo (se decide mirando el payload, no la opinión de nadie)
y es el que uso para justificar dónde me aparto de la lista de partida de
`harness/features.json` (ver §9, D1 y D2).

### Clasificación completa del payload (33 ficheros versionados)

| Ruta relativa | Cat. | Por qué |
|---|---|---|
| `.claude/agents/implementer.md` | a | Protocolo genérico del arnés. |
| `.claude/agents/leader.md` | a | Ídem. |
| `.claude/agents/reviewer.md` | a | Ídem. Es donde entran las mejoras 1.5.2. |
| `.claude/agents/spec-author.md` | a | Ídem. |
| `specs/SPECS.md` | a | Formato de specs, genérico. |
| `scripts/despierto_hook.sh` | a | Script genérico. |
| `scripts/mantener_despierto.ps1` | a | Ídem. |
| `harness/__init__.py` | a | Código del arnés. |
| `harness/alcance.py` | a | Ídem. |
| `harness/backlog.py` | a | Ídem (genera `BACKLOG.md`). |
| `harness/cobertura.py` | a | Ídem. |
| `harness/mutacion.py` | a | Ídem (es lo que cambia F-034). |
| `harness/mutacion_paralela.py` | a | Ídem. |
| `harness/rigor.py` | a | Ídem. |
| `harness/rutas_sensibles.py` | a | Ídem. |
| `harness/servicios.py` | a | Ídem. |
| `harness/rigor.json` | a | Umbrales del arnés. Un proyecto que los afine pierde ese ajuste al actualizar: riesgo aceptado, cubierto por backup y resumen (ver §9, R-3). |
| `harness/rutas_sensibles.ejemplo.json` | a | Es el **ejemplo**; el fichero real del proyecto es `rutas_sensibles.json`, que va a (c). |
| `harness/servicios.ejemplo.json` | a | Ídem con `servicios.json`. |
| `harness/VERSION` | a | Lo escribe el arnés y **debe** actualizarse: si no, la versión instalada miente. |
| `tests/test_backlog_md.py` | a | Tests del propio arnés. |
| `tests/test_mutacion_informe.py` | a | Ídem. |
| `CLAUDE.md` | b | Genérico + mapa del repositorio y prohibiciones propias (218 líneas en `albaranes` frente a 197 del payload). |
| `CHECKPOINTS.md` | b | Genérico salvo el punto `[ADAPTAR]` de C3 (194 vs 183). |
| `harness/init.sh` | b | **El híbrido puro**: cuerpo genérico + cabecera de configuración (`PROYECTO_PYTHON`, `COMANDO_TESTS`, `RUTAS_PYTHON`) y sección 9 propias (498 vs 505). |
| `docs/CONVENTIONS.md` | b | El payload trae 65 líneas de convenciones **reales y mejorables**; el proyecto poda las de los lenguajes que no usa (70 en `albaranes`). |
| `docs/referencia/README.md` | b | Doctrina genérica sobre incorporar documentos + índice propio (100 vs 91). |
| `.claude/settings.json` | b | Configuración funcional que el arnés sí evoluciona (los hooks `SessionStart`/`SessionEnd` llegaron en 1.1.0) y que el proyecto adapta (en `albaranes`, el `PostToolUse` acota pytest a `tests/`). |
| `harness/features.json` | **c** | El payload es el ejemplo `F-001` de calentamiento. Aceptarlo **nunca** aporta nada. Es el fichero que perdió 34 features → 1. |
| `docs/ARCHITECTURE.md` | **c** | El payload son 37 líneas de esqueleto `[ADAPTAR]` sin una sola frase reutilizable. 183 → 37 el 2026-08-19. |
| `progress/current.md` | **c** | El payload dice literalmente «(vacío — ninguna feature en ejecución)», 4 líneas. Memoria entre sesiones. |
| `progress/history.md` | **c** | El payload son 6 líneas de cabecera. Registro append-only del proyecto. |
| `harness/gitignore.arnes` | excl. | Ya excluido hoy: es material del instalador, se anexa al `.gitignore`. |

### Entradas preventivas de `estado_del_proyecto` (no están hoy en el payload)

`progress/**` (cubre los informes `impl_*.md`, `review_*.md`, `mutacion_*.md`),
`docs/referencia/**` (los documentos convertidos de PDF), `specs/**` (con la
excepción exacta `specs/SPECS.md`), `BACKLOG.md` (**generado** por
`harness/backlog.py` desde `features.json`: pisarlo con una plantilla sería
además incoherente con su fuente), `harness/servicios.json`,
`harness/rutas_sensibles.json`, `.claude/settings.local.json`, `.env`.

Que hoy ninguna de esas rutas esté en el payload es exactamente el motivo de
declararlas: el día que alguien añada `progress/plantilla.md` al payload, la
protección ya está puesta y no hay que acordarse de nada (R5).

---

## 3. Dónde vive la lista, y por qué ahí

**Decisión: fichero de datos JSON en la raíz de `arnes-base`, fuera del
payload** — `arnes-base/politica_ficheros.json`.

Alternativas evaluadas:

| Opción | Por qué no |
|---|---|
| **Array en `instalar_arnes.ps1`** | Funciona, pero mezcla política y mecanismo en un `.ps1` que casi nadie lee. La política es la parte que el humano debe poder auditar y discutir sin leer PowerShell, y es la que se toca cada vez que se añade un fichero al payload. Se descarta por legibilidad, no por capacidad. |
| **Marcas dentro de cada fichero** (`<!-- ARNES: estado -->`) | Falla estructuralmente. Si la marca se lee **del destino**, un proyecto instalado con una versión antigua no la tiene y queda desprotegido — justo el repositorio más atrasado, que es el que más riesgo corre, exactamente el caso del 2026-08-19. Si se lee **del payload**, funciona pero obliga a ensuciar cada fichero (incluido JSON sin comentarios) con metadatos que viajan al destino, y no sabe expresar carpetas (`progress/**`) ni rutas que no están en el payload (R5). Se descarta. |
| **Fichero de datos dentro del payload** (`arnes-base/harness/politica.json`) | Se instalaría en cada proyecto (ruido), o habría que excluirlo como `gitignore.arnes`. Peor: una copia en el destino invita a que un proyecto edite su propia protección, y la protección debe ser del instalador, no negociable por el instalado. Se descarta. |

La opción elegida además habilita la comprobación de integridad de R4 —«todo
fichero del payload está clasificado, y si no, el instalador para»—, que es lo
que convierte la política en una obligación mantenida en vez de una lista que
se queda vieja en silencio.

### Formato

```json
{
  "$doc": "Clasificación de los ficheros del payload. La usa instalar_arnes.ps1 en modo actualizar. NO se copia al proyecto destino.",
  "$reglas": "Rutas relativas al payload con / como separador. Sufijo /** = prefijo de carpeta. Gana la entrada más específica: exacta > prefijo más largo. Todo fichero del payload debe casar con alguna entrada o el instalador aborta.",
  "version_politica": 1,
  "excluidos":            ["harness/gitignore.arnes", "**/__pycache__/**", "**/*.pyc", "**/*.pyo", "**/.pytest_cache/**"],
  "estado_del_proyecto":  ["harness/features.json", "docs/ARCHITECTURE.md", "progress/**", "docs/referencia/**", "specs/**", "BACKLOG.md", "harness/servicios.json", "harness/rutas_sensibles.json", ".claude/settings.local.json", ".env"],
  "adaptado":             ["CLAUDE.md", "CHECKPOINTS.md", "harness/init.sh", "docs/CONVENTIONS.md", "docs/referencia/README.md", ".claude/settings.json"],
  "arnes_puro":           ["specs/SPECS.md", ".claude/agents/**", "scripts/**", "tests/**", "harness/**"]
}
```

Nótese cómo la regla de especificidad (R3) hace el trabajo fino sin listas
enormes: `harness/**` es puro, pero `harness/features.json` (exacta) es estado;
`specs/**` es estado, pero `specs/SPECS.md` (exacta) es puro;
`docs/referencia/**` es estado, pero `docs/referencia/README.md` (exacta) es
adaptado.

---

## 4. Backup

**Ruta**: `%LOCALAPPDATA%\arnes-base\backups\<nombre-del-destino>\<yyyyMMdd-HHmmss>\`,
sobreescribible con `-DirBackup`.

Por qué `LOCALAPPDATA` y no otras:

- **Dentro del destino** (`.arnes_backup/`): descartado. Lo que se está
  protegiendo es el árbol del destino; escribir ahí ensucia su `git status` y
  puede acabar en un `git add -A`, que es precisamente el escenario que la
  feature teme.
- **Hermano del destino** (`..\albaranes-backup-...`): descartado; el padre de
  un repositorio puede ser a su vez un repositorio o una carpeta sincronizada.
- **`%TEMP%`**: descartado; Windows y las herramientas de limpieza lo vacían, y
  un backup que puede desaparecer solo no es un backup. (El del 2026-08-19
  sobrevivió por casualidad en el scratchpad de la sesión.)

**Contenido**: copia de la versión **previa del destino** de cada fichero que
se vaya a sobrescribir, conservando la ruta relativa, más `MANIFIESTO.md`
(R21).

**Momento**: el directorio se crea **una vez, antes del recorrido**; si no se
puede crear, el instalador aborta sin tocar nada (R18). Cada fichero se copia
**justo antes** de su `Copy-Item -Force`, no en bloque al principio: así el
backup contiene exactamente lo que se pisó y nada más.

**Si falla la copia de un fichero suelto** (R20): ese fichero **no** se
sobrescribe, se cuenta aparte como `no aplicado (fallo de backup)`, el
recorrido sigue y el script termina con código ≠ 0. Abortarlo todo a mitad
dejaría el destino en un estado mezclado, que es peor.

**No hay `-SinBackup`.** Un backup local de unos pocos KB no tiene coste que
justifique una vía de escape, y toda vía de escape acaba pulsándose.

---

## 5. Cambios en `instalar_arnes.ps1` (ficheros a crear y modificar)

### Ficheros a crear

| Ruta (en `arnes-base`) | Qué es |
|---|---|
| `politica_ficheros.json` | La política de §3. UTF-8 **sin BOM** (lo lee `Get-Content`/`ConvertFrom-Json`, y el `.gitattributes` lo fija a LF por `*.json`). |
| `tests_instalador/prueba_instalador.ps1` | La prueba de §7. UTF-8 **con BOM y CRLF** por `docs/CONVENTIONS.md` §PowerShell + `.gitattributes` (`*.ps1 text eol=crlf`). |
| `tests_instalador/README.md` | Cuatro líneas: cómo se lanza y qué demuestra. |

> Nombre `tests_instalador/` a propósito: `pruebas/` está en el `.gitignore` de
> `arnes-base` («Pruebas del instalador: nunca deben entrar al repositorio»), y
> esta prueba **sí** tiene que versionarse.

### Ficheros a modificar

**`arnes-base/instalar_arnes.ps1`** — funciones nuevas y puntos de injerto:

| Función / bloque | Responsabilidad | Dónde |
|---|---|---|
| `param(...)` | Añadir `[string]$DirBackup`, `[switch]$IgnorarPrecondiciones`, `[switch]$PreguntarTodo`. | líneas 21-26 |
| `Get-Politica([string]$ruta)` | Lee y valida `politica_ficheros.json`. Si falta o no parsea → `Write-Error` y salida ≠ 0 (sin política no se corre: el fallo abierto sería volver al comportamiento peligroso). | tras la línea 42 |
| `Get-CategoriaFichero([object]$politica, [string]$rel)` | Devuelve `excluido` / `estado` / `adaptado` / `puro` / `$null`, aplicando la especificidad de R3. Función **pura**: es la que la prueba puede ejercitar sin tocar disco. | ídem |
| `Test-PayloadClasificado` | Recorre el payload y aborta si alguna ruta devuelve `$null` (R4). Se ejecuta **antes** de cualquier escritura. | antes de la línea 112 |
| `Test-MismoContenido` | **Modificar**: para extensiones de texto (`.md .py .json .sh .ps1 .txt .arnes` y `VERSION`), comparar tras normalizar CRLF→LF y quitar BOM; para el resto, SHA-256 como hoy. Devuelve `igual` / `solo-eol` / `distinto`. | líneas 102-106 |
| `Test-Precondiciones($destino, $rutasATocar)` | R25/R27/R28. Usa `git -C $destino status --porcelain -- <rutas>` y `git rev-list --count HEAD..dev`. | tras el bloque de versión |
| `New-DirectorioBackup` / `Backup-Fichero` / `Write-Manifiesto` | R17-R22. | nuevo bloque antes del recorrido |
| Recorrido del payload | Reordenar: obtener categoría → si `excluido`, `continue`; si no existe en destino, copiar (R16); si `igual`/`solo-eol`, contar y `continue`; si `estado`, contar `protegido` y `continue` (**antes** de `Show-Diff`); si `puro` y no `-PreguntarTodo`, backup + copiar; si `adaptado` (o `-PreguntarTodo`), diff + preguntar con default CONSERVAR. | líneas 113-186 |
| Diálogo | Prompt nuevo: `[N] conservar (por defecto, Intro)`. Intro ⇒ `'n'` a la primera (R14). `T` y `C` siguen existiendo, pero `T` ya solo alcanza a (b), porque (a) no pregunta y (c) no se ofrece. | líneas 146-185 |
| `Copy-Item ... -Force` | Precedido **siempre** por `Backup-Fichero`. | línea 179 |
| Texto de `ARNES_VERSION.md` | R38. | líneas 232-255 |
| Resumen | R29/R30/R22: contadores nuevos `protegidos`, `solo finales de línea`, `no aplicados (fallo de backup)`, y la ruta del backup. | líneas 260-269 |

**`arnes-base/GUIA_INSTALACION.md`** — sección nueva «Qué no puede pisar el
instalador (X.Y.0)» con las tres categorías, la política, el backup y las
precondiciones (R35); y corrección del párrafo «Qué conservar casi siempre» de
la sección C (líneas 101-109), que hoy manda al humano vigilar a mano justo lo
que a partir de ahora protege el código (R36).

**`arnes-base/arnes-base/harness/VERSION`** — `ARNES_VERSION` y `ARNES_FECHA`
(R37, §8).

### Ficheros que NO se tocan (los colindantes que tientan)

- **Nada de `albaranes` fuera de `specs/F-035-*/` y `progress/`.** En
  particular, **no** se re-ejecuta el instalador contra `albaranes` como parte
  de esta feature: eso es un paso posterior que decide el humano.
- `arnes-base/arnes-base/**` salvo `harness/VERSION`: el payload no cambia de
  contenido. Esta feature no mejora el arnés instalado, mejora quien lo
  instala.
- `arnes-base/.gitattributes`, `arnes-base/.gitignore`, `README.md`: no hacen
  falta cambios (los patrones `*.json` y `*.ps1` ya cubren los ficheros
  nuevos).
- El **modo `instalar`**: fuera de alcance por declaración de la feature. La
  política se calcula igual en ambos modos (para la comprobación de R4 y las
  exclusiones de R24), pero la rama de la línea 136 no cambia.
- `harness/mutacion.py` y `CHECKPOINTS.md`: son el alcance de **F-034**. Si
  F-034 se cierra antes, el implementer de F-035 se limita a rebasar sobre su
  `arnes-base` ya actualizado.

---

## 6. Precondiciones: el criterio y su contra, escritos

El punto (4) de la feature pregunta si `actualizar` debe negarse a correr con
el árbol sucio o fuera de la rama de integración. **Sopesado, la respuesta es
media**, y la parto en dos porque las dos mitades tienen coste muy distinto:

**Árbol sucio → bloquea, pero solo en las rutas que se van a tocar (R25).**

- A favor: el 2026-08-19 el daño fue reversible **únicamente** porque git tenía
  el estado anterior. Un fichero de estado modificado y sin commitear es el
  único caso en que el instalador puede destruir algo irrecuperable desde git.
- El contra real: exigir el árbol **entero** limpio deja fuera el caso normal
  —un repositorio con trabajo en curso, que es cuando uno actualiza el arnés—.
  Un guardarraíl que salta siempre se desactiva siempre: acabaríamos escribiendo
  `-IgnorarPrecondiciones` de memoria en cada invocación y volveríamos al punto
  de partida, pero con la falsa sensación de estar protegidos.
- El criterio afinado tiene las dos propiedades buenas: en `albaranes` con
  `services/**` a medias **no** salta; con `harness/features.json` modificado y
  sin commitear **sí**. Y es barato: `git status --porcelain -- <rutas>` con la
  lista exacta de rutas que el recorrido va a tocar en esa pasada.
- Vía de escape: `-IgnorarPrecondiciones`, **no `-Forzar`** (D3 en §9).

**Rama → avisa, no bloquea (R27).**

- El instalador no sabe cuál es la rama de integración de cada proyecto
  (`dev` aquí, `main` en otros, `master` o `trunk` en otros). Cualquier regla
  por nombre produce falsos bloqueos en repositorios ajenos, y el instalador es
  genérico por definición.
- Lo que sí puede hacer, y es lo que faltó ese día, es **dar el dato**: rama
  actual y, si existe `dev`, `git rev-list --count HEAD..dev`. «Estás en
  `feature/F-019-...`, 25 commits por detrás de `dev`» habría parado la mano
  sin necesidad de prohibir nada.

---

## 7. Verificación

### 7.1 Lo que hay hoy en `arnes-base` (y lo que no)

- **No hay ninguna prueba del instalador.** La carpeta `tests/` que aparece en
  el repositorio está **dentro del payload**
  (`arnes-base/arnes-base/tests/test_backlog_md.py`,
  `test_mutacion_informe.py`): son tests de `harness/backlog.py` y
  `harness/mutacion.py` que se **instalan en el proyecto destino**. No prueban
  `instalar_arnes.ps1` ni se ejecutan contra él.
- **No hay CI** en `arnes-base` (ni `.github/`, ni equivalente).
- **Pester**: comprobado en esta máquina, `Get-Module -ListAvailable Pester`
  devuelve **3.4.0** (el que trae Windows), con PowerShell 5.1.26100.9168.
  Pester 3.4 sirve, pero su sintaxis es **incompatible** con la 5.x: el día que
  alguien instale Pester 5 en cualquier máquina, la suite deja de ejecutarse.
  Un arnés que se instala en máquinas distintas no puede depender de eso.

**Decisión: PowerShell puro, sin framework.** `tests_instalador/prueba_instalador.ps1`
con un `Assert-Igual` propio de cinco líneas, un contador y `exit 1` si algo
falla. Cero dependencias (R34), corre en cualquier Windows con PS 5.1, y no se
rompe al actualizar módulos. Es la alternativa más barata que sigue siendo
verificable, tal como pide el enunciado.

### 7.2 La prueba de fuego

Un solo script, con `try/finally` para limpiar. Cada caso monta un repositorio
de mentira desechable en `$env:TEMP\arnes_prueba_<guid>`:

```
1. New-Item; git init; git config user.email/user.name  (local al repo)
2. instalar_arnes.ps1 -Destino <falso> -Modo instalar
3. Sembrar ESTADO:
   - harness/features.json  con N = 7 features
   - docs/ARCHITECTURE.md   con 200 líneas
   - progress/current.md    con un marcador reconocible
   - progress/history.md    ídem
4. Ensuciar ARNÉS PURO: .claude/agents/leader.md  <- "MODIFICADO POR EL PROYECTO"
5. Ensuciar ADAPTADO:  CLAUDE.md                  <- marcador propio
6. git add -A; git commit  (árbol limpio: no debe bloquear)
7. instalar_arnes.ps1 -Destino <falso> -Modo actualizar -Forzar
8. ASERTAR
```

| Caso | Qué asegura | Requisito |
|---|---|---|
| **P1 — la prueba de fuego** | `features.json` sigue teniendo **7** features tras `-Forzar`. | R9, R10, R39 |
| P2 | `docs/ARCHITECTURE.md` sigue con 200 líneas; `progress/current.md` e `history.md` conservan su marcador. | R9, R40(i) |
| P3 | `.claude/agents/leader.md` **sí** quedó idéntico al payload (la actualización funciona; la protección no es una parálisis). | R11, R40(ii) |
| P4 | Sin `-Forzar` y con la entrada redirigida a vacío, `CLAUDE.md` conserva su marcador y el resumen dice `conservado`. | R13, R14, R15, R40(iii) |
| P5 | Existe el directorio de backup con sello; contiene la copia **previa** de `.claude/agents/leader.md`; el `MANIFIESTO.md` lo lista y trae rama y commit. | R17, R19, R21, R40(iv) |
| P6 | El resumen imprime `Protegidos: 4` y lista las cuatro rutas. | R29, R30 |
| P7 | Con `harness/features.json` modificado y sin commitear, el instalador sale ≠ 0 y `features.json` no cambia; con `-IgnorarPrecondiciones` sí corre. | R25, R26, R40(v) |
| P8 | Con `services/algo.txt` modificado y sin commitear (ruta que el instalador no toca), **no** bloquea. | R25, R40(vi) |
| P9 | Modo `instalar` sobre el mismo repo sembrado: `features.json` sigue con 7 y `CLAUDE.md` con su marcador. | R32, R40(vii) |
| P10 | Añadida una ruta inventada al payload de una copia temporal y sin entrada en la política, el instalador aborta ≠ 0 y no escribe. | R4, R40(viii) |
| P11 | Un fichero de categoría (a) idéntico salvo CRLF en el destino no se cuenta como distinto ni se toca (`mtime` sin cambiar). | R23 |
| P12 | Tras instalar, el destino no contiene `__pycache__`, `*.pyc` ni `.pytest_cache`. | R24 |

**Fase RED (exigida por rigor `estandar`)**: P1, P2, P6, P7, P11 y P12 deben
**fallar** contra `instalar_arnes.ps1` tal como está hoy (1.5.2), antes de
tocar el script. P1 fallando es la reproducción exacta del incidente en un
banco de pruebas. Esa ejecución en rojo se pega en `progress/impl_F-035.md`.

### 7.3 Sustituto de la campaña de mutación

`harness/mutacion.py` solo muta Python y solo mide el diff de **este**
repositorio: contra F-035 dará 0 mutantes por falta de sujeto, no por calidad.
La evidencia equivalente es una **campaña manual** sobre
`instalar_arnes.ps1` y `politica_ficheros.json`, con el texto exacto
original → mutado de cada sustitución (formato que F-034 propone volver
obligatorio en `CHECKPOINTS.md`). Mínimo propuesto, 6 mutantes, todos con
mutante aplicado a mano, prueba ejecutada, y revertido:

| # | Original → mutado | Debe morir en |
|---|---|---|
| M1 | Quitar `"harness/features.json"` de `estado_del_proyecto` | P1 |
| M2 | Quitar `"progress/**"` de `estado_del_proyecto` | P2 |
| M3 | En la resolución de categoría, cambiar la precedencia exacta>prefijo por el orden inverso | P1 y P9 |
| M4 | Cambiar el default del diálogo de `'n'` a `'s'` | P4 |
| M5 | Eliminar la llamada a `Backup-Fichero` previa al `Copy-Item -Force` | P5 |
| M6 | En la precondición, cambiar `status --porcelain -- <rutas>` por `status --porcelain` (repo entero) | P8 |

Si algún mutante **sobrevive**, es un hueco real de la prueba y se cierra
antes de dar la feature por hecha.

### 7.4 Verificación MANUAL del humano (fuera de la prueba automática)

`Verificación: MANUAL (humano)` — con `arnes-base` ya actualizado, ejecutar
contra este repositorio, en una rama limpia creada desde `dev`:

```powershell
cd C:\Users\pgris\PycharmProjects\arnes-base
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\albaranes" -Modo actualizar -SoloDiff
```

Y comprobar a ojo que en el listado aparecen como `protegidos`
`harness/features.json`, `docs/ARCHITECTURE.md`, `progress/current.md` y
`progress/history.md`, y que el número de ficheros «distintos» baja de 13 a 5
al desaparecer el ruido CRLF. `-SoloDiff` no escribe nada (R31), así que esta
comprobación es segura.

---

## 8. Qué versión de `arnes-base` sale

`harness/features.json` propone 1.5.3. **Propongo MINOR, no PATCH**, y por
tanto **1.7.0** — con la regla de desempate que sigue.

Razones para no ser PATCH:

1. Se añaden **tres parámetros** a la interfaz pública del instalador
   (`-DirBackup`, `-IgnorarPrecondiciones`, `-PreguntarTodo`).
2. Cambia el **comportamiento por defecto** del modo `actualizar`: los (a) se
   aplican sin preguntar y los (c) dejan de ofrecerse. Quien invoque el
   instalador igual que ayer obtiene un resultado distinto (mejor, pero
   distinto).
3. Aparece un **artefacto nuevo versionado** del que el script depende para
   arrancar (`politica_ficheros.json`).
4. Toda la serie 1.x del arnés ha usado el MINOR para «capacidad nueva»
   (1.3.0 monorepo, 1.4.0 rutas sensibles, 1.5.0 BACKLOG) y el PATCH para
   correcciones sin interfaz nueva (1.3.1, 1.5.1, 1.5.2). Esto es capacidad
   nueva.

Regla de desempate con **F-034**, que declara subir a 1.6.0 y tiene prioridad 1:

- Si F-034 cierra antes → F-035 sale como **1.7.0**.
- Si F-035 cerrara antes que F-034 → sale como **1.6.0**, y F-034 pasaría a
  1.7.0.
- Si el humano decide agruparlas en una sola versión → ambas en **1.6.0**.

Operativamente: el implementer **lee
`arnes-base/arnes-base/harness/VERSION` en el momento de implementar** y sube
el MINOR siguiente al que encuentre. No cablear el número desde esta spec.

Y, en `albaranes`, el consumo del resultado (volver a pasar el instalador para
llegar a esa versión) es un trabajo **posterior y del humano**, no parte de
F-035.

---

## 9. Riesgos y decisiones

### Decisiones abiertas (necesitan un sí o un no del humano)

**D1 · `.claude/settings.json`: propongo (b), no (c).**
`harness/features.json` lo lista entre los intocables. Me aparto aplicando el
criterio de §2: el payload trae una configuración **funcional y mejorable**
(los hooks `SessionStart`/`SessionEnd` entraron en 1.1.0 y llegaron a los
proyectos por esta vía), no una plantilla vacía. Con default en CONSERVAR y
backup previo, el riesgo de pisarlo es un Intro de distancia y recuperable; el
coste de hacerlo intocable es que ninguna mejora de hooks vuelva a llegar a
ningún proyecto. **Si el humano prefiere (c), es un cambio de una línea en
`politica_ficheros.json`.**

**D2 · `docs/CONVENTIONS.md`: propongo (b), no (c).**
Mismo razonamiento: el payload trae 65 líneas de convenciones reales que el
arnés sí mejora; el proyecto poda las de los lenguajes que no usa. En
`albaranes` la diferencia es de 5 líneas, no de 150 como en `ARCHITECTURE.md`.
Misma vía de cambio si el humano discrepa.

**D3 · Vía de escape separada de `-Forzar`.**
Propongo `-IgnorarPrecondiciones` en vez de reutilizar `-Forzar`, porque son
dos cosas distintas: `-Forzar` significa «no me preguntes» y el incidente
ocurrió **sin** `-Forzar`. Quien no quiere preguntas no necesariamente quiere
saltarse la red de seguridad, y `-Forzar -IgnorarPrecondiciones` juntos son una
declaración de intenciones inequívoca.

**D4 · Normalización de finales de línea (R23) — ¿entra o no?**
Es lo único de esta spec que no se deduce literalmente del enunciado de la
feature. Entra porque es causa contribuyente medida (8 diffs vacíos de 13) y
porque cuesta una función. **Si el humano lo quiere fuera**, se saca sin tocar
el resto del diseño; el precio es que el instalador siga presentando ruido y
siga empujando a la tecla `T`.

**D5 · Rigor declarado.**
F-035 está declarada `rigor: estandar` en `harness/features.json`, pero en
`albaranes` no hay código: las puertas de cobertura y mutación no tienen
sujeto (§0). Propongo **mantener `estandar`** y aceptar como evidencia
equivalente la fase RED de §7.2 y la campaña manual de §7.3, dejándolo escrito
en `progress/impl_F-035.md` para que el reviewer no lo lea como puerta saltada.
La alternativa —bajarla a `documental`— sería mentir: aquí hay código, solo que
en otro repositorio.

### Riesgos

- **R-1 · Un proyecto que sí había personalizado un fichero (a).** Con R11 se
  le pisa sin preguntar. Mitigado por el backup (R19), por el resumen que lo
  nombra (R29) y por `-PreguntarTodo` (R12). Aceptado: es el precio de que
  actualizar el arnés deje de ser un interrogatorio de 13 preguntas del que se
  sale pulsando `T`.
- **R-2 · La política se queda vieja.** Alguien añade un fichero al payload y
  no lo clasifica. Mitigado por diseño: R4 hace **abortar** el instalador y P10
  lo prueba. Es un fallo cerrado y ruidoso, no silencioso.
- **R-3 · `harness/rigor.json` clasificado como (a).** Un proyecto que hubiera
  bajado su umbral de cobertura lo pierde al actualizar. Riesgo aceptado y
  escrito: son umbrales del arnés y el arnés es quien debe fijarlos; el backup
  cubre el descuido.
- **R-4 · La prueba no corre en Linux/macOS.** Es PowerShell 5.1 sobre Windows,
  como el instalador. Sin CI, se ejecuta a mano. Se asume: el instalador solo
  se usa desde Windows en este ecosistema.
- **R-5 · Doble repositorio, un solo trabajo.** El riesgo de proceso más real:
  cerrar F-035 en `albaranes` con el código a medias en `arnes-base`, o
  commitear en `arnes-base` cambios de otra sesión. El implementer debe dejar
  en `progress/impl_F-035.md` los **hashes de los commits de `arnes-base`**, y
  el reviewer verificarlos ahí (`git -C ...\arnes-base log`). Sin `push` en
  ninguno de los dos repositorios salvo petición explícita.
- **R-6 · Colisión con F-034.** Ambas tocan `arnes-base` y ambas suben versión.
  Mitigado por la regla de desempate de §8 y por no cablear el número.
