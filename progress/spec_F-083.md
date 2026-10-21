<!-- progress/spec_F-083.md -->
# F-083 · Inventario de modelos y notas del spec-author

Anexo de `specs/F-083-comparar-modelos/`. Aquí está el **inventario con fuentes**; la tabla
`evals/precios_modelos.json` (T1) se rellena con estos valores y ninguno más. Consultado el
**2026-10-19**. Precios en **USD por millón de tokens**, nivel estándar y API directa del proveedor
(ni Batch, ni Bedrock/Vertex/Foundry).

## 1. Lo que corre hoy en producción (del código, no de memoria)

| Fase | Servicio | Proveedor y modelo | De dónde sale |
|---|---|---|---|
| IA1 | sv2 | gemini · `gemini-3.7-flash` | `infra/create_capps.ps1` (`IA_PRIMERA_FASE=gemini`, `GEMINI_MODEL`) |
| IA2 | sv2 | openai · `gpt-5.4` | `IA_SEGUNDA_FASE` sin fijar ⇒ `openai` (`services/albaranes-api/config/settings.py`), `OPENAI_MODEL` |
| IA3 | sv5 | claude · `claude-opus-4-8` | sv5 solo habilita Claude (`ENABLE_CLAUDE=true`, el resto `false` por defecto), `IA3_PROVIDER` sin fijar |
| IA4 | sv5 | claude · `claude-opus-4-8` | `IA4_PROVIDER` sin fijar ⇒ el primer proveedor habilitado |

`WORKER_CON_FASE2=false` en `create_capps.ps1` **no lo lee ningún código** (`grep` en `services/`): el
worker de sv2 ejecuta siempre la fase 2. Es una variable muerta; no se toca en F-083.

Los clientes de `ruesma_comun/llm/` **no envían** esfuerzo de razonamiento ni nivel de pensamiento:
cada modelo corre con el valor por defecto de su API. El de Claude fuerza la herramienta
(`tool_choice={"type":"tool"}`), `max_tokens=8192` y `timeout=120 s`.

### Tres hallazgos que condicionan la comparación

1. **`gemini-3.7-flash` está descontinuado y Google lo redirige a `gemini-3.8-flash`.** Página oficial
   del modelo (https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash, actualizada 2026-10-12):
   «`gemini-3.7-flash` is deprecated and has been replaced by Gemini 3.8 Flash» y «API requests to
   `gemini-3.7-flash` are automatically routed to `gemini-3.8-flash`». No da fecha. No aparece ya en
   la página de modelos (2026-10-13) ni en la de precios (2026-10-16). **IA1 en producción ya lee con
   3.8 Flash**, y a su precio (supuesto: la página no da precio de 3.7). Cambiar el nombre en `infra/`
   queda fuera de F-083; se avisa al humano.
2. **La línea base de F-075 probablemente no es la de producción.** El runner toma el modelo de
   `GEMINI_MODEL`/`OPENAI_MODEL` del entorno y, si no está, usa los de `MODELOS_POR_PROVEEDOR`
   (`gemini-2.5-flash`, `gpt-5`). El comando de T17 de F-075 no fijaba esas variables y el informe
   no registra el modelo. Además IA3, IA4 y E2E corrieron con **gemini** (por defecto del runner),
   mientras producción valora con **Claude**. Por eso F-083 mide la referencia de producción en la
   misma corrida y deja las cifras de F-075 (IA1 141, IA2 2, IA3 408, IA4 27, E2E 537) solo como
   referencia histórica.
3. **El cliente de Claude fuerza la herramienta, y tres modelos nuevos lo rechazan con 400**:
   `claude-opus-5-5`, `claude-sonnet-5-5` y `claude-fable-5-1` («tool_choice: type "tool" and "any"
   are not supported for this model»; guía de migración de Anthropic, secciones de Opus 5.5, Sonnet 5.5
   y Fable 5.1). Sin un cambio en comun no se pueden medir: pregunta P5 del design.

## 2. «Luna»

