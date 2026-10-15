# F-064 · IA1 e IA2 ignoran al cliente y la IA2 confirma el proveedor — diseño

## 1. Encaje

El proveedor lo decide la IA y lo verifican las reglas (memoria «clasificacion-la-decide-la-ia», criterio de
F-055). F-064 actúa en la IA (sv2: prompt de IA1 y checklist de IA2); la verificación ya existe en sv3
(F-002/F-062 red por CIF, F-063 descarte del CIF propio) y no cambia. La lista de empresas del cliente es la
de F-063 (`ruesma_comun.proveedores`): una sola fuente para el prompt y para el descarte.

```
CIFS_PROPIOS_POR_DEFECTO + CIFS_PROPIOS ──► sv2: {empresas_cliente} en el task de fase 1
                                                 ├─► IA1 (instructions de fase 1)
                                                 └─► IA2 (dentro de {prompt_fase_1}) + regla proveedor_emisor ({revision_rules})
                                        └──► sv3: descarte F-063 (sin cambios)
```

Límite de servicio: todo cabe en sv2 (prompt y su montaje). Sin responsabilidad nueva ni servicio nuevo.

## 2. Ficheros a crear

- `services/albaranes-api/application/services/empresas_cliente.py` (application, puro, importa solo
  `ruesma_comun.proveedores`):
  - `MARCADOR_EMPRESAS_CLIENTE = "{empresas_cliente}"`.
  - `@dataclass(frozen=True) EmpresaCliente(cif: str, razon_social: str | None)`.
  - `empresas_cliente(extra: str | None = None) -> tuple[EmpresaCliente, ...]`: las de
    `CIFS_PROPIOS_POR_DEFECTO` en su orden, con su razón social; después las de `cifs_propios(extra)` que no
    son de serie, ordenadas, con `razon_social=None` (R1, R3). Lee el diccionario en cada llamada (R4).
  - `render_empresas_cliente(empresas) -> str`: cabecera fija `EMPRESAS DEL CLIENTE (CIF — razón social):`
    y una línea `  - <cif> — <razón social o «empresa del grupo, sin razón social configurada»>` (R3).
- Tests de sv2 (raíz `services/albaranes-api`): `tests/test_f064_empresas_cliente.py` (R1–R4),
  `tests/test_f064_prompt_ia1_proveedor.py` (R5–R8), `tests/test_f064_prompt_ia2_proveedor.py` (R9–R12).
  Patrón: doble de cliente de visión que captura las instructions (`test_f051_prompt_partida.py`).
- `evals/procesos/sv2_proveedor.py` y `evals/comparar_proveedor.py` (§6) y `tests/test_f064_comparar_
  proveedor.py` (raíz, R14–R17, sin red ni LLM: `extraer` doble).

## 3. Ficheros a modificar

- `services/albaranes-api/config/prompts.yaml`, clave `albaran_factura_es`: SOLO las viñetas
  `proveedor_nombre` y `proveedor_cif` (hoy líneas 41–51), sustituidas por el texto de §4 (R5, R8).
- `services/albaranes-api/config/revision_rules.yaml`: regla nueva `proveedor_emisor` tras
  `unidad_medida_camion`, antes de la plantilla comentada (§5, R9).
- `services/albaranes-api/application/services/albaran_extraction_service.py`:
  - `__init__(..., empresas_cliente: Sequence[EmpresaCliente] | None = None)`; `None` ⇒
    `empresas_cliente(None)` (R2).
  - `_render_task_fase_1`: tras el catálogo de familias y antes de `_render_contexto_correo`, si el marcador
    está, `task.replace(MARCADOR_EMPRESAS_CLIENTE, render_empresas_cliente(...))`; si no está, nada (R6, R7).
    Como IA2 recibe el task de fase 1 renderizado por esta misma función, el bloque le llega sin más (R10).
- `services/albaranes-api/config/settings.py`: `cifs_propios: str = Field("", alias="CIFS_PROPIOS")`, con
  comentario «igual que en sv3» (sv2 no tiene `.env.example`: la variable se documenta aquí y en la regla 18).
- `services/albaranes-api/interface_adapters/composition.py` y `interface_adapters/api/app.py`: pasar
  `empresas_cliente=empresas_cliente(settings.cifs_propios)` al servicio (R2).
