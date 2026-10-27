// The .dashui model, shared by the editor's webview (browser) and the tests (node):
// object types and their properties, edits on the tree (add, move, delete, change)
// that keep everything the editor does not know (unknown keys stay as they are), and
// an approximate HTML preview. Format: docs/MUI_EDITOR.md.
(function (root, factory) {
    if (typeof module === 'object' && module.exports) module.exports = factory();
    else root.DashUI = factory();
}(typeof self !== 'undefined' ? self : this, function () {
    'use strict';

    // type -> { group, props: [[name, kind, default]], events: [...] }
    const TYPES = {
        vgroup:   { group: true,  label: 'Grupo vertical',   props: [], events: [] },
        hgroup:   { group: true,  label: 'Grupo horizontal', props: [], events: [] },
        frame:    { group: true,  label: 'Marco',            props: [['title', 'string', ''], ['horizontal', 'bool', false]], events: [] },
        columns:  { group: true,  label: 'Columnas',         props: [['columns', 'int', 2]], events: [] },
        tabs:     { group: true,  label: 'Pestañas',         props: [['titles', 'string', 'Uno|Dos']], events: ['change'] },
        scroll:   { group: true,  label: 'Desplazable',      props: [], events: [] },
        text:     { group: false, label: 'Texto',            props: [['text', 'string', 'Texto']], events: [] },
        label:    { group: false, label: 'Etiqueta',         props: [['text', 'string', 'Etiqueta:']], events: [] },
        button:   { group: false, label: 'Botón',            props: [['label', 'string', 'Botón']], events: ['event'] },
        string:   { group: false, label: 'Campo de texto',   props: [['text', 'string', ''], ['max', 'int', 80]], events: ['ack', 'change'] },
        checkbox: { group: false, label: 'Casilla',          props: [['checked', 'bool', false]], events: ['change'] },
        cycle:    { group: false, label: 'Ciclo',            props: [['options', 'string', 'Uno|Dos']], events: ['change'] },
        slider:   { group: false, label: 'Deslizador',       props: [['min', 'int', 0], ['max', 'int', 100], ['value', 'int', 0]], events: ['change'] },
        gauge:    { group: false, label: 'Barra',            props: [['max', 'int', 100]], events: [] },
        list:     { group: false, label: 'Lista',            props: [], events: ['change', 'double'] },
        canvas:   { group: false, label: 'Zona de dibujo',   props: [['min_width', 'int', 64], ['min_height', 'int', 32]], events: [] },
        scrollbar:{ group: false, label: 'Barra de desplazamiento', props: [['vertical', 'bool', true]], events: ['change'] },
        image:    { group: false, label: 'Imagen',           props: [['file', 'string', '']], events: [] },
        image_button: { group: false, label: 'Botón con imagen', props: [['file', 'string', '']], events: ['event'] },
        image_toggle: { group: false, label: 'Botón que se queda pulsado', props: [['file', 'string', ''], ['group', 'int', 0], ['checked', 'bool', false]], events: ['change'] },
        combo:    { group: false, label: 'Desplegable editable', props: [['text', 'string', ''], ['options', 'string', 'Uno|Dos']], events: ['ack', 'change'] },
        space:    { group: false, label: 'Espacio',          props: [], events: [] },
        balance:  { group: false, label: 'Separador',        props: [], events: [] },
    };
    const COMMON = [['name', 'ident', ''], ['weight', 'int', 100], ['disabled', 'bool', false], ['hidden', 'bool', false],
                    ['help', 'string', ''], ['context_menu', 'string', '']];   // (the name of a context menu, Lorraine D15)
    const IDENT = /^[A-Za-z_][A-Za-z0-9_]*$/;
    // words of the language: not names (compiler/dashui.py reserved(), the same list; a test compares them)
    const RESERVED = new Set(["EventLoop", "Main", "Print", "Stop", "Wait", "Window", "and", "borrow", "break", "const", "continue", "elif", "else", "end", "enum", "false", "fn", "for", "func", "if", "import", "in", "interface", "nil", "not", "or", "return", "self", "step", "struct", "true", "var", "weak", "while"]);
    /** Why a name of a window or object is not valid, or null */
    function badName(name) {
        if (!IDENT.test(String(name || ''))) return 'letras sin tilde, cifras y _, sin empezar por cifra';
        if (RESERVED.has(name)) return 'es una palabra del lenguaje';
        return null;
    }

    function newDocument() {
        return { dashui: 1, windows: [newWindow('Principal')] };
    }

    function newWindow(name) {
        return { name: name, title: name, id: 0, menus: [], root: { type: 'vgroup', children: [] } };
    }

    function newNode(type) {
        const t = TYPES[type];
        if (!t) throw new Error('unknown type ' + type);
        const node = { type: type };
        for (const [p, , def] of t.props) node[p] = def;
        if (t.group) node.children = [];
        return node;
    }

    function parse(text) {
        const doc = JSON.parse(text);
        if (!doc || doc.dashui !== 1) throw new Error('not a version 1 .dashui file');
        if (!Array.isArray(doc.windows)) doc.windows = [];
        return doc;
    }

    function serialize(doc) {
        return JSON.stringify(doc, null, 2) + '\n';
    }

    // A path is a list of child indices from a window's root: [] = the root itself
    function nodeAt(win, path) {
        let node = win.root;
        for (const i of path) {
            if (!node || !node.children || i < 0 || i >= node.children.length) return null;
            node = node.children[i];
        }
        return node;
    }

    function isAncestor(a, b) {   // path a is b or contains it
        return a.length <= b.length && a.every((v, i) => b[i] === v);
    }

    /** Add a new object of that type inside the group at parentPath (at index, or at the end). */
    function add(win, parentPath, type, index) {
        const parent = nodeAt(win, parentPath);
        if (!parent || !TYPES[parent.type] || !TYPES[parent.type].group) throw new Error('not a group');
        const node = newNode(type);
        const at = index === undefined || index > parent.children.length ? parent.children.length : index;
        parent.children.splice(at, 0, node);
        return parentPath.concat([at]);
    }

    /** Remove the object at path (not the root). */
    function remove(win, path) {
        if (!path.length) throw new Error('the root cannot be removed');
        const parent = nodeAt(win, path.slice(0, -1));
        return parent.children.splice(path[path.length - 1], 1)[0];
    }

    /** Move the object at path into the group at parentPath, at index. Returns its new path. */
    function move(win, path, parentPath, index) {
        if (!path.length) throw new Error('the root cannot be moved');
        if (isAncestor(path, parentPath)) throw new Error('an object cannot go inside itself');
        const target = nodeAt(win, parentPath);
        if (!target || !TYPES[target.type] || !TYPES[target.type].group) throw new Error('not a group');
        const node = remove(win, path);
        // removing shifts the later siblings of the same parent (and paths below them)
        const p = parentPath.slice();
        const rp = path.slice(0, -1), ri = path[path.length - 1];
        if (p.length > rp.length && isAncestor(rp, p) && p[rp.length] > ri) p[rp.length]--;
        let at = index;
        if (JSON.stringify(rp) === JSON.stringify(p) && at > ri) at--;
        const parent = nodeAt(win, p);
        if (at === undefined || at > parent.children.length) at = parent.children.length;
        parent.children.splice(at, 0, node);
        return p.concat([at]);
    }

    /** Change one property; empty/default values of optional keys are removed. Returns an error text or null. */
    function setProp(node, key, value) {
        if (key === 'name') {
            if (value === '' || value === null || value === undefined) { delete node.name; return null; }
            if (value === 'window') return 'nombre no válido: window (es el de la ventana)';
            if (badName(value)) return `nombre no válido: ${value} (${badName(value)})`;
            node.name = value;
            return null;
        }
        if (['event', 'change', 'ack', 'double'].includes(key) || key === 'weight') {
            if (value === '' || value === null || value === undefined) { delete node[key]; return null; }
            const n = Number(value);
            if (!Number.isInteger(n)) return key + ': número entero';
            node[key] = n;
            return null;
        }
        if (key === 'disabled' || key === 'hidden') {
            if (value) node[key] = true; else delete node[key];
            return null;
        }
        if (key === 'help') {
            if (value) node.help = String(value); else delete node.help;
            return null;
        }
        const spec = (TYPES[node.type] || { props: [] }).props.find(([p]) => p === key);
        if (spec && spec[1] === 'int') {
            const n = Number(value);
            if (String(value).trim() === '' || !Number.isInteger(n)) return key + ': número entero';   // ('' would be 0)
            node[key] = n;
        } else if (spec && spec[1] === 'bool') {
            node[key] = !!value;
        } else {
            node[key] = String(value);
        }
        return null;
    }

    /** Where a drop on the object at path goes: before or after it (in its group), or into it (a group:
        at the end). Returns {parentPath, index} or null (the root has no before or after). */
    function dropTarget(win, path, where) {
        const node = nodeAt(win, path);
        if (!node) return null;
        if (where === 'into' && TYPES[node.type] && TYPES[node.type].group) return { parentPath: path, index: undefined };
        if (!path.length) return where === 'into' ? null : { parentPath: [], index: where === 'before' ? 0 : undefined };
        const i = path[path.length - 1];
        return { parentPath: path.slice(0, -1), index: where === 'before' ? i : i + 1 };
    }

    /** A copy of the object at path (deep, as JSON: everything it has, known or not). */
    function copy(win, path) {
        const node = nodeAt(win, path);
        return node ? JSON.parse(JSON.stringify(node)) : null;
    }

    /** Insert a copied object into the group at parentPath (at index, or at the end). Its names (and those
        inside it) that the window already has get a number: boton -> boton2. Returns its path. */
    function paste(win, parentPath, node, index) {
        const parent = nodeAt(win, parentPath);
        if (!parent || !TYPES[parent.type] || !TYPES[parent.type].group) throw new Error('not a group');
        if (!node || typeof node !== 'object' || !node.type) throw new Error('not an object of a .dashui');
        const clone = JSON.parse(JSON.stringify(node));
        const taken = new Set(names(win));
        (function rename(n) {
            if (n.name) {
                const base = String(n.name).replace(/\d+$/, '') || 'objeto';
                let name = n.name, k = 2;
                while (taken.has(name)) name = base + k++;
                n.name = name;
                taken.add(name);
            }
            (n.children || []).forEach(rename);
        })(clone);
        const at = index === undefined || index > parent.children.length ? parent.children.length : index;
        parent.children.splice(at, 0, clone);
        return parentPath.concat([at]);
    }

    /** Move the object at path one place up (delta -1) or down (+1) among its siblings; its new path. */
    function moveBy(win, path, delta) {
        if (!path.length) return path;
        const parent = nodeAt(win, path.slice(0, -1));
        const i = path[path.length - 1], j = i + delta;
        if (!parent || j < 0 || j >= parent.children.length) return path;
        const [node] = parent.children.splice(i, 1);
        parent.children.splice(j, 0, node);
        return path.slice(0, -1).concat([j]);
    }

    /** The paths of a window's objects in the order the tree shows them (the root first). */
    function paths(win) {
        const out = [];
        (function walk(n, path) {
            if (!n) return;
            out.push(path);
            (n.children || []).forEach((c, i) => walk(c, path.concat([i])));
        })(win && win.root, []);
        return out;
    }

    function names(win) {
        const out = [];
        (function walk(n) {
            if (!n) return;
            if (n.name) out.push(n.name);
            (n.children || []).forEach(walk);
        })(win.root);
        return out;
    }

    /** Problems the compiler would refuse: names used twice or not valid, unknown types, numbers that are not. */
    function check(doc) {
        const problems = [];
        const windows = new Set();
        doc.windows.forEach((win, w) => {
            if (badName(win.name)) problems.push(`ventana ${w + 1}: nombre no válido (${badName(win.name)})`);
            else if (windows.has(win.name)) problems.push(`ventana ${w + 1}: nombre repetido ${win.name}`);
            windows.add(win.name);
            if (String(win.title || '').includes('#{')) problems.push(`${win.name}: el título no puede llevar #{ (se leería como interpolación)`);
            for (const k of ['id', 'close']) {   // the compiler wants whole numbers here too
                if (win[k] !== undefined && !Number.isInteger(win[k])) problems.push(`${win.name}: ${k} de la ventana no es un número entero`);
            }
            if (win.size !== undefined && !(Array.isArray(win.size) && win.size.length === 2 && win.size.every(Number.isFinite)))
                problems.push(`${win.name}: size es [ancho, alto] en porcentaje`);
            const seen = new Set();   // (an object would find "constructor" or "toString" in its prototype)
            function named(n) {   // menus, items and objects with "name" are fields of the window (Lorraine D47)
                if (!n.name) return;
                if (badName(n.name)) problems.push(`${win.name}: nombre no válido ${n.name} (${badName(n.name)})`);
                else if (seen.has(n.name)) problems.push(`${win.name}: nombre repetido ${n.name}`);
                seen.add(n.name);
            }
            const contextNames = new Set();
            (win.context_menus || []).forEach((m, i) => {   // (Lorraine D15)
                if (!m.name) problems.push(`${win.name}: el menú contextual ${i + 1} no tiene nombre`);
                else contextNames.add(m.name);
            });
            (win.menus || []).concat(win.context_menus || []).forEach((m) => {
                named(m);
                (function items(list, top) {
                    (list || []).forEach((it) => {
                        if (it.separator) return;
                        named(it);
                        if (it.submenu !== undefined) {
                            if (!top) problems.push(`${win.name}: el submenú ${it.label || ''} está dentro de otro (solo hay un nivel)`);
                            else items(it.submenu, false);
                        } else if (it.event !== undefined && !Number.isInteger(it.event))
                            problems.push(`${win.name}: el evento de la opción ${it.label || ''} del menú ${m.title || ''} no es un número entero`);
                        if (it.checked !== undefined && !it.check)
                            problems.push(`${win.name}: la opción ${it.label || ''} tiene checked sin "check": true`);
                    });
                })(m.items, true);
            });
            (function walk(n) {
                if (!n) return;
                if (!n.type) problems.push(`${win.name}: un objeto sin tipo`);
                else if (!TYPES[n.type]) problems.push(`${win.name}: tipo desconocido ${n.type}`);
                else if (!TYPES[n.type].group && Array.isArray(n.children) && n.children.length)
                    problems.push(`${win.name}: ${n.name || n.type} no es un grupo: no puede tener objetos dentro`);
                const what = n.name || n.type;
                if (n.tr !== undefined && !Number.isInteger(n.tr) && !(n.tr && typeof n.tr === 'object' && !Array.isArray(n.tr) &&
                        Object.values(n.tr).every(Number.isInteger)))
                    problems.push(`${win.name}: tr de ${what} es un número o {"campo": número}`);
                const known = new Set(COMMON.map(([k]) => k).concat(((TYPES[n.type] || {}).props || []).map(([k]) => k)));
                for (const [k, v] of Object.entries(n)) {   // the compiler takes texts, numbers and true/false (unknown keys stay)
                    if (known.has(k) && v !== null && typeof v === 'object')
                        problems.push(`${win.name}: ${k} de ${what} no puede ser una lista ni un objeto`);
                }
                named(n);
                for (const [k, v] of Object.entries(n)) {   // the compiler refuses texts with #{ (interpolation)
                    if (typeof v === 'string' && v.includes('#{')) problems.push(`${win.name}: ${k} de ${n.name || n.type} no puede llevar #{`);
                }
                if (n.context_menu && !contextNames.has(n.context_menu))
                    problems.push(`${win.name}: ${what} abre el menú contextual ${n.context_menu}, que la ventana no tiene`);
                for (const k of ['event', 'change', 'ack', 'double', 'weight']) {   // ("event": "uno")
                    if (n[k] !== undefined && !Number.isInteger(n[k])) problems.push(`${win.name}: ${k} de ${n.name || n.type} no es un número entero`);
                }
                (n.children || []).forEach(walk);
            })(win.root);
        });
        return problems;
    }

    function esc(s) {
        return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    }

    /** Approximate look of the window in HTML (classes styled by media/editor.css). */
    function preview(win, selectedPath) {
        const sel = JSON.stringify(selectedPath || null);
        function render(n, path) {
            const cls = 'mui-' + n.type + (JSON.stringify(path) === sel ? ' selected' : '') + (n.hidden ? ' hidden' : '') +
                (n.disabled ? ' disabled' : '');
            const attrs = ` class="${cls}" data-path="${esc(JSON.stringify(path))}"` +   // (canvas puts its own style)
                (n.weight && n.weight !== 100 && n.type !== 'canvas' ? ` style="flex-grow:${n.weight / 100}"` : '');
            const kids = (n.children || []).map((c, i) => render(c, path.concat([i]))).join('');
            switch (n.type) {
            case 'vgroup': case 'hgroup': case 'columns': case 'scroll':
                return `<div${attrs}${n.type === 'columns' ? ` data-columns="${n.columns || 2}"` : ''}>${kids}</div>`;
            case 'frame':
                return `<fieldset${attrs}>${n.title ? `<legend>${esc(n.title)}</legend>` : ''}${kids}</fieldset>`;
            case 'tabs': {
                const titles = String(n.titles || '').split('|');
                return `<div${attrs}><div class="tabbar">${titles.map((t, i) =>
                    `<span class="${i === 0 ? 'active' : ''}">${esc(t)}</span>`).join('')}</div>` +
                    `<div class="page">${kids.length ? render(n.children[0], path.concat([0])) : ''}</div></div>`;
            }
            case 'text': return `<span${attrs}>${esc(n.text || '').replace(/\u001b./g, '')}</span>`;
            case 'label': return `<span${attrs}>${esc(n.text || '')}</span>`;
            case 'button': return `<button${attrs}>${esc((n.label || '').replace('_', ''))}</button>`;
            case 'string': return `<input${attrs} value="${esc(n.text || '')}" readonly>`;
            case 'checkbox': return `<input type="checkbox"${attrs}${n.checked ? ' checked' : ''} onclick="return false">`;
            case 'cycle': return `<select${attrs}><option>${esc(String(n.options || '').split('|')[0])}</option></select>`;
            case 'slider': return `<input type="range"${attrs} min="${n.min}" max="${n.max}" value="${n.value}" disabled>`;
            case 'gauge': return `<div${attrs}><div class="fill"></div></div>`;
            case 'list': return `<div${attrs}><div>línea 1</div><div>línea 2</div></div>`;
            case 'canvas': return `<div${attrs} style="min-width:${n.min_width}px;min-height:${n.min_height}px${
                n.weight && n.weight !== 100 ? `;flex-grow:${n.weight / 100}` : ''}"></div>`;
            case 'scrollbar': return `<div${attrs}></div>`;
            case 'image': return `<div${attrs}>${esc(n.file || 'imagen')}</div>`;
            case 'image_button': return `<button${attrs}>${esc(String(n.file || 'icono').replace(/^.*[\/:]/, ''))}</button>`;
            case 'image_toggle': return `<button${attrs}${n.checked ? ' data-pressed="1"' : ''}>${esc(String(n.file || 'icono').replace(/^.*[\/:]/, ''))}</button>`;
            case 'combo': return `<span${attrs}><input value="${esc(n.text || '')}" readonly><button>▾</button></span>`;
            default: return `<div${attrs}></div>`;
            }
        }
        const menus = (win.menus || []).map((m) => `<span>${esc(m.title || '')}</span>`).join('');
        return `<div class="mui-window"><div class="titlebar">${esc(win.title || win.name)}</div>` +
            (menus ? `<div class="menubar">${menus}</div>` : '') + render(win.root, []) + '</div>';
    }

    return { TYPES, COMMON, RESERVED, badName, newDocument, newWindow, newNode, parse, serialize, nodeAt, add, remove, move,
             dropTarget, copy, paste, moveBy, paths, setProp, names, check, preview };
}));
