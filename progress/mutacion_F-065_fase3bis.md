<!-- progress/mutacion_F-065_fase3bis.md -->
# F-065 · fase 3 bis · mutación de lo nuevo (a mano: JS, CSS y plantilla) — rehecha en la pasada 2 (CR3)

`python -m harness.mutacion --feature F-065 --base cd3baf1 --rama HEAD` da **ALCANCE VACÍO**: la fase 3 bis no cambia
ni una línea de Python de producción (todo es `static/app.js`, `static/styles.css` y la plantilla), así que el
generador no tiene nada que mutar y no escribe informe. Por eso la campaña es **a mano**, con el script de abajo:
cada mutante cambia UN trozo exacto (original→mutado, que debe aparecer una sola vez), corre los tres ficheros de
tests **sin `-x`** (se cuentan los fallos) y restaura el fichero byte a byte.

- **HEAD medido: `1b605415b0b4dd6f2ca99dfced7d8af94eb8fea0`** (árbol de sv4 limpio; lo posterior es solo
  documentación). Desde `services/albaranes-front`, con `.venv\Scripts\python`.
- **Línea base** (`tests/test_f065_f3bis_front.py`, `tests/test_f065_f3_dividir.py`, `tests/test_f065_f2_origen.py`,
  sin mutar): **192 passed** en 7,8 s (9,2 s con el arranque).
- **Resultado: 57 mutantes, 57 muertos, 0 supervivientes, 0 sin aplicar, 0 equivalentes declarados.**
- **CSS sin tests textuales (RM3)**: los 12 mutantes de `styles.css` se repitieron quitando los dos tests que leen el
  CSS como texto (`-k "not acciones_siempre_a_la_vista and not acciones_ancho_estable"`, 190 tests): **12 de 12
  muertos** por el motor de cascada (`test_f065_cr2_*`), que mira qué regla GANA en la celda y la cabecera tal como
  las pinta la plantilla. Lo que no tenía efecto se quitó del CSS en vez de dejarlo como equivalente: el `background`
  de la celda (lo pone la fila, más específica), su `white-space: normal` (es el heredado) y los dos `z-index`
  (comprobado en Chrome sin cabeza: sin ellos la columna sigue encima de lo que se desplaza; ver el informe).
- **Nota sobre el #2** (`dialogo.open` quitado de la guarda de F7): muere por conducta (F7 con el foco en una fila y la
  ventana abierta la reiniciaba). En un navegador el `showModal` deja la ficha inerte y ese estado no se alcanza con el
  teclado; la guarda viene de la fase 3 (con F6) y se conserva como defensa.

## Primeras campañas (historia)

- Pasada 1, sobre `bb3d250`: 43 aplicados, 5 supervivientes (F7 con la ventana abierta; `resto === 0` y `>`→`>=` del
  resto; `n === 0` de la parte; «contiene» en vez de «prefijo»), cerrados en `2380376`; luego 44/44 en `2380376`.
  **Esa campaña no valía** (review de la fase 3 bis, CR3): la cabecera sticky perdía la cascada y su mutante murió
  solo por un test textual; la tabla no daba línea ni nº de fallos.
- Pasada 2, sobre `333edf0c954f8fe6100166722bb91f8578d273dd`: 59 mutantes, 1 superviviente (`panel.hidden &&
  !textoNuevo` → `!textoNuevo`: pinchar en la casilla con la lista abierta tomaba lo tecleado como valor de antes),
  cerrado con `test_f065_cr1_teclear_pinchar_en_la_casilla_y_salir_vuelve_la_original` (`8f67a2a`); 59/59 en `8f67a2a`
  y en `3f904f5`. Después se quitaron los `z-index` (2 mutantes menos) y se midió la final, arriba.

## Tabla (campaña final)

