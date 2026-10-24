<!-- specs/F-104-codigos-contrato-v83/design.md -->
# F-104 · sv9 y sv4 entienden los códigos del contrato v8.3 de sigrid-api · Diseño (v1)

Contrato v8.3: `sigrid-api` `871cc0c`, `specs/F-009-alta-albaran-compra/contrato_albaranes.md` §3.2–§3.3; resumen en su
`progress/t0_F-015_albaranes.md`. Se enlaza; no se copia ni se edita (regla del humano del 2026-10-06: albaranes solo
edita lo que consume, y aquí ni eso: el acuse ya se envió).

## 1. Encaje y límite de servicio

- **sv9** sigue siendo el único que habla con `sigrid/albaran`. F-104 solo amplía un **dato** del dominio: la tabla
  `CODIGOS_CABECERA` de `domain/services/clasificador.py` (capa *domain*, pura). Ni petición, ni cliente, ni
  comparador, ni servicio de aplicación cambian.
- **sv4** solo lee `albaran_altas_sigrid`: textos en `domain/models/alta_sigrid_models.py` (*domain*) y una rama en la
  plantilla del panel (*interface_adapters*, Jinja2).
- Sin responsabilidad nueva, sin `ruesma_comun`, sin DDL, sin configuración nueva: no hay límite de servicio que
  evaluar. Encaje con `docs/ARCHITECTURE.md` (tabla de servicios, sv9 = único que escribe en el ERP): intacto.
- Relación con **F-103** (`blocked`): su D6 / R11–R14 / T7 (Bloque C) quedan **absorbidos** por F-104. Al retomar
  F-103 hay que quitar ese bloque de su spec (anotado en `progress/current.md`; aquí no se toca su rama).

## 2. Ficheros a crear

- `services/albaranes-alta-sigrid/tests/test_f104_contrato_v83.py` — R1–R6, R10 (nombres `test_f104_rN_...`). Sin red
  ni BBDD: `ErrorAlta`/`RespuestaAlta` construidos a mano, `SigridFalso` y el repositorio en memoria de
  `tests/f053_fakes.py` (como `test_f053_servicio_previa.py`), `Settings` con `monkeypatch` (como
  `test_f053_t3_esqueleto.py`), y lectura de `infra/*.ps1` y `.env.example` como texto (R4).
- `services/albaranes-front/tests/test_f104_textos_avisos.py` — R7–R10 (textos, `avisos_sigrid`, render del panel con
  los *fixtures* `render_detalle`/`documento_detalle` de F-077).

## 3. Ficheros a modificar

### 3.1 sv9

- `services/albaranes-alta-sigrid/domain/services/clasificador.py`
  - En `CODIGOS_CABECERA`, bloque «Se corrige obra o contrato en sv4, o alta a mano en Sigrid», tras
    `proveedor_sin_albaran_previo`:
    ```python
    # Contrato v8.3 (F-015 de sigrid-api).
    "proveedor_no_encontrado": _NO_ADMITIDO,
    "proveedor_ambiguo": _NO_ADMITIDO,
    "retencion_no_soportada": _NO_ADMITIDO,
    ```
  - `proveedor_sin_albaran_previo` se queda (R2) con el comentario `# retirado en la v8.3: se quita tras F-104 T7`.
  - Docstring: «códigos del contrato de F-009 v8.3 (§3.3)».
  - **T8 (R10)**: se borra la línea de `proveedor_sin_albaran_previo` y su comentario.
- `services/albaranes-alta-sigrid/tests/test_f053_clasificador.py`: `test_f053_r18_la_tabla_es_la_del_contrato_v8`
  compara la tabla **entera**, así que `TABLA_CABECERA` gana los tres Errores v8.3 (y en T8 pierde el Código retirado);
  docstring a «v8.3, `871cc0c`». Es el único test existente que cambia.
- `services/albaranes-alta-sigrid/tests/test_f053_servicio_previa.py`: en T8, el caso parametrizado de
  `proveedor_sin_albaran_previo` → `NO_ADMITIDO` pasa a `proveedor_no_encontrado` → `NO_ADMITIDO`.
- `services/albaranes-alta-sigrid/sv9.md`: cabecera «contrato v8.3, `871cc0c` (rama F-015 de sigrid-api)» y sección
  nueva «Códigos del contrato v8.3 (F-104)» (≤ 12 líneas): los cinco, su estado, que los avisos no bloquean y se ven en
  el panel, y el estado de la retirada (D1).

### 3.2 sv4