**Es la gama Luna de OpenAI** (Luna, Terra, Sol y Astra son niveles de las familias 5.6 y 6). La
página oficial de precios (https://developers.openai.com/api/docs/pricing) y la de modelos
(https://developers.openai.com/api/docs/models) traen dos: **`gpt-6-luna`** («Our most efficient
model for focused, high-volume tasks») y **`gpt-5.6-luna`** («cost-sensitive, high-volume workloads»,
el equivalente al antiguo *nano*). **No existe `gpt-6.1-luna`**: la familia 6.1 solo tiene
`gpt-6.1-sol`. El humano pidió «6 y 6.1 luna» (dato del líder, 2026-10-19): queda como pregunta P1.
Por ser OpenAI, **no hace falta cliente nuevo en comun**: va por `OpenAIResponsesVisionClient`.
No se encontró ningún otro modelo llamado Luna en Anthropic ni en Google.

## 3. Inventario por proveedor

Columnas: entrada · entrada en caché (lectura) · escritura de caché (5 min) · salida. «Img/PDF» =
si la documentación oficial dice que admite imagen y PDF de entrada (IA1 manda una imagen por página
de los PDF escaneados y el PDF tal cual cuando trae texto). «Tanda 1» = recomendación del design (P2).

### Anthropic — https://platform.claude.com/docs/en/about-claude/pricing (y claude.com/pricing)

| ID de API | Entrada | Caché lect. | Caché escr. | Salida | Img/PDF | Herramienta forzada | Tanda 1 |
|---|---|---|---|---|---|---|---|
| `claude-opus-4-8` (legacy) | 5 | 0,50 | 6,25 | 25 | sí/sí | admite | **referencia IA3/IA4** |
| `claude-opus-5` (legacy) | 5 | 0,50 | 6,25 | 25 | sí/sí | admite | sí |
| `claude-sonnet-5` (legacy) | 2 | 0,20 | 2,50 | 10 | sí/sí | admite | sí |
| `claude-haiku-5-5` | 0,10 | 0,01 | 0,125 | 0,50 | sí/sí | admite (sin pensar) | sí |
| `claude-opus-5-5` | 4 | 0,20 | 5 | 20 | sí/sí | **400** | si P5 = (a) |
| `claude-sonnet-5-5` | 2 | 0,10 | 2,50 | 10 | sí/sí | **400** | si P5 = (a) |
| `claude-fable-5` (legacy) | 10 | 1 | 12,50 | 50 | sí/sí | admite | no (precio) |
| `claude-fable-5-1` | 10 | 0,25 | 12,50 | 50 | sí/sí | **400** | no (precio) |

Notas: Haiku 5.5 sube a 0,50 / 0,05 / 0,625 / 2,50 con más de 100.000 tokens de entrada (tramo largo).
Mythos 5 y 5.1: acceso limitado, excluidos. Opus 4.7/4.6, Sonnet 4.6 y Haiku 4.5: por debajo de 4.8.
Imagen: «All current models support text and image input» (models overview); PDF: «Claude works
with any standard PDF» (guía *PDF support*). Los modelos 4.7+ usan un tokenizador que da ~30 % más
tokens con el mismo texto (página de precios). Batch: −50 % (no aplica: el comparador no usa Batch).

### Google — https://ai.google.dev/gemini-api/docs/pricing (actualizada 2026-10-16)

| ID de API | Entrada | Caché lect. | Salida (incluye pensamiento) | Img/PDF | Tanda 1 |
|---|---|---|---|---|---|
| `gemini-3.7-flash` | (sin precio: se factura como 3.8, supuesto) | — | — | sí/sí | **referencia IA1** |
| `gemini-3.8-flash` | 0,75 | 0,075 | 3,75 | sí/sí | según P2 (duplica la referencia) |
| `gemini-4-argon` | 2 | 0,10 (implícita) | 10 | sí/sí | sí |

**Cambio de precio anunciado**: `gemini-3.8-flash` pasa a 1,50 / 0,15 / 7,50 desde el **2027-01-01**
y `gemini-4-argon` a 4 / 0,20 / 20 desde el **2026-12-01**. La tabla los lleva con `vigente_hasta`.
Img/PDF: fichas oficiales de `gemini-3.8-flash` (2026-09-02) y `gemini-4-argon` (2026-10-14): «Text,
image, video, audio, and PDF». Fuera: `gemini-3.6-flash` (< 3.7), `gemini-3.5-flash-lite` y
`gemini-3.1-flash-lite` (< 3.7, gama lite), `gemini-3.1-pro-preview` (versión 3.1 y preview),
`gemini-omni-1.1-flash` (modelo de generación multimodal, no de la línea Flash).

### OpenAI — https://developers.openai.com/api/docs/pricing (sin fecha de actualización visible)

| ID de API | Entrada | Caché lect. | Salida | Img/PDF | Tanda 1 |
|---|---|---|---|---|---|
| `gpt-5.4` | 2,50 | 0,25 | 15 | sí/probable | **referencia IA2** (< 5.5) |
| `gpt-5.5` | 5 | 0,50 | 30 | sí/probable | sí |
| `gpt-5.6-luna` | 0,20 | 0,02 | 1,20 | sí/**sin confirmar** | sí (P1) |
| `gpt-5.6-terra` | 2 | 0,20 | 12 | sí/probable | no (6.1-sol es más nuevo y no más caro) |
| `gpt-5.6-sol` | 4 | 0,40 | 20 | sí/probable | no (precio) |
| `gpt-6-luna` | 0,10 | 0,01 | 0,50 | sí/**sin confirmar** | sí (P1) |
| `gpt-6.1-sol` | 2 | 0,10 | 10 | sí/probable | sí (P1) |
| `gpt-6-astra` | 10 | 1 | 50 | sí/probable | no (precio) |

Tramo largo: por encima de **272K** tokens de entrada, ×2 la entrada y la caché y ×1,5 la salida
(fichas de `gpt-5.5`, `gpt-5.6-luna`, `gpt-6.1-sol`). Los albaranes no se acercan, pero la tabla lo
lleva. Escritura de caché: la ficha de `gpt-6-luna` da 0,125 (1,25× la entrada); el cliente de comun
no pide caché explícita, así que solo cuenta si el `usage` la informa. `gpt-6-sol` (2 / 0,20 / 10)
queda fuera por tener ya `gpt-6.1-sol` al mismo precio de entrada y salida; `gpt-5.5-pro` y
`gpt-5.4-pro` (30 / 180) por precio; `gpt-5.4-mini`/`-nano` por debajo de 5.5.
Img/PDF: «All latest OpenAI models support text and image input» (models). PDF por `input_file`:
«requires models with vision capabilities, such as gpt-4o and later» (guía *PDF files*); ninguna
ficha por modelo lo confirma, y **las de las dos Luna no lo mencionan**. Lo resuelve la corrida de
humo (T13): un caso con PDF de texto por modelo.

## 4. Estimación de la tanda 1 (para P3)

Supuestos por llamada (los de `estimacion_por_defecto` de la tabla, con margen ×1,5): IA1 10.000 de
entrada y 3.000 de salida; IA2 14.000 / 4.000; IA3 12.000 / 4.000; IA4 5.000 / 1.500. Llamadas por
modelo: IA1 57 (59 casos, 2 sin albarán), IA2 9 (+9 de preparación), IA3 59 (IA4 del libro, sin
coste), IA4 13 (+13 de preparación con `claude-opus-4-8`).

| Fase | 11 modelos (sin P5, sin 3.8 duplicado) | Más caro por modelo |
|---|---|---|
| IA1 | ≈ 55 USD | `gpt-5.5` ≈ 12, `claude-opus-4-8`/`-5` ≈ 11 |
| IA2 | ≈ 12 USD | `gpt-5.5` ≈ 2,6 |
| IA3 | ≈ 73 USD | `gpt-5.5` ≈ 16, Opus ≈ 14 |
| IA4 | ≈ 9 USD | `gpt-5.5` ≈ 1,4 |
| **Total** | **≈ 150 USD** (≈ 185 con `claude-opus-5-5` y `claude-sonnet-5-5`) | |

Es una cota alta: el margen ×1,5 y los tokens por defecto son conservadores. Tras la corrida de
humo, la estimación usa los tokens medidos (R13) y baja.
