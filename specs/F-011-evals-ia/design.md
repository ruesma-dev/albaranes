<!-- specs/F-011-evals-ia/design.md -->
# F-011 · Evals de IA con ground truth y puerta en el arnés — Diseño

## Encaje en la arquitectura

`evals/` es **herramienta transversal del monorepo**, como `harness/`: no es
un séptimo servicio ni entra en `harness/servicios.json`. Internamente sigue
la disciplina hexagonal a su escala: lógica pura (conversor, comparador,
barrido, criticidad, informe: sin red, sin BBDD, sin imports de servicios)
separada de los adaptadores que componen servicios reales
(`evals/procesos/`). Los servicios sv2/sv5/sv6 **no se modifican**: los
evals los importan y componen desde fuera, contra las costuras que ya
existen:

- **sv2 (IA1/IA2)**: `AlbaranExtractionService.extract_phase_1` /
  `review_phase_2` reciben proveedores, prompts y adjuntos ya construidos.
  El runner hace su propia composición mínima (prompt repo YAML + clientes
  LLM + registry de schemas), sin pasar por `interface_adapters/composition.py`
  (que arrastra FastAPI) y sin colas ni blobs.
- **sv5 (IA3/IA4 reales)**: `ValuationExtractionService` «recibe el contexto
  ya construido» (docstring) y `ConciliacionService.conciliar` igual: el
  runner construye `ContextoValoracion` desde los fixtures de INPUTS y llama
  con clientes LLM reales. Sin SQL crudo, sin SharePoint
  (`attachment=None`, camino ya soportado por los 3 clientes).
- **sv6 (redes deterministas y build final)**: `ValuationBuilder` y las
  redes (`partida_matcher`, `unit_converter`, `unit_category_guard`,
  `importe_calculator`, `price_reconciler`, `residuos_container_calc`,
  `modifier_contract_matcher`) consumen el envelope de sv5. Reciben un
  envelope real (pasada completa) o estimulado (modo determinista) y NO
  instancian repositorio de BBDD ni clientes HTTP.

**Restricción de imports**: sv2, sv5 y sv6 usan paquetes de primer nivel con
el mismo nombre (`application`, `domain`…): no pueden importarse dos
servicios en el mismo proceso. El CLI del runner orquesta **un subproceso
por servicio**: `evals/procesos/sv2_extraccion.py` (IA1/IA2),
`evals/procesos/sv5_valoracion.py` (IA3/IA4 reales) y
`evals/procesos/sv6_build.py` (redes deterministas + build). Cada subproceso
inserta en `sys.path[0]` solo la raíz de SU servicio y devuelve resultados
como JSON por stdout. El **hand-off sv5 → sv6 del extremo-a-extremo** es el
propio envelope serializado a JSON, igual que en producción: el subproceso
de sv5 lo emite y el de sv6 lo consume.

**Límite de microservicio**: no se viola. Los evals no añaden
responsabilidades a ningún servicio; son tooling del repositorio, como la
campaña de mutación. La puerta es arnés puro.

## Las dos corridas del runner

| Corrida | Comando | Qué ejecuta | Coste | Para qué |
|---|---|---|---|---|
| **Pasada completa** | `python -m evals.runner --con-llm [--feature F-XXX] [--proveedores ...] [--casos ...]` | IA1, IA2 (sv2 real, proveedor primario por defecto — D3), IA3, IA4 (sv5 real) y extremo-a-extremo (envelope real de sv5 → build sv6 → comparación contra `RESULTADO_FINAL`) | Llamadas LLM | La evidencia que exige la puerta (D2: no se trocea por fase) |
| **Modo determinista** | `python -m evals.runner [--feature F-XXX] [--casos ...]` | Redes de sv6 estimuladas (IA3/IA4) + extremo-a-extremo determinista (propuesta estimulada → build → comparación contra `RESULTADO_FINAL`) | Cero (sin red) | Desarrollo diario de las redes de sv6, barato |

Pedir IA1/IA2 sin `--con-llm` es un error explícito (R10): el gasto LLM
nunca es implícito. Ambas corridas escriben el mismo formato de informe; la
puerta solo acepta como evidencia el de una pasada completa (R24).

## Ficheros a crear