| # | fichero:línea | original | mutado | fallos | veredicto |
|---|---|---|---|---|---|
| 1 | static/app.js:1390 | `if (ev.key !== "F7" \|\| dialogo.open)` | `if (ev.key !== "F6" \|\| dialogo.open)` | 4 | MUERTO |
| 2 | static/app.js:1390 | `if (ev.key !== "F7" \|\| dialogo.open)` | `if (ev.key !== "F7")` | 1 | MUERTO |
| 3 | static/app.js:1193 | `return Math.round((q - suma) * 1e6) / 1e6;` | `return Math.round((q - suma) * 1000) / 1000;` | 1 | MUERTO |
| 4 | static/app.js:1201 | `const ultimaMal = resto * q <= 0;` | `const ultimaMal = resto * q < 0;` | 2 | MUERTO |
| 5 | static/app.js:1201 | `const ultimaMal = resto * q <= 0;` | `const ultimaMal = resto * q >= 0;` | 3 | MUERTO |
| 6 | static/app.js:1201 | `const ultimaMal = resto * q <= 0;` | `const ultimaMal = resto <= 0;` | 1 | MUERTO |
| 7 | static/app.js:1204 | `mensaje = resto === 0⏎                ? "La última` | `mensaje = resto !== 0⏎                ? "La última` | 2 | MUERTO |
| 8 | static/app.js:1206 | `"Sobra: " + String(Math.abs(resto))` | `"Sobra: " + String(resto)` | 2 | MUERTO |
| 9 | static/app.js:1210 | `if (n === null) {⏎                    mensaje = "Falta` | `if (n === 0) {⏎                    mensaje = "Falta` | 2 | MUERTO |
| 10 | static/app.js:1214 | `if (n * q <= 0) {` | `if (n * q < 0) {` | 1 | MUERTO |
| 11 | static/app.js:1214 | `if (n * q <= 0) {` | `if (n <= 0) {` | 1 | MUERTO |
| 12 | static/app.js:1214 | `if (n * q <= 0) {` | `if (n === 0) {` | 1 | MUERTO |
| 13 | static/app.js:1211 | `"Falta la cantidad de la parte " + (i + 1)` | `"Falta la cantidad de la parte " + i` | 2 | MUERTO |
| 14 | static/app.js:1212 | `break;⏎                }⏎                if (n * q` | `}⏎                if (n * q` | 2 | MUERTO |
| 15 | static/app.js:1270 | `const estado = estadoReparto(actual.q, cantidades().slice(0, -1));` | `const estado = estadoReparto(actual.q, cantidades());` | 3 | MUERTO |
| 16 | static/app.js:1271 | `ultima.value = String(estado.resto).replace(".", ",");` | `ultima.value = String(estado.resto);` | 1 | MUERTO |
| 17 | static/app.js:1272 | `ultima.classList.toggle("dividir-resto-mal", estado.ultimaMal);` | *(nada)* | 2 | MUERTO |
| 18 | static/app.js:1274 | `aceptar.disabled = !repartoValido(actual.q, cantidades());⏎        }⏎⏎        function pintarPartes` | `aceptar.disabled = false;⏎        }⏎⏎        function pintarPartes` | 1 | MUERTO |
| 19 | static/app.js:1281 | `const previas = cantidades().slice(0, -1);` | `const previas = cantidades();` | 1 | MUERTO |
| 20 | static/app.js:1295 | `cant.readOnly = true;` | `cant.readOnly = false;` | 1 | MUERTO |
| 21 | static/app.js:1296 | `cant.tabIndex = -1;` | *(nada)* | 1 | MUERTO |
| 22 | static/app.js:1297 | `cant.classList.add("dividir-auto");` | *(nada)* | 1 | MUERTO |
| 23 | static/app.js:1294 | `if (i === n - 1) {⏎                    cant.readOnly` | `if (i === 0) {⏎                    cant.readOnly` | 3 | MUERTO |
| 24 | static/app.js:848 | `eligiendo = true;⏎            input.dispatchEvent` | `eligiendo = false;⏎            input.dispatchEvent` | 3 | MUERTO |
| 25 | static/app.js:850 | `            eligiendo = false;⏎        }` | `        }` | 2 | MUERTO |
| 26 | static/app.js:907 | `if (!eligiendo && document.activeElement === input) { open(true); }` | `if (document.activeElement === input) { open(true); }` | 3 | MUERTO |
| 27 | static/app.js:907 | `if (!eligiendo && document.activeElement === input) { open(true); }` | `if (!eligiendo && document.activeElement === input) { open(false); }` | 5 | MUERTO |
| 28 | static/app.js:890 | `if (panel.hidden && !textoNuevo) { alAbrir = input.value; }` | `if (panel.hidden) { alAbrir = input.value; }` | 3 | MUERTO |
| 29 | static/app.js:890 | `if (panel.hidden && !textoNuevo) { alAbrir = input.value; }` | `if (!textoNuevo) { alAbrir = input.value; }` | 1 | MUERTO |
| 30 | static/app.js:890 | `if (panel.hidden && !textoNuevo) { alAbrir = input.value; }` | `if (panel.hidden \|\| !textoNuevo) { alAbrir = input.value; }` | 4 | MUERTO |
| 31 | static/app.js:890 | `if (panel.hidden && !textoNuevo) { alAbrir = input.value; }` | *(nada)* | 2 | MUERTO |
| 32 | static/app.js:895 | `activo = esAlmacenTecleado(input.value) ? 0 : -1;` | `activo = esAlmacenTecleado(input.value) ? 0 : Math.min(activo, shown.length - 1);` | 1 | MUERTO |
| 33 | static/app.js:895 | `activo = esAlmacenTecleado(input.value) ? 0 : -1;` | `activo = -1;` | 1 | MUERTO |
| 34 | static/app.js:900 | `if (textoNuevo) { panel.scrollTop = 0; }` | *(nada)* | 2 | MUERTO |
| 35 | static/app.js:759 | `return t !== "" && ("almacen".indexOf(t) === 0 \|\| t.indexOf("almacen") === 0);` | `return ("almacen".indexOf(t) === 0 \|\| t.indexOf("almacen") === 0);` | 1 | MUERTO |
| 36 | static/app.js:759 | `return t !== "" && ("almacen".indexOf(t) === 0 \|\| t.indexOf("almacen") === 0);` | `return t !== "" && "almacen".indexOf(t) === 0;` | 1 | MUERTO |
| 37 | static/app.js:759 | `return t !== "" && ("almacen".indexOf(t) === 0 \|\| t.indexOf("almacen") === 0);` | `return t !== "" && ("almacen".indexOf(t) !== -1 \|\| t.indexOf("almacen") === 0);` | 1 | MUERTO |
| 38 | static/app.js:758 | `const t = _normLine(texto).trim();` | `const t = String(texto).trim();` | 1 | MUERTO |
| 39 | static/app.js:3151 | `var gridApi = enhanceTable(document.getElementById("lines-table"));` | `var gridApi = null;` | 1 | MUERTO |
| 40 | static/app.js:2967 | `out[k] = (isFinite(w) && w >= MIN_W) ? w : defW(k);` | `out[k] = (isFinite(w)) ? w : defW(k);` | 1 | MUERTO |
| 41 | static/styles.css:1632 | `.salmon-table thead tr.salmon-head th[data-col="acciones"] {` | `.salmon-table thead th[data-col="acciones"] {` | 2 | MUERTO |
| 42 | static/styles.css:1626 | `    position: sticky;⏎    right: 0;⏎    box-shadow` | `    right: 0;⏎    box-shadow` | 2 | MUERTO |
| 43 | static/styles.css:1626 | `    position: sticky;⏎    right: 0;⏎    box-shadow` | `    position: sticky;⏎    box-shadow` | 2 | MUERTO |
| 44 | static/styles.css:1633 | `    position: sticky;⏎    right: 0;⏎    cursor` | `    right: 0;⏎    cursor` | 2 | MUERTO |
| 45 | static/styles.css:1633 | `    position: sticky;⏎    right: 0;⏎    cursor` | `    position: sticky;⏎    cursor` | 2 | MUERTO |
| 46 | static/styles.css:1634 | `    right: 0;⏎    cursor: default;` | `    right: 0;` | 1 | MUERTO |
| 47 | static/styles.css:1627 | `    right: 0;⏎    box-shadow: -6px 0 6px -6px rgba(0, 0, 0, 0.3);⏎    overflow` | `    right: 0;⏎    overflow` | 1 | MUERTO |
| 48 | static/styles.css:1635 | `    cursor: default;⏎    box-shadow: -6px 0 6px -6px rgba(0, 0, 0, 0.3);` | `    cursor: default;` | 1 | MUERTO |
| 49 | static/styles.css:1629 | `    overflow: visible;⏎    text-align` | `    white-space: nowrap;⏎    overflow: visible;⏎    text-align` | 2 | MUERTO |
| 50 | static/styles.css:1629 | `    overflow: visible;⏎    text-align` | `    text-align` | 2 | MUERTO |
| 51 | static/styles.css:1629 | `    overflow: visible;⏎    text-align: right;` | `    overflow: visible;` | 1 | MUERTO |
| 52 | static/styles.css:1638 | `.salmon-table td.td-acciones .btn { white-space: nowrap;` | `.salmon-table td.td-acciones .btn {` | 2 | MUERTO |
| 53 | templates/document_detail.html:707 | `<th data-col="acciones" data-col-fixed>` | `<th data-col="acciones" draggable="true">` | 1 | MUERTO |
| 54 | templates/document_detail.html:692 | `<col data-col="acciones" data-w="200">` | `<col data-col="acciones" data-w="156">` | 1 | MUERTO |
| 55 | templates/document_detail.html:883 | `aria-label="Borrar" title=` | `title=` | 1 | MUERTO |
| 56 | templates/document_detail.html:883 | `>✕</button>` | `>Borrar ✕</button>` | 1 | MUERTO |
| 57 | templates/document_detail.html:887 | `cada una con su cantidad y su partida (F7)">` | `cada una con su cantidad y su partida (F6)">` | 1 | MUERTO |

