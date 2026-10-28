# F-110 · Diseño técnico (v1)

Servicios: **comun** (la menor siguiente a la que deje F-106; previsto 0.10.0 → 0.11.0), **sv9-alta-sigrid**,
**sv4-front**, `infra/` y documentación. Sin DDL, sin colas, sin endpoints nuevos. sv3, sv5, sv6 y sigrid-api no se
tocan desde aquí (sigrid-api lo cambia su propia sesión, F-018). Se implementa sobre `dev` con F-106 fusionada.

## 1. Límite de servicio

Qué se manda a Sigrid es de sv9 (dueño de la petición, regla 19); lo que la ficha enseña antes de aprobar, de sv4; la
regla que comparten vive en comun (`ruesma_comun.alta_sigrid`), como «vinculada» y «producto efectivo». Que Sigrid
acepte y escriba el `dto` es de sigrid-api (F-018): albaranes solo pide y consume. Ninguna responsabilidad nueva.

## 2. Cómo es hoy (`dev` 43e87e5; F-106 aún sin fusionar)

- sv9 `_linea_peticion` (`validador_alta.py:288-314`): `precio = round(|I| / |Qs|, 6)` (`:294`), sin descuento;
  `LineaPeticion` no tiene `dto` (`alta_models.py:181-205`). F-106 mueve esa cuenta a `alta_sigrid.linea_a_sigrid`
  y añade P y d a `LineaAlta` y `SQL_LINEAS` (su R2, R17).
- La previa compara por línea `total` frente a I con `ALTA_SIGRID_TOLERANCIA_EUR` 0,05, la partida y los avisos
  (`comparador_previa.py:64-109`); cualquier motivo ⇒ `revisar`. La respuesta se guarda con sus líneas enteras.
- sigrid-api (`azure-apps/sigrid_api.md` §8.6, hacia `:1040`): `lineas[]` con `cantidad` y `precio` y nada más,
  `extra="forbid"` ⇒ hoy un `dto` daría 400 sin código ⇒ `error`.
- `dcapro` (`azure-apps/sigrid_tablas.md:7742`): `pre` «Precio», `tar` «P.Bruto», `dto` «Descuentos» (texto de 24),
  `tot` «Importe Línea». Qué columna recibe el bruto es de sigrid-api (su F-018 dice `pre`; nuestra caché de contrato
  lee `ctrpro.tar` como `precio_bruto`, `sigrid_api_contrato_client.py:88`): no lo decidimos aquí.
- Panel de sv4 (`_alta_sigrid.html:84-110`, `alta_sigrid_models.py:423-453`): Producto, Partida, Cantidad, Precio,
  Total previa; sin descuento.

## 3. Medición en producción (spec-author, 2026-10-28, PostgreSQL de Azure con `default_transaction_read_only=on`)

| Lectura | Resultado |
|---|---|
| Líneas con importe ≠ 0 por `descuento_albaran_aplicado` | nulo 319 (109 docs); en (0,100) con ≤ 2 decimales 100 (39 docs); **0** cero, negativos, ≥ 100 o > 2 decimales |
| Con d > 0 por proveedor | FEYMACO 42 (d 40; **9 vinculadas**), IBERFERRETERIA 28 (45), CECOIS 22 (7), RONDÓN 4 (10–30), TEYMO 4 (42) |
| Sin vincular con d > 0 (91) | **82** P exacto al céntimo con Qs; 2 a 1–2 céntimos; 7 no cuadran (> 0,02: los para F-106 R17); Qs = Q en todas |
| Vinculadas con d > 0 (9, FEYMACO) | 9 exactas; `ctrpro` con `tar` = `pre` (4500, 1000, 3000), **`dto` vacío** y P ≠ precio del contrato |
| `albaran_contrato_lines_merge.descuentos` | **nulo en las 3198** líneas: albaranes no conoce el `dto` del contrato |
| Altas con alguna línea d > 0 | 11 `registrado` real y 1 `ya_en_sigrid` (todas mandadas en neto) |
| CECOIS registrados (4 altas) | A 26018351: 12 × 0,645 −7 % = 7,20 ⇒ se mandó 0,60; A 26018267: 151,20 −7 % = 140,62 ⇒ 140,62; A 26018058: 6 × 8,826 −7 % = 49,25 ⇒ 8,208333 |

Conclusiones: el despeje puro enseñaría en Sigrid 0,645161 donde la plataforma dice 0,645 (D1); validar el `dto`
contra el `ctrpro` sin más rechazaría las 9 vinculadas de FEYMACO (D3); no hay descuentos raros que tratar (D6).

## 4. Contrato SUPUESTO con sigrid-api (F-018; a confirmar en la T18)