- `harness/rutas_sensibles.json`: `propios.py` de comun y `empresas_cliente.py` de sv2 (R18).
- `docs/ARCHITECTURE.md`, regla 18: viñeta «Prompts (F-064)» con el flujo de §1, R9 y R12.

## 4. Texto de IA1 (literal propuesto, `albaran_factura_es`)

```
    - proveedor_nombre: RAZÓN SOCIAL del EMISOR del albarán (la empresa que
      lo emite y suministra), tal y como aparece en su BLOQUE FISCAL, es
      decir, el nombre que acompaña a su CIF/NIF (suele llevar la forma
      jurídica: S.L., S.A., S.L.U., S. Coop., etc.). La marca comercial o el
      nombre del grupo que aparece en el LOGOTIPO NO es el proveedor: si el
      logotipo y el bloque fiscal dicen cosas distintas, manda SIEMPRE el
      bloque fiscal. Si no identificas al emisor, null.
    - proveedor_cif: CIF/NIF/NIE del EMISOR según formato español. Está en
      su membrete, junto a su razón social o en el pie del documento (la
      inscripción en el Registro Mercantil suele acabar con su C.I.F.).
      Devuélvelo sin espacios, guiones, puntos ni barras (A-28/733558 ⇒
      A28733558). Si el documento no trae el CIF del emisor, null.
    - El CLIENTE no es el proveedor. Estas son las empresas del cliente
      (nosotros, la constructora que recibe el albarán):

      {empresas_cliente}

      Aparecen en las casillas del cliente ("Cliente", "Nº cliente",
      "Empresa", "Destinatario", "Facturar a" y su "C.I.F./D.N.I."), con la
      razón social completa o abreviada y con o sin forma jurídica. NUNCA
      devuelvas su nombre en proveedor_nombre ni su CIF en proveedor_cif,
      aunque sea el único CIF que veas o esté en una casilla rotulada CIF:
      ignóralos y busca los del emisor. Si el único CIF del documento es de
      una empresa del cliente, proveedor_cif es null.
```

Sale la frase escrita a mano («Construcciones Ruesma, cuyo CIF es A81873903, somos nosotros…») y la de
«Busca el código por un campo que ponga CIF o NIF o NIE» (la trampa de FEYMACO). Los tests fijan las frases
clave, no el párrafo entero (el reviewer contrasta el literal con esta sección).

## 5. Regla de IA2 (literal propuesto, `revision_rules.yaml`)

La viñeta «Si no puedes leer con seguridad al emisor…» es la O1 de `progress/review_F-064.md`, aprobada por el
humano el 2026-10-15 (en la duda, IA2 no reescribe un proveedor correcto de fase 1).

```
  - id: proveedor_emisor
    titulo: El proveedor es el EMISOR del albarán, nunca una empresa del cliente
    descripcion: |
      Confirma SIEMPRE el proveedor de la fase 1, sea cual sea la familia del
      albarán: compara cabecera.proveedor_nombre y cabecera.proveedor_cif con
      el documento.
      - El proveedor es la empresa que EMITE el albarán: su membrete, su
        bloque fiscal o el pie con la inscripción en el Registro Mercantil.
      - Las EMPRESAS DEL CLIENTE que listan las reglas de la fase 1 somos
        nosotros y nunca son el proveedor. Esta regla prevalece sobre
        cualquier otra de la cabecera, también sobre el contexto del ERP
        Sigrid aunque dé ese CIF por validado.
      Acción:
        - Si el nombre o el CIF de fase 1 son de una empresa del cliente, o no
          son los del emisor, corrígelos con los del emisor leídos en el
          documento. Si el CIF del emisor no aparece, deja proveedor_cif en
          null: el sistema buscará el proveedor por su nombre.
        - Si no puedes leer con seguridad al emisor, conserva lo de fase 1,
          salvo que sea una empresa del cliente: entonces deja proveedor_cif
          en null.
        - Si son correctos, cópialos tal cual y no añadas razonamiento.
        - Cada cambio lleva su razonamiento con campo "cabecera.proveedor_cif"
          o "cabecera.proveedor_nombre" y patron_aplicado "proveedor_emisor".
    ejemplo: |
      Fase 1 trae como proveedor_cif el CIF de la casilla C.I.F./D.N.I. del
      bloque del cliente (una empresa del cliente). El pie dice «Inscrita en el
      Registro Mercantil … C.I.F. A-28/733558» ⇒ proveedor_cif "A28733558" y
      razonamiento «el CIF de fase 1 es del cliente; el del emisor está en el
      pie».
```