TOTAL 57 mutantes, 0 vivos

## Script (reproducible)

```python
# Mutación A MANO de lo nuevo de la fase 3 bis de F-065 (JS, CSS y plantilla de sv4): el generador del arnés
# solo muta Python y aquí no cambia ni una línea de Python de producción. Se lanza desde
# services/albaranes-front con el python del venv de sv4:
#     .venv\Scripts\python mutacion_js2.py
# Cada mutante cambia UN trozo (texto exacto original -> mutado; debe aparecer una sola vez), corre los tres
# ficheros de tests SIN -x (cuenta los fallos) y restaura el fichero byte a byte. Imprime la tabla en Markdown.
import pathlib
import re
import subprocess
import sys
import time

R = pathlib.Path(".")
TESTS = ["tests/test_f065_f3bis_front.py", "tests/test_f065_f3_dividir.py", "tests/test_f065_f2_origen.py"]
NL = "\n"
M = [
    # --- F7 (R29 v3) ---
    ("static/app.js", 'if (ev.key !== "F7" || dialogo.open)', 'if (ev.key !== "F6" || dialogo.open)'),
    ("static/app.js", 'if (ev.key !== "F7" || dialogo.open)', 'if (ev.key !== "F7")'),
    # --- última parte automática (R29 v3) ---
    ("static/app.js", "return Math.round((q - suma) * 1e6) / 1e6;", "return Math.round((q - suma) * 1000) / 1000;"),
    ("static/app.js", "const ultimaMal = resto * q <= 0;", "const ultimaMal = resto * q < 0;"),
    ("static/app.js", "const ultimaMal = resto * q <= 0;", "const ultimaMal = resto * q >= 0;"),
    ("static/app.js", "const ultimaMal = resto * q <= 0;", "const ultimaMal = resto <= 0;"),
    ("static/app.js", 'mensaje = resto === 0' + NL + '                ? "La última', 'mensaje = resto !== 0' + NL + '                ? "La última'),
    ("static/app.js", '"Sobra: " + String(Math.abs(resto))', '"Sobra: " + String(resto)'),
    ("static/app.js", "if (n === null) {" + NL + '                    mensaje = "Falta', "if (n === 0) {" + NL + '                    mensaje = "Falta'),
    ("static/app.js", "if (n * q <= 0) {", "if (n * q < 0) {"),
    ("static/app.js", "if (n * q <= 0) {", "if (n <= 0) {"),
    ("static/app.js", "if (n * q <= 0) {", "if (n === 0) {"),
    ("static/app.js", '"Falta la cantidad de la parte " + (i + 1)', '"Falta la cantidad de la parte " + i'),
    ("static/app.js", "break;" + NL + "                }" + NL + "                if (n * q", "}" + NL + "                if (n * q"),
    ("static/app.js", "const estado = estadoReparto(actual.q, cantidades().slice(0, -1));", "const estado = estadoReparto(actual.q, cantidades());"),
    ("static/app.js", 'ultima.value = String(estado.resto).replace(".", ",");', "ultima.value = String(estado.resto);"),
    ("static/app.js", 'ultima.classList.toggle("dividir-resto-mal", estado.ultimaMal);', ""),
    ("static/app.js", "aceptar.disabled = !repartoValido(actual.q, cantidades());" + NL + "        }" + NL + NL + "        function pintarPartes",
     "aceptar.disabled = false;" + NL + "        }" + NL + NL + "        function pintarPartes"),
    ("static/app.js", "const previas = cantidades().slice(0, -1);", "const previas = cantidades();"),
    ("static/app.js", "cant.readOnly = true;", "cant.readOnly = false;"),
    ("static/app.js", "cant.tabIndex = -1;", ""),
    ("static/app.js", 'cant.classList.add("dividir-auto");', ""),
    ("static/app.js", "if (i === n - 1) {" + NL + "                    cant.readOnly", "if (i === 0) {" + NL + "                    cant.readOnly"),
    # --- combo de partida (R27 v3 y CR1) ---
    ("static/app.js", "eligiendo = true;" + NL + "            input.dispatchEvent", "eligiendo = false;" + NL + "            input.dispatchEvent"),
    ("static/app.js", "            eligiendo = false;" + NL + "        }", "        }"),
    ("static/app.js", "if (!eligiendo && document.activeElement === input) { open(true); }", "if (document.activeElement === input) { open(true); }"),
    ("static/app.js", "if (!eligiendo && document.activeElement === input) { open(true); }", "if (!eligiendo && document.activeElement === input) { open(false); }"),
    ("static/app.js", "if (panel.hidden && !textoNuevo) { alAbrir = input.value; }", "if (panel.hidden) { alAbrir = input.value; }"),
    ("static/app.js", "if (panel.hidden && !textoNuevo) { alAbrir = input.value; }", "if (!textoNuevo) { alAbrir = input.value; }"),
    ("static/app.js", "if (panel.hidden && !textoNuevo) { alAbrir = input.value; }", "if (panel.hidden || !textoNuevo) { alAbrir = input.value; }"),
    ("static/app.js", "if (panel.hidden && !textoNuevo) { alAbrir = input.value; }", ""),
    ("static/app.js", "activo = esAlmacenTecleado(input.value) ? 0 : -1;", "activo = esAlmacenTecleado(input.value) ? 0 : Math.min(activo, shown.length - 1);"),
    ("static/app.js", "activo = esAlmacenTecleado(input.value) ? 0 : -1;", "activo = -1;"),
    ("static/app.js", "if (textoNuevo) { panel.scrollTop = 0; }", ""),
    ("static/app.js", 'return t !== "" && ("almacen".indexOf(t) === 0 || t.indexOf("almacen") === 0);', 'return ("almacen".indexOf(t) === 0 || t.indexOf("almacen") === 0);'),
    ("static/app.js", 'return t !== "" && ("almacen".indexOf(t) === 0 || t.indexOf("almacen") === 0);', 'return t !== "" && "almacen".indexOf(t) === 0;'),
    ("static/app.js", 'return t !== "" && ("almacen".indexOf(t) === 0 || t.indexOf("almacen") === 0);', 'return t !== "" && ("almacen".indexOf(t) !== -1 || t.indexOf("almacen") === 0);'),
    ("static/app.js", "const t = _normLine(texto).trim();", "const t = String(texto).trim();"),
    # --- columnas restauradas (D1) ---
    ("static/app.js", 'var gridApi = enhanceTable(document.getElementById("lines-table"));', "var gridApi = null;"),
    ("static/app.js", "out[k] = (isFinite(w) && w >= MIN_W) ? w : defW(k);", "out[k] = (isFinite(w)) ? w : defW(k);"),
    # --- «Acciones» (R29 v3 y CR2): cada regla gana la cascada (motor de cascada del test) ---
    ("static/styles.css", ".salmon-table thead tr.salmon-head th[data-col=\"acciones\"] {", ".salmon-table thead th[data-col=\"acciones\"] {"),
    ("static/styles.css", "    position: sticky;" + NL + "    right: 0;" + NL + "    box-shadow", "    right: 0;" + NL + "    box-shadow"),
    ("static/styles.css", "    position: sticky;" + NL + "    right: 0;" + NL + "    box-shadow", "    position: sticky;" + NL + "    box-shadow"),
    ("static/styles.css", "    position: sticky;" + NL + "    right: 0;" + NL + "    cursor", "    right: 0;" + NL + "    cursor"),
    ("static/styles.css", "    position: sticky;" + NL + "    right: 0;" + NL + "    cursor", "    position: sticky;" + NL + "    cursor"),
    ("static/styles.css", "    right: 0;" + NL + "    cursor: default;", "    right: 0;"),
    ("static/styles.css", "    right: 0;" + NL + "    box-shadow: -6px 0 6px -6px rgba(0, 0, 0, 0.3);" + NL + "    overflow", "    right: 0;" + NL + "    overflow"),
    ("static/styles.css", "    cursor: default;" + NL + "    box-shadow: -6px 0 6px -6px rgba(0, 0, 0, 0.3);", "    cursor: default;"),
    ("static/styles.css", "    overflow: visible;" + NL + "    text-align", "    white-space: nowrap;" + NL + "    overflow: visible;" + NL + "    text-align"),
    ("static/styles.css", "    overflow: visible;" + NL + "    text-align", "    text-align"),
    ("static/styles.css", "    overflow: visible;" + NL + "    text-align: right;", "    overflow: visible;"),
    ("static/styles.css", ".salmon-table td.td-acciones .btn { white-space: nowrap;", ".salmon-table td.td-acciones .btn {"),
    # --- plantilla ---
    ("templates/document_detail.html", '<th data-col="acciones" data-col-fixed>', '<th data-col="acciones" draggable="true">'),
    ("templates/document_detail.html", '<col data-col="acciones" data-w="200">', '<col data-col="acciones" data-w="156">'),
    ("templates/document_detail.html", 'aria-label="Borrar" title=', "title="),
    ("templates/document_detail.html", ">✕</button>", ">Borrar ✕</button>"),
    ("templates/document_detail.html", 'cada una con su cantidad y su partida (F7)">', 'cada una con su cantidad y su partida (F6)">'),
]


def correr():
    t0 = time.time()
    r = subprocess.run([sys.executable, "-m", "pytest", *TESTS, "-q", "-p", "no:cacheprovider"],
                       capture_output=True, text=True)
    fin = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]
    fallos = int(m.group(1)) if (m := re.search(r"(\d+) failed", fin)) else 0
    errores = int(m.group(1)) if (m := re.search(r"(\d+) error", fin)) else 0
    return r.returncode, fallos + errores, fin, time.time() - t0


def celda(s):
    return "`" + s.replace("|", "\\|").replace(NL, "⏎") + "`" if s else "*(nada)*"


sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
sucio = subprocess.run(["git", "status", "--porcelain", "--", "."], capture_output=True, text=True).stdout.strip()
print(f"HEAD medido: `{sha}`; árbol de sv4 {'LIMPIO' if not sucio else 'SUCIO: ' + sucio}")
codigo, _, fin, dur = correr()
print(f"Línea base (los tres ficheros, sin mutar): código {codigo}, `{fin}`, {dur:.1f} s")
print()
print("| # | fichero:línea | original | mutado | fallos | veredicto |")
print("|---|---|---|---|---|---|")
vivos = 0
for i, (f, v, n) in enumerate(M, 1):
    p = R / f
    orig = p.read_bytes()
    t = orig.decode("utf-8")
    crlf = "\r\n" in t
    v2, n2 = (v.replace(NL, "\r\n"), n.replace(NL, "\r\n")) if crlf else (v, n)
    if t.count(v2) != 1:
        print(f"| {i} | {f} | {celda(v)} | {celda(n)} | — | NO APLICA ({t.count(v2)} apariciones) |")
        continue
    linea = t[:t.index(v2)].count("\n") + 1
    p.write_bytes(t.replace(v2, n2).encode("utf-8"))
    try:
        codigo, fallos, fin, dur = correr()
    finally:
        p.write_bytes(orig)
    veredicto = "MUERTO" if codigo != 0 else "VIVO"
    vivos += veredicto == "VIVO"
    print(f"| {i} | {f}:{linea} | {celda(v)} | {celda(n)} | {fallos} | {veredicto} |", flush=True)
print()
print(f"TOTAL {len(M)} mutantes, {vivos} vivos")
```