- **Petición**: `lineas[].dto?`, número, `0 < dto < 100` (albaranes nunca manda 0 ni 100), 2 decimales, sin cascada.
  Ausente ⇒ todo como hoy. Con `dto`, `precio` es el unitario **sin** descuento.
- **Escritura**: el bruto, el `dto` (texto, p. ej. «7») y `tot` = `cantidad × precio × (1 − dto/100)` con el redondeo
  de la UI de Sigrid; el reparto entre `pre` y `tar`, `impbru`/`totbas`, `mov`/PMP y `canser` los mide y decide sigrid-api.
- **Previa**: cada línea devuelve `dto` (número, o nulo si no lo aplica) y su `total` ya descontado.
- **Vinculadas**: si el precio cuadra con el del `ctrpro` (su H14 C), validan el `dto` de la línea contra el del
  `ctrpro`; si no cuadra, aceptan el de la línea (§3: FEYMACO). Lo que hagan al no coincidir (400 con código o aviso)
  se mapea en la T18.
- **Pendiente de la forma final (PARADA 1)**: nombre y tipo de `dto` en petición y previa, rango exacto, códigos nuevos,
  decimales con que Sigrid guarda el precio y redondeo de `tot`.

## 5. Regla de la línea a Sigrid (R1–R4)

| Línea | Guarda apagada | Guarda encendida |
|---|---|---|
| d nulo, 0 o inválido | como hoy (F-106 R2) | como hoy, sin `dto` |
| d aplicable y `Qs × round(P, 6) × (1 − dto)` = I al céntimo | como hoy (neto) | `precio = round(P, 6)`, `dto = round(d, 2)` |
| d aplicable y no da I al céntimo | como hoy (neto) | `precio = unitario_despejado(I, Qs, dto)`, `dto` |
| d 100 % o no despejable | como hoy | `None` ⇒ `linea_no_cuadra` (R8) |

`dto` se redondea antes de calcular el precio, así Sigrid y la plataforma usan el mismo. Casos de R22 en una tabla
`services/albaranes-comun/tests/f110_casos.json` que leen el test de comun y el de JS (R16).

## 6. Ficheros a modificar

| Fichero | Cambio |
|---|---|
| `services/albaranes-comun/ruesma_comun/alta_sigrid.py` | `LineaASigrid` (dataclass congelada: `cantidad`, `precio`, `dto`); `linea_a_sigrid` con `precio`, `descuento`, `con_descuento` (R1–R4); `LITERAL_ENVIAR_DTO = "true"` y `enviar_dto_activo(valor) -> bool` (R5, R14). |
| `services/albaranes-comun/pyproject.toml`, `ruesma_comun/__init__.py` | versión menor siguiente. |
| `services/albaranes-alta-sigrid/config/settings.py` | `alta_sigrid_enviar_dto: str` (alias `ALTA_SIGRID_ENVIAR_DTO`, defecto `"false"`) y propiedad `enviar_dto` con `enviar_dto_activo`. |
| `services/albaranes-alta-sigrid/interface_adapters/composition.py` | `ConfigAlta(mapeo=..., enviar_dto=settings.enviar_dto)` (`:59`); log de arranque con la guarda. |
| `services/albaranes-alta-sigrid/domain/services/validador_alta.py` | `ConfigAlta.enviar_dto: bool = False`; `_linea_peticion` con `LineaASigrid` y `dto`; R8 en `_motivos_lineas` tras el de F-106; docstring del módulo (`:29-30`). |
| `services/albaranes-alta-sigrid/domain/models/alta_models.py` | `LineaPeticion.dto: float \| None = None`, en `a_dict` tras `precio` (R7, R10). |
| `services/albaranes-alta-sigrid/domain/services/comparador_previa.py` | `dto_distinto` (R11, R12), en `Decimal` desde su texto como los importes. |
| `services/albaranes-alta-sigrid/domain/services/clasificador.py` | solo en la T19, si el contrato trae códigos (R13). |
| script de F-106 R18 (`services/albaranes-alta-sigrid/scripts/listar_altas_descuadradas_f106.py`) | comparación con `dto` (R19). |
| `services/albaranes-alta-sigrid/.env.example`, `sv9.md` | la variable y la regla (R20, R21). |
| `services/albaranes-front/config/settings.py` | `ALTA_SIGRID_ENVIAR_DTO` con `enviar_dto_activo` (R14). |
| la vista «A Sigrid» que deje F-106 (sv4: `review_repository.py`, modelos de vista) | `linea_a_sigrid(..., con_descuento=guarda)`; texto con «−7 %» y visibilidad de R15. |
| `services/albaranes-front/templates/document_detail.html` | `data-alta-dto` y los datos de la fila que use `precioASigrid` (R15, R16). |
| `services/albaranes-front/static/app.js` | `precioASigrid` con la regla de §5 (R15). |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | `lineas` con `dto` y `dto_sigrid`; `TEXTOS_MOTIVO_ALTA["dto_distinto"]` (R17, R18). |
| `services/albaranes-front/templates/_alta_sigrid.html` | columna «Dto %» (R17). |
| `infra/00_capps_vars.ps1`, `infra/set_alta_sigrid.ps1` | variable en `AltaSigridEnvComun` y relectura (R20); UTF-8 con BOM y CRLF. |
| `docs/ARCHITECTURE.md` | regla 19: viñeta «Precio y descuento a Sigrid (F-110)» (R21). |
| `azure-apps/albaranes.md` (otro repo; commit local, sin push) | variable y consumo `lineas[].dto` (R21). |

