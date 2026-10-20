// Webview of the .dashui editor: palette, tree, properties, menus and preview.
// The document text belongs to VS Code: every change is sent whole ({type:'edit'}),
// VS Code applies it (undo, save, dirty state work as usual) and sends the text back
// ({type:'update'}). In a plain browser (tests) acquireVsCodeApi is faked.
// Keyboard: in the tree, arrows move the selection (left: its group, right: inside),
// Alt+arrows move the object, Delete removes it, F2 goes to its name, Enter to its
// properties, Ctrl+D duplicates; copy, cut and paste are the usual ones (the clipboard
// events, which VS Code also sends to a webview); the palette's buttons add an object.
(function () {
    'use strict';
    const M = window.DashUI;
    const vscode = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi()
        : { postMessage: (m) => (window.__posted = window.__posted || []).push(m), getState: () => null, setState() {} };

    let doc = null;          // the parsed document
    let error = null;        // text that is not valid .dashui
    let winIndex = 0;        // window shown
    let selected = [];       // path of the selected object ([] = root)
    let dragging = null;     // {type} from the palette or {path} from the tree or the preview
    let clip = null;         // the object copied last (also on the clipboard, as JSON)
    let focusTree = false;   // after the next render, the focus on the selected row of the tree
    const amiga = { busy: false, note: '', error: false };   // "Ver en Amiga": running, what it says

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
        box.setAttribute('role', 'toolbar');
        box.setAttribute('aria-orientation', 'vertical');
        box.setAttribute('aria-label', 'Añadir un objeto');
        for (const [type, t] of Object.entries(M.TYPES)) {
            box.append(el('button', {
                class: 'palette-item' + (t.group ? ' group' : ''), draggable: 'true', 'data-type': type,
                title: `Añadir ${t.label} (${type}): clic o Intro, o arrastrarlo al árbol o a la vista`,
                ondragstart: (e) => { dragging = { type }; e.dataTransfer.setData('text/plain', type); },
                onclick: () => addHere(type),
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

    /** Where a pasted or duplicated object goes: inside the selected group, or after the selected object */
    function pasteTarget() {
        const node = M.nodeAt(win(), selected);
        if (node && M.TYPES[node.type] && M.TYPES[node.type].group) return { parentPath: selected, index: undefined };
        return { parentPath: selected.slice(0, -1), index: selected[selected.length - 1] + 1 };
    }

    function pasteNode(node) {
        const t = pasteTarget();
        try {
            selected = M.paste(win(), t.parentPath, node, t.index);
            commit();
        } catch (e) {
            showProblems([e.message]);
        }
    }

    function duplicate() {
        if (!selected.length) return;
        const node = M.copy(win(), selected);
        try {
            selected = M.paste(win(), selected.slice(0, -1), node, selected[selected.length - 1] + 1);
            commit();
        } catch (e) {
            showProblems([e.message]);
        }
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
        box.setAttribute('role', 'tree');
        box.setAttribute('aria-label', 'Objetos de la ventana');
        if (!win()) return;
        (function walk(n, path, depth) {
            const isGroup = M.TYPES[n.type] && M.TYPES[n.type].group;
            const isSelected = JSON.stringify(path) === JSON.stringify(selected);
            const row = el('div', {
                class: 'tree-row' + (isSelected ? ' selected' : ''), role: 'treeitem',
                'aria-level': String(depth + 1), 'aria-selected': isSelected ? 'true' : 'false',
                'aria-expanded': isGroup ? 'true' : undefined,
                style: `padding-left:${depth * 14 + 4}px`, draggable: path.length ? 'true' : 'false',
                'data-path': JSON.stringify(path), tabindex: isSelected ? '0' : '-1',
                onclick: () => { selected = path; render(); },
                ondragstart: (e) => { dragging = { path }; e.dataTransfer.setData('text/plain', JSON.stringify(path)); },
            }, (isGroup ? '▾ ' : '• ') + describe(n));
            dropZone(row, path, false);
            box.append(row);
            (n.children || []).forEach((c, i) => walk(c, path.concat([i]), depth + 1));
        })(win().root, [], 0);
    }

    /** Before, after or into the object at path, by where the pointer is over its element (horizontal
        for the objects of a horizontal group in the preview) */
    function dropWhere(e, target, path, horizontal) {
        const node = M.nodeAt(win(), path);
        const isGroup = node && M.TYPES[node.type] && M.TYPES[node.type].group;
        const r = target.getBoundingClientRect();
        const f = horizontal ? (e.clientX - r.left) / (r.width || 1) : (e.clientY - r.top) / (r.height || 1);
        if (!path.length) return 'into';
        if (isGroup) return f < 0.25 ? 'before' : f > 0.75 ? 'after' : 'into';
        return f < 0.5 ? 'before' : 'after';
    }

    function clearDrop() {
        document.querySelectorAll('.drop-before, .drop-after, .drop-into')
            .forEach((x) => x.classList.remove('drop-before', 'drop-after', 'drop-into'));
    }

    /** An element (a tree row, an object of the preview) where palette objects and objects can be dropped */
    function dropZone(target, path, horizontal) {
        target.addEventListener('dragover', (e) => {
            if (!dragging) return;
            e.preventDefault();
            e.stopPropagation();
            clearDrop();
            target.classList.add('drop-' + dropWhere(e, target, path, horizontal));
        });
        target.addEventListener('dragleave', () => target.classList.remove('drop-before', 'drop-after', 'drop-into'));
        target.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            clearDrop();
            drop(path, dropWhere(e, target, path, horizontal));
        });
    }

    /** Dropped on the object at path: before it, after it or into it (a group) */
    function drop(path, where) {
        const w = win();
        const t = M.dropTarget(w, path, where);
        try {
            if (!t) return;
            if (dragging && dragging.type) selected = M.add(w, t.parentPath, dragging.type, t.index);
            else if (dragging && dragging.path) selected = M.move(w, dragging.path, t.parentPath, t.index);
            else return;
            commit();
        } catch (e) {
            showProblems([e.message]);
        } finally {
            dragging = null;
        }
    }

    /** The tree's keys (the selection moves, and the focus with it) */
    function treeKey(e) {
        const w = win();
        const all = M.paths(w).map((p) => JSON.stringify(p));
        const i = all.indexOf(JSON.stringify(selected));
        const go = (p) => { e.preventDefault(); selected = p; render(); };
        const node = M.nodeAt(w, selected);
        if (e.altKey && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
            e.preventDefault();
            const p = M.moveBy(w, selected, e.key === 'ArrowUp' ? -1 : 1);
            if (JSON.stringify(p) !== JSON.stringify(selected)) { selected = p; commit(); }
        } else if (e.key === 'ArrowDown' && i + 1 < all.length) go(JSON.parse(all[i + 1]));
        else if (e.key === 'ArrowUp' && i > 0) go(JSON.parse(all[i - 1]));
        else if (e.key === 'Home') go([]);
        else if (e.key === 'End') go(JSON.parse(all[all.length - 1]));
        else if (e.key === 'ArrowLeft' && selected.length) go(selected.slice(0, -1));
        else if (e.key === 'ArrowRight' && node && node.children && node.children.length) go(selected.concat([0]));
        else if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); deleteSelected(); }
        else if ((e.ctrlKey || e.metaKey) && (e.key === 'd' || e.key === 'D')) { e.preventDefault(); duplicate(); }
        else if (e.key === 'F2') {
            e.preventDefault();
            const f = $(selected.length ? 'prop-name' : 'win-name');
            if (f) { f.focus(); f.select(); }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            const f = $('props').querySelector('input, button');
            if (f) f.focus();
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
                box.append(el('div', { class: 'prop' }, el('label', { for: 'win-' + key }, key),
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
                el('input', { value: m.title || '', 'aria-label': `Título del menú ${mi + 1}`,
                              onchange: (e) => { m.title = e.target.value; commit(); } }),
                el('button', { title: 'Quitar el menú', 'aria-label': `Quitar el menú ${m.title || mi + 1}`,
                               onclick: () => { w.menus.splice(mi, 1); commit(); } }, '×')));
            (m.items || []).forEach((it, ii) => {
                box.append(el('div', { class: 'prop item' },
                    it.separator ? el('span', {}, '———') :
                        el('input', { value: it.label || '', placeholder: 'texto', 'aria-label': 'Texto de la opción',
                            onchange: (e) => { it.label = e.target.value; commit(); } }),
                    it.separator ? null : el('input', { class: 'key', value: it.key || '', placeholder: 'tecla',
                        'aria-label': 'Tecla de la opción', onchange: (e) => { it.key = e.target.value; commit(); } }),
                    it.separator ? null : el('input', { class: 'num', type: 'number', value: it.event || '',
                        placeholder: 'evento', 'aria-label': 'Evento de la opción',
                        onchange: (e) => { it.event = Number(e.target.value); commit(); } }),
                    el('button', { title: 'Quitar la opción', 'aria-label': `Quitar la opción ${it.label || ii + 1}`,
                                   onclick: () => { m.items.splice(ii, 1); commit(); } }, '×')));
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
        box.setAttribute('role', 'toolbar');
        box.setAttribute('aria-label', 'Ventanas');
        doc.windows.forEach((w, i) => box.append(el('button', {
            class: i === winIndex ? 'active' : '', 'aria-pressed': i === winIndex ? 'true' : 'false',
            onclick: () => { winIndex = i; selected = []; render(); } }, w.name)));
        box.append(el('button', { id: 'add-window', title: 'Nueva ventana', 'aria-label': 'Nueva ventana', onclick: () => {
            let n = doc.windows.length + 1;
            while (doc.windows.some((w) => w.name === 'Ventana' + n)) n++;
            doc.windows.push(M.newWindow('Ventana' + n));
            winIndex = doc.windows.length - 1;
            selected = [];
            commit();
        } }, '+'));
        box.append(el('button', { id: 'undo', title: 'Deshacer (Ctrl+Z)', onclick: () => vscode.postMessage({ type: 'undo' }) }, '↶'));
        box.append(el('button', { id: 'redo', title: 'Rehacer (Ctrl+Y)', onclick: () => vscode.postMessage({ type: 'redo' }) }, '↷'));
        box.append(el('button', { id: 'amiga', title: 'Ver en Amiga (FS-UAE)', disabled: amiga.busy,
            onclick: () => {
                amiga.busy = true;
                amiga.note = 'Compilando y arrancando el emulador…';
                renderWindows();
                vscode.postMessage({ type: 'amiga', window: win().name });
            } }, amiga.busy ? 'Arrancando el Amiga… (30 s)' : 'Ver en Amiga'));
        // what "Ver en Amiga" is doing, next to its button (the picture comes below the preview)
        box.append(el('span', { id: 'amiga-note', class: amiga.error ? 'error' : '' }, amiga.note));
    }

    function renderPreview() {
        const box = $('preview');
        box.innerHTML = M.preview(win(), selected);
        box.setAttribute('aria-hidden', 'true');      // the tree says the same to a screen reader
        box.querySelectorAll('[data-path]').forEach((e) => {
            const path = JSON.parse(e.getAttribute('data-path'));
            e.addEventListener('click', (ev) => {
                ev.preventDefault();
                ev.stopPropagation();
                selected = path;
                focusTree = true;         // the keys of the tree (Delete, arrows...) work on it now
                render();
            });
            if (path.length) {
                e.setAttribute('draggable', 'true');
                e.addEventListener('dragstart', (ev) => {
                    ev.stopPropagation();
                    dragging = { path };
                    ev.dataTransfer.setData('text/plain', JSON.stringify(path));
                });
            }
            dropZone(e, path, !!(e.parentElement && e.parentElement.classList.contains('mui-hgroup')));
        });
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
        const inTree = focusTree ||
            (document.activeElement && document.activeElement.closest && document.activeElement.closest('#tree'));
        focusTree = false;
        renderWindows();
        renderTree();
        if (inTree) {
            const row = $('tree').querySelector('.tree-row.selected');
            if (row) row.focus();
        }
        renderProps();
        renderPreview();
        showProblems(M.check(doc));
    }

    window.addEventListener('message', (e) => {
        const m = e.data;
        if (m.type === 'update') load(m.text);
        if (m.type === 'screenshot') {
            const img = $('amiga-shot');
            if (m.src) img.onload = () => img.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            img.src = m.src || '';
            img.alt = m.error || '';
            $('amiga-status').textContent = m.error || m.status || '';
            amiga.busy = !!m.busy;
            amiga.note = m.error || (m.src ? 'Listo: la imagen está debajo de la vista' : m.status || '');
            amiga.error = !!m.error;
            if (doc && !error) renderWindows();
        }
    });
    $('tree').addEventListener('keydown', (e) => { if (doc && !error) treeKey(e); });
    const editing = (t) => t && (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
    // copy, cut and paste: the clipboard events (a key in a browser, VS Code's commands in a webview)
    document.addEventListener('copy', (e) => {
        if (editing(e.target) || !doc || error || !selected.length) return;
        clip = M.copy(win(), selected);
        e.clipboardData.setData('text/plain', JSON.stringify(clip, null, 2));
        e.preventDefault();
    });
    document.addEventListener('cut', (e) => {
        if (editing(e.target) || !doc || error || !selected.length) return;
        clip = M.copy(win(), selected);
        e.clipboardData.setData('text/plain', JSON.stringify(clip, null, 2));
        e.preventDefault();
        deleteSelected();
    });
    document.addEventListener('paste', (e) => {
        if (editing(e.target) || !doc || error) return;
        let node = clip;
        try {
            const text = e.clipboardData.getData('text/plain');
            const parsed = text ? JSON.parse(text) : null;
            if (parsed && typeof parsed === 'object' && parsed.type) node = parsed;
        } catch (err) { /* not an object of a .dashui: the last one copied here */ }
        if (!node) return;
        e.preventDefault();
        pasteNode(node);
    });

    renderPalette();
    window.DashUIEditor = { load, get doc() { return doc; }, get selected() { return selected; },
                            select: (p) => { selected = p; render(); } };
    vscode.postMessage({ type: 'ready' });
}());
