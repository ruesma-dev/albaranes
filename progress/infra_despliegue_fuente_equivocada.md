<!-- progress/infra_despliegue_fuente_equivocada.md -->
# El despliegue construía desde las carpetas equivocadas (14-sep-2026)

> Rama `chore/infra-build-desde-el-monorepo`, a partir de `main` (5467f23).
> Solo se ha tocado `infra/`. Ni un `git push`, ni un despliegue, ni una sola
> llamada real a `az`.

Tres fallos encadenados en `infra/` hacían que el despliegue terminara «en
verde» sin llevar a producción **nada de lo desarrollado desde julio**. Se
descubrió hoy al intentar desplegar F-043.

---

## Fallo 1 · El build leía de los repositorios ARCHIVADOS

`infra/build_images.ps1` tenía la raíz escrita a mano:

```powershell
[string] $ProjectsRoot = "C:\Users\pgris\PycharmProjects",
...
$svcDir = Join-Path $ProjectsRoot $services[$img]   # -> ...\PycharmProjects\albaranes-api
```

Es decir: cada servicio se cogía de la **carpeta hermana** previa a la
migración al monorepo, no de `albaranes/services/<mismo nombre>`.

Evidencia (último commit de cada carpeta hermana):

| Carpeta hermana | Último commit |
|---|---|
| `albaranes-api` (sv2) | `a8729aa` 2026-08-12 «ARCHIVADO: migrado al monorepo albaranes; no trabajar aqui» |
| `albaranes-front` (sv4) | `562057f` 2026-08-12 «ARCHIVADO: …» |
| `albaran-valoracion-api` (sv5) | `c3c8191` 2026-08-12 «ARCHIVADO: …» |
| `albaran-valoracion-persist` (sv6) | `78f96fc` 2026-08-12 «ARCHIVADO: …» |
| `albaranes-email` (sv1) | `6dc240a` **2026-07-13** «seleccion contrato auto» (ni siquiera marcada) |
| `albaranes-comun` | **no es un repositorio git** |

Comprobación objetiva del desfase, con el catálogo de familias de F-043:

```
services/albaranes-comun/ruesma_comun/contratos/familias.py   -> existe (16 350 bytes)
../albaranes-comun/ruesma_comun/contratos/familias.py         -> No such file or directory
```

Lo mismo con código de producción de F-036 en sv6:
`application/services/residuos_incrementos.py` existe en el monorepo y **no**
en `..\albaran-valoracion-persist`.

## Fallo 2 · `-Only` no llegaba al build

`deploy.ps1` validaba `-Only`, lo usaba para filtrar el `az containerapp
update`… y llamaba al build sin filtro:

```powershell
& (Join-Path $PSScriptRoot "build_images.ps1")     # sin -Only
```

`.\deploy.ps1 -Only sv3` construía **los seis** servicios (desde las carpetas
equivocadas, además) y solo después actualizaba sv3.

## Fallo 3 · La suscripción no se cargaba

`infra/00_vars.ps1:9` fijaba `$Global:SUBSCRIPTION =
"REDACTADO-VER-COPIA-LOCAL"` y **nunca** cargaba `infra/00_vars.local.ps1`,
que existe (no versionado, `.gitignore: infra/*.local.ps1`) y trae el valor
real. Resultado: `az account set --subscription REDACTADO-...` fallaba con

```
The subscription of 'redactado-ver-copia-local' doesn't exist in cloud 'AzureCloud'.
```

y el build continuaba **por casualidad**, contra la suscripción activa de la
consola, fuera cual fuera.

---

## Qué se ha cambiado

### `infra/build_images.ps1` (+129 / −11)

1. **Raíz derivada del propio script**: `$RepoRoot = Split-Path -Parent
   $PSScriptRoot`, `$ServicesRoot = $RepoRoot\services`. `-ProjectsRoot` sigue
   admitiéndose explícito; por defecto vale `$ServicesRoot`. `$ComunPath`
   deriva de `$ProjectsRoot` (por defecto `…\services\albaranes-comun`).
   **El mapa `sv1..sv6 -> nombre de carpeta` no se ha tocado.**
