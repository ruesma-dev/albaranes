<!-- progress/mutacion_F-070.md -->
# F-070 · Campaña de mutación a mano (complemento)

**Complemento** de la campaña de la herramienta (`progress/mutacion_F-070_arnes.md`, la evidencia de C4 bis: 95
líneas en alcance, **4 mutantes, 4 muertos**). La herramienta solo genera mutantes de operadores (`in`, `is not`…)
y no muta las llamadas que son el cambio de F-070 en sv3, sv4 y sv9; aquí se muta cada punto de canonización.

**Método** (`mutar_f070.py` del scratchpad de la sesión): sobre `67e1898` (el test RM5 de sv9 se añadió después: no cambia ningún veredicto), cada mutante sustituye
un texto exacto (1 ocurrencia, comprobada) del fichero, corre la suite **entera** del servicio con `-x` (comun: solo
`test_f070_codigo_obra.py` y `test_f052_obras_codigo.py`, la suite de comun tarda 210 s) y restaura el fichero; en serie,
1 worker, sin bytecode. Entorno de §0 de `progress/impl_F-070.md` (comun de la rama). Línea base en verde: comun 77,
sv3 703, sv4 1423, sv9 637 passed.

**Resultado: 18 mutantes, 18 muertos, 0 vivos**, 693.6 s. El 17 (los motivos de la obra leídos con `_texto`) muere
solo por el test estructural de R15: en comportamiento es **equivalente**, demostrado en
`test_f070_r15_motivos_de_obra_equivalentes_a_los_de_antes` (14 entradas, con control que distingue `686`/`0686`).

