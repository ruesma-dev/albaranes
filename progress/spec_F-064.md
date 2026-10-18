# F-064 · informe del spec-author

Spec en `specs/F-064-proveedor-en-prompts/` (requirements 132/150, design 205/250, tasks 13 tareas). Rama
`feature/F-064-proveedor-en-prompts`, worktree `../albaranes-F-064`, desde `dev` `544113b` (trae F-062 y
F-063). Solo lectura de código; sin `.env`, sin sigrid-api, Azure ni BBDD; sin evals con LLM. F-064 dada de
alta en `harness/features.json` como `spec_ready` (id libre: comprobado en `albaranes-F-049`, `-F-053` y el
árbol principal) y `BACKLOG.md` regenerado.

## 1. Qué hay hoy

- **IA1** (`config/prompts.yaml`, `albaran_factura_es`, únicas viñetas del proveedor en líneas 41–51): ya
  dice a mano «Construcciones Ruesma, cuyo CIF es A81873903, somos nosotros la constructora: ignóralo», pero
  solo en la viñeta del NOMBRE; la del CIF dice «Busca el código por un campo que ponga CIF o NIF o NIE».
- **IA2** (cuatro `albaran_revision_fase2_*`): no tiene instrucción propia sobre el proveedor; solo el bloque
  `{sigrid_context}`, que en producción es `GroundingNulo` (nota «no disponible»). Recibe el task de IA1 ya
  renderizado dentro de `{prompt_fase_1}` (`_render_task_fase_1`, un solo sitio) y la checklist de
  `revision_rules.yaml` (2 reglas activas) dentro de `{revision_rules}`.
- **Salida**: el envelope final es el `documento_revisado` de IA2 (`phase_merge`); sv3 lee
  `cabecera.proveedor_cif/proveedor_nombre` y aplica F-063 (descarte del CIF propio, motivo
  `proveedor_cif_propio:`) y F-062/F-002 (red por CIF; sin CIF, por nombre dentro de la obra).
- **Lista de CIF propios** (F-063): `ruesma_comun.proveedores` (`CIFS_PROPIOS_POR_DEFECTO` = {A81873903:
  «Construcciones Ruesma»}, `cifs_propios(extra)`, `es_cif_propio`); `CIFS_PROPIOS` solo en sv3.
- `config/prompts/svc2_prompt_albaran_factura_es.yaml` no lo carga nadie (ya lo dijo `spec_F-051.md`).

## 2. Hallazgos

1. **La trampa está en el propio prompt.** En los albaranes de FEYMACO del banco (vistos FER-001 y FER-003,
   el mismo formato que el incidente) la única casilla rotulada «C.I.E./D.N.I.» es la del cliente («CNES.
   RUESMA, S.A.», A81873903) y el CIF del emisor solo está en el pie («Inscrita en el Registro Mercantil …
   C.I.F. A-28/733558»). La viñeta del CIF manda a la IA justo a la casilla equivocada; la frase de Ruesma, en
   la viñeta del nombre, no la contrarresta. El cliente aparece abreviado («CNES.»): el texto nuevo cubre las
   variantes de forma genérica.
2. **El banco no mide el CIF.** `proveedor_cif` = `NO_COMPARAR` en los 60 casos de IA1; IA2 solo compara
   `contexto_linea`; en E2E `cif` sale como «no observable» (el E2E sale de `fixtures/inputs`, no de sv2). Por
   eso el plan de evals necesita un comparador propio (`evals/comparar_proveedor.py`, design §6).
3. **11 casos del banco llevan impreso al cliente con su CIF**: FER-001…003 (escaneados) y HOR-005…011 y
   MOR-003 (HORPRESOL, capa de texto con nombre y A81873903). Los otros 48 son escaneados sin capa de texto:
   no se ha comprobado si lo llevan. El CIF esperado de los 60 está en `fixtures/final` (`cif`).
4. **Base de la puerta disponible.** `evals_F-051.md` (commit `6b332e0`, 2026-10-06) se hizo con los mismos
   prompts, reglas, servicio de extracción y fixtures que `dev` hoy (diff vacío): IA1 147 fallos críticos, IA2
   2. Ese informe solo vive en `albaranes-F-051/progress/` (ignorado por git): **copiarlo antes de quitar ese
   worktree**.
5. **Riesgo latente para F-055.** Si se conecta el grounding de sv3 (`header-grounding`), A81873903 sale
   «VALIDADO POR CIF (no lo revises)» y el prompt manda a IA2 copiarlo. F-064 pone la regla nueva por encima
   («prevalece también sobre el contexto de Sigrid») y deja a F-055 el contrato de excluir los CIF propios
   (design §8).
6. **Sin choque con F-049 ni F-051.** F-049 toca `obra_codigo` de IA1, el encabezado ante `{sigrid_context}`
   de los cuatro prompts de fase 2, `review_phase_2` y `_render_sigrid_context`; F-051, el «Código de
   imputación manuscrito». F-064 solo toca las viñetas del proveedor (con tres viñetas intactas entre medias
   de la de F-049), `_render_task_fase_1` y `revision_rules.yaml`. Único fichero compartido con F-049:
   `composition.py` (una línea).
7. **Solo se despliega sv2.** Ni schema ni `ruesma_comun` cambian: sin orden de despliegue ni rebuild de los
   demás. Métrica de producción gratis: el motivo `proveedor_cif_propio:` de F-063 debería dejar de aparecer.

## 3. Preguntas cerradas con recomendación (a validar en la PARADA 1)

