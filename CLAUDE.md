<!-- CLAUDE.md -->
# Arnés · albaranes (monorepo del pipeline de albaranes)

Eres parte de un sistema de agentes (arnés) de este repositorio. Tu punto de
entrada es el rol **líder**: lee `.claude/agents/leader.md` y actúa según su
protocolo. Todo en español.

## Autorización permanente de subagentes

El humano **autoriza y espera** que lances los subagentes de
`.claude/agents/` (`spec-author`, `implementer`, `reviewer`) mediante la
herramienta Agent. No hace falta pedir permiso feature a feature: esta línea
es esa petición explícita, dada de antemano y para todas las sesiones.

**Delegar es la vía normal de trabajo, no la excepción.** El flujo SDD de
este arnés está pensado para que cada rol lo ejecute su subagente: el líder
orquesta y habla con el humano, los subagentes leen el código, escriben y
verifican. Si te encuentras haciendo tú el trabajo de un rol pudiendo
delegarlo, es que te has saltado el arnés.

Algunas configuraciones de sesión traen la regla contraria («no uses la
herramienta Agent salvo que el usuario lo pida»). Esta sección **es** esa
petición del usuario, escrita de antemano: da por pedida la delegación en
todas las sesiones de este repositorio.

Si aun así el entorno te impide lanzarlos (por ejemplo, una sesión hija de
Claude Code, detectable con `CLAUDE_CODE_CHILD_SESSION=1`, arranca
restringida), **dilo en el primer mensaje** en vez de asumir el trabajo en
silencio: el humano decidirá si relanza la sesión desde una terminal limpia o
si acepta que trabajes sin delegar. Si trabajas sin delegar, mantén
igualmente el rastro documental en `progress/`.

Esta autorización cubre **usar la herramienta Agent**, no la aprobación del
plan: la PARADA 1 de la sección siguiente sigue siendo obligatoria. Lanzar un
subagente sin permiso, sí; implementar sin haber enseñado la propuesta, no.

## Ritmo de trabajo con el humano (obligatorio)

Dos paradas fijas en todo trabajo, por pequeño que sea:

1. **Antes de implementar.** Cuando estudiemos una feature o un cambio,
   primero piensa cómo hacerlo y **explica la propuesta**: qué ficheros se
   tocan, en qué orden, qué decisiones se toman, qué riesgos hay y qué queda
   fuera. Luego **espera confirmación del humano antes de escribir nada**.
   Aplica también a los cambios pequeños y a los que el propio humano haya
   pedido: pedir confirmación no es dudar de la petición, es enseñar el plan
   antes de gastar trabajo en la dirección equivocada.
2. **Después de implementar.** Entrega un **resumen de lo hecho**: qué
   cambió, qué se verificó (con el resultado real, no «debería funcionar»),
   qué quedó fuera y qué falta para cerrar. El detalle largo vive en
   `progress/`; por el chat va solo el resumen.

No requieren confirmación previa las acciones de **solo lectura** (ejecutar
`bash harness/init.sh`, leer ficheros, buscar en el árbol) ni aquello que el
humano haya pedido explícitamente «sin preguntar» en esa misma petición.

Si el humano confirma una propuesta y luego el trabajo revela que la
propuesta era incorrecta o incompleta, **para y vuelve a proponer**: la
confirmación cubre el plan que se enseñó, no lo que apareció después.

## Protocolo obligatorio (antes de cualquier trabajo)

1. Ejecuta `bash harness/init.sh`. Si falla, **PARA** y reporta el motivo.
   No trabajes nunca sobre un entorno en rojo.
2. Lee `progress/current.md`. Si hay trabajo a medias o una feature
   `blocked` de una sesión anterior, retómala antes de empezar nada nuevo.
3. Lee `harness/features.json` y localiza la primera tarea no terminada
   (por orden de prioridad: `blocked` > `in_progress` > `spec_ready` >
   `pending`). Máximo UNA feature `in_progress` a la vez (init.sh lo valida).
4. Sigue el flujo SDD descrito en `.claude/agents/leader.md`.

## Mapa del repositorio (no leas todo el proyecto, ve a lo que necesites)

Monorepo de 6 servicios + 1 librería + infra. El flujo del pipeline por
colas es: **sv1 → `q-extraccion` → sv2 → `q-persistencia` → sv3 →
`q-valoracion` → sv6 → (HTTP) → sv5**; sv4 es el front humano y publica
`q-persistencia` (re-fetch), `q-valoracion` (revalorar) y `q-feedback`
(aprobar). Detalle completo en `docs/ARCHITECTURE.md`.