## Pasada 3 (H1, R27 v4): mutación a mano de lo nuevo

Mismo script que arriba con otra lista `M` (abajo; el resto del script, igual). Solo lo nuevo de la pasada 3:
`marcadaAlTeclear`, su uso al teclear y el Enter sin marcada (`static/app.js`; ni CSS ni plantilla cambian).

- **HEAD medido: `0075ce4900a27867ec0c1e6c0c80f46dcf5d5711`** (árbol de sv4 limpio).
- **Línea base** de los tres ficheros: **204 passed**.
- **Resultado: 15 mutantes, 15 muertos, 0 supervivientes.**
- Primera vuelta sobre `3f3aeff3254ed3f143270038114b0433b83a060b`: 15/15, pero #3, #4 y #9 morían solo por el test de
  la función pura; se añadió `test_f065_r27v4_borrar_lo_tecleado_y_enter_no_elige_nada` (`""` y `"   "`, conducta en
  el combo) y ahora mueren también por conducta.
- **Repetida sin el test de la función pura** (`-k "not que_marca_al_teclear"`): 14 de 15 muertos; vive **#5** (quitar
  `shown.length > 1`). Es **equivalente en el combo** y queda demostrado así, ejecutando: sin coincidencias `shown` solo
  tiene «Almacén», la marcada 1 no existe (`render` no marca nada, `shown[1]` es `undefined` y Enter no elige) y
  `siguienteActivo` lleva 1 y -1 al mismo 0 con las flechas. Lo mata el test de la función, que fija su contrato
  (-1 = ninguna). Se deja: devolver una posición que no existe sería un contrato peor. No hay tests textuales en juego
  (todo es JS ejecutado con node).
