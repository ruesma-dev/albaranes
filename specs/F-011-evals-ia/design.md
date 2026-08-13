<!-- specs/F-011-evals-ia/design.md -->
# F-011 · Evals de IA con ground truth y puerta en el arnés — Diseño

## Encaje en la arquitectura

`evals/` es **herramienta transversal del monorepo**, como `harness/`: no es
un séptimo servicio ni entra en `harness/servicios.json`. Internamente sigue
la disciplina hexagonal a su escala: lógica pura (conversor, comparador,
barrido, informe: sin red, sin BBDD, sin imports de servicios) separada de
los adaptadores que componen servicios reales (`evals/procesos/`). Los
servicios sv2/sv5/sv6 **no se modifican**: los evals los importan y componen
desde fuera, contra las costuras que ya existen:

- **sv2 (IA1/IA2)**: `AlbaranExtractionService.extract_phase_1` /
  `review_phase_2` reciben proveedores, prompts y adjuntos ya construidos.
  El runner hace su propia composición mínima (prompt repo YAML + clientes
  LLM + registry de schemas), sin pasar por `interface_adapters/composition.py`
  (que arrastra FastAPI) y sin colas ni blobs.
- **sv5 (IA3/IA4 modo real)**: `ValuationExtractionService` «recibe el
  contexto ya construido» (docstring) y `ConciliacionService.conciliar`
  igual: el runner construye `ContextoValoracion` desde los fixtures de
  INPUTS y llama con clientes LLM reales. Sin SQL crudo, sin SharePoint
  (`attachment=None`, camino ya soportado por los 3 clientes).
- **sv6 (IA3/IA4 modo determinista)**: `ValuationBuilder` y las redes
  (`partida_matcher`, `unit_converter`, `unit_category_guard`,
  `importe_calculator`, `price_reconciler`, `residuos_container_calc`,
  `modifier_contract_matcher`) consumen el envelope de sv5. El modo
  determinista fabrica ese envelope desde el ground truth (ver abajo) y NO
  instancia repositorio de BBDD ni clientes HTTP.

**Restricción de imports**: sv2 y sv6 usan paquetes de primer nivel con el
mismo nombre (`application`, `domain`…): no pueden importarse en el mismo
proceso. El CLI del runner orquesta un **subproceso por servicio**
(`evals/procesos/ia12.py` para sv2, `evals/procesos/ia34.py` para sv5+sv6
—sv5 y sv6 también colisionan entre sí: dentro de `ia34.py` el modo real usa
sv5 y el determinista usa sv6, y si una corrida pide ambos, `runner.py`
lanza dos subprocesos—). Cada subproceso inserta en `sys.path[0]` solo la
raíz de SU servicio y devuelve resultados como JSON por stdout.

**Límite de microservicio**: no se viola. Los evals no añaden
responsabilidades a ningún servicio; son tooling del repositorio, como la
campaña de mutación. La puerta es arnés puro.

## Ficheros a crear

| Ruta | Contenido |
|---|---|
| `evals/__init__.py` | paquete |
| `evals/modelos.py` | dataclasses puras: `Caso`, `ValorEsperado` (con sentinela `NO_COMPARAR` para `?`), `Discrepancia`, `ResultadoCaso`, `ResultadoFase` |
| `evals/barrido.py` | `PATRONES: tuple[tuple[str, re.Pattern], ...]` (correo, IP, GUID, token/clave — los de C3 bis) y `barrer(texto: str) -> list[Hallazgo]`. Puro |
| `evals/conversor.py` | CLI `python -m evals.conversor`. `parsear_hoja(ws) -> list[Tabla]` (localiza `TABLA n —` y títulos de INPUTS), `normalizar_celda(valor) -> ValorEsperado`, `convertir(dir_gt, dir_fixtures) -> InformeConversion`. Escritura atómica: primero todo en memoria, barrido R4, luego disco. JSON con claves ordenadas, `ensure_ascii=False`, metadato `sha256_libro` |
| `evals/comparador.py` | `comparar(esperado: dict, obtenido: dict) -> list[Discrepancia]` aplicando convenios R2. Puro |
| `evals/informe.py` | render del informe Markdown (R12) y `parsear_veredicto(texto) -> str` (lo reutiliza la puerta) |
| `evals/runner.py` | CLI `python -m evals.runner --fases IA1,IA2,IA3,IA4 [--modo determinista|real] [--con-llm] [--proveedores ...] [--feature F-XXX] [--casos ...]`. Orquesta subprocesos, agrega resultados, escribe informe, exit code R13 |
| `evals/procesos/__init__.py` | paquete |
| `evals/procesos/ia12.py` | adaptador sv2: composición mínima (prompt repo, clientes LLM reales, preprocesado de material idéntico al de producción), bucle secuencial de casos |
| `evals/procesos/ia34.py` | adaptador sv5/sv6: modo real (contexto desde fixtures → `ValuationExtractionService` / `ConciliacionService`) y modo determinista (envelope estimulado → `ValuationBuilder` + redes, con `ValuationIaClient` stub) |
| `evals/requirements.txt` | dependencias extra del venv raíz (P5): PyYAML, pydantic-settings, PyMuPDF, opencv-python-headless, numpy |
| `evals/fixtures/` | salida versionada del conversor: `IA1/<caso_id>.json`, `IA2/…`, `IA3/…`, `IA4/…`, `inputs/<caso_id>.json` |
| `harness/rutas_sensibles.py` | módulo GENÉRICO (portable tal cual a arnes-base): carga y validación de la declaración, `ficheros_tocados(feature, base, git)` reutilizando `harness.alcance.resolver_refs` + `parsear_diff` (sin `filtrar_produccion`), cotejo por `fnmatch` sobre rutas normalizadas, `evaluar_puerta(...)`, CLI `--validar` / `--puerta --base <rama>` |
| `harness/rutas_sensibles.json` | declaración de ESTE repo (ver esquema abajo) |
| `tests/test_f011_r*.py` | tests trazables en el `tests/` de la raíz (corren con el venv raíz vía sección 7 de init.sh) |

