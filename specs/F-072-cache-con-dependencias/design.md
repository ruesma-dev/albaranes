<!-- specs/F-072-cache-con-dependencias/design.md -->
# F-072 · Diseño: caché de suites con dependencias declaradas

## 1. Encaje, alcance y rigor

- **Qué se toca:** solo el arnés (`harness/`, `tests/` de la raíz). Ningún servicio
  cambia, no hay SQL ni colas y `azure-apps/` no cambia. Límite de servicio: no
  aplica; es infraestructura **genérica** del arnés y se porta a `arnes-base` (§7).
- **Rigor `critico`.** Es la «infraestructura compartida» de `rigor.json`: decide qué
  es verde en el portero de todos los repositorios con arnés, y su modo de fallo es
  un verde falso silencioso (uno de los casos del encargo 1.7.12 invalidó una
  campaña de mutación entera). El taller ya la clasificó `critico` (F-028). F-038 a
  F-040 fueron `estandar` porque tocaban cómo se mide, no el veredicto. El módulo es
  pequeño (~200 líneas): la campaña completa sale barata.

## 2. Ficheros a crear

| Ruta | Qué |
|---|---|
| `harness/cache_suites.py` | Cálculo de la clave, sonda, decisión y CLI (§4) |
| `tests/test_f072_r1_r6_esquema_servicios.py` | R1–R6 |
| `tests/test_f072_r7_r17_clave.py` | R7–R17 (repositorio git temporal y sonda falsa) |
| `tests/test_f072_r18_r22_decision_y_cli.py` | R18–R22 |
| `tests/test_f072_r23_r27_init_sh.py` | R23–R27: contrato estático del texto de `init.sh` §7 bis |
| `tests/test_f072_r28_r30_declaracion.py` | R28–R30 |
| `tests/test_f072_r31_r33_escenarios.py` | R31–R33, de punta a punta con git y sonda reales |

Sin red ni BBDD. `git` local en `tmp_path`, identidad por `-c user.name=… -c
user.email=…` y sin las variables `GIT_*` del entorno (desde un hook, `GIT_DIR`
haría operar al test sobre el repositorio real).

## 3. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `harness/servicios.py` | `Servicio` gana `depende_de`, `importa` y `entradas_no_versionadas` (tuplas, por defecto `()`), con su validación (R2–R5). `linea_shell` y `--shell` **no cambian** |
| `harness/init.sh` | Cabecera: `SIN_CACHE="${ARNES_SIN_CACHE:-0}"` junto a `SALTAR_SUITES`. §7 bis: la caché pasa por `harness.cache_suites` (§5) |
| `harness/servicios.json` | `depende_de` + `importa` en sv1, sv2, sv3, sv4, sv5, sv6 y sv9 (R28) |
| `harness/servicios.ejemplo.json` | `$doc` con los tres campos y un servicio de ejemplo que los usa (R29) |
| `harness/ARNES_VERSION.md` | Nota: lleva la caché con dependencias de la 1.7.16 sobre su 1.7.2, desarrollada aquí (R30) |

**No se tocan:** `harness/mutacion.py`, `mutacion_paralela.py`, `cobertura.py`,
`rutas_sensibles.py` y `alcance.py` (usan `cargar_servicios`; los campos nuevos
tienen defecto y no les afectan). Tampoco el formato de `--shell` (su único
consumidor es `init.sh`, y un campo más rompería el `read` de cinco campos),
`harness/VERSION`, `CHECKPOINTS.md`, `.claude/agents/*`, `.claude/settings.json`
(ver P3 en `progress/spec_F-072.md`), `services/**` y `docs/ARCHITECTURE.md`.

## 4. `harness/cache_suites.py` (herramienta del arnés, sin capas hexagonales)

