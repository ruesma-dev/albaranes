<!-- progress/spec_F-114.md -->
# F-114 · Informe del spec-author (2026-10-30)

Spec v1 en `specs/F-114-proveedor-todos-sigrid/` (requirements 110/150, design 183/250, tasks T0–T9).
Rama `feature/F-114-proveedor-todos-sigrid` (worktree `../albaranes-F-114`). Rigor `estandar`. Solo sv4.

## Qué propone

- Check «Solo de la obra», marcado al cargar, junto al combo de proveedor de la ficha. Marcado: lo de hoy, sin tocarlo.
- Desmarcado: búsqueda en el servidor (`GET /api/sigrid/proveedores/todos?q=`), con 3 caracteres como mínimo,
  50 resultados como máximo, por nombre (sin distinguir mayúsculas ni acentos) o por CIF.
- Qué se lista: los proveedores **vivos** de `prv`, es decir `con.tip = 5`, `emp = 1` y `fecbaj = 0`. Es la misma
  definición que usa sigrid-api (`L17_PROVEEDOR_POR_CIF` de su F-015, leída en
  `sigrid-api/application/use_cases/albaran_compra_statements.py`) para reconocer al proveedor de un alta sin contrato.
- Una entrada por CIF, con «N fichas en Sigrid» cuando hay varias. Los CIF propios (F-063) se quitan.

## Decisiones para la PARADA 1 (detalle en design §8)

| D | Pregunta | Recomendación |
|---|---|---|
| D1 | ¿Lista completa o búsqueda al escribir? | **(b) búsqueda en servidor**, mínimo 3, límite 50. (a) solo si T0 da ≤ 5.000 CIF vivos |
| D2 | ¿Qué hacer con un CIF repetido? | **Una entrada por CIF con «N fichas en Sigrid»**. Avisa de que puede salir `proveedor_ambiguo` |
| D3 | ¿Bajas y bloqueos? | **Baja = `con.fecbaj ≠ 0`, se excluye**. `prvblo` (bloqueos por empresa) no se filtra ni se marca: no se sabe qué significa y sigrid-api no lo mira |
| D4 | ¿Se recuerda el check? | **No**: sale marcado en cada carga, también tras el guardado automático |
| D5 | ¿Cómo encaja con F-062? | **Sin cambios**. Es la misma edición manual (solo `prv.cif`). sv3 no la corrige porque el CIF existe, y retira la marca `[CORREGIDO]` |
| D6 | ¿Y el contrato del proveedor anterior, que se queda seleccionado? | **Fuera: feature aparte** (abajo) |
| D7 | ¿Qué empresa? | **`emp = 1`**, como el resto de sv4 |

## Aguas abajo de un proveedor sin contrato en la obra (design §6)

- **Guardar**: relanza la búsqueda (F-052 D4-A). sv3 devuelve `no_results` y la ficha ya lo enseña. La red de
  proveedor (regla 17) no actúa.
- **Botón de buscar contratos**: también `no_results`; el combo de contratos queda vacío.
- **Valoración**: valoración directa de F-075 (`no_contract`) si el albarán trae importes. Sin importes, no se puede
  aprobar hasta completarla.
- **sv9**: `cod_contrato` nulo y todas las líneas sin vincular, con producto genérico.
  - **No manda `sin_contrato`**: ese campo existe solo en `sigrid/proforma` (§8.10 de `sigrid_api.md`), no en
    `sigrid/albaran`.
  - Con la F-015 desplegada (24-10), sigrid-api saca la identidad del proveedor, por este orden: del contrato; si no
    hay, del último albarán de ese CIF; si tampoco, del único `prv` vivo con ese CIF.
  - Si no encuentra ninguno da `proveedor_no_encontrado`; si encuentra varios, `proveedor_ambiguo`. Los dos quedan
    `no_admitido` en sv9 desde F-104.
  - **sv9 no necesita cambios.**

## Feature aparte que se propone (D6; no se ha dado de alta)

