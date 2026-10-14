<!-- progress/mutacion_F-053_v8.md -->
# F-053 v8 (Bloque H) · mutación de lo nuevo, a mano (T50)

Campaña **a mano** sobre lo que añade la v8: `usuario_sigrid`, `buscar_usuario` y el `usu` del adjunto en el cliente,
la normalización de R14 (Python y SQL), la rama R47–R48 del servicio (`_resolver_usuario`, el error y el adjunto),
`approved_by` en la reclamación, la variable renombrada y su aviso de arranque, y en sv4 `_reviewer_from_request`
y el PUT (R49), `puede_reintentar_adjunto`/`reintentar_adjunto_sigrid` y su ruta (R30), el `usu` del panel (R29),
la lectura de `approved_by` del alta y la plantilla. No se usó `python -m harness.mutacion --feature F-053`: su
informe por defecto es `progress/mutacion_F-053.md`, la campaña de la v7 con los 10 equivalentes que aceptó el
humano, y lo que se pide aquí es la tabla de lo nuevo con los fallos por fila.

**Método** (script en el scratchpad de la sesión, `mutar_v8.py`): cada mutante cambia UN trozo exacto (debe
aparecer una sola vez en el fichero), corre los tests de su servicio **sin `-x`** (`-rfE --tb=no`), cuenta los
fallos, apunta qué tests caen y restaura el fichero byte a byte (`git status` limpio al acabar). sv9: la suite
entera (`python -m pytest`, venv del árbol principal). sv4: los 7 ficheros de F-053 que tocan lo mutado
(`test_f053_r49_revisor`, `r30_reintentar_adjunto`, `r29_panel_usu`, `t20_rutas`, `t21_panel`,
`t25_supervivientes`, `t18_publicar`) con `.venv\Scripts\python`.

- **HEAD medido (pasada 1): `1b3c8e51db2692d9e1bc0c8ef395b8cba833f077`.** Supervivientes re-medidos en
  **`77b62577ea89912f61fbb171b5976d31cb0b59c4`** (solo añade tests: el código de producción es idéntico).
- **Línea base** (sin mutar, en `1b3c8e5`): sv9 **619 passed** en 24,5 s; sv4 (los 7 ficheros) **225 passed** en
  45,4 s. En `77b6257`: sv9 621 y sv4 231 (los tests nuevos).
- **Resultado: 64 mutantes, 64 aplicados. Pasada 1: 57 muertos, 7 vivos. Tras 5 tests nuevos: 62 muertos, 2
  equivalentes demostrados (RM5, `test_f053_v8_equivalentes.py`), 0 vivos sin test ni justificación.**
- **Tiempo total y workers**: en serie, **1 worker** (el propio árbol). Pasada 1: **2965,6 s** para los 64 mutantes
  (46,3 s por mutante; sv9 entero 23–62 s, los 7 ficheros de sv4 29–59 s). Re-medida de los 7 vivos: **347,0 s**.
- **Complemento**: desde la pasada 2 de la review, la evidencia de C4 bis es la campaña de la herramienta,
  `progress/mutacion_F-053_v8_arnes.md`. Esta tabla manual se conserva porque cubre la plantilla y el texto SQL, que
  la herramienta no muta.
- **Tests textuales**: el script separa los que miran el código como texto o su forma (`inspect.getsource`,
  firmas, `model_fields`, el SQL como constante, `.env.example` e `infra/`). **Ningún mutante muere solo por
  ellos**: en todos los muertos hay al menos un test de conducta (columna «conducta»). Los dos equivalentes no los
  mata ningún test, textual o no.

## Tabla

Texto COMPLETO de cada sustitución (⏎ = salto de línea; los espacios de sangría van tal cual). El bloque exacto, con su sangría, está en el anexo.