**A crear**: `services/albaranes-comun/tests/test_f110_linea_a_sigrid.py` y `tests/f110_casos.json`; sv9
`tests/test_f110_{peticion,previa,config,infra,script}.py`; sv4 `tests/test_f110_{ficha,js,panel}.py`.

## 7. Ficheros que NO se tocan

sv6 entero (P, d e I los deja como están: F-110 no cambia la valoración ni la regla 13), sv3, sv5, colas y mensajes.
`importes.py` (se reutilizan `clasificar_descuento`, `importe_de_linea`, `unitario_despejado`, `difieren` y la
`cuadra_linea` de F-106). La previa como paso (orden, tolerancia 0,05, `importe_distinto`), `sigrid_api_alta_client.py`
(serializa `a_dict` tal cual), `CODIGOS_CABECERA`, la grabación y el adjunto. `azure-apps/sigrid_api.md`.
`create_capps_sv9.ps1` y `create_capps_sv4.ps1` (crean sin la variable ⇒ apagada).

## 8. Clases y funciones

**comun · `alta_sigrid`** (dominio puro):
- `LineaASigrid(cantidad: float, precio: float, dto: float | None)`.
- `linea_a_sigrid(*, vinculada, cantidad_albaran, cantidad_convertida, importe, precio=None, descuento=None,
  con_descuento=False) -> LineaASigrid | None`: §5. Los llamantes de F-106 (sv9 `_linea_peticion`, la vista de sv4,
  el script R18) pasan a leer `.cantidad` y `.precio`; con los valores por defecto el resultado es el de F-106.
- `enviar_dto_activo(valor: str | None) -> bool`: `valor == LITERAL_ENVIAR_DTO` (sin `strip` ni mayúsculas, como
  `ALTA_SIGRID_COMMIT`).

**sv9**: `_linea_peticion(linea, datos, config)` llama a `linea_a_sigrid(..., precio=linea.precio_unitario_final,
descuento=linea.descuento_albaran_aplicado, con_descuento=config.enviar_dto)` (nombres de F-106) y pone `dto`;
`_motivos_lineas` añade R8 con `cuadra_linea` sobre la línea a Sigrid si lleva `dto`; `comparar(...)` añade
`_dto_distinto(pedida, devuelta) -> Motivo | None` para las pedidas con `dto`.

**sv4**: la vista de F-106 R15 recibe la guarda de `Settings` como hoy recibe el mapeo de producto; `precioASigrid
(q, p, d, importe, conDto)` en JS replica §5 (redondeo a céntimos con `Math.round(x * 100) / 100`, como
`importeDeFila`).

## 9. SQL

Sin DDL ni escrituras. Lectura nueva solo en la T20 (MANUAL del líder, solo lectura): altas reales `registrado` con
alguna línea d > 0 mandada sin `dto`:

```sql
SELECT a.document_id, m.proveedor_nombre, m.numero_albaran, a.sigrid_cod, COUNT(*) AS lineas_con_dto
FROM albaran_altas_sigrid a
JOIN albaran_documents_merge m ON m.id = a.document_id
JOIN albaran_valuations v ON v.document_id = a.document_id
JOIN albaran_line_valuations lv ON lv.valuation_id = v.id
WHERE a.estado = 'registrado' AND a.modo = 'real'
  AND lv.descuento_albaran_aplicado > 0 AND COALESCE(lv.importe_calculado, 0) <> 0
  AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(a.peticion_json::jsonb -> 'lineas') e
                  WHERE e ->> 'referencia_linea' = lv.id::text AND e ? 'dto')
GROUP BY 1, 2, 3, 4 ORDER BY 3;
```

## 10. Decisiones (PARADA 1; recomendada la (a) en todas)

- **D0 · F-095.** (a) F-095 («Alta con el precio BRUTO y el % de descuento», Óscar Domingo, 22-10) es el mismo
  problema: queda absorbida por F-110 (lo marca el líder). (b) Se mantienen las dos.