## 6. Evals: `evals/comparar_proveedor.py`

Por qué existe: el banco no mide el CIF (requirements, «Evals»). Mismo esquema que `comparar_obra` (F-048),
sin sigrid-api ni correo, pero con las DOS fases y los DOS YAML.

- `procesos/sv2_proveedor.py` (sv2 se importa solo dentro de funciones): `ficheros_de_base(directorio, base)`
  saca con `git show <base>:…` `prompts.yaml` y `revision_rules.yaml`; `montar_servicio(prompts, reglas,
  especificaciones)` (sin `obras_activas_provider`, como el runner); `montar_extractor(...)` devuelve
  `extraer(variante, caso_id, ruta, tipologia) -> {"ia1": {nombre, cif}, "ia2": {nombre, cif}}`, fase 1 con
  `IA_PRIMERA_FASE` y fase 2 con `IA_SEGUNDA_FASE`, prompt de fase 2 con `sv2_extraccion.prompt_de_fase_2`.
  Reutiliza `_especificacion`, `_adjuntos` y `ruta_de_albaran` de `sv2_extraccion`.
- `comparar_proveedor.py`: CLI `--casos` (defecto: los 19 de §7), `--repeticiones 3`, `--variante
  base|rama|ambas`, `--base dev`, `--albaranes`, `--salida`, `--resumen progress/comparar_proveedor_F-064.md`.
  Puras y testeadas: `clasificar_cif(cif, esperado, propios)` (con `normalizar_cif`/`es_cif_propio`),
  `mayoritaria(categorias)` (empate ⇒ `inestable`), `veredicto(...)` (C1–C3), `render_resumen` (sin CIF ni
  nombres). Paradas con código 2 antes del LLM (R17). Esperado: `evals/fixtures/final/<caso>.json`
  (`datos_generales[0].cif`); tipología: `evals/fixtures/IA1/<caso>.json`.
- Variante `base` = código de la rama + YAML de la base: como la base no trae `{empresas_cliente}`, R7 hace
  que lo que recibe el LLM sea lo de `dev` (el schema no cambia: no hace falta recortar como en F-048).

## 7. Plan de evals y criterio (MANUAL del humano)

**Casos con el cliente impreso** (comprobado el 2026-10-08 en `evals/inputs/albaranes/` del árbol principal):
FER-001…003 (FEYMACO, el formato del incidente: CIF del cliente en «C.I.E./D.N.I.», el de FEYMACO solo en el
pie; escaneados, vistos FER-001 y FER-003) y HOR-005…011 y MOR-003 (HORPRESOL, con capa de texto: nombre y CIF
de Ruesma en el PDF). **Controles**: ALQ-001, COM-001, GEN-002, GEN-004, GEN-010, HOR-012, RES-001, RES-010.

Criterios (por caso, categoría mayoritaria de 3 repeticiones):
- **C1** · en la rama, 0 ejecuciones con CIF `cliente` tras IA2 en los 19 casos; tras IA1, ≤ base.
- **C2** · casos con mayoría `emisor`: rama ≥ base, tras IA1 y tras IA2.
- **C3** · ningún caso con mayoría `emisor` en base la pierde en la rama (ni tras IA1 ni tras IA2).
- **Puerta** (`python -m evals.runner --con-llm --feature F-064`): IA1 ≤ 154 fallos críticos e IA2 ≤ 4 (base:
  147 y 2 de `evals_F-051.md`, commit `6b332e0`, con los mismos prompts y fixtures que `dev`; +5 % de ruido en
  IA1). IA3, IA4 y E2E no dependen de sv2 (salen de `fixtures/inputs`): se anotan, no se juzgan.
- Si la base no da ningún `cliente` en los 11, el banco no reproduce el incidente: C1 no prueba nada y se
  añade el albarán real (Q4 del informe).

Coste: comparador 19 × 2 fases × 2 variantes × 3 = **228 llamadas** (114 de IA1 y 114 de IA2); puerta ≈ 59 × 2
de sv2 + 59 de IA3 + ~13 de IA4 ≈ **190**. Sin cifra en euros en el repositorio: la da la consola del proveedor.

## 8. Encaje con F-049, F-051 y F-055

