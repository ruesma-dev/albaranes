# Levantar el pipeline de albaranes en local (orden, venvs y .env)

Flujo por colas (Azurite):

```
sv1 ──q-extraccion──▶ sv2 ──q-persistencia──▶ sv3 ──q-valoracion──▶ sv6 ──HTTP──▶ sv5
(buzón)              (IA)                   (persist+Sigrid)     (valora+persist) (matching Claude)

sv4 (portal) publica q-persistencia (re-fetch), q-valoracion (valorar), q-feedback (aprobar)
sv7 = orquestador antiguo, DISUELTO → no se levanta
```

Las colas **almacenan** los mensajes, así que el orden no es crítico; aun
así conviene arrancar los **consumidores antes** que el productor (sv1).

---

## 0. Infra (una vez, siempre encendida)

- **Azurite** (colas + blobs):
  ```powershell
  azurite --silent --location C:\azurite
  ```
- **Postgres** dev (el que ya usa sv1). Cada servicio con BBDD apunta con
  sus `PG_*`.

---

## 1. Instalación por servicio (cada proyecto tiene su `.venv`)

En la Terminal de PyCharm de **cada** proyecto (con su `.venv` activo):

```powershell
# Paquete común (editable). Trae httpx, sqlalchemy, pydantic, azure-storage-*.
pip install -e C:\Users\pgris\PycharmProjects\albaranes-comun
# Deps propias del servicio.
pip install -r requirements.txt
```

**Excepción IA** — sv2 y sv5 usan `ruesma_comun.llm.*`, así que instala el
común con el extra `[llm]` (añade anthropic/openai/google-genai):

```powershell
pip install -e "C:\Users\pgris\PycharmProjects\albaranes-comun[llm]"
```

Notas:
- **sv5 y sv6 no traían `requirements.txt`**: se añaden en este entregable.
- **sv3** ya lista sus extras (markitdown/mammoth/xhtml2pdf) en su
  `requirements.txt`. Para convertir contratos Word→PDF puede necesitar
  **LibreOffice** instalado en Windows (según `WORD_TO_PDF_BACKEND`); si esa
  parte falla, revísalo (no bloquea el resto del pipeline).

---

## 2. Añadidos al `.env` (local)

Lo que ya tienes de Azure (PG_*, claves IA, `SIGRID_API_*`, `SHAREPOINT_*`,
`GRAPH_KEY`) sigue valiendo. Para local añade:

| Servicio | Añadir al `.env`                                                                 |
|----------|----------------------------------------------------------------------------------|
| sv1      | `COLAS_CONNECTION_STRING=<Azurite>`                                               |
| sv2      | `COLAS_CONNECTION_STRING=<Azurite>` (sv2 **no** usa BBDD)                         |
| sv3      | `COLAS_CONNECTION_STRING=<Azurite>` · `VALUATION_TRIGGER_ENABLED=false`           |
| sv4      | `COLAS_CONNECTION_STRING=<Azurite>` (con ella, sv4 corre CON colas, no solo-front)|
| sv5      | *(nada nuevo: no usa colas; lee todo de Settings/.env)*                           |
| sv6      | `COLAS_CONNECTION_STRING=<Azurite>` · `VALUATION_API_BASE_URL=http://127.0.0.1:8002` |

`<Azurite>` es la cadena de desarrollo:
```
DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1
```

- Con `COLAS_CONNECTION_STRING` basta también para **blobs** (`input/`,
  `envelopes/`): el BlobEndpoint se deriva de la misma cadena.
- `VALUATION_TRIGGER_ENABLED=false` en sv3 evita duplicar la valoración (ya
  la dispara el trigger de cola q-valoracion).
- Puertos por defecto: **sv5 = 8002**, **sv4 = 8004** (no chocan).

**`load_dotenv`**: para que el `.env` llegue a `os.environ` (donde leen los
builders de `ruesma_comun`):
- sv1 ✔ (ya), sv2/sv3/sv6 ✔ (ya, en `main_worker.py`), **sv4 ✔ (este ZIP)**.
- sv5 no lo necesita (no usa esos builders).

---

## 3. Orden de arranque y comando

| Orden | Servicio | Proyecto                     | Comando                 | Rol                                  |
|:-----:|----------|------------------------------|-------------------------|--------------------------------------|
| 1     | **sv5**  | albaran-valoracion-api       | `python main.py`        | API matching (Claude), HTTP :8002    |
| 2     | **sv6**  | albaran-valoracion-persist   | `python main_worker.py` | Worker q-valoracion → llama sv5, persiste |
| 3     | **sv3**  | albaranes-persistencia       | `python main_worker.py` | Worker q-persistencia → q-valoracion |
| 4     | **sv2**  | albaranes-api                | `python main_worker.py` | Worker q-extraccion → q-persistencia |
| 5     | **sv4**  | albaranes-front              | `python main.py`        | Portal, HTTP :8004                   |
| 6     | **sv1**  | albaranes-email              | `python main.py`        | Productor: buzón → q-extraccion      |

- **sv2, sv3, sv6 se lanzan como WORKER** (`main_worker.py`), no como su
  `main.py` (ese es el servidor HTTP, no consume cola).
- **sv5** sí como `main.py` (es API HTTP que consume sv6).
- **sv7 no se levanta.**
- Cada servicio en su propio proceso/consola con su `.venv` y su `.env`.

Las colas se crean solas al primer publish/consume. Si quieres dejarlas
listas: `az storage queue create --name q-extraccion --connection-string "<Azurite>"`
(y `q-persistencia`, `q-valoracion`, `q-feedback`).

---

## 4. Prueba de humo

1. Infra arriba (Azurite + Postgres).
2. sv5 → sv6 → sv3 → sv2 → sv4 → sv1 arrancados (orden de la tabla).
3. Llega un correo con albarán → sv1 lo sube a `input/` y publica
   q-extraccion → sv2 extrae (IA) → sv3 persiste + Sigrid → q-valoracion →
   sv6 valora (llamando a sv5) → el documento aparece valorado en sv4 para
   revisar/aprobar.
4. En sv4: elegir contrato → guarda → refetch (sv3) → valorar → sv6/sv5 →
   refresco.

---

## Resumen

- **Instalar**: `pip install -e ..\albaranes-comun` (+ `[llm]` en sv2/sv5) y
  `pip install -r requirements.txt` en cada `.venv`.
- **.env**: sobre todo `COLAS_CONNECTION_STRING` (Azurite) en
  sv1/sv2/sv3/sv4/sv6; `VALUATION_API_BASE_URL` en sv6; `VALUATION_TRIGGER_
  ENABLED=false` en sv3.
- **Arrancar**: sv5, sv6(worker), sv3(worker), sv2(worker), sv4, sv1.