| Ruta | Contenido |
|---|---|
| `evals/__init__.py` | paquete |
| `evals/modelos.py` | dataclasses puras: `Caso`, `ValorEsperado` (sentinelas `NO_COMPARAR` para `?` y `ESPERA_REVISION` para el literal `REVISIÓN`), `Discrepancia` (con severidad `fallo`/`aviso`), `ResultadoCaso`, `ResultadoFase`, `ResultadoPasada` |
| `evals/barrido.py` | `PATRONES: tuple[tuple[str, re.Pattern], ...]` (correo, IP, GUID, token/clave — los de C3 bis; precios/razón social/CIF quedan fuera por D1) y `barrer(texto: str) -> list[Hallazgo]`. Puro |
| `evals/criticidad.json` | configuración versionada de criticidad por campo (D4): bloque `criticos` (partida final, cantidades, precios, importes, códigos de producto/obra/contrato/CIF/LER), bloque `laxos` (`descripcion`, comentarios) y ajustes por campo concreto. Campo no clasificado → crítico + aviso (R8) |
| `evals/criticidad.py` | carga y validación de `criticidad.json`; `severidad(campo: str) -> Severidad`. Puro |
| `evals/conversor.py` | CLI `python -m evals.conversor`. `parsear_hoja(ws) -> list[Tabla]` (localiza `TABLA n —` y títulos de INPUTS), `normalizar_celda(valor) -> ValorEsperado` (incluye `REVISIÓN`), `convertir(dir_gt, dir_fixtures) -> InformeConversion` sobre los **6 libros**. Escritura atómica: primero todo en memoria, barrido R4, luego disco. JSON con claves ordenadas, `ensure_ascii=False`, metadato `sha256_libro` |
| `evals/comparador.py` | `comparar(esperado: dict, obtenido: dict, criticidad) -> list[Discrepancia]` aplicando convenios R2 y severidad R7/R8. El sentinela `ESPERA_REVISION` casa con «el pipeline dejó el valor a revisión» (flag de revisión activo / precio o partida sin resolver). Puro |
| `evals/informe.py` | render del informe Markdown (R15: fallos críticos vs avisos laxos, secciones por fase + extremo-a-extremo) y `parsear_veredicto(texto) -> str` + `es_pasada_completa(texto) -> bool` (los reutiliza la puerta) |
| `evals/runner.py` | CLI (tabla de arriba). Orquesta subprocesos en secuencia, encadena el envelope sv5→sv6, agrega resultados, escribe informe, exit codes R16, NO_EVALUABLE R18 |
| `evals/procesos/__init__.py` | paquete |
| `evals/procesos/sv2_extraccion.py` | adaptador sv2: composición mínima (prompt repo, clientes LLM reales, preprocesado de material idéntico al de producción), bucle secuencial de casos IA1/IA2 |
| `evals/procesos/sv5_valoracion.py` | adaptador sv5: contexto desde fixtures INPUTS → `ValuationExtractionService` (IA3) y `ConciliacionService` (IA4); emite resultados de fase Y el envelope final por caso para el extremo-a-extremo |
| `evals/procesos/sv6_build.py` | adaptador sv6: recibe envelope (real o estimulado desde ground truth), ejecuta redes + `ValuationBuilder` con stubs de IA/repositorio, devuelve records finales para comparar contra IA3/IA4 y `RESULTADO_FINAL` |
| `evals/requirements.txt` | dependencias extra del venv raíz (D6): PyYAML, pydantic-settings, PyMuPDF, opencv-python-headless, numpy |
| `evals/fixtures/` | salida versionada del conversor: `IA1/<caso_id>.json`, `IA2/…`, `IA3/…`, `IA4/…`, `inputs/<caso_id>.json`, `final/<caso_id>.json` |
| `harness/rutas_sensibles.py` | módulo GENÉRICO (portable tal cual a arnes-base): carga y validación de la declaración, `ficheros_tocados(feature, base, git)` reutilizando `harness.alcance.resolver_refs` + `parsear_diff` (sin `filtrar_produccion`), cotejo por `fnmatch` sobre rutas normalizadas, `evaluar_puerta(...)`, CLI `--validar` / `--puerta --base <rama>` |
| `harness/rutas_sensibles.json` | declaración de ESTE repo (ver esquema abajo) |
| `tests/test_f011_r*.py` | tests trazables en el `tests/` de la raíz (corren con el venv raíz vía sección 7 de init.sh) |

### Esquema de `harness/rutas_sensibles.json`

Tras D2, la declaración NO trocea por fases: tocar cualquier ruta sensible
exige la pasada completa. El campo `fases` de la primera versión desaparece.