- Línea anterior: el `activo >= 0 &&` del Enter se quitó antes de medir (`3f3aeff`): `shown[-1]` es `undefined`, así que
  era redundante y habría dado un mutante equivalente.


| # | fichero:línea | original | mutado | fallos | veredicto |
|---|---|---|---|---|---|
| 1 | static/app.js:766 | `if (esAlmacenTecleado(texto)) { return 0; }` | *(nada)* | 3 | MUERTO |
| 2 | static/app.js:766 | `if (esAlmacenTecleado(texto)) { return 0; }` | `if (esAlmacenTecleado(texto)) { return 1; }` | 3 | MUERTO |
| 3 | static/app.js:767 | `return String(texto \|\| "").trim() !== "" && shown.length > 1 ? 1 : -1;` | `return shown.length > 1 ? 1 : -1;` | 3 | MUERTO |
| 4 | static/app.js:767 | `return String(texto \|\| "").trim() !== "" && shown.length > 1 ? 1 : -1;` | `return String(texto \|\| "") !== "" && shown.length > 1 ? 1 : -1;` | 2 | MUERTO |
| 5 | static/app.js:767 | `return String(texto \|\| "").trim() !== "" && shown.length > 1 ? 1 : -1;` | `return String(texto \|\| "").trim() !== "" ? 1 : -1;` | 1 | MUERTO |
| 6 | static/app.js:767 | `return String(texto \|\| "").trim() !== "" && shown.length > 1 ? 1 : -1;` | `return String(texto \|\| "").trim() !== "" && shown.length > 2 ? 1 : -1;` | 4 | MUERTO |
| 7 | static/app.js:767 | `return String(texto \|\| "").trim() !== "" && shown.length > 1 ? 1 : -1;` | `return String(texto \|\| "").trim() !== "" && shown.length > 1 ? 2 : -1;` | 6 | MUERTO |
| 8 | static/app.js:767 | `return String(texto \|\| "").trim() !== "" && shown.length > 1 ? 1 : -1;` | `return String(texto \|\| "").trim() !== "" && shown.length > 1 ? 1 : 0;` | 5 | MUERTO |
| 9 | static/app.js:767 | `return String(texto \|\| "").trim() !== "" && shown.length > 1 ? 1 : -1;` | `return String(texto \|\| "").trim() !== "" \|\| shown.length > 1 ? 1 : -1;` | 3 | MUERTO |
| 10 | static/app.js:904 | `activo = marcadaAlTeclear(shown, input.value);` | `activo = esAlmacenTecleado(input.value) ? 0 : -1;` | 5 | MUERTO |
| 11 | static/app.js:904 | `activo = marcadaAlTeclear(shown, input.value);` | `activo = -1;` | 7 | MUERTO |
| 12 | static/app.js:936 | `const elegido = shown[activo];  // sin marcada (-1): undefined` | `const elegido = shown[activo >= 0 ? activo : 0];` | 7 | MUERTO |
| 13 | static/app.js:936 | `const elegido = shown[activo];  // sin marcada (-1): undefined` | `const elegido = shown[0];` | 11 | MUERTO |
| 14 | static/app.js:937 | `if (elegido) { pick(elegido); }⏎            } else if (e.key === "Escape")` | `pick(elegido);⏎            } else if (e.key === "Escape")` | 7 | MUERTO |
| 15 | static/app.js:937 | `if (elegido) { pick(elegido); }⏎            } else if (e.key === "Escape")` | `⏎            } else if (e.key === "Escape")` | 7 | MUERTO |

TOTAL 15 mutantes, 0 vivos