| # | fichero:línea | original | mutado | fallos (conducta) | veredicto |
|---|---|---|---|---|---|
| 1 | sv9/domain/services/usuario_sigrid.py:25 | `if texto.count("@") != 1:` | `if texto.count("@") < 1:` | 1 (1) | MUERTO |
| 2 | sv9/domain/services/usuario_sigrid.py:24 | `texto = (approved_by or "").strip()` | `texto = (approved_by or "")` | 3 (3) | MUERTO |
| 3 | sv9/domain/services/usuario_sigrid.py:28 | `if dominio.lower() != DOMINIO_RUESMA:` | `if dominio != DOMINIO_RUESMA:` | 3 (3) | MUERTO |
| 4 | sv9/domain/services/usuario_sigrid.py:30 | `if not local or len(local) > MAX_LOGIN:` | `if len(local) > MAX_LOGIN:` | 1 (1) | MUERTO |
| 5 | sv9/domain/services/usuario_sigrid.py:30 | `if not local or len(local) > MAX_LOGIN:` | `if not local or len(local) >= MAX_LOGIN:` | 1 (1) | MUERTO |
| 6 | sv9/domain/services/usuario_sigrid.py:12 | `MAX_LOGIN = 24` | `MAX_LOGIN = 25` | 2 (2) | MUERTO |
| 7 | sv9/domain/services/usuario_sigrid.py:32 | `    return local⏎` | `    return local.lower()⏎` | 2 (2) | MUERTO |
| 8 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:219 | `encontrado = str(filas[0].get("cod") or "").strip() if filas else ""` | `encontrado = str(filas[0].get("cod") or "") if filas else ""` | 2 (2) | MUERTO |
| 9 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:220 | `        return encontrado or None⏎` | `        return encontrado⏎` | 4 (4) | MUERTO |
| 10 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:218 | `filas = self._leer(SQL_BUSCAR_USUARIO, [cod], "f053-usuario", 2)` | `filas = self._leer(SQL_BUSCAR_USUARIO, [cod.lower()], "f053-usuario", 2)` | 1 (1) | MUERTO (cuerpo exacto; ver abajo) |
| 11 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:218 | `filas = self._leer(SQL_BUSCAR_USUARIO, [cod], "f053-usuario", 2)` | `filas = self._leer(SQL_BUSCAR_USUARIO, [cod], "f053-usuario", 1)` | 1 (1) | MUERTO (cuerpo exacto; ver abajo) |
| 12 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:71 | `SQL_BUSCAR_USUARIO = "SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?"` | `SQL_BUSCAR_USUARIO = "SELECT cod FROM dbo.usu WHERE cod = ?"` | 1 (1) | MUERTO (cuerpo exacto; ver abajo) |
| 13 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:261 | `            "usu": usu,` | `            "usu": usu.lower(),` | 1 (1) | MUERTO |
| 14 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:199 | `        if not numero:⏎            # Solo separadores: casaría con cualquier ``entref`` vacío.⏎            return []⏎` | *(nada)* | 3 (3) | MUERTO |
| 15 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:203 | `SQL_BUSCAR_ALBARANES, [cif, numero, referencia_externa],` | `SQL_BUSCAR_ALBARANES, [cif, referencia, referencia_externa],` | 2 (2) | MUERTO |
| 16 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:64 | `f"WHERE c.tip = 14 AND d.entcif = ? AND UPPER({_ENTREF_NORMALIZADO}) = ? "` | `f"WHERE c.tip = 14 AND d.entcif = ? AND {_ENTREF_NORMALIZADO} = ? "` | 3 (2) | MUERTO (cuerpo exacto; ver abajo) |
| 17 | sv9/domain/services/validador_alta.py:97 | `SEPARADORES_REFERENCIA = (" ", ".", "-", "/")` | `SEPARADORES_REFERENCIA = (" ", ".", "-")` | 8 (7) | MUERTO |
| 18 | sv9/domain/services/validador_alta.py:104 | `texto = (numero or "").upper()` | `texto = (numero or "")` | 3 (3) | MUERTO |
| 19 | sv9/domain/services/validador_alta.py:327 | `        usu=usu,⏎` | `        usu="",⏎` | 21 (20) | MUERTO |
| 20 | sv9/application/alta_sigrid_service.py:241 | `        if candidato is not None:⏎            try:` | `        if candidato is None:⏎            try:` | 79 (79) | MUERTO |
| 21 | sv9/application/alta_sigrid_service.py:248 | `            if cod:⏎                logger.info` | `            if True:⏎                logger.info` | 3 (3) | MUERTO |
| 22 | sv9/application/alta_sigrid_service.py:251 | `        if not self._respaldo:⏎            raise` | `        if self._respaldo:⏎            raise` | 74 (74) | MUERTO |
| 23 | sv9/application/alta_sigrid_service.py:138 | `self._respaldo = (usuario_respaldo or "").strip()` | `self._respaldo = (usuario_respaldo or "")` | 3 (3) | MUERTO |
| 24 | sv9/application/alta_sigrid_service.py:242 | `            try:⏎                cod = self._sigrid.buscar_usuario(candidato)⏎            except Exception as exc:  # noqa: BLE001 — R48: sin comprobar, no se atribuye⏎                raise UsuarioNoResuelto(⏎                    f"no se pudo leer dbo.usu: {type(exc).__name__}",⏎                ) from exc⏎` | `            cod = self._sigrid.buscar_usuario(candidato)⏎` | 2 (2) | MUERTO |
| 25 | sv9/application/alta_sigrid_service.py:274 | `                    EstadoAlta.ERROR, paso, motivos=(Motivo(MOTIVO_USUARIO, str(exc)),),⏎                ))⏎                return⏎` | `                    EstadoAlta.ERROR, paso, motivos=(Motivo(MOTIVO_USUARIO, str(exc)),),⏎                ))⏎` | 0 → 1 (1) | VIVO → MUERTO con test nuevo |
| 26 | sv9/application/alta_sigrid_service.py:392 | `usu = str((resultado.peticion or {}).get("usu") or "").strip()` | `usu = str((resultado.peticion or {}).get("usu") or "")` | 1 (1) | MUERTO |
| 27 | sv9/application/alta_sigrid_service.py:394 | `            if not usu:⏎                raise UsuarioNoResuelto("la petición guardada no lleva usu")⏎` | *(nada)* | 4 (4) | MUERTO |
| 28 | sv9/application/alta_sigrid_service.py:402 | `adjunto = ResultadoAdjunto(False, codigo=MOTIVO_USUARIO, mensaje=str(exc))` | `adjunto = ResultadoAdjunto(False, codigo=type(exc).__name__, mensaje=str(exc))` | 4 (4) | MUERTO |
| 29 | sv9/application/alta_sigrid_service.py:398 | `resultado.sigrid_con_ide, nombre, contenido, usu=usu,` | `resultado.sigrid_con_ide, nombre, contenido, usu=self._respaldo,` | 2 (2) | MUERTO |
| 30 | sv9/application/alta_sigrid_service.py:179 | `return self._procesar_alta(document_id, reclamacion.alta, reclamacion.approved_by)` | `return self._procesar_alta(document_id, reclamacion.alta, None)` | 8 (8) | MUERTO |
| 31 | sv9/domain/services/reclamacion.py:76 | `    if documento is None:⏎        return reclamacion⏎    return replace` | `    return replace` | 5 (5) | MUERTO |
| 32 | sv9/domain/services/reclamacion.py:78 | `    return replace(reclamacion, approved_by=documento.approved_by)` | `    return reclamacion` | 10 (10) | MUERTO |
| 33 | sv9/config/settings.py:61 | `Field("", alias="ALTA_SIGRID_USUARIO_RESPALDO")` | `Field("", alias="ALTA_SIGRID_USUARIO")` | 5 (5) | MUERTO |
| 34 | sv9/config/settings.py:61 | `Field("", alias="ALTA_SIGRID_USUARIO_RESPALDO")` | `Field("pgris", alias="ALTA_SIGRID_USUARIO_RESPALDO")` | 2 (2) | MUERTO |
| 35 | sv9/main_worker.py:114 | `if settings.desde is not None and not settings.usuario_respaldo.strip():` | `if settings.desde is not None and not settings.usuario_respaldo:` | 0 → 1 (1) | VIVO → MUERTO con test nuevo |
| 36 | sv9/main_worker.py:114 | `if settings.desde is not None and not settings.usuario_respaldo.strip():` | `if not settings.usuario_respaldo.strip():` | 2 (2) | MUERTO |
| 37 | sv9/interface_adapters/composition.py:60 | `usuario_respaldo=settings.usuario_respaldo,` | `usuario_respaldo="",` | 2 (2) | MUERTO |
| 38 | sv4/interface_adapters/web/app.py:469 | `        if propuesto and propuesto.strip():⏎            return propuesto.strip()` | `        if propuesto:⏎            return propuesto.strip()` | 0 | EQUIVALENTE (demostrado, ver abajo) |
| 39 | sv4/interface_adapters/web/app.py:469 | `        if propuesto and propuesto.strip():⏎            return propuesto.strip()` | `        if propuesto and propuesto.strip():⏎            return propuesto` | 1 (1) | MUERTO |
| 40 | sv4/interface_adapters/web/app.py:467 | `        if principal and principal.strip():⏎            return principal.strip()⏎        if propuesto` | `        if principal:⏎            return principal.strip()⏎        if propuesto` | 1 (1) | MUERTO |
| 41 | sv4/interface_adapters/web/app.py:757 | `                approved_by=_reviewer_from_request(request, approved_by),` | `                approved_by=approved_by.strip() or _reviewer_from_request(request),` | 2 (2) | MUERTO |
| 42 | sv4/interface_adapters/web/app.py:1209 | `        payload.approved_by = _reviewer_from_request(request, payload.approved_by)⏎` | *(nada)* | 3 (3) | MUERTO |
| 43 | sv4/interface_adapters/web/app.py:1209 | `        payload.approved_by = _reviewer_from_request(request, payload.approved_by)⏎` | `        payload.approved_by = payload.approved_by or _reviewer_from_request(request)⏎` | 1 (1) | MUERTO |
| 44 | sv4/interface_adapters/web/app.py:1777 | `return _a_la_ficha(document_id, MENSAJES_ALTA["reintentar_adjunto"][resultado])` | `return _a_la_ficha(document_id, MENSAJES_ALTA["alta"][resultado])` | 1 (1) | MUERTO |
| 45 | sv4/domain/services/alta_sigrid.py:80 | `        alta is not None⏎        and alta.estado == "registrado"` | `        alta.estado == "registrado"` | 1 (1) | MUERTO |
| 46 | sv4/domain/services/alta_sigrid.py:81 | `        and alta.estado == "registrado"⏎` | *(nada)* | 3 (3) | MUERTO |
| 47 | sv4/domain/services/alta_sigrid.py:82 | `        and alta.modo == "real"⏎` | *(nada)* | 2 (2) | MUERTO |
| 48 | sv4/domain/services/alta_sigrid.py:83 | `        and alta.adjunto_estado != "colgado"` | `        and alta.adjunto_estado == "error"` | 1 (1) | MUERTO |
| 49 | sv4/domain/services/alta_sigrid.py:46 | `return not (aprobado_en is None or config.desde is None or aprobado_en < config.desde)` | `return not (aprobado_en is None or config.desde is None or aprobado_en <= config.desde)` | 1 (1) | MUERTO |
| 50 | sv4/domain/services/alta_sigrid.py:43 | `    if not config.activa or not aprobado or not activo:⏎        return False⏎    aprobado_en` | `    if not aprobado or not activo:⏎        return False⏎    aprobado_en` | 0 | EQUIVALENTE (demostrado, ver abajo) |
| 51 | sv4/application/services/review_service.py:961 | `        if not self._config_alta.activa:⏎            return "apagada"⏎        if not self.puede_reintentar_adjunto(document_id):` | `        if not self.puede_reintentar_adjunto(document_id):` | 1 (1) | MUERTO |
| 52 | sv4/application/services/review_service.py:965 | `return self._publicar_feedback(document_id, "alta", solicitado_por)⏎⏎    def verificar_anulacion_sigrid(` | `return self._publicar_feedback(document_id, "verificar_anulacion", solicitado_por)⏎⏎    def verificar_anulacion_sigrid(` | 2 (2) | MUERTO |
| 53 | sv4/application/services/review_service.py:162 | `"alta_puede_reintentar_adjunto": self.puede_reintentar_adjunto(document_id),` | `"alta_puede_reintentar_adjunto": False,` | 1 (1) | MUERTO |
| 54 | sv4/application/services/review_service.py:942 | `        if not self._config_alta.activa:⏎            return False⏎        estado = self._repository.estado_aprobacion(document_id)⏎        if estado is None:⏎            return False⏎        return puede_reintentar_adjunto(` | `        estado = self._repository.estado_aprobacion(document_id)⏎        if estado is None:⏎            return False⏎        return puede_reintentar_adjunto(` | 0 → 1 (1) | VIVO → MUERTO con test nuevo |
| 55 | sv4/domain/models/alta_sigrid_models.py:198 | `        return texto or None⏎` | `        return texto⏎` | 4 (4) | MUERTO |
| 56 | sv4/domain/models/alta_sigrid_models.py:209 | `        return self.usu.casefold() != parte_local.casefold()` | `        return self.usu != parte_local.casefold()` | 1 (1) | MUERTO |
| 57 | sv4/domain/models/alta_sigrid_models.py:208 | `parte_local = texto.split("@")[0] if "@" in texto else ""` | `parte_local = texto.split("@")[0]` | 0 → 1 (1) | VIVO → MUERTO con test nuevo |
| 58 | sv4/domain/models/alta_sigrid_models.py:205 | `        if self.usu is None:⏎            return False⏎        texto` | `        texto` | 4 (4) | MUERTO |
| 59 | sv4/domain/models/alta_sigrid_models.py:197 | `        texto = "" if valor is None else str(valor).strip()` | `        texto = "" if valor is None else str(valor)` | 0 → 2 (2) | VIVO → MUERTO con test nuevo |
| 60 | sv4/infrastructure/database/review_repository.py:4194 | `            approved_by=fila["approved_by"],⏎` | *(nada)* | 1 (1) | MUERTO |
| 61 | sv4/templates/_alta_sigrid.html:26 | `{% if alta.usu_respaldo %} (respaldo){% endif %}` | *(nada)* | 1 (1) | MUERTO |
| 62 | sv4/templates/_alta_sigrid.html:26 | `{% if alta.usu_respaldo %} (respaldo){% endif %}` | `{% if alta.usu %} (respaldo){% endif %}` | 1 (1) | MUERTO |
| 63 | sv4/templates/_alta_sigrid.html:92 | `        {% if document.alta_puede_reintentar_adjunto %}` | `        {% if alta %}` | 1 (1) | MUERTO |
| 64 | sv4/templates/_alta_sigrid.html:26 | `        {% if alta.usu %}· <span` | `        {% if alta %}· <span` | 1 (1) | MUERTO |

