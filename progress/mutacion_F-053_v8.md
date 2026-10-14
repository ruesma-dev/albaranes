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
  equivalentes justificados, 0 vivos sin test ni justificación.**
- **Tests textuales**: el script separa los que miran el código como texto o su forma (`inspect.getsource`,
  firmas, `model_fields`, el SQL como constante, `.env.example` e `infra/`). **Ningún mutante muere solo por
  ellos**: en todos los muertos hay al menos un test de conducta (columna «conducta»). Los dos equivalentes no los
  mata ningún test, textual o no.

## Tabla

| # | fichero:línea | original | mutado | fallos (conducta) | veredicto |
|---|---|---|---|---|---|
| 1 | sv9/domain/services/usuario_sigrid.py:25 | `if texto.count("@") != 1:` | `if texto.count("@") < 1:` | 1 (1) | MUERTO |
| 2 | sv9/domain/services/usuario_sigrid.py:24 | `texto = (approved_by or "").strip()` | `texto = (approved_by or "")` | 3 (3) | MUERTO |
| 3 | sv9/domain/services/usuario_sigrid.py:28 | `if dominio.lower() != DOMINIO_RUESMA:` | `if dominio != DOMINIO_RUESMA:` | 3 (3) | MUERTO |
| 4 | sv9/domain/services/usuario_sigrid.py:30 | `if not local or len(local) > MAX_LOGIN:` | `if len(local) > MAX_LOGIN:` | 1 (1) | MUERTO |
| 5 | sv9/domain/services/usuario_sigrid.py:30 | `if not local or len(local) > MAX_LOGIN:` | `if not local or len(local) >= MAX_LOGIN:` | 1 (1) | MUERTO |
| 6 | sv9/domain/services/usuario_sigrid.py:12 | `MAX_LOGIN = 24` | `MAX_LOGIN = 25` | 2 (2) | MUERTO |
| 7 | sv9/domain/services/usuario_sigrid.py:32 | `return local⏎` | `return local.lower()⏎` | 2 (2) | MUERTO |
| 8 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:219 | `encontrado = str(filas[0].get("cod") or "").strip() if fi…` | `encontrado = str(filas[0].get("cod") or "") if filas else…` | 2 (2) | MUERTO |
| 9 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:220 | `return encontrado or None⏎` | `return encontrado⏎` | 4 (4) | MUERTO |
| 10 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:218 | `filas = self._leer(SQL_BUSCAR_USUARIO, [cod], "f053-usuar…` | `filas = self._leer(SQL_BUSCAR_USUARIO, [cod.lower()], "f0…` | 1 (1) | MUERTO (cuerpo exacto; ver abajo) |
| 11 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:218 | `filas = self._leer(SQL_BUSCAR_USUARIO, [cod], "f053-usuar…` | `filas = self._leer(SQL_BUSCAR_USUARIO, [cod], "f053-usuar…` | 1 (1) | MUERTO (cuerpo exacto; ver abajo) |
| 12 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:71 | `SQL_BUSCAR_USUARIO = "SELECT TOP (1) cod FROM dbo.usu WHE…` | `SQL_BUSCAR_USUARIO = "SELECT cod FROM dbo.usu WHERE cod =…` | 1 (1) | MUERTO (cuerpo exacto; ver abajo) |
| 13 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:261 | `"usu": usu,` | `"usu": usu.lower(),` | 1 (1) | MUERTO |
| 14 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:199 | `if not numero:⏎            # Solo separadores: casaría co…` | `(nada)` | 3 (3) | MUERTO |
| 15 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:203 | `SQL_BUSCAR_ALBARANES, [cif, numero, referencia_externa],` | `SQL_BUSCAR_ALBARANES, [cif, referencia, referencia_extern…` | 2 (2) | MUERTO |
| 16 | sv9/infrastructure/sigrid/sigrid_api_alta_client.py:64 | `f"WHERE c.tip = 14 AND d.entcif = ? AND UPPER({_ENTREF_NO…` | `f"WHERE c.tip = 14 AND d.entcif = ? AND {_ENTREF_NORMALIZ…` | 3 (2) | MUERTO (cuerpo exacto; ver abajo) |
| 17 | sv9/domain/services/validador_alta.py:97 | `SEPARADORES_REFERENCIA = (" ", ".", "-", "/")` | `SEPARADORES_REFERENCIA = (" ", ".", "-")` | 8 (7) | MUERTO |
| 18 | sv9/domain/services/validador_alta.py:104 | `texto = (numero or "").upper()` | `texto = (numero or "")` | 3 (3) | MUERTO |
| 19 | sv9/domain/services/validador_alta.py:327 | `usu=usu,⏎` | `usu="",⏎` | 21 (20) | MUERTO |
| 20 | sv9/application/alta_sigrid_service.py:241 | `if candidato is not None:⏎            try:` | `if candidato is None:⏎            try:` | 79 (79) | MUERTO |
| 21 | sv9/application/alta_sigrid_service.py:248 | `if cod:⏎                logger.info` | `if True:⏎                logger.info` | 3 (3) | MUERTO |
| 22 | sv9/application/alta_sigrid_service.py:251 | `if not self._respaldo:⏎            raise` | `if self._respaldo:⏎            raise` | 74 (74) | MUERTO |
| 23 | sv9/application/alta_sigrid_service.py:138 | `self._respaldo = (usuario_respaldo or "").strip()` | `self._respaldo = (usuario_respaldo or "")` | 3 (3) | MUERTO |
| 24 | sv9/application/alta_sigrid_service.py:242 | `try:⏎                cod = self._sigrid.buscar_usuario(ca…` | `cod = self._sigrid.buscar_usuario(candidato)⏎` | 2 (2) | MUERTO |
| 25 | sv9/application/alta_sigrid_service.py:274 | `…MOTIVO_USUARIO, str(exc)),),⏎ ))⏎ return` | `…MOTIVO_USUARIO, str(exc)),),⏎ ))` (sin el `return`) | 0 → 1 (1) | VIVO → MUERTO con test nuevo (1) |
| 26 | sv9/application/alta_sigrid_service.py:392 | `usu = str((resultado.peticion or {}).get("usu") or "").st…` | `usu = str((resultado.peticion or {}).get("usu") or "")` | 1 (1) | MUERTO |
| 27 | sv9/application/alta_sigrid_service.py:394 | `if not usu:⏎                raise UsuarioNoResuelto("la p…` | `(nada)` | 4 (4) | MUERTO |
| 28 | sv9/application/alta_sigrid_service.py:402 | `adjunto = ResultadoAdjunto(False, codigo=MOTIVO_USUARIO, …` | `adjunto = ResultadoAdjunto(False, codigo=type(exc).__name…` | 4 (4) | MUERTO |
| 29 | sv9/application/alta_sigrid_service.py:398 | `resultado.sigrid_con_ide, nombre, contenido, usu=usu,` | `resultado.sigrid_con_ide, nombre, contenido, usu=self._re…` | 2 (2) | MUERTO |
| 30 | sv9/application/alta_sigrid_service.py:179 | `return self._procesar_alta(document_id, reclamacion.alta,…` | `return self._procesar_alta(document_id, reclamacion.alta,…` | 8 (8) | MUERTO |
| 31 | sv9/domain/services/reclamacion.py:76 | `if documento is None:⏎        return reclamacion⏎    retu…` | `return replace` | 5 (5) | MUERTO |
| 32 | sv9/domain/services/reclamacion.py:78 | `return replace(reclamacion, approved_by=documento.approve…` | `return reclamacion` | 10 (10) | MUERTO |
| 33 | sv9/config/settings.py:61 | `Field("", alias="ALTA_SIGRID_USUARIO_RESPALDO")` | `Field("", alias="ALTA_SIGRID_USUARIO")` | 5 (5) | MUERTO |
| 34 | sv9/config/settings.py:61 | `Field("", alias="ALTA_SIGRID_USUARIO_RESPALDO")` | `Field("pgris", alias="ALTA_SIGRID_USUARIO_RESPALDO")` | 2 (2) | MUERTO |
| 35 | sv9/main_worker.py:114 | `if settings.desde is not None and not settings.usuario_re…` | `if settings.desde is not None and not settings.usuario_re…` | 0 → 1 (1) | VIVO → MUERTO con test nuevo (1) |
| 36 | sv9/main_worker.py:114 | `if settings.desde is not None and not settings.usuario_re…` | `if not settings.usuario_respaldo.strip():` | 2 (2) | MUERTO |
| 37 | sv9/interface_adapters/composition.py:60 | `usuario_respaldo=settings.usuario_respaldo,` | `usuario_respaldo="",` | 2 (2) | MUERTO |
| 38 | sv4/interface_adapters/web/app.py:469 | `if propuesto and propuesto.strip():⏎            return pr…` | `if propuesto:⏎            return propuesto.strip()` | 0 | EQUIVALENTE (ver abajo) |
| 39 | sv4/interface_adapters/web/app.py:469 | `if propuesto and propuesto.strip():⏎            return pr…` | `if propuesto and propuesto.strip():⏎            return pr…` | 1 (1) | MUERTO |
| 40 | sv4/interface_adapters/web/app.py:467 | `if principal and principal.strip():⏎            return pr…` | `if principal:⏎            return principal.strip()⏎      …` | 1 (1) | MUERTO |
| 41 | sv4/interface_adapters/web/app.py:757 | `approved_by=_reviewer_from_request(request, approved_by),` | `approved_by=approved_by.strip() or _reviewer_from_request…` | 2 (2) | MUERTO |
| 42 | sv4/interface_adapters/web/app.py:1209 | `payload.approved_by = _reviewer_from_request(request, pay…` | `(nada)` | 3 (3) | MUERTO |
| 43 | sv4/interface_adapters/web/app.py:1209 | `payload.approved_by = _reviewer_from_request(request, pay…` | `payload.approved_by = payload.approved_by or _reviewer_fr…` | 1 (1) | MUERTO |
| 44 | sv4/interface_adapters/web/app.py:1777 | `return _a_la_ficha(document_id, MENSAJES_ALTA["reintentar…` | `return _a_la_ficha(document_id, MENSAJES_ALTA["alta"][res…` | 1 (1) | MUERTO |
| 45 | sv4/domain/services/alta_sigrid.py:80 | `alta is not None⏎        and alta.estado == "registrado"` | `alta.estado == "registrado"` | 1 (1) | MUERTO |
| 46 | sv4/domain/services/alta_sigrid.py:81 | `and alta.estado == "registrado"⏎` | `(nada)` | 3 (3) | MUERTO |
| 47 | sv4/domain/services/alta_sigrid.py:82 | `and alta.modo == "real"⏎` | `(nada)` | 2 (2) | MUERTO |
| 48 | sv4/domain/services/alta_sigrid.py:83 | `and alta.adjunto_estado != "colgado"` | `and alta.adjunto_estado == "error"` | 1 (1) | MUERTO |
| 49 | sv4/domain/services/alta_sigrid.py:46 | `return not (aprobado_en is None or config.desde is None o…` | `return not (aprobado_en is None or config.desde is None o…` | 1 (1) | MUERTO |
| 50 | sv4/domain/services/alta_sigrid.py:43 | `if not config.activa or not aprobado or not activo:⏎     …` | `if not aprobado or not activo:⏎        return False⏎    a…` | 0 | EQUIVALENTE (ver abajo) |
| 51 | sv4/application/services/review_service.py:961 | `if not self._config_alta.activa:⏎            return "apag…` | `if not self.puede_reintentar_adjunto(document_id):` | 1 (1) | MUERTO |
| 52 | sv4/application/services/review_service.py:965 | `return self._publicar_feedback(document_id, "alta", solic…` | `return self._publicar_feedback(document_id, "verificar_an…` | 2 (2) | MUERTO |
| 53 | sv4/application/services/review_service.py:162 | `"alta_puede_reintentar_adjunto": self.puede_reintentar_ad…` | `"alta_puede_reintentar_adjunto": False,` | 1 (1) | MUERTO |
| 54 | sv4/application/services/review_service.py:942 | `if not self._config_alta.activa:⏎            return False…` | `estado = self._repository.estado_aprobacion(document_id)⏎…` | 0 → 1 (1) | VIVO → MUERTO con test nuevo (1) |
| 55 | sv4/domain/models/alta_sigrid_models.py:198 | `return texto or None⏎` | `return texto⏎` | 4 (4) | MUERTO |
| 56 | sv4/domain/models/alta_sigrid_models.py:209 | `return self.usu.casefold() != parte_local.casefold()` | `return self.usu != parte_local.casefold()` | 1 (1) | MUERTO |
| 57 | sv4/domain/models/alta_sigrid_models.py:208 | `parte_local = texto.split("@")[0] if "@" in texto else ""` | `parte_local = texto.split("@")[0]` | 0 → 1 (1) | VIVO → MUERTO con test nuevo (1) |
| 58 | sv4/domain/models/alta_sigrid_models.py:205 | `if self.usu is None:⏎            return False⏎        tex…` | `texto` | 4 (4) | MUERTO |
| 59 | sv4/domain/models/alta_sigrid_models.py:197 | `texto = "" if valor is None else str(valor).strip()` | `texto = "" if valor is None else str(valor)` | 0 → 2 (2) | VIVO → MUERTO con test nuevo (2) |
| 60 | sv4/infrastructure/database/review_repository.py:4194 | `approved_by=fila["approved_by"],⏎` | `(nada)` | 1 (1) | MUERTO |
| 61 | sv4/templates/_alta_sigrid.html:26 | `{% if alta.usu_respaldo %} (respaldo){% endif %}` | `(nada)` | 1 (1) | MUERTO |
| 62 | sv4/templates/_alta_sigrid.html:26 | `{% if alta.usu_respaldo %} (respaldo){% endif %}` | `{% if alta.usu %} (respaldo){% endif %}` | 1 (1) | MUERTO |
| 63 | sv4/templates/_alta_sigrid.html:92 | `{% if document.alta_puede_reintentar_adjunto %}` | `{% if alta %}` | 1 (1) | MUERTO |
| 64 | sv4/templates/_alta_sigrid.html:26 | `{% if alta.usu %}· <span` | `{% if alta %}· <span` | 1 (1) | MUERTO |

