// Webview of the .dashui editor: palette, tree, properties, menus and preview.
// The document text belongs to VS Code: every change is sent whole ({type:'edit'}),
// VS Code applies it (undo, save, dirty state work as usual) and sends the text back
// ({type:'update'}). In a plain browser (tests) acquireVsCodeApi is faked.
(function () {
    'use strict';
    const M = window.DashUI;
    const vscode = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi()
        : { postMessage: (m) => (window.__posted = window.__posted || []).push(m), getState: () => null, setState() {} };

    let doc = null;          // the parsed document
    let error = null;        // text that is not valid .dashui
    let winIndex = 0;        // window shown
    let selected = [];       // path of the selected object ([] = root)
    let dragging = null;     // {type} from the palette or {path} from the tree

    const $ = (id) => document.getElementById(id);
    const el = (tag, attrs, ...kids) => {
        const e = document.createElement(tag);
        for (const [k, v] of Object.entries(attrs || {})) {
            if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
            else if (k === 'class') e.className = v;
            else if (v !== undefined && v !== null && v !== false) e.setAttribute(k, v === true ? '' : v);
        }
        for (const k of kids) if (k !== null && k !== undefined) e.append(k);
        return e;
    };

    function win() { return doc && doc.windows[winIndex]; }

    function commit() {
        const text = M.serialize(doc);
        vscode.postMessage({ type: 'edit', text });
        render();
    }

    /** Path of the object with that name in a window, or null */
    function findNamed(w, name) {
        let found = null;
        (function walk(n, path) {
            if (found || !n) return;
            if (n.name === name) { found = path; return; }
            (n.children || []).forEach((c, i) => walk(c, path.concat([i])));
        })(w && w.root, []);
        return found;
    }

    function load(text) {
        // keep the selection on the same object when the text changed elsewhere
        const old = doc && win() ? M.nodeAt(win(), selected) : null;
        const oldName = old && old.name;
        const oldWindow = doc && win() ? win().name : null;
        try {
            doc = M.parse(text);
            error = null;
            if (!doc.windows.length) doc.windows.push(M.newWindow('Principal'));
            const wi = doc.windows.findIndex((w) => w.name === oldWindow);
            if (wi >= 0) winIndex = wi;
            if (winIndex >= doc.windows.length) winIndex = 0;
            const byName = oldName ? findNamed(win(), oldName) : null;
            if (byName) selected = byName;
            else if (!M.nodeAt(win(), selected)) selected = [];
        } catch (e) {
            error = e.message;
        }
        render();
    }

    // --- palette --------------------------------------------------------------
    function renderPalette() {
        const box = $('palette');
        box.replaceChildren();
        for (const [type, t] of Object.entries(M.TYPES)) {
            box.append(el('div', {
                class: 'palette-item' + (t.group ? ' group' : ''), draggable: 'true', 'data-type': type, title: type,
                ondragstart: (e) => { dragging = { type }; e.dataTransfer.setData('text/plain', type); },
                ondblclick: () => addHere(type),
            }, t.label));
        }
    }

    /** Add inside the selected group, or after the selected object. */
    function addHere(type) {
        const w = win();
        let parentPath = selected, index;
        const node = M.nodeAt(w, selected);
        if (!node || !M.TYPES[node.type] || !M.TYPES[node.type].group) {
            parentPath = selected.slice(0, -1);
            index = selected[selected.length - 1] + 1;
        }
        selected = M.add(w, parentPath, type, index);
        commit();
    }

    // --- tree -----------------------------------------------------------------
    function describe(n) {
        const t = M.TYPES[n.type];
        const text = n.name ? n.name : (n.label || n.text || n.title || '');
        return (t ? t.label : n.type) + (text ? ' · ' + text : '');
    }

    function renderTree() {
        const box = $('tree');
        box.replaceChildren();
        if (!win()) return;
        (function walk(n, path, depth) {
            const isGroup = M.TYPES[n.type] && M.TYPES[n.type].group;
            const row = el('div', {
                class: 'tree-row' + (JSON.stringify(path) === JSON.stringify(selected) ? ' selected' : ''),
                style: `padding-left:${depth * 14 + 4}px`, draggable: path.length ? 'true' : 'false',
                'data-path': JSON.stringify(path), tabindex: '0',
                onclick: () => { selected = path; render(); },
                ondragstart: (e) => { dragging = { path }; e.dataTransfer.setData('text/plain', JSON.stringify(path)); },
                ondragover: (e) => { e.preventDefault(); row.classList.add('drop'); },
                ondragleave: () => row.classList.remove('drop'),
                ondrop: (e) => { e.preventDefault(); row.classList.remove('drop'); drop(path, isGroup); },
            }, (isGroup ? '▾ ' : '• ') + describe(n));
            box.append(row);
            (n.children || []).forEach((c, i) => walk(c, path.concat([i]), depth + 1));
        })(win().root, [], 0);
    }

    /** Dropped on the object at path: into it if it is a group, else after it. */
    function drop(path, isGroup) {
        const w = win();
        const parentPath = isGroup ? path : path.slice(0, -1);
        const index = isGroup ? undefined : path[path.length - 1] + 1;
        try {
            if (dragging && dragging.type) selected = M.add(w, parentPath, dragging.type, index);
            else if (dragging && dragging.path) selected = M.move(w, dragging.path, parentPath, index);
            else return;
            commit();
        } catch (e) {
            showProblems([e.message]);
        } finally {
            dragging = null;
        }
    }

    function deleteSelected() {
        if (!selected.length) return;
        M.remove(win(), selected);
        selected = selected.slice(0, -1);
        commit();
    }

    // --- properties -------------------------------------------------------------
    function field(node, key, kind) {
        const value = node[key];
        const id = 'prop-' + key;
        let input;
        if (kind === 'bool') {
            input = el('input', { type: 'checkbox', id, checked: !!value,
                onchange: (e) => change(node, key, e.target.checked) });
        } else {
            input = el('input', { type: kind === 'int' ? 'number' : 'text', id, value: value === undefined ? '' : value,
                onchange: (e) => change(node, key, e.target.value) });
        }
        return el('div', { class: 'prop' }, el('label', { for: id }, key), input);
    }

    function change(node, key, value) {
        const problem = M.setProp(node, key, value);
        if (problem) showProblems([problem]);
        else commit();
    }

    function renderProps() {
        const box = $('props');
        box.replaceChildren();
        const w = win();
        if (!w) return;
        const node = M.nodeAt(w, selected);
        if (!selected.length) {   // the window itself
            box.append(el('h3', {}, 'Ventana'));
            for (const [key, kind] of [['name', 'ident'], ['title', 'string'], ['id', 'int'], ['close', 'int']]) {
                box.append(el('div', { class: 'prop' }, el('label', {}, key),
                    el('input', { type: kind === 'int' ? 'number' : 'text', id: 'win-' + key,
                        value: w[key] === undefined ? '' : w[key],
                        onchange: (e) => {
                            const v = e.target.value;
                            if (kind === 'int') { if (v === '') delete w[key]; else w[key] = Number(v); }
                            else w[key] = v;
                            commit();
                        } })));
            }
            box.append(el('h3', {}, 'Menús'), renderMenus(w));
            return;
        }
        const t = M.TYPES[node.type] || { props: [], events: [] };
        box.append(el('h3', {}, t.label || node.type));
        for (const [key, kind] of M.COMMON) box.append(field(node, key, kind));
        for (const [key, kind] of t.props) box.append(field(node, key, kind));
        for (const key of t.events) box.append(field(node, key, 'int'));
        box.append(el('button', { id: 'delete', onclick: deleteSelected }, 'Borrar'));
    }

    function renderMenus(w) {
        const box = el('div', { class: 'menus' });
        (w.menus || []).forEach((m, mi) => {
            box.append(el('div', { class: 'prop' }, el('label', {}, 'menú'),
                el('input', { value: m.title || '', onchange: (e) => { m.title = e.target.value; commit(); } }),
                el('button', { title: 'Quitar', onclick: () => { w.menus.splice(mi, 1); commit(); } }, '×')));
            (m.items || []).forEach((it, ii) => {
                box.append(el('div', { class: 'prop item' },
                    it.separator ? el('span', {}, '———') :
                        el('input', { value: it.label || '', placeholder: 'texto',
                            onchange: (e) => { it.label = e.target.value; commit(); } }),
                    it.separator ? null : el('input', { class: 'key', value: it.key || '', placeholder: 'tecla',
                        onchange: (e) => { it.key = e.target.value; commit(); } }),
                    it.separator ? null : el('input', { class: 'num', type: 'number', value: it.event || '',
                        placeholder: 'evento', onchange: (e) => { it.event = Number(e.target.value); commit(); } }),
                    el('button', { title: 'Quitar', onclick: () => { m.items.splice(ii, 1); commit(); } }, '×')));
            });
            box.append(el('div', { class: 'prop item' },
                el('button', { onclick: () => { (m.items = m.items || []).push({ label: 'Opción', key: '', event: 0 }); commit(); } }, '+ opción'),
                el('button', { onclick: () => { (m.items = m.items || []).push({ separator: true }); commit(); } }, '+ separador')));
        });
        box.append(el('button', { id: 'add-menu', onclick: () => { (w.menus = w.menus || []).push({ title: 'Menú', items: [] }); commit(); } }, '+ menú'));
        return box;
    }

    // --- windows, preview, problems ------------------------------------------------
    function renderWindows() {
        const box = $('windows');
        box.replaceChildren();
        doc.windows.forEach((w, i) => box.append(el('button', {
            class: i === winIndex ? 'active' : '', onclick: () => { winIndex = i; selected = []; render(); } }, w.name)));
        box.append(el('button', { id: 'add-window', onclick: () => {
            let n = doc.windows.length + 1;
            while (doc.windows.some((w) => w.name === 'Ventana' + n)) n++;
            doc.windows.push(M.newWindow('Ventana' + n));
            winIndex = doc.windows.length - 1;
            selected = [];
            commit();
        } }, '+'));
        box.append(el('button', { id: 'amiga', title: 'Ver en Amiga (FS-UAE)',
            onclick: () => vscode.postMessage({ type: 'amiga', window: win().name }) }, 'Ver en Amiga'));
    }

    function renderPreview() {
        const box = $('preview');
        box.innerHTML = M.preview(win(), selected);
        box.querySelectorAll('[data-path]').forEach((e) => e.addEventListener('click', (ev) => {
            ev.stopPropagation();
            selected = JSON.parse(e.getAttribute('data-path'));
            render();
        }));
    }

    function showProblems(list) {
        $('problems').textContent = list.join(' · ');
    }

    function render() {
        if (error) {
            document.body.classList.add('invalid');
            $('error').textContent = 'No es un .dashui válido: ' + error + ' (corrígelo como texto: "Reopen With... Text Editor")';
            return;
        }
        document.body.classList.remove('invalid');
        renderWindows();
        renderTree();
        renderProps();
        renderPreview();
        showProblems(M.check(doc));
    }

    window.addEventListener('message', (e) => {
        const m = e.data;
        if (m.type === 'update') load(m.text);
        if (m.type === 'screenshot') {
            const img = $('amiga-shot');
            img.src = m.src || '';
            img.alt = m.error || '';
            $('amiga-status').textContent = m.error || m.status || '';
        }
    });
    document.addEventListener('keydown', (e) => {
        if ((e.key === 'Delete' || e.key === 'Backspace') && e.target.tagName !== 'INPUT') deleteSelected();
    });

    renderPalette();
    window.DashUIEditor = { load, get doc() { return doc; }, select: (p) => { selected = p; render(); } };
    vscode.postMessage({ type: 'ready' });
}());