- `services/albaranes-front/domain/models/alta_sigrid_models.py`
  - `TEXTOS_MOTIVO_ALTA`, bloque «Códigos de cabecera de sigrid-api», tras `proveedor_sin_albaran_previo` (que **no**
    se borra nunca, R10):
    ```python
    # Contrato v8.3 (F-015 de sigrid-api; F-104).
    "proveedor_no_encontrado": "El proveedor no existe en Sigrid en la empresa de la obra",
    "proveedor_ambiguo": "Hay varios proveedores en Sigrid con ese CIF",
    "retencion_no_soportada": "La retención del contrato no la admite el alta automática: alta a mano",
    ```
    y un bloque nuevo, tras el de códigos de línea:
    ```python
    # Avisos de cabecera de sigrid-api (v8.3): no son motivos ni bloquean;
    # el panel los pinta en «Avisos de Sigrid» con su mensaje (F-104 R8).
    "retencion_del_contrato": "Sigrid aplicó la retención del contrato",
    "cabecera_sin_dato": "Sigrid dejó vacío algún dato de pago de la cabecera",
    ```
  - `AltaSigridVista`: `computed_field` nuevo `avisos_sigrid -> list[dict[str, Any]]`: por cada elemento dict de
    `avisos`, `{"codigo", "texto", "mensaje", "referencia_linea"}` con `texto = TEXTOS_MOTIVO_ALTA.get(codigo)` (o
    `None`); ignora lo que no sea dict, como `avisos_resolucion`.
- `services/albaranes-front/templates/_alta_sigrid.html`, bloque `{% if alta.avisos %}`: itera `alta.avisos_sigrid`;
  con `a.texto`: `<li title="{{ a.codigo }}">{{ a.texto }}{% if a.mensaje %} · {{ a.mensaje }}{% endif %}…</li>`; sin
  texto, la línea de hoy (`<code>{{ a.codigo }}</code> · mensaje`). El sufijo «(línea N)» igual en las dos ramas.

### 3.3 Fuera del repositorio

- `azure-apps/albaranes.md` §10: viñeta nueva al final, «Códigos del contrato v8.3 (F-104, oct 2026)»: los tres
  errores a `no_admitido`, los dos avisos informativos (fuera de `ALTA_SIGRID_AVISOS_BLOQUEANTES`) y visibles en el
  panel, `proveedor_sin_albaran_previo` hasta la verificación, orden de despliegue (§7). Commit local en `azure-apps`.

## 4. Clases y funciones

| Símbolo | Capa | Cambio |
|---|---|---|
| `clasificador.CODIGOS_CABECERA` | domain (sv9) | +3 entradas; −1 en T8 |
| `clasificar`, `motivos_de_error` | domain (sv9) | sin cambios (R1 las ejercita) |
| `alta_sigrid_models.TEXTOS_MOTIVO_ALTA` | domain (sv4) | +5 entradas |
| `AltaSigridVista.avisos_sigrid` | domain (sv4) | nuevo `computed_field`, puro |
| `_alta_sigrid.html` | interface_adapters (sv4) | rama `texto` en «Avisos de Sigrid» |

## 5. Ficheros que NO se tocan

- sv9: `domain/services/comparador_previa.py` (R6, R11), `domain/models/alta_models.py` (`RespuestaAlta` ya descarta
  `filas` y guarda `totales` entero), `infrastructure/sigrid/sigrid_api_alta_client.py` (la forma no cambia; su
  docstring «v8.2» se deja: describe la petición, que es la misma), `application/alta_sigrid_service.py`,
  `config/settings.py` (R4 solo lo comprueba), `.env.example`, `main_worker.py`.
- `infra/*.ps1` (ni `set_alta_sigrid.ps1` ni `create_capps_sv9.ps1`): sin variables nuevas.
- `ruesma_comun`, sv3 (DDL), sv1, sv2, sv5, sv6. La rama y la spec de F-103.
- El repositorio de sigrid-api y `azure-apps/sigrid_api.md` (suyos).

## 6. Verificación MANUAL (líder, solo lectura)

**M1 · antes de desplegar** (R13), desde `infra/` con `. .\00_vars.ps1; . .\00_capps_vars.ps1`:
```powershell
az containerapp show -n ca-sv9-alta-sigrid -g $RG --query "properties.template.containers[0].env[?name=='ALTA_SIGRID_AVISOS_BLOQUEANTES'].{n:name,v:value}" -o table
```
VERDE: vacío (manda el defecto) o un CSV sin `retencion_del_contrato` ni `cabecera_sin_dato`.

**M2 · tras el despliegue de F-015** (R14). PostgreSQL `albaranes` de Azure (las `PG_*` de Azure en la consola: el
`.env` apunta a local), en `BEGIN READ ONLY; … ROLLBACK;`, con `:desde` = fecha ISO del despliegue de F-015:
```sql
SELECT estado,
  COUNT(*) AS altas,
  COUNT(*) FILTER (WHERE motivos_json::jsonb @> '[{"codigo":"proveedor_sin_albaran_previo"}]') AS retirado,
  COUNT(*) FILTER (WHERE motivos_json::jsonb @> '[{"codigo":"proveedor_no_encontrado"}]'
                      OR motivos_json::jsonb @> '[{"codigo":"proveedor_ambiguo"}]'
                      OR motivos_json::jsonb @> '[{"codigo":"retencion_no_soportada"}]') AS errores_v83,
  COUNT(*) FILTER (WHERE avisos_json::jsonb @> '[{"codigo":"retencion_del_contrato"}]') AS con_retencion,
  COUNT(*) FILTER (WHERE avisos_json::jsonb @> '[{"codigo":"cabecera_sin_dato"}]') AS sin_dato,
  COUNT(*) FILTER (WHERE motivos_json LIKE '%"aviso_bloqueante"%'
                     AND (motivos_json LIKE '%retencion_del_contrato:%'
                          OR motivos_json LIKE '%cabecera_sin_dato:%')) AS aviso_v83_bloqueo
FROM albaran_altas_sigrid
WHERE ultimo_intento_at_utc >= :desde
GROUP BY estado ORDER BY estado;
```
VERDE: `retirado` = 0 en todas las filas; `errores_v83` > 0 solo en `no_admitido`; `aviso_v83_bloqueo` = 0. Si
`con_retencion` = 0, aún no ha pasado un albarán de contrato con retención: se repite más tarde (no es rojo). Rojo
(`errores_v83` en `error`): sv9 corre una imagen sin F-104; parar y avisar al humano. El resultado (solo recuentos por
estado) va a `progress/impl_F-104.md`.