- **D1 · Qué precio se manda con `dto`.** (a) P si da I al céntimo con Qs; si no, el despejado (§5): Sigrid enseña
  lo de la plataforma en 91 de 100 líneas (§3) y su importe es siempre I. (b) Siempre P: en 2 de 91 Sigrid calcularía
  1–2 céntimos distintos del albarán. (c) Siempre el despejado: 0,645161 en vez de 0,645.
- **D2 · Guarda.** (a) `ALTA_SIGRID_ENVIAR_DTO`, literal `true`, mismo valor en sv4 y sv9 (`AltaSigridEnvComun`),
  apagada por defecto; apagarla es la vuelta atrás. (b) Solo en sv9: la ficha no sabría qué se mandará.
- **D3 · Vinculadas.** (a) Misma regla; sv9 no valida contra el `ctrpro` (no tiene su `dto`, §3) y pide a sigrid-api
  que valide solo cuando el precio cuadre con el contrato (H14 C); la previa (R11) detecta lo que Sigrid no aplique.
  (b) Vinculadas sin `dto` (neto, como hoy): las 9 de FEYMACO seguirían mal. (c) Validar en sv9: imposible sin caché.
- **D4 · Previa sin `dto`.** (a) Pedido con `dto` y la previa no lo trae ⇒ `dto_distinto` (`revisar`): la guarda solo
  se enciende con el contrato desplegado, así que su ausencia es un fallo. (b) Solo si lo trae y difiere.
- **D5 · Altas ya grabadas en neto (11).** (a) No se reenvían: el importe es correcto; el líder las lista (T20) y el
  humano decide si las corrige a mano en Sigrid. (b) No se listan.
- **D6 · Descuentos raros.** (a) Inválidos (≤ 0, > 100, ilegibles) como hoy, sin `dto` (`factor_descuento` ya los
  ignora; 0 en producción); con más de 2 decimales, `round(d, 2)`. (b) Motivo nuevo `no_admitido`.
- **D7 · `importe` por línea a sigrid-api.** (a) No se pide: con D1 Sigrid calcula I y la previa lo vigila (0,05 €).
  (b) Pedir `lineas[].importe?` para que `tot` sea el nuestro sin recalcular.

**Para que el líder lo traslade a sigrid-api** (no lo hace este agente): las 9 vinculadas de FEYMACO (D3), D1 (precio
a 6 decimales: ¿con cuántos lo guarda Sigrid?), D4 (que la previa devuelva `dto`) y la duda `pre`/`tar` de §2.

## 11. Riesgos

- **R-1 · Contrato distinto del supuesto.** Mitigación: guarda apagada, T18 antes de encenderla, R24 (parar).
- **R-2 · Redondeo de Sigrid.** Si redondea `tot` o `pre` distinto, la previa da `importe_distinto` (`revisar`), no
  graba: se ve en la T22 y se ajusta.
- **R-3 · sv4 y sv9 con distinto valor.** Solo afecta al «A Sigrid» previo, nunca al dinero; `set_alta_sigrid.ps1`
  relee las dos y avisa.
- **R-4 · Choque con F-106.** Nombres que F-106 fije distintos de los de su spec: la T0 los lee y se ajusta el diseño
  sin cambiar R; si cambia una R de F-106, se para.
- **R-5 · Precio despejado con Qs grande** (como F-106 R-6): `no_admitido` por R8, nunca un importe distinto.
- **R-6 · Se aplica a todos los proveedores con descuento**, no solo a CECOIS (FEYMACO, IBERFERRETERIA, RONDÓN, TEYMO).

## 12. Despliegue y activación (lo lanza el humano)

1. comun ⇒ sv9 → sv4 con la guarda apagada (`.\deploy.ps1 -Only sv9,sv4`; `.\check_deploy.ps1`): nada cambia.
2. sigrid-api publica y despliega F-018; el líder hace la T18 (y la T19 si hace falta, con su redespliegue).
3. Humano: `ALTA_SIGRID_ENVIAR_DTO = "true"` en `infra/00_capps_vars.ps1` y `.\set_alta_sigrid.ps1` (sv4 y sv9).
4. Primera alta real con descuento ⇒ T22. Vuelta atrás: `"false"` y `.\set_alta_sigrid.ps1`.

## 13. Encaje con F-106

F-106 garantiza que la fila cuadra al aprobar (R16) y al dar de alta (R17) y deja «a Sigrid» en un único sitio (R2);
F-110 solo cambia ese sitio, añade la guarda, el `dto` a la petición, su comprobación a Sigrid (R8) y a la previa
(R11), y lo enseña donde F-106 ya enseña lo que se manda (R15) y en el panel. Sin F-106 en `dev`, F-110 no empieza.
