# email-albaranes-ingestor (Servicio 1 / sv1)

> **Microservicio orquestador de la ingesta de albaranes** del ecosistema Construcciones Ruesma.
> Hace *polling* a un buzón Microsoft 365 vía **Microsoft Graph**, descarga los adjuntos
> (PDFs e imágenes), los normaliza (split página a página en PDFs multipágina) y los reenvía
> a los servicios de **extracción** (Servicio 2) y **persistencia** (Servicio 3).

---

## 1. ¿Qué hace exactamente?

`email-albaranes-ingestor` es un **proceso de larga duración** (loop infinito) cuya única
responsabilidad es:

1. Vigilar una carpeta de un buzón M365 (por defecto `inbox`).
2. Detectar emails **no leídos con adjuntos**.
3. Por cada email candidato:
   - Listar adjuntos.
   - Filtrar por tipo (`.pdf`, `.jpg`, `.jpeg`, `.png`, `.webp`) y por tamaño (≤ `MAX_ATTACHMENT_MB`).
   - Descargar el contenido binario.
   - Si es PDF de N páginas, **trocearlo en N "documentos lógicos" de 1 página cada uno**.
   - Llamar a **Servicio 2** (`POST` multipart) → recibe el envelope JSON con la extracción.
   - Llamar a **Servicio 3** (`POST` multipart) → persiste el documento + extracción + contexto del email.
4. Mover el email a la carpeta **`Procesados`** si todo fue bien, o a **`Errores`** si algo falló.
5. Esperar `POLL_INTERVAL_S` segundos y repetir.

> No persiste nada por sí mismo: es un **orquestador stateless** sobre M365 + dos servicios HTTP.
> El propio buzón actúa como cola de trabajo: si el email sigue en `inbox` sin leer, está
> pendiente; si está en `Procesados`/`Errores`, ya tiene desenlace.

---

## 2. Lugar dentro del ecosistema (6 microservicios)

```
        ┌──────────────────────────┐
        │   Buzón M365 (Graph)     │
        │   dev@ruesma.es / inbox  │
        └─────────────┬────────────┘
                      │  poll cada 60s
                      ▼
   ┌──────────────────────────────────────┐
   │   sv1 · email-albaranes-ingestor     │  ← ESTE SERVICIO
   │   (orquestador, stateless)           │
   └────────────┬───────────────┬─────────┘
                │ POST multipart │ POST multipart
                ▼                ▼
   ┌─────────────────────┐  ┌────────────────────────┐
   │ sv2 · extractor     │  │ sv3 · persister        │
   │ /v1/albaranes/      │  │ /v1/albaranes/persist  │
   │ extract             │  │                        │
   └─────────────────────┘  └────────────┬───────────┘
                                          │
                                          ▼
                                 (BD destino, blob, etc.)
```

`sv1` es el **único** punto de contacto con Microsoft Graph. El resto de servicios no saben
nada de emails: reciben ficheros con su contexto.

---

## 3. Arquitectura interna (Hexagonal / Clean)

El proyecto sigue una arquitectura limpia con separación estricta de capas:

```
email-albaranes-ingestor/
├─ main.py                                  # Composition root (wiring de dependencias)
├─ config/
│  ├─ settings.py                           # pydantic-settings (.env)
│  └─ logging_config.py                     # RotatingFileHandler + consola
├─ domain/
│  ├─ models/
│  │  └─ email_models.py                    # EmailMessage, EmailAttachment (dataclasses inmutables)
│  └─ ports/                                # Interfaces ABC (contratos)
│     ├─ mailbox_client.py                  # Puerto: buzón M365
│     ├─ extraction_client.py               # Puerto: servicio extractor
│     └─ persistence_client.py              # Puerto: servicio persistencia
├─ application/
│  └─ pipelines/
│     └─ polling_pipeline.py                # Patrón Pipeline + run_forever
└─ infrastructure/                          # Adaptadores concretos
   ├─ graph/
   │  ├─ token_provider.py                  # OAuth2 client_credentials + cache + backoff
   │  └─ mail_client.py                     # Microsoft Graph v1.0 (REST)
   ├─ document/
   │  └─ pdf_page_splitter.py               # pypdf · separación página a página
   └─ http/
      ├─ service2_http_client.py            # Cliente HTTP del extractor (sv2)
      └─ service3_http_client.py            # Cliente HTTP del persister (sv3)
```

