# Probar el adaptador de colas contra Azurite (local, Windows)

Esto valida lo que sustituye a las llamadas HTTP entre servicios: publicar y
consumir mensajes en **Azure Storage Queues**, con reintentos y cola *poison*,
exactamente igual que se comportará en Azure Container Apps (allí sin claves,
con managed identity).

> Yo aquí he validado la **lógica** del adaptador con un cliente de cola en
> memoria (4 escenarios en verde: encadenado, reintento→poison, cuerpo
> inválido→poison, serialización). Estos pasos hacen el **e2e real contra
> Azurite** en tu máquina.

## 0) Qué se entrega
Paquete `ruesma_comun/colas/` (en el proyecto **comun**):
- `mensajes.py` — mensajes tipados (Pydantic). Regla: **1 mensaje = `{document_id}`**;
  el PDF NUNCA viaja en el mensaje (va por referencia a SharePoint vía BBDD).
- `conexion.py` — `FabricaColas`: cadena de conexión (Azurite/local) **o**
  `account_url` + managed identity (nube). Nombres canónicos de las colas.
- `publicador.py` — `PublicadorColas` (sustituye los clientes HTTP de salida).
- `consumidor.py` — `ConsumidorCola` (el "main loop" de cada worker: poison por
  reintentos/cuerpo inválido, reintento por visibilidad, parada limpia con SIGTERM).
- `__init__.py` — API pública del paquete.
- `demo_colas.py` (en la raíz de comun) — el test e2e contra Azurite.

**Borra** la carpeta antigua `ruesma_comun/queue/` si sigue en tu comun (era un
borrador en inglés ya sustituido por `colas/`).

## 1) Instalar Azurite (una vez)
Opción A — npm (necesita Node.js):
```powershell
npm install -g azurite
```
Opción B — Docker:
```powershell
docker run -d --name azurite -p 10001:10001 mcr.microsoft.com/azure-storage/azurite azurite-queue --queueHost 0.0.0.0 --skipApiVersionCheck
```
Opción C — extensión "Azurite" de VS Code (botón "Azurite Queue Service" en la barra inferior).

## 2) Arrancar Azurite (solo el servicio de colas)
En una consola aparte (déjala abierta):
```powershell
azurite-queue --silent --location C:\azurite --queuePort 10001 --skipApiVersionCheck
```
> El flag `--skipApiVersionCheck` evita el error *"The API version ... is not
> supported by Azurite"* cuando el SDK manda una versión de API más nueva que
> la que soporta tu Azurite. Es solo cosa del emulador local; en Azure real no
> hace falta. (Alternativa: `npm i -g azurite@latest` para actualizarlo.)
Debe decir: `Azurite Queue service successfully listens on http://127.0.0.1:10001`.

## 3) Instalar comun en un venv y lanzar el demo
En **otra** consola, desde la carpeta del proyecto comun:
```powershell
cd C:\Users\pgris\PycharmProjects\comun
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .                 # instala ruesma_comun + deps (pydantic, azure-storage-queue...)
python demo_colas.py
```

## 4) Salida esperada
```
=== ESCENARIO 1: encadenado de colas ===
[colas] publicado tipo=extraccion document_id=DOC-1001 → q-extraccion
[sv2] extrae document_id=DOC-1001 -> q-persistencia
...
ESCENARIO 1 OK: 3 docs fluyeron extraccion -> persistencia

=== ESCENARIO 2: reintento + poison ===
[falla] intento=1 document_id=DOC-FALLO
[falla] intento=2 document_id=DOC-FALLO
[falla] intento=3 document_id=DOC-FALLO
[consumidor] → poison cola=q-valoracion motivo=dequeue_count=4 supera el máximo (3) ...
ESCENARIO 2 OK: reintentado 3 veces y movido a poison

TODOS LOS ESCENARIOS OK
```
Código de salida 0 = todo bien. Si ves `No conecto con Azurite (...). ¿Levantado
en :10001?` → Azurite no está arrancado o escucha en otro puerto.

## 5) (Opcional) Ver las colas
Con **Azure Storage Explorer** → "Attach to a local emulator" → verás las colas
`q-extraccion`, `q-persistencia`, `q-valoracion` y sus `-poison`. Tras el demo
quedan vacías (el demo limpia al empezar cada escenario).

## 6) Cómo lo usarán los servicios (siguiente paso)
- **Local**: variable de entorno
  `COLAS_CONNECTION_STRING` = la cadena de Azurite (está como
  `AZURITE_CONNECTION_STRING` en `conexion.py`).
- **Nube (ACA)**: `COLAS_ACCOUNT_URL = https://<cuenta>.queue.core.windows.net`
  y el rol *Storage Queue Data Contributor* en la identidad del Container App
  (sin secretos). El código es el mismo en los dos sitios.

El cableado de sv7→workers (productor en sv1, consumidor en sv2, etc.) es el
paso siguiente; necesito tu `sv7.zip` (esta vez no llegó la subida) para
mapear sus pasos a publicar/consumir sin inventar.
