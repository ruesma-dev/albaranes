<!-- harness/ARNES_VERSION.md -->
# Version del arnes instalada en este repositorio

Lo escribe `instalar_arnes.ps1`. **No lo edites a mano.**

| Dato | Valor |
|---|---|
| Version del arnes | `1.10.0` |
| Fecha de la version | 2026-11-12 |
| Instalado/actualizado el | 2026-11-12 20:18 |
| Modo | actualizar |
| Origen | `arnes-base` |

> **Lo hecho a mano en la actualizacion a la 1.10.0 (2026-11-12).**
> Desde la 1.7.2 con piezas sueltas de la 1.7.16 (cache de suites de F-072 y
> `backlog.py`), con el instalador en modo `actualizar`. Se conservaron los seis
> `adaptado` y en cada uno se incorporo a mano lo generico nuevo:
> `CLAUDE.md` (paradas, `qa-e2e`, prioridades de ocho estados, regla «tal
> cual», merges y push, protocolo de `azure-apps` compartido), `CHECKPOINTS.md`
> (el de la 1.10.0 con las tres trampas de C3 y el bloque propio de evals en
> C4 ter), `harness/init.sh` (el de la 1.10.0 con `REQUIERE_ENV=0`),
> `docs/CONVENTIONS.md` (quien hace cada merge) y `.claude/settings.json` (el
> de la 1.10.0: fuera el hook `PostToolUse` local). `docs/referencia/README.md`
> no cambia. Los tests con nombre propio que copiaban tests genericos
> (`test_f038_*`, `test_f039_r15_r16_*`, `test_f040_r*`, cinco de `test_f072_*`)
> se borraron a favor de sus genericos; `test_f039_r3_r7_*` quedo reducido a su
> caso propio (`test_f039_r7_paridad_f012.py`) y los que traen casos propios
> siguen.
> Detalle en `progress/arnes_1.10.0.md`.

> **AVISO de la 1.6.3: hay informes de mutacion que pueden no valer.**
> Hasta ese parche la campania lanzaba la suite dejando escribir `__pycache__`,
> asi que un `.pyc` compilado desde el codigo MUTADO sobrevivia a la
> restauracion del `.py`. El sintoma es una campania absurdamente rapida: si el
> **coste por mutante** —«Tiempo total» x workers / mutantes— de un informe baja
> de un segundo, relanza esa campania con la cache limpia antes de fiarte de sus
> numeros.

> **AVISO de la 1.6.0, la 1.7.2, la 1.8.0, la 1.9.0 y la 1.10.0: los informes de
> mutacion no son comparables entre versiones.** La 1.6.0 empezo a mutar `is` /
> `is not` (aqui se remidieron F-019 y F-027; el resto de
> `progress/mutacion_*.md` lleva anotado con que vara se midio). La 1.7.2 deriva
> el timeout de la linea base: no compares campanias con «Timeout efectivo»
> distinto. La 1.8.0 muestrea uno por linea en `critico` y deja `estandar`
> informativa; la 1.9.0 cambia el criterio de muerte (`indeterminado`) y anade
> operadores; la 1.10.0 cambia el reloj de la linea base. El primer
> `--incremental` tras actualizar mide entero.

Para actualizar a una version posterior, desde el repositorio `arnes-base`:

```powershell
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\albaranes" -Modo actualizar
```

Que hace el instalador por su cuenta al actualizar, sin que tengas que
vigilarlo fichero a fichero:

- **No toca el estado de este proyecto**: `harness/features.json`,
  `docs/ARCHITECTURE.md`, `progress/`, `specs/`, `docs/referencia/`,
  `BACKLOG.md` y la configuracion local. Ni con `-Forzar`.
- **Aplica sin preguntar** los ficheros genericos del arnes (los agentes,
  `harness/*.py`, `specs/SPECS.md`...), guardando antes una copia de la
  version que tenias.
- **Pregunta solo** por los que mezclan lo generico con lo tuyo (`CLAUDE.md`,
  `CHECKPOINTS.md`, `harness/init.sh`, `docs/CONVENTIONS.md`,
  `.claude/settings.json`), y la opcion por defecto es CONSERVAR el tuyo.

La clasificacion completa vive en `politica_ficheros.json`, en `arnes-base`.
Detalle en `GUIA_INSTALACION.md`.