### Patrones aplicados

| Patrón                  | Dónde                                       | Por qué                                                           |
|-------------------------|---------------------------------------------|-------------------------------------------------------------------|
| **Hexagonal / Ports & Adapters** | `domain/ports` ↔ `infrastructure/*` | Permite cambiar Graph por IMAP, o sv2/sv3 por SDKs sin tocar la lógica. |
| **Pipeline**            | `PollingPipeline.run_forever`               | Pasos encadenados: list → filter → download → split → extract → persist → move. |
| **Composition root**    | `main.py`                                   | Único sitio donde se construyen e inyectan dependencias.          |
| **Retry con backoff exponencial + jitter** | `GraphTokenProvider`         | Tolerancia a 429/5xx en login.microsoftonline.com.                |
| **Token caching**       | `GraphTokenProvider`                        | Evita pedir token a AAD en cada llamada.                          |
| **Frozen dataclasses**  | dominio + `PreparedDocument`                | Inmutabilidad → razonamiento sencillo.                            |

---

## 4. Flujo detallado de un ciclo (`_run_once`)

```
1. mailbox.list_unread_with_attachments(folder=SOURCE_FOLDER, top=MAX_EMAILS)
       └─ filtros OData: isRead eq false AND hasAttachments eq true
2. Por cada email:
   a) mailbox.list_attachments(message_id)
        ├─ Si falla → ok_email=False, list_attachments_failed=True
        └─ Si OK   → filtrar:
              · is_inline → descartar
              · @odata.type ≠ fileAttachment → descartar
              · extensión no soportada → descartar
              · size > MAX_ATTACHMENT_MB → ok_email=False
   b) Si no hay adjuntos relevantes → ok_email=False
   c) Por cada adjunto relevante:
       · mailbox.download_attachment_value(message_id, attachment_id)
       · pdf_splitter.split(filename, mime, bytes) → List[PreparedDocument]
              (PDF de N pág. → N PreparedDocument; otros → 1 PreparedDocument)
       · Para cada PreparedDocument:
            - extractor.extract(filename, mime, bytes)        → envelope JSON
            - persistence.persist(file, envelope, context)    → {"ok": true, "document_id": ...}
            - Si ok=false → RuntimeError (ok_email=False y al except)
   d) move_message(message_id, destino):
            - Procesados si ok_email=True
            - Errores en otro caso
3. sleep(POLL_INTERVAL_S) y vuelta a 1.
```

### Manejo de fallos

- **Transitorios** (`httpx.HTTPError`, `GraphTokenTransientError`) → log warning y siguiente ciclo.
- **No transitorios** dentro de un email → email a `Errores`, ciclo continúa.
- **Bootstrap** (verificar carpeta, crear `Procesados`/`Errores`) → se reintenta con `sleep_s`
  antes de iniciar el loop. Si es no recuperable, aborta.

### Trazabilidad

Para cada documento lógico se calculan **dos SHA-256**:

- `attachment_sha256`: hash del adjunto original tal cual viene del email.
- `document_sha256`: hash del PDF de una sola página (puede ser distinto al original si fue *split*).

Ambos viajan en el `context` que se envía al Servicio 3.

---

## 5. Contratos HTTP de salida

### 5.1 Hacia Servicio 2 (extractor)

```http
POST {SERVICE2_BASE_URL}{SERVICE2_EXTRACT_PATH}
Content-Type: multipart/form-data

file: <bytes del documento lógico (1 página si era PDF)>
```

**Respuesta esperada**: `200 OK` con `application/json` (cualquier dict). El servicio sv1
no inspecciona la estructura: la pasa íntegra al sv3 como `extraction_envelope`.

### 5.2 Hacia Servicio 3 (persister)

```http
POST {SERVICE3_BASE_URL}{SERVICE3_PERSIST_PATH}
Content-Type: multipart/form-data

file:            <bytes del documento lógico>
extraction_json: <JSON serializado del envelope que devolvió sv2>
context_json:    <JSON serializado del contexto de email/adjunto/documento>
```

