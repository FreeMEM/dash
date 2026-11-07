// @ts-check
// The sprite and BOB editor's webview: a frame of an IFF ILBM drawn big, its colours, its size and kind, the
// animation and the frames, with Forja's keys. Each change goes to the extension as the whole file (spriteEditor.js),
// which keeps VS Code's undo and save; what is only on screen (the frame, the colour, the tool) stays here.
(function () {
    'use strict';
    /* global acquireVsCodeApi */
    const vscode = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi()
        : { postMessage: (m) => { (window.__posted = window.__posted || []).push(m); }, getState: () => null, setState: () => {} };
    const IFF = window.DashIFF, M = window.DashSprite;

    const E = window.DashSpriteEditor = {
        s: null,            // the sprite (DashIFF's)
        name: 'sprite.iff', // the file's name, for the copied code
        frame: 0, color: 1, tool: 0,
        onion: false, playing: false, grid: true,
        zoom: 0,            // 0: the biggest that fits
        message: '',
        drag: null,         // while the button is down: {tool, x0, y0, x1, y1, colour, filled, changed}
        cursor: null,       // the pixel under the pointer
        view: 0,            // the frame the animated view shows
    };
    const $ = (id) => /** @type {HTMLElement} */ (document.getElementById(id));

    function el(tag, attrs, ...children) {
        const e = document.createElement(tag);
        for (const [k, v] of Object.entries(attrs || {})) {
            if (v === undefined || v === null || v === false) continue;
            if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
            else if (k === 'style' && typeof v === 'object') Object.assign(e.style, v);
            else if (k in e && k !== 'list') e[k] = v;
            else e.setAttribute(k, v === true ? '' : v);
        }
        for (const c of children) if (c !== null && c !== undefined) e.append(c);
        return e;
    }
    const hex = (c) => '#' + (c & 0xFFFFFF).toString(16).padStart(6, '0');

    // --- changes -----------------------------------------------------------------------------------------------
    /** After a change to E.s: to the extension (undo, save) and on screen */
    function commit(label) {
        vscode.postMessage({ type: 'edit', label, bytes: Array.from(IFF.writeIlbm(E.s)) });
        render();
    }
    function say(text) { E.message = text || ''; renderStatus(); }
    /** The result of a model change: {ok, message} */
    function apply(r, label) {
        if (r && r.message) E.message = r.message; else E.message = '';
        if (r && r.ok) commit(label); else render();
    }
    function clampState() {
        const s = E.s;
        if (E.frame >= s.frames.length) E.frame = s.frames.length - 1;
        if (E.frame < 0) E.frame = 0;
        if (E.color >= M.colours(s)) E.color = M.colours(s) - 1;
        if (E.view >= s.frames.length) E.view = 0;
    }

    function setFrame(f) { E.frame = f; E.view = f; render(); }

    // the frame operations, as Forja's keys
    const ops = {
        newFrame: (copy) => { E.frame = M.newFrame(E.s, E.frame, copy); commit(copy ? 'Duplicar fotograma' : 'Fotograma nuevo'); },
        removeFrame: () => { const r = M.removeFrame(E.s, E.frame); if (r.frame < 0) say(r.message); else { E.frame = r.frame; commit('Quitar fotograma'); } },
        moveFrame: (step) => { const f = M.moveFrame(E.s, E.frame, step); if (f >= 0) { E.frame = f; commit('Mover fotograma'); } },
        clearFrame: () => { if (M.clearFrame(E.s, E.frame)) commit('Vaciar fotograma'); },
        mirror: (h) => { M.mirror(E.s, E.frame, h); commit(h ? 'Espejo horizontal' : 'Espejo vertical'); },
        shift: (dx, dy) => { M.shift(E.s, E.frame, dx, dy); commit('Desplazar'); },
        size: (dw, dh) => apply(M.changeSize(E.s, dw, dh), 'Tamaño'),
        kind: () => apply(M.cycleKind(E.s), 'Tipo'),
        speed: (d) => { if (M.setSpeed(E.s, E.s.speed + d)) commit('Velocidad'); },
        play: () => { E.playing = !E.playing; E.view = E.frame; startTimer(); render(); },
        onion: () => { E.onion = !E.onion; render(); },
        code: () => vscode.postMessage({ type: 'clipboard', text: M.code(E.s, E.name),
            say: 'Copiadas las líneas de Dash que cargan ' + E.name }),
    };

    // --- the grid ----------------------------------------------------------------------------------------------
    function zoomNow() {
        if (E.zoom) return E.zoom;
        const pane = $('canvas-pane');
        const w = Math.max(64, pane.clientWidth - 16), h = Math.max(64, pane.clientHeight - 16);
        return Math.max(1, Math.min(48, Math.floor(Math.min(w / E.s.width, h / E.s.height))));
    }

    /** Draws frame f of sprite s on canvas c at zoom z (onion: the frame before, faint, where this one is 0) */
    function paint(c, s, f, z, onion) {
        const w = s.width, h = s.height;
        c.width = w * z; c.height = h * z;
        const ctx = c.getContext('2d');
        const img = ctx.createImageData(w, h);
        const p = s.frames[f], prev = onion && s.frames.length > 1 ? s.frames[(f + s.frames.length - 1) % s.frames.length] : null;
        const bg = s.palette[0];
        for (let i = 0; i < w * h; i++) {
            let c1 = s.palette[p[i]];
            if (!p[i] && prev && prev[i]) {
                const o = s.palette[prev[i]];
                const mix = (sh) => Math.round(((bg >> sh) & 255) * 0.6 + ((o >> sh) & 255) * 0.4);
                c1 = (mix(16) << 16) | (mix(8) << 8) | mix(0);
            }
            img.data[i * 4] = (c1 >> 16) & 255; img.data[i * 4 + 1] = (c1 >> 8) & 255;
            img.data[i * 4 + 2] = c1 & 255; img.data[i * 4 + 3] = 255;
        }
        const tmp = document.createElement('canvas');
        tmp.width = w; tmp.height = h;
        tmp.getContext('2d').putImageData(img, 0, 0);
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(tmp, 0, 0, w * z, h * z);
        return ctx;
    }

    function renderGrid() {
        const s = E.s, z = zoomNow(), c = /** @type {HTMLCanvasElement} */ ($('grid'));
        const ctx = paint(c, s, E.frame, z, E.onion);
        // the figure being drawn
        const d = E.drag;
        if (d && (d.tool === 1 || d.tool === 2)) {
            const pts = d.tool === 1 ? M.linePoints(s, d.x0, d.y0, d.x1, d.y1) : M.boxPoints(s, d.x0, d.y0, d.x1, d.y1, d.filled);
            ctx.fillStyle = hex(s.palette[d.colour]);
            for (const i of pts) ctx.fillRect((i % s.width) * z, Math.floor(i / s.width) * z, z, z);
        }
        if (E.grid && z >= 6) {
            ctx.strokeStyle = 'rgba(128,128,128,0.35)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            for (let x = 1; x < s.width; x++) { ctx.moveTo(x * z + 0.5, 0); ctx.lineTo(x * z + 0.5, s.height * z); }
            for (let y = 1; y < s.height; y++) { ctx.moveTo(0, y * z + 0.5); ctx.lineTo(s.width * z, y * z + 0.5); }
            ctx.stroke();
        }
        // the grab point (GRAB): a cross, always while the grab tool is chosen
        if (E.tool === 5 || s.grabX || s.grabY) {
            ctx.strokeStyle = E.tool === 5 ? '#ff0' : 'rgba(255,255,0,0.5)';
            ctx.lineWidth = Math.max(1, z / 6);
            const gx = s.grabX * z + z / 2, gy = s.grabY * z + z / 2;
            ctx.beginPath();
            ctx.moveTo(gx - z, gy); ctx.lineTo(gx + z, gy); ctx.moveTo(gx, gy - z); ctx.lineTo(gx, gy + z);
            ctx.stroke();
        }
        c.setAttribute('aria-label', `Fotograma ${E.frame + 1} de ${s.frames.length}, ${s.width} x ${s.height}`);
    }

    function pixelAt(e) {
        const c = /** @type {HTMLCanvasElement} */ ($('grid')), r = c.getBoundingClientRect();
        const z = c.width / E.s.width;
        return { x: Math.floor((e.clientX - r.left) * (c.width / r.width) / z), y: Math.floor((e.clientY - r.top) * (c.height / r.height) / z) };
    }

    function down(e) {
        if (!E.s || (e.button !== 0 && e.button !== 2)) return;
        e.preventDefault();
        $('grid').focus();
        const s = E.s, { x, y } = pixelAt(e);
        if (x < 0 || y < 0 || x >= s.width || y >= s.height) return;
        if (e.ctrlKey || E.tool === 4) {                                   // the picker: Ctrl + click, or K
            E.color = M.px(s, E.frame, x, y);
            render();
            return;
        }
        const colour = e.altKey || e.button === 2 ? 0 : E.color;          // Alt + click (or the right button) erases
        if (E.tool === 5) { s.grabX = x; s.grabY = y; commit('Punto de agarre'); return; }
        if (E.tool === 3) { if (M.fill(s, E.frame, x, y, colour)) commit('Rellenar'); return; }
        E.drag = { tool: E.tool, x0: x, y0: y, x1: x, y1: y, colour, filled: e.shiftKey, changed: false };
        if (E.tool === 0) E.drag.changed = M.plot(s, E.frame, M.linePoints(s, x, y, x, y), colour);
        c_capture(e);
        renderGrid();
    }
    function c_capture(e) { try { $('grid').setPointerCapture(e.pointerId); } catch (err) { /* not a pointer event */ } }

    function move(e) {
        if (!E.s) return;
        const p = pixelAt(e);
        E.cursor = p.x >= 0 && p.y >= 0 && p.x < E.s.width && p.y < E.s.height ? p : null;
        const d = E.drag;
        if (d) {
            if (d.tool === 0) {
                if (M.plot(E.s, E.frame, M.linePoints(E.s, d.x1, d.y1, p.x, p.y), d.colour)) d.changed = true;
            }
            d.x1 = p.x; d.y1 = p.y;
            renderGrid();
        }
        renderStatus();
    }

    function up() {
        const d = E.drag;
        if (!d) return;
        E.drag = null;
        const s = E.s;
        if (d.tool === 1 || d.tool === 2) {
            const pts = d.tool === 1 ? M.linePoints(s, d.x0, d.y0, d.x1, d.y1) : M.boxPoints(s, d.x0, d.y0, d.x1, d.y1, d.filled);
            if (M.plot(s, E.frame, pts, d.colour)) commit(d.tool === 1 ? 'Línea' : 'Caja');
            else renderGrid();
        } else if (d.changed) commit('Dibujar');
    }

    // --- the panes ---------------------------------------------------------------------------------------------
    function renderToolbar() {
        const bar = $('toolbar');
        bar.replaceChildren();
        M.TOOLS.forEach((t, i) => bar.append(el('button', { 'aria-pressed': String(E.tool === i), 'data-tool': t,
            title: `${M.TOOL_NAMES[i]} (${M.TOOL_KEYS[i].toUpperCase()})` + (i === 2 ? '; con Mayúsculas al empezar, rellena' : ''),
            onclick: () => { E.tool = i; render(); } }, M.TOOL_NAMES[i])));
        bar.append(el('span', { className: 'sep' }));
        bar.append(el('button', { title: 'Espejo de izquierda a derecha (H)', onclick: () => ops.mirror(true) }, '⇋ H'));
        bar.append(el('button', { title: 'Espejo de arriba abajo (V)', onclick: () => ops.mirror(false) }, '⇵ V'));
        bar.append(el('span', { className: 'sep' }));
        bar.append(el('button', { title: 'Alejar', onclick: () => { E.zoom = Math.max(1, zoomNow() - 1); render(); } }, '−'));
        bar.append(el('button', { title: 'Acercar', onclick: () => { E.zoom = Math.min(64, zoomNow() + 1); render(); } }, '+'));
        bar.append(el('button', { title: 'Ajustar a la ventana', 'aria-pressed': String(!E.zoom), onclick: () => { E.zoom = 0; render(); } }, 'Ajustar'));
        bar.append(el('button', { title: 'Rejilla entre los píxeles', 'aria-pressed': String(E.grid), onclick: () => { E.grid = !E.grid; render(); } }, 'Rejilla'));
        bar.append(el('span', { className: 'sep' }));
        bar.append(el('button', { title: 'Deshacer (Ctrl+Z)', onclick: () => vscode.postMessage({ type: 'undo' }) }, '↶'));
        bar.append(el('button', { title: 'Rehacer (Ctrl+Y)', onclick: () => vscode.postMessage({ type: 'redo' }) }, '↷'));
        bar.append(el('span', { className: 'sep' }));
        bar.append(el('button', { id: 'code', title: 'Copiar las líneas de Dash que lo cargan (C)', onclick: ops.code }, 'Copiar código'));
        bar.append(el('button', { id: 'amiga', className: 'on', disabled: amiga.busy, title: 'Cargarlo en el Amiga emulado como lo haría un juego',
            onclick: () => vscode.postMessage({ type: 'amiga' }) }, 'Ver en Amiga'));
    }

    function renderPalette() {
        const s = E.s, pane = $('palette-pane'), n = M.colours(s);
        pane.replaceChildren(el('h3', {}, `Colores (${n})`));
        const sw = el('div', { className: 'swatches', role: 'listbox', 'aria-label': 'Paleta' });
        for (let i = 0; i < n; i++)
            sw.append(el('button', { className: 'swatch' + (i === E.color ? ' selected' : ''), role: 'option',
                'aria-selected': String(i === E.color), title: `Color ${i}: ${hex(s.palette[i])}` + (i === 0 ? ' (transparente)' : ''),
                style: { background: hex(s.palette[i]) }, onclick: () => { E.color = i; render(); } }, n <= 32 ? String(i) : ''));
        pane.append(sw);
        const c = s.palette[E.color];
        pane.append(el('div', { className: 'row' }, el('span', {}, `Color ${E.color}`),
            el('span', { className: 'hint' }, hex(c) + (s.hardware ? ' (4 bits por componente)' : ''))));
        ['R', 'G', 'B'].forEach((name, k) => {
            const v = (c >> (16 - k * 8)) & 255;
            const num = el('span', { style: { minWidth: '2.2em', textAlign: 'right' } }, String(v));
            const range = /** @type {HTMLInputElement} */ (el('input', { type: 'range', min: 0, max: 255, step: s.hardware ? 17 : 1,
                value: v, 'aria-label': ['Rojo', 'Verde', 'Azul'][k] }));
            range.addEventListener('input', () => {
                M.setComponent(E.s, E.color, k, Number(range.value));
                num.textContent = String((E.s.palette[E.color] >> (16 - k * 8)) & 255);
                renderGrid(); renderFrames(); renderPreview();
            });
            range.addEventListener('change', () => commit('Color'));
            pane.append(el('div', { className: 'row' }, el('label', { style: { minWidth: '1em' } }, name), range, num));
        });
    }

    function renderSize() {
        const s = E.s, pane = $('size-pane'), kind = M.kindOf(s);
        pane.replaceChildren(el('h3', {}, 'Tamaño y tipo'));
        const kinds = el('select', { 'aria-label': 'Tipo', title: 'T pasa al tipo siguiente',
            onchange: (e) => apply(M.setKind(E.s, e.target.value), 'Tipo') });
        for (const k of ['sprite', 'attached', 'bob']) kinds.append(el('option', { value: k, selected: k === kind }, M.KIND_NAMES[k]));
        pane.append(el('div', { className: 'row' }, el('label', {}, 'Tipo'), kinds));
        const num = (label, value, disabled, set) => el('div', { className: 'row' }, el('label', {}, label),
            el('input', { type: 'number', min: 1, max: M.MAX_SIDE, value, disabled, 'aria-label': label,
                onchange: (e) => set(Number(e.target.value) | 0) }));
        pane.append(num('Ancho', s.width, s.hardware, (w) => apply(M.setSize(E.s, w, E.s.height), 'Tamaño')));
        pane.append(num('Alto', s.height, false, (h) => apply(M.setSize(E.s, E.s.width, h), 'Tamaño')));
        const cols = el('select', { 'aria-label': 'Colores', disabled: s.hardware,
            onchange: (e) => apply(M.changePlanes(E.s, Number(e.target.value)), 'Colores') });
        for (let p = 1; p <= 8; p++) cols.append(el('option', { value: p, selected: p === s.planes }, String(1 << p)));
        pane.append(el('div', { className: 'row' }, el('label', {}, 'Colores'), cols));
        pane.append(el('div', { className: 'hint' }, 'Ctrl + flechas cambian el tamaño. ' +
            (kind === 'bob' ? 'Un BOB, del tamaño y los colores que quieras.' :
                kind === 'sprite' ? 'Sprite de hardware: 16 de ancho, 3 colores y el transparente.' :
                    'Sprite acoplado: 16 de ancho, 15 colores y el transparente.')));
    }

    function renderAnim() {
        const s = E.s, pane = $('anim-pane');
        pane.replaceChildren(el('h3', {}, 'Animar'));
        pane.append(el('canvas', { id: 'preview', 'aria-label': 'Vista animada' }));
        const fps = (50 / s.speed).toFixed(s.speed > 5 ? 1 : 0);
        pane.append(el('div', { className: 'row' },
            el('button', { id: 'play', 'aria-pressed': String(E.playing), title: 'En marcha o parada (Espacio)', onclick: ops.play },
                E.playing ? '⏸ Parar' : '▶ Animar'),
            el('button', { title: 'Más lento (-)', onclick: () => ops.speed(1) }, '−'),
            el('span', { title: 'Tics de 1/50 s por fotograma' }, `${s.speed} tics (${fps}/s)`),
            el('button', { title: 'Más rápido (+)', onclick: () => ops.speed(-1) }, '+')));
        pane.append(el('div', { className: 'row' },
            el('button', { 'aria-pressed': String(E.onion), title: 'Piel de cebolla: el fotograma anterior, tenue (O)', onclick: ops.onion }, 'Cebolla')));
        renderPreview();
    }

    function renderPreview() {
        const c = /** @type {HTMLCanvasElement} */ (document.getElementById('preview'));
        if (!c) return;
        const s = E.s, z = Math.max(1, Math.min(8, Math.floor(160 / Math.max(s.width, s.height))));
        paint(c, s, E.playing ? E.view : E.frame, z, false);
    }

    function renderFrames() {
        const s = E.s, box = $('frames');
        box.replaceChildren();
        const z = Math.max(1, Math.min(4, Math.floor(48 / Math.max(s.width, s.height))));
        s.frames.forEach((f, i) => {
            const c = /** @type {HTMLCanvasElement} */ (el('canvas'));
            paint(c, s, i, z, false);
            box.append(el('button', { className: 'frame' + (i === E.frame ? ' selected' : ''), role: 'option',
                'aria-selected': String(i === E.frame), title: `Fotograma ${i + 1}`, onclick: () => setFrame(i) }, c, String(i + 1)));
        });
        box.append(el('button', { id: 'new-frame', title: 'Fotograma nuevo (N); D lo duplica', onclick: () => ops.newFrame(false) }, '+'));
    }

    function renderStatus() {
        const s = E.s, st = $('status');
        if (!s) return;
        const parts = [`${M.KIND_NAMES[M.kindOf(s)]} de ${s.width} x ${s.height}`, `fotograma ${E.frame + 1} de ${s.frames.length}`,
            `color ${E.color}`];
        if (E.cursor) parts.push(`x ${E.cursor.x}, y ${E.cursor.y}`);
        st.replaceChildren(el('span', { className: 'message' }, E.message), parts.join(' · '));
    }

    function render() {
        if (!E.s) return;
        clampState();
        renderToolbar(); renderPalette(); renderSize(); renderAnim(); renderFrames(); renderStatus();
        renderGrid();                                  // the last: its zoom fits what the other panes left
    }

    // --- the animated view -------------------------------------------------------------------------------------
    let timer = null;
    function startTimer() {
        if (timer) { clearInterval(timer); timer = null; }
        if (!E.playing || !E.s) return;
        timer = setInterval(() => {
            if (!E.s || !E.playing) return;
            E.view = (E.view + 1) % E.s.frames.length;
            renderPreview();
        }, E.s.speed * 20);
    }

    // --- keys: Forja's ----------------------------------------------------------------------------------------
    function key(e) {
        if (!E.s) return;
        const t = /** @type {HTMLElement} */ (e.target);
        if (t && /^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName)) return;
        if (e.metaKey) return;
        const k = e.key, s = E.s;
        const arrow = { ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowDown: [0, 1], ArrowUp: [0, -1] }[k];
        let done = true;
        if (e.ctrlKey && arrow) ops.size(arrow[0], arrow[1]);
        else if (e.ctrlKey) done = false;                                  // Ctrl+Z, Ctrl+C...: VS Code's or the clipboard's
        else if (e.shiftKey && arrow) ops.shift(arrow[0], arrow[1]);
        else if (e.altKey && arrow && arrow[0]) ops.moveFrame(arrow[0]);
        else if (k === 'ArrowRight' || k === 'ArrowLeft') setFrame((E.frame + (k === 'ArrowRight' ? 1 : -1) + s.frames.length) % s.frames.length);
        else if (k === 'ArrowUp' || k === 'ArrowDown') { E.color = (E.color + (k === 'ArrowDown' ? 1 : -1) + M.colours(s)) % M.colours(s); render(); }
        else if (k === 'Delete') ops.removeFrame();
        else if (k === 'Backspace') ops.clearFrame();
        else if (k === ' ') ops.play();
        else if (k === '+') ops.speed(-1);
        else if (k === '-') ops.speed(1);
        else if (/^[0-9]$/.test(k) && Number(k) < M.colours(s)) { E.color = Number(k); render(); }
        else {
            const l = k.toLowerCase();
            const tool = l.length === 1 ? M.TOOL_KEYS.indexOf(l) : -1;
            if (tool >= 0) { E.tool = tool; render(); }
            else if (l === 't') ops.kind();
            else if (l === 'n') ops.newFrame(false);
            else if (l === 'd') ops.newFrame(true);
            else if (l === 'h') ops.mirror(true);
            else if (l === 'v') ops.mirror(false);
            else if (l === 'o') ops.onion();
            else if (l === 'c') ops.code();
            else done = false;
        }
        if (done) e.preventDefault();
    }

    // Ctrl+C / X / V: the frame, through the clipboard events VS Code gives a webview
    function clip(e) {
        if (!E.s) return;
        const t = /** @type {HTMLElement} */ (e.target);
        if (t && /^(INPUT|TEXTAREA)$/.test(t.tagName)) return;
        if (e.type === 'paste') {
            const f = M.pasteFrame(E.s, E.frame, e.clipboardData ? e.clipboardData.getData('text/plain') : '');
            if (f < 0) say('No hay ningún fotograma copiado.');
            else { E.frame = f; commit('Pegar fotograma'); }
        } else {
            if (e.clipboardData) e.clipboardData.setData('text/plain', M.frameText(E.s, E.frame));
            if (e.type === 'cut') {
                const r = M.removeFrame(E.s, E.frame);
                if (r.frame < 0) { M.clearFrame(E.s, E.frame); commit('Cortar fotograma'); }
                else { E.frame = r.frame; commit('Cortar fotograma'); }
            } else say('Fotograma copiado.');
        }
        e.preventDefault();
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
        const m = ev.data;
        if (!m || m.type !== 'load') return;
        if (m.name) E.name = m.name;
        try {
            E.s = IFF.readIlbm(new Uint8Array(m.bytes));
            $('error').className = '';
            $('layout').style.display = '';
        } catch (err) {
            E.s = null;
            $('error').textContent = (m.name || 'El fichero') + ': ' + err.message + ' Ábrelo con otro editor (Abrir con...).';
            $('error').className = 'shown';
            $('layout').style.display = 'none';
            return;
        }
        if (!m.keep) { E.frame = 0; E.view = 0; E.color = Math.min(1, M.colours(E.s) - 1); }
        render();
        startTimer();
    });

    const grid = $('grid');
    grid.addEventListener('pointerdown', down);
    grid.addEventListener('pointermove', move);
    grid.addEventListener('pointerup', up);
    grid.addEventListener('pointercancel', up);
    grid.addEventListener('pointerleave', () => { E.cursor = null; renderStatus(); });
    grid.addEventListener('contextmenu', (e) => e.preventDefault());
    $('canvas-pane').addEventListener('wheel', (e) => {
        if (!e.ctrlKey || !E.s) return;
        e.preventDefault();
        E.zoom = Math.max(1, Math.min(64, zoomNow() + (e.deltaY < 0 ? 1 : -1)));
        renderGrid();
    }, { passive: false });
    document.addEventListener('keydown', key);
    for (const t of ['copy', 'cut', 'paste']) document.addEventListener(t, clip);
    window.addEventListener('resize', () => { if (E.s && !E.zoom) renderGrid(); });
    E.ops = ops;
    vscode.postMessage({ type: 'ready' });
})();