## Muertos solo por el cuerpo exacto de la petición (10, 11, 12, 16)

No son tests textuales: comprueban lo que el cliente MANDA a sigrid-api (`json.loads(peticion.content)`), que es su
conducta hacia fuera y el contrato. Se señalan porque en SQL Server podrían ser equivalentes: `cod.lower()` (10) y
quitar `UPPER` (16) no cambian nada si la intercalación de `dbo.usu.cod` y `dca.entref` no distingue mayúsculas (lo
habitual, `Modern_Spanish_CI_AS`, pero **no se ha medido**); `max_rows` 1 (11) depende de si sigrid-api marca
`truncated` al llegar justo al tope; sin `TOP (1)` (12), de que `dbo.usu.cod` sea único. Se mantiene la forma pedida
porque es la que valida sigrid-api (la misma consulta de `usuario_no_valido`) y no depende de la intercalación.

## Equivalentes (38, 50) · demostración ejecutable (RM5)

`services/albaranes-front/tests/test_f053_v8_equivalentes.py`, patrón de `test_f053_t25_equivalentes.py`: carga el
módulo REAL, fabrica la variante con el texto exacto del mutante (la fuente se normaliza antes por si una campaña lo
ha inyectado), compara las dos sobre un dominio amplio y lleva un CONTROL no equivalente que sí se detecta.