```json
{
  "verificaciones": [
    {
      "nombre": "evals",
      "comando": "python -m evals.runner --con-llm --feature {feature}",
      "informe": "progress/evals_{feature}.md",
      "exigencia": "aviso",
      "rutas": [
        { "patron": "services/albaranes-api/config/prompts/**",            "motivo": "prompts YAML de extracción (IA1/IA2)" },
        { "patron": "services/albaranes-api/config/prompts.yaml",          "motivo": "índice de prompts sv2" },
        { "patron": "services/albaranes-api/config/revision_rules.yaml",   "motivo": "reglas de revisión fase 2" },
        { "patron": "services/albaranes-api/domain/models/**",             "motivo": "schemas Pydantic de extracción" },
        { "patron": "services/albaranes-api/infrastructure/llm/**",        "motivo": "clientes LLM sv2" },
        { "patron": "services/albaran-valoracion-api/config/prompts/**",   "motivo": "prompt de valoración (IA3)" },
        { "patron": "services/albaran-valoracion-api/config/prompts.yaml", "motivo": "índice de prompts sv5 (incluye conciliación IA4)" },
        { "patron": "services/albaran-valoracion-api/config/revision_rules.yaml", "motivo": "reglas de revisión sv5" },
        { "patron": "services/albaran-valoracion-api/domain/models/**",    "motivo": "schemas Pydantic de valoración/conciliación" },
        { "patron": "services/albaran-valoracion-api/infrastructure/llm/**", "motivo": "clientes LLM sv5" },
        { "patron": "services/albaran-valoracion-persist/application/services/**", "motivo": "redes deterministas de sv6" },
        { "patron": "services/albaran-valoracion-persist/domain/models/**", "motivo": "envelope DTO y records de sv6" },
        { "patron": "services/albaran-valoracion-persist/config/unit_registry.yaml", "motivo": "registro de unidades" },
        { "patron": "services/albaranes-comun/ruesma_comun/llm/**",        "motivo": "clientes LLM y json_coercion compartidos" }
      ]
    }
  ]
}
```

`exigencia` arranca en `aviso` y se sube a `bloqueo` cuando haya ground
truth rellenado (D5): es una línea de este JSON. El validador imita a
`harness/servicios.py`: campos obligatorios con mensajes que nombran qué
entrada falla, nombres de verificación únicos, cada patrón casa con >= 1
fichero real (una declaración muerta es un aviso falso de protección), y
fichero roto ⇒ exit 1 ⇒ KO en init.sh (R22). Fichero ausente ⇒ lista vacía
y nada cambia (R21).

## Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `harness/init.sh` | nueva sección **«7 ter. Puerta de rutas sensibles»** tras la 7b, con el patrón exacto de la 7b: si existe `harness/rutas_sensibles.json` y hay Python, `SALIDA=$($PY -m harness.rutas_sensibles --puerta --base "$RAMA_BASE" 2>&1)`; exit 0 → `ok "$SALIDA"` (incluye los N/A con motivo), exit 1 → `ko "$SALIDA"`, y un exit 3 reservado para exigencia `aviso` → `warn "$SALIDA"`. Sin declaración, ni una línea |
| `CHECKPOINTS.md` | bloque nuevo **«C4 ter — Verificaciones extra por rutas sensibles»**: si la puerta señaló rutas tocadas, el reviewer comprueba que el informe existe, corresponde a una pasada completa con veredicto VERDE (o AVISO justificado si exigencia `aviso`) y es FRESCO (su commit pertenece a la rama y es posterior al último commit que tocó rutas sensibles). El párrafo genérico del mecanismo se redacta portable; la mención a evals y a la pasada completa es la parte específica de este repo |
| `evals/README.md` | actualizar a la realidad implementada: el 6º libro `RESULTADO_FINAL` (eval extremo-a-extremo, libros IA1–IA4 como evals de fase), comandos del conversor y del runner, las dos corridas, criticidad, dónde quedan informes y fixtures, dependencias (D6) |
| `.gitignore` | sin cambios previstos (`*.xlsx` y `*.pdf` ya cubiertos; los informes van a `progress/`). Si al implementar aparece un directorio temporal del runner, se añade aquí |

## Ficheros que NO se tocan (y podrían tentar)

- **Nada bajo `services/`**: ni sv2, ni sv5, ni sv6, ni comun. Si al
  implementar el runner aparece la necesidad de cambiar una firma de un
  servicio, se para y se re-propone (la costura documentada arriba dice que
  no hace falta).
- `harness/alcance.py`: se **importa**, no se modifica (expone ya
  `resolver_refs`, `parsear_diff`, `rama_de_feature`, `git_en` y el filtro
  es opcional por construcción).
- `harness/cobertura.py`, `harness/mutacion.py`, `harness/rigor.*`,
  `harness/servicios.*`, `harness/features.json`.
- `progress/*` (los escribe el runner en runtime, no esta feature en git
  salvo el flujo normal del arnés).
- Los 6 `.xlsx` y `evals/inputs/albaranes/` (datos del humano, sin
  versionar).

## Extremo-a-extremo contra `RESULTADO_FINAL` — mecánica

Por caso: el contexto de valoración sale de `fixtures/inputs/<caso>.json`.

