<!-- progress/mutacion_F-065_fase3bis.md -->
# F-065 · fase 3 bis · mutación de lo nuevo (a mano: JS, CSS y plantilla)

`python -m harness.mutacion --feature F-065 --base cd3baf1 --rama HEAD` dice **ALCANCE VACÍO** (la fase 3 bis no
cambia ni una línea de Python de producción: todo es `static/app.js`, `static/styles.css` y la plantilla) y, con razón,
no escribe informe. Para no dejar lo nuevo sin medir se hizo una campaña A MANO con el script de abajo: cada mutante
cambia UN trozo del código nuevo (o restaurado), corre `tests/test_f065_f3bis_front.py`, `tests/test_f065_f3_dividir.py`
y `tests/test_f065_f2_origen.py` (`-x`) y restaura el fichero byte a byte. Desde `services/albaranes-front`, con su venv.

## Resultado

- **Primera campaña** (sobre `bb3d250`, T33): 43 aplicados (los 4 de CSS no aplicaron: el script no contemplaba CRLF),
  **5 supervivientes**, todos huecos reales o código redundante, cerrados en `2380376`:
  1. `sin la guarda de ventana abierta` (F7 con la ventana ya abierta): test nuevo
     `test_f065_r29v3_f7_con_la_ventana_abierta_no_la_reinicia` (sin la guarda, F7 reiniciaba lo tecleado).
  2. `resto === 0 ||` quitado y 3. `>` → `>=` en el signo del resto: con Q > 0 la condición era redundante y con Q < 0
     nadie lo probaba. Reescrito como `resto * q <= 0` (0 o de otro signo que Q, una sola expresión: el `>=` ya no
     existe) y casos con Q negativa en `test_f065_r29v3_estado_del_reparto` (`-10, ["-10"]` ⇒ 0 en rojo).
  4. `n === 0 ||` quitado en el mensaje de una parte: igual, `n * q <= 0` y los casos `-10, ["0"]` y `-10, ["-4", "1"]`.
  5. `"almacen".indexOf(t) === 0` → `!== -1` (contiene en vez de prefijo): casos «macen», «cen», «lmac» ⇒ no es Almacén.
- **Campaña final** (sobre `2380376`): **44 mutantes, 44 muertos, 0 supervivientes, 0 sin aplicar**. Sin equivalentes.

```
MUERTO | static/app.js | F7 -> F6
MUERTO | static/app.js | sin la guarda de ventana abierta
MUERTO | static/app.js | redondeo a milésimas
MUERTO | static/app.js | resto 0 no va en rojo
MUERTO | static/app.js | rojo invertido
MUERTO | static/app.js | sin el signo de Q
MUERTO | static/app.js | mensaje 0 invertido
MUERTO | static/app.js | Sobra sin abs
MUERTO | static/app.js | falta: null -> 0
MUERTO | static/app.js | parte 0 sin mensaje
MUERTO | static/app.js | parte sin el signo de Q
MUERTO | static/app.js | parte de otro signo sin mensaje
MUERTO | static/app.js | número de parte -1
MUERTO | static/app.js | sin break (sigue mirando)
MUERTO | static/app.js | la última cuenta en el resto
MUERTO | static/app.js | resto sin coma decimal
MUERTO | static/app.js | sin rojo
MUERTO | static/app.js | Aceptar siempre
MUERTO | static/app.js | conserva el resto viejo
MUERTO | static/app.js | última editable
MUERTO | static/app.js | última tabulable
MUERTO | static/app.js | sin clase auto
MUERTO | static/app.js | la automática es la primera
MUERTO | static/app.js | pick reabre
MUERTO | static/app.js | sin guarda eligiendo
MUERTO | static/app.js | teclear no es texto nuevo
MUERTO | static/app.js | otro texto conserva la marcada
MUERTO | static/app.js | al no marca Almacén
MUERTO | static/app.js | sin volver arriba
MUERTO | static/app.js | vacío cuenta como almacén
MUERTO | static/app.js | almacén entero no cuenta
MUERTO | static/app.js | contiene en vez de prefijo
MUERTO | static/app.js | sin normalizar
MUERTO | static/app.js | grid sin cablear
MUERTO | static/app.js | ancho guardado sin mínimo
MUERTO | static/styles.css | celda sin sticky
MUERTO | static/styles.css | cabecera sin sticky
MUERTO | static/styles.css | celda transparente
MUERTO | static/styles.css | vuelve a recortar
MUERTO | static/styles.css | botón partible
MUERTO | templates/document_detail.html | acciones arrastrable
MUERTO | templates/document_detail.html | ancho de antes
MUERTO | templates/document_detail.html | sin aria-label
MUERTO | templates/document_detail.html | título F6
TOTAL 44 mutantes, 0 vivos: []
```