- **Q1 · ¿Cómo devuelve IA2 la confirmación?** Recomendado: **sin campo nuevo** (design D1): corrige en
  `documento_revisado.cabecera` y deja razonamiento `patron_aplicado=proveedor_emisor`; `origen_datos` no
  cambia. Alternativa: campo `proveedor_verificacion` (confirmado/corregido/anulado) en la respuesta de fase
  2, que cambia el schema de los 3 proveedores LLM por poco más que un log.
- **Q2 · ¿sv2 filtra el CIF del cliente con un `if`?** Recomendado: **no** (D2): borraría la señal de F-063 y
  la regla del humano es que decida la IA y las reglas verifiquen.
- **Q3 · ¿sv2 lee también `CIFS_PROPIOS`?** Recomendado: **sí**, mismo nombre y regla (D6); la vía buena para
  añadir una empresa del grupo es una entrada en `CIFS_PROPIOS_POR_DEFECTO` con su razón social.
- **Q4 · ¿Añadir al banco el albarán real del incidente** (FEYMACO 0694, merge `b1d3e179-…`) como FER-004?
  Recomendado: **sí, si lo tienes a mano** (fila en `RESULTADO_FINAL` con `cif` A28733558 y `python -m
  evals.conversor`), y obligatorio si la variante base no da ningún `cliente` (el banco no reproduciría el
  fallo). No bloquea empezar.
- **Q5 · ¿IA1 devuelve el CIF normalizado** (`A-28/733558` ⇒ `A28733558`)? Recomendado: **sí** (D7); sv3 ya
  normaliza y el comparador lo vigila.
- **Q6 · ¿Razón social de serie «Construcciones Ruesma, S.A.»?** Recomendado: **dejar «Construcciones
  Ruesma»** en comun (D5): cambiarla toca la nota de F-063 y obliga a reconstruir sv3; el texto genérico
  cubre las variantes.

## 4. Plan de implementación (PARADA 1)

1. T1: `application/services/empresas_cliente.py` en sv2 (lista desde `ruesma_comun.proveedores` + bloque).
2. T2: `CIFS_PROPIOS` en settings de sv2, argumento del servicio y sustitución de `{empresas_cliente}` en
   `_render_task_fase_1`, antes del correo; cableado en worker y API.
3. T3: IA1 — reescribir solo las viñetas `proveedor_nombre`/`proveedor_cif` (literal en design §4).
4. T4: IA2 — regla `proveedor_emisor` en `revision_rules.yaml` (literal en design §5); los cuatro prompts de
   fase 2 no se tocan.
5. T5: tests de contrato: schemas sin campos nuevos y envelope final sin filtro; sv3 intacto.
6. T6: `evals/comparar_proveedor.py` + `procesos/sv2_proveedor.py` (base = YAML de `dev` con el código de la
   rama), con tests sin LLM.
7. T7: `rutas_sensibles.json` (`propios.py` y el módulo nuevo) y `ARCHITECTURE.md` regla 18.
8. T8: cobertura ≥ 80 % y mutación. T11: `init.sh` en verde.
9. Humano: T9 comparador (≈ 228 llamadas) y T10 pasada completa (≈ 190); tras fusionar, T12 desplegar solo
   sv2 y vigilar.
Fuera: lista de proveedores de la obra para IA2 (F-055), `header-grounding`, comun, sv3, backfill.

## 5. MANUAL del humano (comandos exactos, PowerShell)

Entorno (solo nombres): `GEMINI_API_KEY` y `OPENAI_API_KEY` (o las de `IA_PRIMERA_FASE`/`IA_SEGUNDA_FASE` si
las cambias). Los albaranes del banco no están en el worktree (ignorados): el comparador los lee del árbol
principal con `--albaranes`; para el runner hay que copiarlos.

**T9 · comparador base/rama** (se factura ≈ 228 llamadas; tras T6 y T3–T4):
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-064
& C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe -m evals.comparar_proveedor --variante ambas --repeticiones 3 --base dev --albaranes C:\Users\pgris\PycharmProjects\albaranes\evals\inputs\albaranes
```
Criterio (design §7): C1, C2 y C3 en verde en `progress/comparar_proveedor_F-064.md`.

**T10 · pasada completa de la puerta** (se factura ≈ 190 llamadas):
```powershell
Copy-Item -Recurse C:\Users\pgris\PycharmProjects\albaranes\evals\inputs C:\Users\pgris\PycharmProjects\albaranes-F-064\evals\inputs
cd C:\Users\pgris\PycharmProjects\albaranes-F-064
& C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe -m evals.runner --con-llm --feature F-064
```
Criterio: en `progress/evals_F-064.md`, IA1 ≤ 154 e IA2 ≤ 4 fallos críticos (base 147 y 2 de `evals_F-051.md`).

**T12 · tras fusionar en `dev` e `init.sh` en verde: desplegar SOLO sv2 y vigilar.**
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
.\deploy.ps1 -Only sv2
.\check_deploy.ps1
```
Vigilancia, solo lectura contra la BBDD `albaranes` (la misma vía que las consultas de F-062):
```sql
SELECT m.id, m.numero_albaran, m.created_at_utc, m.obra_codigo, m.proveedor_nombre
FROM albaran_documents_merge m
WHERE m.is_active AND m.review_reasons_json LIKE '%proveedor_cif_propio:%'
  AND m.created_at_utc >= '<fecha-hora UTC del despliegue de sv2, ISO>'
ORDER BY m.created_at_utc DESC;
```
Criterio: 0 filas en una semana. Una fila = la IA volvió a leer el CIF del cliente (F-063 lo paró): volver a
la spec con ese albarán.