- **Pasada completa**: `sv5_valoracion.py` ejecuta IA3 real y, sobre las no
  casadas, IA4 real; emite el envelope. `sv6_build.py` lo consume y ejecuta
  el build determinista completo. Los records finales se comparan contra
  `fixtures/final/<caso>.json`: TABLA 1 (obra, proveedor, CIF, contrato
  elegido, total valorado, ¿requiere revisión?), TABLA 2 (por línea impresa:
  ¿casa?, línea de contrato, partida final, precio final y su origen,
  importe, ¿a revisión?) y TABLA 3 (líneas añadidas no impresas: concepto,
  cantidad, precio, partida, importe). Criticidad D4 y sentinelas `?` /
  `REVISIÓN` aplican en todas.
- **Modo determinista**: mismo build y misma comparación, pero el envelope
  se estimula desde el ground truth de IA3/IA4 (ver siguiente sección) en
  vez de llamar a sv5.

## Modo determinista IA3/IA4 — mecánica

Por caso: se carga `fixtures/inputs/<caso>.json` y `fixtures/IA3/<caso>.json`.
Se fabrica el envelope que sv5 habría devuelto con: los matches de TABLA 1,
las sintéticas de TABLA 2 **y las prohibidas de TABLA 3 inyectadas como
propuestas de la IA**. Se ejecuta `ValuationBuilder` con las redes reales
(unit registry YAML real de sv6) y un `ValuationIaClient`/repositorio stub.
Asserts: las prohibidas NO aparecen en los records finales; las esperadas
sí, con la partida heredada; `codigo_partida_final`,
`precio_unitario_final`, `precio_source`, `importe_calculado` y
`review_required` coinciden con TABLA 1 (convenios R2, criticidad R7). Para
IA4: la respuesta de conciliación se stubea desde `fixtures/IA4/<caso>.json`
y se asserta la mutación del envelope por `conciliacion_orchestrator` y su
efecto en el build. **Límite declarado**: el modo determinista NO evalúa el
juicio del LLM (eso es la pasada completa); evalúa que las redes de sv6
hagan cumplir las reglas aunque la IA proponga lo prohibido.

## Riesgos y decisiones (alternativas descartadas)

1. **Runner vía HTTP a servicios levantados** (sv5 `/value`): descartado —
   exige BBDD poblada (sv5 lee contexto por SQL crudo) y levantar el
   pipeline local entero; la composición directa con contexto inyectado usa
   las mismas clases de producción sin infraestructura.
2. **Ejecutar el modo determinista dentro de init.sh**: descartado — la
   puerta solo lee informes (R26), como la campaña de mutación. Mantiene
   init.sh rápido y un único patrón «herramienta cara a demanda + evidencia
   en progress/».
3. **Un solo proceso importando varios servicios**: imposible por colisión
   de paquetes de primer nivel (`application`, `domain`); de ahí un
   subproceso por servicio y el hand-off del envelope por JSON.
4. **Barrido como paso posterior manual**: prohibido por el alcance
   acordado; integrado en el conversor con aborto total (R4). Sin lista de
   excepciones en v1: si un patrón legítimo cae en el barrido, se decide con
   el humano.
5. **Puerta genérica acoplada a «evals»**: descartado — la declaración lleva
   nombre/comando/informe por verificación, de modo que arnes-base recibe un
   mecanismo neutro («rutas declaradas ⇒ evidencia obligatoria») y albaranes
   lo instancia con evals.
6. **Troceo de la puerta por fases** (diseño de la primera versión):
   retirado por D2 — cualquier ruta sensible tocada exige la pasada
   completa; el campo `fases` de la declaración desaparece y el informe de
   fase sirve para localizar el fallo, no para reducir la corrida.
7. **Umbral porcentual de verde**: descartado por D4 — la clasificación
   crítico/laxo por campo (configuración versionada) da el margen donde el
   negocio lo tolera sin regalar los campos que pagan facturas.
8. **Frescura del informe validada por la puerta**: descartado en v1 — el
   informe vive en progress/ y su commit mueve HEAD, lo que haría la
   comprobación automática frágil; la frescura queda en C4 ter (reviewer),
   igual que la verificación independiente de la mutación en C4 bis.
9. **Riesgo**: los 6 libros están hoy sin casos; hasta que el humano los
   rellene, el runner dará NO_EVALUABLE (R18). Cubierto por la exigencia
   `aviso` inicial (D5) sin bloquear F-002…F-006.
10. **Riesgo**: deriva entre los libros Excel y los fixtures versionados (el
    humano edita el Excel y nadie reconvierte). Mitigación: el metadato
    `sha256_libro` de cada fixture permite al reviewer (C4 ter) detectar que
    el Excel presente no casa con los fixtures; no se automatiza en v1
    porque los xlsx no están en git.
11. **Riesgo**: el veredicto VERDE con avisos laxos puede acumular deriva en
    descripciones. Mitigación: los avisos constan siempre en el informe y la
    criticidad es ajustable por campo (subir un campo a crítico es una línea
    de `evals/criticidad.json`).
