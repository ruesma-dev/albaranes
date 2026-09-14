# Fase 2 — parte 2: Container Apps del núcleo (sv5, sv6, sv2, sv3)

## Redespliegue del día a día (lo habitual)

```powershell
. .\00_vars.ps1
.\deploy.ps1                    # build de los 6 + update, tag por fecha
.\deploy.ps1 -Only sv4,sv6      # solo esos
.\deploy.ps1 -SkipBuild         # re-apunta a $IMG sin reconstruir
.\check_deploy.ps1 -ConModelos  # qué corre de verdad ahora mismo
```

`deploy.ps1` genera un tag **por fecha** (`r20260724-1530`), construye, verifica
que el tag existe en ACR, actualiza cada app con `--revision-suffix` y deja
todas en modo de revisión **single**. Reglas aprendidas a base de perder
mañanas (24-jul-2026):

- **Nunca reescribas un tag** (`v2`, `v3`…). La revisión activa de una
  Container App conserva el **digest** con el que nació: si reescribes el tag,
  el ACR tiene código nuevo pero Azure sigue ejecutando el viejo. Síntoma
  clásico: «en local va bien y desplegado se comporta raro».
- **Nombres de app**: viven en `$APPS` (`00_vars.ps1`). Ojo, `rg-partes-dev`
  tiene apps con el **mismo nombre** para el pipeline de partes; pasa siempre
  `-g $RG`.
- **Nada de `foreach` con `az containerapp`** sin fijar
  `$ErrorActionPreference = "Continue"`: la extensión escribe avisos por stderr
  y el bucle muere en la primera iteración *sin decir nada* (se actualizaba
  solo el primer servicio).
- **`comun` no tiene imagen propia**: `build_images.ps1` lo copia fresco desde
  `services/albaranes-comun` a cada contexto. Por eso, si tocas `comun`, hay
  que reconstruir **todos** los servicios que lo usan (sv2, sv3, sv5, sv6),
  aunque su código propio no haya cambiado.
- **`replicas 0` en sv3/sv6 es normal**: son workers KEDA escalados a cero.

### Lo que costó dos meses (14-sep-2026)

Tres fallos encadenados hacían que el despliegue «funcionara» sin desplegar
nada de lo desarrollado desde julio. Ya están corregidos; quedan aquí para que
no se repitan:

- **El build leía de los repositorios ARCHIVADOS.** `$ProjectsRoot` estaba
  escrito a mano como `C:\Users\pgris\PycharmProjects`, así que cada servicio
  se cogía de la carpeta hermana previa a la migración al monorepo (cuatro de
  ellas con «ARCHIVADO: migrado al monorepo albaranes» como último commit).
  Ahora la raíz se **deriva de la ubicación del script** (`<repo>\services`) y
  una guarda hace **fallar el build en seco** si alguna carpeta fuente cae
  fuera de ese `services\`. Para construir a propósito desde fuera:
  `-PermitirFuenteExterna` (avisa por pantalla).
- **`-Only` no llegaba al build.** `.\deploy.ps1 -Only sv3` construía los seis
  y solo filtraba el update. Ahora `deploy.ps1` se lo pasa a `build_images.ps1`,
  que también acepta `-Only sv1..sv6`.
- **La suscripción no se cargaba.** `00_vars.ps1` fija marcadores
  `REDACTADO-VER-COPIA-LOCAL` y **nunca** cargaba `00_vars.local.ps1` (que
  existe, no se versiona y trae los valores reales). `az account set` fallaba
  con «The subscription of 'redactado-ver-copia-local' doesn't exist in cloud
  'AzureCloud'» y todo seguía **por casualidad**, contra la suscripción activa
  de la consola. Ahora `00_vars.ps1` carga el `.local` al final, avisa en rojo
  si tras eso la suscripción sigue redactada, y `build_images.ps1` se niega a
  construir en ese estado.

Moraleja operativa: **`az acr build` en verde no prueba que se haya construido
lo que crees**. Antes de dar por bueno un despliegue, comprueba en la app algo
que solo exista en el código nuevo.

### Cambiar modelo LLM sin reconstruir

```powershell
.\set_models.ps1 -Anthropic claude-opus-4-7
```

Toca sv2 (los tres proveedores) y sv5 (solo Claude). Persiste solo hasta la
próxima recreación: fija también `$ANTHROPIC_MODEL` en `create_capps.ps1`.

**Modelos probados** (24-jul-2026): `claude-sonnet-4-6` estable;
`claude-opus-4-7` devolvía el JSON doblemente anidado y tumbaba sv5 con un
400 — absorbido desde entonces por `comun/llm/json_coercion.py`. Al cambiar
de modelo, **valora un albarán y mira el log de sv5**: los warnings
`[json-coercion]` indican que el modelo devuelve el JSON deformado (se
corrige solo, pero conviene saberlo).
Desde **Opus 4.7** los modelos rechazan `temperature`/`top_p`/`top_k` (error
400) y solo admiten *adaptive thinking*; el cliente de `comun` no envía ninguno
de esos parámetros, así que el cambio es seguro.

## Creación desde cero (solo la primera vez)

### Orden
```powershell
. .\00_vars.ps1
. .\00_capps_vars.ps1     # rellena antes el bloque $SP (SharePoint) con tu .env
.\create_capps.ps1
```
Prerrequisitos: imágenes en ACR (build_images.ps1), secretos en Key Vault
(add_secrets.ps1 + PG-PASSWORD), y `$SP` relleno.

## Qué crea
- **ca-sv5-valuation**: interno HTTP :8002, min 1 / max 3. Lo llama sv6.
- **ca-sv6-valorador**, **ca-sv2-extraccion**, **ca-sv3-persistencia**:
  workers, min 0 / max 5, con **KEDA** escalando por su cola.
- Todos con la managed identity, secretos por **Key Vault reference** y los
  endpoints de storage por **identidad** (COLAS_ACCOUNT_URL/BLOBS_ACCOUNT_URL +
  AZURE_CLIENT_ID), sin connection strings.

## Cosas a vigilar en el primer arranque (mira los logs en Log Analytics)
1. **Comando de los workers**: se sobrescribe a `python main_worker.py` con
   `--command python --args main_worker.py`. Si algún worker arranca el HTTP en
   vez del worker, ese override no se aplicó.
2. **KEDA + identidad**: los workers están a min-replicas=0; deben escalar a 1
   al encolar. Si no escalan, revisa que la MI tenga *Storage Queue Data
   Contributor* (la asignó Fase 1) y el `--scale-rule-identity`.
3. **PostgreSQL SSL**: Azure PG Flexible exige TLS. psycopg3 por defecto
   negocia SSL ('prefer'); si ves error de SSL, lo ajustamos (sslmode).
4. **sv6 -> sv5 interno**: sv6 llama a `https://<fqdn-interno-sv5>`. Si da error
   TLS/conn, revisamos transporte del ingress interno.
5. **GRAPH_KEY**: va como JSON por Key Vault; la app lo parsea. Si el secreto
   no es el JSON correcto, sv3/sv5 fallarán al tocar SharePoint.

## Probar el pipeline desplegado
Sube un PDF a `input/<id>.pdf` (seed) y encola en `q-extraccion` (puedes usar
los scripts seed_input.py / encolar_extraccion.py apuntando con
BLOBS_ACCOUNT_URL/COLAS_ACCOUNT_URL a la cuenta real en vez de Azurite), o
espera a tener sv1 (productor) en la siguiente entrega.