- **38** (`if propuesto and propuesto.strip()` → `if propuesto`). En la pasada 1 **no era equivalente** (review v8,
  cambio 3): con `DEFAULT_REVIEWER` con espacios, `_reviewer_from_request` lo devolvía sin recortar, el merge quedaba
  igual (`_clean_text`) pero el `MensajeFeedback` cambiaba. Arreglado en `4be8eb2` (`app.py`: `return
  (settings.default_reviewer or "").strip() or None`), con su RED (`test_f053_r49_default_reviewer_recortado`, 6
  casos por los dos caminos: merge y mensaje recortados). Desde ahí sí lo es: con formulario o cuerpo en blanco el
  mutante devuelve `""` y el servicio lo cambia por el mismo defecto recortado. Demostración: `app.py` real y su
  variante con `build_app` y dobles, cabecera × formulario/cuerpo × `DEFAULT_REVIEWER` (5 × 5 × 5, por el listado y
  por el PUT): mismo merge y mismos mensajes. Control `return propuesto.strip()` → `return propuesto`: distinto.
- **50** (quitar `not config.activa` de `_documento_admite_alta`): `ConfigAltaSigrid.activa` es exactamente
  `desde is not None`, y la misma función ya comprueba `config.desde is None`. Demostración: `_documento_admite_alta`,
  `puede_reintentar_adjunto` y `puede_solicitar_alta` del módulo real y de la variante sobre `desde` (`None` o fecha)
  × aprobado × activo × 8 `approved_at_utc` (válidas antes, en y después de DESDE, sin zona, ilegible, vacía, `None`)
  × 5 altas: 320 casos (tres funciones en cada uno), idénticos. Control `aprobado_en < config.desde` → `<=`: distinto.