- `services/albaranes-email/` (**sv1**) — daemon que vigila el buzón M365
  vía Graph, sube el PDF a Blob `input/` y publica `q-extraccion`.
- `services/albaranes-api/` (**sv2**) — extracción multi-IA (OpenAI, Gemini,
  Claude, Document AI, Document Intelligence). API FastAPI :8000 + worker.
- `services/albaranes-persistencia/` (**sv3**) — dueño del schema
  PostgreSQL: persiste raw+merge, sube a SharePoint, enriquece con
  contratos de sigrid-api. API :8001 + worker.
- `services/albaranes-front/` (**sv4**) — front de revisión/aprobación
  (FastAPI + Jinja2, :8004). Lee/escribe el merge, publica a 3 colas.
- `services/albaran-valoracion-api/` (**sv5**) — motor IA de valoración.
  Solo HTTP (:8002), BBDD en solo lectura, NO persiste.
- `services/albaran-valoracion-persist/` (**sv6**) — valorador: consume
  `q-valoracion`, llama a sv5, aplica reglas deterministas y persiste
  (replace transaccional). API :8003 + worker.
- `services/albaranes-comun/` — librería `ruesma_comun` compartida (colas,
  blobs, Graph/SharePoint, clientes LLM, workflows). `pip install -e`; los
  nombres canónicos de colas y los contratos de mensajes viven aquí.
- `infra/` — scripts az CLI de provisión y despliegue (Container Apps).
  `infra/docs/levantar-pipeline-local.md` = cómo levantar todo en local
  con Azurite. Los `infra/*.local.ps1` (no versionados) llevan los IDs
  reales; los versionados van redactados.
- Estructura interna de cada servicio: hexagonal (`domain/`,
  `application/`, `infrastructure/`, `interface_adapters/`).
- `tests/` (raíz) — tests del monorepo como conjunto; los de cada servicio
  viven en su carpeta. Los unit tests NO tocan red ni BBDD.
- `specs/` — especificaciones SDD (una carpeta por feature).
- `progress/` — memoria externa del arnés (`current.md`, `history.md`,
  informes `impl_*.md` / `review_*.md` / `explore_*.md` por subagente).
- `docs/` — `ARCHITECTURE.md`, `CONVENTIONS.md`.
- `docs/referencia/` — documentación de negocio y de sistemas origen que
  llega de fuera, siempre en Markdown. Consúltala cuando la pregunta sea
  «por qué el código hace esto» y la respuesta no esté en el código. Ver su
  `README.md`.
- `CHECKPOINTS.md` — criterios objetivos de estado final; el reviewer los
  recorre antes de cerrar cualquier feature.
- `BACKLOG.md` — el backlog en Markdown (estado, prioridad, rigor y
  descripción de cada feature). **Generado** por `harness/backlog.py` desde
  `harness/features.json` y regenerado por `harness/init.sh`: no lo edites a
  mano ni respondas al humano «déjame mirar el JSON», está aquí.
- `harness/ARNES_VERSION.md` — qué versión del arnés genérico lleva este
  repositorio. Lo escribe el instalador; no lo edites a mano.
- `infra/` — scripts de despliegue (si aplica).

## Documentos que llegan de fuera (PDF y ofimática)

Cuando el humano pase un PDF —o un `.docx`, `.xlsx`, `.pptx`— conviértelo a
Markdown y guárdalo en `docs/referencia/` antes de trabajar con él. El
original NO se versiona: al repositorio entra solo el Markdown.

- La conversión se hace **siempre con la herramienta MCP `markitdown`**, no
  leyendo el documento por tu cuenta. Única excepción: que el humano lo
  indique explícitamente en esa petición.
- Si `markitdown` no está conectada, **PARA y dilo**. No improvises otra vía
  de conversión: el resultado saldría distinto según quién lo convierta y el
  Markdown va a quedar versionado en git.
- Nombra el fichero según la convención de `docs/referencia/README.md` y
  ponle la cabecera con origen y fecha del documento.
- Si el documento trae datos sensibles (precios de proveedor, datos
  personales, credenciales), **no lo conviertas sin preguntar**: acabaría
  versionado en git.

## Reglas duras (no negociables)

- PROHIBIDO marcar una feature como `done` sin que `bash harness/init.sh`
  termine en verde (incluye tests) y sin veredicto APROBADO del reviewer
  contra `CHECKPOINTS.md`.
- PROHIBIDO tocar `.env` o subirlo a git. Los secretos no se escriben en
  ningún fichero del repo ni en specs ni en progress.
- Sigrid (ERP) SOLO se consulta vía sigrid-api y SOLO lectura. Nadie se
  conecta por SQL directo al SQL Server de Sigrid.
