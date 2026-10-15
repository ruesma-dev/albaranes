// tests/dom_falso.js
// DOM mínimo para EJECUTAR con node los componentes de la ficha que tocan el
// DOM (F-065 fase 3 bis: el combo de partida y la ventana de «Dividir»). No
// es un navegador: solo lo que esas funciones usan (elementos con hijos,
// clases, atributos y ``dataset``, eventos que burbujean, foco y los
// selectores de ``_simple``). Lo cargan los tests de Python delante del
// programa.
"use strict";

class Event {
    constructor(type, init) {
        this.type = type;
        this.bubbles = !!(init && init.bubbles);
        this.key = init && init.key;
        this.defaultPrevented = false;
        this.target = null;
        this._parar = false;
        this._pararYa = false;
    }
    preventDefault() { this.defaultPrevented = true; }
    stopPropagation() { this._parar = true; }
    stopImmediatePropagation() { this._parar = true; this._pararYa = true; }
}

// Selectores: «tag», «.clase», «[atributo]», «[atributo="valor"]», sus
// combinaciones, el descendiente («thead tr») y la lista con comas.
function _simple(el, sel) {
    const m = sel.match(/^([a-z0-9*]*)((?:\.[\w-]+)*)((?:\[[\w-]+(?:="[^"]*")?\])*)$/i);
    if (!m) { throw new Error("selector no soportado por el DOM falso: " + sel); }
    if (!el.tagName || el.tagName === "#DOCUMENT") { return false; }
    if (m[1] && m[1] !== "*" && el.tagName !== m[1].toUpperCase()) { return false; }
    const clases = m[2] ? m[2].split(".").filter(Boolean) : [];
    if (!clases.every(function (c) { return el.classList.contains(c); })) { return false; }
    return (m[3].match(/\[[^\]]+\]/g) || []).every(function (a) {
        const mm = a.match(/^\[([\w-]+)(?:="([^"]*)")?\]$/);
        const v = el.getAttribute(mm[1]);
        return v !== null && (mm[2] === undefined || v === mm[2]);
    });
}

function _coincide(el, sel) {
    return String(sel).split(",").some(function (uno) {
        const partes = uno.trim().split(/\s+/);
        if (!_simple(el, partes[partes.length - 1])) { return false; }
        let nodo = el.parentNode;
        for (let i = partes.length - 2; i >= 0; i--) {
            while (nodo && !_simple(nodo, partes[i])) { nodo = nodo.parentNode; }
            if (!nodo) { return false; }
            nodo = nodo.parentNode;
        }
        return true;
    });
}

// «data-valuation-line-id» <-> dataset.valuationLineId, como el navegador.
function _clave(k) {
    return k.slice(5).replace(/-([a-z])/g, function (m, c) { return c.toUpperCase(); });
}

class Elemento {
    constructor(tag) {
        this.tagName = String(tag).toUpperCase();
        this.children = [];
        this.parentNode = null;
        this.dataset = {};
        this.style = {};
        this.atributos = {};
        this.className = "";
        this.value = "";
        this.type = "";
        this.hidden = false;
        this.disabled = false;
        this.readOnly = false;
        this.tabIndex = 0;
        this.open = false;
        this.scrollTop = 0;
        this._texto = "";
        this._oyentes = {};
    }
    get classList() {
        const el = this;
        const lista = function () { return el.className.split(/\s+/).filter(Boolean); };
        return {
            contains: function (c) { return lista().indexOf(c) !== -1; },
            add: function () {
                const l = lista();
                [].forEach.call(arguments, function (c) { if (l.indexOf(c) === -1) { l.push(c); } });
                el.className = l.join(" ");
            },
            remove: function () {
                const quitar = [].slice.call(arguments);
                el.className = lista().filter(function (c) { return quitar.indexOf(c) === -1; }).join(" ");
            },
            toggle: function (c, forzar) {
                const poner = forzar === undefined ? !this.contains(c) : !!forzar;
                if (poner) { this.add(c); } else { this.remove(c); }
                return poner;
            },
        };
    }
    setAttribute(k, v) {
        if (k.indexOf("data-") === 0) { this.dataset[_clave(k)] = String(v); } else { this.atributos[k] = String(v); }
    }
    getAttribute(k) {
        if (k.indexOf("data-") === 0) {
            return _clave(k) in this.dataset ? String(this.dataset[_clave(k)]) : null;
        }
        return k in this.atributos ? this.atributos[k] : null;
    }
    hasAttribute(k) { return this.getAttribute(k) !== null; }
    removeAttribute(k) {
        if (k.indexOf("data-") === 0) { delete this.dataset[_clave(k)]; } else { delete this.atributos[k]; }
    }
    appendChild(hijo) {
        if (hijo.parentNode) { hijo.parentNode.removeChild(hijo); }
        hijo.parentNode = this;
        this.children.push(hijo);
        return hijo;
    }
    insertBefore(hijo, ref) {
        if (hijo.parentNode) { hijo.parentNode.removeChild(hijo); }
        const i = this.children.indexOf(ref);
        hijo.parentNode = this;
        if (i === -1) { this.children.push(hijo); } else { this.children.splice(i, 0, hijo); }
        return hijo;
    }
    removeChild(hijo) {
        const i = this.children.indexOf(hijo);
        if (i !== -1) { this.children.splice(i, 1); hijo.parentNode = null; }
        return hijo;
    }
    set innerHTML(v) {
        this.children.forEach(function (c) { c.parentNode = null; });
        this.children = [];
        this._texto = String(v || "");
    }
    get textContent() {
        return this._texto + this.children.map(function (c) { return c.textContent; }).join("");
    }
    set textContent(v) { this.innerHTML = ""; this._texto = String(v); }
    addEventListener(tipo, f) { (this._oyentes[tipo] = this._oyentes[tipo] || []).push(f); }
    removeEventListener(tipo, f) {
        this._oyentes[tipo] = (this._oyentes[tipo] || []).filter(function (g) { return g !== f; });
    }
    dispatchEvent(ev) {
        if (!ev.target) { ev.target = this; }
        let nodo = this;
        while (nodo) {
            const oyentes = (nodo._oyentes[ev.type] || []).slice();
            for (let i = 0; i < oyentes.length; i++) {
                oyentes[i].call(nodo, ev);
                if (ev._pararYa) { break; }
            }
            if (ev._parar || !ev.bubbles) { break; }
            nodo = nodo.parentNode;
        }
        return !ev.defaultPrevented;
    }
    contains(otro) {
        while (otro) { if (otro === this) { return true; } otro = otro.parentNode; }
        return false;
    }
    _descendientes() {
        let out = [];
        this.children.forEach(function (c) { out.push(c); out = out.concat(c._descendientes()); });
        return out;
    }
    querySelectorAll(sel) {
        return this._descendientes().filter(function (el) { return _coincide(el, sel); });
    }
    querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
    closest(sel) {
        let nodo = this;
        while (nodo && nodo.tagName !== "#DOCUMENT") {
            if (_coincide(nodo, sel)) { return nodo; }
            nodo = nodo.parentNode;
        }
        return null;
    }
    getBoundingClientRect() { return { top: 0, bottom: 20, left: 0, width: 120 }; }
    scrollIntoView() {}
    focus() {
        if (document.activeElement === this) { return; }
        document.activeElement = this;
        this.dispatchEvent(new Event("focus"));
    }
    blur() {
        if (document.activeElement !== this) { return; }
        document.activeElement = document.body;
        this.dispatchEvent(new Event("blur"));
    }
    click() {
        // Como el navegador: un botón desactivado no recibe el clic (tampoco el de .click()).
        if (this.disabled) { return; }
        this.dispatchEvent(new Event("click", { bubbles: true }));
    }
    showModal() { this.open = true; }
    close() { this.open = false; }
}

const document = new Elemento("#document");
document.activeElement = null;
document.body = document.appendChild(new Elemento("body"));
document.createElement = function (tag) { return new Elemento(tag); };
document.getElementById = function (id) {
    return document._descendientes().filter(function (el) { return el.id === id; })[0] || null;
};

const window = {
    _oyentes: {},
    _recargas: 0,
    addEventListener: function (tipo, f) { (this._oyentes[tipo] = this._oyentes[tipo] || []).push(f); },
    removeEventListener: function (tipo, f) {
        this._oyentes[tipo] = (this._oyentes[tipo] || []).filter(function (g) { return g !== f; });
    },
    confirm: function () { return true; },
    location: { reload: function () { window._recargas += 1; } },
};

// Un elemento con clases (y, si se da, un padre), en una línea.
function el(tag, clases, padre) {
    const e = document.createElement(tag);
    e.className = clases || "";
    if (padre) { padre.appendChild(e); }
    return e;
}

// Deja correr las promesas pendientes (el combo carga las partidas con .then).
function tiempo() { return new Promise(function (r) { setTimeout(r, 0); }); }

// Teclea: pone el valor y lanza el «input» como el navegador (burbujea).
function teclear(input, valor) {
    input.value = valor;
    input.dispatchEvent(new Event("input", { bubbles: true }));
}

function tecla(destino, key) {
    const ev = new Event("keydown", { bubbles: true, key: key });
    destino.dispatchEvent(ev);
    return ev;
}