Están pendientes de la **aceptación escrita del humano** (nivel `critico`), como los 10 de la v7.

## Supervivientes de la pasada 1 cerrados con test (25, 35, 54, 57, 59)

| # | Qué no se veía | Test que lo mata (commit `77b6257`) |
|---|---|---|
| 25 | tras guardar `error` `usuario_no_resuelto`, seguir a validar sin `usu` (acababa en «fallo inesperado» en el log, el alta ya cerrada) | `test_f053_r48_sin_usuario_no_sigue_ni_deja_un_fallo_inesperado` |
| 35 | respaldo de solo espacios sin aviso de arranque | caso `"   "` de `test_f053_r47_config_aviso_de_arranque_sin_respaldo` |
| 54 | con DESDE vacía, `puede_reintentar_adjunto` leía el merge y el alta (R3: no se lee nada) | `test_f053_r30_reintentar_adjunto_con_desde_vacia_no_lee_nada` |
| 57 | `approved_by` sin @ igual al `usu` (`pgris`/`pgris`) no se marcaba «(respaldo)» | caso `("pgris", "pgris", True)` de `test_f053_r29_usu_y_respaldo` |
| 59 | `usu` con espacios en la petición | `test_f053_r29_usu_recortado` y caso `{"usu": "   "}` |

## Anexo · sustituciones exactas (JSON, una por mutante)

Cada objeto es lo que aplicó `mutar_v8.py`: `orig` debe aparecer UNA vez en `fichero` (con los saltos normalizados a `
`), se sustituye por `mut`, se corre la suite del servicio sin `-x` y se restaura el fichero byte a byte.

