<!-- progress/impl_F-106.md -->
# F-106 · informe del implementer

Rama `feature/F-106-precio-al-cambiar-medicion` (worktree `../albaranes-F-106`). Rigor `critico`.

## Pasada 1 (2026-10-28): fusión de `dev` y T0

**Fusión de `dev` (5dd1f45)** en la rama (`dc9e4c2`). Conflictos en `harness/features.json`, `BACKLOG.md` y
`progress/current.md`, resueltos con lo de `dev`: F-106 `in_progress` con una sola clave `branch` y los servicios de la
spec v3 (comun, sv4, sv6, sv9); `current.md` de `dev`; `BACKLOG.md` regenerado con `python harness/backlog.py`.

Alcance de esta pasada: **solo la T0** (orden del líder). La T1 no se ha empezado; no se ha tocado código ni lanzado
ninguna suite.

### T0 · cuántas líneas pendientes no cuadran (solo lectura, producción)

**Cómo se leyó.** BBDD `albaranes` de Azure (`psql-albaranes-*`), una sola conexión psycopg con
`options=-c default_transaction_read_only=on`; el script comprueba antes `SHOW transaction_read_only` = `on` (salió
`on`) y aborta si no. Variables de `infra/00_vars.ps1` (con su capa local no versionada); la clave `PG-PASSWORD` salió
de Key Vault solo a `$env:PG_PASSWORD` del proceso y se borró en `finally` (comprobado: vacía al terminar), nunca a
fichero. Solo `SELECT`. El script vive en el scratchpad de la sesión, no en el repo; imprime solo recuentos (ni
textos, ni importes de proveedor, ni nombres). Fecha: 2026-10-28.

**Universo.** Documentos activos de `albaran_documents_merge`: **57 pendientes** (no aprobados) y 100 aprobados. De
los 57, 50 tienen valoración con filas (49 `ok`, 1 `manual`): 126 filas (93 `from_albaran`, 32 `synthetic_modifier`,
1 `manual`).

**Fórmula.** La de la T0: `dif = |round(Q × P × (1 − COALESCE(d, 0)/100), 2) − I|`, con `Q = cantidad_convertida ??
cantidad_albaran`. Se repitió con `importes.importe_de_linea` de comun (la que usará `cuadra_linea`, que ignora un dto
inválido): mismo resultado, 5 filas.

**(1) Cuadre.** Filas con I ≠ 0 y P no nulo:

| Universo | `importe_source` | Filas | No comparables | > 0,02 € | > 0,1 € | > 1 % |
|---|---|---|---|---|---|---|
| U1 · literal de la T0 | `calculated` | 48 | 0 | 0 | 0 | 0 |
| | `declared_albaran` | 50 | 0 | 5 | 5 | 5 |
| | **total** | **98** | 0 | **5 (5,10 %)** | 5 | 5 |
| U2 · filas que pinta la ficha (con línea de contrato o derivada) | total | 98 | 0 | 5 (5,10 %) | 5 | 5 |
| U3 · U2 sin las de almacén (partida final vacía) | total | 78 | 0 | 4 (5,13 %) | 4 | 4 |

Documentos afectados (con al menos una fila > 0,02 €): **2 de los 45** documentos con filas en el universo
(**4,44 %**), es decir el **3,51 % de los 57 pendientes**. En U3, 1 de 33 (1,75 % de los pendientes).

- Las 5 filas que no cuadran son todas `declared_albaran`, el origen de R-1 (sv6 guarda el importe leído y acepta
  hasta un 5 % de diferencia sin motivo). Ninguna `calculated` falla.
- Las 5 superan el 1 % y los 0,1 €: no son redondeos. Si no se arreglan, R16/R17 las bloquearían.
- No hay filas no comparables (Q nula) en el universo.

**Veredicto del umbral (design §13 R-1, 10 %): NO se pasa.** 5,10 % de las líneas y 4,44 % de los documentos con
filas (3,51 % de los pendientes). Por esta regla se puede seguir con la T1. La decisión es del líder.

**(2) Filas legadas en documentos pendientes** (R27: desde el despliegue se conservarán enteras al revalorar):

| Marca (`es_fila_manual`) | Filas | Documentos |
|---|---|---|
| `bloqueada` | 8 | 2 |
| `line_kind IN ('manual','reparto')` | 1 | 1 |
| `precio_unitario_agreement = 'manual'` | 11 | 8 |
| `partida_action = 'almacen_elegido'` | 1 | 1 |
| derivada `manual_override` | 2 | 2 |
| **cualquiera de ellas** | **16** | **8** |

16 de las 126 filas pendientes (12,7 %), en 8 de los 50 documentos con valoración, contarán como `fila_entera` al
revalorar después del despliegue (R-3).

### Tareas

- [x] T0: medición en producción (solo lectura), resultado arriba.
- T1–T25: sin empezar (las autoriza el líder).

## Fase RED

No aplica todavía: la T0 es una medición y no tiene test. Empieza en la T1.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | ninguno en esta pasada (T0 no tiene test; ninguna suite lanzada) |
| Cobertura de las líneas cambiadas | no aplica: sin código cambiado |
| Mutantes generados / supervivientes | no aplica todavía (campaña en la T21) |
| Tiempo de la suite | no aplica |
| `bash harness/init.sh` | no ejecutado en esta pasada: se lanzará cuando haya código (T1 en adelante) |
