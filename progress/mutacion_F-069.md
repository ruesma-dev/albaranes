<!-- progress/mutacion_F-069.md -->
# F-069 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-069` el 2026-10-24 04:47.

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
| Muertos | 137 |
| Supervivientes | 11 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2780.2 s |
| SHA de HEAD medido | `8ede6ca071ac0eb95107f984f528b3da00a207a7` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_8i6uhlat/wk_0/services/albaranes-alta-sigrid` | 68.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_8i6uhlat/wk_0/services/albaranes-front` | 211.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_8i6uhlat/wk_1/services/albaranes-alta-sigrid` | 68.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_8i6uhlat/wk_1/services/albaranes-front` | 211.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_8i6uhlat/wk_2/services/albaranes-alta-sigrid` | 68.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_8i6uhlat/wk_2/services/albaranes-front` | 210.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_8i6uhlat/wk_3/services/albaranes-alta-sigrid` | 68.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-069_8i6uhlat/wk_3/services/albaranes-front` | 210.8 |
| Media por mutante evaluado (s) | 18.8 |
| Timeout efectivo por mutante (s) | 423 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-alta-sigrid/domain/services/usuario_sigrid.py:130` [booleano]

- Original: `repetida = _repetida(valor, sin_mayusculas=False)`
- Mutado:   `repetida = _repetida(valor, sin_mayusculas=True)`

#### Análisis

> Hueco real. Ningún test probaba una clave interna que solo difiere en mayúsculas: con `casefold`, `{"usu", "USU"}` daba «repetida» en vez de «claves no admitidas». **Test nuevo** en `tests/test_f069_t15_supervivientes.py`: `test_f069_t15_clave_interna_en_mayusculas_es_no_admitida_no_repetida` (comprobado: con el mutante, 1 failed).

### 2. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:44` [entero]

- Original: `RAIZ_SV9 = Path(__file__).resolve().parents[1]`
- Mutado:   `RAIZ_SV9 = Path(__file__).resolve().parents[2]`

#### Análisis

> Hueco real. Los tests importan el script con la raíz de sv9 ya en `sys.path` (pytest), así que una raíz equivocada no se notaba. **Test nuevo** en `tests/test_f069_t15_supervivientes.py`: `test_f069_t15_script_arranca_fuera_de_sv9_y_su_ayuda_es_la_primera_linea` comprueba `RAIZ_SV9` y lanza el script con `--help` desde otra carpeta, como lo lanzará el líder (comprobado: 1 failed).

### 3. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:46` [entero]

- Original: `sys.path.insert(0, str(RAIZ_SV9))`
- Mutado:   `sys.path.insert(1, str(RAIZ_SV9))`

#### Análisis

> **Mutante equivalente.** Insertar la raíz de sv9 en la posición 1 en vez de la 0 solo la deja detrás de `sys.path[0]`, que al lanzar el script es su propia carpeta `scripts/`, y ahí solo están `__init__.py` y el propio script: ningún módulo de esa carpeta tapa a `domain`, `infrastructure` ni `config`. Las importaciones resuelven igual en las dos posiciones. Justificación para que la acepte el humano (rigor `critico`).

### 4. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:110` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> Hueco real (inmutabilidad de `Medida` sin test). **Test nuevo** en `tests/test_f069_t15_supervivientes.py`: `test_f069_t15_medida_y_alta_escrita_son_inmutables` (comprobado: 1 failed).

### 5. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:121` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> Hueco real (inmutabilidad de `AltaEscrita` sin test). Mismo test nuevo en `tests/test_f069_t15_supervivientes.py`: `test_f069_t15_medida_y_alta_escrita_son_inmutables` (comprobado: 1 failed).

### 6. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:193` [aritmetico]

- Original: `return f"{100.0 * n / total:.1f}".replace(".", ",") if total else "0,0"`
- Mutado:   `return f"{100.0 // n / total:.1f}".replace(".", ",") if total else "0,0"`

#### Análisis

> Hueco real: los tests del resumen tenían cada clase con 1 Quien aprobó, y con n = 1 `100 // n` = `100 * n`. **Test nuevo** en `tests/test_f069_t15_supervivientes.py`: `test_f069_t15_porcentaje_con_varios_de_una_clase` (dos `unico` de cuatro = 50,0; comprobado: 1 failed).

### 7. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:286` [entero]

- Original: `wait=wait_exponential(multiplier=self._espera, max=30),`
- Mutado:   `wait=wait_exponential(multiplier=self._espera, max=31),`

#### Análisis

> Hueco real: con la espera base de los tests (0 s) el tope de 30 s nunca se alcanzaba. **Test nuevo** en `tests/test_f069_t15_supervivientes.py`: `test_f069_t15_espera_entre_reintentos_con_tope_de_30_s` (espera base 100 s y `time.sleep` de tenacity sustituido: las esperas son `[30, 30]`; comprobado: 1 failed).

### 8. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:306` [booleano]

- Original: `return [dict(zip(columnas, fila, strict=False)) for fila in datos.get("rows") or []]`
- Mutado:   `return [dict(zip(columnas, fila, strict=True)) for fila in datos.get("rows") or []]`

#### Análisis

> **Mutante equivalente** para el contrato de `sql/read` de sigrid-api: cada fila de `rows` trae un valor por cada elemento de `columns` (es una tabla: columnas y filas de la misma consulta), así que `zip` estricto o no da el mismo dict. Es la misma decisión que el cliente de sv9 (`sigrid_api_alta_client.py:208`, F-053), del que el script copia la lectura. Si un día sigrid-api devolviera una fila desparejada, el script de solo lectura daría una medición incompleta, no una escritura. Justificación para que la acepte el humano (rigor `critico`).

### 9. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:343` [aritmetico]

- Original: `por_correo[correo] = Medida(_login(correo), clase, ide, time.perf_counter() - inicio)`
- Mutado:   `por_correo[correo] = Medida(_login(correo), clase, ide, time.perf_counter() + inicio)`

#### Análisis

> Hueco real: solo se comprobaba que `segundos` no fuera nulo. **Test nuevo** en `tests/test_f069_t15_supervivientes.py`: `test_f069_t15_segundos_es_lo_que_tardo_la_consulta` (reloj que avanza 0,25 s por lectura desde 1000 s: la diferencia es pequeña y positiva, la suma daría ~2000 s; comprobado: 1 failed).

### 10. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:382` [entero]

- Original: `parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])`
- Mutado:   `parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])`

#### Análisis

> Hueco real: nadie miraba la ayuda del script. Lo mata el mismo test que el 2: `test_f069_t15_script_arranca_fuera_de_sv9_y_su_ayuda_es_la_primera_linea` (la ayuda contiene la primera línea del docstring y no la segunda; comprobado: 1 failed).

### 11. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:414` [booleano]

- Original: `salida.mkdir(parents=True, exist_ok=True)`
- Mutado:   `salida.mkdir(parents=False, exist_ok=True)`

#### Análisis

> Hueco real: `--salida` siempre era una carpeta que ya existía. **Test nuevo** en `tests/test_f069_t15_supervivientes.py`: `test_f069_t15_salida_anidada_que_no_existe` (comprobado: 1 failed).

