<!-- progress/mutacion_F-069.md -->
# F-069 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-069` el 2026-10-24 05:47.

## Alcance

Origen del diff: **rama** (`6601a92f5e838f85f167cfbd304e33eb08ab8135` .. `feature/F-069-usuario-empleado-sigrid`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-alta-sigrid/application/alta_sigrid_service.py` | 135 |
| `services/albaranes-alta-sigrid/config/settings.py` | 18 |
| `services/albaranes-alta-sigrid/domain/models/alta_models.py` | 67 |
| `services/albaranes-alta-sigrid/domain/ports/sigrid_alta_port.py` | 15 |
| `services/albaranes-alta-sigrid/domain/services/usuario_sigrid.py` | 218 |
| `services/albaranes-alta-sigrid/domain/services/validador_alta.py` | 9 |
| `services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py` | 40 |
| `services/albaranes-alta-sigrid/interface_adapters/composition.py` | 2 |
| `services/albaranes-alta-sigrid/main_worker.py` | 15 |
| `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py` | 424 |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | 59 |
| **Total** | **1002** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 148 |
| Mutantes evaluados | 148 |
| Muertos | 146 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2510.3 s |
| SHA de HEAD medido | `8d210975cfc809c040201e1ca3591d88e71066f5` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_opwhnb01/wk_0/services/albaranes-alta-sigrid` | 68.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_opwhnb01/wk_0/services/albaranes-front` | 197.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_opwhnb01/wk_1/services/albaranes-alta-sigrid` | 68.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_opwhnb01/wk_1/services/albaranes-front` | 198.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_opwhnb01/wk_2/services/albaranes-alta-sigrid` | 68.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_opwhnb01/wk_2/services/albaranes-front` | 198.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_opwhnb01/wk_3/services/albaranes-alta-sigrid` | 68.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_opwhnb01/wk_3/services/albaranes-front` | 200.5 |
| Media por mutante evaluado (s) | 17.0 |
| Timeout efectivo por mutante (s) | 401 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:46` [entero]

- Original: `sys.path.insert(0, str(RAIZ_SV9))`
- Mutado:   `sys.path.insert(1, str(RAIZ_SV9))`

#### Análisis

> **Mutante equivalente.** Insertar la raíz de sv9 en la posición 1 en vez de la 0 solo la deja detrás de `sys.path[0]`, que al lanzar el script es su propia carpeta `scripts/`, y ahí solo están `__init__.py` y el propio script: ningún módulo de esa carpeta tapa a `domain`, `infrastructure` ni `config`. Las importaciones resuelven igual en las dos posiciones. Justificación para que la acepte el humano (rigor `critico`).

> **Demostración ejecutable (RM5, 2026-10-24)**: dos copias de sv9 sin `tests/` en una carpeta temporal, original y con el mutante; cada una lanza el script con `--help` como `__main__` y `sys.path[0]` = su `scripts/`, e imprime de dónde salió cada módulo. Las dos resuelven `domain` e `infrastructure` a su propia copia de sv9 y `httpx`, `psycopg` y `tenacity` a site-packages, y salen con 0: mismo comportamiento.

```python
# Demostración RM5 del superviviente 1 de F-069 (sys.path.insert(0) -> insert(1)).
import runpy, shutil, subprocess, sys, tempfile
from pathlib import Path
SV9 = Path(r"C:\Users\pgris\PycharmProjects\albaranes-F-069\services\albaranes-alta-sigrid")
SONDA = r'''
import runpy, sys
script = sys.argv[1]
sys.path[0] = str(__import__("pathlib").Path(script).parent)   # como al lanzar el script
sys.argv = [script, "--help"]
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit as fin:
    codigo = fin.code
for m in ("domain", "domain.services.usuario_sigrid", "infrastructure.sigrid.sigrid_api_alta_client", "httpx", "psycopg", "tenacity"):
    print("MOD", m, sys.modules[m].__file__)
print("SALIDA", codigo)
'''
base = Path(tempfile.mkdtemp(prefix="rm5_f069_"))
for nombre, mutar in (("original", False), ("mutante", True)):
    copia = base / nombre / "albaranes-alta-sigrid"
    shutil.copytree(SV9, copia, ignore=shutil.ignore_patterns("tests", "__pycache__", ".venv", "*.pyc"))
    ruta = copia / "scripts" / "medir_empleados_f069.py"
    texto = ruta.read_text(encoding="utf-8")
    if mutar:
        assert texto.count("sys.path.insert(0, str(RAIZ_SV9))") == 1
        texto = texto.replace("sys.path.insert(0, str(RAIZ_SV9))", "sys.path.insert(1, str(RAIZ_SV9))")
        ruta.write_text(texto, encoding="utf-8")
    r = subprocess.run([sys.executable, "-c", SONDA, str(ruta)], capture_output=True, text=True, cwd=base)
    print(f"== {nombre} (exit {r.returncode})")
    for linea in r.stdout.splitlines():
        if linea.startswith(("MOD", "SALIDA")):
            print("  " + linea.replace(str(base), "<tmp>"))
    if r.returncode: print(r.stderr[-800:])
shutil.rmtree(base)
```

Salida real (`python -I rm5_sv9.py`):

```
== original (exit 0)
  MOD domain <tmp>\original\albaranes-alta-sigrid\domain\__init__.py
  MOD domain.services.usuario_sigrid <tmp>\original\albaranes-alta-sigrid\domain\services\usuario_sigrid.py
  MOD infrastructure.sigrid.sigrid_api_alta_client <tmp>\original\albaranes-alta-sigrid\infrastructure\sigrid\sigrid_api_alta_client.py
  MOD httpx C:\Users\pgris\PycharmProjects\albaranes\.venv\Lib\site-packages\httpx\__init__.py
  MOD psycopg C:\Users\pgris\PycharmProjects\albaranes\.venv\Lib\site-packages\psycopg\__init__.py
  MOD tenacity C:\Users\pgris\PycharmProjects\albaranes\.venv\Lib\site-packages\tenacity\__init__.py
  SALIDA 0
== mutante (exit 0)
  MOD domain <tmp>\mutante\albaranes-alta-sigrid\domain\__init__.py
  MOD domain.services.usuario_sigrid <tmp>\mutante\albaranes-alta-sigrid\domain\services\usuario_sigrid.py
  MOD infrastructure.sigrid.sigrid_api_alta_client <tmp>\mutante\albaranes-alta-sigrid\infrastructure\sigrid\sigrid_api_alta_client.py
  MOD httpx C:\Users\pgris\PycharmProjects\albaranes\.venv\Lib\site-packages\httpx\__init__.py
  MOD psycopg C:\Users\pgris\PycharmProjects\albaranes\.venv\Lib\site-packages\psycopg\__init__.py
  MOD tenacity C:\Users\pgris\PycharmProjects\albaranes\.venv\Lib\site-packages\tenacity\__init__.py
  SALIDA 0
```

### 2. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:306` [booleano]

- Original: `return [dict(zip(columnas, fila, strict=False)) for fila in datos.get("rows") or []]`
- Mutado:   `return [dict(zip(columnas, fila, strict=True)) for fila in datos.get("rows") or []]`

#### Análisis

> **Mutante equivalente** para el contrato de `sql/read` de sigrid-api: cada fila de `rows` trae un valor por cada elemento de `columns` (es una tabla: columnas y filas de la misma consulta), así que `zip` estricto o no da el mismo dict. Es la misma decisión que el cliente de sv9 (`sigrid_api_alta_client.py:208`, F-053), del que el script copia la lectura. Si un día sigrid-api devolviera una fila desparejada, el script de solo lectura daría una medición incompleta, no una escritura. Justificación para que la acepte el humano (rigor `critico`).


## Campaña anterior (nota del implementer)

Primera campaña, sobre `8ede6ca` (T13): 148 mutantes, 137 muertos, **11 supervivientes**.
Nueve eran huecos reales y tienen test nuevo en
`services/albaranes-alta-sigrid/tests/test_f069_t15_supervivientes.py` (`8d21097`): la clave
interna en mayúsculas (`usuario_sigrid.py`), `RAIZ_SV9` y la ayuda del script, la
inmutabilidad de `Medida` y `AltaEscrita`, el porcentaje con n > 1, el tope de 30 s de la
espera, los segundos de la consulta y `--salida` anidada. Cada test se comprobó contra su
mutante aplicado a mano antes de esta segunda campaña, que ya los da por muertos. Quedan
los dos equivalentes de arriba, **pendientes de que el humano acepte la justificación**
(rigor `critico`, `supervivientes_maximos` 0): por eso la orden sale con código 1.
