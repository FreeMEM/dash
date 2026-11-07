// @ts-check
// The tile map editor's webview (FMAP, as Forja's): the map drawn with its tileset (a BOB of the sprite editor, a
// frame per tile), its layers, collision layers and objects, with Forja's keys. Each change goes to the extension as
// the whole file (spriteEditor.js: the same binary document), which keeps VS Code's undo and save.
(function () {
    'use strict';
    /* global acquireVsCodeApi */
    const vscode = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi()
        : { postMessage: (m) => { (window.__posted = window.__posted || []).push(m); } };
    const IFF = window.DashIFF, D = window.DashMap;

    const E = window.DashMapEditor = {
        m: null, name: 'mapa.fmap',
        layer: 0, tile: 1, mirror: 0, tool: 0, collision: 1, kind: D.CLASSES[0], object: -1,
        page: 'tiles', zoom: 0, ox: 0, oy: 0, grid: true,
        tileset: null, tilesetFor: null, tilesetError: '',   // the tileset read (a sprite of DashIFF) and for which name
        sprites: new Map(),                                   // the sprites of the objects, by name (null: missing)
        drag: null, cursor: null, message: '',
    };
    const $ = (id) => /** @type {HTMLElement} */ (document.getElementById(id));
    function el(tag, attrs, ...children) {
        const e = document.createElement(tag);
        for (const [k, v] of Object.entries(attrs || {})) {
            if (v === undefined || v === null || v === false) continue;
            if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
            else if (k === 'style' && typeof v === 'object') Object.assign(e.style, v);
            else if (k in e) e[k] = v;
            else e.setAttribute(k, v === true ? '' : v);
        }
        for (const c of children) if (c !== null && c !== undefined) e.append(c);
        return e;
    }
    const hex = (c) => '#' + (c & 0xFFFFFF).toString(16).padStart(6, '0');
    const rgba = (c, a) => `rgba(${(c >> 16) & 255},${(c >> 8) & 255},${c & 255},${a})`;

    // --- the extension: files next to the map ------------------------------------------------------------------
    let asked = 0;
    const waiting = new Map();
    function ask(message) {
        const id = ++asked;
        return new Promise((resolve) => { waiting.set(id, resolve); vscode.postMessage(Object.assign({ id }, message)); });
    }
    async function loadTileset() {
        const name = E.m.tileset;
        if (E.tilesetFor === name) return;
        E.tilesetFor = name; E.tileset = null; E.tilesetError = ''; tileCache.clear();
        if (!name) { render(); return; }
        const r = await ask({ type: 'readFile', path: name });
        if (E.tilesetFor !== name) return;
        if (!r.bytes) E.tilesetError = `No encuentro el tileset ${name}.`;
        else {
            try { E.tileset = IFF.readIlbm(new Uint8Array(r.bytes)); } catch (e) { E.tilesetError = `${name}: ${e.message}`; }
        }
        tileCache.clear();
        render();
    }
    async function loadSprite(name) {
        if (!name || E.sprites.has(name)) return;
        E.sprites.set(name, null);
        const r = await ask({ type: 'readFile', path: name });
        try { if (r.bytes) E.sprites.set(name, IFF.readIlbm(new Uint8Array(r.bytes))); } catch (e) { /* drawn as a frame */ }
        renderView();
    }

    // --- changes -----------------------------------------------------------------------------------------------
    function commit(label) {
        vscode.postMessage({ type: 'edit', label, bytes: Array.from(IFF.writeFmap(E.m)) });
        render();
    }
    function apply(r, label) {
        E.message = (r && r.message) || '';
        if (r && 'layer' in r) E.layer = r.layer;
        if (r && 'object' in r) E.object = r.object;
        if (r && r.ok) commit(label); else render();
    }
    function say(t) { E.message = t; renderStatus(); }
    function clamp() {
        if (E.layer >= E.m.layers.length) E.layer = E.m.layers.length - 1;
        if (E.object >= E.m.objects.length) E.object = -1;
        const n = tileCount();
        if (n && E.tile > n) E.tile = n;
    }
    const tileCount = () => (E.tileset ? E.tileset.frames.length : 0);
    const collisionsHere = () => D.isCollisions(E.m, E.layer);

    // --- drawing -----------------------------------------------------------------------------------------------
    const tileCache = new Map();
    /** A tile (1 the first frame) as a canvas of its size, mirrored; opaque: colour 0 painted (layer 0) */
    function tileImage(t, mirror, opaque) {
        const key = `${t}|${mirror}|${opaque ? 1 : 0}`;
        if (tileCache.has(key)) return tileCache.get(key);
        const s = E.tileset;
        let c = null;
        if (s && t >= 1 && t <= s.frames.length) {
            c = document.createElement('canvas');
            c.width = s.width; c.height = s.height;
            const ctx = c.getContext('2d'), img = ctx.createImageData(s.width, s.height), p = s.frames[t - 1];
            for (let y = 0; y < s.height; y++)
                for (let x = 0; x < s.width; x++) {
                    const sx = mirror & IFF.MIRROR_H ? s.width - 1 - x : x, sy = mirror & IFF.MIRROR_V ? s.height - 1 - y : y;
                    const v = p[sy * s.width + sx], i = (y * s.width + x) * 4, col = s.palette[v];
                    if (!v && !opaque) continue;
                    img.data[i] = (col >> 16) & 255; img.data[i + 1] = (col >> 8) & 255; img.data[i + 2] = col & 255; img.data[i + 3] = 255;
                }
            ctx.putImageData(img, 0, 0);
        }
        if (c) tileCache.set(key, c);                      // (none yet: not kept, the tileset may still come)
        return c;
    }
    function spriteImage(s) {
        if (s._canvas) return s._canvas;
        const c = document.createElement('canvas');
        c.width = s.width; c.height = s.height;
        const ctx = c.getContext('2d'), img = ctx.createImageData(s.width, s.height), p = s.frames[0];
        for (let i = 0; i < p.length; i++) if (p[i]) {
            const col = s.palette[p[i]];
            img.data[i * 4] = (col >> 16) & 255; img.data[i * 4 + 1] = (col >> 8) & 255; img.data[i * 4 + 2] = col & 255; img.data[i * 4 + 3] = 255;
        }
        ctx.putImageData(img, 0, 0);
        s._canvas = c;
        return c;
    }

    function zoomNow() {
        if (E.zoom) return E.zoom;
        const pane = $('canvas-pane');                       // the first time: 2 if 8 rows fit, else 1 (Forja's rule)
        E.zoom = E.m.tile * 2 * 8 <= Math.max(pane.clientHeight, 1) ? 2 : 1;
        return E.zoom;
    }
    const cellPx = () => E.m.tile * zoomNow();

    function renderView() {
        const m = E.m, c = /** @type {HTMLCanvasElement} */ ($('view')), pane = $('canvas-pane');
        if (!m) return;
        const W = Math.max(64, pane.clientWidth), H = Math.max(64, pane.clientHeight);
        if (c.width !== W || c.height !== H) { c.width = W; c.height = H; }
        const ctx = c.getContext('2d');
        ctx.imageSmoothingEnabled = false;
        const z = zoomNow(), cp = cellPx();
        limitView();
        ctx.fillStyle = '#2a2a2a';
        ctx.fillRect(0, 0, W, H);
        const x0 = -E.ox * z, y0 = -E.oy * z;               // where the map's corner is on the canvas
        ctx.fillStyle = hex(E.tileset ? E.tileset.palette[0] : 0);
        ctx.fillRect(x0, y0, m.width * cp, m.height * cp);
        const c0 = Math.max(0, Math.floor(E.ox / m.tile)), r0 = Math.max(0, Math.floor(E.oy / m.tile));
        const c1 = Math.min(m.width, Math.ceil((E.ox + W / z) / m.tile)), r1 = Math.min(m.height, Math.ceil((E.oy + H / z) / m.tile));
        m.layers.forEach((l, li) => {
            if (!l.visible) return;
            for (let y = r0; y < r1; y++)
                for (let x = c0; x < c1; x++) {
                    const v = l.cells[y * m.width + x];
                    if (!v) continue;
                    const px = x0 + x * cp, py = y0 + y * cp;
                    if (l.type === D.COLLISIONS) {
                        const col = D.COLLISION_COLOURS[(v - 1) & 3];
                        ctx.fillStyle = rgba(col, 0.35);
                        ctx.fillRect(px, py, cp, cp);
                        ctx.strokeStyle = rgba(col, 0.9);
                        ctx.strokeRect(px + 0.5, py + 0.5, cp - 1, cp - 1);
                        continue;
                    }
                    const t = v & IFF.TILE_MASK, img = tileImage(t, v & (IFF.MIRROR_H | IFF.MIRROR_V), li === 0);
                    if (img) ctx.drawImage(img, px, py, cp, cp);
                    else {                                    // no tileset: the number, in a colour of its own
                        ctx.fillStyle = `hsl(${(t * 47) % 360} 50% 40%)`;
                        ctx.fillRect(px, py, cp, cp);
                        if (cp >= 16) { ctx.fillStyle = '#fff'; ctx.font = `${Math.min(12, cp / 2)}px sans-serif`; ctx.fillText(String(t), px + 2, py + cp - 3); }
                    }
                }
        });
        // objects: their sprite (its first frame), or a frame with the initial of the class
        m.objects.forEach((o, i) => {
            const px = x0 + o.x * z, py = y0 + o.y * z, s = o.sprite ? E.sprites.get(o.sprite) : null;
            if (o.sprite && !E.sprites.has(o.sprite)) loadSprite(o.sprite);
            if (s) ctx.drawImage(spriteImage(s), px, py, s.width * z, s.height * z);
            else {
                ctx.strokeStyle = '#fff';
                ctx.strokeRect(px + 1.5, py + 1.5, cp - 3, cp - 3);
                ctx.fillStyle = '#fff';
                ctx.font = `bold ${Math.max(8, cp * 0.6)}px sans-serif`;
                ctx.fillText((o.kind[0] || '?').toUpperCase(), px + cp * 0.25, py + cp * 0.75);
            }
            if (i === E.object && E.page === 'objects') {
                ctx.strokeStyle = '#ff0'; ctx.lineWidth = 2;
                ctx.strokeRect(px, py, cp, cp);
                ctx.lineWidth = 1;
            }
        });
        if (E.grid && cp >= 8) {
            ctx.strokeStyle = 'rgba(128,128,128,0.35)';
            ctx.beginPath();
            for (let x = c0; x <= c1; x++) { ctx.moveTo(x0 + x * cp + 0.5, y0 + r0 * cp); ctx.lineTo(x0 + x * cp + 0.5, y0 + r1 * cp); }
            for (let y = r0; y <= r1; y++) { ctx.moveTo(x0 + c0 * cp, y0 + y * cp + 0.5); ctx.lineTo(x0 + c1 * cp, y0 + y * cp + 0.5); }
            ctx.stroke();
        }
        const d = E.drag;
        if (d && d.box) {
            ctx.strokeStyle = '#ff0';
            const xa = Math.min(d.x0, d.x1), ya = Math.min(d.y0, d.y1);
            ctx.strokeRect(x0 + xa * cp + 0.5, y0 + ya * cp + 0.5, (Math.abs(d.x1 - d.x0) + 1) * cp - 1, (Math.abs(d.y1 - d.y0) + 1) * cp - 1);
        } else if (E.cursor) {
            ctx.strokeStyle = 'rgba(255,255,255,0.7)';
            ctx.strokeRect(x0 + E.cursor.x * cp + 0.5, y0 + E.cursor.y * cp + 0.5, cp - 1, cp - 1);
        }
        c.setAttribute('aria-label', `Mapa de ${m.width} x ${m.height}, capa ${E.layer + 1}: ${m.layers[E.layer].name}`);
    }

    /** The view does not go past the map (but a small map stays at the corner) */
    function limitView() {
        const z = zoomNow(), pane = $('canvas-pane');
        const maxX = Math.max(0, E.m.width * E.m.tile - pane.clientWidth / z), maxY = Math.max(0, E.m.height * E.m.tile - pane.clientHeight / z);
        E.ox = Math.max(0, Math.min(maxX, E.ox)); E.oy = Math.max(0, Math.min(maxY, E.oy));
    }
    function moveView(dx, dy) { E.ox += dx * E.m.tile; E.oy += dy * E.m.tile; renderView(); }
    function setZoom(z) {
        z = Math.max(1, Math.min(8, z));
        const pane = $('canvas-pane'), old = zoomNow();
        const cx = E.ox + pane.clientWidth / old / 2, cy = E.oy + pane.clientHeight / old / 2;   // keep the middle
        E.zoom = z;
        E.ox = cx - pane.clientWidth / z / 2; E.oy = cy - pane.clientHeight / z / 2;
        render();
    }

    // --- the mouse ---------------------------------------------------------------------------------------------
    function at(e) {
        const c = /** @type {HTMLCanvasElement} */ ($('view')), r = c.getBoundingClientRect(), z = zoomNow();
        const px = Math.floor(E.ox + (e.clientX - r.left) / z), py = Math.floor(E.oy + (e.clientY - r.top) / z);
        return { px, py, x: Math.floor(px / E.m.tile), y: Math.floor(py / E.m.tile) };
    }
    const inside = (p) => p.x >= 0 && p.y >= 0 && p.x < E.m.width && p.y < E.m.height;

    function down(e) {
        if (!E.m) return;
        e.preventDefault();
        $('view').focus();
        try { $('view').setPointerCapture(e.pointerId); } catch (err) { /* not a pointer */ }
        const p = at(e), m = E.m;
        if (e.button === 1) { E.drag = { pan: true, sx: e.clientX, sy: e.clientY, ox: E.ox, oy: E.oy }; return; }
        if (!inside(p) || (e.button !== 0 && e.button !== 2)) return;
        if (E.page === 'objects' && e.button === 0) {
            const i = D.objectAt(m, p.px, p.py);
            if (i >= 0) { E.object = i; E.drag = { object: i, moved: false }; render(); return; }
            apply(D.addObject(m, p.x, p.y, E.kind), 'Objeto nuevo');
            return;
        }
        let tool = E.tool;
        if (e.altKey || e.button === 2) tool = 4;
        else if (e.ctrlKey) tool = 3;
        const l = E.layer;
        if (tool === 3) {
            const v = D.get(m, l, p.x, p.y);
            if (collisionsHere()) { if (v >= 1 && v <= 4) E.collision = v; }
            else { E.tile = v & IFF.TILE_MASK; E.mirror = v & (IFF.MIRROR_H | IFF.MIRROR_V); }
            render();
            return;
        }
        const v = tool === 4 ? 0 : D.value(m, l, E.tile, E.mirror, E.collision);
        if (tool === 2) { if (D.fill(m, l, p.x, p.y, v)) commit('Rellenar'); return; }
        if (tool === 1) { E.drag = { box: true, x0: p.x, y0: p.y, x1: p.x, y1: p.y, v }; renderView(); return; }
        E.drag = { pencil: true, x: p.x, y: p.y, v, changed: D.set(m, l, p.x, p.y, v) };
        renderView();
    }
    function move(e) {
        if (!E.m) return;
        const p = at(e), d = E.drag;
        E.cursor = inside(p) ? { x: p.x, y: p.y } : null;
        if (d && d.pan) {
            const z = zoomNow();
            E.ox = d.ox - (e.clientX - d.sx) / z; E.oy = d.oy - (e.clientY - d.sy) / z;
        } else if (d && d.object !== undefined) {
            if (D.moveObject(E.m, d.object, p.x, p.y)) d.moved = true;
        } else if (d && d.box) { d.x1 = Math.max(0, Math.min(E.m.width - 1, p.x)); d.y1 = Math.max(0, Math.min(E.m.height - 1, p.y)); }
        else if (d && d.pencil) {
            if (D.line(E.m, E.layer, d.x, d.y, p.x, p.y, d.v)) d.changed = true;
            d.x = p.x; d.y = p.y;
        }
        renderView();
        renderStatus();
    }
    function up() {
        const d = E.drag;
        E.drag = null;
        if (!d) return;
        if (d.box) { if (D.box(E.m, E.layer, d.x0, d.y0, d.x1, d.y1, d.v)) commit('Caja'); else renderView(); }
        else if (d.pencil && d.changed) commit(d.v ? 'Dibujar' : 'Borrar');
        else if (d.object !== undefined && d.moved) commit('Mover objeto');
        else renderView();
    }

    // --- the panes ---------------------------------------------------------------------------------------------
    function renderToolbar() {
        const bar = $('toolbar');
        bar.replaceChildren();
        D.TOOLS.forEach((t, i) => bar.append(el('button', { 'aria-pressed': String(E.tool === i), 'data-tool': t,
            title: `${D.TOOL_NAMES[i]} (${D.TOOL_KEYS[i].toUpperCase()})`, onclick: () => { E.tool = i; if (E.page === 'objects') E.page = 'tiles'; render(); } },
            D.TOOL_NAMES[i])));
        bar.append(el('span', { className: 'sep' }));
        bar.append(el('button', { 'aria-pressed': String(!!(E.mirror & IFF.MIRROR_H)), title: 'El tile en espejo de izquierda a derecha (H)',
            onclick: () => { E.mirror ^= IFF.MIRROR_H; render(); } }, '⇋ H'));
        bar.append(el('button', { 'aria-pressed': String(!!(E.mirror & IFF.MIRROR_V)), title: 'El tile en espejo de arriba abajo (V)',
            onclick: () => { E.mirror ^= IFF.MIRROR_V; render(); } }, '⇵ V'));
        bar.append(el('span', { className: 'sep' }));
        bar.append(el('button', { title: 'Alejar (-)', onclick: () => setZoom(zoomNow() - 1) }, '−'));
        bar.append(el('span', {}, `${zoomNow()}x`));
        bar.append(el('button', { title: 'Acercar (+)', onclick: () => setZoom(zoomNow() + 1) }, '+'));
        bar.append(el('button', { 'aria-pressed': String(E.grid), title: 'Rejilla (G)', onclick: () => { E.grid = !E.grid; render(); } }, 'Rejilla'));
        bar.append(el('span', { className: 'sep' }));
        bar.append(el('button', { title: 'Deshacer (Ctrl+Z)', onclick: () => vscode.postMessage({ type: 'undo' }) }, '↶'));
        bar.append(el('button', { title: 'Rehacer (Ctrl+Y)', onclick: () => vscode.postMessage({ type: 'redo' }) }, '↷'));
        bar.append(el('span', { className: 'sep' }));
        bar.append(el('button', { id: 'code', title: 'Copiar las líneas de Dash que lo cargan y lo pintan (C)', onclick: copyCode }, 'Copiar código'));
        bar.append(el('button', { id: 'amiga', className: 'on', disabled: amiga.busy, title: 'Cargarlo en el Amiga emulado como lo haría un juego, desde la esquina de la vista',
            onclick: () => vscode.postMessage({ type: 'amiga', tx: Math.floor(E.ox / E.m.tile), ty: Math.floor(E.oy / E.m.tile) }) }, 'Ver en Amiga'));
    }
    function copyCode() {
        vscode.postMessage({ type: 'clipboard', text: D.code(E.m, E.name), say: 'Copiadas las líneas de Dash que cargan ' + E.name });
    }
    async function chooseTileset() {
        const r = await ask({ type: 'pickFile', title: 'El tileset: un BOB con un fotograma por tile' });
        if (r.path && r.path !== E.m.tileset) { E.m.tileset = r.path; commit('Tileset'); loadTileset(); }
    }

    const PAGES = [['tiles', 'Tiles'], ['layers', 'Capas'], ['map', 'Mapa'], ['objects', 'Objetos']];
    function renderSide() {
        const tabs = $('pages');
        tabs.replaceChildren(...PAGES.map(([id, name]) => el('button', { role: 'tab', 'aria-selected': String(E.page === id), 'data-page': id,
            onclick: () => { E.page = id; render(); } }, name)));
        const page = $('page');
        page.replaceChildren();
        ({ tiles: pageTiles, layers: pageLayers, map: pageMap, objects: pageObjects })[E.page](page);
    }

    function pageTiles(page) {
        const m = E.m;
        if (collisionsHere()) {
            page.append(el('h3', {}, 'Choques'), el('div', { className: 'hint' }, 'Capa de choques: el juego la lee con tilemap_get.'));
            D.COLLISION_NAMES.forEach((name, i) => page.append(el('button', { className: 'collision', 'aria-pressed': String(E.collision === i + 1),
                onclick: () => { E.collision = i + 1; render(); } }, el('i', { style: { background: hex(D.COLLISION_COLOURS[i]) } }), `${i + 1}. ${name}`)));
            return;
        }
        page.append(el('h3', {}, 'Tileset'));
        page.append(el('div', { className: 'row' }, el('span', { className: 'name' }, m.tileset || '(ninguno)'),
            el('button', { onclick: chooseTileset, title: 'Un BOB del editor de sprites, con un fotograma por tile' }, 'Elegir...')));
        if (E.tilesetError) page.append(el('div', { className: 'hint' }, E.tilesetError));
        const s = E.tileset;
        if (s && (s.width !== m.tile || s.height !== m.tile))
            page.append(el('div', { className: 'hint' }, `Los fotogramas del tileset miden ${s.width} x ${s.height}; los tiles del mapa, ${m.tile}.`));
        if (!s) return;
        page.append(el('h3', {}, `Tiles (${s.frames.length}) · elegido: ${E.tile || 'ninguno'}`));
        const box = el('div', { className: 'tiles', role: 'listbox', 'aria-label': 'Tiles' });
        const z = Math.max(1, Math.floor(32 / Math.max(s.width, s.height)));
        for (let t = 1; t <= s.frames.length; t++) {
            const c = /** @type {HTMLCanvasElement} */ (el('canvas', { width: s.width * z, height: s.height * z }));
            const ctx = c.getContext('2d');
            ctx.imageSmoothingEnabled = false;
            const img = tileImage(t, 0, true);
            if (img) ctx.drawImage(img, 0, 0, c.width, c.height);
            box.append(el('button', { className: 'tile' + (t === E.tile ? ' selected' : ''), role: 'option', 'aria-selected': String(t === E.tile),
                title: `Tile ${t}`, onclick: () => { E.tile = t; render(); } }, c));
        }
        page.append(box, el('div', { className: 'hint' }, 'Coma y punto cambian de tile; H y V, el espejo.'));
    }

    function pageLayers(page) {
        const m = E.m;
        page.append(el('h3', {}, `Capas (${m.layers.length} de ${IFF.MAX_LAYERS})`));
        m.layers.forEach((l, i) => page.append(el('div', { className: 'list-row' + (i === E.layer ? ' selected' : ''), role: 'option',
            'aria-selected': String(i === E.layer), onclick: () => { E.layer = i; render(); } },
        el('input', { type: 'checkbox', checked: l.visible, title: 'Verla u ocultarla', 'aria-label': 'Ver ' + l.name,
            onclick: (e) => e.stopPropagation(), onchange: () => apply(D.toggleVisible(m, i), 'Ver capa') }),
        el('span', { className: 'name' }, `${i}. ${l.name}`), l.type === D.COLLISIONS ? el('span', { className: 'hint' }, 'choques') : null)));
        const l = m.layers[E.layer];
        page.append(el('div', { className: 'row' }, el('label', {}, 'Nombre'), el('input', { value: l.name, 'aria-label': 'Nombre de la capa',
            onchange: (e) => apply(D.renameLayer(m, E.layer, e.target.value), 'Nombre de capa') })));
        page.append(el('div', { className: 'row' },
            el('button', { onclick: () => apply(D.addLayer(m, E.layer), 'Capa nueva') }, 'Nueva'),
            el('button', { onclick: () => apply(D.removeLayer(m, E.layer), 'Quitar capa') }, 'Quitar')));
        page.append(el('div', { className: 'row' },
            el('button', { title: 'Se pinta antes', onclick: () => apply(D.moveLayer(m, E.layer, -1), 'Mover capa') }, 'Atrás'),
            el('button', { title: 'Se pinta después', onclick: () => apply(D.moveLayer(m, E.layer, 1), 'Mover capa') }, 'Delante')));
        page.append(el('div', { className: 'row' }, el('button', { onclick: () => apply(D.toggleType(m, E.layer), 'Tipo de capa') },
            l.type === D.COLLISIONS ? 'Pasar a capa de tiles' : 'Pasar a capa de choques')));
    }

    function pageMap(page) {
        const m = E.m;
        page.append(el('h3', {}, 'Mapa'));
        const num = (label, value, set) => el('div', { className: 'row' }, el('label', {}, label),
            el('input', { type: 'number', min: 1, max: D.MAX_SIDE, value, 'aria-label': label, onchange: (e) => set(Number(e.target.value) | 0) }));
        page.append(num('Ancho', m.width, (w) => apply(D.resize(m, w, m.height), 'Tamaño del mapa')));
        page.append(num('Alto', m.height, (h) => apply(D.resize(m, m.width, h), 'Tamaño del mapa')));
        const tile = el('select', { 'aria-label': 'Tile', onchange: (e) => apply(D.setTileSize(m, Number(e.target.value)), 'Lado del tile') });
        for (const t of [8, 16, 32]) tile.append(el('option', { value: t, selected: t === m.tile }, `${t} x ${t}`));
        page.append(el('div', { className: 'row' }, el('label', {}, 'Tile'), tile));
        const zoom = el('select', { 'aria-label': 'Zoom', onchange: (e) => setZoom(Number(e.target.value)) });
        for (const z of [1, 2, 3, 4, 6, 8]) zoom.append(el('option', { value: z, selected: z === zoomNow() }, `${z}x`));
        page.append(el('div', { className: 'row' }, el('label', {}, 'Zoom'), zoom));
        page.append(el('div', { className: 'row' }, el('label', {}, 'Tileset'), el('span', { className: 'name' }, m.tileset || '(ninguno)'),
            el('button', { onclick: chooseTileset }, 'Elegir...')));
        page.append(el('div', { className: 'hint' }, 'Flechas y rueda mueven la vista (con Mayúsculas, de pantalla en pantalla); el botón del medio la arrastra.'));
    }

    function pageObjects(page) {
        const m = E.m;
        page.append(el('h3', {}, 'Clase de los objetos nuevos'));
        const row = el('div', { className: 'row', style: { flexWrap: 'wrap' } });
        for (const k of D.CLASSES) row.append(el('button', { 'aria-pressed': String(E.kind === k), onclick: () => { E.kind = k; render(); } }, k));
        page.append(row, el('div', { className: 'hint' }, 'Un clic pone uno o elige el que hay; arrastrando se mueve; Supr lo quita.'));
        const o = m.objects[E.object];
        if (o) {
            page.append(el('h3', {}, `Objeto ${E.object + 1}: x ${o.x}, y ${o.y}`));
            const kind = el('select', { 'aria-label': 'Clase', onchange: (e) => apply(D.setObject(m, E.object, { kind: e.target.value }), 'Clase del objeto') });
            for (const k of D.CLASSES.includes(o.kind) ? D.CLASSES : [o.kind, ...D.CLASSES]) kind.append(el('option', { value: k, selected: k === o.kind }, k));
            page.append(el('div', { className: 'row' }, el('label', {}, 'Clase'), kind));
            page.append(el('div', { className: 'row' }, el('label', {}, 'Nombre'), el('input', { value: o.name, 'aria-label': 'Nombre del objeto',
                onchange: (e) => apply(D.setObject(m, E.object, { name: e.target.value }), 'Nombre del objeto') })));
            page.append(el('div', { className: 'row' }, el('label', {}, 'Sprite'), el('span', { className: 'name' }, o.sprite || '(ninguno)')));
            page.append(el('div', { className: 'row' },
                el('button', { onclick: async () => {
                    const i = E.object, r = await ask({ type: 'pickFile', title: 'El sprite del objeto' });
                    if (r.path) apply(D.setObject(E.m, i, { sprite: r.path }), 'Sprite del objeto');
                } }, 'Sprite...'),
                o.sprite ? el('button', { onclick: () => apply(D.setObject(m, E.object, { sprite: '' }), 'Sin sprite') }, 'Sin sprite') : null,
                el('button', { onclick: () => apply(D.removeObject(m, E.object), 'Quitar objeto') }, 'Quitar')));
        }
        if (m.objects.length) {
            page.append(el('h3', {}, `Objetos (${m.objects.length})`));
            m.objects.forEach((ob, i) => page.append(el('div', { className: 'list-row' + (i === E.object ? ' selected' : ''), role: 'option',
                'aria-selected': String(i === E.object), onclick: () => { E.object = i; showObject(ob); render(); } },
            `${i + 1}. ${ob.kind}${ob.name ? ' "' + ob.name + '"' : ''} (${ob.x}, ${ob.y})`)));
        }
    }
    function showObject(o) {
        const pane = $('canvas-pane'), z = zoomNow();
        E.ox = o.x - pane.clientWidth / z / 2; E.oy = o.y - pane.clientHeight / z / 2;
    }

    function renderStatus() {
        const m = E.m;
        if (!m) return;
        const l = m.layers[E.layer];
        const parts = [`${m.width} x ${m.height} tiles de ${m.tile}`, `capa ${E.layer}: ${l.name}${l.type === D.COLLISIONS ? ' (choques)' : ''}`,
            E.page === 'objects' ? `objetos: ${E.kind}` : collisionsHere() ? `choque ${D.COLLISION_NAMES[E.collision - 1]}`
                : `tile ${E.tile}${E.mirror & IFF.MIRROR_H ? ' H' : ''}${E.mirror & IFF.MIRROR_V ? ' V' : ''}`];
        if (E.cursor) {
            const v = D.get(m, E.layer, E.cursor.x, E.cursor.y);
            parts.push(`x ${E.cursor.x}, y ${E.cursor.y}: ${v & IFF.TILE_MASK}`);
        }
        $('status').replaceChildren(el('span', { className: 'message' }, E.message), parts.join(' · '));
    }

    function render() {
        if (!E.m) return;
        clamp();
        renderToolbar(); renderSide(); renderView(); renderStatus();
    }

    // --- keys: Forja's ----------------------------------------------------------------------------------------
    function key(e) {
        if (!E.m) return;
        const t = /** @type {HTMLElement} */ (e.target);
        if (t && /^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName)) return;
        if (e.ctrlKey || e.metaKey) return;                           // VS Code's (undo, save...)
        const pane = $('canvas-pane'), z = zoomNow();
        const pageX = Math.max(1, Math.floor(pane.clientWidth / cellPx()) - 1), pageY = Math.max(1, Math.floor(pane.clientHeight / cellPx()) - 1);
        const k = e.key, l = k.length === 1 ? k.toLowerCase() : '';
        let done = true;
        if (k === 'ArrowRight') moveView(e.shiftKey ? pageX : 1, 0);
        else if (k === 'ArrowLeft') moveView(e.shiftKey ? -pageX : -1, 0);
        else if (k === 'ArrowDown') moveView(0, e.shiftKey ? pageY : 1);
        else if (k === 'ArrowUp') moveView(0, e.shiftKey ? -pageY : -1);
        else if (k === 'Delete' && E.page === 'objects') apply(D.removeObject(E.m, E.object), 'Quitar objeto');
        else if (l && D.TOOL_KEYS.includes(l)) { E.tool = D.TOOL_KEYS.indexOf(l); if (E.page === 'objects') E.page = 'tiles'; render(); }
        else if (l === '+') setZoom(z + 1);
        else if (l === '-') setZoom(z - 1);
        else if (l === 'g') { E.grid = !E.grid; render(); }
        else if (l === 'h') { E.mirror ^= IFF.MIRROR_H; render(); }
        else if (l === 'v') { E.mirror ^= IFF.MIRROR_V; render(); }
        else if (l === 'c') copyCode();
        else if ((l === '.' || l === ',') && tileCount()) {
            const n = tileCount();
            E.tile = l === '.' ? (E.tile % n) + 1 : ((E.tile + n - 2) % n) + 1;
            render();
        } else done = false;
        if (done) e.preventDefault();
    }


    // --- Ver en Amiga: the picture of the emulated Amiga (the extension runs it) -------------------------------
    const amiga = { busy: false, status: '', error: '', src: '' };
    function renderAmiga() {
        const pane = $('amiga-pane');
        if (!pane) return;
        pane.replaceChildren();
        if (!amiga.status && !amiga.error && !amiga.src) return;
        pane.append(el('h3', {}, 'Ver en Amiga'));
        if (amiga.error) pane.append(el('div', { className: 'hint error' }, amiga.error));
        else if (amiga.status) pane.append(el('div', { className: 'hint' }, amiga.status));
        if (amiga.src) pane.append(el('img', { id: 'amiga-shot', src: amiga.src, alt: 'La pantalla del Amiga emulado' }));
    }
    window.addEventListener('message', (ev) => {
        const m = ev.data;
        if (!m || m.type !== 'amiga') return;
        amiga.busy = !!m.busy;
        amiga.status = m.status || '';
        amiga.error = m.error || '';
        if (m.src) amiga.src = m.src;
        const b = document.getElementById('amiga');
        if (b) b.disabled = amiga.busy;
        renderAmiga();
    });

    // --- messages ----------------------------------------------------------------------------------------------
    window.addEventListener('message', (ev) => {
        const msg = ev.data;
        if (!msg) return;
        if ((msg.type === 'file' || msg.type === 'picked') && waiting.has(msg.id)) {
            waiting.get(msg.id)(msg);
            waiting.delete(msg.id);
            return;
        }
        if (msg.type !== 'load') return;
        if (msg.name) E.name = msg.name;
        try {
            E.m = IFF.readFmap(new Uint8Array(msg.bytes));
            if (!E.m.layers.length) E.m.layers.push({ name: 'fondo', type: D.TILES, visible: true, cells: new Uint16Array(E.m.width * E.m.height) });
            $('error').className = '';
            $('layout').style.display = '';
        } catch (err) {
            E.m = null;
            $('error').textContent = (msg.name || 'El fichero') + ': ' + err.message + ' Ábrelo con otro editor (Abrir con...).';
            $('error').className = 'shown';
            $('layout').style.display = 'none';
            return;
        }
        if (!msg.keep) { E.layer = 0; E.object = -1; E.ox = 0; E.oy = 0; }
        if (E.m.tileset !== E.tilesetFor) loadTileset();
        render();
    });

    const view = $('view');
    view.addEventListener('pointerdown', down);
    view.addEventListener('pointermove', move);
    view.addEventListener('pointerup', up);
    view.addEventListener('pointercancel', up);
    view.addEventListener('pointerleave', () => { E.cursor = null; renderView(); renderStatus(); });
    view.addEventListener('contextmenu', (e) => e.preventDefault());
    view.addEventListener('auxclick', (e) => e.preventDefault());
    $('canvas-pane').addEventListener('wheel', (e) => {
        if (!E.m) return;
        e.preventDefault();
        if (e.ctrlKey) { setZoom(zoomNow() + (e.deltaY < 0 ? 1 : -1)); return; }
        const d = Math.sign(e.deltaY || e.deltaX) * 2;
        if (e.shiftKey || (!e.deltaY && e.deltaX)) moveView(d, 0); else moveView(0, d);
    }, { passive: false });
    document.addEventListener('keydown', key);
    window.addEventListener('resize', () => { if (E.m) renderView(); });
    E.render = render;
    vscode.postMessage({ type: 'ready' });
})();
