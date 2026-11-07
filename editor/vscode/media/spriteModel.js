// @ts-check
// What the sprite and BOB editor does to a sprite, as Forja's (src/sprites.dash): drawing, frames, size and kind,
// colours, and the Dash lines that load it. No DOM here: the webview (media/sprite.js) and the tests use it as it is.
// A sprite is DashIFF's (media/iff.js): {width, height, planes, hardware, palette, frames, speed, grabX, grabY}.
(function (root) {
    'use strict';
    const IFF = typeof module === 'object' && module.exports ? require('./iff.js') : root.DashIFF;

    const TOOLS = ['pencil', 'line', 'box', 'fill', 'picker', 'grab'];
    const TOOL_KEYS = 'plbfka';                 // the keys of Forja: lápiz, línea, caja (box), relleno (fill)...
    const TOOL_NAMES = ['Lápiz', 'Línea', 'Caja', 'Relleno', 'Cuentagotas', 'Punto de agarre'];
    const MAX_SIDE = 256, MAX_SPEED = 50;

    const colours = (s) => 1 << s.planes;
    const kindOf = (s) => (s.hardware ? (s.planes === 4 ? 'attached' : 'sprite') : 'bob');
    const KIND_NAMES = { sprite: 'Sprite de hardware', attached: 'Sprite acoplado', bob: 'BOB' };

    /** A deep copy (the frames are typed arrays) */
    function clone(s) {
        return Object.assign({}, s, { palette: s.palette.slice(), frames: s.frames.map((f) => f.slice()) });
    }

    function px(s, f, x, y) {
        return x < 0 || y < 0 || x >= s.width || y >= s.height ? 0 : s.frames[f][y * s.width + x];
    }

    /** The pixels (indices) of a line from x0, y0 to x1, y1 (Bresenham, as Forja) */
    function linePoints(s, x0, y0, x1, y1) {
        const out = [];
        let dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
        const sx = x1 < x0 ? -1 : 1, sy = y1 < y0 ? -1 : 1;
        let err = dx - dy;
        for (;;) {
            if (x0 >= 0 && y0 >= 0 && x0 < s.width && y0 < s.height) out.push(y0 * s.width + x0);
            if (x0 === x1 && y0 === y1) break;
            const e2 = err * 2;
            if (e2 > -dy) { err -= dy; x0 += sx; }
            if (e2 < dx) { err += dx; y0 += sy; }
        }
        return out;
    }

    /** The pixels of a box from one corner to the other: its edge, or all of it if filled */
    function boxPoints(s, x0, y0, x1, y1, filled) {
        const out = [];
        const xa = Math.max(0, Math.min(x0, x1)), xb = Math.min(s.width - 1, Math.max(x0, x1));
        const ya = Math.max(0, Math.min(y0, y1)), yb = Math.min(s.height - 1, Math.max(y0, y1));
        const X1 = Math.min(x0, x1), X2 = Math.max(x0, x1), Y1 = Math.min(y0, y1), Y2 = Math.max(y0, y1);
        for (let y = ya; y <= yb; y++)
            for (let x = xa; x <= xb; x++)
                if (filled || y === Y1 || y === Y2 || x === X1 || x === X2) out.push(y * s.width + x);
        return out;
    }

    /** Puts colour c on those pixels of frame f; true if something changed */
    function plot(s, f, points, c) {
        let changed = false;
        const p = s.frames[f];
        for (const i of points) if (p[i] !== c) { p[i] = c; changed = true; }
        return changed;
    }

    /** Fills from x, y the pixels of the same colour joined by their sides (as Forja); true if something changed */
    function fill(s, f, x, y, c) {
        const p = s.frames[f];
        if (x < 0 || y < 0 || x >= s.width || y >= s.height) return false;
        const old = p[y * s.width + x];
        if (old === c) return false;
        const stack = [y * s.width + x];
        while (stack.length) {
            const i = stack.pop();
            if (p[i] !== old) continue;
            p[i] = c;
            const cx = i % s.width;
            if (cx > 0) stack.push(i - 1);
            if (cx < s.width - 1) stack.push(i + 1);
            if (i >= s.width) stack.push(i - s.width);
            if (i + s.width < p.length) stack.push(i + s.width);
        }
        return true;
    }

    /** Sets component k (0 red, 1 green, 2 blue) of colour c to v (0-255); a hardware sprite has 4 bits */
    function setComponent(s, c, k, v) {
        v = Math.max(0, Math.min(255, Math.round(v)));
        if (s.hardware) v = Math.floor((v + 8) / 17) * 17;
        const shift = 16 - k * 8;
        s.palette[c] = (s.palette[c] & ~(255 << shift) & 0xFFFFFF) | (v << shift);
    }

    function resize(s, w, h) {
        s.frames = s.frames.map((p) => {
            const n = new Uint8Array(w * h);
            for (let y = 0; y < h && y < s.height; y++)
                for (let x = 0; x < w && x < s.width; x++) n[y * w + x] = p[y * s.width + x];
            return n;
        });
        s.width = w; s.height = h;
        if (s.grabX >= w) s.grabX = w - 1;
        if (s.grabY >= h) s.grabY = h - 1;
    }

    // keeps only the colours that fit in planes (the low bits, as sprite_load)
    function setPlanes(s, planes) {
        const mask = (1 << planes) - 1;
        for (const p of s.frames) for (let i = 0; i < p.length; i++) p[i] &= mask;
        s.planes = planes;
    }

    /**
     * Changes the size by dw, dh: {ok} or {message} (why not, in words)
     * @returns {{ok?: boolean, message?: string}}
     */
    function changeSize(s, dw, dh) {
        return setSize(s, s.width + dw, s.height + dh);
    }
    function setSize(s, w, h) {
        if (s.hardware && w !== s.width) return { message: 'Un sprite de hardware mide 16 de ancho (T cambia el tipo).' };
        if (w < 1 || h < 1 || w > MAX_SIDE || h > MAX_SIDE) return {};
        if (w === s.width && h === s.height) return {};
        resize(s, w, h);
        return { ok: true };
    }

    function changePlanes(s, planes) {
        if (s.hardware && s.planes === 4) return { message: 'Un sprite acoplado tiene 15 colores y el transparente (T cambia el tipo).' };
        if (s.hardware) return { message: 'Un sprite de hardware tiene 3 colores y el transparente (T cambia el tipo).' };
        if (planes < 1 || planes > 8 || planes === s.planes) return {};
        setPlanes(s, planes);
        return { ok: true };
    }

    /** The next kind: BOB -> hardware sprite (16 wide, 2 planes: what does not fit goes) -> attached -> BOB */
    function cycleKind(s) {
        if (s.hardware && s.planes !== 4) {
            setPlanes(s, 4);
            return { ok: true, message: 'Ahora es un sprite acoplado: 16 de ancho y 16 colores.' };
        }
        if (s.hardware) {
            s.hardware = false;
            return { ok: true, message: 'Ahora es un BOB.' };
        }
        if (s.width !== 16) resize(s, 16, s.height);
        if (s.planes !== 2) setPlanes(s, 2);
        s.hardware = true;
        return { ok: true, message: 'Ahora es un sprite de hardware: 16 de ancho y 4 colores.' };
    }

    /** Goes to kind ('sprite', 'attached' or 'bob') the way T does */
    function setKind(s, kind) {
        let msg = null;
        for (let i = 0; i < 3 && kindOf(s) !== kind; i++) msg = cycleKind(s).message;
        return msg ? { ok: true, message: msg } : {};
    }

    // --- frames: each returns the frame that is current after it, or -1 if nothing changed (and why, in .message)
    function newFrame(s, cur, copy) {
        s.frames.splice(cur + 1, 0, copy ? s.frames[cur].slice() : new Uint8Array(s.width * s.height));
        return cur + 1;
    }
    function removeFrame(s, cur) {
        if (s.frames.length < 2) return { frame: -1, message: 'Hace falta al menos un fotograma.' };
        s.frames.splice(cur, 1);
        return { frame: Math.min(cur, s.frames.length - 1) };
    }
    function moveFrame(s, cur, step) {
        const other = cur + step;
        if (other < 0 || other >= s.frames.length) return -1;
        const p = s.frames[cur];
        s.frames[cur] = s.frames[other];
        s.frames[other] = p;
        return other;
    }
    function clearFrame(s, cur) {
        if (!s.frames[cur].some((v) => v)) return false;
        s.frames[cur] = new Uint8Array(s.width * s.height);
        return true;
    }
    function mirror(s, cur, horizontal) {
        const p = s.frames[cur], n = new Uint8Array(p.length);
        for (let y = 0; y < s.height; y++)
            for (let x = 0; x < s.width; x++)
                n[y * s.width + x] = horizontal ? p[y * s.width + s.width - 1 - x] : p[(s.height - 1 - y) * s.width + x];
        s.frames[cur] = n;
    }
    /** Moves the drawing dx, dy pixels; what goes out on one side comes in on the other */
    function shift(s, cur, dx, dy) {
        const p = s.frames[cur], n = new Uint8Array(p.length);
        for (let y = 0; y < s.height; y++)
            for (let x = 0; x < s.width; x++)
                n[((y + dy + s.height) % s.height) * s.width + (x + dx + s.width) % s.width] = p[y * s.width + x];
        s.frames[cur] = n;
    }
    /** A copied frame as text (for the clipboard): {dashFrame: 1, width, height, pixels} */
    function frameText(s, cur) {
        return JSON.stringify({ dashFrame: 1, width: s.width, height: s.height, pixels: Array.from(s.frames[cur]) });
    }
    /** Pastes a copied frame as a new one after cur (another size: from the corner, cut); -1 if text is not one */
    function pasteFrame(s, cur, text) {
        let c;
        try { c = JSON.parse(text); } catch (e) { return -1; }
        if (!c || c.dashFrame !== 1 || !Array.isArray(c.pixels)) return -1;
        const n = new Uint8Array(s.width * s.height), mask = colours(s) - 1;
        for (let y = 0; y < s.height && y < c.height; y++)
            for (let x = 0; x < s.width && x < c.width; x++) n[y * s.width + x] = (c.pixels[y * c.width + x] | 0) & mask;
        s.frames.splice(cur + 1, 0, n);
        return cur + 1;
    }

    /** Ticks per frame, between 1 and 50 */
    function setSpeed(s, ticks) {
        const v = Math.max(1, Math.min(MAX_SPEED, ticks | 0));
        if (v === s.speed) return false;
        s.speed = v;
        return true;
    }

    /**
     * The Dash lines that load this sprite (file: its name as the program will see it), give it its colours and say
     * how to animate it: the same text Forja copies (sp_codigo)
     */
    function code(s, file) {
        const n = s.frames.length;
        let t = '# ' + file + ': ';
        if (s.hardware && s.planes === 4) t += `sprite acoplado de 16 x ${s.height}`;
        else if (s.hardware) t += `sprite de hardware de 16 x ${s.height}`;
        else t += `BOB de ${s.width} x ${s.height}, ${colours(s)} colores`;
        t += `, ${n} fotogramas, ${s.speed} tics por fotograma\n`;
        const animate = '# animarlo: en cada wait_vblank(), cuenta = cuenta + 1 y\n';
        if (s.hardware) {
            const order = s.planes === 4 ? 'sprite_load_attached' : 'sprite_load';
            t += `if not ${order}(0, "${file}")\n    Print "No se puede cargar ${file}"\nend\n`;
            t += '# sus colores, los del fichero (en una pantalla propia del programa)\n';
            t += `sprite_load_colors(0, "${file}")\n`;
            if (n > 1) t += animate + `# sprite_frame(0, (cuenta / ${s.speed}) % ${n})\n`;
            return t;
        }
        t += `if not bob_load(0, "${file}")\n    Print "No se puede cargar ${file}"\nend\n`;
        t += '# sus colores, los del fichero, en la paleta de la pantalla (el 0, el transparente, es el fondo)\n';
        t += `bob_load_colors("${file}", 0)\n`;
        if (n > 1) t += animate + `# bob_frame(0, (cuenta / ${s.speed}) % ${n}), bob_pos(0, x, y), bob_draw(0)\n`;
        return t;
    }

    const api = { IFF, TOOLS, TOOL_KEYS, TOOL_NAMES, KIND_NAMES, MAX_SIDE, MAX_SPEED, colours, kindOf, clone, px,
        linePoints, boxPoints, plot, fill, setComponent, changeSize, setSize, changePlanes, cycleKind, setKind,
        newFrame, removeFrame, moveFrame, clearFrame, mirror, shift, frameText, pasteFrame, setSpeed, code };
    if (typeof module === 'object' && module.exports) module.exports = api;
    else root.DashSprite = api;
})(typeof window !== 'undefined' ? window : globalThis);