### Esquema de `harness/rutas_sensibles.json`

```json
{
  "verificaciones": [
    {
      "nombre": "evals",
      "comando": "python -m evals.runner --fases {fases} --feature {feature}",
      "informe": "progress/evals_{feature}.md",
      "exigencia": "aviso",
      "rutas": [
        { "patron": "services/albaranes-api/config/prompts/**",            "fases": ["IA1", "IA2"], "motivo": "prompts YAML de extracción" },
        { "patron": "services/albaranes-api/config/prompts.yaml",          "fases": ["IA1", "IA2"], "motivo": "índice de prompts sv2" },
        { "patron": "services/albaranes-api/config/revision_rules.yaml",   "fases": ["IA2"],        "motivo": "reglas de revisión fase 2" },
        { "patron": "services/albaranes-api/domain/models/**",             "fases": ["IA1", "IA2"], "motivo": "schemas Pydantic de extracción" },
        { "patron": "services/albaranes-api/infrastructure/llm/**",        "fases": ["IA1", "IA2"], "motivo": "clientes LLM sv2" },
        { "patron": "services/albaran-valoracion-api/config/prompts/**",   "fases": ["IA3"],        "motivo": "prompt de valoración" },
        { "patron": "services/albaran-valoracion-api/config/prompts.yaml", "fases": ["IA3", "IA4"], "motivo": "índice de prompts sv5 (incluye conciliación)" },
        { "patron": "services/albaran-valoracion-api/config/revision_rules.yaml", "fases": ["IA3"], "motivo": "reglas de revisión sv5" },
        { "patron": "services/albaran-valoracion-api/domain/models/**",    "fases": ["IA3", "IA4"], "motivo": "schemas Pydantic de valoración/conciliación" },
        { "patron": "services/albaran-valoracion-api/infrastructure/llm/**", "fases": ["IA3", "IA4"], "motivo": "clientes LLM sv5" },
        { "patron": "services/albaran-valoracion-persist/application/services/**", "fases": ["IA3", "IA4"], "motivo": "redes deterministas de sv6" },
        { "patron": "services/albaran-valoracion-persist/domain/models/**", "fases": ["IA3", "IA4"], "motivo": "envelope DTO y records de sv6" },
        { "patron": "services/albaran-valoracion-persist/config/unit_registry.yaml", "fases": ["IA3", "IA4"], "motivo": "registro de unidades" },
        { "patron": "services/albaranes-comun/ruesma_comun/llm/**",        "fases": ["IA1", "IA2", "IA3", "IA4"], "motivo": "clientes LLM y json_coercion compartidos" }
      ]
    }
  ]
}
```

El valor de `exigencia` arranca según decida el humano (P4). El validador
imita a `harness/servicios.py`: campos obligatorios con mensajes que nombran
qué entrada falla, nombres de verificación únicos, cada patrón casa con >= 1
fichero real (una declaración muerta es un aviso falso de protección), y
fichero roto ⇒ exit 1 ⇒ KO en init.sh (R19). Fichero ausente ⇒ lista vacía y
nada cambia (R18).

## Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `harness/init.sh` | nueva sección **«7 ter. Puerta de rutas sensibles»** tras la 7b, con el patrón exacto de la 7b: si existe `harness/rutas_sensibles.json` y hay Python, `SALIDA=$($PY -m harness.rutas_sensibles --puerta --base "$RAMA_BASE" 2>&1)`; exit 0 → `ok "$SALIDA"` (incluye los N/A con motivo), exit 1 → `ko "$SALIDA"`, y un exit 3 reservado para exigencia `aviso` → `warn "$SALIDA"`. Sin declaración, ni una línea |
| `CHECKPOINTS.md` | bloque nuevo **«C4 ter — Verificaciones extra por rutas sensibles»**: si la puerta señaló rutas tocadas, el reviewer comprueba que el informe de evals existe, veredicto VERDE (o AVISO justificado si exigencia `aviso`), cubre las fases exigidas y es FRESCO (su commit pertenece a la rama y es posterior al último commit que tocó rutas sensibles). El párrafo genérico del mecanismo se redacta portable; la mención a evals/fases es la parte específica de este repo |
| `evals/README.md` | actualizar «Diseño previsto» a realidad: comandos del conversor y runner, modos, dónde quedan informes y fixtures, dependencias (P5) |
| `.gitignore` | añadir `evals/resultados/` NO (no existe: los informes van a `progress/`); único cambio: nada — los `*.xlsx` y `*.pdf` ya están cubiertos. Si al implementar aparece un directorio temporal del runner, se añade aquí |