```json
{"id": 1, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/usuario_sigrid.py", "orig": "if texto.count(\"@\") != 1:", "mut": "if texto.count(\"@\") < 1:"}
{"id": 2, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/usuario_sigrid.py", "orig": "texto = (approved_by or \"\").strip()", "mut": "texto = (approved_by or \"\")"}
{"id": 3, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/usuario_sigrid.py", "orig": "if dominio.lower() != DOMINIO_RUESMA:", "mut": "if dominio != DOMINIO_RUESMA:"}
{"id": 4, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/usuario_sigrid.py", "orig": "if not local or len(local) > MAX_LOGIN:", "mut": "if len(local) > MAX_LOGIN:"}
{"id": 5, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/usuario_sigrid.py", "orig": "if not local or len(local) > MAX_LOGIN:", "mut": "if not local or len(local) >= MAX_LOGIN:"}
{"id": 6, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/usuario_sigrid.py", "orig": "MAX_LOGIN = 24", "mut": "MAX_LOGIN = 25"}
{"id": 7, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/usuario_sigrid.py", "orig": "    return local\n", "mut": "    return local.lower()\n"}
{"id": 8, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py", "orig": "encontrado = str(filas[0].get(\"cod\") or \"\").strip() if filas else \"\"", "mut": "encontrado = str(filas[0].get(\"cod\") or \"\") if filas else \"\""}
{"id": 9, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py", "orig": "        return encontrado or None\n", "mut": "        return encontrado\n"}
{"id": 10, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py", "orig": "filas = self._leer(SQL_BUSCAR_USUARIO, [cod], \"f053-usuario\", 2)", "mut": "filas = self._leer(SQL_BUSCAR_USUARIO, [cod.lower()], \"f053-usuario\", 2)"}
{"id": 11, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py", "orig": "filas = self._leer(SQL_BUSCAR_USUARIO, [cod], \"f053-usuario\", 2)", "mut": "filas = self._leer(SQL_BUSCAR_USUARIO, [cod], \"f053-usuario\", 1)"}
{"id": 12, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py", "orig": "SQL_BUSCAR_USUARIO = \"SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?\"", "mut": "SQL_BUSCAR_USUARIO = \"SELECT cod FROM dbo.usu WHERE cod = ?\""}
{"id": 13, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py", "orig": "            \"usu\": usu,", "mut": "            \"usu\": usu.lower(),"}
{"id": 14, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py", "orig": "        if not numero:\n            # Solo separadores: casaría con cualquier ``entref`` vacío.\n            return []\n", "mut": ""}
{"id": 15, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py", "orig": "SQL_BUSCAR_ALBARANES, [cif, numero, referencia_externa],", "mut": "SQL_BUSCAR_ALBARANES, [cif, referencia, referencia_externa],"}
{"id": 16, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/infrastructure/sigrid/sigrid_api_alta_client.py", "orig": "f\"WHERE c.tip = 14 AND d.entcif = ? AND UPPER({_ENTREF_NORMALIZADO}) = ? \"", "mut": "f\"WHERE c.tip = 14 AND d.entcif = ? AND {_ENTREF_NORMALIZADO} = ? \""}
{"id": 17, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/validador_alta.py", "orig": "SEPARADORES_REFERENCIA = (\" \", \".\", \"-\", \"/\")", "mut": "SEPARADORES_REFERENCIA = (\" \", \".\", \"-\")"}
{"id": 18, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/validador_alta.py", "orig": "texto = (numero or \"\").upper()", "mut": "texto = (numero or \"\")"}
{"id": 19, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/validador_alta.py", "orig": "        usu=usu,\n", "mut": "        usu=\"\",\n"}
{"id": 20, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "        if candidato is not None:\n            try:", "mut": "        if candidato is None:\n            try:"}
{"id": 21, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "            if cod:\n                logger.info", "mut": "            if True:\n                logger.info"}
{"id": 22, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "        if not self._respaldo:\n            raise", "mut": "        if self._respaldo:\n            raise"}
{"id": 23, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "self._respaldo = (usuario_respaldo or \"\").strip()", "mut": "self._respaldo = (usuario_respaldo or \"\")"}
{"id": 24, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "            try:\n                cod = self._sigrid.buscar_usuario(candidato)\n            except Exception as exc:  # noqa: BLE001 — R48: sin comprobar, no se atribuye\n                raise UsuarioNoResuelto(\n                    f\"no se pudo leer dbo.usu: {type(exc).__name__}\",\n                ) from exc\n", "mut": "            cod = self._sigrid.buscar_usuario(candidato)\n"}
{"id": 25, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "                    EstadoAlta.ERROR, paso, motivos=(Motivo(MOTIVO_USUARIO, str(exc)),),\n                ))\n                return\n", "mut": "                    EstadoAlta.ERROR, paso, motivos=(Motivo(MOTIVO_USUARIO, str(exc)),),\n                ))\n"}
{"id": 26, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "usu = str((resultado.peticion or {}).get(\"usu\") or \"\").strip()", "mut": "usu = str((resultado.peticion or {}).get(\"usu\") or \"\")"}
{"id": 27, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "            if not usu:\n                raise UsuarioNoResuelto(\"la petición guardada no lleva usu\")\n", "mut": ""}
{"id": 28, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "adjunto = ResultadoAdjunto(False, codigo=MOTIVO_USUARIO, mensaje=str(exc))", "mut": "adjunto = ResultadoAdjunto(False, codigo=type(exc).__name__, mensaje=str(exc))"}
{"id": 29, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "resultado.sigrid_con_ide, nombre, contenido, usu=usu,", "mut": "resultado.sigrid_con_ide, nombre, contenido, usu=self._respaldo,"}
{"id": 30, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/application/alta_sigrid_service.py", "orig": "return self._procesar_alta(document_id, reclamacion.alta, reclamacion.approved_by)", "mut": "return self._procesar_alta(document_id, reclamacion.alta, None)"}
{"id": 31, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/reclamacion.py", "orig": "    if documento is None:\n        return reclamacion\n    return replace", "mut": "    return replace"}
{"id": 32, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/domain/services/reclamacion.py", "orig": "    return replace(reclamacion, approved_by=documento.approved_by)", "mut": "    return reclamacion"}
{"id": 33, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/config/settings.py", "orig": "Field(\"\", alias=\"ALTA_SIGRID_USUARIO_RESPALDO\")", "mut": "Field(\"\", alias=\"ALTA_SIGRID_USUARIO\")"}
{"id": 34, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/config/settings.py", "orig": "Field(\"\", alias=\"ALTA_SIGRID_USUARIO_RESPALDO\")", "mut": "Field(\"pgris\", alias=\"ALTA_SIGRID_USUARIO_RESPALDO\")"}
{"id": 35, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/main_worker.py", "orig": "if settings.desde is not None and not settings.usuario_respaldo.strip():", "mut": "if settings.desde is not None and not settings.usuario_respaldo:"}
{"id": 36, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/main_worker.py", "orig": "if settings.desde is not None and not settings.usuario_respaldo.strip():", "mut": "if not settings.usuario_respaldo.strip():"}
{"id": 37, "svc": "sv9", "fichero": "services/albaranes-alta-sigrid/interface_adapters/composition.py", "orig": "usuario_respaldo=settings.usuario_respaldo,", "mut": "usuario_respaldo=\"\","}
{"id": 38, "svc": "sv4", "fichero": "services/albaranes-front/interface_adapters/web/app.py", "orig": "        if propuesto and propuesto.strip():\n            return propuesto.strip()", "mut": "        if propuesto:\n            return propuesto.strip()"}
{"id": 39, "svc": "sv4", "fichero": "services/albaranes-front/interface_adapters/web/app.py", "orig": "        if propuesto and propuesto.strip():\n            return propuesto.strip()", "mut": "        if propuesto and propuesto.strip():\n            return propuesto"}
{"id": 40, "svc": "sv4", "fichero": "services/albaranes-front/interface_adapters/web/app.py", "orig": "        if principal and principal.strip():\n            return principal.strip()\n        if propuesto", "mut": "        if principal:\n            return principal.strip()\n        if propuesto"}
{"id": 41, "svc": "sv4", "fichero": "services/albaranes-front/interface_adapters/web/app.py", "orig": "                approved_by=_reviewer_from_request(request, approved_by),", "mut": "                approved_by=approved_by.strip() or _reviewer_from_request(request),"}
{"id": 42, "svc": "sv4", "fichero": "services/albaranes-front/interface_adapters/web/app.py", "orig": "        payload.approved_by = _reviewer_from_request(request, payload.approved_by)\n", "mut": ""}
{"id": 43, "svc": "sv4", "fichero": "services/albaranes-front/interface_adapters/web/app.py", "orig": "        payload.approved_by = _reviewer_from_request(request, payload.approved_by)\n", "mut": "        payload.approved_by = payload.approved_by or _reviewer_from_request(request)\n"}
{"id": 44, "svc": "sv4", "fichero": "services/albaranes-front/interface_adapters/web/app.py", "orig": "return _a_la_ficha(document_id, MENSAJES_ALTA[\"reintentar_adjunto\"][resultado])", "mut": "return _a_la_ficha(document_id, MENSAJES_ALTA[\"alta\"][resultado])"}
{"id": 45, "svc": "sv4", "fichero": "services/albaranes-front/domain/services/alta_sigrid.py", "orig": "        alta is not None\n        and alta.estado == \"registrado\"", "mut": "        alta.estado == \"registrado\""}
{"id": 46, "svc": "sv4", "fichero": "services/albaranes-front/domain/services/alta_sigrid.py", "orig": "        and alta.estado == \"registrado\"\n", "mut": ""}
{"id": 47, "svc": "sv4", "fichero": "services/albaranes-front/domain/services/alta_sigrid.py", "orig": "        and alta.modo == \"real\"\n", "mut": ""}
{"id": 48, "svc": "sv4", "fichero": "services/albaranes-front/domain/services/alta_sigrid.py", "orig": "        and alta.adjunto_estado != \"colgado\"", "mut": "        and alta.adjunto_estado == \"error\""}
{"id": 49, "svc": "sv4", "fichero": "services/albaranes-front/domain/services/alta_sigrid.py", "orig": "return not (aprobado_en is None or config.desde is None or aprobado_en < config.desde)", "mut": "return not (aprobado_en is None or config.desde is None or aprobado_en <= config.desde)"}
{"id": 50, "svc": "sv4", "fichero": "services/albaranes-front/domain/services/alta_sigrid.py", "orig": "    if not config.activa or not aprobado or not activo:\n        return False\n    aprobado_en", "mut": "    if not aprobado or not activo:\n        return False\n    aprobado_en"}
{"id": 51, "svc": "sv4", "fichero": "services/albaranes-front/application/services/review_service.py", "orig": "        if not self._config_alta.activa:\n            return \"apagada\"\n        if not self.puede_reintentar_adjunto(document_id):", "mut": "        if not self.puede_reintentar_adjunto(document_id):"}
{"id": 52, "svc": "sv4", "fichero": "services/albaranes-front/application/services/review_service.py", "orig": "return self._publicar_feedback(document_id, \"alta\", solicitado_por)\n\n    def verificar_anulacion_sigrid(", "mut": "return self._publicar_feedback(document_id, \"verificar_anulacion\", solicitado_por)\n\n    def verificar_anulacion_sigrid("}
{"id": 53, "svc": "sv4", "fichero": "services/albaranes-front/application/services/review_service.py", "orig": "\"alta_puede_reintentar_adjunto\": self.puede_reintentar_adjunto(document_id),", "mut": "\"alta_puede_reintentar_adjunto\": False,"}
{"id": 54, "svc": "sv4", "fichero": "services/albaranes-front/application/services/review_service.py", "orig": "        if not self._config_alta.activa:\n            return False\n        estado = self._repository.estado_aprobacion(document_id)\n        if estado is None:\n            return False\n        return puede_reintentar_adjunto(", "mut": "        estado = self._repository.estado_aprobacion(document_id)\n        if estado is None:\n            return False\n        return puede_reintentar_adjunto("}
{"id": 55, "svc": "sv4", "fichero": "services/albaranes-front/domain/models/alta_sigrid_models.py", "orig": "        return texto or None\n", "mut": "        return texto\n"}
{"id": 56, "svc": "sv4", "fichero": "services/albaranes-front/domain/models/alta_sigrid_models.py", "orig": "        return self.usu.casefold() != parte_local.casefold()", "mut": "        return self.usu != parte_local.casefold()"}
{"id": 57, "svc": "sv4", "fichero": "services/albaranes-front/domain/models/alta_sigrid_models.py", "orig": "parte_local = texto.split(\"@\")[0] if \"@\" in texto else \"\"", "mut": "parte_local = texto.split(\"@\")[0]"}
{"id": 58, "svc": "sv4", "fichero": "services/albaranes-front/domain/models/alta_sigrid_models.py", "orig": "        if self.usu is None:\n            return False\n        texto", "mut": "        texto"}
{"id": 59, "svc": "sv4", "fichero": "services/albaranes-front/domain/models/alta_sigrid_models.py", "orig": "        texto = \"\" if valor is None else str(valor).strip()", "mut": "        texto = \"\" if valor is None else str(valor)"}
{"id": 60, "svc": "sv4", "fichero": "services/albaranes-front/infrastructure/database/review_repository.py", "orig": "            approved_by=fila[\"approved_by\"],\n", "mut": ""}
{"id": 61, "svc": "sv4", "fichero": "services/albaranes-front/templates/_alta_sigrid.html", "orig": "{% if alta.usu_respaldo %} (respaldo){% endif %}", "mut": ""}
{"id": 62, "svc": "sv4", "fichero": "services/albaranes-front/templates/_alta_sigrid.html", "orig": "{% if alta.usu_respaldo %} (respaldo){% endif %}", "mut": "{% if alta.usu %} (respaldo){% endif %}"}
{"id": 63, "svc": "sv4", "fichero": "services/albaranes-front/templates/_alta_sigrid.html", "orig": "        {% if document.alta_puede_reintentar_adjunto %}", "mut": "        {% if alta %}"}
{"id": 64, "svc": "sv4", "fichero": "services/albaranes-front/templates/_alta_sigrid.html", "orig": "        {% if alta.usu %}· <span", "mut": "        {% if alta %}· <span"}
```