2. **Guarda de fuente** (`Assert-FuenteDelMonorepo`): criterio objetivo y
   barato — toda carpeta fuente (los seis servicios **y** `comun`) debe estar
   bajo el `services\` del repositorio donde vive el script. Si no, el build
   **para en seco** con un mensaje que dice la ruta, la raíz esperada y el
   porqué. Escape explícito y ruidoso: `-PermitirFuenteExterna`.
3. **`-Only sv1..sv6`**, mismo formato que `deploy.ps1`. Un servicio
   desconocido es error, no aviso. Imprime raíz, `comun`, los que construye y
   los que omite.
4. **Guarda de suscripción** antes de `az account set`: si sigue redactada,
   error claro en vez del mensaje críptico de `az`.
5. Un manifest o una carpeta fuente ausentes pasan de `Write-Warning` +
   `continue` a `throw`. Antes, un servicio pedido podía saltarse en silencio
   y el despliegue seguía con la imagen vieja.

### `infra/deploy.ps1` (+10 / −1)

`& build_images.ps1 -Only $svcs`. `$svcs` ya viene validado y, sin `-Only`,
contiene los seis. Nota del fallo en la cabecera del script.

### `infra/00_vars.ps1` (+41)

Carga `00_vars.local.ps1` **al final** (para que pise a los marcadores) con
guardia de reentrada — el `.local` es hoy una copia completa de este fichero,
así que si alguien lo refresca copiando el versionado encima, sin guardia el
dot-source se llamaría a sí mismo sin fin. Si tras cargarlo la suscripción
sigue redactada, bloque de aviso en rojo diciendo qué falta y que no se lance
build ni deploy. **`00_vars.local.ps1` no se ha tocado ni se ha copiado de él
ningún valor a un fichero versionado.**

### Documentación

`infra/README_capps.md`: sección «Lo que costó dos meses (14-sep-2026)» con
los tres fallos y la moraleja operativa. `infra/README.md`: nota sobre
`00_vars.local.ps1` en *Notas / gotchas*.

---

## Cómo se ha verificado, sin tocar Azure

Dos bancos de prueba en el scratchpad (no versionados) que ejecutan **los
scripts reales** con `az` sustituido por una función `az` global: en
PowerShell una función gana a un ejecutable, así que ninguna invocación sale
del proceso. Precedencia comprobada antes de nada (`(Get-Command az).CommandType
-> Function`). El stub corre con el CWD puesto en el contexto de build, o sea
que inspecciona **exactamente** lo que se le habría pasado a `az acr build`.

`prueba_build_images.ps1` — 20 comprobaciones, **todas verdes**:

| Caso | Resultado |
|---|---|
| `00_vars.ps1` resuelve `SUBSCRIPTION` y `TENANT` | ya no redactados (valores **no** impresos) |
| `-Only sv3` | 1 build, `sv3-persistencia:…`, fuente `…\albaranes\services\albaranes-persistencia` |
| contexto de sv3 y sv2 | contiene `comun\ruesma_comun\contratos\familias.py` (F-043, sep-2026) |
| contexto de sv6 | contiene `application\services\residuos_incrementos.py` (F-036, ago-2026) |
| `-Only sv2,sv6` | 2 builds, en el orden del mapa |
| `-Only svX` | `Servicio 'svX' desconocido. Validos: sv1…sv6`, 0 builds |
| `-ProjectsRoot ...\PycharmProjects` | guarda activa: `Fuente fuera del monorepo para sv6`, 0 builds |
| `-ComunPath ...\albaranes-comun` (el archivado) | guarda activa sobre `comun`, 0 builds |
| `-PermitirFuenteExterna` | deja construir (la puerta no queda cerrada) y **contraste**: ese contexto NO lleva `residuos_incrementos.py` — esto es lo que se venía subiendo |
| sin `-Only` | 6 builds, los seis desde `…\albaranes\services\`, los seis con el catálogo de F-043 |

`sandbox_deploy/runner.ps1` — el `deploy.ps1` **real** (copiado) con
`00_vars.ps1`, `build_images.ps1` y `check_deploy.ps1` falsos alrededor, para
ver qué recibe el build. 6 comprobaciones, **todas verdes**: `-Only sv3` →
build recibe `[sv3]` y se actualiza solo `ca-sv3`; `-Only sv2,sv6` → `[sv2,
sv6]`; sin `-Only` → los seis; `-SkipBuild` sigue saltándose el build.

`prueba_suscripcion.ps1` — 5 comprobaciones, **todas verdes**: copiando
`00_vars.ps1` a una carpeta sin `.local` al lado sale el aviso «SUSCRIPCION
SIN RESOLVER» + «NO lances build ni deploy»; y con `$SUBSCRIPTION` forzada al
marcador, `build_images.ps1` aborta con mensaje propio y **cero** llamadas a
`az`.

Además: `[Parser]::ParseFile` sin errores en los tres `.ps1`, y BOM UTF-8 +
CRLF preservados en todos (`docs/CONVENTIONS.md` §PowerShell).

`bash harness/init.sh`: **verde** (569 tests en 159 s, las 6 suites de
servicio en verde). La única línea `[KO]` fue «Estás en 'main'», que es lo que
motivó crear la rama `chore/`; desde la rama, en verde.

## Qué queda SIN verificar hasta que el humano despliegue

Nada de esto se puede probar sin Azure, y no se ha probado:

1. Que `az acr build` acepte el contexto y **el Dockerfile construya** con el
   código del monorepo. Los manifests no han cambiado, pero el contenido de
   las carpetas fuente sí: si algún `requirements.txt` o import se movió en la
   migración, saldrá aquí y no antes.
2. Que la imagen resultante **arranque** en Container Apps y que el pipeline
   funcione de punta a punta con el código nuevo.
3. Que `az account set` con la suscripción real ya cargada funcione (hasta hoy
   esa llamada fallaba **siempre**; nunca se ha ejecutado bien).
4. El tamaño del contexto: `comun` se copia con `Copy-Item -Recurse` sin
   excluir nada, así que entran `__pycache__`, `tests/` y `local/`. El
   `.dockerignore` filtra `**/__pycache__` y `**/*.pyc`, pero `tests/` no: son
   unos pocos KB y no rompe, aunque engorda la imagen.

Guion sugerido para el humano (uno solo, y comprobando después que la app
sirve código nuevo):

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
.\deploy.ps1 -Only sv6
```

## AVISO · la imagen subida hoy es basura

**`sv1:r20260914-2152`**, subida hoy al ACR `acralbaranesdev`, está construida
desde `C:\Users\pgris\PycharmProjects\albaranes-email` — la carpeta
**archivada**, cuyo último commit es del **13-jul-2026**. No contiene nada
posterior. **No la despliegues y bórrala** para que nadie la reutilice por
error:

```powershell
az acr repository delete --name acralbaranesdev --image sv1:r20260914-2152 --yes
```

Por la misma razón, **cualquier tag anterior del ACR es sospechoso**: todos se
construyeron con la raíz equivocada. La primera reconstrucción con estos
scripts es la primera imagen fiable desde la migración al monorepo.

## Hallazgos colaterales — anotados, NO arreglados

No se han tocado: quedan para que el humano decida.

1. **`infra/create_capps_sv4.ps1` tiene la misma enfermedad** (líneas 34-35):
   `$SV4_DIR = "…\PycharmProjects\albaranes-front"` y `$COMUN_DIR =
   "…\PycharmProjects\albaranes-comun"`, ambas archivadas. Además su
   `$MANIFEST = "$SV4_DIR\manifests\sv4"` apunta a una carpeta que no existe
   (los manifests viven en `infra\manifests\`). Es un script de creación
   inicial, no del ciclo de `deploy.ps1`, pero si alguien lo lanza repite el
   fallo. Su gemelo `create_capps_sv4.local.ps1` no está versionado y tiene
   las mismas dos rutas.
2. **`infra/docs/levantar-pipeline-local.md` (líneas 48 y 57)** manda hacer
   `pip install -e C:\Users\pgris\PycharmProjects\albaranes-comun`, o sea el
   `comun` **archivado**. Quien siga la guía monta un entorno local sin el
   catálogo de familias de F-043 ni nada posterior a julio. Es la misma clase
   de fallo, en el entorno local en vez de en el despliegue.
3. **`deploy.ps1` comprueba `$LASTEXITCODE` después de llamar a un `.ps1`**
   (`if ($LASTEXITCODE -ne 0) { throw "build_images.ps1 fallo" }`). Invocar un
   script con `&` no fija `$LASTEXITCODE`: lo que se lee ahí es el valor que
   dejara el último ejecutable nativo. Hoy no causa daño porque
   `build_images.ps1` aborta con `throw` y el error se propaga, pero esa línea
   no protege de nada.
4. **`00_vars.local.ps1` es una copia completa de `00_vars.ps1`**, no un
   parche de tres líneas. Cada cambio en el versionado hay que replicarlo a
   mano en el local o el local lo pisa al cargarse. Convertirlo en una
   superposición mínima (solo `SUBSCRIPTION`, `TENANT` y lo que de verdad sea
   secreto) es un arreglo de diez minutos que quita una trampa permanente; no
   se ha hecho porque el fichero no se versiona y es del humano.
5. **`services/albaranes-email` (sv1) no tiene directorio de tests** —
   `init.sh` lo avisa: «NADIE está comprobando los tests de sv1-email».
   Preexistente, ajeno a esta tarea.

## Estado del árbol

Limpio salvo **una modificación de `README.md` que no es mía** y ya estaba sin
commitear al empezar la sesión: cinco líneas añadidas al final con el comando
`powershell -ExecutionPolicy Bypass -File .\infra\local\arrancar_local.ps1`.
No la he tocado ni la he metido en el commit de `infra:` — es trabajo ajeno y
no verificado. Decide el humano si la commitea aparte o la descarta.