**M3 · panel** (R8, R14): el líder abre en el navegador la ficha de un alta con `con_retencion` > 0 y comprueba
«Sigrid aplicó la retención del contrato · <mensaje de sigrid-api>», con el código en el `title`, sin estado de error.

## 7. Despliegue (lo lanza el humano) y vuelta atrás

- Tras APPROVED, fusión en `dev` e `init.sh` en verde en el árbol principal: `Set-DeployTag; .\deploy.ps1 -Only
  sv9,sv4` (sin `ruesma_comun` ⇒ solo esas dos imágenes; sin cambios de configuración; `deploy.ps1` enseña antes
  `ALTA_SIGRID_COMMIT`, que sigue en `true` y no se toca). Orden entre ellas indiferente (sv9 sin sv4: el panel
  enseña el código en crudo, nunca se pierde; sv4 sin sv9: textos que aún no se usan).
- **Antes o a la vez que la F-015 de sigrid-api**, que avisa antes de desplegar. Nunca después: con la v8.3 y la imagen
  actual, los tres Errores v8.3 van a `error` (H25) y el revisor ve «fallo del servicio» donde toca «alta a mano».
- La imagen con F-104 es compatible con la v8.2 aún desplegada: los códigos nuevos no llegan y el retirado sigue
  mapeado (R2).
- T8 (retirada) no exige despliegue propio: sale con la siguiente imagen de sv9 (D1).
- Vuelta atrás: la imagen anterior de sv9/sv4 (los tres códigos vuelven a `error`); sin datos que migrar.

## 8. Decisiones abiertas (las valida el humano en la PARADA 1; recomendada primero)

**D1 · Cómo y cuándo retirar `proveedor_sin_albaran_previo`.**
1. *Recomendada*: T8 dentro de F-104, tras M2 en verde: se quita de `CODIGOS_CABECERA` (y del test de la tabla), el
   texto de sv4 se conserva (altas antiguas), y la imagen sale con el siguiente despliegue de sv9, sin uno propio
   (el código ya no llega: con o sin la línea, sv9 se comporta igual). Tras APPROVED de T1–T7, F-104 queda `blocked`
   («espera al despliegue de F-015 de sigrid-api», como F-085) y se cierra en `done` con T8 fusionada.
2. Cerrar F-104 en `done` al desplegar y dejar la retirada como nota en `progress/current.md` para la próxima feature
   que toque sv9. Descartada como primera: es la nota que se pierde (lección del 2026-08-08).
3. No retirarlo nunca (entrada muerta, inofensiva). Descartada: el contrato pide quitar el mapeo.

**D2 · Cómo se ven los dos Avisos v8.3 en el panel.** Hoy «Avisos de Sigrid» pinta `<code>codigo</code> · mensaje`.
1. *Recomendada*: texto de `TEXTOS_MOTIVO_ALTA` **más** el `mensaje` de sigrid-api, código en el `title` (R8). El
   mensaje lleva lo que importa (código, porcentaje, base y cuota de la retención; columnas vacías en
   `cabecera_sin_dato`) y no se pierde. Solo cambia la línea de los avisos con texto: los otros nueve, como hoy.
2. Textos en la tabla, pero panel sin cambios: los dos textos quedarían muertos (nadie los lee).
3. Texto **en lugar** del mensaje. Descartada: se pierden porcentaje, cuota y columnas.

## 9. Riesgos

- **Nombres de los códigos**: salen de `871cc0c` (rama de sigrid-api aún sin fusionar). Si cambian antes de su
  despliegue, se corrige la tabla antes de desplegar; M2 lo destapa (`errores_v83` en `error`).
- **Despliegue tarde** (después de F-015): ver §7; mitigación, el aviso previo de sigrid-api y M1.
- **`motivos_json`/`avisos_json` no JSON** en filas antiguas: el `::jsonb` de M2 fallaría; si pasa, se filtra antes con
  `motivos_json LIKE '[%'` (es solo lectura).
- **Conflicto con F-103** al fusionarla: toca los mismos bloques (`CODIGOS_CABECERA`, `TEXTOS_MOTIVO_ALTA`); lo evita
  quitar su Bloque C al retomarla (§1).