**«Al cambiar el CIF, desseleccionar el contrato que no es de ese proveedor» (sv3 y/o sv4).**

- Qué pasa hoy:
  - sv3 hace *upsert* de los contratos (`upsert_contratos`).
  - Con 0 resultados no limpia `selected_contrato_codigo`.
  - El PUT de sv4 reenvía el contrato seleccionado del campo oculto.
- Consecuencia: si el documento tenía elegido un contrato del proveedor A y se cambia a B (de la lista de la obra o de
  la global), la valoración sigue con el contrato de A, y sv9 pediría el alta con el contrato de A y el CIF de B.
- Gravedad: el fallo sería visible (lo rechaza sigrid-api), no silencioso. Ya ocurre hoy, F-114 no lo crea.
- Antes de diseñarlo hay que confirmar el caso en local.

## Riesgos (design §7)

- **R-1, CIF guardado con otra grafía**: sigrid-api compara `prv.cif` exacto con el CIF normalizado que manda sv9. La T0
  lo mide.
- **R-2, contrato del proveedor anterior**: es el problema de D6.
- **R-3, sintaxis**: puede que el validador de sigrid-api no acepte `TOP (?)`, `COLLATE` o `ESCAPE`. La T0 prueba la
  SQL tal cual; si falla, se para.
- **R-4, rendimiento**: `LIKE '%…%'` sobre `prv`. La T0 mide el tiempo.

## T0 (MANUAL, solo lectura; resultados aquí)

Las tres lecturas y su comando de PowerShell están en `tasks.md`, bloque 0. Sus resultados se anotan en esta sección.

Hecha por el líder el 2026-10-30, en solo lectura, con `sql/read` de sigrid-api sobre la base de negocio. La clave solo
estuvo en una variable del proceso y se borró al terminar. No se anotan nombres ni CIF de proveedores, porque entre
ellos hay personas físicas.

- **A · Tamaño** (`con.tip = 5`, `emp = 1`).
  - 7.367 fichas y 7.266 CIF distintos. Vivas (`fecbaj = 0`): 7.295 fichas, con 7.232 CIF.
  - 5 CIF vivos están repetidos y 1 ficha viva tiene el CIF sin normalizar (R-1).
  - La consulta tardó 2,2 s.
  - Como hay más de 5.000 CIF vivos, **D1 = (b), búsqueda en el servidor**.
- **B · Bloqueos**: ningún proveedor vivo tiene un `prvblo` activo en la empresa 1. Se confirma D3: no se filtran.
- **C · SQL de la búsqueda**:
  - Con `ESCAPE` y la barra invertida falla con HTTP 500 (SQL Server 506: «Carácter de escape "" no válido»): la barra
    no llega intacta hasta SQL Server.
  - **Con `ESCAPE '!'` funciona.** «cera» devuelve 35 CIF en 1,6 s, «ferr» llega al límite de 51 en 1,3 s y un trozo
    de CIF devuelve 2 en 1,2 s.
  - `TOP (?)` y `COLLATE` funcionan.
  - El carácter de escape pasa a `!` en design §3 y en `tasks.md`.
- **Riesgos**: R-3 resuelto con el cambio de escape. R-4: entre 1,2 y 1,6 s, por debajo de los 5 s.
- Dato conocido: 3.543 proveedores con contrato en la empresa 1 el 29-09 (`search_proveedores` de sv3,
  `azure-apps/albaranes.md` §8). `prv` entero será mayor.

## Notas para el líder

- `azure-apps/sigrid_api.md` (l.796, 824, 1115 y 1778) sigue diciendo que la F-015 está «PENDIENTE DE DESPLIEGUE», pero
  `azure-apps/albaranes.md` (F-104) la da por desplegada el 24-10. El documento es de sigrid-api: avisar a su sesión,
  no editarlo desde aquí.
- `.env` local: la T8 (navegador) depende de a qué BBDD apunte sv4 local. Elegir un proveedor guarda: no se hace sin
  autorización.