```python
M = [
    # --- R27 v4 (pasada 3, H1): marcadaAlTeclear ---
    ("static/app.js", "if (esAlmacenTecleado(texto)) { return 0; }", ""),
    ("static/app.js", "if (esAlmacenTecleado(texto)) { return 0; }", "if (esAlmacenTecleado(texto)) { return 1; }"),
    ("static/app.js", 'return String(texto || "").trim() !== "" && shown.length > 1 ? 1 : -1;', "return shown.length > 1 ? 1 : -1;"),
    ("static/app.js", 'return String(texto || "").trim() !== "" && shown.length > 1 ? 1 : -1;', 'return String(texto || "") !== "" && shown.length > 1 ? 1 : -1;'),
    ("static/app.js", 'return String(texto || "").trim() !== "" && shown.length > 1 ? 1 : -1;', 'return String(texto || "").trim() !== "" ? 1 : -1;'),
    ("static/app.js", 'return String(texto || "").trim() !== "" && shown.length > 1 ? 1 : -1;', 'return String(texto || "").trim() !== "" && shown.length > 2 ? 1 : -1;'),
    ("static/app.js", 'return String(texto || "").trim() !== "" && shown.length > 1 ? 1 : -1;', 'return String(texto || "").trim() !== "" && shown.length > 1 ? 2 : -1;'),
    ("static/app.js", 'return String(texto || "").trim() !== "" && shown.length > 1 ? 1 : -1;', 'return String(texto || "").trim() !== "" && shown.length > 1 ? 1 : 0;'),
    ("static/app.js", 'return String(texto || "").trim() !== "" && shown.length > 1 ? 1 : -1;', 'return String(texto || "").trim() !== "" || shown.length > 1 ? 1 : -1;'),
    # --- uso en el combo ---
    ("static/app.js", "activo = marcadaAlTeclear(shown, input.value);", "activo = esAlmacenTecleado(input.value) ? 0 : -1;"),
    ("static/app.js", "activo = marcadaAlTeclear(shown, input.value);", "activo = -1;"),
    ("static/app.js", "const elegido = shown[activo];  // sin marcada (-1): undefined", "const elegido = shown[activo >= 0 ? activo : 0];"),
    ("static/app.js", "const elegido = shown[activo];  // sin marcada (-1): undefined", "const elegido = shown[0];"),
    ("static/app.js", "if (elegido) { pick(elegido); }" + NL + "            } else if (e.key === \"Escape\")", "pick(elegido);" + NL + "            } else if (e.key === \"Escape\")"),
    ("static/app.js", "if (elegido) { pick(elegido); }" + NL + "            } else if (e.key === \"Escape\")", "" + NL + "            } else if (e.key === \"Escape\")"),
]
```

## Pasada 4 (R27 v5): mutación a mano de lo nuevo

Mismo script con otra lista `M` y un fichero de tests más (`tests/test_f065_f1_js.py`: los guardados de la fila);
abajo. Lo nuevo: carga y `abierta` del combo, Enter siempre del combo, `marcarPartida`, `partidasInvalidas`, su uso en
«Guardar», «Guardar todas», el aviso de «Guardar y aprobar» y «Dividir», y la regla CSS `partida-invalida`.

- **HEAD medido: `e1563f565d582368e2a1ed549166bbb41b500a3f`** (árbol de sv4 limpio).
- **Línea base** de los cuatro ficheros: **239 passed** en 18,6 s (20,4 s con el arranque).
- **Resultado: 38 mutantes, 38 muertos, 0 supervivientes, 0 sin aplicar, 0 equivalentes.**
- **Sin tests textuales**: repetida con solo `tests/test_f065_f3bis_front.py` y `-k "not acciones_siempre_a_la_vista and
  not acciones_ancho_estable and not el_bloque_esta_cableado and not f7_en_titulos"` (50 tests: conducta con node y el
  motor de cascada): **38 de 38 muertos**.
- Antes de medir se quitó lo que habría dado equivalentes: el `return` tras el Enter (pasa a cadena `if/else`), la
  guarda `if (!inp)` de `partidasInvalidas` (toda fila editable tiene su casilla de partida) y la rama de plural del
  aviso de «Guardar todas» (un solo texto).


