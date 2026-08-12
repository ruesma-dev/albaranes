# README.md — ruesma-albaranes-comun

Paquete interno con la **infraestructura y los contratos compartidos** del
sistema de albaranes. Aquí NO vive lógica de dominio de ningún servicio.
Resuelve la duplicación con deriva detectada en el análisis de código
(4 versiones de `token_provider`, 3 de `contexto_linea`, etc.).

## Contenido (entrega 1 de la Fase 0)

| Módulo | Qué es | Sustituye a |
|---|---|---|
| `ruesma_comun.graph.token_provider` | Token de Microsoft Graph (GRAPH_KEY JSON/base64, reintentos 429/5xx) | las 4 copias divergentes de sv1/sv3/sv4/sv5 (se adoptó la de sv3, la más completa) |
| `ruesma_comun.colas.mensajes` | Contratos Pydantic de los mensajes (`extraccion`, `persistencia`, `valoracion`, `feedback`) | los bodies HTTP entre servicios |
| `ruesma_comun.colas.conexion` | Fábrica de `QueueClient` (Azurite por connection string · managed identity en nube) + nombres canónicos de colas | — |
| `ruesma_comun.colas.publicador` | Publicador tipado + variante best-effort (filosofía sv4) | `HttpOrchestratorClient`, triggers HTTP entre servicios |
| `ruesma_comun.colas.consumidor` | Runtime de worker: visibilidad 600 s, poison a `dequeue_count>5`, mensajes corruptos a poison inmediato, parada limpia SIGTERM | el servidor HTTP como entrada + el `FailedWorkflowRetrier` de sv7 |
| `ruesma_comun.workflows` | Máquina de estados heredada de sv7 (enum + ORM `workflow_runs` + repositorio: creación idempotente por `correlation_key`, transiciones, fallos) | el motor de sv7 (que desaparece como proceso) |
| `ruesma_comun.db.session_factory` | SessionFactory canónico (el de sv3) + `SessionFactoryDesdeEngine` para tests | las 5 copias |
| `ruesma_comun.llm` *(entrega 2)* | Puerto `LlmVisionClient` (adjunto opcional), `LlmAttachment`, `RetryPolicy`, `LlmCallLogger` y los 3 clientes de visión (Claude con `tool_name` parametrizado, OpenAI, Gemini) | las 2 copias divergentes de sv2/sv5 (merge: base sv2 + fix adjunto-opcional de sv5) |
| `ruesma_comun.contratos.contexto_linea` *(entrega 2)* | Modelo compartido `ContextoLinea` del envelope | las 4 copias de sv2/sv3/sv5/sv6 |
| `ruesma_comun.sharepoint.GraphSharePointClient` *(entrega 3)* | Núcleo Graph/SharePoint: resolución site/drive (3 modos), carpetas, **subida** y **descarga** (bytes y texto) por path relativo, sharing link | el bloque casi idéntico de sv3 (sube) y sv5 (lee el contrato); sv4 era código muerto |
| `ruesma_comun.markdown` *(entrega 4)* | Conversión de contratos (PDF/Word) a **Markdown** con markitdown: `a_markdown`, `combinar_a_markdown` (conserva tablas de tarifas; degrada al texto de fallback) | — (capacidad nueva) |

Hecho en la **entrega 2**: capa LLM y `contexto_linea` migradas como
*reexports* de 3 líneas en los servicios. Hecho en la **entrega 3**: el
núcleo SharePoint/Graph extraído a `GraphSharePointClient`; los
adaptadores de sv3 (subida) y sv5 (lectura del contrato para valorar)
pasan a subclasearlo conservando byte a byte sus llamadas a Graph y sus
tipos de dominio. **sv4 NO se toca**: su `SharePointContratoPdfStorage`
ya era código muerto (sv4 delega en sv3 vía `Sv3RefetchClient`). Los SDKs
de IA son extra opcional: `pip install -e ".[llm]"` (sv2/sv5 ya los traen
en sus requirements). Pendiente real para la nube (Fases 2-3): los
adaptadores de ENTRADA por cola de cada worker.

## Instalación en local (PyCharm)

Colocar esta carpeta como `C:\Users\pgris\PycharmProjects\comun` y, en el
venv de CADA servicio:

```bash
pip install -e ..\comun           # editable: los cambios se ven al instante
pip install -e "..\comun[dev]"    # con pytest, para ejecutar los tests
```

En Docker lo instala el `Dockerfile` de cada servicio desde el contexto de
build (ver `local/preparar_contexto.ps1`).

## Configuración de colas en los servicios

Exactamente UNA de estas dos variables en el `.env` / secretos de ACA:

```ini
# Local (Azurite):
COLAS_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;

# Nube (managed identity, sin secreto):
COLAS_ACCOUNT_URL=https://stalbaranesruesma.queue.core.windows.net
```

(La AccountKey de arriba es la cuenta de desarrollo *well-known* de
Azurite, pública por diseño: no es un secreto real.)

## Probarlo (tests de humo)

```bash
# 1) Azurite (elige una):
docker compose -f local/docker-compose.azurite.yml up -d
#    o sin Docker:
npm i -g azurite && azurite-queue --queuePort 10001 --skipApiVersionCheck

# 2) Tests (colas reales contra Azurite + workflows sobre SQLite):
pytest tests/ -v
```

> `--skipApiVersionCheck` es necesario porque el SDK
> `azure-storage-queue` reciente habla una versión de API más nueva que
> la que Azurite valida. Contra Azure real no aplica.

Si Azurite no está levantado, los tests de colas se saltan (skip) y los
de workflows se ejecutan igualmente.

## Decisiones registradas

- **Tablas físicas `workflow_runs` / `workflow_step_history` se conservan**
  (no se renombran a `albaran_workflows`): la tabla compartida es el mismo
  esquema de sv7 → cero migración de datos locales.
- **Mensajes en JSON plano (sin base64)**: controlamos ambos extremos.
- **Reintentos = la cola** (visibilidad + `dequeue_count`), no un proceso:
  es el sustituto directo del `FailedWorkflowRetrier`.
- **Poison ⇒ `on_poison`** del servicio marca el estado `*_failed` en
  `workflow_runs` (mapa `ESTADO_FALLO_POR_COLA` en `workflows.estados`).