**Estructura de `context_json`** que envía sv1:

```json
{
  "email": {
    "id": "AAMkAG...",
    "subject": "Albarán 12345",
    "sender": "proveedor@ejemplo.es",
    "receivedDateTime": "2026-05-02T10:23:45Z"
  },
  "attachment": {
    "id": "AAMkAG...",
    "name": "albaran.pdf",
    "contentType": "application/pdf",
    "size": 184321,
    "sha256": "<sha256 del adjunto original>",
    "page_number": 2,
    "page_count": 5,
    "was_split": true
  },
  "document": {
    "filename": "albaran__page_002_of_005.pdf",
    "mime_type": "application/pdf",
    "sha256": "<sha256 de la página individual>",
    "page_number": 2,
    "page_count": 5,
    "was_split": true,
    "source_attachment_filename": "albaran.pdf",
    "source_attachment_mime_type": "application/pdf",
    "source_attachment_sha256": "<sha256 del adjunto original>"
  }
}
```

**Respuesta esperada del sv3**: `200 OK` con `{"ok": true, "document_id": "..."}`. Si `ok=false`
sv1 considera el email fallido y lo manda a `Errores`.

---

## 6. Configuración (variables de entorno)

Todas las variables se cargan desde un `.env` en la raíz del proyecto vía `pydantic-settings`.

| Variable                 | Default                            | Descripción                                                                |
|--------------------------|------------------------------------|----------------------------------------------------------------------------|
| `MAILBOX_ADDRESS`        | `dev@ruesma.es`                    | Buzón a vigilar.                                                           |
| `GRAPH_KEY`              | *(obligatorio)*                    | **JSON o base64-JSON** con `tenant_id`, `client_id`, `client_secret`. Si llega un string plano lo trata como token ya emitido (modo dev). |
| `SOURCE_FOLDER`          | `inbox`                            | Carpeta origen (id o nombre conocido por Graph).                           |
| `FOLDER_PROCESADOS`      | `Procesados`                       | Carpeta destino tras éxito (se crea si no existe).                         |
| `FOLDER_ERRORES`         | `Errores`                          | Carpeta destino tras fallo (se crea si no existe).                         |
| `POLL_INTERVAL_S`        | `60`                               | Segundos entre ciclos.                                                     |
| `MAX_EMAILS`             | `10`                               | Tope de emails por ciclo (`$top` en Graph).                                |
| `MAX_ATTACHMENT_MB`      | `25`                               | Tamaño máximo permitido por adjunto.                                       |
| `SERVICE2_BASE_URL`      | `http://127.0.0.1:8000`            | URL base del extractor (sv2).                                              |
| `SERVICE2_EXTRACT_PATH`  | `/v1/albaranes/extract`            | Path del extractor.                                                        |
| `SERVICE2_TIMEOUT_S`     | `300`                              | Timeout HTTP de lectura para sv2 (la extracción puede ser lenta).          |
| `SERVICE3_BASE_URL`      | `http://127.0.0.1:8001`            | URL base del persister (sv3).                                              |
| `SERVICE3_PERSIST_PATH`  | `/v1/albaranes/persist`            | Path del persister.                                                        |
| `SERVICE3_TIMEOUT_S`     | `120` (acepta también `HTTP_TIMEOUT_S`) | Timeout HTTP para sv3.                                                |
| `GRAPH_TIMEOUT_S`        | `60` (acepta también `HTTP_TIMEOUT_S`)  | Timeout HTTP para Microsoft Graph y AAD.                              |
| `LOG_LEVEL`              | `INFO`                             | Nivel global de logging.                                                   |
| `LOG_DIR`                | `logs`                             | Carpeta donde se escribe `email_albaranes_ingestor.log`.                   |

### Ejemplo de `.env`

```dotenv
MAILBOX_ADDRESS=dev@ruesma.es
GRAPH_KEY={"tenant_id":"12d28010-...","client_id":"...","client_secret":"..."}
SOURCE_FOLDER=inbox
FOLDER_PROCESADOS=Procesados
FOLDER_ERRORES=Errores
POLL_INTERVAL_S=60
MAX_EMAILS=10
MAX_ATTACHMENT_MB=25
SERVICE2_BASE_URL=http://127.0.0.1:8000
SERVICE2_EXTRACT_PATH=/v1/albaranes/extract
SERVICE2_TIMEOUT_S=300
SERVICE3_BASE_URL=http://127.0.0.1:8001
SERVICE3_PERSIST_PATH=/v1/albaranes/persist
SERVICE3_TIMEOUT_S=120
GRAPH_TIMEOUT_S=60
LOG_LEVEL=INFO
LOG_DIR=logs
```

