<!-- progress/impl_F-083_mutantes.md -->
# F-083 · Veredicto de cada mutante en las dos campañas

Generado desde la salida de `python -m harness.mutacion --feature F-083` de las dos campañas (c1: `--workers 4`, 2026-10-20 03:00–09:22, commit `6c40149`; c2: `--workers 3`, 2026-10-20 09:33 – 2026-10-21, commit `0912abd`, mismo código). Las dos generan los mismos 366 mutantes.

| Fichero | Mutantes |
|---|---|
| `evals/comparar_modelos.py` | 77 |
| `evals/costes.py` | 98 |
| `evals/decision.py` | 85 |
| `evals/informe_modelos.py` | 51 |
| `evals/procesos/medidor.py` | 25 |
| `evals/procesos/sv2_extraccion.py` | 1 |
| `evals/procesos/sv2_modelos.py` | 11 |
| `evals/procesos/sv5_modelos.py` | 9 |
| `evals/procesos/sv5_valoracion.py` | 6 |
| `evals/runner.py` | 2 |
| `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 1 |

| # | Mutante | c1 | c2 |
|---|---|---|---|
| 1 | `evals/comparar_modelos.py:139 [aritmetico] for repeticion in range(1, self.repeticiones + 1) -> for repeticion in range(1, self.repeticiones - 1)` | muerto | muerto |
| 2 | `evals/comparar_modelos.py:139 [entero] for repeticion in range(1, self.repeticiones + 1) -> for repeticion in range(1, self.repeticiones + 2)` | muerto | muerto |
| 3 | `evals/comparar_modelos.py:139 [entero] for repeticion in range(1, self.repeticiones + 1) -> for repeticion in range(2, self.repeticiones + 1)` | muerto | muerto |
| 4 | `evals/comparar_modelos.py:146 [aritmetico] Partida(modelo, "candidato", self.fase, len(self.casos) * self.repeticiones) -> Partida(modelo, "candidato", self.fase, len(self.casos) // self.repeticiones)` | muerto | muerto |
| 5 | `evals/comparar_modelos.py:149 [comparacion] if self.preparacion is not None: -> if self.preparacion is None:` | muerto | muerto |
| 6 | `evals/comparar_modelos.py:150 [entero] fase_previa = PREPARACION[self.fase][0] -> fase_previa = PREPARACION[self.fase][1]` | muerto | muerto |
| 7 | `evals/comparar_modelos.py:167 [comparacion] inputs = cargar_fixtures(fixtures, "inputs") if fase == "IA4" else {} -> inputs = cargar_fixtures(fixtures, "inputs") if fase != "IA4" else {}` | muerto | muerto |
| 8 | `evals/comparar_modelos.py:177 [comparacion] if fase in ("IA1", "IA2") and ruta_de_albaran(caso, albaranes) is None: -> if fase in ("IA1", "IA2") and ruta_de_albaran(caso, albaranes) is not None:` | muerto | muerto |
| 9 | `evals/comparar_modelos.py:177 [logico] if fase in ("IA1", "IA2") and ruta_de_albaran(caso, albaranes) is None: -> if fase in ("IA1", "IA2") or ruta_de_albaran(caso, albaranes) is None:` | muerto | muerto |
| 10 | `evals/comparar_modelos.py:179 [comparacion] elif fase == "IA4" and caso not in inputs: -> elif fase != "IA4" and caso not in inputs:` | muerto | muerto |
| 11 | `evals/comparar_modelos.py:179 [logico] elif fase == "IA4" and caso not in inputs: -> elif fase == "IA4" or caso not in inputs:` | muerto | muerto |
| 12 | `evals/comparar_modelos.py:194 [comparacion] elif tabla.modelo(modelo).papel == "excluido": -> elif tabla.modelo(modelo).papel != "excluido":` | muerto | muerto |
| 13 | `evals/comparar_modelos.py:198 [aritmetico] "modelos no válidos: " + "; ".join(malos) -> "modelos no válidos: " - "; ".join(malos)` | muerto | muerto |
| 14 | `evals/comparar_modelos.py:199 [aritmetico] + ". Válidos: " + ", ".join(tabla.validos()) -> + ". Válidos: " - ", ".join(tabla.validos())` | muerto | muerto |
| 15 | `evals/comparar_modelos.py:199 [aritmetico] + ". Válidos: " + ", ".join(tabla.validos()) -> - ". Válidos: " + ", ".join(tabla.validos())` | muerto | muerto |
| 16 | `evals/comparar_modelos.py:200 [aritmetico] + ". No se ha llamado a ningún LLM." -> - ". No se ha llamado a ningún LLM."` | muerto | muerto |
| 17 | `evals/comparar_modelos.py:203 [comparacion] modelos = [referencia, *(m for m in pedidos if m != referencia)] -> modelos = [referencia, *(m for m in pedidos if m == referencia)]` | muerto | muerto |
| 18 | `evals/comparar_modelos.py:204 [entero] preparacion = tabla.referencia(PREPARACION[fase][0]) if fase in PREPARACION else None -> preparacion = tabla.referencia(PREPARACION[fase][1]) if fase in PREPARACION else None` | muerto | muerto |
| 19 | `evals/comparar_modelos.py:206 [not] if not casos: -> if casos:` | muerto | muerto |
| 20 | `evals/comparar_modelos.py:262 [logico] tabla = dependencias.tabla or cargar_tabla() -> tabla = dependencias.tabla and cargar_tabla()` | muerto | muerto |
| 21 | `evals/comparar_modelos.py:271 [entero] return 0 -> return 1` | muerto | muerto |
| 22 | `evals/comparar_modelos.py:273 [comparacion] if estimacion.total > opciones.tope_usd: -> if estimacion.total >= opciones.tope_usd:` | muerto | muerto |
| 23 | `evals/comparar_modelos.py:279 [aritmetico] if acumulado + estimacion.total > opciones.tope_total_usd: -> if acumulado - estimacion.total > opciones.tope_total_usd:` | muerto | muerto |
| 24 | `evals/comparar_modelos.py:279 [comparacion] if acumulado + estimacion.total > opciones.tope_total_usd: -> if acumulado + estimacion.total >= opciones.tope_total_usd:` | muerto | muerto |
| 25 | `evals/comparar_modelos.py:347 [comparacion] ejecutar = dependencias.ejecutar_sv2 if "IA1" in trabajo_fase or trabajo_fase == "IA2" else ( -> ejecutar = dependencias.ejecutar_sv2 if "IA1" in trabajo_fase or trabajo_fase != "IA2" else (` | muerto | muerto |
| 26 | `evals/comparar_modelos.py:347 [logico] ejecutar = dependencias.ejecutar_sv2 if "IA1" in trabajo_fase or trabajo_fase == "IA2" else ( -> ejecutar = dependencias.ejecutar_sv2 if "IA1" in trabajo_fase and trabajo_fase == "IA2" else (` | muerto | muerto |
| 27 | `evals/comparar_modelos.py:366 [entero] return sum((Decimal(r.get("coste_usd", "0")) for r in registros), Decimal(0)) -> return sum((Decimal(r.get("coste_usd", "0")) for r in registros), Decimal(1))` | muerto | muerto |
| 28 | `evals/comparar_modelos.py:370 [logico] error = resultado.get("error") or {} -> error = resultado.get("error") and {}` | muerto | muerto |
| 29 | `evals/comparar_modelos.py:371 [logico] return f"ERROR en {error.get('fase') or '?'} · {error.get('motivo', '')}" -> return f"ERROR en {error.get('fase') and '?'} · {error.get('motivo', '')}"` | muerto | muerto |
| 30 | `evals/comparar_modelos.py:382 [comparacion] if preparacion is None: -> if preparacion is not None:` | muerto | muerto |
| 31 | `evals/comparar_modelos.py:391 [comparacion] if resultado is None: -> if resultado is not None:` | muerto | muerto |
| 32 | `evals/comparar_modelos.py:416 [comparacion] caso, fase, resultado, prep.get(caso), plan.preparacion is not None -> caso, fase, resultado, prep.get(caso), plan.preparacion is None` | muerto | muerto |
| 33 | `evals/comparar_modelos.py:418 [comparacion] if sin_evaluar is not None: -> if sin_evaluar is None:` | muerto | muerto |
| 34 | `evals/comparar_modelos.py:433 [comparacion] if plan.fase == "IA3": -> if plan.fase != "IA3":` | muerto | muerto |
| 35 | `evals/comparar_modelos.py:449 [comparacion] libros["IA3"] if plan.fase == "IA3" else {}, -> libros["IA3"] if plan.fase != "IA3" else {},` | muerto | muerto |
| 36 | `evals/comparar_modelos.py:450 [comparacion] libros["IA4"] if plan.fase == "IA4" else {}, -> libros["IA4"] if plan.fase != "IA4" else {},` | muerto | muerto |
| 37 | `evals/comparar_modelos.py:481 [booleano] salida.mkdir(parents=True, exist_ok=True) -> salida.mkdir(parents=False, exist_ok=True)` | muerto | muerto |
| 38 | `evals/comparar_modelos.py:481 [booleano] salida.mkdir(parents=True, exist_ok=True) -> salida.mkdir(parents=True, exist_ok=False)` | muerto | muerto |
| 39 | `evals/comparar_modelos.py:486 [entero] gastado = Decimal(0) -> gastado = Decimal(1)` | muerto | muerto |
| 40 | `evals/comparar_modelos.py:490 [comparacion] if plan.preparacion is not None: -> if plan.preparacion is None:` | muerto | muerto |
| 41 | `evals/comparar_modelos.py:492 [entero] PREPARACION[plan.fase][1], plan.preparacion, list(trabajos.values()), tope, -> PREPARACION[plan.fase][2], plan.preparacion, list(trabajos.values()), tope,` | muerto | muerto |
| 42 | `evals/comparar_modelos.py:497 [aritmetico] gastado += _gasto(bloque.registros) -> gastado -= _gasto(bloque.registros)` | muerto | muerto |
| 43 | `evals/comparar_modelos.py:500 [comparacion] salida_prep, campo_prep = ("documento", "ia1") if plan.fase == "IA2" else ("envelope", "envelope") -> salida_prep, campo_prep = ("documento", "ia1") if plan.fase != "IA2" else ("envelope", "envelope")` | muerto | muerto |
| 44 | `evals/comparar_modelos.py:507 [comparacion] if plan.preparacion is None: -> if plan.preparacion is not None:` | muerto | muerto |
| 45 | `evals/comparar_modelos.py:511 [aritmetico] restante = tope - gastado -> restante = tope + gastado` | muerto | muerto |
| 46 | `evals/comparar_modelos.py:512 [comparacion] if restante <= 0: -> if restante < 0:` | muerto | muerto |
| 47 | `evals/comparar_modelos.py:512 [entero] if restante <= 0: -> if restante <= 1:` | muerto | muerto |
| 48 | `evals/comparar_modelos.py:513 [booleano] bloque = Bloque({c["caso_id"]: {"caso_id": c["caso_id"], "no_ejecutado": True} -> bloque = Bloque({c["caso_id"]: {"caso_id": c["caso_id"], "no_ejecutado": False}` | muerto | muerto |
| 49 | `evals/comparar_modelos.py:520 [aritmetico] gastado += _gasto(bloque.registros) -> gastado -= _gasto(bloque.registros)` | muerto | muerto |
| 50 | `evals/comparar_modelos.py:521 [aritmetico] registros[modelo] += [{**r, "repeticion": repeticion} for r in bloque.registros] -> registros[modelo] -= [{**r, "repeticion": repeticion} for r in bloque.registros]` | muerto | muerto |
| 51 | `evals/comparar_modelos.py:541 [comparacion] if plan.preparacion is not None: -> if plan.preparacion is None:` | muerto | muerto |
| 52 | `evals/comparar_modelos.py:542 [entero] metricas_prep = medir(plan.preparacion, PREPARACION[plan.fase][0], [], -> metricas_prep = medir(plan.preparacion, PREPARACION[plan.fase][1], [],` | muerto | muerto |
| 53 | `evals/comparar_modelos.py:547 [entero] for repeticion, lista in enumerate(principal[modelo], start=1) -> for repeticion, lista in enumerate(principal[modelo], start=2)` | muerto | muerto |
| 54 | `evals/comparar_modelos.py:549 [comparacion] if caso.estado == ERROR -> if caso.estado != ERROR` | muerto | muerto |
| 55 | `evals/comparar_modelos.py:552 [comparacion] caso.estado == NO_EJECUTADO for listas in principal.values() for lista in listas for caso in lista -> caso.estado != NO_EJECUTADO for listas in principal.values() for lista in listas for caso in lista` | muerto | muerto |
| 56 | `evals/comparar_modelos.py:574 [booleano] resumen.parent.mkdir(parents=True, exist_ok=True) -> resumen.parent.mkdir(parents=False, exist_ok=True)` | muerto | muerto |
| 57 | `evals/comparar_modelos.py:574 [booleano] resumen.parent.mkdir(parents=True, exist_ok=True) -> resumen.parent.mkdir(parents=True, exist_ok=False)` | muerto | muerto |
| 58 | `evals/comparar_modelos.py:581 [booleano] ensure_ascii=False, indent=2, default=str, -> ensure_ascii=True, indent=2, default=str,` | muerto | muerto |
| 59 | `evals/comparar_modelos.py:581 [entero] ensure_ascii=False, indent=2, default=str, -> ensure_ascii=False, indent=3, default=str,` | muerto | muerto |
| 60 | `evals/comparar_modelos.py:589 [entero] return 3 -> return 4` | muerto | timeout |
| 61 | `evals/comparar_modelos.py:592 [entero] return 0 if alguno else 1 -> return 0 if alguno else 2` | muerto | muerto |
| 62 | `evals/comparar_modelos.py:592 [entero] return 0 if alguno else 1 -> return 1 if alguno else 1` | muerto | muerto |
| 63 | `evals/comparar_modelos.py:603 [comparacion] if valor < 0: -> if valor <= 0:` | muerto | muerto |
| 64 | `evals/comparar_modelos.py:603 [entero] if valor < 0: -> if valor < 1:` | muerto | muerto |
| 65 | `evals/comparar_modelos.py:620 [booleano] analizador.add_argument("--fase", required=True, choices=FASES) -> analizador.add_argument("--fase", required=False, choices=FASES)` | muerto | timeout |
| 66 | `evals/comparar_modelos.py:621 [booleano] analizador.add_argument("--modelos", required=True, help="ids de la tabla, separados por coma") -> analizador.add_argument("--modelos", required=False, help="ids de la tabla, separados por coma")` | muerto | muerto |
| 67 | `evals/comparar_modelos.py:623 [entero] analizador.add_argument("--repeticiones", type=int, default=1, help="por defecto 1") -> analizador.add_argument("--repeticiones", type=int, default=2, help="por defecto 1")` | muerto | timeout |
| 68 | `evals/comparar_modelos.py:637 [logico] opciones.lista_casos = _lista(opciones.casos) or None -> opciones.lista_casos = _lista(opciones.casos) and None` | muerto | muerto |
| 69 | `evals/comparar_modelos.py:638 [not] if not opciones.lista_modelos: -> if opciones.lista_modelos:` | muerto | timeout |
| 70 | `evals/comparar_modelos.py:640 [comparacion] if opciones.repeticiones < 1: -> if opciones.repeticiones <= 1:` | muerto | muerto |
| 71 | `evals/comparar_modelos.py:640 [entero] if opciones.repeticiones < 1: -> if opciones.repeticiones < 2:` | muerto | muerto |
| 72 | `evals/comparar_modelos.py:656 [comparacion] entorno if entorno is not None else dict(os.environ), -> entorno if entorno is None else dict(os.environ),` | muerto | muerto |
| 73 | `evals/comparar_modelos.py:657 [logico] dependencias or Dependencias(), -> dependencias and Dependencias(),` | muerto | muerto |
| 74 | `evals/comparar_modelos.py:661 [entero] return 2 -> return 3` | muerto | muerto |
| 75 | `evals/comparar_modelos.py:664 [comparacion] if __name__ == "__main__":  # pragma: no cover -> if __name__ != "__main__":  # pragma: no cover` | muerto | muerto |
| 76 | `evals/comparar_modelos.py:78 [entero] TOPE_USD = Decimal(25) -> TOPE_USD = Decimal(26)` | muerto | muerto |
| 77 | `evals/comparar_modelos.py:79 [entero] TOPE_TOTAL_USD = Decimal(200) -> TOPE_TOTAL_USD = Decimal(201)` | muerto | muerto |
| 78 | `evals/costes.py:102 [comparacion] return [m.id for m in self.modelos.values() if m.papel != "excluido"] -> return [m.id for m in self.modelos.values() if m.papel == "excluido"]` | muerto | muerto |
| 79 | `evals/costes.py:122 [logico] referencias = dict(datos.get("referencias") or {}) -> referencias = dict(datos.get("referencias") and {})` | muerto | muerto |
| 80 | `evals/costes.py:124 [logico] crudas = datos.get("estimacion_por_defecto") or {} -> crudas = datos.get("estimacion_por_defecto") and {}` | muerto | muerto |
| 81 | `evals/costes.py:127 [comparacion] if referencia not in modelos or modelos[referencia].papel == "excluido": -> if referencia not in modelos or modelos[referencia].papel != "excluido":` | muerto | muerto |
| 82 | `evals/costes.py:127 [logico] if referencia not in modelos or modelos[referencia].papel == "excluido": -> if referencia not in modelos and modelos[referencia].papel == "excluido":` | muerto | muerto |
| 83 | `evals/costes.py:143 [logico] modelo_id = str(crudo.get("id") or "").strip() -> modelo_id = str(crudo.get("id") and "").strip()` | muerto | muerto |
| 84 | `evals/costes.py:144 [not] if not modelo_id: -> if modelo_id:` | muerto | muerto |
| 85 | `evals/costes.py:149 [logico] if campo not in crudo or (isinstance(crudo[campo], str) and not crudo[campo].strip()): -> if campo not in crudo and (isinstance(crudo[campo], str) and not crudo[campo].strip()):` | muerto | muerto |
| 86 | `evals/costes.py:149 [logico] if campo not in crudo or (isinstance(crudo[campo], str) and not crudo[campo].strip()): -> if campo not in crudo or (isinstance(crudo[campo], str) or not crudo[campo].strip()):` | muerto | muerto |
| 87 | `evals/costes.py:149 [not] if campo not in crudo or (isinstance(crudo[campo], str) and not crudo[campo].strip()): -> if campo not in crudo or (isinstance(crudo[campo], str) and crudo[campo].strip()):` | muerto | muerto |
| 88 | `evals/costes.py:155 [logico] motivo = str(crudo.get("motivo") or "").strip() -> motivo = str(crudo.get("motivo") and "").strip()` | muerto | muerto |
| 89 | `evals/costes.py:156 [comparacion] if crudo["papel"] == "excluido" and not motivo: -> if crudo["papel"] != "excluido" and not motivo:` | muerto | muerto |
| 90 | `evals/costes.py:156 [logico] if crudo["papel"] == "excluido" and not motivo: -> if crudo["papel"] == "excluido" or not motivo:` | muerto | muerto |
| 91 | `evals/costes.py:156 [not] if crudo["papel"] == "excluido" and not motivo: -> if crudo["papel"] == "excluido" and motivo:` | muerto | muerto |
| 92 | `evals/costes.py:159 [comparacion] if crudo["proveedor"] == "claude" and not isinstance(herramienta, bool): -> if crudo["proveedor"] != "claude" and not isinstance(herramienta, bool):` | muerto | muerto |
| 93 | `evals/costes.py:159 [logico] if crudo["proveedor"] == "claude" and not isinstance(herramienta, bool): -> if crudo["proveedor"] == "claude" or not isinstance(herramienta, bool):` | muerto | muerto |
| 94 | `evals/costes.py:159 [not] if crudo["proveedor"] == "claude" and not isinstance(herramienta, bool): -> if crudo["proveedor"] == "claude" and isinstance(herramienta, bool):` | muerto | muerto |
| 95 | `evals/costes.py:163 [comparacion] if crudo.get("tramo_largo") is not None: -> if crudo.get("tramo_largo") is None:` | muerto | muerto |
| 96 | `evals/costes.py:167 [logico] precio=_precio(tramo_crudo.get("precio") or {}, f"{donde}: tramo_largo"), -> precio=_precio(tramo_crudo.get("precio") and {}, f"{donde}: tramo_largo"),` | muerto | muerto |
| 97 | `evals/costes.py:172 [logico] precio=_precio(crudo.get("precio") or {}, donde), -> precio=_precio(crudo.get("precio") and {}, donde),` | muerto | muerto |
| 98 | `evals/costes.py:187 [comparacion] if crudo.get("siguiente") is not None: -> if crudo.get("siguiente") is None:` | muerto | muerto |
| 99 | `evals/costes.py:190 [comparacion] if crudo.get("vigente_hasta") is not None: -> if crudo.get("vigente_hasta") is None:` | muerto | muerto |
| 100 | `evals/costes.py:202 [comparacion] if valor < 0: -> if valor <= 0:` | muerto | muerto |
| 101 | `evals/costes.py:202 [entero] if valor < 0: -> if valor < 1:` | muerto | muerto |
| 102 | `evals/costes.py:217 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)` | muerto | muerto |
| 103 | `evals/costes.py:225 [booleano] incompleto: bool = False -> incompleto: bool = True` | muerto | muerto |
| 104 | `evals/costes.py:230 [aritmetico] return self.entrada + self.lectura_cache + self.escritura_cache -> return self.entrada + self.lectura_cache - self.escritura_cache` | muerto | muerto |
| 105 | `evals/costes.py:230 [aritmetico] return self.entrada + self.lectura_cache + self.escritura_cache -> return self.entrada - self.lectura_cache + self.escritura_cache` | muerto | muerto |
| 106 | `evals/costes.py:245 [comparacion] if valor is None: -> if valor is not None:` | muerto | muerto |
| 107 | `evals/costes.py:246 [entero] return 0, obligatorio -> return 1, obligatorio` | muerto | muerto |
| 108 | `evals/costes.py:247 [logico] if isinstance(valor, bool) or not isinstance(valor, int): -> if isinstance(valor, bool) and not isinstance(valor, int):` | muerto | muerto |
| 109 | `evals/costes.py:247 [not] if isinstance(valor, bool) or not isinstance(valor, int): -> if isinstance(valor, bool) or isinstance(valor, int):` | muerto | muerto |
| 110 | `evals/costes.py:248 [booleano] return 0, True -> return 0, False` | muerto | muerto |
| 111 | `evals/costes.py:248 [entero] return 0, True -> return 1, True` | muerto | muerto |
| 112 | `evals/costes.py:249 [booleano] return valor, False -> return valor, True` | muerto | muerto |
| 113 | `evals/costes.py:258 [booleano] ("input_tokens", True), -> ("input_tokens", False),` | muerto | muerto |
| 114 | `evals/costes.py:259 [booleano] ("cache_read_input_tokens", False), -> ("cache_read_input_tokens", True),` | muerto | muerto |
| 115 | `evals/costes.py:260 [booleano] ("cache_creation_input_tokens", False), -> ("cache_creation_input_tokens", True),` | muerto | muerto |
| 116 | `evals/costes.py:261 [booleano] ("output_tokens", True), -> ("output_tokens", False),` | muerto | muerto |
| 117 | `evals/costes.py:266 [booleano] ("input_tokens", True), -> ("input_tokens", False),` | muerto | muerto |
| 118 | `evals/costes.py:267 [booleano] ("input_tokens_details.cached_tokens", False), -> ("input_tokens_details.cached_tokens", True),` | muerto | muerto |
| 119 | `evals/costes.py:269 [booleano] ("output_tokens", True), -> ("output_tokens", False),` | muerto | muerto |
| 120 | `evals/costes.py:274 [booleano] ("prompt_token_count", True), -> ("prompt_token_count", False),` | muerto | muerto |
| 121 | `evals/costes.py:275 [booleano] ("cached_content_token_count", False), -> ("cached_content_token_count", True),` | muerto | muerto |
| 122 | `evals/costes.py:277 [booleano] ("candidates_token_count", True), -> ("candidates_token_count", False),` | muerto | muerto |
| 123 | `evals/costes.py:278 [booleano] ("thoughts_token_count", False), -> ("thoughts_token_count", True),` | muerto | muerto |
| 124 | `evals/costes.py:289 [booleano] return Uso(0, 0, 0, 0, True) -> return Uso(0, 0, 0, 0, False)` | muerto | muerto |
| 125 | `evals/costes.py:289 [entero] return Uso(0, 0, 0, 0, True) -> return Uso(0, 0, 0, 1, True)` | muerto | muerto |
| 126 | `evals/costes.py:289 [entero] return Uso(0, 0, 0, 0, True) -> return Uso(0, 0, 1, 0, True)` | muerto | muerto |
| 127 | `evals/costes.py:289 [entero] return Uso(0, 0, 0, 0, True) -> return Uso(0, 1, 0, 0, True)` | muerto | muerto |
| 128 | `evals/costes.py:289 [entero] return Uso(0, 0, 0, 0, True) -> return Uso(1, 0, 0, 0, True)` | muerto | muerto |
| 129 | `evals/costes.py:293 [booleano] falta = False -> falta = True` | muerto | muerto |
| 130 | `evals/costes.py:295 [comparacion] if campo is None: -> if campo is not None:` | muerto | muerto |
| 131 | `evals/costes.py:296 [entero] valores.append(0) -> valores.append(1)` | muerto | muerto |
| 132 | `evals/costes.py:305 [logico] falta = falta or ausente -> falta = falta and ausente` | muerto | muerto |
| 133 | `evals/costes.py:308 [comparacion] falta = falta or lectura > entrada -> falta = falta or lectura >= entrada` | muerto | muerto |
| 134 | `evals/costes.py:308 [logico] falta = falta or lectura > entrada -> falta = falta and lectura > entrada` | muerto | muerto |
| 135 | `evals/costes.py:309 [aritmetico] entrada = max(entrada - lectura, 0) -> entrada = max(entrada + lectura, 0)` | muerto | muerto |
| 136 | `evals/costes.py:309 [entero] entrada = max(entrada - lectura, 0) -> entrada = max(entrada - lectura, 1)` | muerto | muerto |
| 137 | `evals/costes.py:310 [aritmetico] return Uso(entrada, lectura, escritura, salida + pensamiento, falta) -> return Uso(entrada, lectura, escritura, salida - pensamiento, falta)` | muerto | muerto |
| 138 | `evals/costes.py:314 [comparacion] if valor is None: -> if valor is not None:` | muerto | muerto |
| 139 | `evals/costes.py:323 [comparacion] if proveedor == "gemini": -> if proveedor != "gemini":` | muerto | muerto |
| 140 | `evals/costes.py:33 [entero] TOPE_TEXTO = 60 -> TOPE_TEXTO = 61` | muerto | muerto |
| 141 | `evals/costes.py:330 [comparacion] if proveedor == "claude": -> if proveedor != "claude":` | muerto | muerto |
| 142 | `evals/costes.py:332 [comparacion] if proveedor == "openai": -> if proveedor != "openai":` | muerto | muerto |
| 143 | `evals/costes.py:335 [comparacion] return _texto_corto(estado if razon is None else f"{estado}:{razon}") -> return _texto_corto(estado if razon is not None else f"{estado}:{razon}")` | muerto | muerto |
| 144 | `evals/costes.py:336 [comparacion] if proveedor == "gemini": -> if proveedor != "gemini":` | muerto | muerto |
| 145 | `evals/costes.py:337 [logico] candidatos = _campo(respuesta, "candidates") or [] -> candidatos = _campo(respuesta, "candidates") and []` | muerto | muerto |
| 146 | `evals/costes.py:338 [not] if not candidatos: -> if candidatos:` | muerto | muerto |
| 147 | `evals/costes.py:340 [entero] motivo = _campo(candidatos[0], "finish_reason") -> motivo = _campo(candidatos[1], "finish_reason")` | muerto | muerto |
| 148 | `evals/costes.py:351 [comparacion] while precio.vigente_hasta is not None and fecha > precio.vigente_hasta: -> while precio.vigente_hasta is None and fecha > precio.vigente_hasta:` | muerto | muerto |
| 149 | `evals/costes.py:351 [comparacion] while precio.vigente_hasta is not None and fecha > precio.vigente_hasta: -> while precio.vigente_hasta is not None and fecha >= precio.vigente_hasta:` | muerto | muerto |
| 150 | `evals/costes.py:351 [logico] while precio.vigente_hasta is not None and fecha > precio.vigente_hasta: -> while precio.vigente_hasta is not None or fecha > precio.vigente_hasta:` | muerto | muerto |
| 151 | `evals/costes.py:352 [comparacion] if precio.siguiente is None: -> if precio.siguiente is not None:` | muerto | muerto |
| 152 | `evals/costes.py:36 [entero] MILLON = Decimal(1_000_000) -> MILLON = Decimal(1000001)` | muerto | muerto |
| 153 | `evals/costes.py:366 [comparacion] if tramo is not None and uso.entrada_total > tramo.umbral: -> if tramo is None and uso.entrada_total > tramo.umbral:` | muerto | muerto |
| 154 | `evals/costes.py:366 [comparacion] if tramo is not None and uso.entrada_total > tramo.umbral: -> if tramo is not None and uso.entrada_total >= tramo.umbral:` | muerto | muerto |
| 155 | `evals/costes.py:366 [logico] if tramo is not None and uso.entrada_total > tramo.umbral: -> if tramo is not None or uso.entrada_total > tramo.umbral:` | muerto | muerto |
| 156 | `evals/costes.py:369 [aritmetico] uso.entrada * precio.entrada -> uso.entrada // precio.entrada` | muerto | muerto |
| 157 | `evals/costes.py:370 [aritmetico] + uso.lectura_cache * precio.lectura_cache -> + uso.lectura_cache // precio.lectura_cache` | muerto | muerto |
| 158 | `evals/costes.py:370 [aritmetico] + uso.lectura_cache * precio.lectura_cache -> - uso.lectura_cache * precio.lectura_cache` | muerto | muerto |
| 159 | `evals/costes.py:371 [aritmetico] + uso.escritura_cache * precio.escritura_cache -> + uso.escritura_cache // precio.escritura_cache` | muerto | muerto |
| 160 | `evals/costes.py:371 [aritmetico] + uso.escritura_cache * precio.escritura_cache -> - uso.escritura_cache * precio.escritura_cache` | muerto | muerto |
| 161 | `evals/costes.py:372 [aritmetico] + uso.salida * precio.salida -> + uso.salida // precio.salida` | muerto | muerto |
| 162 | `evals/costes.py:372 [aritmetico] + uso.salida * precio.salida -> - uso.salida * precio.salida` | muerto | muerto |
| 163 | `evals/costes.py:379 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)` | muerto | muerto |
| 164 | `evals/costes.py:389 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)` | muerto | muerto |
| 165 | `evals/costes.py:401 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)` | muerto | muerto |
| 166 | `evals/costes.py:422 [aritmetico] entrada, salida = int(entrada * margen), int(salida * margen) -> entrada, salida = int(entrada * margen), int(salida // margen)` | muerto | muerto |
| 167 | `evals/costes.py:422 [aritmetico] entrada, salida = int(entrada * margen), int(salida * margen) -> entrada, salida = int(entrada // margen), int(salida * margen)` | muerto | muerto |
| 168 | `evals/costes.py:424 [entero] por_llamada = coste_usd(tabla.modelo(partida.modelo), Uso(entrada, 0, 0, salida), fecha) -> por_llamada = coste_usd(tabla.modelo(partida.modelo), Uso(entrada, 0, 1, salida), fecha)` | muerto | muerto |
| 169 | `evals/costes.py:424 [entero] por_llamada = coste_usd(tabla.modelo(partida.modelo), Uso(entrada, 0, 0, salida), fecha) -> por_llamada = coste_usd(tabla.modelo(partida.modelo), Uso(entrada, 1, 0, salida), fecha)` | muerto | muerto |
| 170 | `evals/costes.py:434 [aritmetico] usd=por_llamada * partida.llamadas, -> usd=por_llamada // partida.llamadas,` | muerto | muerto |
| 171 | `evals/costes.py:437 [entero] return Estimacion(lineas=lineas, total=sum((linea.usd for linea in lineas), Decimal(0))) -> return Estimacion(lineas=lineas, total=sum((linea.usd for linea in lineas), Decimal(1)))` | muerto | muerto |
| 172 | `evals/costes.py:47 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)` | muerto | muerto |
| 173 | `evals/costes.py:59 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)` | muerto | muerto |
| 174 | `evals/costes.py:67 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)` | muerto | muerto |
| 175 | `evals/costes.py:82 [booleano] @dataclass(frozen=True) -> @dataclass(frozen=False)` | muerto | muerto |
| 176 | `evals/decision.py:100 [comparacion] propios = [r for r in registros if r.get("etiqueta") == etiqueta] -> propios = [r for r in registros if r.get("etiqueta") != etiqueta]` | muerto | muerto |
| 177 | `evals/decision.py:104 [entero] entrada = salida = respondidas = 0 -> entrada = salida = respondidas = 1` | muerto | muerto |
| 178 | `evals/decision.py:107 [aritmetico] metricas.coste_total += Decimal(registro["coste_usd"]) -> metricas.coste_total -= Decimal(registro["coste_usd"])` | muerto | muerto |
| 179 | `evals/decision.py:108 [aritmetico] metricas.fallos_medidor += bool(registro.get("fallo_medidor")) -> metricas.fallos_medidor -= bool(registro.get("fallo_medidor"))` | muerto | muerto |
| 180 | `evals/decision.py:109 [aritmetico] metricas.uso_incompleto += bool(registro.get("uso_incompleto")) -> metricas.uso_incompleto -= bool(registro.get("uso_incompleto"))` | muerto | muerto |
| 181 | `evals/decision.py:111 [aritmetico] duraciones[albaran] = duraciones.get(albaran, 0) + registro["duracion_ms"] -> duraciones[albaran] = duraciones.get(albaran, 0) - registro["duracion_ms"]` | muerto | muerto |
| 182 | `evals/decision.py:111 [entero] duraciones[albaran] = duraciones.get(albaran, 0) + registro["duracion_ms"] -> duraciones[albaran] = duraciones.get(albaran, 1) + registro["duracion_ms"]` | muerto | muerto |
| 183 | `evals/decision.py:115 [aritmetico] respondidas += 1 -> respondidas -= 1` | muerto | timeout |
| 184 | `evals/decision.py:115 [entero] respondidas += 1 -> respondidas += 2` | muerto | muerto |
| 185 | `evals/decision.py:116 [aritmetico] entrada += ( -> entrada -= (` | muerto | muerto |
| 186 | `evals/decision.py:117 [aritmetico] registro["entrada"] + registro["lectura_cache"] + registro["escritura_cache"] -> registro["entrada"] + registro["lectura_cache"] - registro["escritura_cache"]` | muerto | muerto |
| 187 | `evals/decision.py:117 [aritmetico] registro["entrada"] + registro["lectura_cache"] + registro["escritura_cache"] -> registro["entrada"] - registro["lectura_cache"] + registro["escritura_cache"]` | muerto | muerto |
| 188 | `evals/decision.py:119 [aritmetico] salida += registro["salida"] -> salida -= registro["salida"]` | muerto | muerto |
| 189 | `evals/decision.py:124 [aritmetico] motivos[registro["motivo_parada"]] += 1 -> motivos[registro["motivo_parada"]] -= 1` | muerto | muerto |
| 190 | `evals/decision.py:124 [entero] motivos[registro["motivo_parada"]] += 1 -> motivos[registro["motivo_parada"]] += 2` | muerto | muerto |
| 191 | `evals/decision.py:128 [entero] metricas.tiempo_medio_s = _media(sum(duraciones.values()), len(duraciones)) / 1000 -> metricas.tiempo_medio_s = _media(sum(duraciones.values()), len(duraciones)) / 1001` | muerto | muerto |
| 192 | `evals/decision.py:129 [entero] metricas.tiempo_max_s = Decimal(max(duraciones.values(), default=0)) / 1000 -> metricas.tiempo_max_s = Decimal(max(duraciones.values(), default=0)) / 1001` | muerto | muerto |
| 193 | `evals/decision.py:129 [entero] metricas.tiempo_max_s = Decimal(max(duraciones.values(), default=0)) / 1000 -> metricas.tiempo_max_s = Decimal(max(duraciones.values(), default=1)) / 1000` | muerto | muerto |
| 194 | `evals/decision.py:148 [comparacion] if repeticiones >= REPETICIONES_FIRMES: -> if repeticiones > REPETICIONES_FIRMES:` | muerto | muerto |
| 195 | `evals/decision.py:150 [comparacion] return f"provisional ({repeticiones} repetici{'ón' if repeticiones == 1 else 'ones'})" -> return f"provisional ({repeticiones} repetici{'ón' if repeticiones != 1 else 'ones'})"` | muerto | muerto |
| 196 | `evals/decision.py:150 [entero] return f"provisional ({repeticiones} repetici{'ón' if repeticiones == 1 else 'ones'})" -> return f"provisional ({repeticiones} repetici{'ón' if repeticiones == 2 else 'ones'})"` | muerto | muerto |
| 197 | `evals/decision.py:158 [comparacion] if ref is None or ref.errores or ref.no_ejecutados or not ref.casos: -> if ref is not None or ref.errores or ref.no_ejecutados or not ref.casos:` | muerto | muerto |
| 198 | `evals/decision.py:158 [logico] if ref is None or ref.errores or ref.no_ejecutados or not ref.casos: -> if ref is None and ref.errores or ref.no_ejecutados or not ref.casos:` | muerto | muerto |
| 199 | `evals/decision.py:158 [logico] if ref is None or ref.errores or ref.no_ejecutados or not ref.casos: -> if ref is None or ref.errores and ref.no_ejecutados or not ref.casos:` | muerto | muerto |
| 200 | `evals/decision.py:158 [logico] if ref is None or ref.errores or ref.no_ejecutados or not ref.casos: -> if ref is None or ref.errores or ref.no_ejecutados and not ref.casos:` | muerto | muerto |
| 201 | `evals/decision.py:158 [not] if ref is None or ref.errores or ref.no_ejecutados or not ref.casos: -> if ref is None or ref.errores or ref.no_ejecutados or ref.casos:` | muerto | muerto |
| 202 | `evals/decision.py:163 [comparacion] if not m.errores and not m.no_ejecutados and m.fallos <= ref.fallos -> if not m.errores and not m.no_ejecutados and m.fallos < ref.fallos` | muerto | muerto |
| 203 | `evals/decision.py:163 [logico] if not m.errores and not m.no_ejecutados and m.fallos <= ref.fallos -> if not m.errores and not m.no_ejecutados or m.fallos <= ref.fallos` | muerto | muerto |
| 204 | `evals/decision.py:163 [logico] if not m.errores and not m.no_ejecutados and m.fallos <= ref.fallos -> if not m.errores or not m.no_ejecutados and m.fallos <= ref.fallos` | muerto | muerto |
| 205 | `evals/decision.py:163 [not] if not m.errores and not m.no_ejecutados and m.fallos <= ref.fallos -> if m.errores and not m.no_ejecutados and m.fallos <= ref.fallos` | muerto | muerto |
| 206 | `evals/decision.py:163 [not] if not m.errores and not m.no_ejecutados and m.fallos <= ref.fallos -> if not m.errores and m.no_ejecutados and m.fallos <= ref.fallos` | muerto | muerto |
| 207 | `evals/decision.py:166 [aritmetico] holgura = max(Decimal(BANDA_MINIMA), BANDA_RELATIVA * mejor) -> holgura = max(Decimal(BANDA_MINIMA), BANDA_RELATIVA // mejor)` | muerto | muerto |
| 208 | `evals/decision.py:167 [aritmetico] banda = [m for m in elegibles if m.fallos <= mejor + holgura] -> banda = [m for m in elegibles if m.fallos <= mejor - holgura]` | muerto | muerto |
| 209 | `evals/decision.py:167 [comparacion] banda = [m for m in elegibles if m.fallos <= mejor + holgura] -> banda = [m for m in elegibles if m.fallos < mejor + holgura]` | muerto | muerto |
| 210 | `evals/decision.py:172 [comparacion] if m is barato -> if m is not barato` | muerto | muerto |
| 211 | `evals/decision.py:173 [aritmetico] or m.coste_por_albaran - barato.coste_por_albaran < EMPATE_COSTE * barato.coste_por_albaran -> or m.coste_por_albaran + barato.coste_por_albaran < EMPATE_COSTE * barato.coste_por_albaran` | muerto | muerto |
| 212 | `evals/decision.py:173 [aritmetico] or m.coste_por_albaran - barato.coste_por_albaran < EMPATE_COSTE * barato.coste_por_albaran -> or m.coste_por_albaran - barato.coste_por_albaran < EMPATE_COSTE // barato.coste_por_albaran` | muerto | muerto |
| 213 | `evals/decision.py:173 [comparacion] or m.coste_por_albaran - barato.coste_por_albaran < EMPATE_COSTE * barato.coste_por_albaran -> or m.coste_por_albaran - barato.coste_por_albaran <= EMPATE_COSTE * barato.coste_por_albaran` | muerto | muerto |
| 214 | `evals/decision.py:173 [logico] or m.coste_por_albaran - barato.coste_por_albaran < EMPATE_COSTE * barato.coste_por_albaran -> and m.coste_por_albaran - barato.coste_por_albaran < EMPATE_COSTE * barato.coste_por_albaran` | muerto | muerto |
| 215 | `evals/decision.py:178 [comparacion] if elegido.modelo != referencia: -> if elegido.modelo == referencia:` | muerto | muerto |
| 216 | `evals/decision.py:180 [aritmetico] elegido.fallos <= MEJORA_FALLOS * ref.fallos -> elegido.fallos <= MEJORA_FALLOS // ref.fallos` | muerto | timeout |
| 217 | `evals/decision.py:180 [comparacion] elegido.fallos <= MEJORA_FALLOS * ref.fallos -> elegido.fallos < MEJORA_FALLOS * ref.fallos` | muerto | timeout |
| 218 | `evals/decision.py:181 [aritmetico] and elegido.coste_por_albaran <= MEJORA_COSTE * ref.coste_por_albaran -> and elegido.coste_por_albaran <= MEJORA_COSTE // ref.coste_por_albaran` | muerto | muerto |
| 219 | `evals/decision.py:181 [comparacion] and elegido.coste_por_albaran <= MEJORA_COSTE * ref.coste_por_albaran -> and elegido.coste_por_albaran < MEJORA_COSTE * ref.coste_por_albaran` | muerto | timeout |
| 220 | `evals/decision.py:181 [logico] and elegido.coste_por_albaran <= MEJORA_COSTE * ref.coste_por_albaran -> or elegido.coste_por_albaran <= MEJORA_COSTE * ref.coste_por_albaran` | muerto | muerto |
| 221 | `evals/decision.py:183 [aritmetico] ahorro = elegido.coste_por_albaran <= AHORRO_COSTE * ref.coste_por_albaran -> ahorro = elegido.coste_por_albaran <= AHORRO_COSTE // ref.coste_por_albaran` | muerto | muerto |
| 222 | `evals/decision.py:183 [comparacion] ahorro = elegido.coste_por_albaran <= AHORRO_COSTE * ref.coste_por_albaran -> ahorro = elegido.coste_por_albaran < AHORRO_COSTE * ref.coste_por_albaran` | muerto | muerto |
| 223 | `evals/decision.py:184 [logico] if mejora or ahorro: -> if mejora and ahorro:` | muerto | muerto |
| 224 | `evals/decision.py:188 [aritmetico] if elegido.tiempo_medio_s > LATENCIA * ref.tiempo_medio_s: -> if elegido.tiempo_medio_s > LATENCIA // ref.tiempo_medio_s:` | muerto | muerto |
| 225 | `evals/decision.py:188 [comparacion] if elegido.tiempo_medio_s > LATENCIA * ref.tiempo_medio_s: -> if elegido.tiempo_medio_s >= LATENCIA * ref.tiempo_medio_s:` | muerto | muerto |
| 226 | `evals/decision.py:32 [entero] BANDA_MINIMA = 2 -> BANDA_MINIMA = 3` | muerto | muerto |
| 227 | `evals/decision.py:38 [entero] LATENCIA = 2 -> LATENCIA = 3` | muerto | muerto |
| 228 | `evals/decision.py:39 [entero] REPETICIONES_FIRMES = 3 -> REPETICIONES_FIRMES = 4` | muerto | muerto |
| 229 | `evals/decision.py:48 [entero] repeticiones: int = 1 -> repeticiones: int = 2` | muerto | muerto |
| 230 | `evals/decision.py:49 [entero] casos: int = 0 -> casos: int = 1` | muerto | muerto |
| 231 | `evals/decision.py:50 [entero] errores: int = 0 -> errores: int = 1` | muerto | muerto |
| 232 | `evals/decision.py:51 [entero] no_ejecutados: int = 0 -> no_ejecutados: int = 1` | muerto | muerto |
| 233 | `evals/decision.py:52 [entero] verdes: int = 0 -> verdes: int = 1` | muerto | muerto |
| 234 | `evals/decision.py:53 [entero] fallos: Decimal = Decimal(0) -> fallos: Decimal = Decimal(1)` | muerto | muerto |
| 235 | `evals/decision.py:54 [entero] fallos_min: int = 0 -> fallos_min: int = 1` | muerto | muerto |
| 236 | `evals/decision.py:55 [entero] fallos_max: int = 0 -> fallos_max: int = 1` | muerto | muerto |
| 237 | `evals/decision.py:56 [entero] avisos: int = 0 -> avisos: int = 1` | muerto | muerto |
| 238 | `evals/decision.py:57 [entero] tiempo_medio_s: Decimal = Decimal(0) -> tiempo_medio_s: Decimal = Decimal(1)` | muerto | muerto |
| 239 | `evals/decision.py:58 [entero] tiempo_max_s: Decimal = Decimal(0) -> tiempo_max_s: Decimal = Decimal(1)` | muerto | muerto |
| 240 | `evals/decision.py:59 [entero] llamadas: int = 0 -> llamadas: int = 1` | muerto | muerto |
| 241 | `evals/decision.py:60 [entero] tokens_entrada_medios: Decimal = Decimal(0) -> tokens_entrada_medios: Decimal = Decimal(1)` | muerto | muerto |
| 242 | `evals/decision.py:61 [entero] tokens_salida_medios: Decimal = Decimal(0) -> tokens_salida_medios: Decimal = Decimal(1)` | muerto | muerto |
| 243 | `evals/decision.py:62 [entero] coste_total: Decimal = Decimal(0) -> coste_total: Decimal = Decimal(1)` | muerto | muerto |
| 244 | `evals/decision.py:63 [entero] coste_por_albaran: Decimal = Decimal(0) -> coste_por_albaran: Decimal = Decimal(1)` | muerto | muerto |
| 245 | `evals/decision.py:64 [entero] uso_incompleto: int = 0 -> uso_incompleto: int = 1` | muerto | muerto |
| 246 | `evals/decision.py:65 [entero] fallos_medidor: int = 0 -> fallos_medidor: int = 1` | muerto | muerto |
| 247 | `evals/decision.py:71 [entero] return Decimal(total) / cuantos if cuantos else Decimal(0) -> return Decimal(total) / cuantos if cuantos else Decimal(1)` | muerto | muerto |
| 248 | `evals/decision.py:90 [aritmetico] metricas.casos += len(evaluados) -> metricas.casos -= len(evaluados)` | muerto | muerto |
| 249 | `evals/decision.py:91 [aritmetico] metricas.errores += sum(1 for c in casos if c.estado == ERROR) -> metricas.errores -= sum(1 for c in casos if c.estado == ERROR)` | muerto | muerto |
| 250 | `evals/decision.py:91 [comparacion] metricas.errores += sum(1 for c in casos if c.estado == ERROR) -> metricas.errores += sum(1 for c in casos if c.estado != ERROR)` | muerto | muerto |
| 251 | `evals/decision.py:91 [entero] metricas.errores += sum(1 for c in casos if c.estado == ERROR) -> metricas.errores += sum(2 for c in casos if c.estado == ERROR)` | muerto | muerto |
| 252 | `evals/decision.py:92 [aritmetico] metricas.no_ejecutados += sum(1 for c in casos if c.estado == NO_EJECUTADO) -> metricas.no_ejecutados -= sum(1 for c in casos if c.estado == NO_EJECUTADO)` | muerto | muerto |
| 253 | `evals/decision.py:92 [comparacion] metricas.no_ejecutados += sum(1 for c in casos if c.estado == NO_EJECUTADO) -> metricas.no_ejecutados += sum(1 for c in casos if c.estado != NO_EJECUTADO)` | muerto | muerto |
| 254 | `evals/decision.py:92 [entero] metricas.no_ejecutados += sum(1 for c in casos if c.estado == NO_EJECUTADO) -> metricas.no_ejecutados += sum(2 for c in casos if c.estado == NO_EJECUTADO)` | muerto | muerto |
| 255 | `evals/decision.py:93 [aritmetico] metricas.verdes += sum(1 for c in evaluados if c.estado == VERDE) -> metricas.verdes -= sum(1 for c in evaluados if c.estado == VERDE)` | muerto | muerto |
| 256 | `evals/decision.py:93 [comparacion] metricas.verdes += sum(1 for c in evaluados if c.estado == VERDE) -> metricas.verdes += sum(1 for c in evaluados if c.estado != VERDE)` | muerto | muerto |
| 257 | `evals/decision.py:93 [entero] metricas.verdes += sum(1 for c in evaluados if c.estado == VERDE) -> metricas.verdes += sum(2 for c in evaluados if c.estado == VERDE)` | muerto | muerto |
| 258 | `evals/decision.py:94 [aritmetico] metricas.avisos += sum(len(c.avisos) for c in evaluados) -> metricas.avisos -= sum(len(c.avisos) for c in evaluados)` | muerto | muerto |
| 259 | `evals/decision.py:97 [entero] metricas.fallos_min = min(fallos_por_rep, default=0) -> metricas.fallos_min = min(fallos_por_rep, default=1)` | muerto | muerto |
| 260 | `evals/decision.py:98 [entero] metricas.fallos_max = max(fallos_por_rep, default=0) -> metricas.fallos_max = max(fallos_por_rep, default=1)` | muerto | muerto |
| 261 | `evals/informe_modelos.py:101 [not] if not metricas.modelos_servidos: -> if metricas.modelos_servidos:` | muerto | muerto |
| 262 | `evals/informe_modelos.py:110 [logico] return ", ".join(f"{motivo} ×{n}" for motivo, n in sorted(metricas.motivos_parada.items())) or "—" -> return ", ".join(f"{motivo} ×{n}" for motivo, n in sorted(metricas.motivos_parada.items())) and "—"` | muerto | muerto |
| 263 | `evals/informe_modelos.py:118 [aritmetico] "\|---\|" + "---\|" * 15, -> "\|---\|" + "---\|" // 15,` | muerto | muerto |
| 264 | `evals/informe_modelos.py:118 [aritmetico] "\|---\|" + "---\|" * 15, -> "\|---\|" - "---\|" * 15,` | muerto | muerto |
| 265 | `evals/informe_modelos.py:118 [entero] "\|---\|" + "---\|" * 15, -> "\|---\|" + "---\|" * 16,` | muerto | muerto |
| 266 | `evals/informe_modelos.py:128 [aritmetico] lineas.append("\| " + " \| ".join(str(c) for c in celdas) + " \|") -> lineas.append("\| " + " \| ".join(str(c) for c in celdas) - " \|")` | muerto | muerto |
| 267 | `evals/informe_modelos.py:128 [aritmetico] lineas.append("\| " + " \| ".join(str(c) for c in celdas) + " \|") -> lineas.append("\| " - " \| ".join(str(c) for c in celdas) + " \|")` | muerto | muerto |
| 268 | `evals/informe_modelos.py:134 [aritmetico] "\|---\|" + "---\|" * 6] -> "\|---\|" + "---\|" // 6]` | muerto | muerto |
| 269 | `evals/informe_modelos.py:134 [aritmetico] "\|---\|" + "---\|" * 6] -> "\|---\|" - "---\|" * 6]` | muerto | muerto |
| 270 | `evals/informe_modelos.py:134 [entero] "\|---\|" + "---\|" * 6] -> "\|---\|" + "---\|" * 7]` | muerto | muerto |
| 271 | `evals/informe_modelos.py:138 [aritmetico] lineas.append("\| " + " \| ".join(str(c) for c in celdas) + " \|") -> lineas.append("\| " + " \| ".join(str(c) for c in celdas) - " \|")` | muerto | muerto |
| 272 | `evals/informe_modelos.py:138 [aritmetico] lineas.append("\| " + " \| ".join(str(c) for c in celdas) + " \|") -> lineas.append("\| " - " \| ".join(str(c) for c in celdas) + " \|")` | muerto | muerto |
| 273 | `evals/informe_modelos.py:144 [aritmetico] titulo = "### Recomendación" + (f" · {r.etiqueta_provisional}" if r.provisional else "") -> titulo = "### Recomendación" - (f" · {r.etiqueta_provisional}" if r.provisional else "")` | muerto | muerto |
| 274 | `evals/informe_modelos.py:145 [comparacion] if r.veredicto == "sin datos": -> if r.veredicto != "sin datos":` | muerto | muerto |
| 275 | `evals/informe_modelos.py:150 [comparacion] elif r.veredicto == "cambiar": -> elif r.veredicto != "cambiar":` | muerto | muerto |
| 276 | `evals/informe_modelos.py:154 [comparacion] if r.recomendado != seccion.referencia: -> if r.recomendado == seccion.referencia:` | muerto | muerto |
| 277 | `evals/informe_modelos.py:155 [aritmetico] veredicto += ( -> veredicto -= (` | muerto | muerto |
| 278 | `evals/informe_modelos.py:161 [aritmetico] "- Elegibles: " + ", ".join(f"`{m}`" for m in r.elegibles) -> "- Elegibles: " - ", ".join(f"`{m}`" for m in r.elegibles)` | muerto | muerto |
| 279 | `evals/informe_modelos.py:162 [aritmetico] + " · banda de empate: " + ", ".join(f"`{m}`" for m in r.banda) -> + " · banda de empate: " - ", ".join(f"`{m}`" for m in r.banda)` | muerto | muerto |
| 280 | `evals/informe_modelos.py:162 [aritmetico] + " · banda de empate: " + ", ".join(f"`{m}`" for m in r.banda) -> - " · banda de empate: " + ", ".join(f"`{m}`" for m in r.banda)` | muerto | muerto |
| 281 | `evals/informe_modelos.py:164 [aritmetico] lineas += [f"- AVISO: {aviso}" for aviso in r.avisos] -> lineas -= [f"- AVISO: {aviso}" for aviso in r.avisos]` | muerto | muerto |
| 282 | `evals/informe_modelos.py:169 [logico] if not metricas.tokens_entrada_medios and not metricas.tokens_salida_medios: -> if not metricas.tokens_entrada_medios or not metricas.tokens_salida_medios:` | muerto | muerto |
| 283 | `evals/informe_modelos.py:169 [not] if not metricas.tokens_entrada_medios and not metricas.tokens_salida_medios: -> if metricas.tokens_entrada_medios and not metricas.tokens_salida_medios:` | muerto | muerto |
| 284 | `evals/informe_modelos.py:169 [not] if not metricas.tokens_entrada_medios and not metricas.tokens_salida_medios: -> if not metricas.tokens_entrada_medios and metricas.tokens_salida_medios:` | muerto | muerto |
| 285 | `evals/informe_modelos.py:179 [comparacion] repeticiones = f"{seccion.repeticiones} repetici{'ón' if seccion.repeticiones == 1 else 'ones'}" -> repeticiones = f"{seccion.repeticiones} repetici{'ón' if seccion.repeticiones != 1 else 'ones'}"` | muerto | muerto |
| 286 | `evals/informe_modelos.py:179 [entero] repeticiones = f"{seccion.repeticiones} repetici{'ón' if seccion.repeticiones == 1 else 'ones'}" -> repeticiones = f"{seccion.repeticiones} repetici{'ón' if seccion.repeticiones == 2 else 'ones'}"` | muerto | muerto |
| 287 | `evals/informe_modelos.py:180 [logico] cabecera = f"- Commit `{seccion.commit or '?'}` · referencia `{seccion.referencia}`" -> cabecera = f"- Commit `{seccion.commit and '?'}` · referencia `{seccion.referencia}`"` | muerto | muerto |
| 288 | `evals/informe_modelos.py:182 [aritmetico] cabecera += " (añadida: no se había pedido)" -> cabecera -= " (añadida: no se había pedido)"` | muerto | muerto |
| 289 | `evals/informe_modelos.py:193 [aritmetico] lineas += ["", *_tabla(seccion.metricas)] -> lineas -= ["", *_tabla(seccion.metricas)]` | muerto | muerto |
| 290 | `evals/informe_modelos.py:195 [comparacion] if prep is not None: -> if prep is None:` | muerto | muerto |
| 291 | `evals/informe_modelos.py:196 [aritmetico] lineas += ["", (f"- Preparación ({prep.fase}, una vez): `{prep.modelo}` · " -> lineas -= ["", (f"- Preparación ({prep.fase}, una vez): `{prep.modelo}` · "` | muerto | muerto |
| 292 | `evals/informe_modelos.py:199 [aritmetico] lineas += ["", "### E2E", "", *_tabla_e2e(seccion.metricas_e2e)] -> lineas -= ["", "### E2E", "", *_tabla_e2e(seccion.metricas_e2e)]` | muerto | muerto |
| 293 | `evals/informe_modelos.py:200 [aritmetico] lineas += ["", *_recomendacion(seccion), "", "### Casos con ERROR (sin valores)", ""] -> lineas -= ["", *_recomendacion(seccion), "", "### Casos con ERROR (sin valores)", ""]` | muerto | muerto |
| 294 | `evals/informe_modelos.py:201 [aritmetico] lineas += [ -> lineas -= [` | muerto | muerto |
| 295 | `evals/informe_modelos.py:203 [logico] ] or ["(ninguno)"] -> ] and ["(ninguno)"]` | muerto | muerto |
| 296 | `evals/informe_modelos.py:204 [aritmetico] lineas += [ -> lineas -= [` | muerto | muerto |
| 297 | `evals/informe_modelos.py:210 [comparacion] if prep is not None: -> if prep is None:` | muerto | muerto |
| 298 | `evals/informe_modelos.py:212 [aritmetico] lineas += [linea for linea in tokens if linea] -> lineas -= [linea for linea in tokens if linea]` | muerto | muerto |
| 299 | `evals/informe_modelos.py:215 [aritmetico] return "\n".join(lineas) + "\n" -> return "\n".join(lineas) - "\n"` | muerto | muerto |
| 300 | `evals/informe_modelos.py:221 [aritmetico] return base.rstrip("\n") + "\n\n" + seccion -> return base.rstrip("\n") + "\n\n" - seccion` | muerto | muerto |
| 301 | `evals/informe_modelos.py:221 [aritmetico] return base.rstrip("\n") + "\n\n" + seccion -> return base.rstrip("\n") - "\n\n" + seccion` | muerto | muerto |
| 302 | `evals/informe_modelos.py:229 [logico] f"{seccion.fecha} · {seccion.fase} · commit `{seccion.commit or '?'}`", -> f"{seccion.fecha} · {seccion.fase} · commit `{seccion.commit and '?'}`",` | muerto | muerto |
| 303 | `evals/informe_modelos.py:233 [entero] for indice, resultados in enumerate(repeticiones, start=1): -> for indice, resultados in enumerate(repeticiones, start=2):` | muerto | muerto |
| 304 | `evals/informe_modelos.py:237 [aritmetico] lineas += [f"  - {d.descripcion()}" for d in caso.discrepancias] -> lineas -= [f"  - {d.descripcion()}" for d in caso.discrepancias]` | muerto | muerto |
| 305 | `evals/informe_modelos.py:238 [aritmetico] return "\n".join(lineas) + "\n" -> return "\n".join(lineas) - "\n"` | muerto | muerto |
| 306 | `evals/informe_modelos.py:54 [entero] return sum((Decimal(usd) for usd in _GASTO.findall(texto)), Decimal(0)) -> return sum((Decimal(usd) for usd in _GASTO.findall(texto)), Decimal(1))` | muerto | muerto |
| 307 | `evals/informe_modelos.py:67 [aritmetico] return re.fullmatch(re.escape(pedido) + r"(-\d.*)?", servido) is None -> return re.fullmatch(re.escape(pedido) - r"(-\d.*)?", servido) is None` | muerto | muerto |
| 308 | `evals/informe_modelos.py:67 [comparacion] return re.fullmatch(re.escape(pedido) + r"(-\d.*)?", servido) is None -> return re.fullmatch(re.escape(pedido) + r"(-\d.*)?", servido) is not None` | muerto | timeout |
| 309 | `evals/informe_modelos.py:91 [booleano] cortado: bool = False -> cortado: bool = True` | muerto | muerto |
| 310 | `evals/informe_modelos.py:95 [comparacion] if metricas.repeticiones > 1: -> if metricas.repeticiones >= 1:` | muerto | muerto |
| 311 | `evals/informe_modelos.py:95 [entero] if metricas.repeticiones > 1: -> if metricas.repeticiones > 2:` | muerto | muerto |
| 312 | `evals/procesos/medidor.py:101 [comparacion] con_respuesta = respuesta is not None -> con_respuesta = respuesta is None` | muerto | muerto |
| 313 | `evals/procesos/medidor.py:102 [entero] uso = uso_de_respuesta(proveedor, respuesta) if con_respuesta else Uso(0, 0, 0, 0) -> uso = uso_de_respuesta(proveedor, respuesta) if con_respuesta else Uso(0, 0, 0, 1)` | muerto | muerto |
| 314 | `evals/procesos/medidor.py:102 [entero] uso = uso_de_respuesta(proveedor, respuesta) if con_respuesta else Uso(0, 0, 0, 0) -> uso = uso_de_respuesta(proveedor, respuesta) if con_respuesta else Uso(0, 0, 1, 0)` | muerto | muerto |
| 315 | `evals/procesos/medidor.py:102 [entero] uso = uso_de_respuesta(proveedor, respuesta) if con_respuesta else Uso(0, 0, 0, 0) -> uso = uso_de_respuesta(proveedor, respuesta) if con_respuesta else Uso(0, 1, 0, 0)` | muerto | muerto |
| 316 | `evals/procesos/medidor.py:102 [entero] uso = uso_de_respuesta(proveedor, respuesta) if con_respuesta else Uso(0, 0, 0, 0) -> uso = uso_de_respuesta(proveedor, respuesta) if con_respuesta else Uso(1, 0, 0, 0)` | muerto | muerto |
| 317 | `evals/procesos/medidor.py:105 [entero] coste = coste_usd(entrada_tabla, uso, self.fecha) if con_respuesta else Decimal(0) -> coste = coste_usd(entrada_tabla, uso, self.fecha) if con_respuesta else Decimal(1)` | muerto | muerto |
| 318 | `evals/procesos/medidor.py:106 [logico] duracion = (resumen or {}).get("duration_ms") -> duracion = (resumen and {}).get("duration_ms")` | muerto | muerto |
| 319 | `evals/procesos/medidor.py:121 [comparacion] "fallo": error is not None, -> "fallo": error is None,` | muerto | muerto |
| 320 | `evals/procesos/medidor.py:128 [comparacion] if self.fichero is None: -> if self.fichero is not None:` | muerto | muerto |
| 321 | `evals/procesos/medidor.py:131 [booleano] self.fichero.parent.mkdir(parents=True, exist_ok=True) -> self.fichero.parent.mkdir(parents=False, exist_ok=True)` | muerto | muerto |
| 322 | `evals/procesos/medidor.py:131 [booleano] self.fichero.parent.mkdir(parents=True, exist_ok=True) -> self.fichero.parent.mkdir(parents=True, exist_ok=False)` | muerto | muerto |
| 323 | `evals/procesos/medidor.py:133 [aritmetico] salida.write(json.dumps(registro, ensure_ascii=False) + "\n") -> salida.write(json.dumps(registro, ensure_ascii=False) - "\n")` | muerto | muerto |
| 324 | `evals/procesos/medidor.py:133 [booleano] salida.write(json.dumps(registro, ensure_ascii=False) + "\n") -> salida.write(json.dumps(registro, ensure_ascii=True) + "\n")` | muerto | muerto |
| 325 | `evals/procesos/medidor.py:154 [comparacion] if medidor.gasto_usd() >= presupuesto: -> if medidor.gasto_usd() > presupuesto:` | muerto | muerto |
| 326 | `evals/procesos/medidor.py:155 [booleano] resultados.append({"caso_id": caso_id, "no_ejecutado": True}) -> resultados.append({"caso_id": caso_id, "no_ejecutado": False})` | muerto | muerto |
| 327 | `evals/procesos/medidor.py:181 [logico] [interprete or sys.executable, "-m", modulo], -> [interprete and sys.executable, "-m", modulo],` | muerto | muerto |
| 328 | `evals/procesos/medidor.py:187 [booleano] check=False, -> check=True,` | muerto | muerto |
| 329 | `evals/procesos/medidor.py:189 [comparacion] if proceso.returncode != 0: -> if proceso.returncode == 0:` | muerto | muerto |
| 330 | `evals/procesos/medidor.py:189 [entero] if proceso.returncode != 0: -> if proceso.returncode != 1:` | muerto | muerto |
| 331 | `evals/procesos/medidor.py:200 [not] if not ruta.is_file(): -> if ruta.is_file():` | muerto | muerto |
| 332 | `evals/procesos/medidor.py:48 [booleano] enabled = True -> enabled = False` | muerto | muerto |
| 333 | `evals/procesos/medidor.py:60 [comparacion] self.fichero = Path(fichero) if fichero is not None else None -> self.fichero = Path(fichero) if fichero is None else None` | muerto | muerto |
| 334 | `evals/procesos/medidor.py:69 [entero] return sum((Decimal(r["coste_usd"]) for r in self.registros), Decimal(0)) -> return sum((Decimal(r["coste_usd"]) for r in self.registros), Decimal(1))` | muerto | muerto |
| 335 | `evals/procesos/medidor.py:91 [booleano] "fallo_medidor": True, -> "fallo_medidor": False,` | muerto | muerto |
| 336 | `evals/procesos/medidor.py:99 [logico] if isinstance(payload, dict) and "raw_sdk_response" in payload: -> if isinstance(payload, dict) or "raw_sdk_response" in payload:` | muerto | muerto |
| 337 | `evals/procesos/sv2_extraccion.py:202 [booleano] proveedor: str, modelo: str \| None = None, call_logger=None, forzar_herramienta: bool = True -> proveedor: str, modelo: str \| None = None, call_logger=None, forzar_herramienta: bool = False` | muerto | muerto |
| 338 | `evals/procesos/sv2_modelos.py:116 [logico] trabajo = json.loads(sys.stdin.read() or "{}") -> trabajo = json.loads(sys.stdin.read() and "{}")` | muerto | muerto |
| 339 | `evals/procesos/sv2_modelos.py:121 [entero] return 1 -> return 2` | muerto | muerto |
| 340 | `evals/procesos/sv2_modelos.py:123 [entero] return 0 -> return 1` | muerto | muerto |
| 341 | `evals/procesos/sv2_modelos.py:126 [comparacion] if __name__ == "__main__":  # pragma: no cover - lo ejerce el subproceso -> if __name__ != "__main__":  # pragma: no cover - lo ejerce el subproceso` | muerto | muerto |
| 342 | `evals/procesos/sv2_modelos.py:60 [logico] return {"documento": revisado.get("documento_revisado") or caso["ia1"]} -> return {"documento": revisado.get("documento_revisado") and caso["ia1"]}` | muerto | muerto |
| 343 | `evals/procesos/sv2_modelos.py:62 [comparacion] return ia2 if fase == "IA2" else ia1 -> return ia2 if fase != "IA2" else ia1` | muerto | muerto |
| 344 | `evals/procesos/sv2_modelos.py:76 [booleano] forzar = modelo.get("herramienta_forzada") is not False -> forzar = modelo.get("herramienta_forzada") is not True` | muerto | muerto |
| 345 | `evals/procesos/sv2_modelos.py:76 [comparacion] forzar = modelo.get("herramienta_forzada") is not False -> forzar = modelo.get("herramienta_forzada") is False` | muerto | muerto |
| 346 | `evals/procesos/sv2_modelos.py:77 [logico] servicio = (montar or _montar_servicio)(modelo["id"], modelo["proveedor"], forzar, medidor) -> servicio = (montar and _montar_servicio)(modelo["id"], modelo["proveedor"], forzar, medidor)` | muerto | muerto |
| 347 | `evals/procesos/sv2_modelos.py:78 [logico] llamar = llamador(fase, servicio, adjuntos or sv2_extraccion._adjuntos, modelo["proveedor"]) -> llamar = llamador(fase, servicio, adjuntos and sv2_extraccion._adjuntos, modelo["proveedor"])` | muerto | muerto |
| 348 | `evals/procesos/sv2_modelos.py:84 [comparacion] "IA2" if fase == "IA2" else "IA1", -> "IA2" if fase != "IA2" else "IA1",` | muerto | muerto |
| 349 | `evals/procesos/sv5_modelos.py:44 [comparacion] return ia4 if fase == "IA4" else ia3 -> return ia4 if fase != "IA4" else ia3` | muerto | muerto |
| 350 | `evals/procesos/sv5_modelos.py:57 [booleano] forzar = modelo.get("herramienta_forzada") is not False -> forzar = modelo.get("herramienta_forzada") is not True` | muerto | muerto |
| 351 | `evals/procesos/sv5_modelos.py:57 [comparacion] forzar = modelo.get("herramienta_forzada") is not False -> forzar = modelo.get("herramienta_forzada") is False` | muerto | muerto |
| 352 | `evals/procesos/sv5_modelos.py:58 [logico] valorar, conciliar = (montar or _montar_servicios)( -> valorar, conciliar = (montar and _montar_servicios)(` | muerto | muerto |
| 353 | `evals/procesos/sv5_modelos.py:67 [comparacion] "IA4" if fase == "IA4" else "IA3", -> "IA4" if fase != "IA4" else "IA3",` | muerto | muerto |
| 354 | `evals/procesos/sv5_modelos.py:85 [logico] trabajo = json.loads(sys.stdin.read() or "{}") -> trabajo = json.loads(sys.stdin.read() and "{}")` | muerto | muerto |
| 355 | `evals/procesos/sv5_modelos.py:90 [entero] return 1 -> return 2` | muerto | muerto |
| 356 | `evals/procesos/sv5_modelos.py:92 [entero] return 0 -> return 1` | muerto | muerto |
| 357 | `evals/procesos/sv5_modelos.py:95 [comparacion] if __name__ == "__main__":  # pragma: no cover - lo ejerce el subproceso -> if __name__ != "__main__":  # pragma: no cover - lo ejerce el subproceso` | muerto | muerto |
| 358 | `evals/procesos/sv5_valoracion.py:255 [logico] modelo = modelo or os.environ.get(variable, por_defecto) -> modelo = modelo and os.environ.get(variable, por_defecto)` | muerto | muerto |
| 359 | `evals/procesos/sv5_valoracion.py:256 [comparacion] extra = {} if call_logger is None else {"call_logger": call_logger} -> extra = {} if call_logger is not None else {"call_logger": call_logger}` | muerto | muerto |
| 360 | `evals/procesos/sv5_valoracion.py:259 [not] if not forzar_herramienta: -> if forzar_herramienta:` | muerto | muerto |
| 361 | `evals/procesos/sv5_valoracion.py:260 [booleano] extra["forzar_herramienta"] = False -> extra["forzar_herramienta"] = True` | timeout | muerto |
| 362 | `evals/procesos/sv5_valoracion.py:270 [booleano] proveedor: str, modelo: str \| None = None, call_logger=None, forzar_herramienta: bool = True -> proveedor: str, modelo: str \| None = None, call_logger=None, forzar_herramienta: bool = False` | timeout | muerto |
| 363 | `evals/procesos/sv5_valoracion.py:390 [logico] fabrica = fabrica or _clientes_reales -> fabrica = fabrica and _clientes_reales` | timeout | muerto |
| 364 | `evals/runner.py:182 [logico] build or sv6_build.ejecutar_en_subproceso, -> build and sv6_build.ejecutar_en_subproceso,` | muerto | muerto |
| 365 | `evals/runner.py:517 [comparacion] if fases is None: -> if fases is not None:` | muerto | muerto |
| 366 | `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py:45 [booleano] forzar_herramienta: bool = True, -> forzar_herramienta: bool = False,` | muerto | muerto |