```python
FORMATO_CLAVE = "cache-suites/2"        # marca de formato: entra en el texto de la clave
LIMITE_SONDA_S = 30
ENTRADAS_LOCALES_POR_DEFECTO = (".env",)  # en la raíz y bajo la ruta de cada servicio

@dataclass(frozen=True)
class Sondeo:
    origenes: dict[str, str | None]   # módulo -> ruta real (fichero o carpeta); None = no encontrado
    tiene_coverage: bool

@dataclass(frozen=True)
class Decision:
    servir: bool
    clave: str | None                 # None = no se guarda caché
    fecha_verde: str | None           # "AAAA-MM-DD HH:MM" solo si servir
    avisos: tuple[str, ...]

class ErrorDeSonda(Exception): ...

def hash_en_head(ruta: str, raiz: str) -> str | None        # git rev-parse HEAD:<ruta>; None si no existe
def hay_cambios(rutas: list[str], raiz: str) -> bool         # git status --porcelain -- <rutas...> no vacío
def raiz_del_repositorio(raiz: str) -> Path                  # git rev-parse --show-toplevel, resuelta
def huella_local(ruta: str, raiz: str) -> str                # "<ruta>@<tamaño>:<mtime_ns>" | "<ruta>@ausente"
def sondear(interprete: str, modulos: tuple[str, ...], cwd: Path,
            limite_s: int = LIMITE_SONDA_S) -> Sondeo        # lanza ErrorDeSonda
def texto_de_clave(servicio, raiz: str, interprete: str,
                   sondeo: Sondeo) -> tuple[str | None, list[str]]   # (texto canónico o None, avisos)
def clave_de(servicio, raiz, interprete, sondeo) -> tuple[str | None, list[str]]  # sha256 hex del texto
def decidir(servicio, raiz: str = ".", *, sin_cache: bool = False,
            sondear=sondear) -> Decision                     # `sondear` inyectable para los tests
def lineas_de_salida(decision: Decision) -> list[str]        # protocolo de R22
def main(argv: list[str] | None = None) -> int               # --servicio NOMBRE [--sin-cache] [--raiz .]
```

**Texto canónico** (una línea por dato, cada grupo ordenado; R7, R8):

```
formato=cache-suites/2
servicio=<ruta>@<hash HEAD>
depende=<ruta>@<hash HEAD>                 # una por dependencia
interprete=<ruta resuelta y normcase>
modulo=<nombre>@<origen resuelto y normcase>
local=<ruta>@<tamaño>:<mtime_ns> | <ruta>@ausente   # .env raíz, <ruta>/.env y declaradas, sin duplicados
```

La clave es el `sha256` hexadecimal (64 caracteres) de ese texto. Una caché del
formato anterior guarda un hash de árbol de 40, así que nunca coincide (R20): tras
actualizar, cada suite se ejecuta una vez y se reescribe.

**Reglas de `texto_de_clave`** (devuelve `None` y, en su caso, el aviso):
1. `hay_cambios([ruta] + depende_de)` → `None`, sin aviso (R11, igual que hoy).
2. `hash_en_head` de la ruta es `None` → `None`. Si lo es el de una dependencia →
   aviso «`<dep>` no está versionada en HEAD; si es un fichero local, declárala en
   `entradas_no_versionadas`» (R12).
3. Por cada módulo vigilado (R13–R15):
   - origen `None` → aviso «no se encuentra `<mod>` con el intérprete de `<svc>`»;
   - un origen que no es una ruta (`built-in`, `frozen`) o que cae fuera de
     `raiz_del_repositorio` → aviso «importa `<mod>` desde `<ruta real>`, fuera de
     este repositorio: su suite prueba ESA copia y no la de este árbol; no se
     cachea»;
   - dentro del repositorio pero fuera de `[ruta] + depende_de` → aviso «importa
     `<mod>` desde `<ruta relativa>`, que no está declarada: añádela a
     `depende_de`».
4. Las comparaciones de rutas usan `Path.resolve()` + `os.path.normcase` en una
   función pura `_dentro_de(ruta, base) -> bool` (R17).
5. `huella_local` usa solo `os.stat`: **nunca abre el fichero** (R10).

**Sonda** (R16). `[interprete, "-c", SONDA, *modulos]` con `cwd = raiz/ruta`,
`stdin=DEVNULL`, salida capturada y `timeout=limite_s`. No se usa `-I`: la sonda
tiene que ver el mismo `sys.path` que verá `python -m pytest` desde esa carpeta.
`SONDA` es un literal que, por módulo, llama a `importlib.util.find_spec` (no
ejecuta el `__init__` del primer nivel; en un nombre con puntos sí se importan los
padres, que es inevitable). Toma `origin` o, si es un paquete de espacio de
nombres, la primera de `submodule_search_locations`. Imprime en JSON
`{"origenes": {...}, "coverage": find_spec("coverage") is not None}`. Una salida
distinta de 0, un JSON ilegible o el timeout lanzan `ErrorDeSonda` con el motivo.
La sonda se lanza siempre, aunque no haya módulos vigilados: también responde si
hay `coverage`, que hoy pregunta el propio bash.