> El `GRAPH_KEY` admite también un JSON codificado en base64 (útil para
> Azure App Settings / Key Vault references).

---

## 7. Permisos de Microsoft Graph

La aplicación de Entra ID asociada a `client_id` necesita los siguientes permisos
**de aplicación** (Application, no Delegated) con consentimiento de admin:

- `Mail.ReadWrite` *(o como mínimo `Mail.Read` + `Mail.ReadWrite` para mover)*
- `Mail.ReadWrite.Shared` (si el buzón es compartido)
- *(opcional)* `User.Read.All`

> Es **imprescindible** poder mover mensajes (`POST /messages/{id}/move`) y crear carpetas
> (`POST /mailFolders`). Sin esos permisos, el servicio aborta en el bootstrap.

---

## 8. Cómo invocar este servicio

`email-albaranes-ingestor` **no expone API HTTP**. Es un proceso *daemon* que se invoca por
línea de comandos y mantiene un loop infinito hasta que se le envía `SIGINT`/`SIGTERM`.

### 8.1 Localmente (PyCharm / Windows)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt    # httpx, pydantic-settings, pypdf
copy .env.example .env             # rellenar GRAPH_KEY, etc.
python main.py
```

### 8.2 En Azure (despliegue objetivo)

Para un proceso de polling de larga duración hay dos opciones razonables sobre la *Landing Zone*
de Construcciones Ruesma:

1. **Container App** en el spoke DEV con un único *replica* y `minReplicas = maxReplicas = 1`.
2. **Azure Function** con *Timer Trigger* cada `POLL_INTERVAL_S` y `_run_once()` por invocación
   (requiere refactor del `run_forever` para que el ciclo sea idempotente y *single-shot*).

> **Recomendación:** dado que ya hay otra Function App planificada para `sigrid-api`, lo más
> coherente es **Container App** para `sv1` (mantiene `httpx` síncrono y el loop tal cual).
> Si se prefiere consolidar todo en Functions, hay que extraer `_run_once` como entry point
> reutilizable (esto sería un cambio de arquitectura, no un simple wrapping).

### 8.3 ¿Otro servicio puede "llamarle"?

No directamente, porque no expone endpoint. Sin embargo, **un actor externo influye en él**
de tres formas:

1. **Enviando emails al buzón** vigilado → eso es el "input" real.
2. **Cambiando manualmente** un email de `Errores` a `Inbox` y marcándolo como *no leído* →
   se reprocesa automáticamente en el siguiente ciclo (mecanismo de *replay* operativo).
3. **Ajustando el `.env`** (p. ej. `POLL_INTERVAL_S`, `MAX_EMAILS`) → requiere reinicio del proceso.

---

## 9. Inputs / Outputs del servicio

### Inputs
| Origen          | Naturaleza                  | Detalle                                                                |
|-----------------|-----------------------------|------------------------------------------------------------------------|
| Microsoft Graph | Emails con adjuntos         | Filtro: `isRead=false AND hasAttachments=true`, en `SOURCE_FOLDER`.    |
| `.env`          | Configuración estática      | Credenciales Graph + URLs de sv2/sv3 + límites.                        |

### Outputs
| Destino            | Naturaleza                       | Detalle                                                                                  |
|--------------------|----------------------------------|------------------------------------------------------------------------------------------|
| sv2 (HTTP)         | `POST` multipart con `file`      | 1 llamada por **documento lógico** (= 1 por página de PDF, o 1 por imagen).              |
| sv3 (HTTP)         | `POST` multipart con `file`+JSON | 1 llamada por **documento lógico**, sólo si la llamada a sv2 tuvo éxito.                 |
| Microsoft Graph    | `POST /messages/{id}/move`       | Mueve email a `Procesados` o `Errores`.                                                  |
| Filesystem (local) | Logs rotados                     | `logs/email_albaranes_ingestor.log` (5 MB × 5 backups).                                  |

> **Importante:** el servicio NO almacena ficheros en disco salvo los logs.
> Todo lo que descarga vive en memoria mientras se procesa.

---

## 10. Observabilidad

- **Logging** estructurado a fichero rotado + consola, con formato:
  `timestamp | LEVEL | logger | file:line | mensaje`.
- Cada ciclo loggea `Ciclo: emails candidatos=N`.
- Cada documento lógico loggea `Procesando documento lógico. file=... page=... split=...`
  y al finalizar `Documento lógico OK -> persistido. ... document_id=...`.
- Cada email loggea su movimiento final a `PROCESADOS` o `ERRORES`.
- En despliegue Azure, redirigir stdout a Log Analytics (Container App) o a Application Insights
  (Function App) cumple con la sección 5.2 del Documento de Diseño de la Landing Zone.

---

## 11. Decisiones técnicas relevantes

1. **Síncrono, no `asyncio`.** El cuello de botella es la latencia de sv2 (extracción ≈ varios
   segundos por documento). Un ciclo procesa pocos emails y mucho tiempo de espera; un modelo
   síncrono es más simple y se beneficia poco del async.
2. **`httpx` y no `requests`.** Permite `Timeout` granular (connect/read/write/pool) y
   trust_env (proxies corporativos).
3. **Split por página antes de extraer.** Cada página = 1 albarán es la convención del negocio.
   Esto permite que sv2 sea más simple (no tiene que devolver una lista de extracciones por página)
   y que sv3 persista un albarán por documento.
4. **El buzón actúa como cola.** No hace falta Service Bus, Storage Queue ni Cosmos para idempotencia.
   Lo único que importa es no procesar dos veces el mismo email (lo garantiza `isRead=false` +
   `move_message`).
5. **Retry sólo en el token AAD.** Las llamadas a Graph y a sv2/sv3 NO se reintentan dentro
   del ciclo: si fallan, el email se manda a `Errores`. Es deliberado para evitar duplicados
   en sv3 (no tenemos idempotency key todavía).

---

## 12. Limitaciones conocidas y mejoras propuestas

| # | Limitación                                                              | Mejora propuesta                                                                          |
|---|-------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| 1 | No idempotente entre sv1 y sv3 (un fallo en `move_message` reprocesaría) | Enviar `idempotency_key = sha256(email_id + page_number)` en `context` y que sv3 lo respete. |
| 2 | Sin reintentos de sv2/sv3                                               | Añadir reintento exponencial sólo para 5xx/timeout, manteniendo idempotency_key.          |
| 3 | `list_unread_with_attachments` usa `$top` sin paginación                | Si el buzón acumula >`MAX_EMAILS` no leídos, sólo procesa los más recientes.              |
| 4 | El loop bloquea si Graph cae más que `POLL_INTERVAL_S`                  | OK porque el sleep ocurre tras la excepción; pero conviene jitter para no martillear.    |
| 5 | Configuración estática (necesita reinicio para cambios)                 | Si pasamos a Container App, montar `.env` desde Key Vault references.                     |
| 6 | Logs sólo en disco                                                      | En Azure: `LogHandler` adicional hacia Application Insights / Log Analytics.              |

---

## 13. Resumen de un vistazo

| Característica         | Valor                                                                |
|-----------------------|-----------------------------------------------------------------------|
| Tipo                  | Daemon de polling (loop infinito)                                     |
| Lenguaje              | Python 3.12                                                           |
| Entrada               | Buzón M365 (Microsoft Graph)                                          |
| Salidas               | HTTP a sv2 (extracción) y sv3 (persistencia) + movimiento de emails   |
| Persistencia propia   | Ninguna (sólo logs)                                                   |
| Concurrencia          | Single-thread, secuencial                                             |
| Despliegue objetivo   | Azure Container App (recomendado) o Azure Function con Timer Trigger  |
| Punto de entrada      | `python main.py`                                                      |
| Dependencias clave    | `httpx`, `pydantic-settings`, `pypdf`                                 |

---

*Documento generado a partir del análisis del código del paquete `sv1.zip` aportado.*