## Muertos solo por el cuerpo exacto de la petición (10, 11, 12, 16)

No son tests textuales: comprueban lo que el cliente MANDA a sigrid-api (`json.loads(peticion.content)`), que es su
conducta hacia fuera y el contrato. Se señalan porque en SQL Server podrían ser equivalentes: `cod.lower()` (10) y
quitar `UPPER` (16) no cambian nada si la intercalación de `dbo.usu.cod` y `dca.entref` no distingue mayúsculas (lo
habitual, `Modern_Spanish_CI_AS`, pero **no se ha medido**); `max_rows` 1 (11) depende de si sigrid-api marca
`truncated` al llegar justo al tope; sin `TOP (1)` (12), de que `dbo.usu.cod` sea único. Se mantiene la forma pedida
porque es la que valida sigrid-api (la misma consulta de `usuario_no_valido`) y no depende de la intercalación.

## Equivalentes (38, 50)

- **38** (`if propuesto and propuesto.strip()` → `if propuesto`): con un formulario o cuerpo de solo espacios y sin
  cabecera, la función devuelve `""` en vez de `DEFAULT_REVIEWER`, pero el servicio convierte `""` en
  `DEFAULT_REVIEWER` en los dos caminos (`approve_document`: `approved_by or self._default_reviewer`;
  `_guardar_y_aprobar`: `if payload.approved and not payload.approved_by`). Lo comprueban los casos `"   "` de
  `test_f053_r49_listado` y `test_f053_r49_ficha`: el resultado es el mismo con y sin el mutante. Solo pasa en local.