| # | fichero:línea | original | mutado | fallos | veredicto |
|---|---|---|---|---|---|
| 1 | static/app.js:841 | `            panel.hidden = true;⏎            abierta = false;` | `            panel.hidden = true;` | 1 | MUERTO |
| 2 | static/app.js:907 | `            abierta = true;⏎            if (!cargadas)` | `            if (!cargadas)` | 19 | MUERTO |
| 3 | static/app.js:908 | `if (!cargadas) { render(); }  // ya, con «Cargando partidas…»` | *(nada)* | 2 | MUERTO |
| 4 | static/app.js:911 | `                cargadas = true;⏎                if (!abierta)` | `                if (!abierta)` | 5 | MUERTO |
| 5 | static/app.js:912 | `                if (!abierta) { return; }⏎` | *(nada)* | 1 | MUERTO |
| 6 | static/app.js:879 | `if (!cargadas \|\| partidas.error) {` | `if (partidas.error) {` | 1 | MUERTO |
| 7 | static/app.js:879 | `if (!cargadas \|\| partidas.error) {` | `if (!cargadas && partidas.error) {` | 1 | MUERTO |
| 8 | static/app.js:882 | `d.textContent = cargadas ? "No se pudieron cargar las partidas" : "Cargando partidas…";` | `d.textContent = !cargadas ? "No se pudieron cargar las partidas" : "Cargando partidas…";` | 1 | MUERTO |
| 9 | static/app.js:927 | `            marcarPartida(input, false);  // al cambiarla, fuera el rojo (R27 v5)⏎` | *(nada)* | 1 | MUERTO |
| 10 | static/app.js:941 | `                e.preventDefault();⏎                e.stopImmediatePropagation();⏎                const elegido = shown[activo];` | `                e.stopImmediatePropagation();⏎                const elegido = shown[activo];` | 9 | MUERTO |
| 11 | static/app.js:941 | `                e.preventDefault();⏎                e.stopImmediatePropagation();⏎                const elegido = shown[activo];` | `                e.preventDefault();⏎                const elegido = shown[activo];` | 5 | MUERTO |
| 12 | static/app.js:933 | `if (e.key === "Enter") {⏎                // R27 v5` | `if (e.key === "Enter" && !panel.hidden) {⏎                // R27 v5` | 3 | MUERTO |
| 13 | static/app.js:1021 | `if (mal && !inp.classList.contains("partida-invalida")) {` | `if (mal) {` | 1 | MUERTO |
| 14 | static/app.js:1024 | `} else if (!mal && inp.classList.contains("partida-invalida")) {⏎            inp.title = inp.dataset.tituloAntes;⏎` | `} else if (!mal && inp.classList.contains("partida-invalida")) {⏎` | 1 | MUERTO |
| 15 | static/app.js:1022 | `inp.dataset.tituloAntes = inp.title \|\| "";` | *(nada)* | 1 | MUERTO |
| 16 | static/app.js:1027 | `inp.classList.toggle("partida-invalida", mal);` | `inp.classList.toggle("partida-invalida", true);` | 5 | MUERTO |
| 17 | static/app.js:1028 | `if (mal) { inp.setAttribute("aria-invalid", "true"); } else { inp.removeAttribute("aria-invalid"); }` | `if (mal) { inp.setAttribute("aria-invalid", "true"); }` | 1 | MUERTO |
| 18 | static/app.js:1028 | `if (mal) { inp.setAttribute("aria-invalid", "true"); } else { inp.removeAttribute("aria-invalid"); }` | `if (!mal) { inp.removeAttribute("aria-invalid"); }` | 1 | MUERTO |
| 19 | static/app.js:1040 | `const mal = partidaParaEnviar(inp) !== null && !partidaValida(inp.value, res.items);` | `const mal = !partidaValida(inp.value, res.items);` | 1 | MUERTO |
| 20 | static/app.js:1040 | `const mal = partidaParaEnviar(inp) !== null && !partidaValida(inp.value, res.items);` | `const mal = partidaParaEnviar(inp) !== null && partidaValida(inp.value, res.items);` | 7 | MUERTO |
| 21 | static/app.js:1040 | `const mal = partidaParaEnviar(inp) !== null && !partidaValida(inp.value, res.items);` | `const mal = partidaParaEnviar(inp) !== null \|\| !partidaValida(inp.value, res.items);` | 6 | MUERTO |
| 22 | static/app.js:1041 | `            marcarPartida(inp, mal);⏎            if (mal) { malas.push(inp); }` | `            if (mal) { malas.push(inp); }` | 5 | MUERTO |
| 23 | static/app.js:1042 | `            if (mal) { malas.push(inp); }⏎` | *(nada)* | 4 | MUERTO |
| 24 | static/app.js:1189 | `if ((await partidasInvalidas([tr])).length) { return; }` | *(nada)* | 3 | MUERTO |
| 25 | static/app.js:1489 | `                    filas.push(tr);⏎` | *(nada)* | 1 | MUERTO |
| 26 | static/app.js:1497 | `if ((await partidasInvalidas(filas)).length) {⏎                window.alert("Hay partidas` | `if (false) {⏎                window.alert("Hay partidas` | 1 | MUERTO |
| 27 | static/app.js:2161 | `            await partidasInvalidas(filas);  // R27 v5: las que no valen, en rojo⏎` | *(nada)* | 1 | MUERTO |
| 28 | static/app.js:1409 | `const mal = inp.value.trim() !== actual.partida && !partidaValida(inp.value, res.items);` | `const mal = !partidaValida(inp.value, res.items);` | 2 | MUERTO |
| 29 | static/app.js:1409 | `const mal = inp.value.trim() !== actual.partida && !partidaValida(inp.value, res.items);` | `const mal = inp.value.trim() !== actual.partida && partidaValida(inp.value, res.items);` | 2 | MUERTO |
| 30 | static/app.js:1410 | `                marcarPartida(inp, mal);⏎                if (mal) { malas += 1; }` | `                if (mal) { malas += 1; }` | 1 | MUERTO |
| 31 | static/app.js:1411 | `                if (mal) { malas += 1; }⏎` | *(nada)* | 1 | MUERTO |
| 32 | static/app.js:1415 | `                errorEl.hidden = false;⏎                return;⏎            }⏎            aceptar.disabled = true;` | `                return;⏎            }⏎            aceptar.disabled = true;` | 1 | MUERTO |
| 33 | static/app.js:1415 | `                errorEl.hidden = false;⏎                return;⏎            }⏎            aceptar.disabled = true;` | `                errorEl.hidden = false;⏎            }⏎            aceptar.disabled = true;` | 1 | MUERTO |
| 34 | static/styles.css:1846 | `.conciliacion-row .cell-input.partida-invalida,⏎` | *(nada)* | 1 | MUERTO |
| 35 | static/styles.css:1846 | `.conciliacion-row .cell-input.partida-invalida,⏎.dividir-dialog .cell-input.partida-invalida {` | `.conciliacion-row .cell-input.partida-invalida {` | 1 | MUERTO |
| 36 | static/styles.css:1848 | `    border-color: var(--danger, #b42318);⏎    background: #fdecea;⏎    color: var(--danger, #b42318);` | `    background: #fdecea;⏎    color: var(--danger, #b42318);` | 1 | MUERTO |
| 37 | static/styles.css:1848 | `    border-color: var(--danger, #b42318);⏎    background: #fdecea;⏎    color: var(--danger, #b42318);` | `    border-color: var(--danger, #b42318);⏎    color: var(--danger, #b42318);` | 1 | MUERTO |
| 38 | static/styles.css:1848 | `    border-color: var(--danger, #b42318);⏎    background: #fdecea;⏎    color: var(--danger, #b42318);` | `    border-color: var(--danger, #b42318);⏎    background: #fdecea;` | 1 | MUERTO |

TOTAL 38 mutantes, 0 vivos