**`decidir`** (R18–R21):

```
interprete = servicios.interprete(servicio, raiz)
sondeo = sondear(...)       # ErrorDeSonda -> aviso + clave None (R15)
clave, avisos = clave_de(...)
fichero = raiz/.arnes_cache/suite_<nombre>.ok
servir = not sin_cache and clave and fichero.is_file()
         and fichero.read_text().strip() == clave
         and (not sondeo.tiene_coverage or (raiz/ruta/"coverage.json").is_file())
fecha_verde = mtime(fichero) en hora local "%Y-%m-%d %H:%M" si servir
```

**CLI** (R22). `python -m harness.cache_suites --servicio NOMBRE [--sin-cache]
[--raiz .]`. Por stdout van las líneas `AVISO|<texto>`, y al final
`SERVIR|<fecha>` o `EJECUTAR|<clave o vacío>`, con código 0. Si el servicio no
está declarado, no es `python` o la declaración es inválida, sale con código 1 y
el motivo en stderr.

## 5. `harness/init.sh` §7 bis (pegamento, sin lógica de clave)

Sustituye las líneas que hoy calculan `HASH_SRV`/`SUCIO_SRV` y comparan, y la
escritura de la caché:

```bash
# al entrar en la sección, una vez:
[ "$SIN_CACHE" = "1" ] && warn "ARNES_SIN_CACHE=1: las suites de los servicios se ejecutan sin caché (y la refrescan si salen en verde)"
# por servicio Python, tras las comprobaciones de tests/ y SALTAR_SUITES:
OPCION_CACHE=""; [ "$SIN_CACHE" = "1" ] && OPCION_CACHE="--sin-cache"
CLAVE_SRV=""; FECHA_VERDE=""
if DECISION=$($PY -m harness.cache_suites --servicio "$NOMBRE" $OPCION_CACHE </dev/null); then
    while IFS='|' read -r TIPO VALOR; do
        case "$TIPO" in
            AVISO)    warn "servicio $NOMBRE ($RUTA): $VALOR" ;;
            SERVIR)   FECHA_VERDE="$VALOR" ;;
            EJECUTAR) CLAVE_SRV="$VALOR" ;;
        esac
    done <<EOF_CACHE
$DECISION
EOF_CACHE
else
    warn "servicio $NOMBRE ($RUTA): no se pudo decidir la caché (python -m harness.cache_suites --servicio $NOMBRE); se ejecuta la suite y no se guarda"
fi
if [ -n "$FECHA_VERDE" ]; then
    ok "servicio $NOMBRE ($RUTA): pytest en verde (caché: ni el servicio ni sus dependencias han cambiado desde el verde del $FECHA_VERDE)"
    continue
fi
# ... la suite se ejecuta igual que hoy ...
# tras el verde:
[ -n "$CLAVE_SRV" ] && mkdir -p .arnes_cache && printf '%s' "$CLAVE_SRV" > ".arnes_cache/suite_${NOMBRE}.ok"
```

`</dev/null`: ni el módulo ni su sonda se comen el heredoc del bucle exterior
(R27). Si falla la llamada (R26), la suite se ejecuta: el error va al lado seguro.
`[AVISO]` y no `[KO]`: D2. El comentario de la sección explica qué entra en la clave.

## 6. Declaración de albaranes (R28)

```json
{ "nombre": "sv1-email", "ruta": "services/albaranes-email", "lenguaje": "python",
  "depende_de": ["services/albaranes-comun"], "importa": ["ruesma_comun"] }
```

Igual en sv2, sv3, sv4 (con su `venv`), sv5, sv6 y sv9 (los siete importan
`ruesma_comun`: grep del 2026-10-15). **Efecto:** en el árbol principal se cachean
y un commit en la comun los invalida; en un worktree la sonda ve la comun del árbol
principal → aviso de R13 y suite siempre ejecutada (D7).

## 7. Porte a `arnes-base` (regla de propagación, R34)