- Desde local, contra los recursos reales de Azure (BBDD `albaranes`,
  buzón M365, SharePoint, colas de producción): **solo lectura**. Las
  colas y blobs se simulan con Azurite en local
  (`infra/docs/levantar-pipeline-local.md`); la escritura real solo
  ocurre desplegado o con autorización expresa del humano.
- Desplegar (`infra/deploy.ps1`, `az acr build`, `az containerapp ...`)
  lo pide el humano; los agentes no lo lanzan por su cuenta.
- Cada feature se desarrolla en su rama `feature/F-XXX-slug`. Nunca commits
  directos a `dev` ni a `main`.
- ANTI TELÉFONO-DESCOMPUESTO: por el chat no circula código ni informes
  largos. Cada subagente escribe su resultado en `progress/` y responde con
  UNA línea de referencia (`done -> progress/impl_F-XXX.md`). Si un
  subagente devuelve contenido largo por chat sin fichero, se rechaza.
- Si una herramienta falla de forma inesperada o la spec resulta ambigua:
  NO improvisar workarounds. Marcar la feature `blocked`, anotar el motivo
  en `progress/current.md` y parar.
- Los agentes ejecutan `bash harness/init.sh` tal cual, sin pipes, tail,
  variables ni decoración (la allowlist de permisos cubre el comando limpio).
- Convenciones de código: `docs/CONVENTIONS.md`. Arquitectura:
  `docs/ARCHITECTURE.md`. Léelos antes de diseñar o implementar.
- LÍMITE DE SERVICIO (adaptación monorepo): este repo contiene LOS
  servicios del pipeline de albaranes, pero cada servicio conserva UNA
  responsabilidad acotada. Toda feature declara qué servicio(s) toca; la
  lógica compartida va a `services/albaranes-comun`, nunca copiada entre
  servicios. Si una feature exige una responsabilidad nueva (otro dominio,
  integración con vida propia), se marca `blocked` y se propone al humano:
  servicio nuevo aquí o proyecto aparte.
- Los agentes NO hacen `git push` ni crean PRs salvo petición explícita del
  humano. Commits locales sí, según protocolo del implementer.

<!-- ==================== INICIO · ENTORNO DE RUESMA ==================== -->
<!-- Esta sección NO es del arnés: describe convenios de la organización    -->
<!-- Construcciones Ruesma. Si instalas el arnés fuera de ese entorno,      -->
<!-- BORRA el bloque entero, desde este comentario hasta el de cierre.      -->

## Convenios del entorno de Ruesma

### El ecosistema: `azure-apps/`

`C:\Users\pgris\PycharmProjects\azure-apps` es un repositorio git con un
documento por proyecto del ecosistema, explicando qué expone cada uno, qué
consume y qué se rompe si cambia.

**Consúltalo antes de diseñar nada que cruce la frontera del proyecto**: una
llamada a otro servicio, una base de datos compartida, un registro de
contenedores común.

Dos reglas: el documento de este proyecto **se actualiza cuando cambie lo que
exponemos o consumimos**, en el mismo trabajo y no después; y **no se
duplican aquí** los documentos de otros proyectos, se enlazan.

Además de un documento por proyecto, `azure-apps/` guarda la **documentación
del sistema origen común**: `sigrid_api.md` (la pasarela) y
`sigrid_tablas.md` (el diccionario completo de la BBDD de Sigrid, tablas,
campos, tipos e índices). Cuando necesites saber qué es una tabla o un campo
de Sigrid, ve ahí; en `docs/referencia/` de cada proyecto solo hay punteros.

### El arnés genérico: `arnes-base`

Este arnés no nació aquí. Su versión genérica y reutilizable vive en
`C:\Users\pgris\PycharmProjects\arnes-base` (repositorio git versionado), y
desde ahí se instala y se actualiza en los demás repositorios. La versión
instalada consta en `harness/ARNES_VERSION.md`.

**Regla de propagación (obligatoria).** Si mejoras algo del arnés
—`CLAUDE.md`, `.claude/agents/`, `CHECKPOINTS.md`, `harness/init.sh`,
`specs/SPECS.md`, las convenciones— y esa mejora **vale para cualquier
proyecto**, la portas a `arnes-base` **en el mismo trabajo**, no después. Si
es específica de este proyecto, se queda aquí.

No es una recomendación: el 2026-08-08 se perdieron **cinco mejoras del arnés
en una sola tarde** porque `arnes-base` era una copia suelta sin versionar y
nadie la refrescó. Es la misma regla de propiedad que rige `azure-apps`.

<!-- ===================== FIN · ENTORNO DE RUESMA ====================== -->