- **50** (quitar `not config.activa` de `_documento_admite_alta`): `ConfigAltaSigrid.activa` es exactamente
  `desde is not None` (`alta_sigrid_models.py`), y la misma línea ya comprueba `config.desde is None`: quitar una de
  las dos condiciones idénticas no cambia nada. Era así antes de la v8 (`puede_solicitar_alta`); la v8 solo la movió
  a la función común.

## Supervivientes de la pasada 1 cerrados con test (25, 35, 54, 57, 59)

| # | Qué no se veía | Test que lo mata (commit `77b6257`) |
|---|---|---|
| 25 | sv9/application/alta_sigrid_service.py:274 | `…MOTIVO_USUARIO, str(exc)),),⏎ ))⏎ return` | `…MOTIVO_USUARIO, str(exc)),),⏎ ))` (sin el `return`) | 0 → 1 (1) | VIVO → MUERTO con test nuevo (1) |
| 35 | respaldo de solo espacios sin aviso de arranque | caso `"   "` de `test_f053_r47_config_aviso_de_arranque_sin_respaldo` |
| 54 | con DESDE vacía, `puede_reintentar_adjunto` leía el merge y el alta (R3: no se lee nada) | `test_f053_r30_reintentar_adjunto_con_desde_vacia_no_lee_nada` |
| 57 | `approved_by` sin @ igual al `usu` (`pgris`/`pgris`) no se marcaba «(respaldo)» | caso `("pgris", "pgris", True)` de `test_f053_r29_usu_y_respaldo` |
| 59 | `usu` con espacios en la petición | `test_f053_r29_usu_recortado` y caso `{"usu": "   "}` |