## Script (reproducible)

```python
# Mutación a mano de lo nuevo de la fase 3 bis (JS, CSS, plantilla): la herramienta del arnés solo muta Python.
import pathlib, subprocess, sys
R = pathlib.Path(".")
M = [
 ("static/app.js", 'if (ev.key !== "F7" || dialogo.open)', 'if (ev.key !== "F6" || dialogo.open)', "F7 -> F6"),
 ("static/app.js", 'if (ev.key !== "F7" || dialogo.open)', 'if (ev.key !== "F7")', "sin la guarda de ventana abierta"),
 ("static/app.js", "return Math.round((q - suma) * 1e6) / 1e6;", "return Math.round((q - suma) * 1000) / 1000;", "redondeo a milésimas"),
 ("static/app.js", "const ultimaMal = resto * q <= 0;", "const ultimaMal = resto * q < 0;", "resto 0 no va en rojo"),
 ("static/app.js", "const ultimaMal = resto * q <= 0;", "const ultimaMal = resto * q >= 0;", "rojo invertido"),
 ("static/app.js", "const ultimaMal = resto * q <= 0;", "const ultimaMal = resto <= 0;", "sin el signo de Q"),
 ("static/app.js", 'mensaje = resto === 0\n                ? "La última parte quedaría a 0."', 'mensaje = resto !== 0\n                ? "La última parte quedaría a 0."', "mensaje 0 invertido"),
 ("static/app.js", '"Sobra: " + String(Math.abs(resto))', '"Sobra: " + String(resto)', "Sobra sin abs"),
 ("static/app.js", "if (n === null) {\n                    mensaje = \"Falta", "if (n === 0) {\n                    mensaje = \"Falta", "falta: null -> 0"),
 ("static/app.js", "if (n * q <= 0) {", "if (n * q < 0) {", "parte 0 sin mensaje"),
 ("static/app.js", "if (n * q <= 0) {", "if (n <= 0) {", "parte sin el signo de Q"),
 ("static/app.js", "if (n * q <= 0) {", "if (n === 0) {", "parte de otro signo sin mensaje"),
 ("static/app.js", '"Falta la cantidad de la parte " + (i + 1)', '"Falta la cantidad de la parte " + i', "número de parte -1"),
 ("static/app.js", "break;\n                }\n                if (n * q", "}\n                if (n * q", "sin break (sigue mirando)"),
 ("static/app.js", "const estado = estadoReparto(actual.q, cantidades().slice(0, -1));", "const estado = estadoReparto(actual.q, cantidades());", "la última cuenta en el resto"),
 ("static/app.js", 'ultima.value = String(estado.resto).replace(".", ",");', 'ultima.value = String(estado.resto);', "resto sin coma decimal"),
 ("static/app.js", 'ultima.classList.toggle("dividir-resto-mal", estado.ultimaMal);', '', "sin rojo"),
 ("static/app.js", "aceptar.disabled = !repartoValido(actual.q, cantidades());\n        }\n\n        function pintarPartes", "aceptar.disabled = false;\n        }\n\n        function pintarPartes", "Aceptar siempre"),
 ("static/app.js", "const previas = cantidades().slice(0, -1);", "const previas = cantidades();", "conserva el resto viejo"),
 ("static/app.js", "cant.readOnly = true;", "cant.readOnly = false;", "última editable"),
 ("static/app.js", "cant.tabIndex = -1;", "", "última tabulable"),
 ("static/app.js", 'cant.classList.add("dividir-auto");', "", "sin clase auto"),
 ("static/app.js", "if (i === n - 1) {\n                    cant.readOnly", "if (i === 0) {\n                    cant.readOnly", "la automática es la primera"),
 ("static/app.js", "eligiendo = true;\n            input.dispatchEvent", "eligiendo = false;\n            input.dispatchEvent", "pick reabre"),
 ("static/app.js", "if (!eligiendo && document.activeElement === input) { open(true); }", "if (document.activeElement === input) { open(true); }", "sin guarda eligiendo"),
 ("static/app.js", "if (!eligiendo && document.activeElement === input) { open(true); }", "if (!eligiendo && document.activeElement === input) { open(false); }", "teclear no es texto nuevo"),
 ("static/app.js", "activo = esAlmacenTecleado(input.value) ? 0 : -1;", "activo = esAlmacenTecleado(input.value) ? 0 : Math.min(activo, shown.length - 1);", "otro texto conserva la marcada"),
 ("static/app.js", "activo = esAlmacenTecleado(input.value) ? 0 : -1;", "activo = -1;", "al no marca Almacén"),
 ("static/app.js", "if (textoNuevo) { panel.scrollTop = 0; }", "", "sin volver arriba"),
 ("static/app.js", 'return t !== "" && ("almacen".indexOf(t) === 0 || t.indexOf("almacen") === 0);', 'return ("almacen".indexOf(t) === 0 || t.indexOf("almacen") === 0);', "vacío cuenta como almacén"),
 ("static/app.js", 'return t !== "" && ("almacen".indexOf(t) === 0 || t.indexOf("almacen") === 0);', 'return t !== "" && "almacen".indexOf(t) === 0;', "almacén entero no cuenta"),
 ("static/app.js", 'return t !== "" && ("almacen".indexOf(t) === 0 || t.indexOf("almacen") === 0);', 'return t !== "" && ("almacen".indexOf(t) !== -1 || t.indexOf("almacen") === 0);', "contiene en vez de prefijo"),
 ("static/app.js", "const t = _normLine(texto).trim();", "const t = String(texto).trim();", "sin normalizar"),
 ("static/app.js", "var gridApi = enhanceTable(document.getElementById(\"lines-table\"));", "var gridApi = null;", "grid sin cablear"),
 ("static/app.js", "out[k] = (isFinite(w) && w >= MIN_W) ? w : defW(k);", "out[k] = (isFinite(w)) ? w : defW(k);", "ancho guardado sin mínimo"),
 ("static/styles.css", "    position: sticky;\n    right: 0;\n    z-index: 2;", "    right: 0;\n    z-index: 2;", "celda sin sticky"),
 ("static/styles.css", "    position: sticky;\n    right: 0;\n    z-index: 3;", "    right: 0;\n    z-index: 3;", "cabecera sin sticky"),
 ("static/styles.css", "    background: var(--paper, #ffffff);\n    box-shadow", "    box-shadow", "celda transparente"),
 ("static/styles.css", "    white-space: normal;\n    overflow: visible;", "    white-space: nowrap;\n    overflow: hidden;", "vuelve a recortar"),
 ("static/styles.css", ".salmon-table td.td-acciones .btn { white-space: nowrap;", ".salmon-table td.td-acciones .btn {", "botón partible"),
 ("templates/document_detail.html", '<th data-col="acciones" data-col-fixed>', '<th data-col="acciones" draggable="true">', "acciones arrastrable"),
 ("templates/document_detail.html", '<col data-col="acciones" data-w="200">', '<col data-col="acciones" data-w="156">', "ancho de antes"),
 ("templates/document_detail.html", 'aria-label="Borrar" title=', 'title=', "sin aria-label"),
 ("templates/document_detail.html", 'cada una con su cantidad y su partida (F7)">', 'cada una con su cantidad y su partida (F6)">', "título F6"),
]
TESTS = ["tests/test_f065_f3bis_front.py", "tests/test_f065_f3_dividir.py", "tests/test_f065_f2_origen.py"]
vivos = []
for f, v, n, d in M:
    p = R / f; orig = p.read_bytes(); t = orig.decode("utf-8")
    if chr(13) + chr(10) in t:
        v, n = v.replace(chr(10), chr(13) + chr(10)), n.replace(chr(10), chr(13) + chr(10))
    if t.count(v) != 1:
        print("NO APLICA", d, t.count(v)); continue
    p.write_bytes(t.replace(v, n).encode("utf-8"))
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", *TESTS, "-q", "-x", "-p", "no:cacheprovider"], capture_output=True, text=True)
    finally:
        p.write_bytes(orig)
    estado = "MUERTO" if r.returncode != 0 else "VIVO"
    if estado == "VIVO": vivos.append(d)
    print(estado, "|", f, "|", d)
print(f"TOTAL {len(M)} mutantes, {len(vivos)} vivos: {vivos}")
```