```python
TESTS = ["tests/test_f065_f3bis_front.py", "tests/test_f065_f3_dividir.py", "tests/test_f065_f2_origen.py", "tests/test_f065_f1_js.py"]
M = [
    # --- combo: carga y «abierta» (R27 v5) ---
    ("static/app.js", "            panel.hidden = true;" + NL + "            abierta = false;", "            panel.hidden = true;"),
    ("static/app.js", "            abierta = true;" + NL + "            if (!cargadas)", "            if (!cargadas)"),
    ("static/app.js", "if (!cargadas) { render(); }  // ya, con «Cargando partidas…»", ""),
    ("static/app.js", "                cargadas = true;" + NL + "                if (!abierta)", "                if (!abierta)"),
    ("static/app.js", "                if (!abierta) { return; }" + NL, ""),
    ("static/app.js", "if (!cargadas || partidas.error) {", "if (partidas.error) {"),
    ("static/app.js", "if (!cargadas || partidas.error) {", "if (!cargadas && partidas.error) {"),
    ("static/app.js", 'd.textContent = cargadas ? "No se pudieron cargar las partidas" : "Cargando partidas…";',
     'd.textContent = !cargadas ? "No se pudieron cargar las partidas" : "Cargando partidas…";'),
    ("static/app.js", "            marcarPartida(input, false);  // al cambiarla, fuera el rojo (R27 v5)" + NL, ""),
    # --- combo: Enter siempre del combo ---
    ("static/app.js", "                e.preventDefault();" + NL + "                e.stopImmediatePropagation();" + NL + "                const elegido = shown[activo];",
     "                e.stopImmediatePropagation();" + NL + "                const elegido = shown[activo];"),
    ("static/app.js", "                e.preventDefault();" + NL + "                e.stopImmediatePropagation();" + NL + "                const elegido = shown[activo];",
     "                e.preventDefault();" + NL + "                const elegido = shown[activo];"),
    ("static/app.js", 'if (e.key === "Enter") {' + NL + "                // R27 v5", 'if (e.key === "Enter" && !panel.hidden) {' + NL + "                // R27 v5"),
    # --- marcarPartida ---
    ("static/app.js", 'if (mal && !inp.classList.contains("partida-invalida")) {', "if (mal) {"),
    ("static/app.js", '} else if (!mal && inp.classList.contains("partida-invalida")) {' + NL + "            inp.title = inp.dataset.tituloAntes;" + NL,
     '} else if (!mal && inp.classList.contains("partida-invalida")) {' + NL),
    ("static/app.js", 'inp.dataset.tituloAntes = inp.title || "";', ""),
    ("static/app.js", 'inp.classList.toggle("partida-invalida", mal);', 'inp.classList.toggle("partida-invalida", true);'),
    ("static/app.js", 'if (mal) { inp.setAttribute("aria-invalid", "true"); } else { inp.removeAttribute("aria-invalid"); }',
     'if (mal) { inp.setAttribute("aria-invalid", "true"); }'),
    ("static/app.js", 'if (mal) { inp.setAttribute("aria-invalid", "true"); } else { inp.removeAttribute("aria-invalid"); }',
     'if (!mal) { inp.removeAttribute("aria-invalid"); }'),
    # --- partidasInvalidas ---
    ("static/app.js", "const mal = partidaParaEnviar(inp) !== null && !partidaValida(inp.value, res.items);",
     "const mal = !partidaValida(inp.value, res.items);"),
    ("static/app.js", "const mal = partidaParaEnviar(inp) !== null && !partidaValida(inp.value, res.items);",
     "const mal = partidaParaEnviar(inp) !== null && partidaValida(inp.value, res.items);"),
    ("static/app.js", "const mal = partidaParaEnviar(inp) !== null && !partidaValida(inp.value, res.items);",
     "const mal = partidaParaEnviar(inp) !== null || !partidaValida(inp.value, res.items);"),
    ("static/app.js", "            marcarPartida(inp, mal);" + NL + "            if (mal) { malas.push(inp); }", "            if (mal) { malas.push(inp); }"),
    ("static/app.js", "            if (mal) { malas.push(inp); }" + NL, ""),
    # --- los guardados ---
    ("static/app.js", "if ((await partidasInvalidas([tr])).length) { return; }", ""),
    ("static/app.js", "                    filas.push(tr);" + NL, ""),
    ("static/app.js", "if ((await partidasInvalidas(filas)).length) {" + NL + '                window.alert("Hay partidas',
     "if (false) {" + NL + '                window.alert("Hay partidas'),
    ("static/app.js", "            await partidasInvalidas(filas);  // R27 v5: las que no valen, en rojo" + NL, ""),
    # --- «Dividir» ---
    ("static/app.js", "const mal = inp.value.trim() !== actual.partida && !partidaValida(inp.value, res.items);",
     "const mal = !partidaValida(inp.value, res.items);"),
    ("static/app.js", "const mal = inp.value.trim() !== actual.partida && !partidaValida(inp.value, res.items);",
     "const mal = inp.value.trim() !== actual.partida && partidaValida(inp.value, res.items);"),
    ("static/app.js", "                marcarPartida(inp, mal);" + NL + "                if (mal) { malas += 1; }", "                if (mal) { malas += 1; }"),
    ("static/app.js", "                if (mal) { malas += 1; }" + NL, ""),
    ("static/app.js", "                errorEl.hidden = false;" + NL + "                return;" + NL + "            }" + NL + "            aceptar.disabled = true;",
     "                return;" + NL + "            }" + NL + "            aceptar.disabled = true;"),
    ("static/app.js", "                errorEl.hidden = false;" + NL + "                return;" + NL + "            }" + NL + "            aceptar.disabled = true;",
     "                errorEl.hidden = false;" + NL + "            }" + NL + "            aceptar.disabled = true;"),
    # --- CSS (gana la cascada: motor de cascada) ---
    ("static/styles.css", ".conciliacion-row .cell-input.partida-invalida," + NL, ""),
    ("static/styles.css", ".conciliacion-row .cell-input.partida-invalida," + NL + ".dividir-dialog .cell-input.partida-invalida {",
     ".conciliacion-row .cell-input.partida-invalida {"),
    ("static/styles.css", "    border-color: var(--danger, #b42318);" + NL + "    background: #fdecea;" + NL + "    color: var(--danger, #b42318);",
     "    background: #fdecea;" + NL + "    color: var(--danger, #b42318);"),
    ("static/styles.css", "    border-color: var(--danger, #b42318);" + NL + "    background: #fdecea;" + NL + "    color: var(--danger, #b42318);",
     "    border-color: var(--danger, #b42318);" + NL + "    color: var(--danger, #b42318);"),
    ("static/styles.css", "    border-color: var(--danger, #b42318);" + NL + "    background: #fdecea;" + NL + "    color: var(--danger, #b42318);",
     "    border-color: var(--danger, #b42318);" + NL + "    background: #fdecea;"),
]
```