- **F-051** (en `dev`): sección «Código de imputación manuscrito» de IA1. F-064 no la toca.
- **F-049** (`blocked`, rama propia): cambia la viñeta `obra_codigo` de IA1, el encabezado y el párrafo que
  preceden a `{sigrid_context}` en los cuatro prompts de fase 2, `review_phase_2` y `_render_sigrid_context`
  (que mueve a `contexto_sigrid_fase2.render_cabecera`). F-064 no toca nada de eso: sus cambios de IA1 acaban
  en `proveedor_cif` y dejan intactas `fecha`, `numero_albaran` y `forma_pago` entre medias; IA2 se instruye
  por `revision_rules.yaml`. Solo comparten `composition.py` (una línea de argumento: conflicto trivial).
- **F-055** (`pending`): reutilizará `ContextoSigridFase2` de F-049 para dar a IA2 los proveedores con
  contrato en la obra. Contrato que F-064 le deja: (1) la regla `proveedor_emisor` prevalece sobre ese
  contexto; (2) la cabecera que prepare (hoy `header-grounding` de sv3) debe excluir los CIF propios, de
  validados y de candidatos (`es_cif_propio`), o contradirá a la regla; (3) el campo de salida es el mismo
  (`documento_revisado.cabecera`), y `origen_datos.proveedor`, si hace falta, lo define F-055.

## 9. Ficheros que NO se tocan

Los cuatro prompts `albaran_revision_fase2_*`; el resto de `albaran_factura_es`; `review_phase_2`,
`_MARCADORES_FASE_2` y `_render_sigrid_context`; `extraction_worker.py` y `phase_merge.py`; los schemas de
`domain/models/`; `config/prompts/svc2_prompt_albaran_factura_es.yaml` (no se carga, ver `spec_F-051.md`);
`ruesma_comun` entero (incluido `propios.py`); todo sv3; `evals/comparar_obra.py` y `procesos/sv2_obra.py`;
`azure-apps/` (variable opcional sin valor, como en F-063).

## 10. Decisiones y riesgos

- **D1 · Sin campo nuevo** (R11). IA2 corrige en `documento_revisado.cabecera` y deja rastro en
  `razonamientos` (`patron_aplicado=proveedor_emisor`, viaja en `debug.phase_2`). Descartadas: (B) campo
  `proveedor_verificacion` en `RevisionAlbaranFase2` (schema que se manda a 3 proveedores LLM por poco más
  que un log) y (C) `origen_datos.proveedor` (contrato con sv3, orden de despliegue sv3→sv2 y sin consumidor
  hasta F-055).
- **D2 · sv2 no filtra** (R12). Un `if` en sv2 borraría la señal de F-063 (`proveedor_cif_propio:`), que es la
  métrica de producción de F-064; y la regla del humano es que decida la IA.
- **D3 · IA2 por la checklist**. Una regla en `revision_rules.yaml` llega a los cuatro prompts de fase 2 sin
  editarlos (cero choque con F-049, una sola copia del texto). La lista llega por `{prompt_fase_1}`: no hace
  falta un marcador en fase 2.
- **D4 · Sin marcador, nada** (R7). Al revés que el catálogo (que se añade al final): la variante `base`
  necesita reproducir `dev` byte a byte, y el YAML real siempre lo lleva (test de R5).
- **D5 · `ruesma_comun` no cambia**. La razón social de serie sigue «Construcciones Ruesma» (sin «S.A.»):
  cambiarla altera la nota de F-063; las variantes («CNES. RUESMA, S.A.» en FEYMACO) las cubre el texto
  genérico de §4. Sin cambio en comun no hay que reconstruir sv3, sv5 ni sv6.
- **D6 · `CIFS_PROPIOS` también en sv2**. Mismo nombre y misma regla; si algún día se usa, hay que ponerla
  igual en las dos Container Apps. La vía recomendada para añadir una empresa del grupo es una entrada en
  `CIFS_PROPIOS_POR_DEFECTO` con su razón social (código, reconstruir sv2 y sv3).
- **D7 · CIF normalizado en la salida de IA1** (R8). sv3 ya normaliza; ayuda a la comparación y a los logs.
  Riesgo: cambiar el formato de los CIF de todos los albaranes; lo mide C2/C3.
- **Riesgo · exceso de celo**: que la IA deje `null` CIF del emisor que hoy acierta. Lo vigila C3; en
  producción, sv3 lo resuelve por nombre dentro de la obra (F-062/F-063).
- **Despliegue**: solo sv2, sin orden (ni schema ni comun). Vuelta atrás: la revisión anterior de sv2.