Medido el 2026-10-15: albaranes va por la 1.7.2 y `arnes-base` por la 1.7.15, pero
`servicios.py`, `servicios.ejemplo.json` y la §7 bis de `init.sh` son **idénticos**
(`diff --strip-trailing-cr`). El resto de `init.sh` difiere en la cabecera
adaptable, el venv del proyecto (1.7.4) y comentarios. Porte **pieza a pieza**,
como la 1.7.15, no por el instalador.

- **Destino:** `C:\Users\pgris\PycharmProjects\arnes-base`, rama `main`, commit local
  (sin push) «1.7.16: la caché de suites tiene en cuenta las dependencias de cada
  servicio (origen: albaranes F-072)», solo con estos ficheros. Los sin rastrear
  `codex/` e `instalar_arnes_dual.ps1` son de otra sesión: no se tocan.
- **Payload (`arnes-base/arnes-base/`):** `harness/cache_suites.py` (nuevo),
  `servicios.py`, `servicios.ejemplo.json`, `init.sh` (línea `SIN_CACHE` + §7 bis) y
  `VERSION` → `1.7.16` con la fecha del porte. Tests con los mismos casos, sin el
  prefijo `f072_` y con el origen en el docstring: `tests/test_servicios_dependencias.py`
  (R1–R6), `tests/test_cache_suites.py` (R7–R22, R31–R33) y
  `tests/test_cache_suites_init_sh.py` (R23–R27). R28–R30 son de albaranes y no viajan.
- **`politica_ficheros.json`:** sin cambios (`harness/**` y `tests/**` ya son
  `arnes_puro`; `harness/servicios.json`, `estado_del_proyecto`).
- **`GUIA_INSTALACION.md`:** sección «La caché de suites ve las dependencias de cada
  servicio (1.7.16, fecha)» con el formato de la 1.7.15 (caso, cambio, tabla de
  campos, `ARNES_SIN_CACHE=1`, aviso de worktree, «Qué hacer al actualizar»: aceptar
  la §7 bis, declarar dependencias, la 1.ª ejecución no sirve caché), y la fila de los
  campos en la tabla de «Monorepo multi-servicio».
- **`ENCARGO_1.7.12_…md`:** una línea de cabecera, «Implementado en 1.7.16 (origen:
  albaranes F-072): §4, §9 y §10». La F-028 del backlog del taller (`dev` de
  `arnes-base`) no se toca: la cierra su propia sesión (P5).

## 8. Riesgos y decisiones

- **D1 · La clave se calcula en Python, no en bash.** Así queda testeable y entra
  en la campaña de mutación; bash solo pega. Se descarta ampliar `--shell` con más
  campos: rompe el `read` de cinco campos y complica el bucle.
- **D2 · Módulo de fuera = `[AVISO]` y no `[KO]`** (pregunta P1). En este
  repositorio, cada worktree importa la comun del árbol principal. Un KO pondría
  en rojo todo worktree sin que la feature tenga culpa. La suite sí se ejecuta, y
  el aviso dice qué copia prueba.
- **D3 · No se cambia QUÉ comun importa la suite en un worktree** (pregunta P2).
  Hacerlo con `PYTHONPATH` cambia cómo se ejecutan las suites, no la caché, y queda
  fuera de esta feature.
- **D4/D5 · Descartados** el hash del árbol entero (encargo 1.7.12 §9: cada tarea toca
  `progress/` y no serviría nunca) y caducar por tiempo (acota el verde falso, no lo evita).
- **D6 · La sonda con `find_spec`** no ve un `conftest.py` que toque `sys.path`
  para llegar a otro paquete. Aquí los conftest solo anclan la raíz de su servicio
  (comprobado). La limitación se documenta en el `$doc` del ejemplo.
- **D7 · Coste.** Cada servicio Python suma un proceso y una sonda (~0,3 s cada
  uno). En worktrees, sv1–sv9 dejan de servirse de caché: es el precio de no
  mentir. El implementer mide el tiempo de `init.sh` antes y después.
- **D8 · Versión 1.7.16,** no 1.8.0: el cambio es compatible y la 1.8.0 la reserva
  el encargo de adelgazar el arnés.
- **D9 · La fecha del verde sale del `mtime` del fichero de caché**, no de su
  contenido: el fichero sigue siendo una sola clave.