| # | Servicio | Fichero | Original | Mutado | Veredicto | s | Primer test que falla |
|---|---|---|---|---|---|---|---|
| 1 | comun | `ruesma_comun/obras/codigo.py` | `        return limpio.upper()⏎    if not limpio` | `        return limpio⏎    if not limpio` | MUERTO | 1.6 | tests/test_f070_codigo_obra.py::test_f070_r2_var_y_postv2_son_canonicos[var-VAR] |
| 2 | comun | `ruesma_comun/obras/codigo.py` | `    if limpio.upper() in CODIGOS_OBRA_SIN_CERO:` | `    if limpio in CODIGOS_OBRA_SIN_CERO:` | MUERTO | 1.6 | tests/test_f070_codigo_obra.py::test_f070_r2_var_y_postv2_son_canonicos[var-VAR] |
| 3 | comun | `ruesma_comun/obras/codigo.py` | `frozenset({"VAR", "POSTV2"})` | `frozenset({"VAR"})` | MUERTO | 1.5 | tests/test_f070_codigo_obra.py::test_f070_r2_var_y_postv2_son_canonicos[POSTV2-POSTV2] |
| 4 | comun | `ruesma_comun/obras/codigo.py` | `    if canonico is not None:⏎        return canonico⏎` | `(borrado)` | MUERTO | 1.4 | tests/test_f070_codigo_obra.py::test_f070_r4_canonizar[686-0686] |
| 5 | comun | `ruesma_comun/obras/codigo.py` | `    return str(valor).strip() or None⏎` | `    return str(valor) or None⏎` | MUERTO | 1.4 | tests/test_f070_codigo_obra.py::test_f070_r4_canonizar[ GG -GG] |
| 6 | comun | `ruesma_comun/obras/codigo.py` | `    return str(valor).strip() or None⏎` | `    return str(valor).strip()⏎` | MUERTO | 1.4 | tests/test_f070_codigo_obra.py::test_f070_r4_canonizar[-None] |
| 7 | comun | `ruesma_comun/obras/codigo.py` | `    if valor is None:⏎        return None⏎    return str(valor)` | `    return str(valor)` | MUERTO | 1.4 | tests/test_f070_codigo_obra.py::test_f070_r4_canonizar[None-None] |
| 8 | sv3 | `application/services/albaran_normalizer.py` | `        return canonizar_codigo_obra(AlbaranNormalizer.normalize_identifier(value))` | `        return AlbaranNormalizer.normalize_identifier(value)` | MUERTO | 12.0 | tests/test_f070_obra_canonica.py::test_f070_r6_normalize_obra_codigo[686-0686] |
| 9 | sv3 | `application/services/albaran_normalizer.py` | `"obra_codigo": self.normalize_obra_codigo(header.obra_codigo)` | `"obra_codigo": self.normalize_identifier(header.obra_codigo)` | MUERTO | 11.0 | tests/test_f070_obra_canonica.py::test_f070_r6_normalize_header_sella_la_obra_canonica |
| 10 | sv3 | `application/services/header_resolver_service.py` | `            return canonizar_codigo_obra(best.codigo_obra)` | `            return (best.codigo_obra or "").strip() or None` | MUERTO | 10.9 | tests/test_f070_obra_canonica.py::test_f070_r7_obra_deducida_por_texto_canonizada[227-0227] |
| 11 | sv4 | `infrastructure/sigrid/sigrid_lookup_client.py` | `        codigo = canonizar_codigo_obra(codigo_obra)⏎        if not codigo:⏎            return []⏎        columns, rows = self._post_sql_read(⏎            sql=_SQL_PROVEEDORES_POR_OBRA` | `        codigo = (codigo_obra or "").strip()⏎        if not codigo:⏎            return []⏎        columns, rows = self._post_sql_read(⏎            sql=_SQL_PROVEEDORES_POR_OBRA` | MUERTO | 120.6 | tests/test_f070_obra_canonica.py::test_f070_r10_consulta_con_la_obra_canonica[686-0686-proveedores] |
| 12 | sv4 | `infrastructure/sigrid/sigrid_lookup_client.py` | `        codigo = canonizar_codigo_obra(codigo_obra)⏎        if not codigo:⏎            return []⏎        columns, rows = self._post_sql_read(⏎            sql=_SQL_PARTIDAS_POR_OBRA` | `        codigo = (codigo_obra or "").strip()⏎        if not codigo:⏎            return []⏎        columns, rows = self._post_sql_read(⏎            sql=_SQL_PARTIDAS_POR_OBRA` | MUERTO | 97.9 | tests/test_f070_obra_canonica.py::test_f070_r10_consulta_con_la_obra_canonica[686-0686-partidas] |
| 13 | sv4 | `infrastructure/sigrid/sigrid_lookup_client.py` | `        codigo = canonizar_codigo_obra(codigo_obra)⏎        if not codigo:⏎            return []⏎        columns, rows = self._post_sql_read(⏎            sql=_SQL_CONTRATOS_POR_OBRA` | `        codigo = (codigo_obra or "").strip()⏎        if not codigo:⏎            return []⏎        columns, rows = self._post_sql_read(⏎            sql=_SQL_CONTRATOS_POR_OBRA` | MUERTO | 150.2 | tests/test_f070_obra_canonica.py::test_f070_r10_consulta_con_la_obra_canonica[686-0686-contratos] |
| 14 | sv4 | `infrastructure/database/review_repository.py` | `            document.obra_codigo = canonizar_codigo_obra(⏎                self._clean_text(payload.obra_codigo),⏎            )` | `            document.obra_codigo = self._clean_text(payload.obra_codigo)` | MUERTO | 148.3 | tests/test_f070_obra_canonica.py::test_f070_r12_guardar_cabecera_guarda_la_obra_canonica[686-0686] |
| 15 | sv9 | `domain/services/validador_alta.py` | `    return canonizar_codigo_obra(cab.obra_codigo) or ""` | `    return _texto(cab.obra_codigo)` | MUERTO | 42.2 | tests/test_f070_cod_obra.py::test_f070_r14_cod_obra_canonico[686-0686] |
| 16 | sv9 | `domain/services/validador_alta.py` | `    return canonizar_codigo_obra(cab.obra_codigo) or ""` | `    return canonizar_codigo_obra(cab.obra_codigo) or "X"` | MUERTO | 9.1 | tests/test_f053_servicio_duplicados.py::test_f053_r10_sin_llamadas_no_admitido[simulacion] |
| 17 | sv9 | `domain/services/validador_alta.py` | `    obra = _cod_obra(cab)⏎` | `    obra = _texto(cab.obra_codigo)⏎` | MUERTO | 39.8 | tests/test_f070_cod_obra.py::test_f070_r15_motivos_usan_la_misma_funcion_que_la_peticion |
| 18 | sv9 | `domain/services/validador_alta.py` | `        cod_obra=_cod_obra(cab),⏎` | `        cod_obra=_texto(cab.obra_codigo),⏎` | MUERTO | 41.3 | tests/test_f070_cod_obra.py::test_f070_r14_cod_obra_canonico[686-0686] |