## Ficheros que NO se tocan (y podrían tentar)

- **Nada bajo `services/`**: ni sv2, ni sv5, ni sv6, ni comun. Si al
  implementar el runner aparece la necesidad de cambiar una firma de un
  servicio, se para y se re-propone (la costura documentada arriba dice que
  no hace falta).
- `harness/alcance.py`: se **importa**, no se modifica (expone ya
  `resolver_refs`, `parsear_diff`, `rama_de_feature`, `git_en` y el filtro es
  opcional por construcción).
- `harness/cobertura.py`, `harness/mutacion.py`, `harness/rigor.*`,
  `harness/servicios.*`, `harness/features.json`.
- `progress/*` (los escribe el runner en runtime, no esta feature en git
  salvo el flujo normal del arnés).
- Los 5 `.xlsx` y `evals/inputs/albaranes/` (datos del humano, sin
  versionar).

## Modo determinista IA3/IA4 — mecánica

Por caso: se carga `fixtures/inputs/<caso>.json` (líneas albarán, líneas
contrato, condiciones) y `fixtures/IA3/<caso>.json`. Se fabrica el envelope
que sv5 habría devuelto con: los matches de TABLA 1, las sintéticas de
TABLA 2 **y las prohibidas de TABLA 3 inyectadas como propuestas de la IA**.
Se ejecuta `ValuationBuilder` con las redes reales (unit registry YAML real
de sv6) y un `ValuationIaClient`/repositorio stub. Asserts: las prohibidas
NO aparecen en los records finales; las esperadas sí, con la partida
heredada; `codigo_partida_final`, `precio_unitario_final`, `precio_source`,
`importe_calculado` y `review_required` coinciden con TABLA 1 (convenios
R2). Para IA4 determinista: la respuesta de conciliación se stubea desde
`fixtures/IA4/<caso>.json` y se asserta la mutación del envelope por
`conciliacion_orchestrator` y su efecto en el build. **Límite declarado**:
el modo determinista NO evalúa el juicio del LLM (eso es el modo real);
evalúa que las redes de sv6 hagan cumplir las reglas aunque la IA proponga
lo prohibido.

## Riesgos y decisiones (alternativas descartadas)

1. **Runner vía HTTP a servicios levantados** (sv5 `/value`): descartado —
   exige BBDD poblada (sv5 lee contexto por SQL crudo) y levantar el
   pipeline local entero; la composición directa con contexto inyectado usa
   las mismas clases de producción sin infraestructura.
2. **Ejecutar el modo determinista dentro de init.sh**: descartado — la
   puerta solo lee informes (R23), como la campaña de mutación. Mantiene
   init.sh rápido y un único patrón «herramienta cara a demanda + evidencia
   en progress/».
3. **Un solo proceso importando sv2 y sv6**: imposible por colisión de
   paquetes de primer nivel (`application`, `domain`); de ahí los
   subprocesos por servicio.
4. **Barrido como paso posterior manual**: prohibido por el alcance acordado;
   integrado en el conversor con aborto total (R4). Se descartó una lista de
   excepciones en v1: si un patrón legítimo cae en el barrido, se decide con
   el humano.
5. **Puerta genérica acoplada a «evals»**: descartado — la declaración lleva
   nombre/comando/informe por verificación, de modo que arnes-base recibe un
   mecanismo neutro («rutas declaradas ⇒ evidencia obligatoria») y albaranes
   lo instancia con evals.
6. **Frescura del informe validada por la puerta**: descartado en v1 — el
   informe vive en progress/ y su commit mueve HEAD, lo que haría la
   comprobación automática frágil; la frescura queda en C4 ter (reviewer),
   igual que la verificación independiente de la mutación en C4 bis.
7. **Riesgo**: los 5 libros están vacíos; hasta que el humano los rellene, el
   runner dará NO_EVALUABLE (R15) y la puerta en `bloqueo` frenaría
   F-002…F-006. Mitigación: campo `exigencia` (P4).
8. **Riesgo**: deriva entre los libros Excel y los fixtures versionados (el
   humano edita el Excel y nadie reconvierte). Mitigación: el metadato
   `sha256_libro` de cada fixture permite al reviewer (C4 ter) detectar que
   el Excel presente no casa con los fixtures; no se automatiza en v1 porque
   los xlsx no están en git.
